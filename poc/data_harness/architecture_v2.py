"""Preview: the revised campaign architecture in two slides.

A  Codex is the single interface: the governed data layer (slide 7's first layer), the semantic layer and knowledge
   graph on Gold A, Codex in the middle, and the Cohort Resolution and Activation engines on Gold B.
B  Gold B: the restricted patient layer, what is in it, who can read it and what we do with it.

    python3 architecture_v2.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import R, SRC, new_slide
from build_mad_ig_deck import BLACK, CYAN, MAGENTA, YELLOW, set_notes
from footer import fix_footers
from sierra_voice import CARD, EDGE, T1, T2, T3, gbar
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "architecture_v2.pptx")
TINTS = {CYAN: "06262B", YELLOW: "2B2508", MAGENTA: "2B0716", EDGE: CARD}
ON = "FFFFFE"


def chip(cv, x, y, w, h, title, body, color, tsize=7.5):
    cv.rect(x, y, w, h, TINTS[color], color, 0.9, R, 0.08)
    cv.text(x + 0.08, y + 0.04, w - 0.14, h - 0.08, [[(title, {"bold": True, "color": T1, "size": tsize})],
                                                     [(body, {"color": T2})]], size=7, anchor=MSO_ANCHOR.MIDDLE,
            after=1, line=0.92)


def row(cv, x, y, w, h, n, title, body, color):
    cv.rect(x, y, w, h, CARD, None)
    cv.rect(x, y, 0.05, h, color, None)
    cv.text(x + 0.14, y, w - 0.2, h, [[(n + "  " if n else "", {"bold": True, "color": color}),
                                       (title, {"bold": True, "color": T1}), ("  " + body, {"color": T2})]],
            size=7, anchor=MSO_ANCHOR.MIDDLE, line=0.92)


def head_bar(cv, x, y, w, t, color, sub=""):
    cv.rect(x, y, w, 0.28, color, None)
    cv.text(x + 0.12, y, w - 0.24, 0.28, [[(t, {"bold": True, "track": 120}), ("   " + sub, {})] if sub else
                                          [(t, {"bold": True, "track": 120})]], size=7,
            color=ON if color == MAGENTA else "000000", anchor=MSO_ANCHOR.MIDDLE)


# ================================================================== A: Codex is the single interface
NOTES_A = """SLIDE: Codex is the single interface for discovery, approvals and continuous activation   (about 3 minutes)

KEY MESSAGE
The business user works in one place, Codex. The data is refreshed every day, agents decide what campaign and what cohort from definitions and counts, and engines we build in Google Cloud decide exactly which patients, push the newly eligible to Marketing Cloud every day and take out anyone who no longer qualifies, without a daily approval.

