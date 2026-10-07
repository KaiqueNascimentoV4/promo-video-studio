"""sheet.py SAIDA.jpg COLS LARGURA F0 F1 PASSO [DIR] — folha de contato com o número do quadro.
DIR padrão = ref/half (jpg); para os seus quadros passe out/<G>/x (png).
pares:  sheet.py SAIDA.jpg --pares 10,11,250,251 [DIR_NOSSO]  → linhas REF | NOSSO (costuras entre grupos, 1 q/s)."""
import os, sys
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _proj import ROOT, proj

P = proj(); REF = os.path.join(ROOT, P.get('REF_HALF', 'ref/half'))


def ler(d, f):
    for ext in ('.jpg', '.png'):
        p = os.path.join(d, f'f{f:04d}{ext}')
        if os.path.exists(p): return cv2.imread(p)
    return None


def rot(im, txt):
    cv2.rectangle(im, (0, 0), (12 + 11 * len(txt), 22), (0, 0, 0), -1)
    cv2.putText(im, txt, (3, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA); return im


out = sys.argv[1]
if sys.argv[2] == '--pares':
    fr = [int(x) for x in sys.argv[3].split(',')]; d = sys.argv[4] if len(sys.argv) > 4 else os.path.join(ROOT, 'out', 'full')
    w = 400; h = int(round(w * P['H'] / P['W'])); tiles = []
    for f in fr:
        a, b = ler(REF, f), ler(d, f)
        if a is None or b is None: continue
        tiles.append(np.hstack([rot(cv2.resize(a, (w, h)), f'REF {f}'), rot(cv2.resize(b, (w, h)), f'NOSSO {f}'), np.zeros((h, 6, 3), np.uint8)]))
    while len(tiles) % 3: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]), [cv2.IMWRITE_JPEG_QUALITY, 82])
else:
    cols, w, f0, f1, st = map(int, sys.argv[2:7]); d = sys.argv[7] if len(sys.argv) > 7 else REF
    h = int(round(w * P['H'] / P['W'])); ims = []
    for f in range(f0, f1 + 1, st):
        im = ler(d, f)
        if im is not None: ims.append(rot(cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA), str(f)))
    while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(out, np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
print('→', out)
