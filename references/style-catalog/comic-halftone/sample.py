# Comic halftone style sample: thick ink outlines, screen-tone dots, speed lines, panels.
import os, math, random
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
INK = (18, 16, 20)
PAPER = (250, 246, 234)
RED = (226, 52, 48)
YEL = (255, 214, 64)
CYAN = (60, 170, 220)
rng = random.Random(61)
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_CJK = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_MONO = "/System/Library/Fonts/Menlo.ttc"

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)

def mask_of(shape_fn):
    m = Image.new("L", (W, H), 0)
    shape_fn(ImageDraw.Draw(m))
    return m

def halftone(mask, color, spacing=11, rmin=0.8, rmax=4.6, angle=45, grad=None):
    """Screen-tone dots on a rotated grid, only where mask is set; radius varies by grad(x,y) in 0..1."""
    px = mask.load()
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    bb = mask.getbbox()
    if not bb:
        return
    x0, y0, x1, y1 = bb
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R = int(math.hypot(x1 - x0, y1 - y0) / 2) + spacing
    for i in range(-R, R + 1, spacing):
        for j in range(-R, R + 1, spacing):
            x = cx + i * ca - j * sa
            y = cy + i * sa + j * ca
            xi, yi = int(x), int(y)
            if 0 <= xi < W and 0 <= yi < H and px[xi, yi] > 0:
                t = grad(x, y) if grad else 0.5
                r = rmin + (rmax - rmin) * max(0, min(1, t))
                d.ellipse([x - r, y - r, x + r, y + r], fill=color)

def ink_poly(pts, fill=None, w=7):
    """Thick brush-like outline: main stroke plus round joints."""
    if fill:
        d.polygon(pts, fill=fill)
    pts2 = list(pts) + [pts[0]]
    d.line(pts2, fill=INK, width=w, joint="curve")
    for p in pts:
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=INK)

def ink_rect(box, fill=None, w=7):
    x0, y0, x1, y1 = box
    ink_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, w)

def speed_lines(cx, cy, r_in, r_out, n, clip_box, width_max=7):
    """Radial focus lines (tapered wedges) converging on a point, clipped to a panel."""
    layer = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(layer)
    for k in range(n):
        ang = rng.uniform(0, math.tau)
        wdt = rng.uniform(0.004, 0.012) * width_max
        ri = r_in * rng.uniform(0.9, 1.4)
        p1 = (cx + math.cos(ang - wdt) * r_out, cy + math.sin(ang - wdt) * r_out)
        p2 = (cx + math.cos(ang + wdt) * r_out, cy + math.sin(ang + wdt) * r_out)
        p0 = (cx + math.cos(ang) * ri, cy + math.sin(ang) * ri)
        ld.polygon([p0, p1, p2], fill=255)
    clip = Image.new("L", (W, H), 0)
    ImageDraw.Draw(clip).rectangle(clip_box, fill=255)
    from PIL import ImageChops
    layer = ImageChops.multiply(layer, clip)
    img.paste(INK, mask=layer)

def parallel_speed(box, n, direction=(1, 0)):
    """Horizontal action lines streaking behind a moving object."""
    x0, y0, x1, y1 = box
    for _ in range(n):
        y = rng.uniform(y0, y1)
        L = rng.uniform(60, 220)
        xs = rng.uniform(x0, x1 - L)
        w = rng.choice([2, 3, 3, 4])
        d.line([(xs, y), (xs + L, y)], fill=INK, width=w)

def burst(cx, cy, r1, r2, n, fill):
    pts = []
    for k in range(n * 2):
        ang = math.pi * k / n + rng.uniform(-0.05, 0.05)
        r = r2 * rng.uniform(0.9, 1.08) if k % 2 == 0 else r1 * rng.uniform(0.92, 1.05)
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    ink_poly(pts, fill, 8)
    return pts

def outlined_text(xy, text, font, fill, stroke=8, anchor="mm"):
    d.text(xy, text, font=font, fill=fill, stroke_width=stroke, stroke_fill=INK, anchor=anchor)

# ---- panel layout (gutter = paper) ----
G = 22
P1 = (G, G, W - G, 330)               # heading panel
P2 = (G, 330 + G, 560, 1030)           # agent panel
P3 = (560 + G, 330 + G, W - G, 1030)   # knowledge base panel
CALM_Y = int(H * 0.78)

