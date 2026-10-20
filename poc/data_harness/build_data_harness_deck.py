"""Agentic Harness + data harness: a short black-theme deck on the IG template (6 slides).

1 Title
2 One agent team: seven delivery agents and four data agents
3 The platform, now with the data harness
4 Health Cloud: a story from Codex to production (GCP patient data not needed, shown grey)
5 Marketing Cloud: campaigns on governed GCP data (GCP data required)
6 How PHI is masked in GCP (the ADDG flow)

    python3 build_data_harness_deck.py [out.pptx]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "..", "deck")
sys.path.insert(0, DECK)

from pptx import Presentation                                     # noqa: E402
from pptx.enum.shapes import MSO_SHAPE                             # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN                    # noqa: E402
from pptx.util import Inches                                       # noqa: E402

from build_mad_ig_deck import BLACK, CYAN, GREEN, MAGENTA, NAVY, WHITE, YELLOW, Canvas, set_notes  # noqa: E402
from footer import fix_footers                                     # noqa: E402
from story_slides import dark_header, set_bg                       # noqa: E402

SRC = os.path.join(DECK, "source", "Ascension Agentic Harness - final.pptx")
OUT = os.path.join(HERE, "Ascension Agentic Harness - Data Harness.pptx")
LOGOS = os.path.join(DECK, "assets", "logos")
R = MSO_SHAPE.ROUNDED_RECTANGLE

CARD, CARD2, EDGE = "141414", "1E1E1E", "3A3A3A"
SOFT, DIM = "BFBFBF", "8C8C8C"
VIO = "8B7CD8"
GREY_BG, GREY_LN, GREY_TX = "0E0E0E", "3A3A3A", "6B6B6B"
TINT = {CYAN: "06262B", YELLOW: "2B2508", MAGENTA: "2B0716", VIO: "1A1630", GREEN: "0E2A08", NAVY: "0A1A24"}


# ------------------------------------------------------------------ helpers
def new_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg(s, BLACK)
    return s, Canvas(s)


def logo(cv, name, x, y, size):
    cv.s.shapes.add_picture(os.path.join(LOGOS, name + ".png"), Inches(x), Inches(y), Inches(size), Inches(size))


def badge(cv, x, y, n, color=CYAN, size=0.22):
    cv.rect(x, y, size, size, color, None, shape=MSO_SHAPE.OVAL)
    cv.text(x, y, size, size, str(n), size=6.6, bold=True, color=BLACK, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)


def pill(cv, x, y, w, t, color, filled=False, h=0.18, size=5.6, tcolor=None):
    cv.rect(x, y, w, h, color if filled else None, color, 0.75, R, 0.5)
    cv.text(x, y, w, h, t, size=size, bold=True, color=tcolor or (BLACK if filled else color),
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=80)


def card(cv, x, y, w, h, title, body=None, line=EDGE, fill=CARD, n=None, ncolor=CYAN, tag=None, lw=1.0,
         dash=None, tsize=8, bsize=6.5, tcolor=WHITE, bcolor=SOFT, icon=None):
    cv.rect(x, y, w, h, fill, line, lw, R, 0.07, dash=dash)
    tx = x + 0.1
    if n is not None:
        badge(cv, x + 0.08, y + 0.07, n, ncolor)
        tx = x + 0.36
    if icon:
        logo(cv, icon, tx, y + 0.07, 0.2)
        tx += 0.26
    right = 0.08
    if tag:
        tw = 0.18 + 0.055 * len(tag[0])
        pill(cv, x + w - tw - 0.08, y + 0.08, tw, tag[0], tag[1], tag[2] if len(tag) > 2 else False)
        right = tw + 0.14
    cv.text(tx, y + 0.06, x + w - tx - right, 0.22, title, size=tsize, bold=True, color=tcolor,
            anchor=MSO_ANCHOR.MIDDLE)
    if body:
        if isinstance(body, str):
            body = [body]
        cv.text(x + 0.1, y + 0.31, w - 0.2, h - 0.34, [[(b, {})] if isinstance(b, str) else b for b in body],
                size=bsize, color=bcolor, after=1)


def bar(cv, x, y, w, t, sub, color, tcolor=BLACK, h=0.3):
    cv.rect(x, y, w, h, color, None)
    cv.text(x + 0.1, y, w - 0.2, h, [[(t, {"bold": True, "track": 150}), ("   " + sub, {"color": tcolor})]
                                     if sub else [(t, {"bold": True, "track": 150})]],
            size=7, color=tcolor, anchor=MSO_ANCHOR.MIDDLE)


def path(cv, pts, color, w=1.5, dash=None):
    for k, (p, q) in enumerate(zip(pts, pts[1:])):
        cv.arrow(p[0], p[1], q[0], q[1], color, w, dash=dash, head=(k == len(pts) - 2))


# ================================================================== 1 title
def title_slide(prs):
    s = prs.slides[0]
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text
        if t.startswith("An Agentic Harness"):
            r = sh.text_frame.paragraphs[0].runs
            r[0].text = ("One harness, two jobs: Health Cloud delivery from Codex, and Marketing Cloud campaigns "
                         "on governed, masked Google Cloud data.")
            for extra in r[1:]:
                extra.text = ""
        elif t == "AI-DRIVEN SALESFORCE DELIVERY":
            sh.text_frame.paragraphs[0].runs[0].text = "AGENTS FOR DELIVERY AND DATA"
    set_notes(s, "Open: the same Agentic Harness now does two jobs. For Health Cloud it takes a Jira story to a "
                 "tested, approved change. For Marketing Cloud it plans and prepares campaigns on governed Google "
                 "Cloud data, where agents only ever see masked data and people release the right patients.")


# ================================================================== 2 agent team
DELIVERY = [("Orchestrator", "Classifies the task, gathers context, routes the chain, enforces gates", "COORDINATES",
             CYAN),
            ("Requirements Agent", "Jira story and Confluence design into a clear brief", "HUMAN GATE", YELLOW),
            ("Architect Agent", "Impact, reuse and risk from the graph; the change plan", "HUMAN GATE", YELLOW),
            ("Developer Agent", "Builds to Ascension standards in DEV; journeys for Marketing Cloud", "AI-LED",
             GREEN),
            ("Review Agent", "Quality, security and Ascension coding standards", "HUMAN GATE", YELLOW),
            ("Test Agent", "Unit, regression and performance tests; Zephyr to Copado", "HUMAN GATE", YELLOW),
            ("Release Agent", "Packages and promotes through Copado to lower environments", "AI-LED", GREEN)]
DATA = [("Campaign Strategist", "Ranks campaigns from the masked graph: size, care gap, consent, past lift",
         "HUMAN GATE", YELLOW),
        ("Audience Agent", "Builds the audience on masked views as a BigQuery job: tokens and counts only",
         "AI-LED", GREEN),
        ("Privacy Guard", "Consent first, minimum fields; writes the masked pre-send report", "GUARD", MAGENTA),
        ("Measurement Agent", "Lift against a holdout; writes what worked back to the graph", "AI-LED", GREEN)]

TEAM_NOTES = """SLIDE: One agent team: seven delivery agents and four data agents   (about 2 minutes)

KEY MESSAGE
The seven delivery agents are unchanged and serve every pod. Four data agents are added for campaigns on governed Google Cloud data. They only ever see masked data, and people approve at every gate.

