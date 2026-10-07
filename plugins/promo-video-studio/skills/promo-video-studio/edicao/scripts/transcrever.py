"""Transcrição com tempo por palavra (faster-whisper), GPU se houver, VAD ligado.

  python transcrever.py ARQUIVO... [--lang pt] [--modelo medium] [--glossario nomes.txt] [--cpu]

Para cada ARQUIVO gera ARQUIVO.words.json:
  {"arquivo", "idioma", "duracao", "palavras": [{"w","s","e","p"}], "segmentos": [{"s","e","texto"}]}
e imprime o texto com tempos. Glossário = um nome próprio/marca por linha: vira prompt inicial do Whisper e corrige
a grafia depois (sem diferenciar maiúsculas/acentos).
Regras: nunca modelos .en para português; VAD ligado (sem ele o silêncio vira "a a a").
"""
import argparse, glob, json, os, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import run, ffbin, gravar_json, cfg


def _dlls_nvidia():
    """No Windows, os wheels nvidia-cudnn/cublas instalam DLLs que o ctranslate2 não acha sozinho."""
    if os.name != 'nt': return
    import site
    for base in site.getsitepackages() + [site.getusersitepackages()]:
        for sub in ('nvidia/cudnn/bin', 'nvidia/cublas/bin'):
            d = os.path.join(base, sub)
            if os.path.isdir(d):
                os.add_dll_directory(d); os.environ['PATH'] = d + os.pathsep + os.environ.get('PATH', '')


def modelo(nome, cpu):
    from faster_whisper import WhisperModel
    if not cpu:
        try:
            _dlls_nvidia()
            m = WhisperModel(nome, device='cuda', compute_type='float16')
            return m, 'cuda'
        except Exception as e:
            print(f'(GPU indisponível: {str(e)[:90]} → CPU)')
    return WhisperModel(nome, device='cpu', compute_type='int8'), 'cpu'


def _norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')


def wav16(src, tmp):
    run([ffbin(), '-y', '-v', 'error', '-i', src, '-vn', '-ac', '1', '-ar', '16000', tmp])
    return tmp


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('arquivos', nargs='+'); ap.add_argument('--lang', default=cfg().get('idioma', 'pt'))
    ap.add_argument('--modelo', default='medium'); ap.add_argument('--glossario'); ap.add_argument('--cpu', action='store_true')
    a = ap.parse_args()
    arqs = [f for x in a.arquivos for f in (sorted(glob.glob(x)) or [x])]
    nomes = []
    if a.glossario:
        nomes = [l.strip() for l in open(a.glossario, encoding='utf-8') if l.strip() and not l.startswith('#')]
    gl = {_norm(n): n for n in nomes for _ in [0] if ' ' not in n}
    m, dev = modelo(a.modelo, a.cpu)
    print(f'modelo {a.modelo} em {dev}')
    for src in arqs:
        tmp = os.path.join(os.path.dirname(os.path.abspath(src)), '.' + os.path.basename(src) + '.16k.wav')
        wav16(src, tmp)
        try:
            segs, info = m.transcribe(tmp, language=a.lang, word_timestamps=True, vad_filter=True,
                                      vad_parameters=dict(min_silence_duration_ms=300), beam_size=5,
                                      condition_on_previous_text=False,
                                      initial_prompt=('Nomes: ' + ', '.join(nomes) + '.') if nomes else None)
            palavras, segmentos = [], []
            for sg in segs:
                segmentos.append(dict(s=round(sg.start, 3), e=round(sg.end, 3), texto=sg.text.strip()))
                for w in sg.words or []:
                    t = w.word.strip()
                    if not t: continue
                    core = t.strip('.,!?;:…"\'()')
                    if _norm(core) in gl: t = t.replace(core, gl[_norm(core)])
                    palavras.append(dict(w=t, s=round(w.start, 3), e=round(w.end, 3), p=round(w.probability, 3)))
        finally:
            try: os.remove(tmp)
            except OSError: pass
        out = src + '.words.json' if not src.endswith('.wav') else src[:-4] + '.words.json'
        gravar_json(out, dict(arquivo=os.path.abspath(src), idioma=a.lang, duracao=round(info.duration, 3),
                              palavras=palavras, segmentos=segmentos))
        print(f'\n== {os.path.basename(src)}  ({info.duration:.1f} s, {len(palavras)} palavras) → {os.path.basename(out)}')
        for sg in segmentos: print(f'  [{sg["s"]:7.2f}–{sg["e"]:7.2f}] {sg["texto"]}')


if __name__ == '__main__':
    main()
