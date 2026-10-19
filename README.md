# Canvas Motion

**一支 HTML，就是一支影片。**

Canvas Motion 是一個開放式的 [Claude Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)，讓 Claude 用程式做出動畫短片：畫面由 Canvas 逐格繪製，配樂由 WebAudio 即時合成，整支片就是一個 HTML 檔。主題、敘事結構、畫面與視覺風格都不設限：Claude 會依你的內容與情境設計分鏡，並提出適合的風格建議。同一個檔案可以直接在瀏覽器播放、發布成 claude.ai Artifact 分享連結，也能匯出成含配樂的 MP4 或 GIF。

![Canvas Motion 介紹](media/intro.gif)

這支介紹動畫本身就是用 Canvas Motion 做的：每一格都由程式算出、配樂即時合成、產品示範像真的錄影（傾斜進場、推近、動態模糊）、數字追溯素材、自動檢查到通過。範例專案都在 [`examples/`](examples/)：產品示範（[`product-demo`](examples/product-demo)，虛構筆記 App「Notely」從痛點、操作到成果與行動呼籲的 29 秒短片，含旁白字幕）、UI 微動態（數據、互動）、畫風與形狀展示。

## 特色

- **像設計師一樣先對方向，再修細節**：開工先問參考風格（具體的片子或畫面），把素材串成一條因果故事、找一個視覺隱喻，用畫面演出來而不是用字寫。劇組（3 位導演提案互評、製作、3 位審查）每做出一版先審故事、畫面敘事、視覺傳達與事實，給你看；你確認方向後才逐格精修並匯出（評分見 `references/rubric.md`，分工見 `references/agents.md`）。
- **提示是輔助構思，不是限制**：原則、類型慣例、劇組流程與檢查提醒都是幫你想得更遠的工具；只有技術限制會擋，創作規則可以刻意打破。提案時會多給一個更大膽的方向。
- **創意優先，不套框架**：沒有版面零件、沒有敘事範本。每一幕的構圖、隱喻與動畫都由 Claude 依素材自己發想、寫成場景程式，數字、流程、據點也會變成畫面裡的物件在做事，而不是排成卡片。
- **自由敘事**：依素材設計結構，幕數、順序與每一幕的畫面都不受限。
- **現成畫筆**：文件、人物、筆電、齒輪、燈泡、星星、弧線等常用物件（`library/kit.js`），加上 10 種畫風的形狀與渲染，只為省時間，不是可選清單。
- **多種畫風、構圖開放**：動畫風背景、水彩、水墨、扁平插畫、像素、霓虹、低多邊形、剪紙、美漫網點、蠟筆，Claude 依情境建議畫風；畫面要放什麼、怎麼安排，由你描述。
- **依情境建議風格**：Claude 會依主題、觀眾與播放場合提出視覺與配樂風格的建議，也能配合品牌色客製。
- **橫式、直式都有專屬版面**：同一支片在電腦上是 16:9，在手機上自動變成 9:16，不是等比縮小。
- **畫面跟著音樂走**：場景切點對齊小節，配樂依每幕的強度（energy）自動編曲，結尾自動收成和弦。
- **配樂也能自己寫**：參數調不出的曲風（戲曲、民族樂、特定樂器）可以整支自己作曲，引擎提供鑼、鈸、梆子、皮鼓、滑音弦等合成樂器，鑼鼓點也能對準角色動作的拍點。
- **好看靠手藝**：動作函式庫（彈簧、預備動作、擠壓伸展、抹影、鏡頭、視差）、每幕必填的高光瞬間與延續、音效綁動作、高潮前靜默、匯出動態模糊；`taste.py` 會量出「畫面沒在動、沒對拍、高潮沒演出來、像投影片、同一刻疊太多強調」。
- **產品介紹與操作示範**：`capture.py` 先擷取產品網站的真實截圖、頁面文字與品牌色（擷取失敗就停下來要素材，不憑印象畫假介面）；再用瀏覽器／App 視窗／手機外框、像人手的游標路徑與點擊漣漪、打字效果、依點擊自動推近的鏡頭（Screen Studio 式）、聚光與功能標籤演出操作過程。外框可以立體傾斜著升起再轉正；鏡頭推拉與游標快速移動時帶動態模糊，游標停著會自動淡出；推近、聚光、標籤、字幕一次只出一個。敘事先講結果、不只講怎麼點：分鏡標上痛點、操作、成果、行動呼籲，storyboard 會提醒缺了哪段或操作拖太長。參考了 HyperFrames、Screen Studio／OpenScreen、Tella、21st.dev 游標元件與 remocn 的做法。
- **旁白配音與字幕**：每幕寫一句 `vo`，`voice.py` 用 Windows 內建的離線台灣中文語音（Yating、Hanhan、Zhiwei）配音，每句產 3 個版本、用內建語音辨識挑最清楚的一版，依旁白實際長度自動調整每幕小節數；字幕燒進畫面並另存 `.srt`，旁白出現時配樂自動壓低約 11dB。也支援 Edge 線上語音、macOS 語音或自己錄的音檔。
- **高質感 UI 微動態**：40 多個「A → B」元件（`library/ui.js`、`uictl.js`）：浮起的玻璃卡片、KPI 數字滾動與成長標籤、長條長成趨勢線、按鈕從載入變成綠色完成、開關、分段切換、通知堆疊、動態島、行事曆拖曳排程、刷卡機付款、線框變成 App 畫面，範例在 `examples/ui-data-demo`、`ui-controls-demo`。
- **字幕樣式與自訂音效**：字幕有底板、逐字亮起、短影音大字、無底板、左下角標題條五種；音效除了內建合成，也能用你放進專案 `sfx/` 的音檔。
- **插畫角色**：人物用 [Open Peeps](https://www.openpeeps.com)（Pablo Stanley，CC0）的插畫部件組合：站姿、坐姿、半身（含筆電、文件、咖啡）、33 種表情、53 種髮型，可套品牌色。角色靠換表情、換姿勢、自動眨眼、說話、呼吸與彈跳進場演戲；`references/peeps/` 有部件型錄，`castsheet.py` 產生角色設定表。
- **動態設計準則**：出場順序（一個主角先行）、依元素與調性的時長、緩動、錯開與反向動作，改寫自 LottieFiles Motion Design Skill（MIT）。
- **類型特效**：美漫（網點、爆炸框）、港漫（氣勁、集中線、斜格）、日式動畫（衝擊幀、流線）、電影（寬銀幕、青橙調色、光束），新增 hkcomic、amcomic、cinema 三種風格。
- **劇組流程做一分鐘故事片**：編劇（一句話故事、主角弧線、三幕節拍）、美術、導演（景別、運鏡、畫面方向）、剪輯、聲音、場記，storyboard 會檢查三幕比例、節拍、景別變化、跳軸與剪輯節奏。
- **所見即所得**：每一格都是 `frame(t)` 的純函式，所以播放、截圖驗證、匯出 MP4 的畫面完全一致。
- **穩定出片**：分鏡節奏檢查、風格自動驗證（對比不足自動修正）、場景程式檢查、文字裁切／重疊偵測、數字出處追溯，出錯時 Claude 會自己修到通過。

## 視覺風格

風格不從固定清單裡挑選。Claude 會依內容的情境（主題、觀眾、播放場合、想留下的感受）提出畫風與風格建議，說明配色、字體、轉場與配樂的方向與理由，你確認或調整後再製作。**構圖由你決定**：Claude 會用開放式問題問你畫面的主體、場景、遠近與動態，並附上一個依素材想到的構圖供你參考。有品牌規範時，也可以直接提供品牌色與字體。

## 安裝

### claude.ai

1. 到 [Releases](../../releases) 下載 `canvas-motion.skill`，或自己打包（見下方「開發」）。
2. 在 claude.ai 的「設定 → Capabilities → Skills」上傳。
3. 需要開啟「Code execution and file creation」。

### Claude Code

```bash
git clone https://github.com/chengwesley/canvas-motion.git ~/.claude/skills/canvas-motion
```

### 環境需求

| 工具 | 用途 | 缺少時 |
|---|---|---|
| Python 3.10+ | 建置、截圖、匯出腳本 | 必要 |
| Node.js | 建置時的語法檢查 | 可缺，會略過檢查 |
| Playwright + Chromium | 截圖驗證、MP4 匯出 | 可缺，但只能產出 HTML |
| ffmpeg | MP4 匯出 | 可用 `pip install imageio-ffmpeg` 代替 |
| Pillow | 縮圖總覽、產品截圖處理 | 截圖時必要 |
| 旁白語音 | 旁白配音（`voice.py`） | 可缺，不配音就不需要。Windows 內建台灣中文語音（Yating、Hanhan、Zhiwei）；其他系統用 `pip install edge-tts` 或 macOS 的 `say` |
| 中文字型 | 截圖顯示中文 | 截圖會出現方框 |

執行 `python3 ~/.claude/skills/canvas-motion/scripts/check_env.py` 可以一次檢查。claude.ai 的程式執行環境已經全部內建。

## 使用方式

### 跟 Claude 說

安裝後直接用自然語言描述，Claude 會自己決定何時使用這個 skill：

> 幫我把這份產品說明做成 30 秒的介紹影片，要直式，給 IG Reels 用。

> 把這篇文章的核心概念做成一支動態解說，風格請你依內容建議。

> 用這些數字講一個故事，重點是最後那個轉折。

> 做一支我們產品的功能示範影片：從官網開始，示範怎麼完成第一個任務，加上旁白和字幕。

你只要說需求、素材與參考風格。Claude 會從目的、觀眾與播放平台推斷片長、比例與敘事，由劇組提出故事與視覺隱喻、互評選定後做出第一版，**每一版都先給你看**；你說方向對了，才精修細節、匯出影片，並自動檢查版面、文字與素材出處。**畫面上的文案和數字只會來自你提供的素材**；素材撐不起某一幕時，Claude 會刪掉那一幕，而不是自行編造內容。

### 手動操作

```bash
SKILL=~/.claude/skills/canvas-motion

# 1. 寫分鏡 storyboard.json（格式見 scripts/storyboard.py 開頭），先預覽分鏡表與節奏檢查
python3 $SKILL/scripts/storyboard.py storyboard.json --preview

# 2. 產生專案（project.json + 自訂場景鷹架）
python3 $SKILL/scripts/storyboard.py storyboard.json my-video

# （產品片）擷取產品網站的真實截圖、頁面文字與品牌色 → my-video/assets/、source.txt、brands/
python3 $SKILL/scripts/capture.py https://產品網址 my-video --name home --brand 品牌名

# （有旁白）每幕寫好 vo 後產生配音，--fit 依旁白實際長度自動加小節
python3 $SKILL/scripts/voice.py my-video --fit

# 3. 需要自訂畫面時，在 my-video/scenes/ 編輯場景函式（寫法見 references/api.md）

# 4. 一鍵檢查（建置＋縮圖＋文字檢查），結束碼 0 才算通過
python3 $SKILL/scripts/verify.py my-video                # → my-video/dist/index.html、my-video/sheets/*.jpg

# 5. 匯出 MP4 或 GIF
python3 $SKILL/scripts/export.py my-video out.mp4 --size 1080x1920 --mobile --verify 2,10
python3 $SKILL/scripts/export.py my-video out.gif
python3 $SKILL/scripts/export.py my-video out.mp4 --size 1280x720 --crf 25   # 720p、檔案較小；有旁白時另存 out.srt，加 --no-subs 不燒字幕
```

`dist/index.html` 用任何瀏覽器打開就能播放；空白鍵暫停，左右鍵前後跳一小節，右下角可以切換比例。

### project.json 範例

```json
{
  "title": "新功能發表",
  "style": { "base": "tech", "mood": "俐落、有未來感", "colors": { "a1": "#5ef2c6" }, "music": { "bpm": 116 } },
  "aspect": "auto",
  "scenes": [
    { "fn": "sHook",    "bars": 2, "energy": 0.35, "trans": "zoom" },
    { "fn": "sFeature", "bars": 3, "energy": 0.7,  "trans": "push",
      "vo": ["一句旁白，也是字幕", { "say": "上傳 P D F 文件", "sub": "上傳 PDF 文件" }] },
    { "fn": "sOutro",   "bars": 2, "energy": 1 }
  ],
  "voice": { "engine": "winrt", "voice": "Yating", "subs": true, "duck": 0.28 }
}
```

- `fn`：這幕的場景函式，寫在 `scenes/` 裡。
- `style`：風格參數，由 Claude 依情境決定；建置時會自動驗證對比、字體與節奏並修正（格式見 [`styles/_schema.json`](styles/_schema.json)）。
- `bars`：這幕佔幾小節（120 BPM 時一小節 2 秒）。
- `energy`：0–1，控制配樂密度，由低到高安排情緒起伏。
- `trans`：離開這幕的轉場，可用 `cut` `fade` `push` `wipe` `zoom` `iris` `flash` `glitch`。
- `vo`：這幕的旁白（選填），字串就是念的話也是字幕；念法和字幕不同時分開寫 `say`／`sub`。`voice` 設定語音、字幕與配樂壓低的程度（見 [`references/voice.md`](references/voice.md)）。

場景函式的寫法見 [`references/api.md`](references/api.md) 與 [`examples/keynote-demo`](examples/keynote-demo)。

## 專案結構

```
.
├── README.md
├── media/                     README 用的介紹動畫
├── SKILL.md                   給 Claude 的操作說明
├── engine/                    固定引擎：HTML 外殼、繪圖與排版、時間軸與配樂、播放器
├── library/                   畫筆（不是版面）：kit.js、畫風 looks.js、產品示範 product.js、UI 微動態 ui.js／uictl.js、插畫角色 peeps.js
├── brands/                    品牌設定檔（capture.py --brand 產生）
├── styles/                    風格設定
├── scripts/                   verify / capture / voice / storyboard / build / sheet / export / style_gen / check_env / selftest
├── references/                direction.md（情境→規格與節奏）、looks.md（畫風與常用形狀）、api.md（場景寫法）、
│                              style-pack.md（風格設定）、product.md（產品示範）、ui-kit.md（UI 微動態）、voice.md（旁白與字幕）、
│                              motion-design.md（出場順序與緩動）、character.md（角色）＋ peeps/（部件型錄）
└── examples/                  範例專案（也是回歸測試）
```

## 運作原理

```
project.json + scenes/*.js（＋ assets/ 截圖、voice/ 旁白音檔）
        │  build.py
        ▼
engine/infra.js ─ 風格設定 ─ 場景 ─ engine/tail.js
        │
        ▼
dist/index.html（單一檔案：截圖與旁白都內嵌成 data URI，無外部依賴，字體從 Google Fonts 載入）
        │
        ├── 瀏覽器播放：requestAnimationFrame → frame(t)，AudioContext 即時排程配樂與旁白
        ├── sheet.py：Playwright 呼叫 frame(t) 截圖 → 縮圖總覽
        └── export.py：OfflineAudioContext 合成 WAV（配樂＋旁白＋音效）→ 逐格 frame(i/fps) → ffmpeg（H.264 + AAC）＋ .srt
```

- **時間軸**：場景長度以小節計算，切點落在小節第一拍。轉場中點對齊切點，期間同時繪製前後兩幕再合成。
- **文字**：`txt()` 延後到後製之後才繪製，所以不會被 bloom 糊掉；中文換行支援避頭點。
- **配樂**：每 16 分音符呼叫一次 `step()`，依當下場景的 energy 決定要加入哪些聲部（pad、鼓、bass、主旋律），和弦進行與音色由風格設定決定。專案若在 `scenes/` 定義全域函式 `MUSIC(A, i, t, info)`，整支配樂改由它負責（樂器：`tone`、`bend`、`gong`、`cymbal`、`woodblock`、`drum`、`kick`、`pad`…）。
- **旁白與字幕**：`voice.py` 產生的音檔依實際長度排在每幕裡（幕首、句間、幕尾留白可調），引擎播放旁白時把配樂匯流排壓到約 0.28 倍、講完再回升；字幕依標點切成短句、依字數分配時間，畫在所有畫面與後製之上，也會接受文字檢查。
- **產品截圖**：`assets/` 的圖片內嵌後由 `pic()` 繪製，`picMap()` 把截圖上的相對位置換成畫面座標，游標、鏡頭推近、聚光都用它定位；所有圖片與旁白解碼完才開始截圖或匯出。
- **效能**：DPR 上限 1.5，背景與光暈預先烘焙成低解析度圖層，重複繪製的元素快取到 offscreen canvas。

## 已知限制

- 不處理實拍影片或角色逐格動畫。照片與截圖可以當素材（產品截圖用 `capture.py` 擷取，或匯入使用者提供的圖片），需要登入的產品畫面要自己截圖。
- 離線旁白（winrt）只能在 Windows 執行；語音辨識常把同音字聽錯，挑版本用的字錯率只能比較好壞，交片前仍要用耳朵聽一次。
- 程式執行環境無法連上 Google Fonts，所以截圖使用系統的 Noto Sans CJK；線上播放時才會用風格設定指定的字體，兩者字型會略有不同。
- 在沒有 GPU 的環境（例如雲端容器）中繪製較慢，但只影響截圖與匯出的速度，不影響成品品質。
- 瀏覽器規定必須由使用者點擊後才能播放聲音，所以頁面一定會先顯示播放鈕。

## 開發

修改後跑回歸測試（建置所有組合，並對範例專案做截圖與文字檢查）：

```bash
python3 scripts/selftest.py --sheet
```

確認沒有場景錯誤，並逐格檢查縮圖。

打包成 `.skill` 檔（就是 zip，最上層是 `canvas-motion/` 資料夾）：

```bash
git archive --prefix=canvas-motion/ -o canvas-motion.skill HEAD
```

風格設定的格式見 [`references/style-pack.md`](references/style-pack.md)；場景寫法見 [`references/api.md`](references/api.md)。
