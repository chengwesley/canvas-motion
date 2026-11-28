#!/usr/bin/env python3
"""flat-vector component kit (original artwork, Python 3 + PIL only).

Run directly to render components.png (the component sheet). Import it to compose scenes:

    from components import *
    L = Layer(1080, 1350)
    robot(L, 260, 1050, pose='reach', hand=(560, 700))
    img = Canvas(1080, 1350, BG[1]); img.cast(L, 120); img.put(L)

Technique (one rule set for every component):
  * No outlines. Shapes are separated only by tone steps.
  * Every solid gets: base fill, a hard core-shade crescent on the bottom-right (silhouette
    minus itself shifted toward the top-left light), a 3-4 px rim light on the top-left, and
    at most one round-capped specular dash.
  * Flat sheets (paper, book spines, drawer cards) get a hard 2-tone split instead of a crescent.
  * Drop shadows are hard-edged and flat: the silhouette swept 45 deg down-right, applied as
    one multiply tone (so it darkens whatever is behind it evenly). Floor objects add a flat
    contact capsule. No blur, no gradient, no glow anywhere.
"""
from PIL import Image, ImageDraw, ImageFont, ImageChops
import math, os, random

S = 2  # supersample factor; all public coordinates are in output pixels
HEI = '/System/Library/Fonts/STHeiti Medium.ttc'       # Chinese: STHeiti Medium only
NUM = '/System/Library/Fonts/Avenir Next.ttc'          # digits / Latin: Avenir Next
NUM_HEAVY, NUM_BOLD, NUM_DEMI = 8, 0, 2


def rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(*hexes): return [rgb(h) for h in hexes]


# 4-step ramps: [shade, base, light, highlight]
BG = ramp('E8DCC8', 'F3EBDD', 'F9F4EA', 'FFFCF6')      # paper wall
FLOOR = ramp('DCCDB3', 'E6D9C2', 'EEE4D2', 'F6EFE2')
SUN = ramp('F6CF8E', 'F9DDA8', 'FBE8C6', 'FDF3E1')
NAVY = ramp('182240', '233158', '33467A', '5A72AE')
TEAL = ramp('16867B', '22A697', '4FC4B5', 'A8E8DE')
CORAL = ramp('D24A35', 'EF6449', 'F68A70', 'FFC7B5')
MUST = ramp('D98F16', 'F4B43A', 'F9C966', 'FFE6A8')
CREAM = ramp('E5D7BF', 'FFF9EE', 'FFFCF6', 'FFFFFF')
INK = rgb('BFC6D6')            # text bars on paper
HOLE = rgb('121A33')           # compartment interiors
TINT = (233, 222, 205)         # multiply tone for every cast shadow (~ -9% warm)
BOOKS = [TEAL, CORAL, MUST, CREAM, NAVY]
SPINES = [TEAL, MUST, CREAM, TEAL, MUST, CREAM, CORAL]   # coral kept rare: it is the accent


# ---------------------------------------------------------------- geometry helpers
def rot(cx, cy, deg):
    a = math.radians(deg); ca, sa = math.cos(a), math.sin(a)
    return lambda u, v: (cx + u * ca - v * sa, cy + u * sa + v * ca)


def ik(sh, hand, l1, l2, bend=1):
    """two-bone IK: returns elbow point. bend=+1 elbow below the shoulder->hand line."""
    dx, dy = hand[0] - sh[0], hand[1] - sh[1]
    d = max(1e-3, min(math.hypot(dx, dy), l1 + l2 - 1))
    a = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    t = math.atan2(dy, dx) + (a if bend > 0 else -a)
    e = (sh[0] + l1 * math.cos(t), sh[1] + l1 * math.sin(t))
    return e


def bez(p0, p1, p2, n):
    return [((1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1]) for t in (i / (n - 1) for i in range(n))]


def _shift(m, dx, dy):
    o = Image.new('L', m.size, 0); o.paste(m, (int(round(dx)), int(round(dy)))); return o


def font(size, path=HEI, index=0): return ImageFont.truetype(path, int(size * S), index=index)


def check_glyphs(txt, path=HEI, index=0):
    """raise if any character would render as .notdef (tofu)."""
    f = ImageFont.truetype(path, 48, index=index)

    def r(c):
        im = Image.new('L', (80, 80), 0); ImageDraw.Draw(im).text((8, 8), c, font=f, fill=255); return im
    tofu = r('\U0010FFFD').tobytes()
    for ch in txt:
        if ch.isspace(): continue
        m = r(ch)
        if m.getbbox() is None or m.tobytes() == tofu:
            raise ValueError(f'missing glyph {ch!r} in {os.path.basename(path)}')


