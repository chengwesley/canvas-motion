/* 成果 → 行動呼籲：四項待辦依序打勾（全部完成的樣子），視窗縮到後面淡出，Logo 和「免費試用」按鈕彈出並停住一小節 */
const END_TASKS = ['整理週會重點', '回覆設計稿意見', '準備下週簡報', '預約客戶訪談'];
function sEnd(t, T, pulse) {
  backdrop(t, { amt: .35 });
  const cta = BEAT * 6, out = E.io(prog(t, cta - .15, cta + .2));
  const ww = PORT ? SAFE.w : Math.min(SAFE.w * .62, SAFE.h * 1.2), wh = PORT ? SAFE.h * .62 : ww * .62;
  const wx = W / 2 - ww / 2, wy = H / 2 - wh / 2;
  ctx.save(); ctx.globalAlpha *= 1 - out; ctx.translate(W / 2, H / 2); ctx.scale(1 - out * .15, 1 - out * .15); ctx.translate(-W / 2, -H / 2);
  frameWindow(wx, wy, ww, wh, { title: 'Notely', lift: .7 }, b => {
    ctx.fillStyle = UI.paper; ctx.fillRect(b.x, b.y, b.w, b.h);
    txtB('本週待辦', b.x + b.w * .08, b.y + b.h * .14, { size: MIN * .036, weight: 800, color: UI.ink, maxW: b.w * .8, ui: true });
    const rh = b.h * .17, ch = rh * .76, cw = b.w * .84;
    END_TASKS.forEach((s, i) => {
      const y = b.y + b.h * .32 + i * rh, x = b.x + b.w * .08, at = BEAT * (1 + i * .75), done = clamp((t - at) / .5);
      ctx.fillStyle = done >= 1 ? mixc(UI.paper, STYLE.c.a2, .07) : UI.paper; ctx.strokeStyle = UI.line; ctx.lineWidth = 1.5;
      fillRR(x, y - ch / 2, cw, ch, ch * .25); strokeRR(x, y - ch / 2, cw, ch, ch * .25);
      txtB(s, x + ch * .9, y, { size: ch * .36, weight: 600, color: done >= 1 ? UI.sub : UI.ink, maxW: cw - ch, ui: true });
      if (done <= 0) { ctx.strokeStyle = UI.line; ctx.lineWidth = 2; strokeRR(x + ch * .3, y - ch * .15, ch * .3, ch * .3, ch * .08); }
      uiCheck(x + ch * .45, y, ch * .24, done, { col: STYLE.c.a2, burst: i === END_TASKS.length - 1 });
    });
  });
  ctx.restore();
  // 行動呼籲：Logo＋產品名，按鈕彈出，最後一小節停住（只有呼吸）
  if (t > cta) {
    const k = clamp(spring(t, cta, 2, .45), 0, 1.2), ls = MIN * .1, y0 = H * (PORT ? .42 : .4);
    ctx.save(); ctx.translate(W / 2, y0); ctx.scale(k, k); ctx.translate(-W / 2, -y0);
    const nw = measure('Notely', { size: ls * .62, weight: 900, fam: 'display' }).w, gx = W / 2 - (ls + MIN * .03 + nw) / 2;
    ctx.fillStyle = STYLE.c.a1; fillRR(gx, y0 - ls / 2, ls, ls, ls * .28);
    txtB('Notely', gx + ls + MIN * .03, y0, { size: ls * .62, weight: 900, fam: 'display', color: UIC.ink, maxW: W * .6, ui: true });
    ctx.restore();
    const bk = clamp(spring(t, cta + BEAT * .75, 2.2, .45), 0, 1.2), bw = MIN * .34, bh = MIN * .1, by = y0 + MIN * .17;
    const br = 1 + .02 * Math.sin(t * 3);   // 停住時按鈕輕微呼吸
    ctx.save(); ctx.translate(W / 2, by); ctx.scale(bk * br, bk * br);
    ctx.shadowColor = rgba(STYLE.c.a1, .4); ctx.shadowBlur = bh * .4; ctx.shadowOffsetY = bh * .12;
    ctx.fillStyle = STYLE.c.a1; fillRR(-bw / 2, -bh / 2, bw, bh, bh / 2); ctx.shadowColor = 'transparent';
    txtB('免費試用', 0, 0, { size: bh * .4, weight: 800, color: UI.paper, align: 'center', maxW: bw * .8, ui: true });
    ctx.restore();
  }
}
