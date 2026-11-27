# Riso print style sample (original): 3 spot-ink drums printed in order yellow -> pink -> blue,
# each drum = solid stencil + rotated AM halftone, multiply overprint, misregistration,
# roller banding, ink-starvation flecks and paper tooth.
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

W, H = 1080, 1350
RNG = random.Random(61)
HERE = os.path.dirname(os.path.abspath(__file__))


def rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


PAPER = rgb("F3EEE1")                    # natural cream stock
INKS = {"yellow": rgb("FFE800"), "pink": rgb("FF48B0"), "blue": rgb("0078BF")}
ORDER = ("yellow", "pink", "blue")       # light ink first, darkest last
ANGLE = {"yellow": 75, "pink": 45, "blue": 15}   # 30 deg apart -> no moire
OFFSET = {"yellow": (5, 4), "pink": (-3, 2), "blue": (0, 0)}  # blue is the key drum
CELL = 10                                # screen pitch in px (~108 lines across 1080 px)
HEI = "/System/Library/Fonts/STHeiti Medium.ttc"
DIN = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"

L = {k: {"solid": Image.new("L", (W, H), 0), "tone": Image.new("L", (W, H), 0)} for k in INKS}


def D(k, part="solid"):
    return ImageDraw.Draw(L[k][part])


def glyphs_ok(font, text):
    nd = font.getmask("￿")
    nd = (nd.getbbox(), bytes(nd))
    for ch in text:
        m = font.getmask(ch)
        if m.getbbox() is None or (m.getbbox(), bytes(m)) == nd:
            raise SystemExit("missing glyph: " + ch)


def halftone(tone, angle, cell=CELL):
    out = Image.new("L", (W, H), 0); d = ImageDraw.Draw(out)
    if tone.getbbox() is None:
        return out
    px = tone.load()
    a = math.radians(angle); ca, sa = math.cos(a), math.sin(a)
    R = int(math.hypot(W, H) / cell / 2) + 2
    for i in range(-R, R + 1):
        for j in range(-R, R + 1):
            u, v = i * cell, j * cell
            x = W / 2 + u * ca - v * sa; y = H / 2 + u * sa + v * ca
            if 0 <= x < W and 0 <= y < H:
                t = px[int(x), int(y)] / 255
                if t > 0.04:
                    r = cell * 0.60 * math.sqrt(t)   # dot area ~ tone
                    d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return out


def flecks(density):
    # ink starvation: tiny unprinted specks inside solids
    sw, sh = W // 2, H // 2
    m = Image.frombytes("L", (sw, sh), bytes(255 if RNG.random() < density else 0 for _ in range(sw * sh)))
    return m.resize((W, H), Image.NEAREST).filter(ImageFilter.GaussianBlur(0.7)).point(lambda v: 255 if v > 100 else 0)


def banding():
    # horizontal roller density variation, 86-100 %
    b = Image.new("L", (1, H))
    for y in range(H):
        b.putpixel((0, y), int(255 * (0.93 + 0.07 * math.sin(y / 37.0) * math.sin(y / 211.0 + 1))))
    return b.resize((W, H))


def stencil_edge(m):
    return m.filter(ImageFilter.GaussianBlur(1.1)).point(lambda v: 255 if v > 118 else 0)


def compose():
    paper = Image.new("RGB", (W, H), PAPER)
    band = banding()
    for k in ORDER:
        cov = ImageChops.lighter(stencil_edge(L[k]["solid"]), halftone(L[k]["tone"], ANGLE[k]))
        cov = ImageChops.subtract(cov, flecks(0.035))
        cov = ImageChops.multiply(cov, band)
        cov = ImageChops.offset(cov, *OFFSET[k]).point(lambda v: int(v * 0.94))   # translucent ink
        layer = Image.composite(Image.new("RGB", (W, H), INKS[k]), Image.new("RGB", (W, H), (255, 255, 255)), cov)
        paper = ImageChops.multiply(paper, layer)     # overprint
    sw, sh = W // 2, H // 2
    nz = Image.frombytes("L", (sw, sh), bytes(RNG.randint(236, 255) for _ in range(sw * sh))).resize((W, H))
    return ImageChops.multiply(paper, Image.merge("RGB", (nz, nz, nz)))


def knock(k, shape, *a, **kw):
    # knock-out: clear an area from one drum so another ink sits on bare paper
    getattr(D(k), shape)(*a, fill=0, **kw)


def knock_all(shape, *a, inks=("yellow", "pink", "blue"), **kw):
    # clear every drum (solid and tone) so the area prints as bare paper
    for k in inks:
        for part in ("solid", "tone"):
            getattr(D(k, part), shape)(*a, fill=0, **kw)


def rot(cx, cy, w, h, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]]


# ---------------- heading + big number
fh = ImageFont.truetype(HEI, 168); glyphs_ok(fh, "知識庫")
D("pink").text((62, 58), "知識庫", font=fh, fill=255)
fl = ImageFont.truetype(DIN, 40)
D("blue").text((68, 262), "KNOWLEDGE BASE", font=fl, fill=255)
D("blue").rectangle([68, 312, 470, 318], fill=255)

f61 = ImageFont.truetype(DIN, 360)
D("yellow").rectangle([600, 96, 1010, 392], fill=255)        # yellow block under the number
D("blue").text((616, 52), "61%", font=f61, fill=255)          # blue on yellow overprints to green-black
# 61 % progress: 10 bars, 6 full + a tenth
for i in range(10):
    x = 600 + i * 42
    D("blue").rectangle([x, 452, x + 32, 492], outline=255, width=4)
    if i < 6:
        D("pink").rectangle([x, 452, x + 32, 492], fill=255)
D("pink").rectangle([852, 452, 856, 492], fill=255)

