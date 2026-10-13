// @fonts https://fonts.googleapis.com/css2?family=Nunito:wght@600;800;900&family=Zen+Maru+Gothic:wght@500;700;900&display=swap
/* 風格包：溫暖手作 warm — 暖色紙感、圓體、抖動線條、彈性緩動 */
const STYLE = {
  name: 'warm', light: true,
  fonts: {
    sans: '"Nunito","Zen Maru Gothic","Noto Sans TC","Noto Sans CJK TC","PingFang TC",sans-serif',
    display: '"Zen Maru Gothic","Nunito","Noto Sans CJK TC",sans-serif',
    mono: '"Nunito",ui-monospace,monospace',
  },
  c: { bg: '#f6e9d7', fg: '#3b2a20', mute: '#8c7361', a1: '#e07a4f', a2: '#5c9e7a', a3: '#e8b64c',
       line: 'rgba(59,42,32,.14)', card: '#fff8ee', cardLine: 'rgba(59,42,32,.18)', flash: '#fff8ee' },
  post: { bloom: 0, vignette: .12, grain: .07 },
  trans: ['iris', 'push', 'fade'],
  music: { bpm: 100, kit: 'half', snare: 'snare', lead: 'pluck', leadWave: 'triangle', leadLen: .9, leadCut: 3000, leadGain: .1,
    arp: [0, 2, 1, 2, 3, 2, 1, 2], bassWave: 'triangle', bassCut: 700, bassPat: [0, 6, 8, 14], padGain: .03, padWave: 'triangle',
    // G → C → Em → D
    chords: [[55, 59, 62, 67], [60, 64, 67, 72], [52, 55, 59, 64], [50, 54, 57, 62]] },
  bg(time) {
    const p = cached('warm-paper', W, H, (x, w, h) => {
      x.fillStyle = '#f6e9d7'; x.fillRect(0, 0, w, h); const r = rng(3);
      for (let i = 0; i < 1400; i++) { x.fillStyle = `rgba(120,80,40,${r() * .05})`; x.fillRect(r() * w, r() * h, 1 + r() * 2, 1 + r() * 2); }
    });
    ctx.drawImage(p, 0, 0, W, H);
    ctx.globalAlpha = .18;
    circle(W * (.12 + .02 * Math.sin(time * .4)), H * .2, MIN * .22, this.c.a3);
    circle(W * (.9 + .02 * Math.cos(time * .33)), H * .85, MIN * .28, this.c.a2);
    ctx.globalAlpha = 1;
  },
};
/** 手繪抖動線（warm 專用輔助） */
function wobble(x1, y1, x2, y2, col, lw = 3, t = 0) {
  const n = 12; ctx.beginPath();
  for (let i = 0; i <= n; i++) { const k = i / n, j = noise1(i * 1.7 + Math.floor(t * 8) * 3.1) * lw * .9;
    const x = lerp(x1, x2, k) + j, y = lerp(y1, y2, k) - j; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
  ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
}
