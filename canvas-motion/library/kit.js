/* kit.js：常用繪圖小工具（k 開頭）。
 * 這些是「畫筆」，不是「版面」：只畫單一物件，位置、大小、動畫全由場景決定。
 * 顏色都取自 STYLE.c，換風格不用改。用不到就別用，想畫別的就自己畫。 */

// 文件頁：上方色條＋幾行文字線。rot 旋轉、lines 行數
function kPage(x, y, w, h, rot, col, lines) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot || 0);
  ctx.shadowColor = STYLE.cardShadow || rgba(STYLE.c.fg, .15); ctx.shadowBlur = MIN * .02; ctx.shadowOffsetY = MIN * .006;
  ctx.fillStyle = STYLE.c.card; fillRR(-w / 2, -h / 2, w, h, w * .06);
  ctx.shadowColor = 'transparent';
  ctx.fillStyle = col || STYLE.c.a1; ctx.fillRect(-w / 2, -h / 2, w, h * .12);
  const n = lines == null ? 5 : lines;
  for (let i = 0; i < n; i++) {
    ctx.fillStyle = rgba(STYLE.c.fg, .14);
    ctx.fillRect(-w * .36, -h * .22 + i * h * .13, w * (i % 3 === 2 ? .45 : .72), h * .045);
  }
  ctx.restore();
}

// 人物剪影：(x, y) 是腳底中心，h 是身高
function kPerson(x, y, h, col) {
  ctx.fillStyle = col;
  circle(x, y - h * .82, h * .13, col);
  ctx.beginPath();
  ctx.moveTo(x - h * .24, y); ctx.quadraticCurveTo(x - h * .24, y - h * .62, x, y - h * .64);
  ctx.quadraticCurveTo(x + h * .24, y - h * .62, x + h * .24, y); ctx.closePath(); ctx.fill();
}

// 筆電：(x, y) 是底座中心，open 0–1 開合，回傳螢幕區 {x, y, w, h}（中心座標）供場景在上面畫內容
function kLaptop(x, y, w, open, screenCol, glowA) {
  const sw = w, sh = w * .62 * open;
  ctx.fillStyle = mixc(STYLE.c.fg, STYLE.c.mute, .35);
  fillRR(x - sw * .56, y, sw * 1.12, w * .045, w * .02);
  ctx.fillStyle = STYLE.c.fg; fillRR(x - sw / 2, y - sh, sw, sh, w * .03);
  ctx.fillStyle = screenCol; fillRR(x - sw * .46, y - sh * .92, sw * .92, sh * .84, w * .015);
  if (glowA > 0) glow(x, y - sh * .5, w * 1.1, screenCol, glowA);
  return { x: x, y: y - sh * .5, w: sw * .92, h: sh * .84 };
}

// 齒輪：rot 旋轉角
function kGear(x, y, r, rot, col) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.fillStyle = col;
  for (let i = 0; i < 8; i++) { ctx.save(); ctx.rotate(i * Math.PI / 4); ctx.fillRect(-r * .16, -r * 1.18, r * .32, r * .4); ctx.restore(); }
  circle(0, 0, r, col); circle(0, 0, r * .42, STYLE.c.bg);
  ctx.restore();
}

// 燈泡：lit 0–1 點亮程度
function kBulb(x, y, r, lit, col) {
  glow(x, y, r * 3.2, col, .5 * lit);
  circle(x, y, r, mixc(rgba(STYLE.c.fg, .15), col, lit));
  ctx.fillStyle = STYLE.c.mute; fillRR(x - r * .45, y + r * .8, r * .9, r * .5, r * .12);
  for (let i = 0; i < 8; i++) {
    const a = i * Math.PI / 4, l = r * (1.4 + .25 * lit);
    line(x + Math.cos(a) * r * 1.2, y + Math.sin(a) * r * 1.2, x + Math.cos(a) * l, y + Math.sin(a) * l, rgba(col, lit), r * .12);
  }
}

// 五角星
function kStar(x, y, r, col) {
  ctx.fillStyle = col; ctx.beginPath();
  for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * .45 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
  ctx.closePath(); ctx.fill();
}

// 二次貝茲弧線，p 0–1 畫到哪；lift 是弧高（兩點距離的比例）。航線、連線、拋物飛行都能用
function kArc(x1, y1, x2, y2, p, lift, col, lw) {
  const d = Math.hypot(x2 - x1, y2 - y1), mx = (x1 + x2) / 2, my = (y1 + y2) / 2 - d * (lift == null ? .3 : lift);
  ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.beginPath();
  const n = Math.max(1, Math.floor(40 * clamp(p)));
  for (let k = 0; k <= n; k++) {
    const u = k / 40, a = (1 - u) * (1 - u), b = 2 * u * (1 - u), e = u * u;
    const x = a * x1 + b * mx + e * x2, y = a * y1 + b * my + e * y2;
    k ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  }
  ctx.stroke();
  const u = n / 40; return { x: (1 - u) * (1 - u) * x1 + 2 * u * (1 - u) * mx + u * u * x2, y: (1 - u) * (1 - u) * y1 + 2 * u * (1 - u) * my + u * u * y2 };
}
