"""Style catalog sample: bauhaus (basic shapes, primary colours, constructed type).
Self-contained: Python 3 + PIL only. Renders sample.png (1080x1350) next to this file.
Technique encoded here:
  - every object is built from circle / square / triangle / bar only
  - each ink is a separate "plate" (L mask); plates are multiplied onto paper,
    so overlaps mix like overprinted ink (yellow x blue, red x yellow ...)
  - knock() cuts a hole through all plates (paper shows through)
  - numerals are constructed from rings, arcs and bars, not typed
  - slight plate misregistration + ink mottling + paper grain = printed poster feel
"""
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
import math, os, random

W, H, S = 1080, 1350, 2                      # S = supersampling factor
HERE = os.path.dirname(os.path.abspath(__file__))
rnd = random.Random(1919)

PAPER = (238, 229, 208)
INKS = {                                     # plate name -> ink colour, print order
    'yellow': (243, 186, 28),
    'red':    (212, 50, 38),
    'blue':   (28, 70, 150),
    'black':  (28, 26, 26),
}
OFFSET = {'yellow': (2, -1), 'red': (-2, 1), 'blue': (1, 2), 'black': (0, 0)}  # misregistration (px @1x)

plates = {k: Image.new('L', (W * S, H * S), 0) for k in INKS}
draws = {k: ImageDraw.Draw(v) for k, v in plates.items()}


def sc(pts): return [(x * S, y * S) for x, y in pts]

# ---- primitives (the only vocabulary allowed) ---------------------------------
def poly(ink, pts, v=255): draws[ink].polygon(sc(pts), fill=v)
def rect(ink, x0, y0, x1, y1, v=255): draws[ink].rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=v)
def disc(ink, cx, cy, r, v=255): draws[ink].ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=v)
def ring(ink, cx, cy, r, w, v=255): draws[ink].ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], outline=v, width=int(w * S))
def arc(ink, cx, cy, r, a0, a1, w, v=255): draws[ink].arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], a0, a1, fill=v, width=int(w * S))
def pie(ink, cx, cy, r, a0, a1, v=255): draws[ink].pieslice([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], a0, a1, fill=v)
def bar(ink, x0, y0, x1, y1, w, v=255):
    """thick straight bar with square ends"""
    a = math.atan2(y1 - y0, x1 - x0); nx, ny = -math.sin(a) * w / 2, math.cos(a) * w / 2
    poly(ink, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], v)
