# PROMPT OBRIGATÓRIO: remake 1:1 frame-locked

No modo 5, preencha os campos `[...]` com o que o usuário e o MIV deram, mostre a versão preenchida ao usuário e **execute exatamente por ela**. Não pule fases nem afrouxe o ACCEPTANCE. O bloco original (em inglês) fica abaixo, sem alteração de conteúdo. Só os falsos links `http://` que o colar criou em `window.seek(t)`, `sync.py` e `encode.py` foram limpos. Os **complementos** depois dele são lições de execução real e também valem.

---

```text
TASK: frame-locked 1:1 remake of REF=[path/to/reference.mp4]. Swap ONLY: brand name→[NAME], logo→[path/to/logo.png|svg], palette→[hex list or "derive from logo"], platform UI→[e.g. LinkedIn→X], faces/screens→[source]. All else identical: layout, sizes, positions, timing, easing, camera, cuts, blur, cursor path, typing cadence, audio beat grid.
ACCEPTANCE: REF and remake stacked + frame-locked → same pose every frame. Cuts 0 frames off. Position/size error ≤1% of frame. Typing char-count, cursor, camera on the same frames. Differences allowed only where the swap forces them (word widths); report each.

PHASE 0 — ANALYSIS (no building yet)
- ffprobe fps/res/duration. Extract ALL frames 0-based to ref/full/fNNNN.jpg + audio to ref/audio.wav. 1fps contact sheets for overview.
- Detect cuts via per-frame mean-abs-diff spikes; confirm visually. Write SPEC.md: shot table (id, f0–f1, content, transition in/out), per-shot detail, component inventory, verbatim on-screen text in order, colour tokens sampled from pixels, font sizes from cap height, cursor paths (tip xy per frame), camera keyframes.
- MEASURE with numpy on ref frames (ink bounding boxes, flood fills, template match), never eyeball. Store per-frame sample arrays for every major move; the spec's prose is a guide, ref/full is truth.
- Audio: STT with word timestamps (narration table: line, start, end, text). Music BPM + beat phase (onset autocorrelation), drop time, loudness arc per section, hard-stop time. SFX hit times from onset/spectral analysis. Voice pitch/wpm.

PHASE 1 — ENGINE (you, before any agents)
- Single HTML page, stage at REF native resolution. window.seek(t) renders frame F=t*fps as a PURE function of F: no timers, no Date, no Math.random (seeded hash), no CSS transitions/animations. Shots register SHOT({id,f0,f1,render(lf,F)}) returning HTML; seek routes F to its shot. window.ready=true only after document.fonts loaded + all images decoded.
- core.js shared helpers: easing set, kf(F,keys,ease), samples(F,f0,arr) interpolating measured arrays, camera(inner,scale,tx,ty,origin,blur), directional motion blur (SVG feGaussianBlur), cursor (glyph MEASURED from ref, press-scale curve measured), ripple, text reveal, brand tokens, logo component (mask-image of logo so any fill/gradient works), avatar/persona pickers.
- Palette swap as ONE deterministic filter applied to each rendered HTML string (hex/rgb/rgba re-hued by band, lightness preserved) so hard-coded colours in shots can't leak the old brand. Bitmaps untouched.
- render.mjs (Playwright Chromium, deviceScaleFactor 1): modes stills <frames> | compare <frames> (ref left | ours right + labelled sheet) | full <f0> <f1>. Per-agent OUT dirs so parallel runs don't collide. Print page errors.
- sync.py: REF over remake stacked, frame-locked mp4. encode.py: PNG frames → h264 at REF fps, mux audio.

PHASE 2 — PARALLEL BUILD
- Split shots into 4 contiguous groups; one agent each; each writes ONLY shots/<G>.js (IIFE, helpers prefixed <G>_), never edits core.js (request changes from you). Give each: BRIEF.md (acceptance bar, swap rules, file rules, verify loop), SPEC.md sections, core.js API.
- Verify loop per shot: compare first/last frame, every keyframe, 2 frames into each transition; iterate until within tolerance. ≤15 frames per render call; one render at a time per agent.
- Report table: shot | frames | MATCHES/CLOSE/ROUGH | residual diff | frames that would drift when stacked | spec errors found vs ref.
- 5th agent = audio: royalty-free commercial-OK track (record URL+licence), time-stretch to REF BPM, cut on beats so drop/breaks/silences land on REF times; SFX synthesized (numpy) on REF hit times; mix script with VO slot table (REF start times, text swapped) that fits each line (≤8% stretch), ducks music under voice, loudness-normalizes (~-14 LUFS, TP ≤ -1). Never reuse REF music or voice.

PHASE 3 — INTEGRATE
- Unify shared glyphs/components across groups (cursor, DM window, logo) — one definition, everyone uses it.
- Full render all frames (2–3 parallel chunks max), encode with mix, run sync.py, build 1-per-second ref|ours contact sheet + sheets at every group seam (last 2 / first 2 frames). Inspect. Fix drift. Re-render. Scan all frames for leftover old-brand colour.
- VO: generate per line (any TTS), trim silence, place on slots, re-mix.

PITFALLS (seen in practice)
- Measure text widths only AFTER fonts load (measureText before load caches fallback widths → words collide). Lazy-init any width tables.
- Word-length changes from the brand swap shift centred layouts; keep shared elements on ref positions, absorb the delta in the swapped word, report it.
- Randomised bursts/particles won't match stacked; drive the visible ones from measured tracks.
- Ref whips may be crisp (no blur); check before adding motion blur.
- Headless Chromium may need to run outside any OS sandbox; use swiftshader/ANGLE if WebGL is involved.
- Never claim a shot matches without viewing ref|ours side by side for it.

DELIVER: remake.mp4 (with audio), sync-check.mp4, SPEC.md, source, and a list of every remaining difference vs REF with frame numbers.
```

