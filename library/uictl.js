/* uictl.js：UI 互動元件（ui.js 的延伸）——一個元件演一個「A → B」的產品瞬間：
 * 開關、分段切換、按鈕（按下 → 載入 → 完成）、進度環、通知、數字翻轉、狀態膠囊、動態島、信用卡與刷卡機、
 * 線框變 App、行事曆拖放、Dock、視窗從圖示打開、鎖定畫面通知堆疊。
 * 共用 ui.js 的 UIC、uiCard、uiCheck。全部是 t 的純函式；介面裡的字用 txtB(…, { ui: true, maxW })。
 * 範例：examples/ui-controls-demo。 */

/* ---------- 共用小工具 ---------- */

/** 按下的擠壓：at 秒按下，先壓扁再彈回（微微過衝）。回傳 { sx, sy, k }，以元件中心 ctx.scale(sx, sy) 套用 */
function uiPress(t, at, amt = .08) {
  const x = t - at; if (x < 0) return { sx: 1, sy: 1, k: 1 };
  const d = x < .09 ? E.out(x / .09) : 1 - spring(t, at + .09, 2.6, .32);
  return { sx: 1 + amt * .45 * d, sy: 1 - amt * d, k: 1 - amt * .6 * d };
}

/** 玻璃卡：半透明白底＋柔和陰影＋頂部高光＋白色細邊（壓在桌布、鎖定畫面上用）。o.fill 底色、o.sh 陰影濃度 */
function uiGlass(x, y, w, h, r, o = {}) {
  ctx.save(); ctx.shadowColor = `rgba(15,23,42,${o.sh ?? .14})`; ctx.shadowBlur = Math.min(w, h) * .35; ctx.shadowOffsetY = Math.min(w, h) * .1;
  ctx.fillStyle = o.fill || 'rgba(255,255,255,.8)'; fillRR(x, y, w, h, r); ctx.restore();
  ctx.save(); ctx.beginPath(); rrect(x, y, w, h, r); ctx.clip();
  const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, 'rgba(255,255,255,.55)'); g.addColorStop(.5, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h); ctx.restore();
  ctx.save(); ctx.strokeStyle = 'rgba(255,255,255,.75)'; ctx.lineWidth = Math.max(1, Math.min(w, h) * .012); strokeRR(x + .5, y + .5, w - 1, h - 1, r); ctx.restore();
}

/** 小圖示（線條／實心）：kind = check, doc, chat, mail, cal, chart, photo, bag, video, play, bell, pen, music, card, focus。(cx, cy) 中心、s 邊長 */
function uiGlyph(kind, cx, cy, s, col = '#fff') {
  const u = s / 2;
  ctx.save(); ctx.translate(cx, cy); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = s * .1; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const L = (pts) => { ctx.beginPath(); pts.forEach(([a, b], i) => i ? ctx.lineTo(a * u, b * u) : ctx.moveTo(a * u, b * u)); ctx.stroke(); };
  switch (kind) {
    case 'check': L([[-.55, .02], [-.15, .42], [.6, -.4]]); break;
    case 'doc': rrect(-u * .6, -u * .8, u * 1.2, u * 1.6, u * .2); ctx.stroke(); L([[-.28, -.25], [.28, -.25]]); L([[-.28, .08], [.28, .08]]); L([[-.28, .4], [.1, .4]]); break;
    case 'chat': rrect(-u * .82, -u * .7, u * 1.64, u * 1.18, u * .45); ctx.fill(); ctx.beginPath(); ctx.moveTo(-u * .45, u * .3); ctx.lineTo(-u * .6, u * .82); ctx.lineTo(-u * .05, u * .4); ctx.fill(); break;
    case 'mail': rrect(-u * .8, -u * .55, u * 1.6, u * 1.1, u * .18); ctx.stroke(); L([[-.72, -.42], [0, .12], [.72, -.42]]); break;
    case 'cal': rrect(-u * .75, -u * .62, u * 1.5, u * 1.42, u * .22); ctx.stroke(); L([[-.75, -.2], [.75, -.2]]); L([[-.38, -.85], [-.38, -.5]]); L([[.38, -.85], [.38, -.5]]);
      circle(-u * .3, u * .25, u * .11, col); circle(u * .05, u * .25, u * .11, col); circle(u * .4, u * .25, u * .11, col); break;
    case 'chart': [[-.62, .15], [-.12, -.25], [.38, -.7]].forEach(([x, y]) => { rrect(x * u, y * u, u * .34, (.8 - y) * u, u * .1); ctx.fill(); }); break;
    case 'photo': rrect(-u * .8, -u * .62, u * 1.6, u * 1.24, u * .2); ctx.stroke(); L([[-.62, .45], [-.18, -.05], [.12, .25], [.32, .08], [.62, .45]]); circle(u * .35, -u * .25, u * .13, col); break;
    case 'bag': rrect(-u * .66, -u * .3, u * 1.32, u * 1.1, u * .2); ctx.fill(); ctx.beginPath(); ctx.arc(0, -u * .3, u * .34, Math.PI, 0); ctx.stroke(); break;
    case 'video': rrect(-u * .82, -u * .48, u * 1.12, u * .96, u * .22); ctx.fill(); ctx.beginPath(); ctx.moveTo(u * .38, -u * .08); ctx.lineTo(u * .85, -u * .42); ctx.lineTo(u * .85, u * .42); ctx.lineTo(u * .38, u * .08); ctx.closePath(); ctx.fill(); break;
    case 'play': ctx.beginPath(); ctx.moveTo(-u * .38, -u * .55); ctx.lineTo(u * .6, 0); ctx.lineTo(-u * .38, u * .55); ctx.closePath(); ctx.fill(); break;
    case 'bell': ctx.beginPath(); ctx.moveTo(-u * .62, u * .4); ctx.quadraticCurveTo(-u * .5, u * .2, -u * .5, -u * .1); ctx.arc(0, -u * .1, u * .5, Math.PI, 0); ctx.quadraticCurveTo(u * .5, u * .2, u * .62, u * .4); ctx.closePath(); ctx.fill(); circle(0, u * .62, u * .16, col); break;
    case 'pen': L([[-.75, .3], [-.45, -.25], [-.2, .35], [.05, -.15], [.25, .25], [.75, -.3]]); break;
    case 'music': L([[-.15, .5], [-.15, -.6], [.55, -.75], [.55, .35]]); circle(-u * .38, u * .52, u * .26, col); circle(u * .32, u * .38, u * .26, col); break;
    case 'card': rrect(-u * .82, -u * .55, u * 1.64, u * 1.1, u * .18); ctx.stroke(); ctx.fillRect(-u * .82, -u * .28, u * 1.64, u * .2); break;
    case 'focus': ctx.beginPath(); ctx.arc(0, 0, u * .7, 0, Math.PI * 2); ctx.stroke(); circle(0, 0, u * .28, col); break;
    default: circle(0, 0, u * .4, col);
  }
  ctx.restore();
}

/* ---------- 開關、分段、按鈕、進度環 ---------- */

