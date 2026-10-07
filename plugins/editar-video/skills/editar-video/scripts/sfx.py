"""Monta a lista de SFX (sfx.json) amarrada aos movimentos, e sintetiza os sons que faltarem.

  python sfx.py [--cortes cortes.json] [--words voz.words.json --chaves "grátis,agora"] [--cenas cenas.json]
                [--nivel leve|medio|carregado] [--out sfx.json] [--sintetizar [--pasta-sint sfx_sint]]

Fontes de eventos:
  --cortes  cortes do cortar.py → whoosh (leve: 1 a cada 3 cortes; médio: cortes de take + batida; carregado: todos)
  --chaves  palavras-chave da fala → clique de obturador quando a palavra é dita (não use "bop" suave)
  --cenas   JSON [{"t": s, "cat": "whoosh|whoosh_grave|impacto|sub|obturador|clique|digitacao|check|riser", "nivel": "medio"}]
            (cenas de motion, CTA, contagem → use "whoosh" no número subindo, nunca tique de contagem)
Categorias → arquivos pelo sfx_mapa da config (config.py --mapear-sfx). Sem pack ou com --sintetizar, gera os sons
em numpy (whoosh, impacto, sub, obturador, clique, digitação, check, riser) em --pasta-sint.
O mixar.py apara o ataque, aplica de-esser + highcut em TODO SFX e ajusta o nível pelo RMS da música no instante.
"""
import argparse, os, re, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import cfg, ler_json, gravar_json

SR = 48000
NIVEL = {'baixo': -8, 'medio': -4, 'alto': 0}


def _env(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) ** 2 if na else 1; e[n - nr:] = np.linspace(1, 0, nr) ** 2 if nr else 1
    return e


def _ruido(n, seed): return np.random.default_rng(seed).standard_normal(n)


def _passa_banda(x, f0, f1):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < f0) | (f > f1)] = 0
    return np.fft.irfft(X, len(x))


def sintetizar(cat, seed=1):
    if cat in ('whoosh', 'whoosh_grave'):
        n = int(0.55 * SR); x = _ruido(n, seed); t = np.linspace(0, 1, n)
        lo, hi = (120, 1500) if cat == 'whoosh_grave' else (500, 6000)
        seg = np.array_split(x, 24); out = []
        for i, s in enumerate(seg):  # varredura de banda (sobe e desce)
            k = np.sin(np.pi * i / 23); out.append(_passa_banda(s, lo, lo + (hi - lo) * (0.3 + 0.7 * k)))
        x = np.concatenate(out) * np.exp(-((t - 0.55) / 0.22) ** 2)
    elif cat == 'impacto':
        n = int(0.6 * SR); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * (70 * t - 20 * t ** 2)) * np.exp(-t * 9) + 0.3 * _passa_banda(_ruido(n, seed), 100, 2500) * np.exp(-t * 30)
    elif cat == 'sub':
        n = int(1.2 * SR); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * np.cumsum(60 - 25 * t / 1.2) / SR) * np.exp(-t * 3) * _env(n, 0.005, 0.2)
    elif cat in ('obturador', 'clique'):
        n = int(0.12 * SR); x = np.zeros(n)
        for off, g in ((0, 1), (0.045, 0.7)) if cat == 'obturador' else ((0, 1),):
            k = int(off * SR); m = int(0.012 * SR)
            x[k:k + m] += g * _passa_banda(_ruido(m, seed + k), 1500, 9000) * np.exp(-np.arange(m) / (0.002 * SR))
    elif cat == 'digitacao':
        n = int(0.3 * SR); x = np.zeros(n)
        for i, off in enumerate((0, 0.07, 0.13, 0.21)):
            k = int(off * SR); m = int(0.008 * SR)
            x[k:k + m] += _passa_banda(_ruido(m, seed + i), 2000, 8000) * np.exp(-np.arange(m) / (0.0015 * SR))
    elif cat == 'check':
        n = int(0.45 * SR); t = np.arange(n) / SR
        x = sum(np.sin(2 * np.pi * f * t) * np.exp(-(t - d).clip(0) * 9) * (t >= d) for f, d in ((880, 0), (1320, 0.09)))
    elif cat == 'riser':
        n = int(1.6 * SR); t = np.linspace(0, 1, n)
        x = _passa_banda(_ruido(n, seed), 300, 7000) * t ** 2 * _env(n, 0.05, 0.02)
    else: raise ValueError(cat)
    x = x / (np.abs(x).max() + 1e-9) * 0.7
    return np.stack([x, x], 1).astype(np.float32)


def gravar_wav(p, x):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with wave.open(p, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cortes'); ap.add_argument('--words'); ap.add_argument('--chaves', default='')
    ap.add_argument('--cenas'); ap.add_argument('--legenda', help='(compatibilidade) ignorado: use --words/--chaves')
    ap.add_argument('--nivel', default='medio', choices=['leve', 'medio', 'carregado'])
    ap.add_argument('--out', default='sfx.json'); ap.add_argument('--sintetizar', action='store_true')
    ap.add_argument('--pasta-sint', default='sfx_sint')
    a = ap.parse_args()
    mapa = cfg().get('sfx_mapa', {})
    ev = []
    if a.cortes:
        cs = ler_json(a.cortes)['cortes']
        for i, c in enumerate(cs):
            if a.nivel == 'leve' and i % 3: continue
            if a.nivel == 'medio' and not (c['tipo'] == 'take' or c.get('batida')): continue
            ev.append(dict(t=c['t'], cat='whoosh', nivel='baixo' if a.nivel == 'leve' else 'medio', alinhar='pico', origem='corte'))
    if a.words and a.chaves:
        ch = {re.sub(r'\W', '', k.strip().lower()) for k in a.chaves.split(',') if k.strip()}
        for w in ler_json(a.words)['palavras']:
            if re.sub(r'\W', '', w['w'].lower()) in ch: ev.append(dict(t=w['s'], cat='obturador', nivel='medio', alinhar='inicio', origem='palavra:' + w['w']))
    if a.cenas:
        for c in ler_json(a.cenas):
            ev.append(dict(t=c['t'], cat=c['cat'], nivel=c.get('nivel', 'medio'),
                           alinhar='pico' if c['cat'].startswith('whoosh') or c['cat'] == 'riser' else 'inicio', origem='cena'))
    ev.sort(key=lambda e: e['t'])
    # evita empilhar: dois eventos a < 0,25 s → fica o mais forte
    limpo = []
    for e in ev:
        if limpo and e['t'] - limpo[-1]['t'] < 0.25:
            if NIVEL[e['nivel']] > NIVEL[limpo[-1]['nivel']]: limpo[-1] = e
            continue
        limpo.append(e)
    usados = {e['cat'] for e in limpo}
    for cat in sorted(usados):
        if a.sintetizar or cat not in mapa or not os.path.exists(mapa.get(cat, '')):
            p = os.path.join(a.pasta_sint, f'{cat}.wav'); gravar_wav(p, sintetizar(cat)); mapa = dict(mapa, **{cat: os.path.abspath(p)})
    for e in limpo: e['arquivo'] = mapa[e['cat']]
    gravar_json(a.out, dict(eventos=limpo))
    print(f'{len(limpo)} SFX ({a.nivel}) → {a.out}')
    for e in limpo: print(f'  {e["t"]:7.2f}  {e["cat"]:12s} {e["nivel"]:6s} {os.path.basename(e["arquivo"])}  ({e["origem"]})')


if __name__ == '__main__':
    main()
