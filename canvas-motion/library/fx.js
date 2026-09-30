/* fx.js：類型特效（動漫、美漫、港漫、電影）。用法與各類型的規則見 references/genres.md。
 * 全部是 t 的純函式；會「抖」的效果（集中線、火、閃電）用 floor(t × 12) 當種子，每 2 格換一次形狀，這是動畫感的來源。
 * 光敏安全：全畫面閃光（fxFlash、fxInvert）每秒不要超過 3 次。 */

const _fxQ = (t, fps = 12) => Math.floor(t * fps + 1e-6);
/** 墨色：亮底風格用前景色，暗底風格（前景是淺色）固定用深墨，框裡的字才讀得到 */
const fxInk = () => STYLE.light ? STYLE.c.fg : '#141414';

/* ---------- 動漫／漫畫的動態 ---------- */
/** 集中線：從畫面外指向焦點的楔形，中心留空。o: { n, inner（留空半徑，短邊比例）, col, amt 0–1, fps } */
function fxFocusLines(cx, cy, t, o = {}) {
  const amt = o.amt ?? 1; if (amt <= .01) return;
  const R = rng(97 + _fxQ(t, o.fps || 12)), n = o.n || 90, far = Math.hypot(W, H), inner = MIN * (o.inner ?? .3);
  ctx.save(); ctx.fillStyle = o.col || STYLE.c.fg; ctx.globalAlpha *= amt;
  for (let i = 0; i < n; i++) {
    const a = R() * 6.283, w = (.004 + R() * .012), r0 = inner * (1 + R() * .6) + (1 - amt) * far * .4;
    ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0);
    ctx.lineTo(cx + Math.cos(a + w) * far, cy + Math.sin(a + w) * far); ctx.lineTo(cx + Math.cos(a - w) * far, cy + Math.sin(a - w) * far); ctx.fill();
  }
  ctx.restore();
}
/** 流線：背景換成平行速度條紋（主體在跑、背景在流）。ang 是流動方向（弧度），speed 像素／秒 */
function fxFlowLines(t, ang = Math.PI, speed = MIN * 3, o = {}) {
  const R = rng(o.seed || 5), n = o.n || 40, L = Math.hypot(W, H);
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(ang); ctx.strokeStyle = o.col || rgba(STYLE.c.fg, .5); ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const y = (R() - .5) * L, len = MIN * (.1 + R() * .5), sp = speed * (.6 + R() * .8);
    const x = ((R() * L + t * sp) % (L * 1.5)) - L * .75;
    ctx.lineWidth = MIN * (.002 + R() * .006); ctx.globalAlpha = .3 + R() * .5;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - len, y); ctx.stroke();
  }
  ctx.restore();
}
/** 衝擊幀：在 hitT 起 frames 格（24fps）內回傳 0,1,2…，其他時間回傳 -1。場景依回傳值換成剪影或反相畫面 */
const fxImpact = (t, hitT, frames = 3) => { const k = Math.floor((t - hitT) * 24); return k >= 0 && k < frames ? k : -1; };
/** 全畫面反相（difference 疊白）。在場景最後呼叫 */
function fxInvert(a = 1) { ctx.save(); ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.globalCompositeOperation = 'difference'; ctx.globalAlpha = a; ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, W, H); ctx.restore(); }
/** 白閃：hitT 後迅速淡出 */
function fxFlash(t, hitT, col = '#ffffff', dur = .12) {
  const x = t - hitT; if (x < 0 || x > dur) return;
  ctx.save(); ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.globalAlpha = 1 - x / dur; ctx.fillStyle = col; ctx.fillRect(0, 0, W, H); ctx.restore();
}
/** 衝擊波環：t0 起擴張、變細、消失 */
function fxShockwave(x, y, t, t0, maxR = MIN * .6, col = '#ffffff', dur = .45) {
  const p = prog(t, t0, t0 + dur); if (p <= 0 || p >= 1) return;
  ctx.save(); ctx.strokeStyle = col; ctx.globalAlpha = 1 - p; ctx.lineWidth = MIN * .03 * (1 - p) + 1;
  ctx.beginPath(); ctx.ellipse(x, y, maxR * E.out(p), maxR * E.out(p) * .45, 0, 0, 6.283); ctx.stroke(); ctx.restore();
}

