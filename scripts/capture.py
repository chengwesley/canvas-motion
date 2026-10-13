#!/usr/bin/env python3
"""擷取產品的真實畫面當素材：網頁截圖、品牌色與字型、頁面文字。產品片先跑這支，再動手畫。

用法：
  python3 capture.py <網址> <專案> --name home                       # 1440x900 視窗截圖 → <專案>/assets/home.jpg
  python3 capture.py <網址> <專案> --name pricing --full              # 整頁長截圖（場景用 pic(…, {fit:'width'}) 往下捲）
  python3 capture.py <網址> <專案> --name hero --element "header"     # 只截某個元素（按鈕、卡片、表單）
  python3 capture.py <網址> <專案> --name menu --click "#open-menu"   # 先點開再截（可重複 --click）
  python3 capture.py <網址> <專案> --name m --size 390x844 --scale 3  # 手機版
  python3 capture.py <網址> <專案> --name home --brand dottedsign     # 另外存品牌設定檔 brands/dottedsign.json
  python3 capture.py --file 截圖.png <專案> --name editor             # 匯入使用者給的截圖（登入後的畫面用這個）

產出：
  <專案>/assets/<name>.jpg   build.py 會內嵌，場景用 pic('<name>', …) 畫
  <專案>/assets/capture.json 每張圖的來源網址、尺寸、時間（交付時說明素材出處）
  <專案>/source.txt          附加頁面上的可見文字（build.py 用來追溯畫面上的數字）
  brands/<brand>.json        --brand 時：網站實際使用的強調色與字型，storyboard 的 style 寫 "brand": "<brand>" 套用

擷取失敗（打不開、空白頁、需要登入）時寫 <專案>/assets/BLOCKED.md 並以代碼 1 結束：
停下來請使用者提供截圖（--file）或可公開的網址，**不要自己畫一個假的產品畫面冒充真實介面**。
Cookie／同意視窗與客服聊天浮窗只用 CSS 隱藏（--keep-widgets 保留），不會替使用者按「同意」。
"""
import argparse, json, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）

SKILL = Path(__file__).resolve().parent.parent
HIDE = ("[id*=cookie i],[class*=cookie i],[id*=consent i],[class*=consent i],[aria-label*=cookie i],"
        "#onetrust-consent-sdk,#CybotCookiebotDialog,.cc-window,[class*=gdpr i]{display:none!important}")
WIDGETS = ("#intercom-container,.intercom-lightweight-app,#hubspot-messages-iframe-container,#crisp-chatbox,#tidio-chat,"
           "[id*=chat-widget i],[class*=chat-widget i],[id*=chatbot i],[class*=chatbot i],[class*=livechat i],"
           "iframe[title*=chat i],iframe[src*=chat i],[class*=launcher i]{display:none!important}")

BRAND_JS = r"""() => {
  const parse = s => { const m = s && s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const v = m[1].split(',').map(x => parseFloat(x)); if (v.length > 3 && v[3] < .5) return null; return v.slice(0, 3); };
  const hex = v => '#' + v.map(x => Math.round(x).toString(16).padStart(2, '0')).join('');
  const sat = ([r, g, b]) => { const mx = Math.max(r, g, b), mn = Math.min(r, g, b); return mx ? (mx - mn) / mx : 0; };
  const score = new Map(), add = (v, w) => { if (!v || sat(v) < .25 || Math.max(...v) < 40) return;
    if (v[0] < 10 && v[1] < 10 && v[2] > 225) return;   // 瀏覽器預設連結藍 #0000ee，不是品牌色
    const k = hex(v.map(x => Math.round(x / 8) * 8).map(x => Math.min(255, x))); score.set(k, (score.get(k) || 0) + w); };
  const vis = el => { const r = el.getBoundingClientRect(); return r.width > 4 && r.height > 4 && r.top < innerHeight * 3 ? r : null; };
  document.querySelectorAll('a,button,[role=button],[class*=btn],[class*=button],h1,h2,h3,header,nav,svg,[class*=badge],[class*=tag]').forEach(el => {
    const r = vis(el); if (!r) return; const cs = getComputedStyle(el), area = Math.min(r.width * r.height, 40000);
    add(parse(cs.backgroundColor), area / 400 + 4); add(parse(cs.color), 3); add(parse(cs.borderTopColor), 1);
    if (el.tagName === 'svg' || el.closest('svg')) add(parse(cs.fill), 2);
  });
  const fam = el => el ? getComputedStyle(el).fontFamily.split(',')[0].replace(/["']/g, '').trim() : null;
  const body = getComputedStyle(document.body);
  return { palette: [...score.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6).map(([c, s]) => ({ c, s: Math.round(s) })),
           bg: parse(body.backgroundColor) ? hex(parse(body.backgroundColor)) : '#ffffff', fg: parse(body.color) ? hex(parse(body.color)) : null,
           fonts: { sans: fam(document.body), display: fam(document.querySelector('h1,h2')) }, title: document.title };
}"""


