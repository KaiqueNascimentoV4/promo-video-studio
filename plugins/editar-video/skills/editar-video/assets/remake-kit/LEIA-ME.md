# Kit de remake (motor de quadro determinístico)

Copie esta pasta inteira para o projeto (`<Cliente>-remake/`). Serve para o **modo 5** (remake 1:1) e também para
motion livre no modo 4 quando precisar de controle total por quadro.

```
project.json / project.js   W, H, fps exato, total de quadros, escala de visualização, fontes, TIMEMAP (gerados por analisar_ref)
brand.js                    tokens da marca nova + bandas de troca de cor da marca antiga
core.js                     motor (window.C) — NÃO editar dentro dos agentes
index.html                  carrega project → brand → core → footage → shots/G1..G4.js
render.mjs                  stills | compare | full (Playwright Chromium)
shots/exemplo.js            shot de demonstração do contrato (apague depois)
tools/analisar_ref.py       FASE 0: quadros, áudio, folhas, cortes, BPM, SFX, narração, SPEC.md + G1..G4.md
tools/medir.py              medir com numpy: tinta, caixa-alta, cor, trilha (template match), tinta por quadro
tools/compare.py            REF | NOSSO | DIF + mad/edge (chamado pelo render compare)
tools/sheet.py              folhas de contato e pares REF|NOSSO nas costuras
tools/footage.py            biblioteca de clipes do cliente no fps da ref + catálogo
tools/sync.py               sync-check.mp4 (REF em cima, remake embaixo, número do quadro)
tools/encode.py             PNG → remake.mp4 com o mix
BRIEF.template.md           modelo do brief dos 4 agentes de plano
fonts/                      fontes locais (@font-face no index.html; liste em project.json → FONTS_LOAD)
```

Teste rápido (sem referência): `npm i playwright && npx playwright install chromium && node render.mjs stills 0,30,60`.
Com referência: `python tools/analisar_ref.py caminho/ref.mp4` e siga `references/modo-5-remake-1a1.md` e `assets/prompt-remake.md`.
