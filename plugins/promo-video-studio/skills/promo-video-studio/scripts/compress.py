"""Compress a video under a size limit (e.g. Instagram/WhatsApp) with 2-pass x264.

Usage:  python compress.py video.mp4 [--max-mb 24] [--fps 30] [--audio-k 128] [--out saida.mp4]
At low bitrates 30 fps looks sharper than 60 (twice the bits per frame). Keeps resolution.
"""
import argparse, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tools import run, duration  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--max-mb', type=float, default=24)
ap.add_argument('--fps', default='30'); ap.add_argument('--audio-k', type=int, default=128); ap.add_argument('--out')
a = ap.parse_args()
dur = duration(a.video)
total_kbps = a.max_mb * 8 * 1024 * 0.96 / dur          # 4% container/safety margin
vk = int(total_kbps - a.audio_k)
out = a.out or os.path.splitext(a.video)[0] + f'_{int(a.max_mb)}MB.mp4'
log = os.path.join(tempfile.gettempdir(), 'pvs_2pass')
common = ['-vf', f'fps={a.fps}', '-c:v', 'libx264', '-preset', 'slow', '-b:v', f'{vk}k', '-maxrate', f'{int(vk*1.4)}k', '-bufsize', f'{vk*2}k',
          '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-passlogfile', log]
run(['-y', '-loglevel', 'error', '-i', a.video] + common + ['-pass', '1', '-an', '-f', 'mp4', os.devnull])
run(['-y', '-loglevel', 'error', '-i', a.video] + common + ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
     '-pass', '2', '-c:a', 'aac', '-b:a', f'{a.audio_k}k', '-ar', '48000', '-movflags', '+faststart', out])
print(f'ok: {out}  {os.path.getsize(out)/1024/1024:.1f} MB  (vídeo {vk} kbps, {a.fps} fps)')
