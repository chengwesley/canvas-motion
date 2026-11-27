"""v4 full component sheet in the top-down dithered pixel style (all original)."""
from PIL import Image, ImageDraw, ImageFont
import math, random

def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
G = [rgb('2d5a3a'), rgb('4f8a3c'), rgb('8fbf4a'), rgb('cfe37a')]
PUR = [rgb('3a2a55'), rgb('5d447e')]
SAND = [rgb('c9b27a'), rgb('e8dcae'), rgb('f6f0cf')]
WAT = [rgb('16245a'), rgb('24457f'), rgb('3f8fb0'), rgb('8fd0c8'), rgb('e3f4ee')]
ROOF = [rgb('7a2f2a'), rgb('c8502f'), rgb('f09a3e'), rgb('f8d27a')]
STONE = [rgb('6f6a66'), rgb('8f8672'), rgb('c9bfa5'), rgb('efe6d0')]
WOOD = [rgb('4a2c1a'), rgb('7a4a26'), rgb('b0783c'), rgb('ddb070')]
GOLD = [rgb('a8641c'), rgb('e8a33a'), rgb('ffd65c'), rgb('fff4b8')]
REDS = [rgb('8c2b3a'), rgb('d9473f'), rgb('f27b5b'), rgb('ffc2a6')]
GRN = [rgb('1f6e55'), rgb('2fa86a'), rgb('6bd68a'), rgb('c4f5c8')]
BLU = [rgb('283c8f'), rgb('3a6be0'), rgb('6ea8ff'), rgb('c8e2ff')]
NAVY = [rgb('141633'), rgb('262b5c'), rgb('3c4488')]
OUT = rgb('23203a'); WHITE = rgb('fbf8ea'); CYAN = rgb('7fe8e0'); PAPER = [rgb('b9b29a'), rgb('e9e2c8'), rgb('fbf8ea')]
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
def dth(x, y, t): return t > (BAYER[y % 4][x % 4] + .5) / 16
def noise(x, y): return (math.sin(x * .31 + y * .17) + math.sin(x * .13 - y * .29 + 2) + math.sin((x + y) * .23 + 5)) / 3
T = 56


class C:
    def __init__(s, w=T, h=T, bg='grass'):
        s.w, s.h = w, h; s.im = Image.new('RGB', (w, h)); s.p = s.im.load()
        for y in range(h):
            for x in range(w):
                if bg == 'grass':
                    n = noise(x, y) * .5 + .5; c = G[2] if dth(x, y, n * .8 + .15) else G[1]
                elif bg == 'night': c = NAVY[1] if dth(x, y, .5 + noise(x, y) * .3) else NAVY[0]
                elif bg == 'sand': c = SAND[2] if dth(x, y, .55 + noise(x * 2, y * 2) * .3) else SAND[1]
                else: c = bg
                s.p[x, y] = c
    def put(s, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < s.w and 0 <= y < s.h: s.p[x, y] = c
    def rect(s, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1): s.put(x, y, c)
    def box(s, x0, y0, x1, y1, c, hi=None, sh=None):
        s.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, OUT); s.rect(x0, y0, x1, y1, c)
        if hi: s.rect(x0, y0, x1, y0, hi); s.rect(x0, y0, x0, y1, hi)
        if sh: s.rect(x0, y1, x1, y1, sh); s.rect(x1, y0, x1, y1, sh)
    def shadow(s, cx, cy, rx, ry):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1 and dth(x, y, .6): s.put(x, y, PUR[1] if dth(x + 2, y + 1, .5) else PUR[0])
    def blob(s, cx, cy, r, ramp, seed=1, squash=1.1, lumps=5, dark=PUR[0]):
        pts = {}
        for y in range(int(cy - r - 3), int(cy + r + 3)):
            for x in range(int(cx - r - 3), int(cx + r + 3)):
                a = math.atan2(y - cy, x - cx); rr = r * (1 + .14 * math.sin(a * lumps + seed) + .07 * math.sin(a * 9 + seed * 2))
                if math.hypot(x - cx, (y - cy) * squash) < rr: pts[(x, y)] = 1
        for (x, y) in pts:
            l = (-(x - cx) * .55 - (y - cy) * .85) / r + math.sin(x * 1.3 + seed) * math.sin(y * 1.1) * .22
            if l > .55: c = ramp[3] if dth(x, y, (l - .55) * 2.2) else ramp[2]
            elif l > .05: c = ramp[2] if dth(x, y, (l - .05) * 2) else ramp[1]
            elif l > -.45: c = ramp[1] if dth(x, y, (l + .45) * 2) else ramp[0]
            else: c = ramp[0] if dth(x, y, (l + .95) * 2) else dark
            s.put(x, y, c)
        for (x, y) in pts:
            if any((x + dx, y + dy) not in pts for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): s.put(x, y, OUT if (y > cy - r * .3 or x > cx) else ramp[0])
    def disc(s, cx, cy, r, fn):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if d <= r:
                    c = fn(x, y, d)
                    if c: s.put(x, y, c)
    def line(s, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n):
            t = k / max(1, n - 1); s.put(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)
    def flower(s, x, y, c=REDS[1]):
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)): s.put(x + dx, y + dy, c)
        s.put(x, y, GOLD[2])
    def sparkle(s, x, y, c=GOLD[2]):
        s.put(x, y, WHITE)
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)): s.put(x + dx, y + dy, c)


