/* Clinical Network Knowledge Graph: 3 slide concept deck.
   Slide 1 replicates the layered architecture poster format. */

const pptxgen = require("pptxgenjs");
const path = require("path");
const OUT = process.argv[2] || path.join(__dirname, "network-graph.pptx");

const C = {
  l1: "1B6BC0", l2: "0E8A7D", l3: "7A4FC0", l4: "C2185B",
  l5: "C77400", l6: "C62828", l7: "2E7D32", l8: "00757F",
  ink: "0E1B2E", text: "1A1A1A", grey: "5A5A5A", rule: "D5D9DE",
  panel: "F4F6F8", white: "FFFFFF",
};
const F = { head: "Calibri", body: "Calibri", mono: "Courier New" };

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
function bullets(s, items, o) {
  s.addText(items.map((t, i) => ({
    text: t,
    options: {
      bullet: { characterCode: "25AA" },
      breakLine: i < items.length - 1,
      paraSpaceAfter: o.gap === undefined ? 1.5 : o.gap,
    },
  })), Object.assign({ isTextBox: true, margin: 0, valign: "top" }, o));
}

/* ==================== SLIDE 1: ARCHITECTURE POSTER ==================== */
const s1 = pres.addSlide();
s1.background = { color: C.white };

const M = 0.12, CW = W - M * 2;

/* ---- top band ---- */
box(s1, M, 0.07, 3.62, 0.66, C.white, C.rule);
txt(s1, "SEVEN AUTHORITATIVE SOURCES", {
  x: M + 0.1, y: 0.13, w: 3.4, h: 0.18, fontSize: 8.5, bold: true,
  charSpacing: 0.6, color: C.l1, fontFace: F.head,
});
const srcs = ["EHR", "Credential", "Directory", "Scheduling", "Claims", "Referrals", "Geo"];
srcs.forEach((n, i) => {
  const x = M + 0.1 + i * 0.5;
  txt(s1, n, {
    x, y: 0.36, w: 0.48, h: 0.16, fontSize: 6.5, bold: true, color: C.text,
    fontFace: F.body, align: "center",
  });
});
txt(s1, "read only  ·  tokenised  ·  provenance tagged", {
  x: M + 0.1, y: 0.56, w: 3.4, h: 0.15, fontSize: 6.5, italic: true,
  color: C.grey, fontFace: F.body,
});

box(s1, 3.86, 0.07, 5.55, 0.66, C.ink);
txt(s1, "PROVIDER, FACILITY AND PATIENT DEMAND", {
  x: 3.96, y: 0.12, w: 5.35, h: 0.24, fontSize: 13, bold: true, color: C.white,
  fontFace: F.head, align: "center",
});
txt(s1, "Clinical Network Knowledge Graph Architecture", {
  x: 3.96, y: 0.34, w: 5.35, h: 0.18, fontSize: 9, bold: true, color: "5FD0C0",
  fontFace: F.head, align: "center",
});
txt(s1, "sources → connectors → identity → domain model → JSON snapshot → derived edges → graph → gap engines", {
  x: 3.96, y: 0.55, w: 5.35, h: 0.16, fontSize: 6, color: "A9B4C2",
  fontFace: F.body, align: "center",
});

box(s1, 9.57, 0.07, 3.64, 0.66, C.white, C.rule);
txt(s1, "WHAT THE GRAPH ANSWERS", {
  x: 9.67, y: 0.13, w: 3.44, h: 0.18, fontSize: 8.5, bold: true,
  charSpacing: 0.6, color: C.l7, fontFace: F.head,
});
txt(s1, "Where demand has no provider  ·  where a provider has no demand  ·  where capability and credential do not meet  ·  where patients leave the network", {
  x: 9.67, y: 0.33, w: 3.44, h: 0.24, fontSize: 6.5, color: C.text,
  fontFace: F.body, lineSpacingMultiple: 1.04,
});
txt(s1, "The missing edge is the answer", {
  x: 9.67, y: 0.56, w: 3.44, h: 0.15, fontSize: 6.5, italic: true,
  color: C.l7, fontFace: F.body,
});

