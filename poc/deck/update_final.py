"""Edits on the team's final deck (source/Ascension Agentic Harness - final.pptx).

The final deck is the user's own ordering: 16 slides up to Thank you, rough
slides after it. Only the slides named here are changed; everything else is
left exactly as the user saved it.
"""
import copy
import os
import sys

from pptx import Presentation
from pptx.util import Inches

from build_mad_ig_deck import HERE, set_notes
import interactive_hld
import review_slides

FINAL = os.path.join(HERE, "source", "Ascension Agentic Harness - final.pptx")
OUT = os.path.join(HERE, "..", "Ascension Agentic Harness.pptx")


def by_id(slide):
    return {sh.shape_id: sh for sh in slide.shapes}


def set_text(sh, text):
    """Replace a text box's text, keeping the first run's formatting."""
    tf = sh.text_frame
    paras = tf.paragraphs
    for p in paras[1:]:
        p._p.getparent().remove(p._p)
    runs = paras[0].runs
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    if runs:
        runs[0].text = text
    else:
        paras[0].add_run().text = text


def set_lines(sh, lines):
    """One paragraph per line, each a copy of the first paragraph's formatting."""
    set_text(sh, lines[0])
    first = sh.text_frame.paragraphs[0]._p
    prev = first
    for line in lines[1:]:
        p = copy.deepcopy(first)
        rs = p.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}r")
        rs[0].find("{http://schemas.openxmlformats.org/drawingml/2006/main}t").text = line
        prev.addnext(p)
        prev = p


def drop(sh):
    sh._element.getparent().remove(sh._element)


# ------------------------------------------------------------------ slide 9: a Health Cloud change
# Today: one Health Cloud task, Jira story to UAT sign-off, about two weeks (10 working days).
HC_TODAY = [  # (step, detail, start day, days)
    ("Story intake", "Jira story; criteria unclear; back and forth with the PO", 0, 1),
    ("Clarify requirements", "Confluence, meetings; acceptance criteria agreed", 1, 1),
    ("Impact analysis", "Find the objects, Flows, sharing and who else uses them", 2, 1.5),
    ("Solution design", "Data model, sharing and automation; architect review", 3.5, 1),
    ("Build", "Apex, LWC, Flows and permission sets in DEV", 4.5, 2),
    ("Code review and fixes", "Peer review, Code Analyzer, rework", 6.5, 1),
    ("Test preparation", "Write Zephyr cases and test data by hand", 7.5, 1),
    ("QA and regression", "Run cases, Copado regression, fix defects", 8.5, 1),
    ("Promote and UAT sign-off", "Copado to SIT / UAT; business signs off", 9.5, 0.5),
]
# With the harness: the same task in about two days (48 hours elapsed); agents build overnight.
HC_HARNESS = [  # (agent detail, start hour, hours)
    ("Plans the change, routes agents, enforces gates", 0, 48),
    ("Jira + Confluence into a brief; product owner approves", 0, 3),
    ("Impact and reuse from the graph; architect approves", 3, 5),
    ("Apex, LWC, Flows and sharing in DEV, overnight", 8, 16),
    ("Code, security, sharing; tech lead approves", 24, 6),
    ("Zephyr cases, Copado regression; people sign UAT", 30, 12),
    ("Copado to SIT / UAT; CAB approves production", 42, 4),
]
HC_NOTES = """SLIDE: A Health Cloud change, 2 weeks today vs 2 days with the Agentic Harness   (about 3 minutes)

KEY MESSAGE
Any Health Cloud task on the Network Services pod, from Jira story to UAT sign-off, takes about two weeks today. On the Agentic Harness the same task takes about two days. People still approve at every gate.

WALK IT
- Left, today: nine steps, one hand-off at a time, inside office hours. About 10 working days. Most of the time goes on understanding the story, finding the impact by hand and writing tests by hand.
- Right, with the harness: the same seven agents as every pod, with Health Cloud skills.
  - Day 1 morning: the Requirements Agent turns the story into a brief and the product owner approves (H1). The Architect Agent reads impact and reuse from the knowledge graph and the architect approves (H2).
  - Day 1 afternoon and overnight: the Developer Agent builds in DEV (Apex, LWC, Flows, sharing).
  - Day 2: the Review Agent checks code, security and sharing and the tech lead approves (H3); the Test Agent runs Zephyr cases and Copado regression and people sign UAT (H4); the Release Agent promotes to SIT / UAT.
- Production still goes through CAB in its normal window; the two days are story to UAT sign-off.

THE NUMBERS
- About 80% faster: 10 working days to about 2 days.
- Already measured with agent-assisted delivery: 1-2 weeks down to 2-4 days. The harness adds the graph, the overnight build and the automated tests that take it to about 2 days. The 2 days is the target, confirmed against the Phase 0 baseline.

BE READY FOR
- "Does every task take 2 days?" Small changes take less; large or cross-pod changes take longer because more owners must approve. Two days is the typical Health Cloud task.
- "Who approves?" The same people as today: product owner, architect, tech lead, business owner for UAT, and CAB for production."""


