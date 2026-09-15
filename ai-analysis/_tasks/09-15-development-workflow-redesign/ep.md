# 開發流程重設計：依風險執行、依證據接續

> **ep_type**: implementation
> **mode**: docs（行為控制面；完整 review 與 instruction behavior 驗證仍必須）
> **baseline**: 0bbddb1ca69b8d574b6f5ef20cecaba14050a691
> **Marshal 實作基線**: b4a301992356e8960892894f392e91346a4d492f（user 指定；git show 已核對 catalog/presets/work-unit doctrine 落地）
> **狀態**: 四段計畫與 Marshal overhead 增補已完成審查／裁決／修訂複核，可交其他 LLM 實作。此 session 只交計畫；HTML 互動／視覺驗證依 user 指示本輪延後。runtime／成本效果尚待實作驗證。
> **研究與接續**: [reports checkpoint](../../reports/2026-09-15-development-workflow-redesign-checkpoint.md)
> **任務簡報**: [index.html](index.html)

## 進度與接續入口

- [x] 讀取當日五份報告及前日兩份 Marshal 報告；核對現行 review／compact／metadata 接線。
- [x] 已完成 AIR-91 與 AIR-96 分界（規劃期 AIR-96 在途，其後已結案）；找到 AIR-60 恢復鏈既有承諾。
- [x] 目標流程、UC、Scenario Matrix、四個自足段落、遷移與驗證策略落盤。
- [x] 獨立 reviewer 的 F1–F5 維度 findings 回收、Arbiter 裁決與必要修訂（六項）。
- [x] 修訂後 reviewer followup：六項 resolved，無新增 Important。
- [x] Marshal overhead 增補：契約相容性調查→骨架→具體 work-unit 編排／情境→增補審查及三項漏洞修訂複核。
- HTML 互動／視覺驗證本輪延後（user 明示）；不阻擋計畫交付，不宣稱已驗。
- [x] 主 session ep-review（N1–N8＋S1）staged → 外部 Muse 審查收回（`references/external-review-muse.json`，job `job-mu2kr2hs-6k82uh`）→ 裁定全採納並回寫（N1/N4 依外部審查修正版；無新增 Important）。
- [x] user 接受新預設，明示進入 implement（09-15 深夜 marshal 任務單；owner 卡 AIR-101、branch air-101、baseline 4fc5caa）。
- [x] S1 落地（09-16）：review-engine profile 驅動重寫＋workflow-review-pattern identity 三欄＋no-candidate ledger 點 8；承接清單 `.agent-tmp/air-101/s1-consumer-manifest.md`（S2 十項/S4 四檔/pointer-only 六檔）。
- [x] S2 落地（09-16）：S2a 五檔（execution-plan/ep-review/implement/code-review/audit-test 接線）＋S2b 七檔（post-build 三閘快道/agent-review-cycle profile 表/work-order 批次 envelope/judge coverage 核對/followup status 單一寫入者/agent-workflow cap 語義/agents AGENTS 掛點）。
- [x] S3 落地（09-16）：`_common/task-recovery.md` 新檔＋compact-prep/at（Phase 0 先結算）/handoff/autonomous-execution/rules context-management 接線（bundle +104B）；AIR-60 段① rehydration 單一源骨幹隨此交付。
- [x] S4 落地（09-16）：illustrate-html-mode 圖觸發 task 型態預設＋deep-work S1/S2 接線＋metadata-sync review identity 復用邊界＋skills/CLAUDE 對帳＋blueprint workflow 導航＋post-build 模式 B 舊錨歸零。
- [ ] S1–S4 驗收：static 全綠（各段 rg 閘）；外部 review 鏈（codex+muse→judge）進行中；behavior 情境（SM-01..24 抽樣）與真實 pilot 未跑——按 EP「未做不補成完成」將分列 Built／行為驗證／pilot／部署，部署另取 user 授權。

下一個動作：所有 review 工作已收回，沒有待回收 job。實作接手者在 user 指示 implement 後讀本 EP Review 區段及 checkpoint 最末狀態，先對齊 AIR-60 owner／AC，再核對 HEAD／dirty 與治理檔，從 S1 起。本 EP 不修改 AIR-96 定稿的 model-routing/catalog/generator。

## 實作總覽

### User Story

作為 solo developer，我希望用既有開發命令推進工作，讓 AI 按風險完成必要的研究、驗證與獨立審查，減少重複載入、派工與結算；我只需讀一份簡短的方向／成果說明，就能理解重要行為和設計取捨。usage 或 context 中斷時，工作能從已保存的證據接續，不重做、不誤報完成。

### 成功標準

1. 同一任務在 execution-plan／implement／post-build 的 review 配置由同一風險規則推導；少派 reviewer 不等於丟失意圖、正確性或結構檢查。
2. 已完成的審查只在可核對身份與覆蓋時復用；新增內容、不同 profile 與跨段整合仍驗證。
3. compact 前先保住任務狀態；恢復後查實物及未收回工作，再採取下一個動作。沒有 hook 也能執行。
4. 方向與成果各有簡短 viewport；圖與 tour 有明確觸發，不強制每弧產新圖。必要的人類判斷材料保留。
5. 必要防線不退化：authority、accepted EP、Writer/Reviewer 分離、critical invariant、實跑驗證、finding closure、outward consent。
6. 成本改善以相同場景的實際動作與可取得 usage 比較；無數據不宣稱節省比例，無 runtime 不宣稱行為已驗收。

### 範圍與不做項目

產品僅既有 `.md` workflow/rule/common-template 的修改，加一份共用恢復協定文件。無新 Marshal agent、workflow engine、router、CLI、hook、資料庫或自動 compact。AIR-91 的 ModelCatalog／DispatchBinding／ExecutionPreset／WorkUnitContract 契約保持既有 ownership；AIR-96 已結案（五項全落地，含 muse bundle 瘦身至 30,088B／81.6%），無遺留 dirty 待協調——本弧消費其定稿、不重開。

不改 commit/deploy 授權、memory pool 寫入治理、board id/branch 協定、排程、WT 基建、CR 本體、tour generator。恢復協定記錄授權的來源與範圍，引用目前 governing consent；不吸收 AIR-60「歷史授權全部失效」的 blanket 句，也不新增 blanket 延期。該項需在其 owner 弧依現行上位規範另行處理。

本次 product 為 docs mode；任務家內可重播情境、verifier、原始輸出僅 evidence artifact，不可被 production consumer 引用。若發現必須修改 `.py`／`.toml`／`.sh` 或生成器才能成立，先更新範圍與驗證策略，不能用 docs mode 偷渡 executable 改動。

### 已有約束與本次提案

已存在：Marshal 是編排責任而非角色實例；Reviewer 只產 findings，Arbiter 裁決；model 選擇由 resolver 決定；compact 時機由 user 決定；資料與 instruction 的受眾分開。

本次待接受提案：review 不再預設填滿並發；一般段落以實跑驗證＋持久證據為主、只在邊界觸發段級 review；最後獨立 review 必保留；圖按需；compact-prep 的 memory 整理移出救援必要路徑。上述預設須經本 EP 審查及 user 的 implement 指令才改變現行行為。

### 相對複雜度與排序