WALK IT
- Left: what the agents read. The engineering sources (Jira, Confluence, Salesforce, Git, Copado, Drive) for every pod. Google Cloud governed data, masked by Collibra policy, only for Marketing Cloud pods: counts and segments, never a patient.
- Middle: the seven delivery agents, then the four data agents: Campaign Strategist (ranks campaigns), Audience (builds the audience on masked views), Privacy Guard (consent first, minimum fields, the pre-send report), Measurement (lift and learning). The Developer Agent builds Marketing Cloud journeys with its Marketing Cloud skills.
- Right: what changes per pod. Health Cloud pods use the delivery agents; Marketing Cloud pods use the delivery and the data agents.
- Bottom: two governed paths. The delivery path is unchanged; the campaign path releases only the minimum fields after a masked pre-send review."""


def team_slide(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · AGENT TEAM",
                "One agent team: seven delivery agents and four data agents",
                "Delivery agents build and release changes for every pod. Data agents plan and prepare campaigns "
                "on masked Google Cloud data. People approve at every gate.")
    top, bot = 1.28, 5.95
    # left: what agents read
    lx, lw = 0.45, 2.75
    bar(cv, lx, top, lw, "WHAT AGENTS READ", "", NAVY, WHITE)
    cv.rect(lx, top + 0.3, lw, bot - top - 0.3, CARD, EDGE, 0.75)
    srcs = [("jira", "Jira", "stories, criteria, history"), ("confluence", "Confluence", "designs, business rules"),
            ("salesforce", "Salesforce", "objects, Flows, Apex, journeys"), ("git", "Git", "Apex, LWC, metadata"),
            (None, "Copado", "releases, test runs"), ("googledrive", "Google Drive", "specs, mapping sheets")]
    y = top + 0.42
    for ic, n, d in srcs:
        if ic:
            logo(cv, ic, lx + 0.12, y + 0.06, 0.22)
        else:
            pill(cv, lx + 0.12, y + 0.08, 0.22, "Co", SOFT, h=0.2, size=5.2)
        cv.text(lx + 0.42, y, lw - 0.5, 0.36, [[(n, {"bold": True, "color": WHITE})], [(d, {"color": DIM,
                                                                                            "size": 6})]],
                size=7.4, anchor=MSO_ANCHOR.MIDDLE)
        y += 0.42
    cv.text(lx + 0.12, y + 0.02, lw - 0.24, 0.2, "FOR MARKETING CLOUD PODS", size=5.8, bold=True, color=MAGENTA,
            track=120)
    gy = y + 0.25
    cv.rect(lx + 0.1, gy, lw - 0.2, 0.86, TINT[MAGENTA], MAGENTA, 1.25, R, 0.08)
    logo(cv, "googlecloud", lx + 0.2, gy + 0.08, 0.22)
    cv.text(lx + 0.5, gy + 0.05, lw - 0.7, 0.26, "Governed GCP data", size=7.8, bold=True, color=WHITE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(lx + 0.2, gy + 0.33, lw - 0.4, 0.5, "Masked by Collibra policy: agents see counts and segments, "
            "never a patient.", size=6.3, color=SOFT)
    cv.text(lx + 0.12, bot - 0.42, lw - 0.24, 0.36, "Every fact is cited with its source and SHA-256.", size=6.2,
            color=DIM, anchor=MSO_ANCHOR.MIDDLE)

    # middle: agents
    mx, mw = 3.35, 6.35
    bar(cv, mx, top, mw, "DELIVERY AGENTS", "the same on every pod", CYAN)
    rh = 0.345
    y = top + 0.36

    def row(i, n, name, desc, mode, col):
        cv.rect(mx, y, mw, rh - 0.04, CARD if i % 2 == 0 else BLACK, None)
        badge(cv, mx + 0.08, y + (rh - 0.04 - 0.22) / 2, n, col if col != YELLOW else YELLOW)
        cv.text(mx + 0.38, y, 1.65, rh - 0.04, name, size=7.6, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(mx + 2.05, y, mw - 3.15, rh - 0.04, desc, size=6.4, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)
        pill(cv, mx + mw - 1.0, y + (rh - 0.04 - 0.18) / 2, 0.9, mode, col)

    for i, (name, desc, mode, col) in enumerate(DELIVERY):
        row(i, i + 1, name, desc, mode, col)
        y += rh
    y += 0.06
    bar(cv, mx, y, mw, "DATA AGENTS", "new: campaigns on governed, masked data", MAGENTA, WHITE)
    y += 0.36
    for i, (name, desc, mode, col) in enumerate(DATA):
        row(i, i + 8, name, desc, mode, col)
        y += rh

    # right: pod skills
    rx, rw = 9.85, 3.03
    bar(cv, rx, top, rw, "POD SKILLS", "what changes per pod", MAGENTA, WHITE)
    cv.rect(rx, top + 0.3, rw, bot - top - 0.3, CARD, EDGE, 0.75)
    pods = [("Health Cloud pods", "Network Services, Clinical Transformation, Contact Center",
             "Apex, Flows, LWC, sharing, Health Cloud objects", [("DELIVERY AGENTS", CYAN)]),
            ("Marketing Cloud pods", "Nudge / Demand, VBC outreach",
             "Data Cloud, SFMC SQL, AMPscript, journeys", [("DELIVERY + DATA AGENTS", MAGENTA),
                                                            ("GCP DATA", MAGENTA)]),
            ("QA, all pods", "Every release", "Zephyr test cases, Copado robotic and regression", [])]
    y = top + 0.42
    for t, sub, d, tags in pods:
        tx0 = rx + 0.12
        if "Cloud" in t:
            logo(cv, "salesforce", tx0, y + 0.01, 0.2)
            tx0 += 0.27
        cv.text(tx0, y, rw - 0.24, 0.22, t, size=8, bold=True, color=MAGENTA if "Marketing" in t else WHITE,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(rx + 0.12, y + 0.22, rw - 0.24, 0.2, sub, size=6, color=DIM)
        cv.text(rx + 0.12, y + 0.42, rw - 0.24, 0.36, d, size=6.6, color=WHITE)
        tx = rx + 0.12
        for tg, c in tags:
            w = 0.2 + 0.055 * len(tg)
            pill(cv, tx, y + 0.78, w, tg, c)
            tx += w + 0.06
        y += 1.12
    cv.rect(rx + 0.1, bot - 0.62, rw - 0.2, 0.5, TINT[MAGENTA], None, shape=R, radius=0.1)
    cv.text(rx + 0.2, bot - 0.62, rw - 0.4, 0.5, "A new pod adds its sources and skills, not new agents.",
            size=6.6, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)

    # bottom: two governed paths
    by = 6.08
    paths = [("DELIVERY PATH", ["AI build", "Copado", "Quality gates", "DEV", "SIT", "UAT", "Human approval", "CAB",
                                "PROD"], CYAN),
             ("CAMPAIGN PATH", ["Ask in Codex", "Masked audience", "Pre-send review", "Release minimum fields",
                                "SFMC pulls", "Journey runs"], MAGENTA)]
    for k, (lab, steps, col) in enumerate(paths):
        yy = by + k * 0.4
        cv.text(0.45, yy, 1.3, 0.32, lab, size=6.4, bold=True, color=col, track=120, anchor=MSO_ANCHOR.MIDDLE)
        x = 1.8
        sw = (12.88 - 1.8 - (len(steps) - 1) * 0.08) / len(steps)
        for j, st in enumerate(steps):
            gate = st in ("Human approval", "CAB", "UAT", "Pre-send review")
            cv.rect(x, yy, sw, 0.32, TINT[YELLOW] if gate else CARD, YELLOW if gate else col, 0.9, R, 0.3)
            cv.text(x, yy, sw, 0.32, st, size=6.6, bold=gate, color=YELLOW if gate else WHITE,
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            if j < len(steps) - 1:
                cv.arrow(x + sw, yy + 0.16, x + sw + 0.08, yy + 0.16, DIM, 0.75)
            x += sw + 0.08
    set_notes(s, TEAM_NOTES)
    return s


# ================================================================== 3 platform
PLATFORM_NOTES = """SLIDE: The platform, now with the data harness   (about 2 minutes)

KEY MESSAGE
Codex is the engine; the Agentic Harness is everything around it. The data harness adds three things: a data context built on masked BigQuery data, a Privacy Guard and Collibra masking in Govern, and a masked pre-send review in Looker.

