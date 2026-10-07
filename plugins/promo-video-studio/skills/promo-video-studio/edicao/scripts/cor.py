"""Cor: HDR→Rec.709, looks da casa, LUT e medição/igualação entre planos.

  python cor.py ENTRADA SAIDA [--look frio|neutro|quente|pb|tecnico] [--lut arq.cube --lut-mix 0.6]
        aplica a conversão (detecta HLG/PQ sozinho) + look num vídeo inteiro
  python cor.py --medir mudo.mp4 --mapa mapa.json [--look frio] [--trim trim.json]
        mede o FUNDO (faixa de cima + laterais, onde a pessoa não está) de cada segmento e grava/atualiza trim.json
        (o cortar.py aplica o trim). Alvos: Y ≈ 106, R−B ≈ −16 (frio) / 0 (neutro). Recusa medir o MESMO arquivo
        duas vezes (isso acumularia a correção em dobro): renderize de novo entre as medições.
  python cor.py --cadeia [--hdr HLG] [--look frio]     só imprime a cadeia de filtros

Funções usadas pelo cortar.py: conversao(hdr), look(nome), lut(arq, mix), trim_filtro(t).
"""
import argparse, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ffbin, run, probe, video_stream, ler_json, gravar_json, esc_filtro

LOOKS = {
    'frio': 'colorbalance=rs=-0.03:bs=0.05:rm=-0.025:bm=0.035:rh=-0.01:bh=0.01,eq=contrast=1.08:saturation=0.95',
    'neutro': 'eq=contrast=1.03',
    'quente': 'colorbalance=rs=-0.02:bs=0.03:rm=0.045:bm=-0.04:rh=0.02:bh=-0.02,eq=contrast=1.06:saturation=1.05',
    'pb': 'hue=s=0,eq=contrast=1.15',
    'tecnico': '',
}
ALVO_RB = {'frio': -16, 'neutro': 0, 'quente': 12}


def conversao(hdr):
    """HLG/PQ → Rec.709 SDR (tonemap hable). Vazio se já é SDR."""
    if not hdr: return ''
    npl = 203 if hdr == 'HLG' else 100
    return (f'zscale=t=linear:npl={npl},format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,'
            'zscale=t=bt709:m=bt709:r=tv,format=gbrp')


def look(nome):
    if nome not in LOOKS: sys.exit(f'look desconhecido: {nome} ({", ".join(LOOKS)})')
    return LOOKS[nome]


def lut(arq, mix=1.0):
    if not arq: return ''
    f = f"lut3d=file='{esc_filtro(arq)}'"
    if mix >= 0.999: return f
    return f'split[a][b];[b]{f}[l];[a][l]blend=all_expr=A*{1 - mix:.3f}+B*{mix:.3f}'


def trim_filtro(t):
    """t = {"brilho": float(-1..1), "temp": float(+ = mais quente)}"""
    if not t: return ''
    out = []
    if abs(t.get('brilho', 0)) > 1e-4: out.append(f"eq=brightness={t['brilho']:.4f}")
    if abs(t.get('temp', 0)) > 1e-4: out.append(f"colorbalance=rm={t['temp']:.4f}:bm={-t['temp']:.4f}")
    return ','.join(out)


def hdr_de(path):
    v = video_stream(probe(path)); trc = (v or {}).get('color_transfer', '')
    return 'HLG' if trc == 'arib-std-b67' else 'PQ' if trc == 'smpte2084' else ''


def cadeia(hdr='', nome='frio', lut_arq=None, mix=1.0):
    return ','.join(x for x in (conversao(hdr), look(nome), lut(lut_arq, mix), 'format=yuv420p') if x)


SAIDA_709 = ['-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv']


def aplicar(ent, sai, nome, lut_arq, mix):
    vf = cadeia(hdr_de(ent), nome, lut_arq, mix) + ',setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv'
    run([ffbin(), '-y', '-v', 'error', '-i', ent, '-vf', vf, '-c:v', 'libx264', '-crf', '16', '-preset', 'medium',
         *SAIDA_709, '-c:a', 'copy', sai])
    print('→', sai)


