---
name: compact-prep
description: "當你要跑 /compact 壓縮對話前，外部化前置：掃全 session 產脈絡外部化檔（結構化 preserve-list，禁時序流水帳），然後請 user 執行 /compact；memory 候選整理是落盤後可選步驟、非救援必要路徑。不解決壓縮本身（harness 擁有），只解決 compact 後的接續材料。"
---

# compact-prep：/compact 的前置外部化

> 背景：/compact 的摘要會壓掉 verbatim 交付物（實測 A/B：指示要求 verbatim 無效）、re-injection 快照可能過時。結構性解法＝compact 前把接續材料落檔。

> **產出方針**：① **脈絡壓縮非時序流水**——落檔按任務脈絡結構組織，禁逐輪對話照抄；② **素材範圍＝全 session**——掃整個對話的任務結構（目標/決策/懸掛），非尾端幾筆對話窗口。preserve-list 語義與 [ai-development-guide](../../ai-development-guide.md)「Summary Instructions（壓縮策略）」同源。

## 步驟

1. **定位當前 session（自我錨定，禁用「取 db 最新 session」法——同 worktree 並行 session 會撈到別的 session）**：以本 skill 的調用字串為錨——**必須 join message 限定 user-role part**：`SELECT DISTINCT p.session_id FROM part p JOIN message m ON p.message_id=m.id WHERE p.data LIKE '%compact-prep%' AND json_extract(m.data,'$.role')='user' ORDER BY p.time_created DESC LIMIT 1;`——裸 `part.data LIKE` 會誤中**後spawn 的 subagent session**（其繼承 context 含 skill 內文，時間戳更晚；2026-08-31 實測錨到 subagent）。另注意 schema：role/type 都在 data JSON 內（`json_extract`），無獨立欄位。撈出後抽查該 session 最後一則 user part 是否為本次調用，確認非鄰近 session 誤中。
2. **落檔脈絡外部化檔**：**durable owner 優先**——先更新既有 EP 進度＋必要 evidence 檔（無 EP 用既有 `.agent-tmp/session-journal.md`；user 指定 report 則用該 report），checkpoint 欄位見 [task-recovery](../_common/task-recovery.md)「寫入端」；compact-context 檔保留作交接包——引用 durable owner 而非重抄內容，需逐字保存的錯誤／findings 原文例外。掃**全 session**（`message.sequence` 全程，非尾端窗口）提煉接續材料，寫入 `<repo>/.agent-tmp/compact-context-<date>.md`（檔頭標註 session id 與時間）。內容按 preserve-list 結構組織（非時序流水）：任務目標與待辦／已決策＋理由／已讀改檔案路徑／測試結果與錯誤訊息（verbatim）／懸掛動作（未執行命令、待確認提案、背景任務）／計數（verbatim）。關鍵交付物原文（錯誤訊息、findings）逐字保留——**選擇標準是相關性，不是對話位置**。
3. **memory 候選整理（可選——落盤成功後才做，非救援必要路徑）**：本 session 的裁決/教訓是否值得寫 memory（cluster-first）？有 → 補寫。usage 不足／無寫權／gate 故障時跳過並記交接待辦——不得跳過後宣稱已蒸餾。
4. **交付確認**：印出 context 檔路徑＋摘要（涵蓋哪些任務脈絡、多少字元），然後請 user 執行 `/compact`，並**明確提醒 user：compact 後開口第一句讓 AI 讀 context 檔**（例如「讀 context 檔續任務」）——新 context 的 AI 不知道檔案存在，沒有這句步驟 5 不會發生。
5. **compact 後恢復**（無 hook 注入的環境；恢復順序單一源＝[task-recovery](../_common/task-recovery.md)「恢復順序」）：被 user 提醒後先讀 context 檔恢復任務脈絡，再繼續任務；已註冊 SessionStart(compact) hook 的環境 raw tail 已自動注入 context（verbatim 復原層），讀 context 檔補結構化脈絡後續任務。
6. **清理**：context 檔恢復用途完成後即無價值——依 `.agent-tmp/` 既有清理紀律處理（互動模式完成時列清單保留/刪除）。

## 搭檔：compact-audit（重大弧線選配，高成本）

壓縮後摘要品質審計：spawn 乾淨 context agent 讀 session DB 獨立提煉 15-20 條關鍵要點 → 與壓縮摘要三色比對（✓保留／△細節流失／✗遺漏）。成本量級：數 M tokens／數分鐘——**僅重大弧線 session（deep-work／多 EP）壓縮後跑**，例行壓縮不跑（與 callstack 生成同成本紀律：高成本操作獨立觸發）。

agent prompt 須內嵌的非顯知識（2026-08-24 mosaic dogfood 實測）：
- 壓縮摘要以 **user-role message** 注入 DB——獨立提煉須明確排除該 message（否則是抄摘要非獨立）
- `part.sequence` 是 per-message 非全域錨；全域時序錨用 `message.sequence`
- part types：text／tool／reasoning／compaction／step-start／step-finish／timeline

## 邊界

- 不做壓縮、不產摘要（harness 職責）；只做 compact 前外部化＋compact 後恢復指針。
- **ZCode：SessionStart(compact) hook 已實測死路（2026-08-24 L4 終驗：compact 不派發 SessionStart 給 config hooks）——步驟 2/4/5 全跑，hook 分支不適用**。Claude Code：SessionStart(compact) hook **已註冊**（`hooks/compact-tail-inject.py`，settings.json matcher=compact，2026-08-30 接線；tail 原文取自 CC transcript JSONL）——hook 是**機械 verbatim 復原層**（自動注入 raw tail；腳本做不了脈絡壓縮）；本 skill 職責＝步驟 2 脈絡外部化檔＋**步驟 3 memory 候選整理（可選，非救援必要路徑）**（皆 LLM 判斷層）＋步驟 4 讀檔提醒（hook 注入的 raw tail 不含 context 檔存在資訊）。
- Claude Code 環境同樣適用（db 路徑改為該環境的 session 儲存；無 db 時步驟 1-2 改為模型直接從自己 context 提煉脈絡外部化檔——context 內含全程任務脈絡，非尾端窗口）。