def note(c, x, y, state='plain', w=13, h=17):
    edge = {'plain': OUT, 'wrong': REDS[1], 'ok': GRN[1]}[state]
    c.rect(x - 1, y - 1, x + w, y + h, OUT)
    if state != 'plain': c.rect(x - 2, y - 2, x + w + 1, y + h + 1, OUT); c.rect(x - 1, y - 1, x + w, y + h, edge)
    c.rect(x, y, x + w - 1, y + h - 1, PAPER[2]); c.rect(x + w - 1, y, x + w - 1, y + h - 1, PAPER[1]); c.rect(x, y + h - 1, x + w - 1, y + h - 1, PAPER[1])
    for k, lw in enumerate((9, 7, 9, 5)): c.rect(x + 2, y + 3 + k * 3, x + 1 + lw, y + 3 + k * 3, STONE[1])
    if state == 'wrong':
        for k in range(5): c.put(x + w - 7 + k, y + h - 7 + k, REDS[1]); c.put(x + w - 3 - k, y + h - 7 + k, REDS[1]); c.put(x + w - 6 + k, y + h - 7 + k, REDS[1])
    if state == 'ok':
        c.line(x + w - 8, y + h - 5, x + w - 6, y + h - 3, GRN[1]); c.line(x + w - 6, y + h - 3, x + w - 2, y + h - 8, GRN[1])
        c.line(x + w - 8, y + h - 6, x + w - 6, y + h - 4, GRN[1]); c.line(x + w - 6, y + h - 4, x + w - 2, y + h - 9, GRN[1])