---

## Complementos (lições de um remake real de ~73 s / 1752 quadros a 4K)

**Antes da Fase 0**
- **MIV do cliente** antes de tudo: paleta oficial, logo vetorial (SVG recortado justo: viewBox = caixa da tinta), fontes, tom. Sem MIV: `scripts/paleta.py logo.png` e confirmação do usuário.
- **Copy**: decida com o usuário entre (a) estrutura da ref com o texto do cliente, mantendo o número de palavras por cartão o mais próximo possível para não estourar layout, ou (b) copy gerada pelo contexto (`references/copy.md`). Escreva um `SCRIPT-<CLIENTE>.md` plano a plano: o que troca o quê (texto, footage, UI, números) e quais fatos são reais.
- **Footage do cliente** costuma ser fraco (vídeo institucional comprimido, 848×478 de WhatsApp): faça uma **biblioteca de clipes** (`tools/footage.py NOME T0 T1 [--speed] [--crop]`) com folha-catálogo, e considere upscale (Real-ESRGAN `realesr-animevideov3` x2 levou ~0,17 s/quadro numa RTX 3050, ~28× mais rápido que `x4plus`) para a versão final.

**Fase 0**
- Extraia `ref/full` (nativo, para medir) **e** `ref/half` (para comparar rápido). `assets/remake-kit/tools/analisar_ref.py` faz ffprobe, quadros, áudio, folhas 1 fps, candidatos a corte e o esqueleto do `SPEC.md`.
- Divida a spec por grupo (`analysis/spec/G1..G4.md`) com trilhas por quadro em `analysis/tracks/<G>_*.json`. Os agentes leem só a sua parte.
- Detecte **flashes** (quadros brancos de 1 q), **quadros pretos**, cadência "segurada" (gráficos que só mudam a 10–16 Hz) e contadores em pulldown 30→23,976. Eles precisam cair no mesmo quadro.

**Fase 1**
- O kit pronto está em `assets/remake-kit/` (core.js genérico, index.html, render.mjs, tools/compare|sync|encode|sheet|footage). Ajuste `project.js` (W, H, fps, total, escala de visualização, fontes) e `brand.js` (tokens, logo, bandas de troca de cor).
- `compare` imprime `mad` (diferença média de luma) e `edge` (diferença de bordas = desalinhamento de layout; a troca de cor quase não mexe nele) com grade de 10% para julgar o erro de posição.

**Fase 2**
- O `BRIEF.md` dos agentes tem de proibir **inventar fatos**: num remake real, agentes criaram depoimentos falsos, contagem de seguidores e "t/ano" que o cliente não tinha. Tudo isso foi removido. Número não confirmado = `[ILUSTRATIVO]` e entra no relatório.
- Agente de áudio: os SFX ficaram **11 LU abaixo da música** e o usuário "não ouviu nenhum SFX". Exija que o pico de cada evento fique acima do RMS da música (≈4 LU abaixo dela) e verifique evento por evento.
- Trilha: royalty-free genérica foi rejeitada ("parecendo anime"). Pergunte se o time tem pack licenciado e prefira-o (registre a licença).

**Fase 3**
- Render completo de 1752 quadros a 4K ≈ 25 min em 3 blocos paralelos (0 erros). Mais que 3 blocos estoura memória numa máquina de 16 GB.
- Encode: `noise=alls=2:allf=t` + `crf 19 -tune film` (43 MB). Ruído por quadro com crf 16 deu 800 MB.
- Entregue `DIFFERENCES.md`: tabela "forçadas pela troca" (quadros + o quê) e "resíduos" (quadros + o quê).

**VO no remake**
- O prompt diz "generate per line (any TTS)": use `scripts/voz_local.py --roteiro vo.txt --takes 2` (uma linha por slot da ref), escolha
  o take que cabe no slot (≤ 8% de esticamento) e encaixe. Emoção/ritmo próximos da voz da ref (`--emocao`, `--ritmo`), nunca clonando a voz da ref.

**Revisões comuns depois da entrega**
- "Tudo muito rápido": desacelere com um **mapa de tempo** (TIMEMAP no core: trechos com fator 1,12–1,40). Os gráficos são avaliados no quadro inteiro da ref; o footage toca denso e interpolado (render de sonda nos vizinhos). Avise que a partir daí o sync-check deixa de ser 1:1.
- Qualidade baixa do footage: upscale + grade por plano casada com a luma da ref.
