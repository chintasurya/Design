"""Requirement agent: reads Jira, checks the knowledge graph, writes a spec.

A tool loop over the OpenAI Responses API. The model can only reach Jira and
the graph through the functions below, and it finishes a ticket analysis by
calling `submit_requirement_spec`, which is what the Developer agent consumes.
The conversation is chained with `previous_response_id`, so follow-up
questions in the LWC keep their context.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
from typing import Any

from ..codex import LEAN_NO_TOOLS
from ..graph.store import GraphService, now_iso
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

FIELD_TYPES = ["Text", "TextArea", "LongTextArea", "Number", "Currency", "Percent", "Checkbox", "Date",
               "DateTime", "Email", "Phone", "Url", "Picklist"]
NULLABLE_INT = {"type": ["integer", "null"]}
FIELD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "description": "Field definition, so the gateway can write the field without a model call",
    "properties": {
        "data_type": {"type": "string", "enum": FIELD_TYPES},
        "label": {"type": "string"},
        "help_text": {"type": "string", "description": "inlineHelpText shown to users"},
        "required": {"type": "boolean"},
        "length": NULLABLE_INT, "precision": NULLABLE_INT, "scale": NULLABLE_INT,
        "picklist_values": {"type": "array", "items": {"type": "string"}},
        "default_value": {"type": ["string", "null"]},
    },
    "required": ["data_type", "label", "help_text", "required", "length", "precision", "scale",
                 "picklist_values", "default_value"],
    "additionalProperties": False,
}

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
                    "field": {"anyOf": [FIELD_SCHEMA, {"type": "null"}],
                              "description": "For a CustomField to create: its definition. Null otherwise"},
                },
                "required": ["action", "type", "api_name", "description", "exists_in_org", "evidence", "field"],
                "additionalProperties": False,
            },
        },
        "reuse": {"type": "array", "items": {"type": "string"},
                  "description": "Existing components to reuse and how"},
        "impact": {"type": "array", "items": {"type": "string"},
                   "description": "Existing automation or components the change could affect"},
        "test_plan": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "approach": {
            "type": "object",
            "description": "Declarative first: Flow or configuration unless it cannot do the job",
            "properties": {
                "build_with": {"type": "string", "enum": ["Configuration", "Flow", "Trigger", "Apex", "LWC", "Mixed"]},
                "why_not_flow": {"type": "string",
                                 "description": "Required when build_with is Trigger, Apex or Mixed: why a Flow "
                                                "cannot do it. Empty for Flow or Configuration."},
                "existing_automation": {"type": "string",
                                        "description": "Triggers or record-triggered flows already on the object, "
                                                       "and how this change extends rather than duplicates them"},
            },
            "required": ["build_with", "why_not_flow", "existing_automation"],
            "additionalProperties": False,
        },
        "risk": {"type": "string", "enum": ["low", "medium", "high"]},
        "ready_for_development": {"type": "boolean"},
    },
    "required": ["ticket_key", "title", "summary", "acceptance_criteria", "approach", "components", "reuse", "impact",
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


def standard_api_name(api_name: str) -> str:
    """NAM-01/NAM-02: no underscores in custom names. Next_Step_Date__c ->
    NextStepDate__c, Opportunity.Next_Step__c -> Opportunity.NextStep__c."""
    prefix, _, name = api_name.rpartition(".")
    if not name.endswith("__c"):
        return api_name
    base = "".join(part[:1].upper() + part[1:] for part in name[:-3].split("_") if part)
    return (prefix + "." if prefix else "") + base + "__c"


def ground_spec(spec: dict, g: Any, tickets_seen: dict[str, dict]) -> dict:
    """Re-check every CustomField in the plan against the graph. The model's
    claim is not evidence; the graph's lookup is."""
    for comp in spec.get("components", []):
        # name new fields and objects to the standard now, not after a build round
        if comp.get("action") == "create" and comp.get("type") in ("CustomField", "CustomObject"):
            fixed = standard_api_name(comp.get("api_name", ""))
            obj, _, fld = comp.get("api_name", "").rpartition(".")
            taken = comp["type"] == "CustomField" and obj and g.field_exists(obj, fld).get("exists")
            if fixed != comp.get("api_name") and not taken:  # an existing field keeps its name
                old = comp["api_name"]
                comp["api_name"] = fixed
                comp["evidence"] = (comp.get("evidence", "") + f"; renamed from {old} (naming standard)").lstrip("; ")
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
    # GEN-01: declarative first. A code approach without a reason is not ready.
    approach = spec.get("approach") or {}
    if approach.get("build_with") in ("Trigger", "Apex", "Mixed") and not (approach.get("why_not_flow") or "").strip():
        spec["ready_for_development"] = False
        spec.setdefault("open_questions", []).append(
            "[GEN-01] The plan uses code but does not say why a Flow cannot do it. Explain, or plan a Flow.")
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
says it has no field-level security, plan to grant it. For every CustomField
to create, fill `field` (type, label, help text, length or precision) so it can
be built without a model; null for every other component. Custom API names have
no underscores: NextStepDate__c, not Next_Step_Date__c. Field access always
goes in the existing permission set HarnessAgentAccess (component type
PermissionSet, action modify), never a new permission set or a profile. Mark
ready_for_development false when the ticket is ambiguous. Otherwise set `spec`
to null and just answer.

