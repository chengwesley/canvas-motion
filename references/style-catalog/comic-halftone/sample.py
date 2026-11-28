# Comic halftone sample page, composed from components.py.
# Subject: an AI agent pushes a note card INTO the knowledge-base shelf; big number 61%.
# Three-beat page: A carry (wide, dutch tilt) -> B insert (close-up, 3D) -> C result (burst).
import os, math, random
from components import *

W, H = 1080, 1350
P = Page(W, H)
G = 14  # gutter

# ---------- layout ----------
def a_bottom(x):  # slanted bottom edge of panel A
    return 600 - 46 * (x - 30) / 1020

A = [(30, 196), (1050, 196), (1050, a_bottom(1050)), (30, a_bottom(30))]
SPLIT = 600  # x where B and C meet (slanted divider)
B = [(30, a_bottom(30) + G), (SPLIT + 18, a_bottom(SPLIT + 18) + G), (SPLIT - 18, 1040), (30, 1040)]
C = [(SPLIT + 18 + G, a_bottom(SPLIT + 18 + G) + G), (1050, a_bottom(1050) + G), (1050, 1040), (SPLIT - 18 + G, 1040)]

# ---------- heading ----------
title_lettering(P, 34, 104, "知識庫", 128, stroke=6, extrude=(7, 8))
chapter_tag(P, 452, 82, "01", "歸檔", size=28)

# ---------- panel A: the agent carries the card toward the empty slot ----------
mA = panel(P, A)
P.tone(mA, "B", lambda x, y: 0.05 + 0.30 * max(0.0, (y - 196) / 400) ** 1.3)
speed_lines(P, mA, 30, 250, 300, 520, ang=-2.6, n=16, w=5, seed=8)
# shelf, low camera so it towers on the right; cropped by the panel border
camA = Cam(812, 392, f=980, yaw=-28, pitch=6, dist=1000, target=(190, 150, 30), roll=-2.6)
infoA = shelf3d(P, camA, W=380, Hr=84, D=70, rows=3, seed=31, gap=(1, 4, 48), card=False, clip=mA)
sx0, sy0, sx1, sy1 = infoA["slot"]
slot_c = camA((sx0 + sx1) / 2, (sy0 + sy1) / 2 + 6, 6)
# robot striding in, card held high in the gripper
o = robot(P, 268, 586, 1.42, "carrying")
hand = o["hand_f"]
card_c = (hand[0] + 58, hand[1] - 6)
note_card(P, card_c[0], card_c[1], 112, 74, angle=-12)
# intent arrow from card to slot, and a highlight burst ring around the empty slot
arrow(P, bezier([(card_c[0] + 64, card_c[1] - 34), ((card_c[0] + slot_c[0]) / 2, card_c[1] - 120),
                 (slot_c[0] - 4, slot_c[1] - 10)], 50), width=26, head=1.9, extrude=(4, 5))
# dashed "target" outline inside the empty slot (where the card will go)
q = [camA(sx0 + 6, sy0 + 6, 2), camA(sx1 - 6, sy0 + 6, 2), camA(sx1 - 6, sy0 + 70, 2), camA(sx0 + 6, sy0 + 70, 2)]
for i in range(4):
    a_, b_ = q[i], q[(i + 1) % 4]
    for t in range(0, 10, 2):
        p0, p1 = lerp(a_, b_, t / 10), lerp(a_, b_, (t + 1.2) / 10)
        P.fill(P._strip([p0, p1], [4.5, 4.5], False), YELLOW)
sparkle(P, q[1][0] + 6, q[1][1] - 6, 16, w=3.5)
panel_border(P, A, 5)

# ---------- panel B: close-up, the card slides INTO the slot ----------
mB = panel(P, B)
P.tone(mB, "B", 0.5)
QUIET = [BLUE, YELLOW, BLUE, BLUE, YELLOW, RED]
books = make_books(3, 420, 41, (1, 7, 32), cols=QUIET)
gb = [b for b in books[1] if b["gap"]][0]
gx = gb["x"] + gb["w"] / 2
Hr, board = 104, 12
yb = 1 * (Hr + board) + board
camB = Cam(340, 838, f=1300, yaw=-40, pitch=-12, dist=430, target=(gx, yb + Hr * 0.42, -30), roll=-3)
infoB = shelf3d(P, camB, W=420, Hr=Hr, D=90, rows=3, seed=41, gap=(1, 7, 32), card_in=0.52, clip=mB, lw=6, cols=QUIET)
z_out, z_in = infoB["card_z"]
cy0, ch = infoB["card_y"] + 2, infoB["card_h"]
edge_mid = camB(gx, cy0 + ch * 0.5, z_out)
ahead = camB(gx, cy0 + ch * 0.5, z_out + 30)
ux, uy = ahead[0] - edge_mid[0], ahead[1] - edge_mid[1]
ul = math.hypot(ux, uy); ux, uy = ux / ul, uy / ul
# push arrow lines (motion behind the hand, aimed along the push direction)
nx, ny = -uy, ux
rng = random.Random(3)
for i in range(9):
    off = (i - 4) * 15 + rng.uniform(-4, 4)
    L0 = rng.uniform(150, 260)
    st = 70 + rng.uniform(0, 30)
    p0 = (edge_mid[0] - ux * (st + L0) + nx * off, edge_mid[1] - uy * (st + L0) + ny * off)
    p1 = (edge_mid[0] - ux * st + nx * off, edge_mid[1] - uy * st + ny * off)
    P.stroke([p0, p1], rng.uniform(6, 10), taper=(0.9, 0.06), wmin=0.03, clip=mB)
palm = (edge_mid[0] - ux * 22, edge_mid[1] - uy * 22)
elbow = (palm[0] - ux * 190 + nx * 30, palm[1] - uy * 190 + ny * 30)
limb_arm(P, elbow, palm, s=2.3)
# slot-mouth impact ticks
bx_, by_ = 175, a_bottom(175) + 88
burst(P, bx_, by_, 128, seed=19, n=18, layers=(WHITE, WHITE), ry=74, w=5)
sfx(P, "CLICK!", bx_, by_ + 2, 60, angle=-9, extrude=(4, 5), stroke=5, spacing=1.06)
panel_border(P, B, 5)

# ---------- panel C: result ----------
mC = panel(P, C)
P.tone(mC, "Y", 0.22)
ccx, ccy = 832, 818
focus_lines(P, mC, ccx, ccy, 150, n=120, w=8, seed=12)
panel_border(P, C, 5)
burst_number(P, ccx, ccy - 6, 212, "61", "%", size=150, seed=5, ry=196)

# ---------- calm footer (bottom ~22%) ----------
P.line([(30, 1088), (1050, 1088)], 3)
P.text((540, 1196), "一張筆記，推進知識庫", P.font(FONT_CJK, 42))

bad = check_glyphs("".join(CJK_USED))
print("missing glyphs:", bad)
P.render().save(os.path.join(HERE, "sample.png"))
print("ok")
