---
id: AIR-100
title: memory 池治理整併弧——auto-memory 導流納管＋存量補審＋寫入防護＋夜波半機械化（併 AIR-90/83）
status: To Do
assignee: []
created_date: '2026-09-15 14:34'
updated_date: '2026-09-15 14:34'
labels:
  - governance
  - memory
  - agent-workflow
dependencies: []
ordinal: 85000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ZCode 的 auto-memory 功能會自動把 session 結論直接寫進記憶池（已實證是 harness 背景寫入、繞過六問與所有閘），池內已堆 41 條未審寫入。這張卡把記憶池治理一次收攏：把 auto-memory 納管為正式寫入源、41＋19 條存量逐條補審、寫入端加防護、夜波抽檢半機械化；整併原 AIR-90 與 AIR-83 成單一治理弧避免同域互踩。驗收＝AC A1–A6（機械可驗）。
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

〔已決策勿重辯：①auto-memory 機制定論＝ZCode harness 原生背景蒸餕寫入者（09-15 三證據釘死）：非 skill/rule 觸發（格式無 repo 定義）、非 session LLM 寫入（本 session 7 條反證）、繞 hook/inbox/六問②治理方向＝導流納管（三選一之 2，user 09-15 拍板）：承認為第五寫入源、經 consolidation 審查路徑納管（夜波 quarantine 三 allow 增列 auto-memory 類）；不拆 symlink、不硬擋——品質有真值（user 糾正/平台事實類），擋掉等於放棄已運作的蒸餕管道③存量＝reconciler 口徑 41 條＋AIR-90 原 19 條對帳一次處置，防雙重④清洗標的＝弧狀態/inflight 類（已開卡 To Do＋commit hash 違 desc 三不）；真蒸餕價值＝收編進池 git⑤AIR-90/83 整併入本卡（同域單弧防 wave/治理檔互踩；兩卡原已決策由本 Plan 承接，final summary 記歸屬）⑥memory-audit:147「projection 機制尚未落地（AIR-85）」註記 stale——AIR-85 已 Done、bundle pointer projection 實際在場（系統提示可證），本卡順手訂正⑦池鐵律：禁整池 reset／git clean；untracked 一律保留待裁〕

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
<!-- SECTION:NOTES:END -->
