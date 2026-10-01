"""Break down a reference video: contact sheets with timestamps (2 fps) + narration transcript.

Usage:
  python analyze_reference.py referencia.mp4 [--out pasta] [--lang pt] [--fps 2]
Then READ the generated sheet_*.jpg images and the transcript to extract structure, pacing and visual language.
"""
import argparse, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tools import run, duration  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--out'); ap.add_argument('--lang', default='pt'); ap.add_argument('--fps', default='2')
a = ap.parse_args()
out = a.out or os.path.splitext(os.path.basename(a.video))[0] + '_analise'
os.makedirs(out, exist_ok=True)
info = run(['-hide_banner', '-i', a.video], check=False, capture=True).stderr
print('\n'.join(l.strip() for l in info.splitlines() if re.search(r'Duration|Stream', l)))
run(['-y', '-loglevel', 'error', '-i', a.video, '-vf',
     f"fps={a.fps},scale=640:-1,drawtext=text='%{{pts\\:hms}}':x=8:y=8:fontsize=20:fontcolor=yellow:box=1:boxcolor=black,tile=4x3",
     os.path.join(out, 'sheet_%02d.jpg')], check=False)
sheets = sorted(f for f in os.listdir(out) if f.startswith('sheet_'))
print(f'{len(sheets)} contact sheets em {out} (cada uma = {12 / float(a.fps):.0f}s)')
has_audio = 'Audio:' in info
if has_audio:
    print('\nTranscrição:')
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'words.py'), a.video, '--lang', a.lang, '--text'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    txt = r.stdout.strip() or r.stderr.strip()[-500:]
    open(os.path.join(out, 'transcricao.txt'), 'w', encoding='utf-8').write(txt); print(txt)
print(f'\nDuração: {duration(a.video):.1f}s')
