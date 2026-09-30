# 角色：figure.js

程序化人偶：骨架（正向運動學）＋姿勢＋表情＋三種精細度＋類型畫法。能演戲、能被看懂，但不是擬真人物或動畫原畫等級的臉；需要特定長相時請使用者提供有授權的圖。

## 建立與繪製
```js
const F = figCast('leo', H * .5);                       // 從 project.json 的 cast 建立（連戲靠它）
figDraw(F, x, groundY, figPose.walk(t / 1.2), { t, dir: 1, view: 1, face: EXPR.happy, rim: '#ffc940' });
```
- `props`（比例）：`flat` 插畫修長、`cute` 大頭可愛、`chibi` 2.5 頭身、`cartoon` 5、`teen` 6.5、`anime` 7.5、`real` 7.5、`hero` 8.5、`hk` 9。分段比例取自人體測量常數，依頭身推算。
- `detail`：`stick`（火柴人）、`mannequin`（人偶）、`full`（衣服、頭髮、臉）。
- `render`：**`illus`（扁平插畫風，人物主角的預設首選）**、`flat`、`cel`、`anime`、`amcomic`、`hkcomic`、`silhouette`。
  `illus` 用曲線輪廓、粗圓頭連續四肢、大塊髮型剪影、點眼簡化五官、無描邊加柔和陰影；程序化畫人最好看的風格。搭配 `props: 'flat'`（修長）或 `'cute'`（大頭可愛）。
  膠囊人偶畫法（cel、hkcomic 等）在特寫會顯得像關節人偶，適合遠景、剪影或漫畫類型。
- `hair`：`short`、`spiky`、`long`、`bun`、`none`；`outfit`：`sleeve`（long／short／none）、`legs`（pants／shorts／skirt／robe）、`cape`、`sash`（會跟著 `sway` 甩）。
- `dir` 面向（1 右、-1 左）、`view` 0 正面到 1 側面。腳會自動著地（`ground: false` 關掉，跳躍、特寫用）。

## 姿勢
- 循環：`figPose.walk(phase, k)`、`figPose.run(phase, k)`（關鍵影格表插值，手臂比腳晚 1–2 格），`figPose.idle(t)`。
- 關鍵姿勢：`stand`、`crouch`、`leap`、`land`、`cheer`、`point`、`think`、`sit`、`horse`（馬步）、`bow`（弓步）、`punch`、`chamber`（收拳）、`kick`、`hero`（叉腰）、`fall`。
- 表演：`figPose.seq(t, [[0, 'stand'], [.6, 'crouch', 'io'], [1.2, 'leap', 'expo']])`；`figPose.mix`、`figPose.add` 疊加。
- **不滑步**：往前走的距離 = `figStride(F, 'walk') × 週期數`。

## 表情
`EXPR.neutral／happy／laugh／angry／sad／surprised／determined／fear／shout`，`figExprMix(a, b, p)` 漸變。自動眨眼（閉快睜慢、偶爾連眨）。說話時嘴巴開合：`{ ...EXPR.neutral, mouth: 'open', open: .15 + .25 * Math.abs(Math.sin(t * 11)) }`。

## 取景
- `figFrame(F, x, groundY, 'ELS'|'LS'|'MS'|'CU'|'ECU')` → `shot()` 用的鏡頭。
- 特寫：`const at = figPlace(F, pose, 頭x, 頭y, { dir, view }); figDraw(F, at.x, at.y, pose, { ..., ground: false })`。

## 表演原則
- 先定動勢線（C 或 S 形），關鍵姿勢四肢離開軀幹，填黑剪影也看得懂。
- 左右不要完全對稱；一次只讓一個主動作發生。
- 力量集中在 2–3 格內爆發，前面要有預備、後面要有停頓。
- 同一場戲裡角色的面向（`dir`）不要亂換（見 crew.md 場記）。
