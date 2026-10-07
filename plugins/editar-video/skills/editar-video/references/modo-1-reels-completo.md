# Modo 1: Reels com motion completa

Talking head, ou takes com fala, que viram Reels "de agência": decupagem no ritmo, cor, legenda dinâmica, trilha com arco, SFX amarrados a cada movimento e **cenas de motion que encenam a fala** (palavra gigante atrás da pessoa, cartão de vidro de UI, tela de virada, CTA animado).
Régua de qualidade: reels estilo Iman Gadzhi (herói atrás da cabeça) + talking head com UI da Apple (Devin Jatho) + anúncio do Apple Card. A família G do estudo de motion (`motion-vocabulario.md` §2) é a mais próxima: apresentador e o motion fazendo o corte.

## 1. Briefing (`briefing.md`)
A (material) → B (formato/duração) → C (legenda) → D (trilha + SFX) → E (cliente/CTA) → F (copy, se for roteiro novo) → G (look) → H (cenas de motion).
Se houver cliente: MIV (`identidade-cliente.md`) antes de desenhar qualquer cena.

## 2. Pipeline

```
inventario.py   brutos → inventario.json (HLG? rotação? fps?)
transcrever.py  todos os brutos, com palavra → *.words.json
decupar.py      sugere o EDL (melhor take por fala, sem repetição/direção) → edl.json → REVISAR À MÃO
cortar.py       edl.json → voz.wav (respiração inteira, silêncios apertados) + mudo.mp4 (reenquadrado + cor)
transcrever.py  voz.wav de novo → voz.words.json  (os tempos finais vêm DAQUI, nunca dos brutos)
batidas.py      trilha → batidas.json  (BPM, fase, drop, arco)
cortar.py       2.ª passada: planos de ~1,9 s alternando aberto/fechado com corte na batida (--batidas)
cor.py          medir → corrigir plano a plano (Y ≈ 106 ± 2, parede R−B ≈ −16) → mudo.mp4
[recorte]       matte da pessoa SÓ nas janelas com algo atrás dela (rembg u2net_human_seg / hyperframes remove-background)
[motion]        cenas (HyperFrames, motor de quadro do kit ou compositor Python) → camadas atrás/frente com alfa
legendas.py     voz.words.json + roteiro → legenda.ass (corrida) + enfase.ass (blocos/heróis)
sfx.py          sfx.json: um som por movimento, ataque aparado, de-esser
mixar.py        voz + trilha (ducking) + SFX → mix.wav (−14 LUFS, TP −1)
montar.py       camadas na ordem do §3 + áudio → FINAL.mp4 (H.264, bt709)
qc.py           folha, loudness, cobertura de legenda → corrigir → entregar
```

Rode tudo numa pasta de projeto `EDICAO_<PROJETO>/trabalho/` e entregue em `EDICAO_<PROJETO>/`.

### 2.1 Decupagem (o que decide a qualidade)
- Leia a transcrição **inteira** antes de cortar. Para cada frase da mensagem, escolha o take mais limpo: dicção, olhar na lente, sem tropeço, câmera parada.
- Frases do mesmo take ficam num segmento só (a respiração fica natural).
- Tire: repetições, falsos começos, conversa de direção ("né?", "ok?", "é isso?", "de novo"), voz de outra pessoa, takes olhando para baixo.
- Silêncio entre takes ~0,11 s; pausas internas > 0,22 s viram 0,14 s.
- Corte no **envelope do áudio**, não no tempo do Whisper (que erra 50–150 ms). Recue ~40 ms antes de plosivas (/t/, /p/, /k/): o detector de ataque para no silêncio de oclusão ("San|ta").
- Takes com câmera ruim: o **áudio fica** e a imagem vira motion ou câmera lenta dos quadros bons. Nunca congelar.