def frames_em(video, tempos, w=270, h=480):
    out = []
    for t in tempos:
        r = subprocess.run([ffbin(), '-v', 'error', '-ss', f'{t:.3f}', '-i', video, '-frames:v', '1', '-vf', f'scale={w}:{h}',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
        if len(r.stdout) == w * h * 3: out.append(np.frombuffer(r.stdout, np.uint8).reshape(h, w, 3).astype(np.float32))
    return out


def fundo(im):
    """Máscara do fundo provável: faixa de cima (22%) + laterais (14%) da metade de cima."""
    h, w, _ = im.shape
    m = np.zeros((h, w), bool); m[:int(h * .22)] = True
    m[:int(h * .55), :int(w * .14)] = True; m[:int(h * .55), int(w * .86):] = True
    return im[m]


def medir(video, mapa_p, nome, trim_p):
    mapa = ler_json(mapa_p)
    trim = ler_json(trim_p) if os.path.exists(trim_p) else {}
    marca = f'{os.path.abspath(video)}|{os.path.getmtime(video):.0f}'
    if trim.get('_medido') == marca:
        sys.exit('este mudo.mp4 já foi medido — renderize de novo (cortar.py) antes de medir outra vez (senão a correção dobra)')
    alvo_rb = ALVO_RB.get(nome)
    seg_t = {}
    for p in mapa['pecas']:
        seg_t.setdefault(str(p['seg']), []).append((p['t0'], p['t1']))
    print(f'{"seg":>4s} {"Y":>6s} {"p5":>5s} {"R-B":>6s}  ajuste')
    for seg, rs in seg_t.items():
        ts = [a + (b - a) * k for a, b in rs for k in (0.3, 0.7)][:6]
        px = [fundo(im) for im in frames_em(video, ts)]
        if not px: continue
        p = np.concatenate(px)
        Y = float((0.2126 * p[:, 0] + 0.7152 * p[:, 1] + 0.0722 * p[:, 2]).mean())
        p5 = float(np.percentile(0.2126 * p[:, 0] + 0.7152 * p[:, 1] + 0.0722 * p[:, 2], 5))
        rb = float((p[:, 0] - p[:, 2]).mean())
        t = trim.get(seg, {'brilho': 0.0, 'temp': 0.0})
        db = float(np.clip((106 - Y) / 219 * 0.8, -0.12, 0.12))
        dt = 0.0 if alvo_rb is None else float(np.clip((alvo_rb - rb) / 220, -0.06, 0.06))
        t['brilho'] = round(t.get('brilho', 0) + db, 4); t['temp'] = round(t.get('temp', 0) + dt, 4)
        trim[seg] = t
        print(f'{seg:>4s} {Y:6.1f} {p5:5.1f} {rb:6.1f}  brilho {t["brilho"]:+.3f} temp {t["temp"]:+.3f}')
    trim['_medido'] = marca
    gravar_json(trim_p, trim)
    print('→', trim_p, '(rode cortar.py de novo; no máximo 2 passadas)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('entrada', nargs='?'); ap.add_argument('saida', nargs='?')
    ap.add_argument('--look', default='frio'); ap.add_argument('--lut'); ap.add_argument('--lut-mix', type=float, default=1.0)
    ap.add_argument('--medir'); ap.add_argument('--mapa'); ap.add_argument('--trim', default='trim.json')
    ap.add_argument('--cadeia', action='store_true'); ap.add_argument('--hdr', default='')
    a = ap.parse_args()
    if a.cadeia: print(cadeia(a.hdr, a.look, a.lut, a.lut_mix))
    elif a.medir:
        if not a.mapa: sys.exit('--medir precisa de --mapa (o mapa.json que o cortar.py grava)')
        medir(a.medir, a.mapa, a.look, a.trim)
    elif a.entrada and a.saida: aplicar(a.entrada, a.saida, a.look, a.lut, a.lut_mix)
    else: ap.print_help()
