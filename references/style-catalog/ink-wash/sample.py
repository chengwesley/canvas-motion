# Ink-wash (shuimo) style sample: an ink-drawn robot files a note card into a drawer cabinet; big 61%.
# Technique: xuan paper -> pale washes first (far) -> mid washes -> bone strokes (gou le) dark last,
# ink layers MULTIPLY so overlaps darken (ji mo); dry-brush (fei bai) from hair dropout; one cinnabar seal.
import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 1080, 1350
SS = 2  # supersample factor for brush strokes
R = random.Random(1961)
HERE = os.path.dirname(os.path.abspath(__file__))
HEI = "/System/Library/Fonts/STHeiti Medium.ttc"          # Chinese glyphs only from STHeiti / Hiragino
NUM = "/System/Library/Fonts/Supplemental/Songti.ttc"      # Latin digits only (index 0, Black)

# Palette (must match style.md)
PAPER = (240, 233, 216)      # xuan paper
PAPER_DK = (222, 211, 188)   # paper mottling
CARD = (252, 249, 241)       # note card: brighter than paper (the only "lifted white")
INK = (24, 22, 20)           # jiao mo (scorched ink), all ink tones are densities of this
CINNABAR = (178, 40, 30)     # seal paste, used once
# ink densities (0-255 alpha of INK over paper): 5 tones of "mo fen wu se"
JIAO, NONG, ZHONG, DAN, QING = 245, 200, 140, 80, 36


def check_glyphs(path, text, size=80):
    """Fail loudly if any CJK char would render as tofu / notdef."""
    f = ImageFont.truetype(path, size)
    def m(ch):
        im = Image.new("L", (size * 2, size * 2), 0)
        ImageDraw.Draw(im).text((size // 2, size // 2), ch, font=f, fill=255)
        return im
    notdef = m("\U000F0000").tobytes()
    for ch in text:
        b = m(ch)
        assert b.getbbox() and b.tobytes() != notdef, f"missing glyph {ch!r} in {path}"


def rice_paper():
    sw, sh = W // 8, H // 8
    n = Image.new("L", (sw, sh)); n.putdata([R.randint(0, 255) for _ in range(sw * sh)])
    n = n.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(4))
    img = Image.composite(Image.new("RGB", (W, H), PAPER_DK), Image.new("RGB", (W, H), PAPER),
                          n.point(lambda v: int(max(0, v - 140) * 0.35)))
    d = ImageDraw.Draw(img)
    for _ in range(1100):  # fibres
        x, y = R.uniform(0, W), R.uniform(0, H)
        a, L = R.uniform(0, math.pi), R.uniform(4, 20)
        c = R.randint(212, 230)
        d.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], fill=(c, c - 6, c - 16), width=1)
    return img


def ink(img, mask, color=INK):
    """Multiply ink onto paper so overlapping layers accumulate (ji mo)."""
    k = [1 - c / 255 for c in color]
    layer = Image.merge("RGB", [mask.point(lambda v, kk=kk: int(255 - v * kk)) for kk in k])
    return ImageChops.multiply(img, layer)


def wash(img, cx, cy, rx, ry, dens, blobs=14, blur=26, rim=0.35):
    """Wet wash (po mo): soft blobs; a darker tide-line rim where water dried."""
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for _ in range(blobs):
        x, y = cx + R.gauss(0, rx * 0.4), cy + R.gauss(0, ry * 0.4)
        a, b = R.uniform(0.35, 0.7) * rx, R.uniform(0.35, 0.7) * ry
        d.ellipse([x - a, y - b, x + a, y + b], fill=255)
    hard = m.filter(ImageFilter.GaussianBlur(blur * 0.35)).point(lambda v: 255 if v > 110 else 0)
    body = hard.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * dens / 255))
    edge = ImageChops.subtract(hard, hard.filter(ImageFilter.MinFilter(5))).filter(ImageFilter.GaussianBlur(2))
    body = ImageChops.add(body, edge.point(lambda v: int(v * dens * rim / 255)))
    return ink(img, body)


