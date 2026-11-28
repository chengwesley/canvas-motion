#!/usr/bin/env python3
"""isometric style sample (original artwork). Renders sample.png next to this file.

Canonical isometric-illustration technique encoded below:
  iso()        true isometric projection: x axis -> lower-right at 30 deg, y axis -> lower-left
               at 30 deg, z straight up. One unit = U px. Every edge is parallel to one of the
               three axes; no perspective, no foreshortening differences.
  box()        every solid = 3 visible faces with FIXED tone roles from a 4-step ramp:
               top = light (ramp[2]), +y face (screen-left) = base (ramp[1]),
               +x face (screen-right) = shade (ramp[0]); ramp[3] = 1px edge light on the
               two front top edges. Light comes from the upper-left, so these roles never change.
  face_y/x()   details (drawers, panels, visor) are flat insets lying ON a face plane,
               drawn in that face's ramp shifted one step.
  cast()       flat hard cast shadow: hull of the footprint and the footprint pushed +x,
               one flat colour (platform top one step down). No blur on objects.
  Painter's order: draw back to front (small x+y first), floor -> shadows -> solids.
No outlines. Palette: 4-step ramps (shade, base, light, edge) for 7 materials.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

W, H, S = 1080, 1350, 2
HERE = os.path.dirname(os.path.abspath(__file__))
HEI = '/System/Library/Fonts/STHeiti Medium.ttc'
HIRA = '/System/Library/Fonts/Hiragino Sans GB.ttc'


def rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(*hx): return [rgb(h) for h in hx]       # [shade(+x face), base(+y face), light(top), edge]


BG = rgb('EEF1F6')
INK = rgb('24304F')
PLAT = ramp('B7C0D3', 'D8DEEA', 'F8F9FC', 'FFFFFF')
PLAT_SH = rgb('E3E7F0')                           # cast shadow on platform = top one step down
GRID = rgb('ECEFF5')
NAVY = ramp('27365F', '3B4E86', '5A6FA8', '8EA2D6')
NAVY_IN = ramp('1E2A4C', '33457A', '4A5E96', '7C90C6')   # drawer fronts: one step under NAVY
WHITE = ramp('C3CADB', 'E2E7F0', 'FFFFFF', 'FFFFFF')
DARK = ramp('2A3045', '3B435C', '56607D', '7B87A8')
CORAL = ramp('C9503A', 'F26B4F', 'FF9C80', 'FFC7B5')
TEAL = ramp('23887C', '36B3A3', '7DE0D2', 'C8F5EE')
SUN = ramp('C98F1F', 'F5B83D', 'FFD978', 'FFF0C2')
CARD = ramp('D6CDB4', 'EDE6D2', 'FFFDF6', 'FFFFFF')

U = 62 * S
OX, OY = (562 - 0.866 * 62) * S, 440 * S
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))


def iso(x, y, z=0):
    return (OX + (x - y) * C30 * U, OY + (x + y) * S30 * U - z * U)


img = Image.new('RGB', (W * S, H * S), BG)
d = ImageDraw.Draw(img)


def poly(pts, col): d.polygon([iso(*p) for p in pts], fill=col)


def box(x, y, z, w, dp, h, r, edge=True, top=True):
    a, b, c = x + w, y + dp, z + h
    poly([(x, b, z), (a, b, z), (a, b, c), (x, b, c)], r[1])          # +y face (left on screen)
    poly([(a, y, z), (a, b, z), (a, b, c), (a, y, c)], r[0])          # +x face (right on screen)
    if top: poly([(x, y, c), (a, y, c), (a, b, c), (x, b, c)], r[2])
    if edge:                                                          # edge light on front top edges
        d.line([iso(x, b, c), iso(a, b, c), iso(a, y, c)], fill=r[3], width=int(1.2 * S))


def face_y(y, x0, x1, z0, z1, col): poly([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], col)
def face_x(x, y0, y1, z0, z1, col): poly([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], col)
def top_rect(z, x0, x1, y0, y1, col): poly([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], col)


def hull(pts):
    pts = sorted(set(pts))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and (out[-1][0] - out[-2][0]) * (p[1] - out[-2][1]) - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0]) <= 0:
                out.pop()
            out.append(p)
        return out
    lo, hi = half(pts), half(pts[::-1]); return lo[:-1] + hi[:-1]


SHM = Image.new('L', (W * S, H * S), 0)


def cast(x, y, w, dp, h, z=0, k=.62):
    """hard flat shadow: light from upper-left -> shadow slides along +x by k*h.
    Collected in one mask and clipped to the platform top, so it never hangs in the air."""
    foot = [(x, y), (x + w, y), (x + w, y + dp), (x, y + dp)]
    sh = [(px + h * k, py - h * .12) for px, py in foot]
    ImageDraw.Draw(SHM).polygon(hull([iso(px, py, z) for px, py in foot + sh]), fill=255)


# ---------------------------------------------------------------- floor
PX, PY, PH = 9, 7, .5
m = Image.new('L', img.size, 0)
ImageDraw.Draw(m).polygon([iso(0, 0, -PH), iso(PX, 0, -PH), iso(PX, PY, -PH), iso(0, PY, -PH)], fill=70)
img.paste(rgb('C5CCDC'), (int(26 * S), int(30 * S)), m.filter(ImageFilter.GaussianBlur(22 * S)))
d = ImageDraw.Draw(img)
box(0, 0, -PH, PX, PY, PH, PLAT)
for i in range(1, PX):
    d.line([iso(i, 0), iso(i, PY)], fill=GRID, width=int(1.5 * S))
for j in range(1, PY):
    d.line([iso(0, j), iso(PX, j)], fill=GRID, width=int(1.5 * S))

# geometry of the scene (units)
CX0, CX1, CY0, CY1, CH = 3.3, 8.3, .4, 2.3, 4.4           # cabinet = knowledge base
COLS, ROWS = 2, 3
cw, rh = (CX1 - CX0 - .3) / COLS, (CH - .5) / ROWS
DC, DR = 0, 0                                               # the pulled-out drawer (col, row)
dx0 = CX0 + .15 + DC * cw + .07; dx1 = dx0 + cw - .14
dz0 = .25 + DR * rh + .06; dz1 = dz0 + rh - .12
DPULL = 1.35
RX, RY = 1.0, 3.9                                           # robot footprint origin

# ---------------------------------------------------------------- cast shadows (all first)
cast(CX0, CY0, CX1 - CX0, CY1 - CY0, CH)
cast(dx0, CY1, dx1 - dx0, DPULL, dz1)
cast(RX, RY, 1.9, 1.6, 4.2)
cast(.5, 5.6, 1.1, .8, .5)
cast(7.4, 4.6, .9, .9, 1.0)
clip = Image.new('L', SHM.size, 0)
ImageDraw.Draw(clip).polygon([iso(0, 0), iso(PX, 0), iso(PX, PY), iso(0, PY)], fill=255)
from PIL import ImageChops
img.paste(PLAT_SH, (0, 0), ImageChops.multiply(SHM, clip))
d = ImageDraw.Draw(img)

# ---------------------------------------------------------------- knowledge base cabinet
box(CX0, CY0, 0, CX1 - CX0, CY1 - CY0, .2, DARK)                       # plinth
box(CX0, CY0, .2, CX1 - CX0, CY1 - CY0, CH - .2, NAVY)
box(CX0 - .1, CY0 - .1, CH, CX1 - CX0 + .2, CY1 - CY0 + .2, .22, NAVY)  # cap
tabs = [CORAL, SUN, TEAL, WHITE]
for r in range(ROWS):
    for c in range(COLS):
        x0 = CX0 + .15 + c * cw + .07; x1 = x0 + cw - .14
        z0 = .25 + r * rh + .06; z1 = z0 + rh - .12
        if (c, r) == (DC, DR):
            face_y(CY1 + .001, x0, x1, z0, z1, NAVY_IN[0])               # empty dark slot
            continue
        face_y(CY1 + .001, x0, x1, z0, z1, NAVY_IN[1])
        face_y(CY1 + .002, x0, x1, z1 - .07, z1, NAVY_IN[2])           # bevel light on top lip
        lab = tabs[(r * 3 + c) % 4]
        face_y(CY1 + .003, x0 + cw * .3, x1 - cw * .3, z0 + rh * .5, z0 + rh * .66, lab[1])
        face_y(CY1 + .003, x0 + cw * .38, x1 - cw * .38, z0 + rh * .2, z0 + rh * .3, NAVY_IN[0])
# fill gauge on the +x face = the number as a physical quantity (61%)
gz0, gz1 = .6, CH - .5
face_x(CX1 + .001, CY0 + .75, CY0 + 1.25, gz0, gz1, NAVY_IN[0])
face_x(CX1 + .002, CY0 + .75, CY0 + 1.25, gz0, gz0 + (gz1 - gz0) * .61, TEAL[1])
face_x(CX1 + .003, CY0 + .75, CY0 + 1.25, gz0 + (gz1 - gz0) * .61 - .08, gz0 + (gz1 - gz0) * .61, TEAL[3])
for k in range(1, 4):
    zz = gz0 + (gz1 - gz0) * k / 4
    face_x(CX1 + .004, CY0 + 1.25, CY0 + 1.45, zz - .03, zz + .03, NAVY[3])
# status lights on cap front
for k, rr in enumerate((TEAL, TEAL, SUN)):
    face_y(CY1 + .101, CX1 - .5 - k * .32, CX1 - .3 - k * .32, CH + .06, CH + .16, rr[2])

# pulled drawer: open-top tray with filed cards standing upright
box(dx0, CY1, dz0, dx1 - dx0, DPULL, dz1 - dz0, NAVY_IN, top=False)
top_rect(dz1, dx0, dx1, CY1, CY1 + DPULL, NAVY_IN[2])                    # rim
top_rect(dz1, dx0 + .08, dx1 - .08, CY1, CY1 + DPULL - .08, NAVY_IN[0])  # cavity
face_x(dx0 + .08, CY1, CY1 + DPULL - .08, dz1 - .32, dz1, NAVY_IN[1])    # inner wall catches light
GAP = 2                                                                    # empty slot index
slots = [CY1 + .14 + k * .19 for k in range(6)]
for k, sy in enumerate(slots):
    if k == GAP:
        top_rect(dz1 - .02, dx0 + .1, dx1 - .1, sy - .06, sy + .1, TEAL[1])  # glowing target gap
        continue
    lab = tabs[k % 4]
    box(dx0 + .14, sy, dz1 - .3, dx1 - dx0 - .28, .07, .42, CARD, edge=False)
    box(dx0 + .2 + (k % 3) * .22, sy, dz1 + .12, .26, .07, .1, lab, edge=False)

# the note card being filed: upright, hovering over the glowing gap
cy = slots[GAP]; ky0 = cy; cz0 = dz1 - .75      # lower third sinks into the tray, hidden by the drawer front
kx0, kx1, kz1 = dx0 + .1, dx1 - .1, cz0 + 1.3
box(kx0, ky0, cz0, kx1 - kx0, .08, kz1 - cz0, CARD)
face_y(ky0 + .081, kx0, kx0 + .45, kz1 - .22, kz1, CORAL[1])    # coral index tab
for i, lw in enumerate((.78, .56, .68)):
    zl = kz1 - .2 - i * .19
    face_y(ky0 + .082, kx0 + .48 if i == 0 else kx0 + .12, kx0 + .12 + (kx1 - kx0 - .24) * lw, zl - .035, zl + .035, rgb('B9C2D6'))

face_y(CY1 + DPULL, dx0, dx1, dz0, dz1, NAVY_IN[1])                      # drawer front
face_y(CY1 + DPULL + .001, dx0 + .3, dx1 - .3, dz0 + .3, dz0 + .42, CORAL[1])   # handle

# floor path: inbox tray -> robot -> drawer (the route of a note), pale teal tiles
for tx, ty in ((1.7, 5.6), (2.3, 5.0), (2.9, 4.4)):
    top_rect(.002, tx, tx + .42, ty, ty + .42, rgb('CDEFEA'))
# small inbox tray of unsorted cards behind the robot
box(.5, 5.6, 0, 1.1, .8, .22, DARK)
for k, lab in enumerate((CORAL, SUN, TEAL)):
    box(.58, 5.68, .22 + k * .09, .94, .64, .07, CARD, edge=False)
    face_y(6.321, .65 + k * .22, .85 + k * .22, .22 + k * .09, .29 + k * .09, lab[1])

# a small network node on the right, linked to the cabinet by a floor cable
d.line([iso(7.85, 2.3, .01), iso(7.85, 4.6, .01)], fill=NAVY[3], width=int(3 * S))
box(7.4, 4.6, 0, .9, .9, .7, NAVY)
box(7.55, 4.75, .7, .6, .6, .3, TEAL)

# ---------------------------------------------------------------- robot (machine, no face)
box(RX, RY, 0, 1.9, 1.6, .28, DARK)                                       # tread base
for k in range(4):                                                         # tread grooves (+y face)
    face_y(RY + 1.601, RX + .15 + k * .45, RX + .35 + k * .45, .05, .23, DARK[0])
box(RX + .2, RY + .2, .28, 1.5, 1.2, .25, DARK)                           # hip
box(RX + .15, RY + .15, .53, 1.6, 1.3, 1.65, WHITE)                       # torso
face_y(RY + 1.451, RX + .15, RX + 1.75, .9, 1.05, CORAL[1])               # body stripe (left face)
face_x(RX + 1.751, RY + .15, RY + 1.45, .9, 1.05, CORAL[0])               # stripe continues (+x)
face_x(RX + 1.752, RY + .35, RY + 1.0, 1.25, 1.95, DARK[1])               # chest panel faces the drawer
for k, rr in enumerate((TEAL, SUN, CORAL)):
    face_x(RX + 1.753, RY + .45 + k * .18, RY + .58 + k * .18, 1.55, 1.75, rr[2])
face_x(RX + 1.753, RY + .45, RY + .9, 1.33, 1.4, TEAL[1])
# back arm hanging on the visible left side
box(RX + .5, RY + 1.45, 1.75, .6, .34, .35, DARK)                       # shoulder cap
box(RX + .55, RY + 1.45, 1.1, .5, .32, .65, WHITE)
box(RX + .52, RY + 1.45, .85, .56, .36, .28, DARK)
box(RX + .55, RY + .55, 2.18, .9, .7, .2, DARK)                           # neck
box(RX + .25, RY + .3, 2.38, 1.4, 1.1, .95, WHITE)                        # head block
face_x(RX + 1.651, RY + .42, RY + 1.28, 2.72, 2.95, DARK[1])              # visor slit faces +x
face_x(RX + 1.652, RY + .52, RY + .95, 2.79, 2.88, TEAL[2])               # sensor light
face_y(RY + 1.401, RX + 1.25, RX + 1.65, 2.72, 2.95, DARK[1])             # visor wraps the corner
box(RX + .55, RY + .55, 3.33, .12, .12, .55, DARK, edge=False)           # antenna
box(RX + .5, RY + .5, 3.85, .22, .22, .22, CORAL)

# reaching arm (every segment axis-aligned): shoulder -> upper arm along +x -> forearm along -y
# passing beside the drawer -> wrist column rising next to the card -> finger pinching its edge.
# Nothing passes in front of the card's face, so the card stays the clearest shape in the frame.
AY0, AY1 = RY + .55, RY + .95
AZ0 = dz1 + .12                                                            # arm height: just above the drawer rim
EX0 = kx1 + .1                                                             # wrist column sits right of the card
box(RX + 1.75, AY0 - .05, AZ0 - .1, .3, .5, .5, DARK)                     # shoulder joint
box(RX + 2.05, AY0, AZ0, EX0 - RX - 2.05, AY1 - AY0, .3, WHITE)          # upper arm (+x)
box(EX0, ky0 + .3, AZ0, .4, AY0 - ky0 - .3, .3, WHITE)                    # forearm (-y)
box(EX0 - .05, AY0 - .05, AZ0 - .1, .5, .5, .5, DARK)                     # elbow joint
box(EX0, ky0 - .12, AZ0 - .05, .4, .42, kz1 - .25 - AZ0 + .05, WHITE)     # wrist column (up)
box(EX0 - .04, ky0 - .16, kz1 - .4, .48, .5, .3, DARK)                    # wrist joint
box(kx1 - .25, ky0 - .06, kz1 - .34, EX0 - kx1 + .25, .06, .16, DARK, edge=False)   # finger behind
box(kx1 - .25, ky0 + .1, kz1 - .34, EX0 - kx1 + .25, .06, .16, DARK, edge=False)    # finger in front
img = img.resize((W, H), Image.LANCZOS)
d = ImageDraw.Draw(img)

# ---------------------------------------------------------------- typography
d.rectangle([76, 66, 140, 74], fill=CORAL[1])
d.text((72, 92), '知識庫', font=ImageFont.truetype(HEI, 76), fill=INK)
d.text((64, 170), '61%', font=ImageFont.truetype(HIRA, 176, index=2), fill=CORAL[1])
img.save(os.path.join(HERE, 'sample.png'))
