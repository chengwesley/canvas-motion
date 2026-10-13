/* 官網截圖放進瀏覽器外框 → 游標移到「免費試用」→ 鏡頭推近、點擊、聚光、標籤 */
function sSite(t, T, pulse) {
  backdrop(t);
  const fw = PORT ? SAFE.w * 1.04 : Math.min(SAFE.w * .86, SAFE.h * 1.45), fh = PORT ? SAFE.h * .6 : fw / 1.6;
  const fx = W / 2 - fw / 2, fy = PORT ? H * .33 : H / 2 - fh / 2 + MIN * .03;
  const cb = browserContent(fx, fy, fw, fh);
  const po = PORT ? { fit: 'cover', u: .43, v: .42 } : { fit: 'width', v: .0 };
  const m = picMap('home', cb.x, cb.y, cb.w, cb.h, po);
  const btn = m.at(.43, .437), b0 = m.at(.364, .412), b1 = m.at(.495, .462);
  const nav = m.at(.19, .036), head = m.at(.62, .2);
  const keys = [{ t: 0, x: W * .8, y: H * .92 }, { t: BEAT * 2, x: nav.x, y: nav.y, focus: true, zoom: 1.35 }, { t: BEAT * 3.6, x: nav.x + MIN * .1, y: nav.y },
    { t: BEAT * 5.2, x: head.x, y: head.y }, { t: BEAT * 6.9, x: btn.x, y: btn.y, click: true }];
  const cam = follow(t, camFromClicks(keys, { zoom: PORT ? 1.5 : 2, hold: 4 }));
  const enter = spring(t, -.2, 1.4, .55);
  txt('點點簽 DottedSign', W / 2, PORT ? H * .16 : SAFE.y + fz('h3') * .2, { size: fz('h2'), weight: 800, fam: 'display', align: 'center', maxW: SAFE.w, alpha: tw(t, -.25, .5) * (1 - tw(t, BEAT * 5, .5)) });
  shot(cam, () => {
    ctx.save(); ctx.translate(0, (1 - enter) * H * .3);
    frameBrowser(fx, fy, fw, fh, { url: 'www.dottedsign.com/zh-tw', lift: .4 + enter * .3 }, box => pic('home', box.x, box.y, box.w, box.h, po));
    ctx.restore();
    spotlight(b0.x, b0.y, b1.x - b0.x, b1.y - b0.y, tw(t, BEAT * 7.2, .4), { r: (b1.y - b0.y) / 2, dim: .35 });
    callout(b1.x, b0.y, b1.x + MIN * .12, b0.y - MIN * .07, '免費試用', tw(t, BEAT * 7.6, .5), { size: MIN * .022 });
    drawCursor(cursorAt(t, keys), t, { kind: t > BEAT * 5.6 ? 'hand' : 'arrow', size: MIN * .03 });
  });
}