Spec fields: approach.build_with is how it is built (Flow or Configuration
unless they cannot do it); why_not_flow is required for Trigger, Apex or Mixed;
existing_automation names triggers or flows already on the object. Each
component's evidence is what the graph says about it.

Keep the answer short, it is paid for per token: `reply` at most 6 "-" bullets
of one line each, plain text; spec strings one sentence each; no repetition
between `reply` and `spec`.
"""

def without_descriptions(schema: Any) -> Any:
    """The answer schema is sent with every call; its guidance lives in the
    instructions instead, once."""
    if isinstance(schema, dict):
        # a string "description" is an annotation; a dict one is a property named description
        return {k: without_descriptions(v) for k, v in schema.items()
                if not (k == "description" and isinstance(v, str))}
    if isinstance(schema, list):
        return [without_descriptions(v) for v in schema]
    return schema


CODEX_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"reply": {"type": "string"},
                   "spec": {"anyOf": [without_descriptions(SPEC_SCHEMA), {"type": "null"}]}},
    "required": ["reply", "spec"],
    "additionalProperties": False,
}


ANALYSIS = re.compile(r"\b(analy[sz]\w*|spec|prepare|refine|develop\w*|build|implement\w*|plan\w*|design|"
                      r"impact|break\w*|risk\w*|estimat\w*|approach|ready|review|reuse|exist\w*|how\b)", re.I)
LISTING = re.compile(r"\b(list|show|open|my|all)\b.*\btickets?\b|\btickets?\b.*\b(open|list)\b", re.I)
SPEC_REQUEST = re.compile(r"\b(analy[sz]\w*|spec|prepare|refine)\b", re.I)
BUILD = re.compile(r"\b(build|develop|implement|deliver)\b", re.I)
FORCE = re.compile(r"\b(again|refresh|re-?analy[sz]e|fresh)\b", re.I)
LINK_WORDS = {"TICKET_MENTIONS": "Mentions", "TICKET_IMPLEMENTED_BY": "Built by the Developer agent",
              "TICKET_ANALYSED_AS": "Analysed by the Requirement agent",
              "TICKET_PARENT_OF": "Parent of", "TICKET_LINKS_TO": "Linked to"}


def requirement_hash(ticket: dict) -> str:
    """What the requirement says, not when it was touched: a comment, a status
    change or the Developer agent's own updates do not make an analysis stale."""
    text = "\n".join([ticket.get("summary") or "", ticket.get("description") or "",
                      *(ticket.get("acceptance_criteria") or [])])
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:16]


def is_build_command(message: str) -> bool:
    """"build KAN-16", "Develop kan 16", "please implement KAN16": a short order
    to build a ticket, not a question that happens to contain the word."""
    words = re.findall(r"[A-Za-z0-9]+", message)
    return bool(BUILD.search(message)) and len(words) <= 7 and "?" not in message


