"""Estimate rendered paragraph heights so blocks can be positioned around the
screenshots. Wrapping is measured with the real Trenda faces, which is what
PowerPoint will use.
"""
from PIL import ImageFont

FONT_DIR = "/usr/share/fonts/truetype/ig"
SCALE = 16  # measure at 16x nominal size for sub-point precision

_cache = {}
def _font(bold, pt):
    key = (bold, pt)
    if key not in _cache:
        name = "TrendaIGText-Bold.otf" if bold else "TrendaIGText-Regular.otf"
        _cache[key] = ImageFont.truetype(f"{FONT_DIR}/{name}", int(pt * SCALE))
    return _cache[key]


# marL (indent) and font size per paragraph style, in inches / points
STYLE = {
    "head":   dict(indent=0.0,    size=12.0, spacing=1.0,  after=6.0, before=8.0),
    "body":   dict(indent=0.0,    size=10.5, spacing=1.5,  after=0.0),
    "bullet": dict(indent=0.1875, size=10.5, spacing=1.5,  after=0.0),
    "prereq": dict(indent=0.0,    size=10.5, spacing=1.5,  after=0.0),
    "num":    dict(indent=0.25,   size=10.5, spacing=1.5,  after=0.0),
    "sub":    dict(indent=0.75,   size=10.5, spacing=1.5,  after=0.0),
    "last":   dict(indent=0.25,   size=10.5, spacing=1.5,  after=0.0),
}
RIGHT_INSET = 0.1   # bodyPr default rIns


def _width_pt(text, bold, pt):
    return _font(bold, pt).getlength(text) / SCALE


def line_count(segments, style, box_width):
    """Greedy word wrap across runs of differing weight."""
    avail_pt = (box_width - RIGHT_INSET - style["indent"]) * 72
    words = []
    for seg in segments:
        text, bold = seg[0], seg[1]
        parts = text.split(" ")
        for i, w in enumerate(parts):
            if w == "" and i != len(parts) - 1:
                continue
            words.append((w, bold))
    if not words:
        return 1
    lines, cur = 1, 0.0
    space = _width_pt(" ", False, style["size"])
    for i, (w, bold) in enumerate(words):
        ww = _width_pt(w, bold, style["size"])
        add = ww if cur == 0 else space + ww
        if cur + add > avail_pt and cur > 0:
            lines += 1
            cur = ww
        else:
            cur += add
    return lines


def para_height(kind, segments, box_width, space_before=False):
    style = STYLE[kind]
    n = line_count(segments, style, box_width)
    line_pt = style["size"] * 1.2 * style["spacing"]
    before = style.get("before", 0.0) if space_before else 0.0
    return (n * line_pt + style["after"] + before) / 72.0


def block_height(block, box_width, first_head_spaced=False):
    total, seen_head = 0.0, first_head_spaced
    for kind, segs in block:
        total += para_height(kind, segs, box_width, space_before=(kind == "head" and seen_head))
        if kind == "head":
            seen_head = True
    return total
