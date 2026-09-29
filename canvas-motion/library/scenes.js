/* ==========================================================================
 * Canvas Motion — 場景庫（library/scenes.js）
 * 資料驅動的通用場景。project.json 裡寫 {"fn": "L_cards", "data": {...}} 即可使用，
 * 不需要寫程式。每個場景都有橫式與直式版面，只用 STYLE.c.* 顏色，任何風格包都能用。
 * 欄位說明見 references/library.md。
 * ========================================================================== */

const _D = s => (s && s.data) || {};
const _n = (arr, max) => (arr || []).slice(0, max);
/** 在可用時間內平均分配 n 個元素的出現間隔，並對齊半拍 */
function _gap(T, n, start = .2, tail = BEAT * 2, max = BEAT * 2) {
  if (n <= 1) return BEAT;
  const g = Math.min(max, (T - start - tail) / (n - 1));
  return Math.max(BEAT * .5, Math.floor(g / (BEAT / 2)) * (BEAT / 2));
}
/** 解析 "NT$ 1,200萬"、"98.5%"、1200 這類數值：回傳 {pre, num, suf, dec, comma} 或 null */
function _num(v) {
  if (typeof v === 'number') return { pre: '', num: v, suf: '', dec: (String(v).split('.')[1] || '').length, comma: v >= 1000 };
  const m = String(v).match(/^(\D*?)(-?[\d,]*\.?\d+)(.*)$/);
  if (!m) return null;
  return { pre: m[1], num: parseFloat(m[2].replace(/,/g, '')), suf: m[3], dec: (m[2].split('.')[1] || '').length, comma: m[2].includes(',') };
}
function _fmtNum(p, v) {
  const q = _num(v); if (!q) return typeOn(v, p);
  const x = lerp(0, q.num, clamp(p));
  const s = q.comma ? x.toLocaleString('en-US', { minimumFractionDigits: q.dec, maximumFractionDigits: q.dec }) : x.toFixed(q.dec);
  return q.pre + s + q.suf;
}
/** 頁首標題：回傳標題下緣的 y */
function L_head(t, title, sub, o = {}) {
  if (!title) return SAFE.y;
  const al = o.align || (PORT ? 'left' : 'center'), x = al === 'left' ? SAFE.x : W / 2, a = tw(t, -.25, .5);
  const size = fit(title, SAFE.w, fz(o.size || 'h2'), 800, 'display', 2);
  const m = txt(title, x, SAFE.y, { size, weight: 800, fam: 'display', align: al, base: 'top', alpha: a, maxW: SAFE.w });
  let b = m.bottom;
  if (sub) b = txt(sub, x, b + fz('body') * .35, { size: fz('body'), weight: 500, color: STYLE.c.mute, align: al, base: 'top', alpha: tw(t, 0, .5), maxW: SAFE.w }).bottom;
  if (al === 'left') line(SAFE.x, b + MIN * .018, SAFE.x + MIN * .08, b + MIN * .018, STYLE.c.a1, MIN * .005, tw(t, .1, .5));
  return b + MIN * .045;
}
/** 自訂或預設的小勾 */
function _check(x, y, r, col, p = 1) {
  ctx.save(); ctx.beginPath(); ctx.moveTo(x - r * .5, y); ctx.lineTo(x - r * .12, y + r * .38); ctx.lineTo(x + r * .55, y - r * .42);
  ctx.strokeStyle = col; ctx.lineWidth = r * .28; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.setLineDash([r * 3, r * 3]); ctx.lineDashOffset = r * 3 * (1 - clamp(p)); ctx.stroke(); ctx.restore();
}
function _cross(x, y, r, col) {
  line(x - r * .4, y - r * .4, x + r * .4, y + r * .4, col, r * .24); line(x + r * .4, y - r * .4, x - r * .4, y + r * .4, col, r * .24);
}

/* ---------- L_title：大字標題（開場、揭示、結論） ----------
 * data: { kicker?, lines: [..], sub?, align?: 'center'|'left' } */
