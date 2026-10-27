"""Preview: what happens behind "create a campaign" in Codex. A sequence view of the Marketing Cloud solution:
who calls whom, in order, and where the trust boundary sits between definitions and counts (agents) and patient-level
data (deterministic services only). Colourful black IG style.

    python3 mc_backend_flow.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import R, SRC, logo, new_slide
from build_mad_ig_deck import BLACK, CYAN, MAGENTA, YELLOW, set_notes
from footer import fix_footers
from sierra_voice import CARD, EDGE, T1, T2, T3
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "mc_backend_flow.pptx")
TINTS = {CYAN: "06262B", YELLOW: "2B2508", MAGENTA: "2B0716", T1: "1A1A1A"}

LANES = [("people", "People", "Codex · approval page", YELLOW),
         ("harness", "Agents", "Orchestrator, Strategist, Analytics, Design, Readiness", CYAN),
         ("googlebigquery", "Gold A · opted in", "consented patients, masked for agents; policy tags", YELLOW),
         ("googlecloudspanner", "Knowledge graph", "semantic layer: definitions, counts, rules · Spanner Graph", CYAN),
         ("googlecloud", "Eligibility service", "deterministic; runs on Gold A records", MAGENTA),
         (None, "Activation engine", "policy checks; unmasks minimum fields", MAGENTA),
         ("salesforce", "Marketing Cloud", "journey + data extension", T1)]

# (kind, from lane, to lane, label, colour); kinds: msg, ret (dashed return), gate, self
ROWS = [("msg", 2, 3, "0  Kept current: aggregates and definitions only, never patient records", YELLOW),
        ("msg", 0, 1, "1  “Build a post-discharge campaign for heart-failure patients”", CYAN),
        ("msg", 1, 3, "2  What is a heart-failure patient? Which data, which rules?", CYAN),
        ("ret", 3, 1, "3  Definition, Gold A table and consent rule, each with its source", T2),
        ("msg", 1, 2, "4  Count the cohort by channel and region", CYAN),
        ("ret", 2, 1, "5  Counts only, never names; patient rows stay masked in BigQuery", T2),
        ("ret", 1, 0, "6  Opportunity Brief + masked Tableau dashboard", T2),
        ("gate", 0, 0, "G1 · marketer + clinical approve the brief", YELLOW),
        ("msg", 1, 6, "7  Build the journey and data extension, paused: no patients yet", CYAN),
        ("msg", 1, 6, "8  Test on test contacts only; a failure goes back to its cause", CYAN),
        ("gate", 0, 0, "G3 · clinical + compliance approve the journey", YELLOW),
        ("msg", 1, 4, "9  Run eligibility on Gold A for the approved rule (no patient data comes back)", CYAN),
        ("self", 4, 4, "10  Consent, contact, STOP, deceased, duplicates; no consent or missing → Gold B", MAGENTA),
        ("ret", 4, 0, "11  Masked pre-send report: counts and exclusions", T2),
        ("gate", 0, 0, "G2 · SME + tech lead approve before send", YELLOW),
        ("msg", 4, 5, "12  Eligible patients, masked keys", MAGENTA),
        ("msg", 5, 6, "13  Unmask the minimum fields; release after G2 + G3, time-limited", MAGENTA),
        ("self", 6, 6, "14  Journey sends; consent re-checked at send", T1),
        ("ret", 6, 2, "15  Results back as aggregates, for measurement", T2)]

NOTES = """SLIDE: what happens behind "create a campaign" in Codex   (about 2 minutes)

KEY MESSAGE
Agents work only with definitions and counts. Patient-level data moves only through deterministic services, and only after people approve.

WALK IT (top to bottom)
0 Before any request, Gold A keeps the knowledge graph current with aggregates and definitions only: what the data means and how much there is, never who the patients are. Masked Gold A rows are still PHI, so they stay in BigQuery.
1 The marketer asks in Codex. 2-3 The agents ask the knowledge graph what a heart-failure patient is; the semantic layer answers with the definition, the Gold A table and the consent rule, each cited. 4-5 They count the cohort in Gold A; masked views return counts, never names. 6 The Opportunity Brief and a masked Tableau dashboard go to people, who approve it (G1).
7-8 The Campaign Design Agent builds the journey and data extension, paused, and the Readiness Agent tests on test contacts; clinical and compliance approve (G3).
9-11 The eligibility service, not an agent, applies the rule to the opted-in patient records in Gold A (consent, contact, STOP, deceased, duplicates). Anyone with no consent or missing information goes to Gold B, where an update request can invite them to opt in. A masked pre-send report goes to the SME and tech lead, who approve (G2).
12-13 Only then does the activation engine check the policy, unmask only the minimum fields for the eligible patients, and release them, time-limited, to Marketing Cloud. 14 The journey sends, with consent re-checked at send. 15 Results come back as aggregates.

