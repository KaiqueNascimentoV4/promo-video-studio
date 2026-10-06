# ElevenLabs — guia prático (via MCP "creative_*")

## Sumário
1. Ferramentas e fluxo (flows, nodes, status, download)
2. Voz (TTS) — modelo, escolha de voz, tags, pronúncia, takes
3. Música — prompts por estrutura, armadilhas de duração
4. SFX — catálogo que funcionou
5. Imagens — personagem consistente, quando usar
6. Outros nodes úteis
7. Custos e saldo

---

## 1. Ferramentas e fluxo

- Carregue os schemas com `ToolSearch` antes de usar (são "deferred"): `creative_create_flow`, `creative_add_flow_node`, `creative_run_flow_nodes`, `creative_get_flow_run_status`, `creative_generate_speech`, `creative_list_voices`, `creative_get_model_schema`, `creative_get_model_guide`, `creative_attach_reference_file`, `creative_get_flow_node_types`.
- Crie **um flow por projeto** (`creative_create_flow`) e reutilize o `flow_id` — tudo fica organizado e o usuário pode abrir `https://elevenlabs.io/app/flows/<id>` para ouvir/comparar.
- Para parâmetros (duração, aspect ratio, instrumental): `creative_add_flow_node` com `model_parameters` + `creative_run_flow_nodes` (aceita `generations_count` 1–4). `creative_generate_speech` é atalho para TTS.
- O run retorna na hora; a geração roda em segundo plano. Para baixar: `creative_get_flow_run_status(flow_id, session_ids)` → `media[].master_url` (URL assinada, expira ~2 h). Baixe com `curl -s -o arquivo "<url>"` (aspas!) ou um `.py` com `urllib`. URLs muito longas: grave num script em vez de colar no shell.
- Sempre cheque `status` de cada geração: `failed` com `error_message: "Insufficient funds"` = sem saldo. Avise o usuário antes de apresentar opções.
- **Custo real (out/2026):** `creative_generate_in_flow` gera **4 versões por padrão** e não aceita `generations_count` — cada nó custa 4×. Referência medida: narração v4 de ~55 palavras = 390 créditos/versão (1.560 o nó); trilha 40 s = 900/versão (3.600 o nó); SFX ≈ 17/versão. O `credit_costs` devolvido na criação é uma reserva (≈2× o preço final). Quando o usuário pedir "com moderação": 1 nó de narração com o roteiro inteiro (corte em frases depois — ver `audio-mix.md`), 1 nó de trilha, poucos SFX, e avise o custo estimado antes.
- Em 06/10/2026 `creative_get_flow_run_status` voltou a funcionar (devolve `master_url` e preço). Teste-o primeiro; se falhar, use o export .zip do flow (abaixo).
- **Mudança de out/2026 (API do MCP):** `creative_run_flow_nodes`, `creative_generate_speech`, `creative_get_flow_run_status` e `creative_show_flow_results` passaram a devolver só "Error calling tool" (sem mensagem — NÃO é falta de saldo). O que funciona: `creative_generate_in_flow(flow_id, node_type, model_id, prompt, voice_id?)` — sem `generations_count` (gera 4 takes) e sem `model_parameters` (duração/instrumental vão no texto do prompt: "Instrumental only, no vocals. 30-second…"). Para baixar: peça ao usuário para exportar o flow como .zip na interface do ElevenLabs (vem 1 arquivo por nó, nomes "New tts node (N).mp3" na ordem de criação). Identifique as falas transcrevendo (`words.py`) e os SFX pela ordem de criação + duração/espectro. Teste primeiro esses tools antigos com uma chamada barata; se falharem, vá direto para este caminho.

## 2. Voz (TTS)

**Modelo**: `eleven_v4` (o mais natural; aceita audio tags e IPA). `eleven_v3` também aceita tags. `eleven_multilingual_v2` não aceita tags (lê colchetes em voz alta), soa mais "locutor robótico" e mais lento — evite para comerciais.

