/* product.js：產品介紹與操作示範的畫筆——真實截圖、裝置／視窗外框、游標、打字、鏡頭跟隨、標註。
 * 全部是 t 的純函式，匯出與截圖驗證的畫面一致。用法與產品片的導演思維見 references/product.md。
 * 這些是「畫筆」，不是版面：外框放哪、鏡頭推到哪、介面長什麼樣，仍由場景依素材決定。 */

/* ---------- 截圖素材（<專案>/assets/ 由 build.py 內嵌成 ASSETS） ---------- */
const IMG = {};
const IMG_READY = Promise.all(Object.entries(typeof ASSETS === 'undefined' ? {} : ASSETS).map(([k, src]) => new Promise(res => {
  const im = new Image(); im.onload = im.onerror = () => res(); im.src = src; IMG[k] = im;
})));
const imgOK = name => { const im = IMG[name]; return !!(im && im.complete && im.naturalWidth); };
const _picMiss = new Set();
let _imgDone = false; IMG_READY.then(() => { _imgDone = true; });

/**
 * 把截圖畫進 (x, y, w, h)，回傳座標換算器：m.at(u, v) 把「截圖上的相對位置」（0–1）換成畫面座標，
 * 游標、標註、鏡頭焦點都用它定位，換尺寸或直式時不用重算。
 * o.fit：'cover'（填滿裁切，預設）、'contain'（完整放進）、'width'（寬貼齊，從 o.v 往下捲）
 * o.u / o.v：截圖上要對準框中心的點（0–1，預設 .5）；o.z：再放大幾倍（Ken Burns、局部特寫）
 * o.r：圓角；o.alpha：透明度。截圖找不到時畫佔位框並記一筆場景錯誤（verify 會擋下）
 */
function pic(name, x, y, w, h, o = {}) {
  const m = picMap(name, x, y, w, h, o);
  if (!imgOK(name)) {   // 還在解碼時只畫佔位框，解碼完仍沒有才記錯誤
    if ((_imgDone || !(name in IMG)) && !_picMiss.has(name) && typeof ERRS !== 'undefined') { _picMiss.add(name); ERRS.push({ fn: '(assets)', i: -1, t: 0, msg: `找不到截圖 ${name}（放進 <專案>/assets/ 後重新 build）` }); }
    ctx.save(); ctx.fillStyle = rgba(STYLE.c.fg, .06); fillRR(x, y, w, h, o.r || 0);
    ctx.strokeStyle = rgba(STYLE.c.fg, .25); ctx.setLineDash([8, 6]); strokeRR(x, y, w, h, o.r || 0); ctx.restore();
    return m;
  }
  const b = m.box;
  ctx.save(); ctx.globalAlpha *= o.alpha ?? 1;
  ctx.beginPath(); o.r ? rrect(x, y, w, h, o.r) : ctx.rect(x, y, w, h); ctx.clip();
  ctx.imageSmoothingQuality = 'high'; ctx.drawImage(IMG[name], b.x, b.y, b.w, b.h); ctx.restore();
  return m;
}
/** 只算 pic() 的座標換算、不畫：鏡頭與游標要在畫之前就知道點擊位置時用（參數與 pic 相同） */
function picMap(name, x, y, w, h, o = {}) {
  if (!imgOK(name)) return { s: 1, at: (u, v) => ({ x: x + u * w, y: y + v * h }), box: { x, y, w, h } };
  const im = IMG[name], iw = im.naturalWidth, ih = im.naturalHeight, fit = o.fit || 'cover', z = o.z ?? 1;
  const s0 = fit === 'contain' ? Math.min(w / iw, h / ih) : fit === 'width' ? w / iw : Math.max(w / iw, h / ih), s = s0 * z;
  const dw = iw * s, dh = ih * s;
  const place = (len, d, u) => d <= len ? (len - d) / 2 : clamp(len / 2 - u * d, len - d, 0);   // 不露出截圖外面
  const dx = x + place(w, dw, o.u ?? .5), dy = y + (fit === 'width' && o.v === undefined ? 0 : place(h, dh, o.v ?? .5));
  return { s, at: (u, v) => ({ x: dx + u * dw, y: dy + v * dh }), box: { x: dx, y: dy, w: dw, h: dh } };
}

