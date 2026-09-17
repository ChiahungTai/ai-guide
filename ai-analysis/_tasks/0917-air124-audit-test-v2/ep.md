# AIR-124 EP——audit-test 改版（存量補強場景重構）

> **ep_type**: implementation（docs mode——product 全為 .md instruction 檔）
> **baseline**: 45ed513
> **author_family**: glm
> 卡：AIR-124（backlog/tasks/air-124*.md——Plan ①-㉕＋AC ①-⑩為意圖合約）
> 設計鏈（段落 0 等效研究，已前置完成）：web 研究 4 搜＋bi 設計討論（muse mu5kt9v4／codex mu5kvs0u）＋flash 三查（coverage/SC pwspec/mosaic UI）＋user 三修（存量場景/非 TDD/多家族 night-mode）＋審卡雙腿（muse mu5lp8ss／codex mu5lrksz——16 findings＋8 契約全吸收進卡 Plan v2）。verdict 全文：.agent-tmp/dispatch-compiler-proposal/audit-test-*.md 與 air124-*-verdict.md。

## 實作總覽

把 /audit-test 從「開發期八角度稽核器」改版為「存量補強場景」的五證據域稽核器＋night-mode 補強生產線。四段：S1 oracle 正典（定義源先行）→ S2 audit-test 五域重構 → S3 night-mode 節 → S4 接口＋指針＋部署收尾。product 全 .md；驗證＝rg 機械掃描＋跨檔一致性＋/consistency。

## UC 盤點（docs mode——受影響命令/rules 清單）

### Backlog 關聯
- AIR-124（本卡，To Do→In Progress 隨開工）
- 相鄰不動：AIR-118（審查階梯——night-mode 引用其詞彙）、AIR-121（寫入權準則——oracle 分級同檔相鄰節）、AIR-123（availability 工具——night-mode per-stage 消費）

### SYSTEM-MAP 影響
- ai-guide 無 SYSTEM-MAP.md——跳過（元專案）

### 掃描範圍
- skills/audit-test/SKILL.md（被改版物）、rules/acceptance-evidence.md、skills/acceptance-evidence/SKILL.md、skills/test-driven-development/SKILL.md、skills/fix-test/SKILL.md、skills/execution-plan/SKILL.md（測試規劃段——引用側）、skills/model-routing/SKILL.md（panel 詞彙——引用側）

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| /audit-test Diff/Commit/Daily 三模式稽核 | ✅ | audit-test SKILL.md | 更新 | Diff/Commit 保留；Daily→night-mode 吸收 |
| 角度 8 TC 契約對帳 | ✅ | audit-test SKILL.md | 更新 | 七項表原文保留、升 Traceability 域第一 gate |
| /fix-test 分類修復 | ✅ | fix-test SKILL.md | 更新 | 僅加 oracle 正典引用一句 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| 存量測試五證據域稽核（oracle 分級/vacuous-green/vector 報告） | 📋 | skills/audit-test/SKILL.md |
| 多家族 night-mode 補強生產線（五段管線＋八契約） | 📋 | skills/audit-test/SKILL.md |
| oracle authority 正典（S/H/I/N） | 📋 | rules/acceptance-evidence.md＋skill 下沉 |

