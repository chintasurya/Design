"""Requirement agent: reads Jira, checks the knowledge graph, writes a spec.

A tool loop over the OpenAI Responses API. The model can only reach Jira and
the graph through the functions below, and it finishes a ticket analysis by
calling `submit_requirement_spec`, which is what the Developer agent consumes.
The conversation is chained with `previous_response_id`, so follow-up
questions in the LWC keep their context.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from typing import Any

from ..graph.store import GraphService
from ..jira import TICKET_KEY, JiraClient, simplify
from ..runs import RunContext

MAX_TURNS = 10

INSTRUCTIONS = """\
You are the Requirement Agent for a Salesforce org. You work with a Jira project
and a knowledge graph of the org's metadata (objects, fields, record types, Apex,
triggers, flows, LWC, validation rules) plus the Jira tickets themselves.

How you work:
- Answer questions about Jira tickets using the Jira tools. Never invent ticket
  content; if a ticket does not exist, say so.
- When asked to analyze, refine, or prepare a ticket for development:
  1. Read the ticket with get_jira_ticket.
  2. Query the knowledge graph for every object, field and component the ticket
     touches. Use check_field_exists for every field the ticket wants to create:
     a field that already exists must be reused, never duplicated.
  3. Call submit_requirement_spec exactly once with the complete spec.
  4. Then reply with a short summary: what will be built, what already exists and
     will be reused, what could break, and open questions.
- Prefer declarative or small changes. Every Apex class you plan must come with a
  test class. Use API names the org actually has (from the graph).
- Mark ready_for_development false when the ticket is ambiguous, and list the
  open questions instead of guessing.
- Keep replies short and concrete. Use plain text with simple "-" bullets.
"""

SPEC_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "ticket_key": {"type": "string"},
        "title": {"type": "string"},
        "summary": {"type": "string", "description": "What the business wants, in two or three sentences"},
        "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
        "components": {
            "type": "array",
            "description": "Every metadata component to create or modify",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "modify"]},
                    "type": {"type": "string", "enum": ["CustomObject", "CustomField", "ApexClass", "ApexTrigger",
                                                         "LWC", "Flow", "ValidationRule", "PermissionSet",
                                                         "Layout", "Other"]},
                    "api_name": {"type": "string",
                                 "description": "Full API name, e.g. Account.Risk_Score__c or AccountRiskService"},
                    "description": {"type": "string"},
                    "exists_in_org": {"type": "boolean"},
                    "evidence": {"type": "string", "description": "Graph evidence for the existence claim"},
                },
                "required": ["action", "type", "api_name", "description", "exists_in_org", "evidence"],
                "additionalProperties": False,
            },
        },
        "reuse": {"type": "array", "items": {"type": "string"},
                  "description": "Existing components to reuse and how"},
        "impact": {"type": "array", "items": {"type": "string"},
                   "description": "Existing automation or components the change could affect"},
        "test_plan": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "ready_for_development": {"type": "boolean"},
    },
    "required": ["ticket_key", "title", "summary", "acceptance_criteria", "components", "reuse", "impact",
                 "test_plan", "open_questions", "risk", "ready_for_development"],
    "additionalProperties": False,
}

TOOLS: list[dict[str, Any]] = [
    {"type": "function", "name": "list_jira_tickets",
     "description": "List tickets in the configured Jira project, most recently updated first.",
     "parameters": {"type": "object", "properties": {
         "only_open": {"type": "boolean", "description": "Exclude tickets in a Done status"},
         "max_results": {"type": "integer", "description": "1 to 50"}},
         "required": ["only_open", "max_results"], "additionalProperties": False}},
    {"type": "function", "name": "search_jira",
     "description": "Search Jira with JQL. Restricted to the configured project.",
     "parameters": {"type": "object", "properties": {"jql": {"type": "string"}},
                    "required": ["jql"], "additionalProperties": False}},
    {"type": "function", "name": "get_jira_ticket",
     "description": "Read one ticket in full: description, acceptance criteria, links, recent comments.",
     "parameters": {"type": "object", "properties": {"key": {"type": "string"}},
                    "required": ["key"], "additionalProperties": False}},
    {"type": "function", "name": "query_knowledge_graph",
     "description": "Search the org knowledge graph with free text (object, field, class or business terms). "
                    "Returns matching components and the automation around them.",
     "parameters": {"type": "object", "properties": {"text": {"type": "string"}},
                    "required": ["text"], "additionalProperties": False}},
    {"type": "function", "name": "check_field_exists",
     "description": "Exact existence check for a field on an object, by API name or label.",
     "parameters": {"type": "object", "properties": {"object": {"type": "string"}, "field": {"type": "string"}},
                    "required": ["object", "field"], "additionalProperties": False}},
    {"type": "function", "name": "submit_requirement_spec",
     "description": "Submit the development-ready requirement spec for one ticket.",
     "parameters": SPEC_SCHEMA},
]


def ground_spec(spec: dict, g: Any, tickets_seen: dict[str, dict]) -> dict:
    """Re-check every CustomField in the plan against the graph. The model's
    claim is not evidence; the graph's lookup is."""
    for comp in spec.get("components", []):
        if comp.get("type") == "CustomField" and "." in comp.get("api_name", ""):
            obj, fld = comp["api_name"].split(".", 1)
            res = g.field_exists(obj, fld)
            if res.get("exists"):
                comp["exists_in_org"] = True
                comp["evidence"] = f"graph: {res.get('field')} already exists ({res.get('data_type') or 'type unknown'})"
                if res.get("note"):
                    comp["evidence"] += f"; {res['note']}"
                if comp.get("action") == "create":
                    comp["action"] = "modify"
                    spec.setdefault("open_questions", []).append(
                        f"{res.get('field')} already exists; the plan was changed from create to modify. "
                        "Confirm it should be changed rather than reused as is.")
    key = spec.get("ticket_key", "").upper()
    if key in tickets_seen:
        spec["ticket_url"] = tickets_seen[key].get("url")
        spec["ticket"] = tickets_seen[key]
    return spec


