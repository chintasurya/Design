"""Campaign-platform slides for the Agentic Harness deck (build_data_harness_deck.py places them).

FLOW_NOTES      talk track for the end-to-end slide (combined_flow.build)
build_order     how we build it: phases 0-6 mapped to the slide's boxes, safeguards first, release last
phi_governance  PHI governance: masking is one control; the four additions the architecture review asked for
"""
import os

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

import combined_flow
from build_data_harness_deck import CARD, CARD2, DIM, R, SOFT, TINT, VIO, new_slide, pill
from build_data_harness_deck import EDGE as EDGE_
from build_mad_ig_deck import BLACK, CYAN, GREEN, MAGENTA, WHITE, YELLOW, set_notes
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
ON_COLOR = combined_flow.ON_COLOR

TITLE_NOTES = ("Open: this is the agentic healthcare campaign platform. The data is governed in Google Cloud first, "
               "AI agents plan and build campaigns on masked data, and only approved patients are released to "
               "Marketing Cloud. It is a proposed target state, piloted first on the CHF post-discharge nudge.")

FLOW_NOTES = """SLIDE: From governed data to a tested, approved campaign   (about 3-4 minutes)

OPEN
This one slide is the whole platform. Read it top to bottom: first we govern the data in Google Cloud, then a marketer works with AI agents on masked data, and only at the end are approved patients released to Marketing Cloud. Two lines cross the slide; they are the two rules that keep patients safe.

BAND 1 · GOVERN THE DATA IN GOOGLE CLOUD
(1) Sources: Epic, athenahealth, ADSI, Strata, Salesforce, Marketing Cloud engagement. Approved datasets only, not the whole estate.
(2) Governance comes first: before anything lands, a Collibra steward approves each dataset, DLP finds the sensitive columns and policy tags mask the PHI.
(3) Bronze keeps the approved, tagged extracts with lineage, under restricted access; DLP re-scans what lands.
(4) Silver standardizes identities, encounters, contacts and consent evidence. It keeps every patient: eligibility is decided per campaign.
(5) Gold B: identity-linked eligibility inputs, restricted services only. (6) Gold A: protected aggregates (heart, maternity, general and more), the only thing agents use.
This is prepared once and kept fresh, instead of rebuilt for every campaign.

LINE 1 · TRUST BOUNDARY
Agents have no access to raw patient data. Only Gold A's protected aggregates cross this line.

BAND 2 · PROMPT IN CODEX, PLAN, BUILD + TEST
(7) The marketer types in Codex or a business console: "Build a post-discharge follow-up campaign for heart patients."
(8) The Orchestrator, Campaign Strategist and Analytics agents read the knowledge graph and Gold A and size the audience in counts, never names.
(9) G1: the marketer and a clinical reviewer approve the Campaign Opportunity Brief, using masked Tableau dashboards.
(10) The Campaign Design Agent uses Journey Builder to build the journey and data extension, paused.
(11) The Activation Readiness Agent tests with test contacts only, against a catalog of failure modes (consent, STOP, links, quiet hours). Failures go back to 10, at most five times, then to a named owner.
(12) G3: clinical and compliance approve the journey and content when every test passes. It waits, active, with no one in it.
Underneath: the knowledge graph (metadata, never patients), Tableau, the Compliance Guardian, the Measurement Agent and the people who approve.

LINE 2 · RECOMMENDATION IS NOT RELEASE
An agent's recommendation is never permission to release data. Everything above is a proposal; release happens only below, through approved services.

BAND 3 · RELEASE + SEND
(13) A deterministic eligibility service applies the approved rules to Gold B: no consent, no phone or email, STOP, deceased, duplicates out, each with a reason.
(14) G2: the SME and tech lead review a masked pre-send report. No PHI on screen.
(15) The policy engine and activation gateway check purpose, consent, suppression and minimum fields, record a Compliance Passport, and release only the fields this campaign needs, for this run, time-limited.
(16) Through Data Cloud today, or a direct pull once proven. (17-18) Records land in the data extension and the tested journey starts. (19) Consent, STOP and caps are checked again at send. (20) Measurement against a holdout refreshes Gold A; engagement returns to Bronze.

CLOSE
Build and test before data lands, a masked review, minimum fields after two approvals, no raw PHI for agents, steward-approved masking, a retry cap, and re-checks at send: faster campaigns, never the wrong or a no-consent patient.

LIKELY QUESTIONS
- Do agents see names? No: Gold A aggregates and counts only. Only the gateway resolves contact details, after G2 and G3.
- Why test first? The data extension starts the journey by itself, so the journey must be ready before records arrive.
- Are we replacing Data Cloud? No: it stays as Path A. Path B only after parity and security sign-off.
- How much faster? No number yet: we measure today's CHF process against a pilot first."""

