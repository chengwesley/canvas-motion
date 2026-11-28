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
# Post-Impressionism (Van Gogh + Gauguin)
#  Van Gogh : directional impasto strokes that follow form, complementary pairs
#             (cobalt/orange, yellow/violet), dark contour, swirling flow in the sky.
#  Gauguin  : the floor is one flat, unmodelled area of colour closed by a dark line (cloisonne).
# =====================================================================
R = random.Random(21)
C = hexc
NAVY = C('#0E1A44')
BLUE = [C(h) for h in ('#16255E', '#1F3C94', '#2B58B8', '#3F7AD0', '#6AA6E0', '#A9D2F0')]
YEL = [C(h) for h in ('#C98A12', '#E8A91C', '#F6C72E', '#FBDF5E', '#FFF0A0')]
ORA = [C(h) for h in ('#8E2A1A', '#C4401F', '#E4651F', '#F58A2A', '#FBB04A')]


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def lift(c, t):
    return tuple(int(v + (255 - v) * t) for v in c)


def jit(c, a=9):
    return tuple(max(0, min(255, v + R.randint(-a, a))) for v in c)


def pick(ramp, v, spread=.12, flick=None, pf=.1):
    n = len(ramp)
    v = max(0.0, min(1.0, v + R.gauss(0, spread)))
    c = ramp[int(round(v * (n - 1)))]
    if flick and R.random() < pf:
        c = R.choice(flick)
    return jit(c)


def crop_filter(mask, flt, pad):
    b = bbox_of(mask, pad + 2)
    sub = mask.crop(b).filter(flt)
    out = Image.new('L', (W, H), 0)
    out.paste(sub, b[:2])
    return out


def contour(img, mask, col=NAVY, px=4):
    """Cloisonne line: a dark band just outside the shape, closing every colour area."""
    grow = crop_filter(mask, ImageFilter.MaxFilter(2 * px + 1), px)
    img.paste(col, mask=ImageChops.subtract(grow, mask))


def follow_rect(b):
    """Flow that runs parallel to the nearest edge of a box: strokes wrap the form like concentric frames."""
    x0, y0, x1, y1 = b

    def f(x, y):
        dl, dr, dt, db = x - x0, x1 - x, y - y0, y1 - y
        m = min(dl, dr, dt, db)
        return math.pi / 2 if m in (dl, dr) else 0.0
    return f


def follow_limb(pts):
    """Flow along the nearest segment of a polyline (arms, legs)."""
    segs = list(zip(pts[:-1], pts[1:]))

    def f(x, y):
        best, ang = 1e9, 0.0
        for (a, b) in segs:
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy + 1e-9)))
            d = math.hypot(x - a[0] - t * dx, y - a[1] - t * dy)
            if d < best:
                best, ang = d, math.atan2(dy, dx)
        return ang
    return f


def swirl(cx, cy, wob=.5, freq=46):
    """Sky flow: strokes circle the action and ripple outward, as in Van Gogh's night skies."""
    def f(x, y):
        r = math.hypot(x - cx, y - cy)
        return math.atan2(y - cy, x - cx) + math.pi / 2 + wob * math.sin(r / freq)
    return f


