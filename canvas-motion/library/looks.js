/* ============================================================
 * 畫風零件 looks.js：10 種畫風，構圖不寫死。
 *   anime 動畫風背景　water 水彩　ink 水墨　flat 扁平插畫　pixel 像素
 *   neon 霓虹合成波　poly 低多邊形　paper 剪紙　comic 美漫網點　crayon 蠟筆
 * 兩種用法（說明見 references/looks.md）：
 *   1. 資料驅動：project.json 用 L_look，在 data 裡描述構圖（圖層、稜線、多邊形、太陽、粒子…）
 *   2. 自訂場景：withLook(s, t, pulse, (L, P) => { ... lookShape(L, P, path, '色名') ... })
 *      用這個畫法畫任何主體（人物、建築、物件），會自動套用該畫風的填色與質感
 * 每種畫風的預設色盤在 LOOKS[name].pal，可用 data.pal 局部覆寫。
 * ============================================================ */

/* ---------- 共用工具 ---------- */
function _lkPath(x, pts) { x.beginPath(); pts.forEach(([a, b], i) => i ? x.lineTo(a, b) : x.moveTo(a, b)); x.closePath(); }
const _lkBB = pts => pts.reduce((b, [a, c]) => [Math.min(b[0], a), Math.min(b[1], c), Math.max(b[2], a), Math.max(b[3], c)], [1e9, 1e9, -1e9, -1e9]);
/** 山稜線多邊形（像素座標）：base 基線 y、amp 起伏、seed 形狀 */
function lookRidge(w, h, base, amp, seed, n = 18) {
  const R = rng(seed), f = [R() * 3 + 1, R() * 5 + 3, R() * 9 + 6], ph = [R() * 6, R() * 6, R() * 6], pts = [];
  for (let i = 0; i <= n; i++) {
    const u = i / n, y = base - amp * (.55 * Math.sin(u * f[0] + ph[0]) + .3 * Math.sin(u * f[1] + ph[1]) + .15 * Math.sin(u * f[2] + ph[2]));
    pts.push([u * w, y]);
  }
  return [...pts, [w, h], [0, h]];
}
function _lkJitter(pts, R, amp, sub = 6) {   // 平滑隨機漫步擾動：不規則但不鋸齒
  const out = []; let v = 0, dv = 0;
  for (let i = 0; i < pts.length; i++) {
    const [x1, y1] = pts[i], [x2, y2] = pts[(i + 1) % pts.length];
    for (let k = 0; k < sub; k++) { dv = dv * .8 + (R() - .5) * .5; v = (v + dv) * .92; const u = k / sub, d = amp * clamp(v, -1.2, 1.2);
      out.push([lerp(x1, x2, u) + d * .4, lerp(y1, y2, u) + d]); }
  }
  return out;
}
const _BLK = 'rgb(0,0,0)', _WHT = 'rgb(255,255,255)';
function _lkWash(x, pts, col, seed, o = {}) {   // 水彩：模糊暈染 → 收邊 → 濕邊 → 顆粒
  const R = rng(seed), amp = o.amp || MIN * .02, passes = o.passes || 6, bb = _lkBB(pts), top = o.top || col;
  const fill = () => { const g = x.createLinearGradient(0, bb[1], 0, bb[1] + (bb[3] - bb[1]) * .5); g.addColorStop(0, top); g.addColorStop(1, col); return g; };
  x.save();
  for (let p = 0; p < passes; p++) {
    x.filter = p < passes - 2 ? `blur(${(amp * (.5 + p * .25)).toFixed(1)}px)` : 'none';
    _lkPath(x, _lkJitter(pts, R, amp * (1 + p * .2))); x.globalAlpha = o.alpha || .2; x.fillStyle = fill(); x.fill();
  }
  x.filter = 'none';
  const edge = _lkJitter(pts, R, amp * .7);
  for (let k = 0; k < 2; k++) { _lkPath(x, edge); x.globalAlpha = .06; x.lineWidth = amp * (.15 + k * .15); x.strokeStyle = mixc(col, _BLK, .3); x.stroke(); }
  _lkPath(x, pts); x.clip();
  for (let i = 0; i < (bb[2] - bb[0]) * (bb[3] - bb[1]) / 70; i++) {
    const r = R() * 1.6 + .3; x.globalAlpha = R() * .16; x.fillStyle = R() < .5 ? mixc(col, _BLK, .45) : mixc(col, _WHT, .4);
    x.fillRect(lerp(bb[0], bb[2], R()), lerp(bb[1], bb[3], R()), r, r);
  }
  x.restore();
}
function _lkHalftone(x, x0, y0, w, h, col, dens) {   // 網點：dens(u,v) 0–1 決定點的大小
  const g = Math.max(4, MIN * .012); x.fillStyle = col;
  for (let yy = 0; yy < h; yy += g) for (let xx = (yy / g % 2) * g / 2; xx < w; xx += g) {
    const r = g * .5 * clamp(dens(xx / w, yy / h)); if (r > .3) { x.beginPath(); x.arc(x0 + xx, y0 + yy, r, 0, 6.283); x.fill(); } }
}
function _lkCrayon(x, pts, col, seed, o = {}) {   // 蠟筆：同方向短筆觸填滿
  const R = rng(seed), bb = _lkBB(pts), ang = o.ang ?? -.6, len = MIN * (o.len || .03), dens = o.dens || 1;
  x.save(); _lkPath(x, pts); x.clip(); x.lineCap = 'round';
  const n = (bb[2] - bb[0]) * (bb[3] - bb[1]) / (MIN * MIN) * 2600 * dens;
  for (let i = 0; i < n; i++) {
    const a = lerp(bb[0], bb[2], R()), b = lerp(bb[1], bb[3], R()), an = ang + (R() - .5) * .35, l = len * (.5 + R());
    x.strokeStyle = rgba(mixc(col, R() < .5 ? _WHT : _BLK, R() * .18), .35 + R() * .4); x.lineWidth = MIN * (.002 + R() * .003);
    x.beginPath(); x.moveTo(a, b); x.lineTo(a + Math.cos(an) * l, b + Math.sin(an) * l); x.stroke();
  }
  x.restore();
}
function _lkPolyFill(x, pts, col, seed, P, cols = 16, vg) {   // 低多邊形：外框範圍切三角面，依面向上色後裁成形狀；vg=[上,下] 時底色改成垂直漸層
  const R = rng(seed), bb = _lkBB(pts), rows = 7, w = bb[2] - bb[0], h = bb[3] - bb[1], g = [];
  for (let j = 0; j <= rows; j++) { const row = []; for (let i = 0; i <= cols; i++)
    row.push([bb[0] + w * i / cols + (i % cols ? (R() - .5) * w / cols * .8 : 0), bb[1] + h * j / rows + (j % rows ? (R() - .5) * h / rows * .8 : 0)]); g.push(row); }
  x.save(); _lkPath(x, pts); x.clip();
  for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
    const a = g[j][i], b = g[j][i + 1], c = g[j + 1][i], d = g[j + 1][i + 1];
    [[a, b, c], [b, d, c]].forEach(tr => {
      const nx = (tr[1][1] - tr[0][1]) * (tr[2][0] - tr[0][0]) - (tr[1][0] - tr[0][0]) * (tr[2][1] - tr[0][1]);
      const l = clamp(.5 + nx / (w * h / cols / rows) * 1.2 + (R() - .5) * .25 - j / rows * .25);
      x.beginPath(); x.moveTo(...tr[0]); x.lineTo(...tr[1]); x.lineTo(...tr[2]); x.closePath();
      const base = vg ? mixc(vg[0], vg[1], (tr[0][1] - bb[1]) / (h || 1)) : col;
      x.fillStyle = vg ? mixc(base, P.sun || _WHT, l * .18) : mixc(mixc(base, P.shade || _BLK, .45), mixc(base, P.sun || _WHT, .3), l); x.fill(); x.strokeStyle = x.fillStyle; x.lineWidth = .8; x.stroke();
    });
  }
  x.restore();
}
function _lkPaper(key, P, alpha = .55, dots = 14) {   // 紙紋（乘法疊在最上層）
  const im = cached(key, W / 2, H / 2, (x, w, h) => {
    x.fillStyle = P.paper; x.fillRect(0, 0, w, h); const R = rng(8);
    for (let i = 0; i < w * h / dots; i++) { x.fillStyle = rgba(P.ink || _BLK, R() * .06); x.fillRect(R() * w, R() * h, 1 + R(), 1 + R()); }
  }, [P.paper, P.ink, dots]);
  ctx.save(); ctx.setTransform(ctx.getTransform()); ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = alpha; ctx.drawImage(im, 0, 0, W, H); ctx.restore();
}
function _lkCelCloud(x, w, h, seed, P, o = {}) {   // 平塗分色雲（光源在右下）
  const R = rng(seed), cs = [];
  for (let i = 0; i < 9; i++) cs.push([w * (.18 + i * .08 + (R() - .5) * .05), h * (.62 - Math.sin(i / 8 * Math.PI) * .32 + (R() - .5) * .1), h * (.2 + R() * .16)]);
  const blob = (dx, dy) => { x.beginPath(); cs.forEach(([a, b, r]) => { x.moveTo(a + dx + r, b + dy); x.arc(a + dx, b + dy, r, 0, Math.PI * 2); }); };
  // 描邊版：先把所有圓用粗線描一次，再整朵填色蓋上 → 只剩最外圈輪廓（不會變成一串圈圈）
  if (o.outline) { x.save(); blob(0, 0); x.lineWidth = MIN * .01; x.strokeStyle = o.outline; x.stroke(); x.restore(); }
  x.save(); blob(0, 0); x.clip();
  x.fillStyle = P.cloudLit; x.fillRect(0, 0, w, h);
  x.fillStyle = P.cloudShade; blob(-h * .07, -h * .1); x.fill();
  x.globalAlpha = .5; x.fillStyle = mixc(P.cloudShade, P.sky1, .5); blob(-h * .16, -h * .2); x.fill();
  x.restore();
}
function _lkRays(P, x0, y0, t, hz, col, n = 14, a = .045, pulse = 0) {
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, hz); ctx.clip();
  ctx.globalCompositeOperation = 'lighter'; ctx.translate(x0, y0); ctx.rotate(t * .03);
  for (let i = 0; i < n; i++) {
    ctx.rotate(Math.PI * 2 / n); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(MIN * 1.3, -MIN * .035); ctx.lineTo(MIN * 1.3, MIN * .035); ctx.closePath();
    ctx.fillStyle = rgba(col, a + (i % 3 === 0 ? .03 : 0) + pulse * .015); ctx.fill();
  }
  ctx.restore();
}
function _lkBands(x, w, hz, cols, dither = 0) {   // 色帶天空；dither>0 時用棋盤格抖色過渡（像素）
  const n = cols.length;
  if (!dither) { cols.forEach((c, i) => { x.fillStyle = c; x.fillRect(0, hz * i / n - 1, w, hz / n + 2); }); return; }
  for (let yy = 0; yy < hz; yy += dither) {
    const f = yy / hz * (n - 1), i = Math.floor(f), fr = f - i;
    for (let xx = 0; xx < w; xx += dither) { x.fillStyle = cols[Math.min(n - 1, i + (((xx + yy) / dither) % 2 === 0 && fr > .5 ? 1 : 0))]; x.fillRect(xx, yy, dither, dither); }
  }
}
const _grad4 = (x, w, h, hz, cs) => { const g = x.createLinearGradient(0, 0, 0, hz); cs.forEach((c, i) => g.addColorStop(i / (cs.length - 1), c)); x.fillStyle = g; x.fillRect(0, 0, w, h); };

