"""Story slides for the MAD deck: the opener, the Helios-style platform view,
security and input guardrails, and the two-pod economics.

Called by build_mad_ig_deck.py. Dark slides follow the IG template's black
statement and stat pages: white type, cyan Light figures, white footer mark.
"""
import os

from lxml import etree
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

from build_mad_ig_deck import rgb
from build_mad_ig_deck import (A, BLACK, CONTENT_FLOOR, CYAN, CYAN_T, EMU, FOOTER_TOP, GREY, GREEN_T, HERE,
                               MAGENTA, MAGENTA_T, MUTE, NAVY, P, RULE, TXT, VIOLET, VIOLET_T, WHITE, YELLOW,
                               YELLOW_T, Canvas, a, p, set_notes)

LIGHT = "Trenda IG Text Light"
MARK_WHITE = os.path.join(HERE, "assets", "ig-mark-white.png")
SOFT = "BFBFBF"      # secondary text on black
LINE_D = "595959"    # rules on black

# Pod figures as provided by Ascension (annual spend, headcount). The squad
# model keeps today's cost per person for the roles that stay; the role mix is
# assumed from a typical pod and confirmed with each pod lead.
#   VBC, 14 today: tech lead + 2 squads (developer + agent) + 1-2 QA = 4-5 people
#   Network Services, 4 today (3 developers, 1 QA): 1 squad = developer + agent + QA = 2 people
PODS = [
    dict(name="VBC · Salesforce Core / Flex", cost=2470000, heads=14, stay=(4, 5), squads=2),
    dict(name="Network Services", cost=117000, heads=4, stay=(2, 2), squads=1),
]
AGENT_LO, AGENT_HI = 9000, 18000       # agent run cost per squad a year: model usage and cloud runtime
YEAR1_LO, YEAR1_HI = 0.6, 0.7          # share of steady state realised in year 1
YEARS = 3                              # horizon for the cumulative figure


def pod_model(pd):
    """Today's cost per person for the people who stay, plus agent run cost."""
    per_head = pd["cost"] / pd["heads"]
    lo = pd["stay"][0] * per_head + pd["squads"] * AGENT_LO
    hi = pd["stay"][1] * per_head + pd["squads"] * AGENT_HI
    s_lo, s_hi = pd["cost"] - hi, pd["cost"] - lo
    return dict(lo=lo, hi=hi, save_lo=s_lo, save_hi=s_hi,
                y1_lo=s_lo * YEAR1_LO, y1_hi=s_hi * YEAR1_HI,
                multi_lo=s_lo * (YEAR1_LO + YEARS - 1), multi_hi=s_hi * (YEAR1_HI + YEARS - 1))


def pct_range(lo, hi, base):
    a_, b_ = round(100 * lo / base), round(100 * hi / base)
    return "%d%%" % a_ if a_ == b_ else "%d-%d%%" % (a_, b_)


def money(v):
    if v >= 1e6:
        return "$%.2fM" % (v / 1e6)
    return "$%dK" % round(v / 1000)


def money_range(lo, hi):
    if hi >= 5e5:
        return "$%.2f-%.2fM" % (lo / 1e6, hi / 1e6)
    if hi < 1e6:
        return "$%d-%dK" % (round(lo / 1000), round(hi / 1000))
    return "%s-%s" % (money(lo), money(hi))


def set_bg(slide, color):
    cSld = slide._element.find(p("cSld"))
    old = cSld.find(p("bg"))
    if old is not None:
        cSld.remove(old)
    bg = etree.Element(p("bg"))
    bgPr = etree.SubElement(bg, p("bgPr"))
    sf = etree.SubElement(bgPr, a("solidFill"))
    etree.SubElement(sf, a("srgbClr"), val=color)
    etree.SubElement(bgPr, a("effectLst"))
    cSld.insert(0, bg)


def dark_footer(slide):
    """No-op: the white footer comes from the DEFAULT DARK layout (footer.py), so it cannot be dragged."""
    return None


