# AIR-29 Agents Registry 兩軸重構 Execution Plan

> **EP 類型**：implementation
> **任務基線**：`40f47e8797a69f9a3d455742962df8330421efc5`
> **需求來源**：`ai-analysis/_tasks/09-05-agents-two-axis-refactor/spec.md`
> **任務卡**：AIR-29（既有 To Do 卡；本次不另建卡、不改卡狀態）

## 實作總覽

### User Story

作為跨 ZCode、Claude Code、Codex companion、Grok Build 與 Muse Code 調度工作的 solo developer，我要以同一份 role 定義描述「誰負責什麼」，再由 harness projection 決定「在哪裡可被叫到」、由 requirement × provider resolution 決定「用什麼能力檔執行」，使新增、修改、刪除角色不再靠人工同步，也不把模型世代或 harness 限制固化進角色語義。

### 核心裁決

1. `agents/roles/` 是 role authoring source；`agents/{zcode,claude}/` 是 generator 管理的實檔 registry；`skills/model-routing/SKILL.md` 是 role→requirement 與 requirement×provider model/effort 的權威來源。
2. dispatch 固定先選 harness／runtime，再按 requirement 語義（旗艦／影像／隨意）解析 provider/model/effort——**正式 token 沿用 tier 詞 `full`／`vision`／`lite`**（與 AIR-24 同源、五檔既有 tier 引用面零改動，不另造第三套詞彙；中文語義標籤只用於表格列名）；role name 不承載 tier、provider 或 harness。
3. 10 個既有 role name 完全不變；EP 規劃、judge、post-build、commit consent 仍由 full 主 session 執行。
4. generated files 帶 ownership marker。stale cleanup 只刪 marker-owned outputs；unmarked file 是人工 fork，永不自動刪。人工 fork 若與 expected output 同名則 fail loud，不覆寫。
5. work-order 保持十個 top-level sections，在 §2 增加 `Role contract` 子段，不讓 §3–§10 consumer 因純重編號漂移。
6. S1 先建立 durable routing source，S2 才 materialize generator；S2 將 role 遷移、兩 registry 重建與 smoke check 視為一個 atomic maintenance checkpoint，禁止在 registry 缺檔的中間態開新 session。

### 複雜度、依賴與風險

- **相對複雜度：高**。難點是 role body、per-harness tools、pins、external work-order、consumer refs 五者的 ownership，不是搬檔本身。
- **順序依賴**：routing source → atomic role migration/projector → consumer/invariant cutover → runtime acceptance。倒序會讓 generator 依賴尚不存在的 policy，或讓 live registry 短暫缺檔。
- **高風險點**：`--check` 偷寫、stale cleanup 誤刪 fork、錯 pin 仍產生綠燈、舊 consumer 引用遺漏、官方 contract 被高報為本機 L4。
- **里程碑**：S1 語義 source；S2 ownership＋生成機械；S3 consumer＋常駐 gate；S4 runtime acceptance。四段皆可各自驗收，不升 Blueprint。

## 段落 0：全域研究

### 現況與可複用基礎設施

- `agents/AGENTS.md:5-19`：`shared/`＋人工 cp 是現行 ownership，並已有 UI 覆寫警告與 real-file 約束。
- `agents/AGENTS.md:56-97`：execution contract 與 projection map 把八個 pinned roles 留在 ZCode-only；現況為 zcode 10 檔、claude 2 檔、shared 2 檔。
- `skills/model-routing/SKILL.md:10-73`：現有 tier／family model facts；`rules/model-routing.md:10-36`：always-on role→tier skeleton。兩者需改成 requirement 語彙，但具體值仍只住 skill。
- `skills/_common/work-order.md:1-95`：現行十節 external-runtime interface；Role contract 應擴充 §2。
- `scripts/deploy_agents.py`：受限 frontmatter parse、dry-run 與 bundle freshness 先例；`pyproject.toml` 無 runtime dependencies，新 projector 不加 PyYAML。
- `skills/scan-project/scripts/check_single_source.py:30-128,448-469`：declarative `INVARIANTS` registry 與 checker dispatch；正確註冊路徑不是 `scripts/check_single_source.py`。
- `tests/test_deploy_agents.py`、`tests/test_check_single_source.py`：tmp_path、pure-check、missing-source、fail-loud 測試形態可複用。
- root、`agents/AGENTS.md`、`skills/CLAUDE.md`、`skills/code-review/SKILL.md`、`skills/memory-audit/SKILL.md`、`rules/model-routing.md` 與 generated role bodies 是已確認的活躍 consumer 面；歸檔 task 只分類、不改寫。
- repo 無 `SYSTEM-MAP.md` 與 task callstack plan；本弧不建立虛構 lifecycle 文件。

