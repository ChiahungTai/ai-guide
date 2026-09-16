---
name: work-order-contract-point-to-source
description: 委派工單（muse/subagent）內嵌契約值會漂——卡 ref 形態等指向 skill 合約單一源路徑，不 inline
  複製值（AIR-18 raw URL 實證）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_7622de15-8cf2-4fc5-a0b2-49b7f5f19f0b
---

AIR-18 結案時 muse 把卡 ref 寫成 raw md URL——根因不是 muse 錯，是主 session 的委派工單內嵌了當時形態的 URL（muse 忠實照抄）；同晚中央 viewer 掛載讓該值過時。

**Why**：工單是快照，契約值（URL 形態／命令語義／流程步驟）內嵌進去就與單一源脫鉤——源更新後工單仍帶舊值；被委派方（muse/subagent）不載自家 skill、無從發現漂移。

**How to apply**：工單涉及既有契約（卡 ref 形態、結案兩步、雙 ref 合約、流程段落）時寫「見 skills/kanban-board/SKILL.md 雙 ref 合約」並標「以合約為準」，不在工單裡複製完整值；AIR-13 D3 固化 muse 工單模板時把這條寫入。機械兜底＝週日治理 cron 卡 ref lint。關聯 [[feedback_relay-claims-verify-current-state]]、[[report-server-md-viewer-central-mount]]。
