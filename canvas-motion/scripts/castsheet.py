#!/usr/bin/env python3
"""角色設定表（美術交付物）：把 cast 裡每個角色畫成全身＋半身＋四種表情，給使用者確認外型。

用法：python3 castsheet.py <專案或 storyboard.json> [--out cast.png]
cast 的格式見 references/character.md（Open Peeps：body、head、face、colors…）。
"""
import argparse, base64, json, shutil, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401
from build import build  # noqa: E402
from _browser import open_page  # noqa: E402

SCENE = r"""
function sCastSheet(t, T, pulse, s) {
  STYLE.overlay = null; STYLE.letterbox = 0;
  ctx.fillStyle = STYLE.c.bg; ctx.fillRect(0, 0, W, H);
  const names = Object.keys(PROJECT.cast || {}), n = Math.max(1, names.length), rowH = (H - SAFE.y) / n, EX = ['Calm', 'Smile', 'Awe', 'Concerned'];
  names.forEach((nm, r) => {
    const y0 = SAFE.y * .6 + r * rowH, base = peepCast(nm, { blink: false, idle: false }), full = !!(PEEPS.standing[base.body] || PEEPS.sitting[base.body]);
    txtPlate(nm + (base.note ? '｜' + base.note : ''), SAFE.x, y0 + rowH * .06, { size: Math.min(fz('body'), rowH * .08), weight: 800, maxW: W * .4 });
    if (full) peep(SAFE.x + W * .1, y0 + rowH * .95, rowH * .8, base, 0);
    else peepBust(SAFE.x + W * .1, y0 + rowH * .95, rowH * .75, base, 0);
    EX.forEach((f, k) => {
      peepBust(W * .38 + k * W * .15, y0 + rowH * .95, rowH * .62, { ...base, body: full ? 'Tee' : base.body, face: f }, 0);
      txt(f, W * .38 + k * W * .15, y0 + rowH * .14, { size: Math.min(fz('cap'), rowH * .06), color: STYLE.c.mute, align: 'center', maxW: W * .12 });
    });
  });
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out")
    a = ap.parse_args()
    src = Path(a.src)
    cfg = json.loads((src / "project.json" if src.is_dir() else src).read_text("utf-8"))
    if not cfg.get("cast"):
        sys.exit("✗ 沒有 cast（角色設定），格式見 references/character.md")
    base = src if src.is_dir() else src.parent
    out = Path(a.out) if a.out else base / "sheets" / "cast.png"
    with tempfile.TemporaryDirectory() as td:
        p = Path(td); (p / "scenes").mkdir()
        (p / "scenes" / "cast.js").write_text(SCENE, "utf-8")
        (p / "project.json").write_text(json.dumps({"title": "cast", "style": cfg.get("style", "minimal"), "cast": cfg["cast"], "music": False,
                                                    "webfonts": False, "scenes": [{"fn": "sCastSheet", "bars": 1}]}, ensure_ascii=False), "utf-8")
        html = build(p, quiet=True)
        with open_page(html) as pg:
            url = pg.evaluate("() => { __cm.resize(1920, 1080, 1); __cm.frame(.1); return CV.toDataURL('image/png'); }")
            errs = pg.evaluate("__cm.errors")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(url.split(",", 1)[1]))
    for e in errs:
        print(f"✗ {e['fn']}：{e['msg']}")
    print(f"✓ 角色設定表 {out}")


if __name__ == "__main__":
    main()
