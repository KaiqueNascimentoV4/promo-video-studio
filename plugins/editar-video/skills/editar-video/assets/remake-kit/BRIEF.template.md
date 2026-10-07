# BRIEF: agentes de plano (leia inteiro antes de escrever código)

<!-- Modelo: preencha os <...> e entregue a cada agente junto com a seção dele da SPEC. -->

Projeto: `<pasta do projeto>`. Você reconstrói um grupo contíguo de planos de um filme de `<duração>` s, `<fps>` fps
(REF = `<descrição curta da referência>`, `<N>` quadros) como **remake 1:1 travado no quadro para `<CLIENTE>`**. Leia, nesta ordem:
1. `SCRIPT-<CLIENTE>.md`: o que substitui o quê no seu grupo (copy, footage, UI). É a troca criativa; siga-a.
2. `SPEC.md`: spec mestre (gramática visual, tipografia, tokens de cor, flashes).
3. `analysis/spec/<G>.md`: a spec medida do seu grupo; `analysis/tracks/<G>_*.json` é a verdade por quadro.
4. `analysis/spec/AUDIO.md` só para contexto de batida (você NÃO faz áudio).

## Critério de aceite
REF e remake empilhados e travados no quadro → **mesma pose em todo quadro**.
- Cortes no mesmo quadro (0 de diferença). Flashes idênticos. Erro de posição/tamanho ≤ 1% do quadro.
- Texto: mesmo centro de linha, altura de caixa-alta, linha de base; mesmos quadros de entrada e saída por palavra; mesmas curvas de zoom.
- Digitação (caracteres por quadro), cursor e câmera nos mesmos quadros. Contadores mudam nos mesmos quadros (cadência segurada).
- Diferenças só onde a troca obriga (largura das palavras, forma do logo, conteúdo do footage): **reporte cada uma**.
- Mesma curva (use as trilhas medidas; a curva importa, não só as pontas). Motion blur só onde a REF tem.

## Regras da troca
- Mude só marca, logo, paleta, UI de plataforma, copy (conforme o SCRIPT) e footage. Layout, tamanhos, tempos, curvas, câmera,
  blur, caminho do cursor, cadência de digitação e efeitos ficam idênticos.
- Cores: escreva as cores da REF que você amostrou. O `seek()` aplica a troca de paleta (`brand.js` → `SWAP_BANDS`) em todo HTML.
  Em canvas: `C.col('#hexDaRef')`.
- Logo: `C.logo(h, fill)` (máscara CSS: qualquer cor/degradê). Lockups: `C.svgImg(C.BRAND.<asset>, h)`.
- Footage é bitmap (não é re-matizado). Reproduza a grade da REF com filtros CSS/SVG, overlays ou canvas num `post`.
- **Nunca invente fatos**: depoimento, número, seguidores, prêmio, prazo. Sem fonte no SCRIPT = `[ILUSTRATIVO]` + avise no relatório.

## Footage
- Biblioteca: `assets/footage/<nome>/f0001.jpg…` no fps da REF; catálogo em `work/footage_catalog.jpg`.
- Clipe novo: `python tools/footage.py <G>_nome T0 T1 --src <vídeo do cliente> [--speed S] [--crop w:h:x:y]`.
- No shot: `C.plate(nome, i, css)` = `<img>` de quadro inteiro do quadro i (0-based, limitado). `C.clipInfo[nome].n` = nº de quadros.
- Precisa de algo que não existe no material do cliente (celular, papel, mapa)? Construa em HTML/SVG/canvas. Não baixe stock;
  diga no relatório se um plano realmente não dá para fazer.

## Regras de arquivo
- Você escreve **só** `shots/<G>.js` (+ rascunho em `work/<G>/`, renders em `out/<G>/`, clipes/bitmaps novos com o seu prefixo).
  IIFE; helpers com prefixo `<G>_`; nada global além de `SHOT(...)`.
- **Nunca edite** `core.js`, `index.html`, `render.mjs`, `tools/`, arquivos de outros grupos, `ref/`, `analysis/`.
  Precisa mudar o core? Faça uma versão local `<G>_` e peça a mudança no relatório.

## Contrato do motor (`window.C`)
Palco = `PROJECT.W × PROJECT.H` CSS px (nativo da REF: use os números da spec direto).
`SHOT({id, f0, f1, z?, render(lf, F) -> html, post?(el, lf, F) -> Promise})`, `lf = F − f0`. Função pura de F:
**sem timers, Date, Math.random, transições/animações CSS, `<video>`**. Shots podem se sobrepor (empilhados por z).
- Matemática: `C.E` (linear, in/out/inOut Quad…Quint, Expo, Sine, outBack, inBack, step, bezier(…)), `C.clamp, lerp, inv, prog(F,a,b,ease)`,
  `C.kf(F, [[f,v,ease?],…])`, `C.samples(F, f0, arr)`, `C.stepAt(F, [[f,val],…])`, `C.held(F, quadrosDeMudança)`, `C.pulldown(F, f0, fase)`.
- Ruído: `C.hash(n, seed)`, `C.rng(seed)`, `C.noise1(x, seed)`.
- Layout: `C.abs(x,y,inner,css)`, `C.full`, `C.bg(cor)`, `C.camera(inner,{scale,tx,ty,ox,oy,rot,rx,ry,persp,blur})`, `C.zoomLin`,
  `C.mblur(inner, ângulo, sigma)`, `C.rgbSplit`, `C.defFilter(id, corpoSVG)`, `C.scanlines`, `C.vignette`, `C.dof`, `C.flash`, `C.ripple`.
- Texto: `C.FONT` (do project.json), `C.wordLine(palavras, {size, family, weight, cx, baseline, tracking, color, visible:[bool], wordStyle})`
  → linha diagramada UMA vez, palavras cortando no lugar final; `C.textAt`, `C.run`, `C.capToSize(capPx, família, peso)`, `C.measure`,
  `C.fontMetrics` (**só dentro do render**: fontes precisam estar carregadas), `C.fmtBR`, `C.esc`, `C.typeOn`.
- Cursor: `C.cursor(x, y, {type:'arrow'|'hand'|'ibeam', cell, press, opacity, blur})`, ponta em (x,y). Meça o glifo na REF e ajuste `cell`.

## Ferramentas
- `node render.mjs stills <quadros> --out out/<G>/x` · `node render.mjs compare <quadros> --out out/<G>/cmp` (REF | NOSSO | DIF com
  grade de 10%, imprime `mad` e `edge`). **≤ 15 quadros por chamada, um render por vez.**
- Medir: `python tools/medir.py tinta|caixa-alta|cor|trilha|tinta-trilha …` em `ref/full`. Folhas: `python tools/sheet.py`.

## Loop de verificação (por shot)
1. Leia a spec e as trilhas do shot; meça o que faltar em `ref/full`.
2. Construa a partir das trilhas e das chaves ajustadas.
3. `compare` no primeiro e no último quadro, em cada quadro-chave e 2 quadros dentro de cada transição. Itere até a tolerância.
4. **Nunca diga que um shot bate sem ver REF|NOSSO lado a lado.**

## Relatório final (sua última mensagem)
Tabela: `shot | quadros | BATE/PERTO/GROSSO | resíduo (mad/edge + o quê) | quadros que derivariam empilhados | erros da spec vs ref`.
Depois: diferenças forçadas pela troca (com quadros), pedidos ao core, assets/clipes novos, copy que precisou adaptar, fatos [ILUSTRATIVO].
