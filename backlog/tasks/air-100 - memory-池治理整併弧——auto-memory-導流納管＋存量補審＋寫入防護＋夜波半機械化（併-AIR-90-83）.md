---
id: AIR-100
title: memory 池治理整併弧——auto-memory staging＋單向晉升＋存量補審＋寫入防護＋夜波半機械化（併 AIR-90/83）
status: Done
assignee: []
created_date: '2026-09-15 14:34'
updated_date: '2026-09-17 00:54'
labels:
  - governance
  - memory
  - agent-workflow
dependencies: []
ordinal: 85000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ZCode 的 auto-memory 功能會自動把 session 結論直接寫進記憶池（已實證是 harness 背景寫入、繞過六問與所有閘），池內已堆 41 條未審寫入、池基線也早被污染。這張卡把記憶池治理一次收攏：auto-memory 產物改走 staging＋單向晉升（永不自動進池）、41＋19 條存量與已污染基線逐條補審、寫入端加防護、夜波抽檢半機械化；整併原 AIR-90 與 AIR-83 成單一治理弧。治理形態經 codex/muse 雙腿第二輪討論收斂（兩腿獨立提出同構方案）。驗收＝AC A1–A6（機械可驗）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A1 導流條款在場：memory-audit 含 auto-memory 第五寫入源＋consolidation 審查路徑（rg 可驗）；夜波 quarantine allow-list 增列（可驗）
A2 存量清零：41＋19 對帳處置表落任務家（每條 disposition＋證據：收編 commit／搬卡 notes／刪）；reconciler 復跑 exit 0（或殘留全為處置日後新流入，明列）
A3 寫入防護實測：帶狀態後綴新條目被擋（實測一筆）；成對殘留偵測跑一輪有輸出證據
A4 夜波半機械化：新流入 Q1 初篩 script 實跑（排序＋指針銷帳報告）；memory-audit B 形態條文校準＋cron prompt 接線在場
A5 memory-audit:147 stale 訂正（AIR-85 已 Done、projection 實際在場）；若觸 rules 照 rules/AGENTS.md 部署驗證綠
A6 護欄：池 git 歷史僅增補（無 force/reset/git clean）；untracked 處置全程留痕
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide b8a70b1；證據＝scripts/reconcile_memory_pool.py 實測 FAIL 41 條（15M＋26 untracked）＋ auto-memory 機制調查（originSessionId/node_type 格式無 repo 出處；跨專案 code-reality 88/89、ai-lifecycle 37/40 帶同格式；本 session 7 條非本人寫、mtime 對齊里程碑時刻；夜波流入快照自 09-09 起已收編同格式——approved baseline 混有 auto 產出）＋ 09-15 載體稽核（reports/2026-09-15-workflow-carriers-crud-principles.md 三主題群抽樣）〕

〔已決策勿重辯：①auto-memory 機制定論＝ZCode harness 原生背景蒸餕寫入者（09-15 三證據釘死）：非 skill/rule 觸發（格式無 repo 定義）、非 session LLM 寫入（本 session 7 條反證）、繞 hook/inbox/六問②治理方向＝**staging＋單向晉升**（09-15 第二輪雙腿討論後修訂；原「導流納管」方案被雙腿論證否決——muse：consolidation 負擔隨寫入量線性膨脹且寫入量由背景模型決定、純納管＝追認已污染基線、弧狀態/inflight 類在官方記憶定義域外＝normalization of deviance；codex：純納管需加隔離層才成立）：auto-memory 產物**永不自動進池、永不自動進 inbox**；晉升＝pull（按需人/LLM 觸發）逐條重寫成六問形狀＋provenance 標籤；工作量 O(需求) 非 O(寫入)。staging 形態二選一（實作首日定並記錄理由）：(a) 拆 symlink→ZCode 原生目錄即 staging（池外零基建；代價＝ZCode 開場注入轉原生 index，curated 池靠 AGENTS.md 指引 rg 補）或 (b) symlink 改指 `.agents/memory-auto/`（repo 內 staging、gitignored；auto-memory 續寫不停）——共同點：池 HEAD 恢復乾淨、reconciler「HEAD＝approved」語義恢復真實。組態事實（muse 查證）：ZCode Memory 開關存在（UI 級：設定→通用→Memory；**預設關**、v3.6.4+、僅新 session 生效；`config.json` 無 memory 鍵——ref-docs/harness/zcode/cn/docs/memory.md L38–43；cn 是唯一操作文檔）；粒度（per-project vs 全域）實作時先驗證，若 per-project 安全可作源頭輔助開關（user 的 UI 動作），非本卡依賴③存量範圍擴大＝不只 41 dirty：**污染基線重審**——夜波自 09-09 起以流入快照收編 auto-origin 條目進池 git（HEAD≠純六問策展），實作時以 `git log -S originSessionId` 定量後逐條重審，處置路徑同 41 條；41 條＋AIR-90 原 19 條對帳一次處置防雙重④清洗標的＝弧狀態/inflight 類（已開卡 To Do＋commit hash 違 desc 三不）；真蒸餕價值＝收編進池 git⑤AIR-90/83 整併入本卡（同域單弧防 wave/治理檔互踩；兩卡原已決策由本 Plan 承接，final summary 記歸屬）⑥memory-audit:147「projection 機制尚未落地（AIR-85）」註記 stale——AIR-85 已 Done、bundle pointer projection 實際在場（系統提示可證），本卡順手訂正⑦池鐵律：禁整池 reset／git clean；untracked 一律保留待裁〕

