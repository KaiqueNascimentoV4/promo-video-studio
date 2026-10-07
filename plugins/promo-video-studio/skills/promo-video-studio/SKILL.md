---
name: promo-video-studio
description: Produz vídeos de marketing/promo/comerciais de produto (motion design, tipografia cinética, telas de produto animadas, com ou sem fotos) renderizados de HTML via Chromium headless + ffmpeg, com narração, trilha, efeitos e imagens gerados no ElevenLabs. Use SEMPRE que o usuário pedir um vídeo promocional, comercial, anúncio, showreel, vídeo de lançamento, vídeo para Instagram/Reels/LinkedIn de um produto/sistema/empresa, "um vídeo nessa pegada" com uma referência (mp4, landing page, site), versão traduzida/dublada de um vídeo, roteiro de comercial, ou pacote editável para Premiere — mesmo que não diga "motion design" nem "ElevenLabs".
---

# Promo Video Studio

Pipeline para criar vídeos promocionais de alto nível (estilo comercial de SaaS: monday.com, Apple) sem editor de vídeo: cada quadro é renderizado de uma página HTML animada por código (determinística por tempo), e o áudio vem do ElevenLabs. Isso dá precisão de quadro, sincronia exata com a narração, e permite refazer qualquer coisa em minutos.

O que já foi produzido com este processo (use como régua de qualidade):
- **Kinetic/HUD 15s** (CRM de pós-venda): tipografia cinética, HUD, motion blur, trilha eletrônica sincronizada no beat.
- **Brand film 30s** (assistente de vendas com IA): identidade extraída da landing, esfera pontilhada animada, telas do produto.
- **Comercial narrado 45s** ("as palavras que se perdem", assistente de vendas com IA): roteiro com gancho de dado, narração ElevenLabs v4, motion design sem pessoas, versão PT e ES. ← o formato mais elogiado.

## Preparar o ambiente (uma vez por projeto)

- Pasta do projeto (ex. `Downloads/<Projeto>_src/`): `npm init -y && npm i playwright-core`. Chromium: usa o do Playwright (`npx playwright install chromium` se não houver) ou a variável `CHROME`.
- ffmpeg no PATH ou variável `FFMPEG` com o caminho (os scripts procuram em pastas comuns, mas definir é mais rápido).
- Python: `pip install faster-whisper numpy pillow` (transcrição local grátis, análise de áudio, grids de imagem).
- Copie `assets/template.html` → `projeto.html` e `assets/anchors.example.js` → `anchors.js`. Scripts em `scripts/` (rode com o caminho absoluto da skill).

## Visão geral do fluxo

1. **Briefing + referências** → entender produto, público, canal, duração, idioma.
2. **Análise da referência** (vídeo e/ou landing) → ritmo, estrutura, linguagem visual, identidade.
3. **Conceito + roteiro** → 2–3 ideias curtas, usuário escolhe; roteiro final com tempos.
4. **Áudio no ElevenLabs** → narração (2 takes), trilha (2 variações), SFX.
5. **Sincronia** → transcrever a narração com tempo por palavra → arquivo de âncoras.
6. **Animação HTML** → cenas amarradas às âncoras (template em `assets/template.html`).
7. **Stills de checagem** → revisar quadros-chave antes do render completo.
8. **Render + mix** → vídeo 1080p60 + mix com ducking, SFX, loudness −14 LUFS.
9. **QA** → contact sheet, transcrição do vídeo final, loudness/pico, estéreo.
10. **Entregas extras** (sob pedido) → versão comprimida p/ redes, outro idioma, vertical 9:16, pacote Premiere.

Mantenha o usuário informado em cada fase com frases curtas, e mostre opções (vozes, trilhas, conceitos) em vez de decidir tudo sozinho quando a escolha é de gosto.

## 1. Briefing (pergunte só o que faltar)

- Produto/empresa e o que ele resolve (1 frase). Público e canal (IG, LinkedIn, site, evento).
- Referência de estilo (vídeo, landing, site). Se houver landing, ela é a fonte da identidade e do copy.
- Duração. **Prefira 30–45s com narração** a 15s acelerado: o feedback recorrente foi "passou informação rápido demais". Texto na tela precisa ficar ≥ ~2,4 s para ser lido.
- Idioma(s). Com fotos de pessoas ou não (ver abaixo).
- **Voz**: ElevenLabs (pago por crédito) ou **voz local** (grátis, gerada no PC: `references/voz-local.md`)? Sem créditos ou sem conector, use a local.
- Créditos ElevenLabs disponíveis — cada narração ~700 créditos, cada trilha ~700, imagem Nano Banana Pro 2K ~1.200–1.800. Se uma geração falhar com "Insufficient funds", avise na hora; não deixe o usuário escolher uma opção que não existe.

## 2. Análise de referência