def core(c, cx, cy, state='idle', R=9):
    dream = state == 'dream'
    halo = {'idle': 5, 'active': 9, 'think': 6, 'dream': 7}[state]
    hc = (REDS[3], GOLD[2]) if state == 'active' else ((BLU[3], WHITE) if dream else (CYAN, WHITE))
    for y in range(cy - R - halo, cy + R + halo + 1):
        for x in range(cx - R - halo, cx + R + halo + 1):
            d = math.hypot(x - cx, y - cy)
            if R < d < R + halo:
                if state == 'think' and int((math.degrees(math.atan2(y - cy, x - cx)) + 360) // 30) % 2: continue
                if dth(x, y, (R + halo - d) / halo * (1 if state == 'active' else .8)): c.put(x, y, hc[0] if dth(x + 1, y + 1, .5) else hc[1])
    shell = NAVY if dream else [BLU[0], BLU[1], BLU[2]]
    cr = GOLD if dream else REDS
    def fn(x, y, d):
        if d > R - 1.2: return OUT
        if d > R * .58: return shell[2] if (x - cx + y - cy) < -4 else (shell[0] if (x - cx + y - cy) > 4 else shell[1])
        if d > R * .47: return OUT
        if dream and math.hypot(x - cx + 2.2, y - cy - 1.2) < R * .42: return NAVY[1]
        lvl = 3 if d < R * .16 else (2 if d < R * .3 else 1)
        if state == 'idle': lvl = max(0, lvl - 1)
        return cr[lvl] if lvl < 3 else WHITE
    c.disc(cx, cy, R, fn)
    c.put(cx - R * .55, cy - R * .6, WHITE); c.put(cx - R * .65, cy - R * .5, WHITE)
    if state == 'active':
        for a in range(0, 360, 45):
            for r in (R + 3, R + 4, R + 5): c.put(cx + round(r * math.cos(math.radians(a))), cy + round(r * math.sin(math.radians(a))), GOLD[2])
    if dream:
        for (dx, dy) in ((-13, -11), (12, -12), (14, 5)): c.sparkle(cx + dx, cy + dy)
    if state == 'think':
        for a in (300, 325, 350): c.sparkle(cx + round((R + 5) * math.cos(math.radians(a))), cy + round((R + 5) * math.sin(math.radians(a))), CYAN)


ITEMS = []
def item(label, sub=''):
    def deco(fn): ITEMS.append((label, sub, fn)); return fn
    return deco

# ---------- terrain ----------
@item('草地', '抖色兩階＋亮斑')
def _():
    c = C(); [c.flower(x, y, col) for x, y, col in ((12, 14, REDS[1]), (40, 30, WHITE), (24, 44, REDS[1]))]
    for x, y in ((30, 12), (8, 34), (46, 46)):
        for k in range(3): c.put(x + k * 2, y - (k % 2), G[3]); c.put(x + k * 2, y + 1, G[0])
    return c
@item('沙路', '邊緣抖色融入草地')
def _():
    c = C()
    for y in range(T):
        for x in range(T):
            d = abs(x - 28 - math.sin(y * .15) * 6) + noise(x * 3, y * 3) * 2
            if d < 13 and dth(x, y, 1 - max(0, (d - 9) / 4)): c.put(x, y, SAND[2] if dth(x + 1, y + 2, .55 + noise(x * 2, y * 2) * .3) else SAND[1])
            elif 13 <= d < 15 and dth(x, y, .5): c.put(x, y, G[0])
    for x, y in ((24, 10), (33, 30), (26, 46)): c.put(x, y, SAND[0]); c.put(x + 1, y, SAND[0])
    return c
@item('水', '五階深淺＋波光')
def _():
    c = C()
    for y in range(T):
        for x in range(T):
            r = math.hypot((x - 28) / 25, (y - 28) / 24) + noise(x * 2, y * 2) * .08
            if r < 1:
                t = 1 - r
                if t < .12: col = WAT[4] if dth(x, y, .6) else WAT[3]
                elif t < .35: col = WAT[3] if dth(x, y, 1 - (t - .12) / .23) else WAT[2]
                elif t < .6: col = WAT[2] if dth(x, y, 1 - (t - .35) / .25) else WAT[1]
                else: col = WAT[1] if dth(x, y, 1 - (t - .6) / .4) else WAT[0]
                c.put(x, y, col)
            elif r < 1.08: c.put(x, y, SAND[1] if dth(x, y, .6) else G[0])
    for x, y in ((18, 20), (34, 34), (26, 40)): c.rect(x, y, x + 4, y, WAT[4])
    return c
@item('闊葉樹', '亮面、暗面、紫色陰影')
def _(): c = C(); c.shadow(30, 44, 17, 6); c.rect(26, 36, 29, 46, WOOD[1]); c.rect(26, 36, 26, 46, WOOD[0]); c.blob(28, 24, 17, G, 3); return c
@item('針葉樹', '三層樹冠')
def _():
    c = C(); c.shadow(30, 48, 14, 5); c.rect(26, 42, 29, 50, WOOD[1])
    for i, (cy, hw) in enumerate(((38, 16), (27, 13), (17, 9))):
        for y in range(cy - 12, cy + 1):
            w = hw * (y - cy + 12) / 12
            for x in range(int(28 - w), int(28 + w) + 1):
                l = (28 - x) / max(1, w) * .6 + (cy - y) / 12 * .5
                c.put(x, y, G[3] if (l > .6 and dth(x, y, .6)) else (G[2] if l > .1 and dth(x, y, .5 + l) else (G[1] if l > -.4 else G[0])))
            c.put(int(28 - w) - 1, y, OUT); c.put(int(28 + w) + 1, y, OUT)
        c.rect(28 - hw - 1, cy + 1, 28 + hw + 1, cy + 1, OUT)
    return c
@item('灌木與花', '小景點綴')
def _(): c = C(); c.shadow(22, 34, 12, 4); c.blob(20, 26, 10, G, 5, lumps=4); c.blob(38, 34, 8, G, 9, lumps=4); [c.flower(x, y, col) for x, y, col in ((17, 22, REDS[1]), (24, 28, WHITE), (38, 32, REDS[2]), (46, 46, REDS[1]), (10, 46, WHITE))]; return c
@item('岩石', '三階灰＋苔')
def _(): c = C(); c.shadow(30, 42, 18, 5); c.blob(26, 30, 13, [STONE[0], STONE[1], STONE[2], STONE[3]], 2, squash=1.3, lumps=3, dark=PUR[0]); c.blob(42, 38, 7, [STONE[0], STONE[1], STONE[2], STONE[3]], 6, squash=1.3, lumps=3); [c.put(x, y, G[2]) for x, y in ((20, 24), (21, 24), (22, 25), (30, 22), (31, 23))]; return c
@item('木柵欄', '圍出院子')
def _():
    c = C()
    for x in range(4, 52):
        if (x - 4) % 6 == 0:
            c.rect(x - 1, 20, x + 3, 36, OUT); c.rect(x, 21, x + 2, 35, WHITE); c.rect(x + 2, 22, x + 2, 35, STONE[2]); c.put(x + 1, 19, OUT); c.put(x + 1, 20, WHITE)
    c.rect(4, 25, 51, 26, WHITE); c.rect(4, 27, 51, 27, STONE[2]); c.rect(4, 31, 51, 32, WHITE); c.rect(4, 33, 51, 33, STONE[2]); c.rect(4, 37, 51, 37, PUR[0])
    return c
@item('單向崖', '月見山：掉下去回不來')
def _():
    c = C()
    for y in range(24, 40):
        for x in range(T):
            t = (y - 24) / 16; c.put(x, y, STONE[2] if dth(x, y, 1 - t) and (x + y // 3) % 7 else (STONE[1] if dth(x, y, 1.2 - t) else STONE[0]))
    c.rect(0, 23, T, 23, OUT); c.rect(0, 40, T, 40, OUT)
    for y in range(40, 46):
        for x in range(T):
            if dth(x, y, .7 - (y - 40) * .1): c.put(x, y, PUR[0])
    for ax in (14, 28, 42):
        for k in range(4): c.rect(ax - k, 27 + k, ax + k, 27 + k, WHITE if k < 3 else OUT)
        c.rect(ax - 1, 31, ax + 1, 36, WHITE)
    return c
@item('路牌', '月見山／華藍市／尼比市')
def _(): c = C(); c.shadow(30, 48, 10, 3); c.rect(26, 28, 29, 48, WOOD[1]); c.rect(26, 28, 26, 48, WOOD[0]); c.box(10, 12, 45, 27, WOOD[2], WOOD[3], WOOD[1]); [c.rect(x, 18 + (i % 2) * 4, x + 3, 18 + (i % 2) * 4, WOOD[0]) for i, x in enumerate((14, 20, 26, 32, 38))]; [c.put(x, y, STONE[2]) for x, y in ((12, 14), (43, 14), (12, 25), (43, 25))]; return c
@item('城門', '抵達城市的終點')
def _():
    c = C(); c.shadow(28, 50, 22, 4)
    for x0 in (6, 38): c.box(x0, 18, x0 + 11, 48, STONE[2], STONE[3], STONE[1]); [c.rect(x0, yy, x0 + 11, yy, STONE[1]) for yy in (26, 34, 42)]; c.box(x0 - 2, 12, x0 + 13, 17, ROOF[1], ROOF[2], ROOF[0])
    c.box(18, 14, 37, 22, WOOD[2], WOOD[3], WOOD[1]); c.rect(27, 6, 28, 13, WOOD[1])
    for k in range(6): c.rect(29, 5 + k, 29 + (6 - abs(k - 2) * 2), 5 + k, GRN[1])
    return c
@item('營火帳篷', '一次工作階段')
def _():
    c = C(); c.shadow(24, 46, 20, 5)
    for y in range(16, 46):
        w = (y - 16) * .62
        for x in range(int(22 - w), int(22 + w) + 1): c.put(x, y, BLU[2] if x < 22 - w * .3 else (BLU[1] if x < 22 + w * .4 or dth(x, y, .5) else BLU[0]))
        c.put(int(22 - w) - 1, y, OUT); c.put(int(22 + w) + 1, y, OUT)
    for y in range(30, 46):
        w = (y - 30) * .35
        for x in range(int(22 - w), int(22 + w) + 1): c.put(x, y, NAVY[0])
    c.rect(3, 46, 41, 46, OUT)
    for k, col in enumerate((REDS[1], ROOF[2], GOLD[2], WHITE)):
        c.disc(46, 42 - k, 4 - k, lambda x, y, d, col=col: col)
    c.rect(41, 46, 51, 47, WOOD[0])
    return c

# ---------- the four memory layers as places ----------
@item('① 逐字稿庫', '石造地窖，一捲捲卷軸')
def _():
    c = C(); c.shadow(28, 48, 24, 5); c.box(6, 20, 49, 46, STONE[2], STONE[3], STONE[1])
    for y in range(20, 47):
        for x in range(6, 50):
            if (y - 20) % 5 == 4 or (x + ((y - 20) // 5) * 4) % 10 == 0: c.put(x, y, STONE[1])
    for y in range(8, 20):
        w = 22 * math.sqrt(max(0, 1 - ((19 - y) / 12) ** 2)) if y < 19 else 22
        for x in range(int(28 - w), int(28 + w) + 1): c.put(x, y, STONE[3] if x < 24 else STONE[2])
        c.put(int(28 - w) - 1, y, OUT); c.put(int(28 + w) + 1, y, OUT)
    c.rect(18, 7, 38, 7, OUT)
    c.box(20, 28, 35, 46, NAVY[0])
    for k, yy in enumerate((30, 35, 40)):
        for j in range(3): c.rect(22 + j * 5, yy, 24 + j * 5, yy + 3, PAPER[2]); c.rect(22 + j * 5, yy, 22 + j * 5, yy + 3, WOOD[2]); c.rect(24 + j * 5, yy, 24 + j * 5, yy + 3, WOOD[2])
    return c
@item('② 筆記佈告欄', 'Agent 自己寫的筆記')
def _():
    c = C(); c.shadow(28, 50, 22, 4)
    for x0 in (10, 44): c.rect(x0, 14, x0 + 2, 50, WOOD[1]); c.rect(x0, 14, x0, 50, WOOD[0])
    c.box(6, 14, 49, 40, WOOD[2], WOOD[3], WOOD[1]); c.box(4, 8, 51, 13, ROOF[1], ROOF[2], ROOF[0])
    for (x, y, col) in ((10, 18, PAPER[2]), (22, 17, GOLD[3]), (35, 19, PAPER[2]), (14, 29, PAPER[2]), (28, 28, CYAN), (39, 30, PAPER[2])):
        c.rect(x - 1, y - 1, x + 8, y + 8, OUT); c.rect(x, y, x + 7, y + 7, col); c.rect(x + 1, y + 2, x + 5, y + 2, STONE[1]); c.rect(x + 1, y + 4, x + 6, y + 4, STONE[1]); c.put(x + 3, y - 1, REDS[1]); c.put(x + 4, y - 1, REDS[1])
    return c
@item('③ wiki 圖書館', '筆記連成知識網')
def _():
    c = C(); c.shadow(30, 50, 24, 4); c.box(8, 26, 47, 48, STONE[3], WHITE, STONE[2])
    for y in range(26, 49):
        for x in range(8, 48):
            if (y - 26) % 4 == 3 or (x + ((y - 26) // 4) * 4) % 9 == 0: c.put(x, y, STONE[2])
    for y in range(8, 27):
        ins = max(0, 5 - (y - 8) // 2)
        for x in range(5 + ins, 51 - ins):
            row = (y - 8) // 5; lx = (x + row * 3) % 7; ly = (y - 8) % 5
            col = ROOF[1]
            if ly == 0: col = ROOF[2] if lx in (1, 2, 3, 4) else ROOF[3]
            elif ly == 4 or lx == 0: col = ROOF[0]
            c.put(x, y, col)
        c.put(4 + ins, y, OUT); c.put(51 - ins, y, OUT)
    c.rect(10, 7, 45, 7, OUT); c.rect(4, 27, 51, 27, OUT)
    c.box(24, 34, 31, 48, WOOD[1], WOOD[2], WOOD[0]); c.put(30, 41, GOLD[2])
    for wx in (11, 36):
        c.box(wx, 32, wx + 8, 41, WAT[1])
        for k, col in enumerate((ROOF[2], WHITE, CYAN, REDS[1])): c.rect(wx + 1 + k * 2, 34, wx + 1 + k * 2, 40, col)
    return c
@item('④ 最上層祭壇', '每次都先載入，只放一塊')
def _():
    c = C(); c.shadow(28, 48, 20, 5)
    for i, (hw, y0) in enumerate(((20, 40), (15, 34), (10, 28))): c.box(28 - hw, y0, 27 + hw, y0 + 5, STONE[2], STONE[3], STONE[1])
    for dy in range(9):
        w = 5 - abs(dy - 4) + 1
        for x in range(28 - w, 28 + w): c.put(x, 13 + dy, CYAN if x < 28 else WAT[2])
        c.put(28 - w - 1, 13 + dy, OUT); c.put(28 + w, 13 + dy, OUT)
    c.put(26, 15, WHITE); c.put(27, 14, WHITE); c.rect(26, 12, 29, 12, OUT); c.rect(27, 22, 28, 22, OUT)
    for (dx, dy) in ((-12, 12), (12, 10), (-9, 22), (10, 22)): c.sparkle(28 + dx, dy, CYAN)
    return c
@item('記憶寶箱', '跨工作階段保留')
def _():
    c = C(); c.shadow(28, 46, 20, 5); c.box(10, 26, 45, 44, WOOD[2], WOOD[3], WOOD[1])
    for y in range(14, 26):
        w = 18 * math.sqrt(max(0, 1 - ((25 - y) / 12) ** 2)) if y < 25 else 18
        for x in range(int(28 - w), int(28 + w) + 1): c.put(x, y, WOOD[3] if x < 22 else (WOOD[2] if x < 36 else WOOD[1]))
        c.put(int(28 - w) - 1, y, OUT); c.put(int(28 + w) + 1, y, OUT)
    c.rect(14, 13, 41, 13, OUT)
    for x0 in (14, 38): c.rect(x0, 14, x0 + 3, 44, GOLD[1]); c.rect(x0, 14, x0, 44, GOLD[2])
    c.rect(10, 25, 45, 26, OUT); c.box(25, 23, 30, 30, GOLD[2], GOLD[3], GOLD[0]); c.rect(27, 26, 28, 28, OUT)
    return c
@item('MEMORY.md 石板', '只載入前 200 行')
def _():
    c = C(); c.shadow(28, 48, 16, 4); c.box(14, 10, 41, 46, STONE[3], WHITE, STONE[2])
    for k, w in enumerate((20, 16, 20, 12, 18)): c.rect(18, 16 + k * 5, 17 + w, 17 + k * 5, STONE[0] if k else REDS[1])
    c.rect(14, 40, 41, 40, REDS[1]); c.rect(14, 41, 41, 46, STONE[2]);
    for x in range(14, 42, 4): c.rect(x, 43, x + 1, 43, STONE[1])
    return c

# ---------- items ----------
@item('筆記', '一般')
def _(): c = C(bg='sand'); c.shadow(30, 44, 12, 3); note(c, 16, 12, 'plain', 22, 28); return c
@item('筆記（寫錯）', '紅框＋叉')
def _(): c = C(bg='sand'); c.shadow(30, 44, 12, 3); note(c, 16, 12, 'wrong', 22, 28); return c
@item('筆記（已驗證）', '綠框＋勾')
def _(): c = C(bg='sand'); c.shadow(30, 44, 12, 3); note(c, 16, 12, 'ok', 22, 28); return c
@item('逐字稿卷軸', '原始事件紀錄')
def _():
    c = C(bg='sand'); c.shadow(28, 46, 18, 3); c.box(12, 14, 43, 40, PAPER[2], WHITE, PAPER[1])
    for k in range(5): c.rect(16, 18 + k * 4, 16 + (22 if k % 2 else 26) - 1, 18 + k * 4, STONE[1]); c.put(14, 18 + k * 4, REDS[1])
    for yy in (9, 41): c.box(9, yy, 46, yy + 4, WOOD[2], WOOD[3], WOOD[1]); c.box(6, yy + 1, 8, yy + 3, GOLD[1]); c.box(47, yy + 1, 49, yy + 3, GOLD[1])
    return c
@item('wiki 頁面連結', '頁面互相連結')
def _():
    c = C(bg='sand'); P = ((8, 8), (34, 6), (20, 26), (38, 34), (6, 38))
    for a, b in ((0, 2), (1, 2), (2, 3), (2, 4), (1, 3), (0, 4)):
        c.line(P[a][0] + 6, P[a][1] + 7, P[b][0] + 6, P[b][1] + 7, BLU[1]); c.line(P[a][0] + 6, P[a][1] + 8, P[b][0] + 6, P[b][1] + 8, BLU[2])
    for i, (x, y) in enumerate(P): note(c, x, y, 'plain', 12, 14); c.rect(x + 2, y + 2, x + 9, y + 3, BLU[1] if i != 2 else REDS[1])
    return c
@item('金幣', '畫面上看得到→不用記')
def _():
    c = C(bg='sand'); c.shadow(28, 46, 13, 3)
    c.disc(28, 27, 15, lambda x, y, d: OUT if d > 13.8 else (GOLD[1] if d > 10 else (GOLD[2] if (x + y) < 52 else GOLD[1])))
    c.disc(28, 27, 9, lambda x, y, d: GOLD[0] if d > 8 else None); c.rect(27, 21, 29, 33, GOLD[0]); c.rect(25, 23, 31, 24, GOLD[0]); c.rect(25, 30, 31, 31, GOLD[0]); c.put(20, 19, WHITE); c.put(21, 18, WHITE); c.put(19, 20, WHITE)
    return c
@item('地圖釘', '畫面上看得到→不用記')
def _():
    c = C(bg='sand'); c.shadow(28, 47, 8, 3)
    for y in range(26, 45):
        w = max(0, 10 * (44 - y) / 18)
        for x in range(int(28 - w), int(28 + w) + 1): c.put(x, y, REDS[1] if x < 30 else REDS[0])
        c.put(int(28 - w) - 1, y, OUT); c.put(int(28 + w) + 1, y, OUT)
    c.disc(28, 22, 13, lambda x, y, d: OUT if d > 11.8 else (REDS[2] if (x + y) < 46 else (REDS[1] if (x + y) < 56 else REDS[0])))
    c.disc(28, 22, 5, lambda x, y, d: OUT if d > 4 else WHITE); return c
@item('徽章', '遊戲進度')
def _():
    c = C(bg='sand'); c.shadow(28, 48, 12, 3)
    for x0, col in ((18, REDS[1]), (30, BLU[1])): c.box(x0, 6, x0 + 7, 24, col, None, None)
    pts = []
    c.disc(28, 34, 14, lambda x, y, d: OUT if d > 12.8 else (GOLD[1] if d > 9.5 else (GOLD[2] if (x + y) < 60 else GOLD[1])))
    for i in range(10):
        a = math.radians(-90 + i * 36); r = 7 if i % 2 == 0 else 3; pts.append((28 + r * math.cos(a), 34 + r * math.sin(a)))
    for y in range(26, 43):
        for x in range(20, 37):
            ins = False; j = 9
            for i in range(10):
                xi, yi = pts[i]; xj, yj = pts[j]
                if (yi > y + .5) != (yj > y + .5) and x + .5 < (xj - xi) * (y + .5 - yi) / (yj - yi + 1e-9) + xi: ins = not ins
                j = i
            if ins: c.put(x, y, WHITE if y < 33 else GOLD[3])
    return c
@item('陀螺', '對照逐字稿＝現實檢查')
def _():
    c = C(bg='sand'); c.shadow(28, 49, 12, 3); c.rect(27, 5, 29, 16, WOOD[2]); c.rect(26, 4, 30, 5, OUT); c.rect(26, 6, 26, 16, OUT); c.rect(30, 6, 30, 16, OUT)
    for y in range(17, 47):
        w = 17 if y < 22 else 17 * (46 - y) / 24
        for x in range(int(28 - w), int(28 + w) + 1):
            col = REDS[2] if x < 28 - w * .4 else (REDS[1] if x < 28 + w * .45 else REDS[0])
            if 24 <= y <= 26: col = GOLD[2] if x < 30 else GOLD[1]
            if y < 19: col = REDS[3] if x < 30 else REDS[2]
            c.put(x, y, col)
        c.put(int(28 - w) - 1, y, OUT); c.put(int(28 + w) + 1, y, OUT)
    c.rect(11, 16, 45, 16, OUT); c.put(28, 47, OUT)
    for (x, y) in ((6, 30), (8, 36), (48, 28), (50, 34)): c.rect(x, y, x + 2, y, STONE[1])
    return c
@item('放大鏡', '比對筆記與紀錄')
def _():
    c = C(bg='sand'); c.shadow(30, 48, 14, 3)
    for k in range(14): c.rect(33 + k, 33 + k, 37 + k, 36 + k, OUT)
    for k in range(13): c.rect(35 + k, 34 + k, 37 + k, 36 + k, WOOD[2])
    c.disc(22, 22, 17, lambda x, y, d: OUT if d > 15.8 else (STONE[3] if d > 12.5 and (x + y) < 44 else (STONE[1] if d > 12.5 else (OUT if d > 11.5 else (WAT[4] if dth(x, y, .35) and (x + y) < 40 else WAT[3])))))
    c.rect(15, 15, 19, 16, WHITE); c.rect(14, 17, 15, 20, WHITE); return c
@item('月亮', '做夢的符號')
def _():
    c = C(bg='night')
    c.disc(28, 28, 18, lambda x, y, d: None if math.hypot(x - 35, y - 23) < 15 else (OUT if d > 16.8 else (GOLD[3] if (x + y) < 44 else (GOLD[2] if dth(x, y, .7) else GOLD[1]))))
    for (x, y) in ((42, 12), (46, 40), (10, 10), (38, 30)): c.sparkle(x, y)
    return c

# ---------- agent ----------
for st, lb, sub in (('idle', 'Agent 待機', '核心微亮'), ('active', 'Agent 工作中', '核心全亮＋放射光'), ('think', 'Agent 思考', '虛環＋青色光點'), ('dream', 'Agent 做夢', '深藍外殼＋月牙核心')):
    def mkc(st=st):
        c = C(bg='night' if st == 'dream' else 'grass'); c.shadow(28, 46, 12, 3) if st != 'dream' else None; core(c, 28, 27, st, 12); return c
    ITEMS.append((lb, sub, mkc))

@item('固定規則的籠子', '規定怎麼記')
def _():
    c = C(); c.shadow(28, 48, 18, 4); note(c, 21, 20, 'plain', 14, 18); c.box(10, 8, 45, 12, STONE[1], STONE[2], STONE[0]); c.box(10, 44, 45, 47, STONE[1], STONE[2], STONE[0])
    for x in range(12, 45, 6): c.rect(x - 1, 13, x + 2, 43, OUT); c.rect(x, 13, x + 1, 43, STONE[2]); c.rect(x, 13, x, 43, STONE[3])
    return c
@item('用途指標', '說明記憶是用來做什麼')
def _():
    c = C(); c.shadow(28, 50, 10, 3); c.rect(26, 30, 29, 50, WOOD[1]); c.rect(26, 30, 26, 50, WOOD[0])
    for y in range(10, 31):
        tip = 10 - abs(y - 20)
        x1 = 34 + (tip if 12 <= y <= 28 else 0); x0 = 8
        if 14 <= y <= 26: c.rect(x0, y, 34, y, GRN[1] if y > 16 else GRN[2])
        if 10 <= y <= 30: c.rect(34, y, 34 + max(0, tip + 4), y, GRN[1] if y > 16 else GRN[2])
    for y in range(10, 31):
        tip = max(0, 10 - abs(y - 20) + 4); c.put(35 + tip, y, OUT)
    c.rect(8, 13, 34, 13, OUT); c.rect(8, 27, 34, 27, OUT); c.rect(7, 14, 7, 26, OUT); c.rect(34, 9, 36, 9, OUT); c.rect(34, 31, 36, 31, OUT)
    c.sparkle(50, 8); return c

# ---------- assemble sheet ----------
S = 4; COLS = 6; GAPX, GAPY = 62, 96
rows = math.ceil(len(ITEMS) / COLS)
W = 80 + COLS * (T * S + GAPX); UIY = 250 + rows * (T * S + GAPY); H = UIY + 760
sheet = Image.new('RGB', (W, H), rgb('f4efe1')); d = ImageDraw.Draw(sheet)
ZH = '/System/Library/Fonts/STHeiti Medium.ttc'; MONO = '/System/Library/Fonts/Menlo.ttc'
def F(p, n): return ImageFont.truetype(p, n)
d.text((60, 40), 'v4 全部元件（俯視角抖色像素風・全部原創）', fill=OUT, font=F(ZH, 58))
d.text((60, 122), f'每格 {T}×{T} 像素、放大 {S} 倍顯示｜統一深紫描邊、每色 3–4 階、陰影用紫色抖色｜不含任何遊戲的角色或圖樣', fill=STONE[0], font=F(ZH, 28))
secs = {0: '地形與場景', 12: '記憶四層（地點）與相關物件', 18: '道具', 30: 'Agent 能量核心與引導'}
for i, (lb, sub, fn) in enumerate(ITEMS):
    cx = 60 + (i % COLS) * (T * S + GAPX); cy = 230 + (i // COLS) * (T * S + GAPY)
    tile = fn().im.resize((T * S, T * S), Image.NEAREST)
    d.rectangle([cx - 6, cy - 6, cx + T * S + 5, cy + T * S + 5], fill=OUT); sheet.paste(tile, (cx, cy))
    d.text((cx, cy + T * S + 12), lb, fill=OUT, font=F(ZH, 28)); d.text((cx, cy + T * S + 48), sub, fill=STONE[0], font=F(ZH, 20))

# UI section
def box(x0, y0, x1, y1, fill, b=6):
    d.rectangle([x0 + b, y0, x1 - b, y1], fill=OUT); d.rectangle([x0, y0 + b, x1, y1 - b], fill=OUT)
    d.rectangle([x0 + b, y0 + b, x1 - b, y1 - b], fill=fill); d.rectangle([x0 + b, y0 + b, x1 - b, y0 + b * 2 - 1], fill=WHITE if fill != WHITE else rgb('e9e2c8'))
d.text((60, UIY), '介面元件', fill=OUT, font=F(ZH, 44))
box(60, UIY + 80, 560, UIY + 160, NAVY[1]); d.text((86, UIY + 98), 'STAGE 2', fill=GOLD[2], font=F(MONO, 40)); d.text((310, UIY + 100), '筆記', fill=WHITE, font=F(ZH, 40))
d.text((60, UIY + 172), '頂部 HUD：目前講到哪一層', fill=STONE[0], font=F(ZH, 24))
box(620, UIY + 80, 1640, UIY + 270, WHITE); d.text((664, UIY + 110), '做夢時，它回頭拿筆記對照原始逐字稿，', fill=OUT, font=F(ZH, 46)); d.text((664, UIY + 180), '發現錯誤、改寫筆記。', fill=OUT, font=F(ZH, 46))
d.text((620, UIY + 282), '對話框字幕（取代暗色字幕條）', fill=STONE[0], font=F(ZH, 24))
# big numbers
box(60, UIY + 330, 420, UIY + 520, WHITE); d.text((90, UIY + 350), '413', fill=OUT, font=F(MONO, 110)); d.text((300, UIY + 440), '個檔', fill=STONE[0], font=F(ZH, 30))
box(450, UIY + 330, 760, UIY + 520, WHITE); d.text((480, UIY + 350), '61%', fill=GRN[1], font=F(MONO, 110))
d.text((60, UIY + 532), '大數字牌（成片改用像素字體）', fill=STONE[0], font=F(ZH, 24))
# bar chart blocks
bx = 820
for i, (lb, v, col) in enumerate((('只用搜尋', 53, STONE[1]), ('wiki＋搜尋', 61, GRN[1]))):
    y = UIY + 350 + i * 80; d.text((bx, y), lb, fill=OUT, font=F(ZH, 30))
    for k in range(v // 4):
        d.rectangle([bx + 200 + k * 24, y, bx + 220 + k * 24, y + 36], fill=OUT); d.rectangle([bx + 203 + k * 24, y + 3, bx + 217 + k * 24, y + 33], fill=col)
    d.text((bx + 210 + (v // 4) * 24, y), f'{v}%', fill=OUT, font=F(MONO, 34))
d.text((bx, UIY + 532), '方塊長條圖', fill=STONE[0], font=F(ZH, 24))
# level map
d.text((60, UIY + 590), '關卡地圖（記憶四層）', fill=OUT, font=F(ZH, 32))
names = ['① 逐字稿庫', '② 筆記佈告欄', '③ wiki 圖書館', '④ 最上層祭壇']; mp = {n: f for n, _, f in ITEMS}
for i, n in enumerate(names):
    x = 80 + i * 400; y = UIY + 640
    if i < 3:
        for k in range(12): d.rectangle([x + 110 + k * 24, y + 44, x + 124 + k * 24, y + 58], fill=OUT); d.rectangle([x + 113 + k * 24, y + 47, x + 121 + k * 24, y + 55], fill=GOLD[2] if k % 2 else WHITE)
    t = mp[n]().im.resize((T * 2, T * 2), Image.NEAREST)
    d.rectangle([x - 5, y - 5, x + T * 2 + 4, y + T * 2 + 4], fill=REDS[1] if i == 1 else OUT); sheet.paste(t, (x, y))
sheet.save('__DIR__/components.png'); print('ok', sheet.size, len(ITEMS))
