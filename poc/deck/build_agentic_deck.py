"""Build the Agentic Delivery client deck on the Universal Gap Framework template.

    python3 build_agentic_deck.py <Universal_Gap_Framework.pptx> <out.pptx>

The template's own architecture slides (5: Engineering Context, 6: Clinical
Network) are carried over byte for byte. Every other slide is drawn here in the
template's visual language: navy header band, teal eyebrow, Trenda IG type,
F4F6F9 cards ruled in D5D9DE, square markers, navy and light callout bars.
"""
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Emu, Inches, Pt

# Template palette, read from the UGF deck.
NAVY = "0E1B2E"
TEAL = "5FD0C0"
INK = "1A1A1A"
MUTE = "5A6573"
NOTE = "A9B4C2"
ON_DARK = "D8DEE6"
WHITE = "FFFFFF"
CARD = "F4F6F9"
CARD_ALT = "ECEFF3"
RULE = "D5D9DE"
BLUE = "1B6BC0"
JADE = "0E8A7D"
PURPLE = "6A1B9A"
PLUM = "7A4FC0"
ROSE = "C2185B"
AMBER = "C77400"
RED = "C62828"
GREEN = "2E7D32"
CYAN = "00757F"

DISPLAY_BOLD = "Trenda IG Display Bold"
DISPLAY_SEMI = "Trenda IG Display Semibold"
TEXT = "Trenda IG Text"
TEXT_SEMI = "Trenda IG Text Semibold"
TEXT_LIGHT = "Trenda IG Text Light"

KEEP_ENGINEERING = 5  # template slide numbers carried over unchanged
KEEP_CLINICAL = 6


def rgb(h):
    return RGBColor.from_string(h)


class Deck:
    def __init__(self, template):
        self.prs = Presentation(template)
        self.layout = self.prs.slide_layouts[0]
        self.originals = list(self.prs.slides._sldIdLst)

    # ---------- primitives ----------
    def new(self, dark=False):
        s = self.prs.slides.add_slide(self.layout)
        fill = s.background.fill
        fill.solid()
        fill.fore_color.rgb = rgb(NAVY if dark else WHITE)
        return s

    def rect(self, s, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, lw=0.75):
        sp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if fill:
            sp.fill.solid()
            sp.fill.fore_color.rgb = rgb(fill)
        else:
            sp.fill.background()
        if line:
            sp.line.color.rgb = rgb(line)
            sp.line.width = Pt(lw)
        else:
            sp.line.fill.background()
        sp.shadow.inherit = False
        return sp

    def sq(self, s, x, y, color, size=0.10):
        return self.rect(s, x, y, size, size, color)

    def text(self, s, x, y, w, h, paras, size=10.5, color=INK, font=TEXT,
             anchor=MSO_ANCHOR.TOP, align=None, bullet=False, spacing=None,
             after=None, caps=False, track=None):
        """paras: str, or list of str / list of (str, overrides dict) runs."""
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = anchor
        if isinstance(paras, str):
            paras = [paras]
        for i, para in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            if align:
                p.alignment = align
            if spacing:
                p.line_spacing = spacing
            if after is not None:
                p.space_after = Pt(after)
            pPr = p._p.get_or_add_pPr()
            if bullet:
                pPr.set("marL", "114300")
                pPr.set("indent", "-114300")
                bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
                pPr.append(bu)
            else:
                pPr.append(pPr.makeelement(qn("a:buNone"), {}))
            runs = para if isinstance(para, list) else [(para, {})]
            for chunk in runs:
                t, o = chunk if isinstance(chunk, tuple) else (chunk, {})
                r = p.add_run()
                r.text = t.upper() if caps else t
                f = r.font
                f.name = o.get("font", font)
                f.size = Pt(o.get("size", size))
                f.color.rgb = rgb(o.get("color", color))
                if o.get("italic"):
                    f.italic = True
                tr = o.get("track", track)
                if tr:
                    r._r.get_or_add_rPr().set("spc", str(tr))
        return tb

    def notes(self, s, text):
        ns = s.notes_slide
        if ns.notes_text_frame is None:
            # The template's notes master has no body placeholder, so add the
            # same "Notes Placeholder" its own notes slides carry.
            ns.shapes._spTree.append(parse_xml(
                '<p:sp %s><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/>'
                '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr>'
                '</p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
                % nsdecls("p", "a")))
        ns.notes_text_frame.text = text

    # ---------- template components ----------
    def header(self, s, eyebrow, title, note=None):
        self.rect(s, 0, 0, 13.33, 0.95, NAVY)
        self.text(s, 0.5, 0.15, 9.0, 0.21, eyebrow, 10.5, TEAL, DISPLAY_SEMI, caps=True, track=120)
        self.text(s, 0.5, 0.40, 10.0, 0.38, title, 22, WHITE, DISPLAY_BOLD)
        if note:
            self.text(s, 10.7, 0.24, 2.3, 0.5, note, 9, NOTE, TEXT_LIGHT, spacing=1.08)

    def label(self, s, x, y, w, t, color=MUTE):
        self.text(s, x, y, w, 0.17, t, 7.5, color, TEXT_SEMI, caps=True, track=60)

    def card(self, s, x, y, w, h, title, body, accent=BLUE, dark=False, size=10, bullets=True):
        self.rect(s, x, y, w, h, NAVY if dark else CARD, None if dark else RULE)
        self.sq(s, x + 0.2, y + 0.22, TEAL if dark else accent)
        self.text(s, x + 0.4, y + 0.13, w - 0.6, 0.3, title, 13.5, WHITE if dark else INK, DISPLAY_BOLD)
        if body:
            self.text(s, x + 0.2, y + 0.52, w - 0.4, h - 0.62, body, size,
                      ON_DARK if dark else INK, TEXT, bullet=bullets, spacing=1.02, after=7)

    def bar(self, s, y, t, dark=True, h=None, size=None):
        # Template positions: light bar 5.86" x 0.62", navy bar 6.62" x 0.54".
        if y is None:
            y = 6.62 if dark else 5.86
        if h is None:
            h = 0.54 if dark else 0.62
        self.rect(s, 0.12, y, 13.09, h, NAVY if dark else CARD, None if dark else RULE)
        self.sq(s, 0.30 if dark else 0.32, y + h / 2 - 0.05, TEAL if dark else BLUE)
        self.text(s, 0.5, y, 12.6, h, t, size or (11 if dark else 10.5), WHITE if dark else INK,
                  TEXT, anchor=MSO_ANCHOR.MIDDLE)

    def badge(self, s, x, y, w, t, fill, h=0.22):
        self.rect(s, x, y, w, h, fill)
        self.text(s, x, y, w, h, t, 6.8, WHITE, TEXT_SEMI, anchor=MSO_ANCHOR.MIDDLE,
                  align=PP_ALIGN.CENTER, caps=True, track=40)

    def arrow(self, s, x, y, w=0.28, h=0.18, color="9AA7B5"):
        return self.rect(s, x, y, w, h, color, shape=MSO_SHAPE.RIGHT_ARROW)

    # ---------- ordering ----------
    def finish(self, order, out):
        lst = self.prs.slides._sldIdLst
        ids = list(lst)
        keep = {KEEP_ENGINEERING: self.originals[KEEP_ENGINEERING - 1],
                KEEP_CLINICAL: self.originals[KEEP_CLINICAL - 1]}
        for sid in self.originals:
            if sid not in keep.values():
                self.prs.part.drop_rel(sid.get(qn("r:id")))
        for sid in ids:
            lst.remove(sid)
        for item in order:
            lst.append(keep[item] if isinstance(item, int) else item)
        self.prs.save(out)


