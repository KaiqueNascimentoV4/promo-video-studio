"""Locução natural gerada NO PRÓPRIO PC (GPU/CPU), sem API e sem custo por geração. Uso comercial liberado.

  python voz_local.py --texto "Frase única." [--out locucao/]
  python voz_local.py --roteiro roteiro.txt [--out locucao/]          uma fala por linha (vira um arquivo por linha)
      [--motor chatterbox|kokoro]        chatterbox (padrão): o mais natural, clona timbre de uma referência; GPU recomendada
                                         kokoro: leve e rápido (roda bem em CPU), vozes prontas pt-BR
      [--referencia voz.wav]             chatterbox: 6–15 s de UMA pessoa falando limpo (sem música) → clona o timbre.
                                         SÓ com autorização da pessoa dona da voz. Sem referência: usa uma voz pronta do
                                         Kokoro (--voz) como semente de timbre.
      [--voz pf_dora|pm_alex|pm_santa]   voz do Kokoro (f = feminina, m = masculina). Padrão pf_dora
      [--emocao 0.5]                     chatterbox exaggeration: 0,3 sóbrio · 0,5 natural · 0,7–0,9 empolgado (comercial)
      [--ritmo 0.5]                      chatterbox cfg_weight: menor = fala mais lenta e pausada (0,3 para narração calma)
      [--velocidade 1.0]                 kokoro speed
      [--takes 2] [--seed 7]             takes por linha para escolher (seeds diferentes)
      [--pausa 0.25]                     silêncio entre linhas no arquivo juntado
  python voz_local.py --instalar         cria o ambiente isolado (~/.venvs/voz) com torch CUDA + chatterbox + kokoro
  python voz_local.py --checar           confere ambiente, GPU e modelos

Saída em --out: linha_01_t1.wav … (48 kHz estéreo, silêncio aparado, pico −3 dB), locucao.wav (take 1 de cada linha
juntado), linhas.json [{linha, texto, arquivo, takes[], dur}]. Depois: transcrever.py locucao.wav → tempos por palavra.
Motores: Chatterbox Multilingual (Resemble AI, licença MIT; marca d'água inaudível "Perth" no áudio) e Kokoro-82M
(Apache 2.0). Rodam no ambiente ~/.venvs/voz (ou config voz_python) para não brigar com o Python principal.
"""
import argparse, json, os, re, subprocess, sys

