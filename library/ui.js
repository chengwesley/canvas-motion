/* ui.js：高質感 UI 微動態（資料與卡片類的「A → B」產品瞬間）：浮起的白卡、數字滾動、成長標籤、KPI 卡、
 * 走勢線、長條長成趨勢線、粒子匯流成結果、目標環合攏、地圖路線與圖釘、價格卡翻轉、字重滑桿、App 圖示磚。
 * 互動控制（開關、分段、按鈕、進度環、通知）在 uictl.js。全部是 t（或進度 p）的純函式，不用 Math.random。
 * 這些是畫筆不是版面：一個畫面只演一件事、一個主角（references/motion-design.md）。介面裡的字用 ui: true（不受文字檢查）。 */

const UIC = { ok: '#22c55e', okDark: '#16a34a', warn: '#f59e0b', bad: '#ef4444', glass: 'rgba(255,255,255,.72)', ink: '#0f172a', sub: '#64748b',
  line: '#e2e8f0', soft: '#f1f5f9', shade: '30,41,82' };

/* ---------- 共用小工具 ---------- */
/** 可調過衝的 back 緩動：p 0–1，s 越大過衝越多（1.2 約 5%、1.7 約 10%），p ≥ 1 時剛好等於 1（不會跳） */
const uiBack = (p, s = 1.4) => p <= 0 ? 0 : p >= 1 ? 1 : 1 + (s + 1) * Math.pow(p - 1, 3) + s * Math.pow(p - 1, 2);
/** Catmull-Rom 平滑取樣：pts = [[x, y], …] → 細分後的點陣列（每段 seg 點），走勢線與路線共用 */
function _uiCurve(pts, seg = 14) {
  if (pts.length < 3) return pts.map(p => [p[0], p[1]]);
  const out = [[pts[0][0], pts[0][1]]];
  const f = (a, b, c, d, u) => .5 * (2 * b + (c - a) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (3 * b - a - 3 * c + d) * u * u * u);
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    for (let k = 1; k <= seg; k++) out.push([f(p0[0], p1[0], p2[0], p3[0], k / seg), f(p0[1], p1[1], p2[1], p3[1], k / seg)]);
  }
  return out;
}
/** 取取樣線的前 p（依長度）：回傳 { pts, end, cum（每點累積長度）, total } */
function _uiPartial(s, p) {
  const cum = [0]; for (let i = 1; i < s.length; i++) cum.push(cum[i - 1] + Math.hypot(s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1]));
  const total = cum[cum.length - 1], L = total * clamp(p), pts = [s[0]];
  let end = s[0];
  for (let i = 1; i < s.length; i++) {
    if (cum[i] <= L) { pts.push(s[i]); end = s[i]; continue; }
    const u = (L - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]);
    end = [lerp(s[i - 1][0], s[i][0], u), lerp(s[i - 1][1], s[i][1], u)]; pts.push(end); break;
  }
  return { pts, end, cum, total };
}
const _uiPath = pts => { ctx.beginPath(); pts.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); };
/** 發光端點（走勢線、路線的頭）：白圈＋色點＋外光，o.t 有給時外圈每拍擴散一次 */
function uiDot(x, y, r, col, o = {}) {
  glow(x, y, r * 5, col, .55);
  if (o.t !== undefined) { const k = ((o.t % (o.period || 1.2)) + (o.period || 1.2)) % (o.period || 1.2) / (o.period || 1.2);
    ctx.save(); ctx.globalAlpha *= (1 - k) * .5; ctx.strokeStyle = col; ctx.lineWidth = r * .5; ctx.beginPath(); ctx.arc(x, y, r * (1.4 + k * 2.4), 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
  ctx.save(); ctx.shadowColor = rgba(col, .5); ctx.shadowBlur = r * 1.6; circle(x, y, r * 1.45, '#ffffff'); ctx.restore();
  circle(x, y, r, col);
}

/* ---------- 卡片與進場 ---------- */
/** 浮起的白卡：大圓角、三層柔和陰影（環境／主光／接觸）、頂部玻璃反光、內緣白線。o.glow 背後色光、o.fill 底色、o.lift 0–1 浮起量、o.r 圓角 */
function uiCard(x, y, w, h, o = {}) {
  const r = o.r ?? Math.min(w, h) * .1, lift = o.lift ?? .6, fill = o.fill || '#ffffff', S = UIC.shade;
  if (o.glow) glow(x + w / 2, y + h * .62, Math.max(w, h) * .8, o.glow, .3 * lift);
  ctx.save();
  ctx.shadowColor = `rgba(${S},${.06 + .08 * lift})`; ctx.shadowBlur = MIN * (.05 + .09 * lift); ctx.shadowOffsetY = MIN * (.02 + .04 * lift); fillRR(x, y, w, h, r, fill);
  ctx.shadowColor = `rgba(${S},${.05 + .05 * lift})`; ctx.shadowBlur = MIN * (.01 + .012 * lift); ctx.shadowOffsetY = MIN * (.004 + .006 * lift); fillRR(x, y, w, h, r, fill);
  ctx.restore();
  ctx.save(); rrect(x, y, w, h, r); ctx.clip();
  const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(1, 'rgba(226,232,240,.35)');
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
  const s = ctx.createLinearGradient(x, y, x + w * .55, y + h * .45); s.addColorStop(0, 'rgba(255,255,255,.75)'); s.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = s; ctx.fillRect(x, y, w, h * .5);
  strokeRR(x + 1.5, y + 1.5, w - 3, h - 3, r - 1.5, 'rgba(255,255,255,.9)', 1.5);
  ctx.restore();
  strokeRR(x + .5, y + .5, w - 1, h - 1, r, `rgba(${S},.08)`, 1);
}

/** 彈入進場：start 秒起由 o.from（預設 .9）彈到 1、由下 o.dy 滑上、淡入，以 (cx, cy) 為縮放中心呼叫 draw()。o.freq / o.damp 彈簧參數 */
function uiIn(t, start, cx, cy, draw, o = {}) {
  const a = clamp((t - start) * (o.fade || 5)); if (a <= 0) return;
  const k = spring(t, start, o.freq || 2, o.damp ?? .5), sc = lerp(o.from ?? .9, 1, k);
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(cx, cy + (1 - k) * (o.dy ?? MIN * .05)); ctx.scale(sc, sc); ctx.translate(-cx, -cy);
  draw(); ctx.restore();
}

/* ---------- 數字與標籤 ---------- */
/** 數字滾動：from → to，start 秒開始、dur 秒，快進慢停（o.ease 可換）。回傳格式化字串（千分位、o.dp 小數位、o.pre / o.post 前後綴） */
function uiCount(t, start, dur, from, to, o = {}) {
  const v = lerp(from, to, E[o.ease || 'expo'](prog(t, start, start + dur)));
  return (o.pre || '') + v.toLocaleString('en-US', { minimumFractionDigits: o.dp || 0, maximumFractionDigits: o.dp || 0 }) + (o.post || '');
}

/** 成長標籤（「+18% this month」膠囊）：(x, y) 左側中心（o.align 'center' 時為中心）。p 0–1 彈入。o.arrow 'up' / 'down' / false、o.col 主色。回傳寬度 */
function uiBadge(x, y, s, p = 1, o = {}) {
  const size = o.size || MIN * .022, col = o.col || (o.arrow === 'down' ? UIC.bad : UIC.ok), arrow = o.arrow ?? 'up';
  const m = measure(s, { size, weight: 800 }), h = size * 1.75, w = m.w + h * (arrow ? 1.45 : .9);
  if (p <= 0) return w;
  const k = uiBack(p, 1.8), x0 = o.align === 'center' ? x - w / 2 : x;
  ctx.save(); ctx.translate(x0 + h * .5, y); ctx.scale(k, k); ctx.translate(-h * .5, 0); ctx.globalAlpha *= clamp(p * 3);
  fillRR(0, -h / 2, w, h, h / 2, rgba(col, .13));
  let tx = h * .45;
  if (arrow) {
    circle(h / 2, 0, h * .33, col); const d = arrow === 'down' ? -1 : 1;
    ctx.strokeStyle = '#fff'; ctx.lineWidth = h * .085; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath();
    ctx.moveTo(h / 2, h * .16 * d); ctx.lineTo(h / 2, -h * .16 * d); ctx.moveTo(h / 2 - h * .13, -h * .03 * d); ctx.lineTo(h / 2, -h * .16 * d); ctx.lineTo(h / 2 + h * .13, -h * .03 * d); ctx.stroke();
    tx = h * .98;
  }
  txtB(s, tx, 0, { size, weight: 800, color: o.ink || mixc(col, UIC.ink, .35), ui: true });
  ctx.restore(); return w;
}

/** 結果膠囊（「447 sales」「4 new stores」「Goal hit」）：(cx, cy) 中心、白底浮起、左邊色圓配圖示。p 0–1 彈入、o.bump 0–1 額外放大（收到粒子時跳一下）、o.glyph 圖示、o.col、o.size。回傳 { w, h } */
function uiResult(cx, cy, s, p = 1, o = {}) {
  const size = o.size || MIN * .032, col = o.col || STYLE.c.a1, m = measure(s, { size, weight: 800 }), h = size * 2.1, w = m.w + h * 1.45;
  if (p <= 0) return { w, h };
  const k = uiBack(p, 2) * (1 + (o.bump || 0) * .08);
  ctx.save(); ctx.translate(cx, cy); ctx.scale(k, k); ctx.globalAlpha *= clamp(p * 3);
  glow(0, h * .2, w * .7, col, .25);
  ctx.save(); ctx.shadowColor = rgba(col, .35); ctx.shadowBlur = h * .55; ctx.shadowOffsetY = h * .2; fillRR(-w / 2, -h / 2, w, h, h / 2, '#ffffff'); ctx.restore();
  strokeRR(-w / 2 + .5, -h / 2 + .5, w - 1, h - 1, h / 2, rgba(col, .25), 1);
  const ix = -w / 2 + h * .52, g = ctx.createLinearGradient(0, -h * .36, 0, h * .36);
  g.addColorStop(0, mixc(col, '#ffffff', .25)); g.addColorStop(1, col); circle(ix, 0, h * .36, g);
  uiIcon(ix, 0, h * .62, o.glyph || 'check', '#ffffff');
  txtB(s, ix + h * .5, 0, { size, weight: 800, color: o.ink || UIC.ink, ui: true });
  ctx.restore(); return { w, h };
}

/** 打勾：(x, y) 中心、r 半徑，p 0–1 畫到哪。o.col 圓的顏色、o.bg false 只畫勾、o.burst true 完成時放射短線 */
function uiCheck(x, y, r, p, o = {}) {
  if (p <= 0) return;
  const k = uiBack(clamp(p / .55), 2.2), col = o.col || UIC.ok;
  if (o.burst && p > .5) { const b = clamp((p - .5) / .5), e = E.out(b);
    ctx.save(); ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.lineWidth = r * .14 * (1 - b); ctx.globalAlpha *= 1 - b;
    for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2, r0 = r * (1.2 + e * .5), r1 = r * (1.35 + e * .9);
      ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r0, y + Math.sin(a) * r0); ctx.lineTo(x + Math.cos(a) * r1, y + Math.sin(a) * r1); ctx.stroke(); }
    ctx.restore(); }
  if (o.bg !== false) { ctx.save(); ctx.translate(x, y); ctx.scale(k, k); ctx.shadowColor = rgba(col, .45); ctx.shadowBlur = r * .6; ctx.shadowOffsetY = r * .15; circle(0, 0, r, col); ctx.restore(); }
  const q = clamp((p - .15) / .6), pts = [[-.42, .02], [-.12, .3], [.44, -.28]];
  ctx.save(); ctx.strokeStyle = o.ink || '#fff'; ctx.lineWidth = r * .22; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath();
  const L1 = Math.hypot(.3, .28), L2 = Math.hypot(.56, .58), d = E.out(q) * (L1 + L2);
  ctx.moveTo(x + pts[0][0] * r, y + pts[0][1] * r);
  if (d <= L1) { const u = d / L1; ctx.lineTo(x + lerp(pts[0][0], pts[1][0], u) * r, y + lerp(pts[0][1], pts[1][1], u) * r); }
  else { const u = (d - L1) / L2; ctx.lineTo(x + pts[1][0] * r, y + pts[1][1] * r); ctx.lineTo(x + lerp(pts[1][0], pts[2][0], u) * r, y + lerp(pts[1][1], pts[2][1], u) * r); }
  ctx.stroke(); ctx.restore();
}

