# Deck

`../Ascension Network Services Knowledge Graph.pptx` holds the architecture
story. Slides 1 to 8 are the original: what we set out to build. Slides 9 to 21
were generated from this directory and describe what was actually built and
measured in the sandbox.

## Regenerating the POC slides

Safe to run repeatedly. Every generated slide carries a marker comment, and a
run removes its own previous slides before writing new ones, so the count does
not grow and the original eight are never touched.

```bash
python3 add_poc_slides.py
python3 check_geometry.py "../Ascension Network Services Knowledge Graph.pptx" 9
python3 <skill>/scripts/office/validate.py \
    "../Ascension Network Services Knowledge Graph.pptx" --original <pristine 8-slide copy>
```

Pass `--original`. The deck ships a `revisionInfo.xml` the XSD rejects on its
own terms; without a baseline that pre-existing error reads as a regression.

The generated slides reference `slideLayout1` and nothing else, which is what
slides 5, 6 and 8 of the original do. No media, notes or theme parts are
touched, so a regeneration cannot disturb the original eight.

## Design language, read out of the deck rather than guessed

| | |
|---|---|
| Ground | `F4F7FC`, matching the original content slides |
| Text | `12233B` navy, `0E1B2E` for titles, `5C6E85` muted, `9AA7B5` faint |
| Accents | `1B6BC0` blue · `00757F` teal · `0E8A7D` jade · `2E7D32` green · `C77400` amber · `7A4FC0` plum · `C2185B` rose |
| Type | Trenda IG Display Bold (titles), Trenda IG Text / Semibold (body), Courier New (API names) |
| Title block | 20pt at x=0.4" y=0.28", standfirst 9.5pt at y=0.7" — the original's exact offsets |

Body copy sits at 8 to 9.5pt rather than the original's 5 to 7pt. These slides
carry explanation rather than reference diagrams, and are meant to be read by
people who will not zoom in.

## Verification, and its one gap

```bash
python3 <skill>/scripts/office/validate.py "../Ascension ....pptx" --original <original>
python3 check_geometry.py "../Ascension ....pptx" 9
```

Package validation passes. `check_geometry.py` confirms no shape leaves the
slide, no text box overlaps another, margins hold, and every text box is large
enough for the text in it.

**These slides have not been looked at.** LibreOffice cannot load any file in
the environment they were generated in — including a freshly generated empty
one — so rendering to images was impossible and the usual visual pass did not
happen. The geometry check is an arithmetic substitute: it catches overflow,
overlap, off-slide shapes and collapsed line spacing, but it cannot judge
whether a slide *looks* right. Open the deck before presenting it.

### What the first version got wrong, and why the check missed it

Every wrapped paragraph rendered with its lines on top of each other. In
OOXML, `<a:spcPct val="..."/>` is thousandths of a percent, so 100% is
`100000`. The generator emitted `1250` for a 1.25 line multiple, setting line
height to 1.25% and stacking every line at the same position.

`check_geometry.py` read that value correctly and then threw it away, taking
`max(line, 1.0)` on the reasonable-sounding grounds that spacing below single
made no sense. It made the defect invisible to the one check that should have
caught it. The clamp is gone, and a line-spacing value under 50% is now
reported as an error in its own right rather than normalised into silence.
