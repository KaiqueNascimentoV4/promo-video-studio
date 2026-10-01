"""Build an editable Premiere Pro package (FCP7 XML + separated layers + audio stems + font).

Usage:
  python premiere_package.py --page projeto.html --dur 45 --mix mix.json --out "C:/Users/<you>/Downloads/Projeto_Premiere" [--name "Projeto"] [--markers markers.json]

The HTML must implement window.__setLayer('base'|'doodle'|'text'), window.__annExport() and window.__scenes()
(assets/template.html does). markers.json (optional): [[seconds, "frase da narração"], ...]
Output layout:
  Video/V1_Cenas_base.mp4 · Video/V2_Setas_desenhos_alpha.mov · Video/V4_Textos_renderizados_alpha.mov
  Audio/01_Narracao.wav · Audio/02_Trilha_com_ducking.wav · Audio/SFX_*.wav
  <name>.xml · Fonte/ · LEIA-ME.txt
"""
import argparse, json, os, shutil, subprocess, sys
from xml.sax.saxutils import escape
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from _tools import run, loudness, duration  # noqa: E402
import mix as MIX  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--page', required=True); ap.add_argument('--dur', type=float, required=True); ap.add_argument('--mix', required=True)
ap.add_argument('--out', required=True); ap.add_argument('--name', default='Promo'); ap.add_argument('--fps', type=int, default=60)
ap.add_argument('--markers'); ap.add_argument('--skip-render', action='store_true')
a = ap.parse_args()
OUT = os.path.abspath(a.out); FPS, W, H, DUR = a.fps, 1920, 1080, a.dur; N = int(round(FPS * DUR))
for d in ['Video', 'Audio', 'Fonte']: os.makedirs(os.path.join(OUT, d), exist_ok=True)
fr = lambda t: int(round(t * FPS))

# ---------- 1. layers ----------
R = os.path.join(HERE, 'render.mjs'); ann_path = os.path.join(OUT, 'ann.json')
def node(*args): subprocess.run(['node', R, '--page', a.page, '--dur', str(DUR), '--fps', str(FPS)] + list(args), check=True)
node('--export-ann', ann_path)
if not a.skip_render:
    node('--layer', 'base', '--out', os.path.join(OUT, 'Video', 'V1_Cenas_base.mp4'))
    node('--layer', 'doodle', '--out', os.path.join(OUT, 'Video', 'V2_Setas_desenhos_alpha.mov'))
    node('--layer', 'text', '--out', os.path.join(OUT, 'Video', 'V4_Textos_renderizados_alpha.mov'))
A = json.load(open(ann_path, encoding='utf-8')); texts, scenes = A['ann'], A['scenes']

# ---------- 2. audio stems (gain matched to the master, capped to avoid clipping) ----------
C = MIX.load(a.mix); AD = os.path.join(OUT, 'Audio'); tmp = os.path.join(AD, '_premix.wav')
inp, fc = MIX.build_audio(C, master=False)
run(['-y', '-loglevel', 'error'] + inp + ['-filter_complex', fc, '-map', '[out]', tmp])
L, PK = loudness(tmp); G = min(C.get('loudness', -14) - L, -1.1 - PK); os.remove(tmp)
g = f'volume={G:.2f}dB'
def stem(parts, name):
    inp, fc = MIX.build_audio(C, master=False, parts=parts)
    run(['-y', '-loglevel', 'error'] + inp + ['-filter_complex', fc + f';[out]{g}[o]', '-map', '[o]', os.path.join(AD, name)])
stem(('vo',), '01_Narracao.wav')
if C.get('music'): stem(('music',), '02_Trilha_com_ducking.wav')
sfx_files, events = {}, []
for e in C.get('events', []):
    key = (e['file'], e.get('vol', .3), bool(e.get('hp')))
    if key not in sfx_files:
        nm = f"SFX_{os.path.splitext(os.path.basename(e['file']))[0]}_{int(key[1]*100):02d}.wav"
        run(['-y', '-loglevel', 'error', '-i', MIX.P(C, e['file']), '-af', ('highpass=f=900,' if key[2] else '') + f'aresample=48000,volume={key[1]},{g}', '-ac', '2', os.path.join(AD, nm)])
        sfx_files[key] = nm
    events.append((sfx_files[key], float(e['t'])))

