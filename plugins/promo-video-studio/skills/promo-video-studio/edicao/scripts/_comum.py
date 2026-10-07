"""Funções compartilhadas pelos scripts da skill editar-video (config local, ffmpeg, formatos, JSON)."""
import json, os, shutil, subprocess, sys

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

CONFIG = os.path.expanduser(os.environ.get('PROMO_VIDEO_STUDIO_CONFIG', '~/.claude/editar-video.json'))
FORMATOS = {'9:16': (1080, 1920), '4:5': (1080, 1350), '1:1': (1080, 1080), '16:9': (1920, 1080)}


def cfg():
    """Configuração local (caminhos pessoais ficam FORA do repositório)."""
    try:
        with open(CONFIG, encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return {}


def salvar_cfg(c):
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, 'w', encoding='utf-8') as f: json.dump(c, f, ensure_ascii=False, indent=2)


def ffbin(nome='ffmpeg'):
    """ffmpeg/ffprobe: variável FFMPEG/FFPROBE, config, ou PATH."""
    env = os.environ.get(nome.upper())
    if env and os.path.exists(env): return env
    c = cfg().get(nome)
    if c and os.path.exists(c): return c
    if nome == 'ffprobe' and os.environ.get('FFMPEG'):
        p = os.path.join(os.path.dirname(os.environ['FFMPEG']), 'ffprobe' + ('.exe' if os.name == 'nt' else ''))
        if os.path.exists(p): return p
    p = shutil.which(nome)
    if not p: sys.exit(f'{nome} não encontrado. Instale (ver references/ambiente.md) ou rode: config.py --set {nome} <caminho>')
    return p


def run(cmd, check=True, quiet=False):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and r.returncode:
        sys.exit(f'falhou: {" ".join(map(str, cmd))[:400]}\n{r.stderr[-2000:]}')
    return r


def probe(path):
    r = run([ffbin('ffprobe'), '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', path])
    return json.loads(r.stdout)


def fps_de(stream):
    n, d = (stream.get('avg_frame_rate') or stream.get('r_frame_rate') or '30/1').split('/')
    return float(n) / float(d or 1) if float(n) else 30.0


def video_stream(info):
    return next((s for s in info.get('streams', []) if s.get('codec_type') == 'video'), None)


def rotacao(stream):
    for sd in stream.get('side_data_list', []) or []:
        if 'rotation' in sd: return int(sd['rotation'])
    return int((stream.get('tags') or {}).get('rotate', 0))


def dims(formato):
    if formato in FORMATOS: return FORMATOS[formato]
    if 'x' in formato:
        w, h = formato.lower().split('x'); return int(w), int(h)
    sys.exit(f'formato desconhecido: {formato} (use 9:16, 4:5, 1:1, 16:9 ou LxA)')


def ler_json(p):
    with open(p, encoding='utf-8') as f: return json.load(f)


def gravar_json(p, obj):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f: json.dump(obj, f, ensure_ascii=False, indent=1)


def fontes_dir():
    """Pasta de fontes da config (Helvetica etc.), senão None (o libass cai nas fontes do sistema)."""
    d = cfg().get('fontes')
    return d if d and os.path.isdir(d) else None


def esc_filtro(p):
    """Escapa caminho para dentro de um filtro do ffmpeg (subtitles=..., fontsdir=...)."""
    p = os.path.abspath(p).replace('\\', '/')
    return p.replace(':', '\\:').replace("'", "\\'")
