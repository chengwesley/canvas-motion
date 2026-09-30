#!/usr/bin/env python3
"""角色設定表（美術交付物）：把 cast 裡每個角色畫成 正面／3/4 側／側面 ＋ 四種表情，給使用者確認外型。

用法：python3 castsheet.py <專案或 storyboard.json> [--out cast.png]
讀 project.json（或 storyboard.json）的 style 與 cast，輸出 <專案>/sheets/cast.png。
"""
import argparse, base64, json, shutil, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401
from build import build  # noqa: E402
from _browser import open_page  # noqa: E402

SCENE = r"""
function sCastSheet(t, T, pulse, s) {
  STYLE.overlay = null; STYLE.letterbox = 0;   // a design sheet shows the whole frame: no letterbox or grading
  const names = Object.keys(PROJECT.cast || {}), n = Math.max(1, names.length);
  const rowH = (H - SAFE.y * 1.4) / n, EX = ['neutral', 'happy', 'angry', 'surprised'];
  ctx.fillStyle = STYLE.c.bg; ctx.fillRect(0, 0, W, H);
  names.forEach((nm, r) => {
    const y0 = SAFE.y * .8 + r * rowH, ground = y0 + rowH * .92, hgt = rowH * .8;
    const F = figCast(nm, hgt), spec = PROJECT.cast[nm];
    txtPlate(nm + (spec.note ? '｜' + spec.note : ''), SAFE.x, y0 + rowH * .06, { size: Math.min(fz('body'), rowH * .07), weight: 800, maxW: W * .5 });
    [[0, 1], [.5, 1], [1, 1], [1, -1]].forEach(([v, d], k) => {
      figDraw(F, SAFE.x + W * .07 + k * W * .12, ground, figPose.key(k === 3 ? 'point' : 'stand'), { view: v, dir: d, t: 0, blink: false });
    });
    // expression close-ups: head only (clipped), so the face reads at a glance
    EX.forEach((e, k) => {
      const hx = W * .62 + k * W * .095, hr = Math.min(W * .038, rowH * .24), F2 = figCast(nm, hr * 2 / F.P.head * 1.02);
      const cy = y0 + rowH * .45;
      ctx.save(); ctx.beginPath(); ctx.arc(hx, cy, hr * 1.55, 0, 6.283); ctx.fillStyle = rgba(STYLE.c.fg, .06); ctx.fill(); ctx.clip();
      const J = _figJoints(F2, figPose.zero(), 1, .25), head = J.head, low = Math.max(J.ftR.y, J.ftL.y, J.anR.y, J.anL.y);
      figDraw(F2, hx - head.x, cy - (head.y - low), figPose.zero(), { view: .25, t: 0, blink: false, face: EXPR[e], shadow: false });
      ctx.restore();
      txt(e, hx, cy + hr * 1.9, { size: Math.min(fz('cap'), rowH * .06), align: 'center', color: STYLE.c.mute, maxW: W * .09 });
    });
  });
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--out")
    a = ap.parse_args()
    src = Path(a.project).resolve()
    cfg_path = src if src.suffix == ".json" else src / "project.json"
    cfg = json.loads(cfg_path.read_text("utf-8"))
    if not cfg.get("cast"):
        sys.exit("✗ 沒有 cast（角色設定）")
    tmp = Path(tempfile.mkdtemp(prefix="cm-cast-"))
    (tmp / "scenes").mkdir()
    (tmp / "scenes" / "castsheet.js").write_text(SCENE, "utf-8")
    proj = {k: cfg[k] for k in ("title", "style", "cast") if k in cfg}
    proj.update({"music": False, "scenes": [{"fn": "sCastSheet", "bars": 2}]})
    (tmp / "project.json").write_text(json.dumps(proj, ensure_ascii=False), "utf-8")
    if (src.parent if src.suffix == ".json" else src).joinpath("styles").exists():
        shutil.copytree((src.parent if src.suffix == ".json" else src) / "styles", tmp / "styles")
    html = build(tmp, quiet=True)
    with open_page(html) as pg:
        url = pg.evaluate("() => { __cm.resize(1920, 1080, 1); __cm.frame(1); return CV.toDataURL('image/png'); }")
        errs = pg.evaluate("__cm.errors")
    base = src.parent if src.suffix == ".json" else src
    out = Path(a.out) if a.out else base / "sheets" / "cast.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(url.split(",", 1)[1]))
    shutil.rmtree(tmp, ignore_errors=True)
    for e in errs:
        print(f"✗ {e['fn']}：{e['msg']}")
    print(f"✓ 角色設定表 {out}")
    sys.exit(2 if errs else 0)


if __name__ == "__main__":
    main()
