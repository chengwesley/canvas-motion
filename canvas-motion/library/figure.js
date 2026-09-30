/* figure.js：程序化人物（骨架＋姿勢＋表情＋三種精細度＋類型畫法）。用法與表演原則見 references/character.md。
 * 全部是純函式：姿勢是一組關節角度，畫一次 = figDraw(角色, 腳底 x, 地面 y, 姿勢, 選項)。
 * 角度（弧度）：肢體 0 = 朝下，正值 = 往角色面向的方向擺；軀幹 0 = 朝上，正值 = 前傾。
 * 這是「能演戲的人偶」，不是擬真人物：需要特定真人或原畫等級的臉，請使用者提供有授權的圖。 */

/* ---------- 比例（頭身） ----------
 * 各段佔身高 H 的比例（寫實取自 Drillis & Contini 分段常數，其他畫風依頭身推算；各段相加 ≈ 1）：
 * head 頭、neck 頸、torso 肩線→髖關節、upper/fore/hand 上臂／前臂／手、thigh/shin 大腿／小腿、ankle 踝高、foot 腳長、
 * sh／hip 肩寬／髖寬、limb 肢體粗細倍率、eye 眼睛高度（頭高比例）、waist 腰寬（髖寬比例，越小越倒三角） */
const FIG_PROPS = {
  chibi:   { head: .40, neck: .01, torso: .25, upper: .12, fore: .10, hand: .06, thigh: .15, shin: .17, ankle: .02, foot: .10, sh: .26, hip: .22, limb: 1.6, eye: .26, waist: .95 },
  cartoon: { head: .20, neck: .02, torso: .28, upper: .16, fore: .14, hand: .12, thigh: .22, shin: .24, ankle: .04, foot: .16, sh: .30, hip: .26, limb: 1.3, eye: .2, waist: .9 },
  teen:    { head: .154, neck: .045, torso: .25, upper: .17, fore: .14, hand: .085, thigh: .25, shin: .26, ankle: .04, foot: .12, sh: .22, hip: .18, limb: .9, eye: .18, waist: .85 },
  anime:   { head: .133, neck: .05, torso: .26, upper: .18, fore: .15, hand: .09, thigh: .26, shin: .26, ankle: .04, foot: .13, sh: .24, hip: .18, limb: .95, eye: .16, waist: .8 },
  real:    { head: .130, neck: .052, torso: .288, upper: .186, fore: .146, hand: .108, thigh: .245, shin: .246, ankle: .039, foot: .152, sh: .259, hip: .191, limb: 1, eye: .09, waist: .8 },
  hero:    { head: .118, neck: .045, torso: .27, upper: .19, fore: .15, hand: .10, thigh: .26, shin: .26, ankle: .04, foot: .14, sh: .33, hip: .19, limb: 1.4, eye: .085, waist: .62 },
  flat:    { head: .15, neck: .035, torso: .27, upper: .17, fore: .15, hand: .07, thigh: .25, shin: .27, ankle: .03, foot: .1, sh: .25, hip: .17, limb: 1.1, eye: .12, waist: .9 },
  cute:    { head: .26, neck: .02, torso: .25, upper: .14, fore: .12, hand: .06, thigh: .2, shin: .22, ankle: .03, foot: .1, sh: .22, hip: .2, limb: 1.5, eye: .2, waist: 1 },
  hk:      { head: .111, neck: .04, torso: .28, upper: .19, fore: .15, hand: .10, thigh: .26, shin: .27, ankle: .04, foot: .14, sh: .36, hip: .20, limb: 1.45, eye: .09, waist: .6 },
};

/** 建立角色。o: { props:'anime', height, detail:'full'|'mannequin'|'stick', pal:{skin,hair,top,bottom,shoe,accent,line},
 *  hair:'short'|'spiky'|'long'|'bun'|'none', outfit:{ sleeve:'long'|'short'|'none', legs:'pants'|'shorts'|'skirt', cape, sash }, render:'flat' } */
function figMake(o = {}) {
  const P = FIG_PROPS[o.props || 'anime'] || FIG_PROPS.anime, Hf = o.height || MIN * .5, h = Hf * P.head;
  const pal = { skin: '#f3c9a5', hair: '#2a2230', eye: '#3b2a22', top: STYLE.c.a1, bottom: '#2c3550', shoe: '#1c1c22', accent: STYLE.c.a2, line: '#141414', ...(o.pal || {}) };
  return { P, Hf, h, headR: h / 2, neck: P.neck * Hf, torso: P.torso * Hf, thigh: P.thigh * Hf, shin: (P.shin + P.ankle) * Hf, foot: P.foot * Hf * .8,
    upper: P.upper * Hf, fore: P.fore * Hf, hand: P.hand * Hf, shW: P.sh * Hf, hipW: P.hip * Hf, limbR: Hf * .036 * P.limb,
    pal, detail: o.detail || 'full', hair: o.hair || 'short', outfit: { sleeve: 'short', legs: 'pants', ...(o.outfit || {}) }, render: o.render || 'flat' };
}

/* ---------- 姿勢 ----------
 * { lean, spine, neck, head, shL, elL, shR, elR, hipL, knL, hipR, knR, ftL, ftR, bob, twist }
 * L = 靠鏡頭遠的那側（側面時被身體擋住）。bob = 骨盆上下位移（身高比例），twist = 肩膀前後扭轉（-1..1） */
