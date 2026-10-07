# Áudio: voz, trilha, SFX e mix

O som é metade do vídeo. Os vídeos de lançamento que mais viralizaram foram os de SFX mais travado na imagem.

## 1. Voz
Cadeia padrão (equivalente ao fluxo de Premiere do time: Dynamic Processing "Broadcast" → Vocal Enhance → EQ paramétrico → Hard Limiter):
```
highpass=f=80, afftdn=nf=-25 (só se tiver ruído), acompressor=threshold=-18dB:ratio=3:attack=5:release=80:makeup=4,
equalizer=f=200:t=q:w=1:g=-2, equalizer=f=4000:t=q:w=1.2:g=3, deesser=i=0.4, alimiter=limit=0.89:level=0
```
- Áudio de WhatsApp/celular: denoise leve antes, sem exagero (voz "de lata").
- Som direto/ambiente do take ajuda (risada, ambiente de evento): mantenha baixo, por baixo da voz.
- Reverb "great hall" só em trecho P&B/virada: wet ≈ 0,40, RT60 ≈ 2 s; 0,90 estourou. Normalize o reverb pelo RMS relativo à voz, não pelo pico (o pico esmaga a cauda).
- `afir` do ffmpeg devolve silêncio em algumas builds: faça a convolução por FFT em numpy.

## 2. Trilha
**Escolha** (`batidas.py` mede cada candidata):
- **Arco positivo** (cresce ao longo do vídeo), **pulso claro**, agudo contido (não briga com a voz), grave presente.
- **Duração real ≥ duração do vídeo.** Cuidado com trilha que é um loop de 10 s.
- Pack licenciado do time primeiro (`config.py`: `trilhas`). Stock genérico soou "barato/parecendo anime". Gerada (ElevenLabs Music): descreva a **estrutura no tempo** ("intro contida até 3 s, groove em 4 s, pausa em 12 s, drop em 13,5 s, final que ressoa"); o modelo às vezes ignora a duração, então meça.
- Nunca use música de vídeo de referência de terceiros. Biblioteca livre: guarde URL + licença em `LICENCAS.txt`.

**Encaixe**:
- `batidas.py` dá BPM, fase, grade, drop e o arco (RMS por seção). Desloque o início da trilha para o **drop cair no momento-chave** (revelação do produto, palavra-herói, virada).
- Trilha abafada (lowpass ~800 Hz) até a virada e aberta nela: efeito de "porta abrindo".
- Pausa dramática: corte o volume da música ~1,5 s antes do punchline.
- Fim: a trilha termina **com** o vídeo (fade de 0,5–1 s ou num final natural), nunca cortada seca no meio da frase musical.

## 3. SFX
**Regra 1, audível**: o pico de cada evento **acima do RMS da música** (≈ 4 LU abaixo da música, não 11). Verifique evento por evento (`mixar.py --relatorio`).
**Regra 2, de-esser em todo SFX** (`deesser` + highcut suave ~9 kHz), não só na voz.
**Regra 3, apare o ataque**: arquivos de pack têm silêncio na frente; corte até o primeiro ponto acima de −42 dB, senão o som chega atrasado.
**Regra 4, densidade com critério**: efeito demais vira desenho animado. Um som por movimento importante.

| movimento | som (categoria do pack) | nível relativo |
|---|---|---|
| passagem de cena / cortina / whip | whoosh rápido | médio |
| entrada pesada (cena de virada) | whoosh grave (sub whoosh) | médio-baixo |
| palavra-herói assenta | impacto baixo | baixo (0,18) |
| corte para P&B | sub boom | médio |
| cartão/UI aparece, palavra de legenda-chave | **clique de obturador de câmera** (não "bop" suave) | médio |
| digitação / dígitos | digitação curta de celular | baixo |
| item de lista | clique de interface | baixo |
| check / concluído | "correct" curto | médio |
| número subindo | **whoosh leve** (nunca tique de contagem) | baixo |
| fecho / CTA | **1** whoosh suave + clique no toque (nada de riser + sub + impacto empilhados) | médio |

`sfx.py` monta o `sfx.json` a partir dos cortes, da legenda e da lista de cenas; categorias → arquivos via config (`sfx_mapa`). Sem pack: `sfx.py --sintetizar` gera whoosh, clique, pop e impacto em numpy (útil no remake, onde os SFX são sintetizados nos tempos da referência).

## 4. Mix (`mixar.py mix.json`)
- Voz no centro, trilha com **ducking por sidechain** sob a voz **desde o 1.º quadro** (voz ~6 dB acima da cama; no gancho também; num reel a voz ficou 1,4 dB abaixo da cama no gancho e a 1.ª frase ficou ininteligível).
- Ordem: voz (cadeia) → trilha (EQ cortando 2–4 kHz levemente + ducking) → SFX (de-esser) → soma → `loudnorm=I=-14:TP=-1:LRA=11` (duas passadas) → limiter.
- Alvo: **−14 LUFS integrado, TP ≤ −1 dB** (−12 se pedirem "mais alto", padrão antigo de Reels). Estéreo, 48 kHz, AAC 256k.
- Confira: `qc.py` mede I/TP; ouça o gancho, a virada e o fecho.

## 5. Locução gerada
**Padrão: voz local, no próprio PC** (`scripts/voz_local.py`), sem custo por geração, sem internet depois do 1.º download, uso comercial liberado:
| motor | quando | como |
|---|---|---|
| **Chatterbox Multilingual** (MIT) | o mais natural: entonação, respiração, emoção controlável; clona o timbre de uma referência de 6–15 s | `voz_local.py --roteiro roteiro.txt --motor chatterbox --emocao 0.5 --ritmo 0.5 --takes 2 [--referencia voz.wav]` |
| **Kokoro-82M** (Apache 2.0) | rápido, roda em CPU, vozes prontas pt-BR (`pf_dora` feminina, `pm_alex`/`pm_santa` masculinas) | `voz_local.py --roteiro roteiro.txt --motor kokoro --voz pm_alex` |

- Comercial/anúncio: `--emocao 0.7` e `--ritmo 0.4`. Narração calma/institucional: `--emocao 0.35 --ritmo 0.3`. Explicativo: 0,5/0,5.
- **Referência de voz** (clonar timbre) só com **autorização da pessoa** (o próprio cliente, o locutor contratado, você). Áudio limpo, sem música, 6–15 s, uma pessoa. Sem referência, o Chatterbox usa como semente a voz pronta do Kokoro (`--voz`).
- Gere **2 takes** por linha (`--takes 2`) e escolha ouvindo; mande 2 vozes diferentes para o usuário escolher na primeira vez.
- Números, siglas e marcas: escreva como se fala ("R$ 697" → "seiscentos e noventa e sete reais"; "CNPJ" → "cê ene pê jota").
- Depois: `transcrever.py locucao/locucao.wav` → tempos por palavra → legendas e âncoras de motion. Aplique a cadeia de voz no `mixar.py` como qualquer voz.
- Alternativas: ElevenLabs (se o conector estiver ligado; ótimo, mas pago por crédito) ou `edge-tts` (grátis, mas é nuvem da Microsoft e soa mais "assistente").
- Por linha: gere, apare o silêncio e encaixe no slot; estique no máximo 8% para caber (acima disso, reescreva a linha).
- Transcreva cada take gerado e compare com o roteiro: marca que soa como palavra comum precisa de grafia fonética.