# Panel 1: heading with focus lines
d.rectangle(P1, fill=(255, 255, 255))
speed_lines(W / 2, 175, 150, 900, 170, P1)
halftone(mask_of(lambda m: m.rectangle(P1, fill=255)), YEL, spacing=14, rmin=0.5, rmax=6,
         grad=lambda x, y: abs(x - W / 2) / (W / 2))
d.rounded_rectangle([W / 2 - 260, 95, W / 2 + 260, 255], radius=20, fill=PAPER)
f_head = ImageFont.truetype(FONT_CJK, 150)
outlined_text((W / 2, 172), "知識庫", f_head, RED, stroke=9)
ink_rect(P1, None, 9)

# Panel 2: robot arm placing a note card
d.rectangle(P2, fill=(255, 255, 255))
m2 = mask_of(lambda m: m.rectangle(P2, fill=255))
halftone(m2, CYAN, spacing=12, rmin=0.6, rmax=5.2, grad=lambda x, y: (y - P2[1]) / (P2[3] - P2[1]))
parallel_speed((P2[0] + 10, 400, 470, 560), 22)
# robot: treads, boxy torso, square head with visor bar (no face), antenna, jointed arm
bx0, by0 = 70, 800
# treads
ink_rect((bx0 - 10, by0 + 190, bx0 + 250, by0 + 225), (70, 72, 82), 8)
for k in range(6):
    d.ellipse([bx0 + 6 + k * 42, by0 + 198, bx0 + 30 + k * 42, by0 + 218], fill=(150, 152, 165), outline=INK, width=4)
# torso
ink_rect((bx0, by0, bx0 + 230, by0 + 190), (225, 228, 238), 8)
ts = mask_of(lambda m: m.polygon([(bx0 + 150, by0), (bx0 + 230, by0), (bx0 + 230, by0 + 190), (bx0 + 110, by0 + 190)], fill=255))
halftone(ts, INK, spacing=8, rmin=1.0, rmax=2.8, angle=15)
ink_rect((bx0, by0, bx0 + 230, by0 + 190), None, 8)
ink_rect((bx0 + 24, by0 + 24, bx0 + 120, by0 + 92), YEL, 6)   # chest panel
d.ellipse([bx0 + 52, by0 + 40, bx0 + 92, by0 + 76], fill=RED, outline=INK, width=5)
for k in range(3):
    d.line([(bx0 + 24, by0 + 116 + k * 20), (bx0 + 120, by0 + 116 + k * 20)], fill=INK, width=6)
# neck + head
ink_rect((bx0 + 80, by0 - 24, bx0 + 150, by0), (150, 152, 165), 6)
ink_rect((bx0 + 25, by0 - 150, bx0 + 205, by0 - 22), (225, 228, 238), 8)
hs = mask_of(lambda m: m.polygon([(bx0 + 150, by0 - 150), (bx0 + 205, by0 - 150), (bx0 + 205, by0 - 22), (bx0 + 120, by0 - 22)], fill=255))
halftone(hs, INK, spacing=8, rmin=1.0, rmax=2.6, angle=15)
ink_rect((bx0 + 25, by0 - 150, bx0 + 205, by0 - 22), None, 8)
ink_rect((bx0 + 45, by0 - 112, bx0 + 185, by0 - 62), INK, 6)      # dark visor
d.rectangle((bx0 + 60, by0 - 94, bx0 + 170, by0 - 80), fill=CYAN)    # single scanning light bar
d.line([(bx0 + 115, by0 - 150), (bx0 + 115, by0 - 205)], fill=INK, width=8)
d.ellipse([bx0 + 97, by0 - 232, bx0 + 133, by0 - 196], fill=RED, outline=INK, width=6)
for sgn in (-1, 1):  # antenna signal ticks
    d.line([(bx0 + 115 + sgn * 34, by0 - 232), (bx0 + 115 + sgn * 52, by0 - 244)], fill=INK, width=5)
# segmented arm
joints = [(bx0 + 230, by0 + 60), (400, 760), (470, 660)]
for a_, b_ in zip(joints, joints[1:]):
    d.line([a_, b_], fill=INK, width=44)
    d.line([a_, b_], fill=(205, 208, 220), width=28)
