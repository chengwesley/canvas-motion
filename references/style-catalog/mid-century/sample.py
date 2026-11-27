# Mid-century illustration sample: misregistered colour blocks, dry-brush texture,
# warm muted palette, simplified geometric shapes, paper grain.
import os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1350
S = 2  # draw at half resolution, upscale
w, h = W // S, H // S
R = random.Random(1957)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample.png")

PAPER = (238, 226, 200)
INK = (52, 44, 38)
MUSTARD = (214, 160, 58)
RUST = (190, 88, 52)
TEAL = (52, 112, 108)
OLIVE = (128, 132, 78)
PINK = (222, 160, 138)
SKY = (176, 196, 182)

def shade(c, d):
    return tuple(max(0, min(255, v + d)) for v in c)

def dry_brush(dr, box, col, n=40, horiz=True):
    # streaky brush marks inside a block; broken strokes with gaps
    x0, y0, x1, y1 = box
    for _ in range(n):
        c = shade(col, R.choice([-18, -10, 12, 18]))
        if horiz:
            y = R.uniform(y0, y1); xs = R.uniform(x0, x1 - 4); L = R.uniform(10, (x1 - x0) * 0.8)
            x = xs
            while x < min(xs + L, x1):
                seg = R.uniform(3, 14)
                dr.line([(x, y), (min(x + seg, x1), y + R.uniform(-0.6, 0.6))], fill=c, width=1)
                x += seg + R.uniform(1, 5)
        else:
            x = R.uniform(x0, x1); ys = R.uniform(y0, y1 - 4); L = R.uniform(10, (y1 - y0) * 0.8)
            y = ys
            while y < min(ys + L, y1):
                seg = R.uniform(3, 14)
                dr.line([(x, y), (x + R.uniform(-0.6, 0.6), min(y + seg, y1))], fill=c, width=1)
                y += seg + R.uniform(1, 5)

def misreg_rect(dr, box, col, off=(4, -3), brush=True, horiz=True, outline=True):
    # colour fill and ink outline printed out of register
    x0, y0, x1, y1 = box
    dr.rectangle(box, fill=col)
    if brush:
        dry_brush(dr, box, col, n=int((x1 - x0) * (y1 - y0) / 120) + 8, horiz=horiz)
    if outline:
        ox, oy = off
        rough_line(dr, [(x0+ox, y0+oy), (x1+ox, y0+oy), (x1+ox, y1+oy), (x0+ox, y1+oy), (x0+ox, y0+oy)])

def misreg_ellipse(dr, box, col, off=(-4, 3), brush=True):
    dr.ellipse(box, fill=col)
    ox, oy = off
    b = (box[0]+ox, box[1]+oy, box[2]+ox, box[3]+oy)
    dr.arc(b, R.uniform(10, 60), R.uniform(250, 330), fill=INK, width=2)

def rough_line(dr, pts, width=2):
    # hand-inked line with slight wobble and skipped bits
    for (a, b) in zip(pts, pts[1:]):
        steps = max(2, int(((b[0]-a[0])**2 + (b[1]-a[1])**2) ** 0.5 / 6))
        prev = a
        for i in range(1, steps + 1):
            t = i / steps
            p = (a[0] + (b[0]-a[0]) * t + R.uniform(-0.7, 0.7), a[1] + (b[1]-a[1]) * t + R.uniform(-0.7, 0.7))
            if R.random() > 0.08:
                dr.line([prev, p], fill=INK, width=width)
            prev = p

def stipple(dr, box, col, n):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = R.uniform(x0, x1), R.uniform(y0, y1)
        dr.point((x, y), fill=col)

def grain(img, amt=14):
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            d = R.randint(-amt, amt)
            r, g, b = px[x, y]
            px[x, y] = (max(0, min(255, r+d)), max(0, min(255, g+d)), max(0, min(255, b+d)))

img = Image.new("RGB", (w, h), PAPER)
dr = ImageDraw.Draw(img)

# background blocks (offset, overlapping)
misreg_rect(dr, (0, 120, 300, 520), SKY, outline=False, horiz=False)
misreg_ellipse(dr, (360, 40, 500, 180), MUSTARD)
dr.polygon([(250, 525), (540, 300), (540, 525)], fill=shade(PINK, 10))
dry_brush(dr, (300, 380, 540, 525), PINK, n=60)

