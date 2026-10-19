"""One slide: governed campaign data, from classified BigQuery columns to a Marketing Cloud data extension.

Sources: the ADDG governance flow (DLP -> Collibra steward -> tagger -> column policies) and the campaign
activation deck (campaign mart -> Looker approval -> Cloud Run activator -> Marketing Cloud, outcomes back).

    python3 governance_slide.py [out.pptx]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "..", "deck")
sys.path.insert(0, DECK)

from pptx import Presentation                                    # noqa: E402
from pptx.enum.shapes import MSO_SHAPE                            # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN                   # noqa: E402

from build_mad_ig_deck import (BLACK, CYAN, CYAN_T, GREEN, GREY, MAGENTA, MUTE, NAVY, VIOLET, VIOLET_T,  # noqa: E402
                               WHITE, YELLOW, YELLOW_T, Canvas, set_notes)

RULE_C = "D9D9D9"
TEMPLATE = os.path.join(DECK, "source", "Ascension Agentic Harness - final.pptx")
OUT = os.path.join(HERE, "Campaign Data Governance.pptx")
R = MSO_SHAPE.ROUNDED_RECTANGLE
CYAN_D, GOLD, INK, ORANGE = "0097AD", "C9A800", "2B2B2B", "FA8B35"
STATUS = {"UPSTREAM": (WHITE, MUTE, MUTE), "BUILT": (GREEN, GREEN, WHITE), "LIVE IN DEV": (CYAN, CYAN, BLACK),
          "IN PROGRESS": (ORANGE, ORANGE, WHITE)}

CX = [0.6 + i * 2.27 for i in range(4)]       # four columns inside the GCP boundary
CW, NH = 2.06, 0.72

NOTES = """SLIDE: Governed data first: how campaign data is protected before Marketing Cloud ever sees it   (about 4 minutes)

KEY MESSAGE
Before any campaign runs, the data is governed in Google Cloud. Every column is classified, approved by a data steward and protected inside BigQuery. Only a minimum-necessary, tokenized audience is approved in Looker and published to an outbound bucket, from which Marketing Cloud pulls it into a data extension. PHI never leaves Google Cloud, and every visit booked comes back inside to prove the result.

WALK IT
1 Govern the data (ADDG, top band)
- Cloud DLP scans the BigQuery columns in the production projects and proposes an infotype for each one.
- A data steward approves or rejects each classification in Collibra; nothing changes before that sign-off.
- Outcomes sync into one reviewed-classifications table, the single list every job works from.
- A rollout gate enables production project by project; a person runs each promotion.
- The Data Policy Tagger (Cloud Run job, dry-run first) applies column policies: SHA-256 masking or raw-access only.
- Every applied policy is recorded as a binding and checked against the live schema. If a steward rejects, the policy remover clears it and the binding is retired.

2 Build the audience
- Authorized views apply the campaign criteria on policy-tagged data.
- The campaign mart holds one table per campaign: tokenized member ID, channel, segment, eligibility flags and run ID. No names, dates of birth or diagnoses.
- A quality gate blocks the run if a new column is untagged or a source is stale.
- In Looker, a named approver reviews audience size, segments and exclusions and approves.

3 Publish, and Marketing Cloud pulls
- After approval, a Cloud Run job re-checks consent and suppression and writes one tokenized file per run ID to an outbound Cloud Storage bucket (CMEK, files expire).
- Marketing Cloud pulls it: an Automation Studio scheduled import reads the file with a read-only key and loads the campaign data extension. Nothing is pushed out of Google Cloud; Marketing Cloud can read only that bucket.
- Marketing Cloud sends through Journey Builder with consent, frequency caps and STOP handling. Messages carry no clinical wording and no identifiers in links.
- Booked visits come back into BigQuery outcome tables, inside the boundary, and are measured as lift against a random holdout.

STATUS (from the ADDG flow)
DLP and Collibra are upstream. The reviewed-classifications table, rollout gate and bindings are built. The tagger and the column policies are live in DEV. The policy remover is in progress.

