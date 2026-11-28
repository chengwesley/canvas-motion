"""glass-ui sample frame (glassmorphism: frosted translucent UI layers over blurred colour light).
Subject: a floating glass robot slides note card #61 into a knowledge-base panel; widget shows 61%.
Technique encoded as helpers:
  - Light field: vertical base gradient + 4 colour blobs drawn at 1/4 size, blurred, upscaled
  - glass(): drop shadow -> backdrop blur of what is already behind -> white veil -> top sheen
             -> 1.5px rim lit from top-left (bright) to bottom-right (faint). Order matters.
  - Depth = blur radius + veil opacity: far layers blur less and are more transparent,
            the foreground card is the most opaque
  - One accent gradient (violet) for progress / selection; one status light (cyan) for the machine
  - Agent: robot made of glass parts (head, visor with scan light, torso, arm tubes), hovers; no face
Deterministic, PIL only. Writes sample.png (1080x1350) next to this file.
"""
import os, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, SS = 1080, 1350, 4          # SS = supersample factor for anti-aliased masks
HERE = os.path.dirname(os.path.abspath(__file__))

# ---- palette (must match style.md) ---------------------------------------------------------
BG_TOP  = (76, 62, 176)     # #4C3EB0  deep violet sky (top)
BG_MID  = (184, 168, 236)   # #B8A8EC  lavender
BG_BOT  = (243, 238, 248)   # #F3EEF8  calm bottom (subtitle zone)
BLOB_V  = (139, 123, 255)   # #8B7BFF  violet light
BLOB_P  = (255, 143, 184)   # #FF8FB8  pink light
BLOB_C  = (94, 214, 230)    # #5ED6E6  cyan light
BLOB_O  = (255, 197, 158)   # #FFC59E  peach light
INK     = (30, 27, 75)      # #1E1B4B  text, visor
INK2    = (74, 70, 128)     # #4A4680  secondary text, list lines
ACC_A   = (108, 92, 231)    # #6C5CE7  accent gradient start
ACC_B   = (167, 139, 250)   # #A78BFA  accent gradient end
LIGHT   = (125, 249, 255)   # #7DF9FF  machine status light (visor scan, antenna, thruster)
WHITE   = (255, 255, 255)

# ---- fonts ---------------------------------------------------------------------------------
def sf(size, weight=b'Semibold'):
    f = ImageFont.truetype('/System/Library/Fonts/SFNS.ttf', size)
    f.set_variation_by_name(weight); return f
def hei(size, w6=True):
    return ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', size, index=2 if w6 else 0)

def check_glyphs(s, f):
    """Fail if any CJK char renders as notdef (tofu) or blank."""
    def mask(ch):
        m = Image.new('L', (f.size * 2, f.size * 2), 0)
        ImageDraw.Draw(m).text((0, 0), ch, font=f, fill=255); return m.tobytes()
    nd = mask('')
    for ch in s:
        if ord(ch) >= 0x2E80 and (mask(ch) == nd or not any(mask(ch))):
            raise SystemExit('missing glyph %r' % ch)

# ---- light field ---------------------------------------------------------------------------
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def background():
    bg = Image.new('RGB', (W, H)); d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        c = lerp(BG_TOP, BG_MID, t / 0.55) if t < 0.55 else lerp(BG_MID, BG_BOT, min(1, (t - 0.55) / 0.25))
        d.line([(0, y), (W, y)], fill=c)
    q = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0)); qd = ImageDraw.Draw(q)
    for x, y, r, c, a in [(40, 60, 80, BLOB_V, 235), (250, 110, 70, BLOB_P, 220),
                          (60, 200, 60, BLOB_C, 200), (240, 235, 55, BLOB_O, 190)]:
        qd.ellipse([x - r, y - r, x + r, y + r], fill=c + (a,))
    q = q.filter(ImageFilter.GaussianBlur(30)).resize((W, H), Image.BICUBIC)
    bg = Image.alpha_composite(bg.convert('RGBA'), q)
    # calm bottom 22%: fade everything back to BG_BOT
    fade = Image.new('L', (1, H), 0)
    for y in range(H):
        fade.putpixel((0, y), int(255 * max(0, min(1, (y - 0.70 * H) / (0.12 * H)))))
    return Image.composite(Image.new('RGBA', (W, H), BG_BOT + (255,)), bg, fade.resize((W, H)))

def grain(im, amt=6):
    """Deterministic film grain (+-amt) from a seeded 128px tile; keeps glass from looking plastic."""
    rnd = random.Random(11)
    tile = Image.new('L', (128, 128)); tile.putdata([128 + rnd.randint(-amt, amt) for _ in range(128 * 128)])
    n = Image.new('L', (W, H))
    for x in range(0, W, 128):
        for y in range(0, H, 128): n.paste(tile, (x, y))
    n = Image.merge('RGB', (n, n, n))
    return ImageChops.add(im.convert('RGB'), n, 1, -128).convert('RGBA')

