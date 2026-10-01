// Coletor de textos para o pacote After Effects (scripts/ae_package.py).
// Inclua na página DEPOIS do engine:  <script src="ae_export.js"></script>
// e defina window.__aeExport usando aeCollector (exemplo no fim do arquivo).
//
// Cada texto vira uma camada de texto nativa no AE com a mesma fonte, cor, tracking, entrelinha,
// posição (pela linha de base) e tempo. A animação é recriada por tipo:
//   {type:'fade', d}                 opacidade 0→100
//   {type:'slide', dx, dy, d}        desliza de (dx,dy) até a posição + fade curto
//   {type:'scale', from, dy?, d}     escala from%→100% (+ deslize opcional) + fade curto
//   {type:'stamp', from, d}          carimbo: escala from%→100%, aparece seco
//   {type:'reveal', d}               letra por letra (animador de texto)
//   {type:'karaoke', words:[t...]}   palavra por palavra acende (animador, tempos absolutos de cada palavra)
// opts: { own:true  → só o texto direto do elemento (ignora filhos com outro estilo, que viram camadas próprias),
//         neutral:[[el, transform]] → transform usado só durante a medida (tire rotação/escala da animação),
//         rot: graus (rotação final), expr: expression do Source Text (contadores, timecode),
//         group: nome da cena (ordena e numera as camadas no AE) }

