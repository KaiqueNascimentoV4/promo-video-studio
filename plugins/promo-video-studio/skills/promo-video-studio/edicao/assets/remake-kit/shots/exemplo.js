/* exemplo.js — um shot de demonstração do contrato (apague quando os grupos G1–G4 existirem).
 * IIFE, helpers com prefixo do grupo, função pura de F. Cores escritas como AMOSTRADAS na ref (a troca de paleta
 * acontece sozinha no seek). Números = coordenadas nativas da ref (PROJECT.W × PROJECT.H). */
(function () {
  const C = window.C, SHOT = window.SHOT, W = C.W, H = C.H;
  const EX_card = (p) => {
    const y = C.lerp(H * 0.62, H * 0.5, C.E.outExpo(p)), s = C.lerp(0.94, 1, C.E.outExpo(p));
    return C.abs(W * 0.5 - W * 0.22, y - H * 0.12,
      `<div style="width:${W * 0.44}px;height:${H * 0.24}px;border-radius:${H * 0.03}px;background:#ffffff;opacity:${p.toFixed(3)};` +
      `transform:scale(${s});box-shadow:0 ${H * 0.02}px ${H * 0.06}px rgba(0,0,0,.08)"></div>`);
  };
  SHOT({
    id: 'EX01', f0: 0, f1: (C.TOTAL || 90) - 1,
    render(lf, F) {
      const n = (C.TOTAL || 90) - 1;
      const pIn = C.prog(lf, 4, 18, C.E.outExpo);                     // cartão entra (expo.out, sem overshoot)
      const words = ['Seu', 'texto', 'aqui'];
      const vis = words.map((_, i) => lf >= 22 + i * 6);              // palavra a palavra, layout fixo
      const lineVis = C.wordLine(words, { size: H * 0.07, cx: W / 2, baseline: H * 0.52, color: '#111111', tracking: -0.03, visible: vis });
      const cx = C.kf(lf, [[30, W * 0.85], [60, W * 0.62, C.E.inOutQuad]]), cy = C.kf(lf, [[30, H * 0.9], [60, H * 0.56, C.E.inOutQuad]]);
      const press = C.kf(lf, [[60, 0], [62, 1], [66, 0]]);
      return C.bg('#ff4c00') + EX_card(pIn) + lineVis.html +
        (lf >= 60 ? C.ripple(cx, cy, C.prog(lf, 60, 72), { r: H * 0.05, color: 'rgba(0,0,0,.35)' }) : '') +
        C.cursor(cx, cy, { press }) + C.textAt(`f${F}`, W * 0.02, H * 0.06, { size: H * 0.03, color: '#ffffff' });
    },
  });
})();
