# EP：任務特化 agent 體系＋全生命週期 agent 化＋workflow 形態（AIR-28）

> **ep_type**: implementation（docs mode——product scope 全為 .md：agent 定義/skills/rules；無 executable source）
> baseline: 9cebabd（初稿於 55d128a；平行 session 七 commit 已對時吸收——S4-P2 完成〔75d4221〕、errs CC 化〔AIR-27/e5cbfa1〕、external-runtime 收法 push 化〔AIR-26/4b1950d〕、HASH_RE 補強〔cb3150c〕、寫入六問〔58ada07〕、kanban 建卡即 commit＋防撞預掃〔ad671ba〕）
> 定稿：09-05 雙家族 EP review（muse 16＋codex 8 findings）→ judge 24 條處置（22 全採＋R2 部分採納）→ 全數回寫——處置表見文末

## 實作總覽

**User Story**：作為 solo developer，我要讓「開卡→EP 規劃→build→review→post-build→commit」全生命週期每一段都有**可解析、可啟動、可回收、可驗收的 execution contract**——多數段 dispatch 給任務特化 registry agent（model/effort/tools 按 AIR-24 分工律對號），判斷密集段（judge／EP 規劃／post-build 編排）依 AIR-24 明文由 full 主 agent 執行、commit 的 consent gate 永遠在主 session——兩端載體分流（CC 原生 Workflow／`--agent --bg`；ZCode 模式等價），吸收 Anthropic plugin review 方法論（P1-P6）＋cross-verify 泛用編排。

**已決策勿重辯**（user 09-05 逐項裁定＋review 後增補）：

1. **全生命週期 execution contract**——每段必有一行 contract（stage→owning orchestrator→registry name→tier→harness registry→artifact→failure fallback）；「dispatch 給適合的執行者」含**主 session**（判斷密集位不 agent 化——AIR-24 分工律）
2. **兩端載體**：CC 原生（Workflow＋`claude --agent <name> --bg`）；ZCode 模式等價（findings 落檔＋背景 agent 群＋skill 即 script）——方法論共用、載體分流
3. **特化 agent 按 tier 對號**（含 effort 各家族詞彙對譯）；**archify 先不拆**——既有 `archify-gen.md` 為 canonical 殼 owner（同一 lifecycle responsibility 只一個 canonical agent），assembler/narrative 拆分改「實證痛點後再議」；registry projection 跨 harness（shared→zcode/claude）或逐項標 ZCode-only
4. **P1-P6 採納／P7 不採**；P2 依適用範圍**拆分流**（review-engine 只收全命令適用條款；HIGH SIGNAL filter 屬 code-review profile）
5. **cross-verify 泛用命令**：源枚舉制（web 軸須顯式點名）、機械交叉對帳、unverified 標記；investigator＝**單一參數化 agent 檔**（不長六檔——對齊 agents 治理「不長特化」原則）
6. **agent-view 輕接線**：`--agent --bg` 為 CC 端分發機制；**ownership state machine 必須閉環**（dispatch ref→worktree/branch→attach 驗收→consent→commit→rebase 回收）
7. **報告殼分工**：archify-gen（lite 產線）＋篩選敘事（full）＋視覺驗收（vision）——分工註記落 illustrate html-mode
8. 已對時不重做：S4-P2、errs CC 化（AIR-27）、push 收法（AIR-26）、寫入六問、HASH_RE 補強；AIR-24/25/26/27 已落地者不重做

## UC 盤點（元專業：受影響面清單）

| 面向 | 檔案 | 段 |
|------|------|-----|
| agent registry | `agents/zcode/`（九檔現況：archify-gen/code-reviewer×2/cr-research/impl-flash/lite-verify/mem-distill/spec-miner/vision-review）＋`agents/shared/`＋`agents/claude/`（projection）＋`agents/AGENTS.md`（治理段＋execution contract 表） | S1 |
| tier/effort 單一源 | `rules/model-routing.md`＋`skills/model-routing/SKILL.md`（effort 家族對譯表——缺則補） | S1/S6 |
| review 引擎（僅全命令適用條款） | `skills/review-engine/SKILL.md`（P3 限縮版 preamble／P5 冗餘分流註記——落點指明：quorum 配置在 code-review SKILL＋workflow-review-pattern） | S2 |
| 審查命令 profile | `skills/code-review/SKILL.md`＋`skills/code-review-and-quality/SKILL.md`（P2 HIGH SIGNAL filter＋P4 適用範圍＋P6 Correctness checklist） | S2 |
| Workflow 執行 | `skills/_common/workflow-review-pattern.md`（分級 verify node——**錨點修正：非 review-engine**） | S2/S5 |
| 機械驗證 | `agents/zcode/lite-verify.md`（P1 錨點驗證擴項——口徑統一：併 lite-verify，不另建 findings-verifier） | S2 |
| 新 skill | `skills/cross-verify/SKILL.md`＋`agents/zcode/cross-verify-investigator.md`（單一參數化） | S3 |
| 生命週期接線 | `skills/agent-workflow/SKILL.md`（execution contract 表主體）、deep-work/execution-plan/implement/post-build/commit 各一行形態註記（互指單源） | S4 |
| 報告殼 | `skills/illustrate/SKILL.md`＋`_common/illustrate-html-mode.md`（分工註記＋機械底稿定義） | S4 |
| CC 端 | workflow-review-pattern（verify node）＋deep-work substrate 段（state machine＋兩互動） | S5 |
| 索引 | `skills/CLAUDE.md` | S6 |

