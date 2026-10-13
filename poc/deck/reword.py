"""Rename MAD to the Agentic Harness across the deck: slide text, tables,
groups and speaker notes. Replacements run per text run, longest phrase first,
so formatting is kept. Anything still saying MAD afterwards is reported."""
import re

RULES = [
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