const FIG_ZERO = { lean: 0, spine: 0, neck: 0, head: 0, shL: .12, elL: .32, shR: -.06, elR: .28, hipL: 0, knL: .04, hipR: 0, knR: .04, ftL: 0, ftR: 0, bob: 0, twist: 0 };
const D = Math.PI / 180;
const figPose = {
  zero: () => ({ ...FIG_ZERO }),
  mix(a, b, p) { const o = {}; for (const k in FIG_ZERO) o[k] = lerp(a[k] ?? FIG_ZERO[k], b[k] ?? FIG_ZERO[k], p); return o; },
  add(a, b, k = 1) { const o = { ...a }; for (const key in b) o[key] = (a[key] ?? 0) + b[key] * k; return o; },
  /** 站姿呼吸：重心微移、手臂輕擺 */
  idle(t) { const b = Math.sin(t * 2.1); return { ...FIG_ZERO, spine: b * .02, head: Math.sin(t * .9) * .04, shL: .1 + b * .03, shR: -.06 - b * .03, bob: b * .004 }; },
  /** 走路：phase 0–1 為一個完整週期（兩步），0 = 近側（R）腳跟觸地。k = 幅度（.6 散步、1 正常、1.3 大步） */
  walk(ph, k = 1) { return _figCycle(ph, k, FIG_WALK, { lean: 4, arm: .8, elbow: [12, 38], twist: .25, lag: .04 }); },
  /** 跑步：步幅大、有騰空、身體前傾 12°、手肘約 90° */
  run(ph, k = 1) { return _figCycle(ph, k, FIG_RUN, { lean: 14, arm: 1.4, elbow: [85, 100], twist: .45, lag: .03, head: -8 }); },
  /** 單張關鍵姿勢 */
  key(name) {
    const K = {
      stand: {},
      crouch: { lean: 18 * D, spine: 10 * D, hipL: 75 * D, knL: 120 * D, hipR: 70 * D, knR: 115 * D, ftL: -30 * D, ftR: -28 * D, shL: -30 * D, elL: 40 * D, shR: -40 * D, elR: 40 * D, bob: -.16 },
      leap: { lean: 10 * D, spine: -10 * D, head: -10 * D, hipR: 60 * D, knR: 80 * D, hipL: -35 * D, knL: 30 * D, shL: 160 * D, elL: 10 * D, shR: 150 * D, elR: 10 * D, bob: 0 },
      land: { lean: 12 * D, spine: 14 * D, hipL: 55 * D, knL: 95 * D, hipR: 50 * D, knR: 90 * D, ftL: -22 * D, ftR: -20 * D, shL: 60 * D, elL: 30 * D, shR: -50 * D, elR: 30 * D, bob: -.12 },
      cheer: { spine: -8 * D, head: -14 * D, shL: 165 * D, elL: 10 * D, shR: 170 * D, elR: 5 * D, hipL: -4 * D, hipR: 6 * D },
      point: { lean: 4 * D, shR: 85 * D, elR: 4 * D, shL: -10 * D, elL: 30 * D, head: 4 * D, hipR: 8 * D, hipL: -6 * D },
      think: { spine: 4 * D, head: 12 * D, neck: 6 * D, shR: 40 * D, elR: 140 * D, shL: 20 * D, elL: 110 * D },
      sit: { lean: -4 * D, hipL: 90 * D, knL: 90 * D, hipR: 88 * D, knR: 92 * D, shL: 25 * D, elL: 40 * D, shR: 20 * D, elR: 45 * D, bob: -.2 },
      // 武術：馬步、弓步、直拳、蓄勁（港漫、功夫題材）
      horse: { spine: -2 * D, hipL: -32 * D, knL: 60 * D, hipR: 32 * D, knR: 60 * D, ftL: 20 * D, ftR: -20 * D, shL: 20 * D, elL: 120 * D, shR: 20 * D, elR: 120 * D, bob: -.09, wide: 1 },
      bow: { lean: 8 * D, hipR: 55 * D, knR: 65 * D, hipL: -38 * D, knL: 6 * D, ftL: 18 * D, shR: 80 * D, elR: 6 * D, shL: -20 * D, elL: 130 * D, bob: -.07, twist: .5 },
      punch: { lean: 14 * D, spine: 6 * D, hipR: 50 * D, knR: 55 * D, hipL: -35 * D, knL: 8 * D, shR: 88 * D, elR: 0, shL: -35 * D, elL: 135 * D, bob: -.06, twist: .8 },
      chamber: { lean: -6 * D, spine: -6 * D, hipR: 20 * D, knR: 30 * D, hipL: -10 * D, knL: 20 * D, shR: -40 * D, elR: 140 * D, shL: 40 * D, elL: 60 * D, bob: -.03, twist: -.6 },
      kick: { lean: -18 * D, spine: -10 * D, hipR: 95 * D, knR: 5 * D, ftR: 20 * D, hipL: -8 * D, knL: 12 * D, shR: -60 * D, elR: 60 * D, shL: 70 * D, elL: 40 * D, bob: 0 },
      hero: { spine: -6 * D, head: -8 * D, hipL: -12 * D, hipR: 12 * D, knL: 4 * D, knR: 4 * D, shL: 25 * D, elL: 70 * D, shR: -25 * D, elR: 70 * D, handsOnHips: 1 },
      fall: { lean: -35 * D, spine: -20 * D, head: 20 * D, hipR: 40 * D, knR: 60 * D, hipL: 10 * D, knL: 30 * D, shR: 130 * D, elR: 20 * D, shL: 100 * D, elL: 40 * D },
    };
    return { ...FIG_ZERO, ...(K[name] || {}) };
  },
  /** 依時間播放一串關鍵姿勢：keys = [[秒, 姿勢或名稱, 緩動?], …]，姿勢之間用緩動補間（預設 io） */
  seq(t, keys) {
    const k = keys.map(([tt, p, e]) => [tt, typeof p === 'string' ? figPose.key(p) : p, e || 'io']);
    if (t <= k[0][0]) return k[0][1];
    for (let i = 0; i < k.length - 1; i++) if (t < k[i + 1][0]) return figPose.mix(k[i][1], k[i + 1][1], E[k[i + 1][2]](prog(t, k[i][0], k[i + 1][0])));
    return k[k.length - 1][1];
  },
};
/* 單腿關鍵影格：[phase, 髖, 膝, 踝]（度；髖正 = 往前、膝正 = 彎、踝正 = 腳尖翹）。另一腿相位 +.5 */
const FIG_WALK = [[0, 25, 5, 5], [.125, 20, 18, 0], [.25, 0, 5, 5], [.375, -10, 8, -10], [.5, -15, 35, -18], [.625, -5, 55, -10], [.73, 15, 60, 0], [.875, 28, 25, 5]];
const FIG_RUN = [[0, 30, 20, 0], [.08, 22, 42, -5], [.25, -20, 15, -25], [.4, -10, 90, -10], [.55, 20, 125, 0], [.75, 50, 80, 5], [.9, 45, 35, 5]];
function _figKey(tab, ph) {   // periodic Catmull-Rom over the keyframe table
  ph = ((ph % 1) + 1) % 1; const n = tab.length; let i = n - 1; while (i > 0 && tab[i][0] > ph) i--;
  const a = tab[(i - 1 + n) % n], b = tab[i], c = tab[(i + 1) % n], d = tab[(i + 2) % n];
  const t0 = b[0], t1 = i + 1 < n ? c[0] : c[0] + 1, u = (ph - t0) / (t1 - t0);
  return [1, 2, 3].map(j => { const p0 = a[j], p1 = b[j], p2 = c[j], p3 = d[j];
    return .5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u); });
}
function _figCycle(ph, k, tab, o) {
  const R = _figKey(tab, ph), L = _figKey(tab, ph + .5), Ra = _figKey(tab, ph - o.lag), La = _figKey(tab, ph + .5 - o.lag);
  const el = (hip) => (o.elbow[0] + (o.elbow[1] - o.elbow[0]) * clamp(hip / 25 * .5 + .5)) * D;
  return { ...FIG_ZERO, lean: o.lean * D * k, spine: 2 * D, head: (o.head || -2) * D,
    hipR: R[0] * D * k, knR: R[1] * D * k, ftR: R[2] * D, hipL: L[0] * D * k, knL: L[1] * D * k, ftL: L[2] * D,
    // arms swing opposite to the same-side leg, peaking 1–2 frames later (lag)
    shR: -o.arm * Ra[0] * D * k, elR: el(-Ra[0]), shL: -o.arm * La[0] * D * k, elL: el(-La[0]),
    twist: o.twist * k * Math.sin(ph * 2 * Math.PI) };
}
/** 走路／跑步一個週期往前走多遠（像素）：讓腳不滑步。x = figStride(角色, 'walk') × 經過的週期數 */
function figStride(F, kind = 'walk', k = 1) {
  const p = figPose[kind](0, k), J = _figJoints(F, p, 1, 1);
  return Math.abs(J.anR.x - J.anL.x) * 2;   // heel strike: distance between ankles at contact × 2 steps
}