SYSTEM-MAP：無（元專案）。

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 |
|---|------|------|---------|
| SM-1 | 互動 session 開新弧 | user 下任務 | execution contract 表逐段生效（每段有 owning orchestrator＋registry name＋fallback） |
| SM-2 | findings 浮出前 | reviewer 產出 Important+ finding | lite-verify 機械錨點驗證（file:line/符號屬實）——假錨點不浮出；驗證≠裁決 |
| SM-3 | 多源查證 | `/cross-verify <問題> <軸>` | 軸群（枚舉源）平行取證→交叉對帳→verdict＋unverified；web 軸未點名不存在 |
| SM-4 | ZCode 背景 agent 群中斷 | session 殺/斷電 | findings 已落檔，新 session 從檔案接手 |
| SM-5 | archify 殼生成 | illustrate html-mode | archify-gen（lite 產線）→篩選敘事（full）→vision 驗收；**數據宣稱只從機械底稿帶入**（＝delta_tour 輸出、archify JSON、命令輸出原文）＋確定性再生 diff |
| SM-6 | CC 長程自主弧 | `claude --agent <name> --bg` | 特化 agent 為 session 主體；收尾**不 auto-commit**（commit-consent take precedence）**且變更可回收**（state machine 走到 consent→commit→rebase） |
| SM-7 | spawn 失敗 | 1302 帳號級 | 重試≤2→顯式降級記錄（AIR-24 定版） |
| SM-8 | agent 定義缺 model pin | spawn 時 | 靜態 schema：full/shared＝省略 model（非字面 inherit）；ZCode lite/vision＝model＋thoughtLevel；缺→S1 補齊歸零 |
| SM-9 | **cross-verify 源缺場** | db.sqlite 缺場／CR 未連線／web 未點名 | 該軸記 unverified、不阻斷合成（[WARN] degraded） |
| SM-10 | **CC 端未知名稱** | `--agent <不存在的名>` | session 立即退出（agent-view.md:438）——S5 驗收含 unknown-name failure 測試 |
| SM-11 | **背景 worktree 未 commit 回收** | override 生效、產物在 `.claude/worktrees/` | owning session attach 驗收→consent→commit→rebase 回主線（state machine 不允許變更滯留失蹤） |

## 段落 0 研究摘要（已完成——引用不重跑）

- **P1-P7 證據釘 SHA** `d7dbd9a0`——引文逐字核（雙家族獨立核對一致）；**吸收時禁照抄**（內部殘留 errorIds/Sentry/Statsig/logForDebugging/logEvent——殘留掃描 pattern 用全五詞）
- **CC 文檔已讀**：workflows.md（計畫在 script/中間結果在變數/可 resume）；agent-view.md（`--agent --bg`、supervisor、worktree isolation〔基於 committed state——看不到 uncommitted〕、git instructions take precedence〔:506，列舉 task/CLAUDE.md/memory——**rules/ 檔路徑覆蓋與否＝S5 實測點**〕、未知名稱立即退出〔:438〕）
- **分工律已定版**（AIR-24）；**push 收法已定版**（AIR-26——wrapper 僅單發轉發，輪詢＝主 session 背景 Bash 直呼 companion/bridge）
- **registry 現況（review 後修正）**：九檔（見 UC 表）——含 archify-gen（AIR-26 建的殼產線 agent）與 impl-flash（平行 session）
- **review-engine 收進判準**（:11「所有 review 命令都適用」）＋ Correctness lens/checklist 分界（checklist 屬 code-review-and-quality）＋ Workflow 執行住 workflow-review-pattern——S2 落點依此分流
- **風險假設**：高——平行 session 活躍（impl-flash untracked 在場）——實作 session 每段開工前 `git log` 對時＋防撞預掃；中——CC 端 `--agent --bg` 對 frontmatter 讀取未實測→S5 L4；thoughtLevel sticky 不達 wire→S1 runtime 抽查

