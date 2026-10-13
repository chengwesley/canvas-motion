# 畫風零件（library/looks.js）

10 種畫風，**構圖不寫死**。畫風只決定「怎麼畫」（天空、太陽、雲、圖層填色、主體填色、最上層質感），畫什麼、放哪裡由構圖決定。構圖要先開放問使用者（見 SKILL.md 第 2 節），不要套固定畫面。

範例與回歸測試：`examples/look-gallery`（同一個構圖 × 10 種畫風，最後一幕示範自訂主體）。

## 畫風一覽

| 名稱 | 畫風 | 特徵 | 適合的情境 | 程度 |
|---|---|---|---|---|
| `anime` | 動畫風背景 | 長漸層天空、放射光、分色雲、稜線亮邊、逆光 | 情緒短片、片頭、MV、故事開場 | 背景很好；人物只到簡化風 |
| `water` | 水彩 | 濕中濕暈染、濕邊、顆粒、紙紋、上淡下濃 | 溫暖故事、品牌、節慶、繪本感 | 好，偏數位水彩 |
| `ink` | 水墨 | 墨色濃淡、雲霧留白、飛白、朱印 | 文化、東方主題、典故、節慶 | 好 |
| `flat` | 扁平插畫 | 幾何色塊、無描邊、同心圓太陽 | 產品介紹、說明動畫、商業簡報 | 很好 |
| `pixel` | 像素 | 整幕 1/6 解析度、最近鄰放大、抖色色帶 | 電玩、復古、活動、社群 | 好 |
| `neon` | 霓虹合成波 | 條紋太陽、透視網格、發光線框、掃描線 | MV、尾牙、潮流、科技活動 | 很好 |
| `poly` | 低多邊形 | 三角面、依面向與高度上色 | 科技、風景、資料視覺背景 | 中上 |
| `paper` | 剪紙 | 紙層投影、纖維紋理、紙偶晃動、掛線雲 | 童趣、繪本、節慶、教育 | 很好 |
| `comic` | 美漫網點 | 網點陰影、粗描邊、速度線、分格框、狀聲字 | 活動宣傳、社群短影音、衝擊感 | 很好 |
| `crayon` | 蠟筆 | 同向短筆觸、紙面顆粒、逐格抖動 | 兒童、手作感、溫馨 | 中上，筆觸略規律 |

**做不到的**：擬真人物、動畫原畫等級的角色臉部與表情、特定插畫家的畫風。需要時請使用者提供有授權的圖片素材。

## 用法一：L_look 當背景（資料驅動）

背景構圖寫在該幕的 `data`，在自訂場景第一行呼叫 `L_look(t, T, pulse, s)`，主體再疊在上面（每一幕仍是 `s` 開頭的自訂場景，storyboard.py 不接受 `L_look` 直接當 fn）：

```json
{ "fn": "sValley", "bars": 3, "energy": 0.5, "data": {
  "look": "ink",
  "horizon": 0.6,
  "sun": { "x": 0.72, "y": 0.4, "r": 0.07 },
  "clouds": 2,
  "layers": [
    { "ridge": { "base": 0.57, "amp": 0.17, "seed": 5 }, "color": "hill1", "parallax": 0.02 },
    { "ridge": { "base": 0.67, "amp": 0.12, "seed": 9 }, "color": "hill2", "parallax": 0.05 },
    { "points": [[0,0.9],[0.3,0.8],[0.6,0.88],[1,0.92],[1,1],[0,1]], "color": "ground", "parallax": 0.13, "solid": true }
  ],
  "particles": { "n": 20, "color": "petal" },
  "seal": "春",
  "caption": { "title": "…", "note": "…" },
  "port": { "horizon": 0.55, "sun": { "x": 0.6, "y": 0.35, "r": 0.08 } }
} }
```

| 欄位 | 說明 |
|---|---|
| `look` | 畫風名稱（上表） |
| `pal` | 覆寫色盤的部分顏色；色名見 looks.js 各畫風的 `pal`（常用：sky1–4、sun、hill1–3、ground、petal、label、ink） |
| `horizon` | 地平線位置（畫面高度比例），影響天空漸層、光芒裁切、水墨雲霧 |
| `sun` | `{x, y, r}`，x/y 為畫面比例、r 為短邊比例；`null` 不畫。月亮、光源都可以用它 |
| `clouds` | 數量（0–4，用預設位置）或 `[{x, y, size, speed}]`；畫風沒有雲（ink、pixel、neon、poly）時略過 |
| `layers` | 由遠到近。`ridge`：山稜線（base 基線比例、amp 起伏、seed 形狀）；`points`：任意多邊形（0–1 座標，可畫城市天際線、海面、建築剪影、道路）；`grid`：透視網格地面。`color` 可以是色名或顏色；`parallax` 越近越大；`solid` 表示前景實心層（預設最後一層） |
| `particles` | 飄落粒子：花瓣、雪、火花、落葉（改 color 與 size） |
| `seal` / `sfx` | 朱印文字（水墨）／狀聲字（美漫）；任何畫風都能用 |
| `caption` | 左下角的標題與說明（有底板，任何背景都讀得到） |
| `camera.push` | 鏡頭推進速度，預設 .01 |
| `port` | 直式專屬構圖：以上任一欄位的覆寫。直式不是等比縮小，地平線、太陽、圖層通常都要重排 |