def ticket_keys(message: str, project_key: str) -> list[str]:
    """Ticket keys as people type them: KAN-7, but also "KAN -7", "kan 7", "Kan- 7"."""
    found = TICKET_KEY.findall(message.upper())
    if project_key:
        loose = re.compile(rf"\b{re.escape(project_key)}\s*[-_]?\s*(\d+)\b", re.I)
        found += [f"{project_key.upper()}-{n}" for n in loose.findall(message)]
    return list(dict.fromkeys(found))[:3]


def model_ticket(t: dict) -> dict:
    """What the model needs from a ticket. The acceptance criteria are already in
    the description, so they are not sent twice; url, assignee and dates not at all."""
    out = {k: t.get(k) for k in ("key", "summary", "type", "status")}
    out["description"] = (t.get("description") or "")[:3000]
    if t.get("links"):
        out["links"] = [f"{x.get('relation')} {x.get('key')}: {x.get('summary')}" for x in t["links"]][:5]
    if t.get("recent_comments"):
        out["comments"] = [c[:300] for c in t["recent_comments"][-3:]]
    return out


def model_graph(slice_: dict) -> dict:
    """The graph slice as short lines instead of JSON objects with ids and scores."""
    def line(m: dict) -> str:
        p = m.get("properties") or {}
        bits = [p.get("label"), p.get("type") or p.get("data_type"), "custom" if p.get("custom") else None,
                "required" if p.get("required") else None, p.get("note"),
                f"on {p['trigger_object']}" if p.get("trigger_object") else None, p.get("status")]
        extra = ", ".join(str(b) for b in bits if b)
        return f"{m.get('type')} {m.get('api_name')}" + (f" ({extra})" if extra else "")
    return {"matches": [line(m) for m in slice_.get("matches", [])], "related": slice_.get("related", [])}


PLANNING_RULES = ("GEN-01", "GEN-04", "FLW-04", "TRG-01", "TRG-02", "TST-01")


def planning_instructions(guardrails) -> str:
    """The standards that decide *how* to build, appended to the agent's
    instructions. Only these few are sent; the Developer agent gets the rest."""
    if guardrails is None:
        return CODEX_INSTRUCTIONS
    rules = guardrails.by_id()
    lines = [f"- [{r}] {rules[r]['title']}: {rules[r]['rule']}" for r in PLANNING_RULES if r in rules
             and rules[r].get("severity") != "off"]
    return (CODEX_INSTRUCTIONS + "\nDevelopment standards to plan by (" + guardrails.pack().get("name", "")
            + "). Fill `approach` from them: Flow or configuration first; Trigger or Apex only with `why_not_flow`; "
              "check the graph for automation already on the object.\n" + "\n".join(lines) + "\n")


