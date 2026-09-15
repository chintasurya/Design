// Shared theme + layout helpers, matched to the McKesson proposal deck design system.
const C = {
  bg:    '0A0D14',  // slide ground
  panel: '151A24',  // card
  panel2:'1A2130',  // nested card / table stripe
  line:  '252D3D',  // hairline border
  txt:   'E6EAF2',  // body
  mute:  '8A94A6',  // secondary
  cyan:  '22D3EE',  // primary accent
  pink:  'FF0069',  // IG brand accent
  green: '22C55E',
  amber: 'F59E0B',
  white: 'FFFFFF',
};
const F  = 'Trenda IG Text';     // body, tables, bullets
const FD = 'Trenda IG Display';  // titles, display numerals, kickers
const M = { l: 0.55, r: 0.55, w: 12.23 };   // 13.333 wide slide
const ASSET = { wordmark: 'assets/ig-wordmark.png', mark: 'assets/ig-mark.png' };

let PAGE = 0;

function newSlide(pptx) {
  const s = pptx.addSlide();
  s.background = { color: C.bg };
  return s;
}

// Section kicker + title + optional standfirst. Returns the y where content may start.
function header(s, { kicker, title, sub, titleSize = 26 }) {
  let y = 0.42;
  if (kicker) {
    s.addText(kicker.toUpperCase(), {
      x: M.l, y, w: M.w, h: 0.24, isTextBox: true, margin: 0,
      fontFace: FD, fontSize: 10, bold: true, color: C.cyan, charSpacing: 2.2, valign: 'middle',
    });
    y += 0.30;
  }
  // Wrap aware: allocate real height so a long title never lands on the standfirst.
  const T = title.toUpperCase();
  const perLine = Math.floor(M.w / (titleSize * 0.0088));
  const lines = Math.max(1, Math.ceil(T.length / perLine));
  const tH = lines * (titleSize * 1.26 / 72);
  s.addText(T, {
    x: M.l, y, w: M.w, h: tH, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: titleSize, bold: true, color: C.white, charSpacing: 0.4,
    valign: 'middle', lineSpacing: titleSize * 1.16,
  });
  y += tH + 0.09;
  if (sub) {
    s.addText(sub, {
      x: M.l, y, w: M.w, h: 0.42, isTextBox: true, margin: 0,
      fontFace: F, fontSize: 11.5, color: C.mute, lineSpacing: 15, valign: 'top',
    });
    y += 0.52;
  }
  return y + 0.18;
}

function card(s, { x, y, w, h, fill = C.panel, line = C.line, radius = 0.04 }) {
  s.addShape('roundRect', {
    x, y, w, h, rectRadius: radius,
    fill: { color: fill }, line: { color: line, width: 1 },
  });
}

// Small numeral / label chip used as the deck's repeating motif.
function chip(s, { x, y, text, color = C.cyan, w = 0.34, h = 0.28, size = 10.5 }) {
  s.addShape('roundRect', {
    x, y, w, h, rectRadius: 0.05,
    fill: { color: C.bg }, line: { color, width: 1 },
  });
  s.addText(text, {
    x, y, w, h, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: size, bold: true, color, align: 'center', valign: 'middle',
  });
}

// Filled pill for naming a Salesforce component.
function pill(s, { x, y, w, h, text, color = C.cyan, size = 8.5 }) {
  s.addShape('roundRect', {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: C.panel2 }, line: { color: C.line, width: 1 },
  });
  s.addText(text, {
    x: x + 0.09, y, w: w - 0.18, h, isTextBox: true, margin: 0,
    fontFace: F, fontSize: size, color, valign: 'middle', lineSpacing: size + 2.5,
  });
}

function label(s, { x, y, w, text, color = C.mute, size = 9, h = 0.22, bold = true }) {
  s.addText(text.toUpperCase(), {
    x, y, w, h, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: size, bold, color, charSpacing: 1.4, valign: 'middle',
  });
}

function body(s, { x, y, w, h, text, size = 10, color = C.txt, lineSpacing }) {
  s.addText(text, {
    x, y, w, h, isTextBox: true, margin: 0,
    fontFace: F, fontSize: size, color, valign: 'top',
    lineSpacing: lineSpacing || size + 5,
  });
}

// Bulleted list with consistent paragraph spacing.
function bullets(s, { x, y, w, h, items, size = 10, color = C.txt, gap = 5 }) {
  s.addText(items.map((t, i) => ({
    text: t,
    options: { bullet: { code: '2022', indent: 12 }, breakLine: i !== items.length - 1 },
  })), {
    x, y, w, h, isTextBox: true, margin: 0,
    fontFace: F, fontSize: size, color, valign: 'top',
    paraSpaceAfter: gap, lineSpacing: size + 4, indentLevel: 0,
  });
}

// Big number + caption tile.
function stat(s, { x, y, w, h = 1.15, value, caption, color = C.cyan, valueSize = 27 }) {
  card(s, { x, y, w, h });
  s.addText(value, {
    x: x + 0.18, y: y + 0.12, w: w - 0.36, h: 0.52, isTextBox: true, margin: 0,
    fontFace: FD, fontSize: valueSize, bold: true, color, valign: 'middle',
  });
  s.addText(caption, {
    x: x + 0.18, y: y + 0.64, w: w - 0.36, h: h - 0.76, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 9, color: C.mute, valign: 'top', lineSpacing: 12,
  });
}

