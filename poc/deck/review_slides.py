"""Three slides for review before they go into the team's final deck.

hld_slide              the Codex-to-Production high-level design, on white, after the architecture slide
roi_slide              slide 11 as the return on investment: one year, investment, saving, ROI, payback
team_cost_slide        slides 15 and 16 as one: the team for months 1-18 and the build cost
"""
import os

from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

import plan_slides
from build_mad_ig_deck import (TXT_LIGHT as LIGHT, BLACK, CYAN, CYAN_T, GREEN, GREEN_T, GREY, MAGENTA, MAGENTA_T, MUTE, NAVY, RULE,
                               VIOLET, VIOLET_T, WHITE, YELLOW, YELLOW_T, Canvas, set_notes)
from build_mad_ig_deck import HERE
from story_slides import money

CYAN_D, GOLD, INK = "0097AD", "C9A800", "2B2B2B"
R = MSO_SHAPE.ROUNDED_RECTANGLE
LOGO_DIR = os.path.join(HERE, "assets", "logos")


def logo(cv, name, x, y, size):
    return cv.s.shapes.add_picture(os.path.join(LOGO_DIR, name + ".png"), Inches(x), Inches(y), Inches(size),
                                   Inches(size))


def text_badge(cv, t, x, y, size, color):
    cv.rect(x, y, size, size, WHITE, color, 0.75, R, 0.2)
    cv.text(x, y, size, size, t, size=5.5, bold=True, color=color, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def card(cv, x, y, w, h, title, body, fill=WHITE, line=NAVY, lw=0.75, tsize=7.5, bsize=6.3, tcolor=BLACK,
         bcolor=INK, icon=None):
    cv.rect(x, y, w, h, fill, line, lw, R, 0.06)
    if icon:
        logo(cv, icon, x + w - 0.28, y + 0.07, 0.2)
    cv.text(x + 0.08, y + 0.06, w - (0.42 if icon else 0.16), h - 0.1,
            [[(title, {"bold": True, "size": tsize, "color": tcolor})], [(body, {"size": bsize, "color": bcolor})]],
            size=bsize, after=1)


def eval_tag(cv, x, y, w=0.46):
    cv.rect(x, y, w, 0.16, YELLOW, BLACK, 0.75, R, 0.5)
    cv.text(x, y, w, 0.16, "EVALS", size=5.5, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
            track=120)


PILLARS = ["Context", "Action", "Orchestration", "Control", "Feedback"]


def pillar_tag(cv, x, y, n, right=False):
    """Harness-engineering pillar marker, as on the harness engineering slide: black, cyan number."""
    name = PILLARS[n - 1].upper()
    w = 0.27 + 0.052 * len(name)
    if right:
        x -= w
    cv.rect(x, y, w, 0.17, BLACK, CYAN, 0.75, R, 0.5)
    cv.text(x, y, w, 0.17, [[("%02d  " % n, {"color": CYAN}), (name, {})]], size=5.2, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=60)
    return w


def badge(cv, x, y, n):
    cv.rect(x, y, 0.19, 0.19, BLACK, WHITE, 0.75, MSO_SHAPE.OVAL)
    cv.text(x, y, 0.19, 0.19, str(n), size=6.5, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)


# ================================================================== new slide 4: high-level design
HLD_NOTES = """SLIDE: Codex to Production, the high-level design   (about 3 minutes)

KEY MESSAGE
One story, end to end. People give their inputs in Salesforce, Codex does the work, the knowledge graph grounds it, evals score every step, and people approve every gate. Nothing reaches production without the owning team.

WALK IT (follow the numbers)
1. In Salesforce, a person opens the Agentic Harness console (an LWC) and enters the Jira key or the requirement, picks the pod and attaches the design.
2. The LWC calls the harness through Apex and a Named Credential; Codex starts the run with the ADLC skills.
3. Every agent reads the knowledge graph for cited facts: what exists, what it affects, who owns it.
4. Every action goes through the tool gateway with one of three identities; none can reach production.
5. Status, approvals and links come back to the same LWC.

WHERE THE EVALS RUN (the yellow boxes)
- On every step: each agent's output is scored before it moves on (answer relevancy, groundedness, tool sequence, pass@k). Pass goes to the next gate; a fail retries with the feedback, at most five times, then goes to a named owner.
- Before any change to the harness: the eval gate in Cloud Build runs the golden set and a held-out set before any prompt, skill or model change; a weekly blind sample is labelled by Ascension's experts.
- At each gate, approvers see the eval scores with the evidence.

WHERE HARNESS ENGINEERING SHOWS (the black numbered tags, same five pillars as the harness engineering slide)
- 01 Context: the knowledge graph. Agents get cited facts and a bounded slice, never a raw org dump.
- 02 Action: the MCP tool gateway. Agents act only through approved tools, with one of three identities.
- 03 Orchestration: the run loop. Nine durable steps, checkpoints, retries, gates.
- 04 Control: the Change Guardian, Model Armor and the human gates. Rules the agents cannot break.
- 05 Feedback: the eval gate, the change passport and the per-pod measures. How the harness gets better.
Codex is the engine; everything inside the dashed frame is the harness we build around it.

BOTTOM ROW
The nine steps of every run, with the four human gates and CAB. The yellow EVALS marks show the steps scored before they move."""


def hld_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION AGENTIC HARNESS · HIGH-LEVEL DESIGN",
              "Codex to Production: one story through the Agentic Harness",
              "People give their inputs in Salesforce, Codex does the work, the knowledge graph grounds it, "
              "evals score every step, and people approve every gate.")
    top, bot = 1.27, 5.95

    # ---------------------------------------------------------- left: user + ADLC, in Salesforce
    lx, lw = 0.45, 2.22
    cv.rect(lx, top, lw, 0.28, BLACK)
    cv.text(lx + 0.1, top, lw - 0.2, 0.28, [[("USER + ADLC", {"bold": True, "track": 150}),
                                            ("   in Salesforce", {"color": "BFBFBF"})]],
            size=7.5, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(lx, top + 0.28, lw, bot - top - 0.28, WHITE, RULE, 0.75)
    cv.text(lx + 0.1, top + 0.36, lw - 0.2, 0.4,
            [[("People", {"bold": True, "size": 7.5})],
             [("PM, tech lead, developer, QA; approvers at H1-H4 and CAB", {"color": MUTE})]], size=6.3)
    badge(cv, lx + 0.1, 1.98, 1)
    cv.text(lx + 0.33, 1.98, 1.8, 0.19, "gives inputs", size=6.3, color=MUTE, anchor=MSO_ANCHOR.MIDDLE)
    card(cv, lx + 0.1, 2.22, lw - 0.2, 1.02, "Salesforce LWC · Agentic Harness console",
         "Connect to Codex, enter the Jira key or the requirement, pick the pod, attach the design. Approve "
         "at each gate and watch every step.", fill=CYAN_T, line=CYAN_D, lw=1.25, icon="salesforce")
    cv.arrow(lx + lw / 2, 3.24, lx + lw / 2, 3.5, BLACK, 1.25)
    cv.text(lx + lw / 2 + 0.06, 3.27, 1.05, 0.2, "Apex · Named Credential", size=5.8, color=MUTE,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(lx + 0.1, 3.5, lw - 0.2, 1.12, BLACK, None, shape=R, radius=0.06)
    logo(cv, "openai-white", lx + lw - 0.36, 3.57, 0.2)
    cv.text(lx + 0.18, 3.56, lw - 0.58, 1.02,
            [[("OpenAI Codex · ADLC skills", {"bold": True, "size": 7.5})],
             [("Each user signs in to their own Codex Enterprise account (SSO). The run starts from the Jira key; "
               "the ADLC skills take it through understand, design, build, verify, promote, release and close.",
               {"color": "D9D9D9"})]], size=6.3, color=WHITE, after=1)
    cv.rect(lx + 0.1, 4.72, lw - 0.2, 1.13, GREEN_T, GREEN, 0.75, R, 0.06)
    checks = ["No production identity for any agent", "No agent approves its own work",
              "Every claim cites a source + SHA-256", "Every tool call checked and logged",
              "No model trained on Ascension data"]
    cv.text(lx + 0.18, 4.78, lw - 0.3, 1.05,
            [[("Trust built in", {"bold": True, "size": 7.5})]] + [[("✓  ", {"bold": True, "color": GREEN}),
                                                                   (c_, {})] for c_ in checks],
            size=6.2, after=0.5)

    # ---------------------------------------------------------- middle: Google Cloud
    gx, gw = 2.83, 7.53
    cv.rect(gx, top, gw, bot - top, None, NAVY, 1.0, R, 0.02, dash="dash")
    logo(cv, "googlecloud", gx + 0.12, top + 0.03, 0.17)
    cv.text(gx + 0.34, top + 0.02, 3.0, 0.2, [[("The Agentic Harness", {"bold": True}),
                                              ("  on Google Cloud", {"color": MUTE})]],
            size=7, anchor=MSO_ANCHOR.MIDDLE)
    ix, iw = gx + 0.12, gw - 0.24
    # key: the five harness-engineering pillars, each tagged where it lives
    kx = gx + gw - 0.12
    for n in range(5, 0, -1):
        kx -= pillar_tag(cv, kx, top + 0.035, n, right=True) + 0.03
    cv.text(kx - 1.75, top + 0.02, 1.7, 0.2, "HARNESS ENGINEERING", size=6, bold=True, track=120,
            align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)

    # phase 1: knowledge graph
    p1y, p1h = 1.55, 1.2
    cv.rect(ix, p1y, iw, p1h, VIOLET_T, VIOLET, 1.0, R, 0.04)
    cv.rect(ix + 0.1, p1y - 0.09, 3.4, 0.2, VIOLET, None, shape=R, radius=0.5)
    cv.text(ix + 0.1, p1y - 0.09, 3.4, 0.2, "PHASE 1 · ENGINEERING CONTEXT KNOWLEDGE GRAPH", size=6.2, bold=True,
            color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=100)
    by, bh = p1y + 0.2, 0.9
    card(cv, ix + 0.1, by, 2.6, bh, "Graph API + MCP server",
         "graph.exists · find_reuse · blast_radius · owners · context_slice. Every answer cites node, source "
         "and SHA-256; agents never write queries.", line=VIOLET)
    card(cv, ix + 2.8, by, 1.85, bh, "Spanner Graph",
         "Property graph, GQL. History and ownership edges for every component.", line=VIOLET,
         icon="googlecloudspanner")
    card(cv, ix + 4.75, by, iw - 4.85, bh, "Ingest pipeline · Cloud Run Jobs",
         "Read-only connectors, on a schedule and on webhooks. DLP de-identifies text; parse, validate and "
         "link before anything is stored.", line=VIOLET)
    cv.arrow(ix + 4.75, by + bh / 2, ix + 4.65, by + bh / 2, VIOLET, 1.25)
    cv.arrow(ix + 2.8, by + bh / 2, ix + 2.7, by + bh / 2, VIOLET, 1.25)
    pillar_tag(cv, ix + iw - 0.1, p1y - 0.085, 1, right=True)

    # phase 2: runtime
    p2y, p2h = 2.92, 2.05
    cv.rect(ix, p2y, iw, p2h, WHITE, NAVY, 1.0, R, 0.03)
    cv.rect(ix + 0.1, p2y - 0.09, 2.6, 0.2, NAVY, None, shape=R, radius=0.5)
    cv.text(ix + 0.1, p2y - 0.09, 2.6, 0.2, "PHASE 2 · AGENTIC HARNESS RUNTIME", size=6.2, bold=True,
            color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=100)
    ry = p2y + 0.2
    card(cv, ix + 0.1, ry, 1.82, 1.05, "Run orchestration",
         "Run API starts the run · Cloud Workflows: 9 steps, retries, gate callbacks · Firestore checkpoints, "
         "resumable · Dispatcher starts one job per step.")
    card(cv, ix + 0.1, ry + 1.13, 1.82, 0.62, "Approval service · IAP",
         "Shows each gate's evidence and eval scores; the signed decision resumes the run.",
         fill=YELLOW_T, line=GOLD)
    # agent workers
    ax, aw = ix + 2.02, 2.9
    cv.rect(ax, ry, aw, 1.05, CYAN_T, CYAN_D, 1.0, R, 0.05)
    cv.text(ax + 0.08, ry + 0.04, aw - 0.16, 0.18, [[("Agent workers", {"bold": True, "size": 7.5}),
                                                     ("  Cloud Run Jobs, one per step", {"color": MUTE})]],
            size=6.2, anchor=MSO_ANCHOR.MIDDLE)
    agents = [("Requirements", "sa-ai-read"), ("Architect", "sa-ai-read"), ("Developer · Codex", "sa-ai-dev"),
              ("Review", "sa-ai-read"), ("Test · Codex", "sa-ai-dev"), ("Release", "sa-ai-release")]
    cw_ = (aw - 0.24) / 2
    for i, (n, ident) in enumerate(agents):
        cx = ax + 0.08 + (i % 2) * (cw_ + 0.08)
        cy = ry + 0.27 + (i // 2) * 0.255
        cv.rect(cx, cy, cw_, 0.22, WHITE, CYAN_D, 0.5, R, 0.2)
        cv.text(cx + 0.06, cy, cw_ - 0.1, 0.22, [[(n, {"bold": True}), ("  " + ident, {"color": MUTE, "size": 5.5})]],
                size=6.2, anchor=MSO_ANCHOR.MIDDLE)
    # EVALS on every step (highlighted)
    ey, eh = ry + 1.13, 0.62
    cv.rect(ax, ey, aw, eh, YELLOW_T, GOLD, 2.25, R, 0.08)
    cv.text(ax + 0.1, ey + 0.05, aw - 0.65, eh - 0.08,
            [[("Evals on every step", {"bold": True, "size": 7.5})],
             [("Each output is scored before it moves: relevancy, groundedness, tool sequence, pass@k. Pass to "
               "the gate; fail retries with feedback, max 5, then a named owner.", {})]], size=6.1, after=1)
    eval_tag(cv, ax + aw - 0.54, ey + 0.06)
    cv.arrow(ax + aw / 2, ry + 1.05, ax + aw / 2, ey, GOLD, 1.5)
    # change guardian + gateway
    gx2, gw2 = ix + 5.02, iw - 5.12
    card(cv, gx2, ry, gw2, 0.62, "Change Guardian · OPA",
         "Diff + ownership graph: PASS, NEEDS OWNER APPROVAL or BLOCK.", fill=MAGENTA_T, line=MAGENTA)
    cv.rect(gx2, ry + 0.7, gw2, 1.05, MAGENTA_T, MAGENTA, 1.0, R, 0.06)
    cv.text(gx2 + 0.08, ry + 0.75, gw2 - 0.16, 0.5,
            [[("MCP tool gateway", {"bold": True, "size": 7.5})],
             [("Checks identity, tool, target and approval, then acts; every decision logged.", {})]],
            size=6.1, after=1)
    for i, ident in enumerate(("sa-ai-read", "sa-ai-dev", "sa-ai-release")):
        iw_ = (gw2 - 0.24) / 3
        cv.rect(gx2 + 0.08 + i * (iw_ + 0.04), ry + 1.25, iw_, 0.2, WHITE, MAGENTA, 0.5, R, 0.3)
        cv.text(gx2 + 0.08 + i * (iw_ + 0.04), ry + 1.25, iw_, 0.2, ident, size=5.5, bold=True,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(gx2 + 0.08, ry + 1.5, gw2 - 0.16, 0.2, "No production identity for any agent.", size=6, bold=True,
            color=MAGENTA, anchor=MSO_ANCHOR.MIDDLE)
    pillar_tag(cv, ix + 1.88, ry - 0.125, 3, right=True)
    pillar_tag(cv, gx2 + gw2 - 0.06, ry - 0.125, 4, right=True)
    pillar_tag(cv, gx2 + gw2 - 0.06, ry + 0.7 - 0.125, 2, right=True)
    # flow arrows inside phase 2
    cv.arrow(ix + 1.92, ry + 0.5, ax, ry + 0.5, BLACK, 1.25)
    cv.arrow(ax + aw, ry + 1.0, gx2, ry + 1.0, MAGENTA, 1.5)
    badge(cv, ax + aw - 0.05, ry + 0.72, 4)
    cv.arrow(gx2 + gw2 / 2, ry + 0.62, gx2 + gw2 / 2, ry + 0.7, MAGENTA, 1.0)
    # agents read the graph
    cv.arrow(ax + 0.5, ry, ax + 0.5, by + bh, VIOLET, 1.5)
    badge(cv, ax + 0.6, p2y - 0.16, 3)
    cv.text(ax + 0.82, p2y - 0.16, 1.6, 0.19, "graph.* · cited facts", size=6, color=VIOLET, bold=True,
            anchor=MSO_ANCHOR.MIDDLE)

    # bottom row: audit, insight + learning
    uy, uh = 5.07, 0.8
    cv.rect(ix, uy, 2.5, uh, YELLOW_T, GOLD, 2.25, R, 0.08)
    cv.text(ix + 0.1, uy + 0.05, 1.9, uh - 0.08,
            [[("Eval gate · Cloud Build", {"bold": True, "size": 7.5})],
             [("Golden set + held-out set pass before any prompt, skill or model change. Weekly blind sample "
               "labelled by your experts.", {})]], size=6.1, after=1)
    eval_tag(cv, ix + 2.5 - 0.54, uy + 0.06)
    pillar_tag(cv, ix + 0.1, uy - 0.125, 5)
    card(cv, ix + 2.6, uy, 1.6, uh, "Change passport · BigQuery", "One hash-chained row per event: "
                                                                  "tamper-evident.")
    card(cv, ix + 4.3, uy, 1.35, uh, "Measured per pod", "Cycle time, rework, defects, cost per change.")
    card(cv, ix + 5.75, uy, iw - 5.75, uh, "Codex Enterprise",
         "Model Armor screens every prompt and response; enterprise data protection signed.", icon="openai")

    # ---------------------------------------------------------- right: systems of record
    sx, sw = 10.5, 2.38
    cv.rect(sx, top, sw, 0.28, BLACK)
    cv.text(sx + 0.1, top, sw - 0.2, 0.28, [[("SYSTEMS OF RECORD", {"bold": True, "track": 150}),
                                            ("   read · write", {"color": "BFBFBF"})]],
            size=7.5, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    cv.rect(sx, top + 0.28, sw, bot - top - 0.28, WHITE, RULE, 0.75)
    marks = {"Jira": "jira", "Confluence": "confluence", "Google Drive": "googledrive", "Git": "git",
             "Salesforce": "salesforce", "Zephyr Scale": "ZS", "Copado": "Co"}
    systems = [("Jira", "stories, criteria", "brief, status to Done"),
               ("Confluence", "designs, rules", "design draft, as-built"),
               ("Google Drive", "specs, mapping sheets", None),
               ("Git", "Apex, LWC, metadata", "branch, pull request"),
               ("Salesforce", "Health, Data, Marketing Cloud", "DEV sandbox deploy"),
               ("Zephyr Scale", None, "test cases, results"),
               ("Copado", "promotions, test runs", "user story, SIT to UAT")]
    yy = top + 0.38
    for n, rd, wr in systems:
        rh = 0.27 + 0.15 * sum(1 for t_ in (rd, wr) if t_)
        mk = marks[n]
        if len(mk) == 2:
            text_badge(cv, mk, sx + 0.1, yy, 0.18, NAVY)
        else:
            logo(cv, mk, sx + 0.1, yy, 0.18)
        cv.text(sx + 0.34, yy, sw - 0.44, 0.18, n, size=7.5, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        ly = yy + 0.19
        for tag, txt, col in (("READ", rd, VIOLET), ("WRITE", wr, MAGENTA)):
            if not txt:
                continue
            cv.rect(sx + 0.1, ly + 0.02, 0.38, 0.12, WHITE, col, 0.5, R, 0.5)
            cv.text(sx + 0.1, ly + 0.02, 0.38, 0.12, tag, size=5, bold=True, color=col, align=PP_ALIGN.CENTER,
                    anchor=MSO_ANCHOR.MIDDLE)
            cv.text(sx + 0.54, ly, sw - 0.64, 0.16, txt, size=6, color=INK, anchor=MSO_ANCHOR.MIDDLE)
            ly += 0.15
        yy += rh
    cv.rect(sx + 0.1, yy + 0.02, sw - 0.2, 0.55, WHITE, MUTE, 0.75, R, 0.08, dash="dash")
    cv.text(sx + 0.18, yy + 0.05, sw - 0.36, 0.5,
            [[("Production", {"bold": True, "size": 7.5})],
             [("The owning team deploys after CAB. No agent credential, no agent path.", {"color": MUTE})]],
            size=6, after=1)
    # cross-lane arrows
    cv.arrow(sx, 2.2, ix + iw, 2.2, VIOLET, 1.5)
    cv.arrow(ix + iw, ry + 1.2, sx, ry + 1.2, MAGENTA, 1.5)
    # user to runtime, and back
    cv.arrow(lx + lw - 0.1, 3.9, ix + 0.1, 3.9, BLACK, 1.5)
    badge(cv, lx + lw + 0.02, 3.66, 2)
    # status and links back to the LWC
    cv.arrow(ix + 0.1, ry + 0.25, lx + lw + 0.08, ry + 0.25, BLACK, 1.0, dash="dash", head=False)
    cv.arrow(lx + lw + 0.08, ry + 0.25, lx + lw + 0.08, 2.75, BLACK, 1.0, dash="dash", head=False)
    cv.arrow(lx + lw + 0.08, 2.75, lx + lw - 0.1, 2.75, BLACK, 1.0, dash="dash")
    badge(cv, lx + lw + 0.12, 2.86, 5)

    # ---------------------------------------------------------- bottom: every run, step by step
    sy = 6.07
    cv.text(0.45, sy, 1.05, 0.4, [[("EACH RUN", {"bold": True, "track": 150})],
                                  [("step by step", {"color": MUTE})]], size=6.3, anchor=MSO_ANCHOR.MIDDLE)
    steps = [("01 Understand", "Requirements", "s"), ("H1", "product owner", "g"), ("02 Design", "Architect + CG", "s"),
             ("H2", "architect + pods", "g"), ("03 Build", "Developer", "s"), ("04 Verify", "Review + Test", "s"),
             ("H3", "tech lead + security", "g"), ("05 Promote", "Release · SIT, UAT", "s"),
             ("H4", "business UAT", "g"), ("07 Prepare", "Release · CAB pack", "s"), ("CAB", "release owner", "g"),
             ("08 Deploy", "owning team", "n"), ("09 Close", "resync, Jira Done", "s")]
    x0, cwid, gap = 1.55, 0.82, 0.05
    for i, (n, sub, kind) in enumerate(steps):
        x = x0 + i * (cwid + gap)
        fill, line, dash = {"s": (WHITE, CYAN_D, None), "g": (YELLOW, YELLOW, None),
                            "n": (WHITE, MUTE, "dash")}[kind]
        cv.rect(x, sy, cwid, 0.42, fill, line, 0.75, R, 0.25, dash=dash)
        cv.text(x + 0.03, sy, cwid - 0.06, 0.42, [[(n, {"bold": True, "size": 6.5})], [(sub, {"size": 5.3,
                                                                                             "color": INK})]],
                size=6, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if kind == "s" and n != "09 Close":
            eval_tag(cv, x + (cwid - 0.46) / 2, sy + 0.47)
        if i < len(steps) - 1:
            cv.arrow(x + cwid, sy + 0.21, x + cwid + gap, sy + 0.21, MUTE, 0.75)
    cv.text(0.45, sy + 0.47, 1.05, 0.16, [[("EVALS", {"bold": True})], ], size=5.5, color=GOLD,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, sy + 0.62, 1.05, 0.2, "scored before it moves", size=5.3, color=MUTE)
    set_notes(s, HLD_NOTES)
    return s


# ================================================================== slide 11: return on investment
ONE_YEAR_TODAY = 16.0e6
ONE_YEAR_HARNESS = 7.0e6
ROI_NOTES = """SLIDE: What it means for Ascension: the return on the investment   (about 2 minutes)

KEY MESSAGE
Ascension invests {inv} once. From go-live it gets {save} back every year: {today} a year today becomes {harness}. That is a {roi} return in the first year, paid back in under {months} months.

WALK IT
- The bars: what Ascension spends today, what it spends with the harness, the yearly saving, and the one-time investment, all on the same scale. The saving bar is bigger than the investment bar: the first year alone pays for the build almost twice.
- Right: first-year ROI, payback and the return multiple.
- Beyond the money: the measured and planned delivery results from earlier slides, so the saving has a mechanism behind it.
- Black band: how each number is built, and the floor we commit to.

HOW THE NUMBERS ARE BUILT (for you, not the slide)
- Investment = fixed build fee {fee} + Google Cloud and model usage during the build, at cost, about {plat}.
- Saving = {today} today minus {harness} with the harness, the first full year after go-live with every pod live; the {harness} includes agent run costs and the managed service.
- First-year ROI = (saving minus investment) / investment.
- The 20-25% lower run cost per pod on the business outcomes slide is the floor we commit to; this slide is the target, confirmed against each pod's Phase 0 baseline.

BE READY FOR
- "Is the ROI guaranteed?" The floor and the phase exits are the commitment; these numbers are the target, measured pod by pod.
- "What about the people?" Ascension chooses: redeploy to backlog, absorb through attrition, or keep the team and deliver more."""


def roi_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    save = ONE_YEAR_TODAY - ONE_YEAR_HARNESS
    fee = plan_slides.build_price()[1]
    plat = sum((plan_slides.PLATFORM_EARLY if p[3] <= 11 else plan_slides.PLATFORM_SCALE) * plan_slides.months(p)
               for p in plan_slides.PHASES)
    inv = fee + plat
    roi = (save - inv) / inv
    months_back = int(inv / save * 12) + 1
    cv.header("ASCENSION AGENTIC HARNESS · WHAT IT MEANS FOR ASCENSION",
              "Return on investment: %s back every year on a %s build" % (money(save), "$%.1fM" % (inv / 1e6)),
              "Every squad of 4-5 developers becomes 1 developer directing the harness agent, plus 1 QA. "
              "All pods, first full year after go-live.")
    X0, W = 0.45, 12.43

    # ---- the investment and the return, on one scale
    bw_max, bx = 5.0, 2.55
    cv.label(X0, 1.36, 6, "The investment and the return, a year")
    rows = [("Spend today", "a year, all pods", ONE_YEAR_TODAY, GREY, "A6A6A6", MUTE),
            ("With the harness", "a year, agents included", ONE_YEAR_HARNESS, BLACK, None, BLACK),
            ("Saved", "every year from go-live", save, YELLOW, BLACK, BLACK),
            ("Investment", "once, months 1 to 18", inv, NAVY, None, NAVY)]
    for i, (lab, sub, v, fill, line, col) in enumerate(rows):
        y = 1.62 + i * 0.47
        cv.text(X0, y, bx - X0 - 0.1, 0.38, [[(lab, {"bold": True, "size": 9})], [(sub, {"color": MUTE})]],
                size=6.5, anchor=MSO_ANCHOR.MIDDLE)
        w = bw_max * v / ONE_YEAR_TODAY
        cv.rect(bx, y + 0.03, w, 0.32, fill, line, 1.0 if line else 0.75)
        cv.text(bx + w + 0.1, y, 1.2, 0.38, "$%.1fM" % (v / 1e6) if v == inv else money(v), size=13,
                bold=i >= 2, color=col, anchor=MSO_ANCHOR.MIDDLE)
    # ---- ROI hero
    hx, hw = 9.0, X0 + W - 9.0
    fx, fy, fw, fh = cv.frame(hx, 1.3, hw, 2.3, YELLOW_T, 0.06)
    cv.label(fx + 0.3, fy + 0.22, fw - 0.6, "First-year return on investment")
    cv.text(fx + 0.3, fy + 0.45, fw - 0.6, 0.95, "%d%%" % round(100 * roi), size=60, bold=True,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.3, fy + 1.45, fw - 0.6, 0.65,
            [[("Paid back in under %d months" % months_back, {"bold": True})],
             [("%.1fx the investment back in year one" % (save / inv), {"color": MUTE})]], size=10, after=2)

    # ---- beyond the money
    cv.label(X0, 3.83, 6, "Beyond the money: what Ascension gets back")
    tiles = [("90 → 15-20 days", "to launch a campaign", "about 80% faster, recorded averages"),
             ("2 weeks → 2 days", "for a Health Cloud task", "story to UAT sign-off"),
             ("75-85%", "faster test-case preparation", "measured with QA agents"),
             ("2-3x", "campaigns per quarter", "same squad; people still approve")]
    tw = (W - 3 * 0.2) / 4
    for i, (big, lab, sub) in enumerate(tiles):
        x = X0 + i * (tw + 0.2)
        cv.rect(x, 4.05, tw, 1.12, WHITE, RULE, 0.75)
        cv.rect(x, 4.05, 0.06, 1.12, CYAN)
        cv.text(x + 0.2, 4.12, tw - 0.3, 0.45, big, size=20, font=LIGHT, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.2, 4.58, tw - 0.3, 0.22, lab, size=9, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.2, 4.82, tw - 0.3, 0.22, sub, size=7.5, color=MUTE, anchor=MSO_ANCHOR.MIDDLE)

    # ---- how the numbers are built
    by_, bh_ = 5.38, 1.0
    cv.rect(X0, by_, W, bh_, BLACK)
    cells = [("Investment", "$%.1fM" % (inv / 1e6), "build fee %s + cloud and model usage at cost %s" % (
                 money(fee), "$%.2fM" % (plat / 1e6))),
             ("Annual saving", money(save), "%s today − %s with the harness; agents and managed service "
                                             "included" % (money(ONE_YEAR_TODAY), money(ONE_YEAR_HARNESS))),
             ("Floor we commit to", "20-25%", "lower net run cost per pod, measured against each pod's baseline")]
    cwid = W / 3
    for i, (lab, big, small) in enumerate(cells):
        cx = X0 + 0.25 + i * cwid
        cv.text(cx, by_ + 0.1, cwid - 0.4, 0.18, lab, size=8, color="BFBFBF")
        cv.text(cx, by_ + 0.3, cwid - 0.4, 0.38, big, size=20, bold=True,
                color=(WHITE, YELLOW, CYAN)[i], anchor=MSO_ANCHOR.MIDDLE)
        cv.text(cx, by_ + 0.7, cwid - 0.4, 0.25, small, size=7, color="BFBFBF")
    cv.text(X0, 6.5, W, 0.32,
            "Ascension's spend across all pods, about %s a year, as provided. The harness figure is the first full "
            "year after the 18-month implementation, with every pod live. First-year ROI = (saving − "
            "investment) ÷ investment. Planning estimates, confirmed against each pod's Phase 0 baseline."
            % money(ONE_YEAR_TODAY), size=6.5, color=MUTE)
    set_notes(s, ROI_NOTES.format(inv="$%.1fM" % (inv / 1e6), save=money(save), today=money(ONE_YEAR_TODAY),
                                  harness=money(ONE_YEAR_HARNESS), roi="%d%%" % round(100 * roi),
                                  months=months_back, fee=money(fee), plat="$%.2fM" % (plat / 1e6)))
    return s


# ================================================================== slides 15 + 16: team and build cost
TEAM_COST_NOTES = """SLIDE: The team and the build cost   (about 2 minutes)

KEY MESSAGE
Seventeen people at peak across ten roles build the Agentic Harness in eighteen months, for one fixed build fee of {fee}, invoiced only as each phase exit is signed.

WALK IT
- Left: who we bring, how many at peak, and when they are on the team.
- Right: the one number for months 1 to 18. Fixed, paid by phase exit, so Ascension pays for outcomes it has signed.

BE READY FOR
- "Why so many harness engineers?" They build the agents, the run loop, the gateway and the evals, then tune them in each pod.
- "What happens after month 18?" A small run team keeps the harness running as a managed service; that is a separate, later decision.
- Rates are assumed for sizing; replace them with the Insight Global rate card before this goes to the client."""


def team_cost_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    fee = plan_slides.build_price()[1]
    people = plan_slides.people_at_peak()
    cv.header("ASCENSION AGENTIC HARNESS · TEAM AND BUILD COST",
              "%d people, %d roles, %s to build in eighteen months" % (people, len(plan_slides.ROLES), money(fee)),
              "The team we bring for months 1 to 18, and one fixed build fee, invoiced as each phase exit is signed.")
    X0 = 0.45
    cols = [("Role", 4.0), ("Peak", 0.8), ("On the team", 1.2)]
    tw = sum(w for _, w in cols)
    y = 1.4
    x = X0
    for name, w in cols:
        cv.text(x + 0.1, y, w - 0.1, 0.26, name, size=9, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        x += w
    cv.rect(X0, y + 0.3, tw, 0.015, BLACK)
    y += 0.36
    rh = (6.45 - y) / (len(plan_slides.ROLES) + 1)
    for i, r in enumerate(plan_slides.ROLES):
        if i % 2 == 0:
            cv.rect(X0, y, tw, rh, GREY)
        cv.rect(X0 + 0.12, y + rh / 2 - 0.06, 0.12, 0.12, r[4])
        cv.text(X0 + 0.34, y, cols[0][1] - 0.4, rh, r[0], size=9.5, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(X0 + cols[0][1], y, cols[1][1], rh, plan_slides.peak(r), size=10, bold=True,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(X0 + cols[0][1] + cols[1][1] + 0.1, y, cols[2][1] - 0.1, rh, plan_slides.when(r), size=9,
                color=MUTE, anchor=MSO_ANCHOR.MIDDLE)
        y += rh
    cv.rect(X0, y, tw, 0.015, BLACK)
    cv.text(X0 + 0.34, y + 0.02, cols[0][1], rh, "Total at peak", size=9.5, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(X0 + cols[0][1], y + 0.02, cols[1][1], rh, str(people), size=11, bold=True, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE)
    cv.text(X0 + cols[0][1] + cols[1][1] + 0.1, y + 0.02, cols[2][1], rh, "all offshore", size=9, color=MUTE,
            anchor=MSO_ANCHOR.MIDDLE)

    # the build cost
    cx, cw = X0 + tw + 0.5, 12.88 - (X0 + tw + 0.5)
    fx, fy, fw, fh = cv.frame(cx, 1.4, cw, 3.2, WHITE, 0.06)
    cv.label(fx + 0.4, fy + 0.35, fw - 0.8, "Build cost · months 1 to 18")
    cv.text(fx + 0.4, fy + 0.7, fw - 0.8, 1.3, money(fee), size=80, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(fx + 0.4, fy + 2.1, fw - 0.8, 0.8,
            [[("Fixed fee for the whole build.", {"bold": True})],
             [("Invoiced only when each phase exit is signed: Ascension pays for outcomes it has accepted.",
               {"color": MUTE})]], size=11, after=3)
    facts = [("%d" % people, "people at peak"), ("18", "months, seven phases"), ("100%", "offshore delivery")]
    fw3 = (cw - 2 * 0.25) / 3
    for i, (big, small) in enumerate(facts):
        x = cx + i * (fw3 + 0.25)
        cv.rect(x, 4.85, fw3, 1.25, GREY)
        cv.text(x + 0.25, 4.98, fw3 - 0.5, 0.6, big, size=32, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.25, 5.6, fw3 - 0.5, 0.3, small, size=9, color=MUTE)
    cv.text(cx, 6.3, cw, 0.3, "Rates assumed for sizing; replace with the Insight Global rate card before sharing.",
            size=6.5, color=MUTE)
    set_notes(s, TEAM_COST_NOTES.format(fee=money(fee)))
    return s