/* ---------- 圖示 ---------- */
/** 線條圖示：(cx, cy) 中心、s 尺寸、glyph：chart / user / bell / check / plus / calendar / cart / pin / star / bolt / mail，col 線色 */
function uiIcon(cx, cy, s, glyph, col = '#ffffff') {
  const P = (a, b) => [cx + a * s, cy + b * s];
  ctx.save(); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = s * .085; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const L = (...pts) => { ctx.beginPath(); pts.forEach((p, i) => { const q = P(...p); i ? ctx.lineTo(...q) : ctx.moveTo(...q); }); ctx.stroke(); };
  if (glyph === 'chart') { [[-.2, .1], [0, -.06], [.2, -.22]].forEach(([x, top]) => L([x, .24], [x, top])); }
  else if (glyph === 'user') { ctx.beginPath(); ctx.arc(cx, cy - s * .1, s * .13, 0, Math.PI * 2); ctx.stroke(); ctx.beginPath(); ctx.arc(cx, cy + s * .3, s * .24, Math.PI * 1.08, Math.PI * 1.92); ctx.stroke(); }
  else if (glyph === 'bell') { ctx.beginPath(); ctx.moveTo(...P(-.22, .13)); ctx.quadraticCurveTo(...P(-.16, .05), ...P(-.16, -.04)); ctx.arc(cx, cy - s * .04, s * .16, Math.PI, 0); ctx.quadraticCurveTo(...P(.16, .05), ...P(.22, .13)); ctx.closePath(); ctx.stroke(); L([-.05, .23], [.05, .23]); }
  else if (glyph === 'check') L([-.2, .01], [-.06, .15], [.21, -.14]);
  else if (glyph === 'plus') { L([0, -.2], [0, .2]); L([-.2, 0], [.2, 0]); }
  else if (glyph === 'calendar') { ctx.beginPath(); rrect(cx - s * .22, cy - s * .17, s * .44, s * .4, s * .07); ctx.stroke(); L([-.22, -.05], [.22, -.05]); L([-.1, -.25], [-.1, -.13]); L([.1, -.25], [.1, -.13]);
    [[-.09, .07], [.04, .07], [-.09, .15]].forEach(([a, b]) => circle(...P(a + .02, b), s * .028, col)); }
  else if (glyph === 'cart') { L([-.26, -.18], [-.16, -.18], [-.08, .1], [.18, .1], [.24, -.1], [-.13, -.1]); circle(...P(-.05, .2), s * .04, col); circle(...P(.15, .2), s * .04, col); }
  else if (glyph === 'pin') { ctx.beginPath(); ctx.arc(cx, cy - s * .06, s * .16, Math.PI * .8, Math.PI * 2.2); ctx.lineTo(...P(0, .24)); ctx.closePath(); ctx.stroke(); circle(cx, cy - s * .06, s * .045, col); }
  else if (glyph === 'star') { ctx.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = s * (i % 2 ? .1 : .23); ctx.lineTo(cx + Math.cos(a) * rr, cy + .02 * s + Math.sin(a) * rr); } ctx.closePath(); ctx.stroke(); }
  else if (glyph === 'bolt') { ctx.beginPath(); [[.04, -.26], [-.14, .03], [0, .03], [-.04, .26], [.14, -.03], [0, -.03]].forEach((p, i) => i ? ctx.lineTo(...P(...p)) : ctx.moveTo(...P(...p))); ctx.closePath(); ctx.fill(); }
  else if (glyph === 'mail') { ctx.beginPath(); rrect(cx - s * .23, cy - s * .16, s * .46, s * .32, s * .05); ctx.stroke(); L([-.2, -.12], [0, .03], [.2, -.12]); }
  ctx.restore();
}

