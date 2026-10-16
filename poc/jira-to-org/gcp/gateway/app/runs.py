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
    def list_recent(self, limit: int = 500) -> list[dict]: ...


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

    def list_recent(self, limit: int = 500) -> list[dict]:
        with self._lock:
            runs = sorted(self._runs.values(), key=lambda r: r["created_at"], reverse=True)
            return copy.deepcopy(runs[:limit])

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

    def list_recent(self, limit: int = 500) -> list[dict]:
        from google.cloud import firestore

        query = self.runs.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
        return [d.to_dict() for d in query.stream()]

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
        run = store.get(run_id) or {}
        self._steps: list[dict] = run.get("steps", [])
        self._usage: dict | None = run.get("usage")

    def step(self, name: str, status: str = "done", detail: str = "") -> None:
        self._steps.append({"at": now_iso(), "name": name, "status": status, "detail": detail[:2000]})
        self.store.update(self.run_id, steps=self._steps)

    def add_usage(self, agent: str, model: str | None, input_tokens: int = 0, output_tokens: int = 0,
                  cached_input_tokens: int = 0, reasoning_tokens: int = 0, ticket: str | None = None,
                  calls: int = 1) -> None:
        """Accumulate model tokens on the run; the dashboard sums these."""
        u = self._usage or {"agent": agent, "model": model, "ticket": ticket, "calls": 0, "input_tokens": 0,
                            "cached_input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0,
                            "total_tokens": 0}
        u["calls"] += calls
        u["input_tokens"] += int(input_tokens or 0)
        u["cached_input_tokens"] += int(cached_input_tokens or 0)
        u["output_tokens"] += int(output_tokens or 0)
        u["reasoning_tokens"] += int(reasoning_tokens or 0)
        u["total_tokens"] = u["input_tokens"] + u["output_tokens"]
        u["model"] = model or u.get("model")
        u["ticket"] = ticket or u.get("ticket")
        self._usage = u
        self.store.update(self.run_id, usage=u)

    def plan_usage(self, before: dict | None, after: dict | None) -> None:
        """How much of the developer's Codex plan this run used: limit
        percentage points and credits, from snapshots taken around it."""
        if not after:
            return
        def pct(snap: dict | None, window: str) -> float | None:
            return ((snap or {}).get(window) or {}).get("used_percent")
        def bal(snap: dict | None) -> float | None:
            return ((snap or {}).get("credits") or {}).get("balance")
        delta = {"after": after}
        for window in ("primary", "secondary"):
            if pct(before, window) is not None and pct(after, window) is not None:
                delta[f"{window}_pct_used"] = round(pct(after, window) - pct(before, window), 2)
        if bal(before) is not None and bal(after) is not None:
            delta["credits_used"] = round(bal(before) - bal(after), 4)
        self.store.update(self.run_id, plan_usage=delta)

    def usage_ticket(self, ticket: str | None) -> None:
        if self._usage and ticket:
            self._usage["ticket"] = ticket
            self.store.update(self.run_id, usage=self._usage)

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