/** 開關：(x, y) 左上、w 寬（高 = w × .56）。p 0（關）→ 1（開），建議傳 spring；鈕會沿途拉長、開啟時軌道發光。o.on 開的顏色、o.off 關的顏色 */
function uiToggle(x, y, w, p, o = {}) {
  const h = w * .56, c = clamp(p), q = clamp(p, -.08, 1.08), on = o.on || UIC.ok;
  ctx.save(); ctx.fillStyle = mixc(o.off || '#d6dce6', on, c); fillRR(x, y, w, h, h / 2);
  ctx.beginPath(); rrect(x, y, w, h, h / 2); ctx.clip();
  const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, 'rgba(15,23,42,.14)'); g.addColorStop(.35, 'rgba(15,23,42,0)');
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h); ctx.restore();
  if (c > .5) glow(x + w * .5, y + h * .55, w * .9, on, .3 * (c - .5) * 2);
  const kd = h * .84, kw = kd * (1 + Math.sin(c * Math.PI) * .3), cx = x + h / 2 + (w - h) * q;
  const kx = clamp(cx - kw / 2, x + h * .08 - h * .04, x + w - h * .08 - kw + h * .04);
  ctx.save(); ctx.shadowColor = 'rgba(15,23,42,.28)'; ctx.shadowBlur = h * .22; ctx.shadowOffsetY = h * .07;
  ctx.fillStyle = '#fff'; fillRR(kx, y + h * .08, kw, kd, kd / 2); ctx.restore();
  const kg = ctx.createLinearGradient(0, y + h * .08, 0, y + h * .92); kg.addColorStop(0, 'rgba(255,255,255,0)'); kg.addColorStop(1, 'rgba(15,23,42,.06)');
  ctx.fillStyle = kg; fillRR(kx, y + h * .08, kw, kd, kd / 2);
}

/**
 * 分段切換（Monthly／Yearly）：(x, y) 左上、w × h，labels 陣列，p 為目前位置（0 到 labels.length-1，可小數，建議傳 spring）。
 * 滑塊移動中會拉長。o.light：白色滑塊＋深色字（iOS 風）；否則滑塊用 o.on（預設 STYLE.c.a1）＋白字。o.track 軌道色
 */
function uiSegment(x, y, w, h, labels, p, o = {}) {
  const n = labels.length, sw = w / n, pad = h * .09, light = !!o.light;
  ctx.save(); ctx.fillStyle = o.track || '#e7ebf2'; fillRR(x, y, w, h, h / 2);
  ctx.beginPath(); rrect(x, y, w, h, h / 2); ctx.clip();
  const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, 'rgba(15,23,42,.1)'); g.addColorStop(.3, 'rgba(15,23,42,0)');
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h); ctx.restore();
  const pc = clamp(p, -.06, n - .94), f = pc - Math.floor(pc), st = Math.sin(clamp(f) * Math.PI) * .22;
  const kw = (sw - pad * 2) * (1 + st), kx = x + pad + pc * sw - (kw - (sw - pad * 2)) / 2, kh = h - pad * 2, col = light ? '#ffffff' : (o.on || STYLE.c.a1);
  ctx.save(); ctx.shadowColor = light ? 'rgba(15,23,42,.18)' : rgba(col, .45); ctx.shadowBlur = h * .3; ctx.shadowOffsetY = h * .08;
  ctx.fillStyle = col; fillRR(kx, y + pad, kw, kh, kh / 2); ctx.restore();
  const kg = ctx.createLinearGradient(0, y + pad, 0, y + pad + kh); kg.addColorStop(0, 'rgba(255,255,255,.3)'); kg.addColorStop(.6, 'rgba(255,255,255,0)');
  ctx.fillStyle = kg; fillRR(kx, y + pad, kw, kh, kh / 2);
  labels.forEach((s, i) => {
    const near = 1 - clamp(Math.abs(p - i));
    txtB(s, x + sw * (i + .5), y + h / 2, { size: h * .36, weight: 700, align: 'center', color: mixc(o.ink || UIC.sub, light ? UIC.ink : '#ffffff', near), maxW: sw * .84, ui: true });
  });
}

/**
 * 按鈕狀態：label →（tPress 按下、壓扁回彈）→ 載入（縮成圓圈轉）→（tDone）完成（彈開成綠色＋打勾＋doneLabel）。
 * (cx, cy) 中心、w × h。o = { label, doneLabel, col, okCol, doneW（完成寬，預設依字寬）}
 */