## Scenario Matrix（docs mode——文檔語境）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 存量測試無 EP 出身 | 掃到無 TC 對帳來源的舊測試 | 標 provenance:unknown（非跳過）——出生證明查核 | rg "provenance:unknown" 命中於新 SKILL | 存量稽核 |
| SM-2 | 會計測試條件式斷言 | if-in 包 assert 形態（test_accounting 形態） | vacuous-green detector 判 Important（非計數健康） | rg 條文在場＋案例描述 | 存量稽核 |
| SM-3 | health score 舊用法 | AI 讀新 SKILL 想算百分比 | 無 health score 條文＋vector 模板在場；rg "健康度 =" 零殘留 | rg 掃描 | 存量稽核 |
| SM-4 | 夜間 GLM 撞 1308 | per-stage availability resolve | flash 腿預設不存活＋P3 無 judge→stop-before-P4 條文 | rg 條文在場 | night-mode |
| SM-5 | P2 工單含 P1 ledger | 組 blind reviewer 工單 | blind input contract：禁讀清單（P1 .partial.md/daily report/另一 reviewer output）必載 | rg 條文在場 | night-mode |
| SM-6 | S/H 測試使 baseline RED | P4 補強測試對 canonical baseline 跑 | ＝production defect→pending-decisions；夜間禁改 production | rg 條文在場 | night-mode |
| SM-7 | survived mutant 餵 P4 | P4 想看 survivor 寫斷言 | survivor 只可指出 probe 位置、禁決定 expected value（封閉迴圈防護） | rg 條文在場 | night-mode |
| SM-8 | kill-rate drop | trend 觀察 | investigation signal 不阻擋（唯一 hard gate＝新增確認 non-equivalent survivor） | rg 條文在場 | mutation 三層 |
| SM-9 | 夜間管線中斷 resume | P2 完成後 process 終止再續 | immutable ledger 恢復、不重跑已完成 stage、不污染 blind 邊界 | rg resume 條文在場 | night-mode |
| SM-10 | P2 兩家 reviewer 全缺 | muse/codex 同時 unavailable/timeout | stop-before-P4＋degradation receipt（禁靜默跳過） | rg 條文在場 | night-mode |
| SM-11 | delta 零交集 | 兩 reviewer findings 交集為空 | 仍成 delta（全差集）→全部進裁決隊列，禁自動 P4 | rg 條文在場 | night-mode |
| SM-12 | sink adapter 缺席 | 目標 repo 無 inbox/daily-report | fail-closed＋degradation receipt＋零靜默寫入 | rg 條文在場 | night-mode |
| SM-13 | P4 admission 缺三證據鏈元件 | finding 缺任一證據鏈成分 | 拒絕進入 P4（非降級放行） | rg 條文在場 | night-mode |

## 測試規劃段

**跳過**——純文檔 EP（docs mode）：product 無可執行碼；驗證＝rg 機械掃描（SM 各列）＋跨檔一致性＋/consistency。控制面語義變更的審查鏈由本 EP 的 ep-review（跨家族雙腿）＋收線 docs-mode 鏈承擔。

## 段落劃分原則

線性依賴（定義源→重構→新節→接口）：S1→S2→S3→S4。S2/S3 同檔先後編輯；段落自足（每段 Context 帶卡 Plan 對應條號）。

---

## S1：oracle 正典（定義源先行）

**Context**：審卡定案（codex 建議）——oracle 分級正典歸宿＝rules/acceptance-evidence.md（證據獨立性 domain），非 quality-constraints。卡 Plan ⑤㉕。無程式碼；修改要點層。
**依賴錨點**：rules/acceptance-evidence.md「核心原則:證據獨立性」節（定義端）／消費端＝audit-test（S2）、fix-test、execution-plan 測試規劃段（後續引用）。
**修改要點**：
1. rules/acceptance-evidence.md 加一段 oracle authority 正典（卡 ⑤原文）：S＝具獨立 authoritative oracle_source（規格/領域恆等式/歷史數據，禁待測實作）的 frozen spec/TC——frozen 本身不授予 S；H＝歷史真實數據/真實 carrier 行為（anchor＝dataset/version/hash/record-id；text 類才 file:line）；I＝impl 衍生；N＝無 oracle——I/N 禁 autonomous 補強授權
2. skills/acceptance-evidence/SKILL.md 對應節下沉細則（H anchor 形態例、S 判定流程）＋指回 rule 一句
3. fix-test／execution-plan 測試規劃段各加一行引用（禁重寫）
**驗證策略**：rg "oracle authority|S=具獨立" rule 在場；三處引用 rg 命中；/consistency 兩檔；跨檔零重複定義（正典句只出現 rule 一處，其餘皆引用形）。

## S2：audit-test 五證據域重構

