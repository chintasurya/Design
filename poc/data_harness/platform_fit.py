"""One-slide preview: Platform fit. Core benefits, and how the platform is built, scales, stays accurate, protects
data and is controlled. Black muted IG style. Slide 10 of the Agentic Harness deck (build_data_harness_deck.py); this script also
renders it alone.

    python3 platform_fit.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import R, SRC, logo, new_slide
from build_mad_ig_deck import CYAN, MAGENTA, YELLOW, set_notes
from footer import fix_footers
from sierra_voice import CARD, CARD2, EDGE, GATE, T1, T2, T3, gbar
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "platform_fit.pptx")
TINTS = {CYAN: "06262B", YELLOW: "2B2508", MAGENTA: "2B0716"}

NOTES = """SLIDE: Platform fit   (about 2-3 minutes)

KEY MESSAGE
One harness serves every pod and three jobs: delivery, campaigns and the Sierra voice agent. Each agent is built once, scales across pods without losing accuracy, and stays under the same controls.

WALK IT
- Top: one harness, three jobs, sharing the knowledge graph, governance, evals, approvals and the change passport.
- How we build: one definition per agent plus pod skill packs; versioned prompts, skills and model; an eval gate before any new version ships; pods onboard one at a time.
- How it scales (concurrency): each request is its own isolated run; fair share for every pod, a per-pod cap set in config so no pod crowds out another; scales with demand within model and API quotas, sized in the Phase 0 load test; extra requests wait, none are dropped. If asked for numbers: our starting design is a few runs per pod and a few dozen overall, both settings.
- How it stays accurate: cited facts only; the same eval bar for every pod, max 5 retries then an owner; load changes the wait, not the answer, because runs share no memory; measured every run.
- How we protect data (measured): share of sensitive fields classified by DLP and approved in Collibra (target 100% before use); masking policy tags verified against the schema every run, drift flagged; negative-access tests each release prove agent identities cannot read raw PHI (target zero); every PHI access logged, releases reconciled, access reviewed each quarter.
- How we control: no production access, guardrails, people decide at the gates, quotas and a kill switch.
- Bottom: the core benefits beyond cost: consistency, reuse, knowledge kept, quality, auditability, safe by design."""


def panel(cv, x, y, w, h, title, sub=""):
    cv.rect(x, y, w, h, CARD2, None, shape=R, radius=0.02)
    cv.rect(x, y, w, 0.28, "2B2B2B", None)
    cv.text(x + 0.12, y, w - 0.24, 0.28, [[(title, {"bold": True, "track": 120, "color": T1}),
                                           ("   " + sub, {"color": T2})] if sub else
                                          [(title, {"bold": True, "track": 120, "color": T1})]],
            size=6.4, anchor=MSO_ANCHOR.MIDDLE)


def build(prs, layout, colorful=False):
    """colorful: IG cyan, yellow and magenta per job and per column (black deck); else muted greys."""
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
        jc = (CYAN, MAGENTA, YELLOW)[k] if colorful else CYAN
        cv.rect(x, ty, jw, th, TINTS[jc] if colorful else CARD, jc, 1.0 if colorful else 0.75, R, 0.12)
        tx = x + 0.12
        if ic:
            logo(cv, ic, tx, ty + 0.14, 0.22)
            tx += 0.3
        cv.text(tx, ty, x + jw - tx - 0.08, th, [[(t, {"bold": True, "color": T1})], [(d, {"color": T2,
                                                                                         "size": 5.6})]],
                size=7.2, anchor=MSO_ANCHOR.MIDDLE)
    sx = 1.95 + 3 * (jw + 0.12) + 0.05
    cv.text(sx, ty, 12.88 - sx, th, [[("SHARED BY ALL THREE", {"bold": True, "color": CYAN, "track": 100})],
                                     [("knowledge graph · governance · evals · approvals · change passport",
                                       {"color": T2})]], size=7, anchor=MSO_ANCHOR.MIDDLE, after=1)
    # ---------------------------------------------------------------- build, scale, accuracy, control
    my, mh = 1.95, 3.62
    cols = [("HOW WE BUILD", "", CYAN, [
                ("One definition per agent", "plus a skill pack per pod; a new pod adds skills, not agents"),
                ("Versioned", "prompts, skills and model pinned in config; roll back in one step"),
                ("Eval gate", "a new agent version ships only if it passes its eval set"),
                ("Pod by pod", "onboard one pod, measure it, then the next")]),
            ("HOW IT SCALES", "concurrency", YELLOW, [
                ("One isolated run per request", "own container, context, branch and checkpoint; no shared memory"),
                ("Fair share for every pod", "a per-pod cap, set in config: no pod crowds out another"),
                ("Scales with demand", "runs added as load grows, within model and API quotas; sized in Phase 0"),
                ("Queued, never dropped", "waits its turn, resumes from checkpoints; the wait time is measured")]),
            ("HOW IT STAYS ACCURATE", "accuracy", MAGENTA, [
                ("Cited facts only", "every fact from the graph carries its source; agents never guess"),
                ("Same bar for every pod", "every run scored before it moves; max 5 retries, then an owner"),
                ("Load changes the wait, not the answer", "runs share no memory; two pods on one object are "
                 "sequenced"),
                ("Measured every run", "eval score per agent and pod, first-pass approval, defects after release")]),
            ("HOW WE PROTECT DATA", "measured", CYAN, [
                ("Classified and approved", "share of in-scope sensitive fields classified by DLP and approved "
                 "by a Collibra steward; target 100% before use"),
                ("Masked and verified", "policy tags applied and checked against the schema every run; drift "
                 "flagged"),
                ("Zero unauthorized access", "negative-access tests each release: agent identities cannot read "
                 "raw PHI"),
                ("Every access audited", "PHI access logged, release reconciled, access reviewed each quarter")]),
            ("HOW WE CONTROL", "", MAGENTA, [
                ("No production access", "three identities, tool allowlist"),
                ("Guardrails", "Model Armor in and out; no raw PHI for agents"),
                ("People decide", "human gates H1-H4, CAB, G1-G3; change passport"),
                ("Quotas + kill switch", "per pod and per agent")])]
    cw = (12.43 - 4 * 0.12) / 5
    for k, (t, sub, acc, items) in enumerate(cols):
        x = 0.45 + k * (cw + 0.12)
        if not colorful:
            acc = CYAN
        if colorful:
            tc = "FFFFFE" if acc == MAGENTA else "000000"
            cv.rect(x, my, cw, mh, TINTS[acc], acc, 0.75, R, 0.02)
            cv.rect(x, my, cw, 0.28, acc, None)
            cv.text(x + 0.12, my, cw - 0.24, 0.28, [[(t, {"bold": True, "track": 120}), ("   " + sub, {})] if sub
                                                    else [(t, {"bold": True, "track": 120})]], size=6.6, color=tc,
                    anchor=MSO_ANCHOR.MIDDLE)
        else:
            panel(cv, x, my, cw, mh, t, sub)
        ih = (mh - 0.28 - 0.12 - 3 * 0.08) / 4
        for j, (it, d) in enumerate(items):
            y = my + 0.38 + j * (ih + 0.08)
            gate_ = t == "HOW WE CONTROL" and j == 2
            cv.rect(x + 0.12, y, cw - 0.24, ih, CARD, None)
            cv.rect(x + 0.12, y, 0.05 if colorful else 0.04, ih, YELLOW if gate_ else acc, None)
            cv.text(x + 0.24, y + 0.04, cw - 0.4, ih - 0.08, [[(it, {"bold": True, "size": 7.2,
                                                                   "color": YELLOW if gate_ else
                                                                   (acc if colorful else T1)})],
                                                              [(d, {"color": T2})]], size=6.2,
                    anchor=MSO_ANCHOR.MIDDLE, after=2)
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
