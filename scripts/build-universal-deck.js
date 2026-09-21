/* Universal Gap Intelligence Framework: does the pattern travel?
   Type: Trenda IG Display / Trenda IG Text. 3 slides. */

const pptxgen = require("pptxgenjs");
const path = require("path");
const OUT = process.argv[2] || path.join(__dirname, "universal-framework.pptx");

const C = {
  core: "0E8A7D", pack: "C77400", blue: "1B6BC0", purple: "6A1B9A",
  pink: "C2185B", red: "C62828", green: "2E7D32", teal: "00757F",
  ink: "0E1B2E", ink2: "16202C", text: "1A1A1A", grey: "5A6573",
  rule: "D5D9DE", panel: "F4F6F9", panel2: "ECEFF3", white: "FFFFFF", mint: "5FD0C0",
};
const F = {
  dspSemi: "Trenda IG Display Semibold",
  dspBold: "Trenda IG Display Bold",
  txt: "Trenda IG Text",
  txtLight: "Trenda IG Text Light",
  txtSemi: "Trenda IG Text Semibold",
};

const W = 13.33;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Insight Global Labs";
pres.title = "Universal Gap Intelligence Framework";

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
function nLines(str, face, pt, wIn) {
  const sp = textW(" ", face, pt);
  let n = 1, cur = 0;
  for (const word of str.split(" ")) {
    const ww = textW(word, face, pt);
    if (ww > wIn) { if (cur > 0) n += 1; n += Math.ceil(ww / wIn) - 1; cur = ww % wIn; }
    else if (cur === 0) cur = ww;
    else if (cur + sp + ww <= wIn) cur += sp + ww;
    else { n += 1; cur = ww; }
  }
  return n;
}
function txt(s, t, o) {
  s.addText(t, Object.assign({ isTextBox: true, margin: 0, valign: "top" }, o));
}
function box(s, x, y, w, h, fill, line) {
  s.addShape(pres.ShapeType.rect, Object.assign(
    { x, y, w, h, fill: { color: fill } }, line ? { line: { color: line, width: 0.75 } } : {}));
}
function dot(s, x, y, color, size) {
  const d = size || 0.09;
  s.addShape(pres.ShapeType.rect, { x, y, w: d, h: d, fill: { color } });
}
function bullets(s, items, o) {
  s.addText(items.map((t, i) => ({
    text: t,
    options: {
      bullet: { characterCode: "2022", indent: o.bulletIndent || 9 },
      breakLine: i < items.length - 1,
      paraSpaceAfter: o.gap === undefined ? 4 : o.gap,
    },
  })), Object.assign({ isTextBox: true, margin: 0, valign: "top" }, o));
}
function header(s, eyebrow, title, right) {
  box(s, 0, 0, W, 0.95, C.ink);
  txt(s, eyebrow, {
    x: 0.5, y: 0.15, w: 9.0, h: 0.21, fontSize: 10.5, charSpacing: 1.2,
    color: C.mint, fontFace: F.dspSemi,
  });
  txt(s, title, {
    x: 0.5, y: 0.4, w: 10.0, h: 0.38, fontSize: 22, color: C.white, fontFace: F.dspBold,
  });
  if (right) txt(s, right, {
    x: 10.7, y: 0.24, w: 2.3, h: 0.5, fontSize: 9, color: "A9B4C2",
    fontFace: F.txtLight, lineSpacingMultiple: 1.08,
  });
}
function strip(s, y, text) {
  box(s, 0.12, y, W - 0.24, 0.54, C.ink);
  dot(s, 0.3, y + 0.19, C.mint, 0.1);
  txt(s, text, {
    x: 0.5, y: y, w: 12.6, h: 0.54, fontSize: 11, color: C.white,
    fontFace: F.txt, valign: "middle",
  });
}

/* ============ SLIDE 1: CORE AND PACK ============ */
const s1 = pres.addSlide();
s1.background = { color: C.white };
header(s1, "ONE FRAMEWORK, MANY MARKETS",
  "What stays the same, and what every industry has to declare",
  "Roughly seven parts in ten\nnever change.");

