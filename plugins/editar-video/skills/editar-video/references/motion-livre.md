# Motion livre: como fazer qualquer ideia

O motion não precisa caber num padrão. Este arquivo é o método para transformar **qualquer conceito** em vídeo determinístico e renderizável, com o catálogo de ideias que o time já entregou (sem nomes de clientes) para servir de faísca.

## 1. Da ideia ao plano
1. **Uma frase**: "o espectador vê ___ virar ___ e entende ___". Se não cabe numa frase, a ideia ainda não está pronta.
2. **Movimento-assinatura**: o único movimento que alguém descreveria para um amigo (a câmera atravessa a palavra; o mundo fica cinza e só o extintor fica vermelho; o celular desenhado preenche o formulário sozinho).
3. **Mundo visual**: fundo (papel, escuro, cor sólida da marca, foto do cliente), 1–2 fontes, 1 cor de acento, textura (grão, papel quadriculado, scanline).
4. **Mapa de batidas** com tempos absolutos, amarrado à locução (palavras) ou à trilha (batidas/drop).
5. **Quadros-chave** (3–4 stills) antes do render completo. O usuário aprova o look nos stills, não no vídeo de 6 min de render.

## 2. Qual engine (todas determinísticas: o quadro é função pura do tempo)

| engine | quando | como |
|---|---|---|
| **HyperFrames** (HTML + GSAP, `npx hyperframes`) | tipografia, UI, cartões, kinetic type, legenda embutida, registro de ~400 efeitos prontos; o mais rápido de iterar | `npx hyperframes init` → `index.html` com timeline GSAP pausada → `npx hyperframes check` → `render`. Se as skills `hyperframes*` estiverem instaladas, siga-as (contrato, CLI, catálogo). |
| **Motor de quadro próprio** (kit do remake: `assets/remake-kit/core.js` + `render.mjs`) | controle total por quadro, dados medidos, câmeras e efeitos SVG, iframes vivos (UI real mockada), canvas | `window.seekF(F)` monta o HTML do quadro F; Playwright fotografa. O mesmo kit do modo 5, sem referência. |
| **Compositor Python** (numpy + OpenCV + PIL) | footage pesado: recorte da pessoa, câmera que se move sobre vídeo, colagem, matte sandwich, grão, light leak | `render.py` com `quadro(n) -> imagem`, cache por quadro, encode via pipe para o ffmpeg |
| **p5.js / p5.brush** | pintura, desenho à mão, escrita que se escreve sozinha | se a skill `p5-paint-animation` estiver instalada, use-a |
| **Three.js** (dentro do HyperFrames ou do motor) | 3D real: anel de fotos em volta do logo, objetos girando, câmera voando | relógio do Three.js = tempo do quadro, nunca `requestAnimationFrame` |
| **rough.js** | doodles, setas e caixas desenhadas, estilo quadro branco | seed fixa por elemento; draw-on por `stroke-dashoffset` |

**Assets que não existem**: objetos 3D cromados, mockups e texturas podem ser gerados por IA de imagem (ChatGPT, Nano Banana/ElevenLabs Image). Peça "transparent background (PNG), no text, no logos"; tela de celular em verde puro `#00FF00` para encaixar a UI depois por homografia. Se a geração for por navegador, **nunca envie um rascunho que já estava na caixa de texto do usuário**: limpe antes.

## 3. Acabamento que separa "animação" de "filme"
- **Motion blur real**: render a 120 fps → `ffmpeg -vf "tmix=frames=4:weights='1 1 1 1',select='not(mod(n+1\,4))',setpts=N/(30*TB),fps=30"` (obturador 360°). Custa 4× o render. Alternativa barata: 3 subamostras por quadro no compositor.
- **Grão no ffmpeg** (`noise=alls=6:allf=t`), não em SVG `feTurbulence` (pesado e lento no Chromium).
- **Profundidade**: DOF falso (cópias desfocadas mascaradas em anel), sombra difusa 8%, parallax em 2–3 planos.
- **Câmera viva**: deriva de 1–3% do quadro por segundo (`sine.inOut`) em plano parado.
- **Encode**: ruído leve + `-tune film` evita banding; ruído forte por quadro em crf baixo explode o arquivo (já virou 800 MB). Use `noise=alls=2` + crf 19.

## 4. Render: armadilhas de máquina
- Chromium fica lento em sessão longa (memória): renderize em **blocos de 30–300 quadros** com reinício automático; 2–3 blocos em paralelo no máximo.
- Iframe escondido com `display:none` perde layout e rolagem: esconda com `opacity:0`.
- `clip-path: circle()` não interpola em tween: anime um número (proxy) e escreva o estilo no `onUpdate`. 72% já cobre os cantos de 1080×1920.
- Fontes variáveis podem falhar em algumas engines: tenha a versão estática.
- Formulário real de site (gera lead/cobrança): **nunca** preencha o vivo. Faça uma cópia local com rede bloqueada (`fetch` stubado + `route.abort` no Playwright).
- Contador com serif (Playfair): use algarismos tabulares e alinhados (`font-feature-settings:"lnum","tnum"`); o padrão é oldstyle.

## 5. Catálogo de ideias já entregues (faísca, não fôrma)
| ideia | o que acontece | serviu para |
|---|---|---|
| **Modo vistoria** | o mundo vira cinza e só os equipamentos-chave ficam na cor, com rótulos HUD rastreados por fluxo óptico | prestador de serviço técnico mostrando o que o leigo não vê |
| **Rewind em LED** | painel de LED volta no tempo até a data do evento, e o filme começa ali | cobertura de evento |
| **Drop na multidão** | pausa da música em "portas abertas" → drop no corte para a multidão colorida, com o relógio real do clipe | evento, energia |
| **ASCII vermelho** | o quadro vira caracteres na cor da marca no clímax | transição de impacto |
| **Anel 3D de fotos** | fotos do evento orbitam o logo em 3D | fecho institucional |
| **Mão de pixel no CTA** | cursor/mão pixelada aperta "Chame no WhatsApp" | CTA divertido |
| **Editorial cromado** | objetos 3D cromados (gerados por IA) sobre papel, serif fina, primeiro plano desfocado, motion suave com blur real | oferta de serviço "premium e limpo" sobre áudio de WhatsApp |
| **Explainer desenhado** | papel quadriculado de engenharia, doodles rough.js que se desenham, celular desenhado com cópia viva do formulário real sendo preenchida (digitação, toques, rolagem, upload) | "como funciona" de uma plataforma, passo a passo |
| **Colagem/revista** | recortes de fotos e vídeos entrando secos sobre fundo branco, texto central fixo em caixa branca | vídeo pessoal/afetivo (o usuário preferiu cortes secos e retos a "bouncy") |
| **Remake de filme de marca** | ver modo 5 | adaptar um filme de referência para um cliente |

Quando a ideia nova der certo, acrescente uma linha aqui (genérica) e publique a skill.
