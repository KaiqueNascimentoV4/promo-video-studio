"""encode.py [QUADROS_DIR] [SAIDA.mp4] [AUDIO.wav] [--nvenc] — PNG f0000… → H.264 no fps EXATO da ref, com o mix.
Ruído leve (alls=2) + crf 19 -tune film: evita banding sem explodir o arquivo (ruído forte por quadro com crf 16 → 800 MB).
Saída bt709/tv; áudio AAC 256k cortado na duração do vídeo."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _proj import ROOT, proj, fps_str, ff

args = [a for a in sys.argv[1:] if not a.startswith('--')]; nvenc = '--nvenc' in sys.argv
P = proj(); fr = fps_str(P)
frames = args[0] if len(args) > 0 else os.path.join(ROOT, 'out', 'full')
out = args[1] if len(args) > 1 else os.path.join(ROOT, 'remake.mp4')
audio = args[2] if len(args) > 2 else os.path.join(ROOT, 'audio', 'mix.wav')
n = len([f for f in os.listdir(frames) if f.startswith('f') and f.endswith('.png')])
dur = n * P['FPS_DEN'] / P['FPS_NUM']
cmd = [ff(), '-y', '-v', 'error', '-framerate', fr, '-start_number', '0', '-i', os.path.join(frames, 'f%04d.png')]
if os.path.exists(audio): cmd += ['-i', audio, '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-t', f'{dur:.4f}']
cmd += ['-vf', 'noise=alls=2:allf=t,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv']
cmd += (['-c:v', 'h264_nvenc', '-preset', 'p5', '-tune', 'hq', '-rc', 'vbr', '-cq', '19', '-b:v', '0'] if nvenc
        else ['-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-tune', 'film'])
cmd += ['-pix_fmt', 'yuv420p', '-r', fr, '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart', out]
subprocess.run(cmd, check=True)
print(f'→ {out}  ({n} quadros, {dur:.3f} s{", com áudio" if os.path.exists(audio) else ", SEM áudio"})')