## 用法二：自訂場景＋畫風（畫任何主體）

構圖裡有具體主體（人物、建築、交通工具、動物、產品）時，在自訂場景裡用 `withLook` 包住繪製，主體用 `lookShape` 填色，就會自動套上該畫風的畫法（剪紙有投影、美漫有粗描邊、霓虹有發光邊、像素會被像素化……）。

```js
function sCastle(t, T, pulse, s) {
  L_look(t, T, pulse, { ...s, data: { ...s.data, caption: null } });   // 背景交給 L_look
  withLook(s, t, pulse, (L, P) => {
    lookShape(L, P, () => { ctx.beginPath(); ctx.rect(W * .4, H * .5, W * .2, H * .3); }, 'hill3');
    lookShape(L, P, () => { ctx.beginPath(); ctx.moveTo(W * .38, H * .5); ctx.lineTo(W * .5, H * .35); ctx.lineTo(W * .62, H * .5); ctx.closePath(); }, 'scarf', { lw: 2 });
  });
  lookExtras(t, s);   // 朱印、狀聲字、標題
}
```

- `lookShape(L, P, 建立路徑的函式, 色名或顏色, { lw, rim })`
- 主體的動作（擺動、呼吸、移動）自己用 `t` 算；保持 `rng()`、不用 `Math.random()`。
- 同一個場景把 `data.look` 換掉，主體就換畫風；適合做「同一主體、多種畫風」的比較。

## 選畫風的原則（提案時說明理由）

- 先看**情緒與場合**：溫暖 → water／paper／crayon；東方文化 → ink；商業說明 → flat；衝擊、活動 → comic／neon；懷舊電玩 → pixel；情緒、故事 → anime。
- **一支片通常一種畫風**；要換畫風時用轉場明確切開（例如回憶段落改 water）。
- 使用者點名畫風就照做；沒點名時依情境建議一種，並說明跟其他候選的差別。
- 品牌色：用 `pal` 覆寫 sky／hill／ground 等主要色，維持畫風的質感。

## 常用形狀（LK_SHAPES）

自訂主體不用從零寫路徑。每個形狀回傳部件陣列，交給 `lookDraw` 畫，會自動套用當前畫風（剪紙有投影、美漫有粗描邊、霓虹發光、像素會被像素化）。座標：`x` 是水平中心、`y` 是底部（站在地上的位置），尺寸是像素。

| 形狀 | 呼叫 | 部件（可用 colors 覆寫） |
|---|---|---|
| 房屋 | `LK_SHAPES.house(x, y, w, colors)` | body、roof、door、win |
| 室內一角 | `LK_SHAPES.room(x, y, w, h, colors)` | wall、floor、win、frame |
| 紙張 | `LK_SHAPES.paper(x, y, w, h, r, colors)` | sheet、line |
| 螢幕 | `LK_SHAPES.screen(x, y, w, colors)` | frame、glass、stand |
| 手機 | `LK_SHAPES.phone(x, y, h, colors)` | body、glass |
| 人形剪影 | `LK_SHAPES.person(x, y, h, 'stand'|'sit', colors)` | body、head |
| 樹 | `LK_SHAPES.tree(x, y, h, colors)` | trunk、leaf、leaf2 |
| 車（側面朝右） | `LK_SHAPES.car(x, y, w, colors)` | body、glass、wheel |

```js
withLook(s, t, pulse, (L, P) => {
  lookDraw(L, P, LK_SHAPES.house(W * .3, H * .82, MIN * .25, { roof: 'sun' }));
  const c = anchorLerp('carStart', 'carEnd', tw(t, BEAT, T - BEAT * 2, 'io'));   // 跨幕錨點見 api.md
  lookDraw(L, P, LK_SHAPES.car(c.x, c.y, MIN * .2));
});
```

人形剪影只是能擺進構圖的「人」，不是角色骨架：沒有關節動作，要移動就改座標或外層 `ctx.rotate`。需要表情、動作豐富的角色時，請使用者提供角色圖片。完整示範：`examples/shapes-demo`。

## 一支片混用多種畫風

1. 用轉場明確切開（fade／wipe），不要在同一幕混兩種畫風。
2. 用 `pal` 讓兩種畫風共用主色（例如 sun、hill2、label 設成同一組品牌色），看起來仍是同一支片。
3. 每種畫風的幕都要各自有直式構圖（`port`），不能共用橫式座標。
4. 常見用法：主線用扁平或剪紙，回憶或想像段落改水彩；科技主線中插一段霓虹做高潮。

## 品牌

- 品牌色：用 `pal` 覆寫主要色（sky、hill、ground、sun、label），保留畫風的質感；文字用 `txtPlate` 確保讀得到。
- Logo：SVG 轉成 `Path2D` 用 `lookShape` 畫（會套畫風），PNG 轉 data URI。使用前確認使用者有權使用；沒有 Logo 檔就用文字字標，不要自己畫仿製的 Logo。
