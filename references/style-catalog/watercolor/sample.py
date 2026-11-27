# Watercolor style sample (transparent glazing on cold-press paper).
# Technique encoded: pale-to-dark glazing with multiply blending, reserved paper whites,
# wet edges (pigment pooling at the rim), gravity bead (lighter top / denser bottom),
# granulation in paper tooth, backrun blooms, wet-in-wet soft edges vs wet-on-dry hard edges,
# light pencil underdrawing, darkest accents last. Light from top-left, shadows fall bottom-right.
import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

W, H = 1080, 1350
CALM_Y = int(H * 0.78)
R = random.Random(20261128)
HERE = os.path.dirname(os.path.abspath(__file__))
HEI = "/System/Library/Fonts/STHeiti Medium.ttc"
BASK = "/System/Library/Fonts/Supplemental/Baskerville.ttc"   # index 1 = bold, lining figures

def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
# Limited palette: 4 pigments + neutral mix. Ramps = shadow, main, light, glaze
ULTRA = [rgb('2E3F6E'), rgb('4A64A6'), rgb('8FA6D1'), rgb('C9D5EA')]   # ultramarine
SIENNA = [rgb('6E3B22'), rgb('A65A32'), rgb('CF8A5C'), rgb('EBC3A0')]  # burnt sienna
OCHRE = [rgb('9A6A22'), rgb('C9963E'), rgb('E3C07A'), rgb('F3E1B5')]   # yellow ochre
ROSE = [rgb('8E2A2E'), rgb('C8463F'), rgb('E27E6E'), rgb('F4C2B6')]    # accent (61% only + 1 tiny dot)
NEUTRAL = rgb('3A3640')   # ultramarine + burnt sienna dark
PAPER = rgb('F6F0E2')
PENCIL = rgb('7A7068')

