# Editar vídeo: fluxos da central única

Este guia reúne os fluxos de edição de vídeo curto: decupagem, legenda dinâmica, cor, SFX, trilha, motion de UI, motion livre e remake frame a frame. Faça o briefing e obtenha aprovação do plano antes de produzir.

Fluxo: **formulário da skill principal → modo → briefing do modo → (MIV + copy, se houver cliente) → ideias e plano temporal para aprovação → execução → QC → entrega.** As regras de aprovação do `../SKILL.md` prevalecem em todos os modos.

---

## 0. Gatilho

Quando o usuário pedir edição, use o formulário do `../SKILL.md`; entre aqui com o modo escolhido. Se o pedido já trouxer o modo e o briefing completos, avance diretamente para a análise do material.

Se o pedido já vier completo (por exemplo, "legenda esses 3 takes, 9:16, legenda dinâmica, sem música"), **pule as perguntas já respondidas**. Pergunte só o que falta.

Primeira vez nesta máquina? Rode `python scripts/config.py --check` (veja o §4). Ele diz onde estão o pack de SFX, as trilhas, as fontes e o ffmpeg. Se faltar algo, pergunte o caminho uma vez e salve com `config.py --set`.

---

## 1. Modos escolhidos no formulário principal

| modo | decupagem | legenda | cor | SFX | trilha | cenas de motion | arquivo de instruções |
|---|---|---|---|---|---|---|---|
| 1 · Reels completo | ✅ | ✅ dinâmica | ✅ | ✅ | ✅ | ✅ | `references/modo-1-reels-completo.md` |
| 2 · Reels intermediário | ✅ | ✅ dinâmica | ✅ | ✅ leve | ✅ | ❌ | `references/modo-2-reels-intermediario.md` |
| 3 · Decupagem + legenda | ✅ | ✅ | só correção técnica (HLG→709) | ❌ | ❌ | ❌ | `references/modo-3-decupagem-legenda.md` |
| 4 · Motion complexo | — | opcional | — | ✅ | ✅ | ✅ é o vídeo | `references/modo-4-motion-complexo.md` |
| 5 · Remake 1:1 | — | como a ref. | como a ref. | ✅ sintetizado | ✅ original | ✅ cópia exata | `references/modo-5-remake-1a1.md` + `assets/prompt-remake.md` |

**Depois da escolha, leia o arquivo do modo inteiro antes de continuar.** Cada um tem o briefing específico, o pipeline e o QC.

---

## 2. Briefing do modo (as perguntas mudam por modo)

O arquivo do modo diz quais perguntas fazer. O banco de perguntas está em `references/briefing.md`: textos e opções que podem ser apresentados pela ferramenta de perguntas disponível ou em mensagem. Em resumo:

- **Material**: onde estão os takes/arquivos (pasta ou arquivos arrastados). Modos 4 e 5: assets, logo, referência.
- **Formato**: 9:16 1080×1920 (padrão) · 4:5 · 1:1 · 16:9. **Duração-alvo.**
- **Legenda** (modos 1–4), sempre oferecendo a dinâmica:
  - *Dinâmica palavra a palavra* (padrão da casa): a linha se enche no tempo exato da fala, 1–3 palavras.
  - *Dinâmica com destaque*: a palavra ativa troca de cor ou escala, com blocos de ênfase e palavra gigante atrás da pessoa.
  - *Cinematográfica / 3D*: palavras no espaço, atrás da pessoa, câmera passando por elas.
  - *Simples*: frase limpa, sem animação.
  - Detalhes e como fazer cada uma: `references/legendas.md`.
- **Trilha**: pack próprio do time (config) · gerar (ElevenLabs, se conectado) · biblioteca livre com licença comercial · sem trilha.
- **Cliente/marca**: tem? Então §3 (MIV + copy).
- **CTA final**: botão "Chame no WhatsApp" animado (padrão para cliente) · link/perfil · nenhum.

Feche o briefing com ideias quando houver escolha criativa; espere o usuário escolher. Depois, mostre um **plano temporal para aprovação**: trechos e cortes propostos, texto/copy, cenas de motion, áudio/SFX, duração e entregas. Em motion livre, detalhe segundo a segundo. **Espere aprovação explícita antes de produzir.** No modo 5, confirme o custo antes da análise detalhada (§5) e depois aprove também o plano.

