#!/usr/bin/env python3
"""
Append the POC slides to "Ascension Network Services Knowledge Graph.pptx".

The existing eight slides describe what we set out to build. These describe
what was actually built and measured in the sandbox, in the same visual
language: F4F7FC ground, 12233B navy, Trenda IG type, dense colour-coded
cards, a 20pt Display Bold title and a 9.5pt standfirst at the same offsets.

New slides reference slideLayout1 and nothing else, which is exactly what
slides 5, 6 and 8 of the original do, so no media or notes parts are copied
and the merge cannot disturb anything already in the deck.

    python3 add_poc_slides.py
"""

import copy
import os
import re
import shutil
import zipfile

EMU = 914400
SRC = "../Ascension Network Services Knowledge Graph.pptx"
OUT = "../Ascension Network Services Knowledge Graph.pptx"

# ------------------------------------------------------------------ palette --
NAVY = "12233B"
INK = "0E1B2E"
MUTE = "5C6E85"
FAINT = "9AA7B5"
RULE = "DCE4EE"
RULE2 = "C7D2DE"
PAPER = "FFFFFF"
GROUND = "F4F7FC"
BLUE = "1B6BC0"
TEAL = "00757F"
JADE = "0E8A7D"
GREEN = "2E7D32"
AMBER = "C77400"
PLUM = "7A4FC0"
ROSE = "C2185B"
RED = "C62828"

DISPLAY_B = "Trenda IG Display Bold"
DISPLAY = "Trenda IG Display"
TEXT = "Trenda IG Text"
TEXT_SB = "Trenda IG Text Semibold"
MONO = "Courier New"

_uid = [100]


def nid():
    _uid[0] += 1
    return _uid[0]


def emu(v):
    return int(round(v * EMU))


def _font(face):
    return (
        '<a:latin typeface="%s" pitchFamily="34" charset="0"/>'
        '<a:ea typeface="%s" pitchFamily="34" charset="-122"/>'
        '<a:cs typeface="%s" pitchFamily="34" charset="-120"/>' % (face, face, face)
    )


def _esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def run(text, size=9, color=NAVY, face=TEXT, bold=False, italic=False):
    rpr = '<a:rPr lang="en-US" sz="%d"%s%s dirty="0">' % (
        int(size * 100),
        ' b="1"' if bold else "",
        ' i="1"' if italic else "",
    )
    rpr += '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>%s</a:rPr>' % (
        color, _font(face))
    sp = ' xml:space="preserve"' if text != text.strip() else ""
    return "<a:r>%s<a:t%s>%s</a:t></a:r>" % (rpr, sp, _esc(text))


def para(runs, align="l", space_after=0, line=None, bullet=False, indent=0.0):
    ppr = '<a:pPr marL="%d" indent="%d" algn="%s">' % (
        emu(indent) if bullet else 0, emu(-0.11) if bullet else 0, align)
    if space_after:
        ppr += '<a:spcAft><a:spcPts val="%d"/></a:spcAft>' % int(space_after * 100)
    if line:
        ppr += '<a:lnSpc><a:spcPct val="%d"/></a:lnSpc>' % int(line * 1000)
    if bullet:
        ppr += '<a:buFont typeface="Arial"/><a:buChar char="•"/>'
    else:
        ppr += "<a:buNone/>"
    ppr += "</a:pPr>"
    return "<a:p>%s%s</a:p>" % (ppr, "".join(runs))


def textbox(x, y, w, h, paras, anchor="t", wrap=True):
    return (
        '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="Text %d"/>'
        '<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        '<p:spPr><a:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln/></p:spPr>'
        '<p:txBody><a:bodyPr wrap="%s" lIns="0" tIns="0" rIns="0" bIns="0" '
        'rtlCol="0" anchor="%s"/><a:lstStyle/>%s</p:txBody></p:sp>'
        % (nid(), nid(), emu(x), emu(y), emu(w), emu(h),
           "square" if wrap else "none", anchor, "".join(paras))
    )


def shape(prst, x, y, w, h, fill=None, line=None, line_w=1.0, radius=None):
    adj = ""
    if radius is not None and prst == "roundRect":
        adj = '<a:avLst><a:gd name="adj" fmla="val %d"/></a:avLst>' % int(radius)
    else:
        adj = "<a:avLst/>"
    f = ('<a:solidFill><a:srgbClr val="%s"/></a:solidFill>' % fill) if fill else "<a:noFill/>"
    ln = ('<a:ln w="%d"><a:solidFill><a:srgbClr val="%s"/></a:solidFill></a:ln>'
          % (int(line_w * 12700), line)) if line else '<a:ln><a:noFill/></a:ln>'
    return (
        '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="Shape %d"/><p:cNvSpPr/><p:nvPr/>'
        '</p:nvSpPr><p:spPr><a:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/>'
        '</a:xfrm><a:prstGeom prst="%s">%s</a:prstGeom>%s%s</p:spPr>'
        '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p>'
        "</p:txBody></p:sp>"
        % (nid(), nid(), emu(x), emu(y), emu(w), emu(h), prst, adj, f, ln)
    )


def card(x, y, w, h, fill=PAPER, line=RULE, radius=None):
    return shape("roundRect" if radius else "rect", x, y, w, h,
                 fill=fill, line=line, line_w=0.75, radius=radius or 0)


def chip(x, y, w, h, label, fill, text_color=PAPER, size=8):
    return shape("roundRect", x, y, w, h, fill=fill, radius=18000) + textbox(
        x, y, w, h, [para([run(label, size, text_color, TEXT_SB, bold=True)],
                          align="ctr")], anchor="ctr")


def arrow(x, y, w, h=0.11, fill=RULE2):
    return shape("rightArrow", x, y, w, h, fill=fill)


