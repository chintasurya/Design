// Render deck slides to exact 1600x900 PNGs via the Chrome DevTools Protocol.
// Usage: node tools/shot.mjs [outDir] [scale] [extraQuery] [namePrefix]
//   scale 2 renders at 3200x1800 (for PowerPoint / print).
//   extraQuery e.g. "&bg=1" renders the artwork with the editable copy hidden.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const DIR = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = resolve(process.argv[2] || `${DIR}/export`);
const CHROME = process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const PORT = 9333;
const W = 1600, H = 900;
const SCALE = Number(process.argv[3]) || 1;
const EXTRA = process.argv[4] || '';
const PREFIX = process.argv[5] || 'shieldforge-slide-0';

mkdirSync(OUT, { recursive: true });

const chrome = spawn(CHROME, [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
  '--force-device-scale-factor=1', `--remote-debugging-port=${PORT}`,
  '--no-first-run', '--user-data-dir=/tmp/cdp-profile', 'about:blank'
], { stdio: 'ignore' });

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function endpoint() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/version`);
      return (await r.json()).webSocketDebuggerUrl;
    } catch { await sleep(250); }
  }
  throw new Error('chrome did not start');
}

class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.waiting = new Map(); this.events = new Map();
    ws.onmessage = e => {
      const m = JSON.parse(e.data);
      if (m.id && this.waiting.has(m.id)) { this.waiting.get(m.id)(m.result); this.waiting.delete(m.id); }
      if (m.method && this.events.has(m.method)) { this.events.get(m.method)(); this.events.delete(m.method); }
    };
  }
  send(method, params = {}, sessionId) {
    const id = ++this.id;
    return new Promise(res => {
      this.waiting.set(id, res);
      this.ws.send(JSON.stringify({ id, method, params, sessionId }));
    });
  }
  once(method) { return new Promise(res => this.events.set(method, res)); }
}

const wsUrl = await endpoint();
const ws = new WebSocket(wsUrl);
await new Promise(r => ws.onopen = r);
const cdp = new CDP(ws);

const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });

await cdp.send('Page.enable', {}, sessionId);
await cdp.send('Emulation.setDeviceMetricsOverride',
  { width: W, height: H, deviceScaleFactor: SCALE, mobile: false }, sessionId);

for (const i of [1, 2, 3]) {
  const loaded = cdp.once('Page.loadEventFired');
  await cdp.send('Page.navigate', { url: `file://${DIR}/index.html?solo=${i}${EXTRA}` }, sessionId);
  await loaded;
  await cdp.send('Runtime.evaluate', { expression: 'document.fonts.ready', awaitPromise: true }, sessionId);
  await sleep(350);
  const { data } = await cdp.send('Page.captureScreenshot', {
    format: 'png', captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: W, height: H, scale: 1 }
  }, sessionId);
  const file = `${OUT}/${PREFIX}${i}.png`;
  writeFileSync(file, Buffer.from(data, 'base64'));
  console.log(`  wrote ${file}`);
}

ws.close();
chrome.kill();
