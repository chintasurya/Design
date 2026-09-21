/* Patient and Provider Gap Intelligence: layered solution design deck.
   Brand system lifted from the Insight Global case study one-pager. */

const pptxgen = require("pptxgenjs");
const path = require("path");

const OUT = process.argv[2] || path.join(__dirname, "gap-intelligence.pptx");

/* ---------- brand ---------- */
const C = {
  ink: "0D0D12",
  ink2: "1A1A1A",
  navy: "1E2761",
  green: "3DDC97",
  green2: "1E8E5A",
  red: "B23A48",
  grey: "5A5A5A",
  rule: "CCCCCC",
  panel: "F2F4F3",
  panel2: "E9EDEB",
  white: "FFFFFF",
};
const F = { head: "Cambria", body: "Calibri" };

const W = 13.33, H = 7.5;
const M = 0.55;                 // side margin
const CW = W - M * 2;           // content width
const BODY_TOP = 1.58;
const BODY_BOT = 6.92;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Insight Global Labs";
pres.company = "Insight Global";
pres.title = "Patient and Provider Gap Intelligence";

let pageNo = 0;

/* ---------- primitives ---------- */

function txt(slide, text, o) {
  slide.addText(text, Object.assign({ isTextBox: true, margin: 0, valign: "top" }, o));
}

function marker(slide, x, y, color, size) {
  const s = size || 0.13;
  slide.addShape(pres.ShapeType.rect, { x, y, w: s, h: s, fill: { color } });
}

/* dark title block used on every content slide */
function header(slide, eyebrow, title, badge, badgeColor) {
  slide.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: W, h: 1.26, fill: { color: C.ink } });
  txt(slide, eyebrow, {
    x: M, y: 0.18, w: 8.6, h: 0.26, fontSize: 10.5, bold: true, charSpacing: 2,
    color: C.green, fontFace: F.body,
  });
  txt(slide, title, {
    x: M, y: 0.44, w: badge ? 10.2 : 12.2, h: 0.76, fontSize: 22, bold: true,
    color: C.white, fontFace: F.head, valign: "top",
  });
  if (badge) {
    slide.addShape(pres.ShapeType.roundRect, {
      x: 11.0, y: 0.43, w: 1.78, h: 0.46, rectRadius: 0.08,
      fill: { color: C.ink2 }, line: { color: badgeColor || C.green, width: 1 },
    });
    txt(slide, badge, {
      x: 11.0, y: 0.43, w: 1.78, h: 0.46, fontSize: 11.5, bold: true,
      color: badgeColor || C.green, fontFace: F.body, align: "center", valign: "middle",
    });
  }
}

function footer(slide, dark) {
  pageNo += 1;
  const col = dark ? "8A8F8C" : C.grey;
  txt(slide, "Insight Global Labs  ·  Solution 2 design  ·  Confidential", {
    x: M, y: 7.02, w: 7.0, h: 0.26, fontSize: 9, color: col, fontFace: F.body,
  });
  txt(slide, String(pageNo), {
    x: W - M - 0.9, y: 7.02, w: 0.9, h: 0.26, fontSize: 9, color: col,
    fontFace: F.body, align: "right",
  });
}

/* standard light content slide */
function slide(eyebrow, title, badge, badgeColor) {
  const s = pres.addSlide();
  s.background = { color: C.white };
  header(s, eyebrow, title, badge, badgeColor);
  footer(s, false);
  return s;
}

/* a tinted content card */
function card(slide, o) {
  const { x, y, w, h, accent, title, lines, titleSize, bodySize, fill } = o;
  slide.addShape(pres.ShapeType.rect, {
    x, y, w, h, fill: { color: fill || C.panel },
  });
  marker(slide, x + 0.22, y + 0.26, accent || C.green2);
  txt(slide, title, {
    x: x + 0.48, y: y + 0.17, w: w - 0.7, h: 0.44, fontSize: titleSize || 13,
    bold: true, color: C.ink2, fontFace: F.head,
  });
  if (lines && lines.length) {
    slide.addText(
      lines.map((t, i) => ({
        text: t,
        options: { bullet: false, breakLine: i < lines.length - 1, paraSpaceAfter: 5 },
      })),
      {
        isTextBox: true, margin: 0, x: x + 0.48, y: y + 0.66, w: w - 0.74,
        h: h - 0.82, fontSize: bodySize || 10.5, color: C.ink2, fontFace: F.body,
        valign: "top", lineSpacingMultiple: 1.05,
      }
    );
  }
}

/* a full width note strip */
function note(slide, y, text, accent) {
  slide.addShape(pres.ShapeType.rect, { x: M, y, w: CW, h: 0.52, fill: { color: C.ink } });
  marker(slide, M + 0.22, y + 0.19, accent || C.green);
  txt(slide, text, {
    x: M + 0.48, y, w: CW - 0.7, h: 0.52, fontSize: 11, italic: true,
    color: C.white, fontFace: F.body, valign: "middle",
  });
}

/* simple data table */
function table(slide, o) {
  const { x, y, w, cols, rows, headFill, fontSize } = o;
  const fs = fontSize || 10;
  slide.addTable(
    [cols.map((c) => ({
      text: c.t,
      options: {
        bold: true, color: C.white, fill: { color: headFill || C.navy }, fontSize: fs - 0.5,
        fontFace: F.body, align: c.a || "left", valign: "middle",
      },
    }))].concat(
      rows.map((r, ri) =>
        r.map((cell, ci) => ({
          text: cell,
          options: {
            color: C.ink2, fontSize: fs, fontFace: F.body,
            fill: { color: ri % 2 ? C.panel : C.white },
            align: cols[ci].a || "left", valign: "top",
            bold: ci === 0 && (o.boldFirst !== false),
          },
        }))
      )
    ),
    {
      x, y, w, colW: cols.map((c) => c.w), border: { type: "solid", color: C.rule, pt: 0.5 },
      rowH: o.rowH || 0.32, margin: [4, 7, 4, 7], autoPage: false,
    }
  );
}

