// @fonts https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@500;600&family=Noto+Sans+TC:wght@400;700;900&display=swap
/* 風格包：資料視覺 data — 中性深底、語意色、等寬數字、圖表生長 */
const STYLE = {
  name: 'data',
  fonts: {
    sans: '"IBM Plex Sans","Noto Sans TC","Noto Sans CJK TC","PingFang TC","Microsoft JhengHei",sans-serif',
    display: '"IBM Plex Sans","Noto Sans TC","Noto Sans CJK TC",sans-serif',
    mono: '"IBM Plex Mono","Noto Sans Mono CJK TC",ui-monospace,monospace',
  },
  // a1 = 正向／重點、a2 = 中性比較、a3 = 警示
  c: { bg: '#11151c', fg: '#e8edf4', mute: '#7d8898', a1: '#3ec7a0', a2: '#5b9cf0', a3: '#f0a35b',
       line: 'rgba(232,237,244,.08)', card: 'rgba(232,237,244,.04)', cardLine: 'rgba(232,237,244,.1)', flash: '#e8edf4' },
  post: { bloom: .08, vignette: .35, grain: .025 },
  trans: ['push', 'fade', 'wipe'],
  music: { bpm: 110, kit: 'four', snare: 'snare', lead: 'pluck', leadWave: 'square', leadGain: .04, leadCut: 1800,
    bassWave: 'triangle', bassCut: 500, padGain: .035, delaySend: .2,
    // Am7 → Fmaj7 → C → G
    chords: [[57, 60, 64, 67], [53, 57, 60, 64], [60, 64, 67, 72], [55, 59, 62, 67]] },
  bg() {
    const g = cached('data-bg', W, H, (x, w, h) => {
      x.fillStyle = '#11151c'; x.fillRect(0, 0, w, h); const s = Math.min(w, h) * .05;
      x.fillStyle = 'rgba(232,237,244,.07)';
      for (let yy = s / 2; yy < h; yy += s) for (let xx = s / 2; xx < w; xx += s) x.fillRect(xx, yy, 1.5, 1.5);
    });
    ctx.drawImage(g, 0, 0, W, H);
  },
};
/** 長條圖生長（data 專用輔助）：vals 數值陣列，p 0→1 */
function bars(x, y, w, h, vals, p, o = {}) {
  const n = vals.length, gap = w / n * .28, bw = w / n - gap, mx = o.max ?? Math.max(...vals);
  vals.forEach((v, i) => { const k = E.out(clamp(p * 1.4 - i * .4 / n)), bh = h * v / mx * k;
    fillRR(x + i * (bw + gap) + gap / 2, y + h - bh, bw, bh, Math.min(bw * .15, 6), o.colors ? o.colors[i] : (i === o.hi ? STYLE.c.a1 : rgba(STYLE.c.a2, .75))); });
}
