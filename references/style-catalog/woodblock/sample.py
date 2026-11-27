# Woodblock print (木刻版畫) sample: separate colour plates, wood-grain ink transfer,
# gouge-carved highlights, thick black key-block outlines, slight mis-registration.
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1350
HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(61)
PAPER = (238, 228, 205)
INK = (30, 25, 22)
RED = (188, 54, 40)
INDIGO = (40, 64, 98)
OCHRE = (212, 160, 76)
HEI = "/System/Library/Fonts/STHeiti Medium.ttc"
SONG = HEI


def plate():
    img = Image.new('L', (W, H), 0)
    return img, ImageDraw.Draw(img)


def wood_grain(seed, strength=70):
    """Grain lines + knots that starve ink where the wood is low."""
    rr = random.Random(seed)
    g = Image.new('L', (W, H), 255)
    d = ImageDraw.Draw(g)
    y = -40.0
    while y < H + 40:
        amp, fr, ph = rr.uniform(2, 12), rr.uniform(0.003, 0.01), rr.uniform(0, 6.28)
        pts = [(x, y + amp * math.sin(x * fr + ph) + 4 * math.sin(x * 0.027 + ph * 3))
               for x in range(-12, W + 24, 12)]
        d.line(pts, fill=255 - rr.randint(strength // 3, strength), width=rr.choice([1, 1, 2, 3]))
        y += rr.uniform(4, 11)
    for _ in range(3):
        cx, cy = rr.uniform(0, W), rr.uniform(0, H)
        for k in range(1, 9):
            d.ellipse((cx - k * 9, cy - k * 4, cx + k * 9, cy + k * 4), outline=255 - strength, width=1)
    # speckle where paper fibres missed the ink
    for _ in range(2500):
        x, y2 = rr.uniform(0, W), rr.uniform(0, H)
        r = rr.uniform(0.6, 2.0)
        d.ellipse((x - r, y2 - r, x + r, y2 + r), fill=rr.randint(60, 180))
    return g.filter(ImageFilter.GaussianBlur(0.5))


def rough_edges(mask, seed):
    """Wobble edges like a hand-cut block: blur + noisy threshold."""
    rr = random.Random(seed)
    m = mask.filter(ImageFilter.GaussianBlur(1.6))
    noise = Image.new('L', (W // 8, H // 8))
    noise.putdata([rr.randint(90, 165) for _ in range((W // 8) * (H // 8))])
    noise = noise.resize((W, H), Image.BILINEAR)
    diff = ImageChops.subtract(m, noise, 1, 0)
    return diff.point(lambda v: 255 if v > 0 else 0)


def gouge(d, x, y, length, ang, w, fill=0):
    """Tapered V-gouge cut (leaf shape)."""
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    pts = []
    for i in range(9):
        t = i / 8
        r = w * math.sin(math.pi * t) * (0.6 + 0.4 * (1 - t))
        pts.append((x + ca * length * t + nx * r, y + sa * length * t + ny * r))
    for i in range(8, -1, -1):
        t = i / 8
        r = w * math.sin(math.pi * t) * (0.6 + 0.4 * (1 - t))
        pts.append((x + ca * length * t - nx * r, y + sa * length * t - ny * r))
    d.polygon(pts, fill=fill)


def gouge_hatch(d, box, ang, gap, rr, w=3, fill=0):
    """Parallel carved strokes used as shading."""
    x0, y0, x1, y1 = box
    y = y0
    while y < y1:
        x = x0 + rr.uniform(-6, 6)
        while x < x1:
            L = rr.uniform(30, 70)
            gouge(d, x, y + rr.uniform(-2, 2), L, ang + rr.uniform(-0.06, 0.06), w * rr.uniform(0.7, 1.2), fill)
            x += L + rr.uniform(4, 14)
        y += gap


def carved_line(d, pts, w, rr, fill=255):
    """Thick key-block contour with hand jitter and round joints."""
    jp = [(x + rr.uniform(-1.5, 1.5), y + rr.uniform(-1.5, 1.5)) for x, y in pts]
    for a, b in zip(jp, jp[1:]):
        ww = w * rr.uniform(0.85, 1.15)
        d.line([a, b], fill=fill, width=int(ww))
        d.ellipse((b[0] - ww / 2, b[1] - ww / 2, b[0] + ww / 2, b[1] + ww / 2), fill=fill)
    a = jp[0]
    d.ellipse((a[0] - w / 2, a[1] - w / 2, a[0] + w / 2, a[1] + w / 2), fill=fill)


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def seg_poly(x1, y1, x2, y2, w):
    a = math.atan2(y2 - y1, x2 - x1)
    nx, ny = -math.sin(a) * w / 2, math.cos(a) * w / 2
    return [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]


def print_plate(paper, mask, color, seed, offset, strength=70):
    m = rough_edges(mask, seed)
    m = ImageChops.multiply(m, wood_grain(seed + 7, strength))
    m = ImageChops.offset(m, *offset)
    paper.paste(Image.new('RGB', (W, H), color), (0, 0), m)


# ---------- paper ----------
paper = Image.new('RGB', (W, H), PAPER)
pn = Image.new('L', (W // 4, H // 4))
pn.putdata([R.randint(0, 22) for _ in range((W // 4) * (H // 4))])
pn = pn.resize((W, H), Image.BILINEAR)
paper = ImageChops.subtract(paper, Image.merge('RGB', (pn, pn, pn)))

# geometry
BOT = int(H * 0.78)
cab = (600, 300, 1010, BOT - 20)   # knowledge-base cabinet
slot = (700, 628, 820, 718)        # empty slot being filled
card = (455, 590, 590, 680)        # note card in the claw

# ---------- ochre plate: sun disc, books, card tint ----------
ochre, od = plate()
od.ellipse((40, 300, 560, 820), fill=255)
od.rectangle((0, BOT, W, H), fill=255)
rr = random.Random(3)
shelves = [cab[1] + 70 + i * 120 for i in range(5)]
books = []
for i, sy in enumerate(shelves):
    x = cab[0] + 30
    while x < cab[2] - 40:
        bw = rr.randint(22, 42)
        bh = rr.randint(70, 100)
        if not (i == 2 and slot[0] - 10 < x < slot[2]):
            books.append((x, sy + 110 - bh, x + bw, sy + 110, rr.random()))
        x += bw + rr.randint(3, 8)
for b in books:
    if b[4] < 0.55:
        od.rectangle(b[:4], fill=255)
od.rectangle(card, fill=0)
print_plate(paper, ochre, OCHRE, 11, (3, -2), 55)

# ---------- indigo plate: cabinet body, sky band, network nodes ----------
ind, idd = plate()
idd.rectangle((0, 0, W, 250), fill=255)
idd.rectangle((cab[0], cab[1], cab[2], cab[3]), fill=255)
for b in books:
    idd.rectangle(b[:4], fill=0)  # books knocked out of indigo
idd.rectangle(slot, fill=0)
idd.rectangle(card, fill=0)
idd.rectangle((0, BOT + 26, W, H), fill=255)
rr = random.Random(5)
gouge_hatch(idd, (0, 20, W, 240), 0.0, 22, rr, 3)            # carved sky ripples
gouge_hatch(idd, (0, BOT + 60, W, H - 30), 0.0, 40, rr, 2.5)  # calm water/ground
print_plate(paper, ind, INDIGO, 21, (-2, 2), 80)

# ---------- red plate: 61%, some books, card tab ----------
red, rd = plate()
f61 = ImageFont.truetype(HEI, 250)
rd.text((560, 20), "61%", font=f61, fill=255)
for b in books:
    if b[4] >= 0.8:
        rd.rectangle(b[:4], fill=255)
rd.rectangle((card[0], card[1], card[0] + 34, card[1] + 16), fill=255)
rr = random.Random(9)
gouge_hatch(rd, (560, 150, 1060, 260), -0.12, 26, rr, 2.2)    # carved texture in numerals
print_plate(paper, red, RED, 31, (2, 3), 65)

# ---------- key block (black): outlines, robot, heading ----------
key, kd = plate()
rr = random.Random(13)
# heading
fh = ImageFont.truetype(HEI, 140)
kd.text((48, 70), "知識庫", font=fh, fill=255)
# cabinet outline + shelves
carved_line(kd, rect_pts(*cab), 12, rr)
for sy in shelves:
    carved_line(kd, [(cab[0], sy + 112), (cab[2], sy + 112)], 9, rr)
for b in books:
    carved_line(kd, rect_pts(*b[:4]), 4, rr)
carved_line(kd, rect_pts(*slot), 5, rr)
# cabinet roof (archive building)
carved_line(kd, [(cab[0] - 24, cab[1]), ((cab[0] + cab[2]) / 2, cab[1] - 70), (cab[2] + 24, cab[1]), (cab[0] - 24, cab[1])], 11, rr)
# network nodes on the roof pediment
nodes = [((cab[0] + cab[2]) / 2 + dx, cab[1] - 26 + dy) for dx, dy in [(-90, 8), (-30, -18), (30, -18), (90, 8), (0, 10)]]
for a in nodes:
    for b in nodes:
        if a < b:
            kd.line([a, b], fill=255, width=3)
for x, y in nodes:
    kd.ellipse((x - 8, y - 8, x + 8, y + 8), fill=255)

# robot: tracked base, torso, square head with visor slit (no face), antenna, jointed arm, claw
kd.rectangle((120, 960, 390, BOT), fill=255)              # tracks
for tx in range(150, 380, 40):
    kd.ellipse((tx, 985, tx + 28, 1013), fill=0)
kd.rectangle((160, 790, 350, 960), fill=255)              # torso
gouge_hatch(kd, (170, 805, 340, 945), 0.0, 18, rr, 2.5)
kd.rectangle((200, 700, 310, 780), fill=255)              # head
kd.rectangle((215, 730, 295, 746), fill=0)                # visor slit
kd.line([(255, 700), (255, 655)], fill=255, width=8)
kd.ellipse((241, 640, 269, 668), fill=255)
for rx, ry in [(180, 810), (330, 810), (180, 940), (330, 940)]:
    kd.ellipse((rx - 6, ry - 6, rx + 6, ry + 6), fill=0)  # rivets
shoulder = (350, 840)
elbow = (450, 790)
wrist = (480, 660)
for p, q, w in [(shoulder, elbow, 44), (elbow, wrist, 36)]:
    kd.polygon(seg_poly(*p, *q, w), fill=255)
for (x, y), r in [(shoulder, 30), (elbow, 24), (wrist, 18)]:
    kd.ellipse((x - r, y - r, x + r, y + r), fill=255)
    kd.ellipse((x - r * 0.35, y - r * 0.35, x + r * 0.35, y + r * 0.35), fill=0)
# claw pinching the card's left edge
carved_line(kd, [wrist, (card[0] + 6, card[1] + 6)], 12, rr)
carved_line(kd, [wrist, (card[0] + 6, card[3] - 6)], 12, rr)
# note card
carved_line(kd, rect_pts(*card), 7, rr)
for i in range(3):
    yy = card[1] + 34 + i * 18
    kd.line([(card[0] + 20, yy), (card[2] - 20 - i * 18, yy)], fill=255, width=5)
# motion: gouge strokes from card to slot
for i in range(4):
    gouge(kd, card[2] + 14, card[1] + 20 + i * 18, 80 - i * 8, 0.0, 4, fill=255)
# ground line (bottom calm zone starts here)
carved_line(kd, [(0, BOT), (W, BOT)], 10, rr)
carved_line(kd, [(0, BOT + 26), (W, BOT + 26)], 5, rr)
# small seal in calm zone
print_plate(paper, key, INK, 41, (0, 0), 40)

# chop-mark seal in red
seal, sd = plate()
sd.rectangle((968, 1228, 1022, 1282), fill=255)
sd.rectangle((980, 1240, 1010, 1270), outline=0, width=5)
sd.line([(980, 1255), (1010, 1255)], fill=0, width=4)
print_plate(paper, seal, RED, 51, (0, 0), 30)

paper.save(os.path.join(HERE, "sample.png"))
