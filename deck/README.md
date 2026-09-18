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
| `tools/shot.mjs` | Renders each slide to an exact 1600x900 PNG over the DevTools Protocol. |
| `render.sh` | One command: three PNGs + a 3-page PDF into `export/`. |
| `export/` | Generated artwork. Safe to delete and regenerate. |

## Viewing

Open `index.html` directly. Useful URL flags:

- `?solo=2` — one slide alone at 1:1 (used by the PNG export)
- `?print=1` — all three at 1:1 with page breaks (used by the PDF export)

## Exporting

```bash
./render.sh            # -> export/shieldforge-slide-0{1,2,3}.png + shieldforge-deck.pdf
./render.sh /some/dir  # somewhere else
```

Set `CHROME=/path/to/chrome` if Chromium lives elsewhere.

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