# ---------------- knowledge base: card catalogue cabinet
kx0, ky0, kx1, ky1 = 590, 620, 1015, 1040
D("blue", "tone").rectangle([kx0, ky0, kx1, ky1], fill=70)                 # 27 % blue body tint
D("blue").rectangle([kx0, ky0, kx1, ky1], outline=255, width=10)
D("blue").rectangle([kx0 - 14, ky0 - 22, kx1 + 14, ky0], fill=255)       # top slab
cols, rows = [616, 812], [650, 780, 910]
for r, y in enumerate(rows):
    for q, x in enumerate(cols):
        if r == 0 and q == 0:
            D("blue").rectangle([x, y, x + 176, y + 110], fill=255)          # dark open slot
            continue
        D("blue").rectangle([x, y, x + 176, y + 110], outline=255, width=6)
        D("yellow").rectangle([x + 58, y + 30, x + 118, y + 58], fill=255)   # label holder
        D("blue").rectangle([x + 58, y + 30, x + 118, y + 58], outline=255, width=4)
        D("blue").ellipse([x + 78, y + 70, x + 98, y + 90], fill=255)        # pull
# filed cards standing in the open drawer
for i, x in enumerate(range(630, 780, 26)):
    top = 672 + (i % 3) * 9
    knock_all("rectangle", [x, top, x + 18, 760])
    D("pink").rectangle([x, top, x + 18, top + 7], fill=255)          # coloured tab on each card

# ---------------- note card being lowered into the drawer (paper white, pink keyline)
card = rot(712, 636, 124, 160, 5)
knock_all("polygon", card)
D("pink").line(card + [card[0]], fill=255, width=7)
for k_, t in enumerate((0.25, 0.42, 0.59)):
    a = (card[0][0] + (card[3][0] - card[0][0]) * t + 22, card[0][1] + (card[3][1] - card[0][1]) * t)
    b = (card[1][0] + (card[2][0] - card[1][0]) * t - 22 - (40 if k_ == 2 else 0), card[1][1] + (card[2][1] - card[1][1]) * t)
    D("blue").line([a, b], fill=255, width=7)
D("yellow").ellipse([738, 576, 762, 600], fill=255)               # tag dot
# drawer front pulled forward over the slot
knock_all("rectangle", [606, 712, 802, 808], inks=("blue",))
D("blue").rectangle([606, 712, 802, 808], outline=255, width=8)
D("blue", "tone").rectangle([606, 712, 802, 808], fill=120)
D("yellow").rectangle([672, 738, 736, 764], fill=255)
# descent marks above the card
# pink down-arrow beside the card: "goes in here"
D("pink").line([(818, 540), (818, 604)], fill=255, width=10)
D("pink").polygon([(796, 596), (840, 596), (818, 630)], fill=255)

# ---------------- robot (machine: tread base, boxy torso, screen head with visor slit, antenna)
D("blue").rounded_rectangle([130, 962, 470, 1040], 38, fill=255)           # tread
for x in (178, 248, 318, 388):                                             # wheels (knock + yellow)
    knock("blue", "ellipse", [x - 22, 979, x + 22, 1023])
    D("yellow").ellipse([x - 22, 979, x + 22, 1023], fill=255)
    D("blue").ellipse([x - 7, 994, x + 7, 1008], fill=255)
D("blue").rectangle([214, 920, 386, 962], fill=255)                        # hip
D("yellow", "tone").rectangle([170, 700, 430, 920], fill=170)              # torso: yellow 67 %
D("blue").rectangle([170, 700, 430, 920], outline=255, width=9)
D("pink").rectangle([212, 742, 388, 840], fill=255)                        # chest panel
for i in range(3):
    knock("pink", "rectangle", [232, 760 + i * 26, 232 + 120 - i * 34, 772 + i * 26])
D("blue").rectangle([212, 864, 388, 876], fill=255)
D("blue").rectangle([270, 664, 330, 700], fill=255)                        # neck
D("blue").rounded_rectangle([160, 456, 440, 664], 46, fill=255)            # head
knock("blue", "rounded_rectangle", [196, 532, 404, 590], 28)               # visor slit knocked out
D("yellow").rounded_rectangle([196, 532, 404, 590], 28, fill=255)
D("pink", "tone").rounded_rectangle([196, 562, 404, 590], 14, fill=110)    # visor shading
D("pink").ellipse([140, 536, 170, 586], fill=255)                          # side bolts
D("pink").ellipse([430, 536, 460, 586], fill=255)
D("blue").rectangle([296, 396, 304, 456], fill=255)                        # antenna
D("pink").ellipse([276, 362, 324, 410], fill=255)
D("yellow", "tone").ellipse([110, 1022, 490, 1066], fill=110)              # floor shadow (tone)

# arm: shoulder -> elbow -> wrist, gripper pinching the card
pts = [(430, 760), (520, 660), (612, 642)]
D("blue").line(pts, fill=255, width=26, joint="curve")
for p in pts:
    D("pink").ellipse([p[0] - 20, p[1] - 20, p[0] + 20, p[1] + 20], fill=255)
D("blue").line([(612, 642), (668, 618)], fill=255, width=10)   # upper finger over the card edge
D("blue").line([(612, 642), (668, 668)], fill=255, width=10)   # lower finger

# ---------------- calm bottom (~22 %): ground rule, light yellow tint, one small credit line
D("blue").rectangle([60, 1080, 1020, 1086], fill=255)
D("yellow", "tone").rectangle([0, 1086, W, H], fill=46)
fs = ImageFont.truetype(DIN, 34)
D("blue").text((60, 1112), "NO.061  /  FILED", font=fs, fill=255)

compose().save(os.path.join(HERE, "sample.png"))
