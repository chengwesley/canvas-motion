/* 痛點：便利貼、聊天、文件、信件四張卡片散在畫面各處、各自飄移；找不到時跳出問號，最後全部往下落、交給下一幕的瀏覽器 */
const PAIN_CARDS = [
  { label: '便利貼', icon: 'pin', u: .2, v: .32, r: -.12 },
  { label: '聊天訊息', icon: 'user', u: .78, v: .26, r: .1 },
  { label: '文件', icon: 'calendar', u: .28, v: .7, r: .08 },
  { label: '信件', icon: 'mail', u: .74, v: .68, r: -.07 },
];
function sPain(t, T, pulse) {
  backdrop(t, { amt: .3 });
  const cw = PORT ? W * .42 : W * .2, ch = cw * .62, fall = E.in(prog(t, T - .55, T));   // 收尾往下落
  const q = BEAT * 4, sk = shake(t, q, .03, .45);   // 高光：找不到的那一拍，整個畫面抖一下
  ctx.save(); ctx.translate(sk.x, sk.y); ctx.rotate(sk.r);
  PAIN_CARDS.forEach((c, i) => {
    const at = i * .12, d = spring(t, at, 1.8, .5), drift = Math.sin(t * .9 + i * 1.7) * MIN * .012;
    const x = W * (PORT ? lerp(.28, .72, c.u > .5 ? 1 : 0) : c.u), y = H * (PORT ? lerp(.22, .62, c.v > .5 ? 1 : 0) + (i % 2) * .08 : c.v) + drift;
    const tx = lerp(x, W / 2, fall), ty = lerp(y, H * 1.1, fall);
    if (d <= 0) return;
    ctx.save(); ctx.translate(tx, ty); ctx.rotate(c.r * (1 + Math.sin(t * .7 + i) * .3) + fall * c.r * 2); ctx.scale(d * (1 - fall * .4), d * (1 - fall * .4));
    uiCard(-cw / 2, -ch / 2, cw, ch, { r: MIN * .014, lift: .5 });
    ctx.fillStyle = accent(i); fillRR(-cw * .42, -ch * .3, ch * .36, ch * .36, ch * .09); uiIcon(-cw * .42 + ch * .18, -ch * .12, ch * .36, c.icon);
    txtB(c.label, -cw * .42 + ch * .48, -ch * .12, { size: ch * .16, weight: 700, color: UIC.ink, maxW: cw * .55, ui: true });
    for (let k = 0; k < 2; k++) { ctx.fillStyle = UI.fill; fillRR(-cw * .38, ch * (.12 + k * .16), cw * (k ? .5 : .7), ch * .07, 3); }
    ctx.restore();
  });
  // 高光：找不到 → 正中央的搜尋框打字、跳出大問號
  const sw = PORT ? W * .7 : W * .32, sh = MIN * .075, sy = H * (PORT ? .5 : .5);
  uiIn(t, BEAT * 2, W / 2, sy, () => {
    ctx.save(); ctx.globalAlpha *= 1 - fall;
    uiCard(W / 2 - sw / 2, sy - sh / 2, sw, sh, { r: sh / 2, lift: .7 });
    const gx = W / 2 - sw / 2 + sh * .5, gr = sh * .14;   // 放大鏡
    ctx.save(); ctx.strokeStyle = UIC.sub; ctx.lineWidth = sh * .05; ctx.lineCap = 'round'; ctx.beginPath(); ctx.arc(gx, sy - gr * .2, gr, 0, Math.PI * 2); ctx.stroke(); line(gx + gr * .7, sy + gr * .5, gx + gr * 1.4, sy + gr * 1.2, UIC.sub, sh * .05); ctx.restore();
    const ty = typing('下週簡報', t, BEAT * 2.4, 6);
    txtB(ty.text, W / 2 - sw / 2 + sh * 1.05, sy, { size: sh * .36, weight: 600, color: UIC.ink, maxW: sw * .6, ui: true });
    if (t > q) { const pk = clamp(spring(t, q, 2.4, .35), 0, 1.4), pr = sh * .55;
      ctx.save(); ctx.translate(W / 2 + sw / 2, sy - sh * .6); ctx.scale(pk, pk); circle(0, 0, pr, UIC.bad);
      txtB('?', 0, pr * .04, { size: pr * 1.2, weight: 900, color: UI.paper, align: 'center', maxW: pr * 1.6, ui: true }); ctx.restore(); }
    ctx.restore();
  });
  ctx.restore();
}
