"""Legendas .ass com a tipografia da casa, a partir do words.json da VOZ MONTADA.

  python legendas.py voz.words.json [--estilo dinamica|destaque|simples] [--formato 9:16] [--out legenda.ass]
                     [--cor-destaque "#2F6BFF"] [--fonte "Helvetica"] [--tamanho 74] [--y 0.66] [--max-palavras 3]
                     [--pular "12.3-15.0,30-32"] [--srt legenda.srt] [--enfase enfase.json --out-enfase enfase.ass]

Estilos:
  dinamica  a linha se ENCHE palavra por palavra (cada palavra aparece no instante em que é falada; o layout da linha
            é fixo desde o início, nada recentraliza). Padrão da casa.
  destaque  igual, e a palavra ativa fica na --cor-destaque até a próxima entrar.
  simples   frase/pedaço inteiro, estático.
Regras aplicadas: sans bold, entreletra −0,07 em (\\fsp inline, compensando o tamanho real do libass), sem contorno/sombra,
pedaços de 1–3 palavras (≤ 16 caracteres no 9:16), quebra em pontuação/pausa > 0,25 s, nenhum pedaço < 0,7 s,
posição fora da interface do Instagram. --fundo: escurecimento desfocado atrás do pedaço (quando o fundo é claro). --pular = trechos em que uma cena de motion já escreve a frase.

Ênfase (--enfase): JSON [{"t0":s,"t1":s,"apoio":"…","chave":"…","fecho":"…"}] (ou "palavra":"x","n":1 no lugar de t0
= a n-ésima ocorrência da palavra na fala) → blocos de 3 linhas (serif romana / SemiBold na cor / fecho) com fundo
escurecido e desfocado atrás, sem borda.
"""
import argparse, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ler_json, dims, fontes_dir

FATOR = {'helvetica': 0.83, 'arial': 0.83, 'inter': 0.82, 'arimo': 0.83, 'playfair': 0.70, 'anton': 0.575}


def fator(fonte):
    return next((v for k, v in FATOR.items() if k in fonte.lower()), 0.83)


def fonte_padrao():
    d = fontes_dir()
    if d:
        nomes = ' '.join(os.listdir(d)).lower()
        for cand, fam in (('helvetica', 'Helvetica'), ('arimo', 'Arimo'), ('inter', 'Inter')):
            if cand in nomes: return fam
    return 'Arial'


def ass_cor(hexc, alpha=0):
    h = hexc.lstrip('#'); r, g, b = h[0:2], h[2:4], h[4:6]
    return f'&H{alpha:02X}{b}{g}{r}&'.upper()