WALK IT
- Surface: where people work. Codex (a Jira number for a delivery story, or a campaign question), the Salesforce LWC console, the approval page, the masked pre-send review in Looker, and Jira.
- Runtime and Registry: unchanged. Durable runs, one agent task per step; tools, skills and templates, now including campaign skills and journey templates.
- Context: the knowledge graph and cited retrieval, plus the new data context: masked BigQuery aggregates through Collibra policy tags.
- Govern: Change Guardian, Model Armor guardrails, identities, human gates, evals and the change passport, plus Collibra masking and the Privacy Guard (consent first, minimum fields).
- Bottom: it all runs on what Ascension already owns, including BigQuery, Collibra, DLP, Looker and Spanner."""


def platform_slide(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · PLATFORM",
                "Agentic Harness platform, now with the data harness",
                "Codex is the engine; the harness is everything around it. New: a masked data context, Collibra "
                "masking and a Privacy Guard, and a masked pre-send review.")
    chips = [("7 delivery agents", VIO), ("4 data agents", MAGENTA), ("9-step workflow", VIO),
             ("Campaign run", MAGENTA), ("Pod skill packs", VIO)]
    x = 1.6
    for t, c in chips:
        w = 0.4 + 0.075 * len(t)
        cv.rect(x, 1.27, w, 0.36, None, c, 1.25, R, 0.5)
        cv.text(x, 1.27, w, 0.36, t, size=8.5, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += w + 0.15
    fy, fh = 1.78, 3.98
    cv.rect(0.45, fy, 9.15, fh, None, YELLOW, 1.0, R, 0.03, dash="sysDot")

    def new_tag(x, y):
        pill(cv, x, y, 0.36, "NEW", CYAN, True, h=0.15, size=5)

    # surface
    sx, sw = 0.6, 1.85
    cv.rect(sx, fy + 0.14, sw, fh - 0.28, None, YELLOW, 1.25, R, 0.05)
    logo(cv, "harness", sx + 0.12, fy + 0.26, 0.28)
    cv.text(sx + 0.48, fy + 0.2, sw - 0.56, 0.42, [[("Harness", {})], [("Surface", {})]], size=10, color=WHITE,
            line=0.9)
    surf = [("openai-white", "Codex", "a Jira number, or a campaign ask"),
            ("salesforce", "Salesforce LWC", "the Agentic Harness console"),
            ("people", "Approval page", "SSO · H1-H4 · G1-G3"), ("looker", "Looker review", "the masked pre-send report"),
            ("jira", "Jira", "status of every step")]
    y = fy + 0.75
    for i, (ic, t, d) in enumerate(surf):
        logo(cv, ic, sx + 0.12, y + 0.01, 0.2)
        cv.text(sx + 0.4, y, sw - 0.48, 0.2, t, size=8, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(sx + 0.4, y + 0.2, sw - 0.48, 0.3, d, size=6.3, color=SOFT)
        if t == "Looker review":
            new_tag(sx + sw - 0.46, y + 0.03)
        y += 0.6

    # runtime / registry / context
    mx, mw = 2.6, 4.25

    def block(y, h, title, sub, items, new=None):
        cv.rect(mx, y, mw, h, None, YELLOW, 1.25, R, 0.05)
        cv.text(mx + 0.12, y + 0.06, 1.3, 0.26, title, size=10, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(mx + 0.12, y + 0.32, 1.2, 0.5, sub, size=6, color=DIM)
        iw = (mw - 1.45 - 0.1) / len(items)
        for k, (t, d) in enumerate(items):
            ix = mx + 1.4 + k * iw
            cv.text(ix, y + 0.08, iw - 0.05, 0.2, t, size=7.4, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
                    anchor=MSO_ANCHOR.MIDDLE)
            cv.text(ix, y + 0.3, iw - 0.05, 0.4, d, size=6, color=SOFT, align=PP_ALIGN.CENTER)
            if new and k in new:
                new_tag(ix + (iw - 0.41) / 2, y + h - 0.22)

    block(fy + 0.14, 0.9, "Runtime", "Runs every story or campaign as a durable workflow.",
          [("Orchestration", "Cloud Workflows"), ("Dispatcher", "one agent task per step"),
           ("State + memory", "Firestore checkpoints")])
    block(fy + 1.12, 0.95, "Registry", "What agents may use.",
          [("Tools", "MCP gateway tools"), ("Skills", "Health, Marketing, QA, campaign"),
           ("Templates", "briefs, designs, journeys")], new=[1, 2])
    cy, ch = fy + 2.15, 1.69
    cv.rect(mx, cy, mw, ch, None, YELLOW, 1.25, R, 0.05)
    cv.text(mx + 0.12, cy + 0.06, 1.3, 0.26, "Context", size=10, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(mx + 0.12, cy + 0.32, 1.2, 0.5, "What agents know, always cited.", size=6, color=DIM)
    citems = [("Knowledge graph", "Spanner Graph, GQL"), ("Cited retrieval", "Graph API over MCP"),
              ("Data context", "masked BigQuery aggregates")]
    iw = (mw - 1.45 - 0.1) / 3
    for k, (t, d) in enumerate(citems):
        ix = mx + 1.4 + k * iw
        cv.text(ix, cy + 0.08, iw - 0.05, 0.2, t, size=7.4, bold=True, color=MAGENTA if k == 2 else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(ix, cy + 0.3, iw - 0.05, 0.36, d, size=6, color=SOFT, align=PP_ALIGN.CENTER)
    new_tag(mx + 1.4 + 2 * iw + (iw - 0.41) / 2, cy + 0.62)
    cv.text(mx + 0.12, cy + 0.88, 1.0, 0.16, "SOURCES", size=5.8, bold=True, color=YELLOW, track=150)
    srcs = ["Jira", "Confluence", "Salesforce", "Git", "Copado", "Google Drive", "GCP · BigQuery (masked)"]
    xx, yy = mx + 0.12, cy + 1.08
    for t in srcs:
        w = 0.16 + 0.058 * len(t)
        if xx + w > mx + mw - 0.1:
            xx, yy = mx + 0.12, yy + 0.26
        gcp = t.startswith("GCP")
        cv.rect(xx, yy, w, 0.2, TINT[MAGENTA] if gcp else CARD2, MAGENTA if gcp else EDGE, 0.75, R, 0.4)
        cv.text(xx, yy, w, 0.2, t, size=5.9, bold=gcp, color=MAGENTA if gcp else WHITE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        xx += w + 0.06

    # govern
    gx, gw = 7.0, 2.45
    cv.rect(gx, fy + 0.14, gw, fh - 0.28, None, MAGENTA, 1.5, R, 0.05)
    cv.text(gx + 0.14, fy + 0.2, gw - 0.2, 0.28, "Harness Govern", size=10, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(gx + 0.14, fy + 0.47, gw - 0.2, 0.2, "Safe, controlled and measurable.", size=6, color=DIM)
    gov = [("Change Guardian", False), ("Guardrails in + out · Model Armor", False), ("Identity + access",
                                                                                        False),
           ("Collibra masking + DLP", True), ("Privacy Guard: consent first", True),
           ("Human gates H1-H4, CAB, G1-G3", False), ("Evaluation set", False),
           ("Observability + change passport", False)]
    y = fy + 0.78
    for t, nw in gov:
        cv.text(gx + 0.14, y, gw - 0.6, 0.34, t, size=7.4, bold=True, color=MAGENTA if nw else WHITE,
                anchor=MSO_ANCHOR.MIDDLE)
        if nw:
            new_tag(gx + gw - 0.48, y + 0.1)
        y += 0.38

    # differentiators
    dx, dw = 9.75, 3.13
    cv.text(dx, 1.8, dw, 0.26, "Differentiators", size=11, bold=True, color=MAGENTA, anchor=MSO_ANCHOR.MIDDLE)
    diffs = [("Grounded in the org and its data", "Agents read a cited graph of the delivery estate, and masked "
              "aggregates for campaigns.", "Ask before build."),
             ("No pod breaks another", "The Change Guardian checks every change against who owns and uses it.",
              "Governed by design."),
             ("Agents never see a patient", "Collibra policy masks PHI; only counts and tokens; minimum "
              "fields released after review.", "Private by design.")]
    y = 2.12
    for i, (t, d, k) in enumerate(diffs):
        cv.rect(dx, y, dw, 1.12, CARD, WHITE, 1.0, R, 0.1)
        badge(cv, dx + 0.12, y + 0.14, i + 1, MAGENTA, 0.3)
        cv.text(dx + 0.52, y + 0.1, dw - 0.6, 0.26, t, size=8.4, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(dx + 0.52, y + 0.38, dw - 0.6, 0.46, d, size=6.5, color=SOFT)
        cv.text(dx + 0.52, y + 0.84, dw - 0.6, 0.2, k, size=6.5, color=MAGENTA)
        y += 1.22

    # core components
    by = 5.9
    cv.rect(0.45, by, 12.43, 0.95, None, WHITE, 1.25, R, 0.4)
    cv.text(0.8, by + 0.08, 2.0, 0.2, "ASCENSION CORE COMPONENTS", size=6, bold=True, color=WHITE, track=150)
    cv.text(0.8, by + 0.36, 2.0, 0.5, [[("Infrastructure", {"size": 11})], [("Runs in Ascension's cloud", {"size":
                                                                                                       6.5,
                                                                                                       "color":
                                                                                                       SOFT})]],
            size=11, color=WHITE)
    comps = [("salesforce", "Salesforce", "Health, Marketing + Data Cloud"),
             ("git", "Delivery", "Copado, Git, Jira, Zephyr"),
             ("googlebigquery", "Data", "BigQuery, Collibra, DLP, Looker, Spanner"),
             ("openai-white", "Models", "Codex Enterprise; model in config; tools via MCP"),
             ("googlecloud", "Cloud", "Google Cloud: Cloud Run, VPC-SC, CMEK")]
    cw_ = (12.88 - 3.0 - 0.2) / 5
    for i, (ic, t, d) in enumerate(comps):
        x = 3.0 + i * cw_
        logo(cv, ic, x, by + 0.14, 0.22)
        x += 0.3
        cv.text(x, by + 0.12, cw_ - 0.4, 0.26, t, size=9, bold=True, color=MAGENTA if t == "Data" else WHITE,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x, by + 0.4, cw_ - 0.4, 0.45, d, size=6.6, color=SOFT)
    set_notes(s, PLATFORM_NOTES)
    return s


# ================================================================== 4 Health Cloud flow
HC_NOTES = """SLIDE: Health Cloud: a story from Codex to production   (about 3 minutes)

