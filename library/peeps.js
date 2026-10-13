/* peeps.js：Open Peeps 插畫角色（CC0，Pablo Stanley）。插畫師畫好的部件組合：全身（站姿、坐姿）、半身（含筆電、文件、咖啡等道具）、
 * 33 種表情、53 種髮型、鬍子、眼鏡。不用骨架：角色靠「換表情、換姿勢、眨眼、說話、呼吸、點頭、彈跳進場」演戲。
 * 部件清單與用法見 references/character.md；build.py 只把場景與 project.json 用到的部件內嵌進 HTML（PEEPS）。 */

/** 顏色名稱對應：colors 可以用簡短的名稱，也可以直接寫部件的原始參數名（skinColor…） */
const PEEP_COL = { skin: ['skinColor'], top: ['topColor'], pants: ['pantsColor'], shoes: ['shoesColor'],
  jacket: ['jacketColor', 'blazerColor', 'coatColor'], hair: ['hairColor', 'beardColor'], outline: ['outlineColor'],
  prop: ['computerColor', 'paperColor', 'cupColor'], hat: ['beanieColor', 'capColor', 'hijabColor', 'turbanColor', 'clipColor'] };
const PEEP_SKIN = { light: '#F3D3B5', fair: '#F1C9A5', tan: '#E0A57E', medium: '#C68A62', brown: '#A06A44', deep: '#7A4B2E' };
const _peepNeck = {};

function _peepVars(c = {}) {
  const v = {};
  for (const [k, val] of Object.entries(c)) {
    const col = k === 'skin' && PEEP_SKIN[val] ? PEEP_SKIN[val] : val;
    (PEEP_COL[k] || [k]).forEach(n => { v[n] = col; });
  }
  return v;
}
function _peepPart(it, vars, c = ctx) {
  if (!it) return;
  if (!it._p) it._p = it.paths.map(p => new Path2D(p[0]));
  const v = Object.assign({}, it.defaults, vars), col = s => s && s[0] === '$' ? (v[s.slice(1)] || '#000') : s;
  it.paths.forEach((p, i) => {
    const f = col(p[1]);
    if (f && f !== 'none') { c.fillStyle = f; c.fill(it._p[i], p[p.length - 1] === 'evenodd' ? 'evenodd' : 'nonzero'); }
    if (p[2] && p[2] !== 'none' && p[2] !== 'evenodd') { c.strokeStyle = col(p[2]); c.lineWidth = +p[3] || 1; c.stroke(it._p[i]); }
  });
}
function _peepGet(cat, name) {
  const it = PEEPS && PEEPS[cat] && PEEPS[cat][name];
  if (!it && typeof ERRS !== 'undefined' && !ERRS.find(e => e.msg.includes(`${cat}/${name}`)))
    ERRS.push({ fn: '(peeps)', i: -1, t: 0, msg: `找不到角色部件 ${cat}/${name}（名稱見 references/character.md）` });
  return it;
}
/** 脖子頂端位置（依部件輪廓自動量，快取） */
function _peepNeckOf(cat, name) {
  const key = cat + '/' + name; if (_peepNeck[key]) return _peepNeck[key];
  const it = PEEPS[cat][name], [, , w, h] = it.vb, k = .25, cv = document.createElement('canvas');
  cv.width = Math.ceil(w * k); cv.height = Math.ceil(h * k);
  const g = cv.getContext('2d', { willReadFrequently: true }); g.scale(k, k); _peepPart(it, {}, g);
  const d = g.getImageData(0, 0, cv.width, cv.height).data;
  const row = y => { let a = -1, b = -1; for (let i = 0; i < cv.width; i++) if (d[(y * cv.width + i) * 4 + 3] > 40) { if (a < 0) a = i; b = i; } return [a, b]; };
  let top = 0; while (top < cv.height - 1 && row(top)[0] < 0) top++;
  const [a, b] = row(Math.min(cv.height - 1, top + 6));
  return (_peepNeck[key] = { x: (a + b) / 2 / k, y: top / k });
}
/** 這一格要用的表情：眨眼（o.blink，預設開）、說話（o.talk：true 或 t => 布林）會暫時換臉 */
function _peepFace(o, t) {
  if (o.talk && (typeof o.talk === 'function' ? o.talk(t) : true) && Math.floor(t * 8.5) % 2) return o.talkFace || 'Explaining';
  if (o.blink !== false) { const per = 2.6 + ((o.seed || 1) * 7 % 10) * .17, ph = (t + (o.seed || 1) * .37) % per; if (ph < .13) return 'EyesClosed'; }
  return o.face || 'Calm';
}
/** 畫頭（半身像座標系）：髮型、臉、鬍子、配件，套官方組裝位移 */
function _peepHead(o, vars, t, bodyName) {
  const L = PEEPS._layout, G = L.groups, OF = L.offsets, at = (g, off, fn) => {
    ctx.save(); ctx.translate(G[g][0], G[g][1]); if (off) { ctx.translate(off[0], off[1]); ctx.scale(off[2], off[3]); } fn(); ctx.restore(); };
  ctx.save(); const ho = bodyName && OF.createHead[bodyName]; if (ho) ctx.translate(ho[0], ho[1]);
  if (o.head) at('Hair', OF.createHair[o.head], () => _peepPart(_peepGet('head', o.head), vars));
  at('Face', null, () => _peepPart(_peepGet('face', _peepFace(o, t)), vars));
  if (o.beard) at('Beard', OF.createBeard[o.beard], () => _peepPart(_peepGet('beard', o.beard), vars));
  if (o.acc) at('Accessories', OF.createAccessory[o.acc], () => _peepPart(_peepGet('accessory', o.acc), vars));
  ctx.restore();
}
/** 頭的擺動：o.nod 幅度（預設 .025 弧度的緩慢擺動）＋ o.tilt 固定傾斜 */
const _peepNod = (o, t) => (o.tilt || 0) + (o.idle === false ? 0 : (o.nod ?? .025) * Math.sin(t * 1.3 + (o.seed || 1)));
const _peepBreath = (o, t) => o.idle === false ? 1 : 1 + .007 * Math.sin(t * 2.1 + (o.seed || 1) * 1.7);

