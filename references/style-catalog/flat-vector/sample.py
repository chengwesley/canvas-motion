#!/usr/bin/env python3
"""flat-vector style sample (original artwork). Renders sample.png next to this file.

Canonical flat-vector technique encoded in the helpers below:
  solid()        every shape = base fill + core-shade crescent (bottom-right) + thin rim light
                 (top-left) + optional specular dash. The crescents are made by subtracting
                 the shape's own silhouette shifted toward / away from the light, so every
                 shape is lit from the same top-left light with zero outlines.
  split()        hard 2-tone split for flat panels (book spines, card, cabinet): shade on the
                 right ~35%, never a gradient.
  long_shadow()  45 deg down-right soft long shadow, one colour (a darker step of the
                 background), fading with distance, clipped at the ground line.
  grain()        fine monochrome film grain so big flat fields are not sterile.
Palette: 4-step ramps (shade, base, light, highlight) for 5 hues + background.
"""
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
import math, os, random

W, H, S = 1080, 1350, 2           # S = supersample factor
GROUND = 1032                     # ground line; below GROUND+20 the frame stays calm for subtitles
rnd = random.Random(61)
HEI_TC = '/System/Library/Fonts/STHeiti Medium.ttc'
HIRA = '/System/Library/Fonts/Hiragino Sans GB.ttc'


def rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# 4-step ramps: [shade, base, light, highlight]
BG = [rgb('EAD9BD'), rgb('F5E8D3'), rgb('FAF1E2'), rgb('FFF9EF')]
SUN = [rgb('F8D49A'), rgb('FBE0B0'), rgb('FDEBC9'), rgb('FFF4DE')]
NAVY = [rgb('1B2748'), rgb('26365F'), rgb('34497C'), rgb('5B74B0')]
TEAL = [rgb('1E8C82'), rgb('2DB3A6'), rgb('5CCDBF'), rgb('B5EEE5')]
CORAL = [rgb('CF4A38'), rgb('F2664F'), rgb('F78A73'), rgb('FFC9B8')]
MUST = [rgb('DE9620'), rgb('F7B93E'), rgb('FACB68'), rgb('FFE7AE')]
CREAM = [rgb('E6D6BC'), rgb('FFF8EA'), rgb('FFFCF5'), rgb('FFFFFF')]
INK = rgb('B9C2D6')               # text bars on paper
SHADOW = rgb('D9C29E')            # long-shadow colour = one step darker than BG base
BOOKS = [TEAL, CORAL, MUST, CREAM]


# ------------------------------------------------------------------ technique helpers
def _shift(m, dx, dy):
    o = Image.new('L', m.size, 0); o.paste(m, (int(dx), int(dy))); return o


class Layer:
    """Transparent supersampled layer; all drawing in 1080-space units."""
    def __init__(s):
        s.im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)

    # ---- the core rule: one light from top-left, no outlines
    def solid(s, draw, box, ramp, shade=.16, rim=3.5, spec=None, flat=False):
        """draw(d, ox, oy) paints the silhouette (255) onto a local mask whose origin is box[0:2].
        shade = crescent depth as a fraction of the shape's short side."""
        pad = 40
        x0, y0, x1, y1 = box
        ox, oy = (x0 - pad) * S, (y0 - pad) * S
        m = Image.new('L', (int((x1 - x0 + 2 * pad) * S), int((y1 - y0 + 2 * pad) * S)), 0)
        draw(ImageDraw.Draw(m), ox, oy)
        pos = (int(ox), int(oy))
        s.im.paste(ramp[1] + (255,), pos, m)
        if flat: return
        k = min(x1 - x0, y1 - y0) * shade * S
        if k > 1:   # core shade: the part not covered when the shape is moved toward the light
            s.im.paste(ramp[0] + (255,), pos, ImageChops.subtract(m, _shift(m, -k * .55, -k)))
        if rim:     # rim light: thin crescent on the lit side
            r = rim * S
            s.im.paste(ramp[2] + (255,), pos, ImageChops.subtract(m, _shift(m, r * .7, r)))
        if spec:    # specular dash: short round stroke in the highlight tone, top-left inside
            (a, b), (c, e), w = spec
            s.d.line([(a * S, b * S), (c * S, e * S)], fill=ramp[3], width=int(w * S))
            for px, py in ((a, b), (c, e)):
                s.d.ellipse([(px - w / 2) * S, (py - w / 2) * S, (px + w / 2) * S, (py + w / 2) * S], fill=ramp[3])

    def rr(s, x0, y0, x1, y1, r, ramp, **kw):
        s.solid(lambda d, ox, oy: d.rounded_rectangle([x0 * S - ox, y0 * S - oy, x1 * S - ox, y1 * S - oy], r * S, fill=255),
                (x0, y0, x1, y1), ramp, **kw)

    def circ(s, cx, cy, r, ramp, **kw):
        s.solid(lambda d, ox, oy: d.ellipse([(cx - r) * S - ox, (cy - r) * S - oy, (cx + r) * S - ox, (cy + r) * S - oy], fill=255),
                (cx - r, cy - r, cx + r, cy + r), ramp, **kw)

    def split(s, pts, ramp, at=.65, ang=0):
        """flat panel (polygon given as 4 corners TL,TR,BR,BL) with a hard 2-tone split:
        everything right of `at` (fraction along the top edge) is the shade tone."""
        s.d.polygon([(x * S, y * S) for x, y in pts], fill=ramp[1])
        (ax, ay), (bx, by), (cx, cy), (dx, dy) = pts
        u = lambda p, q, t: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        p1, p2 = u(pts[0], pts[1], at), u(pts[3], pts[2], at)
        s.d.polygon([(x * S, y * S) for x, y in (p1, pts[1], pts[2], p2)], fill=ramp[0])

    def poly(s, pts, col):
        s.d.polygon([(x * S, y * S) for x, y in pts], fill=col)

    def limb(s, pts, w, col):
        p = [(x * S, y * S) for x, y in pts]
        s.d.line(p, fill=col, width=int(w * S), joint='curve')
        for x, y in p:
            s.d.ellipse([x - w * S / 2, y - w * S / 2, x + w * S / 2, y + w * S / 2], fill=col)


