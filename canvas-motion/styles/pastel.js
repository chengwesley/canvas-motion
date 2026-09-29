// @fonts https://fonts.googleapis.com/css2?family=Nunito:wght@600;800;900&family=M+PLUS+Rounded+1c:wght@500;700;800&display=swap
/* 風格包：柔和漸層 pastel — 淡紫粉藍、飄動色塊、圓角玻璃卡，適合活動邀請、社群貼文、輕鬆的公告 */
const STYLE = {
  name: 'pastel', light: true,
  fonts: {
    sans: '"Nunito","M PLUS Rounded 1c","Noto Sans TC","Noto Sans CJK TC","PingFang TC",sans-serif',
    display: '"Nunito","M PLUS Rounded 1c","Noto Sans CJK TC",sans-serif',
    mono: '"Nunito",ui-rounded,sans-serif',
  },
  c: { bg: '#fbf5ff', fg: '#2d2440', mute: '#7d7196', a1: '#ff6fae', a2: '#6f93ff', a3: '#3cc9a4',
       line: 'rgba(45,36,64,.08)', card: 'rgba(255,255,255,.72)', cardLine: 'rgba(255,255,255,.95)', flash: '#ffffff' },
  cardShadow: 'rgba(111,147,255,.18)', cardR: .035,
  post: { bloom: 0, vignette: 0, grain: .03 },
  trans: ['iris', 'zoom', 'push'],
  music: { bpm: 104, kit: 'half', snare: 'clap', lead: 'bell', leadWave: 'sine', leadGain: .1, leadLen: 1.8, leadCut: 4000, leadOct: 2,
    arp: [0, 2, 3, 2, 1, 3], bassWave: 'sine', bassCut: 600, bassPat: [0, 8, 11], padWave: 'triangle', padCut: 1800, padGain: .04, delaySend: .38,
    // Fmaj7 → Em7 → Dm9 → G6（輕快、甜）
    chords: [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 64], [55, 59, 62, 64]] },
  bg(time) {
    ctx.fillStyle = this.c.bg; ctx.fillRect(0, 0, W, H);
    const blobs = [[.18, .22, this.c.a1, .8], [.82, .3, this.c.a2, .7], [.55, .88, this.c.a3, .6], [.1, .85, this.c.a2, .45]];
    blobs.forEach(([x, y, c, r], i) => glow(W * (x + .05 * Math.sin(time * .3 + i * 1.7)), H * (y + .05 * Math.cos(time * .25 + i)), MIN * r, c, .5));
  },
};
