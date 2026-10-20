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
                "Proposed target state. Agents plan and build on masked or aggregated data; patient-level data stays "
                "on the restricted path and leaves only through the gateway, after tests and approvals.")
    # ---------------------------------------------------------------- analytical zone
    zy, zh = 1.3, 2.3
    cv.rect(0.45, zy, 12.43, zh, TINT[VIO], VIO, 1.0, R, 0.03)
    side(cv, 0.45, zy, zh, "ANALYTICAL · AI PROPOSES", VIO, "harness")
    r1, h1 = 1.52, 0.62
    r2, h2 = 2.2, 0.6
    r3, h3 = 2.86, 0.62
    for x, t, c in ((0.85, "PLAN ON MASKED DATA", VIO), (5.4, "BUILD + TEST BEFORE ANY PATIENT DATA", CYAN),
                    (9.9, "OVERSIGHT", YELLOW)):
        cv.text(x, 1.32, 4.3, 0.18, t, size=5.6, bold=True, color=c, track=120, anchor=MSO_ANCHOR.MIDDLE)
    # plan
    lx, lw, rx, rw = 0.85, 2.5, 3.47, 1.77
    item(cv, lx, r1, lw, h1, "Build the campaign in Codex", "“Build a post-discharge follow-up campaign for heart "
         "patients”, or the business console.", line=CYAN, n=1, icon="openai-white", bsize=5.6, tsize=6.6)
    item(cv, lx, r2, lw, h2, "Orchestrator · Strategist · Analytics", "Fetch from the graph and Gold A; size the "
         "audience as counts.", line=VIO, n=2, ncolor=VIO, bsize=5.6, tsize=6.4)
    gw_ = (lw - 0.06) / 2
    item(cv, lx, r3, gw_, h3, "Knowledge graph", "Metadata, rules, lineage. Not a patient store.", line=VIO,
         icon="googlecloudspanner", bsize=5.4, tsize=6.2)
    item(cv, lx + gw_ + 0.06, r3, gw_, h3, "Tableau", "Masked dashboards only.", line=EDGE, icon="tableau",
         bsize=5.4, tsize=6.2)
    gatecard(cv, rx, r1, rw, r2 + h2 - r1, "G1", "Confirm brief", "Marketer and clinical approve the Campaign "
             "Opportunity Brief: audience size, channel, content plan. Counts only.", n=3, bsize=5.6)
    item(cv, rx, r3, rw, h3, "Gold A · intelligence", "Aggregate cohorts, e.g. Heart · Maternity · General · more.",
         line=YELLOW, icon="googlebigquery", bsize=5.4, tsize=6.2)
    cv.arrow(lx + 0.7, r1 + h1, lx + 0.7, r2, WHITE, 1.25)
    cv.arrow(lx + 0.5, r2 + h2, lx + 0.5, r3, VIO, 1.25)
    cv.arrow(lx + 0.7, r3, lx + 0.7, r2 + h2, VIO, 1.25)
    cv.arrow(lx + lw, r2 + h2 / 2, rx, r2 + h2 / 2, VIO, 1.25)
    cv.arrow(rx + rw, r1 + 0.31, 5.4, r1 + 0.31, YELLOW, 1.5)
    # build + test
    bx, bw = 5.4, 4.35
    item(cv, bx, r1, 1.45, h1, "Campaign build", "Invokes Journey Builder (native).", icon="salesforce",
         bsize=5.6, tsize=6.4)
    dx = bx + 1.57
    item(cv, dx, r1, bx + bw - dx, h1, "Campaign Design Agent", "Builds the journey and data extension from "
         "approved templates, paused; seeds known risks.", line=VIO, n=4, ncolor=VIO, bsize=5.6, tsize=6.4)
    cv.arrow(bx + 1.45, r1 + h1 / 2, dx, r1 + h1 / 2, WHITE, 1.25)
    cv.rect(bx, r2, bw, h2, "0B2418", GREEN, 1.0, R, 0.06)
    badge(cv, bx + 0.07, r2 + 0.05, 5, GREEN, 0.2)
    cv.text(bx + 0.32, r2 + 0.02, 2.4, 0.24, "Activation Readiness · testing", size=6.4, bold=True, color=GREEN,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(bx + 2.3, r2 + 0.02, bw - 2.38, 0.24, "failed → 4 · max 5, then an owner", size=5.4, bold=True,
            color=MAGENTA, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    chips = [("Test cases: test contacts only", EDGE), ("Failure modes: consent, STOP, links, hours", MAGENTA),
             ("Classify + report", EDGE)]
    cw = (bw - 0.16 - 2 * 0.14) / 3
    for k, (t, c) in enumerate(chips):
        x = bx + 0.08 + k * (cw + 0.14)
        cv.rect(x, r2 + 0.3, cw, 0.25, CARD, c, 0.75, R, 0.25)
        cv.text(x, r2 + 0.3, cw, 0.25, t, size=5.2, color=MAGENTA if k == 1 else WHITE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        if k < 2:
            cv.arrow(x + cw, r2 + 0.425, x + cw + 0.14, r2 + 0.425, SOFT, 1.0)
    cv.arrow(dx + 1.6, r1 + h1, dx + 1.6, r2, WHITE, 1.25)
    cv.arrow(dx + 0.6, r2, dx + 0.6, r1 + h1, MAGENTA, 1.5)
    gatecard(cv, bx, r3, bw, h3, "G3", "Approve the journey + content", "Clinical and compliance, only when every "
             "test passes. The journey then waits, active, for entries.", n=6, bsize=5.6)
    cv.arrow(bx + bw / 2, r2 + h2, bx + bw / 2, r3, WHITE, 1.25)
    # oversight
    ox, ow = 9.9, 2.9
    item(cv, ox, r1, ow, h1, "Compliance Guardian", "Explains exclusions, assembles evidence for 8. Cannot override "
         "policy or see raw PHI.", line=VIO, icon="harness", bsize=5.6, tsize=6.4)
    item(cv, ox, r2, ow, h2, "Measurement Agent", "Aggregated outcomes, forecasts and experiment results.",
         line=VIO, icon="harness", bsize=5.6, tsize=6.4)
    gatecard(cv, ox, r3, ow, h3, "G1-3", "People approve", "Product, clinical, privacy, security: purpose, "
             "audience rules and release.", bsize=5.6)
    # ---------------------------------------------------------------- trust boundary
    by = 3.71
    cv.arrow(0.45, by, 12.88, by, MAGENTA, 1.25, dash="dash", head=False)
    pill(cv, 0.8, by - 0.09, 3.45, "AGENTS: NO RAW-PHI PERMISSION · RECOMMENDATION ≠ RELEASE", MAGENTA, True,
         h=0.18, size=5, tcolor=WHITE)
    # ---------------------------------------------------------------- restricted zone
    ry, rh = 3.89, 2.33
    cv.rect(0.45, ry, 12.43, rh, BLACK, MAGENTA, 1.0, R, 0.03)
    side(cv, 0.45, ry, rh, "RESTRICTED · DATA + GOVERNANCE", MAGENTA, "googlecloud")
    ay, ah = 3.97, 0.78
    rowa = [("Sources", "Epic, athenahealth, ADSI, Strata, SFDC, SFMC engagement. Approved datasets only.",
             EDGE, CARD, "googlecloud", 1.25),
            ("Bronze", "Approved raw extracts with lineage. Restricted access.", "A0703C", CARD, None, 1.3),
            ("DLP + Collibra", "DLP classifies, the Collibra steward approves, policy tags mask PHI.", MAGENTA,
             TINT[MAGENTA], None, 1.95),
            ("Silver", "Identities, encounters, contacts, consent evidence. Keeps everyone.", SOFT, CARD, None, 1.75),
            ("Gold B · eligibility", "Identity-linked eligibility inputs. Services only.", YELLOW, CARD, None, 1.6)]
    x = 0.85
    pos = {}
    for t, d, ln, fl, ic, w in rowa:
        item(cv, x, ay, w, ah, t, d, line=ln, fill=fl, icon=ic, bsize=5.5, tsize=6.4)
        pos[t] = (x, w)
        x += w + 0.12
    mx = x + 0.12
    item(cv, mx, ay, 12.8 - mx, ah, "Measurement service", "Protected attribution against a holdout; aggregates "
         "refresh Gold A and the graph.", line=MAGENTA, bsize=5.5, tsize=6.4)
    keys = [r[0] for r in rowa]
    for k1, k2 in zip(keys, keys[1:]):
        x1 = pos[k1][0] + pos[k1][1]
        cv.arrow(x1, ay + ah / 2, x1 + 0.12, ay + ah / 2, WHITE, 1.25)
    # DLP -> Gold A, across the boundary
    gx_ = rx + 0.9
    cv.arrow(gx_, ay, gx_, r3 + h3, YELLOW, 1.5)
    cv.text(gx_ + 0.08, 3.75, 1.6, 0.12, "protected aggregates only", size=5.2, color=YELLOW,
            anchor=MSO_ANCHOR.MIDDLE)
    # release + send
    by_, bh = 5.02, 1.0
    bx_ = [0.85]
    widths = [1.85, 1.6, 2.3, 1.55, 1.25, 1.3]
    for w in widths:
        bx_.append(bx_[-1] + w + 0.12)
    sw_last = 12.8 - bx_[-1]
    item(cv, bx_[0], by_, widths[0], bh, "Eligibility service", "Approved rules per campaign: no consent, no phone "
         "or email, STOP, deceased, duplicates excluded, with reasons.", line=MAGENTA, n=7, ncolor=MAGENTA,
         bsize=5.4, tsize=6.4)
    gatecard(cv, bx_[1], by_, widths[1], bh, "G2", "Pre-send", "SME + tech lead review a masked report: counts, "
             "consent, exclusions. No PHI on screen.", n=8, bsize=5.4)
    fx, fy, fw, fh = cv.frame(bx_[2], by_, widths[2], bh, BLACK, 0.04)
    badge(cv, fx + 0.05, fy + 0.05, 9, YELLOW, 0.2)
    cv.text(fx + 0.3, fy + 0.02, fw - 0.34, 0.26, "Policy engine + activation gateway", size=6.4, bold=True,
            color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.08, fy + 0.3, fw - 0.14, fh - 0.32, "Purpose, eligibility, consent, suppression, minimum fields, "
            "human authorization. Compliance Passport; time-limited; no agent access.", size=5.4, color=SOFT)
    ph = (bh - 0.08) / 2
    item(cv, bx_[3], by_, widths[3], ph, "A · via Data Cloud", None, line=CYAN, icon="salesforce", tsize=5.8)
    item(cv, bx_[3], by_ + ph + 0.08, widths[3], ph, "B · direct pull", None, line=CYAN, dash="dash", tsize=5.8)
    badge(cv, bx_[3] + widths[3] - 0.24, by_ + 0.12, 10, CYAN, 0.18)
    item(cv, bx_[4], by_, widths[4], bh, "Data extension", "Approved records, this run only.", n=11,
         icon="salesforce", bsize=5.4, tsize=6.0)
    item(cv, bx_[5], by_, widths[5], bh, "Journey starts", "Built in 4, tested in 5, approved in 6.", n=12,
         bsize=5.4, tsize=6.0)
    item(cv, bx_[6], by_, sw_last, bh, "Send-time check", "Consent, STOP, frequency caps re-checked; SMS or email.",
         line=MAGENTA, fill=TINT[MAGENTA], n=13, ncolor=MAGENTA, bsize=5.4, tsize=6.0)
    mid = by_ + bh / 2
    for k in range(6):
        if k == 2:
            for yy in (by_ + ph / 2, by_ + ph + 0.08 + ph / 2):
                cv.arrow(bx_[2] + widths[2], yy, bx_[3], yy, WHITE, 1.0)
        elif k == 3:
            for yy in (by_ + ph / 2, by_ + ph + 0.08 + ph / 2):
                cv.arrow(bx_[3] + widths[3], yy, bx_[4], yy, WHITE, 1.0)
        else:
            cv.arrow(bx_[k] + widths[k], mid, bx_[k + 1], mid, WHITE, 1.25)
    # Gold B -> eligibility (channel between the rows)
    gbx, gbw = pos["Gold B · eligibility"]
    path(cv, [(gbx + 0.3, ay + ah), (gbx + 0.3, 4.81), (bx_[0] + 0.9, 4.81), (bx_[0] + 0.9, by_)], MAGENTA, 1.5)
    cv.text(bx_[0] + 1.0, 4.82, 2.2, 0.13, "eligibility inputs (restricted)", size=5, color=MAGENTA,
            anchor=MSO_ANCHOR.MIDDLE)
    # approvals -> gateway, down the corridor next to the measurement service
    cx_ = mx - 0.06
    path(cv, [(ox + 0.25, r3 + h3), (ox + 0.25, 3.62), (cx_, 3.62), (cx_, 4.94), (bx_[2] + widths[2] - 0.35, 4.94),
              (bx_[2] + widths[2] - 0.35, by_)], YELLOW, 1.5)
    cv.text(cx_ + 0.08, 3.75, 2.4, 0.12, "approved purpose + rules, no patient data", size=5.2, color=YELLOW,
            anchor=MSO_ANCHOR.MIDDLE)
    # engagement feedback
    fy_ = 6.12
    path(cv, [(bx_[6] + sw_last / 2, by_ + bh), (bx_[6] + sw_last / 2, fy_), (0.79, fy_), (0.79, ay + ah / 2),
              (0.85, ay + ah / 2)], GREEN, 1.25)
    pill(cv, 9.6, fy_ - 0.075, 2.6, "ENGAGEMENT BACK → NEXT RUN", GREEN, True, h=0.15, size=4.8)
    # ---------------------------------------------------------------- safeguards
    sy, sh = 6.32, 0.53
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
