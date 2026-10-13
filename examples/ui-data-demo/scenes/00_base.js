/* ui-data-demo 共用：淡藍底的柔光桌布＋卡片格線（橫式一列、直式一欄） */
/** 柔光桌布：四團淡色光烘焙成 1/4 解析度的貼圖（全螢幕漸層每格重畫很貴），放大後緩慢漂移 */
function udBg(t) {
  const img = cached('udbg', W / 4, H / 4, (c, w, h) => {
    c.fillStyle = STYLE.c.bg; c.fillRect(0, 0, w, h);
    [[.12, .15, STYLE.c.a1, .16], [.9, .85, UIC.ok, .13], [.75, .08, STYLE.c.card, .8], [.25, .95, STYLE.c.a3, .08]].forEach(([u, v, col, a]) => {
      const g = c.createRadialGradient(u * w, v * h, 0, u * w, v * h, Math.max(w, h) * .6);
      g.addColorStop(0, rgba(col, a)); g.addColorStop(1, rgba(col, 0)); c.fillStyle = g; c.fillRect(0, 0, w, h);
    });
  }, [STYLE.c.bg, STYLE.c.a1, STYLE.c.a3]);
  ctx.drawImage(img, -W * .03 + Math.sin(t * .15) * W * .02, -H * .03 + Math.cos(t * .12) * H * .02, W * 1.06, H * 1.06);
}

/** ratios：每張卡的寬高比（橫式用）。回傳 [{x, y, w, h}]，整組置中 */
function udCells(ratios) {
  const n = ratios.length, gap = MIN * .06;
  if (PORT) {
    const w = SAFE.w, h = Math.min((SAFE.h - gap * (n - 1)) / n, w * .95), top = H / 2 - (h * n + gap * (n - 1)) / 2;
    return ratios.map((r, i) => ({ x: W / 2 - w / 2, y: top + i * (h + gap), w, h }));
  }
  let h = SAFE.h * .84, sum = ratios.reduce((a, r) => a + r, 0);
  if (h * sum + gap * (n - 1) > SAFE.w) h = (SAFE.w - gap * (n - 1)) / sum;
  let x = W / 2 - (h * sum + gap * (n - 1)) / 2;
  return ratios.map(r => { const c = { x, y: H / 2 - h / 2, w: h * r, h }; x += h * r + gap; return c; });
}
/** 卡片標頭：圖示磚＋標題＋副標，回傳標頭底部 y */
function udHead(c, glyph, title, sub, col) {
  const pad = Math.min(c.w, c.h) * .08, ts = Math.min(c.h * .13, c.w * .13);
  uiIconTile(c.x + pad, c.y + pad, ts, glyph, { col: col || STYLE.c.a1 });
  const mw = c.w - pad * 2 - ts * 1.3;
  txtB(title, c.x + pad + ts * 1.3, c.y + pad + ts * .32, { size: ts * .36, weight: 700, color: UIC.ink, fit: { lines: 1, min: .6 }, maxW: mw, ui: true });
  txtB(sub, c.x + pad + ts * 1.3, c.y + pad + ts * .76, { size: ts * .28, weight: 500, color: UIC.sub, fit: { lines: 1, min: .6 }, maxW: mw, ui: true });
  return { pad, bottom: c.y + pad + ts };
}
const udMid = c => [c.x + c.w / 2, c.y + c.h / 2];
/** 卡片進場（uiIn 彈入）＋落定後緩慢漂浮（第 i 張相位錯開），讓畫面不會完全靜止 */
function udCard(t, start, c, i, draw) {
  const f = Math.sin(t * 1.6 + i * 1.9) * MIN * .005 * clamp(t - start - .6);
  ctx.save(); ctx.translate(0, f); uiIn(t, start, ...udMid(c), draw); ctx.restore();
}
