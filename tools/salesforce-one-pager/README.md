# Salesforce certification-linking one-pager

Builds `docs/IG_Consulting_-_Salesforce_Certification_Linking_Instructions_-_One_Pager.pptx`
in the same format as the AWS certification-linking one-pager.

The AWS deck (`assets/IG_Consulting_-_AWS_Certification_Linking_Instructions_-_One_Pager.pptx`)
is used as the template rather than rebuilt from scratch, so the slide master,
theme, Trenda type styles, "INSIGHT GLOBAL CONSULTING" eyebrow and the logo
footer carry over untouched. Only the title, the body copy and the screenshots
are replaced.

## Files

| File | Purpose |
| --- | --- |
| `content.py` | All copy. Each paragraph is a list of `(text, bold)` segments; a third element makes the segment a hyperlink. |
| `measure.py` | Wraps the copy using the real Trenda faces to predict rendered height, so the text blocks can be positioned around the screenshots. |
| `build.py` | Assembles the deck. |
| `screenshots.py` | Cuts the screenshots out of the source Salesforce guide PDF and recolours its cyan callout boxes to Insight Global gold (`FFC000`). |

## Rebuilding

```sh
pip install python-pptx pypdfium2 pillow numpy
python3 build.py
```

Editing copy in `content.py` is enough for most changes: the layout re-measures
itself and `build.py` fails loudly if the content would run into the footer
logo. Keep an eye on the reported `content bottom` — the logo starts at 10.19in.

To re-cut the screenshots after the source guide changes:

```sh
python3 screenshots.py path/to/Salesforce_Partner_Portal_Certification_Linking_Guide.pdf
```

Crop boxes are in `CROPS` in that script, in pixels at 4x render scale.

## Fonts

Trenda IG Display and Trenda IG Text are in `fonts/Trenda IG/` at the repo root
and must be installed for the deck to render correctly; without them
PowerPoint substitutes and the layout shifts.
