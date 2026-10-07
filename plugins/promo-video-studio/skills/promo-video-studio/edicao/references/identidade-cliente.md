# Identidade do cliente (MIV) → tokens do vídeo

## 1. O que pedir
- **MIV (Manual de Identidade Visual)**: PDF ou imagens. É a fonte da verdade.
- Sem MIV: **logo vetorial** (SVG/PDF/AI; PNG transparente grande no mínimo), site, Instagram, 2–3 posts que o cliente considera "a cara da marca".
- Fotos/vídeos institucionais, prints do produto, fachada, equipe (com autorização de uso).
- Dados fixos: nome exato (grafia, maiúsculas), slogan, telefone/WhatsApp, @, site, cidade, tempo de mercado. **Pergunte se o site está atualizado**: já aconteceu de o site dizer "15 anos" e o certo ser 20.

## 2. O que extrair do MIV (escreva em `marca.json` no projeto)
```json
{
  "nome": "…", "grafia_curta": "…",
  "cores": { "primaria": "#…", "secundaria": "#…", "acento": "#…", "fundo_claro": "#…", "fundo_escuro": "#…", "texto": "#…" },
  "proporcao_uso": "60% neutro / 30% primária / 10% acento",
  "fontes": { "titulo": "…", "texto": "…", "substituta_livre": "…" },
  "logo": { "principal": "assets/brand/logo.svg", "simbolo": "assets/brand/simbolo.svg", "negativo": "…", "area_respiro": "x = altura do símbolo", "tamanho_min_px": 120 },
  "tom": "técnico e confiável / jovem e direto / …",
  "proibicoes": ["não distorcer", "não aplicar sobre foto sem caixa", "…"],
  "contato": { "whatsapp": "…", "site": "…", "instagram": "@…" }
}
```
- Cores do PDF podem vir em CMYK/Pantone: converta para sRGB hex e **confira no pixel** de uma peça digital oficial (site/Instagram), que manda no vídeo.
- Fonte paga que o time não tem: use a substituta livre mais próxima (Google Fonts) e avise.

## 3. Sem MIV: derivar do logo
`python scripts/paleta.py logo.png --n 5` → cores dominantes (ignora branco, preto e transparente), com hex, % de área e uma sugestão de papéis (primária = mais saturada e com mais área). **Confirme com o usuário.** Gere a versão escura e a clara da primária (L ± 15%) para fundos e gradientes.

## 4. Como a marca entra no vídeo
- **Logo como máscara** (`mask-image`): qualquer cor ou gradiente sem redesenhar; SVG recortado justo (viewBox = caixa da tinta) para posicionar pela tinta.
- **Cor da marca**: fundos de cortina/herói, palavra de destaque da legenda, botão do CTA, sublinhados. Um acento por quadro.
- **Tipografia da marca** em títulos e cartões; a legenda corrida continua na sans bold da casa, a não ser que o MIV proíba.
- Fecho: logo com área de respiro + contato (WhatsApp) + 1 linha. Parado ≥ 2 s.
- Paleta trocada em motion HTML: aplique a cor via variáveis CSS ou, no remake, pelo filtro único de troca de bandas (`brand.js`).

## 5. Checagem de marca (antes de entregar)
Grafia do nome em todas as telas · logo sem distorção e com respiro · cores conferidas no pixel (`qc.py --cor "#HEX"` mede o delta E) · contato correto · nenhum número ou claim inventado · nenhuma marca de terceiro (no remake, varrer a cor antiga).
