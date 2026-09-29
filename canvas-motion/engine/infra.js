'use strict';
/* ==========================================================================
 * Canvas Motion — infra.js（固定引擎，作品之間共用，不要為單一作品修改）
 * 提供：畫布尺寸、數學與緩動、色彩、排版（fz/fit/wrap/txt）、繪圖工具、
 *       快取、3D 投影、轉場、後製。完整 API 見 references/api.md。
 * ========================================================================== */

const CV = document.getElementById('cv');
const MAIN = CV.getContext('2d');
let ctx = MAIN;                // 場景一律畫在全域 ctx；轉場時引擎會暫時換成緩衝區
let W = 1280, H = 720, DPR = 1, PORT = false, SQUARE = false, MIN = 720;
const _caches = new Map();
const _bufs = [];

function resize(w, h, dpr) {
  DPR = Math.min(dpr || 1, 1.5);
  W = Math.max(2, Math.round(w)); H = Math.max(2, Math.round(h));
  CV.width = Math.round(W * DPR); CV.height = Math.round(H * DPR);
  CV.style.width = W + 'px'; CV.style.height = H + 'px';
  PORT = H > W * 1.05; SQUARE = !PORT && W < H * 1.2; MIN = Math.min(W, H);
  MAIN.setTransform(DPR, 0, 0, DPR, 0, 0);
  _caches.clear(); _bufs.length = 0;
}
function buf(i) {
  let b = _bufs[i];
  if (!b || b.c.width !== CV.width || b.c.height !== CV.height) {
    const c = document.createElement('canvas'); c.width = CV.width; c.height = CV.height;
    b = _bufs[i] = { c, x: c.getContext('2d') };
  }
  const x = b.x;
  x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, b.c.width, b.c.height);
  x.setTransform(DPR, 0, 0, DPR, 0, 0); x.globalAlpha = 1; x.globalCompositeOperation = 'source-over';
  return b;
}

