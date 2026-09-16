# Guides Refactoring——夜間 deep-work 執行計畫（02:00 runner 用）

> 建立：2026-09-16 22:46｜排程：09-17 02:01 one-shot（automation 見 `.at-contexts/`）｜模式：deep-work autonomous
> 判準源：本目錄 `README.md`（框架＋現況）＋底下附錄 codex 設計＋補強。
> **紅線（autonomous session）**：全程唯讀調查＋文檔產出可自主；**commit 一律禁**（以提案＋建議 message 停在等 user OK）；**deploy 不做**；破壞性動作停手記 completion report。

## 1. 已確認的弧計畫（user 0916 22:4x 拍板原文語義）

前期調查（muse/flash 各 2 腿，依 codex 設計＋補強）→ 回收資料交 **GLM 5.3** 歸納分析 → 與 **codex** 討論出作法 → **execution-plan 由 5.3 寫** → **implement 用 flash** → post-build → **review：codex＋muse** → **judge：5.3** → commit（提案）。

## 2. 前期調查 legs（2+2 配對，已定）

配對原則：flash 產 manifest、muse 吃 manifest 做語義判讀；兩條鏈各自成對（F-A→M-A、F-C→M-D）。其餘腿（F-B／M-B／M-C，覆蓋議題 4/5/6/8）不入本波——由後續 EP 決定第二波。

### 腿 1｜F-A：rules/skills 結構 manifest（flash，registry `lite-verify` spawn，唯讀）

- 覆蓋議題 1/2/3/4 的事實層。
- Read-set（見附錄 codex F-A 全清單）：rules/tool-discipline.md、rules/modern-cli-preference.md、rules/symbol-query-routing.md、instruction 群 7 支、review 群 2 支、接續群 5 支＋實際引用的 _common、維護群 6 支、domain skills 7 支、memory-audit SKILL 載體統一定義表。
- 輸出 row schema：`issue_id | path:line | artifact | trigger/desc/anchor | inbound references | observed overlap key`。
- 驗收：議題 1 三檔全有 anchor；議題 2–4 宣告 skill 每支 ≥1 row；每 row 有 path:line；**禁出 equivalent/redundant/merge 類 verdict 欄**。
- 補強①適用：池無關；不變。

### 腿 2｜F-C：hooks 註冊/涵蓋 wiring 矩陣（flash，registry `lite-verify` spawn，唯讀）

- 覆蓋議題 7 的事實層（窄面：僅 memory 寫入治理，非 hooks 全目錄健檢）。
- Read-set：hooks/block-memory-index-write.py、scripts/reconcile_memory_pool.py、hooks/zcode-registration.json、~/.claude/settings.json、~/.codex/config.toml、~/.zcode/cli/config.json、.agents/memory-governance.json、muse-plugins/memory-governance/README.md、rg 掃 `inflight|landed|pending|memory-inbox` 命中的其他 hook 檔。
- 輸出：`harness | event | registration anchor | target script | guarded path/pattern | writer class`；writer class 四分（main tool write／subagent tool write／muse plugin+inbox／session-end teardown non-tool write）；靜態無法證明填 `unknown`，**unknown 不得轉 PASS**。
- 驗收：三家各有 row 或顯式 `no registration found`；每個 target 解析到 script path:line。

### 腿 3｜M-A：ownership/residency 語義審（muse，bridge `task --family muse` advisory，唯讀）

- 覆蓋議題 1/2/3 的判讀層。Read-set：F-A manifest＋議題 1 三支 rules＋memory-audit 統一定義表＋instruction-testing SKILL＋domain skills 7 支＋（需要時）rules/AGENTS.md。
- 輸出每 finding：`issue | file:line | knowledge owner | required residency | observed placement | candidate label | evidence | limitation`。標籤限：保留/pointer 化/下沉 skill/retire candidate/待查。
- 要點：議題 1 須分辨三處是否各有 bootstrap 責任、哪些可留一行 pointer；議題 2 必須給 keep/retire 二選一（hanging 不接受）；議題 3 須分清「body 按需」與「desc 注入面常駐成本」。

### 腿 4｜M-D：hooks 語義涵蓋 matrix（muse，bridge `task --family muse` advisory，唯讀）

- 覆蓋議題 7 的判讀層。Read-set：F-C matrix＋memory guard scripts＋三家 registration＋.agents/memory-governance.json＋muse governance README。
- 輸出 coverage matrix：`writer | harness/path | registered event | guard reached? | evidence | status(covered/gap/unknown)`；writer 起碼含 CC main/subagent、ZCode main/subagent、muse tool write、muse teardown。
- 驗收：covered 必須同時有 registration anchor＋guard anchor；teardown 已知 bypass 不得被 registration presence 覆蓋。
- 補強③適用：結論若是 unknown→產「runtime 驗證」建議卡，不產「修 hook」卡。

