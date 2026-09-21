/* Clinical Network Knowledge Graph: concept deck.
   Type: Trenda IG Display / Trenda IG Text (each weight is its own Windows family).
   4 slides: nine layer architecture, scenario catalogue, graph model, feasibility. */

const pptxgen = require("pptxgenjs");
const path = require("path");
const OUT = process.argv[2] || path.join(__dirname, "network-graph.pptx");

const C = {
  l1: "1B6BC0", l2: "0E8A7D", l3: "6A1B9A", l4: "7A4FC0", l5: "C2185B",
  l6: "C77400", l7: "C62828", l8: "2E7D32", l9: "00757F",
  ink: "0E1B2E", ink2: "16202C", text: "1A1A1A", grey: "5A6573",
  rule: "D5D9DE", panel: "F4F6F9", white: "FFFFFF", mint: "5FD0C0",
};
/* Trenda ships each weight as a separate family name, so weight is selected by
   face rather than by the bold flag. Never set bold on these or PowerPoint
   synthesises a second, fake bold on top. */
const F = {
  dsp: "Trenda IG Display",
  dspSemi: "Trenda IG Display Semibold",
  dspBold: "Trenda IG Display Bold",
  dspHeavy: "Trenda IG Display Heavy",
  txt: "Trenda IG Text",
  txtLight: "Trenda IG Text Light",
  txtSemi: "Trenda IG Text Semibold",
  txtBold: "Trenda IG Text Bold",
  mono: "Courier New",
};

const W = 13.33, H = 7.5;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Insight Global Labs";
pres.title = "Clinical Network Knowledge Graph";

function txt(s, t, o) {
  s.addText(t, Object.assign({ isTextBox: true, margin: 0, valign: "top" }, o));
}
function box(s, x, y, w, h, fill, line) {
  s.addShape(pres.ShapeType.rect, Object.assign(
    { x, y, w, h, fill: { color: fill } },
    line ? { line: { color: line, width: 0.75 } } : {}
  ));
}
function dot(s, x, y, color, size) {
  const d = size || 0.09;
  s.addShape(pres.ShapeType.rect, { x, y, w: d, h: d, fill: { color } });
}
function bullets(s, items, o) {
  s.addText(items.map((t, i) => ({
    text: t,
    options: {
      bullet: o.bulletIndent
        ? { characterCode: "2022", indent: o.bulletIndent }
        : { characterCode: "2022" },
      breakLine: i < items.length - 1,
      paraSpaceAfter: o.gap === undefined ? 2 : o.gap,
    },
  })), Object.assign({ isTextBox: true, margin: 0, valign: "top" }, o));
}

/* ---- real Trenda metrics, so the poster can size itself ---- */
const WD = require(require("path").join(__dirname, "trenda-widths.json"));
function faceOf(f) { return WD[f] ? f : "Trenda IG Text"; }
function textW(str, face, pt) {
  const m = WD[faceOf(face)];
  let em = 0;
  for (const ch of str) em += m.widths[ch] !== undefined ? m.widths[ch] : m.default;
  return em * pt / 72;
}
function lineH(face, pt, mult) {
  return WD[faceOf(face)].lineHeight * pt / 72 * (mult === undefined ? 1 : mult);
}
/* greedy wrap, same rule PowerPoint uses */
function nLines(str, face, pt, wIn) {
  const sp = textW(" ", face, pt);
  let n = 1, cur = 0;
  for (const word of str.split(" ")) {
    const ww = textW(word, face, pt);
    if (ww > wIn) {                 // PowerPoint breaks mid-token
      if (cur > 0) n += 1;
      n += Math.ceil(ww / wIn) - 1;
      cur = ww % wIn;
    } else if (cur === 0) cur = ww;
    else if (cur + sp + ww <= wIn) cur += sp + ww;
    else { n += 1; cur = ww; }
  }
  return n;
}

/* ==================== SLIDE 1: NINE LAYER ARCHITECTURE ==================== */
const s1 = pres.addSlide();
s1.background = { color: C.white };
const M = 0.12;

/* ---- top band ---- */
box(s1, M, 0.07, 3.5, 0.67, C.white, C.rule);
txt(s1, "SEVEN AUTHORITATIVE SOURCES", {
  x: M + 0.11, y: 0.13, w: 3.3, h: 0.19, fontSize: 9.5, charSpacing: 0.5,
  color: C.l1, fontFace: F.dspBold,
});
txt(s1, "EHR  ·  Credentialing  ·  Directory  ·  Scheduling  ·  Claims  ·  Referrals  ·  Geography", {
  x: M + 0.11, y: 0.32, w: 3.3, h: 0.26, fontSize: 7.5, color: C.text, fontFace: F.txtSemi,
  lineSpacingMultiple: 1.0,
});
txt(s1, "read only  ·  tokenised at the boundary  ·  provenance tagged", {
  x: M + 0.11, y: 0.585, w: 3.3, h: 0.15, fontSize: 7, color: C.grey, fontFace: F.txtLight,
});

