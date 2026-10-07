"""Configuração LOCAL da skill (PROMO_VIDEO_STUDIO_CONFIG ou ~/.claude/editar-video.json; nunca no repositório).

  python config.py --show                     mostra a config
  python config.py --check                    confere ferramentas e caminhos e diz o que falta
  python config.py --set CHAVE VALOR          ex.: --set sfx "D:/Packs/SFX"   (chaves: sfx, trilhas, fontes, luts,
                                              saida, whatsapp_padrao, ffmpeg, ffprobe, idioma)
  python config.py --mapear-sfx               procura no pack de SFX um arquivo por categoria e grava sfx_mapa
"""
import argparse, importlib.util, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import cfg, salvar_cfg, CONFIG

CATEGORIAS = {  # categoria -> palavras procuradas no nome do arquivo (ordem = preferência)
    'whoosh': ['fast swoosh', 'swoosh', 'whoosh', 'woosh'],
    'whoosh_grave': ['low sub whoosh', 'sub whoosh', 'low whoosh'],
    'impacto': ['impact', 'hit'],
    'sub': ['sub boom', 'boom', 'sub drop'],
    'obturador': ['shutter', 'camera click', 'camera'],
    'clique': ['click', 'interface', 'tap'],
    'digitacao': ['type', 'typing', 'keyboard'],
    'check': ['correct', 'success', 'check', 'done'],
    'riser': ['riser'],
}
AUDIO_EXT = ('.wav', '.mp3', '.aif', '.aiff', '.flac', '.ogg', '.m4a')


def mapear_sfx(pasta):
    arquivos = []
    for raiz, _, fs in os.walk(pasta):
        for f in fs:
            if f.lower().endswith(AUDIO_EXT): arquivos.append(os.path.join(raiz, f))
    mapa = {}
    for cat, chaves in CATEGORIAS.items():
        for k in chaves:
            hit = sorted([a for a in arquivos if k in os.path.basename(a).lower()], key=lambda a: (len(os.path.basename(a)), a))
            if hit: mapa[cat] = hit[0]; break
    return mapa, len(arquivos)


def check():
    c = cfg(); ok = True
    print(f'config: {CONFIG} ({"existe" if c else "ainda não criada"})')
    for b in ('ffmpeg', 'ffprobe', 'node', 'npx'):
        p = c.get(b) if b in c else shutil.which(b)
        print(f'  {"✔" if p else "✘"} {b}: {p or "NÃO ENCONTRADO"}'); ok &= bool(p) or b == 'npx'
    if shutil.which('ffmpeg') or c.get('ffmpeg'):
        fl = subprocess.run([c.get('ffmpeg') or 'ffmpeg', '-hide_banner', '-filters'], capture_output=True, text=True).stdout
        for f in ('subtitles', 'zscale', 'tonemap', 'loudnorm', 'deesser', 'sidechaincompress'):
            has = f' {f} ' in fl
            print(f'    {"✔" if has else "✘"} filtro {f}'); ok &= has
    for mod in ('numpy', 'cv2', 'PIL', 'faster_whisper'):
        has = importlib.util.find_spec(mod) is not None
        print(f'  {"✔" if has else "✘"} python: {mod}'); ok &= has
    for mod in ('rembg',):
        print(f'  {"✔" if importlib.util.find_spec(mod) else "·"} python (opcional): {mod}')
    for k in ('sfx', 'trilhas', 'fontes', 'luts', 'saida'):
        v = c.get(k)
        print(f'  {"✔" if v and os.path.isdir(v) else "·"} {k}: {v or "(não configurado — pergunte ao usuário e use --set)"}')
    if c.get('sfx_mapa'): print(f'  ✔ sfx_mapa: {len(c["sfx_mapa"])} categorias')
    print('PRONTO' if ok else 'FALTAM ITENS OBRIGATÓRIOS (ver references/ambiente.md)')
    return ok


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--show', action='store_true'); ap.add_argument('--check', action='store_true')
    ap.add_argument('--set', nargs=2, metavar=('CHAVE', 'VALOR')); ap.add_argument('--mapear-sfx', action='store_true')
    a = ap.parse_args()
    c = cfg()
    if a.set:
        c[a.set[0]] = a.set[1]; salvar_cfg(c); print(f'{a.set[0]} = {a.set[1]}')
    if a.mapear_sfx:
        if not c.get('sfx'): sys.exit('configure antes: --set sfx <pasta do pack>')
        mapa, n = mapear_sfx(c['sfx']); c['sfx_mapa'] = mapa; salvar_cfg(c)
        print(f'{n} arquivos de áudio no pack; mapeado:')
        for k, v in mapa.items(): print(f'  {k:13s} {os.path.relpath(v, c["sfx"])}')
        faltam = [k for k in CATEGORIAS if k not in mapa]
        if faltam: print('sem arquivo para:', ', '.join(faltam), '(sfx.py sintetiza essas)')
    if a.show or not (a.set or a.check or a.mapear_sfx):
        import json; print(json.dumps(c, ensure_ascii=False, indent=2) if c else f'(vazia) {CONFIG}')
    if a.check: sys.exit(0 if check() else 1)