# Deterministic paper/noise textures (no Image.effect_noise: it is not seeded)
def rnd_tex(w, h, scale=1, blur=0.0):
    t = Image.frombytes('L', (w // scale, h // scale), R.randbytes((w // scale) * (h // scale)))
    if scale > 1: t = t.resize((w, h), Image.BICUBIC)
    return t.filter(ImageFilter.GaussianBlur(blur)) if blur else t
FINE = rnd_tex(W, H, 1, 0.7)
COARSE = rnd_tex(W, H, 4, 1.5)
TOOTH = ImageChops.blend(FINE, COARSE, 0.4)   # paper valleys = low values
FLOW = rnd_tex(W, H, 48, 18).point(lambda v: max(0, min(255, (v - 128) * 6 + 128)))  # low-frequency pigment unevenness

def jitter(pts, amt, sub=3):
    out = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        for k in range(sub):
            t = k / sub
            out.append((a[0] + (b[0] - a[0]) * t + R.uniform(-amt, amt), a[1] + (b[1] - a[1]) * t + R.uniform(-amt, amt)))
    return out

def wash(img, pts, color, a=0.6, jit=3.0, layers=4, wet=1.6, edge=0.55, gran=0.3, grav=0.35,
         bloom=0, holes=(), dry=0.0, vary=0.35, reserve=True):
    """One transparent glaze. wet = softness (wet-in-wet large, wet-on-dry small).
    edge = pigment pooled at the rim. grav = top lighter than bottom (bead settles low).
    holes = reserved paper (highlights are never painted white). dry = dry-brush breakup."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    pad = int(jit * 2 + wet * 3 + 12)
    x0, y0 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad)
    x1, y1 = min(W, int(max(xs)) + pad), min(H, int(max(ys)) + pad)
    if x1 <= x0 or y1 <= y0: return
    bw, bh = x1 - x0, y1 - y0
    loc = lambda P: [(x - x0, y - y0) for x, y in P]
    m = Image.new('L', (bw, bh), 0)
    for _ in range(layers):
        lay = Image.new('L', (bw, bh), 0)
        ImageDraw.Draw(lay).polygon(loc(jitter(pts, jit)), fill=int(min(255, 255 / layers * 1.35)))
        m = ImageChops.add(m, lay)
    for hp in list(holes) + (RESERVE if reserve else []):
        hm = Image.new('L', (bw, bh), 0)
        ImageDraw.Draw(hm).polygon(loc(jitter(hp, jit * 0.6)), fill=255)
        m = ImageChops.subtract(m, hm.filter(ImageFilter.GaussianBlur(wet * 0.8)))
    m = m.filter(ImageFilter.GaussianBlur(wet))
    if edge:
        inner = m.filter(ImageFilter.MinFilter(7)).filter(ImageFilter.GaussianBlur(2.5))
        rim = ImageChops.subtract(m, inner).point(lambda v: min(255, v * 2))
        m = ImageChops.add(m.point(lambda v: v * (1 - edge * 0.45)), rim.point(lambda v: v * edge))
    if grav:
        top, bot = min(ys) - y0, max(ys) - y0
        g = Image.new('L', (1, bh))
        gp = g.load()
        for yy in range(bh):
            t = max(0.0, min(1.0, (yy - top) / max(1, bot - top)))
            gp[0, yy] = int(255 * (1 - grav + grav * t ** 1.4))
        m = ImageChops.multiply(m, g.resize((bw, bh)))
    if vary:  # pigment never lies flat: low-frequency density variation inside the wash
        m = ImageChops.multiply(m, FLOW.crop((x0, y0, x1, y1)).point(lambda v: int(255 * (1 - vary + vary * v / 255))))
    if gran:
        tooth = TOOTH.crop((x0, y0, x1, y1)).point(lambda v: int(255 - gran * max(0, 150 - v) * 1.7))
        m = ImageChops.multiply(m, tooth)
    if dry:
        brk = TOOTH.crop((x0, y0, x1, y1)).point(lambda v: 255 if v > 128 - dry * 60 else int(255 * (1 - dry)))
        m = ImageChops.multiply(m, brk)
    for _ in range(bloom):  # backrun: water pushes pigment out, pale centre with a dark frilly rim
        bx, by = R.uniform(min(xs), max(xs)) - x0, R.uniform(min(ys), max(ys)) - y0
        rr = R.uniform(14, 30)
        poly = [(bx + rr * (0.65 + 0.5 * R.random()) * math.cos(t), by + rr * (0.65 + 0.5 * R.random()) * math.sin(t))
                for t in [i * math.tau / 22 for i in range(22)]]
        bl = Image.new('L', (bw, bh), 0); ImageDraw.Draw(bl).polygon(poly, fill=255)
        rim = ImageChops.subtract(bl, bl.filter(ImageFilter.MinFilter(5))).filter(ImageFilter.GaussianBlur(1))
        m = ImageChops.subtract(m, bl.filter(ImageFilter.GaussianBlur(2)).point(lambda v: v * 0.55))
        m = ImageChops.add(m, ImageChops.multiply(rim, m.point(lambda v: min(255, v * 2))).point(lambda v: v * 0.5))
    m = m.point(lambda v: int(v * a))
    crop = img.crop((x0, y0, x1, y1))
    layer = Image.composite(Image.new('RGB', (bw, bh), color), Image.new('RGB', (bw, bh), (255, 255, 255)), m)
    img.paste(ImageChops.multiply(crop, layer), (x0, y0))   # glaze: overlaps darken, never lighten

RESERVE = []   # paper kept white for later passes (like masking fluid)

def rect(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
def rrect(x0, y0, x1, y1, r, n=5):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        pts += [(cx + r * math.cos(math.radians(a0 + 90 * k / n)), cy + r * math.sin(math.radians(a0 + 90 * k / n))) for k in range(n + 1)]
    return pts
def ell(cx, cy, rx, ry, n=28): return [(cx + rx * math.cos(math.tau * i / n), cy + ry * math.sin(math.tau * i / n)) for i in range(n)]
def rot(pts, cx, cy, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]
def limb(a, b, w):
    nx, ny = -(b[1] - a[1]), b[0] - a[0]; L = math.hypot(nx, ny); nx, ny = nx / L * w, ny / L * w
    return [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]

def pencil(d, pts, closed=True, over=10, alpha=80):
    # construction lines overshoot corners slightly, drawn twice, light hand
    seq = pts + ([pts[0]] if closed else [])
    for a, b in zip(seq, seq[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
        ex, ey = dx / L * over * R.uniform(0.2, 1), dy / L * over * R.uniform(0.2, 1)
        for _ in range(2):
            d.line([(a[0] - ex + R.uniform(-1, 1), a[1] - ey + R.uniform(-1, 1)),
                    (b[0] + ex + R.uniform(-1, 1), b[1] + ey + R.uniform(-1, 1))], fill=PENCIL + (alpha,), width=1)

def splatter(img, cx, cy, rad, color, n):
    lay = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(lay)
    for _ in range(n):
        t = R.uniform(0, math.tau); r = rad * R.random() ** 0.6; s = R.uniform(1.2, 4.5) * (1 - r / rad * 0.6)
        x, y = cx + r * math.cos(t), cy + r * math.sin(t)
        dd.ellipse([x - s, y - s, x + s, y + s], fill=R.randint(90, 170))
    layer = Image.composite(Image.new('RGB', (W, H), color), Image.new('RGB', (W, H), (255, 255, 255)), lay.filter(ImageFilter.GaussianBlur(0.6)))
    img.paste(ImageChops.multiply(img, layer))

def ink_text(img, xy, text, font, color, a=0.9, anchor='la'):
    """Lettering painted as a wash: soft bleed, pooled rim, granulation, lighter top."""
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).text(xy, text, font=font, fill=255, anchor=anchor)
    bb = m.getbbox(); x0, y0, x1, y1 = bb[0] - 12, bb[1] - 12, bb[2] + 12, bb[3] + 12
    c = m.crop((x0, y0, x1, y1))
    soft = c.filter(ImageFilter.GaussianBlur(2.5))
    inner = c.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(2))
    rim = ImageChops.subtract(c, inner)
    body = ImageChops.add(ImageChops.add(soft.point(lambda v: v * 0.3), c.point(lambda v: v * 0.55)), rim.point(lambda v: v * 0.5))
    g = Image.new('L', (1, y1 - y0)); gp = g.load()
    for yy in range(y1 - y0): gp[0, yy] = int(255 * (0.72 + 0.28 * yy / (y1 - y0)))
    body = ImageChops.multiply(body, g.resize((x1 - x0, y1 - y0)))
    body = ImageChops.multiply(body, TOOTH.crop((x0, y0, x1, y1)).point(lambda v: int(255 - 0.35 * max(0, 150 - v) * 1.7)))
    body = body.point(lambda v: int(v * a))
    crop = img.crop((x0, y0, x1, y1))
    layer = Image.composite(Image.new('RGB', c.size, color), Image.new('RGB', c.size, (255, 255, 255)), body)
    img.paste(ImageChops.multiply(crop, layer), (x0, y0))

# ---------------- paper ----------------
img = Image.new('RGB', (W, H), PAPER)
img = ImageChops.multiply(img, Image.merge('RGB', [FINE.point(lambda v: 255 - max(0, 135 - v) // 7)] * 3))

CARD = rot(rect(604, 600, 724, 700), 610, 602, 5)
RESERVE.append(CARD)

# ---------------- 1. first wash: wet-in-wet sky, pale top, deeper toward the horizon ----------------
wash(img, rect(-40, -40, W + 40, 760), ULTRA[3], a=0.6, jit=12, wet=16, edge=0.12, gran=0.45, grav=0.85, bloom=1, vary=0.5)
wash(img, rect(-40, 380, W + 40, 975), ULTRA[2], a=0.45, jit=16, wet=22, edge=0.15, gran=0.5, grav=0.9, bloom=2, vary=0.55,
     holes=[rect(620, 560, 1030, 990)])
wash(img, rect(600, 470, W + 40, 975), OCHRE[3], a=0.45, jit=18, wet=26, edge=0.0, gran=0.3, grav=0.4, vary=0.5)   # warm bleed behind the cabinet
# ground: ochre + sienna, wet-on-dry, bead settling at the bottom edge
wash(img, [(-30, 965), (W + 30, 955), (W + 30, 1050), (-30, 1058)], OCHRE[2], a=0.6, jit=5, wet=2.5, edge=0.6, gran=0.6, grav=0.5)
wash(img, [(-30, 992), (W + 30, 986), (W + 30, 1046), (-30, 1052)], SIENNA[3], a=0.4, jit=6, wet=2, edge=0.5, gran=0.7, dry=0.5)
# calm zone: a single pale glaze fading out, nothing drawn on it
wash(img, rect(-30, 1054, W + 30, 1140), OCHRE[3], a=0.28, jit=8, wet=16, edge=0.0, gran=0.3, grav=0, vary=0.4)

# ---------------- 2. knowledge base: wooden card-catalogue cabinet (right) ----------------
CX0, CY0, CX1, CY1 = 650, 600, 1000, 985
wash(img, [(CX1 - 10, CY1 - 6), (CX1 + 60, CY1 - 20), (CX1 + 70, CY1 + 22), (CX0 + 40, CY1 + 26)], ULTRA[1], a=0.4, wet=4, edge=0.4, gran=0.6)
wash(img, rect(CX0, CY0, CX1, CY1), SIENNA[2], a=0.8, jit=2, wet=1.4, edge=0.6, gran=0.5, grav=0.45, bloom=1)
wash(img, rect(CX0 - 14, CY0 - 30, CX1 + 14, CY0), SIENNA[1], a=0.8, jit=2, wet=1.2, edge=0.6, gran=0.4,
     holes=[rect(CX0 - 6, CY0 - 26, CX0 + 200, CY0 - 20)])                                                   # top board, lit edge reserved
wash(img, rect(CX1 - 34, CY0, CX1, CY1), SIENNA[0], a=0.5, jit=2, wet=1.2, edge=0.5, gran=0.4)               # right side in shade
wash(img, rect(CX0, CY1 - 26, CX1, CY1), SIENNA[0], a=0.5, jit=2, wet=1.2, edge=0.5, gran=0.4)               # plinth
cols, rows = 3, 5
DW, DH = (CX1 - 34 - CX0 - 24) / cols, (CY1 - 26 - CY0 - 20) / rows
OPEN = (0, 1)
drawers = {}
for r_ in range(rows):
    for c_ in range(cols):
        x0 = CX0 + 12 + c_ * DW + 6; y0 = CY0 + 10 + r_ * DH + 6
        x1, y1 = x0 + DW - 12, y0 + DH - 12
        drawers[(c_, r_)] = (x0, y0, x1, y1)
        if (c_, r_) == OPEN:
            wash(img, rect(x0, y0, x1, y1), NEUTRAL, a=0.8, jit=1.2, wet=1.0, edge=0.5, gran=0.3)        # dark cavity
            continue
        wash(img, rect(x0, y0, x1, y1), SIENNA[1], a=0.5, jit=1.5, wet=1.0, edge=0.7, gran=0.5, grav=0.5,
             holes=[rect(x0 + 3, y0 + 3, x1 - 24, y0 + 8)])
        mx = (x0 + x1) / 2
        wash(img, rect(mx - 15, y0 + 14, mx + 15, y0 + 28), OCHRE[1], a=0.7, jit=1, wet=0.8, edge=0.6, gran=0.2, vary=0.1)
        wash(img, ell(mx, y0 + 44, 6, 6, 14), SIENNA[0], a=0.7, jit=0.8, wet=0.8, edge=0.5, gran=0.1, vary=0.1)
# pulled-out drawer seen slightly from above: front face comes down & forward, interior shows filed cards
ox0, oy0, ox1, oy1 = drawers[OPEN]
sc, dy = 1.22, 92
mxo = (ox0 + ox1) / 2
fx0, fx1 = mxo - (ox1 - ox0) / 2 * sc, mxo + (ox1 - ox0) / 2 * sc
fy0, fy1 = oy0 + dy, oy0 + dy + (oy1 - oy0) * sc
wash(img, [(ox0, oy0), (ox1, oy0), (fx1, fy0), (fx0, fy0)], OCHRE[3], a=0.85, jit=0.8, wet=0.9, edge=0.4, gran=0.2, vary=0.2)   # interior, lit
wash(img, [(ox1, oy0), (fx1, fy0), (fx1, fy0 + 6), (ox1, oy0 + 4)], SIENNA[0], a=0.5, jit=0.5, wet=0.8, edge=0.4)                 # inner side wall
for k in range(5):  # filed card tops standing in the drawer
    t = (k + 0.7) / 5.6
    lx0 = ox0 + (fx0 - ox0) * t + 6; lx1 = ox1 + (fx1 - ox1) * t - 6; ly = oy0 + (fy0 - oy0) * t
    wash(img, [(lx0, ly - 1), (lx1, ly - 1), (lx1, ly + 3), (lx0, ly + 3)], SIENNA[0], a=0.45, jit=0.4, wet=0.6, edge=0.3, grav=0, vary=0.1)
# ---------------- 3. AI agent: tracked service robot (left), no face, single visor slot ----------------
wash(img, [(110, 995), (420, 985), (470, 1028), (150, 1040)], ULTRA[1], a=0.4, wet=4, edge=0.4, gran=0.6)
wash(img, rrect(100, 920, 400, 1000, 36), NEUTRAL, a=0.72, jit=1.5, wet=1.2, edge=0.6, gran=0.5, grav=0.4)
for k in range(5):
    wash(img, ell(140 + k * 55, 960, 20, 20, 18), ULTRA[2], a=0.65, jit=0.8, wet=0.9, edge=0.6, gran=0.3,
         holes=[ell(134 + k * 55, 954, 6, 6, 10)])
# torso: first glaze light, second glaze only on the shadow side (bottom-right), highlight reserved
wash(img, rrect(140, 650, 370, 925, 34), ULTRA[2], a=0.8, jit=2, wet=1.4, edge=0.6, gran=0.55, grav=0.45, bloom=1,
     holes=[[(160, 668), (300, 666), (290, 690), (164, 700)]])
wash(img, [(300, 650), (370, 680), (370, 925), (150, 925), (150, 880), (300, 860)], ULTRA[1], a=0.4, jit=3, wet=2.0, edge=0.55, gran=0.5)
wash(img, rrect(180, 720, 320, 850, 14), ULTRA[3], a=0.65, jit=1.5, wet=1.0, edge=0.7, gran=0.3)
for k in range(4):
    wash(img, rect(196, 742 + k * 22, 300, 750 + k * 22), ULTRA[0], a=0.55, jit=0.8, wet=0.8, edge=0.4, gran=0.2, vary=0.1)
wash(img, ell(290, 882, 11, 11, 16), OCHRE[1], a=0.85, jit=0.6, wet=0.8, edge=0.6, vary=0.1)
wash(img, rect(232, 612, 282, 656), NEUTRAL, a=0.6, jit=1, wet=1, edge=0.5, gran=0.4)
wash(img, rrect(170, 505, 345, 620, 30), ULTRA[2], a=0.8, jit=1.6, wet=1.3, edge=0.6, gran=0.5, grav=0.45,
     holes=[[(190, 518), (290, 516), (280, 532), (192, 540)]])
wash(img, [(300, 508), (345, 530), (345, 620), (180, 620), (180, 600), (300, 595)], ULTRA[1], a=0.35, jit=2, wet=1.8, edge=0.5, gran=0.5)
wash(img, rrect(190, 548, 328, 584, 16), NEUTRAL, a=0.88, jit=1, wet=1, edge=0.5, gran=0.3, vary=0.15)
wash(img, rrect(214, 558, 304, 574, 8), OCHRE[2], a=0.95, jit=0.6, wet=1.6, edge=0.2, gran=0.1, grav=0, vary=0)
wash(img, ell(259, 566, 70, 30), OCHRE[2], a=0.25, jit=2, wet=10, edge=0, gran=0, grav=0, vary=0)        # glow bleeding wet-in-wet
wash(img, limb((292, 505), (310, 448), 4), NEUTRAL, a=0.75, jit=0.5, wet=0.8, edge=0.3, grav=0)
wash(img, ell(312, 440, 12, 12, 16), ROSE[1], a=0.8, jit=0.6, wet=0.9, edge=0.6, holes=[ell(308, 436, 4, 4, 8)], vary=0.1)
wash(img, limb((150, 700), (112, 812), 15), ULTRA[1], a=0.7, jit=1, wet=1.1, edge=0.6, gran=0.5)
wash(img, ell(150, 700, 22, 22), NEUTRAL, a=0.6, jit=0.8, wet=1, edge=0.5)
wash(img, [(96, 812), (128, 812), (136, 846), (90, 846)], NEUTRAL, a=0.65, jit=0.8, wet=1, edge=0.5)
# reaching arm: shoulder -> elbow -> wrist, ending above the open drawer
SH, EL, WR = (362, 700), (480, 600), (604, 580)
wash(img, limb(SH, EL, 17), ULTRA[1], a=0.75, jit=1, wet=1.1, edge=0.6, gran=0.5)
wash(img, limb(EL, WR, 14), ULTRA[1], a=0.75, jit=1, wet=1.1, edge=0.6, gran=0.5)
for j, rr in ((SH, 24), (EL, 20)):
    wash(img, ell(j[0], j[1], rr, rr), NEUTRAL, a=0.62, jit=0.8, wet=1, edge=0.5, holes=[ell(j[0] - 6, j[1] - 6, 6, 6, 10)])
# gripper: two fingers pinching the card's top edge
wash(img, [(596, 566), (640, 570), (640, 586), (596, 590)], NEUTRAL, a=0.82, jit=0.6, wet=0.9, edge=0.5, vary=0.1)   # wrist block
wash(img, [(630, 584), (644, 584), (650, 612), (636, 614)], NEUTRAL, a=0.82, jit=0.6, wet=0.9, edge=0.5, vary=0.1)   # front finger
wash(img, [(604, 586), (616, 586), (614, 608), (602, 606)], NEUTRAL, a=0.82, jit=0.6, wet=0.9, edge=0.5, vary=0.1)   # back finger

# ---------------- 4. the note card, half-way into the open drawer ----------------
RESERVE.remove(CARD)
wash(img, CARD, ULTRA[3], a=0.35, jit=0.6, wet=0.8, edge=0.95, gran=0.15, grav=0, vary=0.2)     # paper card: only its rim is painted
wash(img, rot(rect(604, 600, 724, 613), 610, 602, 5), ROSE[2], a=0.65, jit=0.4, wet=0.7, edge=0.5, grav=0, vary=0.1)   # index-card header band
for k in range(3):
    wash(img, rot(rect(618, 630 + k * 16, 704 - k * 16, 634 + k * 16), 610, 602, 5), ULTRA[1], a=0.55, jit=0.3, wet=0.6, edge=0.2, grav=0, vary=0.1)
wash(img, rect(fx0, fy0, fx1, fy1), SIENNA[1], a=0.75, jit=1.5, wet=1.0, edge=0.7, gran=0.5, grav=0.5,
     holes=[rect(fx0 + 4, fy0 + 3, fx1 - 30, fy0 + 9)])
mx = (fx0 + fx1) / 2
wash(img, rect(mx - 16, fy0 + 15, mx + 16, fy0 + 30), OCHRE[1], a=0.75, jit=1, wet=0.8, edge=0.6, vary=0.1)
wash(img, ell(mx, fy0 + 48, 7, 7, 14), SIENNA[0], a=0.75, jit=0.8, wet=0.8, edge=0.5, vary=0.1)
wash(img, [(fx0 + 6, fy1), (fx1 + 10, fy1), (fx1 + 26, fy1 + 16), (fx0 + 20, fy1 + 16)], NEUTRAL, a=0.4, jit=1, wet=2.5, edge=0.3)  # drawer's shadow

# motion path: dry-brush dabs arcing from the robot's chest toward the drawer
for k, (tx, ty) in enumerate([(470, 520), (510, 498), (552, 488), (594, 492), (634, 508)]):
    wash(img, ell(tx, ty, 7 - k * 0.5, 4), ULTRA[1], a=0.22 + k * 0.05, jit=1.2, wet=1, edge=0.6, gran=0.6, dry=0.4)
# warm light pooling in the receiving drawer (wet-in-wet glow)
wash(img, ell((ox0 + ox1) / 2, oy0 + 40, 100, 70), OCHRE[2], a=0.35, jit=6, wet=14, edge=0, gran=0.2, grav=0, vary=0.2)

# ---------------- 5. darkest accents last (wet-on-dry, hard edges) ----------------
wash(img, [(370, 905), (395, 920), (380, 930), (300, 928)], NEUTRAL, a=0.4, jit=1, wet=1, edge=0.6)
splatter(img, 470, 880, 70, OCHRE[1], 14)
splatter(img, 90, 1000, 60, SIENNA[1], 14)
splatter(img, 960, 1000, 50, ULTRA[1], 10)

# ---------------- 6. pencil underdrawing left visible ----------------
d = ImageDraw.Draw(img, 'RGBA')
pencil(d, rect(CX0, CY0, CX1, CY1)); pencil(d, rect(CX0 - 14, CY0 - 30, CX1 + 14, CY0))
pencil(d, rrect(140, 650, 370, 925, 34, 3), over=6); pencil(d, rrect(170, 505, 345, 620, 30, 3), over=6)
pencil(d, rrect(100, 920, 400, 1000, 36, 3), over=6); pencil(d, CARD, over=8, alpha=120)
pencil(d, [SH, EL, WR], closed=False, over=6); pencil(d, rect(fx0, fy0, fx1, fy1), over=8)
d.line([(40, 975), (1040, 966)], fill=PENCIL + (50,), width=1)   # horizon guide

# ---------------- 7. lettering painted as pigment ----------------
ink_text(img, (78, 70), "知識庫", ImageFont.truetype(HEI, 132), ULTRA[0], a=0.95)
ink_text(img, (1012, 420), "61%", ImageFont.truetype(BASK, 250, index=1), ROSE[1], a=0.95, anchor='rs')
wash(img, [(560, 440), (1004, 432), (1008, 446), (562, 456)], ROSE[2], a=0.5, jit=1.5, wet=1.2, edge=0.6, gran=0.6, dry=0.6)  # dry-brush underline

img.save(os.path.join(HERE, "sample.png"))