def impasto(img, mask, flow, colf, L=28, w=10, spacing=6, pad=3, keep=1.0, clip=True, relief=True):
    """Thick directional strokes. Each stroke = shadow edge, body, highlight ridge, so paint stands up
    (light from upper-left). Strokes integrate the flow field, so they bend with the form."""
    tmp = img.copy() if clip else img
    d = ImageDraw.Draw(tmp)
    b = bbox_of(mask, pad + 2)
    mk = crop_filter(mask, ImageFilter.MaxFilter(2 * pad + 1), pad) if pad else mask
    px = mk.load()
    pts = []
    for gy in range(b[1], b[3], spacing):
        for gx in range(b[0], b[2], spacing):
            x = gx + R.uniform(-.5, .5) * spacing * 1.3
            y = gy + R.uniform(-.5, .5) * spacing * 1.3
            if 0 <= x < W and 0 <= y < H and px[int(x), int(y)] > 0 and R.random() < keep:
                pts.append((x, y))
    R.shuffle(pts)
    for (x, y) in pts:
        ll = L * R.uniform(.7, 1.25)
        ww = w * R.uniform(.8, 1.2)
        n = max(2, int(ll / 6))
        path = [(x, y)]
        cx, cy = x, y
        for _ in range(n):
            a = flow(cx, cy)
            cx += math.cos(a) * ll / n
            cy += math.sin(a) * ll / n
            path.append((cx, cy))
        c = colf(x, y)
        if relief:
            d.line([(px_ + 1.8, py_ + 1.8) for px_, py_ in path], fill=shade(c, .66), width=int(ww + 1), joint='curve')
        d.line(path, fill=c, width=int(ww), joint='curve')
        for (ex, ey) in (path[0], path[-1]):
            d.ellipse([ex - ww / 2, ey - ww / 2, ex + ww / 2, ey + ww / 2], fill=c)
        if relief and ww > 5:
            o = ww * .22
            d.line([(px_ - o, py_ - o) for px_, py_ in path], fill=lift(c, .35), width=max(2, int(ww * .26)), joint='curve')
    if clip:
        img.paste(tmp, mask=mask)


def solid(img, mask, col):
    img.paste(col, mask=mask)