KEY MESSAGE
For Health Cloud the harness delivers a change, not a campaign, so it needs the engineering context, not patient data. The governed GCP data source is shown grey: it is not used for delivery stories.

WALK IT
1 A team member enters NS-1234 in Codex or the Salesforce console: an HFN validation rule for Texas CIN.
2 The Requirements Agent reads Jira and Confluence and the knowledge graph; the product owner approves the brief (H1).
3 The Architect Agent checks what already exists, its impact and its owners; the Change Guardian names affected pods; the architect and pod owners approve (H2).
4 The Developer Agent builds in the DEV sandbox on its own branch.
5 The Review and Test Agents check code, security and sharing, and run the tests; a failed check goes back to the Developer Agent, at most five times, then to a named owner; the tech lead approves (H3).
6 The Release Agent promotes through Copado to SIT and UAT; business signs UAT (H4); CAB approves; the owning team deploys to production. No agent holds a production credential.
Every step is scored by evals and recorded in the change passport."""


def health_slide(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · HEALTH CLOUD FLOW",
                "Health Cloud: one story from Codex to production",
                "Example: NS-1234, an HFN validation rule for Texas CIN. Delivery needs the engineering context, not "
                "patient data, so the GCP data source stays out (grey).")
    # row 1: the run frame
    y1 = 1.3
    cv.rect(0.45, y1, 3.05, 0.78, BLACK, CYAN, 1.25, R, 0.1)
    badge(cv, 0.53, y1 + 0.08, 1)
    logo(cv, "openai-white", 0.82, y1 + 0.07, 0.22)
    cv.text(1.1, y1 + 0.05, 2.3, 0.26, "Start in Codex or the LWC", size=8, bold=True, color=WHITE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.57, y1 + 0.36, 2.85, 0.4, "“Deliver NS-1234: HFN validation rule for Texas CIN”", size=6.8,
            color=SOFT, font="Courier New")
    frame = [("Run orchestration", "Cloud Workflows: 9 steps, checkpoints, resumable", CYAN),
             ("Tool gateway", "3 identities: read, develop, release; no production", MAGENTA),
             ("Evals on every step", "Scored before it moves; max 5 retries, then a named owner", YELLOW)]
    x = 3.65
    fw = (12.88 - 3.65 - 2 * 0.15) / 3
    for t, d, c in frame:
        card(cv, x, y1, fw, 0.78, t, d, line=c, fill=TINT[c], bsize=6.5)
        x += fw + 0.15
    cv.arrow(3.5, y1 + 0.39, 3.65, y1 + 0.39, CYAN, 1.5)

    # row 2: the chain
    y2, h2 = 2.4, 1.5
    chain = [("a", "Requirements", "Brief from the Jira story + Confluence design; open questions flagged.", 2),
             ("g", "H1", "product owner"),
             ("a", "Architect", "Reuse and impact from the graph; Change Guardian names affected pods.", 3),
             ("g", "H2", "architect + pod owners"),
             ("a", "Developer", "Validation rule, Flow and tests in the DEV sandbox, on its own branch.", 4),
             ("a", "Review + Test", "Code, security and sharing checks; Apex tests and Zephyr cases.", 5),
             ("g", "H3", "tech lead + security"),
             ("a", "Release", "Copado promotion to SIT, then UAT; rollback plan and CAB pack.", 6),
             ("g", "H4 · CAB", "business UAT, then CAB"),
             ("p", "Production", "the owning team deploys; no agent credential")]
    widths = {"a": 1.6, "g": 0.62, "p": 1.0}
    total = sum(widths[c[0]] for c in chain) + (len(chain) - 1) * 0.1
    x = 0.45 + (12.43 - total) / 2
    xs = {}
    for c in chain:
        w = widths[c[0]]
        if c[0] == "a":
            card(cv, x, y2, w, h2 - 0.28, c[1] + " Agent" if c[1] != "Review + Test" else "Review + Test Agents",
                 c[2], line=CYAN, fill=CARD, n=c[3], tsize=7.4, bsize=6.3)
            pill(cv, x + (w - 0.5) / 2, y2 + h2 - 0.22, 0.5, "EVALS", YELLOW, True, h=0.17)
        elif c[0] == "g":
            cv.rect(x, y2, w, h2 - 0.28, YELLOW, None, shape=R, radius=0.2)
            logo(cv, "people-black", x + (w - 0.2) / 2, y2 + 0.1, 0.2)
            cv.text(x + 0.03, y2 + 0.3, w - 0.06, 0.3, c[1], size=8.5, bold=True, color=BLACK,
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            cv.text(x + 0.03, y2 + 0.62, w - 0.06, 0.55, c[2], size=6, color=BLACK, align=PP_ALIGN.CENTER)
        else:
            cv.rect(x, y2, w, h2 - 0.28, None, SOFT, 1.0, R, 0.1, dash="dash")
            cv.text(x + 0.06, y2 + 0.1, w - 0.12, 0.26, c[1], size=8, bold=True, color=WHITE,
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            cv.text(x + 0.06, y2 + 0.42, w - 0.12, 0.7, c[2], size=6.2, color=SOFT, align=PP_ALIGN.CENTER)
        xs[c[1]] = (x, w)
        x += w + 0.1
    keys = [c[1] for c in chain]
    for k1, k2 in zip(keys, keys[1:]):
        x1 = xs[k1][0] + xs[k1][1]
        cv.arrow(x1, y2 + (h2 - 0.28) / 2, x1 + 0.1, y2 + (h2 - 0.28) / 2, WHITE, 1.0)
    # 1 -> 2: the Codex ask starts the Requirements Agent
    rqx, rqw = xs["Requirements"]
    cv.arrow(rqx + rqw / 2, y1 + 0.78, rqx + rqw / 2, y2, CYAN, 1.75)
    # bounded retry: a failed check in 5 goes back to 4, over the top
    dvx, dvw = xs["Developer"]
    rtx, rtw = xs["Review + Test"]
    ly_ = y2 - 0.14
    path(cv, [(rtx + 0.35, y2), (rtx + 0.35, ly_), (dvx + dvw - 0.35, ly_), (dvx + dvw - 0.35, y2)], MAGENTA, 1.75)
    pill(cv, rtx + 0.45, ly_ - 0.09, 1.95, "5 → 4  FAIL → FIX · MAX 5, THEN OWNER", MAGENTA, True, h=0.18,
         tcolor=WHITE)

    # row 3: knowledge graph + systems
    y3 = 4.05
    kx, kw = 0.45, 7.55
    cv.rect(kx, y3, kw, 1.72, TINT[VIO], VIO, 1.25, R, 0.05)
    cv.text(kx + 0.14, y3 + 0.06, kw - 0.3, 0.24, [[("ENGINEERING CONTEXT KNOWLEDGE GRAPH", {"bold": True,
                                                                                         "track": 150}),
                                                  ("   Spanner Graph · every fact cited", {"color": SOFT})]],
            size=7, color=VIO, anchor=MSO_ANCHOR.MIDDLE)
    srcs = [("jira", "Jira", "stories, history"), ("confluence", "Confluence", "designs, rules"),
            ("salesforce", "Salesforce", "Health Cloud metadata"), ("git", "Git", "Apex, LWC, tests"),
            (None, "Copado", "releases, test runs"), ("googledrive", "Google Drive", "specs")]
    sw = (kw - 0.28 - 6 * 0.08) / 7
    for i, (ic, n, d) in enumerate(srcs):
        x = kx + 0.14 + i * (sw + 0.08)
        cv.rect(x, y3 + 0.38, sw, 0.62, CARD, VIO, 0.9, R, 0.1)
        if ic:
            logo(cv, ic, x + 0.08, y3 + 0.45, 0.2)
        else:
            pill(cv, x + 0.08, y3 + 0.46, 0.2, "Co", SOFT, h=0.18, size=5)
        cv.text(x + 0.33, y3 + 0.42, sw - 0.36, 0.24, n, size=7, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.08, y3 + 0.7, sw - 0.12, 0.28, d, size=5.8, color=SOFT)
    # the GCP source, grey: not needed for Health Cloud delivery
    x = kx + 0.14 + 6 * (sw + 0.08)
    cv.rect(x, y3 + 0.38, sw, 0.62, GREY_BG, GREY_LN, 0.9, R, 0.1, dash="dash")
    logo(cv, "googlecloud-grey", x + 0.08, y3 + 0.45, 0.2)
    cv.text(x + 0.33, y3 + 0.42, sw - 0.36, 0.24, "GCP data", size=7, bold=True, color=GREY_TX,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(x + 0.08, y3 + 0.66, sw - 0.12, 0.32, "not needed for Health Cloud stories", size=5.6, color=GREY_TX)
    qs = ["graph.exists", "graph.find_reuse", "graph.blast_radius", "graph.owners", "graph.context_slice"]
    xx = kx + 0.14
    cv.text(xx, y3 + 1.1, 1.3, 0.2, "AGENTS ASK", size=5.8, bold=True, color=VIO, track=150,
            anchor=MSO_ANCHOR.MIDDLE)
    xx += 0.85
    for q in qs:
        w = 0.16 + 0.06 * len(q)
        cv.rect(xx, y3 + 1.1, w, 0.2, CARD2, EDGE, 0.75, R, 0.4)
        cv.text(xx, y3 + 1.1, w, 0.2, q, size=5.8, color=WHITE, font="Courier New", align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        xx += w + 0.06
    cv.text(kx + 0.14, y3 + 1.38, kw - 0.3, 0.26, "A bounded, cited context slice for each step, never a raw org "
            "dump. Agents never write queries.", size=6.4, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)
    # graph feeds requirements + architect
    for k in ("Requirements", "Architect"):
        x0, w0 = xs[k]
        cv.arrow(x0 + 0.3, y3, x0 + 0.3, y2 + h2 - 0.28, VIO, 1.5)

    # systems written
    sx, sw2 = 8.15, 4.73
    cv.rect(sx, y3, sw2, 1.72, CARD, EDGE, 0.75, R, 0.05)
    cv.text(sx + 0.14, y3 + 0.06, sw2 - 0.3, 0.24, [[("WHERE OUTPUT LANDS", {"bold": True, "track": 150}),
                                                    ("   through the tool gateway", {"color": SOFT})]],
            size=7, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    outs = [("jira", "Jira", "brief, status to Done"), ("confluence", "Confluence", "design draft, as-built"),
            ("git", "Git", "branch, pull request"), ("salesforce", "Salesforce DEV", "deploy, Apex tests"),
            (None, "Copado", "SIT, then UAT"), (None, "Zephyr Scale", "cases, results")]
    for i, (ic, n, d) in enumerate(outs):
        x = sx + 0.14 + (i % 2) * 2.25
        y = y3 + 0.36 + (i // 2) * 0.35
        if ic:
            logo(cv, ic, x, y + 0.05, 0.2)
        else:
            pill(cv, x, y + 0.06, 0.2, "Co" if n == "Copado" else "ZS", SOFT, h=0.18, size=5)
        cv.text(x + 0.27, y, 1.95, 0.32, [[(n, {"bold": True, "color": WHITE}), ("  " + d, {"color": SOFT,
                                                                                              "size": 6})]],
                size=7, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(sx + 0.14, y3 + 1.42, sw2 - 0.3, 0.22, "Production: the owning team's pipeline after CAB. No agent path.",
            size=6.4, bold=True, color=MAGENTA, anchor=MSO_ANCHOR.MIDDLE)

    # bottom line
    by = 5.95
    cells = [("~2 weeks → ~2 days", "per Health Cloud task, story to UAT"),
             ("People approve", "H1, H2, H3, H4 and CAB, as today"),
             ("Change passport", "every step, approval and test recorded")]
    cw_ = (12.43 - 2 * 0.15) / 3
    for i, (t, d) in enumerate(cells):
        x = 0.45 + i * (cw_ + 0.15)
        cv.rect(x, by, cw_, 0.85, CARD, None)
        cv.rect(x, by, 0.06, 0.85, (CYAN, YELLOW, MAGENTA)[i], None)
        cv.text(x + 0.22, by + 0.08, cw_ - 0.3, 0.4, t, size=14, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.22, by + 0.48, cw_ - 0.3, 0.3, d, size=7, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, HC_NOTES)
    return s


# ================================================================== 5 Marketing Cloud campaigns
MC_NOTES = """SLIDE: Marketing Cloud: campaigns on governed GCP data   (about 3 minutes)

