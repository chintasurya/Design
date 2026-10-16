"""Agent gateway: the one HTTP surface the Salesforce LWC talks to (via Apex).

    POST /v1/codex/connect          connect first; nothing agentic works before it
    GET  /v1/codex/login            poll a developer's Codex sign-in (ChatGPT mode)
    POST /v1/codex/login/complete   browser sign-in: the redirect address the developer pasted
    POST /v1/codex/logout           sign the developer out of Codex
    GET  /v1/status                 what is connected, graph size
    GET  /v1/jira/tickets           ticket picker
    POST /v1/requirements/chat      Requirement agent turn       -> run id
    POST /v1/developer/runs         Developer agent on a spec    -> run id
    GET  /v1/runs/{id}              poll a run
    POST /v1/runs/{id}/deploy       approval gate: deploy what was validated
    POST /v1/runs/{id}/reject
    POST /v1/graph/rebuild          re-ingest Salesforce + Jira  -> run id
    GET  /v1/graph/stats | /v1/graph/search?q=
"""
from __future__ import annotations

import hmac
import os
import re
import uuid
from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from . import config
from .agents.developer import DeveloperAgent, SalesforceCli
from .agents.requirement import CodexRequirementAgent, RequirementAgent
from .codex import CodexConnection, CodexNotConnectedError, run_codex
from .codex_sessions import CodexSessions, MemoryVault, SecretManagerVault
from .config import secret
from .graph.ingest import SalesforceIngest, ingest_jira
from .graph.model import Graph
from .graph.store import BigQueryStore, GraphService, LocalJsonStore
from .jira import JiraClient, JiraError, simplify
from .runs import FirestoreRunStore, MemoryRunStore, RunContext, Runner
from .salesforce import SalesforceClient
from .usage import summarize

RUN_ID = re.compile(r"^[a-f0-9]{8,32}$")


class Services:
    """Everything wired once per process. Tests build their own."""

    def __init__(self, settings: config.Settings, codex: CodexConnection | None = None,
                 jira: JiraClient | None = None, sf: SalesforceClient | None = None,
                 graphs: GraphService | None = None, runs=None, openai_client_factory=None,
                 developer: DeveloperAgent | None = None, sync_runs: bool = False,
                 sessions: CodexSessions | None = None, codex_exec=None):
        self.settings = settings
        self.codex = codex or CodexConnection(settings)
        self.chatgpt_mode = settings.codex_auth_mode == "chatgpt"
        if sessions is None:
            vault = SecretManagerVault(settings.gcp_project) if settings.gcp_project else MemoryVault()
            sessions = CodexSessions(settings, vault)
        self.sessions = sessions
        self.codex_exec = codex_exec or run_codex
        self.jira = jira if jira is not None else self._jira()
        self.sf = sf if sf is not None else self._sf()
        if graphs is None:
            store = (BigQueryStore(settings.gcp_project, settings.bq_dataset)
                     if settings.graph_store == "bigquery" else LocalJsonStore(settings.local_graph_path))
            graphs = GraphService(store)
        self.graphs = graphs
        self.runs = runs or (FirestoreRunStore(settings.gcp_project) if settings.run_store == "firestore"
                             else MemoryRunStore())
        self.runner = Runner(self.runs)
        self.sync_runs = sync_runs
        self.openai_client_factory = openai_client_factory or self.codex.openai_client
        self._developer = developer

    def _jira(self) -> JiraClient | None:
        s = self.settings
        try:
            return JiraClient(s.jira_base_url, s.jira_email, secret("JIRA_API_TOKEN"), s.jira_project_key)
        except JiraError:
            return None

    def _sf(self) -> SalesforceClient | None:
        s = self.settings
        if not s.salesforce_configured:
            return None
        if secret("SF_AUTH_URL"):
            return SalesforceClient.from_auth_url(secret("SF_AUTH_URL"), s.sf_api_version)
        return SalesforceClient(s.sf_login_url, secret("SF_CLIENT_ID"), secret("SF_CLIENT_SECRET"), s.sf_api_version)

    def developer(self) -> DeveloperAgent:
        if self._developer is None:
            if not self.sf:
                raise HTTPException(503, "Salesforce is not configured on the gateway")
            self._developer = DeveloperAgent(self.settings, self.codex, SalesforceCli(self.settings, self.sf),
                                             self.jira, self.graphs)
        return self._developer

    def submit(self, run: dict, fn) -> dict:
        return self.runner.submit(run, fn, sync=self.sync_runs)


@lru_cache(maxsize=1)
def default_services() -> Services:
    return Services(config.load())


