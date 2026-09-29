/* 收尾：環形 Logo 畫出 → 字標逐字展開 → 標語；最後一小節由配樂收束和弦 */
function sOutro(t, T, pulse) {
  const cx = W / 2, cy = H * pick(.44, .42), R = MIN * pick(.075, .09);
  const lp = tw(t, .05, .8, 'io');
  glow(cx, cy - R * 1.6, R * 5 * (.8 + lp * .4), STYLE.c.a2, .25 + pulse * .1);
  ctx.save(); ctx.translate(cx, cy - R * 1.6); ctx.rotate(t * .4);
  ring(0, 0, R, STYLE.c.a1, R * .16, lp); ring(0, 0, R * .58, STYLE.c.a3, R * .12, tw(t, .3, .7, 'io'), Math.PI / 2);
  ctx.restore();
  const word = 'Canvas Motion', wp = tw(t, BEAT * 2, .9, 'out');
  const size = fit(word, SAFE.w, fz('h1'), 800, 'display');
  txtB(typeOn(word, wp), cx, cy + R * .5, { size, weight: 800, fam: 'display', align: 'center', track: lerp(.3, .02, wp) });
  const tp = tw(t, BEAT * 4, .6);
  txt('讓內容，動起來。', cx, cy + R * .5 + size * 1.05 + (1 - tp) * 10, { size: fz('h3'), color: STYLE.c.mute, align: 'center', alpha: tp, maxW: SAFE.w });
}
