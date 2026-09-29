/* 流程：一拍半一步，節點沿線點亮；橫式水平、直式垂直 */
const DEMO_FLOW = [['素材', '網址／文件／口述'], ['分鏡', '切點對齊小節'], ['場景', '每幕只講一件事'], ['驗證', '橫直式逐幕截圖'], ['發布', 'Artifact 或 MP4']];
function sFlow(t, T, pulse) {
  const a = tw(t, -.25, .5), n = DEMO_FLOW.length, st0 = .5, gap = BEAT * 1.8;
  const title = txt('從素材到成片', PORT ? SAFE.x : W / 2, SAFE.y + fz('h2') * .6,
    { size: fz('h2'), weight: 800, fam: 'display', align: PORT ? 'left' : 'center', alpha: a });
  const pts = DEMO_FLOW.map((_, i) => PORT
    ? { x: SAFE.x + MIN * .07, y: lerp(title.bottom + H * .09, SAFE.b - H * .05, i / (n - 1)) }
    : { x: lerp(SAFE.x + SAFE.w * .08, SAFE.r - SAFE.w * .08, i / (n - 1)), y: H * .56 });
  const R = MIN * pick(.045, .06), prog2 = clamp((t - st0) / (gap * (n - 1)));
  ctx.save(); ctx.globalAlpha = a;
  line(pts[0].x, pts[0].y, pts[n - 1].x, pts[n - 1].y, STYLE.c.cardLine, 2);
  line(pts[0].x, pts[0].y, pts[n - 1].x, pts[n - 1].y, STYLE.c.a1, 3, E.io(prog2));
  DEMO_FLOW.forEach(([name, sub], i) => {
    const on = tw(t, st0 + i * gap, .45, 'back'), P = pts[i], cur = t >= st0 + i * gap && (i === n - 1 || t < st0 + (i + 1) * gap);
    if (cur) glow(P.x, P.y, R * 3.2, accent(i), .5 + pulse * .4);
    circle(P.x, P.y, R, STYLE.c.bg);
    ring(P.x, P.y, R, on > 0 ? accent(i) : STYLE.c.cardLine, 2.5, on > 0 ? on : 1);
    txtB(String(i + 1), P.x, P.y, { size: R * .8, fam: 'mono', weight: 600, align: 'center', color: on > 0 ? STYLE.c.fg : STYLE.c.mute });
    const la = clamp(on) * a;
    if (PORT) {
      txt(name, P.x + R * 1.8, P.y - fz('body') * .45, { size: fz('h3'), weight: 700, alpha: la, maxW: SAFE.r - P.x - R * 2 });
      txt(sub, P.x + R * 1.8, P.y + fz('h3') * .62, { size: fz('body') * .85, color: STYLE.c.mute, alpha: la, maxW: SAFE.r - P.x - R * 2 });
    } else {
      const cw = SAFE.w / n * .95;
      txt(name, P.x, P.y + R * 2.1, { size: fz('h3'), weight: 700, align: 'center', alpha: la });
      txt(sub, P.x, P.y + R * 2.1 + fz('h3') * 1.05, { size: fit(sub, cw, fz('cap'), 500), weight: 500, color: STYLE.c.mute, align: 'center', alpha: la });
    }
  });
  ctx.restore();
}
