# Deck

`../Ascension Network Services Knowledge Graph.pptx` holds the architecture
story. Slides 1 to 8 are the original: what we set out to build. Slides 9 to 21
were generated from this directory and describe what was actually built and
measured in the sandbox.

## Regenerating the POC slides

`add_poc_slides.py` **appends** slides to the deck. Running it twice adds them
twice, so restore the eight-slide original from git first:

```bash
git checkout -- "../Ascension Network Services Knowledge Graph.pptx"   # only if slides 9+ exist
python3 add_poc_slides.py
python3 check_geometry.py "../Ascension Network Services Knowledge Graph.pptx" 9
```

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
the environment they were generated in, so rendering to images was impossible
and the usual visual pass did not happen. The geometry check is an arithmetic
substitute for it: it catches overflow, overlap and off-slide shapes, but it
cannot judge whether a slide *looks* right. Open the deck before presenting it.
