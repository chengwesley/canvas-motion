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

# ---- palette: every ramp is shadow / base / light / highlight ----------------------
SKY = ramp('1f2147', '2e2f63', '4a3f78', '7a4f86', 'b8627e', 'e88a6e')   # zenith -> horizon
FAR = ramp('3b3a6b', '524d85', '6e66a0', '8f86b8')                     # far mountains (lighter, low contrast = atmospheric perspective)
def ridge1(x): return 560 - 150 * abs(math.sin(x / 230 + 0.6)) - 60 * abs(math.sin(x / 97))
g = jitter_grid(0, 320, W, 860, 14, 7, 0.45, lambda x, y: 240 * abs(math.sin(x / 120 + y / 300)) + RNG.uniform(0, 60))
masked_mesh(g, lambda t: FAR[shade_idx(*t, 4, 0.05)], ridge1)

# mid hills (darker, more contrast)
def ridge2(x): return 820 - 70 * abs(math.sin(x / 180 + 1.3)) - 30 * abs(math.sin(x / 61))
g = jitter_grid(0, 700, W, 1060, 12, 5, 0.45, lambda x, y: RNG.uniform(0, 160))
masked_mesh(g, lambda t: HILL[shade_idx(*t, 4)], ridge2)

# calm bottom band: 22 % of the frame, near-flat mesh, 2 adjacent ramp steps only
g = jitter_grid(0, 1050, W, H, 8, 3, 0.4, lambda x, y: RNG.uniform(0, 10))
tri_mesh(g, lambda t: CALM[1 + (shade_idx(*t, 2) > 0)])
fill([(0, 1046), (W, 1046), (W, 1054), (0, 1054)], HILL[0])         # horizon seam


def on_right(pr, u, v):
    F, Rr = pr['F'], pr['R']
    return (F[0] + (Rr[0] - F[0]) * u, F[1] + (Rr[1] - F[1]) * u - pr['h'] * v)


def ground_shadow(pts): fill(pts, HILL[0])


# ---- knowledge base: an iso archive block with a drawer wall, crystal on top ---------
ground_shadow([(800, 1044), (1080, 900), (1080, 1044)])
KB = prism(800, 1036, 230, 270, 300, VAULT, top=2, left=1, right=0)
COLS, ROWS = 4, 4
OPEN = (1, 2)
for ci in range(COLS):
    for ri in range(ROWS):
        u0, u1 = 0.06 + ci * 0.225, 0.06 + ci * 0.225 + 0.19
        v0, v1 = 0.07 + ri * 0.225, 0.07 + ri * 0.225 + 0.17
        q = [on_left(KB, u0, v0), on_left(KB, u1, v0), on_left(KB, u1, v1), on_left(KB, u0, v1)]
        fill(q, VAULT[0])                                    # recess (shadow step)
        if (ci, ri) == OPEN:
            OPENQ = q; continue
        fill([q[3], q[2], (q[2][0], q[2][1] + 5), (q[3][0], q[3][1] + 5)], VAULT[2])   # lit upper lip
        hx, hy = on_left(KB, (u0 + u1) / 2, (v0 + v1) / 2)
        fill([(hx - 9, hy + 2), (hx + 9, hy - 8), (hx + 9, hy - 3), (hx - 9, hy + 7)],
             AMBER[2] if (ci * 3 + ri) % 5 == 0 else VAULT[3])
# the open drawer: pulled out along the left face's outward normal
q = OPENQ
fill(q, rgb('0e1a2e'))                                       # dark mouth
PULL = (-RX * 84, -RY * 84)
mv = lambda p: (p[0] + PULL[0], p[1] + PULL[1])
fill([q[0], q[1], mv(q[1]), mv(q[0])], VAULT[0])             # underside
# drawer box: front panel + inside (lower than rim) + lit rim
fr = [mv(q[0]), mv(q[1]), mv(q[2]), mv(q[3])]
fill([q[3], q[2], mv(q[2]), mv(q[3])], CYAN[0])              # open top = glowing inside
cards_in = [(mv(q[3])[0] + 26 + i * 20, mv(q[3])[1] + 6 - i * 11.5) for i in range(5)]
for x, y in cards_in:                                        # filed cards standing in the drawer
    fill([(x, y), (x + 14, y - 8), (x + 14, y - 26), (x, y - 18)], CARD[1])
    fill([(x, y - 18), (x + 14, y - 26), (x + 18, y - 24), (x + 4, y - 16)], CARD[3])
