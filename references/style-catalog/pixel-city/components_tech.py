"""v4 component sheet, TECH CITY edition: bright sci-fi city, robot agent. Reuses helpers from components.py."""
import math
src = open('__DIR__/components.py').read()
head, tail = src.split('# ---------- assemble sheet ----------')
exec(head)   # helpers + old items
OLD = {lb: (lb, sub, fn) for lb, sub, fn in ITEMS}
ITEMS.clear()

PLZ = [rgb('8fa0b8'), rgb('b8c4d6'), rgb('d5deea'), rgb('edf2f8')]
MET = [rgb('3a4260'), rgb('5d6a8a'), rgb('93a1bd'), rgb('d3dcea')]
GLS = [rgb('1b5f80'), rgb('2a9fc4'), rgb('6fe0ea'), rgb('d6fbfa')]
ROAD = [rgb('2a3050'), rgb('3a4266'), rgb('4c5682')]
MAG = [rgb('8a2a6e'), rgb('e0489a'), rgb('ff9ccb')]
ORG = [rgb('a8481c'), rgb('f0742e'), rgb('ffae5c'), rgb('ffe2b0')]
SH = [rgb('4a5478'), rgb('6a769c')]


def plaza(c, glow=True):
    for y in range(c.h):
        for x in range(c.w):
            n = noise(x, y) * .5 + .5
            col = PLZ[3] if dth(x, y, .55 + n * .3) else PLZ[2]
            if x % 14 == 0 or y % 14 == 0: col = PLZ[1]
            if x % 14 == 0 and y % 14 == 0: col = GLS[2] if glow else PLZ[0]
            c.put(x, y, col)
def tshadow(c, cx, cy, rx, ry):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1 and dth(x, y, .6): c.put(x, y, SH[1] if dth(x + 2, y + 1, .5) else SH[0])
def P(glow=True):
    c = C(bg=PLZ[2]); plaza(c, glow); return c
def lights(c, x0, y0, n, dx=3, cols=(GLS[2], GRN[2], ORG[2])):
    for k in range(n): c.put(x0 + k * dx, y0, cols[k % len(cols)])