/* ================= 1. COVER ================= */
{
  const s = pres.addSlide();
  s.background = { color: C.ink };
  s.addShape(pres.ShapeType.ellipse, {
    x: 11.0, y: -1.05, w: 3.6, h: 3.6, fill: { color: C.navy, transparency: 45 },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: 11.72, y: 2.82, w: 2.3, h: 2.3, fill: { color: C.green, transparency: 80 },
  });
  txt(s, "INSIGHT GLOBAL  ·  SOLUTION DESIGN", {
    x: M, y: 1.28, w: 8.4, h: 0.3, fontSize: 11, bold: true, charSpacing: 2,
    color: C.green, fontFace: F.body,
  });
  txt(s, "Patient and Provider Gap Intelligence, on the Same Knowledge Graph", {
    x: M, y: 1.72, w: 9.7, h: 1.82, fontSize: 33, bold: true, color: C.white, fontFace: F.head,
  });
  txt(s,
    "Solution 2. Find where patient inflow is highest and provider outcomes are weakest, "
    + "explain the gap with evidence, and turn it into a governed campaign. Built on the "
    + "Neo4j graph, TopQuadrant ontology and GraphRAG stack already in production.", {
    x: M, y: 3.66, w: 8.5, h: 1.1, fontSize: 13.5, color: "C9CFCC", fontFace: F.body,
    lineSpacingMultiple: 1.2,
  });
  s.addShape(pres.ShapeType.roundRect, {
    x: 10.35, y: 1.28, w: 2.43, h: 0.5, rectRadius: 0.1,
    fill: { color: C.ink2 }, line: { color: C.green, width: 1 },
  });
  txt(s, "AI Knowledge Graph", {
    x: 10.35, y: 1.28, w: 2.43, h: 0.5, fontSize: 12, bold: true, color: C.white,
    fontFace: F.body, align: "center", valign: "middle",
  });
  // three teaser stats
  const teasers = [
    ["8 layers", "L0 source to L7 governance, every one specified"],
    ["5 gap types", "access, outcome, leakage, care, adequacy"],
    ["1 graph", "the same production Neo4j estate, extended"],
  ];
  teasers.forEach((t, i) => {
    const x = M + i * 4.13;
    s.addShape(pres.ShapeType.rect, { x, y: 5.0, w: 3.85, h: 1.28, fill: { color: "16161C" } });
    marker(s, x + 0.24, 5.24, C.green);
    txt(s, t[0], {
      x: x + 0.5, y: 5.13, w: 3.2, h: 0.4, fontSize: 19, bold: true, color: C.green,
      fontFace: F.head,
    });
    txt(s, t[1], {
      x: x + 0.5, y: 5.6, w: 3.15, h: 0.55, fontSize: 10.5, color: "C9CFCC", fontFace: F.body,
    });
  });
  txt(s, "Prepared for: President, Consulting  |  Office of the CRO/VP, Global Operations  |  Office of the COO", {
    x: M, y: 6.62, w: 11.0, h: 0.28, fontSize: 10, italic: true, color: "8A8F8C", fontFace: F.body,
  });
  footer(s, true);
}

/* ================= 2. FEASIBILITY VERDICT ================= */
{
  const s = slide("FEASIBILITY", "Can the same graph answer it? Yes, with three conditions.", "VERDICT", C.green);
  txt(s, "The question you asked is a graph question. Patient inflow is a traversal, provider outcome is a node property, and the gap between them is the path that does not exist yet. Nothing in it needs a new platform.", {
    x: M, y: BODY_TOP, w: CW, h: 0.6, fontSize: 13, color: C.ink2, fontFace: F.body,
    lineSpacingMultiple: 1.15,
  });
  const cards = [
    {
      accent: C.green2, title: "1 · Same model, new domain",
      lines: [
        "Account becomes Patient and Population.",
        "Opportunity becomes Encounter and Episode.",
        "Product becomes Service Line and Procedure.",
        "BDR and SDR scores become risk, outcome and capacity indices, promoted to traversals the same way.",
        "Neo4j, TopQuadrant, SageMaker, Snowflake, Data Cloud, MCP: unchanged.",
      ],
    },
    {
      accent: C.navy, title: "2 · Outcomes need adjusting first",
      lines: [
        "Ranking raw outcomes punishes the providers who take the sickest patients, and the finding will not survive its first review.",
        "Risk adjustment, minimum denominators, shrinkage and confidence intervals are in the build, not a later refinement.",
        "This is the single largest difference from Solution 1.",
      ],
    },
    {
      accent: C.red, title: "3 · Activation needs a new gate",
      lines: [
        "Consent state, channel permission and suppression are checked at cohort build, not at send.",
        "PHI stays out of model prompts unless the endpoint is covered by a BAA.",
        "A named human approves every cohort before it leaves the building.",
      ],
    },
  ];
  cards.forEach((c, i) => {
    card(s, Object.assign({ x: M + i * 4.13, y: 2.34, w: 3.85, h: 3.2 }, c, { bodySize: 10.5 }));
  });
  note(s, 5.86, "What this is not: it does not make clinical decisions and it does not publish a league table of clinicians. It ranks addressable gaps and names who can close them.", C.red);
}

/* ================= 3. REUSE MAP ================= */
{
  const s = slide("SOLUTION 1 TO SOLUTION 2", "What we reuse, what we adapt, what we build new", "REUSE MAP", C.green);
  txt(s, "The case study asset is the spine. Roughly two thirds of Solution 2 is the Solution 1 stack pointed at a different ontology.", {
    x: M, y: BODY_TOP, w: CW, h: 0.32, fontSize: 12.5, color: C.grey, fontFace: F.body,
  });
  const cols = [
    {
      x: M, accent: C.green2, tag: "REUSE AS IS", bul: "✓",
      items: [
        "Neo4j production cluster and scaled index design",
        "TopQuadrant ontology tooling and SHACL validation",
        "GraphRAG retrieval pattern and prompt scaffolding",
        "MCP tool surface into Agentforce and Slack",
        "LLM as a judge evaluation harness and gold set method",
        "Evidence gated, milestone based delivery model",
      ],
    },
    {
      x: M + 4.13, accent: C.navy, tag: "ADAPT", bul: "▪",
      items: [
        "Ontology classes move from sales objects to care delivery objects",
        "Signal migration pipeline retargeted from BDR and SDR to risk, outcome and capacity",
        "Data Cloud bridge carries referral notes, clinical notes and call transcripts",
        "Snowflake models extended from CRM to claims, EHR, directory and scheduling",
        "Agent personas rewritten for market and provider questions",
      ],
    },
    {
      x: M + 8.26, accent: C.red, tag: "BUILD NEW", bul: "+",
      items: [
        "Patient and provider identity resolution, EMPI plus NPI and TIN",
        "Risk adjustment and the statistical guardrail set",
        "Five gap engines and the inflow versus outcome quadrant",
        "Campaign activation with consent gate, holdout and write back",
        "PHI governance, minimum necessary enforcement and audit",
      ],
    },
  ];
  cols.forEach((c) => {
    s.addShape(pres.ShapeType.rect, { x: c.x, y: 2.12, w: 3.85, h: 0.42, fill: { color: c.accent } });
    txt(s, c.tag, {
      x: c.x + 0.2, y: 2.12, w: 3.5, h: 0.42, fontSize: 11, bold: true, charSpacing: 1.5,
      color: C.white, fontFace: F.body, valign: "middle",
    });
    s.addShape(pres.ShapeType.rect, { x: c.x, y: 2.54, w: 3.85, h: 3.4, fill: { color: C.panel } });
    s.addText(
      c.items.map((t, i) => ({
        text: t,
        options: {
          bullet: { characterCode: c.bul === "+" ? "002B" : (c.bul === "✓" ? "2713" : "25AA") },
          breakLine: i < c.items.length - 1, paraSpaceAfter: 9,
        },
      })),
      {
        isTextBox: true, x: c.x + 0.24, y: 2.72, w: 3.4, h: 3.1, margin: 0,
        fontSize: 10.5, color: C.ink2, fontFace: F.body, valign: "top", lineSpacingMultiple: 1.05,
      }
    );
  });
  note(s, 6.14, "Everything in the first two columns is delivery risk already retired. The third column is where the four month plan spends its time.", C.green);
}