### 外部 grounding

- OpenAI 官方 models 文件：Sol 是 flagship、Terra 是 balanced；spec 已裁定 lite（隨意）至少 Terra high 且排除 Luna。來源：<https://platform.openai.com/docs/models>。
- Anthropic 官方 vision/files 文件：current Claude models 可接 image input；vision requirement 應約束 capability，不虛構唯一固定 alias。來源：<https://platform.claude.com/docs/en/build-with-claude/vision>。
- xAI 官方 model page 列 `grok-build-0.1` 的 Text/Image modalities；官方 plugin README 定義 Grok CLI bridge、read-only review 與 model/effort surface。來源：<https://docs.x.ai/developers/models/grok-build-0.1>、<https://github.com/xai-org/grok-build-plugin-cc>。
- Muse `--image` 沿用 `skills/model-routing/SKILL.md:65-73` 的 repo 內記錄；仍需 first-real-usage 補 L4。
- `hooks/AGENTS.md` 的本機狀態必在 build 時重讀；目前證據只足以說 Grok Build local runtime 未驗證，不能因 upstream docs 宣稱本機可用。

### Role requirement 分類

| Requirement（token＝tier 詞） | Roles |
|---|---|
| `full`（旗艦） | `code-reviewer`, `code-reviewer-primed` |
| `vision`（影像） | `vision-review` |
| `lite`（隨意） | `archify-gen`, `cr-research`, `cross-verify-investigator`, `impl-flash`, `lite-verify`, `mem-distill`, `spec-miner` |

### Projection 預演

- task-local plan：`projection/plan.toml`；source：`projection/sources/scripts/sync_agents.py`。
- 預演涵蓋 canonical load、三種 requirement、expected render、owned-output inventory、content comparison、collision guard、marker-owned apply/cleanup、check/map/sync mode 分流。
- `code-reality project` 最新重跑得到 11 條 planned edges、兩個 `[projected][WIRED]` claims；index stamp `b48fe63...` 仍落後 task baseline，S4 落地後必須重建 index。`[projected]` 是 producer 宣告，不是 current-tree correctness evidence。

## UC 盤點

AIR-29 已覆蓋 UC1–UC4，不建立重複卡。既有卡 description 的舊 baseline 與「12 命令檔零改動」已被 spec 推翻；`/implement` 的第一個卡動作必須先設 In Progress，再同步為本 EP baseline 與 consumer reference integrity。規劃階段不提前改卡。

| UC | 能力 | Owner／入口 | 狀態 |
|---|---|---|---|
| UC1 | role authoring single source | `agents/roles/*.md` | 📋 AIR-29 |
| UC2 | harness-first、requirement×provider-second routing | `agents/AGENTS.md`＋`skills/model-routing/SKILL.md` | 📋 AIR-29 |
| UC3 | sync/check/map/stale cleanup | `uv run python scripts/sync_agents.py` | 📋 AIR-29 |
| UC4 | external work-order role contract | `skills/_common/work-order.md` §2 | 📋 AIR-29 |

## Scenario Matrix

保留 spec 的 SM-1～SM-12 identity；external runtime 子路徑用 SM-4a/b/c，不重定義原編號。