整體高風險控制面變更，實作複雜度中高。S1 review 規則最先；S2 把規則接到入口；S3 恢復協定可在 S1 定稿後並行設計（設計可並行；S3 實作待 S2「段落結果寫 EP 進度」欄位定稿），但寫同檔時串行；S4 統一交付與跨入口驗收。四段屬同一流程改造、共享已定 ownership，不另拆 blueprint 或新命令體系。

## 段落 0：全域研究

### 證據與限制

本研究是文件拓樸／控制面分析，工具為 rg、分段 Read、git status／HEAD。未對 application callable 作 negative 宣稱，CR/LSP 符號圖及 projection code N/A；不以文件接線宣稱 harness runtime 已運作。外部 compact 能力僅引用報告的 source 分析，不升格成目前桌面的事實。

| 材料／現行錨點 | 觀察 | 設計後果 |
|---|---|---|
| `ai-analysis/reports/2026-09-15-dev-flow-current-practices-inventory.md:3` | 以 AIR-91 Done 為基線，目標含人追上實作 | 不重做 routing；保留人類 viewport |
| `ai-analysis/reports/2026-09-15-dev-flow-overhead-inventory.md:8` | observed/protection/candidate 分類，未給刪除結論 | 每項減量附替代防線與改判條件 |
| `skills/review-engine/SKILL.md:141` | 共通 review 預設、固定 max 與多視角 | 改此源，消費端只取結果 |
| `skills/implement/SKILL.md:192` | Agent Review 固定多 perspective | S2 改成邊界觸發，保留 lens 覆蓋 |
| `skills/post-build/SKILL.md:76–80` | 已有身份去重＋缺鍵全審 | 補 identity producer，不再建第二去重機制 |
| `skills/_common/workflow-review-pattern.md:121` | identity 只有 baseline/reviewed/uncommitted/writer | 補 scope/profile／coverage 關聯，服務既有去重 |
| `skills/compact-prep/SKILL.md:15` | 全 session preserve-list、memory 檢查、恢復 | 重用現有載體，先落盤再可選整理 |
| `skills/metadata-sync/SKILL.md:12` | build／收斂／standalone 分工已存在 | 保留 Built/Verified，減少同 revision 重算 |
| `skills/_common/illustrate-html-mode.md:76` | 同一殼生命週期；持久 tour 已 ask-once | 不重提 tour 去強制化；僅調整強制產圖 |
| `ai-analysis/blueprint/workflow.md:28` | 人類八站導引權威，不取代 skills | 修改掛點時同步導引，保留兩受眾 |

補充來源：兩份前日 Marshal 報告、controlled-compact-strategy、memory-mechanism-analysis、codex-compact-architecture；全部按歷史證據使用。AIR-91 done EP 進度節記錄測試、behavior experiment 與部署，本次沒有重跑其驗收。STATE 是舊觀察，不能推翻 done 位置或當前卡面。

### 可重用機制與 ownership

| 責任 | 定義 owner | 消費者／改動 |
|---|---|---|
| review 風險、獨立性、配置 | review-engine | ep-review、code-review、audit-test、EP/implement adapters |
| findings/identity／closure 結構 | `_common/workflow-review-pattern.md` | `_common/agent-review-cycle.md`、judge/followup、post-build |
| phase 的 WorkUnitContract | 各 owning workflow | 引 model-routing resolver；不在共用 protocol 重列 model |
| 恢復順序 | 擬新增 `_common/task-recovery.md` | compact-prep、at、handoff、autonomous-execution、context-management |
| 當前工作實物狀態 | git＋EP 進度＋active findings/job ledger | recovery 讀取，STATE 只補轉向理由 |
| finalization 邏輯 | metadata-sync | implement/post-build/standalone 引用 |
| 殼格式與生命週期 | illustrate-html-mode＋既有 HTML template | EP 與 final brief，不另建 UI |

### 風險假設與對策

- H1：合併 reviewer 執行會降低獨立 lens 價值。高風險；S1 只讓一般變更用單獨 context，邊界變更保留分離視角；S4 用 seeded defects＋真實 pilot 比較，不能把「少 finding」當成功。
- H2：去重身份不足會把新變更當已驗。高風險；S2 完整 scope/content/profile 覆蓋＋缺鍵全審；未提交新檔內容改動是必測反例。
- H3：落盤／restore 增加另一套狀態。中風險；S3 schema 是現有檔案中的欄位，不增 registry；active pointer 就是既有 EP 進度節的 checkpoint 連結（無 EP 時用既有 journal／user 指定 report），不另建索引檔；原始證據由既有 owner 持有。
- H4：減少图會讓人看不懂。中風險；S4 保留具體 before/after、風險與回源；人讀 pilot 後能回答「改了什麼／為什麼／哪些未驗」，不能只以產物更短判成功。
- H5：新的降頻條款在長 context 被誤套成免驗。高風險；以「quota 快沒了＋進度已近完成＋聲稱前輪審過」組合壓力驗證；安全分支不通不能部署。
- 無致命外部 API 假設：不依賴尚未驗證的 compact hooks 或 runtime router。behavior 可行性仍待 S4 實驗。

## UC 盤點

### Backlog 與相關弧

- AIR-91：既有完成能力，本 EP 消費，無重開需求。
- AIR-96：已結案（Done）——generator／effort／inherit／bundle／bridge 五項已落地；本弧不重開、消費其定稿。
- AIR-60：To Do，承諾 rehydration 單一源、review closure、segment receipt；S2/S3 對應內容須在實作開工前把其 Plan/AC 與本 EP 對齊，不能雙 writer 並做。
- DRAFT-6：family×任務 fit 的研究，僅相關，不以本 EP 取代家族評估。
- AIR-72／AIR-73：WT、board control 與殼 codegen 的既有規劃，均不承接。
- 本輪是元專案 docs-mode 設計，依 execution-plan docs-mode 例外不自動建立能力卡或追蹤卡、不 commit backlog；現有 AIR-60 保留原狀。要進實作時先確定 owner 卡承接範圍並履行 kanban 起手式，禁止先寫後補歸屬。

掃描範圍：root AGENTS、skills/CLAUDE 工作流索引、相關 workflow skills、backlog/tasks 與 drafts 主題字串。無 library Capabilities；改以受影響命令作能力索引。root SYSTEM-MAP 未納入現有材料，元專案跳過；人類主鏈導航同步 `ai-analysis/blueprint/workflow.md`。

同主題 memory 條目（唯讀盤點，不授權寫池）：`feedback_compact-user-judgment-memory-continuity`（穩定 user 偏好，已讀）、`feedback_compact-output-context-not-transcript`（preserve-list 原則）、`project_role-vocabulary-terminal`（AIR-91 終態，索引標兩尾巴未裁）、`feedback_session-close-handoff-review-companion`（接續陪審偏好）。後三者本次僅索引定位，結案如需蒸餾由有權 owner 核對全文；Codex 不直接寫主體。

| UC | 類型 | 消費者行為／入口 |
|---|---|---|
| UC-R 依風險安排獨立審查 | 更新 | EP/code review 自動選必要配置，無需 user 手選 model |
| UC-E 復用有身份的證據 | 更新 | implement→post-build／跨 session 不重審同內容，不漏 delta |
| UC-C 中斷後安全接續 | 更新 AIR-60 | compact-prep／at／handoff 共用恢復次序，先核對再做 |
| UC-V 輕量且可信的方向與成果視圖 | 更新 | 同一殼前後更新，按需深挖；Built 不冒充 Verified |

