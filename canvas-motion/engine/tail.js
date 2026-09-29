/* ==========================================================================
 * Canvas Motion — tail.js（固定引擎）
 * 場景時間表、frame(t)、配樂合成 step()、即時／離線音訊、播放控制列。
 * build.py 會在此之前注入 PROJECT（來自 project.json）。
 * ========================================================================== */

const BPM = PROJECT.bpm || STYLE.music.bpm || 120;
const BAR = 240 / BPM, BEAT = 60 / BPM, SX = BAR / 16;   // 小節、拍、16 分音符（秒）
const TD = PROJECT.transDur ?? Math.min(.6, BEAT * 1.2); // 轉場長度，中點對齊切點
const ERRS = [];
const SC = (() => {
  let acc = 0;
  return PROJECT.scenes.map((s, i) => {
    const dur = (s.bars || 2) * BAR; const o = { energy: .6, ...s, i, start: acc, dur }; acc += dur; return o;
  });
})();
const TOTAL = SC.length ? SC[SC.length - 1].start + SC[SC.length - 1].dur : 1;

function sceneAt(t) { for (let i = SC.length - 1; i >= 0; i--) if (t >= SC[i].start - 1e-6) return i; return 0; }
function beatInfo(t) {
  const b = t / BEAT, f = b - Math.floor(b);
  return { n: Math.floor(b), frac: f, pulse: Math.exp(-f * 5.5), bar: Math.floor(t / BAR), barPulse: Math.exp(-((t / BAR) % 1) * 3) };
}
const transOf = s => s.trans || (STYLE.trans || ['fade'])[s.i % (STYLE.trans || ['fade']).length];

function drawSceneInto(s, time, bi, c) {
  ctx = c;
  ctx.save(); STYLE.bg(time, bi.pulse, s); ctx.restore();
  ctx.save();
  const fn = window[s.fn];
  try {
    if (typeof fn !== 'function') throw new Error(`找不到場景函式 ${s.fn}`);
    fn(time - s.start, s.dur, bi.pulse, s);
  } catch (e) {
    if (!ERRS.find(x => x.i === s.i)) ERRS.push({ fn: s.fn, i: s.i, t: +(time - s.start).toFixed(2), msg: String(e && e.message || e) });
    ctx.restore(); ctx.save(); ctx.fillStyle = '#ff3b5c'; ctx.font = `700 ${Math.round(MIN * .03)}px monospace`;
    ctx.textAlign = 'center'; ctx.fillText(`${s.fn}: ${e && e.message}`, W / 2, H / 2);
  }
  ctx.restore();
}

/** 繪製時間點 time（秒）的畫面。匯出與截圖都呼叫這支 */
function frame(time) {
  time = clamp(time, 0, TOTAL - 1e-4);
  const bi = beatInfo(time), i = sceneAt(time), s = SC[i], end = s.start + s.dur;
  let A = null, B = null, p = 0, tr = null;
  if (i > 0 && time < s.start + TD / 2 && transOf(SC[i - 1]) !== 'cut') { A = SC[i - 1]; B = s; tr = transOf(A); p = (time - (s.start - TD / 2)) / TD; }
  else if (i < SC.length - 1 && time > end - TD / 2 && transOf(s) !== 'cut') { A = s; B = SC[i + 1]; tr = transOf(s); p = (time - (end - TD / 2)) / TD; }
  TXQ.length = 0;
  MAIN.save(); MAIN.setTransform(DPR, 0, 0, DPR, 0, 0); MAIN.globalAlpha = 1; MAIN.globalCompositeOperation = 'source-over';
  MAIN.fillStyle = STYLE.c.bg; MAIN.fillRect(0, 0, W, H);
  if (!tr) {
    drawSceneInto(s, time, bi, MAIN); ctx = MAIN;
    post(time); flushTxt(MAIN);
  } else {
    const ba = buf(0), bb = buf(1);
    // 兩幕各自「畫面 → 後製 → 文字」，文字才不會在轉場時被 bloom 糊掉（跟一般畫面一致）
    drawSceneInto(A, time, bi, ba.x); post(time, ba.x); flushTxt(ba.x);
    drawSceneInto(B, time, bi, bb.x); post(time, bb.x); flushTxt(bb.x);
    ctx = MAIN; (TR[tr] || TR.fade)(MAIN, ba.c, bb.c, clamp(p));
  }
  if (STYLE.overlay) { ctx = MAIN; MAIN.save(); STYLE.overlay(time, bi.pulse); MAIN.restore(); }
  MAIN.restore(); ctx = MAIN;
}

