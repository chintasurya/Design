"""Marketing Cloud campaign timeline: ~90 days manual vs ~10-12 days on the data harness with the campaign
agents. The manual steps are the ones in the Ascension Agentic Harness deck (CHF runbook and campaign pages); the
harness figures are pilot targets. Colourful black IG style.

    python3 campaign_timeline.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import R, SRC, logo, new_slide
from build_mad_ig_deck import CYAN, MAGENTA, YELLOW, set_notes
from footer import fix_footers
from sierra_voice import CARD, EDGE, T1, T2, T3, gbar
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "campaign_timeline.pptx")
TINTS = {CYAN: "06262B", YELLOW: "2B2508", MAGENTA: "2B0716"}

MANUAL = [("Discovery & PRD", "scope, audience, KPIs, holdout design", 0, 10, True),
          ("ADSI data readiness", "BigQuery tables, mapping, EUID, consent", 10, 20, True),
          ("Data Cloud ingestion", "streams, transforms, DMOs, identity links", 20, 32, True),
          ("Segment & activation", "consent and age filters, activate to SFMC", 32, 40, True),
          ("SFMC data prep", "SQL, messaging DE, suppression", 40, 48, False),
          ("Content & legal approval", "copy, AMPscript, STOP keywords, sign-off", 48, 62, False),
          ("Journey Builder build", "entry DE, splits, CloudPages, surveys", 62, 70, False),
          ("Testing & UAT", "scenarios, seed sends, UAT sign-off", 70, 82, False),
          ("Deploy & go-live", "Data Kit, Copado, smoke test", 82, 90, False)]

HARNESS = [("Prompt → Opportunity Brief · G1", "Orchestrator, Strategist, Analytics; people approve", 0, 1, CYAN),
           ("Data ready", "governed in Gold A / B by the data harness", 0, 0, MAGENTA),
           ("Eligibility rule", "eligibility service: consent, contact, exclusions", 1, 2, CYAN),
           ("Journey + data extension build", "Campaign Design Agent, from approved templates", 2, 4, CYAN),
           ("Content & legal approval", "Design Agent drafts; legal approves", 2, 8, YELLOW),
           ("Testing on test contacts · G3", "Activation Readiness; clinical + compliance approve", 8, 10, CYAN),
           ("Pre-send review G2 + release", "SME + tech lead; activation gateway", 10, 11, YELLOW),
           ("Go live", "Marketing Cloud; consent re-checked at send", 11, 12, CYAN)]

NOTES = """SLIDE: Launching a campaign: ~90 days manual vs ~10-12 days on the data harness   (about 2 minutes)

KEY MESSAGE
About 40 of today's 90 days go on discovery, data readiness, Data Cloud ingestion and segmentation, repeated for every campaign. The data harness does that work once and keeps it fresh, so a campaign starts from ready, governed data. The campaign agents build and test; people approve; legal review sets the pace.

LEFT · TODAY
Nine steps, one after another: discovery and PRD 10 days, ADSI data readiness 10, Data Cloud ingestion 12, segmentation 8, SFMC data prep 8, content and legal 14, journey build 8, testing and UAT 12, deploy 8. The first four (magenta) are what the data harness takes off every campaign.

RIGHT · WITH THE DATA HARNESS
Day 0-1 the marketer prompts in Codex; the Orchestrator, Strategist and Analytics agents produce the Campaign Opportunity Brief and people approve it (G1). The data is already ready. Day 1-2 the eligibility service applies the campaign rule. Day 2-4 the Campaign Design Agent builds the journey and data extension while legal reviews the content (days 2-8, the longest step). Day 8-10 the Activation Readiness Agent tests on test contacts and clinical and compliance approve (G3). Day 10-11 the SME and tech lead review the masked pre-send report (G2) and the gateway releases. Day 11-12 the journey goes live, with consent re-checked at send.

BE HONEST
Content and legal approval does not shrink much; it becomes the critical path. The ~10-12 days is a pilot target, measured on the CHF campaign against today's baseline."""