## 目標流程

### Marshal 編排骨架

每個階段先決定「還缺什麼成果／證據」，再形成 work unit，最後由既有 resolver 選 candidate。Role 不直接決定 process 數量；同時不得用批次化混合 authority 或獨立性。整體保留四段：S1 定 review 需求與證據身份；S2 決定成果邊界、派工與收回；S3 保存與恢復；S4 驗收成本／品質並交付。相容工單合併與 read-set 復用細節由本輪增補調查核定，不新增 runtime。

此次融合多模型不預設每個家族都參加每弧；每增加一腿須能指出未覆蓋問題、資格／能力需求或必需獨立性。常規零 findings 分支沿用現行 post-build 直進 docs，不額外跑空 judge／followup；輸出缺失或執行失敗不能當零 findings。

```text
定位任務與當前狀態
  → 需求／規劃（simple 保留既有免 EP 路徑）
  → 計畫獨立 review＋必要裁決 → 方向 brief → accepted EP
  → 實作 ↔ scoped 實跑驗證
       遇公開邊界／新 invariant／高風險或階段交接 → 段級 review
       普通段收斂 → 寫進度與證據指針
  → post-build：身份核對 → 補尚未覆蓋 review／跨段整合
  → findings 裁決 → 已採納修正 → followup 驗證
  → metadata＋成果 brief（同 revision 結算一次）
  → user commit consent

任何階段中斷：寫 checkpoint → user 選 compact／等待／handoff
恢復：核對任務 → 實物與 job → active findings → 決策理由 → 下一動
```

review 正常路徑從一個獨立 reviewer 開始，必讀要求、正確性、validation profile；fresh-first 後再比對需求，這只保證 writer context 分離，不宣稱等同多個 context。保護面／跨邊界仍用獨立 fresh＋intent／專項腿。並發容量是上限，不是必須派滿的數量。

## Scenario Matrix

| ID | 情境／觸發 | 可觀察預期 | Checkpoint | UC |
|---|---|---|---|---|
| SM-01 | 單檔 typo、無規範語義變更 | 保留現行快道，引用與 consistency；不生成 EP/圖/多 reviewer | 變更與檢查結果 | R,V |
| SM-02 | 一般跨檔 feature、有既有保護測試 | 計畫獨立 review；段落實跑；弧末獨立 review | EP 段結果／review identity | R,E |
| SM-03 | 小 diff 改 money/public boundary/MUST→SHOULD | 升邊界配置；invariant／架構／控制面 behavior 依觸發驗 | 風險理由與相應證據 | R |
| SM-04 | 前輪相同 scope/content/profile 已審 | 引用已審證據，只補 delta 與跨段整合；不抄全量 findings | identity／coverage | E |
| SM-05 | HEAD 未變但 untracked 內容變 | identity 不匹配，針對新內容補 review；不可跳審 | content hashes | E |
| SM-06 | 缺 profile/scope／舊證據檔失聯 | 顯性失效，對所需範圍完整 review | 失效理由 | E |
| SM-07 | 審後修正波及新 consumer／新 invariant | 重新分級＋delta review，未閉合不得 Verified | 新 finding／delta | R,E |
| SM-08 | quota 將盡，正在 debug 半程 | 先保存已知／未知、失敗原文、未完成修改，無 completed 宣稱 | 現有 EP/checkpoint | C |
| SM-09 | compact 後 STATE 與 git/EP 不同 | 完成度採實物；保留 STATE 理由；漂移未解先停相關 apply | 恢復核對結果 | C |
| SM-10 | 背景 worker 未終局，wait timeout | 查既有 job／liveness；重掛收法，禁止重派同一工作 | jobId/owner/收法 | C |
| SM-11 | 無 compact hook／transcript 不可讀 | 用目前可見全任務結構＋實物寫檔；標明未恢復範圍 | 覆蓋限制 | C |
| SM-12 | reviewer conflicts／needs-confirmation | 交 Arbiter；authority 不因共識升級；保留未決，不發 accepted/Verified | finding ledger | R,E |
| SM-13 | resolver 無合格可用 candidate | pending 入既有帳本，記 owner／retry 條件，完成報告可見；不以主模型裸自審取代 | DispatchTrace／ledger | R,C |
| SM-14 | user 只要了解最終行為 | 殼顯示前後例、取捨、證據與缺口；圖無新增價值可省 | 同一殼／source SHA | V |
| SM-15 | 只剩 metadata／新 actor 無 memory 寫權 | 必要導航與結算照做；memory 工作交接、不得假報蒸餾 | owner／待辦 | C,V |
| SM-16 | user 明示不跑 post-build，弧末 review 缺席 | fallback 先補獨立 review；若 user 同時明示停審，只交 Built／🟡，禁 ✅／Done／歸檔 | closure identity／pending ledger | E,V |
| SM-17 | 漫長報告／多輪審查 | path＋精簡差異工單，保留全量 source；不重載整弧 transcript | evidence pointer | R,C |
| SM-18 | 政策翻轉後舊 session 繼續 | 依既有 freshness 要求重載／fresh context 驗收；舊 context 不作新政策證明 | source hashes | R,C |
| SM-19 | 整合器段、新簽名／注入點或 UC 數 >6 | 保留 adapter 對應的 adversarial、architecture＋consumer-perspective、UC-split；不得被普通 base 吞掉 | 觸發信號／review coverage | R,E |
| SM-20 | 同一批同權限、共同 read-set 的機械工作 | 單工單可多成果；每項 scope/結果獨立，缺一不報全完成 | unit→artifact/result 對照 | E |
| SM-21 | 要合併 writer/reviewer、reviewer/arbiter、必要獨立 lens | 拆開；單 candidate 合格不能取代 context／provider 獨立性 | 不合併理由／contract | R |
| SM-22 | 新 worker 沒讀契約或 quota snapshot stale | 讀可達最小契約、形成當次 snapshot；1308 窗內不重選，不臆造 resume／TTL | read-set／DispatchTrace | C,E |
| SM-23 | reviewer 出錯、空輸出或截斷 | 不當零 findings；保留 pending，不能跳 judge 後報驗收成功 | terminal/output completeness | R,E |
| SM-24 | 原 Reviewer followup 修正結果 | 只產 findings／證據；主鏈編排者核對並寫 status，不新增弧級獨立覆蓋；新爭議交 Arbiter | 原 finding→修訂→證據 | R,E |

## S1：review 風險判準與證據身份

### Context

實作 UC-R/UC-E 的共通契約。使用者要省重複工，不降低正確性與獨立性；無另附 spec，Always＝authority/consent/invariant，Ask First＝新預設接受與 deploy，Never＝同寫同審冒充獨立。依賴 AIR-91 doctrine 已在場；不改模型 catalog。共用假設：S2/4 消費同一風險結果與 identity。

錨點：定義 `skills/review-engine/SKILL.md:141` → 消費 `skills/implement/SKILL.md:195`、`skills/ep-review/SKILL.md:28`；identity 定義 `skills/_common/workflow-review-pattern.md:121` → 消費 `skills/post-build/SKILL.md:76–80`。實作前 rg 重定位，行號只作起點。

### 修改要點

