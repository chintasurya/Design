from datetime import datetime, timedelta, timezone

from app.runs import MemoryRunStore, reap_if_stale
from .test_api import KEY, api  # noqa: F401 - fixture

SA = "agent-gateway@p.iam.gserviceaccount.com"


class FakeTasks:
    def __init__(self):
        self.sent = []

    def dispatch(self, run_id, job):
        self.sent.append((run_id, job))


def queued_through_tasks(svc):
    tasks = FakeTasks()
    svc.tasks = tasks
    svc.settings = type(svc.settings)(**{**svc.settings.__dict__, "tasks_service_account": SA})
    svc.verify_task_token = lambda token: SA if token == "good-oidc" else "someone-else@x.com"
    return tasks


def test_runs_go_through_the_queue_and_execute_inside_the_task_request(api):  # noqa: F811
    client, svc = api
    tasks = queued_through_tasks(svc)
    client.post("/v1/codex/connect", json={"apiKey": "sk-good"}, headers=KEY)
    started = client.post("/v1/requirements/chat", json={"message": "Analyze KAN-7"}, headers=KEY).json()
    assert tasks.sent == [(started["runId"], "requirement")]
    assert client.get(f"/v1/runs/{started['runId']}", headers=KEY).json()["status"] == "queued"

    url = f"/internal/runs/{started['runId']}/execute"
    assert client.post(url, json={"job": "requirement"}).status_code == 403
    assert client.post(url, json={"job": "requirement"},
                       headers={"Authorization": "Bearer stolen"}).status_code == 403
    out = client.post(url, json={"job": "requirement"}, headers={"Authorization": "Bearer good-oidc"}).json()
    assert out["status"] == "succeeded"
    run = client.get(f"/v1/runs/{started['runId']}", headers=KEY).json()
    assert run["result"]["spec"]["ticket_key"] == "KAN-7" and run["heartbeat_at"]

    again = client.post(url, json={"job": "requirement"}, headers={"Authorization": "Bearer good-oidc"}).json()
    assert again == {"skipped": "run is succeeded"}  # a redelivered task never re-runs the work

    dev = client.post("/v1/developer/runs", json={"ticketKey": "KAN-7", "spec": run["result"]["spec"]},
                      headers=KEY).json()
    assert tasks.sent[-1] == (dev["runId"], "developer")
    client.post(f"/internal/runs/{dev['runId']}/execute", json={"job": "developer"},
                headers={"Authorization": "Bearer good-oidc"})
    assert client.get(f"/v1/runs/{dev['runId']}", headers=KEY).json()["status"] == "waiting_approval"
    client.post(f"/v1/runs/{dev['runId']}/deploy", headers=KEY)
    assert tasks.sent[-1] == (dev["runId"], "deploy")
    client.post(f"/internal/runs/{dev['runId']}/execute", json={"job": "deploy"},
                headers={"Authorization": "Bearer good-oidc"})
    run = client.get(f"/v1/runs/{dev['runId']}", headers=KEY).json()
    assert run["status"] == "succeeded" and run["result"]["deployment"]["success"]


def test_a_run_whose_instance_died_fails_instead_of_spinning():
    store = MemoryRunStore()
    run = store.create("requirement", {})
    old = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    store._runs[run["id"]].update(status="running", heartbeat_at=old, updated_at=old)
    out = reap_if_stale(store, store.get(run["id"]))
    assert out["status"] == "failed" and out["error"].startswith("Interrupted") and "Ask again" in out["error"]

    fresh = store.create("requirement", {})
    store.update(fresh["id"], status="running", heartbeat_at=datetime.now(timezone.utc).isoformat())
    assert reap_if_stale(store, store.get(fresh["id"]))["status"] == "running"
