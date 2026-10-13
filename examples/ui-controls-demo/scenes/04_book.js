/* Dock → open（Dock 圖示跳兩下、行事曆視窗從圖示打開）接 Drag → booked（事件拖到週三 11 點、吸附、Booked 彈出） */
function sBook(t, T, pulse) {
  demoBg(t);
  const tClick = BEAT, tOpen = BEAT * 1.55, tGrab = BEAT * 5, tDrop = BEAT * 7.9, tBook = BEAT * 8.1;
  const ww = PORT ? W * .88 : Math.min(MIN * 1.3, W * .78), wh = PORT ? H * .6 : H * .64, wx = (W - ww) / 2, wy = PORT ? H * .16 : H * .13;
  const s = PORT ? W * .1 : MIN * .075, by = PORT ? H * .9 : H * .955;
  const bh = Math.max(MIN * .036, wh * .05), pad = Math.min(ww, wh) * .05, cal = { x: wx + pad, y: wy + bh + pad, w: ww - pad * 2, h: wh - bh - pad * 2 };
  const co = { today: 2, hours: [9, 10, 11, 12, 13, 14], card: false, ...(PORT ? { days: ['Mon', 'Tue', 'Wed'], dates: [13, 14, 15] } : {}) };   // 直式只排三天，格子才夠大
  const G = uiCalGrid(cal.x, cal.y, cal.w, cal.h, co), from = G.slot(0, 9, 10), to = G.slot(2, 11, 12);
  const icons = [{ col: '#2563eb', glyph: 'doc' }, { col: '#22c55e', glyph: 'chat' }, { col: '#0ea5e9', glyph: 'mail' },
    { col: '#ffffff', col2: '#e2e8f0', glyph: 'cal', ink: STYLE.c.a1 }, { col: '#f97316', glyph: 'photo' }, { col: '#8b5cf6', glyph: 'music' }];
  // Dock 圖示位置（不放大時）：游標要先知道行事曆圖示在哪
  const gap = s * .22, calIx = W / 2 - (6 * s + 5 * gap) / 2 + 3 * (s + gap) + s / 2, calIy = by - s * .2 - s / 2;
  const grabOff = { x: from.w * .45, y: from.h * .5 };
  const keys = [{ t: 0, x: W * .72, y: H * 1.05 }, { t: tClick, x: calIx + s * .1, y: calIy + s * .1, click: true },
    { t: tGrab, x: from.x + grabOff.x, y: from.y + grabOff.y, click: true }, { t: tDrop, x: to.x + grabOff.x, y: to.y + grabOff.y, drag: true },
    { t: tDrop + BEAT * 2, x: to.x + to.w * 1.15, y: to.y + to.h * 1.4 }];
  const c = cursorAt(t, keys);

  // Dock（進場從下方滑上來）
  const dk = spring(t, -.3, 1.5, .62);
  ctx.save(); ctx.globalAlpha *= clamp(dk * 2); ctx.translate(0, (1 - clamp(dk)) * s * 1.5);
  const near = clamp(1 - (by - s * 1.6 - c.y) / (s * 2.2));
  const D = uiDock(W / 2, by, s, icons, t, { mx: c.x, mag: .5 * near, bounce: { i: 3, at: tClick + .05, n: 2 }, running: t > tOpen ? [0, 3] : [0] });
  ctx.restore();

  // 視窗從行事曆圖示打開
  const op = spring(t, tOpen, 1.5, .62), drag = uiDragSnap(t, tGrab, tDrop, { x: from.x, y: from.y }, { x: to.x, y: to.y });
  const booked = t >= tDrop;
  uiOpenFrom(D[3].x, D[3].y, wx, wy, ww, wh, op, () => {
    frameWindow(wx, wy, ww, wh, { title: 'Calendar', lift: .7 }, () => {
      ctx.fillStyle = '#ffffff'; ctx.fillRect(wx, wy + bh, ww, wh - bh);
      uiCalendar(cal.x, cal.y, cal.w, cal.h, { ...co, events: [
        { d: 1, h0: 10, h1: 11, title: 'Stand-up', time: '10:00', col: UIC.ok },
        PORT ? { d: 0, h0: 11.5, h1: 13, title: 'Interview', time: '11:30', col: '#8b5cf6' } : { d: 3, h0: 9, h1: 10.5, title: 'Interview', time: '9:00', col: '#8b5cf6' },
        PORT ? { d: 2, h0: 13, h1: 14, title: 'Lunch', time: '13:00', col: '#f97316' } : { d: 4, h0: 12, h1: 13, title: 'Lunch', time: '12:00', col: '#f97316' }],
        target: { d: 2, h0: 11, h1: 12, p: clamp((t - tGrab) * 3) * (1 - clamp((t - tDrop) * 5)) } });
      const pk = booked ? impact(t, tDrop, .08, .3) : { sx: 1, sy: 1 };
      ctx.save(); ctx.translate(drag.x + to.w / 2, drag.y + to.h / 2); ctx.scale(pk.sx, pk.sy); ctx.translate(-(drag.x + to.w / 2), -(drag.y + to.h / 2));
      uiEventBlock(drag.x, drag.y, to.w, to.h, { title: 'Design review', time: booked ? 'Wed 11:00' : 'Mon 9:00', col: STYLE.c.a1, lift: drag.lift, rot: drag.rot, done: prog(t, tBook, tBook + .45) });
      ctx.restore();
    });
  });
  uiBurst(to.x + to.w / 2, to.y + to.h / 2, to.w * .7, t, tDrop + .02, { ky: .6, n: 12, col: STYLE.c.a1 });
  const pillY = to.y - MIN * .035;
  uiPill(to.x + to.w / 2, pillY, 'Booked', t, tBook, { kind: 'ok', solid: true, col: UIC.ok, size: MIN * .022 });

  if (t > tGrab - .3 && t < tDrop + BEAT * 2.2) drawCursor(c, t, { kind: t > tGrab - .05 && t < tDrop + .1 ? 'hand' : 'arrow' });
  else drawCursor(c, t);

  const ca = clamp(spring(t, -.2, 1.5, .62) * 2), a1 = 1 - clamp((t - BEAT * 4) * 6), a2 = clamp((t - BEAT * 4 - .2) * 5);
  if (a1 > 0) demoCap('Dock → open', W / 2, wy - MIN * .045, ca * a1);
  if (a2 > 0) demoCap('Drag → booked', W / 2, wy - MIN * .045, ca * a2);
}