def blocked(proj, url, why):
    d = proj / "assets"; d.mkdir(parents=True, exist_ok=True)
    (d / "BLOCKED.md").write_text(f"# 擷取失敗\n\n- 網址：{url}\n- 原因：{why}\n- 時間：{time.strftime('%Y-%m-%d %H:%M')}\n\n"
                                  "請使用者提供截圖（capture.py --file）或可公開的網址；不要自行畫假的產品介面冒充真實畫面。\n", "utf-8")
    print(f"✗ 擷取失敗：{why}\n  已寫入 {d / 'BLOCKED.md'}。請使用者提供截圖（--file）或可公開的網址", file=sys.stderr)
    sys.exit(1)


def save_jpeg(raw: bytes, out: Path, width: int, quality: int):
    """統一轉 JPEG、限制寬度（控制 Artifact 大小）。回傳 (寬, 高)。"""
    from io import BytesIO
    from PIL import Image
    im = Image.open(BytesIO(raw))
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255)); im = im.convert("RGBA"); bg.paste(im, mask=im.split()[-1]); im = bg
    else:
        im = im.convert("RGB")
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    if im.height > 16000:   # 瀏覽器 canvas 的安全上限
        im = im.crop((0, 0, im.width, 16000)); print("! 長截圖超過 16000px，已裁掉下方")
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
    return im.size


