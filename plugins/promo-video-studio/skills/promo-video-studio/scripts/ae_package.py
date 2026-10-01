"""Monta um pacote editável para After Effects: script .jsx que recria o vídeo com textos nativos, imagens nativas,
base renderizada sem textos, áudio (mix final + separados) e camadas organizadas por cena, em ordem cronológica.

Uso:
  node render.mjs --page projeto.html --export ae_data.json --fn __aeExport          # dados (ver assets/ae_export.js)
  node render.mjs --page projeto.html --dur 45 --layer base --out base.mp4           # base sem textos (página com body.L-base)
  python ae_package.py --data ae_data.json --base base.mp4 --out "C:/.../Projeto_AE" --name "Projeto" \
      [--file imagens/produto.png=assets/produto.png ...] [--mix mix.wav] [--stems stems.json --audio-dir stems/] \
      [--ref video_final.mp4] [--zip]

stems.json = [[arquivo, inicio_s, "voz"|"sfx"|"trilha", "nome legível opcional"], ...] (arquivos dentro de --audio-dir).
Sem After Effects na máquina, valide com scripts/ae_sim.mjs.
"""
import argparse, json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tools import ffmpeg  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--data', required=True); ap.add_argument('--out', required=True); ap.add_argument('--name', default='Projeto')
ap.add_argument('--base'); ap.add_argument('--file', action='append', default=[]); ap.add_argument('--mix')
ap.add_argument('--stems'); ap.add_argument('--audio-dir'); ap.add_argument('--ref'); ap.add_argument('--zip', action='store_true')
ap.add_argument('--fps', type=int, default=60)
a = ap.parse_args()

data = json.load(open(a.data, encoding='utf-8'))
data.setdefault('images', []); data.setdefault('overlays', []); data.setdefault('grain', []); data.setdefault('markers', [])
OUT = a.out; [os.makedirs(os.path.join(OUT, d), exist_ok=True) for d in ('video', 'imagens', 'audio')]

