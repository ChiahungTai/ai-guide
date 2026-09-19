---
id: AIR-82
title: corrections-weekly cron 首跑靜默空轉——投遞被 session 歷史誤讀為對齊檢查（09-06 零產出、09-12 產出誤標手動）
status: Done
assignee: []
created_date: '2026-09-12 21:35'
updated_date: '2026-09-19 21:04'
labels: []
dependencies: []
references:
  - ai-analysis/schedule-registry.md
ordinal: 68000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
修復 corrections-weekly cron 投遞在綁定 session 的語義誤讀失敗態：cron prompt 祈使化重寫＋下輪 fire 實證執行與歸因正確
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Cron prompt 重寫為祈使執行框架——對照 nightly 收斂 cron 實證（🔴 排程頭＋「你是 autonomous…session」角色指派＋步驟編號＋禁止事項：禁止當對齊/資訊檢查處理、禁止自稱手動觸發）；CronUpdate 後同步 schedule-registry.md 條 3
- [x] #2 下次 fire 實證：Skill tool 實際調用、月檔 append、報告週節標記排程觸發非手動
- [x] #3 查證 ZCode automation 投遞目標可否配置 per-run fresh session（docs 鏡像證據薄；不可配置則 prompt 祈使框架為唯一修復槓桿），結論記卡 notes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
調查結論（09-13，證據＝ZCode db.sqlite session/message/part 表）：①09-05 23:10:15 首跑投遞進建 cron 的原 session sess_9fe48e77（T3-1 糾正挖掘 spike），model reasoning 逐字「The user pasted an updated cron prompt…」→ 只做 prompt/skill 對齊檢查回「三面全部對齊，無需動作」，零執行——fallback 條款（skill 清單不可見）從未觸發，失敗發生在執行前的語義誤讀。②09-12 23:10:20 二跑 sourceCommandId=automation-370fafc5:1789225800000 實證為排程投遞非手貼；誤判「手動觸發」但正確執行 skill，產 weekly-20260912.json＋corrections-2026-09.md（23:15:48）——報告標頭「手動觸發」係 run 自身誤標，調查 session 已更正標頭存查。③拓撲通案：cron 投遞 append 進綁定 session——nightly 收斂 cron 10 run 全落 sess_07836405（含 154 則互動對話仍正確執行）→ 判別因子＝prompt 祈使框架，非 session 乾淨度。④工作目錄提示：查證入口 sqlite3 -readonly ~/.zcode/cli/db/db.sqlite（頂層 ~/.zcode/cli/db.sqlite 是 0-byte 殘檔）。

09-17 AC#1 完成——cron prompt 祈使化重寫已 CronUpdate 落地（automation-c52d4574，automationId/cron/下次 fire 2026-09-19 23:10 不變）；schedule-registry.md 條 3＋更新時點已同步（branch air-82）。prompt 四要素齊：🔴排程頭＋「autonomous 執行 session」角色指派＋步驟編號＋禁止事項（禁當對齊檢查處理、禁自稱手動觸發、report-only）——對照 nightly 收斂 cron 十跑實證形態。AC#2 待 09-19 fire 實證；AC#3（per-run fresh session 可配置性查證）未做。

【0919 查證（AIR-136-139 盤點時的 stale 嫌疑排查看證）】非 stale——本卡在等 AC#2 實證：CronList 機械確認 automation-c52d4574 enabled/active/runCount=0、nextRunAt=2026-09-19 23:10（今晚首發；祈使化 prompt 已在場）。registry 同步已落 main（daf36172，branch air-82 已合併刪除——卡 notes 舊稱「branch air-82」僅歷史）。下一步：明晨讀 corrections-2026-09 報告驗 AC#2（實際執行＋標記「排程觸發」）→ AC#3（per-run fresh session 可配置性查證）→ 結算。

【0919 AC#3 查證結論——per-run fresh session 不可配置】官方文檔明載投遞綁定會話為設計行為：ref-docs/harness/zcode/cn/docs/automations.md:52「用這種方式創建的任務會綁定到當前會話：後續每次觸發都把結果投遞回同一個會話，而不是每次新開一個」；任務配置四欄＝項目／權限／模型／推理強度（同檔 :74-78）、表單創建欄位（:43-48）皆無 session 目標欄；工具面 CronCreate／CronUpdate 參數面亦無 session／fresh 參數（本 session 工具 schema 機械確認）。結論：投遞目標 session 不可配置 per-run fresh，prompt 祈使框架為唯一修復槓桿——AC#1 修復方向正確，與調查結論③（nightly cron 十跑實證：判別因子＝prompt 祈使框架非 session 乾淨度）互證。AC#2 待今晚 23:10 fire 後明晨讀報告驗證。

【0920 AC#2 驗證 PASS——祈使化 prompt 修復實證生效】機械證據：CronList runCount 0→1、lastRunAt＝2026-09-19 23:10:14（排程 23:10:00＋14s）、nextRunAt 滾至 09-26 23:10。三判準全過：①Skill 實際執行——完整週報產出（糾正＋CR＋Memory 三節），evidence 檔 ai-analysis/memory-telemetry/weekly-20260919.json（421KB，mtime 23:11）；②月檔 append——corrections-2026-09.md 新增「## 09-13 ~ 09-19 週報（2026-09-19 23:10 排程觸發 run 產出）」（mtime 23:20）；③標頭逐字「排程觸發」、無手動誤標（對照 09-12 run 誤標手動的失敗態已消除）。三跑對照：09-06 靜默空轉→09-12 執行但誤標→09-19 完整正確——語義誤讀失敗態修復閉環。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
三 AC 全綠結案——祈使化 prompt 修復閉環（09-06 靜默空轉→09-12 執行但誤標手動→09-19 23:10:14 排程觸發完整正確）；AC#3 查證 per-run fresh session 不可配置、prompt 祈使框架為唯一修復槓桿。
<!-- SECTION:FINAL_SUMMARY:END -->
