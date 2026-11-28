"""Style catalog sample: low-poly (flat-shaded triangles, colour by face normal).
Self-contained: Python 3 + PIL only. Renders sample.png (1080x1350) next to this file.
Technique encoded here:
  - every surface is a triangle (or a flat prism face); one flat colour per face, no gradients inside a face
  - face colour = Lambert(normal . LIGHT) quantised onto a 4-step ramp (shadow / base / light / highlight)
  - light from the top-left; iso prisms: top = light, left face = base, right face = shadow,
    1-step highlight bevel on the lit front edges
  - terrain = jittered lattice split into triangles, ramps get lighter / bluer with distance
  - no outlines: neighbouring faces are separated only by value
  - 2x supersampling then LANCZOS down, so edges are crisp but not jagged
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFont

W, H, S = 1080, 1350, 2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample.png")
HEI = "/System/Library/Fonts/STHeiti Medium.ttc"
RNG = random.Random(61)
LIGHT = (-0.45, -0.65, 0.62)
_l = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _l for c in LIGHT)



def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def ramp(*hs): return [rgb(h) for h in hs]
def clamp(v, a, b): return max(a, min(b, v))

# ---- palette: every ramp is shadow / base / light / highlight (sky has 6 steps) -------
SKY = ramp('1f2147', '2e2f63', '4a3f78', '7a4f86', 'b8627e', 'e88a6e')   # zenith -> horizon
FAR = ramp('3b3a6b', '524d85', '6e66a0', '8f86b8')                     # far mountains: lighter, low contrast
HILL = ramp('1f4a4a', '2f6b5f', '4a9380', '6fb69c')                    # mid hills: darker, more contrast
CALM = ramp('203f43', '234549', '264c4e')                              # bottom band: adjacent steps only
VAULT = ramp('1b2f5c', '2e5a88', '5a91b0', 'a6cbdc')                   # knowledge base block
STEEL = ramp('444a78', '7a7ea6', 'c0bdd6', 'ece6ee')                   # agent body
DARK = ramp('1f2036', '33344f', '4f5070', '7a7c9c')                    # tracks, joints
AMBER = ramp('b5601c', 'e8923a', 'ffb94d', 'ffe3a0')                   # accent: number, core, card tab
CYAN = ramp('1f7f86', '38bfc0', '8aeee0', 'd2fff6')                    # visor, crystal
CARD = ramp('b49a6e', 'e0c994', 'f6e6bd', 'fff7e0')                    # cream note card
MOUTH = rgb('0e1a2e')

img = Image.new("RGB", (W * S, H * S), SKY[0])
d = ImageDraw.Draw(img)


def fill(pts, color):
    p = [(x * S, y * S) for x, y in pts]
    d.polygon(p, fill=color, outline=color)


def jitter_grid(x0, y0, x1, y1, nx, ny, jit, zfn):
    """(ny+1) x (nx+1) lattice of (x, y, z); inner points jittered, border points slide along the border"""
    dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
    g = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x, y = x0 + i * dx, y0 + j * dy
            if 0 < i < nx: x += RNG.uniform(-jit, jit) * dx
            if 0 < j < ny: y += RNG.uniform(-jit, jit) * dy
            row.append((x, y, zfn(x, y)))
        g.append(row)
    return g


def shade_idx(p0, p1, p2, n, bias=0.0):
    """Lambert of the triangle normal (x right, y down, z up) quantised to n steps"""
    ax, ay, az = (p1[k] - p0[k] for k in range(3)); bx, by, bz = (p2[k] - p0[k] for k in range(3))
    nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
    if nz < 0: nx, ny, nz = -nx, -ny, -nz
    L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
    dot = (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / L
    t = (dot - 0.3) / 0.65 + bias
    return int(clamp(t, 0, 0.999) * n)


def tri_mesh(g, colorfn):
    for j in range(len(g) - 1):
        for i in range(len(g[0]) - 1):
            a, b, c, e = g[j][i], g[j][i + 1], g[j + 1][i + 1], g[j + 1][i]
            tris = ((a, b, c), (a, c, e)) if (i + j) % 2 == 0 else ((a, b, e), (b, c, e))
            for t in tris:
                fill([(p[0], p[1]) for p in t], colorfn(t))


def masked_mesh(g, colorfn, ridge):
    """draw the mesh only below a ridge line"""
    global d
    keep_img, keep_d = img, d
    layer = Image.new("RGB", img.size); d = ImageDraw.Draw(layer)
    tri_mesh(g, colorfn)
    d = keep_d
    mask = Image.new("L", img.size, 0)
    pts = [(x * S, ridge(x) * S) for x in range(0, W + 1, 4)] + [(W * S, H * S), (0, H * S)]
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    img.paste(layer, (0, 0), mask)


# ---- sky: a triangle mesh, ramp index follows height with a random step ---------------
g = jitter_grid(0, 0, W, 1050, 9, 11, 0.4, lambda x, y: 0)
tri_mesh(g, lambda t: SKY[clamp(int(sum(p[1] for p in t) / 3 / 1050 * 5.4 + RNG.uniform(-0.55, 0.55)), 0, 5)])

# Delaunay disc: concentric rings cut into wedges, complementary hues side by side (simultaneous contrast)
def disc(cx, cy, radii, pairs, n=12, rot=0.2):
    for ri in range(len(radii) - 1, -1, -1):
        r_out = radii[ri]; r_in = radii[ri + 1] if ri + 1 < len(radii) else 0
        off = rot + (ri % 2) * math.pi / n                  # each ring turns half a wedge
        for k in range(n):
            a0, a1 = off + math.tau * k / n, off + math.tau * (k + 1) / n
            P = lambda r, a: (cx + r * math.cos(a), cy + r * math.sin(a))
            fill([P(r_out, a0), P(r_out, a1), P(r_in, a1), P(r_in, a0)], pairs[ri][k % 2])
disc(800, 200, [128, 92, 58, 26], [(SKY[4], SKY[2]), (CYAN[0], SKY[3]), (SKY[4], VAULT[1]), (AMBER[2], AMBER[2])])

# far mountains
def ridge1(x): return 600 - 150 * abs(math.sin(x / 230 + 0.6)) - 60 * abs(math.sin(x / 97))
g = jitter_grid(0, 330, W, 900, 14, 7, 0.45, lambda x, y: 240 * abs(math.sin(x / 120 + y / 300)) + RNG.uniform(0, 60))
masked_mesh(g, lambda t: FAR[shade_idx(*t, 4, 0.05)], ridge1)

# mid hills
def ridge2(x): return 840 - 70 * abs(math.sin(x / 180 + 1.3)) - 30 * abs(math.sin(x / 61))
g = jitter_grid(0, 720, W, 1120, 12, 6, 0.45, lambda x, y: RNG.uniform(0, 160))
masked_mesh(g, lambda t: HILL[shade_idx(*t, 4)], ridge2)

# calm bottom band: 22 % of the frame, near-flat mesh, 2 adjacent ramp steps only
g = jitter_grid(0, 1050, W, H, 8, 3, 0.4, lambda x, y: RNG.uniform(0, 10))
tri_mesh(g, lambda t: CALM[1 + (shade_idx(*t, 2) > 0)])
fill([(0, 1046), (W, 1046), (W, 1054), (0, 1054)], HILL[0])         # horizon seam

# ---- iso helpers -------------------------------------------------------------------------
C30, S30 = math.cos(math.radians(30)), 0.5

def prism(fx, fy, wl, wr, h, rp, top=2, left=1, right=0, bevel=True):
    """iso box: F = front-bottom corner; left face runs up-left (length wl), right face up-right (wr).
    top = light, left = base, right = shadow; each face is split into two triangles one step apart."""
    F = (fx, fy); L = (fx - wl * C30, fy - wl * S30); R = (fx + wr * C30, fy - wr * S30)
    B = (L[0] + R[0] - F[0], L[1] + R[1] - F[1])
    up = lambda p: (p[0], p[1] - h)
    hi = lambda k: min(3, k + 1)
    fill([up(F), up(L), up(B)], rp[top]); fill([up(F), up(B), up(R)], rp[max(0, top - 1)] if top > 1 else rp[top])
    fill([F, L, up(L)], rp[left]); fill([F, up(L), up(F)], rp[hi(left)])
    fill([F, R, up(R), up(F)], rp[right])
    if bevel:
        fill([up(F), up(L), (L[0], L[1] - h + 6), (F[0], F[1] - h + 6)], rp[3])
    return dict(F=F, L=L, R=R, B=B, h=h)

def on_left(pr, u, v):
    F, L = pr['F'], pr['L']
    return (F[0] + (L[0] - F[0]) * u, F[1] + (L[1] - F[1]) * u - pr['h'] * v)

def on_right(pr, u, v):
    F, R = pr['F'], pr['R']
    return (F[0] + (R[0] - F[0]) * u, F[1] + (R[1] - F[1]) * u - pr['h'] * v)

def gem(x, y, r, rp, n=5, rot=0.0, h=1.0):
    """small faceted polygon: fan of triangles, step by angle to the light"""
    pts = [(x + r * math.cos(rot + math.tau * i / n), y + r * h * math.sin(rot + math.tau * i / n)) for i in range(n)]
    for i in range(n):
        a = rot + math.tau * (i + 0.5) / n
        k = int(clamp((-math.cos(a) * 0.45 - math.sin(a) * 0.65 + 1) / 2 * 4, 0, 3.99))
        fill([(x, y), pts[i], pts[(i + 1) % n]], rp[k])

def limb(a, b, w, rp):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    fill([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny), (b[0], b[1]), (a[0], a[1])], rp[2])
    fill([(a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny), (b[0], b[1]), (a[0], a[1])], rp[1])

def joint(x, y, r): gem(x, y, r, DARK, n=6)

def crystal(cx, cy, rw, hh, rp):
    top, bot = (cx, cy - hh / 2), (cx, cy + hh / 2)
    lf, rt = (cx - rw, cy), (cx + rw, cy)
    fr, bk = (cx, cy + rw * 0.35), (cx, cy - rw * 0.35)
    fill([top, lf, bk], rp[2]); fill([top, bk, rt], rp[1])
    fill([top, lf, fr], rp[3]); fill([top, fr, rt], rp[2])
    fill([bot, lf, fr], rp[1]); fill([bot, fr, rt], rp[0])

# ---- knowledge base: iso archive block, 3 x 4 drawer wall, crystal on top ----------------
KF = (810, 1036)
fill([(KF[0] - 40, 1040), (1080, 900), (1080, 1044)], HILL[0])        # ground shadow, falls to the right
KB = prism(KF[0], KF[1], 380, 300, 380, VAULT, top=2, left=1, right=0)
COLS, ROWS = 3, 3
OPEN = (2, 1)
for ci in range(COLS):
    for ri in range(ROWS):
        u0, v0 = 0.06 + ci * 0.31, 0.05 + ri * 0.32
        u1, v1 = u0 + 0.26, v0 + 0.27
        q = [on_left(KB, u0, v0), on_left(KB, u1, v0), on_left(KB, u1, v1), on_left(KB, u0, v1)]
        fill(q, VAULT[0])                                    # recess (shadow step)
        if (ci, ri) == OPEN:
            OPENQ = q; continue
        fill([q[3], q[2], (q[2][0], q[2][1] + 5), (q[3][0], q[3][1] + 5)], VAULT[2])   # lit upper lip
        hx, hy = on_left(KB, (u0 + u1) / 2, (v0 + v1) / 2)
        fill([(hx - 12, hy + 3), (hx + 12, hy - 9), (hx + 12, hy - 4), (hx - 12, hy + 8)],
             AMBER[2] if (ci * 3 + ri) % 5 == 0 else VAULT[3])

# the open drawer: pulled out along the left face's outward normal (toward the robot)
q = OPENQ
PULL = (-C30 * 80, S30 * 80)
mv = lambda p: (p[0] + PULL[0], p[1] + PULL[1])
fill(q, MOUTH)                                               # dark mouth left in the wall
fill([q[0], q[1], mv(q[1]), mv(q[0])], VAULT[0])             # underside
fill([q[3], q[2], mv(q[2]), mv(q[3])], CYAN[0])              # open top: glowing inside
fill([q[2], mv(q[2]), (mv(q[2])[0], mv(q[2])[1] + 0), q[1]], VAULT[0])
fr = [mv(q[0]), mv(q[1]), mv(q[2]), mv(q[3])]
mid_top = ((fr[2][0] + fr[3][0]) / 2, (fr[2][1] + fr[3][1]) / 2)

# ---- the note card: a slab in a plane parallel to the wall, sunk into the drawer ---------
# built BEFORE the drawer front, so the front panel hides its lower end = card is going in
cw, chh = 84, 130
back = (-PULL[0] * 0.42, -PULL[1] * 0.42)                    # card sits 42 % of the way back into the drawer
c0 = (mid_top[0] + back[0] + 4, mid_top[1] + back[1] + 36)    # bottom-centre of card (36 px below the lip line)
along = (-C30, -S30)                                         # card width runs parallel to the wall
cp = [(c0[0] - along[0] * cw / 2, c0[1] - along[1] * cw / 2)]
cp.append((cp[0][0] + along[0] * cw, cp[0][1] + along[1] * cw))
cp = [cp[0], cp[1], (cp[1][0], cp[1][1] - chh), (cp[0][0], cp[0][1] - chh)]
ctr = ((cp[0][0] + cp[2][0]) / 2 - 10, (cp[0][1] + cp[2][1]) / 2 - 10, 14)
for i in range(4):                                           # 4 shallow facets meeting off-centre
    p, qq = cp[i], cp[(i + 1) % 4]
    k = shade_idx(ctr, (p[0], p[1], 0), (qq[0], qq[1], 0), 4, 0.25)
    fill([ctr[:2], p, qq], CARD[max(1, k)])
def on_card(u, v): return (cp[0][0] + (cp[1][0] - cp[0][0]) * u, cp[0][1] + (cp[1][1] - cp[0][1]) * u - chh * v)
a_, b_ = on_card(0.06, 0.93), on_card(0.94, 0.93)
fill([a_, b_, (b_[0], b_[1] + 12), (a_[0], a_[1] + 12)], AMBER[1])    # amber tab = the new note
for i, L_ in enumerate((0.8, 0.8, 0.5)):                     # text lines parallel to the wall
    a_, b_ = on_card(0.12, 0.74 - i * 0.12), on_card(0.12 + L_ * 0.76, 0.74 - i * 0.12)
    fill([a_, b_, (b_[0], b_[1] + 5), (a_[0], a_[1] + 5)], CARD[0])

# drawer front panel goes on top of the card
fill(fr, VAULT[1])
fill([fr[3], fr[2], (fr[2][0], fr[2][1] + 6), (fr[3][0], fr[3][1] + 6)], VAULT[3])   # highlight bevel on the lip
fill([fr[3], (fr[3][0], fr[3][1] + 40), (fr[3][0] + (fr[2][0] - fr[3][0]) * 0.5, fr[3][1] + 40 + (fr[2][1] - fr[3][1]) * 0.5), (fr[3][0] + (fr[2][0] - fr[3][0]) * 0.5, fr[3][1] + (fr[2][1] - fr[3][1]) * 0.5)], VAULT[2])
hx, hy = (fr[0][0] + fr[2][0]) / 2, (fr[0][1] + fr[2][1]) / 2 + 8
fill([(hx - 14, hy + 4), (hx + 14, hy - 10), (hx + 14, hy - 3), (hx - 14, hy + 11)], AMBER[2])

# crystal on the roof = the stored knowledge, with a halo of small facets
tc = ((KB['F'][0] + KB['B'][0]) / 2, (KB['F'][1] + KB['B'][1]) / 2 - KB['h'])
for i in range(6):
    a = i * 1.05 + 0.4; rr = 92 + (i % 3) * 18
    gem(tc[0] + rr * math.cos(a), tc[1] - 90 + rr * 0.5 * math.sin(a), 8 + (i % 2) * 4, CYAN, n=4, rot=a)
fill([(tc[0] - 46, tc[1] + 6), (tc[0], tc[1] - 18), (tc[0] + 46, tc[1] + 6), (tc[0], tc[1] + 30)], VAULT[0])  # contact shadow
crystal(tc[0], tc[1] - 80, 48, 96, CYAN)

# ---- the AI agent: a boxy low-poly mech on tracks, one visor band, no face ---------------
AX, AY = 235, 1030
fill([(AX - 130, AY + 8), (AX + 200, AY + 8), (AX + 225, AY - 20), (AX - 105, AY - 20)], HILL[0])
TR = prism(AX, AY, 190, 120, 54, DARK, top=2, left=1, right=0)
for i in range(4):
    x, y = on_left(TR, 0.14 + i * 0.24, 0.42); gem(x, y, 14, STEEL, n=6, h=0.6)
TO = prism(AX - 4, AY - 54, 150, 120, 190, STEEL, top=2, left=1, right=0)       # torso
cx_, cy_ = on_left(TO, 0.5, 0.52)                            # chest core: amber diamond plate
fill([(cx_ - 30, cy_ - 2), (cx_ + 4, cy_ - 34), (cx_ + 30, cy_ - 4), (cx_ - 4, cy_ + 28)], AMBER[0])
fill([(cx_ - 26, cy_ - 4), (cx_ + 3, cy_ - 30), (cx_ + 3, cy_ - 2)], AMBER[3])
fill([(cx_ + 3, cy_ - 30), (cx_ + 26, cy_ - 4), (cx_ + 3, cy_ - 2)], AMBER[2])
fill([(cx_ - 26, cy_ - 4), (cx_ + 3, cy_ - 2), (cx_ - 3, cy_ + 24)], AMBER[1])
for v in (0.16, 0.86):                                       # vent slats
    a, b = on_left(TO, 0.12, v), on_left(TO, 0.88, v)
    fill([a, b, (b[0], b[1] - 5), (a[0], a[1] - 5)], STEEL[0])
s0 = on_left(TO, 0.88, 0.86); s1 = (s0[0] - 10, s0[1] + 120)  # idle arm on the lit side, hanging
limb(s0, s1, 30, STEEL); joint(*s0, 22)
fill([(s1[0] - 13, s1[1]), (s1[0] + 10, s1[1] + 2), (s1[0] - 3, s1[1] + 22)], DARK[1])
prism(AX + 34, AY - 244, 56, 50, 20, DARK, bevel=False)                         # neck
HD = prism(AX + 8, AY - 264, 125, 100, 100, STEEL, top=2, left=1, right=0)       # head
VV = 0.5                                                     # visor: one sensor band over both faces
a, b = on_left(HD, 0.08, VV), on_left(HD, 0.94, VV)
fill([a, b, (b[0], b[1] - 22), (a[0], a[1] - 22)], CYAN[1]); fill([a, b, (b[0], b[1] - 6), (a[0], a[1] - 6)], CYAN[3])
a, b = on_right(HD, 0.0, VV), on_right(HD, 0.9, VV)
fill([a, b, (b[0], b[1] - 22), (a[0], a[1] - 22)], CYAN[0])
top_c = ((HD['F'][0] + HD['B'][0]) / 2, (HD['F'][1] + HD['B'][1]) / 2 - HD['h'])
limb(top_c, (top_c[0], top_c[1] - 62), 9, DARK)
gem(top_c[0], top_c[1] - 70, 12, AMBER, n=5, h=1.2)
# working arm: shadow-side shoulder -> elbow -> gripper above the card
SH = on_right(TO, 0.5, 0.8)
GR = (cp[3][0] - 4, cp[3][1] + 10)                           # claws close on the card's left edge
EL = (GR[0] - 100, GR[1] - 70)
limb(SH, EL, 38, STEEL); limb(EL, GR, 30, STEEL)
joint(*SH, 30); joint(*EL, 25)
fill([(GR[0] - 14, GR[1] - 26), (GR[0] + 22, GR[1] - 30), (GR[0] + 6, GR[1] - 8)], DARK[2])
fill([(GR[0] - 14, GR[1] + 14), (GR[0] + 26, GR[1] + 20), (GR[0] + 8, GR[1] + 2)], DARK[0])
# ===================================== type ============================================
def check_glyphs(font, text):
    """fail loudly if any CJK char would render as tofu (same bitmap as a missing glyph)"""
    def bm(ch):
        im = Image.new("L", (font.size * 2, font.size * 2), 0)
        ImageDraw.Draw(im).text((0, 0), ch, font=font, fill=255)
        return im.tobytes()
    miss = bm('\U0010FFFD')
    for ch in text:
        if ch.strip() and (bm(ch) == miss or not any(bm(ch))):
            raise SystemExit(f"missing glyph {ch!r} in {font.path}")


def faceted_text(xy, text, font, rp, cell, extrude, lo=1, hi=3):
    """extruded type: shadow-step copies offset down-right, then a facet mesh through the glyph mask"""
    big = (xy[0] * S, xy[1] * S)
    for k in range(extrude, 0, -1):
        ImageDraw.Draw(img).text((big[0] + k * S, big[1] + k * S), text, font=font, fill=rp[0])
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text(big, text, font=font, fill=255)
    x0, y0, x1, y1 = mask.getbbox()
    layer = Image.new("RGB", img.size)
    global d
    keep = d; d = ImageDraw.Draw(layer)
    gg = jitter_grid(x0 / S - 4, y0 / S - 4, x1 / S + 4, y1 / S + 4,
                     max(2, int((x1 - x0) / S / cell)), max(2, int((y1 - y0) / S / cell)), 0.38,
                     lambda x, y: RNG.uniform(0, cell * 0.9))
    tri_mesh(gg, lambda t: rp[lo + min(hi - lo, shade_idx(*t, hi - lo + 1, 0.15))])
    d = keep
    img.paste(layer, (0, 0), mask)


fh = ImageFont.truetype(HEI, 112 * S); check_glyphs(fh, "知識庫")
faceted_text((72, 66), "知識庫", fh, CARD, cell=40, extrude=6, lo=2, hi=3)
fb = ImageFont.truetype(HEI, 250 * S)
faceted_text((62, 200), "61%", fb, AMBER, cell=46, extrude=12, lo=1, hi=3)

img = img.resize((W, H), Image.LANCZOS)
img.save(OUT)
print(OUT)