txt(s1, "THE NINE LAYERS, MARKED CORE OR PACK", {
  x: 0.12, y: 1.1, w: 5.0, h: 0.17, fontSize: 7.5, charSpacing: 0.6,
  color: C.grey, fontFace: F.txtSemi,
});
const rows = [
  ["L1", "Source systems", "PACK", "Whatever the systems of record are, in any vendor"],
  ["L2", "Source connectors", "PACK", "One connector per system. The contract is core"],
  ["L3", "Trust and privacy boundary", "BOTH", "Mechanics are core. HIPAA, GDPR or PCI is the pack"],
  ["L4", "Ingest and identity", "BOTH", "Resolution machinery is core. The identity spine is the pack"],
  ["L5", "Domain model", "PACK", "The classes change. Bitemporal and evidence rules do not"],
  ["L6", "Graph storage", "CORE", "Content addressed, immutable, vendor neutral"],
  ["L7", "Derived edge engine", "BOTH", "The engine is core. Reachability and thresholds are the pack"],
  ["L8", "Graph runtime", "CORE", "Traversal, vectors, shadow graph, analytics"],
  ["L9", "Gap engines and API", "CORE", "The twelve scenarios are domain neutral already"],
];
const tag = { CORE: C.core, PACK: C.pack, BOTH: C.purple };
rows.forEach((r, i) => {
  const y = 1.32 + i * 0.5;
  box(s1, 0.12, y, 8.1, 0.44, i % 2 ? C.panel : C.panel2);
  box(s1, 0.12, y, 0.5, 0.44, C.ink);
  txt(s1, r[0], {
    x: 0.12, y: y, w: 0.5, h: 0.44, fontSize: 9.5, color: C.white,
    fontFace: F.dspBold, align: "center", valign: "middle",
  });
  txt(s1, r[1], {
    x: 0.72, y: y, w: 2.3, h: 0.44, fontSize: 10, color: C.text,
    fontFace: F.txtSemi, valign: "middle",
  });
  box(s1, 3.08, y + 0.11, 0.64, 0.22, tag[r[2]]);
  txt(s1, r[2], {
    x: 3.08, y: y + 0.11, w: 0.64, h: 0.22, fontSize: 6.8, charSpacing: 0.3,
    color: C.white, fontFace: F.txtSemi, align: "center", valign: "middle",
  });
  txt(s1, r[3], {
    x: 3.86, y: y, w: 4.28, h: 0.44, fontSize: 8.8, color: C.grey,
    fontFace: F.txt, valign: "middle",
  });
});

/* right column */
box(s1, 8.42, 1.32, 4.79, 2.26, C.ink);
dot(s1, 8.62, 1.54, C.mint, 0.1);
txt(s1, "The invariant claim", {
  x: 8.82, y: 1.45, w: 4.2, h: 0.28, fontSize: 13.5, color: C.white, fontFace: F.dspBold,
});
bullets(s1, [
  "A gap is a missing path between demand and a supply that satisfies a declared capability, reachable inside a constraint.",
  "That sentence contains no industry. Change the nouns and the engine does not notice.",
  "Everything above L5 operates on the abstraction, never on the domain.",
], {
  x: 8.62, y: 1.86, w: 4.4, h: 1.6, fontSize: 9.2, color: "D8DEE6",
  fontFace: F.txt, gap: 7, lineSpacingMultiple: 1.02,
});

box(s1, 8.42, 3.7, 4.79, 2.12, C.panel, C.rule);
dot(s1, 8.62, 3.92, C.pack, 0.1);
txt(s1, "The pack contract", {
  x: 8.82, y: 3.83, w: 4.2, h: 0.28, fontSize: 13.5, color: C.text, fontFace: F.dspBold,
});
bullets(s1, [
  "Ontology classes and the identity spine",
  "The reachability metric: drive time, signal, latency, territory",
  "The capability specification: what an offering requires",
  "The regulatory profile and its thresholds",
  "Source connectors and the action catalogue",
], {
  x: 8.62, y: 4.22, w: 4.4, h: 1.5, fontSize: 9.2, color: C.text,
  fontFace: F.txt, gap: 5, lineSpacingMultiple: 1.02,
});

