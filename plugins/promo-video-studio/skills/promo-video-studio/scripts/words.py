"""Transcribe narration with word timestamps (faster-whisper, local, free).

Usage:
  python words.py narracao.mp3 --lang pt            # prints "t palavra | ..." and writes narracao.words.json
  python words.py final.mp4 --lang es --text        # only the full text (QA of the final mix)
  python words.py narracao.mp3 --pauses             # list silences (>0.25 s) to compress or check pacing
Options: --model small (default) | medium (more accurate, slower)
"""
import argparse, json, os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tools import run, to_wav  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('file'); ap.add_argument('--lang', default='pt'); ap.add_argument('--model', default='small')
ap.add_argument('--text', action='store_true'); ap.add_argument('--pauses', action='store_true')
a = ap.parse_args()

if a.pauses:
    r = run(['-hide_banner', '-i', a.file, '-af', 'silencedetect=noise=-40dB:d=0.25', '-f', 'null', '-'], check=False, capture=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', r)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]
    for s, e in zip(starts, ends):
        print(f'{s:6.2f} → {e:6.2f}  ({e - s:.2f}s)')
    sys.exit(0)

from faster_whisper import WhisperModel  # pip install faster-whisper
wav = to_wav(a.file, os.path.join(tempfile.gettempdir(), 'pvs_words.wav'))
model = WhisperModel(a.model, device='cpu', compute_type='int8')
segs, _ = model.transcribe(wav, language=a.lang, word_timestamps=not a.text, vad_filter=False)
if a.text:
    print(' '.join(s.text.strip() for s in segs))
    sys.exit(0)
words = [(round(w.start, 2), round(w.end, 2), w.word.strip()) for s in segs for w in s.words]
out = os.path.splitext(a.file)[0] + '.words.json'
json.dump(words, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
print(' | '.join(f'{s:.2f} {w}' for s, e, w in words))
print(f'\n{len(words)} palavras · fim da fala {words[-1][1]:.2f}s · salvo em {out}')