# ---- masks (drawn at SS x, downsampled = anti-aliased) ------------------------------------
def mask_from(draw_fn):
    m = Image.new('L', (W * SS, H * SS), 0); draw_fn(ImageDraw.Draw(m), SS)
    return m.resize((W, H), Image.LANCZOS)
def rr(box, r):
    return mask_from(lambda d, s: d.rounded_rectangle([v * s for v in box], radius=r * s, fill=255))
def tube(pts, w):
    def f(d, s):
        d.line([(x * s, y * s) for x, y in pts], fill=255, width=int(w * s), joint='curve')
        for x, y in (pts[0], pts[-1]): d.ellipse([(x - w / 2) * s, (y - w / 2) * s, (x + w / 2) * s, (y + w / 2) * s], fill=255)
    return mask_from(f)

def gradient_rim(mask, hi=0.8, lo=0.18, width=2):
    """Inner rim of a mask; alpha falls from top-left (hi) to bottom-right (lo)."""
    inner = mask.filter(ImageFilter.MinFilter(width * 2 + 1))
    rim = ImageChops.subtract(mask, inner)
    x0, y0, x1, y1 = mask.getbbox()
    v = Image.linear_gradient('L').resize((x1 - x0, y1 - y0))                         # 0 top -> 255 bottom
    h = Image.linear_gradient('L').transpose(Image.TRANSPOSE).resize((x1 - x0, y1 - y0))  # 0 left -> 255 right
    g = ImageChops.add(v, h, scale=2)                                                   # diagonal, no empty corners
    full = Image.new('L', (W, H), 0)
    full.paste(g.point(lambda v: int(255 * (hi - (hi - lo) * v / 255))), (x0, y0))
    return ImageChops.multiply(rim, full)

def glass(scene, mask, blur=22, veil=0.20, sheen=0.28, shadow=0.22, lift=18, tint=WHITE):
    """Frosted glass over whatever is already in `scene`."""
    x0, y0, x1, y1 = mask.getbbox()
    if shadow:                                                    # 1. soft drop shadow
        sh = Image.new('L', (W, H), 0); sh.paste(mask, (0, lift))
        sh = sh.filter(ImageFilter.GaussianBlur(lift * 1.6)).point(lambda v: int(v * shadow))
        scene.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), INK).split(), sh)))
    pad = blur * 3                                                # 2. backdrop blur
    bx = (max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad))
    blurred = scene.crop(bx).filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); layer.paste(blurred, bx[:2])
    scene.paste(layer, (0, 0), mask)
    scene.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), tint).split(),
                                               mask.point(lambda v: int(v * veil)))))   # 3. veil
    if sheen:                                                     # 4. top sheen (light from above)
        g = Image.linear_gradient('L').resize((1, y1 - y0)).point(
            lambda v: int(255 * sheen * max(0, 1 - v / 255 / 0.55)))
        s = Image.new('L', (W, H), 0); s.paste(g.resize((W, y1 - y0)), (0, y0))
        scene.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), WHITE).split(),
                                                   ImageChops.multiply(s, mask))))
    rim = gradient_rim(mask)                                      # 5. lit rim
    scene.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), WHITE).split(), rim)))

def glow(scene, cx, cy, rx, ry, color, strength=200, blur=24):
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=strength)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    scene.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), color).split(), m)))

def solid(scene, mask, color, alpha=1.0):
    scene.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), color).split(),
                                               mask.point(lambda v: int(v * alpha)))))

def hgrad(scene, mask, c0, c1):
    x0, _, x1, _ = mask.getbbox()
    g = Image.linear_gradient('L').rotate(90).transpose(Image.FLIP_LEFT_RIGHT).resize((x1 - x0, H))
    full = Image.new('L', (W, H), 0); full.paste(g, (x0, 0))
    col = Image.composite(Image.new('RGB', (W, H), c1), Image.new('RGB', (W, H), c0), full)
    scene.alpha_composite(Image.merge('RGBA', (*col.split(), mask)))

def text(scene, xy, s, f, c, alpha=255, anchor='la'):
    check_glyphs(s, f)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, s, font=f, fill=c + (alpha,), anchor=anchor)
    scene.alpha_composite(lay)

# =============================================================================================
scene = background()