/* ---- the eight layers ---- */
const COLW = 1.585, STEP = 1.6425;
const HDR_Y = 0.79, HDR_H = 0.58;
const BODY_Y = 1.39, BODY_BOT = 6.18;
const WYG_H = 0.46;

const layers = [
  {
    c: C.l1, n: "LAYER 1", t: "Source Systems", cap: "Authoritative systems of record",
    wyg: "Every network fact in one place, no more tribal knowledge",
    secs: [
      ["EHR and clinical", ["Encounters, diagnoses, procedures", "ADT admit, transfer, discharge", "Orders, results, problem list", "Department and visit type"]],
      ["Credentialing and privileging", ["Licence, board certification", "Privileges by procedure", "Appointment and expirables", "Sanctions and restrictions"]],
      ["Provider directory and MDM", ["Individual and organisation NPI", "NUCC taxonomy, subspecialty", "Practice locations, group TIN", "Panel open or closed"]],
      ["Scheduling and access", ["Templates, sessions, slots", "Booked against bookable", "Third next available", "No show and cancellation"]],
      ["Claims and billing", ["CPT, ICD-10, place of service", "Rendering and billing NPI", "Payer, plan, network status", "Out of network activity"]],
      ["Referrals, orders and geo", ["Referring to receiving NPI", "Reason, urgency, completion", "Census tract and drive time", "CMS adequacy standards"]],
    ],
  },
  {
    c: C.l2, n: "LAYER 2", t: "Source Connectors", cap: "Read only, PHI safe at the boundary",
    wyg: "Safe, repeatable reads. No writes, no PHI sprawl",
    secs: [
      ["EHRConnector", ["FHIR R4 and HL7 v2 feeds", "Read only service account", "Bulk export plus ADT stream", "MRN tokenised at ingress"]],
      ["CredentialingConnector", ["Roster API or SFTP delta", "Privilege code dictionary", "Expirables change capture"]],
      ["DirectoryConnector", ["NPPES weekly plus MDM API", "NPI to TIN cross walk", "Taxonomy version pinned"]],
      ["SchedulingConnector", ["Slot and template API", "Nightly bookable snapshot", "Wait time series retained"]],
      ["ClaimsConnector", ["837 and 835 extract", "De-identified at the boundary", "Monthly close, replayable"]],
      ["Referral and Geo connectors", ["Order and referral export", "Census and drive time matrix", "Hash per record, no writes"]],
    ],
  },
  {
    c: C.l3, n: "LAYER 3", t: "Ingestors and Identity", cap: "Parse, resolve, prove",
    wyg: "One patient, one provider, one place, with the proof kept",
    secs: [
      ["Parse and normalise", ["FHIR to domain objects", "ICD-10, CPT, SNOMED mapped", "Taxonomy to specialty", "Units, dates, time zones"]],
      ["Patient identity, EMPI", ["Deterministic MRN, member id", "Probabilistic name, DOB, address", "Review band, no silent merge", "Token downstream, never MRN"]],
      ["Provider and place identity", ["Individual NPI is the person", "TIN plus NPI is the practice", "CCN is the facility", "Roster, claims, NPPES deduped"]],
      ["Validation", ["Required fields and code sets", "Privilege against procedure", "Affiliation validity dates", "Rejects to exception queue"]],
      ["Provenance", ["Source, extract id, hash", "retrievedAt, derivationMethod", "FACTUAL or INFERRED"]],
    ],
  },
  {
    c: C.l4, n: "LAYER 4", t: "Domain Model", cap: "CareNetworkContext",
    wyg: "Raw records become a typed network model",
    secs: [
      ["Root object", ["networkId, marketId", "asOfDate, snapshotId", "provenance block"]],
      ["providers[]", ["npi, specialty[], subspecialty", "privileges[], credentialStatus", "fte, sessions, panelStatus", "practiceGroup, locations[]"]],
      ["facilities[]", ["ccn, type, hospital or ASC", "serviceLines[], capabilities[]", "beds, rooms, equipment", "geo, driveTimeBands[]"]],
      ["serviceLines[]", ["requiredSpecialties[]", "requiredCapabilities[]", "minVolumeThreshold"]],
      ["demand[]", ["geographyId, serviceLineId", "patients, encounters, trend", "acuityMix, payerMix"]],
      ["access[] and flows[]", ["slots, thirdNextAvailable", "referral origin to destination", "inNetwork, leakageFlag", "outcome O over E, n, interval"]],
    ],
  },
  {
    c: C.l5, n: "LAYER 5", t: "Graph Storage", cap: "Neutral JSON contract",
    json: [
      "{",
      ' "snapshotId": "tx-2026Q3",',
      ' "nodes": [{',
      '   "id": "npi:1487…",',
      '   "type": "PROVIDER",',
      '   "properties": {',
      '     "specialty": "CARDIOLOGY",',
      '     "fte": 0.6, "panel": "OPEN" },',
      '   "sourceRefs": [{ "system":"CAQH",',
      '     "hash": "a91f…" }] }],',
      ' "relationships": [{',
      '   "type": "PRACTICES_AT",',
      '   "from": "npi:1487…",',
      '   "to":   "ccn:450214",',
      '   "validFrom": "2024-07-01",',
      '   "confidence": 1.0 }]',
      "}",
    ],
    wyg: "A portable snapshot any tool or engine can consume",
    secs: [
      ["What the file holds", ["Every node with its properties", "Every typed relationship", "Validity dates on each edge", "Provenance and content hash", "One snapshot per period"]],
      ["Storage rules", ["Rebuilt, never written back", "Versioned per snapshot", "De-identified by default", "Encrypted at rest"]],
    ],
  },
  {
    c: C.l6, n: "LAYER 6", t: "Derived Edge Engine", cap: "Where a gap becomes computable",
    wyg: "The missing edge becomes a measurable, defensible number",
    secs: [
      ["Derived edges", ["SERVES geo to facility, driveMin", "REQUIRES serviceLine to specialty", "COVERS provider to line at site", "SUBSTITUTE_FOR provider to provider", "REFERS_TO provider to provider"]],
      ["Computed indices", ["inflow and trend by geo and line", "capacity, bookable against demand", "coverage and adequacy", "leakage share, referral depth", "outcome O over E with shrinkage", "concentration, HHI, SPOF flag"]],
      ["Guardrails", ["Minimum volume before ranking", "Peer group by setting and case mix", "Confidence interval published", "Valid-at date on every index"]],
      ["Rebuild policy", ["Every index dated and versioned", "Last quarter reproduces exactly"]],
    ],
  },
  {
    c: C.l7, n: "LAYER 7", t: "Network ContextGraph", cap: "In-memory knowledge graph",
    wyg: "Gap, blast radius and what-if answered in under a second",
    secs: [
      ["Graph structure", ["Nodes by type, typed edges", "Weights: driveMin, volume, cost", "Adjacency and drive time index", "O(1) node access, typed scans"]],
      ["Traversals", ["coverage_path(geo, serviceLine)", "missing_edge(demand, supply)", "blast_radius(provider, hops)", "shortest_referral_path(a, b)", "k_nearest_providers(geo, k)"]],
      ["Network analytics", ["Centrality: who is load bearing", "Components: network islands", "Communities: referral clusters", "Set cover: fewest hires to fix"]],
      ["What-if simulation", ["Insert a hypothetical provider", "Re-run traversals, diff result", "Patients gaining access", "Leakage recaptured"]],
    ],
  },
  {
    c: C.l8, n: "LAYER 8", t: "Gap Engines and API", cap: "Scenario library on verified facts",
    wyg: "Ranked, explainable gaps with the action already attached",
    secs: [
      ["Gap engines", ["access_gap() demand, no supply", "idle_supply_gap() supply, no demand", "capability_credential_gap()", "service_line_completeness()", "leakage_gap(), adequacy_gap()", "single_point_of_failure()", "volume_threshold_gap()", "patient_care_gap()"]],
      ["Query API", ["graph.query, gap.rank", "whatif.simulate", "cohort.build, evidence.path"]],
      ["Agent surface", ["Natural language, cited nodes", "Refuses below the evidence floor", "Every answer carries its date"]],
      ["Output contract", ["Ranked gap with evidence path", "Patients and volume affected", "Recommended action and owner", "Cohort ready for activation"]],
    ],
  },
];

