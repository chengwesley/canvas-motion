/* Visits → sales（訪客粒子匯進結果膠囊）｜ Rings → closed（三圈目標合攏、Goal hit） */
function sConvert(t, T, pulse) {
  udBg(t);
  const [A, B] = udCells([1.1, 1.1]);
  udCard(t, -.2, A, 0, () => {
    uiCard(A.x, A.y, A.w, A.h);
    const hd = udHead(A, 'cart', 'Store traffic', '3,200 visits today'), pad = hd.pad;
    const src = { x: A.x + pad * 1.2, y: hd.bottom + A.h * .06, w: A.w - pad * 2.4, h: A.h * .36 }, dst = { x: A.x + A.w / 2, y: A.y + A.h * .72 };
    const r = uiParticlesTo(t, BEAT * 1, BEAT * 3.4, src, dst, { n: 56, seed: 21, size: Math.min(A.w, A.h) * .011 });
    const s = Math.round(447 * r.arrived) + ' sales';
    uiResult(dst.x, dst.y, s, clamp((t - BEAT * 1.2) / .5), { glyph: 'cart', col: UIC.ok, bump: r.bump, size: Math.min(A.w, A.h) * .075 });
    uiBadge(dst.x, A.y + A.h * .87, '14% conversion', clamp((t - BEAT * 5) / .45), { size: Math.min(A.w, A.h) * .045, align: 'center' });
  });
  udCard(t, -.12, B, 1, () => {
    uiCard(B.x, B.y, B.w, B.h);
    const hd = udHead(B, 'star', 'Daily goals', 'Sales · Leads · Calls', STYLE.c.a3), pad = hd.pad;
    const rr = Math.min(B.w * .27, (B.y + B.h * .74 - hd.bottom) * .42), cx = B.x + B.w / 2, cy = (hd.bottom + B.y + B.h * .74) / 2 + B.h * .02;
    const from = [.62, .45, .78], ps = from.map((f, i) => lerp(f, 1, E.io(prog(t, BEAT * (1.4 + i * .5), BEAT * (3.4 + i * .5)))));
    uiGoalRings(cx, cy, rr, ps, { cols: [STYLE.c.a1, UIC.ok, UIC.warn] });
    const done = prog(t, BEAT * 4.5, BEAT * 4.5 + .55), avg = ps.reduce((a, v) => a + v, 0) / 3;
    if (done < .3) txtB(Math.round(avg * 100) + '%', cx, cy, { size: rr * .36, weight: 800, color: UIC.ink, align: 'center', alpha: 1 - done / .3, maxW: rr * 1.4, ui: true });
    uiCheck(cx, cy, rr * .28, done, { burst: true });
    uiResult(cx, B.y + B.h * .86, 'Goal hit', clamp((t - BEAT * 5) / .5), { glyph: 'check', col: UIC.ok, size: Math.min(B.w, B.h) * .062 });
  });
}