def wash_poly(img, pts, dens, blur=6, rim=0.5, grad=None):
    """Wash filling a shape (mo gu fill) with tide-line edge.
    grad=(dx, dy): ink gets denser toward that direction (shadow side); the lit side stays near paper."""
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    jit = Image.effect_noise((W // 4, H // 4), 60).resize((W, H), Image.BICUBIC)
    body = ImageChops.multiply(m.filter(ImageFilter.GaussianBlur(blur)), jit.point(lambda v: 170 + v // 4))
    if grad:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
        steps = 40
        for i in range(steps):  # linear ramp 25% -> 100% along grad direction
            t = i / (steps - 1); v = int(255 * (0.25 + 0.75 * t))
            if grad[0]:
                gd.rectangle([x0 + (x1 - x0) * i / steps, y0, x0 + (x1 - x0) * (i + 1) / steps + 1, y1], fill=v)
            else:
                gd.rectangle([x0, y0 + (y1 - y0) * i / steps, x1, y0 + (y1 - y0) * (i + 1) / steps + 1], fill=v)
        body = ImageChops.multiply(body, g.filter(ImageFilter.GaussianBlur(8)))
    body = body.point(lambda v: int(v * dens / 255))
    edge = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(5))).filter(ImageFilter.GaussianBlur(1.5))
    return ink(img, ImageChops.add(body, edge.point(lambda v: int(v * dens * rim / 255))))


def far_hills(img, y_base, amp, dens, seed, x0=0, x1=W, fade=110):
    """Distant ridge (yuan shan): densest along the ridge line, dissolving downward into mist."""
    rr = random.Random(seed)
    ph = [rr.uniform(0, 6.28) for _ in range(3)]
    ridge = [(x, y_base - amp * (0.55 * math.sin(x / 140 + ph[0]) + 0.3 * math.sin(x / 61 + ph[1]) + 0.15 * math.sin(x / 23 + ph[2])))
             for x in range(int(x0), int(x1) + 1, 6)]
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for k in range(fade):  # stacked ridge copies, each fainter and lower
        v = int(dens * (1 - k / fade) ** 1.6)
        d.line([(x, y + k) for x, y in ridge], fill=v, width=2)
    return ink(img, m.filter(ImageFilter.GaussianBlur(5)))


def smooth(pts, n):
    """Catmull-Rom through control points -> n samples."""
    if len(pts) == 2:
        return [(pts[0][0] + (pts[1][0] - pts[0][0]) * i / n, pts[0][1] + (pts[1][1] - pts[0][1]) * i / n) for i in range(n + 1)]
    P = [pts[0]] + list(pts) + [pts[-1]]
    out, segs = [], len(pts) - 1
    for i in range(n + 1):
        u = i / n * segs; s = min(int(u), segs - 1); t = u - s
        p0, p1, p2, p3 = P[s], P[s + 1], P[s + 2], P[s + 3]
        out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                                + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in (0, 1)))
    return out


