#!/usr/bin/env python3
"""檢查 canvas-motion 需要的工具是否齊全。用法：python3 check_env.py"""
import shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）

SKILL = Path(__file__).resolve().parent.parent
ok = True


def row(name, good, note, required=True):
    global ok
    if required and not good:
        ok = False
    print(f"{'✓' if good else ('✗' if required else '!')} {name:<14} {note}")


for f in ["engine/head.html", "engine/infra.js", "engine/tail.js"]:
    e = (SKILL / f).exists(); ok &= e; row(f, e, "" if e else "引擎檔案遺失：停下來告知使用者，不要自行重寫")
styles = sorted(p.stem for p in (SKILL / "styles").glob("*.js") if not p.stem.startswith("_"))
row("styles", bool(styles), ", ".join(styles))
node = shutil.which("node"); row("node", bool(node), subprocess.run([node, "-v"], capture_output=True, text=True).stdout.strip() if node else "可缺：只影響語法檢查", required=False)
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        p.chromium.launch().close()
    row("playwright", True, "Chromium 可用（截圖、MP4 匯出）")
except Exception as e:  # noqa: BLE001
    row("playwright", False, "無法截圖／匯出。安裝：pip install playwright && python -m playwright install chromium")
ff = shutil.which("ffmpeg")
if not ff:
    try:
        import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
row("ffmpeg", bool(ff), ff or "無法匯出 MP4。安裝：pip install imageio-ffmpeg")
try:
    import PIL; row("pillow", True, PIL.__version__)
except ImportError:
    row("pillow", False, "sheet.py 需要：pip install pillow", required=False)
if shutil.which("fc-list"):
    cjk = bool(subprocess.run(["fc-list", ":lang=zh"], capture_output=True, text=True).stdout.strip())
else:   # Windows／macOS 沒有 fc-list：直接找常見中文字型檔
    cjk = any(Path(p).exists() for p in ["C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/msjhl.ttc", "/System/Library/Fonts/PingFang.ttc",
                                          "/System/Library/Fonts/STHeiti Medium.ttc",
                                          "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"])
row("中文字型", cjk, "有" if cjk else "截圖會出現方框：apt install fonts-noto-cjk（Windows 需要微軟正黑體）")
import platform  # noqa: E402
if platform.system() == "Windows":   # 旁白配音（voice.py）：Windows 內建離線語音
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SKILL / "scripts" / "tts_winrt.ps1"), "-list"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60).stdout
        zh = [ln.split("	")[0].replace("Microsoft ", "") for ln in out.splitlines() if "zh-TW" in ln]
        row("旁白語音", bool(zh), "台灣中文：" + "、".join(zh) if zh else "沒有 zh-TW 語音：設定 → 時間與語言 → 語音 → 新增中文（台灣）；或用 --engine edge", required=False)
    except Exception:  # noqa: BLE001
        row("旁白語音", False, "無法列出語音，可改用 voice.py --engine edge", required=False)
else:
    try:
        import edge_tts  # noqa: F401
        row("旁白語音", True, "edge-tts（線上）")
    except ImportError:
        row("旁白語音", shutil.which("say") is not None, "macOS say" if shutil.which("say") else "要旁白時：pip install edge-tts（線上）", required=False)
probe = shutil.which("ffprobe")
row("ffprobe", bool(probe), probe or "可缺：export.py 會改用 ffmpeg 驗證輸出", required=False)
sys.exit(0 if ok else 1)