/* ---------- 特效作畫：火、煙、火花、碎片、閃電、氣勁 ---------- */
/** 火：外紅、中橙、白黃核心的舌狀火焰，每 2 格換形（不連續變形） */
function fxFire(x, y, w, h, t, o = {}) {
  const q = _fxQ(t, o.fps || 12), cols = o.cols || ['#e8361f', '#ff8a1c', '#ffe9a0'];
  ctx.save(); ctx.globalCompositeOperation = o.add ? 'lighter' : 'source-over';
  cols.forEach((c, L) => {
    const R = rng((o.seed || 1) * 31 + q * 7 + L), k = 1 - L * .28, n = 5 + L;
    ctx.fillStyle = c; ctx.beginPath(); ctx.moveTo(x - w / 2 * k, y);
    for (let i = 0; i <= n; i++) {
      const u = i / n, tx = x - w / 2 * k + u * w * k, th = h * k * (.45 + R() * .55) * Math.sin(Math.PI * (.15 + u * .7));
      ctx.quadraticCurveTo(tx - w * .06, y - th * .5, tx + (R() - .5) * w * .1, y - th);
      ctx.quadraticCurveTo(tx + w * .06, y - th * .45, x - w / 2 * k + (i + .5) / n * w * k, y - h * .15 * k);
    }
    ctx.lineTo(x + w / 2 * k, y); ctx.closePath(); ctx.fill();
    // 頂端斷開的火苗：上升、縮小
    for (let j = 0; j < 2; j++) { const u = R(), ph = ((t * 2 + R()) % 1); circle(x + (u - .5) * w * k * .6, y - h * k * (.8 + ph * .6), w * .04 * k * (1 - ph), c); }
  });
  ctx.restore();
}
/** 煙：團狀球體，快速膨脹後慢慢漂移、縮小消散（不是淡出）。t0 起算，dur 秒 */
function fxSmoke(x, y, r, t, t0, o = {}) {
  const p = prog(t, t0, t0 + (o.dur || 1.6)); if (p <= 0 || p >= 1) return;
  const R = rng(o.seed || 3), n = o.n || 9, grow = E.out(clamp(p * 3)), die = clamp((p - .45) / .55);
  for (let i = 0; i < n; i++) {
    const a = R() * 6.283, d = r * (.3 + R() * .7) * grow, rr = r * (.35 + R() * .3) * grow * (1 - die * (.6 + R() * .4));
    const px = x + Math.cos(a) * d + (o.wind || 0) * p * r, py = y + Math.sin(a) * d * .6 - p * r * .8;
    if (rr <= 0) continue;
    circle(px, py, rr, o.col || '#8a8a90'); circle(px - rr * .25, py - rr * .25, rr * .7, o.lit || '#b9b9be');
  }
}
/** 火花：細長菱形，拋物線飛出，約 .3 秒壽命 */
function fxSparks(x, y, t, t0, o = {}) {
  const R = rng(o.seed || 9), n = o.n || 14, life = o.life || .35;
  ctx.save(); ctx.fillStyle = o.col || '#ffe28a';
  for (let i = 0; i < n; i++) {
    const a = (o.ang ?? -Math.PI / 2) + (R() - .5) * (o.spread ?? 2.4), sp = MIN * (1.2 + R() * 1.6), x0 = t - t0 - R() * .05;
    if (x0 < 0 || x0 > life) continue;
    const px = x + Math.cos(a) * sp * x0, py = y + Math.sin(a) * sp * x0 + MIN * 2.2 * x0 * x0, vx = Math.cos(a) * sp, vy = Math.sin(a) * sp + MIN * 4.4 * x0;
    const L = MIN * .035 * (1 - x0 / life), ang = Math.atan2(vy, vx);
    ctx.save(); ctx.translate(px, py); ctx.rotate(ang); ctx.beginPath(); ctx.moveTo(L, 0); ctx.lineTo(0, L * .12); ctx.lineTo(-L * 1.6, 0); ctx.lineTo(0, -L * .12); ctx.fill(); ctx.restore();
  }
  ctx.restore();
}
/** 碎片：石塊或紙片，旋轉、受重力落下 */
function fxDebris(x, y, t, t0, o = {}) {
  const R = rng(o.seed || 4), n = o.n || 12, x0 = t - t0; if (x0 < 0 || x0 > (o.life || 1.4)) return;
  for (let i = 0; i < n; i++) {
    const a = -Math.PI / 2 + (R() - .5) * 2.6, sp = MIN * (.5 + R() * 1.2), s = MIN * (.012 + R() * .03), rot = (R() - .5) * 16;
    const px = x + Math.cos(a) * sp * x0, py = y + Math.sin(a) * sp * x0 + MIN * 1.6 * x0 * x0;
    ctx.save(); ctx.translate(px, py); ctx.rotate(rot * x0); ctx.fillStyle = o.col || '#6b5a4a'; ctx.beginPath();
    ctx.moveTo(-s, -s * .6); ctx.lineTo(s * .8, -s); ctx.lineTo(s, s * .5); ctx.lineTo(-s * .4, s); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = o.line || '#141414'; ctx.lineWidth = 1.5; ctx.stroke(); ctx.restore();
  }
}
/** 閃電：折線加分岔，每 1–2 格重新生成，白核加色暈 */
function fxLightning(x1, y1, x2, y2, t, o = {}) {
  const R = rng((o.seed || 2) * 13 + _fxQ(t, o.fps || 20)), segs = 10, pts = [[x1, y1]];
  const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy), nx = -dy / L, ny = dx / L;
  for (let i = 1; i < segs; i++) { const u = i / segs, off = (R() - .5) * L * .18; pts.push([x1 + dx * u + nx * off, y1 + dy * u + ny * off]); }
  pts.push([x2, y2]);
  const stroke = (w, c) => { ctx.strokeStyle = c; ctx.lineWidth = w; ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(...p) : ctx.moveTo(...p)); ctx.stroke(); };
  ctx.save(); ctx.lineJoin = 'round'; ctx.globalCompositeOperation = 'lighter';
  stroke(MIN * .02, rgba(o.col || '#7fe8ff', .35)); stroke(MIN * .008, o.col || '#7fe8ff'); stroke(MIN * .003, '#ffffff');
  ctx.restore();
}
/** 氣勁（港漫）：沿著一圈向外的火焰狀舌頭，白核→彩色外緣，多層加亮疊加。box = {x, y, w, h}（通常是角色外框） */
function fxAura(box, t, o = {}) {
  const q = _fxQ(t, o.fps || 12), cols = o.cols || ['#ff6a13', '#ffc940', '#fff6d0'], cx = box.x + box.w / 2, cy = box.y + box.h / 2, amt = o.amt ?? 1, op = o.alpha ?? .55;
  if (amt <= .01) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  cols.forEach((c, L) => {
    const R = rng(17 + q * 5 + L), n = 22, k = (1.25 - L * .12) * amt;
    ctx.fillStyle = rgba(c, op * (1 - L * .25)); ctx.beginPath();
    for (let i = 0; i <= n * 2; i++) {
      const a = i / (n * 2) * 6.283 - Math.PI / 2, up = Math.max(0, -Math.sin(a)) * .8 + .35, spike = i % 2 ? .55 : 1 + R() * .7 * up;
      const rx = box.w / 2 * k * (i % 2 ? .92 : spike), ry = box.h / 2 * k * (i % 2 ? .92 : spike);
      ctx.lineTo(cx + Math.cos(a) * rx, cy + Math.sin(a) * ry - (i % 2 ? 0 : up * box.h * .12 * amt));
    }
    ctx.closePath(); ctx.fill();
  });
  ctx.restore();
}
/** 能量黑點（Kirby 式）：大小不一、互相重疊的黑點團，形成滋滋作響的碎形邊緣 */
function fxKrackle(x, y, r, t, o = {}) {
  const R = rng((o.seed || 6) + _fxQ(t, o.fps || 8)), n = o.n || 26;
  for (let i = 0; i < n; i++) {
    const a = R() * 6.283, d = r * Math.sqrt(R()), rr = MIN * (.004 + R() * .02) * (1 - d / r * .5);
    circle(x + Math.cos(a) * d, y + Math.sin(a) * d, rr, o.col || STYLE.c.fg);
    if (R() < .4) { ctx.save(); ctx.strokeStyle = o.col || STYLE.c.fg; ctx.lineWidth = rr * .5; ctx.beginPath(); ctx.arc(x + Math.cos(a) * d, y + Math.sin(a) * d, rr * 1.8, 0, 6.283); ctx.stroke(); ctx.restore(); }
  }
}

