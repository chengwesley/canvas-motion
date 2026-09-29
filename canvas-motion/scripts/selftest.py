#!/usr/bin/env python3
"""回歸自測：所有範例專案 × 所有錨點風格都要能建置，並測一組生成風格。修改引擎、工具或風格後執行。

用法：python3 selftest.py            # 只建置（快，不需要 Playwright）
      python3 selftest.py --sheet    # 另外對 examples/ 跑 sheet.py（含文字檢查）
"""
import argparse, contextlib, io, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）

sys.path.insert(0, str(Path(__file__).parent))
import build as B  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent


def fill(o):
    if isinstance(o, str):
        return re.sub(r"\{\{[^}]*\}\}", "測試文字", o)
    if isinstance(o, list):
        return [fill(x) for x in o]
    if isinstance(o, dict):
        return {k: fill(v) for k, v in o.items()}
    return o


def try_build(cfg, tmp: Path, scenes: Path = None):
    (tmp / "scenes").mkdir(parents=True, exist_ok=True)
    if scenes and scenes.exists():
        for f in scenes.glob("*.js"):
            shutil.copy(f, tmp / "scenes" / f.name)
    (tmp / "project.json").write_text(json.dumps(cfg, ensure_ascii=False), "utf-8")
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            B.build(tmp, quiet=True)
        return None
    except SystemExit:
        return err.getvalue().strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args()
    styles = sorted(p.stem for p in (SKILL / "styles").glob("*.js") if not p.stem.startswith("_"))
    temps = sorted(p for p in (SKILL / "examples").iterdir() if (p / "project.json").exists())
    gen = [{"base": "tech", "name": "gen-light", "colors": {"bg": "#ffffff", "fg": "#999999"}, "background": {"kind": k}}
           for k in ("solid", "gradient", "glow", "grid", "dots", "paper")]
    fails, n = [], 0
    with tempfile.TemporaryDirectory() as td:
        for tp in temps:
            base = fill(json.loads((tp / "project.json").read_text("utf-8")))
            for st in styles + gen:
                n += 1
                cfg = dict(base, style=st)
                e = try_build(cfg, Path(td) / f"p{n}", tp / "scenes")
                if e:
                    fails.append(f"{tp.stem} × {st if isinstance(st, str) else st['background']['kind']}：{e}")
    print(f"建置：{n - len(fails)}/{n} 通過（{len(temps)} 範例 × {len(styles)} 錨點 + {len(gen)} 生成背景）")
    for f in fails:
        print(f"✗ {f}")
    code = 1 if fails else 0
    if a.sheet:   # 實際渲染抽樣畫格：語法對但執行時丟錯的場景也要抓到
        from _browser import open_page, goto
        rfails = []
        with tempfile.TemporaryDirectory() as td:
            htmls = []
            for tp in temps:
                for st in ("tech", "minimal"):
                    d = Path(td) / f"{tp.stem}-{st}"
                    if not try_build(dict(fill(json.loads((tp / "project.json").read_text("utf-8"))), style=st, webfonts=False), d, tp / "scenes"):
                        htmls.append((f"{tp.stem} × {st}", d / "dist" / "index.html"))
            if htmls:
                with open_page(htmls[0][1]) as pg:
                    for k, (lab, h) in enumerate(htmls):
                        if k:
                            goto(pg, h)
                        errs = pg.evaluate("(() => { const S = __cm.SC; for (const s of S) for (const f of [.1, .5, .95]) __cm.frame(s.start + s.dur * f); return __cm.errors; })()")
                        if errs:
                            rfails.append(f"{lab}：{errs[0]['fn']} {errs[0]['msg']}")
            print(f"渲染：{len(htmls) - len(rfails)}/{len(htmls)} 通過（{len(temps)} 範例 × 2 錨點，每幕 3 格）")
            for f in rfails:
                print(f"✗ {f}")
            code = code or (1 if rfails else 0)
        for ex in sorted((SKILL / "examples").iterdir()):
            r = subprocess.run([sys.executable, str(SKILL / "scripts" / "sheet.py"), str(ex), "--trans"],
                               capture_output=True, text=True, encoding="utf-8")
            tail = [l for l in r.stdout.splitlines() if "文字檢查" in l or "場景錯誤" in l or l.strip().startswith("! ")]
            print(f"{'✓' if r.returncode == 0 else '✗'} sheet {ex.name}" + ("".join(f"\n    {l.strip()}" for l in tail[:8])))
            code = code or (1 if r.returncode else 0)
    sys.exit(code)


if __name__ == "__main__":
    main()
