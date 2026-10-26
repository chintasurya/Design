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

LANES = [("googlecloud", "Shared knowledge", "approved articles · semantic layer + graph", CYAN),
         ("people", "Patient", "calls the Ascension number", YELLOW),
         (None, "Sierra voice agent", "answers, verifies, acts · BAA", CYAN),
         (None, "Identity + verification", "caller ID + date of birth · patient token", YELLOW),
         (None, "Verified Patient Action Engine", "narrow functions · this patient only", MAGENTA),
         (None, "Epic scheduling", "system of record", T1),
         ("googlebigquery", "Gold B", "patient context · read-only", MAGENTA)]

# (kind, from lane, to lane, label, colour); kinds: msg, ret (dashed return), gate, self
ROWS = [("gate", 1, 1, "Emergency words? Straight to 911 or the nurse line: no check, no wait", MAGENTA),
        ("msg", 1, 2, "1  “When is my next cardiology appointment?”", YELLOW),
        ("msg", 2, 3, "2  Caller ID matches the number on file + date of birth; carrier + SIM-swap checks", CYAN),
        ("ret", 3, 2, "3  Verified in seconds: a short-lived Verified Patient Token (no SMS wait)", T2),
        ("msg", 2, 4, "4  GetNextAppointment(token)", CYAN),
        ("msg", 4, 5, "5  Read: this patient only", MAGENTA),
        ("ret", 5, 4, "6  Appointment record", T2),
        ("ret", 4, 2, "7  Minimum fields: Monday 10:30, cardiology, location", T2),
        ("ret", 2, 1, "8  “Your cardiology appointment is Monday at 10:30 AM.”", T2),
        ("msg", 1, 2, "9  “Can you move it to Friday?”", YELLOW),
        ("msg", 2, 4, "10  SearchAvailableSlots(token, Friday): rules applied", CYAN),
        ("msg", 4, 5, "11  Live availability", MAGENTA),
        ("ret", 2, 1, "12  “Friday has 10:00 AM and 2:30 PM available.”", T2),
        ("msg", 1, 2, "13  “2:30.”", YELLOW),
        ("msg", 2, 4, "14  RescheduleAppointment(token, Friday 2:30)", CYAN),
        ("msg", 4, 5, "15  Written to Epic", MAGENTA),
        ("ret", 4, 1, "16  Confirmed: Sierra tells the caller; confirmation text sent", T2),
        ("msg", 2, 0, "17  Prep for a cardiology follow-up? Approved article, no PHI", CYAN),
        ("gate", 1, 1, "Step-up or hand-off: no caller-ID match, a higher-risk change or a clinical question", YELLOW),
        ("msg", 4, 6, "18  After the call: outcome into Gold B, aggregates into Gold A; transcript masked", CYAN)]

NOTES = """SLIDE: a patient calls about a booked appointment   (about 2 minutes)

KEY MESSAGE
Knowledge is shared across agents; patient-level transactions are not. Sierra answers general questions from shared, governed knowledge, and acts for a patient only through the Verified Patient Action Engine, after a check that takes seconds. Emergencies never wait for a check.

WALK IT (top to bottom)
Emergency: words such as chest pain or can't breathe send the caller straight to 911 or the nurse line. No PHI is needed, so nothing is verified.
1-3 The patient asks about their next cardiology appointment. The Patient Identity & Verification Service checks that the caller ID matches the number on file, with carrier and SIM-swap checks, and the spoken date of birth, and issues a short-lived Verified Patient Token in seconds. No SMS wait.
4-8 With the token, the Verified Patient Action Engine calls GetNextAppointment against Epic and returns the minimum fields; Sierra answers.
9-12 The patient asks to move it; SearchAvailableSlots returns Friday's live availability with the rules applied; Sierra offers 10:00 and 2:30.
13-16 The patient picks 2:30; RescheduleAppointment writes it to Epic; Sierra confirms and a confirmation text is sent.
17 Preparation advice comes from an approved article in the shared knowledge, with no PHI.
Step-up or hand-off: an app push, SMS code or a person only when the caller ID does not match, the change is higher risk (for example new contact details), or the question is clinical.
18 After the call the outcome goes into Gold B for this patient and into Gold A as aggregates; the transcript is masked before any analytics."""


def build(prs, layout):
    s, cv = new_slide(prs, layout)
    dark_header(cv, "ASCENSION · SIERRA VOICE AGENT · CALL FLOW",
                "A patient calls about their appointment: what happens behind the scenes",
                "Knowledge is shared; patient transactions are not. Sierra acts for a patient only through the Verified "
                "Patient Action Engine, after a check that takes seconds.")
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
            w = 0.055 * len(label) + 0.3
            cv.rect(cx[a] - 0.75, y - 0.13, w, 0.16, col, None, shape=R, radius=0.5)   # clear of the next label
            cv.text(cx[a] - 0.75, y - 0.13, w, 0.16, label, size=7, bold=True,
                    color="FFFFFE" if col == MAGENTA else "000000",
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        else:
            w = 0.055 * len(label) + 0.2
            lx = min(max(cx[a] - w / 2, tb + 0.06), x0 + wtot - w)
            cv.rect(lx, y - 0.09, w, 0.18, TINTS[col], col, 0.9, R, 0.5)
            cv.text(lx, y - 0.09, w, 0.18, label, size=7, color=T1, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        y += step
    px_ = max(tb - 2.7, x0)
    cv.rect(px_, bot + 0.1, 6.2, 0.2, MAGENTA, None, shape=R, radius=0.5)
    cv.text(px_, bot + 0.1, 6.2, 0.2, "←  SHARED KNOWLEDGE: NO PHI   ·   PATIENT TRANSACTIONS: THE VERIFIED CALLER ONLY  →",
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
