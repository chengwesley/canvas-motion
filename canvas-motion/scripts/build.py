#!/usr/bin/env python3
"""把專案組裝成單一 HTML。

用法：python3 build.py <專案資料夾> [--out 路徑]
專案資料夾需要 project.json 與 scenes/*.js。project.json 的 style 可以是：
  - 物件：風格參數（錨點 + 覆寫，格式見 styles/_schema.json），由 style_gen.py 產生並驗證
  - 字串：先找 <專案>/styles/<style>.js，找不到再用 skill 內建的錨點 styles/<style>.js
輸出預設為 <專案>/dist/index.html。

建置時另外做兩項檢查（只警告、不中斷，Math.random 除外）：
  - 自訂場景 lint：Math.random、txt 沒給 maxW、寫死色碼、自己淡出
  - 素材追溯：若專案有 source.txt（或 project.json 的 "_source" 指向檔案），列出畫面上找不到出處的數字
"""
import argparse, html, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from style_gen import generate as gen_style  # noqa: E402
LIMIT = 16 * 1024 * 1024


def fail(msg):
    print(f"✗ {msg}", file=sys.stderr)
    sys.exit(1)


def lint_scene(name, src):
    """自訂場景的靜態檢查。回傳 (錯誤, 警告)。"""
    errs, warns = [], []
    code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    code = re.sub(r"(?<![:'\"\\])//.*", "", code)   # 行註解；https:// 這類字串裡的不算
    if "Math.random" in code:
        errs.append(f"{name}：用了 Math.random()，匯出時每格不同會閃爍，改用 rng(種子)")
    for m in re.finditer(r"\b(txt|txtB|txtPlate)\(", code):   # 用括號配對取出完整參數（可以跨行）
        depth, i = 1, m.end()
        while i < len(code) and depth:
            depth += {"(": 1, ")": -1}.get(code[i], 0); i += 1
        args = code[m.end():i]
        if "maxW" not in args and "fit" not in args and "..." not in args:   # 有展開（...o）時看不到內容，不判定
            warns.append(f"{name}：{m.group(1)} 沒有 maxW，長文字可能溢出 → {m.group(0)}{' '.join(args.split())[:50]}")
            break
    hexes = set(re.findall(r"['\"]#[0-9a-fA-F]{3,6}['\"]", code))
    if hexes:
        warns.append(f"{name}：寫死色碼 {', '.join(sorted(hexes)[:3])}，換風格會不協調，改用 STYLE.c.*")
    if re.search(r"1\s*-\s*tw\(\s*t\s*,\s*T", code):
        warns.append(f"{name}：看起來在幕尾自己淡出；有轉場時會讓轉場只剩背景")
    return errs, warns


def trace_source(proj, cfg):
    """列出 project.json data 裡、在素材中找不到的數字。"""
    sp = cfg.get("_source")
    sp = (proj / sp) if sp else proj / "source.txt"
    if not sp.exists():
        return None
    src = re.sub(r"[,\s]", "", sp.read_text("utf-8", errors="ignore"))
    data = json.dumps([s.get("data", {}) for s in cfg["scenes"]], ensure_ascii=False)
    data = re.sub(r'"_[^"]*":\s*"[^"]*"', "", data)
    data = re.sub(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)", "", data)   # 色碼不是畫面上的數字
    data = re.sub(r'"(?:pal|x|y|r|size|speed|base|amp|seed|parallax|horizon|push|n|no)":\s*[\d.]+', "", data)   # 構圖參數也不是
    nums = set(re.findall(r"\d+(?:[.,]\d+)*", data))
    def found(n):   # 數字邊界：畫面上的 12 不能靠素材裡的 2012 過關
        return re.search(r"(?<![\d.])" + re.escape(n.replace(",", "")) + r"(?![\d])", src) is not None
    return sorted(n for n in nums if len(n.replace(",", "")) >= 2 and not found(n))


