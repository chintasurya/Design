# ShieldForge by Insight Global — 3-slide deck

An HTML rebuild of the three ShieldForge slides, set in the brand's own
Trenda IG typefaces. Every element is live HTML/CSS/SVG — no flattened
screenshots — so copy, numbers and layout stay editable.

## Files

| Path | What it is |
| --- | --- |
| `index.html` | The deck. Open it in a browser; it scales to the window. |
| `css/deck.css` | All styling: tokens, slide chrome, product-mockup components. |
| `fonts/` | Trenda IG Display + Trenda IG Text (brand faces) and the script face used for the "Govern with Confidence" lockup. |
| `tools/shot.mjs` | Renders each slide to an exact 1600x900 PNG over the DevTools Protocol (pass a scale of `2` for 3200x1800). |
| `tools/build_pptx.py` | Packages the rendered slides into a 16:9 `.pptx`, flattened or editable. |
| `tools/measure.sh` | Dumps the geometry and styling of the editable copy as JSON. |
| `tools/preview_pptx.py` | Rebuilds an HTML preview from a `.pptx`, for checking the result. |
| `render.sh` | One command: PNGs, both `.pptx` files and a 3-page PDF into `export/`. |
| `export/` | Generated artwork. Safe to delete and regenerate. |

## Viewing

Open `index.html` directly. Useful URL flags:

- `?solo=2` — one slide alone at 1:1 (used by the PNG export)
- `?print=1` — all three at 1:1 with page breaks (used by the PDF export)
- `?bg=1` — the artwork with the editable copy hidden (used by the PPTX export)
- `?measure=1` — dumps that copy's geometry and styling as JSON

## Exporting

```bash
./render.sh            # -> export/  (3 PNGs, 2 PPTX files, 1 PDF)
./render.sh /some/dir  # somewhere else
```

Set `CHROME=/path/to/chrome` if Chromium lives elsewhere.

### The two PowerPoint files

`tools/build_pptx.py` writes the OOXML package directly, so neither file needs
PowerPoint or LibreOffice to build. Both are 13.333in x 7.5in (16:9), carry
alt text on every picture, and use a theme holding the brand palette and the
Trenda font names.

**`shieldforge-deck.pptx`** — each slide is one full-bleed 3200x1800 picture.
Identical on any machine, no fonts to install, nothing to edit.

**`shieldforge-deck-editable.pptx`** — same artwork with the copy hidden,
and 38 native text boxes placed back on top: headlines, subheads, feature
titles and descriptions, the checkmark labels, the footer, page numbers and
the demo-view note. Headlines keep their two-tone colouring, one run per
colour. The product mockups stay part of the artwork.

Opening the editable file needs **Trenda IG Display** and **Trenda IG Text**
installed (the `fonts/` folder here holds them). Without them PowerPoint
substitutes and the line breaks move. Each weight installs as its own family
— "Trenda IG Display Black", "Trenda IG Text Semibold" and so on — which is
how the deck reaches weights PowerPoint cannot express as plain bold.

Either way `index.html` stays the source of truth: edit there and re-run
`./render.sh` rather than hand-patching a `.pptx`.

### Checking a build

`tools/preview_pptx.py` reads the shapes back out of a generated `.pptx` and
rebuilds them as HTML, so the EMU maths, font mapping and colour conversion
are checked against what actually shipped rather than against the numbers that
produced it. Render that preview and difference it against
`export/shieldforge-slide-0N.png` to see any drift. Note that the preview is
an emulation of PowerPoint's text engine, not PowerPoint, and is good to about
a pixel.

## Design notes

- **Canvas** is 1600x900 (16:9). Slide elements are absolutely positioned in
  that coordinate space, so nudging something is a matter of changing one
  `top`/`left` value.
- **Type** is Trenda IG Display for headlines, UI headings and numerals;
  Trenda IG Text for body copy. Weights are wired up in `css/deck.css`
  under `@font-face`.
- **Logos** are set as live text in Trenda plus the brand dots (cyan "o",
  yellow "g" with the magenta descender dot), matching the supplied
  ShieldForge and Insight Global artwork. Because they are text, they stay
  sharp at any size. To swap in the official vector files instead, replace
  the contents of the `#tpl-logo` template in `index.html` with an `<img>`.
- **Brand colors** live as CSS custom properties on `:root`: `--cyan`,
  `--yellow`, `--pink`, `--navy`.
- **Product mockups** (Health Check, Segregation of Duties, User 360,
  Profile Migration, Release Radar, Compliance) are built from shared
  components — `.mock`, `.chrome`, `.score`, `.kpi`, `.stat`, `table.t` —
  so numbers and labels can be edited inline.
