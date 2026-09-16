---
id: AIR-84
title: instruction-writing skill 跨 harness 撰寫層——修 dir 層可達性宣稱＋併入官方文檔研究增量條目
status: To Do
assignee: []
created_date: '2026-09-12 22:24'
updated_date: '2026-09-16 07:31'
labels: []
dependencies: []
ordinal: 70000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕
跨四家 harness 官方文檔的 md 撰寫研究已完成（提取＋覆核＋合成＋審查全綠）。這卡把結晶落進 instruction-writing skill：修正一個與官方文檔衝突的舊宣稱（模組層 instruction 不是四家都讀得到），並把研究發現的增量知識（層級差異、尺寸預算、截斷陷阱）併入撰寫規範。

〔baseline：ai-rules 2d09c09；研究本體已 harvest ai-analysis/reports/2026-09-12-cross-harness-md-writing-research/（十檔：四提取＋四覆核＋synthesis-draft＋review-final）〕
〔已決策勿重辯（user 09-13 拍板「照你說的做」）：①OQ1 裁選項 a——修 SKILL.md:24「每層雙檔確保四家都讀得到」宣稱：口徑＝IW 原文四家含 OpenCode 不含 Muse；修文＝模組層定位改「CC（lazy）＋Codex（cwd 路徑）深層；ZCode 官方明文不掃子目錄不可達、OpenCode 未驗證；不可達家靠 root 導航種子」②OQ3 採納——description 觸發詞前綴紀律（最嚴約束 ZCode 清單摘要 250 字元內承載「何時用」）③OQ7 採納——委派 session 讀不到主對話 memory→工單必須自含（與 self-contained-prompt 同向，補機制級理由）④OQ2/OQ4/OQ6 維持掛起（M3 觀察窗 09-13/09-14 夜波；subagent 觸發＝首個寫池角色；OpenCode 不補）〕
〔驗收：①SKILL.md:24 宣稱改寫後 rg 驗證無「四家 harness 都讀得到」絕對宣稱，新文案含各家 dir 層可達性差異＋OpenCode 未驗證標註②增量節落位（層級語義三分表／尺寸預算三形態表／截斷陷阱／250 前綴／委派自含）且每條帶官方錨點或〔ai-rules 經驗〕標記（素材＝synthesis-draft 3c/3d/3e，不重複 3a 既有序）③model-routing skill webgpt 失敗態表補兩新簽名（Selected model is at capacity——處置＝並發釋放後序列重試；turn token invalid/expired/revoked——處置＝棄審換 family）＋註明 glm 429 與 codex/muse 同晚雙降級的 glm bridge 降級路徑實證④memory-audit 觸發詞/CLAUDE.md 索引如有 skill 變動同步〕

範圍：skills/instruction-writing/SKILL.md（修宣稱＋新節）、skills/model-routing/SKILL.md（webgpt 表）、skills/CLAUDE.md（如索引需同步）。來源素材：ai-analysis/reports/2026-09-12-cross-harness-md-writing-research/synthesis-draft.md（含七開放問題裁決紀錄）；DRAFT-6（webgpt 失敗簽名實證關聯）。弧閉環：本卡建立即 cross-harness-md-writing-guideline-arc 指針退休條件成立。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔0916 muse 調查卷宗〕建卡後零施工。①錯誤宣稱還在線上：SKILL.md:38「每層雙檔確保四家 harness 都讀得到」被 ZCode 官方文檔明文證偽（不掃子目錄——斷），對 Muse（向上-only）／Codex（cwd-only）／CC（lazy）也過強 ②研究素材十檔齊備未動用（reports/2026-09-12-cross-harness-md-writing-research/，1158dc9 定錨）③AC③ 兩 webgpt 簽名未補、glm 429 實證源不明 ④四處脫鉤：行號 24→38、口徑 OpenCode→Muse、失敗態五類→六類、M3 觀察窗已過期。處置建議＝先改卡面（對齊現況）→ 施工。卷宗＝本對話 air-84-muse.out。
<!-- SECTION:NOTES:END -->