/* ================= 配樂合成 ================= */
const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
let _nOff = 0;
function initAudio(ac, dest) {
  const M = STYLE.music, out = ac.createGain(); out.gain.value = M.gain ?? .68;
  const comp = ac.createDynamicsCompressor(); comp.threshold.value = -16; comp.ratio.value = 4; comp.attack.value = .005; comp.release.value = .2;
  out.connect(comp); comp.connect(dest);
  const send = ac.createGain(); send.gain.value = M.delaySend ?? .28;
  const dly = ac.createDelay(2); dly.delayTime.value = SX * 3;
  const fb = ac.createGain(); fb.gain.value = M.delayFb ?? .33;
  const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 2800;
  send.connect(dly); dly.connect(lp); lp.connect(fb); fb.connect(dly); lp.connect(out);
  const nb = ac.createBuffer(1, ac.sampleRate, ac.sampleRate), d = nb.getChannelData(0); let sd = 12345;
  for (let i = 0; i < d.length; i++) { sd = (sd * 16807) % 2147483647; d[i] = sd / 1073741823.5 - 1; }
  _nOff = 0;
  return { ac, out, send, noise: nb, master: out };
}
function _env(A, t, a, d, peak, dest) {
  const g = A.ac.createGain(); g.gain.setValueAtTime(.0001, t);
  g.gain.exponentialRampToValueAtTime(Math.max(.0002, peak), t + a);
  g.gain.exponentialRampToValueAtTime(.0001, t + a + d); g.connect(dest); return g;
}
function kick(A, t, v = 1) {
  const o = A.ac.createOscillator(); o.frequency.setValueAtTime(160, t); o.frequency.exponentialRampToValueAtTime(42, t + .13);
  o.connect(_env(A, t, .002, .38, .95 * v, A.out)); o.start(t); o.stop(t + .45);
}
function noiseHit(A, t, dur, freq, type, peak, q = .8, send = 0) {
  const s = A.ac.createBufferSource(); s.buffer = A.noise;
  const f = A.ac.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
  const g = _env(A, t, .002, dur, peak, A.out); if (send) g.connect(A.send);
  s.connect(f); f.connect(g); s.start(t, (_nOff = (_nOff + .137) % .7)); s.stop(t + dur + .05);
}
function snare(A, t, v = 1) {
  noiseHit(A, t, .17, 1900, 'bandpass', .5 * v, .7);
  const o = A.ac.createOscillator(); o.type = 'triangle'; o.frequency.setValueAtTime(210, t); o.frequency.exponentialRampToValueAtTime(140, t + .08);
  o.connect(_env(A, t, .002, .09, .25 * v, A.out)); o.start(t); o.stop(t + .15);
}
function clap(A, t, v = 1) { for (let k = 0; k < 3; k++) noiseHit(A, t + k * .011, k < 2 ? .03 : .16, 1400, 'bandpass', .42 * v, 1.2, k === 2 ? 1 : 0); }
const hat = (A, t, v = .15) => noiseHit(A, t, .04, 8500, 'highpass', v, .6);
const crash = (A, t, v = .14) => noiseHit(A, t, 1.1, 6500, 'highpass', v, .5, 1);
function tone(A, t, m, dur, o = {}) {
  const osc = A.ac.createOscillator(); osc.type = o.wave || 'triangle'; osc.frequency.value = mtof(m); osc.detune.value = o.detune || 0;
  let n = osc;
  if (o.cut) {
    const f = A.ac.createBiquadFilter(); f.type = 'lowpass'; f.Q.value = o.q ?? 2;
    f.frequency.setValueAtTime(o.cut * 3, t); f.frequency.exponentialRampToValueAtTime(o.cut, t + Math.max(.02, dur * .5));
    osc.connect(f); n = f;
  }
  const g = _env(A, t, o.a ?? .004, dur, o.peak ?? .2, A.out); n.connect(g); if (o.send) g.connect(A.send);
  osc.start(t); osc.stop(t + (o.a ?? .004) + dur + .05);
}
function pad(A, t, notes, dur, peak = .05, wave = 'sawtooth', cut = 900) {
  const f = A.ac.createBiquadFilter(); f.type = 'lowpass'; f.frequency.value = cut;
  const g = A.ac.createGain(); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(peak, t + Math.min(.45, dur * .3));
  g.gain.setTargetAtTime(0, t + dur * .8, dur * .12); f.connect(g); g.connect(A.out);
  for (const m of notes) for (const dt of [-7, 7]) {
    const o = A.ac.createOscillator(); o.type = wave; o.frequency.value = mtof(m); o.detune.value = dt;
    o.connect(f); o.start(t); o.stop(t + dur * 1.6 + .2);
  }
}

