---
id: AIR-84
title: instruction-writing skill 跨 harness 撰寫層——修 dir 層可達性宣稱＋併入官方文檔研究增量條目
status: To Do
assignee: []
created_date: '2026-09-12 22:24'
updated_date: '2026-09-16 07:58'
labels: []
dependencies: []
ordinal: 70000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
跨 harness 撰寫層修正（0916 muse 調查後重對口徑）：SKILL.md 的「每層雙檔確保四家 harness 都讀得到」宣稱被研究證偽——ZCode 官方明文不掃子目錄（斷）、Codex 僅 cwd 路徑、Muse 僅向上、CC 為 lazy。本卡重寫該宣稱為四家可達性差異表、按 09-12 研究素材（十檔齊備）落增量節、補兩個 webgpt 簽名進現行六類失敗態表。素材：ai-analysis/reports/2026-09-12-cross-harness-md-writing-research/（1158dc9 定錨）；調查卷宗：本卡 notes＋.agent-tmp/air-84-muse.out。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 5e191cd〕
〔已決策勿重辯：①卡面四處脫鉤已對齊（0916 muse 調查＋user 拍板先改卡）：行號 24→38、四家口徑＝Claude/ZCode/Codex/Muse（OpenCode 已退役除名）、失敗態基線＝現行六類（0916 兩新形態已在）、M3 過期觀察窗（OQ2/OQ4/OQ6）撤銷按現行研究狀態寫 ②研究素材十檔齊備＝reports/2026-09-12-cross-harness-md-writing-research/（1158dc9 定錨），增量節逐條掛官方錨點 ③glm 429 與 codex/muse 同晚雙降級實證源不明——施工時定位，定位不到則該點降級為推估並標注〕
範圍：①重寫 skills/instruction-writing/SKILL.md:38 全稱句為四家可達性差異表（CC lazy／Codex cwd-only／Muse 向上-only／ZCode 斷）②按素材 3c/3d/3e 落增量節（尺寸預算三形態／層級語義三分／per-harness 撰寫要點與陷阱／官方缺口）逐條掛錨 ③補 Selected model at capacity＋turn token invalid/expired/revoked 兩簽名進 model-routing 現行六類表 ④skills/CLAUDE.md 索引同步（有變動時）。風險面：寫入契約首改（跨 harness 撰寫層語義）——分類開工正式定（預期 boundary）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔0916 muse 調查卷宗〕建卡後零施工。①錯誤宣稱還在線上：SKILL.md:38「每層雙檔確保四家 harness 都讀得到」被 ZCode 官方文檔明文證偽（不掃子目錄——斷），對 Muse（向上-only）／Codex（cwd-only）／CC（lazy）也過強 ②研究素材十檔齊備未動用（reports/2026-09-12-cross-harness-md-writing-research/，1158dc9 定錨）③AC③ 兩 webgpt 簽名未補、glm 429 實證源不明 ④四處脫鉤：行號 24→38、口徑 OpenCode→Muse、失敗態五類→六類、M3 觀察窗已過期。處置建議＝先改卡面（對齊現況）→ 施工。卷宗＝本對話 air-84-muse.out。
<!-- SECTION:NOTES:END -->