# 1. Heading: large, dark, sits directly on the light field (not in a card)
text(scene, (72, 84), '知識庫', hei(104), INK)
text(scene, (78, 214), 'KNOWLEDGE BASE  ·  AGENT SYNC', sf(20, b'Medium'), INK, 190)
# status chip, top right (UI element as scenery)
chip = rr((792, 96, 1008, 150), 27)
glass(scene, chip, blur=14, veil=0.24, shadow=0.12, lift=8)
glow(scene, 826, 123, 10, 10, LIGHT, 255, 6)
solid(scene, mask_from(lambda d, s: d.ellipse([820 * s, 117 * s, 832 * s, 129 * s], fill=255)), (40, 200, 220))
text(scene, (848, 112), 'SYNCING', sf(22, b'Semibold'), INK)

# 2. Knowledge-base panel (far layer: big, light blur), with 6 rows; row 3 is the empty slot
PX0, PY0, PX1, PY1 = 584, 292, 1008, 960
glass(scene, rr((PX0, PY0, PX1, PY1), 36), blur=26, veil=0.16, shadow=0.20, lift=24)
text(scene, (PX0 + 36, PY0 + 34), 'Library', sf(30, b'Semibold'), INK)
text(scene, (PX1 - 36, PY0 + 40), '61 / 100', sf(22, b'Medium'), INK2, anchor='ra')
ROW_H, ROW_G = 78, 16
dots = [BLOB_V, BLOB_P, None, BLOB_C, BLOB_O, BLOB_V]
for i, dc in enumerate(dots):
    ry0 = PY0 + 104 + i * (ROW_H + ROW_G)
    box = (PX0 + 28, ry0, PX1 - 28, ry0 + ROW_H)
    if dc is None:                               # the empty slot: dashed rim, no fill
        SLOT = box
        m = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(m)
        x, y = box[0] + 22, box[1]
        while x < box[2] - 22:
            dd.line([(x, box[1]), (min(x + 14, box[2] - 22), box[1])], fill=200, width=2)
            dd.line([(x, box[3]), (min(x + 14, box[2] - 22), box[3])], fill=200, width=2); x += 24
        for yy in range(box[1] + 18, box[3] - 18, 24):
            dd.line([(box[0], yy), (box[0], min(yy + 14, box[3] - 18))], fill=200, width=2)
            dd.line([(box[2], yy), (box[2], min(yy + 14, box[3] - 18))], fill=200, width=2)
        solid(scene, m, WHITE)
        continue
    glass(scene, rr(box, 22), blur=10, veil=0.22, sheen=0.18, shadow=0.08, lift=6)
    solid(scene, mask_from(lambda d, s, y=ry0: d.ellipse([(PX0 + 56) * s, (y + 29) * s, (PX0 + 76) * s, (y + 49) * s], fill=255)), dc)
    for j, wf in enumerate((0.62 - 0.07 * (i % 3), 0.38)):
        lw = (PX1 - PX0 - 160) * wf
        solid(scene, rr((PX0 + 98, ry0 + 24 + j * 22, PX0 + 98 + lw, ry0 + 34 + j * 22), 5), INK2, 0.75 if j == 0 else 0.4)
# 3. Robot (mid layer). Hovering glass machine: antenna, head with visor, torso, arms, thruster.
RX = 286
glow(scene, RX, 742, 70, 18, LIGHT, 170, 18)                     # thruster light on the field
glow(scene, RX, 800, 120, 16, INK, 60, 18)                       # far, faint ground shadow
# back arm (drawn first = behind torso)
glass(scene, tube([(RX - 96, 530), (RX - 140, 610), (RX - 120, 672)], 34), blur=12, veil=0.26, shadow=0.10, lift=8)
# torso
TOR = (RX - 100, 498, RX + 100, 706)
glass(scene, rr(TOR, 44), blur=18, veil=0.30, sheen=0.34, shadow=0.24, lift=22)
core = rr((RX - 46, 562, RX + 46, 640), 18)
solid(scene, core, INK, 0.78)
for i, h in enumerate((0.8, 0.5, 1.0, 0.35)):                     # status equaliser on the chest screen
    bx = RX - 30 + i * 17
    solid(scene, rr((bx, 626 - 52 * h, bx + 9, 626), 4), LIGHT, 0.9)
# neck + head
glass(scene, rr((RX - 26, 470, RX + 26, 506), 12), blur=10, veil=0.3, shadow=0, sheen=0.2)
HEAD = (RX - 118, 318, RX + 118, 476)
glass(scene, rr(HEAD, 54), blur=18, veil=0.32, sheen=0.38, shadow=0.20, lift=18)
VIS = (RX - 90, 364, RX + 90, 432)
solid(scene, rr(VIS, 34), INK, 0.88)                              # visor (dark glass, a sensor band, not eyes)
glow(scene, RX + 18, 398, 56, 8, LIGHT, 230, 7)                   # scan light, shifted right = looking at the panel
solid(scene, rr((RX - 30, 394, RX + 66, 402), 4), (220, 255, 255), 0.95)
solid(scene, rr((VIS[0] + 18, VIS[1] + 8, VIS[2] - 60, VIS[1] + 14), 3), WHITE, 0.35)   # visor reflection
# ear discs + antenna
for ex in (HEAD[0] - 14, HEAD[2] - 14):
    glass(scene, rr((ex, 370, ex + 28, 426), 14), blur=8, veil=0.34, shadow=0, sheen=0.2)
