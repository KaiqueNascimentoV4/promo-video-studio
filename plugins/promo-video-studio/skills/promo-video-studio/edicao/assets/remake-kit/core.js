/* core.js — motor de quadro determinístico para remakes 1:1 (e motion livre).
 * Palco = resolução NATIVA da referência (PROJECT.W × PROJECT.H, CSS px): todo número da SPEC vale 1:1.
 * Exibido em PROJECT.VIEW_SCALE na viewport do render. Cada quadro é FUNÇÃO PURA de F (0-based):
 * sem timers, Date, Math.random, transições/animações CSS, <video>.
 * Config: project.js (window.PROJECT) e brand.js (window.BRAND, window.SWAP_BANDS) — carregados ANTES deste arquivo.
 * API em window.C. Shots: SHOT({id, f0, f1, z?, render(lf, F) -> html, post?(el, lf, F) -> Promise}).
 */
(function () {
  const P = window.PROJECT || {};
  const W = P.W || 1920, H = P.H || 1080, FPS = (P.FPS_NUM || 30) / (P.FPS_DEN || 1), TOTAL = P.TOTAL || 300;
  const shots = [];

  /* ---------------- math ---------------- */
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const inv = (a, b, v) => (b === a ? 0 : (v - a) / (b - a));
  const prog = (F, a, b, ease) => (ease || E.linear)(clamp(inv(a, b, F)));

  function bezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = t => ((ax * t + bx) * t + cx) * t, sy = t => ((ay * t + by) * t + cy) * t, dx = t => (3 * ax * t + 2 * bx) * t + cx;
    return x => {
      if (x <= 0) return 0; if (x >= 1) return 1;
      let t = x;
      for (let i = 0; i < 8; i++) { const e = sx(t) - x, d = dx(t); if (Math.abs(e) < 1e-6 || !d) break; t -= e / d; }
      return sy(clamp(t));
    };
  }
  const E = {
    linear: t => t,
    inQuad: t => t * t, outQuad: t => 1 - (1 - t) * (1 - t), inOutQuad: t => (t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
    inCubic: t => t ** 3, outCubic: t => 1 - Math.pow(1 - t, 3), inOutCubic: t => (t < .5 ? 4 * t ** 3 : 1 - Math.pow(-2 * t + 2, 3) / 2),
    inQuart: t => t ** 4, outQuart: t => 1 - Math.pow(1 - t, 4), inOutQuart: t => (t < .5 ? 8 * t ** 4 : 1 - Math.pow(-2 * t + 2, 4) / 2),
    inQuint: t => t ** 5, outQuint: t => 1 - Math.pow(1 - t, 5), inOutQuint: t => (t < .5 ? 16 * t ** 5 : 1 - Math.pow(-2 * t + 2, 5) / 2),
    inExpo: t => (t === 0 ? 0 : Math.pow(2, 10 * t - 10)), outExpo: t => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
    inOutExpo: t => (t === 0 ? 0 : t === 1 ? 1 : t < .5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
    inSine: t => 1 - Math.cos((t * Math.PI) / 2), outSine: t => Math.sin((t * Math.PI) / 2), inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
    outBack: (t, s = 1.70158) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
    inBack: (t, s = 1.70158) => (s + 1) * t ** 3 - s * t * t,
    step: t => (t < 1 ? 0 : 1), bezier,
  };
  /* kf(F, [[f, v, ease?], ...]) — o ease da chave i vale para o trecho i-1 → i. v número ou array. */
  function kf(F, keys, defEase) {
    if (!keys.length) return 0;
    if (F <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [f1, v1, e] = keys[i];
      if (F <= f1) {
        const [f0, v0] = keys[i - 1];
        const t = (e || defEase || E.linear)(clamp(inv(f0, f1, F)));
        return Array.isArray(v0) ? v0.map((a, j) => lerp(a, v1[j], t)) : lerp(v0, v1, t);
      }
    }
    return keys[keys.length - 1][1];
  }
  /* samples(F, f0, arr) — trilhas MEDIDAS por quadro (arr[i] é do quadro f0+i), interpoladas. */
  function samples(F, f0, arr) {
    const x = clamp(F - f0, 0, arr.length - 1), i = Math.floor(x), t = x - i;
    const a = arr[i], b = arr[Math.min(i + 1, arr.length - 1)];
    if (Array.isArray(a)) return a.map((v, j) => (v == null ? null : lerp(v, b[j], t)));
    return lerp(a, b, t);
  }
  /* stepAt(F, [[f, valor], ...]) — último valor com f <= F (contadores, quadros segurados). */
  function stepAt(F, table, before) {
    let v = before !== undefined ? before : table[0][1];
    for (const [f, val] of table) { if (f <= F) v = val; else break; }
    return v;
  }
  /* held(F, quadrosDeMudança) — gráficos da ref que só mudam em alguns quadros (≈10–16 Hz): avalie em held(F). */
  function held(F, changes) { let h = changes[0]; for (const c of changes) { if (c <= F) h = c; else break; } return Math.min(h, F); }
  /* pulldown(F, f0, fase) — fonte 30 fps puxada para 23,976: índice avança 5 a cada 4 quadros. */
  const pulldown = (F, f0, phase = 0) => Math.floor((F - f0) * 1.25 + phase * 0.25 + 1e-6);

  /* ---------------- ruído determinístico ---------------- */
  function hash(n, seed = 0) {
    let x = Math.imul((n | 0) ^ 0x9e3779b9, 0x85ebca6b) ^ Math.imul(seed | 0, 0xc2b2ae35);
    x ^= x >>> 16; x = Math.imul(x, 0x7feb352d); x ^= x >>> 15; x = Math.imul(x, 0x846ca68b); x ^= x >>> 16;
    return (x >>> 0) / 4294967296;
  }
  const rng = seed => { let i = 0; return () => hash(i++, seed); };
  function noise1(x, seed = 0) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i, seed), hash(i + 1, seed), u); }

  /* ---------------- cor ---------------- */
  function hexToRgb(h) {
    h = h.replace('#', ''); if (h.length === 3 || h.length === 4) h = h.split('').map(c => c + c).join('');
    const n = parseInt(h.slice(0, 6), 16), a = h.length === 8 ? parseInt(h.slice(6, 8), 16) / 255 : 1;
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255, a];
  }
  function rgbToHsl(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2;
    if (mx === mn) return [0, 0, l];
    const d = mx - mn, s = l > .5 ? d / (2 - mx - mn) : d / (mx + mn);
    const h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return [h * 60, s, l];
  }
  function hslToRgb(h, s, l) {
    h = ((h % 360) + 360) % 360 / 360;
    if (!s) return [l * 255, l * 255, l * 255];
    const q = l < .5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q;
    const f = t => { t = (t + 1) % 1; return t < 1 / 6 ? p + (q - p) * 6 * t : t < .5 ? q : t < 2 / 3 ? p + (q - p) * (2 / 3 - t) * 6 : p; };
    return [f(h + 1 / 3) * 255, f(h) * 255, f(h - 1 / 3) * 255];
  }
  /* TROCA DE PALETA — UM filtro determinístico aplicado a todo HTML renderizado (bitmaps intocados).
   * SWAP_BANDS (brand.js): [{lo, hi, minS, target, center, spread, sMul?, lAdd?}] — toda cor saturada com matiz em
   * [lo, hi] vai para target + (h − center) × spread (degradês mantêm um pouco de variação); saturação × sMul,
   * luminosidade + lAdd (padrão: preservadas). Escreva nos shots as cores AMOSTRADAS da ref. */
  const BANDS = window.SWAP_BANDS || [];
  const SWAP = { on: true };
  function swapRgb(r, g, b) {
    if (!SWAP.on || !BANDS.length) return [r, g, b];
    const [h, s, l] = rgbToHsl(r, g, b);
    for (const B of BANDS) {
      const inBand = B.lo <= B.hi ? h >= B.lo && h <= B.hi : h >= B.lo || h <= B.hi;
      if (s >= (B.minS ?? 0.35) && inBand) {
        const c = B.center ?? (B.lo + B.hi) / 2;
        return hslToRgb(B.target + (h - c) * (B.spread ?? 0.45), clamp(s * (B.sMul ?? 1)), clamp(l + (B.lAdd ?? 0)));
      }
    }
    return [r, g, b];
  }
  const hx = v => Math.round(clamp(v, 0, 255)).toString(16).padStart(2, '0');
  function swapColor(str) {
    if (str[0] === '#') {
      const [r, g, b, a] = hexToRgb(str), [nr, ng, nb] = swapRgb(r, g, b);
      return '#' + hx(nr) + hx(ng) + hx(nb) + (str.length === 9 || str.length === 5 ? hx(a * 255) : '');
    }
    const m = str.match(/rgba?\(([^)]+)\)/i); if (!m) return str;
    const p = m[1].split(/[\s,\/]+/).filter(Boolean), [nr, ng, nb] = swapRgb(+p[0], +p[1], +p[2]);
    return p.length > 3 ? `rgba(${Math.round(nr)},${Math.round(ng)},${Math.round(nb)},${p[3]})` : `rgb(${Math.round(nr)},${Math.round(ng)},${Math.round(nb)})`;
  }
  /* Só cores dentro de style/fill/stroke/stop-color… — texto visível como "#3891" nunca é tocado; url(...) fica. */
  const COLOR_IN_ATTR = /(url\([^)]*\))|(#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3,4}\b|rgba?\([^)]*\))/g;
  function swapHTML(html) {
    return html.replace(/\b(style|fill|stroke|stop-color|flood-color|lighting-color|color)="([^"]*)"/g,
      (m, attr, val) => `${attr}="${val.replace(COLOR_IN_ATTR, (mm, keep, c) => (keep ? keep : swapColor(c)))}"`);
  }
  const col = c => swapColor(c);   // para canvas

  /* ---------------- marca (brand.js) ---------------- */
  const BRAND = window.BRAND || { name: 'Cliente', primary: '#FF6720', logo: null };
  const FONT = Object.assign({ sans: "'Inter', Arial, sans-serif", mono: "'JetBrains Mono', monospace" }, (P.FONT || {}));
  /* assets SVG recortados justo (viewBox = caixa da tinta). asset = {src, aspect: w/h} */
  const svgImg = (a, h, extra = '') => `<img src="${a.src}" style="display:block;height:${h}px;width:${(h * a.aspect).toFixed(2)}px;${extra}">`;
  /* maskFill — o logo como máscara CSS: qualquer cor/degradê sem redesenhar */
  function maskFill(a, h, fill = '#fff', extra = '') {
    const w = h * a.aspect;
    return `<div style="width:${w.toFixed(2)}px;height:${h}px;background:${fill};-webkit-mask:url(${a.src}) center/100% 100% no-repeat;mask:url(${a.src}) center/100% 100% no-repeat;${extra}"></div>`;
  }
  const logo = (h, fill = BRAND.primary, extra = '') => (BRAND.logo ? maskFill(BRAND.logo, h, fill, extra) : '');

  /* ---------------- layout ---------------- */
  const px = v => (typeof v === 'number' ? v.toFixed(3) + 'px' : v);
  const abs = (x, y, inner, extra = '') => `<div style="position:absolute;left:${px(x)};top:${px(y)};${extra}">${inner}</div>`;
  const full = (inner, extra = '') => `<div style="position:absolute;inset:0;${extra}">${inner}</div>`;
  const bg = c => `<div style="position:absolute;inset:0;background:${c}"></div>`;
  /* camera(inner, {scale, tx, ty, ox, oy, rot, rx, ry, persp, blur}) — embrulha uma camada de quadro inteiro */
  function camera(inner, o = {}) {
    const { scale = 1, tx = 0, ty = 0, ox = W / 2, oy = H / 2, rot = 0, rx = 0, ry = 0, persp = 0, blur = 0, extra = '' } = o;
    const t = `${persp ? `perspective(${persp}px) ` : ''}translate(${tx}px,${ty}px) rotate(${rot}deg) rotateX(${rx}deg) rotateY(${ry}deg) scale(${scale})`;
    return `<div style="position:absolute;inset:0;transform-origin:${ox}px ${oy}px;transform:${t};${blur ? `filter:blur(${blur}px);` : ''}${extra}">${inner}</div>`;
  }
  const zoomLin = (lf, n, s0, s1) => lerp(s0, s1, clamp(lf / Math.max(1, n - 1)));

  /* ---------------- filtros SVG (registrados uma vez, por id) ---------------- */
  const filterDefs = new Map();
  function defFilter(id, body) { if (!filterDefs.has(id)) filterDefs.set(id, `<filter id="${id}" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">${body}</filter>`); return id; }
  function mbFilter(sx, sy) { const id = `mb_${Math.round(sx * 10)}_${Math.round(sy * 10)}`; return defFilter(id, `<feGaussianBlur stdDeviation="${sx.toFixed(1)} ${sy.toFixed(1)}"/>`); }
  /* mblur(inner, ânguloGraus, sigma) — motion blur direcional (0 = horizontal). Confira se a REF tem blur antes de usar. */
  function mblur(inner, angle = 0, amount = 0, extra = '') {
    if (amount < 0.3) return `<div style="position:absolute;inset:0;${extra}">${inner}</div>`;
    const id = mbFilter(amount, 0);
    return `<div style="position:absolute;inset:0;transform:rotate(${angle}deg);filter:url(#${id});${extra}"><div style="position:absolute;inset:0;transform:rotate(${-angle}deg)">${inner}</div></div>`;
  }
  /* rgbSplit — aberração cromática: R deslocado (rx,ry), B (bx,by) */
  function rgbSplit(inner, rx = -1, ry = -1, bx = 1, by = 1, extra = '') {
    const id = defFilter(`rgb_${rx}_${ry}_${bx}_${by}`.replace(/\./g, 'p').replace(/-/g, 'm'),
      `<feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r"/><feOffset in="r" dx="${rx}" dy="${ry}" result="ro"/>` +
      `<feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="g"/>` +
      `<feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="b"/><feOffset in="b" dx="${bx}" dy="${by}" result="bo"/>` +
      `<feBlend in="ro" in2="g" mode="screen" result="rg"/><feBlend in="rg" in2="bo" mode="screen"/>`);
    return `<div style="position:absolute;inset:0;filter:url(#${id});${extra}">${inner}</div>`;
  }
  /* texturas fixas no quadro */
  function scanlines(period = 10, depth = 0.45, z = 50, duty = 0.35) {
    const d = Math.round(255 * (1 - depth)), a = (period * duty).toFixed(2), p = period.toFixed(2);
    return `<div style="position:absolute;inset:0;z-index:${z};pointer-events:none;mix-blend-mode:multiply;background:repeating-linear-gradient(0deg,rgb(${d},${d},${d}) 0px,rgb(255,255,255) ${a}px,rgb(255,255,255) ${p}px)"></div>`;
  }
  const vignette = (k = 0.6, z = 49) => `<div style="position:absolute;inset:0;z-index:${z};pointer-events:none;background:radial-gradient(ellipse 75% 75% at 50% 50%,rgba(0,0,0,0) 35%,rgba(0,0,0,${(1 - k).toFixed(3)}) 100%)"></div>`;
  /* dof — profundidade de campo falsa: elipse nítida em (cx,cy), blur crescendo para fora (cópias mascaradas) */
  function dof(inner, o = {}) {
    const { cx = W / 2, cy = H / 2, rx = W * 0.36, ry = H * 0.23, sigmas = [1.2, 2.5, 4.8] } = o;
    let out = `<div style="position:absolute;inset:0;filter:blur(${sigmas[0]}px)">${inner}</div>`;
    sigmas.slice(1).forEach((s, i) => {
      const k = (i + 1) / (sigmas.length - 1), r0 = 0.55 + 0.45 * (k - 1 / (sigmas.length - 1)), r1 = r0 + 0.45;
      const m = `radial-gradient(ellipse ${rx * (1 + k * 0.6)}px ${ry * (1 + k * 0.6)}px at ${cx}px ${cy}px,transparent ${Math.round(r0 * 100)}%,#000 ${Math.round(Math.min(1, r1) * 100)}%)`;
      out += `<div style="position:absolute;inset:0;filter:blur(${s}px);-webkit-mask-image:${m};mask-image:${m}">${inner}</div>`;
    });
    return `<div style="position:absolute;inset:0">${out}</div>`;
  }
  const flash = (over = '') => `<div style="position:absolute;inset:0;background:#fff"></div>${over}`;
  /* ripple(x, y, p, {r, color, width}) — onda de toque/clique, p 0..1 */
  const ripple = (x, y, p, o = {}) => { const { r = 60, color = 'rgba(255,255,255,.6)', width = 4 } = o, rr = r * E.outExpo(clamp(p));
    return `<div style="position:absolute;left:${px(x - rr)};top:${px(y - rr)};width:${px(2 * rr)};height:${px(2 * rr)};border-radius:50%;border:${width}px solid ${color};opacity:${(1 - p).toFixed(3)}"></div>`; };

  /* ---------------- texto ---------------- */
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const typeOn = (text, n) => text.slice(0, Math.max(0, Math.floor(n)));
  const measureCache = new Map(); let mctx = null;
  /* measure(text, font) — largura em px. SÓ depois das fontes carregarem (dentro do render, nunca no topo do arquivo). */
  function measure(text, font) {
    const k = font + '|' + text; if (measureCache.has(k)) return measureCache.get(k);
    if (!window.__fontsReady) throw new Error('measure() antes das fontes carregarem');
    mctx = mctx || document.createElement('canvas').getContext('2d'); mctx.font = font;
    const w = mctx.measureText(text).width; measureCache.set(k, w); return w;
  }
  const metricCache = new Map();
  function fontMetrics(font) {
    if (metricCache.has(font)) return metricCache.get(font);
    if (!window.__fontsReady) throw new Error('fontMetrics() antes das fontes carregarem');
    mctx = mctx || document.createElement('canvas').getContext('2d'); mctx.font = font;
    const m = mctx.measureText('Hg');
    const r = { asc: m.fontBoundingBoxAscent, desc: m.fontBoundingBoxDescent, cap: mctx.measureText('H').actualBoundingBoxAscent };
    metricCache.set(font, r); return r;
  }
  /* run — um texto posicionado pela LINHA DE BASE, exato */
  function run(text, left, baseline, font, tracking, color, extra = '') {
    const m = fontMetrics(font);
    return `<div style="position:absolute;left:${left.toFixed(2)}px;top:${(baseline - m.asc).toFixed(2)}px;height:${(m.asc + m.desc).toFixed(2)}px;line-height:${(m.asc + m.desc).toFixed(2)}px;white-space:pre;font:${font};letter-spacing:${tracking}em;color:${color};${extra}">${esc(text)}</div>`;
  }
  /* capToSize — font-size CSS que dá a altura de caixa-alta MEDIDA na ref */
  const capToSize = (cap, family = FONT.sans, weight = 700) => cap * 100 / fontMetrics(`${weight} 100px ${family}`).cap;
  /* wordLine — a linha INTEIRA é diagramada uma vez, centrada em cx; cada palavra fica no seu lugar final e só aparece
   * se visible[i] (sem recentralizar — como as refs fazem). Retorna {html, slots:[{x,w}], width}. */
  function wordLine(words, o = {}) {
    const { size = 112, family = FONT.sans, weight = 700, cx = W / 2, baseline = H / 2, tracking = -0.015, color = '#fff', visible = null, wordStyle = null, spaceEm = null } = o;
    const font = `${weight} ${size}px ${family}`;
    const sp = spaceEm != null ? spaceEm * size : measure(' ', font) + tracking * size;
    const ws = words.map(w => measure(w, font) + tracking * size * Math.max(0, [...w].length - 1));
    const total = ws.reduce((a, b) => a + b, 0) + sp * (words.length - 1);
    let x = cx - total / 2, html = ''; const slots = [];
    words.forEach((w, i) => { slots.push({ x, w: ws[i] }); if (!visible || visible[i]) html += run(w, x, baseline, font, tracking, color, wordStyle ? wordStyle(i) : ''); x += ws[i] + sp; });
    return { html, slots, width: total };
  }
  function textAt(text, x, baseline, o = {}) {
    const { size = 112, family = FONT.sans, weight = 700, tracking = -0.015, color = '#fff', anchor = 'left', extra = '' } = o;
    const font = `${weight} ${size}px ${family}`, w = measure(text, font) + tracking * size * Math.max(0, [...text].length - 1);
    return run(text, anchor === 'center' ? x - w / 2 : anchor === 'right' ? x - w : x, baseline, font, tracking, color, extra);
  }
  const fmtBR = (n, dec = 0) => Number(n).toLocaleString('pt-BR', { minimumFractionDigits: dec, maximumFractionDigits: dec });

  /* ---------------- cursor (pixel art; MEÇA o glifo da ref e ajuste cell) ---------------- */
  const ARROW = ['#...........', '##..........', '#o#.........', '#oo#........', '#ooo#.......', '#oooo#......', '#ooooo#.....', '#oooooo#....',
    '#ooooooo#...', '#oooooooo#..', '#ooooo#####.', '#oo#oo#.....', '#o#.#oo#....', '##..#oo#....', '#....#oo#...', '.....#oo#...', '......##....'];
  const HAND = ['....##..........', '...#oo#.........', '...#oo#.........', '...#oo#.........', '...#oo###.......', '...#oo#oo###....', '...#oo#oo#oo##..',
    '.###oo#oo#oo#o#.', '#oo#oooooooo#o#.', '#ooooooooooooo#.', '.#oooooooooooo#.', '.#ooooooooooo#..', '..#oooooooooo#..', '..#ooooooooo#...', '...#oooooooo#...', '...#oooooooo#...', '...##########...'];
  const IBEAM = ['###.###', '...#...', '...#...', '...#...', '...#...', '...#...', '...#...', '...#...', '...#...', '...#...', '...#...', '...#...', '...#...', '###.###'];
  function glyphSVG(rows, cell, ink = '#000', fill = '#fff') {
    let r = '';
    rows.forEach((row, y) => [...row].forEach((c, x) => { if (c === '#') r += `<rect x="${x}" y="${y}" width="1.02" height="1.02" fill="${ink}"/>`; else if (c === 'o') r += `<rect x="${x}" y="${y}" width="1.02" height="1.02" fill="${fill}"/>`; }));
    return `<svg width="${rows[0].length * cell}" height="${rows.length * cell}" viewBox="0 0 ${rows[0].length} ${rows.length}" shape-rendering="crispEdges" style="display:block">${r}</svg>`;
  }
  const GLY = { arrow: ARROW, hand: HAND, ibeam: IBEAM }, HOT = { arrow: [0, 0], hand: [5, 0], ibeam: [3, 7] };
  /* cursor(x, y, {type, cell, opacity, blur, press}) — (x,y) = ponta; press 0..1 = escala de clique medida (≈0,85 no fundo) */
  function cursor(x, y, o = {}) {
    const { type = 'arrow', cell = Math.round(W / 550), opacity = 1, blur = 0, press = 0 } = o;
    const rows = GLY[type] || ARROW, [hx0, hy0] = HOT[type] || [0, 0];
    const ink = type === 'hand' ? '#000' : '#fff', fillC = type === 'arrow' ? '#000' : '#fff', s = 1 - 0.15 * clamp(press);
    return `<div style="position:absolute;left:${px(x - hx0 * cell)};top:${px(y - hy0 * cell)};opacity:${opacity};transform-origin:${hx0 * cell}px ${hy0 * cell}px;transform:scale(${s});${blur ? `filter:blur(${blur}px);` : ''}">${glyphSVG(rows, cell, ink, fillC)}</div>`;
  }

  /* ---------------- mídia ---------------- */
  const clipInfo = {};   // preenchido por assets/footage/index.js (tools/footage.py)
  function footage(name, i) {
    const info = clipInfo[name], n = info ? info.n : 1, k = clamp(Math.floor(i), 0, n - 1) + 1;
    return `assets/footage/${name}/f${String(k).padStart(4, '0')}.jpg`;
  }
  const plate = (name, i, css = '') => `<img src="${footage(name, i)}" style="position:absolute;left:0;top:0;width:${W}px;height:${H}px;object-fit:cover;display:block;${css}">`;
  const img = (src, css = '') => `<img src="${src}" style="display:block;${css}">`;

  /* ---------------- registro de shots e seek ---------------- */
  function SHOT(s) {
    if (!s.id || s.f0 == null || s.f1 == null || !s.render) throw new Error('SHOT precisa de id, f0, f1, render');
    shots.push(s); shots.sort((a, b) => a.f0 - b.f0 || (a.z || 0) - (b.z || 0));
  }
  const shotsAt = F => shots.filter(s => F >= s.f0 && F <= s.f1);
  const stage = () => document.getElementById('stage');
  async function seekF(F) {
    const act = shotsAt(F); let html = '';
    for (const s of act) html += `<div class="shot" data-shot="${s.id}" style="position:absolute;inset:0;overflow:hidden;z-index:${s.z || 0}">${s.render(F - s.f0, F)}</div>`;
    html = swapHTML(html);
    stage().innerHTML = `<svg width="0" height="0" style="position:absolute"><defs>${[...filterDefs.values()].join('')}</defs></svg>` + html;
    for (const s of act) if (s.post) await s.post(stage().querySelector(`[data-shot="${s.id}"]`), F - s.f0, F);
    await decodeAll(stage());
    return F;
  }
  /* TIMEMAP opcional (PROJECT.TIMEMAP = [[F0, F1, fator], ...]): desacelerar trechos numa revisão ("muito rápido").
   * seekK(k) = quadro de SAÍDA k → quadro da ref F = FofK(k) (os gráficos são avaliados no quadro inteiro). */
  const TIMEMAP = P.TIMEMAP || [[0, TOTAL, 1]];
  function KofF(F) { let K = 0; for (const [a, b, w] of TIMEMAP) { if (F <= b) return K + (F - a) * w; K += (b - a) * w; } return K; }
  function FofK(k) { let K = 0; for (const [a, b, w] of TIMEMAP) { const L = (b - a) * w; if (k < K + L) return a + (k - K) / w; K += L; } return TOTAL; }
  const seekK = k => seekF(Math.floor(FofK(k) + 1e-9));
  const seek = t => seekF(Math.round(t * FPS));

  async function decodeAll(root) {
    const imgs = [...root.querySelectorAll('img')];
    await Promise.all(imgs.map(async i => {
      for (let t = 0; t < 4; t++) {
        try {
          if (!i.complete) await new Promise(r => { i.addEventListener('load', r, { once: true }); i.addEventListener('error', r, { once: true }); });
          if (i.naturalWidth) { await i.decode().catch(() => {}); return; }
        } catch (e) {}
        await new Promise(r => setTimeout(r, 60 * (t + 1)));
        if (!i.naturalWidth) { const s = i.src; i.src = ''; i.src = s; }
      }
      console.error('IMG FAIL ' + i.src);
    }));
    const urls = new Set();
    root.querySelectorAll('[style*="url("]').forEach(el => { for (const m of el.getAttribute('style').matchAll(/url\(([^)#][^)]*)\)/g)) urls.add(m[1].replace(/["']/g, '')); });
    await Promise.all([...urls].map(preload));
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  }
  const imgCache = new Map();
  function preload(src) {
    if (!imgCache.has(src)) imgCache.set(src, new Promise(res => { const i = new Image(); i.onload = () => i.decode().then(() => res(i), () => res(i)); i.onerror = () => { console.error('PRELOAD FAIL ' + src); res(null); }; i.src = src; }));
    return imgCache.get(src);
  }

  async function boot() {
    await document.fonts.ready;
    await Promise.all((P.FONTS_LOAD || []).map(([f, w]) => document.fonts.load(`${w} 40px '${f}'`).catch(() => {})));
    window.__fontsReady = true;
    const brandAssets = Object.values(BRAND).filter(v => v && typeof v === 'object' && v.src);
    await Promise.all(brandAssets.map(v => preload(v.src)));
    if (window.PRELOAD) await Promise.all(window.PRELOAD.map(preload));
    window.ready = true;
  }

  window.C = {
    W, H, FPS, TOTAL, E, clamp, lerp, inv, prog, kf, samples, stepAt, held, pulldown, bezier,
    hash, rng, noise1, hexToRgb, rgbToHsl, hslToRgb, swapColor, swapHTML, col, SWAP,
    BRAND, FONT, svgImg, maskFill, logo,
    px, abs, full, bg, camera, zoomLin, defFilter, mbFilter, mblur, rgbSplit, scanlines, vignette, dof, flash, ripple,
    esc, typeOn, measure, fontMetrics, run, capToSize, wordLine, textAt, fmtBR,
    cursor, glyphSVG, ARROW, HAND, IBEAM, footage, plate, clipInfo, img, preload,
    SHOT, shotsAt, shots, TIMEMAP, KofF, FofK,
  };
  window.SHOT = SHOT; window.seek = seek; window.seekF = seekF; window.seekK = seekK; window.ready = false;
  window.addEventListener('load', boot);
})();
