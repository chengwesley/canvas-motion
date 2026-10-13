/* 共用：淺色漸層桌布、浮起卡片進場、元件標題。場景只負責「誰在哪裡、何時從 A 變成 B」 */

/** 淺色桌布：底色上幾團很淡的藍綠光暈慢慢漂移，再加極慢的鏡頭推近（整幕的呼吸；引擎每幕會還原 context） */
function demoBg(t) { backdrop(t, { colors: [STYLE.c.a1, UIC.ok, '#7dd3fc'], amt: .16 }); camPush(1 + t * .006); }

/** 兩個並排（直式改上下）的區塊。o.ph 直式時每塊高度比例 */
function demoTwo(o = {}) {
  if (PORT) {
    const w = W * .8, h = H * (o.ph || .34), x = (W - w) / 2, y1 = H * .085, y2 = y1 + h + H * .1;
    return [{ x, y: y1, w, h }, { x, y: y2, w, h }];
  }
  const w = Math.min(MIN * (o.lw || .62), W * .4), h = MIN * (o.lh || .7), gap = MIN * .1, y = H / 2 - h / 2 - MIN * .035;
  return [{ x: W / 2 - gap / 2 - w, y, w, h }, { x: W / 2 + gap / 2, y, w, h }];
}

/** 浮起卡片的進場：從下方彈上來、微縮放、淡入（i 依序錯開）。o.card false 不畫白卡；o.cap 卡片下方的標題 */
function demoEnter(t, i, R, draw, o = {}) {
  const k = spring(t, -.3 + i * .1, 1.5, .62), a = clamp(k * 2);
  ctx.save(); ctx.globalAlpha *= a;
  // 落定後微微漂浮（次要動作，畫面不會完全靜止）
  ctx.translate(R.x + R.w / 2, R.y + R.h / 2 + (1 - k) * MIN * .09 + Math.sin(t * 1.5 + i * 1.9) * MIN * .006); ctx.scale(lerp(.93, 1, clamp(k)), lerp(.93, 1, clamp(k))); ctx.translate(-(R.x + R.w / 2), -(R.y + R.h / 2));
  if (o.card !== false) uiCard(R.x, R.y, R.w, R.h, { r: MIN * .045, lift: .8, glow: o.glow });
  draw();
  ctx.restore();
  if (o.cap) demoCap(o.cap, R.x + R.w / 2, R.y + R.h + MIN * .05, a);
}

/** 元件標題（「Monthly → yearly」那種小字） */
function demoCap(s, x, y, a = 1) {
  txt(s, x, y, { size: fz('cap'), weight: 700, color: '#475569', align: 'center', alpha: a, maxW: W * .42 });
}