box(s1, 3.78, 0.07, 5.72, 0.67, C.ink);
txt(s1, "PROVIDER, FACILITY AND PATIENT DEMAND", {
  x: 3.88, y: 0.12, w: 5.52, h: 0.25, fontSize: 14.5, color: C.white,
  fontFace: F.dspBold, align: "center",
});
txt(s1, "Clinical Network Knowledge Graph Architecture", {
  x: 3.88, y: 0.36, w: 5.52, h: 0.2, fontSize: 10, color: C.mint,
  fontFace: F.dspSemi, align: "center",
});
txt(s1, "sources → connectors → privacy boundary → identity → domain model → storage → derived edges → graph → gap engines", {
  x: 3.88, y: 0.57, w: 5.52, h: 0.15, fontSize: 6.2, color: "A9B4C2",
  fontFace: F.txt, align: "center",
});

box(s1, 9.62, 0.07, 3.59, 0.67, C.white, C.rule);
txt(s1, "WHAT THE GRAPH ANSWERS", {
  x: 9.73, y: 0.13, w: 3.4, h: 0.19, fontSize: 9.5, charSpacing: 0.5,
  color: C.l8, fontFace: F.dspBold,
});
txt(s1, "Where demand has no provider  ·  where a provider has no demand  ·  where capability and credential do not meet  ·  where patients leave", {
  x: 9.73, y: 0.34, w: 3.38, h: 0.24, fontSize: 7, color: C.text,
  fontFace: F.txt, lineSpacingMultiple: 1.02,
});
txt(s1, "The missing edge is the answer", {
  x: 9.73, y: 0.57, w: 3.38, h: 0.15, fontSize: 7, color: C.l8, fontFace: F.txtSemi,
});

/* ---- nine layers ---- */
const COLW = 1.41, STEP = 1.46;
const HDR_Y = 0.78, HDR_H = 0.68;
const BODY_Y = 1.48, BODY_BOT = 6.22, WYG_H = 0.50;