/* ---------- 表情 ----------
 * brow：眉毛角度（正 = 生氣的倒八字）、browY：眉毛高度（正 = 抬高）、eye：眼睛張開 0–1.3、look：瞳孔方向 {x,y}、
 * mouth：'neutral'|'smile'|'grin'|'open'|'o'|'frown'|'grit'、open：嘴張開 0–1 */
const EXPR = {
  neutral:    { brow: 0, browY: 0, eye: 1, mouth: 'neutral', open: 0 },
  happy:      { brow: -.1, browY: .15, eye: .75, mouth: 'smile', open: .35 },
  laugh:      { brow: -.15, browY: .2, eye: .15, mouth: 'grin', open: .9 },
  angry:      { brow: .55, browY: -.25, eye: .85, mouth: 'grit', open: .45 },
  sad:        { brow: -.45, browY: .1, eye: .6, mouth: 'frown', open: .1 },
  surprised:  { brow: -.05, browY: .45, eye: 1.3, mouth: 'o', open: .8 },
  determined: { brow: .35, browY: -.15, eye: .8, mouth: 'frown', open: 0 },
  fear:       { brow: -.4, browY: .35, eye: 1.25, mouth: 'open', open: .5 },
  shout:      { brow: .6, browY: -.2, eye: .95, mouth: 'open', open: 1 },
};
const figExprMix = (a, b, p) => ({ brow: lerp(a.brow, b.brow, p), browY: lerp(a.browY, b.browY, p), eye: lerp(a.eye, b.eye, p),
  mouth: p < .5 ? a.mouth : b.mouth, open: lerp(a.open, b.open, p), look: b.look || a.look });
/** 自動眨眼：每 2.5–4.5 秒眨一次，一次約 .15 秒。回傳眼睛張開的倍數 */
function figBlink(t, seed = 1) {
  const R = rng(seed); let at = R() * 2;
  while (at < t - .6) at += 2 + R() * 4;
  const one = x => x < 0 || x > .25 ? 1 : x < .08 ? 1 - x / .08 : x < .12 ? 0 : (x - .12) / .13;   // close fast, open slower
  return Math.min(one(t - at), R() < .15 ? one(t - at - .3) : 1);
}

/* ---------- 正向運動學 ---------- */
const _v = (a, len, dir, view) => ({ x: Math.sin(a) * len * dir * view, y: Math.cos(a) * len });   // 肢體：0 朝下
function _figJoints(F, p, dir, view) {
  const pel = { x: 0, y: -(F.thigh + F.shin) + (p.bob || 0) * F.Hf }, lean = p.lean || 0;
  const up = a => ({ x: Math.sin(a) * dir * view, y: -Math.cos(a) });                                 // 軀幹：0 朝上
  const ta = lean + (p.spine || 0), tv = up(ta);
  const chest = { x: pel.x + tv.x * F.torso, y: pel.y + tv.y * F.torso };
  const na = ta + (p.neck || 0), nv = up(na), neckTop = { x: chest.x + nv.x * F.neck, y: chest.y + nv.y * F.neck };
  const ha = na + (p.head || 0), hv = up(ha), head = { x: neckTop.x + hv.x * F.headR * .95, y: neckTop.y + hv.y * F.headR * .95 };
  const tw = (p.twist || 0) * view, side = 1 - view * .72, wide = p.wide ? 1.6 : 1;
  const shO = F.shW / 2 * side, hipO = F.hipW / 2 * side * wide;
  // 肩膀扭轉：側面時一肩在前一肩在後（x 位移），正面時左右分開
  const shN = { x: chest.x + (shO + tw * F.shW * .18) * dir, y: chest.y + F.h * .12 }, shF = { x: chest.x - (shO - tw * F.shW * .18) * dir, y: chest.y + F.h * .12 };
  const hpN = { x: pel.x + hipO * dir, y: pel.y }, hpF = { x: pel.x - hipO * dir, y: pel.y };
  const limb = (base, a1, l1, a2, l2, a3, l3, bodyA) => {
    const A1 = bodyA + a1, v1 = _v(A1, l1, dir, view), j1 = { x: base.x + v1.x, y: base.y + v1.y };
    const A2 = A1 + a2, v2 = _v(A2, l2, dir, view), j2 = { x: j1.x + v2.x, y: j1.y + v2.y };
    const A3 = A2 + (a3 || 0), v3 = _v(A3, l3, dir, view), j3 = { x: j2.x + v3.x, y: j2.y + v3.y };
    return [base, j1, j2, j3, A3];
  };
  // 腿：膝蓋往後彎（-kn）；腳掌往前（+90°）
  const legJ = (hp, a, kn, ft) => { const r = limb(hp, a, F.thigh, -kn, F.shin, 0, 0, 0);
    const fa = r[4] + Math.PI / 2 + (ft || 0), fv = _v(fa, F.foot, dir, Math.max(view, .35)); return [r[0], r[1], r[2], { x: r[2].x + fv.x, y: r[2].y + fv.y }]; };
  const armJ = (sh, a, el) => limb(sh, a, F.upper, el, F.fore, el * .15, F.hand * .8, lean * .5);
  const LR = legJ(hpN, p.hipR, p.knR, p.ftR), LL = legJ(hpF, p.hipL, p.knL, p.ftL);
  let AR = armJ(shN, p.shR, p.elR), AL = armJ(shF, p.shL, p.elL);
  if (p.handsOnHips) { const hipN2 = { x: pel.x + hipO * 1.1 * dir, y: pel.y - F.h * .25 }, hipF2 = { x: pel.x - hipO * 1.1 * dir, y: pel.y - F.h * .25 };
    AR = [shN, { x: lerp(shN.x, hipN2.x, .5) + F.h * .55 * dir * (1 - view * .5), y: lerp(shN.y, hipN2.y, .5) }, hipN2, hipN2];
    AL = [shF, { x: lerp(shF.x, hipF2.x, .5) - F.h * .55 * dir * (1 - view * .5), y: lerp(shF.y, hipF2.y, .5) }, hipF2, hipF2]; }
  return { pel, chest, neckTop, head, ha, shN, shF, hpN, hpF, armN: AR, armF: AL, legN: LR, legF: LL, ftR: LR[3], ftL: LL[3], anR: LR[2], anL: LL[2] };
}