function uiButton(cx, cy, w, h, t, tPress, tDone, o = {}) {
  const pr = uiPress(t, tPress, .1), toLoad = E.io(prog(t, tPress + .08, tPress + .38)), toDone = spring(t, tDone, 2.2, .42);
  const loading = t >= tPress + .08 && t < tDone, done = t >= tDone, okCol = o.okCol || UIC.ok, base = o.col || STYLE.c.a1, fs = h * .38;
  const dw = o.doneW ? w * o.doneW : (o.doneLabel ? Math.min(w * 1.2, measure(o.doneLabel, { size: fs, weight: 800 }).w + h * 1.55) : w);
  const bw = done ? lerp(h, dw, clamp(toDone, 0, 1.12)) : lerp(w, h, toLoad);
  const col = done ? mixc(base, okCol, clamp(toDone * 1.5)) : base, dp = done ? uiPress(t, tDone, -.06) : pr;
  ctx.save(); ctx.translate(cx, cy); ctx.scale(pr.sx * (done ? dp.sx : 1), pr.sy * (done ? dp.sy : 1));
  if (done) glow(0, h * .1, dw * .75, okCol, .4 * Math.exp(-(t - tDone) * 1.6));
  ctx.save(); ctx.shadowColor = rgba(col, .42); ctx.shadowBlur = h * .55; ctx.shadowOffsetY = h * .2;
  ctx.fillStyle = col; fillRR(-bw / 2, -h / 2, bw, h, h / 2); ctx.restore();
  const g = ctx.createLinearGradient(0, -h / 2, 0, h / 2); g.addColorStop(0, 'rgba(255,255,255,.3)'); g.addColorStop(.55, 'rgba(255,255,255,0)'); g.addColorStop(1, 'rgba(0,0,0,.06)');
  ctx.fillStyle = g; fillRR(-bw / 2, -h / 2, bw, h, h / 2);
  if (!done && toLoad < .5) txtB(o.label || 'Publish', 0, 0, { size: fs, weight: 800, color: '#fff', align: 'center', maxW: Math.max(1, bw - h * .6), alpha: 1 - toLoad * 2, ui: true });
  if (loading) {
    const a = (t - tPress) * 8.5, la = clamp((toLoad - .6) * 3);
    ctx.globalAlpha *= la; ctx.lineWidth = h * .085; ctx.lineCap = 'round';
    ctx.strokeStyle = 'rgba(255,255,255,.3)'; ctx.beginPath(); ctx.arc(0, 0, h * .24, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = '#fff'; ctx.beginPath(); ctx.arc(0, 0, h * .24, a, a + 1.9 + Math.sin(a * .5) * .6); ctx.stroke();
  }
  if (done) {
    const lw = o.doneLabel ? measure(o.doneLabel, { size: fs, weight: 800 }).w : 0, gw = o.doneLabel ? h * .5 + lw : 0, ox = o.doneLabel ? -gw / 2 + h * .15 : 0;
    uiCheck(ox, 0, h * .32, prog(t, tDone + .05, tDone + .5), { bg: false });
    if (o.doneLabel) txtB(o.doneLabel, ox + h * .38, 0, { size: fs, weight: 800, color: '#fff', maxW: Math.max(1, bw - h * .9), alpha: clamp((t - tDone - .12) * 5), ui: true });
  }
  ctx.restore();
}

/** 進度環：(cx, cy) 中心、r 半徑、p 0–1。o.col 顏色、o.track 底色、o.w 線寬比例、o.label 中間大字、o.sub 小字；完成（p ≥ 1）時加光暈 */
function uiRing(cx, cy, r, p, o = {}) {
  const lw = r * (o.w || .16), col = o.col || UIC.ok, pc = clamp(p);
  ctx.save(); ctx.strokeStyle = o.track || rgba(col, .14); ctx.lineWidth = lw; ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
  if (p >= 1) glow(cx, cy, r * 1.6, col, .35);
  const a0 = -Math.PI / 2, a1 = a0 + Math.PI * 2 * pc;
  if (pc > .002) {
    const g = ctx.createConicGradient ? ctx.createConicGradient(a0, cx, cy) : null;
    if (g) { g.addColorStop(0, mixc(col, '#ffffff', .45)); g.addColorStop(Math.max(.01, pc), col); g.addColorStop(1, col); }
    ctx.shadowColor = rgba(col, .35); ctx.shadowBlur = lw * .8;
    ctx.strokeStyle = g || col; ctx.lineCap = 'round'; ctx.beginPath(); ctx.arc(cx, cy, r, a0, a1); ctx.stroke(); ctx.shadowColor = 'transparent';
    if (g) circle(cx, cy - r, lw / 2, mixc(col, '#ffffff', .45));   // 起點圓頭補上漸層起始色（否則會拿到漸層尾端的深色）
    circle(cx + Math.cos(a1) * r, cy + Math.sin(a1) * r, lw * .26, 'rgba(255,255,255,.9)');
  }
  ctx.restore();
  if (o.label) txtB(o.label, cx, cy - (o.sub ? r * .1 : 0), { size: r * (o.labelSize || .5), weight: 800, align: 'center', color: o.ink || UIC.ink, maxW: r * 1.5, ui: true });
  if (o.sub) txtB(o.sub, cx, cy + r * .32, { size: r * .17, weight: 600, align: 'center', color: UIC.sub, maxW: r * 1.4, ui: true });
}

/* ---------- 數字翻轉、狀態膠囊、成功迸發 ---------- */

/** 成功迸發：at 秒從 (cx, cy) 向外射出 n 條短線並淡出（Published、Paid、Booked 的句點）。r 半徑；o = { col, n, dur, ky（垂直壓扁比例，膠囊形用 .5）} */
function uiBurst(cx, cy, r, t, at, o = {}) {
  const u = (t - at) / (o.dur || .55); if (u <= 0 || u >= 1) return;
  const n = o.n || 10, e = E.out(u), ky = o.ky ?? 1;
  ctx.save(); ctx.strokeStyle = o.col || UIC.ok; ctx.lineCap = 'round'; ctx.lineWidth = MIN * .0045 * (1 - u) + 1; ctx.globalAlpha *= (1 - E.in(u)) * .85;
  for (let i = 0; i < n; i++) {
    const a = (i + .5) / n * Math.PI * 2, c = Math.cos(a), s = Math.sin(a) * ky, r0 = r * (.62 + e * .5), r1 = r * (.7 + e * .75);
    ctx.beginPath(); ctx.moveTo(cx + c * r0, cy + s * r0); ctx.lineTo(cx + c * r1, cy + s * r1); ctx.stroke();
  }
  ctx.restore();
}

/**
 * 數字翻轉（里程表）：from 字串翻成 to 字串，不同的字由下往上換、逐字錯開、落定時微彈。at 秒開始。
 * (x, y) 為對齊點（中線）。o = { size, weight, color, align（left/center/right）, gap（每字錯開秒數）, fam }
 */
function uiRoll(from, to, x, y, t, at, o = {}) {
  const size = o.size || MIN * .08, wt = o.weight || 800, fo = { size, weight: wt, fam: o.fam };
  const A = Array.from(String(from)), B = Array.from(String(to)), gap = o.gap ?? .06, al = o.align || 'left';
  const pre = arr => { const r = [0]; let s = ''; arr.forEach(ch => { s += ch; r.push(measure(s, fo).w); }); return r; };
  const pa = pre(A), pb = pre(B), wa = pa[A.length], wb = pb[B.length], e = E.io(prog(t, at, at + .45));
  const off = wv => al === 'center' ? -wv / 2 : al === 'right' ? -wv : 0;
  ctx.save(); ctx.beginPath(); ctx.rect(x - Math.max(wa, wb) * 1.2 - size, y - size * .64, Math.max(wa, wb) * 2.4 + size * 2, size * 1.28); ctx.clip();
  const n = Math.max(A.length, B.length), o2 = { size, weight: wt, fam: o.fam, color: o.color || UIC.ink, ui: true };
  for (let i = 0; i < n; i++) {
    const a = A[i], b = B[i], ox = x + off(wa) + pa[i], nx = x + off(wb) + pb[i];
    if (a === b) { txtB(a, lerp(ox, nx, e), y, o2); continue; }   // 相同的字只滑到新位置
    const k = clamp(spring(t, at + i * gap, 2.4, .5), 0, 1.15);
    if (a !== undefined && k < 1) txtB(a, ox, y - k * size * 1.05, { ...o2, alpha: 1 - clamp(k) });
    if (b !== undefined) txtB(b, nx, y + (1 - k) * size * 1.05, { ...o2, alpha: clamp(k * 1.6) });
  }
  ctx.restore();
  return { w: lerp(wa, wb, e) };
}

/**
 * 狀態膠囊（LIVE／Paid／Published／2 months free）：(cx, cy) 中心，at 秒彈出（spring 過衝）。
 * o.kind：'live'（紅點脈動）、'ok'（打勾）、'dot'、'none'，或 uiGlyph 的圖示名；o.col 主色；o.solid 實心底＋白字（預設淡色底）；
 * o.size 字級；o.align 'center'|'left'|'right'（cx 當中心／左緣／右緣）。回傳寬度
 */
function uiPill(cx, cy, s, t, at, o = {}) {
  const k = spring(t, at, 2.4, .42); if (k <= .001 && t < at + .05) return 0;
  const size = o.size || MIN * .022, kind = o.kind || 'dot', col = o.col || (kind === 'live' ? UIC.bad : UIC.ok), solid = !!o.solid;
  const tw_ = measure(s, { size, weight: 800 }).w, h = size * 1.9, ic = kind === 'none' ? 0 : h * .62, w = tw_ + h * .9 + ic;
  const x0 = o.align === 'left' ? cx : o.align === 'right' ? cx - w : cx - w / 2;
  ctx.save(); ctx.translate(x0 + w / 2, cy); ctx.scale(k, lerp(k, 1, .25)); ctx.globalAlpha *= clamp(k * 3);
  if (solid) { ctx.save(); ctx.shadowColor = rgba(col, .45); ctx.shadowBlur = h * .5; ctx.shadowOffsetY = h * .15; ctx.fillStyle = col; fillRR(-w / 2, -h / 2, w, h, h / 2); ctx.restore();
    const g = ctx.createLinearGradient(0, -h / 2, 0, h / 2); g.addColorStop(0, 'rgba(255,255,255,.28)'); g.addColorStop(.6, 'rgba(255,255,255,0)'); ctx.fillStyle = g; fillRR(-w / 2, -h / 2, w, h, h / 2);
  } else { ctx.fillStyle = mixc('#ffffff', col, .14); fillRR(-w / 2, -h / 2, w, h, h / 2); ctx.strokeStyle = rgba(col, .22); ctx.lineWidth = Math.max(1, h * .04); strokeRR(-w / 2, -h / 2, w, h, h / 2); }
  const ix = -w / 2 + h * .45 + ic * .4, fg = solid ? '#ffffff' : col;
  if (kind === 'live') {
    const ph = ((t - at) % 1 + 1) % 1, dc = solid ? '#ffffff' : col;
    ctx.save(); ctx.globalAlpha *= (1 - ph) * .6; ctx.strokeStyle = dc; ctx.lineWidth = h * .06; ctx.beginPath(); ctx.arc(ix, 0, h * .14 + ph * h * .26, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
    circle(ix, 0, h * (.15 + Math.sin((t - at) * Math.PI * 2) * .015), dc);
  } else if (kind === 'ok') { circle(ix, 0, ic * .45, solid ? 'rgba(255,255,255,.25)' : col); uiGlyph('check', ix, 0, ic * .55, '#ffffff'); }
  else if (kind === 'dot') circle(ix, 0, h * .14, fg);
  else if (kind !== 'none') uiGlyph(kind, ix, 0, ic * .75, fg);
  txtB(s, -w / 2 + h * .45 + ic, 0, { size, weight: 800, color: solid ? '#ffffff' : mixc(col, '#0f172a', .35), maxW: tw_ + 4, ui: true });
  ctx.restore(); return w;
}

/* ---------- 手機：動態島、鎖定畫面、通知 ---------- */

/**
 * 動態島：(cx, y) 為上緣中心、s 為螢幕寬。p 0（收起的小膠囊）→ 1（展開成即時活動），建議傳 spring（會過衝）。
 * o = { title, sub, icon（uiGlyph 名）, iconCol, live（右側 LIVE 膠囊文字，false 不畫）, t（脈動用）, at（膠囊出現秒數）}
 */
function uiIsland(cx, y, s, p, o = {}) {
  const w0 = s * .32, h0 = s * .09, w1 = s * .92, h1 = s * .24, q = Math.max(-.1, p);   // 小於 0 = 展開前的預備收縮
  const w = lerp(w0, w1, q), h = lerp(h0, h1, Math.min(q, 1 + (q - 1) * .4)), r = Math.min(h / 2, lerp(h0 / 2, h1 * .42, clamp(q)));
  ctx.save(); ctx.shadowColor = `rgba(0,0,0,${.35 * clamp(q)})`; ctx.shadowBlur = h * .4; ctx.shadowOffsetY = h * .12;
  ctx.fillStyle = '#000'; fillRR(cx - w / 2, y, w, h, r); ctx.restore();
  const a = clamp((p - .6) * 3); if (a <= 0) return { x: cx - w / 2, y, w, h };
  ctx.save(); ctx.globalAlpha *= a; const ih = h1 * .56, ix = cx - w / 2 + h1 * .2, iy = y + h / 2;
  ctx.fillStyle = o.iconCol || STYLE.c.a1; fillRR(ix, iy - ih / 2, ih, ih, ih * .28);
  uiGlyph(o.icon || 'video', ix + ih / 2, iy, ih * .55, '#fff');
  const tx = ix + ih + h1 * .14, liveW = o.live === false ? 0 : s * .24, tw_ = Math.max(1, w - (tx - (cx - w / 2)) - liveW - h1 * .2);
  if (o.title) txtB(o.title, tx, iy - (o.sub ? h1 * .13 : 0), { size: h1 * .2, weight: 700, color: '#ffffff', maxW: tw_, fit: { lines: 1, min: .6 }, ui: true });
  if (o.sub) txtB(o.sub, tx, iy + h1 * .16, { size: h1 * .16, weight: 500, color: 'rgba(255,255,255,.62)', maxW: tw_, fit: { lines: 1, min: .6 }, ui: true });
  ctx.restore();
  if (o.live !== false) uiPill(cx + w / 2 - h1 * .2 - liveW / 2, iy, o.live || 'LIVE', o.t ?? 0, o.at ?? 0, { kind: 'live', solid: true, col: UIC.bad, size: h1 * .15 });
  return { x: cx - w / 2, y, w, h };
}

/**
 * 通知堆疊：items = [{ at, title, sub, icon（uiGlyph 名）, col }]，新的從上方彈入、舊的往下推；
 * o.stackAt 秒後全部收成一疊（上層顯示 o.summary，例如「12 new orders」，下面兩張露邊）。
 * (x, y) 最上面一張左上、w 寬；o.h 卡高、o.glass 半透明玻璃（壓在桌布上）、o.app 右上角 App 名、o.time 右上時間字
 */
function uiNotifStack(x, y, w, items, t, o = {}) {
  const h = o.h || w * .24, gap = h * .14, peek = h * .16, shown = items.filter(it => t >= it.at - .02);
  const c = o.stackAt != null ? clamp(spring(t, o.stackAt, 2, .55), 0, 1.08) : 0, n = shown.length, r = h * .3;
  for (let k = 0; k < n; k++) {
    const it = shown[k], depth = n - 1 - k;
    let ly = y; for (let j = k + 1; j < n; j++) ly += (h + gap) * clamp(spring(t, shown[j].at, 2.2, .62), 0, 1.05);
    const inK = spring(t, it.at, 2.4, .5), enter = (1 - clamp(inK, 0, 1.2)) * h * .9;
    const sy = y + Math.min(depth, 2) * peek, sc = lerp(1, 1 - Math.min(depth, 2) * .06, clamp(c)), yy = lerp(ly - enter, sy, c);
    const a = clamp(inK * 2) * (depth > 2 ? 1 - clamp(c * 1.5) : 1); if (a <= 0) continue;
    ctx.save(); ctx.globalAlpha *= a; ctx.translate(x + w / 2, yy + h); ctx.scale(sc, sc); ctx.translate(-(x + w / 2), -(yy + h));
    if (o.glass) uiGlass(x, yy, w, h, r, { fill: depth ? 'rgba(241,245,250,.94)' : 'rgba(255,255,255,.95)' }); else uiCard(x, yy, w, h, { r, lift: .45 });
    const ca = depth === 0 ? 1 : 1 - clamp(c * 2.2);
    const sum = depth === 0 && c > .45 && o.summary, cf = sum ? clamp((c - .45) * 4) : 1;
    if (ca > 0) {
      ctx.save(); ctx.globalAlpha *= ca;
      const ic = h * .5, ix = x + h * .22, col = it.col || STYLE.c.a1;
      ctx.fillStyle = col; fillRR(ix, yy + (h - ic) / 2, ic, ic, ic * .26); uiGlyph(it.icon || 'bell', ix + ic / 2, yy + h / 2, ic * .55, '#fff');
      const tx = ix + ic + h * .2, mw = Math.max(1, x + w - tx - h * .5);
      if (o.app) txtB(o.app, tx, yy + h * .24, { size: h * .14, weight: 600, color: UIC.sub, maxW: mw * .7, ui: true });
      if (o.time) txtB(o.time, x + w - h * .22, yy + h * .24, { size: h * .14, weight: 500, color: UIC.sub, align: 'right', maxW: mw * .3, ui: true });
      const tA = sum ? 1 - cf : 1, title = it.title, sub = it.sub, ty = o.app ? .5 : .38, sy2 = o.app ? .74 : .64;
      if (tA > 0) { txtB(title, tx, yy + h * ty, { size: h * .19, weight: 800, color: UIC.ink, maxW: mw, alpha: tA, ui: true });
        if (sub) txtB(sub, tx, yy + h * sy2, { size: h * .16, weight: 500, color: UIC.sub, maxW: mw, alpha: tA, ui: true }); }
      if (sum) { txtB(o.summary, tx, yy + h * ty, { size: h * .19, weight: 800, color: UIC.ink, maxW: mw, alpha: cf, ui: true });
        if (o.summarySub) txtB(o.summarySub, tx, yy + h * sy2, { size: h * .16, weight: 500, color: UIC.sub, maxW: mw, alpha: cf, ui: true }); }
      ctx.restore();
    }
    ctx.restore();
  }
  return { h: c > .5 ? h + peek * Math.min(n - 1, 2) : n * (h + gap) - gap };
}

/**
 * 通知（相容舊版）：items = [{ at, title, sub, icon: 顏色 }]，新的從上方彈入、舊的往下疊並縮小。
 * (x, y) 最上面一張的左上、w 寬。最多顯示 o.max（預設 3）張；o.glass 玻璃卡、o.time 右上時間字
 */
function uiToasts(x, y, w, items, t, o = {}) {
  const h = o.h || w * .26, gap = h * .18, shown = items.filter(it => t >= it.at - .05), max = o.max || 3;
  shown.slice(-max - 1).forEach((it, idx, arr) => {
    const depth = arr.length - 1 - idx, d = spring(t, it.at, 2.2, .5), sc = 1 - Math.min(depth, max) * .06;
    const yy = y + depth * gap - (1 - clamp(d, 0, 1.2)) * h * 1.2, a = depth >= max ? 0 : clamp(d * 2) * (1 - depth * .18);
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha *= a; ctx.translate(x + w / 2, yy + h / 2); ctx.scale(sc, sc); ctx.translate(-(x + w / 2), -(yy + h / 2));
    if (o.glass) uiGlass(x, yy, w, h, h * .28); else uiCard(x, yy, w, h, { r: h * .28, lift: .5 });
    const ic = h * .52, col = it.icon && it.icon[0] === '#' ? it.icon : (it.col || STYLE.c.a1);
    ctx.fillStyle = col; fillRR(x + h * .24, yy + (h - ic) / 2, ic, ic, ic * .28);
    uiGlyph(it.glyph || 'bell', x + h * .24 + ic / 2, yy + h / 2, ic * .55, '#fff');
    const tx = x + h * .24 + ic + h * .2, mw = Math.max(1, w - (tx - x) - h * (o.time ? .9 : .3));
    txtB(it.title, tx, yy + h * .38, { size: h * .22, weight: 800, color: UIC.ink, maxW: mw, ui: true });
    if (it.sub) txtB(it.sub, tx, yy + h * .66, { size: h * .18, weight: 500, color: UIC.sub, maxW: mw, ui: true });
    if (o.time) txtB(o.time, x + w - h * .24, yy + h * .32, { size: h * .15, weight: 500, color: UIC.sub, align: 'right', maxW: h * .7, ui: true });
    ctx.restore();
  });
}

/**
 * 鎖定畫面：在 framePhone 回傳的 box 裡畫桌布、時間、日期，再接 uiNotifStack。
 * o = { time: '9:41', date, wall: [色, 色], items, stackAt, summary, summarySub, app }。回傳通知區 { x, y, w }
 */
function uiLockScreen(box, t, o = {}) {
  const { x, y, w, h } = box, wall = o.wall || [mixc(STYLE.c.a1, '#ffffff', .25), mixc(UIC.ok, '#ffffff', .35)];
  const g = ctx.createLinearGradient(x, y, x + w * .6, y + h); g.addColorStop(0, wall[0]); g.addColorStop(1, wall[1]);
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
  glow(x + w * .2, y + h * .3, w * .9, '#ffffff', .35); glow(x + w * .9, y + h * .85, w * .8, wall[0], .5);
  txtB(o.date || 'Tuesday, 14 October', x + w / 2, y + h * .14, { size: w * .05, weight: 600, color: 'rgba(255,255,255,.9)', align: 'center', maxW: w * .85, ui: true });
  txtB(o.time || '9:41', x + w / 2, y + h * .23, { size: w * .25, weight: 700, color: '#ffffff', align: 'center', maxW: w * .9, ui: true });
  const nx = x + w * .05, ny = y + h * .36, nw = w * .9;
  if (o.items) uiNotifStack(nx, ny, nw, o.items, t, { glass: true, h: nw * .24, stackAt: o.stackAt, summary: o.summary, summarySub: o.summarySub, app: o.app, time: o.timeAgo || 'now' });
  ctx.fillStyle = 'rgba(255,255,255,.85)'; fillRR(x + w * .35, y + h - w * .045, w * .3, w * .014, w * .007);
  return { x: nx, y: ny, w: nw };
}

/* ---------- 付款：信用卡、刷卡機 ---------- */

/** 信用卡：(cx, cy) 中心、w 寬（高 = w × .63）。o = { rot, col（主色）, col2, num: '4242', name, sheen（0–1 光澤掃過位置）} */
function uiCreditCard(cx, cy, w, o = {}) {
  const h = w * .63, r = w * .06, c1 = o.col || STYLE.c.a1, c2 = o.col2 || mixc(c1, '#0f172a', .45);
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(o.rot || 0);
  ctx.save(); ctx.shadowColor = 'rgba(15,23,42,.3)'; ctx.shadowBlur = w * .12; ctx.shadowOffsetY = w * .05;
  const g = ctx.createLinearGradient(-w / 2, -h / 2, w / 2, h / 2); g.addColorStop(0, mixc(c1, '#ffffff', .12)); g.addColorStop(1, c2);
  ctx.fillStyle = g; fillRR(-w / 2, -h / 2, w, h, r); ctx.restore();
  ctx.save(); ctx.beginPath(); rrect(-w / 2, -h / 2, w, h, r); ctx.clip();
  circle(w * .42, -h * .55, w * .5, 'rgba(255,255,255,.08)'); circle(w * .55, h * .1, w * .38, 'rgba(255,255,255,.06)');
  const sx = lerp(-w * 1.1, w * 1.1, o.sheen ?? .2), sg = ctx.createLinearGradient(sx - w * .3, 0, sx + w * .3, 0);
  sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(.5, 'rgba(255,255,255,.22)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = sg; ctx.fillRect(-w / 2, -h / 2, w, h);
  const hg = ctx.createLinearGradient(0, -h / 2, 0, 0); hg.addColorStop(0, 'rgba(255,255,255,.22)'); hg.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = hg; ctx.fillRect(-w / 2, -h / 2, w, h / 2);
  ctx.restore();
  const cw = w * .13, ch = w * .1, chx = -w * .39, chy = -h * .14;
  const cg = ctx.createLinearGradient(chx, chy, chx + cw, chy + ch); cg.addColorStop(0, '#f6e7b0'); cg.addColorStop(1, '#c9a24a');
  ctx.fillStyle = cg; fillRR(chx, chy, cw, ch, ch * .2);
  ctx.strokeStyle = 'rgba(120,90,30,.45)'; ctx.lineWidth = Math.max(1, w * .004); ctx.beginPath();
  ctx.moveTo(chx, chy + ch / 2); ctx.lineTo(chx + cw, chy + ch / 2); ctx.moveTo(chx + cw * .35, chy); ctx.lineTo(chx + cw * .35, chy + ch); ctx.moveTo(chx + cw * .65, chy); ctx.lineTo(chx + cw * .65, chy + ch); ctx.stroke();
  ctx.strokeStyle = 'rgba(255,255,255,.8)'; ctx.lineWidth = w * .009; ctx.lineCap = 'round';
  for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.arc(chx + cw + w * .03, chy + ch / 2, w * (.025 + i * .022), -.7, .7); ctx.stroke(); }
  txtB('••••  ••••  ••••  ' + (o.num || '4242'), -w * .39, h * .14, { size: w * .058, weight: 700, color: 'rgba(255,255,255,.95)', maxW: w * .8, track: .04, ui: true });
  txtB(o.name || 'ALEX MORGAN', -w * .39, h * .33, { size: w * .042, weight: 600, color: 'rgba(255,255,255,.78)', maxW: w * .55, track: .08, ui: true });
  circle(w * .3, h * .3, w * .055, 'rgba(255,255,255,.55)'); circle(w * .36, h * .3, w * .055, 'rgba(255,255,255,.3)');
  ctx.restore();
}

/**
 * 刷卡機（立架）：(cx, cy) 中心、w 寬（高 = w × 1.3），上緣有插卡槽。paid 0–1：螢幕從金額轉成綠色打勾。
 * 先畫卡片（插進槽的部分會被機身蓋住）再畫刷卡機。o = { amount, label, paidLabel }。回傳 { slotY, slotX, slotW, screen }
 */
function uiPOS(cx, cy, w, paid, o = {}) {
  const h = w * 1.3, x = cx - w / 2, y = cy - h / 2, r = w * .12, slotY = y + h * .02;
  ctx.save(); ctx.shadowColor = 'rgba(15,23,42,.22)'; ctx.shadowBlur = w * .2; ctx.shadowOffsetY = w * .08;
  ctx.fillStyle = '#ffffff'; fillRR(x, y, w, h, r); ctx.restore();
  const bg = ctx.createLinearGradient(0, y, 0, y + h); bg.addColorStop(0, '#ffffff'); bg.addColorStop(1, '#eef1f6'); ctx.fillStyle = bg; fillRR(x, y, w, h, r);
  ctx.fillStyle = '#1e293b'; fillRR(x + w * .08, slotY - w * .012, w * .84, w * .03, w * .015);
  const sx = x + w * .1, sy = y + h * .1, sw = w * .8, sh = h * .5, pc = clamp(paid);
  ctx.fillStyle = mixc('#0f172a', UIC.ok, pc); fillRR(sx, sy, sw, sh, w * .07);
  ctx.save(); ctx.beginPath(); rrect(sx, sy, sw, sh, w * .07); ctx.clip();
  const sg = ctx.createLinearGradient(sx, sy, sx + sw, sy + sh); sg.addColorStop(0, 'rgba(255,255,255,.14)'); sg.addColorStop(.5, 'rgba(255,255,255,0)'); ctx.fillStyle = sg; ctx.fillRect(sx, sy, sw, sh);
  ctx.restore();
  if (pc < 1) {
    txtB(o.label || 'Total', cx, sy + sh * .3 - pc * sh * .1, { size: w * .07, weight: 600, color: 'rgba(255,255,255,.6)', align: 'center', maxW: sw * .8, alpha: clamp(1 - pc * 2.5), ui: true });
    txtB(o.amount || '£290.00', cx, sy + sh * .55 - pc * sh * .1, { size: w * .13, weight: 800, color: '#ffffff', align: 'center', maxW: sw * .86, alpha: clamp(1 - pc * 2.5), ui: true });
  }
  if (pc > .25) { uiCheck(cx, sy + sh * .42, w * .12, clamp((pc - .25) / .75), { col: 'rgba(255,255,255,.25)' });
    txtB(o.paidLabel || 'Approved', cx, sy + sh * .78, { size: w * .075, weight: 800, color: '#ffffff', align: 'center', maxW: sw * .8, alpha: clamp(pc * 2 - 1), ui: true }); }
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) { ctx.fillStyle = '#dfe4ec'; fillRR(x + w * (.18 + j * .23), y + h * (.68 + i * .095), w * .18, h * .065, h * .03); }
  return { slotY, slotX: cx, slotW: w * .84, screen: { x: sx, y: sy, w: sw, h: sh } };
}

/* ---------- 線框 → App ---------- */

/**
 * 線框變成 App 畫面（Sketch → app）：在 (x, y, w, h)（通常是 framePhone 的 box）裡，各區塊由虛線框依序變成實心卡片。
 * p 0–1（各區塊錯開）。o = { title: 'Daily Focus', sub, value: 86, ringLabel, tiles: [{ v, l, col }], cta }
 */
function uiWireMorph(x, y, w, h, p, o = {}) {
  const pad = w * .07, col = o.col || STYLE.c.a1, ok = o.col2 || UIC.ok;
  const bp = clamp(p * 1.4);
  ctx.fillStyle = mixc('#f6f7f9', mixc('#ffffff', col, .05), bp); ctx.fillRect(x, y, w, h);
  if (bp < 1) { ctx.save(); ctx.globalAlpha *= 1 - bp; ctx.strokeStyle = 'rgba(100,116,139,.12)'; ctx.lineWidth = 1;
    for (let gx = x; gx < x + w; gx += w / 12) { ctx.beginPath(); ctx.moveTo(gx, y); ctx.lineTo(gx, y + h); ctx.stroke(); }
    for (let gy = y; gy < y + h; gy += w / 12) { ctx.beginPath(); ctx.moveTo(x, gy); ctx.lineTo(x + w, gy); ctx.stroke(); } ctx.restore(); }
  const tiles = o.tiles || [{ v: '4h 12m', l: 'Focus' }, { v: '12', l: 'Tasks' }, { v: '7d', l: 'Streak' }];
  const top = y + h * .12, blocks = [
    { x: x + pad, y: top, w: w - pad * 2, h: h * .1, kind: 'head' },
    { x: x + pad, y: top + h * .13, w: w - pad * 2, h: h * .36, kind: 'ring' },
    ...tiles.map((tl, i) => { const tw_ = (w - pad * 2 - pad * .5 * (tiles.length - 1)) / tiles.length; return { x: x + pad + i * (tw_ + pad * .5), y: top + h * .52, w: tw_, h: h * .15, kind: 'tile', tl }; }),
    { x: x + pad, y: top + h * .71, w: w - pad * 2, h: h * .085, kind: 'cta' },
  ];
  const N = blocks.length;
  blocks.forEach((b, i) => {
    const q = clamp((p - i * .07) / .55), e = E.out(q), pop = 1 + Math.sin(clamp(q * 1.3) * Math.PI) * .045, r = Math.min(b.h * .3, w * .06);
    ctx.save(); ctx.translate(b.x + b.w / 2, b.y + b.h / 2); ctx.scale(pop, pop); ctx.translate(-(b.x + b.w / 2), -(b.y + b.h / 2));
    if (e < 1) { ctx.save(); ctx.globalAlpha *= 1 - e; ctx.setLineDash([w * .02, w * .015]); ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = Math.max(1, w * .006); strokeRR(b.x, b.y, b.w, b.h, r);
      ctx.setLineDash([]); ctx.fillStyle = 'rgba(148,163,184,.25)';
      if (b.kind === 'ring') { ctx.lineWidth = Math.max(1, w * .006); ctx.strokeStyle = '#cbd5e1'; ctx.setLineDash([w * .02, w * .015]); ctx.beginPath(); ctx.arc(b.x + b.w / 2, b.y + b.h * .48, b.h * .32, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]); }
      else { fillRR(b.x + b.w * .08, b.y + b.h * .3, b.w * .5, b.h * .16, b.h * .08); fillRR(b.x + b.w * .08, b.y + b.h * .58, b.w * .32, b.h * .12, b.h * .06); }
      ctx.restore(); }
    if (e > 0) {
      ctx.save(); ctx.globalAlpha *= e;
      if (b.kind === 'head') {
        txtB(o.title || 'Daily Focus', b.x, b.y + b.h * .32, { size: b.h * .42, weight: 800, color: UIC.ink, maxW: b.w * .72, ui: true });
        txtB(o.sub || 'Tuesday · 3 sessions', b.x, b.y + b.h * .78, { size: b.h * .22, weight: 500, color: UIC.sub, maxW: b.w * .72, ui: true });
        circle(b.x + b.w - b.h * .4, b.y + b.h * .45, b.h * .36, mixc('#ffffff', col, .2)); uiGlyph('focus', b.x + b.w - b.h * .4, b.y + b.h * .45, b.h * .4, col);
      } else if (b.kind === 'ring') {
        uiCard(b.x, b.y, b.w, b.h, { r, lift: .35 });
        const v = Math.round((o.value ?? 86) * E.out(clamp((q - .2) / .8)));
        uiRing(b.x + b.w / 2, b.y + b.h * .5, b.h * .32, v / 100, { col: ok, w: .17, label: v + '%', sub: o.ringLabel || 'of daily goal', labelSize: .44 });
      } else if (b.kind === 'tile') {
        uiCard(b.x, b.y, b.w, b.h, { r, lift: .25 });
        circle(b.x + b.w * .12 + b.h * .07, b.y + b.h * .24, b.h * .07, b.tl.col || (i % 2 ? ok : col));
        txtB(b.tl.v, b.x + b.w * .12, b.y + b.h * .53, { size: Math.min(b.h * .22, b.w * .2), weight: 800, color: UIC.ink, maxW: b.w * .8, fit: { lines: 1, min: .55 }, ui: true });
        txtB(b.tl.l, b.x + b.w * .12, b.y + b.h * .78, { size: Math.min(b.h * .14, b.w * .13), weight: 600, color: UIC.sub, maxW: b.w * .8, fit: { lines: 1, min: .6 }, ui: true });
      } else {
        ctx.save(); ctx.shadowColor = rgba(col, .35); ctx.shadowBlur = b.h * .4; ctx.shadowOffsetY = b.h * .12; ctx.fillStyle = col; fillRR(b.x, b.y, b.w, b.h, b.h / 2); ctx.restore();
        txtB(o.cta || 'Start session', b.x + b.w / 2, b.y + b.h / 2, { size: b.h * .36, weight: 800, color: '#fff', align: 'center', maxW: b.w * .8, ui: true });
      }
      ctx.restore();
    }
    ctx.restore();
  });
  return N;
}

