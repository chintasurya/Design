"""Lean team and savings, redesigned: today's squad and the lean squad, what changes per pod (Health Cloud,
Marketing Cloud, Sierra), build and run, then Year 1, 2 and 3 and a three-year band. No pricing shown.

Savings model (rescaled to the real squad):
  today        PM / outcome owner, tech lead / SEM, 2-3 developers, 1-2 QA     = 5-7 people (6 on average)
  with harness PM / outcome owner, 1 engineer (dev + QA), tech lead shared by 2-3 squads, harness agent
               = about 2.4 people, so people cost falls to 40% of today
  run cost     run team + platform $1.24M a year, model and token allowance $0.4M a year (to confirm)
  ramp         60% of the saving in year 1, 90% in year 2, 100% in year 3, as pods go live
  all pods     $16M a year today (as provided)  ->  $8.0M at full run rate: about $8M saved a year

    python3 lean_team.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import R, SRC, logo, new_slide
from build_mad_ig_deck import CYAN, MAGENTA, YELLOW, set_notes
from footer import fix_footers
from sierra_voice import CARD, EDGE, T1, T2, T3
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "lean_team.pptx")
TINTS = {CYAN: "06262B", YELLOW: "2B2508", MAGENTA: "2B0716"}

TODAY = 16.0
PEOPLE_SHARE = 2.4 / 6
RUN = 1.24 + 0.4
STEADY = TODAY * PEOPLE_SHARE + RUN
SAVE = TODAY - STEADY
RAMP = (0.6, 0.9, 1.0)
YEARS = [(TODAY - SAVE * r, SAVE * r) for r in RAMP]

NOTES = """SLIDE: Lean squads and what they save   (about 3 minutes)

KEY MESSAGE
Today a squad is 5-7 people. With the factory it is a PM, one engineer who directs the harness agent and verifies its work, and a tech lead shared across two or three squads. Across all pods, $16M a year today falls to about $8M at full run rate: about $20M saved over three years.

TOP
- Today's squad: PM / outcome owner, tech lead / SEM, 2-3 developers, 1-2 QA.
- With the harness: the PM keeps ownership; one engineer (dev + QA) directs the agent and verifies; the tech lead / SEM is shared across 2-3 squads and still approves the code at H3. The agent drafts code, tests and the Copado package.
- Why a human still checks quality: the agent writes requirements, code and tests from the same understanding, so a person must confirm we built the right thing, sign UAT, and own it at CAB.
- What changes per pod: Health Cloud pods take a story to UAT in about 2 days instead of about 2 weeks; Marketing Cloud pods build campaigns on governed data that is already ready; the Sierra pod answers from governed articles and books through scoped APIs.
- Build and run: 17 people at peak over 18 months, then a run team of 4.

YEARS
Year 1 saves about $4.8M (pods go live through the year), year 2 about $7.2M, year 3 about $8.0M at full run rate.