class RequirementAgent:
    def __init__(self, client, model: str, jira: JiraClient, graphs: GraphService):
        self.client = client
        self.model = model
        self.jira = jira
        self.graphs = graphs
        self.spec: dict | None = None
        self.tickets_seen: dict[str, dict] = {}

    # -- tools ---------------------------------------------------------------
    def _scoped_jql(self, jql: str) -> str:
        project = f'project = "{self.jira.project_key}"'
        if project.lower() in jql.lower() or f"project = {self.jira.project_key}".lower() in jql.lower():
            return jql
        order = ""
        if " order by " in jql.lower():
            idx = jql.lower().index(" order by ")
            jql, order = jql[:idx], jql[idx:]
        return f"{project} AND ({jql}){order}" if jql.strip() else project + order

    def _brief(self, issue: dict) -> dict:
        t = simplify(issue, self.jira.browse_url(issue["key"]))
        return {k: t[k] for k in ("key", "summary", "type", "status", "priority", "assignee", "url")}

    def call_tool(self, name: str, args: dict, ctx: RunContext) -> Any:
        if name == "list_jira_tickets":
            issues = self.jira.project_issues(bool(args.get("only_open")), max(1, min(50, int(args.get("max_results") or 20))))
            ctx.step(f"Listed {len(issues)} Jira tickets", detail=f"project {self.jira.project_key}")
            return [self._brief(i) for i in issues]
        if name == "search_jira":
            jql = self._scoped_jql(args["jql"])
            issues = self.jira.search(jql, 25)
            ctx.step(f"Searched Jira: {len(issues)} found", detail=jql)
            return [self._brief(i) for i in issues]
        if name == "get_jira_ticket":
            key = args["key"].strip().upper()
            t = simplify(self.jira.get_issue(key), self.jira.browse_url(key))
            self.tickets_seen[key] = t
            ctx.step(f"Read {key}", detail=t.get("summary") or "")
            return t
        if name == "query_knowledge_graph":
            g = self.graphs.graph()
            sl = g.context_slice(args["text"])
            ctx.step(f"Queried knowledge graph: {len(sl['matches'])} matches", detail=args["text"])
            return sl
        if name == "check_field_exists":
            res = self.graphs.graph().field_exists(args["object"], args["field"])
            verdict = "exists" if res.get("exists") else ("absent" if res.get("object_found") else "object not in graph")
            ctx.step(f"Field check {args['object']}.{args['field']}: {verdict}")
            return res
        if name == "submit_requirement_spec":
            self.spec = self._ground(args)
            ctx.step(f"Requirement spec ready for {self.spec.get('ticket_key')}",
                     detail=f"{len(self.spec.get('components', []))} components · risk {self.spec.get('risk')}")
            return {"accepted": True}
        return {"error": f"unknown tool {name}"}

    def _ground(self, spec: dict) -> dict:
        return ground_spec(spec, self.graphs.graph(), self.tickets_seen)

    # -- loop ----------------------------------------------------------------
    def _count(self, resp: Any, ctx: RunContext, ticket: str | None) -> None:
        u = getattr(resp, "usage", None)
        if u is None:
            return
        cached = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", 0) or 0
        reasoning = getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", 0) or 0
        ctx.add_usage("requirement", getattr(resp, "model", None) or self.model,
                      getattr(u, "input_tokens", 0) or 0, getattr(u, "output_tokens", 0) or 0,
                      cached, reasoning, ticket)

    def chat(self, message: str, previous_response_id: str | None, ctx: RunContext) -> dict:
        keys = TICKET_KEY.findall(message.upper())
        ctx.step("Requirement agent thinking", detail=f"ticket(s): {', '.join(keys)}" if keys else message[:200])
        kwargs: dict[str, Any] = {"model": self.model, "instructions": INSTRUCTIONS, "tools": TOOLS,
                                  "input": [{"role": "user", "content": message}]}
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        ticket = keys[0] if keys else None
        resp = self.client.responses.create(**kwargs)
        self._count(resp, ctx, ticket)
        for _ in range(MAX_TURNS):
            calls = [o for o in resp.output if getattr(o, "type", None) == "function_call"]
            if not calls:
                break
            outputs = []
            for call in calls:
                try:
                    result = self.call_tool(call.name, json.loads(call.arguments or "{}"), ctx)
                except Exception as exc:  # noqa: BLE001 - the model sees the error and can recover
                    ctx.step(f"Tool {call.name} failed", "error", str(exc)[:300])
                    result = {"error": str(exc)[:500]}
                outputs.append({"type": "function_call_output", "call_id": call.call_id,
                                "output": json.dumps(result, default=str)[:30000]})
            resp = self.client.responses.create(model=self.model, instructions=INSTRUCTIONS, tools=TOOLS,
                                                previous_response_id=resp.id, input=outputs)
            self._count(resp, ctx, ticket)
        else:
            ctx.step("Stopped after the tool-call limit", "error", f"{MAX_TURNS} turns")
        if self.spec:
            ctx.usage_ticket(self.spec.get("ticket_key"))
        return {"reply": (getattr(resp, "output_text", "") or "").strip(), "spec": self.spec,
                "response_id": resp.id}