**Context**：卡 ④⑤⑥⑦⑧㉔＋審卡 muse F4（精華段歸宿）/F5（輸入模式）。主體工程——SKILL.md 結構置換。
**修改要點**：
1. 八角度→五域結構（域標題＋域內 detector 清單）；搬遷對照：角度 8 七項對帳表**原文**入 Traceability 域＋升該域第一 gate（有凍結 TC 時）；PropertyMock 危險性段**原文**入 Semantic Integrity＋新增 per-repo mock 豁免教義（vi.mock('vscode') 形態，豁免清單 repo 自持）；Registry Membership／Method Coverage 流程**原文**入 Traceability
2. **搬遷保存清單（migration manifest——審卡/EP review 雙腿裁決）**：三精華段各建錨點對照行（舊 section heading → 新域 section → status moved/intentionally-removed），S2 產物附於 EP review 區段——驗收從「看 diff」變「對錨點」；搬遷時改字＝SM-14 偵測點
3. 新 detector：vacuous-green（條件式斷言——無 else-fail 的守衛斷言；附 test_accounting 形態案例描述）；oracle 分級標注（引用 S1 正典，每 finding 帶 S/H/I/N 欄）＋**誤判推翻半句**（分級是 detector 標注非判官——findings 非定論，judge-review/實作查證可推翻）
4. **Adversarial 域補 mutation 三層 gate 語義**（卡⑨落點——審卡 muse Important）：P0 critical path 變更弧 scoped mutmut 必跑＋gate 判「新增且確認 non-equivalent survivor」＋**mutation feedback 永不取得 oracle/expected value 修正權**禁令明文
5. 砍除：角度 5 marker 分層、mock-count>assert-count heuristic、單一 health score（含計算式與評分表）——條文移除
6. 角度 2 修正：source↔test diff 對稱→behavior impact evidence 查詢（凍結 TC 制度相容）
7. 報告模板置換：8 維 vector（semantic_integrity/traceability/critical_invariant_coverage/path_evidence/adversarial_strength/fixture_provenance/flake_isolation/suite_operability）＋gate 判準（Critical evidence 存在＋P0 mandatory dimensions 缺場）＋trend 註記（分數類無 blocking authority）
8. 輸入模式處置：Diff/Commit 保留（pre-commit gate 接點不變）；Daily→night-mode 吸收（互指一句）
**驗證策略**：SM-1/2/3/13 各 rg；砍除**引用側全 repo 掃**（codex 裁決——非僅 audit-test 自檔）：rg「八角度|角度 5|健康度 =|mock 數.*assert|漸進式驗證合規」於 skills/ rules/ AGENTS.md（allowlist：archive/歷史報告/卡檔）；五域標題在場；migration manifest 錨點對照齊；/consistency。

## S3：night-mode 節（執行契約 10 條）

**Context**：卡 ⑯-㉒㉓——audit-test SKILL.md 新 top-level 節。user 設計要求（家族分配）；審卡雙腿＋EP review 雙腿裁決全收。**Entry condition（codex）**：S2 完成——五域名稱穩定、finding schema 含 oracle_level 欄、gate 語義在場、audit-test SKILL 無 legacy 角度詞彙殘留。
**節首 rationale 一句**（卡⑯⑲落點）：分配軸＝獨立性需求×判斷密度×成本；夜間可用性以 spine 事件＋三訊號判定不預設。
**修改要點**：
1. 五段管線條文（P1 flash 掃描→P2 跨家族盲審→delta→P3 judge 裁決→P4 補強→P5 機械驗收），每段：載體、輸入、輸出、停止條件；**resume 條**（SM-9）：P2-P5 產物同等 durable 落盤（P3 決策記錄/P5 receipts），中斷後從 ledger 判已完成 stage 續跑、禁重跑禁污染 blind
2. **執行契約 10 條**（codex 正名——原「八契約」實列 10 條：target manifest（P1 前凍結、來源＝Adversarial 域 critical-path 輪選清單〔原角度 7〕＋dependency-graph hotspots、禁 P1 污染 P2 targets）／blind input contract（禁讀清單：P1 .partial.md/daily report/另一 reviewer output；如實標 procedural blindness——hard 隔離待實作期 sandbox 驗證）／delta identity（canonical key＝target/module＋behavior/predicate＋oracle anchor；交集＝support-count≥2；**零交集→全差集進裁決隊列禁自動 P4**〔SM-11〕）＋**delta 三選一歸類表**（卡㉒落點：spec 歧義→修 spec／單邊漏→聯集／兩可→user 裁決）／mutation baseline（pre-run 與 P5 同 scope/operator/config）／P4 admission（S/H＋三證據鏈**缺一即拒**〔SM-13〕＋survivor 禁決定 expected value）＋exit（baseline GREEN＋targeted mutant RED；baseline RED＝production defect→pending-decisions 夜間禁改 production）／per-stage availability（P3 無 judge→stop-before-P4；GLM 撞牆 flash 預設不存活；**兩家 reviewer 全缺→stop＋degradation receipt**〔SM-10〕）＋degradation receipt（panel=single＋same-family 記錄）／sink resolver（repo adapter；**adapter 缺席→fail-closed 零靜默寫入**〔SM-12〕）／readout owner（P5 aggregator 從 immutable ledgers 組裝）
3. autonomous 紅線（不 commit／夜間止於 P5 證據／P4 只寫 tests/fixtures）
**Deferred（judge 裁決記錄）**：codex 建議 mutation baseline＋pipeline 契約抽 _common/（night-mode-contract.md）——**本弧不抽**（單一消費者，YAGNI）；promotion trigger＝第二個 night-mode 消費者（如 code-review night mode）出現時抽離。
**驗證策略**：SM-4/5/6/7/8/9/10/11/12/13 各 rg 條文在場；契約 10 節標題齊；與 model-routing panel 詞彙零重定義（rg tri/bi 引用形）。