## S1：任務型別×agent×tier——execution contract 與 registry 落地

**Context**：EP 真正賭注不是 agent 數量而是**分發紀律**（muse 深層思考）——contract 表＋tier 對號＋錨點驗證三件。
**要點**：

1. **execution contract 表**（落 `agents/AGENTS.md` 治理段）：`stage｜owning orchestrator（主 session 直做／spawn agent 名）｜registry name｜tier｜harness registry（zcode/claude/shared）｜artifact（輸入→輸出落點）｜failure fallback（1302 降級路徑）`——行×主體無空缺；**commit 拆兩半**：preparation（agent 可做）＋consent gate（主 session 互動，永遠）
2. **registry projection**：每個跨 harness agent 明列 authoring source 與 `shared→zcode/claude` projection；ZCode-only 者逐項標記（CC dispatch 表不得引用 ZCode-only 名稱）
3. **新 agent**：`cross-verify-investigator`（lite 參數化單檔——軸＝prompt 參數；工具接線沿 code-reviewer-primed 的 CR MCP 全名先例＋snapshot 在場 caveat，db/log/git 軸走 Bash）；archify 拆分**撤銷**（archify-gen 為 canonical；實證痛點後再議）
4. **既有九檔逐檔核 effort 定義**：靜態 schema——full/shared 行＝**省略 model**（禁字面 `model: inherit`、禁寫 thoughtLevel〔綁具體 model，inherit 時死欄〕）；ZCode lite/vision 行＝`model`＋`thoughtLevel` 必填；CC 面＝spawn-time `effort`。**effort 家族對譯表**（ZCode thoughtLevel／CC effort／muse low~ultra／codex reasoning）單一源在 model-routing skill（缺則本弧補）
5. **驗收兩層**：靜態 rg（schema 判定如上）＋**runtime 抽查**——各抽一 lite/full agent，per-message modelID（db.sqlite）驗 model 與 effective effort 真達 wire（歸因紀律；sticky thoughtLevel bug 家族）
6. impl-flash 為範式**加但書**：tools 的 Grep/Glob 是 ZCode 靜默忽略死欄——文字/檔案搜尋走 Bash rg/fd，新定義不照抄

**驗證**：contract 表行×主體無空缺（rg）；registry↔矩陣一一對應；runtime modelID 抽查記錄；`uv run python scripts/deploy_agents.py`（rules 觸面時）。

## S2：review 體系吸收 P1-P6（依 profile 邊界分流）

**Context**：review-engine 只收全命令適用條款（:11 判準）——plugin 的 HIGH SIGNAL 是 PR bug-review policy，全域化會壓掉 ep-review/audit 的合法 Important/Suggestion（codex R4）。
**要點**：

- **P2 拆分流**：(a) `code-review-and-quality`（或 code-review SKILL）新節＝HIGH SIGNAL filter 六條全收（含 muse F4-1 補的「appears-bug-but-correct」＋「quality 類僅 instruction 明示才報」——後者在本 repo 是 load-bearing）＋pre-existing 對齊 mixed-tree 歸因；(b) `review-engine` 只收**全命令適用**的 attribution/noise 條款（如「宣稱須附機械證據」既有條的強化）
- **P3 限縮版**（review-engine spawn 模板節）：措辭＝「不做無目的 capability probe；每個 tool call 有明確證據目的；工具實際失敗走既有 `[WARN]`＋fallback，**不把 All tools functional 當 runtime fact**」——相容 degraded contract
- **P5** → quorum 配置落點指明：code-review SKILL＋workflow-review-pattern（review-engine 無 quorum 節）
- **P4** → code-review 模式 B primed 餵料段：審某檔只適用同路徑/祖先路徑 AGENTS.md；「最近者優先、子層覆寫上層」**標為本弧新決策**（source 無此語義，與既有階層慣例對齊）
- **P1** → code-review 模式 B：Important+ findings 浮出前 lite-verify 錨點驗證（批次清單）；lite-verify 定義加「findings 錨點屬實性」項（口徑統一：併 lite-verify）
- **P6** → `code-review-and-quality` Correctness 段（checklist 層）：錯誤處理點枚舉（try/except/callback/fallback default/optional chaining/log-and-continue）→每點五維；通則化重寫；diff 語義觸發

