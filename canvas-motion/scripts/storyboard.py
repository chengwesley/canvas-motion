#!/usr/bin/env python3
"""分鏡 → 專案：一步產生 project.json 與自訂場景鷹架，並檢查節奏。

用法：
  python3 storyboard.py storyboard.json --preview        # 只印出提案用的分鏡表與檢查結果，不寫檔
  python3 storyboard.py storyboard.json <專案資料夾>      # 產生 <專案>/project.json 與 scenes/ 鷹架
  python3 storyboard.py storyboard.json <專案> --force   # 覆寫既有 project.json（已存在的場景檔不會被覆寫）

storyboard.json：
{
  "title": "片名", "aspect": "auto", "bpm": 100,            // bpm 選填，預設取風格
  "style": "minimal" 或 { "base": "minimal", ... },         // 風格參數見 styles/_schema.json
  "source": "source.txt",                                   // 選填：素材檔，build.py 用來追溯數字
  "scenes": [
    { "fn": "sHook", "bars": 2, "energy": 0.3, "trans": "zoom", "say": "這幕講的一件事" },
    { "fn": "sProduct", "bars": 3, "energy": 0.7, "say": "產品如何運作" }   // s 開頭 = 自訂場景，會產生鷹架
  ]
}
"""
import argparse, json, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）

sys.path.insert(0, str(Path(__file__).parent))
from new_project import SCAFFOLD  # noqa: E402
from style_gen import anchor_info, anchor_src  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
TRANS = {"cut", "fade", "push", "wipe", "zoom", "iris", "flash", "glitch"}


def lib_scenes():
    src = "\n".join(p.read_text("utf-8") for p in (SKILL / "library").glob("*.js"))
    return set(re.findall(r"function\s+(L_[A-Za-z0-9_]+)\s*\(", src))


def style_bpm(style):
    if isinstance(style, dict):
        b = (style.get("music") or {}).get("bpm")
        return min(140, max(70, int(b))) if b else anchor_info(anchor_src(style.get("base", "minimal")))["bpm"]
    p = SKILL / "styles" / f"{style}.js"
    return anchor_info(p.read_text("utf-8"))["bpm"] if p.exists() else 120


def check(sb):
    """回傳 (錯誤, 警告)。"""
    errs, warns = [], []
    sc = sb.get("scenes") or []
    if not sc:
        return ["沒有任何幕"], []
    for i, s in enumerate(sc, 1):
        fn = s.get("fn", "")
        if not isinstance(s.get("energy", .5), (int, float)):
            errs.append(f"第 {i} 幕 energy 要是數字"); continue
        if not fn.startswith("s"):
            errs.append(f"第 {i} 幕 fn「{fn}」要是 s 開頭的自訂場景（每幕都由自己發想構圖與動畫，不套版面零件）")
        b = s.get("bars", 2)
        if not isinstance(b, int) or b < 1:
            errs.append(f"第 {i} 幕 bars 必須是正整數（切點才會落在小節第一拍）")
        e = s.get("energy", .5)
        if not 0 <= e <= 1:
            errs.append(f"第 {i} 幕 energy 要在 0–1")
        if s.get("trans") and s["trans"] not in TRANS:
            errs.append(f"第 {i} 幕轉場 {s['trans']} 不支援（{', '.join(sorted(TRANS))}）")
        for k, v in (s.get("data") or {}).items():
            if isinstance(v, list) and isinstance(b, int) and len(v) > b * 4:
                warns.append(f"第 {i} 幕 {k} 有 {len(v)} 項，{b} 小節內每項不到一拍，考慮加小節或刪項")
        if not s.get("say"):
            warns.append(f"第 {i} 幕沒寫 say（這幕講的一件事），提案時使用者看不懂用意")
    if isinstance(sc[-1].get("bars", 2), int) and sc[-1].get("bars", 2) < 2:
        errs.append("最後一幕至少 2 小節，留給收束和弦與餘韻")
    en = [s.get("energy", .5) for s in sc]
    if len(sc) >= 3:
        if en[0] > .5:
            warns.append(f"開場 energy {en[0]} 偏高，通常從 .3 左右開始才有起伏")
        if en.index(max(en)) < len(en) / 2:
            warns.append("最高 energy 在前半段，高潮通常放在後半")
    tr = [s.get("trans") for s in sc[:-1] if s.get("trans")]
    if len(tr) >= 3 and len(set(tr)) == 1:
        warns.append(f"整支片只用 {tr[0]} 轉場，依內容關係換幾種（延續 push、揭示 wipe/iris、轉強 zoom/flash）")
    return errs, warns


def table(sb):
    bpm = int(sb.get("bpm") or style_bpm(sb.get("style", "minimal")))
    bar = 240 / bpm
    rows = ["| # | 畫面 | 小節 | 秒數 | energy | 這幕講的一件事 | 轉場 |", "|---|---|---|---|---|---|---|"]
    t = 0
    for i, s in enumerate(sb["scenes"], 1):
        d = s.get("bars", 2) * bar
        kind = "自訂" if str(s.get("fn", "")).startswith("s") else s.get("fn", "?")
        rows.append(f"| {i} | {kind} | {s.get('bars', 2)} | {t:.0f}–{t + d:.0f} | {s.get('energy', .5)} | {s.get('say', '')} | {s.get('trans', '—')} |")
        t += d
    return "\n".join(rows) + f"\n\n總長約 {t:.0f} 秒（{bpm} BPM）"


def write(sb, d: Path, force=False, sb_dir: Path = Path(".")):
    if (d / "project.json").exists() and not force:
        sys.exit(f"✗ {d}/project.json 已存在（要覆寫加 --force）")
    (d / "scenes").mkdir(parents=True, exist_ok=True)
    cfg = {k: sb[k] for k in ("title", "style", "aspect", "bpm", "anchors") if k in sb}
    cfg.setdefault("aspect", "auto")
    cfg.setdefault("style", "minimal")
    if sb.get("source"):
        src = (sb_dir / sb["source"]).resolve()
        if src.exists() and src != (d / "source.txt").resolve():
            shutil.copy(src, d / "source.txt")
    cfg["scenes"] = []
    existing = "\n".join(p.read_text("utf-8") for p in (d / "scenes").glob("*.js"))
    for k, s in enumerate(sb["scenes"]):
        row = {"fn": s["fn"], "bars": s.get("bars", 2), "energy": s.get("energy", .5)}
        for key in ("trans", "data"):
            if key in s:
                row[key] = s[key]
        if s.get("say"):
            row["_say"] = s["say"]
        cfg["scenes"].append(row)
        if s["fn"].startswith("s") and not re.search(rf"function\s+{s['fn']}\s*\(", existing):
            f = d / "scenes" / f"{k:02d}_{s['fn'][1:].lower()}.js"
            f.write_text(SCAFFOLD.format(fn=s["fn"], note=s.get("say", "描述這幕要講的一件事")), "utf-8")
            print(f"  + 鷹架 {f.name}")
    (d / "project.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"✓ 已寫入 {d / 'project.json'}（{len(cfg['scenes'])} 幕）  下一步：寫自訂場景 → build.py → sheet.py --trans")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    sp = Path(a.storyboard)
    sb = json.loads(sp.read_text("utf-8"))
    errs, warns = check(sb)
    if not errs:
        print(table(sb) + "\n")
    for w in warns:
        print(f"! {w}")
    for e in errs:
        print(f"✗ {e}")
    if errs:
        sys.exit(1)
    if a.dir and not a.preview:
        write(sb, Path(a.dir), a.force, sp.parent)


if __name__ == "__main__":
    main()