| ID | UC | 觸發 | 預期與證據 | Checkpoint／恢復點 | 效能期待 |
|---|---|---|---|---|---|
| SM-1 | UC1–3 | ZCode background spawn 任一 role | 10-role registry/map 靜態完整；L4 指定抽 `lite-verify`、`impl-flash`、`code-reviewer`，核 modelID/variant 與重構前行為 | sync 完成後才開 fresh session；失敗回復舊 registry | spawn 不受 generator 影響；sync 為 O(R×H) |
| SM-2 | UC1–3 | `claude --agent <role> --bg` | 10 名逐一成功；unknown name 立即退出，皆為本機 L4 | fresh session／file watcher 載入點；任一名稱敗即停 | 逐名 probe 有界 10+1，不做無界重試 |
| SM-3 | UC2 | CC Agent tool spawn-time model+effort | requirement→provider→model+effort 查表；文件對帳＋首例實戰補驗，不高報本輪 L4 | first-real-usage record；缺 runtime fact 標 pending | routing 為常數表查找，不引入額外 network probe |
| SM-4a | UC2/4 | Muse 工單 | role contract 引用 roles body，model/effort 查表，bridge 必經；首例實戰補驗 | ledger jobId／blocked record | 不以 LLM 輪詢等待，沿用 push 收法 |
| SM-4b | UC2/4 | Codex companion 工單 | 同上；以 companion contract 派發，首例實戰補驗 | thread/job evidence／blocked record | 工單 body 單份，不重複 role 文本維護 |
| SM-4c | UC2/4 | Grok Build 工單 | 同上；upstream contract 已 grounding，本機缺場則 blocked；不得安裝代替驗收 | local availability gate／blocked record | 缺場立即停止，不做安裝重試迴圈 |
| SM-5 | UC1/3 | 編輯 role body | 只改 roles→sync 兩 registry；明示 UI 手改 generated copy 會被覆蓋 | roles source 是重跑 checkpoint | 讀寫量隨 roles×harness 線性成長 |
| SM-6 | UC2 | 判斷密集任務誤派非旗艦 | requirement table＋AIR-24 擋下；非旗艦＋高 effort 仍標未驗證 | dispatch 前 validation | fail-fast，不啟動錯誤 runtime |
| SM-7 | UC1/3 | 新增 role | 兩 registry 同步；缺 requirement/pin key fail loud | compute 階段、零寫入 | 缺 key 在 render 前 O(R) 發現 |
| SM-8 | UC3 | 手改 generated output | `--check` non-zero 列 drift，content hash＋mtime 證明零寫入 | drift list 是修因 checkpoint | check 為 O(files+bytes)、零寫入 |
| SM-9 | UC1/3 | 刪除 role | 只清 marker-owned stale output；unmarked fork 保留；同名 collision fail loud | owned inventory；失敗不刪任何檔 | cleanup 單次線性 inventory，不掃 repo 外 |
| SM-10 | UC2/3 | vision pin／dispatch 降到無 image model | generator parity 與 model-axis validator 雙擋，fail loud | provider table source status | 純表格驗證，不在每次 sync 查網路 |
| SM-11 | UC3 | single-source 長期 drift | `agents-projection-sync` invariant 執行 pure compare 並 non-zero | checker finding | 複用 projector compare，不重算第二套模型 |
| SM-12 | UC1–4 | 12+ consumer 引用 role name/path | names 零改；活躍 references 全對帳，不用「檔案零 diff」假驗收 | baseline consumer manifest | bounded active roots；archive 只分類一次 |

## S1 Routing Source 與 External Role Contract

### Context

- **承接**：UC2、UC4；SM-3、SM-4a/b/c、SM-6、SM-10。
- **定義端**：`skills/model-routing/SKILL.md:10-73`；`rules/model-routing.md:10-36`。
- **消費端**：`agents/AGENTS.md:56-97`、`skills/agent-workflow/SKILL.md`、`skills/_common/work-order.md:13-18`。
- **Invariant Impact**：無交易 domain invariant；保留 AIR-24 judgment-density invariant 與 Luna exclusion。