/* ---------- 數學與緩動 ---------- */
const clamp = (v, a = 0, b = 1) => v < a ? a : v > b ? b : v;
const lerp = (a, b, p) => a + (b - a) * p;
const prog = (t, a, b) => clamp((t - a) / (b - a));
const E = {
  lin: p => p,
  out: p => 1 - Math.pow(1 - p, 3),
  in: p => p * p * p,
  io: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
  expo: p => p >= 1 ? 1 : 1 - Math.pow(2, -10 * p),
  back: p => { const c = 1.70158; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); },
  elastic: p => p <= 0 ? 0 : p >= 1 ? 1 : Math.pow(2, -10 * p) * Math.sin((p * 10 - .75) * 2.0944) + 1,
};
/** 從 a 秒開始、持續 d 秒的補間，回傳 0→1 */
const tw = (t, a, d, ease = 'out') => E[ease](prog(t, a, a + d));
/** 進場後在場景結尾前退場：適合每個元素的 alpha */
const inout = (t, T, a, d, ease = 'out', outD = .35) => tw(t, a, d, ease) * (1 - tw(t, T - outD, outD, 'in'));
/** 第 i 個元素的錯開補間 */
const stag = (t, i, start, gap, d, ease = 'out') => tw(t, start + i * gap, d, ease);
/** 橫式／直式二選一 */
const pick = (land, port, square) => PORT ? port : (SQUARE && square !== undefined ? square : land);
function rng(seed) {
  let a = (seed >>> 0) || 1;
  return () => { a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
function noise1(x) {
  const i = Math.floor(x), f = x - i, h = n => { const s = Math.sin(n * 127.1) * 43758.5453; return s - Math.floor(s); };
  const u = f * f * (3 - 2 * f); return lerp(h(i), h(i + 1), u) * 2 - 1;
}
/** 數字滾動：countUp(p, 0, 12800) → "12,800"；decimals 小數位 */
function countUp(p, from, to, decimals = 0) {
  const v = lerp(from, to, clamp(p));
  return v.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}
/** 打字效果：依 p 回傳前 n 個字 */
const typeOn = (s, p) => { const a = Array.from(String(s)); return a.slice(0, Math.round(a.length * clamp(p))).join(''); };

/* ---------- 色彩 ---------- */
const _rgbC = new Map();
function rgb(c) {
  if (_rgbC.has(c)) return _rgbC.get(c);
  let r = 255, g = 255, b = 255;
  if (c[0] === '#') {
    let h = c.slice(1); if (h.length === 3) h = h.split('').map(x => x + x).join('');
    r = parseInt(h.slice(0, 2), 16); g = parseInt(h.slice(2, 4), 16); b = parseInt(h.slice(4, 6), 16);
  } else { const m = c.match(/[\d.]+/g); if (m) [r, g, b] = m.map(Number); }
  const v = [r, g, b]; _rgbC.set(c, v); return v;
}
const rgba = (c, a) => { const [r, g, b] = rgb(c); return `rgba(${r},${g},${b},${a})`; };
function mixc(c1, c2, p) { const a = rgb(c1), b = rgb(c2);
  return `rgb(${Math.round(lerp(a[0], b[0], p))},${Math.round(lerp(a[1], b[1], p))},${Math.round(lerp(a[2], b[2], p))})`; }
/** 依序取風格強調色 a1/a2/a3 */
const accent = i => [STYLE.c.a1, STYLE.c.a2, STYLE.c.a3][((i % 3) + 3) % 3];

/* ---------- 版面 ---------- */
const SAFE = {
  get x() { return Math.round(W * (PORT ? .08 : .065)); },
  get y() { return Math.round(H * (PORT ? .07 : .09)); },
  get w() { return W - 2 * this.x; },
  get h() { return H - 2 * this.y; },
  get r() { return W - this.x; },
  get b() { return H - this.y; },
};
const FZ_L = { hero: .15, h1: .10, h2: .068, h3: .048, body: .036, cap: .026, tiny: .02 };
const FZ_P = { hero: .17, h1: .115, h2: .082, h3: .06, body: .046, cap: .035, tiny: .027 };
/** 字級：fz('h1')；直式以寬為基準、橫式以高為基準。也可傳比例數字 */
function fz(k) { const r = typeof k === 'number' ? k : (PORT ? FZ_P : FZ_L)[k] || FZ_L.body; return Math.round((PORT ? W : H) * r); }
const fam = f => (STYLE.fonts && STYLE.fonts[f]) || f || 'sans-serif';
function setFont(size, weight = 700, f = 'sans', c = ctx) { c.font = `${weight} ${size}px ${fam(f)}`; }

const NO_START = '，。、．,.!！?？:：;；)）]］}｝」』》〉】〕…‧·—%％ー～';
const NO_END = '(（[［{｛「『《〈【〔';
function _tokens(s) {
  const out = []; let b = '';
  for (const ch of s) {
    if (/[\u2E80-\u9FFF\uF900-\uFAFF\uFF00-\uFFEF\u3000-\u303F]/.test(ch)) { if (b) { out.push(b); b = ''; } out.push(ch); }
    else if (ch === ' ') { out.push(b + ' '); b = ''; }
    else b += ch;
  }
  if (b) out.push(b); return out;
}
/** 換行後最後一行是否太短：中文 2 字以內，或只剩一個英文單字（而上一行不只一個） */
function _shortTail(lines) {
  if (lines.length < 2) return false;
  const last = lines[lines.length - 1].trim(), prev = lines[lines.length - 2].trim();
  if (!last) return false;
  const cjk = (last.match(/[\u2E80-\u9FFF\uF900-\uFAFF\uFF00-\uFFEF\u3000-\u303F]/g) || []).length;
  if (cjk && [...last].length <= 2) return true;
  return !cjk && !/\s/.test(last) && /\s/.test(prev) && last.length <= 8;
}
/** 自動換行（中文逐字、英文逐詞，含避頭點與避尾點）。
 *  最後一行太短時自動收窄寬度重排，讓行長平均（不會出現「……跟上了／嗎？」） */
function wrap(s, maxW, size, weight = 700, f = 'sans', c = ctx) {
  const k = `w:${s}|${Math.round(maxW)}|${Math.round(size)}|${weight}|${f}|${c.letterSpacing || ''}`;
  let r = _caches.get(k); if (r) return r;
  r = _wrapRaw(s, maxW, size, weight, f, c);
  if (_shortTail(r) && !String(s).includes('\n')) {
    for (let w = maxW * .96; w >= maxW * .55; w *= .96) {
      const t = _wrapRaw(s, w, size, weight, f, c);
      if (t.length > r.length) break;
      if (!_shortTail(t)) { r = t; break; }
    }
  }
  _caches.set(k, r); return r;
}
function _wrapRaw(s, maxW, size, weight = 700, f = 'sans', c = ctx) {
  setFont(size, weight, f, c); const lines = [];
  for (const para of String(s).split('\n')) {
    let line = '';
    for (const t of _tokens(para)) {
      const test = line + t;
      if (line && c.measureText(test.trimEnd()).width > maxW) {
        if (NO_START.includes(t[0])) { line = test; continue; }
        let carry = '';
        if (NO_END.includes(line.slice(-1))) { carry = line.slice(-1); line = line.slice(0, -1); }
        lines.push(line.trimEnd()); line = carry + t.trimStart();
      } else line = test;
    }
    lines.push(line.trimEnd());
  }
  return lines;
}
/** 找出能在 maxLines 行內放進 maxW 的最大字級。track：字距（字級的比例，同 txt 的 track） */
function fit(s, maxW, size, weight = 700, f = 'sans', maxLines = 1, minR = .5, track = 0) {
  let z = size; const ls = ctx.letterSpacing;
  try {
    while (z > size * minR) { ctx.letterSpacing = track ? (track * z) + 'px' : '0px'; if (wrap(s, maxW, z, weight, f).length <= maxLines) return z; z *= .94; }
    return Math.round(size * minR);
  } finally { ctx.letterSpacing = ls; }
}

/** 換行後最多保留 n 行，超出以「…」結尾 */
function clampLines(s, maxW, size, n = 2, weight = 500, f = 'sans') {
  const ls = wrap(s, maxW, size, weight, f); if (ls.length <= n) return ls.join('\n');
  let last = ls[n - 1]; setFont(size, weight, f);
  while (last.length > 1 && ctx.measureText(last + '…').width > maxW) last = last.slice(0, -1);
  return [...ls.slice(0, n - 1), last + '…'].join('\n');
}

/* ---------- 文字 ---------- */
const TXQ = [];
function _drawText(c, s, x, y, o) {
  const size = o.size || fz('body'), w = o.weight || 700, f = o.fam || 'sans';
  setFont(size, w, f, c);
  c.letterSpacing = o.track ? (o.track * size) + 'px' : '0px';
  const lines = o.maxW ? wrap(s, o.maxW, size, w, f, c) : String(s).split('\n');
  const lh = size * (o.lh || 1.28), total = lh * lines.length;
  const y0 = o.base === 'top' ? y : o.base === 'bottom' ? y - total : y - total / 2;
  c.textAlign = o.align || 'left'; c.textBaseline = 'middle';
  const ga = c.globalAlpha; c.globalAlpha = ga * (o.alpha ?? 1);
  if (o.shadow) { c.shadowColor = o.shadow; c.shadowBlur = size * .45; }
  if (o.gradient) {
    const wmax = Math.max(...lines.map(l => c.measureText(l).width));
    const gx = o.align === 'center' ? x - wmax / 2 : o.align === 'right' ? x - wmax : x;
    const g = c.createLinearGradient(gx, 0, gx + wmax, 0);
    o.gradient.forEach((col, i) => g.addColorStop(i / Math.max(1, o.gradient.length - 1), col));
    c.fillStyle = g;
  } else c.fillStyle = o.color || STYLE.c.fg;
  lines.forEach((ln, i) => c.fillText(ln, x, y0 + lh * (i + .52)));
  c.shadowBlur = 0; c.shadowColor = 'transparent'; c.globalAlpha = ga; c.letterSpacing = '0px';
  let wmax = 0; for (const l of lines) wmax = Math.max(wmax, c.measureText(l).width);
  return { w: wmax, h: total, lines: lines.length, top: y0, bottom: y0 + total };
}
/** 量測文字區塊，不繪製；top/bottom 以 y 為基準 */
function measure(s, o = {}, y = 0) {
  const size = o.size || fz('body'), w = o.weight || 700, f = o.fam || 'sans';
  MAIN.save(); setFont(size, w, f, MAIN); MAIN.letterSpacing = o.track ? (o.track * size) + 'px' : '0px';
  const lines = o.maxW ? wrap(s, o.maxW, size, w, f, MAIN) : String(s).split('\n');
  let wm = 0; for (const l of lines) wm = Math.max(wm, MAIN.measureText(l).width);
  MAIN.restore();
  const total = size * (o.lh || 1.28) * lines.length;
  const y0 = o.base === 'top' ? y : o.base === 'bottom' ? y - total : y - total / 2;
  return { w: wm, h: total, lines: lines.length, top: y0, bottom: y0 + total };
}
/** o.fit = { lines: 2, min: .5 }：在 maxW 內自動縮字到指定行數以內 */
function _autoFit(s, o) {
  if (!o.fit || !o.maxW) return o;
  const z = o.size || fz('body');
  return { ...o, size: fit(s, o.maxW, z, o.weight || 700, o.fam || 'sans', o.fit.lines || 1, o.fit.min || .5, o.track || 0) };
}
/** 延後繪製（在後製之後才畫，保持銳利、不被 bloom 糊掉）。回傳量測結果 */
function txt(s, x, y, o = {}) { o = _autoFit(s, o); TXQ.push({ s, x, y, o, m: ctx.getTransform(), a: ctx.globalAlpha }); return measure(s, o, y); }
/** 立即繪製（會參與 bloom 發光，適合大標與霓虹字） */
const txtB = (s, x, y, o = {}) => _drawText(ctx, s, x, y, _autoFit(s, o));
/**
 * 有底板的文字：壓在畫風背景、照片、複雜圖形上也讀得到。
 * o.plate：'auto'（依字色深淺選深或淺底板，預設）、'dark'、'light'，或直接給顏色；o.pad：內距（字級比例，預設 .5）
 */
function txtPlate(s, x, y, o = {}) {
  o = _autoFit(s, o);
  const m = measure(s, o, y), z = o.size || fz('body'), pad = z * (o.pad ?? .5), col = o.color || STYLE.c.fg;
  const [r, g, b] = rgb(col), light = (r * .299 + g * .587 + b * .114) > 140;
  const plate = o.plate && o.plate !== 'auto' ? (o.plate === 'dark' ? 'rgba(15,12,25,.5)' : o.plate === 'light' ? 'rgba(255,252,245,.78)' : o.plate)
    : (light ? 'rgba(15,12,25,.45)' : 'rgba(255,252,245,.75)');
  const left = o.align === 'center' ? x - m.w / 2 : o.align === 'right' ? x - m.w : x;
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1); fillRR(left - pad, m.top - pad * .6, m.w + pad * 2, m.h + pad * 1.2, z * .35, plate); ctx.restore();
  return txt(s, x, y, o);
}
/** 畫到指定 context（用於 cached() 內） */
const txtOn = (c, s, x, y, o = {}) => _drawText(c, s, x, y, o);
function flushTxt(c) {
  for (const q of TXQ) { c.save(); c.setTransform(q.m); c.globalAlpha = q.a; _drawText(c, q.s, q.x, q.y, q.o); c.restore(); }
  TXQ.length = 0;
}

/* ---------- 跨幕錨點 ----------
 * project.json 的 "anchors": { "stack1": { "x": .25, "y": .6, "s": 1, "r": 0, "port": { "x": .3 } } }
 * 同一個物件在上一幕的終點＝下一幕的起點，用同一個錨點名稱，就不用在兩個場景各寫一次座標。
 * 本幕 data.anchors 可以覆寫。回傳像素座標 { x, y, s, r }。 */
function anchor(name, s) {
  const base = (typeof PROJECT !== 'undefined' && PROJECT.anchors) || {}, over = (s && s.data && s.data.anchors) || {};
  let a = over[name] || base[name];
  if (!a) throw new Error(`找不到錨點 ${name}（在 project.json 的 anchors 定義）`);
  if (PORT && a.port) a = { ...a, ...a.port };
  return { x: (a.x ?? .5) * W, y: (a.y ?? .5) * H, s: a.s ?? 1, r: a.r ?? 0 };
}
/** 兩個錨點之間插值（p 0–1），可加弧形抬升 lift（短邊比例） */
function anchorLerp(a, b, p, lift = 0) {
  const A = typeof a === 'string' ? anchor(a) : a, B = typeof b === 'string' ? anchor(b) : b;
  return { x: lerp(A.x, B.x, p), y: lerp(A.y, B.y, p) - Math.sin(p * Math.PI) * lift * MIN, s: lerp(A.s, B.s, p), r: lerp(A.r, B.r, p) };
}

/* ---------- 形狀 ---------- */
function rrect(x, y, w, h, r, c = ctx) { c.beginPath(); c.roundRect(x, y, w, h, Math.max(0, Math.min(r, w / 2, h / 2))); }
function fillRR(x, y, w, h, r, fill) { rrect(x, y, w, h, r); ctx.fillStyle = fill; ctx.fill(); }
function strokeRR(x, y, w, h, r, col, lw = 1) { rrect(x, y, w, h, r); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.stroke(); }
function circle(x, y, r, fill) { ctx.beginPath(); ctx.arc(x, y, Math.max(0, r), 0, Math.PI * 2); ctx.fillStyle = fill; ctx.fill(); }
function ring(x, y, r, col, lw = 2, p = 1, a0 = -Math.PI / 2) {
  ctx.beginPath(); ctx.arc(x, y, Math.max(0, r), a0, a0 + Math.PI * 2 * clamp(p));
  ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.stroke();
}
function line(x1, y1, x2, y2, col, lw = 1, p = 1) {
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(lerp(x1, x2, clamp(p)), lerp(y1, y2, clamp(p)));
  ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.stroke();
}
/** 卡片：半透明底 + 細框，使用風格 token card / cardLine */
function card(x, y, w, h, o = {}) {
  const r = o.r ?? (STYLE.cardR !== undefined ? MIN * STYLE.cardR : MIN * .018), lw = o.lw || STYLE.cardLw || 1;
  if (STYLE.cardShadow) { ctx.save(); ctx.shadowColor = STYLE.cardShadow; ctx.shadowBlur = MIN * .03; ctx.shadowOffsetY = MIN * .008;
    fillRR(x, y, w, h, r, o.fill || STYLE.c.card); ctx.restore(); } else fillRR(x, y, w, h, r, o.fill || STYLE.c.card);
  strokeRR(x + lw / 2, y + lw / 2, w - lw, h - lw, r, o.stroke || STYLE.c.cardLine, lw);
}
/** 遮罩揭示：在 (x,y,w,h) 內從 dir 方向依 p 展開，fn 內照常繪製 */
function reveal(p, x, y, w, h, fn, dir = 'up') {
  p = clamp(p); if (p <= 0) return; ctx.save(); ctx.beginPath();
  if (dir === 'up') ctx.rect(x, y + h * (1 - p), w, h * p);
  else if (dir === 'down') ctx.rect(x, y, w, h * p);
  else if (dir === 'left') ctx.rect(x + w * (1 - p), y, w * p, h);
  else ctx.rect(x, y, w * p, h);
  ctx.clip(); fn(); ctx.restore();
}
/** 光暈（預先烘焙的貼圖，便宜） */
function glow(x, y, r, col, a = 1) {
  if (STYLE.noGlow) return;
  const k = 'glow:' + col; let s = _caches.get(k);
  if (!s) {
    s = document.createElement('canvas'); s.width = s.height = 128; const g = s.getContext('2d');
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    gr.addColorStop(0, rgba(col, 1)); gr.addColorStop(.3, rgba(col, .35)); gr.addColorStop(1, rgba(col, 0));
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128); _caches.set(k, s);
  }
  const op = ctx.globalCompositeOperation, ga = ctx.globalAlpha;
  // 暗底用加亮混合；亮底（STYLE.light）改用一般混合，否則光暈會變成一片白
  ctx.globalCompositeOperation = STYLE.light ? 'source-over' : 'lighter'; ctx.globalAlpha = ga * clamp(STYLE.light ? a * .6 : a, 0, 4);
  ctx.drawImage(s, x - r, y - r, r * 2, r * 2);
  ctx.globalCompositeOperation = op; ctx.globalAlpha = ga;
}
/** 快取到 offscreen canvas：fn(c, w, h) 只在第一次或尺寸改變時執行 */
/** 烘焙快取。deps：內容依賴的值（顏色、資料…），會併進快取鍵；同一個 key 內容不同時一定要給 */
function cached(key, w, h, fn, deps) {
  const k = `c:${key}:${Math.round(w)}x${Math.round(h)}` + (deps === undefined ? '' : ':' + JSON.stringify(deps)); let c = _caches.get(k);
  if (!c) {
    c = document.createElement('canvas'); c.width = Math.ceil(w * DPR); c.height = Math.ceil(h * DPR);
    const x = c.getContext('2d'); x.setTransform(DPR, 0, 0, DPR, 0, 0); fn(x, w, h); _caches.set(k, c);
  }
  return c;
}
const drawCached = (key, x, y, w, h, fn) => ctx.drawImage(cached(key, w, h, fn), x, y, w, h);

