# 高質感 UI 微動態：library/ui.js、library/uictl.js

產品片裡「A → B」的瞬間：數字從 0 跳到 12,480、按鈕從 Publish 變成綠色 Published、行程拖進空檔、卡片插進刷卡機變 Paid。
外觀是浮起的白色玻璃卡片、柔和大陰影、粗體大數字、藍綠強調色。寫法看 `examples/ui-data-demo`、`examples/ui-controls-demo`。

**原則**（motion-design.md）：一個畫面只演一件事、一個主角；A 狀態先停半拍讓觀眾看懂，再變成 B；變化那一拍配 `pop`、`click`、`chime` 音效。
介面裡的字一律 `txtB(…, { ui: true, maxW })`；顏色用 `STYLE.c.a1／a2` 或 `UIC`（`ok`、`okDark`、`warn`、`bad`、`ink`、`sub`）。

## 卡片與數據（ui.js）

| 函式 | 用途 |
|---|---|
| `uiCard(x, y, w, h, { r, lift, glow, fill })` | 浮起的玻璃卡片（三層柔和陰影、頂部微光） |
| `uiIn(t, start, cx, cy, draw, o)` | 彈簧進場（放大＋上滑＋淡入），把畫卡片的函式包進去 |
| `uiBack(p, s)` | 帶過衝的緩動 |
| `uiCount(t, start, dur, from, to, { pre, post, dp, ease })` | 數字滾動字串（千分位、小數位、前後綴） |
| `uiKPI(x, y, w, h, t, o)` | KPI 卡：圖示、標題、大數字滾動、成長標籤、走勢線 |
| `uiBadge(x, y, s, p, { col, arrow, align })` | 成長標籤膠囊（「+18% this month」） |
| `uiResult(cx, cy, s, p, { bump })` | 白色結果膠囊（「447 sales」） |
| `uiCheck(x, y, r, p, { col, bg, burst })` | 打勾（圓底彈出、筆畫畫出） |
| `uiBars(x, y, w, h, values, p, q, { labels, col, trend })` | 長條錯開長出、再畫平滑趨勢線與發光端點 |
| `uiSpark(x, y, w, h, values, p, o)` | 走勢線（漸層面積、發光端點） |
| `uiGoalRings(cx, cy, r, ps, o)` | 同心目標環，閉合時發光 |
| `uiParticlesTo(t, start, dur, src, dst, o)` | 粒子沿弧線匯聚到目標（流量 → 轉換） |
| `uiMap(x, y, w, h, o)`、`uiPin(x, y, s, p)`、`uiRoute(pts, p, o)` | 抽象地圖、掉落的圖釘、依序畫出的路線 |
| `uiPriceCard(cx, cy, w, h, a, o)` | 價格卡 360° 翻轉（可有原價刪除線） |
| `uiSlider(x, y, w, p, o)` | 滑桿（數值泡泡） |
| `uiWeight(cx, cy, word, p, o)` | 大字字重從細變粗 |
| `uiIcon(cx, cy, s, glyph, col)`、`uiIconTile(x, y, s, glyph, o)`、`uiDot(x, y, r, col)` | 線條圖示、漸層 App 圖示磚、發光脈動點 |

## 互動與狀態（uictl.js）

| 函式 | 用途 |
|---|---|
| `uiPress(t, at, amt)` | 按下的擠壓回彈 → `{sx, sy}` |
| `uiGlass(x, y, w, h, r, o)` | 毛玻璃卡片 |
| `uiToggle(x, y, w, p, o)`、`uiSegment(x, y, w, h, labels, p, { light })` | 開關、分段切換（Monthly／Yearly） |
| `uiButton(cx, cy, w, h, t, tPress, tDone, { label, doneLabel })` | 按鈕：按下 → 載入 → 綠色完成＋打勾 |
| `uiRoll(from, to, x, y, t, at, o)` | 數字翻牌（只有變的位數往上翻） |
| `uiPill(cx, cy, s, t, at, { kind: 'live'｜'ok'｜'dot', solid, align })` | 狀態膠囊（LIVE 紅點、Paid、Published） |
| `uiBurst(cx, cy, r, t, at, o)` | 成功的放射短線 |
| `uiRing(cx, cy, r, p, { label, sub, col })` | 進度環（中央文字、端點白點） |
| `uiToasts(x, y, w, items, t, o)`、`uiNotifStack(x, y, w, items, t, o)` | 通知彈入、往下疊，最後收成摘要（「12 new orders」） |
| `uiIsland(cx, y, s, p, o)` | 動態島展開成即時動態 |
| `uiLockScreen(box, t, o)` | 手機鎖屏（時間＋通知），放進 `framePhone` 的螢幕 |
| `uiCreditCard(cx, cy, w, o)`、`uiPOS(cx, cy, w, paid, o)` | 信用卡、刷卡機（金額 → 綠色 Approved） |
| `uiWireMorph(x, y, w, h, p, o)` | 線框逐塊填滿成 App 畫面 |
| `uiCalendar(x, y, w, h, o)`、`uiEventBlock(…)`、`uiDragSnap(t, t0, t1, a, b)` | 週行事曆、行程方塊、拖曳後吸附 |
| `uiDock(cx, by, s, icons, t, o)`、`uiAppIcon(cx, cy, s, it)`、`uiOpenFrom(…)` | Dock 放大彈跳、App 圖示、從圖示展開視窗 |
| `uiGlyph(kind, cx, cy, s, col)` | 15 種小圖示（check、doc、chat、mail、cal、chart…） |

## 效能
陰影與漸層很吃效能：同一個畫面的卡片控制在 6 張以內；背景用 `backdrop(t)`（已降解析度繪製）或預先烘焙的背景，不要每格畫全螢幕漸層。
