/* 五個風格包卡片：橫式一列、直式一欄；每拍輪流高亮 */
const DEMO_STYLES = [
  ['矽谷科技', ['#07080c', '#5ef2c6', '#5b8cff', '#b07bff']],
  ['極簡品牌', ['#f4f1ea', '#e8462f', '#16161a']],
  ['溫暖手作', ['#f6e9d7', '#e07a4f', '#5c9e7a', '#e8b64c']],
  ['資料視覺', ['#11151c', '#3ec7a0', '#5b9cf0', '#f0a35b']],
  ['霓虹復古', ['#07020f', '#ff3fa4', '#2ff3ff', '#ffd23f']],
];
function sStyles(t, T, pulse) {
  const a = tw(t, -.25, .5);   // 進場從切點前開始，轉場中就看得到
  const title = txt('5 種風格包', W / 2, SAFE.y + fz('h2') * .6, { size: fz('h2'), weight: 800, fam: 'display', align: 'center', alpha: a });
  txt('換風格不換引擎', W / 2, title.bottom + fz('body') * .9, { size: fz('body'), color: STYLE.c.mute, align: 'center', alpha: a, fam: 'mono' });
  const top = title.bottom + fz('body') * 2.4, n = DEMO_STYLES.length, gap = MIN * .025;
  const hi = t > BEAT * 3 ? Math.floor(t / BEAT) % n : -1;
  DEMO_STYLES.forEach(([name, pal], i) => {
    const p = stag(t, i, 0, BEAT * .5, .6, 'back'), al = clamp(p) * a;
    let x, y, w, h;
    if (PORT) { h = (SAFE.b - top - gap * (n - 1)) / n; w = SAFE.w; x = SAFE.x; y = top + i * (h + gap); }
    else { w = (SAFE.w - gap * (n - 1)) / n; h = Math.min(SAFE.b - top, w * 1.25); x = SAFE.x + i * (w + gap); y = top + (SAFE.b - top - h) / 2; }
    ctx.save(); ctx.globalAlpha = al; ctx.translate(0, (1 - p) * MIN * .08);
    if (i === hi) glow(x + w / 2, y + h / 2, Math.max(w, h) * .7, pal[1], .35 + pulse * .25);
    card(x, y, w, h, { stroke: i === hi ? rgba(pal[1], .9) : STYLE.c.cardLine, lw: i === hi ? 2 : 1 });
    const sw = PORT ? { x: x + h * .12, y: y + h * .12, w: h * .76 * 1.6, h: h * .76 } : { x: x + w * .1, y: y + w * .1, w: w * .8, h: h * .56 };
    fillRR(sw.x, sw.y, sw.w, sw.h, MIN * .012, pal[0]);
    const r = Math.min(sw.w / (pal.length * 2.6), sw.h * .16);
    pal.slice(1).forEach((c, k) => circle(sw.x + sw.w * .22 + k * r * 2.6, sw.y + sw.h - r * 1.8, r, c));
    const fs = fz(PORT ? 'h3' : 'body');
    if (PORT) txt(name, sw.x + sw.w + h * .18, y + h / 2, { size: fs, weight: 700, alpha: al, maxW: x + w - (sw.x + sw.w + h * .3) });
    else txt(name, x + w / 2, sw.y + sw.h + (y + h - sw.y - sw.h) / 2, { size: fit(name, w * .84, fs, 700), weight: 700, align: 'center', alpha: al });
    ctx.restore();
  });
}
