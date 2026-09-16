---
id: AIR-50
title: 開發流程契約修復＋反饋固化——codex 六斷點＋mosaic MOS-74 四條
status: Done
assignee: []
created_date: '2026-09-08 22:02'
updated_date: '2026-09-09 04:17'
labels:
  - docs
  - skills
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-09-skill-contract-fixes/index.html
  - ai-analysis/_tasks/_archived/09-09-skill-contract-fixes/index.html
ordinal: 42000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔baseline：ai-rules ba386cb〕〔已決策勿重辯：A線①保留七 skill 入口不合併；修序先交接→再分流→最後減法②PB3 結案時點採收斂後單一發布（post-build hook 2／implement 6 fallback；5a 只到 🟡 Built）——guide 等全引用面同步（EP Review F1 補五消費端：flow-review/skills CLAUDE.md/blueprint-bootstrap/maintain/context-management）③findings 帳本＝.review 正典化為工作帳本（EP review 區段＝規劃期）；caller 指定可覆寫④.md 分流以**語義判準**判行為控制面（塑造 LLM 行為之檔——AGENTS.md 家族/rules/skills/agents/commands/hooks/settings/guide；路徑降 hint＋純修飾輕量快道）走 code-review docs-mode⑤EP 定稿 gate＝三背景 agents 遺漏吸收＋EP Review（已完成——零 Critical、F1-F6 全處置）；B線⑥bridge 直跑範式定案（agent 轉發退役——timeout 約束從未存在；外部 runtime 承載者＝背景 Bash，禁 subagent wrapper）；resume 鏈 review→judge→修正→同 session followup 獨立記載⑦Finding 驗證式欄＋external reviewer 工單要素（followup 零摩擦關鍵）⑧長命令背景跑通則入 tool-discipline＋三層反模式案例⑨固化分層：操作事實留 memory、機制進 ai-rules（mosaic 側已改寫，承接不重做）⑩tour_validate 重現實測**不重現**（現行版中文目錄掃描正常、205 tours）——降級結案，repro 紀錄留任務 references/；C線⑪AIR-48 剩餘併入同弧（S9）——本卡結案時同步結 AIR-48；裁⑫review agent 層（ep-review／code-review 審查 agents）**預設 lite（glm-5.3-flash）**＋條件式升 full；judge／EP 規劃層不變（full 主 session）——model-routing skill:42 強化＋rule 骨架對齊（修 rule↔skill drift）＋registry pins 經 sync_agents 重生成＋ep-review spawn 載體改 registry 唯讀 lite（user 09-09 裁定，S10）；⑬rename 反掃——post-build metadata-sync 段補機械步驟（弧 diff 萃取 rename/move/retire 舊符號→rg 掃 AGENTS.md 家族＋快 drift 檔→命中修或記 drift；非 rename 弧空跳、不全檔重驗）——mosaic 地毯掃描量化證據（5/8 P1+P2 源自 rename 型 EP 結案未同步；主 session 抽驗 TW_STOCK_REGIME 殘留屬實），證據 durable 化 references/consistency-sweep/（S11）；⑭派工/查證三修補（S12——collaboration-constraints 刪除查證清單補「backlog 卡是否提及或依賴」＋model-routing 補 bridge 派發 echo `[Bridge] family/model/effort`＋口語模型詞經 family 表正規化；當日四事故〔general-purpose×2/muse effort/standup 誤刪〕規則面收口，user 09-09）〕〔驗收：①SM-1~19 場景 rg 可驗②「結案兩步」全 repo 同詞單一時點（含 F1 五消費端）③sync-sources 全綠＋guide 部署同步（deploy_agents）④model-routing 無 agent 轉發殘留、有直跑＋resume 鏈＋驗證式要素＋「lite 預設」條款⑤tool-discipline 通則＋案例在場⑥AIR-48 P4 dogfood 收尾＋定義表 wrapper 條目＋P5 裁決點彙整⑦暫存證據已搬 durable（任務 references/）⑧registry code-reviewer pins＝glm-5.3-flash⑨post-build metadata-sync 段含 rename 反掃條款⑩S12 三條款 rg 在場（collaboration-constraints backlog 卡面＋bridge echo＋口語正規化）〕
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A 線六斷點＋B 線反饋固化＋C 線 AIR-48 剩餘＋S10 review agent lite 化落地：SM-1~17 rg 可驗、結案時點全消費端同步、sync-sources/部署全綠、registry pins 重生成、AIR-48 同弧結案
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【09-09】user 裁定 AIR-48 剩餘併入本弧（S9：P4 dogfood 窗口至 09-10＋P5 裁決點＋memory-audit 統一定義表補 wrapper 誤置條目）——本卡結案時同步結 AIR-48；air-50 branch 已重建快進至 main（開工 checkout 依新 git 慣例）

〔09-09 查證補充〕references/consistency-sweep/02-airules-handoff.md（mosaic 地毯掃描反饋）的 rename 反掃任務＝本卡 S11 段已吸收（desc ⑬／SM-18／驗收⑨），勿重複開卡。狀態核實：S11 已規劃未執行——條款本體尚未寫進 skill（rg 'rename|反掃' skills/post-build/SKILL.md skills/metadata-sync/SKILL.md 零命中，09-09 機械驗證）；f7e60dc commit＝EP 擴 S11 段＋handoff 證據 durable 化，非條款落地。執行序不變（post-build 共檔鏈 S1→S2→S3→S4→S11 收尾）。另註：卡狀態顯示 To Do 但 air-50 branch 與本弧 working tree 改動在場——owning session 確認是否補切 In Progress（起手式①）。

〔開工 handoff 09-09 command center〕排序拍板：51 收→53 收→50 開工（本日主弧，S9 綁 AIR-48 dogfood 窗口 09-10）→54→52。開工起手式：checkout -b air-50 → In Progress → 開工雙 ref → code-reality snapshot --repo <root> --label air-50（勿跳）→ /implement（EP＋殼在本卡 references）。B 線機械段 S6/S8/S12 可派 codex 平行。收尾含 EP 收尾段 S12 三條款＋AIR-48 同弧結案。過渡紀律：本弧結案蒸餾後手動重跑 .agent-tmp/poc_muse_projection.py 刷新 muse copy 投影（AIR-54 過渡形態）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
S1–S5/S9–S12全落地＋三輪post-build收斂（自審F1–F5＋獨審R-F1–R-F4＋delta D-F1–D-F4全驗）＋deploy 3/3＋sync-sources綠（別弧舊殼除外）
<!-- SECTION:FINAL_SUMMARY:END -->
