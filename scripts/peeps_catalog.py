#!/usr/bin/env python3
"""（維護用）把 Open Peeps 部件畫成型錄圖：references/peeps/standing.jpg、sitting.jpg、bust.jpg、face.jpg、head.jpg、extra.jpg。
寫場景前用 view 看型錄挑部件名稱。部件資料更新（peeps_import.py）後重跑。用法：python3 peeps_catalog.py"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _utf8  # noqa: E402,F401

SKILL = Path(__file__).resolve().parent.parent
JS = r"""
const c = document.getElementById('c'), x = c.getContext('2d'), G = P._layout.groups, OF = P._layout.offsets;
x.fillStyle = '#f6f4ee'; x.fillRect(0, 0, c.width, c.height);
const V = { skinColor: '#F1C9A5', topColor: '#4860e8', pantsColor: '#202848', jacketColor: '#8FA7DF', blazerColor: '#8FA7DF' };
function part(it, ox = 0, oy = 0) {
  const v = Object.assign({}, it.defaults, V), col = s => s && s[0] === '$' ? (v[s.slice(1)] || '#000') : s;
  x.save(); x.translate(ox, oy);
  for (const p of it.paths) { const path = new Path2D(p[0]), f = col(p[1]);
    if (f && f !== 'none') { x.fillStyle = f; x.fill(path, p[p.length - 1] === 'evenodd' ? 'evenodd' : 'nonzero'); }
    if (p[2] && p[2] !== 'none' && p[2] !== 'evenodd') { x.strokeStyle = col(p[2]); x.lineWidth = +p[3] || 1; x.stroke(path); } }
  x.restore();
}
function headAt(face, hair, bx, by, s, body) {   // 用半身像座標畫一顆頭（型錄的臉與髮型）
  x.save(); x.translate(bx, by); x.scale(s, s); x.translate(-531, -300);
  if (hair) { x.save(); x.translate(G.Hair[0], G.Hair[1]); const o = OF.createHair[hair]; if (o) { x.translate(o[0], o[1]); x.scale(o[2], o[3]); } part(P.head[hair]); x.restore(); }
  else part(P.head.NoHairTwo, G.Hair[0], G.Hair[1]);
  part(P.face[face || 'Calm'], G.Face[0], G.Face[1]); x.restore();
}
const names = Object.keys(P[CAT] || {}), cols = COLS, cw = c.width / cols, ch = (c.height - 70) / Math.ceil(names.length / cols);
x.fillStyle = '#1d2333'; x.font = '800 30px "Microsoft JhengHei", sans-serif'; x.fillText(TITLE, 24, 46);
names.forEach((k, i) => {
  const cx = (i % cols) * cw, cy = 70 + Math.floor(i / cols) * ch, it = P[CAT][k];
  if (CAT === 'face') headAt(k, 'ShortTwo', cx + cw / 2, cy + ch * .38, Math.min(cw, ch) * .0028);
  else if (CAT === 'head') headAt('Calm', k, cx + cw / 2, cy + ch * .46, Math.min(cw, ch) * .0022);
  else if (CAT === 'effigy') { const s = Math.min(cw * .9 / 940, (ch - 30) / 1130); x.save(); x.translate(cx + cw / 2 - 654 * s, cy); x.scale(s, s);
    part(it, G.Body[0], G.Body[1]); const ho = OF.createHead[k]; if (ho) x.translate(ho[0], ho[1]); part(P.head.ShortTwo, G.Hair[0], G.Hair[1]); part(P.face.Calm, G.Face[0], G.Face[1]); x.restore(); }
  else { const [, , w, h] = it.vb, s = Math.min(cw * .85 / w, (ch - 30) / h); x.save(); x.translate(cx + cw / 2 - w * s / 2, cy + 4); x.scale(s, s); part(it); x.restore(); }
  x.fillStyle = '#333'; x.font = '600 15px sans-serif'; x.textAlign = 'center'; x.fillText(k, cx + cw / 2, cy + ch - 8); x.textAlign = 'left';
});
"""
SHEETS = [("standing", "全身站姿（peep body）", 8, 1600, 1300), ("sitting", "全身坐姿（peep body）", 6, 1600, 900),
          ("effigy", "半身（peepBust body）", 7, 1600, 1250), ("face", "表情（face）", 9, 1600, 1100),
          ("head", "髮型（head）", 11, 1700, 1350), ("beard", "鬍子（beard）", 8, 1400, 500), ("accessory", "配件（acc）", 9, 1400, 300)]


def main():
    from playwright.sync_api import sync_playwright
    data = (SKILL / "library" / "peeps" / "open-peeps.json").read_text("utf-8")
    out = SKILL / "references" / "peeps"; out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for cat, title, cols, w, h in SHEETS:
            pg = b.new_page(viewport={"width": w, "height": h}); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            js = f"const P={data}; const CAT={json.dumps(cat)}, TITLE={json.dumps(title, ensure_ascii=False)}, COLS={cols};" + JS
            pg.set_content(f"<!doctype html><meta charset=utf-8><body style='margin:0'><canvas id=c width={w} height={h}></canvas><script>{js}</script>")
            pg.wait_for_timeout(200)
            f = out / f"{'bust' if cat == 'effigy' else cat}.jpg"
            pg.screenshot(path=str(f), type="jpeg", quality=78); pg.close()
            print(("✗ " + errs[0]) if errs else f"✓ {f.name}")
        b.close()


if __name__ == "__main__":
    main()
