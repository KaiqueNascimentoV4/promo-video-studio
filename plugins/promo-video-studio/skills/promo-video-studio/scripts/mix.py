"""Mix narration + music (ducked) + SFX onto the rendered video and encode the final file.

Usage:  python mix.py mix.json
Config (paths relative to the json file):
{
  "video": "video_noaudio.mp4",            # rendered by render.mjs (no audio)
  "out": "Final_45s.mp4",
  "dur": 45.0,
  "vo":    {"file": "narracao.mp3", "offset": 0.4},
  "music": {"file": "trilha.mp3", "shift": 1.6, "volume": 0.62, "fade_in": 0.2, "fade_out": 2.2,
            "stops": [[35.99, 37.5]],          # optional comic stop-time windows (video time): music dips to ~12%
            "duck": {"threshold": 0.02, "ratio": 7, "attack": 20, "release": 420}},
  "events": [ {"file": "whoosh.mp3", "t": 2.75, "vol": 0.22, "hp": true} ],   # t = video time; hp = high-pass 900 Hz
  "loudness": -14
}
Writes the mp4 (bt709 tv-range, H.264 CRF 17, AAC 256k stereo) and prints loudness/peak.
Other scripts import build_audio() from here (premiere_package.py uses it for stems).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tools import run, loudness  # noqa: E402


def load(cfg_path):
    base = os.path.dirname(os.path.abspath(cfg_path))
    C = json.load(open(cfg_path, encoding='utf-8'))
    C['_base'] = base
    return C


def P(C, p):
    return p if os.path.isabs(p) else os.path.join(C['_base'], p)


def build_audio(C, first=0, master=True, parts=('vo', 'music', 'events')):
    """Return (inputs, filter_complex). Audio inputs start at index `first`. Output label: [out]."""
    DUR = float(C['dur']); vo = C['vo']; mu = C.get('music'); O = float(vo.get('offset', 0.4))
    inputs, fc, labels = [], [], []
    idx = first
    inputs += ['-i', P(C, vo['file'])]
    fc.append(f"[{idx}:a]aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=80,"
              f"adelay={int(O*1000)}|{int(O*1000)},apad=whole_dur={DUR},aformat=channel_layouts=stereo,asplit=2[vo][vosc]")
    idx += 1
    if 'vo' in parts:
        labels.append('[vo]')
    else:
        fc.append('[vo]anullsink')
    if mu:
        inputs += ['-i', P(C, mu['file'])]
        sh = float(mu.get('shift', 0)); fo = float(mu.get('fade_out', 2.0)); d = mu.get('duck', {})
        vol = ''
        if mu.get('stops'):
            terms = '*'.join(f"(1-0.88*clip((t-{a:.2f})/0.08\\,0\\,1)*(1-clip((t-{b:.2f})/0.12\\,0\\,1)))" for a, b in mu['stops'])
            vol = f",volume=eval=frame:volume='{terms}'"
        fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim={sh}:{sh + DUR},asetpts=PTS-STARTPTS{vol},"
                  f"afade=t=in:st=0:d={mu.get('fade_in', 0.2)},afade=t=out:st={DUR - fo}:d={fo},apad=whole_dur={DUR},volume={mu.get('volume', 0.6)}[mus]")
        fc.append(f"[mus][vosc]sidechaincompress=threshold={d.get('threshold', 0.02)}:ratio={d.get('ratio', 7)}:"
                  f"attack={d.get('attack', 20)}:release={d.get('release', 420)}:makeup=1[duck]")
        idx += 1
        if 'music' in parts:
            labels.append('[duck]')
        else:
            fc.append('[duck]anullsink')
    else:
        fc.append('[vosc]anullsink')
    if 'events' in parts:
        for i, e in enumerate(C.get('events', [])):
            inputs += ['-i', P(C, e['file'])]; ms = int(round(float(e['t']) * 1000)); hp = ',highpass=f=900' if e.get('hp') else ''
            fc.append(f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo{hp},volume={e.get('vol', 0.3)},adelay={ms}|{ms}[e{i}]")
            labels.append(f'[e{i}]'); idx += 1
    m = f",loudnorm=I={C.get('loudness', -14)}:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.87:level=false" if master else ''
    fc.append(''.join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{DUR}{m}[out]")
    return inputs, ';'.join(fc)


VIDEO_ENC = ['-vf', 'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p',
             '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-maxrate', '30M', '-bufsize', '60M', '-profile:v', 'high',
             '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']

if __name__ == '__main__':
    C = load(sys.argv[1])
    inputs, fc = build_audio(C, first=1)
    out = P(C, C['out'])
    run(['-y', '-loglevel', 'error', '-i', P(C, C['video'])] + inputs + ['-filter_complex', fc, '-map', '0:v', '-map', '[out]'] + VIDEO_ENC +
        ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2', '-t', str(C['dur']), '-movflags', '+faststart', out])
    lufs, peak = loudness(out)
    print(f'ok: {out}\n  loudness {lufs} LUFS · pico {peak} dBFS (alvo ~{C.get("loudness", -14)} LUFS, pico <= -1)')
