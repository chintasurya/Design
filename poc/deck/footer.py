"""Keep the IG footer fixed: it lives on the slide layout, never on a slide.

Light slides already use the DEFAULT layout, whose footer (black ●●●IG mark and
page number) is part of the layout. Dark slides need the same footer in white,
so this module adds a "DEFAULT DARK" copy of that layout with the white mark and
a white page number, moves every dark slide onto it, and removes any footer
pictures or page numbers that were placed on the slides themselves (those are
the ones that could be dragged).
"""
import copy
import os

from lxml import etree
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.parts.slide import SlideLayoutPart
from pptx.util import Emu

from build_mad_ig_deck import A, FOOTER_TOP, HERE, P

MARK_WHITE = os.path.join(HERE, "assets", "ig-mark-white.png")
DARK_NAME = "DEFAULT DARK"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _q(ns, tag):
    return "{%s}%s" % (ns, tag)


def dark_layout(prs, light):
    """Return the dark copy of `light`, creating it the first time."""
    master = light.slide_master
    for lay in master.slide_layouts:
        if lay.name == DARK_NAME:
            return lay
    pkg = prs.part.package
    partname = pkg.next_partname("/ppt/slideLayouts/slideLayout%d.xml")
    el = copy.deepcopy(light._element)
    part = SlideLayoutPart(partname, light.part.content_type, pkg, el)
    # same relationships as the light layout, with rIds remapped in the XML
    remap = {}
    for rel in list(light.part.rels.values()):
        if rel.is_external:
            continue
        remap[rel.rId] = part.relate_to(rel.target_part, rel.reltype)
    for node in el.iter():
        for attr in (_q(R, "embed"), _q(R, "id"), _q(R, "link")):
            v = node.get(attr)
            if v in remap:
                node.set(attr, remap[v])
    el.find(_q(P, "cSld")).set("name", DARK_NAME)
    # white mark instead of the black one
    _, white_rid = part.get_or_add_image_part(MARK_WHITE)
    for pic in el.iter(_q(P, "pic")):
        if pic.find(".//" + _q(P, "cNvPr")).get("name") == "IG Footer Mark":
            pic.find(".//" + _q(A, "blip")).set(_q(R, "embed"), white_rid)
    # white page number
    for sp in el.iter(_q(P, "sp")):
        if sp.find(".//" + _q(P, "cNvPr")).get("name") == "IG Footer Page Number":
            for rpr in sp.iter(_q(A, "rPr")):
                for old in rpr.findall(_q(A, "solidFill")):
                    rpr.remove(old)
                fill = etree.Element(_q(A, "solidFill"))
                etree.SubElement(fill, _q(A, "srgbClr"), val="FFFFFF")
                rpr.insert(0, fill)
    # register with the master
    rid = master.part.relate_to(part, RT.SLIDE_LAYOUT)
    lst = master._element.find(_q(P, "sldLayoutIdLst"))
    used = [int(x.get("id")) for x in lst] + [int(x.get("id")) for x in
                                               prs.part._element.find(_q(P, "sldMasterIdLst"))]
    etree.SubElement(lst, _q(P, "sldLayoutId"), {"id": str(max(used) + 1), _q(R, "id"): rid})
    for lay in master.slide_layouts:
        if lay.name == DARK_NAME:
            return lay
    raise RuntimeError("dark layout not registered")


def _is_dark(slide):
    bg = slide._element.find(_q(P, "cSld")).find(_q(P, "bg"))
    if bg is None:
        return False
    if bg.find(".//" + _q(A, "blipFill")) is not None:
        return True
    clr = bg.find(".//" + _q(A, "srgbClr"))
    return clr is not None and clr.get("val") == "000000"


def _set_layout(slide, layout):
    for rel in slide.part.rels.values():
        if rel.reltype == RT.SLIDE_LAYOUT:
            rel._target = layout.part


def _drop_slide_footer(slide):
    """Footer marks and page numbers placed on the slide itself: the draggable ones."""
    n = 0
    for sh in list(slide.shapes):
        top = Emu(sh.top).inches if sh.top is not None else 0
        if abs(top - FOOTER_TOP) > 0.05:
            continue
        if sh.shape_type == 13 or sh.name.startswith("IG Footer Page Number"):
            sh._element.getparent().remove(sh._element)
            n += 1
    return n


def fix_footers(prs):
    light = None
    for lay in prs.slide_masters[0].slide_layouts:
        if lay.name == "DEFAULT":
            light = lay
    dark = dark_layout(prs, light)
    report = []
    for i, slide in enumerate(prs.slides, 1):
        if slide.slide_layout.name not in ("DEFAULT", DARK_NAME):
            continue                                  # title and closing layouts carry their own design
        removed = _drop_slide_footer(slide)
        if _is_dark(slide) and slide.slide_layout.name != DARK_NAME:
            _set_layout(slide, dark)
            report.append("slide %d: dark layout%s" % (i, ", removed %d slide-level footer shapes" % removed
                                                       if removed else ""))
        elif removed:
            report.append("slide %d: removed %d slide-level footer shapes" % (i, removed))
    return report