function L_title(t, T, pulse, s) {
  const d = _D(s), lines = _n(d.lines || [d.title || ''], 4), al = d.align || 'center';
  const x = al === 'left' ? SAFE.x : W / 2;
  const longest = lines.reduce((a, b) => (Array.from(b).length > Array.from(a).length ? b : a), '');
  const size = Math.min(fit(longest, SAFE.w, fz(lines.length > 2 ? 'h1' : 'hero'), 800, 'display'), fz('hero'));
  const lh = size * 1.18, kz = fz('cap'), sz = fz('body');
  const blockH = (d.kicker ? kz * 2 : 0) + lh * lines.length + (d.sub ? sz * 2.2 : 0);
  let y = H * pick(.5, .47) - blockH / 2;
  ctx.save(); camPush(1 + t * .01);
  if (d.kicker) {
    const kp = tw(t, -.2, .5);
    txt(d.kicker, x, y + kz / 2, { size: kz, fam: 'mono', weight: 600, color: STYLE.c.a1, align: al, alpha: kp, track: .12, maxW: SAFE.w });
    y += kz * 2;
  }
  lines.forEach((ln, i) => {
    const at = i === 0 ? -.1 : BEAT * 2 * i, p = tw(t, at, .55, 'expo'), yy = y + lh * (i + .5);
    const m = measure(ln, { size, weight: 800, fam: 'display' });
    const lx = al === 'left' ? x : x - m.w / 2;
    const last = i === lines.length - 1 && lines.length > 1;
    reveal(p, lx - size, yy - size * .75, m.w + size * 2, size * 1.5, () =>
      txtB(ln, x, yy + (1 - p) * size * .45, { size, weight: 800, fam: 'display', align: al,
        gradient: last ? [STYLE.c.a1, STYLE.c.a2, STYLE.c.a3] : null }));
  });
  y += lh * lines.length;
  if (d.sub) {
    const sp = tw(t, BEAT * 2 * Math.max(1, lines.length - 1) + BEAT, .5);
    line(al === 'left' ? x : x - SAFE.w * .12, y + sz * .4, al === 'left' ? x + SAFE.w * .18 : x + SAFE.w * .12, y + sz * .4, rgba(STYLE.c.a1, .7), 2, sp);
    txt(d.sub, x, y + sz * 1.5 + (1 - sp) * 10, { size: sz, weight: 500, color: STYLE.c.mute, align: al, alpha: sp, maxW: SAFE.w });
  }
  ctx.restore();
}

/* ---------- L_quote：金句／洞察 ----------
 * data: { quote, by? } */
function L_quote(t, T, pulse, s) {
  const d = _D(s), q = d.quote || '', maxW = SAFE.w * pick(.82, 1);
  const size = fit(q, maxW, fz('h2') * 1.1, 700, 'display', PORT ? 5 : 3, .6);
  const ls = wrap(q, maxW, size, 700, 'display'), lh = size * 1.35, h = ls.length * lh;
  const x0 = W / 2 - maxW / 2, y0 = H * pick(.47, .45) - h / 2;
  ctx.save(); camPush(1.02 - t * .005);
  const mp = tw(t, -.2, .6, 'back');
  txtB('“', x0 - size * .15, y0 - size * .55, { size: size * 2.6, fam: 'display', weight: 800, color: STYLE.c.a1, alpha: mp * .9 });
  ls.forEach((ln, i) => {
    const p = stag(t, i, .05, BEAT * .75, .6);
    txt(ln, x0, y0 + lh * (i + .5) + (1 - p) * size * .4, { size, weight: 700, fam: 'display', alpha: p });
  });
  if (d.by) {
    const bp = tw(t, .1 + ls.length * BEAT * .75 + BEAT, .5);
    line(x0, y0 + h + size * .9, x0 + MIN * .05, y0 + h + size * .9, STYLE.c.a1, 2, bp);
    txt(d.by, x0 + MIN * .07, y0 + h + size * .9, { size: fz('body'), color: STYLE.c.mute, weight: 500, alpha: bp, maxW: maxW - MIN * .07 });
  }
  ctx.restore();
}

/* ---------- L_cards：2–6 張卡片（特色、作品、團隊、資源） ----------
 * data: { title?, sub?, items: [{ title, desc?, tag? }] } */