/* ---------- 行事曆拖放 ---------- */

/**
 * 行事曆週視圖：(x, y, w, h) 白卡內畫星期欄、時間列。o = { days: ['Mon', …], dates: [13, …], hours: [9, …], today（欄索引）,
 * events: [{ d, h0, h1, title, col }], target: { d, h0, h1, p }（拖放目標的虛線框，p 0–1 顯示程度）, card（false 不畫白卡）}。
 * 回傳 { slot(d, h0, h1) → { x, y, w, h } } 讓事件方塊對齊格子
 */
function uiCalendar(x, y, w, h, o = {}) {
  const G = uiCalGrid(x, y, w, h, o), { days, dates, hours, gut, head, gx, gw, gy, gh, cw, rh, slot } = G;
  if (o.card !== false) uiCard(x, y, w, h, { r: Math.min(w, h) * .05, lift: .5 });
  days.forEach((s, i) => {
    const cx = gx + (i + .5) * cw, td = i === o.today;
    txtB(s, cx, y + head * .3, { size: head * .2, weight: 600, color: td ? STYLE.c.a1 : UIC.sub, align: 'center', maxW: cw * .9, ui: true });
    if (td) circle(cx, y + head * .66, head * .22, STYLE.c.a1);
    txtB(String(dates[i] ?? ''), cx, y + head * .66, { size: head * .26, weight: 800, color: td ? '#fff' : UIC.ink, align: 'center', maxW: cw * .9, ui: true });
  });
  ctx.strokeStyle = 'rgba(15,23,42,.07)'; ctx.lineWidth = 1;
  hours.forEach((hr, j) => {
    const ly = gy + j * rh; ctx.beginPath(); ctx.moveTo(gx, ly); ctx.lineTo(gx + gw, ly); ctx.stroke();
    txtB((hr > 12 ? hr - 12 : hr) + (hr >= 12 ? ' PM' : ' AM'), gx - w * .015, ly + rh * .02, { size: Math.min(rh * .2, w * .022), weight: 600, color: UIC.sub, align: 'right', maxW: gut * .9, ui: true });
  });
  for (let i = 1; i < days.length; i++) { ctx.beginPath(); ctx.moveTo(gx + i * cw, gy); ctx.lineTo(gx + i * cw, gy + gh); ctx.stroke(); }
  (o.events || []).forEach(ev => { const s = slot(ev.d, ev.h0, ev.h1); uiEventBlock(s.x, s.y, s.w, s.h, ev); });
  if (o.target && o.target.p > 0) {
    const s = slot(o.target.d, o.target.h0, o.target.h1), tp = o.target.p, c = o.target.col || STYLE.c.a1;
    ctx.save(); ctx.globalAlpha *= tp; ctx.fillStyle = rgba(c, .08); fillRR(s.x, s.y, s.w, s.h, s.w * .1);
    ctx.setLineDash([s.w * .06, s.w * .045]); ctx.strokeStyle = rgba(c, .7); ctx.lineWidth = Math.max(1.5, s.w * .02); strokeRR(s.x, s.y, s.w, s.h, s.w * .1); ctx.restore();
  }
  return G;
}

