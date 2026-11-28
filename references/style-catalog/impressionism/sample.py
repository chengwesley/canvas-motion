#!/usr/bin/env python3
"""Original artwork. Subject shared by every catalog entry: an AI agent (a robot, no cartoon face)
slides a note card into the knowledge base; big number 61% and the heading beside it.
Python 3 + PIL only, deterministic, no numpy."""
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1350
GROUND = 1052                       # bottom ~22% (y > 1052) stays calm for subtitles
HERE = os.path.dirname(os.path.abspath(__file__))
HEI = '/System/Library/Fonts/STHeiti Medium.ttc'
AVE = '/System/Library/Fonts/Avenir Next.ttc'


def F(path, size, idx=0):
    return ImageFont.truetype(path, size, index=idx)


def check_glyphs(s, path=HEI, idx=0):
    """Raise if any character renders as the missing-glyph box or as nothing."""
    f = F(path, 60, idx)

    def render(ch):
        im = Image.new('L', (90, 90), 0)
        ImageDraw.Draw(im).text((10, 5), ch, font=f, fill=255)
        return im.tobytes()
    nd = render('￿')
    for ch in s:
        if ch.isspace():
            continue
        b = render(ch)
        if b == nd or not any(b):
            raise ValueError('glyph missing: %r' % ch)


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------- shared scene geometry (all styles interpret the same layout) ----------
def ik(s, h, l1, l2, sign=1):
    dx, dy = h[0] - s[0], h[1] - s[1]
    d = min(math.hypot(dx, dy), l1 + l2 - 1)
    a = math.atan2(dy, dx)
    A = math.acos((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))
    return (s[0] + l1 * math.cos(a + sign * A), s[1] + l1 * math.sin(a + sign * A))


SH_L, SH_T, SH_R, SH_B = 515, 360, 945, 1030          # knowledge base cabinet
ROWS = (360, 554, 748, 1030)                            # row bounds (.29/.29/.42 of 670)
CARD = (585, 782, 703, 946)                             # the new note card (x0,y0,x1,y1)
FRONT_Y = 917                                           # drawer front plate top (hides the lower card)
SHOULD_R, SHOULD_L = (438, 745), (242, 745)
HAND_R = (589, 846)
ELB_R = ik(SHOULD_R, HAND_R, 92, 92, -1)
HAND_L = (212, 940)
ELB_L = (221, 842)

_br = random.Random(3)
BOOKS = []                                              # (row, x0, x1, y0, y1, kind)
for _row, (_ya, _yb) in enumerate(((376, 546), (562, 740))):
    _x = 536
    while _x < 915:
        _w = _br.randint(24, 40)
        _h = _br.randint(104, 150) if _row == 0 else _br.randint(112, 156)
        BOOKS.append((_row, _x, min(_x + _w, 926), _yb - _h, _yb, _br.randint(0, 5)))
        _x += _w + _br.randint(2, 6)
SLOTCARDS = [(545 + 0, 790, 575, 930)] + [(722 + i * 40, 796 + (i % 2) * 8, 722 + i * 40 + 32, 930) for i in range(5)]

TITLE, TITLE_POS, TITLE_SZ = '知識庫', (74, 100), 66
NUM, NUM_POS, NUM_SZ = '61%', (68, 176), 184
LABEL, LABEL_POS, LABEL_SZ = '筆記已歸檔', (80, 456), 32
BAR = (80, 412, 470, 436)                               # progress capsule, 61% filled
check_glyphs(TITLE + LABEL)


def text_mask(s, pos, size, path=HEI, idx=0, stroke=0):
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).text(pos, s, font=F(path, size, idx), fill=255, stroke_width=stroke)
    return m


def sh_draw(d, sh, fill):
    k = sh[0]
    if k == 'rr':
        d.rounded_rectangle(sh[1], sh[2], fill=fill)
    elif k == 'rect':
        d.rectangle(sh[1], fill=fill)
    elif k == 'poly':
        d.polygon(sh[1], fill=fill)
    elif k == 'circ':
        cx, cy, r = sh[1]
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    elif k == 'line':
        pts, w = sh[1], sh[2]
        d.line(pts, fill=fill, width=w, joint='curve')
        for (x, y) in (pts[0], pts[-1]):
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=fill)


def mask_of(shapes):
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for sh in shapes:
        sh_draw(d, sh, 255)
    return m