/* ---------- 印刷與陰影 ---------- */
/** 網點（Ben-Day／港漫網點）：angle 網角（美漫 C105° M75° Y90° K45°）、cell 網格（短邊比例）、dens(u, v) → 0–1 濃度。會烘焙快取 */
function fxHalftone(x, y, w, h, col, dens, o = {}) {
  const cell = MIN * (o.cell || .014), ang = (o.angle ?? 45) * Math.PI / 180, key = `fx-ht-${o.key || 'a'}`;
  ctx.drawImage(cached(key, w, h, (c, cw, ch) => {
    c.fillStyle = col; const L = Math.hypot(cw, ch);
    c.translate(cw / 2, ch / 2); c.rotate(ang);
    for (let yy = -L / 2; yy < L / 2; yy += cell) for (let xx = -L / 2; xx < L / 2; xx += cell) {
      const px = xx * Math.cos(ang) - yy * Math.sin(ang) + cw / 2, py = xx * Math.sin(ang) + yy * Math.cos(ang) + ch / 2;
      if (px < -cell || py < -cell || px > cw + cell || py > ch + cell) continue;
      const d = dens(px / cw, py / ch); if (d > .03) { c.beginPath(); c.arc(xx, yy, cell * .55 * Math.sqrt(d), 0, 6.283); c.fill(); }
    }
  }, [col, o.cell, o.angle, o.dk || 0]), x, y, w, h);
}
/** 排線陰影：在 path() 範圍內畫平行線（cross = true 再加一組 90°），美漫羽毛線、港漫肌肉紋都用它 */
function fxHatch(path, bb, o = {}) {
  const g = o.gap || MIN * .008, ang = (o.angle ?? 30) * Math.PI / 180;
  ctx.save(); ctx.beginPath(); path(); ctx.clip(); ctx.strokeStyle = o.col || rgba(STYLE.c.fg, .6); ctx.lineWidth = o.lw || Math.max(.8, MIN * .0015);
  const cx = (bb[0] + bb[2]) / 2, cy = (bb[1] + bb[3]) / 2, L = Math.hypot(bb[2] - bb[0], bb[3] - bb[1]);
  [ang].concat(o.cross ? [ang + Math.PI / 2] : []).forEach(a => {
    ctx.beginPath();
    for (let d = -L / 2; d < L / 2; d += g) { const px = cx + Math.cos(a + Math.PI / 2) * d, py = cy + Math.sin(a + Math.PI / 2) * d;
      ctx.moveTo(px - Math.cos(a) * L / 2, py - Math.sin(a) * L / 2); ctx.lineTo(px + Math.cos(a) * L / 2, py + Math.sin(a) * L / 2); }
    ctx.stroke();
  });
  ctx.restore();
}

