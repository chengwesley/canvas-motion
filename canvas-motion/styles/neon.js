// @fonts https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Share+Tech+Mono&family=Noto+Sans+TC:wght@700;900&display=swap
/* 風格包：霓虹復古 neon — 黑底霓虹粉青、合成波太陽與網格、掃描線、glitch */
const STYLE = {
  name: 'neon',
  fonts: {
    sans: '"Orbitron","Noto Sans TC","Noto Sans CJK TC","PingFang TC",sans-serif',
    display: '"Orbitron","Noto Sans TC","Noto Sans CJK TC",sans-serif',
    mono: '"Share Tech Mono",ui-monospace,monospace',
  },
  c: { bg: '#07020f', fg: '#fdf2ff', mute: '#9a7fb8', a1: '#ff3fa4', a2: '#2ff3ff', a3: '#ffd23f',
       line: 'rgba(255,63,164,.35)', card: 'rgba(47,243,255,.05)', cardLine: 'rgba(47,243,255,.4)', flash: '#ff3fa4' },
  post: { bloom: .5, vignette: .6, grain: .06 },
  trans: ['glitch', 'flash', 'push'],
  music: { bpm: 110, kit: 'four', snare: 'snare', lead: 'arp', leadWave: 'sawtooth', leadGain: .055, leadCut: 1800, leadFrom: .5,
    arp: [0, 1, 2, 3, 2, 1, 0, 2], bassWave: 'sawtooth', bassCut: 520, bassPat: [0, 2, 4, 6, 8, 10, 12, 14], padGain: .04,
    // Am → F → C → G
    chords: [[57, 60, 64, 69], [53, 57, 60, 65], [60, 64, 67, 72], [55, 59, 62, 67]] },
  bg(time, pulse) {
    ctx.fillStyle = this.c.bg; ctx.fillRect(0, 0, W, H);
    const hz = H * pick(.76, .8), sr = MIN * pick(.2, .24), cx = W / 2, cy = hz - sr * .05; // 太陽壓低，避免與前景文字搶
    const sun = cached('neon-sun', sr * 2, sr * 2, (x, w, h) => {
      const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#ffd23f'); g.addColorStop(1, '#ff3fa4');
      x.fillStyle = g; x.beginPath(); x.arc(w / 2, h / 2, w / 2, 0, Math.PI * 2); x.fill();
      x.globalCompositeOperation = 'destination-out';
      for (let i = 0; i < 7; i++) { const yy = h * (.55 + i * .065); x.fillRect(0, yy, w, h * (.012 + i * .005)); }
    });
    glow(cx, cy, sr * 2.2, this.c.a1, .25 + pulse * .12);
    ctx.globalAlpha = .5; ctx.drawImage(sun, cx - sr, cy - sr, sr * 2, sr * 2); ctx.globalAlpha = 1;
    ctx.fillStyle = this.c.bg; ctx.fillRect(0, hz, W, H - hz);
    const sp = (time * .6) % 1; ctx.strokeStyle = this.c.line; ctx.lineWidth = 1.5;
    for (let i = 0; i < 14; i++) { const k = (i + sp) / 14, y = hz + (H - hz) * k * k; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    for (let i = -12; i <= 12; i++) { ctx.beginPath(); ctx.moveTo(cx + i * W * .015, hz); ctx.lineTo(cx + i * W * .14, H); ctx.stroke(); }
    ctx.fillStyle = rgba(this.c.a2, .9); ctx.fillRect(0, hz - 1, W, 2);
  },
  overlay() { // 掃描線
    const s = cached('scan', W, H, (x, w, h) => { x.fillStyle = 'rgba(0,0,0,.22)'; for (let y = 0; y < h; y += 3) x.fillRect(0, y, w, 1); });
    ctx.drawImage(s, 0, 0, W, H);
  },
};
