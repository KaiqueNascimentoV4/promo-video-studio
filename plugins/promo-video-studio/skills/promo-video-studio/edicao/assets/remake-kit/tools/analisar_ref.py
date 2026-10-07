"""FASE 0 automática: prepara a referência e o esqueleto da SPEC (a medição fina continua sendo sua, com numpy).

  python tools/analisar_ref.py REF.mp4 [--sem-quadros] [--sem-audio] [--grupos 4] [--k 4.0]
  python tools/analisar_ref.py --so-project        (só regenera project.js a partir do project.json)

Faz: ffprobe (W, H, fps exato, nº de quadros) → project.json/js (VIEW_SCALE para caber em 1920 px) ·
copia a ref para ref/source.* · TODOS os quadros 0-based em ref/full/fNNNN.jpg (nativo, para MEDIR) e ref/half/
(metade, para comparar rápido) · ref/audio.wav · folhas 1 q/s em ref/sheets/ · cortes por pico de MAD + flashes +
quadros pretos → analysis/tracks/cortes.json · áudio: BPM/fase (fluxo espectral), loudness por seção, golpes de SFX
(onsets > 4 kHz), narração com tempo por palavra (faster-whisper, se instalado) → analysis/tracks/AUDIO_*.json +
analysis/spec/AUDIO.md · SPEC.md com a tabela de planos e as seções a preencher · divisão em N grupos contíguos
(analysis/spec/G1..GN.md). CONFIRME os cortes visualmente antes de dividir o trabalho.
"""
import argparse, glob, json, os, shutil, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _proj import ROOT, proj, salvar_proj, ff


