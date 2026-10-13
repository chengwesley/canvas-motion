// @fonts https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Noto+Serif+TC:wght@500;700;900&family=Inter:wght@400;600&display=swap
/* 風格包：雜誌編輯 editorial — 米白紙、襯線大標、紅色點綴、欄線，適合品牌故事、人物專訪、年度回顧 */
const STYLE = {
  name: 'editorial', light: true,
  fonts: {
    sans: '"Inter","Noto Sans TC","Noto Sans CJK TC","PingFang TC",sans-serif',
    display: '"Playfair Display","Noto Serif TC","Noto Serif CJK TC","Songti TC",serif',
    mono: '"Inter","Noto Sans TC",sans-serif',
  },
  c: { bg: '#fbf9f4', fg: '#141414', mute: '#77736a', a1: '#c8102e', a2: '#141414', a3: '#9c8f74',
       line: 'rgba(20,20,20,.12)', card: 'rgba(255,255,255,.6)', cardLine: 'rgba(20,20,20,.85)', flash: '#fbf9f4' },
  cardR: 0, cardLw: 1.5,
  post: { bloom: 0, vignette: .06, grain: .05 },
  trans: ['wipe', 'fade', 'push'],
  music: { bpm: 84, kit: 'soft', lead: 'piano', leadWave: 'sine', leadGain: .12, leadLen: 3.5, leadCut: 3000, leadFrom: .35,
    arp: [0, 2, 3, 1], bassWave: 'sine', bassCut: 500, bassPat: [0, 10], padWave: 'sine', padCut: 1200, padGain: .05, delaySend: .35,
    // Fmaj7 → Em7 → Dm7 → Cmaj7（沉穩、敘事感）
    chords: [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]] },
  bg(time) {
    ctx.fillStyle = this.c.bg; ctx.fillRect(0, 0, W, H);
    const m = MIN * .045;
    ctx.fillStyle = this.c.fg; ctx.fillRect(m, m, W - 2 * m, 2); ctx.fillRect(m, H - m, W - 2 * m, 1);
    ctx.fillStyle = this.c.line; for (let k = 1; k < (PORT ? 2 : 4); k++) ctx.fillRect(m + (W - 2 * m) * k / (PORT ? 2 : 4), m + MIN * .02, 1, H - 2 * m - MIN * .04);
    setFont(MIN * .018, 600, 'sans'); ctx.fillStyle = this.c.mute; ctx.textBaseline = 'bottom'; ctx.textAlign = 'right';
    ctx.fillText(String(Math.floor(time / BAR) + 1).padStart(2, '0'), W - m, m - MIN * .008);
    ctx.fillStyle = this.c.a1; ctx.fillRect(m, m - MIN * .016, MIN * .05, MIN * .008);
  },
};