/* 通用樂器（自訂配樂 MUSIC() 可直接呼叫；時間 t 為 AudioContext 秒數） */
// 鑼：數個不諧和泛音＋音高下滑。big=true 為大鑼（低、長），false 為小鑼（高、短、上揚）
function gong(A, t, v = 1, big = true) {
  const base = big ? 110 : 520, parts = big ? [1, 1.47, 2.09, 2.56, 3.2] : [1, 1.5, 2.3];
  const dur = big ? 2.4 : .55;
  parts.forEach((r, k) => {
    const o = A.ac.createOscillator(); o.type = 'sine';
    const f0 = base * r;
    if (big) { o.frequency.setValueAtTime(f0 * 1.02, t); o.frequency.exponentialRampToValueAtTime(f0 * .97, t + dur); }
    else { o.frequency.setValueAtTime(f0 * .94, t); o.frequency.exponentialRampToValueAtTime(f0 * 1.08, t + .12); }
    const g = _env(A, t, .003, dur * (1 - k * .12), .16 * v / (1 + k * .6), A.out); o.connect(g); if (big && !k) g.connect(A.send);
    o.start(t); o.stop(t + dur + .1);
  });
  noiseHit(A, t, big ? .25 : .08, big ? 900 : 3000, 'bandpass', .12 * v, 1.5);
}
// 鈸／鐃鈸：金屬噪音，closed=true 為悶擊
function cymbal(A, t, v = 1, closed = false) {
  noiseHit(A, t, closed ? .07 : .7, 5200, 'bandpass', .22 * v, .9, closed ? 0 : 1);
  noiseHit(A, t, closed ? .05 : .45, 9000, 'highpass', .12 * v, .5);
}
// 梆子／板（木魚）：短促木質音
function woodblock(A, t, v = 1, hi = true) {
  const o = A.ac.createOscillator(); o.type = 'sine'; o.frequency.setValueAtTime(hi ? 1250 : 820, t); o.frequency.exponentialRampToValueAtTime(hi ? 1050 : 700, t + .04);
  o.connect(_env(A, t, .001, .06, .35 * v, A.out)); o.start(t); o.stop(t + .1);
}
// 通鼓／堂鼓：有音高的皮鼓
function drum(A, t, v = 1, pitch = 120) {
  const o = A.ac.createOscillator(); o.frequency.setValueAtTime(pitch * 1.6, t); o.frequency.exponentialRampToValueAtTime(pitch, t + .06);
  o.connect(_env(A, t, .002, .22, .6 * v, A.out)); o.start(t); o.stop(t + .3);
  noiseHit(A, t, .04, 1800, 'bandpass', .12 * v, 1);
}
// 滑音長音（弦樂、嗩吶類）：從 m0 滑到 m1，帶顫音。o: wave, peak, cut, vib(音分), glide(秒), send
function bend(A, t, m0, m1, dur, o = {}) {
  const osc = A.ac.createOscillator(); osc.type = o.wave || 'sawtooth';
  osc.frequency.setValueAtTime(mtof(m0), t); osc.frequency.exponentialRampToValueAtTime(mtof(m1), t + Math.min(dur * .6, o.glide ?? .12));
  const lfo = A.ac.createOscillator(), lg = A.ac.createGain(); lfo.frequency.value = o.rate ?? 5.5; lg.gain.value = o.vib ?? 18;
  lfo.connect(lg); lg.connect(osc.detune); lfo.start(t + dur * .3); lfo.stop(t + dur + .1);
  const f = A.ac.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = o.cut ?? 1600; f.Q.value = o.q ?? .9;
  const g = A.ac.createGain(); g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(o.peak ?? .12, t + (o.a ?? .05));
  g.gain.setValueAtTime(o.peak ?? .12, t + dur * .75); g.gain.exponentialRampToValueAtTime(.0001, t + dur);
  osc.connect(f); f.connect(g); g.connect(A.out); if (o.send) g.connect(A.send);
  osc.start(t); osc.stop(t + dur + .05);
}