fill(fr, VAULT[1])                                           # drawer front
fill([fr[3], fr[2], (fr[2][0], fr[2][1] + 6), (fr[3][0], fr[3][1] + 6)], VAULT[3])   # highlight bevel
hx, hy = (fr[0][0] + fr[2][0]) / 2, (fr[0][1] + fr[2][1]) / 2
fill([(hx - 12, hy + 3), (hx + 12, hy - 10), (hx + 12, hy - 3), (hx - 12, hy + 10)], AMBER[2])

# crystal on the roof = the stored knowledge, with a halo of small facets
tc = ((KB['F'][0] + KB['B'][0]) / 2, (KB['F'][1] + KB['B'][1]) / 2 - KB['h'])
for i in range(6):
    a = i * 1.05 + 0.4; rr = 92 + (i % 3) * 18
    gem(tc[0] + rr * math.cos(a), tc[1] - 90 + rr * 0.5 * math.sin(a), 8 + (i % 2) * 4, CYAN, n=4, rot=a)
fill([(tc[0] - 46, tc[1] + 6), (tc[0], tc[1] - 18), (tc[0] + 46, tc[1] + 6), (tc[0], tc[1] + 30)], VAULT[0])  # contact shadow
crystal(tc[0], tc[1] - 80, 48, 96, CYAN)

# ---- the AI agent: a boxy low-poly mech on tracks, one visor band, no face -----------
AX, AY = 150, 1030
ground_shadow([(AX - 50, AY + 8), (AX + 190, AY + 8), (AX + 215, AY - 20), (AX - 25, AY - 20)])
TR = prism(AX, AY, 150, 90, 48, DARK, top=2, left=1, right=0)
for i in range(4):
    x, y = on_left(TR, 0.14 + i * 0.24, 0.42); gem(x, y, 14, STEEL, n=6, h=0.6)
for i in range(4):
    x, y = on_right(TR, 0.14 + i * 0.24, 0.42); gem(x, y, 13, DARK, n=6, h=0.6)
prism(AX + 36, AY - 48, 64, 46, 40, DARK, bevel=False)                          # hip
TO = prism(AX - 4, AY - 88, 160, 116, 150, STEEL, top=2, left=1, right=0)      # torso
# chest core: amber diamond plate inset on the lit face
cx_, cy_ = on_left(TO, 0.5, 0.52)
fill([(cx_ - 30, cy_ - 2), (cx_ + 4, cy_ - 34), (cx_ + 30, cy_ - 4), (cx_ - 4, cy_ + 28)], AMBER[0])
fill([(cx_ - 26, cy_ - 4), (cx_ + 3, cy_ - 30), (cx_ + 3, cy_ - 2)], AMBER[3])
fill([(cx_ + 3, cy_ - 30), (cx_ + 26, cy_ - 4), (cx_ + 3, cy_ - 2)], AMBER[2])
fill([(cx_ - 26, cy_ - 4), (cx_ + 3, cy_ - 2), (cx_ - 3, cy_ + 24)], AMBER[1])
for v in (0.16, 0.86):                                       # vent slats
    a, b = on_left(TO, 0.12, v), on_left(TO, 0.88, v)
    fill([a, b, (b[0], b[1] - 5), (a[0], a[1] - 5)], STEEL[0])
