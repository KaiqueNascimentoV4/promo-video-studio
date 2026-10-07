"""Mix final: voz (cadeia broadcast) + trilha (ducking desde o 1.º quadro) + SFX (ataque aparado, de-esser) → loudnorm.

  python mixar.py mix.json [--relatorio]
  python mixar.py --so-voz voz.wav --out mix.wav [--lufs -14]

mix.json:
{
  "voz": "voz.wav",                       (opcional em motion sem fala)
  "duracao": 38.5,                        (opcional; padrão = voz ou vídeo em "video")
  "video": "mudo.mp4",                    (opcional, só para pegar a duração)
  "trilha": {"arquivo": "musica.wav", "inicio": 0.0,          segundo da música que toca no t=0 do vídeo
             "drop_em": 12.4, "batidas": "musica.batidas.json", alinha o drop da música neste instante do vídeo
             "abafar_ate": 12.4,                                lowpass 800 Hz até aqui (porta abrindo)
             "voz_acima_db": 6, "fade_out": 1.0},
  "sfx": "sfx.json",
  "lufs": -14, "tp": -1, "out": "mix.wav"
}
--relatorio: para cada SFX imprime o pico do evento × RMS da música no instante (o pico tem de ficar ACIMA).
"""
import argparse, json, os, subprocess, sys, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ffbin, run, ler_json, probe

SR = 48000
CADEIA_VOZ = ('highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=5:release=80:makeup=4,'
              'equalizer=f=200:t=q:w=1:g=-2,equalizer=f=4000:t=q:w=1.2:g=3,deesser=i=0.4,alimiter=limit=0.89:level=0')
CADEIA_SFX = 'deesser=i=0.5,lowpass=f=9000'
NIVEL = {'baixo': -8, 'medio': -4, 'alto': 0}


def ler(p, filtro=None, sr=SR):
    cmd = [ffbin(), '-v', 'error', '-i', p]
    if filtro: cmd += ['-af', filtro]
    cmd += ['-ac', '2', '-ar', str(sr), '-f', 'f32le', '-']
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode: sys.exit(f'falhou ao ler {p}: {r.stderr.decode(errors="ignore")[-300:]}')
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()


def gravar(p, x):
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def db(x): return 20 * np.log10(max(float(x), 1e-9))


def rms_env(x, win=0.05):
    m = (x ** 2).mean(1); k = int(win * SR)
    return np.sqrt(np.convolve(m, np.ones(k) / k, 'same') + 1e-12)


def loudnorm(src, out, I=-14, tp=-1):
    r = run([ffbin(), '-hide_banner', '-i', src, '-af', f'loudnorm=I={I}:TP={tp}:LRA=11:print_format=json', '-f', 'null', '-'])
    js = json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}') + 1])
    f = (f'loudnorm=I={I}:TP={tp}:LRA=11:measured_I={js["input_i"]}:measured_TP={js["input_tp"]}:measured_LRA={js["input_lra"]}:'
         f'measured_thresh={js["input_thresh"]}:offset={js["target_offset"]}:linear=true,alimiter=limit={10 ** ((tp - 0.3) / 20):.3f}:level=0')
    run([ffbin(), '-y', '-v', 'error', '-i', src, '-af', f, '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le', out])
    m = run([ffbin(), '-hide_banner', '-i', out, '-af', 'ebur128=peak=true', '-f', 'null', '-']).stderr
    I_ = m[m.rfind('I:'):].split()[1]; TP_ = m[m.rfind('Peak:'):].split()[1]
    print(f'→ {out}  {I_} LUFS, true peak {TP_} dBTP')


def aparar_ataque(x, lim_db=-42):
    a = np.abs(x).max(1); thr = 10 ** (lim_db / 20)
    idx = np.argmax(a > thr) if (a > thr).any() else 0
    return x[max(0, idx - int(0.002 * SR)):]


