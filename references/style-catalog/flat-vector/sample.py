#!/usr/bin/env python3
"""flat-vector sample (original artwork): an AI agent slides a note card into the
knowledge base's card drawer; big number 61% beside it. Composed from components.py."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from components import *

W, H = 1080, 1350
PINK = ramp('F0A9A4', 'F7C3BC', 'FBD8D2', 'FDEAE6')   # Blair pink disc
GROUND = 1052                      # bottom ~22% (298 px) is calm floor for subtitles


def main():
    cv = Canvas(W, H, BG[1])
    # backdrop: one big sun disc (two flat steps) behind the action, floor band
    # Bass: one big hard-cut diagonal shard (pale teal) cuts the upper-right of the wall as one triangle
    cv.d.polygon([(x * S, y * S) for x, y in ((520, 0), (W, 0), (W, 600))], fill=TEAL[3])
    # Blair: unexpected pairing - pink disc, light-mustard core, against the teal/navy
    cv.d.ellipse([s * S for s in (150, 330, 870, 1050)], fill=PINK[1])    # disc frames the action
    cv.d.ellipse([s * S for s in (250, 430, 770, 950)], fill=MUST[3])
    cv.d.rectangle([0, GROUND * S, W * S, H * S], fill=FLOOR[1])
    cv.d.rectangle([0, GROUND * S, W * S, (GROUND + 10) * S], fill=FLOOR[0])

    # knowledge base (right) with the new card inside the drawer slot
    grip = {}
    shelf = Layer(W, H)

    def insert(L, slot):
        cw, chh = 118, 164
        cx = slot['x']; top = slot['row'][0] + 26; cy = top + chh / 2
        card(L, cx, cy, cw, chh, deg=0)
        grip['p'] = (cx - cw / 2 + 4, top + 62)              # hand on the left edge, header stays visible
        x = cx + cw / 2 + 30                                   # motion chevrons: "down, into"
        for j in range(2):
            y = top + 22 + j * 30
            L.fline([(x - 12, y - 8), (x, y + 4), (x + 12, y - 8)], 7, MUST[2])

    SX = 515
    kb_shelf(shelf, SX, 360, SX + 430, 1030, insert=insert, slot_frac=.3, card_w=118,
             fracs=(.29, .29, .42), drawer=2, front=.6, simple=True)
    plant(shelf, SX + 361, 336, k=.9)

    # agent (left of the shelf), right hand on the card's edge
    bot = Layer(W, H)
    RX = 340
    robot(bot, RX, GROUND, 'reach', hand=grip['p'], hand_l=(RX - 126, GROUND - 98))

    # type block: chapter rule + heading, big number, progress capsule, one label
    txt = Layer(W, H)
    txt.frr(78, 70, 150, 82, 6, CORAL[1])
    txt.text('知識庫', 74, 100, 66, NAVY[1])
    num = Layer(W, H)
    num.text('61%', 68, 176, 184, CORAL[1], NUM, NUM_HEAVY)
    big_bar(num, 80, 412, 390, 24, .61)
    txt.text('筆記已歸檔', 80, 456, 32, NAVY[2])

    # shadows: hard, one tone, 45 degrees, only on the wall
    wall = (0, 0, W, GROUND)
    cv.cast(shelf, 26, clip=wall)
    cv.cast(bot, 22, clip=wall)
    cv.contact(RX, GROUND + 4, 230, 12)
    cv.contact(SX + 215, GROUND + 4, 470, 12)
    for lay in (shelf, bot, num, txt): cv.put(lay)
    cv.final().save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.png'))


if __name__ == '__main__':
    main()