layers.forEach((L, i) => {
  const x = M + i * STEP;
  /* header */
  box(s1, x, HDR_Y, COLW, HDR_H, L.c);
  txt(s1, L.n, {
    x: x + 0.06, y: HDR_Y + 0.05, w: COLW - 0.12, h: 0.14, fontSize: 7,
    bold: true, charSpacing: 0.5, color: "FFFFFF", fontFace: F.head, align: "center",
  });
  txt(s1, L.t, {
    x: x + 0.04, y: HDR_Y + 0.18, w: COLW - 0.08, h: 0.28, fontSize: 9, bold: true,
    color: "FFFFFF", fontFace: F.head, align: "center", lineSpacingMultiple: 0.92,
  });
  txt(s1, L.cap, {
    x: x + 0.05, y: HDR_Y + 0.43, w: COLW - 0.1, h: 0.13, fontSize: 5.5, italic: true,
    color: "E8F0F4", fontFace: F.body, align: "center",
  });
  /* body */
  box(s1, x, BODY_Y, COLW, BODY_BOT - BODY_Y, C.white, C.rule);

  let cy = BODY_Y + 0.07;
  if (L.json) {
    txt(s1, "network.json (excerpt)", {
      x: x + 0.07, y: cy, w: COLW - 0.14, h: 0.13, fontSize: 6.5, bold: true,
      color: L.c, fontFace: F.head,
    });
    cy += 0.16;
    box(s1, x + 0.05, cy, COLW - 0.1, 1.42, C.panel, C.rule);
    txt(s1, L.json.join("\n"), {
      x: x + 0.1, y: cy + 0.04, w: COLW - 0.2, h: 1.34, fontSize: 4.6,
      color: C.text, fontFace: F.mono, lineSpacingMultiple: 1.0,
    });
    cy += 1.5;
  }
  L.secs.forEach((sec) => {
    s1.addShape(pres.ShapeType.rect, {
      x: x + 0.07, y: cy + 0.035, w: 0.07, h: 0.07, fill: { color: L.c },
    });
    txt(s1, sec[0], {
      x: x + 0.18, y: cy, w: COLW - 0.25, h: 0.14, fontSize: 6.5, bold: true,
      color: L.c, fontFace: F.head,
    });
    cy += 0.16;
    bullets(s1, sec[1], {
      x: x + 0.1, y: cy, w: COLW - 0.18, h: sec[1].length * 0.115 + 0.1,
      fontSize: 5.5, color: C.text, fontFace: F.body, gap: 1,
      lineSpacingMultiple: 0.95,
    });
    cy += sec[1].length * 0.106 + 0.09;
  });
  /* what you get */
  box(s1, x, BODY_BOT - WYG_H, COLW, WYG_H, L.c);
  txt(s1, "WHAT YOU GET", {
    x: x + 0.07, y: BODY_BOT - WYG_H + 0.04, w: COLW - 0.14, h: 0.12, fontSize: 5.5,
    bold: true, charSpacing: 0.4, color: "D8EAF2", fontFace: F.head,
  });
  txt(s1, L.wyg, {
    x: x + 0.07, y: BODY_BOT - WYG_H + 0.17, w: COLW - 0.14, h: 0.26, fontSize: 5.8,
    bold: true, color: "FFFFFF", fontFace: F.body, lineSpacingMultiple: 0.95,
  });
  /* arrow into the next layer */
  if (i < layers.length - 1) {
    txt(s1, "▶", {
      x: x + COLW - 0.005, y: HDR_Y + 0.2, w: 0.07, h: 0.14, fontSize: 5,
      color: "9AA4B0", fontFace: F.body, align: "center",
    });
  }
});

