// @fonts https://fonts.googleapis.com/css2?family=Chiron+Hei+HK:wght@700;900&family=Noto+Serif+HK:wght@700;900&family=Noto+Sans+HK:wght@500;700;900&display=swap
/* 風格包：港漫 hkcomic — 深藍紫夜色、金色輪廓光、火紅氣勁、厚重旁白框，適合武俠、功夫、熱血對決、史詩感 */
const STYLE = {
  name: 'hkcomic',
  fonts: {
    sans: '"Noto Sans HK","Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif',
    display: '"Chiron Hei HK","Noto Sans HK","Noto Sans TC","PingFang TC",sans-serif',
    serif: '"Noto Serif HK","Noto Serif TC","PMingLiU",serif',
    mono: '"Noto Sans HK",ui-monospace,monospace',
  },
  c: { bg: '#0b1030', fg: '#fff4dc', mute: '#b9a98a', a1: '#ffc940', a2: '#ff6a13', a3: '#7fe8ff',
       line: 'rgba(255,244,220,.12)', card: '#fff8e0', cardLine: '#141414', flash: '#fff6d0' },
  post: { bloom: .28, vignette: .6, grain: .04 },
  trans: ['flash', 'wipe', 'cut', 'zoom'],
  music: { bpm: 96, kit: 'half', snare: 'snare', lead: 'pluck', leadWave: 'sawtooth', leadGain: .06, leadCut: 1800, leadFrom: .6,
    arp: [0, 2, 1, 3, 2, 1, 0, 2], bassWave: 'sawtooth', bassCut: 420, bassPat: [0, 3, 8, 11], padWave: 'sawtooth', padCut: 800,
    // Am → F → G → E（小調、史詩、武俠）
    chords: [[57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67], [52, 56, 59, 64]] },
  bg(time, pulse) {
    // 深夜色＋頂光：大面積暗部，主體靠輪廓光撐起來
    const L = cached('hk-bg', W / 3, H / 3, (x, w, h) => {
      const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#1a0f2e'); g.addColorStop(.6, '#0b1030'); g.addColorStop(1, '#05060f');
      x.fillStyle = g; x.fillRect(0, 0, w, h);
      const r = x.createRadialGradient(w * .5, h * .15, 0, w * .5, h * .15, Math.max(w, h) * .7);
      r.addColorStop(0, 'rgba(255,201,64,.22)'); r.addColorStop(.4, 'rgba(58,30,92,.25)'); r.addColorStop(1, 'rgba(0,0,0,0)');
      x.fillStyle = r; x.fillRect(0, 0, w, h);
    });
    ctx.drawImage(L, -W * .03 + Math.sin(time * .15) * W * .02, -H * .03, W * 1.06, H * 1.06);
  },
};