KEY MESSAGE
For Marketing Cloud the governed GCP data is required: it is where the patients are. Agents only ever see it masked; people review a masked pre-send report; only then are the minimum fields released for Marketing Cloud to pull, and the journey starts by itself.

WALK IT (follow the numbers)
- Sources: Epic, athenahealth, Strata, SFDC leads, SFMC engagement, CallRail, forms and direct mail land in BigQuery; DLP classifies, the Collibra steward approves, policy tags mask PHI.
1 The marketer asks in Codex: "What are the top 10 campaigns I can run for heart patients?"
2-3 The Campaign Strategist reads the knowledge graph built on masked data and ranks campaigns.
4 The marketer picks (G1).
5-6 The Audience Agent and Privacy Guard build the audience on masked views, consent first: tokens and counts per run ID.
7 The SME and tech lead approve the masked pre-send report (G2).
8 The Developer Agent builds the data extension, the pull and the journey from approved templates; clinical and compliance approve (G3).
9 Only after G2 and G3: token, name, email, phone, condition group and discharge date go to the release store, time-limited.
10 Marketing Cloud pulls; new records start the journey; consent and STOP are re-checked at send.
11 Engagement comes back; the Measurement Agent measures lift and the graph learns."""


def marketing_slide(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · MARKETING CLOUD CAMPAIGNS",
                "Marketing Cloud: ask in Codex, agents work masked, people release the right patients",
                "Here the governed GCP data is required. Agents see counts and tokens; a masked pre-send report is "
                "approved before the minimum fields reach Marketing Cloud.")
    X0, X1 = 0.45, 10.38
    W = X1 - X0
    cx = [0.88 + i * 2.38 for i in range(4)]
    cw = 2.25
    lanes = [(1.28, 1.1, "PEOPLE", "2A2A2A", WHITE, CARD, EDGE, "people"),
             (2.46, 1.04, "HARNESS", "0A4A52", WHITE, TINT[CYAN], CYAN, "harness"),
             (3.58, 2.04, "GOOGLE CLOUD", "3A0A1E", WHITE, BLACK, MAGENTA, "googlecloud")]
    for y, h, t, lc, tc, fill, line, ic in lanes:
        cv.rect(X0, y, W, h, fill, line, 1.0, R, 0.03, dash="dash" if t == "GOOGLE CLOUD" else None)
        cv.rect(X0, y, 0.3, h, lc, None)
        logo(cv, ic, X0 + 0.04, y + 0.08, 0.22)
        tb = cv.text(0.6 - (h - 0.3) / 2, y + 0.3 + (h - 0.3) / 2 - 0.14, h - 0.3, 0.28, t, size=6.6, bold=True, color=tc,
                     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=150)
        tb.rotation = 270
    p_y, p_h = 1.43, 0.82
    a_y, a_h = 2.62, 0.74
    d_y, d_h = 3.7, 0.95

    # people
    cv.rect(cx[0], p_y, cw, p_h, BLACK, CYAN, 1.0, R, 0.1)
    badge(cv, cx[0] + 0.07, p_y + 0.06, 1)
    logo(cv, "openai-white", cx[0] + 0.35, p_y + 0.07, 0.18)
    cv.text(cx[0] + 0.58, p_y + 0.05, cw - 0.64, 0.22, "Ask in Codex", size=7.6, bold=True, color=WHITE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(cx[0] + 0.12, p_y + 0.3, cw - 0.22, p_h - 0.32,
            [[("“Top 10 campaigns I can run for heart patients?”", {})],
             [("or: “Run a campaign for heart patients”", {"color": DIM})]], size=6.3, color=SOFT,
            font="Courier New", after=1)
    card(cv, cx[1], p_y, cw, p_h, "Ranked list · pick", ["1  CHF post-discharge SMS nudge",
                                                          "2  Cardiac rehab referral",
                                                          "3  Statin refill reminder …"],
         line=YELLOW, fill=TINT[YELLOW], n=4, tag=("G1", YELLOW, True), bsize=6)
    card(cv, cx[2], p_y, cw, p_h, "Pre-send review", ["SME + tech lead approve a masked report: counts, consent, "
                                                      "exclusions.", [("No PHI on screen.", {"bold": True,
                                                                                              "color": MAGENTA})]],
         line=YELLOW, fill=TINT[YELLOW], n=7, tag=("G2", YELLOW, True), bsize=6, icon="looker")
    card(cv, cx[3], p_y, cw, p_h, "Approve journey + content", "Clinical and compliance approve messages and "
         "journey; it waits, active, for entries.", line=YELLOW, fill=TINT[YELLOW], tag=("G3", YELLOW, True),
         bsize=6)
    # agents
    card(cv, cx[0], a_y, cw, a_h, "Campaign Strategist", "Reads the masked graph; ranks by size, care gap, "
         "consent, past lift.", line=CYAN, n=2, bsize=6)
    card(cv, cx[1], a_y, cw, a_h, "Audience + Privacy Guard", "Consent first: opt-in per channel, STOP, deceased, "
         "readmitted, duplicates out.", line=CYAN, n=5, bsize=6)
    card(cv, cx[2], a_y, cw, a_h, "Measurement Agent", "Lift against a holdout; writes what worked back to the "
         "graph.", line=CYAN, n=11, bsize=6)
    card(cv, cx[3], a_y, cw, a_h, "Developer Agent · journeys", "Builds the data extension, the pull and the "
         "journey from approved templates.", line=CYAN, n=8, bsize=6)
    # data
    card(cv, cx[0], d_y, cw, d_h, "Knowledge graph", ["Segments, counts, care gaps, consent coverage, past lift.",
                                                     [("Masked: no patient visible.", {"bold": True,
                                                                                       "color": MAGENTA})]],
         line=VIO, fill=TINT[VIO], n=3, ncolor=VIO, bsize=6, icon="googlecloudspanner")
    card(cv, cx[1], d_y, cw, d_h, "Masked audience · BigQuery", ["Tokens and counts per run ID; holdout set aside.",
                                                                [("Agents never unmask.", {"bold": True,
                                                                                           "color": MAGENTA})]],
         line=MAGENTA, n=6, ncolor=MAGENTA, bsize=6, icon="googlebigquery")
    card(cv, cx[2], d_y, cw, d_h, "ROI engine", "EUID matching, attribution, lift vs holdout, Contribution "
         "Margin.", line=EDGE, bsize=6, icon="googlebigquery")
    fx, fy, fw, fh = cv.frame(cx[3], d_y, cw, d_h, BLACK, 0.04)
    badge(cv, fx + 0.05, fy + 0.05, 9, YELLOW)
    logo(cv, "googlecloudspanner", fx + 0.33, fy + 0.05, 0.2)
    cv.text(fx + 0.58, fy + 0.03, fw - 0.62, 0.24, "Release store · Spanner", size=7.6, bold=True, color=WHITE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.08, fy + 0.29, fw - 0.16, fh - 0.3, [[("Only after G2 + G3: ", {"bold": True, "color": YELLOW}),
                                                         ("token, name, email, phone, condition group, discharge "
                                                          "date. Time-limited, read-only API.", {})]],
            size=6, color=SOFT)
    # sources strip: required here
    sy = 5.0
    cv.rect(cx[0], sy, cx[3] + cw - cx[0], 0.5, TINT[MAGENTA], MAGENTA, 1.25, R, 0.2)
    pill(cv, cx[0] + 0.1, sy + 0.16, 0.8, "REQUIRED", MAGENTA, True, tcolor=WHITE)
    cv.text(cx[0] + 1.0, sy, cx[3] + cw - cx[0] - 1.1, 0.5,
            [[("Epic · athenahealth · Strata · SFDC leads · SFMC engagement · CallRail · forms · direct mail", {}),
              ("  → BigQuery →  ", {"bold": True, "color": WHITE}),
              ("DLP classifies, Collibra steward approves, policy tags mask PHI", {"color": MAGENTA})]],
            size=6.3, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)
    # arrows
    m = cw / 2
    cv.arrow(cx[0] + m, p_y + p_h, cx[0] + m, a_y, WHITE, 1.5)
    cv.arrow(cx[0] + m - 0.15, a_y + a_h, cx[0] + m - 0.15, d_y, VIO, 1.5)
    cv.arrow(cx[0] + m + 0.15, d_y, cx[0] + m + 0.15, a_y + a_h, VIO, 1.5)
    gab = cx[0] + cw + 0.065
    path(cv, [(cx[0] + cw, a_y + a_h / 2), (gab, a_y + a_h / 2), (gab, p_y + p_h / 2), (cx[1], p_y + p_h / 2)], CYAN)
    cv.arrow(cx[1] + m, p_y + p_h, cx[1] + m, a_y, YELLOW, 1.5)
    cv.arrow(cx[1] + m, a_y + a_h, cx[1] + m, d_y, CYAN, 1.5)
    gbc = cx[1] + cw + 0.065
    path(cv, [(cx[1] + cw, d_y + 0.6), (gbc, d_y + 0.6), (gbc, p_y + p_h / 2), (cx[2], p_y + p_h / 2)], SOFT)
    gcd = cx[2] + cw + 0.065
    # 7 -> 8: an approved pre-send report lets the Developer Agent build
    path(cv, [(cx[2] + cw, p_y + p_h / 2), (gcd, p_y + p_h / 2), (gcd, a_y + a_h / 2), (cx[3], a_y + a_h / 2)],
         YELLOW, 1.75)
    # 8 -> G3: the built journey goes to clinical + compliance
    cv.arrow(cx[3] + m, a_y, cx[3] + m, p_y + p_h, CYAN, 1.5)
    # G3 -> 9: only then is the release store filled (right-hand side, clear of 7 -> 8)
    gr = cx[3] + cw + 0.065
    path(cv, [(cx[3] + cw, p_y + p_h / 2), (gr, p_y + p_h / 2), (gr, d_y + 0.25), (cx[3] + cw, d_y + 0.25)],
         YELLOW, 1.75)
    cv.arrow(cx[2] + m, d_y, cx[2] + m, a_y + a_h, MAGENTA, 1.5)
    ly = 4.82
    path(cv, [(cx[2] + 0.5, d_y + d_h), (cx[2] + 0.5, ly), (cx[0] + m, ly), (cx[0] + m, d_y + d_h)], GREEN)
    pill(cv, cx[0] + m + 0.15, ly - 0.09, 3.0, "← WHAT WORKED IMPROVES THE NEXT SUGGESTION", GREEN, True)
    # Marketing Cloud, bottom-up
    mx, mw = 10.55, 2.33
    cv.rect(mx, 1.28, mw, 0.3, WHITE, None)
    logo(cv, "salesforce", mx + 0.08, 1.31, 0.24)
    cv.text(mx + 0.4, 1.28, mw - 0.5, 0.3, "MARKETING CLOUD", size=7, bold=True, color=BLACK, track=150,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(mx, 1.58, mw, 4.04, CARD, EDGE, 0.75)
    nx, nw = mx + 0.1, mw - 0.2
    card(cv, nx, 1.7, nw, 0.62, "SMS or email nudge", "Consent, STOP, frequency caps re-checked at send.",
         line=EDGE, fill=BLACK, bsize=6)
    card(cv, nx, 2.48, nw, 0.76, "Journey starts itself", "Built by the Developer Agent (8); new records in the data "
         "extension enter it.", line=EDGE, fill=BLACK, bsize=6)
    fx, fy, fw, fh = cv.frame(nx, 3.4, nw, 0.74, BLACK, 0.04)
    cv.text(fx + 0.08, fy + 0.04, fw - 0.16, 0.22, "Campaign data extension", size=7.6, bold=True, color=WHITE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.08, fy + 0.3, fw - 0.16, fh - 0.32, "Only the released minimum fields, for this run.", size=6,
            color=SOFT)
    card(cv, nx, 4.3, nw, 0.82, "Pulls the released records", "Automation Studio calls the read-only API, scoped "
         "to the run ID.", line=CYAN, fill=TINT[CYAN], n=10, bsize=6, icon="salesforce")
    for lo, hi in ((2.48, 2.32), (3.4, 3.24), (4.3, 4.14)):
        cv.arrow(nx + nw / 2, lo, nx + nw / 2, hi, SOFT, 1.25)
    cv.arrow(cx[3] + cw, d_y + 0.62, nx, 4.62, WHITE, 2.0)
    path(cv, [(nx + nw / 2, 5.12), (nx + nw / 2, 5.56), (cx[2] + 1.6, 5.56), (cx[2] + 1.6, sy + 0.5)], MAGENTA,
         1.25)
    cv.text(nx + nw / 2 + 0.06, 5.15, nw / 2 - 0.06, 0.3, "engagement back to BigQuery", size=5.4, color=MAGENTA,
            anchor=MSO_ANCHOR.MIDDLE)
    # bottom principles
    pr = [("Masked for agents and reviewers", "Collibra policy masks PHI; agents see counts and tokens.", MAGENTA),
          ("Consent decides, people confirm", "No consent for the channel, no message.", VIO),
          ("Minimum necessary leaves", "Only the fields a campaign needs, one run, time-limited.", YELLOW),
          ("Review before release", "The data extension starts the journey, so review comes first.", GREEN)]
    pw = (12.43 - 3 * 0.15) / 4
    for i, (t, d, c) in enumerate(pr):
        x = 0.45 + i * (pw + 0.15)
        cv.rect(x, 5.8, pw, 0.62, CARD, None)
        cv.rect(x, 5.8, 0.06, 0.62, c, None)
        cv.text(x + 0.18, 5.84, pw - 0.26, 0.56, [[(t, {"bold": True, "size": 8, "color": WHITE})],
                                                 [(d, {"color": SOFT})]], size=6.6, anchor=MSO_ANCHOR.MIDDLE,
                after=1)
    set_notes(s, MC_NOTES)
    return s


# ================================================================== 6 masking in GCP (ADDG)
MASK_NOTES = """SLIDE: How PHI is masked in Google Cloud   (about 3 minutes)

