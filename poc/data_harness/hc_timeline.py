"""Health Cloud change timeline: ~2 weeks manual vs ~2 days on the Agentic Harness, Jira story to UAT sign-off.
The manual steps and figures are the ones in the Agentic Harness deck (deck/update_final.py); ~2 days is the
harness target. Colourful black IG style, like campaign_timeline.py.

    python3 hc_timeline.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import R, SRC, new_slide
from build_mad_ig_deck import CYAN, MAGENTA, YELLOW, set_notes
from campaign_timeline import axis, gantt
from footer import fix_footers
from sierra_voice import CARD, EDGE, T1, T2, T3, gbar
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "hc_timeline.pptx")

# today: one Health Cloud task, Jira story to UAT sign-off, ~10 working days; magenta: the hand work the harness
# takes out (understanding the story, finding the impact, writing tests)
MANUAL = [("Story intake", "Jira story; back and forth with the PO", 0, 1, True),
          ("Clarify requirements", "Confluence, meetings; criteria agreed", 1, 2, True),
          ("Impact analysis", "objects, Flows, sharing and who uses them", 2, 3.5, True),
          ("Solution design", "data model, sharing, automation; review", 3.5, 4.5, False),
          ("Build", "Apex, LWC, Flows, permission sets in DEV", 4.5, 6.5, False),
          ("Code review and fixes", "peer review, Code Analyzer, rework", 6.5, 7.5, False),
          ("Test preparation", "Zephyr cases and test data by hand", 7.5, 8.5, True),
          ("QA and regression", "run cases, Copado regression, defects", 8.5, 9.5, False),
          ("Promote and UAT sign-off", "Copado to SIT / UAT; business signs", 9.5, 10, False)]

# with the harness, in elapsed hours: agents build overnight, people approve by day; (gate) after the bar
HARNESS = [("Requirements Agent", "Jira + Confluence into a brief", 0, 3, CYAN, "H1"),
           ("Architect Agent", "impact and reuse from the graph; Change Guardian", 3, 8, CYAN, "H2"),
           ("Developer Agent", "Apex, LWC, Flows, sharing in DEV, overnight", 8, 24, CYAN, None),
           ("Review + Test Agents", "code, security, sharing; Apex tests, Zephyr", 24, 32, CYAN, "H3"),
           ("Release Agent", "Copado to SIT, then UAT; CAB pack", 32, 38, CYAN, None),
           ("Business UAT sign-off · H4", "the business owner signs UAT", 38, 48, YELLOW, "H4")]

NOTES = """SLIDE: A Health Cloud change: ~2 weeks manual vs ~2 days on the Agentic Harness   (about 2 minutes)

KEY MESSAGE
A typical Health Cloud task on the Network Services pod, from Jira story to UAT sign-off, takes about two weeks today. On the Agentic Harness the same task takes about two days. People still approve at every gate.

LEFT · TODAY
Nine steps, one hand-off at a time, inside office hours: about 10 working days. About four and a half of them (magenta) go on understanding the story, finding the impact by hand and writing tests by hand: that is what the harness takes out.

RIGHT · WITH THE AGENTIC HARNESS
The same seven delivery agents as every pod, with Health Cloud skills. Day 1 morning: the Requirements Agent turns the story into a brief and the product owner approves (H1); the Architect Agent reads impact and reuse from the knowledge graph, the Change Guardian names affected pods, and the architect and pod owners approve (H2). Day 1 afternoon and overnight: the Developer Agent builds in DEV. Day 2: the Review and Test Agents check code, security and sharing and run the tests, and the tech lead approves (H3); the Release Agent promotes through Copado to SIT and UAT; the business signs UAT (H4).

THE NUMBERS
About 80% faster: 10 working days to about 2 days. Already measured with agent-assisted delivery: 1-2 weeks down to 2-4 days. The graph, the overnight build and the automated tests take it to about 2 days: the target, confirmed against the Phase 0 baseline.

