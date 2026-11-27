#!/usr/bin/env python3
"""Style catalog sample: neon-grid / synthwave (original artwork, PIL only).

Technique encoded here:
  - dark sky gradient, one horizon line, perspective floor grid (rays to one vanishing point,
    cross lines spaced by 1/z so they bunch toward the horizon)
  - every drawn line is a neon tube: coloured tube + near-white core, then a 3-radius additive bloom
  - objects are wireframes with oblique depth; their silhouettes are filled with near-black first
    so the grid never shows through a solid object (occlusion before glow)
  - 3 tube colours (pink, cyan, violet) + 1 accent (amber) reserved for the note card / target slot
  - striped sun behind the scene, clipped at the horizon; faint scanlines over everything
  - bottom ~22% fades the grid to a quiet dark floor for subtitles
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

W, H = 1080, 1350
HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(61)

F_ZH = '/System/Library/Fonts/STHeiti Medium.ttc'
F_NUM = ('/System/Library/Fonts/Supplemental/Futura.ttc', 2)   # Futura Bold
F_LBL = ('/System/Library/Fonts/Supplemental/Futura.ttc', 0)   # Futura Medium

# palette (must match style.md)
SKY_TOP = (8, 4, 28)        # #08041C
SKY_MID = (42, 10, 68)      # #2A0A44
HORIZON = (110, 24, 112)    # #6E1870  haze band just above the horizon
FLOOR = (10, 3, 22)         # #0A0316
OCCLUDE = (12, 6, 30)       # #0C061E  fill inside wireframe objects
PINK = (255, 46, 170)       # #FF2EAA
CYAN = (0, 235, 255)        # #00EBFF
VIOLET = (150, 70, 255)     # #9646FF
AMBER = (255, 170, 60)      # #FFAA3C
SUN_TOP = (255, 214, 92)    # #FFD65C
SUN_BOT = (255, 46, 140)    # #FF2E8C

HOR = 700          # horizon y
VX = 540           # vanishing point x


def tint(c, k=.6):
    """Hot core of a tube: the tube colour pushed toward white."""
    return tuple(int(v + (255 - v) * k) for v in c)


class Neon:
    """Tube layer (bloomed) + core layer (thin, near white, not bloomed)."""
    def __init__(s):
        s.tube = Image.new('RGB', (W, H)); s.core = Image.new('RGB', (W, H))
        s.dt = ImageDraw.Draw(s.tube); s.dc = ImageDraw.Draw(s.core)

    def line(s, pts, c, w=4):
        s.dt.line(pts, fill=c, width=w, joint='curve')
        s.dc.line(pts, fill=tint(c), width=max(1, w // 3), joint='curve')
        for p in (pts[0], pts[-1]):                      # round caps
            r = w / 2; s.dt.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=c)

    def poly(s, pts, c, w=4): s.line(list(pts) + [pts[0]], c, w)

    def rect(s, x0, y0, x1, y1, c, w=4): s.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], c, w)

    def rrect(s, x0, y0, x1, y1, r, c, w=4):
        s.dt.rounded_rectangle([x0, y0, x1, y1], r, outline=c, width=w)
        s.dc.rounded_rectangle([x0, y0, x1, y1], r, outline=tint(c), width=max(1, w // 3))

    def circle(s, cx, cy, r, c, w=4):
        s.dt.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=w)
        s.dc.ellipse([cx - r, cy - r, cx + r, cy + r], outline=tint(c), width=max(1, w // 3))

    def dot(s, x, y, r, c):
        s.dt.ellipse([x - r, y - r, x + r, y + r], fill=c)
        s.dc.ellipse([x - r / 2, y - r / 2, x + r / 2, y + r / 2], fill=tint(c, .85))

    def bloom(s, base, radii=((34, .5), (12, .8), (4, 1.0))):
        out = base
        for rad, k in radii:
            b = s.tube.filter(ImageFilter.GaussianBlur(rad))
            out = ImageChops.add(out, b.point(lambda v, k=k: int(v * k)))
        out = ImageChops.add(out, s.tube)
        return ImageChops.lighter(out, s.core)


def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky():
    img = Image.new('RGB', (W, H)); d = ImageDraw.Draw(img)
    for y in range(H):
        if y < HOR:
            t = y / HOR
            c = lerp(SKY_TOP, SKY_MID, min(1, t / .8)) if t < .8 else lerp(SKY_MID, HORIZON, (t - .8) / .2)
        else:
            c = lerp((40, 8, 60), FLOOR, min(1, (y - HOR) / 160))
        d.line([(0, y), (W, y)], fill=c)
    return img


def stars(img):
    d = ImageDraw.Draw(img)
    for _ in range(70):
        x, y = R.uniform(0, W), R.uniform(0, HOR - 120)
        g = R.randint(70, 190)
        if R.random() < .15: d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(g, g, min(255, g + 40)))
        else: d.point((x, y), fill=(g, g, min(255, g + 40)))


def sun(img, cx, cy, r):
    """Gradient disc sliced by horizontal gaps that widen toward the horizon."""
    col = Image.new('RGB', (W, H)); cd = ImageDraw.Draw(col)
    for y in range(cy - r, cy + r + 1):
        cd.line([(cx - r, y), (cx + r, y)], fill=lerp(SUN_TOP, SUN_BOT, (y - cy + r) / (2 * r)))
    m = Image.new('L', (W, H), 0); md = ImageDraw.Draw(m)
    md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=215)
    y, gap, step = cy - r * .15, 3, 26
    while y < cy + r:
        md.rectangle([0, y, W, y + gap], fill=0); y += gap + step; gap += 3; step = max(10, step - 4)
    md.rectangle([0, HOR, W, H], fill=0)
    gm = Image.new('L', (W, H), 0); ImageDraw.Draw(gm).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    ImageDraw.Draw(gm).rectangle([0, HOR, W, H], fill=0)
    glow = Image.composite(Image.new('RGB', (W, H), (150, 40, 90)), Image.new('RGB', (W, H)),
                           gm.filter(ImageFilter.GaussianBlur(46)).point(lambda v: v * 6 // 10))
    img = ImageChops.add(img, glow)
    return Image.composite(col, img, m)


def mountains(n):
    """Low wireframe ridge on the horizon, violet, with a few interior ridge lines."""
    pts = [(-20, HOR)]; x = -20
    while x < W + 20:
        x += R.randint(46, 90); pts.append((x, HOR - (R.randint(28, 80) if len(pts) % 2 else R.randint(4, 22))))
    n.line(pts, (96, 44, 170), 2)
    for i in range(1, len(pts) - 1, 2):
        n.line([pts[i], ((pts[i][0] + pts[i + 1][0]) / 2 + 8, HOR)], (70, 30, 130), 1)


def grid(n):
    """Floor: rays from the vanishing point + cross lines at y = HOR + K/z."""
    def fade(y):                                   # dim near horizon, full mid, quiet bottom 22%
        a = min(1, (y - HOR) / 150)
        if y > 980: a *= max(.12, 1 - (y - 980) / 130)
        return a
    for i in range(-12, 13):
        x_near = VX + i * 128
        steps = 24
        for k in range(steps):                     # segment the ray so its brightness can fade
            t0, t1 = k / steps, (k + 1) / steps
            y0 = HOR + (H - HOR) * t0; y1 = HOR + (H - HOR) * t1
            x0 = VX + (x_near - VX) * t0; x1 = VX + (x_near - VX) * t1
            c = lerp((0, 0, 0), PINK, fade((y0 + y1) / 2) * .8)
            n.dt.line([(x0, y0), (x1, y1)], fill=c, width=2)
    for k in range(1, 60):
        y = HOR + 620 / (.5 + .35 * k)          # perspective: equal floor steps bunch toward the horizon
        if y > H: continue
        if y - HOR < 96: break                 # closer lines would merge into a solid band
        c = lerp((0, 0, 0), PINK, fade(y) * .85)
        n.dt.line([(0, y), (W, y)], fill=c, width=2)
        if fade(y) > .6: n.dc.line([(0, y), (W, y)], fill=lerp((0, 0, 0), tint(PINK, .3), fade(y) * .35), width=1)
    n.line([(0, HOR), (W, HOR)], PINK, 3)


def occlude(img, polys, shadows=()):
    """Fill object silhouettes with near-black so grid and sun do not show through them."""
    d = ImageDraw.Draw(img)
    for cx, cy, rx, ry in shadows:
        sh = Image.new('L', (W, H), 0)
        ImageDraw.Draw(sh).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=200)
        img = Image.composite(Image.new('RGB', (W, H), (4, 1, 10)), img, sh.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(img)
    for p in polys: d.polygon(p, fill=OCCLUDE)
    return img


def box(n, x0, y0, x1, y1, dx, dy, c, w=4, back=True):
    """Wireframe box: front face + top and right faces in oblique depth (dx, dy)."""
    n.rect(x0, y0, x1, y1, c, w)
    n.line([(x0, y0), (x0 + dx, y0 + dy), (x1 + dx, y0 + dy), (x1, y0)], c, w)
    n.line([(x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1)], c, w)


def box_poly(x0, y0, x1, y1, dx, dy):
    return [(x0, y0), (x0 + dx, y0 + dy), (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1), (x0, y1)]


# ---------- robot ----------
RD = (16, -11)   # robot depth


def robot_polys():
    return [box_poly(120, 930, 380, 996, *RD), box_poly(170, 720, 340, 890, *RD),
            box_poly(186, 584, 318, 684, *RD), box_poly(232, 890, 274, 930, *RD), box_poly(238, 684, 268, 720, *RD)]


def robot(n):
    # tracked base
    n.rrect(120, 930, 380, 996, 30, VIOLET, 4)
    n.line([(140, 930), (136 + RD[0], 930 + RD[1]), (364 + RD[0], 930 + RD[1]), (380 + RD[0], 950 + RD[1]), (380, 950)], VIOLET, 3)
    for k in range(5): n.circle(152 + k * 49, 963, 17, VIOLET, 3); n.dot(152 + k * 49, 963, 3, CYAN)
    # hip column
    box(n, 232, 890, 274, 930, *RD, VIOLET, 3)
    # torso: wireframe box with a chest status panel (three level bars)
    box(n, 170, 720, 340, 890, *RD, CYAN, 5)
    n.rect(196, 746, 314, 820, CYAN, 2)
    for k, L in enumerate((.9, .62, .4)):
        n.line([(210, 764 + k * 20), (210 + 90 * L, 764 + k * 20)], PINK if k == 0 else VIOLET, 5)
    for k in range(3): n.dot(214 + k * 22, 856, 4, CYAN if k else PINK)
    # neck
    box(n, 238, 684, 268, 720, *RD, VIOLET, 3)
    # head: a sensor block with one horizontal visor slit (no face)
    box(n, 186, 584, 318, 684, *RD, CYAN, 5)
    n.rrect(204, 616, 300, 644, 8, PINK, 3)
    n.line([(216, 630), (288, 630)], PINK, 7)
    for k in range(4): n.line([(204 + k * 10, 664), (204 + k * 10, 674)], VIOLET, 2)
    # antenna
    n.line([(252 + RD[0] / 2, 584 + RD[1] / 2), (252 + RD[0] / 2, 540)], CYAN, 3)
    n.circle(252 + RD[0] / 2, 530, 9, PINK, 3)
    for r_ in (22, 34):
        n.dt.arc([260 - r_, 530 - r_, 260 + r_, 530 + r_], 210, 330, fill=lerp((0, 0, 0), VIOLET, .7), width=2)
    # left arm resting
    n.line([(170, 746), (138, 800), (148, 862)], CYAN, 7)
    n.circle(170, 746, 12, PINK, 4); n.circle(138, 800, 10, PINK, 3)
    n.line([(140, 872), (132, 890)], VIOLET, 4); n.line([(156, 872), (164, 890)], VIOLET, 4)
    # right arm reaching to the shelf: shoulder - elbow - wrist
    sh, el, wr = (340, 746), (446, 684), (562, 670)
    n.line([sh, el], CYAN, 9); n.line([el, wr], CYAN, 8)
    for j, r_ in ((sh, 15), (el, 13), (wr, 11)):
        n.circle(j[0], j[1], r_, PINK, 4)
    # gripper jaws pinching the card's left edge
    n.line([(wr[0] + 8, wr[1] - 8), (wr[0] + 20, wr[1] - 26), (wr[0] + 34, wr[1] - 26)], CYAN, 4)
    n.line([(wr[0] + 8, wr[1] + 8), (wr[0] + 20, wr[1] + 26), (wr[0] + 34, wr[1] + 26)], CYAN, 4)
    return wr


# ---------- knowledge base ----------
KB = (708, 560, 960, 1000)
KD = (44, -30)
ROWS = 5


def kb_cells():
    x0, y0, x1, y1 = KB; rh = (y1 - y0) / ROWS
    return [(x0, y0 + r * rh, x1, y0 + (r + 1) * rh) for r in range(ROWS)]


def knowledge_base(n):
    x0, y0, x1, y1 = KB
    box(n, x0, y0, x1, y1, *KD, CYAN, 5)
    cells = kb_cells()
    for (a, b, c, d) in cells[1:]:
        n.line([(a, b), (c, b)], CYAN, 3); n.line([(c, b), (c + KD[0], b + KD[1])], CYAN, 2)
    target = 1
    for r, (a, b, c, d) in enumerate(cells):
        if r == target: continue
        # drawer of filed cards: thin vertical card edges, varied heights, a few lit tabs
        xx = a + 16
        while xx < c - 18:
            wd = R.choice((8, 10, 12)); top = b + 16 + R.randint(0, 22)
            col = R.choice((VIOLET, VIOLET, CYAN, PINK))
            n.dt.rectangle([xx, top, xx + wd, d - 10], outline=lerp((0, 0, 0), col, .75), width=2)
            if R.random() < .2: n.dot(xx + wd / 2, top - 6, 2.5, col)
            xx += wd + R.choice((4, 5, 7))
    # the open slot: amber light spilling out of the target row
    a, b, c, d = cells[target]
    sy = (b + d) / 2
    dim = lerp((0, 0, 0), AMBER, .5)
    n.dt.rectangle([a + 4, sy - 40, a + 96, sy + 40], fill=(20, 10, 3))      # the card's hidden part, inside
    for k in range(6):                                                        # drawn as a dashed hidden outline
        n.line([(a + 10 + k * 15, sy - 40), (a + 18 + k * 15, sy - 40)], dim, 2)
        n.line([(a + 10 + k * 15, sy + 40), (a + 18 + k * 15, sy + 40)], dim, 2)
    n.line([(a + 96, sy - 40), (a + 96, sy - 28)], dim, 2); n.line([(a + 96, sy + 28), (a + 96, sy + 40)], dim, 2)
    n.line([(a, sy - 54), (a, sy + 54)], AMBER, 6)                            # the glowing slot mouth
    # data nodes on top of the shelf: small network = "knowledge"
    nodes = [(x0 + 40 + KD[0] / 2, y0 + KD[1] / 2 - 40), (x0 + 130, y0 - 92), (x0 + 220, y0 - 58), (x1 + 20, y0 - 120)]
    for p, q in ((0, 1), (1, 2), (1, 3), (2, 3)): n.line([nodes[p], nodes[q]], VIOLET, 2)
    for p in nodes: n.line([p, (p[0], y0 + KD[1] / 2)], lerp((0, 0, 0), VIOLET, .5), 1); n.dot(p[0], p[1], 6, VIOLET)
    return (a, sy)


def card(n, x, y, w=128, h=86, clip_x=None):
    """Note card being pushed into the slot; the part past clip_x is already inside."""
    xr = min(x + w, clip_x) if clip_x else x + w
    n.dt.rectangle([x, y, xr, y + h], fill=(48, 26, 8))
    n.line([(xr, y), (x, y), (x, y + h), (xr, y + h)], AMBER, 5)
    for k, L in enumerate((.72, .9, .6)):
        n.line([(x + 18, y + 24 + k * 19), (min(xr - 6, x + 18 + (w - 36) * L), y + 24 + k * 19)], AMBER, 3)
    # direction cue: three chevrons above the card, brightest nearest the slot
    for k in range(3):
        cx = x + 46 + k * 26; cy = y - 26
        n.line([(cx - 7, cy - 10), (cx + 4, cy), (cx - 7, cy + 10)], lerp((0, 0, 0), AMBER, .4 + k * .3), 4)


# ---------- type ----------
def neon_text(img, xy, s, font, c, anchor='mm', outline=0, aberr=0):
    """Glowing type. outline>0 draws a hollow tube letter (stroke only)."""
    m = Image.new('L', (W, H), 0); md = ImageDraw.Draw(m)
    if outline:
        md.text(xy, s, font=font, fill=255, anchor=anchor, stroke_width=outline, stroke_fill=255)
        inner = Image.new('L', (W, H), 0)
        ImageDraw.Draw(inner).text(xy, s, font=font, fill=255, anchor=anchor)
        inner = inner.filter(ImageFilter.MinFilter(2 * outline - 1))
        m = ImageChops.subtract(m, inner)
    else:
        md.text(xy, s, font=font, fill=255, anchor=anchor)
    tube = Image.composite(Image.new('RGB', (W, H), c), Image.new('RGB', (W, H)), m)
    if aberr:   # mild channel split: pink copy left, cyan copy right, weak
        for off, col in ((-aberr, PINK), (aberr, CYAN)):
            sm = ImageChops.offset(m, off, 0).point(lambda v: v * 45 // 100)
            img = ImageChops.add(img, Image.composite(Image.new('RGB', (W, H), col), Image.new('RGB', (W, H)), sm))
    for rad, k in ((30, .55), (10, .8), (3, .9)):
        img = ImageChops.add(img, tube.filter(ImageFilter.GaussianBlur(rad)).point(lambda v, k=k: int(v * k)))
    core = m.filter(ImageFilter.MinFilter(3))
    img = ImageChops.lighter(img, tube)
    return Image.composite(Image.new('RGB', (W, H), tint(c, .75)), img, core)


def scanlines(img, step=3, k=.86):
    m = Image.new('L', (W, H), 255); d = ImageDraw.Draw(m)
    for y in range(0, H, step): d.line([(0, y), (W, y)], fill=int(255 * k))
    return Image.composite(img, Image.new('RGB', (W, H)), m)


def main():
    img = sky(); stars(img)
    img = sun(img, 862, 566, 172)
    bg = Neon(); mountains(bg); grid(bg)
    img = bg.bloom(img, ((20, .35), (6, .7), (2, .8)))
    # objects: occlude, then glow
    img = occlude(img, robot_polys() + [box_poly(*KB, *KD), [(588, 649), (708, 649), (708, 735), (588, 735)]],
                  shadows=((250, 1000, 190, 18), (850, 1004, 170, 16)))
    fg = Neon()
    wr = robot(fg)
    slot_x, slot_y = knowledge_base(fg)
    card(fg, wr[0] + 26, slot_y - 43, clip_x=slot_x)
    img = fg.bloom(img)
    # type
    img = neon_text(img, (540, 112), '知識庫', ImageFont.truetype(F_ZH, 104), PINK)
    img = neon_text(img, (78, 338), '61%', ImageFont.truetype(F_NUM[0], 250, index=F_NUM[1]), CYAN, anchor='lm', outline=4, aberr=4)
    lbl = Neon()
    f = ImageFont.truetype(F_LBL[0], 26, index=F_LBL[1])
    x = 84
    for ch in 'SYNCED TO MEMORY':
        lbl.dt.text((x, 470), ch, font=f, fill=VIOLET, anchor='lm'); lbl.dc.text((x, 470), ch, font=f, fill=tint(VIOLET, .5), anchor='lm')
        x += f.getlength(ch) + 6
    lbl.line([(84, 496), (x - 6, 496)], VIOLET, 2)
    img = lbl.bloom(img, ((10, .6), (3, .8)))
    img = scanlines(img)
    img.save(os.path.join(HERE, 'sample.png'))


if __name__ == '__main__':
    main()
