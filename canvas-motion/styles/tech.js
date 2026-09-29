// @fonts https://fonts.googleapis.com/css2?family=Geist:wght@400;600;800&family=Geist+Mono:wght@400;600&family=Noto+Sans+TC:wght@400;700;900&display=swap
/* 風格包：矽谷科技 tech — 深黑底、薄荷／藍／紫漸層、透視網格、bloom */
const STYLE = {
  name: 'tech',
  fonts: {
    sans: '"Geist","Noto Sans TC","Noto Sans CJK TC","PingFang TC","Microsoft JhengHei",sans-serif',
    display: '"Geist","Noto Sans TC","Noto Sans CJK TC","PingFang TC",sans-serif',
    mono: '"Geist Mono","JetBrains Mono","Noto Sans Mono CJK TC",ui-monospace,monospace',
  },
  c: { bg: '#07080c', fg: '#f3f5fa', mute: '#8b93a7', a1: '#5ef2c6', a2: '#5b8cff', a3: '#b07bff',
       line: 'rgba(255,255,255,.08)', card: 'rgba(255,255,255,.045)', cardLine: 'rgba(255,255,255,.12)', flash: '#dffcf3' },
  post: { bloom: .32, vignette: .55, grain: .05 },
  trans: ['push', 'wipe', 'zoom', 'glitch'],
  music: { bpm: 120, kit: 'four', snare: 'clap', lead: 'pluck', leadWave: 'triangle', leadCut: 2400, bassWave: 'sawtooth',
    // Cmaj7 → Am7 → Fmaj7 → G6（MIDI，60 = C4）
    chords: [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 64]] },
  bg(time, pulse) {
    // 漸層與光暈烘焙成低解析度圖層（便宜），再以微幅漂移製造呼吸感
    const L = cached('tech-bg', W / 4, H / 4, (x, w, h) => {
      const gr = x.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#0a0c14'); gr.addColorStop(1, '#040508');
      x.fillStyle = gr; x.fillRect(0, 0, w, h);
      for (const [px, py, r, col, al] of [[.25, .3, .9, this.c.a2, .16], [.78, .72, .8, this.c.a3, .12]]) {
        const g = x.createRadialGradient(w * px, h * py, 0, w * px, h * py, Math.min(w, h) * r);
        g.addColorStop(0, rgba(col, al)); g.addColorStop(.35, rgba(col, al * .35)); g.addColorStop(1, rgba(col, 0));
        x.fillStyle = g; x.fillRect(0, 0, w, h);
      }
    });
    const dx = Math.sin(time * .21) * W * .03, dy = Math.cos(time * .17) * H * .03;
    ctx.drawImage(L, -W * .05 + dx, -H * .05 + dy, W * 1.1, H * 1.1);
    const hz = H * .62, n = 18, sp = (time * .35) % 1;
    ctx.save(); ctx.globalAlpha = .55 + pulse * .25; ctx.strokeStyle = this.c.line; ctx.lineWidth = 1;
    for (let i = 0; i < n; i++) { const k = (i + sp) / n, y = hz + (H - hz) * k * k; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    for (let i = -10; i <= 10; i++) { ctx.beginPath(); ctx.moveTo(W / 2 + i * W * .02, hz); ctx.lineTo(W / 2 + i * W * .16, H); ctx.stroke(); }
    ctx.restore();
    const fade = ctx.createLinearGradient(0, hz - H * .05, 0, hz + H * .12);
    fade.addColorStop(0, 'rgba(7,8,12,1)'); fade.addColorStop(1, 'rgba(7,8,12,0)'); ctx.fillStyle = fade; ctx.fillRect(0, hz - H * .05, W, H * .17);
  },
};
