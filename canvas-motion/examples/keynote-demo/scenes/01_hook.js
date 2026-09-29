/* 冷開場：兩行大字依拍點遮罩揭示，第二行漸層並參與 bloom */
function sHook(t, T, pulse) {
  const l1 = '一支 HTML', l2 = '就是一支影片', cap = 'Canvas 逐幀繪製 × WebAudio 即時配樂';
  const size = fit(l2, SAFE.w, fz('hero'), 800, 'display');
  const cx = W / 2, cy = H * pick(.46, .44);
  ctx.save(); camPush(1 + t * .012);
  const out = 1; // 有轉場的幕不自己淡出，交給轉場
  [[l1, cy - size * .62, .15, STYLE.c.fg], [l2, cy + size * .62, BEAT * 2, null]].forEach(([s, y, at, col]) => {
    const p = tw(t, at, .55, 'expo');
    const m = measure(s, { size, weight: 800, fam: 'display' });
    reveal(p, cx - m.w / 2 - size, y - size * .7, m.w + size * 2, size * 1.4, () => {
      txtB(s, cx, y + (1 - p) * size * .5, { size, weight: 800, fam: 'display', align: 'center', alpha: out,
        color: col, gradient: col ? null : [STYLE.c.a1, STYLE.c.a2, STYLE.c.a3] });
    });
  });
  const pc = tw(t, BEAT * 4, .5);
  txt(cap, cx, cy + size * 1.78 + (1 - pc) * 12, { size: fz('cap'), fam: 'mono', weight: 500, color: STYLE.c.mute,
    align: 'center', alpha: pc * out, maxW: SAFE.w, track: .04 });
  line(cx - SAFE.w * .15, cy + size * 1.38, cx + SAFE.w * .15, cy + size * 1.38, rgba(STYLE.c.a1, .6 * out), 2, tw(t, BEAT * 3.5, .6));
  ctx.restore();
}