def rot_rect(cx, cy, w, h, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
def knock(pts):
    for k in INKS: poly(k, pts, 0)
def knock_disc(cx, cy, r):
    for k in INKS: disc(k, cx, cy, r, 0)
def stripes(ink, x0, y0, x1, y1, n, horizontal=True):
    """n equal bars with equal gaps"""
    if horizontal:
        h = (y1 - y0) / (2 * n - 1)
        for i in range(n): rect(ink, x0, y0 + 2 * i * h, x1, y0 + (2 * i + 1) * h)
    else:
        w = (x1 - x0) / (2 * n - 1)
        for i in range(n): rect(ink, x0 + 2 * i * w, y0, x0 + (2 * i + 1) * w, y1)

# ---- constructed numerals ------------------------------------------------------
def num6(ink, x, base, h=240, t=48):
    R = h / 3                                   # bowl radius
    ring(ink, x + R, base - R, R, t)
    arc(ink, x + 2 * R, base - R, 2 * R, 180, 268, t)   # stem = quarter of a twice-as-big circle
    return 2 * R
def num1(ink, x, base, h=240, t=48):
    rect(ink, x + 46, base - h, x + 46 + t, base)
    poly(ink, [(x + 46, base - h), (x + 46, base - h + t * 1.5), (x, base - h + t * 1.5)])  # flag = triangle
    return 46 + t
def percent(ink, x, base, h=240, t=26):
    r = h * .19
    ring(ink, x + r, base - h + r, r, t)
    ring(ink, x + h * .62 - r + 26, base - r, r, t)
    bar(ink, x + 6, base, x + h * .62 + 20, base - h, t)
    return h * .62 + 26

# ================================ composition ===================================
GROUND = 962
# -- background fields ------------------------------------------------------------
disc('yellow', 286, 700, 232)                              # sun-like field behind the agent
pie('red', 1080, 0, 205, 90, 180)                          # corner quarter disc
bar('black', -10, 1014, 640, 484, 5)                       # diagonal axis: ground -> shelf, the arm lies on it
rect('yellow', 1010, 1, 1050, 392)                           # Moholy-Nagy: yellow bar overprints the red corner (transparent overlap), stops on the shelf top
rect('black', 60, GROUND, 1020, GROUND + 12)               # ground rule
for t_, r_ in ((0.035, 5), (0.085, 8), (0.15, 12)):        # Kandinsky: points of growing size accelerate along the diagonal
    disc('black', -10 + 650 * t_, 1014 - 530 * t_, r_)

# -- knowledge base: a shelf made of bars, books = rectangles ----------------------
SX0, SX1 = 640, 1000
shelves = [522, 668, 814, GROUND]
rect('black', SX0, 392, SX0 + 22, GROUND)                  # left post
rect('black', SX0, 392, SX1, 392 + 22)                     # top bar
for y in shelves[:-1]: rect('black', SX0, y, SX1, y + 12)
book_cols = ['red', 'blue', 'black', 'yellow']
ROWEND = [SX1 - 190, SX1 - 30, SX1 - 230, SX1 - 30]       # Mondrian: leave the open fields open, white dominates
for si, y in enumerate(shelves):
    x = SX0 + 34
    top = (392 + 22) if si == 0 else shelves[si - 1] + 12
    room = y - top
    k = 0
    while x < ROWEND[si]:
        w = rnd.choice([22, 30, 30, 44, 58]); h = room * rnd.choice([.62, .74, .86, .86])
        if x + w > SX1 - 6: break
        if si == 1 and k == 0:                             # the empty slot waiting for the card
            x += 116; k += 1; continue
        ink = book_cols[(k + si * 3) % 4] if rnd.random() < .8 else rnd.choice(book_cols)
        if rnd.random() < .16 and x + w + 40 < SX1:        # a leaning book
            knock(rot_rect(x + w / 2 + 16, y - h / 2 + 3, w, h, 14)); poly(ink, rot_rect(x + w / 2 + 16, y - h / 2 + 3, w, h, 14)); x += w + 40
        else:
            knock([(x, y - h), (x + w, y - h), (x + w, y), (x, y)]); rect(ink, x, y - h, x + w, y)
            if w >= 44 and ink != 'yellow':                # spine band
                knock([(x, y - h + 16), (x + w, y - h + 16), (x + w, y - h + 26), (x, y - h + 26)])
            x += w + rnd.choice([6, 6, 10, 22])
        k += 1
stripes('black', SX0 + 34, 322, SX1, 372, 3)               # stripes above the shelf (rhythm)
pie('blue', SX1, GROUND, 236, 180, 270)                    # quarter disc OVERPRINTS the lower shelves (inks mix)

# -- the AI agent: a machine built from square, rectangle, circle, triangle ---------
# No eyes, no mouth: the head carries one horizontal visor slot (a bar), nothing else.
AX = 250
# tracked base: one long bar + three wheels (circle / knocked hub / red dot)
knock([(AX - 112, 878), (AX + 112, 878), (AX + 112, 958), (AX - 112, 958)])
rect('black', AX - 110, 880, AX + 110, 956)
for wx in (AX - 72, AX, AX + 72):
    knock_disc(wx, 918, 24); disc('red', wx, 918, 9)
rect('black', AX - 34, 812, AX + 34, 880)                              # hip column
# torso: blue square, chest gauge = knocked disc with a red 61 % sector
knock([(AX - 102, 620), (AX + 102, 620), (AX + 102, 816), (AX - 102, 816)])
rect('blue', AX - 100, 622, AX + 100, 814)
knock_disc(AX, 718, 52); pie('red', AX, 718, 52, -90, -90 + 220); disc('black', AX, 718, 10)
for bx, by in ((AX - 82, 640), (AX + 82, 640), (AX - 82, 796), (AX + 82, 796)): disc('black', bx, by, 7)   # bolts
rect('black', AX - 18, 588, AX + 18, 622)                              # neck
# head: black square, one visor slot, antenna
knock([(AX - 78, 476), (AX + 78, 476), (AX + 78, 592), (AX - 78, 592)])
rect('black', AX - 76, 478, AX + 76, 590)
knock([(AX - 58, 522), (AX + 58, 522), (AX + 58, 546), (AX - 58, 546)])   # visor slot = paper
rect('red', AX + 6, 522, AX + 58, 546)                                  # scan segment, looking right
rect('black', AX - 3, 420, AX + 3, 478); disc('red', AX, 412, 14)       # antenna
# idle arm (left): straight bar down, joint discs, triangle hand
bar('black', AX - 100, 646, AX - 150, 790, 18); disc('black', AX - 100, 646, 16); disc('red', AX - 150, 790, 13)
# working arm (right): shoulder -> elbow -> card, one straight diagonal toward the shelf slot
SH, EL, HD = (AX + 100, 650), (AX + 220, 612), (660, 590)
bar('black', *SH, *EL, 20); bar('black', *EL, *HD, 16)
disc('black', *SH, 17); knock_disc(*EL, 17); disc('red', *EL, 14)
poly('black', [(HD[0] - 4, HD[1] - 26), (HD[0] + 22, HD[1] - 18), (HD[0] + 4, HD[1] - 4)])   # upper jaw
poly('black', [(HD[0] - 4, HD[1] + 26), (HD[0] + 22, HD[1] + 18), (HD[0] + 4, HD[1] + 4)])   # lower jaw

# -- the note card, half-way into the empty slot of shelf row 2 ----------------------
CX, CY, CA = 716, 594, 0
card = rot_rect(CX, CY, 104, 132, CA)
knock(card); poly('black', card)
knock(rot_rect(CX, CY, 88, 116, CA))
for i, lw in enumerate((60, 60, 38)):                                  # three text bars
    poly('black', rot_rect(CX - (60 - lw) / 2 + i * 0.0, CY - 14 + i * 26, lw, 9, CA))
poly('red', rot_rect(CX - 26, CY - 42, 22, 22, CA))                    # red tab = the new note
# slot cover: a red panel in front of the slot, the card disappears under it (occlusion)
knock([(738, 536), (790, 536), (790, 666), (738, 666)])
rect('red', 740, 538, 788, 664)
for yy in (560, 600, 640): rect('black', 746, yy, 782, yy + 4)
# gripper drawn over the card so the hand visibly holds it
bar('black', HD[0] - 30, HD[1], HD[0] + 4, HD[1], 16)
poly('black', [(HD[0] - 4, HD[1] - 30), (HD[0] + 26, HD[1] - 22), (HD[0] + 6, HD[1] - 6)])
poly('black', [(HD[0] - 4, HD[1] + 30), (HD[0] + 26, HD[1] + 22), (HD[0] + 6, HD[1] + 6)])

# -- big constructed number ------------------------------------------------------------
x, base = 70, 352
x += num6('black', x, base) + 26
x += num1('black', x, base) + 34
percent('red', x, base)
rect('black', 70, base + 26, 560, base + 38)                           # heavy rule under the number
rect('red', 70, 74, 118, 86)                                           # small accent bar
# signature row: the three basic shapes, sitting just under the ground rule
rect('blue', 70, 992, 100, 1022); disc('red', 133, 1007, 15); poly('yellow', [(166, 1022), (198, 1022), (182, 992)])

# ================================ printing ============================================
def noise_tile(size, cell, lo, hi):
    w, h = size[0] // cell + 2, size[1] // cell + 2
    im = Image.frombytes('L', (w, h), rnd.randbytes(w * h)).resize(size, Image.BICUBIC)
    return im.point(lambda v: int(lo + (hi - lo) * v / 255))

small = {k: v.resize((W, H), Image.LANCZOS) for k, v in plates.items()}

# heading typed in a plain grotesque, knocked into the black plate as a block
f = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 92)
td = ImageDraw.Draw(small['black'])
tx = SX0 + 34
for ch in '知識庫':                                                     # tracked out to span the shelf grid
    td.text((tx, 208), ch, font=f, fill=255); tx += (SX1 - SX0 - 34 - 92) / 2

canvas = Image.new('RGB', (W, H), PAPER)
white = Image.new('RGB', (W, H), (255, 255, 255))
for name, col in INKS.items():
    m = ImageChops.offset(small[name], *OFFSET[name])
    m = ImageChops.multiply(m, noise_tile((W, H), 3, 218, 255))        # ink mottling
    m = ImageChops.multiply(m, noise_tile((W, H), 90, 225, 255))       # uneven pressure
    tint = Image.composite(Image.new('RGB', (W, H), col), white, m)
    canvas = ImageChops.multiply(canvas, tint)                         # overprint
grain = noise_tile((W, H), 1, 236, 255).filter(ImageFilter.GaussianBlur(.6))
canvas = ImageChops.multiply(canvas, Image.merge('RGB', (grain, grain, grain)))
canvas.save(os.path.join(HERE, 'sample.png'))
