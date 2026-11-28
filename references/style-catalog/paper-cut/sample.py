# Paper-cut layered style sample: stacked paper sheets, per-layer drop shadow, fiber texture, deckle edges.
import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

W, H = 1080, 1350
R = random.Random(61)
HERE = os.path.dirname(os.path.abspath(__file__))
HEI = "/System/Library/Fonts/STHeiti Medium.ttc"
MENLO = "/System/Library/Fonts/Menlo.ttc"

def fiber_texture(w, h, rng):
    # grayscale paper fibers + speckles, multiplied onto each sheet
    t = Image.new("L", (w, h), 246)
    d = ImageDraw.Draw(t)
    for _ in range(9000):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a, l = rng.uniform(0, 6.283), rng.uniform(5, 24)
        pts = [(x, y)]
        for _k in range(3):
            x += math.cos(a) * l / 3; y += math.sin(a) * l / 3; a += rng.uniform(-.6, .6)
            pts.append((x, y))
        d.line(pts, fill=rng.choice([226, 232, 238, 255]), width=1)
    for _ in range(5000):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        d.point((x, y), fill=rng.choice([205, 220]))
    return t.filter(ImageFilter.GaussianBlur(0.7))

TEX = fiber_texture(W, H, R)
TEX3 = Image.merge("RGB", (TEX, TEX, TEX))

def deckle(poly, amp=1.6, step=10):
    # subdivide edges and jitter: hand-cut scissor/knife edge
    out = []
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % n]
        seg = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for s in range(seg):
            t = s / seg
            out.append((x0 + (x1 - x0) * t + R.uniform(-amp, amp), y0 + (y1 - y0) * t + R.uniform(-amp, amp)))
    return out

def circle(cx, cy, r, n=72):
    return [(cx + r * math.cos(6.283 * i / n), cy + r * math.sin(6.283 * i / n)) for i in range(n)]

def rect(cx, cy, w, h, ang=0):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]]

def bar(p, q, w):
    ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
    return rect((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, math.hypot(q[0] - p[0], q[1] - p[1]), w, ang)

def taper(p, q, w0, w1):
    # Reiniger-style limb: a slim jointed strip, wider at the shoulder end
    a = math.atan2(q[1] - p[1], q[0] - p[0]); nx, ny = -math.sin(a), math.cos(a)
    return [(p[0] + nx * w0 / 2, p[1] + ny * w0 / 2), (q[0] + nx * w1 / 2, q[1] + ny * w1 / 2),
            (q[0] - nx * w1 / 2, q[1] - ny * w1 / 2), (p[0] - nx * w0 / 2, p[1] - ny * w0 / 2)]

def lobed(cx, cy, r, k, ph=0.0, n=120):
    # Matisse-style scissor-cut form: one flowing outline with a few big lobes, no straight edges
    pts = []
    for i in range(n):
        t = 6.283 * i / n
        rr = r * (1 + .34 * math.cos(k * t + ph) + .12 * math.cos((k - 2) * t + 1.7 * ph))
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    return pts

def hole(canvas, poly):
    # a cut-through opening: paper shows through, with a thin shadow on the upper-left inner edge
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    canvas.paste(ImageChops.multiply(Image.new("RGB", (W, H), CREAM), TEX3), (0, 0), m)
    inner = ImageChops.subtract(m, ImageChops.offset(m, 3, 3)).filter(ImageFilter.GaussianBlur(1.2))
    canvas.paste(Image.new("RGB", (W, H), (58, 40, 30)), (0, 0), inner.point(lambda v: int(v * .5)))

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)

def sheet(canvas, mask, color, depth=1.0):
    # one paper layer: soft cast shadow, fiber-textured fill, light cut-edge bevel
    off = (int(3 + 3 * depth), int(4 + 5 * depth))
    sh = Image.new("L", (W, H), 0); sh.paste(mask, off)
    sh = sh.filter(ImageFilter.GaussianBlur(5 + 4 * depth)).point(lambda v: int(v * 0.42))
    canvas.paste(Image.new("RGB", (W, H), (58, 40, 30)), (0, 0), sh)
    fill = ImageChops.multiply(Image.new("RGB", (W, H), shade(color, 1.04)), TEX3)
    canvas.paste(fill, (0, 0), mask)
    edge = ImageChops.subtract(mask, ImageChops.offset(mask, 2, 2)).filter(ImageFilter.GaussianBlur(0.8))
    canvas.paste(Image.new("RGB", (W, H), shade(color, 1.25)), (0, 0), edge.point(lambda v: int(v * .55)))

