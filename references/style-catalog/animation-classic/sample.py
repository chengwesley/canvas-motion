#!/usr/bin/env python3
"""animation-classic sample (original artwork): ONE key frame. A robot lunges toward the
knowledge base, stretched along its arc, after dropping a note card into the drawer
(card half hidden by the drawer front). Painted, luminous, layered background.
Python 3 + PIL only. Deterministic. Writes sample.png (1080x1350)."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

W, H, S = 1080, 1350, 2
GROUND = 1052
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = '/System/Library/Fonts/STHeiti Medium.ttc'
AVN = '/System/Library/Fonts/Avenir Next.ttc'

def hx(s): return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
def lerp(a, b, t): return a + (b - a) * t
def lerpc(a, b, t): return tuple(int(lerp(a[i], b[i], t)) for i in range(3))

SKY_T, SKY_B = hx('78B6DA'), hx('F8E7BC')
CLOUD, CLOUD_S = hx('FFF9EA'), hx('E9D9C4')
HILL_FAR, HILL_MID = hx('A7C9CC'), hx('7FB09A')
LEAF_D, LEAF_M, LEAF_L, LEAF_H = hx('2F6B4D'), hx('4A8A53'), hx('7FB04F'), hx('C9DE7A')
GRASS_T, GRASS_B = hx('8DB853'), hx('5F9440')
PATH = hx('E2CC93')
TEAL, TEAL_D, TEAL_L = hx('2A9D8F'), hx('1B6E69'), hx('7FD6C6')
CORAL, CORAL_D = hx('E4573D'), hx('B33A27')
SUN, SUN_L = hx('F5B83D'), hx('FFE49A')
PLUM, PLUM_D, PLUM_L = hx('6B3E52'), hx('45263A'), hx('9A5C74')
HOLE = hx('2A1722')
CARD, CARD_S, CARD_L = hx('FFF6E2'), hx('E6D3B3'), hx('D6C5A6')
INDIGO = hx('2B2D5B')
SLATE = hx('1F3B4D')

def font(p, sz, idx=0): return ImageFont.truetype(p, int(sz * S), index=idx)
def _glyph(f, ch):
    im = Image.new('L', (int(f.size * 2), int(f.size * 2)), 0)
    ImageDraw.Draw(im).text((4, 4), ch, font=f, fill=255)
    return im.tobytes()
def check_glyphs(text, f):
    bad = _glyph(f, '\U0010ffff')
    for ch in text:
        if ch.isspace(): continue
        g = _glyph(f, ch)
        if g == bad or not any(g): raise SystemExit('missing glyph: %r' % ch)

# ------------------------------------------------------------ painted background (1x, soft)
def blob(img, cx, cy, rx, ry, col, a=255, blur=0, rot=0):
    pad = int(blur * 3) + 4
    x0, y0 = int(cx - rx - pad), int(cy - ry - pad)
    w, h = int(2 * rx + 2 * pad), int(2 * ry + 2 * pad)
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).ellipse([pad, pad, pad + 2 * rx, pad + 2 * ry], fill=a)
    if rot: m = m.rotate(rot, resample=Image.BICUBIC)
    if blur: m = m.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.new('RGB', (w, h), col), (x0, y0), m)

def vgrad(img, y0, y1, c0, c1):
    d = ImageDraw.Draw(img)
    for y in range(y0, y1):
        d.line([(0, y), (W, y)], fill=lerpc(c0, c1, (y - y0) / max(1, y1 - y0 - 1)))

def ridge(img, base, amp, seed, col, step=6, blur=0):
    r = random.Random(seed)
    ph = [r.uniform(0, 6.28) for _ in range(3)]
    pts = [(0, H)]
    for x in range(0, W + step, step):
        y = base + amp * (math.sin(x / 150 + ph[0]) * .5 + math.sin(x / 61 + ph[1]) * .3 + math.sin(x / 270 + ph[2]) * .6)
        pts.append((x, y))
    pts.append((W, H))
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    if blur: m = m.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.new('RGB', (W, H), col), (0, 0), m)

def tree_clump(img, cx, cy, rad, seed, n=70):
    r = random.Random(seed)
    for _ in range(n):                                   # dark body of leaves
        a, d = r.uniform(0, 6.28), rad * math.sqrt(r.random())
        blob(img, cx + math.cos(a) * d, cy + math.sin(a) * d * .8, r.randint(14, 26), r.randint(10, 20), r.choice([LEAF_D, LEAF_M]), 255, 1.0)
    for _ in range(int(n * .9)):                         # light from the upper left: mid and high leaves
        a, d = r.uniform(3.1, 5.0), rad * r.uniform(.25, 1.0)
        blob(img, cx + math.cos(a) * d * .9, cy + math.sin(a) * d * .75, r.randint(8, 16), r.randint(6, 11), r.choice([LEAF_L, LEAF_M, LEAF_H]), 235, .8)
    for _ in range(14):                                  # sky holes
        a, d = r.uniform(0, 6.28), rad * r.uniform(.2, .85)
        blob(img, cx + math.cos(a) * d, cy + math.sin(a) * d * .8, 4, 3, SKY_B, 200, .6)

def background():
    bg = Image.new('RGB', (W, H), SKY_T)
    vgrad(bg, 0, 820, SKY_T, SKY_B)
    blob(bg, 120, 170, 260, 170, SUN_L, 120, 90)                       # sun glow upper left
    for cx, cy, rx, ry in ((300, 240, 230, 62), (470, 285, 150, 42), (840, 190, 190, 52), (940, 250, 110, 34), (110, 330, 160, 44)):
        blob(bg, cx + 8, cy + 14, rx, ry, CLOUD_S, 150, 8)               # cloud shadow underside
        blob(bg, cx, cy, rx, ry, CLOUD, 235, 6)
        blob(bg, cx - rx * .3, cy - ry * .55, rx * .55, ry * .7, CLOUD, 255, 5)
    ridge(bg, 700, 34, 3, HILL_FAR, blur=3)                              # far haze hills
    ridge(bg, 775, 28, 8, lerpc(HILL_MID, HILL_FAR, .45), blur=2)
    tree_clump(bg, 95, 790, 120, 11, 55)                                # mid-ground tree clumps frame the left
    tree_clump(bg, 980, 700, 100, 13, 40)
    ridge(bg, 905, 20, 21, GRASS_T, blur=1.5)                            # meadow bands, nearer = darker and stronger
    vgrad(bg.crop((0, 930, W, H)), 0, 1, GRASS_T, GRASS_B)
    d = ImageDraw.Draw(bg)
    for y in range(930, H):
        d.line([(0, y), (W, y)], fill=lerpc(lerpc(GRASS_T, HILL_MID, .2), GRASS_B, (y - 930) / (H - 930)))
    r = random.Random(5)
    for _ in range(260):                                                 # grass strokes, left-leaning
        x, y = r.randint(0, W), r.randint(940, 1040)
        c = r.choice([GRASS_T, LEAF_L, LEAF_H, GRASS_B])
        d.line([(x, y), (x - 3, y - r.randint(6, 13))], fill=c, width=2)
    blob(bg, 540, 1210, 700, 120, lerpc(GRASS_B, GRASS_T, .25), 120, 40)  # calm meadow in the bottom 22%
    for _ in range(14):                                                  # a few flowers, kept clear of the action
        x, y = r.randint(40, 1040), r.randint(1130, 1290)
        blob(bg, x, y, 4, 3, r.choice([CARD, SUN, CORAL]), 255, .5)
    # light shafts from the upper left, converging on the action
    sh = Image.new('L', (W, H), 0); sd = ImageDraw.Draw(sh)
    for k in range(4):
        x0 = -100 + k * 150
        sd.polygon([(x0, 0), (x0 + 90, 0), (x0 + 700 + k * 40, 1000), (x0 + 520 + k * 40, 1000)], fill=60)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    bg.paste(Image.new('RGB', (W, H), SUN_L), (0, 0), sh)
    # dappled light on the path / grass near the ground line
    for _ in range(20):
        blob(bg, r.randint(40, 1040), r.randint(1060, 1100), r.randint(22, 50), r.randint(5, 9), PATH, 150, 4)
    return bg

# ------------------------------------------------------------ hard layer (2x)
def P(pts): return [(x * S, y * S) for x, y in pts]
class Layer:
    def __init__(self):
        self.im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def poly(self, pts, col, a=255): self.d.polygon(P(pts), fill=col + (a,))
    def rr(self, box, r, col, a=255): self.d.rounded_rectangle([v * S for v in box], r * S, fill=col + (a,))
    def el(self, cx, cy, rx, ry, col, a=255): self.d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=col + (a,))
    def line(self, pts, w, col, a=255):
        self.d.line(P(pts), fill=col + (a,), width=int(w * S), joint='curve')
        for x, y in (pts[0], pts[-1]): self.el(x, y, w / 2, w / 2, col, a)
    def text(self, s, x, y, size, col, path=CJK, idx=0):
        f = font(path, size, idx)
        if path == CJK: check_glyphs(s, f)
        self.d.text((x * S, y * S), s, font=f, fill=col + (255,))

def ell_pts(cx, cy, a, b, ang, n=60):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + a * math.cos(t) * c - b * math.sin(t) * s, cy + a * math.cos(t) * s + b * math.sin(t) * c) for t in [i * 2 * math.pi / n for i in range(n)]]

def shade(base, mask_layer_fn, dark, light, off=(-9, -7)):
    """cel shading from a silhouette: crescent on the lower right, thin rim light upper left"""
    m = Image.new('L', (W * S, H * S), 0); mask_layer_fn(ImageDraw.Draw(m))
    sh = ImageChops.offset(m, int(off[0] * S), int(off[1] * S))
    dark_m = ImageChops.subtract(m, sh)
    rim_m = ImageChops.subtract(m, ImageChops.offset(m, int(-5 * S), int(-4 * S)))
    base.paste(Image.new('RGB', base.size, dark), (0, 0), dark_m)
    base.paste(Image.new('RGB', base.size, light), (0, 0), rim_m)

def build():
    bg = background().resize((W * S, H * S), Image.BICUBIC)
    # painted grain
    r = random.Random(1)
    tile = Image.new('L', (W // 2, H // 2)); tile.putdata([r.randint(110, 146) for _ in range((W // 2) * (H // 2))])
    grain = tile.resize((W * S, H * S), Image.BICUBIC)
    bg = Image.composite(Image.new('RGB', bg.size, (255, 244, 220)), bg, grain.point(lambda v: max(0, v - 126) * 1))
    cv = bg

    # soft painted contact shadows (light from the upper left, so they fall right)
    shd = Image.new('L', (W * S, H * S), 0); sd = ImageDraw.Draw(shd)
    for (cx, cy, rx, ry) in ((430, GROUND + 6, 150, 16), (835, GROUND + 6, 250, 20), (260, GROUND + 4, 70, 9)):
        sd.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=150)
    shd = shd.filter(ImageFilter.GaussianBlur(10 * S))
    cv.paste(Image.new('RGB', cv.size, hx('2C4A2A')), (0, 0), shd)

    # knowledge base
    X0, X1, T, B = 630, 1030, 400, 1030
    rows = [T, T + 183, T + 366, B]
    k = Layer()
    k.rr((X0, T, X1, B), 14, PLUM)
    k.rr((X0 - 6, T - 14, X1 + 6, T + 8), 8, PLUM_L)
    rnd = random.Random(4)
    cols = [SUN, TEAL, CORAL, CARD, hx('E98BA5')]
    for rr in range(2):
        y0, y1 = rows[rr] + 14, rows[rr + 1] - 6
        k.rr((X0 + 12, y0, X1 - 12, y1), 6, HOLE)
        x = X0 + 22
        while x < X1 - 56:
            w = rnd.choice([26, 32, 38, 30]); hgt = min(rnd.choice([112, 126, 136, 104]), y1 - y0 - 14)
            c = cols[rnd.randrange(len(cols))]
            lean = rnd.random() < .08
            if lean: k.poly([(x, y1), (x + w, y1), (x + w + 24, y1 - hgt + 6), (x + 24, y1 - hgt)], c)
            else:
                k.rr((x, y1 - hgt, x + w, y1), 4, c)
                k.rr((x + w * .66, y1 - hgt, x + w, y1), 4, lerpc(c, PLUM_D, .3))
                k.rr((x + 4, y1 - hgt + 14, x + w - 4, y1 - hgt + 20), 2, lerpc(c, CARD, .5))
            x += w + (24 if lean else 4)
    k.rr((X0 + 12, rows[2] + 14, X1 - 12, B - 12), 6, HOLE)
    k.rr((X0 + 12, rows[2] + 14, X1 - 12, rows[2] + 28), 4, hx('150A10'))
    k.rr((700, rows[2] + 40, 780, 905), 4, SUN_L, 90)                   # warm lit slot behind the card
    cv.paste(k.im.resize(cv.size), (0, 0), k.im)
    # the card: pushed in, upper half visible, drawn before the drawer front so the front occludes it
    c = Layer(); ccx, ccy, cw, ch = 742, 892, 118, 150
    ang = math.radians(3)
    def tf(x, y): return (ccx + x * math.cos(ang) - y * math.sin(ang), ccy + x * math.sin(ang) + y * math.cos(ang))
    body = [tf(-cw / 2, -ch / 2), tf(cw / 2, -ch / 2), tf(cw / 2, ch / 2), tf(-cw / 2, ch / 2)]
    c.poly(body, CARD)
    c.poly([tf(cw / 2 - 26, -ch / 2), tf(cw / 2, -ch / 2), tf(cw / 2, -ch / 2 + 26)], CARD_S)      # curled corner (follow-through)
    c.poly([tf(-cw / 2, -ch / 2), tf(cw / 2 - 26, -ch / 2), tf(cw / 2, -ch / 2 + 26), tf(cw / 2, -ch / 2 + 32), tf(-cw / 2, -ch / 2 + 34)], CORAL)
    c.poly([tf(cw / 2 - 22, -ch / 2), tf(cw / 2, -ch / 2), tf(cw / 2, -ch / 2 + 22)], CORAL_D)
    for j in range(3): c.line([tf(-cw / 2 + 16, -ch / 2 + 54 + j * 20), tf(cw / 2 - 18 - (20 if j == 2 else 0), -ch / 2 + 54 + j * 20)], 5, CARD_L)
    cv.paste(c.im.resize(cv.size), (0, 0), c.im)
    f = Layer()                                                          # drawer front (occluder)
    f.rr((X0 - 10, 905, X1 + 10, B - 4), 12, PLUM_L)
    f.rr((X0 - 10, 905, X1 + 10, 918), 8, lerpc(PLUM_L, CARD, .3))
    f.rr((X0 - 4, 990, X1 + 4, B - 4), 8, PLUM)
    f.rr((790, 950, 880, 972), 11, PLUM_D)
    cv.paste(f.im.resize(cv.size), (0, 0), f.im)

    # ANTICIPATION ghost: the crouch (squashed) a moment earlier, plus dust and an arc of the leap
    g = Layer()
    g.d.polygon(P(ell_pts(210, 985, 100, 56, 0)), fill=TEAL + (150,))
    g.d.polygon(P(ell_pts(210, 960, 60, 36, 0)), fill=TEAL_L + (110,))
    g.d.line(P(ell_pts(210, 985, 100, 56, 0) + [ell_pts(210, 985, 100, 56, 0)[0]]), fill=TEAL_D + (220,), width=4 * S)
    for (dx, dy, rr) in ((120, 1030, 22), (92, 1018, 15), (150, 1042, 12), (300, 1036, 16)):
        g.el(dx, dy, rr, rr * .75, CARD, 215)
    pts = [(210 + t * 260, 985 - 190 * math.sin(math.pi * t * .85) + 60 * t * t) for t in [i / 40 for i in range(41)]]
    for i in range(0, 40, 3): g.line(pts[i:i + 2], 5, SUN, 230)
    cv.paste(g.im.resize(cv.size), (0, 0), g.im)

    # ROBOT: stretched along its direction of travel (axis from pelvis to head)
    r = Layer()
    P0, P1 = (372, 948), (484, 738)
    axis = math.atan2(P1[1] - P0[1], P1[0] - P0[0])
    mid = ((P0[0] + P1[0]) / 2, (P0[1] + P1[1]) / 2)
    L = math.hypot(P1[0] - P0[0], P1[1] - P0[1])
    a, b = L / 2 + 6, 62                                                 # long and thin = stretch (volume kept)
    # legs first: planted front leg, trailing back leg with follow-through bend
    r.line([(402, 930), (414, 1034)], 30, TEAL_D); r.el(428, 1042, 36, 13, SLATE)
    r.line([(358, 925), (318, 990), (232, 972)], 28, TEAL_D); r.el(214, 968, 30, 12, SLATE)
    # trailing back arm (flung back)
    sh2 = (452, 790)
    r.line([sh2, (388, 748), (332, 770)], 24, TEAL_D); r.el(322, 774, 17, 17, SLATE)
    ux0, uy0 = math.cos(axis), math.sin(axis)
    hc = (P1[0] + ux0 * 30, P1[1] + uy0 * 30)
    ab = (hc[0] + ux0 * 52, hc[1] + uy0 * 52)
    ant = [ab, (ab[0] - 4, ab[1] - 30), (ab[0] - 32, ab[1] - 52), (ab[0] - 72, ab[1] - 54)]
    r.line(ant, 7, SLATE); r.el(ant[-1][0] - 8, ant[-1][1] + 2, 14, 14, CORAL); r.el(ant[-1][0] - 12, ant[-1][1] - 3, 5, 5, hx('FFC7B5'))
    base = cv.copy()
    cv.paste(r.im.resize(cv.size), (0, 0), r.im)
    # body bean
    body_fn = lambda d: d.polygon(P(ell_pts(mid[0], mid[1], a, b, axis)), fill=255)
    bl = Layer(); bl.poly(ell_pts(mid[0], mid[1], a, b, axis), TEAL)
    bod = cv.copy(); bod.paste(bl.im.resize(cv.size), (0, 0), bl.im)
    cv = bod
    shade(cv, body_fn, TEAL_D, TEAL_L, off=(-14, -10))
    ux, uy = math.cos(axis), math.sin(axis); vx, vy = -uy, ux
    def at(u, v): return (mid[0] + ux * (u * a) + vx * v, mid[1] + uy * (u * a) + vy * v)
    hl = Layer(); hl.poly(ell_pts(hc[0], hc[1], 64, 56, axis), hx('F6EBD3'))
    hd = cv.copy(); hd.paste(hl.im.resize(cv.size), (0, 0), hl.im); cv = hd
    shade(cv, lambda d: d.polygon(P(ell_pts(hc[0], hc[1], 64, 56, axis)), fill=255), hx('D9C7A4'), CARD, off=(-9, -7))
    def ha(u, v): return (hc[0] + ux * u + vx * v, hc[1] + uy * u + vy * v)
    vis = Layer()
    vis.poly([ha(-4, -50), ha(34, -44), ha(34, 44), ha(-4, 50)], SLATE)             # visor band, no face
    vis.poly([ha(8, -34), ha(14, -34), ha(14, 34), ha(8, 34)], SUN)
    vis.poly([ha(-4, -50), ha(10, -48), ha(10, -26), ha(-4, -28)], hx('3C6178'), 150)
    vis.poly([at(-.58, -b * .5), at(-.2, -b * .5), at(-.2, b * .5), at(-.58, b * .5)], hx('D8F2EA'))
    vis.line([at(-.50, -b * .22), at(-.28, -b * .22)], 5, TEAL_D); vis.line([at(-.50, b * .18), at(-.28, b * .18)], 5, TEAL_D)
    vis.el(*at(-.42, b * .44), 5, 5, CORAL)
    cv.paste(vis.im.resize(cv.size), (0, 0), vis.im)
    # front arm: extended toward the drawer, the hand has just let go of the card (follow-through)
    ar = Layer()
    shd_ = (468, 800); elb = (572, 826); hand = (672, 858)
    ar.line([shd_, elb, hand], 26, TEAL)
    ar.line([(shd_[0] + 4, shd_[1] + 9), (elb[0], elb[1] + 9), (hand[0] - 20, hand[1] + 9)], 6, TEAL_D, 255)
    ar.el(shd_[0], shd_[1], 20, 20, SLATE); ar.el(elb[0], elb[1], 14, 14, TEAL_L); ar.el(hand[0], hand[1], 19, 19, SLATE)
    ar.el(hand[0] - 5, hand[1] - 6, 6, 6, hx('4B7A93'))
    cv.paste(ar.im.resize(cv.size), (0, 0), ar.im)
    # staging: three speed streaks behind the body, ending where the stretch begins
    st = Layer()
    for (x0, y0, x1, y1, w) in ((250, 850, 340, 836, 6), (232, 890, 336, 880, 5), (270, 810, 346, 800, 4)):
        st.line([(x0, y0), (x1, y1)], w, CARD, 190)
    cv.paste(st.im.resize(cv.size), (0, 0), st.im)

    # type
    tx = Layer()
    tx.rr((78, 70, 150, 82), 6, CORAL)
    tx.text('知識庫', 74, 100, 66, INDIGO)
    tx.text('61%', 68, 176, 184, CORAL, AVN, 8)
    tx.rr((80, 412, 470, 436), 12, CARD); tx.rr((80, 412, 80 + 390 * .61, 436), 12, TEAL)
    tx.text('筆記已歸檔', 80, 456, 32, INDIGO)
    cv.paste(tx.im.resize(cv.size), (0, 0), tx.im)
    return cv

if __name__ == '__main__':
    build().resize((W, H), Image.LANCZOS).save(os.path.join(HERE, 'sample.png'))
