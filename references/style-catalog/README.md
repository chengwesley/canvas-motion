# 風格目錄

做插畫感的知識影片前，先從這裡挑風格，再給使用者看樣張確認。每種風格一個資料夾：

- `sample.png`：同一個題目的樣張（AI 助理把筆記卡放進知識庫，旁邊一個大數字 61%），方便互相比較
- `sample.py`：產生樣張的程式（Python＋PIL），也是這個風格的畫法起點
- `style.md`：風格指引（指標畫法、代表畫家與作品、配色色階、光影、線條、質感、比例、字體、動態、元件清單、常見失敗、原創界線）

總覽圖：`overview_done.png`（已有完整指引的風格）、`overview.png`（全部 20 種，含只有樣張的）。重新產生：`python3 make_overview.py --done`、`python3 make_overview.py`。

## 狀態

| 風格 | 資料夾 | 指引 |
|---|---|---|
| 扁平向量 | flat-vector | 完整 |
| 線稿手繪 | line-art | 完整 |
| 剪紙層次 | paper-cut | 完整 |
| 藍圖線框 | blueprint | 完整 |
| 霓虹網格 | neon-grid | 完整 |
| 復古孔版印刷 | riso-print | 完整 |
| 漫畫網點 | comic-halftone | 完整 |
| 拼貼編輯風 | collage | 完整 |
| 木刻版畫 | woodblock | 完整 |
| 像素科技城市 | pixel-city | 完整（另有 `components.png` 元件表與元件程式） |
| 等角立體 | isometric | 只有樣張 |
| 柔軟黏土感 | soft-clay | 只有樣張 |
| 瑞士極簡資料風 | swiss-data | 只有樣張 |
| 玻璃擬態介面 | glass-ui | 只有樣張 |
| 黑板粉筆 | chalkboard | 只有樣張 |
| 水墨 | ink-wash | 只有樣張（小字有缺字） |
| 水彩 | watercolor | 只有樣張（小字有缺字） |
| 低多邊形 | low-poly | 只有樣張 |
| 包浩斯幾何 | bauhaus | 只有樣張 |
| 世紀中期插畫 | mid-century | 只有樣張（小字有缺字） |

## 補一種風格時

照已完成的 `style.md` 的段落格式寫，色碼要跟 `sample.py` 一致。中文字只用 STHeiti Medium 或 Hiragino Sans GB，其他字型常缺繁體字。代表畫家與作品只列有把握的，不確定的在該行標「（待查證）」。主角是機器人或機械形體，不畫有眼睛嘴巴的卡通臉。

## 注意

- 各 `style.md` 的「代表畫家與作品」是 AI 依知識寫的，尚未逐條查證；標「待查證」的尤其要核對。
- 參考畫家只用來學技法，不照畫他們的構圖、角色或招牌圖樣。
