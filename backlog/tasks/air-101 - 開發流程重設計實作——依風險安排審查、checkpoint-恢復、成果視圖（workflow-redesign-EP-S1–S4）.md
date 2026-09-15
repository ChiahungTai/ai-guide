---
id: AIR-101
title: 開發流程重設計實作——依風險安排審查、checkpoint 恢復、成果視圖（workflow redesign EP S1–S4）
status: In Progress
assignee: []
created_date: '2026-09-15 15:49'
updated_date: '2026-09-15 21:25'
labels:
  - governance
  - skills
dependencies: []
references:
  - ai-analysis/_tasks/09-15-development-workflow-redesign/ep.md
  - ai-analysis/_tasks/09-15-development-workflow-redesign/index.html
ordinal: 86000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
把已三輪外部審查 verified 的開發流程重設計 EP 落地：review 改依風險配置、中斷後 checkpoint 恢復、成果視圖與結算。現在到哪：EP 計畫定稿、等實作。本卡是 EP owner 卡，S1–S4 依 manifest 逐段實作與驗收。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 4fc5caa（main、clean、單 WT）；EP 實作基線 b4a3019 已核對在場〕
〔已決策勿重辯：①EP（ai-analysis/_tasks/09-15-development-workflow-redesign/ep.md）四段計畫已 muse 三輪外部審查＋主 session N1–N8 外審全收斂 verified——實作照 manifest 與各段修改要點執行，不重辯計畫；實作前依 EP 條款 rg 重定位錨點（行號只作起點）②S1/S2 是同一政策切換、未全接完不 deploy；主線中間不插他卡改同檔——AIR-76 六檔落檔先於 EP S1 完成（同檔避撞）③AIR-60 部分承接（09-15 對帳已記兩卡 notes）：EP S3 承接其 rehydration 單一源骨幹、EP S2 承接段落結果寫 EP 進度方向；AIR-60 保留授權失效條款／雙 lens closure／segment receipt 自算，AIR-101 結算時回寫其 Plan/AC ④HTML 互動／視覺驗證本輪延後（user 明示於 EP），不阻擋交付 ⑤docs mode——若發現必須改 .py/.toml/.sh 才成立，先回報擴範圍不得偷渡 ⑥AIR-91/96 定稿的 catalog/generator 不動〕
範圍：EP manifest S1–S4 產品寫入集合（S1 review-engine＋workflow-review-pattern；S2 主鏈十二檔；S3 task-recovery.md 新檔＋恢復入口五檔；S4 殼/metadata-sync/deep-work/索引導航）＋AIR-76 前置落檔；驗證依 EP 各段驗證與完成條件（static＋behavior＋oracle）。
〔執行形態：marshal 調度（L1），worker 分段派工；review 鏈＝codex+muse 外審→5.3 judge→user commit consent；三線（air-101/air-98/air-63）檔案正交已驗證，序列化 ff 合併回 main〕
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔09-15 marshal 調度 checkpoint〕三線已開跑：AIR-67 已結案（9e4d427）；本卡建卡＋起手式完成（56f24de/b431660）；lane98[air-98]＋lane63[air-63] 兩 WT 開設同基線。三 worker 背景在飛：①lane98=AIR-98 P1 probe pipeline（impl-lite；probe 來源已凍結＝bridge usage glm/codex 兩腿＋webgpt 三訊號健康組合＋muse 顯性 unsupported；bridge usage 輸出形態已 live 勘查）②lane63=AIR-63 S1–S5 pending 覆層（impl-lite；draft-5 設計內嵌工單；三拍板採建議值：手動＋夜波／池 gitignore／300字＋4K；S2 池 generator pointer＝worker 產 patch、marshal 合併後套用——池 gitignored 單一寫入者拓撲）③root[air-101]=AIR-76 drift 盤點＋S1 餘量＋S0 實驗備料（general-purpose；S2–S7 凍結待 S0 過線；v3.1 S1 宣稱已由 AIR-96 大半落地、cr-research 已 pin glm-5.3 full 已機械確認）。AIR-60 對帳已記兩卡 notes（EP S3 承接 rehydration 單一源骨幹；授權失效條款/雙 lens/segment receipt 留 AIR-60 自算）。下一步：收三 verdict→review 鏈（codex+muse 外審→5.3 judge）→S0 實驗 marshal 編排→S2–S7→EP S1–S4→序列化合併。

〔09-16 marshal checkpoint 2〕EP S1 PASS（review-engine profile 驅動重寫＋workflow-review-pattern identity 三欄＋去重復用判準＋no-candidate ledger 點 8；承接清單 S2 十項/S4 四檔/pointer-only 六檔落 .agent-tmp/air-101/s1-consumer-manifest.md；偏差：3-perspective/dual-context 字面 token 保留——check_single_source.py 機械契約＋boundary 別名錨，語義已重錨）。S2 已拆 S2a（execution-plan/ep-review/implement/code-review/audit-test）＋S2b（post-build/agent-workflow/agent-review-cycle/work-order/judge-review/followup-review/agents AGENTS）兩 worker 並行在飛。後續：S3（task-recovery 等）＋S4（殼/metadata-sync/deep-work/索引）→ review 鏈。

〔09-16 deploy 完成（user 授權「可以Deploy了」）〕deploy_agents 三端 OK（~/.zcode、~/.codex、~/.config/muse 各 AGENTS.md；dry-run 30,335B 全 gate 綠；舊 bundle 備份 *.bak-20260916-052452）；逐端 rg 驗 task-recovery 單一源行在場（:191）。注意：本 session 載入的是舊規則——新預設（review profile 化等）自下一個 fresh session 生效；fresh context 驗收＋SM 行為抽樣＋真實 pilot 仍待跑（驗收腿）。
<!-- SECTION:NOTES:END -->
