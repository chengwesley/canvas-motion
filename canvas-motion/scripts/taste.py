#!/usr/bin/env python3
"""動態品味檢查：量「畫面有沒有在動、動得對不對」，抓出自動檢查抓不到的無趣。只提醒，不擋交付。

用法：python3 taste.py <專案> [--fps 24] [--size 256x144]
輸出：<專案>/sheets/motion.png（動作曲線：灰線是拍、藍線是 energy、橘點是高光），並印出：
  - 靜止段落：超過 1 秒幾乎沒變化（最後一小節收尾除外）
  - 開場鉤子：第 1 秒動作量太低
  - energy 與動作量：音樂變強、畫面卻沒有變強
  - 對拍：每幕最大的動作沒落在拍點附近
  - 高光：hero 那一拍沒有明顯的動作高峰
  - 動的範圍：整幕只有一小塊在動（像投影片）
動作量＝相鄰兩格的平均亮度差（0–255），在小尺寸、關掉顆粒下量，轉場期間不計。
"""
import argparse, statistics as st, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401
from PIL import Image, ImageDraw  # noqa: E402
from build import build  # noqa: E402
from _browser import open_page  # noqa: E402

STATIC = .35      # 動作量低於這個值算「幾乎沒動」（依畫面對比度等比調低，暗場景不會誤報）
clamp01 = lambda v, a, b: max(a, min(b, v))
MIN_COVER = .2    # 整幕動過的像素比例低於這個值算「只有一小塊在動」

JS = r"""([w, h, fps]) => {
  if (STYLE.post) STYLE.post.grain = 0;
  __cm.resize(w, h, 1);
  const n = Math.floor(__cm.TOTAL * fps), SCn = __cm.SC, skip = [];
  SCn.forEach((s, i) => { if (!i) return; const p = SCn[i - 1];
    skip.push(p.trans === 'cut' ? [s.start - .5 / fps, s.start + 1.5 / fps] : [s.start - __cm.TD / 2 - .5 / fps, s.start + __cm.TD / 2 + 1.5 / fps]); });
  const masks = SCn.map(() => new Uint8Array(w * h)), d = [], ok = [], con = [];
  let prev = null; const hist = [], lagN = Math.max(1, Math.round(fps / 4));   // 動的範圍：跟 0.25 秒前比，慢而大的移動也算
  for (let k = 0; k <= n; k++) {
    const t = Math.min(k / fps, __cm.TOTAL - 1e-3); __cm.frame(t);
    const px = MAIN.getImageData(0, 0, w, h).data, lum = new Float32Array(w * h);
    let m1 = 0, m2 = 0;
    for (let j = 0, q = 0; j < lum.length; j++, q += 4) { const L = px[q] * .299 + px[q + 1] * .587 + px[q + 2] * .114; lum[j] = L; m1 += L; m2 += L * L; }
    m1 /= lum.length; con.push(Math.sqrt(Math.max(0, m2 / lum.length - m1 * m1)));
    const keep = !skip.some(([a, b]) => t >= a && t <= b);
    let si = 0; for (let i = SCn.length - 1; i >= 0; i--) if (t >= SCn[i].start - 1e-6) { si = i; break; }
    const old = hist.length >= lagN ? hist[hist.length - lagN] : null;
    const keepOld = keep && !skip.some(([a, b]) => t - lagN / fps <= b && t >= a) && t - lagN / fps >= SCn[si].start;
    if (prev) { let sum = 0; const m = masks[si];
      for (let j = 0; j < lum.length; j++) { sum += Math.abs(lum[j] - prev[j]); if (old && keepOld && Math.abs(lum[j] - old[j]) > 20) m[j] = 1; }
      d.push(sum / lum.length); } else d.push(0);
    ok.push(keep && k > 0); prev = lum; hist.push(lum); if (hist.length > lagN) hist.shift();
  }
  return { d, ok, con, cover: masks.map(m => m.reduce((a, b) => a + b, 0) / m.length), SC: SCn, BEAT: __cm.BEAT, BAR: __cm.BAR, TOTAL: __cm.TOTAL };
}"""