solid(scene, rr((RX - 3, 270, RX + 3, 320), 3), WHITE, 0.8)
glow(scene, RX, 266, 18, 18, LIGHT, 255, 9)
solid(scene, mask_from(lambda d, s: d.ellipse([(RX - 9) * s, 257 * s, (RX + 9) * s, 275 * s], fill=255)), (225, 255, 255))
# thruster ring under the torso
glass(scene, rr((RX - 56, 712, RX + 56, 736), 12), blur=8, veil=0.34, shadow=0, sheen=0.2)
solid(scene, rr((RX - 40, 730, RX + 40, 736), 3), LIGHT, 0.9)

# 4. Note card: slides INTO the slot. The card is drawn first (sharp, violet-tinted), then the slot's
#    front glass pane is laid over it: the part inside the slot is seen blurred and dimmed through
#    frosted glass (occlusion = it is inside), the part outside stays sharp.
CW_, CH_ = 300, 70
CX0 = SLOT[0] - 140; CY0 = SLOT[1] + (SLOT[3] - SLOT[1] - CH_) // 2
ARM = [(RX + 92, 532), (RX + 150, 586), (CX0 - 6, CY0 + CH_ // 2)]
glass(scene, tube(ARM, 34), blur=12, veil=0.30, shadow=0.12, lift=10)
card = rr((CX0, CY0, CX0 + CW_, CY0 + CH_), 20)
glass(scene, card, blur=30, veil=0.55, sheen=0.3, shadow=0.30, lift=24, tint=ACC_B)
hgrad(scene, rr((CX0 + 22, CY0 + 40, CX0 + 150, CY0 + 50), 5), ACC_A, ACC_B)
solid(scene, rr((CX0 + 22, CY0 + 54, CX0 + 250, CY0 + 60), 3), INK2, 0.55)
text(scene, (CX0 + 22, CY0 + 8), '#61', sf(24, b'Bold'), INK)
# gripper: two small glass pads clamping the card's left edge
for gy in (CY0 - 14, CY0 + CH_ - 8):
    glass(scene, rr((CX0 - 22, gy, CX0 + 26, gy + 22), 11), blur=8, veil=0.4, shadow=0.1, lift=4, sheen=0.2)
# slot front pane over the card + a light leak at the mouth
glass(scene, rr(SLOT, 22), blur=9, veil=0.30, sheen=0.22, shadow=0, lift=0)
glow(scene, SLOT[0] + 2, (SLOT[1] + SLOT[3]) // 2, 6, 34, LIGHT, 230, 8)
# slot hint arrow inside the empty slot (points in the direction the card travels)
sx = SLOT[2] - 70; sy = (SLOT[1] + SLOT[3]) // 2
solid(scene, mask_from(lambda d, s: d.polygon([((sx - 10) * s, (sy - 12) * s), ((sx + 8) * s, sy * s), ((sx - 10) * s, (sy + 12) * s)], fill=255)), WHITE, 0.7)


# 5. Big-number widget (front-left)
WG = (72, 792, 520, 1030)
glass(scene, rr(WG, 40), blur=24, veil=0.26, sheen=0.3, shadow=0.24, lift=22)
text(scene, (WG[0] + 40, WG[1] + 30), '已收錄', hei(26, w6=False), INK2)
text(scene, (WG[2] - 40, WG[1] + 32), '+1 today', sf(22, b'Medium'), INK2, anchor='ra')
text(scene, (WG[0] + 34, WG[1] + 172), '61', sf(150, b'Bold'), INK, anchor='ls')
PX_ = WG[0] + 34 + sf(150, b'Bold').getlength('61') + 6          # % sits 6px after the figures
text(scene, (PX_, WG[1] + 172), '%', sf(84, b'Semibold'), INK, anchor='ls')
bar = (WG[0] + 40, WG[1] + 194, WG[2] - 40, WG[1] + 208)
solid(scene, rr(bar, 9), WHITE, 0.55)
fill_x = bar[0] + (bar[2] - bar[0]) * 0.61
glow(scene, (bar[0] + fill_x) // 2, (bar[1] + bar[3]) // 2, (fill_x - bar[0]) // 2, 10, ACC_B, 150, 10)
hgrad(scene, rr((bar[0], bar[1], fill_x, bar[3]), 9), ACC_A, ACC_B)

# 6. Subtitle zone (y > 1053) stays empty light field.
scene = grain(scene)
scene.convert('RGB').save(os.path.join(HERE, 'sample.png'))