### 實作

1. 在 model-routing skill 建立 role→requirement 表與 3 requirements × 5 providers 的權威表；每格為 resolved model/effort、explicit non-default/unsupported，或有 source 的 unverified，不准空白。**分層（spec §7.4）**：model/effort 值的單一源＝既有 tier→(model,effort) 解析表（下層，擴為五公司欄）；3×5 權威表由下層派生（上層只管 requirement 語義與對齊行），parity test 比對「展開表↔下層 tier 表」——不產生第二套 model 值源。
2. `agents/AGENTS.md` 建 harness axis：ZCode registry、CC named agent＋Agent tool、Muse bridge、Codex companion、Grok Build 各一行，說明 transport/provider binding/role source/evidence status。
3. `rules/model-routing.md` 只保留兩跳骨架、requirement 語彙與 AIR-24；requirement 正式 token＝tier 詞（full/vision/lite，AIR-24 同源）——tier 詞彙**保留不退役**（repo 五檔引用面與 AIR-24 措辭依賴）；具體 model strings 不複製進 rule。
4. 三個 vision TBD 結算為 capability constraints：Claude current image-input model、OpenAI multimodal Sol/Terra 按 judgment density、Grok Build image modality；xai「隨意」格並列結算（待查證值或顯式 unsupported-lite，缺值不阻斷其他 provider 行）。Meta 保留非經濟預設；Luna 禁止 lite。
5. work-order §2 增 `Role contract`：role name、requirement（tier token）、canonical path、body/path handoff、body hash（若貼入）；model/effort 回查表。**落位裁定＝§2 子段，推翻 spec UC-4「§4 後」建議**——理由：保持十個 top-level 節，§3–§10 consumer 不因重編號漂移（spec 該建議為非裁決性，已同步回寫）；並與 `agents/AGENTS.md` external-runtime 節互指（單一源在模板）。紅線、baseline、evidence、completion sections 不變。

### 驗證

- table completeness/parity fixture；role names 正好 10 且每名恰有一 requirement。
- 負向：judge/EP/post-build 被 agent 化、lite→Luna、vision→無 image capability 皆 fail。
- work-order top-level headings 仍為 1–10，Role contract 在 §2，原 redlines/completion fields 未失。
- external facts 逐格標 `official-doc`／`repo-observed`／`first-real-usage-pending`；不得把官方 docs 升格本機 L4。

### 成功條件

- generator 可從這個 durable source 抄 policy，S2 parity test 有可查來源；role/harness/provider 三層無反向 ownership。

## S2 Atomic Role Migration 與 Pure Registry Projector

### Context

- **承接**：UC1、UC3；SM-1、SM-2、SM-5、SM-7～SM-11。
- **前置**：S1 routing source 已落地。
- **定義端**：現有 `agents/shared/*.md`＋`agents/zcode/*.md`；`scripts/deploy_agents.py` parser/dry-run 形態。
- **消費端**：`~/.zcode/agents`／`~/.claude/agents` 對 repo registry 的目錄 symlink（`agents/AGENTS.md:3,14-19`）。
- **Invariant Impact**：無 domain invariant；check purity、determinism、marker ownership、missing-policy loud failure 是本段 invariants。

### Atomic maintenance checkpoint

