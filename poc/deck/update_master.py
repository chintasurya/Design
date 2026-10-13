"""Refresh the generated plan slides inside the reordered master deck.

The master deck (source/Ascension MAD Approach - master.pptx) is the user's own
ordering and edits. This replaces only the slides named in REFRESH, in place,
with fresh builds from plan_slides.py, and writes the output deck.
"""
import os
import sys

from urllib.parse import quote

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

import plan_slides
from build_mad_ig_deck import HERE, TXT, rgb
from reword import reword_slide

MASTER = os.path.join(HERE, "source", "Ascension MAD Approach - master.pptx")
OUT = os.path.join(HERE, "..", "Ascension Agentic Harness.pptx")
REFRESH = {
    "ASCENSION MAD APPROACH · DELIVERY TEAM": plan_slides.team_slide,
    "ASCENSION MAD APPROACH · COMMERCIALS": plan_slides.commercials_slide,
}


# The detailed design, opened straight in the draw.io web app from the public repo.
LLD_RAW = ("https://raw.githubusercontent.com/chintasurya/Design/refs/heads/claude/funny-babbage-t29499/"
           "poc/diagrams/Codex-to-Production%20Agentic%20Harness%20LLD.drawio")
LLD_URL = "https://app.diagrams.net/#U" + quote(LLD_RAW, safe="")
LINK_ON = {"ASCENSION AGENTIC HARNESS · PLATFORM": "00D6F2",            # dark slide: cyan
           "ASCENSION AGENTIC HARNESS · TARGET ARCHITECTURE": "00273B"}  # light slide: navy
LINK_NAME = "draw.io link"


def add_lld_link(slide, color):
    if any(sh.name == LINK_NAME for sh in slide.shapes):
        return False
    tb = slide.shapes.add_textbox(Inches(8.6), Inches(6.98), Inches(3.6), Inches(0.22))
    tb.name = LINK_NAME
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    pg = tf.paragraphs[0]
    pg.alignment = PP_ALIGN.RIGHT
    r = pg.add_run()
    r.text = "Open the detailed design in draw.io  \u2197"
    r.font.name = TXT
    r.font.size = Pt(8)
    r.font.bold = True
    r.font.underline = True
    r.font.color.rgb = rgb(color)
    r.hyperlink.address = LLD_URL
    tb.click_action.hyperlink.address = LLD_URL
    return True


def eyebrow(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            return sh.text_frame.text.strip()
    return ""


def main(src=MASTER, out=OUT):
    prs = Presentation(src)
    lst = prs.slides._sldIdLst
    swaps = []
    for i, slide in enumerate(list(prs.slides)):
        build = REFRESH.get(eyebrow(slide))
        if build:
            build(prs, slide.slide_layout)       # build every slide first, so part names stay unique
            swaps.append((list(lst)[i], list(lst)[-1], eyebrow(slide)))
    for old, new, name in swaps:
        lst.remove(new)
        old.addnext(new)
        prs.part.drop_rel(old.rId)
        lst.remove(old)
        print("refreshed slide %d: %s" % (list(lst).index(new) + 1, name))
    for i, slide in enumerate(prs.slides):
        for t in reword_slide(slide):
            print("still says MAD on slide %d: %s" % (i + 1, t[:90]))
    for i, slide in enumerate(prs.slides):
        color = LINK_ON.get(eyebrow(slide))
        if color and add_lld_link(slide, color):
            print("draw.io link on slide %d: %s" % (i + 1, eyebrow(slide)))
    prs.save(out)
    print("wrote", os.path.abspath(out), "-", len(prs.slides), "slides")


if __name__ == "__main__":
    main(*sys.argv[1:])