def down_arrow(x, y, w=0.11, h=0.2, fill=RULE2):
    return shape("downArrow", x, y, w, h, fill=fill)


def title(text, standfirst):
    """Exactly the offsets and sizes the existing content slides use."""
    return (
        textbox(0.4, 0.28, 12.53, 0.38,
                [para([run(text, 20, INK, DISPLAY_B)])], anchor="ctr")
        + textbox(0.4, 0.7, 12.53, 0.24,
                  [para([run(standfirst, 9.5, MUTE, DISPLAY)])], anchor="ctr")
    )


def kicker(text, x=0.4, y=1.06, color=TEAL):
    return textbox(x, y, 12.53, 0.18,
                   [para([run(text.upper(), 7, color, TEXT_SB, bold=True)])])


SLIDE_HEAD = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
    '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
    '<p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="%s"/></a:solidFill>'
    '<a:effectLst/></p:bgPr></p:bg>'
    '<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
    "</p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/>"
    '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
    "</a:xfrm></p:grpSpPr>"
)
SLIDE_TAIL = (
    "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"
)


def slide(body, ground=GROUND):
    return SLIDE_HEAD % ground + body + SLIDE_TAIL


# ============================================================ SLIDE CONTENT ==
slides = []

# ---------------------------------------------------------------- divider ---
b = ""
b += textbox(0.4, 2.35, 12.53, 0.3,
             [para([run("FROM ARCHITECTURE TO WORKING SOFTWARE", 9, JADE,
                        TEXT_SB, bold=True)])])
b += textbox(0.4, 2.75, 11.0, 0.72,
             [para([run("What we built, and what it measured", 34, INK,
                        DISPLAY_B)])])
b += textbox(0.4, 3.62, 10.4, 0.9, [para([run(
    "The slides before this one describe the target architecture. The slides after it describe a "
    "running system in a Salesforce sandbox: the Network Services pod, mapped, searchable, and "
    "answering change requests in about seven seconds with no AI model in the read path.",
    11, MUTE, TEXT)], line=1.35)])
facts = [("2,859", "components mapped", BLUE), ("3,969", "relationships", TEAL),
         ("1.8 MB", "the whole map, one file", JADE),
         ("~7 sec", "to answer a request", AMBER)]
for i, (v, l, c) in enumerate(facts):
    x = 0.4 + i * 3.16
    b += card(x, 4.85, 2.92, 1.0, fill=PAPER, line=RULE)
    b += textbox(x + 0.22, 5.0, 2.5, 0.42,
                 [para([run(v, 18, c, DISPLAY_B)])])
    b += textbox(x + 0.22, 5.46, 2.5, 0.22,
                 [para([run(l, 8, MUTE, TEXT)])])
slides.append(slide(b))

# --------------------------------------------- high level architecture ------
b = title("What the POC does, end to end",
          "Five parts. Everything left of the gate costs nothing and calls nobody; nothing crosses the gate without a person.")
b += kicker("the read path  ·  free, repeatable, explainable")

row_y = 1.42
boxes = [
    ("Salesforce org", "objects, fields, flows,\ntriggers, Apex classes", RULE, NAVY, 2.15),
    ("Graph export", "background job reads\nthe pod's metadata", BLUE, PAPER, 2.15),
    ("Knowledge graph", "one JSON file\nstored in the org", TEAL, PAPER, 2.15),
    ("Search", "anchor on the object,\nwalk the relationships", JADE, PAPER, 2.15),
    ("Verdict", "with the evidence\nthat produced it", GREEN, PAPER, 2.15),
]
x = 0.4
for label, detail, fill, tc, w in boxes:
    b += shape("roundRect", x, row_y, w, 1.28, fill=fill, radius=12000)
    b += textbox(x + 0.14, row_y + 0.17, w - 0.28, 0.24,
                 [para([run(label, 10, tc, TEXT_SB, bold=True)], align="ctr")])
    for j, ln in enumerate(detail.split("\n")):
        b += textbox(x + 0.14, row_y + 0.5 + j * 0.2, w - 0.28, 0.2,
                     [para([run(ln, 7.5, FAINT if tc == PAPER else MUTE, TEXT)],
                           align="ctr")])
    if x < 10.0:
        b += arrow(x + w + 0.07, row_y + 0.58, 0.32)
    x += w + 0.46

b += card(0.4, 3.05, 6.05, 1.55, fill=PAPER, line=RULE)
b += textbox(0.62, 3.22, 5.6, 0.22,
             [para([run("The request decides where the search starts", 9.5, INK,
                        TEXT_SB, bold=True)])])
b += textbox(0.62, 3.52, 5.6, 0.95, [para([run(
    "Someone types a sentence on one screen. The system reads an action, an object and a shape out "
    "of it, then matches the sentence against the graph's own object names to pick the starting point. "
    "No form, no dropdowns, no tagging.", 8, MUTE, TEXT)], line=1.3)])

b += card(6.88, 3.05, 6.05, 1.55, fill=PAPER, line=RULE)
b += textbox(7.1, 3.22, 5.6, 0.22,
             [para([run("The graph answers most questions for free", 9.5, INK,
                        TEXT_SB, bold=True)])])
b += textbox(7.1, 3.52, 5.6, 0.95, [para([run(
    "Relationships were resolved once, when the map was built. Answering is a walk over pointers "
    "already in memory: no queries against the org, no external call, no tokens spent, and the same "
    "question gives the same answer tomorrow.", 8, MUTE, TEXT)], line=1.3)])

b += shape("roundRect", 0.4, 4.85, 12.53, 1.62, fill="EAF1F9", radius=10000)
b += chip(0.64, 5.05, 1.5, 0.28, "GATE 1", AMBER)
b += textbox(2.32, 5.05, 10.3, 0.24,
             [para([run("A person reads the verdict and the evidence, then approves or rejects",
                        10, INK, TEXT_SB, bold=True)])])
