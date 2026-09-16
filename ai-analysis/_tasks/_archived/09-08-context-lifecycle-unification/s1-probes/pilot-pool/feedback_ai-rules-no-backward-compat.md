---
name: ai-rules-no-backward-compat
description: ai-rules 重構不考慮向後相容（條文在 edit-discipline rule）；本條僅留 F7 增量——不預寫未發生情境的條件式文案
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0f50f804-f216-4b45-bbdf-a93cbb3074a2
---

規則主體在 `rules/edit-discipline.md`（架構優先＋向後相容確認機制——例外僅外部系統整合/生產數據/部署，ai-rules 三者皆不成立）——審 ai-rules 重構提案直接讀 rule，此處不重述。EP 別寫「向後相容」「保留舊 X 作相容」（2026-06-20 糾正實證：AI 保守傾向套用不適用的工程慣例）。

**F7 條款增量**（repo 零承載，2026-08-18 user 裁決）：不預寫未發生情境的條件式文案（對偶形態的相容保留）——規則論證在現行條件下有效就不動；條件改變時一次重推導重寫，不留「若 X 計費則…」投機文字。實證：報告建議現在改計費條件式被否（違「專注當前有效規則」）；未來重推導釘 kanban 卡承接。

相關：[[fix-immediately-not-defer]]（反拖延）。