/* ================= 4. THE QUESTION, DECOMPOSED + QUADRANT ================= */
{
  const s = slide("THE BUSINESS QUESTION", "Highest inflow, weakest outcome: four computable questions", "MODEL", C.green);
  const qs = [
    ["Q1  Demand", "Where do patients actually come from, by geography and service line, and is that volume growing?"],
    ["Q2  Supply", "Who is contracted to serve them, with what bookable capacity and what panel status?"],
    ["Q3  Performance", "How good is the outcome once you adjust for how sick the patients were?"],
    ["Q4  Addressability", "Which gaps can an outreach actually move, and who is reachable and consented?"],
  ];
  qs.forEach((q, i) => {
    const y = BODY_TOP + i * 1.05;
    s.addShape(pres.ShapeType.rect, { x: M, y, w: 6.35, h: 0.92, fill: { color: C.panel } });
    marker(s, M + 0.22, y + 0.24, [C.green2, C.navy, C.red, C.green2][i]);
    txt(s, q[0], {
      x: M + 0.48, y: y + 0.15, w: 2.0, h: 0.28, fontSize: 12.5, bold: true,
      color: C.ink2, fontFace: F.head,
    });
    txt(s, q[1], {
      x: M + 0.48, y: y + 0.45, w: 5.65, h: 0.42, fontSize: 10.5, color: C.ink2, fontFace: F.body,
    });
  });

  /* quadrant plot */
  const px = 7.42, py = BODY_TOP + 0.48, pw = 5.36, ph = 3.52;
  const hw = pw / 2, hh = ph / 2;
  const quads = [
    { x: px, y: py, label: "GROW", sub: "low volume,\nstrong outcome", fill: "E6F6EF", col: C.green2 },
    { x: px + hw, y: py, label: "PROTECT", sub: "high volume,\nstrong outcome", fill: "DFF2FB", col: C.navy },
    { x: px, y: py + hh, label: "WATCH", sub: "low volume,\nweak outcome", fill: C.panel2, col: C.grey },
    { x: px + hw, y: py + hh, label: "PRIORITY", sub: "high volume,\nweak outcome", fill: "F7E3E6", col: C.red },
  ];
  quads.forEach((q) => {
    s.addShape(pres.ShapeType.rect, {
      x: q.x, y: q.y, w: hw, h: hh, fill: { color: q.fill }, line: { color: C.white, width: 1.5 },
    });
    txt(s, q.label, {
      x: q.x + 0.16, y: q.y + 0.14, w: hw - 0.3, h: 0.28, fontSize: 12.5, bold: true,
      color: q.col, fontFace: F.head,
    });
    txt(s, q.sub, {
      x: q.x + 0.16, y: q.y + 0.46, w: hw - 0.34, h: 0.64, fontSize: 9.5, color: C.grey, fontFace: F.body,
    });
  });
  // scatter dots
  const dots = [
    [0.22, 0.30], [0.35, 0.18], [0.16, 0.52], [0.40, 0.44],
    [0.62, 0.22], [0.80, 0.31], [0.71, 0.14], [0.90, 0.40],
    [0.18, 0.78], [0.33, 0.88], [0.44, 0.70],
    [0.66, 0.74], [0.78, 0.86], [0.88, 0.68], [0.72, 0.92], [0.60, 0.83],
  ];
  dots.forEach(([dx, dy]) => {
    const hot = dx > 0.5 && dy > 0.5;
    s.addShape(pres.ShapeType.ellipse, {
      x: px + dx * pw - 0.055, y: py + dy * ph - 0.055, w: 0.11, h: 0.11,
      fill: { color: hot ? C.red : C.grey, transparency: hot ? 0 : 45 },
    });
  });
  txt(s, "Vertical: risk adjusted outcome, strongest at the top", {
    x: px, y: BODY_TOP + 0.06, w: pw, h: 0.24, fontSize: 9.5, bold: true, color: C.grey, fontFace: F.body,
  });
  txt(s, "Horizontal: patient inflow, highest at the right", {
    x: px, y: py + ph + 0.1, w: pw, h: 0.26, fontSize: 9.5, bold: true, color: C.grey, fontFace: F.body,
  });
  note(s, 6.3, "The PRIORITY quadrant is the campaign cohort. The GROW quadrant is where the volume is steered. Both come out of one query.", C.green);
}

/* ================= 5. FIVE GAPS ================= */
{
  const s = slide("WHAT A GAP ACTUALLY IS", "Six gaps the graph can compute, and what each one triggers", "GAP TYPES", C.green);
  const gaps = [
    ["Access gap", "Demand versus contracted, bookable capacity by geography and service line.", "Triggers: provider recruitment and contracting"],
    ["Outcome gap", "Risk adjusted outcome index against a like for like peer benchmark.", "Triggers: quality improvement campaign"],
    ["Leakage gap", "Attributed patients treated outside the network, traced along referral paths.", "Triggers: in network capture campaign"],
    ["Care gap", "Open quality measures per patient: screening, chronic follow up, adherence.", "Triggers: patient outreach cohort"],
    ["Adequacy gap", "Time, distance and appointment wait standards by county and specialty.", "Triggers: network filing and expansion"],
    ["Link gap", "Entities that exist in the sources but are not related in the ontology.", "Triggers: the graph backlog itself"],
  ];
  gaps.forEach((g, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = M + col * 4.13, y = BODY_TOP + row * 2.28;
    const accent = [C.green2, C.navy, C.red][col];
    s.addShape(pres.ShapeType.rect, { x, y, w: 3.85, h: 2.06, fill: { color: C.panel } });
    s.addShape(pres.ShapeType.roundRect, {
      x: x + 0.22, y: y + 0.22, w: 0.42, h: 0.42, rectRadius: 0.2, fill: { color: accent },
    });
    txt(s, String(i + 1), {
      x: x + 0.22, y: y + 0.22, w: 0.42, h: 0.42, fontSize: 12, bold: true, color: C.white,
      fontFace: F.body, align: "center", valign: "middle",
    });
    txt(s, g[0], {
      x: x + 0.78, y: y + 0.27, w: 2.8, h: 0.32, fontSize: 14, bold: true, color: C.ink2, fontFace: F.head,
    });
    txt(s, g[1], {
      x: x + 0.24, y: y + 0.82, w: 3.4, h: 0.72, fontSize: 10.5, color: C.ink2,
      fontFace: F.body, lineSpacingMultiple: 1.08,
    });
    txt(s, g[2], {
      x: x + 0.24, y: y + 1.6, w: 3.4, h: 0.3, fontSize: 9.5, bold: true, color: accent, fontFace: F.body,
    });
  });
  note(s, 6.16, "Gap six is the one the case study already taught us: entities present in the source but unlinked in the ontology look exactly like a business gap until you check.", C.navy);
}