def stroke(img, pts, w, dens=JIAO, dry=0.35, press=(0.55, 1.0, 0.45), bleed=0.7):
    """Bristle brush: hairs side by side; each hair runs dry along the stroke -> fei bai streaks.
    press = (entry, body, exit) pressure; dry 0 = fully loaded, 1 = very dry."""
    L = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    path = smooth(pts, max(8, int(L / 1.5)))
    xs = [p[0] for p in path]; ys = [p[1] for p in path]
    pad = w + 6
    ox, oy = int(min(xs) - pad), int(min(ys) - pad)
    bw, bh = int(max(xs) + pad) - ox, int(max(ys) + pad) - oy
    m = Image.new("L", (bw * SS, bh * SS), 0); d = ImageDraw.Draw(m)
    hairs = max(6, int(w / 1.6))
    offs = sorted(R.uniform(-0.5, 0.5) for _ in range(hairs))
    load = [R.uniform(0.55, 1.0) for _ in range(hairs)]
    n = len(path)
    for h in range(hairs):
        gap_run = 0
        for i, (x, y) in enumerate(path):
            t = i / (n - 1)
            p = press[0] + (press[1] - press[0]) * min(1, t / 0.2) if t < 0.2 else \
                press[1] + (press[2] - press[1]) * max(0, (t - 0.6) / 0.4)
            j0, j1 = path[max(i - 1, 0)], path[min(i + 1, n - 1)]
            dx, dy = j1[0] - j0[0], j1[1] - j0[1]; ln = math.hypot(dx, dy) or 1
            o = offs[h] * w * p
            hx, hy = (x - ox - dy / ln * o) * SS, (y - oy + dx / ln * o) * SS
            left = load[h] - t * dry * 1.5
            if gap_run > 0:
                gap_run -= 1; continue
            if left < R.uniform(0, 0.55):
                gap_run = R.randint(8, 34); continue  # hair runs dry: long streak gaps = fei bai
            r = max(0.8, w * p / hairs * 1.25) * SS
            v = int(dens * max(0.45, min(1.0, left + 0.45)))
            d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=v)
    m = m.resize((bw, bh), Image.LANCZOS)
    if bleed:
        m = ImageChops.lighter(m, m.filter(ImageFilter.GaussianBlur(bleed * 2)).point(lambda v: int(v * 0.45)))
    full = Image.new("L", (W, H), 0); full.paste(m, (ox, oy))
    return ink(img, full)


def dot(img, x, y, r, dens=JIAO):
    """Dian: a pressed blob, slightly irregular, wet edge."""
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for _ in range(6):
        a, b = R.uniform(-r * .25, r * .25), R.uniform(-r * .25, r * .25)
        rr = r * R.uniform(0.7, 1.0)
        d.ellipse([x + a - rr, y + b - rr, x + a + rr, y + b + rr], fill=dens)
    return ink(img, m.filter(ImageFilter.GaussianBlur(1.2)))


def text_ink(img, xy, s, font, dens=JIAO, anchor="la", streak=0.18, angle=0):
    """Type set as ink: rough edges, slight bleed, sparse dry-brush streaks along the stroke direction."""
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text(xy, s, font=font, fill=255, anchor=anchor)
    bb = m.getbbox()
    rough = Image.effect_noise((W, H), 90).filter(ImageFilter.GaussianBlur(1))
    m = ImageChops.multiply(m.filter(ImageFilter.GaussianBlur(1.6)), rough.point(lambda v: 255 if v > 70 else 180))
    m = m.point(lambda v: 255 if v > 120 else int(v * 1.6))
    st = Image.new("L", (W, H), 255); d = ImageDraw.Draw(st)
    for _ in range(int((bb[2] - bb[0]) * streak)) if streak else []:
        x, y = R.uniform(bb[0], bb[2]), R.uniform(bb[1], bb[3])
        Lw = R.uniform(10, 40)
        dx, dy = math.cos(angle) * Lw, math.sin(angle) * Lw
        d.line([(x, y), (x + dx, y + dy)], fill=R.randint(0, 90), width=R.choice([1, 2]))
    m = ImageChops.multiply(m, st.filter(ImageFilter.GaussianBlur(0.5)))
    m = ImageChops.lighter(m.point(lambda v: v * dens // 255), m.filter(ImageFilter.GaussianBlur(2.5)).point(lambda v: v // 6))
    return ink(img, m)


def seal(img, x, y, size, ch):
    """Cinnabar seal, intaglio (white char on red), worn edges. One per picture."""
    s = Image.new("L", (size, size), 0); d = ImageDraw.Draw(s)
    d.rectangle([3, 3, size - 4, size - 4], fill=230)
    f = ImageFont.truetype(HEI, int(size * 0.7))
    d.text((size / 2, size / 2 + 1), ch, font=f, fill=0, anchor="mm")
    for _ in range(int(size * 0.7)):
        rx, ry = R.uniform(0, size), R.uniform(0, size)
        rr = R.uniform(0.5, 1.5)
        d.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], fill=R.choice([0, 120, 230]))
    m = Image.new("L", (W, H), 0)
    m.paste(s.rotate(R.uniform(-2.5, 2.5), resample=Image.BICUBIC), (x, y))
    return ink(img, m.filter(ImageFilter.GaussianBlur(0.5)), CINNABAR)


