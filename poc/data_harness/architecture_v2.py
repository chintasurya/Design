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
The business user works in one place, Codex. Agents decide what campaign and what cohort, from definitions and counts. Engines we build in Google Cloud decide exactly which patients, release only the minimum fields to Marketing Cloud after people approve, and keep the cohort current without a daily approval.

WALK IT
1 Govern the data in Google Cloud: before anything is ingested, a Collibra steward approves each dataset, DLP classifies the PHI and the policy tags are set; approved extracts land in Bronze, where DLP re-scans; Silver resolves identity across systems (EUID) and holds the consent of record; Gold splits into Gold A (insight: aggregates, small groups suppressed, for agents) and Gold B (restricted: patient, contact and consent, for the engines only).
2 Governed intelligence, side by side on Gold A: the semantic layer (Kyvos or built in-house) and the knowledge graph in Spanner, with no patient nodes.
3 Codex: the goal; the campaign and cohort JSON, a versioned contract with its refresh policy, approved at G1; the journey built and tested on test contacts, approved at G3; the first run's summary, approved at G2; then ongoing status: each refresh, failure, pause and rule-change alert. Approvals come from the approval service with named roles and a signed token.
4 The Cohort Resolution Engine checks the JSON and the token, runs a controlled, parameterized query on Gold B, applies consent, STOP, suppression, deceased, duplicate and contactability rules, and returns counts only. After G2 the Activation Engine checks the G2 token, purpose, rule version and minimum fields and pushes the records to a Marketing Cloud data extension; Journey Builder runs the cadence, day 1 to day 30, and re-checks consent at send.
5 Continuous cohort refresh: a daily or event-driven trigger, skipped if the data is stale; the incremental resolver applies the approved rule to new and changed patients and re-checks consent every run; delta activation adds the newly eligible without duplicates; exit sync removes anyone who opted out, died or no longer meets the rule. No daily approval while the rule version, purpose, fields and destination are unchanged; volume caps and spike alerts pause the run; re-approval when any of those change, a semantic definition changes, or the approval expires.
Always on: immediate opt-out to the consent of record, a run ID with reconciliation on every run, and engagement back into Gold B, aggregated into Gold A."""


def slide_a(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "AGENTIC HEALTHCARE CAMPAIGN PLATFORM · SINGLE USER EXPERIENCE",
                "Codex is the single interface for discovery, approvals and continuous activation",
                "Agents see definitions and counts only. Approved, versioned cohort rules keep adding newly eligible "
                "patients, within set limits, without a daily approval.")
    # ---------------------------------------------------------------- 1 govern the data
    by, bh = 1.22, 0.86
    cv.rect(0.45, by, 12.43, bh, "0A0A0A", EDGE, 0.75, R, 0.04)
    cv.text(0.6, by + 0.02, 6, 0.2, "1  GOVERN THE DATA IN GOOGLE CLOUD", size=7, bold=True, color=MAGENTA,
            track=120, anchor=MSO_ANCHOR.MIDDLE)
    iy, ih = by + 0.24, 0.54
    w = (12.43 - 0.24 - 4 * 0.16) / 5
    xs = [0.57 + k * (w + 0.16) for k in range(5)]
    chip(cv, xs[0], iy, w, ih, "Sources", "Epic, athenahealth, ADSI, Salesforce, SFMC", EDGE)
    chip(cv, xs[1], iy, w, ih, "DLP + Collibra", "approve datasets, classify PHI, set policy tags before "
         "ingest", MAGENTA)
    chip(cv, xs[2], iy, w, ih, "Bronze", "approved raw extracts, lineage; restricted; DLP re-scans", EDGE)
    chip(cv, xs[3], iy, w, ih, "Silver", "identity resolution (EUID); consent of record", EDGE)
    gh = (ih - 0.04) / 2
    chip(cv, xs[4], iy, w, gh, "Gold A · insight", "aggregates → agents", YELLOW, 7)
    chip(cv, xs[4], iy + gh + 0.04, w, gh, "Gold B · restricted", "patients → engines only", MAGENTA, 7)
    for k in range(3):
        cv.arrow(xs[k] + w, iy + ih / 2, xs[k + 1], iy + ih / 2, T2, 1.0)
    cv.arrow(xs[3] + w, iy + gh / 2, xs[4], iy + gh / 2, T2, 1.0)
    cv.arrow(xs[3] + w, iy + gh + 0.04 + gh / 2, xs[4], iy + gh + 0.04 + gh / 2, T2, 1.0)
    # ---------------------------------------------------------------- columns
    top, bot = 2.2, 5.5
    lx, lw = 0.45, 3.0
    mx, mw = 3.65, 3.85
    rx, rw = 8.2, 4.68
    # 2 governed intelligence
    cv.text(lx, top, lw, 0.26, "2  GOVERNED INTELLIGENCE · ON GOLD A", size=7, bold=True, color=CYAN, track=100,
            anchor=MSO_ANCHOR.MIDDLE)
    ch = 1.38
    cards = [(CYAN, "Semantic layer", "Kyvos or built in-house", "One meaning for every term: patient, discharge, "
              "cohort, consent, engagement, KPI. Small groups suppressed."),
             (MAGENTA, "Knowledge graph", "Spanner Graph", "Concepts, cohort rules, campaigns, templates, lineage "
              "and owners. No patient nodes.")]
    ys = [top + 0.32, top + 0.32 + ch + 0.14]
    for (c, t, sub, d), y in zip(cards, ys):
        cv.rect(lx, y, lw, ch, TINTS[c], c, 1.0, R, 0.05)
        cv.text(lx + 0.15, y + 0.1, lw - 0.3, 0.46, [[(t, {"bold": True, "color": T1, "size": 10})],
                                                     [(sub, {"color": c, "size": 7.5})]], size=10, after=1)
        cv.text(lx + 0.15, y + 0.62, lw - 0.3, ch - 0.68, d, size=7.5, color=T2)
        cv.arrow(lx + lw, y + ch / 2, mx, y + ch / 2, c, 1.5)
    # 3 Codex
    cv.rect(mx, top, mw, bot - top, BLACK, YELLOW, 1.5, R, 0.06)
    cv.text(mx, top + 0.06, mw, 0.28, "3  CODEX · AGENTIC ORCHESTRATION", size=11, bold=True, color=T1,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(mx + 0.1, top + 0.34, mw - 0.2, 0.2, "One conversation · approvals by named roles, signed by the "
            "approval service", size=7, color=YELLOW, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    steps = [(CYAN, "A", "Campaign goal", "channel, cadence and target population", None),
             (YELLOW, "B", "Cohort JSON + refresh policy", "versioned contract: purpose, criteria, fields, KPIs",
              "G1"),
             (YELLOW, "C", "Build + test the journey", "Design + Readiness agents, test contacts only", "G3"),
             (YELLOW, "D", "First run, then ongoing status", "counts only; refreshes, pauses, rule-change alerts",
              "G2")]
    sx, sw, sh = mx + 0.16, mw - 0.32, 0.58
    sy = [top + 0.62 + k * (sh + 0.08) for k in range(4)]
    for (c, n, t, d, g), y in zip(steps, sy):
        cv.rect(sx, y, sw, sh, TINTS[c], c, 1.0, R, 0.08)
        cv.text(sx + 0.12, y + 0.04, sw - 0.75, 0.25, [[(n + "  ", {"bold": True, "color": c}),
                                                       (t, {"bold": True, "color": T1})]], size=8,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(sx + 0.12, y + 0.3, sw - 0.24, sh - 0.32, d, size=7, color=T2)
        if g:
            cv.rect(sx + sw - 0.55, y + 0.07, 0.45, 0.2, YELLOW, None, shape=R, radius=0.5)
            cv.text(sx + sw - 0.55, y + 0.07, 0.45, 0.2, g, size=7, bold=True, color="000000",
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    for y0, y1 in zip(sy, sy[1:]):
        cv.arrow(mx + mw / 2, y0 + sh, mx + mw / 2, y1, T2, 1.0)
    # 4 engines, inside the protected boundary
    cv.rect(rx - 0.06, top - 0.04, rw + 0.12, bot - top + 0.08, None, MAGENTA, 1.25, R, 0.03, dash="dash")
    cv.text(rx + 0.06, top + 0.02, rw - 0.12, 0.22, "4  COHORT RESOLUTION + ACTIVATION · ON GOLD B", size=7,
            bold=True, color=MAGENTA, track=100, anchor=MSO_ANCHOR.MIDDLE)
    ex, ew = rx + 0.06, rw - 0.12
    e1y = top + 0.3
    head_bar(cv, ex, e1y, ew, "COHORT RESOLUTION ENGINE", CYAN, "deterministic, no AI")
    res = [("1", "Cohort API", "checks the JSON and the G1 + G3 token"),
           ("2", "Controlled query on Gold B", "approved concepts → parameterized SQL; agents never write SQL"),
           ("3", "Eligibility + consent rules", "consent · STOP · suppression · deceased · duplicates · "
            "contactability"),
           ("4", "Summary to Codex", "counts and exclusions by rule; no PHI")]
    rh = 0.3
    ry = [e1y + 0.32 + k * (rh + 0.04) for k in range(len(res))]
    for (n, t, d), y in zip(res, ry):
        row(cv, ex, y, ew, rh, n, t, d, CYAN)
    e2y = ry[-1] + rh + 0.08
    head_bar(cv, ex, e2y, ew, "CAMPAIGN ACTIVATION ENGINE", MAGENTA, "rules engine")
    act = [("5", "Activation rules", "checks the G2 token, purpose, rule version, minimum fields"),
           ("6", "Marketing Cloud DE → journey", "day 1 → day 30 cadence; consent re-checked at send")]
    ay = [e2y + 0.32 + k * (rh + 0.04) for k in range(len(act))]
    for (n, t, d), y in zip(act, ay):
        row(cv, ex, y, ew, rh, n, t, d, MAGENTA)
    # Codex <-> engines: (from x, from y, to y, x of the vertical, colour, dash, label, label offset)
    gx0, gx1 = mx + mw, rx - 0.06
    links = [(gx0, sy[1] + sh / 2, ry[0] + rh / 2, gx1 - 0.1, CYAN, None, "JSON + token", -0.3),
             (gx1, ry[3] + rh / 2, sy[3] + 0.16, gx1 - 0.1, T2, "dash", "summary only", None),
             (gx0, sy[3] + sh - 0.1, ay[0] + rh / 2, gx1 - 0.24, YELLOW, None, "G2 token", 0.03)]
    for a, ya, yb, xv, c, dash, lab, dy in links:
        b = gx1 if a == gx0 else gx0
        cv.arrow(a, ya, xv, ya, c, 1.25, dash=dash, head=False)
        cv.arrow(xv, ya, xv, yb, c, 1.25, dash=dash, head=False)
        cv.arrow(xv, yb, b, yb, c, 1.25, dash=dash)
        ly = (ya + dy) if dy is not None else yb - 0.3
        cv.text(gx0 + 0.03, ly, xv - gx0 - 0.06, 0.27, lab.split(" ", 1), size=7, bold=True,
                color=c if c != T2 else T1, anchor=MSO_ANCHOR.MIDDLE, line=0.85)
    # ---------------------------------------------------------------- 5 continuous cohort refresh
    cy_, chh = bot + 0.1, 0.92
    cv.rect(0.45, cy_, 12.43, chh, "06262B", CYAN, 1.0, R, 0.05)
    cv.text(0.6, cy_, 1.75, chh, [[("5  CONTINUOUS", {"bold": True, "color": CYAN, "track": 100})],
                                  [("COHORT REFRESH", {"bold": True, "color": CYAN, "track": 100})],
                                  [("on Gold B, no daily approval", {"color": T2})]], size=7,
            anchor=MSO_ANCHOR.MIDDLE, after=1)
    refresh = [("Refresh trigger", "daily or on new data; skipped if data is stale"),
               ("Incremental resolver", "approved rule on new + changed patients; consent re-checked"),
               ("Delta activation", "adds the newly eligible to the journey; no duplicates"),
               ("Exit sync", "removes anyone who opts out, dies or no longer qualifies")]
    w4 = 1.95
    for k, (t, d) in enumerate(refresh):
        x = 2.4 + k * (w4 + 0.14)
        chip(cv, x, cy_ + 0.12, w4, chh - 0.24, t, d, CYAN, 7.5)
        if k < 3:
            cv.arrow(x + w4, cy_ + chh / 2, x + w4 + 0.14, cy_ + chh / 2, T2, 1.0)
    gxr = 2.4 + 4 * (w4 + 0.14) - 0.04
    cv.text(gxr, cy_ + 0.06, 12.8 - gxr, chh - 0.12, [
        [("Re-approval only ", {"bold": True, "color": YELLOW}),
         ("when the rule, purpose, fields, destination, consent policy or a semantic definition changes, or "
          "the approval expires. Volume caps and spike alerts pause a run.", {"color": T1})]], size=7,
        anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- always on
    fy = cy_ + chh + 0.06
    fx, fy_, fw, fh = cv.frame(0.45, fy, 12.43, 0.3, "0A0A0A", 0.02)
    cv.text(fx + 0.15, fy_, fw - 0.3, fh, [[("ALWAYS ON   ", {"bold": True, "color": YELLOW, "track": 100}),
                                           ("opt-outs to the consent of record at once  ·  run ID + reconciliation "
                                            "on every run  ·  engagement → Gold B → aggregated into Gold A",
                                            {"color": T1})]], size=7, anchor=MSO_ANCHOR.MIDDLE)
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