def analyze(r, fps):
    d, ok, SC, BEAT, BAR, TOTAL = r["d"], r["ok"], r["SC"], r["BEAT"], r["BAR"], r["TOTAL"]
    tt = [k / fps for k in range(len(d))]
    warns, rows = [], []
    valid = [v for v, o in zip(d, ok) if o]
    med_all = st.median(valid) if valid else 0

    # 靜止段落（最後一小節是收束，允許停住）
    run0 = None
    con = r.get("con") or [60] * len(d)
    # dark, low-contrast shots (cinema, night) change fewer luminance levels per frame for the same motion: scale the bar by contrast
    thr = lambda k: STATIC * clamp01(con[k] / 55, .3, 1)
    for k, (t, v, o) in enumerate(zip(tt, d, ok)):
        still = o and v < thr(k) and t < TOTAL - BAR
        if still and run0 is None:
            run0 = t
        if (not still or k == len(d) - 1) and run0 is not None:
            if t - run0 > 1.0:
                warns.append(f"{run0:.1f}–{t:.1f}s 有 {t - run0:.1f} 秒幾乎沒動：加一個次要動作（呼吸、鏡頭推移、背景元素），或把這段剪短")
            run0 = None

    # 開場鉤子
    hook = [v for t, v, o in zip(tt, d, ok) if o and t < 1.0]
    if hook and med_all and st.mean(hook) < med_all * .5:
        warns.append(f"開場第 1 秒動作量 {st.mean(hook):.2f}，不到全片中位數的一半：第一秒就要有抓住目光的動作")

    motion = []
    for i, s in enumerate(SC):
        end = s["start"] + s["dur"] - (BAR if i == len(SC) - 1 else 0)   # 最後一小節是收尾，不算進動作量
        idx = [k for k, t in enumerate(tt) if s["start"] <= t < end and ok[k]]
        vals = [d[k] for k in idx]
        m = st.mean(vals) if vals else 0
        motion.append(m)
        cover = r["cover"][i]
        info = {"fn": s["fn"], "energy": s["energy"], "motion": m, "cover": cover, "hero": "—"}
        if vals:
            kmax = max(idx, key=lambda k: d[k])
            off = ((tt[kmax] - s["start"]) / BEAT) % 1
            off = off - 1 if off > .5 else off   # 距最近一拍的拍數，負 = 拍前
            if not -.15 <= off <= .35 and d[kmax] > STATIC * 3:
                warns.append(f"{s['fn']}：最大的動作在 {tt[kmax]:.2f}s，離拍點 {off:+.2f} 拍；把衝擊對到拍上，畫面才會跟音樂黏在一起")
        if cover < MIN_COVER:
            warns.append(f"{s['fn']}：整幕只有 {cover:.0%} 的畫面動過，看起來像靜態版面（投影片）；讓主體變大、移動、變形，或讓鏡頭動起來")
        h = s.get("hero")
        if h and isinstance(h.get("beat"), (int, float)) and vals:
            ht = s["start"] + h["beat"] * BEAT
            win = [d[k] for k in idx if ht - BEAT * .5 <= tt[k] <= ht + BEAT * .75]
            q75 = sorted(vals)[int(len(vals) * .75)]
            peak = max(win) if win else 0
            good = peak >= max(q75, st.median(vals) * 1.5, STATIC * 2)
            info["hero"] = f"{'✓' if good else '!'} {ht:.1f}s"
            if not good:
                warns.append(f"{s['fn']}：高光「{h.get('what', '')}」（{ht:.1f}s）附近沒有明顯的動作高峰；高光要是整幕最有力的一瞬間")
        rows.append(info)

    for a, b in zip(rows, rows[1:]):
        if b["energy"] - a["energy"] >= .15 and b["motion"] < a["motion"] * .8:
            warns.append(f"{a['fn']} → {b['fn']}：energy {a['energy']} → {b['energy']} 變強，動作量卻從 {a['motion']:.2f} 降到 {b['motion']:.2f}；畫面強度要跟著音樂走")
    if len(rows) >= 3:
        hi = max(rows, key=lambda x: x["energy"])
        if hi["motion"] < st.median(motion):
            warns.append(f"energy 最高的 {hi['fn']} 動作量低於各幕中位數：高潮沒有演出來")
    return rows, warns, tt


