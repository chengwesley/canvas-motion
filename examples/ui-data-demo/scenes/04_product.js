/* Card → 360°（價格卡轉一圈換成特價）｜ Weight → bold（大字字重跟著滑桿變粗） */
function sProduct(t, T, pulse) {
  udBg(t);
  const [A, B] = udCells([.78, 1.15]);
  const spin = spring(t, BEAT * 1.6, .85, .55), sale = spin > .75;
  udCard(t, -.2, A, 0, () => {
    const h = A.h * (PORT ? .96 : 1), w = Math.min(A.w, h * .76);
    uiPriceCard(A.x + A.w / 2, A.y + A.h / 2, w, h, spin, {
      front: { name: 'Aero Speaker', sub: 'Wireless · 24h battery', cur: '$', price: sale ? '119' : '149', was: sale ? '$149' : '', tag: sale ? 'Save 20%' : 'New' },
      back: { title: 'What’s included', items: ['Free 2-day shipping', '2-year warranty', '30-day returns'] }, glyph: 'bolt' });
  });
  udCard(t, -.12, B, 1, () => {
    uiCard(B.x, B.y, B.w, B.h);
    const hd = udHead(B, 'plus', 'Typeface weight', 'Inter Display', UIC.ink), pad = hd.pad;
    const p = E.io(prog(t, BEAT * 1.4, BEAT * 4.6)), sy = B.y + B.h - pad - B.h * .1, wy = (hd.bottom + sy) / 2 - B.h * .02;
    const wt = uiWeight(B.x + B.w / 2, wy, 'Bold', p, { size: Math.min(B.w * .28, B.h * .3), gradient: [UIC.ink, STYLE.c.a1] });
    const press = prog(t, BEAT * 1.2, BEAT * 1.4) * (1 - prog(t, BEAT * 4.6, BEAT * 4.9));
    uiSlider(B.x + pad * 1.4, sy, B.w - pad * 2.8, p, { label: String(wt), press, h: Math.min(B.w, B.h) * .024 });
  });
}
