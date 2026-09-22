# blueprint — AI coding 開發藍圖知識庫

> **定位**：本目錄提供 ai-rules 的人讀合成視角，讓人類在約五分鐘內掌握整體工作流、執行拓撲與重建路徑；AI 也可據此理解跨域流程，但機器導航與規範權威仍在 repo `AGENTS.md`、`rules/`、`skills/` 與各機制 source，本目錄不建立第二套規則。

## 各檔真相源映射

| 檔案 | 真相源 | drift 速度 | 本檔負責合成 | 更新觸發 |
| --- | --- | --- | --- | --- |
| [workflow.md](workflow.md) | WT 形態與責任邊界以 [WT workflow 正式裁決報告](../reports/2026-09-10-wt-workflow-decision.md) 為準；git/branch 收斂語義以 repo AGENTS.md「git 慣例」與 kanban-board 為準；八站主軸取自 [整體設計審視](../reports/2026-09-10-holistic-design-review.md)；O1–O8 與波次取自 [執行順序藍圖](../blueprint-execution-order-0910.md)；②⑥站殼 codegen 取自 [illustrate 三方終案](../../.agent-tmp/illupatch-synthesis.md)（固化後改指正式 report）＋mosaic [試驗附錄](../../../Github/mosaic_alpha/ai-analysis/_projects/marking/tasks/09-09-tree-registry-compiler/ep.md)（跨 repo pointer）；viewport 供給以 [viewport 架構裁決](../reports/2026-09-10-viewport-serving-architecture.md) 為準，服務機械事實＝mosaic run-report-server.sh（跨 repo）＋schedule-registry 條 A5＋illustrate-html-mode 放置分流；測試契約與驗證分工以 [測試契約裁決 v3.1](../reports/2026-09-11-test-contract-design.md) 為準（user 三輪挑戰＋muse/codex 三輪複驗；含 cr-research 升 full 的研究層 agent 分工） | 中；WT 基建落地期偏快 | 八站生命週期、primary/card-WT 責任分界、board single-writer、memory 拓撲、open/close transaction、波次與 freshness invariant、viewport 供給三層與放置規則、測試契約與驗證分工、agent 分工原則（判斷密集 vs 機械可驗） | WT/branch 慣例、kanban ownership、memory topology、session 開收流程、O1–O8 衝突或波次裁決、殼產線（codegen/手填 legacy）改變、viewport 供給層（:6421 路由／launchd 服務／preview 慣例）改變、測試契約（TC／challenge／audit 軸A／review 軸B）改變 |
| [onboarding.md](onboarding.md) | [MULTI-MACHINE.md](../../hooks/MULTI-MACHINE.md)＋[deploy_agents.py](../../scripts/deploy_agents.py)＋[rules 部署契約](../../rules/AGENTS.md)＋[agents registry 契約](../../agents/AGENTS.md)＋fresh-machine / new-repo dry run [UC6/7 清單](../reports/2026-09-10-dryrun-uc67.md)。排程現況由 [schedule-registry.md](../schedule-registry.md) 輔助，code-reality 安裝語義由 [code-reality skill](../../skills/code-reality/SKILL.md) 提供 | 中；machine-local 接線改動時快 | 從空機器恢復 ai-rules 所需的六段 runbook，以及現有支撐與缺口 | deploy 目標、skills/agents symlink、hooks 接線、memory 備份拓撲、cron/launchd、code-reality 安裝或 UC6/7 dry run 結果改變 |
| [structure.md](structure.md) | 載體結構事實以各域治理檔（root／[rules](../../rules/AGENTS.md)／[agents](../../agents/AGENTS.md)／[hooks](../../hooks/AGENTS.md) AGENTS.md＋[skills](../../skills/AGENTS.md)、[governance](../../governance/AGENTS.md)、[scripts](../../scripts/AGENTS.md) 各域 AGENTS.md）與三 generator（deploy_agents／sync_agents／check_single_source）為準；workflow 消費表以 agents/AGENTS.md execution contract＋skills/AGENTS.md 拓撲＋schedule-registry 為準 | 低；載體生成鏈穩定，增退役載體時改變 | 五層載體×四種邊（部署/引用/消費/治理）全域結構、reference 分層配對、已知斷鏈與受控缺口 | 載體增退役、generator／invariant／registry 投影規則改變、部署接線或記憶/tour/排程拓撲改變 |

