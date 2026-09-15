/**
 * Renders talktrack.js as a presenter handout (.docx) via a docx-ready JSON
 * handoff, so the deck notes and the handout always come from one source.
 */
const fs = require('fs');
const TT = require('./talktrack.js');
const total = TT.reduce((a, t) => a + t.secs, 0);
fs.writeFileSync('talktrack.json', JSON.stringify({
  slides: TT,
  totalMinutes: Math.round(total / 60),
}, null, 2));
console.log('talktrack.json written:', TT.length, 'slides,', Math.round(total / 60), 'min');