/** 行事曆格線的幾何（不畫）：參數同 uiCalendar。先算好拖放起點、終點與游標位置時用。回傳 { slot(d, h0, h1), cw, rh, … } */
function uiCalGrid(x, y, w, h, o = {}) {
  const days = o.days || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'], dates = o.dates || [13, 14, 15, 16, 17], hours = o.hours || [9, 10, 11, 12, 13, 14];
  const gut = w * .11, head = h * .16, gx = x + gut, gw = w - gut - w * .03, gy = y + head, gh = h - head - h * .05, cw = gw / days.length, rh = gh / hours.length;
  const slot = (d, h0, h1) => ({ x: gx + d * cw + cw * .06, y: gy + (h0 - hours[0]) * rh + rh * .06, w: cw * .88, h: (h1 - h0) * rh - rh * .12 });
  return { days, dates, hours, gut, head, gx, gw, gy, gh, cw, rh, slot };
}

/** 事件方塊：(x, y, w, h)。o = { title, time, col, lift（0–1 拿起：放大、加深陰影、傾斜）, rot, done（右上角打勾 0–1）} */
function uiEventBlock(x, y, w, h, o = {}) {
  const col = o.col || STYLE.c.a1, lift = clamp(o.lift || 0), r = Math.min(w * .1, h * .2), sc = 1 + lift * .06;
  ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.rotate((o.rot || 0) + lift * -.03); ctx.scale(sc, sc); ctx.translate(-w / 2, -h / 2);
  ctx.save(); ctx.shadowColor = `rgba(15,23,42,${.06 + lift * .2})`; ctx.shadowBlur = w * (.04 + lift * .25); ctx.shadowOffsetY = w * (.01 + lift * .1);
  ctx.fillStyle = mixc('#ffffff', col, lift > 0 ? .2 : .14); fillRR(0, 0, w, h, r); ctx.restore();
  ctx.save(); ctx.beginPath(); rrect(0, 0, w, h, r); ctx.clip(); ctx.fillStyle = col; ctx.fillRect(0, 0, Math.max(3, w * .05), h); ctx.restore();
  const ink = mixc(col, '#0f172a', .45), fs = o.fs || Math.min(w * .1, h * .3);
  const mw = w * (o.done > 0 ? .62 : .8);
  if (o.title) txtB(o.title, w * .14, o.time ? h * .34 : h / 2, { size: fs, weight: 800, color: ink, maxW: mw, fit: { lines: 1, min: .6 }, ui: true });
  if (o.time) txtB(o.time, w * .14, h * .66, { size: fs * .78, weight: 600, color: rgba(ink, .7), maxW: mw, fit: { lines: 1, min: .6 }, ui: true });
  if (o.done > 0) uiCheck(w - fs * .9, fs * .9, fs * .55, o.done);
  ctx.restore();
}

