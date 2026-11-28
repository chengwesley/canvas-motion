#!/usr/bin/env python3
"""chrono-motion sample (original artwork): an AI agent's arm, body and note card are shown
as 7 equal-time positions (multiple exposure) ending inside the knowledge base drawer.
Python 3 + PIL only. Deterministic. Writes sample.png (1080x1350)."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

W, H, S = 1080, 1350, 2
GROUND = 1052                       # bottom ~22% stays calm
HERE = os.path.dirname(os.path.abspath(__file__))
CJK = '/System/Library/Fonts/STHeiti Medium.ttc'
AVN = '/System/Library/Fonts/Avenir Next.ttc'

def hx(s): return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
PAPER, PAPER_D = hx('F1E8D6'), hx('E3D6BC')
GRID = hx('DDD0B6')
INK, INK_L = hx('3A2A1E'), hx('6B5644')
OCHRE, OCHRE_L = hx('D9A441'), hx('F2D58F')
SIENNA, SIENNA_D = hx('B4562F'), hx('8A3C1E')
SLATE, SLATE_L, SLATE_D = hx('24485A'), hx('3F7387'), hx('15303D')
CREAM = hx('FFF8E8')
HOLE, HOLE_D = hx('141D22'), hx('0B1013')

def font(path, size, idx=0): return ImageFont.truetype(path, int(size * S), index=idx)

def lerp(a, b, t): return a + (b - a) * t
def lerpc(a, b, t): return tuple(int(lerp(a[i], b[i], t)) for i in range(3))
def ease(t): return t * t * (3 - 2 * t)          # slow in / slow out
def P(pts): return [(x * S, y * S) for x, y in pts]

def _glyph(f, ch):
    im = Image.new('L', (int(f.size * 2), int(f.size * 2)), 0)
    ImageDraw.Draw(im).text((4, 4), ch, font=f, fill=255)
    return im.tobytes()

def check_glyphs(text, f):
    bad = _glyph(f, '\U0010ffff')
    for ch in text:
        if ch.isspace(): continue
        g = _glyph(f, ch)
        if g == bad or not any(g): raise SystemExit('missing glyph: %r' % ch)

class Layer:
    def __init__(self):
        self.im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
    def text(self, s, x, y, size, col, path=CJK, idx=0, a=255):
        f = font(path, size, idx)
        if path == CJK: check_glyphs(s, f)
        self.d.text((x * S, y * S), s, font=f, fill=col + (a,))
    def rr(self, box, r, col, a=255):
        self.d.rounded_rectangle([v * S for v in box], r * S, fill=col + (a,))
    def line(self, pts, w, col, a=255):
        self.d.line(P(pts), fill=col + (a,), width=int(w * S), joint='curve')
        for x, y in (pts[0], pts[-1]):
            self.d.ellipse([(x - w / 2) * S, (y - w / 2) * S, (x + w / 2) * S, (y + w / 2) * S], fill=col + (a,))
    def dot(self, x, y, r, col, a=255):
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=col + (a,))

# ---------------------------------------------------------------- geometry
def ik(sh, hand, l1=160, l2=160):
    dx, dy = hand[0] - sh[0], hand[1] - sh[1]
    d = min(math.hypot(dx, dy), l1 + l2 - 1)
    a = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    ang = a + math.acos(max(-1, min(1, c)))          # elbow bends downward
    return (sh[0] + l1 * math.cos(ang), sh[1] + l1 * math.sin(ang))

def card_pts(cx, cy, deg, w=118, h=160):
    r = math.radians(deg)
    def tf(x, y): return (cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r))
    return {'body': [tf(-w / 2, -h / 2), tf(w / 2, -h / 2), tf(w / 2, h / 2), tf(-w / 2, h / 2)],
            'head': [tf(-w / 2, -h / 2), tf(w / 2, -h / 2), tf(w / 2, -h / 2 + h * .19), tf(-w / 2, -h / 2 + h * .19)],
            'lines': [[tf(-w / 2 + 16, -h / 2 + h * (.34 + .15 * k)), tf(w / 2 - 16 - (24 if k == 3 else 0), -h / 2 + h * (.34 + .15 * k))] for k in range(4)],
            'edge': tf(-w / 2 + 4, -10)}

def pose(i, n):
    """equal time steps; ease makes positions bunch up at both ends (slow in / slow out)"""
    t = i / (n - 1); e = ease(t)
    RX = lerp(230, 400, e)
    cx = lerp(520, 760, e); cy = lerp(540, 868, e) - 40 * math.sin(math.pi * e)
    deg = lerp(-22, 0, e)
    ph = 0 if i == n - 1 else i * 1.9
    return dict(t=t, RX=RX, card=(cx, cy, deg), ph=ph, lean=lerp(10, 0, e))

def robot_geo(p):
    RX, ph = p['RX'], p['ph']
    g = {}
    g['sh'] = (RX + p['lean'] + 82, GROUND - 252)
    cp = card_pts(*p['card'])
    g['hand'] = cp['edge']
    g['el'] = ik(g['sh'], g['hand'])
    hip = (RX, GROUND - 112)
    g['legs'] = []
    for s in (-1, 1):
        sw = math.sin(ph + (0 if s < 0 else math.pi))
        lift = max(0.0, math.cos(ph + (0 if s < 0 else math.pi))) * 16 if ph else 0
        g['legs'].append((RX + s * 38, GROUND - 112, RX + s * 38 + 44 * sw * (1 if ph else 0), GROUND - 8 - lift))
    g['body'] = (RX - 85, GROUND - 305, RX + 85, GROUND - 112)
    g['head'] = (RX - 100 + p['lean'], GROUND - 446, RX + 100 + p['lean'], GROUND - 322)
    g['ant'] = ((RX + p['lean'] + 40, GROUND - 446), (RX + p['lean'] + 52, GROUND - 505))
    g['neck'] = (RX + p['lean'] * .5, GROUND - 316)
    g['hip'] = hip
    return g, cp

def body_sil(m, g):
    d = ImageDraw.Draw(m)
    for (x0, y0, x1, y1) in g['legs']:
        d.line(P([(x0, y0), (x1, y1)]), fill=255, width=30 * S)
        d.ellipse([(x1 - 24) * S, (y1 - 10) * S, (x1 + 30) * S, (y1 + 12) * S], fill=255)
    d.rounded_rectangle([v * S for v in g['body']], 44 * S, fill=255)
    d.rounded_rectangle([v * S for v in g['head']], 36 * S, fill=255)
    d.line(P(list(g['ant'])), fill=255, width=8 * S)

def arm_sil(m, g, cp):
    d = ImageDraw.Draw(m)
    d.line(P([g['sh'], g['el'], g['hand']]), fill=255, width=26 * S, joint='curve')
    d.polygon(P(cp['body']), fill=255)

# ---------------------------------------------------------------- scene
def build():
    cv = Image.new('RGB', (W * S, H * S), PAPER)
    d = ImageDraw.Draw(cv)
    # Muybridge-style measuring grid on the wall (faint) and a ruled ground band
    for x in range(0, W + 1, 90): d.line([(x * S, 0), (x * S, GROUND * S)], fill=GRID, width=2)
    for y in range(GROUND, 0, -90): d.line([(0, y * S), (W * S, y * S)], fill=GRID, width=2)
    d.rectangle([0, GROUND * S, W * S, H * S], fill=PAPER_D)
    d.line([(0, GROUND * S), (W * S, GROUND * S)], fill=INK_L, width=4)
    for x in range(0, W + 1, 45):                                   # ground scale ticks
        d.line([(x * S, GROUND * S), (x * S, (GROUND + (22 if x % 90 == 0 else 12)) * S)], fill=INK_L, width=3)

    # knowledge base (right): three rows, bottom row is a drawer whose front hides the card
    sh = Layer()
    X0, X1, T, B = 590, 1020, 360, 1030
    rows = [T, T + 195, T + 389, B]
    sh.rr((X0, T, X1, B), 16, SLATE_D)
    rnd = random.Random(7)
    cols = [OCHRE, SIENNA, CREAM, SLATE_L, OCHRE_L]
    for r in range(2):
        y0, y1 = rows[r] + 16, rows[r + 1] - 6
        sh.rr((X0 + 14, y0, X1 - 14, y1), 6, HOLE)
        x = X0 + 24
        while x < X1 - 60:
            w = rnd.choice([26, 32, 38, 30, 42]); hgt = rnd.choice([128, 140, 150, 118]) if r == 0 else rnd.choice([120, 138, 146])
            hgt = min(hgt, y1 - y0 - 12)
            c = cols[rnd.randrange(len(cols))]
            sh.rr((x, y1 - hgt, x + w, y1), 4, c)
            sh.rr((x + w * .62, y1 - hgt, x + w, y1), 4, lerpc(c, INK, .28))
            x += w + 4
    sh.rr((X0 + 14, rows[2] + 16, X1 - 14, B - 14), 6, HOLE)
    sh.rr((X0 + 14, rows[2] + 16, X1 - 14, rows[2] + 30), 4, HOLE_D)
    sh.rr((690, 770, 830, 880), 6, OCHRE_L)                          # lit slot behind the card
    cv.paste(sh.im, (0, 0), sh.im)

    n = 7
    poses = [pose(i, n) for i in range(n)]
    gs = [robot_geo(p) for p in poses]

    # final card sits inside the drawer: drawn after the cavity, before the front plate
    g, cp = gs[-1]
    cd = Layer()
    cd.d.polygon(P(cp['body']), fill=CREAM + (255,))
    cd.d.polygon(P(cp['head']), fill=SIENNA + (255,))
    for ln in cp['lines']: cd.line(ln, 6, hx('BFB59F'))
    cv.paste(cd.im, (0, 0), cd.im)

    fr = Layer()                                                     # drawer front plate, lower half only
    fr.rr((X0 - 12, 858, X1 + 12, B - 4), 12, SLATE_L)
    fr.rr((X0 - 12, 858, X1 + 12, 872), 8, lerpc(SLATE_L, CREAM, .25))
    fr.rr((X0 - 12 + 6, 1000, X1 + 12 - 6, B - 4), 8, SLATE)
    fr.rr((750, 930, 860, 952), 11, SLATE_D)                         # handle slot
    cv.paste(fr.im, (0, 0), fr.im)

    # ghosts: successive exposures, older = fainter, colour drifts ochre -> sienna
    for i in range(n - 1):
        tt = i / (n - 2)
        col = lerpc(OCHRE, SIENNA, tt)
        mb = Image.new('L', (W * S, H * S), 0); body_sil(mb, gs[i][0])        # body: outline only, very faint
        eb = ImageChops.subtract(mb, mb.filter(ImageFilter.MinFilter(5)))
        cv.paste(Image.new('RGB', cv.size, lerpc(col, INK, .35)), (0, 0), eb.point(lambda v: int(v * (.22 + .25 * tt))))
        cv.paste(Image.new('RGB', cv.size, col), (0, 0), mb.point(lambda v: int(v * .07)))
        ma = Image.new('L', (W * S, H * S), 0); arm_sil(ma, *gs[i])           # arm + card: filled exposure
        ea = ImageChops.subtract(ma, ma.filter(ImageFilter.MinFilter(5)))
        cv.paste(Image.new('RGB', cv.size, col), (0, 0), ma.point(lambda v: int(v * (.22 + .22 * tt))))
        cv.paste(Image.new('RGB', cv.size, lerpc(col, INK, .5)), (0, 0), ea.point(lambda v: int(v * (.45 + .4 * tt))))

    # Marey-style skeleton + Balla-style path, drawn thin over the exposures
    ov = Layer()
    path = [gs[i][1]['edge'] for i in range(n)]
    cpts = []
    for i in range(121):                                             # dense arc through the card centres
        pp = pose_cont(i / 120.0); cpts.append((pp[0], pp[1]))
    for off, wd, al in ((-18, 3, 110), (18, 3, 110), (0, 5, 210)):
        for k in range(0, 120, 4):                                   # dashed Balla-style paths
            ov.line([(x, y + off) for x, y in cpts[k:k + 3]], wd, SIENNA, al)
    for i in range(n):
        g, cp = gs[i]; a = int(lerp(120, 255, i / (n - 1)))
        ov.line([g['sh'], g['el'], g['hand']], 3, INK, a)
        ov.line([g['neck'], g['hip']], 3, INK, a)
        for (x0, y0, x1, y1) in g['legs']: ov.line([(x0, y0), (x1, y1)], 3, INK, a)
        for pt in (g['sh'], g['el'], g['hand']): ov.dot(pt[0], pt[1], 6, CREAM, a); ov.d.ellipse([(pt[0] - 6) * S, (pt[1] - 6) * S, (pt[0] + 6) * S, (pt[1] + 6) * S], outline=INK + (a,), width=3)
        cx, cy, dg = poses[i]['card']
        ov.dot(cx, cy, 7, SIENNA_D, a)
        if i < n - 1:
            bx, by = (cx - 100, cy - 70) if i == 0 else (cx + 6, cy - 112)
            ov.dot(bx, by, 19, CREAM, 235); ov.d.ellipse([(bx - 19) * S, (by - 19) * S, (bx + 19) * S, (by + 19) * S], outline=SIENNA_D + (255,), width=3)
            ov.text(str(i + 1), bx - 8, by - 19, 30, SIENNA_D, AVN, 0)
    cv.paste(ov.im, (0, 0), ov.im)

    # the current (last) body, solid, drawn on top
    g, cp = gs[-1]
    fg = Layer(); p = poses[-1]
    for (x0, y0, x1, y1) in g['legs']:
        fg.line([(x0, y0), (x1, y1)], 30, SLATE_D)
        fg.d.ellipse([(x1 - 24) * S, (y1 - 10) * S, (x1 + 30) * S, (y1 + 12) * S], fill=SLATE_D + (255,))
    fg.line(list(g['ant']), 8, INK); fg.dot(g['ant'][1][0], g['ant'][1][1], 12, SIENNA)
    fg.rr(g['body'], 44, SLATE)
    fg.rr((g['body'][2] - 52, g['body'][1] + 4, g['body'][2], g['body'][3] - 4), 40, SLATE_D, 120)       # right-side shade
    fg.rr((g['body'][0] + 30, g['body'][1] + 40, g['body'][0] + 108, g['body'][1] + 118), 12, SLATE_L)      # chest panel
    fg.dot(g['body'][0] + 50, g['body'][1] + 62, 7, OCHRE)
    fg.line([(g['body'][0] + 66, g['body'][1] + 62), (g['body'][0] + 92, g['body'][1] + 62)], 5, CREAM)
    fg.line([(g['body'][0] + 50, g['body'][1] + 88), (g['body'][0] + 92, g['body'][1] + 88)], 5, CREAM)
    fg.rr(g['head'], 36, CREAM)
    hd = g['head']
    fg.rr((hd[2] - 48, hd[1] + 4, hd[2], hd[3] - 4), 30, hx('E5D7BF'), 160)
    fg.rr((hd[0] + 22, hd[1] + 30, hd[2] - 22, hd[1] + 88), 24, SLATE_D)       # visor
    fg.rr((hd[0] + 46, hd[1] + 54, hd[2] - 40, hd[1] + 64), 5, OCHRE)          # sensor bar
    fg.line([g['sh'], g['el'], g['hand']], 26, SLATE_D)
    fg.dot(g['sh'][0], g['sh'][1], 20, SLATE); fg.dot(g['el'][0], g['el'][1], 15, SLATE_L); fg.dot(g['hand'][0], g['hand'][1], 17, SLATE)
    cv.paste(fg.im, (0, 0), fg.im)

    # type block
    tx = Layer()
    tx.rr((78, 70, 150, 82), 6, SIENNA)
    tx.text('知識庫', 74, 100, 66, INK)
    tx.text('61%', 68, 176, 184, SIENNA, AVN, 8)
    tx.rr((80, 412, 470, 436), 12, PAPER_D); tx.rr((80, 412, 80 + 390 * .61, 436), 12, SLATE)
    tx.text('筆記已歸檔', 80, 456, 32, INK_L)
    cv.paste(tx.im, (0, 0), tx.im)
    return cv

def pose_cont(t):
    e = ease(t)
    return (lerp(520, 760, e), lerp(540, 868, e) - 40 * math.sin(math.pi * e))

if __name__ == '__main__':
    out = build().resize((W, H), Image.LANCZOS)
    out.save(os.path.join(HERE, 'sample.png'))