const AE_FONT_MAP = { // família CSS → prefixo PostScript (acrescente as fontes da marca)
  'Inter': 'Inter', 'Inter Tight': 'InterTight', 'JetBrains Mono': 'JetBrainsMono', 'DM Sans': 'DMSans', 'Manrope': 'Manrope',
  'Geist Mono': 'GeistMono', 'Montserrat': 'Montserrat', 'Poppins': 'Poppins', 'Roboto': 'Roboto',
};
const AE_SINGLE = { 'Anton': 'Anton-Regular', 'Permanent Marker': 'PermanentMarker-Regular', 'Gochi Hand': 'GochiHand-Regular', 'Bebas Neue': 'BebasNeue-Regular' };
function aePostScript(fam, w) {
  fam = fam.split(',')[0].replace(/['"]/g, '').trim(); if (AE_SINGLE[fam]) return AE_SINGLE[fam];
  const WN = { 100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular', 500: 'Medium', 600: 'SemiBold', 700: 'Bold', 800: 'ExtraBold', 900: 'Black' };
  return (AE_FONT_MAP[fam] || fam.replace(/ /g, '')) + '-' + (WN[+w] || 'Regular');
}
const _aeCtx = document.createElement('canvas').getContext('2d');
function aeMeasure(el, own, neutral = []) {
  const saved = neutral.map(([e, tr]) => { const s = e.style.transform; e.style.transform = tr; return [e, s]; });
  const nodes = []; const walk = n => { for (const c of n.childNodes) { if (c.nodeType === 3) { if (c.textContent.trim()) nodes.push(c); } else if (!own && c.nodeType === 1) walk(c); } }; walk(el);
  if (!nodes.length) { saved.forEach(([e, s]) => e.style.transform = s); throw new Error('sem texto: ' + (el.id || el.className)); }
  const words = []; let prevSp = true;
  for (const nd of nodes) { const s = nd.textContent, re = /\S+/g; let m; while ((m = re.exec(s))) { const r = document.createRange(); r.setStart(nd, m.index); r.setEnd(nd, m.index + m[0].length);
      const sp = m.index > 0 ? /\s/.test(s[m.index - 1]) : prevSp; words.push({ w: m[0], sp, r: r.getClientRects()[0] || r.getBoundingClientRect() }); } prevSp = /\s$/.test(s); }
  const lines = []; for (const w of words) { let L = lines.find(l => Math.abs(l.top - w.r.top) < w.r.height * .5); if (!L) { L = { top: w.r.top, words: [] }; lines.push(L); } L.words.push(w); }
  lines.sort((a, b) => a.top - b.top);
  const st = getComputedStyle(nodes[0].parentElement), fs = parseFloat(st.fontSize);
  _aeCtx.font = `${st.fontWeight} ${fs}px ${st.fontFamily}`; const asc = _aeCtx.measureText('Hg').fontBoundingBoxAscent;
  const L0 = lines[0], l0 = Math.min(...L0.words.map(w => w.r.left)), r0 = Math.max(...L0.words.map(w => w.r.right));
  const just = st.textAlign === 'center' ? 'center' : (st.textAlign === 'right' || st.textAlign === 'end') ? 'right' : 'left';
  const all = words.map(w => w.r), ux0 = Math.min(...all.map(r => r.left)), ux1 = Math.max(...all.map(r => r.right)), uy0 = Math.min(...all.map(r => r.top)), uy1 = Math.max(...all.map(r => r.bottom));
  const ls = st.letterSpacing === 'normal' ? 0 : parseFloat(st.letterSpacing), lh = st.lineHeight === 'normal' ? fs * 1.2 : parseFloat(st.lineHeight);
  const col = st.color.match(/[\d.]+/g).map(Number), up = st.textTransform === 'uppercase';
  saved.forEach(([e, s]) => e.style.transform = s);
  return { text: lines.map(l => l.words.map((w, i) => (i && w.sp ? ' ' : '') + (up ? w.w.toUpperCase() : w.w)).join('')).join('\r'),
    font: aePostScript(st.fontFamily, st.fontWeight), size: fs, color: [col[0] / 255, col[1] / 255, col[2] / 255], tracking: Math.round(ls / fs * 1000),
    leading: Math.round(lh * 100) / 100, just, base: [(just === 'center' ? (l0 + r0) / 2 : just === 'right' ? r0 : l0), L0.top + asc],
    center: [(ux0 + ux1) / 2, (uy0 + uy1) / 2], nwords: words.length };
}
// render: a função window.__render(t) da página
function aeCollector(render) {
  const texts = [], images = [];
  return {
    texts, images,
    // tr = tempo "em repouso" (texto já entrou e está parado), tin/tout = entrada/saída da camada
    text(name, el, tr, tin, tout, anim = { type: 'fade', d: .3 }, o = {}) { render(tr); const e = typeof el === 'string' ? document.querySelector(el) : el;
      texts.push(Object.assign(aeMeasure(e, o.own, o.neutral || []), { name, group: o.group || name.split(' · ')[0], tin: Math.max(0, tin), tout, anim, rot: o.rot || 0, expr: o.expr || null })); },
    // imagem nativa (produto/logo): file = caminho dentro do pacote (ex. 'imagens/produto.png'), srcW = largura original em px
    // anchorFrac = origem do transform no CSS (ex. [.5,.6]); rise = entrada {dy, from, d}; bob = flutuação em px
    image(name, el, tr, tin, tout, file, srcW, o = {}) { render(tr); const e = typeof el === 'string' ? document.querySelector(el) : el, s = e.style.transform; e.style.transform = 'none';
      const r = e.getBoundingClientRect(); e.style.transform = s; const af = o.anchorFrac || [.5, .5];
      images.push({ name, group: o.group || name.split(' · ')[0], file, center: [r.left + r.width * af[0], r.top + r.height * af[1]], anchorFrac: af, scale: r.width / srcW * 100,
        tin, tout, rise: o.rise || null, bob: o.bob || 0 }); },
  };
}
/* Exemplo:
window.__aeExport = () => {
  const ae = aeCollector(render);
  ae.text('Abertura · título', '#titulo', 3.0, .5, 4.8, { type: 'scale', from: 118, d: .8 }, { neutral: [[document.querySelector('#titulo'), 'none']] });
  ae.text('Cena 2 · legenda', '#cap', 8.9, 5.0, 9.1, { type: 'karaoke', words: [5.0, 5.4, 5.9] });
  ae.image('Produto · imagem', '#produto', 44, 39.7, 49.2, 'imagens/produto.png', 1254, { anchorFrac: [.5, .6], rise: { dy: 260, from: 90, d: .9 }, bob: 6 });
  return { dur: DUR, texts: ae.texts, images: ae.images,
    overlays: [{ file: 'imagens/textura.png', name: 'FX · textura', tin: 0, tout: 36.9 }],   // PNGs por cima de tudo (opcional)
    grain: [[0, 6], [36.9, 3]],                                                             // [tempo, % de Noise] (opcional)
    markers: [{ name: 'Abertura', t: 0 }] };
};
*/
