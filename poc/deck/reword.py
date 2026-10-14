"""Rename MAD to the Agentic Harness across the deck: slide text, tables,
groups and speaker notes. Replacements run per text run, longest phrase first,
so formatting is kept. Anything still saying MAD afterwards is reported."""
import re

RULES = [
    (r"\bSDLC\b", "ADLC"),
    (r"Failures go round the fix loop a bounded number of times, then to a person\.",
     "Failures go round the fix loop up to five times, then the step stops and goes to a named owner."),
    (r"ASCENSION MAD APPROACH · MULTI-AGENT DELIVERY", "ASCENSION AGENTIC HARNESS"),
    (r"ASCENSION MAD APPROACH", "ASCENSION AGENTIC HARNESS"),
    (r"Ascension MAD Approach", "Ascension Agentic Harness"),
    (r"Multi-Agent Delivery on an", "An Agentic Harness on an"),
    (r"PHASE 2 · MULTI-AGENT DELIVERY \(MAD\)", "PHASE 2 · AGENTIC HARNESS"),
    (r"knowledge-graph AI multi-agent delivery \(MAD\)", "knowledge-graph Agentic Harness"),
    (r"[Mm]ulti-agent delivery \(MAD\)", "the Agentic Harness"),
    (r"Multi-Agent Delivery \(MAD\)", "Agentic Harness"),
    (r"MAD · High-level architecture", "Agentic Harness · High-level architecture"),
    (r"^MAD$", "Harness"),
    (r"MAD (Surface|Runtime|Registry|Context|Govern)", r"Harness \1"),
    (r"^Architecture: agents grounded in one graph", "Harness architecture: agents grounded in one graph"),
    (r"^Durable workflow controller$", "Harness run loop"),
    (r"^Approval service$", "Harness approvals"),
    (r"TOOL \+ POLICY GATEWAY \(MCP\)", "HARNESS TOOL GATEWAY (MCP + POLICY)"),
    (r"CHANGE PASSPORT \+ AUDIT", "HARNESS AUDIT TRAIL · CHANGE PASSPORT"),
    (r"^LEARNING LOOP", "EVAL + LEARNING LOOP"),
    (r"MAD ADDS", "HARNESS ADDS"),
    (r"WITH MAD", "WITH THE HARNESS"),
    (r"What MAD does", "What the harness does"),
    (r"Ready for MAD", "Ready for Harness"),
    (r"Shared MAD platform", "Shared Agentic Harness"),
    (r"MAD pilot", "Harness pilot"),
    (r"MAD agent team", "harness agent team"),
    (r"^MAD agent", "Harness agent"),
    (r"MAD agents?", lambda m: m.group(0).replace("MAD", "harness")),
    (r"^MAD is one AI agent team", "The Agentic Harness runs one AI agent team"),
    (r"With MAD keeps", "The harness figure keeps"),
    (r"(^|[.!?:]\s+|\n)MAD\b", r"\1The Agentic Harness"),
    (r"\bwith MAD\b", "with the Agentic Harness"),
    (r"\bWith MAD\b", "With the harness"),
    (r"\b(on|to|by|of|for|in|from|onto|into|without|under) MAD\b", r"\1 the Agentic Harness"),
    (r"\bMAD's\b", "the harness's"),
    (r"\bMAD\b", "the Agentic Harness"),
    (r"\bmad\.(start_run|status)\b", r"harness.\1"),
    (r"AI-DRIVEN MULTI-AGENT DELIVERY", "AI-DRIVEN SALESFORCE DELIVERY"),
    (r"MULTI-AGENT DELIVERY", "AGENTIC HARNESS"),
    (r"[Mm]ulti-[Aa]gent [Dd]elivery", "Agentic Harness"),
    # the model is chosen in the runtime; MCP keeps the tools portable, not the model
    (r"OpenAI Codex Enterprise;\nswappable via MCP", "OpenAI Codex Enterprise;\nmodel set in config;\ntools portable via MCP"),
    (r"Nothing in the architecture is locked to GCP",
     "Only the graph store is Google Cloud native, and it reloads from the JSON snapshot"),
    (r"model swappable behind MCP", "model set by config, tools via MCP"),
    (r"Codex Enterprise; the model is swappable\.",
     "Codex Enterprise. The model is set by configuration in the agent runtime; the tools sit behind MCP, so they "
     "stay the same whichever model runs them."),
    # the graph runs on Spanner Graph: Ascension is on Google Cloud, so the graph store is native there
    (r"In-memory directed property graph", "Spanner Graph: managed property graph on Google Cloud"),
    (r"O\(1\) node access; type indexes", "Indexed lookups by node id and type"),
    (r"save_to_file\(path\) / load_from_file\(path\); snapshot diffing",
     "Loaded from the versioned JSON snapshot; snapshot diffing"),
    (r"Query time < 0\.01s · ~1 MB typical · scales to 1M\+ nodes", "GQL queries in milliseconds · scales horizontally"),
    (r"load_from_json\(path\)", "load_snapshot(snapshot_id)"),
    (r"Semantica ContextGraph and the adapter API run as a Cloud Run service",
     "Spanner Graph holds the graph; the adapter API runs as a Cloud Run service"),
    (r"Scales to zero between syncs and queries",
     "Spanner Graph is native to Google Cloud: no separate graph database to buy or approve"),
    (r"The graph service is a container, so it runs anywhere containers run",
     "The adapter is a container, and the graph reloads from JSON into any graph store"),
    (r"query < 0\.01s", "GQL queries in milliseconds"),
    (r"(in )?under 0\.01 ?s(econds)?\b", "in milliseconds"),
    (r"In-memory knowledge graph", "Managed graph on Google Cloud"),
    (r"In-memory directed graph", "Spanner property graph (GQL)"),
    (r"^O\(1\) node access$", "Indexed lookups"),
    (r"^save / load_from_file$", "Load from JSON snapshot"),
    (r"Query < 0\.01s · 1M\+ nodes", "Millisecond GQL · scales out"),
    (r"loaded into the in-memory graph", "loaded into Spanner Graph"),
    (r"SemanticaGraphAdapter", "SpannerGraphAdapter"),
    (r"Semantica ContextGraph", "Spanner Graph"),
]
RULES = [(re.compile(p, re.M), r) for p, r in RULES]


def reword(text):
    for pat, rep in RULES:
        text = pat.sub(rep, text)
    return text


def _frames(shapes):
    for sh in shapes:
        if sh.shape_type == 6:                      # group
            yield from _frames(sh.shapes)
        if sh.has_text_frame:
            yield sh.text_frame
        if getattr(sh, "has_table", False) and sh.has_table:
            for row in sh.table.rows:
                for cell in row.cells:
                    yield cell.text_frame


def reword_slide(slide):
    frames = list(_frames(slide.shapes))
    if slide.has_notes_slide:
        frames.append(slide.notes_slide.notes_text_frame)
    left = []
    for tf in frames:
        for para in tf.paragraphs:
            for r in para.runs:
                new = reword(r.text)
                if new != r.text:
                    r.text = new
            t = "".join(r.text for r in para.runs)
            if re.search(r"\bMAD\b", t):
                left.append(t)
    return left
