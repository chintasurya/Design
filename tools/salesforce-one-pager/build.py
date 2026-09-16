"""Build the Salesforce certification-linking one-pager.

The AWS one-pager is used as the template so the master, theme, Trenda type
styles, header and footer all carry over untouched; only the title, the body
copy and the screenshots are replaced.
"""
import copy
import os
import sys

from lxml import etree
from pptx import Presentation
from pptx.util import Emu, Inches

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content
import measure

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"a": A, "r": R}
def q(tag):
    return f"{{{A}}}{tag}"

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
REPO = os.path.dirname(os.path.dirname(HERE))
# the AWS one-pager is the template: master, theme, Trenda styles, header/footer
SRC = os.path.join(
    ASSETS, "IG_Consulting_-_AWS_Certification_Linking_Instructions_-_One_Pager.pptx")
OUT = os.path.join(
    REPO, "docs",
    "IG_Consulting_-_Salesforce_Certification_Linking_Instructions_-_One_Pager.pptx")

TITLE = "Salesforce Certification Linking: How-To Guide"

# Layout, in inches. Text keeps the AWS left margin; screenshots are inset a
# little so they read as figures rather than as a full-bleed band.
TEXT_LEFT, TEXT_WIDTH = 0.65, 7.59
SHOT_WIDTH = 7.30
SHOT_LEFT = (8.5 - SHOT_WIDTH) / 2
TOP = 1.22
GAP_BEFORE_SHOT = 0.12
GAP_AFTER_SHOT = 0.14
LOGO_TOP = 10.19   # footer logo on the layout; content must clear it


def para_templates(body_tf):
    """Map each paragraph style to a template paragraph from the AWS slide."""
    p = body_tf.paragraphs
    return {
        "head": p[0]._p, "body": p[1]._p, "bullet": p[2]._p,
        "prereq": p[6]._p, "num": p[7]._p, "sub": p[23]._p, "last": p[24]._p,
    }


def run_templates(body_tf):
    """A bold and a regular run for each paragraph style, cloned for new text."""
    p = body_tf.paragraphs
    plain, bold = {}, {}
    bold["head"] = p[0].runs[0]._r
    plain["body"] = p[1].runs[0]._r
    bold["bullet"], plain["bullet"] = p[2].runs[0]._r, p[2].runs[1]._r
    plain["prereq"] = p[6].runs[0]._r
    bold["num"], plain["num"] = p[7].runs[0]._r, p[7].runs[3]._r
    plain["sub"] = p[23].runs[0]._r
    bold["last"], plain["last"] = p[24].runs[0]._r, p[24].runs[1]._r
    # styles that only ever appear in one weight still need the other
    plain["head"] = plain["body"]
    bold["body"] = bold["bullet"]
    bold["prereq"] = bold["num"]
    bold["sub"] = bold["num"]
    return plain, bold


SPACE_BEFORE_HEAD = 800   # hundredths of a point, in place of a blank line


def make_para(kind, segments, templates, plain, bold, rel_for, number=None,
              space_before=False):
    """Clone a template paragraph and fill it with the given runs."""
    p = copy.deepcopy(templates[kind])
    pPr = p.find(q("pPr"))
    if number is not None:
        # each text box would otherwise restart its own list at 1
        pPr.find(q("buAutoNum")).set("startAt", str(number))
    if space_before:
        spc = pPr.find(q("spcBef"))
        if spc is None:
            spc = etree.Element(q("spcBef"))
            pPr.insert(0, spc)
        for child in list(spc):
            spc.remove(child)
        etree.SubElement(spc, q("spcPts")).set("val", str(SPACE_BEFORE_HEAD))
    for r in p.findall(q("r")) + p.findall(q("endParaRPr")) + p.findall(q("br")):
        p.remove(r)
    for seg in segments:
        text, is_bold = seg[0], seg[1]
        src = (bold if is_bold else plain)[kind]
        r = copy.deepcopy(src)
        rPr = r.find(q("rPr"))
        # drop any hyperlink inherited from the template run
        for h in rPr.findall(q("hlinkClick")):
            rPr.remove(h)
        if is_bold:
            rPr.set("b", "1")
        elif "b" in rPr.attrib:
            del rPr.attrib["b"]
        if len(seg) > 2:
            h = etree.SubElement(rPr, q("hlinkClick"))
            h.set(f"{{{R}}}id", rel_for(seg[2]))
        t = r.find(q("t"))
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        p.append(r)
    return p


