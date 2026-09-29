#!/usr/bin/env python3
"""建立新專案。

用法：
  python3 new_project.py --list                                   # 列出腳本範本與風格包
  python3 new_project.py <資料夾> --blank --title "片名"           # 空白骨架，自由設計分鏡（預設建議）
  python3 new_project.py <資料夾> --template keynote --title "片名"  # 從敘事參考範本建立
  python3 new_project.py <資料夾> --title "片名" --scenes sHook:2,sProof:3,sOutro:2   # 空白自訂場景
選填：--style tech  --bpm 120  --aspect auto|16:9|9:16|1:1

--blank 只產生最小的 project.json（一幕開場），依分鏡自由增減幕、混用 L_ 場景與自訂場景。
範本只是敘事參考，建立後可任意刪改；場景庫不夠用時，在 scenes/ 寫自訂場景函式（s 開頭）。
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）

SKILL = Path(__file__).resolve().parent.parent

SCAFFOLD = '''/* {fn}：{note}
 * t = 本幕經過秒數（0 = 切點）、T = 本幕長度、pulse = 拍點脈衝、s = project.json 裡這幕的設定
 * 守則：橫直式各自排版（pick）、文字都給 maxW、顏色只用 STYLE.c.*、隨機用 rng()、
 *       進場從切點前開始、有轉場時不要自己淡出。API 見 references/api.md */
function {fn}(t, T, pulse, s) {{
  const a = tw(t, -.25, .5);                                   // 進場從切點前開始，轉場中就看得到
  const L = pick({{ x: W / 2, y: H * .5, w: SAFE.w * .8 }},     // 橫式
                 {{ x: W / 2, y: H * .45, w: SAFE.w }});        // 直式：一欄、字更大，不是等比縮小
  const R = rng(1);                                            // 需要隨機分布時用它，不要用 Math.random()
  ctx.save(); camPush(1 + t * .01);                            // 鏡頭微推，避免畫面靜止
  glow(L.x, L.y, MIN * .35 * (1 + pulse * .15), STYLE.c.a1, .35);
  const title = '替換成素材中的標題';
  const size = fit(title, L.w, fz('h1'), 800, 'display', 2);
  const m = txtB(title, L.x, L.y, {{ size, weight: 800, fam: 'display', align: 'center', alpha: a, maxW: L.w }});
  // 下一段接在上一段的實際底部（m.bottom），標題換行時才不會疊字
  txt('替換成素材中的文案', L.x, m.bottom + size * .35, {{ size: fz('body'), color: STYLE.c.mute, align: 'center',
    base: 'top', alpha: tw(t, BEAT, .5), maxW: L.w }});
  ctx.restore();
}}
'''
TEMPLATE = SCAFFOLD  # 舊名稱相容


def list_all():
    print("敘事參考範本（--template，選用）：")
    for p in sorted((SKILL / "templates").glob("*.json")):
        c = json.loads(p.read_text("utf-8"))
        bars = sum(s["bars"] for s in c["scenes"])
        print(f"  {p.stem:<17} [{c['style']}, {len(c['scenes'])} 幕 / {bars} 小節]  {c['_desc']}")
    print("\n風格包（--style）：")
    for p in sorted((SKILL / "styles").glob("*.js")):
        head = p.read_text("utf-8").splitlines()[1]
        print(f"  {p.stem:<11} {head.strip('/* ').split('—')[-1].strip(' */')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--template")
    ap.add_argument("--blank", action="store_true", help="空白骨架，不套範本")
    ap.add_argument("--title")
    ap.add_argument("--style")
    ap.add_argument("--bpm", type=int)
    ap.add_argument("--aspect")
    ap.add_argument("--scenes", default="sHook:2,sReveal:2,sProof:3,sOutro:2")
    a = ap.parse_args()
    if a.list:
        return list_all()
    if not a.dir or not a.title:
        ap.error("需要 <資料夾> 與 --title（或用 --list）")
    d = Path(a.dir)
    if (d / "project.json").exists():
        sys.exit(f"✗ {d}/project.json 已存在")
    if a.style and not (SKILL / "styles" / f"{a.style}.js").exists():
        sys.exit(f"✗ 沒有風格包 {a.style}（用 --list 查看）")

    if a.blank and a.template:
        ap.error("--blank 與 --template 只能擇一")
    (d / "scenes").mkdir(parents=True, exist_ok=True)
    if a.blank:
        cfg = {"title": a.title, "style": "minimal", "aspect": "auto", "scenes": [
            {"fn": "L_title", "bars": 2, "energy": 0.4, "_hint": "依分鏡增減幕；L_ 場景與自訂場景可混用",
             "data": {"lines": ["{{開場文案}}"]}}]}
    elif a.template:
        tp = SKILL / "templates" / f"{a.template}.json"
        if not tp.exists():
            sys.exit(f"✗ 沒有腳本範本 {a.template}（用 --list 查看）")
        cfg = json.loads(tp.read_text("utf-8"))
        cfg["title"] = a.title
    else:
        scenes = []
        items = [(x.split(":") + ["2"])[:2] for x in a.scenes.split(",") if x.strip()]   # 沒寫小節數就用 2
        for k, (fn, bars) in enumerate(items):
            scenes.append({"fn": fn, "bars": int(bars), "energy": round(0.35 + 0.6 * k / max(1, len(items) - 1), 2)})
            (d / "scenes" / f"{k:02d}_{fn[1:].lower()}.js").write_text(TEMPLATE.format(fn=fn, note="描述這幕要講的一件事"), "utf-8")
        cfg = {"title": a.title, "style": "tech", "aspect": "auto", "scenes": scenes}
    for k in ("style", "bpm", "aspect"):
        if getattr(a, k):
            cfg[k] = getattr(a, k)
    (d / "project.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", "utf-8")
    holes = json.dumps(cfg, ensure_ascii=False).count("{{")
    print(f"✓ 已建立 {d}（{len(cfg['scenes'])} 幕，風格 {cfg['style']}）" + (f"，有 {holes} 個 {{{{待填}}}} 欄位" if holes else ""))
    print("  下一步：填入素材內容 → build.py → sheet.py")


if __name__ == "__main__":
    main()
