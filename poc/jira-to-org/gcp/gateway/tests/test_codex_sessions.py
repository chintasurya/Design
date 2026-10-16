import base64
import json
import os
import threading

import pytest
from fastapi.testclient import TestClient

from app import main
from app.agents.developer import DeveloperAgent, SalesforceCli
from app.codex import CodexConnection
from app.codex_sessions import CodexSessions, MemoryVault, account_from_auth, parse_device_prompt, user_key
from app.graph.store import GraphService, LocalJsonStore
from app.runs import MemoryRunStore

from .fakes import SUCCESS, FakeCliRunner, FakeJira, FakeSalesforce, issue, sample_graph, settings
from .test_agents import GOOD, SPEC, codex_writes

KEY = {"X-Gateway-Key": "k" * 32}
ALICE = {**KEY, "X-Salesforce-User": "alice@example.com"}
BOB = {**KEY, "X-Salesforce-User": "bob@example.com"}

# exactly what codex-rs/login/src/device_code_auth.rs prints, ANSI colours included
PROMPT = ("\nFollow these steps to sign in with ChatGPT using device code authorization:\n"
          "\n1. Open this link in your browser and sign in to your account\n   \x1b[94mhttps://auth.openai.com/codex/device\x1b[0m\n"
          "\n2. Enter this one-time code \x1b[90m(expires in 15 minutes)\x1b[0m\n   \x1b[94mABCD-12345\x1b[0m\n")


def jwt(claims):
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return f"e30.{body}.sig"


AUTH = json.dumps({"OPENAI_API_KEY": None, "tokens": {
    "id_token": jwt({"email": "alice@example.com", "https://api.openai.com/auth": {"chatgpt_plan_type": "plus"}}),
    "access_token": "at", "refresh_token": "rt"}})


class FakeLogin:
    """Stands in for `codex login --device-auth`: prints the prompt, then
    waits until the test 'approves' in the browser and writes auth.json."""

    def __init__(self, cmd, env):
        assert cmd[1:] == ["login", "--device-auth"]
        self.home = env["CODEX_HOME"]
        self.approved = threading.Event()
        self.code = None
        self.stdout = iter(PROMPT.splitlines(keepends=True))

    def poll(self):
        return self.code

    def wait(self):
        self.approved.wait(5)
        with open(os.path.join(self.home, "auth.json"), "w") as fh:
            fh.write(AUTH)
        self.code = 0
        return 0

    def kill(self):
        self.code = -9


class Spawner:
    def __init__(self):
        self.logins = []

    def __call__(self, cmd, env):
        login = FakeLogin(cmd, env)
        self.logins.append(login)
        return login


def approve(spawner, sessions, user):
    spawner.logins[-1].approved.set()
    for _ in range(200):
        if sessions.status(user)["connected"] and user_key(user) in sessions.vault.data:
            return
        threading.Event().wait(0.01)
    raise AssertionError("sign-in never completed")


def test_parse_device_prompt_and_account():
    assert parse_device_prompt(PROMPT) == ("https://auth.openai.com/codex/device", "ABCD-12345")
    assert account_from_auth(AUTH) == {"email": "alice@example.com", "plan": "plus"}
    assert account_from_auth("not json") == {}


def test_sign_in_survives_a_new_instance_and_sign_out_forgets_it(tmp_path):
    vault, spawner = MemoryVault(), Spawner()
    s = settings(tmp_path, codex_auth_mode="chatgpt")
    sessions = CodexSessions(s, vault, spawn=spawner)
    started = sessions.connect("alice@example.com")
    assert started["pending"] and started["userCode"] == "ABCD-12345"
    assert started["verificationUrl"] == "https://auth.openai.com/codex/device"
    assert sessions.connect("alice@example.com")["userCode"] == "ABCD-12345"  # no second login process
    assert len(spawner.logins) == 1
    approve(spawner, sessions, "alice@example.com")
    assert sessions.status("alice@example.com")["account"] == {"email": "alice@example.com", "plan": "plus"}
    assert "alice@example.com" not in json.dumps(vault.data.keys().__repr__())  # stored by hash only

    # a fresh Cloud Run instance: empty disk, same vault
    fresh = CodexSessions(settings(tmp_path / "other", codex_auth_mode="chatgpt"), vault, spawn=spawner)
    assert fresh.connected("alice@example.com")
    assert not fresh.connected("bob@example.com")

    fresh.logout("alice@example.com")
    assert vault.data == {} and not fresh.connected("alice@example.com")