---

## 3. Cliente: MIV e copy

Sempre que o vídeo for para um cliente (modos 1, 2, 4, 5 e, se tiver CTA ou marca, o 3):

1. **Peça o MIV (Manual de Identidade Visual)**: PDF, imagens ou link. Se não houver MIV, peça logo (SVG/PNG), site e Instagram, e **derive a paleta do logo** (`scripts/paleta.py logo.png`). O que extrair e como virar tokens: `references/identidade-cliente.md`.
2. **Copy**: pergunte se já existe roteiro/copy ou se **a copy deve ser gerada pelo contexto do cliente**. Se for gerada, faça as perguntas de contexto de `references/copy.md` (o que vende, para quem, oferta, prova real, objeção, CTA, tom) e entregue 2–3 ganchos + a copy recomendada **para aprovação antes de produzir**.
3. **Nunca invente** número, depoimento, prêmio, prazo ou preço. O que não foi confirmado entra como `[ILUSTRATIVO]` e é listado na entrega. Já aconteceu de um agente inventar depoimento e contagem de seguidores, e isso teve de ser removido.

---

## 4. Ambiente e configuração local

`references/ambiente.md` traz instalação, ferramentas e armadilhas de Windows e de memória. Em resumo:
- Precisa de **ffmpeg** (com libass/zscale), **Python 3.10+** (`pip install faster-whisper numpy opencv-python pillow`) e **Node 18+** (`npm i playwright` + `npx playwright install chromium`) para motion/remake.
- Voz local: `python scripts/voz_local.py --instalar` (ambiente isolado `~/.venvs/voz` com PyTorch CUDA, Chatterbox e Kokoro).
- Opcionais que turbinam: skills HyperFrames (`npx hyperframes`), `rembg`/`npx hyperframes remove-background` (recorte da pessoa), Real-ESRGAN (upscale de material fraco), GPU NVIDIA para o Whisper.
- **Caminhos pessoais ficam fora do repo**. `scripts/config.py` usa `~/.claude/editar-video.json` por compatibilidade com instalações existentes; em qualquer agente, `PROMO_VIDEO_STUDIO_CONFIG` pode apontar para outro JSON local. Guarde ali pack de SFX, trilhas, fontes, LUTs, pasta de saída e WhatsApp padrão.

Scripts prontos (`scripts/`, rode com o caminho absoluto da skill; todos têm `--help`):

| script | faz |
|---|---|
| `config.py` | cria, mostra e confere a configuração local |
| `inventario.py PASTA` | ffprobe de todos os brutos: resolução, fps, duração, **HLG?**, rotação, áudio → `inventario.json` + tabela |
| `transcrever.py ARQ…` | faster-whisper com **tempo por palavra** (GPU se houver, VAD ligado) → `*.words.json` + texto |
| `decupar.py` | monta o EDL a partir da transcrição: acha takes repetidos, sugere o melhor e aperta silêncios → `edl.json` editável |
| `cortar.py edl.json` | corta, reenquadra para o formato e aplica a cor → `mudo.mp4` + `voz.wav` |
| `cor.py` | HLG→Rec.709, looks (frio/neutro/quente/PB), LUT `.cube`, medição de Y e R−B |
| `batidas.py MUSICA` | BPM, fase e grade de batidas, drop, arco de energia → `batidas.json` |
| `legendas.py words.json` | legenda `.ass` nos estilos dinâmico, destaque e simples, com a tipografia da casa |
| `sfx.py` | coloca SFX do pack nos tempos (cortes, pops de legenda, cenas), apara o ataque e aplica de-esser |
| `mixar.py mix.json` | voz (cadeia broadcast) + trilha com ducking + SFX → loudnorm −14/−12 LUFS, TP −1 |
| `montar.py` | queima a legenda, junta as camadas e o áudio → MP4 H.264 bt709 |
| `folha.py VIDEO` | folha de contato (1 q/s, tempos escolhidos ou cortes) para revisar de verdade |
| `cortes.py VIDEO` | detecta cortes por pico de diferença entre quadros (análise de referência) |
| `paleta.py IMG` | paleta dominante de um logo ou print → tokens hex |
| `voz_local.py` | **locução natural gerada no próprio PC** (Chatterbox Multilingual / Kokoro, GPU ou CPU, uso comercial liberado): `--roteiro` → um arquivo por fala + `locucao.wav` |
| `qc.py FINAL.mp4` | ffprobe, loudness e pico, quadros, cor bt709, cobertura de legenda, folha de QC |
| `publicar.py "msg"` | publica melhorias da skill no repo (bloqueia caminhos, e-mails, tokens e nomes de clientes) |

