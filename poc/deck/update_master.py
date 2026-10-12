"""Refresh the generated plan slides inside the reordered master deck.

The master deck (source/Ascension MAD Approach - master.pptx) is the user's own
ordering and edits. This replaces only the slides named in REFRESH, in place,
with fresh builds from plan_slides.py, and writes the output deck.
"""
import os
import sys

from pptx import Presentation

import plan_slides
from build_mad_ig_deck import HERE, OUT

MASTER = os.path.join(HERE, "source", "Ascension MAD Approach - master.pptx")
REFRESH = {
    "ASCENSION MAD APPROACH · DELIVERY TEAM": plan_slides.team_slide,
    "ASCENSION MAD APPROACH · COMMERCIALS": plan_slides.commercials_slide,
}


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
    prs.save(out)
    print("wrote", os.path.abspath(out), "-", len(prs.slides), "slides")


if __name__ == "__main__":
    main(*sys.argv[1:])
