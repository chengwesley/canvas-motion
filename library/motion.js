/* motion.js：動作質感工具（動畫原則的程式版）。用法與原則見 references/craft.md。
 * 全部是 t 的純函式：同一個 t 永遠得到同一個結果，所以殘影、拖尾、動態模糊都能精確重算。
 * 這些是「動法」，不是「版面」：畫什麼、放哪裡仍由場景決定。 */

/** 彈簧：從 start 秒開始由 0 彈到 1，會過衝再回穩。freq 越高越快、damp 越小越彈（.2 很彈、.7 幾乎不過衝） */
function spring(t, start = 0, freq = 2.2, damp = .38) {
  const x = t - start; if (x <= 0) return 0;
  const w = freq * 2 * Math.PI, z = clamp(damp, .01, .99), wd = w * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w * x) * (Math.cos(wd * x) + (z * w / wd) * Math.sin(wd * x));
}

/** 預備動作：先往反方向退 amt，再衝到 1。wind 是預備佔整段的比例，ease 是衝出去的緩動（'back' 會再過衝一點） */
function anticipate(t, start, dur, amt = .18, wind = .3, ease = 'out') {
  const p = prog(t, start, start + dur);
  if (p < wind) return -amt * E.io(p / wind);
  return lerp(-amt, 1, E[ease]((p - wind) / (1 - wind)));
}

/** 數值微分：fn 是 t → 數字或 {x, y} 的函式，回傳該時間的速度（每秒） */
function vel(fn, t, dt = 1 / 120) {
  const a = fn(t - dt), b = fn(t + dt);
  return typeof a === 'number' ? (b - a) / (2 * dt) : { x: (b.x - a.x) / (2 * dt), y: (b.y - a.y) / (2 * dt) };
}

/** 擠壓與伸展：沿速度方向拉長、垂直方向變窄（面積不變），在 (x, y) 畫 draw()。
 *  k 是靈敏度（速度 × k = 拉伸量）、max 是上限。靜止時等於沒變形 */
function withSquash(x, y, vx, vy, draw, k = .0009, max = .5) {
  const sp = Math.hypot(vx, vy), s = Math.min(max, sp * k / (MIN / 720)), a = Math.atan2(vy, vx);
  ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.scale(1 + s, 1 / (1 + s)); ctx.rotate(-a);
  draw(); ctx.restore();
}

/** 落地擠壓：在 hitT 撞擊後，物體壓扁再回彈。回傳 {sx, sy}，底部對齊地面時用 ctx.scale(sx, sy) */
function impact(t, hitT, amt = .35, dur = .32) {
  const x = t - hitT; if (x < 0 || x > dur) return { sx: 1, sy: 1 };
  const d = Math.exp(-x / dur * 4) * Math.cos(x / dur * Math.PI * 2.5) * amt;
  return { sx: 1 + d, sy: 1 / (1 + d) };
}

/** 跟隨與重疊：同一段動作延遲 i × lag 秒。頭髮、尾巴、隊伍裡的第 i 個成員用它，停下時會晚一點才停 */
const lagT = (t, i, lag = .06) => t - i * lag;

/** 拖尾：沿 fn(t) 的軌跡往回取 n 個位置，由舊到新呼叫 draw(pos, i, alpha)。gap 是取樣間隔秒數 */
function trail(t, fn, draw, n = 6, gap = 1 / 50) {
  for (let i = n; i >= 0; i--) draw(fn(t - i * gap), i, i ? (1 - i / (n + 1)) * .45 : 1);
}

/** 抹影（smear）：速度快時，在這一格和上一格位置之間補上殘影，2D 動畫的招牌手法；慢的時候什麼都不做。
 *  fn(t) → {x, y}；draw(pos, alpha) 畫一次物體。minPx 是每格至少移動多少像素才開始抹 */
function smear(t, fn, draw, n = 5, dt = 1 / 30, minPx) {
  const a = fn(t - dt), b = fn(t), d = Math.hypot(b.x - a.x, b.y - a.y);
  if (d > (minPx ?? MIN * .02)) for (let i = n; i >= 1; i--) {
    const u = i / (n + 1); draw({ ...b, x: lerp(b.x, a.x, u), y: lerp(b.y, a.y, u) }, (1 - u) * .5);
  }
  draw(b, 1);
}

