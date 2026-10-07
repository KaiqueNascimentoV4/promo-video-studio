# Legendas: estilos, medidas e como fazer

A legenda é a parte que **todo** espectador vê (85% assiste sem som). Sempre ofereça a **dinâmica**; ela é o padrão da casa.

## 1. Os estilos

| estilo | o que é | como fazer |
|---|---|---|
| **Dinâmica palavra a palavra** (padrão) | a linha se **enche** palavra por palavra, cada palavra aparecendo no instante em que é falada; pedaços de 1–3 palavras na mesma altura | `legendas.py --estilo dinamica` (ASS com `\t` por palavra) |
| **Dinâmica com destaque** | igual, mas a palavra **ativa** ganha a cor de destaque (marca) até a próxima entrar, e as anteriores voltam ao branco (sem pop de escala no ASS: escalar uma palavra empurra as vizinhas; se quiser pop, faça a legenda em HTML/motion) | `legendas.py --estilo destaque --cor-destaque "#HEX"` |
| **Blocos de ênfase** (com destaque, modo 1) | 3 linhas centradas: apoio em Playfair romana (0,54) → **palavra-chave** em Playfair SemiBold grande na cor da marca (~880 px de largura) → fecho (0,62). Fundo escurecido com blur 36 atrás, **sem borda** | `legendas.py --enfase roteiro.json` gera `enfase.ass` |
| **Herói atrás da pessoa** (modo 1) | palavra gigante (até 250 px, ~990 px de largura) atrás da cabeça, que morde ~30% da base; o fundo vira a cor da marca subindo como cortina | cena de motion + recorte (`motion-vocabulario.md` §1.1) |
| **Cinematográfica / 3D** | grupos de palavras em profundidades diferentes, câmera atravessando, palavra escondida atrás da pessoa por matte | HyperFrames `embedded-captions` / `camera-3d-captions` se instaladas; senão motor de quadro + recorte |
| **Simples** | frase por frase, estática, sem animação | `legendas.py --estilo simples` |

## 2. Tipografia (regras inegociáveis)
- **Nunca** sombra, contorno ou glow. Se não lê, escureça o fundo atrás do bloco.
- Sans **bold** (Helvetica Bold; livres: Inter Bold, Arimo Bold), **entreletra −0,07 em**, minúscula normal, **com pontuação**.
- Tamanho no 9:16: corpo da legenda 64–80 px (≥ 3,5% da altura), destaque/gancho 130–170 px.
- Posição: centro horizontal; vertical por volta de 62–70% da altura (abaixo do rosto, acima da interface). Nada nos 120 px do topo nem nos ~300 px de baixo.
- Nome composto junto ("São José", "Nossa Senhora" nunca quebram); número de marca por extenso quando é nome ("Sete Mares", nunca "7 Mares").

## 3. Tempo
- Tempos **da voz montada** (re-transcrita depois da decupagem), nunca dos brutos.
- Cada palavra entra no **início** da sua marca do Whisper (pode adiantar 1–2 quadros: a leitura ganha da fala).
- Pedaço: 1–3 palavras (até ~16 caracteres por linha no 9:16); quebre em pontuação e em pausas > 0,25 s; nenhum pedaço < 0,7 s na tela (estenda até o próximo começar).
- O pedaço some quando o próximo entra (sem buraco) ou 0,3 s depois da última palavra, numa pausa longa.
- Não legendar por cima de cena de motion que já escreve a mesma frase (use `pular` só nesses trechos).

## 4. Armadilhas do libass (ASS queimado pelo ffmpeg)
- O campo `Spacing` do estilo é **ignorado**: a entreletra vai inline (`\fsp`).
- O libass desenha **menor que o nominal**: Playfair ≈ 0,70, Helvetica Bold ≈ 0,83, Helvetica ≈ 0,84, Anton ≈ 0,575. O `legendas.py` compensa (`FATOR`): calcula a entreletra em em **renderizado**, senão sai 40% mais apertada e o espaço some.
- Fontes: passe `fontsdir=` no filtro `subtitles`/`ass`, ou o ffmpeg cai em Arial sem avisar. Confira no frame.
- Heredoc do bash come um nível de barra invertida (`\\an4` vira `\an4`): gere o `.ass` por script Python, não por echo/heredoc.
- `PlayResX/PlayResY` iguais à resolução do vídeo, senão tudo escala errado.

## 5. Revisão do texto
- O Whisper troca **nomes de marca e pessoas** por palavras comuns e erra números ("7 Mares" × "Sete Mares"). Peça a lista de nomes próprios no briefing e passe em `--glossario nomes.txt` (prompt inicial do Whisper + correção pós).
- Transcreva em **trechos/por take**: um prompt de arquivo inteiro faz o Whisper entrar em loop ou alucinar. Use VAD (sem ele, no silêncio sai "a a a").
- Leia o roteiro final inteiro antes de queimar.

## 6. Cobertura (QC obrigatório)
`qc.py --words voz.words.json --ass legenda.ass`: para cada palavra falada, o meio dela tem de cair dentro de algum evento de legenda (ou de uma cena de motion marcada como "escreve texto"). O script lista as que faltam. Zero faltando antes de entregar.
