# AIR-42.1 — Memory 載體分流校準

> **ep_type**: implementation
> **product-type**: docs
> **parent**: ai-analysis/_tasks/09-07-memory-governance/ep.md
> **baseline**: f03d3460c9c157e1dc6079ccdfb7acd680bbe25a
> **depends-on**: AIR-40、AIR-41 正式首跑與觀測限制
> **status**: 已落地（S1 advisory＋S2 修訂；共享 memory 未動——advisory only）

## 實作總覽

目的：讓memory留已確定且影響下次行動的事實/約束，方法進skill、短硬約束進適當範圍rule/AGENTS，任務歷程回Backlog/git。以AIR-40/41真實樣本核對目前分類規則，修少數模糊措辭並交可審核的分流advisory；不靠chars/Read替代內容價值，不增加閘門。

本卡product只有rules/skills文檔與advisory。共享memory修改、全域bundle部署、排程配置不在此卡scope；不在本輪憑「memory可清」擴張授權。原始事實判不準就保留。

## UC盤點與研究

更新命令：memory-audit寫入/收斂、context-management提醒、直接引用者。已有AIR-42.1與母卡，無新增卡/庫Capabilities；SYSTEM-MAP無對應。

文件錨點：`skills/memory-audit/SKILL.md:133`通用原則→rule表述、`:137`按需方法論→skill、`:67`固化指針、`:68`收斂落點；`rules/context-management.md:28`長摘要。消費端 `skills/kanban-board/SKILL.md:57`、`skills/commit/SKILL.md:145`、`skills/execution-plan/SKILL.md:91`、`agents/roles/mem-distill.md:19`（目前保留已退役終態句，須依本次定位判是否歷程）；`skills/instruction-writing/SKILL.md:18`載體決策表。以上為當時rg錨，實作前重定位。

同主題memory：project_memory-desc-loop-posture-pending.md、feedback_memory-failsoft-importance-ordering.md、project_agents-registry-split-design.md；僅候選清單，正式樣本取AIR-40/41，不硬指定一定要遷移這幾份。從池Read僅作本卡advisory，讀取用途需標維護避免污染AIR-41。

docs topology以rg查文本，不需symbol graph；不改code依賴、無projection source假想碼。高風險假設：repo已承載某事實必逐項找到實際來源，否則不刪/不主張可刪；廣主題cluster可能破壞召回，按共用情境判非同前綴即合併。

## Scenario Matrix

| ID | 觸發 | 預期行為 | Checkpoint | UC |
|---|---|---|---|---|
| K1 | 通用多步驟方法 | 進skill，不能因通用就進always-on rule | sample report | 分流 |
| K2 | 專案專用方法 | 可進project skill，不必跨repo才可用 | report | 分流 |
| K3 | 每次適用的短約束 | 放範圍最小的rule/AGENTS | report | 分流 |
| K4 | 固化後全文重複 | 有額外召回價值才留pointer | destination evidence | 分流 |
| K5 | 任務blocker/歷程 | backlog/git；外部已確認限制可留memory | evidence | 分流 |
| K6 | 低Read但重大約束/description足夠 | 保留，不直接cold或刪 | rationale | 分流 |
| K7 | 新writer/未知真值/找不到目的地 | HOLD，標來源hash stale或unknown | snapshot | 分流 |
| K8 | 無候選/全部保留 | 完整判讀仍可验收，不湊遷移數 | advisory | 分流 |
| K9 | 样本太廣 | 分批有限樣本，不全池深審 | sample manifest | 分流 |

## S1：樣本對照與載體決策

Context：實作「載體分流判讀」，依赖兩卡正式report，不能用母POC raw排行榜替代。技術選型：LLM判語義、rg核權威來源、script只算hash與掃描；不建立機械分類器。Invariant Impact：無交易domain invariant，保護知識不因觀測不足而刪除。

修改要點：任務家新增 `routing-advisory.md`。從高寫入、未觀測Read/維護Read、hot或低頻約束保留對照組取有代表性小批；有意選反例，不只挑最肥條目。每項：entry/path/content SHA/觀測時間、召回情境、確定事實、影響行動、當前權威來源、建議載體、保留或移出理由、coverage限制。方法條目是否project-specific不决定能否用skill；rule取最小適用範圍。