/* ---------- 外框：瀏覽器、App 視窗、手機、背景 ---------- */
function _uiPal(dark) {
  const d = dark ?? (rgb(STYLE.c.bg).reduce((a, v) => a + v, 0) / 3 < 110);
  return d ? { bar: '#25272d', body: '#16171b', pill: '#34363d', text: '#c9ccd3', line: 'rgba(255,255,255,.08)' }
    : { bar: '#eef0f3', body: '#ffffff', pill: '#ffffff', text: '#5f6670', line: 'rgba(0,0,0,.08)' };
}
/**
 * 介面模型的中性色（自己畫 App 畫面時用，不受風格明暗影響；強調色仍用 STYLE.c.a1）：
 * UI.paper 頁面白、UI.panel 側欄底、UI.ink 主文字、UI.sub 次要文字、UI.line 分隔線、UI.fill 灰色占位條
 */
const UI = { paper: '#ffffff', panel: '#f4f5f8', ink: '#1d2333', sub: '#8a90a0', line: '#e3e6ec', fill: '#e6e8ee',
  dark: { paper: '#1b1d22', panel: '#23262c', ink: '#eceef2', sub: '#9aa0ad', line: '#30343c', fill: '#2c3038' } };
/** 浮起的陰影（畫在外框底下）。lift 0–1：越大越像拿起來 */
function floatShadow(x, y, w, h, r, lift = .5) {
  ctx.save(); ctx.shadowColor = `rgba(0,0,0,${.18 + lift * .22})`; ctx.shadowBlur = MIN * (.03 + lift * .06);
  ctx.shadowOffsetY = MIN * (.01 + lift * .025); ctx.fillStyle = 'rgba(0,0,0,.35)'; fillRR(x, y, w, h, r); ctx.restore();
}
/**
 * 瀏覽器外框。回傳內容區 {x, y, w, h}；內容在 content(box) 裡畫（自動裁切在內容區內）。
 * o.url：網址列文字；o.dark：深色外框（預設跟風格明暗）；o.lift：陰影浮起量；o.r：圓角
 * 內容區裡的字用 txtB(…, { ui: true })：txt() 延後繪製，不會被裁切、會蓋在游標上面；ui: true 讓文字檢查把它當成畫面內容
 */
/* ---------- 立體傾斜進場 ---------- */
/** 傾斜程度：at 秒前是 1（斜躺），之後彈簧轉正到 0、帶一點過衝（會短暫小於 0）。o.dur 大約幾秒轉正 */
function tiltIn(t, at, o = {}) { return 1 - spring(t, at, 1.1 / (o.dur ?? .9), .5); }
/** 以 (cx, cy) 為中心把 draw() 畫成斜躺的樣子：k 1 = 最斜、0 = 正面。o.deg 傾斜角（上限 15°，Canvas 2D 用斜切近似透視，再大會像平行四邊形）、o.rise 下沉量 */
function tilted(cx, cy, k, draw, o = {}) {
  if (Math.abs(k) < .002) return draw();
  const deg = Math.min(o.deg ?? 15, 15) * Math.PI / 180, ry = deg * k, rx = deg * .6 * k, s = 1 - .14 * Math.max(0, k);
  ctx.save(); ctx.translate(cx, cy + Math.max(0, k) * H * (o.rise ?? .14));
  ctx.transform(s * Math.cos(ry), -s * Math.sin(ry) * .35, s * Math.sin(rx) * .35, s * Math.cos(rx), 0, 0);
  ctx.translate(-cx, -cy);
  try { return draw(); } finally { ctx.restore(); }
}