**驗證**：rg 殘留（DO-NOT-FLAG 六條單源於 profile 層；`errorIds|Sentry|Statsig|logForDebugging|logEvent` 全 repo 零命中）；`/consistency`；錨點複核（六軸/Workflow 落點）。

## S3：cross-verify 泛用 skill＋參數化 investigator

**Context**：deep-research 模式吸收（源枚舉制）；今日三軸鑑識＝原型。
**要點**：`skills/cross-verify/SKILL.md`——輸入（問題＋軸清單：db.sqlite/git/log/memory/CR graph/web〔顯式點名〕）；單一 `cross-verify-investigator` agent 參數化派發（背景群＋落檔 `.agent-tmp/cross-verify/`）；交叉對帳（宣稱 vs 機械證據逐條）；合成（verdict＋unverified＋機械錨點）；**源缺場→該軸 unverified 不阻斷**（SM-9）；受眾＝軌道①（產出可直接餵 judge-review）。
**驗證**：與 lite-verify/agent-workflow 引用一致；一次 L4 試跑（小問題兩軸）＋**一次源缺場試跑**（拔一軸源驗 unverified 行為）。

## S4：全生命週期 execution contract 接線

**Context**：「不在 deep-work 也照這作法」；表主體落 agent-workflow（spawn 規範的家），各命令互指不重抄。
**要點**：agent-workflow 新節＝S1 contract 表的消費側規範（各階段怎麼查表 dispatch）；deep-work 加「各段形態引用」；execution-plan/implement/post-build/commit 各加一行形態註記（指 agent-workflow 單源）；illustrate html-mode＋illustrate SKILL 補殼分工註記（SM-5：archify-gen/full 篩選/vision 三 tier＋機械底稿定義＋確定性再生 diff）。
**驗證**：`rg "execution contract"` 單源；`/consistency`；CLAUDE.md 索引行更新。

## S5：CC 端接線（Workflow 分級＋agent-view state machine）

**Context**：CC 原生載體；research preview 風險標註。
**要點**：

- workflow-review-pattern（**錨點修正**）補分級 verify node（lite 錨點批次 vs Critical quorum）
- deep-work substrate 段補 `--agent <name> --bg` 形態＋**ownership state machine**：從 committed ref dispatch（worktree 看不到 uncommitted——依賴先 commit 或主 session attach 餵）→ agent 結果落 worktree/branch → 無 commit 時 owning session attach 驗收 → consent gate → commit → rebase 回主線
- 兩互動條款：worktree isolation 對齊 trunk+多 WT 線模型（產出回主線走 rebase 慣例）；auto-commit override——**實測以 rules/ 檔的 commit-consent 為唯一 override 源**（agent-view:506 列舉 task/CLAUDE.md/memory，rules/ 路徑覆蓋與否正是待驗證點；未過標〔未驗證〕）
- **L4 驗收雙面**：不 outward（無 auto-commit/push）**且可回收**（變更可被 owning session 找到→驗收→進既定 branch）；**逐一啟動每個新增 CC 名稱**＋unknown-name failure 測試（SM-10）

**驗證**：文檔引用對鏡像行號；`--agent --bg` L4 雙面實測（實作 session，結果入完成報告）。

## S6：收尾

1. tier/effort 對譯表、registry、索引同步（skills/CLAUDE.md、agents/AGENTS.md）
2. `/sync-sources` 綠；rules 觸面→`uv run python scripts/deploy_agents.py`（三 bundle 同步綠——zcode/opencode/codex 三部署檔 cmp 一致）
3. 卡 AIR-28 結案兩步＋弧結案蒸餾（寫入六問制下首 dogfood）
4. 任務 brief 殼：**基礎款變體**（illustrate-html-mode 變體表選「基礎款」）落任務家 `index.html`；機械底稿＝delta_tour 輸出／archify JSON／命令輸出原文
5. 實作 session 完成報告含 L4 實測結果（cross-verify 兩試跑＋`--agent --bg` 雙面＋runtime modelID 抽查）

## 整合策略

- 依賴序：S1→S2/S3/S4；S5 獨立；S6 最後
- baseline: `9cebabd`；實作=新 session（本 session 僅 EP＋建卡＋review 定稿）
- 防線：平行 session 活躍——實作每段開工前 `git log` 對時＋防撞預掃（ad671ba 新制適用 agent 定義面）；2.8 finalization 對帳閘門照常

