import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.agents.developer import DeveloperAgent, SalesforceCli
from app.codex import CodexConnection
from app.graph.store import GraphService, LocalJsonStore
from app.runs import MemoryRunStore

from .fakes import (SUCCESS, FakeCliRunner, FakeJira, FakeOpenAI, FakeSalesforce, call, issue, sample_graph,
                    settings)
from .test_agents import GOOD, SPEC, codex_writes

KEY = {"X-Gateway-Key": "k" * 32}


def openai_transport(models=("gpt-5.2-codex", "gpt-4o")):
    def handler(req: httpx.Request):
        if req.headers["Authorization"] != "Bearer sk-good":
            return httpx.Response(401, json={"error": "bad key"})
        return httpx.Response(200, json={"data": [{"id": m} for m in models]})
    return httpx.MockTransport(handler)


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("GATEWAY_API_KEY", "k" * 32)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = settings(tmp_path)
    graphs = GraphService(LocalJsonStore(str(tmp_path / "kg.json")))
    graphs.replace(sample_graph())
    codex = CodexConnection(s, transport=openai_transport())
    codex._codex_login = lambda key: "codex-cli test"
    jira = FakeJira([issue("KAN-7", "Account risk score")])
    script = FakeOpenAI([[call("submit_requirement_spec", SPEC)], "Spec ready."])
    sf = FakeSalesforce()
    dev = DeveloperAgent(s, codex, SalesforceCli(s, sf, FakeCliRunner([SUCCESS, SUCCESS])), jira, graphs,
                         codex_runner=codex_writes([GOOD]))
    svc = main.Services(s, codex=codex, jira=jira, sf=sf, graphs=graphs, runs=MemoryRunStore(),
                        openai_client_factory=lambda: script, developer=dev, sync_runs=True)
    main.app.dependency_overrides[main.get_services] = lambda: svc
    yield TestClient(main.app), svc
    main.app.dependency_overrides.clear()


def test_every_route_needs_the_gateway_key(api):
    client, _ = api
    assert client.get("/healthz").status_code == 200
    assert client.get("/v1/status").status_code == 401
    assert client.get("/v1/status", headers={"X-Gateway-Key": "wrong"}).status_code == 401


def test_nothing_agentic_works_before_codex_is_connected(api):
    client, _ = api
    r = client.post("/v1/requirements/chat", json={"message": "list tickets"}, headers=KEY)
    assert r.status_code == 409 and "Connect to Codex first" in r.text


def test_connect_asks_for_a_key_rejects_a_bad_one_and_picks_a_codex_model(api):
    client, svc = api
    r = client.post("/v1/codex/connect", json={}, headers=KEY).json()
    assert r["connected"] is False and r["needsKey"] is True
    r = client.post("/v1/codex/connect", json={"apiKey": "sk-bad"}, headers=KEY).json()
    assert r["connected"] is False and "401" in r["message"]
    r = client.post("/v1/codex/connect", json={"apiKey": "sk-good"}, headers=KEY).json()
    assert r["connected"] is True and r["model"] == "gpt-5.2-codex" and r["codexCli"] == "codex-cli test"
    status = client.get("/v1/status", headers=KEY).json()
    assert status["codex"]["connected"] and status["graph"]["nodes"] == len(sample_graph().nodes)


def test_jira_to_org_end_to_end(api):
    client, svc = api
    client.post("/v1/codex/connect", json={"apiKey": "sk-good"}, headers=KEY)

    tickets = client.get("/v1/jira/tickets", headers=KEY).json()
    assert tickets["tickets"][0]["key"] == "KAN-7"

    started = client.post("/v1/requirements/chat", json={"message": "Analyze KAN-7"}, headers=KEY).json()
    run = client.get(f"/v1/runs/{started['runId']}", headers=KEY).json()
    assert run["status"] == "succeeded" and run["result"]["spec"]["ticket_key"] == "KAN-7"
    assert svc.runs.get_conversation(started["conversationId"])["previous_response_id"] == "resp_2"

    dev = client.post("/v1/developer/runs", json={"ticketKey": "KAN-7", "spec": run["result"]["spec"]},
                      headers=KEY).json()
    run = client.get(f"/v1/runs/{dev['runId']}", headers=KEY).json()
    assert run["status"] == "waiting_approval", run
    assert run["result"]["validation"]["success"]

    client.post(f"/v1/runs/{dev['runId']}/deploy", headers=KEY)
    run = client.get(f"/v1/runs/{dev['runId']}", headers=KEY).json()
    assert run["status"] == "succeeded" and run["result"]["deployment"]["success"]
    assert client.post(f"/v1/runs/{dev['runId']}/deploy", headers=KEY).status_code == 409  # only once

    found = client.get("/v1/graph/search", params={"q": "KAN-7"}, headers=KEY).json()
    assert any("implemented by" in line for line in found["related"])


def test_a_spec_marked_not_ready_needs_an_explicit_override(api):
    client, _ = api
    client.post("/v1/codex/connect", json={"apiKey": "sk-good"}, headers=KEY)
    body = {"ticketKey": "KAN-7", "spec": {**SPEC, "ready_for_development": False}}
    assert client.post("/v1/developer/runs", json=body, headers=KEY).status_code == 409
    assert client.post("/v1/developer/runs", json={**body, "override": True}, headers=KEY).status_code == 200
    bad = {"ticketKey": "KAN-8", "spec": SPEC}
    assert client.post("/v1/developer/runs", json=bad, headers=KEY).status_code == 400


def test_graph_rebuild_ingests_salesforce_and_jira(api):
    client, _ = api
    run_id = client.post("/v1/graph/rebuild", headers=KEY).json()["runId"]
    run = client.get(f"/v1/runs/{run_id}", headers=KEY).json()
    assert run["status"] == "succeeded", run
    assert run["result"]["node_types"]["JiraTicket"] == 1 and run["result"]["node_types"]["Flow"] == 1
    assert client.get("/v1/runs/not-an-id!", headers=KEY).status_code in (400, 404)