const layers = [
  {
    c: C.l1, n: "LAYER 1", t: "Source Systems", cap: "Systems of record",
    wyg: "Every network fact in one place",
    secs: [
      ["EHR and clinical", ["Encounters and diagnoses", "ADT admit and discharge", "Orders, results, problems"]],
      ["Credentialing", ["Licence and board certs", "Privileges by procedure", "Expirables and sanctions"]],
      ["Directory and MDM", ["Individual and org NPI", "NUCC taxonomy and sub", "Locations, TIN, panel"]],
      ["Scheduling and access", ["Templates and sessions", "Booked against bookable", "Third next available"]],
      ["Claims, referrals, geo", ["CPT, ICD-10, place of service", "Referring to receiving", "Drive time and tracts"]],
    ],
  },
  {
    c: C.l2, n: "LAYER 2", t: "Source Connectors", cap: "Read only and replayable",
    wyg: "Safe, repeatable reads. No writes anywhere",
    secs: [
      ["Clinical connectors", ["FHIR R4 and HL7 v2", "Bulk export, ADT stream", "Read only accounts"]],
      ["Workforce connectors", ["Credentialing delta", "NPPES weekly, MDM API", "Taxonomy version pinned"]],
      ["Operational connectors", ["Slot and template API", "Nightly bookable snapshot", "837 and 835 monthly"]],
      ["Connector contract", ["No writes, ever", "SHA-256 per record", "Replay by extract id"]],
      ["Failure handling", ["Partial pull discarded", "Late file supersedes", "Every run leaves a receipt"]],
    ],
  },
  {
    c: C.l3, n: "LAYER 3", t: "Trust and Privacy Boundary", cap: "Nothing crosses identified",
    wyg: "PHI never crosses the line in identifiable form",
    secs: [
      ["De-identify at ingress", ["Safe Harbor identifiers out", "MRN to HMAC token", "Dates shifted per patient"]],
      ["Three data planes", ["Analytic: k-anonymous", "Operational: LDS, BAA", "Identified: break glass"]],
      ["Keys and crypto", ["KMS or HSM held keys", "Envelope per snapshot", "TLS 1.3, AES-256 at rest"]],
      ["Re-identification defence", ["k-anonymity floor per cell", "Rare plus small suppressed", "Query budget per user"]],
      ["Assurance", ["HIPAA, HITRUST, SOC 2", "Immutable WORM audit", "Quarterly re-id review"]],
    ],
  },
  {
    c: C.l4, n: "LAYER 4", t: "Ingest and Identity", cap: "Resolve, reconcile, prove",
    wyg: "One patient, one provider, one place, with the proof",
    secs: [
      ["Parse and normalise", ["FHIR to domain objects", "ICD-10, CPT, SNOMED", "Taxonomy to specialty"]],
      ["Patient identity, EMPI", ["Deterministic on token", "Probabilistic, reviewed", "Links stay reversible"]],
      ["Provider and place", ["NPI is the person", "TIN plus NPI is practice", "CCN is the facility"]],
      ["Conflict resolution", ["Precedence per attribute", "Losing value retained", "Confidence on every link"]],
      ["Provenance", ["Source, extract, hash", "FACTUAL or INFERRED"]],
    ],
  },
  {
    c: C.l5, n: "LAYER 5", t: "Domain Model", cap: "CareNetworkContext",
    wyg: "A typed, bitemporal model of the network",
    secs: [
      ["Entities", ["providers[], facilities[]", "serviceLines[], capabilities[]", "geographies[], payers[]"]],
      ["Relationship objects", ["Affiliation, Privilege", "Coverage, Referral", "Attribution, Contract"]],
      ["Service line spec", ["requiredSpecialties[]", "requiredCapabilities[]", "coverageWindow, minVolume"]],
      ["Demand and access", ["patients, encounters, trend", "acuityMix, payerMix", "slots, thirdNextAvailable"]],
      ["Bitemporal by default", ["validFrom, validTo", "recordedAt, supersededAt"]],
    ],
  },
  {
    c: C.l6, n: "LAYER 6", t: "Graph Storage", cap: "Bitemporal and immutable",
    json: [
      '{ "snapshot": "sha256:7c41\u2026",',
      '  "nodes": [',
      '   {"id": "prv:9f2a\u2026",',
      '    "type": "PROVIDER",',
      '    "spec": "CARDIOLOGY",',
      '    "fte": 0.6, "panel": "OPEN"}],',
      '  "edges": [',
      '   {"id": "cov:41b7\u2026",',
      '    "type": "COVERS",',
      '    "from": "prv:9f2a\u2026",',
      '    "to": "svc:CARD@450214",',
      '    "validFrom": "2024-07-01",',
      '    "validTo": null,',
      '    "recordedAt": "2026-08-02",',
      '    "confidence": 0.92,',
      '    "evidence": ["caqh:8821#r44"]',
      '   }] }',
    ],
    wyg: "Any past state of the network, replayed exactly",
    secs: [
      ["What the file holds", ["Every node and edge typed", "Two time axes per edge", "Confidence and evidence", "Tokens only, no ids"]],
      ["Storage rules", ["Content addressed", "Rebuilt, never written back", "Encrypted per snapshot"]],
    ],
  },
  {
    c: C.l7, n: "LAYER 7", t: "Derived Edge Engine", cap: "A gap becomes a number",
    wyg: "The missing edge becomes a defensible number",
    secs: [
      ["Derived edges", ["SERVES geo to site", "REQUIRES line to specialty", "COVERS provider to line", "SUBSTITUTE_FOR pairs"]],
      ["Constraint evaluation", ["Spec run against graph", "Unsatisfied means a gap", "New line is a spec row"]],
      ["Indices", ["inflow, capacity, coverage", "leakage, adequacy, depth", "outcome O over E, shrunk", "concentration and SPOF"]],
      ["Guardrails", ["Minimum volume to rank", "Peer group by case mix", "Interval with every value"]],
    ],
  },
  {
    c: C.l8, n: "LAYER 8", t: "Network ContextGraph", cap: "Traversals and what-if",
    wyg: "Gap, blast radius and what-if in under a second",
    secs: [
      ["Graph runtime", ["Typed nodes and edges", "Weights: time, volume", "As-of views on any date"]],
      ["Traversals", ["coverage_path(geo, svc)", "missing_edge(dmd, sup)", "blast_radius(prv)", "k_nearest(geo, k)"]],
      ["Vector plane", ["Embeddings per type", "Substitutability search", "Anchor symbolic, rank vector"]],
      ["Shadow graph", ["Copy on write namespace", "Insert hypothetical nodes", "Diff against base"]],
      ["Analytics", ["Centrality, components", "Referral communities", "Set cover: fewest hires"]],
    ],
  },
  {
    c: C.l9, n: "LAYER 9", t: "Gap Engines and API", cap: "Twelve scenarios, one engine",
    wyg: "Ranked, explainable gaps with the action attached",
    secs: [
      ["Gap engines", ["access_gap()", "idle_supply_gap()", "credential_gap()", "line_completeness()", "leakage_gap()", "adequacy_gap()", "failure_point()"]],
      ["Query API", ["graph.query, gap.rank", "whatif.simulate", "cohort.build, asof(date)"]],
      ["Policy at query time", ["Purpose of use required", "Minimum necessary compiled", "k-anonymity pre-return"]],
      ["Output contract", ["Ranked gap, evidence path", "Patients and volume", "Action, owner, cohort"]],
    ],
  },
];