- review-engine 用可觀察變更語義決定 profile、獨立性與必需視角；不再按 effort 大小選更多審查儀式。既有 provider 並發 cap 繼續由 model-routing 擁有。
- 一般變更：一個獨立 context，順序為 source/diff→正確性與驗證→需求對照；同一 reviewer 必覆蓋 profile 各軸。這不是 fresh/primed 雙 context 等價品。
- 邊界變更：public API、跨 context invariant、money/risk/security、控制面 authority/gate 改動，保留分離的 fresh 與 intent 視角，加必要專項；資格仍由各 workflow WorkUnitContract 升級。條件不明採更保護分支。
- explicit user review scope 或 hard independence 不能被較省配置覆蓋。缺 candidate 顯性 pending。
- 本次減少 base，不刪現行 adaptive extras：整合器／外部整合→adversarial，新簽名／注入點→architecture＋consumer-perspective，UC 數 >6→UC-split。沿用既有 adapter 信號與 owner，S2 映射須逐項承接；前兩者觸發段級 review，UC-split 保留適用 scope 的分拆審查。
- no-candidate 由該 workflow 編排者在既有帳本記 open 阻擋項（規劃期本 EP Review 節；實作期 `.review/<branch>.md`），含 scope/profile、原因、owner、DispatchTrace、下次查 availability 的條件。完成報告與 post-build triage 必列出；有已授權排程才排 re-arm，否則保留明確接續動作，不暗建 automation。再次 dispatch 前先查有無活 job，不把無候選和 worker timeout 混同。
- `_common/workflow-review-pattern.md` 的既有 header 補 `scope`（包含／排除檔案與 UC/invariant）、`review_profile`（profile identifier＋definition content identity）、`coverage`（完成／未驗及 evidence ref）。不另建 JSON registry、不更名 finding status。
- 可復用判準：同任務基線、相同實物內容（tracked/untracked）、scope 覆蓋目前要求、profile 定義與所需獨立性相容、證據可讀且未失效。缺一就不能宣稱 complete coverage。複用 findings 不等於複用測試；環境/config/input 改變時驗證證據另行失效。
- 去重只合併同位置同一 claim；矛盾 findings 並列交 Arbiter，不以投票或「先回者」裁決。
- 先選風險 profile／必要 lens，再安排 worker。批次化不能重寫 S1 的配置：高風險 fresh/intent、專項與 required provider-family independence 保持分離；ordinary 單 reviewer 是本 EP 明示且需實驗驗收的新預設，不可推成所有同 Role 可合併。回復時恢復舊 profile，不以 quota 臨場降級。

### Invariant Impact

控制面核心 invariant：Reviewer≠Arbiter、缺證據≠PASS、revision/profile 改變不能復用舊結論。非交易 domain 計算，無 money path 實作；其觸發案例仍列風險測試。

### 驗證與完成條件

對 SM-01/03/05/06/12/13 建 control/treatment behavior 情境，觀察實際派工選擇／拒絕跳審，而非複述詞表。微測 identity 缺欄、untracked 改動、profile 變更、證據失聯；任何一項假命中阻擋 S2。以 rg 列出 `max-agents`、`3-perspective`、`dual-context`、`header identity` 的所有 current consumers，按 manifest 分段承接（S2 接主鏈檔；`skills/CLAUDE.md`、`skills/deep-work/SKILL.md` 等 S4 檔由 S4 接；pointer-only 命中記免改），不得有無主 consumer；S2 結段前出承接清單（file→segment），S4 開工核對；歷史 reports/done 不改。成功＝共通源可推導一致輸出，且沒有新增 model/tier 真值副本。

## S2：主鏈接線與段級／弧級 review 收斂

### Context

更新 UC-R/UC-E；依賴 S1 定稿。需求邊界同本段自足陳述：只在 scope 已可判且 accepted EP 成立後 apply；任何新決策轉 Planner/Arbiter，不以 execution 腿補設計。S1/S2 共享 scope/profile identity；S3 恢復會讀本段產物。

複用：`skills/implement/SKILL.md:56` accepted-EP predicate、`:192` review cycle；`skills/post-build/SKILL.md:76–80` reuse；`skills/_common/agent-review-cycle.md` perspectives；`skills/execution-plan/SKILL.md` EP Review Cycle；`skills/ep-review/SKILL.md` F1–F5；`skills/code-review/SKILL.md` mode B；`agents/AGENTS.md` execution contract。

### 修改要點

- execution-plan/ep-review 保留所有 F1–F5 維度，引用 S1 的配置；刪除自行以主模型/effort 重建 agent 數量的重複判準。EP Review 完成才產 accepted eligibility；不刪獨立計畫 review。
- implement 普通中間段做 scoped 實跑、invariant assertions、必要 test audit、寫段落結果；當公開邊界／跨 context／高保護面／獨立交接／user 要求時啟動段級 review。全弧仍需獨立 review；最後段已覆蓋全弧者可依身份復用。
- S1 的整合器／新簽名／注入點 extras 與 UC-split 映射一併接入，不能只接 base。implement 階段 6 fallback 必先核對弧級 review coverage；缺席則補獨立 review＋裁決＋修正驗證再結案。若 user 要求停止審查，尊重停工但只交 Built／🟡，列 pending，不發 ✅、不移 Done、不歸檔 EP；缺帳本不能以 git／卡狀態推導為已驗。
- 段落結果寫 EP 進度，不新增每段 report：產物路徑／內容身份、實跑命令及結果指針、未驗與下一步、review 尚需/已覆蓋。原始長輸出留 evidence 檔，不灌回 prompt。
- code-review/agent-review-cycle 消費 S1 風險結果；Correctness lens 不消失。audit-test 保留 test 特有 mandate；profile 覆蓋已包含相同 test 審核時引用相同證據，scope 新增則補，不另固定全量重跑。
- post-build 首先核對前段 identity，保留已存在 fallback 全審與跨段整合要求；任何修正產生新 scope 則重分級。需確認項影響 scope/AC/gate 時阻擋 accepted/Verified，純建議可保留顯性未決但不偽裝全清。
- agents/AGENTS、agent-workflow 的 lifecycle 表只留指向 owning workflow 的掛點；skills/CLAUDE 索引同步。judge 的 disposition authority 與 status 值域維持；judge/followup 均同步 identity 讀取指針（judge 裁決前核對 `coverage` 未驗項，見 SM-12）；followup 依下節消除雙寫者措辭。
- 明確修改 `skills/post-build/SKILL.md:88` 零 findings 快道：先核對 terminal=completed、輸出完整且包含明確 review 結果／scope coverage，再判 findings 為空。timeout／非零失敗／輸出空白／截斷／缺 coverage 一律留 pending，不能直進成功結算。只靠 exit 0 不足；無 job 的合法執行面需等價完成及輸出證據，不臆造 job。
- 每次 dispatch 延用 WorkUnitContract/resolver，已確認 definition 未變時引用已載材料；availability 在 dispatch 當下查，不能用省讀為由沿用 stale quota。

### Marshal 工單粒度與派工契約

本節是 workflow adapter 編排，不改 model-routing schema/catalog/presets。共用寫法放既有 `skills/_common/work-order.md`，消費端由 agent-workflow、EP/implement/post-build 指向；不新增 batch engine、cache 或模板檔。一個工單可列多個既有 work-unit rows 的引用，但不能 union 成較寬 authority 的新 row。

