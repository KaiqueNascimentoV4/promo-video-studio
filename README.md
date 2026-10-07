# Promo Video Studio

Skill única para **Claude Code e Codex** que cria e edita vídeos: briefing por formulário, conceito e roteiro para aprovação, edição de takes, legendas, cor, SFX, motion, render, mixagem, QA e pacotes editáveis para **After Effects** e **Premiere**.

Formatos já testados e aprovados:
- **Comercial narrado (40–45 s)** com gancho de dado: o formato mais elogiado.
- **Paródia de programa de TV (50–57 s)**: depoimentos com filtro de gravação, depois a virada para o produto.
- **Personagem + apelidos**, no estilo dos comerciais da monday.com.
- **Kinetic/HUD curto**, sem narração.

## Instalar no Claude Code

No Claude Code (terminal ou app):

```
/plugin marketplace add KaiqueNascimentoV4/promo-video-studio
/plugin install promo-video-studio@promo-video-studio
```

Depois, para receber as melhorias automaticamente: **`/plugin` → Marketplaces → promo-video-studio → Enable auto-update**.
Sem auto-update, atualize quando quiser com `/plugin marketplace update promo-video-studio`.

A skill entra sozinha quando você pede um vídeo ou edição, ou chame com `/promo-video-studio:promo-video-studio`.

## Instalar no Codex

O repositório contém o manifesto portátil em `plugins/promo-video-studio/plugin.json` e o catálogo em `.agents/plugins/marketplace.json`. No Codex CLI, adicione o marketplace com:

```text
codex plugin marketplace add KaiqueNascimentoV4/promo-video-studio
```

Depois, abra `/plugins`, selecione **Promo Video Studio** e instale. No app desktop, abra o catálogo de plugins após adicionar o marketplace e instale o mesmo plugin. Em uma conversa nova, peça um vídeo ou invoque `$promo-video-studio`.

Nos dois agentes, `editar video iniciar` abre o formulário de modos. O agente apresenta ideias e um roteiro/plano com tempos e **espera sua aprovação antes de produzir**.

## O que precisa na máquina

- **Node.js** 18+ e, na pasta do projeto do vídeo, `npm i playwright-core`. O Chromium vem com `npx playwright install chromium`.
- **ffmpeg** no PATH, ou a variável `FFMPEG` apontando para o executável.
- **Python 3.10+** com `pip install faster-whisper numpy pillow`.
- **Conector do ElevenLabs** quando quiser gerar voz, trilha ou efeitos por crédito. Voz local e packs de áudio são alternativas nos fluxos de edição.
- Opcional: After Effects 2022+ ou Premiere, para os pacotes editáveis.

## Como a skill está organizada

```
plugins/promo-video-studio/skills/promo-video-studio/
  SKILL.md                 formulário único, aprovação e fluxo de comerciais
  edicao/                  cinco modos de edição, referências, scripts e kit de remake
  references/              guias: elevenlabs, voz local (grátis, no PC), roteiro (formatos), animação, áudio/mix, entregas (AE/Premiere/redes/idiomas)
  scripts/                 render.mjs, words.py, audio_profile.py, analyze_reference.py, mix.py, compress.py,
                           premiere_package.py, ae_package.py, ae_sim.mjs, voz_local.py, publicar.py
  assets/                  template.html (engine de animação), ae_export.js, anchors.example.js, fonte manuscrita
```

## Modos de edição

Digite **`editar video iniciar`**. O formulário da mesma skill direciona para comercial do zero ou um dos cinco modos de edição:

| modo | o que entra |
|---|---|
| 1 · Reels completo | decupagem, legenda dinâmica, cor, SFX, trilha **e** cenas de motion (palavra atrás da pessoa, cartão de UI, CTA WhatsApp animado) |
| 2 · Reels intermediário | decupagem, legenda dinâmica, SFX, música e color grading |
| 3 · Decupagem + legenda | melhores takes no ritmo + legenda (voz limpa, sem trilha) |
| 4 · Motion complexo | vídeo 100% motion de qualquer ideia (kinetic, UI, 3D, explainer desenhado, HUD…) |
| 5 · Remake 1:1 | refaz um vídeo de referência quadro a quadro para um cliente (pede o MIV; gasta muito token; segue um prompt obrigatório) |

Também gera **locução natural no próprio PC** (Chatterbox Multilingual / Kokoro, uso comercial liberado), sem custo por geração.
Caminhos pessoais (pack de SFX, trilhas, fontes) ficam fora do repo. `scripts/config.py` usa `~/.claude/editar-video.json` por compatibilidade; em qualquer agente, `PROMO_VIDEO_STUDIO_CONFIG` pode apontar para outro arquivo local.
Estrutura: `plugins/promo-video-studio/skills/promo-video-studio/edicao/` → `GUIA.md` (guia dos modos), `references/` (um arquivo por modo + legenda,
cor, áudio, motion, MIV, copy, QC), `scripts/` (inventário, transcrição, decupagem, corte, cor, batidas, legenda, SFX, mix, montagem,
QC, voz local) e `assets/` (prompt de remake obrigatório + kit do motor de quadro).

## Contribuir

A skill melhora a cada vídeo. Quando surgir uma melhoria reutilizável, atualize a skill e valide a mudança. `python scripts/publicar.py "o que mudou"` faz commit e push; use esse script somente quando a publicação estiver autorizada. Quem não tiver permissão de escrita pode abrir um pull request.

O repositório é **público**: nada de nomes de clientes, roteiros reais, dados de clientes, caminhos pessoais ou chaves. O `publicar.py` bloqueia tokens, e-mails e caminhos de usuário automaticamente.
