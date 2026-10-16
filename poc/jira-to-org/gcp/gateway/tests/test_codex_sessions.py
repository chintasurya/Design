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
        assert cmd[1] == "login" and cmd[-1] == "--device-auth"
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


BROWSER_OUT = ("Starting local login server on http://localhost:1455.\n"
               "If your browser did not open, navigate to this URL to authenticate:\n\n"
               "https://auth.openai.com/oauth/authorize?response_type=code&client_id=app_x&redirect_uri="
               "http%3A%2F%2F127.0.0.1%3A1455%2Fauth%2Fcallback&code_challenge=c&state=s1\n\n"
               "On a remote or headless machine? Use `codex login --device-auth` instead.\n")


class FakeBrowserLogin:
    """Stands in for `codex login` (browser flow): prints the real output, then
    waits for the callback on its local port."""

    def __init__(self, cmd, env):
        assert cmd[1] == "login" and "--device-auth" not in cmd and env["BROWSER"] == "/bin/true"
        self.home = env["CODEX_HOME"]
        self.done = threading.Event()
        self.code = None
        self.stdout = iter(BROWSER_OUT.splitlines(keepends=True))

    def callback(self, url):  # what the CLI's local server does with the replayed request
        assert url == "http://127.0.0.1:1455/auth/callback?code=AUTHCODE&state=s1"
        with open(os.path.join(self.home, "auth.json"), "w") as fh:
            fh.write(AUTH)
        self.code = 0
        self.done.set()

    def poll(self):
        return self.code

    def wait(self):
        self.done.wait(5)
        return self.code if self.code is not None else 1

    def kill(self):
        self.code = -9
        self.done.set()


def test_browser_sign_in_with_sso_and_a_pasted_redirect(tmp_path):
    from app.codex_sessions import callback_target

    logins = []
    spawn = lambda cmd, env: logins.append(FakeBrowserLogin(cmd, env)) or logins[-1]  # noqa: E731
    s = settings(tmp_path, codex_auth_mode="chatgpt", codex_login_flow="browser")
    sessions = CodexSessions(s, MemoryVault(), spawn=spawn, replay=lambda url: logins[-1].callback(url))
    started = sessions.connect("alice@example.com")
    assert started["pending"] and started["flow"] == "browser"
    assert started["authUrl"].startswith("https://auth.openai.com/oauth/authorize?")
    # one browser sign-in at a time: the CLI owns port 1455
    assert sessions.connect("bob@example.com")["busy"] is True

    with pytest.raises(ValueError, match="not the Codex sign-in callback"):
        sessions.complete("alice@example.com", "http://localhost:9999/auth/callback?code=x&state=y")
    with pytest.raises(ValueError, match="starts with http://localhost:1455"):
        sessions.complete("alice@example.com", "https://evil.example/auth/callback?code=x&state=y")
    with pytest.raises(ValueError, match="refused"):
        callback_target(started["authUrl"], "http://localhost:1455/auth/callback?error=access_denied&state=s1")

    # the browser lands on 127.0.0.1 or localhost; both are accepted
    done = sessions.complete("alice@example.com", "http://127.0.0.1:1455/auth/callback?code=AUTHCODE&state=s1")
    assert done["connected"] and done["account"]["email"] == "alice@example.com"
    assert user_key("alice@example.com") in sessions.vault.data
    assert sessions.connect("bob@example.com")["pending"]  # the port is free again


@pytest.fixture
def chatgpt_api(tmp_path, monkeypatch):
    monkeypatch.setenv("GATEWAY_API_KEY", "k" * 32)
    s = settings(tmp_path, codex_auth_mode="chatgpt")
    graphs = GraphService(LocalJsonStore(str(tmp_path / "kg.json")))
    graphs.replace(sample_graph())
    spawner = Spawner()
    plan = {"n": 0}

    def fetch_usage(token, account):  # each call: 2 more points of the 5-hour window, 0.5 credits
        plan["n"] += 1
        return {"plan_type": "plus", "rate_limit": {
            "primary_window": {"used_percent": 10 + 2 * plan["n"], "limit_window_seconds": 18000, "reset_at": 1},
            "secondary_window": {"used_percent": 3, "limit_window_seconds": 604800, "reset_at": 2}},
            "credits": {"has_credits": True, "unlimited": False, "balance": str(20 - 0.5 * plan["n"])}}

    sessions = CodexSessions(s, MemoryVault(), spawn=spawner, fetch_usage=fetch_usage)
    jira = FakeJira([issue("KAN-7", "Add Risk Score to Account", "Acceptance Criteria\n- Score 0-100")])
    prompts = []

    def requirement_exec(conn, ws, prompt, on_line, home=None, sandbox=None, output_schema=None,
                         instructions=None, extra_args=None):
        prompts.append({"prompt": prompt, "home": home, "sandbox": sandbox, "schema": output_schema,
                        "instructions": instructions, "extra_args": extra_args})
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
    # lean: our own short instructions, no tools, no environment block
    assert call["instructions"].startswith("You are the Requirement Agent")
    assert "shell_tool" in call["extra_args"] and "include_environment_context=false" in call["extra_args"]
    assert "You are the Requirement Agent" not in call["prompt"]  # instructions are not sent twice
    # plan usage around the call: 2 points of the 5-hour limit and half a credit
    assert run["plan_usage"]["primary_pct_used"] == 2 and run["plan_usage"]["credits_used"] == 0.5
    assert '"KAN-7"' in call["prompt"] and "knowledge_graph" in call["prompt"]  # the gateway looked it up
    assert call["schema"]["required"] == ["reply", "spec"]
    comp = run["result"]["spec"]["components"][0]
    assert comp["exists_in_org"] and comp["action"] == "modify"  # still grounded against the graph
    assert run["usage"]["ticket"] == "KAN-7" and run["usage"]["total_tokens"] == 3500

    # the same unchanged ticket again: the stored spec, no model call
    calls = len(prompts)
    again = client.post("/v1/requirements/chat", json={"message": "Analyze KAN-7"}, headers=ALICE).json()
    cached = client.get(f"/v1/runs/{again['runId']}", headers=ALICE).json()
    assert len(prompts) == calls and "Reused" in cached["result"]["reply"]
    assert cached["usage"]["calls"] == 0 and cached["usage"]["total_tokens"] == 0
    client.post("/v1/requirements/chat", json={"message": "Analyze KAN-7 again"}, headers=ALICE)
    assert len(prompts) == calls + 1  # asked to refresh, so it calls Codex

    # reading a ticket or listing tickets never calls the model
    calls = len(prompts)
    read = client.post("/v1/requirements/chat", json={"message": "Read KAN-7"}, headers=ALICE).json()
    r = client.get(f"/v1/runs/{read['runId']}", headers=ALICE).json()
    assert len(prompts) == calls and "Score 0-100" in r["result"]["reply"] and "no model call" in r["result"]["reply"]
    assert r["usage"]["model"] == "knowledge graph (no model call)" and r["usage"]["total_tokens"] == 0
    listed = client.post("/v1/requirements/chat", json={"message": "list my open tickets"}, headers=ALICE).json()
    r = client.get(f"/v1/runs/{listed['runId']}", headers=ALICE).json()
    assert len(prompts) == calls and "KAN-7 · Add Risk Score to Account" in r["result"]["reply"]

    plan_now = client.get("/v1/codex/plan", headers=ALICE).json()
    assert plan_now["available"] and plan_now["plan"] == "plus" and plan_now["secondary"]["window_minutes"] == 10080
    assert client.get("/v1/codex/plan", headers=BOB).json()["available"] is False

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
