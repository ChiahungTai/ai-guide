---
name: full-domain-structure-uniformity
description: user 裁定結構慣例要 full domain——自家 repo 群全部採用（ai-rules 自家也 dogfood），探測
  fallback 只為外部消費 repo 保留
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_89592a9f-fbba-4b02-ade1-3b58b15bfd54
---

user 2026-09-02 裁定「我是要 full domain」：新結構慣例（三池 `ai-analysis/{_inbox,_projects,_tasks}`）不是 mosaic 專屬——**user 的 repo 群逐一採結構，實踐上全域一致**；ai-rules 自家也不例外（dogfood），不接受「skill 教的規則自家不守」。

**Why**：user 看到 ai-rules 自家 EP 落 `00-tasks/`（探測 fallback 正確行為）仍視為不一致——對 user 而言，規則的價值在於他管理的每個 repo 長得一樣；fallback 是給外部消費 repo（如無 ai-analysis 樹的 repo）的相容面，不是自家可用的例外。

**How to apply**：設計跨 repo 慣例時，落地計畫必含「自家 repo 群逐一採結構」的任務（mosaic ✓、ai-rules ✓＝`ai-analysis/_tasks/_archived/09-02-ai-rules-three-pool/ep.md`〔已歸檔〕、未來 code-reality/codetour 複製模式）；不改 skill 硬編路徑（探測條款保留）；發現自家與所教慣例不一致（如 skills 宣告退役的 execution-plans/specs 實體還在自家）＝清債任務，非可容忍的例外。相關：[[ai-analysis-restructure-design]]。
