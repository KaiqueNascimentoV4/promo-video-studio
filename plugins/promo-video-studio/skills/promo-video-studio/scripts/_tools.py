"""Shared helpers: locate ffmpeg/ffprobe, run commands, parse loudness."""
import glob
import os
import re
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


_FFMPEG = None


def ffmpeg() -> str:
    """Return a usable ffmpeg executable (env FFMPEG > PATH > common install folders). Cached."""
    global _FFMPEG
    if _FFMPEG:
        return _FFMPEG
    cand = os.environ.get('FFMPEG')
    if cand and os.path.exists(cand):
        _FFMPEG = cand
        return cand
    found = shutil.which('ffmpeg')
    if found:
        _FFMPEG = found
        return found
    home = os.path.expanduser('~')
    # shallow patterns only (a recursive scan of Documents takes minutes on dev machines)
    patterns = [
        os.path.join(home, 'Documents', 'ffmpeg*', 'bin', 'ffmpeg.exe'),
        os.path.join(home, 'Documents', '*', 'ffmpeg*', 'bin', 'ffmpeg.exe'),
        os.path.join(home, 'Downloads', 'ffmpeg*', 'bin', 'ffmpeg.exe'),
        os.path.join(home, 'scoop', 'apps', 'ffmpeg', '*', 'bin', 'ffmpeg.exe'),
        r'C:\ffmpeg\bin\ffmpeg.exe', r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
        '/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/usr/bin/ffmpeg',
    ]
    for p in patterns:
        hits = sorted(glob.glob(p))
        if hits:
            _FFMPEG = hits[-1]
            return _FFMPEG
    raise SystemExit('ffmpeg não encontrado. Instale ou defina a variável FFMPEG com o caminho do executável.')


def run(args, check=True, capture=False):
    """Run ffmpeg with args (list, without the executable)."""
    cmd = [ffmpeg()] + list(args)
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return subprocess.run(cmd, check=check)


def duration(path) -> float:
    r = run(['-hide_banner', '-i', path], check=False, capture=True).stderr
    h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def loudness(path):
    """Return (integrated LUFS, true peak dBFS)."""
    r = run(['-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], check=False, capture=True).stderr
    lufs = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])
    peak = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
    return lufs, peak


def to_wav(src, dst, sr=16000, mono=True):
    args = ['-y', '-loglevel', 'error', '-i', src]
    if mono:
        args += ['-ac', '1']
    args += ['-ar', str(sr), dst]
    run(args)
    return dst
