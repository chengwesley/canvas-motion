/* 程序化介面：從左欄把「Signature」欄位拖到文件上 → 打字填入 → 鏡頭跟著（介面字用 txtB + ui: true、顏色用 UI.*） */
function sType(t, T, pulse) {
  backdrop(t, { amt: .35 });
  const ww = PORT ? SAFE.w : Math.min(SAFE.w * .8, SAFE.h * 1.5), wh = PORT ? SAFE.h * .8 : ww / 1.6;
  const wx = W / 2 - ww / 2, wy = H / 2 - wh / 2;
  const side = PORT ? 0 : ww * .24, bar = Math.max(MIN * .036, wh * .05);
  const doc = { x: wx + side + ww * .08, y: wy + bar + wh * .08, w: ww - side - ww * .16, h: wh - bar - wh * .12 };
  const field = { x: wx + MIN * .03, y: wy + bar + wh * .25 }, drop = { x: doc.x + doc.w * .55, y: doc.y + doc.h * .72 };
  const src = PORT ? { x: W / 2, y: wy + wh + MIN * .02 } : field;
  const keys = [{ t: 0, x: W * .2, y: H * .9 }, { t: BEAT * 1.6, x: src.x + MIN * .04, y: src.y + MIN * .01, click: true },
    { t: BEAT * 4, x: drop.x, y: drop.y, drag: true, focus: true }, { t: BEAT * 5, x: drop.x + MIN * .02, y: drop.y + MIN * .03 }];
  const cam = follow(t, camFromClicks(keys, { zoom: 1.6, hold: 3 }));
  const c = cursorAt(t, keys), dropped = t > BEAT * 4, fwid = MIN * .2, fht = MIN * .055;
  shot(cam, () => {
    frameWindow(wx, wy, ww, wh, { title: 'Employment contract' }, box => {
      ctx.fillStyle = mixc(UI.paper, STYLE.c.a1, .05); ctx.fillRect(box.x, box.y, box.w, box.h);
      if (!PORT) { ctx.fillStyle = mixc(UI.paper, STYLE.c.a1, .08); ctx.fillRect(box.x, box.y, side, box.h);
        ['Signature', 'Date', 'Text', 'Checkbox'].forEach((s, i) => txtB(s, box.x + MIN * .03, field.y + i * MIN * .05, { size: MIN * .022, weight: 600, color: UI.ink, maxW: side * .8, ui: true })); }
      ctx.fillStyle = UI.paper; floatShadow(doc.x, doc.y, doc.w, doc.h, 4, .15); fillRR(doc.x, doc.y, doc.w, doc.h, 4);
      txtB('Contract', doc.x + doc.w * .08, doc.y + doc.h * .12, { size: MIN * .04, weight: 800, color: UI.ink, maxW: doc.w * .8, ui: true });
      for (let i = 0; i < 4; i++) { ctx.fillStyle = UI.fill; fillRR(doc.x + doc.w * .08, doc.y + doc.h * (.26 + i * .09), doc.w * (i % 2 ? .6 : .8), MIN * .008, 3); }
      if (dropped) {
        const p = spring(t, BEAT * 4, 3, .4), ty = typing('DottedSign', t, BEAT * 5.5, 10);
        ctx.save(); ctx.translate(drop.x, drop.y); ctx.scale(p, p);
        ctx.fillStyle = rgba(STYLE.c.a1, .1); fillRR(-fwid / 2, -fht / 2, fwid, fht, 6); ctx.strokeStyle = STYLE.c.a1; ctx.lineWidth = 2; strokeRR(-fwid / 2, -fht / 2, fwid, fht, 6);
        txtB(ty.text || 'Signature', -fwid * .42, 0, { size: MIN * .026, weight: ty.text ? 700 : 500, fam: ty.text ? 'display' : 'sans', color: ty.text ? UI.ink : UI.sub, maxW: fwid * .84, ui: true });
        if (ty.caret && ty.text) { const mw = measure(ty.text, { size: MIN * .026, weight: 700, fam: 'display' }).w; ctx.fillStyle = STYLE.c.a1; ctx.fillRect(-fwid * .42 + mw + 3, -fht * .28, 2, fht * .56); }
        ctx.restore();
      }
    });
    if (!dropped && t > BEAT * 1.7) {   // 拖曳中的欄位跟著游標
      ctx.save(); ctx.globalAlpha = .85; ctx.fillStyle = rgba(STYLE.c.a1, .15); fillRR(c.x - fwid * .3, c.y - fht * .3, fwid, fht, 6); ctx.restore();
    }
    drawCursor(c, t, { kind: dropped ? 'arrow' : 'hand' });
  });
}