/**
 * 全身角色。(x, groundY) 是腳底中心，h 是全身高（含頭）。
 * o = { body: 'BlazerColorTee'（站姿或坐姿名稱）, head: 'Bun', face: 'Smile', beard, acc: 'Glasses',
 *       colors: { skin: 'fair'｜色碼, top, pants, jacket, shoes, hair, outline }, dir: 1｜-1（面向）, talk, blink, nod, tilt, idle, seed }
 * t 傳本幕秒數（眨眼、說話、呼吸用）。回傳 { head: {x, y}（頭頂附近，可放對話框）, w, h }
 */
function peep(x, groundY, h, o, t = 0) {
  if (!PEEPS) return null;
  const cat = PEEPS.standing[o.body] ? 'standing' : 'sitting', body = _peepGet(cat, o.body); if (!body) return null;
  const vars = _peepVars(o.colors), nk = _peepNeckOf(cat, o.body), ref = _peepNeckOf('effigy', 'Tee'), G = PEEPS._layout.groups;
  const REF = { x: G.Body[0] + ref.x, y: G.Body[1] + ref.y }, HS = 1.06, bh = body.vb[3];
  const headTop = (G.Hair[1] - REF.y) / HS, sc = h / (bh - headTop), br = _peepBreath(o, t);
  ctx.save(); ctx.translate(x, groundY); ctx.scale((o.dir || 1) * sc, sc * br); ctx.translate(-nk.x, -bh);
  _peepPart(body, vars);
  ctx.save(); ctx.translate(nk.x, nk.y); ctx.rotate(_peepNod(o, t)); ctx.scale(1 / HS, 1 / HS); ctx.translate(-REF.x, -REF.y);
  _peepHead(o, vars, t, null); ctx.restore();
  ctx.restore();
  return { head: { x, y: groundY - h * br }, w: body.vb[2] * sc, h };
}
/**
 * 半身角色（胸口以上，常配桌子當前景）。(x, bottom) 是底部中心，h 是高。
 * o.body 用半身名稱（Computer、Paper、Coffee、Explaining、BlazerBlackTee、ButtonShirt、Tee…），其他同 peep()
 */
function peepBust(x, bottom, h, o, t = 0) {
  if (!PEEPS) return null;
  const body = _peepGet('effigy', o.body); if (!body) return null;
  const vars = _peepVars(o.colors), VB = [184.2, 210.8, 940.3, 1130.6], s = h / VB[3], G = PEEPS._layout.groups, br = _peepBreath(o, t);
  const ref = _peepNeckOf('effigy', 'Tee'), nx = G.Body[0] + ref.x, ny = G.Body[1] + ref.y;
  ctx.save(); ctx.translate(x, bottom); ctx.scale((o.dir || 1) * s, s * br); ctx.translate(-(VB[0] + VB[2] / 2), -(VB[1] + VB[3]));
  ctx.save(); ctx.translate(G.Body[0], G.Body[1]); _peepPart(body, vars); ctx.restore();
  ctx.save(); ctx.translate(nx, ny); ctx.rotate(_peepNod(o, t)); ctx.translate(-nx, -ny); _peepHead(o, vars, t, o.body); ctx.restore();
  ctx.restore();
  return { head: { x, y: bottom - h * br }, w: VB[2] * s, h };
}
/** 從 project.json 的 cast 取角色設定（同一個角色整支片外型一致），over 可覆寫 face、body 等 */
const peepCast = (name, over = {}) => Object.assign({ seed: [...name].reduce((a, ch) => a + ch.charCodeAt(0), 0) % 97 },
  (typeof PROJECT !== 'undefined' && PROJECT.cast && PROJECT.cast[name]) || {}, over);
