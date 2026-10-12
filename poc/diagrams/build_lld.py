"""Build the draw.io low-level design: from a Codex prompt to production.

    python3 build_lld.py [--preview out.png]

Writes "Codex-to-Production MAD LLD.drawio" beside this script. Open it at
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
OUT = os.path.join(HERE, "Codex-to-Production MAD LLD.drawio")

W, H = 3400, 2020

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
text(40, 18, 2300, 44, "Codex to Production · MAD end-to-end low-level design", size=30, bold=True)
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
text(2506, 94, 850, 32, "the user's journey: 1 type · 2 start the run · 3 agents read the graph (graph.* over MCP, cited facts) · 4 act through the gateway · 5 see results", size=13)

# =========================================================== lanes
LY, LH = 140, 1570
lane(40, LY, 620, LH, "1 · USER + CODEX  (what the user sees)", BLACK)
lane(690, LY, 800, LH, "2 · PHASE 1 · ENGINEERING CONTEXT KNOWLEDGE GRAPH", VIOLET)
lane(1520, LY, 1180, LH, "3 · PHASE 2 · MAD DELIVERY RUNTIME  (Google Cloud)", NAVY)
lane(2730, LY, 630, LH, "4 · OUTPUT  (what lands where)", "#3A3A3A")

# =========================================================== lane 1: user + codex
user = nid("u")
cells.append((user, "v", "User<br>" + small("PM · Tech Lead · Developer"),
              "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;"
              "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2;fontSize=14;fontStyle=1;",
              (80, 212, 44, 80)))
shapes[user] = (80, 212, 44, 80)
codex = box(220, 200, 420, 112,
            T("CODEX", small("OpenAI Codex (CLI, IDE or app) · MCP client<br>"
                             "MAD tools: mad.start_run · mad.status · graph.*", "#D9D9D9"), 20),
            fill=BLACK, stroke=BLACK, font=WHITE, size=13)

screen_lines = [
    ("#FFFFFF", "&gt; Implement Jira NS-1234"),
    ("#8C8C8C", ""),
    (CYAN, "[01] Reading NS-1234 · drafting acceptance criteria"),
    (YELLOW, "[H1] waiting: product owner approval  (link)"),
    (CYAN, "[02] Graph: exists? no · reuse: 1 flow"),
    (CYAN, "[02] Blast radius: automations on object, 2 pods"),
    (MAGENTA, "[02] Guardian: NEEDS OWNER APPROVAL"),
    (YELLOW, "[H2] waiting: architect + affected pod owner"),
    (CYAN, "[03] Branch mad/NS-1234 · deploy to DEV"),
    (CYAN, "[03] Apex tests passing · pull request opened"),
    (CYAN, "[04] Review: 0 blocking · regression: 2 pods"),
    (YELLOW, "[H3] waiting: tech lead + security"),
    (CYAN, "[05] Copado: promoted to SIT, then UAT"),
    (YELLOW, "[H4] waiting: business UAT sign-off"),
    (CYAN, "[07] Release bundle, rollback plan, CAB pack"),
    (YELLOW, "[CAB] approved · owner pipeline deploys"),
    (CYAN, "[09] Done · Jira closed · graph refreshed"),
    ("#8C8C8C", ""),
    ("#8C8C8C", "links: brief · design · PR · UAT · passport"),
]
body = "<br>".join("<font color='%s'>%s</font>" % (c, l if l else "&nbsp;") for c, l in screen_lines)
screen = box(60, 352, 580, 640,
             "<font color='#8C8C8C'>CODEX SESSION · illustrative run</font><br><br>" + body,
             fill="#0D1117", stroke="#3A3A3A", font=WHITE, size=16, align="left", valign="top",
             extra="fontFamily=Courier New;spacingLeft=16;spacingTop=16;")
note1 = box(60, 1016, 580, 190,
            T("How Codex reaches MAD",
              "Codex is the front door. It calls MAD over MCP (<i>mad.start_run</i>). The run itself is long and "
              "durable, so it lives in Google Cloud; Codex shows progress from <i>mad.status</i> and "
              "the approval links. The user's Codex never holds Jira, Salesforce or Copado credentials."),
            fill=WHITE, stroke=GREY_D, align="left", valign="top", size=13)
note2 = box(60, 1226, 580, 170,
            T("Two Codex roles",
              "<b>Front-door Codex</b>: where people ask and approve.<br>"
              "<b>Worker Codex</b>: the coding engine inside the Developer and Test Agent containers, "
              "headless (Codex SDK / codex exec), on its own branch, DEV sandbox only."),
            fill=CYAN_T, stroke=CYAN_D, align="left", valign="top", size=13)
note3 = box(60, 1416, 580, 270,
            T("What the user can do in Codex",
              "• Start: a Jira key or a plain request<br>"
              "• Watch: each step's status as it runs<br>"
              "• Open: brief, design page, PR, UAT build<br>"
              "• Approve: opens the approval page (SSO)<br>"
              "• Ask: graph questions (does X exist, who owns Y)<br>"
              "• Stop or send back with a comment"),
            fill=WHITE, stroke=GREY_D, align="left", valign="top", size=13)

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
          T("Run API · Cloud Run", small("validates the story · idempotency key = story + revision · "
                                         "creates the run · starts one Workflows execution")),
          fill=SVC_T, stroke=NAVY)
fs = box(2000, 196, 680, 112,
         T("Firestore · runs/{runId}", small("current step · status · attempts · minutes and token budget · "
                                             "artifact URIs · commit SHA · approval ids · checkpoints<br>"
                                             "a run can be inspected or resumed from this document alone")),
         fill=SVC_T, stroke=NAVY)
wf = box(1550, 340, 410, 990, "", fill=WHITE, stroke=NAVY, sw=2, valign="top")
text(1566, 346, 380, 52, "<b>Cloud Workflows</b> · the nine steps (YAML)<br>" +
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
     "fix ≤ 2", color=MAGENTA, dashed=True, width=1.5)

appr = box(1550, 1362, 410, 150,
           T("Approval service · Cloud Run + IAP",
             small("Ascension SSO · shows the evidence for that gate · decision signed with Cloud KMS, bound to "
                   "run, scope, commit SHA and target · resumes the run through its Workflows callback",
                   "#2B2B2B")),
           fill=YELLOW_T, stroke="#C9A800", sw=2)
learn = box(1550, 1544, 410, 142,
            T("Learning loop · no model trained on our data",
              small("step 09 resyncs the graph · incidents become Guardian rules · rejected outputs become "
                    "evaluation cases that run in Cloud Build before any prompt or model change", "#2B2B2B")),
            fill=GREEN_T, stroke=GREEN, sw=2)

disp = box(2000, 340, 330, 112,
           T("Dispatcher · Cloud Run", small("starts one Cloud Run Job per step with: runId, step, agent, skills, "
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
text(2016, 1186, 650, 64, "<b>MCP tool gateway · Cloud Run + Open Policy Agent</b><br>" +
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
                   "re-run once, then owner · failed tests → fix loop ≤ 2, then tech lead · budget breach → "
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
    ("jira", "Jira", "brief posted (01) · status: Ready for MAD → In progress → QA → Done", 92, GREY_D, False),
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
          T("Change passport · BigQuery",
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
edge(user, codex, [(124, 256), (220, 256)], "types a request", color=BLACK)
badge(150, 228, 1)
edge(codex, run, [(640, 240), (668, 240), (668, 118), (1755, 118), (1755, 196)],
     "mad.start_run(NS-1234) over MCP", color=BLACK, width=2.5)
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
edge(back, screen, [(2750, yb + hb / 2), (2722, yb + hb / 2), (2722, 1700), (650, 1700), (650, 900), (640, 900)],
     "results and links shown in Codex", color=BLACK, width=2.5)
badge(1170, 1686, 5)

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
for i, (n, d) in enumerate(plat):
    px = 56 + (i % 5) * 660
    py = BY + 60 + (i // 5) * 92
    box(px, py, 644, 80, T(n, small(d)), fill=SVC_T, stroke=NAVY, size=14, sw=1)


# =========================================================== write
def to_xml():
    out = ['<mxfile host="app.diagrams.net" agent="build_lld.py" version="24.7.17">',
           '<diagram id="mad-lld" name="Codex to Production · MAD LLD">',
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
