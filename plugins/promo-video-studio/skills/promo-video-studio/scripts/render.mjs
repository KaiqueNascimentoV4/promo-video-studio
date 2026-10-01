#!/usr/bin/env node
// Render an animated HTML page (exposing window.__render(t) and window.__ready) to video or stills.
//
// Usage:
//   node render.mjs --page cena.html --dur 45 --out video_noaudio.mp4          # full render (H.264 CRF 14)
//   node render.mjs --page cena.html --dur 45 --stills 1.2,4,6.9 [--stills-dir stills]
//   node render.mjs --page cena.html --dur 45 --layer doodle --out L.mov       # transparent layer (qtrle alpha)
//   node render.mjs --page cena.html --export-ann ann.json                     # text annotations + scenes (Premiere)
// Options: --fps 60 --width 1920 --height 1080
// Needs `playwright-core` installed in the current folder (npm i playwright-core) and a Chromium
// (env CHROME, or Playwright's browsers in ms-playwright, or `npx playwright install chromium`).
// ffmpeg from env FFMPEG or PATH.
import { spawn, execSync } from 'node:child_process';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, arr) => {
  if (a.startsWith('--')) acc.push([a.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]); return acc; }, []));
if (args.help || !args.page) { console.log(fs.readFileSync(new URL(import.meta.url)).toString().split('\n').slice(1, 13).join('\n')); process.exit(args.page ? 0 : 1); }
const FPS = +(args.fps || 60), DUR = +(args.dur || 15), W = +(args.width || 1920), H = +(args.height || 1080);

function loadPlaywright() {
  for (const base of [process.cwd(), path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'))]) {
    try { return createRequire(path.join(base, 'noop.js'))('playwright-core'); } catch {}
    try { return createRequire(path.join(base, 'noop.js'))('playwright'); } catch {}
  }
  console.error('playwright-core não encontrado. Rode: npm i playwright-core  (na pasta do projeto)'); process.exit(1);
}
function findChrome() {
  if (process.env.CHROME && fs.existsSync(process.env.CHROME)) return process.env.CHROME;
  const roots = [path.join(process.env.LOCALAPPDATA || '', 'ms-playwright'), path.join(os.homedir(), 'Library', 'Caches', 'ms-playwright'), path.join(os.homedir(), '.cache', 'ms-playwright')];
  for (const r of roots) {
    if (!fs.existsSync(r)) continue;
    const dirs = fs.readdirSync(r).filter(d => /^chromium-\d+$/.test(d)).sort((a, b) => +b.split('-')[1] - +a.split('-')[1]);
    for (const d of dirs) for (const sub of ['chrome-win64/chrome.exe', 'chrome-win/chrome.exe', 'chrome-linux/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium']) {
      const p = path.join(r, d, sub); if (fs.existsSync(p)) return p; }
  }
  return undefined; // let Playwright use its default
}
function findFfmpeg() {
  if (process.env.FFMPEG && fs.existsSync(process.env.FFMPEG)) return process.env.FFMPEG;
  try { execSync(process.platform === 'win32' ? 'where ffmpeg' : 'which ffmpeg', { stdio: 'ignore' }); return 'ffmpeg'; } catch {}
  const home = os.homedir(); const docs = path.join(home, 'Documents');
  const walk = (dir, depth) => { if (depth < 0 || !fs.existsSync(dir)) return null; for (const e of fs.readdirSync(dir, { withFileTypes: true })) { if (!e.isDirectory()) continue;
      const p = path.join(dir, e.name); if (/ffmpeg/i.test(e.name) && fs.existsSync(path.join(p, 'bin', 'ffmpeg.exe'))) return path.join(p, 'bin', 'ffmpeg.exe'); const r = walk(p, depth - 1); if (r) return r; } return null; };
  const hit = walk(docs, 3); if (hit) return hit;
  console.error('ffmpeg não encontrado. Defina FFMPEG.'); process.exit(1);
}

const { chromium } = loadPlaywright();
const browser = await chromium.launch({ executablePath: findChrome(), args: ['--allow-file-access-from-files', '--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.resolve(args.page)).href + '?t=0');
await page.evaluate(() => window.__ready);
await page.waitForTimeout(300);

if (args.export) {   // --export dados.json --fn __aeExport : salva o retorno de qualquer função da página
  const data = await page.evaluate(fn => window[fn](), args.fn || '__aeExport');
  fs.writeFileSync(args.export, JSON.stringify(data, null, 1));
  console.log('exported', args.fn || '__aeExport', '->', args.export);
} else if (args['export-ann']) {
  const data = await page.evaluate(() => ({ ann: window.__annExport ? window.__annExport() : [], scenes: window.__scenes ? window.__scenes() : [] }));
  fs.writeFileSync(args['export-ann'], JSON.stringify(data, null, 1));
  console.log('exported', data.ann.length, 'texts,', data.scenes.length, 'scenes');
} else if (args.stills) {
  const dir = args['stills-dir'] || 'stills'; fs.mkdirSync(dir, { recursive: true });
  if (args.layer) await page.evaluate(m => window.__setLayer && window.__setLayer(m), args.layer);
  for (const t of String(args.stills).split(',').map(Number)) {
    await page.evaluate(t => window.__render(t), t);
    await page.screenshot({ path: path.join(dir, `t_${t.toFixed(2)}.jpg`), type: 'jpeg', quality: 88 });
  }
  console.log('stills ->', dir);
} else {
  const out = args.out || 'video_noaudio.mp4';
  const alpha = args.layer && args.layer !== 'base';
  if (args.layer) await page.evaluate(m => window.__setLayer && window.__setLayer(m), args.layer);
  const ffArgs = alpha
    ? ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-', '-c:v', 'qtrle', '-pix_fmt', 'argb', '-r', String(FPS), out]
    : ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', String(FPS), out];
  const ff = spawn(findFfmpeg(), ffArgs, { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(FPS * DUR), t0 = Date.now();
  for (let f = 0; f < N; f++) {
    await page.evaluate(t => window.__render(t), f / FPS);
    const buf = alpha ? await page.screenshot({ type: 'png', omitBackground: true }) : await page.screenshot({ type: 'jpeg', quality: 96 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (FPS * 5) === 0) console.log(`frame ${f}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('done', out);
}
await browser.close();
