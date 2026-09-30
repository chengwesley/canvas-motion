# Canvas Motion 引擎 API

寫場景前讀這份。每一幕都是自己發想、自己寫的場景函式；常用畫筆在 `library/kit.js`（文件、人物、筆電、齒輪、燈泡、星星、弧線）與 `library/looks.js`。引擎在 `engine/`，所有函式都是全域的，場景檔直接呼叫即可。

## 目錄
1. project.json
2. 場景函式的約定
3. 全域變數
4. 時間與緩動
5. 版面與字級
6. 文字
7. 形狀與效果
8. 3D 與鏡頭
9. 轉場
10. 配樂
11. 常用場景寫法
12. 除錯介面
13. 跨幕錨點（物件跨幕延續）
14. 畫風與常用形狀（見 looks.md）
15. 動作質感（motion.js，見 craft.md）
16. 音效與靜默（sfx、rest）

---

## 1. project.json

```json
{
  "title": "片名（也是網頁 <title>）",
  "style": "tech",
  "aspect": "auto",
  "bpm": 120,
  "transDur": 0.6,
  "music": true,
  "ending": "hold",
  "poster": 2.8,
  "webfonts": true,
  "scenes": [
    { "fn": "sHook",  "bars": 2, "energy": 0.35, "trans": "zoom" },
    { "fn": "sOutro", "bars": 2, "energy": 1 }
  ]
}
```

| 欄位 | 說明 |
|---|---|
| `style` | `styles/` 裡的風格包名稱。專案資料夾下的 `styles/<名>.js` 優先於內建 |
| `aspect` | `auto`（手機直式、電腦橫式）、`16:9`、`9:16`、`1:1`、`fill` |
| `bpm` | 省略時用風格包的 bpm。一小節 = 240 / bpm 秒 |
| `transDur` | 轉場秒數，中點對齊切點。預設 min(0.6, 1.2 拍) |
| `music` | `false` 關閉配樂 |
| `ending` | `hold`（停在最後一格，最後一小節是收束和弦）或 `loop`（循環播放） |
| `poster` | 按下播放前顯示的畫面秒數 |
| `scenes[].bars` | 這幕佔幾小節。**用整數**，切點才會落在小節第一拍 |
| `scenes[].energy` | 0–1，決定配樂密度：<.3 只有 pad；≥.3 加鼓與 bass；≥.5 加小鼓；≥.55 加主旋律；≥.8 hi-hat 加密；≥.85 旋律改 16 分音符 |
| `scenes[].trans` | 離開這幕時用的轉場（見第 9 節）。省略時輪流使用風格包的 `trans` |
| `scenes[].hero` | `{ "beat": 拍數, "what": "高光瞬間" }`。建議寫；taste.py 會看那一拍有沒有動作高峰（刻意安靜的高光可以忽略） |
| `scenes[].carry` | 上一幕的什麼變成這幕的主角（說明用，提案表會列出） |
| `scenes[].sfx` | 音效清單 `[[拍數, 種類, 音量?, 長度?], …]`（第 16 節） |
| `scenes[].rest` | `[起拍, 終拍]`：這段配樂靜默（第 16 節） |

播放順序由 `scenes` 陣列決定；`scenes/*.js` 的檔名只影響載入順序。

## 2. 場景函式的約定

```js
function sName(t, T, pulse, s) { ... }
```

- `t`：本幕經過秒數。`t = 0` 就是本幕的切點（小節第一拍）。轉場前半段 `t` 會是負值，轉場後半段會超過 `T`。
- `T`：本幕長度（秒）＝ bars × 小節秒數。
- `pulse`：拍點脈衝。每拍開頭為 1，之後指數衰減到約 0.004。用來做呼吸、閃爍、放大。
- `s`：project.json 裡這幕的設定（可放自訂欄位，例如 `s.items`）。

每格引擎會先畫風格包背景，再呼叫場景函式，之後做後製，最後畫 `txt()` 佇列裡的文字。場景函式內不需要自己 `save/restore` 整個 context，引擎已處理；但局部變換仍要自己包。

