#!/usr/bin/env python3
"""Style catalog sample: blueprint (original artwork, PIL only).

Technique encoded here:
  - two ink layers only (white line ink + one amber accent ink) on blue paper
  - four line weights (outline / part / detail / hairline) and drafted corner overshoot
  - line types: solid, hidden (dashed), centre line (long-short), section hatch
  - dimension lines with extension lines and slim arrowheads
  - paper: mottled blue, fold creases, two-level grid, sheet border with zone ticks
Everything is drawn at 2x and downsampled for clean anti-aliased lines.
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, S = 1080, 1350, 2
HERE = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(61)

F_ZH = ('/System/Library/Fonts/STHeiti Medium.ttc', 0)
F_NUM = ('/System/Library/Fonts/Menlo.ttc', 1)
F_LBL = ('/System/Library/Fonts/Menlo.ttc', 0)

PAPER = (22, 66, 134)
PAPER_DARK = (11, 38, 90)
LINE = (238, 245, 255)
ACCENT = (255, 198, 96)

# line weights in final pixels
OUTLINE, PART, DETAIL, HAIR = 4.6, 3.0, 1.8, 1.1

INK = Image.new('L', (W * S, H * S), 0)   # white line ink
AMB = Image.new('L', (W * S, H * S), 0)   # amber accent ink


def font(spec, size): return ImageFont.truetype(spec[0], int(size * S), index=spec[1])
def sc(p): return (p[0] * S, p[1] * S)
def wpx(w): return max(1, int(round(w * S)))


# ---------- line primitives ----------
def ln(layer, p0, p1, w=DETAIL, over=0, v=255):
    """Straight line with round caps; `over` extends both ends (drafted overshoot)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0) or 1
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    a = (x0 - ux * over, y0 - uy * over); b = (x1 + ux * over, y1 + uy * over)
    d = ImageDraw.Draw(layer); ww = wpx(w)
    d.line([sc(a), sc(b)], fill=v, width=ww)
    if ww > 2:
        r = ww / 2
        for p in (a, b): d.ellipse([p[0] * S - r, p[1] * S - r, p[0] * S + r, p[1] * S + r], fill=v)


def path(layer, pts, w=DETAIL, closed=False, over=0):
    pts = list(pts)
    if closed: pts = pts + [pts[0]]
    for a, b in zip(pts, pts[1:]): ln(layer, a, b, w, over)


def rect(layer, x0, y0, x1, y1, w=DETAIL, over=0):
    path(layer, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], w, True, over)


def rrect(layer, x0, y0, x1, y1, r, w=DETAIL):
    ImageDraw.Draw(layer).rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, outline=255, width=wpx(w))