/* Pick the largest uniform body size at which all nine columns still fit.
   This is what "use the space we have" means in practice. */
const PAD = 0.08, BULLET_IND = 0.1;
const HDR_W = COLW - 0.19 - 0.07;          // section header text width
const BUL_W = COLW - PAD - 0.03 - BULLET_IND;  // bullet text width
const AVAIL = (BODY_BOT - WYG_H) - BODY_Y - 0.14;

function colHeight(L, bodyPt) {
  const hdrPt = bodyPt + 1;
  let h = 0;
  if (L.json) h += lineH(F.dspBold, hdrPt) + 0.05 + 1.42 + 0.12;
  L.secs.forEach((sec) => {
    h += nLines(sec[0], F.dspBold, hdrPt, HDR_W) * lineH(F.dspBold, hdrPt) + 0.05;
    sec[1].forEach((b) => {
      h += nLines(b, F.txt, bodyPt, BUL_W) * lineH(F.txt, bodyPt, 0.98) + 1.5 / 72;
    });
    h += 0.07;
  });
  return h;
}
let BODY_PT = 6.0;
for (let t = 9.0; t >= 6.0; t -= 0.25) {
  if (layers.every((L) => colHeight(L, t) <= AVAIL)) { BODY_PT = t; break; }
}
const HDR_PT = BODY_PT + 1;
console.log("poster body size chosen:", BODY_PT + "pt, section headers " + HDR_PT + "pt");
layers.forEach((L) => {
  const slack = (AVAIL - colHeight(L, BODY_PT)).toFixed(2);
  if (slack < 0) console.log("  OVER  " + L.t + " by " + (-slack));
});

layers.forEach((L, i) => {
  const x = M + i * STEP;
  box(s1, x, HDR_Y, COLW, HDR_H, L.c);
  txt(s1, L.n, {
    x: x + 0.05, y: HDR_Y + 0.05, w: COLW - 0.1, h: 0.15, fontSize: 7.5,
    charSpacing: 0.4, color: "FFFFFF", fontFace: F.dspSemi, align: "center",
  });
  txt(s1, L.t, {
    x: x + 0.04, y: HDR_Y + 0.19, w: COLW - 0.08, h: 0.36, fontSize: 10,
    color: "FFFFFF", fontFace: F.dspBold, align: "center", lineSpacingMultiple: 0.92,
  });
  txt(s1, L.cap, {
    x: x + 0.05, y: HDR_Y + 0.52, w: COLW - 0.1, h: 0.15, fontSize: 6.5,
    color: "E4EEF2", fontFace: F.txtLight, align: "center",
  });
  box(s1, x, BODY_Y, COLW, BODY_BOT - BODY_Y, C.white, C.rule);

  let cy = BODY_Y + 0.09;
  if (L.json) {
    txt(s1, "network.json (excerpt)", {
      x: x + PAD, y: cy, w: COLW - PAD * 2, h: lineH(F.dspBold, HDR_PT),
      fontSize: HDR_PT, color: L.c, fontFace: F.dspBold,
    });
    cy += lineH(F.dspBold, HDR_PT) + 0.05;
    box(s1, x + 0.05, cy, COLW - 0.1, 1.42, C.panel, C.rule);
    txt(s1, L.json.join("\n"), {
      x: x + 0.09, y: cy + 0.05, w: COLW - 0.18, h: 1.34, fontSize: 4.5,
      color: C.text, fontFace: F.mono, lineSpacingMultiple: 1.0,
    });
    cy += 1.42 + 0.12;
  }
  L.secs.forEach((sec) => {
    const hl = nLines(sec[0], F.dspBold, HDR_PT, HDR_W);
    dot(s1, x + PAD, cy + 0.035, L.c, 0.07);
    txt(s1, sec[0], {
      x: x + 0.19, y: cy, w: HDR_W, h: hl * lineH(F.dspBold, HDR_PT) + 0.02,
      fontSize: HDR_PT, color: L.c, fontFace: F.dspBold, lineSpacingMultiple: 0.98,
    });
    cy += hl * lineH(F.dspBold, HDR_PT) + 0.05;
    let bh = 0;
    sec[1].forEach((b) => {
      bh += nLines(b, F.txt, BODY_PT, BUL_W) * lineH(F.txt, BODY_PT, 0.98) + 1.5 / 72;
    });
    bullets(s1, sec[1], {
      x: x + PAD, y: cy, w: COLW - PAD - 0.03, h: bh + 0.04,
      fontSize: BODY_PT, color: C.text, fontFace: F.txt, gap: 1.5,
      lineSpacingMultiple: 0.98, bulletIndent: BULLET_IND * 72,
    });
    cy += bh + 0.07;
  });

  box(s1, x, BODY_BOT - WYG_H, COLW, WYG_H, L.c);
  txt(s1, "WHAT YOU GET", {
    x: x + PAD, y: BODY_BOT - WYG_H + 0.05, w: COLW - 0.16, h: 0.14, fontSize: 6.5,
    charSpacing: 0.4, color: "CFE6EE", fontFace: F.txtSemi,
  });
  txt(s1, L.wyg, {
    x: x + PAD, y: BODY_BOT - WYG_H + 0.19, w: COLW - 0.16, h: 0.3, fontSize: 7,
    color: "FFFFFF", fontFace: F.txtSemi, lineSpacingMultiple: 0.97,
  });
  if (i < layers.length - 1) {
    txt(s1, "\u25B6", {
      x: x + COLW - 0.002, y: HDR_Y + 0.22, w: 0.054, h: 0.14, fontSize: 4.5,
      color: "9AA4B0", fontFace: F.txt, align: "center",
    });
  }
});

