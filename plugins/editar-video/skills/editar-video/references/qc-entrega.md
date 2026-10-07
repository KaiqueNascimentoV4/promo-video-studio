# QC e entrega: antes de dizer "pronto"

## 1. Automático (`qc.py FINAL.mp4 [--words voz.words.json] [--ass legenda.ass] [--cor "#HEX"]`)
- **ffprobe**: resolução e fps certos; número de quadros = duração × fps; `color_primaries/trc/space = bt709`, range tv; H.264 yuv420p; AAC 48 kHz estéreo.
- **Loudness** (ebur128): I = −14 ± 1 LUFS (ou o alvo pedido), TP ≤ −1 dB.
- **Cobertura de legenda**: toda palavra falada coberta por um evento de legenda (lista as faltantes).
- **Zona de interface** (9:16): eventos de legenda fora dos 120 px do topo e dos ~300 px de baixo.
- **Cor da marca** (`--cor`): delta E da cor da marca nos quadros onde ela aparece.
- **Folha de QC**: 1 quadro por segundo + quadros nos cortes → `qc_folha.jpg`.

## 2. Olhar de verdade (ninguém faz por você)
Abra a folha e os quadros nos momentos de motion e em cada corte:
- Cabeça nunca cortada; olhos nunca cobertos por texto.
- Texto cortado na borda, sobreposição de elementos, quadro vazio, layout quebrado.
- Recorte da pessoa sem faixa nem buraco (ombro, cabelo, base do quadro).
- Nada "em degraus" (pose nova a cada quadro), nada congelado, nada rápido demais.
- Legenda certa: grafia de nomes, pontuação, números.
- Marca: logo, cores, contato.

Ouça: o gancho (voz inteligível acima da cama?), cada SFX (audível?), a virada, o fecho, o fim da trilha.

## 3. Entrega
Pasta `EDICAO_<PROJETO>/`:
```
<PROJETO>_FINAL_1080x1920.mp4      ← o que o usuário assiste/posta (H.264)
LEIA-ME.md                          ← como refazer, onde mudar textos e tempos, fatos do cliente, pendências
trabalho/                           ← scripts, edl.json, words.json, legenda.ass, mix.json, projeto de motion
(opcional) master ProRes, .srt, stems de áudio, pacote editável
```
- Remova versões velhas da pasta de entrega (ou mova para `versoes/` com v1, v2…). Nunca deixe o usuário abrir um arquivo velho achando que é o novo.
- Abra o vídeo para ele (Windows: `cmd.exe /c start "" "<caminho>.mp4"`; Mac: `open`).

**Mensagem de entrega** (curta):
1. Caminho do `.mp4`, duração, loudness.
2. **O que olhar, com minutagem** ("0:03 palavra atrás da cabeça; 0:12 cartão; 0:27 CTA").
3. O que é ilustrativo ou precisa de confirmação.
4. O que ficou de fora e por quê.

## 4. Revisão
Críticas costumam vir em lote e com urgência. Faça uma lista com **cada item**, corrija tudo, re-renderize e responda com uma tabela `item → o que fiz → minutagem para conferir`. Se um pedido contradizer uma regra da casa, faça o que ele pediu e anote a regra nova (é preferência do cliente, ou da casa? Se for da casa, atualize a skill).