O kit de remake (`assets/remake-kit/`) traz engine de quadro, render, comparação, sync e encode. Veja o modo 5.

---

## 5. Modo 5: o aviso de custo (obrigatório)

Antes de qualquer análise, diga com estas palavras (pode adaptar o tom):

> ⚠️ O remake 1:1 é o modo mais caro: analisa a referência quadro a quadro, reconstrói cada plano em código com 4 agentes em paralelo mais 1 de áudio e renderiza tudo, em várias rodadas de comparação. Um filme de ~70 s levou horas de máquina e **muito token**. Para vídeos curtos ou quando "parecido" basta, o modo 4 (motion inspirado na referência) sai por uma fração do custo. Quer seguir com o 1:1?

Só depois do "sim" para o custo: peça a referência, o **MIV do cliente** e a decisão de copy (manter a estrutura da ref com o texto do cliente, ou gerar pelo contexto). Preencha o prompt de `assets/prompt-remake.md`, mostre a copy e o plano temporal para aprovação e só então execute por ele.

---

## 6. Regras da casa (valem para todos os modos)

Cada regra veio de uma correção real. Pular uma é repetir retrabalho.

**Tipografia**
- **Nunca** sombra, contorno ou glow na letra. Se o texto sumir, escureça o **fundo** (degradê ou blur atrás do bloco, sem borda).
- Entreletra **−0,07 em** (o "−70" dos plugins) na legenda e nos títulos. Rótulos em caixa alta pequena usam o contrário: entreletra larga (+0,30 em).
- Legenda corrida em sans **bold** (Helvetica Bold; livre: Inter/Arimo Bold), minúscula normal, **com pontuação**. Apoio editorial em serif romana (Playfair Display), SemiBold na palavra-chave.
- Proibido o layout "cinza pequeno em cima + palavra gigante embaixo + pontuação órfã".
- Nome composto e número de marca juntos e por extenso quando for nome ("Sete Mares", nunca "7 Mares").

**Legenda**
- **Toda fala tem legenda.** Nenhum trecho falado sem texto (o `qc.py` confere).
- Cada palavra entra no instante em que é falada; pedaços de 1–3 palavras; nenhum pedaço com menos de ~0,7 s na tela; altura fixa.
- Fora da interface do Instagram: nada nos 120 px do topo nem nos ~300 px de baixo (9:16).
- Legenda corrida nunca por cima de uma cena de motion que já escreve a frase.

**Cor**
- Bruto de iPhone costuma ser **HDR HLG** (bt2020/arib-std-b67): converta para Rec.709 **antes** de qualquer grade e marque bt709 na saída. Esse foi o erro mais grave já cometido ("cor horrível").
- Look padrão da casa: **frio/neutro, levemente azulado** (parede R−B ≈ −16), nada estourado, consistente entre takes. Se o MIV pedir quente, siga o MIV.

**Ritmo**
- Plano parado é pecado: planos de ~1,8–1,9 s (mín. 1,05 s), alternando aberto e fechado. Nos Reels, corte na fala e nas batidas da trilha; em motion de produto, corte na fala e na leitura.
- Silêncios: ~0,11 s entre takes; pausas internas > 0,22 s viram 0,14 s. Fora: voz sobreposta, conversa de direção ("né?", "ok?"), take com a pessoa fora de posição.
- Nunca cortar palavra no meio (recue ~40 ms antes de /t/, /p/, /k/). **Nunca congelar imagem**: take ruim vira câmera lenta com mistura de quadros.