def health_cloud_slide(slide):
    s = by_id(slide)
    set_text(s[3], "A Health Cloud change: 2 weeks today vs 2 days with the Agentic Harness")
    set_text(s[4], "Any Health Cloud task on the Network Services pod, from Jira story to UAT sign-off. "
                   "Same 7 agents, Health Cloud skills.")
    # ---- today
    set_text(s[7], "Today · manual delivery")
    set_text(s[8], "~2 weeks")
    set_text(s[9], "~10 working days; one hand-off at a time, inside office hours")
    x0, x1 = Inches(4.22), Inches(6.04)
    per_day = (x1 - x0) / 10
    for line, lab, day in ((10, 11, 0), (12, 13, 5), (16, 17, 10)):
        s[line].left = int(x0 + per_day * day)
        s[lab].left = s[line].left - Inches(0.28)
        set_text(s[lab], "Day %d" % day)
    drop(s[14])
    drop(s[15])
    for i, (step, detail, start, days) in enumerate(HC_TODAY):
        base = 20 + 6 * i                      # title, detail, bar, label
        set_text(s[base], step)
        set_text(s[base + 1], detail)
        bar = s[base + 2]
        bar.left = int(x0 + per_day * start)
        bar.width = int(per_day * days)
        set_text(s[base + 3], ("%gd" % days))
    # ---- with the harness
    set_text(s[75], "~2 days")
    set_text(s[76], "~2-day critical path; agents build overnight, people approve by day")
    h0, h1 = Inches(10.70), Inches(11.91)
    per_hour = (h1 - h0) / 48
    for line, lab, day in ((78, 79, 0), (80, 81, 1), (84, 85, 2)):
        s[line].left = int(h0 + per_hour * 24 * day)
        s[lab].left = s[line].left - Inches(0.28)
        set_text(s[lab], "Day %d" % day)
    drop(s[82])
    drop(s[83])
    for i, (detail, start, hours) in enumerate(HC_HARNESS):
        desc, bar, lab = 89 + 7 * i, 91 + 7 * i, 92 + 7 * i       # detail, bar, duration label
        set_text(s[desc], detail)
        s[bar].left = int(h0 + per_hour * start)
        s[bar].width = int(per_hour * hours)
        if i:                                                   # the Orchestrator spans the run, no label
            set_text(s[lab], "%dh" % hours)
    # ---- the four numbers
    set_text(s[138], "~80%")
    set_text(s[139], "faster per task")
    set_text(s[140], "~2 weeks to ~2 days, story to UAT")
    set_text(s[143], "2-4 days")
    set_text(s[144], "measured so far")
    set_text(s[145], "Agent-assisted today; the harness takes it to ~2")
    set_text(s[148], "4 gates")
    set_text(s[149], "people still approve")
    set_text(s[150], "Requirements, design, code and UAT")
    set_text(s[156], "Today: a typical Health Cloud task on the Network Services pod, Jira story to UAT sign-off. "
                     "Measured: Agentifying Ascension Ways of Working (1-2 weeks to 2-4 days with agent assistance). "
                     "About 2 days is the harness target, confirmed against the Phase 0 baseline. Production "
                     "release follows the normal CAB window.")
    set_notes(slide, HC_NOTES)


