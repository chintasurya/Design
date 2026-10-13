"""The three plan slides for the MAD deck: timeline, team, commercials.

Called by build_mad_ig_deck.py. One staffing plan drives all three, so the
timeline's phases, the team's headcount and the price cannot disagree.

Rates are ASSUMED bill rates for sizing, not an Insight Global rate card:
replace the per-role rates in ROLES before the numbers go to a client.
"""
import math

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from build_mad_ig_deck import (BLACK, CONTENT_FLOOR, CYAN, CYAN_T, GREEN, GREEN_T, GREY, MAGENTA, MAGENTA_T,
                               MUTE, NAVY, RULE, TXT, VIOLET, VIOLET_T, WHITE, YELLOW, YELLOW_T, Canvas, rgb,
                               set_notes)

HOURS = 160             # per FTE-month
GATE_DISCOUNT = 0.13    # fixed fee by gate vs time and materials: IG prices the outcome and brings its accelerators
PLATFORM_EARLY, PLATFORM_SCALE = 8000, 20000   # USD per month, GCP + model usage allowance, at cost

# phase, months (first, last), gate
PHASES = [("0", "Mobilise", 1, 1, "Access and decisions signed"),
          ("1", "Knowledge graph", 2, 5, "Gate 1 · graph proven on 10-15 past changes"),
          ("2", "MAD pilot", 6, 9, "Gate 2 · two pilots measured"),
          ("3", "Harden", 10, 11, "Gate 3 · production authorised"),
          ("4", "Scale wave 1", 12, 14, "5 pods live"),
          ("5", "Scale wave 2", 15, 17, "All 9-10 pods live"),
          ("6", "Handover", 18, 18, "Run team takes over")]

# role, what they build, ASSUMED offshore bill rate (USD/h), FTE per phase (0..6), category colour.
# Every role is offshore. Rates are for sizing only: replace with the Insight Global rate card.
ROLES = [
    ("Engagement lead / project manager", "Gates, sprint plans, RAID log, pod baselines and requirements "
     "workshops (no separate BA)", 145, [1, 1, 1, 1, 1, 1, 1], NAVY),
    ("Solution architect", "End-to-end design: GCP landing zone, Spanner Graph model, Salesforce and "
     "Copado integration, security", 175, [1, 1, 1, 1, 1, 1, 1], NAVY),
    ("AI harness architect", "Harness design: agent loop, OpenAI Agents SDK, Codex SDK, MCP tool gateway, guardrails, evaluation "
     "strategy", 195, [1, 1, 1, 1, 1, 1, 1], CYAN),
    ("Harness engineers", "Build the 7 agents, the run loop, tool gateway, approval and Change Guardian "
     "services; tune them inside each pod", 165, [0, 2, 3, 3, 3, 3, 1], CYAN),
    ("Knowledge graph engineers", "Six source connectors, DLP, Spanner Graph (GQL), Graph API + MCP; "
     "add each wave's sources", 135, [0, 2, 2, 1, 1, 1, 0], VIOLET),
    ("Cloud and DevOps engineers", "Terraform, Cloud Run, Workflows, IAM, VPC-SC, monitoring; Copado "
     "pipeline and CI checks", 125, [1, 2, 2, 2, 2, 2, 1], NAVY),
    ("Salesforce Health Cloud developers", "Health Cloud skill packs: Apex, LWC and Flow patterns, golden "
     "examples; review agent code in pilots", 120, [0, 1, 2, 2, 2, 2, 1], NAVY),
    ("Marketing / Data Cloud developer", "Nudge skill pack: SFMC SQL, AMPscript, Journey and Data Cloud "
     "templates; review agent output", 115, [0, 0, 1, 1, 1, 1, 0], NAVY),
    ("QA automation engineers", "Test Agent skills, Copado Robotic Testing, Zephyr; the evaluation set that "
     "gates every agent change", 100, [0, 1, 3, 3, 3, 3, 1], CYAN),
    ("Cloud security engineer (HIPAA)", "HIPAA controls, DLP rules, IAM and VPC-SC review, pen test, BAA "
     "and data terms", 145, [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0], MAGENTA),
]
RUN_ROLES = [("Harness engineer, run lead", 165), ("Knowledge graph and cloud engineer", 135),
             ("Salesforce developer", 120), ("QA automation engineer", 100)]