/* ---------- 3D 相機 ---------- */
/** 預設在 z=0 平面上 1 單位 = 1px */
const cam = (o = {}) => ({ x: 0, y: 0, z: -MIN * 1.2, rx: 0, ry: 0, f: MIN * 1.2, ...o });
function proj(p, c) {
  let x = p.x - c.x, y = p.y - c.y, z = p.z - c.z;
  const cy = Math.cos(c.ry), sy = Math.sin(c.ry); [x, z] = [x * cy - z * sy, x * sy + z * cy];
  const cx = Math.cos(c.rx), sx = Math.sin(c.rx); [y, z] = [y * cx - z * sx, y * sx + z * cx];
  if (z <= 1) return null; const s = c.f / z; return { x: W / 2 + x * s, y: H / 2 + y * s, s, z };
}
/** 以畫面中心為原點縮放／旋轉整個場景（鏡頭微動用） */
function camPush(scale = 1, rot = 0, dx = 0, dy = 0) {
  ctx.translate(W / 2 + dx, H / 2 + dy); ctx.rotate(rot); ctx.scale(scale, scale); ctx.translate(-W / 2, -H / 2);
}

/* ---------- 轉場（A、B 為已畫好的整幕緩衝區） ---------- */
const TR = {
  cut(c, A, B, p) { c.drawImage(p < .5 ? A : B, 0, 0, W, H); },
  fade(c, A, B, p) { c.drawImage(A, 0, 0, W, H); c.globalAlpha = E.io(p); c.drawImage(B, 0, 0, W, H); c.globalAlpha = 1; },
  push(c, A, B, p) {
    const e = E.io(p);
    if (PORT) { c.drawImage(A, 0, -H * e, W, H); c.drawImage(B, 0, H * (1 - e), W, H); }
    else { c.drawImage(A, -W * e, 0, W, H); c.drawImage(B, W * (1 - e), 0, W, H); }
  },
  wipe(c, A, B, p) {
    const e = E.io(p), sk = W * .18, x = lerp(-sk, W + sk, e);
    c.drawImage(A, 0, 0, W, H); c.save(); c.beginPath();
    c.moveTo(x - sk, 0); c.lineTo(x, H); c.lineTo(-W, H); c.lineTo(-W, 0); c.closePath(); c.clip();
    c.drawImage(B, 0, 0, W, H); c.restore();
    c.beginPath(); c.moveTo(x - sk, 0); c.lineTo(x, H); c.strokeStyle = STYLE.c.a1; c.lineWidth = MIN * .006; c.stroke();
  },
  zoom(c, A, B, p) {
    const e = E.io(p), sa = 1 + e * .35, sb = .82 + .18 * e;
    c.globalAlpha = 1 - e; c.drawImage(A, W / 2 * (1 - sa), H / 2 * (1 - sa), W * sa, H * sa);
    c.globalAlpha = e; c.drawImage(B, W / 2 * (1 - sb), H / 2 * (1 - sb), W * sb, H * sb); c.globalAlpha = 1;
  },
  iris(c, A, B, p) {
    const e = E.io(p); c.drawImage(A, 0, 0, W, H); c.save(); c.beginPath();
    c.arc(W / 2, H / 2, Math.hypot(W, H) / 2 * e, 0, Math.PI * 2); c.clip(); c.drawImage(B, 0, 0, W, H); c.restore();
  },
  flash(c, A, B, p) {
    c.drawImage(p < .5 ? A : B, 0, 0, W, H);
    c.fillStyle = rgba(STYLE.c.flash || '#ffffff', Math.pow(1 - Math.abs(p - .5) * 2, 2) * .9); c.fillRect(0, 0, W, H);
  },
  glitch(c, A, B, p) {
    const n = 14, r = rng(Math.floor(p * 18) + 7), bh = H / n, sx = CV.width / W;
    for (let i = 0; i < n; i++) {
      const useB = r() < p * 1.15 - .08, src = useB ? B : A, off = (r() - .5) * W * .08 * Math.sin(p * Math.PI);
      c.drawImage(src, 0, i * bh * sx, CV.width, bh * sx, off, i * bh, W, bh + 1);
    }
  },
};

