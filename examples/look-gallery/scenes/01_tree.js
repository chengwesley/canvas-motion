/* sTree：自訂主體示範。背景交給 L_look，主體用 lookShape 畫，畫風由 data.look 決定。
 * 把 data.look 換成任何畫風（ink、comic、pixel…），這棵樹會跟著換畫法。 */
function sTree(t, T, pulse, s) {
  L_look(t, T, pulse, { ...s, data: { ...s.data, caption: null, clouds: 2 } });   // 背景：預設構圖
  withLook(s, t, pulse, (L, P) => {
    const x = W * pick(.3, .38), y = H * pick(.82, .78), k = MIN * .004, sway = Math.sin(t * 1.6) * .04;
    ctx.save(); ctx.translate(x, y); ctx.scale(k, k);
    lookShape(L, P, () => { ctx.beginPath(); ctx.moveTo(-5, 0); ctx.lineTo(-3, -60); ctx.lineTo(3, -60); ctx.lineTo(5, 0); ctx.closePath(); }, 'ground');
    ctx.rotate(sway);
    [[0, -95, 36, 'hill3'], [-26, -72, 26, 'hill2'], [26, -74, 24, 'hill2'], [0, -122, 24, 'hill1']].forEach(([cx, cy, r, c], i) =>
      lookShape(L, P, () => { ctx.beginPath(); ctx.arc(cx, cy + Math.sin(t * 2 + i) * 1.5, r * (1 + pulse * .02), 0, Math.PI * 2); }, c, { lw: 1.5 }));
    ctx.restore();
  });
  lookExtras(t, s);
}
