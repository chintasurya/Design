const pptxgen = require('pptxgenjs');
const sharp = require('sharp');
(async () => {
  const W = 1428, H = 166;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
  <rect width="100%" height="100%" fill="#0b0b0c"/>
  <defs>
   <radialGradient id="a" cx="0.05" cy="0.6" r="0.35"><stop offset="0" stop-color="#8a1a4a"/><stop offset="1" stop-color="#8a1a4a" stop-opacity="0"/></radialGradient>
   <radialGradient id="b" cx="0.33" cy="0.1" r="0.3"><stop offset="0" stop-color="#b8531a"/><stop offset="1" stop-color="#b8531a" stop-opacity="0"/></radialGradient>
   <radialGradient id="c" cx="0.48" cy="0.2" r="0.25"><stop offset="0" stop-color="#8a8a20"/><stop offset="1" stop-color="#8a8a20" stop-opacity="0"/></radialGradient>
   <radialGradient id="d" cx="0.62" cy="0.3" r="0.3"><stop offset="0" stop-color="#1f6e3a"/><stop offset="1" stop-color="#1f6e3a" stop-opacity="0"/></radialGradient>
   <radialGradient id="e" cx="0.5" cy="1.1" r="0.3"><stop offset="0" stop-color="#1c3c7a"/><stop offset="1" stop-color="#1c3c7a" stop-opacity="0"/></radialGradient>
   <radialGradient id="f" cx="0.85" cy="0.1" r="0.3"><stop offset="0" stop-color="#0f4a2a"/><stop offset="1" stop-color="#0f4a2a" stop-opacity="0"/></radialGradient>
  </defs>
  ${['a','b','c','d','e','f'].map(i=>`<rect width="100%" height="100%" fill="url(#${i})"/>`).join('')}
  </svg>`;
  const bg = await sharp(Buffer.from(svg)).resize(W*2, H*2).png().toBuffer();

  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE';
  const s = pres.addSlide();
  s.background = { color: 'FFFFFF' };
  const F = 'Arial', PINK = 'F0106E', INK = '111111';
  const hdrH = 1.55, leftW = 3.35;

  s.addImage({ data: 'image/png;base64,' + bg.toString('base64'), x: 0, y: 0, w: 13.333, h: hdrH });
  s.addText('INSIGHT GLOBAL: CASE STUDY', { isTextBox: true, x: 0.47, y: 0.36, w: 6, h: 0.22, margin: 0, fontFace: F, fontSize: 10, bold: true, color: 'FFFFFF', charSpacing: 3 });
  s.addText('Event-Driven Patient Registration & Identity Matching with Salesforce and Ascension Care ID',
    { isTextBox: true, x: 0.47, y: 0.55, w: 10.3, h: 0.95, margin: 0, fontFace: F, fontSize: 28, bold: true, color: 'FFFFFF', valign: 'top', lineSpacingMultiple: 0.9 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 10.55, y: 0.1, w: 2.7, h: 0.42, rectRadius: 0.21, fill: { color: '000000', transparency: 100 }, line: { color: 'FFFFFF', width: 0.75 } });
  s.addText('Patient Identity & Registration', { isTextBox: true, x: 10.55, y: 0.1, w: 2.7, h: 0.42, margin: 0, align: 'center', valign: 'middle', fontFace: F, fontSize: 11.5, color: 'FFFFFF' });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: hdrH, w: leftW, h: 7.5 - hdrH, fill: { color: '000000' }, line: { color: '000000', width: 0 } });
  const lh = (t, y) => s.addText(t, { isTextBox: true, x: 0.18, y, w: 3.0, h: 0.25, margin: 0, fontFace: F, fontSize: 11.5, bold: true, color: 'FFFFFF', charSpacing: 4 });
  const lbody = () => ({ fontFace: F, fontSize: 10.5, color: 'FFFFFF' });
  lh('ABOUT THE CLIENT', 1.7);
  s.addText('Same national nonprofit health system. Integrated Ascension Care ID, the organization’s single sign-on identity platform, with Salesforce to register patients in real time, match them to existing records, and maintain one trusted patient profile across consumer and associate applications.',
    { isTextBox: true, x: 0.18, y: 1.97, w: 3.05, h: 1.6, margin: 0, valign: 'top', ...lbody() });
  lh('CHALLENGE', 3.45);
  s.addText([
    { text: 'As patients created Care ID accounts across digital channels, Salesforce had to recognize them instantly and link them to the correct record without duplicates or manual effort.', options: { breakLine: true, paraSpaceAfter: 6 } },
    { text: 'Patients, health plan members and prospective consumers lived in separate accounts with no shared identifier, creating duplicate profiles and fragmented service history.', options: { bullet: { indent: 12 }, breakLine: true, paraSpaceAfter: 3 } },
    { text: 'Identity changes (EMPI EUID, SmartHealth subscriber ID) happened outside Salesforce, and Shield-encrypted fields blocked standard Flow lookups.', options: { bullet: { indent: 12 } } },
  ], { isTextBox: true, x: 0.18, y: 3.72, w: 3.05, h: 3.5, margin: 0, valign: 'top', ...lbody() });

  const sx = 3.6, sw = 5.2;
  s.addText('SOLUTION', { isTextBox: true, x: sx, y: 1.8, w: 3, h: 0.25, margin: 0, fontFace: F, fontSize: 12, bold: true, color: INK, charSpacing: 4 });
  s.addText('Built an event-driven registration and identity-resolution framework on the Salesforce Platform (Person Accounts, Platform Events, Flow, Apex, External Services) connected to Ascension Care ID and the enterprise MPI.',
    { isTextBox: true, x: sx, y: 2.08, w: sw, h: 0.72, margin: 0, valign: 'top', fontFace: F, fontSize: 10.5, color: INK });
  const items = [
    ['Real-Time Event Processing', 'Care ID publishes a platform event whenever a profile is created or its EUID or SmartHealth subscriber details change; a platform event-triggered flow processes it instantly.'],
    ['Automated Patient Registration', 'Matches patients by EMPI EUID via Apex SOQL actions that support Shield-encrypted fields; when no match exists, retrieves and inserts the patient from EMPI and stamps the Care ID.'],
    ['Member & Prospect Matching', 'Calls the Care ID User Profile API (OAuth 2.0 External Service) to match health plan members by subscriber key and create prospect (Preclinical) accounts for new sign-ups.'],
    ['Duplicate Resolution & Merge', 'Flags duplicate prospect accounts for merge; an asynchronous flow re-parents cases, tasks and chat transcripts to the surviving patient or member account.'],
    ['Enterprise Identity Foundation', 'Care ID stored on the Account and carried in HealthConnect patient payloads, giving every Ascension application one shared patient identity.'],
  ];
  items.forEach(([h, b], i) => {
    const y = 2.85 + i * 0.73;
    s.addShape(pres.shapes.OVAL, { x: sx + 0.06, y: y + 0.07, w: 0.05, h: 0.05, fill: { color: INK }, line: { color: INK, width: 0 } });
    s.addText([{ text: h + ': ', options: { bold: true } }, { text: b }],
      { isTextBox: true, x: sx + 0.22, y, w: sw - 0.2, h: 0.7, margin: 0, valign: 'top', fontFace: F, fontSize: 10.5, color: INK });
  });

  const rx = 8.97;
  s.addText('RESULTS', { isTextBox: true, x: rx, y: 1.85, w: 3, h: 0.25, margin: 0, fontFace: F, fontSize: 12, bold: true, color: INK, charSpacing: 4 });
  const res = [
    ['1 ID', 'Single patient identity across Ascension apps'],
    ['Real-Time', 'Event-driven sync from Care ID to Salesforce'],
    ['3 Paths', 'Patient, Member & Prospect record matching'],
    ['Auto-Merge', 'Duplicates merged with cases, tasks & chats moved'],
  ];
  res.forEach(([n, l], i) => {
    const y = 2.25 + i * 1.08;
    s.addText(n, { isTextBox: true, x: rx, y, w: 4, h: 0.55, margin: 0, fontFace: F, fontSize: 36, color: PINK, valign: 'bottom' });
    s.addText(l, { isTextBox: true, x: rx, y: y + 0.6, w: 4.0, h: 0.4, margin: 0, fontFace: F, fontSize: 10.5, color: INK, valign: 'top' });
  });

  s.addShape(pres.shapes.LINE, { x: 3.72, y: 6.68, w: 9.2, h: 0, line: { color: 'BBBBBB', width: 0.75, dashType: 'sysDot' } });
  s.addText('InsightGlobal', { isTextBox: true, x: 3.68, y: 6.83, w: 1.4, h: 0.3, margin: 0, fontFace: F, fontSize: 14, bold: true, color: '0B1F3A' });
  [['F0106E', 0], ['FFC20E', 0.09], ['00AEEF', 0.18]].forEach(([c, dx]) =>
    s.addShape(pres.shapes.OVAL, { x: 3.93 + dx, y: 7.15, w: 0.07, h: 0.07, fill: { color: c }, line: { color: c, width: 0 } }));
  s.addText([{ text: 'Connect with your IG partner directly or at ' }, { text: 'insightglobal.com', options: { color: PINK, underline: true, hyperlink: { url: 'https://insightglobal.com' } } }, { text: '.' }],
    { isTextBox: true, x: 5.7, y: 6.86, w: 3.3, h: 0.25, margin: 0, fontFace: F, fontSize: 8.5, color: INK });
  s.addText('© 2026 Insight Global', { isTextBox: true, x: 9.65, y: 6.86, w: 1.5, h: 0.25, margin: 0, fontFace: F, fontSize: 8.5, color: INK });
  s.addText('© 2026 Insight Global', { isTextBox: true, x: 11.35, y: 6.86, w: 1.5, h: 0.25, margin: 0, fontFace: F, fontSize: 8.5, color: INK });

  await pres.writeFile({ fileName: 'Care_ID_Patient_Registration_Case_Study.pptx' });
})();