範圍：
P1 auto-memory 導流條款——memory-audit（載體統一定義表＋consolidation 節）增第五寫入源與審查路徑；夜波 quarantine allow-list 增列。
P2 存量補審——41＋19 對帳逐條 disposition（收編／搬卡 notes／刪），處置表落任務家 references；reconciler 復跑驗收。
P3 寫入端防護（原 AIR-90）——狀態後綴（-inflight/-pending 等）新條目硬擋＋同名成對殘留偵測。
P4 夜波半機械化（原 AIR-83）——新流入 Q1 初篩 script（排序＋指針銷帳）＋memory-audit B 形態遺留條文校準＋host cron prompt 接線。
P5 memory-audit:147 訂正＋（若觸 rules）部署照 rules/AGENTS.md。

不做：不拆 ZCode memory symlink、不動 muse governance plugin（AIR-93 軸另計）、不整池重寫、不做額度經濟學。

風險面：誤刪真價值條目（處置表留痕＋可逆 git）；wave 與本卡並行互踩（memory 域已整併單弧）。相鄰不重複：AIR-93（muse teardown 繞閘——同 genus 不同家族）、AIR-63（inbox pending 覆層——feature 非治理）、DRAFT-4（記憶拓撲審視）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Provenance：09-15 user 提問「CRUD 準則有沒有開卡＋驗一下配置」→ 載體稽核三主題群抽樣（rules 分層 ✓/卡面 ✓/memory 抽樣抓誤置）→ 發現 41 條未收編（reconciler FAIL）→ auto-memory 機制調查（user 假說「其他 session 觸發 skill/rule」被三證據否證：格式無 repo 出處、他專案無 skills 照寫、本 session 反證）→ 治理三選一 → user 拍板導流納管＋整併開卡。併卡：AIR-90（P3＋P2 對帳）、AIR-83（P4）。調查過程在本 session 對話＋reports/2026-09-15-workflow-carriers-crud-principles.md。

09-15 user 質問「改連 memory-auto 後 ZCode 怎用到維護池」——P1 增設計項【開場注入保護】：事實＝ZCode 對池的消費有兩面——push（開場注入 MEMORY.md 常駐 12 條，經 zcode memory dir 雙跳）與 pull（AGENTS.md 觀察池路由：主體路徑＋rg _inventory → Read body，always-on）。改指後 pull 不受影響（路由行與 symlink 無關）；push 會失去。緩解＝在 memory-auto/ 手寫 MEMORY.md 當 routing 指針（本目錄＝未審 staging；curated 池在 .agents/memory/，rg _inventory）→ 開場注入變成池的指針。待驗證＝ZCode 背景寫入者會否覆寫/重生成其目錄的 MEMORY.md（P1 實測；若會，fallback＝強化 AGENTS.md 路由行）。誠實成本＝常駐 12 條的被動提醒（~2.3KB）改為指針；CC 端不受影響（readlink 實證：CC 腳獨立直連池，zcode 腳改指不動它）。

09-15 user 裁定①：**P0 POC gate 前置、不馬上做**——staging 形態 (a)/(b) 及開場注入方案須 POC 實證後才拍板。②user 提出**變體 (c)：memory-auto/MEMORY.md 用 symlink 連到池的 MEMORY.md**——直接保住 push 注入（優於手寫指針）；風險＝若背景寫入者會寫 index，write-through symlink 會污染池投影——這正是 POC 要測的。P0 POC 項：(1) 背景寫入者是否寫/重生成其目錄 MEMORY.md（觀察 code-reality 原生 dir＋ai-guide 改指後實測）(2) 若寫，是否 write-through symlink 進池 (3) 變體 (c) 下注入是否真吃到池 index。pre-POC 證據（09-15）：code-reality MEMORY.md 為 session 手筆風格（rich 列點/✅終態/跨引用），未見 originSessionId 條目入列——index 由 session LLM 維護的假說獲佐證、背景寫入者不動 index 的機率高。P0 通過後才動 P1 手術。

