# Modo 3: só decupagem + legenda

O mínimo bem feito: escolher os melhores takes, cortar no tempo certo (sem gagueira, sem repetição, sem conversa de direção) e legendar tudo. **Sem trilha, sem SFX, sem grade criativa.** Serve para entregar rápido, ou para o cliente/editor finalizar depois.

**Entra:** decupagem · silêncios apertados · reenquadramento para o formato · **correção técnica de cor** (HLG → Rec.709, para não sair lavado/estourado, sem look) · limpeza de voz (highpass + compressão leve + loudnorm) · legenda.
**Opcional se pedirem:** exportar também o `.srt`/`.ass` separado e um EDL/XML para o Premiere, com os cortes para quem for finalizar.

## 1. Briefing
A (material) → B (formato/duração) → C (legenda; aqui "simples" também é comum) → E só se houver CTA/marca.
Não pergunte trilha, SFX nem look.

## 2. Pipeline

```bash
S=<pasta da skill>/scripts
python $S/inventario.py brutos/
python $S/transcrever.py brutos/*.MOV --lang pt
python $S/decupar.py brutos/ --out edl.json             # REVISE
python $S/cortar.py edl.json --formato 9:16 --look tecnico --out trabalho/
python $S/transcrever.py trabalho/voz.wav --lang pt
python $S/legendas.py trabalho/voz.words.json --estilo dinamica --out trabalho/legenda.ass --srt trabalho/legenda.srt
python $S/mixar.py --so-voz trabalho/voz.wav --out trabalho/mix.wav    # cadeia de voz + −14 LUFS
python $S/montar.py --video trabalho/mudo.mp4 --ass trabalho/legenda.ass --audio trabalho/mix.wav --out FINAL.mp4
python $S/qc.py FINAL.mp4 --words trabalho/voz.words.json --ass trabalho/legenda.ass
```

`--look tecnico` = só HLG→709 (se for HLG) e normalização de nível, sem mexer em temperatura nem contraste.

## 3. Regras que mais pesam aqui
- **Toda fala com legenda.** Confira a cobertura no `qc.py`.
- Legenda com **pontuação**, minúscula normal, nomes próprios e marcas com a grafia certa (peça a lista de nomes ao usuário se o Whisper errar: ele costuma trocar nome de marca por palavra comum).
- Nunca cortar palavra no meio; recue ~40 ms antes de plosivas.
- Nada de pular trecho falado "porque estava ruim" sem avisar: liste o que foi tirado e por quê.

## 4. Entrega
`FINAL.mp4` + (se pedido) `legenda.srt` e `edl.json`/XML. Na mensagem: duração final, quantos takes viraram quantos cortes, trechos removidos com o motivo.