def tower(c, x0, y0, x1, y1, ramp, win=None, rows=4):
    c.box(x0, y0, x1, y1, ramp[2], ramp[3], ramp[1])
    for y in range(y0, y1 + 1):
        for x in range(x1 - 3, x1 + 1):
            if dth(x, y, .5): c.put(x, y, ramp[1])
    if win:
        for r in range(rows):
            yy = y0 + 4 + r * ((y1 - y0 - 6) // rows)
            for x in range(x0 + 3, x1 - 3, 4): c.rect(x, yy, x + 2, yy + 2, win[(x + r) % len(win)])
def item(label, sub=''):
    def deco(fn): ITEMS.append((label, sub, fn)); return fn
    return deco


# ---------- city terrain ----------
@item('廣場地磚', '淺灰藍磚＋交點發光')
def _(): return P()
@item('光軌道路', '深色路面＋青色導引光')
def _():
    c = P()
    for y in range(T):
        for x in range(16, 41):
            c.put(x, y, ROAD[1] if dth(x, y, .5 + noise(x, y) * .3) else ROAD[0])
        c.put(15, y, OUT); c.put(41, y, OUT); c.put(17, y, GLS[2] if y % 6 < 4 else GLS[1]); c.put(39, y, GLS[2] if y % 6 < 4 else GLS[1])
        if y % 10 < 5: c.rect(28, y, 29, y, PLZ[3])
    for y in (10, 34):
        for k in range(4): c.rect(28 - k, y + k, 29 + k, y + k, GLS[3])
    return c
@item('資料水道', '流動的資料光點')
def _():
    c = P()
    for y in range(T):
        cx = 28 + math.sin(y * .14) * 5
        for x in range(int(cx - 11), int(cx + 12)):
            e = abs(x - cx) / 11
            c.put(x, y, GLS[3] if e > .86 else (GLS[2] if dth(x, y + y // 2, .45 + math.sin(y * .5 + x * .3) * .3) else GLS[1]))
        c.put(int(cx - 12), y, MET[1]); c.put(int(cx + 12), y, MET[1])
    for (x, y) in ((24, 8), (30, 20), (26, 33), (33, 44), (22, 48)): c.rect(x, y, x + 1, y + 1, WHITE); c.put(x + 2, y, GLS[3])
    return c
@item('全像樹', '金屬樹幹＋青色光葉')
def _():
    c = P(); tshadow(c, 30, 47, 15, 4); c.rect(26, 34, 29, 48, MET[2]); c.rect(26, 34, 26, 48, MET[1]); c.rect(24, 48, 31, 49, MET[0])
    c.blob(28, 22, 16, [GLS[0], GLS[1], GLS[2], GLS[3]], 3, dark=NAVY[1])
    for (x, y) in ((20, 14), (34, 18), (26, 28), (38, 26)): c.put(x, y, WHITE)
    return c
@item('天線塔', '訊號柱')
def _():
    c = P(); tshadow(c, 30, 49, 10, 3)
    for y in range(12, 50):
        w = 1 + (y - 12) * .16
        c.rect(28 - w, y, 28 + w, y, MET[2] if (y // 4) % 2 else MET[1]); c.put(28 - w - 1, y, OUT); c.put(28 + w + 1, y, OUT)
    c.rect(27, 4, 28, 12, MET[3]); c.sparkle(27, 3, ORG[2])
    for r, a0 in ((8, 200), (12, 200), (8, -20), (12, -20)):
        for a in range(a0, a0 + 50, 8): c.put(28 + round(r * math.cos(math.radians(a))), 8 + round(r * math.sin(math.radians(a)) * .6), GLS[1])
    return c
@item('植栽箱', '城市裡的一點綠')
def _():
    c = P(); tshadow(c, 30, 46, 20, 4); c.box(8, 30, 47, 44, MET[2], MET[3], MET[1]); c.rect(8, 40, 47, 40, GLS[2])
    c.blob(18, 24, 9, G, 4, lumps=4); c.blob(34, 22, 11, G, 8, lumps=4); c.flower(16, 20); c.flower(36, 18, WHITE); c.flower(30, 26, ORG[1]); return c
@item('感測燈柱', '路燈＋光暈')
def _():
    c = P()
    for y in range(4, 26):
        for x in range(14, 43):
            d = math.hypot(x - 28, y - 14)
            if 5 < d < 13 and dth(x, y, (13 - d) / 10): c.put(x, y, ORG[3])
    tshadow(c, 30, 49, 8, 3); c.rect(27, 18, 29, 49, MET[2]); c.rect(27, 18, 27, 49, MET[1]); c.rect(24, 49, 32, 50, MET[0])
    c.disc(28, 14, 6, lambda x, y, d: OUT if d > 4.8 else (WHITE if d < 2 else ORG[2])); return c
@item('光柵護欄', '圍出區域')
def _():
    c = P()
    for x in range(6, 52, 10): c.box(x, 22, x + 2, 36, MET[2], MET[3], MET[1]); c.put(x + 1, 21, GLS[2])
    for yy in (26, 31):
        for x in range(9, 46): c.put(x, yy, GLS[2] if x % 3 else WHITE)
    return c
@item('單向落差', '月見山：下得去、回不來')
def _():
    c = P()
    for y in range(22, 40):
        for x in range(T):
            t = (y - 22) / 18; c.put(x, y, MET[2] if dth(x, y, 1 - t) and x % 8 else (MET[1] if dth(x, y, 1.25 - t) else MET[0]))
    c.rect(0, 21, T, 21, OUT); c.rect(0, 22, T, 22, GLS[2]); c.rect(0, 40, T, 40, OUT)
    for y in range(41, 47):
        for x in range(T):
            if dth(x, y, .7 - (y - 41) * .1): c.put(x, y, SH[0])
    for ax in (14, 28, 42):
        for k in range(4): c.rect(ax - k, 27 + k, ax + k, 27 + k, ORG[2])
        c.rect(ax - 1, 31, ax + 1, 36, ORG[2])
    return c
@item('全像路牌', '月見山／華藍市／尼比市')
def _():
    c = P(); tshadow(c, 30, 49, 9, 3); c.rect(27, 28, 29, 49, MET[2]); c.rect(27, 28, 27, 49, MET[1])
    c.box(8, 10, 47, 27, NAVY[1], NAVY[2], NAVY[0]); c.rect(8, 10, 47, 10, GLS[2])
    for i, x in enumerate((12, 18, 24, 30, 36)): c.rect(x, 16 + (i % 2) * 5, x + 4, 17 + (i % 2) * 5, GLS[2])
    c.rect(42, 14, 44, 16, ORG[2]); return c
@item('城市閘門', '抵達城市的終點')
def _():
    c = P(); tshadow(c, 28, 50, 24, 4)
    for x0 in (5, 39): tower(c, x0, 14, x0 + 11, 48, MET); c.rect(x0 + 4, 18, x0 + 6, 44, GLS[2]); c.rect(x0 + 5, 18, x0 + 5, 44, WHITE)
    c.box(17, 10, 38, 18, NAVY[1], NAVY[2], NAVY[0]); lights(c, 20, 14, 6)
    for y in range(20, 48, 3): c.rect(18, y, 37, y, GLS[2] if (y // 3) % 2 else GLS[3])
    return c
@item('充電艙', '一次工作階段')
def _():
    c = P(); tshadow(c, 28, 49, 20, 4); c.box(10, 34, 45, 47, MET[2], MET[3], MET[1])
    for y in range(8, 34):
        w = 15 * math.sqrt(max(0, 1 - ((33 - y) / 26) ** 2))
        for x in range(int(28 - w), int(28 + w) + 1): c.put(x, y, GLS[3] if x < 28 - w * .45 else (GLS[2] if dth(x, y, .6) else GLS[1]))
        c.put(int(28 - w) - 1, y, OUT); c.put(int(28 + w) + 1, y, OUT)
    c.rect(22, 7, 34, 7, OUT); c.rect(12, 40, 43, 40, ORG[2]); lights(c, 14, 44, 10); return c

# ---------- four memory layers ----------
@item('① 逐字稿資料中心', '伺服器機櫃，保存所有原始紀錄')
def _():
    c = P(); tshadow(c, 30, 50, 24, 4); tower(c, 4, 10, 51, 48, MET)
    for k in range(4):
        x0 = 7 + k * 11; c.box(x0, 15, x0 + 8, 44, NAVY[1], NAVY[2], NAVY[0])
        for r in range(6):
            c.rect(x0 + 1, 18 + r * 4, x0 + 5, 18 + r * 4, MET[1]); c.put(x0 + 7, 18 + r * 4, (GRN[2], GLS[2], ORG[2])[(k + r) % 3])
    c.rect(4, 10, 51, 11, GLS[2]); return c
@item('② 筆記終端', 'Agent 自己寫下的筆記')
def _():
    c = P(); tshadow(c, 30, 50, 20, 4); c.box(22, 38, 33, 48, MET[2], MET[3], MET[1]); c.box(14, 46, 41, 49, MET[1], MET[2], MET[0])
    c.box(6, 8, 49, 38, NAVY[1], NAVY[2], NAVY[0]); c.rect(6, 8, 49, 8, GLS[2])
    for (x, y, col) in ((10, 12, PAPER[2]), (23, 12, ORG[3]), (36, 12, PAPER[2]), (10, 25, PAPER[2]), (23, 25, GLS[3]), (36, 25, PAPER[2])):
        c.rect(x, y, x + 9, y + 9, col); c.rect(x + 1, y + 2, x + 7, y + 2, MET[1]); c.rect(x + 1, y + 4, x + 5, y + 4, MET[1]); c.rect(x + 1, y + 6, x + 7, y + 6, MET[1])
    return c
@item('③ wiki 塔', '筆記連成知識網的玻璃塔')
def _():
    c = P(); tshadow(c, 32, 51, 20, 4)
    tower(c, 12, 20, 43, 49, GLS, win=(WHITE, GLS[3], ORG[2]), rows=4); tower(c, 18, 8, 37, 20, GLS)
    c.rect(27, 2, 28, 8, MET[2]); c.sparkle(27, 1, GLS[2])
    N = ((22, 12), (33, 11), (28, 17), (24, 16))
    for a, b in ((0, 1), (0, 2), (1, 2), (3, 2)): c.line(N[a][0], N[a][1], N[b][0], N[b][1], WHITE)
    for (x, y) in N: c.rect(x - 1, y - 1, x + 1, y + 1, ORG[2])
    c.box(24, 40, 31, 49, NAVY[1]); c.rect(27, 41, 28, 49, GLS[2]); return c
@item('④ 最上層信標', '每次都先載入，只放最重要的')
def _():
    c = P(); tshadow(c, 28, 49, 20, 4)
    for i, (hw, y0) in enumerate(((20, 42), (15, 36), (10, 30))): c.box(28 - hw, y0, 27 + hw, y0 + 5, MET[2], MET[3], MET[1]); c.rect(28 - hw, y0 + 5, 27 + hw, y0 + 5, GLS[2])
    for y in range(4, 28):
        for x in range(14, 43):
            d = math.hypot(x - 28, y - 16)
            if 7 < d < 14 and dth(x, y, (14 - d) / 10): c.put(x, y, ORG[3])
    for dy in range(11):
        w = 6 - abs(dy - 5)
        for x in range(28 - w, 28 + w): c.put(x, 11 + dy, ORG[3] if x < 27 else (ORG[2] if x < 29 else ORG[1]))
        c.put(28 - w - 1, 11 + dy, OUT); c.put(28 + w, 11 + dy, OUT)
    c.put(26, 13, WHITE); c.put(27, 12, WHITE); c.rect(27, 10, 28, 10, OUT); c.rect(27, 22, 28, 22, OUT); return c
@item('記憶保險庫', '跨工作階段保留下來')
def _():
    c = P(); tshadow(c, 28, 49, 22, 4); tower(c, 8, 12, 47, 47, MET)
    c.disc(28, 30, 14, lambda x, y, d: OUT if d > 12.8 else (MET[3] if d > 10 and (x + y) < 56 else (MET[1] if d > 10 else (NAVY[1] if d > 3.5 else ORG[2]))))
    for a in range(0, 360, 45): c.line(28 + 4 * math.cos(math.radians(a)), 30 + 4 * math.sin(math.radians(a)), 28 + 9 * math.cos(math.radians(a)), 30 + 9 * math.sin(math.radians(a)), MET[2])
    lights(c, 11, 15, 4); c.rect(8, 12, 47, 12, GLS[2]); return c
@item('MEMORY.md 面板', '只載入前 200 行')
def _():
    c = P(); tshadow(c, 28, 49, 16, 3); c.box(12, 8, 43, 46, NAVY[1], NAVY[2], NAVY[0]); c.rect(12, 8, 43, 8, GLS[2])
    for k, w in enumerate((22, 18, 24, 14, 20, 16)): c.rect(16, 13 + k * 4, 15 + w, 14 + k * 4, ORG[2] if k == 0 else GLS[2])
    c.rect(12, 37, 43, 37, ORG[1])
    for k in range(2): c.rect(16, 40 + k * 3, 36 - k * 6, 40 + k * 3, MET[1])
    return c

# ---------- items (re-skinned on plaza) ----------
def reskin(lb, sub=None):
    o = OLD[lb]
    def fn():
        c0 = o[2](); c = P(glow=False) if False else C(bg=PLZ[2]); plaza(c, False)
        # copy non-sand pixels of the old sprite onto the plaza
        for y in range(T):
            for x in range(T):
                p = c0.p[x, y]
                if p not in (SAND[1], SAND[2], SAND[0]) and p not in (PUR[0], PUR[1]): c.p[x, y] = p
                elif p in (PUR[0], PUR[1]): c.p[x, y] = SH[0] if p == PUR[0] else SH[1]
        return c
    ITEMS.append((lb, sub or o[1], fn))
for lb, sub in (('筆記', '資料卡：一般'), ('筆記（寫錯）', '紅框＋叉'), ('筆記（已驗證）', '綠框＋勾'), ('wiki 頁面連結', None), ('金幣', None), ('地圖釘', None), ('徽章', None), ('陀螺', None), ('放大鏡', None)):
    reskin(lb, sub)
@item('紀錄磁帶', '逐字稿：原始事件紀錄')
def _():
    c = P(False); tshadow(c, 28, 48, 20, 3); c.box(8, 14, 47, 44, NAVY[1], NAVY[2], NAVY[0]); c.box(12, 18, 43, 32, MET[3], WHITE, MET[2])
    for cx in (20, 36):
        c.disc(cx, 25, 6, lambda x, y, d: OUT if d > 4.8 else (MET[1] if d > 2 else WHITE))
    c.rect(24, 24, 32, 26, WOOD[1]);
    for k in range(7): c.rect(12 + k * 5, 37, 14 + k * 5, 40, GLS[2] if k % 2 else ORG[2])
    return c
ITEMS.append(OLD['月亮'])

# ---------- robot agent ----------
def robot(c, cx, cy, state='idle'):
    dream = state == 'dream'
    body = MET; acc = ORG
    if not dream: tshadow(c, cx + 1, cy + 19, 12, 3)
    # antenna
    c.rect(cx, cy - 20, cx, cy - 15, OUT); tip = {'idle': ORG[1], 'active': ORG[3], 'think': GLS[2], 'dream': NAVY[2]}[state]
    c.rect(cx - 1, cy - 22, cx + 1, cy - 20, OUT); c.put(cx, cy - 21, tip)
    if state == 'active':
        for a in range(0, 360, 45): c.put(cx + round(4 * math.cos(math.radians(a))), cy - 21 + round(4 * math.sin(math.radians(a))), ORG[2])
    # head
    c.box(cx - 9, cy - 14, cx + 9, cy - 2, body[3], WHITE, body[2])
    c.rect(cx - 9, cy - 3, cx + 9, cy - 2, body[2]); c.rect(cx + 7, cy - 14, cx + 9, cy - 2, body[2])
    # visor band (no cartoon eyes)
    c.rect(cx - 7, cy - 11, cx + 7, cy - 6, OUT); c.rect(cx - 6, cy - 10, cx + 6, cy - 7, NAVY[0])
    if state == 'idle': c.rect(cx - 5, cy - 9, cx + 5, cy - 8, GLS[2]); c.rect(cx - 5, cy - 9, cx - 3, cy - 9, WHITE)
    if state == 'active': c.rect(cx - 6, cy - 10, cx + 6, cy - 7, GLS[2]); c.rect(cx - 5, cy - 10, cx + 5, cy - 9, GLS[3]); c.rect(cx - 5, cy - 10, cx - 2, cy - 10, WHITE)
    if state == 'think':
        for k in range(3): c.rect(cx - 5 + k * 4, cy - 9, cx - 4 + k * 4, cy - 8, GLS[2] if k != 1 else WHITE)
    if dream: c.rect(cx - 5, cy - 8, cx + 5, cy - 8, NAVY[2])
    # ear bolts
    for sx in (-1, 1): c.rect(cx + sx * 11 - 1, cy - 10, cx + sx * 11 + 1, cy - 6, OUT); c.put(cx + sx * 11, cy - 8, body[2])
    # body
    c.box(cx - 7, cy, cx + 7, cy + 12, body[2], body[3], body[1]); c.rect(cx + 5, cy, cx + 7, cy + 12, body[1])
    # chest core
    cc = {'idle': acc[1], 'active': acc[3], 'think': acc[2], 'dream': GOLD[2]}[state]
    c.rect(cx - 3, cy + 3, cx + 3, cy + 9, OUT); c.rect(cx - 2, cy + 4, cx + 2, cy + 8, cc)
    if dream: c.rect(cx, cy + 4, cx + 2, cy + 6, NAVY[1])   # crescent core
    else: c.put(cx - 2, cy + 4, WHITE)
    if state == 'active':
        for y in range(cy - 2, cy + 15):
            for x in range(cx - 14, cx + 15):
                d = math.hypot(x - cx, y - cy - 6)
                if 9 < d < 14 and dth(x, y, (14 - d) / 8) and c.p[x, y] in (PLZ[1], PLZ[2], PLZ[3]): c.put(x, y, ORG[3])
    # arms
    ay = cy + 2 if state != 'active' else cy - 1
    for sx in (-1, 1):
        c.rect(cx + sx * 9 - 1, ay, cx + sx * 9 + 1, ay + 8, OUT); c.rect(cx + sx * 9, ay + 1, cx + sx * 9, ay + 7, body[2])
        c.rect(cx + sx * 9 - 1, ay + 8, cx + sx * 9 + 1, ay + 10, OUT); c.put(cx + sx * 9, ay + 9, acc[1])
    # treads
    c.box(cx - 8, cy + 14, cx + 8, cy + 18, NAVY[1], NAVY[2], NAVY[0])
    for x in range(cx - 7, cx + 8, 3): c.put(x, cy + 16, body[2])
    if state == 'think':
        for k, (dx, dy) in enumerate(((13, -18), (17, -23), (22, -27))): c.rect(cx + dx, cy + dy, cx + dx + k, cy + dy + k, GLS[2]);
    if dream:
        for k, (dx, dy) in enumerate(((12, -16), (17, -21))): c.rect(cx + dx, cy + dy, cx + dx + 3, cy + dy, WHITE); c.line(cx + dx + 3, cy + dy, cx + dx, cy + dy + 3, WHITE); c.rect(cx + dx, cy + dy + 3, cx + dx + 3, cy + dy + 3, WHITE)
        for (dx, dy) in ((-16, -18), (-19, 4), (20, 8)): c.sparkle(cx + dx, cy + dy)
for st, lb, sub in (('idle', '機器人：待機', '護目鏡微亮、核心橘色'), ('active', '機器人：工作中', '護目鏡全亮、核心放光'),
                    ('think', '機器人：思考', '護目鏡跑三點'), ('dream', '機器人：做夢', '護目鏡熄成線、核心月牙')):
    def mk(st=st):
        c = C(bg='night') if st == 'dream' else P(); robot(c, 28, 28, st); return c
    ITEMS.append((lb, sub, mk))
for lb in ('固定規則的籠子', '用途指標'):
    o = OLD[lb]
    def fn(o=o):
        c0 = o[2](); c = P(False)
        base = C()   # plain grass to diff against
        for y in range(T):
            for x in range(T):
                p = c0.p[x, y]
                if p != base.p[x, y]: c.p[x, y] = SH[0] if p == PUR[0] else (SH[1] if p == PUR[1] else p)
        return c
    ITEMS.append((lb, o[1], fn))

tail = tail.replace('v4 全部元件（俯視角抖色像素風・全部原創）', 'v4 全部元件：科技城市版（全部原創）')
tail = tail.replace("names = ['① 逐字稿庫', '② 筆記佈告欄', '③ wiki 圖書館', '④ 最上層祭壇']", "names = ['① 逐字稿資料中心', '② 筆記終端', '③ wiki 塔', '④ 最上層信標']")
tail = tail.replace("sheet = Image.new('RGB', (W, H), rgb('f4efe1'))", "sheet = Image.new('RGB', (W, H), rgb('eef2f8'))")
tail = tail.replace('components.png', 'components_tech.png')
exec(tail)