| 形態 | 本弧決策 | 責任與輸出 |
|---|---|---|
| 合格主 session 的規劃／編排／裁決 | 沿用現況，各階段明示 authority，不為角色清單另開 worker | Planner 出計畫，Arbiter 出 disposition；主 session 不合格仍依 resolver 外派，不能宣稱永遠主做 |
| 同 authority、相容 surface/qualification、同 owning scope 的機械查證或實作子成果 | 允許單次 dispatch 批次，所有 unit 必須各自滿足既有 resolver；共用 read-set；不含多個 review units | 工單列 unit 引用、scope/fence、依賴順序、各成果路徑／完成條件，收回逐項 PASS/FAIL/未做 |
| Reviewer 讀 source＋驗 finding 錨點 | 屬同一 review work unit；不為內建查證重開 Verifier | evidence 隨 findings，無 final disposition/apply；既有獨立 verifier 要求不被此取代 |
| 不同 authority／Writer↔Reviewer／Reviewer↔Arbiter | 本弧不做跨 authority worker 合併；分開明示 work unit | 防 role switch 擴權與自己裁自己；模型可相同但不因此算 context/provider 獨立 |
| required 獨立 lens／跨 provider 第二意見 | 分開符合 contract 的 context／provider；不足則按既有降級／pending 路徑 | family transport 不冒充 provider 獨立性，soft-visible 不寫成 hard 已滿足 |
| 原 Reviewer followup | 用 Reviewer/findings、review_findings qualification；judgment floor 繼承原保護面要求 | 核對原 finding 的修正與反例，回覆 findings／證據；主鏈編排者核對後寫 verified/closed，爭議再交 Arbiter，不作新獨立弧級 review |

批次 candidate 必須通過每一 unit 的資格／capability／effort／independence 要求；沒有共同合格 candidate 即拆分或 no-candidate，不因合併任意升級整批。共享 carrier 的前提是一次派發可承載此工單；不依賴 session resume 或中途換 role 的工具能力。每 unit 的 DispatchPlan/Trace 可對應同一 jobId，但保留 scope 與結果；dispatcher 仍須按現行欄位產出 preview，不新造 wire 欄位。

一批內互相依賴的工作順序執行；無依賴且寫入 fence 不重疊才可平行。部分失敗先核對實物與已完成證據，只重派未完成且前置仍成立的部分；上游成果已改則下游證據失效重驗。不能把同 worker 結束或 exit 0 當所有 unit 完成。

多個 review units 不共 worker context，即使 authority 都是 findings；讀取錨點污染不受寫入 fence 保護。每個 review unit 按 S1 profile 建獨立 context/read-set。單一弧級 review 在同 scope 內審多檔仍是一個 unit；不得把彼此獨立的任務改名為同一 unit 規避。驗證加入 A review 已讀 A 意圖後續審 B 的反例，預期仍派 fresh context，不只看 scope 欄相同。

穩定材料只在同 context 且確認未變時引用已載內容；新 worker 的工單仍附可達 read-set、必要契約和禁止再委派。每次實際 dispatch 都形成當次 AvailabilitySnapshot；一次 batch 可共享當次來源，但逐 unit 留 trace。跨次不發明 TTL，不用已知 retryable-at 當 availability=true；它只限制何時可重試。unknown/stale 依現行 fail-closed 處理。

`followup-review/SKILL.md` 補明上述 WorkUnitContract row 與「不計新弧級 coverage」；點名修改現行逐項驗收／驗收後更新帳本段（約 :43–51）及 muse 續接的 :61，統一為 followup 只回 findings／證據、主鏈編排者為 status 唯一寫入者。verified/closed 是進度 status，不是採納／拒絕 disposition；僅有可核對驗證結果且原採納／拒絕決策未受挑戰時更新，新增／矛盾 findings 交 Arbiter 重新裁決後再更新，不能由主鏈自推「修好了」。既有 status 值域不變，`workflow-review-pattern`、implement/post-build 同步引用這一寫入責任。

carrier resume 僅在工具已證實且有成本收益時使用；無支援就 fresh context＋原 findings/修訂 read-set，不假設 resume 更便宜。

### Invariant Impact

accepted EP 才 apply；未被 review 的 ordinary 段不能把 Built 當 Verified；scope/profile/content 未覆蓋不能結案。驗證對應 SM-02/04/07/12/16。

### 驗證與完成條件

用同一 fixture 分別從 execution-plan、standalone ep-review、implement、post-build、code-review 進入；觀察是否套同一風險配置、相同 scope identity 與不同 consumer mandates。測普通多段弧、段級高風險、僅 untracked 變更、已有完備 review、缺鍵 legacy 帳本；另測 SM-16 零 review fallback、SM-19 三種 extras，以及 no-candidate 到恢復可用的 pending 收斂。完整 current-consumer rg 逐檔列 disposition，不以零 keyword 自證無語義殘留。成功＝無條件派滿／固定重審退出活跃入口，必要獨立性與跨段 coverage 未丟。

增補 SM-20–24：同權限三個機械成果共享工單，其中第二項失敗，驗收第一項不被盲重做、第三項按依賴判是否有效；跨 authority／缺資格／required lens 合併被拒；空輸出不得進零 findings 快道；新 worker 實際取得最小契約；1308 retryable-at 前不重選。觀察 action／artifact，不以讓 subject 複述規則當 behavior PASS。

## S3：checkpoint-first 與恢復驗證

補充交接：[compact 建議方向](../../reports/2026-09-15-compact-direction-handoff.md)。user 在 usage 5% 時要求完整保存；其新增救援優先序／案例／研究候選未獨立審查，不擴張本段已審契約。接手若採入新的行為／AC，先做 scoped review。

背景報告的 compact 機制改善選項（codex-compact-architecture §10：代際鏈、摘要本體存檔、pre/post 標定、換模型紀律；memory-mechanism-analysis §8：verification 輕量版、semantic 指引、ZCode tail 補償、transcript 錨、memory 半自動化）未納入本 EP——本弧止於 checkpoint-first＋恢復驗證；機制改善留待 compact 專弧另立範圍，非遺漏。

### Context

更新 UC-C，承接 AIR-60 恢復順序部分；不改其 consent、WT 或其他未承接工作。依賴 S2 的段落證據與 S1 identity。無另附 spec；compact 操作／時機由 user，AI 可依已授權任務持續 checkpoint。未定案推論可存 checkpoint，不能寫作 memory fact。

錨點：定義 `rules/context-management.md:11` 恢復 read-set → `skills/compact-prep/SKILL.md:15`、`skills/at/SKILL.md:36`、`skills/handoff/SKILL.md:31`；`skills/_common/state-md-write.md:13` 指明 STATE 非 recovery authority。另讀 autonomous-execution 的 Session Recovery，沿用檔案實物核對。

### 修改要點