**有轉場的幕不要自己淡出**：轉場期間引擎會同時畫兩幕再合成，如果前一幕已經淡成空白，轉場就只剩背景。只有 `trans: "cut"` 或幕內元素交棒時才用 `inout()`。

**進場從切點前開始**：`tw(t, -.25, .5)` 讓標題在轉場後半段就滑入，切點時已經看得到。

## 3. 全域變數

| 名稱 | 說明 |
|---|---|
| `ctx` | 目前的 2D context。**一律畫在 `ctx`**，不要存成區域變數跨幀使用 |
| `W`, `H` | 畫布 CSS 像素尺寸 |
| `MIN` | `min(W, H)`，尺寸單位用它乘比例 |
| `PORT` | 直式（H > W × 1.05） |
| `SQUARE` | 接近正方形的橫式 |
| `BPM`, `BAR`, `BEAT`, `SX` | 速度、小節秒數、一拍秒數、16 分音符秒數 |
| `STYLE` | 目前風格包。顏色用 `STYLE.c.xxx`，不要寫死色碼 |
| `SAFE` | 安全區：`x, y, w, h, r(右邊界), b(下邊界)` |

## 4. 時間與緩動

| 函式 | 用途 |
|---|---|
| `prog(t, a, b)` | t 在 a→b 之間的 0–1 進度（已夾住） |
| `tw(t, start, dur, ease='out')` | 補間，回傳緩動後的 0–1 |
| `inout(t, T, start, dur, ease, outD=.35)` | 進場後在結尾前退場 |
| `stag(t, i, start, gap, dur, ease)` | 第 i 個元素錯開 gap 秒 |
| `E.lin / out / in / io / expo / back / elastic` | 緩動函式 |
| `clamp, lerp, pick(land, port, square?)` | 基本工具；`pick` 依版面二選一 |
| `rng(seed)` | 可重現的亂數產生器，粒子位置用它（每格結果相同） |
| `noise1(x)` | 平滑 1D 雜訊，−1 到 1 |
| `countUp(p, from, to, decimals)` | 數字滾動字串，含千分位 |
| `typeOn(s, p)` | 打字效果，依 p 回傳前幾個字 |

**以拍為單位排時間**：`tw(t, BEAT * 2, .5)` 表示第三拍開始。高潮放在拍點上，觀眾會覺得畫面跟音樂黏在一起。

**不要用 `Math.random()`**：匯出時每格都重新計算，隨機值會讓畫面閃爍。改用 `rng(固定種子)`。

## 5. 版面與字級

- `fz(key)`：字級。`hero, h1, h2, h3, body, cap, tiny`，或傳比例數字 `fz(.3)`。直式以寬為基準、橫式以高為基準，同一個 key 在兩種版面都好讀。
- `fit(text, maxW, size, weight, fam, maxLines=1, minR=.5, track=0)`：縮小字級直到能在 maxLines 行內放進 maxW（有字距時傳 track）。
- `wrap(text, maxW, size, weight, fam)`：回傳分好的行陣列。中文逐字斷、英文逐詞斷，含避頭點（，。」等不放行首）。**最後一行太短（中文 2 字以內、或只剩一個英文單字）時會自動收窄寬度重排**，行長較平均；結果有快取。
- `measure(text, opts, y)`：量測，回傳 `{w, h, lines, top, bottom}`。
- `clampLines(text, maxW, size, n, weight, fam)`：換行後最多保留 n 行，超出以「…」結尾。

**直式要有專屬版面，不是等比縮小**。橫式一列 5 張卡，直式改一欄 5 列；橫式左右兩欄，直式改上下。用 `PORT ? … : …` 或 `pick()` 分開算座標。

## 6. 文字

```js
txt(text, x, y, {
  size, weight=700, fam='sans'|'display'|'mono', color=STYLE.c.fg,
  align='left'|'center'|'right', base='middle'|'top'|'bottom',
  alpha=1, maxW, lh=1.28, track(字距，字級倍數), shadow(顏色), gradient:[色, 色, …],
  fit: { lines: 2, min: .5 }   // 選用：在 maxW 內自動縮字到 lines 行以內
})
txtPlate(text, x, y, { …同上, plate: 'auto'|'dark'|'light'|顏色, pad: .5 })   // 自動加底板
```

