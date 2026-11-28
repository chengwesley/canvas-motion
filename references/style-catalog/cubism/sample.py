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
# Cubism (principles of Picasso / Braque / Gris, analytic -> synthetic)
#  - every object is cut into flat planes (facets) with arbitrary light, tones from a restrained ramp
#  - several viewpoints at once (head front + profile, cabinet front + top + side, card + ghost copy)
#  - some edges are lost (passage), long lines run on through objects
#  - synthetic collage: newsprint, faux wood-grain, wallpaper, stencil lettering
# =====================================================================
S = 2                                   # draw at 2x, downsample for crisp edges
R = random.Random(31)
C = hexc
INK = C('#1E1A17')
OCH = [C(h) for h in ('#6E4A2A', '#9A6A36', '#C69A52', '#E2C282', '#F2E3B8')]
GRY = [C(h) for h in ('#2F3A44', '#4E5B66', '#7A8892', '#A9B3B8', '#D5D8D2')]
OLV = [C(h) for h in ('#4A4A28', '#6E6D3A', '#8F8D54', '#B5B27A', '#D9D5A5')]
BRK = [C(h) for h in ('#6B2B22', '#9B4330', '#B5503A', '#D17A5A', '#EDB08F')]
CREAM, NEWS, WOOD = C('#F3EAD0'), C('#E4DABD'), C('#A8794A')
ANG = [-1.05, -.45, .26, .87, 1.48]     # the few angles of the cuts: keeps the planes crystalline


def sc(p):
    return [(x * S, y * S) for x, y in p]


def area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2


def centroid(p):
    return (sum(x for x, _ in p) / len(p), sum(y for _, y in p) / len(p))


def clip(p, a, b, c):
    """Keep the part of polygon p where a*x + b*y + c >= 0 (Sutherland-Hodgman)."""
    out = []
    for i in range(len(p)):
        P, Q = p[i], p[(i + 1) % len(p)]
        fp, fq = a * P[0] + b * P[1] + c, a * Q[0] + b * Q[1] + c
        if fp >= 0:
            out.append(P)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((P[0] + t * (Q[0] - P[0]), P[1] + t * (Q[1] - P[1])))
    return out


def facets(poly, n, minA=700, angs=ANG):
    """Cut a polygon into n flat planes along a restricted set of angles."""
    polys = [poly]
    for _ in range(n):
        for _try in range(8):
            polys.sort(key=area, reverse=True)
            tgt = polys[0] if R.random() < .6 else R.choice(polys[:3])
            cx, cy = centroid(tgt)
            ex = max(x for x, _ in tgt) - min(x for x, _ in tgt)
            ey = max(y for _, y in tgt) - min(y for _, y in tgt)
            px, py = cx + R.gauss(0, ex * .16), cy + R.gauss(0, ey * .16)
            a = R.choice(angs) + R.uniform(-.08, .08)
            nx, ny = -math.sin(a), math.cos(a)
            c = -(nx * px + ny * py)
            p1, p2 = clip(tgt, nx, ny, c), clip(tgt, -nx, -ny, -c)
            if len(p1) >= 3 and len(p2) >= 3 and area(p1) > minA and area(p2) > minA:
                polys.remove(tgt)
                polys += [p1, p2]
                break
    return polys


def hatch(img, poly, ang, gap, col, w=2):
    """Parallel hatching clipped to one plane (modulated passage)."""
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    b = (int(min(xs)) - 2, int(min(ys)) - 2, int(max(xs)) + 3, int(max(ys)) + 3)
    bw, bh = b[2] - b[0], b[3] - b[1]
    m = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(m).polygon([(x - b[0], y - b[1]) for x, y in poly], fill=255)
    l = Image.new('L', (bw, bh), 0)
    ld = ImageDraw.Draw(l)
    dx, dy = math.cos(ang), math.sin(ang)
    reach = bw + bh
    k = -reach
    while k < reach:
        ox, oy = bw / 2 - dy * k, bh / 2 + dx * k
        ld.line([(ox - dx * reach, oy - dy * reach), (ox + dx * reach, oy + dy * reach)], fill=255, width=w)
        k += gap
    img.paste(col, b[:2], ImageChops.multiply(m, l))