Rode `scripts/analyze_reference.py <video>` → gera contact sheets com timestamp (2 fps) e a transcrição da narração. Leia as folhas e extraia:
- **Estrutura narrativa** (ex. monday: apresenta personagem → problema com apelido engraçado → marca digitada numa busca → produto resolvendo com zoom na UI → payoff de apelidos → card preto com logo + CTA).
- **Linguagem visual**: paleta, tipografia, transições (whip com motion blur, flash, wipe), HUD, anotações à mão, zoom/câmera em UI.
- **Ritmo**: segundos por cena, quando entra a música, onde há pausa cômica.

Para **landing page** (HTML local ou URL): renderize com Playwright, troque para o idioma certo se houver seletor, extraia texto visível, variáveis CSS (`:root`), fontes, e imagens base64 (logos). Detalhes em `references/animacao.md` → "Extrair identidade".

## 3. Conceito e roteiro

Leia `references/roteiro.md`. Resumo:
- Ofereça **2–3 conceitos** em 3–4 linhas cada (gancho, visual, tom), recomende um, e escreva o roteiro completo só do recomendado. O usuário escolhe.
- Formatos que funcionaram: **gancho de dado** ("o cliente fala 5.000 palavras, você anota 12"), **personagem + apelidos** (estilo monday), **kinetic + HUD** (curtos, sem narração).
- **Menos texto na tela, mais narração.** A tela mostra produto e metáforas visuais; a voz conta. Textos de tela = rótulos curtos, números, anotações à mão.
- Fotos de pessoas geradas por IA dividiram opiniões (o usuário preferiu "sem imagens de pessoas"). Motion design + telas do produto é o padrão seguro; use fotos só se o usuário fornecer ou pedir. Se precisar de imagens dele, entregue um **briefing de imagens** (formato, protagonista consistente, área livre para anotações por foto) — modelo em `references/roteiro.md`.
- Feche com callback ao gancho + tagline da marca + CTA. Use o copy oficial da landing quando existir.
- Duração da fala: ~2,6–2,9 palavras/s em PT/ES com v4 (roteiro de ~115 palavras ≈ 41–45 s).

## 4. Áudio no ElevenLabs (ou voz local)

**Narração sem ElevenLabs:** `python scripts/voz_local.py --roteiro roteiro.txt --motor chatterbox --takes 2` gera a locução no próprio PC (Chatterbox Multilingual/Kokoro, uso comercial liberado). Instalação, parâmetros de emoção/ritmo e clonagem autorizada em `references/voz-local.md`. O resto do fluxo (âncoras, mix) é igual.


Leia `references/elevenlabs.md` antes de gerar. Essenciais:
- **Voz**: modelo `eleven_v4` (melhor; aceita tags `[warmly] [chuckles] [mischievously] [pause]`). Busque vozes com `creative_list_voices` (idioma, `voice_category: high_quality`, `sort: usage_character_count_1y`, use_cases advertisement/conversational). Gere 2 takes; para escolha de voz, gere o roteiro inteiro em 2–3 vozes e deixe o usuário ouvir.
- **Trilha**: `eleven_music_v2_5`, instrumental. Descreva a **estrutura no tempo** (intro contida até X s, groove entra em Y s, pausa em Z s, final que ressoa). O modelo **ignora a duração pedida** às vezes (veio 24, 39, 51, 58, 66 s) — sempre analise e edite (`scripts/audio_profile.py`).
- **SFX**: `eleven_text_to_sound_v2`, curtos (0,5–3 s): whoosh suave, pop de UI, rabisco de caneta, digitação, chime de logo.
- Baixe tudo localmente via as URLs `master_url` de `creative_get_flow_run_status` (expiram em ~2 h).
- Confira pronúncia transcrevendo cada take (`scripts/words.py`). Marca que soa como palavra comum (ex.: uma marca "Lume" ouvida como "lume", ou um nome curto engolido depois de "com o") deve ser sinalizada ao usuário.

## 5. Sincronia por âncoras

`python scripts/words.py narracao.mp3 --lang pt` → tempo de cada palavra. Monte um `anchors.js` com chaves semânticas (`gancho`, `cincomil`, `doze`, `memo1`, `crm`…) apontando para o início da palavra. Toda cena e animação usa `k('chave')` — assim trocar a voz/idioma só exige regenerar as âncoras. Para tradução, mantenha as **mesmas chaves** com tempos novos.

## 6. Animação HTML

Comece de `assets/template.html` (engine com helpers: whip com motion blur, máscara de texto, anotações à mão que se escrevem, setas desenhadas, câmera em UI, esfera pontilhada, contador, flash de corte). Regras em `references/animacao.md`. Pontos-chave:
- Tudo é função pura de `t` (`window.__render(t)`); nada de `setTimeout`/CSS animation. Isso torna o render determinístico.
- Identidade: cores como variáveis CSS, fontes do Google Fonts (as mesmas da marca), logo extraído da landing.
- Telas do produto: recrie em HTML/vetor (nítido em 1080p) com dados **fictícios** — não use dados reais de clientes/receita em material de marketing; screenshots via painel saem em baixa resolução.
- Cada cena: entra com algo em movimento nos primeiros 0,3 s, segura legível, sai antes do corte. Evite >1,5 s de quadro estático (o QA pegou "nuvem parada" e "balão vazio" — resolvido com zoom lento e "digitando •••").