def box(img, x0, y0, x1, y1, w, dens=NONG, dry=0.4):
    """Hand-ruled box: four separate strokes with overshoot, never a closed vector rect."""
    j = lambda: R.uniform(-2.5, 2.5)
    img = stroke(img, [(x0 - 4, y0 + j()), (x1 + 5, y0 + j())], w, dens, dry)
    img = stroke(img, [(x1 + j(), y0 - 3), (x1 + j(), y1 + 4)], w, dens, dry)
    img = stroke(img, [(x0 - 3, y1 + j()), (x1 + 4, y1 + j())], w * 1.1, dens, dry)
    img = stroke(img, [(x0 + j(), y0 - 4), (x0 + j(), y1 + 3)], w, dens, dry)
    return img


check_glyphs(HEI, "知識庫")
img = rice_paper()

# ---- 1. far layer: pale ridges dissolving into mist (qing mo), drawn first ----
img = far_hills(img, 540, 60, QING + 6, 3, 420, W, fade=140)
img = far_hills(img, 600, 26, QING - 12, 8, 0, 520, fade=80)

# ---- 2. knowledge base: drawer cabinet (yao gui), 3 x 4 drawers; faces left as paper ----
cx0, cy0, cx1, cy1 = 650, 610, 960, 1010
cols, rows = 3, 4
dw, dh = (cx1 - cx0) / cols, (cy1 - cy0) / rows
depth = 46  # visible right side face
img = wash_poly(img, [(cx1, cy0), (cx1 + depth, cy0 - 24), (cx1 + depth, cy1 - 24), (cx1, cy1)], ZHONG, blur=4, rim=0.6, grad=(0, 1))
img = wash_poly(img, [(cx0, cy0 + dh * 2.4), (cx1, cy0 + dh * 2.4), (cx1, cy1), (cx0, cy1)], DAN - 40, blur=18, rim=0, grad=(0, 1))
open_cell = (0, 1)  # drawer receiving the card
for r_ in range(rows):
    for c_ in range(cols):
        x0, y0 = cx0 + c_ * dw, cy0 + r_ * dh
        if (c_, r_) == open_cell:
            continue
        img = stroke(img, [(x0 + dw / 2 - 16, y0 + dh * 0.42), (x0 + dw / 2 + 16, y0 + dh * 0.42)], 5, NONG, dry=0.2, press=(0.9, 1, 0.8))
        img = dot(img, x0 + dw / 2, y0 + dh * 0.42 + 8, 5, JIAO)
# frame: bone strokes, darkest ink, drawn after washes
img = stroke(img, [(cx0 - 3, cy0 - 26), (cx0 + 2, cy0 + 200), (cx0 - 3, cy1 + 8)], 18, JIAO, dry=0.45)
img = stroke(img, [(cx1, cy0 - 10), (cx1 + 3, cy0 + 220), (cx1, cy1 + 4)], 12, NONG, dry=0.5)
img = stroke(img, [(cx1 + depth, cy0 - 30), (cx1 + depth + 2, cy1 - 20)], 9, NONG, dry=0.75)
img = stroke(img, [(cx0 - 6, cy1 + 4), (cx1 + 4, cy1 + 2), (cx1 + depth, cy1 - 24)], 12, JIAO, dry=0.5)
for k in range(1, rows):
    yy = cy0 + k * dh
    img = stroke(img, [(cx0, yy + R.uniform(-2, 2)), (cx1, yy + R.uniform(-2, 2))], 6, NONG, dry=0.45)
for k in range(1, cols):
    xx = cx0 + k * dw
    img = stroke(img, [(xx, cy0), (xx + R.uniform(-3, 3), cy1)], 5, ZHONG + 30, dry=0.55)
