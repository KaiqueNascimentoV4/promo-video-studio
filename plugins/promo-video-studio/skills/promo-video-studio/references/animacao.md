# Animação HTML → vídeo

## Packshot de produto em fundo branco
Recorte automático (flood fill a partir das bordas) **vaza** quando o produto também é branco (latas, potes, rótulos claros). Em vez de brigar com o recorte, use a foto inteira como "foto" num **card branco arredondado** com sombra (perfil de app, vitrine, grid) — fica limpo e sem borda serrilhada. Se precisar mesmo do recorte, peça PNG com transparência ao cliente.
Logo da marca: procure o `<svg>` no header da landing (vetor, nítido em qualquer tamanho); se a landing usar iframe, abra a URL do iframe direto.

## Sumário
1. Princípio do engine
2. Estrutura do template (`assets/template.html`)
3. Extrair identidade (landing/site/vídeo)
4. Biblioteca de efeitos (o que usar e quando)
5. Telas de produto (UI recriada)
6. Layout e legibilidade
7. Checagem com stills e QA visual
8. Armadilhas conhecidas

---

## 1. Princípio

Uma página 1920×1080 expõe `window.__render(t)` que posiciona **tudo** em função do tempo `t` (segundos) — sem CSS animations, sem timers. `scripts/render.mjs` abre a página no Chromium headless, chama `__render(f/60)` para cada quadro, tira screenshot e envia para o ffmpeg. Resultado: determinístico, sincronizável ao centésimo, re-renderizável. `window.__ready` deve resolver após fontes e imagens carregarem.

Tempos nunca são números soltos: vêm de âncoras da narração (`k('chave')` = tempo da palavra + offset). Cenas são definidas numa tabela `S = { id: [inicio, fim] }` derivada das âncoras.

## 2. Template

`assets/template.html` + `assets/anchors.example.js` já trazem:
- helpers de easing (`E.outExpo`, `E.outBack`, `E.inOutCubic`…), `pr(t,a,b)` (progresso 0–1), `lerp`, `cl`, `rng(seed)` determinístico;
- `whip(el,t,a,b)` — entrada/saída lateral com **motion blur** por filtro SVG proporcional à velocidade;
- `maskIn(el,t,t0)` — texto subindo por trás de máscara;
- `hand()` / `arrow()` / `stroke()` — anotações manuscritas (fonte Gochi Hand) que se "escrevem", setas desenhadas;
- `drawOrb()` — esfera pontilhada animada (halftone) que reage a uma "voz";
- `cam(el,t,keys)` — câmera (zoom/pan) sobre uma UI;
- grão de filme, blobs de cor, grid de pontos, flash nos cortes;
- cenas de exemplo: gancho com contador, tela de produto com câmera, card final.
Copie para a pasta do projeto, ajuste variáveis CSS da marca, troque as cenas.

## 3. Extrair identidade

**Landing page (arquivo HTML ou URL)** — com Playwright:
- `page.goto(...)`, role a página para disparar animações, troque idioma se houver seletor (`getByText('PT',{exact:true}).click()`), extraia `document.body.innerText` (copy oficial), variáveis CSS de `:root` (cores), `getComputedStyle` das fontes, e screenshots por viewport (grid em contact sheet).
- Imagens embutidas em base64 (logos!) — extraia com regex `data:image/...;base64,` e salve; normalmente há versão clara e escura do logo. Para fundo colorido, recolora o logo com PIL (partes coloridas → tom claro da marca, resto → branco).
- Registre: fundo, tinta, cor de destaque, fontes de título/corpo/mono, elementos visuais únicos (ex. esfera pontilhada do app), tom do copy.

**Sistema/app do usuário**: screenshots pelo painel do navegador saem em baixa resolução e com dados reais — prefira ler o texto das páginas (`get_page_text`) e recriar as telas em HTML com dados fictícios.

**Vídeo de referência**: `scripts/analyze_reference.py` (contact sheets 2 fps com timestamp + transcrição).

## 4. Efeitos — quando usar

| Efeito | Uso |
|---|---|
| Tipografia cinética (palavra a palavra, escala 1.2→1 + blur) | ganchos, slogans, kinetic curtos |
| Whip lateral com motion blur | troca de cena com energia (kinetic/HUD) |
| Flash branco 0,16 s a ~20% | marca o corte sem distrair (comerciais narrados) |
| Máscara de texto subindo | títulos e taglines |
| Anotações à mão + setas | humor, apontar coisas (estilo monday) |
| Contador numérico | dados do gancho |
| Nuvem de palavras com física (rolagem, congelar, cair, ser sugada) | "informação perdida" |
| Câmera em UI (zoom em coluna/card no momento da fala) | mostrar produto |
| Wipe circular / varredura de cor | entrada do card final |
| HUD (cantos, timecode, capítulo) | estética tech/financeira |
| Ken Burns (zoom lento) | fotos e cenas paradas |

## 5. Telas de produto

Recrie em HTML: sidebar com logo e navegação, cabeçalho com cliente, cards com rótulo mono + título + bullets, tabela/board com pills de status coloridas, "Sincronizado" com check verde, celular com notch e bolhas de chat. Anime: cards entram em sequência (outBack), marca-texto (`scaleX`) sobre a frase dita, datas pulsam no "próximo passo", checks de CRM em cascata, cursor se movendo e clicando. Use a câmera para focar exatamente o que a narração cita.

## 6. Layout e legibilidade

- Margens ≥ 120 px; nada encostando na borda (frases traduzidas crescem — reposicione).
- Texto sobre fundo movimentado: halo/radial da cor de fundo por trás (ex. contador sobre nuvem de palavras).
- Rótulos de fase/HUD não podem cobrir títulos da UI quando a câmera dá zoom (colocar embaixo).
- Fonte manuscrita: confirme glifos do idioma (Gochi Hand desenha "¿" como "c").
- Tamanhos: título 90–140 px, corpo 24–34 px, rótulo mono 15–20 px com letter-spacing.

## 7. Stills e QA visual

Antes do render completo: `node scripts/render.mjs --page X.html --dur D --stills t1,t2,...` em 8–12 tempos (meio de cada cena + transições) e monte um grid com PIL para olhar. Depois do render: contact sheet 1 fps do vídeo final (`ffmpeg -vf fps=1,scale=400:-1,tile=9x5`). Procure: texto cortado, sobreposição, quadros vazios/estáticos >1,5 s, elementos que "vazam" para outra cena, flashes errados.

## 8. Armadilhas

- `getBoundingClientRect` de elementos em cena com `display:none` retorna 0 — meça antes de esconder.
- Canvas como camada de grão não estica com `inset` — use div com `background-image` repetido.
- Filtro SVG em ancestral de elemento 3D achata o 3D (ok, mas saiba).
- Escapes em JS escritos por Python/bash: prefira gravar arquivos com a ferramenta de escrita; `\n` dentro de string JS gerada por Python vira quebra real.
- Pontuação com fontes de grande letter-spacing negativo: aproxime "." e "," com `margin-left:-.06em`.
