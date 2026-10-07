"""Grade de batidas de uma trilha: BPM, fase, batidas, compassos, drop e arco de energia.

  python batidas.py MUSICA [--out batidas.json] [--bpm-min 70 --bpm-max 180]

Método: fluxo espectral (onset) → autocorrelação para o período → fase pela soma do onset nos instantes da grade.
Drop = maior subida de energia grave (RMS < 150 Hz) entre janelas de 2 s depois de 15% da música.
Arco = RMS por seção de 4 compassos (dB) → "positivo" se a 2.ª metade é ≥ 2 dB mais alta que a 1.ª.
Saída: {bpm, periodo, fase, batidas[], compassos[], drop, duracao, arco_db[], arco, onsets_fortes[]}
"""
import argparse, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ffbin, gravar_json

SR = 22050


def carregar(p, sr=SR):
    r = subprocess.run([ffbin(), '-v', 'error', '-i', p, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True)
    x = np.frombuffer(r.stdout, np.float32)
    if not len(x): sys.exit(f'não consegui ler o áudio de {p}')
    return x


def analisar(x, sr=SR, bmin=70, bmax=180):
    hop, n = 512, 2048
    nfr = 1 + (len(x) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(nfr)[:, None]
    S = np.abs(np.fft.rfft(x[idx] * np.hanning(n), axis=1))
    L = np.log1p(100 * S)
    flux = np.maximum(0, np.diff(L, axis=0)).sum(1); flux = np.concatenate([[0], flux])
    flux = flux - np.convolve(flux, np.ones(16) / 16, 'same'); flux = np.maximum(flux, 0)
    fps = sr / hop
    ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]
    lags = np.arange(len(ac)); bpms = 60 * fps / np.maximum(lags, 1)
    ok = (bpms >= bmin) & (bpms <= bmax)
    w = np.exp(-0.5 * (np.log2(np.maximum(bpms, 1) / 100) / 1.0) ** 2)  # leve preferência por ~100 (evita o dobro do tempo)
    lag = int(lags[ok][np.argmax((ac * w)[ok])])
    # refina o período com interpolação parabólica
    if 1 <= lag < len(ac) - 1:
        a_, b_, c_ = ac[lag - 1], ac[lag], ac[lag + 1]; d = 0.5 * (a_ - c_) / (a_ - 2 * b_ + c_ + 1e-9); lagf = lag + d
    else: lagf = lag
    per = lagf / fps; bpm = 60 / per
    fases = np.linspace(0, per, 48, endpoint=False)
    dur = len(x) / sr
    def score(ph):
        ts = np.arange(ph, dur, per); k = np.clip((ts * fps).astype(int), 0, len(flux) - 1); return flux[k].sum()
    fase = float(fases[np.argmax([score(p) for p in fases])])
    beats = np.arange(fase, dur, per)
    # compasso: qual das 4 batidas tem mais grave → "1"
    lo = S[:, :int(150 / (sr / n)) + 1].sum(1)
    k = np.clip((beats * fps).astype(int), 0, len(lo) - 1)
    off = int(np.argmax([lo[k[j::4]].sum() for j in range(4)]))
    compassos = beats[off::4]
    # drop
    win = int(2 * fps); rms_lo = np.convolve(lo, np.ones(win) / win, 'same')
    st = int(len(rms_lo) * 0.15); dif = rms_lo[st + win:] - rms_lo[st:-win] if len(rms_lo) > st + win else np.array([0])
    drop_t = float((st + win + int(np.argmax(dif))) / fps) if dif.size else None
    drop = round(float(beats[np.argmin(np.abs(beats - drop_t))]), 3) if drop_t is not None and len(beats) else None
    # arco
    rms = np.sqrt(np.convolve(x ** 2, np.ones(sr) / sr, 'same') + 1e-12)
    sec = per * 16; nsec = max(1, int(dur // sec))
    arco = [round(float(20 * np.log10(rms[int(i * sec * sr):int((i + 1) * sec * sr)].mean() + 1e-9)), 1) for i in range(nsec)]
    h = len(arco) // 2
    tend = (np.mean(arco[h:]) - np.mean(arco[:h])) if len(arco) >= 2 else 0
    fortes = (np.argsort(flux)[::-1][:40] / fps).round(3).tolist()
    return dict(bpm=round(bpm, 2), periodo=round(per, 4), fase=round(fase, 4), duracao=round(dur, 3),
                batidas=beats.round(3).tolist(), compassos=compassos.round(3).tolist(), drop=drop,
                arco_db=arco, arco='positivo' if tend >= 2 else 'plano' if tend > -2 else 'negativo',
                onsets_fortes=sorted(fortes))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('musica'); ap.add_argument('--out'); ap.add_argument('--bpm-min', type=float, default=70)
    ap.add_argument('--bpm-max', type=float, default=180)
    a = ap.parse_args()
    r = analisar(carregar(a.musica), SR, a.bpm_min, a.bpm_max)
    r['arquivo'] = os.path.abspath(a.musica)
    out = a.out or os.path.splitext(a.musica)[0] + '.batidas.json'
    gravar_json(out, r)
    print(f'{os.path.basename(a.musica)}: {r["bpm"]} BPM, fase {r["fase"]} s, {len(r["batidas"])} batidas, '
          f'drop ≈ {r["drop"]} s, duração {r["duracao"]} s, arco {r["arco"]} {r["arco_db"]}')
    print('→', out)
