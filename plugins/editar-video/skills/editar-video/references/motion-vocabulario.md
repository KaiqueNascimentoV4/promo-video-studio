# Vocabulário de motion (o que já foi aprovado + o que foi medido)

Duas fontes: (1) as cenas da casa, aprovadas em Reels de talking head depois de muitas rodadas de crítica; (2) um estudo quadro a quadro de **47 vídeos de lançamento** (Linear, Raycast, Notion, Apple, Nubank, Stripe, Monzo, Arc, Cursor, Slack, Airtable, Loom, Duolingo, Spotify, Aside, Liquid, Lovable, Listen…), com números medidos.

---

## 1. Cenas da casa (Reels de talking head)

Todos os tempos saem da fala: `em("frase", i)` = início da palavra i da frase na voz montada. Curvas: `expo` (resolve rápido), `cubica` (in-out), `volta` (back-out, só para pop de UI). Motion blur: média de 3 subamostras por quadro.

### 1.1 Herói: palavra gigante atrás da cabeça
- O fundo vira a **cor da marca** subindo como **cortina** de baixo para cima, com um fio de luz na borda e brilho atrás da cabeça.
- Palavra em serif SemiBold (Playfair), até 250 px, ocupando ~990 px; acima da cabeça, com a **cabeça mordendo ~30%** da base (topo da cabeça medido no recorte, por quadro).
- Cada letra entra 40% maior, de baixo, borrada → nítida, com 30 ms entre letras; uma **varredura de luz** passa uma vez; a palavra deriva +3,5% até o fim (nunca congelada).
- Rótulo pequeno acima, caixa alta, entreletra larga (+0,30 em), tom claro da marca.
- 1–3 por vídeo, um por terço, na palavra que é o miolo da frase; o resto da frase vai para a legenda corrida. Versão grafite no trecho P&B.
- **Só com talking head limpo e bem iluminado.**

### 1.2 Cartão de vidro de UI
- Cartão estilo iOS **atrás da pessoa**, no alto (y ≈ 124 em 1080×1920), 900 px de largura, cantos 44 px; o fundo do plano **desfoca e escurece** enquanto ele está no ar.
- Vidro fosco de verdade: o próprio fundo desfocado e tingido, com um fio de luz na borda de cima.
- Entra 14% menor com back-out e assenta; sai subindo.
- **Um cartão atravessando estados** com a fala: carregando (esqueleto cintilando + spinner) → valor (dígito a dígito, borrado → nítido, selo verde com check) → lista (ícones em quadradinhos com gradiente, % contando, barras enchendo, pílulas âmbar) → anel fechando em 100% com check.
- A fala continua legendada embaixo.

### 1.3 Pergunta / virada (tela cheia)
- O quadro **encolhe** devagar (1,0 s, cúbica) até virar **foto de cantos arredondados** (50%, cantos 58 px, sombra suave) sobre a cor da marca, com dois orbes de luz se mexendo.
- A frase se escreve **palavra por palavra no tempo da fala**: rótulo caixa alta → linha serif regular → linha SemiBold → palavra final grande na cor, com **sublinhado** se desenhando.
- No fim a foto **cresce de volta** até encher a tela **já com o plano seguinte dentro** (sem corte seco); o texto sobe e desfoca.

### 1.4 Fecho com CTA
- Herói em display condensado (Anton) "TOQUE NO BOTÃO" atrás da cabeça, com o rótulo da marca em cima.
- **Botão iOS na frente** da pessoa (pílula, gradiente da marca): entra com pop, um dedo pousa, o botão afunda (−5,5%), onda de toque, vira **verde com check** ("Chame no WhatsApp" → "Conversa iniciada").
- O recorte precisa do tronco inteiro: fecho convexo do tronco estendido até a base do quadro.

### 1.5 Outros recursos validados
- **Soco de escala** de 3,6% em 7 quadros nos cortes na batida.
- **Contagem** 0 → valor (R$ 3.000.000) com dígitos tabulares.
- **P&B** num trecho de acusação/virada, com sub no corte e a voz no hall.
- **Take ruim no meio de cena**: renderize o take vivo com o enquadramento e a cor do plano anterior, ache o último quadro bom e toque os quadros bons em câmera lenta com mistura entre vizinhos. **Nunca congelar.**

