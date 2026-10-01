// Valida o pacote After Effects sem ter o AE: desenha cada texto de ae_data.json pelas regras do AE
// (point text ancorado na linha de base, alinhamento, rotação no centro) sobre um still da base sem texto.
// Compare o resultado com um still do vídeo original no mesmo tempo.
//
//   node ae_sim.mjs --data ae_data.json --base stills_base/t_7.50.jpg --t 7.5 --out sim_7.5.jpg
//   (stills da base: node render.mjs --page projeto.html --dur 45 --stills 7.5 --stills-dir stills_base --layer base)
import { createRequire } from 'node:module';
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, arr) => { if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1]]); return acc; }, []));
if (!args.data || !args.base || !args.t) { console.log('uso: node ae_sim.mjs --data ae_data.json --base still_base.jpg --t 7.5 [--out sim.jpg]'); process.exit(1); }
function loadPlaywright() { for (const base of [process.cwd(), path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'))]) {
  try { return createRequire(path.join(base, 'noop.js'))('playwright-core'); } catch {} try { return createRequire(path.join(base, 'noop.js'))('playwright'); } catch {} }
  console.error('playwright-core não encontrado (npm i playwright-core)'); process.exit(1); }
function findChrome() { if (process.env.CHROME && fs.existsSync(process.env.CHROME)) return process.env.CHROME;
  for (const r of [path.join(process.env.LOCALAPPDATA || '', 'ms-playwright'), path.join(os.homedir(), 'Library', 'Caches', 'ms-playwright'), path.join(os.homedir(), '.cache', 'ms-playwright')]) {
    if (!fs.existsSync(r)) continue; for (const d of fs.readdirSync(r).filter(d => /^chromium-\d+$/.test(d)).sort().reverse())
      for (const sub of ['chrome-win64/chrome.exe', 'chrome-win/chrome.exe', 'chrome-linux/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium']) { const p = path.join(r, d, sub); if (fs.existsSync(p)) return p; } } }

const data = JSON.parse(fs.readFileSync(args.data, 'utf8'));
const FAM = { InterTight: 'Inter Tight', JetBrainsMono: 'JetBrains Mono', PermanentMarker: 'Permanent Marker', GochiHand: 'Gochi Hand', DMSans: 'DM Sans', GeistMono: 'Geist Mono', BebasNeue: 'Bebas Neue' };
const WN = { Thin: 100, ExtraLight: 200, Light: 300, Regular: 400, Medium: 500, SemiBold: 600, Bold: 700, ExtraBold: 800, Black: 900 };
const css = ps => { const [f, w] = ps.split('-'); return { family: FAM[f] || f.replace(/([a-z])([A-Z])/g, '$1 $2'), weight: WN[w] || 400 }; };
const fams = {}; for (const t of data.texts) { const c = css(t.font); (fams[c.family] ||= new Set()).add(c.weight); }
const link = 'https://fonts.googleapis.com/css2?' + Object.entries(fams).map(([f, ws]) => 'family=' + f.replace(/ /g, '+') + (ws.size > 1 || ![...ws].includes(400) ? ':wght@' + [...ws].sort().join(';') : '')).join('&') + '&display=block';

const { chromium } = loadPlaywright();
const browser = await chromium.launch({ executablePath: findChrome(), args: ['--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const img = 'data:image/jpeg;base64,' + fs.readFileSync(args.base).toString('base64');
await page.setContent(`<html><head><link href="${link}" rel="stylesheet"><style>html,body{margin:0;background:#000}</style></head><body><canvas id=c width=1920 height=1080></canvas></body></html>`);
await page.evaluate(async ([texts, t, img, fonts]) => {
  for (const f of fonts) await document.fonts.load(f); await document.fonts.ready;
  const g = document.getElementById('c').getContext('2d'), im = new Image(); im.src = img; await im.decode(); g.drawImage(im, 0, 0);
  for (const x of texts) { if (t < x.tin || t >= x.tout) continue; g.save(); g.font = x._css; g.letterSpacing = (x.tracking / 1000 * x.size) + 'px';
    g.fillStyle = `rgb(${x.color.map(v => v * 255 | 0).join(',')})`; g.textAlign = x.just; g.textBaseline = 'alphabetic';
    g.translate(x.center[0], x.center[1]); g.rotate((x.rot || 0) * Math.PI / 180); g.translate(x.base[0] - x.center[0], x.base[1] - x.center[1]);
    x.text.split('\r').forEach((l, i) => g.fillText(l, 0, i * x.leading)); g.restore(); }
}, [data.texts.map(x => { const c = css(x.font); return { ...x, _css: `${c.weight} ${x.size}px '${c.family}'` }; }), +args.t, img,
    data.texts.map(x => { const c = css(x.font); return `${c.weight} 40px '${c.family}'`; })]);
const out = args.out || `sim_${args.t}.jpg`; await page.screenshot({ path: out, type: 'jpeg', quality: 90 }); await browser.close(); console.log('sim ->', out);
