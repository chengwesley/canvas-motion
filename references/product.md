# 產品介紹與操作示範

做產品介紹、功能展示、操作示範（「怎麼用」）、上線公告時讀這份。

做法參考了 HyperFrames（先擷取真實網站再動手、擷取失敗就停）、Screen Studio／OpenScreen（點擊自動推近、浮起的視窗配漸層桌布）、21st.dev 游標元件與 remocn（游標 → 按下 → 漣漪 → 介面反應的動作語彙）、digitalsamba toolkit（品牌設定檔）。

完整範例與回歸測試：`examples/product-demo`（虛構產品 Notely：本機頁面 `source/page.html` 擷取成截圖 → 瀏覽器外框、游標、點擊推近、聚光與標籤 → 程序化編輯器裡拖曳、打字、打勾 → 旁白與字幕）。

## 1. 素材先行：先擷取真實畫面

產品片最常見的失敗，是憑印象畫出一個「看起來像」的介面，結果按鈕位置、文案、顏色都和真的產品不一樣。動手前先拿到真實畫面：

```bash
python3 <SKILL>/scripts/capture.py https://產品網址 <專案> --name home --brand <品牌>   # 截圖＋頁面文字＋品牌色
python3 <SKILL>/scripts/capture.py https://產品網址/pricing <專案> --name pricing --full  # 長截圖
python3 <SKILL>/scripts/capture.py --file 使用者給的截圖.png <專案> --name editor          # 登入後的畫面
```

- **截圖預設 2 倍像素**（`--scale 2`），鏡頭推近 2 倍仍清楚。手機版用 `--size 390x844 --scale 3`。
- **頁面文字會附加到 `source.txt`**，build 用它追溯數字；文案只能用這裡或使用者素材裡有的字。
- **擷取失敗會寫 `assets/BLOCKED.md` 並停下**（打不開、HTTP 錯誤、登入頁、找不到要點的元素）。這時請使用者提供截圖或公開網址，**不要自己畫一個假的產品畫面冒充真實介面**。
- **需要登入的產品畫面**（編輯器、後台）：請使用者自己截圖後用 `--file` 匯入。不要替使用者登入。
- Cookie 視窗與客服聊天浮窗只用 CSS 隱藏，不替使用者按「同意」。
- `--brand <名稱>` 會依網站上按鈕、標題、連結的使用量推出 a1–a3 與字型，存成 `brands/<名稱>.json`。**這是推測值**：提案時把色碼給使用者確認，有官方色碼就直接改檔。之後 storyboard 的 `style` 寫 `{ "base": "minimal", "brand": "<名稱>" }` 就會套用（自己寫的 colors 優先）。

## 2. 真實截圖還是重畫介面？

| 情況 | 做法 |
|---|---|
| 要讓觀眾認得「就是這個產品」（官網、主畫面、定價頁） | 真實截圖：`pic()` 放進 `frameBrowser`／`framePhone` |
| 要示範一個操作的過程（拖曳、填欄位、按下後跳出結果） | 截圖當底，游標與標註疊在上面；狀態變化（跳出視窗、打勾）用程式畫在截圖上 |
| 介面太雜、只想講一個概念 | 程序化重畫成**簡化示意**：只畫素材裡看得到的元素與文字，顏色用 `UI.*` 與品牌色。不要加出產品沒有的功能 |
| 沒有任何截圖、也擷取不到 | 停下來要素材（見第 1 節）；或改成不畫介面的概念畫面 |

## 3. 敘事：產品片的兩種骨架（起點，不是範本）

| 類型 | 骨架 | 高光 |
|---|---|---|
| 產品介紹（20–45 秒） | 痛點（不用產品時的麻煩）→ 產品登場（真實畫面）→ 2–3 個關鍵功能，每個一個操作 → 成果（素材裡的證據）→ 行動（網址、按鈕） | 最關鍵的那一次點擊：按下後問題消失 |
| 操作示範（30–90 秒） | 目標（要完成什麼）→ 步驟 1…N，每步一個鏡頭 → 完成畫面 → 下一步 | 最容易卡住的那一步 |

- **一幕只示範一個操作**，`say` 寫「做了什麼、得到什麼」。步驟太多就拆片，不要每步壓到 1 小節。
- **高光是因果**：按下 → 介面變了。高光拍點放在「介面反應」那一格，不是游標移動途中。
- **延續**：上一幕的截圖推近成下一幕的特寫、按下的按鈕變成下一幕的視窗，比換一張新截圖有力。
- **旁白**：產品片幾乎都適合加旁白與字幕（每幕 `vo`，見 `references/voice.md`）。旁白講為什麼、畫面演怎麼做；說到「按下」的那一拍游標按下。

## 4. 示範的動作語彙

一個完整的操作節拍：**游標移過去 → 鏡頭推近 → 按下（縮一下＋漣漪＋click 音效）→ 介面反應 → 聚光／標籤 → 拉回或平移到下一個操作**。

