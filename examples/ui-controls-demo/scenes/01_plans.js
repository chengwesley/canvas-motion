/* Monthly → yearly（分段切換＋價格翻轉＋「2 months free」膠囊）與 Click → done（開關＋按鈕載入 → Published） */
function sPlans(t, T, pulse) {
  demoBg(t);
  const [A, B] = demoTwo(), tSw = BEAT * 2, tTog = BEAT * 5, tPress = BEAT * 7, tDone = BEAT * 9;
  const fsA = Math.min(A.h * .05, A.w * .058), fsB = Math.min(B.h * .05, B.w * .058);
  // 互動目標的位置（先算好，游標才對得準）
  const segW = A.w * .8, segH = Math.min(A.h * .11, A.w * .13), segX = A.x + (A.w - segW) / 2, segY = A.y + A.h * .17;
  const tgW = Math.min(B.w * .15, B.h * .13), tgX = B.x + B.w * .92 - tgW, tgY = B.y + B.h * .67 - tgW * .28;
  const btn = { x: B.x + B.w / 2, y: B.y + B.h * .85, w: B.w * .6, h: Math.min(B.h * .12, B.w * .13) };
  const keys = [{ t: 0, x: W * .5, y: H * 1.04 }, { t: tSw, x: segX + segW * .75, y: segY + segH * .55, click: true },
    { t: tTog, x: tgX + tgW * .72, y: tgY + tgW * .3, click: true }, { t: tPress, x: btn.x + btn.w * .1, y: btn.y + btn.h * .1, click: true },
    { t: tDone + BEAT * 2.2, x: btn.x + B.w * .32, y: btn.y + B.h * .2 }];

  demoEnter(t, 0, A, () => {
    const lx = A.x + A.w * .1, sp = spring(t, tSw, 2, .5);
    txtB('Pro plan', lx, A.y + A.h * .09, { size: fsA, weight: 700, color: UIC.sub, maxW: A.w * .5, ui: true });
    uiSegment(segX, segY, segW, segH, ['Monthly', 'Yearly'], sp, { light: true });
    const ps = Math.min(A.h * .19, A.w * .2), py = A.y + A.h * .46;
    const r = uiRoll('£29', '£290', lx, py, t, tSw + .08, { size: ps, weight: 800, color: UIC.ink });
    uiRoll('/month', '/year', lx + r.w + ps * .12, py + ps * .2, t, tSw + .2, { size: ps * .26, weight: 600, color: UIC.sub, gap: .03 });
    uiPill(lx, A.y + A.h * .62, '2 months free', t, tSw + .45, { kind: 'ok', col: UIC.ok, align: 'left', size: fsA * .9 });
    ctx.fillStyle = 'rgba(15,23,42,.07)'; ctx.fillRect(lx, A.y + A.h * .72, A.w * .8, 1);
    ['Unlimited documents', 'Priority support'].forEach((s, i) => {
      const yy = A.y + A.h * (.8 + i * .09);
      circle(lx + fsA * .45, yy, fsA * .45, mixc('#ffffff', STYLE.c.a1, .14)); uiGlyph('check', lx + fsA * .45, yy, fsA * .55, STYLE.c.a1);
      txtB(s, lx + fsA * 1.3, yy, { size: fsA, weight: 600, color: UIC.ink, maxW: A.w * .68, ui: true });
    });
  }, { cap: 'Monthly → yearly' });

  demoEnter(t, 1, B, () => {
    const lx = B.x + B.w * .08, ic = Math.min(B.h * .11, B.w * .12), hy = B.y + B.h * .12;
    ctx.fillStyle = STYLE.c.a1; fillRR(lx, hy - ic / 2, ic, ic, ic * .28); uiGlyph('doc', lx + ic / 2, hy, ic * .5, '#fff');
    txtB('Launch post', lx + ic * 1.3, hy - fsB * .55, { size: fsB * 1.1, weight: 800, color: UIC.ink, maxW: B.w * .45, ui: true });
    txtB('Edited 2 min ago', lx + ic * 1.3, hy + fsB * .65, { size: fsB * .82, weight: 500, color: UIC.sub, maxW: B.w * .45, ui: true });
    const px = B.x + B.w * .92;
    if (t < tDone + .1) uiPill(px, hy, 'Draft', t, -1, { kind: 'dot', col: '#94a3b8', size: fsB * .8, align: 'right' });
    else uiPill(px, hy, 'Live', t, tDone + .1, { kind: 'live', col: UIC.ok, size: fsB * .8, align: 'right' });
    // 預覽圖
    const ix = lx, iy = B.y + B.h * .24, iw = B.w * .84, ih = B.h * .26;
    ctx.save(); ctx.beginPath(); rrect(ix, iy, iw, ih, ih * .14); ctx.clip();
    const g = ctx.createLinearGradient(ix, iy, ix + iw, iy + ih); g.addColorStop(0, mixc(STYLE.c.a1, '#ffffff', .55)); g.addColorStop(1, mixc(UIC.ok, '#ffffff', .55));
    ctx.fillStyle = g; ctx.fillRect(ix, iy, iw, ih);
    circle(ix + iw * .78, iy + ih * .3, ih * .14, 'rgba(255,255,255,.85)');
    ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.beginPath(); ctx.moveTo(ix, iy + ih); ctx.lineTo(ix + iw * .3, iy + ih * .45); ctx.lineTo(ix + iw * .55, iy + ih * .8); ctx.lineTo(ix + iw * .7, iy + ih * .6); ctx.lineTo(ix + iw, iy + ih); ctx.fill();
    ctx.restore();
    ctx.fillStyle = '#e8ecf2'; fillRR(lx, B.y + B.h * .55, B.w * .7, B.h * .022, B.h * .011); fillRR(lx, B.y + B.h * .59, B.w * .5, B.h * .022, B.h * .011);
    txtB('Notify subscribers', lx, tgY + tgW * .28, { size: fsB, weight: 600, color: UIC.ink, maxW: tgX - lx - B.w * .04, ui: true });
    uiToggle(tgX, tgY, tgW, spring(t, tTog, 2.2, .42));
    uiButton(btn.x, btn.y, btn.w, btn.h, t, tPress, tDone, { label: 'Publish', doneLabel: 'Published' });
    uiBurst(btn.x, btn.y, btn.w * .62, t, tDone + .05, { ky: .7, n: 12 });
  }, { cap: 'Click → done' });

  drawCursor(cursorAt(t, keys), t);
}