### 2.2 Planos e reenquadramento
- Horizontal → vertical: ancore a **cabeça** (centro por segmento, medido com o recorte ou com detecção de rosto), nunca o centro do quadro.
- Duração-alvo de ~1,9 s por plano (mín. 1,05 s), alternando **aberto ↔ fechado** (zoom 1,0 ↔ 1,25–1,4 no mesmo take = "segunda câmera").
- **Soco de escala** de 3,6% em 7 quadros nos cortes que caem na batida.
- Trecho em **P&B** opcional num momento de acusação/virada (sub no corte, voz com reverb de hall wet ≈ 0,40, RT60 ≈ 2 s; 0,90 estoura).

### 2.3 Cenas de motion (o vocabulário da casa está em `motion-vocabulario.md` §1)
Escolha **3–5 momentos** pela fala: o miolo de cada terço, o número forte, a virada e o fecho.
- **Herói**: palavra gigante atrás da cabeça, com a cabeça mordendo ~30% da base das letras. 1–3 por vídeo. **Só com talking head limpo e bem iluminado.**
- **Cartão de vidro de UI**: um cartão atravessando estados (carregando → valor → lista → anel 100%) sincronizado com a fala, com o fundo desfocado atrás.
- **Pergunta/virada**: o quadro encolhe até virar foto arredondada sobre a cor da marca; a frase se escreve palavra por palavra; a foto volta a encher a tela já com o plano seguinte.
- **Contagem**: número forte de 0 → valor (dígitos tabulares; som = whoosh leve, **nunca** tique de contagem).
- **Fecho com CTA**: botão "Chame no WhatsApp" na frente da pessoa; um dedo pousa, o botão afunda 5,5%, aparece a onda de toque e ele vira verde com check.
- Todos os tempos saem da fala (`voz.words.json`) por chave semântica (`em("frase", i)`), nunca escritos à mão: se a decupagem mudar, nada desencontra.

**Engine:** HyperFrames (HTML+GSAP, `npx hyperframes`) para cenas de UI e tipografia, com duas camadas: `atras` (opaca ou alfa) e `frente` (alfa, ProRes 4444 ou PNG). Para composição pesada com recorte e câmera que se move, use o compositor Python (numpy/OpenCV, função pura do quadro). Uma composição HyperFrames por projeto; a camada da frente fica em outro projeto.

### 2.4 Ordem das camadas (é isso que põe o texto "dentro" da cena)
1. `mudo.mp4`: imagem cortada, reenquadrada e com cor
2. `enfase.ass`: blocos de ênfase
3. cenas de motion **atrás** (fundo de marca, cartão, palavra gigante)
4. **recorte da pessoa por cima de 2 e 3**: a pessoa tapa a palavra e cria profundidade
5. motion **na frente** (botão do CTA, cenas de tela cheia)
6. `legenda.ass` (corrida), sempre por cima
7. `setparams` bt709 nas 4 pontas

### 2.5 SFX deste modo (`audio-sfx.md` §3)
Cortina/entrada de cena = whoosh rápido · palavra herói assenta = impacto baixo · corte P&B = sub boom · cartão aparece = clique/obturador (não "bop") · dígitos = digitação curta · check = "correct" · fecho = 1 whoosh suave + clique. Todos com de-esser e ataque aparado.

## 3. QC (`qc-entrega.md`)
Folha de contato em cada cena de motion e em cada corte · cobertura de legenda 100% · cabeça nunca cortada · texto fora da interface do Instagram · recorte sem faixa/buraco (no fecho, estenda o tronco até o pé do quadro) · loudness/pico · trilha ≥ duração.

## 4. Armadilhas deste modo
- O recorte (u2net) come ombro de terno escuro e corta o corpo na mesa: use o fecho convexo do tronco estendido até a base.
- Subamostras de motion blur não podem cruzar um corte: ancore a altura da cabeça **por quadro**, senão a palavra aparece duplicada.
- Temperatura medida no quadro inteiro engana (roupa): meça **só a parede/fundo**.
- Rodar a medição de cor duas vezes seguidas **acumula a correção em dobro**.
- Não reescreva `mudo.mp4` enquanto o recorte está lendo dele.
- Em máquina de 16 GB, nunca rode dois encodes 4K ao mesmo tempo (`-threads 2`, `-filter_complex_threads 2`).