/* ---------- 後製 ----------
 * 為了在無 GPU 的環境也維持效率：bloom 在 1/6 解析度模糊後放大疊加；
 * 暗角與顆粒都在低解析度預先烘焙，每格只做一次縮放貼圖。 */
function _lowCanvas(key, div) {
  const w = Math.max(2, Math.round(CV.width / div)), h = Math.max(2, Math.round(CV.height / div));
  let b = _caches.get(key); if (!b || b.width !== w || b.height !== h) { b = document.createElement('canvas'); b.width = w; b.height = h; _caches.set(key, b); }
  return b;
}
/** 後製（bloom、暗角、顆粒）。c：要處理的畫布 context，預設主畫布；轉場時分別對前後兩幕的緩衝區做 */
function post(time, c = MAIN) {
  const P = STYLE.post || {};
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.imageSmoothingEnabled = true;
  if (P.bloom > 0) {
    const b = _lowCanvas('bloom', 6), bx = b.getContext('2d');
    bx.globalCompositeOperation = 'copy';
    bx.filter = `blur(${Math.max(1.5, b.width / 220)}px) brightness(${P.bloomGain || 1.15})`;
    bx.drawImage(c.canvas, 0, 0, b.width, b.height); bx.filter = 'none';
    c.globalCompositeOperation = 'lighter'; c.globalAlpha = P.bloom; c.drawImage(b, 0, 0, CV.width, CV.height);
  }
  if (P.vignette > 0) {
    let v = _caches.get('vig');
    if (!v) {
      v = _lowCanvas('vig', 8); const x = v.getContext('2d'), w = v.width, h = v.height;
      const g = x.createRadialGradient(w / 2, h / 2, Math.min(w, h) * .35, w / 2, h / 2, Math.hypot(w, h) * .62);
      g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,1)'); x.fillStyle = g; x.fillRect(0, 0, w, h);
    }
    c.globalCompositeOperation = 'source-over'; c.globalAlpha = P.vignette; c.drawImage(v, 0, 0, CV.width, CV.height);
  }
  if (P.grain > 0) {
    const f = Math.floor(time * 12) % 4, k = 'grain' + f; let g = _caches.get(k);
    if (!g) {
      g = _lowCanvas(k, 2); const x = g.getContext('2d'), d = x.createImageData(g.width, g.height), r = rng(f * 977 + 1);
      for (let i = 0; i < d.data.length; i += 4) { const v = r() > .5 ? 255 : 0; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = r() * 255; }
      x.putImageData(d, 0, 0);
    }
    c.globalCompositeOperation = 'source-over'; c.globalAlpha = P.grain * .6; c.imageSmoothingEnabled = false;
    c.drawImage(g, 0, 0, CV.width, CV.height);
  }
  c.restore();
}