1. 先完成 `tests/test_sync_agents.py` RED：schema、render、check purity、map、add/edit/delete、fork/collision、missing mapping/pin、idempotence、**target 欄位洩漏負向（claude/ 生成物零 `model:` 欄／零 `thoughtLevel`——spec SM-13）**。
2. 實作 `scripts/sync_agents.py` compute-then-apply：所有 parse/render/compare/validation 先完成；`check`／`map` 在任何 mkdir/write/unlink 前 return；sync 才進 mutation boundary。
3. 用 `git mv`：reviewers 從 shared、八個 pinned roles 從 zcode 移至 `agents/roles/`；canonical frontmatter allow-list 僅 `name/description/tools/background`，body 第一節 `## 目標`，零 model/provider/harness/thoughtLevel 字樣。
4. 首次 migration 以一次性顯式 `--adopt-legacy` 對現存 4 個固定 reviewer paths 收編：逐檔把「expected 移除 marker」與既有 bytes 比對——expected 先經 **divergent-tools 渲染**（claude 拷貝＝shared 減 CR MCP 四行；差異權威定義＝`agents/AGENTS.md` 同步紀律節）再逐檔 exact bytes 比較；只有完整舊 topology 且逐檔 exact 才可就地加 marker。default sync 對任何 unmarked 同名檔一律 fail；adoption mode 不接受其他 path，完成後不再使用。
5. 立即執行 adoption/sync 重建 zcode/claude 各 10 實檔，再跑 `--check` 與最小 named-agent smoke；這些步驟是一個 maintenance boundary，途中禁止開新 harness session。任何失敗先恢復 registry 可達性，不留下缺檔中間態。
6. generator projection policy 明列三 tools families：CR MCP、impl-flash Grep/Glob union、reviewers background＋Context7；MCP 全名只在 startup snapshot contract 合法的 target 注入。
7. generated marker 之外的同名檔 fail；stale 只刪 marker-owned。`agents/shared/` 最終消失，不留 tombstone。
8. generated document 第一行必為 YAML opening fence；target-specific fields 寫在 frontmatter，ownership marker 放 closing fence 後、正文前。requirement 只存在 policy/map，不可在 frontmatter 前輸出裸文字；`--check` 逐檔列 drift。

```python
roles = validate(load_roles())
policy = load_copied_policy_with_parity_guard()
expected = render_all(roles, policy)
owned, unowned = inventory_outputs()
drift = compare_bytes(expected, owned)
if mode == "check": return report(drift)
if mode == "map": return print_map(expected)
assert_no_unowned_collisions(expected, unowned)
write_changed_atomically(expected)
delete_marker_owned_stale(owned - expected)
```

### 驗證

- check/map clean 與 drift cases 都以整樹 content hash＋mtime tripwire 證明零寫入。
- exact bytes、deterministic ordering、second-run no diff；新增 role 缺任何 key 先 fail，不產半套 registry。
- exact bytes 另斷言每個 output `startswith("---\n")`、frontmatter 可解析、marker 僅在 closing fence 後出現。
- first-migration fixture 從現行 zcode=10、claude=2、shared=2 topology 完整走到 roles=10、兩 registry=10、shared=0；legacy reviewer 有非允許差異時在任何 write 前失敗。
- `--map` 斷言 10×2 membership＋requirements；parity test 讀 S1 tables 對 generator dict/pins。
- `--map` 固定欄位為 role／requirement／zcode／claude，而非只印 paths；排序、十名集合與每名唯一 requirement 都入 snapshot。
- `git diff --summary -- agents/` 證明 history-preserving renames；canonical roles zero forbidden tokens。
- task-local `code-reality project` 重跑，要求核心 claims 無 HOLE/MISSING；仍標 projected 非 evidence。

### 成功條件

- roles 正好 10、shared 消失、兩 registry 各 10 owned files；`uv run python scripts/sync_agents.py --check` 綠且零寫入。

## S3 Consumer Cutover 與 Single-source Gate

### Context

- **承接**：UC1–4；SM-11、SM-12。
- **前置**：S1/S2 source paths 與 wording 已穩定。
- **雙向錨點**：source=`agents/roles/`＋model-routing tables；已確認 consumers＝root `AGENTS.md`、`agents/AGENTS.md`、`skills/CLAUDE.md`、`skills/agent-workflow/SKILL.md`、`skills/code-review/SKILL.md`、`skills/cross-verify/SKILL.md`、`skills/deep-work/SKILL.md`、`skills/memory-audit/SKILL.md`、work-order、`rules/model-routing.md` 與 generated body links。
- **Invariant Impact**：無 domain invariant；新增 recurring `agents-projection-sync` invariant。

### 實作與驗證