/** App 圖示磚：(x, y) 左上、s 邊長，glyph 見 uiIcon。漸層底、柔和色影、頂部高光。o.col 主色、o.p 0–1 彈入 */
function uiIconTile(x, y, s, glyph, o = {}) {
  const p = o.p ?? 1; if (p <= 0) return;
  const col = o.col || STYLE.c.a1, k = uiBack(p, 2), r = s * .27;
  ctx.save(); ctx.translate(x + s / 2, y + s / 2); ctx.scale(k, k); ctx.globalAlpha *= clamp(p * 3);
  const g = ctx.createLinearGradient(0, -s / 2, 0, s / 2); g.addColorStop(0, mixc(col, '#ffffff', .28)); g.addColorStop(1, mixc(col, '#000000', .08));
  ctx.save(); ctx.shadowColor = rgba(col, .4); ctx.shadowBlur = s * .32; ctx.shadowOffsetY = s * .12; fillRR(-s / 2, -s / 2, s, s, r, g); ctx.restore();
  const hi = ctx.createLinearGradient(0, -s / 2, 0, 0); hi.addColorStop(0, 'rgba(255,255,255,.35)'); hi.addColorStop(1, 'rgba(255,255,255,0)');
  fillRR(-s / 2, -s / 2, s, s * .5, r, hi);
  strokeRR(-s / 2 + 1, -s / 2 + 1, s - 2, s - 2, r - 1, 'rgba(255,255,255,.3)', 1);
  uiIcon(0, 0, s, glyph, '#ffffff');
  ctx.restore();
}

