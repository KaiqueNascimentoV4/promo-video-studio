"""Publica as melhorias da skill no repositório do time (commit + push).

Uso: python scripts/publicar.py "o que mudou"
- Procura o repositório git subindo a partir desta pasta (funciona quando a skill é um clone/link do repo).
- Bloqueia a publicação se achar algo que não pode ir para um repo público (tokens, chaves, e-mails, caminhos de usuário).
- Se a skill foi instalada como plugin (cópia em cache, sem git), explica como clonar e abrir um pull request.
"""
import os, re, subprocess, sys
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

REPO_URL = 'https://github.com/KaiqueNascimentoV4/promo-video-studio'
msg = ' '.join(sys.argv[1:]).strip()
if not msg or msg.startswith('-'): sys.exit(__doc__ if msg in ('-h', '--help') else 'Uso: python publicar.py "o que mudou na skill"')

here = os.path.dirname(os.path.realpath(__file__)); root = here
while root and not os.path.isdir(os.path.join(root, '.git')):
    up = os.path.dirname(root); root = None if up == root else up
if not root:
    sys.exit(f'Esta cópia da skill não é um repositório git (provavelmente instalada como plugin).\n'
             f'Para contribuir: git clone {REPO_URL}, aplique as mudanças em plugins/<plugin>/skills/<skill>/ '
             f'e abra um pull request (ou peça para quem mantém o repo publicar).')

def git(*a, check=True): return subprocess.run(['git', '-C', root, *a], capture_output=True, text=True, encoding='utf-8', check=check)

BAD = [(r'gh[pousr]_[A-Za-z0-9]{20,}', 'token do GitHub'), (r'sk-[A-Za-z0-9_-]{20,}', 'chave de API'), (r'xi-api-key|ELEVENLABS_API_KEY\s*=\s*\S+', 'chave ElevenLabs'),
       (r'[A-Za-z]:[\\/]+Users[\\/]+(?!<you>)[A-Za-z0-9_.-]+', 'caminho de usuário'), (r'/Users/(?!<you>)[a-z0-9_.-]+/', 'caminho de usuário'),
       (r'[A-Za-z0-9._%+-]+@(?!htfonts|anthropic)[A-Za-z0-9.-]+\.(com|br|io|net)\b', 'e-mail')]
# nomes de clientes (listas LOCAIS, fora do repo), um por linha
for _bl in ('~/.claude/promo-video-studio-clientes.txt', '~/.claude/editar-video-clientes.txt'):
    _bl = os.path.expanduser(_bl)
    if os.path.exists(_bl):
        for nome in open(_bl, encoding='utf-8').read().splitlines():
            if nome.strip() and not nome.startswith('#'): BAD.append((r'(?i)' + re.escape(nome.strip()), 'nome de cliente'))
problems = []
changed = [l[3:].strip().strip('"') for l in git('status', '--porcelain', '-uall').stdout.splitlines()]
for rel in changed:
    p = os.path.join(root, rel)
    if os.path.realpath(p) == os.path.realpath(__file__): continue  # o próprio verificador contém os padrões
    if not os.path.isfile(p) or os.path.splitext(p)[1].lower() in ('.ttf', '.otf', '.png', '.jpg', '.mp3', '.wav', '.mp4'): continue
    txt = open(p, encoding='utf-8', errors='ignore').read()
    for pat, what in BAD:
        for m in re.finditer(pat, txt): problems.append(f'{rel}: {what} → {m.group(0)[:40]}')
if problems:
    sys.exit('Publicação bloqueada — remova antes de publicar (o repositório é público):\n  ' + '\n  '.join(problems))
if not changed: sys.exit('Nada para publicar.')

try: subprocess.run(['claude', 'plugin', 'validate', root], check=True, capture_output=True)
except FileNotFoundError: pass
except subprocess.CalledProcessError as e: sys.exit('claude plugin validate falhou:\n' + (e.stdout or b'').decode(errors='ignore') + (e.stderr or b'').decode(errors='ignore'))

git('add', '-A')
git('commit', '-m', msg + '\n\nCo-Authored-By: Claude <noreply@anthropic.com>')
r = git('push', check=False)
if r.returncode: sys.exit('Commit feito, mas o push falhou:\n' + r.stderr)
print('Publicado:', git('log', '-1', '--format=%h %s').stdout.strip(), '→', REPO_URL)
print('O time recebe na próxima atualização automática (ou com /plugin marketplace update promo-video-studio).')