/** 瀏覽器外框的內容區（不畫）：先算好截圖、游標、鏡頭的位置再畫時用 */
const browserContent = (x, y, w, h) => { const bh = Math.max(MIN * .045, h * .065); return { x, y: y + bh, w, h: h - bh }; };
function frameBrowser(x, y, w, h, o = {}, content) {
  if (o.tilt) return tilted(x + w / 2, y + h / 2, o.tilt, () => frameBrowser(x, y, w, h, { ...o, tilt: 0 }, content), o);
  const P = _uiPal(o.dark), r = o.r ?? MIN * .014, bh = browserContent(x, y, w, h).y - y;
  floatShadow(x, y, w, h, r, o.lift ?? .5);
  ctx.save(); ctx.fillStyle = P.body; fillRR(x, y, w, h, r);
  ctx.beginPath(); rrect(x, y, w, h, r); ctx.clip();
  ctx.fillStyle = P.bar; ctx.fillRect(x, y, w, bh); ctx.fillStyle = P.line; ctx.fillRect(x, y + bh - 1, w, 1);
  ['#ff5f57', '#febc2e', '#28c840'].forEach((c, i) => circle(x + bh * (.45 + i * .38), y + bh / 2, bh * .11, c));
  const px = x + bh * 1.6, pw = Math.min(w - bh * 2.6, w * .62);
  ctx.fillStyle = P.pill; fillRR(px, y + bh * .2, pw, bh * .6, bh * .3);
  if (o.url) txtB(o.url, px + bh * .45, y + bh / 2, { size: bh * .3, weight: 500, fam: 'mono', color: P.text, maxW: pw - bh * .9, ui: true });
  const box = { x, y: y + bh, w, h: h - bh };
  if (content) { ctx.save(); ctx.beginPath(); ctx.rect(box.x, box.y, box.w, box.h); ctx.clip(); content(box); ctx.restore(); }
  ctx.restore(); return box;
}
/** App 視窗（桌面軟體）：標題列＋紅黃綠鈕＋可選標題。用法同 frameBrowser */
function frameWindow(x, y, w, h, o = {}, content) {
  if (o.tilt) return tilted(x + w / 2, y + h / 2, o.tilt, () => frameWindow(x, y, w, h, { ...o, tilt: 0 }, content), o);
  const P = _uiPal(o.dark), r = o.r ?? MIN * .014, bh = Math.max(MIN * .036, h * .05);
  floatShadow(x, y, w, h, r, o.lift ?? .5);
  ctx.save(); ctx.fillStyle = P.body; fillRR(x, y, w, h, r);
  ctx.beginPath(); rrect(x, y, w, h, r); ctx.clip();
  ctx.fillStyle = P.bar; ctx.fillRect(x, y, w, bh); ctx.fillStyle = P.line; ctx.fillRect(x, y + bh - 1, w, 1);
  ['#ff5f57', '#febc2e', '#28c840'].forEach((c, i) => circle(x + bh * (.5 + i * .42), y + bh / 2, bh * .13, c));
  if (o.title) txtB(o.title, x + w / 2, y + bh / 2, { size: bh * .38, weight: 600, color: P.text, align: 'center', maxW: w * .5, ui: true });
  const box = { x, y: y + bh, w, h: h - bh };
  if (content) { ctx.save(); ctx.beginPath(); ctx.rect(box.x, box.y, box.w, box.h); ctx.clip(); content(box); ctx.restore(); }
  ctx.restore(); return box;
}
/** 手機外框：(cx, cy) 是中心、h 是機身高。回傳螢幕區；o.body 機身色、o.island 動態島（預設開） */
function framePhone(cx, cy, h, o = {}, content) {
  if (o.tilt) return tilted(cx, cy, o.tilt, () => framePhone(cx, cy, h, { ...o, tilt: 0 }, content), o);
  const w = h * .49, x = cx - w / 2, y = cy - h / 2, r = w * .17, b = w * .035;
  floatShadow(x, y, w, h, r, o.lift ?? .5);
  ctx.save(); ctx.fillStyle = o.body || '#1b1c20'; fillRR(x, y, w, h, r);
  const box = { x: x + b, y: y + b, w: w - b * 2, h: h - b * 2 };
  ctx.fillStyle = '#ffffff'; fillRR(box.x, box.y, box.w, box.h, r - b);
  if (content) { ctx.save(); ctx.beginPath(); rrect(box.x, box.y, box.w, box.h, r - b); ctx.clip(); content(box); ctx.restore(); }
  if (o.island !== false) { ctx.fillStyle = '#000'; fillRR(cx - w * .16, box.y + w * .035, w * .32, w * .085, w * .045); }
  ctx.restore(); return box;
}
/** 產品片背景：底色上幾團緩慢漂移的強調色光暈（Screen Studio 那種漸層桌布）。o.colors 自訂色、o.amt 濃度 */
const _bdC = document.createElement('canvas'), _bdX = _bdC.getContext('2d');
function backdrop(t, o = {}) {   // 漸層畫在 1/8 解析度的小畫布再放大：柔和漸層看不出差別，速度快很多
  const sw = Math.max(16, Math.ceil(W / 8)), sh = Math.max(16, Math.ceil(H / 8));
  if (_bdC.width !== sw || _bdC.height !== sh) { _bdC.width = sw; _bdC.height = sh; }
  const x = _bdX; x.setTransform(1, 0, 0, 1, 0, 0);
  x.fillStyle = STYLE.c.bg; x.fillRect(0, 0, sw, sh);
  const cols = o.colors || [STYLE.c.a1, STYLE.c.a2, STYLE.c.a3], amt = o.amt ?? .5;
  cols.forEach((c, i) => {
    const a = i * 2.1 + .7, gx = sw * (.5 + .38 * Math.cos(a + t * .07)), gy = sh * (.5 + .34 * Math.sin(a * 1.3 + t * .05));
    const g = x.createRadialGradient(gx, gy, 0, gx, gy, Math.max(sw, sh) * .6);
    g.addColorStop(0, rgba(c, .55 * amt)); g.addColorStop(1, rgba(c, 0));
    x.fillStyle = g; x.fillRect(0, 0, sw, sh);
  });
  ctx.save(); ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high'; ctx.drawImage(_bdC, 0, 0, W, H); ctx.restore();
}