b += textbox(0.64, 5.5, 12.05, 0.82, [para([run(
    "Only after that approval does the console offer to connect a model to draft the change, and only "
    "after a second approval would anything deploy. The graph search, the verdict and the audit trail "
    "all happen before any of that — which is the point. Most requests are answered, and some are "
    "refused, without a model ever being contacted.", 8.5, MUTE, TEXT)], line=1.3)])
slides.append(slide(b))

# ----------------------------------------------------- end to end user flow -
b = title("How a user interacts, and what runs behind each step",
          "Four round trips to the server. Each line appears on screen because the work behind it finished, not on a timer.")
b += kicker("user action  ·  what the system does  ·  what it produces")

steps = [
    ("1", "Types the request", BLUE,
     '"Terminate HealthcareFacilityNetwork when due date is exceeded"',
     "A request record is created with a correlation id, status Draft, and an audit stamp. "
     "The request type is read from the sentence, never asked for."),
    ("2", "Reading the request", TEAL,
     "Action, object, component type, name and shape",
     "Rule-based parsing, not a model. The reading is shown back on screen so a misreading is "
     "visible and correctable rather than silent."),
    ("3", "Resolving the scope", JADE,
     "49 objects in the Network Services pod",
     "Declared pod list, resolved against the org, plus what the profile maintains and what carries "
     "a pod record type. Each object can say why it qualified."),
    ("4", "Searching the graph", PLUM,
     "The object named becomes the anchor",
     "The map is loaded into memory and walked outwards: what runs on the object, what that calls, "
     "and what that calls in turn. Findings are written as rows against the request."),
    ("5", "Assessing reuse", GREEN,
     "One of six verdicts, with evidence",
     "Already exists · Likely already handled · Needs review · Safe to create · Impact assessed · "
     "Needs clarification. Three of the six stop the request."),
]
y = 1.42
for n, head, col, out, detail in steps:
    b += card(0.4, y, 12.53, 0.93, fill=PAPER, line=RULE)
    b += shape("ellipse", 0.62, y + 0.22, 0.34, 0.34, fill=col)
    b += textbox(0.62, y + 0.22, 0.34, 0.34,
                 [para([run(n, 9, PAPER, TEXT_SB, bold=True)], align="ctr")],
                 anchor="ctr")
    b += textbox(1.12, y + 0.16, 2.35, 0.22,
                 [para([run(head, 9.5, INK, TEXT_SB, bold=True)])])
    b += textbox(1.12, y + 0.44, 2.35, 0.36,
                 [para([run(out, 7.5, col, TEXT)], line=1.15)])
    b += textbox(3.72, y + 0.2, 8.98, 0.62,
                 [para([run(detail, 8.5, MUTE, TEXT)], line=1.28)])
    y += 1.02

b += textbox(0.4, 6.58, 12.53, 0.22, [para([run(
    "Measured in the sandbox: about seven seconds from pressing Analyse to a verdict on screen.",
    8, FAINT, TEXT, italic=True)])])
slides.append(slide(b))

# ------------------------------------------------------- how graph is built -
b = title("How the graph is built",
          "A background job that reads metadata and writes a map. It never reads a single record of business data.")
b += kicker("layers 2, 3 and 6 of the architecture, running inside Salesforce")

stages = [
    ("Decide the scope", BLUE,
     "Which objects belong to the pod",
     "The declared list is the authority. Objects the profile can maintain and objects carrying a "
     "Network Services record type are added to it. The job refuses to run on an empty scope or on "
     "more than 220 objects, because that is an org rather than a pod."),
    ("Read the metadata", TEAL,
     "Describe calls and queries",
     "Objects, fields and record types by describe. Triggers, flows and Apex classes by query. "
     "Fields on the large standard objects are ordered custom first, because the pod's own data "
     "lives there."),
    ("Make the points", JADE,
     "Every component becomes a node",
     "Name, API name, type, a risk tier, and a provenance line saying where the fact came from. "
     "Object, field, record type, flow, trigger, Apex class and test class."),
    ("Join them up", PLUM,
     "Every connection becomes a typed line",
     "Has field · has record type · related to · runs on · reads or writes · called by a trigger · "
     "calls another class. The last two are what make a handler's handler reachable."),
    ("Write the map", AMBER,
     "One JSON document, saved as a file",
     "Serialised, versioned, and re-merged into the combined document the searches read. "
     "The job reports what it did, what it truncated, and anything it could not resolve."),
]
y = 1.42
for head, col, sub, detail in stages:
    b += shape("rect", 0.4, y, 0.05, 0.86, fill=col)
    b += card(0.45, y, 12.48, 0.86, fill=PAPER, line=RULE)
    b += textbox(0.68, y + 0.14, 2.6, 0.22,
                 [para([run(head, 9.5, INK, TEXT_SB, bold=True)])])
    b += textbox(0.68, y + 0.42, 2.6, 0.3,
                 [para([run(sub, 7.5, col, TEXT)], line=1.15)])
    b += textbox(3.55, y + 0.15, 9.15, 0.62,
                 [para([run(detail, 8.5, MUTE, TEXT)], line=1.28)])
    y += 0.95

b += shape("roundRect", 0.4, 6.2, 12.53, 0.62, fill="EAF1F9", radius=10000)
b += textbox(0.64, 6.36, 12.05, 0.32, [para([run(
    "A component with no relationship to anything is dropped. A point nothing connects to can never "
    "be reached by a search, so it is noise rather than information.",
    8.5, TEAL, TEXT, italic=True)])])
slides.append(slide(b))

# --------------------------------------------------------------- pod scope --
b = title("What counts as the Network Services pod",
          "Three signals, unioned. The declared list is the authority; the other two corroborate it.")