def log(proj, rec):
    p = proj / "assets" / "capture.json"
    data = json.loads(p.read_text("utf-8")) if p.exists() else []
    data = [d for d in data if d.get("name") != rec["name"]] + [rec]
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def write_brand(name, url, info):
    pal = [p["c"] for p in info["palette"]]
    if not pal:
        print("! 頁面上找不到有彩度的品牌色，沒有寫品牌設定檔"); return
    colors = {k: v for k, v in zip(("a1", "a2", "a3"), pal)}
    fonts = {k: v for k, v in info["fonts"].items() if v and not re.match(r"(?i)(-apple-system|system-ui|arial|helvetica|sans-serif|serif|segoe ui|blinkmacsystemfont)$", v)}
    brand = {"name": name, "url": url, "captured": time.strftime("%Y-%m-%d"), "colors": colors, "fonts": fonts,
             "site": {"bg": info["bg"], "fg": info["fg"], "palette": info["palette"]},
             "note": "colors 依網站上按鈕、標題、連結的使用量排序自動推得；交付前請使用者確認，或改成官方色碼。fonts 不在 Google Fonts 上時會退回系統字型"}
    p = SKILL / "brands" / f"{name}.json"; p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(brand, ensure_ascii=False, indent=2), "utf-8")
    print(f"✓ 品牌設定檔 {p}：a1–a3 {', '.join(colors.values())}；字型 {fonts or '（系統字型）'}")
    print("  請把色碼給使用者確認（自動推得，可能不是官方色）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("project")
    ap.add_argument("--name", required=True, help="素材名稱（場景用 pic('名稱') 引用）")
    ap.add_argument("--file", help="匯入本機圖片而不是擷取網頁")
    ap.add_argument("--size", default="1440x900", help="瀏覽器視窗，例如 1440x900、390x844")
    ap.add_argument("--scale", type=float, default=2, help="裝置像素比（2 = Retina，推近時才清楚）")
    ap.add_argument("--full", action="store_true", help="整頁長截圖")
    ap.add_argument("--element", help="只截這個 CSS 選取器的元素")
    ap.add_argument("--click", action="append", default=[], help="截圖前依序點擊的 CSS 選取器")
    ap.add_argument("--wait", type=int, default=1500, help="載入後等幾毫秒（動畫、延遲載入）")
    ap.add_argument("--dark", action="store_true", help="以深色模式開啟")
    ap.add_argument("--width", type=int, default=2400, help="輸出最大寬度（控制檔案大小）")
    ap.add_argument("--quality", type=int, default=85)
    ap.add_argument("--brand", help="另外存品牌設定檔 brands/<名稱>.json")
    ap.add_argument("--keep-widgets", action="store_true", help="保留客服聊天等浮動元件（預設隱藏）")
    ap.add_argument("--no-text", action="store_true", help="不要把頁面文字附加到 source.txt")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    out = proj / "assets" / f"{a.name}.jpg"

    if a.file:
        src = Path(a.file)
        if not src.exists():
            sys.exit(f"✗ 找不到 {src}")
        w, h = save_jpeg(src.read_bytes(), out, a.width, a.quality)
        log(proj, {"name": a.name, "from": str(src), "size": [w, h], "time": time.strftime("%Y-%m-%d %H:%M")})
        print(f"✓ {out}  {w}x{h}  {out.stat().st_size/1024:.0f}KB（來源：使用者提供的檔案）")
        return
    if not a.url:
        ap.error("需要網址或 --file")

    from playwright.sync_api import sync_playwright
    vw, vh = (int(x) for x in a.size.lower().split("x"))
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=a.scale,
                        color_scheme="dark" if a.dark else "light", locale="zh-TW")
        try:
            resp = pg.goto(a.url, wait_until="networkidle", timeout=45000)
        except Exception as e:  # noqa: BLE001
            try:
                resp = pg.goto(a.url, wait_until="load", timeout=30000)
            except Exception:  # noqa: BLE001
                b.close(); blocked(proj, a.url, f"打不開（{str(e).splitlines()[0][:120]}）")
        if resp is not None and resp.status >= 400:
            b.close(); blocked(proj, a.url, f"HTTP {resp.status}")
        pg.add_style_tag(content=HIDE if a.keep_widgets else HIDE + WIDGETS)
        pg.wait_for_timeout(a.wait)
        for sel in a.click:
            try:
                pg.click(sel, timeout=8000); pg.wait_for_timeout(800)
            except Exception:  # noqa: BLE001
                b.close(); blocked(proj, a.url, f"找不到要點擊的元素 {sel}")
        text = pg.evaluate("document.body ? document.body.innerText : ''")
        if re.search(r"(?i)(sign in|log in|登入|登录)", pg.title() + text[:400]) and len(text) < 600:
            b.close(); blocked(proj, a.url, "看起來是登入頁（需要帳號的畫面請使用者自己截圖後用 --file 匯入）")
        if len(text.strip()) < 15 and not a.element:
            print("! 頁面幾乎沒有文字，可能還沒載入完：用 --wait 3000 再試，或用 view 看一下截圖")
        if a.full:   # 觸發延遲載入的圖片
            pg.evaluate("async () => { for (let y = 0; y < document.body.scrollHeight; y += innerHeight * .8) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } scrollTo(0, 0); }")
            pg.wait_for_timeout(600)
        if a.element:
            el = pg.query_selector(a.element)
            if not el:
                b.close(); blocked(proj, a.url, f"找不到元素 {a.element}")
            raw = el.screenshot(type="png")
        else:
            raw = pg.screenshot(type="png", full_page=a.full)
        info = pg.evaluate(BRAND_JS) if a.brand else None
        final_url = pg.url
        b.close()

    w, h = save_jpeg(raw, out, a.width, a.quality)
    log(proj, {"name": a.name, "url": final_url, "viewport": [vw, vh], "scale": a.scale, "full": a.full,
               "element": a.element, "size": [w, h], "time": time.strftime("%Y-%m-%d %H:%M")})
    print(f"✓ {out}  {w}x{h}  {out.stat().st_size/1024:.0f}KB  ← {final_url}")
    if not a.no_text and text.strip():
        sp = proj / "source.txt"
        old = sp.read_text("utf-8") if sp.exists() else ""
        if f"# 擷取自 {final_url}\n" not in old:
            clean = "\n".join(ln.strip() for ln in text.splitlines() if ln.strip())
            sp.write_text(old + ("\n\n" if old else "") + f"# 擷取自 {final_url}\n{clean[:20000]}\n", "utf-8")
            print(f"✓ 頁面文字已附加到 {sp.name}（{len(clean)} 字），文案與數字只能用這裡有的")
    if info:
        write_brand(a.brand, final_url, info)


if __name__ == "__main__":
    main()
