# Modo 5: remake 1:1 de um vídeo de referência para um cliente

Pega um vídeo que o cliente amou (de outra marca, de um creator, de um lançamento) e o **refaz quadro a quadro** para a marca do cliente: mesma composição, tamanhos, tempos, curvas, câmera, cortes, blur, caminho do cursor e cadência de digitação. Muda só o que a troca exige: nome, logo, paleta, UI de plataforma, rostos/telas, copy. O resultado empilhado com a referência tem **a mesma pose em todo quadro**.

**É obrigatório executar pelo prompt de `assets/prompt-remake.md`** (fases 0–3 + complementos).

## 1. Aviso de custo, antes de tudo
Use o texto de `../GUIA.md` §5. Números reais para dar a dimensão: um filme de 73 s / 1752 quadros a 4K teve análise com 57 trilhas medidas por quadro, 4 grupos de planos mais áudio, várias rodadas de `compare`, ~25 min só no render final e 3 versões de revisão. Ofereça o **modo 4 inspirado na referência** como alternativa barata ("mesma vibe, não quadro a quadro").

Siga só com um "sim" explícito.

## 2. Briefing (depois do sim; texto livre, `briefing.md` §I)
1. **Referência**: arquivo ou link (baixe na resolução nativa; guarde a URL).
2. **MIV do cliente** (obrigatório pedir): paleta, logo vetorial, fontes, tom. Sem MIV: logo + site + Instagram → `paleta.py` + confirmação.
3. **Trocas**: marca → `[NOME]`; logo → `[arquivo]`; paleta → `[hex]` ou "derivar do logo"; UI de plataforma (ex.: X → Instagram); rostos/telas → de onde vêm.
4. **Copy**: manter a estrutura da referência com o texto do cliente **ou** gerar pelo contexto (`copy.md`). Mostre a copy e o plano temporal plano a plano para aprovação **antes** de produzir; a aprovação do custo do modo não substitui esta aprovação criativa.
5. **Material do cliente**: vídeo institucional, fotos, prints, gravação do produto. Avise se for fraco (resolução baixa vira upscale + grade casada).
6. **Formato de entrega**: o da referência (padrão) ou também uma versão 9:16 (refazer o enquadramento, não cortar).

Depois **preencha o prompt** e mostre ao usuário:
```
TASK: frame-locked 1:1 remake of REF=ref/source.mp4. Swap ONLY: brand name→<Cliente>, logo→assets/brand/logo.svg,
palette→#XXXXXX,#YYYYYY (do MIV), platform UI→X→Instagram, faces/screens→footage do cliente (assets/footage). …
```

## 3. Estrutura do projeto (o kit cria quase tudo)
```
<Cliente>-remake/
  ref/source.mp4  ref/full/fNNNN.jpg  ref/half/fNNNN.jpg  ref/audio.wav  ref/sheets/
  analysis/spec/{G1..G4,AUDIO}.md   analysis/tracks/*.json      ← Fase 0
  SPEC.md  SCRIPT-<CLIENTE>.md  BRIEF.md                         ← Fase 0/1
  project.js  brand.js  core.js  index.html  render.mjs  tools/  ← Fase 1 (assets/remake-kit)
  shots/G1.js … G4.js                                            ← Fase 2 (um agente por arquivo)
  assets/brand/  assets/footage/<clip>/f0001.jpg + index.js
  audio/  out/  remake.mp4  sync-check.mp4  DIFFERENCES.md        ← Fase 3
```

Começo:
```bash
K=<pasta da skill>/assets/remake-kit
mkdir <Cliente>-remake && cp -r $K/* <Cliente>-remake/ && cd <Cliente>-remake
npm i playwright && npx playwright install chromium
python tools/analisar_ref.py caminho/da/referencia.mp4      # Fase 0: quadros, áudio, folhas, cortes, SPEC esqueleto, project.js
node render.mjs stills 0,10,20                              # o kit roda (shot de exemplo)
```

## 4. Fases (resumo; o prompt manda)
- **Fase 0: análise.** Nada de construir. Medir com numpy, nunca no olho. `SPEC.md` com a tabela de planos, o texto literal na ordem, os tokens de cor amostrados, os tamanhos pela altura de caixa-alta, os caminhos do cursor e os quadros-chave de câmera. Áudio: tabela de narração, BPM e fase, drop, arco de loudness, SFX.
- **Fase 1: engine.** Kit pronto; ajuste `project.js` e `brand.js` (bandas de troca de cor: a cor da marca antiga é re-matizada para a nova com a luminosidade preservada; bitmaps intocados).
- **Fase 2: construção.** Divida os planos em 4 grupos contíguos, cada um em `shots/<G>.js`, e trate o áudio separadamente. Execute os grupos em sequência; se o ambiente oferecer agentes paralelos e o usuário tiver autorizado esse modo de trabalho, distribua cada grupo com `BRIEF.md` (modelo em `assets/remake-kit/BRIEF.template.md`), sua seção da spec e a API do core.
- **Fase 3: integrar.** Unificar componentes compartilhados (cursor, janela, logo), render completo em 2–3 blocos, `encode.py`, `sync.py`, folhas ref|nosso a 1 q/s e nas costuras entre grupos, varredura de cor da marca antiga, VO por linha.

## 5. Ética e direitos (dizer ao usuário quando for o caso)
- Copiar **linguagem visual** (composição, ritmo, movimento) para outro produto é prática comum. Copiar **marca, música, voz, personagens ou footage** de terceiros não é. Por isso a música e a voz da referência **nunca** são reutilizadas, e logos ou nomes de terceiros não aparecem no remake.
- Se a referência mostrar pessoas reais, use o material do cliente ou reconstrução gráfica, nunca o rosto de outra pessoa.
- Números e fatos do cliente: reais ou marcados `[ILUSTRATIVO]`.

## 6. Entrega
`remake.mp4` (com áudio, −14 LUFS, TP ≤ −1) · `sync-check.mp4` (ref em cima, remake embaixo, número do quadro gravado) · `SPEC.md` · fonte completa · `DIFFERENCES.md` (diferenças forçadas pela troca e resíduos, com números de quadro) · lista do que é ilustrativo. Mostre o sync-check: é ele que prova o 1:1.