### Princípios Apple
Espaço negativo; no máximo 2 pesos; branco/cinza + **um** acento; rótulos em caixa alta com entreletra larga (o oposto da legenda, que é apertada); 300–700 ms por elemento em cascata; revelação por máscara; a Apple não briga com o fundo, ela controla o fundo (degradê/escurecimento atrás).

---

## 2. As 7 famílias de estilo (escolha UMA; misture no máximo duas)

| fam. | nome | assinatura | use para |
|---|---|---|---|
| A | Escuro cinematográfico, UI como objeto | UI num plano 3D inclinado (rotateX 34–40°, rotateZ −12…−15°, perspective ~1400 px), spot e vinheta, deriva 1–3%/s, typewriter 9–12 car/s, fecho blur→nítido + reflexo | dev tools, IA, premium técnico |
| B | Cartões sobre cor + cursor protagonista | UI chapada em cartão (raio 12–40, sombra 8%) sobre cor sólida que muda por feature; macro num controle; cursor grande (5–8% da altura) conduz | SaaS B2B, produtividade |
| C | Plano-sequência, câmera virtual, "tudo vira tudo" | zero cortes; objetos se transformam (ponto → esfera → logo; caret → ponto → fundo); crash-zoom com blur; contador de R$ rolando só os dígitos que mudam | explicar fluxo; **a mais fácil de fazer bem em HTML** |
| D | Gravação + auto-zoom | punch-in 1×→2,3× em 0,7 s seguindo o cursor; jump-zoom de 1 quadro no lugar de corte | demo honesta, tutorial |
| E | Tipografia cinética / manifesto | palavra a palavra cinza → nítido (~0,3 s), 1 palavra de cor; slot rotativo; faixas empilhando por palavra; cortes acelerando | gancho, virada, manifesto |
| F | Consumo / evento físico | o benefício vira evento (dinheiro atravessa a parede; o mundo recua e vira a tela do celular); montagem rápida que acelera | fintech, consumo, marca |
| G | **Apresentador + UI flutuante** | pessoa em plano longo e o motion encenando a fala (UI explode do logo; "vamos voltar" → tudo é sugado de volta) | **talking head de cliente**: é o modo 1 |

---

## 3. Números medidos (mediana de 42 vídeos)

| medida | valor | leitura |
|---|---|---|
| duração | 53 s (35–75) | lançamento 35–75 s; teaser 10–40 s |
| duração média de plano | 5,1 s | plano longo + movimento dentro do plano (o Reels de talking head usa ~1,9 s, outro gênero) |
| evento de movimento | 0,71 s (0,48–0,99) | entradas 0,3–0,6 s; câmera/UI 0,5–1,1 s; chegadas longas 2–3 s |
| forma do ease | out 39% · in-out 40% · in 17% | ease-in quase só em saídas/passagens |
| tempo quase parado | 48% | metade do filme é leitura/respiro |
| cortes na batida (±70 ms) | 33% = acaso | marcas cortam na fala/leitura; batida só em rajada-montagem |
| claros × escuros | 21 × 8 | o "escuro Linear" é minoria |
| com locução | 22 de 42 | metade é só música + texto: **texto na tela é obrigatório** |
| overshoot | só ícone/check/chip/pílula | janelas, texto e câmera nunca |

