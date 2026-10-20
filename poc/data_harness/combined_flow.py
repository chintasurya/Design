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

from build_data_harness_deck import CARD, DIM, EDGE, R, SOFT, SRC, TINT, VIO, badge, logo, new_slide, path, pill
from build_mad_ig_deck import BLACK, CYAN, GREEN, MAGENTA, WHITE, YELLOW
from final_solution import gatecard, item
from footer import fix_footers
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "combined_flow.pptx")


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "AGENTIC HEALTHCARE CAMPAIGN PLATFORM · END TO END (FOR REVIEW)",
                "From governed data to a tested, approved campaign",
                "Read left to right, top to bottom: the data is governed in Google Cloud first, then the user prompts "
                "in Codex, then approved patients are released to Marketing Cloud.")
    rows = [1.66 + k * 0.74 for k in range(6)]
    rh = 0.64
    zt, zb = 1.28, 6.08

    def mid(k):
        return rows[k] + rh / 2
    zones = [(0.45, 3.75, MAGENTA, BLACK, "1  GOVERN THE DATA IN GOOGLE CLOUD", "googlecloud", WHITE),
             (3.95, 9.3, VIO, TINT[VIO], "2  PROMPT IN CODEX, PLAN, BUILD + TEST · MASKED DATA ONLY", "harness",
              WHITE),
             (9.5, 12.88, YELLOW, BLACK, "3  RELEASE + SEND · ONLY AFTER G2 + G3", "salesforce", BLACK)]
    for k, (x0, x1, c, fill, t, ic, tc) in enumerate(zones):
        cv.rect(x0, zt, x1 - x0, zb - zt, fill, c, 1.0, R, 0.02)
        cv.rect(x0, zt, x1 - x0, 0.3, c, None)
        logo(cv, ic, x0 + 0.08, zt + 0.04, 0.22)
        cv.text(x0 + 0.36, zt, x1 - x0 - 0.42, 0.3, t, size=6.2, bold=True, color=tc, track=80,
                anchor=MSO_ANCHOR.MIDDLE)
    for bx_, y0, y1, t in ((3.85, 1.7, 3.9, "AGENTS: NO RAW-PHI ACCESS"), (9.4, 1.7, 3.9, "RECOMMENDATION ≠ RELEASE")):
        cv.arrow(bx_, zt, bx_, zb + 0.14, MAGENTA, 1.25, dash="dash", head=False)
        cv.rect(bx_ - 0.09, y0, 0.18, y1 - y0, MAGENTA, None, shape=R, radius=0.5)
        tb = cv.text(bx_ - (y1 - y0) / 2, (y0 + y1) / 2 - 0.09, y1 - y0, 0.18, t, size=4.8, bold=True,
                     color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=80)
        tb.rotation = 270
    # ---------------------------------------------------------------- 1 govern the data (top-down)
    gx, gw = 0.65, 3.0
    data = [("Sources", "Epic, athenahealth, ADSI, Strata, SFDC, SFMC engagement. Approved datasets only.", EDGE,
             CARD, "googlecloud"),
            ("Bronze", "Approved raw extracts with lineage and timestamps. Restricted access.", "A0703C", CARD, None),
            ("DLP + Collibra", "DLP classifies, the Collibra steward approves, policy tags mask PHI.", MAGENTA,
             TINT[MAGENTA], None),
            ("Silver", "Validated identities, encounters, contacts, consent evidence. Keeps everyone.", SOFT, CARD,
             None),
            ("Gold A · intelligence", "Protected aggregates for agents: cohorts e.g. Heart · Maternity · General · "
             "more.", YELLOW, CARD, "googlebigquery"),
            ("Gold B · eligibility", "Identity-linked eligibility inputs. Restricted services only.", YELLOW, CARD,
             None)]
    for k, (t, d, ln, fl, ic) in enumerate(data):
        item(cv, gx, rows[k], gw, rh, t, d, line=ln, fill=fl, icon=ic, n=k + 1, ncolor=MAGENTA if k < 4 else YELLOW,
             bsize=5.4, tsize=6.4)
    for k in range(4):
        cv.arrow(gx + gw / 2, rows[k] + rh, gx + gw / 2, rows[k + 1], WHITE, 1.25)
    path(cv, [(gx, mid(3)), (0.55, mid(3)), (0.55, mid(5)), (gx, mid(5))], MAGENTA, 1.25)
    # ---------------------------------------------------------------- 2 prompt, plan, build + test
    mx, mw = 4.1, 2.9
    sx, sw = 7.12, 2.08
    item(cv, mx, rows[0], mw, rh, "Prompt in Codex", "“Build a post-discharge follow-up campaign for heart "
         "patients”. Or the business console.", line=CYAN, n=7, icon="openai-white", bsize=5.3, tsize=6.4)
    item(cv, mx, rows[1], mw, rh, "Orchestrator · Strategist · Analytics", "Read the graph and Gold A; size the "
         "audience as counts.", line=VIO, n=8, ncolor=VIO, bsize=5.4, tsize=6.2)
    gatecard(cv, mx, rows[2], mw, rh, "G1", "Confirm the brief", "Marketer + clinical approve the Campaign "
             "Opportunity Brief: size, channel, content plan.", n=9, bsize=5.2)
    item(cv, mx, rows[3], mw, rh, "Campaign Design Agent", "Invokes Journey Builder (native); builds the journey "
         "and data extension, paused; seeds known risks.", line=VIO, n=10, ncolor=VIO, bsize=5.2, tsize=6.4)
    cv.rect(mx, rows[4], mw, rh, "0B2418", GREEN, 1.0, R, 0.07)
    badge(cv, mx + 0.08, rows[4] + 0.06, 11, GREEN, 0.22)
    cv.text(mx + 0.36, rows[4] + 0.04, mw - 0.4, 0.22, "Activation Readiness · testing", size=6.4, bold=True,
            color=GREEN, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(mx + 0.1, rows[4] + 0.28, mw - 0.16, rh - 0.3, [[("Test contacts only → failure modes (consent, STOP, "
                                                             "links, quiet hours) → classify + report. ", {}),
                                                            ("Failed → 10, max 5, then an owner.",
                                                             {"bold": True, "color": MAGENTA})]], size=5.2,
            color=SOFT)
    gatecard(cv, mx, rows[5], mw, rh, "G3", "Approve journey + content", "Clinical + compliance, when every test "
             "passes. The journey then waits, active.", n=12, bsize=5.2)
    for k in range(5):
        xo = mx + mw / 2 + (0.35 if k == 3 else 0)
        cv.arrow(xo, rows[k] + rh, xo, rows[k + 1], WHITE, 1.25)
    cv.arrow(mx + mw / 2 - 0.35, rows[4], mx + mw / 2 - 0.35, rows[3] + rh, MAGENTA, 1.5)
    # Gold A -> agents, across the boundary
    path(cv, [(gx + gw, mid(4)), (4.02, mid(4)), (4.02, mid(1)), (mx, mid(1))], YELLOW, 1.5)
    # shared context + oversight
    item(cv, sx, rows[0], sw, rh, "Knowledge graph", "Metadata, rules, lineage. No patients.", line=VIO,
         icon="googlecloudspanner", bsize=5.2, tsize=6.0)
    item(cv, sx, rows[1], sw, rh, "Tableau", "Masked dashboards only.", icon="tableau", bsize=5.2, tsize=6.0)
    item(cv, sx, rows[2], sw, rh, "Compliance Guardian", "Explains exclusions for 14; cannot override policy.",
         line=VIO, bsize=5.2, tsize=6.0)
    item(cv, sx, rows[3], sw, rh, "Measurement Agent", "Aggregated outcomes, forecasts, experiments.", line=VIO,
         bsize=5.2, tsize=6.0)
    gatecard(cv, sx, rows[4], sw, rows[5] + rh - rows[4], "G1-3", "People approve", "Product, clinical, privacy, "
             "security: purpose, audience rules and release. Their approvals go to the gateway (15).", bsize=5.3)
    # ---------------------------------------------------------------- 3 release + send (top-down)
    rx, rw = 9.66, 3.14
    item(cv, rx, rows[0], rw, rh, "Eligibility service", "Gold B + approved rules: no consent, no phone or email, "
         "STOP, deceased, duplicates excluded, with reasons.", line=MAGENTA, n=13, ncolor=MAGENTA, bsize=5.2,
         tsize=6.4)
    gatecard(cv, rx, rows[1], rw, rh, "G2", "Pre-send review", "SME + tech lead review a masked report: counts, "
             "consent, exclusions. No PHI on screen.", n=14, bsize=5.2)
    fx, fy, fw, fh = cv.frame(rx, rows[2], rw, rh, BLACK, 0.04)
    badge(cv, fx + 0.05, fy + 0.04, 15, YELLOW, 0.2)
    cv.text(fx + 0.3, fy + 0.01, fw - 0.34, 0.22, "Policy engine + activation gateway", size=6.4, bold=True,
            color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.08, fy + 0.24, fw - 0.14, fh - 0.25, "Purpose, consent, suppression, minimum fields, human "
            "authorization. Compliance Passport; time-limited; no agent access.", size=5.2, color=SOFT)
    hw = (rw - 0.1) / 2
    item(cv, rx, rows[3], hw, rh, "A · via Data Cloud", "Data Cloud → Marketing Cloud.", line=CYAN, n=16,
         icon="salesforce", bsize=5.2, tsize=5.8)
    item(cv, rx + hw + 0.1, rows[3], hw, rh, "B · direct pull", "Automation Studio, read-only.", line=CYAN,
         dash="dash", bsize=5.2, tsize=5.8)
    item(cv, rx, rows[4], hw, rh, "Data extension", "Approved records, this run only.", n=17, icon="salesforce",
         bsize=5.2, tsize=5.8)
    item(cv, rx + hw + 0.1, rows[4], hw, rh, "Journey starts", "Built in 10, tested in 11, approved in 12.", n=18,
         bsize=5.2, tsize=5.8)
    item(cv, rx + hw + 0.1, rows[5], hw, rh, "Send-time check", "Consent, STOP, caps re-checked. Engagement back "
         "to 2.", line=MAGENTA, fill=TINT[MAGENTA], n=19, ncolor=MAGENTA, bsize=5.2, tsize=5.8)
    item(cv, rx, rows[5], hw, rh, "Measurement service", "Protected attribution; aggregates refresh 5.",
         line=MAGENTA, n=20, ncolor=MAGENTA, bsize=5.2, tsize=5.6)
    for k in (0, 1, 2):
        cv.arrow(rx + rw / 2, rows[k] + rh, rx + rw / 2, rows[k + 1], WHITE, 1.25)
    for x in (rx + hw / 2, rx + hw + 0.1 + hw / 2):
        cv.arrow(x, rows[3] + rh, x, rows[4], WHITE, 1.0)
    cv.arrow(rx + hw, mid(4), rx + hw + 0.1, mid(4), WHITE, 1.25)
    cv.arrow(rx + hw + 0.1 + hw / 2, rows[4] + rh, rx + hw + 0.1 + hw / 2, rows[5], WHITE, 1.25)
    cv.arrow(rx + hw + 0.1, mid(5), rx + hw, mid(5), WHITE, 1.25)
    # Gold B -> eligibility, along the bottom channel
    path(cv, [(gx + 1.5, rows[5] + rh), (gx + 1.5, 6.16), (9.57, 6.16), (9.57, mid(0)), (rx, mid(0))], MAGENTA,
         1.5)
    # ---------------------------------------------------------------- safeguards
    sy, sh = 6.28, 0.56
    cv.text(0.45, sy, 1.25, sh, [[("SAFEGUARDS", {"bold": True, "color": MAGENTA, "track": 120})],
                                 [("no wrong or no-consent patient", {"color": DIM, "size": 5})]], size=6.2,
            anchor=MSO_ANCHOR.MIDDLE, after=1)
    guards = ["Build and test before any data lands", "G2: masked pre-send report",
              "Minimum fields, only after G2 + G3", "Gateway release; agents hold no raw PHI",
              "Collibra steward approves masking", "Retry cap: 5, then an owner", "Send-time re-checks + feedback"]
    gw_ = (12.88 - 1.75 - 6 * 0.08) / 7
    for k, t in enumerate(guards):
        x = 1.75 + k * (gw_ + 0.08)
        cv.rect(x, sy, gw_, sh, CARD, None)
        cv.rect(x, sy, 0.05, sh, MAGENTA, None)
        cv.text(x + 0.12, sy, gw_ - 0.16, sh, t, size=6, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
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