RUN_TEAM = "a run team of %d, offshore: one harness engineer as lead, plus graph and cloud, Salesforce and QA" % len(
    RUN_ROLES)
RUN_MONTHLY = sum(r for _, r in RUN_ROLES) * HOURS


def rate_span():
    rates = [r[2] for r in ROLES]
    return "$%d-%d/h" % (min(rates), max(rates))


def build_price():
    tm = sum(phase_cost(i) for i in range(len(PHASES)))
    return tm, tm * (1 - GATE_DISCOUNT)


def months(p):
    return p[3] - p[2] + 1


def phase_cost(i):
    return sum(r[3][i] * months(PHASES[i]) * HOURS * r[2] for r in ROLES)


def fte_in_phase(i):
    return sum(r[3][i] for r in ROLES)


def fte_months():
    return sum(r[3][i] * months(p) for r in ROLES for i, p in enumerate(PHASES))


def blended_rate():
    return sum(phase_cost(i) for i in range(len(PHASES))) / (fte_months() * HOURS)


def peak_phase():
    return max(range(len(PHASES)), key=fte_in_phase)


def people_at_peak():
    i = peak_phase()
    return sum(math.ceil(r[3][i]) for r in ROLES)


def phase_span(i):
    p = PHASES[i]
    return "month %d" % p[2] if p[2] == p[3] else "months %d-%d" % (p[2], p[3])


def k(v):
    return "$%.2fM" % (v / 1e6) if v >= 1e6 else "$%dK" % round(v / 1000)


def m(v):
    return "$%.2fM" % (v / 1e6)


def when(r):
    act = [i for i, f in enumerate(r[3]) if f]
    return "M%d-M%d" % (PHASES[act[0]][2], PHASES[act[-1]][3])


def peak(r):
    pk = max(r[3])
    return "%g" % math.ceil(pk)