/* ---- handoff row ---- */
txt(s1, "HANDOFF\nBETWEEN LAYERS", {
  x: M, y: 6.28, w: 1.0, h: 0.28, fontSize: 6, color: C.grey,
  fontFace: F.txtSemi, lineSpacingMultiple: 0.95,
});
const hand = [
  ["read only API pull", C.l1],
  ["bytes plus content hash", C.l2],
  ["tokenised, de-identified", C.l3],
  ["resolved entities, provenance", C.l4],
  ["typed CareNetworkContext", C.l5],
  ["immutable JSON snapshot", C.l6],
  ["derived edges, dated indices", C.l7],
  ["graph loaded, traversals ready", C.l8],
];
hand.forEach((h, i) => {
  const x = 1.19 + i * 1.5075;
  box(s1, x, 6.28, 1.45, 0.28, C.white, C.rule);
  dot(s1, x + 0.07, 6.38, h[1], 0.07);
  txt(s1, h[0], {
    x: x + 0.17, y: 6.28, w: 1.24, h: 0.28, fontSize: 6.3, color: C.text,
    fontFace: F.txt, valign: "middle",
  });
});

/* ---- bottom panels ---- */
const bots = [
  [C.l4, "Provenance and authority",
    "Every node and edge carries source, extract id, content hash, retrievedAt and derivation: FACTUAL, INFERRED or MODELLED. Authority stays with the source system. The graph never becomes the system of record for a clinical fact."],
  [C.l3, "Threat model, and the control for each",
    "Re-identification from rare attribute combinations: k-anonymity at the query compiler. Insider browsing: purpose of use required per query. PHI reaching a model: aggregates unless BAA covered. Vendor sprawl: no copies leave the boundary."],
  [C.l1, "Audit and traceability",
    "Every gap resolves back to the source rows that produced it. Every query, answer and cohort is logged with user, purpose, timestamp, snapshot id and the evidence path returned. A gap that cannot be replayed is not published."],
  [C.l8, "Scope of the proof",
    "One market, two service lines, ninety days. Build order: privacy boundary, then identity, then graph, then two gap engines, then one what-if. Success is a gap list a clinical leader and a network leader both sign."],
];
bots.forEach((b, i) => {
  const x = M + i * 3.2925;
  box(s1, x, 6.64, 3.2125, 0.79, C.white, C.rule);
  dot(s1, x + 0.1, 6.74, b[0], 0.085);
  txt(s1, b[1], {
    x: x + 0.24, y: 6.70, w: 2.88, h: 0.17, fontSize: 8, color: b[0], fontFace: F.dspBold,
  });
  txt(s1, b[2], {
    x: x + 0.1, y: 6.90, w: 3.03, h: 0.5, fontSize: 6.8, color: C.text,
    fontFace: F.txt, lineSpacingMultiple: 1.0,
  });
});

/* ==================== SLIDE 2: SCENARIO CATALOGUE ==================== */
const s2 = pres.addSlide();
s2.background = { color: C.white };
box(s2, 0, 0, W, 0.95, C.ink);
txt(s2, "TWELVE SCENARIOS, ONE ENGINE", {
  x: 0.5, y: 0.15, w: 8.0, h: 0.21, fontSize: 10.5, charSpacing: 1.2,
  color: C.mint, fontFace: F.dspSemi,
});
txt(s2, "What the provider, facility and patient graph answers", {
  x: 0.5, y: 0.4, w: 9.0, h: 0.38, fontSize: 22, color: C.white, fontFace: F.dspBold,
});
txt(s2, "Every scenario is the same query shape:\nthe demand path exists, the supply path does not.", {
  x: 9.75, y: 0.24, w: 3.1, h: 0.5, fontSize: 9, color: "A9B4C2",
  fontFace: F.txtLight, lineSpacingMultiple: 1.08,
});