**Escolher voz** (`creative_list_voices`):
- Filtros que deram certo: `languages: ["pt"]` / `["es"]`, `voice_category: "high_quality"`, `sort: "usage_character_count_1y"`, `use_cases: ["advertisement","social_media","conversational"]`, `gender` se o usuário indicou.
- Perfil que funciona em comercial narrado por "colega": jovem, conversacional, carismático, não-locutor. Exemplos usados com sucesso:
  - PT-BR: **Will – Dynamic Voiceover** (`0YziWIrqiRTHCxeg1lyc`) ← aprovado; alternativas Kaique – Conversational (`Hmn4B9B77pf6ttydteJ8`), Raquel – Conversational (feminina, `GDzHdQOi6jjf8zaXhCYD`).
  - ES latino neutro: **Gerardo's cool Latin American voice** (`NDcVpQJv7Naa7ZKrqtEk`) ← aprovado; Diego Alez (energético, neutro). Argentino: Agustin – Conversational.
  - Narrador grave de documentário/true crime (PT-BR): **Nassif – Documentary, History & Thriller** (`acdKA5HckGxoxxvy40dA`) ← aprovado; com `[warmly]` vira caloroso na virada para o produto.
  - Elenco de "depoimentos" (PT-BR, idades variadas, aprovado): Bea (jovem, `cabLxBh81HurPAAJfEHo`), Kaique (homem ~40), Ariane (mulher meia-idade, `HA4HJL7riofv4HuNFvze`), Moutella (homem mais velho, `X3j2R63Qu4Gdv6dsU2hB`), Raquel 55 anos (`CS2gH5fPqUCmkVNpHsy4`), Jhenyfer (jovem, `P5sGFFRJfG9S2mevGUay`), Will. Tags que funcionaram: `[exhausted] [sighs]`, `[frustrated] … [groans]`, `[annoyed]`, `[resigned] … [chuckles]`, `[pained]`, `[exasperated]`.
  - IDs podem mudar — sempre confirme via `creative_list_voices`. Desde out/2026 o filtro `languages` dá erro: use `search` (ex. `"portuguese"` + `gender`) — retorna a biblioteca também.
- Para o usuário escolher: gere o **roteiro inteiro** em 2–3 vozes (1 take cada) e mostre uma tabela (voz, perfil, duração). Depois gere 2 takes da escolhida.

**Tags (v4/v3)** — curtas, antes do trecho, mudam só onde o tom muda:
`[curious]` abertura com gancho · `[pause]` antes do número-piada · `[flatly]` no punchline seco ("doze.") · `[chuckles]` após a piada · `[confident]` na virada para o produto · `[mischievously]` no callback · `[warmly]` no fechamento/tagline. Reticências (…) criam pausas naturais; CAIXA ALTA dá ênfase ("só não sabia ONDE").

**Pronúncia**: transcreva cada take (`scripts/words.py`). Nomes de marca que viram palavra comum (ex.: nome curto ouvido como palavra comum logo após "com o") — avise o usuário e, se confirmar, regenere só a frase com IPA entre barras (ex. `/ˈlumi/`) ou reescreva (ex.: "Com o [Marca]…" → "Com o [Marca], nada…" com pausa). "CRM" é lido como sigla corretamente.

**Duração**: v4 entrega ~2,7 palavras/s em PT e ES. Se ficar longa, prefira cortar texto. Último recurso: comprimir pausas >0,3 s para ~0,26 s (mantendo pausas cômicas) + `atempo=1.07` — ver `references/audio-mix.md`.

## 3. Música (`eleven_music_v2_5`)

Parâmetros: `duration_seconds`, `lyrics_type: "instrumental"`, `instrumental: true`.
Prompt = som, não imagem: gênero, BPM, instrumentos, energia **e a estrutura no tempo**. Exemplo que deu a trilha aprovada:

> Feel-good indie pop for a witty tech commercial at 110 BPM. Opens light and curious for the first 12 seconds: plucked pizzicato strings, soft ticking percussion and a teasing whistled motif, sparse so a voiceover sits on top. At 12 seconds the full groove kicks in: warm strummed acoustic guitar, crisp handclaps, bouncy bass, tambourine and glockenspiel accents, catchy whistled melody hook, optimistic and charming. Builds steadily, a short playful stop-time pause around 33 seconds, then a warm uplifting final chord with a bright little tag that rings out from 40 to 44 seconds. Instrumental, polished modern production.