@pytest.fixture
def chatgpt_api(tmp_path, monkeypatch):
    monkeypatch.setenv("GATEWAY_API_KEY", "k" * 32)
    s = settings(tmp_path, codex_auth_mode="chatgpt")
    graphs = GraphService(LocalJsonStore(str(tmp_path / "kg.json")))
    graphs.replace(sample_graph())
    spawner = Spawner()
    sessions = CodexSessions(s, MemoryVault(), spawn=spawner)
    jira = FakeJira([issue("KAN-7", "Add Risk Score to Account", "Acceptance Criteria\n- Score 0-100")])
    prompts = []

    def requirement_exec(conn, ws, prompt, on_line, home=None, sandbox=None, output_schema=None):
        prompts.append({"prompt": prompt, "home": home, "sandbox": sandbox, "schema": output_schema})
        spec = {**SPEC, "components": [{"action": "create", "type": "CustomField", "api_name": "Account.Risk_Score__c",
                                        "description": "score", "exists_in_org": False, "evidence": "guess"}]}
        return {"exit_code": 0, "final_message": json.dumps({"reply": "Here is the spec.", "spec": spec}),
                "usage": {"input_tokens": 3000, "cached_input_tokens": 0, "output_tokens": 500}}

    dev_runner = codex_writes([GOOD])
    codex = CodexConnection(s)
    dev = DeveloperAgent(s, codex, SalesforceCli(s, FakeSalesforce(), FakeCliRunner([SUCCESS, SUCCESS])), jira,
                         graphs, codex_runner=dev_runner)
    svc = main.Services(s, codex=codex, jira=jira, sf=FakeSalesforce(), graphs=graphs, runs=MemoryRunStore(),
                        developer=dev, sync_runs=True, sessions=sessions, codex_exec=requirement_exec)
    main.app.dependency_overrides[main.get_services] = lambda: svc
    yield TestClient(main.app), svc, spawner, prompts, dev_runner
    main.app.dependency_overrides.clear()


def test_each_developer_connects_their_own_codex(chatgpt_api):
    client, svc, spawner, prompts, dev_runner = chatgpt_api
    assert client.post("/v1/codex/connect", json={}, headers=KEY).status_code == 400  # who are you?
    r = client.post("/v1/requirements/chat", json={"message": "Analyze KAN-7"}, headers=ALICE)
    assert r.status_code == 409 and "Connect to Codex first" in r.text

    pending = client.post("/v1/codex/connect", json={}, headers=ALICE).json()
    assert pending["mode"] == "chatgpt" and pending["pending"] and pending["userCode"] == "ABCD-12345"
    assert client.get("/v1/codex/login", headers=ALICE).json()["pending"]
    approve(spawner, svc.sessions, "alice@example.com")
    done = client.get("/v1/codex/login", headers=ALICE).json()
    assert done["connected"] and done["account"]["plan"] == "plus"
    assert client.get("/v1/status", headers=ALICE).json()["codex"]["connected"]
    assert not client.get("/v1/status", headers=BOB).json()["codex"]["connected"]  # Bob has not signed in

    started = client.post("/v1/requirements/chat", json={"message": "Analyze KAN-7"}, headers=ALICE).json()
    run = client.get(f"/v1/runs/{started['runId']}", headers=ALICE).json()
    assert run["status"] == "succeeded", run
    call = prompts[-1]
    assert call["home"] == svc.sessions.home("alice@example.com") and call["sandbox"] == "read-only"
    assert '"KAN-7"' in call["prompt"] and "knowledge_graph" in call["prompt"]  # the gateway looked it up
    assert call["schema"]["required"] == ["reply", "spec"]
    comp = run["result"]["spec"]["components"][0]
    assert comp["exists_in_org"] and comp["action"] == "modify"  # still grounded against the graph
    assert run["usage"]["ticket"] == "KAN-7" and run["usage"]["total_tokens"] == 3500

    # a follow-up keeps the conversation and the ticket in view
    client.post("/v1/requirements/chat", json={"message": "what could break?",
                                               "conversationId": started["conversationId"]}, headers=ALICE)
    assert "EARLIER IN THIS CONVERSATION" in prompts[-1]["prompt"] and '"KAN-7"' in prompts[-1]["prompt"]

    assert client.post("/v1/developer/runs", json={"ticketKey": "KAN-7", "spec": SPEC}, headers=BOB).status_code == 409
    dev = client.post("/v1/developer/runs", json={"ticketKey": "KAN-7", "spec": SPEC}, headers=ALICE).json()
    assert client.get(f"/v1/runs/{dev['runId']}", headers=ALICE).json()["status"] == "waiting_approval"
    assert dev_runner.homes == [svc.sessions.home("alice@example.com")]  # Codex ran as Alice

    usage = client.get("/v1/usage", headers=ALICE).json()
    assert usage["by_user"][0]["user"] == "alice@example.com" and usage["recent"][0]["user"] == "alice@example.com"

    assert client.post("/v1/codex/logout", json={}, headers=ALICE).json()["connected"] is False
    assert client.post("/v1/requirements/chat", json={"message": "hi"}, headers=ALICE).status_code == 409
