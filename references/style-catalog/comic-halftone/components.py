# Comic halftone component library (Python 3 + PIL only).
# Technique model: a two-layer "press" — a colour layer (Y/R/B process plates + paper)
# and a black (K) ink layer that always overprints. Everything is drawn at 2x and
# downsampled, so dots and tapered lines are anti-aliased like real print.
#
#   P = Page(1080, 1350)
#   m = P.mask(pts); P.fill(m, WHITE); P.tone(m, "B", 0.12); P.outline(pts, 6)
#   P.render().save("out.png")
#
# Import and call the component functions (robot, note_card, shelf3d, burst_number, ...).
import math, random, os
from PIL import Image, ImageDraw, ImageFont, ImageChops

SS = 2  # supersampling factor

# ---------- palette (process-ink look on newsprint) ----------
INK = (24, 20, 28)        # K plate, warm black
PAPER = (247, 240, 222)   # newsprint
WHITE = (255, 252, 243)   # "unprinted" highlight inside objects
RED = (221, 36, 42)       # process red (M+Y)
YELLOW = (255, 208, 30)   # process yellow
BLUE = (28, 122, 198)     # process blue (C + a little M)

# One fixed screen per plate for the whole page (classic plate angles), cell in px @1x.
CELL = 10
PLATES = {"Y": (YELLOW, 0.0), "R": (RED, 75.0), "B": (BLUE, 15.0), "K": (INK, 45.0)}

LIGHT_SHADOW = (0.6, 0.8)  # direction shadows fall (light from top-left)

FONT_CJK = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_SFX = "/System/Library/Fonts/Supplemental/Impact.ttf"

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------- geometry helpers ----------
def rot(p, c, deg):
    a = math.radians(deg)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def rot_pts(pts, c, deg):
    return [rot(p, c, deg) for p in pts]


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def bezier(pts, n=40):
    """Quadratic or cubic bezier sampled into n+1 points."""
    out = []
    for i in range(n + 1):
        t = i / n
        q = list(pts)
        while len(q) > 1:
            q = [lerp(q[k], q[k + 1], t) for k in range(len(q) - 1)]
        out.append(q[0])
    return out


def ellipse_pts(cx, cy, rx, ry, n=72, a0=0, a1=360):
    full = (a1 - a0) % 360 == 0
    k = n if full else n + 1
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(k)]