# ---------- 3. FCP7 XML ----------
rate = f'<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>'
url = lambda rel: 'file://localhost/' + (OUT.replace('\\', '/') + '/' + rel).replace(' ', '%20')
done = set(); cid = [0]
def file_el(fid, rel, frames, kind):
    if fid in done: return f'<file id="{fid}"/>'
    done.add(fid)
    media = (f'<video><samplecharacteristics>{rate}<width>{W}</width><height>{H}</height><anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance></samplecharacteristics></video>'
             if kind != 'audio' else '<audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>')
    return f'<file id="{fid}"><name>{escape(os.path.basename(rel))}</name><pathurl>{url(rel)}</pathurl>{rate}<duration>{frames}</duration><media>{media}</media></file>'
def vclip(name, fid, rel, s, e, alpha=False, enabled=True):
    cid[0] += 1
    return (f'<clipitem id="clipitem-{cid[0]}"><name>{escape(name)}</name><enabled>{"TRUE" if enabled else "FALSE"}</enabled><duration>{N}</duration>{rate}'
            f'<start>{s}</start><end>{e}</end><in>{s}</in><out>{e}</out><alphatype>{"straight" if alpha else "none"}</alphatype>{file_el(fid, rel, N, "video")}</clipitem>')
def aclip(name, rel, start, ch):
    cid[0] += 1; ln = fr(duration(os.path.join(OUT, rel)))
    return (f'<clipitem id="clipitem-{cid[0]}"><name>{escape(name)}</name><enabled>TRUE</enabled><duration>{ln}</duration>{rate}<start>{start}</start><end>{start + ln}</end>'
            f'<in>0</in><out>{ln}</out>{file_el("f-" + rel, rel, ln, "audio")}<sourcetrack><mediatype>audio</mediatype><trackindex>{ch}</trackindex></sourcetrack></clipitem>')
def tgen(t):
    cid[0] += 1; s, e = fr(t['start']), fr(t['end'])
    col = {'ink': (23, 19, 14), 'dark': (23, 19, 14), 'white': (255, 255, 255)}.get(t.get('cls', ''), (79, 70, 229) if t.get('cls') == '' else (255, 255, 255))
    cx, cy = (t['cx'] - W / 2) / W, (t['cy'] - H / 2) / H; txt = escape(t['text']).replace('\n', '\r')
    return (f'<generatoritem id="clipitem-{cid[0]}"><name>{escape(t["text"].replace(chr(10), " "))}</name><enabled>TRUE</enabled><duration>{N}</duration>{rate}'
            f'<start>{s}</start><end>{e}</end><in>0</in><out>{e - s}</out><anamorphic>FALSE</anamorphic><alphatype>black</alphatype>'
            f'<effect><name>Text</name><effectid>Text</effectid><effectcategory>Text</effectcategory><effecttype>generator</effecttype><mediatype>video</mediatype>'
            f'<parameter><parameterid>str</parameterid><name>Text</name><value>{txt}</value></parameter>'
            f'<parameter><parameterid>fontname</parameterid><name>Font</name><value>Gochi Hand</value></parameter>'
            f'<parameter><parameterid>fontsize</parameterid><name>Size</name><valuemin>0</valuemin><valuemax>1000</valuemax><value>{round(t["size"])}</value></parameter>'
            f'<parameter><parameterid>fontalign</parameterid><name>Alignment</name><valuemin>1</valuemin><valuemax>3</valuemax><value>2</value></parameter>'
            f'<parameter><parameterid>fontcolor</parameterid><name>Font Color</name><value><alpha>255</alpha><red>{col[0]}</red><green>{col[1]}</green><blue>{col[2]}</blue></value></parameter>'
            f'</effect><sourcetrack><mediatype>video</mediatype></sourcetrack>'
            f'<filter><effect><name>Basic Motion</name><effectid>basic</effectid><effectcategory>motion</effectcategory><effecttype>motion</effecttype><mediatype>video</mediatype>'
            f'<parameter><parameterid>rotation</parameterid><name>Rotation</name><valuemin>-8640</valuemin><valuemax>8640</valuemax><value>{t.get("rot", 0)}</value></parameter>'
            f'<parameter><parameterid>center</parameterid><name>Center</name><value><horiz>{cx:.5f}</horiz><vert>{cy:.5f}</vert></value></parameter>'
            f'</effect></filter></generatoritem>')
def lanes(items, span):
    out = []
    for it in sorted(items, key=lambda x: span(x)[0]):
        s, e = span(it)
        for ln in out:
            if span(ln[-1])[1] <= s: ln.append(it); break
        else: out.append([it])
    return out
