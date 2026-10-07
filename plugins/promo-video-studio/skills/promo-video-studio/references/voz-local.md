# Voz local: locução natural gerada no próprio PC

Alternativa gratuita ao ElevenLabs para a **narração**: roda na GPU (ou CPU) da máquina, sem crédito, sem internet depois do
primeiro download dos modelos, com **uso comercial liberado**. A trilha e os SFX continuam podendo vir do ElevenLabs.

| motor | licença | quando |
|---|---|---|
| **Chatterbox Multilingual** (Resemble AI) | MIT | o mais natural: entonação de pergunta, respiração, emoção ajustável; clona o timbre de uma referência de 6–15 s |
| **Kokoro-82M** | Apache 2.0 | rápido e leve (roda bem em CPU); vozes prontas pt-BR: `pf_dora` (feminina), `pm_alex` e `pm_santa` (masculinas) |

## Instalar (uma vez por máquina)
```bash
python scripts/voz_local.py --instalar     # cria ~/.venvs/voz (Python 3.11 + PyTorch CUDA + chatterbox + kokoro), ~4 GB
python scripts/voz_local.py --checar       # mostra GPU e motores
```
Ambiente isolado de propósito: o PyTorch fixado pelo Chatterbox não pode brigar com o Python do resto do pipeline.
Sem GPU NVIDIA: troque o índice `cu124` por `cpu` (o Kokoro fica rápido; o Chatterbox fica lento).

## Gerar
```bash
# roteiro.txt = uma fala por linha (vira um arquivo por linha + locucao.wav juntado + linhas.json)
python scripts/voz_local.py --roteiro roteiro.txt --motor chatterbox --emocao 0.6 --ritmo 0.45 --takes 2 --out locucao/
python scripts/voz_local.py --roteiro roteiro.txt --motor kokoro --voz pm_alex --out locucao_kokoro/
python scripts/words.py locucao/locucao.wav --lang pt     # tempos por palavra → anchors.js, como no fluxo normal
```
- `--emocao` (exaggeration): 0,3 sóbrio · 0,5 natural · 0,7–0,9 comercial empolgado. `--ritmo` (cfg_weight): menor = mais lento e pausado.
- Comercial com gancho: `--emocao 0.7 --ritmo 0.4`. Institucional/explicativo: `--emocao 0.4 --ritmo 0.35`.
- `--referencia voz.wav` clona um timbre (6–15 s de uma pessoa, áudio limpo, sem música). **Só com autorização** da dona da voz:
  o próprio cliente, um locutor contratado ou você. Sem referência, o Chatterbox usa a voz do Kokoro (`--voz`) como semente.
- Gere 2 takes (`--takes 2`) e 2 timbres para o usuário escolher, como no ElevenLabs.
- Escreva números, preços e siglas como se fala ("R$ 697" → "seiscentos e noventa e sete reais").
- Verificação: transcreva o take (`words.py --text`) e compare com o roteiro. Marca que soa como palavra comum precisa de grafia fonética.
- Medido nesta máquina (RTX 3050 6 GB): 3 falas (~11 s) em ~1 min com Kokoro e ~2 min com Chatterbox (2 takes), já com o modelo carregado.
  Ambos transcritos sem erro pelo Whisper (confiança 0,97–0,98).

## Problemas conhecidos
- `TypeError: 'NoneType' object is not callable` no `PerthImplicitWatermarker`: o setuptools ≥ 81 removeu `pkg_resources`.
  Resolva com `uv pip install --python ~/.venvs/voz/Scripts/python.exe "setuptools<81"` (o `--instalar` já faz isso).
- O Chatterbox grava uma marca d'água inaudível (Perth) no áudio. Não afeta a qualidade.
