"""One-slide preview: Platform fit. Core benefits, how one agent serves many pods at once, and how the platform is
built, measured and controlled. Black muted IG style. Not part of the deck yet.

    python3 platform_fit.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import R, SRC, logo, new_slide
from build_mad_ig_deck import CYAN, YELLOW, set_notes
from footer import fix_footers
from sierra_voice import CARD, CARD2, EDGE, GATE, T1, T2, T3, gbar
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "platform_fit.pptx")

NOTES = """SLIDE: Platform fit   (about 3 minutes)

KEY MESSAGE
One harness serves every pod and three jobs: delivery, campaigns and the Sierra voice agent. An agent is one versioned definition; every request becomes its own isolated run, so ten pods can use the Requirements Agent at once and each gets the same quality. Load changes the wait, not the answer.

ONE AGENT, MANY PODS
- The Requirements Agent is one definition, versioned, that passed its eval set. It is the same for every pod.
- Right now ten pods are using it: ten isolated runs, each with its own context slice from the graph, its own pod skill pack, its own branch and checkpoint. They share no memory.
- Four questions clients ask: ten pods at once (own container per run; up to 3 per pod, about 30 overall; extra requests wait, none dropped; proposed, sized in the Phase 0 load test); same accuracy for all (one tested definition plus the pod's skills and cited facts: load changes the wait, not the answer); two pods on one object (the Change Guardian flags and sequences it); who decides (each pod's product owner at H1, after evals).

BUILD, MEASURE, CONTROL
- Build: one agent definition plus pod skill packs; versioned prompts, skills and models; a new agent version must pass its eval set before release; pods onboard one at a time.
- Measure: eval score per agent and pod, first-pass approval at gates, retries, cited-fact rate, latency and queue wait, defects found after release, and zero PHI exposure in tests.
- Control: three identities with no production access, a tool gateway allowlist, Model Armor guardrails, human gates, the change passport, per-pod quotas and a kill switch per agent or pod.

