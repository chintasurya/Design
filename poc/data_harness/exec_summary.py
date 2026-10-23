"""Two-slide executive summary for the Ascension Agentic Factory, in the IG proposal style: white page, spaced
section headings, prose and bullets; slide 2 ends in a black timeline band.

1 Our understanding · Results & value · Why Insight Global, in business terms
2 Solution overview · Key considerations · Solution timeline, pilot to scale

    python3 exec_summary.py
"""
import os

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn

from build_data_harness_deck import SRC
from build_mad_ig_deck import CYAN, Canvas, set_notes
from footer import fix_footers
from sierra_voice import gbar
from story_slides import set_bg

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Ascension Agentic Factory - Executive Summary (2 slides).pptx")
INK, SOFT_INK, RULE = "1A1A1A", "4D4D4D", "BFBFBF"
BODY = 12


def heading(cv, x, y, w, t, color=INK):
    cv.text(x, y, w, 0.3, t, size=13, bold=True, color=color, track=300, anchor=MSO_ANCHOR.MIDDLE)


def bullets(cv, x, y, w, h, items, size=BODY, color=INK, gap=4):
    tb = cv.text(x, y, w, h, list(items), size=size, color=color, after=gap)
    for p in tb.text_frame.paragraphs:
        ppr = p._p.get_or_add_pPr()
        ppr.set("marL", "228600")
        ppr.set("indent", "-228600")
        bu = ppr.makeelement(qn("a:buChar"), {"char": "•"})
        ppr.append(bu)
    return tb


def page_head(cv):
    cv.text(0.45, 0.2, 6, 0.2, "EXECUTIVE SUMMARY", size=8, bold=True, color=INK, track=300,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, 0.45, 12.43, 0.7, "Executive Summary", size=36, bold=True, color=INK, anchor=MSO_ANCHOR.MIDDLE)


# ================================================================== 1
NOTES_1 = """SLIDE: Executive summary (1 of 2)   (about 2 minutes)

OUR UNDERSTANDING
Ascension wants to use AI to reach patients sooner, serve them better and run its digital operations at lower cost, without putting patient data at risk. Today a patient-outreach campaign takes about 90 days to launch, a change to care-team tools in Salesforce takes about two weeks, and routine patient calls depend on staff. The Ascension Agentic Factory brings AI to all three on one secure, HIPAA-aligned platform. We start with post-discharge follow-up for heart-failure patients and the Network Services team, then add programs and teams.

RESULTS & VALUE
Campaigns in about 10-12 days instead of about 90; care-team changes in about 2 days instead of about 2 weeks; consent checked before every message; routine calls answered by the voice agent with a hand-off to staff; about $19.9M saved over three years. The figures are pilot targets and planning estimates, confirmed against today's baseline.

WHY INSIGHT GLOBAL
Healthcare-ready and HIPAA-aligned by design; already proven at Ascension (agent-assisted delivery took changes from 1-2 weeks to 2-4 days); built on Ascension's existing Salesforce, Google Cloud and Codex; outcome-led and delivered in small releases."""


