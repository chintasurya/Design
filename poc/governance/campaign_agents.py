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


PRINCIPLES = [("Masked for agents and reviewers", "Collibra policy masks PHI; agents see counts and tokens only.",
               MAGENTA),
              ("Consent decides, people confirm", "No consent for the channel, no message. Checked at every step.",
               VIOLET),
              ("Minimum necessary leaves", "Token, name, email, phone, condition group, discharge date. Nothing "
               "else.", GOLD),
              ("Released only after review", "The data extension starts the journey, so review comes before "
               "release.", GREEN)]


# ================================================================== high-level execution flow
HL_NOTES = """SLIDE: Agentic campaigns on governed data, the execution flow   (about 3 minutes)

KEY MESSAGE
A marketer asks in Codex. Agents work only on masked data; people review a masked pre-send report; only then do the minimum fields needed to send reach Marketing Cloud, which pulls them. Consent decides who can be messaged, at every step.

WALK IT (follow the numbers)
- Sources: Epic, athenahealth, Strata, SFDC leads, SFMC engagement, CallRail, forms and direct mail land in BigQuery. DLP classifies every column, the Collibra steward approves, and policy tags mask PHI for every agent and every reviewer.
1 The marketer asks: "What are the top 10 campaigns I can run for heart patients?" or "Run a campaign for heart patients".
2-3 The Campaign Strategist reads the knowledge graph, built on masked data: segments, counts, care gaps, consent coverage, past lift. No patient is ever visible.
4 Codex shows a ranked list; the marketer picks, for example "run 1 and 2" (G1).
5-6 The Audience and Privacy Guard Agents build the audience on masked views, consent first (channel opt-in, STOP, deceased, readmitted, duplicates). The result is tokens and counts per run ID; agents never unmask.
7 The SME and tech lead review a masked pre-send report (G2): counts, consent by channel, exclusions, right-patient checks. No PHI is on screen.
8 In parallel, the Journey Agent builds the data extension, the pull and the journey from approved templates; clinical and compliance approve the journey and the messages (G3). The journey waits, active, for entries.
9 Only when G2 and G3 are both signed are the minimum fields released to the Spanner release store: token, name, email, phone, condition group, discharge date. Time-limited, behind a read-only API.
10 Marketing Cloud pulls the released records into the data extension; new records trigger the journey automatically; consent, STOP and frequency caps are re-checked at send.
11 Engagement comes back as a source; the Measurement Agent measures lift against the holdout and the graph learns what worked."""