## S4：接口＋指針＋部署收尾

**Context**：卡 ①（TDD 接口）、⑬⑭（指針圍欄）、AC⑨⑩。
**修改要點**：
1. test-driven-development SKILL 加出生證明接口**一句**（三欄最小 schema：provenance 鍵/值域 S/H/I/N/unknown/存放位）——僅此一句，禁建造管線回流
2. audit-test 加域特化指針段（圍欄：問題陳述＋彼側卡連結——mosaic invariant/PBT/hash gate＝MOS 側卡〔含 domain-validity guardrail〕；SC protocol contract 首位＋薄改清單）＋**落定 gate**（卡⑭⑮ uncommitted 前提：開工前確認彼 repo commit hash 回填卡 notes，未落定對應項 defer）
3. 部署：deploy_agents.py（rules 變更）＋fresh session 驗證（rg 新教義命中**部署後 bundle 面**——deploy 是 projection，source rg 不替代 generated 面驗證〔codex〕；stale 偵測交 AIR-122 freshness 閘管轄）
**驗證策略**：TDD 側 rg 僅一句（無 RED/receipt 字樣回流）；指針段 rg 圍欄句；deploy 3/3；新詞（五域/vector/night-mode）於 ~/.zcode/AGENTS.md 或 skills 部署面命中。

---

## 整合策略

- baseline: 45ed513（git rev-parse HEAD 於 EP 建立；implement 開工前確認 HEAD 未漂移——EP review 後卡面 baseline 3b9f1ec 已過時，以本欄為準）
- author_family: glm（EP 作者 GLM；消費端 same-family gate 由 implement 承接——docs mode 無 RED 面，審查鏈以 ep-review 跨家族雙腿補獨立性）
- **Open item（implement 期決）**：夜間執行主體 repo 歸屬（跑在哪 repo/派工面、P4 branch 落點、autonomous 紅線適用哪套）——審卡 muse 殘餘，卡⑳只定義了 sink 未定義主體
- 下游消費者：/implement（docs mode 分支）、post-build（docs-mode 審查鏈）、kanban 收尾；deployment surface=rules＋skills（deploy_agents）
- 與 AIR-121 寫入權準則相鄰：acceptance-evidence.md 兩節並存不互改（S1 只加新節）

## EP Review 記錄