/* ================= 6. LAYER OVERVIEW ================= */
{
  const s = slide("ARCHITECTURE", "Eight layers, same shape as the delivery solution", "L0 – L7", C.green);
  const layers = [
    ["L0", "Source and ingestion", "Land every system of record without changing what it means", "Snowflake · Data Cloud · S3", C.grey],
    ["L1", "Identity resolution", "One patient, one provider, one place, with evidence kept", "EMPI · NPI and TIN · CCN · geocode", C.grey],
    ["L2", "Ontology and graph", "Make the relationship a first class object, validated on load", "TopQuadrant · SHACL · Neo4j", C.navy],
    ["L3", "Signal", "Promote computed scores to native traversals under a latency SLA", "SageMaker · graph projections", C.navy],
    ["L4", "Gap analytics", "Turn the graph into a ranked, defensible, lineage backed gap list", "Neo4j GDS · Snowflake", C.green2],
    ["L5", "GraphRAG and agents", "Answer in natural language, grounded, with node level citations", "GraphRAG · Agentforce · MCP", C.green2],
    ["L6", "Campaign activation", "Turn a gap into a governed outreach with a holdout", "Health Cloud · Marketing Cloud", C.red],
    ["L7", "Evaluation and governance", "Prove it is right, keep it legal, measure what it moved", "LLM judge · holdouts · audit", C.red],
  ];
  const rowH = 0.55, top = BODY_TOP;
  layers.forEach((l, i) => {
    const y = top + i * (rowH + 0.06);
    s.addShape(pres.ShapeType.rect, { x: M, y, w: CW, h: rowH, fill: { color: i % 2 ? C.panel : C.panel2 } });
    s.addShape(pres.ShapeType.rect, { x: M, y, w: 0.72, h: rowH, fill: { color: l[4] } });
    txt(s, l[0], {
      x: M, y, w: 0.72, h: rowH, fontSize: 13, bold: true, color: C.white,
      fontFace: F.head, align: "center", valign: "middle",
    });
    txt(s, l[1], {
      x: M + 0.95, y, w: 2.6, h: rowH, fontSize: 12, bold: true, color: C.ink2,
      fontFace: F.head, valign: "middle",
    });
    txt(s, l[2], {
      x: M + 3.65, y, w: 5.6, h: rowH, fontSize: 10.5, color: C.ink2, fontFace: F.body, valign: "middle",
    });
    txt(s, l[3], {
      x: M + 9.35, y, w: 2.75, h: rowH, fontSize: 9.5, italic: true, color: C.grey,
      fontFace: F.body, align: "right", valign: "middle",
    });
  });
  txt(s, "L0 to L3 are graph construction. L4 is the answer. L5 to L7 make it usable, governed and measurable.", {
    x: M, y: 6.58, w: CW, h: 0.3, fontSize: 11, italic: true, color: C.grey, fontFace: F.body,
  });
}

/* ================= 7. L0 ================= */
{
  const s = slide("LAYER 0", "Source and ingestion: land it, do not reshape it", "L0", C.green);
  table(s, {
    x: M, y: BODY_TOP, w: CW,
    cols: [
      { t: "Source", w: 2.7 }, { t: "What it contributes", w: 4.5 },
      { t: "Grain", w: 2.4 }, { t: "Latency", w: 2.62 },
    ],
    rows: [
      ["Claims, 837 and 835", "Utilisation, cost, outcome proxies, out of network activity", "Claim line", "Monthly, 30 to 90 day lag"],
      ["EHR and FHIR, US Core", "Diagnoses, procedures, labs, vitals, referrals", "Encounter", "Daily"],
      ["Eligibility and attribution", "Who is in the population and which provider owns them", "Member month", "Monthly"],
      ["Provider directory, NPPES, CAQH, roster", "Identity, specialty, location, contract status", "Provider", "Weekly"],
      ["Scheduling and access", "Bookable supply, wait time, panel open or closed", "Slot", "Daily"],
      ["CRM and Health Cloud", "Relationship, contacts, prior outreach, consent state", "Account and contact", "Near real time"],
      ["Unstructured", "Referral notes, clinical notes, call transcripts", "Document", "Streaming"],
      ["Reference and geo", "SNOMED, ICD-10, CPT, NUCC, census, drive time", "Dimension", "Quarterly"],
    ],
    rowH: 0.42, fontSize: 10,
  });
  note(s, 5.92, "Nothing acquires meaning at L0. Meaning is assigned at L2, so a source correction replays through the graph instead of rewriting it.", C.green);
  txt(s, "Design rule carried from the delivery solution: the obligation was the source of truth there, the ontology is the source of truth here. Inputs stay replayable.", {
    x: M, y: 6.56, w: CW, h: 0.3, fontSize: 10.5, italic: true, color: C.grey, fontFace: F.body,
  });
}

/* ================= 8. L1 ================= */
{
  const s = slide("LAYER 1", "Identity resolution: the ceiling on every number here", "L1", C.green);
  card(s, {
    x: M, y: BODY_TOP, w: 5.95, h: 2.62, accent: C.navy, title: "Patient resolution",
    lines: [
      "Deterministic first: source MRN, member id, and a composite of name, date of birth and last four of SSN.",
      "Probabilistic fallback on name, date of birth, address and phone, with a scored threshold and a manual review band.",
      "Survivorship rules decide which attribute wins when sources disagree, and the losing value is kept.",
      "Cross source links are stored as evidence edges, not silent merges, so a bad link can be reversed.",
    ],
  });
  card(s, {
    x: M + 6.25, y: BODY_TOP, w: 5.95, h: 2.62, accent: C.green2, title: "Provider and place resolution",
    lines: [
      "Individual NPI is the person key. TIN plus NPI is the practice key. CCN is the facility key.",
      "Individual and organisational NPIs are never collapsed into one node.",
      "NUCC taxonomy gives specialty. Address geocodes to census tract for drive time and adequacy work.",
      "Affiliation is time bounded, so a provider who left a practice in March does not distort the year.",
    ],
  });
  note(s, 4.42, "A 92 percent provider match rate means up to 8 percent of what looks like a gap is a join failure. Match rate is published next to every gap, every time.", C.red);
  const stats = [
    ["Deterministic", "exact keys, highest confidence, no review"],
    ["Probabilistic", "scored, thresholded, review band above the floor"],
    ["Evidence edges", "links are reversible, merges are not"],
    ["Published match rate", "every gap carries the rate behind it"],
  ];
  stats.forEach((st, i) => {
    const x = M + i * 3.08;
    s.addShape(pres.ShapeType.rect, { x, y: 5.22, w: 2.85, h: 1.06, fill: { color: C.panel } });
    marker(s, x + 0.2, 5.42, C.navy);
    txt(s, st[0], {
      x: x + 0.44, y: 5.35, w: 2.3, h: 0.3, fontSize: 11, bold: true, color: C.ink2, fontFace: F.head,
    });
    txt(s, st[1], {
      x: x + 0.44, y: 5.68, w: 2.32, h: 0.52, fontSize: 9.5, color: C.grey, fontFace: F.body,
    });
  });
}