/**
 * 拖放軌跡：t0 拿起、t1 放下（a → b，走微彎的弧線，放下時吸附過衝）。回傳 { x, y, lift（0–1）, rot, snap（放下後的衝擊 0–1）}
 */
function uiDragSnap(t, t0, t1, a, b, o = {}) {
  const pos = tt => { const e = E.io(prog(tt, t0, t1)), q = arcPt(a.x, a.y, b.x, b.y, e, o.arc ?? .12); return q; };
  const q = pos(t), s = t > t1 ? 1 - spring(t, t1, 3, .35) : 0, dx = b.x - a.x, dy = b.y - a.y, L = Math.hypot(dx, dy) || 1;
  const x = t > t1 ? b.x - dx / L * s * MIN * .02 : q.x, y = t > t1 ? b.y - dy / L * s * MIN * .02 : q.y;
  const vx = (pos(t + .02).x - pos(t - .02).x) / .04;
  const lift = clamp((t - (t0 - .18)) / .18) * (1 - clamp((t - t1 + .02) / .14));
  return { x, y, lift, rot: clamp(vx / (MIN * 8), -.08, .08), snap: t > t1 ? Math.exp(-(t - t1) * 6) : 0 };
}

/* ---------- Dock、App 圖示、視窗打開 ---------- */