# idle arm on the lit side, hanging
s0 = on_left(TO, 0.62, 0.86); s1 = (s0[0] - 26, s0[1] + 112)
limb(s0, s1, 26, STEEL); joint(*s0, 20)
fill([(s1[0] - 14, s1[1]), (s1[0] + 10, s1[1] + 2), (s1[0] - 4, s1[1] + 24)], DARK[1])
prism(AX + 44, AY - 238, 46, 40, 18, DARK, bevel=False)                         # neck
HD = prism(AX + 12, AY - 256, 120, 96, 84, STEEL, top=2, left=1, right=0)      # head
# visor: one band wrapping both visible faces (a sensor strip, not eyes)
VV = 0.5
a, b = on_left(HD, 0.08, VV), on_left(HD, 0.94, VV)
fill([a, b, (b[0], b[1] - 22), (a[0], a[1] - 22)], CYAN[1])
fill([a, b, (b[0], b[1] - 6), (a[0], a[1] - 6)], CYAN[3])
a, b = on_right(HD, 0.0, VV), on_right(HD, 0.9, VV)
fill([a, b, (b[0], b[1] - 22), (a[0], a[1] - 22)], CYAN[0])
# antenna mast + amber tip
top_c = ((HD['F'][0] + HD['B'][0]) / 2, (HD['F'][1] + HD['B'][1]) / 2 - HD['h'])
limb((top_c[0], top_c[1]), (top_c[0], top_c[1] - 62), 9, DARK)
gem(top_c[0], top_c[1] - 70, 12, AMBER, n=5, h=1.2)
# working arm from the shadow-side shoulder: up to the elbow, down to the card
SH = on_right(TO, 0.55, 0.8)
EL = (410, 690)
GR = (590, 744)
limb(SH, EL, 32, STEEL); limb(EL, GR, 26, STEEL)
joint(*SH, 26); joint(*EL, 22)

# ---- the note card: a faceted slab held over the open drawer --------------------------
cardq = [(594, 716), (700, 690), (716, 752), (610, 778)]
ctr = (sum(p[0] for p in cardq) / 4 - 8, sum(p[1] for p in cardq) / 4 - 6, 14)
for i in range(4):                                           # 4 shallow facets meeting off-centre
    p, qq = cardq[i], cardq[(i + 1) % 4]
    k = shade_idx(ctr, (p[0], p[1], 0), (qq[0], qq[1], 0), 4, 0.25)
    fill([ctr[:2], p, qq], CARD[max(1, k)])
fill([cardq[2], cardq[3], (cardq[3][0], cardq[3][1] + 7), (cardq[2][0], cardq[2][1] + 7)], CARD[0])   # thickness
for i in range(3):                                           # text lines parallel to the long edge
    t0 = 0.3 + i * 0.2; L = 0.62 if i < 2 else 0.38
    a = (cardq[0][0] + (cardq[3][0] - cardq[0][0]) * t0 + 30, cardq[0][1] + (cardq[3][1] - cardq[0][1]) * t0 - 7)
    b = (a[0] + (cardq[1][0] - cardq[0][0]) * L, a[1] + (cardq[1][1] - cardq[0][1]) * L)
    fill([a, b, (b[0], b[1] + 5), (a[0], a[1] + 5)], CARD[0])
fill([(604, 722), (624, 717), (628, 732), (608, 737)], AMBER[1])     # amber tab = the new note
# gripper: two claws closing on the card's left edge
fill([(GR[0] - 16, GR[1] - 30), (GR[0] + 22, GR[1] - 34), (GR[0] + 6, GR[1] - 10)], DARK[2])
fill([(GR[0] - 16, GR[1] + 14), (GR[0] + 26, GR[1] + 22), (GR[0] + 8, GR[1] + 2)], DARK[0])
# drop guide: three shrinking shards from the card into the drawer
for i, (x, y) in enumerate([(672, 792), (668, 812), (664, 828)]):
    s_ = 10 - i * 3
    fill([(x - s_, y - s_ * 0.6), (x + s_, y - s_ * 0.6), (x, y + s_)], AMBER[2 - (i > 1)])

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
    for k in range(extrude, 0, -1):                          # solid extrusion in the shadow step
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
fb = ImageFont.truetype(HEI, 300 * S)
faceted_text((58, 196), "61%", fb, AMBER, cell=46, extrude=12, lo=1, hi=3)

img = img.resize((W, H), Image.LANCZOS)
img.save(OUT)
print(OUT)