function L_cards(t, T, pulse, s) {
  const d = _D(s), items = _n(d.items, 6), n = items.length; if (!n) return;
  const top = L_head(t, d.title, d.sub), gap = MIN * .025, bottom = SAFE.b;
  const cols = PORT ? (n <= 4 ? 1 : 2) : (n <= 5 ? n : 3), rows = Math.ceil(n / cols);
  const w = (SAFE.w - gap * (cols - 1)) / cols;
  const h = Math.min((bottom - top - gap * (rows - 1)) / rows, PORT ? MIN * .5 : w * 1.15);
  const y0 = top + (bottom - top - (h * rows + gap * (rows - 1))) / 2;
  const gi = _gap(T, n, 0, BEAT * 3, BEAT * .5), done = gi * (n - 1) + .6;
  const hi = t > done + BEAT ? Math.floor((t - done) / BEAT) % n : -1;
  items.forEach((it, i) => {
    const c = i % cols, r = Math.floor(i / cols), x = SAFE.x + c * (w + gap), y = y0 + r * (h + gap);
    const p = stag(t, i, 0, gi, .6, 'back'), al = clamp(p), col = accent(i);
    ctx.save(); ctx.globalAlpha = al; ctx.translate(0, (1 - p) * MIN * .06);
    if (i === hi) glow(x + w / 2, y + h / 2, Math.max(w, h) * .6, col, .16 + pulse * .12);
    card(x, y, w, h, { stroke: i === hi ? rgba(col, .9) : undefined, lw: i === hi ? Math.max(2, STYLE.cardLw || 1) : undefined });
    const pad = Math.min(w, h) * .12, row = w / h > 2.3;
    const badge = it.tag || String(i + 1).padStart(2, '0'), bz = fz('cap');
    if (row) {
      const bx = x + pad, by = y + h / 2, tx = x + pad + bz * 3.2, tw_ = x + w - pad - tx;
      txt(badge, bx, by, { size: bz, fam: 'mono', weight: 600, color: col });
      const tz = fit(it.title || '', tw_, fz('h3'), 700, 'sans', 1);
      if (it.desc) {
        txt(it.title || '', tx, by - fz('body') * .5, { size: tz, weight: 700 });
        txt(clampLines(it.desc, tw_, fz('body') * .88, 1), tx, by + tz * .62, { size: fz('body') * .88, weight: 500, color: STYLE.c.mute });
      } else txt(it.title || '', tx, by, { size: tz, weight: 700 });
    } else {
      const iw = w - pad * 2; let yy = y + pad;
      fillRR(x + pad, yy, bz * 2.6, bz * 1.5, bz * .4, rgba(col, .16));
      txt(badge, x + pad + bz * 1.3, yy + bz * .75, { size: bz * .85, fam: 'mono', weight: 600, color: col, align: 'center' });
      yy += bz * 2.4;
      const tz = fit(it.title || '', iw, fz('h3'), 700, 'sans', 2);
      yy = txt(it.title || '', x + pad, yy, { size: tz, weight: 700, base: 'top', maxW: iw, lh: 1.2 }).bottom;
      if (it.desc) {
        const dz = fz('body') * pick(.9, .88), room = Math.max(1, Math.floor((y + h - pad - yy - dz * .5) / (dz * 1.35)));
        txt(clampLines(it.desc, iw, dz, Math.min(room, 4)), x + pad, yy + dz * .5, { size: dz, weight: 500, color: STYLE.c.mute, base: 'top', lh: 1.35 });
      }
    }
    ctx.restore();
  });
}

/* ---------- 節點共用（L_steps、L_timeline） ---------- */
function _nodes(t, T, pulse, items, top, kind) {
  const n = items.length; if (!n) return;
  const g = _gap(T, n, .3, BEAT * 2.5, BEAT * 2), st0 = .3, R = MIN * pick(.04, .052, .045);
  const pts = items.map((_, i) => PORT
    ? { x: SAFE.x + R, y: lerp(top + R * 1.4, SAFE.b - R * 1.6, n === 1 ? .5 : i / (n - 1)) }
    : { x: lerp(SAFE.x + SAFE.w / n / 2, SAFE.r - SAFE.w / n / 2, n === 1 ? .5 : i / (n - 1)), y: lerp(top, SAFE.b, kind === 'timeline' ? .5 : .38) });
  const pr = clamp((t - st0) / (g * Math.max(1, n - 1)));
  line(pts[0].x, pts[0].y, pts[n - 1].x, pts[n - 1].y, STYLE.c.cardLine, 2);
  line(pts[0].x, pts[0].y, pts[n - 1].x, pts[n - 1].y, STYLE.c.a1, 3, E.io(pr));
  items.forEach((it, i) => {
    const at = st0 + i * g, on = tw(t, at, .45, 'back'), P = pts[i], col = accent(i);
    const cur = t >= at && (i === n - 1 || t < at + g);
    if (cur) glow(P.x, P.y, R * 3, col, .45 + pulse * .35);
    circle(P.x, P.y, R, STYLE.c.bg);
    ring(P.x, P.y, R, on > 0 ? col : STYLE.c.cardLine, Math.max(2, R * .09), on > 0 ? on : 1);
    if (kind === 'timeline') circle(P.x, P.y, R * .32 * clamp(on), col);
    else txtB(String(i + 1), P.x, P.y, { size: R * .8, fam: 'mono', weight: 600, align: 'center', color: on > 0 ? STYLE.c.fg : STYLE.c.mute });
    const la = clamp(on), tz = fz('h3'), dz = fz('body') * .82;
    if (PORT) {
      // 直式：由上而下堆疊（base: 'top'），每段接在上一段的實際底部，整組以節點為中心
      const tx = P.x + R * 1.9, mw = SAFE.r - tx, blocks = [];
      if (it.when) blocks.push([it.when, { size: fz('cap'), fam: 'mono', weight: 600, color: col }]);
      blocks.push([it.title || '', { size: fit(it.title || '', mw, tz, 700), weight: 700 }]);
      if (it.desc) blocks.push([clampLines(it.desc, mw, dz, 1), { size: dz, weight: 500, color: STYLE.c.mute }]);
      const gap = o => o.size * .18, total = blocks.reduce((h, [str, o]) => h + measure(str, o).h + gap(o), 0) - gap(blocks.at(-1)[1]);
      let yy = P.y - total / 2;
      blocks.forEach(([str, o]) => { const m = txt(str, tx, yy, { ...o, base: 'top', alpha: la, maxW: mw }); yy = m.bottom + gap(o); });
    } else {
      const cw = SAFE.w / n * .92, up = kind === 'timeline' && i % 2 === 1;
      let yy = up ? P.y - R * 2 : P.y + R * 2;
      const base = up ? 'bottom' : 'top';
      const blocks = [];
      if (it.when) blocks.push([it.when, { size: fit(it.when, cw, fz('cap'), 600, 'mono'), fam: 'mono', weight: 600, color: col }]);
      blocks.push([it.title || '', { size: fit(it.title || '', cw, tz, 700), weight: 700 }]);
      if (it.desc) blocks.push([clampLines(it.desc, cw, dz * .92, 2), { size: dz * .92, weight: 500, color: STYLE.c.mute, lh: 1.3 }]);
      (up ? blocks.reverse() : blocks).forEach(([str, o]) => {
        const m = txt(str, P.x, yy, { ...o, align: 'center', base, alpha: la });
        yy = up ? m.top - o.size * .25 : m.bottom + o.size * .25;
      });
    }
  });
}
/* ---------- L_steps：流程步驟 ----------
 * data: { title?, sub?, steps: [{ title, desc? }] }（2–6 步） */
