---
id: AIR-82
title: corrections-weekly cron 首跑靜默空轉——投遞被 session 歷史誤讀為對齊檢查（09-06 零產出、09-12 產出誤標手動）
status: In Progress
assignee: []
created_date: '2026-09-12 21:35'
updated_date: '2026-09-17 03:22'
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
- [ ] #1 Cron prompt 重寫為祈使執行框架——對照 nightly 收斂 cron 實證（🔴 排程頭＋「你是 autonomous…session」角色指派＋步驟編號＋禁止事項：禁止當對齊/資訊檢查處理、禁止自稱手動觸發）；CronUpdate 後同步 schedule-registry.md 條 3
- [ ] #2 下次 fire 實證：Skill tool 實際調用、月檔 append、報告週節標記排程觸發非手動
- [ ] #3 查證 ZCode automation 投遞目標可否配置 per-run fresh session（docs 鏡像證據薄；不可配置則 prompt 祈使框架為唯一修復槓桿），結論記卡 notes
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
調查結論（09-13，證據＝ZCode db.sqlite session/message/part 表）：①09-05 23:10:15 首跑投遞進建 cron 的原 session sess_9fe48e77（T3-1 糾正挖掘 spike），model reasoning 逐字「The user pasted an updated cron prompt…」→ 只做 prompt/skill 對齊檢查回「三面全部對齊，無需動作」，零執行——fallback 條款（skill 清單不可見）從未觸發，失敗發生在執行前的語義誤讀。②09-12 23:10:20 二跑 sourceCommandId=automation-370fafc5:1789225800000 實證為排程投遞非手貼；誤判「手動觸發」但正確執行 skill，產 weekly-20260912.json＋corrections-2026-09.md（23:15:48）——報告標頭「手動觸發」係 run 自身誤標，調查 session 已更正標頭存查。③拓撲通案：cron 投遞 append 進綁定 session——nightly 收斂 cron 10 run 全落 sess_07836405（含 154 則互動對話仍正確執行）→ 判別因子＝prompt 祈使框架，非 session 乾淨度。④工作目錄提示：查證入口 sqlite3 -readonly ~/.zcode/cli/db/db.sqlite（頂層 ~/.zcode/cli/db.sqlite 是 0-byte 殘檔）。
<!-- SECTION:NOTES:END -->