# ------------------------------------------------------------------ timeline
def timeline_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    cv.header("ASCENSION MAD APPROACH · IMPLEMENTATION TIMELINE",
              "Eighteen months from mobilisation to every pod live on MAD",
              "Seven phases, each closed by a gate Ascension signs. Two pods prove it by month 9; production is "
              "authorised at month 11; the remaining pods join in two waves.")
    X0, X1 = 2.55, 12.88
    mw = (X1 - X0) / 18
    mx = lambda mo: X0 + (mo - 1) * mw

    # years and months
    cv.rect(X0, 1.24, 12 * mw - 0.03, 0.2, BLACK)
    cv.text(X0, 1.24, 12 * mw, 0.2, "YEAR 1", size=7, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
            anchor=MSO_ANCHOR.MIDDLE, track=200)
    cv.rect(mx(13), 1.24, 6 * mw, 0.2, NAVY)
    cv.text(mx(13), 1.24, 6 * mw, 0.2, "YEAR 2 · FIRST HALF", size=7, bold=True, color=WHITE,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=200)
    for mo in range(1, 19):
        cv.text(mx(mo), 1.47, mw, 0.17, "M%d" % mo, size=7, color=MUTE, align=PP_ALIGN.CENTER,
                anchor=MSO_ANCHOR.MIDDLE)

    # phases
    cv.label(0.45, 1.75, 2.0, "Phase")
    pcol = [GREY, VIOLET_T, CYAN_T, MAGENTA_T, YELLOW_T, YELLOW_T, GREEN_T]
    pline = ["BFBFBF", VIOLET, "0097AD", MAGENTA, "C9A800", "C9A800", GREEN]
    for (num, name, a, b, _), f, l in zip(PHASES, pcol, pline):
        cv.rect(mx(a) + 0.01, 1.68, (b - a + 1) * mw - 0.03, 0.4, f, l, 1.0)
        cv.text(mx(a) + 0.04, 1.68, (b - a + 1) * mw - 0.08, 0.4,
                [[(num + "  ", {"bold": True}), (name, {})]] if b - a > 0 else [[(num, {"bold": True})]],
                size=7.5, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    rows = [
        ("Knowledge graph", VIOLET, VIOLET_T, [(2, 5, "Connectors, Spanner Graph, Graph API + MCP"),
                                                (12, 14, "Wave 1 pod sources"), (15, 17, "Wave 2 pod sources")]),
        ("Agent platform", "0097AD", CYAN_T, [(5, 9, "Workflow, dispatcher, 7 agents, pod skills"),
                                              (10, 11, "Harden, evals"), (12, 17, "Pod skills for each wave")]),
        ("Controls and governance", MAGENTA, MAGENTA_T, [(6, 9, "Gateway, approvals, Guardian, passport"),
                                                         (10, 11, "Prod sign-off")]),
        ("Salesforce + Copado", NAVY, "E6EAEC", [(2, 6, "Identities, DEV sandboxes, Copado API"),
                                                 (7, 9, "Health Cloud pilot"), (12, 17, "Wave builds")]),
        ("Marketing + Data Cloud", NAVY, "E6EAEC", [(5, 6, "SFMC tooling"), (7, 9, "Nudge pilot"),
                                                    (12, 17, "Marketing pods in waves")]),
        ("QA and evaluation", "0097AD", CYAN_T, [(5, 9, "Test Agent, Zephyr, Robotic Testing"),
                                                 (10, 17, "Evaluation set, regression for each wave")]),
        ("Security and compliance", MAGENTA, MAGENTA_T, [(1, 3, "Reviews, BAA, VPC-SC"),
                                                         (10, 11, "Pen test, DR"), (12, 18, "Quarterly reviews")]),
        ("Change and adoption", "C9A800", YELLOW_T, [(1, 4, "Pod baselines"), (8, 9, "Pilot pods trained"),
                                                     (12, 17, "Pod onboarding waves"), (18, 18, "Run")]),
    ]
    y = 2.2
    rh = 0.44
    for name, line, fill, bars in rows:
        cv.rect(0.45, y + rh - 0.005, X1 - 0.45, 0.005, RULE)
        cv.text(0.45, y, 2.0, rh, name, size=8, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        for a, b, t in bars:
            bx, bw = mx(a) + 0.02, (b - a + 1) * mw - 0.04
            cv.rect(bx, y + 0.07, bw, rh - 0.14, fill, line, 0.75, MSO_SHAPE.ROUNDED_RECTANGLE, 0.3)
            cv.text(bx + 0.04, y + 0.07, bw - 0.08, rh - 0.14, t, size=6.5, align=PP_ALIGN.CENTER,
                    anchor=MSO_ANCHOR.MIDDLE)
        y += rh

    # milestones
    cv.label(0.45, y + 0.12, 2.0, "Gates and milestones")
    my = y + 0.1
    cv.rect(X0, my + 0.1, X1 - X0, 0.012, BLACK)
    level = [0, 1, 0, 1, 0, 1, 0]
    for (num, name, a, b, gate), lv in zip(PHASES, level):
        gx = min(mx(b) + mw, X1 - 0.1)
        cv.rect(gx - 0.09, my + 0.015, 0.18, 0.18, YELLOW, BLACK, 0.75, MSO_SHAPE.DIAMOND)
        lw = 1.75
        lx = min(max(gx - lw / 2, X0 - 0.4), X1 - lw)
        al = PP_ALIGN.RIGHT if lx == X1 - lw else PP_ALIGN.CENTER
        ly = my + 0.24 + lv * 0.3
        cv.text(lx, ly, lw, 0.28, [[("M%d  " % b, {"bold": True}), (gate, {})]], size=6.5, align=al,
                anchor=MSO_ANCHOR.TOP)
    cv.text(0.45, CONTENT_FLOOR - 0.2, 12.4, 0.18,
            "Pods live: 0 until month 8 · 2 at month 9 (Network Services, Nudge) · 5 at month 14 · all 9-10 at "
            "month 17. Durations are planning estimates, confirmed at the Phase 0 gate.",
            size=6.5, color=MUTE, anchor=MSO_ANCHOR.MIDDLE)
    set_notes(s, TIMELINE_NOTES)
    return s


# ------------------------------------------------------------------ team
def team_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    fm = fte_months()
    peak_fte = fte_in_phase(peak_phase())
    people = people_at_peak()
    cv.header("ASCENSION MAD APPROACH · DELIVERY TEAM",
              "The team: %d people at peak across %d roles, delivered offshore" % (people, len(ROLES)),
              "Sized from the phase plan: %g FTE at peak, %g FTE-months over eighteen months, all roles offshore. "
              "Ascension's approvers and pod leads are not in this count." % (peak_fte, fm))
    # table
    X0 = 0.45
    cols = [("Role", 2.35), ("What they build", 3.85), ("Peak", 0.55), ("Where", 0.75), ("On team", 0.85)]
    y = 1.28
    x = X0
    for name, w in cols:
        cv.text(x + 0.05, y, w - 0.05, 0.24, name, size=8, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        x += w
    tw = sum(w for _, w in cols)
    cv.rect(X0, y + 0.26, tw, 0.015, BLACK)
    y += 0.3
    rh = 0.44
    for i, (role, tech, rate, fte, col) in enumerate(ROLES):
        if i % 2 == 0:
            cv.rect(X0, y, tw, rh, GREY)
        cv.rect(X0 + 0.06, y + rh / 2 - 0.05, 0.1, 0.1, col)
        vals = [role, tech, peak(ROLES[i]), "Offshore", when(ROLES[i])]
        x = X0
        for j, ((_, w), v) in enumerate(zip(cols, vals)):
            pad = 0.22 if j == 0 else 0.05
            cv.text(x + pad, y, w - pad - 0.04, rh, v, size=7.5 if j != 1 else 7, bold=(j == 0 or j == 2),
                    anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER if j == 2 else None)
            x += w
        y += rh
    cv.rect(X0, y, tw, 0.015, BLACK)
    cv.text(X0, y + 0.05, tw, 0.2,
            [[("From month 19, run as a service by ", {"bold": True}), (RUN_TEAM + ".", {})]], size=7.5,
            anchor=MSO_ANCHOR.MIDDLE)

    # right column
    RX = X0 + tw + 0.3
    RW = 12.88 - RX
    tiles = [("%g" % peak_fte, "FTE at peak (%s)" % phase_span(peak_phase())), ("%g" % fm, "FTE-months, 18 months"),
             ("100%", "offshore delivery, every role")]
    tw3 = (RW - 0.2) / 3
    for i, (big, small) in enumerate(tiles):
        tx = RX + i * (tw3 + 0.1)
        cv.rect(tx, 1.28, tw3, 0.78, GREY)
        cv.text(tx + 0.08, 1.32, tw3 - 0.12, 0.38, big, size=20, font="Trenda IG Text Light",
                anchor=MSO_ANCHOR.MIDDLE)
        cv.text(tx + 0.08, 1.7, tw3 - 0.12, 0.32, small, size=6.5, color=MUTE)
    # ramp chart
    cv.label(RX, 2.2, RW, "Team size by month (FTE)")
    cd = CategoryChartData()
    cats, vals = [], []
    for i, p in enumerate(PHASES):
        for mo in range(p[2], p[3] + 1):
            cats.append("M%d" % mo)
            vals.append(fte_in_phase(i))
    cd.categories = cats
    cd.add_series("FTE", vals)
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(RX - 0.05), Inches(2.38), Inches(RW + 0.1),
                            Inches(1.95), cd)
    ch = gf.chart
    ch.has_legend = False
    ch.has_title = False
    plot = ch.plots[0]
    plot.gap_width = 40
    ser = plot.series[0]
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = rgb(CYAN)
    plot.has_data_labels = False
    for ax in (ch.category_axis, ch.value_axis):
        ax.tick_labels.font.size = Pt(6.5)
        ax.tick_labels.font.name = TXT
        ax.tick_labels.font.color.rgb = rgb(MUTE)
        ax.format.line.color.rgb = rgb(RULE)
    ch.value_axis.has_major_gridlines = True
    ch.value_axis.major_gridlines.format.line.color.rgb = rgb("EDEDED")
    ch.value_axis.maximum_scale = 5 * math.ceil(peak_fte / 5 + 0.5)
    ch.value_axis.major_unit = 5
    # what Ascension provides
    by = 4.45
    cv.rect(RX, by, RW, CONTENT_FLOOR - 0.02 - by, YELLOW_T, YELLOW, 1.0)
    cv.text(RX + 0.12, by + 0.08, RW - 0.24, 0.2, "ASCENSION PROVIDES, NOT IN THIS COUNT", size=7, bold=True,
            track=150)
    items = ["Product owner for each pod (H1)", "Pod leads and architects as approvers (H2, H3)",
             "Business owners for UAT (H4)", "Release owner and CAB",
             "Security and compliance reviewers", "GCP cloud team: landing zone, access",
             "Salesforce and Copado admins: identities, sandboxes"]
    for i, t in enumerate(items):
        iy = by + 0.36 + i * 0.27
        cv.rect(RX + 0.14, iy + 0.06, 0.06, 0.06, BLACK)
        cv.text(RX + 0.28, iy, RW - 0.4, 0.2, t, size=7.5)
    set_notes(s, team_notes())
    return s


# ------------------------------------------------------------------ commercials
def commercials_slide(prs, layout):
    s = prs.slides.add_slide(layout)
    cv = Canvas(s)
    tm, fixed = build_price()
    plat = sum((PLATFORM_EARLY if p[3] <= 11 else PLATFORM_SCALE) * months(p) for p in PHASES)
    fm = fte_months()
    cv.header("ASCENSION MAD APPROACH · COMMERCIALS",
              "Investment: %s over eighteen months, paid as each gate passes" % m(fixed),
              "A fixed fee for each phase, invoiced only when that phase's gate is signed. Platform usage is passed "
              "through at cost. From month 19, MAD runs as a managed service.")
    X0 = 0.45
    cols = [("Phase", 1.75), ("Months", 0.85), ("Peak team", 0.8), ("Time and materials", 1.25),
            ("Fixed fee", 1.0), ("Invoiced when", 2.45)]
    tw = sum(w for _, w in cols)
    y = 1.28
    x = X0
    for name, w in cols:
        pad = 0.25 if name == "Invoiced when" else 0.05
        cv.text(x + pad, y, w - pad - (0.05 if name in ("Time and materials", "Fixed fee", "Peak team") else 0),
                0.24, name, size=8, bold=True, anchor=MSO_ANCHOR.MIDDLE,
                align=PP_ALIGN.RIGHT if name in ("Time and materials", "Fixed fee", "Peak team") else None)
        x += w
    cv.rect(X0, y + 0.26, tw, 0.015, BLACK)
    y += 0.3
    rh = 0.42
    for i, p in enumerate(PHASES):
        if i % 2 == 0:
            cv.rect(X0, y, tw, rh, GREY)
        tmc = phase_cost(i)
        mon = "M%d" % p[2] if p[2] == p[3] else "M%d-M%d" % (p[2], p[3])
        vals = [p[0] + "  " + p[1], mon, "%g" % fte_in_phase(i), k(tmc), k(tmc * (1 - GATE_DISCOUNT)), p[4]]
        x = X0
        for j, ((name, w), v) in enumerate(zip(cols, vals)):
            right = name in ("Time and materials", "Fixed fee", "Peak team")
            pad = 0.25 if name == "Invoiced when" else 0.05
            cv.text(x + pad, y, w - pad - 0.05, rh, v, size=7.5, bold=(j in (0, 4)), anchor=MSO_ANCHOR.MIDDLE,
                    align=PP_ALIGN.RIGHT if right else None)
            x += w
        y += rh
    cv.rect(X0, y, tw, 0.015, BLACK)
    x = X0
    tot = ["Total", "18 months", "", m(tm), m(fixed), "%g FTE-months" % fm]
    for j, ((name, w), v) in enumerate(zip(cols, tot)):
        right = name in ("Time and materials", "Fixed fee", "Peak team")
        pad = 0.25 if name == "Invoiced when" else 0.05
        cv.text(x + pad, y + 0.03, w - pad - 0.05, 0.34, v, size=9 if j in (3, 4) else 8, bold=True,
                anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.RIGHT if right else None)
        x += w
    y += 0.42
    cv.rect(X0, y, tw, 0.66, MAGENTA_T)
    cv.text(X0 + 0.12, y + 0.06, tw - 0.24, 0.56,
            [[("Platform usage at cost, outside the fee: ", {"bold": True}),
              ("Google Cloud and model usage, allowance %s/month to month 11 and %s/month from month 12, about %s "
               "over 18 months. Sized with Ascension's cloud team in Phase 0." % (k(PLATFORM_EARLY), k(PLATFORM_SCALE),
                                                                                  m(plat)), {})]], size=7.5,
            anchor=MSO_ANCHOR.MIDDLE)

    # options: build (A or B), then run (C)
    RX = X0 + tw + 0.3
    RW = 12.88 - RX

    def card(y, h, title, price, body, rec=False, tag=None, extra=None):
        if rec:
            ix, iy, iw, ih = cv.frame(RX, y, RW, h)
        else:
            ix, iy, iw, ih = RX, y, RW, h
            cv.rect(RX, y, RW, h, WHITE, RULE)
        cv.text(ix + 0.12, iy + 0.06, iw - 1.5, 0.2, title, size=8.5, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(ix + iw - 1.42, iy + 0.04, 1.3, 0.26, price, size=12, font="Trenda IG Text Light",
                align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        cv.text(ix + 0.12, iy + 0.32, iw - 0.24, 0.4, body, size=7)
        if extra:
            cv.rect(ix + 0.1, iy + ih - 0.36, iw - 0.2, 0.28, GREY)
            cv.text(ix + 0.18, iy + ih - 0.36, iw - 0.36, 0.28, extra, size=7, anchor=MSO_ANCHOR.MIDDLE)
        if tag:
            cv.rect(ix + iw - 1.12, iy + ih - 0.24, 1.0, 0.16, BLACK, None, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
                    radius=0.5)
            cv.text(ix + iw - 1.12, iy + ih - 0.24, 1.0, 0.16, tag, size=5.5, bold=True, color=WHITE,
                    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, track=150)

    cv.label(RX, 1.28, RW, "Build · months 1-18 · choose one")
    card(1.5, 0.98, "A · Fixed fee by gate", m(fixed),
         "Priced on the outcome, %d%% below time and materials: Insight Global brings its agent accelerators "
         "and carries delivery risk. Paid only when each gate is signed." % round(GATE_DISCOUNT * 100),
         rec=True, tag="RECOMMENDED")
    card(2.56, 0.74, "B · Time and materials", m(tm),
         "Every hour billed monthly at the rate card, on actuals. Ascension carries the risk of overruns "
         "and pays whether or not a gate passes.")
    cv.label(RX, 3.42, RW, "Run · from month 19, after the build ends")
    run_total = RUN_MONTHLY + PLATFORM_SCALE
    card(3.62, 1.12, "C · Managed service, monthly", "%s / month" % k(RUN_MONTHLY),
         "Starts only once all pods are live. A run team of %d, offshore, keeps the graph, agents, Guardian "
         "rules and evaluations current, fixes failed runs and adds new sources." % len(RUN_ROLES),
         extra=[[("Team %s + platform ~%s = " % (k(RUN_MONTHLY), k(PLATFORM_SCALE)), {}),
                 ("about %s a month (%s a year)" % (k(run_total), m(run_total * 12)), {"bold": True})]])
    vy = 4.86
    vh = CONTENT_FLOOR - 0.02 - vy
    cv.rect(RX, vy, RW, vh, BLACK)
    cv.text(RX + 0.14, vy + 0.08, RW - 0.28, 0.2, "VALUE CHECK", size=7, bold=True, color=YELLOW, track=150)
    import story_slides
    pm = [story_slides.pod_model(pd) for pd in story_slides.PODS]
    s_lo, s_hi = sum(x["save_lo"] for x in pm), sum(x["save_hi"] for x in pm)
    cv.text(RX + 0.14, vy + 0.3, RW - 0.28, vh - 0.36, [
        [("Two pods alone, VBC and Network Services, save %s-%s a year " % (m(s_lo), m(s_hi)),
          {"color": WHITE}), ("with agent-first squads.", {"color": "BFBFBF"})],
        [("The build fee pays back in about %.1f to %.1f years from those two pods; " % (fixed / s_hi, fixed / s_lo),
          {"color": WHITE}), ("every further pod on MAD shortens it.", {"color": WHITE})],
        [("Floor across all pods: 20-25% lower net run cost (business outcomes slide).", {"color": "BFBFBF"})],
    ], size=9, after=6)
    cv.text(X0, CONTENT_FLOOR - 0.36, tw, 0.34,
            "Assumed offshore bill rates for sizing, by role: %s, blended $%.0f/h, %d h per FTE-month, "
            "%g FTE-months. Replace with the Insight Global rate card before sharing. Excludes Ascension staff time "
            "and existing licences (Salesforce, Copado, Atlassian, Codex Enterprise)." % (
                rate_span(), blended_rate(), HOURS, fm),
            size=6, color=MUTE)
    return s


TIMELINE_NOTES = """SLIDE: Implementation timeline, 18 months   (about 2 minutes)

KEY MESSAGE
Eighteen months from mobilisation to every pod on MAD, in seven phases, each closed by a gate Ascension signs. Nothing scales until two pilots have proved it.

WALK IT
- Phase 0, month 1: access, approvers, the graph-store and model decisions, the landing zone. Gate: access matrix and decisions signed.
- Phase 1, months 2-5: the knowledge graph. Six connectors, Spanner Graph, the Graph API. Gate 1: on 10-15 past changes the graph answers exists, impact and owners correctly.
- Phase 2, months 6-9: the agent platform, the controls, and two pilots: Network Services on Health Cloud and a Nudge campaign on Marketing Cloud. Gate 2: both pilots measured against the manual baseline.
- Phase 3, months 10-11: harden. Evaluation set, pen test, disaster recovery, CAB integration. Gate 3: production use authorised.
- Phases 4 and 5, months 12-17: two onboarding waves, about three pods then four or five, each adding its sources to the graph and its skills to the agents. All 9-10 pods live by month 17.
- Phase 6, month 18: handover to the run team.

IF ASKED
- Why so long for the graph? Six sources, PHI controls and proving accuracy on real past changes come before any agent touches code.
- Can it go faster? The waves can overlap once Gate 3 is passed; the pilot cannot be skipped.
- Durations are planning estimates, confirmed at the Phase 0 gate."""

def team_notes():
    fm = fte_months()
    ramp = ", ".join("%g in %s" % (fte_in_phase(i), phase_span(i)) for i in range(len(PHASES)))
    return """SLIDE: Delivery team   (about 2 minutes)

KEY MESSAGE
A lean, senior team: %d people at peak across %d roles, every role offshore, %g FTE-months over 18 months. MAD's own agents do much of the build, so the team is small and senior rather than large.

RAMP (FTE by phase)
%s.

WHO DOES WHAT
- Engagement lead / project manager: one person runs governance, gates, sprints and the requirements workshops; no separate business analyst, because the Requirements Agent drafts the stories and Ascension's product owners sign them.
- Solution architect: the end-to-end design across Google Cloud, the graph, Salesforce and Copado.
- AI harness architect: designs the harness around Codex Enterprise: the agent loop, which tools each step may use, what context it reads, the guardrails, the approval points and the evaluation strategy.
- Harness engineers: build the harness: the seven agents, the run loop with checkpoints and retries, the MCP tool gateway, context assembly from the graph, the guardrails, the approval and Change Guardian services; they sit with each pod to tune it on real stories.
- Knowledge graph engineers: the six connectors and Spanner Graph, then each wave's sources.
- Cloud and DevOps engineers (2 from month 2): landing zone, Cloud Run, IAM, VPC-SC, monitoring and the Copado pipeline (covers what a separate SRE would).
- Salesforce Health Cloud developers and the Marketing / Data Cloud developer do NOT build features for the pods. They build the pod skill packs the agents follow: approved Apex, LWC and Flow patterns, Health Cloud data-model rules, SFMC SQL, AMPscript and Journey templates, and the golden examples. In the pilots they review every agent-written change, which is how the agents reach Ascension's quality bar. Without them the agents would write generic Salesforce code.
- QA automation engineers (3 from the pilot): the Test Agent's skills, Copado Robotic Testing and Zephyr, and the evaluation set that gates every change to an agent.
- Cloud security engineer (HIPAA), half-time across the 18 months: HIPAA controls, DLP rules, IAM and VPC-SC review, pen test, BAA and data terms.

NOT IN THE COUNT
Ascension's product owners, approvers, release owner, security reviewers, cloud team and Salesforce / Copado admins.

AFTER MONTH 18
%s.""" % (people_at_peak(), len(ROLES), fm, ramp, RUN_TEAM[0].upper() + RUN_TEAM[1:])