const fams = [
  ["A  ·  SUPPLY AND DEMAND MISMATCH", C.l1],
  ["B  ·  NETWORK COMPLETENESS", C.l5],
  ["C  ·  PATIENT FLOW", C.l6],
  ["D  ·  ACCESS, QUALITY AND GROWTH", C.l8],
];
const scen = [
  [
    ["1  Demand without supply", "Geography has inflow for a service line and no credentialed provider inside the drive time band", "Recruit, locum, telehealth or a transfer agreement"],
    ["2  Supply without demand", "Sessions and slots exist, encounter volume sits in the bottom decile for the peer group", "Redeploy sessions, re-market, resize the template"],
    ["3  Capability and credential mismatch", "The site holds the asset, cath lab, MRI, labour and delivery, with nobody privileged to use it", "Privilege, credential, or move the asset"],
  ],
  [
    ["4  Incomplete service line", "The line requires N specialties and the site has N minus one, so care finishes somewhere else", "Close the one gap that unlocks the whole line"],
    ["5  Single point of failure", "One provider is the only path to a service line in a county, and the graph names them", "Succession and cross cover, blast radius quantified"],
    ["6  Volume below threshold", "Complex procedures performed under the safe volume floor for that site or provider", "Consolidate or refer, with the quality risk named"],
  ],
  [
    ["7  Referral leakage", "Attributed patients treated out of network, traced along the actual referral edges", "Recapture campaign that fixes the reason, not the symptom"],
    ["8  Bypass and travel burden", "Patients drive past a nearer site to reach a farther one, repeatedly", "Isolates reputation against capability against access"],
    ["9  Referral chain depth", "Four hops to reach definitive care, every hop measurable in days", "Shorten the path, open a direct access pathway"],
  ],
  [
    ["10  Adequacy and access deserts", "CMS time and distance failures by county and specialty, mapped onto the graph", "Filing evidence, and the fewest hires that fix the most counties"],
    ["11  Inflow high, outcome weak", "Volume in the top decile with risk adjusted O over E above the peer benchmark", "Quality campaign, and steer volume to the strong sites"],
    ["12  Hire and site simulation", "Insert a hypothetical provider or site, re-run every traversal, diff the result", "Patients gaining access and leakage recaptured, before you spend"],
  ],
];
const cw2 = 3.19, cs2 = 3.2925;
fams.forEach((f, ci) => {
  const x = 0.12 + ci * cs2;
  box(s2, x, 1.1, cw2, 0.32, f[1]);
  txt(s2, f[0], {
    x: x + 0.13, y: 1.1, w: cw2 - 0.22, h: 0.32, fontSize: 8.5, charSpacing: 0.4,
    color: C.white, fontFace: F.dspBold, valign: "middle",
  });
  scen[ci].forEach((sc, ri) => {
    const y = 1.52 + ri * 1.75;
    box(s2, x, y, cw2, 1.63, C.panel, C.rule);
    txt(s2, sc[0], {
      x: x + 0.15, y: y + 0.13, w: cw2 - 0.3, h: 0.34, fontSize: 11.5,
      color: C.text, fontFace: F.dspBold, lineSpacingMultiple: 0.95,
    });
    txt(s2, "IN THE GRAPH", {
      x: x + 0.15, y: y + 0.54, w: cw2 - 0.3, h: 0.14, fontSize: 6.2,
      charSpacing: 0.5, color: C.grey, fontFace: F.txtSemi,
    });
    txt(s2, sc[1], {
      x: x + 0.15, y: y + 0.69, w: cw2 - 0.3, h: 0.47, fontSize: 9, color: C.text,
      fontFace: F.txt, lineSpacingMultiple: 1.0,
    });
    dot(s2, x + 0.15, y + 1.22, f[1], 0.075);
    txt(s2, sc[2], {
      x: x + 0.29, y: y + 1.17, w: cw2 - 0.44, h: 0.38, fontSize: 8.6,
      color: f[1], fontFace: F.txtSemi, lineSpacingMultiple: 0.98,
    });
  });
});
box(s2, 0.12, 6.82, W - 0.24, 0.5, C.ink);
dot(s2, 0.3, 7.0, C.mint, 0.1);
txt(s2, "Each scenario returns the same four things: the evidence path, the patients affected, the recommended action, and a cohort ready to activate.", {
  x: 0.5, y: 6.82, w: 12.6, h: 0.5, fontSize: 10.5, color: C.white,
  fontFace: F.txt, valign: "middle",
});

