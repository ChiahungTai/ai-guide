# post-build 檢查點

已完成本項文件契約審查。

## PB1 — Important / confirmed：用副檔名決定有無行為審查，控制面變更可繞過整條 review/judge 鏈

證據：post-build:27-31 純 .md 不跑 code 鏈；41-60 review/judge/followup/EP 情境對帳都只在 code 鏈；64-67 docs 鏈只有逐檔 consistency 與條件式 metadata。consistency:151-153 明定單檔內部自洽。反證源 code-review:80-82 已提供 docs-mode 正確性、架構、行為覆蓋及 phantom 偵測。

反例：只改 judge-review.md 的決策落點，該檔內部自洽，但未改 post-build 的讀取落點 → docs 鏈每檔 pass，跨命令交接破裂未被指定審查覆蓋。

建議：把 product 載體與 review 需求分開：文字修飾可走 consistency；會改 LLM 行為/跨檔合約的 Markdown 走 docs-profile review/judge。無需對 docs 跑 Python tests。

驗收：上述只改 producer 路徑的 fixture 必須進 docs-profile 跨檔 review；純 typo 不需要全鏈。static HTML/互動 JS 的模式判定也應直接消費 EP 已定義的規則，避免 implement:40 的舊偵測再定義一套。

## PB2 — Important / confirmed：resume 以帳本存在/open 判斷，沒有核對它審過哪個 revision

證據：post-build:35 有 .review 且 open 就跳 code-review；workflow-review-pattern:103-108 的 Finding Record 無 task baseline/reviewed revision/diff identity。branch 名只能識別容器，無法識別被審產品。

反例：F1 產出後有新 code 修改，同 branch 再 post-build；舊帳本仍 open → 跳審查 → 只裁決舊 finding，新修改未進 initial review。diff 增量 ≥3 檔補審只針對收尾期間，且不涵蓋 resume 前改動/單檔重大變動。

建議：resume 需核對 task 與 reviewed content identity；不匹配時保留舊 finding 但審新增變動。reviewed identity 是帳本 metadata，不必給每列塞重複欄位。

驗收：相同內容 resume 不重審；新單檔行為修改 resume 必補 delta review；adopted/implemented 中斷能按狀態接正確步驟，不能只認 open。

## PB3 — Important / confirmed：完成狀態有兩個不同時點的 writer

證據：implement:251、258 與 metadata-sync:27、40、44 在 build 階段 5a 結案/歸檔/✅；illustrate-html-mode:94 說同時卡仍 In Progress，95 把結案放 post-build hook 2。post-build:59 允許後續修正 loop 未收斂退出。

反例：build 層已 Done/歸檔，post-build 發現 Important 並三輪未修好 → 停下；沒有明確 rollback/reopen Done 與 badge 的契約。不能靠「未 commit」掩蓋：board/下一 session 仍可讀工作樹的已完成狀態。

建議：定義 Built 與 review-complete 的狀態分界，只有最後有效完成 gate 能發布 Done/✅；無 post-build 的 fallback 是同一 gate 的替代入口。不是把 local metadata 移到 commit 後。

驗收：post-build 失敗、needs-confirmation 未決、途中停止時，不留下宣稱最終完成的 Done/badge；成功與 standalone fallback 都有唯一 finalization owner。

## PB4 — Suggestion / evidence-based：收尾 loop 的最後產品與先前測試證據未顯式綁定

implement:157 全量測試在 review/apply 前，224 apply 只明列 ruff；post-build:57-60 apply 後交 followup 與情境覆蓋核對，followup:86 只明列 git diff+Read。全域修改後必執行驗證可補這一洞，因此不報「允許完全不測」。但本鏈沒有明示先前全量結果在修正後失效、哪些受影響證據須重生。

建議：apply 後使受影響驗證過期並按變更風險重跑；完成報告只列對當前產品仍有效的證據。不要無條件每輪重跑整個 repo。

## 架構想法

post-build 正朝 review 編排、metadata 結算、corpus 存量修復、圖表渲染、暫存清理的多重 owner 膨脹。既有 tour 存量修復是明確政策，這次不擅自否定；但應把「本弧可交付」與「附加維護結果」分開報告與重試，避免一個不相關存量問題拖住整弧。