/* ---------- 游標：路徑、點擊、拖曳 ---------- */
/**
 * 游標位置。keys 依時間排序：[{ t, x, y, click?, drag? }, …]，t 是「抵達」的秒數。
 * 兩點之間沿微彎的弧線移動，起步慢、抵達前減速（人手的動法）；click: true 在抵達後按下；
 * drag: true 表示從上一點按住拖過來（移動期間 down = 1）。
 * 回傳 { x, y, down（0–1 按下程度）, clickAt（最近一次點擊的秒數，沒有則 null）}
 */
function cursorAt(t, keys, o = {}) {
  const at = tt => {
    const k0 = keys[0]; let x = k0.x, y = k0.y, down = 0, clickAt = null, last = k0.t ?? 0, next = Infinity;
    for (let i = 1; i < keys.length; i++) {
      const a = keys[i - 1], b = keys[i], d = b.dur ?? Math.min(.75, Math.max(.25, (b.t - a.t) * .8));
      const p = E.io(prog(tt, b.t - d, b.t));
      if (p > 0) { const q = arcPt(a.x, a.y, b.x, b.y, p, b.lift ?? .12); x = q.x; y = q.y; }
      if (b.drag && tt > b.t - d - .12 && tt < b.t + .1) down = 1;
      if (tt >= b.t) last = b.t; else if (b.t - d < next) next = b.t - d;
    }
    for (const k of keys) if (k.click) {
      const ct = k.t + .06; if (tt >= ct - .1) clickAt = ct;
      const e = tt - ct; if (e > -.1 && e < .22) down = Math.max(down, e < 0 ? 1 + e / .1 : 1 - e / .22);
    }
    if (k0.click && tt < k0.t) clickAt = null;
    return { x, y, down: clamp(down), clickAt, last, next };
  };
  const c = at(t), b = at(t - 1 / 30), hide = o.hide ?? 1.6;
  c.vx = (c.x - b.x) * 30; c.vy = (c.y - b.y) * 30;   // 速度（像素／秒），drawCursor 用來畫動態模糊
  // 停著超過 hide 秒就淡出，下一段移動前 0.25 秒淡回來（Tella 式；hide: false 關閉）
  c.alpha = hide === false || c.down > 0 ? 1 : Math.max(1 - clamp((t - c.last - hide) / .35), clamp(1 - (c.next - t) / .25));
  delete c.last; delete c.next; return c;
}
/** 畫游標。c 來自 cursorAt；o.kind：'arrow'（預設）或 'hand'；o.size；o.ripple：點擊漣漪顏色（false 關閉）；
 *  o.blur：快速移動時的殘影（預設開，false 關閉）。c.alpha（閒置淡出）會自動套用 */
