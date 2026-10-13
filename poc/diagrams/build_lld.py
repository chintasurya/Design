"""Build the draw.io low-level design: from a Codex prompt to production.

    python3 build_lld.py [--preview out.png]

Writes "Codex-to-Production Agentic Harness LLD.drawio" beside this script. Open it at
https://app.diagrams.net (File > Open from > Device). Every edge is attached
to its shapes with explicit exit and entry points and waypoints, so the file
opens exactly as laid out here and stays connected when boxes are moved.

--preview draws the same geometry with Pillow, for checking overlaps without
draw.io. It approximates text wrapping; draw.io is the real render.
"""
import html
import os
import re
import sys
from xml.sax.saxutils import quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Codex-to-Production Agentic Harness LLD.drawio")

W, H = 3400, 2020
DX = 320          # lane 1 (user + SDLC plugin) is this much wider; everything right of it shifts
X_SPLIT = 670
FROZEN = set()    # cells laid out in final coordinates, not shifted

# IG palette, as in the deck
NAVY, BLACK, WHITE = "#00273B", "#000000", "#FFFFFF"
CYAN, CYAN_T, CYAN_D = "#00D6F2", "#E0FAFE", "#0097AD"
YELLOW, YELLOW_T = "#FFD700", "#FFF7CC"
MAGENTA, MAGENTA_T = "#FF0069", "#FFE6F0"
VIOLET, VIOLET_T = "#4527A0", "#ECE9F5"
GREEN, GREEN_T = "#2E9E1F", "#EAFBE6"
GREY, GREY_D, MUTE = "#F2F2F2", "#BFBFBF", "#595959"
SVC_T = "#F3F6F8"

cells = []      # (id, kind, value, style, geometry)
shapes = {}     # id -> (x, y, w, h)
_n = [0]


def nid(prefix):
    _n[0] += 1
    return "%s%d" % (prefix, _n[0])


def box(x, y, w, h, value, fill=WHITE, stroke=NAVY, font=BLACK, size=13, bold=False, rounded=True,
        dashed=False, align="center", valign="middle", sw=1.5, extra="", sid=None):
    sid = sid or nid("b")
    style = ("rounded=%d;whiteSpace=wrap;html=1;arcSize=6;fillColor=%s;strokeColor=%s;fontColor=%s;"
             "fontSize=%d;fontStyle=%d;align=%s;verticalAlign=%s;spacing=10;strokeWidth=%s;%s%s") % (
        1 if rounded else 0, fill, stroke, font, size, 1 if bold else 0, align, valign, sw,
        "dashed=1;dashPattern=6 4;" if dashed else "", extra)
    cells.append((sid, "v", value, style, (x, y, w, h)))
    shapes[sid] = (x, y, w, h)
    return sid


def text(x, y, w, h, value, size=13, color=BLACK, bold=False, align="left", valign="middle", extra=""):
    sid = nid("t")
    style = ("text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;fontSize=%d;fontColor=%s;"
             "fontStyle=%d;align=%s;verticalAlign=%s;%s") % (size, color, 1 if bold else 0, align, valign, extra)
    cells.append((sid, "v", value, style, (x, y, w, h)))
    shapes[sid] = (x, y, w, h)
    return sid


def lane(x, y, w, h, title, color):
    box(x, y, w, h, "", fill="#FBFCFD", stroke=color, rounded=True, sw=2)
    box(x, y, w, 44, title, fill=color, stroke=color, font=WHITE, size=16, bold=True, rounded=True, sw=2)


def badge(x, y, n, fill=BLACK, font=WHITE):
    sid = nid("n")
    style = ("ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=%s;strokeColor=%s;fontColor=%s;"
             "fontSize=13;fontStyle=1;") % (fill, WHITE, font)
    cells.append((sid, "v", str(n), style, (x, y, 28, 28)))
    shapes[sid] = (x, y, 28, 28)


def edge(src, tgt, pts, label="", color=NAVY, dashed=False, width=2, both=False, off=None):
    """pts: full polyline, first point on src border, last on tgt border."""
    sx, sy, sw_, sh = shapes[src]
    tx, ty, tw, th = shapes[tgt]
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    ex, ey = (x0 - sx) / sw_, (y0 - sy) / sh
    nx, ny = (x1 - tx) / tw, (y1 - ty) / th
    style = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;strokeColor=%s;"
             "strokeWidth=%s;fontSize=12;fontColor=%s;labelBackgroundColor=#FFFFFF;"
             "exitX=%.4f;exitY=%.4f;exitDx=0;exitDy=0;entryX=%.4f;entryY=%.4f;entryDx=0;entryDy=0;%s%s") % (
        color, width, color, ex, ey, nx, ny, "dashed=1;" if dashed else "",
        "startArrow=block;startFill=1;" if both else "")
    eid = nid("e")
    cells.append((eid, "e", label, style, (src, tgt, pts[1:-1], pts, off)))
    return eid


def T(title, body=None, tsize=None):
    """Bold title + body lines, as draw.io html."""
    s = "<b>%s</b>" % title if tsize is None else "<b><font style='font-size:%dpx'>%s</font></b>" % (tsize, title)
    if body:
        s += "<br>" + body
    return s


def small(s, color=MUTE, size=12):
    return "<font style='font-size:%dpx' color='%s'>%s</font>" % (size, color, s)


# =========================================================== title + legend
text(40, 18, 2300, 44, "Codex to Production · Agentic Harness end-to-end low-level design", size=30, bold=True)
text(40, 62, 2400, 30,
     "Ascension · what the user sees in Codex, what runs behind it on Google Cloud "
     "(Phase 1 Engineering Context Knowledge Graph, Phase 2 Multi-Agent Delivery), and where each output lands",
     size=15, color=MUTE)

