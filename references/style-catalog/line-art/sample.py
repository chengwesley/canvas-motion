"""line-art style sample: whiteboard / sketchnote hand-drawn line art (all original).

Technique encoded in helpers:
  - stroke(): pressure-tapered line with low-frequency hand wobble (never a ruler line)
  - seg()/box(): straight edges drawn as separate strokes that overshoot at corners
  - loop(): circles drawn in one motion that overlap instead of closing perfectly
  - hatch(): 45-degree parallel hatching clipped to a region = the only "shadow"
  - marker(): flat accent fill laid in broad streaks, slightly mis-registered vs. the line
Rendered at 2x then downsampled for soft ink edges. Deterministic (fixed seeds).
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

W, H, S = 1080, 1350, 2               # output size, supersample factor
PAPER = (251, 250, 246)               # #FBFAF6 board white
INK = (30, 30, 30)                    # #1E1E1E marker black
INK_SOFT = (120, 120, 120)            # #787878 light construction lines
ACC = (240, 90, 40)                   # #F05A28 single accent (orange-red marker)
ACC_TINT = (252, 214, 196)            # #FCD6C4 accent at ~25% (marker fill)
BLUE = (47, 128, 200)                 # #2F80C8 secondary, max 1-2 small uses
BLUE_TINT = (205, 226, 244)           # #CDE2F4
SHADOW = (222, 222, 218)             # #DEDEDA grey marker drop-shadow
LW = W * 0.0055                       # main line weight (~6px @1080)
FONT_H = '/System/Library/Fonts/STHeiti Medium.ttc'
FONT_L = '/System/Library/Fonts/Hiragino Sans GB.ttc'

# --- layers: one coverage mask per colour, composited at the end ---------------
LAYERS = {}
def layer(name):
    if name not in LAYERS: LAYERS[name] = Image.new('L', (W * S, H * S), 0)
    return LAYERS[name]


class Wob:
    """Smooth 1-D noise from summed sines with random phases (hand tremor)."""
    def __init__(s, seed):
        r = random.Random(seed)
        s.h = [(r.uniform(.6, 1.4) * f, r.uniform(0, 6.28), a) for f, a in ((1, .6), (2.3, .3), (5.1, .1))]
    def __call__(s, t): return sum(a * math.sin(f * t + p) for f, p, a in s.h)


_seed = [100]
def nseed(): _seed[0] += 1; return _seed[0]


def stroke(pts, w=LW, lay='ink', amp=1.6, taper=True, seed=None, val=255):
    """Draw a polyline as one hand stroke: resample, perpendicular wobble, pressure taper."""
    wob = Wob(seed or nseed()); pw = Wob(nseed())
    d = ImageDraw.Draw(layer(lay))
    seglen = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    L = sum(seglen) or 1
    s = 0.0; step = 0.9
    for i, sl in enumerate(seglen):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        nx, ny = (-(y1 - y0) / (sl or 1), (x1 - x0) / (sl or 1))
        k = 0.0
        while k <= sl:
            t = k / (sl or 1); x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
            o = amp * wob(s / 90)
            x += nx * o; y += ny * o
            ww = w * (0.92 + 0.16 * pw(s / 60))
            if taper:
                e = min(1, s / 26, (L - s) / 26)
                ww *= 0.45 + 0.55 * max(0, e)
            r = max(.5, ww / 2) * S
            d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=val)
            k += step; s += step


def seg(a, b, w=LW, lay='ink', over=(4, 9), amp=1.4):
    """Straight edge with overshoot at both ends (marker lifted late)."""
    r = random.Random(nseed())
    dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy) or 1; ux, uy = dx / l, dy / l
    o0, o1 = r.uniform(*over), r.uniform(*over)
    stroke([(a[0] - ux * o0, a[1] - uy * o0), (b[0] + ux * o1, b[1] + uy * o1)], w, lay, amp)


def box(x0, y0, x1, y1, w=LW, lay='ink'):
    seg((x0, y0), (x1, y0), w, lay); seg((x1, y0), (x1, y1), w, lay)
    seg((x1, y1), (x0, y1), w, lay); seg((x0, y1), (x0, y0), w, lay)


def loop(cx, cy, rx, ry, w=LW, lay='ink', a0=-2.2, extra=.35):
    """Ellipse in one motion, ends overlap by `extra` radians."""
    wob = Wob(nseed()); n = int((rx + ry) * 1.2) + 20
    pts = []
    for i in range(n + 1):
        a = a0 + (2 * math.pi + extra) * i / n
        k = 1 + .025 * wob(a * 1.3)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    stroke(pts, w, lay, amp=.6)


def spline(ctrl, n=40):
    """Catmull-Rom through control points."""
    P = [ctrl[0]] + list(ctrl) + [ctrl[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2, t3 = t * t, t * t * t
            out.append(tuple(.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(ctrl[-1]); return out


def arrow(ctrl, w=LW, lay='ink', head=26, dash=None):
    pts = spline(ctrl)
    if dash:
        # dashed: stroke every other chunk of the path
        acc, chunk, on = 0, [], True
        for i in range(len(pts) - 1):
            chunk.append(pts[i]); acc += math.dist(pts[i], pts[i + 1])
            if acc > (dash if on else dash * .7):
                if on and len(chunk) > 1: stroke(chunk + [pts[i + 1]], w, lay, amp=.8)
                on = not on; acc = 0; chunk = []
    else:
        stroke(pts, w, lay, amp=1.0)
    (xa, ya), (xb, yb) = pts[-6], pts[-1]
    a = math.atan2(yb - ya, xb - xa)
    for da in (2.55, -2.45):
        stroke([(xb + head * math.cos(a + da), yb + head * math.sin(a + da)), (xb, yb)], w, lay, amp=.5)


def region(poly=None, rect=None, ell=None):
    m = Image.new('L', (W * S, H * S), 0); d = ImageDraw.Draw(m)
    sc = lambda p: [(x * S, y * S) for x, y in p]
    if poly: d.polygon(sc(poly), fill=255)
    if rect: d.rectangle([v * S for v in rect], fill=255)
    if ell: cx, cy, rx, ry = ell; d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=255)
    return m


def hatch(mask, spacing=W * .011, ang=45, w=LW * .38, lay='ink'):
    """Parallel hatching (top-right to bottom-left), clipped to mask. Only shading device."""
    tmp_name = '_hatch'; LAYERS.pop(tmp_name, None)
    bb = mask.getbbox()
    if not bb: return
    x0, y0, x1, y1 = [v / S for v in bb]
    a = math.radians(ang); ux, uy = math.cos(a), -math.sin(a)  # direction of the hatch line
    nx, ny = -uy, ux
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = math.hypot(x1 - x0, y1 - y0) / 2 + 4
    r = random.Random(nseed()); k = -R
    while k <= R:
        px, py = cx + nx * k, cy + ny * k
        j = r.uniform(-.15, .15)
        stroke([(px - ux * R, py - uy * R), (px + ux * R, py + uy * R)], w * r.uniform(.85, 1.15), tmp_name, amp=.4, taper=False)
        k += spacing * (1 + j)
    hl = ImageChops.multiply(LAYERS.pop(tmp_name), mask)
    tgt = layer(lay); LAYERS[lay] = ImageChops.lighter(tgt, hl)


def marker(mask, lay='acc_fill', width=W * .03, ang=-28, shift=(7, 5)):
    """Accent fill in broad streaks; offset a few px from the outline (mis-registration)."""
    tmp = Image.new('L', (W * S, H * S), 0); d = ImageDraw.Draw(tmp)
    bb = mask.getbbox()
    if not bb: return
    x0, y0, x1, y1 = bb; r = random.Random(nseed())
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = math.hypot(x1 - x0, y1 - y0) / 2
    k = -R; i = 0
    while k <= R:
        px, py = cx + nx * k, cy + ny * k
        d.line([(px - ux * R, py - uy * R), (px + ux * R, py + uy * R)], fill=(215 if i % 2 else 255), width=int(width * S * 1.15))
        k += width * S * .92; i += 1
    m = mask.transform(mask.size, Image.AFFINE, (1, 0, -shift[0] * S, 0, 1, -shift[1] * S))
    m = ImageChops.multiply(tmp, m)
    LAYERS[lay] = ImageChops.lighter(layer(lay), m)


def text(s, xy, size, font=FONT_H, lay='ink', anchor='la'):
    f = ImageFont.truetype(font, int(size * S))
    ImageDraw.Draw(layer(lay)).text((xy[0] * S, xy[1] * S), s, font=f, fill=255, anchor=anchor)


def wordbox(s, size, font=FONT_H):
    f = ImageFont.truetype(font, int(size)); return f.getbbox(s)


# =============================== scene ==========================================
random.seed(7)

# ---- heading: 知識庫 + marker swoosh underline (top-left) ----
text('知識庫', (78, 78), 92)
stroke(spline([(74, 196), (190, 188), (320, 192), (372, 186)]), W * .016, 'acc', amp=1.2)
text('KNOWLEDGE BASE', (80, 222), 30, FONT_L, 'soft')

# ---- big number 61% (top-right) with circled emphasis ----
text('61', (842 - 40 + 9, 72 + 9), 196, lay='shadow', anchor='ra'); text('%', (848 - 40 + 7, 148 + 7), 104, lay='shadow')
text('61', (842 - 40, 72), 196, anchor='ra')
text('%', (848 - 40, 148), 104, anchor='la')
loop(752, 172, 228, 108, W * .0045, 'acc', a0=-2.9, extra=.45)
text('筆記被重複引用', (752, 296), 30, FONT_L, 'soft', anchor='ma')

# ---- knowledge base: hand-drawn bookshelf (right) ----
SX0, SY0, SX1, SY1 = 600, 450, 980, 960
# side shadow: hatch a thin strip to the right/bottom of the cabinet (light from top-left)
hatch(region(poly=[(SX1, SY0 + 18), (SX1 + 24, SY0 + 34), (SX1 + 24, SY1 + 22), (SX1, SY1)]))
hatch(region(poly=[(SX0 + 20, SY1), (SX1, SY1), (SX1 + 24, SY1 + 22), (SX0 + 40, SY1 + 22)]))
box(SX0, SY0, SX1, SY1)
seg((SX1, SY0), (SX1 + 24, SY0 + 22), LW * .8); seg((SX1 + 24, SY0 + 22), (SX1 + 24, SY1 + 22), LW * .8)
seg((SX1 + 24, SY1 + 22), (SX1, SY1), LW * .8)
shelves = [SY0 + 165, SY0 + 335]
for y in shelves: seg((SX0, y), (SX1, y), LW)
# books: tall thin rectangles, varied heights, one leaning; spines get 1-2 short ticks
r = random.Random(3)
rows = [(SY0, shelves[0]), (shelves[0], shelves[1]), (shelves[1], SY1)]
slot = None
for ri, (top, bot) in enumerate(rows):
    x = SX0 + 18
    while x < SX1 - 40:
        bw = r.choice((30, 36, 42, 48)); bh = r.randint(88, 138)
        if ri == 1 and slot is None:
            slot = (x, bot - 132, x + 96, bot); x += 110; continue
        if x + bw > SX1 - 14: break
        if r.random() < .12 and x + bw + 30 < SX1 - 14:
            # leaning book
            stroke([(x, bot - 4), (x + 30, bot - bh + 6), (x + 30 + bw * .9, bot - bh + 18), (x + bw + 4, bot - 2)], LW * .8, amp=.8, taper=False)
            x += bw + 36; continue
        box(x, bot - bh, x + bw, bot - 4, LW * .8)
        for t in range(r.randint(1, 2)):
            yy = bot - bh + 18 + t * 12; seg((x + 8, yy), (x + bw - 8, yy), LW * .5, over=(0, 2), amp=.3)
        if r.random() < .3: hatch(region(rect=(x + 2, bot - bh + 2, x + bw - 2, bot - 6)), spacing=W * .009)
        x += bw + r.randint(2, 6)
sx0, sy0, sx1, sy1 = slot
# cabinet label
seg((SX0 + 40, SY0), (SX0 + 70, SY0 - 40), LW * .6, over=(0, 2)); seg((SX0 + 130, SY0), (SX0 + 100, SY0 - 40), LW * .6, over=(0, 2))
box(SX0 + 40, SY0 - 92, SX0 + 150, SY0 - 40, LW * .8)
text('KB', (SX0 + 95, SY0 - 88), 34, FONT_H, 'ink', anchor='ma')

# ---- note card held by the agent, flying into the slot ----
CX0, CY0, CX1, CY1 = 410, 585, 535, 745
card = [(CX0, CY0 + 10), (CX1 - 6, CY0), (CX1 + 6, CY1 - 12), (CX0 + 10, CY1)]  # slightly rotated
marker(region(poly=card), 'acc_fill', shift=(8, 6))
for i in range(4): seg(card[i], card[(i + 1) % 4], LW)
for k, lw in enumerate((.78, .62, .72, .45)):
    y = CY0 + 46 + k * 30; x0 = CX0 + 22 + k * 1.5
    stroke([(x0, y), (x0 + (CX1 - CX0 - 40) * lw, y - 4)], LW * .55, amp=.7)
# folded corner
seg((CX1 - 30, CY0 + 3), (CX1 - 22, CY0 + 30), LW * .7); seg((CX1 - 22, CY0 + 30), (CX1 + 1, CY0 + 24), LW * .7)
# ghost card inside the slot (destination), dashed accent
gx0, gy0, gx1, gy1 = sx0 + 12, sy1 - 112, sx1 - 12, sy1 - 8
def dashed(a, b, w, lay, n):
    for k in range(n):
        p = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
        q = (a[0] + (b[0] - a[0]) * (k + .55) / n, a[1] + (b[1] - a[1]) * (k + .55) / n)
        stroke([p, q], w, lay, amp=.2, taper=False)
gc = [(gx0, gy0), (gx1, gy0), (gx1, gy1), (gx0, gy1)]
for i in range(4): dashed(gc[i], gc[(i + 1) % 4], LW * .7, 'acc', 4)
# motion arrow: short arc from the held card into the slot
arrow([(CX1 + 18, CY0 + 30), (570, CY0 + 18), (gx0 - 8, gy0 + 40)], LW * .95, 'acc', head=22)

# ---- AI agent: abstract boxy machine, visor band (no face), left ----
AX = 205
# ground shadow: hatched ellipse
hatch(region(ell=(AX + 10, 938, 150, 22)), spacing=W * .010)
# head
box(AX - 82, 402, AX + 82, 528)
# visor band (the only "face" element): a filled accent-tinted bar with a scan tick
visor = (AX - 60, 446, AX + 60, 486)
marker(region(rect=visor), 'blue_fill', width=W * .02, ang=0, shift=(5, 4))
box(*visor, LW * .85)
stroke([(AX - 40, 466), (AX - 10, 466)], LW * .9, 'blue', amp=.3)
for sx in (-1, 1): loop(AX + sx * 96, 466, 12, 20, LW * .8)
# antenna
seg((AX, 402), (AX, 352), LW * .85, over=(0, 3)); loop(AX, 340, 13, 13, LW * .8)
marker(region(ell=(AX, 340, 12, 12)), 'acc_fill', width=W * .012, shift=(3, 2))
# signal arcs
for k, rr in enumerate((30, 48)):
    pts = [(AX + rr * math.cos(a), 340 + rr * math.sin(a)) for a in [-.9 + i * .06 for i in range(16)]]
    stroke(pts, LW * .55, 'soft', amp=.2)
# neck + body
seg((AX - 22, 528), (AX - 22, 556), LW * .8, over=(0, 2)); seg((AX + 22, 528), (AX + 22, 556), LW * .8, over=(0, 2))
body = (AX - 108, 556, AX + 108, 800)
box(*body)
# body side shading: hatch right third (light from top-left)
hatch(region(rect=(AX + 56, 560, AX + 106, 798)))
# chest panel with three status ticks
box(AX - 60, 600, AX + 30, 660, LW * .75)
for k in range(3): loop(AX - 38 + k * 26, 630, 7, 7, LW * .6)
marker(region(ell=(AX - 38, 630, 7, 7)), 'acc_fill', width=W * .01, shift=(2, 2))
for k in range(3): seg((AX - 70, 700 + k * 22), (AX + 40 - k * 18, 700 + k * 22), LW * .5, over=(0, 3), amp=.4)
# legs / tracks
box(AX - 92, 800, AX - 18, 920); box(AX + 18, 800, AX + 92, 920)
for xx in (AX - 55, AX + 55):
    for k in range(3): seg((xx - 28, 830 + k * 28), (xx + 28, 830 + k * 28), LW * .5, over=(0, 2), amp=.3)
# arm reaching to the card (two segments + gripper)
def limb(p, q, half):
    """Mechanical arm segment: two parallel edges, ends left open for the joints."""
    dx, dy = q[0] - p[0], q[1] - p[1]; l = math.hypot(dx, dy); nx, ny = -dy / l * half, dx / l * half
    seg((p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), LW * .9, over=(0, 3)); seg((p[0] - nx, p[1] - ny), (q[0] - nx, q[1] - ny), LW * .9, over=(0, 3))
SH, EL, WR = (AX + 112, 600), (AX + 170, 712), (CX0 - 10, 665)
limb(SH, EL, 15); limb(EL, WR, 13)
for (jx, jy), rr in ((SH, 20), (EL, 19), (WR, 15)): loop(jx, jy, rr, rr, LW * .85)
marker(region(ell=(EL[0], EL[1], 8, 8)), 'acc_fill', width=W * .01, shift=(2, 2))
# two-finger gripper pinching the card edge
seg((WR[0] + 8, WR[1] - 12), (CX0 + 26, WR[1] - 22), LW * .85, over=(0, 2)); seg((WR[0] + 8, WR[1] + 12), (CX0 + 26, WR[1] + 22), LW * .85, over=(0, 2))
# other arm down
stroke(spline([(AX - 104, 600), (AX - 140, 680), (AX - 128, 760)], 20), LW, amp=.6)
stroke(spline([(AX - 104, 630), (AX - 120, 690), (AX - 104, 760)], 20), LW, amp=.6)
loop(AX - 118, 774, 18, 16, LW * .8)
# label
text('AI Agent', (AX, 968), 30, FONT_H, 'soft', anchor='ma')

# ---- tiny sketchnote marks ----
# sparkle near slot
for a in range(0, 360, 90):
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    stroke([(sx1 + 30 + ca * 8, sy0 - 18 + sa * 8), (sx1 + 30 + ca * 20, sy0 - 18 + sa * 20)], LW * .6, 'acc', amp=.1, taper=False)

# bottom ~22% (y > 1053) left completely empty for subtitles

# =============================== composite ======================================
def tex_paper():
    """Very light paper tooth: blurred random noise, +-3 levels."""
    r = random.Random(11); sm = Image.new('L', (W // 6, H // 6))
    sm.putdata([128 + r.randint(-2, 2) for _ in range(sm.width * sm.height)])
    return sm.resize((W * S, H * S), Image.BICUBIC)

img = Image.new('RGB', (W * S, H * S), PAPER)
grain = tex_paper()
img = ImageChops.add(ImageChops.subtract(img, Image.merge('RGB', [grain.point(lambda v: max(0, 128 - v))] * 3)),
                     Image.merge('RGB', [grain.point(lambda v: max(0, v - 128))] * 3))

def lay_on(base, name, col, mode='over'):
    if name not in LAYERS: return base
    m = LAYERS[name]
    if mode == 'multiply':
        tint = Image.new('RGB', base.size, col)
        mult = ImageChops.multiply(base, tint)
        return Image.composite(mult, base, m)
    return Image.composite(Image.new('RGB', base.size, col), base, m)

img = lay_on(img, 'acc_fill', ACC_TINT, 'multiply')
img = lay_on(img, 'blue_fill', BLUE_TINT, 'multiply')
img = lay_on(img, 'shadow', SHADOW)
img = lay_on(img, 'soft', INK_SOFT)
img = lay_on(img, 'blue', BLUE)
img = lay_on(img, 'acc', ACC)
img = lay_on(img, 'ink', INK)
img = img.resize((W, H), Image.LANCZOS)
img.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.png'))