WALK IT
1 Governed intelligence, left: authoritative sources refresh daily or by streaming; a Collibra steward approves each dataset, DLP classifies the PHI and the policy tags are set before ingest; Bronze, then Silver resolves identity (EUID) and holds the consent of record; Gold A (insight, aggregates for agents) and the restricted patient layer (patients, for the engines only); the semantic layer (Kyvos or built in-house) and the Spanner knowledge graph, with no patient nodes, read Gold A.
2 Codex, middle: the goal; the cohort JSON with its refresh policy, approved at G1; the journey built and tested on test contacts, approved at G3; the first run's counts, approved at G2; then ongoing status. Approvals come from the approval service with named roles.
3 Cohort resolution and activation, right: the Cohort Resolution Engine checks the JSON and token and builds a controlled query; the patient query finds the matching patients inside the protected boundary; eligibility checks apply consent, STOP, suppression, deceased, duplicates and contactability; a summary with no PHI goes back to Codex; after G2 the Campaign Activation Engine checks the G2 token, purpose, rule version and fields and loads the Marketing Cloud data extension.
4 Continuous cohort refresh: every day the data refreshes and its freshness is checked; the refresh trigger runs after it, or skips the run if the data is stale; the incremental resolver applies the approved rule to new and changed patients and re-checks consent; delta activation adds the newly eligible and exit sync removes anyone who opted out, died or no longer qualifies. Each run's results show in Codex.
Marketing Cloud execution, bottom strip: a pseudonymous, stable contact key mapped only inside the protected boundary; records loaded by REST upsert or encrypted SFTP, with exits flagged; Journey Builder with a daily entry schedule, a re-entry rule, exit criteria and a goal, running day 1 to day 30; consent synced both ways within minutes (SMS STOP and email unsubscribes back to the consent of record, opt-outs from elsewhere into SFMC suppression); channel rules (TCPA, STOP/HELP keywords, quiet hours in the patient's time zone, CAN-SPAM, sender authentication); approved templates with no condition or PHI in subject lines, SMS text or URLs; a daily tracking extract into the restricted patient layer, with bounces updating contactability; and a dedicated business unit with SSO, retention policies, encryption and the BAA confirmed for each SFMC service used. Re-approval only when the cohort logic, purpose, fields, destination, consent policy, a semantic definition or the campaign status changes, or the approval expires."""


def slide_a(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "AGENTIC HEALTHCARE CAMPAIGN PLATFORM · SINGLE USER EXPERIENCE",
                "Codex is the single interface for discovery, approvals and continuous activation",
                "Data refreshes every day. Approved, versioned cohort rules push newly eligible patients to Marketing "
                "Cloud daily, without a daily human approval.")

    def section(x, y, n, t, c):
        cv.rect(x, y, 0.24, 0.24, c, None, shape=R, radius=0.5)
        cv.text(x, y, 0.24, 0.24, n, size=7, bold=True, color="000000", align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.32, y, 4.5, 0.24, t, size=8, bold=True, color=c, track=60, anchor=MSO_ANCHOR.MIDDLE)

    hy, top, bot = 1.28, 1.6, 5.55
    lx, lw = 0.45, 3.0
    mx, mw = 3.65, 4.1
    rx, rw = 7.97, 4.91
    # ---------------------------------------------------------------- 1 governed intelligence
    section(lx, hy, "1", "GOVERNED INTELLIGENCE", CYAN)
    items = [(CYAN, "Authoritative sources", "Epic · athenahealth · ADSI · Salesforce · SFMC; daily or streaming"),
             (MAGENTA, "DLP + Collibra", "approve datasets, classify PHI, set policy tags before ingest"),
             (EDGE, "Bronze → Silver", "raw extracts, then identity resolution (EUID) + consent of record"),
             (YELLOW, "Gold A · insight  |  restricted patient layer", "aggregates for agents  |  patients for the engines only"),
             (CYAN, "Kyvos semantic layer", "governed measures and cohort concepts (or built in-house)"),
             (MAGENTA, "Spanner knowledge graph", "concepts, cohort rules, campaigns, lineage; no patient nodes")]
    ih, gap = 0.56, (bot - top - 6 * 0.56) / 5
    iys = [top + k * (ih + gap) for k in range(6)]
    for (c, t, d), y in zip(items, iys):
        cv.rect(lx, y, lw, ih, CARD, EDGE, 0.75, R, 0.06)
        cv.rect(lx, y, 0.05, ih, c if c != EDGE else T3, None)
        cv.text(lx + 0.15, y + 0.03, lw - 0.22, ih - 0.06, [[(t, {"bold": True, "color": T1, "size": 8})],
                                                            [(d, {"color": T2})]], size=7, anchor=MSO_ANCHOR.MIDDLE,
                after=1, line=0.92)
    for y0, y1 in zip(iys, iys[1:]):
        cv.arrow(lx + 0.4, y0 + ih, lx + 0.4, y1, T3, 1.0)
    for k in (4, 5):
        cv.arrow(lx + lw, iys[k] + ih / 2, mx, iys[k] + ih / 2, items[k][0], 1.5)
    # ---------------------------------------------------------------- 2 Codex
    section(mx, hy, "2", "CODEX · SINGLE USER INTERFACE", YELLOW)
    cv.rect(mx, top, mw, bot - top, BLACK, YELLOW, 1.5, R, 0.08)
    cv.text(mx, top + 0.08, mw, 0.26, "ONE CONVERSATION · NAMED APPROVALS", size=10, bold=True, color=T1,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(mx, top + 0.34, mw, 0.18, "approvals signed by the approval service, never by Codex", size=7,
            color=YELLOW, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    steps = [(CYAN, "A", "Campaign goal", "campaign, channel, cadence and target population", None),
             (YELLOW, "B", "Cohort JSON + refresh policy", "versioned criteria and the daily refresh rule", "G1"),
             (YELLOW, "C", "Build + test the journey", "test contacts only; clinical + compliance", "G3"),
             (YELLOW, "D", "First run", "counts, exclusions, fields and destination; no PHI", "G2"),
             (CYAN, "E", "Ongoing status in Codex", "daily refresh results, failures, pauses, rule alerts", None)]
    sx, sw = mx + 0.16, mw - 0.32
    sh = 0.56
    sgap = (bot - 0.1 - (top + 0.62) - 5 * sh) / 4
    sy = [top + 0.62 + k * (sh + sgap) for k in range(5)]
    for (c, n, t, d, g), y in zip(steps, sy):
        cv.rect(sx, y, sw, sh, CARD, EDGE, 0.75, R, 0.08)
        cv.rect(sx, y, 0.05, sh, c, None)
        cv.text(sx + 0.15, y + 0.03, sw - 0.8, 0.26, [[(n + "  ", {"bold": True, "color": c}),
                                                      (t, {"bold": True, "color": T1})]], size=8,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(sx + 0.15, y + 0.29, sw - 0.25, sh - 0.3, d, size=7, color=T2)
        if g:
            cv.rect(sx + sw - 0.55, y + 0.07, 0.45, 0.2, YELLOW, None, shape=R, radius=0.5)
            cv.text(sx + sw - 0.55, y + 0.07, 0.45, 0.2, g, size=7, bold=True, color="000000",
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- 3 cohort resolution + activation
    section(rx, hy, "3", "COHORT RESOLUTION + ACTIVATION · PROTECTED BOUNDARY", MAGENTA)
    cv.rect(rx - 0.04, top - 0.05, rw + 0.08, bot - top + 0.1, None, MAGENTA, 1.0, R, 0.03, dash="dash")
    cw = (rw - 0.16 - 2 * 0.14) / 3
    cxs = [rx + 0.08 + k * (cw + 0.14) for k in range(3)]
    r1, r2, chh = top + 0.08, top + 0.8, 0.62
    row1 = [("5", "Cohort Resolution Engine", "checks JSON + token; controlled query", CYAN),
            ("6", "Patient query", "matching patients, inside the boundary", MAGENTA),
            ("7", "Eligibility checks", "consent · STOP · suppression · deceased · duplicates", CYAN)]
    row2 = [("8", "Summary → Codex", "counts, exclusions, fields; no PHI", YELLOW),
            ("9", "Activation Engine", "checks G2, purpose, rule version, fields", MAGENTA),
            ("10", "MC data extension", "approved records; neutral name", EDGE)]
    for ry_, rowd in ((r1, row1), (r2, row2)):
        for k, (n, t, d, c) in enumerate(rowd):
            chip(cv, cxs[k], ry_, cw, chh, n + "  " + t, d, c, 7.5)
            if k < 2:
                cv.arrow(cxs[k] + cw, ry_ + chh / 2, cxs[k + 1], ry_ + chh / 2, T2, 1.0)
    cv.arrow(cxs[2] + cw / 2, r1 + chh, cxs[2] + cw / 2, r2 - 0.02, T2, 1.0, head=False)
    cv.arrow(cxs[2] + cw / 2, r2 - 0.02 - 0.0, cxs[0] + cw / 2, r2 - 0.02, T2, 1.0, head=False)
    cv.arrow(cxs[0] + cw / 2, r2 - 0.02, cxs[0] + cw / 2, r2, T2, 1.0)
    # 4 continuous cohort refresh
    ry4 = r2 + chh + 0.14
    section(rx + 0.08, ry4, "4", "CONTINUOUS COHORT REFRESH · EVERY DAY", CYAN)
    bx, bw_, byy = rx + 0.08, rw - 0.16, ry4 + 0.3
    cv.rect(bx, byy, bw_, bot - byy - 0.04, "06262B", CYAN, 1.0, R, 0.04)
    ref = [("11", "Daily data refresh", "sources → Bronze → Silver → Gold; freshness checked"),
           ("12", "Refresh trigger", "runs after each refresh; skips the run if data is stale"),
           ("13", "Incremental resolver", "approved rule on new + changed patients; consent re-checked"),
           ("14", "Delta activation + exit sync", "adds the newly eligible; removes those who no longer qualify")]
    rh = 0.3
    for k, (n, t, d) in enumerate(ref):
        row(cv, bx + 0.08, byy + 0.08 + k * (rh + 0.04), bw_ - 0.16, rh, n, t, d, CYAN)
    cv.text(bx + 0.1, byy + 0.08 + 4 * (rh + 0.04), bw_ - 0.2, bot - 0.04 - (byy + 0.08 + 4 * (rh + 0.04)),
            [[("No daily approval ", {"bold": True, "color": YELLOW}),
              ("while the campaign, rule version, purpose, fields and destination stay unchanged.", {"color": T1})]],
            size=7, anchor=MSO_ANCHOR.MIDDLE)
    # Codex <-> engines
    gx0, gx1 = mx + mw, rx - 0.04
    cv.arrow(gx0, r1 + chh / 2, cxs[0], r1 + chh / 2, CYAN, 1.25)                    # cohort JSON + token
    cv.arrow(cxs[0], r2 + chh / 2, gx0, r2 + chh / 2, T2, 1.25, dash="dash")         # summary only
    cv.arrow(bx, sy[4] + sh / 2, gx0, sy[4] + sh / 2, T2, 1.25, dash="dash")         # daily status
    # ---------------------------------------------------------------- Marketing Cloud execution
    jy, jh = bot + 0.13, 0.76
    cv.rect(0.45, jy, 12.43, jh, "06262B", CYAN, 1.0, R, 0.06)
    cv.text(0.6, jy, 1.3, jh, [[("MARKETING CLOUD", {"bold": True, "color": CYAN, "track": 80})],
                               [("EXECUTION", {"bold": True, "color": CYAN, "track": 80})],
                               [("inside SFMC", {"color": T2})]], size=7, anchor=MSO_ANCHOR.MIDDLE, after=1)
    mc = [("Contact key", "pseudonymous, stable; mapped only inside the boundary"),
          ("Load method", "REST upsert or encrypted SFTP; flags exits"),
          ("Journey", "daily entry, re-entry rule, exit + goal; day 1 → 30"),
          ("Consent sync", "two-way in minutes: STOP, unsubscribes"),
          ("Channel rules", "TCPA, STOP/HELP, quiet hours; CAN-SPAM, DMARC"),
          ("Content", "approved templates; no condition or PHI in text, URLs"),
          ("Tracking back", "daily extract → restricted layer; bounces → contactability"),
          ("Security", "own BU, SSO, retention, encryption; BAA confirmed")]
    tw = (12.88 - 0.1 - 1.95 - 7 * 0.08) / 8
    for k, (t, d) in enumerate(mc):
        x = 1.95 + k * (tw + 0.08)
        cv.rect(x, jy + 0.08, tw, jh - 0.16, CARD, None)
        cv.rect(x, jy + 0.08, 0.04, jh - 0.16, CYAN, None)
        cv.text(x + 0.1, jy + 0.1, tw - 0.14, jh - 0.2, [[(t, {"bold": True, "color": T1, "size": 7.5})],
                                                        [(d, {"color": T2})]], size=7, anchor=MSO_ANCHOR.MIDDLE,
                after=1, line=0.92)
    # ---------------------------------------------------------------- re-approval
    ay_ = jy + jh + 0.07
    cv.rect(0.45, ay_, 12.43, 0.4, "2B2508", YELLOW, 1.0, R, 0.08)
    cv.text(0.6, ay_, 12.13, 0.4, [[("RE-APPROVAL REQUIRED ", {"bold": True, "color": YELLOW}),
                                    ("only when cohort logic, purpose, permitted fields, destination, consent "
                                     "policy, a semantic definition or campaign status changes, or the approval "
                                     "expires. Opt-outs apply at once; spike alerts pause a run; every run is "
                                     "reconciled.", {"color": T1})]], size=7.5, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, NOTES_A)
    return s


# ================================================================== B: Gold B
NOTES_B = """SLIDE: Gold B, the restricted patient layer behind every campaign   (about 2 minutes)

KEY MESSAGE
Gold B holds what it takes to decide exactly who may be contacted, now, for an approved campaign. Only the two engines read it; agents, the semantic layer and the knowledge graph never do.

WALK IT
- Top: Silver resolves identity and consent; Gold B serves the Cohort Resolution Engine, the masked G2 summary and the Activation Engine; engagement comes back into Gold B and is aggregated into Gold A.
- Left, what is in it: the patient key, the cohort facts the rules need, consent per channel and purpose, verified contact points, exclusions, preferences, and engagement and outcomes per patient.
- Middle, who can read it: the two engines, for an approved run only; the Sierra voice agent through the patient-context API, for one verified caller. Agents, Codex, the semantic layer and the knowledge graph never; people see the masked G2 summary; any break-glass access is logged.
- Right, what we can do with it: resolve the exact audience, apply consent and suppression at run time, produce the G2 summary, release minimum fields, hold out a control group, track outcomes such as readmissions, and feed safe aggregates back to Gold A.
- Bottom: the controls on Gold B."""


def slide_b(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "AGENTIC HEALTHCARE CAMPAIGN PLATFORM · GOLD B",
                "Gold B: the restricted patient layer behind every campaign",
                "Only deterministic engines read Gold B; agents never do. It answers one question: exactly who may be "
                "contacted, now, for this approved campaign.")
    # flow strip
    fy, fh = 1.3, 0.62
    flow = [("Silver", "identity + consent", EDGE), ("Gold B", "restricted", MAGENTA),
            ("Cohort Resolution", "engine", CYAN), ("G2", "masked summary", YELLOW),
            ("Activation", "engine", MAGENTA), ("Marketing Cloud", "data extension", EDGE),
            ("Engagement", "+ outcomes", EDGE), ("Gold B", "per patient", MAGENTA), ("Gold A", "aggregates only",
                                                                                      YELLOW)]
    w = (12.43 - 8 * 0.16) / 9
    for k, (t, d, c) in enumerate(flow):
        x = 0.45 + k * (w + 0.16)
        chip(cv, x, fy, w, fh, t, d, c)
        if k < 8:
            cv.arrow(x + w, fy + fh / 2, x + w + 0.16, fy + fh / 2, T2, 1.0)
    # three columns
    top = 2.12
    ws = [4.0, 3.9, 4.25]
    xs = [0.45, 0.45 + ws[0] + 0.14, 0.45 + ws[0] + ws[1] + 0.28]
    inside = [("Patient key", "EUID, from Silver identity resolution"),
              ("Cohort facts", "diagnosis, discharge date, facility, age band"),
              ("Consent", "per channel and purpose: SMS, email, voice"),
              ("Contact points", "verified phone and email"),
              ("Exclusions", "STOP / opt-out, deceased, do-not-contact, frequency caps"),
              ("Preferences", "language, quiet hours"),
              ("Engagement", "sends, replies, opt-outs and outcomes per patient")]
    who = [(True, "Cohort Resolution Engine", "for an approved cohort JSON only"),
           (True, "Activation Engine", "minimum fields, for the approved run"),
           (False, "Agents and Codex", "never: counts only, through the summary"),
           (False, "Semantic layer + graph", "never: they read Gold A"),
           (True, "People", "the masked G2 summary; break-glass logged"),
           (True, "Marketing Cloud", "only the released fields, this run"),
           (True, "Sierra voice agent", "patient-context API: this verified caller only")]
    can = ["Resolve the exact eligible audience for an approved campaign",
           "Apply consent, STOP, suppression and contactability at run time",
           "Produce the masked G2 summary: counts and exclusions by rule",
           "Release minimum fields to Marketing Cloud, time-limited",
           "Hold out a control group to measure true impact",
           "Track engagement and outcomes per patient, such as readmissions",
           "Feed aggregates to Gold A, with small groups suppressed"]
    head_bar(cv, xs[0], top, ws[0], "WHAT IS IN GOLD B", MAGENTA)
    head_bar(cv, xs[1], top, ws[1], "WHO CAN READ IT", YELLOW)
    head_bar(cv, xs[2], top, ws[2], "WHAT WE CAN DO WITH IT", CYAN)
    rh = 0.44
    for k, (t, d) in enumerate(inside):
        row(cv, xs[0], top + 0.38 + k * (rh + 0.06), ws[0], rh, "", t, d, MAGENTA)
    rh2 = (7 * (rh + 0.06) - (len(who) - 1) * 0.06) / len(who)
    for k, (ok, t, d) in enumerate(who):
        y = top + 0.38 + k * (rh2 + 0.06)
        c = CYAN if ok else MAGENTA
        row(cv, xs[1], y, ws[1], rh2, "✓" if ok else "✕", t, d, c)
    for k, t in enumerate(can):
        row(cv, xs[2], top + 0.38 + k * (rh + 0.06), ws[2], rh, str(k + 1), t, "", CYAN)
    # controls
    gy, gh = 6.08, 0.74
    cv.text(0.45, gy, 1.3, gh, [[("CONTROLS", {"bold": True, "color": T1, "track": 120})],
                                [("on Gold B", {"color": T3})]], size=7, anchor=MSO_ANCHOR.MIDDLE, after=1)
    ctrls = [("Service identities only", "no agent, no dashboard"), ("Row + column policies", "CMEK encryption"),
             ("Every read logged", "who, why, which rule version"), ("Retention limits", "purged on schedule"),
             ("No copies outside", "only the released fields leave"), ("Reconciled every run", "counts match end to end")]
    w = (12.88 - 1.8 - 5 * 0.1) / 6
    for k, (t, d) in enumerate(ctrls):
        x = 1.8 + k * (w + 0.1)
        cv.rect(x, gy, w, gh, CARD, None)
        gbar(cv, x, gy, 0.05, gh)
        cv.text(x + 0.16, gy, w - 0.22, gh, [[(t, {"bold": True, "color": T1, "size": 7.5})], [(d, {"color": T2})]],
                size=7, anchor=MSO_ANCHOR.MIDDLE, after=1)
    set_notes(s, NOTES_B)
    return s


# ================================================================== B2: Gold B as the not-yet-consented layer (preview)
NOTES_B2 = """SLIDE: Gold B, patients we cannot contact yet   (about 2 minutes)

KEY MESSAGE
Gold B holds the patients who have not given consent or whose information is incomplete. They stay restricted; we invite those we are allowed to ask to give consent or complete their details. When they opt in, they move to Gold A. Explicit opt-outs, STOP and deceased patients are never asked again.

WALK IT
- Top: Silver resolves identity and consent; patients without consent or with missing information land in Gold B. The Cohort Resolution Engine separates explicit opt-outs (never asked) from patients we may ask (consent unknown, details missing). After the masked G2 summary is approved, the Activation Engine sends an update request through a permitted channel. Engagement decides the branch: opted in goes to Gold A; not opted in or still missing stays in Gold B.
- Left, what is in it: the patient key, consent status, the missing information, the contact points we do have, the never-contact exclusions, preferences, and the history of requests.
- Middle, who can read it: the two engines, for an approved run only; the Sierra voice agent for one verified caller. Agents, Codex, the semantic layer and the knowledge graph never; people see the masked G2 summary.
- Right, what we can do with it: find who may be asked, never re-ask opt-outs, approve on counts, send the request, write the answers back to Epic and the consent system, and move consented patients to Gold A at the next refresh.
- Bottom: the controls on Gold B."""


def slide_b2(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "AGENTIC HEALTHCARE CAMPAIGN PLATFORM · GOLD B",
                "Gold B: patients we cannot contact yet",
                "Patients without consent or with missing information stay in Gold B, restricted. Those we may ask are "
                "invited to opt in or complete their details; when they opt in, they move to Gold A.")
    # flow strip, ending in two branches
    fy, fh = 1.26, 0.72
    flow = [("Silver", "identity + consent", EDGE),
            ("Gold B · restricted", "opted out or missing information", MAGENTA),
            ("Cohort Resolution", "engine: checks opt-outs + filled-in information", CYAN),
            ("G2", "masked summary", YELLOW),
            ("Activation", "engine", MAGENTA),
            ("Marketing Cloud", "update request: consent + details", EDGE),
            ("Engagement", "replies + updates", EDGE)]
    w = (12.43 - 7 * 0.16) / 8
    for k, (t, d, c) in enumerate(flow):
        x = 0.45 + k * (w + 0.16)
        chip(cv, x, fy, w, fh, t, d, c)
        if k < 6:
            cv.arrow(x + w, fy + fh / 2, x + w + 0.16, fy + fh / 2, T2, 1.0)
    bx = 0.45 + 7 * (w + 0.16)
    bh = (fh - 0.06) / 2
    ex = 0.45 + 6 * (w + 0.16) + w
    xm = ex + 0.06
    for k, (t, d, c) in enumerate([("Gold A · opted in", "consented; aggregates only", YELLOW),
                                   ("Gold B · not opted in", "or still missing; per patient", MAGENTA)]):
        y = fy + k * (bh + 0.06)
        chip(cv, bx, y, w, bh, t, d, c, 7)
        cv.arrow(ex, fy + fh / 2, xm, fy + fh / 2, T2, 1.0, head=False)
        cv.arrow(xm, fy + fh / 2, xm, y + bh / 2, T2, 1.0, head=False)
        cv.arrow(xm, y + bh / 2, bx, y + bh / 2, YELLOW if k == 0 else MAGENTA, 1.0)
    # three columns
    top = 2.16
    ws = [4.0, 3.9, 4.25]
    xs = [0.45, 0.45 + ws[0] + 0.14, 0.45 + ws[0] + ws[1] + 0.28]
    inside = [("Patient key", "EUID, from Silver identity resolution"),
              ("Consent status", "opted out, or unknown / expired, per channel and purpose"),
              ("Missing information", "no email, no mobile number, or unverified contact"),
              ("Contact points we have", "verified email or phone, where they exist"),
              ("Never-contact", "explicit opt-out, STOP, deceased, do-not-contact"),
              ("Preferences", "language, quiet hours"),
              ("Request history", "update requests sent, replies, consents given")]
    who = [(True, "Cohort Resolution Engine", "for an approved cohort JSON only"),
           (True, "Activation Engine", "minimum fields, for the approved run"),
           (False, "Agents and Codex", "never: counts only, through the summary"),
           (False, "Semantic layer + graph", "never: they read Gold A"),
           (True, "People", "the masked G2 summary; break-glass logged"),
           (True, "Marketing Cloud", "only the released fields, this run"),
           (True, "Sierra voice agent", "patient-context API: this verified caller only")]
    can = ["Find who may be asked: consent unknown or information missing",
           "Never re-ask explicit opt-outs, STOP, deceased or do-not-contact",
           "Produce the masked G2 summary: counts by reason",
           "Send an update request by email where an address exists; else portal",
           "Write answers back to Epic and the consent system, not to Gold B",
           "Opted in: the patient moves to Gold A at the next daily refresh",
           "Not opted in or still missing: stays in Gold B, restricted"]
    head_bar(cv, xs[0], top, ws[0], "WHAT IS IN GOLD B", MAGENTA)
    head_bar(cv, xs[1], top, ws[1], "WHO CAN READ IT", YELLOW)
    head_bar(cv, xs[2], top, ws[2], "WHAT WE CAN DO WITH IT", CYAN)
    rh = 0.44
    for k, (t, d) in enumerate(inside):
        row(cv, xs[0], top + 0.38 + k * (rh + 0.06), ws[0], rh, "", t, d, MAGENTA)
    for k, (ok, t, d) in enumerate(who):
        row(cv, xs[1], top + 0.38 + k * (rh + 0.06), ws[1], rh, "✓" if ok else "✕", t, d, CYAN if ok else MAGENTA)
    for k, t in enumerate(can):
        row(cv, xs[2], top + 0.38 + k * (rh + 0.06), ws[2], rh, str(k + 1), t, "", CYAN)
    # controls
    gy, gh = 6.08, 0.74
    cv.text(0.45, gy, 1.3, gh, [[("CONTROLS", {"bold": True, "color": T1, "track": 120})],
                                [("on Gold B", {"color": T3})]], size=7, anchor=MSO_ANCHOR.MIDDLE, after=1)
    ctrls = [("Service identities only", "no agent, no dashboard"), ("Row + column policies", "CMEK encryption"),
             ("Every read logged", "who, why, which rule version"), ("Retention limits", "purged on schedule"),
             ("Opt-outs never re-asked", "STOP and deceased excluded"), ("Reconciled every run", "counts match end to end")]
    w = (12.88 - 1.8 - 5 * 0.1) / 6
    for k, (t, d) in enumerate(ctrls):
        x = 1.8 + k * (w + 0.1)
        cv.rect(x, gy, w, gh, CARD, None)
        gbar(cv, x, gy, 0.05, gh)
        cv.text(x + 0.16, gy, w - 0.22, gh, [[(t, {"bold": True, "color": T1, "size": 7.5})], [(d, {"color": T2})]],
                size=7, anchor=MSO_ANCHOR.MIDDLE, after=1)
    set_notes(s, NOTES_B2)
    return s


def main(out=OUT):
    import muted_theme as mt
    import sierra_voice
    prs = Presentation(SRC)
    lst = prs.slides._sldIdLst
    for el in list(lst):
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    slide_a(prs, layout)
    slide_b(prs, layout)
    sierra = sierra_voice.build(prs, layout)
    sierra_voice.highlight(sierra, dark=True)
    for sl in prs.slides:
        mt.min_font(sl, 7.0)
    fix_footers(prs)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    prs.save(out)
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
