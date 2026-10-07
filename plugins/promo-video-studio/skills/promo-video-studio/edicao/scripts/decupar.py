"""Decupagem assistida: lê os *.words.json dos brutos e sugere um EDL (melhor take de cada fala).

  python decupar.py PASTA_DOS_BRUTOS [--out edl.json] [--ordem roteiro.txt] [--sim 0.6]

Como decide (SUGESTÃO — revise sempre o edl.json; o script não vê olhar, energia nem câmera):
 1. Cada bruto vira frases (quebra em pausa > 0,6 s ou pontuação final).
 2. Remove conversa de direção ("né?", "ok?", "corta", "de novo", "vou repetir", "é isso?") e frases de 1–2 palavras soltas.
 3. Agrupa frases parecidas (takes repetidos da mesma fala) por similaridade de palavras ≥ --sim.
 4. Em cada grupo escolhe o take com melhor nota = confiança média do Whisper − penalidade por hesitação ("é...", "hã")
    e por repetição interna; empate → o mais recente (na prática o último take costuma ser o bom).
 5. Ordena pela ordem de --ordem (roteiro, uma frase por linha) ou pela 1.ª aparição.
Cada item: {clip, in, out, texto, nota, alternativas:[{clip,in,out,texto,nota}]}. in/out já com folga de 0,08 s
antes (recuo para plosivas) e 0,12 s depois; o cortar.py aperta os silêncios internos.
"""
import argparse, glob, os, re, sys, unicodedata
from difflib import SequenceMatcher
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ler_json, gravar_json

DIRECAO = re.compile(r"^(n[ée]\??|ok\??|t[aá]\??|corta|de novo|vou (repetir|de novo)|[ée] isso\??|pode ser\??|gravando|valendo|"
                     r"peraí|espera|calma|deixa eu|pera|beleza\??|isso\??)[.!?]*$", re.I)
HESIT = re.compile(r"^(é+|hã+|ãh+|hum+|ah+|eh+|tipo)[.,]*$", re.I)


def norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    return re.sub(r"[^a-z0-9 ]", '', s)


def frases(doc):
    out, cur = [], []
    ws = doc['palavras']
    for i, w in enumerate(ws):
        if cur and (w['s'] - cur[-1]['e'] > 0.6): out.append(cur); cur = []
        cur.append(w)
        if re.search(r'[.!?]$', w['w']) and (i + 1 >= len(ws) or ws[i + 1]['s'] - w['e'] > 0.25): out.append(cur); cur = []
    if cur: out.append(cur)
    return out


def nota(ws):
    p = sum(w['p'] for w in ws) / len(ws)
    hes = sum(1 for w in ws if HESIT.match(w['w'].strip()))
    toks = [norm(w['w']) for w in ws]
    rep = sum(1 for i in range(1, len(toks)) if toks[i] and toks[i] == toks[i - 1])
    return round(p - 0.08 * hes - 0.1 * rep, 3)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pasta'); ap.add_argument('--out', default='edl.json'); ap.add_argument('--ordem')
    ap.add_argument('--sim', type=float, default=0.6)
    a = ap.parse_args()
    docs = sorted(glob.glob(os.path.join(a.pasta, '*.words.json')))
    if not docs: sys.exit('nenhum *.words.json — rode transcrever.py nos brutos antes')
    cands = []
    for di, d in enumerate(docs):
        doc = ler_json(d)
        for k, ws in enumerate(frases(doc)):
            texto = ' '.join(w['w'] for w in ws).strip()
            if DIRECAO.match(texto.strip()) or (len(ws) <= 2 and not re.search(r'[.!?]$', texto)): continue
            cands.append(dict(clip=doc['arquivo'], in_=max(0, ws[0]['s'] - 0.08), out=ws[-1]['e'] + 0.12, texto=texto,
                              nota=nota(ws), ordem=(di, k), n=norm(texto)))
    grupos = []
    for c in cands:
        for g in grupos:
            if SequenceMatcher(None, g[0]['n'].split(), c['n'].split()).ratio() >= a.sim: g.append(c); break
        else: grupos.append([c])
    edl = []
    for g in grupos:
        g.sort(key=lambda c: (c['nota'], c['ordem']), reverse=True)
        b = g[0]
        edl.append(dict(clip=b['clip'], **{'in': round(b['in_'], 3)}, out=round(b['out'], 3), texto=b['texto'], nota=b['nota'],
                        primeira=min(c['ordem'] for c in g), alternativas=[dict(clip=c['clip'], **{'in': round(c['in_'], 3)},
                        out=round(c['out'], 3), texto=c['texto'], nota=c['nota']) for c in g[1:]]))
    if a.ordem:
        rot = [norm(l) for l in open(a.ordem, encoding='utf-8') if l.strip()]
        def pos(it):
            sc = [SequenceMatcher(None, r.split(), norm(it['texto']).split()).ratio() for r in rot]
            return (sc.index(max(sc)) if sc and max(sc) > 0.3 else 999, it['primeira'])
        edl.sort(key=pos)
    else: edl.sort(key=lambda it: it['primeira'])
    for it in edl: it.pop('primeira')
    gravar_json(a.out, dict(segmentos=edl, obs='SUGESTÃO automática: revise takes, ordem e cortes antes do cortar.py'))
    dur = sum(it['out'] - it['in'] for it in edl)
    print(f'{len(cands)} frases em {len(docs)} brutos → {len(edl)} falas ({dur:.1f} s antes de apertar silêncios)')
    for i, it in enumerate(edl):
        alt = f'  (+{len(it["alternativas"])} takes)' if it['alternativas'] else ''
        print(f'{i:2d} {os.path.basename(it["clip"])[:16]:16s} {it["in"]:7.2f}–{it["out"]:7.2f} n={it["nota"]:.2f} {it["texto"][:70]}{alt}')
    print('→', a.out)


if __name__ == '__main__':
    main()
