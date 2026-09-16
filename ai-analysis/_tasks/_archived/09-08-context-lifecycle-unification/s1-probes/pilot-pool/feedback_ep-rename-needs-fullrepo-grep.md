---
name: feedback_ep-rename-needs-fullrepo-grep
description: EP 治理對：動前全 repo 盤點（A/B 引用分類）＋_done 不等於落地（ghost-done 查檔）
metadata:
  node_type: memory
  type: feedback
  originSessionId: ac15faf3-d5f8-4bc6-bf1f-45e28f8bdf1f
---

遷移/改名先全 repo 盤點再動手；「EP 在 _done/」不是「已實作」——落地一律查檔。

> merged_from: feedback_ep-done-not-impl, feedback_check-trigger-before-adding-tests.md (2026-08-31, earlier wave), 2026-09-07 cluster-merge wave

## 動前全 repo 盤點（original: feedback，keeper 本體）

遷移/退役/改名 EP 的 S0 **必 `rg <name>` 全 repo**——引用散在別家散文（「供 X 消費」「X 整合段」），只掃直覺索引檔必漏（standup 遷移漏 AGENTS.md 等三處，review 抓 3 drift）。**部分下沉加 A/B 分類**：A＝指向搬走部分（改指新落點）；B＝指向留下部分（**必須不動**——盲改全量會改斷正確引用；殘留對帳兩套標準）。**同族：加測試前先查觸發路徑**（merged 08-31）：測試價值∝被執行頻率——先 `rg` 找 caller（0 caller＝沒人跑的化妝 guard）＋找既有 observation loop（nightly real-data scan 嚴格優於合成 unit test）；no-CI 下先有觸發再加測試，複雜到需測試的 skill 腳本本身即 smell。呼應 lsp-navigation 符號查證（此處 docs 場景用 rg 預防性盤點）。相關 [[feedback_counter-skip-confirmation-bias]]。

## _done 不等於落地（original: feedback，ghost-done 教訓）

兩支 `_done/` EP 宣稱的 segment（假設路徑驗證、產出驗證、scope fence、classifier 重試）**全部沒落地**——rg 實際檔案查無，EP 卻標 done。評估「X 是否已做」→ **rg/read 實際 commands/skills/rules 檔案**，不信 EP 狀態（status≠impl，低層證據冒充高層驗收）；`_done/` EP 只當設計參考。與 [[feedback_verify-wt-before-commit]] 同源：查實際狀態，不信宣稱（彼查 git WT 防 concurrent，本查檔案防 ghost）。
