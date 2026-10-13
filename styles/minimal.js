// @fonts https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=Noto+Sans+TC:wght@400;700;900&display=swap
/* 風格包：極簡品牌 minimal — 米白底、單一主色、大字排版與大量留白 */
const STYLE = {
  name: 'minimal', light: true,
  fonts: {
    sans: '"Inter","Noto Sans TC","Noto Sans CJK TC","PingFang TC","Microsoft JhengHei",sans-serif',
    display: '"Inter","Noto Sans TC","Noto Sans CJK TC",sans-serif',
    mono: 'ui-monospace,"SF Mono",Menlo,monospace',
  },
  c: { bg: '#f4f1ea', fg: '#16161a', mute: '#7a7770', a1: '#e8462f', a2: '#16161a', a3: '#b9b3a6',
       line: 'rgba(22,22,26,.1)', card: '#ffffff', cardLine: 'rgba(22,22,26,.12)', flash: '#ffffff' },
  post: { bloom: 0, vignette: 0, grain: .035 },
  trans: ['wipe', 'push', 'iris'],
  music: { bpm: 90, kit: 'soft', lead: 'piano', leadWave: 'sine', leadGain: .11, leadLen: 3, leadCut: 3200, leadFrom: .4,
    arp: [0, 2, 1, 3], bassWave: 'sine', bassCut: 600, bassPat: [0, 8], padWave: 'triangle', padCut: 1400, padGain: .05,
    // Dmaj9 → Bm7 → Gmaj7 → A6
    chords: [[62, 66, 69, 76], [59, 62, 66, 69], [55, 59, 62, 66], [57, 61, 64, 66]] },
  bg(time) {
    ctx.fillStyle = this.c.bg; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = this.c.line; ctx.lineWidth = 1;
    const m = MIN * .035; ctx.strokeRect(m, m, W - 2 * m, H - 2 * m);
  },
};
