/* Map → route（路線依序串起新店圖釘、4 new stores）｜ Campaign report +38%（KPI 卡＋走勢線） */
function sRoute(t, T, pulse) {
  udBg(t);
  const [A, B] = udCells([1.25, 1]);
  udCard(t, -.2, A, 0, () => {
    uiCard(A.x, A.y, A.w, A.h);
    const m = Math.min(A.w, A.h) * .035, mx = A.x + m, my = A.y + m, mw = A.w - m * 2, mh = A.h - m * 2;
    uiMap(mx, my, mw, mh, { seed: 5, r: Math.min(A.w, A.h) * .07 });
    const pts = [[.12, .8], [.3, .52], [.5, .68], [.68, .36], [.86, .56]].map(([u, v]) => [mx + u * mw, my + v * mh]);
    uiRoute(pts, prog(t, BEAT * .8, BEAT * 4.4), { pin: Math.min(A.w, A.h) * .09, glyph: 'pin', t });
    uiResult(A.x + A.w / 2, my + mh * .15, '4 new stores', clamp((t - BEAT * 5) / .5), { glyph: 'pin', col: UIC.ok, size: Math.min(A.w, A.h) * .06 });
  });
  udCard(t, -.12, B, 1, () => uiKPI(B.x, B.y, B.w, B.h, t, {
    label: 'Campaign report', sub: 'Spring launch · conversions', pre: '+', post: '%', to: 38, start: BEAT * 1.2, dur: BEAT * 2.6,
    badge: 'Above target', badgeAt: BEAT * 5, spark: [2, 2.4, 2.2, 3, 3.4, 3.1, 4.2, 4.8, 5.6], icon: 'bell', col: STYLE.c.a3 }));
}
