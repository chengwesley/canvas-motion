// @fonts https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;600&family=Noto+Serif+TC:wght@300;600;900&family=Noto+Sans+TC:wght@400;700&display=swap
/* 風格包：電影感 cinema — 寬銀幕黑邊、青橙調色、低調光、底片顆粒、襯線片名，適合故事短片、品牌形象、預告片 */
const STYLE = {
  name: 'cinema',
  fonts: {
    sans: '"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif',
    display: '"Cormorant Garamond","Noto Serif TC","PMingLiU",serif',
    serif: '"Noto Serif TC","PMingLiU",serif',
    mono: 'ui-monospace,monospace',
  },
  c: { bg: '#07090c', fg: '#f4efe6', mute: '#9aa3ab', a1: '#f0a060', a2: '#4fb3c8', a3: '#e8d5a8',
       line: 'rgba(244,239,230,.1)', card: 'rgba(255,255,255,.05)', cardLine: 'rgba(255,255,255,.14)', flash: '#fff4e0' },
  post: { bloom: .22, vignette: .7, grain: .08 },
  trans: ['cut', 'fade', 'cut', 'flash'],
  letterbox: 2.39,
  music: { bpm: 84, kit: 'half', snare: 'snare', lead: 'pluck', leadWave: 'sine', leadGain: .07, leadLen: 3, leadCut: 1600, leadFrom: .7,
    arp: [0, 2, 1, 3], bassWave: 'sine', bassCut: 300, bassPat: [0, 8], padWave: 'sawtooth', padCut: 700, padGain: .06, delaySend: .35,
    // Dm → Bb → F → C（i–VI–III–VII，史詩電影）
    chords: [[50, 53, 57, 62], [46, 50, 53, 58], [53, 57, 60, 65], [48, 52, 55, 60]] },
  bg(time, pulse) {
    const L = cached('cine-bg', W / 3, H / 3, (x, w, h) => {
      const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#0d1418'); g.addColorStop(1, '#050608');
      x.fillStyle = g; x.fillRect(0, 0, w, h);
    });
    ctx.drawImage(L, 0, 0, W, H);
  },
  // 寬銀幕黑邊畫在最上層（橫式才有；直式影片不加黑邊）＋青橙調色
  overlay(time) { if (!PORT) { fxGrade({ a: .18, vignette: .35 }); fxLetterbox(this.letterbox, 1); } else fxGrade({ a: .18, vignette: .35 }); },
};