/* ---- handoff row ---- */
txt(s1, "HANDOFF\nBETWEEN LAYERS", {
  x: M, y: 6.26, w: 1.0, h: 0.28, fontSize: 5.5, bold: true, color: C.grey,
  fontFace: F.head, lineSpacingMultiple: 0.95,
});
const hand = [
  ["read only API  ·  FHIR plus roster", C.l1],
  ["source artifact: bytes plus hash", C.l2],
  ["resolved entities plus provenance", C.l3],
  ["typed CareNetworkContext objects", C.l4],
  ["vendor neutral JSON snapshot", C.l5],
  ["derived edges plus dated indices", C.l6],
  ["loaded graph  ·  traversals ready", C.l7],
];
hand.forEach((h, i) => {
  const x = 1.2 + i * 1.73;
  box(s1, x, 6.26, 1.66, 0.26, C.white, C.rule);
  s1.addShape(pres.ShapeType.rect, { x: x + 0.06, y: 6.35, w: 0.06, h: 0.08, fill: { color: h[1] } });
  txt(s1, h[0], {
    x: x + 0.15, y: 6.26, w: 1.46, h: 0.26, fontSize: 5.3, color: C.text,
    fontFace: F.body, valign: "middle",
  });
});

/* ---- bottom panels ---- */
const bots = [
  [C.l3, "Provenance and authority",
    "Every node and edge carries source, extract id, content hash, retrievedAt and derivation (FACTUAL | INFERRED | MODELLED). Authority stays with the source system. The graph never becomes the system of record for a clinical fact."],
  [C.l6, "PHI and three identities",
    "Analytic graph: de-identified and tokenised, no MRN. Operational graph: limited data set under BAA, for outreach only. Identified access: role based, minimum necessary enforced at the query layer. Model endpoints see aggregates unless BAA covered."],
  [C.l1, "Audit and traceability",
    "Every gap resolves back to the source rows that produced it. Every query, answer and cohort is logged with user, timestamp, snapshot id and the evidence path returned. A gap that cannot be replayed is not published."],
  [C.l7, "Scope of the proof",
    "One market, two service lines, ninety days. Build order: identity, then graph, then two gap engines, then one what-if. Success is a gap list that a clinical leader and a network leader both sign."],
];
bots.forEach((b, i) => {
  const x = M + i * 3.2925;
  box(s1, x, 6.62, 3.2125, 0.8, C.white, C.rule);
  s1.addShape(pres.ShapeType.rect, { x: x + 0.09, y: 6.71, w: 0.08, h: 0.08, fill: { color: b[0] } });
  txt(s1, b[1], {
    x: x + 0.22, y: 6.67, w: 2.9, h: 0.15, fontSize: 7, bold: true, color: b[0], fontFace: F.head,
  });
  txt(s1, b[2], {
    x: x + 0.09, y: 6.86, w: 3.05, h: 0.5, fontSize: 5.6, color: C.text,
    fontFace: F.body, lineSpacingMultiple: 1.0,
  });
});

