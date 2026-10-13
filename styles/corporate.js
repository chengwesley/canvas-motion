// @fonts https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap
/* 風格包：企業簡報 corporate — 白底、品牌藍、乾淨卡片陰影，適合內部提案、客戶簡報、SaaS 產品介紹 */
const STYLE = {
  name: 'corporate', light: true,
  fonts: {
    sans: '"Inter","Noto Sans TC","Noto Sans CJK TC","PingFang TC","Microsoft JhengHei",sans-serif',
    display: '"Inter","Noto Sans TC","Noto Sans CJK TC","PingFang TC",sans-serif',
    mono: '"Inter","Noto Sans TC",ui-monospace,monospace',
  },
  c: { bg: '#f5f8fc', fg: '#0f1b2d', mute: '#5b6b82', a1: '#1f5eff', a2: '#00a79d', a3: '#ff9f1c',
       line: 'rgba(15,27,45,.08)', card: '#ffffff', cardLine: 'rgba(15,27,45,.08)', flash: '#ffffff' },
  cardShadow: 'rgba(15,27,45,.10)', cardR: .02,
  post: { bloom: 0, vignette: 0, grain: 0 },
  trans: ['push', 'wipe', 'fade'],
  music: { bpm: 108, kit: 'half', snare: 'clap', lead: 'pluck', leadWave: 'triangle', leadGain: .08, leadCut: 2800, leadLen: 1,
    arp: [0, 2, 1, 3, 2, 1, 3, 2], bassWave: 'triangle', bassCut: 650, bassPat: [0, 6, 8, 14], padWave: 'triangle', padCut: 1600, padGain: .035,
    // C → G/B → Am → F（明亮、正向）
    chords: [[60, 64, 67, 72], [59, 62, 67, 71], [57, 60, 64, 69], [53, 57, 60, 65]] },
  bg(time) {
    const L = cached('corp-bg', W / 3, H / 3, (x, w, h) => {
      x.fillStyle = '#f5f8fc'; x.fillRect(0, 0, w, h);
      const g = x.createLinearGradient(0, 0, w, h); g.addColorStop(0, 'rgba(31,94,255,.10)'); g.addColorStop(.5, 'rgba(31,94,255,0)');
      x.fillStyle = g; x.fillRect(0, 0, w, h);
      x.fillStyle = 'rgba(0,167,157,.07)'; x.beginPath(); x.moveTo(w, h * .55); x.lineTo(w, h); x.lineTo(w * .55, h); x.closePath(); x.fill();
    });
    ctx.drawImage(L, 0, 0, W, H);
    const m = MIN * .035, p = (time * .08) % 1;
    ctx.fillStyle = this.c.a1; ctx.fillRect(0, 0, W * lerp(.18, .26, .5 + .5 * Math.sin(time * .6)), MIN * .006);
    ctx.fillStyle = rgba(this.c.fg, .06); for (let i = 0; i < 6; i++) circle(W - m - i * MIN * .018, H - m, MIN * .004, i === Math.floor(p * 6) ? this.c.a1 : rgba(this.c.fg, .15));
  },
};