### 執行機械

- flash 腿：ZCode spawn registry `lite-verify`（pin glm-5.3-flash），`run_in_background: true`、並發 2；spawn prompt 注入唯讀三條＋工具紀律（rg/fd）＋禁再委派＋WorkUnitContext（objective/constraints/relevant_files/expected_output——見 conversation-dispatch 模板）。
- muse 腿：`delegate-bridge task --family muse --background --prompt-file <file>`（advisory profile＝sandbox 預設、**不帶 --yolo**、工單紅線承載 READ-ONLY/no writes/no git）；bridge pin 唯一源＝installed_plugins.json 的 delegate installPath；背景 Bash 掛 `wait <jobId> --timeout 0` 收。每腿工單 ≤ 合理 bounded（muse 可讀機本檔，read-set 傳路徑即可）。
- 派發確認行：`[Bridge] family=muse model=muse-spark-1.3 effort=high profile=advisory`；spawn 印 `[Agent] model=glm-5.3-flash(lite-verify)`。

## 3. 後續鏈（調查完成後依序）

1. **歸納分析（GLM 5.3）**：判斷密集位。**seat 偵測**：runner 開場自查 model——若主 session 已是 GLM 5.3（user 已切）→ native 做；若仍是 Flash → 走 bridge `task --family glm --model GLM-5.3`（分析＝預設唯讀 plan 檔）。輸入＝四腿產出＋README。
2. **codex 討論作法**：bridge `task --family codex`（web high；**材料內聯 ≤8KB、禁只給路徑**——webgpt 讀不到機本檔；歸納結論濃縮內聯）。顧問僅意見權，兩段式回報。
3. **execution-plan（5.3 寫）**：依 air-111 四層制本弧＝full/standalone EP（控制面語義）。seat 非 5.3 → bridge glm `--write-mode edit` 寫 EP 檔（落 `ai-analysis/_tasks/0917-guides-refactoring/ep.md`）。**EP 定稿後先跑一輪 ep-review（in-harness fresh＋judge）再進 implement**——accepted-EP predicate 硬 gate 的自主版補償（夜間無 user 逐項核，以 judge 腿代審；EP ledger 全 terminal 才放行）。
4. **implement（flash）**：registry `impl-lite` spawn 逐段 TDD；lite 測試僅規格陳述→驗收另補 full 複驗（post-build 鏈兜底）。
5. **post-build**：主 session 編排——code 鏈（dual-context review→judge→修正迴圈）＋docs 鏈（consistency→metadata-sync）。
6. **review：codex＋muse**（user 顯式指定雙家族）：muse 走 bridge review/task（diff 審查）；codex 走 bridge task（**EP/diff 摘要濃縮內聯 ≤8KB**）；findings 回貼→judge。
7. **judge（5.3）**：seat 原則同第 1 步；裁決歸位（accept/modify/reject/defer），apply 由主 session。
8. **commit＝提案停點**：展示摘要＋建議 message，**等 user OK**（autonomous 禁 commit）。deploy 不做，記入 completion report。

## 4. 補強三點（已併入上文）

①F-B/M-C 未入本波（EP 決定第二波）；池 86 條 untracked 若被任何腿觸及，一律標 provenance＋「併 air-100 收編波審」。②Wave 2 直辦項：`memory-audit/SKILL.md:149` stale 條款修正（走 instruction 閘）與 spine `git init`（寫入→EP 內列、執行等 user）。③hooks 查到 unknown→runtime 驗證卡建議，非修 hook 卡。

## 附錄：codex 原始設計（job-mu479d3i-5ppvtj，chatgpt-web/high，2026-09-16 22:3x）

<details><summary>全文（要點已併入上文；此處保留原文供追溯）</summary>

建議把這次體檢拆成 **3 條 Flash/機械預處理腿 + 4 條 Muse 語義腿 + 1 個主 session judge**。核心原則是：**先把「有哪些、在哪裡、誰引用誰」壓成 bounded manifest，再把真正需要 ownership / residency / semantic equivalence 判讀的少量材料交給 Muse**。不要把 84 skills、347 memories、整個 hooks/ 一次灌給任何 LLM。

### 1. 範圍切分
8 條議題全部有 owner，盤點與裁決分開：議題1→F-A+M-A+J；2→F-A+M-A+J；3→F-A+M-A+J；4→F-A+M-B+J；5→F-B+J（不需要 Muse）；6→F-B+M-C+J（不執行 consolidation）；7→F-C+M-D+J；8→F-B+J（lifecycle policy）。

