#!/usr/bin/env python3
"""把同一個專案套上每個風格包，產出一張比較圖，給使用者挑風格。

用法：
  python3 preview_styles.py <專案>                          # 所有風格，每幕 85% 處各一格
  python3 preview_styles.py <專案> --styles tech,corporate,ink
  python3 preview_styles.py <專案> --scenes 0,2,4 --aspect 9:16
輸出：<專案>/sheets/styles_<比例>.jpg（每列一個風格，每欄一幕）。
"""
import argparse, io, json, shutil, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from build import build, SKILL      # noqa: E402
from _browser import open_page, grab, goto  # noqa: E402
from sheet import font, SIZES      # noqa: E402

THUMB = {"16:9": (400, 225), "9:16": (180, 320), "1:1": (260, 260)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--styles", default="")
    ap.add_argument("--scenes", default="", help="場景索引（從 0 起），預設全部，最多 6 幕")
    ap.add_argument("--frac", type=float, default=0.85)
    ap.add_argument("--aspect", default="16:9")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    cfg = json.loads((proj / "project.json").read_text("utf-8"))
    styles = a.styles.split(",") if a.styles else sorted(p.stem for p in (SKILL / "styles").glob("*.js") if not p.stem.startswith("_"))
    idx = [int(x) for x in a.scenes.split(",")] if a.scenes else list(range(min(6, len(cfg["scenes"]))))
    bad = [i for i in idx if not 0 <= i < len(cfg["scenes"])]
    if bad:
        sys.exit(f"✗ --scenes 超出範圍：{bad}（這個專案有 {len(cfg['scenes'])} 幕，索引從 0 起）")
    w, h = SIZES[a.aspect]; tw, th = THUMB[a.aspect]; lab_w = 130
    sheet = Image.new("RGB", (lab_w + len(idx) * (tw + 8) + 8, len(styles) * (th + 8) + 8), (24, 24, 28))
    d = ImageDraw.Draw(sheet); f = font(18)
    tmp = Path(tempfile.mkdtemp())
    htmls = []
    for st in styles:
        work = tmp / st
        shutil.copytree(proj, work, ignore=shutil.ignore_patterns("dist", "sheets"))
        c = dict(cfg, style=st, webfonts=False)
        (work / "project.json").write_text(json.dumps(c, ensure_ascii=False), "utf-8")
        htmls.append(build(work, quiet=True))
    with open_page(htmls[0]) as pg:   # 只開一次瀏覽器，每種風格換頁
        for r, (st, html) in enumerate(zip(styles, htmls)):
            if r:
                goto(pg, html)
            sc = pg.evaluate("__cm.SC")
            for k, i in enumerate(idx):
                s = sc[i]; t = s["start"] + s["dur"] * a.frac
                im = Image.open(io.BytesIO(grab(pg, t, w, h))).convert("RGB").resize((tw, th), Image.LANCZOS)
                sheet.paste(im, (lab_w + 8 + k * (tw + 8), 8 + r * (th + 8)))
            errs = pg.evaluate("__cm.errors")
            d.text((12, 8 + r * (th + 8) + th // 2 - 10), st, fill=(230, 230, 235), font=f)
            print(f"{'✗' if errs else '✓'} {st}" + (f"  錯誤：{errs}" if errs else ""))
    shutil.rmtree(tmp, ignore_errors=True)
    out = proj / "sheets"; out.mkdir(exist_ok=True)
    p = out / f"styles_{a.aspect.replace(':', 'x')}.jpg"; sheet.save(p, quality=86)
    print(f"✓ {p}")


if __name__ == "__main__":
    main()
