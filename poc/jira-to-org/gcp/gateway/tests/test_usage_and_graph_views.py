from datetime import datetime, timezone

from app.usage import summarize

from .fakes import sample_graph
from .test_api import KEY, api  # noqa: F401 - fixture


def run(agent, ticket, total, day, status="succeeded"):
    return {"id": f"{agent}{ticket}{day}", "status": status, "created_at": f"{day}T10:00:00+00:00",
            "usage": {"agent": agent, "model": "m", "ticket": ticket, "calls": 2, "input_tokens": total - 100,
                      "cached_input_tokens": 0, "output_tokens": 100, "reasoning_tokens": 0, "total_tokens": total}}


def test_usage_summary_by_agent_day_and_ticket():
    now = datetime(2026, 10, 16, 12, tzinfo=timezone.utc)
    runs = [run("requirement", "KAN-6", 3000, "2026-10-16"), run("developer", "KAN-6", 20000, "2026-10-16"),
            run("developer", "KAN-7", 9000, "2026-10-15", "failed"), run("requirement", "KAN-1", 999, "2026-09-01"),
            {"id": "graph", "status": "succeeded", "created_at": "2026-10-16T00:00:00+00:00"}]
    out = summarize(runs, days=7, now=now)
    assert out["total_tokens"] == 32000  # the September run is outside the window; graph runs use no model
    assert out["agents"]["developer"]["runs"] == 2 and out["agents"]["developer"]["avg_per_run"] == 14500
    assert out["agents"]["developer"]["outcomes"] == {"succeeded": 1, "failed": 1}
    assert len(out["by_day"]) == 7 and out["by_day"][-1] == {"date": "2026-10-16", "requirement": 3000, "developer": 20000}
    assert out["by_ticket"][0] == {"ticket": "KAN-6", "requirement": 3000, "developer": 20000, "total": 23000, "runs": 2}


def test_graph_schema_and_ego_views(api):  # noqa: F811
    client, _ = api
    schema = client.get("/v1/graph/schema", headers=KEY).json()
    assert {"type": "Field", "count": 2} in schema["node_types"]
    assert {"from_type": "ApexTrigger", "edge_type": "TRIGGER_CALLS_APEX", "to_type": "ApexClass", "count": 1} \
        in schema["edge_types"]
    ego = client.get("/v1/graph/neighbourhood", params={"q": "account"}, headers=KEY).json()
    assert ego["centre"] == "sobj:account" and ego["fields_folded"] == 2  # fields are a count, not 200 dots
    assert {n["id"] for n in ego["nodes"]} == {"sobj:account", "trigger:accounttrigger", "apex:contactservice"}
    again = client.get("/v1/graph/neighbourhood", params={"id": "trigger:accounttrigger"}, headers=KEY).json()
    assert {n["id"] for n in again["nodes"]} == {"trigger:accounttrigger", "sobj:account", "apex:accounttriggerhandler"}
    assert client.get("/v1/graph/neighbourhood", params={"q": "zzzz"}, headers=KEY).status_code == 404


def test_usage_endpoint_counts_a_real_requirement_run(api):  # noqa: F811
    client, _ = api
    client.post("/v1/codex/connect", json={"apiKey": "sk-good"}, headers=KEY)
    client.post("/v1/requirements/chat", json={"message": "Analyze KAN-7"}, headers=KEY)
    out = client.get("/v1/usage", params={"days": 3}, headers=KEY).json()
    assert out["agents"]["requirement"]["total_tokens"] == 2400 and out["recent"][0]["ticket"] == "KAN-7"
