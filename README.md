# Promo Video Studio

Skill do Claude Code para criar **vídeos promocionais de alto nível** sem editor de vídeo: roteiro, voz/trilha/efeitos no ElevenLabs, animação em HTML renderizada quadro a quadro, mixagem, QA e entregas (redes, outros idiomas, vertical, pacotes editáveis para **After Effects** e **Premiere**).

Formatos já testados e aprovados:
- **Comercial narrado (40–45 s)** com gancho de dado: o formato mais elogiado.
- **Paródia de programa de TV (50–57 s)**: depoimentos com filtro de gravação, depois a virada para o produto.
- **Personagem + apelidos**, no estilo dos comerciais da monday.com.
- **Kinetic/HUD curto**, sem narração.

## Instalar (uma vez)

No Claude Code (terminal ou app):

```
/plugin marketplace add KaiqueNascimentoV4/promo-video-studio
/plugin install promo-video-studio@promo-video-studio
```

Depois, para receber as melhorias automaticamente: **`/plugin` → Marketplaces → promo-video-studio → Enable auto-update**.
Sem auto-update, atualize quando quiser com `/plugin marketplace update promo-video-studio`.

A skill entra sozinha quando você pede um vídeo ("faz um vídeo de 30s para o produto X, essa é a landing"), ou chame com `/promo-video-studio:promo-video-studio`.

## O que precisa na máquina

- **Node.js** 18+ e, na pasta do projeto do vídeo, `npm i playwright-core`. O Chromium vem com `npx playwright install chromium`.
- **ffmpeg** no PATH, ou a variável `FFMPEG` apontando para o executável.
- **Python 3.10+** com `pip install faster-whisper numpy pillow`.
- **Conector do ElevenLabs** ligado no Claude, para voz, trilha e efeitos. A skill explica o caminho que funciona hoje na API, inclusive como baixar os áudios.
- Opcional: After Effects 2022+ ou Premiere, para os pacotes editáveis.

## Como a skill está organizada

```
plugins/promo-video-studio/skills/promo-video-studio/
  SKILL.md                 fluxo completo (briefing → roteiro → áudio → animação → render → mix → QA → entregas)
  references/              guias: elevenlabs, roteiro (formatos), animação, áudio/mix, entregas (AE/Premiere/redes/idiomas)
  scripts/                 render.mjs, words.py, audio_profile.py, analyze_reference.py, mix.py, compress.py,
                           premiere_package.py, ae_package.py, ae_sim.mjs, publicar.py
  assets/                  template.html (engine de animação), ae_export.js, anchors.example.js, fonte manuscrita
```

## Contribuir

A skill melhora a cada vídeo. Quando o Claude aprende algo que vale para os próximos (uma correção, uma técnica nova aprovada, uma mudança de API), ele atualiza a skill e publica com `python scripts/publicar.py "o que mudou"`. Quem tem permissão de escrita publica direto. Os demais clonam o repositório e abrem um pull request.

O repositório é **público**: nada de nomes de clientes, roteiros reais, dados de clientes, caminhos pessoais ou chaves. O `publicar.py` bloqueia tokens, e-mails e caminhos de usuário automaticamente.
