const pptxgen = require('pptxgenjs');
const L = require('./lib.js');
const { C, F, M } = L;

const pptx = new pptxgen();
pptx.defineLayout({ name: 'IG', width: 13.333, height: 7.5 });
pptx.layout = 'IG';
pptx.author = 'Insight Global';
pptx.company = 'Insight Global';
pptx.title = 'Intelligent Case Management for McKesson Extended Care';

/* ============================== 01  COVER ============================== */
{
  const s = L.newSlide(pptx);
  L.brandOrbs(s, { x: 8.55, y: 1.85, d: 2.95 });
  s.addImage({ path: L.ASSET.wordmark, x: M.l, y: 0.55, w: 2.15, h: 0.537 });
  L.brandDots(s, { x: M.l, y: 2.42 });

  s.addText('MCKESSON EXTENDED CARE  |  SOLUTION PROPOSAL', {
    x: M.l, y: 2.86, w: 10, h: 0.26, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 11, bold: true, color: C.cyan, charSpacing: 2.6, valign: 'middle',
  });
  s.addText('INTELLIGENT CASE\nMANAGEMENT', {
    x: M.l, y: 3.22, w: 11, h: 1.62, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 44, bold: true, color: C.white, charSpacing: 0.6,
    lineSpacing: 50, valign: 'top',
  });
  s.addText('Salesforce native email case automation. Every inbound case classified, prioritised, routed, timed, summarised and drafted before an agent opens it.', {
    x: M.l, y: 5.05, w: 8.5, h: 0.7, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 13, color: C.mute, lineSpacing: 19, valign: 'top',
  });
  s.addText('Prepared by Insight Global   ·   September 2026', {
    x: M.l, y: 6.62, w: 7, h: 0.28, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 10, color: C.mute, valign: 'middle',
  });
  s.addNotes('Cover. This is a solution and business value proposal. Commercials are handled separately. The single message: the work of reading, classifying, prioritising, routing and drafting is moved into Salesforce, so agent time goes to judgement rather than administration.');
}

