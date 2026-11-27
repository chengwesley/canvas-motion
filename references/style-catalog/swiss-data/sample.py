"""swiss-data sample frame (International Typographic Style x Isotype-like unit chart).
Subject: an AI agent (pictogram robot) files note card #61 into the knowledge base; big number 61%.
Technique encoded as helpers:
  - Grid: 12 columns x 12px baseline; every x comes from col(), every y from bl()
  - Type: grotesk, flush-left / ragged-right, ink edge aligned to the column line,
          tight negative tracking on display sizes, open tracking on small caps labels
  - Colour: paper + ink + 2 greys + ONE accent; accent marks only the thing that changes (card + slot)
  - Chart is the hero: unit chart (1 cell = 1 note = 1%), filled row by row from the bottom, left to right
  - Agent: pictogram robot built only from rectangles, circles and thick strokes; sensor slit, no face
Self-contained: Python 3 + PIL. Writes sample.png (1080x1350) next to this file.
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H, S = 1080, 1350, 3            # S = supersample, drawn at 3x then LANCZOS down: crisp hairlines

# ---- palette (must match style.md) ---------------------------------------------------------
PAPER = (242, 240, 235)   # #F2F0EB  ground, warm off-white
TINT  = (222, 219, 211)   # #DEDBD3  empty unit / quiet fill
MID   = (138, 135, 128)   # #8A8780  hairlines, secondary labels
PULL  = (78, 77, 74)      # #4E4D4A  detail inside ink shapes (drawer pull, panel)
INK   = (20, 20, 20)      # #141414  type, data, machine
ACC   = (228, 50, 22)     # #E43216  THE accent (signal red)
ACC_D = (168, 32, 12)     # #A8200C  accent shadow edge (3px offset under the card only)

# ---- grid ----------------------------------------------------------------------------------
M, GUT, NCOL, BL = 72, 24, 12, 12          # margin, gutter, columns, baseline unit (px)
COLW = (W - 2 * M - (NCOL - 1) * GUT) / NCOL   # = 56
def col(i):            return M + i * (COLW + GUT)                  # left edge of column i
def col_r(i, span=1):  return col(i) + span * (COLW + GUT) - GUT    # right edge after span cols
def bl(n):             return n * BL                                # n baselines from top

# ---- fonts ---------------------------------------------------------------------------------
def font(cands, size):
    for p, idx in cands:
        try: return ImageFont.truetype(p, int(size * S), index=idx)
        except Exception: pass
    raise SystemExit('font missing: %r' % cands)
GROT_B = [('/System/Library/Fonts/HelveticaNeue.ttc', 1), ('/System/Library/Fonts/Helvetica.ttc', 1)]
GROT_M = [('/System/Library/Fonts/HelveticaNeue.ttc', 10), ('/System/Library/Fonts/Helvetica.ttc', 0)]
GROT_R = [('/System/Library/Fonts/HelveticaNeue.ttc', 0), ('/System/Library/Fonts/Helvetica.ttc', 0)]
HEI_M  = [('/System/Library/Fonts/STHeiti Medium.ttc', 0)]
HEI_L  = [('/System/Library/Fonts/Hiragino Sans GB.ttc', 0)]   # W3

im = Image.new('RGB', (W * S, H * S), PAPER)
d = ImageDraw.Draw(im)

def check_glyphs(s, f):
    """Fail loudly if any CJK char would render as the font's notdef (tofu) or as nothing."""
    def mask(ch):
        m = Image.new('L', (f.size * 2, f.size * 2), 0)
        ImageDraw.Draw(m).text((0, 0), ch, font=f, fill=255)
        return m.tobytes()
    notdef = mask('')
    for ch in s:
        if ord(ch) < 0x2E80: continue
        mk = mask(ch)
        if mk == notdef or not any(mk): raise SystemExit('missing glyph %r in %s' % (ch, f.path))