驗證：人工逐項讀源，宣稱repo已承載附rg命中path:line；找不到就HOLD。展示原摘要與建議摘要確認適用條件未丟。樣本hash變動就標stale重核。只產建議不改memory，允许全保留；記錄目前未涵蓋的pool/harness/低頻情境。

## S2：修準規則並同步消費端

Context：依賴S1樣本；規範核心已由本對話定案，不以樣本推翻。更新既有memory-audit，不另創skill。語義約束與S1一致：記憶是未來判斷依據，歷程歸任務；來源唯一且投影不重複。

修改要點：

- Q2改為先判知識用途，再決定rule/skill與scope，移除「rule缺就補rule」捷徑。
- 固化條目僅在額外召回情境/個人化理由仍有價值時保留指針；完全覆蓋則可列退出候選，不自行刪。
- 活躍blocker拆任務狀態與已確認外部限制；完成/退役一句話若只記歷程，同樣回卡，不因短就合法。
- cluster合併按同召回情境，保留不同適用條件，不因同prefix就必併。
- context-management保留用途/寫前載skill/索引ownership必要提醒，程序細節留skill；不動其他無關rules。
- `rg '寫入六問|固化|終態|memory-audit|通用原則' rules/ skills/ agents/`，逐項區分定義/投影/歷史；同步直接引用描述及skills索引，若改role則用既有sync_agents流程生成registry，不手改generated。

驗證：docs mode無pseudo code/TDD；`rg`殘留與跨檔語義、/consistency、獨立EP/code-review docs profile。role若未改則不跑生成；rules部署檢查先讀 deploy_agents --help，只用已支持的零寫check，不從worktree部署到其他harness。沒有可用check則用本地暫存輸出验证，正式部署另列待授權。驗證「無新閘門」以git diff限定hooks/與實際變更檔清單，不宣稱系統全域無變。

## 整合與收尾

baseline: f03d3460c9c157e1dc6079ccdfb7acd680bbe25a

影響instruction檔依instruction-writing；skills/CLAUDE索引同步。純docs跳過mypy/pytest/audit-test，報告殼沿用template需DOM測試。更新AIR-42.1結果與references，母家活躍時子目錄不另搬，母卡最後統一歸檔。共享memory只列owner處置提案，不留「已遷移」假完成；本卡可在advisory+規範修訂完成後Done，實際池遷移若用戶選擇再明確追蹤。母卡驗收也不要求一定遷移。

## EP Review Findings

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| 1 | 🟡 建議 | S2 | `rg '寫入六問\|固化\|終態\|...'` 驗證命令含中文 alternation，引號包裹已寫明；施工注意 shell 轉義 | 照 EP 引號寫法執行 | implemented |
| 2 | ℹ️ 提醒 | S1 | 讀池作 advisory 會污染 AIR-41 觀測（讀取用途標維護）已寫明 | 施工時每次讀池附用途註記 | implemented |

審查結論：有條件執行（F1–F5 通過；docs-mode 無 pseudo 允許；須在 AIR-40/41 首跑證據後開工）。審查者：muse-code（跨家族獨立審查），2026-09-07。

## Build 後 dual review 與修正輪（2026-09-07）

S1（`routing-advisory.md` 10 條四組）＋S2（memory-audit 四處＋rule 瘦身）落地後 dual review（muse 工單 `review-workorder-s1s2.md` job-mtr55yow 通過 3 Suggestion；GLM fresh-eyes 有條件通過 2 🟡＋6 🟢）：judge 採納 F1（#4 分類翻轉——條目 :18 F7 裁決「不預寫條件式文案」是行動增量、repo 零承載，退出候選→指針保留）、F2（#7 權威欄修正——機械檢查在 /sync-sources，僅收尾放置無承載）、F3（rules/AGENTS.md 四問→六問 stale）、F4/F5/F6/F7（數字/錨點/merged_from 錨精修）、F8（Q1 補「不因短就合法」明文）；muse F2（frontmatter 摘要滯後）記觀察不動。修正輪機械複驗：舊形態零殘留、新形態全在場。S1 抽樣自身實錄「流量vs存量 join 誤差」（top_entries 與 inventory 不同集合，absent≠zero-read）已記入 advisory 觀測誤差段。