def part(img, shapes, ramp, flow=None, flick=None, k=.8, L=22, w=9, spacing=5, line=NAVY, px=4, base=None):
    m = mask_of(shapes)
    b = bbox_of(m)
    flow = flow or follow_rect(b)
    lf = light_fn(b, k)
    solid(img, m, base or ramp[len(ramp) // 2])
    impasto(img, m, flow, lambda x, y: pick(ramp, lf(x, y), flick=flick), L=L, w=w, spacing=spacing)
    contour(img, m, line, px)
    return m


def light_fn(b, k=.8):
    x0, y0, x1, y1 = b
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    return lambda x, y: max(0, min(1, 1.1 - k * ((x - x0) / w * .55 + (y - y0) / h * .45) * 1.4))


def main():
    img = Image.new('RGB', (W, H), BLUE[1])

    # --- sky: concentric swirl around the action; yellow core -> pale halo -> cobalt -> ultramarine night
    sky = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sky).rectangle([0, 0, W, GROUND], fill=255)
    cx, cy = 580, 690

    def sky_col(x, y):
        r = math.hypot(x - cx, y - cy) + 26 * math.sin(3 * math.atan2(y - cy, x - cx) + 2)
        if r < 330:
            return pick(YEL, .55 + R.gauss(0, .2), spread=.1, flick=[ORA[3], ORA[4]], pf=.12)
        if r < 430:
            return pick(YEL + ORA[3:], R.random(), spread=.0)
        if r < 500:
            return pick(BLUE[3:], .6 + .4 * R.random(), spread=.1, flick=[YEL[3], YEL[4]], pf=.12)
        if r < 700:
            return pick(BLUE[1:5], .25 + .6 * R.random(), spread=.1, flick=[YEL[2]], pf=.03)
        return pick(BLUE[:4], .15 + .6 * R.random(), spread=.1, flick=[BLUE[5], YEL[3]], pf=.04)
    flow = swirl(cx, cy)
    impasto(img, sky, flow, sky_col, L=40, w=14, spacing=8, pad=0, clip=False)
    impasto(img, sky, flow, sky_col, L=26, w=9, spacing=12, pad=0, clip=False, keep=.7)

    # --- floor: Gauguin flat plane (violet, complement of the yellow light) closed by a dark line, no modelling
    fl = Image.new('L', (W, H), 0)
    ImageDraw.Draw(fl).rectangle([0, GROUND, W, H], fill=255)
    solid(img, fl, C('#5E4B9C'))
    band = mask_of([('poly', [(0, 1196), (180, 1176), (520, 1166), (860, 1150), (1080, 1120), (1080, H), (0, H)])])
    solid(img, band, C('#6A56A8'))        # one flat decorative shape, closed by a thin dark line
    contour(img, band, NAVY, 3)
    img.paste(C('#6A56A8'), mask=band)
    ImageDraw.Draw(img).rectangle([0, GROUND - 4, W, GROUND + 3], fill=NAVY)
    sh = mask_of([('poly', [(250, 1046), (440, 1046), (600, 1100), (440, 1104)]), ('poly', [(505, 1046), (960, 1046), (1040, 1100), (560, 1104)])])
    solid(img, sh, C('#3F327A'))
    contour(img, sh, NAVY, 3)

    # --- cabinet: vermilion/orange frame (complement of the blue interior), strokes wrap around the frame
    cab = [ORA[0], ORA[1], ORA[2], ORA[3], ORA[4], YEL[2]]
    fm = mask_of(CAB_FRAME)
    solid(img, fm, ORA[2])
    impasto(img, fm, follow_rect((SH_L, SH_T, SH_R, SH_B)), lambda x, y: pick(cab, light_fn((SH_L, SH_T, SH_R, SH_B), .9)(x, y), flick=[BLUE[2]], pf=.05), L=26, w=10, spacing=5)
    contour(img, fm, NAVY, 5)
    for h in HOLES:
        hm = mask_of([h])
        hb = bbox_of(hm)
        solid(img, hm, BLUE[0])
        impasto(img, hm, lambda x, y: 0.0, lambda x, y: pick([BLUE[0], C('#101C4E'), BLUE[1]], R.random(), spread=.05), L=26, w=8, spacing=7, pad=0)
        contour(img, hm, NAVY, 3)
    bk = [[C('#B8301F'), C('#E04A2E'), C('#F58A5E')], [YEL[0], YEL[2], YEL[4]], [C('#1F7A52'), C('#3E9E6A'), C('#8FD3A0')],
          [BLUE[2], BLUE[3], BLUE[5]], [C('#5B3A96'), C('#8466C0'), C('#B9A2E4')], [ORA[1], ORA[3], ORA[4]]]
    for (row, x0, x1, y0, y1, kind) in BOOKS:
        part(img, [('rect', (x0, y0, x1, y1))], bk[kind], flow=lambda x, y: math.pi / 2, k=1.0, L=22, w=7, spacing=4, px=2)
    for (x0, y0, x1, y1) in SLOTCARDS:
        part(img, [('rect', (x0, y0, x1, y1))], [C('#C9B067'), C('#E8D48A'), YEL[4]], flow=lambda x, y: math.pi / 2, L=18, w=6, spacing=4, px=2)
    # new card; the drawer front hides its lower part
    cm = part(img, CARD_SH, [C('#D9C47A'), YEL[3], YEL[4], C('#FFF8D0')], flow=lambda x, y: math.pi / 2, L=20, w=7, spacing=4, px=3)
    hd = mask_of([('rect', (CARD[0], CARD[1], CARD[2], 826))])
    impasto(img, hd, lambda x, y: 0.0, lambda x, y: pick(ORA[1:4], R.random(), spread=.05), L=20, w=8, spacing=5, pad=0)
    contour(img, hd, NAVY, 2)
    cd = ImageDraw.Draw(img)
    for i, yy in enumerate((850, 872, 894)):
        cd.line([(603, yy), (603 + (86 if i < 2 else 56), yy)], fill=BLUE[2], width=6)
    part(img, DRAWER_FRONT, cab, flow=follow_rect((503, FRONT_Y, 957, SH_B + 4)), k=.85, flick=[BLUE[2]], L=26, w=10, spacing=5, px=5)
    part(img, [('rr', (690, 960, 770, 984), 10)], YEL, flow=lambda x, y: 0.0, L=16, w=6, spacing=4, px=3)

    # --- robot: cobalt body (orange flecks), ultramarine shadows, pale-yellow ridges, dark contour
    body = [BLUE[0], BLUE[1], BLUE[2], BLUE[3], BLUE[4], YEL[4]]
    fo = [ORA[3], ORA[4], YEL[2]]
    vleg = follow_limb([(0, 0), (0, 100)])
    part(img, LEGS, body, flow=lambda x, y: math.pi / 2, flick=fo, k=.7, L=22, w=8, spacing=4, px=4)
    part(img, TORSO, body, flick=fo[:2], k=.85, L=24, w=9, spacing=5, px=5)
    part(img, PANEL, [ORA[1], ORA[2], ORA[3], ORA[4], YEL[3]], k=.8, L=16, w=6, spacing=4, px=3)
    pd = ImageDraw.Draw(img)
    for (yy, col, ln) in ((769, BLUE[1], 70), (792, BLUE[3], 52), (815, BLUE[1], 34)):   # a list, not a face
        pd.ellipse([290, yy - 6, 302, yy + 6], fill=col)
        pd.line([(314, yy), (314 + ln, yy)], fill=NAVY, width=5)
    part(img, ARM_L, body, flow=follow_limb([SHOULD_L, ELB_L, HAND_L]), flick=fo, k=.8, L=20, w=8, spacing=4, px=4)
    part(img, HEAD, body, flick=fo, k=.9, L=24, w=9, spacing=5, px=5)
    vm = part(img, VISOR, [NAVY, BLUE[0], BLUE[1], BLUE[2]], flow=lambda x, y: 0.0, k=.6, L=18, w=7, spacing=4, px=3, line=C('#0A1236'))
    impasto(img, mask_of([('rr', (268, 616, 372, 636), 10)]), lambda x, y: 0.0, lambda x, y: pick(ORA[2:] + YEL[2:], R.random(), spread=0), L=18, w=7, spacing=3, pad=0)  # sensor light (orange vs blue)
    part(img, ANT, [ORA[1], ORA[2], ORA[3], YEL[3]], flow=follow_limb([(340, 558), (340, 500)]), k=.8, L=14, w=6, spacing=3, px=3)
    part(img, ARM_R, body, flow=follow_limb([SHOULD_R, ELB_R, HAND_R]), flick=fo, k=.8, L=20, w=8, spacing=4, px=4)

    # --- type: dark outline first (cloisonne), colour strokes inside the glyphs
    def typeset(txt, pos, size, ramp, path=HEI, idx=0, outline=5, ang=math.pi / 2, L=20, w=8):
        om = text_mask(txt, pos, size, path, idx, stroke=outline)
        solid(img, om, NAVY)
        m = text_mask(txt, pos, size, path, idx)
        solid(img, m, ramp[len(ramp) // 2])
        impasto(img, m, lambda x, y: ang, lambda x, y: pick(ramp, R.random(), spread=.02), L=L, w=w, spacing=4, pad=0)
    typeset(TITLE, TITLE_POS, TITLE_SZ, [YEL[2], YEL[3], YEL[4]], outline=4, L=14, w=5)
    typeset(NUM, NUM_POS, NUM_SZ, [ORA[3], ORA[4], YEL[2], YEL[3]], AVE, 8, outline=6, L=26, w=11)
    typeset(LABEL, LABEL_POS, LABEL_SZ, [YEL[3], YEL[4]], outline=3, L=10, w=4)
    bm = mask_of([('rr', BAR, 12)])
    solid(img, bm, BLUE[0])
    fm2 = mask_of([('rr', (BAR[0], BAR[1], BAR[0] + int(390 * .61), BAR[3]), 12)])
    solid(img, fm2, ORA[3])
    impasto(img, fm2, lambda x, y: 0.0, lambda x, y: pick(ORA[2:] + YEL[2:3], R.random(), spread=0), L=16, w=7, spacing=4, pad=0)
    contour(img, bm, NAVY, 3)

    img.save(os.path.join(HERE, 'sample.png'))


if __name__ == '__main__':
    main()
