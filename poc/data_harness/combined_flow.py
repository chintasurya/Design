"""One review image: the target-state 'two access paths' architecture merged with the campaign flow.

Nothing from either view is dropped. Where they differ, the final proposed solution wins: Silver keeps every
patient (consent and contact filtering move to the per-campaign eligibility service), Golden splits into Gold A
and Gold B, the release store becomes the activation gateway, the Developer Agent is the Campaign Design Agent
and the testing loop runs under the Activation Readiness Agent.

    python3 combined_flow.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import CARD, DIM, EDGE, R, SOFT, SRC, TINT, VIO, badge, new_slide, path, pill
from build_mad_ig_deck import BLACK, CYAN, GREEN, MAGENTA, WHITE, YELLOW
from final_solution import gatecard, item, side
from footer import fix_footers
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "combined_flow.pptx")


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "AGENTIC HEALTHCARE CAMPAIGN PLATFORM · END TO END (FOR REVIEW)",
                "From governed data to a tested, approved campaign: two access paths",
                "Proposed target state. Google Cloud's restricted path on the left, the analytical path on the "
                "right. Patient-level data leaves only through the gateway, after tests and approvals.")
    zt, zb = 1.28, 6.12
    rows = [1.47 + k * 0.78 for k in range(6)]
    rh = 0.66

    def mid(k):
        return rows[k] + rh / 2
    # ---------------------------------------------------------------- left: restricted (Google Cloud)
    cv.rect(0.45, zt, 6.05, zb - zt, BLACK, MAGENTA, 1.0, R, 0.02)
    side(cv, 0.45, zt, zb - zt, "RESTRICTED · DATA + GOVERNANCE", MAGENTA, "googlecloud")
    ex, ew = 0.85, 2.8          # release + send, top-down
    dx, dw = 3.85, 2.55         # governed data, bottom-up
    cv.text(ex, 1.3, ew, 0.16, "RELEASE + SEND · ONLY AFTER G2 + G3  ↓", size=5.2, bold=True, color=YELLOW,
            track=100, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(dx, 1.3, dw, 0.16, "GOVERN THE DATA  ↑", size=5.2, bold=True, color=MAGENTA, track=100,
            anchor=MSO_ANCHOR.MIDDLE)
    data = [("Measurement service", "Protected attribution vs a holdout; aggregates refresh Gold A and the graph.",
             MAGENTA, CARD, None),
            ("Gold B · eligibility", "Identity-linked eligibility inputs. Services only.", YELLOW, CARD, None),
            ("Silver", "Identities, encounters, contacts, consent evidence. Keeps everyone.", SOFT, CARD, None),
            ("DLP + Collibra", "DLP classifies, the Collibra steward approves, policy tags mask PHI.", MAGENTA,
             TINT[MAGENTA], None),
            ("Bronze", "Approved raw extracts with lineage. Restricted access.", "A0703C", CARD, None),
            ("Sources", "Epic, athenahealth, ADSI, Strata, SFDC, SFMC engagement. Engagement from 13 returns "
             "here for the next run.", EDGE, CARD, "googlecloud")]
    for k, (t, d, ln, fl, ic) in enumerate(data):
        item(cv, dx, rows[k], dw, rh, t, d, line=ln, fill=fl, icon=ic, bsize=5.4, tsize=6.4)
    for k in range(5, 1, -1):                      # Sources -> Bronze -> DLP -> Silver -> Gold B
        cv.arrow(dx + dw / 2, rows[k], dx + dw / 2, rows[k - 1] + rh, WHITE, 1.25)
    # release + send
    item(cv, ex, rows[0], ew, rh, "Eligibility service", "Approved rules per campaign: no consent, no phone or "
         "email, STOP, deceased, duplicates excluded, with reasons.", line=MAGENTA, n=7, ncolor=MAGENTA,
         bsize=5.3, tsize=6.4)
    gatecard(cv, ex, rows[1], ew, rh, "G2", "Pre-send review", "SME + tech lead review a masked report: counts, "
             "consent, exclusions. No PHI on screen.", n=8, bsize=5.4)
    fx, fy, fw, fh = cv.frame(ex, rows[2], ew, rh, BLACK, 0.04)
    badge(cv, fx + 0.05, fy + 0.04, 9, YELLOW, 0.2)
    cv.text(fx + 0.3, fy + 0.01, fw - 0.34, 0.24, "Policy engine + activation gateway", size=6.4, bold=True,
            color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.08, fy + 0.26, fw - 0.14, fh - 0.27, "Takes approved purpose + rules from G1-G3; eligibility, consent, "
            "suppression, minimum fields. Compliance Passport; time-limited; no agent access.", size=5.2,
            color=SOFT)
    hw = (ew - 0.1) / 2
    item(cv, ex, rows[3], hw, rh, "A · via Data Cloud", "Data Cloud → Marketing Cloud.", line=CYAN, n=10,
         icon="salesforce", bsize=5.2, tsize=5.8)
    item(cv, ex + hw + 0.1, rows[3], hw, rh, "B · direct pull", "Automation Studio, read-only.", line=CYAN,
         dash="dash", bsize=5.2, tsize=5.8)
    item(cv, ex, rows[4], ew, rh, "Data extension", "Approved records for this run only.", n=11, icon="salesforce",
         bsize=5.4, tsize=6.4)
    item(cv, ex, rows[5], hw, rh, "Journey starts", "Built in 4, tested in 5, approved in 6.", n=12, bsize=5.2,
         tsize=5.8)
    item(cv, ex + hw + 0.1, rows[5], hw, rh, "Send-time check", "Consent, STOP, caps re-checked; SMS or email.",
         line=MAGENTA, fill=TINT[MAGENTA], n=13, ncolor=MAGENTA, bsize=5.2, tsize=5.8)
    for k in (0, 1, 2):
        cv.arrow(ex + ew / 2, rows[k] + rh, ex + ew / 2, rows[k + 1], WHITE, 1.25)
    for x in (ex + hw / 2, ex + hw + 0.1 + hw / 2):
        cv.arrow(x, rows[3] + rh, x, rows[4], WHITE, 1.0)
    cv.arrow(ex + hw / 2, rows[4] + rh, ex + hw / 2, rows[5], WHITE, 1.25)
    cv.arrow(ex + hw, mid(5), ex + hw + 0.1, mid(5), WHITE, 1.25)
    # Gold B -> eligibility, in the gap between the two columns
    gx = (ex + ew + dx) / 2
    path(cv, [(dx, mid(1)), (gx, mid(1)), (gx, mid(0)), (ex + ew, mid(0))], MAGENTA, 1.5)
    # engagement back: send-time check -> sources (same row)
    cv.arrow(ex + ew, mid(5) + 0.12, dx, mid(5) + 0.12, GREEN, 1.5)
    # ---------------------------------------------------------------- trust boundary (vertical)
    bxl = 6.62
    cv.arrow(bxl, zt, bxl, zb, MAGENTA, 1.25, dash="dash", head=False)
    for y0, y1, t in ((1.36, 2.86, "RECOMMENDATION ≠ RELEASE"), (4.4, 6.0, "AGENTS: NO RAW-PHI ACCESS")):
        cv.rect(bxl - 0.1, y0, 0.2, y1 - y0, MAGENTA, None, shape=R, radius=0.5)
        tb = cv.text(bxl - (y1 - y0) / 2, (y0 + y1) / 2 - 0.1, y1 - y0, 0.2, t, size=4.8, bold=True, color=WHITE,
                     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=80)
        tb.rotation = 270
    # ---------------------------------------------------------------- right: analytical
    ax0 = 6.74
    cv.rect(ax0, zt, 12.88 - ax0, zb - zt, TINT[VIO], VIO, 1.0, R, 0.02)
    side(cv, 12.58, zt, zb - zt, "ANALYTICAL · AI PROPOSES", VIO, "harness")
    px, pw = 6.86, 2.69
    bx, bw = 9.7, 2.75
    cv.text(px, 1.3, pw, 0.16, "PLAN ON MASKED DATA", size=5.2, bold=True, color=VIO, track=100,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(bx, 1.3, bw, 0.16, "BUILD + TEST BEFORE ANY PATIENT DATA", size=5.2, bold=True, color=CYAN,
            track=100, anchor=MSO_ANCHOR.MIDDLE)
    item(cv, px, rows[0], pw, rh, "Build the campaign in Codex", "“Build a post-discharge follow-up campaign for "
         "heart patients”, or the business console.", line=CYAN, n=1, icon="openai-white", bsize=5.3, tsize=6.4)
    item(cv, px, rows[1], pw, rh, "Orchestrator · Strategist · Analytics", "Fetch from the graph and Gold A; size "
         "the audience as counts.", line=VIO, n=2, ncolor=VIO, bsize=5.4, tsize=6.2)
    gatecard(cv, px, rows[2], pw, rh, "G1", "Confirm brief", "Marketer + clinical approve the Campaign Opportunity "
             "Brief: audience size, channel, content plan. Counts only.", n=3, bsize=5.2)
    item(cv, px, rows[3], pw, rh, "Gold A · intelligence", "Protected aggregates only. Cohorts, e.g. Heart · "
         "Maternity · General · more.", line=YELLOW, icon="googlebigquery", bsize=5.3, tsize=6.4)
    hw2 = (pw - 0.1) / 2
    item(cv, px, rows[4], hw2, rh, "Knowledge graph", "Metadata, rules, lineage. No patients.", line=VIO,
         icon="googlecloudspanner", bsize=5.2, tsize=5.8)
    item(cv, px + hw2 + 0.1, rows[4], hw2, rh, "Tableau", "Masked dashboards only.", icon="tableau", bsize=5.2,
         tsize=5.8)
    item(cv, px, rows[5], hw2, rh, "Compliance Guardian", "Explains exclusions for 8; cannot override.", line=VIO,
         bsize=5.2, tsize=5.8)
    item(cv, px + hw2 + 0.1, rows[5], hw2, rh, "Measurement Agent", "Aggregated outcomes, forecasts, tests.",
         line=VIO, bsize=5.2, tsize=5.8)
    cv.arrow(px + pw / 2, rows[0] + rh, px + pw / 2, rows[1], WHITE, 1.25)
    cv.arrow(px + pw / 2, rows[1] + rh, px + pw / 2, rows[2], VIO, 1.25)
    # DLP + Collibra -> Gold A across the boundary
    cv.arrow(dx + dw, mid(3), px, mid(3), YELLOW, 1.5)
    # build + test
    item(cv, bx, rows[0], bw, rh, "Campaign build", "Invokes Journey Builder (native).", icon="salesforce",
         bsize=5.4, tsize=6.4)
    item(cv, bx, rows[1], bw, rh, "Campaign Design Agent", "Builds the journey and data extension from approved "
         "templates, paused; seeds known risks.", line=VIO, n=4, ncolor=VIO, bsize=5.3, tsize=6.4)
    ty, th = rows[2], rows[3] + rh - rows[2]
    cv.rect(bx, ty, bw, th, "0B2418", GREEN, 1.0, R, 0.04)
    badge(cv, bx + 0.07, ty + 0.05, 5, GREEN, 0.2)
    cv.text(bx + 0.32, ty + 0.02, bw - 0.4, 0.24, "Activation Readiness · testing", size=6.4, bold=True,
            color=GREEN, anchor=MSO_ANCHOR.MIDDLE)
    chips = [("Test cases: test contacts only", EDGE), ("Failure modes: consent, STOP, links, quiet hours", MAGENTA),
             ("Classify + report each failure", EDGE)]
    for k, (t, c) in enumerate(chips):
        y = ty + 0.32 + k * 0.33
        cv.rect(bx + 0.1, y, bw - 0.2, 0.25, CARD, c, 0.75, R, 0.25)
        cv.text(bx + 0.1, y, bw - 0.2, 0.25, t, size=5.4, color=MAGENTA if k == 1 else WHITE,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if k < 2:
            cv.arrow(bx + bw / 2, y + 0.25, bx + bw / 2, y + 0.33, SOFT, 1.0)
    cv.text(bx + 0.1, ty + th - 0.2, bw - 0.2, 0.18, "failed → back to 4 · max 5, then an owner", size=5.3,
            bold=True, color=MAGENTA, anchor=MSO_ANCHOR.MIDDLE)
    gatecard(cv, bx, rows[4], bw, rh, "G3", "Approve journey + content", "Clinical + compliance, when every test "
             "passes. The journey then waits, active.", n=6, bsize=5.3)
    gatecard(cv, bx, rows[5], bw, rh, "G1-3", "People approve", "Product, clinical, privacy, security: purpose, "
             "audience rules and release.", bsize=5.3)
    cv.arrow(bx + bw / 2, rows[0] + rh, bx + bw / 2, rows[1], WHITE, 1.25)
    cv.arrow(bx + bw / 2 + 0.3, rows[1] + rh, bx + bw / 2 + 0.3, ty, WHITE, 1.25)
    cv.arrow(bx + bw / 2 - 0.3, ty, bx + bw / 2 - 0.3, rows[1] + rh, MAGENTA, 1.5)
    cv.arrow(bx + bw / 2, ty + th, bx + bw / 2, rows[4], WHITE, 1.25)
    # G1 -> campaign build
    gc = (px + pw + bx) / 2
    path(cv, [(px + pw, mid(2)), (gc, mid(2)), (gc, mid(0)), (bx, mid(0))], YELLOW, 1.5)
    # ---------------------------------------------------------------- safeguards
    sy, sh = 6.25, 0.58
    cv.text(0.45, sy, 1.25, sh, [[("SAFEGUARDS", {"bold": True, "color": MAGENTA, "track": 120})],
                                 [("no wrong or no-consent patient", {"color": DIM, "size": 5})]], size=6.2,
            anchor=MSO_ANCHOR.MIDDLE, after=1)
    guards = ["Build and test before any data lands", "G2: masked pre-send report",
              "Minimum fields, only after G2 + G3", "Gateway release; agents hold no raw PHI",
              "Collibra steward approves masking", "Retry cap: 5, then an owner", "Send-time re-checks + feedback"]
    gw = (12.88 - 1.75 - 6 * 0.08) / 7
    for k, t in enumerate(guards):
        x = 1.75 + k * (gw + 0.08)
        cv.rect(x, sy, gw, sh, CARD, None)
        cv.rect(x, sy, 0.05, sh, MAGENTA, None)
        cv.text(x + 0.12, sy, gw - 0.16, sh, t, size=6, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    return s


def main(out=OUT):
    prs = Presentation(SRC)
    lst = prs.slides._sldIdLst
    for el in list(lst):
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    build(prs, layout)
    for line in fix_footers(prs):
        print(line)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    prs.save(out)
    print("wrote", os.path.abspath(out), "-", len(prs.slides), "slide")


if __name__ == "__main__":
    main(*sys.argv[1:])