def rect(x0, y0, x1, y1, c, r=0):
    box = [round(x0 * S), round(y0 * S), round(x1 * S) - 1, round(y1 * S) - 1]
    if r: d.rounded_rectangle(box, radius=r * S, fill=c)
    else: d.rectangle(box, fill=c)
def hline(x0, x1, y, c=INK, w=1.0): rect(x0, y - w / 2, x1, y + w / 2, c)
def vline(x, y0, y1, c=INK, w=1.0): rect(x - w / 2, y0, x + w / 2, y1, c)
def disc(cx, cy, r, c): d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=c)
def stroke(p0, p1, w, c):           # thick limb with round caps (pictogram joint)
    d.line([(p0[0] * S, p0[1] * S), (p1[0] * S, p1[1] * S)], fill=c, width=int(w * S))
    disc(*p0, w / 2, c); disc(*p1, w / 2, c)
def tri(pts, c): d.polygon([(x * S, y * S) for x, y in pts], fill=c)

def text(x, y, s, f, c=INK, track=0.0, anchor='l'):
    """INK edge of the first glyph sits on x; cap/ideograph top sits on y. track in px.
    anchor 'r' = right aligned (tabular figures). Returns the right ink edge."""
    check_glyphs(s, f)
    top = d.textbbox((0, 0), 'H', font=f)[1]
    widths = [d.textlength(ch, font=f) / S for ch in s]
    total = sum(widths) + track * (len(s) - 1)
    lead = d.textbbox((0, 0), s[0], font=f)[0] / S
    cx = (x - lead) if anchor == 'l' else (x - total)
    for ch, w in zip(s, widths):
        d.text((cx * S, y * S - top), ch, font=f, fill=c)
        cx += w + track
    return cx - track

# =============================================================================================
# 1. Masthead: one heavy rule + metadata row (index, section, unit, figure no.) on columns
rect(M, bl(6), W - M, bl(6) + 8, INK)
small = font(GROT_M, 18)
text(col(0), bl(6) + 24, '03', small, INK, 1)
text(col(1), bl(6) + 24, 'KNOWLEDGE BASE', small, INK, 2.2)
text(col(6), bl(6) + 24, '1 CELL = 1 NOTE', small, MID, 2.2)
text(col_r(11), bl(6) + 24, 'Fig. 3', small, MID, 1, anchor='r')

# 2. The big number: Helvetica Neue Bold 360px, tracking -4.5% of size, ink edge on column 0
BIG = 360
NUM_TOP = bl(13)
r61 = text(col(0) - 2, NUM_TOP, '61', font(GROT_B, BIG), INK, track=-BIG * 0.045)
text(r61 - 14, NUM_TOP, '%', font(GROT_B, BIG * 0.42), INK)   # superior %: 42% size, cap-top aligned

# 3. Heading block on column 8, cap-top aligned with the number
text(col(8), NUM_TOP, '知識庫', font(HEI_M, 76), INK, track=2)
text(col(8), NUM_TOP + 112, '已歸檔', font(HEI_L, 22), MID, track=3)
text(col(8), NUM_TOP + 150, '61 / 100', font(GROT_M, 28), INK, track=0.5)
text(col(8), NUM_TOP + 196, 'NOTES FILED', font(GROT_M, 14), MID, track=2.2)

# 4. Section rule: statement (number) above, evidence (chart) below
hline(M, W - M, bl(37), INK, 2)

# =============================================================================================
# 5. HERO: unit chart = the knowledge base, columns 4-11. 10 x 10 cells, 1 cell = 1 note.
#    Filled row by row from the bottom, left to right, like reading order turned upside down:
#    60 filed = 6 solid rows; cell 61 is the leftmost cell of row 7, right next to the agent.
NX, NY = 10, 10
GX0, GX1 = col(4), col_r(11)
GY0, GY1 = bl(44), bl(84)
GAPX = GAPY = 6
CW = (GX1 - GX0 - (NX - 1) * GAPX) / NX
CH = (GY1 - GY0 - (NY - 1) * GAPY) / NY
def cell(cx, ry):          # ry = row from the bottom (0 = bottom shelf)
    x = GX0 + cx * (CW + GAPX); y = GY1 - (ry + 1) * CH - ry * GAPY
    return x, y, x + CW, y + CH