正式裁決 report 提供 architecture decision；暫存顧問輸出只作形成裁決時的 evidence，不承擔 blueprint 的長期真相源。

## 更新紀律

- **消化重編，非局部 patch**：先讀對應真相源與現行實作，再重寫受影響段落，使一份文件從頭到尾仍是一個完整心智模型。不得只修一行舊敘事而留下前後兩種架構。
- **單一真相不重複**：blueprint 可以重述完成一個跨域流程所需的最小順序，但 CLI 細節、branch 規則、hook schema、排程機械事實、memory-audit 判準仍由各自 source 擁有。詳細規則以連結回源取代正文複製。
- **現況與定案分開**：已落地行為標 `✅`；已有部分 substrate、但 target contract 尚未完整落地標 `⚠️`；尚無可靠執行面標 `❌`。設計已拍板不等於 runtime 已存在。
- **載體層級先判斷**：本目錄只承載 ai-rules project-level 合成知識。若一條原則去掉 repo 名後仍應跨 repo 成立，升到 user-level rule/skill；project-specific 例外、現況與入口留在 repo carrier。memory 只留事故證據、偏好/例外與 pointer，不複製規範正文。
- **退役制**：被新藍圖完整吸收、已無獨立查閱價值的舊 blueprint 文件搬入 `_done/`，檔頭指出由哪個現行文件取代；不讓舊版與新版並列成雙真相。
- **不以 report 歷史當 runtime 現況**：report 固化決策與證據；凡宣稱「現在會怎樣」，仍須回查目前 config、script、skill 或 Git 狀態。
- **TODO 不自動升格**：缺口被列入 blueprint 只是待建項，不代表已承諾實作；承諾仍進 Backlog.md／EP。
- **Priority backbone（user 拍板）**：blueprint 的 target 形態與收斂序列（六線波次等）決定主線做什麼與順序；backlog 仍是承諾單一源——backbone 選卡不改變承諾建卡流程，未被 backbone 支撐的卡照 kanban-board「遠期卡治理」triage 面處置。

## 對齊覆核觸發

以下任一事件發生後，重新覆核對應 blueprint；沒有來源變動時不做定期重寫：

1. `AGENTS.md` 的 card branch / worktree / rebase / ff-only 慣例改變。
2. `kanban-board` 的建卡、status/ref、precheck、`check_active_branches` 或多 WT 契約改變。
3. `wt-open`／`wt-close` 基建落地或 transaction 行為改變。
4. `.agents/memory/`、`.agents/memory-inbox/`、CC/ZCode/Muse 接線或 memory consolidation ownership 改變。
5. `deploy_agents.py`、skills/agents symlink 或其他部署方式改變。
6. ZCode cron、launchd、schedule registry 或 fresh-machine recovery source 改變。
7. code-reality 安裝／bootstrap／repo profile 流程改變。
8. 新一輪 UC dry run 發現現有 runbook 無法從空機器或新 repo 走通。
9. 大型 workflow arc 收斂，並且它改變八站任一站的 owner、輸入、輸出或 handoff。
10. `:6421` 路由、launchd 服務（report-server／backlog-browser）或 viewport／preview 慣例改變。
11. 測試契約六檔（TC 格式／challenge／RED provenance／audit 軸A／review 軸B／test-gen routing）或研究層 agent 分級改變。
12. 載體集合或生成鏈改變：任何載體（rule／skill／agent role／hook／plugin／generator）增退役、invariant 集合變動、registry 投影規則改變——覆核 [structure.md](structure.md) 全圖。

## 對齊覆核流程

1. 依上方映射定位受影響文件與真相源。
2. 先看目前 source 與 executable/config 現況；report 用來確認已裁決 architecture，不能代替 runtime 查證。
3. 對 workflow 類變更，逐項核對 owner、cwd、branch、baseline、board、memory、finalization 是否仍只有一個責任歸屬。
4. 對 onboarding 類變更，從「空 home state」角度重走依賴順序；缺安裝 source、secret recovery pointer 或本機 DB prompt source 時維持缺口，不補未驗證程序。
5. 消化重編 drift 段；同時移除已被新定案取代的舊敘事。
6. 檢查所有 `✅/⚠️/❌` 與 source 一致，尤其避免把 target architecture 寫成 implemented behavior。
7. 人類最後以全貌判讀：能否在約五分鐘回答「工作從哪來、在哪做、誰能寫什麼、如何收、機器壞了怎麼回來」。
