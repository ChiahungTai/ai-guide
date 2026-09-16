---
name: review-even-on-quick-fix
description: review 三則：quick-fix 也跑收尾鏈＋結構化產物驗證五條＋per-project 引用查證範圍
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_9184c58a-9f15-4d17-9564-6cb9060e653d
---

審查鏈不因改動小而跳——「測試綠」只證自洽；gate 跳過要明說；驗證設計跟「產物會怎麼壞」走。

> merged_from: feedback_review-blindspots-structured-artifacts, feedback_review-per-project-reference-scope, 2026-09-07 cluster-merge wave

## quick-fix 也跑收尾鏈（original: feedback，keeper 本體）

2026-09-03 三項小改善直改＋cargo 全綠就提 commit，user 追問「你剛有用 Muse 審查嗎」——流程缺口，補送審查。**Why**：AI 同寫 impl＋test 時測試綠只證自洽（證據獨立性塌縮），審查是另一隻眼。同日升級——user「修好跑 post-build/commit」：期望的是**完整收尾鏈按規模縮配**（<3 files 單 fresh-eyes 即可），不是跳過。**How**：任何 code 變更提 commit 前——正式審查，或提案**明示**「未審查＋為什麼可接受」（與 [[consistency-gate-not-optional]] 同構；跳過要明說）。在場期優先用 Muse（委派形態見 [[agents-registry-split-design]]）。卡結案（`-s Done`）同樣排在重審通過後（2026-09-07 AIR-41 實證：實作完直接 commit＋結案、跨家族 review 4 Important 事後到→fix commit＋卡重開）；委派實作（muse/codex）「已實跑測試全綠」不是審查（writer≠reviewer），等 review 回來。

## 結構化產物驗證五條（original: feedback，AIR-23 補審 1C＋10I 全是主 session 漏的）

1. **讀過≠驗證過**：HTML/XML 產物必含 parser/syntax gate（註解腐敗會被 error-recovery 偽裝正常）。
2. **契約逐條機械對照**：frozen decision 逐條 rg 對 code 屬性，非印象核對。
3. **搬移後驗整個目錄**：mv 後跑全目錄連結檢查（相對深度會變）。
4. **至少一條對抗性輸入**：malformed/空狀態/越界固定一條。
5. **verifier 腳本進 git 隨弧走**：放 .agent-tmp 隨收尾蒸發＝證據滅失；EP 列為 evidence artifact。同族 [[feedback_settlement-scripts-are-code]]。根因：驗證跟「我打算驗什麼」走，沒跟「這類產物會怎麼壞」走；冷 context 補審反而對字面較真。docs-mode 含互動 JS 不得豁免行為驗證。

## per-project 引用查證範圍（original: feedback）

審 skill/command 對 per-project 檔（dependency-graph.md、SYSTEM-MAP.md、各模組 CLAUDE.md 等）的引用時，查證範圍**必須含該檔在目標專案的實際內容**——不能只 rg ai-rules 家 repo。實證：`dependency-graph.md`「Data Infrastructure Cluster」在 ai-rules 0 hits、在 mosaic 6 次，誤判「查無此詞」。結論碰巧對（project-specific 名詞不進 general skill）但理由錯。与 [[feedback_slash-command-existence-verification]] 同屬查證範圍 blindspot 家族。