FILLED = 60
for k in range(NX * NY):
    x0, y0, x1, y1 = cell(k % NX, k // NX)
    if k < FILLED:
        rect(x0, y0, x1, y1, INK)
        rect(x0 + CW * 0.36, y0 + CH * 0.42, x1 - CW * 0.36, y0 + CH * 0.42 + 3, PULL)  # drawer pull
    elif k > FILLED:
        rect(x0, y0, x1, y1, TINT)
TX0, TY0, TX1, TY1 = cell(FILLED % NX, FILLED // NX)
rect(TX0, TY0, TX1, TY1, ACC); rect(TX0 + 3, TY0 + 3, TX1 - 3, TY1 - 3, PAPER)    # open slot

# axis: cumulative count hangs in the right margin, one tick per row; column index under the chart
lab = font(GROT_R, 15); labb = font(GROT_M, 15)
for r in range(NY):
    _, y0, _, y1 = cell(0, r)
    n = (r + 1) * NX
    hot = (n == FILLED)
    hline(GX1 + 6, GX1 + (16 if hot else 11), (y0 + y1) / 2, INK if hot else MID, 1.2)
    text(GX1 + 20, (y0 + y1) / 2 - 5.5, str(n), labb if hot else lab, INK if hot else MID)
for cx in range(NX):
    x0, _, x1, _ = cell(cx, 0)
    t = '%02d' % (cx + 1); tw = d.textlength(t, font=lab) / S
    text((x0 + x1) / 2 - tw / 2, GY1 + 14, t, lab, MID)

# floor: one hairline the agent and the chart share
hline(M, GX1, GY1 + 0.5, INK, 1.5)

# =============================================================================================
# 6. AGENT = pictogram robot (Isotype spirit): body parts are primitives, limbs are 18px strokes.
#    It stands on the floor in columns 0-3 and pushes the card sideways into cell 61.
RX = (col(0) + col_r(3)) / 2 - 10           # robot axis
# tread base
rect(RX - 92, GY1 - 54, RX + 92, GY1, INK, r=27)
for dx in (-58, 0, 58):
    disc(RX + dx, GY1 - 27, 15, PAPER); disc(RX + dx, GY1 - 27, 6, INK)
# mast
rect(RX - 18, GY1 - 116, RX + 18, GY1 - 54, INK)
rect(RX - 30, GY1 - 124, RX + 30, GY1 - 112, INK)
# torso with a status panel (three bars = working)
T0, T1 = GY1 - 270, GY1 - 124
rect(RX - 76, T0, RX + 76, T1, INK, r=10)
rect(RX - 52, T0 + 30, RX + 52, T0 + 96, PULL, r=4)
for i, (h, c) in enumerate(((0.9, PAPER), (0.6, PAPER), (0.35, MID))):
    bx = RX - 38 + i * 28
    rect(bx, T0 + 88 - 52 * h, bx + 16, T0 + 88, c)
rect(RX - 52, T0 + 112, RX - 8, T0 + 118, MID)
# neck + head with one horizontal sensor slit (a sensor, not eyes) + antenna
rect(RX - 15, T0 - 22, RX + 15, T0, INK)
HY0, HY1 = T0 - 116, T0 - 22
rect(RX - 62, HY0, RX + 62, HY1, INK, r=12)
rect(RX - 74, HY0 + 30, RX - 62, HY0 + 64, INK)          # side bolts
rect(RX + 62, HY0 + 30, RX + 74, HY0 + 64, INK)
rect(RX - 44, HY0 + 38, RX + 44, HY0 + 56, PAPER, r=9)    # sensor slit
rect(RX + 4, HY0 + 41, RX + 40, HY0 + 53, MID, r=6)       # scan beam sits in the slit, offset = looking right
vline(RX, HY0 - 40, HY0, INK, 5)
disc(RX, HY0 - 44, 9, INK)
# back arm hangs, gripper open
stroke((RX - 82, T0 + 20), (RX - 98, T0 + 96), 18, INK)
stroke((RX - 98, T0 + 96), (RX - 92, T0 + 150), 16, INK)
rect(RX - 106, T0 + 152, RX - 100, T0 + 172, INK); rect(RX - 84, T0 + 152, RX - 78, T0 + 172, INK)

# the note card (accent), already half inside the slot
CARD_W, CARD_H = CW + 4, CH + 2
CY = (TY0 + TY1) / 2
CARD_X0 = TX0 - CARD_W * 0.45
CARD_Y0 = CY - CARD_H / 2
# reaching arm: shoulder -> elbow -> wrist, ends in a two-jaw gripper on the card's left edge
SH = (RX + 82, T0 + 22)
EL = (RX + 126, CY + 34)
WR = (CARD_X0 - 22, CY)
stroke(SH, EL, 18, INK)
stroke(EL, WR, 16, INK)
rect(WR[0] - 4, CY - CARD_H / 2 - 9, WR[0] + 6, CY + CARD_H / 2 + 9, INK)          # gripper palm
rect(WR[0], CY - CARD_H / 2 - 9, CARD_X0 + 16, CY - CARD_H / 2 - 2, INK)           # upper jaw
rect(WR[0], CY + CARD_H / 2 + 2, CARD_X0 + 16, CY + CARD_H / 2 + 9, INK)           # lower jaw
rect(CARD_X0 + 3, CARD_Y0 + 3, CARD_X0 + CARD_W + 3, CARD_Y0 + CARD_H + 3, ACC_D)  # 3px offset edge
rect(CARD_X0, CARD_Y0, CARD_X0 + CARD_W, CARD_Y0 + CARD_H, ACC)
for i, frac in enumerate((0.72, 0.84, 0.5)):
    yy = CARD_Y0 + 9 + i * 8.5
    rect(CARD_X0 + 9, yy, CARD_X0 + 9 + (CARD_W - 18) * frac, yy + 3.5, PAPER)
# motion: three accent ticks in the slot direction, above the card (speed lines, not an arrow)
for i in range(3):
    xx = TX0 + 10 + i * 14
    rect(xx, CARD_Y0 - 22, xx + 8, CARD_Y0 - 18, ACC)
tri([(TX0 + 52, CARD_Y0 - 26), (TX0 + 52, CARD_Y0 - 14), (TX0 + 62, CARD_Y0 - 20)], ACC)

# 7. Labels: small caps grotesk with a 1px orthogonal leader; English only (no extra CJK)
cap = font(GROT_M, 15)
def label(ax, ay, lx, ly, s, c=INK):
    rx = text(lx, ly, s, cap, c, track=2.2)
    if ax > rx + 8:                       # label sits left of the anchor: L-shaped leader
        hline(rx + 8, ax, ly + 6, c, 1.2); vline(ax, ly + 6, ay, c, 1.2)
    else:
        vline(ax, min(ay, ly + 22), max(ay, ly + 22), c, 1.2)
    rect(ax - 3, ay - 3, ax + 3, ay + 3, c)
label(RX - 68, HY0 + 30, col(0), HY0 - 40, 'AGENT')
label(TX0 + 4, CARD_Y0 - 34, TX0 - 92, CARD_Y0 - 92, 'NOTE 61', ACC)

# =============================================================================================
# 8. Subtitle zone (bottom 22%, y > 1053): intentionally empty paper. Nothing to draw.

im.resize((W, H), Image.LANCZOS).save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.png'))
