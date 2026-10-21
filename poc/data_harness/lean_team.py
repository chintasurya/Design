"""One-slide preview: lean team and cost saving. Figures are the ones already in the Ascension Agentic Harness deck
(team and build cost, commercials, ROI, business outcomes). Black muted IG style. The last slide of the
Agentic Harness deck (build_data_harness_deck.py); this script also renders it alone.

    python3 lean_team.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import R, SRC, logo, new_slide
from build_mad_ig_deck import CYAN, YELLOW, set_notes
from footer import fix_footers
from platform_fit import panel
from sierra_voice import CARD, EDGE, T1, T2, T3, gbar
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "lean_team.pptx")

NOTES = """SLIDE: Lean team and cost saving   (about 2-3 minutes)

KEY MESSAGE
Every squad of 4-5 developers becomes 1 developer directing the harness agent, plus 1 QA. $16M a year today becomes $7M: $9M back every year on a $5.0M build, paid back in under 7 months.

WALK IT
- The squad: 4 developers and a QA today; with the harness, one developer directs the agent, a QA verifies, and the agent drafts code, tests and the Copado package overnight. People review, approve and own every change.
- The pod: what changes for every pod (pilot targets, baselined per pod): a new engineer is productive in about a week instead of 4-6 weeks, because they ask the graph; agents work overnight, so delivery runs about 20 hours a day instead of office hours; every change is checked against the same standards; a new pod goes live on the platform in 2 weeks instead of about 2 months. The same team delivers 1.4-1.6x the output, or the same scope with 20-30% fewer people.
- The build: 17 people at peak, 10 roles, 18 months, $4.79M fixed fee paid only when each gate is signed. From month 19 a run team of 4 keeps it running, about $1.24M a year with platform usage.
- The return (target, first full year after go-live): $16M a year today, $7M with the harness, $9M saved every year, on a $5.0M investment. Paid back in under 7 months; 80% first-year return.
- Floor we commit to: 20-25% lower net run cost per pod, measured against each pod's baseline.

