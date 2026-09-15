# McKesson Extended Care: Salesforce case management proposals

Two solution decks, both solution and business value only. Neither contains
pricing, commercials, staffing or shift coverage.

Both are built on the visual language of the existing
`McKesson email contact center_v1.pptx` and reuse its Insight Global brand
assets.

## The decks

### `McKesson_Four_Doors.pptx` (16 slides) — current

Structured around its own argument rather than a feature list: every case takes
one of four routes into the operation, and the work is moving volume to the
cheaper routes rather than making the expensive route slightly faster.

| Door | Meaning | Cost |
| --- | --- | --- |
| 01 | Never arrives, the demand behind it was removed | Zero |
| 02 | Resolves itself, deterministic and autonomous | Quality sample only |
| 03 | One touch, arrives pre-resolved for approval | About 30 percent less time |
| 04 | Expert, judgement needed but the file is already built | Judgement time protected |

Carries the quantified core: handling effort by queue, modelled phase by phase,
and the case volume migrating between doors.

### `McKesson_Intelligent_Case_Management.pptx` (24 slides) — the one being presented

A six stage pipeline from capture to continuous learning, with a slide per
mechanism. Exhaustive on the Salesforce configuration detail, which is why the
team chose it.

Slide 3, `The solution on one page`, is the executive summary: the whole design
in one picture, with what it is worth, what it runs on and how it lands in three
phases. If an executive sees one slide, it is that one.

Every slide carries its talk track in the speaker notes, so the deck can be
presented from PowerPoint Presenter View with nothing else open.

## Contents

| File | What it is |
| --- | --- |
| `McKesson_Intelligent_Case_Management.pptx` | The six stage deck, with talk track in the speaker notes |
| `McKesson_ICM_Talk_Track.docx` | The same talk track as a printable presenter handout |
| `McKesson_Four_Doors.pptx` | The four doors deck |
| `deck.js` | Generator for the six stage deck |
| `deck2.js` | Generator for the four doors deck |
| `talktrack.js` | The talk track itself: one entry per slide |
| `talktrack-doc.js` / `make_docx.py` | Render the talk track as the handout |
| `lib.js` | Shared theme tokens, layout helpers and chart defaults |
| `assets/` | Insight Global logos extracted from the source deck |
| `fonts/` | The four Trenda IG faces the decks use |

## Rebuilding

```
npm install pptxgenjs
pip install python-docx

node deck.js               # six stage deck, talk track baked into notes
node deck2.js              # four doors deck
node talktrack-doc.js && python3 make_docx.py    # presenter handout
```

## The talk track

`talktrack.js` is the single source of truth. `deck.js` writes each entry into
that slide's speaker notes, and `make_docx.py` renders the same entries as the
handout, so the two can never drift apart. Edit the talk track there and rebuild
both, never in the .pptx or the .docx directly.

Each entry carries:

| Field | What it is |
| --- | --- |
| `title` | The slide's name, for the handout |
| `secs` | Rough spoken length, for pacing a run through |
| `purpose` | One line on why the slide exists |
| `say` | What to actually say in the room |
| `ask` | The question the slide usually attracts, and the answer |

The full run is about 15 minutes of speaking before questions. Slide numbers in
`talktrack.js` are positional: if a slide is added or removed from `deck.js`,
the talk track array has to move with it.

## Typography

| Role | Face |
| --- | --- |
| Titles, kickers, display numerals, section labels | Trenda IG Display |
| Body, bullets, tables | Trenda IG Text |

Trenda IG is not a system font. Anyone opening or presenting these decks needs
the faces installed locally, or PowerPoint will substitute and line breaks will
move. The four faces the decks actually reference are in `fonts/`; install them
before editing or presenting.

## Design tokens

Taken from the reporting slides of the source deck so all decks sit together.

| Token | Hex | Use |
| --- | --- | --- |
| Ground | `0A0D14` | Slide background |
| Panel | `151A24` | Cards |
| Panel 2 | `1A2130` | Nested cards, table header |
| Line | `252D3D` | Hairline borders |
| Text | `E6EAF2` | Body |
| Muted | `8A94A6` | Secondary text |
| Cyan | `22D3EE` | Primary accent |
| Pink | `FF0069` | Insight Global brand accent |

## Chart colour

Chart series use a separately validated categorical palette
(`3987E5, D95926, 199E70, C98500, D55181`), not the brand accents. It passes all
six checks of the dataviz validator against this deck's `0A0D14` surface:
lightness band, chroma floor, colour vision deficiency separation,
normal-vision floor and contrast. Brand cyan and pink stay on chrome so series
colour always carries data identity rather than emphasis.

Queue identity and door identity are each assigned once and held constant across
every chart that shows them.

## Figures

Volume, case mix and handling time come from the operations sample in the source
deck: 33,480 cases per month and 4,419 agent handling hours.

The door mix rates, the phase by phase effort model and the credit case time
split are Insight Global models, labelled as such on the slides. They are stated
for validation against McKesson case data during discovery, not as commitments.