/* ---------- 圖表 ---------- */
/** 走勢線：(x, y) 左上、w × h，values 任意數字（自動依最小最大值縮放），p 0–1 畫到哪。平滑曲線＋下方漸層填色＋發光端點。o.col、o.lw、o.fill false、o.t（端點脈動）、o.min / o.max。回傳端點 {x, y} */
function uiSpark(x, y, w, h, values, p, o = {}) {
  if (p <= 0) return { x, y: y + h };
  const lo = o.min ?? Math.min(...values), hi = o.max ?? Math.max(...values), n = values.length, col = o.col || STYLE.c.a1;
  const pts = values.map((v, i) => [x + i / (n - 1) * w, y + h - (v - lo) / Math.max(1e-6, hi - lo) * h]);
  const part = _uiPartial(_uiCurve(pts), p), e = part.end;
  if (o.fill !== false) {
    const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, rgba(col, .24)); g.addColorStop(1, rgba(col, 0));
    _uiPath(part.pts); ctx.lineTo(e[0], y + h); ctx.lineTo(x, y + h); ctx.closePath(); ctx.fillStyle = g; ctx.fill();
  }
  ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = o.lw || Math.max(2, MIN * .005); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.shadowColor = rgba(col, .35); ctx.shadowBlur = MIN * .012; ctx.shadowOffsetY = MIN * .004; _uiPath(part.pts); ctx.stroke(); ctx.restore();
  if (o.dot !== false) uiDot(e[0], e[1], o.dotR || MIN * .0075, col, { t: o.t });
  return { x: e[0], y: e[1] };
}

/**
 * 長條長成趨勢線：values 0–1。p 0–1 長條依序彈起（約 6% 過衝），q 0–1 趨勢線畫到哪（長完再畫）。(x, y) 左上、w × h。
 * o.col 長條色、o.trend 趨勢線色、o.grid false 不畫格線、o.labels 底部標籤、o.dim 0–1 趨勢出現時長條變淡、o.t 端點脈動。回傳 { end, pts }
 */
function uiBars(x, y, w, h, values, p, q = 0, o = {}) {
  const n = values.length, lab = o.labels ? Math.min(h * .12, MIN * .03) : 0, bh0 = h - lab * 1.4, bw = w / n * (o.bw || .56), col = o.col || STYLE.c.a1;
  if (o.grid !== false) { ctx.save(); ctx.strokeStyle = rgba(UIC.sub, .14); ctx.lineWidth = 1; ctx.setLineDash([4, 6]);
    for (let i = 0; i < 4; i++) { const gy = Math.round(y + bh0 * i / 3) + .5; ctx.beginPath(); ctx.moveTo(x, gy); ctx.lineTo(x + w, gy); ctx.stroke(); } ctx.restore(); }
  const stg = .45 / n, dim = (o.dim ?? .45) * clamp(q * 2);
  const pts = values.map((v, i) => {
    const e = clamp((p - i * stg) / (1 - (n - 1) * stg)), k = uiBack(e, 1.2), bh = Math.max(0, bh0 * v * k);
    const bx = x + (i + .5) * w / n - bw / 2, by = y + bh0 - bh;
    if (bh > 1) {
      const g = ctx.createLinearGradient(0, by, 0, y + bh0); g.addColorStop(0, mixc(col, '#ffffff', dim * .6)); g.addColorStop(1, mixc(col, '#ffffff', .55 + dim * .3));
      ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, [Math.min(bw * .35, bh), Math.min(bw * .35, bh), Math.min(bw * .12, bh / 2), Math.min(bw * .12, bh / 2)]); ctx.fillStyle = g; ctx.fill();
    }
    if (o.labels) txtB(o.labels[i] ?? '', bx + bw / 2, y + h - lab * .5, { size: lab, weight: 600, color: UIC.sub, align: 'center', ui: true });
    return [bx + bw / 2, y + bh0 - bh0 * v - bh0 * .1];
  });
  let end = null;
  if (q > 0) {
    const tc = o.trend || UIC.ok, part = _uiPartial(_uiCurve(pts), E.io(clamp(q)));
    end = { x: part.end[0], y: part.end[1] };
    ctx.save(); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = MIN * .013; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; _uiPath(part.pts); ctx.stroke();
    ctx.strokeStyle = tc; ctx.lineWidth = MIN * .0065; ctx.shadowColor = rgba(tc, .45); ctx.shadowBlur = MIN * .015; _uiPath(part.pts); ctx.stroke(); ctx.restore();
    uiDot(end.x, end.y, MIN * .009, tc, { t: o.t });
  }
  return { end, pts };
}