/* ============================== 02  AGENDA ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Agenda',
    title: 'What this proposal covers',
    sub: 'A Salesforce native operating model for Extended Care email, built on Flow Builder, Prompt Templates and Agentforce, delivered in phases so value lands before any new licensing is required.',
  });

  const items = [
    ['01', 'Where the effort goes today', 'The manual work sitting between an inbound email and a customer reply, and what it costs in handling time.'],
    ['02', 'The intelligent case management model', 'Six stages from capture to continuous learning, and the Salesforce architecture that delivers them.'],
    ['03', 'Classification, priority and SLA', 'A customer service taxonomy, a priority formula, and SLA clocks enforced by Entitlements and Milestones.'],
    ['04', 'Draft, summarise and assist', 'Prompt Templates that summarise the thread, ground the answer in Knowledge and draft the reply for review.'],
    ['05', 'Trust, guardrails and phased delivery', 'PHI handling, the human approval boundary, and a three phase roadmap gated on licensing and readiness.'],
    ['06', 'Business value', 'Modelled handling time reduction, response time impact, and what we need from McKesson to deliver it.'],
  ];
  const cw = 3.93, ch = 1.92, gx = 0.22, gy = 0.24;
  items.forEach((it, i) => {
    const x = M.l + (i % 3) * (cw + gx);
    const y = top + Math.floor(i / 3) * (ch + gy);
    L.card(s, { x, y, w: cw, h: ch });
    L.chip(s, { x: x + 0.24, y: y + 0.24, text: it[0] });
    s.addText(it[1], {
      x: x + 0.24, y: y + 0.62, w: cw - 0.48, h: 0.54, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 12.5, bold: true, color: C.white, valign: 'top', lineSpacing: 16,
    });
    s.addText(it[2], {
      x: x + 0.24, y: y + 1.18, w: cw - 0.48, h: 0.62, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9, color: C.mute, valign: 'top', lineSpacing: 12.5,
    });
  });
  L.footer(s);
  s.addNotes('Agenda. Sections 1 and 6 are the business case. Sections 2 to 5 are the solution. If time is short, run 3, 5, 6, 13, 17, 21 and 22.');
}

/* ============================== 03  CASE FOR CHANGE ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'The case for change  |  01',
    title: 'Where the effort goes today',
    sub: 'Every one of roughly 33,000 monthly email cases is read, classified, prioritised and answered by hand. Most of that effort is administration, not judgement.',
  });

  const sw = 2.93, sg = 0.18;
  const stats = [
    ['33,480', 'Email cases offered per month across the Extended Care queues', C.cyan],
    ['8:15', 'Blended average handling time per case, all queues', C.cyan],
    ['11:25', 'Average handling time on credits and disputes, against 6:40 for order placement', C.amber],
    ['~29%', 'Share of email volume made up of credit requests and disputes', C.pink],
  ];
  stats.forEach((st, i) => L.stat(s, {
    x: M.l + i * (sw + sg), y: top, w: sw, h: 1.26, value: st[0], caption: st[1], color: st[2],
  }));

  const y2 = top + 1.50;
  const lw = 7.3, rw = M.w - lw - 0.24;
  L.card(s, { x: M.l, y: y2, w: lw, h: 2.72 });
  L.label(s, { x: M.l + 0.26, y: y2 + 0.22, w: lw - 0.5, text: 'Six manual steps before the customer hears anything', color: C.white, size: 11 });
  const steps = [
    ['1', 'Read the thread', 'Work out what is actually being asked, across forwarded replies and attachments.'],
    ['2', 'Classify and prioritise', 'Decide the case type and how urgent it is, by judgement rather than rule.'],
    ['3', 'Find the owner', 'Work out which team or individual should hold it, and whether it needs pricing or AR.'],
    ['4', 'Assemble the context', 'Open the account, the order, the invoice and any prior case history.'],
    ['5', 'Find the policy', 'Search Knowledge or ask a colleague for the correct treatment.'],
    ['6', 'Compose the reply', 'Write the response from scratch or adapt a template by hand.'],
  ];
  steps.forEach((st, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M.l + 0.26 + col * 3.46;
    const y = y2 + 0.66 + row * 0.66;
    L.chip(s, { x, y: y + 0.03, text: st[0], w: 0.26, h: 0.26, size: 9.5 });
    s.addText(st[1], {
      x: x + 0.36, y, w: 2.95, h: 0.22, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 10, bold: true, color: C.txt, valign: 'middle',
    });
    s.addText(st[2], {
      x: x + 0.36, y: y + 0.22, w: 2.95, h: 0.36, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, color: C.mute, valign: 'top', lineSpacing: 10.5,
    });
  });

  L.card(s, { x: M.l + lw + 0.24, y: y2, w: rw, h: 2.72 });
  L.label(s, { x: M.l + lw + 0.5, y: y2 + 0.22, w: rw - 0.5, text: 'What it costs', color: C.white, size: 11 });
  L.bullets(s, {
    x: M.l + lw + 0.5, y: y2 + 0.60, w: rw - 0.5, h: 2.02,
    items: [
      'Around two minutes per case is spent on triage that follows rules a system can apply.',
      'First response time is set by queue depth, not by urgency. A P1 waits behind routine status requests.',
      'Response quality varies with who picks the case up, because policy lives in people rather than in the workflow.',
      'SLA breaches are seen after the fact in reporting, not prevented while the clock is still running.',
      'Knowledge gaps stay invisible, because nobody records the article that was missing.',
    ],
    size: 9, gap: 7,
  });

  L.footnote(s, 'Volume, handling time and case mix taken from the Extended Care operations sample in the current proposal. Step level timings are Insight Global estimates, validated during the baseline period.');
  L.footer(s);
  s.addNotes('Anchor the business case in their own numbers. The point of the six steps is that five of them are administration. Only step six needs an expert.');
}

/* ============================== 04  BEFORE / AFTER ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'The case for change  |  02',
    title: 'From a manual queue to intelligent case management',
    sub: 'The same team, the same Salesforce org, the same case types. What changes is how much of the case is already done when an agent opens it.',
  });

  const rows = [
    ['Case creation',   'Email lands in a shared queue and waits to be picked up in arrival order.', 'Email to Case creates the record, matches the thread and acknowledges the customer in seconds.'],
    ['Classification',  'Agent reads the thread and chooses a case type from experience.',            'Category, service family and entities are extracted and written to the case automatically.'],
    ['Priority',        'Set by whoever opens the case, if it is set at all.',                        'Recommended from impact, urgency, customer tier and risk, then enforced by rule.'],
    ['Assignment',      'Manual pickup, or a flat assignment rule that ignores skill.',               'Skills based routing to the right queue and agent, with live capacity awareness.'],
    ['SLA',             'Measured in a report after the month has closed.',                           'Two live clocks per case, with escalation fired at 50, 70, 85 and 100 percent consumed.'],
    ['The response',    'Written from scratch or adapted from a template by hand.',                   'A grounded draft is waiting, with the Knowledge article and order context attached.'],
    ['Handover',        'A free text note, if the outgoing agent has time to write one.',             'A generated case summary with owner, status, last action and next action.'],
  ];

  const hy = top, rh = 0.60;
  const cw = [2.35, 4.85, 5.03];
  const cx = [M.l, M.l + cw[0], M.l + cw[0] + cw[1]];
  L.label(s, { x: cx[1] + 0.16, y: hy, w: cw[1], text: 'Today', color: C.mute, size: 9.5 });
  L.label(s, { x: cx[2] + 0.16, y: hy, w: cw[2], text: 'With intelligent case management', color: C.cyan, size: 9.5 });

  rows.forEach((r, i) => {
    const y = hy + 0.34 + i * rh;
    s.addShape('rect', { x: cx[2], y, w: cw[2], h: rh, fill: { color: i % 2 ? '141C28' : '111826' }, line: { color: C.line, width: 0.75 } });
    s.addShape('rect', { x: cx[1], y, w: cw[1], h: rh, fill: { color: i % 2 ? '12151E' : C.bg }, line: { color: C.line, width: 0.75 } });
    s.addText(r[0], {
      x: cx[0], y, w: cw[0] - 0.14, h: rh, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 10, bold: true, color: C.white, valign: 'middle',
    });
    s.addText(r[1], {
      x: cx[1] + 0.16, y, w: cw[1] - 0.32, h: rh, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9, color: C.mute, valign: 'middle', lineSpacing: 12,
    });
    s.addText(r[2], {
      x: cx[2] + 0.16, y, w: cw[2] - 0.32, h: rh, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9, color: C.txt, valign: 'middle', lineSpacing: 12,
    });
  });
  L.footer(s);
  s.addNotes('Do not read this line by line. Land the shape of it: every row moves work from the agent to the platform, and the right hand column is all standard Salesforce behaviour.');
}

/* ============================== 05  SOLUTION AT A GLANCE ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'The solution  |  01',
    title: 'Six stages, one automated case lifecycle',
    sub: 'Each stage is a defined Salesforce capability rather than a manual habit, so the behaviour is consistent on every case, on every shift, at every volume.',
  });

  const stages = [
    ['01', 'Capture', 'The email becomes a case, threaded to its history and acknowledged immediately.', 'Email to Case  ·  Auto Response  ·  Thread matching'],
    ['02', 'Understand', 'The thread is read, classified and summarised, with order and account entities extracted.', 'Record Triggered Flow  ·  Prompt Template: Triage'],
    ['03', 'Route', 'The case reaches an agent with the right skill, in the right queue, with capacity to take it.', 'Omni Channel  ·  Skills based routing  ·  Queues'],
    ['04', 'Time', 'Two SLA clocks start against business hours, with escalation staged before breach.', 'Entitlements  ·  Milestones  ·  Time triggers'],
    ['05', 'Assist', 'A grounded draft reply and a case summary are waiting when the agent opens the record.', 'Prompt Template: Draft  ·  Knowledge grounding'],
    ['06', 'Learn', 'Closure, feedback and quality findings feed the knowledge base and the prompt library.', 'Surveys  ·  Dashboards  ·  Improvement backlog'],
  ];
  const cw = 3.93, ch = 2.02, gx = 0.22, gy = 0.22;
  stages.forEach((st, i) => {
    const x = M.l + (i % 3) * (cw + gx);
    const y = top + Math.floor(i / 3) * (ch + gy);
    L.card(s, { x, y, w: cw, h: ch });
    L.chip(s, { x: x + 0.24, y: y + 0.22, text: st[0] });
    s.addText(st[1], {
      x: x + 0.68, y: y + 0.22, w: cw - 0.92, h: 0.28, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 14, bold: true, color: C.white, valign: 'middle',
    });
    s.addText(st[2], {
      x: x + 0.24, y: y + 0.64, w: cw - 0.48, h: 0.66, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9.5, color: C.txt, valign: 'top', lineSpacing: 13,
    });
    L.pill(s, { x: x + 0.24, y: y + 1.38, w: cw - 0.48, h: 0.44, text: st[3], color: C.cyan, size: 8 });
  });
  L.footer(s);
  s.addNotes('The six stage frame is used consistently for the rest of the deck. Stages 1, 3, 4 and 6 need no new licensing. Stages 2 and 5 are where Prompt Templates and Agentforce come in.');
}

/* ============================== 06  ARCHITECTURE ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'The solution  |  02',
    title: 'How it works inside McKesson Salesforce',
    sub: 'One record triggered Flow orchestrates the case from creation to closure, calling Prompt Templates where language understanding is needed and deterministic rules where policy must be certain.',
  });

  s.addShape('roundRect', { x: M.l, y: top, w: M.w, h: 0.34, rectRadius: 0.04, fill: { color: '121A2A' }, line: { color: C.line, width: 1 } });
  s.addText('SALESFORCE SERVICE CLOUD  ·  McKesson org  ·  Extended Care email queues', {
    x: M.l + 0.2, y: top, w: M.w - 0.4, h: 0.34, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 8.5, bold: true, color: C.cyan, charSpacing: 1.4, valign: 'middle',
  });

  const cols = [
    ['01', 'CAPTURE',      ['Email to Case', 'Thread ID matching', 'Duplicate check', 'Auto acknowledgement']],
    ['02', 'UNDERSTAND',   ['Record Triggered Flow', 'Prompt Template: Triage', 'Deterministic guardrails', 'Entity extraction']],
    ['03', 'ROUTE & TIME', ['Omni Channel routing', 'Skills and capacity', 'Entitlement Process', 'First response + resolution']],
    ['04', 'ASSIST',       ['Prompt Template: Draft', 'Prompt Template: Summary', 'Knowledge grounding', 'Quick Text and Macros']],
    ['05', 'CLOSE & LEARN',['Agent reviews and sends', 'Survey on closure', 'Milestone dashboards', 'Improvement backlog']],
  ];
  const cy = top + 0.50, chh = 3.18;
  const ccw = (M.w - 4 * 0.40) / 5;
  cols.forEach((col, i) => {
    const x = M.l + i * (ccw + 0.40);
    L.card(s, { x, y: cy, w: ccw, h: chh });
    L.chip(s, { x: x + 0.16, y: cy + 0.16, text: col[0], w: 0.3, h: 0.25, size: 9 });
    s.addText(col[1], {
      x: x + 0.52, y: cy + 0.16, w: ccw - 0.68, h: 0.25, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9.5, bold: true, color: C.white, charSpacing: 0.6, valign: 'middle',
    });
    col[2].forEach((p, j) => {
      L.pill(s, { x: x + 0.16, y: cy + 0.56 + j * 0.62, w: ccw - 0.32, h: 0.52, text: p, color: C.txt, size: 8.5 });
    });
    if (i < 4) L.arrow(s, { x: x + ccw + 0.06, y: cy + chh / 2 - 0.09, w: 0.28, h: 0.18 });
  });

  const ty = cy + chh + 0.20;
  s.addShape('roundRect', { x: M.l, y: ty, w: M.w, h: 0.56, rectRadius: 0.04, fill: { color: '1A1226' }, line: { color: '3D2A4E', width: 1 } });
  s.addText([
    { text: 'EINSTEIN TRUST LAYER   ', options: { bold: true, color: C.pink, charSpacing: 1.4, fontSize: 9 } },
    { text: 'Zero data retention  ·  PHI and PII masking  ·  Dynamic grounding  ·  Prompt injection defence  ·  Toxicity scoring  ·  Full audit trail on every generated output', options: { color: C.txt, fontSize: 9 } },
  ], {
    x: M.l + 0.2, y: ty, w: M.w - 0.4, h: 0.56, isTextBox: true, margin: 0,
    fontFace: F, valign: 'middle',
  });

  L.footnote(s, 'Stages 01, 03 and 05 use capability included in Service Cloud. The Prompt Template components in stages 02 and 04 require Einstein or Agentforce licensing, confirmed with McKesson before Phase 2.');
  L.footer(s);
  s.addNotes('The key architectural point: one Flow is the spine. Prompt Templates are called by the Flow, they do not own the process. That is what keeps policy deterministic and auditable.');
}

/* ============================== 07  CAPTURE & UNDERSTAND ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Stages 01 and 02',
    title: 'Capture the email, then understand it',
    sub: 'Email to Case turns the message into a record. A record triggered Flow then calls the triage Prompt Template, which reads the whole thread and returns structured values the rest of the process can act on.',
  });

  const cw = (M.w - 0.24) / 2;
  L.card(s, { x: M.l, y: top, w: cw, h: 2.60 });
  L.chip(s, { x: M.l + 0.26, y: top + 0.24, text: '01' });
  s.addText('Capture', {
    x: M.l + 0.70, y: top + 0.24, w: cw - 1.0, h: 0.28, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 14, bold: true, color: C.white, valign: 'middle',
  });
  L.bullets(s, {
    x: M.l + 0.26, y: top + 0.70, w: cw - 0.52, h: 1.58,
    items: [
      'Email to Case creates the case from the Extended Care mailboxes for both customers and vendors.',
      'Thread ID matching appends a reply to its existing case instead of opening a duplicate, and reopens a closed case where the customer says the issue remains.',
      'A Flow duplicate check compares sender, account and subject against recent cases and links rather than creates.',
      'An auto response confirms receipt with the case number and the expected turnaround, within seconds of arrival.',
    ],
    size: 9, gap: 6,
  });

  L.card(s, { x: M.l + cw + 0.24, y: top, w: cw, h: 2.60 });
  L.chip(s, { x: M.l + cw + 0.50, y: top + 0.24, text: '02' });
  s.addText('Understand', {
    x: M.l + cw + 0.94, y: top + 0.24, w: cw - 1.2, h: 0.28, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 14, bold: true, color: C.white, valign: 'middle',
  });
  L.bullets(s, {
    x: M.l + cw + 0.50, y: top + 0.70, w: cw - 0.52, h: 1.58,
    items: [
      'A Flex Prompt Template reads the full thread, grounded on the case, the email messages, the account, the contact and prior cases on that account.',
      'Field Generation templates write the returned values straight onto case fields, so no free text parsing is needed for the simple ones.',
      'Deterministic Flow rules sit over the top. Where policy is unambiguous the rule wins, not the model.',
      'Where generative licensing is not available, Einstein Case Classification predicts the same fields from case history.',
    ],
    size: 9, gap: 6,
  });

  const y2 = top + 2.84;
  L.label(s, { x: M.l, y: y2, w: M.w, text: 'What the triage template returns on every case', color: C.white, size: 10.5 });
  const fields = [
    ['Category', 'Request, Inquiry, Issue, Dispute, System, Duplicate'],
    ['Service family', 'Orders, Status, Backorders, Credits, Pricing, Billing'],
    ['Recommended priority', 'P1 to P4, with the reason recorded'],
    ['Extracted entities', 'Order, invoice, PO, account, product, quantity'],
    ['Customer sentiment', 'Tone and escalation risk on the thread'],
    ['Case summary', 'A short factual summary of what is being asked'],
    ['PHI indicator', 'Flags patient identifiable content for handling'],
    ['Suggested queue', 'The routing destination and skills required'],
  ];
  const fw = (M.w - 3 * 0.18) / 4, fh = 0.72;
  fields.forEach((f, i) => {
    const x = M.l + (i % 4) * (fw + 0.18);
    const y = y2 + 0.34 + Math.floor(i / 4) * (fh + 0.16);
    L.card(s, { x, y, w: fw, h: fh, fill: C.panel2 });
    s.addText(f[0], {
      x: x + 0.16, y: y + 0.09, w: fw - 0.32, h: 0.24, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9.5, bold: true, color: C.cyan, valign: 'middle',
    });
    s.addText(f[1], {
      x: x + 0.16, y: y + 0.33, w: fw - 0.32, h: 0.32, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, color: C.mute, valign: 'top', lineSpacing: 10.5,
    });
  });
  L.footer(s);
  s.addNotes('The eight returned values are the whole point. Everything downstream, routing, SLA, drafting and reporting, keys off these fields. Stress that the model recommends and the Flow decides.');
}

/* ============================== 08  CLASSIFICATION ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Classification  |  01',
    title: 'A case taxonomy built for customer service',
    sub: 'Software terms such as story and defect do not describe what an Extended Care customer is asking for. These six categories do, and they map cleanly onto how the work is actually handled.',
  });

  const rows = [
    ['Request or Transaction', 'The customer asks the team to carry out an action', 'Place an order, modify an order, raise a return, request a document'],
    ['Inquiry', 'The customer asks for information', 'Order status, tracking, price, product availability, account question'],
    ['Issue or Exception', 'An expected service or transaction has failed', 'Delivery failure, incorrect order, delayed shipment, billing error'],
    ['Dispute or Financial Case', 'Financial investigation or authorisation is required', 'Credit, return dispute, price dispute, rebill, accounts receivable query'],
    ['System or Access Issue', 'The customer is blocked from using a system or completing an action', 'Login failure, ordering platform error, account access, data problem'],
    ['Duplicate or No Action', 'The case needs validation but no processing', 'Duplicate request, already resolved, insufficient information supplied'],
  ];
  const tw = 8.75;
  s.addTable(
    [[L.th('Primary category'), L.th('What it means'), L.th('Extended Care examples')],
     ...rows.map(r => [L.td(r[0], { bold: true, color: C.white }), L.td(r[1], { color: C.mute }), L.td(r[2])])],
    L.tableOpts({ x: M.l, y: top, w: tw, colW: [2.05, 3.0, 3.70], rowH: 0.52, fontSize: 8.5 })
  );

  const rx = M.l + tw + 0.24, rw = M.w - tw - 0.24;
  L.card(s, { x: rx, y: top, w: rw, h: 3.88 });
  L.label(s, { x: rx + 0.24, y: top + 0.20, w: rw - 0.48, text: 'A second field carries the service family', color: C.white, size: 10 });
  s.addText('Category says what kind of work it is. Service family says which part of the operation owns it. Routing, reporting and knowledge all key off the pair.', {
    x: rx + 0.24, y: top + 0.50, w: rw - 0.48, h: 0.58, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 8.5, color: C.mute, valign: 'top', lineSpacing: 11.5,
  });
  const fams = ['Order management', 'Order status and shipment', 'Backorders and availability', 'Credits and returns', 'Pricing and quotes', 'Account and billing', 'Product research', 'Documentation', 'System or access', 'Other, uncategorised'];
  fams.forEach((f, i) => {
    L.pill(s, { x: rx + 0.24, y: top + 1.20 + i * 0.245, w: rw - 0.48, h: 0.225, text: f, color: C.txt, size: 8 });
  });

  L.footnote(s, 'Duplicate and no action cases are excluded from operational SLA calculation under a disposition code agreed with McKesson, so they do not distort performance either way.');
  L.footer(s);
  s.addNotes('This corrects the earlier draft that used story and defect. Those are engineering words. Agents and McKesson reviewers both read these six categories without translation.');
}

/* ============================== 09  PRIORITY ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Classification  |  02',
    title: 'Priority is derived, not guessed',
    sub: 'Category alone does not tell you how urgent a case is. Priority is recommended from four inputs, then enforced by Flow so the same case always attracts the same treatment.',
  });

  s.addShape('roundRect', { x: M.l, y: top, w: M.w, h: 0.46, rectRadius: 0.04, fill: { color: C.panel2 }, line: { color: C.line, width: 1 } });
  s.addText([
    { text: 'PRIORITY  =  ', options: { bold: true, color: C.cyan, charSpacing: 1.2 } },
    { text: 'business impact', options: { color: C.white, bold: true } }, { text: '   +   ', options: { color: C.mute } },
    { text: 'urgency', options: { color: C.white, bold: true } }, { text: '   +   ', options: { color: C.mute } },
    { text: 'customer criticality', options: { color: C.white, bold: true } }, { text: '   +   ', options: { color: C.mute } },
    { text: 'regulatory or financial risk', options: { color: C.white, bold: true } },
  ], { x: M.l + 0.24, y: top, w: M.w - 0.48, h: 0.46, isTextBox: true, margin: 0, fontFace: F, fontSize: 11, valign: 'middle' });

  const pr = [
    ['P1', 'Critical', C.pink, 'Immediate business, patient service, compliance or widespread operational impact.', 'Ordering unavailable for multiple customers, critical patient delivery risk, PHI or security concern'],
    ['P2', 'High', C.amber, 'Significant customer impact requiring rapid action.', 'Urgent order placement, time sensitive modification, major delivery exception'],
    ['P3', 'Standard', C.cyan, 'Normal operational request or question.', 'Routine order status, product availability, standard account inquiry'],
    ['P4', 'Low', C.mute, 'Low impact administrative or research work.', 'General information, document request, non urgent product research'],
  ];
  const py = top + 0.68, pw = (M.w - 3 * 0.20) / 4, ph = 2.18;
  pr.forEach((p, i) => {
    const x = M.l + i * (pw + 0.20);
    L.card(s, { x, y: py, w: pw, h: ph });
    L.chip(s, { x: x + 0.22, y: py + 0.22, text: p[0], color: p[2], w: 0.44, h: 0.30, size: 11.5 });
    s.addText(p[1], {
      x: x + 0.74, y: py + 0.22, w: pw - 0.96, h: 0.30, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 12.5, bold: true, color: p[2], valign: 'middle',
    });
    s.addText(p[3], {
      x: x + 0.22, y: py + 0.66, w: pw - 0.44, h: 0.64, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9, color: C.txt, valign: 'top', lineSpacing: 12,
    });
    L.label(s, { x: x + 0.22, y: py + 1.34, w: pw - 0.44, text: 'Typical conditions', color: C.mute, size: 7.5, h: 0.18 });
    s.addText(p[4], {
      x: x + 0.22, y: py + 1.56, w: pw - 0.44, h: 0.54, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, color: C.mute, valign: 'top', lineSpacing: 10.5,
    });
  });

  const gy = py + ph + 0.22;
  L.card(s, { x: M.l, y: gy, w: M.w, h: 1.08 });
  L.label(s, { x: M.l + 0.24, y: gy + 0.14, w: 6, text: 'Controls that keep priority honest', color: C.white, size: 10 });
  const ctrls = [
    'Priority is recommended by the template and set by Flow, never left blank.',
    'An agent may change priority only with a recorded reason.',
    'P1 and P2 downgrades require Shift Lead approval.',
    'Premium and VIP accounts carry a separately defined uplift rule.',
    'Every priority change is written to the case audit history.',
    'Ageing alone can raise priority once a case passes an agreed threshold.',
  ];
  ctrls.forEach((c, i) => {
    const x = M.l + 0.24 + (i % 3) * 4.0;
    const y = gy + 0.44 + Math.floor(i / 3) * 0.28;
    s.addText(c, {
      x, y, w: 3.85, h: 0.26, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, color: C.mute, valign: 'middle',
    });
  });
  L.footer(s);
  s.addNotes('The controls matter more than the four levels. Without them, priority drifts and the SLA numbers stop meaning anything.');
}

/* ============================== 10  ROUTING ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Stage 03',
    title: 'Routed to the right team, not the next free agent',
    sub: 'Omni Channel takes the category, service family and priority set in stage 02 and pushes the case to an agent who holds the skill and has the capacity to work it now.',
  });

  const lw = 5.6;
  L.card(s, { x: M.l, y: top, w: lw, h: 3.92 });
  L.label(s, { x: M.l + 0.26, y: top + 0.22, w: lw - 0.5, text: 'How assignment is decided', color: C.white, size: 10.5 });
  const steps = [
    ['Queue', 'The service family selects the queue. Credits never lands in the order placement queue by accident.'],
    ['Skill', 'Skills based routing requires the matching competency, so complex credits reach senior agents.'],
    ['Capacity', 'Each agent carries a work item capacity, so a case is only pushed to someone able to start it.'],
    ['Priority', 'Higher priority work is presented first, so a P1 does not sit behind routine status requests.'],
    ['Coverage', 'Routing is business hours aware, so late arrivals go to agents who are actually on shift.'],
    ['Fallback', 'Anything unrouted past a defined threshold alerts the Shift Lead rather than sitting unowned.'],
  ];
  steps.forEach((st, i) => {
    const y = top + 0.68 + i * 0.53;
    L.chip(s, { x: M.l + 0.26, y: y + 0.07, text: String(i + 1), w: 0.26, h: 0.26, size: 9.5 });
    s.addText(st[0], {
      x: M.l + 0.62, y, w: 1.15, h: 0.34, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9.5, bold: true, color: C.cyan, valign: 'middle',
    });
    s.addText(st[1], {
      x: M.l + 1.80, y, w: lw - 2.06, h: 0.46, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, color: C.mute, valign: 'middle', lineSpacing: 11,
    });
  });

  const rx = M.l + lw + 0.24, rw = M.w - lw - 0.24;
  L.label(s, { x: rx, y: top, w: rw, text: 'The Extended Care queue map', color: C.white, size: 10.5 });
  const queues = [
    ['Order management', 'Place and modify order, returns initiation', 'Order entry, SupplyManager, JD Edwards', C.cyan],
    ['Order status and shipment', 'Status, tracking, proof of delivery', 'Order lookup, carrier tracking', C.cyan],
    ['Backorders and availability', 'Stock position, substitutions, ETAs', 'Inventory, product data', C.cyan],
    ['Credits and disputes', 'Credits, returns, rebills, price disputes', 'Senior only, financial policy, AR liaison', C.amber],
    ['Account and billing', 'Invoices, statements, account admin', 'Billing, account maintenance', C.cyan],
    ['Escalation and exceptions', 'Anything needing McKesson pricing or AR', 'Routed out under a defined escalation path', C.pink],
  ];
  queues.forEach((q, i) => {
    const y = top + 0.36 + i * 0.60;
    L.card(s, { x: rx, y, w: rw, h: 0.52, fill: C.panel2 });
    s.addText(q[0], {
      x: rx + 0.18, y, w: 2.15, h: 0.52, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9, bold: true, color: q[3], valign: 'middle',
    });
    s.addText(q[1], {
      x: rx + 2.38, y, w: 2.15, h: 0.52, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, color: C.txt, valign: 'middle', lineSpacing: 10.5,
    });
    s.addText(q[2], {
      x: rx + 4.60, y, w: rw - 4.78, h: 0.52, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, color: C.mute, valign: 'middle', lineSpacing: 10.5,
    });
  });
  L.footnote(s, 'Queue names, skill definitions and capacity weightings are confirmed with McKesson during discovery and configured before the readiness gate.');
  L.footer(s);
  s.addNotes('Routing is included in Service Cloud. No AI licensing needed for this stage. The value is that skill and capacity are respected, which is what protects the credits queue.');
}

/* ============================== 11  SLA ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Stage 04',
    title: 'Two SLA clocks, enforced by the platform',
    sub: 'Entitlements and Milestones run the SLA inside Salesforce against the Extended Care business hours. The clock is a record, not a report, so it can be acted on while it is still running.',
  });

  const cw = (M.w - 0.24) / 2;
  [['First response SLA', 'Time from case creation to the first meaningful reply to the customer.',
    ['An automated acknowledgement does not close this clock unless McKesson explicitly agrees that it should.',
     'Stops when the agent sends a substantive response, not when the case is opened or assigned.',
     'Runs against business hours, so an 7pm arrival is not judged against overnight time.']],
   ['Resolution SLA', 'Time from creation to resolution, subject to agreed pause conditions.',
    ['Pauses only while waiting on the customer, and only after a valid information request has gone out.',
     'Keeps running while waiting on an internal McKesson team, with dependency time measured separately.',
     'Stops on resolution and is not restarted by an administrative closure.']],
  ].forEach((c, i) => {
    const x = M.l + i * (cw + 0.24);
    L.card(s, { x, y: top, w: cw, h: 1.86 });
    s.addText(c[0], {
      x: x + 0.26, y: top + 0.18, w: cw - 0.52, h: 0.28, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 13, bold: true, color: C.cyan, valign: 'middle',
    });
    s.addText(c[1], {
      x: x + 0.26, y: top + 0.48, w: cw - 0.52, h: 0.26, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9, color: C.mute, valign: 'middle',
    });
    L.bullets(s, { x: x + 0.26, y: top + 0.80, w: cw - 0.52, h: 0.96, items: c[2], size: 8.5, gap: 4 });
  });

  const ty = top + 2.10;
  L.label(s, { x: M.l, y: ty, w: 7, text: 'Proposed targets by priority', color: C.white, size: 10.5 });
  s.addTable(
    [[L.th('Priority'), L.th('First meaningful response'), L.th('Resolution target')],
     [L.td('P1  Critical', { bold: true, color: C.pink }), L.td('15 minutes'), L.td('1 hour, or continuous active ownership')],
     [L.td('P2  High', { bold: true, color: C.amber }), L.td('30 minutes'), L.td('4 business hours')],
     [L.td('P3  Standard', { bold: true, color: C.cyan }), L.td('2 business hours'), L.td('1 business day')],
     [L.td('P4  Low', { bold: true, color: C.mute }), L.td('4 business hours'), L.td('2 to 3 business days')]],
    L.tableOpts({ x: M.l, y: ty + 0.30, w: 7.3, colW: [2.1, 2.5, 2.7], rowH: 0.42, fontSize: 9 })
  );

  const rx = M.l + 7.54, rw = M.w - 7.54;
  L.card(s, { x: rx, y: ty + 0.30, w: rw, h: 2.40 });
  L.label(s, { x: rx + 0.24, y: ty + 0.48, w: rw - 0.48, text: 'Reconciled to the case type targets', color: C.white, size: 10 });
  s.addText('The turnaround goals McKesson has already set remain the operating commitment. Priority tiers sit over them to decide what gets attention first when both are in play.', {
    x: rx + 0.24, y: ty + 0.76, w: rw - 0.48, h: 0.52, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 8.5, color: C.mute, valign: 'top', lineSpacing: 11.5,
  });
  [['Place or modify order', '1 hour'], ['Order status or tracking', '4 hours'], ['Credit requests or returns', '72 hours'], ['First pass resolution', 'Baselined in transition']]
    .forEach((r, i) => {
      const y = ty + 1.34 + i * 0.27;
      s.addText(r[0], { x: rx + 0.24, y, w: rw - 1.70, h: 0.25, isTextBox: true, margin: 0, fontFace: F, fontSize: 8.5, color: C.txt, valign: 'middle' });
      s.addText(r[1], { x: rx + rw - 1.60, y, w: 1.36, h: 0.25, isTextBox: true, margin: 0, fontFace: F, fontSize: 8.5, bold: true, color: C.cyan, align: 'right', valign: 'middle' });
    });
  L.footnote(s, 'Targets shown are design proposals for discussion. Final thresholds, pause conditions and measurement definitions are agreed jointly and configured in the Entitlement Process before go live.');
  L.footer(s);
  s.addNotes('Entitlements and Milestones are standard Service Cloud. The design decision worth flagging: the resolution clock keeps running during internal McKesson dependencies, because pausing it would hide the real customer experience.');
}

/* ============================== 12  ESCALATION ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Stage 04  |  Escalation',
    title: 'Escalation fires on percentage of SLA consumed',
    sub: 'A fixed one hour rule is too slow for a P1 and too noisy for a 72 hour credit. Milestone time triggers escalate in proportion to the clock the case is actually running against.',
  });

  const lad = [
    ['50%', 'Notify the case owner', 'A reminder on the record and in the agent queue view. No management involvement yet.', C.cyan],
    ['70%', 'Notify owner and Shift Lead', 'The Shift Lead can rebalance the queue or reassign before the case is at risk.', C.amber],
    ['85%', 'Escalate to Team Lead, flag on dashboard', 'The case appears in the at risk panel on the operations control tower.', 'F97316'],
    ['100%', 'Escalate to Operations Manager', 'Breach is recorded with reason and root cause, and reviewed in the daily cadence.', C.pink],
  ];
  const lw = (M.w - 3 * 0.20) / 4;
  lad.forEach((l, i) => {
    const x = M.l + i * (lw + 0.20);
    L.card(s, { x, y: top, w: lw, h: 1.74 });
    s.addText(l[0], {
      x: x + 0.24, y: top + 0.18, w: lw - 0.48, h: 0.46, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 24, bold: true, color: l[3], valign: 'middle',
    });
    L.label(s, { x: x + 0.24, y: top + 0.62, w: lw - 0.48, text: 'of SLA consumed', color: C.mute, size: 7.5, h: 0.18 });
    s.addText(l[1], {
      x: x + 0.24, y: top + 0.86, w: lw - 0.48, h: 0.40, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 10, bold: true, color: C.white, valign: 'top', lineSpacing: 13,
    });
    s.addText(l[2], {
      x: x + 0.24, y: top + 1.26, w: lw - 0.48, h: 0.42, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, color: C.mute, valign: 'top', lineSpacing: 10.5,
    });
    if (i < 3) L.arrow(s, { x: x + lw + 0.02, y: top + 0.82, w: 0.16, h: 0.14 });
  });

  const y2 = top + 1.98;
  const halfw = (M.w - 0.24) / 2;
  L.card(s, { x: M.l, y: y2, w: halfw, h: 2.30 });
  L.label(s, { x: M.l + 0.26, y: y2 + 0.20, w: halfw - 0.52, text: 'Additional escalation triggers', color: C.white, size: 10 });
  L.bullets(s, {
    x: M.l + 0.26, y: y2 + 0.56, w: halfw - 0.52, h: 1.62,
    items: [
      'A P1 case is created, or any case is raised to P1 or P2.',
      'A case remains unassigned beyond the agreed threshold.',
      'A case is reopened, or transferred more than once.',
      'The customer sends repeated follow ups on an open case.',
      'An internal dependency exceeds its agreed turnaround.',
      'Negative customer feedback is received on a closed case.',
    ],
    size: 8.5, gap: 5,
  });

  L.card(s, { x: M.l + halfw + 0.24, y: y2, w: halfw, h: 2.30 });
  L.label(s, { x: M.l + halfw + 0.50, y: y2 + 0.20, w: halfw - 0.52, text: 'Why proportional beats fixed', color: C.white, size: 10 });
  s.addText('A P1 carries a 15 minute first response target. Half of that clock is seven and a half minutes, so the owner is prompted while there is still time to act. A 72 hour credit case reaches the same 50 percent mark at 36 hours, which is when a nudge is genuinely useful rather than noise.\n\nThe result is that the escalation load scales with risk. Agents are interrupted when it matters and left alone when it does not, and leadership sees the cases that are genuinely drifting rather than a flat alert stream.', {
    x: M.l + halfw + 0.50, y: y2 + 0.56, w: halfw - 0.52, h: 1.62, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9, color: C.txt, valign: 'top', lineSpacing: 13,
  });
  L.footer(s);
  s.addNotes('Milestone time triggers do this natively. Each trigger can fire a task, an email alert, a field update or a Slack or Chatter post. No custom code.');
}

/* ============================== 13  DRAFT & SUMMARISE ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Stage 05  |  The workload reducer',
    title: 'The draft is waiting when the agent opens the case',
    sub: 'This is where the handling time comes out. The agent stops composing from a blank box and starts reviewing, correcting and sending, with the policy and the order context already on the record.',
  });

  const cw = (M.w - 2 * 0.22) / 3;
  const cards = [
    ['Draft email response', 'Sales Email or Flex prompt template', [
      'Written in the approved Extended Care tone and structure, from the standard response library.',
      'Grounded on the case, the contact, the account, the retrieved Knowledge article and the order record.',
      'Inserts live order, shipment and availability values where the connected system exposes them.',
      'Never sends on its own. The agent reviews, edits and sends, and that action is what stops the SLA clock.',
    ], C.cyan],
    ['Case and thread summary', 'Record Summary or Flex prompt template', [
      'A short factual summary of what the customer asked, written to the case on creation.',
      'A running thread summary so a second agent can pick the case up without reading every reply.',
      'A structured handover note carrying owner, status, priority, last action, next action and remaining SLA.',
      'Feeds the shift report and the daily operations summary, generated from case fields rather than typed by agents.',
    ], C.cyan],
    ['What stays with the agent', 'The human boundary, by design', [
      'Judgement on whether the draft is right, complete and appropriate for this customer.',
      'Every credit, return, pricing adjustment, account hold and billing dispute.',
      'Any case flagged as PHI sensitive, or where grounding data is missing or conflicting.',
      'Complaints, financial authorisation and any case the customer has escalated.',
    ], C.pink],
  ];
  cards.forEach((c, i) => {
    const x = M.l + i * (cw + 0.22);
    L.card(s, { x, y: top, w: cw, h: 3.04, line: i === 2 ? '4A2740' : C.line });
    s.addText(c[0], {
      x: x + 0.26, y: top + 0.20, w: cw - 0.52, h: 0.30, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 13, bold: true, color: c[3], valign: 'middle',
    });
    L.label(s, { x: x + 0.26, y: top + 0.52, w: cw - 0.52, text: c[1], color: C.mute, size: 7.5, h: 0.20 });
    L.bullets(s, { x: x + 0.26, y: top + 0.84, w: cw - 0.52, h: 2.06, items: c[2], size: 9, gap: 7 });
  });

  const y2 = top + 3.28;
  s.addShape('roundRect', { x: M.l, y: y2, w: M.w, h: 0.50, rectRadius: 0.04, fill: { color: '1A1226' }, line: { color: '4A2740', width: 1 } });
  s.addText([
    { text: 'HUMAN IN THE LOOP   ', options: { bold: true, color: C.pink, charSpacing: 1.4, fontSize: 9 } },
    { text: 'In Phase 2 no generated response reaches a customer without an agent approving it. Every draft, the prompt that produced it and the agent edit that followed are retained in the case audit trail.', options: { color: C.txt, fontSize: 9 } },
  ], { x: M.l + 0.22, y: y2, w: M.w - 0.44, h: 0.50, isTextBox: true, margin: 0, fontFace: F, valign: 'middle' });
  L.footer(s);
  s.addNotes('If you only land one slide, land this one. The draft plus summary combination is where the 25 percent handling time reduction comes from, and the third column is what makes it safe to say yes to.');
}

/* ============================== 14  KNOWLEDGE ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Grounding',
    title: 'Knowledge articles are what make the answer correct',
    sub: 'A draft is only as good as what it is grounded in. Salesforce Knowledge is the source of truth for both the agent and the template, which means improving an article improves every future response.',
  });

  const lw = 7.5;
  L.card(s, { x: M.l, y: top, w: lw, h: 3.62 });
  L.label(s, { x: M.l + 0.26, y: top + 0.22, w: lw - 0.52, text: 'The grounding and improvement loop', color: C.white, size: 10.5 });
  const loop = [
    ['Retrieve', 'The case category and service family map onto Knowledge data categories, so the search is scoped before it starts.'],
    ['Recommend', 'Einstein Article Recommendations surface the likely articles on the case record for the agent to confirm.'],
    ['Ground', 'The confirmed article is passed to the draft template as grounding, so the response reflects current policy.'],
    ['Attach', 'The article used is attached to the case, which gives a measurable view of which content actually resolves cases.'],
    ['Capture the gap', 'Where no article fits, the agent raises a gap in one click. That becomes a Knowledge backlog item with an owner.'],
    ['Publish and reuse', 'The new or corrected article is reviewed, approved and published, and the next case is answered from it.'],
  ];
  loop.forEach((l, i) => {
    const y = top + 0.68 + i * 0.49;
    L.chip(s, { x: M.l + 0.26, y: y + 0.05, text: String(i + 1), w: 0.26, h: 0.26, size: 9.5 });
    s.addText(l[0], {
      x: M.l + 0.62, y, w: 1.45, h: 0.32, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9.5, bold: true, color: C.cyan, valign: 'middle',
    });
    s.addText(l[1], {
      x: M.l + 2.08, y, w: lw - 2.34, h: 0.40, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, color: C.mute, valign: 'middle', lineSpacing: 11,
    });
  });

  const rx = M.l + lw + 0.24, rw = M.w - lw - 0.24;
  L.card(s, { x: rx, y: top, w: rw, h: 1.76 });
  L.label(s, { x: rx + 0.24, y: top + 0.18, w: rw - 0.48, text: 'Knowledge governance', color: C.white, size: 10 });
  s.addText('Every article carries an owner, a version, an approval state, a review date and the case types it serves. Articles that pass their review date are flagged rather than left to quietly go stale.', {
    x: rx + 0.24, y: top + 0.50, w: rw - 0.48, h: 0.96, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9, color: C.txt, valign: 'top', lineSpacing: 12.5,
  });

  L.card(s, { x: rx, y: top + 1.98, w: rw, h: 1.64 });
  L.label(s, { x: rx + 0.24, y: top + 2.16, w: rw - 0.48, text: 'Why this compounds', color: C.white, size: 10 });
  s.addText('Today a good answer helps one customer. Under this model a good answer is written once into an article, then grounds every future draft on that case type. Knowledge quality becomes the lever on response quality across the whole operation.', {
    x: rx + 0.24, y: top + 2.48, w: rw - 0.48, h: 1.02, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9, color: C.txt, valign: 'top', lineSpacing: 12.5,
  });
  L.footnote(s, 'Knowledge base development and standardised response content are already committed in the current proposal. This design makes that content the grounding source for automation rather than a reference library alongside it.');
  L.footer(s);
  s.addNotes('This answers the obvious objection, that generated answers might be wrong. They are grounded in McKesson approved articles, and the gap capture step means the base gets better rather than drifting.');
}

/* ============================== 15  LIFECYCLE ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Case lifecycle',
    title: 'Standard statuses, and what each does to the clock',
    sub: 'Ambiguous statuses are how SLA reporting loses credibility. Each status below has one meaning and a defined effect on both clocks, configured in the Entitlement Process.',
  });

  const rows = [
    ['New or Open', 'Received but not yet accepted by an agent', 'Runs', 'Runs'],
    ['Assigned', 'Owner assigned, work not yet started', 'Runs', 'Runs'],
    ['In Progress', 'Agent actively investigating or responding', 'Runs until the response is sent', 'Runs'],
    ['Pending Internal Team', 'Waiting on pricing, AR, warehouse or another McKesson dependency', 'Completed', 'Continues to run, with dependency time measured separately'],
    ['Waiting for Customer', 'Customer information or action is required', 'Completed', 'Pauses, once a valid request has been sent'],
    ['Waiting for Closure Confirmation', 'Resolution supplied, customer confirmation outstanding', 'Completed', 'Pauses'],
    ['Resolved', 'Solution provided, no further operational action required', 'Completed', 'Stops'],
    ['Closed', 'Closure confirmed, or the auto closure rule has completed', 'Completed', 'Completed'],
    ['Reopened', 'Customer indicates the issue is not resolved', 'Completed', 'Resumes, and the reopen is tracked'],
    ['Cancelled or Duplicate', 'Invalid or duplicate case', 'Excluded under agreed rules', 'Excluded under agreed rules'],
  ];
  s.addTable(
    [[L.th('Status'), L.th('What it means'), L.th('First response clock'), L.th('Resolution clock')],
     ...rows.map(r => [
       L.td(r[0], { bold: true, color: C.white }),
       L.td(r[1], { color: C.mute }),
       L.td(r[2], { color: r[2].startsWith('Runs') ? C.amber : r[2].startsWith('Excluded') ? C.mute : C.green }),
       L.td(r[3], { color: /Runs|Continues|Resumes/.test(r[3]) ? C.amber : /Excluded/.test(r[3]) ? C.mute : C.txt }),
     ])],
    L.tableOpts({ x: M.l, y: top, w: M.w, colW: [2.35, 4.35, 2.55, 2.98], rowH: 0.345, fontSize: 8.5 })
  );

  const y2 = top + 3.85;
  s.addShape('roundRect', { x: M.l, y: y2, w: M.w, h: 0.56, rectRadius: 0.04, fill: { color: C.panel2 }, line: { color: C.line, width: 1 } });
  s.addText([
    { text: 'DESIGN DECISION   ', options: { bold: true, color: C.cyan, charSpacing: 1.4, fontSize: 9 } },
    { text: 'The resolution clock is not paused simply because another internal team is involved. Pausing it would hide the real customer experience. Instead four times are measured on every case: end to end closure time, controllable Insight Global processing time, dependency time awaiting a McKesson team, and customer wait time.', options: { color: C.txt, fontSize: 9 } },
  ], { x: M.l + 0.22, y: y2, w: M.w - 0.44, h: 0.56, isTextBox: true, margin: 0, fontFace: F, valign: 'middle', lineSpacing: 12 });
  L.footer(s);
  s.addNotes('Expect a conversation on the Pending Internal Team row. The four way time split is the answer: McKesson can see what is ours and what is theirs, without either of us gaming the headline number.');
}

/* ============================== 16  TRUST & GUARDRAILS ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Trust and control',
    title: 'Built for a PHI sensitive environment',
    sub: 'Generative capability in this design runs through the Einstein Trust Layer inside McKesson tenancy. Nothing is trained on McKesson data and nothing is retained by a model provider.',
  });

  const tl = [
    ['Zero data retention', 'Prompts and responses are not stored or used for training by the model provider. They exist only in the Salesforce audit record.'],
    ['Data masking', 'PHI and PII are masked before the prompt leaves the org and rehydrated in the response, so identifiable data is not exposed to the model.'],
    ['Dynamic grounding', 'The template receives only the specific records it is authorised to see, under the running user permissions.'],
    ['Prompt injection defence', 'Instructions embedded in an inbound customer email are treated as content, not as commands to the system.'],
    ['Toxicity scoring', 'Generated output is scored before it is presented, and flagged output is withheld from the agent.'],
    ['Audit trail', 'Every prompt, response, agent edit and send is retained and reportable, so any customer reply can be reconstructed.'],
  ];
  const cw = (M.w - 2 * 0.22) / 3, chh = 1.18;
  tl.forEach((t, i) => {
    const x = M.l + (i % 3) * (cw + 0.22);
    const y = top + Math.floor(i / 3) * (chh + 0.20);
    L.card(s, { x, y, w: cw, h: chh });
    s.addText(t[0], {
      x: x + 0.24, y: y + 0.16, w: cw - 0.48, h: 0.26, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 11, bold: true, color: C.cyan, valign: 'middle',
    });
    s.addText(t[1], {
      x: x + 0.24, y: y + 0.46, w: cw - 0.48, h: 0.62, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, color: C.mute, valign: 'top', lineSpacing: 11.5,
    });
  });

  const y2 = top + 2 * (chh + 0.20) + 0.06;
  L.card(s, { x: M.l, y: y2, w: M.w, h: 1.22, fill: '1A1226', line: '4A2740' });
  L.label(s, { x: M.l + 0.26, y: y2 + 0.16, w: 8, text: 'Human approval remains mandatory, at every phase', color: C.pink, size: 10 });
  const must = ['Credits and returns', 'Pricing adjustments', 'Account holds', 'Billing disputes', 'PHI sensitive exceptions', 'Customer complaints', 'Financial authorisation', 'Conflicting or missing data'];
  must.forEach((m, i) => {
    const x = M.l + 0.26 + (i % 4) * 2.98;
    const y = y2 + 0.50 + Math.floor(i / 4) * 0.32;
    s.addShape('roundRect', { x, y, w: 2.80, h: 0.27, rectRadius: 0.05, fill: { color: '241733' }, line: { color: '4A2740', width: 1 } });
    s.addText(m, { x: x + 0.12, y, w: 2.56, h: 0.27, isTextBox: true, margin: 0, fontFace: F, fontSize: 8.5, color: C.txt, valign: 'middle' });
  });
  L.footnote(s, 'Einstein Trust Layer controls apply to Prompt Builder and Agentforce features and require the corresponding licensing. Phase 1 uses no generative capability and therefore introduces no new data handling surface.');
  L.footer(s);
  s.addNotes('Security will ask about this. The three answers that matter: it runs in McKesson tenancy, PHI is masked before it leaves the org, and nothing is retained or trained on.');
}

/* ============================== 17  ROADMAP ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Delivery',
    title: 'Three phases, and value before any new licence',
    sub: 'Phase 1 is built entirely from capability McKesson already owns in Service Cloud. Generative features are introduced only once licensing, data access and security approval are confirmed.',
  });

  const phases = [
    ['PHASE 1', 'Safe workflow automation', 'No new licensing required', C.cyan, [
      'Email to Case, thread matching and duplicate handling',
      'Record triggered Flow orchestration across the case lifecycle',
      'Rule based category and priority recommendation',
      'Omni Channel skills based routing and capacity management',
      'Entitlements, Milestones and proportional escalation',
      'Knowledge structure, Quick Text, Macros and the response library',
      'Auto acknowledgement, reminders and closure confirmation',
      'Operations dashboards and automated shift reporting',
    ], 'Delivered with Service Cloud configuration. Einstein Case Classification may be added here where it is already licensed.'],
    ['PHASE 2', 'Assisted agent responses', 'Requires Einstein or Agentforce licensing', C.amber, [
      'Prompt Template: case triage, classification and entity extraction',
      'Prompt Template: case and thread summarisation',
      'Prompt Template: drafted email response for agent review',
      'Knowledge article retrieval and grounding on the draft',
      'Order, shipment and availability data inserted from connected systems',
      'Recommended next action on the case record',
      'Quality, completeness and tone checks before the agent sends',
      'Prompt performance monitoring and template tuning',
    ], 'Gated on licensing confirmation, security approval, Knowledge readiness and a supervised accuracy threshold agreed with McKesson.'],
    ['PHASE 3', 'Controlled autonomous responses', 'Requires Agentforce, scoped separately', C.pink, [
      'Order receipt confirmation',
      'Standard order status response',
      'Shipment tracking response',
      'Published backorder and availability information',
      'Document and copy requests',
      'Requests for missing required information',
      'Closure confirmation and follow up',
      'Everything else continues to route to a human',
    ], 'Positioned as discovery and pilot. Each candidate case type is proven in supervised mode and released individually, with confidence thresholds and exception routing.'],
  ];
  const cw = (M.w - 2 * 0.24) / 3;
  phases.forEach((p, i) => {
    const x = M.l + i * (cw + 0.24);
    L.card(s, { x, y: top, w: cw, h: 4.28 });
    s.addText(p[0], {
      x: x + 0.26, y: top + 0.20, w: cw - 0.52, h: 0.24, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9.5, bold: true, color: p[3], charSpacing: 1.6, valign: 'middle',
    });
    s.addText(p[1], {
      x: x + 0.26, y: top + 0.46, w: cw - 0.52, h: 0.30, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 13.5, bold: true, color: C.white, valign: 'middle',
    });
    s.addShape('roundRect', { x: x + 0.26, y: top + 0.82, w: cw - 0.52, h: 0.30, rectRadius: 0.05, fill: { color: C.panel2 }, line: { color: p[3], width: 1 } });
    s.addText(p[2], {
      x: x + 0.38, y: top + 0.82, w: cw - 0.76, h: 0.30, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, bold: true, color: p[3], valign: 'middle',
    });
    L.bullets(s, { x: x + 0.26, y: top + 1.26, w: cw - 0.52, h: 2.14, items: p[4], size: 8.5, gap: 4 });
    s.addShape('line', { x: x + 0.26, y: top + 3.46, w: cw - 0.52, h: 0, line: { color: C.line, width: 1 } });
    s.addText(p[5], {
      x: x + 0.26, y: top + 3.56, w: cw - 0.52, h: 0.62, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, italic: true, color: C.mute, valign: 'top', lineSpacing: 10.5,
    });
  });
  L.footer(s);
  s.addNotes('The commercial point without talking commercials: Phase 1 is real value at zero licensing risk. That is what lets McKesson start without resolving the Agentforce question first.');
}

/* ============================== 18  DASHBOARDS ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Visibility',
    title: 'What McKesson and the team can see, live',
    sub: 'Because classification, priority and SLA are now structured fields rather than judgement calls, they can be reported on reliably. Dashboards are generated from the case record, not assembled by hand.',
  });

  const cw = (M.w - 0.24) / 2;
  const panels = [
    ['Operations control tower', 'For the Shift Leads, the Operations Manager and McKesson', [
      'Open cases by status, category, priority, owner and shift',
      'First response and resolution SLA at risk, and breached',
      'Backlog volume and ageing profile by queue',
      'Unassigned cases, and cases transferred more than once',
      'Cases waiting on the customer, and on an internal McKesson team',
      'Reopened cases and escalations by destination',
      'Daily intake against daily closure, and queue balance',
      'Automation coverage: cases auto classified, drafts accepted or rewritten',
    ], C.cyan],
    ['Individual agent view', 'For the agent and their Team Lead', [
      'Assigned cases, and cases awaiting an action from them',
      'First response and resolution compliance on their own work',
      'First pass resolution rate and reopen rate',
      'Quality assurance results and customer feedback received',
      'Ageing workload and cases approaching an SLA threshold',
      'Draft acceptance rate, as a coaching signal rather than a target',
      'Knowledge gaps raised and articles contributed',
      'Coaching and training actions outstanding',
    ], C.cyan],
  ];
  panels.forEach((p, i) => {
    const x = M.l + i * (cw + 0.24);
    L.card(s, { x, y: top, w: cw, h: 3.22 });
    s.addText(p[0], {
      x: x + 0.26, y: top + 0.20, w: cw - 0.52, h: 0.30, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 13, bold: true, color: p[3], valign: 'middle',
    });
    L.label(s, { x: x + 0.26, y: top + 0.52, w: cw - 0.52, text: p[1], color: C.mute, size: 7.5, h: 0.20 });
    L.bullets(s, { x: x + 0.26, y: top + 0.84, w: cw - 0.52, h: 2.24, items: p[2], size: 9, gap: 5 });
  });

  const y2 = top + 3.46;
  s.addShape('roundRect', { x: M.l, y: y2, w: M.w, h: 0.56, rectRadius: 0.04, fill: { color: C.panel2 }, line: { color: C.line, width: 1 } });
  s.addText([
    { text: 'REPORTING PRINCIPLE   ', options: { bold: true, color: C.cyan, charSpacing: 1.4, fontSize: 9 } },
    { text: 'Shift and end of day reports are generated from trusted case fields, not written by each agent. That removes manual reporting effort from the floor and makes every number traceable to the record it came from.', options: { color: C.txt, fontSize: 9 } },
  ], { x: M.l + 0.22, y: y2, w: M.w - 0.44, h: 0.56, isTextBox: true, margin: 0, fontFace: F, valign: 'middle', lineSpacing: 12 });
  L.footer(s);
  s.addNotes('Note the automation coverage metrics on the left. Draft acceptance rate is how we prove the AI is actually helping, and it is a coaching signal, never an agent target.');
}

/* ============================== 19  CONTINUOUS IMPROVEMENT ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Improvement',
    title: 'Every closed case feeds the next one',
    sub: 'Feedback, quality findings and draft performance all land in one backlog with an owner and a target date, so improvement is a managed process rather than an intention.',
  });

  const loop = [
    ['01', 'Close and ask', 'A short survey goes out on closure: was it resolved, was the response clear, was the turnaround acceptable, overall satisfaction, optional comment.'],
    ['02', 'Link and triage', 'Feedback is linked to the originating case. Negative feedback automatically raises a service recovery action and is reviewed by the Shift Lead.'],
    ['03', 'Find the cause', 'Quality Assurance determines whether the cause is the agent, the process, the knowledge article, the system, a dependency or the policy itself.'],
    ['04', 'Fix the right thing', 'Agent causes go to coaching. Knowledge causes go to the article. Template causes go to prompt tuning. Process causes go to the workflow.'],
    ['05', 'Track and review', 'Each action carries an owner, a target date, a status and an expected benefit, and trends are reviewed with McKesson in the monthly cadence.'],
  ];
  const cw = (M.w - 4 * 0.20) / 5;
  loop.forEach((l, i) => {
    const x = M.l + i * (cw + 0.20);
    L.card(s, { x, y: top, w: cw, h: 2.30 });
    L.chip(s, { x: x + 0.22, y: top + 0.20, text: l[0] });
    s.addText(l[1], {
      x: x + 0.22, y: top + 0.58, w: cw - 0.44, h: 0.32, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 11.5, bold: true, color: C.white, valign: 'middle',
    });
    s.addText(l[2], {
      x: x + 0.22, y: top + 0.96, w: cw - 0.44, h: 1.18, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, color: C.mute, valign: 'top', lineSpacing: 11.5,
    });
    if (i < 4) L.arrow(s, { x: x + cw + 0.02, y: top + 1.08, w: 0.16, h: 0.14 });
  });

  const y2 = top + 2.54;
  const hw = (M.w - 0.24) / 2;
  L.card(s, { x: M.l, y: y2, w: hw, h: 1.60 });
  L.label(s, { x: M.l + 0.26, y: y2 + 0.18, w: hw - 0.52, text: 'What the automation adds to this loop', color: C.white, size: 10 });
  L.bullets(s, {
    x: M.l + 0.26, y: y2 + 0.52, w: hw - 0.52, h: 0.96,
    items: [
      'Draft acceptance and edit distance show which case types the templates handle well and which need work.',
      'Knowledge gaps are captured at the moment the agent hits one, not recalled weeks later.',
      'Because every case is classified, recurring demand drivers become visible and can be designed out.',
    ],
    size: 8.5, gap: 5,
  });

  L.card(s, { x: M.l + hw + 0.24, y: y2, w: hw, h: 1.60 });
  L.label(s, { x: M.l + hw + 0.50, y: y2 + 0.18, w: hw - 0.52, text: 'Governance cadence', color: C.white, size: 10 });
  const cad = [
    ['Daily', 'Queue review at shift start, handover, SLA risk and aged case review, end of day closure report'],
    ['Weekly', 'Operations review, volume and backlog trends, quality calibration, knowledge gaps, automation candidates'],
    ['Monthly', 'Business review: SLA attainment, first pass resolution, reopens, QA, feedback, automation progress'],
    ['Quarterly', 'Strategic review: capacity and forecast, risks, customer experience trends, next quarter roadmap'],
  ];
  cad.forEach((c, i) => {
    const y = y2 + 0.52 + i * 0.26;
    s.addText(c[0], {
      x: M.l + hw + 0.50, y, w: 0.85, h: 0.24, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, bold: true, color: C.cyan, valign: 'middle',
    });
    s.addText(c[1], {
      x: M.l + hw + 1.38, y, w: hw - 1.64, h: 0.24, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8, color: C.mute, valign: 'middle',
    });
  });
  L.footer(s);
  s.addNotes('The distinction worth making: today improvement depends on someone remembering. Here the signal is captured automatically at the point of work.');
}

/* ============================== 20  WHERE THE MINUTES COME FROM ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Business value  |  01',
    title: 'Where the minutes actually come from',
    sub: 'Handling time is not reduced by asking agents to work faster. It is reduced by removing steps that do not need a person, and shortening the ones that do.',
  });

  const rows = [
    ['Read and comprehend the thread', '1:15', '0:45', '0:30', 'A factual summary is on the case before the agent opens it'],
    ['Classify, prioritise and assign', '1:00', '0:20', '0:40', 'Category, priority and queue are set automatically, the agent verifies'],
    ['Assemble account and order context', '1:30', '1:20', '0:10', 'Extracted entities link the order, invoice and account to the case'],
    ['Find the right policy or article', '1:10', '1:00', '0:10', 'The matching Knowledge article is surfaced and attached'],
    ['Compose the response', '2:30', '2:05', '0:25', 'A grounded draft replaces the blank box, the agent reviews and edits'],
    ['Update, log and close', '0:50', '0:45', '0:05', 'Case fields, summary and disposition are already populated'],
  ];
  s.addTable(
    [[L.th('Step in handling a case'), L.th('Today'), L.th('Modelled'), L.th('Saved'), L.th('What removes the time')],
     ...rows.map(r => [
       L.td(r[0], { color: C.txt }),
       L.td(r[1], { align: 'center', color: C.mute }),
       L.td(r[2], { align: 'center', color: C.white, bold: true }),
       L.td(r[3], { align: 'center', color: C.green, bold: true }),
       L.td(r[4], { color: C.mute, fontSize: 8.5 }),
     ]),
     [L.td('BLENDED AVERAGE HANDLING TIME', { bold: true, color: C.white, fill: { color: '17222E' }, fontSize: 9.5 }),
      L.td('8:15', { align: 'center', bold: true, color: C.mute, fill: { color: '17222E' }, fontSize: 11 }),
      L.td('6:15', { align: 'center', bold: true, color: C.cyan, fill: { color: '17222E' }, fontSize: 11 }),
      L.td('2:00', { align: 'center', bold: true, color: C.green, fill: { color: '17222E' }, fontSize: 11 }),
      L.td('A 24 percent reduction, modelled and validated at baseline', { color: C.txt, fill: { color: '17222E' }, fontSize: 8.5, bold: true })]],
    L.tableOpts({ x: M.l, y: top, w: M.w, colW: [3.65, 1.25, 1.35, 1.25, 4.73], rowH: 0.42, fontSize: 9 })
  );

  const y2 = top + 3.46;
  const cw = (M.w - 2 * 0.22) / 3;
  const notes = [
    ['Compounding across volume', 'Two minutes on 33,480 cases a month is roughly 1,100 hours of handling effort returned every month, or about 13,000 hours a year.', C.cyan],
    ['Triage is the cleanest win', 'The classify and assign step alone removes over 370 hours a month, and it is fully automated rather than assisted.', C.cyan],
    ['Deliberately conservative', 'Assisted drafting typically saves more than 25 seconds per case on templated types. The model assumes review and editing on every draft.', C.mute],
  ];
  notes.forEach((n, i) => {
    const x = M.l + i * (cw + 0.22);
    L.card(s, { x, y: y2, w: cw, h: 1.02 });
    s.addText(n[0], {
      x: x + 0.24, y: y2 + 0.16, w: cw - 0.48, h: 0.26, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 10.5, bold: true, color: n[2], valign: 'middle',
    });
    s.addText(n[1], {
      x: x + 0.24, y: y2 + 0.44, w: cw - 0.48, h: 0.54, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, color: C.mute, valign: 'top', lineSpacing: 11,
    });
  });
  L.footnote(s, 'Step level timings are Insight Global estimates decomposing the 8:15 blended handling time in the current operations sample. They are a design model, not a committed target, and are validated during the baseline period.');
  L.footer(s);
  s.addNotes('Be honest that these are modelled. The credibility comes from showing the decomposition rather than asserting a headline percentage. If challenged, the classify and assign row is the one to defend hardest, because it is deterministic.');
}

/* ============================== 21  IMPACT ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Business value  |  02',
    title: 'Efficiency and response time, the two targets',
    sub: 'Handling time reduction gives back capacity. Automated triage and routing are what actually cut response time, because a case no longer waits its turn to be understood.',
  });

  const sw = (M.w - 3 * 0.20) / 4;
  [['~24%', 'Modelled reduction in blended average handling time, from 8:15 to 6:15', C.cyan],
   ['~1,100', 'Hours of handling effort returned per month at current volume', C.cyan],
   ['Under 60s', 'From email arrival to a classified, prioritised, routed and SLA timed case', C.green],
   ['100%', 'Of cases triaged and summarised, rather than a quality sample', C.green],
  ].forEach((st, i) => L.stat(s, { x: M.l + i * (sw + 0.20), y: top, w: sw, h: 1.22, value: st[0], caption: st[1], color: st[2], valueSize: 26 }));

  const y2 = top + 1.46;
  const hw = (M.w - 0.24) / 2;

  L.card(s, { x: M.l, y: y2, w: hw, h: 2.64 });
  L.label(s, { x: M.l + 0.26, y: y2 + 0.20, w: hw - 0.52, text: 'Why response time falls further than handling time', color: C.white, size: 10.5 });
  L.bullets(s, {
    x: M.l + 0.26, y: y2 + 0.58, w: hw - 0.52, h: 1.92,
    items: [
      'Today, first response time is mostly queue wait. A case is understood only when an agent reaches it, so an urgent request sits behind routine ones.',
      'Under this model the case is understood in seconds, so a P1 or P2 is surfaced at the top of the queue immediately rather than on discovery.',
      'Every customer receives an acknowledgement with a case number and expected turnaround within seconds, which is itself a response time improvement.',
      'Escalation at 50, 70 and 85 percent of the clock means cases are recovered before breach rather than counted after it.',
      'The draft being ready means the agent first action is review and send, not open, research and compose.',
    ],
    size: 8.5, gap: 6,
  });

  L.card(s, { x: M.l + hw + 0.24, y: y2, w: hw, h: 2.64 });
  L.label(s, { x: M.l + hw + 0.50, y: y2 + 0.20, w: hw - 0.52, text: 'What this is worth beyond the numbers', color: C.white, size: 10.5 });
  const benefits = [
    ['Consistency', 'The same case type gets the same treatment on every shift, because the policy is in the workflow rather than in the individual.'],
    ['Faster competence', 'A new agent is productive sooner, because triage, context and a grounded draft compensate for experience they have not built yet.'],
    ['Capacity headroom', 'Released hours absorb volume growth and peak days without the service degrading.'],
    ['Senior time protected', 'Automation carries the routine, so senior agents spend their time on credits, disputes and exceptions.'],
    ['Defensible reporting', 'Because classification and SLA are structured data, performance conversations start from evidence.'],
  ];
  benefits.forEach((b, i) => {
    const y = y2 + 0.58 + i * 0.40;
    s.addText(b[0], {
      x: M.l + hw + 0.50, y, w: 1.35, h: 0.36, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 9, bold: true, color: C.cyan, valign: 'middle',
    });
    s.addText(b[1], {
      x: M.l + hw + 1.88, y, w: hw - 2.14, h: 0.38, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 8.5, color: C.mute, valign: 'middle', lineSpacing: 11,
    });
  });
  L.footnote(s, 'All figures are modelled design targets derived from the current operations sample. They are validated during the baseline period and only then proposed as commitments.');
  L.footer(s);
  s.addNotes('This is the slide the sponsor remembers. Handling time is the efficiency story, sub 60 second triage is the response time story. Both are stated as modelled, which is what makes them credible.');
}

/* ============================== 22  WHAT WE NEED ============================== */
{
  const s = L.newSlide(pptx);
  const top = L.header(s, {
    kicker: 'Next steps',
    title: 'What we need from McKesson to build this',
    sub: 'Phase 1 can begin with access and discovery alone. The licensing question only becomes a decision point at the Phase 2 gate.',
  });

  const groups = [
    ['Access and environment', C.cyan, [
      'Salesforce access and permissions for the delivery team',
      'Sandbox for configuration, testing and the supervised dry run',
      'Confirmation of the Extended Care mailboxes in scope',
      'Change control route for Flow, routing and Entitlement deployment',
    ]],
    ['Licensing decision', C.amber, [
      'Confirmation of current Einstein and Agentforce entitlement',
      'Whether Prompt Builder is available in the McKesson org today',
      'Appetite to pilot Agentforce on a narrow case type in Phase 3',
      'Security approval for generative features on PHI adjacent data',
    ]],
    ['Data and systems', C.cyan, [
      'Historical case data to baseline categories, mix and handling time',
      'Existing Knowledge articles, SOPs and email templates',
      'Read access to order and shipment data for grounding',
      'Definition of premium and VIP account treatment',
    ]],
    ['People and decisions', C.cyan, [
      'Process owners and subject matter experts for discovery',
      'Sign off on the case taxonomy, priority rules and SLA targets',
      'Named owners for pricing, AR and other dependency escalation paths',
      'A McKesson service owner for the governance cadence',
    ]],
  ];
  const cw = (M.w - 0.22) / 2, chh = 1.86;
  groups.forEach((g, i) => {
    const x = M.l + (i % 2) * (cw + 0.22);
    const y = top + Math.floor(i / 2) * (chh + 0.22);
    L.card(s, { x, y, w: cw, h: chh });
    s.addText(g[0], {
      x: x + 0.26, y: y + 0.18, w: cw - 0.52, h: 0.28, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 12, bold: true, color: g[1], valign: 'middle',
    });
    L.bullets(s, { x: x + 0.26, y: y + 0.54, w: cw - 0.52, h: 1.22, items: g[2], size: 9, gap: 5 });
  });

  const y2 = top + 2 * (chh + 0.22) + 0.04;
  s.addShape('roundRect', { x: M.l, y: y2, w: M.w, h: 0.56, rectRadius: 0.04, fill: { color: C.panel2 }, line: { color: C.cyan, width: 1 } });
  s.addText([
    { text: 'PROPOSED NEXT STEP   ', options: { bold: true, color: C.cyan, charSpacing: 1.4, fontSize: 9 } },
    { text: 'A joint design workshop on the case taxonomy, priority rules and SLA definitions, run alongside a technical discovery session on the McKesson Salesforce configuration and current Einstein entitlement.', options: { color: C.txt, fontSize: 9 } },
  ], { x: M.l + 0.22, y: y2, w: M.w - 0.44, h: 0.56, isTextBox: true, margin: 0, fontFace: F, valign: 'middle', lineSpacing: 12 });
  L.footer(s);
  s.addNotes('Close on the ask. The licensing box is deliberately amber: it is the only open question, and Phase 1 does not wait on it.');
}

