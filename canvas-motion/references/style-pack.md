# 風格：生成參數與錨點

**一般情況不用寫 JS。** 依情境（見 direction.md）挑一個錨點，把要改的參數寫成 style spec，直接放進 project.json 的 `style`：

```json
"style": { "base": "minimal", "name": "calm-green", "mood": "安靜、可信任",
           "colors": { "bg": "#f3f1ea", "a1": "#2f7d5b" }, "fonts": { "display": "Noto Serif TC" },
           "music": { "bpm": 92 }, "background": { "kind": "paper", "amount": .5 } }
```

build.py 會呼叫 `scripts/style_gen.py` 產生風格並驗證、自動修正（對比、亮底 bloom、bpm 範圍、和弦音域、轉場名稱），把修正內容印出來。完整欄位見 `styles/_schema.json`。單獨檢查一份 spec：`python3 <SKILL>/scripts/style_gen.py spec.json`；列出錨點參數：`--anchors`。

背景 `background.kind`：`base`（沿用錨點背景，最穩定）、`solid`、`gradient`、`glow`、`grid`、`dots`、`paper`。錨點的背景圖形（例如 tech 的透視網格、ink 的遠山）只能用 `base` 取得。

**只有 spec 做不到時才手寫風格 JS**（例如全新的背景圖形或 overlay）：複製最接近的錨點到 `<專案>/styles/<name>.js` 修改，`style` 改寫成這個名稱。不要改 skill 內建檔案。以下是 STYLE 物件的完整規格，手寫時照著做；引擎依賴這些欄位，缺了會壞。

## 檔案開頭：網頁字體

```js
// @fonts https://fonts.googleapis.com/css2?family=Inter:wght@400;800&family=Noto+Sans+TC:wght@400;700;900&display=swap
```
build.py 會把這行轉成 `<link>`。Artifact 只允許 Google Fonts 當外部樣式來源，其他字體服務會被擋掉。容器或離線環境載不到時會退回字體堆疊中的系統字型，所以 `fonts` 一定要接中文系統字型。

## 必要欄位

```js
const STYLE = {
  name: 'mybrand',
  fonts: {                 // 三組字體堆疊，一定要接中文 fallback
    sans:    '"Inter","Noto Sans TC","Noto Sans CJK TC","PingFang TC","Microsoft JhengHei",sans-serif',
    display: '…',          // 大標
    mono:    '…',          // 數字、程式碼、說明小字
  },
  c: {                     // 色彩 token：場景只能用這些名稱
    bg, fg, mute,          // 背景、主文字、次要文字
    a1, a2, a3,            // 三個強調色（a1 最重要）
    line,                  // 細線、網格
    card, cardLine,        // 卡片底與框
    flash,                 // flash 轉場的閃光色
  },
  post: { bloom, vignette, grain },   // 0 = 關閉。亮底風格 bloom 一律 0
  trans: ['push', 'wipe'],            // 預設轉場輪替
  music: { … },                       // 見下方
  bg(time, pulse, scene) { … },       // 每格背景，畫在 ctx 上
  overlay(time, pulse) { … },         // 選用：後製之後的最上層（如掃描線）
};
```

選填的外觀欄位：

| 欄位 | 說明 |
|---|---|
| `light: true` | 亮底風格一定要設。`glow()` 會改用一般混合，否則光暈會把畫面洗白 |
| `noGlow: true` | 完全關閉光暈（粗野主義這類要平面感的風格） |
| `cardR` | 卡片圓角，MIN 的比例（0 = 直角，預設 .018） |
| `cardLw` | 卡片框線粗細（px） |
| `cardShadow` | 卡片陰影顏色，例如 `'rgba(15,27,45,.1)'`，適合亮底 |

`c.fg` 與 `c.bg` 的對比要夠，否則 `txt()` 預設色會看不清。token 名稱在所有風格包之間一致，場景才能直接換風格。

## 背景函式的效能

背景每格都會畫，而且轉場時畫兩次。
- 靜態的漸層、紙紋、點陣用 `cached()` 烘焙；可以烘成 1/4 解析度再放大（柔和的東西看不出差別）。
- 全螢幕的大光暈在無 GPU 環境很貴，烘進背景圖層後用微幅位移製造漂移感。
- 動態元素（網格捲動、太陽脈動）直接畫，數量控制在幾十條線以內。
- 用 `sheet.py` 印出的毫秒數確認：容器內軟體繪製 1280×720 建議 20ms 以內。