app = FastAPI(title="Jira-to-Org agent gateway", version="1.0.0")
services_dep = default_services


def get_services() -> Services:
    return services_dep()


def require_key(x_gateway_key: str = Header(default="")) -> None:
    expected = secret("GATEWAY_API_KEY")
    if not expected:
        if config.flag("ALLOW_NO_AUTH"):
            return
        raise HTTPException(503, "GATEWAY_API_KEY is not set; the gateway refuses all calls")
    if not hmac.compare_digest(x_gateway_key.encode(), expected.encode()):
        raise HTTPException(401, "bad gateway key")


def current_user(x_salesforce_user: str = Header(default="")) -> str:
    """The Salesforce username Apex sends with every call. Trusted because only
    the org's named credential holds the gateway key."""
    return x_salesforce_user.strip()[:200]


def require_codex(svc: Services, user: str) -> str | None:
    """None in API-key mode; the developer's own Codex home in ChatGPT mode."""
    if svc.chatgpt_mode:
        if not user:
            raise HTTPException(400, "X-Salesforce-User is required to use a developer's own Codex")
        if not svc.sessions.connected(user):
            raise HTTPException(409, "Connect to Codex first")
        return svc.sessions.home(user)
    try:
        svc.codex.require()
    except CodexNotConnectedError as exc:
        raise HTTPException(409, str(exc)) from exc
    return None


def require_jira(svc: Services) -> JiraClient:
    if not svc.jira:
        raise HTTPException(503, "Jira is not configured on the gateway")
    return svc.jira


def public_run(run: dict) -> dict:
    out = {k: v for k, v in run.items() if k != "payload"}
    return out


# -- models -----------------------------------------------------------------
class ConnectBody(BaseModel):
    apiKey: str | None = Field(default=None, max_length=400)


class CompleteLoginBody(BaseModel):
    redirectUrl: str = Field(min_length=10, max_length=4000)


class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversationId: str | None = Field(default=None, max_length=64)


class DevelopBody(BaseModel):
    ticketKey: str = Field(min_length=3, max_length=32)
    spec: dict[str, Any]
    override: bool = False


# -- routes -------------------------------------------------------------------
@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.get("/v1/status", dependencies=[Depends(require_key)])
def status(svc: Services = Depends(get_services), user: str = Depends(current_user)) -> dict:
    graph: dict[str, Any]
    try:
        g = svc.graphs.graph()
        graph = {"nodes": len(g.nodes), "edges": len(g.edges), **svc.graphs.snapshot()}
    except Exception as exc:  # noqa: BLE001
        graph = {"error": str(exc)[:300]}
    return {
        "codex": svc.sessions.status(user) if svc.chatgpt_mode else {**svc.codex.status(), "mode": "apikey"},
        "jira": {"configured": svc.jira is not None, "project": svc.settings.jira_project_key,
                 "site": svc.settings.jira_base_url},
        "salesforce": {"configured": svc.sf is not None,
                       "loginUrl": svc.sf.login_url if svc.sf else svc.settings.sf_login_url},
        "graph": graph,
        "autoDeploy": svc.settings.auto_deploy,
    }


@app.post("/v1/codex/connect", dependencies=[Depends(require_key)])
def connect(body: ConnectBody, svc: Services = Depends(get_services), user: str = Depends(current_user)) -> dict:
    if svc.chatgpt_mode:
        if not user:
            raise HTTPException(400, "X-Salesforce-User is required to connect a developer's own Codex")
        return svc.sessions.connect(user)
    return {**svc.codex.connect(body.apiKey), "mode": "apikey"}


@app.get("/v1/codex/login", dependencies=[Depends(require_key)])
def codex_login(svc: Services = Depends(get_services), user: str = Depends(current_user)) -> dict:
    if not svc.chatgpt_mode:
        return {**svc.codex.status(), "mode": "apikey"}
    return svc.sessions.status(user)


@app.post("/v1/codex/login/complete", dependencies=[Depends(require_key)])
def codex_login_complete(body: CompleteLoginBody, svc: Services = Depends(get_services),
                         user: str = Depends(current_user)) -> dict:
    if not svc.chatgpt_mode or not user:
        raise HTTPException(400, "browser sign-in applies to a developer's own Codex session")
    try:
        return svc.sessions.complete(user, body.redirectUrl)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(502, f"Codex sign-in failed: {exc}") from exc


