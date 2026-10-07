"""compare.py OUTDIR quadros — folha OUTDIR/compare.jpg com linhas [REF | NOSSO | |diferença|] e métricas por quadro:
  mad  = diferença média absoluta de luma a 480 px de largura (0–255)
  edge = diferença média dos mapas de borda Sobel (indicador de DESALINHAMENTO de layout; a troca de cor quase não mexe nele)
Grade de 10% em cada painel para julgar o erro de posição (aceite: ≤ 1% do quadro).
Footage diferente por design (material do cliente): julgue pose, posição, tamanho, tempo, brilho e grade."""
import os, sys
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _proj import ROOT, proj

out, frames = sys.argv[1], [int(x) for x in sys.argv[2].split(',') if x]
P = proj()
REFDIR = os.environ.get('REFDIR', os.path.join(ROOT, P.get('REF_HALF', 'ref/half')))
W = 640; H = int(round(W * P['H'] / P['W']))
lw = 480; lh = int(round(lw * P['H'] / P['W']))


def lum(im): return cv2.cvtColor(cv2.resize(im, (lw, lh), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)


def edges(g):
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1); return np.sqrt(gx * gx + gy * gy)


rows = []
for F in frames:
    ref = cv2.imread(os.path.join(REFDIR, f'f{F:04d}.jpg')); ours = cv2.imread(os.path.join(out, f'f{F:04d}.png'))
    if ref is None or ours is None: print(F, 'faltando (ref ou nosso)'); continue
    a, b = lum(ref), lum(ours)
    mad = float(np.abs(a - b).mean()); edge = float(np.abs(edges(a) - edges(b)).mean())
    print(f'quadro {F:5d}  mad {mad:6.1f}  edge {edge:6.1f}')
    d = cv2.applyColorMap(np.clip(np.abs(a - b) * 2, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    tiles = [cv2.resize(ref, (W, H), interpolation=cv2.INTER_AREA), cv2.resize(ours, (W, H), interpolation=cv2.INTER_AREA), cv2.resize(d, (W, H))]
    for t, lab in zip(tiles, ['REF', 'NOSSO', 'DIF']):
        cv2.rectangle(t, (0, 0), (170, 26), (0, 0, 0), -1)
        cv2.putText(t, f'{lab} {F}', (5, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)
        for k in range(1, 10):
            cv2.line(t, (k * W // 10, 0), (k * W // 10, H), (60, 60, 60), 1); cv2.line(t, (0, k * H // 10), (W, k * H // 10), (60, 60, 60), 1)
    rows.append(np.hstack(tiles))
if rows:
    cv2.imwrite(os.path.join(out, 'compare.jpg'), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print('folha →', os.path.join(out, 'compare.jpg'))