b += kicker("49 objects in scope  ·  out of roughly 1,400 in the org")

sigs = [
    ("13", "Declared in code", BLUE,
     "Account and its chain — Healthcare Provider, Healthcare Facility, Practitioner Facility, "
     "Care Provider Facility Specialty, Contract Payment Agreement — plus Healthcare Facility "
     "Network, Lead, Contact, Opportunity, Task, Case and Credentialing Application."),
    ("12", "Profile can maintain", TEAL,
     "Objects the Network Services profile can create or edit. A reasonable signal, and on its own "
     "an incomplete one."),
    ("24", "Carries a pod record type", JADE,
     "Objects with an active Network Services or Network Services TX CIN record type. This is where "
     "the pod's records actually live."),
]
for i, (n, h, c, d) in enumerate(sigs):
    x = 0.4 + i * 4.22
    b += card(x, 1.42, 3.98, 2.05, fill=PAPER, line=RULE)
    b += textbox(x + 0.24, 1.58, 1.6, 0.42, [para([run(n, 22, c, DISPLAY_B)])])
    b += textbox(x + 0.24, 2.08, 3.5, 0.22,
                 [para([run(h, 9.5, INK, TEXT_SB, bold=True)])])
    b += textbox(x + 0.24, 2.38, 3.5, 0.95,
                 [para([run(d, 7.5, MUTE, TEXT)], line=1.25)])

b += shape("roundRect", 0.4, 3.66, 6.14, 2.0, fill="FDF3E6", radius=10000)
b += textbox(0.64, 3.84, 5.7, 0.22,
             [para([run("Why a declared list had to exist", 9.5, AMBER, TEXT_SB,
                        bold=True)])])
b += textbox(0.64, 4.14, 5.7, 1.4, [para([run(
    "Several of these objects are written only by automation and never typed by a person, so the "
    "profile has no create permission on them. Healthcare Facility Network — the object most "
    "questions are about — was invisible for exactly that reason. Deriving the pod from create "
    "access quietly excluded the thing the pod exists to build.",
    8, "8A5620", TEXT)], line=1.3)])

b += shape("roundRect", 6.79, 3.66, 6.14, 2.0, fill="FBEAEF", radius=10000)
b += textbox(7.03, 3.84, 5.7, 0.22,
             [para([run("And why permission sets were not the answer", 9.5, ROSE,
                        TEXT_SB, bold=True)])])
b += textbox(7.03, 4.14, 5.7, 1.4, [para([run(
    "The obvious alternative was to scope from the permission sets the pod's users are assigned. "
    "Measured in the sandbox, those grant write on 1,319 objects. That is most of the org rather "
    "than a pod, and it would exceed the export limit immediately. The diagnostic stays, as a "
    "warning rather than a source.",
    8, "8C2A48", TEXT)], line=1.3)])

b += textbox(0.4, 5.86, 12.53, 0.5, [para([run(
    "Every object in scope can state which of the three signals put it there, so “why is this in "
    "scope” always has an answer that somebody can check.",
    8.5, MUTE, TEXT, italic=True)])])
slides.append(slide(b))

# ------------------------------------------------------------ json storage --
b = title("Where the map is stored, and why it is a file",
          "The first attempt stored the graph as records. It filled the sandbox and blocked everyone from creating anything.")
b += kicker("layer 5  ·  graph storage")

b += shape("roundRect", 0.4, 1.42, 6.14, 1.95, fill="FBEAEF", radius=10000)
b += chip(0.64, 1.6, 1.75, 0.26, "ATTEMPT ONE", ROSE, size=7)
b += textbox(0.64, 1.98, 5.7, 0.22,
             [para([run("One row per point, one per line", 9.5, "8C2A48",
                        TEXT_SB, bold=True)])])
b += textbox(0.64, 2.28, 5.7, 1.0, [para([run(
    "For a single pod that came to 113,310 rows and roughly 221 MB of data storage. It filled the "
    "sandbox, blocked record creation org-wide, and a plain delete frees nothing for fifteen days.",
    8, "8C2A48", TEXT)], line=1.3)])

b += shape("roundRect", 6.79, 1.42, 6.14, 1.95, fill="E6F2F0", radius=10000)
b += chip(7.03, 1.6, 1.75, 0.26, "ATTEMPT TWO", JADE, size=7)
b += textbox(7.03, 1.98, 5.7, 0.22,
             [para([run("One JSON document, saved as a file", 9.5, "0B6B60",
                        TEXT_SB, bold=True)])])
b += textbox(7.03, 2.28, 5.7, 1.0, [para([run(
    "The same graph, about 1.8 MB. Written in a single operation, versioned on every rebuild, and "
    "counted against file storage rather than data storage — so it stops competing with real records.",
    8, "0B6B60", TEXT)], line=1.3)])

b += textbox(0.4, 3.56, 6.0, 0.22,
             [para([run("The options, and why each was rejected or chosen", 9.5,
                        INK, TEXT_SB, bold=True)])])
rows = [
    ("Custom object records", "Rejected", ROSE,
     "221 MB for one pod. Does not survive a second one."),
    ("Static resource", "Rejected", ROSE,
     "Cannot be written from Apex at runtime without a Metadata API call."),
    ("Git, fetched at run time", "Deferred", MUTE,
     "Needs a network call and a stored token for every read."),
    ("Salesforce File", "Chosen", GREEN,
     "Apex-writable in one insert, versioned, and on a separate storage allocation."),
]
y = 3.88
for name, verdict, col, why in rows:
    b += card(0.4, y, 12.53, 0.44, fill=PAPER if verdict != "Chosen" else "E6F2F0",
              line=RULE)
    b += textbox(0.64, y + 0.12, 3.0, 0.22,
                 [para([run(name, 8.5, INK, TEXT_SB, bold=True)])])
    b += textbox(3.75, y + 0.12, 1.3, 0.22,
                 [para([run(verdict, 8.5, col, TEXT_SB, bold=True)])])
    b += textbox(5.2, y + 0.12, 7.5, 0.22,
                 [para([run(why, 8.5, MUTE, TEXT)])])
    y += 0.52

