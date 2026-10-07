# Cor: técnica primeiro, look depois

## 1. Diagnóstico (`inventario.py` já mostra)
| `color_transfer` | o que é | ação |
|---|---|---|
| `arib-std-b67` | **HDR HLG** (iPhone, muitos Androids) | converter para Rec.709 **antes** de qualquer grade |
| `smpte2084` | HDR PQ | converter (tonemap) |
| `bt709` / vazio | SDR | grade direta |
| S-Log/V-Log (Sony/Panasonic, perfil de câmera) | log | LUT de conversão da câmera → depois o look |

Converter HLG errado (ou não converter) foi o erro mais grave já cometido: "cor horrível", lavada e magenta.

**HLG → Rec.709** (o que o `cor.py` faz):
```
zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p
```
Marque a saída nas 4 pontas: `-color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv` (e `setparams` no filtro final).
Trabalhe em 8 bits `gbrp` depois da conversão. **Nunca** `gbrp10le` com `eq` na cadeia: um bug escureceu um plano de Y 78 para 43.

## 2. Looks (`cor.py --look`)
| look | quando | receita base |
|---|---|---|
| `frio` (padrão da casa) | talking head, corporativo, tech | leve azul nas sombras/médios, pele preservada; fundo com R−B ≈ −16; contraste +8%; saturação −5% |
| `neutro` | quando o MIV pede fidelidade de cor (produto, comida da marca) | só balanço de branco e exposição |
| `quente` | lifestyle, gastronomia, pôr do sol, afetivo | laranja nos médios, sombras levemente teal |
| `pb` | trecho de virada/acusação | `hue=s=0` + contraste +15% + grão |
| `tecnico` | modo 3 | só a conversão HDR→SDR e o nível |
| `--lut arquivo.cube` | o time tem LUT própria | `lut3d=` depois da conversão (intensidade com `--lut-mix 0.6`) |

Amarelos de objetos (quadro dourado, parede creme) brigando com o look frio? Neutralize **só a faixa amarela** com `selectivecolor` em vez de esfriar a imagem inteira.
**Não** use light leak de pack sobre look frio: esquenta e levanta o preto.

## 3. Consistência entre planos (`cor.py --medir`)
1. Para cada plano, meça **só o fundo** (parede/céu), não o quadro inteiro (a roupa engana): Y médio, p5 (preto), saturação e R−B.
2. Alvo: Y ≈ 106 ± 2 (talking head interno), p5 ≈ 16–20, R−B ≈ −16 (frio).
3. `cor.py --medir` grava `trim.json` com o ajuste por plano; `cortar.py` aplica. No máximo 2 passadas. **Medir duas vezes seguidas acumula a correção em dobro**: o `trim.json` guarda o que já foi aplicado.
4. Nada estourado: cheque o p99 da pele < 235.

## 4. Footage fraco (celular comprimido, WhatsApp)
- Upscale com Real-ESRGAN antes do grade, se for para tela grande (`realesr-animevideov3` x2 é rápido; `x4plus` é melhor e muito mais lento).
- Grão leve no fim (`noise=alls=4:allf=t`) disfarça o banding.
- Não aplique recorte da pessoa nem palavra atrás dela: fica artificial.