def sh(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode: sys.exit(f'falhou: {" ".join(map(str, cmd))[:300]}\n{r.stderr[-1500:]}')
    return r


def probe(ref):
    js = json.loads(sh([ff('ffprobe'), '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries',
                        'stream=width,height,r_frame_rate,avg_frame_rate,nb_read_packets,nb_frames:format=duration', '-of', 'json', ref]).stdout)
    s = js['streams'][0]
    num, den = map(int, (s.get('r_frame_rate') or s['avg_frame_rate']).split('/'))
    n = int(s.get('nb_read_packets') or s.get('nb_frames') or round(float(js['format']['duration']) * num / den))
    return s['width'], s['height'], num, den, n, float(js['format']['duration'])


def folhas(total, fps, cols=6, linhas=5, w=320):
    """Folhas 1 q/s (30 s por folha) a partir de ref/half, com segundo e quadro em cada miniatura."""
    import cv2
    qs = [int(round(s * fps)) for s in range(int(total / fps) + 1) if int(round(s * fps)) < total]
    for k in range(0, len(qs), cols * linhas):
        tiles = []
        for f in qs[k:k + cols * linhas]:
            im = cv2.imread(os.path.join(ROOT, 'ref', 'half', f'f{f:04d}.jpg'))
            if im is None: continue
            im = cv2.resize(im, (w, int(w * im.shape[0] / im.shape[1])), interpolation=cv2.INTER_AREA)
            cv2.rectangle(im, (0, 0), (150, 20), (0, 0, 0), -1)
            cv2.putText(im, f'{f / fps:.0f}s f{f}', (3, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
            tiles.append(im)
        while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
        cv2.imwrite(os.path.join(ROOT, 'ref', 'sheets', f'sheet_{k // (cols * linhas):02d}.jpg'),
                    np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 85])


def lumas(ref):
    p = subprocess.Popen([ff(), '-v', 'error', '-i', ref, '-vf', 'scale=96:54:flags=area', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
    d = p.stdout.read(); p.wait()
    return np.frombuffer(d, np.uint8).reshape(-1, 54, 96).astype(np.float32)


def audio(ref, fps, total):
    wav = os.path.join(ROOT, 'ref', 'audio.wav')
    sh([ff(), '-y', '-v', 'error', '-i', ref, '-vn', '-ac', '2', '-ar', '48000', wav])
    r = subprocess.run([ff(), '-v', 'error', '-i', wav, '-ac', '1', '-ar', '22050', '-f', 'f32le', '-'], capture_output=True)
    x = np.frombuffer(r.stdout, np.float32); sr = 22050
    if not len(x): return None
    hop, n = 512, 2048; nfr = 1 + (len(x) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(nfr)[:, None]
    S = np.abs(np.fft.rfft(x[idx] * np.hanning(n), axis=1)); L = np.log1p(100 * S)
    flux = np.concatenate([[0], np.maximum(0, np.diff(L, axis=0)).sum(1)]); fl = flux - np.convolve(flux, np.ones(16) / 16, 'same'); fl = np.maximum(fl, 0)
    hf = np.concatenate([[0], np.maximum(0, np.diff(L[:, int(4000 / (sr / n)):], axis=0)).sum(1)])
    ofps = sr / hop
    ac = np.correlate(fl, fl, 'full')[len(fl) - 1:]; lags = np.arange(len(ac)); bpm = 60 * ofps / np.maximum(lags, 1)
    ok = (bpm >= 70) & (bpm <= 180); lag = int(lags[ok][np.argmax(ac[ok])]) if ok.any() else 0
    per = lag / ofps if lag else None
    beats = []
    if per:
        ph = max(np.linspace(0, per, 48, endpoint=False), key=lambda p: fl[np.clip((np.arange(p, len(x) / sr, per) * ofps).astype(int), 0, len(fl) - 1)].sum())
        beats = np.arange(ph, len(x) / sr, per)
    # golpes de SFX: picos de fluxo agudo acima de 3× a mediana local
    med = np.array([np.median(hf[max(0, i - 40):i + 40]) for i in range(0, len(hf))])
    hits = [i for i in range(1, len(hf) - 1) if hf[i] > 3 * med[i] + 1e-3 and hf[i] >= hf[i - 1] and hf[i] >= hf[i + 1]]
    hits_t = [round(i / ofps, 3) for i in hits]
    rms_f = [float(20 * np.log10(np.sqrt((x[int(f / fps * sr):int((f + 1) / fps * sr)] ** 2).mean() + 1e-12) + 1e-12)) for f in range(total)]
    T = os.path.join(ROOT, 'analysis', 'tracks'); os.makedirs(T, exist_ok=True)
    json.dump(dict(bpm=round(60 / per, 3) if per else None, periodo=per, batidas=[round(b, 4) for b in beats],
                   batidas_quadro=[int(round(b * fps)) for b in beats]), open(os.path.join(T, 'AUDIO_beats.json'), 'w'))
    json.dump(dict(t=hits_t, quadro=[int(round(t * fps)) for t in hits_t]), open(os.path.join(T, 'AUDIO_sfx.json'), 'w'))
    json.dump([round(v, 2) for v in rms_f], open(os.path.join(T, 'AUDIO_rms_per_frame.json'), 'w'))
    narr = []
    try:
        from faster_whisper import WhisperModel
        if os.name == 'nt':  # DLLs do cuDNN/cuBLAS instalados por pip não estão no PATH (sem isso o processo aborta)
            import site
            for base in site.getsitepackages() + [site.getusersitepackages()]:
                for sub in ('nvidia/cudnn/bin', 'nvidia/cublas/bin'):
                    d = os.path.join(base, sub)
                    if os.path.isdir(d): os.add_dll_directory(d); os.environ['PATH'] = d + os.pathsep + os.environ['PATH']
        try: m = WhisperModel('medium', device='cuda', compute_type='float16')
        except Exception: m = WhisperModel('small', device='cpu', compute_type='int8')
        segs, info = m.transcribe(wav, word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
        for sg in segs: narr.append(dict(s=round(sg.start, 3), e=round(sg.end, 3), texto=sg.text.strip(), idioma=info.language,
                                         palavras=[dict(w=w.word.strip(), s=round(w.start, 3), e=round(w.end, 3)) for w in sg.words or []]))
        json.dump(narr, open(os.path.join(T, 'AUDIO_narracao.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    except ImportError: print('(faster-whisper não instalado: narração não transcrita)')
    sec = int(len(rms_f) // 8) or 1
    arco = [round(float(np.mean(rms_f[i:i + sec])), 1) for i in range(0, len(rms_f), sec)]
    md = ['# AUDIO — medido (confira ouvindo)', '', f'- BPM ≈ **{round(60 / per, 2) if per else "?"}**, período {per and round(per, 4)} s, '
          f'{len(beats)} batidas (quadros em tracks/AUDIO_beats.json)', f'- arco de loudness (dBFS por oitavo do filme): {arco}',
          f'- {len(hits_t)} golpes agudos candidatos a SFX (tracks/AUDIO_sfx.json) — confirme e classifique (whoosh, clique, impacto…)',
          '- drop / quebras / silêncios / corte seco final: PREENCHER (ouvir + olhar AUDIO_rms_per_frame.json)', '', '## Narração', '']
    md += ['| linha | início | fim | texto |', '|---|---|---|---|'] + [f'| {i + 1} | {s["s"]} | {s["e"]} | {s["texto"]} |' for i, s in enumerate(narr)] if narr else ['(sem fala detectada)']
    md += ['', '- voz: tom/pitch e palavras por minuto: PREENCHER', '- **Nunca reutilize a música nem a voz da ref.**']
    open(os.path.join(ROOT, 'analysis', 'spec', 'AUDIO.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    return dict(bpm=round(60 / per, 2) if per else None, sfx=len(hits_t), narr=len(narr))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ref', nargs='?'); ap.add_argument('--sem-quadros', action='store_true'); ap.add_argument('--sem-audio', action='store_true')
    ap.add_argument('--grupos', type=int, default=4); ap.add_argument('--k', type=float, default=4.0); ap.add_argument('--so-project', action='store_true')
    a = ap.parse_args()
    if a.so_project: salvar_proj(proj()); print('project.js regenerado'); return
    if not a.ref: ap.print_help(); return
    for d in ('ref/full', 'ref/half', 'ref/sheets', 'analysis/spec', 'analysis/tracks', 'out', 'shots', 'audio'):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    src = os.path.join(ROOT, 'ref', 'source' + os.path.splitext(a.ref)[1].lower())
    if os.path.abspath(a.ref) != os.path.abspath(src): shutil.copyfile(a.ref, src)
    W, H, num, den, total, dur = probe(src); fps = num / den
    p = proj(); p.update(W=W, H=H, FPS_NUM=num, FPS_DEN=den, TOTAL=total, VIEW_SCALE=round(min(1.0, 1920 / max(W, H)), 6))
    salvar_proj(p)
    print(f'REF {W}x{H} @ {num}/{den} ({fps:.3f} fps), {total} quadros, {dur:.3f} s → project.json (VIEW_SCALE {p["VIEW_SCALE"]})')
    if not a.sem_quadros:
        for g in glob.glob(os.path.join(ROOT, 'ref', 'full', '*.jpg')) + glob.glob(os.path.join(ROOT, 'ref', 'half', '*.jpg')): os.remove(g)
        sh([ff(), '-v', 'error', '-i', src, '-start_number', '0', '-q:v', '2', '-fps_mode', 'passthrough', os.path.join(ROOT, 'ref', 'full', 'f%04d.jpg')])
        sh([ff(), '-v', 'error', '-i', src, '-start_number', '0', '-q:v', '3', '-fps_mode', 'passthrough', '-vf', 'scale=iw/2:-2',
            os.path.join(ROOT, 'ref', 'half', 'f%04d.jpg')])
        n = len(glob.glob(os.path.join(ROOT, 'ref', 'full', '*.jpg')))
        print(f'{n} quadros extraídos (ref/full nativo, ref/half)')
        if n != total: print(f'⚠ ffprobe disse {total} quadros, extraí {n}: usando {n}'); p['TOTAL'] = n; salvar_proj(p); total = n
        folhas(total, fps)
    L = lumas(src)
    mad = np.concatenate([[0], np.abs(np.diff(L, axis=0)).mean((1, 2))])
    med = np.array([np.median(mad[max(0, i - 15):i + 16]) for i in range(len(mad))]); lim = np.maximum(12, a.k * med)
    cortes = [i for i in range(1, len(mad)) if mad[i] > lim[i] and mad[i] >= mad[i - 1] and mad[i] >= mad[min(len(mad) - 1, i + 1)]]
    media = L.mean((1, 2)); flashes = [i for i in range(len(media)) if media[i] > 235 and (i == 0 or media[i - 1] < 200)]
    pretos = [i for i in range(len(media)) if media[i] < 8]
    ini = [0] + cortes; fim = [c - 1 for c in cortes] + [len(L) - 1]
    planos = [dict(id=f'S{i + 1:02d}', f0=s, f1=e) for i, (s, e) in enumerate(zip(ini, fim))]
    json.dump(dict(fps=fps, quadros=len(L), mad=mad.round(2).tolist(), cortes=cortes, flashes=flashes, pretos=pretos, planos=planos),
              open(os.path.join(ROOT, 'analysis', 'tracks', 'cortes.json'), 'w'))
    print(f'{len(cortes)} cortes candidatos, {len(flashes)} flashes, {len(pretos)} quadros pretos → analysis/tracks/cortes.json')
    au = None if a.sem_audio else audio(src, fps, len(L))
    if au: print(f'áudio: BPM {au["bpm"]}, {au["sfx"]} golpes de SFX, {au["narr"]} linhas de narração → analysis/spec/AUDIO.md')
    # grupos contíguos equilibrados por número de quadros
    alvo = len(L) / a.grupos; grupos, cur, acc = [], [], 0
    for pl in planos:
        cur.append(pl); acc += pl['f1'] - pl['f0'] + 1
        if acc >= alvo * (len(grupos) + 1) and len(grupos) < a.grupos - 1: grupos.append(cur); cur = []
    if cur: grupos.append(cur)
    tab = ['| shot | f0–f1 | dur (s) | grupo | conteúdo | transição entra / sai |', '|---|---|---|---|---|---|']
    for gi, g in enumerate(grupos, 1):
        for pl in g: tab.append(f'| {pl["id"]} | {pl["f0"]}–{pl["f1"]} | {(pl["f1"] - pl["f0"] + 1) / fps:.2f} | G{gi} | PREENCHER | corte / corte |')
        gs = [f'# G{gi} — {g[0]["id"]}…{g[-1]["id"]} (f{g[0]["f0"]}–f{g[-1]["f1"]})', '',
              'Para cada shot: conteúdo, componentes, texto literal, tokens de cor amostrados, tamanhos (altura de caixa-alta),',
              'quadros-chave de câmera, caminho do cursor (ponta xy por quadro), cadência de digitação, blur, transições.',
              'Trilhas por quadro → analysis/tracks/G' + str(gi) + '_*.json (arrays medidos com numpy em ref/full).', '']
        gs += [f'## {pl["id"]} f{pl["f0"]}–f{pl["f1"]}\n\nPREENCHER\n' for pl in g]
        open(os.path.join(ROOT, 'analysis', 'spec', f'G{gi}.md'), 'w', encoding='utf-8').write('\n'.join(gs))
    spec = ['# SPEC — referência', '', f'REF: ref/source{os.path.splitext(src)[1]} · {W}×{H} · {num}/{den} fps · {len(L)} quadros (0-based) · {dur:.3f} s', '',
            '> A prosa é guia; **ref/full é a verdade**. Meça com numpy (tools/medir.py), nunca no olho.', '',
            '## Tabela de planos (cortes CANDIDATOS — confirme em ref/sheets e nos quadros vizinhos)', ''] + tab + ['',
            f'Flashes (quadro branco): {flashes}', f'Quadros pretos: {pretos}', '',
            '## Gramática visual', '', 'PREENCHER: tipografia (família, peso, entreletra), grade, texturas (scanline, grão, DOF), blur, cursor.', '',
            '## Inventário de componentes', '', 'PREENCHER: cartões, janelas, cursor, logo, HUD, contadores… (um só por componente compartilhado).', '',
            '## Texto na tela (literal, na ordem)', '', 'PREENCHER', '', '## Tokens de cor (amostrados nos pixels)', '',
            '| token | hex | onde (quadro, xy) |', '|---|---|---|', '', '## Áudio', '', 'Ver analysis/spec/AUDIO.md.', '',
            f'## Grupos para os agentes', ''] + [f'- **G{gi}**: {g[0]["id"]}–{g[-1]["id"]} (f{g[0]["f0"]}–f{g[-1]["f1"]}) → analysis/spec/G{gi}.md' for gi, g in enumerate(grupos, 1)]
    open(os.path.join(ROOT, 'SPEC.md'), 'w', encoding='utf-8').write('\n'.join(spec) + '\n')
    print(f'SPEC.md + analysis/spec/G1..G{len(grupos)}.md escritos ({len(planos)} planos). Próximo: confirmar cortes, medir, preencher.')


if __name__ == '__main__':
    main()