def gantt(cv, x, y, w, rows, scale, row_h, label_w, kind):
    bx = x + label_w
    bw = w - label_w - 0.1
    for k, r in enumerate(rows):
        yy = y + k * row_h
        cv.rect(x, yy, w, row_h - 0.05, CARD if k % 2 == 0 else "101010", None)
        if kind == "manual":
            t, d, a, b, data = r
            col = MAGENTA if data else "5A5A5A"
        else:
            t, d, a, b, col = r
        cv.text(x + 0.1, yy, label_w - 0.14, row_h - 0.05, [[(t, {"bold": True, "color": T1})],
                                                            [(d, {"color": T2})]], size=7,
                anchor=MSO_ANCHOR.MIDDLE)
        x0 = bx + bw * a / scale
        x1 = bx + bw * b / scale
        if b > a:
            cv.rect(x0, yy + 0.09, max(x1 - x0, 0.06), row_h - 0.23, col, None, shape=R, radius=0.3)
            lab = "%dd" % (b - a)
            cv.text(x0, yy + 0.09, max(x1 - x0, 0.3), row_h - 0.23, lab, size=7, bold=True,
                    color="FFFFFE" if col in (MAGENTA, "5A5A5A") else "000000", align=PP_ALIGN.CENTER,
                    anchor=MSO_ANCHOR.MIDDLE)
        else:
            cv.rect(x0, yy + 0.09, 0.62, row_h - 0.23, None, MAGENTA, 0.9, R, 0.3)
            cv.text(x0, yy + 0.09, 0.62, row_h - 0.23, "READY", size=7, bold=True, color=MAGENTA,
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return bx, bw


def axis(cv, bx, bw, y, ticks, scale):
    for t in ticks:
        xx = bx + bw * t / scale
        cv.text(xx - 0.3, y, 0.6, 0.16, "Day %d" % t, size=7, color=T3, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · NUDGE POD · DATA HARNESS + MARKETING CLOUD",
                "Launching a campaign: ~90 days manual vs ~10-12 days on the data harness",
                "Data readiness, ingestion and segmentation are done once by the data harness, not per campaign. "
                "Campaign agents build and test; people approve; legal review sets the pace.")
    top, ph = 1.28, 4.36
    # ---------------------------------------------------------------- today
    lx, lw = 0.45, 6.15
    cv.rect(lx, top, lw, ph, "0A0A0A", EDGE, 0.75, R, 0.02)
    cv.text(lx + 0.14, top + 0.06, 3, 0.2, "TODAY · MANUAL DELIVERY", size=7, bold=True, color=T2, track=120,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(lx + 0.14, top + 0.26, 2, 0.42, "~90 days", size=20, color=T1, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(lx + 2.0, top + 0.26, lw - 2.14, 0.42, [[("9 steps in sequence. ", {"color": T2}),
                                                    ("~40 days", {"bold": True, "color": MAGENTA}),
                                                    (" of data and segmentation work, repeated for every campaign",
                                                     {"color": T2})]], size=7, anchor=MSO_ANCHOR.MIDDLE)
    rh = 0.35
    gy = top + 0.98
    bx, bw = gantt(cv, lx + 0.1, gy, lw - 0.2, MANUAL, 90, rh, 2.3, "manual")
    axis(cv, bx, bw, gy - 0.22, (0, 30, 60, 90), 90)
    # bracket for the data steps
    by0, by1 = gy, gy + 4 * rh - 0.05
    cv.rect(lx + 0.03, by0, 0.04, by1 - by0, MAGENTA, None)
    # ---------------------------------------------------------------- with the data harness
    rx = lx + lw + 0.14
    rw = 12.88 - rx
    fx, fy, fw, fh = cv.frame(rx, top, rw, ph, "0A0A0A", 0.02)
    cv.text(fx + 0.14, fy + 0.04, 4, 0.2, "WITH THE DATA HARNESS + CAMPAIGN AGENTS", size=7, bold=True,
            color=CYAN, track=120, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.14, fy + 0.24, 2.2, 0.42, "~10-12 days", size=20, color=CYAN, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 2.3, fy + 0.28, fw - 2.44, 0.36, "data already governed and ready; build runs alongside legal "
            "review", size=7, color=T2, anchor=MSO_ANCHOR.MIDDLE)
    rh2 = 0.34
    gy2 = top + 0.98
    bx2, bw2 = gantt(cv, rx + 0.1, gy2, rw - 0.2, HARNESS, 12, rh2, 2.5, "harness")
    axis(cv, bx2, bw2, gy2 - 0.22, (0, 4, 8, 12), 12)
    cv.text(fx + 0.14, gy2 + 8 * rh2 + 0.06, fw - 0.28, 0.42, [[("Legal review is now the critical path. ",
                                                                 {"bold": True, "color": YELLOW}),
                                                                ("Yellow: people approve (G1, legal, G2). Cyan: "
                                                                 "agents and services.", {"color": T2})]], size=7,
            anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- results
    sy, sh = top + ph + 0.12, 0.74
    stats = [("~87%", "faster to launch", "90 to ~10-12 days"),
             ("0 days", "data preparation per campaign", "the data harness keeps it ready"),
             ("7", "campaign agents", "the same for every Marketing Cloud pod"),
             ("3 gates", "people still approve", "G1 brief, G3 journey, G2 pre-send")]
    w = (12.43 - 3 * 0.12) / 4
    for k, (b, t, d) in enumerate(stats):
        x = 0.45 + k * (w + 0.12)
        cv.rect(x, sy, w, sh, CARD, None)
        gbar(cv, x, sy, 0.05, sh)
        cv.text(x + 0.18, sy, 1.2, sh, b, size=18, color=(CYAN, MAGENTA, T1, YELLOW)[k], anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 1.4, sy, w - 1.5, sh, [[(t, {"bold": True, "color": T1})], [(d, {"color": T2})]], size=7,
                anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, sy + sh + 0.04, 12.43, 0.2, "Today: CHF post-discharge nudge manual steps and SFMC standards, as "
            "in the Agentic Harness deck. With the data harness: pilot targets, measured on the CHF campaign against "
            "today's baseline.", size=7, color=T3, anchor=MSO_ANCHOR.MIDDLE)
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