box(s1, 0.12, 5.86, 13.09, 0.62, C.panel, C.rule);
dot(s1, 0.32, 6.08, C.blue, 0.1);
txt(s1, "We have already built two packs without calling them packs. The engineering delivery graph and the clinical network graph share nine layers and differ only in the five declarations above.", {
  x: 0.54, y: 5.86, w: 12.5, h: 0.62, fontSize: 10.5, color: C.text,
  fontFace: F.txt, valign: "middle",
});
strip(s1, 6.62, "So the honest claim is not that it fits everything. It is that the architecture is the product and the industry is the configuration.");

/* ============ SLIDE 2: THE MAPPING ============ */
const s2 = pres.addSlide();
s2.background = { color: C.white };
header(s2, "THE SAME MODEL, FOUR INDUSTRIES",
  "Change the nouns. The engine does not notice.",
  "Worked, not asserted.");

const cols = [
  ["", 2.35, C.grey],
  ["HEALTHCARE", 2.68, C.pink],
  ["TELECOM", 2.68, C.blue],
  ["AUTOMOTIVE", 2.68, C.pack],
  ["ENGINEERING DELIVERY", 2.68, C.purple],
];
const mrows = [
  ["Party, the demand side", "Patient", "Subscriber", "Owner or buyer", "Requirement or request"],
  ["Resource, the supply side", "Provider, facility", "Cell site, sector, field engineer", "Dealer, bay, technician", "Component, service, team"],
  ["Capability", "Specialty plus privilege", "Band, capacity, backhaul", "Brand and EV certification, rig", "Language, framework, API"],
  ["Offering, which declares what it REQUIRES", "Service line", "Plan or product, such as fixed wireless", "Sale, warranty repair, EV service", "Feature or change"],
  ["Place and reachability", "County, drive time", "Coverage polygon, signal strength", "Territory, drive time", "Repo and domain boundary"],
  ["Interaction", "Encounter", "Session, care call, truck roll", "Service visit, test drive", "Deployment, incident"],
  ["Commitment with a lifecycle", "Appointment", "Subscription", "Order, service booking", "Work item"],
  ["Flow, where value leaks", "Referral out of network", "Port out to a competitor", "Defection to independents", "Dependency across teams"],
  ["The adequacy rule", "CMS time and distance", "Regulator coverage obligation", "OEM network standard", "Architecture standard or SLA"],
  ["Identity spine", "NPI, TIN, CCN, EMPI", "MSISDN, IMSI, account", "VIN, dealer code", "Repo and service id"],
];
let cx = 0.12;
const colX = [];
cols.forEach((c) => { colX.push(cx); cx += c[1]; });
cols.forEach((c, i) => {
  if (i === 0) return;
  box(s2, colX[i], 1.12, cols[i][1] - 0.04, 0.34, c[2]);
  txt(s2, c[0], {
    x: colX[i] + 0.1, y: 1.12, w: cols[i][1] - 0.24, h: 0.34, fontSize: 8,
    charSpacing: 0.4, color: C.white, fontFace: F.txtSemi, valign: "middle",
  });
});
mrows.forEach((r, ri) => {
  const y = 1.52 + ri * 0.44;
  box(s2, 0.12, y, 13.09, 0.4, ri % 2 ? C.panel : C.white, C.rule);
  txt(s2, r[0], {
    x: 0.24, y: y, w: 2.15, h: 0.4, fontSize: 8.6, color: C.text,
    fontFace: F.txtSemi, valign: "middle", lineSpacingMultiple: 0.96,
  });
  for (let i = 1; i <= 4; i++) {
    txt(s2, r[i], {
      x: colX[i] + 0.1, y: y, w: cols[i][1] - 0.22, h: 0.4, fontSize: 8.4,
      color: C.grey, fontFace: F.txt, valign: "middle", lineSpacingMultiple: 0.96,
    });
  }
});

box(s2, 0.12, 6.02, 13.09, 0.68, C.ink);
dot(s2, 0.32, 6.24, C.mint, 0.1);
txt(s2, "Scenario 1, demand without supply, read four ways:", {
  x: 0.54, y: 6.1, w: 3.6, h: 0.2, fontSize: 9, color: C.mint, fontFace: F.txtSemi,
});
txt(s2, "a county with inflow and no credentialed cardiologist inside the drive time band  ·  a postcode with demand and no site carrying the required band  ·  a territory with a growing electric parc and no high voltage certified technician  ·  a requirement with no component that implements it", {
  x: 0.54, y: 6.32, w: 12.5, h: 0.32, fontSize: 8.8, color: "D8DEE6",
  fontFace: F.txt, lineSpacingMultiple: 1.0,
});
strip(s2, 6.78, "Telecom coverage obligations and CMS network adequacy are the same query. So are a stranded cath lab and a 5G radio with no fibre behind it.");

