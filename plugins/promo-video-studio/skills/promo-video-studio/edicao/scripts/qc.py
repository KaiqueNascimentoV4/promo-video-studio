"""QC automático do vídeo final (o olhar humano continua obrigatório: ver references/qc-entrega.md).

  python qc.py FINAL.mp4 [--words voz.words.json] [--ass legenda.ass ...] [--lufs -14] [--cor "#HEX"] [--folha qc_folha.jpg]

Confere: resolução/fps/quadros, bt709 nas 4 pontas, H.264 yuv420p, áudio AAC 48 kHz estéreo; loudness integrado e
true peak; cobertura de legenda (toda palavra falada dentro de um evento do ASS, ou de um trecho 'pular'); zona de
interface no 9:16 (legenda fora dos 120 px de cima e dos 300 px de baixo); cor da marca (menor ΔE encontrado em
quadros a 1 q/s); e gera a folha 1 q/s. Sai com código 1 se algo obrigatório falhar.
"""
import argparse, os, re, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ffbin, run, probe, video_stream, fps_de, ler_json

OK, FAIL, WARN = '✔', '✘', '⚠'


def t2s(t):
    h, m, s = t.split(':'); return int(h) * 3600 + int(m) * 60 + float(s)


def eventos_ass(p):
    ev = []
    for l in open(p, encoding='utf-8-sig'):
        m = re.match(r'(Dialogue|Comment):\s*\d+,([^,]+),([^,]+),([^,]*),[^,]*,\d+,\d+,\d+,([^,]*),(.*)', l.strip())
        if not m: continue
        tipo, a, b, st, efeito, txt = m.groups()
        if (tipo == 'Comment' and efeito != 'pular') or efeito == 'fundo': continue
        y = re.search(r'\\pos\(\s*[\d.]+\s*,\s*([\d.]+)\s*\)', txt)
        ev.append(dict(a=t2s(a), b=t2s(b), estilo=st, pular=tipo == 'Comment', y=float(y.group(1)) if y else None))
    return ev


def delta_e(video, hexc, dur):
    import cv2
    alvo = np.array([[[int(hexc[5:7], 16), int(hexc[3:5], 16), int(hexc[1:3], 16)]]], np.uint8)
    lab_a = cv2.cvtColor(alvo, cv2.COLOR_BGR2LAB)[0, 0].astype(np.float32); lab_a[0] *= 100 / 255; lab_a[1:] -= 128
    best = 1e9
    for t in np.arange(0.5, dur, 1.0):
        r = subprocess.run([ffbin(), '-v', 'error', '-ss', f'{t:.2f}', '-i', video, '-frames:v', '1', '-vf', 'scale=160:-2',
                            '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
        if not r.stdout: continue
        im = np.frombuffer(r.stdout, np.uint8).reshape(-1, 160, 3)
        lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32); lab[:, 0] *= 100 / 255; lab[:, 1:] -= 128
        best = min(best, float(np.sqrt(((lab - lab_a) ** 2).sum(1)).min()))
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video'); ap.add_argument('--words'); ap.add_argument('--ass', nargs='*', default=[])
    ap.add_argument('--lufs', type=float, default=-14); ap.add_argument('--cor'); ap.add_argument('--folha', default='qc_folha.jpg')
    a = ap.parse_args()
    falhas = 0
    def rel(ok, msg, obrig=True):
        nonlocal falhas
        print(f'{OK if ok else (FAIL if obrig else WARN)} {msg}'); falhas += (not ok) and obrig
    info = probe(a.video); v = video_stream(info); au = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
    dur = float(info['format']['duration']); fr = fps_de(v); W, H = v['width'], v['height']
    nb = int(v.get('nb_frames', 0) or 0)
    print(f'{os.path.basename(a.video)}: {W}x{H} @ {fr:.3f} fps, {dur:.2f} s, {nb} quadros')
    rel(v['codec_name'] == 'h264' and v.get('pix_fmt') == 'yuv420p', f'vídeo {v["codec_name"]} {v.get("pix_fmt")} (esperado h264 yuv420p)')
    cs = [v.get('color_primaries'), v.get('color_transfer'), v.get('color_space')]
    rel(all(c == 'bt709' for c in cs) and v.get('color_range') == 'tv', f'cor {cs} range {v.get("color_range")} (esperado bt709 ×3, tv)')
    if nb: rel(abs(nb - dur * fr) <= 2, f'quadros {nb} ≈ duração × fps ({dur * fr:.0f})')
    if au:
        rel(au['codec_name'] == 'aac' and int(au['sample_rate']) == 48000 and au['channels'] == 2,
            f'áudio {au["codec_name"]} {au["sample_rate"]} Hz {au["channels"]} canais (esperado AAC 48 kHz estéreo)')
        m = run([ffbin(), '-hide_banner', '-i', a.video, '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-']).stderr
        I = float(m[m.rfind('I:'):].split()[1]); TP = float(m[m.rfind('Peak:'):].split()[1])
        rel(abs(I - a.lufs) <= 1.0, f'loudness {I:.1f} LUFS (alvo {a.lufs})'); rel(TP <= -0.9, f'true peak {TP:.1f} dBTP (≤ −1)')
    else: rel(False, 'sem áudio', obrig=False)
    if a.ass:
        ev = [e for p in a.ass for e in eventos_ass(p)]
        if H > W:
            fora = [e for e in ev if e['y'] is not None and not e['pular'] and (e['y'] < 120 + 60 or e['y'] > H - 300)]
            rel(not fora, f'zona de interface 9:16: {len(fora)} eventos fora da área segura')
        # contraste: região da legenda clara demais no meio de cada evento → sugerir --fundo
        claros = []
        for e in [e for e in ev if not e['pular'] and e['y'] is not None][:80]:
            t = (e['a'] + e['b']) / 2; y0 = max(0, int(e['y'] - 0.03 * H))
            r = subprocess.run([ffbin(), '-v', 'error', '-ss', f'{t:.2f}', '-i', a.video, '-frames:v', '1', '-vf',
                                f'crop={int(W * 0.6)}:{int(0.06 * H)}:{int(W * 0.2)}:{y0},scale=64:16', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True)
            if r.stdout and np.percentile(np.frombuffer(r.stdout, np.uint8), 30) > 150: claros.append(round(t, 1))  # p30: ignora a própria letra branca
        rel(not claros, f'contraste da legenda: {len(claros)} trechos com fundo claro {claros[:8]} (use legendas.py --fundo)', obrig=False)
        if a.words:
            ws = ler_json(a.words)['palavras']
            faltam = [w for w in ws if not any(e['a'] <= (w['s'] + w['e']) / 2 <= e['b'] for e in ev)]
            rel(not faltam, f'cobertura de legenda: {len(ws) - len(faltam)}/{len(ws)} palavras cobertas')
            for w in faltam[:20]: print(f'     sem legenda: {w["s"]:7.2f}s "{w["w"]}"')
    if a.cor:
        de = delta_e(a.video, a.cor, dur)
        rel(de < 6, f'cor da marca {a.cor}: menor ΔE encontrado {de:.1f} (< 6 = a cor aparece fiel)', obrig=False)
    try:
        from folha import quadro, montar
        ts = list(np.arange(0.0, dur, 1.0))
        montar([quadro(a.video, t, 180) for t in ts], [f'{t:.0f}s' for t in ts], 8, a.folha)
    except Exception as e: print(WARN, 'folha não gerada:', e)
    print('QC OK' if not falhas else f'QC: {falhas} problema(s) obrigatório(s)')
    sys.exit(1 if falhas else 0)


if __name__ == '__main__':
    main()