def layer(canvas, poly, color, depth=1.0, rough=True):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(deckle(poly) if rough else poly, fill=255)
    sheet(canvas, m, color, depth)

def text_layer(canvas, xy, s, font, color, depth=1.0, anchor="la"):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text(xy, s, font=font, fill=255, anchor=anchor)
    sheet(canvas, m, color, depth)

CREAM = (241, 231, 212); INK = (38, 52, 74); TEAL = (40, 96, 98); TEAL2 = (66, 128, 124)
TERRA = (196, 92, 62); TERRA2 = (226, 140, 98); OCHRE = (222, 172, 84); WHITE = (250, 246, 236)
SAGE = (150, 170, 140); PLUM = (120, 70, 88)

img = ImageChops.multiply(Image.new("RGB", (W, H), CREAM), TEX3)

# Matisse: two big scissor-cut lobed forms, flat colour, cropped by the frame, behind everything
layer(img, lobed(70, 470, 150, 5, .4), TEAL2, .35, rough=False)
layer(img, lobed(1055, 540, 95, 4, 1.1), OCHRE, .4, rough=False)
# backdrop: concentric paper discs behind the stat
for r, col, d in [(250, (234, 206, 176), .6), (212, TERRA2, 1.0), (172, TERRA, 1.4)]:
    layer(img, circle(790, 330, r), col, d)
text_layer(img, (790, 340), "61%", ImageFont.truetype(HEI, 150), WHITE, 1.6, "mm")

# heading
text_layer(img, (70, 70), "知識庫", ImageFont.truetype(HEI, 132), INK, 1.2)
layer(img, rect(170, 248, 200, 10), TERRA, .6, rough=False)
text_layer(img, (72, 272), "KNOWLEDGE BASE", ImageFont.truetype(MENLO, 30), TEAL, .5)

# knowledge base: layered library building with shelves
layer(img, [(610, 650), (825, 540), (1040, 650)], TEAL, 1.0)
layer(img, [(650, 640), (825, 560), (1000, 640)], TEAL2, 1.2)
layer(img, rect(825, 850, 400, 420), TEAL, 1.0)
layer(img, rect(825, 858, 360, 384), (28, 66, 70), 1.2)
rows = [(668, 790), (802, 920), (932, 1040)]
palette = [OCHRE, TERRA, WHITE, SAGE, PLUM, TERRA2, (210, 200, 180)]
for ri, (y0, y1) in enumerate(rows):
    layer(img, rect(825, y1 + 4, 370, 12), (214, 190, 150), 1.4, rough=False)
    x = 662 + (78 if ri == 1 else 0)  # empty slot on middle row
    while x < 990:
        w = R.randint(22, 38); h = R.randint(int((y1 - y0) * .62), int((y1 - y0) * .9))
        if x + w > 992: break
        tilt = R.choice([0, 0, 0, -5, 6])
        layer(img, rect(x + w / 2, y1 - h / 2, w, h, tilt), R.choice(palette), 1.6)
        x += w + R.randint(3, 8)
# slot glow behind the card pocket
layer(img, rect(700, 862, 72, 114), (250, 226, 160), 1.3)
layer(img, rect(700, 862, 52, 94), (255, 240, 196), 1.5)
# the note card stands IN the slot: drawn now, then the pocket strip (drawn after) covers its lower part
layer(img, rect(701, 850, 58, 104, -2), WHITE, 1.7)
layer(img, rect(701, 818, 42, 10, -2), TERRA, 1.8, rough=False)
for i, ww in enumerate((42, 34)):
    layer(img, rect(698 + (ww - 42) / 2 * .2, 840 + i * 16, ww, 8, -2), [TEAL2, OCHRE][i], 1.8, rough=False)
layer(img, [(659, 872), (743, 872), (743, 924), (659, 924)], TEAL2, 2.1)           # pocket front
layer(img, rect(701, 888, 34, 8, 0), TERRA2, 2.3, rough=False)                      # pocket tab

