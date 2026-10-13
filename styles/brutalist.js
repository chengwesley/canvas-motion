// @fonts https://fonts.googleapis.com/css2?family=Archivo+Black&family=Space+Mono:wght@700&family=Noto+Sans+TC:wght@900&display=swap
/* 風格包：粗野主義 brutalist — 螢光黃底、純黑粗框、硬切換、快節奏，適合活動倒數、潮流宣傳、社群短影音 */
const STYLE = {
  name: 'brutalist', light: true, noGlow: true,
  fonts: {
    sans: '"Archivo Black","Noto Sans TC","Noto Sans CJK TC","PingFang TC",sans-serif',
    display: '"Archivo Black","Noto Sans TC","Noto Sans CJK TC",sans-serif',
    mono: '"Space Mono",ui-monospace,monospace',
  },
  c: { bg: '#ffe600', fg: '#0a0a0a', mute: '#3d3a1a', a1: '#0a0a0a', a2: '#ff3b00', a3: '#0038ff',
       line: 'rgba(10,10,10,.9)', card: '#ffffff', cardLine: '#0a0a0a', flash: '#0a0a0a' },
  cardR: 0, cardLw: 4,
  post: { bloom: 0, vignette: 0, grain: .05 },
  trans: ['cut', 'flash', 'push', 'glitch'],
  music: { bpm: 128, kit: 'four', snare: 'snare', lead: 'stab', leadWave: 'square', leadGain: .05, leadLen: .6, leadCut: 2200, leadFrom: .5,
    arp: [0, 0, 2, 0, 3, 0, 2, 1], bassWave: 'sawtooth', bassCut: 700, bassPat: [0, 2, 4, 6, 8, 10, 12, 14], pad: false, delaySend: .12,
    // Em → C → G → D（衝、直接）
    chords: [[52, 55, 59, 64], [48, 52, 55, 60], [55, 59, 62, 67], [50, 54, 57, 62]] },
  bg(time, pulse) {
    ctx.fillStyle = this.c.bg; ctx.fillRect(0, 0, W, H);
    const m = MIN * .03, b = MIN * .012;
    ctx.fillStyle = this.c.fg; ctx.fillRect(m, m, W - 2 * m, b); ctx.fillRect(m, H - m - b, W - 2 * m, b);
    const tick = Math.floor(time / BEAT);
    setFont(MIN * .022, 700, 'mono'); ctx.textBaseline = 'middle';
    ctx.textAlign = 'left'; ctx.fillText('●REC ' + String(tick).padStart(4, '0'), m, m + b + MIN * .03);
    ctx.textAlign = 'right'; ctx.fillText(`${BPM} BPM`, W - m, H - m - b - MIN * .03);
    ctx.save(); ctx.translate(W - m - MIN * .05, m + b + MIN * .07); ctx.rotate(tick * Math.PI / 4);
    for (let k = 0; k < 4; k++) { ctx.rotate(Math.PI / 4); ctx.fillRect(-MIN * .03, -MIN * .005, MIN * .06, MIN * .01); } ctx.restore();
  },
};
