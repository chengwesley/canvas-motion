"""共用：以 Playwright Chromium 開啟 dist/index.html，提供 frame 擷取。"""
import base64, sys
from contextlib import contextmanager
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    print("✗ 需要 Playwright：pip install playwright && python -m playwright install chromium", file=sys.stderr)
    sys.exit(1)


@contextmanager
def open_page(html_path: Path):
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required", "--use-mock-keychain"])
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        logs = []
        pg.on("console", lambda m: m.type in ("error", "warning") and logs.append(f"[{m.type}] {m.text}"))
        pg.on("pageerror", lambda e: logs.append(f"[pageerror] {e}"))
        pg.goto(Path(html_path).resolve().as_uri())
        pg.wait_for_function("window.__cm !== undefined", timeout=15000)
        # 等網路字型：最多 8 秒，逐一確認每個字族都已載入；沒載入的列在 pg.fonts_missing
        pg.evaluate("Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 4000))])")
        pg.fonts_missing = pg.evaluate(r"""async () => {
          const fams = new Set(); const F = (typeof STYLE !== 'undefined' && STYLE.fonts) || {};
          Object.values(F).forEach(v => { const m = String(v).match(/"([^"]+)"/); if (m) fams.add(m[1]); });
          const links = [...document.querySelectorAll('link[rel=stylesheet]')].map(l => decodeURIComponent(l.href).replace(/\+/g, ' ')).join(' ');
          const want = [...fams].filter(f => links.includes(f));   // 只檢查有從 Google Fonts 載入的字族
          // 字型是用到才下載：先主動要求載入每個字族（常用字重），最多等 8 秒，再逐一確認
          const load = f => Promise.all(['400', '700', '800'].map(wt => document.fonts.load(`${wt} 16px "${f}"`).catch(() => [])));
          await Promise.race([Promise.all(want.map(load)), new Promise(r => setTimeout(r, 8000))]);
          if (want.every(f => document.fonts.check(`16px "${f}"`))) { _caches.clear(); return []; }
          return want.filter(f => !document.fonts.check(`16px "${f}"`));
        }""")
        pg.logs = logs
        try:
            yield pg
        finally:
            b.close()


def goto(pg, html_path: Path):
    """同一個分頁改開另一個建置結果（省下重開瀏覽器的時間）。"""
    pg.goto(Path(html_path).resolve().as_uri())
    pg.wait_for_function("window.__cm !== undefined", timeout=15000)
    pg.evaluate("Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 4000))])")


def grab(pg, t, w, h, fmt="jpeg", q=0.9) -> bytes:
    url = pg.evaluate(
        "([t,w,h,f,q]) => { if (CV.width!==w||CV.height!==h) __cm.resize(w,h,1); __cm.frame(t);"
        " return CV.toDataURL('image/'+f, q); }", [t, w, h, fmt, q])
    return base64.b64decode(url.split(",", 1)[1])