/** 第 i 個 16 分音符（在 t 秒播放）。依當下場景 energy 決定配器強度。
 *  專案若定義全域函式 MUSIC(A, i, t, info)，整支配樂改由它負責（可呼叫 tone／bend／gong／cymbal／woodblock／drum／kick／pad…）。 */
function step(A, i, t) {
  const M = STYLE.music, time = i * SX; if (time >= TOTAL - 1e-6) return;
  const s = SC[sceneAt(time + 1e-6)], e = s.energy ?? .6, bar = Math.floor(i / 16), st = i % 16;
  const ch = M.chords[bar % M.chords.length], kit = M.kit || 'four';
  const isSceneStart = st === 0 && Math.abs(time - s.start) < SX / 2;
  const lastBar = time >= TOTAL - BAR - 1e-6 && PROJECT.ending !== 'loop';
  if (typeof MUSIC === 'function') return MUSIC(A, i, t, { time, bar, st, e, scene: s, isSceneStart, lastBar, ch });

  if (lastBar) { // 結尾：一個重拍和弦收束，不再有鼓
    if (st === 0) {
      if (kit !== 'none') { kick(A, t, 1); crash(A, t, .16); }
      pad(A, t, ch, BAR * 1.4, .07, M.padWave, M.padCut);
      tone(A, t, ch[0] - 24, BAR * 1.2, { wave: 'sine', peak: .32, a: .004 });
      ch.forEach((m, k) => tone(A, t + k * .035, m + 12, BAR * .9, { wave: M.leadWave || 'triangle', peak: .08, send: 1, cut: M.leadCut || 2600 }));
    }
    return;
  }
  if (isSceneStart && s.i > 0 && kit !== 'none' && e >= .45) crash(A, t, .1 + e * .06);
  if (M.pad !== false && st === 0) pad(A, t, ch, BAR + .1, (M.padGain ?? .045) * (.55 + e * .6), M.padWave, M.padCut);
  if (kit !== 'none' && e >= .3) {
    const kHit = kit === 'four' ? st % 4 === 0 : kit === 'half' ? (st === 0 || st === 10) : st === 0;
    if (kHit) kick(A, t, kit === 'soft' ? .7 : .9);
    if (e >= .5 && (st === 4 || st === 12) && kit !== 'soft') (M.snare === 'clap' ? clap : snare)(A, t, .9);
    if (e >= .4) { if (st % 4 === 2) hat(A, t, .15); else if (e >= .8 && st % 2 === 1) hat(A, t, .06); }
  }
  if (M.bass !== false && e >= .3) {
    const pat = M.bassPat || [0, 3, 6, 8, 11, 14];
    if (pat.includes(st)) tone(A, t, ch[0] - 24, SX * 1.7, { wave: M.bassWave || 'sawtooth', peak: .17, cut: M.bassCut || 380, a: .004 });
  }
  if (M.lead !== 'none' && e >= (M.leadFrom ?? .55)) {
    const every = e >= .85 ? 1 : 2;
    if (st % every === 0) {
      const seq = M.arp || [0, 1, 2, 3, 2, 1, 2, 3], n = ch[seq[Math.floor(st / every) % seq.length] % ch.length];
      tone(A, t, n + 12 * (M.leadOct ?? 1), SX * (M.leadLen || 1.5), { wave: M.leadWave || 'triangle', peak: M.leadGain ?? .085, cut: M.leadCut || 2600, send: 1 });
    }
  }
}

