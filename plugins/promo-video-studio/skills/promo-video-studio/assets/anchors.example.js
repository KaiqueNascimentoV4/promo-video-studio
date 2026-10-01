// Narration anchors: seconds (inside the narration audio file) where each key word starts.
// Generate with: python scripts/words.py narracao.mp3 --lang pt   → pick the words you need.
// Keep the SAME keys across languages/takes; only the times change.
window.K = {
  __offset: 0.4,   // narration starts this many seconds into the video
  __dur: 20.0,     // total video duration (narration end + ~3 s for the end card)
  // --- example script: "Toda semana sua equipe perde 6 horas com planilhas. 6 horas. Com o Acme, os relatórios se montam sozinhos… Acme. Trabalhe no que importa." ---
  gancho: 0.00, seis: 2.10, horas: 2.45, planilhas: 3.30, repete: 4.40,
  marca1: 6.20, relatorios: 7.60, sozinhos: 8.90, painel: 10.80, compartilha: 12.40,
  marca2: 15.20, tagline: 15.80, fim: 17.10,
};