BEFORE ANY REQUEST
The data harness keeps Sources, Bronze and Silver current in Google Cloud; consented patients land in Gold A, and patients with no consent or missing information land in Gold B. DLP classifies and a Collibra steward approves the masking."""


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "AGENTIC HEALTHCARE CAMPAIGN PLATFORM · FUNCTIONAL FLOW",
                "Create a campaign in Codex: what happens behind the scenes",
                "Agents work only with definitions and counts. Patient-level data moves only through deterministic "
                "services, and only after people approve.")
    x0, wtot = 0.45, 12.43
    lw = wtot / len(LANES)
    cx = [x0 + lw * (i + 0.5) for i in range(len(LANES))]
    hy, hh = 1.28, 0.62
    top, bot = hy + hh, 6.42
    # trust boundary between the knowledge graph and Gold B
    tb = x0 + lw * 4
    cv.arrow(tb, hy - 0.04, tb, bot + 0.06, MAGENTA, 1.25, dash="dash", head=False)
    # lane headers + lifelines
    for i, (ic, t, d, c) in enumerate(LANES):
        x = x0 + lw * i + 0.05
        w = lw - 0.1
        if i == 5:
            fx, fy, fw, fh = cv.frame(x, hy, w, hh, BLACK, 0.03)
        else:
            cv.rect(x, hy, w, hh, TINTS[c], c, 1.0, R, 0.08)
        tx = x + 0.08
        if ic:
            logo(cv, ic, tx, hy + 0.08, 0.2)
            tx += 0.26
        cv.text(tx, hy + 0.05, x + w - tx - 0.04, 0.24, t, size=8, bold=True, color=c if c != T1 else T1,
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.08, hy + 0.3, w - 0.14, 0.3, d, size=7, color=T2, line=0.9)
        cv.arrow(cx[i], top, cx[i], bot, "3A3A3A", 1.0, dash="sysDot", head=False)
    # rows
    y = top + 0.27
    step = (bot - 0.1 - y) / (len(ROWS) - 1)
    for kind, a, b, label, col in ROWS:
        if kind in ("msg", "ret"):
            x1, x2 = cx[a], cx[b]
            cv.arrow(x1, y, x2, y, col, 1.5 if kind == "msg" else 1.0, dash="dash" if kind == "ret" else None)
            lo, hi = min(x1, x2), max(x1, x2)
            tw = max(hi - lo - 0.1, 0.055 * len(label) + 0.12)
            lx = (lo + hi) / 2 - tw / 2
            lx = min(max(lx, x0), x0 + wtot - tw)
            cv.rect(lx, y - 0.165, tw, 0.14, BLACK, None)
            cv.text(lx, y - 0.165, tw, 0.14, label, size=7, color=T1 if kind == "msg" else T2,
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        elif kind == "gate":
            w = 2.75
            cv.rect(cx[0] - 0.75, y - 0.1, w, 0.2, YELLOW, None, shape=R, radius=0.5)
            cv.text(cx[0] - 0.75, y - 0.1, w, 0.2, label, size=7, bold=True, color="000000",
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        else:                                               # a step inside one lane
            w = 0.055 * len(label) + 0.2
            lx = min(max(cx[a] - w / 2, tb + 0.06 if a >= 4 else x0), x0 + wtot - w)   # patient side stays right
            cv.rect(lx, y - 0.1, w, 0.2, TINTS[col], col, 0.9, R, 0.5)
            cv.text(lx, y - 0.1, w, 0.2, label, size=7, color=T1, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        y += step
    # boundary label + what runs before any request
    cv.rect(tb - 2.6, bot + 0.1, 5.2, 0.2, MAGENTA, None, shape=R, radius=0.5)
    cv.text(tb - 2.6, bot + 0.1, 5.2, 0.2, "←  AGENTS: DEFINITIONS AND COUNTS ONLY   ·   PATIENT-LEVEL DATA: SERVICES "
            "ONLY  →", size=7, bold=True, color="FFFFFE", track=60, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, bot + 0.36, 12.43, 0.2, [[("Before any request: ", {"bold": True, "color": T1}),
                                            ("the data harness keeps Sources → Bronze → Silver current in Google Cloud; "
                                             "consented patients → Gold A, no consent or missing information → Gold B; "
                                             "DLP classifies and a Collibra steward approves the masking.",
                                             {"color": T3})]], size=7, anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, NOTES)
    return s


def main(out=OUT):
    import muted_theme as mt
    prs = Presentation(SRC)
    lst = prs.slides._sldIdLst
    for el in list(lst):
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    s = build(prs, layout)
    mt.min_font(s, 7.0)
    fix_footers(prs)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    prs.save(out)
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
