"""Agentic campaigns on governed data: high-level execution flow and detailed design.

A marketer asks Codex for campaign ideas (for example, heart patients). Campaign agents in the Agentic Harness
read a knowledge graph built from governed Google Cloud data, propose ranked campaigns, prepare the approved
audience inside the PHI boundary into Spanner, and Marketing Cloud pulls it through an Audience API. A Journey
Agent builds the journey; people approve at four gates; results flow back to improve the next suggestion.

    python3 campaign_agents.py [out.pptx]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from governance_slide import CYAN_D, GOLD, INK, ORANGE, R, RULE_C, TEMPLATE, path, tag  # noqa: E402
from build_mad_ig_deck import (BLACK, CYAN, CYAN_T, GREEN, GREEN_T, GREY, MAGENTA, MUTE, NAVY, VIOLET,  # noqa
                               VIOLET_T, WHITE, YELLOW, YELLOW_T, Canvas, set_notes)
from pptx import Presentation                                    # noqa: E402
from pptx.enum.shapes import MSO_SHAPE                            # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN                   # noqa: E402

OUT = os.path.join(HERE, "Agentic Campaigns on Governed Data.pptx")
MAG_T = "FBE3F2"


def badge(cv, x, y, n, fill=BLACK):
    cv.rect(x, y, 0.22, 0.22, fill, WHITE, 0.75, MSO_SHAPE.OVAL)
    cv.text(x, y, 0.22, 0.22, str(n), size=6.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)


def box(cv, x, y, w, h, title, body, n=None, fill=WHITE, line=NAVY, lw=1.0, dash=None, tsize=7.6, bsize=6.3,
        gate=None):
    cv.rect(x, y, w, h, fill, line, lw, R, 0.08, dash=dash)
    tx = x + 0.09
    if n is not None:
        badge(cv, x + 0.07, y + 0.06, n)
        tx = x + 0.34
    if gate:
        gw = 0.3
        cv.rect(x + w - gw - 0.07, y + 0.07, gw, 0.17, YELLOW, BLACK, 0.5, R, 0.4)
        cv.text(x + w - gw - 0.07, y + 0.07, gw, 0.17, gate, size=5.6, bold=True, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
    cv.text(tx, y + 0.05, x + w - tx - (0.42 if gate else 0.08), 0.22, title, size=tsize, bold=True,
            anchor=MSO_ANCHOR.MIDDLE)
    if isinstance(body, str):
        body = [body]
    cv.text(x + 0.09, y + 0.3, w - 0.18, h - 0.33, [[(b, {})] if isinstance(b, str) else b for b in body],
            size=bsize, color=INK, after=1)


def lane_band(cv, x, y, w, h, fill, line, title, sub, color=None, dash=None):
    cv.rect(x, y, w, h, fill, line, 1.0 if dash else 0.75, R, 0.03, dash=dash)
    cv.text(x + 0.12, y + 0.03, w - 0.24, 0.22, [[(title, {"bold": True, "track": 150, "color": color or BLACK}),
                                                   ("   " + sub, {"color": MUTE})]], size=6.8,
            anchor=MSO_ANCHOR.MIDDLE)


def side_label(cv, y, h, text, fill, color):
    """Vertical lane label in a strip at the left edge, so no arrow ever crosses it."""
    cv.rect(0.45, y, 0.3, h, fill, None)
    tb = cv.text(0.6 - h / 2, y + h / 2 - 0.14, h, 0.28, text, size=6.6, bold=True, color=color,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=150)
    tb.rotation = 270


def principles(cv, y, items):
    pw = (12.43 - 3 * 0.15) / 4
    for i, (t, d, col) in enumerate(items):
        x = 0.45 + i * (pw + 0.15)
        cv.rect(x, y, pw, 0.58, GREY)
        cv.rect(x, y, 0.06, 0.58, col)
        cv.text(x + 0.18, y + 0.04, pw - 0.26, 0.52, [[(t, {"bold": True, "size": 8})], [(d, {"color": MUTE})]],
                size=6.6, anchor=MSO_ANCHOR.MIDDLE, after=1)


PRINCIPLES = [("Agents never see patient rows", "They reason on counts, metadata and SQL; BigQuery runs the query.",
               MAGENTA),
              ("Governed before it is used", "DLP, steward approval and policy tags on every column.", VIOLET),
              ("People approve at four gates", "Pick the campaign, approve the audience, the content, the launch.",
               GOLD),
              ("Pull, not push · and it learns", "Marketing Cloud pulls approved records; results improve the next "
               "suggestion.", GREEN)]


# ================================================================== high-level execution flow
HL_NOTES = """SLIDE: Agentic campaigns on governed data, the execution flow   (about 3 minutes)