b += shape("roundRect", 0.4, 6.05, 12.53, 0.72, fill="EAF1F9", radius=10000)
b += textbox(0.64, 6.2, 12.05, 0.45, [para([run(
    "The size ceiling is real and it drives the design. The whole map is loaded into memory to be "
    "searched, and peak memory runs about five and a half times the file size, so a properly scoped "
    "pod has to stay near a megabyte. Correct scoping is a prerequisite, not a tuning exercise.",
    8.5, BLUE, TEXT)], line=1.25)])
slides.append(slide(b))

# --------------------------------------------------- request reaches graph --
b = title("How the request on screen reaches the graph",
          "From a sentence in a text box to a starting point on the map, with no model in the path.")
b += kicker("layer 8  ·  adapter and user interface")

lanes = [
    ("The screen", "Lightning Web Component", BLUE,
     "One text box and one button, inside Salesforce. The person writes in their own words. Nothing "
     "is categorised, tagged or classified first, because being asked to classify the request is "
     "being asked to answer it."),
    ("The entry point", "Apex controller", TEAL,
     "Creates the request record with an audit trail, then runs the four analysis steps as separate "
     "calls so each result can appear as it lands rather than after a silent wait."),
    ("Reading the request", "Intent parser", JADE,
     "Rules, not a model. Reads the action, component type, name and object out of free text, and "
     "reports its reading back. A wrong interpretation becomes visible and correctable instead of "
     "silently steering the search."),
    ("Finding the starting point", "Graph adapter", PLUM,
     "Matches the sentence against the graph's own object names, including labels written with "
     "spaces and custom objects without their suffix. Any object in the pod is found without a rule "
     "written for each phrasing."),
]
y = 1.42
for head, sub, col, detail in lanes:
    b += card(0.4, y, 12.53, 1.06, fill=PAPER, line=RULE)
    b += shape("rect", 0.4, y, 0.05, 1.06, fill=col)
    b += textbox(0.72, y + 0.18, 2.5, 0.22,
                 [para([run(head, 9.5, INK, TEXT_SB, bold=True)])])
    b += textbox(0.72, y + 0.46, 2.5, 0.22,
                 [para([run(sub, 7.5, col, MONO)])])
    b += textbox(3.5, y + 0.2, 9.2, 0.75,
                 [para([run(detail, 8.5, MUTE, TEXT)], line=1.3)])
    y += 1.16

b += shape("roundRect", 0.4, 6.1, 12.53, 0.68, fill="FDF3E6", radius=10000)
b += textbox(0.64, 6.26, 12.05, 0.42, [para([run(
    "The whole read path is rules and lookups. That is what makes it free to run, fast enough to use "
    "conversationally, and explainable line by line when somebody disagrees with the answer.",
    8.5, "8A5620", TEXT)], line=1.25)])
slides.append(slide(b))

# ---------------------------------------------------------- graph traversal -
b = title("What happens inside the graph",
          "Start where the request points, walk outwards, and stop before the answer turns into a directory.")
b += kicker("layer 7  ·  the graph engine")

hops = [
    ("The object named", "the anchor", BLUE),
    ("One step out", "flows and triggers that run on it", TEAL),
    ("Two steps out", "the classes those hand off to", JADE),
    ("Three steps out", "and what those call in turn", PLUM),
]
x = 0.4
for label, sub, col in hops:
    b += shape("roundRect", x, 1.42, 2.86, 0.95, fill=col, radius=12000)
    b += textbox(x + 0.14, 1.56, 2.58, 0.22,
                 [para([run(label, 9.5, PAPER, TEXT_SB, bold=True)], align="ctr")])
    b += textbox(x + 0.14, 1.86, 2.58, 0.38,
                 [para([run(sub, 7.5, "D6E3EA", TEXT)], align="ctr", line=1.15)])
    if x < 10.0:
        b += arrow(x + 2.93, 1.84, 0.28)
    x += 3.21

b += shape("roundRect", 0.4, 2.62, 6.14, 2.1, fill="FBEAEF", radius=10000)
b += textbox(0.64, 2.8, 5.7, 0.22,
             [para([run("The rule that keeps the answer useful", 9.5, ROSE,
                        TEXT_SB, bold=True)])])
b += textbox(0.64, 3.1, 5.7, 1.5, [para([run(
    "Another object is a destination, not a corridor. Account connects to about seventy classes, so "
    "walking through it turned one question about Healthcare Facility Network into fifty-five "
    "results, almost none of them relevant. That Account is involved is worth reporting. Everything "
    "on the far side of it is not.",
    8, "8C2A48", TEXT)], line=1.3)])

b += shape("roundRect", 6.79, 2.62, 6.14, 2.1, fill="E6F2F0", radius=10000)
b += textbox(7.03, 2.8, 5.7, 0.22,
             [para([run("What comes back", 9.5, "0B6B60", TEXT_SB, bold=True)])])
b += textbox(7.03, 3.1, 5.7, 1.5, [para([run(
    "A bounded list, ordered so it reads top down: the automation that runs, then the code it calls, "
    "then the object and its fields. Every row says how it connects in a sentence — “Flow that runs "
    "when Healthcare Facility Network records change” — and carries the provenance of the fact.",
    8, "0B6B60", TEXT)], line=1.3)])

b += textbox(0.4, 4.95, 12.53, 0.22,
             [para([run("Two things a name search cannot do", 9.5, INK, TEXT_SB,
                        bold=True)])])
