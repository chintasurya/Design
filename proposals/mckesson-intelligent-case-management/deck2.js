const pptxgen = require('pptxgenjs');
const L = require('./lib.js');
const { C, F, FD, M } = L;

const pptx = new pptxgen();
pptx.defineLayout({ name: 'IG', width: 13.333, height: 7.5 });
pptx.layout = 'IG';
pptx.author = 'Insight Global';
pptx.company = 'Insight Global';
pptx.title = 'Intelligent Case Management: The Four Doors';
L.resetPage();

// Queue identity is fixed across every chart in the deck.
const Q = {
  order:     { label: 'Order placement & modification', color: L.SERIES[0], cases: 14660, aht: 400 },
  credits:   { label: 'Credits & disputes',             color: L.SERIES[1], cases: 8170,  aht: 685 },
  account:   { label: 'Account & billing',              color: L.SERIES[2], cases: 5860,  aht: 455 },
  backorder: { label: 'Backorders & availability',      color: L.SERIES[3], cases: 2145,  aht: 455 },
  status:    { label: 'Order status & shipment',        color: L.SERIES[4], cases: 2645,  aht: 305 },
};
const DOOR = [
  { n: '01', name: 'Never arrives',   color: L.SERIES[0] },
  { n: '02', name: 'Resolves itself', color: L.SERIES[1] },
  { n: '03', name: 'One touch',       color: L.SERIES[2] },
  { n: '04', name: 'Expert',          color: L.SERIES[3] },
];

/* ============================== 01  COVER ============================== */
{
  const s = L.newSlide(pptx);
  L.brandOrbs(s, { x: 8.75, y: 1.95, d: 2.9 });
  s.addImage({ path: L.ASSET.wordmark, x: M.l, y: 0.55, w: 2.15, h: 0.537 });
  L.brandDots(s, { x: M.l, y: 2.46 });
  s.addText('MCKESSON EXTENDED CARE  |  SOLUTION PROPOSAL', {
    x: M.l, y: 2.90, w: 10, h: 0.26, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: 11, bold: true, color: C.cyan, charSpacing: 2.6, valign: 'middle',
  });
  s.addText('THE FOUR DOORS', {
    x: M.l, y: 3.26, w: 11, h: 0.82, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: 46, bold: true, color: C.white, charSpacing: 0.6, valign: 'middle',
  });
  s.addText('Intelligent case management for Extended Care email', {
    x: M.l, y: 4.16, w: 10, h: 0.42, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: 17, color: C.txt, valign: 'middle',
  });
  s.addText('Every case takes one of four routes into the operation. The work is moving volume to the cheaper routes, not making the expensive route slightly faster.', {
    x: M.l, y: 4.86, w: 8.1, h: 0.72, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 12.5, color: C.mute, lineSpacing: 18, valign: 'top',
  });
  s.addText('Prepared by Insight Global   ·   September 2026', {
    x: M.l, y: 6.62, w: 7, h: 0.28, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 10, color: C.mute, valign: 'middle',
  });
  s.addNotes('Cover. The four doors is the whole argument. Do not open with technology, open with the idea that most of this volume should not reach a person at all.');
}