/* ================= 9. L2 ONTOLOGY ================= */
{
  const s = slide("LAYER 2", "Ontology and graph model: the relationship is the product", "L2", C.green);
  txt(s, "Core triples, governed in TopQuadrant and enforced by SHACL on load.", {
    x: M, y: BODY_TOP, w: 5.45, h: 0.42, fontSize: 11, color: C.grey, fontFace: F.body,
  });
  const triples = [
    ["Patient", "RESIDES_IN", "Geography"],
    ["Patient", "HAD_ENCOUNTER", "Encounter"],
    ["Patient", "ATTRIBUTED_TO", "Provider"],
    ["Patient", "HAS_OPEN_MEASURE", "Measure"],
    ["Encounter", "PERFORMED_BY", "Provider"],
    ["Encounter", "AT_FACILITY", "Facility"],
    ["Encounter", "FOR_CONDITION", "Condition"],
    ["Condition", "MAPS_TO", "ServiceLine"],
    ["Provider", "AFFILIATED_WITH", "Practice"],
    ["Provider", "HAS_TAXONOMY", "Specialty"],
    ["Provider", "REFERRED_TO", "Provider"],
    ["Provider", "SCORED_ON", "OutcomeIndex"],
    ["Cohort", "TARGETS", "Provider"],
    ["Campaign", "SENT", "Touch"],
    ["Touch", "RESULTED_IN", "Response"],
  ];
  const tw = 5.45, rh = 0.305, rowTop = 2.06;
  triples.forEach((t, i) => {
    const y = rowTop + i * (rh + 0.015);
    const accent = i < 4 ? C.navy : i < 8 ? C.grey : i < 12 ? C.green2 : C.red;
    s.addShape(pres.ShapeType.rect, { x: M, y, w: tw, h: rh, fill: { color: C.panel } });
    s.addShape(pres.ShapeType.rect, { x: M, y, w: 0.055, h: rh, fill: { color: accent } });
    txt(s, t[0], {
      x: M + 0.18, y, w: 1.5, h: rh, fontSize: 9.5, bold: true, color: C.ink2,
      fontFace: F.body, valign: "middle",
    });
    txt(s, ":" + t[1], {
      x: M + 1.72, y, w: 2.1, h: rh, fontSize: 9, bold: true, color: C.green2,
      fontFace: F.body, valign: "middle",
    });
    txt(s, t[2], {
      x: M + 3.88, y, w: 1.45, h: rh, fontSize: 9.5, bold: true, color: C.navy,
      fontFace: F.body, valign: "middle", align: "right",
    });
  });
  card(s, {
    x: 6.3, y: BODY_TOP, w: 6.48, h: 2.42, accent: C.navy, title: "Three rules the ontology enforces",
    lines: [
      "R1  Every score is reachable by traversal. A score stored as a flat attribute cannot be reasoned over, which is exactly what the BDR and SDR migration proved.",
      "R2  Every edge is time bounded. Affiliation, attribution and contract status all change, and a gap computed across a move is a false gap.",
      "R3  Every derived node carries lineage back to the source rows that produced it, or it cannot be published.",
    ],
    bodySize: 10.5,
  });
  card(s, {
    x: 6.3, y: 4.24, w: 6.48, h: 2.44, accent: C.green2, title: "Scale target",
    lines: [
      "The production estate already runs 511,000 plus nodes and 894,000 plus relationships with a scaled index design.",
      "The care delivery subgraph is additive to that estate, not a second graph: patient, encounter, provider, facility, geography and service line attach to the entities that are already there.",
      "Index design is reviewed at M1 against the traversal patterns L4 actually issues, not against the model on paper.",
    ],
    bodySize: 10.5,
  });
}

/* ================= 10. L3 SIGNALS ================= */
{
  const s = slide("LAYER 3", "Signal: scores become traversals, not attributes", "L3", C.green);
  table(s, {
    x: M, y: BODY_TOP, w: CW,
    cols: [
      { t: "Signal", w: 2.75 }, { t: "What it means", w: 4.35 },
      { t: "Method", w: 3.0 }, { t: "Refresh", w: 1.35 }, { t: "SLA", w: 0.77, a: "center" },
    ],
    rows: [
      ["Patient risk score", "Expected acuity and utilisation for the next period", "HCC or CDPS, or internal model on SageMaker", "Monthly", "50ms"],
      ["Risk adjusted outcome index", "Observed over expected for a provider and service line", "O over E with hierarchical shrinkage", "Monthly", "50ms"],
      ["Inflow index", "Patient volume by geography and service line, trended", "Graph aggregation and projection", "Weekly", "50ms"],
      ["Capacity index", "Bookable supply against modelled demand", "Scheduling feed plus panel status", "Daily", "50ms"],
      ["Leakage index", "Share of attributed patients treated out of network", "Bounded path query on referral edges", "Monthly", "50ms"],
      ["Contactability state", "Reachable or not, and on which permitted channel", "CRM plus consent store", "Real time", "50ms"],
    ],
    rowH: 0.48, fontSize: 10,
  });
  note(s, 5.2, "Same pattern as the BDR and SDR migration: a score on a row is a report, a score on a node is an answer. The 50ms budget is what makes an agent reply feel instant.", C.green);
  const boxes = [
    ["Written where it is read", "Indices land on the Provider, Patient and Geography nodes, so retrieval needs no second system."],
    ["Versioned, never overwritten", "Each refresh writes a dated index. Last quarter's gap list can still be reproduced exactly."],
    ["Confidence travels with it", "Every index carries n, its interval and its peer group, and L4 refuses to rank without them."],
  ];
  boxes.forEach((b, i) => {
    const x = M + i * 4.13;
    s.addShape(pres.ShapeType.rect, { x, y: 5.88, w: 3.85, h: 0.96, fill: { color: C.panel } });
    marker(s, x + 0.2, 6.08, C.navy);
    txt(s, b[0], {
      x: x + 0.44, y: 6.0, w: 3.2, h: 0.26, fontSize: 11, bold: true, color: C.ink2, fontFace: F.head,
    });
    txt(s, b[1], {
      x: x + 0.44, y: 6.3, w: 3.25, h: 0.48, fontSize: 9.5, color: C.grey, fontFace: F.body,
    });
  });
}

/* ================= 11. L4 GAP ENGINE ================= */
{
  const s = slide("LAYER 4", "Gap analytics: the ranked list, and why it survives review", "L4", C.green);
  txt(s, "The computation chain", {
    x: M, y: BODY_TOP, w: 6.0, h: 0.3, fontSize: 12.5, bold: true, color: C.ink2, fontFace: F.head,
  });
  const chain = [
    ["1", "Demand", "Inflow index by geography and service line, trended over the attribution window"],
    ["2", "Supply", "Capacity index across contracted providers in the same geography and service line"],
    ["3", "Performance", "Risk adjusted outcome index against the matched peer benchmark"],
    ["4", "Gap score", "A weighted function of demand, supply deficit, outcome deficit and addressability"],
    ["5", "Quadrant", "Rank, place on the inflow versus outcome plane, and attach the evidence"],
  ];
  chain.forEach((c, i) => {
    const y = 2.0 + i * 0.83;
    s.addShape(pres.ShapeType.rect, { x: M, y, w: 6.0, h: 0.7, fill: { color: C.panel } });
    s.addShape(pres.ShapeType.roundRect, {
      x: M + 0.16, y: y + 0.16, w: 0.38, h: 0.38, rectRadius: 0.19, fill: { color: C.green2 },
    });
    txt(s, c[0], {
      x: M + 0.16, y: y + 0.16, w: 0.38, h: 0.38, fontSize: 11, bold: true, color: C.white,
      fontFace: F.body, align: "center", valign: "middle",
    });
    txt(s, c[1], {
      x: M + 0.68, y: y + 0.08, w: 1.4, h: 0.27, fontSize: 11.5, bold: true, color: C.ink2, fontFace: F.head,
    });
    txt(s, c[2], {
      x: M + 0.68, y: y + 0.35, w: 5.1, h: 0.32, fontSize: 9.5, color: C.grey, fontFace: F.body,
    });
  });
  s.addShape(pres.ShapeType.rect, { x: 6.98, y: BODY_TOP, w: 5.8, h: 4.62, fill: { color: C.ink } });
  marker(s, 7.2, BODY_TOP + 0.28, C.green);
  txt(s, "Statistical guardrails", {
    x: 7.46, y: BODY_TOP + 0.2, w: 5.0, h: 0.32, fontSize: 13.5, bold: true, color: C.white, fontFace: F.head,
  });
  const guards = [
    "Minimum denominator. No provider is ranked below the agreed encounter count for that service line.",
    "Shrinkage. Small volume providers are pulled toward the peer mean by empirical Bayes before ranking.",
    "Confidence intervals. Published with every index. Overlapping intervals are reported as not different.",
    "Peer groups. Defined by specialty, care setting and case mix, never by geography alone.",
    "Attribution. One rule per service line, agreed before build, versioned, and stated on every answer.",
    "Lineage. Every gap resolves back to the source rows that produced it, or it is not published.",
  ];
  s.addText(
    guards.map((g, i) => ({
      text: g,
      options: {
        bullet: { characterCode: "25AA" }, breakLine: i < guards.length - 1, paraSpaceAfter: 10,
      },
    })),
    {
      isTextBox: true, x: 7.46, y: BODY_TOP + 0.66, w: 5.1, h: 3.8, margin: 0,
      fontSize: 10.5, color: "D8DCDA", fontFace: F.body, valign: "top", lineSpacingMultiple: 1.05,
    }
  );
  note(s, 6.32, "A gap you cannot defend in front of the provider it names is not a gap, it is a complaint. The guardrails are what make the list usable in a contracting conversation.", C.red);
}