## music 參數

| 參數 | 說明 | 範例 |
|---|---|---|
| `bpm` | 速度 | 90 慢、120 標準、128+ 快 |
| `chords` | 每小節一個和弦，MIDI 音高陣列，循環使用。陣列可以有 3–5 個音（ink 用 5 音做五聲音階） | `[[60,64,67,71],[57,60,64,67]]` |
| `kit` | `four`（四拍踩）、`half`（半拍感）、`soft`（只有第一拍輕踩）、`none` | |
| `snare` | `clap` 或 `snare` | |
| `pad`, `padWave`, `padCut`, `padGain` | 鋪底和弦；`pad:false` 關閉 | |
| `bass`, `bassWave`, `bassCut`, `bassPat` | 低音；`bassPat` 是 16 分音符位置 0–15 | `[0,3,6,8,11,14]` |
| `lead`, `leadWave`, `leadCut`, `leadGain`, `leadLen`, `leadOct`, `leadFrom` | 主旋律琶音；`lead:'none'` 關閉；`leadFrom` 是出現的 energy 門檻 | |
| `arp` | 琶音取和弦第幾個音的順序 | `[0,1,2,3,2,1,2,3]` |
| `delaySend`, `delayFb` | 延遲效果的送出量與回授 | .28 / .33 |
| `gain` | 總音量 | .68 |

常用和弦的 MIDI（C4 = 60）：Cmaj7 `[60,64,67,71]`、Am7 `[57,60,64,67]`、Fmaj7 `[53,57,60,64]`、G `[55,59,62,67]`、Dm7 `[62,65,69,72]`、Em `[52,55,59,64]`。

## 錨點風格（內部起點，不要當清單給使用者挑）

| 名稱 | 氣氛 | 亮／暗 | bpm | 預設轉場 | 適合 |
|---|---|---|---|---|---|
| `tech` | 深黑、薄荷藍紫漸層、透視網格、bloom | 暗 | 120 | push, wipe, zoom, glitch | 產品發表、科技介紹 |
| `corporate` | 白底品牌藍、卡片陰影、乾淨 | 亮 | 108 | push, wipe, fade | 內部提案、客戶簡報、SaaS |
| `minimal` | 米白、單一紅色、細框、留白 | 亮 | 90 | wipe, push, iris | 品牌片頭、教學 |
| `editorial` | 米白紙、襯線大標、欄線、紅點綴 | 亮 | 84 | wipe, fade, push | 品牌故事、人物專訪、年度回顧 |
| `warm` | 紙紋、圓體、柔和色塊 | 亮 | 100 | iris, push, fade | Onboarding、社群、溫馨主題 |
| `pastel` | 淡紫粉藍、飄動色塊、玻璃卡 | 亮 | 104 | iris, zoom, push | 招募、活動邀請、輕鬆公告 |
| `data` | 深灰點陣、語意色、等寬數字 | 暗 | 110 | push, fade, wipe | 報告、營運數據 |
| `neon` | 合成波太陽與網格、掃描線 | 暗 | 110 | glitch, flash, push | MV、尾牙、潮流 |
| `brutalist` | 螢光黃、純黑粗框、無光暈、硬切 | 亮 | 128 | cut, flash, push, glitch | 活動倒數、社群短影音 |
| `ink` | 宣紙、墨暈、遠山、朱印、五聲音階 | 亮 | 76 | fade, iris, wipe | 節慶、文化主題、品牌典故 |

特有輔助函式：warm 的 `wobble(x1,y1,x2,y2,col,lw,t)` 手繪抖動線；data 的 `bars(x,y,w,h,vals,p,{hi,max,colors})` 直條圖生長。只在使用該風格時可用。

**使用者對風格方向猶豫時**：與其列清單，不如依情境生成 2–3 個 spec，用 `preview_styles.py <專案> --styles a,b,c`（放在 `<專案>/styles/` 的手寫風格）或分別建置比較，讓使用者看自己的內容套上不同方向的樣子。

## 品牌風格

使用者提供品牌色時，寫一份 spec：主色放 `colors.a1`，輔色放 `a2`／`a3`，依品牌底色決定亮底錨點（minimal、corporate）或暗底錨點（tech、data）。對比不足時 style_gen 會自動調整並回報，**要告訴使用者品牌色被調過**。確認品牌字體能從 Google Fonts 取得，取不到就用最接近的替代字體，並告訴使用者。