1. 以 `rg -l 'agents/shared|ZCode-only|只改 shared|registry projection map|agents/zcode/(cross-verify-investigator|archify-gen|cr-research|impl-flash|lite-verify|mem-distill|spec-miner|vision-review)' AGENTS.md agents rules skills --glob '*.md'` 建 active consumer manifest；逐檔移除舊教義。上列具名 baseline 是最低 allowlist，動態掃描只負責發現額外 consumer；archive hits 保留並列 excluded evidence。**tier 詞引用面（review-engine/execution-plan/illustrate/blueprint-bootstrap/rules AGENTS.md 等五檔）為保留項不掃除**——tier 詞是正式 token 非舊教義。`agents/AGENTS.md` 改寫附 **keep-list**：Thin forwarder 與 flag profile、dispatch face 與收法、三態判定表、欄位相容策略、tools 清單陷阱、ZCode/Claude 限制六節與重構無關，保留不動；「2026-08-XX 實測/定案」日期註記＝provenance，保留不刪。
2. `skills/scan-project/scripts/check_single_source.py` 登記 `agents-projection-sync`；checker 呼叫 projector pure compare API／`--check`，不得重寫 projection logic。
3. `tests/test_check_single_source.py` 覆蓋 clean、drift、missing source、invocation failure、zero-write；訊息帶 role/target/drift type。
4. 變更 `rules/model-routing.md` 後跑 deploy dry-run 與 `tests/test_deploy_agents.py`。真正寫 `~/.zcode`／`~/.config/opencode`／`~/.codex` 是 outward action：須另取得使用者明確授權，授權後才 deploy＋bundle cmp；未授權則 completion 明示 pending。
5. 跑 `uv run pytest tests/test_sync_agents.py tests/test_check_single_source.py tests/test_deploy_agents.py`（背景）、project ruff/mypy 最小集合、`uv run python skills/scan-project/scripts/check_single_source.py`。

### 成功條件

- active consumer reference integrity 綠，names 零改；single-source checker 真能抓 registry drift，不以散文或「檔案零 diff」代替。

## S4 Runtime Acceptance 與 Closeout

### Context

- **承接**：SM-1～SM-12。
- **前置**：S1–S3 tests/gates 綠。
- **主要消費者**：fresh ZCode session、Claude named-agent/Agent tool、external work-order dispatcher、single-source checker。
- **Invariant Impact**：無 domain invariant；驗 registry reachability 與 evidence honesty。

### 驗收梯度

1. DEPTH-MIN：schema、projector、parity、single-source tests。
2. DEPTH-SAMPLE：ZCode fresh session 精確抽 `lite-verify`、`impl-flash`、`code-reviewer`，以 telemetry modelID/variant 與工具可達性核對，不能信 agent 自述。
3. DEPTH-FULL：Claude fresh session 逐名啟動 10 roles；unknown name loud failure。每名保留命令、exit/status、identity probe 結果。
4. SM-3 與 SM-4a/b/c：docs contract＋首例實戰。環境缺場、額度不足、未授權各自列 blocked；不安裝 Grok Build、不把 schema test 高報 L4。
5. 重建 code-reality index，再查 real generator callers/refs；projection stale warning 消失後才把結構接線升為 current evidence。

### 收尾

- `/implement` 開始時 AIR-29 先 In Progress 並修正卡 baseline/acceptance；全部必做 L4 完成後才 Done＋final-summary＋done ref。
- 跑 post-build 獨立 review→judge→修正→follow-up；聚焦 check purity、cleanup blast radius、role neutrality、runtime false green。
- 更新 task `index.html` badge／evidence；memory 先過寫入六問，任務流水留 EP/card。
- 本 EP 不授權 commit、user-level deployment、plugin install 或 external send。

## 整合策略

- 唯一 baseline：`40f47e8797a69f9a3d455742962df8330421efc5`。實作前若 HEAD 漂移，重跑 status、role counts、consumer manifest、provider facts 與 projection；行號只作本基線錨點。
- S2 是 atomic maintenance segment；S1、S3、S4 各自可獨立結算。測試一律 DEPTH-MIN→SAMPLE→FULL；pytest 背景跑，gate output 不 pipe 到 tail/grep。
- 實作完成後展示 diff 與 commit message，等待獨立 commit consent。

