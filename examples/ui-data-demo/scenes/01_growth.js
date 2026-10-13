/* 0 → 12,480（KPI 卡數字滾動＋成長標籤）｜ Bars → trend（長條彈起 → 趨勢線 → +200%） */
function sGrowth(t, T, pulse) {
  udBg(t);
  const [A, B] = udCells([1.05, 1.2]);
  udCard(t, -.2, A, 0, () => uiKPI(A.x, A.y, A.w, A.h, t, {
    label: 'Subscribers', sub: 'Newsletter · this month', to: 12480, start: BEAT, dur: BEAT * 2.7,
    badge: '+18% this month', badgeAt: BEAT * 4, spark: [3, 4, 3.6, 5, 4.8, 6.2, 7, 6.6, 8.4, 9.8], icon: 'user' }));
  udCard(t, -.2 + .08, B, 1, () => {
    uiCard(B.x, B.y, B.w, B.h);
    const hd = udHead(B, 'chart', 'Weekly revenue', 'Last 8 weeks', UIC.ok), pad = hd.pad;
    const bx = B.x + pad, by = hd.bottom + B.h * .14, bw = B.w - pad * 2, bh = B.y + B.h - pad - by;
    uiBars(bx, by, bw, bh, [.22, .3, .27, .4, .48, .55, .7, .9], prog(t, BEAT * .8, BEAT * 3), prog(t, BEAT * 3.1, BEAT * 4.9),
      { labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8'], t });
    const z = Math.min(B.h * .055, B.w * .05), bwid = uiBadge(0, 0, '+200%', 0, { size: z });
    uiBadge(B.x + B.w - pad - bwid, hd.bottom + B.h * .06, '+200%', clamp((t - BEAT * 5) / .45), { size: z });
  });
}