### Tabela de movimentos (GSAP / equivalente)
| coisa | como | ease |
|---|---|---|
| entrada de janela/cartão | 0,3–0,6 s, de +60–120 px abaixo, escala 0,92–0,96, sem overshoot | `expo.out` .5 / `power3.out` .45 |
| movimento de UI/câmera | 0,5–1,1 s simétrico | `power2.inOut` .7 |
| chegada longa | 2–3,4 s | `power3.out` 3 |
| deriva no plano | 1–3% do quadro/s | `sine.inOut` |
| **atravessar** (passagem) | saída: escala 1→2,4, blur 0→18, 0,28 s → **corte no pico** → entrada: escala 1,25→1, blur 10→0, 0,45 s | `expo.in` / `expo.out` |
| palavra a palavra | 0,3 s por palavra, cinza/blur → nítido | `power2.out` .3 |
| typewriter | 9–12 car/s (pensado) · 33–50 car/s (títulos) | linear |
| streaming de linhas | 0,2 s fade + y 8 px, stagger 0,3 | `power2.out` |
| stagger de grupo | 80–200 ms | — |
| pop de ícone/check | o único lugar com overshoot | `back.out(1.7)` .35–.5 |
| clique | cursor 0,85 por 2×0,08 s + anel 0,4 s + cor do botão 0,2 s | `power2.out` |
| contador | 1,2–1,6 s, só os dígitos que mudam rolam | `power3.out` 1.4 |
| fecho de marca | palavra blur 12–14 px→0 em 0,5 s; reflexo 1 s; frase por máscara 1 s; logo parado 3–7 s | `expo.out` |
| jump-zoom | corte de 1 quadro 55% → 160% da mesma tela | set |
| rajada | 5–10 cortes de 0,21–0,5 s sob texto fixo | set |

Texto: corpo de UI em close 3,5–8% da altura (nunca < 2,5% no celular); títulos 5–12%. Grotesk neutra na UI; mono caixa-alta em rótulos técnicos; serif editorial só em marca "humana".

---

## 4. Catálogo de transições (varie: nunca a mesma duas vezes seguidas; **nada de crossfade**)
1. **Atravessar**: acelera + blur → corte no pico → assenta.
2. **Portal do ícone**: o ícone da marca cresce até virar a moldura da próxima cena.
3. **Caret → ponto → fundo**: o texto se apaga até o caret, que vira ponto, que cresce até ser a próxima cena.
4. **Crash-zoom para dentro de um objeto**: pino do mapa, número numa placa, card no celular.
5. **O mundo vira a tela**: a câmera recua e o cenário se revela como a tela do app.
6. **Match-morph**: o item selecionado encolhe e vira o próximo componente.
7. **Voar para dentro da tela** do aparelho 3D.
8. **Whip** com motion blur (1–2 quadros).
9. **Jump-zoom de 1 quadro.**
10. **Dip para branco / íris.**
11. **Montagem metronômica**: um cartão a cada 10 quadros trocando a cor do fundo.
12. **Objeto-costura**: um elemento sobrevive a todos os cortes (ponto-guia, laptop que abre e fecha, card persistente).
13. **Tinta/máscara cobrindo a tela** no fecho.
14. **Corte seco puro** entre trechos do mesmo plano (o preferido dos premium).

## 5. Playbook de lançamento (quando for produto/app/oferta)
Briefing de 5 perguntas **antes** de animar: (1) o UM momento "espera, ele faz isso?" (o que o usuário printa); (2) o resultado concreto em número; (3) o inimigo (jeito antigo, concorrente); (4) onde o produto vive (o canal: WhatsApp, navegador → vira o 1.º quadro); (5) a objeção que mata a compra.

| tempo (60 s) | bloco | regra |
|---|---|---|
| 0–3 s | gancho | produto "impossível" · visual "wtf" · cinematográfico · afirmação provocativa; 1.º movimento ≤ 0,8 s; som-assinatura antes de 1 s; funciona mudo |
| 3–8 s | promessa | uma frase, verbo + resultado |
| (8–15 s) | problema/inimigo | opcional; escuro |
| 15–40 s | prova = o momento | UMA tarefa inteira, contínua, UI fiel e grande, termina num número |
| 40–52 s | escalada | o inesperado: benchmark, "funciona também em…" |
| (52–56 s) | objeção | opcional, 1–2 frases com ícone |
| fim 3–4 s | fecho | nome + CTA; parado ≥ 2 s |

Para 30 s divida por 2, mantendo gancho e fecho em segundos absolutos. Legenda do post = segundo gancho (o resultado, não o produto).

## 6. Erros típicos de vídeo "feito por IA" (nunca repetir)
Animação em degraus (pose nova a cada 0,13 s) · animações em fila sem sobreposição · rótulos com 1% da altura · 2D chapado sem profundidade nem blur · sem SFX · vitrine longa de resultados sem um momento único · tudo com o mesmo tempo · gradiente roxo em fundo escuro com Inter display.