def rrect_pts(x0, y0, x1, y1, r, n=6):
    r = max(0.01, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    pts = []
    for cx, cy, a in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            t = math.radians(a + 90 * i / n)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def capsule_pts(p, q, r, n=12):
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    pts = []
    for i in range(n + 1):
        t = ang - math.pi / 2 + math.pi * i / n
        pts.append((q[0] + r * math.cos(t), q[1] + r * math.sin(t)))
    for i in range(n + 1):
        t = ang + math.pi / 2 + math.pi * i / n
        pts.append((p[0] + r * math.cos(t), p[1] + r * math.sin(t)))
    return pts


def star_pts(cx, cy, R, ratio=0.62, n=16, seed=1, jitter=0.18, rot0=0.0, ry=None):
    rng = random.Random(seed)
    ry = ry or R
    pts = []
    for i in range(n * 2):
        a = math.radians(rot0 + 180.0 * i / n + rng.uniform(-4, 4))
        if i % 2 == 0:
            k = 1 - rng.uniform(0, jitter)
        else:
            k = ratio * (1 - rng.uniform(0, jitter * 0.6))
        pts.append((cx + R * k * math.cos(a), cy + ry * k * math.sin(a)))
    return pts


def homography(src, dst):
    """3x3 projective map from 4 src points to 4 dst points; returns f(x,y)->(x',y')."""
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    n = 8
    M = [A[i] + [b[i]] for i in range(n)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [M[r][k] - f * M[c][k] for k in range(n + 1)]
    h = [M[i][n] / M[i][i] for i in range(n)] + [1.0]

    def f(x, y):
        w = h[6] * x + h[7] * y + h[8]
        return ((h[0] * x + h[1] * y + h[2]) / w, (h[3] * x + h[4] * y + h[5]) / w)
    return f


class Cam:
    """Tiny perspective camera. World: X right, Y up, Z away from viewer."""

    def __init__(self, cx, cy, f=900, yaw=0.0, pitch=0.0, dist=800, roll=0.0, target=(0, 0, 0)):
        self.cx, self.cy, self.f, self.dist, self.roll = cx, cy, f, dist, roll
        self.cyw, self.syw = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        self.cp, self.sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        self.t = target

    def view(self, X, Y, Z):
        X, Y, Z = X - self.t[0], Y - self.t[1], Z - self.t[2]
        x = X * self.cyw - Z * self.syw
        z = X * self.syw + Z * self.cyw
        y = Y * self.cp - z * self.sp
        z = Y * self.sp + z * self.cp
        return x, y, z + self.dist

    def __call__(self, X, Y, Z):
        x, y, z = self.view(X, Y, Z)
        z = max(z, 1.0)
        p = (self.cx + self.f * x / z, self.cy - self.f * y / z)
        return rot(p, (self.cx, self.cy), self.roll) if self.roll else p


def poly_area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) / 2.0


# ---------- masks ----------
class Mask:
    """L-mode coverage in physical (2x) pixels with an origin offset."""

    def __init__(self, im, ox, oy):
        self.im, self.ox, self.oy = im, int(ox), int(oy)

    def _aligned(self, o):
        t = Image.new("L", self.im.size, 0)
        t.paste(o.im, (o.ox - self.ox, o.oy - self.oy))
        return t

    def inter(self, o):
        return Mask(ImageChops.multiply(self.im, self._aligned(o)), self.ox, self.oy)

    def minus(self, o):
        return Mask(ImageChops.subtract(self.im, self._aligned(o)), self.ox, self.oy)

    def union(self, o):
        x0, y0 = min(self.ox, o.ox), min(self.oy, o.oy)
        x1 = max(self.ox + self.im.width, o.ox + o.im.width)
        y1 = max(self.oy + self.im.height, o.oy + o.im.height)
        a = Image.new("L", (x1 - x0, y1 - y0), 0)
        b = Image.new("L", (x1 - x0, y1 - y0), 0)
        a.paste(self.im, (self.ox - x0, self.oy - y0))
        b.paste(o.im, (o.ox - x0, o.oy - y0))
        return Mask(ImageChops.lighter(a, b), x0, y0)

    def shifted(self, dx, dy):
        return Mask(self.im, self.ox + round(dx * SS), self.oy + round(dy * SS))

    def rim(self, k, d=LIGHT_SHADOW):
        """Shadow crescent: the part of the shape not covered by itself moved toward the light."""
        return self.minus(self.shifted(-k * d[0], -k * d[1]))

    def bbox(self):
        b = self.im.getbbox()
        if not b:
            return None
        return ((b[0] + self.ox) / SS, (b[1] + self.oy) / SS, (b[2] + self.ox) / SS, (b[3] + self.oy) / SS)


# ---------- the page ----------
class Page:
    def __init__(self, w, h, bg=PAPER, misreg=(1.3, 0.9), seed=7):
        self.w, self.h, self.bg = w, h, bg
        self.col = Image.new("RGB", (w * SS, h * SS), bg)
        self.ink = Image.new("L", (w * SS, h * SS), 0)
        self.misreg = misreg
        self.rng = random.Random(seed)

    # -- mask builders (all coordinates logical, 1x) --
    def mask(self, *polys, holes=(), pad=6):
        allp = [p for poly in polys for p in poly]
        xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
        x0, y0 = int((min(xs) - pad) * SS), int((min(ys) - pad) * SS)
        x1, y1 = int((max(xs) + pad) * SS) + 1, int((max(ys) + pad) * SS) + 1
        im = Image.new("L", (max(1, x1 - x0), max(1, y1 - y0)), 0)
        d = ImageDraw.Draw(im)
        for poly in polys:
            d.polygon([(p[0] * SS - x0, p[1] * SS - y0) for p in poly], fill=255)
        for poly in holes:
            d.polygon([(p[0] * SS - x0, p[1] * SS - y0) for p in poly], fill=0)
        return Mask(im, x0, y0)

    def rect_mask(self, x0, y0, x1, y1):
        return self.mask([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def full_mask(self):
        return Mask(Image.new("L", self.col.size, 255), 0, 0)

    def _box(self, m):
        return (m.ox, m.oy, m.ox + m.im.width, m.oy + m.im.height)

    # -- painting --
    def fill(self, m, color):
        """Opaque colour fill; also knocks out any ink underneath (painter's order)."""
        box = self._box(m)
        self.col.paste(color, box, m.im)
        self.ink.paste(0, box, m.im)

    def ink_fill(self, m, clip=None):
        if clip is not None:
            m = m.inter(clip)
        self.ink.paste(255, self._box(m), m.im)

    def tone(self, m, plate, level, cell=CELL, jitter=0.04, rmax=None):
        """Ben-Day dots on the plate's fixed page-wide screen. level = ink coverage 0..0.9
        (float or f(x, y) in logical px). Dot radius r = cell*sqrt(level/pi)."""
        color, ang = PLATES[plate]
        bb = m.bbox()
        if not bb:
            return
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        corners = [(bb[0], bb[1]), (bb[2], bb[1]), (bb[0], bb[3]), (bb[2], bb[3])]
        iu = [(x * ux + y * uy) / cell for x, y in corners]
        jv = [(x * vx + y * vy) / cell for x, y in corners]
        layer = Image.new("L", m.im.size, 0)
        d = ImageDraw.Draw(layer)
        rng = self.rng
        for i in range(int(math.floor(min(iu))) - 1, int(math.ceil(max(iu))) + 2):
            for j in range(int(math.floor(min(jv))) - 1, int(math.ceil(max(jv))) + 2):
                x = (i * ux + j * vx) * cell
                y = (i * uy + j * vy) * cell
                if x < bb[0] - cell or x > bb[2] + cell or y < bb[1] - cell or y > bb[3] + cell:
                    continue
                lv = level(x, y) if callable(level) else level
                if lv <= 0.003:
                    continue
                r = cell * math.sqrt(min(lv, 0.95) / math.pi) * (1 + rng.uniform(-jitter, jitter))
                if rmax:
                    r = min(r, rmax)
                rs = r * SS
                if rs < 0.7:
                    continue
                px, py = x * SS - m.ox, y * SS - m.oy
                d.ellipse([px - rs, py - rs, px + rs, py + rs], fill=255)
        layer = ImageChops.multiply(layer, m.im)
        if plate == "K":
            self.ink.paste(255, self._box(m), layer)
        else:
            self.col.paste(color, self._box(m), layer)

    # -- ink lines --
    def _strip(self, pts, widths, closed):
        n = len(pts)
        allw = max(widths)
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0, y0 = int((min(xs) - allw) * SS) - 2, int((min(ys) - allw) * SS) - 2
        x1, y1 = int((max(xs) + allw) * SS) + 3, int((max(ys) + allw) * SS) + 3
        im = Image.new("L", (max(1, x1 - x0), max(1, y1 - y0)), 0)
        d = ImageDraw.Draw(im)
        P = [(p[0] * SS - x0, p[1] * SS - y0) for p in pts]
        Wd = [w * SS / 2 for w in widths]
        segs = n if closed else n - 1
        for i in range(segs):
            a, b = P[i], P[(i + 1) % n]
            wa, wb = Wd[i], Wd[(i + 1) % n]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            if L < 1e-6:
                continue
            nx, ny = -dy / L, dx / L
            d.polygon([(a[0] + nx * wa, a[1] + ny * wa), (b[0] + nx * wb, b[1] + ny * wb),
                       (b[0] - nx * wb, b[1] - ny * wb), (a[0] - nx * wa, a[1] - ny * wa)], fill=255)
        for p, w in zip(P, Wd):
            if w > 0.5:
                d.ellipse([p[0] - w, p[1] - w, p[0] + w, p[1] + w], fill=255)
        return Mask(im, x0, y0)

    def outline(self, pts, w, closed=True, weight=1.0, clip=None):
        """Weighted contour: edges facing away from the light get up to (1+weight)x thicker,
        lit edges thin down to ~0.6x — the brush 'thick-thin' of Silver-age inking."""
        n = len(pts)
        if closed:
            sgn = 1 if poly_area(pts) > 0 else -1
            fe = []
            for i in range(n):
                a, b = pts[i], pts[(i + 1) % n]
                dx, dy = b[0] - a[0], b[1] - a[1]
                L = math.hypot(dx, dy) or 1
                nx, ny = sgn * dy / L, -sgn * dx / L
                fe.append(0.62 + weight * max(0.0, nx * LIGHT_SHADOW[0] + ny * LIGHT_SHADOW[1]))
            widths = [w * (fe[i - 1] + fe[i]) / 2 for i in range(n)]
        else:
            widths = [w] * n
        self.ink_fill(self._strip(pts, widths, closed), clip)

    def stroke(self, pts, w, taper=(0.35, 0.35), wmin=0.12, clip=None):
        """Tapered brush stroke along a polyline (swell in the middle, points at the ends)."""
        if len(pts) < 2:
            return
        if len(pts) < 16:  # resample so the width profile has a middle to swell into
            dense = []
            for i in range(len(pts) - 1):
                for k in range(8):
                    dense.append(lerp(pts[i], pts[i + 1], k / 8))
            dense.append(pts[-1])
            pts = dense
        acc = [0.0]
        for i in range(1, len(pts)):
            acc.append(acc[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
        tot = acc[-1] or 1
        widths = []
        for s in acc:
            t = s / tot
            k = 1.0
            if taper[0] > 0:
                k = min(k, t / taper[0])
            if taper[1] > 0:
                k = min(k, (1 - t) / taper[1])
            k = math.sin(max(0.0, min(1.0, k)) * math.pi / 2)
            widths.append(w * max(wmin, k))
        self.ink_fill(self._strip(pts, widths, False), clip)

    def line(self, pts, w, clip=None):
        self.ink_fill(self._strip(pts, [w] * len(pts), False), clip)

    # -- text --
    def font(self, path, size, index=0):
        return ImageFont.truetype(path, int(size * SS), index=index)

    def text_mask(self, xy, s, font, anchor="mm", stroke=0):
        bb = font.getbbox(s, anchor=anchor, stroke_width=int(stroke * SS))
        pad = 4
        w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
        im = Image.new("L", (max(1, w), max(1, h)), 0)
        ImageDraw.Draw(im).text((-bb[0] + pad, -bb[1] + pad), s, font=font, fill=255, anchor=anchor,
                                stroke_width=int(stroke * SS), stroke_fill=255)
        return Mask(im, xy[0] * SS + bb[0] - pad, xy[1] * SS + bb[1] - pad)

    def text(self, xy, s, font, fill=INK, stroke=0, anchor="mm", extrude=None):
        """Ink text, or colour text with an ink outline (+ optional ink block extrusion)."""
        if "STHeiti" in str(getattr(font, "path", "")):
            CJK_USED.append(s)
        if fill == INK:
            self.ink_fill(self.text_mask(xy, s, font, anchor, stroke))
            return
        if stroke:
            om = self.text_mask(xy, s, font, anchor, stroke)
            if extrude:
                steps = max(1, int(math.hypot(*extrude) * SS / 1.5))
                for k in range(1, steps + 1):
                    self.ink_fill(om.shifted(extrude[0] * k / steps, extrude[1] * k / steps))
            self.ink_fill(om)
        self.fill(self.text_mask(xy, s, font, anchor, 0), fill)

    # -- output --
    def render(self, grain=10):
        dx, dy = round(self.misreg[0] * SS), round(self.misreg[1] * SS)
        col = Image.new("RGB", self.col.size, self.bg)
        col.paste(self.col, (dx, dy))
        out = Image.composite(Image.new("RGB", self.col.size, INK), col, self.ink)
        out = out.resize((self.w, self.h), Image.LANCZOS)
        if grain:
            n = Image.effect_noise((self.w, self.h), grain).convert("RGB")
            out = ImageChops.add(ImageChops.subtract(out, Image.new("RGB", out.size, (6, 6, 6))),
                                 n.point(lambda v: max(0, v - 128) // 10))
        return out


def check_glyphs(text, path=FONT_CJK, size=40):
    """Return the characters the font cannot draw (compares against the .notdef box)."""
    f = ImageFont.truetype(path, size)

    def bm(ch):
        im = Image.new("L", (size * 2, size * 2), 0)
        ImageDraw.Draw(im).text((size // 2, size // 2), ch, font=f, fill=255)
        return im.tobytes()
    tofu = bm("\U000F0000")
    bad = []
    for ch in sorted(set(text)):
        if ch.isspace() or ord(ch) < 128:
            continue
        b = bm(ch)
        if b == tofu or not any(b):
            bad.append(ch)
    return bad


CJK_USED = []  # every string drawn with the CJK font is logged here for glyph checks


# ---------- shading recipes ----------
def shade(P, m, color, k=10, deep=True):
    """Flat colour + one shadow crescent. Shadow plate depends on the base colour:
    white -> blue dots, yellow -> red dots (orange), red/blue -> black dots."""
    P.fill(m, color)
    r = m.rim(k)
    if color == WHITE:
        P.tone(r, "B", 0.42)
    elif color == YELLOW:
        P.tone(r, "R", 0.42)
    else:
        P.tone(r, "K", 0.38)
    if deep and k >= 8:
        P.tone(m.rim(k * 0.4), "K", 0.30)


def metal(P, m, k=10):
    """Robot metal: unprinted paper-white, blue-dot crescent, black-dot core shadow."""
    P.fill(m, WHITE)
    P.tone(m.rim(k), "B", 0.5)
    if k >= 6:
        P.tone(m.rim(k * 0.42), "K", 0.34)


def part(P, pts, color=None, w=5, k=10, kind="metal"):
    m = P.mask(pts)
    if kind == "metal":
        metal(P, m, k)
    elif kind == "flat":
        P.fill(m, color)
    else:
        shade(P, m, color, k)
    P.outline(pts, w)
    return m


def hatch(P, m, spacing=7, angle=45, w=2.2, cross=False, clip_extra=None):
    """Brush cross-hatching clipped to a mask; each line tapers at both ends."""
    bb = m.bbox()
    if not bb:
        return
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    R = math.hypot(bb[2] - bb[0], bb[3] - bb[1]) / 2 + spacing
    for ang in ([angle, angle + 90] if cross else [angle]):
        a = math.radians(ang)
        ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        t = -R
        while t <= R:
            p0 = (cx + vx * t - ux * R, cy + vy * t - uy * R)
            p1 = (cx + vx * t + ux * R, cy + vy * t + uy * R)
            P.stroke([p0, lerp(p0, p1, 0.5), p1], w, taper=(0.5, 0.5), wmin=0.4,
                     clip=m if clip_extra is None else m.inter(clip_extra))
            t += spacing


# ---------- page furniture ----------
def panel(P, pts, w=5.0, bg=WHITE):
    """Panel = flat paper fill + a ruled border of constant width (panels are ruled, not brushed)."""
    m = P.mask(pts)
    P.fill(m, bg)
    return m


def panel_border(P, pts, w=5.0):
    P.line(list(pts) + [pts[0], pts[1]], w)


def focus_lines(P, clip, cx, cy, r_in, n=140, w=9, seed=3, r_out=None, ry_scale=1.0):
    """Radial 'concentration' lines: tapered wedges pointing at (cx, cy), clipped to a panel."""
    rng = random.Random(seed)
    bb = clip.bbox()
    r_out = r_out or math.hypot(max(abs(bb[0] - cx), abs(bb[2] - cx)), max(abs(bb[1] - cy), abs(bb[3] - cy))) + 20
    for i in range(n):
        a = 2 * math.pi * (i + rng.uniform(-0.4, 0.4)) / n
        r0 = r_in * rng.uniform(1.0, 1.45)
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0 * ry_scale)
        p1 = (cx + math.cos(a) * r_out, cy + math.sin(a) * r_out * ry_scale)
        P.stroke([p0, p1], w * rng.uniform(0.35, 1.0), taper=(1.0, 0.0), wmin=0.02, clip=clip)


def speed_lines(P, clip, x0, y0, x1, y1, ang=0, n=14, w=4, seed=5, gap=0.0):
    """Parallel motion lines in a band; each tapers toward the tail; lengths vary."""
    rng = random.Random(seed)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    for i in range(n):
        t = (i + rng.uniform(0, 0.8)) / n
        y = y0 + (y1 - y0) * t
        L = (x1 - x0) * rng.uniform(0.35, 1.0)
        xs = x1 - rng.uniform(0, gap) - L
        p0 = (xs, y); p1 = (xs + L, y)
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        p0, p1 = rot(p0, c, ang), rot(p1, c, ang)
        P.stroke([p0, p1], w * rng.uniform(0.5, 1.0), taper=(1.0, 0.08), wmin=0.03, clip=clip)


def impact_marks(P, cx, cy, r0, r1, n=7, a0=0, a1=360, w=5, seed=2):
    rng = random.Random(seed)
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * (i + 0.5) / n + rng.uniform(-6, 6))
        rr0 = r0 * rng.uniform(0.9, 1.1); rr1 = r1 * rng.uniform(0.8, 1.15)
        P.stroke([(cx + math.cos(a) * rr0, cy + math.sin(a) * rr0),
                  (cx + math.cos(a) * rr1, cy + math.sin(a) * rr1)], w, taper=(0.0, 1.0), wmin=0.1)


def sparkle(P, cx, cy, r, w=4, color=YELLOW):
    pts = []
    for i in range(8):
        a = math.radians(45 * i - 90)
        rr = r if i % 2 == 0 else r * 0.28
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    m = P.mask(pts)
    P.fill(m, color)
    P.outline(pts, w, weight=0.4)


# ---------- lettering ----------
def sfx(P, text, x, y, size, color=YELLOW, shade_plate="R", angle=-8, extrude=(5, 6), grow=0.10,
        stroke=6, spacing=1.0, font=FONT_SFX):
    """Sound-effect lettering for Latin/numbers: per-glyph rotation and step-up scaling,
    ink outline, solid ink block extrusion, flat fill with a dot gradient on the lower half."""
    glyphs = []
    n = len(text)
    for i, ch in enumerate(text):
        s = size * (1 + grow * (i - (n - 1) / 2) / max(1, n - 1) * 2)
        glyphs.append((ch, P.font(font, s), s))
    widths = [f.getlength(ch) / SS * spacing for ch, f, s in glyphs]
    total = sum(widths)
    cxs, acc = [], -total / 2
    for wdt in widths:
        cxs.append(acc + wdt / 2); acc += wdt
    ca = math.radians(angle)
    placed = []
    for (ch, f, s), cx in zip(glyphs, cxs):
        gx, gy = x + cx * math.cos(ca), y + cx * math.sin(ca)
        ga = angle + P.rng.uniform(-4, 4)
        om = _rot_text_mask(P, ch, f, (gx, gy), ga, stroke)
        fm = _rot_text_mask(P, ch, f, (gx, gy), ga, 0)
        placed.append((om, fm, s, gy))
    steps = max(1, int(math.hypot(*extrude) * SS / 1.5))
    for om, fm, s, gy in placed:
        for k in range(1, steps + 1):
            P.ink_fill(om.shifted(extrude[0] * k / steps, extrude[1] * k / steps))
    for om, fm, s, gy in placed:
        P.ink_fill(om)
    for om, fm, s, gy in placed:
        P.fill(fm, color)
        if shade_plate:
            bb = fm.bbox()
            top, bot = bb[1], bb[3]
            P.tone(fm, shade_plate, lambda xx, yy, top=top, bot=bot: max(0.0, (yy - top) / (bot - top) - 0.45) * 1.1)
    return placed


def _rot_text_mask(P, ch, f, center, ang, stroke):
    sw = int(stroke * SS)
    bb = f.getbbox(ch, anchor="mm", stroke_width=sw)
    pad = 6
    im = Image.new("L", (bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2), 0)
    ImageDraw.Draw(im).text((-bb[0] + pad, -bb[1] + pad), ch, font=f, fill=255, anchor="mm",
                            stroke_width=sw, stroke_fill=255)
    cx0, cy0 = -bb[0] + pad, -bb[1] + pad  # glyph anchor inside im
    im2 = im.rotate(-ang, resample=Image.BICUBIC, expand=True, center=(cx0, cy0))
    # after expand the anchor moves; recompute by rotating the anchor offset
    w, h = im.size
    W2, H2 = im2.size
    ax, ay = rot((cx0, cy0), (w / 2, h / 2), ang)
    ax += (W2 - w) / 2; ay += (H2 - h) / 2
    return Mask(im2, center[0] * SS - ax, center[1] * SS - ay)


def title_lettering(P, x, y, s, size, color=RED, stroke=7, extrude=(6, 7), anchor="lm", font=FONT_CJK):
    f = P.font(font, size)
    P.text((x, y), s, f, fill=color, stroke=stroke, anchor=anchor, extrude=extrude)


def caption_box(P, x0, y0, x1, text, size=30, color=YELLOW, w=4, pad=16, line_gap=1.35):
    """Narrative caption: yellow rectangle, ruled border, ink text, wrapped by width."""
    f = P.font(FONT_CJK, size)
    lines, cur = [], ""
    maxw = (x1 - x0 - pad * 2) * SS
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if f.getlength(cur + ch) > maxw:
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    h = pad * 2 + size * line_gap * len(lines) - size * (line_gap - 1)
    pts = [(x0, y0), (x1, y0), (x1, y0 + h), (x0, y0 + h)]
    m = P.mask(pts)
    P.fill(m, color)
    panel_border(P, pts, w)
    for i, ln in enumerate(lines):
        P.text((x0 + pad, y0 + pad + size / 2 + i * size * line_gap), ln, f, anchor="lm")
    return y0 + h


def chapter_tag(P, x, y, num="01", label="章節", size=30, w=4):
    """Chapter tag: red block with white Impact numeral + paper block with ink label."""
    fn = P.font(FONT_SFX, size * 1.15)
    fl = P.font(FONT_CJK, size)
    nw = fn.getlength(num) / SS + 26
    lw = fl.getlength(label) / SS + 30
    h = size * 1.6
    a = [(x, y), (x + nw, y), (x + nw, y + h), (x, y + h)]
    b = [(x + nw, y), (x + nw + lw, y), (x + nw + lw, y + h), (x + nw, y + h)]
    P.ink_fill(P.mask([(x + 6, y + 6), (x + nw + lw + 6, y + 6), (x + nw + lw + 6, y + h + 6), (x + 6, y + h + 6)]))
    P.fill(P.mask(a), RED)
    P.fill(P.mask(b), WHITE)
    P.text((x + nw / 2, y + h / 2), num, fn, fill=WHITE)
    P.text((x + nw + lw / 2, y + h / 2), label, fl)
    panel_border(P, a, w); panel_border(P, b, w)
    return x + nw + lw


def balloon(P, box, tail, w=5, color=WHITE, spread=0.22):
    """Speech balloon: ellipse with the tail spliced into the same contour (one outline)."""
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    a = math.atan2((tail[1] - cy) / ry, (tail[0] - cx) / rx)
    pts, done = [], False
    for i in range(96):
        t = a + spread + (2 * math.pi - 2 * spread) * i / 95
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    pts.append(tail)
    P.fill(P.mask(pts), color)
    P.outline(pts, w, weight=0.6)
    return pts


# ---------- objects ----------
def burst(P, cx, cy, R, seed=4, n=16, layers=(RED, YELLOW), ry=None, w=7):
    """Explosion balloon: stacked jagged stars (red rim, yellow core) with an orange dot glow."""
    ry = ry or R
    out = star_pts(cx, cy, R, 0.66, n, seed, 0.2, ry=ry)
    m = P.mask(out)
    P.fill(m, layers[0])
    if layers[0] != WHITE:  # a white SFX balloon stays clean
        P.tone(m.rim(10), "K", 0.32)
    P.outline(out, w)
    inner = star_pts(cx, cy, R * 0.8, 0.74, n + 2, seed + 9, 0.14, rot0=7, ry=ry * 0.8)
    mi = P.mask(inner)
    P.fill(mi, layers[1])
    if layers[1] == YELLOW:
        P.tone(mi, "R", lambda x, y: max(0.0, math.hypot((x - cx) / R, (y - cy) / ry) - 0.58) * 1.6)
    P.outline(inner, w * 0.55, weight=0.3)
    return mi


def burst_number(P, cx, cy, R, num="61", unit="%", size=None, seed=4, ry=None):
    burst(P, cx, cy, R, seed=seed, ry=ry)
    size = size or R * 0.78
    f = P.font(FONT_SFX, size)
    fu = P.font(FONT_SFX, size * 0.55)
    nw = f.getlength(num) / SS
    uw = fu.getlength(unit) / SS
    x0 = cx - (nw + uw + size * 0.08) / 2
    ex = (size * 0.05, size * 0.065)
    P.text((x0, cy + size * 0.04), num, f, fill=RED, stroke=size * 0.06, anchor="lm", extrude=ex)
    P.text((x0 + nw + size * 0.08, cy - size * 0.12), unit, fu, fill=RED, stroke=size * 0.05, anchor="lm",
           extrude=(ex[0] * 0.7, ex[1] * 0.7))


def check_mark(P, cx, cy, s=1.0, color=BLUE, w=5):
    """Rounded badge + brush check (thick-thin)."""
    pts = rrect_pts(cx - 40 * s, cy - 40 * s, cx + 40 * s, cy + 40 * s, 14 * s)
    m = P.mask(pts)
    P.fill(m, color)
    P.tone(m.rim(9 * s), "K", 0.36)
    P.outline(pts, w * s)
    path = bezier([(cx - 22 * s, cy + 0 * s), (cx - 10 * s, cy + 8 * s), (cx - 6 * s, cy + 20 * s)], 10) + \
        bezier([(cx - 6 * s, cy + 20 * s), (cx + 6 * s, cy - 6 * s), (cx + 26 * s, cy - 24 * s)], 16)[1:]
    P.stroke([(p[0] + 3 * s, p[1] + 4 * s) for p in path], 15 * s, taper=(0.15, 0.6))
    m2 = P._strip(path, [w * s * 2.6 * max(0.25, min(1, (i + 1) / 6, (len(path) - i) / 12)) for i in range(len(path))], False)
    P.fill(m2, WHITE)


def cross_mark(P, cx, cy, s=1.0, color=RED, w=5):
    pts = rrect_pts(cx - 40 * s, cy - 40 * s, cx + 40 * s, cy + 40 * s, 14 * s)
    m = P.mask(pts)
    P.fill(m, color)
    P.tone(m.rim(9 * s), "K", 0.36)
    P.outline(pts, w * s)
    for a, b in (((-20, -20), (20, 20)), ((20, -20), (-20, 20))):
        p0 = (cx + a[0] * s, cy + a[1] * s); p1 = (cx + b[0] * s, cy + b[1] * s)
        P.stroke([(p0[0] + 3 * s, p0[1] + 4 * s), (p1[0] + 3 * s, p1[1] + 4 * s)], 15 * s, taper=(0.2, 0.2), wmin=0.4)
        m2 = P._strip([p0, lerp(p0, p1, 0.5), p1], [w * s * 1.2, w * s * 2.6, w * s * 1.2], False)
        P.fill(m2, WHITE)


def arrow(P, path, width=34, head=1.9, color=RED, w=5, extrude=(6, 7)):
    """Chunky comic arrow along a (bezier) path with an ink block extrusion."""
    n = len(path)
    L = [0.0]
    for i in range(1, n):
        L.append(L[-1] + math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]))
    hl = width * head * 0.9
    body = [p for p, s in zip(path, L) if s <= L[-1] - hl]
    tip = path[-1]
    base = body[-1]
    ang = math.atan2(tip[1] - base[1], tip[0] - base[0])
    left, right = [], []
    for i, p in enumerate(body):
        q = body[min(i + 1, len(body) - 1)] if i < len(body) - 1 else p
        pp = body[i - 1] if i > 0 else p
        a = math.atan2(q[1] - pp[1], q[0] - pp[0]) if q != pp else ang
        ww = width / 2 * (0.55 + 0.45 * i / max(1, len(body) - 1))
        left.append((p[0] - math.sin(a) * ww, p[1] + math.cos(a) * ww))
        right.append((p[0] + math.sin(a) * ww, p[1] - math.cos(a) * ww))
    hw = width * head / 2
    hb1 = (base[0] - math.sin(ang) * hw, base[1] + math.cos(ang) * hw)
    hb2 = (base[0] + math.sin(ang) * hw, base[1] - math.cos(ang) * hw)
    pts = left + [hb1, tip, hb2] + right[::-1]
    m = P.mask(pts)
    steps = max(1, int(math.hypot(*extrude) * SS / 1.5))
    for k in range(1, steps + 1):
        P.ink_fill(m.shifted(extrude[0] * k / steps, extrude[1] * k / steps))
    P.fill(m, color)
    P.tone(m.rim(8), "K", 0.3)
    P.outline(pts, w, weight=0.5)


def note_card(P, cx, cy, w=200, h=130, angle=-8, state="plain", lw=5, xf=None):
    """Ruled index card (red header rule, blue ruled lines, ink scribbles), folded corner.
    state: plain | wrong (red X stamp) | verified (blue check stamp)."""
    x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
    fold = min(w, h) * 0.18
    local = [(x0, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1), (x0, y1)]

    def T(p):
        q = rot(p, (0, 0), angle)
        q = (q[0] + cx, q[1] + cy)
        return xf(*q) if xf else q
    body = [T(p) for p in local]
    m = P.mask(body)
    P.fill(m, WHITE)
    P.tone(m.rim(max(5, h * 0.07)), "B", 0.38)
    # ruled lines
    for i in range(4):
        yy = y0 + h * 0.36 + i * h * 0.15
        P.line([T((x0 + 4, yy)), T((x1 - 4, yy))], max(1.4, lw * 0.32), clip=m)
        # paint the rule blue: knock the ink back out and lay colour (rules are printed in blue)
    P.ink.paste(0, P._box(m), m.im)
    for i in range(4):
        yy = y0 + h * 0.36 + i * h * 0.15
        rm = P._strip([T((x0 + 3, yy)), T((x1 - 3, yy))], [max(1.6, lw * 0.36)] * 2, False).inter(m)
        P.fill(rm, BLUE)
    hm = P._strip([T((x0 + 3, y0 + h * 0.2)), T((x1 - fold * 0.7, y0 + h * 0.2))], [max(2.2, lw * 0.5)] * 2, False).inter(m)
    P.fill(hm, RED)
    # handwriting scribbles in ink
    rng = random.Random(int(cx * 7 + cy))
    for i in range(3):
        yy = y0 + h * 0.36 + i * h * 0.15 - h * 0.035
        xe = x0 + w * (0.82 if i < 2 else 0.5) * rng.uniform(0.85, 1.0)
        pts = []
        xx = x0 + w * 0.08
        while xx < xe:
            pts.append(T((xx, yy + math.sin(xx * 0.33) * h * 0.012)))
            xx += 4
        if len(pts) > 1:
            P.stroke(pts, max(1.6, lw * 0.45), taper=(0.08, 0.15), wmin=0.4)
    # folded corner
    fpts = [T((x1 - fold, y0)), T((x1 - fold, y0 + fold)), T((x1, y0 + fold))]
    fm = P.mask(fpts)
    P.fill(fm, WHITE)
    P.tone(fm, "B", 0.45)
    P.outline(fpts, lw * 0.7, weight=0.3)
    P.outline(body, lw)
    if state == "wrong":
        P.tone(m.rim(h * 0.12), "R", 0.4)
        s = h / 130
        c = T((w * 0.18, h * 0.12))
        for a, b in (((-24, -24), (24, 24)), ((24, -24), (-24, 24))):
            p0 = (c[0] + a[0] * s, c[1] + a[1] * s); p1 = (c[0] + b[0] * s, c[1] + b[1] * s)
            P.stroke([p0, lerp(p0, p1, 0.5), p1], 9 * s, taper=(0.2, 0.2), wmin=0.5)
            mm = P._strip([p0, lerp(p0, p1, 0.5), p1], [3 * s, 7 * s, 3 * s], False)
            P.fill(mm, RED)
    elif state == "verified":
        s = h / 130
        c = T((w * 0.24, h * 0.16))
        rr = 26 * s
        ring = ellipse_pts(c[0], c[1], rr, rr, 48)
        rm = P.mask(ring)
        P.fill(rm, BLUE)
        P.outline(ring, lw * 0.8, weight=0.4)
        path = [(c[0] - 12 * s, c[1]), (c[0] - 3 * s, c[1] + 10 * s), (c[0] + 14 * s, c[1] - 11 * s)]
        mm = P._strip(path, [3 * s, 7 * s, 3.4 * s], False)
        P.fill(mm, WHITE)
    return body


def database(P, cx, top, rx=80, ry=24, seg_h=58, segs=3, w=5):
    """Stacked-cylinder database tower: blue sides with black-dot shadow, tinted tops,
    a knocked-out highlight stripe and yellow status lights."""
    for i in reversed(range(segs)):
        y = top + i * (seg_h + 6)
        side = ellipse_pts(cx, y + seg_h, rx, ry, 36, 0, 180) + [(cx - rx, y), (cx + rx, y)][::-1][::-1]
        side = [(cx + rx, y)] + ellipse_pts(cx, y + seg_h, rx, ry, 36, 0, 180) + [(cx - rx, y)]
        m = P.mask(side)
        P.fill(m, BLUE)
        P.tone(P.mask([(cx + rx * 0.35, y - ry), (cx + rx + 4, y - ry), (cx + rx + 4, y + seg_h + ry + 4),
                       (cx + rx * 0.35, y + seg_h + ry + 4)]).inter(m), "K", 0.4)
        hl = P.mask([(cx - rx * 0.72, y + 6), (cx - rx * 0.56, y + 6), (cx - rx * 0.56, y + seg_h + ry * 0.7),
                     (cx - rx * 0.72, y + seg_h + ry * 0.6)]).inter(m)
        P.fill(hl, WHITE)
        for k in range(3):
            lc = (cx + rx * 0.05 + k * 16, y + seg_h * 0.55 + ry * 0.55)
            lp = ellipse_pts(lc[0], lc[1], 4.5, 4.5, 16)
            P.fill(P.mask(lp), YELLOW if k < 2 else RED)
            P.outline(lp, 2.2, weight=0)
        P.outline(side, w)
        topp = ellipse_pts(cx, y, rx, ry, 60)
        tm = P.mask(topp)
        P.fill(tm, WHITE)
        P.tone(tm, "B", 0.32)
        P.outline(topp, w * (0.9 if i == 0 else 0.6))


def bar_chart(P, x0, y0, x1, y1, values, labels, hi=None, w=5, vmax=100):
    """Bar chart: thick axis, flat bars with black-dot shadow side, value labels in SFX type;
    only the highlighted bar is red, the rest blue-tint on white."""
    n = len(values)
    gap = (x1 - x0) / n
    bw = gap * 0.56
    fv = P.font(FONT_SFX, gap * 0.36)
    fl = P.font(FONT_CJK, gap * 0.22)
    for i, v in enumerate(values):
        bx = x0 + gap * i + (gap - bw) / 2
        by = y1 - (y1 - y0 - 40) * v / vmax
        pts = [(bx, by), (bx + bw, by), (bx + bw, y1), (bx, y1)]
        m = P.mask(pts)
        if i == hi:
            P.fill(m, RED)
            P.tone(P.rect_mask(bx + bw * 0.68, by, bx + bw + 4, y1).inter(m), "K", 0.42)
        else:
            P.fill(m, WHITE)
            P.tone(m, "B", 0.5)
            P.tone(P.rect_mask(bx + bw * 0.68, by, bx + bw + 4, y1).inter(m), "K", 0.32)
        P.outline(pts, w)
        if i == hi:
            P.text((bx + bw / 2, by - gap * 0.26), f"{v}%", fv, fill=YELLOW, stroke=4, extrude=(3, 4))
        else:
            P.text((bx + bw / 2, by - gap * 0.22), f"{v}%", P.font(FONT_SFX, gap * 0.26))
        P.text((bx + bw / 2, y1 + gap * 0.24), labels[i], fl)
    P.line([(x0 - 6, y1), (x1 + 6, y1)], w * 1.4)


# ---------- the robot (no face: visor only) ----------
POSES = {
    "idle":      dict(lean=0, tilt=0, af=(14, 10), ab=(-12, -8), lf=(4, 0), lb=(-4, 0), hf="fist", hb="fist"),
    "placing":   dict(lean=12, tilt=6, af=(78, 6), ab=(30, 70), lf=(26, -10), lb=(-22, -24), hf="palm", hb="fist"),
    "carrying":  dict(lean=8, tilt=-4, af=(112, 18), ab=(-30, -20), lf=(30, -16), lb=(-24, -30), hf="grip", hb="fist"),
    "thinking":  dict(lean=-4, tilt=-14, af=(100, 135), ab=(30, 80), lf=(6, 0), lb=(-8, 0), hf="fist", hb="fist"),
    "triumph":   dict(lean=-6, tilt=-8, af=(140, 22), ab=(-140, -22), lf=(18, 0), lb=(-18, 0), hf="fist", hb="fist"),
}


def robot(P, x, y, s=1.0, pose="idle", facing=1, w=None, extra=None):
    """Draw the agent robot standing on (x, y). Returns dict of key world points
    (hand_f, hand_b, head, visor). pose: name in POSES or a dict."""
    p = dict(POSES[pose]) if isinstance(pose, str) else dict(pose)
    if extra:
        p.update(extra)
    w = w or 5.5 * s
    k = 11 * s

    def L(u, v):  # local (u forward, v up) -> page
        return (x + facing * u * s, y - v * s)

    def dirv(deg):  # 0 = straight down, + = toward facing direction
        a = math.radians(deg)
        return (math.sin(a), -math.cos(a))

    # legs from hip (0,0) local first, then lift so lowest foot is on the ground
    TH, SH = 30, 28

    def leg(h, kn):
        hip = (0.0, 0.0)
        d1 = dirv(h); knee = (hip[0] + d1[0] * TH, hip[1] + d1[1] * TH)
        d2 = dirv(h + kn); ank = (knee[0] + d2[0] * SH, knee[1] + d2[1] * SH)
        return hip, knee, ank
    lf = leg(*p["lf"]); lb = leg(*p["lb"])
    lift = -min(lf[2][1], lb[2][1]) + 12
    hipv = lift
    lean = p["lean"]
    ax = (math.sin(math.radians(lean)), math.cos(math.radians(lean)))
    px_ = (math.cos(math.radians(lean)), -math.sin(math.radians(lean)))

    def T(a, b):  # torso frame: a across(+forward), b along spine from hip
        return L(a * px_[0] + b * ax[0], hipv + a * px_[1] + b * ax[1])

    def Tl(a, b):
        return (a * px_[0] + b * ax[0], hipv + a * px_[1] + b * ax[1])

    def LL(pt):
        return L(pt[0], pt[1] + hipv)

    sh_f = Tl(30, 84); sh_b = Tl(-30, 84)

    def arm(sh, ang, el):
        d1 = dirv(ang + lean); e = (sh[0] + d1[0] * 36, sh[1] + d1[1] * 36)
        d2 = dirv(ang + el + lean); hnd = (e[0] + d2[0] * 34, e[1] + d2[1] * 34)
        return sh, e, hnd, ang + el + lean

    af = arm(sh_f, *p["af"]); ab = arm(sh_b, *p["ab"])

    def limb(a, b, r):
        pts = capsule_pts(L(*a), L(*b), r * s)
        part(P, pts, w=w * 0.85, k=k * 0.7)

    def joint(c, r):
        pts = ellipse_pts(*L(*c), r * s, r * s, 28)
        part(P, pts, YELLOW, w=w * 0.75, k=k * 0.45, kind="shade")

    def hand(hp, ang, kind):
        c = L(*hp)
        d = dirv(ang)
        dd = (facing * d[0], -d[1])
        if kind == "palm":
            a = math.degrees(math.atan2(dd[1], dd[0]))
            loc = rrect_pts(-6 * s, -17 * s, 10 * s, 17 * s, 6 * s)
            pts = [(c[0] + q[0] * math.cos(math.radians(a)) - q[1] * math.sin(math.radians(a)),
                    c[1] + q[0] * math.sin(math.radians(a)) + q[1] * math.cos(math.radians(a))) for q in loc]
            part(P, pts, w=w * 0.85, k=k * 0.5)
            return (c[0] + dd[0] * 10 * s, c[1] + dd[1] * 10 * s)
        if kind == "grip":
            a = math.atan2(dd[1], dd[0])
            for off in (-0.5, 0.5):
                q = (c[0] + math.cos(a + off) * 18 * s, c[1] + math.sin(a + off) * 18 * s)
                part(P, capsule_pts(c, q, 5 * s), w=w * 0.7, k=k * 0.35)
            pts = ellipse_pts(c[0], c[1], 10 * s, 10 * s, 28)
            part(P, pts, w=w * 0.8, k=k * 0.45)
            return (c[0] + dd[0] * 16 * s, c[1] + dd[1] * 16 * s)
        pts = ellipse_pts(c[0], c[1], 12 * s, 12 * s, 28)
        part(P, pts, w=w * 0.85, k=k * 0.5)
        return c

    out = {}

    def draw_leg(lg):
        hip, knee, ank = lg
        limb((hip[0], hip[1] + hipv), (knee[0], knee[1] + hipv), 11)
        limb((knee[0], knee[1] + hipv), (ank[0], ank[1] + hipv), 10)
        joint((knee[0], knee[1] + hipv), 8)
        a0 = (ank[0] - 12, ank[1] + hipv + 4)
        boot = rrect_pts(0, 0, 1, 1, 0)
        bx, by = ank[0], ank[1] + hipv
        bl = [(bx - 14, by + 6), (bx + 10, by + 6), (bx + 26, by - 4), (bx + 26, by - 12), (bx - 16, by - 12)]
        bpts = [L(*q) for q in bl]
        part(P, bpts, RED, w=w * 0.85, k=k * 0.5, kind="shade")

    def draw_arm(a, kind, key):
        sh, e, hnd, ang = a
        limb(sh, e, 9)
        limb(e, hnd, 8.5)
        joint(e, 7.5)
        out[key] = hand(hnd, ang, kind)
        joint(sh, 10.5)

    draw_arm(ab, p["hb"], "hand_b")
    draw_leg(lb)
    draw_leg(lf)
    # pelvis
    pel = [T(-24, -6), T(24, -6), T(20, 14), T(-20, 14)]
    part(P, pel, w=w, k=k * 0.6)
    # torso: rounded, slightly tapered box
    tor = [T(a, b) for a, b in rrect_pts(-38, 10, 38, 96, 14)]
    tor = [T(a * (0.86 + 0.14 * (b - 10) / 86), b) for a, b in rrect_pts(-38, 10, 38, 96, 14)]
    tm = part(P, tor, w=w, k=k * 1.2)
    # chest plate + core light
    plate = [T(a, b) for a, b in rrect_pts(-20, 46, 20, 80, 7)]
    part(P, plate, YELLOW, w=w * 0.7, k=k * 0.5, kind="shade")
    core = ellipse_pts(*T(0, 63), 9 * s, 9 * s, 28)
    cm = P.mask(core); P.fill(cm, RED); P.tone(cm.rim(4 * s), "K", 0.4); P.outline(core, w * 0.6, weight=0.3)
    gl = ellipse_pts(*T(-3, 66), 2.6 * s, 2.6 * s, 12)
    P.fill(P.mask(gl), WHITE)
    for b in (22, 30, 38):
        P.stroke([T(-22, b), T(22, b)], w * 0.5, taper=(0.15, 0.15), wmin=0.3)
    # neck + head
    part(P, [T(-10, 94), T(10, 94), T(10, 106), T(-10, 106)], w=w * 0.8, k=k * 0.4)
    tilt = p["tilt"]
    hc = Tl(0, 130)

    def H(a, b):  # head frame
        ang = math.radians(tilt + lean)
        ha = (math.cos(ang), -math.sin(ang)); hb = (math.sin(ang), math.cos(ang))
        return L(hc[0] + a * ha[0] + b * hb[0], hc[1] + a * ha[1] + b * hb[1])
    # antenna
    P.stroke([H(6, 28), H(10, 46)], w * 0.8, taper=(0, 0), wmin=1)
    bulb = ellipse_pts(*H(10, 50), 7 * s, 7 * s, 24)
    bm = P.mask(bulb); P.fill(bm, RED); P.tone(bm.rim(3 * s), "K", 0.4); P.outline(bulb, w * 0.6, weight=0.3)
    # ear discs (side of head)
    for sa in (-1, 1):
        ear = [H(a, b) for a, b in rrect_pts(sa * 40 - 6, -12, sa * 40 + 6, 12, 5)]
        part(P, ear, YELLOW, w=w * 0.65, k=k * 0.3, kind="shade")
    head = [H(a, b) for a, b in rrect_pts(-38, -28, 38, 28, 15)]
    part(P, head, w=w * 1.05, k=k * 1.1)
    # visor: solid black band, blue scan stripe, knocked-out glints
    vis = [H(a, b) for a, b in rrect_pts(-30, -14, 32, 10, 10)]
    vm = P.mask(vis)
    P.ink_fill(vm)
    stripe = [H(a, b) for a, b in rrect_pts(-22, -6, 26, 2, 4)]
    sm = P.mask(stripe).inter(vm)
    P.fill(sm, BLUE)
    P.tone(sm, "K", 0.25)
    g1 = [H(-24, 6), H(-16, 6), H(-28, -12), H(-34, -12)] if facing == 1 else [H(-24, 6), H(-16, 6), H(-28, -12), H(-34, -12)]
    P.fill(P.mask(g1).inter(vm), WHITE)
    g2 = [H(-12, 6), H(-9, 6), H(-21, -12), H(-24, -12)]
    P.fill(P.mask(g2).inter(vm), WHITE)
    out["visor"] = H(0, -2)
    out["head"] = H(0, 0)
    draw_arm(af, p["hf"], "hand_f")
    out["chest"] = T(0, 63)
    out["top"] = H(10, 58)
    return out


def limb_arm(P, p, q, s=1.0, hand="palm", w=None):
    """Free-floating robot forearm (for close-ups): elbow joint at p, hand at q."""
    w = w or 5.5 * s
    k = 11 * s
    part(P, capsule_pts(p, q, 9 * s), w=w * 0.85, k=k * 0.7)
    jp = ellipse_pts(p[0], p[1], 8 * s, 8 * s, 28)
    part(P, jp, YELLOW, w=w * 0.75, k=k * 0.45, kind="shade")
    a = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
    loc = rrect_pts(-6 * s, -18 * s, 12 * s, 18 * s, 6 * s)
    pts = [rot((q[0] + u, q[1] + v), q, a) for u, v in loc]
    part(P, pts, w=w * 0.85, k=k * 0.5)


# ---------- knowledge base: bookshelf in 3D ----------
def make_books(n_rows, width, seed=11, gap=None, min_w=26, max_w=40, cols=None):
    rng = random.Random(seed)
    rows = []
    cols = cols or [RED, YELLOW, BLUE, WHITE, BLUE, RED, WHITE, YELLOW]
    for r in range(n_rows):
        x, books = 4, []
        while x < width - min_w - 4:
            bw = rng.uniform(min_w, max_w)
            if x + bw > width - 4:
                break
            if gap and gap[0] == r and len(books) == gap[1]:
                books.append(dict(x=x, w=gap[2], h=0, gap=True))
                x += gap[2] + 1
                continue
            books.append(dict(x=x, w=bw, h=rng.uniform(0.66, 0.92), c=rng.choice(cols), gap=False,
                              band=rng.random() < 0.7, dots=rng.random() < 0.12))
            x += bw + 1
        rows.append(books)
    return rows


def shelf3d(P, cam, W=420, Hr=96, D=70, rows=4, seed=11, gap=(1, 4, 26), card_in=0.55,
            card=True, clip=None, lw=5, board=12, cols=None):
    """Bookshelf drawn in perspective through Cam. A gap slot holds a note card pushed
    `card_in` (0..1) of the way into the shelf depth; the inner part is hidden behind the
    neighbouring book, so the card reads as going INTO the shelf. Returns geometry dict."""
    T = cam
    H = rows * (Hr + board) + board
    books = make_books(rows, W, seed, gap, cols=cols)
    info = {}

    def face(pts3, color, plate=None, lvl=0.35, w=lw, outline=True):
        pts = [T(*q) for q in pts3]
        if poly_area(pts) == 0:
            return None
        m = P.mask(pts)
        if clip is not None:
            m = m.inter(clip)
        P.fill(m, color)
        if plate:
            P.tone(m, plate, lvl)
        if outline:
            P.outline(pts, w, clip=clip, weight=0.5)
        return m

    def visible(pts3):
        pts = [T(*q) for q in pts3]
        return poly_area(pts) > 0

    def box(x0, y0, z0, x1, y1, z1, color, side_plate, side_lvl, top_tint=True, w=lw):
        fr = [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)]  # front, facing -Z
        right = [(x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (x1, y0, z0)]
        left = [(x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1)]
        top = [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)]
        for f_, kind in ((right, "side"), (left, "lit"), (top, "top")):
            if visible(f_):
                if kind == "lit":
                    face(f_, color, "B" if color == WHITE else None, 0.12, w=w * 0.8)
                elif kind == "top":
                    face(f_, WHITE, "B" if color in (WHITE, BLUE) else ("R" if color == RED else "Y"), 0.18, w=w * 0.7)
                else:
                    face(f_, color, side_plate, side_lvl, w=w * 0.8)
        return face(fr, color, None, w=w)

    # back panel + inner cavity
    face([(0, H, D), (W, H, D), (W, 0, D), (0, 0, D)], BLUE, "K", 0.62, w=lw * 0.7)
    cam_right = cam.view(W, H / 2, 0)[0] < cam.view(W + 100, H / 2, 0)[0] and cam.syw < 0
    order_right = cam.syw < 0  # camera on +X side -> draw left to right
    # side walls (far one first)
    wall_c = YELLOW
    side_l = [(0, H, 0), (0, H, D), (0, 0, D), (0, 0, 0)]
    side_r = [(W, H, D), (W, H, 0), (W, 0, 0), (W, 0, D)]
    for r in range(rows + 1):
        y = r * (Hr + board)
        # shelf board top face then its front
        face([(0, y + board, D), (W, y + board, D), (W, y + board, 0), (0, y + board, 0)], YELLOW, "R", 0.2, w=lw * 0.6)
    for r in range(rows):
        yb = r * (Hr + board) + board
        rowbooks = books[rows - 1 - r]
        rr = rows - 1 - r
        seq = rowbooks if order_right else rowbooks[::-1]
        for b in seq:
            if b["gap"]:
                gx = b["x"] + b["w"] / 2
                info["slot"] = (b["x"], yb, b["x"] + b["w"], yb + Hr)
                info["slot_row"] = rr
                if card:
                    ch = Hr * 0.72
                    zin = D * card_in
                    cw = D * 1.25
                    z_out = zin - cw
                    info["card_inner"] = [(gx, yb + ch, zin), (gx, yb, zin)]
                    info["card_outer"] = [(gx, yb + 4, z_out), (gx, yb + ch, z_out)]
                    info["card_z"] = (z_out, zin)
                    info["card_x"] = gx
                    info["card_h"] = ch
                    info["card_y"] = yb
                    _card3d(P, T, gx, yb + 2, ch, max(0, 0), zin, clip, lw, part_="in")
                continue
            bh = Hr * b["h"]
            z0 = 4
            m = box(b["x"], yb, z0, b["x"] + b["w"], yb + bh, D - 4, b["c"], "K" if b["c"] != WHITE else "B", 0.4)
            if m is None:
                continue
            # spine details
            if b["band"]:
                for t in (0.18, 0.78):
                    yy = yb + bh * t
                    P.line([T(b["x"] + 2, yy, z0), T(b["x"] + b["w"] - 2, yy, z0)], lw * 0.45, clip=clip)
            if b["dots"]:
                mm = P.mask([T(b["x"], yb + bh * 0.3, z0), T(b["x"] + b["w"], yb + bh * 0.3, z0),
                             T(b["x"] + b["w"], yb + bh * 0.65, z0), T(b["x"], yb + bh * 0.65, z0)]).inter(m)
                P.tone(mm, "K" if b["c"] != WHITE else "R", 0.4)
            lab = [T(b["x"] + b["w"] * 0.25, yb + bh * 0.42, z0), T(b["x"] + b["w"] * 0.75, yb + bh * 0.42, z0),
                   T(b["x"] + b["w"] * 0.75, yb + bh * 0.56, z0), T(b["x"] + b["w"] * 0.25, yb + bh * 0.56, z0)]
            if not b["dots"]:
                lm = P.mask(lab).inter(m)
                P.fill(lm, WHITE if b["c"] != WHITE else YELLOW)
                P.outline(lab, lw * 0.4, weight=0, clip=clip)
            # shadow side of spine
            P.tone(P.mask([T(b["x"] + b["w"] * 0.72, yb, z0), T(b["x"] + b["w"], yb, z0),
                           T(b["x"] + b["w"], yb + bh, z0), T(b["x"] + b["w"] * 0.72, yb + bh, z0)]).inter(m),
                   "K" if b["c"] != WHITE else "B", 0.35)
        # board fronts (above this row)
    for r in range(rows + 1):
        y = r * (Hr + board)
        face([(0, y + board, 0), (W, y + board, 0), (W, y, 0), (0, y, 0)], YELLOW, "R", 0.28, w=lw)
    # card outer part last
    if card and "card_x" in info:
        _card3d(P, T, info["card_x"], info["card_y"] + 2, info["card_h"], None, info["card_z"], clip, lw, part_="out")
    # side walls drawn as front edges (posts)
    for xs in ((-board, 0), (W, W + board)):
        face([(xs[0], H, 0), (xs[1], H, 0), (xs[1], 0, 0), (xs[0], 0, 0)], YELLOW, "R", 0.28, w=lw)
        sd = [(xs[1], H, 0), (xs[1], H, D), (xs[1], 0, D), (xs[1], 0, 0)]
        if visible(sd):
            face(sd, YELLOW, "R", 0.36, w=lw * 0.8)
        sd2 = [(xs[0], H, D), (xs[0], H, 0), (xs[0], 0, 0), (xs[0], 0, D)]
        if visible(sd2):
            face(sd2, YELLOW, "R", 0.36, w=lw * 0.8)
    topf = [(-board, H, D), (W + board, H, D), (W + board, H, 0), (-board, H, 0)]
    if visible(topf):
        face(topf, YELLOW, "R", 0.25, w=lw * 0.8)
    info["T"] = T
    info["H"] = H
    return info


def _card3d(P, T, gx, y0, ch, _unused, z, clip, lw, part_="in"):
    """Card is a plane at X=gx spanning Z; 'in' draws the inner piece (z>=0) before the
    occluding neighbour book, 'out' draws the protruding piece in front of everything."""
    if part_ == "in":
        zin = z
        za, zb = 0, zin
    else:
        z_out, zin = z
        za, zb = z_out, 0.0
    if zb - za <= 0.5:
        return
    pts3 = [(gx, y0 + ch, za), (gx, y0 + ch, zb), (gx, y0, zb), (gx, y0, za)]
    pts = [T(*q) for q in pts3]
    m = P.mask(pts)
    if clip is not None:
        m = m.inter(clip)
    P.fill(m, WHITE)
    if part_ == "in":
        P.tone(m, "B", 0.55)
        P.tone(m, "K", 0.25)
    # rules along Z (the card's width runs along Z here)
    if part_ == "out":
        za_full, zb_full = z
        span = zb_full - za_full
        for i in range(4):
            yy = y0 + ch * (0.64 - i * 0.15)
            rm = P._strip([T(gx, yy, za + 3), T(gx, yy, zb)], [max(1.6, lw * 0.36)] * 2, False).inter(m)
            P.fill(rm, BLUE)
        hm = P._strip([T(gx, y0 + ch * 0.82, za + 3), T(gx, y0 + ch * 0.82, zb)], [lw * 0.55] * 2, False).inter(m)
        P.fill(hm, RED)
        for i in range(3):
            yy = y0 + ch * (0.64 - i * 0.15) + ch * 0.05
            zz1 = za + span * (0.75 if i < 2 else 0.45)
            pts_s = [T(gx, yy + math.sin(t) * 1.2, za + 8 + (zz1 - za - 8) * t / 6) for t in range(7)]
            P.stroke(pts_s, lw * 0.45, taper=(0.1, 0.2), wmin=0.4, clip=clip)
        P.tone(m.rim(5), "B", 0.4)
    P.outline(pts, lw * 0.9, clip=clip)


# ---------- component sheet ----------
def _label(P, x, y, title, note=None):
    P.text((x, y), title, P.font(FONT_CJK, 24), anchor="lm")
    if note:
        P.text((x, y + 28), note, P.font(FONT_CJK, 17), anchor="lm")


def _cell(P, x0, y0, x1, y1, bg=WHITE):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    m = panel(P, pts, bg=bg)
    return m, pts


def draw_sheet(path):
    W, H = 1800, 2700
    P = Page(W, H)
    title_lettering(P, 40, 62, "漫畫網點 元件表", 54, stroke=5, extrude=(4, 5))
    P.text((40, 122), "四色印刷模型：K 墨版疊印在 Y/R/B 色版上｜網點每版固定角度與格距（Y 0°、R 75°、B 15°、K 45°，格距 10px）｜描邊依受光面粗細變化｜不畫臉，只用護目鏡",
           P.font(FONT_CJK, 19), anchor="lm")
    borders = []

    # ---- row 1: techniques ----
    y0, y1 = 160, 420
    cw = (W - 80 - 5 * 20) / 6
    xs = [40 + i * (cw + 20) for i in range(6)]
    # 1 halftone ramps
    m, pts = _cell(P, xs[0], y0, xs[0] + cw, y1); borders.append(pts)
    for r, pl in enumerate("YRBK"):
        for c in range(5):
            bx = xs[0] + 16 + c * (cw - 32) / 5
            by = y0 + 16 + r * 58
            sq = [(bx, by), (bx + (cw - 32) / 5 - 4, by), (bx + (cw - 32) / 5 - 4, by + 50), (bx, by + 50)]
            P.tone(P.mask(sq, pad=0), pl, [0.08, 0.2, 0.35, 0.55, 0.8][c])
    # 2 weighted outline
    m, pts = _cell(P, xs[1], y0, xs[1] + cw, y1); borders.append(pts)
    cpts = ellipse_pts(xs[1] + cw * 0.36, y0 + 120, 62, 62, 90)
    mm = P.mask(cpts); metal(P, mm, 14); P.outline(cpts, 9)
    rp = rrect_pts(xs[1] + cw * 0.58, y0 + 150, xs[1] + cw - 22, y0 + 230, 10)
    shade(P, P.mask(rp), RED, 10); P.outline(rp, 9)
    # 3 tapered strokes & hatch
    m, pts = _cell(P, xs[2], y0, xs[2] + cw, y1); borders.append(pts)
    for i in range(4):
        P.stroke(bezier([(xs[2] + 20, y0 + 30 + i * 22), (xs[2] + cw / 2, y0 + 10 + i * 22), (xs[2] + cw - 20, y0 + 40 + i * 22)]),
                 3 + i * 2.2, taper=(0.4, 0.4))
    hm = P.mask(ellipse_pts(xs[2] + cw / 2, y0 + 190, 70, 48, 60))
    P.fill(hm, WHITE); hatch(P, hm.rim(40), 7, 45, 2.0); hatch(P, hm.rim(20), 7, -45, 2.0)
    P.outline(ellipse_pts(xs[2] + cw / 2, y0 + 190, 70, 48, 60), 6)
    # 4 speed lines + focus lines
    m, pts = _cell(P, xs[3], y0, xs[3] + cw, y1); borders.append(pts)
    P.tone(m, "B", lambda x, y: 0.05 + 0.4 * (x - xs[3]) / cw)
    focus_lines(P, m, xs[3] + cw / 2, y0 + 130, 46, n=90, w=7)
    # 5 burst
    m, pts = _cell(P, xs[4], y0, xs[4] + cw, y1); borders.append(pts)
    burst(P, xs[4] + cw / 2, y0 + 130, 105, seed=8)
    # 6 panels & gutters thumbnail
    m, pts = _cell(P, xs[5], y0, xs[5] + cw, y1, bg=PAPER); borders.append(pts)
    gx0, gy0 = xs[5] + 16, y0 + 16
    tw, th = cw - 32, y1 - y0 - 32
    thumbs = [[(gx0, gy0), (gx0 + tw, gy0), (gx0 + tw, gy0 + th * 0.42), (gx0, gy0 + th * 0.5)],
              [(gx0, gy0 + th * 0.5 + 8), (gx0 + tw * 0.55 - 4, gy0 + th * 0.47 + 8), (gx0 + tw * 0.5 - 4, gy0 + th), (gx0, gy0 + th)],
              [(gx0 + tw * 0.55 + 4, gy0 + th * 0.465 + 8), (gx0 + tw, gy0 + th * 0.42 + 8), (gx0 + tw, gy0 + th), (gx0 + tw * 0.5 + 4, gy0 + th)]]
    for tp in thumbs:
        tm = panel(P, tp)
        P.tone(tm, "B", 0.12)
        panel_border(P, tp, 3.5)
    labels1 = [("網點四版", "格距固定，只改點徑"), ("粗細描邊", "受光邊 0.6 倍、背光邊 1.6 倍"), ("漸細筆觸＋排線", "陰影可用交叉排線"),
               ("集中線", "楔形，被格框裁切"), ("爆炸框", "紅外圈＋黃心＋橙點"), ("分格與溝", "格線等寬、溝 8–12px")]
    for i, (a, b) in enumerate(labels1):
        _label(P, xs[i], y1 + 26, a, b)

    # ---- row 2: robot poses ----
    y0, y1 = 500, 960
    cw2 = (W - 80 - 3 * 20) / 4
    poses = [("idle", "待機", "站姿、雙手自然下垂"), ("placing", "放置", "前傾、手掌推出"),
             ("thinking", "思考", "頭側傾、手抵護目鏡下緣"), ("triumph", "勝利", "雙手高舉、腳張開")]
    for i, (pz, nm, note) in enumerate(poses):
        x0 = 40 + i * (cw2 + 20)
        m, pts = _cell(P, x0, y0, x0 + cw2, y1); borders.append(pts)
        if pz == "triumph":
            focus_lines(P, m, x0 + cw2 / 2, y0 + 190, 120, n=70, w=6, seed=9)
        else:
            P.tone(m, "B", lambda x, y, y0=y0: 0.04 + 0.16 * (y - y0) / 460)
        o = robot(P, x0 + cw2 / 2 - (20 if pz == "placing" else 0), y1 - 40, 1.45, pz)
        if pz == "thinking":
            sfx(P, "?", x0 + cw2 - 70, y0 + 80, 90, angle=12, grow=0)
        if pz == "triumph":
            sparkle(P, x0 + 60, y0 + 70, 26); sparkle(P, x0 + cw2 - 60, y0 + 110, 20)
        if pz == "placing":
            note_card(P, o["hand_f"][0] + 58, o["hand_f"][1] + 4, 104, 70, angle=-4)
            impact_marks(P, o["hand_f"][0] + 58, o["hand_f"][1] + 4, 62, 86, n=5, a0=-50, a1=50, w=4)
        P.line([(x0 + 10, y1 - 38), (x0 + cw2 - 10, y1 - 38)], 3)
        _label(P, x0, y1 + 26, f"機器人：{nm}", note)

    # ---- row 3: cards, check/cross, arrow ----
    y0, y1 = 1040, 1340
    cw3 = (W - 80 - 4 * 20) / 5
    xs3 = [40 + i * (cw3 + 20) for i in range(5)]
    for i, (st, nm, nt) in enumerate([("plain", "筆記卡", "索引卡：紅標題線、藍格線"), ("wrong", "筆記卡（錯誤）", "紅網點邊＋紅叉"),
                                      ("verified", "筆記卡（已驗證）", "藍章＋白勾")]):
        m, pts = _cell(P, xs3[i], y0, xs3[i] + cw3, y1); borders.append(pts)
        note_card(P, xs3[i] + cw3 / 2, (y0 + y1) / 2, 230, 150, angle=[-6, 4, -3][i], state=st)
        _label(P, xs3[i], y1 + 26, nm, nt)
    m, pts = _cell(P, xs3[3], y0, xs3[3] + cw3, y1); borders.append(pts)
    check_mark(P, xs3[3] + cw3 * 0.3, (y0 + y1) / 2, 1.2)
    cross_mark(P, xs3[3] + cw3 * 0.72, (y0 + y1) / 2, 1.2)
    _label(P, xs3[3], y1 + 26, "勾與叉", "筆觸粗細＋白芯")
    m, pts = _cell(P, xs3[4], y0, xs3[4] + cw3, y1); borders.append(pts)
    arrow(P, bezier([(xs3[4] + 40, y1 - 60), (xs3[4] + cw3 * 0.4, y0 + 40), (xs3[4] + cw3 - 40, y0 + 110)], 50), 40)
    _label(P, xs3[4], y1 + 26, "箭頭", "沿曲線、墨色立體塊")

    # ---- row 4: shelf, database, big number ----
    y0, y1 = 1420, 1980
    wa, wb = 760, 380
    wc = W - 80 - wa - wb - 40
    m, pts = _cell(P, 40, y0, 40 + wa, y1); borders.append(pts)
    P.tone(m, "B", lambda x, y: 0.06 + 0.22 * (y - y0) / 560)
    cam = Cam(40 + wa / 2 + 10, y0 + 275, f=1000, yaw=-40, pitch=-10, dist=950, target=(230, 220, 30))
    shelf3d(P, cam, W=460, Hr=92, D=80, rows=4, gap=(1, 9, 34), card_in=0.5, clip=m)
    _label(P, 40, y1 + 26, "知識庫書櫃（3D）", "卡片插進縫：內段被右側書擋住、外段露出")
    m, pts = _cell(P, 40 + wa + 20, y0, 40 + wa + 20 + wb, y1); borders.append(pts)
    database(P, 40 + wa + 20 + wb / 2, y0 + 120, rx=110, ry=32, seg_h=88)
    _label(P, 40 + wa + 20, y1 + 26, "資料庫塔", "藍柱＋黑點陰影＋白反光條")
    xc = 40 + wa + wb + 40
    m, pts = _cell(P, xc, y0, xc + wc, y1); borders.append(pts)
    focus_lines(P, m, xc + wc / 2, (y0 + y1) / 2, 150, n=110, w=8, seed=12)
    burst_number(P, xc + wc / 2, (y0 + y1) / 2, 210, "61", "%", seed=5)
    _label(P, xc, y1 + 26, "爆炸框大數字", "Impact 紅字＋墨框＋墨色立體塊")

    # ---- row 5: chart, SFX, caption + tag ----
    y0, y1 = 2060, 2480
    wa = 600
    m, pts = _cell(P, 40, y0, 40 + wa, y1); borders.append(pts)
    bar_chart(P, 90, y0 + 50, 40 + wa - 50, y1 - 70, [34, 47, 61], ["只用搜尋", "加筆記", "加知識庫"], hi=2)
    _label(P, 40, y1 + 26, "長條圖", "只有重點那條用紅")
    m, pts = _cell(P, 40 + wa + 20, y0, 40 + 2 * wa + 20, y1); borders.append(pts)
    P.tone(m, "Y", lambda x, y: 0.15 + 0.35 * (y - y0) / 420)
    focus_lines(P, m, 40 + wa + 20 + wa / 2, y0 + 140, 90, n=80, w=6, seed=21)
    sfx(P, "CLICK!", 40 + wa + 20 + wa / 2, y0 + 140, 110, angle=-7)
    sfx(P, "3X", 40 + wa + 20 + wa * 0.3, y0 + 320, 100, color=WHITE, shade_plate="B", angle=6, grow=0.2)
    sfx(P, "100%", 40 + wa + 20 + wa * 0.7, y0 + 320, 84, color=RED, shade_plate="K", angle=-4)
    _label(P, 40 + wa + 20, y1 + 26, "音效字（拉丁字母與數字）", "逐字旋轉、由小變大、墨框＋立體塊")
    xc = 40 + 2 * wa + 40
    m, pts = _cell(P, xc, y0, W - 40, y1, bg=PAPER); borders.append(pts)
    chapter_tag(P, xc + 30, y0 + 40, "02", "記憶的四層")
    caption_box(P, xc + 30, y0 + 130, W - 70, "Agent 把每次學到的事寫成一張卡，放進知識庫。", 30)
    balloon(P, (xc + 60, y0 + 280, xc + 400, y0 + 380), (xc + 140, y0 + 410))
    P.text((xc + 230, y0 + 330), "找到了！", P.font(FONT_CJK, 34))
    _label(P, xc, y1 + 26, "章節標、旁白框、對白泡泡", "黃色旁白框、紅底白字章節號")

    for pts in borders:
        panel_border(P, pts, 4.5)
    P.text((40, H - 70), "全部原創造型；只學網點、描邊與分格技法，不照搬任何作品的構圖或角色。", P.font(FONT_CJK, 20), anchor="lm")
    bad = check_glyphs("".join(CJK_USED))
    print("missing glyphs:", bad)
    P.render().save(path)


if __name__ == "__main__":
    draw_sheet(os.path.join(HERE, "components.png"))
    print("ok")
