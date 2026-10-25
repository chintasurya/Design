"""Preview: one Sierra call end to end. A patient asks about a booked appointment and reschedules it; the sequence
shows each backend call in order, and the boundary between the knowledge path (no PHI) and the verified caller's
data (this patient only). Colourful black IG style, like mc_backend_flow.py.

    python3 sierra_call_flow.py [out.pptx]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from build_data_harness_deck import R, SRC, logo, new_slide
from build_mad_ig_deck import BLACK, CYAN, MAGENTA, YELLOW, set_notes
from footer import fix_footers
from sierra_voice import T1, T2, T3
from story_slides import dark_header

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "sierra_call_flow.pptx")
TINTS = {CYAN: "06262B", YELLOW: "2B2508", MAGENTA: "2B0716", T1: "1A1A1A"}
BOUNDARY = 1            # lanes from here on carry the verified caller's PHI; the knowledge base has none

LANES = [("googlecloud", "Knowledge base", "approved articles · semantic layer + graph", CYAN),
         ("people", "Patient", "calls the Ascension number", YELLOW),
         (None, "Sierra voice agent", "answers, verifies, acts · BAA", CYAN),
         (None, "Identity verification", "date of birth + one-time code", YELLOW),
         (None, "Scoped scheduling API", "this patient only · rules enforced", MAGENTA),
         (None, "Epic scheduling", "system of record", T1),
         ("googlebigquery", "Patient-context API", "Gold B · read-only · this caller", MAGENTA)]

# (kind, from lane, to lane, label, colour); kinds: msg, ret (dashed return), gate, self
ROWS = [("msg", 1, 2, "1  “When is my cardiology appointment? Can I move it?”", YELLOW),
        ("self", 2, 2, "2  Patient-specific request: verify first", CYAN),
        ("msg", 2, 3, "3  Verify: date of birth + number on file", CYAN),
        ("msg", 3, 1, "4  One-time code by SMS; the caller reads it back", YELLOW),
        ("ret", 3, 2, "5  Verified: a session token for this patient only", T2),
        ("msg", 2, 4, "6  Upcoming appointments for this token", CYAN),
        ("msg", 4, 5, "7  Read: this patient only", MAGENTA),
        ("ret", 5, 4, "8  Appointment record", T2),
        ("ret", 4, 2, "9  Date, time, provider, location: minimum fields", T2),
        ("msg", 2, 6, "10  Any campaign or consent context for this caller?", CYAN),
        ("ret", 6, 2, "11  Heart-failure follow-up text sent Monday; SMS consent on file", T2),
        ("msg", 2, 0, "12  Prep for a cardiology follow-up?", CYAN),
        ("ret", 0, 2, "13  Approved article, cited; no PHI", T2),
        ("ret", 2, 1, "14  “Tuesday 10:30 with cardiology. Bring your medication list.”", T2),
        ("msg", 1, 2, "15  “Move it to Friday morning.”", YELLOW),
        ("msg", 2, 4, "16  Friday slots; reschedule rules checked in the API", CYAN),
        ("msg", 4, 5, "17  Reschedule written to Epic", MAGENTA),
        ("ret", 4, 1, "18  Confirmed Friday 9:00; Sierra tells the caller; confirmation text sent", T2),
        ("gate", 1, 1, "Hand-off to a person: not verified, upset or clinical", YELLOW),
        ("msg", 2, 6, "19  After the call: outcome into Gold B, aggregates into Gold A; transcript masked", CYAN)]

NOTES = """PREVIEW: a patient calls about a booked appointment   (about 2 minutes)

KEY MESSAGE
Sierra answers general questions from approved articles with no PHI, and acts only for the verified caller, through scoped APIs, with bookings written to Epic.