KEY MESSAGE
A marketer asks a question in Codex. The campaign agents answer from a knowledge graph built on governed Google Cloud data, prepare the approved audience inside the PHI boundary, and Marketing Cloud pulls it. People approve at four gates, and every campaign teaches the next one.

WALK IT (follow the numbers)
1 The marketer asks in Codex: "What are the top 10 campaigns I can run for heart patients?" or simply "Run a campaign for heart patients".
2-3 The Campaign Strategist Agent reads the campaign knowledge graph: heart cohorts and care gaps, consent coverage, and how past campaigns performed. The graph holds aggregates and metadata only, never patient rows.
4 Codex shows a ranked list with audience size, channel and expected lift. The marketer picks, for example "run 1 and 2" (gate G1).
5-6 The Audience Agent writes the SQL on governed, policy-tagged views; the Privacy Guard Agent checks every column, consent, suppression and the minimum fields; BigQuery runs it under a governed identity and stages the records.
7 A named approver reviews the audience in Looker (gate G2). Only then are tokenized records published to Spanner, behind a read-only Audience API.
8 The Journey Agent builds the data extension, the pull and the journey as a draft from approved templates; clinical and compliance approve the content (gate G3).
9 Marketing Cloud pulls the approved records through the Audience API into the data extension; marketing ops activates the journey (gate G4).
10 Engagement and booked visits come back to the ROI engine; lift against a holdout is written back to the knowledge graph, so the next suggestion is better."""


def high_level(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION · AGENTIC CAMPAIGNS ON GOVERNED DATA",
              "Ask in Codex, approve, and the agents prepare the campaign for Marketing Cloud to pull",
              "Campaign agents in the Agentic Harness reason on a governed knowledge graph, prepare the audience "
              "inside Google Cloud, and hand Marketing Cloud only approved, tokenized records.")
    X0, X1 = 0.45, 10.38
    W = X1 - X0
    cx = [0.88 + i * 2.38 for i in range(4)]
    cw = 2.25
    # lanes: bands, with vertical labels in a strip at the left edge
    cv.rect(X0, 1.28, W, 1.1, GREY, MUTE, 0.75, R, 0.03)
    cv.rect(X0, 2.46, W, 1.04, CYAN_T, CYAN_D, 0.75, R, 0.03)
    cv.rect(X0, 3.58, W, 2.04, WHITE, NAVY, 1.0, R, 0.02, dash="dash")
    side_label(cv, 1.28, 1.1, "PEOPLE", "D9D9D9", BLACK)
    side_label(cv, 2.46, 1.04, "HARNESS", CYAN_D, WHITE)
    side_label(cv, 3.58, 2.04, "GOOGLE CLOUD", NAVY, WHITE)
    cv.text(0.88, 5.32, 6.3, 0.22, [[("PHI BOUNDARY  ", {"bold": True, "track": 120}),
                                    ("DLP · Collibra steward · policy tags · authorized views · Looker · VPC-SC · CMEK",
                                     {"color": MUTE})]], size=6.2, anchor=MSO_ANCHOR.MIDDLE)
    p_y, p_h = 1.43, 0.82
    a_y, a_h = 2.62, 0.74
    d_y, d_h = 3.74, 1.06

    # people
    cv.rect(cx[0], p_y, cw, p_h, BLACK, None, shape=R, radius=0.1)
    badge(cv, cx[0] + 0.07, p_y + 0.06, 1, CYAN_D)
    cv.text(cx[0] + 0.34, p_y + 0.05, cw - 0.4, 0.22, "Ask in Codex", size=7.6, bold=True, color=WHITE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(cx[0] + 0.12, p_y + 0.3, cw - 0.22, p_h - 0.32,
            [[("“What are the top 10 campaigns I can run for heart patients?”", {"italic": True})],
             [("or: “Run a campaign for heart patients”", {"color": "BFBFBF"})]], size=6.4,
            color=WHITE, font="Courier New", after=1)
    cv.rect(cx[1], p_y, cw, p_h, WHITE, GOLD, 1.5, R, 0.08)
    badge(cv, cx[1] + 0.07, p_y + 0.06, 4)
    cv.text(cx[1] + 0.34, p_y + 0.05, cw - 0.8, 0.22, "Ranked list · pick", size=7.6, bold=True,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(cx[1] + cw - 0.37, p_y + 0.07, 0.3, 0.17, YELLOW, BLACK, 0.5, R, 0.4)
    cv.text(cx[1] + cw - 0.37, p_y + 0.07, 0.3, 0.17, "G1", size=5.6, bold=True, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    ideas = ["1  CHF post-discharge SMS nudge", "2  Cardiac rehab referral", "3  Statin refill reminder",
             "…  size, channel, expected lift each"]
    cv.text(cx[1] + 0.12, p_y + 0.29, cw - 0.2, 0.36, [[(t, {"bold": i < 2})] for i, t in enumerate(ideas)],
            size=5.9, color=INK)
    cv.rect(cx[1] + cw - 0.82, p_y + p_h - 0.24, 0.75, 0.18, BLACK, None, shape=R, radius=0.4)
    cv.text(cx[1] + cw - 0.82, p_y + p_h - 0.24, 0.75, 0.18, "“run 1 and 2”", size=5.6, bold=True,
            color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    box(cv, cx[2], p_y, cw, p_h, "Approve the audience · Looker",
        "Size, segments, exclusions and the privacy evidence. A named approver signs off.", n=7, fill=YELLOW_T,
        line=GOLD, lw=1.5, gate="G2")
    box(cv, cx[3], p_y, cw, p_h, "Approve content, then launch",
        "Clinical and compliance approve the messages (G3); marketing ops activates (G4).", fill=YELLOW_T,
        line=GOLD, lw=1.5, gate="G3")

    # agents
    box(cv, cx[0], a_y, cw, a_h, "Campaign Strategist Agent",
        "Reads the graph, ranks campaigns by size, gap, consent and past lift.", n=2, fill=WHITE, line=CYAN_D,
        lw=1.25)
    box(cv, cx[1], a_y, cw, a_h, "Audience + Privacy Guard Agents",
        "Write SQL on governed views; check every column, consent, minimum fields.", n=5, fill=WHITE, line=CYAN_D,
        lw=1.25)
    box(cv, cx[2], a_y, cw, a_h, "Measurement Agent",
        "Lift against a holdout; writes what worked back to the graph.", n=10, fill=WHITE, line=CYAN_D, lw=1.25)
    box(cv, cx[3], a_y, cw, a_h, "Journey Agent",
        "Builds the data extension, the pull and the journey draft from approved templates.", n=8, fill=WHITE,
        line=CYAN_D, lw=1.25)

    # data
    box(cv, cx[0], d_y, cw, d_h, "Campaign knowledge graph",
        ["Cohorts, care gaps, consent coverage, past campaigns and their lift, policy-tagged data assets.",
         [("Aggregates and metadata only.", {"bold": True, "color": MAGENTA})]], n=3, fill=VIOLET_T, line=VIOLET,
        lw=1.25)
    box(cv, cx[1], d_y, cw, d_h, "Governed audience · BigQuery",
        ["Runs on policy-tagged, authorized views; dedupe, suppression, holdout split; staged per run ID.",
         [("Agents get counts back, not rows.", {"bold": True, "color": MAGENTA})]], n=6, fill=WHITE, line=NAVY)
    box(cv, cx[2], d_y, cw, d_h, "ROI engine",
        "Matching on EUID, attribution with lookback windows, lift vs holdout, Contribution Margin dashboard.",
        fill=MAG_T, line=MAGENTA)
    fx, fy, fw, fh = cv.frame(cx[3], d_y, cw, d_h, WHITE, 0.04)
    cv.text(fx + 0.08, fy + 0.04, fw - 0.16, 0.22, "Spanner audience store + API", size=7.6, bold=True,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.08, fy + 0.27, fw - 0.16, fh - 0.3,
            [[("Published only after G2: tokenized records per run ID, with a time limit.", {})],
             [("Read-only Audience API for Marketing Cloud.", {"bold": True})]], size=6.3, color=INK, after=1)

    # arrows: the main flow
    m = cw / 2
    cv.arrow(cx[0] + m, p_y + p_h, cx[0] + m, a_y, BLACK, 1.5)                       # 1 -> 2
    cv.arrow(cx[0] + m - 0.15, a_y + a_h, cx[0] + m - 0.15, d_y, VIOLET, 1.5)          # 2 -> 3
    cv.arrow(cx[0] + m + 0.15, d_y, cx[0] + m + 0.15, a_y + a_h, VIOLET, 1.5)          # 3 -> 2
    gab = cx[0] + cw + 0.075
    path(cv, [(cx[0] + cw, a_y + a_h / 2), (gab, a_y + a_h / 2), (gab, p_y + p_h / 2), (cx[1], p_y + p_h / 2)],
         CYAN_D, 1.5)                                                                     # 2 -> 4
    cv.arrow(cx[1] + m, p_y + p_h, cx[1] + m, a_y, GOLD, 1.5)                          # 4 -> 5
    cv.arrow(cx[1] + m, a_y + a_h, cx[1] + m, d_y, CYAN_D, 1.5)                        # 5 -> 6
    gbc = cx[1] + cw + 0.075
    path(cv, [(cx[1] + cw, d_y + 0.62), (gbc, d_y + 0.62), (gbc, p_y + p_h / 2), (cx[2], p_y + p_h / 2)],
         NAVY, 1.5)                                                                       # 6 -> 7
    gcd = cx[2] + cw + 0.075
    path(cv, [(cx[2] + cw, p_y + p_h / 2), (gcd, p_y + p_h / 2), (gcd, a_y + a_h / 2), (cx[3], a_y + a_h / 2)],
         GOLD, 1.5)                                                                       # 7 -> 8 journey
    path(cv, [(gcd, a_y + a_h / 2), (gcd, d_y + 0.4), (cx[3], d_y + 0.4)], GOLD, 1.5)   # 7 -> publish
    cv.arrow(cx[3] + m, a_y, cx[3] + m, p_y + p_h, CYAN_D, 1.25)                       # 8 -> G3
    cv.arrow(cx[2] + m, d_y, cx[2] + m, a_y + a_h, MAGENTA, 1.5)                       # roi -> measurement
    # learning loop back to the graph
    ly = 5.08
    path(cv, [(cx[2] + 0.5, d_y + d_h), (cx[2] + 0.5, ly), (cx[0] + m, ly), (cx[0] + m, d_y + d_h)], GREEN, 1.75)
    tag(cv, cx[0] + m + 0.15, ly - 0.085, 2.4, "← WHAT WORKED IMPROVES THE NEXT SUGGESTION", GREEN)

    # Marketing Cloud, bottom-up: pull -> data extension -> journey -> nudge
    mx, mw = 10.55, 2.33
    cv.rect(mx, 1.28, mw, 0.3, BLACK)
    cv.text(mx + 0.1, 1.28, mw - 0.2, 0.3, [[("MARKETING CLOUD", {"bold": True, "track": 150})]], size=7,
            color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(mx, 1.58, mw, 4.04, WHITE, MUTE, 0.75)
    nx, nw = mx + 0.1, mw - 0.2
    items = [(1.7, 0.62, "SMS or email nudge", "No clinical wording, no identifiers in links.", WHITE, NAVY, None),
             (2.56, 0.66, "Journey Builder", "Built by the Journey Agent; approved, then activated.", WHITE, NAVY,
              None),
             (3.46, 0.7, "Campaign data extension", "SubscriberKey (token) · channel · segment · RunID", None, None,
              None),
             (4.4, 0.8, "Pulls the approved records", "Automation Studio calls the read-only Audience API, scoped "
              "to the run ID.", CYAN_T, CYAN_D, 9)]
    for y, h, t, d, f, ln, n in items:
        if f is None:
            cv.frame(nx, y, nw, h, WHITE, 0.04)
        else:
            cv.rect(nx, y, nw, h, f, ln, 1.25, R, 0.1)
        tx = nx + (0.34 if n else 0.1)
        if n:
            badge(cv, nx + 0.07, y + 0.07, n)
        cv.text(tx, y + 0.05, nx + nw - tx - 0.06, 0.22, t, size=7.6, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(nx + 0.1, y + 0.3, nw - 0.18, h - 0.32, d, size=6.2, color=INK)
    for (y1, h1), (y2, _) in zip([(2.56, 0.66), (3.46, 0.7), (4.4, 0.8)], [(1.7, 0.62), (2.56, 0.66), (3.46, 0.7)]):
        cv.arrow(nx + nw / 2, y1, nx + nw / 2, y2 + (0.62 if y2 == 1.7 else (0.66 if y2 == 2.56 else 0.7)),
                 NAVY, 1.25)
    cv.arrow(cx[3] + cw, a_y + a_h / 2, nx, a_y + a_h / 2 + 0.17, CYAN_D, 1.5)          # journey agent -> journey
    cv.arrow(cx[3] + cw, d_y + 0.7, nx, d_y + 0.7, BLACK, 2.0)                         # API pull
    tag(cv, cx[3] + cw - 0.66, d_y + d_h + 0.05, 0.6, "PULL", BLACK)
    # outcomes back
    oy = 5.42
    path(cv, [(nx + nw / 2, 5.2), (nx + nw / 2, oy), (cx[2] + 1.6, oy), (cx[2] + 1.6, d_y + d_h)], MAGENTA, 1.5)
    tag(cv, 7.9, oy - 0.085, 2.35, "ENGAGEMENT + BOOKED VISITS ←", MAGENTA)
    principles(cv, 5.8, PRINCIPLES)
    set_notes(s, HL_NOTES)
    return s


# ================================================================== detailed design
DT_NOTES = """SLIDE: Agentic campaigns on governed data, the detailed design   (about 4 minutes)

