"""medir.py — MEDIR na ref com numpy (nunca no olho). Coordenadas nativas (ref/full), quadros 0-based.

  python tools/medir.py tinta   F x0 y0 x1 y1 [--claro|--escuro] [--lim 40]   caixa da tinta (texto/logo) na região
  python tools/medir.py caixa-alta F x0 y0 x1 y1 [--claro|--escuro]           altura de caixa-alta (topo→base de 'H' etc.)
  python tools/medir.py cor     F x y [--r 3]                                   cor média (hex) num ponto ± r
  python tools/medir.py trilha  F0 F1 --modelo F x0 y0 x1 y1 [--busca 200] [--out tracks/G1_x.json]
        rastreia um recorte (template match) quadro a quadro → [[x, y, score], ...] (canto sup. esq.), por quadro
  python tools/medir.py tinta-trilha F0 F1 x0 y0 x1 y1 [--claro|--escuro] [--out ...]
        caixa da tinta por quadro → [[x0, y0, x1, y1] | null, ...]  (entradas, zooms, digitação: largura por quadro)
Fundo claro/escuro: --claro = tinta escura sobre fundo claro; --escuro = tinta clara sobre fundo escuro (padrão: auto).
"""
import argparse, json, os, sys
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _proj import ROOT, proj

P = proj(); FULL = os.path.join(ROOT, P.get('REF_FULL', 'ref/full'))


def q(F):
    im = cv2.imread(os.path.join(FULL, f'f{F:04d}.jpg'))
    if im is None: sys.exit(f'quadro {F} não existe em {FULL}')
    return im


def mascara_tinta(reg, modo, lim):
    g = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY).astype(np.float32)
    fundo = np.median(np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]]))
    if modo == 'auto': modo = 'claro' if fundo > 127 else 'escuro'
    return (g < fundo - lim) if modo == 'claro' else (g > fundo + lim)


def caixa(m):
    ys, xs = np.nonzero(m)
    return None if not len(xs) else [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd'); ap.add_argument('nums', nargs='*', type=int)
    ap.add_argument('--claro', action='store_true'); ap.add_argument('--escuro', action='store_true'); ap.add_argument('--lim', type=float, default=40)
    ap.add_argument('--r', type=int, default=3); ap.add_argument('--modelo', nargs=5, type=int); ap.add_argument('--busca', type=int, default=200)
    ap.add_argument('--out')
    a = ap.parse_args(); modo = 'claro' if a.claro else 'escuro' if a.escuro else 'auto'
    if a.cmd in ('tinta', 'caixa-alta'):
        F, x0, y0, x1, y1 = a.nums; m = mascara_tinta(q(F)[y0:y1, x0:x1], modo, a.lim); b = caixa(m)
        if not b: sys.exit('nenhuma tinta na região (ajuste --lim ou --claro/--escuro)')
        b = [b[0] + x0, b[1] + y0, b[2] + x0, b[3] + y0]
        if a.cmd == 'tinta': print(json.dumps(dict(caixa=b, largura=b[2] - b[0], altura=b[3] - b[1], centro=[(b[0] + b[2]) / 2, (b[1] + b[3]) / 2])))
        else:
            # caixa-alta: a linha de base = linha com mais tinta na metade de baixo; topo = moda dos topos das colunas
            rows = m.sum(1); base = int(np.argmax(rows[len(rows) // 2:]) + len(rows) // 2) if rows.any() else None
            tops = [int(np.argmax(c)) for c in m.T if c.any()]
            topo = int(np.median(tops)) if tops else None
            print(json.dumps(dict(caixa=b, caixa_alta=(base - topo) if base is not None and topo is not None else None, base_y=base + y0 if base else None)))
    elif a.cmd == 'cor':
        F, x, y = a.nums; reg = q(F)[y - a.r:y + a.r + 1, x - a.r:x + a.r + 1].reshape(-1, 3).mean(0)
        print('#%02X%02X%02X' % (int(reg[2]), int(reg[1]), int(reg[0])))
    elif a.cmd == 'trilha':
        F0, F1 = a.nums; mf, x0, y0, x1, y1 = a.modelo; tpl = cv2.cvtColor(q(mf)[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        res, px, py = [], x0, y0
        for F in range(F0, F1 + 1):
            g = cv2.cvtColor(q(F), cv2.COLOR_BGR2GRAY)
            sx0, sy0 = max(0, px - a.busca), max(0, py - a.busca)
            sx1, sy1 = min(g.shape[1], px + (x1 - x0) + a.busca), min(g.shape[0], py + (y1 - y0) + a.busca)
            r = cv2.matchTemplate(g[sy0:sy1, sx0:sx1], tpl, cv2.TM_CCOEFF_NORMED); _, sc, _, loc = cv2.minMaxLoc(r)
            px, py = sx0 + loc[0], sy0 + loc[1]; res.append([px, py, round(float(sc), 3)])
        js = json.dumps(res); print(js if not a.out else f'{len(res)} quadros → {a.out}')
        if a.out: open(a.out if os.path.isabs(a.out) else os.path.join(ROOT, 'analysis', a.out), 'w').write(js)
    elif a.cmd == 'tinta-trilha':
        F0, F1, x0, y0, x1, y1 = a.nums; res = []
        for F in range(F0, F1 + 1):
            b = caixa(mascara_tinta(q(F)[y0:y1, x0:x1], modo, a.lim))
            res.append(None if not b else [b[0] + x0, b[1] + y0, b[2] + x0, b[3] + y0])
        js = json.dumps(res); print(js if not a.out else f'{len(res)} quadros → {a.out}')
        if a.out: open(a.out if os.path.isabs(a.out) else os.path.join(ROOT, 'analysis', a.out), 'w').write(js)
    else: ap.print_help()


if __name__ == '__main__':
    main()