function footnote(s, text, y = 6.60) {
  s.addText(text, {
    x: M.l, y, w: M.w - 1.2, h: 0.38, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 7.5, italic: true, color: C.mute, valign: 'top', lineSpacing: 10,
  });
}

// Footer: IG dot mark + page number, on every content slide.
function footer(s) {
  PAGE += 1;
  s.addImage({ path: ASSET.mark, x: M.l, y: 7.06, w: 0.46, h: 0.158 });
  s.addText(String(PAGE), {
    x: 12.25, y: 7.0, w: 0.53, h: 0.26, isTextBox: true, margin: 0,
    fontFace: F, fontSize: 8.5, color: C.mute, align: 'right', valign: 'middle',
  });
}

// Three IG brand dots, used sparingly as the cover/closing motif.
function brandDots(s, { x, y, d = 0.19, gap = 0.1 }) {
  [C.cyan, 'FFC72C', C.pink].forEach((col, i) => {
    s.addShape('ellipse', {
      x: x + i * (d + gap), y, w: d, h: d,
      fill: { color: col }, line: { color: col, width: 0 },
    });
  });
}

// Large overlapping brand circles, echoing the source deck's closing motif.
// Used only on the cover and the closing slide.
function brandOrbs(s, { x, y, d = 2.5 }) {
  const set = [
    { c: C.cyan,  dx: 0,          dy: 0 },
    { c: 'FFC72C', dx: d * 0.52,  dy: 0 },
    { c: C.pink,  dx: d * 0.26,   dy: d * 0.45 },
  ];
  set.forEach(o => {
    s.addShape('ellipse', {
      x: x + o.dx, y: y + o.dy, w: d, h: d,
      fill: { color: o.c, transparency: 86 }, line: { color: o.c, width: 0 },
    });
  });
}

function arrow(s, { x, y, w = 0.26, h = 0.18, color = '3A4459' }) {
  s.addShape('rightArrow', { x, y, w, h, fill: { color }, line: { color, width: 0 } });
}

// Standard table styling so every dense table reads the same.
function tableOpts({ x, y, w, colW, rowH, fontSize = 9.5 }) {
  return {
    x, y, w, colW, rowH,
    fontFace: F, fontSize, color: C.txt, valign: 'middle',
    border: { type: 'solid', color: C.line, pt: 1 },
    autoPage: false,
  };
}
function th(text, opts = {}) {
  return { text, options: { bold: true, color: C.cyan, fill: { color: C.panel2 }, fontSize: 8.5, charSpacing: 1, valign: 'middle', margin: [4, 7, 4, 7], ...opts } };
}
function td(text, opts = {}) {
  return { text, options: { fill: { color: C.panel }, margin: [4, 7, 4, 7], valign: 'middle', ...opts } };
}

module.exports = { C, F, FD, M, ASSET, newSlide, header, card, chip, pill, label, body, bullets, stat, footnote, footer, brandDots, brandOrbs, arrow, tableOpts, th, td, resetPage: () => { PAGE = 0; } };

/* ---------------------------------------------------------------------------
 * Chart defaults.
 * Series colours are the validated categorical palette (dataviz reference,
 * dark column), confirmed against this deck's 0A0D14 surface: all six checks
 * pass. Brand cyan and pink stay on chrome (kickers, chips, rules) so series
 * colour always carries data identity and never brand emphasis.
 * ------------------------------------------------------------------------- */
const SERIES = ['3987E5', 'D95926', '199E70', 'C98500', 'D55181'];

function chartBase(extra = {}) {
  return {
    chartColors: SERIES,
    showLegend: false,
    showTitle: false,
    catAxisLabelColor: '8A94A6', catAxisLabelFontFace: F, catAxisLabelFontSize: 9,
    valAxisLabelColor: '8A94A6', valAxisLabelFontFace: F, valAxisLabelFontSize: 9,
    catAxisLineShow: false, valAxisLineShow: false,
    catGridLine: { style: 'none' },
    valGridLine: { color: '252D3D', size: 1 },
    chartArea: { fill: { color: '151A24' } },
    plotArea: { fill: { color: '151A24' } },
    dataLabelFontFace: F, dataLabelFontSize: 8, dataLabelColor: 'E6EAF2',
    legendFontFace: F, legendFontSize: 9, legendColor: 'E6EAF2',
    border: { pt: 1.5, color: '151A24' },  // 2px-equivalent surface gap between stacked segments
    ...extra,
  };
}

// Legend swatch + label, drawn by hand so it can sit where the layout wants it.
function legendRow(s, { x, y, items, size = 8.5, gap = 0.14, swatch = 0.11 }) {
  let cx = x;
  items.forEach(it => {
    s.addShape('roundRect', {
      x: cx, y: y + 0.055, w: swatch, h: swatch, rectRadius: 0.02,
      fill: { color: it.color }, line: { color: it.color, width: 0 },
    });
    const tw = it.label.length * size * 0.0079 + 0.06;
    s.addText(it.label, {
      x: cx + swatch + 0.07, y, w: tw, h: 0.22, isTextBox: true, margin: 0,
      fontFace: F, fontSize: size, color: 'E6EAF2', valign: 'middle',
    });
    cx += swatch + 0.07 + tw + gap;
  });
}

module.exports.SERIES = SERIES;
module.exports.chartBase = chartBase;
module.exports.legendRow = legendRow;