KEY MESSAGE
Sensitive BigQuery columns are found by scanning, approved by a data steward in Collibra, then protected automatically with masking or raw-access policies inside BigQuery. Agents, dashboards and reviewers only ever see the masked values.

WALK IT (the approved path, left to right)
- DLP classification: Cloud DLP scans BigQuery columns and proposes an infotype for each (person name, identifier, phone). Results land in the fgac_governance dataset, in the governance tier asc-ahnat-datarepository.
- Steward review: a data steward approves or rejects each classification in Collibra. Nothing changes before that sign-off; Collibra stays the source of truth.
- Reviewed classifications: one governed table (adc_collibra_reviewed_classifications), keyed by project, dataset, table and column.
- Rollout gate: production is enabled project by project; each run logs the promotion SQL for a person to run.
- Data Policy Tagger: a Cloud Run job, the same code in every environment, configured per environment, with a dry-run mode.
- Policies applied: column-level data policies in BigQuery: SHA-256 masking for text and bytes, a numeric-safe policy for numbers. People and agents without raw access see masked values.
- Bindings and validation: every policy is recorded and the table schema is read back to prove it took effect.

REJECTED PATH
If the steward rejects, the policy remover clears the policy, the binding is retired and the column can be reprocessed. The remover is in progress.

WHO SEES WHAT (right)
Agents and the knowledge graph see masked values and aggregates. The pre-send review shows a masked report. Only the release step, under a raw-access service account and only after G2 and G3, reads only the fields a campaign needs."""

ADDG = {  # id: (col, lane, title, subtitle, status)
    "A": (0, 1, ["DLP", "classification"], "Cloud DLP", "UPSTREAM"),
    "B": (1, 0, ["Steward", "review"], "Collibra", "UPSTREAM"),
    "C": (2, 1, ["Reviewed", "classifications"], "governance table", "BUILT"),
    "G": (2, 2, ["Rollout", "gate"], "per project", "BUILT"),
    "T": (3, 2, ["Data Policy", "Tagger"], "Cloud Run job", "LIVE IN DEV"),
    "P": (4, 3, ["Policies", "applied"], "BigQuery columns", "LIVE IN DEV"),
    "V": (5, 1, ["Bindings +", "validation"], "audit trail", "BUILT"),
    "R": (4, 2, ["Policy", "remover"], "rejected path", "IN PROGRESS"),
}
ST_COL = {"UPSTREAM": SOFT, "BUILT": GREEN, "LIVE IN DEV": CYAN, "IN PROGRESS": "FA8B35"}
LANES = [("REVIEW", "Collibra"), ("GOVERNANCE", "asc-ahnat-datarepository"), ("COMPUTE", "asc-datalake"),
         ("TARGET", "asc-ahnat-dataplace")]


def masking_slide(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · DATA GOVERNANCE (ADDG)",
                "How PHI is masked in Google Cloud: classify, approve, protect, prove",
                "Sensitive BigQuery columns are found by scanning, approved by a Collibra data steward, then masked "
                "inside BigQuery. Agents, dashboards and reviewers only ever see masked values.")
    fx0, fx1, fy0 = 0.45, 9.45, 1.3          # the flow, redrawn from the ADDG governance diagram
    lh, lg = 0.92, 0.08
    nx0, pitch, nw, nh = 1.68, 1.29, 1.1, 0.66
    for i, (role, proj) in enumerate(LANES):
        y = fy0 + i * (lh + lg)
        cv.rect(fx0, y, fx1 - fx0, lh, CARD, None)
        cv.rect(fx0, y, 1.1, lh, CARD2, None)
        logo(cv, "people" if role == "REVIEW" else "googlecloud", fx0 + 0.1, y + 0.1, 0.2)
        cv.text(fx0 + 0.1, y + lh / 2 - 0.08, 1.0, 0.4, [[(role, {"bold": True, "color": WHITE, "track": 120})],
                                                       [(proj, {"color": DIM, "size": 5.2, "font": "Courier New"})]],
                size=6.4, anchor=MSO_ANCHOR.MIDDLE, after=1)

    def box(nid):
        c, l = ADDG[nid][:2]
        return nx0 + c * pitch, fy0 + l * (lh + lg) + (lh - nh) / 2

    def right(nid, dy=0.0):
        x, y = box(nid)
        return x + nw, y + nh / 2 + dy

    def left(nid):
        x, y = box(nid)
        return x, y + nh / 2

    def elbow(a, b, dy=0.0):
        (x1, y1), (x2, y2) = right(a, dy), left(b)
        xm = x1 + (x2 - x1) / 2
        return [(x1, y1), (xm, y1), (xm, y2), (x2, y2)]
    for a, b in (("A", "B"), ("B", "C"), ("C", "T"), ("G", "T"), ("T", "P"), ("P", "V")):
        path(cv, elbow(a, b), CYAN, 1.5)
    # rejected path: reviewed classifications -> policy remover -> policy cleared on the column
    rx_, ry_ = box("R")
    x1, y1 = right("C", 0.16)
    path(cv, [(x1, y1), (rx_ + nw / 2, y1), (rx_ + nw / 2, ry_)], MAGENTA, 1.5, dash="dash")
    px_, py_ = box("P")
    path(cv, [(rx_ + nw / 2, ry_ + nh), (px_ + nw / 2, py_)], MAGENTA, 1.5, dash="dash")
    # nodes
    for nid, (c, l, t, sub, st) in ADDG.items():
        x, y = box(nid)
        gate = nid in ("B", "G")
        cv.rect(x, y, nw, nh, TINT[YELLOW] if gate else BLACK, YELLOW if gate else (MAGENTA if nid == "R" else EDGE),
                1.25, R, 0.1, dash="dash" if nid == "G" else None)
        cv.text(x + 0.08, y + 0.04, nw - 0.12, 0.28, [[(t[0], {})], [(t[1], {})]], size=7.2, bold=True,
                color=WHITE, line=0.9)
        sw = 0.14 + 0.05 * len(st)
        pill(cv, x + 0.08, y + 0.34, sw, st, ST_COL[st], h=0.14, size=4.6)
        cv.text(x + 0.08, y + nh - 0.18, nw - 0.12, 0.16, sub, size=5.6, color=DIM, font="Courier New",
                anchor=MSO_ANCHOR.MIDDLE)
    # legend for the paths
    lg_y = fy0 + 4 * (lh + lg) + 0.1
    cv.arrow(1.68, lg_y, 2.08, lg_y, CYAN, 1.5)
    cv.text(2.13, lg_y - 0.08, 1.6, 0.16, "steward approves: protect", size=6, color=SOFT,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.arrow(3.9, lg_y, 4.3, lg_y, MAGENTA, 1.5, dash="dash")
    cv.text(4.35, lg_y - 0.08, 2.4, 0.16, "steward rejects: policy removed, binding retired", size=6, color=SOFT,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(7.0, lg_y - 0.08, 2.4, 0.16, "yellow: a human or rollout gate", size=6, color=SOFT,
            anchor=MSO_ANCHOR.MIDDLE)

    # right: what masking looks like + who sees what
    rx, rw = 9.6, 12.88 - 9.6
    cv.rect(rx, 1.3, rw, 2.12, CARD, EDGE, 0.75, R, 0.05)
    cv.text(rx + 0.12, 1.34, rw - 0.24, 0.24, "WHAT A MASKED COLUMN LOOKS LIKE", size=6.2, bold=True, color=YELLOW,
            track=120, anchor=MSO_ANCHOR.MIDDLE)
    hdr = ["column", "DLP infotype", "without raw access"]
    rows = [("patient_name", "PERSON_NAME", "9f2c…e41a"), ("phone", "PHONE_NUMBER", "71b0…c9d3"),
            ("dob", "DATE_OF_BIRTH", "masked"), ("diagnosis", "medical term", "a4e8…107f"),
            ("encounter_count", "number", "0 (numeric-safe)")]
    xs = [rx + 0.12, rx + 1.08, rx + 2.12]
    for x, t in zip(xs, hdr):
        cv.text(x, 1.62, 1.2, 0.16, t, size=5.6, bold=True, color=DIM)
    for i, row in enumerate(rows):
        y = 1.82 + i * 0.29
        cv.rect(rx + 0.08, y, rw - 0.16, 0.25, CARD2 if i % 2 == 0 else CARD, None)
        for j, (x, v) in enumerate(zip(xs, row)):
            cv.text(x, y, 1.0 if j < 2 else rw - 2.16, 0.25, v, size=6.1, color=MAGENTA if j == 2 else WHITE,
                    font="Courier New", anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(rx, 3.55, rw, 2.15, CARD, EDGE, 0.75, R, 0.05)
    cv.text(rx + 0.12, 3.59, rw - 0.24, 0.24, "WHO SEES WHAT", size=6.2, bold=True, color=YELLOW, track=120,
            anchor=MSO_ANCHOR.MIDDLE)
    who = [("Agents + knowledge graph", "masked values and counts", MAGENTA),
           ("Looker, dashboards", "masked, aggregated views", MAGENTA),
           ("SME + tech lead (G2)", "masked pre-send report", MAGENTA),
           ("Release step (system)", "raw-access service account, minimum fields, after G2 + G3", YELLOW),
           ("Marketing Cloud", "pulls only those fields, for one run", YELLOW)]
    for i, (t, d, c) in enumerate(who):
        y = 3.88 + i * 0.36
        cv.rect(rx + 0.12, y + 0.08, 0.1, 0.1, c, None, shape=MSO_SHAPE.OVAL)
        cv.text(rx + 0.3, y, rw - 0.4, 0.34, [[(t, {"bold": True, "color": WHITE})], [(d, {"color": SOFT,
                                                                                          "size": 5.9})]],
                size=6.8, anchor=MSO_ANCHOR.MIDDLE)

    # built-in controls
    cy = 5.88
    ctrls = [("Human approval first", "No policy until a Collibra steward approves the classification."),
             ("Dry run before apply", "Every run can report its changes without making them."),
             ("Human-gated promotion", "Production rollout by project; the pipeline never promotes itself."),
             ("Auditable bindings", "Each applied or removed policy is recorded and checked against the schema.")]
    cw_ = (12.43 - 3 * 0.15) / 4
    for i, (t, d) in enumerate(ctrls):
        x = 0.45 + i * (cw_ + 0.15)
        cv.rect(x, cy, cw_, 0.92, CARD, None)
        cv.rect(x, cy, 0.06, 0.92, GREEN, None)
        cv.text(x + 0.2, cy + 0.08, cw_ - 0.3, 0.8, [[(t, {"bold": True, "size": 8.4, "color": WHITE})],
                                                    [(d, {"color": SOFT})]], size=6.8, after=2,
                anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, MASK_NOTES)
    return s


# ================================================================== build
def main(out=OUT):
    prs = Presentation(SRC)
    lst = prs.slides._sldIdLst
    for el in list(lst)[1:]:                    # keep only the title slide
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    title_slide(prs)
    team_slide(prs, layout)
    platform_slide(prs, layout)
    health_slide(prs, layout)
    marketing_slide(prs, layout)
    masking_slide(prs, layout)
    for line in fix_footers(prs):
        print(line)
    prs.save(out)
    print("wrote", os.path.abspath(out), "-", len(prs.slides), "slides")


if __name__ == "__main__":
    main(*sys.argv[1:])