function L_steps(t, T, pulse, s) { const d = _D(s); _nodes(t, T, pulse, _n(d.steps, 6), L_head(t, d.title, d.sub), 'steps'); }
/* ---------- L_timeline：時間軸／大事記 ----------
 * data: { title?, sub?, events: [{ when, title, desc? }] }（2–6 個） */
function L_timeline(t, T, pulse, s) { const d = _D(s); _nodes(t, T, pulse, _n(d.events, 6), L_head(t, d.title, d.sub), 'timeline'); }

/* ---------- L_numbers：1–4 個關鍵數字 ----------
 * data: { title?, items: [{ value: 1200 | "98%" | "NT$ 3.2億", label, note? }] } */
function L_numbers(t, T, pulse, s) {
  const d = _D(s), items = _n(d.items, 4), n = items.length; if (!n) return;
  const top = L_head(t, d.title, null), g = _gap(T, n, -.1, BEAT * 3, BEAT * 1.5);
  const ns0 = n === 1 ? fz(PORT ? .3 : .34) : fz(PORT ? (n > 3 ? .15 : .2) : (n > 3 ? .17 : .22));
  ctx.save(); camPush(1.03 - t * .008);
  items.forEach((it, i) => {
    const at = -.1 + i * g, p = tw(t, at, .8, 'expo');
    const cx = PORT ? W / 2 : lerp(SAFE.x, SAFE.r, (i + .5) / n);
    const cy = PORT ? lerp(top, SAFE.b, (i + .42) / n) : lerp(top, SAFE.b, .44);
    const full = _fmtNum(1, it.value), cw = PORT ? SAFE.w : SAFE.w / n * .9;
    const ns = fit(full, cw, ns0, 600, 'mono');
    const hit = t > at + .7 ? Math.exp(-(t - at - .7) * 6) : 0;
    ctx.save(); ctx.globalAlpha = clamp(p); ctx.translate(cx, cy); ctx.scale(1 + hit * .06, 1 + hit * .06); ctx.translate(-cx, -cy);
    txtB(_fmtNum(p, it.value), cx, cy, { size: ns, fam: 'mono', weight: 600, align: 'center', gradient: [accent(i), accent(i + 1)] });
    ctx.restore();
    const lb = txt(it.label || '', cx, cy + ns * .72, { size: fit(it.label || '', cw, fz('h3'), 700, 'sans', 2), weight: 700, align: 'center', base: 'top', alpha: clamp(p), maxW: cw });
    if (it.note) txt(it.note, cx, lb.bottom + fz('cap') * .4, { size: fz('cap'), color: STYLE.c.mute, align: 'center', base: 'top', alpha: clamp(p), maxW: cw });
    if (i < n - 1) {
      const la = tw(t, at + .3, .5) * .7;
      if (PORT) line(W * .38, lerp(top, SAFE.b, (i + 1) / n) - fz('cap'), W * .62, lerp(top, SAFE.b, (i + 1) / n) - fz('cap'), STYLE.c.cardLine, 1, la);
      else { const lx = lerp(SAFE.x, SAFE.r, (i + 1) / n); line(lx, cy - ns * .5, lx, cy + ns * .9, STYLE.c.cardLine, 1, la); }
    }
  });
  ctx.restore();
}