# ---------------------------------------------------------------------------
# ChatGPT sign-in mode: the same agent, run through the developer's own Codex.
#
# A developer's Codex session only works through the Codex CLI, so this agent
# cannot hand the model live tools the way the Responses API loop above does.
# The gateway does the lookups first (the tickets named, or the open tickets,
# and the graph neighbourhood) and gives Codex the facts; Codex answers in a
# fixed JSON shape. Existence is still re-checked against the graph after.

CODEX_INSTRUCTIONS = """\
You are the Requirement Agent for a Salesforce org, answering in a chat inside
Salesforce. Everything you know about Jira and the org is in CONTEXT below;
it was looked up for this message. Do not run commands, open files or browse:
answer from CONTEXT only. If a ticket is not in CONTEXT, say it was not found.

When asked to analyze, refine or prepare a ticket for development, fill `spec`
completely: what to create or modify, with API names the org actually has
(from the graph), what already exists and must be reused, what could break,
a test plan, and open questions. Every Apex class needs a test class. A field
the graph lists as existing must be reused, never created again; if the graph
says it has no field-level security, plan to grant it. Mark
ready_for_development false when the ticket is ambiguous. Otherwise set `spec`
to null and just answer.

`reply` is what the developer reads: short, concrete, plain text with simple
"-" bullets.
"""