/* ==================== SLIDE 2: SCENARIO CATALOGUE ==================== */
const s2 = pres.addSlide();
s2.background = { color: C.white };
box(s2, 0, 0, W, 0.92, C.ink);
txt(s2, "TWELVE SCENARIOS, ONE ENGINE", {
  x: 0.5, y: 0.14, w: 8.0, h: 0.2, fontSize: 10, bold: true, charSpacing: 1.4,
  color: "5FD0C0", fontFace: F.head,
});
txt(s2, "What the provider, facility and patient graph answers", {
  x: 0.5, y: 0.38, w: 9.0, h: 0.36, fontSize: 21, bold: true, color: C.white, fontFace: F.head,
});
txt(s2, "Every scenario is the same query shape:\nthe demand path exists, the supply path does not.", {
  x: 9.7, y: 0.22, w: 3.15, h: 0.5, fontSize: 8.5, italic: true, color: "A9B4C2",
  fontFace: F.body, lineSpacingMultiple: 1.06,
});

const fams = [
  ["A  ·  SUPPLY AND DEMAND MISMATCH", C.l1],
  ["B  ·  NETWORK COMPLETENESS", C.l4],
  ["C  ·  PATIENT FLOW", C.l5],
  ["D  ·  ACCESS, QUALITY AND GROWTH", C.l7],
];
const scen = [
  [ // A
    ["1  Demand without supply", "Geography has inflow for a service line and no credentialed provider inside the drive time band", "Recruit, locum, telehealth or a transfer agreement"],
    ["2  Supply without demand", "Sessions and slots exist, encounter volume sits in the bottom decile for the peer group", "Redeploy sessions, re-market, resize the template"],
    ["3  Capability and credential mismatch", "The site holds the asset, cath lab, MRI, L and D, with nobody privileged to use it, or the reverse", "Privilege, credential, or move the asset"],
  ],
  [ // B
    ["4  Incomplete service line", "The line requires N specialties and the site has N minus one, so care finishes somewhere else", "Close the one gap that unlocks the whole line"],
    ["5  Single point of failure", "One provider is the only path to a service line in a county, and the graph says who", "Succession and cross cover, blast radius quantified"],
    ["6  Volume below threshold", "Complex procedures performed under the safe volume floor for that site or provider", "Consolidate or refer, with the quality risk named"],
  ],
  [ // C
    ["7  Referral leakage", "Attributed patients treated out of network, traced along the actual referral edges", "Recapture campaign that fixes the reason, not the symptom"],
    ["8  Bypass and travel burden", "Patients drive past a nearer site to reach a farther one, repeatedly", "Isolates reputation against capability against access"],
    ["9  Referral chain depth", "Four hops to reach definitive care, every hop measurable in days", "Shorten the path, open a direct access pathway"],
  ],
  [ // D
    ["10  Adequacy and access deserts", "CMS time and distance failures by county and specialty, mapped to the graph", "Filing evidence, and the fewest hires that fix the most counties"],
    ["11  Inflow high, outcome weak", "Volume in the top decile with risk adjusted O over E above the peer benchmark", "Quality campaign, and steer volume to the strong sites"],
    ["12  Hire and site simulation", "Insert a hypothetical provider or site, re-run every traversal, diff the result", "Patients gaining access and leakage recaptured, before you spend"],
  ],
];