lg = [("AI agent", CYAN_T, CYAN_D, False), ("Human gate", YELLOW, YELLOW, False),
      ("Control / policy", MAGENTA_T, MAGENTA, False), ("Knowledge graph", VIOLET_T, VIOLET, False),
      ("Google Cloud service", SVC_T, NAVY, False), ("No agent path", WHITE, MUTE, True)]
for i, (name, f, s, d) in enumerate(lg):
    lx = 2470 + (i % 3) * 300
    ly = 22 + (i // 3) * 36
    box(lx, ly, 34, 22, "", fill=f, stroke=s, dashed=d, sw=2)
    text(lx + 44, ly - 3, 240, 28, name, size=13)
badge(2470, 96, "n")
text(2506, 94, 850, 32, "the user's journey: 1 invoke a skill · 2 start the run · 3 agents read the graph (graph.* over MCP, cited facts) · 4 act through the gateway · 5 see results", size=13)

# =========================================================== lanes
LY, LH = 140, 1570
lane(690, LY, 800, LH, "2 · PHASE 1 · HARNESS CONTEXT · KNOWLEDGE GRAPH", VIOLET)
lane(1520, LY, 1180, LH, "3 · PHASE 2 · AGENTIC HARNESS RUNTIME  (Google Cloud)", NAVY)
lane(2730, LY, 630, LH, "4 · OUTPUT  (what lands where)", "#3A3A3A")

# =========================================================== lane 2: phase 1
src = box(720, 196, 740, 160, "", fill=WHITE, stroke=GREY_D)
text(736, 200, 700, 30, "<b>Systems of record</b> · read-only, authority stays with each system", size=14)
chips = [("Jira Cloud", "stories, acceptance criteria"), ("Confluence", "designs, business rules"),
         ("Salesforce", "Health, Data, Marketing Cloud metadata"),
         ("Git", "Apex, LWC, metadata, tests"), ("Copado", "promotions, test runs"),
         ("Google Drive", "specs, mapping sheets")]
for i, (n, d) in enumerate(chips):
    cx = 736 + (i % 3) * 241
    cy = 236 + (i // 3) * 58
    box(cx, cy, 228, 50, "<b>%s</b><br>%s" % (n, small(d, size=11)), fill=GREY, stroke=GREY_D, size=13, sw=1)

sch = box(720, 386, 310, 92,
          T("Cloud Scheduler", small("cron per source: Jira 15 min · Confluence 1 h · Copado 15 min · "
                                     "Drive 30 min · Salesforce nightly")), fill=SVC_T, stroke=NAVY)
evt = box(1150, 386, 310, 92,
          T("Eventarc + Pub/Sub", small("Jira, Git, Copado webhooks start a sync early")), fill=SVC_T, stroke=NAVY)
con = box(720, 510, 740, 112,
          T("Connector jobs · Cloud Run Jobs (Python 3.12)",
            small("read-only auth: Atlassian token / OAuth · Salesforce JWT bearer (External Client App) · "
                  "Git deploy key · Copado API user · Drive service account<br>"
                  "delta since last high-water mark, kept in <b>Firestore</b> · Salesforce flows read in chained "
                  "batches (one Flow body per Tooling API call)")), fill=SVC_T, stroke=NAVY)
raw = box(720, 654, 350, 92,
          T("Cloud Storage · raw artifacts", small("raw/&lt;source&gt;/&lt;id&gt;/&lt;sha256&gt;<br>"
                                                   "versioned · CMEK · unchanged hash skipped")),
          fill=SVC_T, stroke=NAVY)
dlp = box(1110, 654, 350, 92,
          T("Sensitive Data Protection (DLP)", small("de-identify Jira, Confluence and Drive text "
                                                     "before parsing; Salesforce read as metadata only")),
          fill=MAGENTA_T, stroke=MAGENTA)
ing = box(720, 778, 740, 112,
          T("Ingest · validate · link · Cloud Run Jobs",
            small("parsers: Jira ADF → Given/When/Then · Confluence HTML → rules · Flow XML · Apex SOQL/DML · "
                  "test → class map<br>pydantic + JSON Schema · failures quarantined · "
                  "unproven links stored as INFERRED (confidence &lt; 1.0)")), fill=SVC_T, stroke=NAVY)
snap = box(720, 922, 350, 112,
           T("JSON snapshot · Cloud Storage", small("snapshotId · nodes · relationships · provenance<br>"
                                                    "vendor-neutral contract (deck layers 4 to 6)")),
           fill=SVC_T, stroke=NAVY)
spn = box(1110, 922, 350, 150,
          T("Spanner Graph (Enterprise)", small("Node + Edge tables · CREATE PROPERTY GRAPH<br>"
                                                "valid_from / valid_to history · ownership edges<br>"
                                                "ISO GQL · full-text + vector search", "#2B2B2B")),
          fill=VIOLET_T, stroke=VIOLET, sw=2)
api = box(720, 1104, 740, 196,
          T("Graph API + MCP server · FastAPI on Cloud Run",
            small("private ingress · Google-signed identity tokens · agents never write GQL", "#2B2B2B") +
            "<br><br><font face='Courier New' style='font-size:13px'>"
            "graph.exists &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;graph.find_reuse &nbsp;&nbsp;graph.blast_radius<br>"
            "graph.classify_risk graph.owners &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;graph.coverage_gap<br>"
            "graph.provenance &nbsp;&nbsp;graph.context_slice</font>"),
          fill=VIOLET_T, stroke=VIOLET, sw=2)
gql = box(720, 1332, 740, 160,
          "<font color='#8C8C8C'>-- GQL behind graph.blast_radius (illustrative)</font><br>"
          "GRAPH DeliveryGraph<br>"
          "MATCH (a)-[e:FLOW_UPDATES_SOBJECT|TRIGGER_FIRES_ON_SOBJECT]-&gt;<br>"
          "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(o:SOBJECT {api_name: 'HealthcareFacility'})<br>"
          "RETURN a.name, a.owner_pod, e.source_path",
          fill="#0D1117", stroke="#3A3A3A", font="#E6E6E6", size=13, align="left", valign="top",
          extra="fontFamily=Courier New;spacingLeft=14;")
p1n = box(720, 1524, 740, 162,
          T("Trust built in",
            "• Every answer cites node id, source path, SHA-256, snapshotId<br>"
            "• Existence is a full lookup, never a sample<br>"
            "• Freshness + coverage per source on Cloud Monitoring<br>"
            "• Sandbox POC today: 2,177 nodes · 2,786 edges (Salesforce)"),
          fill=WHITE, stroke=GREY_D, align="left", valign="top", size=13)

edge(src, con, [(1090, 356), (1090, 510)], "read-only APIs")
edge(sch, con, [(875, 478), (875, 510)])
edge(evt, con, [(1305, 478), (1305, 510)])
edge(con, raw, [(895, 622), (895, 654)])
edge(raw, dlp, [(1070, 700), (1110, 700)])
edge(dlp, ing, [(1285, 746), (1285, 778)])
edge(ing, snap, [(895, 890), (895, 922)])
edge(snap, spn, [(1070, 978), (1110, 978)])
edge(spn, api, [(1285, 1072), (1285, 1104)], "GQL", off=(26, 0))

# =========================================================== lane 3: phase 2
run = box(1550, 196, 410, 112,
          T("Harness entry · Run API · Cloud Run", small("validates the story · idempotency key = story + revision · "
                                         "creates the run · starts one Workflows execution")),
          fill=SVC_T, stroke=NAVY)
fs = box(2000, 196, 680, 112,
         T("Harness state · Firestore runs/{runId}", small("current step · status · attempts · minutes and token budget · "
                                             "artifact URIs · commit SHA · approval ids · checkpoints<br>"
                                             "a run can be inspected or resumed from this document alone")),
         fill=SVC_T, stroke=NAVY)
wf = box(1550, 340, 410, 990, "", fill=WHITE, stroke=NAVY, sw=2, valign="top")
text(1566, 346, 380, 52, "<b>Harness run loop</b> · Cloud Workflows, 9 steps<br>" +
     small("try / retry with backoff · callbacks for every gate"), size=14)

seq = [("step", "<b>01 Understand</b> · Requirements Agent → brief.json"),
       ("gate", "<b>H1</b> · product owner / business lead"),
       ("step", "<b>02 Design</b> · Architect Agent → design.json, Confluence draft"),
       ("ctrl", "<b>Change Guardian</b> · design check, names affected pods"),
       ("gate", "<b>H2</b> · architect + affected pod owners"),
       ("step", "<b>03 Build</b> · Developer Agent (worker Codex) → PR + SHA"),
       ("step", "<b>04 Verify</b> · Review ‖ Test Agents → findings, test report"),
       ("gate", "<b>H3</b> · tech lead + security / domain"),
       ("step", "<b>05 Promote</b> · Release Agent → Copado SIT, UAT"),
       ("gate", "<b>H4</b> · business UAT (step 06)"),
       ("step", "<b>07 Prepare</b> · Release Agent → bundle, rollback, CAB pack"),
       ("gate", "<b>CAB</b> · release owner (step 08)"),
       ("none", "<b>08 Deploy</b> · owning team's pipeline, no agent"),
       ("step", "<b>09 Close</b> · resync graph · close passport · Jira Done")]
sy = 410
seq_ids = []
for kind, label in seq:
    h = 56 if kind in ("step", "ctrl", "none") else 40
    st = {"step": dict(fill=CYAN_T, stroke=CYAN_D), "gate": dict(fill=YELLOW, stroke=YELLOW),
          "ctrl": dict(fill=MAGENTA_T, stroke=MAGENTA), "none": dict(fill=WHITE, stroke=MUTE, dashed=True)}[kind]
    seq_ids.append(box(1590, sy, 350, h, label, size=13, **st))
    sy += h + 10
for a_, b_ in zip(seq_ids, seq_ids[1:]):
    ax, ay, aw, ah = shapes[a_]
    bx, by, bw, bh = shapes[b_]
    edge(a_, b_, [(ax + aw / 2, ay + ah), (bx + bw / 2, by)], width=1.5)
# fix loop 04 -> 03
s3, s4 = seq_ids[5], seq_ids[6]
x3, y3, w3, h3 = shapes[s3]
x4, y4, w4, h4 = shapes[s4]
edge(s4, s3, [(x4, y4 + h4 / 2), (1572, y4 + h4 / 2), (1572, y3 + h3 / 2), (x3, y3 + h3 / 2)],
     "fix ≤ 5", color=MAGENTA, dashed=True, width=1.5)

appr = box(1550, 1362, 410, 150,
           T("Harness approvals · Cloud Run + IAP",
             small("Ascension SSO · shows the evidence for that gate · decision signed with Cloud KMS, bound to "
                   "run, scope, commit SHA and target · resumes the run through its Workflows callback",
                   "#2B2B2B")),
           fill=YELLOW_T, stroke="#C9A800", sw=2)
learn = box(1550, 1544, 410, 142,
            T("Evaluation + learning loop",
              small("no model trained on our data · step 09 resyncs the graph · incidents become Guardian rules · rejected outputs become "
                    "evaluation cases that run in Cloud Build before any prompt or model change", "#2B2B2B")),
            fill=GREEN_T, stroke=GREEN, sw=2)

disp = box(2000, 340, 330, 112,
           T("Harness dispatcher · Cloud Run", small("starts one Cloud Run Job per step with: runId, step, agent, skills, "
                                             "identity, inputs, allowedTools, budget, outputSchema")),
           fill=SVC_T, stroke=NAVY)
ps = box(2350, 340, 330, 112,
         T("Pub/Sub", small("step.completed / step.failed<br>output validated against its schema, then a "
                            "checkpoint · dead-letter topic + alert")), fill=SVC_T, stroke=NAVY)

ag = box(2000, 484, 680, 520, "", fill=WHITE, stroke=CYAN_D, sw=2)
text(2016, 490, 650, 40, "<b>Agent workers · Cloud Run Jobs</b> " +
     small("· images in Artifact Registry · run once, then exit"), size=14)
agents = [
    ("Requirements Agent", "OpenAI Agents SDK (Python) · sa-ai-read",
     "Jira story + graph.context_slice → acceptance criteria (Given/When/Then), open questions, every line cited"),
    ("Architect Agent", "Agents SDK · sa-ai-read",
     "exists → find_reuse → blast_radius → owners → classify_risk → coverage_gap → design.json"),
    ("Developer Agent", "worker Codex (Codex SDK / codex exec) · sa-ai-dev",
     "branch mad/&lt;story&gt; · sf project deploy (DEV sandbox only) · sf apex run test · Code Analyzer · "
     "loop until green → PR"),
    ("Review Agent", "Agents SDK + Code Analyzer (PMD), ESLint · sa-ai-read",
     "standards, security, access checks → findings.json + PR comments · cannot approve"),
    ("Test Agent", "worker Codex + Agents SDK · sa-ai-dev",
     "Apex + Jest tests from the design · Zephyr Scale cases · regression scope from blast_radius"),
    ("Release Agent", "Agents SDK · sa-ai-release",
     "Copado API: user story, promote SIT then UAT · manifest, rollback plan, CAB pack"),
]
agent_ids = []
for i, (n, rt, d) in enumerate(agents):
    axx = 2016 + (i % 2) * 332
    ayy = 538 + (i // 2) * 152
    agent_ids.append(box(axx, ayy, 316, 140, T(n, small(rt, CYAN_D) + "<br>" + small(d, "#2B2B2B")),
                         fill=CYAN_T, stroke=CYAN_D, size=14, align="left", valign="top"))

mdl = box(2000, 1036, 330, 112,
          T("Approved model endpoint", small("OpenAI API through Secure Web Proxy allowlist · bounded, "
                                             "redacted context only · BAA / zero retention per Ascension terms")),
          fill=SVC_T, stroke=NAVY)
grd = box(2350, 1036, 330, 112,
          T("Change Guardian · Cloud Run + OPA", small("diff + ownership graph + Rego rulebook → PASS / NEEDS "
                                                       "OWNER APPROVAL / BLOCK · design, every commit, promotion, "
                                                       "nightly drift", "#2B2B2B")),
          fill=MAGENTA_T, stroke=MAGENTA, sw=2)
gw = box(2000, 1180, 680, 196, "", fill=MAGENTA_T, stroke=MAGENTA, sw=2)
text(2016, 1186, 650, 64, "<b>Harness tool gateway · MCP · Cloud Run + Open Policy Agent</b><br>" +
     small("checks identity · tool · target · approval for the current SHA → runs the action with that "
           "identity's credential from Secret Manager → logs the decision to BigQuery", "#2B2B2B"), size=14)
ids = [("sa-ai-read", "graph, Jira, Confluence (read)"), ("sa-ai-dev", "Git branch + DEV sandbox"),
       ("sa-ai-release", "Copado: SIT and UAT only")]
for i, (n, d) in enumerate(ids):
    box(2016 + i * 222, 1262, 210, 58, "<b>%s</b><br>%s" % (n, small(d, size=11)), fill=WHITE,
        stroke=MAGENTA, size=13, sw=1)
text(2016, 1330, 650, 34, "<b>No production identity exists for any agent.</b>", size=13, color=MAGENTA)

fail = box(2000, 1408, 680, 142,
           T("Failure and recovery",
             small("transient error → retry ×3 with backoff, idempotent steps · bad output → schema reject, "
                   "re-run once, then owner · failed tests → fix loop ≤ 5, then owner · budget breach → "
                   "pause + escalate · outage → resume from the Firestore checkpoint", "#2B2B2B")),
           fill=WHITE, stroke=NAVY, align="left", valign="top")
acc = box(2000, 1572, 680, 114,
          T("Accuracy guard",
            small("context only from the graph · every claim cites a node and SHA · an uncited claim or an "
                  "invented dependency is rejected · the agent that builds never approves its own work",
                  "#2B2B2B")),
          fill=WHITE, stroke=NAVY, align="left", valign="top")

# =========================================================== lane 4: output
outs = [
    ("jira", "Jira", "brief posted (01) · status: Ready for Harness → In progress → QA → Done", 92, GREY_D, False),
    ("conf", "Confluence", "design page draft (02) · as-built record (09)", 80, GREY_D, False),
    ("git", "Git", "branch mad/NS-1234 · pull request · commit SHA (03, 04)", 80, GREY_D, False),
    ("sfdev", "Salesforce DEV sandbox", "change deployed, Apex tests run (03)", 80, GREY_D, False),
    ("cop", "Copado", "user story · promotion SIT → UAT · Robotic and regression runs (05)", 92, GREY_D, False),
    ("zep", "Zephyr Scale", "test cases and results (04, 05)", 80, GREY_D, False),
    ("cab", "CAB pack", "generated from the change passport (07)", 80, GREY_D, False),
    ("prod", "PRODUCTION", "owning team's pipeline after CAB (08) · no agent credential", 92, MUTE, True),
]
oy = 196
oid = {}
for k, n, d, h, s, dash in outs:
    oid[k] = box(2750, oy, 590, h, T(n, small(d)), fill=WHITE, stroke=s, dashed=dash, sw=2 if dash else 1.5)
    oy += h + 16
pas = box(2750, oy, 590, 150,
          T("Harness audit trail · change passport · BigQuery",
            small("story → source snapshot → design → approvals → commit SHA → test evidence → deployment → "
                  "outcome<br>one row per event, each hashed with the previous row: tamper-evident", "#2B2B2B")),
          fill=WHITE, stroke=BLACK, sw=2)
oy += 166
back = box(2750, oy, 590, 130,
           T("Back to the user in Codex",
             small("status of every step, approval links, and links to the brief, design, PR, UAT build and "
                   "passport")), fill=BLACK, stroke=BLACK, font=WHITE)
oy += 146
meas = box(2750, oy, 590, 1686 - oy,
           T("Measured per pod",
             small("cycle time per step · rework rounds · escaped defects · agent cost per change<br>"
                   "BigQuery views, Looker Studio dashboards")), fill=WHITE, stroke=GREY_D,
           align="left", valign="top")

# =========================================================== cross-lane edges (the journey)
badge(900, 104, 2)
edge(run, fs, [(1960, 252), (2000, 252)])
edge(run, wf, [(1755, 308), (1755, 340)], "start", off=(28, 0))
edge(wf, disp, [(1960, 396), (2000, 396)], "")
text(1962, 360, 60, 30, small("task"), size=12)
edge(disp, ag, [(2165, 452), (2165, 484)], "Cloud Run Job", off=(56, 0))
edge(ag, ps, [(2515, 484), (2515, 452)], "step.completed", off=(62, 0))
edge(ps, wf, [(2515, 340), (2515, 322), (1980, 322), (1980, 470), (1960, 470)], "resume", width=1.5)
edge(ag, api, [(2000, 990), (1984, 990), (1984, 1346), (1506, 1346), (1506, 1200), (1460, 1200)],
     "graph.*", color=VIOLET, width=2.5)
badge(1515, 1300, 3)
edge(ag, mdl, [(2165, 1004), (2165, 1036)], "LLM calls", off=(42, 0))
edge(ag, gw, [(2680, 900), (2694, 900), (2694, 1278), (2680, 1278)], "", color=MAGENTA, width=2.5)
badge(2652, 1150, 4, fill=MAGENTA)
text(2530, 1149, 118, 30, "every tool call", size=12, color=MAGENTA, bold=True, align="right")
edge(grd, gw, [(2515, 1148), (2515, 1180)], "verdict", off=(-34, 0))
edge(wf, appr, [(1755, 1330), (1755, 1362)], "gates wait", off=(-48, 0))
for k in ("jira", "git", "sfdev", "cop"):
    x_, y_, w_, h_ = shapes[oid[k]]
    edge(gw, oid[k], [(2680, 1230), (2716, 1230), (2716, y_ + h_ / 2), (2750, y_ + h_ / 2)], color=MAGENTA,
         width=1.5)
x_, y_, w_, h_ = shapes[oid["cop"]]
xp, yp, wp, hp = shapes[oid["prod"]]
edge(oid["cop"], oid["prod"], [(3340, y_ + h_ / 2), (3352, y_ + h_ / 2), (3352, yp + hp / 2), (3340, yp + hp / 2)],
     "", color=MUTE, dashed=True)
xb, yb, wb, hb = shapes[back]

# =========================================================== platform band
BY = 1740
box(40, BY, 3320, 250, "", fill=WHITE, stroke=NAVY, sw=2)
box(40, BY, 3320, 44, "GOOGLE CLOUD PLATFORM SERVICES · shared by Phase 1 and Phase 2", fill=NAVY, stroke=NAVY,
    font=WHITE, size=16, bold=True)
plat = [("IAM service accounts", "sa-graph-sync · sa-orchestrator · sa-ai-read · sa-ai-dev · sa-ai-release · sa-guardian"),
        ("VPC Service Controls", "perimeter around Spanner, Storage, BigQuery, Firestore, Secret Manager"),
        ("Cloud KMS", "CMEK on every store · signs approvals"),
        ("Secret Manager", "Salesforce JWT keys, Atlassian, Copado, Git credentials"),
        ("Secure Web Proxy + Cloud NAT", "egress allowlist: OpenAI, Atlassian, Salesforce, Copado, Git"),
        ("Identity-Aware Proxy", "Ascension SSO for people"),
        ("Cloud Logging · Monitoring · Trace", "runId on every log line · dashboards · alerts"),
        ("BigQuery", "change passport · gateway decisions · delivery measures"),
        ("Artifact Registry + Binary Authorization", "scanned, trusted agent and service images"),
        ("Terraform + Cloud Build", "infrastructure as code · CI · evaluation gate")]
pw = (3320 + DX - 32) / 5
for i, (n, d) in enumerate(plat):
    px = 56 + (i % 5) * pw
    py = BY + 60 + (i // 5) * 92
    FROZEN.add(box(px, py, pw - 16, 80, T(n, small(d)), fill=SVC_T, stroke=NAVY, size=14, sw=1))


# =========================================================== widen lane 1: shift everything to its right
def widen():
    global W
    for k, (cid, kind, value, style, geo) in enumerate(cells):
        if cid in FROZEN:
            continue
        if kind == "v":
            x, y, w, h = geo
            if x >= X_SPLIT:
                x += DX
            elif x + w > X_SPLIT + 50:
                w += DX
            cells[k] = (cid, kind, value, style, (x, y, w, h))
            shapes[cid] = (x, y, w, h)
        else:
            s_, t_, way, pts, off = geo
            way = [(px + DX if px >= X_SPLIT else px, py) for px, py in way]
            pts = [(px + DX if px >= X_SPLIT else px, py) for px, py in pts]
            cells[k] = (cid, kind, value, style, (s_, t_, way, pts, off))
    W += DX


widen()

# =========================================================== lane 1: user + SDLC plugin (final coordinates)
L1W = 620 + DX
lane(40, LY, L1W, LH, "1 · USER + SDLC PLUGIN  (what the user sees in Codex)", BLACK)
user = nid("u")
cells.append((user, "v", "",
              "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;"
              "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;", (80, 200, 40, 70)))
shapes[user] = (80, 200, 40, 70)
text(140, 198, 700, 30, "<b>User</b>", size=17)
text(140, 228, 700, 26, "PM, tech lead, developer or QA engineer", size=14, color=MUTE)
MONO = "fontFamily=Courier New;"
PX, PW = 60, L1W - 40                 # plugin card
PY = 330
head = box(PX, PY, PW, 118, "", fill=BLACK, stroke=BLACK, sw=2)
text(PX + 22, PY + 8, 420, 42, "<b>Agentic Harness SDLC plugin</b>", size=24, color=WHITE)
text(PX + 440, PY + 14, PW - 460, 32, "installed once in Codex (CLI, IDE or app)", size=14, color="#BFBFBF")


def chip(x, y, t, fill="#2B2B2B", stroke="#2B2B2B", font=WHITE, w=None, dashed=False, mono=True):
    w = w or (16 + 8.4 * len(t))
    return box(x, y, w, 24, t, fill=fill, stroke=stroke, font=font, size=13, rounded=True, dashed=dashed, sw=1,
               extra=MONO if mono else "")


text(PX + 22, PY + 52, 90, 28, "Package", size=14, color="#BFBFBF")
cx_ = PX + 105
for t in ("plugin.json", "skills/", "mcp.json"):
    chip(cx_, PY + 54, t)
    cx_ += 16 + 8.4 * len(t) + 8
text(PX + 22, PY + 84, 200, 28, "MCP server <b>harness</b>", size=14, color="#BFBFBF")
cx_ = PX + 195
for t in ("harness.start_run", "harness.status", "graph.*"):
    chip(cx_, PY + 86, t)
    cx_ += 16 + 8.4 * len(t) + 8

C1, C2, C3, C4 = PX + 20, PX + 270, PX + 580, PX + PW - 20     # skill · what · runs through · step (right edge)
RH = 29
rows_y = [PY + 128]


def y_next(h=RH):
    y = rows_y[0]
    rows_y[0] += h
    return y


def colhead():
    y = y_next(26)
    for x, t in ((C1, "Skill"), (C2, "What it does"), (C3, "Runs through")):
        text(x, y, 300, 24, t, size=13, color=MUTE)
    text(C4 - 160, y, 160, 24, "Step, gate", size=13, color=MUTE, align="right")


def rule(x, y, w):
    box(x, y, w, 1, "", fill=GREY_D, stroke=GREY_D, rounded=False, sw=0, size=1)


def section(title, sub):
    y = y_next(34)
    text(C1, y + 4, PW - 40, 28, "<b>%s</b>&nbsp;&nbsp;%s" % (title, small(sub, MUTE, 13)), size=16)
    rule(C1, y + 32, PW - 40)


def step_tags(y, steps, gate):
    x = C4
    if gate:
        w = 14 + 9 * len(gate)
        x -= w
        box(x, y + 3, w, 22, "<b>%s</b>" % gate, fill=YELLOW, stroke=YELLOW, size=12, sw=1)
        x -= 6
    for st in reversed(steps):
        w = 14 + 9 * len(st)
        x -= w
        box(x, y + 3, w, 22, st, fill=GREY, stroke=GREY, size=12, sw=1)
        x -= 6


def row(skill, what, runs, steps=(), gate=None, kind="tool", lock=False, sub=False, italic=False):
    y = y_next()
    sx = C1 + (34 if sub else 0)
    if sub:
        box(C1 + 14, y - 2, 2, RH + 2, "", fill=GREY_D, stroke=GREY_D, rounded=False, sw=0)
    label = ("&#128274; " if lock else "") + ("<i>%s</i>" % skill if italic else "<b>%s</b>" % skill)
    text(sx, y, C2 - sx - 6, RH, label, size=14, extra=MONO if not italic else "")
    text(C2, y, C3 - C2 - 10, RH, what, size=13)
    if kind == "agent":
        chip(C3, y + 2, runs, fill=CYAN_T, stroke=CYAN_D, font="#00586A", mono=False, w=12 + 7.8 * len(runs))
    elif kind == "service":
        chip(C3, y + 2, runs, fill=WHITE, stroke=MUTE, font=BLACK, mono=False, w=12 + 7.8 * len(runs))
    elif kind == "none":
        chip(C3, y + 2, runs, fill=WHITE, stroke=MUTE, font=MUTE, mono=False, dashed=True, w=12 + 7.8 * len(runs))
    elif kind == "id":
        chip(C3, y + 2, runs, fill=MAGENTA_T, stroke=MAGENTA, font=MAGENTA)
    else:
        chip(C3, y + 2, runs, fill=GREY, stroke=GREY_D, font=BLACK)
    step_tags(y, steps, gate)


colhead()
section("Drive the run", "one run per story; <font face='Courier New'>$harness-deliver</font> runs seven SDLC skills")
row("$harness-deliver", "runs the SDLC skills below in order, waits at gates", "harness.start_run", ["01-09"],
    lock=True)
for sk, what, agent, st, g in [
        ("sdlc-understand", "acceptance criteria, cited", "Requirements Agent", "01", "H1"),
        ("sdlc-design", "design, blast radius, Guardian check", "Architect Agent", "02", "H2"),
        ("sdlc-build", "branch, DEV deploy, pull request", "Developer Agent", "03", None),
        ("sdlc-verify", "review and tests, findings report", "Review + Test Agents", "04", "H3"),
        ("sdlc-promote", "Copado SIT, then UAT", "Release Agent", "05", "H4"),
        ("sdlc-release", "bundle, rollback plan, CAB pack", "Release Agent", "07", "CAB")]:
    row(sk, what, agent, [st], g, kind="agent", sub=True)
row("no skill", "production deploy, no agent", "team pipeline", ["08"], kind="none", sub=True, italic=True)
row("sdlc-close", "resync graph, close passport", "Workflows", ["09"], kind="service", sub=True)
y = y_next(44)
box(C1 + 14, y - 2, 2, 44, "", fill=GREY_D, stroke=GREY_D, rounded=False, sw=0)
text(C1 + 34, y, PW - 80, 42, small("SDLC skills ship in <font face='Courier New'>skills/</font> and are not invoked "
                                   "directly. The Dispatcher loads each one into its agent; "
                                   "<font face='Courier New'>$harness-redo</font> sends one back.", MUTE, 13), size=13)
row("$harness-redo", "send a step back with a comment", "Approval service", ["any"], kind="service", lock=True)
section("Watch and decide", "anyone on the story")
row("$harness-status", "watch each step as it runs", "harness.status")
row("$harness-approve", "approve at a gate (SSO page)", "Approval service", (), "H1-CAB", kind="service")
row("$harness-stop", "stop the run", "Approval service", kind="service", lock=True)
row("$harness-ask-graph", "does X exist, who owns Y", "graph.*")
section("QA skills", "for QA engineers, read first")
row("$harness-test-scope", "what to test: blast radius, gaps", "graph.*")
row("$harness-test-cases", "review drafted Zephyr cases", "sa-ai-read", ["04"], kind="id")
row("$harness-regression", "rerun regression + Robotic in SIT", "sa-ai-release", (), "QA lead", kind="id", lock=True)
row("$harness-test-report", "results, failures, flaky tests", "sa-ai-read", ["04", "05"], kind="id")
row("$harness-uat", "UAT pack for business testers", "sa-ai-read", ["06"], "H4", kind="id")
y = y_next(34)
rule(C1, y, PW - 40)
text(C1, y + 4, PW - 40, 28, small("&#128274; Explicit only: Codex never starts, redoes or stops work on its own",
                                   MUTE, 13), size=13)
plugin_h = rows_y[0] + 8 - PY
plugin = box(PX, PY, PW, plugin_h, "", fill="none", stroke=BLACK, sw=2.5, extra="arcSize=3;")
# send the plugin outline behind its contents
cells.insert(next(i for i, c in enumerate(cells) if c[0] == head), cells.pop())

# notes and the illustrative session
NY = PY + plugin_h + 20
NW = 410
note1 = box(PX, NY, NW, 300,
            T("How the plugin reaches the harness",
              "Each skill is a <font face='Courier New'>SKILL.md</font> that tells Codex which harness tool to call "
              "and what to show back; <font face='Courier New'>mcp.json</font> registers the harness MCP server.<br><br>"
              "The run lives in Google Cloud. Workflows carries it from step to step; people only approve, send "
              "back or stop. Skills that start, redo or stop work set "
              "<font face='Courier New'>allow_implicit_invocation: false</font>. The plugin holds no Jira, "
              "Salesforce or Copado credentials.<br><br>"
              "QA skills read Zephyr Scale and Copado results as <font face='Courier New'>sa-ai-read</font>. Only "
              "<font face='Courier New'>$harness-regression</font> starts work, as "
              "<font face='Courier New'>sa-ai-release</font>, after a QA lead approves.", 17),
            fill=WHITE, stroke=GREY_D, align="left", valign="top", size=13)
note2 = box(PX, NY + 316, NW, LY + LH - 16 - (NY + 316),
            T("Two Codex roles",
              "<b>Front-door Codex:</b> loads the plugin; people invoke skills and approve here.<br>"
              "<b>Worker Codex:</b> headless (Codex SDK / <font face='Courier New'>codex exec</font>) inside the "
              "Developer and Test Agents; own branch, DEV sandbox only.", 17),
            fill=CYAN_T, stroke=CYAN_D, align="left", valign="top", size=13)
screen_lines = [
    ("#FFFFFF", "&gt; $harness-deliver NS-1234"),
    ("#8C8C8C", "[skill] harness-deliver → harness.start_run(NS-1234)"),
    (CYAN, "[01] Reading NS-1234 · drafting acceptance criteria"),
    (YELLOW, "[H1] waiting: product owner approval (link)"),
    (CYAN, "[02] Graph: exists? no · reuse: 1 flow"),
    (CYAN, "[02] Blast radius: automations on object, 2 pods"),
    (MAGENTA, "[02] Guardian: NEEDS OWNER APPROVAL"),
    (YELLOW, "[H2] waiting: architect + affected pod owner"),
    (CYAN, "[03] Branch harness/NS-1234 · deploy to DEV"),
    (CYAN, "[03] Apex tests passing · pull request opened"),
    (CYAN, "[04] Review: 0 blocking · regression: 2 pods"),
    (YELLOW, "[H3] waiting: tech lead + security"),
    (CYAN, "[05] Copado: promoted to SIT, then UAT"),
    (YELLOW, "[H4] waiting: business UAT sign-off"),
    (CYAN, "[07] Release bundle, rollback plan, CAB pack"),
    (YELLOW, "[CAB] approved · owner pipeline deploys"),
    (CYAN, "[09] Done · Jira closed · graph refreshed"),
    ("#8C8C8C", ""),
    ("#FFFFFF", "&gt; $harness-ask-graph who owns HealthcareFacility?"),
    ("#B39DDB", "[graph] 3 automations · 2 owning pods · cited"),
    ("#8C8C8C", ""),
    ("#8C8C8C", "links: brief · design · PR · UAT · passport"),
]
body = "<br>".join("<font color='%s'>%s</font>" % (c, l if l else "&nbsp;") for c, l in screen_lines)
SX = PX + NW + 20
screen = box(SX, NY, PX + PW - SX, LY + LH - 16 - NY,
             "<font color='#8C8C8C'>● ● ●&nbsp;&nbsp; Codex session with the plugin, illustrative run</font><br><br>"
             + body, fill="#0D1117", stroke="#0D1117", font=WHITE, size=12, align="left", valign="top",
             extra="fontFamily=Courier New;spacingLeft=14;spacingTop=12;")

# journey edges into and out of lane 1
edge(user, head, [(100, 270), (100, PY)], "", color=BLACK)
badge(86, 286, 1)
text(122, 284, 200, 30, "<b>invokes a skill</b>", size=14)
xr, yr, wr, hr = shapes[run]
edge(head, run, [(PX + PW, PY + 40), (L1W + 55, PY + 40), (L1W + 55, 118), (xr + wr / 2, 118), (xr + wr / 2, yr)],
     "harness.start_run(NS-1234) over MCP", color=BLACK, width=2.5)
xb, yb, wb, hb = shapes[back]
sx_, sy_, sw_, sh_ = shapes[screen]
edge(back, screen, [(xb, yb + hb / 2), (xb - 28, yb + hb / 2), (xb - 28, 1722), (L1W + 50, 1722),
                    (L1W + 50, sy_ + sh_ / 2), (sx_ + sw_, sy_ + sh_ / 2)],
     "results and links shown in Codex", color=BLACK, width=2.5)
badge(1490, 1708, 5)


# =========================================================== write
def to_xml():
    out = ['<mxfile host="app.diagrams.net" agent="build_lld.py" version="24.7.17">',
           '<diagram id="harness-lld" name="Codex to Production · Agentic Harness LLD">',
           '<mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
           'arrows="1" fold="1" page="1" pageScale="1" pageWidth="%d" pageHeight="%d" math="0" shadow="0">' % (W, H),
           '<root><mxCell id="0"/><mxCell id="1" parent="0"/>']
    for cid, kind, value, style, geo in cells:
        if kind == "v":
            x, y, w, h = geo
            out.append('<mxCell id="%s" value=%s style=%s vertex="1" parent="1">'
                       '<mxGeometry x="%d" y="%d" width="%d" height="%d" as="geometry"/></mxCell>'
                       % (cid, quoteattr(value), quoteattr(style), x, y, w, h))
        else:
            s, t, way, _, off = geo
            pts = "".join('<mxPoint x="%d" y="%d"/>' % (px, py) for px, py in way)
            offx = '<mxPoint x="%d" y="%d" as="offset"/>' % off if off else ""
            out.append('<mxCell id="%s" value=%s style=%s edge="1" parent="1" source="%s" target="%s">'
                       '<mxGeometry relative="1" as="geometry">%s%s</mxGeometry></mxCell>'
                       % (cid, quoteattr(value), quoteattr(style), s, t,
                          '<Array as="points">%s</Array>' % pts if pts else "", offx))
    out.append("</root></mxGraphModel></diagram></mxfile>")
    return "\n".join(out)


def preview(path):
    from PIL import Image, ImageDraw, ImageFont
    sc = 0.5
    im = Image.new("RGB", (int(W * sc), int(H * sc)), "white")
    d = ImageDraw.Draw(im)
    f = lambda s, b=False: ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), max(6, int(s * sc)))

    def plain(v):
        v = re.sub(r"<br\s*/?>", "\n", v)
        return html.unescape(re.sub(r"<[^>]+>", "", v))

    for cid, kind, value, style, geo in cells:
        if kind != "v":
            continue
        x, y, w, h = [g * sc for g in geo]
        fill = re.search(r"fillColor=([^;]+)", style).group(1)
        stroke = re.search(r"strokeColor=([^;]+)", style).group(1)
        if "umlActor" in style:
            d.ellipse([x + w * .3, y, x + w * .7, y + h * .25], outline="black", width=2)
            d.line([x + w / 2, y + h * .25, x + w / 2, y + h * .65], fill="black", width=2)
            continue
        if fill not in ("none",):
            d.rectangle([x, y, x + w, y + h], fill=fill, outline=None if stroke == "none" else stroke,
                        width=2 if "strokeWidth=2" in style else 1)
        size = int(re.search(r"fontSize=(\d+)", style).group(1))
        col = re.search(r"fontColor=([^;]+)", style).group(1)
        fnt = f(size)
        cw = max(1, int(fnt.getlength("n")))
        lines = []
        for para in plain(value).split("\n"):
            words, cur = para.split(" "), ""
            for wd in words:
                t = (cur + " " + wd).strip()
                if fnt.getlength(t) > w - 20 * sc and cur:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = t
            lines.append(cur)
        lh = size * 1.25 * sc
        th = lh * len(lines)
        ty = y + 8 * sc if "verticalAlign=top" in style else y + (h - th) / 2
        for ln in lines:
            if "align=left" in style:
                tx = x + 10 * sc
            else:
                tx = x + (w - fnt.getlength(ln)) / 2
            d.text((tx, ty), ln, fill=col, font=fnt)
            ty += lh
        if th > h + 2:
            d.rectangle([x, y, x + w, y + h], outline="red", width=3)
    for cid, kind, value, style, geo in cells:
        if kind != "e":
            continue
        pts = [(px * sc, py * sc) for px, py in geo[3]]
        col = re.search(r"strokeColor=([^;]+)", style).group(1)
        d.line(pts, fill=col, width=2)
        ex, ey = pts[-1]
        d.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=col)
        if value:
            tot = sum(((bx - ax) ** 2 + (by - ay) ** 2) ** .5 for (ax, ay), (bx, by) in zip(pts, pts[1:]))
            half, mx, my = tot / 2, pts[0][0], pts[0][1]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                sl = ((bx - ax) ** 2 + (by - ay) ** 2) ** .5
                if half <= sl:
                    mx, my = ax + (bx - ax) * half / max(sl, 1e-6), ay + (by - ay) * half / max(sl, 1e-6)
                    break
                half -= sl
            off = geo[4] or (0, 0)
            fnt = f(12)
            lbl = plain(value)
            lw = fnt.getlength(lbl)
            cx, cy = mx + off[0] * sc, my + off[1] * sc
            d.rectangle([cx - lw / 2 - 2, cy - 5, cx + lw / 2 + 2, cy + 5], fill="white")
            d.text((cx - lw / 2, cy - 5), lbl, fill=col, font=fnt)
    im.save(path)


if __name__ == "__main__":
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(to_xml())
    print("wrote", OUT, len(cells), "cells")
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