def build(template, out):
    d = Deck(template)
    S = {}

    # 1 Cover
    s = d.new(dark=True)
    d.sq(s, 0.9, 2.05, TEAL, 0.16)
    d.text(s, 1.2, 2.0, 9, 0.3, "AI-driven delivery · Proposal", 12, TEAL, DISPLAY_SEMI, caps=True, track=150)
    d.text(s, 0.9, 2.5, 11, 1.6, ["Agentic Delivery", "for Ascension"], 44, WHITE, DISPLAY_BOLD, spacing=0.95)
    d.text(s, 0.9, 4.3, 9.4, 0.9, "One knowledge graph and a team of AI agents that take a business request "
           "to a tested, deployed Salesforce change, with people approving every step.", 15, ON_DARK, TEXT_LIGHT, spacing=1.15)
    d.text(s, 0.9, 6.55, 9, 0.3, "Consumer and Care Engagement tiles  ·  [Date]", 10.5, NOTE, TEXT_LIGHT)
    d.notes(s, "Open with the outcome, not the technology. Today a pod of four to fourteen people carries a request "
            "from business conversation to production. This proposal shows how a PM and a Tech Lead, working with a "
            "team of AI agents and one shared knowledge graph of the Ascension org, can carry the same request, with a "
            "person approving every decision. We are asking for a four-month pilot on one pod before any wider change.")
    S["cover"] = s

    # 2 Today
    s = d.new()
    d.header(s, "Where we are today", "Delivery runs on many pods and on what people remember",
             "Two tiles, nine to ten pods, one shared org.")
    stats = [("2", "Tiles: Consumer and Care Engagement"), ("9–10", "Pods, four to five in each tile"),
             ("$117K", "Network Services pod, 4 people"), ("~$2.47M", "VBC pod, 14 people")]
    w = (13.09 - 3 * 0.2) / 4
    for i, (n, l) in enumerate(stats):
        x = 0.12 + i * (w + 0.2)
        d.rect(s, x, 1.2, w, 2.0, CARD, RULE)
        d.text(s, x + 0.25, 1.45, w - 0.5, 0.8, n, 40, NAVY, DISPLAY_BOLD)
        d.text(s, x + 0.25, 2.4, w - 0.5, 0.7, l, 12, MUTE, TEXT)
    pains = [("Knowledge lives in people", "What already exists in the org, and why, sits in a few heads rather than in a system anyone can ask."),
             ("The same job, built twice", "Healthcare Facility Network records are created in Apex in some scenarios and in Flow in others."),
             ("A queue at every hand-off", "Business analysis, design, build, test and release each wait on the step before.")]
    w = (13.09 - 2 * 0.2) / 3
    for i, (t, b) in enumerate(pains):
        x = 0.12 + i * (w + 0.2)
        d.card(s, x, 3.4, w, 2.26, t, [b], accent=[BLUE, ROSE, AMBER][i], size=12.5, bullets=False)
    d.bar(s, None, "The problem is not how fast code is written. It is that nobody can see what already exists before writing it.", dark=False)
    d.bar(s, None, "Agents make building faster. Without org knowledge, they also make duplicate and conflicting work faster.")
    d.notes(s, "Two tiles, each with four to five pods. Two examples show the range: the Network Services pod is four "
            "people at about $117K, and the VBC pod is fourteen people at roughly $2.47M. Knowledge of what already "
            "exists lives in people, so the same capability gets built twice. A concrete example: Healthcare Facility "
            "Network records are created by Apex in some scenarios and by Flow in others.")
    S["today"] = s

    # 3 Proof
    s = d.new()
    d.header(s, "What we have already proven", "Agents are already shortening delivery at Ascension",
             "Source: Agentifying Ascension Ways of Working.")
    res = [("Health Cloud", ["1–2 weeks", "→ 2–4 days"], "Implementation time with the latest agent-assisted approach."),
           ("Marketing Cloud", ["90 days", "→ 15–20 days"], "About 80% lower recorded completion time, around 75 fewer calendar days."),
           ("QA and test design", "75–85%", "Of initial test-case preparation done by agents, then reviewed by people.")]
    w = (13.09 - 2 * 0.2) / 3
    for i, (k, n, b) in enumerate(res):
        x = 0.12 + i * (w + 0.2)
        d.rect(s, x, 1.2, w, 3.05, CARD, RULE)
        d.sq(s, x + 0.25, 1.47, [JADE, BLUE, PURPLE][i])
        d.text(s, x + 0.45, 1.4, w - 0.7, 0.25, k, 9, MUTE, TEXT_SEMI, caps=True, track=80)
        d.text(s, x + 0.25, 1.8, w - 0.5, 1.2, n, 30, NAVY, DISPLAY_BOLD, spacing=0.95)
        d.text(s, x + 0.25, 3.25, w - 0.5, 0.9, b, 12, INK, TEXT, spacing=1.05)
    d.rect(s, 0.12, 4.45, 13.09, 1.85, NAVY)
    d.sq(s, 0.32, 4.69, TEAL)
    d.text(s, 0.52, 4.6, 12.4, 0.3, "Built so far", 13.5, WHITE, DISPLAY_BOLD)
    d.text(s, 0.32, 5.05, 12.6, 1.15,
           ["7 UI agents, 4 backend agents and 4 QA agents.",
            "From Jira context and architecture through development, review, unit tests, and Zephyr and Copado automation.",
            "Human review remains the validation point at every step."],
           11.5, ON_DARK, TEXT, bullet=True, after=5)
    d.bar(s, 6.54, "This proposal joins these agents into one governed flow, and gives them the one thing they lack.", dark=False)
    d.notes(s, "This is not a greenfield idea. Agents are already in use across UI, backend and QA at Ascension. Health "
            "Cloud implementation went from one to two weeks to two to four days. Marketing Cloud recorded about 80 "
            "percent lower completion time. QA agents prepare 75 to 85 percent of initial test cases, which people "
            "then review. The point of this proposal is to join these agents into one governed flow.")
    S["proof"] = s

    # 4 Gap
    s = d.new()
    d.header(s, "The missing piece", "Every agent knows the ticket. None knows the org.",
             "Both examples measured in an Ascension sandbox.")
    d.rect(s, 0.12, 1.2, 13.09, 1.55, NAVY)
    d.sq(s, 0.4, 1.53, TEAL, 0.14)
    d.text(s, 0.75, 1.42, 12.1, 1.2,
           "None of today's agents knows what already exists in the Salesforce org, or what a change will break.",
           22, WHITE, DISPLAY_BOLD, spacing=1.0)
    ex = [("A field built twice",
           "Asked to add an Effective From Date field to Healthcare Facility, an assistant builds it. The field already "
           "exists: one of 135 on that object, with 17 automations running on it.", ROSE),
          ("Two paths drifting apart",
           "Healthcare Facility Network creation lives half in Apex and half in Flow. Change one without seeing the "
           "other and the two drift apart.", AMBER)]
    w = (13.09 - 0.2) / 2
    for i, (t, b, c) in enumerate(ex):
        d.card(s, 0.12 + i * (w + 0.2), 2.95, w, 2.71, t, [b], accent=c, size=13.5, bullets=False)
    d.bar(s, None, "Coding assistants are good at writing code. Neither one of them can see the org.", dark=False)
    d.bar(s, None, "The fix is a knowledge graph of the org that every agent checks before it acts.")
    d.notes(s, "Slow down here. Coding agents are good at writing code; what they cannot do is see the org. Both "
            "examples are real and measured in the Ascension sandbox. Healthcare Facility has 135 fields and 17 pieces "
            "of automation; a request to create a field that already exists would be built again. HFN creation is "
            "split between Apex and Flow, so a change to one path silently diverges from the other.")
    S["gap"] = s

    # 5 Solution
    s = d.new()
    d.header(s, "The solution", "One front door, a team of agents, one knowledge graph",
             "Agents reach the graph and systems through MCP.")
    y0, h0 = 1.2, 3.7
    d.rect(s, 0.12, y0, 2.1, h0, CARD, RULE)
    d.sq(s, 0.32, y0 + 0.25, BLUE)
    d.text(s, 0.52, y0 + 0.16, 1.6, 0.6, "PM and Tech Lead", 13.5, INK, DISPLAY_BOLD)
    d.text(s, 0.32, y0 + 0.6, 1.75, 2.4, ["Ask in plain English.", "Approve at every gate."], 11.5, INK, TEXT, after=8)
    d.arrow(s, 2.3, y0 + h0 / 2 - 0.09)
    d.rect(s, 2.66, y0, 2.3, h0, NAVY)
    d.sq(s, 2.86, y0 + 0.25, TEAL)
    d.text(s, 3.06, y0 + 0.16, 1.8, 0.3, "Codex", 13.5, WHITE, DISPLAY_BOLD)
    d.text(s, 2.86, y0 + 0.6, 1.95, 2.6, ["The front door.", "Its orchestrator routes each request to the right agents."],
           11.5, ON_DARK, TEXT, after=8)
    d.arrow(s, 5.04, y0 + h0 / 2 - 0.09)
    ax, aw = 5.4, 4.6
    d.rect(s, ax, y0, aw, h0, CARD, RULE)
    d.sq(s, ax + 0.2, y0 + 0.25, PURPLE)
    d.text(s, ax + 0.4, y0 + 0.16, 3.5, 0.3, "Agent team", 13.5, INK, DISPLAY_BOLD)
    chips = ["Requirements", "Impact & Reuse", "Jira", "Architect", "Confluence", "Developer",
             "Review", "Test", "QA automation", "Deployment", "Support & RCA", "Orchestrator"]
    cw, ch = (aw - 0.4 - 0.15) / 2, 0.4
    for i, c in enumerate(chips):
        cx = ax + 0.2 + (i % 2) * (cw + 0.15)
        cy = y0 + 0.62 + (i // 2) * (ch + 0.08)
        d.rect(s, cx, cy, cw, ch, WHITE, RULE)
        d.text(s, cx + 0.12, cy, cw - 0.2, ch, c, 10, INK, TEXT_SEMI, anchor=MSO_ANCHOR.MIDDLE)
    d.rect(s, 10.08, y0 + h0 / 2 - 0.2, 0.3, 0.16, CYAN, shape=MSO_SHAPE.RIGHT_ARROW)
    d.rect(s, 10.08, y0 + h0 / 2 + 0.04, 0.3, 0.16, CYAN, shape=MSO_SHAPE.LEFT_ARROW)
    gx = 10.46
    d.rect(s, gx, y0, 13.21 - gx, h0, "E3F2F4", CYAN, lw=1.25)
    d.sq(s, gx + 0.2, y0 + 0.25, CYAN)
    d.text(s, gx + 0.4, y0 + 0.16, 2.2, 0.6, "Ascension Knowledge Graph", 13.5, INK, DISPLAY_BOLD)
    d.text(s, gx + 0.2, y0 + 0.95, 13.21 - gx - 0.4, 2.5,
           ["On Google Cloud, built on the Universal Gap Framework.",
            "Every component, ticket and design page, and how they connect."], 11.5, INK, TEXT, after=8)
    w = (13.09 - 0.2) / 2
    for i, (k, v) in enumerate([("The graph reads from, read-only", "Salesforce metadata  ·  Git and Copado  ·  Jira  ·  Confluence  ·  Drive"),
                                ("Agents act through, with approval", "Jira tickets  ·  Confluence pages  ·  Git pull requests  ·  Copado deployments")]):
        x = 0.12 + i * (w + 0.2)
        d.rect(s, x, 5.1, w, 1.0, CARD, RULE)
        d.label(s, x + 0.2, 5.27, w - 0.4, k, BLUE)
        d.text(s, x + 0.2, 5.57, w - 0.4, 0.4, v, 11.5, INK, TEXT)
    d.bar(s, None, "Codex asks the graph. It never scans the org, and never invents a dependency.")
    d.notes(s, "Three pieces. Codex is the single place a PM or Tech Lead types a request. Behind it, an orchestrator "
            "hands work to specialist agents, most of which Ascension already has. Every agent checks the Ascension "
            "Knowledge Graph before acting. The graph is read-only towards source systems; agents change things only "
            "through Jira, Confluence, Git pull requests and Copado, and only after approval. Agents reach the graph "
            "and the systems through MCP, the open tool standard Codex supports, so the model can change without "
            "rebuilding anything.")
    S["solution"] = s

    # 6 Journey
    s = d.new()
    d.header(s, "How a request flows", "One request, from business ask to production",
             "Four human gates. Everything else is automated.")
    stages = [("1 · Understand", BLUE, ["Request typed in Codex", "Graph returns exists, reuse or impact",
                                        "Story and acceptance criteria drafted"], "Gate 1 · PM and Tech Lead approve scope", True),
              ("2 · Plan", JADE, ["Jira ticket in the current or next sprint", "Flow, trigger or LWC chosen from facts",
                                  "Design page published to Confluence"], "Gate 2 · Tech Lead approves design", True),
              ("3 · Build", PURPLE, ["Code built to Ascension standards", "Review agent checks quality and security",
                                     "Pull request raised in Git"], "Gate 3 · Tech Lead approves the pull request", True),
              ("4 · Verify", ROSE, ["Unit tests and coverage", "Regression chosen by what the change touches",
                                    "Zephyr cases, Copado automation"], "Automatic · Jira moves to QA with results", False),
              ("5 · Release", CYAN, ["Copado deploys to QA and UAT", "Release notes and rollback plan",
                                     "Graph re-synced with the change"], "Gate 4 · CAB approves production", True)]
    w = (13.09 - 4 * 0.12) / 5
    for i, (t, c, items, gate, is_gate) in enumerate(stages):
        x = 0.12 + i * (w + 0.12)
        d.rect(s, x, 1.2, w, 0.55, c)
        d.text(s, x + 0.15, 1.2, w - 0.3, 0.55, t, 13.5, WHITE, DISPLAY_BOLD, anchor=MSO_ANCHOR.MIDDLE)
        d.rect(s, x, 1.75, w, 3.1, WHITE, RULE)
        d.text(s, x + 0.15, 1.95, w - 0.3, 2.8, items, 11.5, INK, TEXT, bullet=True, after=10, spacing=1.02)
        d.rect(s, x, 4.85, w, 0.85, "FDF1DE" if is_gate else "EAF1FB", RULE)
        d.sq(s, x + 0.15, 5.01, AMBER if is_gate else BLUE)
        d.text(s, x + 0.33, 4.93, w - 0.45, 0.72, gate, 10, INK, TEXT_SEMI, spacing=1.0)
    d.bar(s, None, "Every step is recorded on the Jira ticket: request, evidence, design, code, tests and deployment, traceable end to end.", dark=False)
    d.bar(s, None, "Jira status moves on its own: Ticket created → In progress → QA → Done.")
    d.notes(s, "Walk this left to right. The request starts in Codex. Before anything is written, the graph says whether "
            "it already exists, can be reused, or what it will affect; the PM and Tech Lead approve the scope. Only then "
            "is a Jira ticket raised, in the current sprint or the next one if the current sprint is closed. The "
            "architect agent chooses Flow, trigger or LWC from graph facts and publishes the design to Confluence; the "
            "Tech Lead approves it. Code is built and reviewed by agents, and the Tech Lead approves the pull request. "
            "Tests run automatically and Jira moves to QA. Copado deploys to QA and UAT; production still goes through "
            "Ascension's existing CAB.")
    S["journey"] = s

    # 7 Agents
    s = d.new()
    d.header(s, "The agent team", "Twelve agents, six already built at Ascension",
             "Built · Extend · New, against the agents in use today.")
    agents = [("Orchestrator", "BUILT", "Routes requests and enforces every gate"),
              ("Requirements", "NEW", "Turns business notes into stories and acceptance criteria"),
              ("Impact & Reuse", "EXTEND", "Does it exist? What will it break? About 30% built"),
              ("Jira", "EXTEND", "Raises the ticket in the right sprint and keeps status current"),
              ("Architect", "BUILT", "Chooses Flow, trigger or LWC from graph facts"),
              ("Confluence", "EXTEND", "Writes the design page, then the as-built record"),
              ("Developer", "BUILT", "Builds Apex, Flow and LWC to Ascension standards"),
              ("Review", "BUILT", "Checks quality, security and coding standards"),
              ("Test", "BUILT", "Unit and regression tests, chosen by blast radius"),
              ("QA automation", "BUILT", "Zephyr test cases and Copado functional automation"),
              ("Deployment", "NEW", "Deploys through Copado to QA and UAT, with rollback"),
              ("Support & RCA", "NEW", "Finds what changed when an incident hits")]
    col = {"BUILT": JADE, "EXTEND": BLUE, "NEW": AMBER}
    w, h = (13.09 - 3 * 0.15) / 4, 1.6
    for i, (n, st, b) in enumerate(agents):
        x = 0.12 + (i % 4) * (w + 0.15)
        y = 1.2 + (i // 4) * (h + 0.15)
        d.rect(s, x, y, w, h, CARD if i % 2 == 0 else CARD_ALT, RULE)
        d.text(s, x + 0.2, y + 0.16, w - 1.2, 0.3, n, 13.5, INK, DISPLAY_BOLD)
        d.badge(s, x + w - 0.85, y + 0.2, 0.65, st, col[st])
        d.text(s, x + 0.2, y + 0.62, w - 0.4, 0.9, b, 11.5, MUTE, TEXT, spacing=1.05)
    d.bar(s, 6.62, "Six built, three extended, three new. Support & RCA matters most: pods spend real time on production issues.")
    d.notes(s, "Six of these twelve exist today in the Ascension UI, backend and QA agent sets. Three are extensions: the "
            "Jira and Confluence agents read today and need to write; the Impact and Reuse agent is the knowledge-graph "
            "work, about 30 percent built and running in a sandbox. Three are new: Requirements, Deployment through "
            "Copado, and Support and RCA, because pods spend real time on production issues and the headcount case "
            "does not hold without it.")
    S["agents"] = s

    # 9 Pack (between the two template architecture slides)
    s = d.new()
    d.header(s, "One framework, two packs", "Change the nouns. The engine does not notice.",
             "The delivery graph and the clinical network graph share one core.")
    cols = [("FRAMEWORK", NAVY, 2.6), ("CLINICAL NETWORK", ROSE, 2.9), ("ENGINEERING DELIVERY", PURPLE, 3.1)]
    rows = [("Demand side", "Patient", "Requirement or request"),
            ("Supply side", "Provider, facility", "Component, service, team"),
            ("Capability", "Specialty plus privilege", "Language, framework, API"),
            ("Offering", "Service line", "Feature or change"),
            ("Interaction", "Encounter", "Deployment, incident"),
            ("Commitment", "Appointment", "Work item"),
            ("Adequacy rule", "CMS time and distance", "Architecture standard or SLA"),
            ("Identity spine", "NPI, TIN, CCN, EMPI", "Repo and component id")]
    tw = sum(c[2] for c in cols)
    x = 0.12
    for t, c, cw in cols:
        d.rect(s, x, 1.2, cw - 0.04, 0.34, c)
        d.text(s, x + 0.12, 1.2, cw - 0.2, 0.34, t, 8, WHITE, TEXT_SEMI, anchor=MSO_ANCHOR.MIDDLE, track=40)
        x += cw
    for r, row in enumerate(rows):
        y = 1.6 + r * 0.51
        d.rect(s, 0.12, y, tw - 0.04, 0.47, WHITE if r % 2 == 0 else CARD, RULE)
        x = 0.12
        for k, (v, (_, _, cw)) in enumerate(zip(row, cols)):
            d.text(s, x + 0.12, y, cw - 0.2, 0.47, v, 10.5, INK if k == 0 else MUTE,
                   TEXT_SEMI if k == 0 else TEXT, anchor=MSO_ANCHOR.MIDDLE)
            x += cw
    rx = 0.12 + tw + 0.16
    d.card(s, rx, 1.2, 13.21 - rx, 4.45, "Why it matters to Ascension",
           ["The core is built once: storage, graph runtime and gap engines.",
            "The delivery pilot builds the same core the Clinical Network graph runs on.",
            "A new use is a pack: five declarations and their connectors, not a new build."], dark=True, size=12)
    d.bar(s, None, "A county with demand and no credentialed cardiologist is the same query as a requirement with no component that implements it.", dark=False)
    d.bar(s, None, "The investment in this pilot is also an investment in the clinical network work.")
    d.notes(s, "This is the commercial point. The delivery graph is the engineering delivery pack of the Universal Gap "
            "Framework, the same core that runs the Clinical Network graph shown next. In both, a gap is a missing path "
            "between demand and supply. The core, meaning storage, the graph runtime and the gap engines, is built "
            "once; each new use declares its nouns, identity spine, rules and connectors.")
    S["pack"] = s

    # 11 Decide
    s = d.new()
    d.header(s, "Design from evidence", "Flow or trigger? The graph decides from facts",
             "Illustrative request. Rules are a draft.")
    lw = 6.3
    d.rect(s, 0.12, 1.2, lw, 1.15, CARD, RULE)
    d.label(s, 0.32, 1.32, lw - 0.4, "Example request")
    d.text(s, 0.32, 1.58, lw - 0.4, 0.65, "“When a provider Account is approved, create its Healthcare Facility Network record.”",
           12, INK, TEXT, spacing=1.05)
    d.rect(s, 0.12, 2.5, lw, 2.0, CARD, RULE)
    d.label(s, 0.32, 2.64, lw - 0.4, "What the graph returns")
    d.text(s, 0.32, 2.94, lw - 0.4, 1.5, ["AHC_AccountTrigger already runs on Account",
                                          "HFN records are already created, in Apex for some scenarios and in Flow for others",
                                          "Record-triggered flows already run on Account"],
           11.5, INK, TEXT, bullet=True, after=7)
    d.rect(s, 0.12, 4.65, lw, 1.05, "E3F2F4", CYAN, lw=1.25)
    d.label(s, 0.32, 4.78, lw - 0.4, "Recommendation", CYAN)
    d.text(s, 0.32, 5.06, lw - 0.4, 0.5, "Extend the existing creation logic. Do not add a third path.", 13.5, INK, DISPLAY_BOLD)
    rx = 0.12 + lw + 0.2
    rw = 13.21 - rx
    d.label(s, rx, 1.24, rw, "Rules the Architect agent applies")
    rules = [("When the graph shows…", "Build…"), ("The logic already exists", "Nothing new: reuse it"),
             ("A trigger handler on the object", "An extension to the handler"),
             ("A same-record update, no Apex on the object", "A before-save flow"),
             ("Callouts, high volume or complex logic", "Apex, through the handler"),
             ("Guided steps for a user", "A screen flow or LWC")]
    for r, (a, b) in enumerate(rules):
        y = 1.5 + r * 0.65
        head = r == 0
        d.rect(s, rx, y, rw, 0.6, NAVY if head else (WHITE if r % 2 else CARD), None if head else RULE)
        d.text(s, rx + 0.15, y, rw * 0.58 - 0.2, 0.6, a, 11 if not head else 9, WHITE if head else INK,
               TEXT_SEMI if head else TEXT, anchor=MSO_ANCHOR.MIDDLE)
        d.text(s, rx + rw * 0.58, y, rw * 0.42 - 0.15, 0.6, b, 11 if not head else 9, WHITE if head else MUTE,
               TEXT_SEMI if head else TEXT, anchor=MSO_ANCHOR.MIDDLE)
    d.text(s, rx, 5.45, rw, 0.25, "Draft rules. Ascension's architecture standards set the final list.", 9, MUTE, TEXT_LIGHT)
    d.bar(s, None, "Today the answer depends on who picks up the ticket. Here it depends on what the org already contains.", dark=False)
    d.bar(s, None, "Every recommendation cites the components it was based on.")
    d.notes(s, "This answers the question developers ask every day: should this be a Flow or a trigger? The Architect "
            "agent asks the graph what already runs on the object and whether the capability already exists, then "
            "applies agreed rules. In the example, Account already has an entry trigger and record-triggered flows, "
            "and Healthcare Facility Network creation already exists in two places. The right answer is to extend "
            "what exists, not add a third path. The rules are a draft; Ascension's standards set the final list.")
    S["decide"] = s

    # 12 Governance
    s = d.new()
    d.header(s, "Governance", "People keep every decision. Every change is traceable",
             "Aligned to the framework's security design.")
    gates = [("Gate 1 · Scope", "PM and Tech Lead", "After the impact verdict, before any ticket"),
             ("Gate 2 · Design", "Tech Lead", "Before any code is written"),
             ("Gate 3 · Code", "Tech Lead", "Pull request review before merge"),
             ("Gate 4 · Production", "CAB and release manager", "Ascension's existing change process")]
    w = (13.09 - 3 * 0.15) / 4
    for i, (g, who, when) in enumerate(gates):
        x = 0.12 + i * (w + 0.15)
        d.rect(s, x, 1.2, w, 1.3, "FDF1DE", RULE)
        d.sq(s, x + 0.2, 1.4, AMBER)
        d.text(s, x + 0.4, 1.33, w - 0.6, 0.25, g, 9, "8A5620", TEXT_SEMI, caps=True, track=60)
        d.text(s, x + 0.2, 1.65, w - 0.4, 0.3, who, 13.5, INK, DISPLAY_BOLD)
        d.text(s, x + 0.2, 2.02, w - 0.4, 0.4, when, 10, MUTE, TEXT)
    d.label(s, 0.12, 2.7, 8, "The evidence chain, kept on every ticket")
    chain = ["Request", "Graph verdict", "Jira ticket", "Design page", "Git commit", "Copado deploy", "Test results", "Graph snapshot"]
    pw = (13.09 - 7 * 0.3) / 8
    for i, c in enumerate(chain):
        x = 0.12 + i * (pw + 0.3)
        d.rect(s, x, 2.95, pw, 0.5, NAVY)
        d.text(s, x, 2.95, pw, 0.5, c, 9.5, WHITE, TEXT_SEMI, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
        if i < 7:
            d.arrow(s, x + pw + 0.05, 3.11, 0.2, 0.18)
    prin = [("Three AI identities", "Read, Development (DEV org and branch) and Release (lower environments). None holds a production credential.", PURPLE),
            ("Review routed by risk", "Medium to the Tech Lead, high to architecture, critical to security.", RED),
            ("Metadata, not patient data", "The graph reads how the org is built, never its records.", JADE),
            ("Graph before model", "An AI model is called only when the graph shows something new is needed.", BLUE)]
    for i, (t, b, c) in enumerate(prin):
        x = 0.12 + i * (w + 0.15)
        d.card(s, x, 3.7, w, 1.98, t, [b], accent=c, size=11, bullets=False)
    d.bar(s, None, "Evidence lives in Jira, Git, Copado and the AI audit store: who asked, what the graph found, who approved, what deployed, what the tests said.",
          dark=False, size=10)
    d.bar(s, None, "Production stays inside Ascension's existing CAB process.")
    d.notes(s, "For a healthcare client this is the slide that matters most. Four human gates: scope, design, code and "
            "production, with production inside Ascension's existing CAB. Every ticket carries the full chain of "
            "evidence. Four principles from the framework's security design: three AI identities, none holding a "
            "production credential; review routed by risk; metadata, never patient records; and the graph answers "
            "first, so a model is only called when something genuinely new is needed.")
    S["governance"] = s

    # 13 Model
    s = d.new()
    d.header(s, "Operating model", "Same tiles, fewer and stronger pods", "The target end state, reached in phases.")
    pw = 6.25
    for side in range(2):
        x = 0.12 + side * (pw + 0.59)
        target = side == 1
        d.rect(s, x, 1.2, pw, 4.5, CARD, BLUE if target else RULE, lw=1.5 if target else 0.75)
        d.label(s, x + 0.25, 1.35, 3, "Target" if target else "Today", BLUE if target else MUTE)
        d.rect(s, x + 0.25, 1.65, pw - 0.5, 0.45, NAVY if target else CARD_ALT)
        d.text(s, x + 0.25, 1.65, pw - 0.5, 0.45, "Engineering Director", 11, WHITE if target else INK, TEXT_SEMI,
               anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
        tw2 = (pw - 0.5 - 0.2) / 2
        for t, tile in enumerate(["Consumer", "Care Engagement"]):
            tx = x + 0.25 + t * (tw2 + 0.2)
            d.rect(s, tx, 2.25, tw2, 2.25, WHITE, RULE)
            d.text(s, tx + 0.15, 2.35, tw2 - 0.3, 0.3, tile, 12, INK, DISPLAY_BOLD)
            if not target:
                for k in range(5):
                    px = tx + 0.15 + (k % 3) * 0.85
                    py = 2.8 + (k // 3) * 0.5
                    d.rect(s, px, py, 0.75, 0.38, CARD_ALT)
                    d.text(s, px, py, 0.75, 0.38, "Pod", 9.5, MUTE, TEXT, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
            else:
                for k in range(2):
                    py = 2.75 + k * 0.82
                    d.rect(s, tx + 0.15, py, tw2 - 0.3, 0.7, BLUE)
                    d.text(s, tx + 0.27, py, tw2 - 0.5, 0.7, [[("Agentic pod", {"font": TEXT_SEMI})], "PM + Tech Lead + agents"],
                           9.5, WHITE, TEXT, anchor=MSO_ANCHOR.MIDDLE)
        foot = ("Shared across both tiles: Agent Platform team, plus QA and release support on demand" if target
                else "Each pod: PM, BA, developers, QA and release. Four to fourteen people.")
        if target:
            d.rect(s, x + 0.25, 4.65, pw - 0.5, 0.8, "E3F2F4")
        d.text(s, x + 0.4, 4.65, pw - 0.8, 0.8, foot, 10, INK, TEXT, anchor=MSO_ANCHOR.MIDDLE)
    d.rect(s, 6.47, 3.25, 0.4, 0.3, BLUE, shape=MSO_SHAPE.RIGHT_ARROW)
    d.bar(s, None, "The tiles stay; what changes is inside them. Four to five pods per tile become two agentic pods.", dark=False)
    d.bar(s, None, "Each agentic pod: a PM who owns the business, a Tech Lead who designs, approves and releases.")
    d.notes(s, "The tiles stay; the business structure Ascension knows does not change. Inside each tile, four to five "
            "pods become two agentic pods, each a PM and a Tech Lead with the agent team doing the build, test and "
            "documentation work. The Engineering Director oversees both tiles. Two things are shared and easy to "
            "forget: a small Agent Platform team that keeps the graph and agents healthy, and QA and release support "
            "pods can call on. This is the end state, reached in phases.")
    S["model"] = s

    # 14 Roles
    s = d.new()
    d.header(s, "Roles", "Who does what in an agentic pod", "The platform team is sized in the pilot.")
    roles = [("Product Manager", BLUE, ["Business conversations and priorities", "Requirements and acceptance criteria", "UAT sign-off"],
              "Approves Gate 1. Works with the Requirements and Jira agents."),
             ("Tech Lead", PURPLE, ["Solution design", "Code quality and security", "Release readiness"],
              "Approves Gates 1, 2 and 3. Works with the Architect, Developer, Review, Test and Deployment agents."),
             ("Agent team", AMBER, ["Drafts stories, designs, code and tests", "Deploys to QA and UAT", "Keeps Jira and Confluence current"],
              "Never approves its own work or touches production."),
             ("Agent Platform team", CYAN, ["Keeps the graph current", "Measures agent quality", "Turns standards into agent rules"],
              "Shared across both tiles: a small team sized in the pilot.")]
    w = (13.09 - 3 * 0.15) / 4
    for i, (t, c, items, foot) in enumerate(roles):
        x = 0.12 + i * (w + 0.15)
        d.rect(s, x, 1.2, w, 0.55, c)
        d.text(s, x + 0.2, 1.2, w - 0.4, 0.55, t, 13.5, WHITE, DISPLAY_BOLD, anchor=MSO_ANCHOR.MIDDLE)
        d.rect(s, x, 1.75, w, 2.3, WHITE, RULE)
        d.label(s, x + 0.2, 1.9, w - 0.4, "Owns")
        d.text(s, x + 0.2, 2.2, w - 0.4, 1.8, items, 11.5, INK, TEXT, bullet=True, after=8)
        d.rect(s, x, 4.05, w, 1.65, CARD, RULE)
        d.text(s, x + 0.2, 4.2, w - 0.4, 1.4, foot, 11, MUTE, TEXT, spacing=1.05)
    d.bar(s, None, "The PM owns the business side. The Tech Lead owns the technical side. Agents do the drafting, building, testing and documenting.", dark=False, size=10)
    d.bar(s, None, "No agent approves its own work.")
    d.notes(s, "The PM owns conversations, priorities, requirements and UAT sign-off, with the Requirements and Jira agents "
            "doing the writing. The Tech Lead approves the design, the code and, with the PM, the scope. The agent team "
            "drafts, builds, tests, documents and deploys to lower environments, and never approves its own work. The "
            "Agent Platform team is shared across both tiles and sized during the pilot.")
    S["roles"] = s

    # 15 Savings
    s = d.new()
    d.header(s, "The value", "Savings that are phased, measured and earned", "Planning figures, not commitments.")
    hdr = [("Phase", 2.2), ("When", 1.9), ("Pod shape", 3.6), ("VBC workload", 2.6), ("Annual saving", 2.79)]
    rows = [("Today", "Now", "PM, BA, developers, QA, release", "14 people, ~$2.47M", "None"),
            ("1 · Assist", "First 6 months", "Same team, agents in every step", "14 people", "More delivered per sprint"),
            ("2 · Consolidate", "6–12 months", "Pods merged within each tile", "7–8 people", "≈ $1.1M–$1.2M"),
            ("3 · Agent-native", "Year 2", "PM + Tech Lead + agents", "3–4 people", "≈ $1.8M–$1.9M")]
    x = 0.12
    for t, cw in hdr:
        d.rect(s, x, 1.2, cw - 0.04, 0.4, NAVY)
        d.text(s, x + 0.15, 1.2, cw - 0.25, 0.4, t, 8.5, WHITE, TEXT_SEMI, anchor=MSO_ANCHOR.MIDDLE, caps=True, track=40)
        x += cw
    fills = [WHITE, CARD, "EAF1FB", "E3F2F4"]
    for r, row in enumerate(rows):
        y = 1.66 + r * 0.6
        d.rect(s, 0.12, y, 13.05, 0.56, fills[r], RULE)
        x = 0.12
        for k, (v, (_, cw)) in enumerate(zip(row, hdr)):
            strong = k == 0 or (k == 4 and r >= 2)
            d.text(s, x + 0.15, y, cw - 0.25, 0.56, v, 12 if (k == 4 and r >= 2) else 10.5,
                   INK if strong or k == 3 else MUTE, DISPLAY_BOLD if (k == 4 and r >= 2) else (TEXT_SEMI if k == 0 else TEXT),
                   anchor=MSO_ANCHOR.MIDDLE)
            x += cw
    cards = [("Across both tiles", "[__] people in 9–10 pods today, moving to 4 agentic pods and a shared platform team.", BLUE),
             ("Net of platform cost", "AI model usage, Google Cloud and the Agent Platform team: [$___ a year], sized in the pilot.", AMBER),
             ("How the figures work", "VBC's average cost per person, about $176K. Each phase starts only once the last is measured.", JADE)]
    w = (13.09 - 2 * 0.2) / 3
    for i, (t, b, c) in enumerate(cards):
        d.card(s, 0.12 + i * (w + 0.2), 4.2, w, 1.5, t, [b], accent=c, size=11, bullets=False)
    d.bar(s, None, "Agents shorten build and test. Requirements, support and approvals still take people, which is why each phase is earned.", dark=False, size=10)
    d.bar(s, None, "Phase one changes nothing on cost. It measures how much more the same team delivers.")
    d.notes(s, "VBC is the worked example: fourteen people, about $2.47M, roughly $176K per person. Phase one changes "
            "nothing on cost; we measure how much more the same team delivers. Phase two merges pods within each tile; "
            "seven to eight people for the same workload saves about $1.1M to $1.2M a year. Phase three, a PM and Tech "
            "Lead with agents; three to four people saves about $1.8M to $1.9M. These are gross: model usage, Google "
            "Cloud and the platform team come off the top, sized in the pilot.")
    S["savings"] = s

    # 16 Feasibility (row style of the template's layer table)
    s = d.new()
    d.header(s, "Feasibility", "Is it feasible? Yes, in stages", "The useful answer is not yes to everything.")
    d.label(s, 0.12, 1.1, 8, "Capability, where it stands, and our rating")
    feas = [("Codex as the front door", "HIGH", JADE, "Available now; connects to tools through MCP"),
            ("Developer, test and QA agents", "PROVEN", JADE, "Built and in use at Ascension"),
            ("Jira and Confluence agents", "HIGH", JADE, "Reading built; writing is standard API work"),
            ("Knowledge graph", "HIGH", JADE, "Framework designed; about 30% built in a sandbox"),
            ("Reading what flows do", "HIGH", JADE, "Proven readable in the sandbox; access being finalised"),
            ("Design agent: Flow or trigger", "MEDIUM", BLUE, "Needs Ascension's standards written as rules"),
            ("Deployment through Copado", "MED-HIGH", BLUE, "QA and UAT automated; production stays with CAB"),
            ("Keeping the graph current", "MEDIUM", BLUE, "Re-sync after every deployment, plus nightly"),
            ("Two-person pods", "CONDITION", AMBER, "Depends on duties policy, support cover, review load")]
    for r, (cap, rating, c, where) in enumerate(feas):
        y = 1.32 + r * 0.5
        d.rect(s, 0.12, y, 8.1, 0.44, CARD_ALT if r % 2 == 0 else CARD)
        d.rect(s, 0.12, y, 0.5, 0.44, NAVY)
        d.text(s, 0.12, y, 0.5, 0.44, str(r + 1), 9.5, WHITE, DISPLAY_BOLD, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
        d.text(s, 0.72, y, 2.6, 0.44, cap, 10, INK, TEXT_SEMI, anchor=MSO_ANCHOR.MIDDLE)
        d.badge(s, 3.4, y + 0.11, 0.8, rating, c)
        d.text(s, 4.36, y, 3.8, 0.44, where, 8.8, MUTE, TEXT, anchor=MSO_ANCHOR.MIDDLE)
    d.card(s, 8.42, 1.32, 4.79, 2.4, "Our verdict",
           ["Technology: ready or buildable now.", "Operating model: reachable in stages, each earned by measured results.",
            "The knowledge graph is the newest piece, and it already runs for one pod."], dark=True, size=10)
    d.card(s, 8.42, 3.86, 4.79, 1.9, "What the pilot must answer",
           ["Ascension's separation-of-duties rule", "Production support cover in a smaller pod",
            "How much one Tech Lead can review"], accent=AMBER, size=10)
    d.bar(s, None, "Most of the technology is already in use at Ascension or is standard integration work.", dark=False)
    d.bar(s, None, "The one conditional item is the end-state pod size, and the pilot is designed to settle it.")
    d.notes(s, "Be direct. Most of the technology is already in use at Ascension or standard integration work. The "
            "knowledge graph is the newest piece and already runs for one pod in a sandbox. Two items are medium: the "
            "design agent is only as good as the standards it is given, and the graph must be kept current. The one "
            "conditional item is the end-state pod size, which depends on separation of duties, support cover and "
            "review capacity. The pilot is designed to answer those.")
    S["feasibility"] = s

    # 17 Risks
    s = d.new()
    d.header(s, "Risks", "The risks, and how we plan for each", "People risks first. They decide pod size.")
    risks = [("Separation of duties", "Tech Leads review across pods; production stays with CAB.", AMBER),
             ("Review bottleneck", "Review routed by risk: high to architecture, critical to security. Low-risk changes move faster.", AMBER),
             ("Leave and cover", "Paired pods cover each other. Designs and the graph hold the knowledge, not one person.", AMBER),
             ("Production support", "A Support and RCA agent, and an on-call rota shared across merged pods.", AMBER),
             ("A confident wrong answer", "Every verdict shows its evidence. Tests and review run before any merge.", BLUE),
             ("Graph out of date", "Re-synced after every deployment and nightly. Each answer names the snapshot it used.", BLUE),
             ("Patient data and security", "Metadata only, sandbox credentials only, least-privilege service accounts.", BLUE),
             ("Model lock-in", "Agents reach tools through MCP, an open standard, so the model can be swapped.", BLUE)]
    w, h = (13.09 - 3 * 0.15) / 4, 2.15
    for i, (t, b, c) in enumerate(risks):
        x = 0.12 + (i % 4) * (w + 0.15)
        y = 1.2 + (i // 4) * (h + 0.15)
        d.card(s, x, y, w, h, t, [b], accent=c, size=11.5, bullets=False)
    d.bar(s, None, "Top row: people and process, which decide how small a pod can safely be. Bottom row: technology, each with a built-in control.", dark=False, size=10)
    d.bar(s, None, "We will confirm Ascension's separation-of-duties rule in the first weeks of the pilot.")
    d.notes(s, "The top row is about people and process. Separation of duties: in healthcare change control, the person "
            "who builds a change usually cannot be its only approver, so Tech Leads review across pods and production "
            "stays with CAB. Review depth follows risk. Two-person pods are paired. Production support has its own "
            "agent and a shared rota. The bottom row is technology, and each has a built-in control.")
    S["risks"] = s

    # 18 Roadmap
    s = d.new()
    d.header(s, "Roadmap", "Prove it on one pod, then scale", "Proposed timeline. Depends on access.")
    phases = [("Done · about 30%", "Foundations", JADE, ["Graph built in a sandbox for Network Services", "Duplicate and impact checks working", "Flow internals proven readable"]),
              ("Months 1–2", "Platform", BLUE, ["Graph on Google Cloud, whole org", "Codex connected to the graph", "Jira and Confluence agents writing"]),
              ("Months 3–4", "Pilot", PURPLE, ["Full loop on 10–15 Network Services tickets", "Deployment and test agents on Copado", "Measured against today's baseline"]),
              ("Months 5–9", "First tile", ROSE, ["Pods merged into agentic pods", "Review depth tuned by risk", "Support and RCA agent live"]),
              ("Months 10–12+", "Second tile", CYAN, ["Second tile follows", "Agent-native pods where results allow", "Platform team runs the agents"])]
    w = (13.09 - 4 * 0.12) / 5
    for i, (when, t, c, items) in enumerate(phases):
        x = 0.12 + i * (w + 0.12)
        d.rect(s, x, 1.2, w, 0.75, c)
        d.text(s, x + 0.15, 1.27, w - 0.3, 0.22, when, 8.5, WHITE, TEXT_SEMI, caps=True, track=40)
        d.text(s, x + 0.15, 1.5, w - 0.3, 0.35, t, 13.5, WHITE, DISPLAY_BOLD)
        d.rect(s, x, 1.95, w, 2.95, WHITE if i else "E5F4F1", RULE)
        d.text(s, x + 0.15, 2.12, w - 0.3, 2.7, items, 11.5, INK, TEXT, bullet=True, after=10)
    segs = [("Already done", 1, None), ("Savings phase 1 · Assist", 2, "EAF1FB"), ("Phase 2 · Consolidate", 1, "DCE8F6"), ("Phase 3 · Agent-native", 1, "E3F2F4")]
    x = 0.12
    for t, n, f in segs:
        sw = n * w + (n - 1) * 0.12
        if f:
            d.rect(s, x, 5.08, sw, 0.5, f)
        d.text(s, x, 5.08, sw, 0.5, t, 9.5, MUTE if not f else INK, TEXT_SEMI, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
        x += sw + 0.12
    d.bar(s, None, "Only measured pilot results open the next phase. Nothing is restructured on a forecast.", dark=False)
    d.bar(s, None, "Months 3–4 are the decision point: ten to fifteen real tickets, measured against how they are delivered today.")
    d.notes(s, "About 30 percent of the foundation already exists. Months one and two move the graph to Google Cloud for "
            "the whole org and connect it to Codex. Months three and four run the full loop on ten to fifteen real "
            "Network Services tickets, measured against today. Only with those results do we merge pods in the first "
            "tile, then the second. The timeline is a proposal and depends on access being granted promptly.")
    S["roadmap"] = s

    # 19 Pilot
    s = d.new()
    d.header(s, "The pilot", "What we will measure, and what earns the next step", "Criteria agreed with Ascension at kickoff.")
    lw = 7.9
    d.label(s, 0.12, 1.1, lw, "Measured on every pilot ticket")
    meas = [("Measure", "How"), ("Request to QA time", "Jira timestamps, against the last six months"),
            ("People hours per ticket", "Time spent at each gate"),
            ("Duplicate builds avoided", "Requests answered “exists” or “reuse”"),
            ("Defects reaching UAT", "Zephyr and Jira defect counts"),
            ("Cost per ticket", "People time plus model and cloud spend"),
            ("Evidence completeness", "Verdict, design, tests and deploy on file")]
    for r, (a, b) in enumerate(meas):
        y = 1.32 + r * 0.6
        head = r == 0
        d.rect(s, 0.12, y, lw, 0.55, NAVY if head else (WHITE if r % 2 else CARD), None if head else RULE)
        d.text(s, 0.27, y, 2.9, 0.55, a, 9 if head else 11.5, WHITE if head else INK, TEXT_SEMI, anchor=MSO_ANCHOR.MIDDLE)
        d.text(s, 3.3, y, lw - 3.35, 0.55, b, 9 if head else 11.5, WHITE if head else MUTE,
               TEXT_SEMI if head else TEXT, anchor=MSO_ANCHOR.MIDDLE)
    rx = 0.12 + lw + 0.2
    d.card(s, rx, 1.32, 13.21 - rx, 4.15, "Proposed go / no-go for phase 2",
           ["Request-to-QA time at least halved", "No rise in defects reaching UAT",
            "Every pilot ticket carries its full evidence chain", "Tech Lead review load judged sustainable"], dark=True, size=12)
    d.bar(s, None, "The baseline is the last six months of Network Services tickets, so the comparison is like for like.", dark=False)
    d.bar(s, None, "The decision to consolidate pods is made on evidence both sides agreed in advance.")
    d.notes(s, "The pilot produces the numbers the business case needs, measured on real tickets. The last six months of "
            "Network Services tickets are the baseline for request-to-QA time, people hours, defects reaching UAT and "
            "total cost per ticket. We also count requests the graph answered as already existing or reusable, which "
            "is work avoided entirely. The go / no-go criteria are proposals to agree at kickoff.")
    S["pilot"] = s

    # 20 Ask
    s = d.new(dark=True)
    d.sq(s, 0.9, 1.15, TEAL, 0.16)
    d.text(s, 1.2, 1.1, 9, 0.3, "The decision", 12, TEAL, DISPLAY_SEMI, caps=True, track=150)
    d.text(s, 0.9, 1.6, 11.5, 1.3, ["Approve a four-month pilot", "on the Network Services pod"], 34, WHITE, DISPLAY_BOLD, spacing=0.98)
    needs = ["A Google Cloud project for the graph", "A sandbox integration user, read-only on metadata",
             "Jira and Confluence service accounts", "Copado pipeline access to QA and UAT",
             "A named PM and Tech Lead", "10–15 real tickets from the backlog"]
    w = (11.55 - 2 * 0.2) / 3
    for i, n in enumerate(needs):
        x = 0.9 + (i % 3) * (w + 0.2)
        y = 3.3 + (i // 3) * 1.05
        d.rect(s, x, y, w, 0.88, "1C3253")
        d.sq(s, x + 0.22, y + 0.39, TEAL)
        d.text(s, x + 0.45, y, w - 0.6, 0.88, n, 12, WHITE, TEXT, anchor=MSO_ANCHOR.MIDDLE)
    d.text(s, 0.9, 5.75, 11.5, 0.5, "Decision point at month four: move to the first tile, adjust, or stop.", 15, ON_DARK, TEXT_LIGHT)
    d.notes(s, "Close on a small, reversible decision. We are not asking Ascension to restructure tiles today. We are "
            "asking for four months on one pod, with six things. At month four the results decide the next step: move "
            "to the first tile, adjust, or stop.")
    S["ask"] = s

    order = [S["cover"], S["today"], S["proof"], S["gap"], S["solution"], S["journey"], S["agents"],
             KEEP_ENGINEERING, S["pack"], KEEP_CLINICAL,
             S["decide"], S["governance"], S["model"], S["roles"], S["savings"], S["feasibility"],
             S["risks"], S["roadmap"], S["pilot"], S["ask"]]
    lst = d.prs.slides._sldIdLst
    by_slide = {}
    for sid in lst:
        by_slide[d.prs.part.related_part(sid.get(qn("r:id")))] = sid
    resolved = [o if isinstance(o, int) else by_slide[o.part] for o in order]
    d.finish(resolved, out)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