- 新增 `_common/task-recovery.md` 只持有跨入口恢復順序／checkpoint 必要欄位；它是共用片段，不是新 skill、狀態檔或自動化引擎。
- 優先更新現有 EP 進度＋必要 evidence；無 EP 用現有 journal；user 指定 report 則使用該 report。compact-context 保留作交接包，只引用 durable owner，需逐字保存的錯誤/findings 原文例外。
- active pointer 直接放既有 EP 進度節（無 EP 則既有 journal／指定 report），不新增 active-pointer 檔、registry 或跨任務索引。驗收比對含 ignored 路徑的 scoped 檔案清單，確認除 manifest 共用定義／測試 evidence 外沒有新增狀態庫；不能只靠 git status 漏掉 ignored 新檔。
- 欄位：目標與成功條件、現行階段、scope/cwd/baseline＋本弧 dirty、已決策理由及排除方案、已驗/未驗證據、open findings、背景 jobId/owner/收法、授權來源與範圍指針、下一個可執行 action、read-set 與未恢復範圍。已有欄位不重抄。
- 落盤成功後才做可選 memory 候選整理；無授權／無寫權／usage 不足就記交接。memory gate 故障不能阻止保存工程狀態，亦不能被跳過後報已蒸餾。
- 恢復順序：定位指定任務→當前 git/EP/card 和 active job→active findings＋最新證據→checkpoint 的理由及未決→按需 STATE/memory→所需新鮮 guidance→確認下一動作前置。不用「最新 session」猜身份；缺 transcript 時只聲明可見範圍，不要求無限考古。
- autonomous-execution 的 Session Recovery 改為引用 `task-recovery.md` 恢復順序；intent 維持 EP 段落定義（crash-only reconciliation 不依賴進度檔的語義不變），另加讀 S2「段落結果寫 EP 進度」欄位作已驗/未驗輸入；deep-work 無 EP 弧沿用 journal，不新造進度檔。
- 機械核對檔案／hash／job 狀態；語義核對下一動是否符合仍有效的目標與決策。只重述摘要不算恢復驗證。漂移只擋受影響行動，能獨立做的工作仍可進行。
- at 先結算再排程；handoff 使用同一 read-set，仍保留接手方自足 prompt。不把 checkpoint 的舊 hash 當作當前 HEAD 必須回到的 target；它只是比對依據。
- 不以模型切換自動 compact、不設不可取得的 token threshold、不依賴 SessionEnd。背景 job timeout 先辨識 running/unknown/terminal，保留所有未收回工作，照既有 bridge 收法。

### Invariant Impact

恢復不得跨 task/WT 寫入，不得把推測升級完成，不得重派仍活的 writer，checkpoint 不擴張授權。對應 SM-08/09/10/11/15/18。

### 驗證與完成條件

用兩個 fresh context：A 做到中間狀態寫現有 artifact；B 僅得到入口指針，實際讀料後列下一動。對照普通、debug 中途、STATE stale、untracked 變更、活 job、證據失聯、無 memory 寫權。測試不執行真 commit／部署／compact；假外部動作用可觀察 dry-run 選擇。B 若重做已完成動作、遺漏 pending、把 unknown 寫 completed 即 FAIL。三入口引用同一恢復源，沒有多份分歧清單，才可結段。

## S4：成果視圖、結算與整體驗收

### Context

更新 UC-V 並驗收整體 UC-R/E/C。依賴 S1–S3；方向可理解與工程完成度都要成立。無另附 spec；產品不新增 HTML generator 或修改 tour runtime。既有 Report Shell 仍沿用同一任務家與 template；圖的省略須是提案中的正常分支，不能假報渲染已完成。

錨點：`skills/_common/illustrate-html-mode.md:24` 殼契約 → execution-plan 定稿、post-build hook 2、implement 階段 6；`skills/metadata-sync/SKILL.md:26` 結算矩陣 → implement 5a/post-build；`ai-analysis/blueprint/workflow.md:28` 人讀導航 → blueprint 索引。

### 修改要點

- 方向 brief：問題／使用者看得到的結果／重要取捨／不做範圍／驗收。成果 brief：before/after 具體例／實跑證據／未驗／重要偏離／回源。保留來源 revision/content SHA 與 Built/Verified 區分。
- 不新增另一份日常 debrief；深挖仍由既有 debrief/illustrate 按需。殼同位置更新一次，不能每個 reviewer 都生成一份。
- deep-work 的完整開發流程 pipeline 與 Agent Review／judge 流改引用 S1/S2 新語義：review-engine「review 執行預設」段消費 S1 profile（不再引用 max-agents 填滿）、Agent Review 改邊界觸發、judge 傳入含 `coverage` 的 findings；其對 review-engine 的 pointer 行免改。
- 圖觸發：文字／表格無法清楚表達的跨邊界關係、複雜狀態轉移、user 明示，外加 task 型態預設（user 09-15 反饋）：UI 相關→mockup 圖、流程相關→流程圖、演算法類→步驟／資料流圖解、架構變更→架構圖講解——殼的核心價值＝system analysis/design 的圖，畫不出來或沒有的殼意義不大。品質判準＝人一眼看到重點（sidebar 跳章看大方向＋每章先給結論再給圖）；不達準的圖不如表格。簡單流程可用 HTML 表格；無圖則標「本次以文字/表格呈現」，不留永久 degraded 假待辦。首次部署新預設前以 user 讀稿 pilot 驗方向。
- 持久 tour 延用現有 ask-once／預設略過；不重造政策。既有 tour corpus 指到本次改動而失效仍必修；不能以不產新 tour 逃掉舊鏈維護。
- metadata-sync 保留 build/收斂/standalone 分工與冪等重跑；本弧不新增結算 receipt/cache。只有既有 EP 進度能指向相同輸入內容及仍在場的結算產物時，才引用已完成項；無法核對就由 metadata-sync 對適用項冪等重跑。review identity 只授權復用 review 證據，不代表 metadata 已完成；commit 仍做最後 scope／finalization 對帳。
- 同步 root/guide 導航與 skills/CLAUDE、blueprint workflow 掛點；root AGENTS 若為生成物，改其來源再部署，禁止直接編輯生成投影。rules 政策改動須遵守 freshness／fresh-session 驗收。

### Invariant Impact

人類 brief 不能比 EP/實物更樂觀，未驗證不顯示 Verified；省圖不省行為證據；finalization 不授權 commit/deploy。

### 驗證策略

1. Static：依 instruction-writing 五維檢查、consistency、navigation、single-source checks；current consumers 的固定規則改完，歷史 reports 不改。source 變更先 scoped，再跑既有全域檢查；若舊債失敗記 baseline/歸屬不順修。
2. Behavior：依 instruction-testing 固定 control（修改前）／treatment（修改後）、相同 model/carrier/場景、fresh context。decision/gate 案例帶時間、進度與權威壓力；output 欄位用 micro-test；改 desc 才額外測 activation/nonmatch。保留 PASS/FAIL/UNEXPECTED/INCONCLUSIVE，不挑綠重跑。
3. Oracle：預置 untracked stale、漏 caller/invariant、未裁決 finding、背景 writer、錯 task 身份、零 review fallback、整合器及注入點 extras 等反例，正確選擇在跑之前凍結；reviewer 不讀作者預期解法，只消費其 mandate 所需材料。至少覆蓋一般 feature、控制面、跨邊界、整合器四類；rep 要求引用 instruction-testing，不另複寫一組門檻。
4. 成本：每 case 記實際 agent dispatch 數、所讀材料量、重複檢查數、可取得 usage 的 input/output/cache 口徑、人需要補充的次數。缺 usage 欄標 unknown；並行縮短等待不等於省 token；自動排程亦有成本。本弧不調排程頻率。
5. 驗收：hard invariant 場景不得有 FAIL；普通場景重複派工／重複讀取確實下降；seeded bug 檢出若較舊流程下降，保留舊配置並縮小新預設適用範圍。樣本不足不得宣稱統計等價。
6. 真實 pilot：挑下一個已授權一般變更與控制面變更觀察完整鏈；若 deep-work 有改，pilot 加一 autonomous 小弧或顯式記未 pilot 維持舊語義；user 能由 brief 說明改動與缺口。未做 pilot 可標 Built，不能標新流程 production accepted。如有 HTML interactive artifact，跑瀏覽器導航/折疊/hash restore，再做視覺驗收；static parse 不冒充 runtime。