const colW = 3.19, colStep = 3.2925;
fams.forEach((f, ci) => {
  const x = 0.12 + ci * colStep;
  box(s2, x, 1.08, colW, 0.3, f[1]);
  txt(s2, f[0], {
    x: x + 0.12, y: 1.08, w: colW - 0.2, h: 0.3, fontSize: 8, bold: true,
    charSpacing: 0.5, color: C.white, fontFace: F.head, valign: "middle",
  });
  scen[ci].forEach((sc, ri) => {
    const y = 1.48 + ri * 1.74;
    box(s2, x, y, colW, 1.62, C.panel, C.rule);
    txt(s2, sc[0], {
      x: x + 0.14, y: y + 0.12, w: colW - 0.28, h: 0.34, fontSize: 11, bold: true,
      color: C.text, fontFace: F.head, lineSpacingMultiple: 0.95,
    });
    txt(s2, "IN THE GRAPH", {
      x: x + 0.14, y: y + 0.52, w: colW - 0.28, h: 0.14, fontSize: 5.8, bold: true,
      charSpacing: 0.5, color: C.grey, fontFace: F.head,
    });
    txt(s2, sc[1], {
      x: x + 0.14, y: y + 0.67, w: colW - 0.28, h: 0.48, fontSize: 8.5, color: C.text,
      fontFace: F.body, lineSpacingMultiple: 1.02,
    });
    s2.addShape(pres.ShapeType.rect, { x: x + 0.14, y: y + 1.2, w: 0.07, h: 0.07, fill: { color: f[1] } });
    txt(s2, sc[2], {
      x: x + 0.27, y: y + 1.16, w: colW - 0.42, h: 0.38, fontSize: 8.2, bold: true,
      color: f[1], fontFace: F.body, lineSpacingMultiple: 1.0,
    });
  });
});

box(s2, 0.12, 6.78, W - 0.24, 0.5, C.ink);
s2.addShape(pres.ShapeType.rect, { x: 0.28, y: 6.96, w: 0.1, h: 0.1, fill: { color: "5FD0C0" } });
txt(s2, "Each scenario returns the same four things: the evidence path, the patients affected, the recommended action, and a cohort ready to activate.", {
  x: 0.48, y: 6.78, w: 12.6, h: 0.5, fontSize: 10, italic: true, color: C.white,
  fontFace: F.body, valign: "middle",
});

