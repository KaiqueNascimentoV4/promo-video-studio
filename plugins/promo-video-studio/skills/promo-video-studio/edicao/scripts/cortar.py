"""Corta o EDL em planos: voz montada + vídeo mudo reenquadrado, com cor e ritmo.

  python cortar.py edl.json [--out trabalho/] [--formato 9:16] [--fps 30] [--look frio] [--lut x.cube --lut-mix .6]
                   [--batidas batidas.json] [--plano 1.9] [--zoom-fechado 1.3] [--sem-alternar] [--sem-soco]
                   [--trim trim.json] [--crf 16]

Gera em --out:  mudo.mp4 (sem áudio, bt709) · voz.wav (48 kHz estéreo) · cortes.json · mapa.json
O que faz:
 - Para cada segmento do EDL ({clip, in, out, [cx, cy, zoom, look]}) usa o <clip>.words.json (se existir) para apertar:
   começo = 1.ª palavra − 0,06 s (recuo de plosiva), fim = última + 0,05 s (≈ 0,11 s entre takes);
   pausas internas > 0,22 s viram 0,14 s.
 - Reenquadra para o formato ancorando a CABEÇA (detecção de rosto do OpenCV no meio do segmento; ou cx/cy do EDL).
 - Quebra em planos de ~--plano s nas fronteiras entre palavras (preferindo a batida mais próxima) e alterna
   aberto (zoom 1,0) ↔ fechado (--zoom-fechado), como duas câmeras. Cada take novo entra no enquadramento oposto.
 - Soco de escala de 3,6% em 7 quadros nos cortes que caem a ±70 ms de uma batida.
 - Cor: HLG/PQ → Rec.709 automático + look + LUT + trim por segmento (trim.json do cor.py --medir).
Vídeo e áudio são quantizados no mesmo quadro: sem deriva de sincronia.
"""
import argparse, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ffbin, probe, video_stream, rotacao, dims, ler_json, gravar_json
import cor

SR = 48000


def palavras_do_clip(clip):
    for p in (clip + '.words.json', os.path.splitext(clip)[0] + '.words.json'):
        if os.path.exists(p): return ler_json(p)['palavras']
    return None


def sub_trechos(seg, ws):
    """Intervalos (a, b) do clip a usar, com silêncios apertados, e as fronteiras entre palavras (para cortes de plano)."""
    a0, b0 = seg['in'], seg['out']
    if not ws: return [(a0, b0)], []
    dentro = [w for w in ws if w['e'] > a0 + 0.02 and w['s'] < b0 - 0.02]
    if not dentro: return [(a0, b0)], []
    rs, cur_a = [], max(a0 - 0.1, dentro[0]['s'] - 0.06)
    fronteiras = []
    for w1, w2 in zip(dentro, dentro[1:]):
        gap = w2['s'] - w1['e']
        if gap > 0.22:
            rs.append((cur_a, w1['e'] + 0.07)); cur_a = w2['s'] - 0.07
        else:
            fronteiras.append((w1['e'] + w2['s']) / 2)
    rs.append((cur_a, dentro[-1]['e'] + 0.05))
    return rs, fronteiras


