#!/usr/bin/env python3
"""依情境產生風格：錨點風格 + 參數覆寫 → 驗證（對比、字體、節奏）→ 自動修正 → 產出 STYLE JS。

用法：
  python3 style_gen.py spec.json [--out <專案>/styles/<name>.js]   # 產生並印出驗證報告
  python3 style_gen.py --anchors                                  # 列出錨點與它們的基本參數
也可以直接把 spec 寫進 project.json 的 "style"（物件），build.py 會自動呼叫本模組。

spec 格式見 styles/_schema.json。只有 base 必填，其他欄位都是覆寫。
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401  UTF-8 輸出（Windows cp950 也不會當掉）
from urllib.parse import quote_plus

SKILL = Path(__file__).resolve().parent.parent
TRANS = {"cut", "fade", "push", "wipe", "zoom", "iris", "flash", "glitch"}
CJK = '"Noto Sans TC","Noto Sans CJK TC","PingFang TC","Microsoft JhengHei"'
BG_KINDS = {"base", "solid", "gradient", "glow", "grid", "dots", "paper"}


# ---------- 色彩 ----------
def parse_color(s):
    s = s.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)), 1.0
    m = re.findall(r"[\d.]+", s)
    if len(m) >= 3:
        return tuple(int(float(x)) for x in m[:3]), float(m[3]) if len(m) > 3 else 1.0
    raise ValueError(f"無法解析顏色 {s}")


def hexc(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in rgb)


def lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb)
    return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


def fix_contrast(col, bg, target):
    """把 col 往遠離 bg 的方向（黑或白）推，直到對比達標。回傳 (新顏色, 是否有調整)。"""
    if contrast(col, bg) >= target:
        return col, False
    to = (0, 0, 0) if lum(bg) > .4 else (255, 255, 255)
    c = col
    for k in range(1, 41):
        p = k / 40
        c = tuple(col[i] + (to[i] - col[i]) * p for i in range(3))
        if contrast(c, bg) >= target:
            break
    return c, True


# ---------- 錨點 ----------
def anchor_src(name):
    p = SKILL / "styles" / f"{name}.js"
    if not p.exists() or name.startswith("_"):
        avail = ", ".join(anchors())
        raise SystemExit(f"✗ 沒有錨點風格 {name}（可用：{avail}）")
    return p.read_text("utf-8")


def anchors():
    return sorted(p.stem for p in (SKILL / "styles").glob("*.js") if not p.stem.startswith("_"))


def anchor_info(src):
    m = re.search(r"\bc:\s*\{(.*?)\}", src, re.S)
    colors = dict(re.findall(r"(\w+):\s*'([^']+)'", m.group(1))) if m else {}
    bpm = re.search(r"bpm:\s*(\d+)", src)
    return {"colors": colors, "light": bool(re.search(r"light:\s*true", src)),
            "bpm": int(bpm.group(1)) if bpm else 120,
            "fonts_line": (re.search(r"^// @fonts .*$", src, re.M) or [None])[0]}


# ---------- 背景建構器 ----------
def bg_js(kind, p):
    amt = float(p.get("amount", .5))
    if kind == "solid":
        return "function (time) { ctx.fillStyle = this.c.bg; ctx.fillRect(0, 0, W, H); }"
    if kind == "gradient":
        return f"""function (time) {{
    const L = cached('gen-grad', W / 4, H / 4, (x, w, h) => {{
      const g = x.createLinearGradient(0, 0, w * .4, h); g.addColorStop(0, this.c.bg);
      g.addColorStop(1, mixc(this.c.bg, this.c.a1, {amt * .35:.3f})); x.fillStyle = g; x.fillRect(0, 0, w, h); }});
    ctx.drawImage(L, 0, 0, W, H);
  }}"""
    if kind == "glow":
        return f"""function (time, pulse) {{
    const L = cached('gen-glow', W / 4, H / 4, (x, w, h) => {{
      x.fillStyle = this.c.bg; x.fillRect(0, 0, w, h);
      for (const [px, py, r, col] of [[.25, .3, .9, this.c.a1], [.78, .72, .8, this.c.a2]]) {{
        const g = x.createRadialGradient(w * px, h * py, 0, w * px, h * py, Math.min(w, h) * r);
        g.addColorStop(0, rgba(col, {amt * .3:.3f})); g.addColorStop(1, rgba(col, 0)); x.fillStyle = g; x.fillRect(0, 0, w, h); }} }});
    const dx = Math.sin(time * .21) * W * .03, dy = Math.cos(time * .17) * H * .03;
    ctx.drawImage(L, -W * .05 + dx, -H * .05 + dy, W * 1.1, H * 1.1);
  }}"""
    if kind == "grid":
        return f"""function (time, pulse) {{
    ctx.fillStyle = this.c.bg; ctx.fillRect(0, 0, W, H);
    const s = MIN * {float(p.get('spacing', .08)):.3f}, o = (time * s * .15) % s;
    ctx.save(); ctx.strokeStyle = this.c.line; ctx.lineWidth = 1; ctx.globalAlpha = {.5 + amt * .5:.2f};
    for (let x = -s + o; x < W + s; x += s) {{ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }}
    for (let y = -s + o; y < H + s; y += s) {{ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }}
    ctx.restore();
  }}"""
    if kind == "dots":
        return f"""function (time) {{
    const L = cached('gen-dots', W, H, (x, w, h) => {{
      x.fillStyle = this.c.bg; x.fillRect(0, 0, w, h); x.fillStyle = this.c.line;
      const s = Math.min(w, h) * {float(p.get('spacing', .04)):.3f}, r = Math.max(1, s * .08);
      for (let yy = s / 2; yy < h; yy += s) for (let xx = s / 2; xx < w; xx += s) {{ x.beginPath(); x.arc(xx, yy, r, 0, 6.283); x.fill(); }} }});
    ctx.drawImage(L, 0, 0, W, H);
  }}"""
    if kind == "paper":
        return f"""function (time) {{
    const L = cached('gen-paper', W / 2, H / 2, (x, w, h) => {{
      x.fillStyle = this.c.bg; x.fillRect(0, 0, w, h); const R = rng(7);
      for (let i = 0; i < w * h / 60; i++) {{ x.fillStyle = rgba(this.c.fg, R() * {.03 * amt + .01:.3f}); x.fillRect(R() * w, R() * h, 1, 1); }} }});
    ctx.drawImage(L, 0, 0, W, H);
  }}"""
    raise ValueError(kind)


# ---------- 產生 ----------
def fonts_from(spec_fonts):
    fams, stacks = [], {}
    for role in ("sans", "display", "mono"):
        f = spec_fonts.get(role)
        if not f:
            continue
        if f not in fams:
            fams.append(f)
        tail = 'ui-monospace,"SF Mono",Menlo,monospace' if role == "mono" else CJK + ",sans-serif"
        stacks[role] = f'"{f}",{tail}'
    if "Noto Sans TC" not in fams:
        fams.append("Noto Sans TC")
    url = "https://fonts.googleapis.com/css2?" + "&".join(
        f"family={quote_plus(f)}:wght@400;700;900" for f in fams) + "&display=swap"
    return url, stacks


def generate(spec):
    """回傳 (js 原始碼, 報告列表)。報告每筆以 '✓'、'!' 開頭。"""
    if isinstance(spec, str):
        return anchor_src(spec), []
    rep = []
    base = spec.get("base") or "minimal"
    src = anchor_src(base)
    info = anchor_info(src)
    name = re.sub(r"[^a-z0-9_-]", "", str(spec.get("name", f"{base}-custom")).lower()) or "custom"

    colors = dict(info["colors"])
    colors.update(spec.get("colors", {}))
    bg_rgb, _ = parse_color(colors["bg"])
    light = lum(bg_rgb) > .4
    if light != info["light"]:
        rep.append(f"! 背景明暗與錨點 {base} 不同，已自動設定 light={str(light).lower()}")
    for key, target in (("fg", 4.5), ("mute", 3.0), ("a1", 3.0)):
        if key not in colors:
            continue
        rgb, a = parse_color(colors[key])
        new, changed = fix_contrast(rgb, bg_rgb, target)
        if changed:
            colors[key] = hexc(new)
            rep.append(f"! {key} 與背景對比不足 {target}:1，已自動調整為 {colors[key]}（品牌色時請告知使用者）")
    fg_rgb, _ = parse_color(colors["fg"])
    fg = "%d,%d,%d" % tuple(round(v) for v in fg_rgb)
    for k, a in (("line", .09), ("card", .05 if not light else 1), ("cardLine", .13)):
        if k not in spec.get("colors", {}) and k not in info["colors"]:
            colors[k] = "#ffffff" if (k == "card" and light) else f"rgba({fg},{a})"
    colors.setdefault("flash", "#ffffff")

    over = {"name": name, "light": light, "c": colors}
    fonts_line = info["fonts_line"]
    if spec.get("fonts"):
        url, stacks = fonts_from(spec["fonts"])
        fonts_line = f"// @fonts {url}"
        over["fonts"] = stacks

    post = dict(spec.get("post", {}))
    if light and post.get("bloom", 0):
        rep.append("! 亮底不可開 bloom，已設為 0")
    if light:
        post["bloom"] = 0
    if post:
        over["post"] = post

    if spec.get("trans"):
        bad = [t for t in spec["trans"] if t not in TRANS]
        if bad:
            rep.append(f"! 移除不支援的轉場：{', '.join(bad)}")
        over["trans"] = [t for t in spec["trans"] if t in TRANS] or ["push", "fade"]

    music = dict(spec.get("music", {}))
    if "bpm" in music:
        b = int(music["bpm"])
        if not 70 <= b <= 140:
            music["bpm"] = min(140, max(70, b))
            rep.append(f"! bpm {b} 超出 70–140，已調為 {music['bpm']}")
    if "chords" in music:
        ok = all(3 <= len(ch) <= 5 and all(36 <= n <= 96 for n in ch) for ch in music["chords"])
        if not ok:
            del music["chords"]
            rep.append("! chords 需每個和弦 3–5 音、MIDI 36–96，已改用錨點和弦")

    card = spec.get("card", {})
    for k, v in (("cardR", card.get("r")), ("cardLw", card.get("lw")), ("cardShadow", card.get("shadow"))):
        if v is not None:
            over[k] = v

    body = src.replace(info["fonts_line"] or "\0", "").replace("const STYLE =", "const __ANCHOR =", 1)
    js = [fonts_line or "", f"/* 由 style_gen.py 產生：錨點 {base} → {name}。{spec.get('mood', '')} */", body,
          f"const STYLE = Object.assign({{}}, __ANCHOR, {json.dumps({k: v for k, v in over.items() if k not in ('c', 'post')}, ensure_ascii=False)});",
          f"STYLE.c = Object.assign({{}}, __ANCHOR.c, {json.dumps(colors, ensure_ascii=False)});",
          f"STYLE.post = Object.assign({{}}, __ANCHOR.post, {json.dumps(post)});",
          f"STYLE.music = Object.assign({{}}, __ANCHOR.music, {json.dumps(music)});"]
    kind = (spec.get("background") or {}).get("kind", "base")
    if kind not in BG_KINDS:
        rep.append(f"! 不支援的背景 {kind}，改用錨點背景")
        kind = "base"
    if kind != "base":
        js.append(f"STYLE.bg = {bg_js(kind, spec['background'])};")
    fg_bg = contrast(parse_color(colors['fg'])[0], bg_rgb)
    rep.insert(0, f"✓ 風格 {name}（錨點 {base}，{'亮' if light else '暗'}底，背景 {kind}，fg/bg 對比 {fg_bg:.1f}:1）")
    return "\n".join(js) + "\n", rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--anchors", action="store_true")
    a = ap.parse_args()
    if a.anchors:
        for n in anchors():
            i = anchor_info(anchor_src(n))
            print(f"  {n:<11} {'亮' if i['light'] else '暗'}底  bpm {i['bpm']:<4} bg {i['colors'].get('bg')}  a1 {i['colors'].get('a1')}")
        return
    if not a.spec:
        ap.error("需要 spec.json（或 --anchors）")
    spec = json.loads(Path(a.spec).read_text("utf-8"))
    js, rep = generate(spec)
    print("\n".join(rep))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(js, "utf-8")
        print(f"✓ 已寫入 {a.out}")


if __name__ == "__main__":
    main()
