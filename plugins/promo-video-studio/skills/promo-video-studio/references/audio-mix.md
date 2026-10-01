# Áudio e mix

## Âncoras: transcrição que "erra" palavras
O Whisper escreve números em algarismo ("30" em vez de "trinta") e às vezes grafa a marca diferente ("Naturales"). Antes de montar âncoras/cenas, corrija o texto dessas palavras no `.words.json` (os tempos continuam certos) — senão `kw('n3','trinta')` falha. Marca transcrita diferente nem sempre é pronúncia errada: avise o usuário para ouvir.
Pausas longas da voz: `python scripts/tighten_pauses.py audio/*.mp3` (pausas internas > 0,38 s viram 0,28 s; originais em `audio/orig/`).

## Sumário
1. Narração: preparo e sincronia
2. Trilha: análise e alinhamento
3. SFX: posicionamento e volumes
4. Mix: cadeia, ducking, pausa cômica, master
5. Verificação

---

## 1. Narração

- Converta para WAV mono 48 kHz; leve high-pass 70 Hz + compressor suave (`acompressor=threshold=-20dB:ratio=2.5:attack=5:release=80`).
- Offset de entrada: 0,35–0,4 s (dá respiro ao primeiro quadro).
- `scripts/words.py narracao.wav --lang pt` → JSON com `[inicio, fim, palavra]` e impressão compacta. Monte as âncoras a partir dele (o Whisper erra grafias — "12" vira número, "desse" vira "desce" — mas o tempo está certo).
- Narração longa demais: `scripts/words.py --pauses` lista silêncios; comprima pausas > 0,3 s para ~0,26 s (preserve as cômicas em 0,4–0,55 s) e aplique `atempo` ≤ 1,08. Prefira regerar com roteiro mais curto.

## 2. Trilha

`scripts/audio_profile.py trilha.mp3` imprime: duração, RMS a cada 0,5 s (onde o groove entra/sai), BPM e fase do beat, e salva waveform com grade de segundos (`*_wave.png`) — abra a imagem para ver a estrutura.
Decisões:
- **Drop na marca**: desloque o início da trilha (`music.shift`) para que o momento de energia coincida com a primeira aparição da marca/logo.
- **Cortes no beat** (kinetic): ajuste os tempos das cenas para múltiplos de 60/BPM, ou desloque a trilha pela fase do beat.
- **Trilha mais longa que o vídeo**: corte + `afade` de 1,6–2,2 s no fim; ou emende o final da música (acorde final) no card final, com a emenda em múltiplo de compasso e `acrossfade` de 80 ms.
- **Pausa cômica (stop-time)**: zere a música (~12% de volume) do fim da frase de setup até o punchline, com rampas de 80–150 ms (`volume=eval=frame:volume='1-0.88*clip(...)'`).

## 3. SFX

- Meça o pico de cada SFX (`audio_profile.py --sfx`) e dispare em `t_evento − t_pico` (whoosh ~0,2 s antes do corte).
- Volumes que não mascaram a fala (pré-master): rabisco 0,12 · pop 0,22 · whoosh 0,2–0,45 · digitação 0,4–0,5 · chime de logo 0,45–0,65. Rabiscos e pops com `highpass=f=900`.
- Densidade: SFX em cortes, aparições de elementos-chave, logo e CTA. Não em todo card.

## 4. Mix

`scripts/mix.py config.json` monta tudo com ffmpeg. Cadeia:
1. Narração → `adelay` (offset) → `apad` → estéreo → `asplit` (uma cópia vai para o sidechain).
2. Trilha → estéreo → `atrim` (shift) → automação de volume (pausa cômica) → `afade` in/out → volume base ~0,55–0,62.
3. `sidechaincompress=threshold=0.02:ratio=7:attack=20:release=420` (trilha abaixa sob a voz, volta nas pausas).
4. SFX com `adelay` cada.
5. `amix=normalize=0` → `loudnorm=I=-14:TP=-1.5:LRA=11` → `alimiter=limit=0.87` → AAC 256k 48 kHz **estéreo** (forçar `aformat=channel_layouts=stereo` em todas as entradas — se a primeira entrada for mono, o mix inteiro sai mono).
6. Vídeo: `scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p`, x264 `-preset slow -crf 17 -maxrate 30M -bufsize 60M`, tags bt709, `-movflags +faststart`.

## 5. Verificação

- `ffmpeg -i final.mp4 -af ebur128=peak=true -f null -` → I ≈ −14 LUFS, pico ≤ −1 dBFS.
- `ffprobe`: estéreo, 60 fps, duração certa.
- Transcreva o final (`words.py final.mp4 --text`) e compare com o roteiro: palavra trocada/sumida = SFX ou música alta naquele ponto.