# ---------- mídia ----------
if a.base:  # base em bt709 tv-range (o render sai full range)
    subprocess.run([ffmpeg(), '-y', '-loglevel', 'error', '-i', a.base, '-vf', 'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                    '-color_range', 'tv', '-an', os.path.join(OUT, 'video', 'base_sem_texto.mp4')], check=True)
for spec in a.file:
    dst, src = spec.split('=', 1); os.makedirs(os.path.dirname(os.path.join(OUT, dst)), exist_ok=True); shutil.copy(src, os.path.join(OUT, dst))
if a.mix: shutil.copy(a.mix, os.path.join(OUT, 'audio', 'MIX_FINAL.wav'))
stems = []
if a.stems:
    for s in json.load(open(a.stems, encoding='utf-8')):
        f, t, kind = s[0], s[1], s[2]; nm = s[3] if len(s) > 3 else os.path.splitext(f)[0]
        shutil.copy(os.path.join(a.audio_dir or os.path.dirname(a.stems), f), os.path.join(OUT, 'audio', os.path.basename(f)))
        stems.append([os.path.basename(f), t, kind, nm])
if a.ref: os.makedirs(os.path.join(OUT, 'referencia'), exist_ok=True); shutil.copy(a.ref, os.path.join(OUT, 'referencia', os.path.basename(a.ref)))

# ---------- organização: cenas numeradas em ordem cronológica ----------
LABELS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15]
items = [('t', i, t) for i, t in enumerate(data['texts'])] + [('i', i, im) for i, im in enumerate(data['images'])]
first = {}
for _, i, x in items: first[x['group']] = min(first.get(x['group'], 1e9), x['tin'] + i * 1e-6)
order = sorted(first, key=first.get)
groups = []
for gi, g in enumerate(order):
    xs = [x for _, _, x in items if x['group'] == g]
    groups.append({'title': f"{gi + 1:02d} ==== {g.upper()} ====", 'tin': min(x['tin'] for x in xs), 'tout': max(x['tout'] for x in xs), 'label': LABELS[gi % len(LABELS)]})
gidx = {g: i for i, g in enumerate(order)}
for kind, i, x in items:
    x['g'] = gidx[x['group']]; item = x['name'].split(' · ', 1)[1] if x['name'].startswith(x['group'] + ' · ') else x['name']
    x['name'] = f"{x['g'] + 1:02d} {x['group']} · {item}"; x['ord'] = i
data['texts'].sort(key=lambda t: (t['g'], round(t['tin'], 2), t['ord']))
data['groups'] = groups
AG = len(groups) + 1
data['audioGroup'] = f"{AG:02d} ==== AUDIO ===="
stems.sort(key=lambda s: ({'voz': 0, 'sfx': 1, 'trilha': 2}.get(s[2], 3), s[1]))
for s in stems: s[3] = f"{AG:02d} AUDIO · {s[2]} · {s[3]}"
data['hasBase'] = bool(a.base); data['hasMix'] = bool(a.mix)
FONTS = sorted({t['font'] for t in data['texts']})

JSX = r'''// __NAME__ - projeto editavel para After Effects (gerado pela skill promo-video-studio)
// File > Scripts > Run Script File... e escolha este arquivo. Mantenha-o junto das pastas video/, imagens/ e audio/.
(function () {
var DATA = __DATA__;
var STEMS = __STEMS__;
var FONTS = __FONTS__;
var NAME = __NAMEJS__;
var root = new File($.fileName).parent;
function imp(rel, folder) { var f = new File(root.fsName + "/" + rel); if (!f.exists) { alert("Arquivo nao encontrado: " + rel); return null; }
  var it = app.project.importFile(new ImportOptions(f)); if (folder) it.parentFolder = folder; return it; }
function dims(p) { var t = p.propertyValueType; if (t == PropertyValueType.TwoD_SPATIAL || t == PropertyValueType.ThreeD_SPATIAL || t == PropertyValueType.OneD) return 1; return (t == PropertyValueType.TwoD) ? 2 : 3; }
function easeKeys(p) { for (var k = 1; k <= p.numKeys; k++) { var n = dims(p), e = []; for (var i = 0; i < n; i++) e.push(new KeyframeEase(0, k == 1 ? 10 : 85)); try { p.setTemporalEaseAtIndex(k, e, e); } catch (x) {} } }
function textAnim(L, words, keys, opac, hold) {
  try {
    L.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");
    var an = L.property("ADBE Text Properties").property("ADBE Text Animators").property(1);
    an.name = words ? "Karaoke (palavra por palavra)" : "Revelar (letra por letra)";
    an.property("ADBE Text Animator Properties").addProperty("ADBE Text Opacity");
    an = L.property("ADBE Text Properties").property("ADBE Text Animators").property(1);
    an.property("ADBE Text Animator Properties").property("ADBE Text Opacity").setValue(opac);
    an.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
    an = L.property("ADBE Text Properties").property("ADBE Text Animators").property(1);
    var sel = an.property("ADBE Text Selectors").property(1);
    try { sel.property("ADBE Text Range Advanced").property("ADBE Text Range Type2").setValue(words ? 3 : 1); } catch (e1) {}
    var st = sel.property("ADBE Text Percent Start");
    for (var i = 0; i < keys.length; i++) st.setValueAtTime(keys[i][0], keys[i][1]);
    if (hold) for (var k = 1; k <= st.numKeys; k++) st.setInterpolationTypeAtKey(k, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD);
  } catch (e) {}
}
function animate(L, t) {
  var a = t.anim, tin = t.tin, d = a.d || .3, T = L.transform, O = T.opacity, P = T.position, S = T.scale, p0 = P.value;
  if (a.type == "fade") { O.setValueAtTime(tin, 0); O.setValueAtTime(tin + d, 100); }
  if (a.type == "slide" || a.type == "scale") { O.setValueAtTime(tin, 0); O.setValueAtTime(tin + Math.min(d, .25), 100); }
  if (a.type == "slide" || (a.type == "scale" && a.dy)) { P.setValueAtTime(tin, [p0[0] + (a.dx || 0), p0[1] + (a.dy || 0)]); P.setValueAtTime(tin + d, [p0[0], p0[1]]); easeKeys(P); }
  if (a.type == "scale" || a.type == "stamp") { S.setValueAtTime(tin, [a.from, a.from, 100]); S.setValueAtTime(tin + d, [100, 100, 100]); easeKeys(S); }
  if (a.type == "reveal") textAnim(L, false, [[tin, 0], [tin + d, 100]], 0, false);
  if (a.type == "karaoke") { var keys = [[tin, 0]]; for (var i = 0; i < a.words.length; i++) keys.push([Math.max(tin + .01 * (i + 1), a.words[i]), 100 * (i + 1) / t.nwords]); textAnim(L, true, keys, 18, true); }
}
function mkText(comp, t, label) {
  var L = comp.layers.addText(t.text); L.name = t.name; L.label = label;
  var sp = L.property("ADBE Text Properties").property("ADBE Text Document"), d = sp.value;
  d.text = t.text; try { d.resetCharStyle(); d.resetParagraphStyle(); } catch (e0) {}
  try { d.font = t.font; } catch (e1) {}
  d.fontSize = t.size; d.applyFill = true; d.fillColor = t.color; d.applyStroke = false; d.tracking = t.tracking;
  if (t.text.indexOf("\r") >= 0) { try { d.autoLeading = false; d.leading = t.leading; } catch (e2) {} }
  d.justification = t.just == "center" ? ParagraphJustification.CENTER_JUSTIFY : (t.just == "right" ? ParagraphJustification.RIGHT_JUSTIFY : ParagraphJustification.LEFT_JUSTIFY);
  sp.setValue(d); if (t.expr) sp.expression = t.expr;
  L.transform.anchorPoint.setValue([t.center[0] - t.base[0], t.center[1] - t.base[1]]); L.transform.position.setValue([t.center[0], t.center[1]]);
  if (t.rot) L.transform.rotation.setValue(t.rot);
  L.inPoint = t.tin; L.outPoint = t.tout; animate(L, t); return L;
}

app.beginUndoGroup("Montar " + NAME);
if (!app.project) app.newProject();
var fRoot = app.project.items.addFolder(NAME);
var fMed = app.project.items.addFolder("02 Midia (video base, imagens)"); fMed.parentFolder = fRoot;
var fAud = app.project.items.addFolder("03 Audio"); fAud.parentFolder = fRoot;
var comp = app.project.items.addComp("01 " + NAME, 1920, 1080, 1, DATA.dur, __FPS__); comp.parentFolder = fRoot; comp.bgColor = [0, 0, 0];
var STACK = [], AUD = [], TX = [], IMG = [], DIV = [], OV = [];

for (var s = 0; s < STEMS.length; s++) { var it = imp("audio/" + STEMS[s][0], fAud); if (!it) continue; var al = comp.layers.add(it);
  al.startTime = STEMS[s][1]; al.audioEnabled = false; al.label = 16; al.name = STEMS[s][3]; AUD.push(al); }
var ml = null; if (DATA.hasMix) { var mixIt = imp("audio/MIX_FINAL.wav", fAud); if (mixIt) { ml = comp.layers.add(mixIt); ml.name = DATA.audioGroup.substr(0, 2) + " AUDIO - MIX FINAL (ligado; desligue para editar os separados)"; ml.label = 16; } }
var bl = null; if (DATA.hasBase) { var bIt = imp("video/base_sem_texto.mp4", fMed); if (bIt) { bl = comp.layers.add(bIt); bl.name = "BASE - fundo e graficos renderizados (sem textos, travada)"; bl.audioEnabled = false; bl.label = 0; } }

for (var m1 = 0; m1 < DATA.images.length; m1++) { var im = DATA.images[m1], iIt = imp(im.file, fMed); if (!iIt) continue; var il = comp.layers.add(iIt);
  il.name = im.name + " (Replace Footage para trocar)"; il.label = DATA.groups[im.g].label; il.inPoint = im.tin; il.outPoint = im.tout;
  il.transform.anchorPoint.setValue([iIt.width * im.anchorFrac[0], iIt.height * im.anchorFrac[1]]);
  var IP = il.transform.position, IS = il.transform.scale, IO = il.transform.opacity, r = im.rise;
  if (r) { IP.setValueAtTime(im.tin, [im.center[0], im.center[1] + (r.dy || 0)]); IP.setValueAtTime(im.tin + r.d, [im.center[0], im.center[1]]); easeKeys(IP);
    var f0 = im.scale * (r.from || 100) / 100; IS.setValueAtTime(im.tin, [f0, f0, 100]); IS.setValueAtTime(im.tin + r.d, [im.scale, im.scale, 100]); easeKeys(IS);
    IO.setValueAtTime(im.tin, 0); IO.setValueAtTime(im.tin + .3, 100); }
  else { IP.setValue([im.center[0], im.center[1]]); IS.setValue([im.scale, im.scale, 100]); }
  if (im.bob) IP.expression = "value + [0, Math.sin(time*1.3)*" + im.bob + "]";
  IMG.push([im.g, il]); }

for (var i = 0; i < DATA.texts.length; i++) { var t = DATA.texts[i]; TX.push([t.g, mkText(comp, t, DATA.groups[t.g].label)]); }
for (var g = 0; g < DATA.groups.length; g++) { var G = DATA.groups[g], nl = comp.layers.addNull(DATA.dur); nl.name = G.title; nl.label = G.label; nl.inPoint = G.tin; nl.outPoint = G.tout; DIV.push(nl); }
var ad = null; if (STEMS.length || ml) { ad = comp.layers.addNull(DATA.dur); ad.name = DATA.audioGroup; ad.label = 16; }
for (var o = 0; o < DATA.overlays.length; o++) { var ov = DATA.overlays[o], oIt = imp(ov.file, fMed); if (!oIt) continue; var ol = comp.layers.add(oIt);
  ol.name = "00 " + ov.name; ol.inPoint = ov.tin; ol.outPoint = ov.tout; ol.label = 1; OV.push(ol); }
var adj = null; if (DATA.grain.length) { adj = comp.layers.addSolid([1, 1, 1], "00 FX - Grao (camada de ajuste)", 1920, 1080, 1, DATA.dur); adj.adjustmentLayer = true; adj.label = 0;
  try { var amt = adj.property("ADBE Effect Parade").addProperty("ADBE Noise").property(1);
    for (var q = 0; q < DATA.grain.length; q++) amt.setValueAtTime(DATA.grain[q][0], DATA.grain[q][1]);
    for (var q2 = 1; q2 <= amt.numKeys; q2++) amt.setInterpolationTypeAtKey(q2, KeyframeInterpolationType.HOLD); } catch (e3) {} }

// ordem final (de cima para baixo): FX, cenas em ordem cronologica (divisoria + textos + imagens), base, audio
if (adj) STACK.push(adj); for (var o2 = 0; o2 < OV.length; o2++) STACK.push(OV[o2]);
for (var g2 = 0; g2 < DATA.groups.length; g2++) { STACK.push(DIV[g2]);
  for (var j = 0; j < TX.length; j++) if (TX[j][0] == g2) STACK.push(TX[j][1]);
  for (var j2 = 0; j2 < IMG.length; j2++) if (IMG[j2][0] == g2) STACK.push(IMG[j2][1]); }
if (bl) STACK.push(bl); if (ad) STACK.push(ad); if (ml) STACK.push(ml);
for (var a2 = 0; a2 < AUD.length; a2++) STACK.push(AUD[a2]);
for (var k2 = 0; k2 < STACK.length; k2++) STACK[k2].moveToEnd();
try { if (bl) bl.locked = true; } catch (e5) {}
for (var m = 0; m < DATA.markers.length; m++) comp.markerProperty.setValueAtTime(DATA.markers[m].t, new MarkerValue(DATA.markers[m].name));
app.endUndoGroup();
comp.openInViewer();
var miss = [];
try { if (app.fonts && app.fonts.getFontsByPostScriptName) for (var f = 0; f < FONTS.length; f++) { var rr = app.fonts.getFontsByPostScriptName(FONTS[f]); if (!rr || !rr.length) miss.push(FONTS[f]); } } catch (e4) {}
alert("Projeto montado: " + DATA.texts.length + " textos editaveis, " + DATA.images.length + " imagens, " + STEMS.length + " audios separados." + (miss.length ? "\n\nFontes faltando (instale e rode de novo):\n" + miss.join("\n") : ""));
})();
'''
J = lambda x: json.dumps(x, ensure_ascii=True)
jsx = (JSX.replace('__DATA__', J(data)).replace('__STEMS__', J(stems)).replace('__FONTS__', J(FONTS)).replace('__NAMEJS__', J(a.name))
       .replace('__NAME__', a.name.encode('ascii', 'replace').decode()).replace('__FPS__', str(a.fps)))
fn = 'Montar_Projeto_' + ''.join(c if c.isalnum() else '_' for c in a.name.encode('ascii', 'ignore').decode()) + '.jsx'
open(os.path.join(OUT, fn), 'w', encoding='utf-8').write(jsx)

leia = f"""{a.name} — projeto editável para After Effects
{'=' * 60}
COMO ABRIR
1. Instale as fontes abaixo (Google Fonts, versões "static" de cada peso).
2. After Effects (2022+) > File > Scripts > Run Script File... > {fn}
   (o .jsx precisa ficar nesta pasta, junto de video/, imagens/ e audio/).
3. A comp abre organizada: camadas na ordem do vídeo (de cima para baixo), cada cena com uma divisória
   numerada e cor própria, marcadores por cena. Salve o .aep onde quiser.

FONTES: {', '.join(FONTS)}

EDITÁVEL: {len(data['texts'])} textos nativos (mesma fonte/cor/posição/tempo; animações em keyframes; legendas com
animador palavra por palavra), {len(data['images'])} imagem(ns) nativa(s) (Replace Footage para trocar), FX separados,
áudio: MIX FINAL ligado + {len(stems)} áudios separados desligados (ligue para editar; vêm com folga de volume).
NA BASE (vídeo renderizado sem textos): fundos, gráficos e efeitos gerados por código. Se aumentar muito um texto que
fica dentro de uma tarja/caixa da base, a caixa não acompanha — gere uma base nova.
"""
open(os.path.join(OUT, 'LEIA-ME.txt'), 'w', encoding='utf-8').write(leia)
print('pacote AE ->', OUT, '|', len(data['texts']), 'textos,', len(data['images']), 'imagens,', len(stems), 'áudios,', len(groups), 'cenas')
if a.zip:
    z = shutil.make_archive(OUT.rstrip('/\\'), 'zip', os.path.dirname(OUT.rstrip('/\\')), os.path.basename(OUT.rstrip('/\\'))); print('zip ->', z)