/* ---------- 電影感 ---------- */
/** 寬銀幕黑邊：ratio 2.39 或 1.85；p 0–1 做「黑邊收進來」的開場 */
function fxLetterbox(ratio = 2.39, p = 1, col = '#000000') {
  if (W / H >= ratio) return;
  const bar = (H - W / ratio) / 2 * clamp(p);
  ctx.save(); ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.fillStyle = col; ctx.fillRect(0, 0, W, bar); ctx.fillRect(0, H - bar, W, bar); ctx.restore();
  return bar;
}
/** 調色：暗部偏青、亮部偏橙（teal-orange），再壓暗角。a 為強度 .15–.3 */
function fxGrade(o = {}) {
  ctx.save(); ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, o.shadow || '#0f3b4a'); g.addColorStop(1, o.high || '#f0a060');
  ctx.globalCompositeOperation = 'soft-light'; ctx.globalAlpha = o.a ?? .25; ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const v = ctx.createRadialGradient(W / 2, H / 2, Math.hypot(W, H) * .25, W / 2, H / 2, Math.hypot(W, H) * .6);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, `rgba(0,0,0,${o.vignette ?? .45})`);
  ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = 1; ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}
/** 光束（丁達爾光）：從 (x, y) 往 ang 方向射出的幾道梯形光，加亮疊加，塵粒緩慢漂移 */
function fxRays(x, y, ang, t, o = {}) {
  const R = rng(o.seed || 8), n = o.n || 5, L = Math.hypot(W, H) * 1.2, col = o.col || '#ffe8b0';
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  for (let i = 0; i < n; i++) {
    const a = ang + (R() - .5) * (o.spread ?? .5), w0 = MIN * .01, w1 = MIN * (.08 + R() * .15), al = (o.a ?? .14) * (.6 + .4 * Math.sin(t * .8 + i * 2));
    const g = ctx.createLinearGradient(x, y, x + Math.cos(a) * L, y + Math.sin(a) * L); g.addColorStop(0, rgba(col, al)); g.addColorStop(1, rgba(col, 0));
    const nx = -Math.sin(a), ny = Math.cos(a); ctx.fillStyle = g; ctx.beginPath();
    ctx.moveTo(x + nx * w0, y + ny * w0); ctx.lineTo(x + Math.cos(a) * L + nx * w1, y + Math.sin(a) * L + ny * w1);
    ctx.lineTo(x + Math.cos(a) * L - nx * w1, y + Math.sin(a) * L - ny * w1); ctx.lineTo(x - nx * w0, y - ny * w0); ctx.fill();
  }
  for (let i = 0; i < (o.dust ?? 30); i++) { const px = (R() * W + t * MIN * .02 * (R() + .2)) % W, py = (R() * H + Math.sin(t + i) * MIN * .02) % H;
    circle(px, py, MIN * .002 * (1 + R()), rgba(col, .35 * R())); }
  ctx.restore();
}
/** 鏡頭光斑：沿著光源 → 畫面中心的連線放幾個光圈 */
function fxFlare(lx, ly, a = .6, col = '#ffd9a0') {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  glow(lx, ly, MIN * .35, col, a);
  [[.35, .05, .25], [.7, .025, .35], [1.25, .07, .15], [1.6, .03, .3]].forEach(([k, r, al]) => {
    const px = lx + (W / 2 - lx) * k * 2, py = ly + (H / 2 - ly) * k * 2;
    ctx.globalAlpha = al * a; ctx.strokeStyle = col; ctx.lineWidth = MIN * .004; ctx.beginPath(); ctx.arc(px, py, MIN * r, 0, 6.283); ctx.stroke();
    ctx.globalAlpha = al * a * .4; circle(px, py, MIN * r, col);
  });
  ctx.restore();
}
/** 雨：斜向細線，dens 密度 */
function fxRain(t, o = {}) {
  const R = rng(o.seed || 12), n = o.n || 120, ang = o.ang ?? 1.35, sp = MIN * 2.5, len = MIN * .05;
  ctx.save(); ctx.strokeStyle = o.col || 'rgba(200,220,255,.45)'; ctx.lineWidth = Math.max(1, MIN * .0015); ctx.beginPath();
  for (let i = 0; i < n; i++) { const x0 = R() * W * 1.4 - W * .2, y0 = ((R() * H + t * sp * (.8 + R() * .4)) % (H + len)) - len;
    ctx.moveTo(x0 + Math.cos(ang) * (y0 / Math.sin(ang)) * .2, y0); ctx.lineTo(x0 + Math.cos(ang) * (y0 / Math.sin(ang)) * .2 + Math.cos(ang) * len, y0 + Math.sin(ang) * len); }
  ctx.stroke(); ctx.restore();
}
/** 多層發光（撮影的 diffusion）：把 draw() 畫進離屏，再用 3 層模糊加亮疊回。發光只給光源與特效，不要整個畫面都發光 */
function fxGlowPass(draw, strength = 1) {
  const c = cached('fx-glowbuf', W, H, () => {}), x = c.getContext('2d');
  x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, c.width, c.height); x.setTransform(DPR, 0, 0, DPR, 0, 0);
  const keep = ctx; ctx = x; try { draw(); } finally { ctx = keep; }
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalCompositeOperation = 'lighter';
  [[MIN * .01, .8], [MIN * .03, .5], [MIN * .08, .35]].forEach(([b, a]) => { ctx.filter = `blur(${(b * DPR).toFixed(1)}px)`; ctx.globalAlpha = a * strength; ctx.drawImage(c, 0, 0); });
  ctx.filter = 'none'; ctx.globalAlpha = 1; ctx.drawImage(c, 0, 0); ctx.restore();
}

