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
# robot agent (active), standing on the road
def rb():
    c = P(); robot(c, 28, 28, 'active'); return c
stamp(rb, 14, 70)

# note card: bigger (16x22) so the metaphor reads at icon size (Kare); a dog-ear says "document"
NW, NH = 16, 22
NX, NY = 115, 78
# clean dotted trail: 2x2 blocks on an even 4px pitch, ending at the card (no stray single pixels)
for k in range(11):
    t = k / 10; x = 62 + (NX - 6 - 62) * t; y = 90 + (NY + 8 - 90) * t - math.sin(t * math.pi) * 14
    big.rect(int(x), int(y), int(x) + 1, int(y) + 1, ORG[2] if k % 2 == 0 else WHITE)
tshadow(big, NX + 6, NY + NH + 2, 9, 3)
ear = {(NX - 1 + i, NY - 1 + j): big.p[NX - 1 + i, NY - 1 + j] for i in range(4) for j in range(4)}
note(big, NX, NY, 'plain', NW, NH)
for (px, py), col in ear.items():
    i, j = px - (NX - 1), py - (NY - 1)
    if i + j < 3: big.put(px, py, col)                  # corner cut away
    elif i + j == 3: big.put(px, py, OUT)               # fold line
    elif i < 3 and j < 3: big.put(px, py, PAPER[1])     # folded flap
big.rect(NX + 3, NY + NH - 5, NX + 6, NY + NH - 4, ORG[2])   # orange tab: the one accent on the card

# knowledge base: wiki tower drawn AFTER the card, so its wall hides the card's right half (card is going in)
stamp('③ wiki 塔', 112, 50)
for dy in range(NH): big.put(123, NY + dy, GLS[3] if dy % 4 < 3 else GLS[2])   # glowing slot on the tower wall
big.rect(122, NY + 8, 123, NY + 9, ORG[2])

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