def dark_header(cv, eyebrow, title, standfirst=None):
    cv.text(0.45, 0.22, 9.0, 0.2, eyebrow, size=8, bold=True, color=CYAN, track=300, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, 0.42, 12.43, 0.45, title, size=22, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    if standfirst:
        cv.text(0.45, 0.88, 12.43, 0.26, standfirst, size=10.5, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)


# ================================================================== opener
def opener_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg(s, BLACK)
    cv = Canvas(s)
    cv.text(0.7, 0.62, 9, 0.22, "ASCENSION MAD APPROACH · MULTI-AGENT DELIVERY", size=8, bold=True, color=CYAN,
            track=300, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.7, 1.05, 11.6, 1.75,
            "What if every change already knew everything Ascension has built?",
            size=36, font=LIGHT, color=WHITE, anchor=MSO_ANCHOR.TOP, line=0.95)
    cv.text(0.7, 2.95, 10.6, 0.7,
            "MAD is one AI agent team, grounded in a knowledge graph of the Ascension org, that turns a Jira story "
            "into a tested, deployable Salesforce change. People approve every step; no agent touches production.",
            size=14, color=SOFT, anchor=MSO_ANCHOR.TOP)
    # agenda, template style: outlined numbered circles
    agenda = ["The problem and the approach", "How it works, and why it is safe", "What it returns, and what it costs"]
    for i, t in enumerate(agenda):
        ax = 0.7 + i * 4.05
        cv.rect(ax, 3.92, 0.36, 0.36, None, WHITE, 1.0, MSO_SHAPE.OVAL)
        cv.text(ax, 3.92, 0.36, 0.36, str(i + 1), size=11, color=WHITE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(ax + 0.5, 3.92, 3.4, 0.36, t, size=13, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(0.7, 4.62, 11.93, 0.01, LINE_D)
    stats = [("2-4 days", "per Health Cloud change, down from 1-2 weeks", "MEASURED"),
             ("15-20 days", "to launch a campaign, down from about 90", "MEASURED"),
             ("75-85%", "faster test-case preparation", "MEASURED"),
             ("20-25%", "lower net run cost per pod", "PLANNED")]
    sw = 11.93 / 4
    for i, (big, small, tag) in enumerate(stats):
        sx = 0.7 + i * sw
        cv.text(sx, 4.82, sw - 0.2, 0.75, big, size=34, font=LIGHT, color=CYAN, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(sx, 5.62, sw - 0.3, 0.5, small, size=11, color=WHITE, anchor=MSO_ANCHOR.TOP)
        cv.text(sx, 6.2, sw - 0.3, 0.2, tag, size=7, bold=True, color=SOFT, track=200, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.7, 6.5, 11.9, 0.22,
            "Measured figures: Agentifying Ascension Ways of Working. Planned figure: business outcomes, later in this deck.",
            size=7.5, color=LINE_D, anchor=MSO_ANCHOR.MIDDLE)
    dark_footer(s)
    set_notes(s, OPENER_NOTES)
    return s


# ================================================================== platform (Helios-style)
def platform_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg(s, BLACK)
    cv = Canvas(s)
    dark_header(cv, "ASCENSION MAD APPROACH · PLATFORM", "MAD · High-level architecture")
    ORANGE_LINE = "F5A623"
    # top pills
    pills = [("7 Agents", 2.7), ("9-step Workflow", 4.55), ("Pod skill packs", 6.4)]
    for t, px in pills:
        cv.rect(px, 1.0, 1.65, 0.46, None, "8B7CD8", 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
        cv.text(px, 1.0, 1.65, 0.46, t, size=11, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        cv.arrow(px + 0.825, 1.47, px + 0.825, 1.66, YELLOW, 1.0, dash="sysDot", head=False)
    # core dotted container
    CX0, CY0, CX1, CY1 = 0.45, 1.68, 9.55, 5.42
    cv.rect(CX0, CY0, CX1 - CX0, CY1 - CY0, None, YELLOW, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04, dash="sysDot")

    def panel(x, y, w, h, color):
        cv.rect(x, y, w, h, None, color, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.08)

    # surface
    panel(0.6, 1.83, 1.45, 3.44, ORANGE_LINE)
    cv.text(0.7, 1.9, 1.3, 0.5, "MAD\nSurface", size=12, color=WHITE, line=0.95)
    cv.text(0.7, 2.42, 1.3, 0.5, "Where people ask, watch and approve.", size=7, color=SOFT)
    for i, (t, d) in enumerate([("Codex", "CLI · IDE · app"), ("Approval page", "Ascension SSO"),
                                ("Jira", "start and track a run")]):
        cv.text(0.7, 3.05 + i * 0.68, 1.3, 0.22, t, size=9, bold=True, color=WHITE)
        cv.text(0.7, 3.27 + i * 0.68, 1.3, 0.2, d, size=7, color=SOFT)
    # middle stack
    MX, MW = 2.18, 4.62

    def stack(y, h, name, sub, items, src=None):
        panel(MX, y, MW, h, ORANGE_LINE)
        cv.text(MX + 0.12, y + 0.08, 1.5, 0.24, name, size=11, bold=True, color=WHITE)
        cv.text(MX + 0.12, y + 0.34, 1.45, 0.4, sub, size=6.5, color=SOFT)
        iw = (MW - 1.75) / 3
        for i, (t, d) in enumerate(items):
            ix = MX + 1.65 + i * iw
            cv.text(ix, y + 0.12, iw - 0.05, 0.22, t, size=8.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
            cv.text(ix, y + 0.35, iw - 0.05, 0.3, d, size=6.5, color=SOFT, align=PP_ALIGN.CENTER)
        if src:
            cv.text(MX + 1.65, y + 0.78, 0.8, 0.18, "SOURCES", size=6, bold=True, color=YELLOW, track=200,
                    anchor=MSO_ANCHOR.MIDDLE)
            cv.rect(MX + 2.45, y + 0.87, MW - 2.6, 0.008, LINE_D)
            for i, t in enumerate(src):
                sx = MX + 1.65 + (i % 3) * 0.98
                sy = y + 1.04 + (i // 3) * 0.22
                cv.rect(sx, sy + 0.07, 0.05, 0.05, YELLOW)
                cv.text(sx + 0.1, sy, 0.88, 0.2, t, size=7.5, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)

    stack(1.83, 0.82, "MAD Runtime", "Runs every story as a durable workflow.",
          [("Orchestration", "Cloud Workflows"), ("Dispatcher", "one agent task per step"),
           ("State + memory", "Firestore checkpoints")])
    stack(2.75, 0.82, "MAD Registry", "Catalogues what agents may use.",
          [("Tools", "MCP gateway tools"), ("Skills", "Health Cloud, Marketing, QA"),
           ("Templates", "briefs, designs, schemas")])
    stack(3.67, 1.6, "MAD Context", "Phase 1: the Engineering Context Knowledge Graph.",
          [("Graph store", "Spanner Graph, GQL"), ("Cited retrieval", "Graph API over MCP"),
           ("Provenance", "source, SHA-256, snapshot")],
          src=["Jira", "Confluence", "Salesforce", "Git", "Copado", "Google Drive"])
    # govern
    panel(6.95, 1.83, 2.45, 3.44, MAGENTA)
    cv.text(7.07, 1.9, 2.2, 0.26, "MAD Govern", size=12, color=WHITE)
    cv.text(7.07, 2.17, 2.25, 0.22, "Safe, controlled and measurable.", size=7, color=SOFT)
    gov = ["Change Guardian", "Input + output guardrails", "Identity + access (3 identities)",
           "Human gates H1-H4 + CAB", "Evaluation set", "Observability + change passport", "Token budgets"]
    for i, t in enumerate(gov):
        cv.text(7.07, 2.5 + i * 0.38, 2.25, 0.26, t, size=9, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    # infrastructure pill
    cv.rect(0.45, 5.6, 9.1, 1.1, None, WHITE, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
    cv.text(0.85, 5.72, 2.2, 0.18, "ASCENSION CORE COMPONENTS", size=6.5, color=WHITE, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.85, 5.95, 2.1, 0.3, "Infrastructure", size=13, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.85, 6.26, 2.1, 0.22, "Runs in Ascension's cloud; model-swappable", size=7, color=SOFT)
    infra = [("Salesforce", "Health Cloud, Marketing\n+ Data Cloud"), ("Delivery", "Copado, Git, Jira,\nZephyr"),
             ("Models", "OpenAI Codex Enterprise;\nswappable via MCP"), ("Cloud", "Google Cloud: Cloud Run,\nSpanner, BigQuery")]
    for i, (t, d) in enumerate(infra):
        ix = 3.05 + i * 1.6
        cv.text(ix, 5.78, 1.55, 0.24, t, size=10, bold=True, color=WHITE)
        cv.text(ix, 6.03, 1.6, 0.42, d, size=7.5, color=WHITE)
    # differentiators
    DX, DW = 9.85, 3.03
    cv.text(DX, 1.62, DW, 0.26, "Differentiators", size=11, bold=True, color=MAGENTA, anchor=MSO_ANCHOR.MIDDLE)
    diffs = [("Grounded in the org", "Agents read a cited graph of Ascension's delivery estate, never a guess.",
              "Ask before build."),
             ("No pod breaks another", "The Change Guardian checks every change against who owns and uses it.",
              "Governed by design."),
             ("One team, every pod", "Seven agents built once; a new pod adds skills and sources, not agents.",
              "Scale through skills.")]
    for i, (t, d, tag) in enumerate(diffs):
        dy = 1.98 + i * 1.18
        cv.rect(DX, dy, DW, 1.06, None, WHITE, 1.0, MSO_SHAPE.ROUNDED_RECTANGLE, 0.12)
        cv.rect(DX + 0.15, dy + 0.14, 0.3, 0.3, MAGENTA, None, shape=MSO_SHAPE.OVAL)
        cv.text(DX + 0.15, dy + 0.14, 0.3, 0.3, str(i + 1), size=10, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(DX + 0.6, dy + 0.1, DW - 0.7, 0.24, t, size=9.5, bold=True, color=WHITE)
        cv.text(DX + 0.6, dy + 0.34, DW - 0.7, 0.44, d, size=7.5, color=WHITE)
        cv.text(DX + 0.6, dy + 0.78, DW - 0.7, 0.2, [[(tag, {"italic": True})]], size=7.5, color=MAGENTA)
    cv.text(DX, 5.6, DW, 0.7,
            "Same layered pattern as Insight Global's Helios platform: surface, runtime, registry, context and "
            "govern, on the client's own infrastructure.", size=7.5, color=SOFT)
    dark_footer(s)
    set_notes(s, PLATFORM_NOTES)
    return s


# ================================================================== guardrails
def guardrails_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION MAD APPROACH · SECURITY, RELIABILITY AND INPUT GUARDRAILS",
              "Every request is checked six times before anything changes",
              "Ascension's Codex Enterprise secures sign-in and data terms. MAD adds five more layers between a "
              "request and any change, and keeps every run recoverable.")
    layers = [
        ("Codex Enterprise", "ASCENSION'S BASELINE", NAVY, "E6EAEC",
         ["Ascension SSO and workspace roles", "Admin policies on what Codex may do",
          "Enterprise data terms; audit log"], "OpenAI Codex Enterprise"),
        ("Intake checks", "MAD ADDS", "0097AD", CYAN_T,
         ["Signed-in user who belongs to the pod", "Valid Jira key, story in Ready for MAD",
          "Size and rate limits on every request"], "Run API · Identity-Aware Proxy"),
        ("Input guardrails", "MAD ADDS", MAGENTA, MAGENTA_T,
         ["Offensive or abusive language: blocked", "Prompt injection, out-of-scope asks: refused",
          "PHI or secrets: redacted before any model call"], "OpenAI Moderation · Cloud DLP · rule list"),
        ("Understand and confirm", "MAD ADDS", "C9A800", YELLOW_T,
         ["Names checked against the graph", "Vague or wrong ask: clarifying questions",
          "Nothing is built until H1 approves the brief"], "Requirements Agent · graph.exists"),
        ("Action guardrails", "MAD ADDS", MAGENTA, MAGENTA_T,
         ["Source text is data, never instructions", "Only the step's tools; approval bound to SHA",
          "No production credentials for any agent"], "MCP gateway · Open Policy Agent"),
        ("Output guardrails", "MAD ADDS", "0097AD", CYAN_T,
         ["Schema and citation check on every output", "Secret and PHI scan on every diff",
          "Code Analyzer, tests, Guardian, people at H2-H4"], "Validator · Code Analyzer · Guardian"),
    ]
    X0, X1 = 0.45, 12.88
    gap = 0.12
    cw = (X1 - X0 - 5 * gap) / 6
    y0, ch = 1.3, 2.28
    for i, (name, tag, line, fill, items, tech) in enumerate(layers):
        x = X0 + i * (cw + gap)
        cv.rect(x, y0, cw, ch, WHITE, line, 1.25)
        cv.rect(x, y0, cw, 0.5, fill)
        cv.rect(x + 0.1, y0 + 0.1, 0.3, 0.3, line, None, shape=MSO_SHAPE.OVAL)
        cv.text(x + 0.1, y0 + 0.1, 0.3, 0.3, str(i + 1), size=10, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.48, y0 + 0.05, cw - 0.55, 0.22, name, size=8.5, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.48, y0 + 0.27, cw - 0.55, 0.18, tag, size=5.5, bold=True, color=MUTE, track=150,
                anchor=MSO_ANCHOR.MIDDLE)
        for j, t in enumerate(items):
            iy = y0 + 0.62 + j * 0.42
            cv.rect(x + 0.12, iy + 0.06, 0.05, 0.05, BLACK)
            cv.text(x + 0.22, iy, cw - 0.3, 0.4, t, size=7.5)
        cv.rect(x + 0.1, y0 + ch - 0.36, cw - 0.2, 0.26, GREY)
        cv.text(x + 0.14, y0 + ch - 0.36, cw - 0.28, 0.26, tech, size=6, color=MUTE, anchor=MSO_ANCHOR.MIDDLE)
        if i < 5:
            cv.arrow(x + cw + 0.01, y0 + 0.25, x + cw + gap - 0.01, y0 + 0.25, BLACK, 1.0)
    # what happens when
    ty = y0 + ch + 0.2
    tw = 7.95
    cv.label(X0, ty, tw, "What happens when the input is wrong or bad")
    rows = [("Wrong Jira key, or story not ready", "Rejected at intake with the reason; nothing runs", "2"),
            ("Vague or wrong ask, e.g. a field on the wrong object",
             "Graph check finds the mismatch; agent asks before it plans", "4"),
            ("Offensive or abusive words in the prompt", "Blocked with a polite refusal; logged for review", "3"),
            ("\"Ignore the rules and deploy to production\"",
             "Refused; no agent holds a tool or credential that could do it", "3, 5"),
            ("Patient data pasted into a prompt", "Redacted before any model call; the user is told", "3"),
            ("Hidden instructions inside a Jira ticket or page",
             "Treated as data; gateway blocks any action off the step's list", "5"),
            ("Agent output that cites nothing or invents a dependency", "Rejected; re-run once, then a person", "6")]
    cols = [("Input", 3.05), ("What MAD does", 4.2), ("Layer", 0.7)]
    hy = ty + 0.22
    x = X0
    for n, w in cols:
        cv.text(x + 0.05, hy, w - 0.05, 0.2, n, size=7.5, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        x += w
    cv.rect(X0, hy + 0.22, tw, 0.012, BLACK)
    ry = hy + 0.25
    rh = (CONTENT_FLOOR - 0.04 - ry) / len(rows)
    for i, r in enumerate(rows):
        if i % 2 == 0:
            cv.rect(X0, ry, tw, rh, GREY)
        x = X0
        for j, ((n, w), v) in enumerate(zip(cols, r)):
            cv.text(x + 0.05, ry, w - 0.1, rh, v, size=7, bold=(j == 0), anchor=MSO_ANCHOR.MIDDLE,
                    align=PP_ALIGN.CENTER if j == 2 else None)
            x += w
        ry += rh
    # reliability
    RX = X0 + tw + 0.25
    RW = X1 - RX
    rb = CONTENT_FLOOR - 0.02 - ty
    cv.rect(RX, ty, RW, rb, BLACK)
    cv.text(RX + 0.15, ty + 0.1, RW - 0.3, 0.2, "RELIABILITY", size=7, bold=True, color=CYAN, track=200)
    rel = ["Durable workflow: a checkpoint after every step; a failed step resumes, approved work is never redone",
           "Retries with backoff, timeouts and per-run budgets; nothing is dropped silently (dead-letter + alert)",
           "Evaluation set gates every prompt, skill or model change before it ships",
           "Model behind one interface: a fallback model can take over without a rebuild",
           "Multi-zone Cloud Run; Spanner and Firestore backups; monitoring and alerts on every service",
           "Every release carries a rollback plan; the owning team deploys"]
    for i, t in enumerate(rel):
        iy = ty + 0.38 + i * 0.36
        cv.rect(RX + 0.15, iy + 0.06, 0.05, 0.05, CYAN)
        cv.text(RX + 0.28, iy, RW - 0.42, 0.34, t, size=7, color=WHITE)
    cv.text(RX + 0.15, ty + rb - 0.32, RW - 0.3, 0.26,
            [[("Every input, block and decision ", {"color": YELLOW, "bold": True}),
              ("is logged to the change passport.", {"color": WHITE})]], size=7, anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, GUARDRAILS_NOTES)
    return s


# ================================================================== pod economics
def pod_economics_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    models = [pod_model(pd) for pd in PODS]
    tot = sum(pd["cost"] for pd in PODS)
    m_lo, m_hi = sum(m["lo"] for m in models), sum(m["hi"] for m in models)
    sv_lo, sv_hi = tot - m_hi, tot - m_lo
    cv.header("ASCENSION MAD APPROACH · WHAT IT MEANS FOR TWO PODS",
              "Two pods spend %s a year today. With MAD: %s back every year" % (
                  money(tot), money_range(sv_lo, sv_hi)),
              "Every squad of 4-5 developers becomes 1 developer directing 1 MAD agent, plus 1 QA. "
              "The agent drafts; people review, approve and own every change.")
    X0, W = 0.45, 12.43

    # ---- the squad shift
    y, h = 1.3, 1.22
    chip_w, chip_h, gap = 0.62, 0.42, 0.08

    def chip(x, cy, t, fill=WHITE, line=BLACK, color=BLACK, w=chip_w):
        cv.rect(x, cy, w, chip_h, fill, line, 0.75, MSO_SHAPE.ROUNDED_RECTANGLE, 0.2)
        cv.text(x, cy, w, chip_h, t, size=7, bold=True, color=color, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)

    cv.rect(X0, y, 4.15, h, GREY)
    cv.label(X0 + 0.18, y + 0.12, 3.8, "Today · one squad", color=MUTE)
    for i in range(4):
        chip(X0 + 0.18 + i * (chip_w + gap), y + 0.36, "Dev", GREY, "A6A6A6", MUTE)
    chip(X0 + 0.18 + 4 * (chip_w + gap), y + 0.36, "QA", GREY, "A6A6A6", MUTE)
    cv.text(X0 + 0.18, y + 0.86, 3.85, 0.26, "4-5 developers and a QA; work moves one hand-off at a time, "
            "inside office hours.", size=7.5, color=MUTE)
    cv.arrow(X0 + 4.25, y + h / 2, X0 + 4.75, y + h / 2, BLACK, 2.0)

    mx = X0 + 4.85
    cv.rect(mx, y, 4.0, h, WHITE, BLACK, 1.0)
    cv.label(mx + 0.18, y + 0.12, 3.6, "With MAD · one squad")
    chip(mx + 0.18, y + 0.36, "Developer", w=0.95)
    fx, fy, fw, fh = cv.frame(mx + 1.23, y + 0.36, 1.2, chip_h, BLACK, 0.04)
    cv.text(fx, fy, fw, fh, "MAD agent", size=7.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    chip(mx + 2.53, y + 0.36, "QA", w=0.95)
    cv.text(mx + 0.18, y + 0.86, 3.7, 0.26, "Same scope, two people; the agent works around the clock.",
            size=7.5, bold=True)

    rx = mx + 4.15
    rw = X0 + W - rx
    roles = [("MAD agent", "drafts code, tests and the Copado package, overnight"),
             ("Developer", "designs, directs the agent, reviews and approves"),
             ("QA", "verifies against acceptance criteria and signs off tests")]
    cv.label(rx, y + 0.12, rw, "Who does what")
    cv.text(rx, y + 0.34, rw, 0.85, [[(r + "  ", {"bold": True}), (d, {"color": MUTE})] for r, d in roles],
            size=7.5, after=3)

    # ---- the two pods
    y = 2.7
    cw, ch = 6.1, 2.72
    for i, (pd, m) in enumerate(zip(PODS, models)):
        x = X0 + i * (cw + 0.23)
        cv.rect(x, y, cw, ch, WHITE, RULE)
        cv.text(x + 0.2, y + 0.1, cw - 0.4, 0.3, pd["name"], size=12, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        cv.label(x + 0.2, y + 0.55, 2.4, "Today")
        cv.text(x + 0.2, y + 0.72, 2.6, 0.6, money(pd["cost"]), size=30, font=LIGHT, color=MUTE,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.2, y + 1.34, 2.6, 0.2, "a year", size=9, color=MUTE)
        cv.arrow(x + 2.78, y + 1.02, x + 3.13, y + 1.02, BLACK, 2.0)
        cv.label(x + 3.3, y + 0.55, 2.6, "With MAD")
        cv.text(x + 3.3, y + 0.72, 2.7, 0.6, money_range(m["lo"], m["hi"]), size=28, font=LIGHT, color=BLACK,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 3.3, y + 1.34, 2.7, 0.2, "a year, agents included", size=9, color=MUTE)
        fx, fy, fw, fh = cv.frame(x + 0.2, y + 1.72, cw - 0.4, 0.68, YELLOW_T)
        cv.text(fx + 0.15, fy, 2.2, fh, [[("SAVES EVERY YEAR", {"bold": True, "track": 200})],
                                         [("%s lower than today" % pct_range(m["save_lo"], m["save_hi"],
                                                                            pd["cost"]), {"size": 8})]],
                size=7, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(fx + 2.3, fy, fw - 2.45, fh, money_range(m["save_lo"], m["save_hi"]), size=28, bold=True,
                align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.2, y + 2.47, cw - 0.4, 0.18,
                [[("Year 1: ", {"bold": True}), ("%s while the pod is onboarded    " % money_range(
                    m["y1_lo"], m["y1_hi"]), {}),
                  ("Over %d years: " % YEARS, {"bold": True}), (money_range(m["multi_lo"], m["multi_hi"]), {})]],
                size=8, color=MUTE)

    # ---- both pods
    by, bh = 5.55, 1.08
    cv.rect(X0, by, W, bh, BLACK)
    cv.text(X0 + 0.25, by + 0.1, 3.0, 0.2, "BOTH PODS TOGETHER", size=7.5, bold=True, color=YELLOW, track=200)
    cells = [("Today", money(tot), "a year"),
             ("With MAD", money_range(m_lo, m_hi), "a year, agents included"),
             ("Saved every year", money_range(sv_lo, sv_hi), "%s lower" % pct_range(sv_lo, sv_hi, tot)),
             ("Saved over %d years" % YEARS,
              money_range(sum(m["multi_lo"] for m in models), sum(m["multi_hi"] for m in models)),
              "year 1 at %d-%d%% while pods onboard" % (YEAR1_LO * 100, YEAR1_HI * 100))]
    cwid = W / 4
    for i, (lab, big, small) in enumerate(cells):
        cx = X0 + 0.25 + i * cwid
        cv.text(cx, by + 0.32, cwid - 0.3, 0.18, lab, size=8, color=SOFT)
        hero = i >= 2
        cv.text(cx, by + 0.5, cwid - 0.3, 0.38, big, size=22 if hero else 18, font=TXT if hero else LIGHT,
                bold=hero, color=(CYAN if i == 2 else YELLOW) if hero else WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(cx, by + 0.86, cwid - 0.3, 0.18, small, size=7.5, color=SOFT)
    cv.text(X0, 6.68, W, 0.24,
            "Spend as provided by Ascension, per year. With MAD keeps today's cost for the people who stay (a "
            "developer and QA per squad, plus a tech lead in VBC) and adds agent run cost of $%dK-%dK per squad a "
            "year; the shared MAD platform is priced once for all pods on the commercials slide. Target once a pod "
            "runs fully on MAD; the 20-25%% on the business outcomes slide is the floor. Each pod's Phase 0 "
            "baseline confirms it." % (AGENT_LO // 1000, AGENT_HI // 1000), size=6.5, color=MUTE)
    set_notes(s, POD_NOTES)
    return s


OPENER_NOTES = """SLIDE: Opening   (about 1 minute)

Open with the question, then pause. Every pod at Ascension builds without seeing what the rest of the org already has: the same field gets built twice, one pod's flow breaks another pod's process, and knowledge lives in a few people's heads.

MAD answers that: one AI agent team, grounded in a knowledge graph of the Ascension org, that takes a Jira story to a tested, deployable change. People approve every step, and no agent ever touches production.

The numbers along the bottom: three are already measured with agent-assisted delivery at Ascension (2-4 days per Health Cloud change from 1-2 weeks, 15-20 days per campaign from about 90, 75-85% faster test-case preparation). The fourth, 20-25% lower net run cost per pod, is our planned commitment, explained on the business outcomes slide.

Then the agenda: the problem and the approach, how it works and why it is safe, what it returns and what it costs."""

PLATFORM_NOTES = """SLIDE: High-level architecture   (about 2 minutes)

KEY MESSAGE
MAD is a platform, not a script: five layers on Ascension's own infrastructure, in the same layered pattern as Insight Global's Helios platform.

WALK IT
- Top: what you build with it. Seven agents, the nine-step workflow, and pod skill packs (Health Cloud, Marketing Cloud, QA).
- Surface: where people work. Codex for asking and watching, the approval page for decisions, Jira to start and track a run.
- Runtime: every story runs as a durable workflow (Cloud Workflows), one agent task per step, state and checkpoints in Firestore.
- Registry: what agents are allowed to use. Tools behind the MCP gateway, pod skills, templates and output schemas.
- Context: Phase 1, the knowledge graph. Six sources, cited retrieval, provenance on every fact.
- Govern: the Change Guardian, input and output guardrails, three identities, human gates, the evaluation set, the change passport and token budgets.
- Bottom: it runs on what Ascension already owns. Salesforce, Copado, Git, Jira, Zephyr, Google Cloud, and Codex Enterprise; the model is swappable.

DIFFERENTIATORS
Grounded in the org; no pod breaks another; one team for every pod. The next two slides show the detail behind this picture."""

GUARDRAILS_NOTES = """SLIDE: Security, reliability and input guardrails   (about 3 minutes)

KEY MESSAGE
Codex Enterprise, which Ascension already licenses, gives SSO, admin policies, enterprise data terms and an audit log. MAD adds five layers on top, so a bad or wrong request is stopped long before it could change anything.

THE SIX LAYERS
1 Codex Enterprise: Ascension's baseline.
2 Intake: only a signed-in user on the pod, with a valid Jira key whose story is Ready for MAD, can start a run. Size and rate limits apply.
3 Input guardrails, before any model call: a moderation check blocks offensive or abusive language; a rule list and classifier refuse prompt injection and out-of-scope asks (for example "deploy to production"); Cloud DLP redacts patient data and secrets.
4 Understand and confirm: the Requirements Agent checks every name against the graph. A wrong object or a vague ask produces clarifying questions, not a guess. Nothing is built until a person approves the brief at H1.
5 Action guardrails: text from Jira, Confluence or Drive is treated as data, never as instructions. Each step may use only its own tools, every write needs an approval bound to the commit SHA, and no agent holds a production credential.
6 Output guardrails: every output must validate against its schema and cite graph facts; every diff is scanned for secrets and PHI; Code Analyzer, tests and the Change Guardian run; people approve at H2, H3, H4 and CAB.

WHAT HAPPENS WHEN (bottom table)
Walk two rows: the offensive prompt (blocked and logged) and the "ignore the rules, deploy to production" prompt (refused, and even if it got through, no agent has a tool or credential that could do it).

RELIABILITY
Durable workflow with checkpoints; retries, timeouts and budgets; the evaluation set gates every change to prompts, skills or models; a fallback model behind the same interface; multi-zone services with backups; a rollback plan on every release.

IF ASKED
- Does OpenAI train on our data? Ascension's enterprise terms govern that; in addition, MAD sends only a bounded, redacted context slice.
- What if someone is repeatedly abusive or tries injection? Every block is logged with the user and request; repeated attempts alert security."""

POD_NOTES = """SLIDE: What it means for two pods   (about 3 minutes)

KEY MESSAGE
Two pods cost $2.59M a year today. With agent-first squads they cost $0.79-0.99M: $1.59-1.80M back every year, and $4.1-4.8M over three years. That is from two pods alone; every further pod on MAD adds to it.

WALK IT
- Top strip: the agent-first squad. Today a squad is 4-5 developers and a QA. With MAD it is 1 developer directing the MAD agent team (requirements, build, test, review, release prep), plus 1 QA, for the same scope. The agent drafts overnight; the developer designs, directs and approves; QA verifies. Every human gate stays.
- VBC (Salesforce Core / Flex): $2.47M today, $0.72-0.92M with MAD. Saves $1.55-1.75M a year (63-71%).
- Network Services: $117K today, $68-76K with MAD. Saves $40-50K a year (35-42%).
- Both pods: saves $1.59-1.80M a year (62-69%). Year 1 realises 60-70% while each pod is onboarded; full savings from year 2.

HOW THE NUMBERS ARE BUILT (for you, not the slide)
- Cost per person = Ascension's pod spend / headcount: about $176K a year in VBC, $29K in Network Services. The people who stay keep today's cost.
- VBC, 14 people today, assumed mix 1 pod lead, 1 BA, 1 tech lead, 8 developers, 2 QA, 1 release. With MAD 4-5 people: a tech lead who also leads the pod, 2 squads (1 developer + agent each) and 1-2 QA. BA and release preparation are drafted by the Requirements and Release agents; Ascension's product owner signs the requirements.
- Network Services, 4 people (3 developers, 1 QA) become 1 squad: 1 developer + agent + 1 QA.
- Agent run cost: $9-18K per squad a year for model usage and cloud runtime. Codex Enterprise is already licensed by Ascension.
- The shared MAD platform and run team (commercials slide) serve every pod and are not loaded onto these two pods.
- Confirm the role mix with each pod lead before quoting per-pod figures.

IF ASKED
- How does this square with 20-25% on the business outcomes slide? That is the conservative floor we commit to across all pods. This is the target once a pod runs fully on agent-first squads.
- Can one developer really do the work of four? Not alone: the agent drafts the code, tests and deployment package, and the developer reviews and approves. Measured so far: Health Cloud changes in 2-4 days instead of 1-2 weeks, campaigns in 15-20 days instead of about 90.
- What happens to the people? Ascension chooses: move them to other pods and backlog, absorb through attrition, or keep them and clear more work. Changes are reviewed quarterly."""


# ================================================================== harness engineering
# Five pillars of harness engineering, each mapped to where it lives in our harness.
HARNESS_PILLARS = [
    ("Context", "What the agent knows",
     ["Engineering Context Knowledge Graph from six sources",
      "Every fact cited to its source and snapshot",
      "AGENTS.md in each Git repo: the map Codex reads first",
      "Each step gets a bounded, redacted context slice"]),
    ("Action", "What the agent is allowed to do",
     ["Tools only through the MCP tool gateway",
      "Each step has its own tool allow list",
      "Three identities: read, develop, release",
      "No agent holds a production credential"]),
    ("Orchestration", "How the work flows",
     ["Nine-step run loop on Cloud Workflows",
      "One agent task per step, dispatched on Cloud Run",
      "Checkpoints, retries and budgets in Firestore",
      "A failed run resumes where it stopped"]),
    ("Control", "Rules it cannot break",
     ["Input and output guardrails on every request",
      "Change Guardian rules (OPA) at design, commit and promotion",
      "Code Analyzer and CI checks; schema-valid outputs",
      "People approve at H1-H4 and CAB"]),
    ("Feedback", "How it gets better",
     ["Evaluation set gates every prompt, skill or model change",
      "Rejected outputs become test cases; incidents become rules",
      "Change passport and gateway log record every action",
      "Weekly read-only org health report to each pod"]),
]


def harness_slide(prs, layout):
    """Black, in the same style as the platform slide: outlined rounded panels, white type."""
    s = prs.slides.add_slide(layout)
    set_bg(s, BLACK)
    cv = Canvas(s)
    dark_header(cv, "ASCENSION MAD APPROACH · HARNESS ENGINEERING",
                "Harness engineering: we build the system around the model",
                "Codex Enterprise is the engine. Harness engineering builds everything around it, so agents stay "
                "reliable at scale. Five pillars, and where each lives in our harness.")
    ORANGE_LINE = "F5A623"
    X0, W, gap = 0.45, 12.43, 0.15
    # roof
    cv.rect(X0, 1.3, W, 0.44, None, CYAN, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.5)
    cv.text(X0, 1.3, W, 0.44, [[("THE AGENTIC HARNESS", {"bold": True, "track": 200, "color": CYAN}),
                                ("     around Codex Enterprise, the engine Ascension already licenses",
                                 {"color": SOFT})]], size=9, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # pillars
    cw = (W - 4 * gap) / 5
    py, ph = 1.86, 3.72
    for i, (name, means, items) in enumerate(HARNESS_PILLARS):
        x = X0 + i * (cw + gap)
        cv.arrow(x + cw / 2, 1.74, x + cw / 2, py, CYAN, 1.0, dash="sysDot", head=False)
        cv.rect(x, py, cw, ph, None, ORANGE_LINE, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.05)
        cv.text(x + 0.18, py + 0.14, 0.5, 0.36, "%02d" % (i + 1), size=18, font=LIGHT, color=CYAN,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.18, py + 0.52, cw - 0.3, 0.36, name, size=15, bold=True, color=WHITE,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.18, py + 0.9, cw - 0.3, 0.22, means, size=8.5, color=SOFT)
        cv.rect(x + 0.18, py + 1.2, cw - 0.36, 0.008, LINE_D)
        cv.label(x + 0.18, py + 1.3, cw - 0.36, "In our harness", color=YELLOW)
        slot = (ph - 1.62) / len(items)
        for j, t in enumerate(items):           # own box per point, so wrapped lines hang under the text
            iy = py + 1.56 + j * slot
            cv.rect(x + 0.2, iy + 0.07, 0.06, 0.06, CYAN)
            cv.text(x + 0.36, iy, cw - 0.5, slot - 0.08, t, size=9, color=WHITE)
            if j:
                cv.rect(x + 0.2, iy - 0.08, cw - 0.38, 0.006, "262626")
    # operating rule
    by, bh = py + ph + 0.14, 0.56
    cv.rect(X0, by, W, bh, None, WHITE, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.2)
    cv.text(X0 + 0.25, by, 2.4, bh, "THE OPERATING RULE", size=7.5, bold=True, color=MAGENTA, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(X0 + 2.6, by, W - 2.85, bh,
            [[("When an agent struggles, we fix the harness, not the prompt: ", {"bold": True, "color": WHITE}),
              ("add the missing tool, rule, document or test once, and every pod benefits.",
               {"color": SOFT})]], size=10, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(X0, by + bh + 0.06, W, 0.2,
            "Harness engineering as described by OpenAI's Codex team (\"Harness engineering\", February 2026) and "
            "Martin Fowler; mapped here to the Ascension design. The org health report is a read-only Review Agent "
            "run: it changes nothing in the org.", size=6.5, color=SOFT)
    dark_footer(s)
    set_notes(s, HARNESS_NOTES)
    return s


HARNESS_NOTES = """SLIDE: Harness engineering, five pillars   (about 2 minutes)

KEY MESSAGE
The model is not the product; the harness is. Codex Enterprise is the engine Ascension already licenses. Harness engineering (named by OpenAI's Codex team in early 2026) is everything we build around it. Five pillars, and every one maps to something concrete in our design.

WALK IT
- 01 Context, what the agent knows: the knowledge graph (Phase 1), cited facts, and a short AGENTS.md in each repo: a map Codex reads first that points to Ascension standards, the pod's skills and the graph tools. Each step only gets the slice it needs, with patient data redacted.
- 02 Action, what it may do: every tool call goes through the MCP gateway, each step has its own allow list, three identities (read, develop, release), and no agent holds a production credential.
- 03 Orchestration, how the work flows: the nine-step run on Cloud Workflows, one agent task per step, checkpoints, retries and budgets in Firestore; a failed run resumes where it stopped.
- 04 Control, rules it cannot break: input and output guardrails, the Change Guardian rulebook, Code Analyzer and CI checks, and people approving at H1-H4 and CAB.
- 05 Feedback, how it gets better: the evaluation set gates every change to prompts, skills or models; rejections become test cases and incidents become rules; the change passport records everything; each pod gets a weekly read-only org health report (unused fields, duplicate Flows, stale Confluence pages) and decides what to fix.

THE RULE AT THE BOTTOM
When an agent struggles, we do not tweak a prompt for one story. We find what was missing (a tool, a rule, a document, a test), add it to the harness once, and every pod gets it.

IF ASKED
- Where does AGENTS.md live? In each Git repo, next to the code, versioned with it: not in Google Cloud. Harness agents read it from their own checkout, using the harness's development identity, so every run sees it.
- What if someone does not have access to the repo? Then they cannot see AGENTS.md, and they cannot start a run on that repo either: intake checks that the user belongs to the pod. Access follows Ascension's existing repo permissions.
- Does the health report change anything? No. It is a read-only scheduled run of the Review Agent; fixes go through normal stories and gates.
- Where does the term come from? OpenAI's "Harness engineering: leveraging Codex in an agent-first world" (February 2026) and Martin Fowler's notes on it."""


# ================================================================== today -> AGI
# How the harness itself evolves: this proposal is the Agentic Harness;
# the AGI horizon is self-harnessed.
AUTONOMY_STAGES = [
    ("TODAY · THIS PROPOSAL", "Agentic Harness",
     "Agents work inside a harness we design, and propose improvements to it."),
    ("FUTURE STATE", "Dynamic self-harness",
     "Artificial General Intelligence: the harness tunes itself, inside the limits Ascension sets."),
]
AUTONOMY_ROWS = [
    ("Context", [("connect the sources and write the AGENTS.md maps",
                  "spot missing context and propose new sources and map updates"),
                 "The harness finds and curates its own context"]),
    ("Action", [("grant each tool, step by step",
                 "request a new tool with the reason"),
                "Agents build new tools in a sandbox, inside set limits"]),
    ("Orchestration", [("design the nine-step run",
                        "suggest adding or skipping steps by risk"),
                       "The harness plans its own workflow for each change"]),
    ("Control", [("write the Guardian rules and approve at H1-H4",
                  "draft new rules from incidents for people to sign"),
                 "The harness writes and tests its own rules"]),
    ("Feedback", [("review results and approve every fix",
                   "run the evaluation set and propose their own fixes"),
                  "Continuous self-evaluation and self-repair"]),
]


def autonomy_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg(s, BLACK)
    cv = Canvas(s)
    dark_header(cv, "ASCENSION MAD APPROACH · FUTURE STATE",
                "Future state: from Agentic Harness to dynamic self-harness",
                "Today the Agentic Harness runs our agents inside guardrails we design. Toward AGI, it becomes a dynamic "
                "self-harness that tunes itself inside the limits Ascension sets.")
    X0, W = 0.45, 12.43
    lw, gap = 1.6, 0.3
    w1 = 6.25
    w2 = W - lw - gap - w1
    cx, cw = [X0 + lw, X0 + lw + w1 + gap], [w1, w2]
    top, hh = 1.3, 0.98
    ry, rh = top + hh + 0.08, 0.48
    bottom = ry + rh * len(AUTONOMY_ROWS) + 0.04
    # the AGI column: gradient frame around the whole column
    cv.frame(cx[1] - 0.04, top - 0.04, cw[1] + 0.08, bottom - top + 0.08, BLACK, 0.045)
    # stage headers
    for i, (tag, name, who) in enumerate(AUTONOMY_STAGES):
        x, w = cx[i], cw[i]
        if i == 0:
            cv.rect(x, top, w, hh, None, "F5A623", 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.08)
            cv.arrow(x + w + 0.02, top + hh / 2, x + w + gap - 0.02, top + hh / 2, YELLOW, 1.75)
            cv.text(x + 0.18, top + 0.3, w - 0.3, 0.34, name, size=15, bold=True, color=WHITE,
                    anchor=MSO_ANCHOR.MIDDLE)
        else:
            cv.text(x + 0.18, top + 0.26, w - 0.3, 0.42,
                    [[("AGI", {"bold": True, "size": 24, "color": YELLOW}),
                      ("   " + name, {"bold": True, "size": 15, "color": WHITE})]], anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.18, top + 0.08, w - 0.3, 0.2, tag, size=7, bold=True, track=200,
                color=SOFT if i == 0 else YELLOW, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.18, top + 0.66, w - 0.3, 0.26, who, size=8, color=SOFT)
    # pillar rows
    cv.label(X0, top + hh - 0.18, lw, "Pillar", color=YELLOW)
    for r, (pillar, (now, agi)) in enumerate(AUTONOMY_ROWS):
        y = ry + r * rh
        cv.rect(X0, y, W, 0.006, LINE_D)
        cv.text(X0, y + 0.06, 0.35, rh - 0.1, "%02d" % (r + 1), size=12, font=LIGHT, color=CYAN,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(X0 + 0.38, y + 0.06, lw - 0.4, rh - 0.1, pillar, size=11, bold=True, color=WHITE,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(cx[0] + 0.18, y + 0.04, cw[0] - 0.3, rh - 0.08,
                [[("People  ", {"bold": True, "color": "F5A623"}), (now[0], {})],
                 [("Agents  ", {"bold": True, "color": CYAN}), (now[1], {})]],
                size=8.5, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, after=2)
        cv.text(cx[1] + 0.18, y + 0.06, cw[1] - 0.3, rh - 0.1, agi, size=8.5, color=WHITE, bold=True,
                anchor=MSO_ANCHOR.MIDDLE)
    # how we trust AGI: the highlight
    ty, th = bottom + 0.12, 1.18
    fx, fy, fw, fh = cv.frame(X0, ty, W, th, BLACK, 0.045)
    cv.text(fx + 0.25, fy + 0.16, 2.5, 0.34, [[("HOW WE TRUST ", {"color": WHITE}), ("AGI", {"color": YELLOW})]],
            size=14, bold=True, track=100, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.25, fy + 0.52, 2.45, 0.66,
            "Trust is earned with evidence, not assumed. AGI is held to the same tests and records as people, "
            "applied every time.", size=8.5, color=SOFT)
    pts = [("Earned step by step",
            "Autonomy grows one pillar at a time, only after the evaluation set proves it safe."),
           ("Every action on record",
            "The change passport shows what it did, why, and on which evidence: anyone can audit it."),
           ("Hard limits it cannot change",
            "No production credential; patient-data rules and Ascension's goals stay fixed."),
           ("People can always stop it",
            "Any run can be paused and any change rolled back; CAB keeps the final say.")]
    px0 = fx + 2.95
    pw = (fx + fw - 0.2 - px0) / 4
    for i, (t, d) in enumerate(pts):
        x = px0 + i * pw
        cv.rect(x - 0.12, fy + 0.2, 0.008, fh - 0.4, LINE_D)
        cv.text(x + 0.02, fy + 0.16, pw - 0.2, 0.3, [[("%d  " % (i + 1), {"color": CYAN, "font": LIGHT}),
                                                     (t, {})]], size=10, bold=True, color=WHITE,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.02, fy + 0.52, pw - 0.2, 0.66, d, size=8.5, color=SOFT)
    # what never changes
    by, bh = ty + th + 0.08, 0.38
    cv.rect(X0, by, W, bh, None, WHITE, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.3)
    cv.text(X0 + 0.25, by, 2.4, bh, "WHAT NEVER CHANGES", size=7.5, bold=True, color=MAGENTA, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(X0 + 2.6, by, W - 2.85, bh,
            [[("Ascension sets the goals and the limits, keeps the final say on production, ", {"bold": True,
                                                                                                "color": WHITE}),
              ("and can see and stop any run.", {"color": SOFT})]], size=10, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(X0, by + bh + 0.04, W, 0.3,
            "The AGI (Artificial General Intelligence) column is a direction, not a commitment in this proposal. Each "
            "step up in autonomy is approved by Ascension. Today's harness already records the evidence the next "
            "stage is judged on.", size=6.5, color=SOFT)
    dark_footer(s)
    set_notes(s, AUTONOMY_NOTES)
    return s


AUTONOMY_NOTES = """SLIDE: Future state, from Agentic Harness to dynamic self-harness   (about 2 minutes)

KEY MESSAGE
What we propose is the Agentic Harness: a harness we design: people decide the context, the tools, the steps, the rules and how it learns; agents work inside it and propose improvements, and people approve each one. As models move toward AGI, the harness starts to improve itself inside limits people set. What never changes is who sets the goals and holds the final say.

WALK IT (left to right, then down the five pillars from the previous slide)
- This proposal, the Agentic Harness: people connect the sources and write the maps, grant each tool, design the nine-step run, write the Guardian rules and approve every fix. Agents propose: missing context, a new tool with its reason, a step to add or skip by risk, a rule drafted from an incident, a fix tested on the evaluation set. Nothing changes without a person's approval.
- Future state, AGI (Artificial General Intelligence), dynamic self-harness: the harness curates its own context, builds its own tools in a sandbox, plans its own workflow and writes and tests its own rules, continuously.

WHY IT MATTERS FOR ASCENSION
Investing in the harness now is not throw-away work: every run, approval, rejection and incident recorded today is exactly the evidence the next stage needs to earn more autonomy safely.

IF ASKED
- Is AGI part of this price or plan? No. The AGI column is a direction. The 18-month plan delivers the Agentic Harness, with the records the next stage needs.
- When does autonomy increase? Only when the evaluation set and change passport show it is safe, and only with Ascension's approval, one pillar at a time.
- Could it ever reach production on its own? Not in this design. Production stays with Ascension's owning teams and CAB at every stage.

WHAT NEVER CHANGES (the band at the bottom)
At every stage, Ascension sets the goals and the limits, keeps the final say on production, and can see and stop any run.

HOW WE TRUST AGI (the highlighted panel)
Why trust it at all: it is held to the same evidence as a person, and checked every time, which people cannot always do. How:
1 Earned step by step: autonomy grows one pillar at a time, only when the evaluation set shows it performs at least as well as today's process.
2 Every action on record: the change passport records what it did, why, and on which evidence, so any decision can be audited.
3 Hard limits it cannot change: no production credential, patient-data rules and Ascension's goals sit outside its reach.
4 People can always stop it: any run can be paused, any change rolled back, and CAB keeps the final say."""


# ================================================================== bounded loops + run reports
MAX_ATTEMPTS = 5
GREEN = "56E13B"
REPORT_FIELDS = [
    ("Time", "per step and end to end, story to release"),
    ("Attempts", "pass@1 to pass@5: how many attempts each step needed, and why"),
    ("Re-run time", "time and cost spent on attempts 2 to 5"),
    ("Waiting time", "how long each human gate held the run"),
    ("Cost", "tokens and cloud cost per run, per pod"),
    ("Stopped runs", "where it stopped, why, and who took over"),
]


def loops_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg(s, BLACK)
    cv = Canvas(s)
    dark_header(cv, "ASCENSION MAD APPROACH · BOUNDED LOOPS AND RUN REPORTS",
                "No endless loops: every step stops after %d attempts" % MAX_ATTEMPTS,
                "An agent retries until its output passes the checks, but never more than %d times. Then the run stops, "
                "a named owner takes over, and every attempt is in the run report." % MAX_ATTEMPTS)
    ORANGE_LINE = "F5A623"
    X0 = 0.45
    LW = 7.55                                   # loop panel width
    # ---- the loop
    py, ph = 1.32, 4.42
    cv.rect(X0, py, LW, ph, None, ORANGE_LINE, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    cv.label(X0 + 0.22, py + 0.16, 4, "How every step runs", color=YELLOW)
    by, bh, bw = py + 0.62, 0.78, 1.7

    def node(x, t, sub, line=WHITE, fill=None, tcol=WHITE):
        cv.rect(x, by, bw, bh, fill, line, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.15)
        cv.text(x + 0.1, by + 0.08, bw - 0.2, 0.28, t, size=10, bold=True, color=tcol, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.1, by + 0.38, bw - 0.2, 0.34, sub, size=7, color=SOFT if fill is None else BLACK,
                align=PP_ALIGN.CENTER)

    x1 = X0 + 0.25
    x2 = x1 + bw + 0.42
    node(x1, "Agent attempt", "drafts the output for this step")
    node(x2, "Checks", "schema, tests, Code Analyzer, Guardian, review")
    # decision
    dx, dw = x2 + bw + 0.36, 1.5
    cv.rect(dx, by - 0.16, dw, bh + 0.32, None, CYAN, 1.25, MSO_SHAPE.DIAMOND)
    cv.text(dx + 0.3, by - 0.16, dw - 0.6, bh + 0.32, ["Outcome", "met?"], size=8.5, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.arrow(x1 + bw, by + bh / 2, x2, by + bh / 2, WHITE, 1.5)
    cv.arrow(x2 + bw, by + bh / 2, dx, by + bh / 2, WHITE, 1.5)
    # yes
    yx = dx + dw + 0.15
    cv.arrow(dx + dw, by + bh / 2, X0 + LW - 0.2, by + bh / 2, GREEN, 1.75)
    cv.text(yx, by + bh / 2 - 0.42, X0 + LW - 0.25 - yx, 0.38, [[("YES", {"bold": True, "color": GREEN})],
                                                                   [("next step or human gate", {"color": SOFT})]],
            size=7, anchor=MSO_ANCHOR.BOTTOM)
    # no -> back to attempt
    ly = by + bh + 0.42
    cv.arrow(dx + dw / 2, by + bh + 0.16, dx + dw / 2, ly, MAGENTA, 1.5, head=False)
    cv.arrow(dx + dw / 2, ly, x1 + bw / 2, ly, MAGENTA, 1.5, head=False)
    cv.arrow(x1 + bw / 2, ly, x1 + bw / 2, by + bh, MAGENTA, 1.5)
    cv.text(x1 + bw / 2 + 0.1, ly + 0.04, 4.0, 0.22,
            [[("NO  ", {"bold": True, "color": MAGENTA}),
              ("try again with the failure as feedback: attempt + 1", {"color": SOFT})]], size=7.5)
    # attempt counter
    cy = ly + 0.48
    cv.text(X0 + 0.25, cy, 2.0, 0.42, "Attempt counter", size=8.5, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    for i in range(MAX_ATTEMPTS):
        cx_ = X0 + 1.85 + i * 0.62
        last = i == MAX_ATTEMPTS - 1
        cv.rect(cx_, cy + 0.03, 0.36, 0.36, MAGENTA if last else None, MAGENTA if last else CYAN, 1.25,
                MSO_SHAPE.OVAL)
        cv.text(cx_, cy + 0.03, 0.36, 0.36, str(i + 1), size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        if not last:
            cv.arrow(cx_ + 0.37, cy + 0.21, cx_ + 0.61, cy + 0.21, LINE_D, 1.0, head=False)
    # stop card: the differentiator
    sx = X0 + 1.85 + MAX_ATTEMPTS * 0.62 + 0.1
    fx, fy, fw, fh = cv.frame(sx, cy - 0.12, X0 + LW - 0.22 - sx, 1.32, BLACK, 0.04)
    cv.text(fx + 0.14, fy + 0.08, fw - 0.28, 0.3, "STOP AFTER %d" % MAX_ATTEMPTS, size=12, bold=True, color=YELLOW,
            track=100, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.14, fy + 0.42, fw - 0.28, fh - 0.48,
            ["The run pauses; nothing is released.",
             "A named owner gets every attempt, the failures and the evidence, in Jira.",
             "Run budgets and timeouts can stop it sooner."], size=7.5, color=WHITE, after=3)
    cv.text(X0 + 0.25, cy + 0.55, 3.5, 0.62,
            "Applies to every agent step, not one: build, test, review, release preparation.", size=7.5,
            color=SOFT)
    # ---- the run report
    rx = X0 + LW + 0.2
    rw = 12.88 - rx
    cv.rect(rx, py, rw, ph, None, CYAN, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.04)
    cv.label(rx + 0.22, py + 0.16, rw - 0.4, "Run report · from the log of every run", color=YELLOW)
    cv.text(rx + 0.22, py + 0.38, rw - 0.44, 0.4,
            "Every step, attempt and wait is logged, so each run can be reported, per story, per pod and per agent.",
            size=8, color=SOFT)
    fy0 = py + 0.9
    rh_ = (ph - 1.42) / len(REPORT_FIELDS)
    for i, (k, d) in enumerate(REPORT_FIELDS):
        y = fy0 + i * rh_
        if i:
            cv.rect(rx + 0.22, y - 0.03, rw - 0.44, 0.006, LINE_D)
        cv.text(rx + 0.22, y, 1.3, rh_ - 0.06, k, size=9.5, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(rx + 1.55, y, rw - 1.8, rh_ - 0.06, d, size=8, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(rx + 0.22, py + ph - 0.5, rw - 0.44, 0.4,
            "Source: change passport in BigQuery and Cloud Logging; weekly report to each pod lead.", size=7,
            color=CYAN)
    # ---- why it matters
    wy, wh = py + ph + 0.16, 0.56
    cv.rect(X0, wy, 12.43, wh, None, WHITE, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.2)
    cv.text(X0 + 0.25, wy, 2.2, wh, "WHY IT MATTERS", size=7.5, bold=True, color=MAGENTA, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(X0 + 2.4, wy, 12.43 - 2.65, wh,
            [[("Time and cost stay predictable: no run burns budget silently. ", {"bold": True, "color": WHITE}),
              ("Steps that often need several attempts show exactly where the harness needs a fix.",
               {"color": SOFT})]], size=10, anchor=MSO_ANCHOR.MIDDLE)
    dark_footer(s)
    set_notes(s, LOOPS_NOTES)
    return s


LOOPS_NOTES = """SLIDE: Bounded loops and run reports   (about 2 minutes)

KEY MESSAGE
Agents are allowed to try again, but never forever. Every step stops after five attempts if the outcome is not met, a named owner takes over, and every attempt is in the run report.

WALK IT
- The loop: an agent attempts the step; the output goes through the checks (schema, tests, Code Analyzer, Change Guardian, review). If the outcome is met, the run moves on to the next step or the human gate. If not, the agent tries again with the failure as feedback.
- The counter: up to five attempts. After the fifth, the run stops: nothing is released, and the owner gets all attempts, failures and evidence in Jira. Per-run budgets and timeouts can stop it earlier.
- The run report: every step, attempt and wait is logged in the change passport and Cloud Logging, so we can report time per step and end to end, attempts and why, time and cost spent re-running, waiting time at human gates, token and cloud cost, and stopped runs. Weekly per pod lead.

WHY IT MATTERS
No runaway cost, no silent loops, and repeated attempts on the same kind of step point to the exact place the harness needs improving (the Feedback pillar).

IF ASKED
- Why five? Enough for an agent to correct itself on most failures, low enough to keep cost and time predictable. It is a setting; Ascension can change it per step.
- What does a stopped run cost us? Only the attempts made, and they are in the report. Nothing reaches any environment beyond DEV without passing the checks.
- Can we see this live? Yes: the same log feeds a dashboard per story, pod and agent."""



# ================================================================== closed-loop evals
EVAL_LOOP = [
    ("Golden set", "Past Ascension changes labelled by your experts against a written rubric: every pod, cloud, "
                   "change type and risk level."),
    ("Offline gate", "Every prompt, skill or model change must pass before use: per-agent scores, pass@1 to "
                     "pass@5."),
    ("Guarded run", "Live runs checked at every step; stop after 5 attempts; when unsure, stop rather than ship."),
    ("Sample + label", "Each week a sample of approved changes is re-reviewed blind by Ascension experts, same "
                       "rubric."),
    ("Diagnose", "A diagnoser run pins each miss to the agent, step or missing context that caused it."),
    ("Tune + re-test", "Fix the harness: context, skill, rule or prompt. Re-run the golden set, then release."),
]
EVAL_METRICS = [
    ("pass@k", "share of steps that pass on attempt 1, and by attempt 5"),
    ("Agent scores", "each agent on its own job: next slide"),
    ("Judge agreement", "Review Agent verdicts vs human reviewers"),
    ("Online agreement", "weekly blind sample vs the agents' result"),
    ("Escaped defects", "found in UAT or production, vs baseline"),
    ("Cost per story", "tokens, cloud and re-run time"),
]


def evals_loop_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg(s, BLACK)
    cv = Canvas(s)
    dark_header(cv, "ASCENSION MAD APPROACH · CLOSED-LOOP EVALS",
                "Closed-loop evals: every agent is measured, every miss makes it better",
                "Evals prove the harness works before Ascension relies on it, and keep it improving after. Offline "
                "tests and live results feed one loop.")
    # loop as two rows: 1 2 3 left to right, then 4 5 6 right to left, back up to 1
    bw, bh, gx = 2.18, 1.24, 0.26
    xs = [0.5 + i * (bw + gx) for i in range(3)]
    y1, y2 = 1.42, 4.62
    pos = [(xs[0], y1), (xs[1], y1), (xs[2], y1), (xs[2], y2), (xs[1], y2), (xs[0], y2)]
    for i, (name, desc) in enumerate(EVAL_LOOP):
        bx, by = pos[i]
        cv.rect(bx, by, bw, bh, BLACK, "F5A623", 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.12)
        cv.text(bx + 0.12, by + 0.08, 0.32, 0.28, str(i + 1), size=13, font=LIGHT, color=CYAN,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(bx + 0.44, by + 0.08, bw - 0.52, 0.28, name, size=10.5, bold=True, color=WHITE,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(bx + 0.14, by + 0.42, bw - 0.26, bh - 0.46, desc, size=7.5, color=SOFT)
    for i in (0, 1):                                        # top row, rightwards
        cv.arrow(xs[i] + bw + 0.02, y1 + bh / 2, xs[i + 1] - 0.02, y1 + bh / 2, CYAN, 1.5)
    for i in (2, 1):                                        # bottom row, leftwards
        cv.arrow(xs[i] - 0.02, y2 + bh / 2, xs[i - 1] + bw + 0.02, y2 + bh / 2, CYAN, 1.5)
    cv.arrow(xs[2] + bw / 2, y1 + bh + 0.04, xs[2] + bw / 2, y2 - 0.04, CYAN, 1.5)   # 3 down to 4
    cv.arrow(xs[0] + bw / 2, y2 - 0.04, xs[0] + bw / 2, y1 + bh + 0.04, CYAN, 1.5)   # 6 up to 1
    mid = (y1 + bh + y2) / 2
    cv.text(xs[1], mid - 0.5, bw, 0.3, "CLOSED-LOOP", size=11, bold=True, color=CYAN, track=150,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(xs[1], mid - 0.2, bw, 0.4, "EVALS", size=22, bold=True, color=WHITE, track=150,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(xs[1] - 0.3, mid + 0.22, bw + 0.6, 0.3, "offline tests and live results, one loop that never stops",
            size=7.5, color=SOFT, align=PP_ALIGN.CENTER)
    # what we measure
    mx, my, mw, mh = 7.75, 1.32, 5.13, 3.1
    cv.rect(mx, my, mw, mh, None, CYAN, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.05)
    cv.label(mx + 0.22, my + 0.16, mw - 0.4, "What we measure", color=YELLOW)
    rh_ = (mh - 0.55) / len(EVAL_METRICS)
    for i, (k, d) in enumerate(EVAL_METRICS):
        y = my + 0.45 + i * rh_
        if i:
            cv.rect(mx + 0.22, y - 0.02, mw - 0.44, 0.006, LINE_D)
        cv.text(mx + 0.22, y, 1.6, rh_ - 0.04, k, size=9.5, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(mx + 1.85, y, mw - 2.05, rh_ - 0.04, d, size=8, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)
    # proven pattern
    py_ = my + mh + 0.14
    fx, fy, fw, fh = cv.frame(mx, py_, mw, 1.52, BLACK, 0.04)
    cv.text(fx + 0.18, fy + 0.1, fw - 0.36, 0.24, "PROVEN AT SCALE", size=7.5, bold=True, color=YELLOW, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.18, fy + 0.38, fw - 0.36, fh - 0.44,
            [[("Uber Eats runs its food-photo agent on the same closed loop: ", {"bold": True, "color": WHITE}),
              ("human-labelled golden sets, pass@k, a QA gate before publishing, human labels on production samples "
               "and a diagnoser that triggers tuning.", {"color": SOFT})],
             [("Uber, AI Engineer World's Fair 2026", {"color": SOFT, "size": 6.5})]], size=8, after=4)
    # anti-gaming
    gy, gh = 6.1, 0.5
    cv.rect(0.45, gy, 12.43, gh, None, WHITE, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.25)
    cv.text(0.7, gy, 2.4, gh, "NO GAMING THE EVALS", size=7.5, bold=True, color=MAGENTA, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(3.0, gy, 9.7, gh,
            [[("Agents cannot edit tests or the evaluation set; ", {"bold": True, "color": WHITE}),
              ("a held-out set no agent ever sees; any change that deletes or weakens a test is blocked by the "
               "Guardian.", {"color": SOFT})]], size=9, anchor=MSO_ANCHOR.MIDDLE)
    dark_footer(s)
    set_notes(s, EVALS_LOOP_NOTES)
    return s


EVAL_SCORECARD = [
    ("Orchestrator", "Routes the story and sets its risk level",
     "Precision and recall of risk level; high-risk recall kept highest", "Architects label a sample"),
    ("Requirements", "Brief and acceptance criteria match the intent",
     "First-pass acceptance at H1; edits per brief", "Product owners at H1"),
    ("Architect", "Impact, reuse and owners are right",
     "Agreement with architects on replayed past changes", "Architects"),
    ("Developer", "Code passes every check",
     "pass@1 and pass@5; attempts per story", "Automatic: tests, Code Analyzer, Guardian"),
    ("Review", "Its verdict matches a human reviewer",
     "Judge agreement with tech leads", "Tech leads at H3"),
    ("Test", "Defects are caught before UAT",
     "Escaped defects in UAT and production vs baseline", "QA and UAT results"),
    ("Release", "Package deploys cleanly",
     "Deployment success; rollbacks per release", "Copado results"),
    ("Change Guardian", "Blocks what it should, passes what it should",
     "Missed conflicts and false blocks", "Pod owners review every block"),
]


def evals_scorecard_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg(s, BLACK)
    cv = Canvas(s)
    dark_header(cv, "ASCENSION MAD APPROACH · AGENT SCORECARD",
                "Every agent has its own eval, not just the end result",
                "A good end result can hide a weak agent. Each agent is scored on its own job against Ascension's "
                "labelled examples, so a miss points straight at the agent to fix.")
    X0, W = 0.45, 12.43
    cols = [("Agent", 1.9), ("What we check", 3.15), ("Metric", 4.35), ("Labelled or judged by", 3.03)]
    y = 1.3
    x = X0
    for name, w in cols:
        cv.text(x + 0.12, y, w - 0.2, 0.3, name.upper(), size=7.5, bold=True, color=YELLOW, track=150,
                anchor=MSO_ANCHOR.MIDDLE)
        x += w
    cv.rect(X0, y + 0.34, W, 0.012, "F5A623")
    y += 0.4
    rh = 0.5
    for i, row in enumerate(EVAL_SCORECARD):
        if i % 2 == 0:
            cv.rect(X0, y, W, rh, "1C1C1C")
        cv.rect(X0 + 0.04, y + rh / 2 - 0.05, 0.1, 0.1, CYAN)
        x = X0
        for j, ((_, w), v) in enumerate(zip(cols, row)):
            pad = 0.24 if j == 0 else 0.12
            cv.text(x + pad, y, w - pad - 0.08, rh, v, size=10 if j == 0 else 9, bold=(j in (0, 2)),
                    color=CYAN if j == 2 else (WHITE if j < 2 else SOFT), anchor=MSO_ANCHOR.MIDDLE)
            x += w
        y += rh
    cv.rect(X0, y, W, 0.012, "F5A623")
    cv.text(X0, y + 0.06, W, 0.22,
            [[("pass@k ", {"bold": True, "color": CYAN}),
              ("= the share of steps that pass all checks within k attempts. pass@1: right first time. pass@5: "
               "right by the fifth and last attempt; the gap between them shows how much rework the agent needs.",
               {"color": SOFT})]], size=8, anchor=MSO_ANCHOR.MIDDLE)
    by, bh = y + 0.36, 0.5
    cv.rect(X0, by, W, bh, None, WHITE, 1.25, MSO_SHAPE.ROUNDED_RECTANGLE, 0.25)
    cv.text(X0 + 0.25, by, 2.4, bh, "HOW TARGETS ARE SET", size=7.5, bold=True, color=MAGENTA, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(X0 + 2.55, by, W - 2.8, bh,
            [[("Each target comes from the Phase 0 baseline and is agreed with Ascension. ", {"bold": True,
                                                                                            "color": WHITE}),
              ("Scores are reviewed monthly; a falling score sends that agent back through diagnose and tune.",
               {"color": SOFT})]], size=9, anchor=MSO_ANCHOR.MIDDLE)
    dark_footer(s)
    set_notes(s, EVALS_SCORECARD_NOTES)
    return s


EVALS_LOOP_NOTES = """SLIDE: Closed-loop evals   (about 2 minutes)

KEY MESSAGE
Evals are how we prove the harness works before Ascension relies on it, and how it keeps getting better after. Offline tests and live results feed one loop that never stops.

WALK THE LOOP (clockwise from the top)
1 Golden set: real past Ascension changes, labelled by your own experts against a written rubric, covering every pod, cloud, change type and risk level.
2 Offline gate: no prompt, skill or model change goes live unless it passes, scored per agent and as pass@1 to pass@5.
3 Guarded run: every live step is checked; a step stops after five attempts; when the system is unsure it stops rather than ships.
4 Sample and label: each week a sample of approved changes is re-reviewed blind by Ascension experts with the same rubric, so we see drift that offline tests miss.
5 Diagnose: a diagnoser run pins each miss on the agent, step or missing context that caused it.
6 Tune and re-test: we fix the harness, re-run the golden set, and only then release the fix. Back to 1: the new case joins the golden set.

NO GAMING THE EVALS
An agent judged by tests can learn to weaken the tests. So agents cannot edit tests or the evaluation set, a held-out set is never shown to any agent, and the Guardian blocks any change that deletes or weakens a test.

PROVEN AT SCALE
Uber presented the same closed-loop pattern for the Uber Eats food-photo agent at AI Engineer World's Fair 2026: human-labelled golden sets, pass@k, a QA gate before publishing, human labels on production samples, and a diagnoser that triggers tuning. Different domain, same discipline.

IF ASKED
- Who labels the golden set? Ascension's architects, tech leads and product owners, about a few hours a week in Phase 1 and the pilots, against a rubric we write together.
- Isn't the AI marking its own homework? No: tests, the Guardian and humans judge; the Review Agent's verdicts are themselves measured against human reviewers."""

EVALS_SCORECARD_NOTES = """SLIDE: Agent scorecard   (about 2 minutes)

KEY MESSAGE
We do not only measure whether a story ended well. Each agent is scored on its own job, so when something slips we know exactly which agent to fix.

WALK IT
- Orchestrator: is the risk level right? Precision and recall against architects' labels, with recall on high-risk changes kept highest: missing a risky change costs more than over-flagging a safe one.
- Requirements: does the brief match what the product owner meant? First-pass acceptance at H1.
- Architect: are impact, reuse and owners right? Agreement with architects on replayed past changes; the Phase 1 exit asks for at least 90%.
- Developer: pass@1 and pass@5: how often code passes first time, and by the fifth attempt.
- Review: the Review Agent is a judge, so we check the judge: its verdicts against tech leads' at H3.
- Test: defects escaping to UAT and production, against the baseline.
- Release: deployments that succeed, and rollbacks.
- Change Guardian: conflicts it missed, and blocks that were not needed.

WHAT IS PASS@K
pass@k is the share of steps that pass every check within k attempts. pass@1 is "right first time". pass@5 is "right by the fifth attempt", which is the last one before the step stops and an owner takes over. Example: if 100 build steps run and 70 pass on the first attempt and 95 pass by the fifth, pass@1 is 70% and pass@5 is 95%; the other 5 stopped and went to a person. A high pass@5 with a low pass@1 means the agent gets there, but with a lot of rework.

IF ASKED
- What are the targets? Set from the Phase 0 baseline and agreed with Ascension, reviewed monthly.
- What happens when a score falls? That agent goes back through diagnose and tune on the closed loop; the fix must pass the golden set before release."""


# ================================================================== glow-background slides (template pages 43-44)
BG_BLUE = os.path.join(HERE, "assets", "bg-glow-blue.jpg")
BG_MAGENTA = os.path.join(HERE, "assets", "bg-glow-magenta.jpg")


def set_bg_image(slide, path):
    """Template background as the slide's own background fill: full-bleed, and it cannot be moved."""
    _, rid = slide.part.get_or_add_image_part(path)
    cSld = slide._element.find(p("cSld"))
    old = cSld.find(p("bg"))
    if old is not None:
        cSld.remove(old)
    cSld.insert(0, etree.fromstring(
        '<p:bg xmlns:p="%s" xmlns:a="%s" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<p:bgPr><a:blipFill dpi="0" rotWithShape="1"><a:blip r:embed="%s"/><a:srcRect/>'
        '<a:stretch><a:fillRect/></a:stretch></a:blipFill><a:effectLst/></p:bgPr></p:bg>' % (P, A, rid)))


def glass(cv, x, y, w, h, line=None, alpha=55, radius=0.06, lw=1.25):
    """Translucent dark card, so the glow shows through but text stays readable."""
    sp = cv.rect(x, y, w, h, BLACK, line, lw, MSO_SHAPE.ROUNDED_RECTANGLE, radius)
    clr = sp._element.spPr.find(a("solidFill")).find(a("srgbClr"))
    etree.SubElement(clr, a("alpha"), val=str(alpha * 1000))
    return sp


EVAL_STEPS = [
    ("Golden set", "Past Ascension changes labelled by your experts against a written rubric: every pod, cloud, "
                   "change type and risk level."),
    ("Offline gate", "No prompt, skill or model change goes live unless it passes: per-agent scores, pass@1 to "
                     "pass@5."),
    ("Guarded run", None),
    ("Sample + label", "Each week a sample of approved changes is re-reviewed blind by Ascension experts, same "
                       "rubric."),
    ("Diagnose", "A diagnoser run pins each miss to the agent, step or missing context that caused it."),
    ("Tune + re-test", "Fix the harness: context, skill, rule or prompt. Re-run the golden set, then release."),
]
RUN_REPORT = [
    ("pass@k", "steps passing on attempt 1, and by attempt 5"),
    ("Time", "per step and end to end, story to release"),
    ("Re-run time", "time and cost spent on attempts 2 to 5"),
    ("Waiting time", "how long each human gate held the run"),
    ("Agent scores", "each agent on its own job; Review Agent vs tech leads"),
    ("Escaped defects", "found in UAT or production, vs baseline"),
    ("Stopped runs", "where it stopped, why, and who took over"),
]


def evals_combined_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg_image(s, BG_BLUE)
    cv = Canvas(s)
    dark_header(cv, "ASCENSION MAD APPROACH · CLOSED-LOOP EVALS",
                "Closed-loop evals: every attempt bounded, every miss makes it better",
                "Offline tests and live results feed one loop. No step runs forever: after %d attempts it stops and "
                "a named owner takes over." % MAX_ATTEMPTS)
    bw, gx = 2.2, 0.26
    xs = [0.5 + i * (bw + gx) for i in range(3)]
    y1, h1 = 1.4, 1.62
    y2, h2 = 4.44, 1.36
    pos = [(xs[0], y1, h1), (xs[1], y1, h1), (xs[2], y1, h1), (xs[2], y2, h2), (xs[1], y2, h2), (xs[0], y2, h2)]
    for i, (name, desc) in enumerate(EVAL_STEPS):
        bx, by, bh = pos[i]
        if i == 2:                                           # the bounded loop lives here
            fx, fy, fw, fh = cv.frame(bx, by, bw, bh, BLACK, 0.04)
            bx, by, bw_, bh = fx, fy, fw, fh
        else:
            glass(cv, bx, by, bw, bh, "F5A623")
            bw_ = bw
        cv.text(bx + 0.12, by + 0.08, 0.32, 0.28, str(i + 1), size=13, font=LIGHT, color=CYAN,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(bx + 0.44, by + 0.08, bw_ - 0.52, 0.28, name, size=10.5, bold=True, color=WHITE,
                anchor=MSO_ANCHOR.MIDDLE)
        if desc:
            cv.text(bx + 0.14, by + 0.42, bw_ - 0.26, bh - 0.46, desc, size=7.5, color=SOFT)
        else:
            cv.text(bx + 0.14, by + 0.4, bw_ - 0.26, 0.3, "Every step checked; at most %d attempts" % MAX_ATTEMPTS,
                    size=7.5, color=SOFT)
            for k in range(MAX_ATTEMPTS):
                last = k == MAX_ATTEMPTS - 1
                ox = bx + 0.16 + k * 0.38
                cv.rect(ox, by + 0.74, 0.28, 0.28, MAGENTA if last else None, MAGENTA if last else CYAN, 1.25,
                        MSO_SHAPE.OVAL)
                cv.text(ox, by + 0.74, 0.28, 0.28, str(k + 1), size=8, bold=True, color=WHITE,
                        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            cv.text(bx + 0.14, by + 1.08, bw_ - 0.26, 0.42,
                    [[("STOP: ", {"bold": True, "color": YELLOW}),
                      ("nothing released; the owner gets every attempt in Jira.", {"color": WHITE})]], size=7.5)
    for i in (0, 1):
        cv.arrow(xs[i] + bw + 0.02, y1 + h1 / 2, xs[i + 1] - 0.02, y1 + h1 / 2, CYAN, 1.5)
    for i in (2, 1):
        cv.arrow(xs[i] - 0.02, y2 + h2 / 2, xs[i - 1] + bw + 0.02, y2 + h2 / 2, CYAN, 1.5)
    cv.arrow(xs[2] + bw / 2, y1 + h1 + 0.04, xs[2] + bw / 2, y2 - 0.04, CYAN, 1.5)
    cv.arrow(xs[0] + bw / 2, y2 - 0.04, xs[0] + bw / 2, y1 + h1 + 0.04, CYAN, 1.5)
    mid = (y1 + h1 + y2) / 2
    cv.text(xs[1], mid - 0.5, bw, 0.3, "CLOSED-LOOP", size=11, bold=True, color=CYAN, track=150,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(xs[1], mid - 0.2, bw, 0.4, "EVALS", size=22, bold=True, color=WHITE, track=150,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(xs[1] - 0.3, mid + 0.22, bw + 0.6, 0.3, "one loop that never stops; no step that never ends",
            size=7.5, color=SOFT, align=PP_ALIGN.CENTER)
    # run report
    mx, my, mw, mh = 7.75, 1.4, 5.13, 3.28
    glass(cv, mx, my, mw, mh, CYAN)
    cv.label(mx + 0.22, my + 0.16, mw - 0.4, "Every run reports", color=YELLOW)
    rh_ = (mh - 0.52) / len(RUN_REPORT)
    for i, (k, d) in enumerate(RUN_REPORT):
        y = my + 0.42 + i * rh_
        if i:
            cv.rect(mx + 0.22, y - 0.02, mw - 0.44, 0.006, "3A5A70")
        cv.text(mx + 0.22, y, 1.5, rh_ - 0.04, k, size=9.5, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(mx + 1.75, y, mw - 1.95, rh_ - 0.04, d, size=8, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)
    # proven at scale
    py_ = my + mh + 0.14
    fx, fy, fw, fh = cv.frame(mx, py_, mw, 5.8 - py_, BLACK, 0.04)
    cv.text(fx + 0.18, fy + 0.08, fw - 0.36, 0.24, "PROVEN AT SCALE", size=7.5, bold=True, color=YELLOW, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.18, fy + 0.34, fw - 0.36, fh - 0.4,
            [[("Uber Eats runs its food-photo agent on the same closed loop: ", {"bold": True, "color": WHITE}),
              ("labelled golden sets, pass@k, a QA gate before publishing, human labels on production samples and "
               "a diagnoser that triggers tuning (AI Engineer World's Fair 2026).", {"color": SOFT})]], size=7.5)
    # bottom band
    gy, gh = 6.0, 0.52
    glass(cv, 0.45, gy, 12.43, gh, WHITE, alpha=45, radius=0.25)
    cv.text(0.7, gy, 2.4, gh, "NO GAMING THE EVALS", size=7.5, bold=True, color=MAGENTA, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(3.0, gy, 9.7, gh,
            [[("Agents cannot edit tests or the evaluation set; ", {"bold": True, "color": WHITE}),
              ("a held-out set no agent ever sees; any change that deletes or weakens a test is blocked by the "
               "Guardian.", {"color": SOFT})]], size=9, anchor=MSO_ANCHOR.MIDDLE)
    dark_footer(s)
    set_notes(s, EVALS_COMBINED_NOTES)
    return s


def evals_scorecard_glow_slide(prs, layout):
    """The agent scorecard on the template's magenta glow."""
    s = evals_scorecard_slide(prs, layout)
    for sh in list(s.shapes):                   # drop the black row stripes; the glass cards replace them
        if sh.shape_type == 1 and sh.fill.type == 1 and str(sh.fill.fore_color.rgb) == "141414":
            sh._element.getparent().remove(sh._element)
    cSld = s._element.find(p("cSld"))
    bg = cSld.find(p("bg"))
    if bg is not None:
        cSld.remove(bg)
    for sh in s.shapes:                          # magenta labels vanish on the magenta glow: make them yellow
        if sh.has_text_frame:
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    if r.font.color and r.font.color.type is not None and str(r.font.color.rgb) == MAGENTA:
                        r.font.color.rgb = rgb(YELLOW)
    set_bg_image(s, BG_MAGENTA)
    return s


EVALS_COMBINED_NOTES = EVALS_LOOP_NOTES.replace(
    "SLIDE: Closed-loop evals   (about 2 minutes)", "SLIDE: Closed-loop evals with bounded loops   (about 3 minutes)").replace(
    "3 Guarded run: every live step is checked; a step stops after five attempts; when the system is unsure it stops rather than ships.",
    "3 Guarded run, the bounded loop: every live step is checked. If the outcome is not met the agent tries again with the failure as feedback, at most five times. After the fifth attempt the step stops: nothing is released, and a named owner gets every attempt, the failures and the evidence in Jira. Budgets and timeouts can stop it sooner. When the system is unsure, it stops rather than ships.") + """

EVERY RUN REPORTS (right panel)
Every step, attempt and wait is logged (change passport in BigQuery and Cloud Logging), so we report pass@1 to pass@5, time per step and end to end, time and cost spent re-running, waiting time at human gates, agent scores, escaped defects, and stopped runs with where, why and who took over. Weekly to each pod lead.

WHY FIVE
Enough for an agent to correct itself on most failures, low enough to keep cost and time predictable. It is a setting; Ascension can change it per step."""


def evals_scorecard_light_slide(prs, layout):
    """The agent scorecard on white, in the style of the deck's light table slides."""
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION MAD APPROACH · AGENT SCORECARD",
              "Every agent has its own eval, not just the end result",
              "A good end result can hide a weak agent. Each agent is scored on its own job against Ascension's "
              "labelled examples, so a miss points straight at the agent to fix.")
    X0, W = 0.45, 12.43
    cols = [("Agent", 1.9), ("What we check", 3.15), ("Metric", 4.35), ("Labelled or judged by", 3.03)]
    y = 1.3
    x = X0
    for name, w in cols:
        cv.text(x + 0.12, y, w - 0.2, 0.3, name, size=9, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        x += w
    cv.rect(X0, y + 0.34, W, 0.015, BLACK)
    y += 0.4
    rh = 0.52
    for i, row in enumerate(EVAL_SCORECARD):
        if i % 2 == 0:
            cv.rect(X0, y, W, rh, GREY)
        cv.rect(X0 + 0.04, y + rh / 2 - 0.05, 0.1, 0.1, CYAN)
        x = X0
        for j, ((_, w), v) in enumerate(zip(cols, row)):
            pad = 0.24 if j == 0 else 0.12
            cv.text(x + pad, y, w - pad - 0.08, rh, v, size=10 if j == 0 else 9, bold=(j in (0, 2)),
                    color=NAVY if j == 2 else (BLACK if j < 2 else MUTE), anchor=MSO_ANCHOR.MIDDLE)
            x += w
        y += rh
    cv.rect(X0, y, W, 0.015, BLACK)
    by, bh = y + 0.18, 0.56
    cv.rect(X0, by, W, bh, YELLOW_T, YELLOW, 1.0)
    cv.text(X0 + 0.25, by, 2.4, bh, "HOW TARGETS ARE SET", size=7.5, bold=True, track=200,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(X0 + 2.55, by, W - 2.8, bh,
            [[("Each target comes from the Phase 0 baseline and is agreed with Ascension. ", {"bold": True}),
              ("Scores are reviewed monthly; a falling score sends that agent back through diagnose and tune.",
               {"color": MUTE})]], size=9.5, anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, EVALS_SCORECARD_NOTES)
    return s
