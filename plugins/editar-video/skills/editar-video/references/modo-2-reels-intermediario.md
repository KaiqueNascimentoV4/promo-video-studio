# Modo 2: Reels intermediário (decupagem + legenda + SFX + música + color)

O Reels "bem editado" sem cenas de motion: o melhor take de cada fala, cortes no ritmo, cor consistente, legenda dinâmica, trilha com arco e SFX leves nos cortes e na legenda. É o modo do dia a dia: rápido, barato e com cara de profissional.

**O que entra:** decupagem · reenquadramento com ritmo (aberto/fechado, soco de escala na batida) · color grading · legenda dinâmica · trilha · SFX leves · mix · CTA simples (opcional, como texto/legenda, sem botão animado).
**O que não entra:** palavra atrás da pessoa, cartão de UI, telas de motion. Se o usuário pedir uma dessas no meio, ofereça subir para o modo 1.

## 1. Briefing (`briefing.md`)
A (material) → B (formato/duração) → C (legenda) → D (trilha; SFX padrão = leve) → E (cliente/CTA) → G (look).
Não pergunte sobre motion.

## 2. Pipeline (rápido, quase tudo por script)

```bash
S=<pasta da skill>/scripts
python $S/inventario.py brutos/                       # HLG? vertical? fps?
python $S/transcrever.py brutos/*.MOV --lang pt       # palavras com tempo
python $S/decupar.py brutos/ --out edl.json           # sugere; REVISE o edl.json (ordem, takes, cortes)
python $S/cortar.py edl.json --formato 9:16 --look frio --batidas batidas.json --out trabalho/
python $S/transcrever.py trabalho/voz.wav --lang pt   # tempos finais
python $S/batidas.py trilha.wav                       # se ainda não rodou (o cortar usa para os cortes)
python $S/legendas.py trabalho/voz.words.json --estilo dinamica --formato 9:16 --out trabalho/legenda.ass
python $S/sfx.py --cortes trabalho/cortes.json --legenda trabalho/legenda.ass --nivel leve --out trabalho/sfx.json
python $S/mixar.py trabalho/mix.json                  # voz + trilha (ducking) + sfx → mix.wav
python $S/montar.py --video trabalho/mudo.mp4 --ass trabalho/legenda.ass --audio trabalho/mix.wav --out FINAL.mp4
python $S/qc.py FINAL.mp4 --words trabalho/voz.words.json --ass trabalho/legenda.ass
```

### 2.1 Decupagem
Mesmas regras do modo 1 §2.1. Revise **sempre** o `edl.json` sugerido: o script acha repetições por similaridade de texto, mas não sabe qual take tem o melhor olhar ou a melhor energia. Abra uma folha (`folha.py --tempos`) dos takes concorrentes e escolha.

### 2.2 Ritmo sem motion
- Alternância aberto/fechado no mesmo take (zoom digital 1,0 ↔ 1,25–1,4; ancorado na cabeça) a cada ~1,9 s: dá a sensação de duas câmeras.
- Soco de escala (3,6% em 7 quadros) nos cortes que caem na batida.
- Use **B-roll** se houver (planos de detalhe, produto, ambiente) cobrindo falas longas, com a voz continuando por baixo.

### 2.3 Cor (`cor.md`)
HLG → Rec.709 primeiro. Look da casa (frio/neutro) ou do MIV. Meça Y e R−B do fundo por plano e iguale os takes (`cor.py --medir`, depois `--aplicar`, no máximo 2 passadas).

### 2.4 Legenda (`legendas.md`)
Padrão: **dinâmica palavra a palavra**. "Com destaque" funciona bem aqui (cor da marca na palavra ativa). Sem blocos atrás da pessoa (precisam de recorte; isso é do modo 1).

### 2.5 Trilha e SFX (`audio-sfx.md`)
- Trilha com arco, ≥ duração do vídeo, abafada (lowpass) até a "virada" e aberta depois, opcionalmente.
- SFX leves: whoosh curto em ~1 a cada 2–3 cortes (não em todos), clique de obturador em palavras-chave da legenda, nada no resto. Todos com de-esser, **audíveis** (pico acima do RMS da trilha).
- Voz com a cadeia broadcast; ducking desde o 1.º quadro.

## 3. QC
`qc.py` + olhar a folha: legenda 100% coberta, nada na zona da interface, cor igual entre takes, sem palavra cortada no meio, −14 LUFS / TP −1.

## 4. Tempo esperado
Um Reels de 30–45 s a partir de 10–20 takes: 20–40 min de máquina (a transcrição na GPU leva segundos; na CPU, alguns minutos).
