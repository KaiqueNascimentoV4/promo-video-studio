/* brand.js — tokens da marca NOVA (do MIV) e as bandas de troca de cor da marca ANTIGA (da referência).
 * Logos: SVG recortado justo (viewBox = caixa da tinta) em assets/brand/; aspect = largura/altura do viewBox.
 * SWAP_BANDS: cada cor saturada da ref com matiz em [lo, hi] (graus) e saturação ≥ minS é re-matizada para
 * target + (h − center) × spread, com saturação × sMul e luminosidade + lAdd (padrão: preservadas).
 * Amostre a cor da marca antiga NOS PIXELS da ref (SPEC.md → tokens) e meça o matiz antes de definir a banda. */
window.BRAND = {
  name: 'Cliente', short: 'CLI',
  primary: '#FF6720', secondary: '#2C4528', ink: '#000000', paper: '#FFFFFF',
  site: 'cliente.com.br', whatsapp: '',
  logo: null,                       // ex.: { src: 'assets/brand/logo.svg', aspect: 235.48 / 112.10 }
};
window.SWAP_BANDS = [
  // ex.: marca antiga vermelho-alaranjada (matiz 0–29°) → laranja do cliente (19,6°)
  // { lo: 0, hi: 29, minS: 0.35, center: 16, target: 19.6, spread: 0.45 },
];
