# Entregas extras

## Versão para redes (limite de tamanho)
`python scripts/compress.py video.mp4 --max-mb 24` → 2 passes x264, 30 fps, AAC 128k, mesma resolução. 45 s cabem em ~22,5 MB com qualidade praticamente igual. Para Reels/Stories, ofereça versão 9:16.

## Vertical 9:16
Não é só crop: duplique o HTML com viewport 1080×1920 (`--width 1080 --height 1920` no render), reorganize cenas em coluna (texto em cima, produto embaixo), aumente tipografia ~1,3×, mantenha áreas seguras (topo 250 px e base 350 px livres para a UI do Instagram). Reuse as mesmas âncoras e mix.

## Outro idioma
1. Roteiro adaptado (ver `roteiro.md` §6) → voz nativa (v4, 2 takes) → `words.py --lang es` → âncoras novas com **as mesmas chaves**.
2. Gere `projeto_<lang>.html` por substituição de strings com `assert s.count(a)==1` para cada texto (falha alto se algo não for trocado) e liste resíduos do idioma original no fim.
3. Stills → corrija textos cortados/glifos → render → mix com config do idioma.

## Pacote editável para Premiere (FCP7 XML)
`python scripts/premiere_package.py --page projeto.html --dur 45 --out "Downloads/<Nome>_Premiere" --audio-config mix.json`
Gera:
- `Video/V1_Cenas_base.mp4` (sem anotações), `V2_Setas_desenhos_alpha.mov` e `V4_Textos_renderizados_alpha.mov` (QuickTime Animation com alpha — Premiere lê nativo; arquivos leves porque são quase vazios).
- `Audio/` stems: narração, trilha com/sem ducking, cada SFX — com ganho pré-master limitado para não clipar (o mix fica ~2–3 dB abaixo do final; instruir normalização −14 LUFS no export).
- `<nome>.xml`: V1 cortada por cena, V2 por cena, V3+ títulos de texto editáveis (gerador "Text" FCP7 com fonte, tamanho, cor, rotação e posição), V10+ textos renderizados desligados (referência/backup), áudio em trilhas, marcadores com cada frase da narração.
- `Fonte/` (Gochi Hand OFL) e `LEIA-ME.txt`.
Requisitos no HTML: `window.__setLayer(mode)` (base/doodle/text), `window.__annExport()`, `window.__scenes()` — já presentes no template.
Limitação honesta: a posição/tamanho exatos dos títulos importados de XML não são garantidos pela Adobe; por isso a trilha de textos renderizados acompanha. A animação de "escrita" não vai no texto editável.

## Sempre
Salve fontes (HTML, âncoras, configs de mix, áudios baixados, takes alternativos) em `Downloads/<Projeto>_src/` e mencione na entrega.

## Pacote editável para After Effects (o preferido para motion designers)
Resultado: um `.jsx` que monta o projeto inteiro no AE — textos **nativos** (mesma fonte/cor/tracking/entrelinha/posição/tempo, animações em keyframes, legendas com animador palavra por palavra), imagens nativas (produto/logo, Replace Footage), base renderizada sem textos, FX (textura/grão), áudio (MIX FINAL ligado + separados desligados) e camadas **organizadas**: ordem cronológica de cima para baixo, cada cena com divisória numerada (`NN ==== CENA ====`, null com a duração da cena) e cor própria, `NN Cena · item` nos nomes, base travada, áudio agrupado no fim, marcadores por cena.

1. **Na página** — copie `assets/ae_export.js` para a pasta do projeto, inclua depois do engine e defina `window.__aeExport` com `aeCollector(render)`: um `ae.text(nome, seletor, t_repouso, t_in, t_out, anim, opts)` por texto e `ae.image(...)` por imagem nativa. Nomeie `"Cena · item"` (ou passe `group`). Use `own:true` quando o elemento tiver filhos com outro estilo (cada filho vira uma camada) e `neutral` para tirar escala/rotação da animação durante a medida. Exemplo no fim do arquivo.
2. **Modo base** — CSS `body.L-base #stage *{color:transparent!important;text-shadow:none!important}` + esconda as imagens nativas e texturas que irão como camadas; `window.__setLayer = m => document.body.classList.toggle('L-base', m === 'base')`.
3. **Exportar e renderizar**: `node scripts/render.mjs --page p.html --export ae_data.json --fn __aeExport` e `node scripts/render.mjs --page p.html --dur 45 --layer base --out base.mp4`.
4. **Áudio separado** — no seu script de mix, gere cada voz com o tratamento aplicado (sem atraso), cada SFX processado, a trilha já com ducking (rode o grafo do mix mapeando só a saída da música; saídas não usadas → `anullsink`) e liste em `stems.json` `[arquivo, início_s, "voz"|"sfx"|"trilha", "nome"]`. Ganho = ganho do master − 5 dB (folga, já que não passa pelo limitador).
5. **Empacotar**: `python scripts/ae_package.py --data ae_data.json --base base.mp4 --out "Downloads/<Projeto>_AE" --name "<Projeto>" --file imagens/produto.png=assets/produto.png --mix mix.wav --stems stems.json --audio-dir stems --ref final.mp4 --zip` (converte a base para bt709, copia tudo, escreve o .jsx e o LEIA-ME).
6. **Validar sem AE**: `node scripts/ae_sim.mjs --data ae_data.json --base stills_base/t_7.50.jpg --t 7.5` e compare com o still original no mesmo tempo — posição e tamanho dos textos devem coincidir.

Detalhes técnicos: point text ancorado na linha de base (topo da linha + `fontBoundingBoxAscent`), âncora movida para o centro do texto (rotação/escala giram como no CSS), tracking = letter-spacing/size×1000, fonte → nome PostScript (`AE_FONT_MAP` em ae_export.js — acrescente as da marca), .jsx em ES3 só com ASCII (dados com escapes \uXXXX), pilha de camadas montada num array + `moveToEnd()`. O script foi validado por sintaxe e simulação, sem AE instalado: se der erro ao rodar, peça a mensagem ao usuário e corrija.