def high_level(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION · AGENTIC CAMPAIGNS ON GOVERNED DATA",
              "Ask in Codex; agents work on masked data; people release only the right patients",
              "Every source is masked by Collibra policy. Agents see counts and tokens; a masked pre-send report is "
              "reviewed; only then do the minimum fields reach Marketing Cloud.")
    X0, X1 = 0.45, 10.38
    W = X1 - X0
    cx = [0.88 + i * 2.38 for i in range(4)]
    cw = 2.25
    cv.rect(X0, 1.28, W, 1.1, GREY, MUTE, 0.75, R, 0.03)
    cv.rect(X0, 2.46, W, 1.04, CYAN_T, CYAN_D, 0.75, R, 0.03)
    cv.rect(X0, 3.58, W, 2.04, WHITE, NAVY, 1.0, R, 0.02, dash="dash")
    side_label(cv, 1.28, 1.1, "PEOPLE", "D9D9D9", BLACK)
    side_label(cv, 2.46, 1.04, "HARNESS", CYAN_D, WHITE)
    side_label(cv, 3.58, 2.04, "GOOGLE CLOUD", NAVY, WHITE)
    p_y, p_h = 1.43, 0.82
    a_y, a_h = 2.62, 0.74
    d_y, d_h = 3.7, 0.95

    # people
    cv.rect(cx[0], p_y, cw, p_h, BLACK, None, shape=R, radius=0.1)
    badge(cv, cx[0] + 0.07, p_y + 0.06, 1, CYAN_D)
    cv.text(cx[0] + 0.34, p_y + 0.05, cw - 0.4, 0.22, "Ask in Codex", size=7.6, bold=True, color=WHITE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(cx[0] + 0.12, p_y + 0.3, cw - 0.22, p_h - 0.32,
            [[("“What are the top 10 campaigns I can run for heart patients?”", {})],
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
             "…  counts, channel, expected lift"]
    cv.text(cx[1] + 0.12, p_y + 0.29, cw - 0.2, 0.36, [[(t, {"bold": i < 2})] for i, t in enumerate(ideas)],
            size=5.9, color=INK)
    cv.rect(cx[1] + cw - 0.82, p_y + p_h - 0.24, 0.75, 0.18, BLACK, None, shape=R, radius=0.4)
    cv.text(cx[1] + cw - 0.82, p_y + p_h - 0.24, 0.75, 0.18, "“run 1 and 2”", size=5.6, bold=True,
            color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    box(cv, cx[2], p_y, cw, p_h, "Pre-send review",
        ["SME + tech lead review a masked report: counts, consent by channel, exclusions, checks.",
         [("No PHI on screen.", {"bold": True, "color": MAGENTA})]], n=7, fill=YELLOW_T, line=GOLD, lw=1.5,
        gate="G2")
    box(cv, cx[3], p_y, cw, p_h, "Approve journey + content",
        "Clinical and compliance approve messages and journey; it waits, active, for entries.", fill=YELLOW_T,
        line=GOLD, lw=1.5, gate="G3")

    # agents
    box(cv, cx[0], a_y, cw, a_h, "Campaign Strategist Agent",
        "Reads the masked graph; ranks by size, care gap, consent coverage, past lift.", n=2, line=CYAN_D, lw=1.25)
    box(cv, cx[1], a_y, cw, a_h, "Audience + Privacy Guard Agents",
        "Consent first: channel opt-in, STOP, deceased, readmitted, duplicates out.", n=5, line=CYAN_D, lw=1.25)
    box(cv, cx[2], a_y, cw, a_h, "Measurement Agent",
        "Lift against a holdout; writes what worked back to the graph.", n=11, line=CYAN_D, lw=1.25)
    box(cv, cx[3], a_y, cw, a_h, "Journey Agent",
        "Builds the data extension, the pull and the journey from approved templates.", n=8, line=CYAN_D, lw=1.25)

    # data
    box(cv, cx[0], d_y, cw, d_h, "Campaign knowledge graph",
        ["Segments, counts, care gaps, consent coverage, past lift.",
         [("Built on masked data: no patient visible.", {"bold": True, "color": MAGENTA})]], n=3, fill=VIOLET_T,
        line=VIOLET, lw=1.25)
    box(cv, cx[1], d_y, cw, d_h, "Masked audience · BigQuery",
        ["Tokens and counts per run ID; holdout set aside.",
         [("Agents never unmask.", {"bold": True, "color": MAGENTA})]], n=6)
    box(cv, cx[2], d_y, cw, d_h, "ROI engine",
        "EUID matching, attribution and lookback windows, lift vs holdout, Contribution Margin.", fill=MAG_T,
        line=MAGENTA)
    fx, fy, fw, fh = cv.frame(cx[3], d_y, cw, d_h, WHITE, 0.04)
    badge(cv, fx + 0.04, fy + 0.04, 9)
    cv.text(fx + 0.3, fy + 0.03, fw - 0.36, 0.22, "Release store · Spanner", size=7.6, bold=True,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.08, fy + 0.26, fw - 0.16, fh - 0.28,
            [[("Only after G2 + G3: ", {"bold": True}), ("token, name, email, phone, condition group, discharge "
                                                          "date. Time-limited; read-only API.", {})]],
            size=6.1, color=INK)

    # sources strip: everything lands masked
    sy = 5.02
    cv.rect(cx[0], sy, cx[3] + cw - cx[0], 0.48, VIOLET_T, VIOLET, 0.75, R, 0.2)
    cv.text(cx[0] + 0.12, sy, cx[3] + cw - cx[0] - 0.24, 0.48,
            [[("SOURCES  ", {"bold": True, "track": 120, "color": VIOLET}),
              ("Epic · athenahealth · Strata · SFDC leads · SFMC engagement · CallRail · forms · direct mail", {}),
              ("   → BigQuery → ", {"bold": True}),
              ("DLP classifies, the Collibra steward approves, policy tags mask PHI for every agent and reviewer",
               {"color": INK})]], size=6.4, anchor=MSO_ANCHOR.MIDDLE)

    # arrows
    m = cw / 2
    cv.arrow(cx[0] + m, p_y + p_h, cx[0] + m, a_y, BLACK, 1.5)
    cv.arrow(cx[0] + m - 0.15, a_y + a_h, cx[0] + m - 0.15, d_y, VIOLET, 1.5)
    cv.arrow(cx[0] + m + 0.15, d_y, cx[0] + m + 0.15, a_y + a_h, VIOLET, 1.5)
    gab = cx[0] + cw + 0.065
    path(cv, [(cx[0] + cw, a_y + a_h / 2), (gab, a_y + a_h / 2), (gab, p_y + p_h / 2), (cx[1], p_y + p_h / 2)],
         CYAN_D, 1.5)
    cv.arrow(cx[1] + m, p_y + p_h, cx[1] + m, a_y, GOLD, 1.5)
    cv.arrow(cx[1] + m, a_y + a_h, cx[1] + m, d_y, CYAN_D, 1.5)
    gbc = cx[1] + cw + 0.065
    path(cv, [(cx[1] + cw, d_y + 0.6), (gbc, d_y + 0.6), (gbc, p_y + p_h / 2), (cx[2], p_y + p_h / 2)], NAVY, 1.5)
    gcd = cx[2] + cw + 0.065
    path(cv, [(cx[2] + cw, p_y + p_h / 2), (gcd, p_y + p_h / 2), (gcd, d_y + 0.35), (cx[3], d_y + 0.35)], GOLD,
         1.75)                                                                     # G2 -> release
    cv.arrow(cx[3], p_y + p_h - 0.14, gcd, p_y + p_h - 0.14, GOLD, 1.75)          # G3 joins
    cv.arrow(cx[3] + m, a_y, cx[3] + m, p_y + p_h, CYAN_D, 1.25)                 # journey agent -> G3
    cv.arrow(cx[2] + m, d_y, cx[2] + m, a_y + a_h, MAGENTA, 1.5)
    ly = 4.83
    path(cv, [(cx[2] + 0.5, d_y + d_h), (cx[2] + 0.5, ly), (cx[0] + m, ly), (cx[0] + m, d_y + d_h)], GREEN, 1.5)
    tag(cv, cx[0] + m + 0.15, ly - 0.085, 2.4, "← WHAT WORKED IMPROVES THE NEXT SUGGESTION", GREEN)

    # Marketing Cloud, bottom-up
    mx, mw = 10.55, 2.33
    cv.rect(mx, 1.28, mw, 0.3, BLACK)
    cv.text(mx + 0.1, 1.28, mw - 0.2, 0.3, [[("MARKETING CLOUD", {"bold": True, "track": 150})]], size=7,
            color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(mx, 1.58, mw, 4.04, WHITE, MUTE, 0.75)
    nx, nw = mx + 0.1, mw - 0.2
    items = [(1.7, 0.62, "SMS or email nudge", "Consent, STOP and frequency caps re-checked at send.", WHITE, NAVY,
              None, False),
             (2.48, 0.76, "Journey triggers itself", "New records in the data extension enter the approved "
              "journey: no manual step.", WHITE, NAVY, None, False),
             (3.4, 0.74, "Campaign data extension", "Minimum fields only, for this run.", None, None, None, False),
             (4.3, 0.82, "Pulls the released records", "Automation Studio calls the read-only API, scoped to the "
              "run ID.", CYAN_T, CYAN_D, 10, False)]
    for y, h, t, d, f, ln, n, _ in items:
        if f is None:
            cv.frame(nx, y, nw, h, WHITE, 0.04)
        else:
            cv.rect(nx, y, nw, h, f, ln, 1.25, R, 0.1)
        tx = nx + (0.34 if n else 0.1)
        if n:
            badge(cv, nx + 0.07, y + 0.07, n)
        cv.text(tx, y + 0.05, nx + nw - tx - 0.06, 0.22, t, size=7.6, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(nx + 0.1, y + 0.3, nw - 0.18, h - 0.32, d, size=6.1, color=INK)
    for lo, hi in ((2.48, 2.32), (3.4, 3.24), (4.3, 4.14)):
        cv.arrow(nx + nw / 2, lo, nx + nw / 2, hi, NAVY, 1.25)
    cv.arrow(cx[3] + cw, a_y + a_h / 2, nx, 2.86, CYAN_D, 1.5)
    cv.arrow(cx[3] + cw, d_y + 0.62, nx, 4.62, BLACK, 2.0)
    oy = 5.56
    path(cv, [(nx + nw / 2, 5.12), (nx + nw / 2, oy), (cx[2] + 1.6, oy), (cx[2] + 1.6, sy + 0.48)], MAGENTA, 1.25)
    principles(cv, 5.8, PRINCIPLES)
    set_notes(s, HL_NOTES)
    return s



# ================================================================== detailed design
DT_NOTES = """SLIDE: Agentic campaigns on governed data, the detailed design   (about 4 minutes)

CODEX (left): campaign skills in the Agentic Harness plugin. $campaign-suggest, $campaign-run, $campaign-status. Three human gates: G1 the marketer picks, G2 the SME and tech lead approve a masked pre-send report, G3 clinical and compliance approve the journey and content. Release happens only when G2 and G3 are both signed.

CAMPAIGN AGENTS (top): Orchestrator; Campaign Strategist (reads the masked graph); Audience Agent (builds the audience on masked views as a BigQuery job, sees tokens and counts); Privacy Guard (consent per channel first, STOP, deceased, readmitted, duplicates; writes the pre-send report); Measurement Agent (lift vs holdout, writes back to the graph); Journey Agent (data extension, API pull and journey with entry on new records, in the development business unit). Each has its own identity and runs through the harness: evals, tool gateway, change passport.

KNOWLEDGE GRAPH (middle): Spanner Graph built on Collibra-masked data: counts and segments, never a patient.

GOVERNED DATA PLANE (bottom): sources land in BigQuery; Collibra masking (DLP classifies, the steward approves, policy tags mask PHI for everyone); authorized views and the master table (one EUID); the masked audience per run ID; the masked pre-send review (G2). After G2 and G3, the release store in Spanner holds only token, name, email, phone, condition group and discharge date, time-limited, behind a read-only API.

MARKETING CLOUD (right): the agent-built journey is approved and active; Automation Studio pulls the released records; the data extension starts the journey automatically; consent and STOP are re-checked at send; engagement flows back.

OPEN DECISIONS
- Pull by API (this design) or a file import from a governed bucket.
- Spanner as the release store, or BigQuery with Data Cloud zero-copy.
- Whether a developer reviews agent-built journeys for the first campaigns."""

AGENTS = [
    ("Orchestrator", "Turns the request into a run; routes agents; waits at G1, G2 and G3.", "harness run loop"),
    ("Campaign Strategist", "Reads the masked graph; ranks by size, care gap, consent coverage, past lift.",
     "reads graph only"),
    ("Audience Agent", "Builds the audience on masked views as a BigQuery job; sees tokens and counts.",
     "sa-audience"),
    ("Privacy Guard", "Consent per channel first; STOP, deceased, readmitted, duplicates out; writes the report.",
     "blocks or passes"),
    ("Measurement Agent", "Lift vs holdout from the ROI engine; writes what worked to the graph.", "sa-measure"),
    ("Journey Agent", "Builds the data extension, the API pull and the journey (entry: new records).",
     "sa-sfmc-dev"),
]


def detailed(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION · AGENTIC CAMPAIGNS ON GOVERNED DATA",
              "Detailed design: campaign agents, the knowledge graph and the governed data plane",
              "Agents reason on masked data. The minimum fields leave Google Cloud only after a masked pre-send "
              "review, and Marketing Cloud pulls them.")
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
    gates = [("G1", "marketer picks the campaigns"), ("G2", "SME + tech lead: masked pre-send report"),
             ("G3", "clinical + compliance: journey + content"), ("\u2192", "release only when G2 + G3 signed")]
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
    nums = [None, 2, 5, 5, 11, 8]
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
              "built on Collibra-masked data: counts and segments, never a patient", color=VIOLET)
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
            [[("Fed by: ", {"bold": True}), ("masked BigQuery aggregates · Collibra classifications · ROI engine "
                                             "outcomes · Marketing Cloud metadata · Confluence campaign briefs",
                                             {"color": INK})]], size=6.2, anchor=MSO_ANCHOR.MIDDLE)

    # governed data plane
    gy, gh = 4.04, 1.92
    lane_band(cv, MX0, gy, MW, gh, WHITE, NAVY, "GOVERNED DATA PLANE · GOOGLE CLOUD PHI BOUNDARY",
              "VPC Service Controls · CMEK · audit logs", dash="dash")
    bw_, bg = (MW - 0.2 - 4 * 0.12) / 5, 0.12
    bx = [MX0 + 0.1 + i * (bw_ + bg) for i in range(5)]
    by, bh = gy + 0.3, 0.98
    steps = [("Sources → BigQuery", "Epic, athena, Strata, SFDC, SFMC, CallRail, forms, direct mail.", None,
              WHITE, NAVY, None),
             ("Collibra masking", "DLP classifies; the steward approves; policy tags mask PHI for all.", None,
              VIOLET_T, VIOLET, None),
             ("Authorized views + master", "Policy-tagged views; one EUID per patient; ROI engine reads here.",
              None, WHITE, NAVY, None),
             ("Masked audience", "Tokens + counts per run ID; consent first; holdout set aside.", 6,
              WHITE, NAVY, None),
             ("Pre-send review", "Masked report to SME + tech lead (Looker): counts, consent, checks.", 7,
              YELLOW_T, GOLD, "G2")]
    for i, (t, d, n, f, ln, gate) in enumerate(steps):
        box(cv, bx[i], by, bw_, bh, t, d, n=n, fill=f, line=ln, lw=1.25 if gate else 0.9, gate=gate, tsize=7,
            bsize=6)
        if i < 4:
            cv.arrow(bx[i] + bw_, by + bh / 2, bx[i + 1], by + bh / 2, NAVY, 1.25)
    # publish row
    py = by + bh + 0.13
    fx, fy, fw, fh = cv.frame(bx[3], py, 2 * bw_ + bg, 0.42, WHITE, 0.035)
    cv.text(fx + 0.08, fy, fw - 0.16, fh, [[("Release store · Spanner  ", {"bold": True}),
                                           ("after G2 + G3 only: token, name, email, phone, condition group, "
                                            "discharge date; time-limited; read-only API", {})]],
            size=6, anchor=MSO_ANCHOR.MIDDLE)
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
        "Data extension, pull and journey from approved templates; approved at G3, then active, waiting.",
        n=8, fill=CYAN_T, line=CYAN_D, lw=1.25, bsize=6)
    box(cv, nx, 2.7, nw, 0.78, "Pull from the Audience API",
        "Only after release. OAuth, IP allowlist, read-only, scoped to the run ID.", n=10, fill=WHITE,
        line=BLACK, lw=1.5, bsize=6)
    fx, fy, fw, fh = cv.frame(nx, 3.62, nw, 0.78, WHITE, 0.04)
    cv.text(fx + 0.08, fy + 0.03, fw - 0.16, 0.2, "Campaign data extension", size=7.4, bold=True,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.08, fy + 0.25, fw - 0.16, fh - 0.28, "token · name · email · phone · condition group · "
            "discharge date · RunID", size=6, color=INK)
    box(cv, nx, 4.54, nw, 0.66, "Journey triggers itself",
        "New records enter the approved journey; consent and STOP re-checked at send.", fill=WHITE, line=NAVY,
        lw=1.25, bsize=6)
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


# ================================================================== the human angle
HU_NOTES = """SLIDE: The human angle: who decides, what they see, and how we never message the wrong patient   (about 3 minutes)

KEY MESSAGE
Agents do the work, people make the decisions, and nobody looks at a patient's personal data to do either. Consent decides who can be messaged; people confirm it on a masked report before anything is released, because once records land in the data extension the journey starts by itself.

THE PEOPLE (top row)
- Marketer: picks the campaign (G1). Sees ideas and counts.
- Data steward: approves classifications and masking in Collibra. Sees column metadata, never values.
- SME and tech lead: the pre-send review (G2). See the masked report: counts, consent by channel, exclusions, right-patient checks, a masked sample.
- Clinical and compliance: approve the journey and every message (G3). See templates with placeholders.
- Marketing ops: watch the sends; can pause the journey at any time. See send metrics.
- The patient: can reply STOP or DONE at any time; it is honoured immediately and synced back.

THE PRE-SEND REPORT (middle; numbers are illustrative)
The funnel shows why each patient was excluded; every check must be green; the sample is masked. Approve releases the minimum fields to the release store; Send back returns it to the agents with a reason; Stop ends the campaign.

FIVE CHECKS BEFORE ANY MESSAGE (right)
Consent and right-patient checks run at build, at review, at release, at send and on reply. If any check fails, nothing is sent and a named owner is told.

BE READY FOR
- "Can the reviewer see who is in the audience?" No. They see counts, reasons and masked tokens. The fields needed to send move system to system without a person seeing them.
- "What if consent changes after approval?" Consent is re-checked at release and again by Marketing Cloud at send."""

ROLES_H = [
    ("Marketer", "G1", "Which campaign to run", "Ideas, audience counts, expected lift", "Any patient"),
    ("Data steward", None, "What is PHI and how it is masked", "Column names, classifications", "Values"),
    ("SME + tech lead", "G2", "Release the audience, or send it back", "Masked pre-send report", "Names, phones, "
     "emails, diagnoses"),
    ("Clinical + compliance", "G3", "Messages and journey logic", "Templates with placeholders", "Recipients"),
    ("Marketing ops", None, "Pause or stop a live journey", "Send and opt-out metrics", "Individual records"),
    ("The patient", None, "Reply STOP or DONE at any time", "Only their own message", "Anything about others"),
]


def human_angle(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION · AGENTIC CAMPAIGNS ON GOVERNED DATA · THE HUMAN ANGLE",
              "People decide, consent rules, and nobody needs to see a patient to do it",
              "Agents prepare everything on masked data. People confirm on a masked report before release, because "
              "once records land in the data extension the journey starts by itself.")
    # ---- the people
    n = len(ROLES_H)
    cw = (12.43 - (n - 1) * 0.12) / n
    y0, ch = 1.28, 1.62
    for i, (role, gate, decides, sees, never) in enumerate(ROLES_H):
        x = 0.45 + i * (cw + 0.12)
        patient = role == "The patient"
        cv.rect(x, y0, cw, ch, GREEN_T if patient else (YELLOW_T if gate else WHITE),
                GREEN if patient else (GOLD if gate else MUTE), 1.5 if gate or patient else 0.9, R, 0.06)
        cv.text(x + 0.1, y0 + 0.06, cw - 0.55, 0.24, role, size=8.5, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        if gate:
            cv.rect(x + cw - 0.4, y0 + 0.09, 0.3, 0.18, YELLOW, BLACK, 0.5, R, 0.4)
            cv.text(x + cw - 0.4, y0 + 0.09, 0.3, 0.18, gate, size=5.8, bold=True, align=PP_ALIGN.CENTER,
                    anchor=MSO_ANCHOR.MIDDLE)
        rows = [("DECIDES", decides, BLACK), ("SEES", sees, CYAN_D), ("NEVER SEES", never, MAGENTA)]
        yy = y0 + 0.36
        for lab, txt, col in rows:
            cv.text(x + 0.1, yy, cw - 0.2, 0.14, lab, size=5.4, bold=True, color=col, track=120,
                    anchor=MSO_ANCHOR.MIDDLE)
            cv.text(x + 0.1, yy + 0.14, cw - 0.2, 0.26, txt, size=6.6, color=INK)
            yy += 0.41

    # ---- the masked pre-send report (illustrative)
    rx, ry, rw, rh = 0.45, 3.05, 7.25, 2.68
    cv.rect(rx, ry, rw, rh, WHITE, GOLD, 1.75, R, 0.03)
    cv.rect(rx, ry, rw, 0.34, YELLOW_T, None, shape=R, radius=0.1)
    cv.text(rx + 0.15, ry, rw - 0.3, 0.34, [[("PRE-SEND REVIEW · G2  ", {"bold": True, "track": 120}),
                                            ("CHF post-discharge SMS nudge · run R-0412 · ", {}),
                                            ("illustrative numbers, masked data", {"color": MAGENTA})]],
            size=7, anchor=MSO_ANCHOR.MIDDLE)
    funnel = [("Eligible cohort (CHF, discharged in the last 7 days)", 1240, NAVY),
              ("No SMS consent for this channel", -310, MAGENTA), ("Opted out (STOP / DONE)", -42, MAGENTA),
              ("Readmitted or deceased", -18, MAGENTA), ("Identity match below threshold", -25, MAGENTA),
              ("Shared or unverified mobile number", -11, MAGENTA), ("Holdout set aside (10%)", -83, MUTE),
              ("Released for sending", 751, GREEN)]
    fx0, fy0, bw_max = rx + 0.15, ry + 0.45, 1.5
    cv.text(fx0, fy0 - 0.06, 3.6, 0.16, "WHO IS IN, AND WHY OTHERS ARE OUT", size=5.6, bold=True, color=MUTE,
            track=120)
    for i, (lab, v, col) in enumerate(funnel):
        yy = fy0 + 0.12 + i * 0.19
        cv.text(fx0, yy, 2.25, 0.19, lab, size=6.2, bold=i in (0, len(funnel) - 1), anchor=MSO_ANCHOR.MIDDLE)
        w = max(0.04, bw_max * abs(v) / 1240)
        cv.rect(fx0 + 2.3, yy + 0.035, w, 0.12, col, None)
        cv.text(fx0 + 2.35 + w, yy, 0.55, 0.19, ("%+d" % v) if v < 0 else "{:,}".format(v), size=6.3, bold=True,
                color=col, anchor=MSO_ANCHOR.MIDDLE)
    # checks
    cx0 = rx + 4.45
    cv.text(cx0, fy0 - 0.06, 2.7, 0.16, "CHECKS · ALL MUST BE GREEN", size=5.6, bold=True, color=MUTE, track=120)
    checks = ["Consent on record for SMS, with date and source", "Consent re-checked against today's opt-outs",
              "Discharge date inside the 7-day window", "Mobile verified, E.164 format",
              "Only the 6 approved fields will leave", "Message templates approved (G3)",
              "Frequency cap: no other nudge this week"]
    for i, t in enumerate(checks):
        yy = fy0 + 0.12 + i * 0.19
        cv.rect(cx0, yy + 0.03, 0.14, 0.14, GREEN, None, MSO_SHAPE.OVAL)
        cv.text(cx0, yy + 0.03, 0.14, 0.14, "✓", size=6, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(cx0 + 0.2, yy, 2.55, 0.19, t, size=6.2, anchor=MSO_ANCHOR.MIDDLE)
    # masked sample
    sy = ry + 2.2
    cv.text(fx0, sy - 0.02, 2.0, 0.15, "MASKED SAMPLE", size=5.6, bold=True, color=MUTE, track=120)
    cols = ["token", "name", "phone", "condition group", "discharge", "SMS consent"]
    vals = ["TKN-8F3A…", "•••••", "•••-•••-4417",
            "Heart failure", "D-3", "yes"]
    xs = [fx0, fx0 + 0.75, fx0 + 1.3, fx0 + 2.15, fx0 + 3.05, fx0 + 3.55]
    for x, c_, v in zip(xs, cols, vals):
        cv.text(x, sy + 0.13, 0.9, 0.14, c_, size=5.4, bold=True, color=MUTE)
        cv.text(x, sy + 0.27, 0.95, 0.16, v, size=6.2, font="Courier New")
    # decisions
    bx0 = rx + rw - 2.52
    for i, (t, f, ln, col) in enumerate([("Approve release", GREEN, GREEN, WHITE), ("Send back", WHITE, NAVY, NAVY),
                                         ("Stop", WHITE, MAGENTA, MAGENTA)]):
        bw = (1.0, 0.75, 0.55)[i]
        cv.rect(bx0, sy + 0.15, bw, 0.28, f, ln, 1.0, R, 0.4)
        cv.text(bx0, sy + 0.15, bw, 0.28, t, size=6.6, bold=True, color=col, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        bx0 += bw + 0.08

    # ---- five checks before any message
    kx, kw = 7.88, 12.88 - 7.88
    cv.rect(kx, 3.05, kw, 2.68, BLACK, None, shape=R, radius=0.03)
    cv.text(kx + 0.18, 3.1, kw - 0.36, 0.3, [[("FIVE CHECKS BEFORE ANY MESSAGE", {"bold": True, "track": 120,
                                                                                 "color": YELLOW})]], size=7.5,
            anchor=MSO_ANCHOR.MIDDLE)
    five = [("1 Build", "Privacy Guard: consent per channel, opt-outs, deceased, readmitted, duplicates.", "agent"),
            ("2 Review", "SME + tech lead approve the masked report (G2).", "people"),
            ("3 Release", "Consent re-checked at release; records time-limited to this run.", "system"),
            ("4 Send", "Marketing Cloud re-checks STOP, unsubscribes and frequency caps.", "system"),
            ("5 Reply", "STOP or DONE honoured at once and synced back to every pod.", "patient")]
    tagc = {"agent": CYAN, "people": YELLOW, "system": "BFBFBF", "patient": GREEN}
    for i, (t, d, who) in enumerate(five):
        yy = 3.45 + i * 0.42
        cv.text(kx + 0.18, yy, 0.75, 0.36, t, size=8, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(kx + 0.95, yy, kw - 1.85, 0.36, d, size=6.5, color="E6E6E6", anchor=MSO_ANCHOR.MIDDLE)
        cv.rect(kx + kw - 0.82, yy + 0.09, 0.66, 0.18, None, tagc[who], 0.75, R, 0.4)
        cv.text(kx + kw - 0.82, yy + 0.09, 0.66, 0.18, who.upper(), size=5.4, bold=True, color=tagc[who],
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=100)
    cv.text(kx + 0.18, 5.55, kw - 0.36, 0.16, "Any check fails: nothing is sent, and a named owner is told.",
            size=6.5, bold=True, color=MAGENTA, anchor=MSO_ANCHOR.MIDDLE)

    # ---- bottom line
    by = 5.88
    fx, fy, fw, fh = cv.frame(0.45, by, 12.43, 0.62, WHITE, 0.04)
    cv.text(fx + 0.2, fy, fw - 0.4, fh,
            [[("No person and no agent sees a patient's personal data to run a campaign.  ", {"bold": True}),
              ("The six fields needed to send (token, name, email, phone, condition group, discharge date) move "
               "from the release store to Marketing Cloud system to system, after G2 and G3, and only for this run.",
               {"color": INK})]], size=7.6, anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, HU_NOTES)
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
    human_angle(prs, layout)
    prs.save(out)
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
