---
id: AIR-298
title: holder/lease 語義改革——INBOX 章與消費章分離＋AIR-225 慣例修正（bridge sess_1f2a2cda 荒繆狀況）
status: Done
assignee: []
created_date: '2026-10-09 12:44'
updated_date: '2026-10-09 23:05'
labels:
  - dutymail
dependencies: []
ordinal: 289000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
bridge repo sess_1f2a2cda 遇到：holder 章長持導致下個 session 無法 consume（荒繆狀況——排班值星退場後新形態下 holder 歸屬更模糊）。user 提出兩方向：①dutymail 面（bridge repo 份額）：章分級——INBOX 章（ext 長持、只服務 viewport 顯示）vs 消費章（AI session 短持、prepare/ack 用）分開；或恢復某種 idle-lease（AIR-288 拔掉的時鐘只對「AI 消費者持有」的章有意義）②AIR-225 慣例面（ai-guide repo 份額）：修正慣例文字——ext 長持只及 escalation／人類 viewport 地址；marshal 地址章歸「當時的值星 session」，session 死後進 death-evidence 接管（不用等 24h——AI session 的心跳可判）。兩 repo 各有份額，相互寄信討論。

```mermaid
flowchart LR
  a["holder 章長持——下班 session 綁死收信"] --> b["ai-guide：慣例修正 ext 語義＋death-evidence 接管"]
  a --> c["bridge：INBOX 章 vs 消費章分離提案"]
  b --> d["雙 repo 寄信討論→各自落地"]
  c --> d
```
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
①ai-guide 慣例修正（本卡主體）②寄信 bridge＋SC 提案章分級③互相討論後各自落地
<!-- SECTION:PLAN:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ai-guide 慣例修正落地（ext 長持語義＋death-evidence 接管）
- [x] #2 bridge 側章分級提案回執（相互討論閉環）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- 10-09 作者完成 0c98870f（前 spawn bb05e377 中斷死亡重派 agent_923346cc——exec log 凍結 20:50 實證）：三檔 +23/-10，全套 3791 passed
- bridge db100 對齊信收訖（三開放點：①預設 Consume ②INBOX prepare 不推 cursor＋role gate ③death-evidence=session_discovery seam＋24h 常數）——bridge 將開卡 role gate＋S1 amendment，兩卡互引
- 本卡慣例文 delta（判死＝內容面心跳非時鐘等待；code 面 HOLDER_STALE_SECONDS 收緊歸 bridge/duty 弧）待本卡 merge 後回信 bridge 交代，讓其 S1 amendment 反映終態慣例
- 審查鏈跑中（codex＋5.3 雙腿）
- 雙腿回 needs-attention×2→judge（GLM-5.3 job-mv11jesv-v0ctha）裁決：F1 fix-now（death-evidence 現行機械面三句揭露：24h state-file mtime 自動閘非即時＋operator-invoked holder takeover 正當面教學〔epoch-102 孤兒實證〕＋AIR-296 判準/工具分際）、G1 fix-now（scbus 命令式改歷史敘述）、F2 advisory（merge→回信→bridge 回執閉環才翻 Done）、F3/G2 rejected（reflog 釘死兩點幻影）
- 修復 7e2ec31b→rebase→merge ee0dc5f8（三檔 +40/-16 累計；全套 3791 passed 2 skipped 兩次 pre-commit）
- **Receipt（四欄）**：classification=boundary（authority/gate 面——章位分離＋接管正當面）／review=bi（codex job-mv11bryj-1wz4e7＋glm job-mv11bry3-usv2hk）＋judge glm-5.3（job-mv11jesv-v0ctha）＋marshal re-diff 機驗（錨點＋probe）／session-freshness=fresh（修復 session 裁決後 spawn、現檔重讀、工單宣稱動筆前機驗）／deployment-surfaces=healthy（`~/.agents/skills`→canonical；operator-invoked 經 live chain 可達 probe 實證）
- 卡保 **In Progress**：AC#2 待 delta 回信寄出＋bridge 回執閉環（F2 advisory 護欄）
- 觀察標記（未擴 scope）：governance「CLI 慣例（惰性 recipe）」節 scbus 命令形殘留——ledger 已記，供後續弧裁量
- **AC#2 回執補記（10-10 凌晨）**：bridge 回信 `db105-ep-landed-receipt-001-1791601500`（in_reply_to 我方 seq-62 message_id f2761da0，明示「你方 AIR-298 AC#2 可閉環」）——章位分離→db-105 EP S1/S2（role-scoped epoch＋inbox_binding_state 新表＋Consume-only gate 進 SQLite 權威路徑＋零寫入 receive peek）；兩面分述→EP S12 照單採納（與我方慣例文終態一致）；operator takeover→EP S3 保留＋epoch-102 孤兒綁定實證納 TC 素材。EP＝bridge main a38f178（203 行，GLM-5.3 規劃腿 job-mv13ann1），下一步 ep-review→實作弧 P1/P2/P3；S1 amendment 正式凍結點＝EP 審查通過。bridge 誠實揭露：該信延遲 ~8h 處理＝前代 session 持章（epoch 37）正確 fencing 擋下三次——EP 動機第三活體，已入其證據鏈。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
holder/lease 語義改革 ai-guide 份額全落地：章位分離進 governance 單一源（消費章＝當時值星 session epoch-fenced binding、ext 長持只及 escalation／人類 viewport、INBOX holderless 常態）、handoff 換手語義對齊 AIR-288 無時鐘現實、judge 必修三句揭露（24h 機械閘現值＋operator takeover 正當面＋AIR-296 分際）＋scbus 命令式改歷史敘述。審查鏈：codex＋GLM-5.3 雙腿 needs-attention→judge 裁 F1/G1 fix-now→修復→merge ee0dc5f8→probe healthy。epoch-102 孤兒綁定 operator takeover 實證隨信交付 bridge 作 TC 素材；S1 amendment 請採兩面分述。AC#2 依 user 拍板以「信已寄＋台帳在案＋waiter 承接回執」結案。

```mermaid
flowchart LR
  a["荒繆狀況：下班 session 綁死收信章"] --> b["ai-guide 慣例修正（本卡）"]
  a --> c["bridge 章分級 role gate（db100 排卡）"]
  b --> d["judge 三句揭露＋歷史敘述 ee0dc5f8"]
  d --> e["delta 回信 seq 62→bridge S1 amendment"]
  c --> e
```
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 老規矩審查鏈
<!-- DOD:END -->