- muse 腿（job-mu5mc16p，intent）：EP-needs-fix——⑨ gate 語義落點/㉒歸類表落點/stale pointer 已修；Suggestion（SM-9/誤判半句/錨點對照/F7 gate/rationale 引言）全採納
- codex 腿（job-mu5mc17y，fresh）：EP-accepted with targeted fixes——S3 entry condition/契約正名 10 條/migration manifest/SM-9~13/引用側掃描/deploy projection 驗證已修；_common 抽離 Deferred（YAGNI，promotion trigger 記錄）
- verdict 全文：.agent-tmp/dispatch-compiler-proposal/air124-epreview-*-verdict.md

## S5 Final acceptance（recovery owner 單一 narrator——0918 衝突裁決後重寫）

- **Final authority**: recovery owner（互動主 session，user 指定）
- **Selected implementation**: A 線（branch air-124，已收斂）
- **Final revision**: `fd1cdc04`（＝A 實作 `7e0c92b`＋drift 同步 `61d62e4`＋吸收 commit）
- **Acceptance evidence**: EP review 雙腿（mu5mc16p/mu5mc17y）＋落地審查 muse accept（SM-13 獨立複驗＋搬遷 byte-identical）＋codex accept（五設計遺產保真）＋5.3 judge accept；部署 3/3 從 canonical main `fd1cdc04` 重跑（provenance 重建）
- **Incident（事故紀錄——B 的原始 S5 草稿見 .agent-tmp/air124-incident/b-epmd-delta.diff）**:
  - A（互動主 session）與 B（平行 session，user 已令停止）自 EP 祖先 `3f582c79` 獨立實作；核心檔互 diff 769 行
  - A 曾 merge 進 main＋部署，被 B 的 stash 操作回滾 main（owning-line 單調性違反——防護規則進 AIR-125）
  - 衝突經 muse（品質軸：keep-A，B 無任一軸反超＋B 有 H anchor 表刪除等結構違規）＋codex（工程軸：Phase 0 凍結＋forward recovery＋防再犯）雙腿裁決＝keep-A＋吸收 B 四項（vacuous 4 訊號/契約8 指針拆分/reviewer 申報/zoom+exec-plan 補漏——吸收 commit `fd1cdc04`）
  - B 線可驗證證據（871 passed/3F 等）作 evidence 留存；「主 session 代貼」ownership claim 不採
  - 非選定實作（air-124-impl branch）未 merge，保留為事故 provenance；B WT 已移除
- **事故窗口 context 注意**：A 部署→回滾期間若有 session 載入過新 audit-test，keep-A 且最終 bytes 等值下語義可續；嚴格起見該 session 下個 consequential use 前應 reset

### AIR-124 S2 migration manifest（三精華段錨點對照——驗收對錨點非對 diff）

| 舊 section heading（搬遷源） | 新域 section（落點） | status |
|---|---|---|
| `### 角度 8：測試契約對帳（EP 含凍結 TC 時）`（七項對帳表） | 域 2 → `### TC 契約對帳（第一 gate——EP 含凍結 TC 時）` | moved（七項表逐字；結構詞「本角度」→「本域」；對帳項 7 交叉引用「既有角度 4」→「消費端路徑證據」同域子節；升域內第一 gate） |
| `#### PropertyMock type-level 危險性` | 域 1 → `#### PropertyMock type-level 危險性` | moved（逐字；其後新增 per-repo mock 豁免教義段——新增非改字） |
| `**Method Coverage 流程**`＋`**Registry Membership 流程**`（含覆蓋搜尋策略三粒度表與教訓 blockquote） | 域 2 → `### 覆蓋查詢：Method Coverage／Registry Membership 流程` | moved（流程步驟逐字；外層「覆蓋對稱性」框架置換為 behavior impact evidence——框架詞替換，流程本體不改字） |

## 收尾步驟

1. Capabilities/索引：skills/CLAUDE.md audit-test 條目 description 同步（存量補強＋night-mode 觸發詞）；AGENTS.md 無需（命令表層級不變）
2. 卡結案兩步＋metadata commit（③特赦鏈）
3. instruction 檔檢查：受影響四 skill 檔頭 when_to_use 與新行為對齊
4. /audit-test 自舉：本弧新增測試（若有 fixture）跑自身稽核；純文檔則標 N/A
5. /consistency 全綠＋部署面對帳（AIR-105 gate）