/** App 圖示（圓角方塊＋漸層＋高光＋圖示）：(cx, cy) 中心、s 邊長。it = { col, col2, glyph（uiGlyph 名）} */
function uiAppIcon(cx, cy, s, it = {}) {
  const c1 = it.col || STYLE.c.a1, c2 = it.col2 || mixc(c1, '#0f172a', .25), r = s * .23, x = cx - s / 2, y = cy - s / 2;
  ctx.save(); ctx.shadowColor = 'rgba(15,23,42,.22)'; ctx.shadowBlur = s * .16; ctx.shadowOffsetY = s * .06;
  const g = ctx.createLinearGradient(0, y, 0, y + s); g.addColorStop(0, mixc(c1, '#ffffff', .15)); g.addColorStop(1, c2);
  ctx.fillStyle = g; fillRR(x, y, s, s, r); ctx.restore();
  ctx.save(); ctx.beginPath(); rrect(x, y, s, s, r); ctx.clip();
  const hg = ctx.createLinearGradient(0, y, 0, y + s * .55); hg.addColorStop(0, 'rgba(255,255,255,.35)'); hg.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = hg; ctx.fillRect(x, y, s, s * .55); ctx.restore();
  uiGlyph(it.glyph || 'doc', cx, cy, s * .5, it.ink || '#ffffff');
}