# eave: one sweeping stroke, pressed at left, lifted at right (the boldest gesture in the picture)
img = stroke(img, [(606, cy0 - 14), (740, cy0 - 50), (880, cy0 - 58), (1040, cy0 - 40)], 36, JIAO, dry=0.4, press=(0.6, 1.0, 0.3))
img = stroke(img, [(cx0 - 10, cy0 - 4), (cx1 + depth, cy0 - 30)], 8, NONG, dry=0.4)
# the open drawer: cavity in the cell + drawer box pulled out to the lower-left
ox0, oy0 = cx0 + 6, cy0 + dh + 6
ox1, oy1 = cx0 + dw - 6, cy0 + 2 * dh - 6
img = wash_poly(img, [(ox0, oy0), (ox1, oy0), (ox1, oy1), (ox0, oy1)], JIAO - 30, blur=2, rim=0.3)
px, py = -62, 26  # pull-out offset
front = [(ox0 + px, oy0 + py + 20), (ox1 + px, oy0 + py + 20), (ox1 + px, oy1 + py), (ox0 + px, oy1 + py)]
img = wash_poly(img, [(ox0 + px, oy0 + py + 20), (ox0, oy0 + 20), (ox1, oy0 + 20), (ox1 + px, oy0 + py + 20)], ZHONG + 20, blur=2, rim=0.5)
img = Image.composite(Image.new("RGB", (W, H), PAPER), img, (lambda m: (ImageDraw.Draw(m).polygon(front, fill=255), m)[1])(Image.new("L", (W, H), 0)))
img = wash_poly(img, front, QING + 10, blur=3, rim=0.8, grad=(0, 1))
img = stroke(img, [front[0], front[1]], 7, JIAO, dry=0.3)
img = stroke(img, [front[3], front[2]], 10, JIAO, dry=0.35)
img = stroke(img, [front[0], front[3]], 7, NONG, dry=0.3)
img = stroke(img, [front[1], front[2]], 7, NONG, dry=0.4)
img = stroke(img, [front[1], (ox1, oy0 + 20)], 5, NONG, dry=0.4)
img = stroke(img, [((front[0][0] + front[1][0]) / 2 - 16, front[3][1] - 30), ((front[0][0] + front[1][0]) / 2 + 16, front[3][1] - 30)], 5, JIAO, dry=0.2)
img = dot(img, (front[0][0] + front[1][0]) / 2, front[3][1] - 22, 5, JIAO)
# ground: wash dissolves into blank paper (liu bai instead of a floor line)
img = wash(img, 790, 1024, 200, 20, DAN - 30, blobs=12, blur=18, rim=0.1)

# ---- 3. AI agent: boxy robot in gou le outline + graded washes, visor slit, no face ----
# light from upper-left: washes darken toward right/bottom, lit side stays paper
img = wash_poly(img, [(170, 600), (310, 596), (314, 690), (174, 694)], DAN, blur=4, grad=(1, 0))
img = box(img, 170, 598, 312, 692, 12, NONG, dry=0.4)
img = stroke(img, [(188, 640), (296, 636)], 18, JIAO, dry=0.1, press=(0.9, 1.0, 0.85))  # visor slit
img = stroke(img, [(242, 596), (240, 548)], 6, NONG, dry=0.3)                            # antenna
img = dot(img, 240, 538, 11, JIAO)
img = stroke(img, [(242, 694), (242, 716)], 16, NONG, dry=0.15)                          # neck
img = wash_poly(img, [(150, 716), (340, 712), (346, 912), (156, 916)], ZHONG, blur=6, grad=(1, 0))
img = box(img, 150, 714, 344, 914, 15, JIAO, dry=0.45)
th = [math.radians(a) for a in range(-50, 260, 20)]                                        # chest dial: open enso
img = stroke(img, [(226 + 30 * math.cos(a), 800 + 30 * math.sin(a)) for a in th], 7, NONG, dry=0.55)
img = dot(img, 226, 800, 6, JIAO)
for k in range(3):
    img = stroke(img, [(178, 860 + k * 15), (236, 860 + k * 15)], 4, NONG, dry=0.4)