/** 抹影線：圓形物體高速移動時，畫一條從舊位置漸細到新位置的膠囊，比多個殘影更像手繪 */
function smearLine(x0, y0, x1, y1, r, col) {
  const d = Math.hypot(x1 - x0, y1 - y0); if (d < 1) return;
  const a = Math.atan2(y1 - y0, x1 - x0);
  ctx.save(); ctx.translate(x1, y1); ctx.rotate(a); ctx.fillStyle = col; ctx.beginPath();
  ctx.moveTo(0, -r); ctx.lineTo(-d, -r * .15); ctx.lineTo(-d, r * .15); ctx.lineTo(0, r); ctx.closePath(); ctx.fill();
  ctx.restore();
}

/** 弧線運動：兩點間走弧線（自然的動作都走弧線，不走直線）。回傳 {x, y, ang}，ang 是前進方向 */
function arcPt(x1, y1, x2, y2, p, lift = .3) {
  const d = Math.hypot(x2 - x1, y2 - y1), mx = (x1 + x2) / 2, my = (y1 + y2) / 2 - d * lift;
  const u = clamp(p), a = (1 - u) * (1 - u), b = 2 * u * (1 - u), e = u * u;
  const dx = 2 * (1 - u) * (mx - x1) + 2 * u * (x2 - mx), dy = 2 * (1 - u) * (my - y1) + 2 * u * (y2 - my);
  return { x: a * x1 + b * mx + e * x2, y: a * y1 + b * my + e * y2, ang: Math.atan2(dy, dx) };
}

/** 拍點衝擊：beats 是本幕的拍數清單（例如 [2, 4, 6]），回傳最近一次衝擊後的衰減 0–1。閃光、放大、震動都用它 */
function hit(t, beats, decay = 7) {
  let last = -1e9; for (const b of beats) { const bt = b * BEAT; if (bt <= t && bt > last) last = bt; }
  return last < -1e8 ? 0 : Math.exp(-(t - last) * decay);
}

/** 鏡頭震動：在 hitT 之後震 dur 秒、逐漸停下。回傳 {x, y, r}，用 ctx.translate(x, y); ctx.rotate(r) 套用 */
function shake(t, hitT, amp = .015, dur = .35, seed = 1) {
  const x = t - hitT; if (x < 0 || x > dur) return { x: 0, y: 0, r: 0 };
  const k = Math.pow(1 - x / dur, 2) * amp * MIN, f = x * 38 + seed * 17;
  return { x: noise1(f) * k, y: noise1(f + 91) * k, r: noise1(f + 47) * k / MIN * .5 };
}

/** 鏡頭：把畫面上的 (x, y) 放到畫面中心、放大 zoom 倍、旋轉 rot，再畫 draw()。
 *  景別：遠景 zoom 1、中景約 1.8、特寫約 3。用 lerp 在兩個鏡頭之間移動就是推軌、搖鏡 */
function shot(cam, draw) {
  const z = cam.zoom ?? 1;
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(cam.rot || 0); ctx.scale(z, z);
  ctx.translate(-(cam.x ?? W / 2), -(cam.y ?? H / 2)); draw(); ctx.restore();
}
const camLerp = (a, b, p) => ({ x: lerp(a.x ?? W / 2, b.x ?? W / 2, p), y: lerp(a.y ?? H / 2, b.y ?? H / 2, p),
  zoom: lerp(a.zoom ?? 1, b.zoom ?? 1, p), rot: lerp(a.rot || 0, b.rot || 0, p) });

/** 視差圖層：depth 0 = 最遠（不動）、1 = 跟鏡頭一起動、>1 = 前景（動得比鏡頭快）。
 *  camX / camY 是鏡頭位移（像素）。blur > 0 時用景深模糊（前景或遠景失焦，主體清楚） */
function layer(depth, camX, camY, draw, blur = 0) {
  ctx.save(); ctx.translate(-camX * depth, -camY * depth);
  if (blur > .3) ctx.filter = `blur(${blur.toFixed(1)}px)`;
  draw(); ctx.restore();
}

/** 一拍兩格（on twos）：把時間量化成每秒 fps 格。手繪、美漫、剪紙、蠟筆畫風用它，動作會有手作的頓挫感 */
const onTwos = (t, fps = 12) => Math.floor(t * fps + 1e-6) / fps;
