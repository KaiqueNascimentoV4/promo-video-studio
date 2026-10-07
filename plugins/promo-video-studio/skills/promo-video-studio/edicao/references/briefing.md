# Banco de perguntas do briefing

Textos prontos para o **AskUserQuestion**: no máximo 4 perguntas por chamada e 2–4 opções por pergunta. O "Outro" aparece sozinho. A opção recomendada vai primeiro, com "(Recomendado)".
Faça **uma ou duas chamadas** por rodada, nunca um interrogatório. Pule o que o usuário já disse ou o que dá para descobrir sozinho (resolução e fps vêm do `inventario.py`, não pergunte).

Perguntas de **texto livre** (caminho de pasta, contexto do cliente, link) não cabem no AskUserQuestion. Faça em uma mensagem curta, numerada, e espere a resposta.

---

## A. Material (texto livre, sempre primeiro nos modos 1–3)

> Me manda os takes: a pasta ou os arquivos (pode arrastar para cá). Se tiver roteiro, referência de estilo ou observação do cliente, manda junto.

Depois de receber: `python scripts/inventario.py <pasta>` e conte o que achou (quantos clipes, duração total, HLG ou não, vertical ou horizontal). Isso substitui perguntas técnicas.

## B. Formato e duração (uma chamada, 2 perguntas)

**"Qual o formato de entrega?"** (header `Formato`)
- `9:16 Reels/TikTok (Recomendado)`: 1080×1920, 30 fps
- `4:5 feed`: 1080×1350
- `1:1 quadrado`: 1080×1080
- `16:9 horizontal`: 1920×1080 (YouTube, LinkedIn, X)

**"Qual a duração-alvo?"** (header `Duração`)
- `Até 30 s (Recomendado)`: o mais assistido até o fim
- `30–60 s`
- `60–90 s`
- `O que o material pedir`: a decupagem decide

## C. Legenda (modos 1–4)

**"Qual estilo de legenda?"** (header `Legenda`)
- `Dinâmica palavra a palavra (Recomendado)`: a linha se enche no tempo da fala, Helvetica Bold apertada, 1–3 palavras
- `Dinâmica com destaque`: palavra ativa com cor/escala, blocos de ênfase e palavra gigante atrás da pessoa
- `Cinematográfica / 3D`: palavras no espaço e atrás da pessoa, câmera atravessando (precisa de talking head limpo)
- `Simples`: frase limpa sem animação

Se for "com destaque", pergunte a **cor de destaque**: cor da marca (do MIV), branco + 1 acento, ou amarelo clássico.
Modo 4 sem narração: troque por **"Tem texto falado?"** (sim, com legenda / não, só tipografia de motion).

## D. Trilha e SFX (modos 1, 2, 4)

**"Qual trilha?"** (header `Trilha`)
- `Pack do time (Recomendado)`: escolho pela energia e pelo arco (caminho no config)
- `Gerar com IA`: ElevenLabs Music, se o conector estiver ligado; descrevo a estrutura no tempo
- `Biblioteca livre`: licença comercial OK, com o link e a licença guardados
- `Sem trilha`

**"Quanto SFX?"** (header `SFX`, modos 1 e 4; no modo 2 o padrão é "leve")
- `Na medida (Recomendado)`: um som por movimento importante (whoosh na passagem, clique no pop, impacto na palavra-herói)
- `Leve`: só cortes e entrada de texto
- `Carregado`: estilo trailer; evite em vídeo institucional

## D2. Locução (quando o vídeo precisa de voz e não há fala gravada: modos 4 e 5, ou narração extra)

**"Como fazemos a voz?"** (header `Voz`)
- `Voz local natural (Recomendado)`: gerada no PC (Chatterbox), grátis, com emoção ajustável
- `Clonar uma voz autorizada`: o cliente/locutor manda 6–15 s de áudio limpo
- `ElevenLabs`: se o conector estiver ligado (pago por crédito)
- `Sem locução`: só texto + trilha

Depois: **"Qual timbre?"** (header `Timbre`) → `Feminina` / `Masculina`, e o tom (sóbrio, natural ou empolgado).

## E. Cliente, marca e CTA

**"É para um cliente/marca?"** (header `Cliente`)
- `Sim, tenho o MIV`: o manual de identidade visual (PDF/imagens)
- `Sim, sem MIV`: mando logo, site e Instagram; você deriva a paleta
- `Não, é pessoal/interno`

**"Como fecha o vídeo?"** (header `CTA`)
- `Botão "Chame no WhatsApp" (Recomendado)`: animado, com toque e check
- `@perfil / link`
- `Logo + slogan`
- `Sem CTA`

Se for WhatsApp: pergunte o número no texto (ou use `whatsapp_padrao` do config).

## F. Copy (quando houver cliente ou o vídeo for criado do zero)

**"E a copy/roteiro?"** (header `Copy`)
- `Gerar pelo contexto do cliente (Recomendado)`: faço as perguntas de contexto e mando 2–3 ganchos para aprovar
- `Já tenho o texto`: uso o seu, revisado para ritmo
- `É o que a pessoa fala no take`: só decupagem (modos 1–3)

Se for gerar: as perguntas de contexto estão em `copy.md` §1 (texto livre, numeradas).

## G. Look (modos 1–2)

**"Qual look de cor?"** (header `Cor`)
- `Frio/neutro da casa (Recomendado)`: limpo, levemente azulado, pele natural
- `Seguir o MIV`: quente ou frio conforme a marca
- `Quente/dourado`: lifestyle, gastronomia, pôr do sol
- `P&B com trecho de virada`: preto e branco num momento de impacto

## H. Motion (modos 1 e 4)

Modo 1, **"Quais cenas de motion?"** (header `Motion`, multiSelect)
- `Palavra gigante atrás da pessoa`: só com talking head limpo
- `Cartão de vidro de UI`: números, listas, checks sincronizados com a fala
- `Tela de pergunta/virada`: o quadro encolhe e vira foto sobre a cor da marca
- `Deixa comigo`: escolho 3–5 momentos pela fala

Modo 4: o briefing de ideia está em `modo-4-motion-complexo.md` §1. A ideia pode ser **qualquer coisa**; não se prenda às famílias conhecidas.

## I. Modo 5 (remake)

Primeiro o **aviso de custo** (SKILL.md §5) e o "sim". Depois, em texto livre e numerado:
1. O vídeo de referência (arquivo ou link).
2. O **MIV do cliente** (ou logo + site + Instagram).
3. O que troca: nome da marca, logo, paleta (hex ou "derivar do logo"), UI de plataforma (ex.: LinkedIn → Instagram), rostos/telas (de onde vêm as imagens do cliente).
4. Copy: **manter a estrutura da ref com o texto do cliente** ou **gerar pelo contexto** (então `copy.md`).
5. Footage do cliente disponível (vídeo institucional, fotos, prints) e a qualidade dele.

Depois preencha o prompt (`assets/prompt-remake.md`) e mostre a versão preenchida antes de começar a Fase 0.