CODEX (left): campaign skills in the Agentic Harness plugin. $campaign-suggest asks for ideas, $campaign-run starts the chosen campaigns, $campaign-status follows them. Every run goes through the harness: Orchestrator, evals on every step, the tool gateway with one identity per agent, the change passport.

CAMPAIGN AGENTS (top)
- Orchestrator: turns the request into a run, routes the agents, waits at the four gates.
- Campaign Strategist: queries the knowledge graph (cohorts, care gaps, consent coverage, past lift) and ranks campaigns. Output: a ranked list with size, channel and expected lift.
- Audience Agent: writes the audience SQL against authorized, policy-tagged views only, as a BigQuery job under its own service account. It receives counts and validation results, never rows.
- Privacy Guard: checks the classification and policy tag of every column used, the minimum-necessary field list, consent and suppression, frequency caps, and blocks small cells (fewer than 11). It writes the privacy evidence the Looker approver sees.
- Measurement Agent: reads outcomes from the ROI engine after the send, computes lift against the holdout, and writes the result to the knowledge graph.
- Journey Agent: in the Marketing Cloud development business unit, through the gateway: the data extension, the Automation Studio pull from the Audience API, and the journey draft from approved templates. Released through Package Manager after G3.

KNOWLEDGE GRAPH (middle): Spanner Graph with campaign entities: cohorts and condition groups, care gaps, campaigns and channels, outcomes and lift, data assets with their policy tags, consent rules, Marketing Cloud assets. Fed from governed BigQuery aggregates, ADDG classifications, the ROI engine and Marketing Cloud metadata. Aggregates and metadata only.

