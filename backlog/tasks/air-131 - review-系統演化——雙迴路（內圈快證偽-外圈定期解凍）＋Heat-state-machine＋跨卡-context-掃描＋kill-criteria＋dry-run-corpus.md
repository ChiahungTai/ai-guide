---
id: AIR-131
title: >-
  review 系統演化——雙迴路（內圈快證偽/外圈定期解凍）＋Heat state machine＋跨卡 context 掃描＋kill
  criteria＋dry-run corpus
status: In Progress
assignee: []
created_date: '2026-09-17 22:52'
updated_date: '2026-09-18 04:22'
labels: []
dependencies: []
references:
  - ai-analysis/_tasks/0918-air131-review-system-evolution/ep.md
ordinal: 112000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
local opt 不是回饋距離問題是目標函數從未重新開放——逐弧凍結決策的系統需要定期解凍機制。本卡把 local-opt bi 討論（muse+codex）＋user 命題修正（卡級審查時間軸盲目）落地成最小機制集四件：Heat 聚合（既有訊號零新基建）、kill criteria 入 EP、dry-run corpus、--arc mode＋cadence 自調；第五件禁令：不為這些再造 lifecycle。等 user 開工拍板。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：main（GUIDE-CR 合併波後回填當下值）〕

〔已決策勿重辯（local-opt bi：muse mu64bkv7＋codex mu64bkwm＋user 命題修正）：①統攝心智模型＝內圈快證偽、外圈定期解凍——local opt≠回饋距離（目標函數從未重新開放；三子題對應三種被拖遠的證據：feasibility/consumer behavior/alternative-architecture）②Heat state machine：五 signal family（R correction recurrence/G ritual growth/V vocabulary divergence/B boundary compounding/U consumer friction）→ Cool/Warm/Hot/Cooldown；Warm 動作＝該區**禁 additive repair、必產 delete/merge/rewrite 候選**（治理自放大防護）；三 tripwire 直升 Hot（大審抓到日常沒攔的 systemic Critical／權威互斥定義出現／≥2 獨立 dry-run 同因失敗）③感測器全既有資料源（corrections 七類週趨勢/parity 殘留計數/overhead 三問季度化/usage 零消費 delta/Critical 逃逸率/gate 二次出現/activation 健康）——零新基建④cadence＝hybrid：事件觸發＋**12 治理弧 ceiling 起始**（arc 數比日曆好）＋每季 state-review sanity；escape 定義收緊（review 前已存在+日常未升格；reviewer 新標準首抓不算）；**review-power guard**（零 Critical 連勝只在 scope/taxonomy/異構覆蓋可比時才配降頻）；慢降快升（×1.5/×0.5，floor 6 ceiling 24 弧）⑤kill criteria 入 execution-plan：EP 加 1-3 個 load-bearing assumptions（Assumption/Probe/Kill observation/Action 四欄可否證格式）；spike 用 **evidence budget**（非 wall-clock timebox）；**INVALIDATED＝成功終態**（uncertainty retired——止損記帳對抗沉沒成本）＋cost-to-disproof 追蹤（會死的方案死得越來越早=健康）⑥dry-run corpus：四型任務（cold navigation/normal/ambiguous-conflict/resume）；控制變數＝**prompt 禁提示 instruction topology**；workaround 比 failure 更有情報量；**同 workaround 兩獨立 contexts 再現＝design smell**；控制面弧必跑＋每季保底；friction log 三行輕量入口（append-only，自動升 type-2 候選——修 flow-feedback 零消費的高儀式病）⑦**跨卡 context 掃描**進審查準備步（user 命題：卡級審查時間軸盲目——今天三事故全此形態）：四掃（相關卡池/近期同域落地 git log --since/平行在飛 worktree+branch/drafts 向前）＋兩問（重複衝突於①②③嗎/④最可能的卡這設計讓它更易還是更難）；機械產出 related-work 塊進審查 brief⑧code-review --arc mode（codex 裁決）：method ownership=code-review（--arc＝baseline..tip+final-state invariants+multi-leg+judge+consumer probes）、orchestration=deep-work 劇本；**risk-driven lanes+convergence stop 取代固定六腿**（unique findings/leg+severity-weighted+overlap 三量；新腿連續只產已知 finding 即停）；不與 state-review 合併（歷史弧 vs 現在態）⑨**第五件禁令**：不為①-⑧造新 lifecycle/新平台——四件是最小機制集⑩審查紀錄：localopt-*-verdict.md 全文＋user 三修（大審不可避免/避免 local opt 是重要方向/卡級時間軸盲目）〕

範圍——改：skills/execution-plan/SKILL.md（⑤kill criteria 段）；skills/corrections-weekly/SKILL.md（③Heat 聚合輸出：五 family→Cool/Warm/Hot 態+觸發 family，週報加一節）；skills/code-review/SKILL.md（⑧--arc mode+lanes+convergence stop+cadence 規則）；skills/review-engine/SKILL.md（⑦跨卡掃描準備步掛點——EP v2 凍定）；skills/deep-work/SKILL.md（⑧一行劇本指針＋dry-run 保底第二行）；新：skills/_common/consumer-dryrun-corpus.md（⑥四型任務+控制變數+friction 格式）；flow-feedback 入口輕量化（⑥）。
明示不動：AIR-126/128（已結案）；AIR-129 獨立平行薄 EP、AIR-127 獨立平行卡直行——對帳已定（EP §5：127 掛點 memory-audit 與本 EP 變更檔零交疊，muse ep-review 機械核查通過）；既有 corrections 分類/parity 機制本體。
AC：①corrections-weekly 週報含 Heat 態行②execution-plan kill criteria 四欄格式表在場③code-review --arc 段在場（scope/lanes/stop/cadence 含 review-power guard）④跨卡掃描掛點+兩問在審查準備⑤dry-run corpus 檔在場（四型+禁 topology 提示+friction 三行）⑥instruction-writing 審查閘（boundary 跨家族）⑦與 AIR-126~131 對帳表（127 重疊處置、優先序）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
S1 結算 Receipt：classification=boundary（Heat 升溫規則）｜review=bi——muse 5 findings＋codex 3 findings 全修入（job-mu6en3ro/job-mu6en3ud）｜fresh｜healthy。S2 結算 Receipt：classification=boundary（EP 條文）｜review=bi——muse ACCEPT＋codex 5 處方全修入（job-mu6ezh4a/job-mu6ezh76；UNKNOWN 限定 hypothesis 層、1-3 cap、decoder rule、INVALIDATED 接 Done、止損 carrier 落 corrections-weekly）｜fresh｜healthy
<!-- SECTION:NOTES:END -->