**Motion**
- Entradas com ease (expo/cúbica). Overshoot (back-out) **só** em ícone, check, chip e pílula. Revelação por máscara, nada de crossfade.
- Nada rápido demais: palavras entram em 0,6–0,7 s. "Tudo muito rápido" é crítica recorrente.
- Motion blur real nas passagens (3 subamostras por quadro ou render a 120 fps + tmix).
- Palavra gigante atrás da pessoa (recorte) **só** com talking head limpo e bem iluminado. Em material de celular fraco ficou "super esquisito".
- Clientes: fecho com **CTA "Chame no WhatsApp"**, botão animado com toque e check.

**Áudio**
- Música **com arco** (cresce) e que **dure o vídeo todo**. Ducking da trilha sob a voz **desde o 1.º quadro** (voz ~6 dB acima da cama, inclusive no gancho).
- **De-esser em todo SFX**, não só na voz. SFX **audíveis**: o pico de cada evento acima do RMS da música (cerca de 4 LU abaixo da música, nunca 11). Um mix com os SFX a −11 LU fez o cliente dizer "não ouvi nenhum SFX".
- Proibidos: tique de contagem em número subindo (use um whoosh leve), "bop" suave de UI (use clique de obturador de câmera), pilha riser + sub + impacto no fecho (fecho = 1 whoosh suave + clique/pop).
- Voz: highpass ~80 Hz → compressão "broadcast" → presença 3–5 kHz → limiter. Loudness final **−14 LUFS** (−12 se pedirem "alto"), **TP ≤ −1 dB**. Aproveite o som direto/ambiente do take quando ajudar.
- Trilha: prefira o pack licenciado do time. Stock genérico costuma soar "barato" ("parecendo anime"). Nunca reutilize música ou voz de uma referência de terceiros.

**Entrega**
- Sempre `.mp4` H.264 (o player do Windows não abre ProRes). ProRes/projeto editável só se pedirem.
- Abra o vídeo para o usuário e diga **o que olhar, com minutagem**. Liste com honestidade o que ficou de fora ou é ilustrativo.
- Crítica em lote: trate **cada item** e confirme um a um no fim.
- Guarde a fonte do projeto (scripts, EDL, JSONs, HTML) ao lado da entrega, numa pasta `EDICAO_<PROJETO>/` com um `LEIA-ME.md`.

---

## 7. Arquivos de referência (leia sob demanda)

| arquivo | quando ler |
|---|---|
| `references/briefing.md` | sempre, logo depois da escolha do modo (banco de perguntas) |
| `references/modo-*.md` | o do modo escolhido, inteiro |
| `references/legendas.md` | toda legenda (estilos, medidas, libass, cobertura) |
| `references/cor.md` | modos 1–3 e footage dos modos 4–5 |
| `references/audio-sfx.md` | trilha, batidas, SFX, mix, loudness |
| `references/motion-vocabulario.md` | modos 1, 4, 5: cenas da casa, famílias de estilo, eases e durações medidos, transições |
| `references/motion-livre.md` | modo 4 e qualquer ideia fora do padrão: como conceber, qual engine, catálogo de ideias já feitas |
| `references/identidade-cliente.md` | quando houver MIV, logo ou cliente |
| `references/copy.md` | quando a copy for gerada pelo contexto |
| `references/qc-entrega.md` | antes de dizer "pronto" |
| `references/ambiente.md` | instalação e armadilhas |
| `assets/prompt-remake.md` | modo 5 (o prompt obrigatório) |

---

## 8. Como falar com o usuário

- Português, direto. Mensagens curtas a cada fase ("decupagem pronta: 14 falas, 38 s; agora a trilha").
- Muitas vezes ele está longe do computador: deixe a cadeia rodando até o fim e só chame quando houver algo para ver ou decidir.
- Mostre opções quando a escolha for de gosto (trilha, conceito, estilo de legenda). Decida sozinho quando for técnica.
- Nunca mostre arquivo velho como se fosse o novo. Se ainda está renderizando, diga.

## 9. Manutenção desta skill

Este guia vive em `plugins/promo-video-studio/skills/promo-video-studio/edicao/`. Quando aprender algo que vale para os próximos vídeos, generalize sem dados de cliente e siga o fluxo de contribuição do README do repositório. Fatos de um projeto específico ficam no `LEIA-ME.md` do projeto.
