"""Requirement agent: reads Jira, checks the knowledge graph, writes a spec.

A tool loop over the OpenAI Responses API. The model can only reach Jira and
the graph through the functions below, and it finishes a ticket analysis by
calling `submit_requirement_spec`, which is what the Developer agent consumes.
The conversation is chained with `previous_response_id`, so follow-up
questions in the LWC keep their context.
"""
from __future__ import annotations

import json
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
        """Re-check every 'create CustomField' against the graph. The model's
        claim is not evidence; the graph's lookup is."""
        g = self.graphs.graph()
        for comp in spec.get("components", []):
            if comp.get("type") == "CustomField" and "." in comp.get("api_name", ""):
                obj, fld = comp["api_name"].split(".", 1)
                res = g.field_exists(obj, fld)
                if res.get("exists"):
                    comp["exists_in_org"] = True
                    comp["evidence"] = f"graph: {res.get('field')} already exists ({res.get('data_type')})"
                    if comp.get("action") == "create":
                        comp["action"] = "modify"
                        spec.setdefault("open_questions", []).append(
                            f"{res.get('field')} already exists; the plan was changed from create to modify. "
                            "Confirm it should be changed rather than reused as is.")
        key = spec.get("ticket_key", "").upper()
        if key in self.tickets_seen:
            spec["ticket_url"] = self.tickets_seen[key].get("url")
            spec["ticket"] = self.tickets_seen[key]
        return spec

    # -- loop ----------------------------------------------------------------
    def chat(self, message: str, previous_response_id: str | None, ctx: RunContext) -> dict:
        keys = TICKET_KEY.findall(message.upper())
        ctx.step("Requirement agent thinking", detail=f"ticket(s): {', '.join(keys)}" if keys else message[:200])
        kwargs: dict[str, Any] = {"model": self.model, "instructions": INSTRUCTIONS, "tools": TOOLS,
                                  "input": [{"role": "user", "content": message}]}
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        resp = self.client.responses.create(**kwargs)
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
        else:
            ctx.step("Stopped after the tool-call limit", "error", f"{MAX_TURNS} turns")
        return {"reply": (getattr(resp, "output_text", "") or "").strip(), "spec": self.spec,
                "response_id": resp.id}

