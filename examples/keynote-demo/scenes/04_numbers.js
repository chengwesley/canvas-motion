/* 數字牆：三個數字依拍點滾動出現；橫式三欄、直式三列 */
const DEMO_NUM = [[6, '腳本範本'], [5, '風格包'], [3, '畫面比例']];
function sNumbers(t, T, pulse) {
  const a = 1, n = DEMO_NUM.length;
  ctx.save(); camPush(1.03 - t * .008);
  DEMO_NUM.forEach(([v, lab], i) => {
    const at = -.1 + i * BEAT * 1.5, p = tw(t, at, .7, 'expo');
    const cx = PORT ? W / 2 : lerp(SAFE.x, SAFE.r, (i + .5) / n);
    const cy = PORT ? lerp(SAFE.y + SAFE.h * .12, SAFE.b - SAFE.h * .18, i / (n - 1)) : H * .47;
    const ns = fz(PORT ? .26 : .3), hit = Math.exp(-Math.max(0, t - at - .55) * 6) * (t > at + .55 ? 1 : 0);
    ctx.save(); ctx.globalAlpha = clamp(p) * a; ctx.translate(cx, cy); ctx.scale(1 + hit * .06, 1 + hit * .06); ctx.translate(-cx, -cy);
    txtB(countUp(p, 0, v), cx, cy, { size: ns, fam: 'mono', weight: 600, align: 'center', gradient: [accent(i), accent(i + 1)] });
    ctx.restore();
    txt(lab, cx, cy + ns * .74, { size: fz('h3'), weight: 700, align: 'center', alpha: clamp(p) * a, color: STYLE.c.fg });
    if (i < n - 1) {
      const la = tw(t, at + .3, .5) * a * .7;
      if (PORT) line(W * .35, cy + ns * .95, W * .65, cy + ns * .95, STYLE.c.cardLine, 1, la);
      else line(lerp(SAFE.x, SAFE.r, (i + 1) / n), H * .32, lerp(SAFE.x, SAFE.r, (i + 1) / n), H * .66, STYLE.c.cardLine, 1, la);
    }
  });
  ctx.restore();
}