| 函式 | 何時用 |
|---|---|
| `txt()` | 預設。延後到後製之後才畫，字不會被 bloom 糊掉。回傳量測結果，可以接著排下一行 |
| `txtB()` | 大標、霓虹字、要發光的數字。立即繪製並參與 bloom；也能被 `reveal()` 遮罩 |
| `txtPlate()` | 壓在畫風背景、圖形、複雜畫面上的字。依字色深淺自動選深或淺色底板，任何背景都讀得到 |
| `txtOn(c, …)` | 在 `cached()` 的 offscreen context 上畫字（這裡的字不在文字檢查範圍內，自己確認） |

- 所有可能變長的文字都要給 `maxW`，否則直式會超出畫面。
- `txt()` 不受 `ctx.clip()` 影響（它延後才畫）。需要遮罩揭示的文字用 `txtB()`。
- `txt()` 會記住當下的 transform 與 globalAlpha，所以放在 `camPush()` 或 `translate()` 內一樣有效。

## 7. 形狀與效果

| 函式 | 說明 |
|---|---|
| `rrect(x,y,w,h,r)` / `fillRR` / `strokeRR` | 圓角矩形 |
| `card(x,y,w,h,{fill,stroke,r,lw})` | 風格化卡片（用 `STYLE.c.card` / `cardLine`） |
| `circle(x,y,r,fill)` | 實心圓 |
| `ring(x,y,r,col,lw,p,a0)` | 圓弧，p = 0–1 畫出比例 |
| `line(x1,y1,x2,y2,col,lw,p)` | 線段，p 控制畫到哪 |
| `reveal(p,x,y,w,h,fn,dir)` | 遮罩揭示，dir = up/down/left/right |
| `glow(x,y,r,col,a)` | 預烘焙光暈貼圖，加亮混合，很便宜 |
| `cached(key,w,h,fn,deps)` / `drawCached(key,x,y,w,h,fn)` | 快取到 offscreen canvas；尺寸改變自動重建。**內容依賴顏色或資料時放進 `deps`**（例如 `[P.paper, s.data.title]`），否則不同幕會拿到舊內容 |
| `rgba(col,a)`、`mixc(c1,c2,p)`、`accent(i)` | 色彩工具；`accent(i)` 依序取 a1/a2/a3 |

風格包可能額外提供輔助函式（例如 warm 的 `wobble()`、data 的 `bars()`），使用前先確認專案用的是該風格。

## 8. 3D 與鏡頭

```js
const c = cam({ ry: Math.sin(t * .3) * .3, z: -MIN * 1.4 });
const p = proj({ x: 100, y: 0, z: 200 }, c);   // → {x, y, s(縮放), z} 或 null（在鏡頭後）
if (p) circle(p.x, p.y, 10 * p.s, STYLE.c.a1);
```
- 預設在 z = 0 平面上 1 單位 ≈ 1px，畫面中心為原點。
- 多個 3D 點先依 `z` 由遠到近排序再畫。
- `camPush(scale, rot, dx, dy)`：以畫面中心縮放整幕，做鏡頭微推。放在 `ctx.save()` 與 `ctx.restore()` 之間。

## 9. 轉場

`cut, fade, push, wipe, zoom, iris, flash, glitch`。push 在直式會自動改成上下推。

挑選原則：內容延續（同一主題下一步）用 `push`；揭示新主題用 `wipe` 或 `iris`；情緒轉強用 `zoom` 或 `flash`；科技或故障感用 `glitch`；最後一幕前通常用 `zoom` 或 `fade`。整支片不要只用一種。

## 10. 配樂

配樂由風格包的 `music` 參數與每幕的 `energy` 自動產生，通常不需要改程式碼。調整方式：
- 想讓某幕安靜：把 `energy` 降到 .3 以下。
- 想要高潮：把 `energy` 拉到 .85 以上，並讓畫面高潮落在小節第一拍。
- 最後一小節自動變成收束和弦（`ending: "hold"`）。所以最後一幕至少要 2 小節，第二小節留給字標與餘韻。
- 換和弦進行：在專案的 `styles/` 放一份修改過的風格包，改 `music.chords`（MIDI 音高，60 = C4）。