/* ==================== SLIDE 3: FEASIBILITY ==================== */
const s3 = pres.addSlide();
s3.background = { color: C.white };
box(s3, 0, 0, W, 0.92, C.ink);
txt(s3, "FEASIBILITY", {
  x: 0.5, y: 0.14, w: 6.0, h: 0.2, fontSize: 10, bold: true, charSpacing: 1.4,
  color: "5FD0C0", fontFace: F.head,
});
txt(s3, "Yes. It is a graph problem, not a dashboard problem.", {
  x: 0.5, y: 0.38, w: 9.5, h: 0.36, fontSize: 21, bold: true, color: C.white, fontFace: F.head,
});
txt(s3, "A gap is a missing path, not a missing row.", {
  x: 9.9, y: 0.34, w: 2.95, h: 0.3, fontSize: 9, italic: true, color: "A9B4C2", fontFace: F.body,
});

const quads = [
  [C.l1, "Why a graph and not a report",
    ["A star schema answers how many cardiologists are in a county",
     "It cannot answer which counties have demand for a service line whose required specialty has no privileged provider within thirty minutes",
     "That is variable depth traversal across seven entity types, where the answer is an absent edge",
     "One modelling decision makes it computable: a service line declares what it REQUIRES, so every site and credential can be tested against it automatically"]],
  [C.l4, "What we must have, and what degrades",
    ["Must have: provider directory with NPI and taxonomy, credentialing roster, encounter or claims history, facility service and capability registry, patient geography",
     "Degrades gracefully: privileging detail, wait time series, payer contract terms, outcome registries",
     "Without bookable supply the capacity index falls back to a proxy, and no slots cannot be separated from a bad template"]],
  [C.l6, "The five hard problems",
    ["Identity resolution is the ceiling on every number. Roster, claims and NPPES disagree about who works where",
     "Privileging data is usually the weakest source, and scenario three depends on it entirely",
     "Bookable against booked supply decides whether capacity is real or inferred",
     "Attribution: whose patient is it. One versioned rule per service line, agreed before build",
     "PHI governance: three identities, enforced at the query layer rather than by convention"]],
  [C.l7, "Ninety day proof",
    ["Weeks 1 to 3: one market, two service lines. Source inventory, attribution rule, required specialty map agreed",
     "Weeks 4 to 7: identity resolution and the graph loaded, match rate published as the first deliverable",
     "Weeks 8 to 11: two gap engines live, scenario one and scenario three, reviewed by a clinical SME",
     "Weeks 12 to 13: one what-if simulation, and a gap list that a clinical leader and a network leader both sign"]],
];
quads.forEach((q, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.12 + col * 6.6, y = 1.12 + row * 2.72;
  box(s3, x, y, 6.49, 2.56, C.panel, C.rule);
  s3.addShape(pres.ShapeType.rect, { x: x + 0.22, y: y + 0.26, w: 0.11, h: 0.11, fill: { color: q[0] } });
  txt(s3, q[1], {
    x: x + 0.44, y: y + 0.18, w: 5.8, h: 0.28, fontSize: 13.5, bold: true,
    color: C.text, fontFace: F.head,
  });
  bullets(s3, q[2], {
    x: x + 0.44, y: y + 0.6, w: 5.85, h: 1.8, fontSize: 9.5, color: C.text,
    fontFace: F.body, gap: 7, lineSpacingMultiple: 1.02,
  });
});

box(s3, 0.12, 6.72, W - 0.24, 0.56, C.ink);
s3.addShape(pres.ShapeType.rect, { x: 0.28, y: 6.93, w: 0.1, h: 0.1, fill: { color: "5FD0C0" } });
txt(s3, "None of the five are blockers. All five are decisions to take in week one, rather than discoveries to make in month three.", {
  x: 0.48, y: 6.72, w: 12.6, h: 0.56, fontSize: 10.5, italic: true, color: C.white,
  fontFace: F.body, valign: "middle",
});

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