/* ---------- 文字：狀聲字、對白框、旁白框、片名 ---------- */
/** 狀聲字：立體厚字＋粗描邊＋傾斜。文字本體用 txtB（會進文字檢查）。o: { fill, stroke, extrude（像素）, ang, skew, fam, weight, maxW } */
function fxSFX(s, x, y, size, o = {}) {
  const fam = o.fam || 'display', wt = o.weight || 900, ex = o.extrude ?? size * .08, st = o.stroke || fxInk();
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.ang || -.08); ctx.transform(1, 0, o.skew ?? -.12, 1, 0, 0);
  setFont(size, wt, fam); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  for (let k = Math.ceil(ex); k > 0; k -= Math.max(1, ex / 6)) { ctx.fillStyle = st; ctx.fillText(s, k, k); }
  ctx.lineWidth = size * .16; ctx.strokeStyle = st; ctx.strokeText(s, 0, 0);
  if (o.outer) { ctx.lineWidth = size * .28; ctx.strokeStyle = o.outer; ctx.globalCompositeOperation = 'destination-over'; ctx.strokeText(s, 0, 0); ctx.globalCompositeOperation = 'source-over'; }
  txtB(s, 0, 0, { size, weight: wt, fam, align: 'center', color: o.fill || '#ffe14d', maxW: o.maxW || SAFE.w, gradient: o.gradient });
  ctx.restore();
}
/** 對白框：kind 'speech' 橢圓、'shout' 爆炸框、'thought' 雲＋小圓串、'radio' 鋸齒。尾巴指向 (tx, ty)。文字用 txt，回傳框的外框 */
function fxBalloon(s, x, y, tx, ty, o = {}) {
  const size = o.size || fz('h3'), maxW = o.maxW || SAFE.w * .4, m = measure(s, { size, weight: o.weight || 800, fam: o.fam || 'sans', maxW });
  const w = m.w + size * 1.6, h = m.h + size * 1.2, kind = o.kind || 'speech', ink = o.line || fxInk(), paper = o.paper || '#ffffff';
  ctx.save(); ctx.lineWidth = Math.max(2, MIN * .005); ctx.strokeStyle = ink; ctx.fillStyle = paper; ctx.lineJoin = 'round';
  const tail = () => { const a = Math.atan2(ty - y, tx - x), bx = x + Math.cos(a) * w * .35, by = y + Math.sin(a) * h * .35, nx = -Math.sin(a) * size * .45, ny = Math.cos(a) * size * .45;
    const ex = lerp(bx, tx, .6), ey = lerp(by, ty, .6); ctx.moveTo(bx + nx, by + ny); ctx.lineTo(ex, ey); ctx.lineTo(bx - nx, by - ny); };
  ctx.beginPath();
  if (kind === 'shout') { const R = rng(o.seed || 3), n = 16; for (let i = 0; i < n * 2; i++) { const a = i / (n * 2) * 6.283, k = i % 2 ? .82 : 1.12 + R() * .15; ctx.lineTo(x + Math.cos(a) * w / 2 * k, y + Math.sin(a) * h / 2 * k); } ctx.closePath(); }
  else if (kind === 'radio') { const n = 20; for (let i = 0; i <= n; i++) { const a = i / n * 6.283, k = i % 2 ? .93 : 1.04; ctx.lineTo(x + Math.cos(a) * w / 2 * k, y + Math.sin(a) * h / 2 * k); } ctx.closePath(); }
  else if (kind === 'thought') { for (let i = 0; i < 12; i++) { const a = i / 12 * 6.283; ctx.moveTo(x + Math.cos(a) * w * .42 + h * .22, y + Math.sin(a) * h * .4); ctx.arc(x + Math.cos(a) * w * .42, y + Math.sin(a) * h * .4, h * .22, 0, 6.283); } ctx.ellipse(x, y, w * .45, h * .42, 0, 0, 6.283); }
  else { ctx.ellipse(x, y, w / 2, h / 2, 0, 0, 6.283); }
  if (kind !== 'thought') tail();
  ctx.stroke(); ctx.fill();
  if (kind === 'thought') [.55, .75, .9].forEach((u, i) => { ctx.beginPath(); ctx.arc(lerp(x, tx, u), lerp(y + h / 2, ty, u), size * (.3 - i * .08), 0, 6.283); ctx.fill(); ctx.stroke(); });
  else { ctx.beginPath(); ctx.ellipse(x, y, w / 2 - ctx.lineWidth, h / 2 - ctx.lineWidth, 0, 0, 6.283); if (kind === 'speech') ctx.fill(); }
  ctx.restore();
  txt(s, x, y, { size, weight: o.weight || 800, fam: o.fam || 'sans', align: 'center', color: ink, maxW, alpha: o.alpha ?? 1 });
  return { x: x - w / 2, y: y - h / 2, w, h };
}
/** 旁白框（港漫多層方框、美漫地點時間框）：左上對齊 */
function fxCaption(s, x, y, o = {}) {
  const size = o.size || fz('body'), pad = size * .5, maxW = (o.maxW || SAFE.w * .45) - pad * 2, m = measure(s, { size, weight: o.weight || 700, fam: o.fam || 'sans', maxW });
  const w = m.w + pad * 2, h = m.h + pad * 1.4;
  ctx.save(); ctx.globalAlpha *= o.alpha ?? 1; ctx.fillStyle = o.shadow || fxInk(); ctx.fillRect(x + size * .15, y + size * .15, w, h);
  ctx.fillStyle = o.paper || '#fff8e0'; ctx.fillRect(x, y, w, h); ctx.strokeStyle = fxInk(); ctx.lineWidth = Math.max(1.5, MIN * .003); ctx.strokeRect(x, y, w, h); ctx.restore();
  txt(s, x + pad, y + h / 2, { size, weight: o.weight || 700, fam: o.fam || 'sans', color: o.color || fxInk(), maxW, alpha: o.alpha ?? 1 });
  return { x, y, w, h, bottom: y + h };
}
/** 電影片名：細字、寬字距、慢慢淡入、光從字後掃過 */
function fxTitle(s, x, y, t, t0, o = {}) {
  const size = o.size || fz('h1'), a = tw(t, t0, o.fade || .6, 'io') * (o.out != null ? 1 - tw(t, o.out, .5, 'in') : 1);
  if (a <= .01) return;
  const sweep = prog(t, t0 + .2, t0 + 1.8), m = measure(s, { size, weight: o.weight || 300, fam: o.fam || 'display', track: o.track ?? .25 });
  glow(x - m.w / 2 + m.w * sweep, y, size * 1.4, o.glow || '#ffe8c0', .45 * a * Math.sin(Math.PI * sweep));
  txt(s, x, y, { size, weight: o.weight || 300, fam: o.fam || 'display', align: 'center', track: o.track ?? .25, alpha: a, color: o.color || '#f4efe6', maxW: SAFE.w });
}

