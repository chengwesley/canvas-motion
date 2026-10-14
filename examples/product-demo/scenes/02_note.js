/* 程序化介面：從左欄把「待辦」卡片拖進清單 → 打字 → 打勾，鏡頭跟著游標（介面字用 txtB + ui: true、顏色用 UI.*） */
function sNote(t, T, pulse) {
  backdrop(t, { amt: .35 });
  const ww = PORT ? SAFE.w : Math.min(SAFE.w * .8, SAFE.h * 1.5), wh = PORT ? SAFE.h * .8 : ww / 1.6;
  const wx = W / 2 - ww / 2, wy = H / 2 - wh / 2;
  const side = PORT ? 0 : ww * .24, bar = Math.max(MIN * .036, wh * .05);
  const doc = { x: wx + side + ww * .06, y: wy + bar + wh * .07, w: ww - side - ww * .12, h: wh - bar - wh * .12 };
  const field = { x: wx + MIN * .03, y: wy + bar + wh * .2 };
  const rowH = doc.h * .14, row = i => doc.y + doc.h * .3 + i * rowH, cw = doc.w * .84, ch = rowH * .78;
  const drop = { x: doc.x + doc.w * .08 + cw / 2, y: row(2) };
  const src = PORT ? { x: doc.x + doc.w * .2, y: doc.y + doc.h * .88 } : { x: field.x + MIN * .04, y: field.y };
  const box = { x: doc.x + doc.w * .08 + ch * .45, y: drop.y };
  const keys = [{ t: 0, x: W * .2, y: H * .9 }, { t: BEAT * 1.6, x: src.x, y: src.y + MIN * .01, click: true },
    { t: BEAT * 4, x: drop.x, y: drop.y, drag: true, focus: true }, { t: BEAT * 7.6, x: box.x, y: box.y, click: true }, { t: BEAT * 9, x: box.x + MIN * .05, y: box.y + MIN * .04 }];
  const cam = follow(t, camFromClicks(keys, { zoom: 1.6, hold: 3 }));
  const c = cursorAt(t, keys), dropped = t > BEAT * 4, done = clamp((t - BEAT * 8) / .6);
  const card = (x, y, label, o = {}) => {   // 清單裡的一列：勾選框＋文字
    ctx.fillStyle = UI.paper; ctx.strokeStyle = UI.line; ctx.lineWidth = 1.5; fillRR(x, y - ch / 2, cw, ch, ch * .25); strokeRR(x, y - ch / 2, cw, ch, ch * .25);
    if (o.checked) { ctx.fillStyle = STYLE.c.a2; fillRR(x + ch * .3, y - ch * .15, ch * .3, ch * .3, ch * .08); }
    else { ctx.strokeStyle = UI.line; ctx.lineWidth = 2; strokeRR(x + ch * .3, y - ch * .15, ch * .3, ch * .3, ch * .08); }
    txtB(label, x + ch * .85, y, { size: ch * .36, weight: 600, color: o.checked ? UI.sub : UI.ink, maxW: cw - ch, ui: true });
  };
  shot(cam, () => {
    frameWindow(wx, wy, ww, wh, { title: 'Notely' }, b => {
      ctx.fillStyle = mixc(UI.paper, STYLE.c.a1, .04); ctx.fillRect(b.x, b.y, b.w, b.h);
      if (!PORT) { ctx.fillStyle = mixc(UI.paper, STYLE.c.a1, .1); ctx.fillRect(b.x, b.y, side, b.h);
        ['待辦', '會議', '想法'].forEach((s, i) => txtB(s, b.x + MIN * .03, field.y + i * MIN * .05, { size: MIN * .022, weight: 600, color: UI.ink, maxW: side * .8, ui: true })); }
      ctx.fillStyle = UI.paper; floatShadow(doc.x, doc.y, doc.w, doc.h, 6, .12); fillRR(doc.x, doc.y, doc.w, doc.h, 6);
      if (PORT) txtB('＋ 待辦', src.x - MIN * .04, src.y, { size: MIN * .03, weight: 700, color: STYLE.c.a1, maxW: doc.w * .5, ui: true });   // 直式沒有左欄，從清單下方的按鈕拉出來
      txtB('本週待辦', doc.x + doc.w * .08, doc.y + doc.h * .13, { size: MIN * .036, weight: 800, color: UI.ink, maxW: doc.w * .8, ui: true });
      card(doc.x + doc.w * .08, row(0), '整理週會重點', { checked: true });
      card(doc.x + doc.w * .08, row(1), '準備下週簡報', { checked: true });
      if (dropped) {
        const p = spring(t, BEAT * 4, 3, .4), ty = typing('預約客戶訪談', t, BEAT * 5.2, 5);
        ctx.save(); ctx.translate(drop.x, drop.y); ctx.scale(p, p); ctx.translate(-drop.x, -drop.y);
        card(doc.x + doc.w * .08, drop.y, ty.text || ' ', { checked: done >= 1 });
        if (ty.caret && !ty.done) { const mw = ty.text ? measure(ty.text, { size: ch * .36, weight: 600 }).w : 0;
          ctx.fillStyle = STYLE.c.a1; ctx.fillRect(doc.x + doc.w * .08 + ch * .85 + mw + 3, drop.y - ch * .22, 2, ch * .44); }
        ctx.restore();
        uiCheck(box.x, box.y, ch * .3, done, { col: STYLE.c.a2, burst: true });
      }
    });
    if (!dropped && t > BEAT * 1.7) {   // 拖曳中的卡片跟著游標
      ctx.save(); ctx.globalAlpha = .85; ctx.fillStyle = rgba(STYLE.c.a1, .18); fillRR(c.x - cw * .2, c.y - ch * .3, cw * .6, ch, ch * .25); ctx.restore();
    }
    drawCursor(c, t, { kind: dropped && t < BEAT * 7 ? 'arrow' : 'hand' });
  });
}
