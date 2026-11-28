# canvas-motion evals

三個測試情境，檢驗 SKILL.md「先確認方向，再投入製作」與講解片「讀懂檢查」是否生效。

| 情境 | 檢查什麼 |
|---|---|
| article-video-direction-first | 研究文章做成 FB 知識片：先問成功標準、樣張先於場景程式、FB 4:5、前兩幕定義名詞、先給架構地圖、保留限制與開放問題、結尾重點回顧 |
| freestyle-offers-style-samples | 風格自由發揮：給 2 種以上風格的實際圖、是快速靜態圖、不整支做完、請使用者挑 |
| repeated-rejection-goes-back-to-samples | 同一問題被否定兩次：退回便宜的樣張、15 分鐘內、具體去雜亂規則、要參考圖或給圖挑 |

## 怎麼跑

- 用 Claude Code：在 skill 資料夾執行 `claude plugin eval . --allow-tools Write,Edit,Bash --scaffold`（會實際呼叫模型、計費）。
- 或用 skill-creator 的流程：新版與舊版快照各跑一次，逐條評分，再用 eval viewer 檢視。

## 第一次結果（2026-11-28，各跑 1 次）

新版通過率 100%，改版前舊版 67.7%。差異最大的是知識片情境（7/7 對 3/7）。