DECISIONS TO CONFIRM
- Which Marketing Cloud products and SMS vendors are under Ascension's BAA.
- Pull through an Automation Studio file import (this design) or through Data Cloud zero-copy on BigQuery.
- One approver, or a second approver above a set audience size.
- A random holdout to prove lift, or report bookings only."""


def node(cv, x, y, w, h, title, body, status=None, fill=WHITE, line=NAVY, dash=None, lw=0.9):
    cv.rect(x, y, w, h, fill, line, lw, R, 0.08, dash=dash)
    tw = w - 0.16
    if status:
        f, ln, col = STATUS[status]
        sw = 0.14 + 0.055 * len(status)
        cv.rect(x + w - sw - 0.07, y + 0.07, sw, 0.15, f, ln, 0.5, R, 0.5)
        cv.text(x + w - sw - 0.07, y + 0.07, sw, 0.15, status, size=4.8, bold=True, color=col,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=60)
        tw -= sw + 0.05
    cv.text(x + 0.09, y + 0.05, tw, 0.2, title, size=7.6, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(x + 0.09, y + 0.26, w - 0.18, h - 0.29, body, size=6.1, color=INK)


def path(cv, pts, color=NAVY, w=1.25, dash=None):
    for k, (p, q) in enumerate(zip(pts, pts[1:])):
        cv.arrow(p[0], p[1], q[0], q[1], color, w, dash=dash, head=(k == len(pts) - 2))


def tag(cv, x, y, w, t, fill=BLACK, color=WHITE):
    cv.rect(x, y, w, 0.17, fill, None, shape=R, radius=0.5)
    cv.text(x, y, w, 0.17, t, size=5.6, bold=True, color=color, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
            track=60)


def lane(cv, y, h, fill, line, num, title, sub, x0=0.6):
    cv.rect(0.52, y, 8.98, h, fill, line, 0.75, R, 0.03)
    cv.rect(x0, y + 0.06, 0.2, 0.2, line, None, MSO_SHAPE.OVAL)
    cv.text(x0, y + 0.06, 0.2, 0.2, str(num), size=7, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(x0 + 0.26, y + 0.05, 9.4 - x0 - 0.26, 0.22, [[(title, {"bold": True, "track": 150}), ("   " + sub, {"color": MUTE})]],
            size=7, anchor=MSO_ANCHOR.MIDDLE)


def governance_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION · CAMPAIGN DATA GOVERNANCE",
              "Detailed design: from classified columns to the data extension Marketing Cloud pulls",
              "PHI stays in Google Cloud. Every column is classified, steward-approved and protected before a "
              "campaign uses it; Marketing Cloud gets only a tokenized, approved audience.")

    # ------------------------------------------------------------ the GCP PHI boundary
    cv.rect(0.45, 1.27, 9.12, 4.87, None, NAVY, 1.25, R, 0.02, dash="dash")
    cv.text(0.6, 1.3, 9.0, 0.24, [[("GOOGLE CLOUD · PHI BOUNDARY", {"bold": True, "track": 150}),
                                   ("   VPC Service Controls · CMEK · audit logs to a locked sink · no direct "
                                    "marketing access", {"color": MUTE})]], size=7, anchor=MSO_ANCHOR.MIDDLE)

    # lane 1: govern the data (ADDG)
    lane(cv, 1.58, 2.04, VIOLET_T, VIOLET, 1, "GOVERN THE DATA · ADDG",
         "classify, approve, protect, prove: governance tier asc-ahnat-datarepository")
    r1, r2 = 1.88, 2.82
    node(cv, CX[0], r1, CW, NH, "Source data",
         "17 production projects in BigQuery (asc-datalake): clinical and engagement tables.", line=VIOLET)
    node(cv, CX[1], r1, CW, NH, "DLP classification",
         "Cloud DLP scans every column and proposes an infotype: name, DOB, MRN, phone.", "UPSTREAM", line=VIOLET)
    node(cv, CX[2], r1, CW, NH, "Steward review · Collibra",
         "A data steward approves or rejects each classification. Nothing changes before.", "UPSTREAM",
         fill=YELLOW_T, line=GOLD, lw=1.5)
    node(cv, CX[3], r1, CW, NH, "Reviewed classifications",
         "One governed table, keyed by project, dataset, table and column: the single list.", "BUILT",
         line=VIOLET)
    node(cv, CX[3], r2, CW, NH, "Rollout gate · per project",
         "Production enabled project by project; a person runs every promotion.", "BUILT",
         fill=YELLOW_T, line=GOLD, dash="dash", lw=1.25)
    node(cv, CX[2], r2, CW, NH, "Data Policy Tagger",
         "Cloud Run job, per-environment config, dry-run first. Decides each column's policy.", "LIVE IN DEV",
         line=VIOLET)
    node(cv, CX[1], r2, CW, NH, "Column policies",
         "In BigQuery: SHA-256 masking or raw-access only. If rejected, the policy remover (in progress) clears it.",
         "LIVE IN DEV",
         fill=CYAN_T, line=CYAN_D, lw=1.25)
    node(cv, CX[0], r2, CW, NH, "Bindings + validation",
         "Every policy recorded and read back from the live schema: the audit trail.", "BUILT", line=VIOLET)
    ym1, ym2 = r1 + NH / 2, r2 + NH / 2
    for i in range(3):
        cv.arrow(CX[i] + CW, ym1, CX[i + 1], ym1, VIOLET, 1.25)
    path(cv, [(CX[3] + CW / 2, r1 + NH), (CX[3] + CW / 2, r2)], VIOLET)
    for i in (3, 2, 1):
        cv.arrow(CX[i], ym2, CX[i - 1] + CW, ym2, VIOLET, 1.25)
    tag(cv, CX[2] + 0.3, r1 + NH + 0.04, 1.46, "REJECTED → POLICY REMOVED", WHITE, MAGENTA)

    # lane 2: build the audience
    lane(cv, 3.72, 1.06, CYAN_T, CYAN_D, 2, "BUILD THE AUDIENCE", "minimum necessary, from protected data only",
         x0=CX[2] - 0.5)
    a2 = 3.98
    node(cv, CX[0], a2, CW, NH, "Authorized views",
         "Campaign criteria on policy-tagged data. Masked columns stay masked.", line=CYAN_D)
    node(cv, CX[1], a2, CW, NH, "Campaign mart",
         "One table per campaign; row-level security, CMEK, DLP scan, partitioned by run.", line=CYAN_D)
    node(cv, CX[2], a2, CW, NH, "Quality gate",
         "Blocks the run if a column is untagged or a source is stale (tagger + CI check).",
         fill=YELLOW_T, line=GOLD, dash="dash", lw=1.25)
    node(cv, CX[3], a2, CW, NH, "Approve in Looker",
         "Audience size, segments, exclusions. A named approver clicks Approve.", fill=YELLOW_T, line=GOLD, lw=1.5)
    for i in range(3):
        cv.arrow(CX[i] + CW, a2 + NH / 2, CX[i + 1], a2 + NH / 2, CYAN_D, 1.25)
    # governance feeds the audience
    path(cv, [(CX[0] + CW / 2, r2 + NH), (CX[0] + CW / 2, a2)], VIOLET, 1.75)
    tag(cv, CX[0] + CW / 2 + 0.1, 3.77, 1.95, "ONLY PROTECTED COLUMNS FLOW ON", VIOLET)

    # lane 3: publish and measure
    lane(cv, 4.88, 1.13, GREY, MUTE, 3, "PUBLISH AND MEASURE", "approved file out, outcomes back in")
    a3 = 5.14
    node(cv, CX[0], a3, CW, NH, "Lift vs holdout",
         "Nudged group against a random holdout: lift and contribution margin, not raw counts.", line=MUTE)
    node(cv, CX[1], a3, CW, NH, "Outcome tables",
         "Booked visits (Epic, Athena) matched to the run, back inside the boundary.", line=MUTE)
    node(cv, CX[2], a3, CW, NH, "Approved extract",
         "Cloud Run job after approval: re-checks consent and suppression, writes one file per run ID.",
         line=NAVY, lw=1.25)
    cv.rect(CX[3], a3, CW, NH, WHITE, NAVY, 1.5, R, 0.08, dash="sysDot")
    cv.text(CX[3] + 0.09, a3 + 0.05, CW - 0.18, NH - 0.08,
            [[("Outbound bucket · GCS", {"bold": True, "size": 7.6})],
             [("Tokenized fields only; read-only key for Marketing Cloud; CMEK; files expire.", {"size": 6.1})],
             [("never name, DOB, diagnosis or MRN", {"size": 6.1, "bold": True, "color": MAGENTA})]], size=6.1,
            after=1)
    path(cv, [(7.7, a2 + NH), (7.7, 5.0), (CX[2] + CW / 2, 5.0), (CX[2] + CW / 2, a3)], GOLD, 1.5)
    cv.arrow(CX[2] + CW, a3 + NH / 2, CX[3], a3 + NH / 2, NAVY, 1.5)
    cv.arrow(CX[1], a3 + NH / 2, CX[0] + CW, a3 + NH / 2, MUTE, 1.25)
    tag(cv, 7.85, 4.93, 1.58, "MARKETING CLOUD PULLS \u2192", BLACK)

    # ------------------------------------------------------------ Marketing Cloud, outside the boundary
    mx, mw = 9.75, 3.13
    cv.rect(mx, 1.27, mw, 0.3, BLACK)
    cv.text(mx + 0.1, 1.27, mw - 0.2, 0.3, [[("MARKETING CLOUD", {"bold": True, "track": 150}),
                                            ("   outside the boundary", {"color": "BFBFBF"})]],
            size=7, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(mx, 1.57, mw, 4.57, WHITE, MUTE, 0.75)
    nx, nw = mx + 0.1, mw - 0.2
    node(cv, nx, 1.68, nw, 0.62, "Automation Studio · scheduled import",
         "Pulls the approved file from the outbound bucket with a read-only key. Nothing is pushed out of GCP.",
         fill=CYAN_T, line=CYAN_D, lw=1.5)
    # the data extension: where the pulled audience lands
    fx, fy, fw, fh = cv.frame(nx, 2.44, nw, 1.36, WHITE, 0.04)
    cv.text(fx + 0.1, fy + 0.04, fw - 0.2, 0.22, "Campaign data extension", size=8.5, bold=True,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.1, fy + 0.25, fw - 0.2, 0.18, "The pulled audience lands here: tokenized IDs only.", size=6.2,
            color=MUTE)
    fields = [("SubscriberKey", "member token"), ("Channel", "SMS / email"), ("Segment", "campaign variant"),
              ("Send window", "send-time fields"), ("RunID", "ties back to the approval")]
    for i, (f_, d_) in enumerate(fields):
        yy = fy + 0.45 + i * 0.165
        cv.text(fx + 0.12, yy, 0.95, 0.16, f_, size=6.2, bold=True, font="Courier New", anchor=MSO_ANCHOR.MIDDLE)
        cv.text(fx + 1.08, yy, fw - 1.2, 0.16, d_, size=6.1, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    node(cv, nx, 3.94, nw, 0.55, "Journey Builder",
         "Timing, frequency caps, variants. Consent and STOP re-checked at send.", line=NAVY)
    node(cv, nx, 4.6, nw, 0.55, "Patient nudge · SMS or email",
         "No clinical wording, no identifiers in links (TCPA consent).", line=NAVY)
    node(cv, nx, 5.26, nw, 0.52, "Visit booked",
         "Online or by phone; AWV billed as G0438 / G0439.", line=NAVY)
    for y1, y2 in ((2.3, 2.44), (3.8, 3.94), (4.49, 4.6), (5.15, 5.26)):
        cv.arrow(nx + nw / 2, y1, nx + nw / 2, y2, NAVY, 1.25)

    # the pull: Marketing Cloud reads the approved file from the bucket (data flows bucket -> import)
    path(cv, [(CX[3] + CW, a3 + NH / 2), (9.66, a3 + NH / 2), (9.66, 1.99), (nx, 1.99)], BLACK, 2.0)
    # outcomes back inside
    by = 5.98
    path(cv, [(nx + 0.4, 5.78), (nx + 0.4, by), (CX[1] + CW / 2, by), (CX[1] + CW / 2, a3 + NH)], GREEN, 1.75)
    tag(cv, 5.3, by - 0.085, 2.05, "\u2190 BOOKED VISITS BACK INSIDE", GREEN)

    # ------------------------------------------------------------ built-in controls
    cy = 6.24
    cv.text(0.45, cy, 1.35, 0.6, [[("BUILT-IN", {"bold": True, "track": 150})], [("CONTROLS", {"bold": True,
                                                                                         "track": 150})]],
            size=7, anchor=MSO_ANCHOR.MIDDLE)
    controls = [("Steward approval first", "no policy before Collibra sign-off"),
                ("Dry run before apply", "every run can report without changing"),
                ("Human-gated promotion", "project by project; never self-promotes"),
                ("Auditable bindings", "each policy recorded and verified"),
                ("Named approver", "Looker approval before any file is published"),
                ("Pull, read-only", "Marketing Cloud pulls tokenized fields only")]
    gw = (12.88 - 1.85 - 5 * 0.1) / 6
    for i, (t_, d_) in enumerate(controls):
        x = 1.85 + i * (gw + 0.1)
        cv.rect(x, cy, gw, 0.6, WHITE, GREEN if i < 4 else GOLD, 0.75, R, 0.1)
        cv.rect(x, cy, 0.05, 0.6, GREEN if i < 4 else GOLD)
        cv.text(x + 0.12, cy + 0.05, gw - 0.18, 0.52, [[(t_, {"bold": True, "size": 7})], [(d_, {"color": MUTE})]],
                size=6.1, after=1, anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, NOTES)
    return s


HL_NOTES = """SLIDE: Governed campaign data, the high-level view   (about 2 minutes)