/* ==================== SLIDE 3: THE GRAPH MODEL ==================== */
const s3 = pres.addSlide();
s3.background = { color: C.white };
box(s3, 0, 0, W, 0.95, C.ink);
txt(s3, "THE GRAPH MODEL", {
  x: 0.5, y: 0.15, w: 6.0, h: 0.21, fontSize: 10.5, charSpacing: 1.2,
  color: C.mint, fontFace: F.dspSemi,
});
txt(s3, "Seven decisions that make this more than a provider directory", {
  x: 0.5, y: 0.4, w: 9.6, h: 0.38, fontSize: 22, color: C.white, fontFace: F.dspBold,
});
txt(s3, "Each one is cheap to build in\nand expensive to retrofit.", {
  x: 10.3, y: 0.24, w: 2.6, h: 0.5, fontSize: 9, color: "A9B4C2",
  fontFace: F.txtLight, lineSpacingMultiple: 1.08,
});

const dec = [
  [C.l6, "1", "Bitemporal by default", [
    "Every edge carries two clocks: when it was true in the world, and when we learned it.",
    "Claims arrive ninety days late and credentials move. Without both clocks you cannot tell a real change from a late arrival.",
  ], "Ask what was true in March, and what we believed in March"],
  [C.l5, "2", "Relationships are nodes", [
    "Affiliation, Privilege and Coverage are objects, not plain edges, so each holds its own dates, confidence, evidence and scope.",
    "Other edges can then point at them.",
  ], "A disputed coverage claim keeps both sides"],
  [C.l4, "3", "Assertion plane, evidence plane", [
    "Every assertion resolves to evidence nodes: source, extract, row, hash.",
    "No evidence path means no publication. The rule is enforced by the engine, not by habit.",
  ], "Defensible in a contracting conversation"],
  [C.l7, "4", "Capability algebra", [
    "A service line is a specification: required specialties, required capabilities, coverage window, minimum volume.",
    "Gap detection becomes constraint satisfaction over the graph instead of a library of hand written queries.",
  ], "A new service line is a spec row, not new code"],
  [C.l8, "5", "Symbolic plus vector", [
    "Typed traversal handles the hard constraints. Embeddings handle likeness: who could substitute, which site is comparable.",
    "Anchor symbolically, rank by vector, never the reverse.",
  ], "Similarity never overrules a credential"],
  [C.l2, "6", "Shadow graph for what-if", [
    "Hypothetical providers and sites are written into a copy on write namespace.",
    "Traversals run against base plus shadow and the diff is the answer. The base graph never mutates.",
  ], "Simulate the hire before you fund it"],
  [C.l3, "7", "Private by construction", [
    "Patient nodes are tokenised and degree limited; the cohort is the queryable unit.",
    "A graph is itself a re-identification vector: rare specialty plus rare condition plus small geography identifies a person.",
  ], "k-anonymity in the query compiler, not the dashboard"],
];
const cw3 = 3.1825, cs3 = 3.3025;
dec.forEach((d, i) => {
  const col = i % 4, row = Math.floor(i / 4);
  const x = 0.12 + col * cs3, y = 1.12 + row * 2.72;
  box(s3, x, y, cw3, 2.56, C.panel, C.rule);
  box(s3, x, y, 0.38, 0.38, d[0]);
  txt(s3, d[1], {
    x: x, y: y, w: 0.38, h: 0.38, fontSize: 13, color: C.white,
    fontFace: F.dspBold, align: "center", valign: "middle",
  });
  txt(s3, d[2], {
    x: x + 0.5, y: y + 0.05, w: cw3 - 0.62, h: 0.46, fontSize: 13,
    color: C.text, fontFace: F.dspBold, lineSpacingMultiple: 0.95,
  });
  txt(s3, d[3].join("\n\n"), {
    x: x + 0.18, y: y + 0.58, w: cw3 - 0.36, h: 1.44, fontSize: 9.2, color: C.text,
    fontFace: F.txt, lineSpacingMultiple: 1.02,
  });
  dot(s3, x + 0.18, y + 2.12, d[0], 0.075);
  txt(s3, d[4], {
    x: x + 0.32, y: y + 2.07, w: cw3 - 0.48, h: 0.4, fontSize: 8.8,
    color: d[0], fontFace: F.txtSemi, lineSpacingMultiple: 0.98,
  });
});
/* eighth cell: the summary */
{
  const x = 0.12 + 3 * cs3, y = 1.12 + 1 * 2.72;
  box(s3, x, y, cw3, 2.56, C.ink);
  txt(s3, "Why it has to be this way", {
    x: x + 0.18, y: y + 0.18, w: cw3 - 0.36, h: 0.3, fontSize: 13,
    color: C.mint, fontFace: F.dspBold,
  });
  bullets(s3, [
    "A directory tells you who exists. This tells you what is missing, and proves it.",
    "Every answer is reproducible at a date, which is what makes it safe to act on.",
    "The model is domain neutral. Swap the specification and it serves another network.",
  ], {
    x: x + 0.18, y: y + 0.58, w: cw3 - 0.36, h: 1.8, fontSize: 9.2,
    color: "D8DEE6", fontFace: F.txt, gap: 9, lineSpacingMultiple: 1.02,
  });
}