def rot(cx, cy, deg):
    a = math.radians(deg); ca, sa = math.cos(a), math.sin(a)
    return lambda u, v: (cx + u * ca - v * sa, cy + u * sa + v * ca)


def long_shadow(layer, length, strength=.55):
    """Smear the silhouette 45 deg down-right, linear fade, soft edge, clipped at the ground."""
    m = layer.im.getchannel('A').resize((W, H), Image.BILINEAR)
    acc = Image.new('L', (W, H), 0)
    for d in range(2, length, 2):
        k = (1 - d / length) ** 1.3 * strength
        t = Image.new('L', (W, H), 0); t.paste(m.point(lambda v, k=k: int(v * k)), (d, d))
        acc = ImageChops.lighter(acc, t)
    clip = Image.new('L', (W, H), 0); ImageDraw.Draw(clip).rectangle([0, 0, W, GROUND], fill=255)
    acc = ImageChops.multiply(acc.filter(ImageFilter.GaussianBlur(3)), clip)
    return acc.resize((W * S, H * S), Image.BILINEAR)


def grain(im, amount=.10, seed=61):
    random.seed(seed)
    n = Image.effect_noise(im.size, 22).convert('RGB')
    return Image.blend(im, ImageChops.overlay(im, n), amount)


def text_layer(txt, x, y, size, col, font=HEI_TC, index=0, fat=0):
    L = Layer(); f = ImageFont.truetype(font, size * S, index=index)
    L.d.text((x * S, y * S), txt, font=f, fill=col, stroke_width=int(fat * S), stroke_fill=col); return L


# ------------------------------------------------------------------ components
def cabinet(L, x0, y0, x1, y1):
    """knowledge base: a cabinet of book spines with one empty, lit slot. Returns slot centre."""
    for fx in (x0 + 18, x1 - 58):
        L.rr(fx, y1 - 10, fx + 40, y1 + 26, 8, NAVY, shade=.3, rim=0)
    L.rr(x0, y0, x1, y1, 24, NAVY, shade=.06, rim=4)
    L.rr(x0 - 18, y0 - 26, x1 + 18, y0 + 14, 14, NAVY, shade=.25, rim=4)
    rows, pad, gap = 4, 26, 18
    rh = (y1 - y0 - 34 - pad - gap * (rows - 1)) / rows; slot = None
    for r in range(rows):
        ry0 = y0 + 34 + r * (rh + gap); ry1 = ry0 + rh
        L.rr(x0 + pad, ry0, x1 - pad, ry1, 10, [NAVY[0], rgb('2E4170'), NAVY[2], NAVY[3]], shade=0, rim=0)
        L.rr(x0 + pad, ry0, x1 - pad, ry0 + 14, 6, [NAVY[0], NAVY[0], NAVY[0], NAVY[0]], flat=True)   # inner top shadow
        x = x0 + pad + 12; i = 0; last = None
        while True:
            bw = rnd.choice((24, 28, 32, 38, 44)); bh = rh - rnd.choice((12, 20, 30, 42))
            if r == 1 and slot is None:
                L.rr(x, ry0 + 16, x + 70, ry1, 8, [rgb('6B88C8')] * 2 + [rgb('86A2DA')] * 2, flat=True)
                L.rr(x + 8, ry0 + 24, x + 62, ry1, 6, [rgb('9DB6E6')] * 4, flat=True)
                slot = (x + 35, (ry0 + ry1) / 2 + 6); x += 78; i += 1; continue
            if x + bw > x1 - pad - 14: break
            c = rnd.choice([p for p in BOOKS if p is not last]); last = c
            if i % 5 == 3 and x + bw + 32 < x1 - pad - 14:          # one leaning book per row
                P = rot(x + bw / 2 + 12, ry1 - bh / 2 + 2, 11)
                L.split([P(-bw / 2, -bh / 2), P(bw / 2, -bh / 2), P(bw / 2, bh / 2), P(-bw / 2, bh / 2)], c, at=.62)
                x += bw + 30
            else:
                L.split([(x, ry1 - bh), (x + bw, ry1 - bh), (x + bw, ry1), (x, ry1)], c, at=.62)
                band = NAVY[1] if c is not CREAM else CORAL[1]
                if bw >= 32: L.poly([(x + 6, ry1 - bh + 14), (x + bw - 6, ry1 - bh + 14), (x + bw - 6, ry1 - bh + 24), (x + 6, ry1 - bh + 24)], band)
                else: L.d.ellipse([(x + bw / 2 - 5) * S, (ry1 - 24) * S, (x + bw / 2 + 5) * S, (ry1 - 14) * S], fill=band)
                x += bw + 5
            i += 1
    return slot


