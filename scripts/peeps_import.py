"""（維護用）把 opeepsfun/open-peeps 的 TSX 部件轉成 library/peeps/open-peeps.json：{分類: {名稱: {w, h, vb, defaults, paths:[[d, fill, stroke?]]}}}。
fill 是顏色字串，或 "$變數名"（例如 $skinColor）。只讀文字，不執行原始碼。
來源：https://github.com/opeepsfun/open-peeps（插畫為 Pablo Stanley 的 Open Peeps，CC0；套件程式碼 MIT，這裡只取插畫路徑）。
用法：下載該 repo 的 tarball 解開到一個空資料夾，python -I peeps_import.py <該資料夾> <SKILL>/library/peeps/open-peeps.json"""
import json, re, sys
from pathlib import Path

root, out = Path(sys.argv[1]), Path(sys.argv[2])
ATTR = re.compile(r"(\w[\w-]*)=(?:'([^']*)'|\"([^\"]*)\"|\{([^}]*)\})")


def parse(fp):
    s = fp.read_text("utf-8")
    vb = re.search(r'viewBox:\s*"([^"]+)"', s)
    sig = re.search(r"=\s*\(\{([^}]*)\}\)\s*=>", s)
    defaults = {}
    if sig:
        for k, v in re.findall(r"(\w+)\s*=\s*\"([^\"]*)\"", sig.group(1)):
            defaults[k] = v
    paths = []
    for tag, body in re.findall(r"<(path|rect)\b(.*?)/>", s, re.S):
        a = {}
        for m in ATTR.finditer(body):
            a[m.group(1)] = m.group(2) or m.group(3) or ("$" + m.group(4).strip() if m.group(4) else "")
        if tag == "rect":
            x, y, w, h = (float(a.get(k, 0)) for k in ("x", "y", "width", "height"))
            a["d"] = f"M{x} {y}h{w}v{h}h{-w}Z"
        if not a.get("d"):
            continue
        item = [a["d"], a.get("fill", "none")]
        if a.get("stroke"):
            item += [a["stroke"], a.get("strokeWidth", "1")]
        if a.get("fillRule") == "evenodd" or a.get("fill-rule") == "evenodd":
            item.append("evenodd")
        paths.append(item)
    v = [float(x) for x in vb.group(1).split()] if vb else None
    return {"vb": v, "defaults": defaults, "paths": paths}


lib = next(root.glob("opeepsfun-*")) / "lib"
EXCLUDE = {"Killer"}   # 拿刀的半身像：產品與企業影片不適用
data = {}
for cat in ["body/standing", "body/sitting", "body/effigy", "face", "head", "beard", "accessory"]:
    d = data.setdefault(cat.split("/")[-1], {})
    for fp in sorted((lib / cat).glob("*.tsx")):
        if fp.stem in EXCLUDE:
            continue
        d[fp.stem] = parse(fp)
out.write_text(json.dumps(data, separators=(",", ":")), "utf-8")
print({k: len(v) for k, v in data.items()}, f"{out.stat().st_size / 1e6:.2f}MB")


# 官方半身像（Effigy.tsx）的組裝座標與各部件的位移微調
eff = (lib / "Effigy.tsx").read_text("utf-8")
offsets = {}
for fn in ("createHair", "createFace", "createBeard", "createAccessory", "createHead", "createBody"):
    m = re.search(rf"const {fn} = .*?\n}};", eff, re.S)
    if not m:
        continue
    tbl = {}
    for name, tr in re.findall(r'\.type === "(\w+)"\)\s*\{\s*return <g transform=\'([^\']+)\'', m.group(0)):
        t = re.search(r"translate\(([-\d.]+)[ ,]+([-\d.]+)\)", tr); s = re.search(r"scale\(([-\d.]+)[ ,]+([-\d.]+)\)", tr)
        tbl[name] = [float(t.group(1)) if t else 0, float(t.group(2)) if t else 0, float(s.group(1)) if s else 1, float(s.group(2)) if s else 1]
    offsets[fn] = tbl
groups = {g: [float(a), float(b)] for g, a, b in re.findall(r"<g id='(\w+)' transform='translate\(([-\d.]+), ([-\d.]+)\)", eff)}
data["_layout"] = {"groups": groups, "offsets": offsets}
out.write_text(json.dumps(data, separators=(",", ":")), "utf-8")
print("layout", groups, {k: len(v) for k, v in offsets.items()})