**自訂配樂（完全自己寫）**：參數調不出想要的曲風（戲曲、民族樂、特定樂器）時，在 `scenes/` 放一個檔案定義全域函式 `MUSIC`，整支配樂就改由它負責：

```js
function MUSIC(A, i, t, o) {   // 每個 16 分音符呼叫一次；t 是 AudioContext 時間
  // o = { time, bar, st(0–15), e(energy), scene, isSceneStart, lastBar, ch }
  if (o.lastBar) { if (o.st === 0) gong(A, t, 1.2, true); return; }
  if (o.st === 0) woodblock(A, t);
  if (o.st % 2 === 0) bend(A, t, 65, 67, SX * 2, { peak: .08, vib: 20 });
}
```

可用樂器：`tone(A,t,midi,dur,{wave,peak,cut,send})`、`bend(A,t,m0,m1,dur,{wave,peak,cut,q,glide,vib,rate,send})`（滑音＋顫音，弦樂、嗩吶）、`gong(A,t,v,big)`（大鑼／小鑼）、`cymbal(A,t,v,closed)`（鈸）、`woodblock(A,t,v,hi)`（梆子、板）、`drum(A,t,v,pitch)`（有音高的皮鼓）、`kick`、`snare`、`clap`、`hat`、`crash`、`noiseHit`、`pad`。範例：歌仔戲鑼鼓經＋殼仔弦五聲旋律。

## 11. 常用場景寫法

**大字遮罩揭示**
```js
const p = tw(t, 0, .55, 'expo'), m = measure(s, { size, weight: 800 });
reveal(p, cx - m.w / 2 - size, y - size * .7, m.w + size * 2, size * 1.4,
  () => txtB(s, cx, y + (1 - p) * size * .5, { size, weight: 800, align: 'center' }));
```

**卡片錯開進場＋直式改一欄**
```js
items.forEach((it, i) => {
  const p = stag(t, i, 0, BEAT * .5, .6, 'back');
  const w = PORT ? SAFE.w : (SAFE.w - gap * (n - 1)) / n;
  const h = PORT ? (SAFE.b - top - gap * (n - 1)) / n : w * 1.2;
  const x = PORT ? SAFE.x : SAFE.x + i * (w + gap), y = PORT ? top + i * (h + gap) : top;
  ctx.save(); ctx.globalAlpha = clamp(p); ctx.translate(0, (1 - p) * MIN * .08);
  card(x, y, w, h); txt(it, x + w / 2, y + h / 2, { align: 'center', maxW: w * .85 });
  ctx.restore();
});
```

**數字滾動落在拍點**
```js
const p = tw(t, BEAT * 2, .7, 'expo');
txtB(countUp(p, 0, 12800), cx, cy, { size: fz(.28), fam: 'mono', gradient: [STYLE.c.a1, STYLE.c.a2], align: 'center' });
```

**呼吸感**：建好畫面後讓 `camPush(1 + t * .01)`、光暈隨 `pulse` 放大、或讓高亮每拍輪流移動，避免超過 1.5 秒完全靜止。

## 12. 除錯介面

頁面上有 `window.__cm`：`frame(t)`、`resize(w,h,dpr)`、`renderWav()`、`TOTAL`、`SC`（場景時間表）、`errors`（場景拋出的錯誤）、`bench(n,w,h)`。

場景拋錯時引擎不會整支停掉，而是在那一幕畫出紅字錯誤訊息，並記錄到 `__cm.errors`；`sheet.py` 會把它印出來並以代碼 2 結束。

網址參數：`?aspect=9:16` 強制比例；`?still=3.2&w=1280&h=720` 只畫一格並把 dataURL 寫進 `#out`（無頭瀏覽器 `--dump-dom` 備援）。

## 13. 跨幕錨點（物件跨幕延續）

同一個物件要從上一幕接到下一幕時（紙片飛到桌上、車子開過兩幕），把位置寫成**具名錨點**，兩個場景都讀同一個名稱，不要各寫一次座標。

