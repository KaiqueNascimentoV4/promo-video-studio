"""footage.py NOME T0 T1 --src VIDEO_DO_CLIENTE [--speed S] [--crop w:h:x:y] [--vf extra] [--escala 1]
Extrai os segundos T0..T1 do vídeo do cliente como sequência JPG no fps EXATO da ref, na resolução da ref × --escala
(lanczos + unsharp leve), em assets/footage/NOME/f0001.jpg…, e reconstrói assets/footage/index.js (C.clipInfo).
--speed 3 = timelapse (3 s da fonte por 1 s de saída). Prefixe o NOME com o seu grupo (g2_esteira).
  footage.py --indice            só reconstrói o index.js
  footage.py --catalogo SAIDA.jpg   folha com 1.º/meio/último quadro de cada clipe"""
import argparse, glob, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _proj import ROOT, proj, fps_str, ff

D = os.path.join(ROOT, 'assets', 'footage')


def rebuild_index():
    os.makedirs(D, exist_ok=True); info = {}
    for n in sorted(os.listdir(D)):
        p = os.path.join(D, n)
        if os.path.isdir(p): info[n] = {'n': len(glob.glob(os.path.join(p, 'f*.jpg')))}
    with open(os.path.join(D, 'index.js'), 'w', encoding='utf-8') as f: f.write('Object.assign(C.clipInfo,' + json.dumps(info) + ');\n')
    return info


def catalogo(out):
    import cv2, numpy as np
    tiles = []
    for n, i in rebuild_index().items():
        for k in (1, max(1, i['n'] // 2), i['n']):
            im = cv2.imread(os.path.join(D, n, f'f{k:04d}.jpg'))
            if im is None: continue
            im = cv2.resize(im, (320, int(320 * im.shape[0] / im.shape[1])))
            cv2.rectangle(im, (0, 0), (320, 20), (0, 0, 0), -1); cv2.putText(im, f'{n} {k}/{i["n"]}', (3, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
            tiles.append(im)
    if not tiles: sys.exit('nenhum clipe')
    h = max(t.shape[0] for t in tiles); tiles = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 0, cv2.BORDER_CONSTANT) for t in tiles]
    while len(tiles) % 6: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]), [cv2.IMWRITE_JPEG_QUALITY, 82]); print('→', out)


if __name__ == '__main__':
    if '--indice' in sys.argv: print(len(rebuild_index()), 'clipes'); sys.exit()
    if '--catalogo' in sys.argv: catalogo(sys.argv[sys.argv.index('--catalogo') + 1]); sys.exit()
    a = argparse.ArgumentParser(); a.add_argument('nome'); a.add_argument('t0', type=float); a.add_argument('t1', type=float)
    a.add_argument('--src', required=True); a.add_argument('--speed', type=float, default=1.0); a.add_argument('--crop')
    a.add_argument('--vf'); a.add_argument('--escala', type=float, default=1.0)
    o = a.parse_args(); P = proj()
    out = os.path.join(D, o.nome); os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, '*.jpg')): os.remove(f)
    W, H = int(P['W'] * o.escala) // 2 * 2, int(P['H'] * o.escala) // 2 * 2
    vf = ([f'crop={o.crop}'] if o.crop else []) + [f'setpts=(PTS-STARTPTS)/{o.speed}', f'fps={fps_str(P)}',
          f'scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},unsharp=5:5:0.6:5:5:0.0'] + ([o.vf] if o.vf else [])
    subprocess.run([ff(), '-v', 'error', '-y', '-ss', str(o.t0), '-to', str(o.t1), '-i', o.src, '-vf', ','.join(vf), '-q:v', '3',
                    '-start_number', '1', os.path.join(out, 'f%04d.jpg')], check=True)
    print(o.nome, rebuild_index()[o.nome]['n'], 'quadros')