box(s3, 0.12, 6.78, W - 0.24, 0.54, C.ink);
dot(s3, 0.3, 6.97, C.mint, 0.1);
txt(s3, "None of this is exotic. It is the difference between a graph that stores what exists and one that can prove what is missing.", {
  x: 0.5, y: 6.78, w: 12.6, h: 0.54, fontSize: 11, color: C.white,
  fontFace: F.txt, valign: "middle",
});

/* ==================== SLIDE 4: FEASIBILITY ==================== */
const s4 = pres.addSlide();
s4.background = { color: C.white };
box(s4, 0, 0, W, 0.95, C.ink);
txt(s4, "FEASIBILITY", {
  x: 0.5, y: 0.15, w: 6.0, h: 0.21, fontSize: 10.5, charSpacing: 1.2,
  color: C.mint, fontFace: F.dspSemi,
});
txt(s4, "Yes. It is a graph problem, not a dashboard problem.", {
  x: 0.5, y: 0.4, w: 9.5, h: 0.38, fontSize: 22, color: C.white, fontFace: F.dspBold,
});
txt(s4, "A gap is a missing path, not a missing row.", {
  x: 9.95, y: 0.44, w: 2.95, h: 0.3, fontSize: 9.5, color: "A9B4C2", fontFace: F.txtLight,
});

const quads = [
  [C.l1, "Why a graph and not a report", [
    "A star schema answers how many cardiologists are in a county",
    "It cannot answer which counties have demand for a service line whose required specialty has no privileged provider within thirty minutes",
    "That is variable depth traversal across nine entity types, where the answer is an absent edge",
    "One modelling decision makes it computable: a service line declares what it REQUIRES, so every site and credential is tested against it automatically",
  ]],
  [C.l5, "What we must have, and what degrades", [
    "Must have: provider directory with NPI and taxonomy, credentialing roster, encounter or claims history, facility capability registry, patient geography",
    "Degrades gracefully: privileging detail, wait time series, payer contract terms, outcome registries",
    "Without bookable supply the capacity index falls back to a proxy, and no slots cannot be separated from a bad template",
  ]],
  [C.l7, "The five hard problems", [
    "Identity resolution is the ceiling on every number. Roster, claims and NPPES disagree about who works where",
    "Privileging data is usually the weakest source, and scenario three depends on it entirely",
    "Bookable against booked supply decides whether capacity is real or inferred",
    "Attribution: whose patient is it. One versioned rule per service line, agreed before build",
    "Re-identification risk is a design constraint, not a review step. It sets what the graph may hold",
  ]],
  [C.l8, "Ninety day proof", [
    "Weeks 1 to 3: one market, two service lines. Source inventory, attribution rule, required specialty map, privacy boundary design",
    "Weeks 4 to 7: boundary and identity resolution live. Match rate and k-anonymity floor published as the first deliverable",
    "Weeks 8 to 11: two gap engines, scenarios one and three, reviewed by a clinical SME",
    "Weeks 12 to 13: one what-if simulation, and a gap list a clinical leader and a network leader both sign",
  ]],
];
quads.forEach((q, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.12 + col * 6.6, y = 1.12 + row * 2.76;
  box(s4, x, y, 6.49, 2.6, C.panel, C.rule);
  dot(s4, x + 0.24, y + 0.27, q[0], 0.11);
  txt(s4, q[1], {
    x: x + 0.47, y: y + 0.18, w: 5.8, h: 0.3, fontSize: 14.5, color: C.text, fontFace: F.dspBold,
  });
  bullets(s4, q[2], {
    x: x + 0.47, y: y + 0.63, w: 5.85, h: 1.85, fontSize: 10, color: C.text,
    fontFace: F.txt, gap: 7, lineSpacingMultiple: 1.02,
  });
});
box(s4, 0.12, 6.78, W - 0.24, 0.54, C.ink);
dot(s4, 0.3, 6.97, C.mint, 0.1);
txt(s4, "None of the five are blockers. All five are decisions to take in week one, rather than discoveries to make in month three.", {
  x: 0.5, y: 6.78, w: 12.6, h: 0.54, fontSize: 11, color: C.white,
  fontFace: F.txt, valign: "middle",
});

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
