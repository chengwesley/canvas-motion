/* Island → live（動態島展開成 LIVE 即時活動）與 Alerts → stack（鎖定畫面通知一張張進來，再收成一疊「12 new orders」） */
function sLive(t, T, pulse) {
  demoBg(t);
  const tIs = BEAT * 2, tStack = BEAT * 8.5;
  const ph = PORT ? Math.min(H * .56, W * .43 / .49) : Math.min(H * .74, MIN * .78), cy = PORT ? H * .44 : H * .46;
  const cx1 = PORT ? W * .27 : W / 2 - MIN * .36, cx2 = PORT ? W * .73 : W / 2 + MIN * .36, pw = ph * .49;
  const R1 = { x: cx1 - pw / 2, y: cy - ph / 2, w: pw, h: ph }, R2 = { x: cx2 - pw / 2, y: cy - ph / 2, w: pw, h: ph };

  demoEnter(t, 0, R1, () => {
    const box = framePhone(cx1, cy, ph, { island: false, lift: .7 }, b => {
      const g = ctx.createLinearGradient(b.x, b.y, b.x + b.w, b.y + b.h); g.addColorStop(0, '#dbeafe'); g.addColorStop(1, '#dcfce7');
      ctx.fillStyle = g; ctx.fillRect(b.x, b.y, b.w, b.h);
      const icons = [['#2563eb', 'chat'], ['#22c55e', 'chart'], ['#0ea5e9', 'mail'], ['#f97316', 'photo'], ['#8b5cf6', 'music'], ['#ef4444', 'video'], ['#14b8a6', 'cal'], ['#64748b', 'doc']];
      const s = b.w * .17, gx = (b.w - s * 4) / 5;
      icons.forEach(([c, gl], i) => {
        const k = clamp(spring(t, .05 + i * .04, 2, .55), 0, 1.1);
        ctx.save(); ctx.globalAlpha *= clamp(k * 2); const ix = b.x + gx + (i % 4) * (s + gx) + s / 2, iy = b.y + b.h * .3 + Math.floor(i / 4) * s * 1.55;
        ctx.translate(ix, iy); ctx.scale(k, k); uiAppIcon(0, 0, s, { col: c, glyph: gl }); ctx.restore();
      });
      // 底部即時活動卡：動態島展開後出現「Join now」
      const jk = spring(t, tIs + .5, 2, .5), cw = b.w * .86, ch = b.w * .36, jx = b.x + (b.w - cw) / 2, jy = b.y + b.h * .64 + (1 - clamp(jk)) * b.h * .1;
      if (jk > .01) { ctx.save(); ctx.globalAlpha *= clamp(jk * 2); uiGlass(jx, jy, cw, ch, ch * .22, { fill: 'rgba(255,255,255,.88)' });
        txtB('Product Live', jx + ch * .2, jy + ch * .3, { size: ch * .15, weight: 800, color: UIC.ink, maxW: cw * .6, ui: true });
        txtB('248 watching', jx + ch * .2, jy + ch * .52, { size: ch * .12, weight: 500, color: UIC.sub, maxW: cw * .6, ui: true });
        ctx.fillStyle = UIC.bad; fillRR(jx + ch * .2, jy + ch * .66, cw - ch * .4, ch * .22, ch * .11);
        txtB('Join now', jx + cw / 2, jy + ch * .77, { size: ch * .12, weight: 800, color: '#fff', align: 'center', maxW: cw * .6, ui: true });
        ctx.restore(); }
    });
    const p = spring(t, tIs, 1.7, .42) - .1 * Math.sin(Math.PI * prog(t, tIs - .32, tIs + .06));
    uiIsland(cx1, box.y + box.w * .03, box.w, p, { title: 'Webinar starts now', sub: 'Product Live', icon: 'video', iconCol: STYLE.c.a1, t, at: tIs + .3 });
  }, { card: false, cap: 'Island → live' });

  const items = [['New order #1042', '£120 · 2 items'], ['New order #1043', '£86 · 1 item'], ['New order #1044', '£240 · 3 items'], ['New order #1045', '£64 · 1 item']]
    .map(([title, sub], i) => ({ at: BEAT * (4 + i * .9), title, sub, icon: 'bag', col: i % 2 ? UIC.ok : STYLE.c.a1 }));
  demoEnter(t, 1, R2, () => {
    framePhone(cx2, cy, ph, { lift: .7 }, b => uiLockScreen(b, t, { items, stackAt: tStack, app: 'SHOP', summary: '12 new orders', summarySub: '£1,840 today', time: '9:41' }));
  }, { card: false, cap: 'Alerts → stack' });
}