/**
 * Dock：底部中心 (cx, by)、s 圖示邊長。icons = [{ col, col2, glyph }]。
 * o = { mx（游標 x，靠近的圖示放大；null 不放大）, mag（最大放大量，預設 .55）, bounce: { i, at, n（跳幾下，預設 2）}, running: [索引] }
 * 回傳每個圖示的 { x, y, s }（圖示中心與目前邊長），用來接 uiOpenFrom
 */
function uiDock(cx, by, s, icons, t, o = {}) {
  const gap = s * .22, padX = s * .28, padY = s * .2, n = icons.length, mag = o.mag ?? .55;
  const baseW = n * s + (n - 1) * gap, bx0 = cx - baseW / 2;
  const sc = icons.map((_, i) => o.mx == null ? 1 : 1 + mag * Math.exp(-Math.pow((bx0 + i * (s + gap) + s / 2 - o.mx) / (s * 1.5), 2)));
  const tot = sc.reduce((a, v) => a + v * s, 0) + (n - 1) * gap, dw = tot + padX * 2, dh = s + padY * 2;
  uiGlass(cx - dw / 2, by - dh, dw, dh, dh * .32, { fill: 'rgba(255,255,255,.62)', sh: .16 });
  let xx = cx - tot / 2; const out = [];
  icons.forEach((it, i) => {
    const ss = s * sc[i], icx = xx + ss / 2; let jy = 0;
    if (o.bounce && o.bounce.i === i) {
      const u = t - o.bounce.at, nb = o.bounce.n || 2, per = .42;
      if (u > 0 && u < per * nb) { const k = Math.floor(u / per), f = (u - k * per) / per; jy = Math.sin(f * Math.PI) * s * .62 * Math.pow(.62, k); }
    }
    const icy = by - padY - ss / 2 - jy;
    uiAppIcon(icx, icy, ss, it);
    if ((o.running || []).includes(i)) circle(icx, by - padY * .38, s * .045, 'rgba(15,23,42,.55)');
    out.push({ x: icx, y: icy, s: ss }); xx += ss + gap;
  });
  return out;
}

/**
 * 視窗從圖示打開（Dock → open）：p 0–1（建議傳 spring），從圖示 (ix, iy) 放大移動到 (x, y, w, h)，寬先開、高稍慢（像 genie）。
 * draw(x, y, w, h) 以最終座標畫視窗內容（例如 frameWindow）
 */
function uiOpenFrom(ix, iy, x, y, w, h, p, draw) {
  if (p <= 0) return;
  const q = Math.max(0, p), sx = lerp(.05, 1, q), sy = lerp(.05, 1, Math.pow(clamp(q), 1.35) + Math.max(0, q - 1));
  const cx = lerp(ix, x + w / 2, E.out(clamp(q))), cy = lerp(iy, y + h / 2, clamp(q));
  ctx.save(); ctx.globalAlpha *= clamp(q * 4); ctx.translate(cx, cy); ctx.scale(sx, sy); ctx.translate(-(x + w / 2), -(y + h / 2));
  draw(x, y, w, h); ctx.restore();
}
