/* sHook：一支 HTML，就是一支影片
 * 前兩拍打出 frame(t)，下方播放軸隨時間前進（程式 = 時間軸）；第 3 拍起兩行大字揭示。 */
function sHook(t, T, pulse) {
  const cx = W / 2, cy = H * pick(.5, .46);
  const l1 = '一支 HTML', l2 = '就是一支影片';
  const size = fit(l2, SAFE.w * pick(.8, 1), fz('hero'), 800, 'display');
  ctx.save(); camPush(1 + t * .012);
  glow(cx, cy, MIN * .55 * (1 + pulse * .12), STYLE.c.a2, .3);

  // 1. 打字：frame(t)
  const code = 'frame(t)', cz = fz('h3');
  const nch = Math.round(clamp(tw(t, -.1, BEAT * 1.6, 'lin')) * code.length);
  const cyC = cy - size * 1.75;
  // 以完整字串置中後固定左緣，打字時文字才不會左右漂移
  const full = measure(code, { size: cz, fam: 'mono', weight: 600 });
  const cm = txt(code.slice(0, nch), cx - full.w / 2, cyC, { size: cz, fam: 'mono', weight: 600, color: STYLE.c.a1, maxW: SAFE.w });
  if (Math.floor(t / (BEAT / 2)) % 2 === 0 || nch < code.length) {
    const cxr = cx - full.w / 2 + cm.w + cz * .12;
    ctx.fillStyle = STYLE.c.a1; ctx.fillRect(cxr, cyC - cz * .45, Math.max(2, cz * .08), cz * .9);
  }

  // 2. 兩行大字：遮罩由下往上揭示
  [[l1, cy - size * .6, BEAT * 2, STYLE.c.fg], [l2, cy + size * .6, BEAT * 3.5, null]].forEach(([s, y, at, col]) => {
    const p = tw(t, at, .55, 'expo'), m = measure(s, { size, weight: 800, fam: 'display' });
    reveal(p, cx - m.w / 2 - size, y - size * .72, m.w + size * 2, size * 1.44, () => {
      txtB(s, cx, y + (1 - p) * size * .5, { size, weight: 800, fam: 'display', align: 'center', maxW: SAFE.w,
        color: col, gradient: col ? null : [STYLE.c.a1, STYLE.c.a2, STYLE.c.a3] });
    });
  });

  // 3. 播放軸：每拍一個刻度，播放頭跟著 t 前進
  const yT = cy + size * 1.55, x0 = cx - SAFE.w * pick(.3, .42), x1 = cx + SAFE.w * pick(.3, .42);
  const pa = tw(t, BEAT, .5);
  ctx.save(); ctx.globalAlpha = pa;
  line(x0, yT, x1, yT, STYLE.c.cardLine, 2);
  const beats = Math.round(T / BEAT);
  for (let i = 0; i <= beats; i++) {
    const x = lerp(x0, x1, i / beats), hit = t >= i * BEAT ? Math.exp(-(t - i * BEAT) * 5) : 0;
    line(x, yT - MIN * (.008 + hit * .012), x, yT + MIN * (.008 + hit * .012), i * BEAT <= t ? STYLE.c.a1 : STYLE.c.cardLine, 2);
  }
  const ph = lerp(x0, x1, clamp(t / T));
  line(x0, yT, ph, yT, STYLE.c.a1, 3);
  circle(ph, yT, MIN * .011 * (1 + pulse * .3), STYLE.c.a1);
  ctx.restore();
  txt(`t = ${t.toFixed(2)}s`, x1, yT + MIN * .045, { size: fz('cap'), fam: 'mono', weight: 500, color: STYLE.c.mute,
    align: 'right', alpha: pa, maxW: SAFE.w * .4 });
  ctx.restore();
}