def clone_textbox(slide, source_sp, name, left, top, width):
    """Copy the AWS body text box (keeping its bodyPr) as an empty text box."""
    sp = copy.deepcopy(source_sp._element)
    slide.shapes._spTree.append(sp)
    shape = slide.shapes[-1]
    shape.name = name
    shape.left, shape.top, shape.width = Inches(left), Inches(top), Inches(width)
    txBody = shape.text_frame._txBody
    for p in txBody.findall(q("p")):
        txBody.remove(p)
    return shape, txBody


SHADOW = f"""<a:effectLst xmlns:a="{A}">
  <a:outerShdw blurRad="50800" dist="38100" dir="2700000" algn="tl" rotWithShape="0">
    <a:prstClr val="black"><a:alpha val="40000"/></a:prstClr>
  </a:outerShdw>
</a:effectLst>"""


def add_shot(slide, path, left, top, width):
    """Place a screenshot at a fixed width, with the AWS drop shadow."""
    from PIL import Image
    with Image.open(path) as im:
        aspect = im.size[1] / im.size[0]
    pic = slide.shapes.add_picture(path, Inches(left), Inches(top), Inches(width),
                                   Inches(width * aspect))
    pic._element.spPr.append(etree.fromstring(SHADOW))
    return pic


def main():
    prs = Presentation(SRC)
    slide = prs.slides[0]
    shapes = {sh.name: sh for sh in slide.shapes}
    body = shapes["TextBox 9"]
    body_tf = body.text_frame

    templates = para_templates(body_tf)
    plain, bold = run_templates(body_tf)

    HLINK = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
    cache = {}
    def rel_for(url):
        if url not in cache:
            cache[url] = slide.part.relate_to(url, HLINK, is_external=True)
        return cache[url]

    # Title
    title = shapes["TextBox 4"]
    title.width = Inches(7.6)
    title.text_frame.paragraphs[0].runs[0].text = TITLE

    # Drop the AWS screenshot group; the Salesforce shots replace it.
    grp = shapes["Group 18"]._element
    grp.getparent().remove(grp)

    blocks = [content.WHY, content.TRAILBLAZER, content.CLOSING]
    shots = [os.path.join(ASSETS, "shot_academy.png"),
             os.path.join(ASSETS, "shot_company.png")]

    y = TOP
    boxes = []
    for i, block in enumerate(blocks):
        h = measure.block_height(block, TEXT_WIDTH)
        boxes.append((block, y, h))
        y += h
        if i < len(shots):
            y += GAP_BEFORE_SHOT
            from PIL import Image
            with Image.open(shots[i]) as im:
                aspect = im.size[1] / im.size[0]
            add_shot(slide, shots[i], SHOT_LEFT, y, SHOT_WIDTH)
            y += SHOT_WIDTH * aspect + GAP_AFTER_SHOT

    step = 0
    seen_head = False
    for i, (block, top, h) in enumerate(boxes):
        shape, txBody = clone_textbox(slide, body, f"Body {i + 1}", TEXT_LEFT, top, TEXT_WIDTH)
        for kind, segments in block:
            number = None
            if kind in ("num", "last"):
                step += 1
                number = step
            space_before = kind == "head" and seen_head
            if kind == "head":
                seen_head = True
            txBody.append(make_para(kind, segments, templates, plain, bold, rel_for,
                                    number=number, space_before=space_before))
        shape.height = Inches(h)

    # the original body box was only a template
    body._element.getparent().remove(body._element)

    core = prs.core_properties
    core.title = TITLE
    core.subject = "Linking Salesforce certifications to Insight Global, LLC"
    core.keywords = "Salesforce, certification, Trailblazer, Trailhead, partner"
    core.last_modified_by = "Insight Global Consulting"

    print(f"content bottom: {y:.2f}in (logo at {LOGO_TOP}in)")
    assert y < LOGO_TOP - 0.2, f"content runs into the footer logo: {y:.2f}in"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    prs.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
