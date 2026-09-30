// @fonts https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:ital,wght@0,700;1,700&family=Noto+Sans+TC:wght@700;900&display=swap
/* 風格包：美漫復古 amcomic — 新聞紙底、四色印刷（紅藍黃黑）、Ben-Day 網點、厚描邊，適合英雄、活動宣傳、熱鬧有趣 */
const STYLE = {
  name: 'amcomic', light: true,
  fonts: {
    sans: '"Comic Neue","Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif',
    display: '"Bangers","Noto Sans TC","PingFang TC",sans-serif',
    mono: '"Comic Neue",ui-monospace,monospace',
  },
  c: { bg: '#f2e8d0', fg: '#1a1a1a', mute: '#5a4f3c', a1: '#e3242b', a2: '#1f5fae', a3: '#f7d117',
       line: 'rgba(26,26,26,.85)', card: '#fffdf4', cardLine: '#1a1a1a', flash: '#ffffff' },
  cardR: 0, cardLw: 4,
  post: { bloom: 0, vignette: .15, grain: .05 },
  trans: ['cut', 'wipe', 'flash', 'push'],
  music: { bpm: 128, kit: 'four', snare: 'clap', lead: 'stab', leadWave: 'square', leadGain: .05, leadLen: .6, leadCut: 2600, leadFrom: .5,
    arp: [0, 2, 3, 2, 0, 3, 2, 1], bassWave: 'square', bassCut: 600, bassPat: [0, 4, 8, 12, 14], pad: false,
    // C → G → Am → F（明亮、英雄）
    chords: [[60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]] },
  bg(time, pulse) {
    // 新聞紙：底色＋很淡的洋紅網點（網角 75°），模擬印刷紙面
    ctx.fillStyle = this.c.bg; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.globalAlpha = .12;
    fxHalftone(0, 0, W, H, this.c.a1, (u, v) => .25 + .25 * v, { key: 'am-paper', angle: 75, cell: .012 });
    ctx.restore();
  },
};