/**
 * 粒子匯流（「Visits → sales」）：n 顆粒子散在 src {x, y, w, h} 範圍內，start 秒起錯開出發，沿弧線飛進 dst {x, y}，dur 為整組時長。
 * o.n 數量、o.col / o.col2 顏色、o.seed、o.size 粒子半徑、o.idle false 出發前不畫、o.ghost false 不留空心原位。回傳 { arrived 0–1, bump 0–1（剛有粒子抵達的脈衝） }
 */
function uiParticlesTo(t, start, dur, src, dst, o = {}) {
  const n = o.n || 40, R = rng(o.seed || 7), col = o.col || STYLE.c.a1, col2 = o.col2 || UIC.ok, sz = o.size || MIN * .007, fly = dur * .45;
  let arrived = 0, last = -1e9;
  for (let i = 0; i < n; i++) {
    const sx = src.x + R() * src.w, sy = src.y + R() * src.h, d = start + R() * (dur - fly), lift = (R() - .5) * .5, ph = R() * 6.28, sr = sz * (.7 + R() * .6);
    const u = (t - d) / fly, bx = sx + Math.sin(t * 1.3 + ph) * sz * 1.2, by = sy + Math.cos(t * 1.1 + ph) * sz * 1.2;
    if (u > 0 && o.ghost !== false) { ctx.strokeStyle = rgba(col, .22 * clamp(u * 3)); ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(sx, sy, sr, 0, Math.PI * 2); ctx.stroke(); }   // 出發後留下空心的原位
    if (u >= 1) { arrived++; last = Math.max(last, d + fly); continue; }
    if (u <= 0) { if (o.idle !== false) circle(bx, by, sr, rgba(col, .55)); continue; }
    const at = v => arcPt(bx, by, dst.x, dst.y, E.io(clamp(v)), lift), c = mixc(col, col2, E.io(u));
    for (let k = 3; k >= 1; k--) { const q = at(u - k * .035); circle(q.x, q.y, sr * (1 - u * .5) * (1 - k * .2), rgba(c, .16 * (4 - k))); }
    const q = at(u); circle(q.x, q.y, sr * (1 - u * .45), c);
  }
  return { arrived: arrived / n, bump: Math.exp(-Math.max(0, t - last) * 8) * (arrived > 0 && arrived < n + 1 ? 1 : 0) };
}

/** 目標環（「Rings → closed」）：(cx, cy) 中心、r 最外圈半徑，ps 每圈進度 0–1（外到內），o.cols 每圈顏色、o.w 線寬比例、o.gap 圈距。合攏的圈端點加光 */
function uiGoalRings(cx, cy, r, ps, o = {}) {
  const cols = o.cols || [STYLE.c.a1, UIC.ok, UIC.warn], lw = r * (o.w || .15), gap = lw * (o.gap ?? 1.22);
  ps.forEach((p, i) => {
    const rr = r - i * gap, col = cols[i % cols.length], a0 = -Math.PI / 2, v = clamp(p), a1 = a0 + Math.PI * 2 * v;
    ctx.save(); ctx.lineWidth = lw; ctx.lineCap = 'round';
    ctx.strokeStyle = rgba(col, .14); ctx.beginPath(); ctx.arc(cx, cy, rr, 0, Math.PI * 2); ctx.stroke();
    if (v > 0) {
      const g = ctx.createConicGradient ? ctx.createConicGradient(a0, cx, cy) : null;
      if (g) { g.addColorStop(0, mixc(col, '#ffffff', .35)); g.addColorStop(Math.max(.02, v * .999), col); g.addColorStop(1, col); }
      ctx.strokeStyle = g || col; ctx.beginPath(); ctx.arc(cx, cy, rr, a0, a1); ctx.stroke();
      const ex = cx + Math.cos(a1) * rr, ey = cy + Math.sin(a1) * rr;   // 端點的小影子，讓接合處有層次
      ctx.shadowColor = 'rgba(15,23,42,.25)'; ctx.shadowBlur = lw * .4; circle(ex, ey, lw / 2, col);
    }
    ctx.restore();
    if (v >= 1) glow(cx, cy - rr, lw * 2.2, col, .5);
  });
}