/* ============================== 02  THE THESIS ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, { kicker: 'The argument', title: 'Making each case cheaper is the smaller win' });

  L.card(s, { x: M.l, y: top, w: M.w, h: 1.62 });
  s.addText([
    { text: 'Most email automation proposals shave minutes off a case. That is worth having, and it is capped: a person still opens all 33,480 cases a month. ', options: { color: C.txt } },
    { text: 'The larger win is that a quarter of this volume never needs a person at all, and the cases that do should arrive with the work already assembled rather than merely labelled.', options: { color: C.white, bold: true } },
  ], {
    x: M.l + 0.34, y: top + 0.24, w: M.w - 0.68, h: 1.14, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 15, valign: 'middle', lineSpacing: 23,
  });

  const y2 = top + 1.90;
  const cw = (M.w - 0.26) / 2;
  L.card(s, { x: M.l, y: y2, w: cw, h: 2.62 });
  L.label(s, { x: M.l + 0.30, y: y2 + 0.24, w: cw - 0.6, text: 'The usual approach', color: C.mute, size: 10 });
  s.addText('Automate the steps', {
    x: M.l + 0.30, y: y2 + 0.52, w: cw - 0.6, h: 0.36, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 18, bold: true, color: C.mute, valign: 'middle',
  });
  L.bullets(s, {
    x: M.l + 0.30, y: y2 + 1.00, w: cw - 0.6, h: 1.44,
    items: [
      'Classify the case, route it, draft a reply, summarise the thread.',
      'Every case still consumes an agent, so the saving is bounded by handling time.',
      'Ceiling is roughly a quarter of effort, and it arrives only once agents trust the drafts.',
    ],
    size: 10, gap: 8, color: C.mute,
  });

  L.card(s, { x: M.l + cw + 0.26, y: y2, w: cw, h: 2.62, line: '2A5468' });
  L.label(s, { x: M.l + cw + 0.56, y: y2 + 0.24, w: cw - 0.6, text: 'What we propose', color: C.cyan, size: 10 });
  s.addText('Change which door the case takes', {
    x: M.l + cw + 0.56, y: y2 + 0.52, w: cw - 0.6, h: 0.36, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 18, bold: true, color: C.white, valign: 'middle',
  });
  L.bullets(s, {
    x: M.l + cw + 0.56, y: y2 + 1.00, w: cw - 0.6, h: 1.44,
    items: [
      'Sort every case into one of four routes in under a minute, then design volume out of the expensive ones.',
      'A quarter of cases resolve with no agent. Most of the rest arrive pre-resolved for approval.',
      'Effort falls by a projected 44 percent, and the cases that need judgement get more of it, not less.',
    ],
    size: 10, gap: 8,
  });
  L.footer(s);
  s.addNotes('This is the slide that separates this proposal from the rest. Say plainly that the assist-only approach has a ceiling, and that we are proposing to go past it.');
}

/* ============================== 03  EFFORT NOT VOLUME ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Diagnosis  |  01',
    title: 'Count effort, not cases',
    sub: 'Case volume says order placement is the problem. Handling effort says order placement and credits are the problem, in almost equal measure, and that everything else is a rounding error.',
  });

  const chw = 6.55;
  L.card(s, { x: M.l, y: top, w: chw, h: 3.30 });
  L.label(s, { x: M.l + 0.24, y: top + 0.18, w: chw - 0.48, text: 'Agent handling effort, hours per month', color: C.white, size: 9.5 });
  s.addChart(pptx.ChartType.bar, [{
    name: 'Handling hours per month',
    labels: [Q.status.label, Q.backorder.label, Q.account.label, Q.credits.label, Q.order.label],
    values: [224, 271, 741, 1555, 1629],
  }], L.chartBase({
    x: M.l + 0.12, y: top + 0.46, w: chw - 0.24, h: 2.70,
    barDir: 'bar', barGapWidthPct: 90,
    showValue: true, dataLabelPosition: 'outEnd',
    chartColors: [Q.status.color, Q.backorder.color, Q.account.color, Q.credits.color, Q.order.color],
    valAxisHidden: true, valGridLine: { style: 'none' },
    catAxisLabelFontSize: 8.5,
  }));

  const rx = M.l + chw + 0.24, rw = M.w - chw - 0.24;
  L.card(s, { x: rx, y: top, w: rw, h: 3.30 });
  L.label(s, { x: rx + 0.26, y: top + 0.18, w: rw - 0.52, text: 'Share of cases against share of effort', color: C.white, size: 9.5 });
  const rows = [
    ['Order placement', '43.8%', '36.9%', Q.order.color],
    ['Credits & disputes', '24.4%', '35.2%', Q.credits.color],
    ['Account & billing', '17.5%', '16.8%', Q.account.color],
    ['Backorders', '6.4%', '6.1%', Q.backorder.color],
    ['Order status', '7.9%', '5.1%', Q.status.color],
  ];
  L.label(s, { x: rx + 0.90, y: top + 0.50, w: 1.5, text: 'Of cases', color: C.mute, size: 7.5, h: 0.2 });
  L.label(s, { x: rx + 2.40, y: top + 0.50, w: 1.5, text: 'Of effort', color: C.cyan, size: 7.5, h: 0.2 });
  rows.forEach((r, i) => {
    const y = top + 0.76 + i * 0.36;
    s.addShape('roundRect', { x: rx + 0.26, y: y + 0.10, w: 0.10, h: 0.10, rectRadius: 0.02, fill: { color: r[3] }, line: { color: r[3], width: 0 } });
    s.addText(r[0], { x: rx + 0.46, y, w: 1.85, h: 0.30, isTextBox: true, margin: 0, fontFace: F, fontSize: 8.5, color: C.txt, valign: 'middle' });
    s.addText(r[1], { x: rx + 0.90, y, w: 1.5, h: 0.30, isTextBox: true, margin: 0, fontFace: F, fontSize: 9, color: C.mute, align: 'right', valign: 'middle' });
    s.addText(r[2], { x: rx + 2.40, y, w: 1.5, h: 0.30, isTextBox: true, margin: 0, fontFace: F, fontSize: 9, bold: true, color: C.white, align: 'right', valign: 'middle' });
  });

  s.addShape('roundRect', { x: rx + 0.26, y: top + 2.66, w: rw - 0.52, h: 0.46, rectRadius: 0.04, fill: { color: '17222E' }, line: { color: '2A5468', width: 1 } });
  s.addText([
    { text: '72%', options: { bold: true, color: C.cyan, fontSize: 13 } },
    { text: '  of all handling effort sits in two queues', options: { color: C.txt, fontSize: 9.5 } },
  ], { x: rx + 0.44, y: top + 2.66, w: rw - 0.80, h: 0.46, isTextBox: true, margin: 0, fontFace: F, valign: 'middle' });

  L.footnote(s, 'Derived from the queue level volumes and average handling times in the Extended Care operations sample: 33,480 cases per month and 4,419 agent handling hours.');
  L.footer(s);
  s.addNotes('The reframe: credits is a quarter of cases but over a third of effort, because it runs at 11:25 against 6:40. Any design that treats all queues alike is optimising the wrong thing.');
}

/* ============================== 04  THE FOUR DOORS ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'The model',
    title: 'Four doors, and the job is to move volume left',
    sub: 'Every inbound email is sorted into one of four routes within a minute of arriving. Each door costs a different amount to serve, and the design intent is to keep shifting volume toward the cheap ones.',
  });

  const doors = [
    ['01', 'Never arrives', 'The case is not created, because the demand behind it was removed.', [
      'Recurring drivers designed out at source',
      'Self service answers published to the customer',
      'Proactive notification before the customer asks',
    ], 'Zero agent minutes', L.SERIES[0]],
    ['02', 'Resolves itself', 'A deterministic case is answered end to end with no agent involved.', [
      'Order status, tracking and proof of delivery',
      'Published availability and backorder positions',
      'Statement, invoice and document requests',
    ], 'Quality sample only', L.SERIES[1]],
    ['03', 'One touch', 'The case arrives pre-resolved. The agent checks it, approves and sends.', [
      'Clean order placement and modification',
      'Routine account and billing questions',
      'The evidenced credit recommendation',
    ], 'About 30 percent less time', L.SERIES[2]],
    ['04', 'Expert', 'The case needs judgement, but the file is already built.', [
      'Contested credits and pricing disputes',
      'Exceptions, holds and escalations',
      'Anything with conflicting or missing data',
    ], 'Judgement time protected', L.SERIES[3]],
  ];
  const cw = (M.w - 3 * 0.20) / 4, ch = 3.18;
  doors.forEach((d, i) => {
    const x = M.l + i * (cw + 0.20);
    L.card(s, { x, y: top, w: cw, h: ch });
    s.addShape('roundRect', { x: x + 0.22, y: top + 0.22, w: 0.40, h: 0.30, rectRadius: 0.05, fill: { color: d[5] }, line: { color: d[5], width: 0 } });
    s.addText(d[0], { x: x + 0.22, y: top + 0.22, w: 0.40, h: 0.30, isTextBox: true, margin: 0, fontFace: F, fontSize: 11, bold: true, color: '0A0D14', align: 'center', valign: 'middle' });
    s.addText(d[1], {
      x: x + 0.70, y: top + 0.22, w: cw - 0.92, h: 0.30, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 13, bold: true, color: C.white, valign: 'middle',
    });
    s.addText(d[2], {
      x: x + 0.22, y: top + 0.62, w: cw - 0.44, h: 0.62, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9.5, color: C.txt, valign: 'top', lineSpacing: 12.5,
    });
    L.label(s, { x: x + 0.22, y: top + 1.30, w: cw - 0.44, text: 'Typical cases', color: C.mute, size: 7.5, h: 0.18 });
    L.bullets(s, { x: x + 0.22, y: top + 1.54, w: cw - 0.44, h: 1.06, items: d[3], size: 8.5, gap: 4 });
    s.addShape('line', { x: x + 0.22, y: top + 2.70, w: cw - 0.44, h: 0, line: { color: C.line, width: 1 } });
    s.addText(d[4], {
      x: x + 0.22, y: top + 2.78, w: cw - 0.44, h: 0.28, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9, bold: true, color: d[5], valign: 'middle',
    });
    if (i < 3) L.arrow(s, { x: x + cw + 0.02, y: top + 1.50, w: 0.16, h: 0.14 });
  });

  const y2 = top + ch + 0.22;
  s.addShape('roundRect', { x: M.l, y: y2, w: M.w, h: 0.54, rectRadius: 0.04, fill: { color: '17222E' }, line: { color: '2A5468', width: 1 } });
  s.addText([
    { text: 'THE OPERATING GOAL   ', options: { bold: true, color: C.cyan, charSpacing: 1.4, fontSize: 9 } },
    { text: 'Today every case goes through door four. At maturity a quarter goes through door two and over half through door three. Governance is about what moved, not just what was handled.', options: { color: C.txt, fontSize: 9.5 } },
  ], { x: M.l + 0.22, y: y2, w: M.w - 0.44, h: 0.54, isTextBox: true, margin: 0, fontFace: F, valign: 'middle' });
  L.footer(s);
  s.addNotes('Doors are numbered by cost, cheapest first. The arrows run left to right only to show the ladder, not the process order. The monthly review question becomes which cases moved a door to the left.');
}

/* ============================== 05  THE SORTING ENGINE ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'The mechanism',
    title: 'One Flow decides the door, in under a minute',
    sub: 'Email to Case creates the record. A record triggered Flow calls a triage Prompt Template for understanding, then applies deterministic gates that decide which door the case is allowed to take.',
  });

  const cw = (M.w - 2 * 0.22) / 3;
  const cols = [
    ['Understand', 'Prompt Template, called from Flow', [
      'Reads the full thread, grounded on the case, the account, the contact and prior cases.',
      'Returns category, service family, extracted entities such as order, invoice and PO, sentiment, a PHI flag and a summary.',
      'Where generative licensing is absent, Einstein Case Classification predicts the same fields from history.',
    ], C.cyan],
    ['Gate', 'Deterministic Flow rules, not the model', [
      'Is every entity resolved against a real record, and is the data complete and unambiguous?',
      'Is the case type on the approved autonomous list, and is the account free of holds or disputes?',
      'Is there no PHI flag, no complaint language, and no financial authorisation required?',
    ], C.white],
    ['Assign the door', 'The gate answers, the Flow acts', [
      'All gates pass and the type is approved: door two, resolved without an agent.',
      'Understood but needs a person to approve: door three, drafted and evidenced for one touch.',
      'Judgement, money or missing data: door four, routed to an expert with the file assembled.',
    ], C.cyan],
  ];
  cols.forEach((c, i) => {
    const x = M.l + i * (cw + 0.22);
    L.card(s, { x, y: top, w: cw, h: 2.62 });
    L.chip(s, { x: x + 0.24, y: top + 0.22, text: String(i + 1) });
    s.addText(c[0], {
      x: x + 0.68, y: top + 0.22, w: cw - 0.92, h: 0.28, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 13.5, bold: true, color: c[3], valign: 'middle',
    });
    L.label(s, { x: x + 0.24, y: top + 0.58, w: cw - 0.48, text: c[1], color: C.mute, size: 7.5, h: 0.20 });
    L.bullets(s, { x: x + 0.24, y: top + 0.88, w: cw - 0.48, h: 1.60, items: c[2], size: 9, gap: 7 });
    if (i < 2) L.arrow(s, { x: x + cw + 0.03, y: top + 1.20, w: 0.16, h: 0.14 });
  });

  const y2 = top + 2.86;
  const hw = (M.w - 0.24) / 2;
  L.card(s, { x: M.l, y: y2, w: hw, h: 1.46, line: '2A5468' });
  L.label(s, { x: M.l + 0.28, y: y2 + 0.18, w: hw - 0.56, text: 'Why the gate is rules and not the model', color: C.cyan, size: 10 });
  s.addText('The template is allowed to interpret language. It is never allowed to decide that a case may skip a human. That decision is a Flow condition McKesson can read, test and change, which is what makes autonomous handling auditable rather than a matter of trust in a model.', {
    x: M.l + 0.28, y: y2 + 0.50, w: hw - 0.56, h: 0.82, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9.5, color: C.txt, valign: 'top', lineSpacing: 13,
  });

  L.card(s, { x: M.l + hw + 0.24, y: y2, w: hw, h: 1.46 });
  L.label(s, { x: M.l + hw + 0.52, y: y2 + 0.18, w: hw - 0.56, text: 'Default is always the safer door', color: C.white, size: 10 });
  s.addText('Any gate that cannot be answered with certainty sends the case one door to the right. An unresolved order number, a partially matched account or a low confidence score does not produce a guess, it produces a human. Failing safe is cheaper than being wrong once.', {
    x: M.l + hw + 0.52, y: y2 + 0.50, w: hw - 0.56, h: 0.82, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9.5, color: C.txt, valign: 'top', lineSpacing: 13,
  });
  L.footer(s);
  s.addNotes('Compressed deliberately: the mechanism is one slide, not five. The two cards at the bottom are the governance answer and are what security and operations will actually test.');
}

/* ============================== 06  DOOR 02 ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Door 02  |  Resolves itself',
    title: 'A quarter of the volume never needs an agent',
    sub: 'These are cases where the correct answer is a lookup, not a decision. They are answered end to end, in about two minutes, including outside the staffed window.',
  });

  const tw = 7.35;
  s.addTable(
    [[L.th('Case type'), L.th('Monthly volume'), L.th('Why it is safe to automate')],
     [L.td('Order status, tracking and proof of delivery', { color: C.white }), L.td('1,984', { align: 'right', bold: true, color: C.cyan }), L.td('The answer is a field on a record. There is no judgement to exercise.', { color: C.mute })],
     [L.td('Clean order acknowledgement', { color: C.white }), L.td('3,665', { align: 'right', bold: true, color: C.cyan }), L.td('Every line validated against a real SKU, account and price before confirming.', { color: C.mute })],
     [L.td('Published backorder and availability', { color: C.white }), L.td('965', { align: 'right', bold: true, color: C.cyan }), L.td('Stock position and ETA are published data, already given to customers today.', { color: C.mute })],
     [L.td('Statements, invoice copies, documents', { color: C.white }), L.td('1,758', { align: 'right', bold: true, color: C.cyan }), L.td('Retrieval and send. No content is authored and no figure is interpreted.', { color: C.mute })],
     [L.td('TOTAL', { bold: true, color: C.white, fill: { color: '17222E' } }), L.td('8,372', { align: 'right', bold: true, color: C.cyan, fill: { color: '17222E' }, fontSize: 11 }), L.td('25 percent of all monthly email volume', { bold: true, color: C.txt, fill: { color: '17222E' } })]],
    L.tableOpts({ x: M.l, y: top, w: tw, colW: [2.85, 1.35, 3.15], rowH: 0.50, fontSize: 9 })
  );

  const rx = M.l + tw + 0.24, rw = M.w - tw - 0.24;
  L.card(s, { x: rx, y: top, w: rw, h: 3.02, line: '2A5468' });
  L.label(s, { x: rx + 0.28, y: top + 0.20, w: rw - 0.56, text: 'The guardrails that make it safe', color: C.cyan, size: 10 });
  L.bullets(s, {
    x: rx + 0.28, y: top + 0.56, w: rw - 0.56, h: 2.28,
    items: [
      'Each case type is released individually, only after it has run in supervised mode and met an accuracy threshold agreed with McKesson.',
      'Every gate must pass. Any unresolved entity, account hold, dispute, PHI flag or complaint language sends the case to a person instead.',
      'A standing sample of autonomous cases is reviewed by QA every day, and the outcome feeds the release decision for the next case type.',
      'Any case type can be switched back to human handling from a single Flow setting, with no redeployment.',
      'Nothing involving money moving, an account changing or a commitment being made is ever on this list.',
    ],
    size: 9, gap: 7,
  });

  const y2 = top + 3.26;
  const sw = (M.w - 3 * 0.20) / 4;
  [['8,372', 'Cases resolved with no agent each month', C.cyan],
   ['Under 2 min', 'From arrival to the customer having their answer', C.cyan],
   ['24 / 7', 'Door two answers outside the staffed window too', C.cyan],
   ['~330 hrs', 'Agent handling effort removed each month', C.cyan],
  ].forEach((st, i) => L.stat(s, { x: M.l + i * (sw + 0.20), y: y2, w: sw, h: 1.12, value: st[0], caption: st[1], color: st[2], valueSize: 22 }));

  L.footnote(s, 'Volumes are modelled automation rates applied to the queue mix in the operations sample, and are proven case type by case type during the pilot rather than assumed at go live.');
  L.footer(s);
  s.addNotes('The 24/7 point is easy to miss and is worth making: a status request at 2am is answered at 2am, which no amount of shift design achieves.');
}

/* ============================== 07  DOOR 03 ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Door 03  |  One touch',
    title: 'Pre-resolved, not pre-labelled',
    sub: 'This is the difference that matters. Most automation hands the agent a classified case and a blank reply box. Door three hands them a finished answer with the evidence attached, and asks them to approve it.',
  });

  const cw = (M.w - 0.26) / 2;
  L.card(s, { x: M.l, y: top, w: cw, h: 2.74 });
  L.label(s, { x: M.l + 0.30, y: top + 0.22, w: cw - 0.6, text: 'What is on the case when the agent opens it', color: C.white, size: 10 });
  const has = [
    ['The answer', 'A complete drafted reply in the approved Extended Care voice, not a template with gaps to fill.'],
    ['The evidence', 'Order, invoice, shipment and account records already retrieved and linked to the case.'],
    ['The authority', 'The Knowledge article the answer is grounded in, attached and cited so it can be checked in seconds.'],
    ['The context', 'A summary of the thread and of anything the account has raised before.'],
    ['The next step', 'The recommended action and disposition, pre-selected and ready to confirm.'],
  ];
  has.forEach((h, i) => {
    const y = top + 0.58 + i * 0.42;
    s.addText(h[0], { x: M.l + 0.30, y, w: 1.30, h: 0.38, isTextBox: true, margin: 0, fontFace: F, fontSize: 9.5, bold: true, color: C.cyan, valign: 'middle' });
    s.addText(h[1], { x: M.l + 1.64, y, w: cw - 1.94, h: 0.40, isTextBox: true, margin: 0, fontFace: F, fontSize: 8.5, color: C.mute, valign: 'middle', lineSpacing: 11.5 });
  });

  const rx = M.l + cw + 0.26;
  L.card(s, { x: rx, y: top, w: cw, h: 2.74 });
  L.label(s, { x: rx + 0.30, y: top + 0.22, w: cw - 0.6, text: 'What the agent actually does', color: C.white, size: 10 });
  s.addText('Read the summary. Check the draft against the evidence. Correct anything that is wrong. Send.', {
    x: rx + 0.30, y: top + 0.56, w: cw - 0.6, h: 0.46, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: 13, color: C.white, valign: 'top', lineSpacing: 19,
  });
  s.addText('The agent is doing the part of the job that needs a person: deciding whether this answer is right for this customer. They are not doing retrieval, and they are not doing composition.\n\nThat is why the saving is around 30 percent rather than the few percent a template library delivers, and why it arrives without asking anyone to work faster.', {
    x: rx + 0.30, y: top + 1.14, w: cw - 0.6, h: 1.42, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9.5, color: C.mute, valign: 'top', lineSpacing: 13.5,
  });

  const y2 = top + 2.98;
  L.card(s, { x: M.l, y: y2, w: M.w, h: 1.40, line: '2A5468' });
  L.label(s, { x: M.l + 0.30, y: y2 + 0.18, w: 8, text: 'The rule that makes this work', color: C.cyan, size: 10 });
  s.addText([
    { text: 'A draft the agent has to rewrite is worse than no draft at all, because they pay to read it before they pay to replace it. ', options: { color: C.white, bold: true } },
    { text: 'So draft acceptance is measured per case type from the first day, and a case type whose drafts are routinely rewritten is pulled out of door three and fixed before it is put back. Acceptance rate is a signal about the template and the knowledge base, never a target for the agent.', options: { color: C.txt } },
  ], {
    x: M.l + 0.30, y: y2 + 0.50, w: M.w - 0.60, h: 0.78, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 10, valign: 'top', lineSpacing: 14.5,
  });
  L.footer(s);
  s.addNotes('The bottom card is the honest one. Everyone claims drafting saves time. It only saves time if the draft is good enough to approve, so we measure that and act on it.');
}

/* ============================== 08  DOOR 04 ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Door 04  |  Expert',
    title: 'Credits: the one pool automation cannot remove',
    sub: 'Credits and disputes are 35 percent of all handling effort and run at 11:25 a case. None of it can be answered autonomously, because money moves. So the target is not the decision, it is everything around the decision.',
  });

  const cw = (M.w - 0.26) / 2;
  L.card(s, { x: M.l, y: top, w: cw, h: 2.90 });
  L.label(s, { x: M.l + 0.30, y: top + 0.22, w: cw - 0.6, text: 'Where 11 minutes goes today', color: C.mute, size: 10 });
  const spend = [
    ['Assemble the evidence', '5:30', 'Invoice, order, delivery proof, pricing agreement, contract terms, prior credits on the account.'],
    ['Reconcile the claim', '2:45', 'Compare what the customer says against what the records show, and quantify the difference.'],
    ['Decide and authorise', '1:50', 'Apply policy, determine the outcome, and route anything beyond the permission threshold.'],
    ['Write and log', '1:20', 'Compose the explanation, record the disposition, update the case.'],
  ];
  spend.forEach((sp, i) => {
    const y = top + 0.60 + i * 0.56;
    s.addText(sp[0], { x: M.l + 0.30, y, w: 2.3, h: 0.26, isTextBox: true, margin: 0, fontFace: F, fontSize: 9.5, bold: true, color: C.txt, valign: 'middle' });
    s.addText(sp[1], { x: M.l + cw - 1.05, y, w: 0.75, h: 0.26, isTextBox: true, margin: 0, fontFace: FD, fontSize: 11, bold: true, color: i === 0 ? C.amber : C.mute, align: 'right', valign: 'middle' });
    s.addText(sp[2], { x: M.l + 0.30, y: y + 0.24, w: cw - 0.6, h: 0.30, isTextBox: true, margin: 0, fontFace: F, fontSize: 8, color: C.mute, valign: 'top', lineSpacing: 10.5 });
  });

  const rx = M.l + cw + 0.26;
  L.card(s, { x: rx, y: top, w: cw, h: 2.90, line: '2A5468' });
  L.label(s, { x: rx + 0.30, y: top + 0.22, w: cw - 0.6, text: 'The credit case file, built before anyone opens it', color: C.cyan, size: 10 });
  s.addText('Half of a credit case is evidence gathering, and all of it is deterministic retrieval. A Flow assembles the file the moment the case is created.', {
    x: rx + 0.30, y: top + 0.56, w: cw - 0.6, h: 0.44, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9.5, color: C.txt, valign: 'top', lineSpacing: 13,
  });
  L.bullets(s, {
    x: rx + 0.30, y: top + 1.08, w: cw - 0.6, h: 1.66,
    items: [
      'Every referenced document pulled and attached, with the disputed lines identified.',
      'The claim reconciled against the records, with the variance calculated and shown.',
      'Prior credits and disputes on the account surfaced, so a pattern is visible immediately.',
      'The applicable policy retrieved, and a recommended outcome offered with its reasoning.',
      'The authorisation path pre-determined, so anything needing McKesson pricing or AR routes on creation rather than after investigation.',
    ],
    size: 9, gap: 6,
  });

  const y2 = top + 3.14;
  const sw = (M.w - 2 * 0.22) / 3;
  [['11:25 to 8:00', 'Modelled handling time on an assisted credit case', C.cyan],
   ['~440 hrs', 'Monthly effort released from the largest single pool', C.cyan],
   ['Decision unchanged', 'The outcome, the authority and the accountability stay with a person', C.txt],
  ].forEach((st, i) => L.stat(s, { x: M.l + i * (sw + 0.22), y: y2, w: sw, h: 1.06, value: st[0], caption: st[1], color: st[2], valueSize: st[0].length > 12 ? 15 : 20 }));

  L.footnote(s, 'Time split within the 11:25 average is an Insight Global estimate for discussion, tested against real credit cases during discovery before any target is set.');
  L.footer(s);
  s.addNotes('This is the slide a service owner will care about most, because credits is their pain. The message: we are not proposing to automate a credit decision, we are proposing to stop paying experts to hunt for paperwork.');
}

/* ============================== 09  DOOR 01 ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Door 01  |  Never arrives',
    title: 'The cheapest case is the one nobody sends',
    sub: 'Because every case is now classified at the field level, recurring demand becomes visible for the first time. That turns a support queue into a list of problems worth fixing.',
  });

  const cw = (M.w - 2 * 0.22) / 3;
  const routes = [
    ['See the pattern', [
      'Classification is structured data, so the top recurring reasons for contact can be counted rather than guessed at.',
      'Repeat contacts from the same account on the same subject are identified and grouped.',
      'Cases created because an earlier answer was unclear are traced back to the article that failed.',
    ], 'Monthly: the ten drivers generating the most avoidable volume'],
    ['Remove the cause', [
      'A recurring ordering error is a form or catalogue problem, raised to the owning McKesson team with the evidence attached.',
      'A recurring question is a gap in published customer guidance, not a training issue.',
      'A recurring dispute type usually points at an upstream pricing or data problem.',
    ], 'Each driver carries an owner, an action and a measured effect'],
    ['Answer before it is asked', [
      'A backorder, a delay or a substitution can be notified when it happens instead of answered when noticed.',
      'Order confirmations carrying the information customers typically write back for.',
      'Published self service answers for the highest volume questions.',
    ], 'Proactive contact replaces reactive contact'],
  ];
  routes.forEach((r, i) => {
    const x = M.l + i * (cw + 0.22);
    L.card(s, { x, y: top, w: cw, h: 3.10 });
    L.chip(s, { x: x + 0.24, y: top + 0.22, text: String(i + 1) });
    s.addText(r[0], {
      x: x + 0.68, y: top + 0.22, w: cw - 0.92, h: 0.28, isTextBox: true, margin: 0,
      fontFace: FD, fontSize: 13.5, bold: true, color: C.white, valign: 'middle',
    });
    L.bullets(s, { x: x + 0.24, y: top + 0.68, w: cw - 0.48, h: 1.82, items: r[1], size: 9, gap: 7 });
    s.addShape('line', { x: x + 0.24, y: top + 2.58, w: cw - 0.48, h: 0, line: { color: C.line, width: 1 } });
    s.addText(r[2], {
      x: x + 0.24, y: top + 2.66, w: cw - 0.48, h: 0.36, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, italic: true, color: C.cyan, valign: 'top', lineSpacing: 11,
    });
  });

  const y2 = top + 3.34;
  L.card(s, { x: M.l, y: y2, w: M.w, h: 1.02 });
  s.addText([
    { text: 'A deliberately modest number.   ', options: { bold: true, color: C.white } },
    { text: 'We model door one at around 4 percent of volume, roughly 1,300 cases a month, because demand removal depends on McKesson teams outside this service acting on what we surface. We will not claim a saving that is not ours to deliver. The mechanism is in scope from day one; the size of the prize is proven case by case and reported as it lands.', options: { color: C.txt } },
  ], {
    x: M.l + 0.30, y: y2 + 0.18, w: M.w - 0.60, h: 0.70, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 10, valign: 'top', lineSpacing: 14.5,
  });
  L.footer(s);
  s.addNotes('Being conservative here buys credibility for the bigger door two and three numbers. It also sets up the governance ask: McKesson has to act on what we find, or this door stays shut.');
}

/* ============================== 10  CONTROL PLANE ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'The control plane',
    title: 'Priority, routing and SLA under every door',
    sub: 'Standard Service Cloud capability, configured once and applied to every case regardless of which door it takes. None of this requires a generative licence.',
  });

  const cw = (M.w - 3 * 0.18) / 4;
  const blocks = [
    ['Priority', 'Derived, never guessed', [
      'P1 to P4 from business impact, urgency, customer criticality and financial or regulatory risk.',
      'Recommended by the template, set by Flow, changed by an agent only with a recorded reason.',
      'P1 and P2 downgrades need Shift Lead approval. Every change is in the audit history.',
    ]],
    ['Routing', 'Omni Channel, skill aware', [
      'Service family selects the queue; skills based routing requires the matching competency.',
      'Agent capacity is respected, so work is pushed only to someone able to start it.',
      'Higher priority presents first, so a P1 never sits behind a routine request.',
    ]],
    ['SLA', 'Entitlements and Milestones', [
      'Two clocks per case: first meaningful response, and resolution, against business hours.',
      'P1 15 min / 1 hr. P2 30 min / 4 hrs. P3 2 hrs / 1 day. P4 4 hrs / 2 to 3 days.',
      'Resolution keeps running through internal dependencies, with that time measured separately.',
    ]],
    ['Escalation', 'Proportional to the clock', [
      'Milestone time triggers at 50, 70, 85 and 100 percent of the SLA consumed.',
      'Owner, then Shift Lead, then Team Lead and dashboard, then Operations Manager.',
      'Also fires on P1 creation, reopen, repeat follow up, second transfer or a breached dependency.',
    ]],
  ];
  blocks.forEach((b, i) => {
    const x = M.l + i * (cw + 0.18);
    L.card(s, { x, y: top, w: cw, h: 2.86 });
    s.addText(b[0], {
      x: x + 0.24, y: top + 0.20, w: cw - 0.48, h: 0.30, isTextBox: true, margin: 0,
      fontFace: FD, fontSize: 15, bold: true, color: C.cyan, valign: 'middle',
    });
    L.label(s, { x: x + 0.24, y: top + 0.52, w: cw - 0.48, text: b[1], color: C.mute, size: 7.5, h: 0.20 });
    L.bullets(s, { x: x + 0.24, y: top + 0.84, w: cw - 0.48, h: 1.86, items: b[2], size: 8.5, gap: 7 });
  });

  const y2 = top + 3.10;
  const hw = (M.w - 0.24) / 2;
  L.card(s, { x: M.l, y: y2, w: hw, h: 1.26 });
  L.label(s, { x: M.l + 0.28, y: y2 + 0.16, w: hw - 0.56, text: 'Statuses that mean one thing', color: C.white, size: 10 });
  s.addText('Ten defined statuses, each with a single meaning and a defined effect on both clocks. The resolution clock is not paused just because an internal team is involved, because that would hide the real customer experience. Four times are measured on every case: end to end, controllable, dependency and customer wait.', {
    x: M.l + 0.28, y: y2 + 0.46, w: hw - 0.56, h: 0.68, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9, color: C.mute, valign: 'top', lineSpacing: 12.5,
  });

  L.card(s, { x: M.l + hw + 0.24, y: y2, w: hw, h: 1.26 });
  L.label(s, { x: M.l + hw + 0.52, y: y2 + 0.16, w: hw - 0.56, text: 'What McKesson watches', color: C.white, size: 10 });
  s.addText('The operations dashboard adds one view the current service cannot produce: the door mix. Cases by door, this month against last, per queue. That is the measure of whether the operation is actually improving or merely keeping up.', {
    x: M.l + hw + 0.52, y: y2 + 0.46, w: hw - 0.56, h: 0.68, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9, color: C.mute, valign: 'top', lineSpacing: 12.5,
  });
  L.footer(s);
  s.addNotes('Deliberately one slide. This is table stakes, not the differentiator, and spending five slides on it would bury the four doors argument.');
}

/* ============================== 11  TRUST ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Trust and control',
    title: 'Autonomy earns its way in, one case type at a time',
    sub: 'Door two is the only part of this design where no person sees the response before the customer does. It is therefore the part with the most control around it.',
  });

  const lw = 7.6;
  L.card(s, { x: M.l, y: top, w: lw, h: 2.66 });
  L.label(s, { x: M.l + 0.28, y: top + 0.20, w: lw - 0.56, text: 'How a case type gets through door two', color: C.white, size: 10 });
  const gatePath = [
    ['Propose', 'A candidate type is identified from volume and determinism, and agreed with McKesson.'],
    ['Shadow', 'The automation runs and drafts, but a person still sends. Outputs are scored against what the agent actually sent.'],
    ['Prove', 'The type must clear an agreed accuracy threshold over an agreed sample before release is considered.'],
    ['Release', 'Switched on for that type alone. Every other type is unaffected.'],
    ['Watch', 'A daily QA sample, plus automatic rollback triggers on complaint, reopen or correction rate.'],
  ];
  gatePath.forEach((g, i) => {
    const y = top + 0.58 + i * 0.40;
    L.chip(s, { x: M.l + 0.28, y: y + 0.04, text: String(i + 1), w: 0.26, h: 0.26, size: 9.5 });
    s.addText(g[0], { x: M.l + 0.64, y, w: 1.05, h: 0.34, isTextBox: true, margin: 0, fontFace: F, fontSize: 9.5, bold: true, color: C.cyan, valign: 'middle' });
    s.addText(g[1], { x: M.l + 1.74, y, w: lw - 2.02, h: 0.36, isTextBox: true, margin: 0, fontFace: F, fontSize: 8.5, color: C.mute, valign: 'middle', lineSpacing: 11 });
  });

  const rx = M.l + lw + 0.24, rw = M.w - lw - 0.24;
  L.card(s, { x: rx, y: top, w: rw, h: 2.66 });
  L.label(s, { x: rx + 0.28, y: top + 0.20, w: rw - 0.56, text: 'Einstein Trust Layer', color: C.white, size: 10 });
  L.bullets(s, {
    x: rx + 0.28, y: top + 0.56, w: rw - 0.56, h: 1.96,
    items: [
      'Runs inside McKesson tenancy. No McKesson data trains any model.',
      'Zero data retention by the model provider.',
      'PHI and PII masked before the prompt leaves the org, rehydrated in the response.',
      'Dynamic grounding under the running user permissions.',
      'Prompt injection defence: instructions inside a customer email are content, not commands.',
      'Every prompt, output, edit and send retained and reportable.',
    ],
    size: 8.5, gap: 5,
  });

  const y2 = top + 2.90;
  L.card(s, { x: M.l, y: y2, w: M.w, h: 1.44, fill: '1A1226', line: '4A2740' });
  L.label(s, { x: M.l + 0.30, y: y2 + 0.16, w: 9, text: 'Never autonomous, at any phase, whatever the confidence score', color: C.pink, size: 10 });
  const never = ['Credits and returns', 'Pricing adjustments', 'Account holds', 'Billing disputes', 'PHI sensitive cases', 'Complaints', 'Financial authorisation', 'Anything contested', 'Conflicting data', 'Missing data', 'New or unknown case types', 'Regulatory matters'];
  never.forEach((n, i) => {
    const x = M.l + 0.30 + (i % 4) * 3.0;
    const y = y2 + 0.50 + Math.floor(i / 4) * 0.30;
    s.addShape('roundRect', { x, y, w: 2.82, h: 0.25, rectRadius: 0.05, fill: { color: '241733' }, line: { color: '4A2740', width: 1 } });
    s.addText(n, { x: x + 0.12, y, w: 2.58, h: 0.25, isTextBox: true, margin: 0, fontFace: F, fontSize: 8.5, color: C.txt, valign: 'middle' });
  });
  L.footer(s);
  s.addNotes('Lead with the shadow mode step. Nobody is asked to trust this on a promise, they are asked to look at scored output on their own cases before anything is switched on.');
}

/* ============================== 12  THE EFFICIENCY MODEL ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'The numbers  |  01',
    title: 'Handling effort, phase by phase',
    sub: 'Monthly agent handling hours at the current case mix. Each phase is additive, and each is gated: nothing here depends on a saving being claimed before it has been demonstrated.',
  });

  const sw = (M.w - 3 * 0.20) / 4;
  [['4,419', 'Handling hours per month today', C.mute, ''],
   ['4,066', 'After Phase 1 routing and control', C.txt, '-8%'],
   ['3,211', 'After Phase 2 assisted doors three and four', C.cyan, '-27%'],
   ['2,466', 'After Phase 3 autonomous door two', C.cyan, '-44%'],
  ].forEach((st, i) => {
    const x = M.l + i * (sw + 0.20);
    L.card(s, { x, y: top, w: sw, h: 1.14, line: i >= 2 ? '2A5468' : C.line });
    s.addText(st[0], {
      x: x + 0.20, y: top + 0.12, w: sw - 1.0, h: 0.48, isTextBox: true, margin: 0,
      fontFace: FD, fontSize: 25, bold: true, color: st[2], valign: 'middle',
    });
    if (st[3]) s.addText(st[3], {
      x: x + sw - 1.02, y: top + 0.12, w: 0.84, h: 0.48, isTextBox: true, margin: 0,
      fontFace: FD, fontSize: 14, bold: true, color: C.cyan, align: 'right', valign: 'middle',
    });
    s.addText(st[1], {
      x: x + 0.20, y: top + 0.64, w: sw - 0.40, h: 0.40, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, color: C.mute, valign: 'top', lineSpacing: 11,
    });
  });

  const cy = top + 1.36, chh = 2.78, chw = 7.9;
  L.card(s, { x: M.l, y: cy, w: chw, h: chh });
  L.label(s, { x: M.l + 0.24, y: cy + 0.16, w: chw - 0.48, text: 'Monthly handling hours, by queue', color: C.white, size: 9.5 });
  s.addChart(pptx.ChartType.bar, [
    { name: 'Order placement', labels: ['Today', 'Phase 1', 'Phase 2', 'Phase 3'], values: [1629, 1499, 1184, 871] },
    { name: 'Credits & disputes', labels: ['Today', 'Phase 1', 'Phase 2', 'Phase 3'], values: [1555, 1430, 1135, 1113] },
    { name: 'Account & billing', labels: ['Today', 'Phase 1', 'Phase 2', 'Phase 3'], values: [741, 681, 545, 351] },
    { name: 'Backorders', labels: ['Today', 'Phase 1', 'Phase 2', 'Phase 3'], values: [271, 249, 190, 97] },
    { name: 'Order status', labels: ['Today', 'Phase 1', 'Phase 2', 'Phase 3'], values: [224, 206, 157, 35] },
  ], L.chartBase({
    x: M.l + 0.14, y: cy + 0.78, w: chw - 0.28, h: 1.88,
    barDir: 'col', barGrouping: 'stacked', barGapWidthPct: 75,
    chartColors: [Q.order.color, Q.credits.color, Q.account.color, Q.backorder.color, Q.status.color],
    valAxisHidden: true, valGridLine: { style: 'none' },
    catAxisLabelFontSize: 9,
  }));
  L.legendRow(s, {
    x: M.l + 0.30, y: cy + 0.46,
    items: [
      { color: Q.order.color, label: 'Order placement' },
      { color: Q.credits.color, label: 'Credits & disputes' },
      { color: Q.account.color, label: 'Account & billing' },
      { color: Q.backorder.color, label: 'Backorders' },
      { color: Q.status.color, label: 'Order status' },
    ],
  });

  const rx = M.l + chw + 0.24, rw = M.w - chw - 0.24;
  L.card(s, { x: rx, y: cy, w: rw, h: chh, line: '2A5468' });
  L.label(s, { x: rx + 0.28, y: cy + 0.18, w: rw - 0.56, text: 'What the shape tells you', color: C.cyan, size: 10 });
  L.bullets(s, {
    x: rx + 0.28, y: cy + 0.54, w: rw - 0.56, h: 2.06,
    items: [
      'Order status all but disappears. It is small in effort but it is the proof that door two works, which is why it is the first case type we pilot.',
      'Order placement falls hardest in absolute terms, because it is large and much of it is clean enough for doors two and three.',
      'Credits barely moves between Phase 2 and Phase 3. There is no door two for credits, and there should not be. It ends as the largest remaining pool, which is the correct outcome: expert time spent on expert work.',
    ],
    size: 9, gap: 8,
  });

  L.footnote(s, 'Modelled from the queue mix and handling times in the operations sample. Door mix rates are Insight Global assumptions for discussion, re-derived from McKesson case data during discovery and re-baselined against actual performance before any target is committed.');
  L.footer(s);
  s.addNotes('If challenged on the 44 percent, go to the credits bar: we are explicitly not claiming automation of the hardest third. That is what makes the rest believable.');
}

/* ============================== 13  VOLUME MIGRATION ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'The numbers  |  02',
    title: 'The door mix, and what it does to response time',
    sub: 'Effort is the cost story. The door mix is the service story, because a case that does not wait for an agent does not wait at all.',
  });

  const chw = 6.6, chh = 3.08;
  L.card(s, { x: M.l, y: top, w: chw, h: chh });
  L.label(s, { x: M.l + 0.24, y: top + 0.16, w: chw - 0.48, text: 'Monthly cases by door', color: C.white, size: 9.5 });
  s.addChart(pptx.ChartType.bar, [
    { name: 'Door 1 never arrives', labels: ['Today', 'Phase 2', 'Phase 3'], values: [0, 0, 1311] },
    { name: 'Door 2 resolves itself', labels: ['Today', 'Phase 2', 'Phase 3'], values: [0, 0, 8372] },
    { name: 'Door 3 one touch', labels: ['Today', 'Phase 2', 'Phase 3'], values: [0, 27658, 17975] },
    { name: 'Door 4 expert', labels: ['Today', 'Phase 2', 'Phase 3'], values: [33480, 5822, 5822] },
  ], L.chartBase({
    x: M.l + 0.14, y: top + 0.76, w: chw - 0.28, h: 2.02,
    barDir: 'col', barGrouping: 'stacked', barGapWidthPct: 85,
    chartColors: DOOR.map(d => d.color),
    valAxisHidden: true, valGridLine: { style: 'none' },
    catAxisLabelFontSize: 9,
  }));
  L.legendRow(s, {
    x: M.l + 0.30, y: top + 0.44, size: 8,
    items: DOOR.map(d => ({ color: d.color, label: d.n + ' ' + d.name })),
  });

  const rx = M.l + chw + 0.24, rw = M.w - chw - 0.24;
  L.label(s, { x: rx, y: top, w: rw, text: 'What that does to the customer', color: C.white, size: 10 });
  const rt = [
    ['Acknowledgement', 'Hours, if at all', 'Seconds', 'Phase 1'],
    ['Door two full answer', 'Same as any case', 'Under 2 minutes', 'Phase 3'],
    ['P1 detection', 'When an agent opens it', 'Under 60 seconds', 'Phase 1'],
    ['First meaningful reply, P2', 'Set by queue depth', '30 minute target', 'Phase 2'],
    ['Cases not waiting for an agent', 'None', '25 percent of volume', 'Phase 3'],
  ];
  L.label(s, { x: rx + 2.30, y: top + 0.30, w: 1.4, text: 'Today', color: C.mute, size: 7, h: 0.18 });
  L.label(s, { x: rx + 3.60, y: top + 0.30, w: 1.5, text: 'Designed', color: C.cyan, size: 7, h: 0.18 });
  rt.forEach((r, i) => {
    const y = top + 0.54 + i * 0.50;
    L.card(s, { x: rx, y, w: rw, h: 0.44, fill: C.panel2 });
    s.addText(r[0], { x: rx + 0.18, y, w: 2.10, h: 0.44, isTextBox: true, margin: 0, fontFace: F, fontSize: 8.5, bold: true, color: C.txt, valign: 'middle', lineSpacing: 10.5 });
    s.addText(r[1], { x: rx + 2.30, y, w: 1.28, h: 0.44, isTextBox: true, margin: 0, fontFace: F, fontSize: 8, color: C.mute, valign: 'middle', lineSpacing: 10.5 });
    s.addText(r[2], { x: rx + 3.60, y, w: 1.50, h: 0.44, isTextBox: true, margin: 0, fontFace: F, fontSize: 8.5, bold: true, color: C.cyan, valign: 'middle', lineSpacing: 10.5 });
    s.addText(r[3], { x: rx + rw - 0.80, y, w: 0.64, h: 0.44, isTextBox: true, margin: 0, fontFace: F, fontSize: 7.5, color: C.mute, align: 'right', valign: 'middle' });
  });

  const y2 = top + 3.32;
  s.addShape('roundRect', { x: M.l, y: y2, w: M.w, h: 0.54, rectRadius: 0.04, fill: { color: '17222E' }, line: { color: '2A5468', width: 1 } });
  s.addText([
    { text: 'THE POINT   ', options: { bold: true, color: C.cyan, charSpacing: 1.4, fontSize: 9 } },
    { text: 'Handling time reduction is bounded by how fast a person can work. Response time reduction is not, because a case that takes door two is never in a queue. That is why the door mix, and not average handling time, is the number we propose to govern against.', options: { color: C.txt, fontSize: 9.5 } },
  ], { x: M.l + 0.22, y: y2, w: M.w - 0.44, h: 0.54, isTextBox: true, margin: 0, fontFace: F, valign: 'middle' });
  L.footer(s);
  s.addNotes('Today bar is deliberately a single block: every case handled by a person. The visual migration across the three bars is the argument in one picture.');
}

/* ============================== 14  PHASING ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Delivery',
    title: 'What opens each door',
    sub: 'Phase 1 uses only what Service Cloud already includes, so the operation improves before the licensing question is answered. Each later phase has an entry condition, not a date.',
  });

  const phases = [
    ['PHASE 1', 'Doors three and four, controlled', 'No new licensing', L.SERIES[0], [
      'Email to Case, thread matching, duplicate handling, auto acknowledgement',
      'Record triggered Flow orchestration across the whole case lifecycle',
      'Rule based classification, priority and the deterministic gates',
      'Omni Channel skills routing, Entitlements, Milestones, proportional escalation',
      'Knowledge structure, Quick Text, Macros, standard response library',
      'Operations dashboards including the door mix view',
    ], 'Entry: Salesforce access and a sandbox. Nothing else.'],
    ['PHASE 2', 'Door three becomes one touch', 'Einstein or Agentforce licence', L.SERIES[2], [
      'Triage Prompt Template: classification, entities, sentiment, summary',
      'Draft response Prompt Template, grounded in Knowledge and order data',
      'The credit case file: automated evidence assembly and reconciliation',
      'Case and thread summarisation for handover and reporting',
      'Draft acceptance measurement per case type, feeding template tuning',
      'Shadow mode scoring on every candidate door two case type',
    ], 'Entry: licence confirmed, security approved, Knowledge base ready.'],
    ['PHASE 3', 'Door two opens, one type at a time', 'Agentforce, scoped separately', L.SERIES[1], [
      'Order status, tracking and proof of delivery first',
      'Then document and statement requests',
      'Then published backorder and availability positions',
      'Then clean, fully validated order acknowledgement',
      'Door one demand removal running in parallel from Phase 2 data',
      'Daily QA sampling and automatic rollback triggers throughout',
    ], 'Entry: each type clears its agreed accuracy threshold in shadow mode.'],
  ];
  const cw = (M.w - 2 * 0.24) / 3;
  phases.forEach((p, i) => {
    const x = M.l + i * (cw + 0.24);
    L.card(s, { x, y: top, w: cw, h: 4.02 });
    s.addText(p[0], {
      x: x + 0.28, y: top + 0.20, w: cw - 0.56, h: 0.24, isTextBox: true, margin: 0,
      fontFace: FD, fontSize: 10, bold: true, color: p[3], charSpacing: 1.6, valign: 'middle',
    });
    s.addText(p[1], {
      x: x + 0.28, y: top + 0.46, w: cw - 0.56, h: 0.34, isTextBox: true, margin: 0,
      fontFace: FD, fontSize: 14, bold: true, color: C.white, valign: 'middle',
    });
    s.addShape('roundRect', { x: x + 0.28, y: top + 0.86, w: cw - 0.56, h: 0.30, rectRadius: 0.05, fill: { color: C.panel2 }, line: { color: p[3], width: 1 } });
    s.addText(p[2], {
      x: x + 0.40, y: top + 0.86, w: cw - 0.80, h: 0.30, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, bold: true, color: p[3], valign: 'middle',
    });
    L.bullets(s, { x: x + 0.28, y: top + 1.30, w: cw - 0.56, h: 1.92, items: p[4], size: 8.5, gap: 5 });
    s.addShape('line', { x: x + 0.28, y: top + 3.34, w: cw - 0.56, h: 0, line: { color: C.line, width: 1 } });
    s.addText(p[5], {
      x: x + 0.28, y: top + 3.44, w: cw - 0.56, h: 0.50, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, italic: true, color: C.cyan, valign: 'top', lineSpacing: 11.5,
    });
  });
  L.footer(s);
  s.addNotes('The entry conditions at the bottom are the important line on each card. No phase has a date attached, because a date would be a commitment we cannot control.');
}

/* ============================== 15  WHAT WE NEED ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Next steps',
    title: 'What opens this up',
    sub: 'Phase 1 needs access and discovery, nothing more. The items below are what turn each later door from a design into a delivered capability.',
  });

  const groups = [
    ['Needed for Phase 1', C.cyan, [
      'Salesforce access, permissions and a configuration sandbox',
      'Confirmation of the Extended Care mailboxes in scope',
      'Historical case data to re-derive the door mix from reality',
      'Process owners and SMEs for discovery',
    ]],
    ['Needed for Phase 2', L.SERIES[2], [
      'Confirmation of current Einstein and Agentforce entitlement',
      'Security approval for generative features on PHI adjacent data',
      'Existing Knowledge articles, SOPs and email templates',
      'Read access to order, shipment and invoice data for grounding',
    ]],
    ['Needed for Phase 3', L.SERIES[1], [
      'Agreement on the first autonomous case type and its accuracy threshold',
      'Sign off on the deterministic gates and the never autonomous list',
      'An agreed shadow mode period and sample size',
      'A named McKesson approver for each case type release',
    ]],
    ['Needed for door one', L.SERIES[3], [
      'Named owners in the teams that own the upstream causes',
      'A route to raise catalogue, pricing and data defects with evidence',
      'Willingness to publish customer facing guidance we identify as missing',
      'A standing item in the monthly review for demand removal',
    ]],
  ];
  const cw = (M.w - 0.22) / 2, ch = 1.86;
  groups.forEach((g, i) => {
    const x = M.l + (i % 2) * (cw + 0.22);
    const y = top + Math.floor(i / 2) * (ch + 0.22);
    L.card(s, { x, y, w: cw, h: ch });
    s.addText(g[0], {
      x: x + 0.28, y: y + 0.18, w: cw - 0.56, h: 0.30, isTextBox: true, margin: 0,
      fontFace: FD, fontSize: 12.5, bold: true, color: g[1], valign: 'middle',
    });
    L.bullets(s, { x: x + 0.28, y: y + 0.54, w: cw - 0.56, h: 1.22, items: g[2], size: 9, gap: 5 });
  });

  const y2 = top + 2 * (ch + 0.22) + 0.04;
  s.addShape('roundRect', { x: M.l, y: y2, w: M.w, h: 0.60, rectRadius: 0.04, fill: { color: '17222E' }, line: { color: C.cyan, width: 1 } });
  s.addText([
    { text: 'PROPOSED NEXT STEP   ', options: { bold: true, color: C.cyan, charSpacing: 1.4, fontSize: 9 } },
    { text: 'A half day working session on your own case data: we sort a real month of Extended Care email into the four doors with you, and you see the actual mix rather than our modelled one before anything is committed.', options: { color: C.txt, fontSize: 9.5 } },
  ], { x: M.l + 0.22, y: y2, w: M.w - 0.44, h: 0.60, isTextBox: true, margin: 0, fontFace: F, valign: 'middle', lineSpacing: 13 });
  L.footer(s);
  s.addNotes('The next step is the strongest close available: we are offering to test our own numbers against their data before they commit to anything.');
}

/* ============================== 16  CLOSE ============================== */
{
  const s = L.newSlide(pptx);
  L.brandOrbs(s, { x: 9.05, y: 2.30, d: 2.65 });
  s.addImage({ path: L.ASSET.wordmark, x: M.l, y: 0.55, w: 2.15, h: 0.537 });
  L.brandDots(s, { x: M.l, y: 2.62 });
  s.addText('THE FOUR DOORS', {
    x: M.l, y: 3.06, w: 10, h: 0.30, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: 11, bold: true, color: C.cyan, charSpacing: 2.4, valign: 'middle',
  });
  s.addText('Stop making the queue faster.\nMake it smaller.', {
    x: M.l, y: 3.44, w: 10.5, h: 1.40, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: 34, bold: true, color: C.white, lineSpacing: 42, valign: 'top',
  });
  s.addText('A quarter of the volume resolved without an agent. Most of the rest arriving pre-resolved. The cases that genuinely need judgement getting more of it, not less.', {
    x: M.l, y: 5.02, w: 8.5, h: 0.70, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 12.5, color: C.mute, lineSpacing: 18, valign: 'top',
  });
  s.addText('Thank you', {
    x: M.l, y: 6.52, w: 6, h: 0.32, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: 13, bold: true, color: C.txt, valign: 'middle',
  });
  s.addNotes('Close on the line: stop making the queue faster, make it smaller.');
}

/* ============================== WRITE ============================== */
pptx.writeFile({ fileName: 'McKesson_Four_Doors.pptx' })
  .then(f => console.log('written:', f))
  .catch(e => { console.error('FAILED', e); process.exit(1); });
