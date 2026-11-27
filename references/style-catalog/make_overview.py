"""Combine every style's sample.png into one overview grid (overview.png)."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
import sys
ALL = ['flat-vector', 'isometric', 'line-art', 'paper-cut', 'blueprint', 'neon-grid', 'soft-clay', 'riso-print', 'swiss-data', 'glass-ui',
         'chalkboard', 'ink-wash', 'watercolor', 'comic-halftone', 'low-poly', 'bauhaus', 'collage', 'woodblock', 'mid-century', 'pixel-city']
DONE = [s for s in ALL if os.path.exists(os.path.join(HERE, s, 'style.md'))]
ORDER = DONE if '--done' in sys.argv else ALL
OUT = 'overview_done.png' if '--done' in sys.argv else 'overview.png'
NAMES = {'flat-vector': '扁平向量', 'isometric': '等角立體', 'line-art': '線稿手繪', 'paper-cut': '剪紙層次', 'blueprint': '藍圖線框',
         'neon-grid': '霓虹網格', 'soft-clay': '柔軟黏土感', 'riso-print': '復古孔版印刷', 'swiss-data': '瑞士極簡資料風', 'glass-ui': '玻璃擬態介面',
         'chalkboard': '黑板粉筆', 'ink-wash': '水墨', 'watercolor': '水彩', 'comic-halftone': '漫畫網點', 'low-poly': '低多邊形',
         'bauhaus': '包浩斯幾何', 'collage': '拼貼編輯風', 'woodblock': '木刻版畫', 'mid-century': '世紀中期插畫', 'pixel-city': '像素科技城市'}
TW, TH, COLS, GAP, LAB = 360, 450, 5, 24, 56
F = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 30)
rows = (len(ORDER) + COLS - 1) // COLS
W = GAP + COLS * (TW + GAP); H = 110 + rows * (TH + LAB + GAP)
im = Image.new('RGB', (W, H), (238, 236, 230)); d = ImageDraw.Draw(im)
d.text((GAP, 30), f'風格目錄 {len(ORDER)} 種（同一題目：AI 助理把筆記卡放進知識庫，61%）', fill=(30, 30, 40), font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 44))
missing = []
for i, slug in enumerate(ORDER):
    x = GAP + (i % COLS) * (TW + GAP); y = 110 + (i // COLS) * (TH + LAB + GAP)
    p = os.path.join(HERE, slug, 'sample.png')
    if os.path.exists(p):
        im.paste(Image.open(p).convert('RGB').resize((TW, TH), Image.LANCZOS), (x, y))
    else:
        missing.append(slug); d.rectangle([x, y, x + TW, y + TH], fill=(210, 206, 198)); d.text((x + 120, y + 200), '尚未完成', fill=(90, 90, 90), font=F)
    d.text((x, y + TH + 10), f'{i + 1:02d} {NAMES[slug]}', fill=(30, 30, 40), font=F)
im.save(os.path.join(HERE, OUT))
print('ok', im.size, 'missing:', missing)