def circle(layer, c, r, w=DETAIL, fill=None):
    box = [(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S]
    ImageDraw.Draw(layer).ellipse(box, outline=255 if fill is None else None, fill=fill, width=wpx(w))


def arc(layer, c, r, a0, a1, w=DETAIL):
    box = [(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S]
    ImageDraw.Draw(layer).arc(box, a0, a1, fill=255, width=wpx(w))


def patterned(layer, p0, p1, pattern, w=HAIR):
    """pattern = (on, off, on, off, ...) lengths in px. Hidden line: (10, 6). Centre line: (22, 5, 4, 5)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    t, k = 0, 0
    while t < L:
        seg = pattern[k % len(pattern)]
        if k % 2 == 0:
            e = min(L, t + seg)
            ln(layer, (x0 + ux * t, y0 + uy * t), (x0 + ux * e, y0 + uy * e), w)
        t += seg; k += 1


HIDDEN = (9, 6)
CENTRE = (24, 5, 4, 5)


def centre_mark(layer, c, r):
    patterned(layer, (c[0] - r, c[1]), (c[0] + r, c[1]), CENTRE, HAIR)
    patterned(layer, (c[0], c[1] - r), (c[0], c[1] + r), CENTRE, HAIR)


def arrow(layer, tip, direction, length=17, half=4.2):
    ux, uy = direction
    L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
    bx, by = tip[0] - ux * length, tip[1] - uy * length
    ImageDraw.Draw(layer).polygon([sc(tip), sc((bx - uy * half, by + ux * half)), sc((bx + uy * half, by - ux * half))], fill=255)


def hatch_mask(layer, mask, gap=9, w=HAIR, v=255):
    """45-degree section hatch clipped to an L mask (same size as the layer)."""
    box = mask.getbbox()
    if not box: return
    x0, y0, x1, y1 = box
    h = Image.new('L', layer.size, 0); d = ImageDraw.Draw(h)
    span = y1 - y0
    c = x0 - span
    while c < x1:
        d.line([(c, y0), (c + span, y1)], fill=v, width=wpx(w)); c += gap * S
    layer.paste(ImageChops.lighter(layer, ImageChops.multiply(h, mask)))


def hatch_poly(layer, poly, gap=9, w=HAIR, holes=()):
    m = Image.new('L', layer.size, 0); d = ImageDraw.Draw(m)
    d.polygon([sc(p) for p in poly], fill=255)
    for hpoly in holes: d.polygon([sc(p) for p in hpoly], fill=0)
    hatch_mask(layer, m, gap, w)


def dim(layer, p0, p1, off, label=None, size=17):
    """Dimension between object points p0-p1, pushed out by vector `off`."""
    L = math.hypot(*off); ox, oy = off[0] / L, off[1] / L
    a = (p0[0] + off[0], p0[1] + off[1]); b = (p1[0] + off[0], p1[1] + off[1])
    for p, q in ((p0, a), (p1, b)):
        ln(layer, (p[0] + ox * 7, p[1] + oy * 7), (q[0] + ox * 9, q[1] + oy * 9), HAIR)
    ln(layer, a, b, HAIR)
    arrow(layer, a, (a[0] - b[0], a[1] - b[1])); arrow(layer, b, (b[0] - a[0], b[1] - a[1]))
    if label:
        f = font(F_LBL, size); d = ImageDraw.Draw(layer)
        mx, my = (a[0] + b[0]) / 2 * S, (a[1] + b[1]) / 2 * S
        l, t, r, bt = d.textbbox((mx, my), label, font=f, anchor='mm')
        d.rectangle([l - 8 * S, t - 4 * S, r + 8 * S, bt + 4 * S], fill=0)
        d.text((mx, my), label, font=f, fill=255, anchor='mm')


# ---------- paper ----------
def noise_tile(n=256):
    return Image.frombytes('L', (n, n), bytes(rng.getrandbits(8) for _ in range(n * n)))


def tiled(tile, size):
    out = Image.new('L', size)
    for y in range(0, size[1], tile.size[1]):
        for x in range(0, size[0], tile.size[0]): out.paste(tile, (x, y))
    return out


def make_paper():
    base = Image.new('RGB', (W, H), PAPER)
    # vignette: darker toward the corners
    vig = Image.radial_gradient('L').resize((int(W * 1.5), int(H * 1.5))).crop((W // 4, H // 4, W // 4 + W, H // 4 + H))
    base = Image.composite(Image.new('RGB', (W, H), PAPER_DARK), base, vig.point(lambda v: int(max(0, v - 70) * 1.0)))
    # blotchy mottling (large) + fine grain (small)
    blot = noise_tile(64).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))
    base = ImageChops.multiply(base, Image.merge('RGB', [blot.point(lambda v: 205 + v * 50 // 255)] * 3))
    grain = tiled(noise_tile(256), (W, H))
    base = ImageChops.multiply(base, Image.merge('RGB', [grain.point(lambda v: 236 + v * 19 // 255)] * 3))
    # grid: minor 30 px, major 150 px
    g = Image.new('L', (W, H), 0); d = ImageDraw.Draw(g)
    for x in range(0, W, 30): d.line([(x, 0), (x, H)], fill=64 if x % 150 == 0 else 26)
    for y in range(0, H, 30): d.line([(0, y), (W, y)], fill=64 if y % 150 == 0 else 26)
    base = Image.composite(Image.new('RGB', (W, H), (150, 190, 240)), base, g)
    # fold creases: a light edge with a dark edge next to it
    c = Image.new('L', (W, H), 0); d = ImageDraw.Draw(c)
    d.line([(W * .5, 0), (W * .5, H)], fill=40, width=2); d.line([(0, H * .5), (W, H * .5)], fill=34, width=2)
    base = Image.composite(Image.new('RGB', (W, H), (190, 215, 250)), base, c.filter(ImageFilter.GaussianBlur(1.2)))
    c = Image.new('L', (W, H), 0); d = ImageDraw.Draw(c)
    d.line([(W * .5 + 3, 0), (W * .5 + 3, H)], fill=60, width=3); d.line([(0, H * .5 + 3), (W, H * .5 + 3)], fill=50, width=3)
    base = Image.composite(Image.new('RGB', (W, H), PAPER_DARK), base, c.filter(ImageFilter.GaussianBlur(2)))
    return base


# ---------- components ----------
FLOOR = 1000
SLOT = {}


def sheet_border():
    rect(INK, 30, 30, W - 30, H - 30, PART)
    rect(INK, 42, 42, W - 42, H - 42, HAIR)
    for x in range(150, W - 60, 150): ln(INK, (x, 30), (x, 42), HAIR); ln(INK, (x, H - 42), (x, H - 30), HAIR)
    for y in range(150, H - 60, 150): ln(INK, (30, y), (42, y), HAIR); ln(INK, (W - 42, y), (W - 30, y), HAIR)


def heading():
    d = ImageDraw.Draw(INK)
    circle(INK, (104, 128), 18, DETAIL); centre_mark(INK, (104, 128), 30)
    d.text((142 * S, 128 * S), '知識庫', font=font(F_ZH, 78), fill=255, anchor='lm')
    ln(INK, (84, 186), (470, 186), PART); ln(INK, (84, 194), (470, 194), HAIR)
    for k in range(0, 13):
        x = 84 + k * 32.2
        ln(INK, (x, 194), (x, 204 if k % 4 else 212), HAIR)


def big_number():
    """Outlined numerals; the lower 61% of each glyph is section-hatched."""
    f = font(F_NUM, 250); pos = (78 * S, 232 * S)
    solid = Image.new('L', INK.size, 0); ImageDraw.Draw(solid).text(pos, '61%', font=f, fill=255)
    l, t, r, b = solid.getbbox()
    edge = Image.new('L', INK.size, 0)
    ImageDraw.Draw(edge).text(pos, '61%', font=f, fill=0, stroke_width=wpx(2.2), stroke_fill=255)
    cut = t + (b - t) * (1 - .61)
    lower = solid.copy(); ImageDraw.Draw(lower).rectangle([0, 0, INK.size[0], cut], fill=0)
    hatch_mask(INK, lower, gap=8, w=HAIR, v=215)
    INK.paste(ImageChops.lighter(INK, edge))
    L, T, R, B = l / S, t / S, r / S, b / S; C = cut / S
    # level line at 61% in amber, running out to the gauge
    patterned(AMB, (L - 22, C), (R + 30, C), CENTRE, DETAIL)
    arrow(AMB, (L - 4, C), (1, 0), 15, 5)
    # height dimension on the right
    dim(INK, (R + 4, T), (R + 4, B), (46, 0))
    ln(AMB, (R + 40, C), (R + 60, C), PART)
    return (L, T, R, B, C)


def gauge(c, r):
    """Dial: ticks every 10%, amber arc for 61%."""
    circle(INK, c, r, PART); circle(INK, c, r - 26, HAIR)
    centre_mark(INK, c, r + 22)
    for k in range(20):
        a = math.radians(-90 + k * 18); r0 = r - (16 if k % 2 == 0 else 9)
        ln(INK, (c[0] + math.cos(a) * r0, c[1] + math.sin(a) * r0), (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r), DETAIL if k % 2 == 0 else HAIR)
    a1 = -90 + 360 * .61
    box = [(c[0] - r + 13) * S, (c[1] - r + 13) * S, (c[0] + r - 13) * S, (c[1] + r - 13) * S]
    ImageDraw.Draw(AMB).arc(box, -90, a1, fill=255, width=wpx(13))
    e = math.radians(a1)
    ln(AMB, c, (c[0] + math.cos(e) * (r + 16), c[1] + math.sin(e) * (r + 16)), DETAIL)
    circle(INK, c, 7, DETAIL); circle(AMB, c, 3.5, 1, fill=255)


PHANTOM = (26, 5, 4, 5, 4, 5)


def text(layer, xy, s, size=15, anchor='lm', spec=F_LBL):
    ImageDraw.Draw(layer).text((xy[0] * S, xy[1] * S), s, font=font(spec, size), fill=255, anchor=anchor)


def phantom_circle(layer, c, r, w=HAIR):
    """Detail boundary: a circle in phantom (long-short-short) line."""
    n = int(2 * math.pi * r / 6); k = 0; t = 0.0
    circ = 2 * math.pi * r
    while t < circ:
        seg = PHANTOM[k % len(PHANTOM)]
        if k % 2 == 0:
            a0, a1 = t / r, min(circ, t + seg) / r
            arc(layer, c, r, math.degrees(a0), math.degrees(a1), w)
        t += seg; k += 1


def balloon(n, c, target, r=17):
    """Item balloon with leader ending in a dot on the part."""
    L = math.hypot(target[0] - c[0], target[1] - c[1]); ux, uy = (target[0] - c[0]) / L, (target[1] - c[1]) / L
    ln(INK, (c[0] + ux * r, c[1] + uy * r), target, HAIR)
    circle(INK, target, 3.2, 1, fill=255)
    erase_circle(c, r); circle(INK, c, r, DETAIL)
    text(INK, c, str(n), 18, 'mm')


def title_block(x0, y0, x1, y1):
    """Simplified drawing title block: fixed cells, uppercase single-stroke lettering."""
    rect(INK, x0, y0, x1, y1, PART)
    ym = (y0 + y1) / 2
    ln(INK, (x0, ym), (x1, ym), HAIR)
    cols = [x0, x0 + (x1 - x0) * .36, x0 + (x1 - x0) * .62, x1]
    for x in cols[1:-1]: ln(INK, (x, y0), (x, y1), HAIR)
    cells = [('DWG NO.', 'KB-061'), ('SCALE', '1:10'), ('SHEET', '1 / 1'),
             ('DRAWN', 'AGENT-01'), ('REV', 'A'), ('DATE', '2026.11')]
    for i, (k, v) in enumerate(cells):
        cx0 = cols[i % 3]; cy0 = y0 if i < 3 else ym
        text(INK, (cx0 + 9, cy0 + 13), k, 11)
        text(INK, (cx0 + 9, cy0 + 37), v, 19)


def detail_view(c, r, src_c, src_r):
    """Circle the slot in phantom line (A), then redraw it at 3:2 inside a detail circle."""
    phantom_circle(INK, src_c, src_r, DETAIL)
    text(INK, (src_c[0] - src_r * .2, src_c[1] - src_r - 16), 'A', 22, 'mm')
    circle(INK, c, r, PART)
    w, h = 150, 150; x, y = c[0] - w / 2, c[1] - h / 2
    lip = y + h * .52
    ImageDraw.Draw(AMB).rectangle([x * S, y * S, (x + w) * S, lip * S], fill=58)
    path(AMB, [(x, lip), (x, y), (x + w, y), (x + w, lip)], OUTLINE)
    for k, lw in enumerate((70, 104, 84)):
        ln(AMB, (x + 18, y + 24 + k * 20), (x + 18 + lw, y + 24 + k * 20), PART)
    rect(INK, x - 14, lip, x + w + 14, y + h + 14, PART)
    ln(INK, (x - 14, lip + 8), (x + w + 14, lip + 8), HAIR)
    for a_, b_ in (((x, lip), (x, y + h)), ((x + w, lip), (x + w, y + h)), ((x, y + h), (x + w, y + h))):
        patterned(AMB, a_, b_, HIDDEN, DETAIL)
    dim(INK, (x, y), (x + w, y), (0, -14), '105', 15)
    text(INK, (c[0], c[1] + r + 24), 'DETAIL A   SCALE 3 : 2', 17, 'mm')


def construction(lines, v=70):
    """Faint construction / projection lines left in, as in hand drafting (thin, low ink)."""
    d = ImageDraw.Draw(INK)
    for a, b in lines: d.line([sc(a), sc(b)], fill=v, width=wpx(1.0))


def link(a, b, half, w=PART):
    """A mechanical arm link: two parallel edges plus round ends, with its centre line."""
    L = math.hypot(b[0] - a[0], b[1] - a[1]); nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
    ln(INK, (a[0] + nx * half, a[1] + ny * half), (b[0] + nx * half, b[1] + ny * half), w)
    ln(INK, (a[0] - nx * half, a[1] - ny * half), (b[0] - nx * half, b[1] - ny * half), w)
    patterned(INK, a, b, CENTRE, HAIR)


def erase(box):
    ImageDraw.Draw(INK).rectangle([box[0] * S, box[1] * S, box[2] * S, box[3] * S], fill=0)


def erase_circle(c, r):
    ImageDraw.Draw(INK).ellipse([(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], fill=0)


def robot():
    # wheels
    for cx in (176, 300):
        c = (cx, FLOOR - 40)
        circle(INK, c, 40, OUTLINE); circle(INK, c, 30, HAIR); circle(INK, c, 12, DETAIL)
        for k in range(6):
            a = math.radians(k * 60 + 15)
            ln(INK, (c[0] + math.cos(a) * 12, c[1] + math.sin(a) * 12), (c[0] + math.cos(a) * 30, c[1] + math.sin(a) * 30), HAIR)
        centre_mark(INK, c, 54)
    # chassis and body
    rect(INK, 128, 884, 348, 922, PART, over=5)
    erase((130, 886, 346, 920)); rect(INK, 128, 884, 348, 922, PART, over=5)
    for x in (146, 330): circle(INK, (x, 903), 5, HAIR)
    for a_, b_ in (((152, 886), (190, 920)), ((190, 886), (152, 920)), ((324, 886), (286, 920)), ((286, 886), (324, 920))): ln(INK, a_, b_, HAIR)
    rrect(INK, 150, 694, 326, 884, 26, OUTLINE)
    rect(INK, 176, 722, 300, 786, DETAIL, over=4)
    for k in range(4): ln(INK, (188, 736 + k * 12), (288 - (k % 2) * 34, 736 + k * 12), HAIR)
    circle(INK, (196, 836), 26, HAIR)                       # internal gear, drawn as hidden line
    for k in range(18):
        a0 = k * 20
        arc(INK, (196, 836), 34, a0, a0 + 11, HAIR)
    centre_mark(INK, (196, 836), 44)
    for k in range(3): circle(INK, (262 + k * 0, 816 + k * 22), 6, HAIR)
    # sensor mast (no face): neck column, turntable, scanner housing shown half in section
    mx = 238
    rect(INK, mx - 16, 650, mx + 16, 694, PART, over=4)
    patterned(INK, (mx, 520), (mx, 700), CENTRE, HAIR)
    rect(INK, mx - 52, 636, mx + 52, 650, PART, over=5)                 # turntable plate
    rect(INK, mx - 66, 572, mx + 66, 636, OUTLINE, over=6)              # scanner housing
    hatch_poly(INK, [(mx - 64, 574), (mx, 574), (mx, 634), (mx - 64, 634)], gap=7, w=HAIR,
               holes=[[(mx - 54, 592), (mx - 2, 592), (mx - 2, 616), (mx - 54, 616)]])
    ln(INK, (mx, 572), (mx, 636), DETAIL)                               # section boundary
    patterned(INK, (mx + 4, 604), (mx + 62, 604), HIDDEN, DETAIL)       # scan window band (hidden)
    rect(INK, mx + 10, 592, mx + 56, 616, DETAIL)
    arc(INK, (mx, 572), 40, 180, 360, PART)                             # dome, triangulated (Fuller)
    ring = [(mx - 40, 572), (mx - 28, 548), (mx - 10, 534), (mx + 10, 534), (mx + 28, 548), (mx + 40, 572)]
    base = [(mx - 40 + k * 16, 572) for k in range(6)]
    for i in range(5):
        ln(INK, base[i], ring[i + 1] if i < 4 else ring[5], HAIR)
    for a_, b_ in zip(ring, ring[1:]): ln(INK, a_, b_, HAIR)
    ln(INK, (mx - 20, 556), (mx + 20, 556), HAIR); ln(INK, (mx - 28, 548), (mx, 572), HAIR); ln(INK, (mx + 28, 548), (mx, 572), HAIR)
    ln(INK, (mx, 532), (mx, 508), PART); circle(INK, (mx, 500), 8, PART)
    for r_ in (20, 31): arc(INK, (mx, 500), r_, 210, 330, HAIR)
    # arm: shoulder -> elbow -> wrist
    sh, el, wr = (326, 770), (412, 716), (488, 668)
    link(sh, el, 11); link(el, wr, 9)
    for c, r_ in ((sh, 20), (el, 15), (wr, 11)):
        erase_circle(c, r_); circle(INK, c, r_, PART); circle(INK, c, r_ * .38, HAIR)
    # sweep arc of the forearm with arrow
    arc(INK, el, 66, -78, -36, HAIR)
    arrow(INK, (el[0] + math.cos(math.radians(-78)) * 66, el[1] + math.sin(math.radians(-78)) * 66), (-1, -.25), 13, 3.6)
    # gripper jaws
    path(INK, [(wr[0] + 6, wr[1] - 9), (wr[0] + 20, wr[1] - 22), (wr[0] + 30, wr[1] - 22)], PART)
    path(INK, [(wr[0] + 6, wr[1] + 9), (wr[0] + 20, wr[1] + 22), (wr[0] + 30, wr[1] + 22)], PART)
    return wr


def card(x, y, w=112, h=78):
    """The note card: the only amber-filled object on the sheet."""
    d = ImageDraw.Draw(AMB)
    d.rectangle([x * S, y * S, (x + w) * S, (y + h) * S], fill=58)
    ImageDraw.Draw(INK).rectangle([(x - 1) * S, (y - 3) * S, (x + w + 3) * S, (y + h + 3) * S], fill=0)
    fold = 20
    path(AMB, [(x, y), (x + w - fold, y), (x + w, y + fold), (x + w, y + h), (x, y + h)], OUTLINE, True)
    path(AMB, [(x + w - fold, y), (x + w - fold, y + fold), (x + w, y + fold)], DETAIL)
    for k, lw in enumerate((56, 78, 64, 40)):
        ln(AMB, (x + 16, y + 20 + k * 14), (x + 16 + lw, y + 20 + k * 14), DETAIL)


def ghost_card(x, y, w=112, h=78):
    """Where the card was a moment ago: amber hidden-line outline only (same sheet, earlier state)."""
    fold = 20
    pts = [(x, y), (x + w - fold, y), (x + w, y + fold), (x + w, y + h), (x, y + h)]
    for a, b in zip(pts, pts[1:] + pts[:1]): patterned(AMB, a, b, HIDDEN, DETAIL)


def cabinet(x0, y0, x1, y1, cols=3, rows=4, t=11):
    dx, dy = 40, -30
    cw = (x1 - x0 - t * (cols + 1)) / cols; ch = (y1 - y0 - t * (rows + 1)) / rows
    cells = [[(x0 + t + c * (cw + t), y0 + t + r * (ch + t), x0 + t + c * (cw + t) + cw, y0 + t + r * (ch + t) + ch)
              for c in range(cols)] for r in range(rows)]
    flat = [b for row in cells for b in row]
    # frame is shown cut: section hatch between outer rect and the cells
    hatch_poly(INK, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], gap=7, w=HAIR,
               holes=[[(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])] for b in flat])
    rect(INK, x0, y0, x1, y1, OUTLINE, over=7)
    for b in flat: rect(INK, b[0], b[1], b[2], b[3], DETAIL)
    # oblique depth: top and right faces
    path(INK, [(x0, y0), (x0 + dx, y0 + dy), (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1)], PART)
    ln(INK, (x1, y0), (x1 + dx, y0 + dy), PART)
    for k in range(1, rows + 1):
        yy = y0 + k * (ch + t)
        patterned(INK, (x1, yy + t / 2), (x1 + dx, yy + t / 2 + dy), HIDDEN, HAIR)
    # feet
    for fx in (x0 + 14, x1 - 44): rect(INK, fx, y1, fx + 30, FLOOR, PART)
    # filed cards inside the cells
    target = (1, 0)
    for r in range(rows):
        for c in range(cols):
            bx0, by0, bx1, by1 = cells[r][c]
            if (r, c) == target: continue
            x = bx0 + 6; n = 0
            while x < bx1 - 12:
                wd = rng.choice((8, 10, 10, 13)); hh = rng.uniform(.55, .9) * ch
                if rng.random() < .16 and x + 30 < bx1:      # a leaning card
                    path(INK, [(x, by1), (x + 14, by1 - hh), (x + 14 + wd, by1 - hh + 3), (x + wd, by1)], HAIR, True)
                    x += wd + 18
                else:
                    rect(INK, x, by1 - hh, x + wd, by1, HAIR)
                    if n % 3 == 0: ln(INK, (x + wd / 2, by1 - hh + 8), (x + wd / 2, by1 - hh + 22), HAIR)
                    x += wd + rng.choice((2, 3, 6))
                n += 1
    # target slot: the card is already inside; the front lip hides its lower part (hidden line = dashed)
    bx0, by0, bx1, by1 = cells[target[0]][target[1]]
    cx = (bx0 + bx1) / 2; cy = (by0 + by1) / 2
    ImageDraw.Draw(AMB).rectangle([bx0 * S, by0 * S, bx1 * S, by1 * S], fill=22)
    kx0, kx1, ky0 = bx0 + 9, bx1 - 9, by0 + 10
    lip = by0 + (by1 - by0) * .52
    ImageDraw.Draw(AMB).rectangle([kx0 * S, ky0 * S, kx1 * S, lip * S], fill=58)
    path(AMB, [(kx0, lip), (kx0, ky0), (kx1, ky0), (kx1, lip)], PART)
    for k in range(2): ln(AMB, (kx0 + 9, ky0 + 11 + k * 11), (kx1 - 12 - k * 12, ky0 + 11 + k * 11), DETAIL)
    rect(INK, bx0 + 2, lip, bx1 - 2, by1 - 2, DETAIL)             # front lip (plain face, drawn in white ink)
    ln(INK, (bx0 + 2, lip + 5), (bx1 - 2, lip + 5), HAIR)
    for a, b in (((kx0, lip), (kx0, by1 - 8)), ((kx1, lip), (kx1, by1 - 8)), ((kx0, by1 - 8), (kx1, by1 - 8))):
        patterned(AMB, a, b, HIDDEN, DETAIL)
    SLOT.update(cell=(bx0, by0, bx1, by1), card=(kx0, ky0, kx1, lip))
    # dimensions
    dim(INK, (x0, y0 + dy), (x1, y0 + dy), (0, -34), '1200')
    dim(INK, (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (34, 0))
    return (cx, cy, bx0)


def ground():
    ln(INK, (70, FLOOR), (1010, FLOOR), OUTLINE)
    for x in range(84, 1004, 20): ln(INK, (x, FLOOR + 16), (x + 13, FLOOR + 3), HAIR)


def compose(paper):
    def down(layer): return layer.resize((W, H), Image.LANCZOS)
    ink, amb = down(INK), down(AMB)
    # uneven print: ink density wobbles slightly, like a contact print
    wob = noise_tile(64).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6)).point(lambda v: 205 + v * 50 // 255)
    ink = ImageChops.multiply(ink, wob); amb = ImageChops.multiply(amb, wob)
    out = paper
    for layer, col in ((ink, LINE), (amb, ACCENT)):
        bleed = layer.filter(ImageFilter.GaussianBlur(2.4)).point(lambda v: int(v * .42))
        out = Image.composite(Image.new('RGB', (W, H), col), out, bleed)     # soft bleed around lines
        out = Image.composite(Image.new('RGB', (W, H), col), out, layer)
    return out


def main():
    paper = make_paper()
    sheet_border(); heading()
    L, T, R, B, C = big_number()
    title_block(640, 58, 1036, 160)
    construction([((52, 570), (632, 570)), ((640, 230), (640, 540)), ((936, 470), (936, 530)),
                  ((52, 884), (120, 884)), ((488, 470), (488, 650)), ((60, 1000), (1030, 1000))])
    ground()
    cx, cy, slot_x = cabinet(676, 570, 960, FLOOR - 16)
    # robot is drawn on its own layer, then nudged left to open a gap before the cabinet
    global INK
    base, INK = INK, Image.new('L', INK.size, 0)
    wr = robot()
    RDX = -26
    INK = ImageChops.lighter(base, ImageChops.offset(INK, RDX * S, 0))
    wr = (wr[0] + RDX, wr[1])
    cx0, cy0 = wr[0] + 31, wr[1] - 39
    ghost_card(cx0, cy0)
    # travel path: centre line arcs from the held card down into the empty slot
    p0 = (cx0 + 112 + 8, cy0 + 30); p2 = (slot_x - 3, SLOT['card'][1] + 16); p1 = ((p0[0] + p2[0]) / 2 + 6, p0[1] - 34)
    pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [k / 24 for k in range(25)]]
    acc, on = 0.0, True
    for a, b in zip(pts, pts[1:]):
        if on: ln(AMB, a, b, DETAIL)
        acc += math.hypot(b[0] - a[0], b[1] - a[1])
        if acc > (14 if on else 6): acc, on = 0.0, not on
    arrow(AMB, p2, (p2[0] - pts[-3][0], p2[1] - pts[-3][1]), 20, 6)
    sc_ = SLOT['cell']; detail_view((850, 330), 120, ((sc_[0] + sc_[2]) / 2, (sc_[1] + sc_[3]) / 2), 62)
    balloon(2, (96 + RDX + 6, 520), (172 + RDX, 600))
    balloon(1, (96 + RDX + 6, 680), (152 + RDX, 780))
    balloon(3, (612, 880), (676, 920))
    compose(paper).save(os.path.join(HERE, 'sample.png'))


if __name__ == '__main__':
    main()