/* ---------- 漫畫分格 ---------- */
/** 一頁分格：kind 'grid'（n 格規則）、'action'（斜格，第一格大）、'strip'（橫條，眼睛特寫用）。回傳多邊形陣列 [[x,y]…] */
function fxPanels(kind, A, o = {}) {
  const g = MIN * (o.gap ?? .018), sl = (o.slant ?? .08) * A.h, { x, y, w, h } = A;
  if (kind === 'strip') { const n = o.n || 3, hh = (h - g * (n - 1)) / n; return Array.from({ length: n }, (_, i) => [[x, y + i * (hh + g)], [x + w, y + i * (hh + g)], [x + w, y + i * (hh + g) + hh], [x, y + i * (hh + g) + hh]]); }
  if (kind === 'action') {
    const mx = x + w * .58, my = y + h * .55;
    return [[[x, y], [mx + sl, y], [mx - sl, my - g / 2], [x, my - g / 2]], [[mx + sl + g, y], [x + w, y], [x + w, my - g / 2 - sl], [mx - sl + g, my - g / 2]],
            [[x, my + g / 2], [x + w * .4 + sl, my + g / 2], [x + w * .4 - sl, y + h], [x, y + h]], [[x + w * .4 + sl + g, my + g / 2], [x + w, my + g / 2 - sl], [x + w, y + h], [x + w * .4 - sl + g, y + h]]];
  }
  const n = o.n || 4, c = Math.ceil(Math.sqrt(n)), r = Math.ceil(n / c), cw = (w - g * (c - 1)) / c, ch = (h - g * (r - 1)) / r;
  return Array.from({ length: n }, (_, i) => { const px = x + (i % c) * (cw + g), py = y + Math.floor(i / c) * (ch + g); return [[px, py], [px + cw, py], [px + cw, py + ch], [px, py + ch]]; });
}
/** 在一格裡畫東西：裁切到格子、白底、粗框。draw(bb) 的 bb = [x0, y0, x1, y1] */
function fxPanel(poly, draw, o = {}) {
  const bb = [Math.min(...poly.map(p => p[0])), Math.min(...poly.map(p => p[1])), Math.max(...poly.map(p => p[0])), Math.max(...poly.map(p => p[1]))];
  const path = () => { ctx.beginPath(); poly.forEach((p, i) => i ? ctx.lineTo(...p) : ctx.moveTo(...p)); ctx.closePath(); };
  ctx.save(); path(); ctx.fillStyle = o.paper || '#fffaf0'; ctx.fill(); ctx.clip(); draw(bb); ctx.restore();
  ctx.save(); path(); ctx.lineWidth = o.lw || Math.max(2, MIN * .006); ctx.strokeStyle = o.line || fxInk(); ctx.lineJoin = 'miter'; ctx.stroke(); ctx.restore();
  return bb;
}