pair = [
    ("Reach across a name boundary", BLUE,
     "A test class two steps from an object is found by walking the relationships, even when the two "
     "share no word in common. Search has nothing to match on."),
    ("Follow a handler to its handler", TEAL,
     "A trigger body is two lines that call a handler. Without call relationships, “what happens when "
     "this is saved” returns the name of a file containing nothing."),
]
for i, (h, c, d) in enumerate(pair):
    x = 0.4 + i * 6.39
    b += card(x, 5.24, 6.14, 1.15, fill=PAPER, line=RULE)
    b += textbox(x + 0.24, 5.4, 5.7, 0.22,
                 [para([run(h, 9, c, TEXT_SB, bold=True)])])
    b += textbox(x + 0.24, 5.68, 5.7, 0.62,
                 [para([run(d, 8, MUTE, TEXT)], line=1.3)])
slides.append(slide(b))

# ------------------------------------------------------------- the verdict --
b = title("The verdict, and why three of them say no",
          "The system exists to refuse work that is already done. A clearance has to be earned.")
b += kicker("layer 8  ·  reuse analysis")

verdicts = [
    ("Already exists", "Stops", ROSE,
     "The component asked for is already in the org. It is cited by name and type, with its "
     "provenance, and the request is told to reuse it."),
    ("Likely already handled", "Stops", ROSE,
     "Automation on that object already references what the request wants written. Building a "
     "second one would run the logic twice."),
    ("Needs review", "Stops", AMBER,
     "Automation fires on the object but its internals cannot be read yet, so the request cannot "
     "honestly be cleared. It says so rather than guessing."),
    ("Safe to create", "Allows", GREEN,
     "Nothing matching was found and the object was genuinely searched. Similar names are listed "
     "anyway, in case one of them was what was meant."),
    ("Impact assessed", "Informs", BLUE,
     "For a change to something that exists: what it touches directly, what it touches one step "
     "out, and how much of that is high risk."),
    ("Needs clarification", "Asks", MUTE,
     "Nothing matched, or the object sits outside the pod. An absence of evidence is never reported "
     "as evidence of absence."),
]
for i, (h, tag, c, d) in enumerate(verdicts):
    col = i % 3
    row = i // 3
    x = 0.4 + col * 4.22
    y = 1.42 + row * 1.68
    b += card(x, y, 3.98, 1.5, fill=PAPER, line=RULE)
    b += shape("ellipse", x + 0.24, y + 0.22, 0.13, 0.13, fill=c)
    b += textbox(x + 0.46, y + 0.16, 2.6, 0.22,
                 [para([run(h, 9.5, INK, TEXT_SB, bold=True)])])
    b += chip(x + 3.06, y + 0.15, 0.7, 0.24, tag, c, size=6.5)
    b += textbox(x + 0.24, y + 0.52, 3.5, 0.88,
                 [para([run(d, 8, MUTE, TEXT)], line=1.28)])

b += shape("roundRect", 0.4, 4.86, 12.53, 1.0, fill="EAF1F9", radius=10000)
b += textbox(0.64, 5.02, 12.05, 0.72, [para([run(
    "The rule underneath all six: the console may only clear a request if it can show it actually "
    "searched. If the object was never in the graph, “nothing was found” means the search never "
    "happened, and reporting that as a clearance is a guess dressed up as an answer. That distinction "
    "is the difference between a useful system and a confident one.",
    8.5, BLUE, TEXT)], line=1.3)])

b += textbox(0.4, 6.1, 12.53, 0.5, [para([run(
    "Worked example from the sandbox: asking to create a field that already existed returned the "
    "existing field, its real type and where it came from, and refused to duplicate it.",
    8.5, MUTE, TEXT, italic=True)])])
slides.append(slide(b))

# ------------------------------------------------------ low level design ----
b = title("Low-level design",
          "The pieces that do the work, what each is responsible for, and the contract between them.")
b += kicker("what is deployed in the sandbox today")

groups = [
    ("Building the map", BLUE, [
        ("Pod definition", "The pod declared in one reviewable place: objects, record type names, "
         "automation naming conventions, entry triggers"),
        ("Scope resolver", "Resolves the declared list against the org, unions the profile and "
         "record type signals, and names anything that did not resolve"),
        ("Exporter", "Background job: reads metadata, emits points and lines, reports what it "
         "truncated, stops on a CPU or memory budget rather than failing"),
        ("File store", "Saves and loads the JSON document with a hard size ceiling, versioned on "
         "every rebuild"),
    ]),
    ("Answering the question", JADE, [
        ("Graph engine", "Loads the document, indexes it into adjacency maps, walks relationships "
         "with no query against the org"),
        ("Intent parser", "Reads action, object, component type and name out of free text, and "
         "distinguishes a component request from a behaviour one"),
        ("Graph adapter", "Picks the anchor, bounds how far the walk travels, and orders the "
         "findings so the answer reads top down"),
        ("Reuse analyser", "Turns findings into one of six verdicts, and refuses to clear a request "
         "it cannot show it searched"),
    ]),
]
for gi, (gh, gc, items) in enumerate(groups):
    x = 0.4 + gi * 6.39
    b += shape("ellipse", x, 1.42, 0.26, 0.26, fill=gc)
    b += textbox(x + 0.4, 1.42, 5.7, 0.26,
                 [para([run(gh, 10, INK, TEXT_SB, bold=True)])], anchor="ctr")
    yy = 1.84
    for h, d in items:
        b += card(x, yy, 6.14, 0.98, fill=PAPER, line=RULE)
        b += textbox(x + 0.24, yy + 0.14, 5.7, 0.22,
                     [para([run(h, 9, gc, TEXT_SB, bold=True)])])
        b += textbox(x + 0.24, yy + 0.42, 5.7, 0.48,
                     [para([run(d, 7.5, MUTE, TEXT)], line=1.25)])
        yy += 1.08