成功＝consumer 行為試驗＋跨入口整合＋人讀材料對齊；不能只以 markdown/rg 全綠完成。

## 修改面 manifest 與整合策略

baseline: 0bbddb1ca69b8d574b6f5ef20cecaba14050a691

| 段落 | Product 寫入集合（實作前逐檔讀取） |
|---|---|
| S1 | skills/review-engine/SKILL.md；skills/_common/workflow-review-pattern.md |
| S2 | skills/execution-plan/SKILL.md；skills/ep-review/SKILL.md；skills/implement/SKILL.md；skills/code-review/SKILL.md；skills/_common/agent-review-cycle.md；skills/_common/work-order.md（批次 envelope）；skills/audit-test/SKILL.md；skills/judge-review/SKILL.md；skills/followup-review/SKILL.md；skills/post-build/SKILL.md；skills/agent-workflow/SKILL.md；agents/AGENTS.md |
| S3 | skills/_common/task-recovery.md（新）；skills/compact-prep/SKILL.md；skills/at/SKILL.md；skills/handoff/SKILL.md；skills/autonomous-execution/SKILL.md；rules/context-management.md；skills/_common/work-order.md（恢復指針，不改 consent） |
| S4 | skills/_common/illustrate-html-mode.md；skills/metadata-sync/SKILL.md；skills/deep-work/SKILL.md；skills/CLAUDE.md；ai-development-guide.md；ai-analysis/blueprint/workflow.md；S2 的 EP/implement/post-build 掛點修訂 |

Verify-only（核對與新語義一致即可，不預期改寫；矛盾時回對應段落修訂而非實作現場改方針）：S3＝`skills/_common/state-md-write.md`；S4＝`skills/debrief/SKILL.md`、`skills/illustrate/SKILL.md`、`skills/commit/SKILL.md`（只對帳引用）。

manifest 是初始閉合集，不是禁止發現真 consumer。rg 搜尋 `3-perspective`、`max-agents`、`dual-context`、`產圖一次`、`header identity`、`compact 後恢復`、`memory 新鮮度`、`共用規範`、`與.*共用` 逐個單 pattern，命中相關 current source 才追加（記理由、owner、段落）；歷史材料排除。未掃到不作零消費者證明。

S1/S2 是同一政策切換，未全接完不 deploy；S3/S4 不覆寫另一弧 dirty。部署前取最新 source hashes、展示具體 target diff＋恢復用舊 bytes，另取 user deploy 授權。失敗修復整組或還原本弧部署，禁止留半新半舊。政策反轉後依現行 freshness 走 fresh context 驗收，本 session 的自審不算新政策證據。

rules 變更的部署驗收依 `rules/AGENTS.md`：先用現行 `scripts/deploy_agents.py` 支援的預覽方式檢查各 target diff 與 size gate（先查 CLI，不猜 flags），授權後 `uv run python scripts/deploy_agents.py` 重建／部署；再逐端 rg marker＋關鍵內容、`/sync-sources` 的 deploy_bundle_freshness byte 比對，Claude 另核 symlink 內容。fresh context 實際載入與 workspace 合併尺寸亦須查驗；pre-deploy 預期 stale 與 post-deploy 失敗分列，不能要求未部署檔先 freshness 綠才允許部署。

## 收尾步驟

### 給實作 LLM 的接手入口

本 session 的交付只有規劃；user 原話「新流程實作會交給其他的llm」。接手者不要把本文件存在當作已開工，也不要重做 Marshal：實作基線 `b4a3019` 已完成，`0bbddb1` 是本輪研究的 integration baseline，不是要求 checkout 回到的目標。

read-set：本 EP 進度／Review 帳本 → reports checkpoint 最末節 → 只讀需處理的增補 findings → current AGENTS、execution-plan／implement、instruction-writing、instruction-testing、相關 owning workflow。其他模型在 `/Users/ctai/Github/ai-guide` 的既有 dirty 不屬本弧。AIR-60 僅部分承接、AIR-96 排除；先做 owner 對帳，不自動結案整張 AIR-60。

段落交付次序：S1 交 review 需求與身份契約；S2 交所有入口一致的派工／coverage 行為；S3 交實際中斷接續證據；S4 交行為對照及成本／品質結果。每段先跑最小反例，再擴到適用場景，保存原始結果與偏差。decision 段由合格 candidate 承擔，機械段可依既有 resolver 派工；不把模型名釘在 EP。

已決策理由：不新增 engine/router，是因 AIR-91 已提供解析契約；不另造狀態庫，是因接續要核對既有實物；減量先去重與批次化，是為避免便宜 worker 反而增加主 session 搬運成本。不能因這些理由刪掉未覆蓋的獨立性／runtime 驗證；效果不成立就縮小新預設適用面。

開工前 prerequisite：user 交付實作指令、最新治理資料可讀、owner/scope 已對齊、增補審查無未解 Important、重取當下 HEAD／source hash 與 bundle size gate 現值（規劃基準後 repo 已前進：AIR-96 結案落地、AIR-97 開收）。部署與 commit 依屆時 user 授權個別處理。HTML 本輪規劃免驗，不授權未來修改互動行為也免驗。最終交付需分列 Built、behavior 驗證、pilot、部署；未做不補成完成。

1. 已接受 finding 回寫段落，followup 驗證完成；新增未決高風險不得用 open=0 假收斂。
2. metadata 依元專案模式：更新受影響 commands/rules 與 skills 索引，不硬造 library Capabilities；SYSTEM-MAP 無對應略過，blueprint 導航同步。
3. AIR-60 只結算本弧真承接且驗收的 AC，其餘保留；不得以本 EP 結案整卡。若開工另有正式追蹤卡，按 kanban precheck/refs 及 final-summary 結案；本次規劃不擅改卡。
4. 殼從 EP 同版投影，保留「計畫／Built／驗收狀態」；若試點或 deployment 未完成明列，不能報全面可用。
5. 文檔驗證、instruction behavior 與任何 evidence verifier 的實跑結果附任務家；若新增可執行 verifier，須實跑並以 audit-test 稽核。純 docs 不跑無關 pytest/mypy 湊證據。
6. memory：只盤點候選與 owner；Codex 不寫共享池，本弧 report 保留未決與終態，不能以沒有 memory 權限偽造收案。
7. 提交前對帳本弧清單及所有既有 dirty 排除；展示摘要/message，依現行 consent 取確認；不含 push/deploy。

## EP Review 帳本

review 対象＝本 EP 及列明 current sources；Reviewer authority=findings、judgment_floor=decision（跨 workflow 控制面）、qualification=review_findings；Arbiter 在主 session，apply 僅修改此 EP。

