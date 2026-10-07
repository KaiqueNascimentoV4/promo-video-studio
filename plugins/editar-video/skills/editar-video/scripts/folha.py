"""Folha de contato de um vídeo, com o tempo (e o quadro) em cada miniatura. Para revisar de verdade.

  python folha.py VIDEO [--fps 1] [--tempos 1.2,3.4,8] [--cortes cortes.json] [--quadros 0,12,30]
                  [--cols 6] [--largura 216] [--out folha.jpg]

--cortes: para cada corte, o quadro anterior e o seguinte (confere cortes e transições).
"""
import argparse, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ffbin, probe, video_stream, fps_de, ler_json


def quadro(video, t, w):
    r = subprocess.run([ffbin(), '-v', 'error', '-ss', f'{max(0, t):.3f}', '-i', video, '-frames:v', '1', '-vf', f'scale={w}:-2',
                        '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True)
    if not r.stdout: return None
    import io
    return Image.open(io.BytesIO(r.stdout)).convert('RGB')


def montar(imgs, rotulos, cols, out):
    imgs = [(i, r) for i, r in zip(imgs, rotulos) if i is not None]
    if not imgs: sys.exit('nenhum quadro extraído')
    w, h = imgs[0][0].size; rows = (len(imgs) + cols - 1) // cols
    folha = Image.new('RGB', (cols * w, rows * h), (20, 20, 20)); d = ImageDraw.Draw(folha)
    try: fnt = ImageFont.truetype('arial.ttf', max(11, w // 14))
    except OSError: fnt = ImageFont.load_default()
    for n, (im, rot) in enumerate(imgs):
        x, y = (n % cols) * w, (n // cols) * h
        folha.paste(im, (x, y)); tw = d.textlength(rot, font=fnt)
        d.rectangle([x, y, x + tw + 8, y + fnt.size + 6], fill=(0, 0, 0)); d.text((x + 4, y + 2), rot, fill=(255, 220, 0), font=fnt)
    folha.save(out, quality=88); print(f'{len(imgs)} quadros → {out}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video'); ap.add_argument('--fps', type=float, default=1); ap.add_argument('--tempos')
    ap.add_argument('--cortes'); ap.add_argument('--quadros'); ap.add_argument('--cols', type=int, default=6)
    ap.add_argument('--largura', type=int, default=216); ap.add_argument('--out', default='folha.jpg')
    a = ap.parse_args()
    info = probe(a.video); fr = fps_de(video_stream(info)); dur = float(info['format']['duration'])
    if a.tempos: ts = [float(x) for x in a.tempos.split(',')]
    elif a.quadros: ts = [int(x) / fr for x in a.quadros.split(',')]
    elif a.cortes:
        ts = []
        for c in ler_json(a.cortes)['cortes']: ts += [c['t'] - 1.5 / fr, c['t'] + 0.5 / fr]
    else: ts = list(np.arange(0.0, dur, 1 / a.fps))
    rot = [f'{t:.2f}s f{int(round(t * fr))}' for t in ts]
    montar([quadro(a.video, t, a.largura) for t in ts], rot, a.cols, a.out)


if __name__ == '__main__':
    main()