VENV = os.path.expanduser('~/.venvs/voz')
VPY = os.path.join(VENV, 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(VENV, 'bin', 'python')
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass


def cfg_python():
    try:
        with open(os.path.expanduser('~/.claude/editar-video.json'), encoding='utf-8') as f: return json.load(f).get('voz_python') or VPY
    except Exception: return VPY


def instalar():
    import shutil
    uv = shutil.which('uv')
    if uv:
        run = lambda *c: subprocess.run(c, check=True)
        run(uv, 'venv', VENV, '--python', '3.11')
        run(uv, 'pip', 'install', '--python', VPY, 'torch==2.6.0', 'torchaudio==2.6.0', '--index-url', 'https://download.pytorch.org/whl/cu124')
        run(uv, 'pip', 'install', '--python', VPY, 'chatterbox-tts', 'kokoro', 'soundfile', 'misaki[en]', 'espeakng-loader', 'setuptools<81')  # perth (marca d'água) usa pkg_resources
    else:
        sys.exit('instale o uv (pip install uv) ou crie à mão: python3.11 -m venv ~/.venvs/voz; pip install torch==2.6.0 torchaudio==2.6.0 '
                 '--index-url https://download.pytorch.org/whl/cu124; pip install chatterbox-tts kokoro soundfile "misaki[en]" espeakng-loader "setuptools<81"')
    print('ambiente pronto:', VPY, '(sem GPU NVIDIA: troque o índice cu124 por cpu; o kokoro roda bem em CPU)')


# ------------------------------------------------------------------ dentro do ambiente de voz
def pos(x, sr):
    """mono float → aparar silêncio (−45 dB, 60 ms de folga), pico −3 dB, 48 kHz estéreo."""
    import numpy as np
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    env = np.abs(x); lim = 10 ** (-45 / 20) * max(env.max(), 1e-9)
    idx = np.nonzero(env > lim)[0]
    if len(idx): x = x[max(0, idx[0] - int(0.06 * sr)):idx[-1] + int(0.12 * sr)]
    x = x / max(np.abs(x).max(), 1e-9) * 10 ** (-3 / 20)
    if sr != 48000:
        n = int(round(len(x) * 48000 / sr)); x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
    return np.stack([x, x], 1)


def gerar(a):
    import numpy as np, soundfile as sf, torch
    linhas = [a.texto] if a.texto else [l.strip() for l in open(a.roteiro, encoding='utf-8') if l.strip() and not l.startswith('#')]
    os.makedirs(a.out, exist_ok=True)
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'motor {a.motor} em {dev}, {len(linhas)} linha(s) × {a.takes} take(s)')
    kpipe = None
    def kokoro(texto, seed):
        nonlocal kpipe
        from kokoro import KPipeline
        if kpipe is None: kpipe = KPipeline(lang_code='p', repo_id='hexgrad/Kokoro-82M', device=dev)
        torch.manual_seed(seed)
        partes = [aud.cpu().numpy() if hasattr(aud, 'cpu') else aud for _, _, aud in kpipe(texto, voice=a.voz, speed=a.velocidade)]
        return np.concatenate(partes), 24000
    ref = a.referencia
    if a.motor == 'chatterbox':
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        model = ChatterboxMultilingualTTS.from_pretrained(device=dev)
        if not ref:  # sem referência: semente de timbre pt-BR feita pelo Kokoro (frase neutra de ~8 s)
            ref = os.path.join(a.out, f'_semente_{a.voz}.wav')
            if not os.path.exists(ref):
                x, sr = kokoro('Olá! Hoje eu vou te mostrar, com calma e passo a passo, como isso funciona na prática. '
                               'É simples, rápido, e você vai entender tudo.', 1)
                sf.write(ref, x, sr)
    res = []
    for i, texto in enumerate(linhas, 1):
        takes = []
        for t in range(1, a.takes + 1):
            seed = a.seed + 101 * t
            if a.motor == 'chatterbox':
                torch.manual_seed(seed)
                wav = model.generate(texto, language_id='pt', audio_prompt_path=ref, exaggeration=a.emocao, cfg_weight=a.ritmo)
                x, sr = wav.squeeze(0).cpu().numpy(), model.sr
            else: x, sr = kokoro(texto, seed)
            p = os.path.join(a.out, f'linha_{i:02d}_t{t}.wav'); sf.write(p, pos(x, sr), 48000); takes.append(p)
        dur = sf.info(takes[0]).duration
        res.append(dict(linha=i, texto=texto, arquivo=takes[0], takes=takes, dur=round(dur, 3)))
        print(f'  {i:2d} {dur:5.2f}s  {texto[:70]}')
    pausa = np.zeros((int(a.pausa * 48000), 2), np.float32)
    junto = np.concatenate([np.concatenate([sf.read(r['arquivo'], dtype='float32')[0], pausa]) for r in res])
    sf.write(os.path.join(a.out, 'locucao.wav'), junto, 48000)
    json.dump(dict(motor=a.motor, voz=a.voz, referencia=a.referencia, emocao=a.emocao, ritmo=a.ritmo, linhas=res),
              open(os.path.join(a.out, 'linhas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('→', os.path.join(a.out, 'locucao.wav'), f'({len(junto) / 48000:.1f} s) + linhas.json')


def checar():
    import torch
    print('torch', torch.__version__, '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'não (CPU)')
    for m in ('chatterbox', 'kokoro', 'soundfile'):
        try: __import__(m); print('  ✔', m)
        except Exception as e: print('  ✘', m, str(e)[:80])


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--texto'); ap.add_argument('--roteiro'); ap.add_argument('--out', default='locucao')
    ap.add_argument('--motor', default='chatterbox', choices=['chatterbox', 'kokoro']); ap.add_argument('--referencia')
    ap.add_argument('--voz', default='pf_dora'); ap.add_argument('--emocao', type=float, default=0.5); ap.add_argument('--ritmo', type=float, default=0.5)
    ap.add_argument('--velocidade', type=float, default=1.0); ap.add_argument('--takes', type=int, default=1); ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--pausa', type=float, default=0.25); ap.add_argument('--instalar', action='store_true'); ap.add_argument('--checar', action='store_true')
    a = ap.parse_args()
    if a.instalar: instalar(); sys.exit()
    py = cfg_python()
    if os.path.abspath(sys.executable).lower() != os.path.abspath(py).lower():  # reexecuta dentro do ambiente de voz
        if not os.path.exists(py): sys.exit(f'ambiente de voz não encontrado ({py}). Rode: python {os.path.basename(__file__)} --instalar')
        sys.exit(subprocess.call([py, os.path.abspath(__file__)] + sys.argv[1:]))
    if a.checar: checar(); sys.exit()
    if not (a.texto or a.roteiro): ap.print_help(); sys.exit(1)
    gerar(a)