## 7–8. Render, mix

```bash
node scripts/render.mjs --page cena.html --dur 45 --stills 1.2,4.0,6.9   # checagem
node scripts/render.mjs --page cena.html --dur 45 --out video_noaudio.mp4  # completo (~6 fps → 45 s ≈ 6–7 min)
python scripts/mix.py mix.json                                             # áudio + encode final
```
`render.mjs` encontra Chromium (Playwright) e ffmpeg sozinho; ver `--help`. Rode o render completo em background e acompanhe o log.
Mix (`references/audio-mix.md`): narração com offset ~0,35–0,4 s; trilha com **ducking por sidechain** sob a voz; alinhe o "drop" da música com o momento da marca (desloque o início da trilha); pausa cômica = corte de volume da música por ~1,5 s antes do punchline; SFX discretos com high-pass 900 Hz (rabiscos/pops em cima de palavras mascaram a fala — volume ~0,12–0,22); loudnorm −14 LUFS, pico ≤ −1 dBTP, **estéreo**, cor bt709 tv-range.

## 9. QA obrigatório antes de entregar

- Contact sheet 1 fps do vídeo final e olhe de verdade (texto cortado na borda, sobreposições, quadros vazios, layout quebrado em outro idioma).
- Transcreva o áudio final (`words.py --text`) e compare com o roteiro — pega SFX mascarando fala e música alta.
- `ffprobe`/ebur128: duração, ~−14 LUFS, pico ≤ −1 dB, estéreo, 1080p60.
Corrija e re-renderize; só então entregue com `SendUserFile` + resumo curto (o que tem em cada cena, o que precisa da atenção do usuário).

## 10. Entregas extras

Ver `references/entregas.md`:
- **Redes (<25 MB)**: `python scripts/compress.py video.mp4 --max-mb 24` (2 passes, 30 fps).
- **Outro idioma**: nova voz nativa + roteiro adaptado (não literal) + script de substituição de textos com `assert` de cada string + âncoras novas. Cheque glifos da fonte manuscrita (Gochi Hand desenha "¿" como "c") e frases mais longas.
- **Vertical 9:16**: reorganize cenas (não só crop).
- **Pacote Premiere editável**: camadas separadas (base, setas/desenhos com alpha, textos) + XML FCP7 com títulos editáveis, áudio separado e marcadores das falas — `scripts/premiere_package.py`.
- **Pacote After Effects editável** (preferido para motion): textos nativos animados, imagens nativas, base sem texto, áudio separado e camadas organizadas por cena — `assets/ae_export.js` + `scripts/ae_package.py`, validação com `scripts/ae_sim.mjs` (passo a passo em `references/entregas.md`).
- Sempre salve os fontes (HTML, âncoras, mix, áudios) numa pasta `*_src` em Downloads para refazer depois.

## Lições que valem ouro (do histórico real)

- Mostre opções de voz/trilha/conceito; o gosto do usuário manda e muda ("não estou gostando dessa direção" → novo conceito sem pessoas foi o maior acerto).
- Narração lenta (55 s para roteiro de 45) → comprimir pausas e acelerar ~7% funciona; melhor ainda: modelo v4 com tags.
- Trilha que "não ficou boa" costuma ser estilo genérico — ofereça 3 direções distintas (indie pop com assobio, bossa-pop, minimal marimba) e deixe ouvir.
- Repetir a marca no fim da narração ("[Marca]. [tagline]…") e mostrar logo + tagline + CTA em card limpo (preto ou cor da marca).
- Saldo do ElevenLabs acaba no meio — confira status de cada geração antes de apresentar opções.

## Manutenção da skill (repositório do time)

Esta skill vive no GitHub (`KaiqueNascimentoV4/promo-video-studio`, plugin marketplace) e o time recebe as mudanças por auto-update. Quando você aprender algo que vale para os próximos vídeos (um bug corrigido num script, uma API que mudou, uma técnica nova aprovada pelo usuário, uma preferência de gosto), **atualize a skill e publique**:
1. Edite os arquivos da skill (generalize: nada de nomes de clientes, roteiros reais, caminhos da sua máquina ou dados sensíveis — o repositório é público).
2. Rode `python scripts/publicar.py "mensagem curta do que mudou"` (na pasta da skill) — ele bloqueia tokens/caminhos/e-mails, valida, faz commit e push. Se você não tiver permissão de escrita no repositório, prepare as mudanças e sugira um pull request.
Mudanças pontuais de um projeto (cores, textos de um cliente) não entram na skill.
