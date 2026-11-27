# Soft clay style sample (original): rounded volumes, 4-tone clay ramps, key light top-left,
# warm bounce light lower-right, tinted contact shadows, very fine surface grain.
import os, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

W, H = 1080, 1350
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample.png")
RNG = random.Random(61)
HEI = "/System/Library/Fonts/STHeiti Medium.ttc"
ROUND = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"


def rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# 4-tone ramps: shadow, base, light, highlight
SHELL = [rgb("B8AEB0"), rgb("ECE6E0"), rgb("F8F5F0"), rgb("FFFFFF")]
VISOR = [rgb("252C52"), rgb("3B4680"), rgb("5D6FB4"), rgb("B4C2F2")]
ORANGE = [rgb("C25E36"), rgb("F08A55"), rgb("FFB487"), rgb("FFE4D2")]
MINT = [rgb("5E9688"), rgb("92C6B8"), rgb("BDE3D7"), rgb("EEFAF5")]
CREAM = [rgb("CDB98F"), rgb("FFF2D6"), rgb("FFF9EA"), rgb("FFFFFF")]
INDIGO = [rgb("2F3B7A"), rgb("4C5CA8"), rgb("7586CF"), rgb("C5CEF5")]
BG_TOP, BG_BOT, FLOOR = rgb("F7E7DC"), rgb("F0D5C8"), rgb("EBC9BA")
SHADOW = rgb("9A6C6C")   # tinted shadow, never black
BOUNCE = rgb("FFC9A8")   # warm floor bounce light
CAVITY = rgb("3E4E56")   # deep recess inside the cabinet

GRAIN = None


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_grain(strength=4.0, scale=2):
    w, h = W // scale, H // scale
    n = Image.new("L", (w, h)); n.putdata([128 + int(RNG.gauss(0, strength)) for _ in range(w * h)])
    return n.resize((W, H), Image.BICUBIC)


def solid(size, c):
    return Image.new("RGB", size, c)


def crop_box(mask, pad):
    b = mask.getbbox()
    return (max(0, b[0] - pad), max(0, b[1] - pad), min(W, b[2] + pad), min(H, b[3] + pad))


def cast_shadow(c, mask, dx=10, dy=22, blur=22, alpha=0.30):
    box = crop_box(mask, blur * 3 + 30)
    m = mask.crop(box); sz = m.size
    region = c.crop(box)
    far = ImageChops.offset(m, dx, dy).filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
    region.paste(solid(sz, SHADOW), (0, 0), far)
    near = ImageChops.offset(m, 2, 6).filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * alpha * 0.9))
    region.paste(solid(sz, mix(SHADOW, (40, 20, 30), 0.3)), (0, 0), near)
    c.paste(region, box[:2])