- **游標像人手**：`cursorAt()` 兩點之間沿微彎弧線、起步慢、抵達前減速。移動 0.4–0.8 秒；太快看不清，太慢拖節奏。到位後停半拍再按。
- **鏡頭跟動作**：`camFromClicks()` 由點擊自動產生鏡頭，推近 1.5–2 倍（直式 1.3–1.6）。連續的操作直接平移、不要每次拉回全景。只想讓觀眾看清楚、不點擊的地方加 `focus: true`。
- **按下要有回饋**：`drawCursor` 自帶漣漪，`sfx` 在同一拍放 `click`；介面的反應（按鈕變色、彈出視窗）用 `spring()` 彈出來，不要淡入。
- **打字**：`typing()` 每秒 10–16 字，中文一字一個；打完游標閃爍半拍再進下一步。
- **標註少而準**：一個畫面最多一個 `spotlight` 或兩個 `callout`。標籤文字用素材裡的功能名稱。
- **停住時不要完全靜止**：`follow()` 推近時預設會輕微呼吸（`breathe`），背景用 `backdrop(t)` 緩慢漂移。

## 5. 版面

- **浮起的視窗配漸層桌布**：`backdrop(t)` 當背景，視窗用 `frameBrowser`／`frameWindow`，陰影會自動畫。視窗進場用 `spring()` 從下方彈上來，`lift` 跟著變大。
- **直式**：桌面截圖不要等比縮小成一條。改用 `pic(…, { fit: 'cover', u, v })` 對準正在操作的區域，或改用手機版截圖放進 `framePhone`。
- **先算座標再畫**：鏡頭要在畫之前知道點擊位置，所以用 `browserContent()` 算內容區、`picMap()` 算截圖換算器，再用 `m.at(u, v)` 取得按鈕的畫面座標。`u, v` 是截圖上的相對位置（0–1），用 `view` 看截圖估出來。
- **字幕與標題放在 `shot()` 外面**，才不會跟著鏡頭放大、被推出畫面。標籤（`callout`）放在裡面，才會黏在按鈕上。

## 6. 文字與檢查

- 介面模型裡的字（按鈕、欄位、網址列）用 `txtB(…, { ui: true })`：立即繪製，會被視窗裁切、在游標下面；`ui: true` 讓文字檢查把它當成畫面內容，鏡頭推近時被裁切不會誤報。
- 片中的說明字幕、標題照常用 `txt()`，照常接受文字檢查。
- 自己畫介面時，顏色用 `UI.paper／panel／ink／sub／line／fill`（深色介面用 `UI.dark.*`），強調色用 `STYLE.c.a1`，不要寫死色碼。
- verify 回報「找不到截圖」（代碼 2）：`assets/` 裡沒有那張圖，或檔名不對（`pic('home')` 對應 `assets/home.jpg`）。
- 截圖合計超過 8MB 時 build 會提醒：用 `--width 1800`、`--quality 75` 重新擷取，或刪掉沒用到的圖。

## 7. API 速查（library/product.js）

| 函式 | 用途 |
|---|---|
| `pic(name, x, y, w, h, { fit, u, v, z, r, alpha })` | 畫截圖。`fit`：`cover`／`contain`／`width`；`u, v` 對準點；`z` 再放大。回傳 `m`，`m.at(u, v)` → 畫面座標 |
| `picMap(…)` | 同 `pic` 但不畫，只回傳換算器 |
| `frameBrowser(x, y, w, h, { url, dark, lift, r }, box => …)` | 瀏覽器外框，內容畫在回呼裡（自動裁切）。`browserContent(x, y, w, h)` 先算內容區 |
| `frameWindow(x, y, w, h, { title, dark, lift }, box => …)` | 桌面 App 視窗 |
| `framePhone(cx, cy, h, { body, island, lift }, box => …)` | 手機外框，h 是機身高 |
| `backdrop(t, { colors, amt })`、`floatShadow(x, y, w, h, r, lift)` | 漸層桌布、浮起陰影 |
| `cursorAt(t, keys)` | keys：`[{ t, x, y, click?, drag?, focus?, zoom?, dur? }]`，t 是抵達秒數。回傳 `{ x, y, down, clickAt }` |
| `drawCursor(c, t, { kind: 'arrow'｜'hand', size, ripple })`、`clickRipple(x, y, age, col)` | 畫游標（含點擊漣漪） |
| `typing(s, t, start, cps)` | 打字：`{ text, caret, done }` |
| `follow(t, camKeys, { bound, breathe })`、`camFromClicks(keys, { zoom, lead, hold, dur })` | 鏡頭跟隨；搭配 `shot(cam, () => …)` |
| `spotlight(x, y, w, h, p, { dim, r, pad, col })` | 框外壓暗、框線強調 |
| `callout(px, py, lx, ly, s, p, { col, size, align, maxW })` | 從指向點拉線到標籤 |
| `UI.*`、`IMG`、`imgOK(name)` | 介面中性色、已載入的截圖 |
