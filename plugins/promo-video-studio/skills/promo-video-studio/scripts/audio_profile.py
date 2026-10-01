"""Profile a music track (energy over time, BPM, beat phase, waveform image) or SFX files (length, peak time).

Usage:
  python audio_profile.py trilha.mp3                 # energy every 0.5 s, BPM, beat phase, writes trilha_wave.png
  python audio_profile.py --sfx whoosh.mp3 pop.mp3   # length / onset / peak of each SFX (fire at t_event - peak)
"""
import argparse, os, sys, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tools import run, to_wav  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('files', nargs='+'); ap.add_argument('--sfx', action='store_true'); a = ap.parse_args()

def load(path, sr=22050):
    w = to_wav(path, os.path.join(tempfile.gettempdir(), 'pvs_prof.wav'), sr=sr)
    f = wave.open(w); x = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(float) / 32768
    return x, f.getframerate()

def env(x, sr, hop_s):
    hop = int(sr * hop_s); return np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) for i in range(len(x) // hop)])

if a.sfx:
    for p in a.files:
        x, sr = load(p); e = env(x, sr, .01)
        print(f'{os.path.basename(p):30s} dur {len(x)/sr:5.2f}s  onset {np.argmax(e > .2 * e.max()) * .01:.2f}s  peak {np.argmax(e) * .01:.2f}s  rms {e.max():.3f}')
    sys.exit(0)

for p in a.files:
    x, sr = load(p); dur = len(x) / sr
    e5 = env(x, sr, .5)
    print(f'== {p}  ({dur:.1f}s)\nenergia (RMS) a cada 0,5 s:')
    print(' '.join(f'{i*.5:.1f}:{v:.3f}' for i, v in enumerate(e5)))
    e = env(x, sr, .01); on = np.maximum(0, np.diff(e, prepend=0))
    seg = on[200:min(len(on), 4000)]; seg = seg - seg.mean(); ac = np.correlate(seg, seg, 'full')[len(seg) - 1:]
    lag = int(np.argmax(ac[33:90]) + 33); beat = lag * .01   # 67–180 BPM (faixa comercial)
    per = lag; fold = np.zeros(per)
    for i in range(len(on)): fold[i % per] += on[i]
    print(f'BPM ≈ {60 / beat:.1f} (beat {beat:.2f}s; se parecer metade/dobro, ajuste)  · fase do beat ≈ {np.argmax(fold) * .01:.2f}s')
    try:
        from PIL import Image, ImageDraw
        png = os.path.splitext(p)[0] + '_wave.png'; W = int(max(1200, dur * 80))
        run(['-y', '-loglevel', 'error', '-i', p, '-filter_complex', f'showwavespic=s={W}x220:colors=white', png])
        im = Image.open(png).convert('RGB'); d = ImageDraw.Draw(im)
        for s in range(int(dur) + 1):
            X = int(s * W / dur); d.line([(X, 0), (X, 220)], fill=(255, 60, 60) if s % 5 == 0 else (80, 80, 80), width=2); d.text((X + 3, 3), str(s), fill=(255, 255, 0))
        im.save(png); print('waveform:', png)
    except Exception as ex:  # PIL optional
        print('(waveform não gerada:', ex, ')')
