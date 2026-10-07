"""Paleta dominante de um logo, print ou peça da marca → tokens hex (para quando não há MIV).

  python paleta.py IMAGEM [--n 5] [--json marca_cores.json]

Ignora transparente, quase-branco e quase-preto (fundos), agrupa por k-means em Lab e sugere papéis:
primária = cor com mais área entre as saturadas; acento = a mais distante da primária; claro/escuro = primária L±15.
CONFIRME com o usuário: a peça oficial (site/Instagram) manda no vídeo.
"""
import argparse, json, os, sys
import numpy as np
import cv2


def hexc(rgb): return '#%02X%02X%02X' % tuple(int(round(v)) for v in rgb)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('imagem'); ap.add_argument('--n', type=int, default=5); ap.add_argument('--json')
    a = ap.parse_args()
    im = cv2.imread(a.imagem, cv2.IMREAD_UNCHANGED)
    if im is None: sys.exit('não abri a imagem (SVG? exporte um PNG antes)')
    if im.ndim == 2: im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGRA)
    if im.shape[2] == 3: im = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)
    s = 400 / max(im.shape[:2]); im = cv2.resize(im, None, fx=min(1, s), fy=min(1, s), interpolation=cv2.INTER_AREA)
    px = im.reshape(-1, 4); px = px[px[:, 3] > 200][:, :3]
    lum = px.mean(1); px = px[(lum > 18) & (lum < 240)]
    if len(px) < 50: sys.exit('quase nada além de branco/preto/transparente — a marca é monocromática?')
    lab = cv2.cvtColor(px.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    k = min(a.n, len(np.unique(px, axis=0)))
    _, lb, cen = cv2.kmeans(lab, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5), 5, cv2.KMEANS_PP_CENTERS)
    cont = np.bincount(lb.ravel(), minlength=k) / len(lb)
    rgb = cv2.cvtColor(cen.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(-1, 3)[:, ::-1]
    hsv = cv2.cvtColor(rgb[:, ::-1].reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2HSV).reshape(-1, 3)
    cores = sorted([dict(hex=hexc(rgb[i]), area=round(float(cont[i]) * 100, 1), sat=int(hsv[i, 1])) for i in range(k)], key=lambda c: -c['area'])
    sat = [c for c in cores if c['sat'] > 60] or cores
    prim = sat[0]
    pi = [c['hex'] for c in cores].index(prim['hex'])
    dist = [float(np.linalg.norm(cen[i] - cen[pi])) for i in range(k)]
    acento = cores[[c['hex'] for c in cores].index(hexc(rgb[int(np.argmax(dist))]))]
    l = cv2.cvtColor(np.array([[[int(prim['hex'][5:7], 16), int(prim['hex'][3:5], 16), int(prim['hex'][1:3], 16)]]], np.uint8), cv2.COLOR_BGR2LAB)[0, 0].astype(int)
    def var(dl):
        x = l.copy(); x[0] = np.clip(x[0] + dl * 2.55, 0, 255)
        return hexc(cv2.cvtColor(np.array([[x]], np.uint8), cv2.COLOR_LAB2BGR)[0, 0][::-1])
    papeis = dict(primaria=prim['hex'], acento=acento['hex'], primaria_clara=var(15), primaria_escura=var(-15))
    for c in cores: print(f"  {c['hex']}  {c['area']:5.1f}%  sat {c['sat']}")
    print('sugestão:', json.dumps(papeis))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f: json.dump(dict(cores=cores, papeis=papeis, fonte=os.path.basename(a.imagem)), f, indent=1)
        print('→', a.json)


if __name__ == '__main__':
    main()
