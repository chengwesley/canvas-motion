// @fonts https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700;900&display=swap
/* 風格包：東方水墨 ink — 宣紙、墨色暈染、朱紅印章、遠山，五聲音階配樂，適合節慶、文化主題、品牌典故 */
const STYLE = {
  name: 'ink', light: true,
  fonts: {
    sans: '"Noto Serif TC","Noto Serif CJK TC","Songti TC","PMingLiU",serif',
    display: '"Noto Serif TC","Noto Serif CJK TC","Songti TC",serif',
    mono: '"Noto Serif TC","Noto Serif CJK TC",serif',
  },
  c: { bg: '#efe7d6', fg: '#1d1b18', mute: '#6e675b', a1: '#b3261e', a2: '#2f3a34', a3: '#8a7b5c',
       line: 'rgba(29,27,24,.14)', card: 'rgba(250,246,236,.7)', cardLine: 'rgba(29,27,24,.35)', flash: '#1d1b18' },
  cardR: .006,
  post: { bloom: 0, vignette: .18, grain: .06 },
  trans: ['fade', 'iris', 'wipe'],
  music: { bpm: 76, kit: 'none', lead: 'guzheng', leadWave: 'triangle', leadGain: .11, leadLen: 2.2, leadCut: 2600, leadFrom: .3,
    arp: [0, 2, 4, 3, 1, 4, 2, 3], bassWave: 'sine', bassCut: 400, bassPat: [0], padWave: 'sine', padCut: 900, padGain: .05, delaySend: .42, delayFb: .4,
    // D 宮五聲音階的不同組合（每個陣列 5 音）
    chords: [[62, 64, 66, 69, 71], [57, 59, 62, 64, 66], [59, 62, 64, 66, 69], [55, 57, 62, 64, 69]] },
  bg(time) {
    const L = cached('ink-bg', W / 2, H / 2, (x, w, h) => {
      x.fillStyle = '#efe7d6'; x.fillRect(0, 0, w, h); const r = rng(11);
      for (let i = 0; i < 900; i++) { x.fillStyle = `rgba(90,70,40,${r() * .05})`; x.fillRect(r() * w, r() * h, 1 + r() * 3, 1); }
      [[.85, .15, .45, .06], [.1, .9, .5, .08], [.5, .5, .7, .03]].forEach(([px, py, rr, al]) => {
        const g = x.createRadialGradient(w * px, h * py, 0, w * px, h * py, Math.min(w, h) * rr);
        g.addColorStop(0, `rgba(29,27,24,${al})`); g.addColorStop(1, 'rgba(29,27,24,0)'); x.fillStyle = g; x.fillRect(0, 0, w, h);
      });
      [[.8, .1, .16], [.86, .05, .24]].forEach(([base, amp, al], k) => { // 遠山
        x.beginPath(); x.moveTo(0, h);
        for (let i = 0; i <= 80; i++) { const xx = w * i / 80; x.lineTo(xx, h * (base - amp * (.5 + .5 * noise1(i * .09 + k * 7)) - amp * .6 * Math.max(0, noise1(i * .03 + k * 3)))); }
        x.lineTo(w, h); x.closePath(); x.fillStyle = `rgba(47,58,52,${al})`; x.fill();
      });
    });
    ctx.drawImage(L, 0, 0, W, H);
    const s = MIN * .06, sx = W - MIN * .07 - s, sy = H - MIN * .07 - s; // 印章
    fillRR(sx, sy, s, s, s * .08, rgba(this.c.a1, .85));
    ctx.strokeStyle = 'rgba(239,231,214,.8)'; ctx.lineWidth = s * .05; ctx.strokeRect(sx + s * .14, sy + s * .14, s * .72, s * .72);
  },
};