/* ---------- 地圖與路線 ---------- */
function _uiBlob(cx, cy, r, R, k = .3) {
  const n = 9, pts = []; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, rr = r * (1 + (R() - .5) * k * 2); pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * .8]); }
  ctx.beginPath(); const m = i => pts[(i + n) % n], mid = i => [(m(i)[0] + m(i + 1)[0]) / 2, (m(i)[1] + m(i + 1)[1]) / 2];
  ctx.moveTo(...mid(0)); for (let i = 1; i <= n; i++) ctx.quadraticCurveTo(...m(i), ...mid(i)); ctx.closePath();
}
/** 抽象地圖底：(x, y, w, h) 圓角區塊內畫陸地、水域、綠地與街道（rng 產生，非真實地理）。o.seed、o.r 圓角 */
function uiMap(x, y, w, h, o = {}) {
  const R = rng(o.seed || 11), r = o.r ?? Math.min(w, h) * .08;
  ctx.save(); rrect(x, y, w, h, r); ctx.clip();
  ctx.fillStyle = '#f3f5f9'; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = '#dbeafe'; _uiBlob(x + w * (.1 + R() * .15), y + h * (.85 + R() * .1), Math.max(w, h) * .32, R); ctx.fill();
  _uiBlob(x + w * (.95 + R() * .05), y + h * (.05 + R() * .1), Math.max(w, h) * .2, R); ctx.fill();
  ctx.fillStyle = '#dcfce7'; for (let i = 0; i < 3; i++) { _uiBlob(x + w * (.2 + R() * .6), y + h * (.15 + R() * .55), Math.min(w, h) * (.06 + R() * .05), R, .25); ctx.fill(); }
  const road = (pts, lw) => { const s = _uiCurve(pts, 10); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.strokeStyle = '#e2e8f0'; ctx.lineWidth = lw + 2; _uiPath(s); ctx.stroke(); ctx.strokeStyle = '#ffffff'; ctx.lineWidth = lw; _uiPath(s); ctx.stroke(); };
  for (let i = 0; i < 4; i++) { const yy = y + h * (.12 + i * .25 + (R() - .5) * .08); road([[x - w * .05, yy], [x + w * .35, yy + (R() - .5) * h * .12], [x + w * .7, yy + (R() - .5) * h * .12], [x + w * 1.05, yy + (R() - .5) * h * .1]], MIN * (i % 2 ? .006 : .011)); }
  for (let i = 0; i < 4; i++) { const xx = x + w * (.1 + i * .27 + (R() - .5) * .08); road([[xx, y - h * .05], [xx + (R() - .5) * w * .1, y + h * .4], [xx + (R() - .5) * w * .12, y + h * .75], [xx + (R() - .5) * w * .08, y + h * 1.05]], MIN * (i % 2 ? .011 : .006)); }
  ctx.restore();
}
/** 地圖圖釘：(x, y) 釘尖、s 高度，p 0–1 從上方掉下彈一下，o.col 顏色、o.glyph 釘頭裡的圖示（預設白點） */
function uiPin(x, y, s, p, o = {}) {
  if (p <= 0) return;
  const col = o.col || STYLE.c.a1, k = uiBack(p, 2.2), dy = (1 - E.out(clamp(p * 1.6))) * s * .8, r = s * .36;
  ctx.save(); ctx.globalAlpha *= clamp(p * 4);
  ctx.fillStyle = `rgba(${UIC.shade},${.18 * k})`; ctx.beginPath(); ctx.ellipse(x, y, r * .7 * k, r * .22 * k, 0, 0, Math.PI * 2); ctx.fill();
  ctx.translate(x, y - dy); ctx.scale(k, k);
  ctx.shadowColor = rgba(col, .45); ctx.shadowBlur = s * .3; ctx.shadowOffsetY = s * .08;
  const g = ctx.createLinearGradient(0, -s, 0, 0); g.addColorStop(0, mixc(col, '#ffffff', .25)); g.addColorStop(1, col);
  ctx.beginPath(); ctx.arc(0, -s + r, r, Math.PI * .78, Math.PI * 2.22); ctx.lineTo(0, 0); ctx.closePath(); ctx.fillStyle = g; ctx.fill();
  ctx.shadowColor = 'transparent';
  if (o.glyph) uiIcon(0, -s + r, r * 1.5, o.glyph, '#ffffff'); else circle(0, -s + r, r * .38, '#ffffff');
  ctx.restore();
}
/**
 * 路線（「Map → route」）：pts = [[x, y], …] 依序連起來，p 0–.85 畫線、最後 15% 留給終點圖釘彈完；路線經過的點依序掉下圖釘。
 * o.col 路線色、o.pinCol 圖釘色、o.pin 圖釘高、o.ghost false 不畫未走的虛線、o.lw 線寬、o.t 頭的脈動。回傳 { head {x, y}, reached 已到幾個點 }
 */
function uiRoute(pts, p, o = {}) {
  const col = o.col || STYLE.c.a1, seg = 14, s = _uiCurve(pts, seg), d = E.io(clamp(p / .85)), part = _uiPartial(s, d), lw = o.lw || MIN * .008;
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (o.ghost !== false) { ctx.strokeStyle = rgba(col, .3); ctx.lineWidth = lw * .5; ctx.setLineDash([lw * .2, lw * 1.6]); _uiPath(s); ctx.stroke(); ctx.setLineDash([]); }
  if (p > 0) { ctx.strokeStyle = '#ffffff'; ctx.lineWidth = lw * 2; _uiPath(part.pts); ctx.stroke();
    ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.shadowColor = rgba(col, .4); ctx.shadowBlur = lw * 1.5; _uiPath(part.pts); ctx.stroke(); }
  ctx.restore();
  const L = part.total * d; let reached = 0;
  pts.forEach((q, i) => {
    const at = part.cum[Math.min(i * seg, part.cum.length - 1)] / Math.max(1, part.total), pp = i === 0 ? 1 : at > .999 ? clamp((p - .85) / .15) : clamp((d - at) / .14);
    if (L >= part.cum[Math.min(i * seg, part.cum.length - 1)] - 1) reached++;
    if (i === 0) { circle(q[0], q[1], lw * 1.3, '#ffffff'); circle(q[0], q[1], lw * .85, col); }
    else uiPin(q[0], q[1], o.pin || MIN * .05, pp, { col: o.pinCol || UIC.ok, glyph: o.glyph });
  });
  if (p > 0 && d < 1) uiDot(part.end[0], part.end[1], lw * .9, col, { t: o.t });
  return { head: { x: part.end[0], y: part.end[1] }, reached };
}

/* ---------- 價格卡、字重、滑桿 ---------- */
/**
 * 價格卡翻轉（「Card → 360°」）：(cx, cy) 中心、w × h，a 轉了幾圈（0 → 1 = 360°，cos 縮放＋斜切做出 3D 感，背面朝前時畫背面）。
 * o.front = { name, sub, price, cur, was（劃掉的原價）, tag（角落標籤）}、o.back = { title, items: [] }、o.col 主色、o.glyph 商品圖示
 */