def rosto(clip, t, w, h):
    """Centro (cx, cy) relativo da cabeça num quadro do clip; None se não achar.
    1) Haar do OpenCV (se a build tiver); 2) senão, maior mancha de tom de pele (YCrCb) nos 75% de cima."""
    import cv2
    sw, sh = 480, int(480 * h / w) // 2 * 2
    r = subprocess.run([ffbin(), '-v', 'error', '-ss', f'{t:.3f}', '-i', clip, '-frames:v', '1', '-vf', f'scale={sw}:{sh}',
                        '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
    if len(r.stdout) != sw * sh * 3: return None
    im = np.frombuffer(r.stdout, np.uint8).reshape(sh, sw, 3)
    if hasattr(cv2, 'CascadeClassifier'):
        det = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        fs = det.detectMultiScale(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), 1.1, 5, minSize=(sw // 14, sw // 14))
        if len(fs):
            x, y, fw, fh = max(fs, key=lambda f: f[2] * f[3])
            return (x + fw / 2) / sw, (y + fh / 2) / sh
    ycc = cv2.cvtColor(im, cv2.COLOR_BGR2YCrCb)
    m = ((ycc[..., 1] > 135) & (ycc[..., 1] < 180) & (ycc[..., 2] > 85) & (ycc[..., 2] < 135) & (ycc[..., 0] > 60)).astype(np.uint8)
    m[int(sh * 0.75):] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    if n <= 1: return None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    if st[k, cv2.CC_STAT_AREA] < sw * sh * 0.004: return None
    x, y, bw, bh = st[k, :4]
    return (x + bw / 2) / sw, (y + min(bh, bw * 1.3) / 2) / sh


def janela(sw, sh, W, H, z, cx, cy):
    """Recorte (x, y, cw, ch) no quadro fonte para o formato W×H com zoom z, rosto em (cx, cy)."""
    A = W / H
    if sw / sh > A: ch, cw = sh, sh * A
    else: cw, ch = sw, sw / A
    cw, ch = cw / z, ch / z
    x = min(max(cx * sw - cw / 2, 0), sw - cw)
    y = min(max(cy * sh - ch * 0.36, 0), sh - ch)
    ev = lambda v: int(round(v / 2) * 2)
    return ev(x), ev(y), ev(cw), ev(ch)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('edl'); ap.add_argument('--out', default='trabalho'); ap.add_argument('--formato', default='9:16')
    ap.add_argument('--fps', type=float, default=30); ap.add_argument('--look', default='frio'); ap.add_argument('--lut')
    ap.add_argument('--lut-mix', type=float, default=1.0); ap.add_argument('--batidas'); ap.add_argument('--plano', type=float, default=1.9)
    ap.add_argument('--zoom-fechado', type=float, default=1.3); ap.add_argument('--sem-alternar', action='store_true')
    ap.add_argument('--sem-soco', action='store_true'); ap.add_argument('--trim', default=None); ap.add_argument('--crf', type=int, default=16)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    W, H = dims(a.formato); FPS = a.fps
    edl = ler_json(a.edl); segs = edl['segmentos'] if isinstance(edl, dict) else edl
    trim_p = a.trim or os.path.join(a.out, 'trim.json')
    trim = ler_json(trim_p) if os.path.exists(trim_p) else {}
    beats = np.array(ler_json(a.batidas)['batidas']) if a.batidas else None

    # 1) peças: (seg, clip, a, b, zoom) em quadros de saída
    pecas, t_out, zoom_atual = [], 0.0, 1.0
    info_cache = {}
    for si, seg in enumerate(segs):
        clip = seg['clip']
        if clip not in info_cache:
            v = video_stream(probe(clip)); sw, sh = v['width'], v['height']
            if abs(rotacao(v)) in (90, 270): sw, sh = sh, sw
            info_cache[clip] = (sw, sh, cor.hdr_de(clip))
        sw, sh, hdr = info_cache[clip]
        rs, fronts = sub_trechos(seg, palavras_do_clip(clip))
        if 'cx' in seg: cx, cy = seg['cx'], seg.get('cy', 0.4)
        else:
            f = rosto(clip, (rs[0][0] + rs[-1][1]) / 2, sw, sh); cx, cy = f if f else (0.5, 0.4)
        if a.sem_alternar: zoom_atual = 1.0
        elif pecas: zoom_atual = 1.0 if pecas[-1]['z'] != 1.0 else a.zoom_fechado  # take novo = enquadramento oposto
        if 'zoom' in seg: zoom_atual = seg['zoom']
        inicio_plano = t_out
        for (ra, rb) in rs:
            # quebra o trecho em planos nas fronteiras de palavra
            pontos = [ra] + [f for f in fronts if ra < f < rb] + [rb]
            cur = ra
            for k, f in enumerate(pontos[1:-1], 1):
                dur_plano = (t_out + (f - cur)) - inicio_plano
                if a.sem_alternar or dur_plano < a.plano * 0.85: continue
                tf = t_out + (f - cur)
                if beats is not None and len(beats):
                    near = beats[np.argmin(np.abs(beats - tf))]
                    if abs(near - tf) > 0.25 and dur_plano < a.plano * 1.3: continue
                pecas.append(dict(seg=si, clip=clip, a=cur, b=f, z=zoom_atual, cx=cx, cy=cy, hdr=hdr, sw=sw, sh=sh))
                t_out += f - cur; cur = f
                zoom_atual = 1.0 if zoom_atual != 1.0 else a.zoom_fechado
                inicio_plano = t_out
            pecas.append(dict(seg=si, clip=clip, a=cur, b=rb, z=zoom_atual, cx=cx, cy=cy, hdr=hdr, sw=sw, sh=sh))
            t_out += rb - cur
    # quantiza em quadros
    acc = 0
    for p in pecas:
        n = max(1, int(round((p['b'] - p['a']) * FPS)))
        p['n'] = n; p['f0'] = acc; acc += n
        p['t0'] = round(p['f0'] / FPS, 4); p['t1'] = round((p['f0'] + n) / FPS, 4)
    total = acc
    # cortes = mudança de take ou de enquadramento (no quadro exato da peça)
    cortes = []
    for i, p in enumerate(pecas):
        if i == 0: continue
        q = pecas[i - 1]
        if q['seg'] != p['seg'] or q['z'] != p['z']:
            t = p['f0'] / FPS
            bat = bool(beats is not None and len(beats) and np.min(np.abs(beats - t)) <= 0.07)
            cortes.append(dict(t=round(t, 3), quadro=p['f0'], tipo='take' if q['seg'] != p['seg'] else 'plano', batida=bat))
            p['soco'] = bat and not a.sem_soco
    print(f'{len(segs)} segmentos → {len(pecas)} peças, {len(cortes)} cortes, {total} quadros ({total / FPS:.2f} s)')

    # 2) vídeo: cada peça decodificada pelo ffmpeg (recorte + cor) → numpy (soco) → um único encoder
    PW, PH = int(round(W * 1.04 / 2) * 2), int(round(H * 1.04 / 2) * 2)
    mudo = os.path.join(a.out, 'mudo.mp4')
    enc = subprocess.Popen([ffbin(), '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', f'{FPS}',
                            '-i', '-', '-c:v', 'libx264', '-crf', str(a.crf), '-preset', 'medium', '-pix_fmt', 'yuv420p',
                            '-vf', 'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv',
                            *cor.SAIDA_709, '-movflags', '+faststart', mudo], stdin=subprocess.PIPE)
    import cv2
    voz = []
    for i, p in enumerate(pecas):
        x, y, cw, ch = janela(p['sw'], p['sh'], W, H, p['z'], p['cx'], p['cy'])
        vf = ','.join(f for f in (f'crop={cw}:{ch}:{x}:{y}', cor.conversao(p['hdr']), f'scale={PW}:{PH}:flags=lanczos',
                                  cor.look(p.get('look') or a.look), cor.lut(a.lut, a.lut_mix), cor.trim_filtro(trim.get(str(p['seg']))),
                                  f'fps={FPS}', 'format=bgr24') if f)
        dur = p['n'] / FPS
        dec = subprocess.Popen([ffbin(), '-v', 'error', '-ss', f'{p["a"]:.4f}', '-i', p['clip'], '-t', f'{dur + 0.5:.4f}', '-an',
                                '-vf', vf, '-frames:v', str(p['n']), '-f', 'rawvideo', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tam, im = PW * PH * 3, None
        ox, oy = (PW - W) // 2, (PH - H) // 2
        for k in range(p['n']):  # streaming: nunca segura a peça inteira na memória
            buf = dec.stdout.read(tam)
            if len(buf) == tam: im = np.frombuffer(buf, np.uint8).reshape(PH, PW, 3)
            elif im is None: sys.exit(f'peça {i} não decodificou: {dec.stderr.read().decode(errors="ignore")[-400:]}')
            s = 1.0 + (0.036 * (1 - k / 7) if p.get('soco') and k < 7 else 0.0)
            if s == 1.0: out = im[oy:oy + H, ox:ox + W]   # 4% de margem: o soco não amplia além da fonte
            else:
                cw2, ch2 = PW / (1.04 * s), PH / (1.04 * s)
                x0, y0 = (PW - cw2) / 2, (PH - ch2) / 2
                M = np.float32([[W / cw2, 0, -x0 * W / cw2], [0, H / ch2, -y0 * H / ch2]])
                out = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR)
            enc.stdin.write(np.ascontiguousarray(out).tobytes())
        dec.stdout.close(); dec.wait()
        # áudio da peça, exatamente n/FPS
        ns = int(round(p['n'] / FPS * SR))
        ra = subprocess.run([ffbin(), '-v', 'error', '-ss', f'{p["a"]:.4f}', '-i', p['clip'], '-t', f'{dur + 0.2:.4f}', '-vn',
                             '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True)
        au = np.frombuffer(ra.stdout, np.float32).reshape(-1, 2)[:ns]
        if len(au) < ns: au = np.vstack([au, np.zeros((ns - len(au), 2), np.float32)])
        fade = min(240, ns // 4)
        if fade: au = au.copy(); au[:fade] *= np.linspace(0, 1, fade)[:, None]; au[-fade:] *= np.linspace(1, 0, fade)[:, None]
        voz.append(au)
        print(f'  peça {i + 1}/{len(pecas)} seg {p["seg"]} z{p["z"]:.2f}{" soco" if p.get("soco") else ""}  {p["t0"]:.2f}–{p["t1"]:.2f}', end='\r')
    enc.stdin.close(); enc.wait()
    print()
    voz = np.concatenate(voz)
    import wave
    vp = os.path.join(a.out, 'voz.wav')
    with wave.open(vp, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(voz, -1, 1) * 32767).astype('<i2').tobytes())
    gravar_json(os.path.join(a.out, 'cortes.json'), dict(fps=FPS, quadros=total, cortes=cortes))
    gravar_json(os.path.join(a.out, 'mapa.json'), dict(fps=FPS, formato=[W, H], quadros=total, pecas=[
        {k: p[k] for k in ('seg', 'clip', 'a', 'b', 'z', 'f0', 'n', 't0', 't1')} for p in pecas]))
    print(f'→ {mudo}  {vp}  ({total / FPS:.2f} s)  + cortes.json, mapa.json')


if __name__ == '__main__':
    main()
