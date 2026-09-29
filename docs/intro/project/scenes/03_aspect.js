/* sAspect：橫式、直式各有專屬版面
 * 一個畫框在 16:9 與 9:16 之間變形，框內三個區塊從「一列」重排成「一欄」，說明不是等比縮小。 */
function sAspect(t, T, pulse) {
  const top = L_head(t, '橫直式各有版面', '同一支片自動重排，不是等比縮小');
  const bx = SAFE.x, bw = SAFE.w, by = top + MIN * .04, bh = SAFE.b - by;
  const cx = bx + bw / 2, cy = by + bh / 2;
  // 兩種畫框各自塞進可用區域
  const fitBox = r => { let w = bw * .92, h = w / r; if (h > bh * .92) { h = bh * .92; w = h * r; } return [w, h]; };
  const [lw, lh] = fitBox(16 / 9), [pw, ph] = fitBox(9 / 16);
  // 第 3 拍變成直式，第 6.5 拍變回橫式
  const k = tw(t, BEAT * 2.5, BEAT * 1.5, 'io') * (1 - tw(t, BEAT * 6, BEAT * 1.2, 'io'));
  const fw = lerp(lw, pw, k), fh = lerp(lh, ph, k), fx = cx - fw / 2, fy = cy - fh / 2;
  const a = tw(t, -.25, .5);

  ctx.save(); ctx.globalAlpha = a; camPush(1 + t * .008);
  glow(cx, cy, Math.max(fw, fh) * .6, STYLE.c.a1, .18 + pulse * .12);
  card(fx, fy, fw, fh, { r: MIN * .02 });
  strokeRR(fx, fy, fw, fh, MIN * .02, rgba(STYLE.c.a1, .7), 2);

  // 框內三個區塊：橫式一列、直式一欄
  const pad = Math.min(fw, fh) * .07;
  for (let i = 0; i < 3; i++) {
    const rw = (fw - pad * 4) / 3, rh = fh - pad * 2 - fh * .22;
    const row = { x: fx + pad + i * (rw + pad), y: fy + pad + fh * .22, w: rw, h: rh };
    const cw = fw - pad * 2, ch = (fh - pad * 4 - fh * .12) / 3;
    const col = { x: fx + pad, y: fy + pad + fh * .12 + i * (ch + pad), w: cw, h: ch };
    const ki = clamp(k * 1.3 - i * .15);
    const r = { x: lerp(row.x, col.x, ki), y: lerp(row.y, col.y, ki), w: lerp(row.w, col.w, ki), h: lerp(row.h, col.h, ki) };
    const c = accent(i);
    fillRR(r.x, r.y, r.w, r.h, MIN * .01, rgba(c, .16));
    strokeRR(r.x, r.y, r.w, r.h, MIN * .01, rgba(c, .55), 1.5);
    const lz = Math.min(r.w, r.h) * .09;
    fillRR(r.x + lz, r.y + lz, r.w * .5, lz, lz / 2, rgba(c, .8));
    fillRR(r.x + lz, r.y + lz * 2.6, r.w * .72, lz * .7, lz / 3, rgba(STYLE.c.fg, .25));
  }
  // 標題列（框內頂部）
  fillRR(fx + pad, fy + pad, fw * lerp(.4, .6, k), Math.min(fw, fh) * .045, MIN * .01, rgba(STYLE.c.fg, .5));
  ctx.restore();

  // 比例標籤：跟著畫框右上角，文字在兩種比例間交叉淡入
  const lz = fz('h3'), lx = fx + fw, ly = fy - lz * .7;
  txt('16:9', lx, ly, { size: lz, fam: 'mono', weight: 600, color: STYLE.c.a1, align: 'right', alpha: a * (1 - k), maxW: SAFE.w * .3 });
  txt('9:16', lx, ly, { size: lz, fam: 'mono', weight: 600, color: STYLE.c.a3, align: 'right', alpha: a * k, maxW: SAFE.w * .3 });
}