@app.get("/v1/codex/plan", dependencies=[Depends(require_key)])
def codex_plan(svc: Services = Depends(get_services), user: str = Depends(current_user)) -> dict:
    """The developer's Codex plan right now: limits used and credits."""
    if not svc.chatgpt_mode or not user:
        return {"available": False, "reason": "plan usage applies to a developer's own Codex sign-in"}
    snap = svc.sessions.plan_usage(user)
    return {"available": snap is not None, **(snap or {}),
            **({} if snap else {"reason": "not connected, or Codex did not report usage"})}


@app.post("/v1/codex/logout", dependencies=[Depends(require_key)])
def codex_logout(svc: Services = Depends(get_services), user: str = Depends(current_user)) -> dict:
    if not svc.chatgpt_mode or not user:
        raise HTTPException(400, "sign-out applies to a developer's own Codex session")
    return svc.sessions.logout(user)


@app.get("/v1/jira/tickets", dependencies=[Depends(require_key)])
def tickets(only_open: bool = True, svc: Services = Depends(get_services)) -> dict:
    jira = require_jira(svc)
    issues = jira.project_issues(only_open=only_open, max_results=50)
    return {"project": jira.project_key, "tickets": [
        {k: t[k] for k in ("key", "summary", "type", "status", "priority", "url")}
        for t in (simplify(i, jira.browse_url(i["key"])) for i in issues)]}


@app.post("/v1/requirements/chat", dependencies=[Depends(require_key)])
def chat(body: ChatBody, svc: Services = Depends(get_services), user: str = Depends(current_user)) -> dict:
    home = require_codex(svc, user)
    jira = require_jira(svc)
    conversation_id = body.conversationId or uuid.uuid4().hex[:16]
    run = svc.runs.create("requirement", {"message": body.message, "conversationId": conversation_id,
                                          "user": user})

    def work_codex(ctx: RunContext) -> dict:
        agent = CodexRequirementAgent(svc.codex_exec, svc.codex, home, jira, svc.graphs,
                                      svc.settings.workspace_root,
                                      cache_get=svc.runs.get_conversation, cache_set=svc.runs.set_conversation,
                                      plan_usage=lambda: svc.sessions.plan_usage(user))
        convo = svc.runs.get_conversation(conversation_id)
        history = convo.get("history", [])
        try:
            out = agent.chat(body.message, history, convo.get("last_spec_ticket"), ctx)
        finally:
            svc.sessions.save(user)
        history = (history + [{"role": "developer", "text": body.message},
                              {"role": "agent", "text": out["reply"]}])[-12:]
        svc.runs.set_conversation(conversation_id, {
            "history": history,
            "last_spec_ticket": (out["spec"] or {}).get("ticket_key") or convo.get("last_spec_ticket")})
        return {"reply": out["reply"], "spec": out["spec"], "conversationId": conversation_id}

    def work(ctx: RunContext) -> dict:
        agent = RequirementAgent(svc.openai_client_factory(), svc.codex.model, jira, svc.graphs)
        prev = svc.runs.get_conversation(conversation_id).get("previous_response_id")
        out = agent.chat(body.message, prev, ctx)
        svc.runs.set_conversation(conversation_id, {"previous_response_id": out["response_id"],
                                                    "last_spec_ticket": (out["spec"] or {}).get("ticket_key")})
        return {"reply": out["reply"], "spec": out["spec"], "conversationId": conversation_id}

    os.makedirs(svc.settings.workspace_root, exist_ok=True)
    svc.submit(run, work_codex if svc.chatgpt_mode else work)
    return {"runId": run["id"], "conversationId": conversation_id}


@app.post("/v1/developer/runs", dependencies=[Depends(require_key)])
def develop(body: DevelopBody, svc: Services = Depends(get_services), user: str = Depends(current_user)) -> dict:
    home = require_codex(svc, user)
    spec = dict(body.spec)
    key = body.ticketKey.strip().upper()
    if (spec.get("ticket_key") or key).upper() != key:
        raise HTTPException(400, "spec.ticket_key does not match ticketKey")
    spec["ticket_key"] = key
    if not spec.get("ready_for_development", False) and not body.override:
        raise HTTPException(409, "The Requirement agent marked this spec not ready; resolve the open questions "
                                 "or develop anyway with override")
    developer = svc.developer()
    if svc.jira and not spec.get("ticket"):
        spec["ticket"] = simplify(svc.jira.get_issue(key), svc.jira.browse_url(key))
        spec["ticket_url"] = spec["ticket"]["url"]
    run = svc.runs.create("developer", {"ticketKey": key, "user": user})
    after = (lambda: svc.sessions.save(user)) if home else None
    plan = (lambda: svc.sessions.plan_usage(user)) if home else None
    svc.submit(run, lambda ctx: developer.develop(run["id"], spec, ctx, codex_home=home, after_codex=after,
                                                  plan_usage=plan))
    return {"runId": run["id"]}