b += shape("roundRect", 0.4, 6.22, 12.53, 0.6, fill="EAF1F9", radius=10000)
b += textbox(0.64, 6.36, 12.05, 0.34, [para([run(
    "Findings are stored as one row per component, never as a blob in a field, so the approval "
    "screen, the ticket and any audit report all read the same evidence and cannot drift apart.",
    8.5, BLUE, TEXT)])])
slides.append(slide(b))

# ---------------------------------------------- POC vs target architecture --
b = title("The eight layers: designed, and as built",
          "The POC is a compressed, in-org version of the target pipeline. The contract between layers is what keeps it replaceable.")
b += kicker("designed  ·  built in the sandbox  ·  the gap")

hdr_y = 1.42
b += textbox(0.4, hdr_y, 2.1, 0.2,
             [para([run("LAYER", 7, FAINT, TEXT_SB, bold=True)])])
b += textbox(2.6, hdr_y, 3.5, 0.2,
             [para([run("DESIGNED", 7, FAINT, TEXT_SB, bold=True)])])
b += textbox(6.3, hdr_y, 3.5, 0.2,
             [para([run("BUILT IN THE POC", 7, FAINT, TEXT_SB, bold=True)])])
b += textbox(10.0, hdr_y, 2.93, 0.2,
             [para([run("STATUS", 7, FAINT, TEXT_SB, bold=True)])])

layers = [
    ("1 · Sources", "Six systems of record", "Salesforce only", "Phase 2", AMBER),
    ("2 · Connectors", "Per-source auth, delta pull, hashing", "Describe calls and queries in Apex", "Working", GREEN),
    ("3 · Ingestors", "Parsers per source format", "Metadata typed into points", "Working", GREEN),
    ("4 · Domain model", "Extensible engineering context", "Neutral node and line contract", "Working", GREEN),
    ("5 · Graph storage", "Vendor-neutral JSON", "JSON in a Salesforce File", "Working", GREEN),
    ("6 · Exporter", "Scheduled rebuild", "Background job, rebuilt on demand", "Working", GREEN),
    ("7 · Graph engine", "In-memory traversal", "In-memory traversal in Apex", "Working", GREEN),
    ("8 · Adapter and UI", "Adapter, prompt, model", "Adapter and reuse analysis; no model yet", "Gate 2", AMBER),
]
y = 1.66
for name, designed, built, status, col in layers:
    b += card(0.4, y, 12.53, 0.52, fill=PAPER, line=RULE)
    b += textbox(0.62, y + 0.15, 2.1, 0.22,
                 [para([run(name, 8.5, INK, TEXT_SB, bold=True)])])
    b += textbox(2.8, y + 0.15, 3.4, 0.22,
                 [para([run(designed, 8, MUTE, TEXT)])])
    b += textbox(6.5, y + 0.15, 3.4, 0.22,
                 [para([run(built, 8, NAVY, TEXT)])])
    b += chip(10.2, y + 0.13, 1.0, 0.26, status, col, size=6.5)
    y += 0.6

b += shape("roundRect", 0.4, 6.56, 12.53, 0.56, fill="EAF1F9", radius=10000)
b += textbox(0.64, 6.68, 12.05, 0.34, [para([run(
    "Moving layers 2 to 7 out to a cloud service changes one class. Everything above depends on the "
    "evidence contract, not on where the graph runs.",
    8.5, BLUE, TEXT)])])
slides.append(slide(b))

# ---------------------------------------------------------------- measured --
b = title("Measured in the sandbox",
          "Not projections. These are the numbers the system reported from the Network Services pod.")
b += kicker("network services  ·  sandbox  ·  september 2026")

stats = [
    ("2,859", "components mapped", "objects, fields, record types, flows, triggers and Apex classes", BLUE),
    ("3,969", "relationships between them", "each one typed, and each one carrying its provenance", TEAL),
    ("1.8 MB", "the entire map as one file", "the same graph stored as records came to 221 MB", JADE),
    ("49", "objects in the pod scope", "out of roughly 1,400 objects in the org", PLUM),
    ("~7 sec", "to answer a request", "four server calls, no AI model, no external service", AMBER),
    ("495", "active flows in the org", "all of them now readable, where 200 was the previous ceiling", GREEN),
]
for i, (v, l, d, c) in enumerate(stats):
    col = i % 3
    row = i // 3
    x = 0.4 + col * 4.22
    y = 1.42 + row * 1.74
    b += card(x, y, 3.98, 1.56, fill=PAPER, line=RULE)
    b += textbox(x + 0.24, y + 0.2, 3.5, 0.46, [para([run(v, 22, c, DISPLAY_B)])])
    b += textbox(x + 0.24, y + 0.74, 3.5, 0.22,
                 [para([run(l, 9, INK, TEXT_SB, bold=True)])])
    b += textbox(x + 0.24, y + 1.0, 3.5, 0.46,
                 [para([run(d, 7.5, MUTE, TEXT)], line=1.25)])

b += shape("roundRect", 0.4, 4.98, 12.53, 0.86, fill="FDF3E6", radius=10000)
b += textbox(0.64, 5.12, 12.05, 0.6, [para([run(
    "One more measurement worth stating: the permission sets assigned to the pod's users grant write "
    "on 1,319 objects. That is the number that settled how the pod scope had to be defined, and it "
    "is the kind of thing nobody knows until the system measures it and says so out loud.",
    8.5, "8A5620", TEXT)], line=1.3)])

b += textbox(0.4, 6.05, 12.53, 0.7, [para([run(
    "Every figure on this slide came out of a debug log in the sandbox. Where the system could not "
    "measure something, it says so rather than estimating: flow internals, real dependency "
    "relationships and test coverage are named as gaps on the next slide rather than approximated here.",
    8.5, MUTE, TEXT, italic=True)], line=1.3)])
