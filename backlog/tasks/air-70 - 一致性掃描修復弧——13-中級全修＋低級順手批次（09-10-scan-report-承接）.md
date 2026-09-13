---
id: AIR-70
title: 一致性掃描修復弧——13 中級全修＋低級順手批次（09-10 scan-report 承接）
status: Done
assignee: []
created_date: '2026-09-09 22:40'
updated_date: '2026-09-13 14:22'
labels:
  - governance
  - consistency
dependencies: []
references:
  - ai-analysis/reports/2026-09-10-repo-consistency-scan.md
ordinal: 56000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
09-10 02:00 三軸掃描報告（ai-analysis/reports/2026-09-10-repo-consistency-scan.md）user 拍板全修。範圍：中級 13 條（五群：G1 部署家族清單三版本/G2 claude-specific boilerplate/G4 bundle-skip 未記載/S1 impl-test-gen role 幽靈〔最重〕/S2 STATE.md 三方/S3 commit flow 重畫/S4 usage-ping 語音殘留/S5 階段3 stale ref/S6 斷連結/F1 cleanup plist 無版控副本/F4 mosaic twin 缺 loud-fail〔次重，跨 repo〕/F3 README 必查路徑撲空＋低級順手批次：共識 trivial G10/S7/S9/F2/F5/G7，歧異帶 G5/G8/G9/S8/S10 併入判讀，G6 不修〔誤報〕）。⚠️ 掃描時點 b75e8a7——AIR-52 修正迴圈＋AIR-66 瘦身已動部分檔案（usage-ping/rules 面），執行前逐條 rg 重驗現況，已被修掉的標 washed-out。修法方向照報告 Phase 4 表（序 1-9），F4 跨 repo（mosaic twin 同步）依跨 repo 慣例；第四軸結構性建議（部署渲染/runtime 消費對等）不入本弧，另行評估。驗收：13+順手逐條附 rg/sha 證據＋post-build（docs-mode 為主）＋G11 先查證（Claude loader paths: 消費——probe 後裁）。素材：報告全文＋兩顧問裁決段＋journals .agent-tmp/consistency-*-journal.md。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔triage 併弧 09-10——升級為一致性×錯置總治理弧（兩段連續做）〕段二＝AIR-69 全部內容併入（原卡搬 completed/ 可查）：memory-audit 統一定義表 v2 兩處修補（層級閘首句＋誤置表 A/B——裁決書 ai-analysis/reports/2026-09-10-carrier-placement-v2-conference.md §二逐字條文；零 bundle 增量硬約束＋同 commit 原子性）＋先鋒 8 條已裁執行（user 拍板：bridge-job-completion-no-push 規範正文刪/backlog-cli-entry 刪/global-vs-project-permissions 重寫/cross-session-commit-on-active-branch 規範搬 kanban SKILL＋留事故/backlog-card-edit-precheck 進 kanban 卡操作段/skill-deletion-consumer-scan 併 zcode-skill-usage-audit 後刪/work-order-contract 進 work-order.md/diagnose-installed-vs-source 進 debugging skill）＋雙池全量 audit（forward/reverse lane 掃描＋歸因投影）＋draft-1/2（telemetry 源接線）併入本段。段一（原 13 中級＋低級修復）收斂後無縫接段二——兩段共用 kanban SKILL 等重疊面避免並行。

09-13 scope 分界研究擴充段二輸入：判準回填 diff（層級閘首句＋rule 資格公式＋residency 三測試＋條件載入層 pointer＋desc 觸發面修訂）已備妥於 ai-analysis/reports/2026-09-13-scope-boundary-memory-rules-skills/report.md §六（逐字 diff 全文＝materials/codex-followup-out.txt §C；judge 已採納）。實施時連同 09-10 原定義表兩處修補一次落，rg 驗零殘留（muse r2 原子性條款）。後續 corpus 搬遷（AIR-86）與 vertical slice（AIR-85）都依本卡回填後的載體表為準——先回填後搬遷。

09-13 現況盤點（lite-verify 機械核對，逐項附 file:line 證據）：

**可銷三項**：①段二判準回填＋09-10 v2 修補整塊——commit 809aacd 覆蓋（層級閘首句＋資格公式＋三測試＋條件載入層＋desc 觸發面＋誤置表 A/B/V 列）②四處舊判準 shadow 清理（rg 零命中實證）③段一 S4 usage-ping 語音殘留＝washed-out（標的 :30/:118 已不存在）。