/* ============================== 23  CLOSE ============================== */
{
  const s = L.newSlide(pptx);
  L.brandOrbs(s, { x: 9.05, y: 2.30, d: 2.65 });
  s.addImage({ path: L.ASSET.wordmark, x: M.l, y: 0.55, w: 2.15, h: 0.537 });
  L.brandDots(s, { x: M.l, y: 2.62 });
  s.addText('INTELLIGENT CASE MANAGEMENT', {
    x: M.l, y: 3.06, w: 10, h: 0.30, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 11, bold: true, color: C.cyan, charSpacing: 2.4, valign: 'middle',
  });
  s.addText('Agents spend their time on the\ncases that need judgement.', {
    x: M.l, y: 3.44, w: 10.5, h: 1.40, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 34, bold: true, color: C.white, lineSpacing: 42, valign: 'top',
  });
  s.addText('Salesforce reads, classifies, prioritises, routes, times, summarises and drafts. Insight Global owns the operation, the quality and the outcome.', {
    x: M.l, y: 5.02, w: 8.6, h: 0.64, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 12.5, color: C.mute, lineSpacing: 18, valign: 'top',
  });
  s.addText('Thank you', {
    x: M.l, y: 6.52, w: 6, h: 0.32, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 13, bold: true, color: C.txt, valign: 'middle',
  });
  s.addNotes('Close. The one line to leave in the room: agents spend their time on the cases that need judgement.');
}

/* ============================== WRITE ============================== */
pptx.writeFile({ fileName: 'McKesson_Intelligent_Case_Management.pptx' })
  .then(f => console.log('written:', f))
  .catch(e => { console.error('FAILED', e); process.exit(1); });
