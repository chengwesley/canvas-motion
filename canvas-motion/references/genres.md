# 類型指南：美漫、港漫、日式動畫、電影

選類型 = 選風格錨點（`styles/`）＋一組特效（`library/fx.js`）＋一套規則。不要混類型（美漫頭身配大眼卡通臉會很假）。

| 類型 | 錨點 | 人物 `props`／`render` | 招牌特效 | 字 |
|---|---|---|---|---|
| 美漫（英雄、活動） | `amcomic`：新聞紙底、四色網點 | `hero`／`amcomic` | `fxHalftone`（網角 C105° M75° Y90° K45°）、`fxKrackle`、爆炸框、平行速度線 | `fxSFX`（BAM、KRAK，厚字＋描邊）、`fxBalloon`（shout／thought／radio） |
| 港漫（武俠、熱血） | `hkcomic`：深藍紫夜色、金色輪廓光 | `hk` 或 `teen`／`hkcomic`（排線陰影＋邊光） | `fxAura`（氣勁，白核→彩色外緣）、`fxFocusLines`、斜格 `fxPanels('action')`、眼睛特寫條 `fxPanels('strip')` | 大狀聲字（轟、砰、嘭），旁白框 `fxCaption`（明體 `fam: 'serif'`） |
| 日式動畫（作畫、動作） | 任何暗底錨點 | `anime`／`teen`＋`anime`（雙色分色＋高光） | 衝擊幀 `fxImpact`＋`fxInvert`、抹影 `smear`、集中線、流線 `fxFlowLines`、`onTwos`、火／煙／火花／閃電 | 字少，靠畫面 |
| 電影（故事、形象） | `cinema`：寬銀幕 2.39、青橙調色、顆粒 | `real`／`anime`＋`cel` | `fxLetterbox`（錨點自帶）、`fxRays`、`fxFlare`、`layer()` 景深、甩鏡（流線＋暗化） | 字幕 `txt` 放畫面下方、片名 `fxTitle`（細字寬字距） |

## 各類型的節奏
- **動漫動作**：慢–極快–停。預備 6–12 格、出招 2–4 格（幾乎沒有中間張）、命中停 4–8 格（hit-stop）、餘波 8–16 格。
- **漫畫**：一格鋪陳、一格爆發；爆發格用斜格或出格。
- **電影**：鏡頭長度隨情緒變化，高潮前剪得越來越快，最後一擊前 1–2 拍靜默（`rest`），黑場或慢推後再爆發。

## 常見的假與業餘
- 均勻線寬；陰影只調暗不偏色（動漫影子要往藍紫偏）；網點角度全部一樣。
- 集中線中心沒留空、線條靜止不動；煙和火用淡出而不是變形消散。
- 衝擊幀、白閃用太多（**光敏安全：全畫面閃光每秒不超過 3 次**）。
- 震動每格都隨機、沒有衰減；所有東西都發光（發光只給光源與特效）。
- 港漫用了缺字的簡中字型（Zhi Mang Xing、Ma Shan Zheng 只有簡中）。錨點已選好有繁中／港字的 OFL 字型（Chiron Hei HK、Noto Serif HK）。