CODEX_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"reply": {"type": "string"}, "spec": {"anyOf": [SPEC_SCHEMA, {"type": "null"}]}},
    "required": ["reply", "spec"],
    "additionalProperties": False,
}


class CodexRequirementAgent:
    def __init__(self, codex_exec, codex_conn, home: str, jira: JiraClient, graphs: GraphService,
                 workspace_root: str):
        self.codex_exec = codex_exec
        self.codex_conn = codex_conn
        self.home = home
        self.jira = jira
        self.graphs = graphs
        self.workspace_root = workspace_root

    def _context(self, message: str, last_ticket: str | None, ctx: RunContext) -> tuple[dict, dict[str, dict]]:
        keys = list(dict.fromkeys(TICKET_KEY.findall(message.upper())))[:3]
        if not keys and last_ticket:
            keys = [last_ticket]
        tickets: dict[str, dict] = {}
        for key in keys:
            try:
                tickets[key] = simplify(self.jira.get_issue(key), self.jira.browse_url(key))
                ctx.step(f"Read {key}", detail=tickets[key].get("summary") or "")
            except Exception as exc:  # noqa: BLE001 - "not found" is an answer, not a failure
                ctx.step(f"{key} not found in Jira", "error", str(exc)[:200])
        context: dict[str, Any] = {"jira_project": self.jira.project_key, "tickets": list(tickets.values())}
        if not tickets:
            issues = self.jira.project_issues(only_open=False, max_results=30)
            context["project_tickets"] = [
                {k: t[k] for k in ("key", "summary", "type", "status", "priority", "assignee")}
                for t in (simplify(i) for i in issues)]
            ctx.step(f"Listed {len(issues)} Jira tickets", detail=f"project {self.jira.project_key}")
        text = " ".join([message] + [f"{t['summary']} {t['description']}" for t in tickets.values()])
        g = self.graphs.graph()
        context["knowledge_graph"] = g.context_slice(text)
        ctx.step(f"Queried knowledge graph: {len(context['knowledge_graph']['matches'])} matches")
        return context, tickets

    def chat(self, message: str, history: list[dict], last_ticket: str | None, ctx: RunContext) -> dict:
        context, tickets = self._context(message, last_ticket, ctx)
        transcript = "\n".join(f"{h['role']}: {h['text'][:1500]}" for h in history[-6:])
        prompt = (CODEX_INSTRUCTIONS + "\nCONTEXT:\n" + json.dumps(context, default=str)[:60000]
                  + ("\n\nEARLIER IN THIS CONVERSATION:\n" + transcript if transcript else "")
                  + "\n\nDEVELOPER'S MESSAGE:\n" + message)
        ctx.step("Requirement agent thinking on your Codex account", "running")
        workspace = tempfile.mkdtemp(prefix="req-", dir=self.workspace_root)
        try:
            out = self.codex_exec(self.codex_conn, workspace, prompt, lambda line: None, home=self.home,
                                  sandbox="read-only", output_schema=CODEX_OUTPUT_SCHEMA)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)
        u = out.get("usage") or {}
        if u:
            ticket = next(iter(tickets), None)
            ctx.add_usage("requirement", "codex (your ChatGPT sign-in)", u.get("input_tokens", 0),
                          u.get("output_tokens", 0), u.get("cached_input_tokens", 0), 0, ticket)
        if out.get("exit_code") not in (0, None) and not out.get("final_message"):
            raise RuntimeError("Codex did not answer: " + (out.get("log_tail") or "no output")[-400:])
        try:
            answer = json.loads(out.get("final_message") or "{}")
        except json.JSONDecodeError:
            answer = {"reply": out.get("final_message") or "", "spec": None}
        spec = answer.get("spec")
        if spec:
            spec = ground_spec(spec, self.graphs.graph(), tickets)
            ctx.step(f"Requirement spec ready for {spec.get('ticket_key')}",
                     detail=f"{len(spec.get('components', []))} components · risk {spec.get('risk')}")
            ctx.usage_ticket(spec.get("ticket_key"))
        return {"reply": (answer.get("reply") or "").strip(), "spec": spec}
