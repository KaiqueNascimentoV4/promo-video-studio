"""sync.py [QUADROS_DIR] [SAIDA.mp4] — REF (em cima) sobre o remake (embaixo), travados quadro a quadro, com o número do
quadro gravado nos dois. Áudio = audio/mix.wav se existir. É a PROVA do 1:1: mostre ao usuário.
(Com TIMEMAP ativo o remake fica mais longo que a ref e o sync deixa de ser 1:1 — avise.)"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _proj import ROOT, proj, fps_str, ff, fonte_sistema

P = proj(); fr = fps_str(P)
frames = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'out', 'full')
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'sync-check.mp4')
mix = os.path.join(ROOT, 'audio', 'mix.wav')
w = 1280 if P['W'] >= P['H'] else 720; h = int(round(w * P['H'] / P['W'] / 2) * 2)
fonte = fonte_sistema()
ft = f"fontfile='{fonte.replace(':', chr(92) + ':')}':" if fonte else ''
dt = lambda lab: f"drawtext={ft}text='{lab} %{{frame_num}}':start_number=0:x=12:y=12:fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.6"
cmd = [ff(), '-y', '-v', 'error', '-framerate', fr, '-start_number', '0', '-i', os.path.join(ROOT, P.get('REF_HALF', 'ref/half'), 'f%04d.jpg'),
       '-framerate', fr, '-start_number', '0', '-i', os.path.join(frames, 'f%04d.png')]
if os.path.exists(mix): cmd += ['-i', mix]
fc = f'[0:v]scale={w}:{h},{dt("REF")}[a];[1:v]scale={w}:{h},{dt("NOSSO")}[b];[a][b]vstack=inputs=2[v]'
cmd += ['-filter_complex', fc, '-map', '[v]']
if os.path.exists(mix): cmd += ['-map', '2:a', '-c:a', 'aac', '-b:a', '192k']
cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-r', fr, '-shortest', out]
subprocess.run(cmd, check=True)
print('→', out)