img = stroke(img, [(130, 952), (170, 934), (322, 934), (364, 952), (322, 972), (170, 972), (130, 954)], 13, JIAO, dry=0.35)
for k in range(4):
    img = dot(img, 182 + k * 44, 953, 9, NONG)
img = stroke(img, [(206, 914), (204, 934)], 12, NONG, dry=0.15)
img = stroke(img, [(290, 914), (292, 934)], 12, NONG, dry=0.15)
img = wash(img, 250, 990, 170, 18, DAN - 20, blobs=10, blur=16, rim=0.1)
# arm: long two-segment reach, joints as heavy dots; card held right at the drawer mouth
sh, el, wr = (348, 744), (450, 690), (568, 662)
img = stroke(img, [sh, (400, 722), el], 15, JIAO, dry=0.3)
img = stroke(img, [el, (510, 664), wr], 13, JIAO, dry=0.45)
img = dot(img, *sh, 14); img = dot(img, *el, 12); img = dot(img, *wr, 9)

# ---- 4. note card: the brightest paper in the picture, lowered INTO the pulled-out drawer ----
# occlusion: the drawer front is drawn over the card, so the lower part is hidden inside the drawer
prev = img.copy()
card = [(601, 636), (681, 628), (683, 800), (603, 808)]
cm = Image.new("L", (W, H), 0); ImageDraw.Draw(cm).polygon(card, fill=255)
img = Image.composite(Image.new("RGB", (W, H), CARD), img, cm.filter(ImageFilter.GaussianBlur(0.7)))
img = stroke(img, [card[0], card[1]], 4, NONG, dry=0.25)
img = stroke(img, [card[1], card[2]], 4, NONG, dry=0.3)
img = stroke(img, [card[0], card[3]], 4, NONG, dry=0.25)
for k in range(3):
    y = 664 + k * 22
    img = stroke(img, [(616, y), (668 - k * 14, y - 3)], 3, ZHONG, dry=0.4)
fm = Image.new("L", (W, H), 0); ImageDraw.Draw(fm).polygon(front, fill=255)
img = Image.composite(prev, img, fm)                       # front of the drawer covers the card
img = stroke(img, [front[0], front[1]], 7, JIAO, dry=0.3)  # re-ink the front's top lip over the card edges
# gripper: two claw strokes pinching the card's left edge
img = stroke(img, [wr, (588, 640), (604, 646)], 8, JIAO, dry=0.15)
img = stroke(img, [wr, (590, 684), (604, 680)], 8, JIAO, dry=0.15)
# placement cue: one dry downward stroke with a small arrowhead above the card
img = stroke(img, [(644, 566), (644, 604)], 5, ZHONG, dry=0.85, press=(0.4, 1.0, 0.2))
img = stroke(img, [(632, 594), (644, 610), (656, 594)], 4, NONG, dry=0.3)

# ---- 5. heading: vertical, top-right, read top-down; seal below it ----
fh = ImageFont.truetype(HEI, 128)
for i, ch in enumerate("知識庫"):
    img = text_ink(img, (964, 60 + i * 140), ch, fh, dens=JIAO, anchor="mt", streak=0.1, angle=math.pi / 2)
img = seal(img, 930, 476, 76, "知")

# ---- 6. big 61%: heavy ink, wet bleed, flying-white streaks running horizontally ----
fn = ImageFont.truetype(NUM, 300, index=0)
img = text_ink(img, (70, 70), "61", fn, dens=JIAO, streak=0.0)
fp = ImageFont.truetype(NUM, 140, index=0)
img = text_ink(img, (344, 222), "%", fp, dens=NONG, streak=0.0)
img = stroke(img, [(78, 412), (300, 404), (520, 410)], 10, ZHONG, dry=0.85, press=(0.5, 1.0, 0.1))

# ---- 7. calm bottom ~22%: blank paper, nothing drawn below y=1050 ----

img.save(os.path.join(HERE, "sample.png"))
print("ok")