function uiPriceCard(cx, cy, w, h, a, o = {}) {
  const ang = a * Math.PI * 2, c = Math.cos(ang), sx = Math.max(.02, Math.abs(c)), sk = Math.sin(ang) * .12, col = o.col || STYLE.c.a1, back = c < 0;
  const ew = w * .5 * (.35 + .65 * sx), sg = ctx.createRadialGradient(0, 0, 0, 0, 0, 1);   // 地面影子：轉到側面時收窄
  sg.addColorStop(0, `rgba(${UIC.shade},${.22 * (.4 + .6 * sx)})`); sg.addColorStop(1, `rgba(${UIC.shade},0)`);
  ctx.save(); ctx.translate(cx, cy + h * .53); ctx.scale(ew, h * .05); ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(0, 0, 1, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  ctx.save(); ctx.translate(cx, cy); ctx.transform(sx, sk * sx, 0, 1, 0, 0); ctx.translate(-w / 2, -h / 2);
  uiCard(0, 0, w, h, { r: w * .09, lift: .5 + .3 * (1 - sx) });
  const pad = w * .09, F = o.front || {}, B = o.back || {};
  if (!back) {
    const ih = h * .46, g = ctx.createLinearGradient(0, pad, 0, pad + ih);
    g.addColorStop(0, mixc(col, '#ffffff', .82)); g.addColorStop(1, mixc(col, '#ffffff', .62)); fillRR(pad, pad, w - pad * 2, ih, w * .06, g);
    const pr = Math.min(w, ih) * .26, px = w / 2, py = pad + ih * .52;   // 商品：光滑的球形圖示
    glow(px, py + pr * .3, pr * 2.2, col, .35);
    const bg = ctx.createRadialGradient(px - pr * .35, py - pr * .4, pr * .1, px, py, pr); bg.addColorStop(0, mixc(col, '#ffffff', .55)); bg.addColorStop(1, mixc(col, '#000000', .12));
    ctx.save(); ctx.shadowColor = rgba(col, .45); ctx.shadowBlur = pr * .6; ctx.shadowOffsetY = pr * .25; circle(px, py, pr, bg); ctx.restore();
    uiIcon(px, py, pr * 1.3, o.glyph || 'bolt', 'rgba(255,255,255,.95)');
    if (F.tag) uiBadge(pad * 1.5, pad * 1.6, F.tag, 1, { arrow: false, col, size: h * .034 });
    const ty = pad + ih + h * .085;
    txtB(F.name || 'Product', pad, ty, { size: h * .058, weight: 800, color: UIC.ink, fit: { lines: 1, min: .6 }, maxW: w - pad * 2, ui: true });
    if (F.sub) txtB(F.sub, pad, ty + h * .065, { size: h * .038, weight: 500, color: UIC.sub, fit: { lines: 1, min: .6 }, maxW: w - pad * 2, ui: true });
    const py2 = h - pad - h * .06, cz = h * .05, pz = h * .12, cw = measure(F.cur || '$', { size: cz, weight: 700 }).w;
    txtB(F.cur || '$', pad, py2 - pz * .22, { size: cz, weight: 700, color: UIC.ink, ui: true });
    const pw = txtB(F.price || '0', pad + cw + cz * .15, py2, { size: pz, weight: 800, color: UIC.ink, track: -.02, ui: true }).w;
    if (F.was) { const wx = pad + cw + cz * .15 + pw + pz * .2, ww = txtB(F.was, wx, py2 + pz * .12, { size: cz, weight: 600, color: UIC.sub, ui: true }).w;
      ctx.strokeStyle = UIC.bad; ctx.lineWidth = Math.max(1.5, cz * .09); ctx.beginPath(); ctx.moveTo(wx - 2, py2 + pz * .12); ctx.lineTo(wx + ww + 2, py2 + pz * .12); ctx.stroke(); }
  } else {
    ctx.save(); ctx.translate(w, 0); ctx.scale(-1, 1);   // 背面左右反過來畫，轉到正面時字才是正的
    const g = ctx.createLinearGradient(0, 0, w, h); g.addColorStop(0, mixc(col, '#ffffff', .1)); g.addColorStop(1, mixc(col, '#000000', .2));
    fillRR(0, 0, w, h, w * .09, g);
    txtB(B.title || 'Details', pad, pad + h * .06, { size: h * .06, weight: 800, color: '#ffffff', fit: { lines: 1, min: .6 }, maxW: w - pad * 2, ui: true });
    (B.items || []).forEach((s, i) => { const yy = pad + h * (.24 + i * .13);
      circle(pad + h * .03, yy, h * .03, 'rgba(255,255,255,.22)'); uiIcon(pad + h * .03, yy, h * .06, 'check', '#ffffff');
      txtB(s, pad + h * .085, yy, { size: h * .042, weight: 600, color: 'rgba(255,255,255,.92)', fit: { lines: 1, min: .6 }, maxW: w - pad * 2 - h * .085, ui: true }); });
    ctx.restore();
  }
  if (sx < .999) { ctx.fillStyle = `rgba(15,23,42,${(1 - sx) * .18})`; fillRR(0, 0, w, h, w * .09); }   // 側轉時變暗
  ctx.restore();
}

/** 滑桿：(x, y) 軌道左端中心、w 長，p 0–1 把手位置。o.col、o.h 軌道粗、o.label 把手上方的數值泡泡、o.press 0–1 把手被按住（放大） */
function uiSlider(x, y, w, p, o = {}) {
  const h = o.h || MIN * .012, col = o.col || STYLE.c.a1, kx = x + w * clamp(p), kr = h * 1.25 * (1 + (o.press || 0) * .15);
  fillRR(x, y - h / 2, w, h, h / 2, UIC.line);
  const g = ctx.createLinearGradient(x, 0, kx, 0); g.addColorStop(0, mixc(col, '#ffffff', .35)); g.addColorStop(1, col);
  if (kx - x > 1) fillRR(x, y - h / 2, kx - x, h, h / 2, g);
  ctx.save(); ctx.shadowColor = `rgba(${UIC.shade},.28)`; ctx.shadowBlur = kr * .8; ctx.shadowOffsetY = kr * .2; circle(kx, y, kr, '#ffffff'); ctx.restore();
  strokeRR(kx - kr, y - kr, kr * 2, kr * 2, kr, `rgba(${UIC.shade},.08)`, 1);
  if (o.label) { const z = h * 1.9, m = measure(o.label, { size: z, weight: 800 }), bw = m.w + z * 1.1, bh = z * 1.7, by = y - kr - bh * .85;
    fillRR(kx - bw / 2, by - bh / 2, bw, bh, bh * .35, UIC.ink);
    ctx.beginPath(); ctx.moveTo(kx - z * .35, by + bh / 2 - 1); ctx.lineTo(kx, by + bh / 2 + z * .35); ctx.lineTo(kx + z * .35, by + bh / 2 - 1); ctx.fillStyle = UIC.ink; ctx.fill();
    txtB(o.label, kx, by, { size: z, weight: 800, color: '#ffffff', align: 'center', ui: true }); }
  return { x: kx, y };
}

/**
 * 字重變化（「Weight → bold」）：大字 word 以 (cx, cy) 為中心，p 0–1 由細變粗（同色描邊加粗＋字距微開，連續不跳格）。
 * o.size 字級、o.col 顏色（可給 gradient: [c1, c2]）、o.from / o.to 字重（顯示用，預設 300 → 900）。回傳目前字重數值
 */
function uiWeight(cx, cy, word, p, o = {}) {
  const size = o.size || MIN * .2, e = clamp(p), sw = size * .075 * e, track = -.03 + e * .02;
  ctx.save(); setFont(size, e < .5 ? 400 : 600, 'display'); ctx.letterSpacing = (track * size) + 'px'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const mw = ctx.measureText(word).width;
  let fill = o.col || UIC.ink;
  if (o.gradient) { const g = ctx.createLinearGradient(cx - mw / 2, 0, cx + mw / 2, 0); o.gradient.forEach((c, i) => g.addColorStop(i / (o.gradient.length - 1), c)); fill = g; }
  ctx.fillStyle = fill; ctx.strokeStyle = fill; ctx.lineJoin = 'round';
  ctx.shadowColor = `rgba(${UIC.shade},${.08 + .12 * e})`; ctx.shadowBlur = size * (.05 + .1 * e); ctx.shadowOffsetY = size * .04 * e;
  ctx.fillText(word, cx, cy); ctx.shadowColor = 'transparent';
  if (sw > .3) { ctx.lineWidth = sw; ctx.strokeText(word, cx, cy); }
  ctx.restore();
  return Math.round(lerp(o.from ?? 300, o.to ?? 900, e) / 100) * 100;
}

/**
 * KPI 卡（「0 → 12,480」）：(x, y) 左上、w × h。圖示磚＋標籤 → 大數字滾動 → 數完彈出成長標籤 → 走勢線（有給 spark 時）。
 * o = { label, to, from, start, dur, pre, post, dp, badge, badgeAt, spark: [數字…], icon, col, sub, lift }
 */
function uiKPI(x, y, w, h, t, o = {}) {
  const col = o.col || STYLE.c.a1, pad = Math.min(w, h) * .09, st = o.start ?? 0, dur = o.dur ?? 1.4, end = st + dur, bAt = o.badgeAt ?? end;
  uiCard(x, y, w, h, { lift: o.lift ?? .6 });
  const ts = Math.min(h * .15, w * .14);
  uiIconTile(x + pad, y + pad, ts, o.icon || 'user', { col });
  txtB(o.label || 'Subscribers', x + pad + ts * 1.3, y + pad + ts * (o.sub ? .32 : .5), { size: ts * .36, weight: 700, color: UIC.ink, fit: { lines: 1, min: .6 }, maxW: w - pad * 2 - ts * 1.3, ui: true });
  if (o.sub) txtB(o.sub, x + pad + ts * 1.3, y + pad + ts * .76, { size: ts * .28, weight: 500, color: UIC.sub, fit: { lines: 1, min: .6 }, maxW: w - pad * 2 - ts * 1.3, ui: true });
  const hasS = !!o.spark, fmt = { pre: o.pre, post: o.post, dp: o.dp }, final = uiCount(1, 0, 1, 0, o.to ?? 0, fmt);
  const z0 = h * (hasS ? .2 : .24), zs = z0 * Math.min(1, (w - pad * 2) / Math.max(1, measure(final, { size: z0, weight: 800, track: -.02 }).w));
  const ny = y + h * (hasS ? .43 : .52), bump = 1 + .05 * Math.exp(-Math.max(0, t - end) * 6) * (t > end ? Math.sin((t - end) * 18) : 0);
  ctx.save(); ctx.translate(x + pad, ny); ctx.scale(bump, bump);
  txtB(uiCount(t, st, dur, o.from ?? 0, o.to ?? 0, fmt), 0, 0, { size: zs, weight: 800, color: UIC.ink, track: -.02, ui: true }); ctx.restore();
  if (o.badge) uiBadge(x + pad, y + h * (hasS ? .6 : .76), o.badge, clamp((t - bAt) / .45), { size: Math.min(h * .055, w * .05), col: o.badgeCol });
  if (hasS) uiSpark(x + pad, y + h * .7, w - pad * 2, h * .2, o.spark, E.out(prog(t, st, end + .2)), { col, t });
}