def bbox_of(m, pad=0):
    b = m.getbbox()
    return (max(0, b[0] - pad), max(0, b[1] - pad), min(W, b[2] + pad), min(H, b[3] + pad))


# robot parts, back to front
LEGS = [('rr', (268, 900, 322, 1050), 12), ('rr', (358, 900, 412, 1050), 12), ('rr', (252, 1026, 330, 1052), 12), ('rr', (350, 1026, 428, 1052), 12)]
TORSO = [('rr', (242, 700, 438, 906), 40)]
PANEL = [('rr', (276, 742, 404, 824), 14)]
HEAD = [('rr', (226, 556, 454, 696), 30)]
VISOR = [('rr', (246, 596, 434, 658), 20)]
ANT = [('line', [(340, 558), (340, 506)], 10), ('circ', (340, 496, 16))]
ARM_R = [('line', [SHOULD_R, ELB_R, HAND_R], 30), ('circ', (SHOULD_R[0], SHOULD_R[1], 24)), ('circ', (HAND_R[0], HAND_R[1], 19))]
ARM_L = [('line', [SHOULD_L, ELB_L, HAND_L], 30), ('circ', (SHOULD_L[0], SHOULD_L[1], 24)), ('circ', (HAND_L[0], HAND_L[1], 18))]
# cabinet
CAB_FRAME = [('rr', (SH_L, SH_T, SH_R, SH_B), 14)]
HOLES = [('rect', (531, 376, 929, 546)), ('rect', (531, 562, 929, 740)), ('rect', (531, 756, 929, 1014))]
DRAWER_FRONT = [('rr', (503, FRONT_Y, 957, SH_B + 4), 12)]
CARD_SH = [('rect', CARD)]

ROBOT_SHAPES = LEGS + TORSO + HEAD + ANT + ARM_R + ARM_L

# =====================================================================
# Impressionism (Monet / Sisley / Morisot): broken colour, no black,
# coloured shadows, one fleeting light (low warm sun upper-left).
# =====================================================================
R = random.Random(11)
C = hexc
SKY = [C(h) for h in ('#9CB4E0', '#A9C8E6', '#BFD4EA', '#CDBEE0', '#EBC2CF', '#F5CDB0', '#F8E3A6', '#FCF1D2')]
FLOOR = [C(h) for h in ('#8FA5D4', '#A6B6DE', '#B9AEDB', '#D2B7D4', '#9CCBD6', '#E7C6CF', '#F1E0C6')]
SHADOW_V = [C(h) for h in ('#6C6DB0', '#7F76BA', '#9486C4')]


def jit(c, a=7):
    return tuple(max(0, min(255, v + R.randint(-a, a))) for v in c)


def mixc(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dab(d, x, y, ang, L, w, c):
    """One stroke of the brush: a short rounded bar, the unit of broken colour."""
    dx, dy = math.cos(ang) * L / 2, math.sin(ang) * L / 2
    d.line([(x - dx, y - dy), (x + dx, y + dy)], fill=c, width=max(1, int(w)))
    r = w / 2
    for sx, sy in ((x - dx, y - dy), (x + dx, y + dy)):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=c)


def ramp_pick(ramp, v, spread=.13, flick=None, pflick=.10):
    """Pick a colour from a dark->light ramp by lightness v (0..1). Neighbouring steps are mixed in
    side by side instead of blended, and a few complementary flecks keep the surface vibrating."""
    n = len(ramp)
    v = max(0.0, min(1.0, v + R.gauss(0, spread)))
    i = int(round(v * (n - 1)))
    if R.random() < .16:
        i = max(0, min(n - 1, i + R.choice((-1, 1))))
    c = ramp[i]
    if flick and R.random() < pflick:
        c = R.choice(flick)
    return jit(c)


def light_fn(b, k=.75):
    """Lit from upper-left: 1 at top-left of the object's box, 0 at bottom-right."""
    x0, y0, x1, y1 = b
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    return lambda x, y: max(0, min(1, 1.05 - k * ((x - x0) / w * .55 + (y - y0) / h * .45) * 1.35))


