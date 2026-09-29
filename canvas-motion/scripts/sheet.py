#!/usr/bin/env python3
"""產出橫式＋直式縮圖總覽，用來逐幕檢查版面。

用法：
  python3 sheet.py <專案資料夾>                 # 每幕 2 個時間點（45%、90%）
  python3 sheet.py <專案> --per 3                # 每幕 3 個時間點
  python3 sheet.py <專案> --frac 0.85            # 每幕只看 85% 處（元素都進場後）
  python3 sheet.py <專案> --at 1.2,4.8,9.0       # 指定全片秒數
  python3 sheet.py <專案> --trans                # 另外加上每個轉場中點
  python3 sheet.py <專案> --aspects 16:9,9:16,1:1
輸出：<專案>/sheets/sheet_<比例>.jpg，並印出錯誤、效能（每格毫秒）。
另外自動做文字檢查（--no-textcheck 關閉）：在每個取樣點記錄每段文字的外框，
回報裁切出畫面、超出安全區、文字互相重疊、字級過小、換行後單字成行。轉場中點不檢查。
"""
import argparse, io, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from build import build           # noqa: E402
from _browser import open_page, grab  # noqa: E402

HOOK = r"""(() => { if (window.__tb) return; window.__tb = []; window.__rec = false; const o = _drawText;
  _drawText = function (c, s, x, y, op) { const r = o(c, s, x, y, op);
    if (window.__rec && c === MAIN && String(s).trim()) {
      const al = c.globalAlpha * (op.alpha ?? 1);
      if (al > .6) { const m = c.getTransform(), w = r.w, x0 = op.align === 'center' ? x - w / 2 : op.align === 'right' ? x - w : x;
        const P = [[x0, r.top], [x0 + w, r.bottom]].map(([px, py]) => [m.a * px + m.c * py + m.e, m.b * px + m.d * py + m.f]);
        __tb.push({ s: String(s).split(String.fromCharCode(10)).join(' ').slice(0, 16), x0: Math.min(P[0][0], P[1][0]), x1: Math.max(P[0][0], P[1][0]),
          y0: Math.min(P[0][1], P[1][1]), y1: Math.max(P[0][1], P[1][1]), size: (op.size || fz('body')) * Math.hypot(m.a, m.b),
          orphan: (() => { if (!op.maxW) return false; const ls = wrap(s, op.maxW, op.size || fz('body'), op.weight || 700, op.fam || 'sans', c);
            if (ls.length < 2) return false; const last = ls[ls.length - 1].trim(), prev = ls[ls.length - 2].trim();
            const cjk = (last.match(/[\u2E80-\u9FFF\uF900-\uFAFF\uFF00-\uFFEF\u3000-\u303F]/g) || []).length;
            return cjk ? [...last].length <= 2 : (!/\s/.test(last) && /\s/.test(prev) && last.length <= 8); })() }); } }
    return r; }; })()"""


def text_check(pg, t, w, h):
    """回傳這個時間點的文字問題清單。"""
    pg.evaluate(HOOK)
    r = pg.evaluate("([t,w,h]) => { if (CV.width!==w||CV.height!==h) __cm.resize(w,h,1); __tb.length = 0; __rec = true;"
                    " __cm.frame(t); __rec = false; return { b: __tb.slice(), S: [SAFE.x, SAFE.y, SAFE.r, SAFE.b], MIN }; }", [t, w, h])
    out, bx = [], r["b"]
    sx, sy, sr, sb = r["S"]; tol = sx * .5
    for b in bx:
        if b["x0"] < -2 or b["y0"] < -2 or b["x1"] > w + 2 or b["y1"] > h + 2:
            out.append(f"「{b['s']}」被裁切出畫面")
        elif b["x0"] < sx - tol or b["y0"] < sy - tol or b["x1"] > sr + tol or b["y1"] > sb + tol:
            out.append(f"「{b['s']}」超出安全區")
        if b.get("orphan"):
            out.append(f"「{b['s']}」換行後最後一行太短（孤字），縮短文案、加寬 maxW，或用 txt 的 fit 選項")
        if b["size"] < r["MIN"] * .018:
            out.append(f"「{b['s']}」字級 {b['size']:.0f}px 過小")
    bx = [b for b in bx if len(b["s"].strip()) > 1 or b["s"].strip().isalnum()]  # 單一裝飾符號（如大引號）不算重疊
    for i in range(len(bx)):
        for j in range(i + 1, len(bx)):
            a, c = bx[i], bx[j]
            if a["s"] == c["s"]:
                continue  # 同一段字畫兩次＝錯位陰影或描邊技法，不是疊字
            ix = min(a["x1"], c["x1"]) - max(a["x0"], c["x0"]); iy = min(a["y1"], c["y1"]) - max(a["y0"], c["y0"])
            small = min((a["x1"] - a["x0"]) * (a["y1"] - a["y0"]), (c["x1"] - c["x0"]) * (c["y1"] - c["y0"])) or 1
            if ix > 0 and iy > 0 and ix * iy / small > .25:
                out.append(f"「{a['s']}」與「{c['s']}」重疊")
    return out


