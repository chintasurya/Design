#!/usr/bin/env python3
"""
Geometry and text-fit checks for the slides this repo generates.

LibreOffice cannot load any file in this sandbox, so the usual render-and-look
pass is not available. This checks arithmetically what that pass would have
caught by eye: shapes off the slide, inconsistent margins, text boxes sitting
on top of each other, and text that will not fit the box it was given.

Text fit is an estimate. Character widths vary by typeface and the deck uses
Trenda IG, which is not installed here, so the width factor below is a
conservative average for a humanist sans. It flags boxes that are close as
well as boxes that are over, and being told about a near miss is the point.

    python3 check_geometry.py <deck.pptx> [first_slide_number]
"""

import re
import sys
import zipfile

EMU = 914400.0
SLIDE_W = 13.333
SLIDE_H = 7.5
MARGIN = 0.38          # the deck's own left/right margin is 0.4"
WIDTH_FACTOR = 0.50    # average glyph width as a fraction of point size
LINE_FACTOR = 1.22     # default line height as a multiple of point size

SP = re.compile(r"<p:sp>.*?</p:sp>", re.S)
OFF = re.compile(r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>')
TXT = re.compile(r"<a:t(?:[^>]*)>(.*?)</a:t>", re.S)
SZ = re.compile(r'sz="(\d+)"')
LNSPC = re.compile(r'<a:spcPct val="(\d+)"/>')
IS_TEXTBOX = re.compile(r'<p:cNvSpPr txBox="1"/>')


def shapes(xml):
    out = []
    for sp in SP.findall(xml):
        m = OFF.search(sp)
        if not m:
            continue
        x, y, w, h = (int(v) / EMU for v in m.groups())
        text = " ".join(TXT.findall(sp)).strip()
        sizes = [int(s) / 100.0 for s in SZ.findall(sp)]
        line = LNSPC.search(sp)
        out.append({
            "x": x, "y": y, "w": w, "h": h,
            "text": text,
            "size": max(sizes) if sizes else 0,
            "line": (int(line.group(1)) / 100000.0) if line else 1.0,
            "is_text": bool(IS_TEXTBOX.search(sp)) and bool(text),
        })
    return out


def fits(s):
    """Estimated lines needed versus lines available."""
    if not s["text"] or not s["size"]:
        return True, 0, 0
    per_line = max(1, int(s["w"] * 72 / (s["size"] * WIDTH_FACTOR)))
    # Count explicit paragraphs as separate blocks.
    need = 0
    for block in s["text"].split(" "):
        need += max(1, -(-len(block) // per_line))
    line_h = s["size"] * LINE_FACTOR * max(s["line"], 1.0) / 72.0
    avail = max(1, int((s["h"] + 0.012) / line_h))
    return need <= avail, need, avail


def overlap(a, b):
    ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
    oy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
    if ox <= 0.02 or oy <= 0.02:
        return 0.0
    return ox * oy


def main():
    path = sys.argv[1]
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    z = zipfile.ZipFile(path)
    slide_names = sorted(
        (n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
        key=lambda n: int(re.search(r"(\d+)", n.split("/")[-1]).group(1)),
    )
    problems = 0
    for name in slide_names:
        n = int(re.search(r"(\d+)", name.split("/")[-1]).group(1))
        if n < first:
            continue
        xml = z.read(name).decode("utf8")
        shp = shapes(xml)
        issues = []

        for s in shp:
            if s["x"] < -0.01 or s["y"] < -0.01:
                issues.append("shape starts off-slide at (%.2f, %.2f)" % (s["x"], s["y"]))
            if s["x"] + s["w"] > SLIDE_W + 0.01:
                issues.append("shape runs past the right edge: ends at %.2f\" (%s)"
                              % (s["x"] + s["w"], s["text"][:34] or "shape"))
            if s["y"] + s["h"] > SLIDE_H + 0.01:
                issues.append("shape runs past the bottom: ends at %.2f\" (%s)"
                              % (s["y"] + s["h"], s["text"][:34] or "shape"))
            if s["is_text"] and s["x"] < MARGIN:
                issues.append("text inside the left margin at x=%.2f\"" % s["x"])
            if s["is_text"]:
                ok, need, avail = fits(s)
                if not ok:
                    issues.append('text needs ~%d lines, box holds ~%d: "%s"'
                                  % (need, avail, s["text"][:52]))

        texts = [s for s in shp if s["is_text"]]
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i], texts[j]
                area = overlap(a, b)
                if area > 0.05:
                    issues.append('text boxes overlap %.2f sq in: "%s" / "%s"'
                                  % (area, a["text"][:26], b["text"][:26]))

        status = "ok" if not issues else "%d ISSUE(S)" % len(issues)
        print("slide %-3d %3d shapes  %s" % (n, len(shp), status))
        for i in issues:
            print("          - " + i)
        problems += len(issues)

    print("\n%d problem(s) across the checked slides" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
