# Modo 4: só motion complexo (qualquer ideia)

Vídeo **100% motion**, sem takes de câmera como base: kinetic typography, UI de app/SaaS, explainer desenhado, objetos 3D, HUD, colagem, mapa, dado virando objeto, ou uma ideia que ninguém fez ainda. Pode ter locução (gravada, TTS ou áudio de WhatsApp do cliente), só trilha + texto, ou fotos/vídeos do cliente como material dentro do motion.

**A ideia pode ser qualquer uma.** As famílias e receitas de `motion-vocabulario.md` são o ponto de partida medido, não uma cerca. `motion-livre.md` explica como conceber uma ideia nova e escolher a engine.

## 1. Briefing da ideia (texto livre, numerado, numa mensagem)
1. **Objetivo e canal**: vender o quê, para quem, onde vai rodar (Reels, X, LinkedIn, site, evento)?
2. **A ideia**: o usuário já tem uma ("explainer desenhado do painel", "estilo Apple", "HUD de vistoria")? Se não, vou propor 2–3.
3. **Referências**: links ou vídeos de estilo (X, YouTube, Instagram) e prints que ele goste.
4. **Áudio**: tem locução? (arquivo/áudio de WhatsApp · gerar TTS · sem voz, só trilha)
5. **Material do cliente**: logo/MIV, prints ou gravação do produto, fotos, vídeos.
6. **Copy**: pronta ou gerar pelo contexto (`copy.md`)?

Depois, pergunte B (formato/duração), D (trilha + SFX), E (CTA) e C se houver fala, pela ferramenta de perguntas disponível ou em texto.

## 2. Conceito antes de animar
- Proponha **2–3 conceitos** em 3–4 linhas cada (gancho dos primeiros 2 s, mundo visual, movimento-assinatura, o momento "espera, ele faz isso?"), **recomende um** e espere a escolha.
- Após a escolha, apresente o roteiro de cenas **segundo a segundo** (texto, movimento, locução, trilha e SFX). Espere a aprovação explícita desse roteiro antes da primeira geração ou animação.
- Lançamento ou produto: use o playbook de `motion-vocabulario.md` §5 (gancho ≤ 4 s, primeiro movimento ≤ 0,8 s, um momento único com 25–35% do tempo terminando num número real, fecho ≥ 2 s parado).
- Diferencie: "o que faria alguém dizer *isso não parece vídeo de agência*?" Escolha **um** ingrediente de fora do comum (objeto cromado 3D, desenho à mão, arquivo de época, tipografia suíça gigante, HUD de vistoria) e use **só ele**.

## 3. Pipeline

```
copy/roteiro aprovado
→ áudio-guia: locução (transcrever.py → tempos por palavra) ou trilha (batidas.py → grade)
→ mapa de batidas: cena | início–fim | o que se move | ease | SFX | texto na tela
→ quadros-chave (stills) de 3–4 momentos → mostrar ao usuário → ajustar o look
→ construir na engine escolhida (motion-livre.md §2)
→ stills de checagem nos picos e passagens → render completo (em blocos, se for pesado)
→ motion blur (120 fps + tmix) / grão no ffmpeg
→ SFX nos eventos + trilha + voz → mixar.py
→ qc.py + folha nos picos → entregar
```

### Regras que o estudo de 47 vídeos de marca confirmou (detalhes em `motion-vocabulario.md`)
- Entradas `expo.out`/`power3.out` 0,3–0,6 s; movimento de câmera/UI `power2.inOut` 0,5–1,1 s; **overshoot só em ícone/check/chip**.
- Passagem de cena = acelera (`expo.in` 0,15–0,3 s + blur) → **corte no pico** → assenta (`expo.out` 0,45 s). **Nada de crossfade.**
- ~48% do tempo é leitura/respiro; a tensão vem do texto digitado/streamado, não da câmera.
- Sobreponha animações em 35–45% (a próxima começa aos ~61% da anterior). Animações em fila com vazio entre elas = "vídeo feito por IA".
- Texto ≥ 2,5% da altura do quadro (ação 4–8%). Texto de UI **nunca inventado**: tarefa, texto e números reais, com a UI reconstruída fiel e **grande**.
- Sempre 30/60 fps contínuos (nada "em degraus"), pelo menos 1 camada de profundidade (DOF, sombra, parallax) e SFX travado na imagem.

## 4. Áudio
- Locução: se vier de WhatsApp/celular, limpe (highpass, denoise leve, cadeia broadcast). Sem locução gravada: **voz local** (`voz_local.py`, Chatterbox/Kokoro, `audio-sfx.md` §5) com 2 vozes para o usuário escolher.
- Trilha: a música "entra" quando o produto ou a ideia se revela (drop no momento-chave; desloque o início da trilha para alinhar).
- SFX em todo pop, clique, passagem e assentamento, com de-esser. Fecho com som mínimo.

## 5. Entrega
`FINAL.mp4` + a pasta do projeto (HTML/JS ou scripts + assets + `LEIA-ME.md` dizendo como re-renderizar e onde mudar textos e tempos).
Se pedirem editável: HyperFrames abre no Studio (`npx hyperframes preview`). Para After Effects/Premiere, use os pacotes da skill principal: `scripts/ae_package.py`, `scripts/premiere_package.py` e `references/entregas.md` na pasta pai de `edicao/`.
