# 角色：Open Peeps（library/peeps.js）

需要人物時用插畫師畫好的 Open Peeps 部件組合（Pablo Stanley，CC0，可商用）。**不要自己用程式從零畫人**：比例、手、表情很難畫得自然。
部件型錄在 `references/peeps/`：`standing.jpg`（站姿 23 種）、`sitting.jpg`（坐姿 11 種）、`bust.jpg`（半身 26 種，含筆電、文件、咖啡、手機遊戲、指向等）、
`face.jpg`（表情 33 種）、`head.jpg`（髮型 53 種）、`beard.jpg`、`accessory.jpg`（眼鏡）。**寫場景前用 view 看型錄挑名稱。**

## 畫角色
```js
const ann = { body: 'BlazerColorTee', head: 'Bun', face: 'Smile', colors: { skin: 'fair', jacket: STYLE.c.a1, top: '#ffffff' } };
peep(x, groundY, H * .6, ann, t);                                  // 全身：(x, 腳底)、全身高
peepBust(x, deskY + H * .05, H * .45, { ...ann, body: 'Computer' }, t);   // 半身：(x, 底部)、高；放在桌子後面就是坐著工作
```
- `body`：全身用站姿或坐姿名稱，半身用半身名稱。`head` 髮型、`face` 表情、`beard` 鬍子、`acc` 配件（`Glasses` 等）。
- `colors`：`skin`（`light`、`fair`、`tan`、`medium`、`brown`、`deep` 或色碼）、`top`、`pants`、`jacket`、`shoes`、`hair`、`outline`（線條，預設黑）、`prop`（筆電、紙、杯子）。
  有些衣服是固定花色（黑色襯衫、圓點外套），型錄看得出哪些會變色。
- `dir: -1` 左右翻轉（面向左）。回傳 `{ head: {x, y} }`：頭頂位置，放對話框、驚嘆號用。
- 同一個角色整支片一致：在 project.json 寫 `cast`，場景用 `peep(x, y, h, peepCast('ann', { face: 'Awe' }), t)`。

## 讓角色演戲（不用骨架）
插畫部件不能彎手彎腳，角色的「動」來自下面這些，組合起來就很生動：
- **自動的**（傳入 `t` 就有）：眨眼（`blink: false` 關掉）、呼吸起伏、頭部緩慢擺動（`nod` 幅度、`idle: false` 全關）。
- **說話**：`talk: true`（或 `talk: tt => 是否在說`）嘴巴開合；搭配旁白時，用旁白那一句的時間決定 `talk`。
- **換表情**：情緒轉折那一拍換 `face`（例如 `Calm` → `Awe`），同一拍讓角色縮放彈一下（`spring`），觀眾才看得到變化。
- **換姿勢**：在剪接點或快速動作中換 `body`（例如 `RestingColorPants` → `PointingFingerColorPants`）；換的那一格加擠壓或抹影，像一個動作而不是跳圖。
- **整個人的動作**：進場用彈跳（`spring` 縮放、從畫面外滑入）、走路用 `WalkingColor*` 姿勢＋平移＋上下彈跳、驚訝時往上跳一下、沮喪時整個人下沉縮小。
- **鏡頭**：特寫就用半身（`peepBust`），情緒戲推近臉。

## 選角與構圖
- 產品片的人物：辦公室情境用半身（`Computer`、`Paper`、`Coffee`、`Explaining`）放在桌後；介紹人物用全身站姿。
- 多個角色時，膚色、髮型、身形要有差異，服裝用品牌色但不要每個人都同一色。
- 角色是配角時畫小一點、放在畫面一側，讓產品畫面當主角；人物故事片才讓角色佔大畫面。
- 避免：`Monster`、`Cyclops` 這類怪物表情與 `Doc*` 醫護裝束，除非主題需要。

## 維護
部件資料 `library/peeps/open-peeps.json` 由 `scripts/peeps_import.py` 從 opeepsfun/open-peeps 轉換；型錄圖由 `scripts/peeps_catalog.py` 產生。授權見 `library/peeps/LICENSE.md`。
build 只會內嵌場景與 project.json 裡出現的部件名稱，所以部件名稱要寫成字串字面值（`'Smile'`），不要用字串拼接。
