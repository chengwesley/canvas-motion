/* 首頁截圖放進瀏覽器外框（立體傾斜進場）→ 游標掃過導覽與標題 → 移到「免費試用」→ 鏡頭推近、點擊、聚光，聚光到位後才出標籤（一次一個重點） */
function sSite(t, T, pulse) {
  backdrop(t);
  const fw = PORT ? SAFE.w * 1.04 : Math.min(SAFE.w * .86, SAFE.h * 1.45), fh = PORT ? SAFE.h * .6 : fw / 1.6;
  const fx = W / 2 - fw / 2, fy = PORT ? H * .33 : H / 2 - fh / 2 + MIN * .03;
  const cb = browserContent(fx, fy, fw, fh);
  const po = PORT ? { fit: 'cover', u: .2, v: .45 } : { fit: 'width', v: .0 };
  const m = picMap('home', cb.x, cb.y, cb.w, cb.h, po);
  const btn = m.at(.104, .52), b0 = m.at(.05, .486), b1 = m.at(.158, .555);
  const nav = m.at(.168, .05), head = m.at(.3, .27);
  const keys = [{ t: 0, x: W * .8, y: H * .92 }, { t: BEAT * 2, x: nav.x, y: nav.y, focus: true, zoom: 1.35 }, { t: BEAT * 3.6, x: nav.x + MIN * .1, y: nav.y },
    { t: BEAT * 5.2, x: head.x, y: head.y }, { t: BEAT * 6.9, x: btn.x, y: btn.y, click: true }];
  const cam = follow(t, camFromClicks(keys, { zoom: PORT ? 1.5 : 2, hold: 4 }));
  const tilt = tiltIn(t, -.1, { dur: 1 });   // 視窗斜躺著升起、轉正（上一幕的筆記卡片落進這裡）
  txt('Notely', W / 2, PORT ? H * .16 : SAFE.y + fz('h3') * .2, { size: fz('h2'), weight: 800, fam: 'display', align: 'center', maxW: SAFE.w, alpha: tw(t, -.25, .5) * (1 - tw(t, BEAT * 5, .5)) });
  shot(cam, () => {
    frameBrowser(fx, fy, fw, fh, { url: 'notely.example', lift: .7 - Math.max(0, tilt) * .3, tilt }, box => pic('home', box.x, box.y, box.w, box.h, po));
    spotlight(b0.x, b0.y, b1.x - b0.x, b1.y - b0.y, tw(t, BEAT * 7.2, .4), { r: (b1.y - b0.y) / 2, dim: .35 });
    callout(b1.x, b1.y, b1.x + MIN * .1, b1.y + MIN * .07, '免費試用', tw(t, BEAT * 8.3, .5), { size: MIN * .022 });
    drawCursor(cursorAt(t, keys), t, { kind: t > BEAT * 5.6 ? 'hand' : 'arrow', size: MIN * .03 });
  });
}