```json
"anchors": {
  "stack": { "x": 0.5, "y": 0.62, "s": 1, "r": 0, "port": { "y": 0.58 } },
  "carEnd": { "x": 0.85, "y": 0.86 }
}
```

- 寫在 storyboard.json（會帶進 project.json）或 project.json 的 `anchors`；座標是畫面比例，`port` 是直式覆寫。本幕 `data.anchors` 可以再覆寫。
- `anchor(name, s)` → `{ x, y, s, r }`（像素）。找不到會丟錯，verify 會抓到。
- `anchorLerp(a, b, p, lift)`：兩個錨點（名稱或物件）之間插值，`lift` 是弧形抬升（短邊比例），適合飛過去的物件。
- 慣例：A 幕把物件從 `x` 移到 `y`，B 幕從 `y` 開始。用 `verify.py --pairs` 並排看每個切點前後，確認接得上。

```js
function sFly(t, T, pulse, s) {
  const p = tw(t, BEAT, BEAT * 3, 'io'), c = anchorLerp('start', 'stack', p, .2);
  lookDraw(L, P, LK_SHAPES.paper(c.x, c.y, MIN * .1, MIN * .13, c.r));
}
```

## 14. 畫風與常用形狀

背景可在場景裡呼叫 `L_look`、主體用 `withLook` + `lookShape`／`LK_SHAPES` + `lookDraw`，說明與範例見 `references/looks.md`、`examples/shapes-demo`。

## 15. 動作質感（motion.js）

原則與範例見 `references/craft.md` 第 2、3 節。全部是 `t` 的純函式。

| 函式 | 用途 |
|---|---|
| `spring(t, start, freq=2.2, damp=.38)` | 0→1 彈簧，會過衝再回穩 |
| `anticipate(t, start, dur, amt=.18, wind=.3, ease)` | 先反向退 amt 再衝到 1 |
| `vel(fn, t)` | fn(t) 的速度（數字或 {x, y}） |
| `withSquash(x, y, vx, vy, draw, k, max)` | 沿速度方向擠壓伸展後在 (x, y) 畫 draw() |
| `impact(t, hitT, amt=.35, dur=.32)` | 撞擊後壓扁回彈，回傳 {sx, sy} |
| `lagT(t, i, lag=.06)` | 第 i 個延遲 lag 秒（跟隨與重疊） |
| `trail(t, fn, draw, n, gap)` / `smear(t, fn, draw, n, dt, minPx)` / `smearLine(x0,y0,x1,y1,r,col)` | 拖尾、高速抹影 |
| `arcPt(x1, y1, x2, y2, p, lift)` | 弧線上的點 {x, y, ang} |
| `hit(t, beats, decay=7)` | 本幕這些拍點的衝擊衰減 0–1 |
| `shake(t, hitT, amp, dur, seed)` | 鏡頭震動 {x, y, r} |
| `shot({x, y, zoom, rot}, draw)` / `camLerp(a, b, p)` | 鏡頭：把一點拉到中心並放大；在兩個鏡頭間移動 |
| `layer(depth, camX, camY, draw, blur)` | 視差圖層（0 遠、1 跟鏡頭、>1 前景），可加景深模糊 |
| `onTwos(t, fps=12)` | 時間量化成一拍兩格（手繪類畫風） |

## 16. 音效與靜默（sfx、rest）

```json
{ "fn": "sDrop", "bars": 2, "energy": 0.95,
  "sfx": [[-0.25, "whoosh"], [0, "boom"], [3, "riser", 0.8, 1.2], [4, "impact"]],
  "rest": [2.5, 3] }
```
- `sfx` 的拍數從本幕切點算起，可以是小數或負數（切點前）。riser 的拍數是「衝到頂」的時間，第 4 個值是長度秒數（預設一小節）。
- 種類：`whoosh`、`swish`、`riser`、`impact`、`boom`、`pop`、`click`、`stamp`、`chime`（用途見 craft.md 第 5 節）。自訂配樂 `MUSIC()` 時音效照樣播放。
- `rest` 期間配樂（含自訂 `MUSIC()`）靜默，音效照常。
- 動態模糊不在場景裡寫，匯出時加 `export.py --blur 5`（引擎的 `__cm.frameBlur`）。
