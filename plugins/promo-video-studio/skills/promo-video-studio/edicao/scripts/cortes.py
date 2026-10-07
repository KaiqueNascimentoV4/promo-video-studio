"""Detecta cortes, flashes e quadros pretos num vídeo (análise de referência / conferência de montagem).

  python cortes.py VIDEO [--out VIDEO.cortes.json] [--k 4.0] [--min 12] [--folha]

Método: luma de cada quadro a 96×54 → diferença média absoluta entre quadros consecutivos (MAD).
Corte = MAD > max(--min, --k × mediana local de 31 quadros) e pico local. Flash = quadro com luma média > 235 isolado;
preto = luma média < 8. Quadros 0-based. CONFIRME visualmente (--folha monta antes|depois de cada corte).
Saída: {fps, quadros, mad[], cortes:[{quadro, t, mad}], flashes[], pretos[], planos:[{id, f0, f1}]}
"""
import argparse, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ffbin, probe, video_stream, fps_de, gravar_json


def lumas(video, w=96, h=54):
    p = subprocess.Popen([ffbin(), '-v', 'error', '-i', video, '-vf', f'scale={w}:{h}:flags=area', '-f', 'rawvideo',
                          '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
    data = p.stdout.read(); p.wait()
    return np.frombuffer(data, np.uint8).reshape(-1, h, w).astype(np.float32)


def detectar(L, k=4.0, mn=12.0):
    mad = np.concatenate([[0], np.abs(np.diff(L, axis=0)).mean((1, 2))])
    med = np.array([np.median(mad[max(0, i - 15):i + 16]) for i in range(len(mad))])
    lim = np.maximum(mn, k * med)
    cortes = [i for i in range(1, len(mad)) if mad[i] > lim[i] and mad[i] >= mad[max(0, i - 1)] and mad[i] >= mad[min(len(mad) - 1, i + 1)]]
    media = L.mean((1, 2))
    flashes = [i for i in range(len(media)) if media[i] > 235 and (i == 0 or media[i - 1] < 200)]
    pretos = [i for i in range(len(media)) if media[i] < 8]
    return mad, cortes, flashes, pretos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video'); ap.add_argument('--out'); ap.add_argument('--k', type=float, default=4.0)
    ap.add_argument('--min', type=float, default=12.0); ap.add_argument('--folha', action='store_true')
    a = ap.parse_args()
    fr = fps_de(video_stream(probe(a.video)))
    L = lumas(a.video)
    mad, cortes, flashes, pretos = detectar(L, a.k, a.min)
    ini = [0] + cortes; fim = [c - 1 for c in cortes] + [len(L) - 1]
    planos = [dict(id=f'S{i + 1:02d}', f0=s, f1=e) for i, (s, e) in enumerate(zip(ini, fim))]
    out = a.out or os.path.splitext(a.video)[0] + '.cortes.json'
    gravar_json(out, dict(fps=fr, quadros=len(L), mad=mad.round(2).tolist(),
                          cortes=[dict(quadro=c, t=round(c / fr, 4), mad=round(float(mad[c]), 1)) for c in cortes],
                          flashes=flashes, pretos=pretos, planos=planos))
    print(f'{len(L)} quadros @ {fr:.3f} fps · {len(cortes)} cortes · {len(flashes)} flashes · {len(pretos)} quadros pretos → {out}')
    for p in planos: print(f'  {p["id"]}  f{p["f0"]:5d}–f{p["f1"]:5d}  ({(p["f1"] - p["f0"] + 1) / fr:5.2f} s)')
    if a.folha and cortes:
        from folha import quadro, montar
        ts, rot = [], []
        for c in cortes[:60]:
            for f in (c - 1, c): ts.append((f + 0.5) / fr); rot.append(f'f{f}')
        montar([quadro(a.video, t, 240) for t in ts], rot, 8, os.path.splitext(out)[0] + '.jpg')


if __name__ == '__main__':
    main()
