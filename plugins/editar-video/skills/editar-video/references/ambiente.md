# Ambiente: instalação, configuração e armadilhas

## 1. Instalar (uma vez por máquina)
| o quê | como | para |
|---|---|---|
| ffmpeg ≥ 6 com libass, zscale, tonemap | Windows: `winget install Gyan.FFmpeg` (build full) · Mac: `brew install ffmpeg` | tudo |
| Python 3.10+ | `pip install faster-whisper numpy opencv-python pillow` | scripts |
| Node 18+ e Playwright | `npm i -g playwright` (ou na pasta do projeto) + `npx playwright install chromium` | motion HTML, remake |
| (opcional) HyperFrames | `npx hyperframes@latest doctor`; skills: `npx skills add heygen-com/hyperframes --agent claude-code` | motion HTML com GSAP, legendas embutidas, recorte |
| (opcional) recorte da pessoa | `pip install rembg onnxruntime` (sessão `u2net_human_seg`) ou `npx hyperframes remove-background` | modo 1 |
| (opcional) GPU NVIDIA para Whisper | `pip install nvidia-cudnn-cu12==8.9.7.29 nvidia-cublas-cu12==12.4.5.8` (o `transcrever.py` acha as DLLs sozinho) | transcrição ~10× mais rápida |
| (opcional) Real-ESRGAN / RIFE | binários ncnn-vulkan | upscale e interpolação de footage fraco |
| voz local (Chatterbox + Kokoro) | `python scripts/voz_local.py --instalar` → ambiente isolado `~/.venvs/voz` (Python 3.11, PyTorch CUDA, ~4 GB) | locução natural no PC, grátis, uso comercial |
| (opcional) edge-tts | `pip install edge-tts` | locução grátis pela nuvem da Microsoft |

`python scripts/config.py --check` confere tudo e diz o que falta.

## 2. Configuração local (`~/.claude/editar-video.json`, fora do repo)
```bash
python scripts/config.py --set sfx "D:/Packs/SFX"
python scripts/config.py --set trilhas "D:/Packs/Trilhas sonoras"
python scripts/config.py --set fontes "D:/Fontes"          # Helvetica, Playfair, Anton…
python scripts/config.py --set luts "D:/LUTs"
python scripts/config.py --set saida "D:/Entregas"
python scripts/config.py --set whatsapp_padrao "+55 11 9…"
python scripts/config.py --show
```
`sfx_mapa` (categoria → arquivo dentro do pack) é preenchido por `config.py --mapear-sfx`, que procura por nome ("whoosh", "swoosh", "impact", "click", "shutter", "correct", "type", "riser", "sub") e deixa você corrigir.
Fontes pagas (Helvetica, Neue Haas) **não vão no repo**. Cada pessoa aponta a sua pasta. Livres que substituem: Inter, Arimo (métrica da Arial/Helvetica), Playfair Display, Anton (Google Fonts).

## 3. Armadilhas conhecidas
**Máquina / memória (16 GB)**
- Nunca dois encodes 4K ao mesmo tempo; `-threads 2 -filter_complex_threads 2` nos passos pesados.
- Chromium fica lento em sessão longa (até ~7 s/quadro): renderize em blocos com reinício.
- Recorte (rembg) com cache por quadro e reinício em `MemoryError`; o `birefnet` estoura memória, o `isnet-general-use` sai pior que o `u2net_human_seg`.
- Upscale de fotos: limite a ~1400 px no cache quando rodar 3 processos (OOM).
- Encode rápido com GPU NVIDIA: `-c:v h264_nvenc -preset p5 -tune hq -rc vbr -cq 18 -b:v 0`.

**ffmpeg**
- `split` com saída não conectada falha: encadeie os filtros.
- `afir` pode devolver silêncio: convolução por FFT em numpy.
- HEIC não abre em várias builds: converta antes.
- Player padrão do Windows não abre ProRes (`apch`): entregue H.264.

**Whisper**
- Use `small`/`medium` multilíngue com `language="pt"`, **nunca** modelos `.en`.
- VAD ligado (sem ele, silêncio vira "a a a").
- Transcreva por take/trecho; um prompt de arquivo inteiro faz entrar em loop.
- Corte no envelope do áudio; os tempos do Whisper erram 50–150 ms.

**Shell / Windows**
- Heredoc do bash come barras invertidas: gere `.ass`, JSON e HTML com script Python ou com a ferramenta Write.
- Nunca ponha aspas duplas dentro de `style="..."` em HTML gerado.
- Caminhos com espaço: sempre entre aspas; prefira barras normais (`D:/Packs/SFX`).
- Fontes variáveis podem falhar em engines nativas: tenha as estáticas.

**HyperFrames** (se usar)
- Uma composição raiz por projeto: a camada da frente com alfa fica em outro projeto.
- `data-width/height` estáticos no HTML; nada de `Math.random`, `Date`, `repeat:-1`, animação CSS.
- Para PT: `transcribe --model small` com idioma, nunca `small.en`.