/* ---------- 繪製 ---------- */
// 錐形膠囊（兩端圓）：從 a 到 b，半徑 ra → rb
function _capsule(c, a, b, ra, rb, dx = 0, dy = 0, k = 1) {
  const ang = Math.atan2(b.y - a.y, b.x - a.x);
  c.moveTo(a.x + dx + Math.cos(ang + Math.PI / 2) * ra * k, a.y + dy + Math.sin(ang + Math.PI / 2) * ra * k);
  c.arc(a.x + dx, a.y + dy, ra * k, ang + Math.PI / 2, ang - Math.PI / 2);
  c.arc(b.x + dx, b.y + dy, rb * k, ang - Math.PI / 2, ang + Math.PI / 2);
  c.closePath();
}
// 一個部件：path(dx, dy, k) 建立路徑；依 render 做描邊／分色陰影／排線／邊光
function _part(F, path, col, o) {
  const R = o.render, L = o.light, ink = F.pal.line, lw = o.lw;
  if (R !== 'flat-noline' && R !== 'silhouette') { ctx.beginPath(); path(0, 0, 1); ctx.lineWidth = lw * 2; ctx.strokeStyle = ink; ctx.lineJoin = 'round'; ctx.stroke(); }
  ctx.beginPath(); path(0, 0, 1); ctx.fillStyle = R === 'silhouette' ? ink : col; ctx.fill();
  if (R === 'silhouette' || R === 'flat' || R === 'flat-noline') return;
  const sd = o.shade * F.limbR;
  ctx.save(); ctx.beginPath(); path(0, 0, 1); ctx.clip();
  if (R === 'cel' || R === 'anime' || R === 'amcomic') {           // 硬邊陰影：整塊暗色，再蓋上往光源偏移的亮色
    ctx.beginPath(); path(0, 0, 1.05); ctx.fillStyle = R === 'amcomic' ? mixc(col, ink, .62) : mixc(col, o.shadowTint || '#3a2a5a', .38); ctx.fill();
    ctx.beginPath(); path(L.x * sd, L.y * sd, 1); ctx.fillStyle = col; ctx.fill();
    if (R === 'anime') { ctx.beginPath(); path(L.x * sd * 1.9, L.y * sd * 1.9, .55); ctx.fillStyle = rgba('#ffffff', .22); ctx.fill(); }
  } else if (R === 'hkcomic' || R === 'hatch') {                   // 排線陰影＋戲劇邊光（港漫）
    ctx.beginPath(); path(0, 0, 1.05); ctx.fillStyle = mixc(col, ink, .45); ctx.fill();
    ctx.strokeStyle = rgba(ink, .55); ctx.lineWidth = Math.max(.8, lw * .45); ctx.beginPath();
    const b = o.bb, g = Math.max(2.5, lw * 1.6);
    for (let x = b[0] - b[3]; x < b[2]; x += g) { ctx.moveTo(x, b[1]); ctx.lineTo(x + (b[3] - b[1]), b[3]); }
    ctx.stroke();
    ctx.beginPath(); path(L.x * sd, L.y * sd, 1); ctx.fillStyle = col; ctx.fill();
    if (o.rim) { ctx.beginPath(); path(-L.x * sd * 1.25, -L.y * sd * 1.25, 1); ctx.lineWidth = lw * 1.6; ctx.strokeStyle = o.rim; ctx.stroke(); }
  }
  ctx.restore();
}

/** 畫角色：(x, y) 是雙腳之間的地面點。o: { dir: 1 右 / -1 左, view: 0 正面–1 側面, face: EXPR.xxx, t, blink, look:{x,y},
 *   render:'flat'|'cel'|'anime'|'amcomic'|'hkcomic'|'silhouette', light:{x,y}, rim, lw, shade, ground:true, sway:{x,y}（頭髮、披風的慣性，用 vel 算）} */