CORE BENEFITS
Consistency, reuse, faster onboarding of a new pod, quality on every step, auditability, and safety by design."""


def panel(cv, x, y, w, h, title, sub=""):
    cv.rect(x, y, w, h, CARD2, None, shape=R, radius=0.02)
    cv.rect(x, y, w, 0.28, "2B2B2B", None)
    cv.text(x + 0.12, y, w - 0.24, 0.28, [[(title, {"bold": True, "track": 120, "color": T1}),
                                           ("   " + sub, {"color": T2})] if sub else
                                          [(title, {"bold": True, "track": 120, "color": T1})]],
            size=6.4, anchor=MSO_ANCHOR.MIDDLE)


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION AGENTIC HARNESS · PLATFORM FIT",
                "Platform fit: one harness for every pod, every job",
                "Delivery, campaigns and the Sierra voice agent share one graph, one governance layer and one approval "
                "flow. Each agent is built once and serves every pod at once.")
    # ---------------------------------------------------------------- top: three jobs, one platform
    ty, th = 1.3, 0.5
    cv.text(0.45, ty, 1.5, th, [[("ONE HARNESS", {"bold": True, "track": 120, "color": T1})],
                                [("three jobs", {"color": T3, "size": 5.4})]], size=6.4, anchor=MSO_ANCHOR.MIDDLE,
            after=1)
    jobs = [("openai-white", "Delivery", "Codex to production · every pod"),
            ("salesforce", "Campaigns", "Marketing Cloud on governed GCP data"),
            (None, "Sierra voice agent", "bookings, reschedules, questions")]
    jw = 2.45
    for k, (ic, t, d) in enumerate(jobs):
        x = 1.95 + k * (jw + 0.12)
        cv.rect(x, ty, jw, th, CARD, CYAN, 0.75, R, 0.12)
        tx = x + 0.12
        if ic:
            logo(cv, ic, tx, ty + 0.14, 0.22)
            tx += 0.3
        cv.text(tx, ty, x + jw - tx - 0.08, th, [[(t, {"bold": True, "color": T1})], [(d, {"color": T2,
                                                                                         "size": 5.6})]],
                size=7.2, anchor=MSO_ANCHOR.MIDDLE)
    sx = 1.95 + 3 * (jw + 0.12) + 0.05
    cv.text(sx, ty, 12.88 - sx, th, [[("SHARED  ", {"bold": True, "color": CYAN, "track": 100}),
                                      ("knowledge graph · governance · evals · approvals · change passport",
                                       {"color": T2})]], size=6.2, anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- left: one agent, many pods (no flow)
    lx, ly, lw, lh = 0.45, 1.95, 6.95, 3.62
    panel(cv, lx, ly, lw, lh, "ONE AGENT, MANY PODS AT ONCE", "example: 10 pods use the Requirements Agent together")
    ix, iw = lx + 0.12, lw - 0.24
    # the agent: one definition
    ay, ah = ly + 0.38, 0.44
    cv.rect(ix, ay, iw, ah, "06262B", CYAN, 0.9, R, 0.12)
    logo(cv, "harness", ix + 0.12, ay + 0.11, 0.22)
    cv.text(ix + 0.44, ay, 2.2, ah, "Requirements Agent", size=8, bold=True, color=T1, anchor=MSO_ANCHOR.MIDDLE)
    tags = ["one definition", "version 1.4", "passed its eval set", "same for every pod"]
    tx = ix + 2.35
    for t in tags:
        w = 0.2 + 0.052 * len(t)
        cv.rect(tx, ay + 0.11, w, 0.22, CARD, CYAN, 0.6, R, 0.4)
        cv.text(tx, ay + 0.11, w, 0.22, t, size=5.6, color=CYAN, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        tx += w + 0.07
    # ten isolated runs, side by side
    gy = ay + ah + 0.1
    cv.text(ix, gy, iw, 0.18, [[("TEN ISOLATED RUNS, RIGHT NOW", {"bold": True, "color": T3, "track": 100}),
                                ("   each with its own context, skill pack, branch and checkpoint; no shared memory",
                                 {"color": T3})]], size=5.4, anchor=MSO_ANCHOR.MIDDLE)
    runs = [("Network Services", "NS-1234", "RUNNING"), ("Clinical Transformation", "CT-412", "RUNNING"),
            ("Contact Center", "CC-77", "AT H1"), ("Nudge / Demand", "ND-301", "RUNNING"),
            ("VBC outreach", "VBC-88", "RUNNING"), ("QA", "QA-519", "RUNNING"), ("Pod 7", "P7-12", "AT H1"),
            ("Pod 8", "P8-40", "RUNNING"), ("Pod 9", "P9-05", "RUNNING"), ("Pod 10", "P10-21", "RUNNING")]
    tw = (iw - 4 * 0.1) / 5
    th2 = 0.5
    for k, (pod, sid, st) in enumerate(runs):
        x = ix + (k % 5) * (tw + 0.1)
        y = gy + 0.24 + (k // 5) * (th2 + 0.08)
        gate_ = st == "AT H1"
        cv.rect(x, y, tw, th2, CARD, YELLOW if gate_ else "2E6E78", 0.75, R, 0.1)
        cv.text(x + 0.08, y + 0.03, tw - 0.12, 0.2, pod, size=5.9, bold=True, color=T1, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.08, y + 0.26, 0.6, 0.18, sid, size=5.4, color=T3, anchor=MSO_ANCHOR.MIDDLE,
                font="Courier New")
        cw2 = 0.5
        cv.rect(x + tw - cw2 - 0.07, y + 0.27, cw2, 0.16, YELLOW if gate_ else CYAN, None, shape=R, radius=0.4)
        cv.text(x + tw - cw2 - 0.07, y + 0.27, cw2, 0.16, st, size=4.8, bold=True, color="000000",
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # four questions a client asks, answered
    qy = gy + 0.24 + 2 * th2 + 0.08 + 0.14
    qh = ly + lh - 0.1 - qy
    qa = [("Ten pods at once?", "Each request runs on its own container. Up to 3 per pod, about 30 overall; extra "
           "requests wait their turn, none are dropped."),
          ("Same accuracy for all?", "One tested definition, plus that pod's skill pack and cited facts. Load "
           "changes the wait, not the answer."),
          ("Two pods, one object?", "The Change Guardian sees the overlap in the graph, flags it and sequences "
           "the second change."),
          ("Who decides?", "Each pod's own product owner, at H1. Every run is scored by evals before it moves.")]
    qw = (iw - 3 * 0.1) / 4
    for k, (q, ans) in enumerate(qa):
        x = ix + k * (qw + 0.1)
        cv.rect(x, qy, qw, qh, CARD, None)
        cv.rect(x, qy, 0.04, qh, YELLOW if k == 3 else CYAN, None)
        cv.text(x + 0.12, qy + 0.06, qw - 0.18, 0.22, q, size=6.8, bold=True, color=YELLOW if k == 3 else CYAN,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.12, qy + 0.34, qw - 0.18, qh - 0.38, ans, size=6.6, color=T2)
    cv.text(lx + lw - 3.0, ly + 0.02, 2.88, 0.24, "concurrency: proposed, sized in the Phase 0 load test",
            size=5.2, color=T3, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    # ---------------------------------------------------------------- right: build, measure, control
    rx, rw = 7.55, 12.88 - 7.55
    blocks = [("HOW WE BUILD", [("One definition", "per agent, plus pod skill packs"),
                                ("Versioned", "prompts, skills, model in config"),
                                ("Eval gate", "a new version ships only if it passes"),
                                ("Pod by pod", "onboard one, measure, then the next")]),
              ("HOW WE MEASURE", [("Eval score", "per agent, per pod, every run"),
                                  ("First-pass approval", "share accepted at H1-H4, G1-G3"),
                                  ("Grounding + retries", "cited facts, retries per run"),
                                  ("Wait + defects", "queue time, issues after release")]),
              ("HOW WE CONTROL", [("No production access", "three identities, tool allowlist"),
                                  ("Guardrails", "Model Armor in and out, no raw PHI"),
                                  ("People decide", "human gates, change passport"),
                                  ("Quotas + kill switch", "per pod, per agent")])]
    bh = (lh - 2 * 0.1) / 3
    for k, (t, items) in enumerate(blocks):
        y = ly + k * (bh + 0.1)
        panel(cv, rx, y, rw, bh, t)
        cw = (rw - 0.36) / 2
        for j, it in enumerate(items):
            x = rx + 0.14 + (j % 2) * (cw + 0.08)
            yy = y + 0.38 + (j // 2) * 0.36
            cv.rect(x, yy + 0.08, 0.06, 0.06, YELLOW if (k == 2 and j == 2) else CYAN, None,
                    shape=MSO_SHAPE.OVAL)
            cv.text(x + 0.12, yy, cw - 0.12, 0.34, [[(it[0], {"bold": True, "color": T1})],
                                                    [(it[1], {"color": T2, "size": 5.6})]], size=6.4,
                    anchor=MSO_ANCHOR.TOP)
    # ---------------------------------------------------------------- bottom: core benefits
    by, bh2 = 5.72, 1.1
    cv.text(0.45, by, 1.3, bh2, [[("CORE BENEFITS", {"bold": True, "color": T1, "track": 120})],
                                 [("beyond cost", {"color": T3, "size": 5.4})]], size=6.4,
            anchor=MSO_ANCHOR.MIDDLE, after=1)
    benefits = [("Consistency", "Same standards and checks in every pod, every time."),
                ("Reuse", "Build once; a new pod adds skills, not agents."),
                ("Knowledge kept", "The graph keeps what people know when they move on."),
                ("Quality", "Every step scored before it moves."),
                ("Auditability", "Every step, approval and test recorded."),
                ("Safe by design", "No production credentials, no raw PHI for agents.")]
    w = (12.88 - 1.8 - 5 * 0.1) / 6
    for k, (t, d) in enumerate(benefits):
        x = 1.8 + k * (w + 0.1)
        cv.rect(x, by, w, bh2, CARD, None)
        gbar(cv, x, by, 0.05, bh2)
        cv.text(x + 0.16, by + 0.04, w - 0.24, bh2 - 0.08, [[(t, {"bold": True, "size": 8, "color": T1})],
                                                            [(d, {"color": T2})]], size=6.2,
                anchor=MSO_ANCHOR.MIDDLE, after=2)
    set_notes(s, NOTES)
    return s


def main(out=OUT):
    prs = Presentation(SRC)
    lst = prs.slides._sldIdLst
    for el in list(lst):
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    build(prs, layout)
    fix_footers(prs)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    prs.save(out)
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