# knowledge base: tall cabinet with shelves of book blocks
cab = (300, 230, 500, 525)
misreg_rect(dr, cab, TEAL, off=(5, -4))
cols = [MUSTARD, RUST, PAPER, PINK, OLIVE]
for i in range(4):
    sy = 255 + i * 66
    dr.rectangle((312, sy + 50, 488, sy + 56), fill=shade(TEAL, -30))
    x = 316
    while x < 480:
        bw = R.randint(10, 22); bh = R.randint(30, 48)
        c = R.choice(cols)
        dr.rectangle((x, sy + 50 - bh, x + bw - 2, sy + 50), fill=c)
        dry_brush(dr, (x, sy + 50 - bh, x + bw - 2, sy + 50), c, n=3, horiz=False)
        if R.random() < 0.5:
            dr.line([(x + 2, sy + 56 - bh), (x + bw - 4, sy + 56 - bh)], fill=INK, width=1)
        x += bw
# open slot on top shelf where card goes
dr.rectangle((440, 262, 476, 305), fill=shade(TEAL, -40))
# network dots on cabinet top
for i, (nx, ny) in enumerate([(320, 205), (370, 185), (420, 210), (470, 190)]):
    dr.ellipse((nx-6, ny-6, nx+6, ny+6), fill=RUST if i % 2 else MUSTARD)
rough_line(dr, [(320, 205), (370, 185), (420, 210), (470, 190)], width=1)

# robot agent: stacked geometric blocks, visor slot, no face
misreg_rect(dr, (90, 300, 210, 420), RUST, off=(-4, 3))       # body
misreg_rect(dr, (110, 245, 190, 300), MUSTARD, off=(4, 2))    # head
dr.rectangle((118, 262, 182, 276), fill=INK)                  # visor slot
dr.rectangle((124, 266, 160, 272), fill=SKY)
rough_line(dr, [(150, 245), (150, 222)])
dr.ellipse((143, 214, 157, 228), fill=TEAL)
dr.ellipse((128, 335, 172, 379), fill=PAPER)                  # chest dial
dr.pieslice((128, 335, 172, 379), -90, -90 + 360 * 0.61, fill=TEAL)
misreg_rect(dr, (100, 420, 130, 500), OLIVE, off=(3, 2))      # legs
misreg_rect(dr, (170, 420, 200, 500), OLIVE, off=(3, 2))
# arm reaching to shelf
arm = [(205, 330), (300, 300), (420, 282)]
dr.line(arm, fill=INK, width=8)
dr.line(arm, fill=TEAL, width=5)
# note card being placed
card = [(408, 250), (452, 244), (458, 300), (414, 306)]
dr.polygon(card, fill=PAPER)
rough_line(dr, [(411, 253), (455, 247), (461, 303), (417, 309), (411, 253)])
for k in range(3):
    dr.line([(416, 262 + k * 10), (446, 258 + k * 10)], fill=RUST, width=2)
# motion ticks
for k in range(3):
    dr.line([(380 - k * 4, 236 + k * 8), (395 - k * 4, 238 + k * 8)], fill=INK, width=1)

# calm bottom band (~22%)
misreg_rect(dr, (0, 525, w, h), OLIVE, outline=False)
dr.rectangle((0, 525, w, 530), fill=shade(OLIVE, -30))
stipple(dr, (0, 535, w, h), shade(OLIVE, 22), 500)

grain(img, 10)
img = img.resize((W, H), Image.LANCZOS)
dr = ImageDraw.Draw(img)

# typography at full res, slightly misregistered double print
hei = "/System/Library/Fonts/STHeiti Medium.ttc"
song = "/System/Library/Fonts/Supplemental/Songti.ttc"
fH = ImageFont.truetype(hei, 120)
fN = ImageFont.truetype(hei, 230)
fS = ImageFont.truetype(song, 34)
def print_text(xy, t, f, col):
    x, y = xy
    dr.text((x + 6, y + 5), t, font=f, fill=shade(col, -60))
    dr.text((x, y), t, font=f, fill=col)
print_text((60, 50), "知識庫", fH, INK)
dr.text((64, 190), "一張筆記，一格書架", font=fS, fill=INK)
print_text((40, 1090), "61%", fN, RUST)
img.save(OUT)
print(OUT)