# ---------------------------------------------------------------- drawing layer
class Layer:
    """Transparent supersampled RGBA layer. All drawing is in output-pixel units."""

    def __init__(s, w, h):
        s.w, s.h = w, h
        s.im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)

    # -- primitive mask painters: prims = [('rr',x0,y0,x1,y1,r) | ('ell',x0,y0,x1,y1) | ('poly',pts) | ('line',pts,w)]
    @staticmethod
    def _paint(d, prims, ox, oy, fill=255):
        for p in prims:
            k = p[0]
            if k == 'rr':
                _, x0, y0, x1, y1, r = p
                d.rounded_rectangle([x0 * S - ox, y0 * S - oy, x1 * S - ox, y1 * S - oy], max(0, r * S), fill=fill)
            elif k == 'ell':
                _, x0, y0, x1, y1 = p
                d.ellipse([x0 * S - ox, y0 * S - oy, x1 * S - ox, y1 * S - oy], fill=fill)
            elif k == 'poly':
                d.polygon([(x * S - ox, y * S - oy) for x, y in p[1]], fill=fill)
            elif k == 'line':
                pts, w = p[1], p[2]; q = [(x * S - ox, y * S - oy) for x, y in pts]
                d.line(q, fill=fill, width=int(w * S), joint='curve')
                for x, y in q: d.ellipse([x - w * S / 2, y - w * S / 2, x + w * S / 2, y + w * S / 2], fill=fill)

    @staticmethod
    def _bbox(prims):
        xs, ys = [], []
        for p in prims:
            if p[0] in ('rr', 'ell'): xs += [p[1], p[3]]; ys += [p[2], p[4]]
            else:
                pad = p[2] / 2 if p[0] == 'line' else 0
                xs += [x - pad for x, _ in p[1]] + [x + pad for x, _ in p[1]]
                ys += [y - pad for _, y in p[1]] + [y + pad for _, y in p[1]]
        return min(xs), min(ys), max(xs), max(ys)

    def solid(s, prims, rp, shade=.18, rim=3.5, spec=None, flat=False, short=None):
        """THE rule: base + core-shade crescent (bottom-right) + rim light (top-left) + 1 spec."""
        x0, y0, x1, y1 = s._bbox(prims); pad = 30
        ox, oy = int((x0 - pad) * S), int((y0 - pad) * S)
        m = Image.new('L', (int((x1 - x0 + 2 * pad) * S) + 2, int((y1 - y0 + 2 * pad) * S) + 2), 0)
        s._paint(ImageDraw.Draw(m), prims, ox, oy)
        pos = (ox, oy)
        s.im.paste(rp[1] + (255,), pos, m)
        if not flat:
            k = (short if short else min(x1 - x0, y1 - y0)) * shade * S
            if k > 1: s.im.paste(rp[0] + (255,), pos, ImageChops.subtract(m, _shift(m, -k * .55, -k)))
            if rim:
                r = rim * S; s.im.paste(rp[2] + (255,), pos, ImageChops.subtract(m, _shift(m, r * .7, r)))
        if spec:
            s.solid([('line', spec[0], spec[1])], [rp[3]] * 4, flat=True)
        return m, pos

    def flat(s, prims, col):
        s._paint(s.d, prims, 0, 0, fill=col if len(col) == 4 else col + (255,))

    # shorthands
    def rr(s, x0, y0, x1, y1, r, rp, **kw): return s.solid([('rr', x0, y0, x1, y1, r)], rp, **kw)

    def circ(s, cx, cy, r, rp, **kw): return s.solid([('ell', cx - r, cy - r, cx + r, cy + r)], rp, **kw)

    def frr(s, x0, y0, x1, y1, r, col): s.flat([('rr', x0, y0, x1, y1, r)], col)

    def fcirc(s, cx, cy, r, col): s.flat([('ell', cx - r, cy - r, cx + r, cy + r)], col)

    def fpoly(s, pts, col): s.flat([('poly', pts)], col)

    def fline(s, pts, w, col): s.flat([('line', pts, w)], col)

    def sheet(s, pts, rp, at=.72):
        """flat sheet (4 corners TL,TR,BR,BL) with a hard 2-tone split on the right."""
        s.fpoly(pts, rp[1])
        u = lambda p, q, t: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        p1, p2 = u(pts[0], pts[1], at), u(pts[3], pts[2], at)
        s.fpoly([p1, pts[1], pts[2], p2], rp[0])

    def text(s, txt, x, y, size, col, path=HEI, index=0, anchor='la'):
        check_glyphs(txt, path, index)
        s.d.text((x * S, y * S), txt, font=font(size, path, index), fill=col, anchor=anchor)

    def text_w(s, txt, size, path=HEI, index=0):
        return s.d.textlength(txt, font=font(size, path, index)) / S