def build(proj: Path, out: Path | None = None, quiet=False, webfonts: bool | None = None) -> Path:
    """webfonts=False：不載入網路字型（離線或要求整支片字型一致時）；None＝依 project.json 的 webfonts（預設開）。"""
    proj = proj.resolve()
    cfg_p = proj / "project.json"
    if not cfg_p.exists():
        fail(f"找不到 {cfg_p}")
    cfg = json.loads(cfg_p.read_text("utf-8"))
    for k in ("title", "style", "scenes"):
        if k not in cfg:
            fail(f"project.json 缺少欄位 {k}")

    style = cfg["style"]
    style_rep = []
    if isinstance(style, dict):
        style_src, style_rep = gen_style(style)
        style = re.search(r"→ (\S+)。", style_src).group(1)
    else:
        sp = proj / "styles" / f"{style}.js"
        if not sp.exists():
            sp = SKILL / "styles" / f"{style}.js"
        if not sp.exists():
            avail = ", ".join(p.stem for p in (SKILL / "styles").glob("*.js") if not p.stem.startswith("_"))
            fail(f"找不到風格 {style}（可用錨點：{avail}；或把 style 寫成參數物件）")
        style_src = sp.read_text("utf-8")

    scene_files = sorted((proj / "scenes").glob("*.js")) if (proj / "scenes").exists() else []
    # library/ 底下全部載入：kit.js（常用繪圖小工具）、looks.js（畫風渲染與形狀）……依檔名排序
    lib_src = "\n".join(f"// ==== library/{p.name}\n{p.read_text('utf-8')}" for p in sorted((SKILL / "library").glob("*.js")))
    scene_src = "\n".join(f"// ---- scenes/{p.name}\n{p.read_text('utf-8')}" for p in scene_files)
    defined = set(re.findall(r"function\s+((?:s|L_)[A-Za-z0-9_]+)\s*\(", lib_src + "\n" + scene_src))
    missing = [s["fn"] for s in cfg["scenes"] if s["fn"] not in defined]
    if missing:
        fail(f"project.json 引用了未定義的場景函式：{', '.join(missing)}")
    unused = {f for f in defined if f.startswith("s")} - {s["fn"] for s in cfg["scenes"]}
    lint_err, lint_warn = [], []
    for p in scene_files:
        e, w = lint_scene(p.name, p.read_text("utf-8"))
        lint_err += e; lint_warn += w
    if lint_err:
        fail("自訂場景有問題：\n  " + "\n  ".join(lint_err))
    holes = re.findall(r"\{\{[^}]*\}\}", json.dumps(cfg, ensure_ascii=False))

    eng = SKILL / "engine"
    js = "\n".join([
        (eng / "infra.js").read_text("utf-8"),
        f"// ==== style: {style}\n{style_src}",
        lib_src,
        scene_src,
        "const PROJECT = " + json.dumps(cfg, ensure_ascii=False) + ";",
        (eng / "tail.js").read_text("utf-8"),
    ])
    if re.search(r"</script", js, re.I):
        fail("JS 內含 '</script'，會提早結束 script 標籤；請改成 '<\\/script'")

    if shutil.which("node"):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(js)
        try:
            r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
        finally:
            os.unlink(f.name)
        if r.returncode:
            fail("語法錯誤：\n" + r.stderr.strip())
    elif not quiet:
        print("! 找不到 node，略過語法檢查")

    fonts = ""
    m = re.search(r"@fonts\s+(\S+)", style_src)
    use_wf = cfg.get("webfonts", True) if webfonts is None else webfonts
    if m and use_wf:
        fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                 f'<link rel="stylesheet" href="{html.escape(m.group(1))}">')
    head = (eng / "head.html").read_text("utf-8")
    head = head.replace("{{TITLE}}", html.escape(cfg["title"])).replace("{{FONTS}}", fonts)
    doc = f"{head}<script>\n{js}\n</script>\n</body>\n</html>\n"

    out = (out or proj / "dist" / "index.html").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, "utf-8")
    size = out.stat().st_size
    if size > LIMIT:
        fail(f"輸出 {size/1e6:.1f}MB，超過 Artifact 16MB 上限")

    if not quiet:
        bpms = re.findall(r"\"?bpm\"?:\s*(\d+)", style_src)  # 取最後一個：產生的風格會覆寫錨點
        bpm = int(cfg.get("bpm") or (bpms[-1] if bpms else 120))
        bars = sum(s.get("bars", 2) for s in cfg["scenes"])
        print(f"✓ {out}  {size/1024:.0f}KB  |  風格 {style}  |  {len(cfg['scenes'])} 幕 / {bars} 小節 / "
              f"{bars*240/bpm:.1f}s @ {bpm} BPM")
        for r in style_rep:
            print(r)
        for w in lint_warn:
            print(f"! {w}")
        missing_src = trace_source(proj, cfg)
        if missing_src:
            print(f"! 素材裡找不到這些數字，請確認出處：{', '.join(missing_src[:8])}")
        elif missing_src == []:
            print("✓ 畫面上的數字都能在素材中找到")
        if holes:
            print(f"! 還有 {len(holes)} 個待填欄位（例如 {holes[0]}），請用素材內容取代")
        if unused:
            print(f"! 已定義但未使用的場景：{', '.join(sorted(unused))}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--out")
    a = ap.parse_args()
    build(Path(a.project), Path(a.out) if a.out else None)
