#!/usr/bin/env python3
"""一鍵檢查：建置 → 縮圖總覽（橫＋直、轉場中點）→ 文字檢查（嚴格）→ 場景錯誤 → 字型 → 效能 → 動態品味（只提醒）。

用法：python3 verify.py <專案> [--aspects 16:9,9:16] [--pairs]
結束碼：0 全部通過；1 建置失敗；2 場景錯誤；3 文字問題。有非 0 就修，修完重跑，直到 0。
通過後再用 view 逐格看 sheets/*.jpg 與 sheets/motion.png，並照 references/craft.md 的自評表檢查一次。
"""
import argparse, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）

HERE = Path(__file__).parent


def run(args):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout + r.stderr).strip()
    return r.returncode, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--aspects", default="16:9,9:16")
    ap.add_argument("--pairs", action="store_true", help="另外檢查每個切點前後的畫面（跨幕物件要接得上時）")
    ap.add_argument("--no-taste", action="store_true", help="跳過動態品味檢查")
    a = ap.parse_args()

    code, out = run([str(HERE / "build.py"), a.project])
    print("── 建置"); print(out)
    if code:
        print("✗ 建置失敗"); sys.exit(1)
    warn = [l for l in out.splitlines() if l.startswith("!")]

    args = [str(HERE / "sheet.py"), a.project, "--trans", "--strict", "--aspects", a.aspects]
    if a.pairs:
        args.append("--pairs")
    code, out = run(args)
    print("── 縮圖與文字檢查"); print(out)

    taste = []
    if code in (0, 3) and not a.no_taste:
        tc, tout = run([str(HERE / "taste.py"), a.project])
        print("── 動態品味（提醒，不擋交付）"); print(tout)
        taste = [l for l in tout.splitlines() if l.startswith("!")]

    print("── 結果")
    if warn:
        print(f"! 建置有 {len(warn)} 則提醒（上方 ! 開頭），確認是否要處理")
    if code == 2:
        print("✗ 場景錯誤：先修場景程式"); sys.exit(2)
    if code == 3:
        print("✗ 文字問題：依上方清單修正（縮短文案、加寬 maxW、txt 加 fit、壓在背景上的字用 txtPlate）"); sys.exit(3)
    if code:
        print("✗ 截圖失敗（Playwright 無法使用？見 check_env.py）"); sys.exit(code)
    if taste:
        print(f"! 動態品味有 {len(taste)} 則提醒：看看是不是刻意的；不是刻意的就改，刻意的就保留並在交付時說明")
    print("✓ 自動檢查全部通過。接著用 view 逐格看 sheets/sheet_16x9.jpg、sheet_9x16.jpg、motion.png，再照 craft.md 自評表檢查")


if __name__ == "__main__":
    main()