function figDraw(F, x, y, pose, o = {}) {
  const dir = o.dir ?? 1, view = o.view ?? 1, J = _figJoints(F, pose, dir, view);
  const render = o.render || F.render, lw = o.lw ?? Math.max(1, F.Hf * .006), light = o.light || { x: -.6 * dir, y: -.8 };
  const low = Math.max(J.ftR.y, J.ftL.y, J.anR.y, J.anL.y), gy = o.ground === false ? 0 : -low;   // 最低的腳著地
  const pal = F.pal, far = c => mixc(c, pal.line, view > .5 ? .22 : 0);
  const po = { render, light, lw, shade: o.shade ?? .55, rim: o.rim, shadowTint: o.shadowTint };
  const S = (path, col, bb) => _part(F, path, col, { ...po, bb: bb || [-F.Hf, -F.Hf * 1.2, F.Hf, F.Hf * .1] });
  ctx.save(); ctx.translate(x, y + gy);
  if (o.shadow !== false && o.ground !== false) { ctx.save(); ctx.globalAlpha = .22; ctx.fillStyle = pal.line; ctx.beginPath();
    ctx.ellipse(J.pel.x, -gy, F.hipW * 1.1 + Math.abs(J.ftR.x - J.ftL.x) * .4, F.h * .09, 0, 0, 6.283); ctx.fill(); ctx.restore(); }
  const R = F.limbR, lvl = F.detail;
  if (render === 'illus' && lvl === 'full') { _figIllus(F, J, pose, { ...o, dir, view, light }); ctx.restore(); return { ...J, gy, x, y }; }
  if (lvl === 'stick') {
    ctx.strokeStyle = o.color || pal.line; ctx.lineWidth = Math.max(2, R * .7); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    const pl = pts => { ctx.beginPath(); pts.forEach((q, i) => i ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y)); ctx.stroke(); };
    [J.legF, J.legN, J.armF.slice(0, 4), J.armN.slice(0, 4)].forEach(pl); pl([J.pel, J.chest, J.neckTop]);
    circle(J.head.x, J.head.y, F.headR * .9, o.color || pal.line); ctx.restore(); return J;
  }
  const sway = o.sway || { x: 0, y: 0 };
  const cape = F.outfit.cape, sash = F.outfit.sash;
  // 披風在最後面：頂端接肩膀，下擺跟著慣性往後飄
  if (cape && lvl === 'full') {
    const top = { x: (J.shN.x + J.shF.x) / 2, y: (J.shN.y + J.shF.y) / 2 }, len = F.torso + F.thigh * 1.4;
    const flow = clamp(-sway.x * dir * .004, -1.2, 1.2), fl = t => Math.sin((o.t || 0) * 3 + t * 4) * F.h * .12;
    S((dx, dy, k) => { ctx.moveTo(top.x - F.shW * .45 + dx, top.y + dy); ctx.lineTo(top.x + F.shW * .45 + dx, top.y + dy);
      ctx.quadraticCurveTo(top.x + F.shW * .5 - flow * len * .5 * dir + dx, top.y + len * .6 + dy, top.x + F.shW * .55 - flow * len * dir + fl(1) + dx, top.y + len * (1 - Math.abs(flow) * .35) + dy);
      ctx.lineTo(top.x - F.shW * .55 - flow * len * dir + fl(2) + dx, top.y + len * (1 - Math.abs(flow) * .3) + dy);
      ctx.quadraticCurveTo(top.x - F.shW * .5 - flow * len * .5 * dir + dx, top.y + len * .6 + dy, top.x - F.shW * .45 + dx, top.y + dy); }, typeof cape === 'string' ? cape : pal.accent);
  }
  const sleeve = F.outfit.sleeve, legs = F.outfit.legs, mann = lvl === 'mannequin';
  const skin = mann ? '#d9d2c6' : pal.skin, topC = mann ? '#cfc7ba' : pal.top, botC = mann ? '#c2baad' : pal.bottom, shoe = mann ? '#b3ab9e' : pal.shoe;
  const limbDraw = (j, r0, r1, cUp, cLow, cEnd, endR, farSide, isLeg) => {
    const f = farSide ? far : c => c;
    S((dx, dy, k) => _capsule(ctx, j[0], j[1], r0, (r0 + r1) / 2, dx, dy, k), f(cUp));
    S((dx, dy, k) => _capsule(ctx, j[1], j[2], (r0 + r1) / 2, r1, dx, dy, k), f(cLow));
    if (isLeg) S((dx, dy, k) => _capsule(ctx, j[2], j[3], r1 * 1.05, r1 * .8, dx, dy, k), f(cEnd));
    else S((dx, dy, k) => { ctx.moveTo(j[2].x + dx + endR * k, j[2].y + dy); ctx.arc(j[2].x + dx, j[2].y + dy, endR * k, 0, 6.283);
      _capsule(ctx, j[2], j[3], endR * k, endR * .75 * k, dx, dy); }, f(cEnd));
  };
  const taper = F.P.waist || 1, legR0 = R * 1.3, legR1 = R * .82, armR0 = R * .95, armR1 = R * .7;
  const armCol = s => sleeve === 'long' ? [topC, topC] : sleeve === 'short' ? [topC, skin] : [skin, skin];
  const legCol = legs === 'shorts' ? [botC, skin] : legs === 'skirt' ? [skin, skin] : legs === 'robe' ? [mixc(botC, pal.line, .35), mixc(botC, pal.line, .35)] : [botC, botC];
  // 遠側手腳 → 軀幹 → 近側手腳（側面時才有前後；正面時順序不影響）
  limbDraw(J.armF, armR0, armR1, ...armCol(), skin, R * .72, true, false);
  limbDraw(J.legF, legR0, legR1, ...legCol, shoe, 0, true, true);
  limbDraw(J.legN, legR0, legR1, ...legCol, shoe, 0, false, true);
  // 軀幹：肩寬 → 腰（taper 越小腰越細，英雄體型）→ 髖
  const waist = { x: lerp(J.pel.x, J.chest.x, .35), y: lerp(J.pel.y, J.chest.y, .35) }, sw = F.shW / 2 * (1 - view * .45), ww = F.hipW / 2 * taper * (1 - view * .35), hw = F.hipW / 2 * (1 - view * .3);
  const torsoPath = (dx, dy, k) => { const ang = Math.atan2(J.chest.y - J.pel.y, J.chest.x - J.pel.x) + Math.PI / 2, cx = Math.cos(ang), cy = Math.sin(ang);
    const P = (b, w) => [b.x + cx * w * k + dx, b.y + cy * w * k + dy], M = (b, w) => [b.x - cx * w * k + dx, b.y - cy * w * k + dy];
    const top = { x: J.chest.x, y: J.chest.y - F.h * .05 }, a = P(top, sw), b = P(waist, ww), c = P(J.pel, hw), d = M(J.pel, hw), e = M(waist, ww), f = M(top, sw);
    ctx.moveTo(...a); ctx.quadraticCurveTo(a[0], a[1] + (b[1] - a[1]) * .5, ...b); ctx.lineTo(...c);
    ctx.quadraticCurveTo(J.pel.x + dx, J.pel.y + F.h * .28 * k + dy, ...d); ctx.lineTo(...e); ctx.quadraticCurveTo(f[0], f[1] + (e[1] - f[1]) * .5, ...f);
    ctx.quadraticCurveTo(top.x + dx, top.y - F.h * .12 * k + dy, ...a); };
  const skirtL = legs === 'robe' ? F.thigh * 1.45 : F.thigh * .75;
  if (legs === 'skirt' || legs === 'robe') S((dx, dy, k) => { ctx.moveTo(J.pel.x - hw * 1.05 + dx, J.pel.y - F.h * .2 + dy); ctx.lineTo(J.pel.x + hw * 1.05 + dx, J.pel.y - F.h * .2 + dy);
    ctx.lineTo(J.pel.x + hw * 1.8 + sway.x * -.002 * F.h + dx, J.pel.y + skirtL + dy); ctx.lineTo(J.pel.x - hw * 1.8 + sway.x * -.002 * F.h + dx, J.pel.y + skirtL + dy); ctx.closePath(); }, botC);
  S((dx, dy, k) => { const nb = J.chest, nt = J.neckTop; _capsule(ctx, nb, nt, R * .9, R * .8, dx, dy, k); }, skin);
  S(torsoPath, topC);
  if (legs !== 'skirt' && legs !== 'robe') S((dx, dy, k) => { const ang = Math.atan2(J.chest.y - J.pel.y, J.chest.x - J.pel.x) + Math.PI / 2, cx = Math.cos(ang), cy = Math.sin(ang);
    ctx.moveTo(J.pel.x + cx * hw * k + dx, J.pel.y + cy * hw * k + dy); ctx.lineTo(J.pel.x - cx * hw * k + dx, J.pel.y - cy * hw * k + dy);
    ctx.lineTo(J.pel.x + dx, J.pel.y + F.h * .3 * k + dy); ctx.closePath(); }, botC);
  if (sash && lvl === 'full') {   // 腰帶＋飄帶（跟著慣性甩）
    const sc = typeof sash === 'string' ? sash : pal.accent, bx = waist.x, by = lerp(waist.y, J.pel.y, .5);
    S((dx, dy, k) => _capsule(ctx, { x: bx - hw * 1.02, y: by }, { x: bx + hw * 1.02, y: by }, F.h * .07, F.h * .07, dx, dy, k), sc);
    const tail = (seed, ph) => { const pts = []; for (let i = 0; i <= 6; i++) { const u = i / 6, w = Math.sin((o.t || 0) * 5 + u * 4 + ph) * F.h * .12 * u;
      pts.push({ x: bx - hw * .6 * dir - dir * u * F.h * (.9 + Math.abs(sway.x) * .002) + w, y: by + u * F.h * (.9 - Math.min(.7, Math.abs(sway.x) * .0015)) + w * .5 }); } return pts; };
    [0, 1.3].forEach(ph => { const q = tail(1, ph); S((dx, dy, k) => { for (let i = 0; i < q.length - 1; i++) _capsule(ctx, q[i], q[i + 1], F.h * .05 * (1 - i / 7), F.h * .05 * (1 - (i + 1) / 7), dx, dy, k); }, sc); });
  }
  // 頭：髮後層 → 臉 → 五官 → 髮前層
  const hx = J.head.x, hy = J.head.y, hr = F.headR, hairC = mann ? '#bdb5a8' : pal.hair, face = o.face || EXPR.neutral;
  const hairBack = F.hair === 'long' ? (dx, dy, k) => { const sx = -sway.x * .0025 * F.h, sy = Math.abs(sway.x) * -.001 * F.h;
      ctx.moveTo(hx - hr * 1.02 + dx, hy + dy); ctx.quadraticCurveTo(hx - hr * 1.2 + sx + dx, hy + hr * 1.6 + sy + dy, hx - hr * .6 + sx * 1.5 + dx, hy + hr * 2.4 + sy + dy);
      ctx.lineTo(hx + hr * .6 + sx * 1.5 + dx, hy + hr * 2.4 + sy + dy); ctx.quadraticCurveTo(hx + hr * 1.2 + sx + dx, hy + hr * 1.6 + sy + dy, hx + hr * 1.02 + dx, hy + dy); ctx.closePath(); }
    : F.hair === 'bun' ? (dx, dy, k) => { ctx.moveTo(hx - hr * .6 * dir * view + hr * .45 + dx, hy - hr * .95 + dy); ctx.arc(hx - hr * .6 * dir * view + dx, hy - hr * .95 + dy, hr * .45 * k, 0, 6.283); } : null;
  if (hairBack && !mann && lvl === 'full') S(hairBack, hairC);
  S((dx, dy, k) => { ctx.moveTo(hx + hr * k + dx, hy + dy); ctx.ellipse(hx + dx, hy + dy, hr * .92 * k, hr * k, J.ha * dir * view * .3, 0, 6.283); }, skin);
  if (lvl === 'full') {
    if (!mann) _figFace(F, hx, hy, hr, dir, view, face, o);
    if (F.hair !== 'none' && !mann) S((dx, dy, k) => _figHairTop(F.hair, hx + dx, hy + dy, hr * k, dir, view, o.t || 0, sway), hairC);
  }
  limbDraw(J.armN, armR0, armR1, ...armCol(), skin, R * .72, false, false);
  ctx.restore();
  return { ...J, gy, x, y };
}
function _figHairTop(kind, hx, hy, hr, dir, view, t, sway) {
  const back = -dir * view * hr * .18;
  if (kind === 'spiky') {
    const n = 7; ctx.moveTo(hx - hr * 1.02, hy - hr * .05);
    for (let i = 0; i <= n; i++) { const u = i / n, a = Math.PI * (1.05 + u * .9), sp = hr * (1.55 + (i % 2) * -.35) + Math.sin(t * 4 + i) * hr * .03;
      const ax = hx + Math.cos(a) * sp + back * (1.5 - u) - sway.x * .0012 * hr, ay = hy + Math.sin(a) * sp * .95;
      ctx.lineTo(ax, ay); ctx.lineTo(hx + Math.cos(a + .2) * hr * 1.02 + back, hy + Math.sin(a + .2) * hr * 1.02); }
    ctx.lineTo(hx + hr * 1.02, hy - hr * .05); ctx.quadraticCurveTo(hx + hr * .5 * dir, hy - hr * .7, hx - hr * .2 * dir, hy - hr * .5);
    ctx.quadraticCurveTo(hx - hr * .7 * dir, hy - hr * .45, hx - hr * 1.02, hy - hr * .05); ctx.closePath();
  } else {   // short / long / bun：頭頂一片，瀏海在面向的反側
    const side = kind === 'long' ? .5 : -.05;   // sideburns end above the eyes; the fringe sweeps across the forehead, never over the eyes
    ctx.moveTo(hx - hr * 1.05, hy + hr * side);
    ctx.bezierCurveTo(hx - hr * 1.15, hy - hr * 1.35, hx + hr * 1.15, hy - hr * 1.35, hx + hr * 1.05, hy + hr * side);
    ctx.quadraticCurveTo(hx + hr * .8 * dir, hy - hr * .55, hx + hr * .1 * dir, hy - hr * .58);
    ctx.quadraticCurveTo(hx - hr * .6 * dir + back, hy - hr * .35, hx - hr * 1.05, hy + hr * side); ctx.closePath();
  }
}
function _figFace(F, hx, hy, hr, dir, view, e, o) {
  const ink = F.pal.line, fx = hx + dir * view * hr * .38, eyeH = hr * 2 * F.P.eye, sep = hr * .42 * (1 - view * .55);
  const blink = o.blink === false ? 1 : figBlink(o.t || 0, o.seed || 3), open = clamp(e.eye * blink, .06, 1.35), look = e.look || o.look || { x: 0, y: 0 };
  const big = F.P.eye > .15;   // 動漫、Q 版：大眼、有高光
  [-1, 1].forEach(side => {
    if (view > .75 && side === -1) return;   // 側面只看得到一隻眼
    const ex = fx + side * sep, ey = hy + hr * .05, ew = eyeH * (big ? .62 : .5), eh = eyeH * open * .5;
    ctx.save(); ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.ellipse(ex, ey, ew, Math.max(.6, eh), 0, 0, 6.283); ctx.fill();
    ctx.clip(); const px = ex + look.x * ew * .45 + dir * view * ew * .3, py = ey + look.y * eh * .4;
    circle(px, py, ew * (big ? .72 : .55), big ? F.pal.eye : ink); if (big) circle(px, py, ew * .38, ink);
    if (big) circle(px - ew * .25, py - eh * .35, ew * .22, '#ffffff');
    ctx.restore();
    ctx.strokeStyle = ink; ctx.lineWidth = Math.max(1.2, hr * .07); ctx.beginPath(); ctx.ellipse(ex, ey, ew, Math.max(.6, eh), 0, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke();
    // 眉毛：brow 正值 = 內側壓低（生氣）
    const by = ey - eyeH * .6 - e.browY * hr * .25, tilt = e.brow * side * dir;
    ctx.lineWidth = Math.max(1.5, hr * (F.P.eye > .15 ? .08 : .1)); ctx.beginPath();
    ctx.moveTo(ex - ew * 1.1, by - tilt * hr * .18 * -1); ctx.lineTo(ex + ew * 1.1, by + tilt * hr * .18 * -1); ctx.stroke();
  });
  // 嘴
  const mx = fx - dir * view * hr * .05, my = hy + hr * .55, mw = hr * (.32 - view * .1), op = e.open * hr * .3;
  ctx.strokeStyle = ink; ctx.lineWidth = Math.max(1.2, hr * .07); ctx.lineCap = 'round'; ctx.beginPath();
  const m = e.mouth;
  if (m === 'smile') { ctx.moveTo(mx - mw, my - hr * .04); ctx.quadraticCurveTo(mx, my + hr * .16 + op, mx + mw, my - hr * .04); if (op > hr * .08) { ctx.closePath(); ctx.fillStyle = '#7a2a2a'; ctx.fill(); } ctx.stroke(); }
  else if (m === 'grin' || m === 'open' || m === 'o' || m === 'shout') {
    const w = m === 'o' ? mw * .45 : mw, hgt = Math.max(hr * .05, op * (m === 'o' ? 1.1 : 1));
    ctx.ellipse(mx, my + hgt * .3, w, hgt, 0, m === 'grin' ? 0 : 0, m === 'grin' ? Math.PI : 6.283); if (m === 'grin') ctx.closePath();
    ctx.fillStyle = '#6a2020'; ctx.fill(); ctx.stroke();
  } else if (m === 'grit') {
    ctx.rect(mx - mw, my - op * .4, mw * 2, Math.max(hr * .08, op * .8)); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(mx - mw, my); ctx.lineTo(mx + mw, my); for (let i = -2; i <= 2; i++) { ctx.moveTo(mx + i * mw * .4, my - op * .4); ctx.lineTo(mx + i * mw * .4, my + op * .4); } ctx.lineWidth = Math.max(.8, hr * .035); ctx.stroke();
  } else if (m === 'frown') { ctx.moveTo(mx - mw, my + hr * .06); ctx.quadraticCurveTo(mx, my - hr * .08, mx + mw, my + hr * .06); ctx.stroke(); }
  else { ctx.moveTo(mx - mw * .8, my); ctx.lineTo(mx + mw * .8, my); ctx.stroke(); }
  if (view > .4) { ctx.beginPath(); ctx.moveTo(hx + dir * hr * .86, hy - hr * .05); ctx.lineTo(hx + dir * hr * 1.02, hy + hr * .22); ctx.lineTo(hx + dir * hr * .86, hy + hr * .3); ctx.lineWidth = Math.max(1, hr * .05); ctx.stroke(); }   // 側面鼻子
}

/* ---------- 劇組工具：角色設定與景別 ---------- */
/** 從 project.json 的 cast 建立角色（美術設定集中在一處，每個鏡頭都用同一份，才會連戲） */
function figCast(name, height, over = {}) {
  const spec = (PROJECT.cast || {})[name];
  if (!spec) throw new Error(`cast 裡沒有角色 ${name}`);
  return figMake({ ...spec, ...over, height, pal: { ...(spec.pal || {}), ...(over.pal || {}) }, outfit: { ...(spec.outfit || {}), ...(over.outfit || {}) } });
}
/** 景別 → 鏡頭：回傳 shot() 用的 {x, y, zoom}，讓角色（腳底在 (x, groundY)）以該景別入鏡。
 *  ELS 角色約佔畫面 12% 高、LS 全身 75%、MS 腰部以上、CU 頭肩、ECU 眼睛。o.off = 主體放在三分線（-1 左、1 右） */
function figFrame(F, x, groundY, size = 'LS', o = {}) {
  const V = H * .9, f = { ELS: [F.Hf / .12, .5], LS: [F.Hf / .75 * .9, .5], MS: [F.Hf * .58, .7], CU: [F.Hf * .26, .86], ECU: [F.h * .7, 1 - F.P.head * .45] }[size] || [F.Hf, .5];
  const zoom = V / f[0], cy = groundY - F.Hf * f[1];
  return { x: x - (o.off || 0) * W / 6 / zoom, y: cy + (o.dy || 0) / zoom, zoom, rot: o.rot || 0 };
}

/** 特寫、大特寫用：回傳要把角色的頭放在 (hx, hy) 時，figDraw 該傳的腳底位置 {x, y}（頭先定位，身體跟著出畫） */
function figPlace(F, pose, hx, hy, o = {}) {
  const J = _figJoints(F, pose, o.dir ?? 1, o.view ?? 1), low = Math.max(J.ftR.y, J.ftL.y, J.anR.y, J.anL.y);
  return { x: hx - J.head.x, y: hy - (J.head.y - low) };
}

/* ---------- 扁平插畫風（render: 'illus'） ----------
 * 向量插畫角色：曲線輪廓、粗圓頭連續四肢（關節自然彎）、大塊髮型剪影、點眼簡化五官、無描邊、一層柔和陰影。
 * 這種風格本來就不追求寫實細節，程序化畫起來最好看。 */
function _figIllus(F, J, pose, o) {
  const pal = F.pal, dir = o.dir, view = o.view, t = o.t || 0, R = F.limbR, e = o.face || EXPR.neutral;
  const shade = c => mixc(c, '#1a1030', .28), far = c => mixc(c, '#1a1030', view > .4 ? .2 : .06);
  const stroke = (pts, w, col) => { ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length - 1; i++) { const m = { x: (pts[i].x + pts[i + 1].x) / 2, y: (pts[i].y + pts[i + 1].y) / 2 }; ctx.quadraticCurveTo(pts[i].x, pts[i].y, i === pts.length - 2 ? pts[i + 1].x : m.x, i === pts.length - 2 ? pts[i + 1].y : m.y); }
    if (pts.length === 2) ctx.lineTo(pts[1].x, pts[1].y); ctx.stroke(); };
  const sleeve = F.outfit.sleeve, legs = F.outfit.legs;
  const arm = (A, isFar) => { const f = isFar ? far : c => c, w = R * 2.1;
    const sl = sleeve === 'long' ? 1 : sleeve === 'short' ? .45 : 0, mid = { x: lerp(A[0].x, A[1].x, 1), y: lerp(A[0].y, A[1].y, 1) };
    stroke([A[0], A[1], A[2]], w, f(pal.skin));
    if (sl >= 1) stroke([A[0], A[1], A[2]], w * 1.08, f(pal.top));
    else if (sl > 0) stroke([A[0], { x: lerp(A[0].x, A[1].x, sl * 1.6), y: lerp(A[0].y, A[1].y, sl * 1.6) }], w * 1.12, f(pal.top));
    circle(A[2].x + (A[3].x - A[2].x) * .35, A[2].y + (A[3].y - A[2].y) * .35, w * .62, f(pal.skin)); };
  const leg = (L, isFar) => { const f = isFar ? far : c => c, w = R * 2.7;
    stroke([L[0], L[1], L[2]], w, f(legs === 'shorts' || legs === 'skirt' ? pal.skin : pal.bottom));
    if (legs === 'shorts') stroke([L[0], { x: lerp(L[0].x, L[1].x, .7), y: lerp(L[0].y, L[1].y, .7) }], w * 1.1, f(pal.bottom));
    const a = Math.atan2(L[3].y - L[2].y, L[3].x - L[2].x);   // rounded shoe along the foot
    ctx.save(); ctx.translate(L[2].x, L[2].y); ctx.rotate(a); fillRR(-w * .45, -w * .42, Math.hypot(L[3].x - L[2].x, L[3].y - L[2].y) + w * .55, w * .75, w * .37, f(pal.shoe)); ctx.restore(); };
  arm(J.armF, true); leg(J.legF, true); leg(J.legN, false);
  // torso: a soft bean from shoulders to hips
  const ang = Math.atan2(J.chest.y - J.pel.y, J.chest.x - J.pel.x) + Math.PI / 2, cx = Math.cos(ang), cy = Math.sin(ang);
  const sw = F.shW / 2 * (1 - view * .4), hw = F.hipW / 2 * (1 - view * .3), top = { x: J.chest.x, y: J.chest.y - R * .6 };
  const torso = () => { ctx.beginPath();
    ctx.moveTo(top.x + cx * sw * .8, top.y + cy * sw * .8);
    ctx.bezierCurveTo(top.x + cx * sw * 1.1, top.y + cy * sw * 1.1 + R, J.pel.x + cx * hw * 1.15, J.pel.y + cy * hw - R * 2, J.pel.x + cx * hw, J.pel.y + cy * hw + R * .6);
    ctx.quadraticCurveTo(J.pel.x, J.pel.y + R * 1.6, J.pel.x - cx * hw, J.pel.y - cy * hw + R * .6);
    ctx.bezierCurveTo(J.pel.x - cx * hw * 1.15, J.pel.y - cy * hw - R * 2, top.x - cx * sw * 1.1, top.y - cy * sw * 1.1 + R, top.x - cx * sw * .8, top.y - cy * sw * .8);
    ctx.quadraticCurveTo(top.x, top.y - R * 1.2, top.x + cx * sw * .8, top.y + cy * sw * .8); ctx.closePath(); };
  if (legs === 'skirt' || legs === 'robe') { ctx.fillStyle = pal.bottom; ctx.beginPath(); const L = legs === 'robe' ? F.thigh * 1.5 : F.thigh * .8;
    ctx.moveTo(J.pel.x - hw, J.pel.y - R); ctx.lineTo(J.pel.x + hw, J.pel.y - R); ctx.lineTo(J.pel.x + hw * 1.7, J.pel.y + L); ctx.quadraticCurveTo(J.pel.x, J.pel.y + L * 1.08, J.pel.x - hw * 1.7, J.pel.y + L); ctx.closePath(); ctx.fill(); }
  stroke([J.chest, J.neckTop], R * 1.2, pal.skin);
  torso(); ctx.fillStyle = pal.top; ctx.fill();
  ctx.save(); torso(); ctx.clip(); ctx.fillStyle = shade(pal.top); ctx.beginPath();          // soft shadow on the side away from the light
  ctx.ellipse(J.pel.x - o.light.x * sw * 1.3, (top.y + J.pel.y) / 2, sw * .9, F.torso, 0, 0, 6.283); ctx.globalAlpha = .45; ctx.fill(); ctx.restore();
  if (F.outfit.sash) { ctx.strokeStyle = typeof F.outfit.sash === 'string' ? F.outfit.sash : pal.accent; ctx.lineWidth = R * .9; ctx.beginPath(); ctx.moveTo(J.pel.x - cx * hw, J.pel.y - cy * hw - R * .8); ctx.lineTo(J.pel.x + cx * hw, J.pel.y + cy * hw - R * .8); ctx.stroke(); }
  // head
  const hx = J.head.x, hy = J.head.y, hr = F.headR, sway = o.sway || { x: 0, y: 0 };
  if (F.hair === 'long') { ctx.fillStyle = shade(pal.hair); ctx.beginPath(); ctx.ellipse(hx - dir * view * hr * .2 - sway.x * .002 * hr, hy + hr * .6, hr * 1.05, hr * 1.35, 0, 0, 6.283); ctx.fill(); }
  if (F.hair === 'bun') circle(hx - dir * view * hr * .55, hy - hr * .95, hr * .45, pal.hair);
  ctx.fillStyle = pal.skin; ctx.beginPath(); ctx.ellipse(hx, hy, hr * .95, hr * 1.02, 0, 0, 6.283); ctx.fill();
  if (view > .3) circle(hx - dir * hr * .25 * view, hy + hr * .1, hr * .16, shade(pal.skin));                  // ear
  if (F.hair !== 'none') { ctx.beginPath(); _figHairTop(F.hair, hx, hy, hr, dir, view, t, sway); ctx.fillStyle = pal.hair; ctx.fill(); }
  // face: dot eyes, short thick brows, simple mouth, blush
  const fx = hx + dir * view * hr * .45, blink = o.blink === false ? 1 : figBlink(t, o.seed || 3), open = clamp((e.eye ?? 1) * blink, .08, 1.3);
  const look = e.look || o.look || { x: 0, y: 0 }, sep = hr * .36 * (1 - view * .5), ey = hy + hr * .08, er = hr * (.1 + F.P.eye * .35);
  [-1, 1].forEach(sd => { if (view > .75 && sd === -dir) return;
    const ex = fx + sd * sep + look.x * er * .4;
    ctx.fillStyle = pal.eye; ctx.beginPath(); ctx.ellipse(ex, ey + look.y * er * .3, er * .8, er * open, 0, 0, 6.283); ctx.fill();
    if (open > .5) circle(ex - er * .25, ey - er * .3, er * .28, 'rgba(255,255,255,.85)');
    const by = ey - er * 1.9 - (e.browY || 0) * hr * .22, tilt = (e.brow || 0) * sd * dir * hr * .12;
    ctx.strokeStyle = shade(pal.hair); ctx.lineWidth = hr * .11; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(ex - er * 1.1, by + tilt); ctx.lineTo(ex + er * 1.1, by - tilt); ctx.stroke(); });
  const mx = fx - dir * view * hr * .05, my = hy + hr * .52, mw = hr * (.26 - view * .08), op = (e.open || 0) * hr * .28, m = e.mouth;
  ctx.strokeStyle = shade(pal.skin); ctx.fillStyle = '#7a2f3a'; ctx.lineWidth = hr * .08; ctx.lineCap = 'round'; ctx.beginPath();
  if (m === 'smile' || m === 'grin') { ctx.moveTo(mx - mw, my - hr * .02); ctx.quadraticCurveTo(mx, my + hr * .16 + op, mx + mw, my - hr * .02); if (op > hr * .06) { ctx.closePath(); ctx.fill(); } else ctx.stroke(); }
  else if (m === 'open' || m === 'o' || m === 'shout') { ctx.ellipse(mx, my + op * .2, m === 'o' ? mw * .45 : mw * .8, Math.max(hr * .05, op * .8), 0, 0, 6.283); ctx.fill(); }
  else if (m === 'frown') { ctx.moveTo(mx - mw, my + hr * .06); ctx.quadraticCurveTo(mx, my - hr * .06, mx + mw, my + hr * .06); ctx.stroke(); }
  else if (m === 'grit') { fillRR(mx - mw, my - op * .3, mw * 2, Math.max(hr * .08, op * .6), hr * .04, '#f4efe6'); }
  else { ctx.moveTo(mx - mw * .6, my); ctx.lineTo(mx + mw * .6, my); ctx.stroke(); }
  if (m === 'smile' || m === 'grin') [-1, 1].forEach(sd => { if (view > .75 && sd === -dir) return; circle(fx + sd * sep * 1.25, ey + er * 2.2, er * 1.1, 'rgba(240,120,120,.35)'); });
  if (view > .4) { ctx.strokeStyle = shade(pal.skin); ctx.lineWidth = hr * .07; ctx.beginPath(); ctx.moveTo(hx + dir * hr * .9, hy + hr * .05); ctx.lineTo(hx + dir * hr * 1.02, hy + hr * .28); ctx.lineTo(hx + dir * hr * .88, hy + hr * .32); ctx.stroke(); }
  arm(J.armN, false);
}
