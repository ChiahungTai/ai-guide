# 三條 ZCode cron 重建 spec（2026-09-14 ai-rules→ai-guide 改名掃尾）

> 背景之三行：ZCode cron 是 workspace-path-scoped——repo 改名後舊排程掛在失效 workspace key 下休眠（新 workspace `CronList` 空），須重建。原 prompt 從 session db（`~/.zcode/cli/db/db.sqlite` part 表 CronUpdate payload）考古還原，僅做 `ai-rules`→`ai-guide` 路徑替換，其餘逐字保留（codex 裁決：禁趁機改寫）。
> **harness 限制**：一個 session 只能建一條排程（建立後 session 即綁定，第二條被拒：「Cannot create a scheduled task inside a session that already belongs to a scheduled task. Ask the user to start a new chat」）——每條須開一個新 session 逐一建立。

## ① 每晚 23:40 memory 收斂——✅ 已建（本弧）

- automationId：`automation-c9eb6495-2301-4fb7-bf18-81e244b135a9`（active；nextRun 首發＝2026-09-14 23:40）
- 對應舊 id：`automation-751ecce2-a79c-4309-a79c-08486e2ee893`（休眠）

## ② 每週日 23:00 治理看照——✅ 已建（2026-09-14 掃尾 session）

- automationId：`automation-23c773b9-52a0-46ba-a1f5-777a6f3261bf`（active；nextRun 首發＝2026-09-20 23:00）
- 對應舊 id：`automation-fed036ff-17bf-4cf0-a50e-3216a7de6665`（休眠）
- prompt 來源：db 考古（fed036ff 最後 CronUpdate payload ts 1788997150600）`ai-rules`→`ai-guide` 全替換（13 處；title 無 ai-rules 無需替換）——payload 內 4 處 `\"`、1 處 `\\.` 字面反斜線序列為原始內容，逐字保留未修；考古暫存＝`.agent-tmp/cron-archaeology-fed036ff.json`＋`.agent-tmp/prompt-2-replaced.txt`

## ③ 每週六 23:10 糾正週報——待建（新 session 貼此 spec；09-14 於已建條 ② 的 session 試建第二條被 harness 拒，constraint 實證仍有效）

- title：`每週六 23:10 糾正週報＋CR 使用健檢（corrections-weekly skill）`
- cron：`10 23 * * 6`，recurring=true
- 對應舊 id：`automation-370fafc5-a050-479e-b62f-9c7988d23521`（休眠）
- prompt 全文（直接複製）：

```text
糾正模式週報＋CR 使用健檢（T3-1＋09-03 擴，每週六 23:10，ai-guide workspace 新 session）：用 Skill tool 調用 `corrections-weekly` skill（無參＝本週 7 天窗）。skill 內含完整雙職步驟（mine_corrections.py 撈糾正候選＋cr_usage.py 量 CR 消費指標→LLM 判讀分類→append ai-analysis/reports/corrections-<YYYY-MM>.md）與紀律（DB 唯讀、一頁、腳本失敗 2 次即止、CR 段 advisory）。若 skill 清單中不可見（快照異常），fallback＝直接讀 /Users/ctai/Github/ai-guide/skills/corrections-weekly/SKILL.md 照步驟執行。

【2026-09-14 改名註記】本排程原掛 ai-rules workspace（automation-370fafc5），repo 改名 ai-guide 後 workspace key 失效，由本排程原樣重建（僅 ai-rules→ai-guide 路徑替換，prompt 其餘逐字保留）。
```

> 【09-14 掃尾後狀態】僅剩 ③ 待建：建新 session 後把上節 ③ 的 title／cron（`10 23 * * 6`，recurring=true）與 prompt 全文（已內嵌本檔，直接複製）貼入 CronCreate 即可，**無需 db 考古**。② 的考古已由掃尾 session 完成（來源記錄見 ② 節）。
