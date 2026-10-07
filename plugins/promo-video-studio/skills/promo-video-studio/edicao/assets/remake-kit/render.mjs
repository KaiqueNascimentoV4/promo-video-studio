// render.mjs — renderizador Playwright/Chromium (deviceScaleFactor 1) do motor de quadro.
//   node render.mjs stills  <quadros> [--out DIR]    quadros: "0,5,10-20" ou "100-140:5"   (máx. 15 por chamada)
//   node render.mjs compare <quadros> [--out DIR]    REF | NOSSO | DIFERENÇA + métricas (tools/compare.py)
//   node render.mjs full    <f0> <f1> [--out DIR]    render completo de um bloco (rode 2–3 blocos em paralelo, no máximo)
// WARPED=1 → os números são quadros de SAÍDA com o TIMEMAP (seekK). OUT=dir ou --out separa agentes em paralelo.
// Imprime os erros da página. PNG na resolução de visualização (PROJECT.W × VIEW_SCALE).
import { createRequire } from 'module';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import { fileURLToPath } from 'url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
let pw;
for (const m of ['playwright', 'playwright-core', path.join(process.env.APPDATA || '', 'npm', 'node_modules', 'playwright'),
  path.join(process.env.HOME || '', '.npm-global', 'lib', 'node_modules', 'playwright')]) {
  try { pw = require(m); break; } catch {}
}
if (!pw) { console.error('playwright não encontrado: npm i playwright && npx playwright install chromium'); process.exit(2); }

const P = JSON.parse(fs.readFileSync(path.join(ROOT, 'project.json'), 'utf8'));
const S = P.VIEW_SCALE || 1, VW = Math.round(P.W * S), VH = Math.round(P.H * S);
const args = process.argv.slice(2), mode = args[0];
if (!['stills', 'compare', 'full'].includes(mode)) { console.error('modo: stills | compare | full'); process.exit(2); }
let outDir = process.env.OUT;
const oi = args.indexOf('--out');
if (oi >= 0) { outDir = args[oi + 1]; args.splice(oi, 2); }
outDir = path.resolve(ROOT, outDir || `out/${mode}`);
fs.mkdirSync(outDir, { recursive: true });

function parseFrames(spec) {
  const out = [];
  for (const part of String(spec).split(',')) {
    const [range, step] = part.split(':');
    if (range.includes('-')) { const [a, b] = range.split('-').map(Number); for (let f = a; f <= b; f += Number(step || 1)) out.push(f); }
    else if (range !== '') out.push(Number(range));
  }
  return out;
}
let frames;
if (mode === 'full') { const a = +args[1], b = +args[2]; frames = []; for (let f = a; f <= b; f++) frames.push(f); }
else frames = parseFrames(args[1] || '0');
if (mode !== 'full' && frames.length > 15 && !process.env.ALLOW_MANY) { console.error(`recusado: ${frames.length} quadros (> 15). ALLOW_MANY=1 força.`); process.exit(2); }

// servidor estático (canvas getImageData exige mesma origem; file:// contamina)
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(p).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'max-age=3600' });
    res.end(data);
  });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await pw.chromium.launch({
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--hide-scrollbars',
    '--font-render-hinting=none', '--disable-lcd-text', '--force-color-profile=srgb'],
});
const page = await browser.newPage({ viewport: { width: VW, height: VH }, deviceScaleFactor: 1 });
let errors = 0;
page.on('pageerror', e => { errors++; console.error('ERRO NA PÁGINA:', e.message); });
page.on('console', m => { if (m.type() === 'error' && !m.text().startsWith('Failed to load resource')) console.error('console:', m.text()); });  // shots/G*.js ausentes = 404 esperado
await page.goto(`http://127.0.0.1:${port}/index.html`, { waitUntil: 'load' });
await page.waitForFunction('window.ready === true', null, { timeout: 60000 });

const t0 = Date.now(); let n = 0;
for (const F of frames) {
  await page.evaluate(([f, warped]) => (warped ? window.seekK(f) : window.seekF(f)), [F, !!process.env.WARPED]);
  await page.locator('#view').screenshot({ path: path.join(outDir, `f${String(F).padStart(4, '0')}.png`), type: 'png', animations: 'disabled', caret: 'hide' });
  n++;
  if (mode === 'full' && F % 50 === 0) console.log(`quadro ${F} (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
}
await browser.close(); server.close();
console.log(`${n} quadros → ${path.relative(ROOT, outDir) || '.'}  erros na página: ${errors}  (${((Date.now() - t0) / n / 1000).toFixed(2)} s/quadro)`);
if (mode === 'compare') {
  const r = spawnSync(process.platform === 'win32' ? 'python' : 'python3', [path.join(ROOT, 'tools', 'compare.py'), outDir, frames.join(',')], { stdio: 'inherit' });
  process.exit(r.status || 0);
}
process.exit(errors ? 1 : 0);
