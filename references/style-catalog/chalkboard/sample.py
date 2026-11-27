# Chalkboard style sample: AI agent filing a note card into a knowledge base, big 61%.
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1350
R = random.Random(61)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample.png")
HEI = "/System/Library/Fonts/STHeiti Medium.ttc"
HAND = "/System/Library/Fonts/Supplemental/ChalkboardSE.ttc"   # Latin + digits only (0 Light, 1 Regular, 2 Bold)

# Palette (must match style.md). Chalk colours are applied through a broken mask, so on screen they
# read a step darker/greener than the hex: that is the point.
BOARD = (34, 56, 46)        # slate green
BOARD_WIPE = (70, 92, 82)   # eraser ghosts
WHITE = (238, 238, 226)     # main chalk: 80% of all marks
YELLOW = (242, 222, 130)    # the new thing / the number
PINK = (240, 168, 160)      # emphasis underline only
BLUE = (160, 205, 230)      # secondary info (AI system parts, network)
TRAY = (92, 66, 44)         # wooden chalk ledge

def board():
    """Slate-green base with mottled eraser wipes and fine grain."""
    img = Image.new("RGB", (W, H), BOARD)
    wipe = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(wipe)
    for _ in range(26):  # broad eraser arcs left from previous lessons
        cx, cy = R.randint(0, W), R.randint(0, H)
        rw, rh = R.randint(120, 380), R.randint(30, 90)
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=R.randint(10, 26))
    wipe = wipe.filter(ImageFilter.GaussianBlur(40))
    img = Image.composite(Image.new("RGB", (W, H), BOARD_WIPE), img, wipe)
    grain = Image.effect_noise((W, H), 22).point(lambda v: max(0, v - 128) // 3)
    img = Image.composite(Image.new("RGB", (W, H), (120, 140, 130)), img, grain)
    return img

class Chalk:
    """Accumulates chalk marks into per-colour masks, then applies paper-tooth dropout."""
    def __init__(self):
        self.layers = {}
    def mask(self, col):
        if col not in self.layers:
            self.layers[col] = Image.new("L", (W, H), 0)
        return self.layers[col]
    def line(self, col, p0, p1, w=5, a=230, wobble=1.6):
        """A chalk stroke: overlapping jittered dabs, uneven pressure, broken edges."""
        d = ImageDraw.Draw(self.mask(col))
        L = math.dist(p0, p1)
        n = max(2, int(L / 1.6))
        nx, ny = (-(p1[1] - p0[1]) / (L or 1), (p1[0] - p0[0]) / (L or 1))
        drift = 0.0
        for i in range(n + 1):
            t = i / n
            drift += R.uniform(-0.25, 0.25); drift = max(-wobble, min(wobble, drift))
            x = p0[0] + (p1[0] - p0[0]) * t + nx * drift
            y = p0[1] + (p1[1] - p0[1]) * t + ny * drift
            press = 0.75 + 0.25 * math.sin(t * math.pi)  # lighter at start/end
            for _ in range(2):
                ox, oy = R.gauss(0, w * 0.28), R.gauss(0, w * 0.28)
                r = w * R.uniform(0.25, 0.55)
                d.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=int(a * press * R.uniform(0.7, 1)))
    def poly(self, col, pts, closed=True, **k):
        seq = pts + ([pts[0]] if closed else [])
        for p, q in zip(seq, seq[1:]):
            # slight overshoot at corners like hand-drawn chalk
            ext = 4
            L = math.dist(p, q) or 1
            ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
            self.line(col, (p[0] - ux * ext, p[1] - uy * ext), (q[0] + ux * ext, q[1] + uy * ext), **k)
    def rect(self, col, x0, y0, x1, y1, **k):
        self.poly(col, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **k)
    def circle(self, col, cx, cy, r, seg=40, **k):
        pts = [(cx + r * math.cos(2 * math.pi * i / seg) + R.uniform(-1, 1),
                cy + r * math.sin(2 * math.pi * i / seg) + R.uniform(-1, 1)) for i in range(seg)]
        self.poly(col, pts, **k)
    def hatch(self, col, x0, y0, x1, y1, gap=9, ang=-0.9, w=2.2, a=140):
        """Side-of-chalk diagonal shading clipped to a box."""
        tmp = Chalk(); tmp.layers = {}
        span = (x1 - x0) + (y1 - y0)
        k = 0
        while k < span * 1.5:
            sx = x0 - (y1 - y0) + k
            tmp.line(col, (sx, y1), (sx + (y1 - y0) * abs(math.tan(ang)), y0), w=w, a=a, wobble=0.8)
            k += gap + R.uniform(-2, 2)
        clip = Image.new("L", (W, H), 0); ImageDraw.Draw(clip).rectangle([x0, y0, x1, y1], fill=255)
        m = ImageChops.multiply(tmp.mask(col), clip)
        self.layers[col] = ImageChops.lighter(self.mask(col), m)
    def dashed(self, col, pts, dash=16, gap=11, **k):
        for p, q in zip(pts, pts[1:]):
            L = math.dist(p, q); t = 0
            while t < L:
                e = min(L, t + dash)
                a_ = (p[0] + (q[0] - p[0]) * t / L, p[1] + (q[1] - p[1]) * t / L)
                b_ = (p[0] + (q[0] - p[0]) * e / L, p[1] + (q[1] - p[1]) * e / L)
                self.line(col, a_, b_, **k); t += dash + gap
    def text(self, col, xy, s, font, a=235):
        """Text pressed into chalk: glyph mask eroded by grain, edges roughened."""
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).text(xy, s, font=font, fill=a)
        m = m.filter(ImageFilter.GaussianBlur(0.8))
        self.layers[col] = ImageChops.lighter(self.mask(col), m)
    def render(self, base):
        tooth = Image.effect_noise((W, H), 70).point(lambda v: 255 if v > 92 else int(v * 2.2))
        streak = Image.effect_noise((W // 6, H), 50).resize((W, H)).point(lambda v: min(255, v + 90))
        for col, m in self.layers.items():
            m = ImageChops.multiply(m, tooth)
            m = ImageChops.multiply(m, streak)
            base.paste(Image.new("RGB", (W, H), col), (0, 0), m)
            # chalk dust halo
            halo = m.filter(ImageFilter.GaussianBlur(7)).point(lambda v: v // 5)
            base.paste(Image.new("RGB", (W, H), col), (0, 0), halo)
        return base

def dust(img):
    """Loose powder: fine specks, densest under drawn areas, plus soft horizontal eraser swipes."""
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for _ in range(700):
        x, y = R.randint(0, W), int(R.triangular(120, 1080, 700))
        r = R.uniform(0.6, 1.8); d.ellipse([x - r, y - r, x + r, y + r], fill=R.randint(30, 120))
    for _ in range(4):  # eraser swipe: wide, very faint, horizontal
        x, y = R.randint(40, 600), R.randint(1100, 1240)
        for k in range(10):
            d.line([(x + k * 3, y + k * 4), (x + 420 + k * 5, y + k * 4 + R.randint(-3, 3))], fill=10, width=4)
    m = m.filter(ImageFilter.GaussianBlur(1.6))
    img.paste(Image.new("RGB", (W, H), WHITE), (0, 0), m)
    return img


def check_glyphs(path, text, size=80):
    """Fail loudly if any CJK char would render as tofu / notdef."""
    f = ImageFont.truetype(path, size)
    def m(ch):
        im = Image.new("L", (size * 2, size * 2), 0)
        ImageDraw.Draw(im).text((size // 2, size // 2), ch, font=f, fill=255)
        return im
    notdef = m("\U000F0000").tobytes()
    for ch in text.replace(" ", ""):
        b = m(ch)
        assert b.getbbox() and b.tobytes() != notdef, f"missing glyph {ch!r}"


def arc_pts(p0, p1, bulge, n=24):
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    L = math.dist(p0, p1) or 1
    cx, cy = mx + -(p1[1] - p0[1]) / L * bulge, my + (p1[0] - p0[0]) / L * bulge
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy + t * t * p1[1]) for t in [i / n for i in range(n + 1)]]


check_glyphs(HEI, "知識庫AI 助理")
img = board()
c = Chalk()
fH = ImageFont.truetype(HEI, 122)
fBig = ImageFont.truetype(HAND, 236, index=2)
fS = ImageFont.truetype(HEI, 38)
fL = ImageFont.truetype(HAND, 34, index=1)

# ---- heading (top-left) + double underline, like a teacher's title ----
c.text(WHITE, (70, 66), "知識庫", fH)
c.line(WHITE, (64, 218), (446, 210), w=6)
c.line(WHITE, (96, 234), (390, 230), w=3.5, a=160)

# ---- big 61% (top-right), circled once with a hasty pink loop ----
c.text(YELLOW, (590, 30), "61%", fBig)
loop = [(800 + 250 * math.cos(a) + R.uniform(-4, 4), 170 + 118 * math.sin(a) + R.uniform(-4, 4))
        for a in [math.radians(200 + k * 13) for k in range(30)]]
c.poly(PINK, loop, closed=False, w=4.5, a=200)
c.text(WHITE, (690, 296), "notes filed", fL, a=190)

# ---- robot: boxy head with visor slit (no face), antenna, body, tread; outline + side-of-chalk hatching ----
rx, ry = 110, 520
c.line(WHITE, (rx + 95, ry - 16), (rx + 95, ry - 66), w=4)                   # antenna
c.circle(YELLOW, rx + 95, ry - 78, 12, seg=16, w=4)
c.rect(WHITE, rx + 18, ry - 16, rx + 172, ry + 92, w=6)                       # head
c.line(BLUE, (rx + 40, ry + 32), (rx + 150, ry + 30), w=12)                   # visor slit
c.hatch(WHITE, rx + 120, ry - 12, rx + 168, ry + 88, gap=10, a=120)           # shadow side (light from top-left)
c.line(WHITE, (rx + 95, ry + 92), (rx + 95, ry + 114), w=7)                   # neck
c.rect(WHITE, rx, ry + 114, rx + 190, ry + 320, w=6)                          # body
c.hatch(WHITE, rx + 120, ry + 118, rx + 186, ry + 316, gap=10, a=110)
c.hatch(WHITE, rx + 4, ry + 262, rx + 120, ry + 316, gap=10, a=90)
c.circle(BLUE, rx + 62, ry + 180, 24, seg=22, w=4)                            # status dial
c.line(BLUE, (rx + 62, ry + 180), (rx + 76, ry + 166), w=3)
for k in range(3):                                                             # vents
    c.line(WHITE, (rx + 30, ry + 226 + k * 12), (rx + 96, ry + 226 + k * 12), w=3, a=160)
c.rect(WHITE, rx - 14, ry + 330, rx + 204, ry + 378, w=5)                     # tread
for k in range(4):
    c.circle(WHITE, rx + 22 + k * 56, ry + 354, 14, seg=14, w=4)
c.line(WHITE, (rx + 40, ry + 320), (rx + 40, ry + 330), w=5); c.line(WHITE, (rx + 150, ry + 320), (rx + 150, ry + 330), w=5)

# arm: shoulder -> elbow -> wrist, joints circled; gripper pinches the card
sh, el, wr = (rx + 190, ry + 150), (rx + 300, ry + 90), (rx + 400, ry + 12)
c.line(WHITE, sh, el, w=8); c.line(WHITE, el, wr, w=8)
c.circle(WHITE, *sh, 11, seg=12, w=4); c.circle(WHITE, *el, 10, seg=12, w=4)
c.line(WHITE, wr, (wr[0] + 26, wr[1] - 26), w=5); c.line(WHITE, wr, (wr[0] + 34, wr[1] + 2), w=5)

# ---- note card (yellow = the new thing), tilted, with ruled lines ----
cx0, cy0 = wr[0] + 14, wr[1] - 118
card = [(cx0, cy0 + 24), (cx0 + 150, cy0), (cx0 + 168, cy0 + 100), (cx0 + 18, cy0 + 124)]
c.poly(YELLOW, card, w=5)
c.hatch(YELLOW, cx0 + 6, cy0 + 8, cx0 + 162, cy0 + 118, gap=14, w=1.6, a=70)
for i in range(3):
    y = cy0 + 50 + i * 22
    c.line(YELLOW, (cx0 + 30, y + 2), (cx0 + 140 - i * 22, y - 18 + 2), w=3, a=190)
# motion ticks behind the card
for k in range(3):
    c.line(WHITE, (cx0 - 26 - k * 4, cy0 + 4 + k * 26), (cx0 - 12 - k * 4, cy0 - 10 + k * 26), w=3, a=150)

# ---- knowledge base: shelf cabinet with roof + network nodes; one empty slot waiting ----
bx0, by0, bx1, by1 = 650, 600, 1010, 1010
c.rect(WHITE, bx0, by0, bx1, by1, w=6)
c.line(WHITE, (bx0 - 22, by0), ((bx0 + bx1) / 2, by0 - 74), w=6)
c.line(WHITE, ((bx0 + bx1) / 2, by0 - 74), (bx1 + 22, by0), w=6)
shelves = [by0 + 102, by0 + 204, by0 + 306]
for y in shelves:
    c.line(WHITE, (bx0, y), (bx1, y), w=5)
slot = None
for si, top in enumerate([by0, *shelves]):
    bottom = shelves[si] if si < 3 else by1
    x = bx0 + 16
    while x < bx1 - 36:
        bw = R.randint(22, 34); bh = R.randint(56, 82)
        if si == 0 and slot is None and x > bx0 + 20:  # empty slot, near the robot
            slot = (x, bottom - 84, x + 44, bottom - 4)
            c.dashed(YELLOW, [(x, bottom - 4), (x, bottom - 84), (x + 44, bottom - 84), (x + 44, bottom - 4)], dash=9, gap=7, w=3)
            x += 52; continue
        col = BLUE if R.random() < 0.18 else WHITE
        c.rect(col, x, bottom - bh, x + bw, bottom - 4, w=3.2, a=190)
        if R.random() < 0.35:
            c.hatch(col, x + 2, bottom - bh + 2, x + bw - 2, bottom - 6, gap=7, w=1.6, a=110)
        x += bw + R.randint(4, 9)
c.hatch(WHITE, bx1 - 60, by0 + 4, bx1 - 4, by1 - 4, gap=11, a=70)            # shadow side of cabinet
nodes = [(bx0 + 74, by0 - 26), ((bx0 + bx1) / 2, by0 - 40), (bx1 - 74, by0 - 26)]
for n in nodes:
    c.circle(BLUE, n[0], n[1], 8, seg=10, w=3)
c.line(BLUE, nodes[0], nodes[1], w=2.5, a=160); c.line(BLUE, nodes[1], nodes[2], w=2.5, a=160)

# ---- placement path: dashed arc from card into the slot, arrowhead at the slot ----
s0 = (card[1][0] + 8, card[1][1] + 30)
s1 = ((slot[0] + slot[2]) / 2, slot[1] - 10)
c.dashed(WHITE, arc_pts(s0, s1, -60), dash=14, gap=10, w=3.5, a=200)
c.line(WHITE, s1, (s1[0] - 18, s1[1] - 16), w=4); c.line(WHITE, s1, (s1[0] + 14, s1[1] - 20), w=4)

# ---- one handwritten label with a leader line ----
c.text(WHITE, (360, 880), "AI 助理", fS, a=210)
c.line(WHITE, (352, 896), (310, 870), w=3, a=170)

# ---- bottom ~22% calm: dust and eraser swipes only, then the chalk ledge ----
img = c.render(img)
img = dust(img)
d = ImageDraw.Draw(img)
d.rectangle([0, H - 34, W, H], fill=TRAY); d.line([0, H - 34, W, H - 34], fill=(120, 90, 62), width=3)
d.rounded_rectangle([780, H - 50, 870, H - 36], 6, fill=WHITE)
d.rounded_rectangle([890, H - 48, 950, H - 36], 6, fill=YELLOW)
img.save(OUT)
print(OUT)
