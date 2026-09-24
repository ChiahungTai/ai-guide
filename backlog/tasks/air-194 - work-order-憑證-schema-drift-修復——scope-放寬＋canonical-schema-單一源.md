---
id: AIR-194
title: work-order-憑證-schema-drift-修復——scope-放寬＋canonical-schema-單一源
status: Done
assignee: []
created_date: '2026-09-24 22:27'
updated_date: '2026-09-24 23:04'
labels: []
dependencies: []
ordinal: 180000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
跨 repo 的派工憑證出現規格斷裂：發行工具開出的憑證（範圍欄是清單形）會被本 repo 的入場檢查拒收——入場檢查要求六欄全是文字，工具卻開出清單。後果：正式管道發的憑證過不了閘，只能手寫（而手寫格式沒文檔）。檢查工具自己也驗不出這件事（兩端深度不同）。

```mermaid
flowchart LR
  T[發行工具<br/>範圍欄＝清單形] -->|正式發行| X[入場檢查拒收<br/>六欄全文字驗證]
  P[修法：範圍欄收文字或清單兩形] --> H[入場檢查放寬]
  H --> OK[發行鏈恢復]
  H --> DOC[憑證規格單一源文檔<br/>防第三個消費者再分叉]
```

**修法（兩位審查者合議定案）**：①入場檢查的範圍欄放寬＝非空文字或非空清單（清單為正典——發行端語義說了算；文字向下相容；檢查只驗在場性不讀內容，放寬符合自家契約）②拒絕訊息去掉寫死的路徑＋附最小手寫憑證範例（補可發現性，不新增發行通道）③同卡立憑證規格單一源文檔（現在三處各說各話，防第三個消費者再分叉——兩位審查者一致）④發行工具端對稱修歸 SC 端裁決；重設計弧消費本 finding 為輸入、獨立小修先止血。

**修復落點**：hooks/＝控制面路徑——本卡 branch 修復＋pre-commit guard 照跑。

## Acceptance Criteria
- [x] #1 範圍欄放寬：工具產憑證（清單形）過閘＋手寫文字憑證仍過（回兼容）
- [x] #2 fail-loud 不回歸：空文字／空清單／混型清單／缺欄皆拒（兩形迴歸測試）
- [x] #3 拒絕訊息：無過時路徑（通用措辭或 marker 推導）＋附最小手寫憑證範例
- [x] #4 憑證規格單一源文檔落本 repo hook 側（工具端引用指針）——對稱修歸 SC 裁決
- [x] #5 全量 hook 測試綠（control-plane guard 不受影響）

證據指針：合議兩腿＝bridge job（0925）；finding 原信＝SC marshal 投 ai-guide-marshal 位址；修復 commit 1e3ac8c3；receipt＝air-194 WT .agent-tmp/air-194-receipt.md。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【0925 修復落地】job-mug4ltoc（flash）——SEAL ALL GREEN（81 hook tests＋29 新）。merge main 1e3ac8c3：scope 放寬（str｜list[str]，array 正典）／deny 文案＋手寫範例／hooks/work-order-schema.md 單一源文檔。AC#1-#5 勾選證據＝rebuild_seal 輸出＋receipt（.agent-tmp/air-194-receipt.md）。工具端對稱修歸 SC 裁決（finding 信已回執）。AC 勾選：全數達成——AC#1 工具形過閘（測試釘）#2 fail-loud 回歸面 #3 文案 #4 schema 文檔 #5 hook 測試綠。

## Final Summary

```mermaid
flowchart TD
  F[SC finding 信<br/>工具憑證被 hook 拒收] --> D[合議：muse＋codex<br/>scope 兩形＋單一源＋範例]
  D --> I[修復 job-mug4ltoc<br/>flash write-mode]
  I --> S[SEAL ALL GREEN<br/>81＋29 tests]
  S --> M[merge main 1e3ac8c3]
  M --> DONE[Done——對稱修歸 SC]
```

**as-built**：load_work_order scope 收 str｜list[str]（array 正典）；deny 文案通用化＋手寫範例；hooks/work-order-schema.md 單一源。SEAL ALL GREEN（110 tests）。<!-- SECTION:FINAL_SUMMARY:END -->
<!-- SECTION:NOTES:END -->
