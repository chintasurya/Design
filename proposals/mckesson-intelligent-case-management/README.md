# McKesson Extended Care: Intelligent Case Management

A 23 slide solution and business value proposal for Salesforce native email case
management, built to match the visual language of the existing
`McKesson email contact center_v1.pptx` proposal deck and reusing its Insight
Global brand assets.

Scope is deliberately solution only. There are no commercial, pricing, staffing
or shift coverage slides.

## Contents

| File | What it is |
| --- | --- |
| `McKesson_Intelligent_Case_Management.pptx` | The deck |
| `deck.js` | Slide by slide generator |
| `lib.js` | Theme tokens and layout helpers |
| `assets/` | Insight Global logos extracted from the source deck |

## Rebuilding

```
npm install pptxgenjs
node deck.js
```

## Design tokens

Taken from the reporting slides of the source deck so the two decks sit together.

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
| Green | `22C55E` | Positive state |
| Amber | `F59E0B` | Warning state |

Typeface is Arial throughout.

## Figures

Volume, case mix and handling time are taken from the operations sample in the
source deck. The step level handling time decomposition on slide 20 is an
Insight Global model, labelled as such on the slide, and is stated for
validation during the baseline period rather than as a commitment.