# ---------------------------------------------------------------- canvas + shadows
class Canvas:
    """Output image at supersampled resolution; shadows are cast onto it before layers are put."""

    def __init__(s, w, h, col):
        s.w, s.h = w, h; s.im = Image.new('RGB', (w * S, h * S), col); s.d = ImageDraw.Draw(s.im)

    def shade(s, mask, tint=TINT):
        dark = ImageChops.multiply(s.im, Image.new('RGB', s.im.size, tint))
        s.im = Image.composite(dark, s.im, mask); s.d = ImageDraw.Draw(s.im)

    def cast(s, layer, length, clip=None, tint=TINT):
        """hard 45-degree long shadow: silhouette swept `length` px down-right, one flat tone.
        clip = (x0, y0, x1, y1) region that may receive the shadow (e.g. the wall above the floor)."""
        m = layer.im.getchannel('A').point(lambda v: 255 if v > 110 else 0)
        n = int(length * S); acc = m; d = 1
        while d * 2 <= n + 1:
            acc = ImageChops.lighter(acc, _shift(acc, d, d)); d *= 2
        acc = ImageChops.lighter(acc, _shift(acc, n - (d - 1), n - (d - 1)))
        acc = ImageChops.subtract(acc, m)                     # never under the object itself
        if clip:
            c = Image.new('L', acc.size, 0)
            ImageDraw.Draw(c).rectangle([v * S for v in clip], fill=255)
            acc = ImageChops.multiply(acc, c)
        s.shade(acc, tint)

    def contact(s, cx, y, w, h=14, tint=(222, 206, 182)):
        m = Image.new('L', s.im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([(cx - w / 2) * S, (y - h / 2) * S, (cx + w / 2) * S, (y + h / 2) * S], h * S / 2, fill=255)
        s.shade(m, tint)

    def put(s, layer, at=(0, 0)):
        s.im.paste(layer.im, (at[0] * S, at[1] * S), layer.im)

    def final(s, grain=.07, seed=61):
        out = s.im.resize((s.w, s.h), Image.LANCZOS)
        if grain:
            random.seed(seed)
            n = Image.effect_noise(out.size, 18).convert('RGB')
            out = Image.blend(out, ImageChops.overlay(out, n), grain)
        return out


# ================================================================= COMPONENTS
# ---- AI agent --------------------------------------------------------------
POSES = ('idle', 'reach', 'think', 'cheer')


def robot(L, cx, base, pose='idle', k=1.0, hand=None, hand_l=None, look=0):
    """AI agent built from capsules. No face: a dark visor with one sensor bar.
    pose: idle | reach (right hand goes to `hand`) | think | cheer.  k = scale.
    look: -1..1 slides the sensor highlight toward where the agent is 'looking'.
    Returns dict with joint positions (hands, head box) for composing props."""
    u = lambda v: v * k
    lift = u(18) if pose == 'cheer' else 0
    b = base - lift
    shR, shL = (cx + u(92), b - u(262)), (cx - u(92), b - u(262))
    l1 = l2 = u(92)
    if pose == 'idle':
        tR, tL = (cx + u(124), b - u(92)), (cx - u(124), b - u(92))
        bendR, bendL = 1, -1
    elif pose == 'reach':
        tR = hand or (cx + u(250), b - u(330)); tL = hand_l or (cx - u(122), b - u(120))
        bendR, bendL = 1, 1; look = 1 if look == 0 else look
    elif pose == 'think':
        tR = (cx + u(126), b - u(392)); tL = (cx - u(120), b - u(120))
        bendR, bendL = 1, 1
    else:  # cheer
        tR, tL = (cx + u(188), b - u(430)), (cx - u(188), b - u(430))
        bendR, bendL = 1, -1
    eR, eL = ik(shR, tR, l1, l2, bendR), ik(shL, tL, l1, l2, bendL)

    def arm(sh, el, hd):
        L.solid([('line', [sh, el, hd], u(30))], NAVY, shade=.3, rim=0, short=u(30))

    # back arm first when it crosses behind the body
    arm(shL, eL, tL)
    for dx in (-1, 1):                                                # legs + feet
        fx = cx + dx * u(46)
        L.rr(fx - u(17), b - u(92), fx + u(17), b - u(18), u(10), NAVY, shade=.35, rim=0)
        if pose == 'cheer':
            L.rr(fx - u(34), b - u(30), fx + u(38), b, u(15), NAVY, shade=.3, rim=2.5)
        else:
            L.rr(fx - u(34), base - u(30), fx + u(38), base, u(15), NAVY, shade=.3, rim=2.5)
    L.rr(cx - u(66), b - u(108), cx + u(66), b - u(80), u(14), NAVY, shade=.3, rim=0)        # hip
    L.rr(cx - u(98), b - u(300), cx + u(98), b - u(94), u(50), TEAL, shade=.17, rim=4,
         spec=([(cx - u(70), b - u(256)), (cx - u(70), b - u(214))], u(10)))                 # body
    L.frr(cx - u(98), b - u(150), cx + u(98), b - u(136), 0, TEAL[0])                        # waist seam
    L.rr(cx - u(46), b - u(240), cx + u(46), b - u(176), u(14), CREAM, shade=.16, rim=0)       # chest status panel
    L.fcirc(cx - u(22), b - u(208), u(11), MUST[1] if pose == 'think' else TEAL[1])
    for i in range(2): L.frr(cx - u(4), b - u(218) + i * u(16), cx + u(30), b - u(211) + i * u(16), u(4), INK)
    L.rr(cx - u(28), b - u(326), cx + u(28), b - u(292), u(8), NAVY, shade=.3, rim=0)          # neck
    for dx in (-1, 1):                                                # ear pods
        L.rr(cx + dx * u(118) - u(16), b - u(432), cx + dx * u(118) + u(16), b - u(372), u(11), NAVY, shade=.3, rim=0)
    ax = cx + u(42)                                                   # antenna
    L.fline([(ax, b - u(462)), (ax + u(14), b - u(522))], u(10), NAVY[1])
    L.circ(ax + u(16), b - u(536), u(20), CORAL, shade=.3, rim=2.5,
           spec=([(ax + u(8), b - u(545)), (ax + u(9), b - u(546))], u(6)))
    L.rr(cx - u(114), b - u(474), cx + u(114), b - u(318), u(58), CREAM, shade=.26, rim=0,
         spec=([(cx - u(78), b - u(446)), (cx - u(40), b - u(458))], u(10)))               # head
    L.rr(cx - u(88), b - u(440), cx + u(88), b - u(352), u(42), NAVY, shade=.1, rim=0)        # visor
    vy = b - u(396)
    if pose == 'think':                                               # sensor: three slow dots
        for i in (-1, 0, 1): L.fcirc(cx + i * u(30), vy, u(9), MUST[2])
    elif pose == 'cheer':                                             # sensor at full brightness
        L.frr(cx - u(62), vy - u(9), cx + u(62), vy + u(9), u(9), TEAL[3])
    else:
        L.frr(cx - u(58), vy - u(7), cx + u(58), vy + u(7), u(7), TEAL[2])
        hx = cx + look * u(30)
        L.frr(hx - u(22), vy - u(5), hx + u(22), vy + u(5), u(5), TEAL[3])
    arm(shR, eR, tR)
    for p in (tL, tR): L.circ(p[0], p[1], u(24), NAVY, shade=.3, rim=2.5)                      # hands
    for p in (shL, shR): L.circ(p[0], p[1], u(19), NAVY, shade=.25, rim=0)                      # shoulders
    return {'handR': tR, 'handL': tL, 'head': (cx - u(114), b - u(474), cx + u(114), b - u(318)),
            'foot_y': base, 'w': u(240)}


def confetti(L, cx, cy, r, seed=3, n=9):
    rr_ = random.Random(seed); cols = [CORAL[1], MUST[1], TEAL[1], NAVY[2]]
    for i in range(n):
        a = -math.pi / 2 + (i - (n - 1) / 2) * (math.pi * 1.1 / n) + rr_.uniform(-.12, .12)
        d = r * rr_.uniform(.8, 1.1); x, y = cx + d * math.cos(a), cy + d * math.sin(a)
        c = cols[i % 4]; kind = i % 3
        if kind == 0: L.fcirc(x, y, 7, c)
        elif kind == 1:
            P = rot(x, y, rr_.uniform(0, 180)); L.fpoly([P(-11, -4), P(11, -4), P(11, 4), P(-11, 4)], c)
        else:
            P = rot(x, y, rr_.uniform(0, 120)); L.fpoly([P(0, -10), P(9, 6), P(-9, 6)], c)


def thought(L, x, y):
    """small thought bubble (two dots + round bubble with a '?')."""
    L.fcirc(x - 46, y + 62, 7, CREAM[1]); L.fcirc(x - 28, y + 40, 11, CREAM[1])
    L.circ(x, y, 34, CREAM, shade=.14, rim=0)
    L.text('?', x - 1, y + 1, 40, NAVY[1], NUM, NUM_HEAVY, anchor='mm')


# ---- note card --------------------------------------------------------------
def card(L, cx, cy, w=130, h=164, deg=0, kind='plain'):
    """note card: cream sheet + colour header band + text bars + hard split on the right.
    kind: plain (coral header) | wrong (coral header, struck line, cross badge) |
          verified (teal header, check badge)."""
    P = rot(cx, cy, deg)
    q = lambda a, b_, c, d: [P(a, b_), P(c, b_), P(c, d), P(a, d)]
    head = TEAL if kind == 'verified' else CORAL
    L.sheet(q(-w / 2, -h / 2, w / 2, h / 2), CREAM, at=.8)
    L.sheet(q(-w / 2, -h / 2, w / 2, -h / 2 + h * .19), head, at=.8)
    bars = (.78, .56, .70, .42)
    for i, lw in enumerate(bars):
        v = -h / 2 + h * .33 + i * h * .145
        L.fline([P(-w / 2 + w * .14, v), P(-w / 2 + w * .14 + w * .72 * lw, v)], max(5, h * .05), INK)
    if kind == 'wrong':
        v = -h / 2 + h * .33 + h * .145
        L.fline([P(-w / 2 + w * .1, v), P(-w / 2 + w * .1 + w * .55, v)], max(4, h * .035), CORAL[1])
        badge(L, *P(w / 2 - w * .08, h / 2 - h * .06), r=h * .16, ok=False)
    elif kind == 'verified':
        badge(L, *P(w / 2 - w * .08, h / 2 - h * .06), r=h * .16, ok=True)


# ---- check & cross ----------------------------------------------------------
def badge(L, cx, cy, r=40, ok=True):
    """round badge: teal check or coral cross, cream round-capped strokes."""
    L.circ(cx, cy, r, TEAL if ok else CORAL, shade=.22, rim=2.5 if r > 30 else 0)
    w = max(4, r * .22)
    if ok: L.fline([(cx - r * .42, cy + r * .02), (cx - r * .1, cy + r * .34), (cx + r * .44, cy - r * .3)], w, CREAM[1])
    else:
        a = r * .34
        L.fline([(cx - a, cy - a), (cx + a, cy + a)], w, CREAM[1]); L.fline([(cx - a, cy + a), (cx + a, cy - a)], w, CREAM[1])


# ---- knowledge base: bookshelf with a card drawer ---------------------------
def books_row(L, x0, x1, ry0, ry1, rnd, lean=True, simple=False):
    x = x0 + 10; i = 0; last = None; leaned = False; coral = False   # max one coral spine per row
    rh = ry1 - ry0
    while True:
        bw = rnd.choice((44, 52, 60) if simple else (24, 28, 32, 36, 42)); bh = rh - rnd.choice((18, 36, 54) if simple else (10, 18, 26, 36))
        if x + bw > x1 - 10: break
        c = rnd.choice([p for p in SPINES if p is not last and not (p is CORAL and coral)]); last = c
        coral = coral or c is CORAL
        if lean and not leaned and i == 3 and x + bw + 30 < x1 - 10:
            P = rot(x + bw / 2 + 12, ry1 - bh / 2 + 1, 12)
            L.sheet([P(-bw / 2, -bh / 2), P(bw / 2, -bh / 2), P(bw / 2, bh / 2), P(-bw / 2, bh / 2)], c, at=.64)
            x += bw + 28; leaned = True
        else:
            L.sheet([(x, ry1 - bh), (x + bw, ry1 - bh), (x + bw, ry1), (x, ry1)], c, at=.64)
            band = NAVY[1] if c is not NAVY else MUST[1]
            if bw >= 32 and not simple:
                L.fpoly([(x + 6, ry1 - bh + 14), (x + bw * .64 - 2, ry1 - bh + 14), (x + bw * .64 - 2, ry1 - bh + 24), (x + 6, ry1 - bh + 24)], band)
            x += bw + 4
        i += 1


def kb_shelf(L, x0, y0, x1, y1, insert=None, seed=7, slot_frac=.52, card_w=118, fracs=(.3, .4, .3), drawer=1, front=.44, simple=False):
    """knowledge base: navy bookshelf; the middle row is a card-catalogue drawer pulled out,
    full of index cards with ONE empty lit slot. `insert(L, slot)` is called after the drawer
    interior and before the drawer front, so whatever it draws (the new card) is visibly
    *inside* the drawer - its lower part hidden by the drawer front.
    slot = dict(x=centre x, front=drawer-front top y, w=slot width). Returns slot."""
    rnd = random.Random(seed)
    for fx in (x0 + 22, x1 - 62):                                     # feet
        L.rr(fx, y1 - 8, fx + 40, y1 + 22, 8, NAVY, shade=.3, rim=0)
    L.rr(x0, y0, x1, y1, 22, NAVY, shade=.05, rim=4)                    # carcass
    L.rr(x0 - 16, y0 - 24, x1 + 16, y0 + 12, 12, NAVY, shade=.28, rim=4)   # top board
    pad, gap = 24, 20
    inner = y1 - y0 - 30 - pad
    hs = [inner * f - gap * 2 / 3 for f in fracs]
    ry = y0 + 30; rows = []
    for h in hs: rows.append((ry, ry + h)); ry += h + gap
    ix0, ix1 = x0 + pad, x1 - pad
    for ry0, ry1 in rows:                                             # compartments
        L.frr(ix0, ry0, ix1, ry1, 10, HOLE)
        L.frr(ix0, ry0, ix1, ry0 + 12, 6, (10, 15, 30))
    for i, (a, b_) in enumerate(rows):
        if i != drawer: books_row(L, ix0, ix1, a + 14, b_, rnd, lean=not simple, simple=simple)
    # ---- drawer row
    ry0, ry1 = rows[drawer]
    front_top = ry0 + (ry1 - ry0) * front
    sx = ix0 + (ix1 - ix0) * slot_frac; sw = card_w + 22
    L.frr(sx - sw / 2, ry0 + 14, sx + sw / 2, front_top + 4, 6, MUST[3])     # lit slot backing
    x = ix0 + 14; j = 0                                               # index cards, tops only
    while x < ix1 - 30:
        if x + 46 > sx - sw / 2 and x < sx + sw / 2: x = sx + sw / 2 + 6; continue
        cw = rnd.choice((40, 46, 52)); top = front_top - rnd.choice((22, 30, 38))
        if x + cw > ix1 - 12: break
        L.sheet([(x, top), (x + cw, top), (x + cw, front_top + 4), (x, front_top + 4)], CREAM, at=.7)
        if j % 2 == 0:
            tc = [TEAL, CORAL, MUST][j // 2 % 3]
            L.frr(x + 8, top - 10, x + 24, top + 2, 3, tc[1])
        x += cw + 4; j += 1
    slot = {'x': sx, 'front': front_top, 'w': sw, 'row': (ry0, ry1)}
    if insert: insert(L, slot)
    # drawer front, pulled out: wider than the opening, drops a flat shadow on the row below
    fx0, fx1, fy1 = ix0 - 12, ix1 + 12, ry1 + 18
    L.frr(fx0 + 8, fy1 - 2, fx1 - 4, fy1 + 12, 6, (12, 18, 36, 255))
    L.rr(fx0, front_top, fx1, fy1, 10, MUST, shade=.14, rim=3.5, short=fy1 - front_top)
    mx = (fx0 + fx1) / 2; my = (front_top + fy1) / 2
    L.rr(mx - 50, my - 28, mx + 50, my + 2, 6, CREAM, shade=.18, rim=0)           # label holder
    L.fline([(mx - 32, my - 13), (mx + 22, my - 13)], 6, INK)
    L.rr(mx - 34, my + 12, mx + 34, my + 26, 7, NAVY, shade=.3, rim=0)             # pull handle
    return slot


# ---- database tower ---------------------------------------------------------
def db_tower(L, cx, base, w=170, n=3, disc=64, gap=12):
    """stacked cylinders: body + lighter elliptic top, one status light per disc."""
    eh = w * .28
    for i in range(n):
        yb = base - i * (disc + gap); yt = yb - disc
        L.solid([('rr', cx - w / 2, yt, cx + w / 2, yb - eh / 2, 0), ('ell', cx - w / 2, yb - eh, cx + w / 2, yb)],
                NAVY, shade=.12, rim=0, short=w * .5)
        L.flat([('ell', cx - w / 2, yt - eh / 2, cx + w / 2, yt + eh / 2)], NAVY[2] + (255,))
        L.flat([('ell', cx - w / 2 + 10, yt - eh / 2 + 6, cx + w / 2 - 10, yt + eh / 2 - 4)], NAVY[3] + (255,)) if i == n - 1 else None
        ly = yt + disc * .55
        L.fcirc(cx - w * .3, ly, 7, TEAL[2] if i != 1 else CORAL[1])
        L.fline([(cx - w * .16, ly), (cx + w * .22, ly)], 6, NAVY[2])


# ---- folder ------------------------------------------------------------------
def folder(L, x0, y0, w=210, h=160):
    x1, y1 = x0 + w, y0 + h
    L.solid([('rr', x0, y0 + 16, x1, y1, 14), ('rr', x0, y0, x0 + w * .42, y0 + 40, 12)], MUST, shade=.0, rim=0)
    L.frr(x0, y0 + 16, x1, y1, 14, MUST[0])
    L.sheet([(x0 + 18, y0 + 30), (x1 - 26, y0 + 22), (x1 - 22, y1 - 20), (x0 + 22, y1 - 14)], CREAM, at=.82)
    L.fline([(x0 + 40, y0 + 52), (x0 + 120, y0 + 48)], 6, INK)
    L.solid([('poly', [(x0 - 6, y0 + 58), (x1 + 6, y0 + 58), (x1, y1), (x0, y1)])], MUST, shade=.14, rim=3.5, short=h * .6)


# ---- big number plate ---------------------------------------------------------
def number_plate(L, x0, y0, num='61%', label='', w=360, h=230, fill=.61, col=CORAL, size=128):
    """cream slab plate: big Avenir Heavy number + progress capsule + STHeiti label."""
    L.frr(x0 + 10, y0 + 12, x0 + w + 10, y0 + h + 12, 22, BG[0])      # flat slab shadow
    L.frr(x0, y0, x0 + w, y0 + h, 22, CREAM[1])
    L.text(num, x0 + 30, y0 + 14, size, col[1], NUM, NUM_HEAVY)
    big_bar(L, x0 + 34, y0 + h - 76, w - 68, 22, fill, col)
    if label: L.text(label, x0 + 34, y0 + h - 44, 26, NAVY[2])


def big_bar(L, x, y, w, h, fill, col=CORAL, track=None):
    L.frr(x, y, x + w, y + h, h / 2, track or BG[0])
    L.rr(x, y, x + max(h, w * fill), y + h, h / 2, col, shade=.3, rim=0, short=h)


# ---- bar chart -----------------------------------------------------------------
def bar_chart(L, x0, base, vals=(.38, .53, .61, .46), bw=46, gap=26, hmax=230, hi=2, labels=None):
    for i, v in enumerate(vals):
        x = x0 + i * (bw + gap); top = base - v * hmax
        c = CORAL if i == hi else (TEAL if i % 2 else NAVY)
        L.solid([('rr', x, top, x + bw, base + bw / 2, bw / 2)], c, shade=.2, rim=3, short=bw)
        if labels:
            L.text(labels[i], x + bw / 2, top - 12, 24, c[1] if i == hi else NAVY[2], NUM, NUM_BOLD, anchor='ms')
    L.frr(x0 - 16, base, x0 + len(vals) * (bw + gap) - gap + 16, base + 30, 0, (0, 0, 0, 0))
    # baseline masks the round bottoms: draw it in the plate colour by the caller if wanted
    L.frr(x0 - 16, base, x0 + len(vals) * (bw + gap) - gap + 16, base + 8, 4, NAVY[1])


# ---- arrows ---------------------------------------------------------------------
def arrow(L, pts, w=18, col=CORAL[1], head=1.0):
    """round-capped polyline / curve + solid triangle head aligned to the last segment."""
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    a = math.atan2(by - ay, bx - ax); hl, hw = w * 2.4 * head, w * 1.7 * head
    stem_end = (bx - math.cos(a) * hl * .6, by - math.sin(a) * hl * .6)
    L.fline(pts[:-1] + [stem_end], w, col)
    P = rot(bx, by, math.degrees(a))
    L.fpoly([P(0, 0), P(-hl, -hw), P(-hl * .78, 0), P(-hl, hw)], col)
    L.fpoly([P(4, 0), P(-hl + 2, -hw + 2), P(-hl + 2, hw - 2)], col)


# ---- path / map -----------------------------------------------------------------
def pin(L, cx, tip, r=26, col=CORAL):
    cy = tip - r * 2.1
    L.solid([('ell', cx - r, cy - r, cx + r, cy + r), ('poly', [(cx - r * .82, cy + r * .5), (cx + r * .82, cy + r * .5), (cx, tip)])],
            col, shade=.22, rim=0, short=r * 2)
    L.fcirc(cx, cy, r * .4, CREAM[1])


def map_tile(L, x0, y0, w=300, h=230):
    x1, y1 = x0 + w, y0 + h
    L.frr(x0 + 10, y0 + 12, x1 + 10, y1 + 12, 20, BG[0])
    L.frr(x0, y0, x1, y1, 20, rgb('E9E2CF'))
    L.frr(x0 + 18, y0 + 18, x0 + 110, y0 + 92, 12, TEAL[2])            # park
    L.frr(x0 + 200, y0 + 130, x1 - 18, y1 - 18, 12, rgb('9FB4DE'))     # water
    L.frr(x0 + 140, y0 + 18, x1 - 18, y0 + 92, 12, rgb('DDD3BC'))      # block
    L.fline([(x0, y0 + 112), (x1, y0 + 112)], 16, CREAM[1])
    L.fline([(x0 + 124, y0), (x0 + 124, y1)], 16, CREAM[1])
    pts = bez((x0 + 40, y1 - 30), (x0 + 120, y0 + 60), (x1 - 56, y0 + 70), 9)
    for i, (x, y) in enumerate(pts[:-1]): L.fcirc(x, y, 5 + i * .4, CORAL[1])
    pin(L, x1 - 56, y0 + 74, r=22)
    L.fcirc(x0 + 40, y1 - 30, 10, NAVY[1])


# ---- timeline ---------------------------------------------------------------------
def timeline(L, x0, y, w, labels, cur=1):
    n = len(labels); step = w / (n - 1)
    L.fline([(x0, y), (x0 + w, y)], 12, BG[0])
    L.fline([(x0, y), (x0 + step * cur, y)], 12, NAVY[2])
    for i, t in enumerate(labels):
        x = x0 + i * step
        if i == cur:
            L.fcirc(x, y, 26, CORAL[3]); L.circ(x, y, 17, CORAL, shade=.25, rim=0)
        else:
            L.circ(x, y, 15, NAVY if i < cur else ramp('D2C4AA', 'DCCFB6', 'E6DCC8', 'F0E9DC'), shade=.25, rim=0)
        L.text(t, x, y + 50, 24, NAVY[1] if i == cur else NAVY[2], anchor='mt')


# ---- dialog box ----------------------------------------------------------------------
def dialog(L, x0, y0, w, h, lines, tail_x=None, size=34):
    tail_x = tail_x or x0 + 70
    for dx, dy, col in ((10, 12, BG[0]), (0, 0, CREAM[1])):
        L.frr(x0 + dx, y0 + dy, x0 + w + dx, y0 + h + dy, 22, col)
        L.fpoly([(tail_x - 18 + dx, y0 + h - 2 + dy), (tail_x + 22 + dx, y0 + h - 2 + dy), (tail_x - 10 + dx, y0 + h + 34 + dy)], col)
    for i, t in enumerate(lines):
        L.text(t, x0 + 34, y0 + 28 + i * size * 1.5, size, NAVY[1])


# ---- chapter tag ----------------------------------------------------------------------
def chapter_tag(L, x, y, num, title, size=64):
    """coral rule + numbered navy pill + STHeiti heading."""
    L.frr(x, y, x + 72, y + 12, 6, CORAL[1])
    nw = L.text_w(num, 26, NUM, NUM_HEAVY) + 34
    L.frr(x, y + 34, x + nw, y + 34 + 40, 20, NAVY[1])
    L.text(num, x + nw / 2, y + 54, 26, MUST[2], NUM, NUM_HEAVY, anchor='mm')
    L.text(title, x - 4, y + 92, size, NAVY[1])


def plant(L, cx, base, k=1.0):
    u = lambda v: v * k
    for deg, ln in ((-40, 78), (-10, 100), (22, 86), (50, 60)):
        P = rot(cx, base - u(34), deg - 90)
        L.fpoly([P(0, 0), P(u(ln) * .5, -u(17)), P(u(ln), 0), P(u(ln) * .5, u(17))], TEAL[1])
        L.fpoly([P(0, 0), P(u(ln), 0), P(u(ln) * .5, u(17))], TEAL[0])
    L.rr(cx - u(34), base - u(42), cx + u(34), base, u(10), CORAL, shade=.3, rim=3)


# ================================================================= SHEET
def _cell(sheet, x, y, w, h, title, sub, draw, shadow=60, ground=None):
    """one panel on the sheet: own layer, own shadow, captions below."""
    P = Layer(sheet.w, sheet.h)
    P.frr(x, y, x + w, y + h, 18, BG[2])
    sheet.put(P)
    L = Layer(sheet.w, sheet.h)
    draw(L, x, y, w, h)
    g = ground if ground is not None else h - 40
    if ground is not None:
        F = Layer(sheet.w, sheet.h); F.frr(x, y + g, x + w, y + h, 0, FLOOR[1])
        F.frr(x, y + h - 18, x + w, y + h, 0, BG[2]); sheet.put(F)
        F2 = Layer(sheet.w, sheet.h); F2.frr(x, y + g, x + w, y + h - 18, 0, (0, 0, 0, 0))
    if shadow:
        sheet.cast(L, shadow, clip=(x, y, x + w, y + (g if ground is not None else h)))
    sheet.put(L)
    T = Layer(sheet.w, sheet.h)
    T.text(title, x + 4, y + h + 14, 28, NAVY[1])
    if sub: T.text(sub, x + 4, y + h + 52, 20, rgb('8A8574'))
    sheet.put(T)


def render_sheet(path):
    W = 1800; H = 3080
    sh = Canvas(W, H, BG[1])
    T = Layer(W, H)
    T.text('扁平向量 元件表', 60, 52, 54, NAVY[1])
    T.text('無描邊｜左上單一光源：新月暗面＋亮緣＋一條高光｜紙張用硬切雙色｜投影＝短距硬邊偏移、單一乘色', 62, 128, 24, rgb('7D7868'))
    sh.put(T)
    M = 60
    # row 1: four robot poses
    cw, ch, y = 405, 640, 200
    poses = [('idle', '機器人：待命', '感測燈置中，手自然下垂'),
             ('reach', '機器人：伸手放置', '感測燈偏向動作方向'),
             ('think', '機器人：思考', '護目鏡跑三點、核心轉芥黃'),
             ('cheer', '機器人：慶祝', '雙手上舉、離地、彩紙')]
    for i, (pz, t, s_) in enumerate(poses):
        x = M + i * (cw + 25)

        def d(L, x, y, w, h, pz=pz):
            cx = x + w / 2 - (40 if pz == 'reach' else 0)
            if pz == 'reach': card(L, cx + 238, y + h - 120 - 380, 108, 138, deg=-8)
            r = robot(L, cx, y + h - 62, pz, k=.98)
            if pz == 'think': thought(L, cx + 140, y + 70)
            if pz == 'cheer': confetti(L, cx, y + h - 360, 230)
        _cell(sh, x, y, cw, ch, t, s_, d, shadow=22, ground=ch - 62)
    # row 2: cards, folder, database, plate
    y = 980; ch = 330
    cards = [('plain', '筆記卡', '珊瑚標頭、右側硬切暗面'), ('wrong', '筆記卡：寫錯', '劃線＋珊瑚叉章'),
             ('verified', '筆記卡：已驗證', '青綠標頭＋勾章')]
    cw2 = 265
    for i, (kd, t, s_) in enumerate(cards):
        x = M + i * (cw2 + 22)
        _cell(sh, x, y, cw2, ch, t, s_, lambda L, x, y, w, h, kd=kd: card(L, x + w / 2 - 6, y + h / 2 + 4, 136, 172, deg=-6 if kd == 'plain' else 0, kind=kd), shadow=16)
    x = M + 3 * (cw2 + 22)
    _cell(sh, x, y, cw2, ch, '資料夾', '後片暗一階、前片斜切', lambda L, x, y, w, h: folder(L, x + 30, y + 80, 200, 170), shadow=16)
    x += cw2 + 22
    _cell(sh, x, y, 520, ch, '大數字牌', '奶油厚片＋進度膠囊', lambda L, x, y, w, h: number_plate(L, x + 70, y + 40, '61%', '筆記已歸檔', w=370, h=240, size=120), shadow=0)
    # row 3: knowledge base, db tower, chart, check/cross, arrows
    y = 1430; ch = 720

    def kb(L, x, y, w, h):
        def ins(L, slot):
            top = slot['row'][0] + 22
            card(L, slot['x'], top + 66, 100, 132, deg=0)
            cx = slot['x'] + 50 + 24
            for j in range(2): L.fline([(cx - 10, top + 16 + j * 26), (cx, top + 26 + j * 26), (cx + 10, top + 16 + j * 26)], 6, MUST[2])
        kb_shelf(L, x + 50, y + 130, x + w - 50, y + h - 70, insert=ins, card_w=100, slot_frac=.3,
                 fracs=(.29, .29, .42), drawer=2, front=.6)
        plant(L, x + w - 110, y + 106, k=.85)
    _cell(sh, M, y, 500, ch, '知識庫書櫃', '拉出的卡片抽屜擋住新卡下半＝放進去', kb, shadow=24, ground=ch - 50)
    _cell(sh, M + 525, y, 300, ch, '資料庫塔', '三段圓柱、頂面亮一階', lambda L, x, y, w, h: db_tower(L, x + w / 2, y + h - 80, 170), shadow=20, ground=ch - 50)

    def chart(L, x, y, w, h):
        bar_chart(L, x + 70, y + 300, labels=('38', '53', '61', '46'))
    _cell(sh, M + 850, y, 420, 340, '長條圖', '膠囊柱、最高那根用珊瑚', chart, shadow=12)

    def checks(L, x, y, w, h):
        badge(L, x + 120, y + 170, 70, True); badge(L, x + 290, y + 170, 70, False)
    _cell(sh, M + 1295, y, 385, 340, '勾與叉', '圓章＋奶油圓頭粗線', checks, shadow=12)

    def arrows(L, x, y, w, h):
        arrow(L, [(x + 50, y + 90), (x + 330, y + 90)], 20, CORAL[1])
        arrow(L, bez((x + 60, y + 250), (x + 200, y + 120), (x + 340, y + 250), 24), 16, NAVY[1])
        arrow(L, [(x + 420, y + 270), (x + 420, y + 100)], 18, TEAL[1])
        arrow(L, [(x + 520, y + 100), (x + 700, y + 100), (x + 700, y + 260)], 16, MUST[1])
    _cell(sh, M + 850, y + 420, 830, 300, '箭頭', '圓頭粗線＋實心三角頭，可折、可彎', arrows, shadow=10)
    # row 4: map, timeline, dialog, chapter tag
    y = 2290
    _cell(sh, M, y, 400, 330, '路徑與地圖', '平面色塊街區、珊瑚點線、地圖釘', lambda L, x, y, w, h: map_tile(L, x + 46, y + 46, 300, 236), shadow=0)

    def tl(L, x, y, w, h): timeline(L, x + 60, y + 130, w - 120, ['收集', '整理', '驗證', '上線'], cur=2)
    _cell(sh, M + 425, y, 560, 330, '時間軸', '已走過用深藍、目前節點珊瑚加光圈', tl, shadow=0)

    def dg(L, x, y, w, h): dialog(L, x + 40, y + 50, w - 90, 170, ['它把筆記放進', '知識庫的對的格子。'])
    _cell(sh, M + 1010, y, 670, 330, '對話框字幕', '奶油圓角、厚片陰影、深藍黑體', dg, shadow=0)
    y = 2770

    def tag(L, x, y, w, h): chapter_tag(L, x + 50, y + 40, '02', '知識庫', 60)
    _cell(sh, M, y, 560, 230, '章節標示', '珊瑚短線＋編號膠囊＋黑體標題', tag, shadow=0)

    def pal(L, x, y, w, h):
        for i, (nm, rp) in enumerate((('NAVY', NAVY), ('TEAL', TEAL), ('CORAL', CORAL), ('MUST', MUST), ('CREAM', CREAM), ('BG', BG))):
            xx = x + 40 + i * 172
            for j in range(4): L.frr(xx, y + 40 + j * 34, xx + 150, y + 40 + j * 34 + 30, 6, rp[3 - j])
            L.text(nm, xx, y + 184, 20, NAVY[2], NUM, NUM_DEMI)
    _cell(sh, M + 585, y, 1095, 230, '色票', '每色四階：高光／亮面／主色／陰影', pal, shadow=0)
    sh.final().save(path)


if __name__ == '__main__':
    render_sheet(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'components.png'))
