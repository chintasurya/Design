"""Health Cloud change timeline: ~2 weeks manual vs ~2 days on the Agentic Harness, Jira story to UAT sign-off.
The manual steps and figures are the ones in the Agentic Harness deck (deck/update_final.py); ~2 days is the
harness target, story to production. Colourful black IG style, like campaign_timeline.py.

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

# with the harness, in working hours (~26): day 1 takes the story to UAT, day 2 is UAT and production;
# (gate) after the bar
HOURS, DAY1 = 26, 18
HARNESS = [("Requirements Agent", "Jira + Confluence into a brief", 0, 3, CYAN, "H1"),
           ("Architect Agent", "impact and reuse from the graph; Change Guardian", 3, 8, CYAN, "H2"),
           ("Developer Agent", "Apex, LWC, Flows, sharing in DEV", 8, 12, CYAN, None),
           ("Review + Test Agents", "code, security, sharing; Apex tests, Zephyr", 12, 16, CYAN, "H3"),
           ("Release Agent", "Copado to SIT, then UAT; CAB pack", 16, 18, CYAN, None),
           ("UAT + production · H4 · CAB", "business signs UAT; CAB; the owning team deploys", 18, 26, YELLOW,
            "H4")]

NOTES = """SLIDE: A Health Cloud change: ~2 weeks manual vs ~2 days on the Agentic Factory   (about 2 minutes)

KEY MESSAGE
A typical Health Cloud task on the Network Services pod takes about two weeks today, from Jira story to UAT sign-off. On the Agentic Factory the same task goes from story to production in about two days. People still approve at every gate.

LEFT · TODAY
Nine steps, one hand-off at a time, inside office hours: about 10 working days. About four and a half of them (magenta) go on understanding the story, finding the impact by hand and writing tests by hand: that is what the harness takes out.

RIGHT · WITH THE AGENTIC FACTORY
The same seven delivery agents as every pod, with Health Cloud skills; about 26 working hours over two days.
Day 1: the Requirements Agent turns the story into a brief in about 3 hours and the product owner approves (H1); the Architect Agent reads impact and reuse from the knowledge graph in about 5 hours, the Change Guardian names affected pods, and the architect and pod owners approve (H2). The Developer Agent builds in DEV in about 4 hours; the Review and Test Agents check code, security and sharing and run the tests in about 4 hours, and the tech lead approves (H3); the Release Agent promotes through Copado to SIT and UAT in about 2 hours.
Day 2: about 8 hours of business UAT (H4), CAB approval and the owning team's deployment to production.

THE NUMBERS
About 80% faster: 10 working days to about 2 days. Already measured with agent-assisted delivery: 1-2 weeks down to 2-4 days. The graph, the agent build and the automated tests take it to about 2 days, story to production: the target, confirmed against the Phase 0 baseline.

