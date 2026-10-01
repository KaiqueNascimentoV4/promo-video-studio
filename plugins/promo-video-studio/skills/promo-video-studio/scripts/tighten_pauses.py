"""Encurta pausas internas das falas: silêncios internos > --min viram --keep s (início/fim intactos).
Uso: python tighten_pauses.py audio/*.mp3 [--min 0.38 --keep 0.28 --noise -38]
Originais ficam em <pasta>/orig/. Apaga o .words.json de cada arquivo alterado (regenere as âncoras).
"""
import argparse, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tools import ffmpeg, duration  # noqa: E402
ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='+'); ap.add_argument('--min', type=float, default=.38)
ap.add_argument('--keep', type=float, default=.28); ap.add_argument('--noise', type=float, default=-38); a = ap.parse_args()
for f in a.files:
    od = os.path.join(os.path.dirname(f) or '.', 'orig'); os.makedirs(od, exist_ok=True); o = os.path.join(od, os.path.basename(f))
    if not os.path.exists(o): shutil.copy(f, o)
    d = duration(o)
    r = subprocess.run([ffmpeg(), '-hide_banner', '-i', o, '-af', f'silencedetect=noise={a.noise}dB:d={a.min}', '-f', 'null', '-'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
    ss = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r)]; ee = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]
    cuts = [(s, e) for s, e in zip(ss, ee) if s > .15 and e < d - .15]
    if not cuts: shutil.copy(o, f); print(f'{f}: sem pausas longas'); continue
    keep, pos = [], 0.0
    for s, e in cuts: mid = (s + e) / 2; keep.append((pos, mid - a.keep / 2)); pos = mid + a.keep / 2
    keep.append((pos, d))
    fc = ''.join(f'[0:a]atrim={x:.3f}:{y:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(0, y - x - .01):.3f}:d=0.01[s{i}];' for i, (x, y) in enumerate(keep))
    fc += ''.join(f'[s{i}]' for i in range(len(keep))) + f'concat=n={len(keep)}:v=0:a=1[o]'
    subprocess.run([ffmpeg(), '-y', '-loglevel', 'error', '-i', o, '-filter_complex', fc, '-map', '[o]', '-b:a', '192k', f], check=True)
    wj = os.path.splitext(f)[0] + '.words.json'
    if os.path.exists(wj): os.remove(wj)
    print(f'{f}: {d:.2f}s -> {duration(f):.2f}s ({len(cuts)} pausas)')