KEEP IT HONEST
- Baseline every pod first. Year 1 delivers about 60-70% of steady state while pods onboard.
- Approvals, UAT and CAB stay human and take the same time.
- These figures cover delivery. The campaign data platform and the Sierra voice agent are sized separately, after Phase 0.
- Rates are assumed for sizing; replace with the Insight Global rate card before sharing."""


def chip(cv, x, y, w, h, t, line=EDGE, fill=CARD, tc=T1, icon=None, size=6.4):
    cv.rect(x, y, w, h, fill, line, 0.75, R, 0.25)
    tx, tw = x, w
    if icon:
        logo(cv, icon, x + 0.08, y + (h - 0.18) / 2, 0.18)
        tx, tw = x + 0.24, w - 0.28
    cv.text(tx, y, tw, h, t, size=size, bold=True, color=tc, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def label(cv, x, y, w, t, color=T3):
    cv.text(x, y, w, 0.18, t, size=5.4, bold=True, color=color, track=100, anchor=MSO_ANCHOR.MIDDLE)


def stat(cv, x, y, w, h, big, small, note=None, color=T1, hook=False):
    if hook:
        cv.frame(x, y, w, h, CARD, 0.02)
    else:
        cv.rect(x, y, w, h, CARD, None)
    y += max(0.0, (h - 1.05) / 2)                 # centre the figure in a tall tile
    cv.text(x + 0.14, y + 0.08, w - 0.24, 0.5, big, size=22, color=color, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(x + 0.14, y + 0.6, w - 0.24, 0.22, small, size=7, bold=True, color=T1, anchor=MSO_ANCHOR.MIDDLE)
    if note:
        cv.text(x + 0.14, y + 0.82, w - 0.24, 0.22, note, size=6, color=T2, anchor=MSO_ANCHOR.MIDDLE)


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · LEAN TEAM AND COST",
                "Lean teams on one platform: $9M back every year on a $5.0M build",
                "Every squad of 4-5 developers becomes 1 developer directing the harness agent, plus 1 QA. People "
                "review, approve and own every change.")
    # ---------------------------------------------------------------- row 1: squad, pod, build
    ty, th = 1.3, 2.15
    pw = (12.43 - 2 * 0.12) / 3
    xs = [0.45 + k * (pw + 0.12) for k in range(3)]
    # the squad
    x = xs[0]
    panel(cv, x, ty, pw, th, "THE SQUAD", "same scope, two people")
    label(cv, x + 0.14, ty + 0.38, 1.5, "TODAY")
    cw = (pw - 0.28 - 4 * 0.06) / 5
    for k, t in enumerate(["Dev", "Dev", "Dev", "Dev", "QA"]):
        chip(cv, x + 0.14 + k * (cw + 0.06), ty + 0.58, cw, 0.3, t, tc=T2)
    label(cv, x + 0.14, ty + 0.98, 1.5, "WITH THE HARNESS", CYAN)
    w3 = (pw - 0.28 - 2 * 0.06) / 3
    chip(cv, x + 0.14, ty + 1.18, w3, 0.3, "Developer", line=CYAN)
    chip(cv, x + 0.14 + w3 + 0.06, ty + 1.18, w3, 0.3, "Harness agent", line=CYAN, fill="06262B", tc=CYAN,
         icon="harness", size=6.0)
    chip(cv, x + 0.14 + 2 * (w3 + 0.06), ty + 1.18, w3, 0.3, "QA", line=CYAN)
    cv.text(x + 0.14, ty + 1.56, pw - 0.28, 0.42, [[("Agent ", {"bold": True, "color": CYAN}),
                                                     ("drafts code, tests and the Copado package overnight. ", {}),
                                                     ("Developer ", {"bold": True, "color": T1}),
                                                     ("directs and approves. ", {}),
                                                     ("QA ", {"bold": True, "color": T1}), ("signs off.", {})]],
            size=6.0, color=T2)
    # the pod: what changes for every pod (pilot targets from the operational efficiency slide)
    x = xs[1]
    panel(cv, x, ty, pw, th, "THE POD", "what changes for every pod")
    c0, c1, c2 = x + 0.14, x + 1.5, x + 2.6
    label(cv, c1, ty + 0.36, 1.0, "TODAY")
    label(cv, c2, ty + 0.36, 1.4, "WITH THE HARNESS", CYAN)
    rows = [("New engineer productive", "4-6 weeks", "about 1 week"),
            ("Delivery each day", "office hours", "about 20 hours"),
            ("Changes checked", "depends on reviewer", "100%, same standards"),
            ("New pod live", "about 2 months", "2 weeks")]
    for k, (a, b, c) in enumerate(rows):
        y = ty + 0.56 + k * 0.29
        cv.rect(c0, y, pw - 0.28, 0.25, CARD, None)
        cv.text(c0 + 0.08, y, 1.3, 0.25, a, size=6.0, bold=True, color=T1, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(c1, y, 1.08, 0.25, b, size=6.0, color=T2, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(c2, y, pw - 2.5, 0.25, c, size=6.0, bold=True, color=CYAN, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(c0, ty + 1.74, pw - 0.28, 0.36, [[("Same team: ", {"bold": True, "color": T1}),
                                              ("1.4-1.6x the output, or the same scope with 20-30% fewer people. ",
                                               {}),
                                              ("Pilot targets, baselined per pod.", {"color": T3})]],
            size=5.9, color=T2, anchor=MSO_ANCHOR.MIDDLE)
    # the build
    x = xs[2]
    panel(cv, x, ty, pw, th, "THE BUILD AND RUN", "fixed fee, paid by gate")
    q = (pw - 0.28 - 2 * 0.08) / 3
    for k, (b, d) in enumerate([("17", "people at peak, 10 roles"), ("18", "months, seven phases"),
                                ("$4.79M", "fixed fee, paid as each gate is signed")]):
        xx = x + 0.14 + k * (q + 0.08)
        cv.rect(xx, ty + 0.4, q, 0.98, CARD, None)
        cv.text(xx + 0.1, ty + 0.44, q - 0.14, 0.44, b, size=16, color=T1, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(xx + 0.1, ty + 0.88, q - 0.14, 0.46, d, size=5.9, color=T2)
    cv.text(x + 0.14, ty + 1.48, pw - 0.28, 0.5, [[("From month 19 ", {"bold": True, "color": T1}),
                                                    ("a run team of 4 keeps the graph, agents and evals current: "
                                                     "about $1.24M a year with platform usage.", {})]], size=6.0,
            color=T2)
    # ---------------------------------------------------------------- row 2: the money
    my = ty + th + 0.15
    mh = 2.15
    panel(cv, 0.45, my, 12.43, mh, "THE RETURN", "target · first full year after go-live")
    lw = 8.3
    sw = (lw - 0.14 - 3 * 0.1) / 4
    tiles = [("$16M", "a year today", "as provided by Ascension", T1, False),
             ("$7M", "a year with the harness", "agents and run team included", T1, False),
             ("$9M", "saved every year", "from go-live", CYAN, True),
             ("$5.0M", "invested once", "$4.79M build + $0.23M usage", T1, False)]
    th3 = mh - 0.52
    for k, (b, sm, n, c, hook) in enumerate(tiles):
        stat(cv, 0.45 + 0.14 + k * (sw + 0.1), my + 0.38, sw, th3, b, sm, n, color=c, hook=hook)
    rx = 0.45 + 0.14 + lw + 0.1
    rw = 12.88 - 0.14 - rx
    ch = (th3 - 0.1) / 2
    cards = [("Paid back in under 7 months", "80% first-year return; 1.8x the investment back in year one", CYAN),
             ("Floor we commit to", "20-25% lower net run cost per pod, against its own baseline", YELLOW)]
    for k, (t, d, c) in enumerate(cards):
        y = my + 0.38 + k * (ch + 0.1)
        cv.rect(rx, y, rw, ch, CARD, None)
        gbar(cv, rx, y, 0.05, ch)
        cv.text(rx + 0.18, y, rw - 0.26, ch, [[(t, {"bold": True, "size": 8, "color": c})], [(d, {"color": T2})]],
                size=6.4, anchor=MSO_ANCHOR.MIDDLE, after=2)
    # ---------------------------------------------------------------- bottom: keep it honest
    by, bh = my + mh + 0.15, 0.7
    cv.text(0.45, by, 1.3, bh, [[("KEEP IT HONEST", {"bold": True, "color": T1, "track": 120})],
                                [("how the numbers hold", {"color": T3, "size": 5.2})]], size=6.4,
            anchor=MSO_ANCHOR.MIDDLE, after=1)
    notes = [("Baseline every pod first", "savings counted against each pod's own numbers"),
             ("Year 1 at 60-70%", "of steady state while pods onboard"),
             ("Approvals stay human", "UAT and CAB take the same time"),
             ("Delivery only", "campaign data platform and Sierra sized after Phase 0")]
    w = (12.88 - 1.8 - 3 * 0.1) / 4
    for k, (t, d) in enumerate(notes):
        x = 1.8 + k * (w + 0.1)
        cv.rect(x, by, w, bh, CARD, None)
        cv.rect(x, by, 0.04, bh, CYAN, None)
        cv.text(x + 0.14, by, w - 0.2, bh, [[(t, {"bold": True, "size": 7, "color": T1})], [(d, {"color": T2})]],
                size=6.0, anchor=MSO_ANCHOR.MIDDLE, after=1)
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