/* ================= 12. L5 GRAPHRAG AND AGENTS ================= */
{
  const s = slide("LAYER 5", "GraphRAG and agents: grounded answers, with citations", "L5", C.green);
  const steps = ["Question", "Entity anchor", "Subgraph expansion", "Signal read", "Rerank and assemble", "Grounded answer"];
  const sw = 2.02, sx0 = M, sy = BODY_TOP;
  steps.forEach((st, i) => {
    s.addShape(pres.ShapeType.chevron, {
      x: sx0 + i * (sw - 0.06), y: sy, w: sw, h: 0.62,
      fill: { color: i === steps.length - 1 ? C.green2 : (i === 0 ? C.grey : C.navy) },
    });
    txt(s, st, {
      x: sx0 + i * (sw - 0.06) + 0.16, y: sy, w: sw - 0.34, h: 0.62, fontSize: 9.5, bold: true,
      color: C.white, fontFace: F.body, align: "center", valign: "middle",
    });
  });
  txt(s, "Resolve county, specialty and provider names to graph identifiers, expand along typed edges within a bounded hop budget, read the indices already sitting on the nodes, then assemble evidence before the model writes a word.", {
    x: M, y: 2.34, w: CW, h: 0.4, fontSize: 10.5, italic: true, color: C.grey, fontFace: F.body,
  });
  const agents = [
    ["Market POV agent", "“Where is our biggest access gap this quarter?”", "Answers with county, service line, gap score and the practices behind it, each one clickable back to its evidence."],
    ["Provider POV agent", "“Why is this practice flagged?”", "Answers with the observed over expected, the peer group, the interval, the volume and the encounters that produced it."],
    ["Campaign planner agent", "“Build me the cohort.”", "Drafts the cohort definition, projected reach and the approvals required. It drafts. It does not send."],
  ];
  agents.forEach((a, i) => {
    const x = M + i * 4.13;
    s.addShape(pres.ShapeType.rect, { x, y: 2.86, w: 3.85, h: 2.5, fill: { color: C.panel } });
    marker(s, x + 0.22, 3.1, [C.green2, C.navy, C.red][i]);
    txt(s, a[0], {
      x: x + 0.48, y: 3.02, w: 3.2, h: 0.3, fontSize: 12.5, bold: true, color: C.ink2, fontFace: F.head,
    });
    txt(s, a[1], {
      x: x + 0.24, y: 3.44, w: 3.4, h: 0.5, fontSize: 10.5, italic: true, color: C.green2, fontFace: F.body,
    });
    txt(s, a[2], {
      x: x + 0.24, y: 4.0, w: 3.4, h: 1.2, fontSize: 10, color: C.ink2, fontFace: F.body,
      lineSpacingMultiple: 1.08,
    });
  });
  s.addShape(pres.ShapeType.rect, { x: M, y: 5.54, w: CW, h: 1.2, fill: { color: C.ink } });
  marker(s, M + 0.22, 5.76, C.red);
  txt(s, "Guardrails", {
    x: M + 0.48, y: 5.68, w: 2.0, h: 0.28, fontSize: 12, bold: true, color: C.white, fontFace: F.head,
  });
  txt(s, "No PHI in a prompt unless the endpoint is covered by a BAA  ·  de-identified aggregates by default  ·  every claim cites the nodes it came from  ·  a refusal path when evidence falls below threshold  ·  full prompt and response audit retained",
    {
      x: M + 0.48, y: 6.02, w: CW - 0.9, h: 0.6, fontSize: 10.5, color: "D8DCDA", fontFace: F.body,
      lineSpacingMultiple: 1.08,
    });
}

/* ================= 13. L6 CAMPAIGN ACTIVATION ================= */
{
  const s = slide("LAYER 6", "Campaign activation: from gap list to governed outreach", "L6", C.green);
  const flow = [
    ["Cohort build", "Drawn from the quadrant and the gap score, with the target metric named up front", "Out: cohort definition"],
    ["Consent gate", "Opt in state, channel permission, suppression list and a minimum necessary check", "Out: eligible list"],
    ["Human review", "Clinical and compliance approval, versioned, with the approver recorded", "Out: approval record"],
    ["Channel routing", "Provider: field task, contracting outreach, quality packet. Patient: SMS, email, call list, care manager", "Out: channel plan"],
    ["Holdout and send", "A randomised control held back at cohort build, ten percent by default, never carved out afterwards", "Out: test and control"],
    ["Write back", "Campaign, Touch and Response land on the graph and feed the next cycle", "Out: graph nodes"],
  ];
  const bw = 1.95, gap = 0.1;
  flow.forEach((f, i) => {
    const x = M + i * (bw + gap);
    const accent = i === 1 || i === 2 ? C.red : (i === 5 ? C.green2 : C.navy);
    s.addShape(pres.ShapeType.rect, { x, y: BODY_TOP, w: bw, h: 2.5, fill: { color: C.panel } });
    s.addShape(pres.ShapeType.rect, { x, y: BODY_TOP, w: bw, h: 0.4, fill: { color: accent } });
    txt(s, String(i + 1), {
      x: x + 0.1, y: BODY_TOP, w: 0.3, h: 0.4, fontSize: 10.5, bold: true, color: C.white,
      fontFace: F.body, valign: "middle",
    });
    txt(s, f[0], {
      x: x + 0.42, y: BODY_TOP, w: bw - 0.5, h: 0.4, fontSize: 10, bold: true, color: C.white,
      fontFace: F.body, valign: "middle",
    });
    txt(s, f[1], {
      x: x + 0.16, y: BODY_TOP + 0.54, w: bw - 0.32, h: 1.9, fontSize: 9.5, color: C.ink2,
      fontFace: F.body, valign: "top", lineSpacingMultiple: 1.08,
    });
    txt(s, f[2], {
      x: x + 0.16, y: BODY_TOP + 2.12, w: bw - 0.32, h: 0.28, fontSize: 9, bold: true,
      color: accent, fontFace: F.body,
    });
    if (i < flow.length - 1) {
      txt(s, "›", {
        x: x + bw - 0.03, y: BODY_TOP + 1.05, w: 0.18, h: 0.4, fontSize: 18, bold: true,
        color: C.grey, fontFace: F.body, align: "center",
      });
    }
  });
  const kk = [
    ["The holdout is not optional", "Defined before the send or the lift number is a story, not a measurement. Ten percent held back by default, agreed per cohort."],
    ["The write back closes the loop", "Campaign, Touch and Response become graph nodes, so the next cycle's targeting trains on what actually worked, not on what was planned."],
  ];
  kk.forEach((k, i) => {
    const x = M + i * 6.25;
    s.addShape(pres.ShapeType.rect, { x, y: 4.36, w: 5.95, h: 1.42, fill: { color: C.ink } });
    marker(s, x + 0.22, 4.58, C.green);
    txt(s, k[0], {
      x: x + 0.48, y: 4.5, w: 5.2, h: 0.3, fontSize: 12, bold: true, color: C.white, fontFace: F.head,
    });
    txt(s, k[1], {
      x: x + 0.48, y: 4.86, w: 5.25, h: 0.8, fontSize: 10, color: "D8DCDA", fontFace: F.body,
      lineSpacingMultiple: 1.08,
    });
  });
  txt(s, "Steps 2 and 3 are the gate. Nothing reaches a channel without passing both, and the agent layer can draft a cohort but cannot open the gate.", {
    x: M, y: 6.02, w: CW, h: 0.3, fontSize: 10.5, italic: true, color: C.grey, fontFace: F.body,
  });
}

