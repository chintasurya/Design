"""Agent runs: state that outlives a single HTTP call.

Salesforce Apex callouts stop at 120 s, and a Codex run takes minutes, so
every agent turn is a run: the LWC starts it, gets an id back at once, and
polls. Runs live in Firestore on GCP, in memory for local runs and tests.
"""
from __future__ import annotations

import copy
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Protocol

from .graph.store import now_iso

TERMINAL = {"succeeded", "failed", "rejected"}


class RunStore(Protocol):
    def create(self, kind: str, payload: dict) -> dict: ...
    def get(self, run_id: str) -> dict | None: ...
    def update(self, run_id: str, **fields: Any) -> dict: ...
    def get_conversation(self, conversation_id: str) -> dict: ...
    def set_conversation(self, conversation_id: str, data: dict) -> None: ...


def _new_run(kind: str, payload: dict) -> dict:
    at = now_iso()
    return {"id": uuid.uuid4().hex[:16], "kind": kind, "status": "queued", "payload": payload,
            "steps": [], "result": None, "error": None, "created_at": at, "updated_at": at}


class MemoryRunStore:
    def __init__(self) -> None:
        self._runs: dict[str, dict] = {}
        self._conversations: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, kind: str, payload: dict) -> dict:
        run = _new_run(kind, payload)
        with self._lock:
            self._runs[run["id"]] = run
        return copy.deepcopy(run)

    def get(self, run_id: str) -> dict | None:
        with self._lock:
            run = self._runs.get(run_id)
            return copy.deepcopy(run) if run else None

    def update(self, run_id: str, **fields: Any) -> dict:
        with self._lock:
            run = self._runs[run_id]
            run.update(copy.deepcopy(fields))
            run["updated_at"] = now_iso()
            return copy.deepcopy(run)

    def get_conversation(self, conversation_id: str) -> dict:
        with self._lock:
            return dict(self._conversations.get(conversation_id, {}))

    def set_conversation(self, conversation_id: str, data: dict) -> None:
        with self._lock:
            self._conversations[conversation_id] = dict(data)


class FirestoreRunStore:
    def __init__(self, project: str):
        from google.cloud import firestore

        self.db = firestore.Client(project=project)
        self.runs = self.db.collection("agent_runs")
        self.conversations = self.db.collection("agent_conversations")

    def create(self, kind: str, payload: dict) -> dict:
        run = _new_run(kind, payload)
        self.runs.document(run["id"]).set(run)
        return run

    def get(self, run_id: str) -> dict | None:
        snap = self.runs.document(run_id).get()
        return snap.to_dict() if snap.exists else None

    def update(self, run_id: str, **fields: Any) -> dict:
        fields["updated_at"] = now_iso()
        self.runs.document(run_id).update(fields)
        return self.get(run_id) or {}

    def get_conversation(self, conversation_id: str) -> dict:
        snap = self.conversations.document(conversation_id).get()
        return snap.to_dict() if snap.exists else {}

    def set_conversation(self, conversation_id: str, data: dict) -> None:
        self.conversations.document(conversation_id).set(data)


class RunContext:
    """What an agent uses to report progress. Each step is visible in the LWC."""

    def __init__(self, store: RunStore, run_id: str):
        self.store = store
        self.run_id = run_id
        self._steps: list[dict] = (store.get(run_id) or {}).get("steps", [])

    def step(self, name: str, status: str = "done", detail: str = "") -> None:
        self._steps.append({"at": now_iso(), "name": name, "status": status, "detail": detail[:2000]})
        self.store.update(self.run_id, steps=self._steps)

    def status(self, status: str, **fields: Any) -> None:
        self.store.update(self.run_id, status=status, **fields)

    def get(self) -> dict:
        return self.store.get(self.run_id) or {}


class Runner:
    """Background execution. Cloud Run is deployed with CPU always allocated
    and one instance, so a thread outlives the request that started it."""

    def __init__(self, store: RunStore, workers: int = 2):
        self.store = store
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="agent")

    def submit(self, run: dict, fn: Callable[[RunContext], dict | None], sync: bool = False) -> dict:
        def job() -> None:
            ctx = RunContext(self.store, run["id"])
            ctx.status("running")
            try:
                result = fn(ctx)
                current = ctx.get().get("status")
                if current == "running":
                    ctx.status("succeeded", result=result)
                elif result is not None:
                    self.store.update(run["id"], result=result)
            except Exception as exc:  # noqa: BLE001 - surfaced to the user as the run's error
                ctx.step("failed", "error", f"{type(exc).__name__}: {exc}")
                ctx.status("failed", error=f"{type(exc).__name__}: {exc}")

        if sync:
            job()
        else:
            self.pool.submit(job)
        return run