def slide_1(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg(s, "FFFFFF")
    cv = Canvas(s)
    page_head(cv)
    heading(cv, 0.45, 1.22, 8, "OUR UNDERSTANDING")
    cv.text(0.45, 1.58, 12.43, 1.5, [
        "Ascension is seeking to use AI to reach patients sooner, serve them better and run its digital operations "
        "at lower cost, without putting patient data at risk. Today a patient-outreach campaign takes about 90 days "
        "to launch, a change to care-team tools in Salesforce takes about two weeks, and routine patient calls depend "
        "on staff. The Ascension Agentic Factory brings AI to all three, on one secure, HIPAA-aligned platform.",
        "The initial focus will be post-discharge follow-up for heart-failure patients and the Network Services "
        "team, followed by more patient programs and teams, using a measured pilot and incremental releases."],
        size=BODY, color=INK, after=10, line=1.08)
    # results & value (left) | why Insight Global (right)
    top = 3.25
    lx, lw = 0.45, 6.75
    heading(cv, lx, top, lw, "RESULTS & VALUE")
    cv.text(lx, top + 0.38, lw, 1.0, "The solution addresses slow launches of patient programs, manual work "
            "repeated for every campaign and change, routine calls that tie up staff, and the risk that comes with "
            "patient data. Success will be measured by time to launch, patients reached, cost per change and zero "
            "unauthorized access to patient data.", size=BODY, color=INK, line=1.08)
    bullets(cv, lx, top + 1.5, lw, 2.1, [
        "Launch patient-outreach campaigns in ~10-12 days, not ~90",
        "Deliver care-team tool changes in ~2 days, not ~2 weeks",
        "Reach the right patients, with consent checked before every message",
        "Handle routine patient calls with the voice agent; staff take the rest",
        "Save about $19.9M over three years",
        "Build a scalable AI foundation for future programs"])
    # dotted divider
    cv.arrow(7.55, top + 0.05, 7.55, 6.85, RULE, 2.0, dash="sysDot", head=False)
    rx, rw = 7.9, 4.98
    heading(cv, rx, top, rw, "WHY INSIGHT GLOBAL")
    bullets(cv, rx, top + 0.42, rw, 3.0, [
        "Healthcare-ready: HIPAA-aligned by design; AI never sees raw patient data",
        "Proven at Ascension: agent-assisted delivery already took changes from 1-2 weeks to 2-4 days",
        "Built on Ascension's existing Salesforce, Google Cloud and Codex investments",
        "Outcome-led delivery with measurable success criteria",
        "Iterative MVP approach: early value, not a big-bang launch",
        "People stay in control: every AI recommendation is approved"], gap=5)
    set_notes(s, NOTES_1)
    return s


# ================================================================== 2
NOTES_2 = """SLIDE: Executive summary (2 of 2)   (about 2 minutes)

SOLUTION OVERVIEW
Insight Global designs and implements an AI solution for three parts of Ascension's business: patient-outreach campaigns in Marketing Cloud, changes to care-team tools in Salesforce Health Cloud, and the voice agent that answers patients and manages appointments. AI agents do the research, building and testing; Ascension's people approve every step; patient data stays in Ascension's Google Cloud, governed and masked.

KEY CONSIDERATIONS
Patient safety and HIPAA come first; people stay in control; existing investments are reused; everything is proven on test data before any real patient; releases are small and frequent; outcomes are measured.

SOLUTION TIMELINE
Six steps: agree goals and measure today; set up the secure data foundation; ready the AI agents on Ascension's own systems and rules; build and test the first campaign on test data; reach the first real patients; then measure and scale to more programs, teams and the voice agent. Durations are agreed in discovery. Care-team changes for the Network Services team start once the agents are ready."""

PHASES = [("Discovery & baseline", "goals, owners, today's measures"),
          ("Secure data foundation", "patient data governed in Google Cloud"),
          ("AI agents ready", "trained on Ascension's systems and rules"),
          ("First campaign built & tested", "heart-failure follow-up, on test data"),
          ("First patients reached", "live, with consent checked"),
          ("Measure & scale", "more programs, teams, the voice agent")]


def slide_2(prs, layout):
    s = prs.slides.add_slide(layout)
    set_bg(s, "000000")                 # black page: the footer turns white over the timeline band
    cv = Canvas(s)
    band = 4.2
    cv.rect(0, 0, 13.333, band, "FFFFFF", None)
    page_head(cv)
    lx, lw = 0.45, 6.6
    heading(cv, lx, 1.45, lw, "SOLUTION OVERVIEW")
    cv.text(lx, 1.83, lw, 2.3, "Insight Global will design and implement an AI solution for three parts of "
            "Ascension's business: patient-outreach campaigns in Marketing Cloud, faster changes to care-team tools in "
            "Salesforce Health Cloud, and a voice agent that answers patients and manages their appointments. AI "
            "agents do the research, building and testing; Ascension's people approve every step; patient data stays "
            "in Ascension's Google Cloud, governed and masked. Delivery follows a measured pilot, providing early "
            "value while establishing a scalable foundation for every team.", size=11.5, color=INK, line=1.08)
    rx, rw = 7.55, 5.33
    heading(cv, rx, 1.45, rw, "KEY CONSIDERATIONS")
    bullets(cv, rx, 1.85, rw, 2.3, [
        "Patient safety and HIPAA first: consent checked before every message",
        "People stay in control: every AI recommendation is approved",
        "Existing Salesforce, Google Cloud and Codex investments reused",
        "Proven on test data before any real patient",
        "Incremental releases, not a big-bang launch",
        "Measurable outcomes: speed, reach, cost and safety"], size=11.5, gap=3)
    # ---------------------------------------------------------------- timeline band
    cv.text(0.45, band + 0.22, 12.4, 0.34, [[("SOLUTION TIMELINE – ", {"color": "FFFFFF"}),
                                            ("Pilot to scale", {"color": CYAN})]], size=14, track=300,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, band + 0.58, 12.4, 0.22, "Durations are agreed in discovery. Care-team changes for the Network "
            "Services team start once the AI agents are ready.", size=8.5, color="8C8C8C", anchor=MSO_ANCHOR.MIDDLE)
    ly = band + 1.7
    gbar(cv, 0, ly, 13.333, 0.04, 0)
    n = len(PHASES)
    x0, x1 = 0.7, 12.6
    for k, (t, d) in enumerate(PHASES):
        xx = x0 + (x1 - x0) * k / (n - 1)
        up = k % 2 == 0
        dy0, dy1 = (ly - 0.36, ly - 0.08) if up else (ly + 0.12, ly + 0.4)
        cv.arrow(xx, dy0, xx, dy1, "FFFFFF", 1.5, dash="sysDot", head=False)
        cv.rect(xx - 0.08, ly - 0.06, 0.16, 0.16, "FFFFFF", None, shape=MSO_SHAPE.OVAL)
        tw = 2.4
        tx = xx - 0.05 if k < n - 1 else xx - tw + 0.05
        ty = ly - 0.95 if up else ly + 0.45
        cv.text(tx, ty, tw, 0.55, [[(t, {"color": "FFFFFF"})], [(d, {"color": "B3B3B3", "size": 9.5})]],
                size=10.5, anchor=MSO_ANCHOR.BOTTOM if up else MSO_ANCHOR.TOP,
                align=PP_ALIGN.RIGHT if k == n - 1 else None, after=1)
    set_notes(s, NOTES_2)
    return s


def main():
    import muted_theme as mt
    prs = Presentation(SRC)
    lst = prs.slides._sldIdLst
    for el in list(lst):
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    slide_1(prs, layout)
    slide_2(prs, layout)
    for sl in prs.slides:
        mt.min_font(sl, 7.0)
    for line in fix_footers(prs):
        print(line)
    prs.save(OUT)
    print("wrote", OUT, "-", len(prs.slides), "slides")


if __name__ == "__main__":
    main()