# robot agent: full paper-cut machine (tracks, body, visor head, antenna, two arms; no face)
NAVY = (60, 78, 104); OCHRE2 = (238, 198, 116); OCHRE0 = (184, 136, 58)
RX = 250
# tracks: dark rounded slab + three wheel discs
layer(img, [(RX - 130, 1050), (RX + 130, 1050), (RX + 150, 1015), (RX + 120, 985), (RX - 120, 985), (RX - 150, 1015)], INK, 1.0)
for dx in (-80, 0, 80):
    layer(img, circle(RX + dx, 1018, 22), NAVY, 1.3)
    layer(img, circle(RX + dx, 1018, 8), SAGE, 1.5)
# body: ochre slab, right side panel one step darker (light from top-left)
layer(img, rect(RX, 880, 210, 200), OCHRE, 1.4)
layer(img, rect(RX + 86, 882, 34, 190), OCHRE0, 1.6, rough=False)
layer(img, rect(RX - 20, 860, 120, 84), TEAL, 1.8)          # chest panel
for k, col in enumerate([TERRA2, WHITE, SAGE]):
    layer(img, circle(RX - 58 + k * 38, 846, 11), col, 2.0)  # status lights
layer(img, rect(RX - 20, 884, 96, 8), TEAL2, 2.0, rough=False)
layer(img, rect(RX - 30, 952, 150, 10), OCHRE0, 1.6, rough=False)
# neck + head
layer(img, rect(RX, 768, 60, 30), NAVY, 1.3)
layer(img, rect(RX, 700, 190, 128), OCHRE2, 1.6)
layer(img, rect(RX + 80, 702, 26, 124), OCHRE, 1.7, rough=False)
layer(img, rect(RX - 8, 700, 150, 46), INK, 2.0)            # visor band (no eyes, no mouth)
layer(img, rect(RX - 30, 700, 70, 10), TEAL2, 2.3, rough=False)  # scan line
for sx in (-1, 1): layer(img, circle(RX + sx * 104, 700, 18), NAVY, 1.5)  # ear bolts
# antenna
layer(img, rect(RX, 612, 10, 50), INK, 1.3, rough=False)
layer(img, circle(RX, 586, 18), TERRA, 1.6)
# left arm hanging (slim tapered strip)
layer(img, taper((RX - 112, 820), (RX - 140, 960), 32, 22), NAVY, 1.7)
layer(img, circle(RX - 112, 820, 24), INK, 1.9)
layer(img, circle(RX - 140, 966, 20), INK, 1.9)
# right arm reaching to the card pocket: shoulder -> elbow -> wrist (two slim tapered strips + pivot holes)
shoulder, elbow, wrist = (RX + 112, 820), (500, 748), (652, 832)
layer(img, taper(shoulder, elbow, 34, 24), NAVY, 2.0)
layer(img, taper(elbow, wrist, 28, 20), NAVY, 2.4)
layer(img, circle(*shoulder, 26), INK, 2.2)
layer(img, circle(*elbow, 24), INK, 2.6)
layer(img, circle(*wrist, 21), INK, 2.8)
for pv in (shoulder, elbow, wrist): hole(img, circle(pv[0], pv[1], 6, 24))             # Reiniger: pivot pin holes
layer(img, bar((652, 832), (676, 818), 14), INK, 3.3)  # gripper fingers pinching the card's left edge
layer(img, bar((652, 832), (676, 848), 14), INK, 3.3)
# motion strips trailing behind the wrist
for i, (x, y, w_) in enumerate([(520, 882, 56), (504, 908, 40), (528, 934, 28)]):
    layer(img, rect(x, y, w_, 8, -9), TERRA2, .7, rough=False)
# Reiniger: filigree of cut-through holes along the robot's belly
for k in range(5): hole(img, circle(RX - 60 + k * 30, 918, 7, 24))

# calm bottom 22%: layered paper hills
for y, col, d, amp in [(1070, SAGE, .8, 22), (1130, TEAL2, 1.1, 16), (1200, TEAL, 1.4, 12)]:
    pts = [(x, y + amp * math.sin(x / 150 + y)) for x in range(-20, W + 40, 40)]
    layer(img, pts + [(W + 20, H + 20), (-20, H + 20)], col, d)

img.save(os.path.join(HERE, "sample.png"))