| ID | 嚴重度 | 問題／證據 | 處置 | 狀態 |
|---|---|---|---|---|
| F1 | Important | fallback 無 review 仍可能結案；implement:320 | ✅ 補弧級 coverage gate；停審只 Built／🟡，SM-16 反例 | verified（EP 修訂） |
| F2 | Important | implement:231–239 三組 extras 漏接 | ✅ 保留全部映射；S1/S2/SM-19/oracle 同步 | verified（EP 修訂） |
| F3 | Important | rules:14–42 的部署驗收需具體承接 | ✅ 加 size／逐端／freshness／fresh context；修正建議中先後倒置 | verified（EP 修訂） |
| F4 | Suggestion | no-candidate pending owner/收法不明 | ✅ 補既有 ledger＋owner＋恢復條件；不要求每三行重複，也不自動排程 | verified（EP 修訂） |
| F5 | Suggestion | 新結算 receipt 無 producer/key | ✅ 移除新 cache；沿用既有進度與 metadata 冪等重跑 | verified（EP 修訂） |
| F6 | Suggestion | active pointer 存放未定 | ✅ 既有 EP/journal/report 欄位；含 ignored 檔盤點，避免 git status 盲區 | verified（EP 修訂） |

來源：`references/review-muse.json`，job `job-mu2dzpyw-geyy61` completed/exit 0；followup：`references/followup-muse.json`，job `job-mu2e7wgx-ffgcbp` completed/exit 0，六項 resolved、無新增 Important。主 session 核對回覆逐項證據後將 EP 修訂標 verified。六項均採納問題，修法依上述調整；無 findings 需 user 裁決。此驗收限計畫修訂，未修改 production source；新預設仍待 user 接受，S1–S4 behavior/pilot 未執行。

需特別檢查：減量是否偷掉獨立性；單 reviewer 假等價；AIR-60 重複承諾；身份失效是否 fail-closed；ordinary 段跳 review 是否仍有弧末覆蓋；brief 是否偷換人類裁決；新增 common 片段是否變第六狀態庫；減少程序是否增加重建成本。

### Marshal 增補審查與裁決

來源 `references/marshal-integration-review.json`，job `job-mu2fgaqy-d9l930` completed/exit 0，已收回。主 session 核對 allow-list、followup 全部流程及 work-order envelope 後裁決：

| ID | 裁決／理由 | 計畫修訂 | 狀態 |
|---|---|---|---|
| M1 | 部分採納：相容判準不能只看 Role。拒絕「普通三視角永不可改」——那是本 EP 明示要驗證的政策變更，不是不可改的底層 invariant；原 Reviewer 自己亦同意去掉 cap 填滿 | S1 profile 先於 batching；S2 本弧僅同 authority 批次，禁止 writer/reviewer、reviewer/arbiter 和必要獨立 lens 合併 | implemented，待增補 followup |
| M2 | 採納：followup 的 responsibility 要明示。現行 followup:43–62 有驗收／帳本措辭與主 session 更新說明，不能只添 row 而不消歧 | S2 補 Reviewer/findings row，Arbiter 做最終閉合；不充當新的弧級獨立證據 | implemented，待增補 followup |
| M3 | 採納：adapter 引用既有 rows 最小；不新增 union schema、engine 或模板檔 | 既有 work-order 多成果 envelope，S2 manifest 同步；逐 unit 資格與結果、部分失敗及依賴失效驗證 | implemented，待增補 followup |
| M4 | 採納 stale/unknown 與 retry 守衛；不採「retryable-at 是唯一可沿用時間值」這種無充分依據的全域宣稱；它是重試下限，不是 available 證據 | 每 dispatch snapshot、新 worker read-set、空輸出不當零 findings；SM-22/23 | implemented，待增補 followup |

新增情境 SM-20–24；成本量測沿用 S4。Muse 未重讀 hook2/compact 背景來源不等於此前證據失效，本次不擴張那些項目的結論，也不聲稱有實際執行頻率統計。原六項 verified 仍限原修訂；本節待增補複核。

增補 followup `references/marshal-followup-review.json`（job `job-mu2fn09e-d6vjf8`）確認 M3 resolved，M1/M2/M4 各留一個 Important：M1-B1 跨 review unit 錨污染、M2-B1 status/disposition 雙寫歧義、M4-B1 快道未指名落點。三項採納並已修訂：批次只限機械查證／實作成果；followup 約 :43–51/:61 的寫入措辭與 pattern/implement/post-build 同步，主鏈編排者寫 status、Arbiter 只裁 disposition；post-build:88 加 completed＋完整輸出＋coverage 閘。這些是 source 修改計畫，非已實作行為。

**增補終態（取代上表中間狀態）**：`references/marshal-closure-review.json`，job `job-mu2fstmq-gouh8l` completed/exit 0，M1-B1/M2-B1/M4-B1 全 resolved、無新增 Important；主 session 核對 EP 錨點後，M1–M4 全標 verified（限計畫修訂）。closure 僅核 EP 文字，未重跑 current source 或 runtime；實作段仍須依 manifest 查當時最新版。原 F1–F6 及增補均無 open Important；新預設的效果不因文件審查而視為已證明。

### User pre-implement 方向修訂（S4）

09-15 user 對殼/圖政策回饋，於 implement gate 前併入 S4（方向權威＝user，不另派外部審查）：①delta tour 維持 ask-once＋預設略過、收尾最後問一句——確認現行設計即目標形態，不另改②圖觸增加 task 型態預設（UI→mockup、流程→流程圖、演算法→圖解、架構→架構圖講解）＋品質判準「人一眼看到重點」；殼核心價值＝system analysis/design 的圖，無圖或畫不出者意義低③成果 brief 的前後對比維持既有 before/after 具體例，機制講解（演算法步驟/架構圖）依 task 型態由圖觸發條款承載④同回饋同步 AIR-73（build_shell codegen 的內容需求輸入）。

### 主 session findings 外部審查與裁定（N1–N8＋S1）

Findings 來源 `references/review-main-session.md`（staged；獨立 subagent F1–F5＋主 session 合成，user 明示外部審查＋裁定後才回寫）；外部審查 `references/external-review-muse.json`，job `job-mu2kr2hs-6k82uh` completed／exit 0，唯讀、對當時 HEAD `2d1c432` 逐條實驗。裁定：N1–N4、N6–N8、S1 全採納——N1 依外部審查修正版落地（staged 建議句在 AIR-96 結案 `b68b7d0` 後自身過時；改為反映「已結案、無遺留 dirty、不重開」，不為已結案弧新增協調條款，開工 prerequisite 補重取 HEAD／size gate 現值）；N4 以「承接清單（file→segment）」取代原「disposition 清單」措辭，避免與 Arbiter 裁決權混淆；N2/N3/N6/N7/N8/S1 按 staged 原建議落地；N5 資訊項 EP 免修（「實作前 rg 重定位」條款覆蓋，references JSON 行號回查以 rg 為準）。外部審查訂正工單檔案歸屬：`skills/CLAUDE.md`、`skills/model-routing/*` 等 8 檔屬 AIR-96（`f68e77b`／`09e08ab`）；AIR-97（`5852e55`）僅動 `ai-development-guide.md`＋`muse-plugins/tool-governance/*`。無新增 Important；此輪仍限計畫修訂，未修改 production source，新預設仍待 user 接受。