/** 離線合成整支配樂，回傳 WAV 的 base64（export.py 使用） */
async function renderWav(sr = 44100) {
  const secs = TOTAL + 2, oc = new OfflineAudioContext(2, Math.ceil(secs * sr), sr);
  const A = initAudio(oc, oc.destination), n = Math.ceil(TOTAL / SX);
  for (let i = 0; i < n; i++) step(A, i, i * SX + .01);
  const b = await oc.startRendering(), L = b.getChannelData(0), R = b.getChannelData(1), len = L.length;
  const ab = new ArrayBuffer(44 + len * 4), v = new DataView(ab), ws = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  ws(0, 'RIFF'); v.setUint32(4, 36 + len * 4, true); ws(8, 'WAVE'); ws(12, 'fmt '); v.setUint32(16, 16, true);
  v.setUint16(20, 1, true); v.setUint16(22, 2, true); v.setUint32(24, sr, true); v.setUint32(28, sr * 4, true);
  v.setUint16(32, 4, true); v.setUint16(34, 16, true); ws(36, 'data'); v.setUint32(40, len * 4, true);
  for (let i = 0, o = 44; i < len; i++, o += 4) { v.setInt16(o, clamp(L[i], -1, 1) * 32767, true); v.setInt16(o + 2, clamp(R[i], -1, 1) * 32767, true); }
  const u8 = new Uint8Array(ab); let bin = ''; for (let i = 0; i < u8.length; i += 32768) bin += String.fromCharCode.apply(null, u8.subarray(i, i + 32768));
  return btoa(bin);
}

/* ================= 播放器 ================= */
const QS = new URLSearchParams(location.search);
const Player = { playing: false, t: 0, ac: null, A: null, t0: 0, next: 0, timer: null, wall0: 0, muted: false };
const ASPECTS = ['auto', '16:9', '9:16', '1:1', 'fill'];
let aspect = QS.get('aspect') || PROJECT.aspect || 'auto';
const $ = id => document.getElementById(id);

function layout() {
  const st = $('stage'), cs = getComputedStyle(st);
  const vw = st.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
  const vh = st.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
  let a = aspect; if (a === 'auto') a = vw < vh ? '9:16' : '16:9';
  let w = vw, h = vh;
  if (a !== 'fill') { const [x, y] = a.split(':').map(Number), r = x / y; if (vw / vh > r) { h = vh; w = vh * r; } else { w = vw; h = vw / r; } }
  resize(w, h, window.devicePixelRatio || 1);
  $('bAsp').textContent = aspect === 'auto' ? '自動' : aspect;
  if (!Player.playing) frame(Player.t);
}
const curTime = () => Player.ac ? Player.ac.currentTime - Player.t0 : performance.now() / 1000 - Player.wall0;
function pump() {
  const ac = Player.ac; if (!ac) return;
  while (Player.t0 + Player.next * SX < ac.currentTime + .15 && Player.next * SX < TOTAL) { step(Player.A, Player.next, Player.t0 + Player.next * SX); Player.next++; }
}
function stopAudio() {
  if (Player.timer) clearInterval(Player.timer); Player.timer = null;
  const ac = Player.ac; Player.ac = null;
  if (ac) { try { Player.A.master.gain.setTargetAtTime(0, ac.currentTime, .02); } catch (e) {} setTimeout(() => ac.close(), 250); }
}
async function play(from = Player.t) {
  if (from >= TOTAL - .05) from = 0;
  stopAudio(); Player.t = from;
  if (PROJECT.music !== false && !Player.muted) {
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)(); await ac.resume();
      Player.ac = ac; Player.A = initAudio(ac, ac.destination);
      Player.t0 = ac.currentTime + .06 - from; Player.next = Math.ceil(from / SX - 1e-6);
      Player.timer = setInterval(pump, 25); pump();
    } catch (e) { Player.ac = null; }
  }
  Player.wall0 = performance.now() / 1000 - from; Player.playing = true;
  $('play').hidden = true; $('hud').hidden = false; $('bPlay').textContent = '❚❚'; poke();
  requestAnimationFrame(loop);
}
function pause() { if (!Player.playing) return; Player.t = clamp(curTime(), 0, TOTAL); Player.playing = false; stopAudio(); $('bPlay').textContent = '▶'; poke(); }
function loop() {
  if (!Player.playing) return;
  const t = curTime();
  if (t >= TOTAL) {
    if (PROJECT.ending === 'loop') { play(0); return; }
    Player.t = TOTAL; frame(TOTAL); pause(); hud(TOTAL); $('play').textContent = '↺ 重播'; $('play').hidden = false; return;
  }
  Player.t = Math.max(0, t); frame(Player.t); hud(Player.t); requestAnimationFrame(loop);
}
const fmt = s => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
function hud(t) { $('fill').style.width = (t / TOTAL * 100) + '%'; $('time').textContent = `${fmt(t)} / ${fmt(TOTAL)}`; }
let _idle;
function poke() { $('hud').classList.remove('idle'); clearTimeout(_idle); _idle = setTimeout(() => Player.playing && $('hud').classList.add('idle'), 2600); }
function seek(t) { const was = Player.playing; pause(); Player.t = clamp(t, 0, TOTAL - .01); frame(Player.t); hud(Player.t); if (was) play(Player.t); }