def mix(cfgm, relatorio):
    base = os.path.dirname(os.path.abspath(cfgm['_arquivo']))
    P = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
    voz = ler(P(cfgm['voz']), CADEIA_VOZ) if cfgm.get('voz') else None
    dur = cfgm.get('duracao') or (len(voz) / SR if voz is not None else float(probe(P(cfgm['video']))['format']['duration']))
    n = int(round(dur * SR)); out = np.zeros((n, 2), np.float32)
    if voz is not None: voz = np.vstack([voz, np.zeros((max(0, n - len(voz)), 2), np.float32)])[:n]; out += voz
    mus_env = np.full(n, 1e-6)
    tr = cfgm.get('trilha')
    if tr:
        m = ler(P(tr['arquivo']))
        ini = tr.get('inicio', 0.0)
        if 'drop_em' in tr and tr.get('batidas'):
            drop = ler_json(P(tr['batidas'])).get('drop')
            if drop is not None: ini = drop - tr['drop_em']
        k0 = int(round(ini * SR))
        seg = m[k0:k0 + n] if k0 >= 0 else np.vstack([np.zeros((-k0, 2), np.float32), m[:n + k0]])
        if len(seg) < n: print(f'⚠ trilha acaba antes do vídeo ({len(seg) / SR:.1f} s < {dur:.1f} s) — escolha outra ou estenda')
        seg = np.vstack([seg, np.zeros((n - len(seg), 2), np.float32)])
        if tr.get('abafar_ate'):
            with tempfile.TemporaryDirectory() as td:
                gravar(os.path.join(td, 'm.wav'), seg); ab = ler(os.path.join(td, 'm.wav'), 'lowpass=f=800,lowpass=f=800')[:n]
            ka = int(tr['abafar_ate'] * SR); xf = int(0.3 * SR)
            w = np.clip((np.arange(n) - (ka - xf)) / xf, 0, 1)[:, None]
            seg = ab * (1 - w) + seg * w
        fo = int(tr.get('fade_out', 1.0) * SR); seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
        g = 10 ** (tr.get('ganho_db', -6) / 20); seg *= g
        if voz is not None:  # ducking desde o 1.º quadro: música alvo = voz − voz_acima_db (nos trechos de fala)
            ve = rms_env(voz, 0.05); ativo = ve > 10 ** (-40 / 20)
            alvo_db = db(np.sqrt((voz[ativo] ** 2).mean())) - tr.get('voz_acima_db', 6) if ativo.any() else -30
            me = rms_env(seg, 0.4)
            red = np.where(ativo, np.minimum(1, 10 ** (alvo_db / 20) / np.maximum(me, 1e-6)), 1.0)
            a_, r_ = np.exp(-1 / (0.03 * SR)), np.exp(-1 / (0.3 * SR))
            gsm = np.empty(n); c = 1.0
            # suavização ataque/release (amostra a amostra seria lento: passo de 1 ms)
            step = int(0.001 * SR)
            for i in range(0, n, step):
                t_ = red[i]; coef = a_ ** step if t_ < c else r_ ** step; c = t_ + (c - t_) * coef; gsm[i:i + step] = c
            seg *= gsm[:, None].astype(np.float32)
        out += seg; mus_env = rms_env(seg, 0.4)
    sfx = cfgm.get('sfx')
    if sfx:
        evs = ler_json(P(sfx))['eventos']; cache = {}
        voz_ref = db(np.sqrt((voz ** 2).mean())) if voz is not None else -20
        if relatorio: print(f'{"t":>7s} {"cat":12s} {"pico":>7s} {"RMS mús":>8s}  ok?')
        for e in evs:
            if e['arquivo'] not in cache: cache[e['arquivo']] = aparar_ataque(ler(e['arquivo'], CADEIA_SFX))
            s = cache[e['arquivo']].copy()
            k = int(e['t'] * SR)
            if e.get('alinhar') == 'pico': k -= int(np.argmax(rms_env(s, 0.02)))
            k = max(0, k)
            seg_n = min(len(s), n - k)
            if seg_n <= 0: continue
            s = s[:seg_n]
            ref_db = db(mus_env[min(n - 1, int(e['t'] * SR))]) if tr else voz_ref - 10
            alvo = ref_db + NIVEL.get(e.get('nivel', 'medio'), -4)
            s *= 10 ** ((alvo - db(np.sqrt((s ** 2).mean()))) / 20)
            if db(np.abs(s).max()) < ref_db + 3: s *= 10 ** ((ref_db + 3 - db(np.abs(s).max())) / 20)  # pico SEMPRE acima da música
            out[k:k + seg_n] += s
            if relatorio:
                pk = db(np.abs(s).max()); print(f'{e["t"]:7.2f} {e["cat"]:12s} {pk:7.1f} {ref_db:8.1f}  {"✔" if pk > ref_db else "✘"}')
    o = P(cfgm.get('out', 'mix.wav'))
    with tempfile.TemporaryDirectory() as td:
        bruto = os.path.join(td, 'bruto.wav'); gravar(bruto, out / max(1.0, np.abs(out).max() / 0.98)); loudnorm(bruto, o, cfgm.get('lufs', -14), cfgm.get('tp', -1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mix', nargs='?'); ap.add_argument('--relatorio', action='store_true')
    ap.add_argument('--so-voz'); ap.add_argument('--out', default='mix.wav'); ap.add_argument('--lufs', type=float, default=-14)
    a = ap.parse_args()
    if a.so_voz:
        with tempfile.TemporaryDirectory() as td:
            t = os.path.join(td, 'v.wav'); gravar(t, ler(a.so_voz, CADEIA_VOZ)); loudnorm(t, a.out, a.lufs, -1)
    elif a.mix:
        c = ler_json(a.mix); c['_arquivo'] = a.mix; mix(c, a.relatorio)
    else: ap.print_help()