slides.append(slide(b))

# ------------------------------------------------------------------ status --
b = title("Where we are, and what comes next",
          "The read path works end to end. The write path is the next phase, and it is gated on a human at both ends.")
b += kicker("built  ·  next  ·  the one constraint that governs all of it")

done = [
    "The graph builds from the org and rebuilds on demand",
    "Pod scope declared, resolved, and explained object by object",
    "Requests read from plain English, with the reading shown back",
    "Search anchored on the object named, bounded so it stays relevant",
    "Relationships between code, not just between names",
    "Six verdicts, with evidence and provenance on every row",
    "Duplicate detection: asking for a field that exists returns that field",
    "Approval gate, with the model choice held behind it",
]
nxt = [
    "Read what a flow does internally, not only that it exists",
    "Real dependency relationships in place of text matching",
    "Flow-to-subflow chains, the way Apex call chains already work",
    "Raise the delivery ticket automatically on approval",
    "Connect a model to draft the change, after approval",
    "Deploy to sandbox, run the tests, report results back",
    "Jira and Confluence as read sources, for requirements and rules",
]

b += shape("ellipse", 0.4, 1.42, 0.26, 0.26, fill=GREEN)
b += textbox(0.8, 1.42, 5.5, 0.26,
             [para([run("Working today", 10, INK, TEXT_SB, bold=True)])],
             anchor="ctr")
b += shape("roundRect", 0.4, 1.8, 6.14, 3.5, fill="E9F3EA", radius=8000)
y = 1.98
for t in done:
    b += shape("ellipse", 0.66, y + 0.06, 0.09, 0.09, fill=GREEN)
    b += textbox(0.9, y, 5.5, 0.38, [para([run(t, 8.5, "1F5B24", TEXT)], line=1.2)])
    y += 0.42

b += shape("ellipse", 6.79, 1.42, 0.26, 0.26, fill=AMBER)
b += textbox(7.19, 1.42, 5.5, 0.26,
             [para([run("Next", 10, INK, TEXT_SB, bold=True)])], anchor="ctr")
b += shape("roundRect", 6.79, 1.8, 6.14, 3.5, fill="FDF3E6", radius=8000)
y = 1.98
for t in nxt:
    b += shape("ellipse", 7.05, y + 0.06, 0.09, 0.09, fill=AMBER)
    b += textbox(7.29, y, 5.5, 0.38, [para([run(t, 8.5, "8A5620", TEXT)], line=1.2)])
    y += 0.42

b += shape("roundRect", 0.4, 5.5, 12.53, 1.28, fill=NAVY, radius=10000)
b += textbox(0.72, 5.68, 11.9, 0.24,
             [para([run("The constraint that governs all of it", 10, PAPER,
                        TEXT_SB, bold=True)])])
b += textbox(0.72, 5.98, 11.9, 0.68, [para([run(
    "Sandbox only. No phase of this design holds a production credential. No model is contacted "
    "before a person has read the evidence and approved it, and nothing deploys before a second "
    "approval. The graph is what makes those approvals cheap enough to be real rather than a "
    "rubber stamp — the evidence is already on the screen when the question is asked.",
    8.5, "C7D2DE", TEXT)], line=1.3)])
slides.append(slide(b))


# ================================================================== MERGE ====
def merge(src, out, new_slides):
    zin = zipfile.ZipFile(src)
    names = zin.namelist()
    existing = [n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)]
    start = max(int(re.search(r"(\d+)\.xml$", n).group(1)) for n in existing) + 1

    pres = zin.read("ppt/presentation.xml").decode("utf8")
    prels = zin.read("ppt/_rels/presentation.xml.rels").decode("utf8")
    ctypes = zin.read("[Content_Types].xml").decode("utf8")

    next_rid = max(int(x) for x in re.findall(r'Id="rId(\d+)"', prels)) + 1
    next_sid = max(int(x) for x in re.findall(r'<p:sldId id="(\d+)"', pres)) + 1

    add_rels, add_ct, add_sld = [], [], []
    payload = {}
    for i, xml in enumerate(new_slides):
        n = start + i
        path = "ppt/slides/slide%d.xml" % n
        payload[path] = xml.encode("utf8")
        payload["ppt/slides/_rels/slide%d.xml.rels" % n] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/slideLayout" '
            'Target="../slideLayouts/slideLayout1.xml"/></Relationships>'
        ).encode("utf8")
        add_rels.append(
            '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/slide" Target="slides/slide%d.xml"/>'
            % (next_rid + i, n))
        add_ct.append(
            '<Override PartName="/ppt/slides/slide%d.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' % n)
        add_sld.append('<p:sldId id="%d" r:id="rId%d"/>'
                       % (next_sid + i, next_rid + i))

    prels = prels.replace("</Relationships>", "".join(add_rels) + "</Relationships>")
    ctypes = ctypes.replace("</Types>", "".join(add_ct) + "</Types>")
    pres = pres.replace("</p:sldIdLst>", "".join(add_sld) + "</p:sldIdLst>")

    tmp = out + ".tmp"
    zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        if item.filename == "ppt/presentation.xml":
            zout.writestr(item, pres.encode("utf8"))
        elif item.filename == "ppt/_rels/presentation.xml.rels":
            zout.writestr(item, prels.encode("utf8"))
        elif item.filename == "[Content_Types].xml":
            zout.writestr(item, ctypes.encode("utf8"))
        else:
            zout.writestr(item, zin.read(item.filename))
    for path, data in payload.items():
        zout.writestr(path, data)
    zout.close()
    zin.close()
    shutil.move(tmp, out)
    return start, start + len(new_slides) - 1


if __name__ == "__main__":
    first, last = merge(SRC, OUT, slides)
    print("added %d slides: slide%d..slide%d" % (len(slides), first, last))