## EP Review Findings

| ID | 嚴重度 | 信心 | EP 段落 | 問題 | 回寫 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| F3-01 | 🟡 important | confirmed | 原 S2/S3 | projector 先於 durable routing source，形成 policy dependency cycle | 改為 S1 routing source→S2 projector，並指定 skill table 為權威、dict 由 parity guard | implemented | ✅ |
| F3-02 | 🟡 important | confirmed | projection | 初版 projection 把非 vision 全標 flagship，只比存在且缺 cleanup/map semantics | 修正 task-local source涵蓋三 requirements、content compare、owned inventory、collision、cleanup、三 modes；重新投影 | implemented | ✅ |
| F3-03 | 🟡 important | evidence-based | 原 S1/S2 | 分段 git mv 會讓 live registry 中間缺檔 | 合併為 S2 atomic maintenance checkpoint，禁止中途新 session，失敗先恢復 registry | implemented | ✅ |
| F5-01 | 🟡 important | confirmed | Scenario Matrix | 初版重定義 SM-3/SM-4，漏 CC Agent tool 與 Muse traceability | 保留 spec IDs，external 拆 SM-4a/b/c | implemented | ✅ |
| F5-02 | 🟡 important | confirmed | SM-1/S4 | ZCode 樣本偏離 spec，且 10-role static completeness 被高報 L4 | 固定抽 lite-verify/impl-flash/code-reviewer；10-role 僅 static，CC 才逐名 L4 | implemented | ✅ |
| F3-04 | 🟡 important | confirmed | projection/S2 | 初次修正版把 marker／裸 requirement 放在 YAML fence 前，generated agent metadata 會失效 | renderer 重建 frontmatter，target fields 留在 YAML、marker 放 closing fence 後；補 exact-bytes parse gate | implemented | ✅ |
| F1-01 | 🔴 critical | confirmed | S2 | 既有 4 個 reviewer copies 無 marker，會被 collision guard 擋住首次 migration | 增 legacy adoption exact-bytes gate 與 current-topology fixture；額外差異在寫入前失敗 | implemented | ✅ |
| F1-02 | 🔴 critical | confirmed | projection/S2 | projection 初稿未忠實表達可載入 frontmatter、pins、tools divergence 與 drift output | 修正 header/pins/tools/filter/drift-list 控制流；完整 exact bytes 留 S2 RED/GREEN | implemented | ✅ |
| F1-03 | 🟡 important | confirmed | Scenario Matrix | 缺 Checkpoint 與效能期待，無法描述中斷恢復與規模行為 | Matrix 增兩欄，逐列標 maintenance/fresh-session/blocked checkpoints 與線性有界期待 | implemented | ✅ |
| F4-01 | 🟡 important | evidence-based | S3 | 已知 cross-verify/deep-work 等 active consumers 未具名，留給實作者重猜 | 寫入具名 baseline allowlist 與可執行 rg pattern，動態掃描只找額外項 | implemented | ✅ |
| F3-05/F1-04 | 🔴 critical | confirmed | projection/S2 | exact-equal unmarked fork 會被常態 sync 誤收編為 generator-owned | adoption 拆成 explicit one-shot mode＋四路徑 allowlist；default sync 對所有 unmarked 同名檔 fail | implemented | ✅ |
| F1-05 | 🟡 important | confirmed | projection/S2 | path-only map 看不見 requirement drift | map 改為 role/requirement/zcode/claude 四欄並加 snapshot gate | implemented | ✅ |

### Judge Review