BUILD_NOTES = """SLIDE: How we build it   (about 2 minutes)

KEY MESSAGE
The 1-20 numbers are the order a campaign runs. We build in a different order: every safeguard exists, and release is proven on synthetic data, before any real patient moves.

WALK IT
- Phase 0: confirm what is in Google Cloud and who owns it, map today's CHF campaign, check BAAs and licences, and measure today's process as the baseline.
- Phase 1: PHI governance first, box 2: a Collibra steward approves each dataset, DLP classifies and policy tags are set before anything lands in Bronze. Its exit is a hard gate: zero unauthorized PHI access in security tests before any agent connects.
- Phase 2: the data foundation, boxes 1, 3, 4, 5, 6, overlapping Phase 1, synthetic first: approved, tagged sources into Bronze, then Silver and Gold.
- Phase 3: the knowledge graph, Tableau and agents on Gold A, boxes 7-9. It can start on synthetic Gold A while Phase 2 finishes.
- Phase 4: build and test the journey with test contacts only, boxes 10-12.
- Phase 5: governed activation, boxes 13-19: Data Cloud first, the direct path only after parity; a pilot on synthetic data, then a small real audience.
- Phase 6: measurement, box 20, compared with the Phase 0 baseline. Only here do we state speed and ROI numbers; then we scale to more campaigns.

THREE RULES
Governance before agents. Build and test before release. Data Cloud before direct."""

PHASES = [("0", "Discovery", "before 1",
           ["BigQuery inventory, PHI classifications, Collibra owners, refresh rates",
            "Map today's CHF campaign end to end", "BAAs, Salesforce licences, G1-G3 signers",
            "Measure today's CHF process"], "Approved architecture, owners, a baseline", CYAN),
          ("1", "PHI governance", "2",
           ["Collibra steward approves each dataset before ingest",
            "DLP classification, policy tags, masking, row access",
            "Separate service identities; fail-closed policy removal", "Negative-access tests"],
           "Approved and tagged before ingest; zero unauthorized PHI access in tests", MAGENTA),
          ("2", "Data foundation", "1 · 3 · 4 · 5 · 6",
           ["Approved, tagged sources into Bronze", "Silver: identities, encounters, contacts, consent; keeps everyone",
            "Gold B (restricted) and Gold A (aggregates)", "Synthetic data first"],
           "Data contracts, refresh times, quality checks pass", MAGENTA),
          ("3", "Agentic intelligence", "6 → 7 · 8 · 9",
           ["Knowledge graph and Tableau on Gold A only", "Codex prompt; Orchestrator, Strategist, Analytics",
            "Opportunity Brief and G1"], "A CHF brief from counts only, approved", VIO),
          ("4", "Build + test", "10 · 11 · 12",
           ["Campaign Design Agent: journey + data extension, paused",
            "Testing loop: test contacts, failure modes, 5-retry cap", "G3 approval flow"],
           "CHF journey built, tested, approved; no real patient", GREEN),
          ("5", "Governed activation", "13 → 19",
           ["Eligibility service on Gold B", "G2 masked pre-send report", "Gateway + Compliance Passport",
            "Path A (Data Cloud) first; Path B after parity", "Pilot: synthetic, then a small real audience"],
           "Real CHF audience, equal or stronger controls; release reconciles", YELLOW),
          ("6", "Measure + scale", "20 + feedback",
           ["Measurement vs holdout; refresh Gold A", "Compare with the Phase 0 baseline: first real speed and ROI",
            "More templates, Path B, monitoring, multi-tenancy"], "A multi-campaign accelerator", CYAN)]


