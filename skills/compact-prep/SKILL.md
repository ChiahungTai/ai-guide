---
name: compact-prep
description: "壓縮邊界的 boundary adapter：①持續外部化義務——工作中持續把接續狀態落檔（checkpoint＋durable owner），compact（manual 或 auto）何時發生皆不丟；②恢復接線——新 context 開口消費 scripts/compact_checkpoint.py 的驗證/proven/cleanup（hook 注入與 fallback 走同一驗證）。不解決壓縮本身（harness 擁有）、不自製 compactor；外部化內容取捨（判斷面）仍是 LLM 職權。"
when_to_use: "① session 工作中——維護 checkpoint 與 durable owner（持續責任制，無事件依賴）；② 新 context 開口（compact 後／resume）——恢復接續時走本 skill 的恢復流程；③ 交接包／compact 摘要品質需審計時（compact-audit 搭檔）。觸發詞：checkpoint、context 外部化、compact 恢復、restore-proven、compact-audit。跨 session／repo 交接屬 handoff、usage reset 自動接續屬 at——兩者不做本 skill 的 checkpoint 義務，不重疊。"
---

# compact-prep：壓縮邊界 boundary adapter

> **定位（AIR-155）**：compact 事件不可觀測（ZCode 0922 gate VETO：兩次獨立 /compact 實測不派發 SessionStart，無 matcher 亦然；auto-compact 閾值各 harness 不受控）→ 放棄 compact-moment 觸發，checkpoint 轉**持續責任制**——工作中持續落檔，狀態永遠已在檔上。
>
> **manual/auto 雙情境語義並列**：codex hooks 以 matcher 分流 PreCompact(manual|auto)（學理依據：manual 與 auto 是兩個 lifecycle 事件），但兩者對 checkpoint 的要求同構——持續責任制使分流失去意義：user 手動 /compact 或 harness auto-compact 何時發生，接續材料都已在檔上。本 skill 條文不區分兩情境，也不依賴任何 compact 事件存在。

## 義務一：持續外部化（持續責任制，無 compact 事件依賴）

前提（CC compaction 保留矩陣機械化）：

- **conversation state 必死**——對話訊息面壓縮即換摘要、不保證 verbatim（A/B 實測：指示要求 verbatim 無效）→ 工作中持續落檔。
- **CLAUDE.md／rules／skills 本體 harness 重注入**——每輪 context 重建自動在場 → 不用抄。

**義務清單**（每次實質進展後更新；落點優先序＝durable owner 先：EP 進度節→journal→user 指定 report，定義源＝[task-recovery](../_common/task-recovery.md)「寫入端」）：

1. **決策與理由**（含排除方案）
2. **evidence 指針**（已驗／未驗證據、檔案路徑、測試結果與錯誤 verbatim）
3. **dirty 邊界**（scope/cwd/baseline＋本弧未提交變更）
4. **pending actions**（未執行命令、待確認提案、背景 job 與收法）
5. **invariants**（不可違反約束、授權範圍——checkpoint 不擴張授權）

**checkpoint 檔**：落點由 `scripts/compact_checkpoint.py` 的 `checkpoint_paths(cwd, session_id)` 給出（單一源，禁手拼）——`<cwd>/.agent-tmp/compact-checkpoints/<session_id>/checkpoint.json`，與 restore-proven receipt 成對同目錄。欄位照 task-recovery 十欄映射（四問必要：objective/completed/next_action/pending；弧起點空 list 是合法回答）。**寫入即驗證**：`validate_checkpoint(load_checkpoint(...))`——壞檔 fail-loud 禁靜默續行。

**內容政策**（承接 preserve-list）：脈絡壓縮非時序流水帳；素材範圍＝全 session 非尾端窗口；需逐字保存的錯誤／findings 原文例外於「引用不重抄」；選擇標準是相關性不是對話位置。

**lessons（十欄之外 optional，觸發式建議非義務）**：觸發——本 session 發生同錯重犯或 user 糾正致行為變更時，checkpoint 加 `lessons: string[]`：≤5 條、一行一條、「下次做 X 而非 Y」形（mistake→correction 語義）；無傷疤 session 省略合法。抽源判準：journal 已記＋實際發生＋correction 已確認或行為已變更，且「接續者不看會重犯」；排除 transient failure、純風格偏好、未驗證風險、設計內行為（如介面記憶歸零）。隱私：路徑一律 repo-relative、禁 secret/home 名。分界：lessons 是 session-local scar，checkpoint lessons 永不自動晉升——跨 session 教訓走 rules/skills/memory 晉升（memory-audit）。讀取面：lessons 被讀到靠恢復流程 step 1 讀 checkpoint 全文，非 hook 注入（hook 只給 thin pointer）。