/* ============ SLIDE 3: FIT AND LIMITS ============ */
const s3 = pres.addSlide();
s3.background = { color: C.white };
header(s3, "FIT, LIMITS AND TECHNOLOGY",
  "Where it travels, where it weakens, and what is really coupled",
  "The useful answer is\nnot yes to everything.");

const CX3 = [0.12, 4.53, 8.94], CW3 = 4.27;

/* fit test */
box(s3, CX3[0], 1.08, CW3, 4.62, C.panel, C.rule);
dot(s3, CX3[0] + 0.2, 1.31, C.core, 0.1);
txt(s3, "Six questions that decide fit", {
  x: CX3[0] + 0.4, y: 1.22, w: CW3 - 0.6, h: 0.3, fontSize: 14, color: C.text, fontFace: F.dspBold,
});
const qs = [
  "Can demand be located, by geography, segment or jurisdiction?",
  "Is supply lumpy, licensed or slow to add? This is the decisive one.",
  "Can someone write down what an offering requires?",
  "Is there an identity spine on both sides?",
  "Does value flow between suppliers, and can it leak?",
  "Is there a commitment with a lifecycle and exits?",
];
let qy = 1.7;
qs.forEach((q, i) => {
  box(s3, CX3[0] + 0.2, qy, 0.26, 0.26, C.core);
  txt(s3, String(i + 1), {
    x: CX3[0] + 0.2, y: qy, w: 0.26, h: 0.26, fontSize: 9, color: C.white,
    fontFace: F.dspBold, align: "center", valign: "middle",
  });
  const n = nLines(q, F.txt, 9.2, CW3 - 0.78);
  txt(s3, q, {
    x: CX3[0] + 0.54, y: qy + 0.01, w: CW3 - 0.76, h: n * lineH(F.txt, 9.2) + 0.04,
    fontSize: 9.2, color: C.text, fontFace: F.txt, lineSpacingMultiple: 1.0,
  });
  qy += Math.max(0.34, n * lineH(F.txt, 9.2) + 0.14);
});
box(s3, CX3[0] + 0.2, 4.36, CW3 - 0.4, 1.16, C.ink);
txt(s3, "Four or more yes", {
  x: CX3[0] + 0.34, y: 4.46, w: CW3 - 0.68, h: 0.2, fontSize: 10, color: C.mint, fontFace: F.txtSemi,
});
txt(s3, "Strong fit. Healthcare, telecom, automotive aftersales, field service, energy networks, logistics and utilities all score five or six. Question two carries the most weight: gap analysis earns its keep only where adding supply takes months and money.", {
  x: CX3[0] + 0.34, y: 4.68, w: CW3 - 0.68, h: 0.78, fontSize: 8.6, color: "D8DEE6",
  fontFace: F.txt, lineSpacingMultiple: 1.02,
});

/* where it weakens */
box(s3, CX3[1], 1.08, CW3, 4.62, C.panel, C.rule);
dot(s3, CX3[1] + 0.2, 1.31, C.red, 0.1);
txt(s3, "Where it weakens", {
  x: CX3[1] + 0.4, y: 1.22, w: CW3 - 0.6, h: 0.3, fontSize: 14, color: C.text, fontFace: F.dspBold,
});
const weak = [
  ["Elastic supply", "If capacity appears on demand, the gap closes itself. Commodity cloud does not need this. Credentialed, licensed or capital bound supply does."],
  ["No reachability constraint", "A purely digital good delivered instantly everywhere loses the strongest gap type. Latency, language or jurisdiction can stand in, but the edge is weaker."],
  ["The specification cannot be written", "Capability algebra needs someone to state what an offering requires. When nobody can, that is a business knowledge problem, and it is usually the hardest workshop."],
  ["No identity spine", "Anonymous consumer markets still support geography level aggregates, but person level flow and leakage are lost."],
  ["Small scale", "Twelve suppliers and three sites is a spreadsheet. The graph earns its keep on heterogeneity and volume."],
];
let wy = 1.68;
weak.forEach((wk) => {
  txt(s3, wk[0], {
    x: CX3[1] + 0.2, y: wy, w: CW3 - 0.4, h: 0.19, fontSize: 9.8,
    color: C.red, fontFace: F.txtSemi,
  });
  const n = nLines(wk[1], F.txt, 8.6, CW3 - 0.42);
  txt(s3, wk[1], {
    x: CX3[1] + 0.2, y: wy + 0.2, w: CW3 - 0.4, h: n * lineH(F.txt, 8.6) + 0.04,
    fontSize: 8.6, color: C.grey, fontFace: F.txt, lineSpacingMultiple: 1.0,
  });
  wy += 0.26 + n * lineH(F.txt, 8.6) + 0.12;
});