/* ================= 14. L7 EVALUATION AND GOVERNANCE ================= */
{
  const s = slide("LAYER 7", "Evaluation and governance: prove it, then keep proving it", "L7", C.green);
  const cols = [
    {
      accent: C.green2, title: "Is the answer right?",
      lines: [
        "Gold set of 100 plus SME labelled questions, the method carried straight from Solution 1.",
        "LLM as a judge scoring, with a human spot audit on a fixed sample.",
        "Clinical SME review of flagged providers before any gap is published.",
        "Match rate and coverage dashboards, read before the gap list is read.",
        "Before and after agent accuracy, on the same gold set.",
      ],
    },
    {
      accent: C.navy, title: "Did the campaign move it?",
      lines: [
        "Holdout lift on one primary metric named at cohort build.",
        "Guardrail metrics tracked alongside: opt out rate, complaint rate, provider abrasion.",
        "Attribution window fixed in advance and not adjusted after the result is known.",
        "A scorecard per cohort, kept whether the result was good or bad.",
      ],
    },
    {
      accent: C.red, title: "Is it legal and audited?",
      lines: [
        "HIPAA minimum necessary enforced at the query layer, not by convention.",
        "Role based access to subgraphs, so a user sees the slice their role permits.",
        "De-identification for analytic use, re-identification only through a controlled path.",
        "Lineage from every published gap back to source rows.",
        "Retention and purge aligned to policy, and every agent prompt and response retained for audit.",
      ],
    },
  ];
  cols.forEach((c, i) => {
    card(s, Object.assign({ x: M + i * 4.13, y: BODY_TOP, w: 3.85, h: 3.5 }, c, { bodySize: 10.5, titleSize: 13.5 }));
  });
  note(s, 5.36, "The evaluation framework is the reusable asset. Solution 1 built it for seller agents. Solution 2 inherits it and adds campaign lift to it, and Solution 3 will inherit both.", C.green);
  txt(s, "Every milestone gate in the delivery plan is evidence produced by this layer. No gate is passed on opinion.", {
    x: M, y: 6.1, w: CW, h: 0.3, fontSize: 11, italic: true, color: C.grey, fontFace: F.body,
  });
}

/* ================= 15. WORKED EXAMPLE ================= */
{
  const s = slide("END TO END", "One question, walked through all eight layers", "WORKED EXAMPLE", C.green);
  txt(s, "Illustrative. The shape of the analysis is real, the figures are placeholders until the source inventory at M0.", {
    x: M, y: BODY_TOP, w: CW, h: 0.3, fontSize: 10.5, italic: true, color: C.grey, fontFace: F.body,
  });
  const steps = [
    ["L0 · L1", "128,000 attributed patients and 41 contracted cardiologists in the county resolve at 96 percent patient match and 94 percent provider match. Both rates are published with the result."],
    ["L2", "Patients, encounters, providers, practices, facilities and the cardiology service line are linked and SHACL validated. Twelve practices and seven facilities carry the volume."],
    ["L3", "Inflow index for the county sits in the top decile. The risk adjusted outcome index is 1.18 observed over expected, and the interval excludes 1.0, so the difference is real."],
    ["L4", "Supply deficit is seven full time equivalents. Leakage is 23 percent of referrals leaving the network. The county lands in the PRIORITY quadrant and ranks first on gap score."],
    ["L5", "The Market POV agent answers the quarterly question with the county, the twelve practices, the interval and a link back to the encounters behind every number."],
    ["L6", "Two cohorts leave the gate: twelve practices for contracting and quality outreach, and 4,100 patients with open measures, ten percent held back as control."],
    ["L7", "Lift measured against the holdout at ninety days. SME sign off recorded before send. The whole chain replays from the source rows on request."],
  ];
  steps.forEach((st, i) => {
    const y = 2.0 + i * 0.615;
    s.addShape(pres.ShapeType.rect, { x: M, y, w: CW, h: 0.55, fill: { color: i % 2 ? C.panel : C.panel2 } });
    s.addShape(pres.ShapeType.rect, { x: M, y, w: 1.08, h: 0.55, fill: { color: i < 2 ? C.grey : (i < 4 ? C.navy : (i < 6 ? C.green2 : C.red)) } });
    txt(s, st[0], {
      x: M, y, w: 1.08, h: 0.55, fontSize: 10.5, bold: true, color: C.white, fontFace: F.head,
      align: "center", valign: "middle",
    });
    txt(s, st[1], {
      x: M + 1.28, y, w: CW - 1.5, h: 0.55, fontSize: 10.5, color: C.ink2, fontFace: F.body, valign: "middle",
    });
  });
  note(s, 6.3, "Harris County cardiology, first in the ranked list. The same query produces the next forty rows, and the GROW quadrant says where the steered volume should go.", C.green);
}

/* ================= 16. RISKS ================= */
{
  const s = slide("HONEST RISKS", "What would make this wrong, and what stops it", "GUARDRAILS", C.red);
  const risks = [
    ["Confounding", "Outcome differences that are really case mix differences.", "Risk adjustment, matched peer groups, published intervals"],
    ["Small denominators", "A provider with two patients looks catastrophic or perfect.", "Minimum volume floor plus empirical Bayes shrinkage"],
    ["Data lag", "Claims run 30 to 90 days behind, so a gap may already be closed.", "Dated indices, and the lag stated on every answer"],
    ["Attribution disputes", "Two parties both claim, or both disclaim, the same patient.", "One versioned rule per service line, agreed before build"],
    ["Identity failure", "A join failure that looks exactly like a business gap.", "Match rate published next to every gap, every time"],
    ["Provider abrasion", "Naming clinicians creates legal and relationship exposure.", "Internal only ranking, review gate, no public league table"],
    ["PHI exposure", "Patient detail reaching a model endpoint or an unapproved channel.", "BAA covered endpoints, de-identified by default, consent gate"],
    ["Campaign fatigue", "The same cohort contacted by three teams in one month.", "Suppression list and contact frequency caps in the graph"],
  ];
  risks.forEach((r, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * 6.25, y = BODY_TOP + row * 1.2;
    s.addShape(pres.ShapeType.rect, { x, y, w: 5.95, h: 1.06, fill: { color: C.panel } });
    marker(s, x + 0.22, y + 0.24, C.red);
    txt(s, r[0], {
      x: x + 0.48, y: y + 0.15, w: 2.2, h: 0.28, fontSize: 12, bold: true, color: C.ink2, fontFace: F.head,
    });
    txt(s, r[1], {
      x: x + 0.48, y: y + 0.44, w: 5.2, h: 0.28, fontSize: 9.5, color: C.grey, fontFace: F.body,
    });
    txt(s, r[2], {
      x: x + 0.48, y: y + 0.72, w: 5.2, h: 0.28, fontSize: 9.5, bold: true, color: C.green2, fontFace: F.body,
    });
  });
  txt(s, "Every one of these is a design decision taken before build, not a caveat added after the first review.", {
    x: M, y: 6.5, w: CW, h: 0.3, fontSize: 11, italic: true, color: C.grey, fontFace: F.body,
  });
}