/* ---------- L_bars：橫條圖 ----------
 * data: { title?, sub?, unit?, hi?: 索引, items: [{ label, value }] }（2–8 列） */
function L_bars(t, T, pulse, s) {
  const d = _D(s), items = _n(d.items, 8), n = items.length; if (!n) return;
  const top = L_head(t, d.title, d.sub), mx = Math.max(...items.map(x => +x.value || 0)) || 1;
  const rowH = Math.min((SAFE.b - top) / n, MIN * pick(.11, .2)), y0 = top + (SAFE.b - top - rowH * n) / 2;
  const lz = fz('body') * pick(.9, 1);
  let lw = 0; setFont(lz, 600); items.forEach(it => lw = Math.max(lw, ctx.measureText(it.label).width));
  lw = PORT ? 0 : Math.min(lw + lz, SAFE.w * .3);
  const bx = SAFE.x + lw, bwMax = SAFE.w - lw - fz('body') * 4.5;
  const g = _gap(T, n, .1, BEAT * 3, BEAT * .5);
  items.forEach((it, i) => {
    const p = tw(t, .1 + i * g, .9, 'expo'), y = y0 + rowH * i, isHi = d.hi === i || (d.hi === undefined && +it.value === mx);
    const col = isHi ? STYLE.c.a1 : rgba(STYLE.c.a2, .7), bh = rowH * pick(.5, .4);
    const by = PORT ? y + rowH * .62 : y + rowH / 2;
    txt(it.label, PORT ? SAFE.x : bx - lz * .8, PORT ? y + rowH * .26 : by, { size: lz, weight: 600, align: PORT ? 'left' : 'right', alpha: tw(t, .1 + i * g - .2, .4), maxW: PORT ? SAFE.w : lw - lz });
    fillRR(bx, by - bh / 2, bwMax, bh, bh * .3, rgba(STYLE.c.fg, .05));
    const bw = Math.max(bh * .6, bwMax * (+it.value || 0) / mx * p);
    if (isHi) glow(bx + bw, by, bh * 2.2, STYLE.c.a1, .35 * p + pulse * .15);
    fillRR(bx, by - bh / 2, bw, bh, bh * .3, col);
    txt(_fmtNum(p, it.value) + (d.unit || ''), bx + bw + lz * .5, by, { size: lz, fam: 'mono', weight: 600, color: isHi ? STYLE.c.a1 : STYLE.c.fg, alpha: clamp(p * 3) });
  });
}

/* ---------- L_line：折線趨勢 ----------
 * data: { title?, sub?, labels: [..], series: [{ name?, values: [..] }]（1–2 條）, unit? } 或 { values: [..] } */
function L_line(t, T, pulse, s) {
  const d = _D(s), series = _n(d.series || [{ values: d.values || [] }], 2), labels = d.labels || [];
  const n = Math.max(...series.map(x => x.values.length)); if (n < 2) return;
  const top = L_head(t, d.title, d.sub), lz = fz('cap');
  const cx0 = SAFE.x + lz * 3.2, cx1 = SAFE.r - lz * 4, cy0 = top + lz * 2.6, cy1 = SAFE.b - lz * 2.4;
  const all = series.flatMap(x => x.values), rawHi = Math.max(...all), rawLo = Math.min(0, ...all);
  const rough = ((rawHi - rawLo) || 1) / 4, mag = Math.pow(10, Math.floor(Math.log10(rough)));
  const stepV = [1, 2, 2.5, 5, 10].map(k => k * mag).find(v => v >= rough), lo = Math.floor(rawLo / stepV) * stepV;
  const hi = Math.ceil(rawHi / stepV) * stepV, span = (hi - lo) || 1, ticks = Math.round(span / stepV);
  const X = i => lerp(cx0, cx1, i / (n - 1)), Y = v => lerp(cy1, cy0, (v - lo) / span);
  const a = tw(t, -.2, .5);
  for (let k = 0; k <= ticks; k++) {
    const v = lo + stepV * k, y = Y(v);
    line(cx0, y, cx1, y, STYLE.c.line, 1, a);
    txt(_fmtNum(1, +v.toFixed(stepV < 1 ? 1 : 0)), cx0 - lz * .6, y, { size: lz * .9, fam: 'mono', color: STYLE.c.mute, align: 'right', alpha: a });
  }
  const step = Math.ceil(n / (PORT ? 4 : 8));
  labels.forEach((lb, i) => { if (i % step === 0 || i === n - 1) txt(lb, X(i), cy1 + lz * 1.2, { size: lz * .9, color: STYLE.c.mute, align: 'center', alpha: a }); });
  const p = tw(t, .3, Math.min(T * .55, BEAT * 6), 'io');
  series.forEach((se, si) => {
    const col = si ? STYLE.c.a2 : STYLE.c.a1, vs = se.values, k = p * (vs.length - 1), kk = Math.floor(k);
    ctx.save();
    const gr = ctx.createLinearGradient(0, cy0, 0, cy1); gr.addColorStop(0, rgba(col, si ? 0 : .22)); gr.addColorStop(1, rgba(col, 0));
    ctx.beginPath(); ctx.moveTo(X(0), Y(vs[0]));
    for (let i = 1; i <= kk; i++) ctx.lineTo(X(i), Y(vs[i]));
    const hx = kk < vs.length - 1 ? lerp(X(kk), X(kk + 1), k - kk) : X(kk), hy = kk < vs.length - 1 ? lerp(Y(vs[kk]), Y(vs[kk + 1]), k - kk) : Y(vs[kk]);
    ctx.lineTo(hx, hy); ctx.strokeStyle = col; ctx.lineWidth = MIN * .007; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke();
    ctx.lineTo(hx, cy1); ctx.lineTo(X(0), cy1); ctx.closePath(); ctx.fillStyle = gr; ctx.fill(); ctx.restore();
    if (p > 0) { glow(hx, hy, MIN * .05, col, .6 + pulse * .3); circle(hx, hy, MIN * .009, col); }
    const vNow = kk < vs.length - 1 ? lerp(vs[kk], vs[kk + 1], k - kk) : vs[kk];
    if (p > 0) txt(_fmtNum(1, Math.round(vNow * 10 ** ((_num(vs[vs.length - 1]) || {}).dec || 0)) / 10 ** ((_num(vs[vs.length - 1]) || {}).dec || 0)) + (d.unit || ''),
      hx + lz * .8, hy - lz * 1.1, { size: fz('body'), fam: 'mono', weight: 600, color: col });
    if (se.name) { const lx = cx0 + lz + si * SAFE.w * pick(.16, .3); fillRR(lx, cy0 - lz * 1.35, lz * 1.4, lz * .3, lz * .15, col);
      txt(se.name, lx + lz * 1.8, cy0 - lz * 1.2, { size: lz, weight: 600, color: col, alpha: a }); }
  });
}