def chart(r, rows, tt, path, fps):
    d, SC, BEAT, TOTAL = r["d"], r["SC"], r["BEAT"], r["TOTAL"]
    from sheet import font
    Wd, Hd, pad = 1400, 360, 40
    im = Image.new("RGB", (Wd, Hd), (22, 23, 28)); g = ImageDraw.Draw(im); f = font(14)
    X = lambda t: pad + (Wd - 2 * pad) * t / TOTAL
    top = max(max(d[1:] or [1]), STATIC * 4)
    Y = lambda v: Hd - pad - (Hd - 2 * pad) * min(1, v / top)
    b = 0
    while b * BEAT < TOTAL:
        g.line([(X(b * BEAT), pad), (X(b * BEAT), Hd - pad)], fill=(48, 50, 58) if b % 4 else (78, 80, 92)); b += 1
    g.line([(pad, Y(STATIC)), (Wd - pad, Y(STATIC))], fill=(90, 60, 60))
    for s in SC:
        g.line([(X(s["start"]), pad - 10), (X(s["start"]), Hd - pad)], fill=(150, 150, 165), width=2)
        g.text((X(s["start"]) + 4, pad - 30), s["fn"], fill=(210, 210, 220), font=f)
        e = Hd - pad - (Hd - 2 * pad) * s["energy"]
        g.line([(X(s["start"]), e), (X(s["start"] + s["dur"]), e)], fill=(90, 140, 255), width=2)
        h = s.get("hero")
        if h and isinstance(h.get("beat"), (int, float)):
            ht = s["start"] + h["beat"] * BEAT
            g.ellipse([X(ht) - 6, pad - 6, X(ht) + 6, pad + 6], fill=(255, 150, 60))
    pts = [(X(t), Y(v)) for t, v, o in zip(tt, d, r["ok"])]
    for (p0, p1), o in zip(zip(pts, pts[1:]), r["ok"][1:]):
        g.line([p0, p1], fill=(94, 242, 198) if o else (70, 70, 80), width=2)
    g.text((pad, Hd - pad + 10), "綠：動作量　藍：energy　橘：高光　紅線：幾乎沒動　灰：拍（亮＝小節）", fill=(170, 170, 180), font=f)
    im.save(path)


def run(project, fps=24, size="256x144"):
    w, h = map(int, size.split("x"))
    proj = Path(project).resolve()
    html = build(proj, quiet=True)
    with open_page(html) as pg:
        r = pg.evaluate(JS, [w, h, fps])
    rows, warns, tt = analyze(r, fps)
    out = proj / "sheets"; out.mkdir(exist_ok=True)
    chart(r, rows, tt, out / "motion.png", fps)
    print("| 幕 | energy | 動作量 | 動的範圍 | 高光 |\n|---|---|---|---|---|")
    for x in rows:
        print(f"| {x['fn']} | {x['energy']} | {x['motion']:.2f} | {x['cover']:.0%} | {x['hero']} |")
    print(f"✓ 動作曲線 {out / 'motion.png'}")
    for m in warns:
        print(f"! {m}")
    if not warns:
        print("✓ 動態品味：沒有發現問題（仍要用自評表看一次）")
    return warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--size", default="256x144")
    a = ap.parse_args()
    run(a.project, a.fps, a.size)


if __name__ == "__main__":
    main()
