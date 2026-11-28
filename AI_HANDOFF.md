# AI Handoff

## 2026-11-28 | Claude | 家裡

- 完成：
  - 用 canvas-motion 把 Anthropic〈The components of agent memory〉做成 FB 4:5 知識影片，四版後定稿為 v4 像素科技城市版（機器人 Agent、四層記憶關卡地圖、對話框字幕，116 秒）。成片在 `~/Antigravity/projects/agent-memory-v4/final/`（1080×1350 正式版與 720×900 手機版）。
  - PR #1（已合併）：SKILL.md 新增「先確認方向，再投入製作」；agents.md 新增 2.5 平行製作規格與審查定位；other-engines.md 新增 3.1 讀懂檢查；新增 references/prerendered-assets.md；_vo.py 字幕不再切開數字；sheet.py 支援 4:5。
  - PR #2（已合併）：新增 references/style-catalog/，20 種風格樣張，其中 10 種有完整 style.md（指標畫法、代表畫家與作品、配色色階、元件清單、原創界線等）。README 列狀態、補寫規則與「要再畫得更好」的步驟。
- 下次：
  - PR #3（查證＋精修）等使用者審核合併。
  - （已完成 2 種）扁平向量、漫畫網點已精修（元件表＋三輪）；其他風格可照同法，並可考慮下載公開館藏參考圖並排比（需使用者同意下載）。
  - 補完另外 10 種風格的 style.md；水墨、水彩、世紀中期的樣張小字有缺字要修。
  - （已完成）FB 貼文已改成配合 v4 影片，並用 ask-wesley 檢查過。
- 注意：
  - 10 份指引的代表畫家與作品已上網查證（VERIFY_LOG_A/B.md），少數生卒年仍依知識填寫。
  - v4 專案 scenes/ 裡的 `zz_end.js` 必須是最後一個載入的檔（遮蔽了引擎的 cam／frame／hud 撞名），新增或改名場景要同步改它。
  - style-catalog 資料夾約 30MB，大多是樣張 PNG。
  - 使用者偏好：先給元件稿或樣張確認再做影片；元件確認後要快、少審查。