**段一 11 群仍待修**（G1/G2/G4/S1/S2/S3/S5/S6/F1/F3/F4——抽驗細節見盤點報告）；**F1 惡化**：deploy/launchd/ 已被 aa3c5e6（09-11）整刪，acceptance-evidence SKILL:43 仍宣稱其存在——宣稱撈空。**段二先鋒 8 條 0/8 落地**（條目全在、規範面落點全零命中；先鋒1 規範面已被 AIR-66 上 rule——刪除條件成熟）。

**處置裁定（user 09-13 拍板）**：剩餘屬雜項性質非 workflow 弧——不採弧儀式，規劃為清掃 session 批次消化（與 AIR-67 剩餘合併評估）；audit 與 draft-1/2 兩軸性質不同另行歸位。

09-13 批二雙審移入（codex finding，non-blocking）：skills/symbol-query-routing/SKILL.md L121-125「條件式 fallback」段仍以現在式描述 lsp-python MCP 連接（server 已於 2026-08-28 停擺，L106 disclaimer 已框住歷史作用域）——改明確過去式即可，防跳讀誤當現行指令。來源＝AIR-86 批二 codex 審查（.agent-tmp/air86-batch2/codex-review-batch2.txt §4）。

09-13 批三 impl 發現（既存 drift）：skills/execution-plan/SKILL.md L155 引 ai-development-guide 的「Scenario Matrix」段落——新舊 guide 皆無此節（該節實住 execution-plan skill 自身 L137）。修正＝改指自檔或刪 link。來源＝AIR-86 批三依賴掃描。

09-13 批三 codex 審查補充（同型既存違規）：skills/symbol-query-routing/SKILL.md L10「（自 rule 下沉 2026-08-31）」標題含日期——違 guide 禁日期規（與本次批二/批三新增兩處已修同型；codex B3-F1）。修法＝刪日期留承接語義。

09-13 雜項清掃批次一（小弧，branch air-70）：①sqr skill 條件式 fallback 段改 lsp-python 時代過去式框架（codex B2-F1）②execution-plan L155 死 link 改指自檔 Scenario Matrix 節③sqr skill L10＋desc L3「下沉 2026-08-31」日期刪除（codex B3-F1 同型）④F1 惡化修復：acceptance-evidence SKILL:43 刪「repo 內 deploy/launchd/ 只是源」stale 宣稱（目錄已 aa3c5e6 刪）⑤implement:256 提煅→提煉錯字。負詞彙全 0＋404 tests。剩餘：段一 11 群（G1/G2/G4/S1/S2/S3/S5/S6/F3/F4——需 09-10 scan report 逐條重驗 washed-out）＋先鋒 8 條 0/8 落地——維持 user 09-13 拍板：清掃 session 批次消化（與 AIR-67 剩餘合併評估），AIR-87 skills 治理前完成一致性面。

09-13 批二完成（清掃 session 批次主體）：洗滌重驗 12 alive/3 washed（G4 skip 零使用者/S7/F5）→修復 13 動作（中級 G1 家族清單四處對齊+G2 boilerplate+S1 impl-lite+S2 三方+S3 純 pointer+S5/S6/F3＋低級 G10/S10/F2/S9）→先鋒 8/8 落地（skill 側 port 4：kanban 落點分流+卡編輯查驗/work-order 指路可達/debugging installed-vs-source；pool 側 fabf4e7：刪5+重寫1+事故化1+併入1、淨瘦 18.8K）→consistency 15 檔（2FAIL+4觀察全修：_inbox 三複本同步/線域/hook 2.0.x 形態/precheck 消歧）→codex NO-GO 8 點全閉（含 F2 executor shape 三段修：路徑→bin 形態→direct executable+SessionEnd zcode）＋verify-close 9/10→10/10（末點照處方逐字）。404 tests＋deploy＋404 基線全綠。**剩餘：F4 跨 repo（mosaic twin cleanup 同步）——另案 handoff/mosaic 側卡**。批一+批二完成＝段一 11 群閉合＋先鋒 8/8，本卡 Done。

09-13 晚 F4 閉合（跨 repo 銷帳）：mosaic twin guard 合併由 mosaic 側 session 依 handoff（backlog/drafts/handoff-mosaic-twin-f4-2026-09-13.md）完成——本卡 09-10 承接的 13 中級 findings 全數閉合。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
一致性掃描修復弧閉合：段一 11 群（9 修+F1/S4 washed+F4 跨 repo 另案）＋低級 trivial＋先鋒 8 條全落地；兩輪清掃批次（09-13）＋codex 三輪審（NO-GO 8 點全閉＋verify-close）；memory 池淨瘦 18.8K＋規範遷移 skill 側四處。F4 除外已全清。
<!-- SECTION:FINAL_SUMMARY:END -->