HOW THE NUMBERS ARE BUILT
People cost falls to 40% of today (2.4 of 6 people per squad). Run cost: run team and platform $1.24M a year, plus a model and token allowance of about $0.4M a year, to confirm against Ascension's Codex limits. Ramp 60%, 90%, 100%. All are planning estimates, confirmed against each pod's Phase 0 baseline."""


def box(cv, x, y, w, h, title, color):
    cv.rect(x, y, w, h, TINTS[color], color, 0.75, R, 0.03)
    cv.rect(x, y, w, 0.28, color, None)
    cv.text(x + 0.12, y, w - 0.24, 0.28, title, size=7, bold=True, track=120,
            color="FFFFFE" if color == MAGENTA else "000000", anchor=MSO_ANCHOR.MIDDLE)


def chip(cv, x, y, w, h, t, line, fill=CARD, tc=T1, icon=None):
    cv.rect(x, y, w, h, fill, line, 0.75, R, 0.25)
    tx, tw = x, w
    if icon:
        logo(cv, icon, x + 0.06, y + (h - 0.16) / 2, 0.16)
        tx, tw = x + 0.2, w - 0.22
    cv.text(tx, y, tw, h, t, size=7, bold=True, color=tc, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def money(v):
    return "$%.1fM" % v


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · LEAN SQUADS",
                "Lean squads on one platform: about $20M back over three years",
                "A squad of 5-7 becomes a PM and one engineer directing the harness agent, with a shared tech lead. "
                "People still approve and own every change.")
    top, th = 1.28, 2.0
    # ---------------------------------------------------------------- 1 the squad
    x1, w1 = 0.45, 4.6
    box(cv, x1, top, w1, th, "THE SQUAD  ·  TODAY → WITH THE HARNESS", CYAN)
    ix = x1 + 0.12
    cv.text(ix, top + 0.34, 2, 0.18, "TODAY · 5-7 PEOPLE", size=7, bold=True, color=T3, track=80,
            anchor=MSO_ANCHOR.MIDDLE)
    today = [("PM / owner", 0.82), ("Tech lead / SEM", 1.0), ("Dev ×2-3", 0.82), ("QA ×1-2", 0.74)]
    x = ix
    for t, w in today:
        chip(cv, x, top + 0.54, w, 0.32, t, EDGE, tc=T2)
        x += w + 0.06
    cv.text(ix, top + 0.98, 3, 0.18, "WITH THE HARNESS · ~2.4 PEOPLE", size=7, bold=True, color=CYAN, track=80,
            anchor=MSO_ANCHOR.MIDDLE)
    lean = [("PM / owner", 0.82, None, CARD, T1), ("Engineer · dev + QA", 1.22, None, CARD, T1),
            ("Harness agent", 1.08, "harness", "06262B", CYAN), ("Tech lead · shared", 1.0, None, CARD, T2)]
    x = ix
    for t, w, ic, fl, tc in lean:
        chip(cv, x, top + 1.18, w, 0.32, t, CYAN, fl, tc, ic)
        x += w + 0.06
    cv.text(ix, top + 1.56, w1 - 0.24, 0.4, [[("Agent ", {"bold": True, "color": CYAN}),
                                              ("drafts code, tests and the Copado package. ", {}),
                                              ("Engineer ", {"bold": True, "color": T1}),
                                              ("directs it and verifies. ", {}),
                                              ("Tech lead ", {"bold": True, "color": T1}),
                                              ("approves at H3 for 2-3 squads.", {})]], size=7, color=T2)
    # ---------------------------------------------------------------- 2 what changes per pod
    x2 = x1 + w1 + 0.12
    w2 = 4.6
    box(cv, x2, top, w2, th, "WHAT CHANGES FOR EVERY POD", MAGENTA)
    pods = [("salesforce", "Health Cloud pods", "Jira story to UAT in about 2 days, not about 2 weeks"),
            ("salesforce", "Marketing Cloud pods", "campaigns build on governed data that is already ready; "
                                                     "no data preparation per campaign"),
            (None, "Sierra pod", "answers from governed articles; bookings through scoped APIs, caller "
                                 "verified first")]
    for k, (ic, t, d) in enumerate(pods):
        y = top + 0.38 + k * 0.53
        cv.rect(x2 + 0.12, y, w2 - 0.24, 0.47, CARD, None)
        cv.rect(x2 + 0.12, y, 0.05, 0.47, MAGENTA, None)
        tx = x2 + 0.26
        if ic:
            logo(cv, ic, tx, y + 0.06, 0.18)
            tx += 0.24
        cv.text(tx, y + 0.03, x2 + w2 - tx - 0.16, 0.2, t, size=7.4, bold=True, color=T1,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x2 + 0.26, y + 0.23, w2 - 0.44, 0.24, d, size=7, color=T2, anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- 3 build and run
    x3 = x2 + w2 + 0.12
    w3 = 12.88 - x3
    box(cv, x3, top, w3, th, "BUILD AND RUN", YELLOW)
    stats = [("17", "people at peak, 10 roles"), ("18", "months to every pod live"), ("4", "run team from month 19")]
    sw = (w3 - 0.24 - 2 * 0.08) / 3
    for k, (b, d) in enumerate(stats):
        x = x3 + 0.12 + k * (sw + 0.08)
        cv.rect(x, top + 0.38, sw, 1.0, CARD, None)
        cv.text(x + 0.08, top + 0.42, sw - 0.12, 0.42, b, size=18, color=YELLOW, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.08, top + 0.86, sw - 0.12, 0.48, d, size=7, color=T2)
    cv.text(x3 + 0.12, top + 1.46, w3 - 0.24, 0.5, "The run team keeps the graph, agents, rules and evals current "
            "once every pod is live.", size=7, color=T2, anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- years
    yy, yh = top + th + 0.16, 1.92
    yw = (12.43 - 2 * 0.16) / 3
    caps = ["Pods go live through the year.", "Every pod on the harness for the full year.",
            "Full run rate: agents carry the delivery, people steer."]
    for k, ((after, saved), cap) in enumerate(zip(YEARS, caps)):
        x = 0.45 + k * (yw + 0.16)
        cv.rect(x, yy, yw, yh, CARD, EDGE, 0.75, R, 0.03)
        cv.text(x + 0.16, yy + 0.08, 2, 0.28, "Year %d" % (k + 1), size=11, bold=True, color=T1,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.16, yy + 0.4, 1.4, 0.16, "TODAY", size=7, bold=True, color=T3, track=100,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 1.75, yy + 0.4, 2, 0.16, "WITH THE HARNESS", size=7, bold=True, color=CYAN, track=100,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.16, yy + 0.56, 1.4, 0.36, money(TODAY), size=18, color=T3, anchor=MSO_ANCHOR.MIDDLE)
        cv.arrow(x + 1.2, yy + 0.74, x + 1.6, yy + 0.74, T1, 1.25)
        cv.text(x + 1.75, yy + 0.56, 2, 0.36, money(after), size=18, color=T1, anchor=MSO_ANCHOR.MIDDLE)
        fx, fy, fw, fh = cv.frame(x + 0.16, yy + 1.0, yw - 0.32, 0.56, "1A1A1A", 0.03)
        cv.text(fx + 0.12, fy, 2, fh, [[("SAVES", {"bold": True, "color": YELLOW, "track": 120})],
                                       [("%d%% of the year's spend" % round(100 * saved / TODAY),
                                         {"color": T2})]], size=7, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(fx + fw - 1.5, fy, 1.4, fh, money(saved), size=22, color=T1, align=PP_ALIGN.RIGHT,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.16, yy + 1.6, yw - 0.32, 0.28, cap, size=7, color=T2, anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- three-year band
    by, bh = yy + yh + 0.14, 0.86
    cv.rect(0.45, by, 12.43, bh, "0A0A0A", EDGE, 0.75, R, 0.03)
    cv.text(0.6, by + 0.04, 4, 0.2, "THREE YEARS, ALL PODS", size=7, bold=True, color=YELLOW, track=120,
            anchor=MSO_ANCHOR.MIDDLE)
    total_after = sum(a for a, _ in YEARS)
    total_saved = sum(v for _, v in YEARS)
    cells = [("Spend today", money(3 * TODAY), "$16M a year × 3", T1),
             ("With the harness", money(total_after), "people, run team and model usage included", T1),
             ("Saved over 3 years", money(total_saved), "%d%% of three years' spend" % round(100 * total_saved /
                                                                                        (3 * TODAY)), CYAN),
             ("At full run rate", "%d%% lower" % round(100 * SAVE / TODAY), "about %s saved every year" %
              money(SAVE), YELLOW)]
    cw = 12.13 / 4
    for k, (t, b, d, c) in enumerate(cells):
        x = 0.6 + k * cw
        cv.text(x, by + 0.24, cw - 0.1, 0.16, t, size=7, color=T2, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x, by + 0.4, cw - 0.1, 0.3, b, size=15, color=c, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x, by + 0.68, cw - 0.1, 0.16, d, size=7, color=T3, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, by + bh + 0.04, 12.43, 0.2, "Planning estimates: people cost falls to 40% (2.4 of 6 per squad); "
            "run team and platform $1.24M a year; model and token allowance $0.4M a year, to confirm against Codex "
            "limits; ramp 60% / 90% / 100%. Confirmed against each pod's Phase 0 baseline.", size=7, color=T3,
            anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, NOTES)
    return s


def main(out=OUT):
    prs = Presentation(SRC)
    lst = prs.slides._sldIdLst
    for el in list(lst):
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    build(prs, layout)
    fix_footers(prs)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    prs.save(out)
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