def plant(L, cx, base):
    """geometric pot plant: leaves are pointed ellipse halves, each split in 2 tones."""
    for deg, ln in ((-38, 80), (-8, 104), (24, 86), (52, 62)):
        P = rot(cx, base - 30, deg - 90)
        L.poly([P(0, 0), P(ln * .5, -18), P(ln, 0), P(ln * .5, 18)], TEAL[1])
        L.poly([P(0, 0), P(ln, 0), P(ln * .5, 18)], TEAL[0])
    L.rr(cx - 34, base - 40, cx + 34, base, 10, CORAL, shade=.3, rim=3)


def card(L, cx, cy, deg=-12, w=124, h=156):
    """note card: cream sheet, coral header band, text bars; hard split shade on the right."""
    P = rot(cx, cy, deg)
    L.split([P(-w / 2, -h / 2), P(w / 2, -h / 2), P(w / 2, h / 2), P(-w / 2, h / 2)], CREAM, at=.8)
    L.split([P(-w / 2, -h / 2), P(w / 2, -h / 2), P(w / 2, -h / 2 + 32), P(-w / 2, -h / 2 + 32)], CORAL, at=.8)
    for k, lw in enumerate((.76, .58, .7, .4)):
        v = -h / 2 + 56 + k * 23
        L.limb([P(-w / 2 + 18, v), P(-w / 2 + 18 + (w - 36) * lw, v)], 8, INK)


def agent(L, cx, base):
    """AI agent: a machine built from capsules and circles. No face: the head carries one
    horizontal sensor light inside a dark visor."""
    for dx in (-46, 46):                                               # legs + feet
        L.rr(cx + dx - 20, base - 96, cx + dx + 20, base - 14, 12, NAVY, shade=.3, rim=0)
        L.rr(cx + dx - 36, base - 30, cx + dx + 40, base, 15, NAVY, shade=.3, rim=3)
    L.limb([(cx - 88, base - 270), (cx - 132, base - 200), (cx - 120, base - 134)], 32, TEAL[0])   # back arm
    L.circ(cx - 120, base - 128, 24, NAVY, shade=.3, rim=0)
    L.rr(cx - 98, base - 318, cx + 98, base - 78, 48, TEAL, shade=.2, rim=5,
         spec=(((cx - 70, base - 270), (cx - 70, base - 236), 9)))                                # body
    L.rr(cx - 56, base - 256, cx + 40, base - 166, 18, CREAM, shade=.14, rim=0)                     # chest panel
    L.circ(cx - 26, base - 211, 16, CORAL, shade=.3, rim=2)
    for k in range(3): L.rr(cx - 2, base - 232 + k * 18, cx + 26, base - 223 + k * 18, 4, [INK] * 4, flat=True)
    L.rr(cx - 60, base - 140, cx + 60, base - 120, 10, [TEAL[0]] * 4, flat=True)
    L.rr(cx - 28, base - 346, cx + 28, base - 304, 8, NAVY, shade=.3, rim=0)                         # neck
    L.limb([(cx + 50, base - 480), (cx + 66, base - 536)], 10, NAVY[1])                               # antenna
    L.circ(cx + 68, base - 548, 21, CORAL, shade=.3, rim=3, spec=(((cx + 60, base - 558), (cx + 60, base - 556), 6)))
    for dx in (-120, 120):                                                                            # ear pods
        L.rr(cx + dx - 17, base - 440, cx + dx + 17, base - 386, 11, NAVY, shade=.3, rim=0)
    L.rr(cx - 114, base - 488, cx + 114, base - 332, 58, CREAM, shade=.32, rim=0,
         spec=(((cx - 74, base - 462), (cx - 40, base - 474), 9)))                                    # head
    L.rr(cx - 86, base - 452, cx + 86, base - 368, 42, NAVY, shade=.12, rim=0)                         # visor
    L.rr(cx - 58, base - 416, cx + 58, base - 402, 7, [TEAL[2]] * 4, flat=True)                        # sensor light
    L.rr(cx - 58, base - 414, cx - 10, base - 404, 5, [TEAL[3]] * 4, flat=True)