def clay(c, mask, ramp, soft=16, shadow=True, gloss=True):
    """Shade one clay lump. soft = size of the rounded falloff in px."""
    if shadow:
        cast_shadow(c, mask)
    box = crop_box(mask, soft * 3 + 10)
    m = mask.crop(box); sz = m.size
    S, B, L, Hi = ramp
    body = solid(sz, S)
    # 1 base: shrink the mask softly so the rim stays in shadow (ambient occlusion feel)
    core = m.filter(ImageFilter.GaussianBlur(soft * 0.6)).point(lambda v: max(0, min(255, (v - 70) * 3)))
    body.paste(solid(sz, B), (0, 0), core)
    # 2 light lobe toward top-left
    k = int(soft * 0.8)
    lit = ImageChops.subtract(core, ImageChops.offset(core, k, k)).filter(ImageFilter.GaussianBlur(soft * 0.5))
    body.paste(solid(sz, L), (0, 0), lit.point(lambda v: min(235, int(v * 1.6))))
    # 3 warm bounce on lower-right rim
    rim = ImageChops.subtract(m, ImageChops.offset(m, -max(3, soft // 3), -max(3, soft // 3)))
    body.paste(solid(sz, mix(S, BOUNCE, 0.45)), (0, 0), rim.filter(ImageFilter.GaussianBlur(max(2, soft // 4))).point(lambda v: int(v * 0.7)))
    # 4 specular: small soft glint near top-left of the lump
    if gloss:
        g = ImageChops.subtract(core, ImageChops.offset(core, int(k * 0.5), int(k * 0.5)))
        g = g.filter(ImageFilter.GaussianBlur(soft * 0.3)).point(lambda v: 210 if v > 170 else int(v * 0.25))
        body.paste(solid(sz, Hi), (0, 0), g.filter(ImageFilter.GaussianBlur(max(1, soft * 0.25))))
    # 5 fine grain (fingerprint-scale, very subtle)
    gr = GRAIN.crop(box)
    body = Image.merge("RGB", [ImageChops.add(ch, gr, 1, -128) for ch in body.split()])
    region = c.crop(box)
    region.paste(body, (0, 0), m.filter(ImageFilter.GaussianBlur(1.0)))
    c.paste(region, box[:2])


def new_mask():
    return Image.new("L", (W, H), 0)


def rr(box, r):
    m = new_mask(); ImageDraw.Draw(m).rounded_rectangle(box, r, fill=255); return m


def ell(box):
    m = new_mask(); ImageDraw.Draw(m).ellipse(box, fill=255); return m


def text_mask(t, font, xy, puff=0):
    # puff = stroke in px that fattens glyphs into rounded clay coils
    m = new_mask(); ImageDraw.Draw(m).text(xy, t, font=font, fill=255, stroke_width=puff, stroke_fill=255); return m


def groove(c, pts, width=6):
    # tool-pressed line: dark trough, light lip just below
    d = new_mask(); ImageDraw.Draw(d).line(pts, fill=255, width=width, joint="curve")
    c.paste(solid((W, H), (255, 248, 240)), (0, 0), ImageChops.offset(d, 0, 3).filter(ImageFilter.GaussianBlur(1.5)).point(lambda v: int(v * 0.6)))
    c.paste(solid((W, H), SHADOW), (0, 0), d.filter(ImageFilter.GaussianBlur(1.5)).point(lambda v: int(v * 0.55)))


def glyphs_ok(font, text):
    # every CJK char must differ from the font's notdef box
    nd = font.getmask("￿").getbbox(), bytes(font.getmask("￿"))
    for ch in text:
        m = font.getmask(ch)
        if m.getbbox() is None or (m.getbbox(), bytes(m)) == nd:
            raise SystemExit("missing glyph: " + ch)


def background():
    bg = Image.new("RGB", (W, H)); d = ImageDraw.Draw(bg)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=mix(BG_TOP, BG_BOT, y / H))
    floor = new_mask(); ImageDraw.Draw(floor).rectangle([0, 1035, W, H], fill=255)
    bg.paste(solid((W, H), FLOOR), (0, 0), floor.filter(ImageFilter.GaussianBlur(24)))
    v = new_mask(); ImageDraw.Draw(v).ellipse([-260, -160, W + 260, H + 140], fill=255)
    v = ImageChops.invert(v.filter(ImageFilter.GaussianBlur(150))).point(lambda x: int(x * 0.28))
    bg.paste(solid((W, H), rgb("D7A79E")), (0, 0), v)
    return Image.merge("RGB", [ImageChops.add(ch, GRAIN, 1, -128) for ch in bg.split()])


def main():
    global GRAIN
    GRAIN = make_grain()
    c = background()

    # --- heading 知識庫 + big number with a clay progress bar
    fh = ImageFont.truetype(HEI, 128); glyphs_ok(fh, "知識庫")
    clay(c, text_mask("知識庫", fh, (76, 88), puff=2), INDIGO, soft=7)
    fn = ImageFont.truetype(ROUND, 230)
    clay(c, text_mask("61%", fn, (548, 40), puff=3), ORANGE, soft=12)
    clay(c, rr([570, 318, 1000, 370], 26), SHELL, soft=10)
    clay(c, rr([578, 326, 578 + int(414 * 0.61), 362], 18), ORANGE, soft=8, shadow=False)

    # --- knowledge base: clay card-catalogue cabinet, top-left drawer pulled open
    cx0, cy0, cx1, cy1 = 600, 590, 1005, 1030
    clay(c, rr([cx0, cy0, cx1, cy1], 54), MINT, soft=20)
    dw, dh = 160, 118
    cols = [632, 812]; rows = [632, 772, 900]
    for r, y in enumerate(rows):
        for q, x in enumerate(cols):
            if r == 0 and q == 0:
                # open slot: dark recess
                clay(c, rr([x - 4, y - 8, x + dw + 4, y + dh + 4], 22), [CAVITY, mix(CAVITY, MINT[0], .35), mix(CAVITY, MINT[0], .5), MINT[0]], soft=10, shadow=False, gloss=False)
                continue
            clay(c, rr([x, y, x + dw, y + dh], 24), MINT, soft=10, shadow=False)
            clay(c, rr([x + 52, y + 50, x + dw - 52, y + 74], 12), ORANGE, soft=5)   # handle
    # filed cards standing inside the open drawer (tops only)
    for i, x in enumerate(range(648, 776, 26)):
        clay(c, rr([x, 640 + (i % 2) * 8, x + 20, 720], 8), CREAM, soft=5, shadow=False, gloss=False)

    # --- the note card being lowered into the open drawer (drawn before the drawer front)
    card = Image.new("L", (150, 196), 0)
    ImageDraw.Draw(card).rounded_rectangle([0, 0, 149, 195], 24, fill=255)
    card = card.rotate(6, expand=True, resample=Image.BICUBIC)
    cm = new_mask(); cm.paste(card, (650, 468))
    clay(c, cm, CREAM, soft=12)
    for (a, b) in [((682, 512), (772, 503)), ((684, 548), (774, 539)), ((686, 584), (748, 578))]:
        groove(c, [a, b], width=8)
    clay(c, ell([752, 488, 778, 514]), ORANGE, soft=5, shadow=False)   # tag dot on the card

    # drawer front, pulled forward and down
    clay(c, rr([616, 704, 808, 800], 24), MINT, soft=12)
    clay(c, rr([678, 740, 746, 766], 12), ORANGE, soft=5)
    # soft mint glow rising from the drawer = "accepted"
    gm = new_mask(); ImageDraw.Draw(gm).ellipse([640, 560, 800, 680], fill=120)
    c.paste(solid((W, H), MINT[3]), (0, 0), gm.filter(ImageFilter.GaussianBlur(30)))

    # --- robot (machine read: visor band, bolts, antenna, chest lights, tread base; no face)
    clay(c, rr([150, 958, 452, 1034], 38), INDIGO, soft=12)                 # tread base
    for x in (192, 260, 328, 396):
        clay(c, ell([x - 18, 978, x + 18, 1014]), SHELL, soft=6, shadow=False)  # wheels
    clay(c, rr([196, 905, 406, 966], 20), SHELL, soft=10)                   # hip
    clay(c, rr([180, 700, 422, 930], 92), SHELL, soft=22)                   # torso
    clay(c, rr([230, 760, 372, 858], 30), VISOR, soft=10, shadow=False)     # chest screen
    for i, col in enumerate([MINT, ORANGE, MINT]):
        clay(c, ell([254 + i * 36, 796, 278 + i * 36, 820]), col, soft=4, shadow=False)
    groove(c, [(240, 890), (362, 890)])
    clay(c, rr([270, 664, 332, 712], 14), SHELL, soft=8)                    # neck
    clay(c, ell([150, 552, 194, 596]), ORANGE, soft=7)                      # ear bolts
    clay(c, ell([408, 552, 452, 596]), ORANGE, soft=7)
    clay(c, rr([170, 456, 432, 686], 96), SHELL, soft=24)                   # head
    clay(c, rr([200, 532, 402, 606], 37), VISOR, soft=10, shadow=False)     # visor band
    # visor reflection sweep (a light strip, not eyes)
    vm = new_mask(); ImageDraw.Draw(vm).rounded_rectangle([224, 546, 330, 558], 6, fill=150)
    c.paste(solid((W, H), VISOR[3]), (0, 0), vm.filter(ImageFilter.GaussianBlur(3)))
    clay(c, rr([292, 384, 310, 462], 9), SHELL, soft=5)                     # antenna
    clay(c, ell([270, 342, 332, 404]), ORANGE, soft=10)

    # arm: shoulder ball -> upper arm -> elbow -> forearm -> gripper holding the card
    arm = new_mask(); da = ImageDraw.Draw(arm)
    da.line([(412, 772), (508, 676)], fill=255, width=50)
    clay(c, arm, SHELL, soft=12)
    arm2 = new_mask(); ImageDraw.Draw(arm2).line([(508, 676), (628, 590)], fill=255, width=44)
    clay(c, arm2, SHELL, soft=11)
    clay(c, ell([382, 742, 442, 802]), ORANGE, soft=9)                       # shoulder
    clay(c, ell([480, 648, 536, 704]), ORANGE, soft=9)                       # elbow
    clay(c, ell([606, 564, 660, 618]), INDIGO, soft=8)                       # wrist
    # two-finger gripper pinching the card's lower-left edge
    f1 = new_mask(); ImageDraw.Draw(f1).line([(640, 578), (672, 548)], fill=255, width=18)
    f2 = new_mask(); ImageDraw.Draw(f2).line([(646, 606), (680, 590)], fill=255, width=18)
    clay(c, f1, INDIGO, soft=5, shadow=False)
    clay(c, f2, INDIGO, soft=5, shadow=False)

    # --- calm bottom (~22%): floor only, one soft highlight line on the table edge
    hl = new_mask(); ImageDraw.Draw(hl).line([(0, 1042), (W, 1042)], fill=90, width=3)
    c.paste(solid((W, H), rgb("FBEDE5")), (0, 0), hl.filter(ImageFilter.GaussianBlur(2)))

    c.save(OUT)


if __name__ == "__main__":
    main()