def broken(img, mask, step, L, w, angf, colf, pad=3, keep=1.0, wobble=.3):
    d = ImageDraw.Draw(img)
    b = bbox_of(mask, pad + 2)
    mk = mask.filter(ImageFilter.MaxFilter(2 * pad + 1)) if pad else mask
    px = mk.load()
    pts = []
    for gy in range(b[1], b[3], step):
        for gx in range(b[0], b[2], step):
            x = gx + R.uniform(-.5, .5) * step * 1.4
            y = gy + R.uniform(-.5, .5) * step * 1.4
            if 0 <= x < W and 0 <= y < H and px[int(x), int(y)] > 0 and R.random() < keep:
                pts.append((x, y))
    R.shuffle(pts)
    for x, y in pts:
        dab(d, x, y, angf(x, y) + R.gauss(0, wobble), L * R.uniform(.7, 1.3), w * R.uniform(.75, 1.25), colf(x, y))


def paint_obj(img, shapes, ramp, flick=None, under=0.5, L=13, w=7, step=4, angf=None, pad=2, k=.75, fine=True):
    m = mask_of(shapes)
    b = bbox_of(m)
    lf = light_fn(b, k)
    ang = angf or (lambda x, y: 0.0)
    img.paste(ramp[int(under * (len(ramp) - 1))], mask=m.filter(ImageFilter.GaussianBlur(.8)))  # ground tone
    col = lambda x, y: ramp_pick(ramp, lf(x, y), flick=flick)
    broken(img, m, step + 1, L * 1.3, w * 1.3, ang, col, pad=pad)
    if fine:
        broken(img, m, step + 2, L * .7, w * .7, ang, col, pad=pad, keep=.8)
    return m


def spark(img, mask, n, cols, L=9, w=4, ang=-.5):
    d = ImageDraw.Draw(img)
    b = bbox_of(mask)
    px = mask.load()
    k = 0
    while k < n:
        x, y = R.uniform(b[0], b[2]), R.uniform(b[1], b[3])
        if px[int(min(x, W - 1)), int(min(y, H - 1))] > 0:
            dab(d, x, y, ang + R.gauss(0, .3), L * R.uniform(.7, 1.3), w, R.choice(cols))
            k += 1


