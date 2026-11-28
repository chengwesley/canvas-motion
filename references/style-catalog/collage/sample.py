# Collage editorial style sample: cut paper, washi tape, torn edges, halftone, magazine type.
import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1350
rng = random.Random(61)
HERE = os.path.dirname(os.path.abspath(__file__))
HEITI = "/System/Library/Fonts/STHeiti Medium.ttc"
MENLO = "/System/Library/Fonts/Menlo.ttc"
SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"

CREAM = (241, 234, 218)
INK = (28, 26, 30)
RED = (214, 69, 52)
MUSTARD = (232, 182, 58)
TEAL = (46, 120, 122)
BLUE = (52, 84, 150)
PINK = (236, 164, 160)
KRAFT = (196, 160, 116)
NEWS = (226, 222, 210)

def font(p, s, i=0):
    return ImageFont.truetype(p, s, index=i)

def grain(size, base, amt=14, scale=3):
    # paper fiber noise: low-res random luminance upscaled
    w, h = max(1, size[0] // scale), max(1, size[1] // scale)
    n = Image.new("L", (w, h))
    n.putdata([128 + rng.randint(-amt, amt) for _ in range(w * h)])
    n = n.resize(size, Image.BILINEAR)
    img = Image.new("RGB", size, base)
    off = Image.merge("RGB", (n, n, n))
    return ImageChops.add(ImageChops.subtract(img, Image.new("RGB", size, (128,)*3)), off, 1, 0) if False else \
        Image.blend(img, ImageChops.multiply(img, Image.merge("RGB", [n.point(lambda v: min(255, v + 127))]*3)), 0.9)

def torn_mask(w, h, amp=6, step=7, sides="trbl"):
    # hand-torn edge: jittered polygon along each side
    m = Image.new("L", (w, h), 0)
    pts = []
    def J(on): return rng.uniform(0, amp) if on else 0
    for x in range(0, w, step): pts.append((x, J("t" in sides)))
    for y in range(0, h, step): pts.append((w - 1 - J("r" in sides), y))
    for x in range(w - 1, 0, -step): pts.append((x, h - 1 - J("b" in sides)))
    for y in range(h - 1, 0, -step): pts.append((J("l" in sides), y))
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m

def cut_piece(w, h, color, torn=True, border=0, pattern=None, amp=6):
    # paper piece with optional white torn fringe (exposed paper core) and print pattern
    face = grain((w, h), color)
    d = ImageDraw.Draw(face)
    if pattern == "halftone":
        dot_c = tuple(max(0, c - 70) for c in color)
        for yy in range(0, h, 12):
            for xx in range(0, w, 12):
                r = 1.2 + 3.6 * (xx / w)
                ox = 6 if (yy // 12) % 2 else 0
                d.ellipse((xx + ox - r, yy - r, xx + ox + r, yy + r), fill=dot_c)
    elif pattern == "stripes":
        sc = tuple(min(255, c + 40) for c in color)
        for k in range(-h, w, 18): d.line((k, 0, k + h, h), fill=sc, width=6)
    elif pattern == "lines":
        for yy in range(30, h, 26): d.line((14, yy, w - 14, yy), fill=(150, 170, 200), width=2)
        d.line((48, 0, 48, h), fill=(220, 120, 120), width=2)
    elif pattern == "news":
        f = font(HEITI, 15)
        for yy in range(10, h, 20):
            s = "".join(rng.choice("知識庫筆記資料卡片記錄") for _ in range(w // 15))
            d.text((8, yy), s, font=f, fill=(90, 86, 80))
    mask = torn_mask(w, h, amp) if torn else Image.new("L", (w, h), 255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if border:
        fringe = Image.new("RGBA", (w, h), (250, 247, 238, 255))
        out.paste(fringe, (0, 0), mask)
        inner = torn_mask(w - 2 * border, h - 2 * border, amp) if torn else Image.new("L", (w - 2 * border, h - 2 * border), 255)
        out.paste(face.crop((border, border, w - border, h - border)), (border, border), inner)
    else:
        out.paste(face, (0, 0), mask)
    return out

def place(canvas, piece, x, y, angle=0, shadow=(6, 8), blur=6, sop=90):
    # glue piece onto canvas with soft drop shadow (paper lifted off page)
    p = piece.rotate(angle, resample=Image.BICUBIC, expand=True)
    a = p.split()[3]
    sh = Image.new("RGBA", p.size, (40, 30, 20, 0))
    sh.putalpha(a.point(lambda v: v * sop // 255).filter(ImageFilter.GaussianBlur(blur)))
    canvas.alpha_composite(sh, (int(x - p.width / 2 + shadow[0]), int(y - p.height / 2 + shadow[1])))
    canvas.alpha_composite(p, (int(x - p.width / 2), int(y - p.height / 2)))

def washi(canvas, x, y, length, angle, color, width=44):
    # translucent masking tape with zigzag cut ends and printed stripes
    t = Image.new("RGBA", (length, width), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    pts = []
    for yy in range(0, width + 1, 6): pts.append((rng.uniform(0, 5) if (yy // 6) % 2 else 0, yy))
    for yy in range(width, -1, -6): pts.append((length - 1 - (rng.uniform(0, 5) if (yy // 6) % 2 else 0), yy))
    d.polygon(pts, fill=color + (165,))
    lc = tuple(min(255, c + 50) for c in color) + (120,)
    for k in range(-width, length, 16): d.line((k, 0, k + width, width), fill=lc, width=4)
    t = t.rotate(angle, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(t, (int(x - t.width / 2), int(y - t.height / 2)))

def cut_letters(canvas, text, x, y, size, palette, fnt):
    # ransom-note style: each glyph on its own snipped paper block
    for i, ch in enumerate(text):
        bg, fg = palette[i % len(palette)]
        f = font(fnt, size)
        bb = f.getbbox(ch)
        cw, chh = bb[2] - bb[0] + 36, bb[3] - bb[1] + 40
        p = cut_piece(cw, chh, bg, torn=False)
        ImageDraw.Draw(p).text((18 - bb[0], 20 - bb[1]), ch, font=f, fill=fg)
        place(canvas, p, x + cw / 2, y, rng.uniform(-6, 6), blur=4)
        x += cw - 6

# ---- base page
page = grain((W, H), CREAM, amt=18, scale=2).convert("RGBA")
pd = ImageDraw.Draw(page)
# faint registration grid like magazine layout paper
for gx in range(60, W, 120): pd.line((gx, 0, gx, int(H * 0.78)), fill=(225, 216, 196, 255), width=1)

# ---- big background blocks
place(page, cut_piece(620, 560, NEWS, pattern="news", amp=9), 700, 520, 3, sop=60)
place(page, cut_piece(380, 380, MUSTARD, pattern="halftone"), 260, 330, -5)

# ---- header: masthead strip + heading
mast = cut_piece(1000, 70, INK, torn=False)
md = ImageDraw.Draw(mast)
md.text((24, 18), "ISSUE 07  /  NOTES  ARCHIVE  MEMORY", font=font(MENLO, 26), fill=CREAM)
md.text((820, 18), "p.61", font=font(MENLO, 26), fill=MUSTARD)
place(page, mast, W / 2, 64, -1, blur=3)
cut_letters(page, "知識庫", 70, 200, 104, [(CREAM, INK), (RED, CREAM), (INK, CREAM)], HEITI)

# ---- knowledge base: cut-paper bookshelf
shelf_x, shelf_y, sw, sh_ = 560, 340, 440, 520
cab = cut_piece(sw, sh_, KRAFT, torn=False)   # Hoch/Bearden: primary pieces are knife-cut, straight edges
cd = ImageDraw.Draw(cab)
rows = 4
for r in range(rows):
    by = 30 + r * 122
    xx = 26
    while xx < sw - 40:
        bw = rng.randint(22, 44); bh = rng.randint(70, 100)
        col = rng.choice([RED, TEAL, BLUE, INK, MUSTARD, PINK, CREAM])
        cd.rectangle((xx, by + 100 - bh, xx + bw, by + 100), fill=col)
        cd.line((xx + 5, by + 100 - bh + 10, xx + bw - 5, by + 100 - bh + 10), fill=CREAM if col != CREAM else INK, width=2)
        xx += bw + 3
    cd.rectangle((14, by + 100, sw - 14, by + 112), fill=(120, 88, 58))
# one empty slot glowing
cd.rectangle((sw - 120, 30 + 2 * 122 + 20, sw - 40, 30 + 2 * 122 + 100), fill=(250, 240, 200))
place(page, cab, shelf_x + sw / 2, shelf_y + sh_ / 2, 1.5)
washi(page, shelf_x + 60, shelf_y - 4, 180, 18, TEAL)
washi(page, shelf_x + sw - 40, shelf_y + 10, 160, -24, RED)
# ---- AI agent: robot built from cut paper (boxy head, visor slit, grille, bolts, jointed arm with claw, treads)
ax, ay = 240, 610
def bolt(cx, cy, r=9):
    j = Image.new("RGBA", (2*r+2, 2*r+2), (0, 0, 0, 0)); jd = ImageDraw.Draw(j)
    jd.ellipse((0, 0, 2*r+1, 2*r+1), fill=INK + (255,), outline=CREAM + (255,), width=3)
    jd.line((r-4, r+1, r+6, r+1), fill=CREAM + (255,), width=2)
    place(page, j, cx, cy, 0, blur=2, shadow=(2, 3), sop=70)
def limb(p, q, th, color):
    ln = int(math.hypot(q[0]-p[0], q[1]-p[1])) + th
    ang = -math.degrees(math.atan2(q[1]-p[1], q[0]-p[0]))
    place(page, cut_piece(ln, th, color, torn=False), (p[0]+q[0])/2, (p[1]+q[1])/2, ang, blur=4)
# treads + legs
place(page, cut_piece(270, 62, INK, torn=False), ax, ay + 205, 0, blur=4)
for k in range(-4, 5): bolt(ax + k * 28, ay + 205, 7)
# torso
place(page, cut_piece(230, 260, BLUE, pattern="stripes", border=8, torn=False), ax, ay + 40, -2)
place(page, cut_piece(150, 100, CREAM, border=0, torn=False), ax, ay + 70, 1)
cp = ImageDraw.Draw(page)
for i in range(4):  # chest vent slats
    place(page, cut_piece(110, 12, INK, torn=False), ax, ay + 40 + i * 20, 1, blur=2, shadow=(1, 2))
core = Image.new("RGBA", (90, 90), (0, 0, 0, 0)); cd2 = ImageDraw.Draw(core)
cd2.ellipse((0, 0, 89, 89), fill=MUSTARD + (255,)); cd2.ellipse((22, 22, 67, 67), fill=INK + (255,)); cd2.ellipse((36, 36, 53, 53), fill=CREAM + (255,))
place(page, core, ax, ay - 50, 0, blur=4)
# neck + head
place(page, cut_piece(60, 30, INK, torn=False), ax, ay - 100, 0, blur=2)
place(page, cut_piece(190, 120, TEAL, border=7, torn=False), ax, ay - 170, 2)
place(page, cut_piece(150, 30, INK, torn=False), ax, ay - 178, 2, blur=2)          # visor slit (no eyes/mouth)
place(page, cut_piece(100, 12, MUSTARD, torn=False), ax - 10, ay - 178, 2, blur=0, shadow=(0, 0), sop=0)
for gx in range(-60, 61, 24): place(page, cut_piece(8, 22, INK, torn=False), ax + gx, ay - 140, 2, blur=1, shadow=(1, 1))
place(page, cut_piece(14, 70, INK, torn=False), ax + 50, ay - 262, 8, blur=3)       # antenna
bolt(ax + 62, ay - 300, 12)
bolt(ax - 82, ay - 210, 7); bolt(ax + 86, ay - 210, 7)
# shoulder, jointed arm, ENLARGED pincer claw (Hoch/Bearden scale jump: the working hand is the biggest part)
sh_p, el_p, hd_p = (ax + 112, ay - 20), (ax + 300, ay + 70), (ax + 520, ay - 112)
limb(sh_p, el_p, 36, RED); limb(el_p, hd_p, 32, RED)
for jp, r in ((sh_p, 26), (el_p, 24)): bolt(jp[0], jp[1], r)

# ---- note card dropped into the pocket of the shelf: lower half hidden behind a front pocket piece (occlusion)
card = cut_piece(176, 134, (252, 250, 242), torn=False, pattern="lines")
ImageDraw.Draw(card).text((56, 10), "NOTE #61", font=font(MENLO, 18), fill=RED)
ImageDraw.Draw(card).text((56, 38), "會議重點", font=font(HEITI, 24), fill=INK)
place(page, card, 930, 588, -4, shadow=(12, 14), blur=9)
washi(page, 940, 526, 100, -14, MUSTARD, width=32)
pocket = cut_piece(190, 80, KRAFT, torn=False)
pk = ImageDraw.Draw(pocket)
for xx in range(14, 176, 18): pk.line((xx, 14, xx + 9, 14), fill=(120, 88, 58), width=3)   # stitch dashes
pk.line((0, 79, 190, 79), fill=(120, 88, 58), width=6)
place(page, pocket, 920, 640, 1.5, blur=5)
# claw jaws drawn last so they bite the card edge
for jp, r in ((hd_p, 28),): bolt(jp[0], jp[1], r)
limb((hd_p[0] + 10, hd_p[1] - 22), (hd_p[0] + 100, hd_p[1] - 30), 24, INK)
limb((hd_p[0] + 10, hd_p[1] + 22), (hd_p[0] + 100, hd_p[1] + 34), 24, INK)
# ---- big 61%
cut_letters(page, "61", 70, 905, 190, [(RED, CREAM), (INK, MUSTARD)], HEITI)
place(page, cut_piece(150, 150, PINK, pattern="halftone"), 470, 905, 8)
pct = Image.new("RGBA", (150, 150), (0, 0, 0, 0)); ImageDraw.Draw(pct).text((14, -6), "%", font=font(HEITI, 140), fill=INK)
place(page, pct, 470, 905, 8, shadow=(0, 0), sop=0)
washi(page, 150, 790, 200, -6, PINK)
tk = cut_piece(250, 84, (232, 214, 170), torn=False)
tkd = ImageDraw.Draw(tk)
for yy in range(6, 84, 14): tkd.ellipse((-6, yy, 6, yy + 8), fill=CREAM)          # perforated stub edge
tkd.text((26, 8), "No.0061", font=font(MENLO, 30), fill=RED)
tkd.text((26, 46), "KNOWLEDGE / 庫", font=font(HEITI, 22), fill=INK)
place(page, tk, 855, 893, 4, blur=3)
lbl = cut_piece(300, 54, CREAM, torn=False); ImageDraw.Draw(lbl).text((14, 12), "已歸檔的筆記比例", font=font(HEITI, 28), fill=INK)
place(page, lbl, 760, 960, -2, blur=4)

# ---- calm footer (bottom ~22%)
fy = int(H * 0.78)
pd.rectangle((0, fy, W, H), fill=CREAM + (255,))
pd.line((60, fy + 40, W - 60, fy + 40), fill=INK + (255,), width=3)
pd.text((60, fy + 70), "筆記，放進知識庫。", font=font(HEITI, 40), fill=INK + (255,))
pd.text((60, fy + 140), "COLLAGE  EDITORIAL  ·  KNOWLEDGE BASE", font=font(MENLO, 20), fill=(110, 100, 90, 255))

page.convert("RGB").save(os.path.join(HERE, "sample.png"))