function drawCursor(c, t, o = {}) {
  const s = (o.size || MIN * .034) * (1 - c.down * .14), a = c.alpha ?? 1;
  if (o.ripple !== false && c.clickAt !== null) clickRipple(c.x, c.y, t - c.clickAt, o.ripple || STYLE.c.a1);
  if (a <= .01) return;
  const sp = Math.hypot(c.vx || 0, c.vy || 0);
  if (o.blur !== false && sp > MIN * 1.2 && !o._ghost) {   // 動態模糊：沿速度反方向畫幾個淡的殘影（約 1/40 秒的軌跡）
    const n = 4;
    for (let i = n; i >= 1; i--) { const k = i / n * .025;
      ctx.save(); ctx.globalAlpha *= a * .22 * (1 - i / (n + 1)); drawCursor({ ...c, x: c.x - c.vx * k, y: c.y - c.vy * k, clickAt: null, alpha: 1 }, t, { ...o, _ghost: true }); ctx.restore(); }
  }
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(c.x, c.y); ctx.scale(s / 24, s / 24);
  ctx.shadowColor = 'rgba(0,0,0,.28)'; ctx.shadowBlur = 5; ctx.shadowOffsetY = 2;
  ctx.beginPath();
  if (o.kind === 'hand') {
    ctx.moveTo(6, 22); ctx.lineTo(2, 13); ctx.quadraticCurveTo(1, 10, 4, 11); ctx.lineTo(7, 14); ctx.lineTo(7, 2);
    ctx.quadraticCurveTo(9.5, 0, 12, 2); ctx.lineTo(12, 9); ctx.quadraticCurveTo(14.5, 7.5, 16, 9.5);
    ctx.quadraticCurveTo(18.5, 8.5, 19.5, 11); ctx.quadraticCurveTo(22, 10.5, 22, 13.5); ctx.lineTo(21, 20); ctx.lineTo(19, 24); ctx.lineTo(8, 24); ctx.closePath();
  } else { ctx.moveTo(0, 0); ctx.lineTo(0, 21); ctx.lineTo(5.5, 16); ctx.lineTo(9.5, 24.5); ctx.lineTo(13, 23); ctx.lineTo(9, 15); ctx.lineTo(16, 15); ctx.closePath(); }
  ctx.fillStyle = '#111'; ctx.fill(); ctx.shadowColor = 'transparent';
  ctx.lineWidth = 1.8; ctx.strokeStyle = '#fff'; ctx.lineJoin = 'round'; ctx.stroke(); ctx.restore();
}
/** 點擊漣漪：age 是點擊後經過的秒數（0.5 秒內有效） */
function clickRipple(x, y, age, col = STYLE.c.a1) {
  if (age < 0 || age > .5) return;
  const p = E.out(age / .5), r = MIN * (.012 + p * .045);
  ctx.save(); ctx.globalAlpha *= (1 - p) * .9; ctx.strokeStyle = col; ctx.lineWidth = MIN * .006 * (1 - p) + 1;
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke();
  ctx.globalAlpha *= .35; ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x, y, r * .55, 0, Math.PI * 2); ctx.fill(); ctx.restore();
}

/* ---------- 打字 ---------- */
/** 打字輸入：從 start 秒起每秒 cps 個字（中文一字一個），回傳 { text, caret（游標此刻是否顯示）, done } */
function typing(s, t, start, cps = 14) {
  const a = Array.from(String(s)), n = clamp(Math.floor((t - start) * cps), 0, a.length);
  const done = n >= a.length, caret = t >= start - .3 && (!done || Math.floor((t - start) * 2.2) % 2 === 0);
  return { text: a.slice(0, n).join(''), caret, done };
}

/* ---------- 鏡頭跟隨（Screen Studio 式自動推近） ---------- */
/**
 * 鏡頭關鍵格：keys = [{ t, x, y, zoom, dur? }, …]，t 是「到位」的秒數，dur 是移過去花多久（預設 .7）。
 * 回傳 shot() 用的鏡頭 {x, y, zoom}。第一格之前停在第一格。推近時焦點不會讓畫面露出邊界（o.bound = false 關閉）。
 * o.breathe：推近停住時的緩慢呼吸幅度（預設 .015，0 關閉），避免停在特寫時畫面完全靜止
 */
function follow(t, keys, o = {}) {
  const at = (tt, log) => {
    let c = { x: keys[0].x ?? W / 2, y: keys[0].y ?? H / 2, zoom: keys[0].zoom ?? 1 };
    for (let i = 1; i < keys.length; i++) {
      const k = keys[i], d = k.dur ?? .7, p = E.io(prog(tt, k.t - d, k.t));
      if (log && (k.zoom ?? 1) > c.zoom + .05) cue('zoom', prog(tt, k.t - d, k.t));
      if (p > 0) c = camLerp(c, { x: k.x ?? W / 2, y: k.y ?? H / 2, zoom: k.zoom ?? 1 }, p);
    }
    return c;
  };
  const c = at(t, true);
  if (o.blur !== false) {   // 動態模糊量：鏡頭在 1/30 秒內移動、縮放了多少（shot() 依 cam.blur 套用）
    const b = at(t - 1 / 30), v = Math.hypot(c.x - b.x, c.y - b.y) * c.zoom / MIN + Math.abs(Math.log(c.zoom / b.zoom));
    c.blur = clamp((v - .006) * 45, 0, 1) * (o.blur ?? 1);
  }
  if (c.zoom > 1.01) c.zoom *= 1 + (o.breathe ?? .015) * (c.zoom - 1) * Math.sin(t * 1.1);
  if (o.bound !== false) {   // 放大後半個可視範圍內不能超出畫面
    const hw = W / 2 / c.zoom, hh = H / 2 / c.zoom;
    c.x = clamp(c.x, Math.min(hw, W / 2), Math.max(W - hw, W / 2)); c.y = clamp(c.y, Math.min(hh, H / 2), Math.max(H - hh, H / 2));
  }
  return c;
}
/**
 * 由游標的點擊自動產生鏡頭：每次點擊前 lead 秒推近到點擊位置（zoom 倍，移動花 dur 秒），
 * 停到點擊後 hold 秒再拉回全景。下一次點擊在 hold＋dur 內時直接平移過去、不拉回。
 * 游標 key 加 focus: true 也會推近（不點擊，只想讓觀眾看清楚）；key 自己的 zoom 覆寫倍率。回傳 follow() 用的 keys
 */