def build_order(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "AGENTIC HEALTHCARE CAMPAIGN PLATFORM · BUILD ORDER",
                "How we build it: safeguards first, release last",
                "The 1-20 numbers are the order a campaign runs. We build in this order, so every safeguard exists "
                "and release is proven on synthetic data before any real patient moves.")
    w = (12.43 - 6 * 0.08) / 7
    for k, (n, t, boxes, work, exit_, c) in enumerate(PHASES):
        x = 0.45 + k * (w + 0.08)
        cv.rect(x, 1.3, w, 0.36, c, None, shape=MSO_SHAPE.CHEVRON if k else MSO_SHAPE.PENTAGON)
        tc = ON_COLOR if c in (MAGENTA, VIO) else BLACK
        cv.text(x + (0.26 if k else 0.12), 1.3, w - 0.36, 0.36, [[("PHASE " + n + "  ", {"bold": True}),
                                                                 (t, {"bold": True})]], size=6.2, color=tc,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.rect(x, 1.74, w, 3.36, CARD, c, 1.0, R, 0.04)
        cv.text(x + 0.1, 1.8, w - 0.2, 0.18, "BOXES ON THE SLIDE", size=4.8, bold=True, color=DIM, track=100,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.rect(x + 0.1, 2.0, w - 0.2, 0.26, TINT.get(c, CARD2), c, 0.75, R, 0.3)
        cv.text(x + 0.1, 2.0, w - 0.2, 0.26, boxes, size=7.4, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        step = min(0.62, 1.92 / len(work))          # spread the bullets over the column
        for j, line in enumerate(work):
            y = 2.36 + j * step
            cv.rect(x + 0.1, y + 0.09, 0.07, 0.07, c, None, shape=MSO_SHAPE.OVAL)
            cv.text(x + 0.22, y, w - 0.28, step - 0.02, line, size=7.0, color=WHITE)
        cv.rect(x + 0.08, 4.32, w - 0.16, 0.72, CARD2, None, shape=R, radius=0.1)
        cv.text(x + 0.14, 4.32, w - 0.24, 0.72, [[("EXIT  ", {"bold": True, "color": c, "size": 5.8})],
                                                 [(exit_, {"bold": True, "color": WHITE})]], size=7.0,
                anchor=MSO_ANCHOR.MIDDLE, after=1)
    # markers under the phases
    x1 = 0.45 + 1 * (w + 0.08)
    x3 = 0.45 + 3 * (w + 0.08)
    x5 = 0.45 + 5 * (w + 0.08)
    cv.rect(x1 + 0.1, 5.2, 2 * w + 0.08 - 0.2, 0.2, None, MAGENTA, 1.0, R, 0.5, dash="dash")
    cv.text(x1 + 0.1, 5.2, 2 * w + 0.08 - 0.2, 0.2, "PHASES 1 + 2 RUN PARTLY IN PARALLEL", size=5, bold=True,
            color=MAGENTA, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=80)
    pill(cv, x1 + w - 0.55, 1.2, 1.0, "HARD GATE", MAGENTA, True, h=0.16, size=5, tcolor=ON_COLOR)
    cv.rect(x3 + 0.1, 5.2, w - 0.2, 0.2, None, VIO, 1.0, R, 0.5, dash="dash")
    cv.text(x3 + 0.1, 5.2, w - 0.2, 0.2, "SYNTHETIC GOLD A FIRST", size=4.6, bold=True, color=VIO,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(x5 + 0.1, 5.2, w - 0.2, 0.2, YELLOW, None, shape=R, radius=0.5)
    cv.text(x5 + 0.1, 5.2, w - 0.2, 0.2, "FIRST REAL PATIENTS", size=4.8, bold=True, color=BLACK,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=80)
    # three rules
    rules = [("Governance before agents", "No data lands and no agent connects until governance passes its tests "
              "(Phase 1 exit).", MAGENTA),
             ("Build and test before release", "The data extension starts the journey by itself, so the journey is "
              "ready first (Phase 4 before 5).", GREEN),
             ("Data Cloud before direct", "Keep today's proven route until the direct path passes parity and "
              "security review.", CYAN)]
    rw = (12.43 - 2 * 0.12) / 3
    cv.text(0.45, 5.52, 4, 0.2, "THREE RULES SET THIS ORDER", size=6.2, bold=True, color=WHITE, track=120,
            anchor=MSO_ANCHOR.MIDDLE)
    for k, (t, d, c) in enumerate(rules):
        x = 0.45 + k * (rw + 0.12)
        cv.rect(x, 5.78, rw, 0.66, CARD, None)
        cv.rect(x, 5.78, 0.05, 0.66, c, None)
        cv.text(x + 0.18, 5.78, rw - 0.26, 0.66, [[(t, {"bold": True, "size": 7.6, "color": WHITE})],
                                                  [(d, {"color": SOFT})]], size=6.2, anchor=MSO_ANCHOR.MIDDLE,
                after=1)
    cv.text(0.45, 6.5, 12.43, 0.3, [[("Nothing in Phase 5 touches real patients until Phases 1 and 4 pass their "
                                      "exits. ", {"bold": True, "color": WHITE}),
                                     ("No speed or ROI number is committed before Phase 6 compares the pilot with "
                                      "today's baseline.", {"color": SOFT})]], size=6.6, anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, BUILD_NOTES)
    return s


GOV_NOTES = """SLIDE: PHI governance: masking is one control, not HIPAA compliance   (about 3 minutes)

KEY MESSAGE
The classification-and-approval flow stays: DLP classifies, a Collibra steward approves, policies protect the columns and bindings prove it. But column masking only controls who sees a value. On its own it does not make data de-identified, establish permitted use, isolate tenants, or complete the HIPAA controls, so we add all four.

WALK IT
- Top left: today's flow, with its status. DLP and Collibra are upstream, the reviewed table, rollout gate and bindings are built, the tagger and policies are live in DEV. The rejected path is now fail-closed: rejecting a classification never removes existing protection.
- Top right: three different things. Masking hides values from readers without access; the data underneath is still PHI. Tokenization can still be PHI, depending on linkability. Only HIPAA de-identification (Safe Harbor or Expert Determination) can take data out of PHI status.
- Bottom, the four additions:
  1 Safe de-identification: assess agent-facing data under Safe Harbor or Expert Determination; measure re-identification risk at column, row, combination and aggregate level; agents get aggregates by default.
  2 Permitted use: privacy-approved purpose and authorization rules per campaign, as policy-as-code; consent and restrictions checked at release and again at send; the Compliance Passport records it.
  3 Tenant isolation: per-customer projects, datasets, keys and identities; tenant-specific policies, retention and audit; no cross-tenant joins.
  4 Complete HIPAA controls: a compliance control register mapping evidence to the Privacy, Security and Breach Notification Rule safeguards: BAAs, risk analysis, workforce training, access reviews, incident and breach handling.
- Strip: how we prove it works, and a reminder that PROPOSED items are design, not production evidence."""

GAPS4 = [("Safe de-identification", "A masked or tokenized row can still identify a patient: dates, rare diagnoses, "
          "facility, geography.",
          ["Safe Harbor or Expert Determination assessment for agent-facing data",
           "Re-identification risk at column, row, combination and aggregate level; small-cell suppression",
           "Agents get aggregates by default; tokenized rows only for an authorized task"], YELLOW),
         ("Permitted use", "Having the data is not permission to use it for a campaign.",
          ["Privacy-approved purpose and authorization rules per campaign, as policy-as-code",
           "Consent and communication restrictions checked at release and again at send",
           "Campaign Compliance Passport records purpose, rule version and approvals"], MAGENTA),
         ("Tenant isolation", "A product for many healthcare organizations cannot mix their PHI or policies.",
          ["Per-customer projects, datasets, CMEK keys and service identities",
           "Tenant-specific policies, retention and audit boundaries",
           "No cross-tenant joins; proven with negative-access tests"], CYAN),
         ("Complete HIPAA controls", "Technical controls and audit evidence are not compliance on their own.",
          ["Compliance control register: evidence mapped to Privacy, Security and Breach Notification safeguards",
           "BAAs, risk analysis, workforce training, access reviews",
           "Incident and breach handling; independent approval to weaken any policy"], GREEN)]


def phi_governance(prs, layout):
    from final_solution import ORANGE, addg_flow
    s, cv = new_slide(prs, layout)
    dark_header(cv, "AGENTIC HEALTHCARE CAMPAIGN PLATFORM · PHI GOVERNANCE",
                "Classification and approval stay. Masking alone is not HIPAA compliance.",
                "Column masking controls who sees a value. It does not by itself give safe de-identification, "
                "permitted use, tenant isolation or complete HIPAA controls, so we add all four.")
    addg_flow(cv, 0.45, 7.6, 1.3)
    rx, rw = 7.78, 12.88 - 7.78
    cv.rect(rx, 1.3, rw, 2.72, CARD, EDGE_, 0.75, R, 0.04)
    cv.text(rx + 0.12, 1.34, rw - 0.24, 0.24, "MASKED IS NOT DE-IDENTIFIED", size=6.4, bold=True, color=YELLOW,
            track=120, anchor=MSO_ANCHOR.MIDDLE)
    colx = [rx + 0.12, rx + 1.35, rx + 3.05]
    colw = [1.2, 1.65, rw - 3.12]
    for x, w, t in zip(colx, colw, ["", "What it does", "HIPAA implication"]):
        cv.text(x, 1.62, w, 0.18, t, size=5.6, bold=True, color=DIM)
    rows = [("Masking", "Hides values from readers without access", "An access control; the data underneath is "
             "still PHI", MAGENTA),
            ("Tokenization", "Replaces identifiers; reversible through a separate map", "Can still be PHI, "
             "depending on linkability and context", ORANGE),
            ("De-identification", "Safe Harbor or Expert Determination met", "Can leave PHI status when the "
             "standard is met", GREEN)]
    for k, (a, b, c, col) in enumerate(rows):
        y = 1.84 + k * 0.56
        cv.rect(rx + 0.08, y, rw - 0.16, 0.5, CARD2, None)
        cv.rect(rx + 0.08, y, 0.05, 0.5, col, None)
        cv.text(colx[0] + 0.06, y, colw[0], 0.5, a, size=6.6, bold=True, color=col, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(colx[1], y, colw[1], 0.5, b, size=5.8, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(colx[2], y, colw[2], 0.5, c, size=5.8, color=SOFT, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(rx + 0.12, 3.52, rw - 0.24, 0.46, [[("A token, a count, a diagnosis combination or a small cohort can "
                                                 "remain sensitive. ", {"color": WHITE}),
                                                ("Each is assessed, not assumed safe.", {"bold": True,
                                                                                       "color": YELLOW})]],
            size=6, anchor=MSO_ANCHOR.MIDDLE)
    gy = 4.3
    cv.text(0.45, gy, 9, 0.22, [[("WHAT MASKING ALONE DOES NOT GIVE US, AND WHAT WE ADD", {"bold": True,
                                                                                       "track": 120,
                                                                                       "color": VIO}),
                                 ("   proposed design", {"color": SOFT})]], size=6.4, anchor=MSO_ANCHOR.MIDDLE)
    cw = (12.43 - 3 * 0.12) / 4
    for k, (t, gap, adds, c) in enumerate(GAPS4):
        x = 0.45 + k * (cw + 0.12)
        y = gy + 0.28
        h = 1.68
        cv.rect(x, y, cw, h, CARD, c, 1.0, R, 0.05)
        cv.rect(x, y, cw, 0.3, c, None)
        cv.text(x + 0.1, y, cw - 0.9, 0.3, [[("%d  " % (k + 1), {"bold": True}), (t, {"bold": True})]], size=7.2,
                color=ON_COLOR if c == MAGENTA else BLACK, anchor=MSO_ANCHOR.MIDDLE)
        pill(cv, x + cw - 0.92, y + 0.07, 0.82, "PROPOSED", ON_COLOR if c == MAGENTA else BLACK, h=0.16,
             size=4.6)
        cv.text(x + 0.1, y + 0.34, cw - 0.2, 0.34, [[("Gap: ", {"bold": True, "color": WHITE}), (gap, {})]],
                size=5.8, color=SOFT)
        for j, a in enumerate(adds):
            yy = y + 0.72 + j * 0.31
            cv.rect(x + 0.12, yy + 0.07, 0.06, 0.06, c, None, shape=MSO_SHAPE.OVAL)
            cv.text(x + 0.24, yy, cw - 0.32, 0.3, a, size=5.7, color=WHITE)
    ey = 6.35
    cv.rect(0.45, ey, 12.43, 0.46, TINT[GREEN], GREEN, 0.9, R, 0.2)
    cv.text(0.6, ey, 12.1, 0.46, [[("HOW WE PROVE IT  ", {"bold": True, "color": GREEN, "track": 100}),
                                   ("Discovery inventory across the approved scope · row-level security and authorized "
                                    "views with masking · raw access isolated from the LLM runtime · negative-access "
                                    "tests · drift detection · periodic access review. ", {"color": WHITE}),
                                   ("PROPOSED items are design, not production evidence.", {"bold": True,
                                                                                          "color": WHITE})]],
            size=5.9, anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, GOV_NOTES)
    return s
