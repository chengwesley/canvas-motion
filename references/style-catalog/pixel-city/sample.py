"""pixel-city sample: tech-city frame. Reuses drawing code of components_base.py / components_tech.py.
Subject: robot agent places a note card into the wiki tower; big 61%; heading. 180x225 art px x6 = 1080x1350."""
import os, math
D = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(D, 'components_tech.py')).read()
src = src[:src.index('tail = tail.replace')].replace('__DIR__/components.py', os.path.join(D, 'components_base.py'))
exec(src)   # helpers, palettes (MET/GLS/ORG/PLZ...), C, tower, robot, note, ITEMS

AW, AH, S = 180, 225, 6
big = C(AW, AH, bg=PLZ[2]); plaza(big, True)

# calm bottom ~22%: plain two-tone plaza, no grid / glow dots
CALM_Y = 176
for y in range(CALM_Y, AH):
    for x in range(AW):
        t = .45 + .35 * (y - CALM_Y) / (AH - CALM_Y) + noise(x, y) * .1
        big.put(x, y, PLZ[3] if dth(x, y, t) else PLZ[2])
for x in range(AW): big.put(x, CALM_Y - 1, PLZ[1])

# light-rail road with cyan guide lights
RY0, RY1 = 108, 124
for y in range(RY0, RY1 + 1):
    for x in range(AW):
        big.put(x, y, ROAD[1] if dth(x, y, .5 + noise(x, y) * .3) else ROAD[0])
for x in range(AW):
    big.put(x, RY0 - 1, OUT); big.put(x, RY1 + 1, OUT)
    big.put(x, RY0 + 2, GLS[2] if x % 8 < 5 else GLS[1]); big.put(x, RY1 - 2, GLS[2] if x % 8 < 5 else GLS[1])
    if x % 12 < 6: big.put(x, (RY0 + RY1) // 2, PLZ[3])

def stamp(label_or_fn, ox, oy):
    """Draw a 56x56 sprite on a plaza tile, paste only pixels that differ from the pristine tile."""
    fn = label_or_fn if callable(label_or_fn) else [f for l, s, f in ITEMS if l == label_or_fn][0]
    sp = fn(); ref = P()
    for y in range(T):
        for x in range(T):
            if sp.p[x, y] != ref.p[x, y]: big.put(ox + x, oy + y, sp.p[x, y])

# small decoration (drawn first so the main subjects overlap)
stamp('全像樹', 140, 118 - 6 + 0) if False else None
stamp('全像樹', 124, -6)
stamp('感測燈柱', 76, -2)
# knowledge base: wiki tower, right side
stamp('③ wiki 塔', 112, 50)
# robot agent (active), standing on the road
def rb():
    c = P(); robot(c, 28, 28, 'active'); return c
stamp(rb, 14, 70)

# note card in flight with a cyan dotted trail to the tower door
TX, TY = 139, 99          # tower door, art px
NX, NY = 62, 74           # note position (top-left)
for k in range(26):
    t = k / 25; x = 70 + (TX - 70) * t; y = 82 + (TY - 82) * t - math.sin(t * math.pi) * 20
    if k % 2 == 0: big.rect(int(x), int(y), int(x) + 1, int(y) + 1, ORG[2] if k % 4 else WHITE)
tshadow(big, NX + 7, NY + 26, 9, 3)
note(big, NX, NY, 'plain', 13, 17)
big.rect(NX + 3, NY + 3, NX + 4, NY + 3, ORG[2])
big.sparkle(NX - 3, NY - 2, GLS[2]); big.sparkle(NX + 17, NY + 20, ORG[2])
# glowing slot at the door
for dy in range(-3, 4): big.put(TX - 4, TY - 6 + dy, GLS[3])
big.rect(TX - 3, TY - 3, TX + 3, TY - 2, ORG[2]); big.sparkle(TX + 6, TY - 8, ORG[2])

# result card behind the big number
CX0, CY0, CX1, CY1 = 12, 134, 104, 170
big.rect(CX0 - 1, CY0 + 3, CX1 + 1, CY1 + 4, SH[1])
big.box(CX0, CY0, CX1, CY1, PAPER[2], WHITE, PAPER[1])
big.rect(CX0, CY0, CX1, CY0 + 1, GLS[2])

out = big.im.resize((AW * S, AH * S), Image.NEAREST)
d = ImageDraw.Draw(out)
ZH = '/System/Library/Fonts/STHeiti Medium.ttc'; MONO = '/System/Library/Fonts/Menlo.ttc'
def txt(xy, s, font, fill, sh=None, off=6):
    if sh: d.text((xy[0] + off, xy[1] + off), s, fill=sh, font=font)
    d.text(xy, s, fill=fill, font=font)
# heading (top-left)
f = ImageFont.truetype(ZH, 104)
txt((54, 54), '知識庫', f, rgb('23203a'), sh=GLS[2], off=5)
# big number
fm = ImageFont.truetype(MONO, 210, index=1)
bb = d.textbbox((0, 0), '61%', font=fm); w = bb[2] - bb[0]; h = bb[3] - bb[1]
cx = (CX0 + CX1) / 2 * S; cy = (CY0 + CY1) / 2 * S
txt((cx - w / 2 - bb[0], cy - h / 2 - bb[1] + 4), '61%', fm, GRN[1], sh=GRN[0], off=6)
out.save(os.path.join(D, 'sample.png'))
print('ok', out.size)