/* ---------- 10 種畫風 ----------
 * 每種畫風的介面：
 *   pal                      預設色盤
 *   sky(x, w, h, P, hz)      烘焙：整張天空（含地平線以下的底色）
 *   sun(P, x, y, r, t, pulse, hz)  每格：太陽／月亮
 *   cloud(x, w, h, seed, P)  烘焙：一朵雲（沒有就不畫雲）
 *   fill(x, pts, col, seed, o, P)  烘焙：一個圖層形狀；o = { depth 0–1（遠→近）, solid, edge（上緣折線） }
 *   shape(P, col, o)         每格：自訂場景畫主體時，路徑已建立，負責填色與描邊
 *   between(P, t, hz)        選用：最後一層（前景）之前畫的東西（例如水墨的雲霧帶）
 *   overlay(P, t, pulse)     選用：最上層質感（紙紋、掃描線、分格框）
 *   pixel / sway             選用：像素化倍率、圖層像紙偶一樣晃動 */
const LOOKS = {
  anime: {
    name: '動畫風背景',
    pal: { sky1: '#3b3f8f', sky2: '#b25a8e', sky3: '#f08a4b', sky4: '#ffd27a', sun: '#fff1c4', cloudLit: '#ffc58a', cloudShade: '#8a5c9e',
      hill1: '#9b7fb8', hill2: '#6d6aa8', hill3: '#4f5f8f', ground: '#3f5a6e', petal: '#ffd9e0', label: '#fff8ec', ink: '#2d2438' },
    sky(x, w, h, P, hz) { _grad4(x, w, h, hz, [P.sky1, P.sky2, P.sky3, P.sky4]); },
    sun(P, x, y, r, t, pulse, hz) { glow(x, y, r * 8, P.sky4, .9); _lkRays(P, x, y, t, hz, P.sun, 14, .045, pulse); circle(x, y, r, P.sun); glow(x, y, r * 2.3, P.sun, .8); },
    cloud(x, w, h, seed, P) { _lkCelCloud(x, w, h, seed, P); },
    fill(x, pts, col, seed, o, P) {
      _lkPath(x, pts); x.fillStyle = col; x.fill();
      const bb = _lkBB(pts); x.save(); _lkPath(x, pts); x.clip(); x.fillStyle = mixc(col, P.sky1, .35); x.fillRect(bb[0], lerp(bb[1], bb[3], .45), bb[2] - bb[0], bb[3]); x.restore();
      if (o.edge) { x.beginPath(); o.edge.forEach(([a, b], i) => i ? x.lineTo(a, b) : x.moveTo(a, b)); x.strokeStyle = rgba(P.sky4, .55); x.lineWidth = MIN * .004; x.stroke(); }
    },
    shape(P, col, o) { ctx.fillStyle = col; ctx.fill(); if (o.rim !== false) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = rgba(P.sun, .35); ctx.lineWidth = o.lw || 1; ctx.stroke(); ctx.restore(); } },
  },
  water: {
    name: '水彩',
    pal: { paper: '#f5efe3', sky1: '#8fa7d6', sky2: '#e3a0b5', sky3: '#f4b77a', sky4: '#fbe3a1', sun: '#f7c35c', hill1: '#a99ccf', hill2: '#7f8fc4', hill3: '#5f7aa8',
      ground: '#6c8f7a', petal: '#f5b9c6', ink: '#3a2f28', label: '#3a2f28', cloudLit: '#fff6ea' },
    sky(x, w, h, P, hz) {
      x.fillStyle = P.paper; x.fillRect(0, 0, w, h);
      [[P.sky1, 0, .35], [P.sky2, .2, .6], [P.sky3, .45, .85], [P.sky4, .7, 1.05]].forEach(([c, a, b], i) =>
        _lkWash(x, [[-w * .05, hz * a], [w * 1.05, hz * (a + .05)], [w * 1.05, hz * b], [-w * .05, hz * b * .98]], c, 30 + i, { amp: MIN * .05, alpha: .18 }));
    },
    sun(P, x, y, r) {
      const im = cached('lk-water-sun' + Math.round(r), r * 6, r * 6, (c, w, h) => _lkWash(c, Array.from({ length: 14 }, (_, i) => [w / 2 + Math.cos(i / 14 * 6.283) * r * 1.4, h / 2 + Math.sin(i / 14 * 6.283) * r * 1.4]), P.sun, 3, { amp: r * .3, alpha: .3 }), [P.sun]);
      ctx.drawImage(im, x - r * 3, y - r * 3, r * 6, r * 6);
    },
    cloud(x, w, h, seed, P) { _lkWash(x, Array.from({ length: 12 }, (_, i) => [w / 2 + Math.cos(i / 12 * 6.283) * w * .38, h / 2 + Math.sin(i / 12 * 6.283) * h * .28]), P.cloudLit, seed, { amp: h * .12, alpha: .22 }); },
    fill(x, pts, col, seed, o, P) { _lkWash(x, pts, col, seed * 7, { amp: MIN * .022, passes: o.solid ? 7 : 6, alpha: o.solid ? .24 : .2, top: mixc(col, P.sky4, (1 - (o.depth ?? .5)) * .45) }); },
    shape(P, col) { ctx.save(); ctx.globalAlpha *= .88; ctx.fillStyle = col; ctx.fill(); ctx.restore(); },
    overlay(P) { _lkPaper('lk-water-paper', P, .6); },
  },
  ink: {
    name: '水墨',
    pal: { paper: '#efe6d2', ink: '#1d1b19', seal: '#c23b2e', sun: '#c23b2e', hill1: 'rgba(29,27,25,.22)', hill2: 'rgba(29,27,25,.45)', hill3: 'rgba(29,27,25,.75)',
      ground: 'rgba(29,27,25,.85)', petal: 'rgba(29,27,25,.5)', label: '#1d1b19' },
    sky(x, w, h, P) { x.fillStyle = P.paper; x.fillRect(0, 0, w, h); },
    sun(P, x, y, r) { circle(x, y, r * 1.1, rgba(P.sun, .85)); },
    fill(x, pts, col, seed, o, P) {
      const bb = _lkBB(pts), R = rng(seed);
      x.save(); _lkPath(x, pts); x.clip();
      if (o.solid) {   // 前景：一筆濃墨，帶飛白
        x.fillStyle = col; x.fillRect(bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]);
        x.globalCompositeOperation = 'destination-out';
        for (let i = 0; i < 260; i++) { x.globalAlpha = R() * .5; x.fillRect(lerp(bb[0], bb[2], R()), bb[1] + R() * (bb[3] - bb[1]) * .25, R() * (bb[2] - bb[0]) * .08, R() * 1.5 + .5); }
      } else {         // 遠山：山頂墨濃、山腳淡入霧中，加皴法細點
        const hh = bb[3] - bb[1], g = x.createLinearGradient(0, bb[1], 0, bb[1] + Math.min(hh, MIN * .45));
        g.addColorStop(0, col); g.addColorStop(.5, rgba(col, .45 * (rgb(col)[3] ?? 1))); g.addColorStop(1, rgba(P.ink, 0));
        x.filter = `blur(${MIN * .004}px)`; x.fillStyle = g; x.fillRect(bb[0], bb[1], bb[2] - bb[0], hh); x.filter = 'none';
        for (let j = 0; j < 120; j++) { x.globalAlpha = R() * .25; x.fillStyle = P.ink; x.fillRect(lerp(bb[0], bb[2], R()), bb[1] + R() * Math.min(hh, MIN * .3), R() * 3 + 1, R() * 8 + 2); }
      }
      x.restore();
    },
    shape(P, col) { ctx.fillStyle = col; ctx.fill(); },
    between(P, t, hz) {   // 雲霧帶：在前景之前慢慢橫移
      for (let i = 0; i < 3; i++) { const y = hz + MIN * (.02 + i * .07), x = ((t * MIN * .02 * (i + 1) + i * W * .3) % (W * 1.4)) - W * .2;
        const g = ctx.createLinearGradient(x, 0, x + W * .6, 0); g.addColorStop(0, rgba(P.paper, 0)); g.addColorStop(.5, rgba(P.paper, .85)); g.addColorStop(1, rgba(P.paper, 0));
        ctx.fillStyle = g; ctx.fillRect(x, y - MIN * .02, W * .6, MIN * .04); }
    },
    overlay(P) { _lkPaper('lk-ink-paper', P, .45, 10); },
  },
  flat: {
    name: '扁平插畫',
    pal: { sky1: '#2f3b73', sky2: '#5a4f8f', sky3: '#e0735a', sky4: '#f6b26b', sun: '#ffe3a3', hill1: '#7b6aa6', hill2: '#4f4f86', hill3: '#353d68',
      ground: '#26304f', shadow: '#10142a', cloudLit: '#ffe3a3', petal: '#ffd1a6', label: '#fff4e0', ink: '#1f1a2e' },
    sky(x, w, h, P, hz) { x.fillStyle = P.sky4; x.fillRect(0, 0, w, h); _lkBands(x, w, hz, [P.sky1, P.sky2, P.sky3, P.sky4]); },
    sun(P, x, y, r, t, pulse) { [3.3, 2.3, 1.5].forEach((k, i) => circle(x, y, r * k * (1 + pulse * .03 * (3 - i)), rgba(P.sun, .18 + i * .25))); circle(x, y, r, P.sun); },
    cloud(x, w, h, seed, P) { fillRRon(x, w * .05, h * .45, w * .9, h * .4, h * .2, rgba(P.cloudLit, .9)); fillRRon(x, w * .28, h * .15, w * .45, h * .4, h * .2, rgba(P.cloudLit, .9)); },
    fill(x, pts, col) { _lkPath(x, pts); x.fillStyle = col; x.fill(); },
    shape(P, col) { ctx.fillStyle = col; ctx.fill(); },
  },
  pixel: {
    name: '像素',
    pixel: 6,
    pal: { sky1: '#1b1f4b', sky2: '#4b3a78', sky3: '#b5577e', sky4: '#f19a5a', sun: '#ffe08a', hill1: '#6a4f8c', hill2: '#3f3a6e', hill3: '#2b2c52',
      ground: '#1b2238', label: '#ffe08a', petal: '#ffe08a', ink: '#221a2e' },
    sky(x, w, h, P, hz) {
      x.fillStyle = P.sky4; x.fillRect(0, 0, w, h); _lkBands(x, w, hz, [P.sky1, P.sky2, P.sky3, P.sky4], 6);
      const R = rng(2); x.fillStyle = P.sun; for (let i = 0; i < 30; i++) x.fillRect(Math.floor(R() * w / 6) * 6, Math.floor(R() * hz * .5 / 6) * 6, 6, 6);
    },
    sun(P, x, y, r, t) {
      ctx.fillStyle = P.sun; const c = 6, n = Math.round(r / c);
      for (let k = -n; k <= n; k++) { const hw = Math.round(Math.sqrt(n * n - k * k)); if (k < 0 || (k + Math.floor(t * 6)) % 3 !== 0) ctx.fillRect(x - hw * c, y + k * c, hw * 2 * c, c); }
    },
    fill(x, pts, col) { _lkPath(x, pts); x.fillStyle = col; x.fill(); },
    shape(P, col) { ctx.fillStyle = col; ctx.fill(); },
  },
  neon: {
    name: '霓虹合成波',
    pal: { sky1: '#0b0620', sky2: '#1c0b3a', sun: '#ffd36e', sun2: '#ff3d8b', line: '#35e0ff', line2: '#ff4fd8', hill1: '#1c0b3a', hill2: '#150830', hill3: '#100626',
      ground: '#070312', label: '#35e0ff', petal: '#ff4fd8', ink: '#0b0620' },
    sky(x, w, h, P, hz) { const g = x.createLinearGradient(0, 0, 0, hz); g.addColorStop(0, P.sky1); g.addColorStop(1, P.sky2); x.fillStyle = g; x.fillRect(0, 0, w, h); },
    sun(P, x, y, r, t, pulse) {
      const R2 = r * 2.8; ctx.save(); ctx.beginPath(); ctx.arc(x, y, R2, 0, Math.PI * 2); ctx.clip();
      const g = ctx.createLinearGradient(0, y - R2, 0, y + R2); g.addColorStop(0, P.sun); g.addColorStop(1, P.sun2); ctx.fillStyle = g; ctx.fillRect(x - R2, y - R2, R2 * 2, R2 * 2);
      ctx.fillStyle = P.sky2; for (let i = 0; i < 7; i++) ctx.fillRect(x - R2, y + R2 * (.05 + i * .14) + (t * MIN * .02 % (R2 * .14)), R2 * 2, R2 * .02 * (i + 1));
      ctx.restore(); glow(x, y, R2 * 2, P.sun2, .6 + pulse * .3);
    },
    fill(x, pts, col, seed, o, P) {
      _lkPath(x, pts); x.fillStyle = col; x.fill();
      const e = o.edge || pts; x.save(); x.shadowBlur = MIN * .02; x.shadowColor = P.line2; x.strokeStyle = P.line2; x.lineWidth = MIN * .003;
      x.beginPath(); e.forEach(([a, b], i) => i ? x.lineTo(a, b) : x.moveTo(a, b)); x.stroke(); x.restore();
    },
    shape(P, col, o) { ctx.save(); ctx.fillStyle = P.ink; ctx.fill(); ctx.shadowBlur = MIN * .02; ctx.shadowColor = P.line; ctx.strokeStyle = P.line; ctx.lineWidth = o.lw || 1; ctx.stroke(); ctx.restore(); },
    overlay() { ctx.fillStyle = 'rgba(0,0,0,.18)'; for (let y = 0; y < H; y += 3) ctx.fillRect(0, y, W, 1); },
  },
  poly: {
    name: '低多邊形',
    pal: { sky1: '#34427a', sky2: '#8a5a9c', sky3: '#f39a62', sun: '#ffe6a0', hill1: '#8f7bb5', hill2: '#62679f', hill3: '#465683', ground: '#3c5a62',
      shade: '#1c2140', label: '#fff4e2', petal: '#ffe6a0', ink: '#1c2140' },
    sky(x, w, h, P, hz) { x.fillStyle = P.sky3; x.fillRect(0, 0, w, h); _lkPolyFill(x, [[0, 0], [w, 0], [w, hz * 1.05], [0, hz * 1.05]], P.sky2, 3, P, 10, [P.sky1, P.sky3]); },
    sun(P, x, y, r, t) { ctx.beginPath(); for (let i = 0; i < 8; i++) { const a = i / 8 * 6.283 + t * .1; ctx.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); } ctx.closePath(); ctx.fillStyle = P.sun; ctx.fill(); glow(x, y, r * 4, P.sun, .6); },
    fill(x, pts, col, seed, o, P) { _lkPolyFill(x, pts, col, seed, P, o.solid ? 22 : 16); },
    shape(P, col) { ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = rgba(P.shade, .4); ctx.lineWidth = .8; ctx.stroke(); },
  },
  paper: {
    name: '剪紙',
    sway: true,
    pal: { sky1: '#f7d9b0', sun: '#e9573f', cloudLit: '#fffaf0', hill1: '#e9b384', hill2: '#d78a5f', hill3: '#b8674a', ground: '#8d4b3d', shadow: '#3a1f18',
      paper: '#fff6e6', label: '#fff6e6', petal: '#fffaf0', ink: '#3a1f18' },
    sky(x, w, h, P) { x.fillStyle = P.sky1; x.fillRect(0, 0, w, h); },
    sun(P, x, y, r, t) { ctx.save(); ctx.shadowColor = rgba(P.shadow, .3); ctx.shadowBlur = MIN * .02; circle(x, y + Math.sin(t * 1.3) * MIN * .006, r * 1.3, P.sun); ctx.restore(); },
    cloud(x, w, h, seed, P) { x.save(); x.shadowColor = rgba(P.shadow, .3); x.shadowBlur = MIN * .015; x.shadowOffsetY = MIN * .006; x.fillStyle = P.cloudLit; x.beginPath();
      [[.3, .6, .22], [.5, .45, .3], [.7, .6, .22]].forEach(([a, b, r]) => { x.moveTo(w * a + h * r, h * b); x.arc(w * a, h * b, h * r, 0, 6.283); }); x.fill(); x.restore(); },
    hang: true,
    fill(x, pts, col, seed, o, P) {
      x.save(); x.shadowColor = rgba(P.shadow, .35); x.shadowBlur = MIN * .02; x.shadowOffsetY = -MIN * .006; _lkPath(x, pts); x.fillStyle = col; x.fill(); x.restore();
      const bb = _lkBB(pts), R = rng(seed); x.save(); _lkPath(x, pts); x.clip();
      for (let i = 0; i < 900; i++) { x.strokeStyle = rgba(R() < .5 ? P.shadow : P.paper, R() * .08); x.lineWidth = .6;
        const a = lerp(bb[0], bb[2], R()), b = lerp(bb[1], bb[3], R()), l = R() * 10 + 3, an = R() * 6.28; x.beginPath(); x.moveTo(a, b); x.lineTo(a + Math.cos(an) * l, b + Math.sin(an) * l); x.stroke(); }
      x.restore();
    },
    shape(P, col) { ctx.save(); ctx.shadowColor = rgba(P.shadow, .45); ctx.shadowBlur = MIN * .012; ctx.shadowOffsetX = MIN * .006; ctx.shadowOffsetY = MIN * .004; ctx.fillStyle = col; ctx.fill(); ctx.restore(); },
  },
  comic: {
    name: '美漫網點',
    pal: { sky1: '#ffd84a', sky2: '#f08c2e', sun: '#fff6c9', ink: '#111111', hill1: '#f2a23a', hill2: '#e0742e', hill3: '#c24f2a', ground: '#8f2f26',
      cloudLit: '#ffffff', cloudShade: '#f2c14a', label: '#ffffff', petal: '#ffffff', sfx: '#ffffff' },
    sky(x, w, h, P, hz) { x.fillStyle = P.sky1; x.fillRect(0, 0, w, h); _lkHalftone(x, 0, 0, w, hz, P.sky2, (u, v) => v * 1.1); },
    sun(P, x, y, r, t, pulse, hz) {
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, hz); ctx.clip(); ctx.strokeStyle = P.ink; const R = rng(Math.floor(t * 8));
      for (let i = 0; i < 40; i++) { const a = R() * 6.283, r0 = r * (1.7 + R()); ctx.lineWidth = R() * MIN * .004 + 1; ctx.globalAlpha = .5;
        ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r0, y + Math.sin(a) * r0); ctx.lineTo(x + Math.cos(a) * MIN * 2, y + Math.sin(a) * MIN * 2); ctx.stroke(); }
      ctx.restore(); circle(x, y, r * 1.3, P.sun); ring(x, y, r * 1.3, P.ink, MIN * .006);
    },
    cloud(x, w, h, seed, P) { _lkCelCloud(x, w, h, seed, P, { outline: P.ink }); },
    fill(x, pts, col, seed, o, P) {
      const bb = _lkBB(pts); _lkPath(x, pts); x.fillStyle = col; x.fill();
      x.save(); _lkPath(x, pts); x.clip(); _lkHalftone(x, bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1], P.ink, (u, v) => o.solid ? .35 + v * .3 : v * .7); x.restore();
      _lkPath(x, pts); x.lineWidth = MIN * .006; x.strokeStyle = P.ink; x.stroke();
    },
    shape(P, col, o) { ctx.fillStyle = col; ctx.fill(); ctx.lineWidth = o.lw || 1.3; ctx.strokeStyle = P.ink; ctx.stroke(); },
    overlay(P) { ctx.save(); ctx.strokeStyle = P.ink; ctx.lineWidth = MIN * .012; ctx.strokeRect(MIN * .02, MIN * .02, W - MIN * .04, H - MIN * .04); ctx.restore(); },
  },
  crayon: {
    name: '蠟筆',
    pal: { paper: '#f7f1e3', sky1: '#7fa3e0', sky2: '#b9a2e6', sky3: '#f5a3a0', sky4: '#ffd48a', sun: '#ff9a3c', hill1: '#9ec07a', hill2: '#6fa36b', hill3: '#4f8a5f',
      ground: '#3f6f4f', ink: '#2a2a2a', label: '#fff7e8', petal: '#e2453a', cloudLit: '#ffffff' },
    sky(x, w, h, P, hz) { x.fillStyle = P.paper; x.fillRect(0, 0, w, h);
      [P.sky1, P.sky2, P.sky3, P.sky4].forEach((c, i) => _lkCrayon(x, [[0, hz * i / 4 - MIN * .03], [w, hz * i / 4 - MIN * .03], [w, hz * (i + 1) / 4 + MIN * .03], [0, hz * (i + 1) / 4 + MIN * .03]], c, 40 + i, { ang: -.3 })); },
    sun(P, x, y, r, t) { ctx.save(); ctx.strokeStyle = P.sun; ctx.lineCap = 'round'; const R = rng(3);
      for (let i = 0; i < 26; i++) { const rr = r * (.3 + i * .032), wob = Math.sin(t * 3 + i) * MIN * .002; ctx.lineWidth = MIN * .004; ctx.globalAlpha = .7;
        ctx.beginPath(); ctx.ellipse(x + (R() - .5) * 3, y + (R() - .5) * 3, rr + wob, rr * .95, R(), 0, 6.283); ctx.stroke(); } ctx.restore(); },
    cloud(x, w, h, seed, P) { _lkCrayon(x, Array.from({ length: 12 }, (_, i) => [w / 2 + Math.cos(i / 12 * 6.283) * w * .4, h / 2 + Math.sin(i / 12 * 6.283) * h * .3]), P.cloudLit, seed, { ang: -.2, dens: 1.4 }); },
    fill(x, pts, col, seed, o) { _lkCrayon(x, pts, col, seed, o.solid ? { ang: -.2, dens: 1.1 } : {}); },
    shape(P, col, o) { ctx.fillStyle = col; ctx.fill(); ctx.lineWidth = o.lw || .9; ctx.strokeStyle = rgba(P.ink, .55); ctx.stroke(); },
    jitter: true,
    overlay(P) { _lkPaper('lk-crayon-paper', P, .5, 8); },
  },
};
/** 在指定 context 上畫圓角矩形（烘焙用） */
function fillRRon(x, a, b, w, h, r, col) { x.beginPath(); x.roundRect(a, b, w, h, r); x.fillStyle = col; x.fill(); }