## EP Review Findings（09-05 雙家族——muse job-mtntj8uc-v6hog9＋codex task-mtntii2z-inhdm8；judge 24 條）

| ID | 嚴重度 | EP 段落 | 問題摘要 | 處置 |
|----|--------|---------|---------|------|
| codex R1 | 🔴 | S1/S5 | CC named-agent 缺 registry projection（agents/claude/ 僅兩 reviewer；SM-6 測不出新名稱） | ✅ S1 要點 2＋S5 逐一啟動＋SM-10 |
| codex R2 | 🔴 | S1/S4 | lifecycle 角色未材料化；「每段 dispatch」與 commit 主 session 字面衝突 | ⚠️ 部分採納：execution contract 表（含 owning orchestrator 欄）＋commit 拆 preparation/consent；**不採**「card/judge/post-build 新增 agent 定義」（違 AIR-24 判斷密集位裁決） |
| codex R3 | 🔴 | S4/S5 | worktree＋禁 auto-commit＋rebase 回收不閉環（rebase 只搬 committed；worktree 看不到 uncommitted） | ✅ S5 state machine＋SM-11＋L4 雙面 |
| codex R4 | 🔴 | S2-P2 | HIGH SIGNAL 全域化會壓掉 ep-review/audit 合法 findings（review-engine 只收全命令適用） | ✅ P2 拆分流（驗證：:11 判準逐字核） |
| codex R5／muse F3-1 | 🟡 | S2-P6 | 六軸/checklist 錨點錯檔（正確源＝code-review-and-quality） | ✅ S2 P6 落點修正 |
| codex R6 | 🟡 | S2-P3 | 「All tools functional」與 degraded contract 衝突 | ✅ P3 限縮措辭 |
| codex R7／muse F3-4 | 🟡 | 段0/S1 | registry 漏 archify-gen；新 assembler 與其 ownership 重疊 | ✅ 先不拆（archify-gen canonical）；inventory 修九檔 |
| codex R8／muse F3-3 | 🟡 | S1 | frontmatter rg 驗不了生效；inherit 表示法未定義；thoughtLevel sticky | ✅ 兩層驗收（schema 判定＋runtime modelID 抽查） |
| muse F1-1 | 🟡 | S4 | dispatch 表缺執行主體欄 | ✅ 併 R2 contract 表 schema |
| muse F1-2 | 🟡 | S1/S3 | investigator 基數未定 | ✅ 單一參數化檔 |
| muse F4-1 | 🟡 | S2-P2 | DO-NOT-FLAG 漏兩條 | ✅ 補入（隨 R4 分流落 profile 層） |
| muse F5-1 | 🟡 | SM | 缺源缺場場景 | ✅ SM-9＋S3 試跑 |
| muse F1-3 | 🟡 | S6/SM-5 | 殼驗收不可判定＋機械底稿未定義 | ✅ S6.4 變體選定＋定義 |
| muse F3-2 | 🟡 | S2/S5 | Workflow 施工錨點錯檔 | ✅ 改 workflow-review-pattern |
| muse F3-6 | ℹ️ | S1/S2 | findings-verifier 口徑不一 | ✅ 統一併 lite-verify |
| muse F3-7 | ℹ️ | S2-P4 | 「最近者優先」是外加語義 | ✅ 標為本弧新決策 |
| muse F3-8 | ℹ️ | S1 | impl-flash 範式含死欄 Grep/Glob | ✅ 範式但書 |
| muse F3-5 | ℹ️ | S3 | CR MCP 接線須沿先例＋snapshot caveat | ✅ S3 要點 |
| muse F4-2 | ℹ️ | S2 | 殘留 pattern 漏 logForDebugging/logEvent | ✅ pattern 擴五詞 |
| muse F5-2 | ℹ️ | S5 | override 實測須以 rules/ 檔為源 | ✅ S5 明寫 |
| muse F1-4 | ℹ️ | S6 | 3/3 縮寫未展開 | ✅ S6.2 展開 |
| muse F1-5 | ℹ️ | 整合 | 「2.8」無前件 | ✅ 展開為 finalization 對帳閘門 |
| muse F2/F3 pass 項 | — | — | F2 合規 pass；P1/P3/P5/P6 引文／`--agent --bg` grounding 屬實 | 佐證採納 |

**judge 自查（三防線②）**：非全採納（R2 部分採納＋一建議明確不採）；否證抽查——R4/R5 逐字核 review-engine:11 判準與 lens/checklist 分界、R1 對照 agents/AGENTS.md:14 registry 結構、R3 對照 agent-workflow:106 worktree committed-state 慣例——均屬實。