def tc(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'


def esc(s):
    return s.replace('\\', '＼').replace('{', '(').replace('}', ')')


def pedacos(ws, maxp, maxc, pular):
    def pulado(w): return any(a <= (w['s'] + w['e']) / 2 <= b for a, b in pular)
    out, cur = [], []
    for i, w in enumerate(ws):
        if pulado(w):
            if cur: out.append(cur); cur = []
            continue
        if cur:
            txt = ' '.join(x['w'] for x in cur + [w])
            if len(cur) >= maxp or len(txt) > maxc or w['s'] - cur[-1]['e'] > 0.25: out.append(cur); cur = []
        cur.append(w)
        if re.search(r'[.!?…,;:]$', w['w']): out.append(cur); cur = []
    if cur: out.append(cur)
    # junta pedaços curtos demais (< 0,7 s até o próximo) quando cabe
    res = []
    for p in out:
        if res and (p[0]['s'] - res[-1][0]['s'] < 0.7) and len(' '.join(x['w'] for x in res[-1] + p)) <= maxc + 6 \
                and not re.search(r'[.!?…]$', res[-1][-1]['w']):
            res[-1] = res[-1] + p
        else: res.append(p)
    return res


def cabecalho(W, H, estilos):
    linhas = ['[Script Info]', 'ScriptType: v4.00+', f'PlayResX: {W}', f'PlayResY: {H}', 'WrapStyle: 2',
              'ScaledBorderAndShadow: yes', 'YCbCr Matrix: TV.709', '', '[V4+ Styles]',
              'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, '
              'Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding']
    linhas += estilos
    linhas += ['', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    return linhas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('words'); ap.add_argument('--estilo', default='dinamica', choices=['dinamica', 'destaque', 'simples'])
    ap.add_argument('--formato', default='9:16'); ap.add_argument('--out', default='legenda.ass')
    ap.add_argument('--cor-destaque', default='#2F6BFF'); ap.add_argument('--cor', default='#FFFFFF')
    ap.add_argument('--fonte'); ap.add_argument('--tamanho', type=float); ap.add_argument('--y', type=float)
    ap.add_argument('--max-palavras', type=int, default=3); ap.add_argument('--pular', default='')
    ap.add_argument('--srt'); ap.add_argument('--enfase'); ap.add_argument('--out-enfase', default='enfase.ass')
    ap.add_argument('--fonte-serif', default='Playfair Display')
    ap.add_argument('--fundo', action='store_true', help='escurece o fundo atrás de cada pedaço (degradê desfocado, sem borda na letra)')
    a = ap.parse_args()
    W, H = dims(a.formato); vertical = H > W
    fonte = a.fonte or fonte_padrao(); F = fator(fonte)
    tam = a.tamanho or (84 if vertical else 64)
    y = (a.y or (0.66 if vertical else 0.86)) * H
    maxc = 16 if vertical else 30
    fsp = -0.07 * tam * F
    pular = [tuple(map(float, r.split('-'))) for r in a.pular.split(',') if r.strip()]
    ws = ler_json(a.words)['palavras']
    ps = pedacos(ws, a.max_palavras, maxc, pular)
    branco, dest = ass_cor(a.cor), ass_cor(a.cor_destaque)
    est = [f'Style: Corrida,{fonte},{tam:.0f},{branco},{branco},&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1']
    ev = []
    lead = 1 / 30  # a leitura ganha da fala por 1 quadro
    for k, p in enumerate(ps):
        t0 = p[0]['s'] - lead
        nxt = ps[k + 1][0]['s'] - lead if k + 1 < len(ps) else None
        t1 = p[-1]['e'] + 0.3
        if nxt is not None and nxt - p[-1]['e'] < 0.6: t1 = nxt
        if t1 - t0 < 0.7: t1 = t0 + 0.7 if nxt is None else max(t1, min(nxt, t0 + 0.7))
        if nxt is not None: t1 = min(t1, nxt)
        pos = f'\\an5\\pos({W / 2:.0f},{y:.0f})\\fsp{fsp:.2f}\\bord0\\shad0'
        if a.estilo == 'simples':
            txt = esc(' '.join(w['w'] for w in p))
        else:
            partes = []
            for i, w in enumerate(p):
                ms = max(0, int(round((w['s'] - lead - t0) * 1000)))
                tag = f'\\alpha&HFF&\\t({ms},{ms + 90},\\alpha&H00&)' if ms > 0 else ''
                if a.estilo == 'destaque':
                    fim = int(round(((p[i + 1]['s'] - lead) if i + 1 < len(p) else t1) * 1000 - t0 * 1000))
                    tag += f'\\1c{dest}'
                    tag += f'\\t({fim},{fim + 60},\\1c{branco})' if i + 1 < len(p) else ''
                partes.append(('{' + tag + '}' if tag else '{\\alpha&H00&\\1c' + branco + '}') + esc(w['w']))
            txt = ' '.join(partes)
        if a.fundo:  # nunca contorno/sombra na letra: escurece o FUNDO atrás do bloco
            bw, bh = min(W * 0.92, len(' '.join(w['w'] for w in p)) * tam * F * 0.62 + tam * 1.6), tam * 2.1
            caixa = f'm 0 0 l {bw:.0f} 0 {bw:.0f} {bh:.0f} 0 {bh:.0f}'
            ev.append(f'Dialogue: 0,{tc(t0)},{tc(t1)},Corrida,,0,0,0,fundo,{{\\an5\\pos({W / 2:.0f},{y:.0f})\\p1\\bord0\\shad0\\blur{tam * 0.45:.0f}'
                      f'\\1c&H000000&\\1a&H90&}}{caixa}{{\\p0}}')
        ev.append(f'Dialogue: 1,{tc(t0)},{tc(t1)},Corrida,,0,0,0,,{{{pos}}}{txt}')
    for a_, b_ in pular: ev.append(f'Comment: 0,{tc(a_)},{tc(b_)},Corrida,,0,0,0,pular,(motion escreve o texto)')
    with open(a.out, 'w', encoding='utf-8-sig') as f: f.write('\n'.join(cabecalho(W, H, est) + ev) + '\n')
    print(f'{len(ps)} pedaços ({a.estilo}, {fonte} {tam:.0f}px, fsp {fsp:.2f}) → {a.out}')
    if a.srt:
        with open(a.srt, 'w', encoding='utf-8') as f:
            for k, p in enumerate(ps, 1):
                s = lambda t: f'{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}'
                f.write(f'{k}\n{s(p[0]["s"])} --> {s(p[-1]["e"] + 0.2)}\n{" ".join(w["w"] for w in p)}\n\n')
        print('→', a.srt)
    if a.enfase: enfase(a, ws, W, H, vertical)


def enfase(a, ws, W, H, vertical):
    blocos = ler_json(a.enfase)
    serif = a.fonte_serif; Fs = fator(serif)
    base = 96 if vertical else 80
    est = [f'Style: Apoio,{serif},{base * 0.54:.0f},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1',
           f'Style: Chave,{serif} SemiBold,{base * 1.9:.0f},{ass_cor(a.cor_destaque)},&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1',
           'Style: Fundo,Arial,10,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1']
    ev = []
    for b in blocos:
        if 'palavra' in b:
            occ = [w for w in ws if re.sub(r'\W', '', w['w'].lower()) == b['palavra'].lower()]
            t0 = occ[min(b.get('n', 1), len(occ)) - 1]['s'] if occ else 0
            t1 = b.get('t1', t0 + b.get('dur', 2.2))
        else: t0, t1 = b['t0'], b['t1']
        cy = H * (0.30 if vertical else 0.45)
        fsp = lambda sz, f: -0.07 * sz * f
        ap_, ch_, fe_ = base * 0.54, base * 1.9, base * 0.62
        bw, bh = W * 0.92, ap_ + ch_ + fe_ + 120
        caixa = f'm 0 0 l {bw:.0f} 0 {bw:.0f} {bh:.0f} 0 {bh:.0f}'
        ev.append(f'Dialogue: 0,{tc(t0)},{tc(t1)},Fundo,,0,0,0,,{{\\an7\\pos({(W - bw) / 2:.0f},{cy - bh / 2:.0f})\\p1\\bord0\\shad0\\blur36'
                  f'\\1c&H000000&\\1a&H70&\\fad(180,180)}}{caixa}{{\\p0}}')
        y1, y2, y3 = cy - ch_ / 2 - ap_ * 0.75, cy, cy + ch_ / 2 + fe_ * 0.75
        for st, txt, yy, sz, f in (('Apoio', b.get('apoio', ''), y1, ap_, Fs), ('Chave', b.get('chave', ''), y2, ch_, Fs),
                                   ('Apoio', b.get('fecho', ''), y3, fe_, Fs)):
            if txt:
                ev.append(f'Dialogue: 1,{tc(t0)},{tc(t1)},{st},,0,0,0,,{{\\an5\\pos({W / 2:.0f},{yy:.0f})\\fs{sz:.0f}\\fsp{fsp(sz, f):.2f}'
                          f'\\bord0\\shad0\\fad(220,160)}}{esc(txt)}')
    with open(a.out_enfase, 'w', encoding='utf-8-sig') as f: f.write('\n'.join(cabecalho(W, H, est) + ev) + '\n')
    print(f'{len(blocos)} blocos de ênfase → {a.out_enfase}')


if __name__ == '__main__':
    main()