def stipple(img, poly, col, n):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    m = Image.new('L', img.size, 0)
    d = ImageDraw.Draw(m)
    for _ in range(n):
        x, y = R.uniform(min(xs), max(xs)), R.uniform(min(ys), max(ys))
        d.ellipse([x, y, x + 3, y + 3], fill=255)
    pm = Image.new('L', img.size, 0)
    ImageDraw.Draw(pm).polygon(poly, fill=255)
    img.paste(col, mask=ImageChops.multiply(m, pm))


def edges(d, poly, w, p_keep=.8, col=INK):
    """Contour with lost edges: a segment is dropped now and then so the plane melts into its neighbour."""
    for i in range(len(poly)):
        if R.random() < p_keep:
            d.line([poly[i], poly[(i + 1) % len(poly)]], fill=col, width=w)


def plane_stack(img, poly, ramps, n, w=3, hatch_p=.3, stip_p=.15, lost=.8, base=2, spread=2, outline=True, minA=3000):
    """Fill one object as a stack of flat planes. ramps: list of colour ramps the planes draw from."""
    d = ImageDraw.Draw(img)
    last = None
    fs = facets(poly, n, minA=minA)
    for f in fs:
        ramp = R.choice(ramps)
        i = max(0, min(len(ramp) - 1, base + R.randint(-spread, spread)))
        while i == last and spread:
            i = max(0, min(len(ramp) - 1, base + R.randint(-spread, spread)))
        last = i
        d.polygon(f, fill=ramp[i])
        if i <= 1 and R.random() < hatch_p + .3:
            hatch(img, f, R.choice(ANG), 9 * S // 2 + R.randint(0, 3), shade_c(ramp[i], .6), 2)
        elif R.random() < hatch_p:
            hatch(img, f, R.choice(ANG), 11 * S // 2, shade_c(ramp[i], .78), 2)
        elif R.random() < stip_p:
            stipple(img, f, shade_c(ramp[i], .85), int(area(f) / 90))
    for f in fs:
        edges(d, f, max(2, w - 1), p_keep=lost - .15, col=shade_c(INK, 1.0))
    if outline:
        edges(d, poly, w + 1, p_keep=.92)
    return fs


def shade_c(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def chamfer(b, c):
    x0, y0, x1, y1 = b
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def to_polys(sh):
    k = sh[0]
    if k == 'rr':
        return [chamfer(sh[1], sh[2] * .55)]
    if k == 'rect':
        x0, y0, x1, y1 = sh[1]
        return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
    if k == 'circ':
        cx, cy, r = sh[1]
        return [[(cx + r * math.cos(a * math.pi / 4 + .39), cy + r * math.sin(a * math.pi / 4 + .39)) for a in range(8)]]
    if k == 'line':
        pts, w = sh[1], sh[2]
        out = []
        for a, b in zip(pts[:-1], pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            nx, ny = -dy / L * w / 2, dx / L * w / 2
            out.append([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)])
        return out
    return []


def wood(img, poly, base=WOOD, grain=(C('#5E3F22'), C('#7D5430')), split=None):
    """Faux-bois paper (Braque's papier colle): clipped wavy grain lines."""
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    b = (int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1)
    bw, bh = b[2] - b[0], b[3] - b[1]
    m = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(m).polygon([(x - b[0], y - b[1]) for x, y in poly], fill=255)
    t = Image.new('RGB', (bw, bh), base)
    td = ImageDraw.Draw(t)
    ph = R.uniform(0, 6)
    for y in range(-20, bh + 20, 9):
        pts = [(x, y + 7 * math.sin(x / 70 + y / 31 + ph) + 3 * math.sin(x / 19 + y)) for x in range(0, bw + 12, 12)]
        td.line(pts, fill=R.choice(grain), width=R.choice((2, 3, 4)))
    img.paste(t, b[:2], m)


def collage_text(img, poly, base, lines, size, col, rot_pad=0):
    """Newsprint: paper polygon filled with rows of real small type (clipped), plus a few torn-looking strips."""
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    b = (int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1)
    bw, bh = b[2] - b[0], b[3] - b[1]
    m = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(m).polygon([(x - b[0], y - b[1]) for x, y in poly], fill=255)
    t = Image.new('RGB', (bw, bh), base)
    td = ImageDraw.Draw(t)
    f = F(HEI, size * S)
    y = 4
    for i in range(400):
        if y > bh:
            break
        td.text((6 + R.randint(0, 20), y), lines[i % len(lines)], font=f, fill=col)
        y += int(size * S * 1.35)
    img.paste(t, b[:2], m)


def text2(img, s, pos, size, fill, path=HEI, idx=0, stroke=0):
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).text((pos[0] * S, pos[1] * S), s, font=F(path, size * S, idx), fill=255, stroke_width=stroke)
    img.paste(fill, mask=m)


def main():
    img = Image.new('RGB', (W * S, H * S), CREAM)
    d = ImageDraw.Draw(img)
    NEWS_LINES = ['知識庫 筆記 歸檔 索引 資料', '卡片 分類 查詢 整理 紀錄', '歸檔 知識 筆記 資料庫 索引']
    for ln in NEWS_LINES:
        check_glyphs(ln.replace(' ', ''))

    # ---- background: shattered planes, light and quiet so the objects carry the contrast
    bg = [(0, 0), (W, 0), (W, GROUND), (0, GROUND)]
    for f in facets(sc(bg), 22, minA=9000 * S * S // 4):
        ramp = R.choice((OCH, GRY, OLV))
        i = R.choice((3, 3, 4, 4, 2))
        d.polygon(f, fill=ramp[i])
        if R.random() < .35:
            hatch(img, f, R.choice(ANG), 14 * S, shade_c(ramp[i], .86), 2)
    # wallpaper strip (collage 1): diagonal stripes + dots
    wp = sc([(0, 560), (230, 520), (250, 760), (0, 800)])
    wm = Image.new('L', img.size, 0)
    ImageDraw.Draw(wm).polygon(wp, fill=255)
    wl = Image.new('RGB', img.size, C('#D9CBA3'))
    wd = ImageDraw.Draw(wl)
    for x in range(-400, 300 * S, 22 * S):
        wd.line([(x, 480 * S), (x + 300 * S, 860 * S)], fill=C('#B79C66'), width=5 * S // 2)
    for x in range(0, 260 * S, 26 * S):
        for y in range(500 * S, 820 * S, 26 * S):
            wd.ellipse([x, y, x + 5 * S, y + 5 * S], fill=C('#8C7248'))
    img.paste(wl, mask=wm)
    edges(d, wp, 3)

    # ---- floor: two or three flat planes, almost one tone (calm, no hatching)
    d.polygon(sc([(0, GROUND), (W, GROUND), (W, H), (0, H)]), fill=C('#CFC3A1'))
    d.polygon(sc([(0, 1130), (W, 1090), (W, H), (0, H)]), fill=C('#C6BA98'))
    d.polygon(sc([(0, 1250), (610, 1196), (W, 1226), (W, H), (0, H)]), fill=C('#BDB090'))
    d.line(sc([(0, GROUND), (W, GROUND)]), fill=INK, width=4 * S // 2)

    # ---- knowledge base: front plane + top seen from above + side seen from the right (3 viewpoints)
    top = sc([(SH_L, SH_T), (SH_R, SH_T), (SH_R + 38, SH_T - 34), (SH_L + 44, SH_T - 34)])
    side = sc([(SH_R, SH_T + 4), (SH_R + 44, SH_T - 30), (SH_R + 44, SH_B - 36), (SH_R, SH_B)])
    plane_stack(img, top, [OCH], 3, base=1, spread=1, hatch_p=.5)
    plane_stack(img, side, [OCH, GRY], 4, base=0, spread=1, hatch_p=.7)
    plane_stack(img, sc(chamfer((SH_L, SH_T, SH_R, SH_B), 10)), [OCH], 5, base=1, spread=1, hatch_p=.3, w=4)
    for h in HOLES:
        hp = sc(to_polys(h)[0])
        d.polygon(hp, fill=C('#2A211B'))
        hatch(img, hp, 1.2, 12 * S, C('#463A2E'), 2)
        edges(d, hp, 3, 1.0)
    cols = [(BRK, 2), (OLV, 2), (GRY, 1), (OCH, 3), (GRY, 3), (BRK, 3)]
    for (row, x0, x1, y0, y1, kind) in BOOKS:
        ramp, bi = cols[kind]
        sp = sc([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        d.polygon(sp, fill=ramp[bi])
        mid = x0 + (x1 - x0) * .62                         # spine plane + page-edge plane = two views of one book
        d.polygon(sc([(mid, y0), (x1, y0), (x1, y1), (mid, y1)]), fill=ramp[max(0, bi - 2)])
        if R.random() < .4:
            d.polygon(sc([(x0, y0), (x1, y0), (x1 + 8, y0 - 9), (x0 + 8, y0 - 9)]), fill=ramp[min(4, bi + 1)])  # top seen from above
        hatch(img, sp, 1.55, 8 * S, shade_c(ramp[bi], .72), 2) if R.random() < .4 else None
        edges(d, sp, 3, .95)
    for (x0, y0, x1, y1) in SLOTCARDS:
        sp = sc([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        d.polygon(sp, fill=C('#E7DCB9'))
        d.polygon(sc([(x0 + 20, y0), (x1, y0), (x1, y1), (x0 + 20, y1)]), fill=C('#C9BC94'))
        edges(d, sp, 3, .95)
    # the new note card: front view, its ghost copy shifted (second view), and the drawer front hides the lower part
    ghost = sc([(CARD[0] - 14, CARD[1] + 10), (CARD[2] - 14, CARD[1] + 10), (CARD[2] - 14, CARD[3] + 10), (CARD[0] - 14, CARD[3] + 10)])
    d.polygon(ghost, fill=C('#D6C79B'))
    edges(d, ghost, 2, 1.0, col=C('#6B5A44'))
    cp = sc(to_polys(('rect', CARD))[0])
    d.polygon(cp, fill=CREAM)
    d.polygon(sc([(CARD[0], CARD[1]), (CARD[2], CARD[1]), (CARD[2], 826), (CARD[0], 826)]), fill=BRK[2])
    d.polygon(sc([(CARD[0] + 76, 826), (CARD[2], 826), (CARD[2], CARD[3]), (CARD[0] + 96, CARD[3])]), fill=C('#DACBA2'))
    for i, yy in enumerate((850, 872, 894)):
        d.line(sc([(603, yy), (603 + (86 if i < 2 else 56), yy)]), fill=GRY[1], width=3 * S)
    edges(d, cp, 4, 1.0)
    # drawer front: faux-wood collage cut by a diagonal into two grain directions
    df = sc(chamfer((503, FRONT_Y, 957, SH_B + 4), 10))
    wood(img, df)
    nx, ny = math.sin(.26), -math.cos(.26)
    half = clip(df, nx, ny, -(nx * 700 * S + ny * 980 * S))
    wood(img, half, base=C('#8C6039'), grain=(C('#4F3319'), C('#6D4725')))
    edges(d, df, 5, 1.0)
    d.line(sc([(700, 917), (760, 1034)]), fill=INK, width=4)
    d.polygon(sc(chamfer((690, 960, 770, 984), 6)), fill=OCH[3])
    edges(d, sc(chamfer((690, 960, 770, 984), 6)), 3, 1.0)

    # ---- robot: every part is a stack of planes, light from several directions at once
    robo = [GRY, GRY, OCH]
    OCHD = OCH[:4]
    for sh in LEGS + TORSO:
        for pg in to_polys(sh):
            plane_stack(img, sc(pg), robo, 5 if area(pg) > 6000 else 2, base=1, spread=1, w=4, hatch_p=.3)
    # torso seen from the side as well: a darker parallelogram at the left
    sd = sc([(242, 706), (204, 742), (204, 884), (242, 906)])
    plane_stack(img, sd, [GRY], 2, base=0, spread=1, hatch_p=.9, w=4)
    for pg in to_polys(PANEL[0]):
        plane_stack(img, sc(pg), [BRK, OCH], 3, base=2, spread=1, w=3, hatch_p=.2)
    pdr = ImageDraw.Draw(img)
    for (yy, ln) in ((769, 70), (792, 52), (815, 34)):
        pdr.rectangle(sc([(290, yy - 5), (300, yy + 5)]), fill=CREAM)
        pdr.line(sc([(314, yy), (314 + ln, yy)]), fill=INK, width=4 * S // 2)
    for pts in (ARM_L, ARM_R):
        for sh in pts:
            for pg in to_polys(sh):
                plane_stack(img, sc(pg), [GRY, GRY, OCH], 2, base=1, spread=1, w=4, hatch_p=.3, minA=1500)
    # head: frontal view + profile view merged into one head
    head = sc(to_polys(HEAD[0])[0])
    plane_stack(img, head, [GRY, GRY, OCH], 5, base=1, spread=2, w=4, hatch_p=.2)
    prof = sc([(412, 566), (470, 590), (490, 628), (466, 640), (480, 668), (446, 696), (412, 696)])
    plane_stack(img, prof, [OCH, GRY], 3, base=3, spread=1, w=4, hatch_p=.4)
    vis = sc(to_polys(VISOR[0])[0])
    d.polygon(vis, fill=C('#262E36'))
    hatch(img, vis, .1, 10 * S, GRY[1], 2)
    edges(d, vis, 4, 1.0)
    d.polygon(sc([(268, 616), (372, 616), (372, 636), (268, 636)]), fill=OCH[3])           # sensor strip, not an eye
    d.polygon(sc([(432, 604), (462, 614), (468, 636), (440, 628)]), fill=OCH[3])          # same sensor, profile view
    edges(d, sc([(432, 604), (462, 614), (468, 636), (440, 628)]), 3, 1.0)
    for pg in to_polys(ANT[0]):
        d.polygon(sc(pg), fill=GRY[0])
    d.polygon(sc(to_polys(ANT[1])[0]), fill=BRK[2])
    edges(d, sc(to_polys(ANT[1])[0]), 3, 1.0)

    # ---- long passage lines run on through objects, across the scene
    for (p, q) in (((0, 330), (610, 130)), ((330, 20), (850, 980)), ((1080, 250), (650, 700)), ((140, 1020), (520, 420)), ((1000, 20), (1080, 380))):
        d.line(sc([p, q]), fill=shade_c(INK, 1.4), width=2)

    # ---- type on collage paper: newsprint label, stencil number with shifted ghost copy
    def paper(poly, lines=None):
        pp = sc(poly)
        if lines:
            collage_text(img, pp, NEWS, lines, 15, C('#8F8670'))
        else:
            d.polygon(pp, fill=CREAM)
        edges(d, pp, 4, 1.0)
    paper([(52, 214), (512, 198), (528, 386), (58, 396)])
    paper([(54, 84), (300, 78), (306, 178), (60, 184)])
    paper([(64, 446), (264, 442), (270, 504), (68, 510)])
    paper([(600, 84), (1010, 66), (1024, 172), (610, 196)], NEWS_LINES)
    text2(img, NUM, (68 + 9, 176 + 7), NUM_SZ, BRK[2], AVE, 8)          # ghost: second viewpoint
    text2(img, NUM, NUM_POS, NUM_SZ, INK, AVE, 8)
    text2(img, TITLE, TITLE_POS, TITLE_SZ, INK)
    text2(img, LABEL, LABEL_POS, LABEL_SZ, INK)
    bar = sc([(80, 412), (470, 412), (470, 436), (80, 436)])
    d.polygon(bar, fill=CREAM)
    d.polygon(sc([(80, 412), (80 + 390 * .61, 412), (80 + 390 * .61 - 10, 436), (80, 436)]), fill=BRK[2])
    edges(d, bar, 4, 1.0)

    # ---- grain: a sprinkle of tiny flecks so flat planes feel like paper/canvas, not vector fill
    g = ImageDraw.Draw(img)
    for _ in range(26000):
        x, y = R.randint(0, W * S - 1), R.randint(0, H * S - 1)
        g.point((x, y), fill=R.choice((C('#D8CCAA'), C('#9C8F72'), C('#EFE6CB'))))
    img = img.resize((W, H), Image.LANCZOS)
    img.save(os.path.join(HERE, 'sample.png'))


if __name__ == '__main__':
    main()
