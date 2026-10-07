"""Leitura do project.json e caminhos do projeto de remake (compartilhado pelas ferramentas)."""
import json, os, shutil, sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def proj():
    with open(os.path.join(ROOT, 'project.json'), encoding='utf-8') as f: return json.load(f)


def salvar_proj(p):
    with open(os.path.join(ROOT, 'project.json'), 'w', encoding='utf-8') as f: json.dump(p, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT, 'project.js'), 'w', encoding='utf-8') as f:
        f.write('/* gerado por tools/analisar_ref.py a partir de project.json — edite o JSON e rode: python tools/analisar_ref.py --so-project */\n')
        f.write('window.PROJECT = ' + json.dumps(p, ensure_ascii=False) + ';\n')


def fps_str(p): return f"{p['FPS_NUM']}/{p['FPS_DEN']}"


def ff(nome='ffmpeg'):
    e = os.environ.get(nome.upper())
    if e and os.path.exists(e): return e
    w = shutil.which(nome)
    if not w: sys.exit(f'{nome} não encontrado no PATH')
    return w


def fonte_sistema():
    for c in ('C:/Windows/Fonts/arial.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if os.path.exists(c): return c
    return None