for j in joints:
    d.ellipse([j[0] - 24, j[1] - 24, j[0] + 24, j[1] + 24], fill=YEL, outline=INK, width=7)
# two-finger claw
d.line([(470, 660), (520, 625)], fill=INK, width=14)
d.line([(470, 660), (525, 680)], fill=INK, width=14)
# note card gripped, heading to the shelf slot
card = [(500, 500), (640, 520), (620, 630), (480, 610)]
ink_poly(card, (255, 255, 250), 8)
for k in range(3):
    t = 0.3 + k * 0.2
    a = (card[0][0] + (card[3][0] - card[0][0]) * t + 18, card[0][1] + (card[3][1] - card[0][1]) * t + 8)
    b = (card[1][0] + (card[2][0] - card[1][0]) * t - 18, card[1][1] + (card[2][1] - card[1][1]) * t - 2)
    d.line([a, b], fill=INK, width=5)
d.rectangle((520, 512, 560, 530), fill=RED)
ink_rect(P2, None, 9)

# Panel 3: knowledge base shelves (database stacks)
d.rectangle(P3, fill=(255, 255, 255))
m3 = mask_of(lambda m: m.rectangle(P3, fill=255))
halftone(m3, (200, 200, 205), spacing=10, rmin=0.4, rmax=3.2, angle=30, grad=lambda x, y: (x - P3[0]) / (P3[2] - P3[0]))
sx0, sx1 = P3[0] + 50, P3[2] - 40
for row in range(4):
    y = 640 + row * 95
    d.line([(sx0, y), (sx1, y)], fill=INK, width=9)
    x = sx0 + 8
    while x < sx1 - 30:
        bw = rng.randint(22, 40)
        bh = rng.randint(55, 82)
        col = rng.choice([RED, YEL, CYAN, (255, 255, 255)])
        ink_rect((x, y - bh, x + bw, y - 4), col, 5)
        if rng.random() < 0.5:
            sh = mask_of(lambda m, x=x, bw=bw, bh=bh, y=y: m.rectangle((x + bw * 0.55, y - bh + 4, x + bw - 4, y - 8), fill=255))
            halftone(sh, INK, spacing=6, rmin=0.8, rmax=1.8, angle=45)
        x += bw + rng.randint(2, 8)
# empty slot glow where the card lands
d.rectangle((sx0 + 140, 640 - 80, sx0 + 190, 636), fill=YEL)
ink_rect((sx0 + 140, 640 - 80, sx0 + 190, 636), None, 5)
# card half-inserted in slot + arrow
ink_poly([(sx0 + 120, 560), (sx0 + 200, 560), (sx0 + 200, 636), (sx0 + 120, 636)], (255, 255, 250), 6)
d.line([(sx0 + 135, 585), (sx0 + 185, 585)], fill=INK, width=4)
d.line([(sx0 + 135, 605), (sx0 + 185, 605)], fill=INK, width=4)
ink_poly([(P3[0] + 20, 700), (P3[0] + 20, 740), (P3[0] + 70, 720)], RED, 6)
ink_rect(P3, None, 9)

# Big 61% burst overlapping panels 1/3
burst(800, 400, 105, 165, 16, YEL)
bm = mask_of(lambda m: m.ellipse([710, 320, 890, 480], fill=255))
halftone(bm, (240, 150, 40), spacing=9, rmin=0.5, rmax=3, grad=lambda x, y: (y - 320) / 160)
f_num = ImageFont.truetype(FONT_MONO, 110)
outlined_text((800, 400), "61%", f_num, RED, stroke=9)

# Calm bottom zone: plain paper with a sparse light tone and a thin rule
cm = mask_of(lambda m: m.rectangle((0, CALM_Y + 40, W, H), fill=255))
halftone(cm, (232, 226, 210), spacing=16, rmin=0.4, rmax=1.6, grad=lambda x, y: (y - CALM_Y) / (H - CALM_Y))
d.line([(G, 1055), (W - G, 1055)], fill=INK, width=4)
f_cap = ImageFont.truetype(FONT_CJK, 40)
d.text((W / 2, 1180), "一張筆記，歸檔入庫", font=f_cap, fill=INK, anchor="mm")

img.save(os.path.join(HERE, "sample.png"))