def main():
    img = Image.new('RGB', (W, H), C('#CBBFE0'))
    full = Image.new('L', (W, H), 255)

    # --- sky: light is the subject. A warm low sun-haze gathers at upper-left, cool lilac-blue recedes upward.
    sky_m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sky_m).rectangle([0, 0, W, GROUND], fill=255)
    gx, gy = 300, 540

    def sky_col(x, y):
        glow = math.exp(-(((x - gx) / 520) ** 2 + ((y - gy) / 430) ** 2))
        s = .06 + .62 * glow + .30 * (y / GROUND) ** 1.3
        return ramp_pick(SKY, s, spread=.10, flick=[C('#F7B6B0'), C('#B3D9E0'), C('#FBEFE0')], pflick=.04)
    sky_ang = lambda x, y: -.16 + .30 * math.sin(x / 170 + y / 95)
    broken(img, sky_m, 7, 30, 16, sky_ang, sky_col, pad=0, wobble=.22)
    broken(img, sky_m, 8, 17, 8, sky_ang, sky_col, pad=0, wobble=.3, keep=.9)
    # sun: a broken disc of warm whites, not a clean circle
    sun = mask_of([('circ', (120, 640, 74))])
    broken(img, sun, 6, 13, 7, lambda x, y: 0, lambda x, y: R.choice([C('#FFF6D6'), C('#FFE9A8'), C('#FFF9EA'), C('#FBD9A4')]), pad=6, keep=.9)

    # --- distant haze at the horizon (reflected light, almost no value change)
    haze = Image.new('L', (W, H), 0)
    ImageDraw.Draw(haze).rectangle([0, 975, W, GROUND], fill=255)
    broken(img, haze, 6, 34, 9, lambda x, y: 0, lambda x, y: R.choice([C('#D9C4E0'), C('#E9CBD6'), C('#C6D3E6'), C('#F1DCCB')]), pad=0, wobble=.08, keep=.8)

    # --- floor / water: calm horizontal strokes, small value range
    fl = Image.new('L', (W, H), 0)
    ImageDraw.Draw(fl).rectangle([0, GROUND, W, H], fill=255)
    floor_col = lambda x, y: ramp_pick(FLOOR, .55 + R.gauss(0, .17) - .15 * (x / W), spread=.0, flick=[C('#E9CFC8'), C('#A9D3D6')], pflick=.06)
    broken(img, fl, 9, 46, 9, lambda x, y: 0, floor_col, pad=0, wobble=.04)

    # --- cast shadows: cool violet-blue, never grey or black
    shadows = [('poly', [(246, 1040), (440, 1036), (640, 1088), (470, 1096)]),
               ('poly', [(505, 1030), (950, 1030), (1038, 1082), (560, 1090)])]
    sm = mask_of(shadows)
    broken(img, sm, 7, 40, 8, lambda x, y: .03, lambda x, y: R.choice(SHADOW_V + [C('#8A9AD0')]), pad=1, wobble=.05)

    # --- knowledge base
    cab = [C('#6C5AA0'), C('#8A5E9E'), C('#B3706F'), C('#D8896A'), C('#EBA67E'), C('#F4C79A')]
    paint_obj(img, CAB_FRAME, cab, flick=[C('#76B6BE'), C('#F2D27C')], L=14, w=8, angf=lambda x, y: 0, k=.9)
    hole = [C('#3F3F86'), C('#4E4A92'), C('#5E55A0'), C('#6D63AC')]
    for h in HOLES:
        paint_obj(img, [h], hole, flick=[C('#8E7FBE')], L=12, w=7, angf=lambda x, y: 1.2, k=.5, fine=False)
    bookcols = [
        [C('#C8506E'), C('#E27A8C'), C('#F4A9B2')],
        [C('#D79A22'), C('#F0C750'), C('#FBE79A')],
        [C('#2F8F95'), C('#5DBDB5'), C('#A7E1D6')],
        [C('#D65F2E'), C('#F08E56'), C('#F9BE90')],
        [C('#4A5AA8'), C('#7C8ED0'), C('#B7C6EC')],
        [C('#7A55A6'), C('#A585CC'), C('#D0B8E6')]]
    for (row, x0, x1, y0, y1, kind) in BOOKS:
        paint_obj(img, [('rect', (x0, y0, x1, y1))], bookcols[kind], L=10, w=5, step=3, angf=lambda x, y: 1.5, pad=1, fine=False)
    for (x0, y0, x1, y1) in SLOTCARDS:
        paint_obj(img, [('rect', (x0, y0, x1, y1))], [C('#C9BDD9'), C('#E2D6E2'), C('#F5EAE0')], L=9, w=5, step=3, angf=lambda x, y: 1.5, pad=1, fine=False)
    # the new card, then the drawer front covers its lower half (occlusion = "inside")
    paint_obj(img, CARD_SH, [C('#C9B3D8'), C('#E8D6DD'), C('#FBF1E6'), C('#FFFAF0')], L=10, w=5, step=3, angf=lambda x, y: 1.5, pad=1)
    cd = ImageDraw.Draw(img)
    for i, yy in enumerate((850, 872, 894)):
        cd.line([(603, yy), (603 + (86 if i < 2 else 56), yy)], fill=C('#8F9CCB'), width=4)
    hdr = mask_of([('rect', (CARD[0], CARD[1], CARD[2], 826))])
    broken(img, hdr, 4, 10, 5, lambda x, y: 0, lambda x, y: R.choice([C('#E0604A'), C('#EE7E5E'), C('#D24F55')]), pad=0)
    paint_obj(img, DRAWER_FRONT, cab, flick=[C('#76B6BE'), C('#F2D27C')], L=14, w=8, angf=lambda x, y: 0, k=.8)
    for x in (680, 770):  # drawer handle plate
        pass
    paint_obj(img, [('rr', (690, 960, 770, 984), 10)], [C('#C99A2E'), C('#EBC453'), C('#FBE79A')], L=8, w=4, step=3, angf=lambda x, y: 0)

    # --- robot: cool steel-turquoise body, violet shadows, warm cream light from the sun side
    body = [C('#5D63A8'), C('#7C86C0'), C('#8FB6CC'), C('#7CC0C0'), C('#B9DCD4'), C('#F4E4C4'), C('#FFF6DE')]
    flk = [C('#E9A88C'), C('#F6D88A'), C('#8E7CC2')]
    vang = lambda x, y: 1.45
    paint_obj(img, LEGS, body, flick=flk, L=12, w=7, angf=vang, k=.7)
    paint_obj(img, TORSO, body, flick=flk, L=14, w=8, angf=lambda x, y: .15 + .002 * (y - 700) / 10, k=.85)
    paint_obj(img, PANEL, [C('#6E73B4'), C('#9DA5D4'), C('#D9DDEE'), C('#FFF3DC')], L=9, w=5, step=3, angf=lambda x, y: 0)
    pd = ImageDraw.Draw(img)
    for (cx, col) in ((298, '#F2C84B'), (322, '#58BDB0')):
        dab(pd, cx, 768, .4, 8, 12, C(col))
    pd.line([(296, 796), (380, 796)], fill=C('#7C86C0'), width=5)
    pd.line([(296, 810), (352, 810)], fill=C('#7C86C0'), width=5)
    paint_obj(img, ARM_L, body, flick=flk, L=11, w=6, step=3, angf=vang, k=.8)
    paint_obj(img, HEAD, body, flick=flk, L=13, w=7, angf=lambda x, y: .1, k=.9)
    paint_obj(img, VISOR, [C('#3F4686'), C('#4D58A0'), C('#6A78C0'), C('#8FA8DA')], flick=[C('#9ADAD6')], L=9, w=5, step=3, angf=lambda x, y: .1, k=.6)
    dab(pd, 310, 626, 0, 70, 12, C('#F8E58E'))                    # sensor light, not an eye
    dab(pd, 306, 623, 0, 52, 5, C('#FFF8D8'))
    paint_obj(img, ANT, [C('#5D63A8'), C('#7C86C0'), C('#E9A88C'), C('#F6D88A')], L=8, w=5, step=3, angf=vang)
    paint_obj(img, ARM_R, body, flick=flk, L=11, w=6, step=3, angf=lambda x, y: .55, k=.8)

    # --- reflections: robot colours echoed faintly in the floor (Monet water), fading before the calm zone
    for (x0, x1, cols) in ((254, 428, [C('#8FA2CE'), C('#9CB6D6'), C('#B7AADC')]), (515, 945, [C('#B6A0CC'), C('#C7A0B8'), C('#9AA0D0')])):
        rm = Image.new('L', (W, H), 0)
        ImageDraw.Draw(rm).rectangle([x0, GROUND + 18, x1, 1112], fill=255)
        broken(img, rm, 11, 30, 5, lambda x, y: 0, lambda x, y: R.choice(cols), pad=0, wobble=.05, keep=.55)

    # --- type: solid colour (legible) plus dabs that break its edge; deep blue-violet, never black
    def typeset(m, base, cols, L, w):
        """Solid base colour keeps the type legible; strokes are clipped inside the glyphs."""
        img.paste(base, mask=m)
        tmp = img.copy()
        broken(tmp, m, 4, L, w, lambda x, y: 1.4, lambda x, y: R.choice(cols), pad=0, keep=.9, wobble=.35)
        img.paste(tmp, mask=m)
    typeset(text_mask(TITLE, TITLE_POS, TITLE_SZ), C('#33408E'), [C('#2E3A86'), C('#4552A4'), C('#5A64B4')], 7, 3)
    typeset(text_mask(NUM, NUM_POS, NUM_SZ, AVE, 8), C('#D8452B'), [C('#E65A32'), C('#C93A3A'), C('#F07A3C'), C('#B8345E')], 12, 5)
    lm = text_mask(LABEL, LABEL_POS, LABEL_SZ)
    img.paste(C('#4A56A0'), mask=lm)
    # progress capsule
    bd = ImageDraw.Draw(img)
    bd.rounded_rectangle(BAR, 12, fill=C('#C9C0E2'))
    bd.rounded_rectangle((BAR[0], BAR[1], BAR[0] + int(390 * .61), BAR[3]), 12, fill=C('#D8452B'))

    # --- canvas weave (barely there)
    weave = Image.new('L', (W, H), 128)
    wd = ImageDraw.Draw(weave)
    for x in range(0, W, 3):
        wd.line([(x, 0), (x, H)], fill=121)
    for y in range(0, H, 3):
        wd.line([(0, y), (W, y)], fill=135)
    img = ImageChops.overlay(img, Image.merge('RGB', (weave,) * 3).point(lambda v: 128 + (v - 128) * 3 // 2))
    img.save(os.path.join(HERE, 'sample.png'))
    lo = min(sum(p) / 3 for p in img.resize((270, 337)).getdata())
    print('darkest mean-channel value (no black expected):', round(lo))


if __name__ == '__main__':
    main()