/* ---------- L_compare：對比（Before / After、舊做法 / 新做法） ----------
 * data: { title?, left: { title, items: [..] }, right: { title, items: [..] } } */
function L_compare(t, T, pulse, s) {
  const d = _D(s), L = d.left || { items: [] }, R = d.right || { items: [] };
  const top = L_head(t, d.title, null), gap = MIN * .03, rAt = Math.max(BEAT * 2, Math.floor(T * .42 / BEAT) * BEAT);
  const boxes = PORT
    ? [{ x: SAFE.x, y: top, w: SAFE.w, h: (SAFE.b - top - gap) / 2 }, { x: SAFE.x, y: top + (SAFE.b - top + gap) / 2, w: SAFE.w, h: (SAFE.b - top - gap) / 2 }]
    : [{ x: SAFE.x, y: top, w: (SAFE.w - gap) / 2, h: SAFE.b - top }, { x: SAFE.x + (SAFE.w + gap) / 2, y: top, w: (SAFE.w - gap) / 2, h: SAFE.b - top }];
  [[L, 0, 0], [R, 1, rAt]].forEach(([side, k, at]) => {
    const b = boxes[k], p = tw(t, at - .15, .6, 'back'), dim = k === 0 ? 1 - tw(t, rAt, .5) * .3 : 1;
    const col = k ? STYLE.c.a1 : STYLE.c.mute, pad = Math.min(b.w, b.h) * .09;
    ctx.save(); ctx.globalAlpha = clamp(p) * dim; ctx.translate(PORT ? 0 : (1 - p) * (k ? 40 : -40), PORT ? (1 - p) * 40 : 0);
    if (k) glow(b.x + b.w / 2, b.y + b.h / 2, Math.max(b.w, b.h) * .55, STYLE.c.a1, .18 + pulse * .12);
    card(b.x, b.y, b.w, b.h, { stroke: k ? rgba(STYLE.c.a1, .8) : undefined });
    const hz = fit(side.title || '', b.w - pad * 2, fz('h3'), 800, 'display');
    let yy = txt(side.title || '', b.x + pad, b.y + pad, { size: hz, weight: 800, fam: 'display', color: k ? STYLE.c.a1 : STYLE.c.fg, base: 'top' }).bottom + hz * .45;
    const its = _n(side.items, 5), iz = fz('body') * pick(.9, .92), room = (b.y + b.h - pad - yy) / Math.max(1, its.length);
    its.forEach((it, i) => {
      const ip = tw(t, at + .2 + i * BEAT * .5, .4), cy = yy + Math.min(room, iz * 2.4) * (i + .5), r = iz * .55;
      if (k) _check(b.x + pad + r, cy, r, STYLE.c.a1, ip); else _cross(b.x + pad + r, cy, r * .9, STYLE.c.mute);
      txt(clampLines(it, b.w - pad * 2 - r * 3.2, iz, 1), b.x + pad + r * 3, cy, { size: iz, weight: 500, color: k ? STYLE.c.fg : STYLE.c.mute, alpha: clamp(ip * 2) });
    });
    ctx.restore();
  });
  if (!PORT) { const ap = tw(t, rAt - .3, .4, 'back'); circle(W / 2, (top + SAFE.b) / 2, gap * .9 * ap, STYLE.c.a1);
    txtB('→', W / 2, (top + SAFE.b) / 2, { size: gap * 1.1, weight: 800, align: 'center', color: STYLE.c.bg, alpha: clamp(ap) }); }
}

