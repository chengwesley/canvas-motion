/* sShapes：LK_SHAPES 的 8 種形狀 + 錨點 + 底板文字 + 自動縮字。換 data.look 就換畫風。 */
function sShapes(t, T, pulse, s) {
  const d = s.data || {};
  L_look(t, T, pulse, { ...s, data: { ...d, clouds: 2, layers: [{ points: [[0, .86], [1, .86], [1, 1], [0, 1]], color: 'ground', solid: true }] } });
  withLook(s, t, pulse, (L, P) => {
    const gy = H * pick(.86, .84), u = MIN;
    const items = PORT
      ? [['house', W * .3, H * .5], ['tree', W * .72, H * .5], ['screen', W * .3, H * .68], ['person', W * .72, H * .68]]
      : [['house', W * .14, gy], ['tree', W * .3, gy], ['room', W * .47, gy], ['screen', W * .64, gy * .82], ['phone', W * .64 + u * .13, gy * .82], ['person', W * .8, gy]];
    items.forEach(([k, x, y], i) => {
      const a = tw(t, i * BEAT * .5, .5, 'back'); if (a <= 0) return;
      ctx.save(); ctx.translate(x, y); ctx.scale(a, a); ctx.translate(-x, -y);
      const parts = k === 'house' ? LK_SHAPES.house(x, y, u * .2) : k === 'tree' ? LK_SHAPES.tree(x, y, u * .3)
        : k === 'room' ? LK_SHAPES.room(x, y, u * .3, u * .3) : k === 'screen' ? LK_SHAPES.screen(x, y, u * .18)
        : k === 'phone' ? LK_SHAPES.phone(x, y, u * .1) : LK_SHAPES.person(x, y, u * .24, i % 2 ? 'sit' : 'stand');
      lookDraw(L, P, parts, { lw: 1.5 });
      ctx.restore();
    });
    // 紙張：輕輕飄動
    lookDraw(L, P, LK_SHAPES.paper(W * pick(.47, .5), H * pick(.4, .3), u * .09, u * .12, Math.sin(t * 2) * .15));
    // 車子：在兩個錨點之間開過去（第二幕從第一幕的終點開回來）
    const c = anchorLerp(anchor(d.carFrom || 'car', s), anchor(d.carTo || 'carEnd', s), tw(t, BEAT, T - BEAT * 2, 'io'));
    lookDraw(L, P, LK_SHAPES.car(c.x, c.y, u * .2));
  });
  lookExtras(t, s);
  const { P } = lookOf(s);
  txtPlate(LOOKS[lookOf(s).name].name + '：常用形狀一次套用畫風', W / 2, SAFE.y + fz('h3'), { size: fz('h3'), weight: 800, align: 'center',
    color: P.label, maxW: SAFE.w * .8, fit: { lines: 1 }, alpha: tw(t, .2, .5) });
}
