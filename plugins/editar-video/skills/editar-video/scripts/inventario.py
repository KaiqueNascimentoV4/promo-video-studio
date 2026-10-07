"""Inventário dos brutos: ffprobe de cada vídeo → inventario.json + tabela.

  python inventario.py PASTA_OU_ARQUIVOS... [--out inventario.json]

Mostra resolução, orientação real (com rotação), fps, duração, codec, HDR (HLG/PQ), bits e áudio, e avisa:
HLG → converter para Rec.709 antes do grade; rotação no metadado; fps misturados; vídeo sem áudio.
"""
import argparse, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import probe, video_stream, fps_de, rotacao, gravar_json

EXT = ('.mp4', '.mov', '.m4v', '.mkv', '.avi', '.mts', '.mxf', '.webm')


def listar(entradas):
    out = []
    for e in entradas:
        if os.path.isdir(e):
            for f in sorted(os.listdir(e)):
                if f.lower().endswith(EXT): out.append(os.path.join(e, f))
        else: out += sorted(glob.glob(e)) or [e]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('entradas', nargs='+'); ap.add_argument('--out', default='inventario.json')
    a = ap.parse_args()
    itens, avisos = [], []
    for p in listar(a.entradas):
        try: info = probe(p)
        except SystemExit as e: avisos.append(f'{os.path.basename(p)}: não abriu ({e})'); continue
        v = video_stream(info)
        if not v: continue
        au = next((s for s in info['streams'] if s.get('codec_type') == 'audio'), None)
        rot = rotacao(v); w, h = v.get('width'), v.get('height')
        if abs(rot) in (90, 270): w, h = h, w
        trc = v.get('color_transfer') or ''
        hdr = 'HLG' if trc == 'arib-std-b67' else 'PQ' if trc == 'smpte2084' else ''
        it = dict(arquivo=os.path.abspath(p), nome=os.path.basename(p), w=w, h=h, rotacao=rot,
                  orientacao='vertical' if h > w else 'horizontal' if w > h else 'quadrado',
                  fps=round(fps_de(v), 3), duracao=round(float(info['format'].get('duration', 0)), 3),
                  codec=v.get('codec_name'), pix_fmt=v.get('pix_fmt'), hdr=hdr,
                  primaries=v.get('color_primaries'), transfer=trc, audio=bool(au),
                  audio_codec=au.get('codec_name') if au else None, audio_hz=int(au.get('sample_rate', 0)) if au else 0)
        itens.append(it)
        if hdr: avisos.append(f'{it["nome"]}: HDR {hdr} → converter para Rec.709 antes do grade (cor.py / cortar.py fazem)')
        if rot: avisos.append(f'{it["nome"]}: rotação {rot}° no metadado (o ffmpeg aplica sozinho; confira o enquadramento)')
        if not au: avisos.append(f'{it["nome"]}: sem áudio')
    if not itens: sys.exit('nenhum vídeo encontrado')
    fpss = sorted({i['fps'] for i in itens})
    if len(fpss) > 1: avisos.append(f'fps misturados {fpss}: a entrega sai em 30 fps (ou no fps do formato); clipes de 60/100 fps dão câmera lenta limpa')
    total = sum(i['duracao'] for i in itens)
    print(f'{"arquivo":28s} {"res":>11s} {"orient":>10s} {"fps":>7s} {"dur":>7s} {"codec":>6s} {"HDR":>4s} {"áudio":>6s}')
    for i in itens:
        print(f'{i["nome"][:28]:28s} {str(i["w"])+"x"+str(i["h"]):>11s} {i["orientacao"]:>10s} {i["fps"]:7.3f} {i["duracao"]:7.1f} {i["codec"][:6]:>6s} {i["hdr"] or "-":>4s} {("sim" if i["audio"] else "não"):>6s}')
    print(f'{len(itens)} vídeos, {total/60:.1f} min no total')
    for x in avisos: print('⚠', x)
    gravar_json(a.out, dict(itens=itens, avisos=avisos, total_s=round(total, 2)))
    print('→', a.out)


if __name__ == '__main__':
    main()