/* ---------- L_list：條列重點（逐拍出現） ----------
 * data: { title?, sub?, items: [..]（2–6 條） } */
function L_list(t, T, pulse, s) {
  const d = _D(s), items = _n(d.items, 6), n = items.length; if (!n) return;
  const top = L_head(t, d.title, d.sub, { align: 'left' }), g = _gap(T, n, 0, BEAT * 2.5, BEAT);
  const iz = fit(items.reduce((a, b) => (b.length > a.length ? b : a), ''), SAFE.w * .88, fz(n <= 3 ? 'h2' : 'h3'), 700, 'sans', 2, .6);
  const rowH = Math.min((SAFE.b - top) / n, iz * 2.9), ly0 = top + ((SAFE.b - top) - rowH * n) * pick(.35, .4);
  items.forEach((it, i) => {
    const at = i * g, p = tw(t, at, .5, 'out'), y = ly0 + rowH * (i + .5), col = accent(i);
    const cur = t >= at && (i === n - 1 || t < at + g);
    ctx.save(); ctx.globalAlpha = clamp(p); ctx.translate((1 - p) * MIN * .05, 0);
    fillRR(SAFE.x, y - iz * .7, MIN * .008, iz * 1.4, MIN * .004, col);
    if (cur) glow(SAFE.x, y, iz * 2, col, .3 + pulse * .3);
    txt(it, SAFE.x + MIN * .035, y, { size: iz, weight: 700, maxW: SAFE.w - MIN * .035, lh: 1.2 });
    ctx.restore();
  });
}

/* ---------- L_kinetic：逐拍大字（節奏型、痛點、口號） ----------
 * data: { words: [..], beats?: 每個字詞佔幾拍（預設自動平均）, invert?: true 交替反白 } */
function L_kinetic(t, T, pulse, s) {
  const d = _D(s), words = d.words || [], n = words.length; if (!n) return;
  const per = d.beats ? d.beats * BEAT : Math.max(BEAT, Math.floor(T / n / BEAT) * BEAT);
  const i = Math.min(n - 1, Math.floor(Math.max(0, t) / per)), lt = t - i * per, w = words[i];
  const size = fit(w, SAFE.w, fz('hero') * 1.15, 900, 'display', 2, .45);
  const p = tw(lt, 0, .28, 'expo'), sc = lerp(1.3, 1, p) * (1 + pulse * .015);
  const inv = d.invert !== false && i % 2 === 1, m = measure(w, { size, weight: 900, fam: 'display', maxW: SAFE.w, lh: 1.1 });
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(sc, sc); ctx.rotate((i % 2 ? -1 : 1) * .012 * (1 - p)); ctx.translate(-W / 2, -H / 2);
  if (inv) fillRR(W / 2 - m.w / 2 - size * .35, H / 2 - m.h / 2 - size * .18, m.w + size * .7, m.h + size * .36, size * .12, rgba(accent(i), .95 * p));
  txtB(w, W / 2, H / 2, { size, weight: 900, fam: 'display', align: 'center', maxW: SAFE.w, lh: 1.1, alpha: p,
    color: inv ? STYLE.c.bg : (i % 3 === 2 ? accent(i) : STYLE.c.fg) });
  ctx.restore();
  for (let k = 0; k < n; k++) circle(W / 2 + (k - (n - 1) / 2) * MIN * .03, SAFE.b, MIN * .006, k === i ? STYLE.c.a1 : STYLE.c.cardLine);
}

/* ---------- L_countdown：倒數 ----------
 * data: { from?: 3, then?: "倒數結束後的字", sub? } */
