"""Cut the one-pager's screenshots out of the source Salesforce guide PDF.

The guide annotates its screenshots with cyan boxes; the Insight Global
one-pagers annotate in gold (FFC000), so the boxes are recoloured on the way
through. Run this only when the source guide changes:

    python3 screenshots.py path/to/Salesforce_Partner_Portal_Certification_Linking_Guide.pdf
"""
import os
import sys

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

RENDER_SCALE = 4          # source PDF is 595x842pt; 4x gives ~300dpi at print size
GOLD = np.array([255, 192, 0], dtype=float)

# (output name, zero-based page, crop box in rendered pixels)
CROPS = [
    ("shot_academy.png", 0, (420, 1765, 2140, 2235)),   # Trailhead Academy -> Employer
    ("shot_company.png", 1, (366, 2075, 2190, 2462)),   # Trailblazer -> My Company
]


def recolor(im):
    """Repaint the guide's cyan callout boxes in Insight Global gold.

    The mask has to clear the cyan strokes without touching Salesforce's own
    navy (#032D60) and blue (#0176D3) UI text, so it also demands a bright
    green channel: only the callout cyan is both blue-dominant and light.
    """
    a = np.array(im.convert("RGB")).astype(float)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    bright = (g > 140) & (b > 160)
    alpha = (np.clip((b - r - 25) / 45.0, 0, 1)
             * np.clip((g - r - 15) / 35.0, 0, 1) * bright)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    # keep each pixel's relative darkness so the stroke keeps its shape
    shade = np.clip(0.55 + 0.75 * lum, 0, 1)[:, :, None]
    out = (a * (1 - alpha[:, :, None])
           + GOLD[None, None, :] * shade * alpha[:, :, None])
    return Image.fromarray(np.clip(out, 0, 255).astype("uint8"))


def main(pdf_path):
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "assets")
    os.makedirs(out_dir, exist_ok=True)
    doc = pdfium.PdfDocument(pdf_path)
    pages = {}
    for name, page_no, box in CROPS:
        if page_no not in pages:
            pages[page_no] = doc[page_no].render(scale=RENDER_SCALE).to_pil()
        shot = recolor(pages[page_no].crop(box))
        shot.save(os.path.join(out_dir, name))
        print(f"{name}: {shot.size[0]}x{shot.size[1]}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