**memory 候選整理（可選，非救援必要路徑）**：落盤成功後才做；usage 不足／無寫權／gate 故障時跳過並記交接待辦——不得跳過後宣稱已蒸餾。

## 義務二：恢復接線（新 context 開口）

兩個入口走**同一驗證**（`scripts/compact_checkpoint.py` 的 validate_checkpoint／verify_restore_proven／assert_cleanup_allowed——機制單一源，任何入口不重寫判準）：

1. **hook 注入（已註冊環境）**：ZCode UserPromptSubmit hook `hooks/compact-restore-inject.py`——每次 user prompt 查本 session 未消費 checkpoint，有則注入 **thin pointer**（路徑＋sha256＋head/tail 預覽；禁全文進 context，codex spill 語義同構：接續材料以檔案承載、context 只帶指針）；無 checkpoint 靜默；已 proven（消費）即靜默。
2. **fallback（未註冊／其他 harness）**：新 context 開口先查 `checkpoint_paths` 指向的檔存在與否，存在即照同一恢復流程。

**恢復流程**（恢復順序單一源＝[task-recovery](../_common/task-recovery.md)「恢復順序」）：

1. 讀 checkpoint → `validate_checkpoint`（四問可答；壞檔 fail-loud——損壞比缺失更危險，禁靜默續行）
2. 依 task-recovery 恢復順序核對實物（checkpoint hash 是比對依據非回滾目標）
3. 驗證通過 → `write_restore_proven` 發 proven receipt（綁 checkpoint 內容 sha256）
4. proven 後 hook 自動靜默；未 proven 前 `assert_cleanup_allowed` 擋 cleanup——禁清 checkpoint／proven（recovery artifact）

## 搭檔：compact-audit（重大弧線選配，高成本）

壓縮後摘要品質審計：spawn 乾淨 context agent 讀 session DB 獨立提煉 15-20 條關鍵要點 → 與壓縮摘要三色比對（✓保留／△細節流失／✗遺漏）。成本量級：數 M tokens／數分鐘——**僅重大弧線 session（deep-work／多 EP）壓縮後跑**，例行壓縮不跑。

agent prompt 須內嵌的非顯知識（2026-08-24 mosaic dogfood 實測）：摘要以 user-role message 注入 DB 須明確排除（否則是抄摘要非獨立）；全域時序錨用 `message.sequence`（`part.sequence` 是 per-message）；session 錨定須 join message 限定 user-role part（裸 `part.data LIKE` 會誤中後 spawn 的 subagent session）；part types：text／tool／reasoning／compaction／step-start／step-finish／timeline。

## 邊界

- 不做壓縮、不產摘要、不自製 compactor（harness 職責）；外部化內容取捨＝LLM 判斷面，機制面只保證「任何時刻都有一份可機械驗證的檔」。
- **ZCode**：compact 事件 VETO（2026-09-22 gate 判決：3.14 兩次獨立 /compact 實測不派發 SessionStart——0824 舊實測為真，hooks 文檔的 compact source 真機不存在）→ 本 skill 不依賴任何 compact 事件；restore 注入走 UserPromptSubmit hook（註冊片段與協議見 `hooks/compact-restore-inject.registration.json`＋`hooks/compact-restore-inject.INSTALL-PROTOCOL.md`；未註冊機器走 fallback）。
- **Claude Code**：SessionStart(compact) hook 已註冊（`hooks/compact-tail-inject.py`，settings.json matcher=compact——機械 verbatim 復原層，自動注入 raw tail）；本 skill 的 checkpoint／restore 流程在 CC 端以 fallback 形態適用（CC 無 scripts 慣例路徑差異時照 `checkpoint_paths` 相對 cwd 落點）。
- 跨 session／repo 交接屬 handoff、usage reset 自動接續屬 at——兩者不做本 skill 的 checkpoint 義務，不重疊。