function camFromClicks(keys, o = {}) {
  const z = o.zoom ?? 1.8, lead = o.lead ?? .15, hold = o.hold ?? 1.2, d = o.dur ?? .8;
  const out = [{ t: 0, x: W / 2, y: H / 2, zoom: 1 }], focus = keys.filter(k => k.click || k.focus);
  focus.forEach((k, i) => {
    out.push({ t: k.t - lead, x: k.x, y: k.y, zoom: k.zoom ?? z, dur: d });
    const nx = focus[i + 1];
    if (!nx || nx.t - lead - d > k.t + hold + d) out.push({ t: k.t + hold + d, x: W / 2, y: H / 2, zoom: 1, dur: d });
  });
  return out.sort((a, b) => a.t - b.t);
}

/* ---------- 標註 ---------- */
/** 聚光：把框外壓暗、框線描強調色。p 0–1 進場程度；o.dim 壓暗量、o.r 圓角、o.pad 外擴、o.col 框線色 */
function spotlight(x, y, w, h, p, o = {}) {
  if (p <= 0) return; cue('spotlight', p);
  const pad = o.pad ?? MIN * .01, r = o.r ?? MIN * .012, e = E.out(clamp(p));
  const X = x - pad, Y = y - pad, Wd = w + pad * 2, Hd = h + pad * 2;
  ctx.save(); ctx.fillStyle = `rgba(8,10,16,${(o.dim ?? .5) * e})`;
  ctx.beginPath(); ctx.rect(0, 0, W, H); rrect(X, Y, Wd, Hd, r); ctx.fill('evenodd');
  ctx.strokeStyle = o.col || STYLE.c.a1; ctx.lineWidth = MIN * .004; ctx.globalAlpha *= e;
  const g = 1 + (1 - e) * .06; ctx.translate(X + Wd / 2, Y + Hd / 2); ctx.scale(g, g); ctx.translate(-(X + Wd / 2), -(Y + Hd / 2));
  strokeRR(X, Y, Wd, Hd, r); ctx.restore();
}
/**
 * 功能標籤：從 (px, py) 指向的點拉一條線到標籤 (lx, ly)，標籤是強調色膠囊。p 0–1 進場。
 * 回傳標籤的量測結果。文字用 txt()（延後繪製、保持銳利），所以標籤會在最上層
 */
function callout(px, py, lx, ly, s, p, o = {}) {
  if (p <= 0) return null; cue('callout', p);
  const col = o.col || STYLE.c.a1, size = o.size || fz('small'), e = E.out(clamp(p));
  const m = measure(s, { size, weight: 700, maxW: o.maxW || MIN * .5 });
  const ex = lerp(px, lx, e), ey = lerp(py, ly, e);
  ctx.save(); ctx.globalAlpha *= clamp(p * 3);
  circle(px, py, MIN * .007, col); line(px, py, ex, ey, col, MIN * .003);
  const pad = size * .55, bw = m.w + pad * 2, bh = m.h + pad * 1.1;
  const bx = o.align === 'right' ? ex - bw : o.align === 'center' ? ex - bw / 2 : ex, by = ey - bh / 2;
  ctx.globalAlpha *= clamp((p - .4) / .6); ctx.fillStyle = col; fillRR(bx, by, bw, bh, bh / 2);
  const ink = (([r, g, b]) => r * .299 + g * .587 + b * .114 > 150)(rgb(col)) ? '#111' : '#fff';
  const res = txt(s, bx + pad, ey, { size, weight: 700, color: ink, maxW: o.maxW || MIN * .5 });
  ctx.restore(); return res;
}