hooks/ 只查窄面（memory write governance / task-state suffix protection），三層：腳本涵蓋面／registration 面／cross-harness coverage（writer→event→registration→script→protected target 鏈）。read-set：hooks/block-memory-index-write.py、scripts/reconcile_memory_pool.py、hooks/zcode-registration.json、~/.claude/settings.json、~/.codex/config.toml、~/.zcode/cli/config.json、.agents/memory-governance.json、muse-plugins/memory-governance/README.md、rg 命中的其他 hook 檔。

### 2. 各腿工單要點
- **F-A**（flash）：row schema `issue_id|path:line|artifact|trigger/desc/anchor|inbound refs|overlap key`；禁 verdict 欄；驗收＝錨點齊、cluster 不漏員。read-set 含 rules 三支＋instruction 群 7＋review 2＋continuation 5＋_common 命中者＋maintenance 6＋domain 7＋memory-audit 定義表。
- **F-B**（flash）：三張 manifest（accumulation：path|generation|bytes|producer；memory candidate：path|category|desc|state-word|source ref；reports：path|referenced-by|consumed evidence|lifecycle state）。驗收＝枚舉數=row 數、38+ 候選不漏、11 篇全有 row、無 retire/delete verdict。
- **F-C**（flash）：`harness|event|registration anchor|target script|guarded path|writer class`（四類 writer）；unknown 不轉 PASS。
- **M-A**（muse）：議題 1/2/3——ownership/residency 判讀；輸出 `issue|file:line|owner|required residency|observed placement|candidate label|evidence|limitation`；標籤限集合；議題 2 禁 hanging 答案；議題 3 分 body 成本 vs desc 注入面成本。
- **M-B**（muse，token 最大戶）：議題 4 四 cluster（instruction 7/review 2/continuation 5+_common/maintenance 6），每 cluster 四格（use case/boundary/evidence/limitation）；member exactly once；overlap finding 需雙錨點；無 finding 也寫 `no material boundary finding`。
- **M-C**（muse）：議題 6 退役判讀，標籤限 `M1-likely`/`stable-project-fact`/`source-check-needed`＋file:line+reason+source pointer；不編輯、不重建索引、不碰 86 收編波。
- **M-D**（muse）：議題 7 coverage matrix（writer×harness→covered/gap/unknown）；covered 需 registration+guard 雙錨；teardown bypass 不得被 registration presence 覆蓋；static 只證 wiring——unknown 升級走 runtime validation 工單。
- **J-MAIN**：議題 5（retention policy：producer|owner|retention unit|retain N/age|cleanup trigger|exception；probe-entitlements 是 volatile observation 不套 memory lifecycle）＋議題 8（report lifecycle：active→consumed→archived/retained→retirement condition；11 篇各映一 state；「已消費」≠delete）。

### 3. 人力配置理由（摘要）
Flash＝縮小語義搜索空間（rg/fd inventory、reference matrix、frontmatter extraction、wiring）；不回答語義等價/退役/合併。Muse 四個 judgment hotspot；M-B 與 M-D 最不可降 lite。確定性問題（幾代 snapshot、哪些被引用）不給 LLM。Flash subagent 寫入 hook 不觸發對本次無額外風險（工單唯讀）。

### 4. 波次
Wave 0 機械三腿平行（gate＝三 manifest 過機械檢查）→ Wave 1 muse 2+2（第一批 M-A+M-D，第二批 M-B+M-C；resource control 非 correctness）→ Wave 2 主 session judge 八題（mechanical facts→advisory finding→governing rule→final disposition；衝突時 Flash=存在性/位置事實、Muse=advisory、主 session 重讀 anchor 裁決）。

### 5. 合併與回寫
findings 統一 schema：issue_id/source_anchor/content_type/owner_candidate/residency_candidate/finding/candidate_action（保留|拆分|合併|下沉|引用現有源|退役候選|待查）/evidence/limitation/confidence；judge 加 judge: accept|modify|reject|defer＋judge_reason。回寫：完整體檢 report（含 rejected，作 why/audit trail）＋remediation 只把 accept 項轉卡（一卡=coherent change boundary，禁一 finding 一卡）。issue 6 consolidation 續歸 air-100。

### 6. 風險與成本觀（摘要）
最大風險＝把 context cost 與 storage cost 混算。Rules＝resident×sessions 乘法成本（議題 1 優先）；skills 拆 discovery（desc×sessions）與 body（×trigger 次數）兩種；memory/reports 是 retrieval precision 問題非 resident 成本。Muse 額度靠 bounded read-set＋precomputed manifest 控制（禁 raw output 直塞）；四 muse legs 是合理上限。限制四條：flash 只當 candidate generator；muse 是 advisory 非 final authority（分類規則歧義回 memory-audit 單一源裁決）；hooks static audit 不證明 runtime interception（registration consistency 與 behavioral coverage 分開報）；不擴到 agents/、86 收編波、hooks 全架構、全部 84 skills。

</details>