# ------------------------------------------------------------------ slide 3: high-level architecture
def platform_slide(slide):
    s = by_id(slide)
    set_lines(s[18], ["CLI · IDE · app", "start a run with a Jira number"])
    set_lines(s[22], ["the harness reads the story;", "status tracked here"])
    set_text(s[68], "Guardrails in + out · Model Armor")
    set_lines(s[83], ["OpenAI Codex Enterprise;", "model set in config;", "tools portable via MCP"])


EDITS = {"ASCENSION AGENTIC HARNESS \u00b7 PLATFORM": platform_slide,
         "ASCENSION AGENTIC HARNESS · NETWORK SERVICES POD · HEALTH CLOUD": health_cloud_slide}


# New slides from review_slides.py, approved by the user.
#   INSERT_AFTER: a new slide right after the slide with this eyebrow
#   REPLACE:      the slide with this eyebrow is swapped for the new one
#   TO_BACKUP:    the slide moves behind Thank you, after the back-up slides already there
INSERT_AFTER = {"ASCENSION AGENTIC HARNESS \u00b7 PLATFORM": interactive_hld.hld_interactive_slide}
REPLACE = {"ASCENSION AGENTIC HARNESS \u00b7 WHAT IT MEANS FOR ASCENSION": review_slides.roi_slide,
           "ASCENSION AGENTIC HARNESS \u00b7 DELIVERY TEAM": review_slides.team_cost_slide}
TO_BACKUP = ["ASCENSION AGENTIC HARNESS \u00b7 COMMERCIALS"]   # its content now lives on the team and cost slide


def eyebrow(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            return sh.text_frame.text.strip()
    return ""


def _sld(prs, slide):
    return next(e for e in prs.slides._sldIdLst if int(e.get("id")) == slide.slide_id)


def main(src=FINAL, out=OUT):
    prs = Presentation(src)
    for i, slide in enumerate(prs.slides, 1):
        edit = EDITS.get(eyebrow(slide))
        if edit:
            edit(slide)
            print("updated slide %d: %s" % (i, eyebrow(slide)))
    lst = prs.slides._sldIdLst
    light = next(lay for lay in prs.slide_layouts if lay.name == "DEFAULT")
    built = []
    for slide in list(prs.slides):               # build every new slide first, so part names stay unique
        name = eyebrow(slide)
        if name in INSERT_AFTER or name in REPLACE:
            built.append((slide, (INSERT_AFTER.get(name) or REPLACE[name])(prs, light), name in REPLACE, name))
    for slide, new, replace, name in built:
        el = _sld(prs, new)
        lst.remove(el)
        _sld(prs, slide).addnext(el)
        if replace:
            old = _sld(prs, slide)
            prs.part.drop_rel(old.rId)
            lst.remove(old)
        print("%s: %s" % ("replaced" if replace else "inserted after", name))
    closer = next(i for i, sl in enumerate(prs.slides) if sl.slide_layout.name == "Closer_1")
    anchor = list(lst)[closer]
    for slide in list(prs.slides):
        if eyebrow(slide) in TO_BACKUP:
            el = _sld(prs, slide)
            lst.remove(el)
            anchor.addnext(el)
            anchor = el
            print("moved behind Thank you: %s" % eyebrow(slide))
    prs.save(out)
    print("wrote", os.path.abspath(out), "-", len(prs.slides), "slides")


if __name__ == "__main__":
    main(*sys.argv[1:])