# ------------------------------------------------------------------ compose
def main():
    bg = Image.new('RGB', (W * S, H * S), BG[1]); d = ImageDraw.Draw(bg)
    for (x0, y0, x1, y1), c in (((420, 150, 1180, 910), SUN[1]), ((515, 245, 1085, 815), SUN[2])):
        d.ellipse([x0 * S, y0 * S, x1 * S, y1 * S], fill=c)
    d.rectangle([0, GROUND * S, W * S, H * S], fill=BG[0])           # floor: one flat step darker
    d.rectangle([0, (GROUND + 14) * S, W * S, H * S], fill=rgb('EFDFC4'))

    deco = Layer()                                                    # sparse geometric confetti
    for x, y, r, c in ((560, 300, 12, TEAL[1]), (612, 112, 15, MUST[1]), (1000, 140, 10, CORAL[1]), (560, 930, 9, MUST[1])):
        deco.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=c)
    for x, y, c in ((540, 470, CORAL[1]), (560, 150, NAVY[1])):
        deco.limb([(x - 13, y), (x + 13, y)], 7, c); deco.limb([(x, y - 13), (x, y + 13)], 7, c)
    deco.poly([(470, 990), (494, 1032), (446, 1032)], MUST[1])

    Lshelf = Layer(); slot = cabinet(Lshelf, 650, 402, 1010, 1006); plant(Lshelf, 940, 376)
    Lbot = Layer(); agent(Lbot, 250, GROUND)
    Lcard = Layer(); card(Lcard, 512, 664)
    Larm = Layer(); Larm.limb([(338, 772), (424, 812), (482, 740)], 34, TEAL[1]); Larm.circ(484, 736, 26, NAVY, shade=.3, rim=3)

    Lpath = Layer()                                                   # dotted flight path card -> slot
    p0, p1, p2 = (572, 566), (620, 420), (slot[0] - 60, slot[1] - 4)
    for i in range(7):
        t = i / 6; x = (1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1]
        r = 5 + 3 * t; Lpath.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=CORAL[1])
    Lpath.poly([(p2[0] + 16, p2[1] - 20), (p2[0] + 16, p2[1] + 20), (p2[0] + 46, p2[1])], CREAM[1])

    Lhead = text_layer('知識庫', 76, 96, 66, NAVY[1])
    Lhead.d.rounded_rectangle([78 * S, 62 * S, 152 * S, 74 * S], 6 * S, fill=CORAL[1])
    Lnum = text_layer('61%', 70, 168, 196, CORAL[1], font=HIRA, index=2)
    # progress capsule = the number as a quantity: 61% of the track filled
    Lbar = Layer(); bx0, bx1, by = 82, 470, 396
    Lbar.rr(bx0, by, bx1, by + 26, 13, [BG[0]] * 4, flat=True)
    Lbar.rr(bx0, by, bx0 + (bx1 - bx0) * .61, by + 26, 13, CORAL, shade=0, rim=0)
    Lbar.rr(bx0 + 10, by + 6, bx0 + (bx1 - bx0) * .61 - 14, by + 11, 3, [CORAL[2]] * 4, flat=True)
    Lcap = text_layer('筆記已歸檔', 82, 436, 32, NAVY[2])

    for lay, ln, st in ((Lnum, 60, .3), (Lbar, 40, .3), (Lshelf, 230, .6), (Lbot, 200, .6), (Lcard, 120, .55), (Larm, 90, .4)):
        bg.paste(SHADOW, (0, 0), long_shadow(lay, ln, st))
    for lay in (deco, Lshelf, Lbot, Lcard, Larm, Lpath, Lhead, Lnum, Lbar, Lcap):
        bg.paste(lay.im, (0, 0), lay.im)
    out = grain(bg.resize((W, H), Image.LANCZOS))
    out.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.png'))


if __name__ == '__main__':
    main()