SIZES = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (960, 960)}
THUMB = {"16:9": (480, 270), "9:16": (225, 400), "1:1": (320, 320)}


def font(sz):
    for p in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/System/Library/Fonts/PingFang.ttc",
              "C:/Windows/Fonts/msjh.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--per", type=int, default=2)
    ap.add_argument("--frac", default="", help="每幕取樣位置，例如 0.5,0.9（覆蓋 --per）")
    ap.add_argument("--at", default="")
    ap.add_argument("--trans", action="store_true")
    ap.add_argument("--aspects", default="16:9,9:16")
    ap.add_argument("--cols", type=int, default=0)
    ap.add_argument("--no-textcheck", action="store_true")
    ap.add_argument("--strict", action="store_true", help="文字檢查有問題時以代碼 3 結束（verify.py 用）")
    ap.add_argument("--pairs", action="store_true", help="另外取每個切點前後（前一幕 97%／下一幕 3%），檢查跨幕物件是否接得上")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    html = build(proj, quiet=True)
    out_dir = proj / "sheets"; out_dir.mkdir(exist_ok=True)

    with open_page(html) as pg:
        info = pg.evaluate("({TOTAL: __cm.TOTAL, SC: __cm.SC})")
        shots = []  # (label, t)
        if a.at:
            for t in map(float, a.at.split(",")):
                sc = [s for s in info["SC"] if s["start"] <= t][-1]
                shots.append((f"{sc['fn']} {t:.2f}s", t))
        else:
            fr = [float(x) for x in a.frac.split(",")] if a.frac else [0.45, 0.9] if a.per == 2 else [(k + 1) / (a.per + 1) for k in range(a.per)] if a.per > 1 else [0.6]
            for s in info["SC"]:
                for f in fr:
                    t = s["start"] + s["dur"] * f
                    shots.append((f"{s['fn']} {t:.2f}s", t))
        if a.pairs:
            for p, s in zip(info["SC"], info["SC"][1:]):
                shots.append((f"接點前 {p['fn']} {p['start'] + p['dur'] * .97:.2f}s", p["start"] + p["dur"] * .97))
                shots.append((f"接點後 {s['fn']} {s['start'] + s['dur'] * .03:.2f}s", s["start"] + s["dur"] * .03))
            shots.sort(key=lambda x: x[1])
        if a.trans:
            for s in info["SC"][1:]:
                shots.append((f"轉場→{s['fn']} {s['start']:.2f}s", s["start"]))
            shots.sort(key=lambda x: x[1])

        f_lab = font(15)
        text_issues = []
        for asp in a.aspects.split(","):
            w, h = SIZES[asp]; tw, th = THUMB[asp]
            cols = a.cols or (4 if asp == "16:9" else 6 if asp == "9:16" else 5)
            rows = -(-len(shots) // cols)
            sheet = Image.new("RGB", (cols * (tw + 12) + 12, rows * (th + 34) + 12), (24, 24, 28))
            d = ImageDraw.Draw(sheet)
            for k, (lab, t) in enumerate(shots):
                im = Image.open(io.BytesIO(grab(pg, t, w, h))).convert("RGB").resize((tw, th), Image.LANCZOS)
                x = 12 + (k % cols) * (tw + 12); y = 12 + (k // cols) * (th + 34)
                sheet.paste(im, (x, y)); d.text((x, y + th + 6), lab, fill=(210, 210, 215), font=f_lab)
            p = out_dir / f"sheet_{asp.replace(':', 'x')}.jpg"
            sheet.save(p, quality=88)
            print(f"✓ {p}  ({len(shots)} 格)")
            if not a.no_textcheck:
                seen = set()
                for lab, t in shots:
                    if lab.startswith("轉場"):
                        continue
                    later = set(text_check(pg, t + .15, w, h))
                    for m in [m for m in text_check(pg, t, w, h) if m in later]:   # 兩個時間點都有才算（排除進場動畫中的瞬間）
                        key = (lab.split()[0], m)
                        if key not in seen:
                            seen.add(key); text_issues.append(f"{asp} {lab}：{m}")

        ms = pg.evaluate("__cm.bench(30, 1280, 720)")
        errs = pg.evaluate("__cm.errors")
        print(f"效能：1280×720 平均每格 {ms:.1f}ms（本機軟體繪製，GPU 瀏覽器約快 3–5 倍）" + ("  ⚠ 超過 20ms，建議烘焙或減少全螢幕光暈" if ms > 20 else ""))
        if not a.no_textcheck:
            print("✓ 文字檢查：沒有發現問題" if not text_issues else f"! 文字檢查發現 {len(text_issues)} 個問題：")
            for m in text_issues[:30]:
                print(f"  ! {m}")
        for e in errs:
            print(f"✗ 場景錯誤 {e['fn']} @ {e['t']}s：{e['msg']}")
        for l in pg.logs:
            if "Failed to load resource" not in l:
                print(l)
        if pg.fonts_missing:
            print(f"! 網路字型沒有載入：{', '.join(pg.fonts_missing)}（截圖用系統字型；線上播放會不同。離線環境正常）")
        if errs:
            sys.exit(2)
        if a.strict and text_issues:
            sys.exit(3)


if __name__ == "__main__":
    main()
