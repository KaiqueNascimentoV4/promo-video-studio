"""Montagem final: vídeo base + camadas (motion, recorte, ASS) na ordem certa + áudio → MP4 H.264 bt709.

  python montar.py --video mudo.mp4 [--ass legenda.ass] [--enfase enfase.ass] [--audio mix.wav] [--out FINAL.mp4]
                   [--camadas camadas.json] [--nvenc] [--crf 18] [--grao 0]

Ordem padrão (de baixo para cima): vídeo → enfase.ass → legenda.ass.
Com --camadas, a ordem é a da lista (de baixo para cima), por exemplo, a ordem do modo 1:
  [{"tipo":"ass","arquivo":"enfase.ass"},
   {"tipo":"video","arquivo":"mg/atras.mov","t0":0},          (com alfa: ProRes 4444 / PNG seq / webm vp9 alfa)
   {"tipo":"video","arquivo":"pessoa.mov","t0":0},            recorte da pessoa (alfa) POR CIMA → a pessoa tapa a palavra
   {"tipo":"video","arquivo":"mg/frente.mov","t0":0},
   {"tipo":"ass","arquivo":"legenda.ass"}]
Fontes do ASS: pasta 'fontes' da config (fontsdir). Saída marcada bt709/tv nas 4 pontas, AAC 48 kHz 256k.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import ffbin, run, ler_json, fontes_dir, esc_filtro, probe, video_stream, fps_de


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--video', required=True); ap.add_argument('--ass'); ap.add_argument('--enfase'); ap.add_argument('--audio')
    ap.add_argument('--out', default='FINAL.mp4'); ap.add_argument('--camadas'); ap.add_argument('--nvenc', action='store_true')
    ap.add_argument('--crf', type=int, default=18); ap.add_argument('--grao', type=float, default=0)
    a = ap.parse_args()
    if a.camadas: camadas = ler_json(a.camadas)
    else: camadas = ([{'tipo': 'ass', 'arquivo': a.enfase}] if a.enfase else []) + ([{'tipo': 'ass', 'arquivo': a.ass}] if a.ass else [])
    v = video_stream(probe(a.video)); fps = fps_de(v)
    ins = ['-i', a.video]; fc = []; cur = '[0:v]'; k = 1; tag = 0
    fd = fontes_dir()
    for c in camadas:
        if c['tipo'] == 'ass':
            f = f"ass='{esc_filtro(c['arquivo'])}'" + (f":fontsdir='{esc_filtro(fd)}'" if fd else '')
            fc.append(f'{cur}{f}[l{tag}]'); cur = f'[l{tag}]'; tag += 1
        elif c['tipo'] == 'video':
            ins += ['-itsoffset', str(c.get('t0', 0)), '-i', c['arquivo']]
            fc.append(f'[{k}:v]format=rgba,fps={fps}[o{k}];{cur}[o{k}]overlay=eof_action=pass:format=auto[l{tag}]')
            cur = f'[l{tag}]'; k += 1; tag += 1
    if a.grao: fc.append(f'{cur}noise=alls={a.grao}:allf=t[l{tag}]'); cur = f'[l{tag}]'; tag += 1
    fc.append(f'{cur}format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv[vout]')
    cmd = [ffbin(), '-y', '-v', 'error', *ins]
    if a.audio: cmd += ['-i', a.audio]
    cmd += ['-filter_complex', ';'.join(fc), '-map', '[vout]']
    if a.audio: cmd += ['-map', f'{k}:a', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest']
    enc = (['-c:v', 'h264_nvenc', '-preset', 'p5', '-tune', 'hq', '-rc', 'vbr', '-cq', str(a.crf), '-b:v', '0'] if a.nvenc
           else ['-c:v', 'libx264', '-crf', str(a.crf), '-preset', 'slow', '-tune', 'film'])
    cmd += enc + ['-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                  '-color_range', 'tv', '-movflags', '+faststart', a.out]
    run(cmd)
    d = float(probe(a.out)['format']['duration'])
    print(f'→ {a.out}  ({d:.2f} s, {len(camadas)} camadas)')


if __name__ == '__main__':
    main()