/** 取得本幕的畫風與色盤：data.look 名稱 + data.pal 覆寫 */
function lookOf(s) {
  const d = (s && s.data) || {}, name = d.look || 'flat', L = LOOKS[name] || LOOKS.flat;
  return { L, P: { ...L.pal, ...(d.pal || {}) }, name: LOOKS[name] ? name : 'flat' };
}
/** 色名轉顏色：'hill2' → 色盤裡的顏色；本身是顏色就直接用 */
const lookCol = (P, c) => (c && P[c]) || (c && /^(#|rgb|hsl)/.test(c) ? c : (P.hill2 || P.ground || P.ink));   // 色盤沒有這個色名時退回主色

/**
 * 自訂場景用：用畫風畫任何主體。先建立路徑（ctx.beginPath() … ），再呼叫 lookShape 填色。
 * o = { lw 描邊粗細, rim 是否描逆光邊 }
 */
function lookShape(L, P, path, col, o = {}) { ctx.save(); path(); L.shape(P, lookCol(P, col), o); ctx.restore(); }

/* ---------- 常用形狀 ----------
 * 自訂場景畫主體時不用從零寫路徑。每個形狀回傳「部件」陣列，交給 lookDraw 畫，就會套用畫風：
 *   lookDraw(L, P, LK_SHAPES.house(W * .3, H * .8, MIN * .3));
 * 座標：x = 水平中心、y = 底部（站在地上的位置）；尺寸以像素為單位。
 * colors 可以覆寫各部件顏色（色名或顏色），例如 { body: 'hill1', roof: 'sun' }。
 * 這些是簡化的形狀，不是角色骨架；動作（擺動、移動）自己用 t 算，改 x、y 或外層 ctx.rotate。 */
const _R = (x, y, w, h) => () => { ctx.beginPath(); ctx.rect(x, y, w, h); };
const _RR = (x, y, w, h, r) => () => { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); };
const _C = (x, y, r) => () => { ctx.beginPath(); ctx.arc(x, y, Math.max(0, r), 0, Math.PI * 2); };
const _PL = pts => () => { ctx.beginPath(); pts.forEach(([a, b], i) => i ? ctx.lineTo(a, b) : ctx.moveTo(a, b)); ctx.closePath(); };
const _LN = (pts) => () => { ctx.beginPath(); pts.forEach(([a, b], i) => i ? ctx.lineTo(a, b) : ctx.moveTo(a, b)); };
const LK_SHAPES = {
  /** 房屋：牆、屋頂、門、窗。w = 寬 */
  house(x, y, w, colors = {}) {
    const c = { body: 'hill1', roof: 'hill3', door: 'ground', win: 'sun', ...colors }, h = w * .7;
    return [{ path: _R(x - w / 2, y - h, w, h), fill: c.body }, { path: _PL([[x - w * .6, y - h], [x, y - h - w * .45], [x + w * .6, y - h]]), fill: c.roof },
      { path: _R(x - w * .1, y - h * .5, w * .2, h * .5), fill: c.door }, { path: _R(x - w * .38, y - h * .75, w * .18, w * .16), fill: c.win },
      { path: _R(x + w * .2, y - h * .75, w * .18, w * .16), fill: c.win }];
  },
  /** 室內一角：後牆、地板、窗（窗內可再畫天空）。以 (x, y) 為地板前緣中心，w×h 為整個房間 */
  room(x, y, w, h, colors = {}) {
    const c = { wall: 'hill1', floor: 'ground', win: 'sun', frame: 'ink', ...colors }, fy = y - h * .28;
    return [{ path: _R(x - w / 2, y - h, w, h * .72), fill: c.wall }, { path: _PL([[x - w / 2, fy], [x + w / 2, fy], [x + w / 2, y], [x - w / 2, y]]), fill: c.floor },
      { path: _R(x + w * .12, y - h * .88, w * .26, h * .34), fill: c.win }, { path: _LN([[x + w * .25, y - h * .88], [x + w * .25, y - h * .54]]), stroke: c.frame, lw: Math.max(1, w * .004) }];
  },
  /** 一張紙：本體＋字跡線。r 旋轉 */
  paper(x, y, w, h, r = 0, colors = {}) {
    const c = { sheet: 'label', line: 'ink', ...colors }, cy = y - h / 2, lines = [];
    const rot = ([a, b]) => [x + (a - x) * Math.cos(r) - (b - cy) * Math.sin(r), cy + (a - x) * Math.sin(r) + (b - cy) * Math.cos(r)];
    const box = [[x - w / 2, y - h], [x + w / 2, y - h], [x + w / 2, y], [x - w / 2, y]].map(rot);
    for (let k = 0; k < 5; k++) { const yy = y - h + h * (k + 1.3) / 6.6; lines.push({ path: _LN([rot([x - w * .36, yy]), rot([x + w * (k % 2 ? .1 : .3), yy])]), stroke: c.line, lw: Math.max(1, h * .012), alpha: .35 }); }
    return [{ path: _PL(box), fill: c.sheet }, ...lines];
  },
  /** 螢幕（桌上型）：外框、畫面、支架。w = 寬 */
  screen(x, y, w, colors = {}) {
    const c = { frame: 'ink', glass: 'sky2', stand: 'ink', ...colors }, h = w * .62;
    return [{ path: _R(x - w * .06, y - w * .12, w * .12, w * .12), fill: c.stand }, { path: _RR(x - w / 2, y - w * .12 - h, w, h, w * .03), fill: c.frame },
      { path: _RR(x - w * .45, y - w * .12 - h * .92, w * .9, h * .82, w * .015), fill: c.glass }];
  },
  /** 手機：機身、螢幕。h = 高 */
  phone(x, y, h, colors = {}) {
    const c = { body: 'ink', glass: 'sky2', ...colors }, w = h * .5;
    return [{ path: _RR(x - w / 2, y - h, w, h, w * .16), fill: c.body }, { path: _RR(x - w * .42, y - h * .95, w * .84, h * .9, w * .1), fill: c.glass }];
  },
  /** 簡化人形剪影（站或坐），h = 身高。不是角色骨架：只是一個可以擺在構圖裡的人 */
  person(x, y, h, pose = 'stand', colors = {}) {
    const c = { body: 'hill3', head: 'hill3', ...colors }, u = h / 100;
    const hy = pose === 'sit' ? y - 72 * u : y - 88 * u;
    const body = pose === 'sit'
      ? [[x - 13 * u, hy + 12 * u], [x + 13 * u, hy + 12 * u], [x + 15 * u, y - 30 * u], [x + 34 * u, y - 28 * u], [x + 34 * u, y - 18 * u], [x - 15 * u, y - 18 * u]]
      : [[x - 12 * u, hy + 12 * u], [x + 12 * u, hy + 12 * u], [x + 16 * u, y - 40 * u], [x + 8 * u, y], [x - 8 * u, y], [x - 16 * u, y - 40 * u]];
    return [{ path: _PL(body), fill: c.body }, { path: _C(x, hy, 11 * u), fill: c.head }];
  },
  /** 樹：樹幹＋三團樹冠。h = 高 */
  tree(x, y, h, colors = {}) {
    const c = { trunk: 'ground', leaf: 'hill2', leaf2: 'hill1', ...colors };
    return [{ path: _PL([[x - h * .04, y], [x - h * .025, y - h * .5], [x + h * .025, y - h * .5], [x + h * .04, y]]), fill: c.trunk },
      { path: _C(x, y - h * .68, h * .28), fill: c.leaf }, { path: _C(x - h * .2, y - h * .52, h * .2), fill: c.leaf2 }, { path: _C(x + h * .2, y - h * .54, h * .19), fill: c.leaf2 }];
  },
  /** 車（側面，朝右）：車身、車窗、輪子。w = 車長 */
  car(x, y, w, colors = {}) {
    const c = { body: 'sun', glass: 'sky1', wheel: 'ink', ...colors }, h = w * .3, wr = w * .09;
    return [{ path: _RR(x - w / 2, y - wr - h * .55, w, h * .55, h * .15), fill: c.body },
      { path: _PL([[x - w * .28, y - wr - h * .55], [x - w * .16, y - wr - h], [x + w * .16, y - wr - h], [x + w * .3, y - wr - h * .55]]), fill: c.body },
      { path: _PL([[x - w * .22, y - wr - h * .6], [x - w * .13, y - wr - h * .92], [x + w * .12, y - wr - h * .92], [x + w * .22, y - wr - h * .6]]), fill: c.glass },
      { path: _C(x - w * .3, y - wr, wr), fill: c.wheel }, { path: _C(x + w * .3, y - wr, wr), fill: c.wheel }];
  },
};
/** 畫一組部件（LK_SHAPES 的回傳值），fill 部件用畫風的 shape 填法，stroke 部件畫線 */
function lookDraw(L, P, parts, o = {}) {
  parts.forEach(pt => {
    if (pt.fill) lookShape(L, P, pt.path, pt.fill, o);
    if (pt.stroke) { ctx.save(); ctx.globalAlpha *= pt.alpha ?? 1; pt.path(); ctx.strokeStyle = lookCol(P, pt.stroke); ctx.lineWidth = pt.lw || 1; ctx.lineCap = 'round'; ctx.stroke(); ctx.restore(); }
  });
}

/**
 * 自訂場景用：包住整段繪製，處理像素化（pixel）與最上層質感（overlay）。
 * fn(L, P) 裡照常畫；用 lookShape 讓主體套用畫風。
 */
function withLook(s, t, pulse, fn) {
  const { L, P, name } = lookOf(s);
  if (L.pixel) {
    // 緩衝區與主畫布同樣套 DPR：txt() 記下的矩陣才會跟主畫布一致（否則高解析度螢幕上文字縮小偏移）
    const bw = Math.ceil(W * DPR), bh = Math.ceil(H * DPR);
    if (!withLook.buf || withLook.buf.width !== bw || withLook.buf.height !== bh) {
      withLook.buf = document.createElement('canvas'); withLook.buf.width = bw; withLook.buf.height = bh;
      withLook.small = document.createElement('canvas');
    }
    const prev = ctx, b = withLook.buf.getContext('2d'); b.setTransform(1, 0, 0, 1, 0, 0); b.clearRect(0, 0, bw, bh); b.setTransform(DPR, 0, 0, DPR, 0, 0);
    ctx = b; fn(L, P, name); ctx = prev;
    const sm = withLook.small, k = L.pixel; sm.width = Math.ceil(W / k); sm.height = Math.ceil(H / k);
    const sx = sm.getContext('2d'); sx.imageSmoothingEnabled = false; sx.drawImage(withLook.buf, 0, 0, sm.width, sm.height);
    ctx.save(); ctx.imageSmoothingEnabled = false; ctx.drawImage(sm, 0, 0, W, H); ctx.restore();
  } else fn(L, P, name);
  if (L.overlay) L.overlay(P, t, pulse);
}

/* ---------- L_look：資料驅動的開放構圖 ----------
 * data: {
 *   look: "ink",                      畫風名稱（見檔頭）
 *   pal: { hill2: "#…" },             選用：覆寫色盤
 *   horizon: .6,                      地平線（畫面高度比例）
 *   sun: { x: .72, y: .55, r: .07 } | null,   太陽／月亮（r 是 MIN 的比例）；null 不畫
 *   clouds: [ { x, y, size, speed } ] | 數量,  雲（畫風沒有雲就略過）
 *   layers: [                          由遠到近；每層可以是：
 *     { ridge: { base: .57, amp: .17, seed: 5 }, color: "hill1", parallax: .02 },   山稜線
 *     { points: [[x,y], …], color: "ground", parallax: .13, solid: true },         任意多邊形（0–1 座標）
 *     { grid: { y: .6 }, color: "line" }                                            透視網格地面
 *   ],
 *   particles: { n: 30, color: "petal", size: .006 },
 *   caption: { no: "01", title: "…", note: "…" },
 *   seal: "風",  sfx: "咻——",            選用：朱印、狀聲字
 *   camera: { push: .01 },
 *   port: { …以上任一欄位… }            直式專屬構圖（覆寫）
 * }
 * 沒給 layers 時用預設的三層山＋前景坡。 */
function _lookData(s) { const d = (s && s.data) || {}; return PORT && d.port ? { ...d, ...d.port } : d; }
function _lookDefaultLayers(hz) {
  return [{ ridge: { base: hz - .03, amp: .17, seed: 5 }, color: 'hill1', parallax: .02 }, { ridge: { base: hz + .07, amp: .12, seed: 9 }, color: 'hill2', parallax: .05 },
    { ridge: { base: hz + .17, amp: .08, seed: 17 }, color: 'hill3', parallax: .09 },
    { points: [[0, .9], [.1, .84], [.2, .8], [.32, .81], [.5, .9], [.7, .95], [1, .93], [1, 1], [0, 1]], color: 'ground', parallax: .13, solid: true }];
}
function _lookLayerPts(ly, w, h, m) {   // 回傳 [多邊形, 上緣]（像素，含左右留白 m）
  if (ly.ridge) { const r = ly.ridge, pts = lookRidge(w, h, r.base * H + (r.base > 1 ? 0 : 0), (r.amp || .1) * MIN, r.seed || 1, r.n || 18); return [pts, pts.slice(0, -2)]; }
  const pts = (ly.points || []).map(([a, b]) => [m + a * W, b * H]); return [pts, null];
}
function L_look(t, T, pulse, s) {
  const d = _lookData(s), hz = (d.horizon ?? pick(.6, .56)) * H, drift = t / T;
  const cam = (d.camera && d.camera.push) ?? .01;
  withLook(s, t, pulse, (L, P, name) => {
    const key = 'lk-' + name + '-' + (s.fn || '') + '-' + (s.start ?? '') + '-' + (PORT ? 'p' : 'l') + '-' + JSON.stringify(P).length + (P.sky1 || '') + (P.ground || '');
    ctx.save(); camPush(1.02 + t * cam);
    drawCached(key + '-sky', 0, 0, W, H, (x, w, h) => L.sky(x, w, h, P, hz));
    if (d.sun !== null) { const sn = d.sun || { x: pick(.72, .66), y: hz / H - .05, r: .07 }; L.sun(P, sn.x * W, sn.y * H, (sn.r || .07) * MIN, t, pulse, hz); }
    if (L.cloud) {
      const cl = Array.isArray(d.clouds) ? d.clouds : [[.12, .16, .34, .6], [.55, .08, .26, 1], [.3, .32, .22, 1.4], [.78, .3, .18, 1.8]].slice(0, d.clouds ?? 4).map(([x, y, size, speed]) => ({ x, y, size, speed }));
      cl.forEach((c, i) => {
        const cw = MIN * c.size * 2.4, ch = MIN * c.size, seed = 11 + i * 12;
        const im = cached(key + '-cl' + i, cw, ch, (x, w, h) => L.cloud(x, w, h, seed, P));
        const cx = W * c.x - cw / 2 + drift * MIN * .04 * (c.speed ?? 1), cy = H * c.y * pick(1, .8) + (L.hang ? Math.sin(t * 1.4 + i) * MIN * .008 : 0);
        if (L.hang) line(cx + cw / 2, 0, cx + cw / 2, cy + ch * .2, rgba(P.shadow || P.ink, .4), 1);
        ctx.drawImage(im, cx, cy, cw, ch);
      });
    }
    const layers = d.layers || _lookDefaultLayers(hz / H), m = W * .1;
    layers.forEach((ly, i) => {
      if (i === layers.length - 1 && L.between) L.between(P, t, hz);
      if (ly.grid) {   // 透視網格地面
        const gy = ly.grid.y * H, sp = (t * .6) % 1; ctx.save(); ctx.fillStyle = lookCol(P, ly.fill || 'ground'); ctx.fillRect(0, gy, W, H - gy);
        ctx.shadowBlur = MIN * .015; ctx.shadowColor = lookCol(P, ly.color || 'line'); ctx.strokeStyle = ctx.shadowColor; ctx.lineWidth = MIN * .002 * (1 + pulse * .6);
        for (let k = 0; k < 16; k++) { const u = (k + sp) / 16, y = gy + (H - gy) * u * u; ctx.globalAlpha = u; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
        ctx.globalAlpha = 1; for (let k = -12; k <= 12; k++) { ctx.beginPath(); ctx.moveTo(W / 2 + k * W * .02, gy); ctx.lineTo(W / 2 + k * W * .2, H); ctx.stroke(); }
        ctx.restore(); return;
      }
      const bw = W + m * 2, solid = ly.solid ?? (i === layers.length - 1), depth = layers.length > 1 ? i / (layers.length - 1) : 1;
      const im = cached(key + '-ly' + i, bw, H, (x, w, h) => {
        let [pts, edge] = _lookLayerPts(ly, w, h, m);
        L.fill(x, pts, lookCol(P, ly.color), (ly.seed || (ly.ridge && ly.ridge.seed) || i + 1) * 3 + i, { depth, solid, edge }, P);
      });
      const sway = L.sway ? Math.sin(t * 1.2 + i * 1.3) * MIN * .006 : 0, jit = L.jitter ? Math.sin(t * 12 + i) * .8 : 0;
      ctx.drawImage(im, -m - drift * W * (ly.parallax ?? .02 * (i + 1)) + jit, sway, bw, H);
    });
    if (d.particles) { const pc = d.particles, R = rng(pc.seed || 5), col = rgba(lookCol(P, pc.color || 'petal'), .85), sz = pc.size || .006;
      for (let i = 0; i < (pc.n || 30); i++) {
        const x0 = R() * W * 1.4, y0 = R() * H, v = .5 + R(), ph = R() * 6;
        const x = ((x0 - t * MIN * .09 * v) % (W * 1.4) + W * 1.4) % (W * 1.4) - W * .2, y = (y0 + t * MIN * .035 * v + Math.sin(t * 1.5 + ph) * MIN * .02) % H;
        ctx.save(); ctx.translate(x, y); ctx.rotate(t * 2 * v + ph); ctx.scale(1, .5 + .5 * Math.sin(t * 3 + ph));
        ctx.beginPath(); ctx.ellipse(0, 0, MIN * sz * v, MIN * sz * .6 * v, 0, 0, Math.PI * 2); ctx.fillStyle = col; ctx.fill(); ctx.restore();
      } }
    ctx.restore();
  });
  lookExtras(t, s);
}
/** 朱印、狀聲字、畫風標籤（L_look 會自動呼叫；自訂場景可在 withLook 之後呼叫） */
function lookExtras(t, s) {
  const d = _lookData(s), { P } = lookOf(s);
  if (d.seal) { const sz = MIN * .06, ix = SAFE.r - sz, iy = SAFE.y;
    ctx.save(); ctx.globalAlpha = tw(t, .6, .3, 'back'); fillRR(ix, iy, sz, sz, sz * .1, P.seal || STYLE.c.a1);
    txt(d.seal, ix + sz / 2, iy + sz / 2, { size: sz * .62, weight: 900, fam: 'display', color: P.paper || STYLE.c.bg, align: 'center', maxW: sz }); ctx.restore(); }
  if (d.sfx) { const p = tw(t, BEAT * 2, .35, 'back'), so = { size: fz('h1'), weight: 900, fam: 'display', align: 'center', maxW: SAFE.w * .5 };
    ctx.save(); ctx.translate(W * .6, H * pick(.22, .2)); ctx.rotate(-.12); ctx.scale(p, p);
    txtB(d.sfx, MIN * .008, MIN * .008, { ...so, color: P.ink || STYLE.c.fg }); txtB(d.sfx, 0, 0, { ...so, color: P.sfx || P.label || STYLE.c.bg }); ctx.restore(); }
  if (d.caption) {
    const c = d.caption, col = P.label || STYLE.c.fg, a = tw(t, .2, .5), z = fz('h3'), head = (c.no ? c.no + '　' : '') + (c.title || '');
    const [r, g, b] = rgb(col), light = (r * .299 + g * .587 + b * .114) > 140;
    const bw = Math.max(measure(head, { size: z, weight: 800, fam: 'display' }).w, c.note ? measure(c.note, { size: fz('cap'), weight: 600 }).w : 0) + z * 1.2;
    ctx.save(); ctx.globalAlpha = a; fillRR(SAFE.x - z * .6, SAFE.b - fz('cap') * 1.6 - z * 1.55, Math.min(bw, SAFE.w * .85), z * 1.55 + fz('cap') * 2.6, z * .35,
      light ? 'rgba(15,12,25,.42)' : 'rgba(255,252,245,.72)'); ctx.restore();
    const m = txt(head, SAFE.x, SAFE.b - fz('cap') * 1.6, { size: z, weight: 800, fam: 'display', color: col, base: 'bottom', alpha: a, maxW: SAFE.w * .6 });
    if (c.note) txt(c.note, SAFE.x, m.bottom + fz('cap') * .3, { size: fz('cap'), weight: 600, color: col, base: 'top', alpha: a * .85, maxW: SAFE.w * .8 });
  }
}