GOVERNED DATA PLANE (bottom): sources land in BigQuery; ADDG classifies, a steward approves and policies are applied; authorized views and the master table (one EUID); the audience is staged per run ID; a named approver signs off in Looker (G2); only then are tokenized records published to the Spanner audience store, with a time limit, behind a read-only Audience API (Cloud Run, OAuth client credentials, IP allowlist, scoped to the run ID).

MARKETING CLOUD (right): Automation Studio pulls the approved records into the data extension; the journey runs after G3 content approval and G4 activation by marketing ops; engagement flows back to the ROI engine.

OPEN DECISIONS
- Pull by API (this design) or a file import from a governed bucket.
- Spanner as the audience store, or BigQuery with Data Cloud zero-copy.
- Which agent-built journeys may go live without a developer review."""

AGENTS = [
    ("Orchestrator", "Turns the request into a run; routes agents; waits at G1-G4.", "harness run loop"),
    ("Campaign Strategist", "Reads the graph; ranks campaigns by size, care gap, consent and past lift.",
     "reads graph only"),
    ("Audience Agent", "Writes SQL on authorized views; runs it as a BigQuery job; gets counts, not rows.",
     "sa-audience"),
    ("Privacy Guard", "Checks tags, minimum fields, consent, suppression; blocks cells under 11.",
     "blocks or passes"),
    ("Measurement Agent", "Lift vs holdout from the ROI engine; writes what worked to the graph.", "sa-measure"),
    ("Journey Agent", "Builds the data extension, the API pull and the journey draft in the dev BU.",
     "sa-sfmc-dev"),
]


def detailed(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION · AGENTIC CAMPAIGNS ON GOVERNED DATA",
              "Detailed design: campaign agents, the knowledge graph and the governed data plane",
              "Agents reason on metadata and counts; every patient record stays in Google Cloud until it is "
              "approved, tokenized and pulled.")
    top = 1.27
    # ---- Codex column
    lx, lw = 0.45, 2.02
    cv.rect(lx, top, lw, 0.3, BLACK)
    cv.text(lx + 0.1, top, lw - 0.2, 0.3, [[("CODEX", {"bold": True, "track": 150}), ("   campaign skills",
                                                                                     {"color": "BFBFBF"})]],
            size=7, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(lx, top + 0.3, lw, 4.32, WHITE, MUTE, 0.75)
    cv.rect(lx + 0.1, 1.7, lw - 0.2, 0.86, BLACK, None, shape=R, radius=0.1)
    badge(cv, lx + 0.16, 1.76, 1, CYAN_D)
    cv.text(lx + 0.43, 1.76, lw - 0.6, 0.22, "Marketer asks", size=7.4, bold=True, color=WHITE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(lx + 0.18, 2.0, lw - 0.34, 0.54, "“Top 10 campaigns for heart patients” → "
            "“run 1 and 2”", size=6.3, color=WHITE, font="Courier New")
    cv.text(lx + 0.12, 2.66, lw - 0.24, 0.18, "SKILLS", size=6.2, bold=True, color=CYAN_D, track=150)
    for i, (sk, d) in enumerate([("$campaign-suggest", "ideas from the graph"), ("$campaign-run", "start the "
                                 "chosen ones"), ("$campaign-status", "follow every gate")]):
        y = 2.86 + i * 0.36
        cv.rect(lx + 0.1, y, lw - 0.2, 0.3, GREY, None, shape=R, radius=0.2)
        cv.text(lx + 0.17, y, lw - 0.3, 0.3, [[(sk, {"bold": True, "font": "Courier New"})],
                                              [(d, {"color": MUTE, "size": 5.6})]], size=6.2,
                anchor=MSO_ANCHOR.MIDDLE)
    cv.text(lx + 0.12, 3.98, lw - 0.24, 0.18, "HUMAN GATES", size=6.2, bold=True, color=GOLD, track=150)
    gates = [("G1", "marketer picks the campaigns"), ("G2", "named approver, audience (Looker)"),
             ("G3", "clinical + compliance, content"), ("G4", "marketing ops activates")]
    for i, (g, d) in enumerate(gates):
        y = 4.18 + i * 0.34
        cv.rect(lx + 0.1, y + 0.04, 0.3, 0.2, YELLOW, BLACK, 0.5, R, 0.4)
        cv.text(lx + 0.1, y + 0.04, 0.3, 0.2, g, size=5.8, bold=True, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(lx + 0.46, y, lw - 0.54, 0.28, d, size=6.1, anchor=MSO_ANCHOR.MIDDLE)

    # ---- middle
    MX0, MX1 = 2.6, 10.35
    MW = MX1 - MX0
    # agents band
    lane_band(cv, MX0, top, MW, 1.62, CYAN_T, CYAN_D, "AGENTIC HARNESS · CAMPAIGN AGENTS",
              "evals on every step · tool gateway · one identity each · change passport", color=CYAN_D)
    aw, ag = (MW - 0.2 - 5 * 0.08) / 6, 0.08
    ax = [MX0 + 0.1 + i * (aw + ag) for i in range(6)]
    ay, ah = top + 0.3, 1.22
    nums = [None, 2, 5, 5, 10, 8]
    for i, (t, d, ident) in enumerate(AGENTS):
        cv.rect(ax[i], ay, aw, ah, WHITE, CYAN_D, 1.25 if i else 0.9, R, 0.08)
        tx = ax[i] + 0.08
        if nums[i]:
            badge(cv, ax[i] + 0.05, ay + 0.06, nums[i])
            tx = ax[i] + 0.3
        cv.text(tx, ay + 0.04, ax[i] + aw - tx - 0.04, 0.32, t, size=7, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(ax[i] + 0.08, ay + 0.4, aw - 0.14, 0.58, d, size=5.9, color=INK)
        cv.rect(ax[i] + 0.08, ay + ah - 0.24, aw - 0.16, 0.17, GREY, None, shape=R, radius=0.4)
        cv.text(ax[i] + 0.08, ay + ah - 0.24, aw - 0.16, 0.17, ident, size=5.4, bold=True, color=MUTE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font="Courier New")

    # knowledge graph band
    ky, kh = 2.98, 0.96
    lane_band(cv, MX0, ky, MW, kh, VIOLET_T, VIOLET, "CAMPAIGN KNOWLEDGE GRAPH · SPANNER GRAPH",
              "aggregates and metadata only, never patient rows", color=VIOLET)
    badge(cv, MX1 - 0.32, ky + 0.04, 3, VIOLET)
    ents = ["Cohort", "Condition group", "Care gap", "Campaign", "Channel", "Outcome + lift", "Data asset + tag",
            "Consent rule", "SFMC asset"]
    ex = MX0 + 0.12
    for e in ents:
        w = 0.14 + 0.058 * len(e)
        cv.rect(ex, ky + 0.32, w, 0.22, WHITE, VIOLET, 0.75, R, 0.4)
        cv.text(ex, ky + 0.32, w, 0.22, e, size=6, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        ex += w + 0.06
    cv.text(MX0 + 0.12, ky + 0.6, MW - 0.24, 0.3,
            [[("Fed by: ", {"bold": True}), ("governed BigQuery aggregates · ADDG classifications · ROI engine "
                                             "outcomes · Marketing Cloud metadata · Confluence campaign briefs",
                                             {"color": INK})]], size=6.2, anchor=MSO_ANCHOR.MIDDLE)

    # governed data plane
    gy, gh = 4.04, 1.92
    lane_band(cv, MX0, gy, MW, gh, WHITE, NAVY, "GOVERNED DATA PLANE · GOOGLE CLOUD PHI BOUNDARY",
              "VPC Service Controls · CMEK · audit logs", dash="dash")
    bw_, bg = (MW - 0.2 - 4 * 0.12) / 5, 0.12
    bx = [MX0 + 0.1 + i * (bw_ + bg) for i in range(5)]
    by, bh = gy + 0.3, 0.98
    steps = [("Sources → BigQuery", "Marketing leads + clinical (Epic, Strata, athena) land per source.", None,
              WHITE, NAVY, None),
             ("ADDG governance", "DLP classifies, steward approves in Collibra, policy tags mask.", None, VIOLET_T,
              VIOLET, None),
             ("Authorized views + master", "Policy-tagged views; one EUID per patient; ROI engine reads here.",
              None, WHITE, NAVY, None),
             ("Audience staging", "Agent SQL runs here per run ID: dedupe, suppression, holdout split.", 6,
              WHITE, NAVY, None),
             ("Looker approval", "Size, segments, exclusions + privacy evidence; named approver.", 7, YELLOW_T,
              GOLD, "G2")]
    for i, (t, d, n, f, ln, gate) in enumerate(steps):
        box(cv, bx[i], by, bw_, bh, t, d, n=n, fill=f, line=ln, lw=1.25 if gate else 0.9, gate=gate, tsize=7,
            bsize=6)
        if i < 4:
            cv.arrow(bx[i] + bw_, by + bh / 2, bx[i + 1], by + bh / 2, NAVY, 1.25)
    # publish row
    py = by + bh + 0.13
    fx, fy, fw, fh = cv.frame(bx[3], py, 2 * bw_ + bg, 0.42, WHITE, 0.035)
    cv.text(fx + 0.08, fy, fw - 0.16, fh, [[("Spanner audience store + Audience API  ", {"bold": True}),
                                           ("tokenized records per run ID, time-limited; read-only API", {})]],
            size=6.2, anchor=MSO_ANCHOR.MIDDLE)
    path(cv, [(bx[4] + bw_ / 2, by + bh), (bx[4] + bw_ / 2, py)], GOLD, 1.25)
    cv.rect(bx[0], py, bx[2] + bw_ - bx[0], 0.42, MAG_T, MAGENTA, 0.9, R, 0.15)
    cv.text(bx[0] + 0.08, py, bx[2] + bw_ - bx[0] - 0.16, 0.42,
            [[("ROI engine  ", {"bold": True}), ("matching on EUID · attribution, lookback windows · lift vs "
                                                 "holdout · Contribution Margin dashboard", {})]], size=6.2,
            anchor=MSO_ANCHOR.MIDDLE)

    # agent <-> graph / data arrows
    def ac(i):
        return ax[i] + aw / 2
    cv.arrow(ac(1), ay + ah, ac(1), ky, VIOLET, 1.5)                       # strategist reads graph
    cv.arrow(ac(4), ky, ac(4), ay + ah, VIOLET, 1.5)                       # measurement writes graph

    # ---- Marketing Cloud
    sx, sw = 10.5, 2.38
    cv.rect(sx, top, sw, 0.3, BLACK)
    cv.text(sx + 0.1, top, sw - 0.2, 0.3, [[("MARKETING CLOUD", {"bold": True, "track": 150}),
                                           ("   dev BU → prod", {"color": "BFBFBF"})]], size=7, color=WHITE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(sx, top + 0.3, sw, 4.39, WHITE, MUTE, 0.75)
    nx, nw = sx + 0.1, sw - 0.2
    box(cv, nx, 1.7, nw, 0.86, "Journey built by the agent",
        "Data extension, Automation Studio pull and journey draft from approved templates; released after G3.",
        n=8, fill=CYAN_T, line=CYAN_D, lw=1.25, bsize=6)
    box(cv, nx, 2.7, nw, 0.78, "Pull from the Audience API",
        "OAuth client credentials, IP allowlist, read-only, scoped to the approved run ID.", n=9, fill=WHITE,
        line=BLACK, lw=1.5, bsize=6)
    fx, fy, fw, fh = cv.frame(nx, 3.62, nw, 0.78, WHITE, 0.04)
    cv.text(fx + 0.08, fy + 0.03, fw - 0.16, 0.2, "Campaign data extension", size=7.4, bold=True,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.08, fy + 0.25, fw - 0.16, fh - 0.28, "SubscriberKey (token) · channel · segment · send "
            "window · holdout flag · RunID", size=6, color=INK)
    box(cv, nx, 4.54, nw, 0.66, "Journey runs · G4",
        "Marketing ops activates; consent and STOP re-checked at send.", fill=YELLOW_T, line=GOLD, lw=1.25,
        bsize=6)
    box(cv, nx, 5.32, nw, 0.56, "Engagement back",
        "Sends, clicks, replies, opt-outs to the ROI engine.", fill=MAG_T, line=MAGENTA, bsize=6)
    for y1, y2 in ((2.56, 2.7), (3.48, 3.62), (4.4, 4.54), (5.2, 5.32)):
        cv.arrow(nx + nw / 2, y1, nx + nw / 2, y2, NAVY, 1.25)
    # journey agent -> Marketing Cloud dev BU
    cv.arrow(ax[5] + aw, ay + 0.55, nx, ay + 0.55, CYAN_D, 1.5)
    # API pull: from the Spanner store to the pull box
    path(cv, [(bx[4] + bw_, py + 0.21), (10.43, py + 0.21), (10.43, 3.09), (nx, 3.09)], BLACK, 2.0)
    # engagement back to the ROI engine
    ry = 6.06
    path(cv, [(nx, 5.6), (10.45, 5.6), (10.45, ry), (bx[1] + 0.6, ry), (bx[1] + 0.6, py + 0.42)], MAGENTA, 1.5)

    principles(cv, 6.2, PRINCIPLES)
    set_notes(s, DT_NOTES)
    return s


def main(out=OUT):
    prs = Presentation(TEMPLATE)
    lst = prs.slides._sldIdLst
    for el in list(lst):
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    high_level(prs, layout)
    detailed(prs, layout)
    prs.save(out)
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