/* technology */
box(s3, CX3[2], 1.08, CW3, 4.62, C.ink);
dot(s3, CX3[2] + 0.2, 1.31, C.mint, 0.1);
txt(s3, "Technology, honestly", {
  x: CX3[2] + 0.4, y: 1.22, w: CW3 - 0.6, h: 0.3, fontSize: 14, color: C.white, fontFace: F.dspBold,
});
txt(s3, "SWAPPABLE WITHOUT REDESIGN", {
  x: CX3[2] + 0.2, y: 1.64, w: CW3 - 0.4, h: 0.16, fontSize: 7,
  charSpacing: 0.5, color: C.mint, fontFace: F.txtSemi,
});
bullets(s3, [
  "CRM: Salesforce, Dynamics, ServiceNow, SAP. It is a connector",
  "System of record: Epic, Cerner, Amdocs, a dealer management system",
  "Graph store: Neo4j, TigerGraph, Neptune, Memgraph",
  "Cloud and model endpoints, behind the same contract",
], {
  x: CX3[2] + 0.2, y: 1.85, w: CW3 - 0.4, h: 1.2, fontSize: 8.8, color: "D8DEE6",
  fontFace: F.txt, gap: 4, lineSpacingMultiple: 1.0,
});
txt(s3, "GENUINELY COUPLED, SO DECIDE EARLY", {
  x: CX3[2] + 0.2, y: 3.14, w: CW3 - 0.4, h: 0.16, fontSize: 7,
  charSpacing: 0.5, color: "E8A87C", fontFace: F.txtSemi,
});
const coupled = [
  ["Graph engine class", "Variable depth traversal is native in a property graph and hand rolled in SQL. Any technology, yes. Any technology equally well, no."],
  ["The identity spine", "Per industry, and not equal. A VIN is a better key than anything healthcare has."],
  ["The regulatory regime", "HIPAA, GDPR and ePrivacy, or right to repair. The boundary layer stays, its rules do not."],
];
let cy2 = 3.36;
coupled.forEach((c) => {
  txt(s3, c[0], {
    x: CX3[2] + 0.2, y: cy2, w: CW3 - 0.4, h: 0.18, fontSize: 9.4,
    color: C.white, fontFace: F.txtSemi,
  });
  const n = nLines(c[1], F.txt, 8.4, CW3 - 0.42);
  txt(s3, c[1], {
    x: CX3[2] + 0.2, y: cy2 + 0.19, w: CW3 - 0.4, h: n * lineH(F.txt, 8.4) + 0.04,
    fontSize: 8.4, color: "A9B4C2", fontFace: F.txt, lineSpacingMultiple: 1.0,
  });
  cy2 += 0.25 + n * lineH(F.txt, 8.4) + 0.1;
});

strip(s3, 6.0, "Answer to the question as asked: it does not fit everything, and the places it does not are predictable from six questions you can ask in a first meeting.");
box(s3, 0.12, 6.64, W - 0.24, 0.66, C.panel, C.rule);
dot(s3, 0.32, 6.86, C.pack, 0.1);
txt(s3, "The commercial shape: build the core once, sell the pack per industry. A new market is a five part declaration and a set of connectors, not a new build, which is what turns a delivered project into a repeatable practice.", {
  x: 0.54, y: 6.64, w: 12.5, h: 0.66, fontSize: 10.5, color: C.text,
  fontFace: F.txt, valign: "middle",
});

pres.writeFile({ fileName: OUT }).then(() => console.log("wrote", OUT));