BE READY FOR
- "Does every task take 2 days?" Small changes take less; large or cross-pod changes take longer because more owners approve.
- "Does CAB meet every day?" Day 2 assumes a CAB slot; otherwise production waits for the next CAB window. The agents never deploy to production.
- "Why only 4 hours to build?" A typical Health Cloud task is a validation rule, a Flow or a small Apex change; the agent builds it with the design already approved and the context from the graph."""


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC FACTORY · NETWORK SERVICES POD · HEALTH CLOUD",
                "A Health Cloud change: ~2 weeks manual vs ~2 days on the Agentic Factory",
                "Any Health Cloud task. The same seven delivery agents with Health Cloud skills: day 1 takes the story "
                "to UAT, day 2 is UAT and production. People approve at every gate.")
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
    axis(cv, bx, bw, gy - 0.22, (0.5, 4.5, 9.5), 10, ["Day 1", "Day 5", "Day 10"])
    # ---------------------------------------------------------------- with the harness
    rx = lx + lw + 0.14
    rw = 12.88 - rx
    fx, fy, fw, fh = cv.frame(rx, top, rw, ph, "0A0A0A", 0.02)
    cv.text(fx + 0.14, fy + 0.04, 4, 0.2, "WITH THE AGENTIC FACTORY · 7 DELIVERY AGENTS", size=7, bold=True,
            color=CYAN, track=120, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.14, fy + 0.24, 2.2, 0.42, "~2 days", size=20, color=CYAN, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 2.3, fy + 0.28, fw - 2.44, 0.36, "~26 working hours: day 1 story to UAT, day 2 UAT and "
            "production", size=7, color=T2, anchor=MSO_ANCHOR.MIDDLE)
    rh2 = 0.45
    gy2 = top + 0.98
    rows = [r[:5] for r in HARNESS]
    bx2, bw2 = gantt(cv, rx + 0.1, gy2, rw - 0.2, rows, HOURS, rh2, 2.5, "harness", unit="h")
    axis(cv, bx2, bw2, gy2 - 0.22, (DAY1 / 2, (DAY1 + HOURS) / 2), HOURS, ["Day 1", "Day 2"])
    xd = bx2 + bw2 * DAY1 / HOURS                          # the day 1 / day 2 boundary, clear of the short
    xd = max(xd, bx2 + bw2 * 16 / HOURS + 0.32)            # release bar (drawn at least 0.3" wide)
    cv.rect(xd - 0.005, gy2 - 0.06, 0.01, len(HARNESS) * rh2 + 0.01, "5A5A5A", None)
    # people approve at the end of the step: a yellow gate marker after the bar
    for k, (t, d, a, b, col, gate) in enumerate(HARNESS):
        if not gate or col == YELLOW:
            continue
        yy = gy2 + k * rh2
        x1 = bx2 + bw2 * b / HOURS
        x1 = max(x1, bx2 + bw2 * a / HOURS + 0.3)          # short bars are drawn at least 0.3" wide
        cv.rect(x1 + 0.05, yy + 0.09, 0.34, rh2 - 0.23, YELLOW, None, shape=R, radius=0.3)
        cv.text(x1 + 0.05, yy + 0.09, 0.34, rh2 - 0.23, gate, size=7, bold=True, color="000000",
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.14, gy2 + 6 * rh2 + 0.06, fw - 0.28, 0.42, [[("Day 2 assumes a CAB slot; otherwise the next CAB window. ",
                                                                 {"bold": True, "color": YELLOW}),
                                                                ("Cyan: agents. Yellow: people approve (H1-H4).",
                                                                 {"color": T2})]], size=7,
            anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- results
    sy, sh = top + ph + 0.12, 0.74
    stats = [("~80%", "faster per task", "~10 working days to ~2 days, now to production"),
             ("2-4 days", "measured so far", "agent-assisted today; the factory takes it to ~2"),
             ("7", "delivery agents", "the same for every pod, with Health Cloud skills"),
             ("4 gates", "people still approve", "H1 brief, H2 design, H3 code, H4 UAT; plus CAB")]
    w = (12.43 - 3 * 0.12) / 4
    for k, (b, t, d) in enumerate(stats):
        x = 0.45 + k * (w + 0.12)
        cv.rect(x, sy, w, sh, CARD, None)
        gbar(cv, x, sy, 0.05, sh)
        cv.text(x + 0.18, sy, 1.2, sh, b, size=18, color=(CYAN, MAGENTA, T1, YELLOW)[k], anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 1.4, sy, w - 1.5, sh, [[(t, {"bold": True, "color": T1})], [(d, {"color": T2})]], size=7,
                anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, sy + sh + 0.04, 12.43, 0.2, "Today: a typical Health Cloud task on the Network Services pod, Jira "
            "story to UAT sign-off. Measured: agent-assisted delivery at Ascension, 1-2 weeks to 2-4 days. ~2 days to "
            "production is the factory target, confirmed against the Phase 0 baseline.", size=7, color=T3, anchor=MSO_ANCHOR.MIDDLE)
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