/* ================= 17. DELIVERY PLAN ================= */
{
  const s = slide("DELIVERY", "Four months, five evidence gates", "PLAN", C.green);
  const ms = [
    ["M0", "Weeks 1 to 3", "Foundation", "Source inventory, attribution and peer group rules agreed, ontology draft, identity baseline", "GATE: match rate at or above the agreed floor, attribution rule signed"],
    ["M1", "Weeks 4 to 7", "Graph and signals", "Ontology loaded with SHACL, care subgraph at production scale, indices as traversals", "GATE: index parity with the analytics team's own numbers, inside tolerance"],
    ["M2", "Weeks 8 to 11", "Gap engines", "Six gap engines, the quadrant, statistical guardrails and lineage", "GATE: clinical SME review of a flagged sample, shrinkage and intervals validated"],
    ["M3", "Weeks 12 to 14", "Agents and eval", "GraphRAG retrieval, three agents in Agentforce and Slack via MCP, gold set baseline", "GATE: accuracy at or above the agreed baseline on the gold set"],
    ["M4", "Weeks 15 to 17", "Activation", "Cohort builder, consent gate, holdout design, write back, first campaign in flight", "GATE: holdout defined pre send, compliance sign off, scorecard live"],
  ];
  const bw = 2.42, gp = 0.12;
  ms.forEach((m, i) => {
    const x = M + i * (bw + gp);
    const accent = [C.grey, C.navy, C.navy, C.green2, C.red][i];
    s.addShape(pres.ShapeType.rect, { x, y: BODY_TOP, w: bw, h: 0.56, fill: { color: accent } });
    txt(s, m[0], {
      x: x + 0.14, y: BODY_TOP, w: 0.7, h: 0.56, fontSize: 15, bold: true, color: C.white,
      fontFace: F.head, valign: "middle",
    });
    txt(s, m[1], {
      x: x + 0.8, y: BODY_TOP, w: bw - 0.92, h: 0.56, fontSize: 9.5, color: C.white,
      fontFace: F.body, align: "right", valign: "middle",
    });
    s.addShape(pres.ShapeType.rect, { x, y: BODY_TOP + 0.56, w: bw, h: 2.5, fill: { color: C.panel } });
    txt(s, m[2], {
      x: x + 0.16, y: BODY_TOP + 0.7, w: bw - 0.32, h: 0.3, fontSize: 12, bold: true, color: C.ink2, fontFace: F.head,
    });
    txt(s, m[3], {
      x: x + 0.16, y: BODY_TOP + 1.06, w: bw - 0.32, h: 1.9, fontSize: 9.5, color: C.ink2,
      fontFace: F.body, lineSpacingMultiple: 1.08,
    });
    s.addShape(pres.ShapeType.rect, { x, y: BODY_TOP + 3.14, w: bw, h: 1.18, fill: { color: C.ink } });
    txt(s, m[4], {
      x: x + 0.16, y: BODY_TOP + 3.24, w: bw - 0.32, h: 1.0, fontSize: 9, bold: true,
      color: C.green, fontFace: F.body, lineSpacingMultiple: 1.08,
    });
  });
  note(s, 6.28, "Gates are evidence, not opinion, which is what de-risked the first engagement. A gate that cannot be evidenced moves the date rather than the standard.", C.green);
}

/* ================= 18. CLOSE ================= */
{
  const s = pres.addSlide();
  s.background = { color: C.ink };
  s.addShape(pres.ShapeType.ellipse, {
    x: 11.55, y: 0.12, w: 2.7, h: 2.7, fill: { color: C.navy, transparency: 55 },
  });
  txt(s, "WHAT YOU GET, AND WHAT WE NEED TO DECIDE", {
    x: M, y: 0.62, w: 9.0, h: 0.3, fontSize: 11, bold: true, charSpacing: 2, color: C.green, fontFace: F.body,
  });
  txt(s, "Yes, we can do it on the same graph. Here is what it returns.", {
    x: M, y: 1.02, w: 10.6, h: 0.9, fontSize: 26, bold: true, color: C.white, fontFace: F.head,
  });
  const outs = [
    "A ranked, lineage backed gap list that survives a contracting conversation",
    "Agents that answer market and provider questions with node level citations",
    "Campaigns whose lift is measured against a holdout, not asserted",
    "One more use case proving the graph, with the evaluation asset reused not rebuilt",
  ];
  s.addShape(pres.ShapeType.rect, { x: M, y: 2.2, w: 6.05, h: 2.78, fill: { color: "16161C" } });
  marker(s, M + 0.26, 2.46, C.green);
  txt(s, "Outcomes", {
    x: M + 0.54, y: 2.38, w: 4.0, h: 0.3, fontSize: 14, bold: true, color: C.white, fontFace: F.head,
  });
  s.addText(
    outs.map((t, i) => ({
      text: t,
      options: { bullet: { characterCode: "2713" }, breakLine: i < outs.length - 1, paraSpaceAfter: 11 },
    })),
    {
      isTextBox: true, x: M + 0.54, y: 2.82, w: 5.2, h: 2.2, margin: 0, fontSize: 11,
      color: "D8DCDA", fontFace: F.body, valign: "top", lineSpacingMultiple: 1.06,
    }
  );
  const qs = [
    "Who owns the attribution rule, and by when?",
    "Risk model: buy the standard grouper or build internally?",
    "Which model endpoints are BAA covered today?",
    "Which system is the consent store of record?",
    "Who signs off a cohort before it is sent?",
    "What is the policy on naming individual clinicians internally?",
  ];
  s.addShape(pres.ShapeType.rect, { x: 6.9, y: 2.2, w: 5.88, h: 2.78, fill: { color: "16161C" } });
  marker(s, 7.16, 2.46, C.red);
  txt(s, "Open questions for week one", {
    x: 7.44, y: 2.38, w: 5.0, h: 0.3, fontSize: 14, bold: true, color: C.white, fontFace: F.head,
  });
  s.addText(
    qs.map((t, i) => ({
      text: t,
      options: { bullet: { characterCode: "25AA" }, breakLine: i < qs.length - 1, paraSpaceAfter: 7 },
    })),
    {
      isTextBox: true, x: 7.44, y: 2.82, w: 5.1, h: 2.2, margin: 0, fontSize: 11,
      color: "D8DCDA", fontFace: F.body, valign: "top", lineSpacingMultiple: 1.06,
    }
  );
  s.addShape(pres.ShapeType.rect, { x: M, y: 5.34, w: CW, h: 0.02, fill: { color: "3A3A42" } });
  txt(s, "InsightGlobal", {
    x: M, y: 5.56, w: 3.0, h: 0.3, fontSize: 13, bold: true, color: C.white, fontFace: F.head,
  });
  txt(s, "Connect with your IG partner directly or at insightglobal.com.", {
    x: 4.2, y: 5.58, w: 5.6, h: 0.3, fontSize: 10.5, color: "8A8F8C", fontFace: F.body,
  });
  txt(s, "© 2026 Insight Global", {
    x: 10.0, y: 5.58, w: 2.78, h: 0.3, fontSize: 10.5, color: "8A8F8C", fontFace: F.body, align: "right",
  });
  footer(s, true);
}

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