@app.get("/v1/runs/{run_id}", dependencies=[Depends(require_key)])
def get_run(run_id: str, svc: Services = Depends(get_services)) -> dict:
    if not RUN_ID.match(run_id):
        raise HTTPException(400, "bad run id")
    run = svc.runs.get(run_id)
    if not run:
        raise HTTPException(404, "no such run")
    return public_run(run)


@app.post("/v1/runs/{run_id}/deploy", dependencies=[Depends(require_key)])
def approve_deploy(run_id: str, svc: Services = Depends(get_services)) -> dict:
    run = get_run(run_id, svc)
    if run["kind"] != "developer" or run["status"] != "waiting_approval":
        raise HTTPException(409, f"run is {run['status']}, not waiting for approval")
    developer = svc.developer()
    svc.runs.update(run_id, status="queued")
    svc.submit(run, lambda ctx: developer.deploy(run_id, run["result"], ctx))
    return {"runId": run_id, "status": "queued"}


@app.post("/v1/runs/{run_id}/reject", dependencies=[Depends(require_key)])
def reject(run_id: str, svc: Services = Depends(get_services)) -> dict:
    run = get_run(run_id, svc)
    if run["status"] != "waiting_approval":
        raise HTTPException(409, f"run is {run['status']}, not waiting for approval")
    ctx = RunContext(svc.runs, run_id)
    ctx.step("Rejected by reviewer", "error")
    ctx.status("rejected")
    return {"runId": run_id, "status": "rejected"}


@app.post("/v1/graph/rebuild", dependencies=[Depends(require_key)])
def rebuild(svc: Services = Depends(get_services)) -> dict:
    if not svc.sf:
        raise HTTPException(503, "Salesforce is not configured on the gateway")
    run = svc.runs.create("graph", {})

    def work(ctx: RunContext) -> dict:
        s = svc.settings
        ctx.step("Reading Salesforce metadata", "running")
        g: Graph = SalesforceIngest(svc.sf, s.kg_standard_objects, s.kg_flow_metadata_max).run()
        ctx.step(f"Salesforce: {len(g.nodes)} nodes, {len(g.edges)} edges")
        if svc.jira:
            ctx.step("Reading Jira tickets", "running")
            ingest_jira(svc.jira, g)
            ctx.step(f"Jira merged: {len(g.nodes)} nodes, {len(g.edges)} edges")
        snap = svc.graphs.replace(g)
        ctx.step(f"Snapshot {snap} saved", detail="\n".join(g.notes[-20:]))
        return {"snapshotId": snap, **g.stats(), "notes": g.notes}

    svc.submit(run, work)
    return {"runId": run["id"]}


@app.get("/v1/graph/stats", dependencies=[Depends(require_key)])
def graph_stats(svc: Services = Depends(get_services)) -> dict:
    return {**svc.graphs.graph().stats(), "snapshot": svc.graphs.snapshot()}


@app.get("/v1/graph/search", dependencies=[Depends(require_key)])
def graph_search(q: str, svc: Services = Depends(get_services)) -> dict:
    return svc.graphs.graph().context_slice(q[:500])


@app.get("/v1/graph/schema", dependencies=[Depends(require_key)])
def graph_schema(svc: Services = Depends(get_services)) -> dict:
    g = svc.graphs.graph()
    return {**g.schema(), "nodes": len(g.nodes), "edges": len(g.edges), "snapshot": svc.graphs.snapshot(),
            "notes": g.notes[-10:]}


@app.get("/v1/graph/neighbourhood", dependencies=[Depends(require_key)])
def graph_neighbourhood(q: str = "", id: str = "", svc: Services = Depends(get_services)) -> dict:
    g = svc.graphs.graph()
    matches = [{"id": n.id, "type": n.node_type, "label": n.api_name or n.name} for n, _ in g.search(q[:200], 8)] if q else []
    centre = id if id in g.nodes else (matches[0]["id"] if matches else "")
    if not centre:
        raise HTTPException(404, f"nothing in the graph matches '{q or id}'")
    return {**g.ego(centre), "matches": matches}


@app.get("/v1/usage", dependencies=[Depends(require_key)])
def usage(days: int = 14, svc: Services = Depends(get_services)) -> dict:
    days = max(1, min(90, days))
    return summarize(svc.runs.list_recent(1000), days)