〔09-16 重裝稽核新事實——muse governance plugin 更新鏈已斷，建議隨本弧 P1 併處〕①稽核實測：muse-memory-governance plugin 的 source provenance 指向 ~/Github/ai-rules/muse-plugins/memory-governance（rename 前舊路徑，現已不存在）；現況 muse cache 內容與 ai-guide/muse-plugins/memory-governance 逐檔一致、runtime trusted_enabled——功能正常，但下次 content update 的源頭註冊會失敗。②與本卡關係：本卡 P1 staging 手術（symlink 改指 memory-auto／變體 c write-through）動的是同一目錄族（.agents/memory* symlink＋memory-governance.json marker＋inbox divert＋reconciler 假設）——plugin 重註冊（源改指 ai-guide 現路徑）宜隨 P1 同弧一次做完，避免兩次動同一拓撲。③原排除條款「不動 muse governance plugin」係指 AIR-93 軸（session-end 繞閘，已 Done）；本項是 0916 稽核新發現的部署鏈事實，非重辯。④處置選項留 user：(a) 隨本弧併處（預設建議）(b) 立即單獨重註冊（一個 muse plugin 指令）。附帶：CR binary 落後 d105806 一 fix（非 memory 域，另計）；「部署面對帳」流程缺口已列治理卡候選。

〔0916 補充更正〕CR binary 一項經 user 已裁定無需更新：d105806 僅改 release.sh（wheels readiness barrier，下次發版才生效），binary 行為零差異——不出 0.9.2。

〔0916 user 拍板〕本卡於 sess_014a87f8-e39c-41dd-bad0-1e658d18a56b 時執行，到時完整規劃。bi panel 規劃素材已存 .agent-tmp/six-card-review/dossier.md＋bi-*.out，該 session 開工必讀——要點：①先立 cutover snapshot 阻止移動目標再逐條補審 78 條 ②baseline 以 as-of 重定（41→78 已翻倍）③staging 拓撲決策需連動 wt-open/close 的池 symlink 敘述 ④panel 依據的仲裁條目（project-uisc-audit-11card-arbitration.md）自身是未審 auto 寫入，補審須裁定可採性 ⑤卡內 staging 方案與舊排除條款矛盾先收斂成單一契約。

0917 凌晨 Segment 0 前置調查開工（caller 排程）：muse（機制正確性評估）＋flash（runtime 探測）兩腿並行——涵蓋 handoff 九條 runtime validation 可執行項；完成後交 codex＋5.3 討論機制，裁決輸入回 user。調查產物＝.agent-tmp/guides-refactoring/。

0917 凌晨機制裁決（caller 拍板，codex/muse/5.3 三顧問共識）：D1 admission 唯一化（consolidation 唯一入池權威）；D3 crash 分級（品質門 fail-open、admission 門 fail-closed）；D4 codex 補最小 path-deny-all（tool 名先探針）；D5 退役夜波快照結算——今晚零工程、停波＝正確行為；S1-S5 吸收為 Segment 0/1 不另開卡，唯 S4/S5（全波停閘改 per-file／scoped snapshot 鏈）因 D5 退役而 moot 不執行；S1（sensor --source 顯式傳入）無條件先做；muse plugin source.path 舊路徑＝從 canonical source 重裝＋re-approve；subagent 雙面隱形＝接受 detected-only＋spawn contract 加禁碰池約束。⚠️ I4 反轉更正：『ZCode sensor 從未 fire』為誤——memory-write-sensor.py:48 硬編 source label，ZCode hooks 一直在 fire（64/64 join 實證）；真盲區＝背景蒸餾器寫入。runtime 探測全記錄＝.agent-tmp/guides-refactoring/{f-probe-output,m-mech-output,mech-synthesis}.md

【收線 coverage matrix＋卡 AC 回寫（EP 收尾步驟 1/2 執行）】writer×防線矩陣終態：CC/ZCode main Write/Edit=prevented；subagent=detected-only（reconcile 兜底；spawn contract 禁碰池已落 agent-workflow skill）；muse tool write=prevented-via-divert（trusted_enabled 已驗證）；muse teardown=Bash redirect=codex 寫池（S-A 前 unsupported→S-A 後 prevented）——codex path-deny 閘已註冊 config.toml:365-376；NotebookEdit=unsupported（matcher 移除，parity assertion 防再生）；後綴 invariant=prevented（P3 落地＋AC-B7 failure-path 誠實標記：載體 fail-open 為已知缺口）。卡 AC 回寫：A1 範圍變更（staging/晉升條文承接＝memory-audit AC-D5，quarantine allow-list 隨 D5 作廢）；A3 吸收路徑（S-D 處置表銷帳＋reconcile）；A4 隨 AIR-83 整併＋D5 作廢；A5 已修（memory-audit:149 projection 訂正 commit 12b25c0）。deferred：AC-A6 codex session live 實跑（須 trust approval 後新 codex session）、P0-5 main live 重放、AC-D1/D4 新 session 觀察——集中總驗卡機制。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
memory 寫入治理落地：codex path-deny 閘（apply_patch canonical＋fail-closed）、後綴擋 P3（air-90 承接）、NotebookEdit dead-matcher 處置＋parity assertion、approve-drift monitor 源、(a) staging 手術＋91 條 reviewed admission（收編 34/修寫 31/退役 21＋air111 墓碑/拆分 4，池 porcelain 歸零）；closure 三層閘自我消費（44 新測試，全套 715 綠）。deferred：AC-A6 live、D1/D4 新 session 觀察——總驗卡機制
<!-- SECTION:FINAL_SUMMARY:END -->