WALK IT (top to bottom)
1-2 The patient asks about their cardiology appointment and wants to move it. That is patient-specific, so Sierra verifies first.
3-5 The verification service checks the date of birth and the number on file and sends a one-time code by SMS; once the caller reads it back, Sierra gets a session token for this patient only.
6-9 With the token, the scoped scheduling API reads this patient's appointments from Epic and returns only the minimum fields: date, time, provider and location.
10-11 The patient-context API reads Gold B, read-only, for this caller: for example, the heart-failure follow-up text sent on Monday and the SMS consent on file. It never returns a list.
12-14 For preparation advice Sierra uses an approved knowledge-base article, cited, with no PHI, then answers the caller.
15-18 The caller asks to move it; the scheduling API offers Friday slots, checks the reschedule rules and writes the change to Epic. Sierra confirms and a confirmation text is sent.
Hand-off: if the caller is not verified, upset, or asks a clinical question, a person takes over.
19 After the call the outcome goes into Gold B for this patient and into Gold A as aggregates; the transcript is masked before any analytics."""


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION · SIERRA VOICE AGENT · CALL FLOW (PREVIEW)",
                "A patient calls about their appointment: what happens behind the scenes",
                "Sierra answers from approved articles, and acts only for the verified caller through scoped APIs; "
                "bookings stay in Epic.")
    x0, wtot = 0.45, 12.43
    lw = wtot / len(LANES)
    cx = [x0 + lw * (i + 0.5) for i in range(len(LANES))]
    hy, hh = 1.28, 0.62
    top, bot = hy + hh, 6.42
    tb = x0 + lw * BOUNDARY
    cv.arrow(tb, hy - 0.04, tb, bot + 0.06, MAGENTA, 1.25, dash="dash", head=False)
    for i, (ic, t, d, c) in enumerate(LANES):
        x = x0 + lw * i + 0.05
        w = lw - 0.1
        if i == 4:
            cv.frame(x, hy, w, hh, BLACK, 0.03)
        else:
            cv.rect(x, hy, w, hh, TINTS[c], c, 1.0, R, 0.08)
        tx = x + 0.08
        if ic:
            logo(cv, ic, tx, hy + 0.08, 0.2)
            tx += 0.26
        cv.text(tx, hy + 0.05, x + w - tx - 0.04, 0.24, t, size=8, bold=True, color=c, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(x + 0.08, hy + 0.3, w - 0.14, 0.3, d, size=7, color=T2, line=0.9)
        cv.arrow(cx[i], top, cx[i], bot, "3A3A3A", 1.0, dash="sysDot", head=False)
    y = top + 0.25
    step = (bot - 0.08 - y) / (len(ROWS) - 1)
    for kind, a, b, label, col in ROWS:
        if kind in ("msg", "ret"):
            x1, x2 = cx[a], cx[b]
            cv.arrow(x1, y, x2, y, col, 1.5 if kind == "msg" else 1.0, dash="dash" if kind == "ret" else None)
            lo, hi = min(x1, x2), max(x1, x2)
            tw = max(hi - lo - 0.1, 0.055 * len(label) + 0.12)
            lx = min(max((lo + hi) / 2 - tw / 2, x0), x0 + wtot - tw)
            cv.rect(lx, y - 0.16, tw, 0.135, BLACK, None)
            cv.text(lx, y - 0.16, tw, 0.135, label, size=7, color=T1 if kind == "msg" else T2,
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        elif kind == "gate":
            w = 3.4
            cv.rect(cx[a] - 0.75, y - 0.09, w, 0.18, YELLOW, None, shape=R, radius=0.5)
            cv.text(cx[a] - 0.75, y - 0.09, w, 0.18, label, size=7, bold=True, color="000000",
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        else:
            w = 0.055 * len(label) + 0.2
            lx = min(max(cx[a] - w / 2, tb + 0.06), x0 + wtot - w)
            cv.rect(lx, y - 0.09, w, 0.18, TINTS[col], col, 0.9, R, 0.5)
            cv.text(lx, y - 0.09, w, 0.18, label, size=7, color=T1, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        y += step
    px_ = max(tb - 2.7, x0)
    cv.rect(px_, bot + 0.1, 5.4, 0.2, MAGENTA, None, shape=R, radius=0.5)
    cv.text(px_, bot + 0.1, 5.4, 0.2, "←  NO PHI: APPROVED ARTICLES ONLY   ·   PHI: THE VERIFIED CALLER ONLY  →",
            size=7, bold=True, color="FFFFFE", track=60, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    cv.text(0.45, bot + 0.36, 12.43, 0.2, [[("Never: ", {"bold": True, "color": T1}),
                                            ("lists of patients, anyone else's data, or a Google Cloud copy of a "
                                             "booking. Transcripts hold PHI: access-controlled, retention-limited, "
                                             "masked before analytics.", {"color": T3})]], size=7,
            anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, NOTES)
    return s


def main(out=OUT):
    import muted_theme as mt
    prs = Presentation(SRC)
    lst = prs.slides._sldIdLst
    for el in list(lst):
        prs.part.drop_rel(el.rId)
        lst.remove(el)
    layout = next(l_ for l_ in prs.slide_layouts if l_.name == "DEFAULT")
    s = build(prs, layout)
    mt.min_font(s, 7.0)
    fix_footers(prs)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    prs.save(out)
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