function boot() {
  if (QS.has('still')) { // 無頭瀏覽器 --dump-dom 備援：?still=3.2&w=1280&h=720
    resize(+QS.get('w') || 1280, +QS.get('h') || 720, 1); frame(+QS.get('still'));
    $('out').textContent = CV.toDataURL('image/jpeg', .9); $('play').hidden = true; return;
  }
  Player.t = PROJECT.poster ?? Math.min(SC[0] ? SC[0].dur * .7 : 1, TOTAL);
  layout(); hud(0);
  addEventListener('resize', layout);
  $('play').onclick = () => { const f = Player.started ? Player.t : 0; Player.started = true; play(f); };
  $('bPlay').onclick = () => Player.playing ? pause() : play(Player.t);
  $('bRe').onclick = () => play(0);
  $('bMute').onclick = () => { Player.muted = !Player.muted; $('bMute').textContent = Player.muted ? '✕' : '♪'; if (Player.playing) play(curTime()); };
  $('bAsp').onclick = () => { aspect = ASPECTS[(ASPECTS.indexOf(aspect) + 1) % ASPECTS.length]; layout(); };
  $('bar').onclick = e => { const r = e.currentTarget.getBoundingClientRect(); seek((e.clientX - r.left) / r.width * TOTAL); };
  CV.onclick = () => { if ($('play').hidden) Player.playing ? pause() : play(Player.t); poke(); };
  addEventListener('pointermove', poke);
  addEventListener('keydown', e => {
    if (e.code === 'Space') { e.preventDefault(); Player.playing ? pause() : play(Player.t); }
    else if (e.code === 'ArrowRight') seek(Player.t + BAR); else if (e.code === 'ArrowLeft') seek(Player.t - BAR);
    else if (e.key === 'r') play(0);
  });
  if (document.fonts) document.fonts.ready.then(() => { _caches.clear(); if (!Player.playing) frame(Player.t); });
}

/** 給 sheet.py / export.py 呼叫的介面 */
window.__cm = { frame, resize, renderWav, TOTAL, BAR, BPM, SC: SC.map(s => ({ fn: s.fn, start: s.start, dur: s.dur, energy: s.energy })), errors: ERRS,
  bench(n = 30, w = 1280, h = 720) { // 每格強制同步（讀回 1px），量到的是完整管線成本
    resize(w, h, 1); frame(0); MAIN.getImageData(0, 0, 1, 1); const t0 = performance.now();
    for (let i = 0; i < n; i++) { frame(TOTAL * i / n); MAIN.getImageData(0, 0, 1, 1); }
    return (performance.now() - t0) / n; } };
boot();
