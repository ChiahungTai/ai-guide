---
name: fix-immediately-not-defer
description: 合理的修正就立即落地，不要「之後再修」（之後 = 忘記修 = 拖延症）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0f50f804-f216-4b45-bbdf-a93cbb3074a2
---

合理就立即修，不要「之後再修」。之後再修 = 忘記修 = 拖延症。

**Why**: 用戶 2026-06-20 明確指出 — 拖延把合理修正變永久遺漏。「之後再修」是自欺，實際永不修。整脊收尾後 code-review 發現 ep_type 欄位未標準化（F1），用戶要求當下修而非累積待辦。

**How to apply**:
- judge-review ✅ 採納的建議，當下落地（不累積待辦）— 反拖延原則已寫入 `skills/judge-review/SKILL.md:29,31` 核心原則段
- ⚠️ 需確認門檻拉高：僅限「規模過大需開 EP」或「真需用戶價值判斷」，不當拖延藉口
- 規模小 + 合理（問題真實 + 解決合理 + 收益 > 成本）→ 直接修 + commit，不問
- 通用原則：不限 judge-review，任何「合理修正」（code-review finding、audit、自發現）都立即落地
- **反藉口：root-cause 純度 ≠ 延後便宜改動的理由**（2026-06-22 code-review session）：我曾以「單獨加 /illustrate 受眾標籤是儀式，要搭配根因閘門才有意義」為由延後一個零成本正確改動，用戶糾正「成本很低為何不做」。正確 framing：**便宜的正確改動現在做；根因閘門是疊加防復發的層，不是前置條件**。「症狀修 vs 根因修」是假對立 —— 症狀修有獨立價值（修當前破壞 + 錨定檔案），根因修防復發，兩者疊加。別用「不夠純粹」包裝拖延
- **「列入報告不修」也是拖延形態**（2026-08-31，user 原話「順手修，不拖延」）：收尾 sync-sources 掃出 allow-list 缺條目，我歸類「既有遺留→列入報告不順手修」，user 糾正當場修。辨析：並行 session 原則的「不順手修」擋的是**改別 session 正在動的檔案**；自己弧內驗收掃出的機械 finding（可驗證、修法明確、低風險）一律當場修。「報告不修」只適用真需 user 裁量或跨弧歸屬的項

相關：[[settlement-scripts-are-code]]（AI 評估查證不盲從，但查證後合理就修不拖）