track = lambda items, extra='': f'<track>{"".join(items)}<enabled>TRUE</enabled><locked>FALSE</locked>{extra}</track>'
v1 = [vclip(s['id'], 'base', 'Video/V1_Cenas_base.mp4', fr(s['a']), fr(min(s['b'], DUR))) for s in scenes]
v2 = [vclip('desenhos · ' + s['id'], 'doodle', 'Video/V2_Setas_desenhos_alpha.mov', fr(s['a']), fr(min(s['b'], DUR)), True) for s in scenes]
tl = lanes(texts, lambda t: (fr(t['start']), fr(t['end'])))
vt = [track([tgen(t) for t in ln]) for ln in tl]
vr = [track([vclip('texto renderizado · ' + t['text'].replace('\n', ' '), 'textr', 'Video/V4_Textos_renderizados_alpha.mov', fr(t['start']), fr(t['end']), True, False) for t in ln]) for ln in tl]
at = [track([aclip('Narração', 'Audio/01_Narracao.wav', 0, 1)], '<outputchannelindex>1</outputchannelindex>'),
      track([aclip('Narração', 'Audio/01_Narracao.wav', 0, 2)], '<outputchannelindex>2</outputchannelindex>')]
if C.get('music'):
    at += [track([aclip('Trilha', 'Audio/02_Trilha_com_ducking.wav', 0, 1)], '<outputchannelindex>1</outputchannelindex>'),
           track([aclip('Trilha', 'Audio/02_Trilha_com_ducking.wav', 0, 2)], '<outputchannelindex>2</outputchannelindex>')]
for ln in lanes(events, lambda ev: (fr(ev[1]), fr(ev[1]) + fr(duration(os.path.join(AD, ev[0]))))):
    at.append(track([aclip(n.replace('.wav', ''), 'Audio/' + n, fr(t), 1) for n, t in ln], '<outputchannelindex>1</outputchannelindex>'))
markers = ''
if a.markers:
    markers = ''.join(f'<marker><comment>{escape(x)}</comment><name>{escape(x[:40])}</name><in>{fr(t)}</in><out>-1</out></marker>' for t, x in json.load(open(a.markers, encoding='utf-8')))
xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="5"><sequence id="sequence-1">'
       f'<name>{escape(a.name)}</name><duration>{N}</duration>{rate}'
       f'<timecode>{rate}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>{markers}'
       f'<media><video><format><samplecharacteristics>{rate}<width>{W}</width><height>{H}</height><anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance></samplecharacteristics></format>'
       f'{track(v1)}{track(v2)}{"".join(vt)}{"".join(vr)}</video>'
       '<audio><numOutputChannels>2</numOutputChannels><format><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics></format>'
       '<outputs><group><index>1</index><numchannels>1</numchannels><downmix>0</downmix><channel><index>1</index></channel></group>'
       '<group><index>2</index><numchannels>1</numchannels><downmix>0</downmix><channel><index>2</index></channel></group></outputs>'
       f'{"".join(at)}</audio></media></sequence></xmeml>\n')
open(os.path.join(OUT, f'{a.name}.xml'), 'w', encoding='utf-8').write(xml)

# ---------- 4. font + readme ----------
fdir = os.path.join(os.path.dirname(HERE), 'assets', 'fonts')
for f in os.listdir(fdir): shutil.copy(os.path.join(fdir, f), os.path.join(OUT, 'Fonte', f))
n_text = len(tl)
open(os.path.join(OUT, 'LEIA-ME.txt'), 'w', encoding='utf-8').write(f"""PACOTE EDITÁVEL — {a.name}
1. Instale a fonte em Fonte/ com o Premiere FECHADO.
2. Premiere → Arquivo → Importar → {a.name}.xml  (se mover a pasta, aponte um arquivo e ele acha o resto).
TRILHAS: V1 cenas · V2 setas/desenhos (alpha) · V3–V{2 + n_text} textos EDITÁVEIS (Gochi Hand) ·
V{3 + n_text}–V{2 + 2 * n_text} textos renderizados com animação (DESLIGADOS, referência/backup).
Áudio: narração (L/R), trilha com ducking (L/R), cada efeito como clipe.
Volume: stems {G:+.1f} dB vs. mix cru; o vídeo final foi masterizado em -14 LUFS — ative
"Normalização de volume" no export (ITU BS.1770, -14 LUFS, pico -1 dB) para igualar.
Textos importados de XML podem vir levemente deslocados: use a trilha de textos renderizados como guia.
A animação de "escrita" e a sombra não vão no texto editável (Recortar/Crop com keyframe imita a escrita).
""")
os.remove(ann_path)
print('pacote:', OUT)