Outras direções que valem como opções: bossa-pop brasileiro (violão nylon, Rhodes, shaker); minimal marimba/kalimba + felt piano (premium, estilo Apple/Notion); eletrônico punchy 120 BPM com impacto (kinetic/HUD curto); acoustic pop ukulele (leve, humor).

**Armadilhas**:
- A duração retornada varia (pedido 15 → 24/39 s; 30 → 51,6 s; 44 → 44 ou 66 s). Sempre rode `scripts/audio_profile.py` e decida: deslocar o início (`MUS_SHIFT`) para alinhar o groove ao momento da marca, cortar e emendar com o final (emenda em múltiplo de compasso: 4 beats = 240/BPM s), ou fade.
- Nem sempre segue a estrutura pedida (uma veio com 8 s de silêncio no meio). Gere **2 variações** e escolha pelo perfil de energia.
- Detecte BPM/fase com o script e alinhe cortes ao grid (beat = 60/BPM).

## 4. SFX (`eleven_text_to_sound_v2`)

`duration_seconds` 0,5–3, `prompt_influence: 0.6`, 1 geração cada. Catálogo usado:
- Soft airy whoosh transition, gentle and smooth (1 s) — cortes.
- Soft glassy UI pop, gentle bubble click (0,5 s) — cards/linhas aparecendo.
- Short quick felt-tip marker scribble on paper (0,8 s) — anotações à mão.
- Four quick soft laptop keyboard key presses + enter (1,6 s) — busca digitando / chat.
- Warm soft logo reveal, shimmering chime swell with soft low thump (3 s) — logo/card final.
- Para versões "agressivas" (kinetic escuro): fast cinematic whoosh; deep sub boom impact with shimmer; crisp digital UI tick.
Meça o pico de cada SFX (`audio_profile.py --sfx`) e posicione `t_evento − t_pico`.

## 5. Imagens (quando realmente precisar)

- Modelos: `gemini-3-pro-image` (Nano Banana Pro) para foto realista e **personagem consistente** com referência; `gpt-image-2` para UI/texto renderizado. Parâmetros: `aspect_ratio: "16:9"`, `resolution: "2K"` (4K se for dar zoom).
- Consistência: gere 1 foto-âncora (ex. time com a protagonista), escolha, `creative_attach_reference_file(url=master_url)` e conecte (`connect_from`) às demais gerações descrevendo "use the woman in the front center of the reference photo… same character".
- Peça "no readable text, no logos" e deixe áreas livres para anotações.
- **Atenção ao gosto**: o usuário reprovou o resultado com fotos de pessoas e pediu "sem imagens de pessoas". Pergunte antes de investir em imagens; prefira motion design. Se ele quiser fornecer fotos, entregue o briefing (modelo em `roteiro.md`).

## 6. Outros nodes

- `video-to-music` (`eleven_video_to_music_v1`): compõe trilha assistindo ao vídeo editado — bom para casar cortes, mas exige o vídeo no flow (upload via `creative_upload_flow_reference`, o usuário escolhe o arquivo no widget).
- `speech-to-text` (`eleven_scribe_v1`): transcrição; localmente `faster-whisper` (já instalado) é grátis e dá tempo por palavra.
- `voice-changer`, `dubbing-audio` (dublagem automática) — alternativa rápida para outra língua, mas roteiro adaptado + voz nativa soa melhor.

## 7. Custos de referência (créditos)

TTS v4 ~45 s: ~680–760 · Música 44–47 s: ~660–705 · SFX: 2–10 · Imagem Nano Banana Pro 2K: ~1.200 (sem ref) / ~1.800 (com ref).
Um comercial completo (2 takes de voz + 2 trilhas + SFX) ≈ 3.000 créditos; com 5 imagens 2K, +8.000.
