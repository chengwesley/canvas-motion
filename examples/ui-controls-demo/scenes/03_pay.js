/* Card → paid（信用卡滑進刷卡機、螢幕轉綠、Paid 膠囊彈出）與 Sketch → app（線框依序長成 Daily Focus 畫面） */
function sPay(t, T, pulse) {
  demoBg(t);
  const tIn = BEAT * 2.25, tHit = BEAT * 3, tPaid = BEAT * 4, tM0 = BEAT * 5.5, tM1 = BEAT * 9.5;
  // 左：刷卡機與卡片
  const pw = PORT ? W * .34 : MIN * .3, pcx = PORT ? W * .5 : W / 2 - MIN * .4, pcy = PORT ? H * .3 : H * .58;
  const slotY = pcy - pw * .65 + pw * 1.3 * .02, cw = pw * .78, ch = cw * .63;
  const R1 = { x: pcx - pw * .7, y: slotY - ch * 1.3, w: pw * 1.4, h: pw * 1.3 + ch * 1.3 };
  demoEnter(t, 0, R1, () => {
    const k1 = spring(t, -.1, 1.25, .62), above = slotY - ch * .62, down = slotY + ch * .12;
    const k2 = E.in(prog(t, tIn, tHit)), cy = lerp(above, down, k2) - Math.max(0, 1 - clamp(k1)) * pw * .3;
    const cx = lerp(pcx - pw * 1.1, pcx, clamp(k1, 0, 1.06)), rot = lerp(-.35, 0, clamp(k1, 0, 1.08));
    uiCreditCard(cx, cy, cw, { rot, sheen: prog(t, tPaid, tPaid + .8) });
    const im = impact(t, tHit, .06, .3), py = pcy + pw * .65;
    ctx.save(); ctx.translate(pcx, py); ctx.scale(im.sx, im.sy); ctx.translate(-pcx, -py);
    uiPOS(pcx, pcy, pw, clamp(spring(t, tPaid, 2.4, .5), 0, 1.05), { amount: '£290.00', paidLabel: 'Approved' });
    ctx.restore();
    uiBurst(pcx, slotY - ch * .2, pw * .55, t, tPaid + .2, { n: 12 });
    uiPill(pcx, down - ch / 2 - pw * .13, 'Paid', t, tPaid + .2, { kind: 'ok', solid: true, col: UIC.ok, size: pw * .075 });
  }, { card: false });
  demoCap('Card → paid', pcx, PORT ? pcy + pw * .65 + MIN * .06 : pcy + pw * .65 + MIN * .07, clamp(spring(t, -.3, 1.5, .62) * 2));

  // 右：手機裡的線框 → App
  const ph = PORT ? H * .38 : Math.min(H * .76, MIN * .8), fcx = PORT ? W * .5 : W / 2 + MIN * .4, fcy = PORT ? H * .7 : H * .46;
  const R2 = { x: fcx - ph * .245, y: fcy - ph / 2, w: ph * .49, h: ph };
  demoEnter(t, 1, R2, () => {
    const mp = E.io(prog(t, tM0, tM1));
    framePhone(fcx, fcy, ph, { lift: .7 }, b => {
      uiWireMorph(b.x, b.y, b.w, b.h, mp, { title: 'Daily Focus', sub: 'Tuesday · 3 sessions', value: 86, ringLabel: 'of daily goal',
        tiles: [{ v: '4h 12m', l: 'Focus' }, { v: '12', l: 'Tasks' }, { v: '7 days', l: 'Streak' }], cta: 'Start session' });
      if (mp > 0 && mp < 1) { const sy = b.y + b.h * (.08 + mp * .9); glow(b.x + b.w / 2, sy, b.w * .5, STYLE.c.a1, .25 * Math.sin(mp * Math.PI)); }
    });
  }, { card: false, cap: PORT ? null : 'Sketch → app' });
  if (PORT) demoCap('Sketch → app', fcx, fcy + ph / 2 + MIN * .05, clamp(spring(t, -.2, 1.5, .62) * 2));
}