十二個獨立問題（十三個 finding IDs；F3-05/F1-04 是雙 reviewer 對同一根因的重複命中）均有 spec／現況行號證據且修正收益高於成本，已逐項採納。否證檢查：F3-02/F1-02 即使把 projection 視為示意仍會製造 false-green，不能只降級措辭；F3-04 不能靠「harness 或許容忍 comment」反駁；F1-01 不能靠 atomic wording 消除既有 reviewer collision；F3-05/F1-04 也不能靠 exact-byte equality 區分剛建立的人工 fork。其餘項目亦無可保留原設計的較強證據。F2 review 無新增 finding。

## EP Review Findings（第二輪——獨立 ep-review，2026-09-05 晚）

> 審查基準＝spec R-1~R-11 回寫後版本（EP 產出於回寫前，存在時間差）。9 條全數採納回寫（狀態 implemented）。

| ID | 嚴重度 | 信心 | EP 段落 | 問題 | 回寫 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| F3-A | 🔴 critical | confirmed | 核心裁決2/段落0/S1/SM-6/S2 | EP 全鏈 `flagship/any` 與 spec R-3「tier 詞 full/vision/lite」正面矛盾；projection source 亦 hardcode | **裁定收斂至 spec 方向**：正式 token＝tier 詞（AIR-24 同源、五檔 tier 引用面零改動——反證 EP 原方向 blast radius 更大且 S1.3 引 AIR-24 卻汰 tier 自相矛盾）；全鏈改寫＋projection source 於 S2 實作時以 tier token 重投影（預演產物隨實作再生，不手改） | implemented | ✅ |
| F3-B | 🟡 important | confirmed | S1.1/S2 | R-4 分層裁定失落——權威表單層直值＝第三套值源回歸 | S1.1 改分層：model 值單一源＝下層 tier 解析表（擴五公司欄），3×5 表由下層派生；parity 比對展開表↔下層表 | implemented | ✅ |
| F4-A | 🟡 important | confirmed | S2 RED | spec SM-13 負向（claude/ 零 model:/thoughtLevel）未編入 | RED 清單增 target 欄位洩漏負向 | implemented | ✅ |
| F4-B | 🟡 important | confirmed | S3.1 | R-5 keep-list 失落——agents/AGENTS.md 六營運節＋日期註記恐被整清 | S3.1 增 keep-list 六節名＋日期註記＝provenance 保留 | implemented | ✅ |
| F3-C | 🟡 important | confirmed | 核心裁決5/S1.5 | work-order 落位（EP §2）與 spec UC-4 建議（§4 後）衝突未宣告 | EP 明示推翻理由（十節不重編號、consumer 不漂移）；spec UC-4 已同步回寫為裁定 | implemented | ✅ |
| F1-A | 🔵 suggestion | confirmed | S3.1 | tier 詞引用面（review-engine 等 5 檔）不在 manifest——EP 原方向下為缺口 | 詞彙收斂至 tier 後 5 檔為保留項；S3.1 明示「tier 詞＝正式 token 非舊教義，不掃除」 | implemented | ✅ |
| F1-B | 🔵 suggestion | confirmed | S1.5 | spec UC-4 互指義務（模板↔agents/AGENTS.md external 節）未編入 | S1.5 補互指錨點（單一源在模板） | implemented | ✅ |
| F3-D | 🔵 suggestion | evidence-based | S2 checkpoint4 | 「完全相等（含已知差異）」字面矛盾；差異權威錨點未給 | 措辭改「divergent-tools 渲染後逐檔 exact」＋指名 agents/AGENTS.md 同步紀律節為差異權威 | implemented | ✅ |
| F3-E | 🔵 suggestion | evidence-based | S1.4 | xai「隨意」格未點名結算 | S1.4 明列（待查證值或 unsupported-lite，不阻斷） | implemented | ✅ |

**第二輪 Judge 自查**：非全盤照收 EP 原方向——F3-A 裁定推翻 EP 自身設計（tier 詞回歸），依據＝F1-A 機械證據（五檔 tier 引用）＋EP S1.3 引 AIR-24（tier 措辭）的內部矛盾；方向改判有據非偏好。其餘八條為 spec 回寫裁定編入 EP 的補漏，無語義重裁。
