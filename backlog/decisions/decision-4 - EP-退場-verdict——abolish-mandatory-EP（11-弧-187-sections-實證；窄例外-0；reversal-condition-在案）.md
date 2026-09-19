---
id: decision-4
title: >-
  EP 退場 verdict——abolish mandatory EP（11 弧 187 sections 實證；窄例外 0；reversal
  condition 在案）
date: '2026-09-19 04:06'
status: proposed
---
## Context

user 方向裁決在先（0919 走查 Step 2：「EP 本來我就要消除」——AIR-135.2 卡 notes）。本 decision 是 dogfood 的證據性 verdict：11 個 archived full-tier 弧（P2 種子 7＋0919 補抽 4）、187 個 section 的消費度抽樣——consumed 74%（嚴格 55%）、五儀式塊 0/47 被消費、unconsumed 46 個全數歸類為無資訊記錄／pointer 冗餘／boilerplate／Plan 級排序理由，**零個「card schema 無法表達」的 primitive 候選**。證據 artifact：`.agent-tmp/air-135/dogfood/ac1-sample-extension.md`；verdict 呈現＝Code Lens POC（`codelens-poc-ep-verdict.html`，機械生成 deterministic）。

## Decision

1. **abolish mandatory EP**：full-tier 不再預設建立 standalone EP；規劃載體＝card Planning Contract 六欄（standard）／parent 引用（bounded child）。
2. **窄例外門**：僅當出現 card schema（Description/AC/Plan/Notes/Final Summary＋decision entity）無法表達、且不可由 decision/doc attachment 承載的具體 planning primitive，才為該 primitive 重開例外審查（11 弧抽樣：0 候選）。
3. **reversal condition**：上述窄例外門被觸發即逆轉審查；EP 形態僅為該 primitive 復活，不回復預設。
4. **退役時序**：EP consumer（16 檔 STRUCTURAL）未遷完前不宣告全域退役（AIR-135.2 AC#4 invariant）；遷移按五類模式分批（resolver 單一源→gate→段錨→結算基準→傳參/ref）。

## Consequences

- 新弧省去 EP 儀式（Scenario Matrix／pseudo-code／report shell 類 0/47 消費的塊直接不再產）；規劃品質不減（六欄契約＋AC 驗證式替代）。
- 遷移成本尖峰＝EP Review Findings 的 finding→裁定→偏差鏈，落 decision entity 時 rejected alternatives＋supersedes 為必填（AIR-29／AIR-48 實證的消費密度尖峰）。
- status：**proposed**——user 對 Code Lens POC 視圖完成 Align pass（AC#5×135.4 AC#4 聯合 dogfood 的 human 檢查點）後翻 accepted；翻正時記 Align 結果（一致／intent diff 清單）。

## Rejected Alternatives

- **保留 mandatory EP 但瘦身**（DRAFT-12 原方向「減少雙載體冗餘」）：被否——187 sections 中 25% unconsumed 全是儀式塊，瘦身後仍是第二 plan truth，雙載體同步成本不消失；且 AIR-29 實證 EP 自身進化掉儀式塊後與卡趨同，載體合一是終態。
- **全面立即退役（consumer 不遷）**：被否——16 檔 STRUCTURAL consumer（ep-review/implement/post-build/segment_receipt 等）讀 EP 的 code path 在場，立即退役打斷在途弧的可恢復性；故保留「未遷完不退役」時序條款。
- **窄例外預先保留（如 Scenario Matrix）**：被否——SM 內容可由卡 AC 驗證式完全承接（嚴格 id 錨 6/11＋2 partial 皆為習慣問題）；預留例外等於預留儀式回流通道。