function L_countdown(t, T, pulse, s) {
  const d = _D(s), N = d.from || 3, thenT = d.then ? BEAT * 4 : 0, per = (T - thenT) / N;
  const cx = W / 2, cy = H * .47, R = MIN * pick(.26, .32);
  if (t < T - thenT) {
    const k = Math.min(N - 1, Math.floor(Math.max(0, t) / per)), lt = t - k * per, p = tw(lt, 0, .3, 'expo');
    ring(cx, cy, R, STYLE.c.cardLine, MIN * .01);
    ring(cx, cy, R, accent(k), MIN * .012, lt / per);
    glow(cx, cy, R * 1.6, accent(k), .25 + pulse * .25);
    txtB(String(N - k), cx, cy, { size: R * 1.25 * lerp(1.4, 1, p), fam: 'mono', weight: 600, align: 'center', alpha: p, color: STYLE.c.fg });
  } else {
    const lt = t - (T - thenT), p = tw(lt, 0, .5, 'expo');
    const size = fit(d.then, SAFE.w, fz('hero'), 900, 'display', 2);
    glow(cx, cy, R * 2 * p, STYLE.c.a1, .35);
    txtB(d.then, cx, cy, { size: size * lerp(1.3, 1, p), weight: 900, fam: 'display', align: 'center', alpha: p, maxW: SAFE.w, gradient: [STYLE.c.a1, STYLE.c.a2, STYLE.c.a3] });
    if (d.sub) txt(d.sub, cx, cy + size * 1.1, { size: fz('body'), color: STYLE.c.mute, align: 'center', alpha: tw(lt, BEAT, .5), maxW: SAFE.w });
  }
}

/* ---------- L_logo：收尾字標 ----------
 * data: { name, tagline?, mark?: 'ring' | 'dot' | 'bars' | 'none' } */
function L_logo(t, T, pulse, s) {
  const d = _D(s), mark = d.mark || 'ring', cx = W / 2, cy = H * pick(.46, .44), R = MIN * pick(.07, .085);
  const lp = tw(t, .05, .8, 'io'), my = cy - R * 1.7;
  if (mark !== 'none') {
    glow(cx, my, R * 4.5 * (.8 + lp * .4), STYLE.c.a2, .22 + pulse * .1);
    ctx.save(); ctx.translate(cx, my);
    if (mark === 'ring') { ctx.rotate(t * .4); ring(0, 0, R, STYLE.c.a1, R * .16, lp); ring(0, 0, R * .58, STYLE.c.a3, R * .12, tw(t, .3, .7, 'io'), Math.PI / 2); }
    else if (mark === 'dot') { circle(0, 0, R * .75 * E.back(lp), STYLE.c.a1); circle(R * .9, -R * .6, R * .22 * tw(t, .4, .5, 'back'), STYLE.c.a3); }
    else [0, 1, 2].forEach(k => { const h = R * (1 + k * .45) * tw(t, .1 + k * .15, .5, 'back'); fillRR(-R * .9 + k * R * .66, R * .7 - h, R * .44, h, R * .1, accent(k)); });
    ctx.restore();
  }
  const word = d.name || '', wp = tw(t, BEAT * 2, .9);
  const size = fit(word, SAFE.w, fz('h1'), 800, 'display');
  txtB(typeOn(word, wp), cx, cy + R * .45, { size, weight: 800, fam: 'display', align: 'center', track: lerp(.25, .02, wp) });
  const tp = tw(t, BEAT * 4, .6);
  if (d.tagline) txt(d.tagline, cx, cy + R * .45 + size * 1.05 + (1 - tp) * 10, { size: fz('h3'), color: STYLE.c.mute, align: 'center', alpha: tp, maxW: SAFE.w });
}

/* ---------- L_cta：行動呼籲 ----------
 * data: { title, action, note? }（note 放網址或聯絡方式；email 請見 SKILL.md 陷阱說明） */
function L_cta(t, T, pulse, s) {
  const d = _D(s), cx = W / 2, cy = H * pick(.42, .4);
  const size = fit(d.title || '', SAFE.w, fz('h1'), 800, 'display', 2);
  const tm = txt(d.title || '', cx, cy, { size, weight: 800, fam: 'display', align: 'center', maxW: SAFE.w, alpha: tw(t, -.2, .5), lh: 1.15 });
  const bp = tw(t, BEAT * 2, .6, 'back'), az = fz('h3'), am = measure(d.action || '', { size: az, weight: 700 });
  const bw = am.w + az * 2.4, bh = az * 2.1, by = tm.bottom + size * .55, sc = (1 + pulse * .04 * clamp(bp)) * clamp(bp);
  ctx.save(); ctx.translate(cx, by + bh / 2); ctx.scale(sc, sc);
  glow(0, 0, bw * .7, STYLE.c.a1, .35 + pulse * .25);
  fillRR(-bw / 2, -bh / 2, bw, bh, bh / 2, STYLE.c.a1);
  txt((d.action || '') + '  →', 0, 0, { size: az, weight: 700, align: 'center', color: STYLE.c.bg });
  ctx.restore();
  if (d.note) txt(d.note, cx, by + bh + az * 1.4, { size: fz('body'), fam: 'mono', weight: 500, color: STYLE.c.mute, align: 'center', alpha: tw(t, BEAT * 3, .5), maxW: SAFE.w });
}