class CodexRequirementAgent:
    """Cheapest answer first:

    1. no model: reading a ticket or listing tickets is answered from Jira
       and the knowledge graph directly (0 tokens);
    2. stored analysis: a ticket analysed before, whose requirement has not
       changed, gets its spec back from the knowledge graph (0 tokens);
    3. lean Codex: real analysis runs Codex with these instructions in place
       of its ~13k-token coding-agent prompt, no tools, and a trimmed context.
    """

    def __init__(self, codex_exec, codex_conn, home: str, jira: JiraClient, graphs: GraphService,
                 workspace_root: str, analysis_get=None, analysis_set=None, plan_usage=None, guardrails=None):
        self.codex_exec = codex_exec
        self.codex_conn = codex_conn
        self.home = home
        self.jira = jira
        self.graphs = graphs
        self.workspace_root = workspace_root
        self.analysis_get = analysis_get or (lambda key: {})
        self.analysis_set = analysis_set or (lambda key, value: None)
        self.plan_usage = plan_usage or (lambda: None)
        self.guardrails = guardrails

    # -- lookups ---------------------------------------------------------------
    def _tickets(self, keys: list[str], ctx: RunContext) -> dict[str, dict]:
        tickets: dict[str, dict] = {}
        for key in keys:
            try:
                tickets[key] = simplify(self.jira.get_issue(key), self.jira.browse_url(key))
                ctx.step(f"Read {key}", detail=tickets[key].get("summary") or "")
            except Exception as exc:  # noqa: BLE001 - "not found" is an answer, not a failure
                ctx.step(f"{key} not found in Jira", "error", str(exc)[:200])
        return tickets

    def _graph_lines(self, key: str) -> list[str]:
        g = self.graphs.graph()
        grouped: dict[str, list[str]] = {}
        for e in g.out_edges(f"ticket:{key.lower()}"):
            n = g.nodes.get(e.to_id)
            if n:
                grouped.setdefault(LINK_WORDS.get(e.edge_type, e.edge_type), []).append(
                    f"{n.api_name or n.name} ({n.node_type})")
        return [f"- {label}: {', '.join(sorted(set(items)))}" for label, items in grouped.items()]

    # -- 0-token answers -------------------------------------------------------
    def _answer_ticket(self, t: dict) -> str:
        lines = [f"{t['key']} · {t['summary']}",
                 f"Status: {t.get('status')} · {t.get('type')} · Priority {t.get('priority') or '-'}"
                 f" · Assignee {t.get('assignee') or 'unassigned'}"]
        desc = (t.get("description") or "").split("Acceptance Criteria")[0].strip()
        if desc:
            lines += ["", desc[:700]]
        if t.get("acceptance_criteria"):
            lines += ["", "Acceptance criteria:"] + [f"- {a}" for a in t["acceptance_criteria"]]
        graph = self._graph_lines(t["key"])
        lines += ["", "In the knowledge graph:"] + (graph or ["- nothing linked to it yet"])
        lines += ["", "Answered from Jira and the knowledge graph, no model call. "
                      f"Say \"analyze {t['key']}\" for a development spec."]
        return "\n".join(lines)

    def _answer_list(self, ctx: RunContext, only_open: bool) -> str:
        issues = self.jira.project_issues(only_open=only_open, max_results=30)
        ctx.step(f"Listed {len(issues)} Jira tickets", detail=f"project {self.jira.project_key}")
        if not issues:
            return f"No {'open ' if only_open else ''}tickets in {self.jira.project_key}."
        rows = [simplify(i) for i in issues]
        head = f"{'Open' if only_open else 'All'} tickets in {self.jira.project_key} ({len(rows)}):"
        return "\n".join([head] + [f"- {r['key']} · {r['summary']} ({r['status']})" for r in rows]
                         + ["", "Answered from Jira, no model call."])

    def _no_model(self, ctx: RunContext, ticket: str | None) -> None:
        ctx.add_usage("requirement", "knowledge graph (no model call)", 0, 0, 0, 0, ticket, calls=0)

    # -- the turn --------------------------------------------------------------
    def chat(self, message: str, history: list[dict], last_ticket: str | None, ctx: RunContext) -> dict:
        keys = ticket_keys(message, self.jira.project_key)
        wants_analysis = bool(ANALYSIS.search(message))
        # only "analyze KAN-x" itself may reuse a stored spec; a new question about it may not
        spec_request = bool(keys) and (bool(SPEC_REQUEST.search(message)) or is_build_command(message))

        if keys and not wants_analysis:                      # 1. read a ticket: no model
            tickets = self._tickets(keys, ctx)
            ctx.step("Answered from Jira and the knowledge graph (no model call)")
            self._no_model(ctx, keys[0])
            reply = "\n\n".join(self._answer_ticket(t) for t in tickets.values()) or \
                f"{', '.join(keys)} was not found in {self.jira.project_key}."
            return {"reply": reply, "spec": None}
        if not keys and LISTING.search(message) and not wants_analysis:
            only_open = not re.search(r"\ball\b", message, re.I)
            reply = self._answer_list(ctx, only_open)
            ctx.step("Answered from Jira (no model call)")
            self._no_model(ctx, None)
            return {"reply": reply, "spec": None}

        if not keys and last_ticket:
            keys = [last_ticket]
        tickets = self._tickets(keys, ctx)
        key = next(iter(tickets), None)

        if key and spec_request and not FORCE.search(message) and len(tickets) == 1:   # 2. cache
            stored = self.analysis_get(key) or {}
            if stored.get("spec") and stored.get("requirement_hash") == requirement_hash(tickets[key]):
                when = (stored.get("at") or "")[:16].replace("T", " ")
                ctx.step(f"Reused the analysis of {key} stored in the knowledge graph (no model call)",
                         detail=f"analysed {when} UTC; summary, description and acceptance criteria unchanged")
                self._no_model(ctx, key)
                return {"reply": (stored.get("reply") or "").strip()
                        + f"\n\n(From the knowledge graph: {key} was analysed {when} UTC and its requirement has "
                          f"not changed, so no model was called. Say \"analyze {key} again\" to redo it.)",
                        "spec": stored["spec"]}
            if stored.get("spec"):
                ctx.step(f"{key} changed since it was analysed; analysing it again")

        # 3. lean Codex
        g = self.graphs.graph()
        text = " ".join([message] + [f"{t['summary']} {t['description']}" for t in tickets.values()])
        context: dict[str, Any] = {"jira_project": self.jira.project_key,
                                   "tickets": [model_ticket(t) for t in tickets.values()],
                                   "knowledge_graph": model_graph(g.context_slice(text, max_related=25,
                                                                                  max_matches=8))}
        if not tickets:
            context["project_tickets"] = [
                {k: t[k] for k in ("key", "summary", "status")}
                for t in (simplify(i) for i in self.jira.project_issues(only_open=False, max_results=30))]
        ctx.step(f"Queried knowledge graph: {len(context['knowledge_graph']['matches'])} matches")
        transcript = "\n".join(f"{h['role']}: {h['text'][:600]}" for h in history[-4:])
        prompt = ("CONTEXT:\n" + json.dumps(context, default=str, separators=(",", ":"))[:12000]
                  + ("\n\nEARLIER IN THIS CONVERSATION:\n" + transcript if transcript else "")
                  + "\n\nDEVELOPER'S MESSAGE:\n" + message)
        ctx.step("Requirement agent thinking on your Codex account (lean call)", "running")
        before = self.plan_usage()
        workspace = tempfile.mkdtemp(prefix="req-", dir=self.workspace_root)
        try:
            out = self.codex_exec(self.codex_conn, workspace, prompt, lambda line: None, home=self.home,
                                  sandbox="read-only", output_schema=CODEX_OUTPUT_SCHEMA,
                                  instructions=planning_instructions(self.guardrails), extra_args=LEAN_NO_TOOLS,
                                  timeout_s=self.codex_conn.settings.requirement_timeout_s)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)
        ctx.plan_usage(before, self.plan_usage())
        u = out.get("usage") or {}
        if u:
            ctx.add_usage("requirement", "codex (your ChatGPT sign-in)", u.get("input_tokens", 0),
                          u.get("output_tokens", 0), u.get("cached_input_tokens", 0), 0, key)
        if out.get("exit_code") not in (0, None) and not out.get("final_message"):
            raise RuntimeError("Codex did not answer: " + (out.get("log_tail") or "no output")[-400:])
        try:
            answer = json.loads(out.get("final_message") or "{}")
        except json.JSONDecodeError:
            answer = {"reply": out.get("final_message") or "", "spec": None}
        spec = answer.get("spec")
        reply = (answer.get("reply") or "").strip()
        if spec:
            spec = ground_spec(spec, g, tickets)
            ctx.step(f"Requirement spec ready for {spec.get('ticket_key')}",
                     detail=f"{len(spec.get('components', []))} components · risk {spec.get('risk')}")
            ctx.usage_ticket(spec.get("ticket_key"))
            sk = (spec.get("ticket_key") or key or "").upper()
            if sk in tickets:
                self.analysis_set(sk, {"spec": spec, "reply": reply, "at": now_iso(),
                                       "requirement_hash": requirement_hash(tickets[sk])})
                ctx.step(f"Analysis of {sk} stored in the knowledge graph")
        return {"reply": reply, "spec": spec}