KEY MESSAGE
To run a campaign we need the right data, and in healthcare that means governed data first. The data is governed, shaped and approved inside Google Cloud; Marketing Cloud only pulls an approved, tokenized file. PHI never leaves Google Cloud.

WALK IT (left to right)
1 Govern the data: DLP finds every sensitive column, a data steward approves it in Collibra, and BigQuery masks it or limits raw access. Every policy is audited.
2 Build the audience: views on protected data only, one campaign table with the minimum fields, and a quality gate that stops the run if anything is untagged or stale.
3 Approve and publish: a named approver signs off in Looker; only then is an approved, tokenized file published to an outbound bucket.
4 Marketing Cloud pulls: a scheduled import pulls that file into the campaign data extension; Journey Builder sends.
Measure: booked visits come back inside Google Cloud and are measured as lift against a holdout.

The next slide shows the detailed design."""


def high_level_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION · CAMPAIGN DATA GOVERNANCE",
              "Governed data first: Marketing Cloud pulls only what has been approved",
              "Data is governed, shaped and approved inside Google Cloud. Marketing Cloud pulls a tokenized, "
              "approved file. PHI never leaves.")
    # boundary
    cv.rect(0.45, 1.3, 9.2, 4.48, None, NAVY, 1.25, R, 0.02, dash="dash")
    cv.text(0.62, 1.34, 9.0, 0.24, [[("GOOGLE CLOUD · PHI BOUNDARY", {"bold": True, "track": 150}),
                                    ("   PHI stays here", {"color": MUTE})]], size=7.5, anchor=MSO_ANCHOR.MIDDLE)
    stages = [
        (1, "GOVERN THE DATA", "ADDG", VIOLET, VIOLET_T,
         [("DLP classifies every column", False), ("Data steward approves · Collibra", True),
          ("Policies applied in BigQuery: mask or raw access", False)],
         "Every sensitive column protected and audited"),
        (2, "BUILD THE AUDIENCE", "minimum necessary", CYAN_D, CYAN_T,
         [("Views on protected data only", False), ("Campaign mart: one table per campaign", False),
          ("Quality gate: untagged or stale blocks", True)],
         "A tokenized, minimum-necessary audience"),
        (3, "APPROVE AND PUBLISH", "people decide", GOLD, YELLOW_T,
         [("Named approver signs off in Looker", True), ("Approved extract: consent re-checked", False),
          ("Outbound bucket: Marketing Cloud pulls, read-only", False)],
         "One approved file per run, tokenized IDs only"),
    ]
    cw, ch, y0 = 2.83, 3.75, 1.7
    xs = [0.62 + i * (cw + 0.2) for i in range(3)]
    for x, (n, title, sub, col, tint, steps, out) in zip(xs, stages):
        cv.rect(x, y0, cw, ch, WHITE, col, 1.5, R, 0.04)
        cv.rect(x, y0, cw, 0.62, tint, None, shape=R, radius=0.12)
        cv.rect(x + 0.14, y0 + 0.16, 0.3, 0.3, col, None, MSO_SHAPE.OVAL)
        cv.text(x + 0.14, y0 + 0.16, 0.3, 0.3, str(n), size=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.52, y0 + 0.1, cw - 0.6, 0.42, [[(title, {"bold": True, "track": 120, "size": 9})],
                                                   [(sub, {"color": MUTE, "size": 7})]], size=8,
                anchor=MSO_ANCHOR.MIDDLE)
        sy = y0 + 0.82
        for k, (t, gate) in enumerate(steps):
            cv.rect(x + 0.18, sy, cw - 0.36, 0.56, YELLOW_T if gate else WHITE, GOLD if gate else RULE_C,
                    1.25 if gate else 0.75, R, 0.15, dash="dash" if gate else None)
            cv.text(x + 0.3, sy, cw - 0.6, 0.56, t, size=8.5, bold=gate, anchor=MSO_ANCHOR.MIDDLE)
            if k < len(steps) - 1:
                cv.arrow(x + cw / 2, sy + 0.56, x + cw / 2, sy + 0.72, col, 1.25)
            sy += 0.72
        cv.rect(x + 0.18, y0 + ch - 0.62, cw - 0.36, 0.46, col, None, shape=R, radius=0.2)
        cv.text(x + 0.25, y0 + ch - 0.62, cw - 0.5, 0.46, out, size=7.5, bold=True,
                color=BLACK if col == GOLD else WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    for i in range(2):
        cv.arrow(xs[i] + cw + 0.02, y0 + ch / 2, xs[i + 1] - 0.02, y0 + ch / 2, NAVY, 2.25)

    # Marketing Cloud pulls
    mx, mw = 9.85, 3.03
    cv.rect(mx, 1.3, mw, 0.34, BLACK)
    cv.text(mx + 0.1, 1.3, mw - 0.2, 0.34, [[("4  MARKETING CLOUD PULLS", {"bold": True, "track": 120})]],
            size=8, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(mx, 1.64, mw, 4.14, WHITE, MUTE, 0.75)
    msteps = [("Scheduled import", "pulls the approved file, read-only", CYAN_T, CYAN_D),
              ("Campaign data extension", "tokenized IDs and send-time fields", WHITE, BLACK),
              ("Journey Builder", "consent, frequency caps, STOP", WHITE, NAVY),
              ("SMS or email nudge", "no clinical wording, no identifiers", WHITE, NAVY)]
    my = 1.78
    for k, (t, d, f, ln) in enumerate(msteps):
        if k == 1:
            fx, fy, fw, fh = cv.frame(mx + 0.15, my, mw - 0.3, 0.7, WHITE, 0.04)
        else:
            cv.rect(mx + 0.15, my, mw - 0.3, 0.7, f, ln, 1.25, R, 0.12)
        cv.text(mx + 0.28, my + 0.05, mw - 0.56, 0.62, [[(t, {"bold": True, "size": 9})], [(d, {"color": MUTE})]],
                size=7, anchor=MSO_ANCHOR.MIDDLE, after=1)
        if k < len(msteps) - 1:
            cv.arrow(mx + mw / 2, my + 0.7, mx + mw / 2, my + 0.86, NAVY, 1.25)
        my += 0.86
    # the pull, from the published file into the import
    path(cv, [(xs[2] + cw, y0 + 0.82 + 2 * 0.72 + 0.28), (9.75, y0 + 0.82 + 2 * 0.72 + 0.28), (9.75, 2.13),
              (mx + 0.15, 2.13)], BLACK, 2.25)
    # measure: outcomes back inside
    path(cv, [(mx + mw / 2, 1.64 + 4.14), (mx + mw / 2, 6.0), (5.2, 6.0), (5.2, 5.78)], GREEN, 1.75)
    tag(cv, 6.0, 5.915, 3.4, "\u2190 BOOKED VISITS COME BACK INSIDE: LIFT AGAINST A HOLDOUT", GREEN)

    # three principles
    py = 6.22
    pr = [("PHI never leaves Google Cloud", "Marketing Cloud sees tokenized IDs and send-time fields only."),
          ("People approve before data moves", "Data steward for every column; named approver for every audience."),
          ("Every step is auditable", "Policies, approvals, files and outcomes all recorded in BigQuery.")]
    pw = (12.43 - 2 * 0.2) / 3
    for i, (t, d) in enumerate(pr):
        x = 0.45 + i * (pw + 0.2)
        cv.rect(x, py, pw, 0.62, GREY)
        cv.rect(x, py, 0.06, 0.62, (VIOLET, GOLD, GREEN)[i])
        cv.text(x + 0.2, py + 0.05, pw - 0.3, 0.54, [[(t, {"bold": True, "size": 9})], [(d, {"color": MUTE})]],
                size=7.5, anchor=MSO_ANCHOR.MIDDLE, after=1)
    set_notes(s, HL_NOTES)
    return s


def main(out=OUT):
    prs = Presentation(TEMPLATE)
    lst = prs.slides._sldIdLst
    for el in list(lst):
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    high_level_slide(prs, layout)
    governance_slide(prs, layout)
    prs.save(out)
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