BE READY FOR
- "Does every task take 2 days?" Small changes take less; large or cross-pod changes take longer because more owners approve.
- "And production?" It still goes through CAB in its normal window; the two days are story to UAT sign-off."""


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · NETWORK SERVICES POD · HEALTH CLOUD",
                "A Health Cloud change: ~2 weeks manual vs ~2 days on the Agentic Harness",
                "Any Health Cloud task, Jira story to UAT sign-off. The same seven delivery agents with Health Cloud "
                "skills; agents build overnight, people approve by day.")
    top, ph = 1.28, 4.36
    # ---------------------------------------------------------------- today
    lx, lw = 0.45, 6.15
    cv.rect(lx, top, lw, ph, "0A0A0A", EDGE, 0.75, R, 0.02)
    cv.text(lx + 0.14, top + 0.06, 3, 0.2, "TODAY · MANUAL DELIVERY", size=7, bold=True, color=T2, track=120,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(lx + 0.14, top + 0.26, 2, 0.42, "~2 weeks", size=20, color=T1, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(lx + 2.0, top + 0.26, lw - 2.14, 0.42, [[("~10 working days, one hand-off at a time. ", {"color": T2}),
                                                    ("~4.5 days", {"bold": True, "color": MAGENTA}),
                                                    (" understanding the story, finding the impact and writing "
                                                     "tests by hand", {"color": T2})]], size=7,
            anchor=MSO_ANCHOR.MIDDLE)
    rh = 0.35
    gy = top + 0.98
    bx, bw = gantt(cv, lx + 0.1, gy, lw - 0.2, MANUAL, 10, rh, 2.3, "manual")
    axis(cv, bx, bw, gy - 0.22, (0, 5, 10), 10)
    # ---------------------------------------------------------------- with the harness
    rx = lx + lw + 0.14
    rw = 12.88 - rx
    fx, fy, fw, fh = cv.frame(rx, top, rw, ph, "0A0A0A", 0.02)
    cv.text(fx + 0.14, fy + 0.04, 4, 0.2, "WITH THE AGENTIC HARNESS · 7 DELIVERY AGENTS", size=7, bold=True,
            color=CYAN, track=120, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.14, fy + 0.24, 2.2, 0.42, "~2 days", size=20, color=CYAN, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 2.3, fy + 0.28, fw - 2.44, 0.36, "~48 hours elapsed: agents build overnight, people approve by "
            "day", size=7, color=T2, anchor=MSO_ANCHOR.MIDDLE)
    rh2 = 0.45
    gy2 = top + 0.98
    rows = [r[:5] for r in HARNESS]
    bx2, bw2 = gantt(cv, rx + 0.1, gy2, rw - 0.2, rows, 48, rh2, 2.5, "harness", unit="h")
    axis(cv, bx2, bw2, gy2 - 0.22, (0, 24, 48), 48, per_day=24)
    # people approve at the end of the step: a yellow gate marker after the bar
    for k, (t, d, a, b, col, gate) in enumerate(HARNESS):
        if not gate or col == YELLOW:
            continue
        yy = gy2 + k * rh2
        x1 = bx2 + bw2 * b / 48
        x1 = max(x1, bx2 + bw2 * a / 48 + 0.3)          # short bars are drawn at least 0.3" wide
        cv.rect(x1 + 0.05, yy + 0.09, 0.34, rh2 - 0.23, YELLOW, None, shape=R, radius=0.3)
        cv.text(x1 + 0.05, yy + 0.09, 0.34, rh2 - 0.23, gate, size=7, bold=True, color="000000",
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.14, gy2 + 6 * rh2 + 0.06, fw - 0.28, 0.42, [[("Production follows the normal CAB window. ",
                                                                 {"bold": True, "color": YELLOW}),
                                                                ("Cyan: agents. Yellow: people approve (H1-H4).",
                                                                 {"color": T2})]], size=7,
            anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- results
    sy, sh = top + ph + 0.12, 0.74
    stats = [("~80%", "faster per task", "~10 working days to ~2 days"),
             ("2-4 days", "measured so far", "agent-assisted today; the harness takes it to ~2"),
             ("7", "delivery agents", "the same for every pod, with Health Cloud skills"),
             ("4 gates", "people still approve", "H1 brief, H2 design, H3 code, H4 UAT; then CAB")]
    w = (12.43 - 3 * 0.12) / 4
    for k, (b, t, d) in enumerate(stats):
        x = 0.45 + k * (w + 0.12)
        cv.rect(x, sy, w, sh, CARD, None)
        gbar(cv, x, sy, 0.05, sh)
        cv.text(x + 0.18, sy, 1.2, sh, b, size=18, color=(CYAN, MAGENTA, T1, YELLOW)[k], anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 1.4, sy, w - 1.5, sh, [[(t, {"bold": True, "color": T1})], [(d, {"color": T2})]], size=7,
                anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, sy + sh + 0.04, 12.43, 0.2, "Today: a typical Health Cloud task on the Network Services pod, Jira "
            "story to UAT sign-off. Measured: agent-assisted delivery at Ascension, 1-2 weeks to 2-4 days. ~2 days is "
            "the harness target, confirmed against the Phase 0 baseline.", size=7, color=T3, anchor=MSO_ANCHOR.MIDDLE)
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
