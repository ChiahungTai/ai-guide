# agents/ — 跨 harness subagent 定義

> 部署＝registry 視圖：`~/.zcode/agents` symlink → `agents/zcode/`、`~/.claude/agents` → `agents/claude/`。與 hooks/ 不同（config 引用、無目錄載入點），subagent 兩家都是**目錄載入點**，symlink 成立。ZCode 設定 UI 的新建/編輯會穿頂層 symlink 寫入 `agents/zcode/`（= 產生 repo working tree diff，屬預期行為）。

## registry 結構（per-harness 指定＝registry membership）

```
agents/
  roles/       # role authoring 單一源（frontmatter 白名單 name/description/tools/background＋零 model/
               #   thoughtLevel 鍵——正文 prose 豁免；body：①目標 ②做法 ③角色特定節〔紀律/方法論等，
               #   skills 引用 inline 散在 body〕；description 不帶 tier 標記——AIR-91 S2 起 requirement
               #   是 presets 相容 token 非 authoring 事實）
  presets.toml # deployment 單一源（AIR-91 S2）：registry slug → harness membership／read-write／sandbox／
               #   background 鏡像（parity gate）／default binding（FK → skills/model-routing/catalog.toml
               #   dispatch_binding；requirement 欄＝--map 四欄相容 token）
  zcode/       # 生成物（~/.zcode/agents → 此）：roles 投影＋presets 解析的部署 pins（model+thoughtLevel）
  claude/      # 生成物（~/.claude/agents → 此）：roles 投影（full 別名釘選 model: opus〔AIR-44——別名可攜〕；
               #   其餘省略 model＝inherit；tools 減 CR MCP 行）
```

- **「指定哪個 harness 用哪些 agent」＝role 出現在哪些 registry**（機制，非命名紀律；現況＝presets.toml 的 harness membership）。**registry 內是實檔拷貝**——理由＝per-harness frontmatter 差異需整檔分歧（zcode pins／claude 減 CR MCP 行），symlink 是整檔單位無法承載差異。ZCode loader 可載入 file-level symlink（2026-09-06 新 session 對照實驗：symlink／實檔探針皆載入，推翻 08-29「檔案 symlink 靜默不載」舊判決——舊判決疑為快照過期混淆）；hardlink 被 clone 破壞不可用，symlink 為 git 原生追蹤
- **同步紀律（生成式）**：**只改 `roles/` 與 `presets.toml`**，改完 `uv run python scripts/sync_agents.py` 重建兩 registry；`--check`＝唯讀 drift gate（生成物 vs roles+presets+catalog 不一致→exit 1 列清單，check_single_source 有 invariant 接線）；`--map`＝role→registry 可用性表（`--map --verbose` 加 preset/binding/token kind/capabilities 欄）；stale cleanup 只刪 marker-owned 生成物——**unmarked 檔是人工檔，永不自動刪**，與 expected 同名的 unmarked 檔＝fail loud（防 fork 被靜默收編）。**已知刻意分歧（2026-08-30 T2-3，由生成器承載）**：claude 拷貝 tools 減 CR MCP 白名單行（`mcp__plugin_code-reality_code-reality__*` 四顆）
- **pin 單一源紀律（AIR-91 S2 起）**：zcode/ 生成檔的 pins 由 `presets.toml` default binding 經 `catalog.toml` 解析生成（wire token／effort encoding 是 catalog 供給事實；loader 驗 FK／carrier 相容／effort 詞彙，違規 fail loud）——改 pin＝改 presets（＋catalog binding）→ 重跑 sync；`presets.background` 與 roles frontmatter 宣告 parity gate（drift＝sync fail loud）。既有 pins 與 AIR-91 前行為逐 byte 等價（tests 等價矩陣 LEGACY_* golden 釘住）
- **UI 防護規則**：不在 ZCode 設定 UI 編輯 registry 檔（model／思考強度／正文皆然）——zcode/claude/ 是**生成物**（檔頭 ownership marker 標記），UI 編輯會被下次 sync **無預警覆蓋**；要改角色 → 改 `roles/` 源；要改 pins → 改 `presets.toml`（**在 zcode/ 建 fork 已非合法形態**——同名 unmarked 檔會擋 sync）
- **tier 命名**：能力語義命名（lite-verify／spec-miner，非具體模型名-*——model 每代換名，改名級聯）；例外＝rescue 類（引擎在本質內，如 codex-rescue）。requirement 相容 token（full/vision/lite）定義在 `presets.toml` allow_lists（tier 語義現行居住處＝`skills/model-routing/SKILL.md` dispatch 預設與 lite 分工律節）
- **生效時機**：ZCode 改動需新建 session（快照制；app 重啟續接同對話亦刷新）；CC 定義檔即時監聽。翻轉頂層 symlink／更新 registry 拷貝後以首個新 session 驗證
- **external-runtime 職責**：本 registry 亦承載 external-runtime 委派的入口指派（family／profile 映射與詞彙定義均見 `skills/model-routing/SKILL.md`——glossary＋family 表）；詳見下節 thin forwarder。

## Thin forwarder（external-runtime 家族入口）

> 治理原則：external-runtime 家族入口＝單一 thin forwarder（工單即介面），**不長特化 agent**——routing 混入 transport agent 的前車之鑑（`~/Github/delegate-bridge/FIX-S3-R2.md:49`）。跨 harness agent 定義保持 thin，路由決策與解析表在 `skills/model-routing/SKILL.md`（詞彙定義見 `rules/model-routing.md` tier 詞彙句），工單協議在 `skills/_common/work-order.md`。

- **原則**：external-runtime 家族（muse／codex／glm）不新增特化 agent 定義檔；任務以工單為介面派發，profile 決定 spawn 參數。
- **派發與收法單一源**：flag 具體值（flag profile → spawn 參數表）、dispatch 形態（bridge 必經、直呼 bridge CLI）、收法（收法決策樹〔fire-and-forget 為頭形態〕／ETA-gate）、transport 三態判定（未啟動／在跑／死中途）——單一源在 `skills/model-routing/SKILL.md`，本檔不複載。
- **flag 未暴露項對策**：以工單紅線替代（見 `skills/_common/work-order.md` 紅線首段），flag 暴露列 delegate-bridge 側 bridge roadmap（本 repo 不動跨 repo，僅記錄）。

## 全生命週期 execution contract

> 每個生命週期段必有一行 contract：stage → owning orchestrator → registry preset（default binding 指針）→ artifact → failure fallback（AIR-28；AIR-91 S2 起 tier 欄改為 preset／binding 指針——judgment／capability demand 的正式表達是 workflow 自有的 work-unit rows〔S3 各 skill 擁有〕，本表只做導航投影）。**「dispatch 給適合的執行者」含主 session**——判斷密集段（EP 規劃／judge 裁決／post-build 編排／commit consent）依 AIR-24 分工律由主 session（decision work unit）執行，不 agent 化。消費側規範（各命令怎麼查表 dispatch、spawn 形態）單一源在 `skills/agent-workflow/SKILL.md`，本表是主體。

| stage | owning orchestrator | registry preset（default binding） | artifact（輸入→輸出） | failure fallback |
|-------|--------------------|-----------------------------------|----------------------|------------------|
| 開卡（backlog 建卡＋建卡 commit） | 主 session 直做 | —（decision work unit） | 任務敘述→卡檔＋commit | —（機械命令，kanban-board skill） |
| 研究（EP 段落 0／規格挖掘） | spawn | **cr-research（zcode→`glm-5.3`——decision／global-research，AIR-76 v3.1 裁升）**；spec-miner（zcode→`glm-5.3-flash`——execution） | 問題→file:line 錨點＋逐字引用 | 重試≤2（1302）→主 session 自做 |
| EP 規劃 | 主 session 直做（判斷密集） | —（decision work unit） | 需求→ep.md（含 EP review 迴圈） | — |
| EP review（雙家族） | 主 session 編排：GLM 側 spawn code-reviewer×2；muse 側**`task` 形態＝`--background` fire-and-forget 提交＋`wait`／`show` 晚收（不佔 agent 並發、不佔 caller session，可跨 session 認領）；`review` 形態仍背景 Bash 阻塞（`review` 無 `--background`）** | code-reviewer（fresh）＋code-reviewer-primed（primed）——preset default＝execution binding（`glm-5.3-flash`）；高保護面／跨邊界語義面＝spawn override 換 decision binding（同 WorkUnitContract 只換 binding／載體——carrier adapter 三路，見 model-routing skill）；muse review（bridge 工單） | diff＋EP→findings→judge 處置表 | classifier／1302 重試≤2→顯式降級記錄；muse 額度不足→in-harness 雙 context（顯式記錄） |
| build 實作段 | 主 session 編排；機械可規格化段 spawn | impl-lite（zcode→`glm-5.3-flash`——execution） | EP 段→code＋測試＋驗證證據 | 失敗家系處置（註 a）→主 session 直做該段；lite 測試＝規格陳述→驗收證據 full 複驗 |
| build 內 Agent Review | spawn（審查配置由風險 profile 推導——單一源＝[review-engine](../skills/review-engine/SKILL.md)「review 執行預設」，掛點＝[implement](../skills/implement/SKILL.md) Agent Review） | 腿組合依 profile（ordinary 單 reviewer／boundary fresh＋intent 分離——見 implement Agent Review rows；可用 preset＝code-reviewer／code-reviewer-primed，高保護面換 decision binding）；錨點驗證＝lite-verify（execution） | diff→findings（錨點驗證後浮出） | 失敗家系處置（註 a）→主 session 自審＋fallback 標記 |
| judge 裁決 | 主 session 直做（判斷密集；不派 agent） | —（decision work unit；seat 非 full 時升級外派 bridge，禁 in-session 降級自判） | findings→✅/❌/⚠️ 處置表 | — |
| post-build 編排 | 主 session 直做（判斷密集） | —（decision work unit；Reviewer legs 依保護面選 execution／decision binding——authority 固定 findings） | 收尾鏈：code-review（審查配置由風險 profile 推導——掛點＝[post-build](../skills/post-build/SKILL.md)）→judge-review→修正→consistency→metadata-sync→殼 refresh | — |
| 機械驗證／consistency gate | spawn | lite-verify（zcode→`glm-5.3-flash`——execution） | 查證清單→逐項機械證據（rg 命中／exit code／file:line） | 失敗家系處置（註 a）→主 session 跑組合命令 |
| 視覺驗收 | spawn | vision-review（zcode→`glm-5.3-flash`——native_vision ∩ binding image_transport；pin 禁降非影像款，生成期防線） | 圖檔→逐張 verdict | 失敗家系處置（註 a）→標「未驗證」（禁主 session 直讀圖） |
| 多源查證 | spawn | cross-verify-investigator（zcode→`glm-5.3-flash`——execution） | 問題＋軸清單→交叉對帳 verdict＋unverified | 軸源缺場→該軸 unverified 不阻斷（skills/cross-verify） |
| commit preparation | 主 session（對帳可 spawn） | lite-verify（finalization 對帳——execution） | working tree→對帳清單＋訊息草稿 | 主 session 直做 |
| **commit consent＋執行** | **主 session 互動（永遠；任何 dispatch 不覆蓋）** | —（decision work unit） | 草稿＋變更摘要→用戶確認→git commit | —（outward-action-consent rule；autonomous 紅線清單例外見該 rule） |
| memory 結案蒸餾 | spawn | mem-distill（zcode→`glm-5.3-flash`——execution，寫入型） | 肥大條目→收斂重寫 | 主 session 直做（寫入六問自檢） |

- **commit 拆兩半**：preparation（finalization 對帳、訊息草擬——agent 可做）＋consent gate（主 session 互動——永遠，contract 表其他行不覆蓋此行）
- **註 a（spawn 失敗態家系——重試語義單一源）**：見 model-routing skill「spawn 失敗態辨識」——1302／classifier unavailable 重試≤2；1301 禁同 prompt 重試；1308 等窗口重置（重置前重派無效）；429 走 backoff／降並發。**禁把「重試≤2」泛化到全失敗類**（實例：1308 重派只會再敗）
- **test-gen（第三家族測試寫手——非常設，P0 最後手段）**：不生成 registry 定義檔、不佔上表 stage 行；啟用條件預寫死＝MVP 實證 pre-RED challenge＋軸B review 擋不住 fixture fidelity 級穿透才啟用（v3.1 測試契約定案——AIR-70 幽靈角色答案反轉）；條件未滿足前，測試寫手委派→拒
- **CC dispatch**：本表 preset 名的全名在兩 registry 皆生成在場——CC `--agent <name>` 全 9 名可用；未知名稱仍立即退出（反向守衛）

### registry projection map

> 跨 harness 可用性的**機械對帳源＝`uv run python scripts/sync_agents.py --map`**（輸出 role／requirement／zcode／claude 四欄表；`--map --verbose` 追加 preset／binding／model identity／token kind／capabilities 欄）；本節文字表是導覽副本，drift 以 --map 為準。生成後全 9 role 在兩 registry 皆在場（roles/ 單一源→雙投影；舊互動圖渲染 agent 已隨其產線退役刪除，AIR-74）。requirement 欄＝presets.toml 的 legacy 相容 token（AIR-91 S2 起 non-routing）。

| agent | requirement | zcode | claude | 備註 |
|-------|-------------|-------|--------|------|
| code-reviewer | lite | ✅ | ✅ | claude 拷貝 tools 減 CR MCP 行（生成器承載的已知分歧） |
| code-reviewer-primed | lite | ✅ | ✅ | 同上 |
| cross-verify-investigator | lite | ✅ | ✅ | 軸＝prompt 參數（AIR-28 S3）；**去 MCP 化**（tools 不掛 CR MCP 全名——cr 軸走 CLI，避免 spawn 綁死「CR plugin 在啟動快照在場」，見下方 tools 清單陷阱） |
| cr-research | full | ✅ | ✅ | decision／global-research（AIR-76 v3.1 裁升；zcode default binding＝`glm-5.3`、claude＝`opus` 別名——此行曾 drift 為 lite，AIR-91 S2 修正） |
| impl-lite | lite | ✅ | ✅ | **範式但書**：其 tools 行含 `Grep`/`Glob`——ZCode 靜默忽略死欄（見「tools 清單陷阱」），新定義不照抄，文字/檔案搜尋走 Bash rg/fd |
| lite-verify | lite | ✅ | ✅ | — |
| mem-distill | lite | ✅ | ✅ | — |
| spec-miner | lite | ✅ | ✅ | — |
| vision-review | vision | ✅ | ✅ | 影像需求（native_vision ∩ image_transport）——pin 禁降非影像款（生成期防線） |

## harness 軸（dispatch matrix——每家怎樣調用 role）

> dispatch 兩跳：先選 harness（本表），再取該 harness 的 named preset 生成檔（pins 已由 `presets.toml` default binding→`catalog.toml` 材料化在 frontmatter）；需偏離 default 時走 carrier adapter（spawn override 換 binding，或 main／bridge 換載體——見 [model-routing](../skills/model-routing/SKILL.md)）。role 定義單一源＝`roles/`（見 registry 結構節）。

| harness | provider 綁定 | 調用形態 | role 來源 | evidence status |
|---------|--------------|---------|-----------|----------------|
| zcode | zai | registry spawn（背景；快照制——新 session 載入） | `agents/zcode/` 生成檔（pins＝部署預設） | repo-observed |
| cc（Claude Code） | CC 詞彙面（sonnet/haiku/opus）——背後接線 machine-local（user 維護）；原生家 Anthropic 未訂閱，訂閱後 user 自換 | `--agent <name> --bg` named-agent＋Agent tool（spawn-time model/effort） | `agents/claude/` 生成檔 | repo-observed（2.1.261 實測：named-agent 可用、未知名稱即退出） |
| muse code | meta | **雙身分**：user 直用開發 harness（該弧主力，muse-spark-1.3 全棧）＋ ZCode 端 bridge 工單委派（`task`／`review`，必經） | 直用＝repo AGENTS.md 載入（全域部署點未查證）；委派＝roles/ body 填工單 Role contract（work-order §2） | repo-observed |
| codex | OpenAI | **經 delegate-bridge `task --family codex` 工單**（AIR-47 吸收；raw CLI 語義留 memory reference） | 同上 | repo-observed |
| grok-build | xai | 工單（同族委派 plugin 形態） | 同上 | **未安裝**·dispatch contract 未證實〔hooks/AGENTS.md〕——引用前先查證，不得假設可用 |

## 定義檔慣例

markdown + YAML frontmatter，正文 = 系統提示詞。兩家必填欄位同為 `name` / `description`（主 agent 依 description 決定何時委派 — 寫清楚觸發時機）。

### 欄位相容策略

| 類別 | 欄位 | 說明 |
|------|------|------|
| 直接共用 | `name` / `description` / `color` / `maxTurns` / `disallowedTools` / `tools` | tools 只列 built-in 共通名（Read / Bash / Edit / Write / WebFetch / WebSearch / TodoWrite）；`Grep`/`Glob` 是 Claude built-in 名，ZCode runtime 未注入但靜默忽略不報錯（見「tools 清單陷阱」） |
| 省略共用 | `model` | 省略＝inherit 僅存於 CC 投影（Claude 別名 sonnet/opus/... 在 ZCode 無效）；ZCode 端 pins 由 presets default binding 生成、全 preset 覆蓋（full 亦釘——AIR-43），生成檔不省略 |
| 可寫（ZCode 安全忽略） | Claude 專屬：`permissionMode` / `skills` / `hooks` / `memory` / `background` / `isolation` / `effort` / `initialPrompt` | ZCode 官方明說未知欄位靜默忽略不報錯 |
| 禁寫進共用檔 | ZCode 專屬：`thoughtLevel` / `injectAgentsMd` | Claude 對未知欄位容忍度未明 — 需要 per-harness 差異時另建 fork 檔 |
| 語義有差 | `mcpServers` | 兩家都吃名稱參考；ZCode 精確匹配、宣告未連接的服務直接失敗；**同名 server user-level 蓋 project-level**（官方文檔「項目配置覆蓋不了」——user 條目缺專案條目的 headers 會 shadow 專案設定，2026-08-22 實測險釀 lsp-python 回歸後回退）；Claude 另支援 inline 定義 |

### tools 清單陷阱（ZCode）

自訂 tools 清單會排除 **user-config MCP 工具**（設定 UI 勾選清單只含 built-in）；harness 隨附 MCP 不受 allowlist 影響（2026-08-22 實測：自訂清單下 `mcp__4_5v_mcp__analyze_image`、`mcp__web_reader__webReader` 仍注入，`mcp__context7__*`/`mcp__zread__*` 等全部排除——官方文檔「排除全部 MCP」宣稱不精確）。補救：手寫 `mcp__<server>__<tool>` 全名（萬用 `mcp__server__*` 無效靜默忽略——官方文檔宣稱；全名補救已本地驗證——2026-08-22 新會話 probe：5 個全名全部注入，context7 實呼成功、zread 工具存在可呼叫）。需要 MCP 的角色（如 lsp-python）**tools 留空**繼承全部。不認得的工具名靜默忽略、spawn 不報錯：`Grep`/`Glob` 寫進 tools 行在 ZCode 不注入（2026-08-22 probe 實測＋telemetry 全歷史數萬次調用零 Grep/Glob；官方文檔勾選清單仍列二者——文檔與 runtime 不一致）→ 共用定義可列兩家 union，ZCode 端文字/檔案搜尋由 Bash rg/fd 承擔。未連線 server 的全名則是 **spawn 直接報錯**（2026-08-22 實測：tools 列 `mcp__crg__*` 全名在非 mosaic session spawn 失敗，報 "Required MCP tool is not available in the parent startup snapshot" 並列出缺失工具）——全名補救只對 user-level server **且該工具在 spawn session 啟動快照在場**的形態安全；專案層 server（如 mosaic 的 CRG/lsp-python）全名跨專案即炸，不可寫進共用 user-level 定義，需要時另建該專案專用 fork 定義。**通則（2026-08-29 vision-review 實例）**：白名單掛任何 MCP 全名＝綁死「該工具在 spawn session 的啟動快照在場」——連 harness 隨附 MCP 都有不快照在場的 session 形態；跨 session 形態的 agent 定義應去 MCP 化（tools 留空繼承全部，或改 Bash/curl 等替代路徑）。

### 背景執行

**新增 agent 定義一律 frontmatter 帶 `background: true`**（user 明確確認要前景才可省）。既有長任務角色（review / research 類）補齊此欄位 — Claude 端強制始終背景執行（即使主 agent 需要結果）。ZCode **不認識此欄位**（靜默忽略）— ZCode 端背景化是 spawn 端行為：官方文檔僅說前台/後台由主 Agent 自行決定（無 UI 開關、無參數記載），Agent tool 的 `run_in_background: true` 參數為 runtime 實測有效（2026-08-14 session：背景 spawn 成功、主對話未阻塞）。

## ZCode 限制（共用定義的邊界）

- Beta 僅 user 級（無 workspace 層）；內建 `general-purpose` / `Explore` 名稱不可複用（不可建同名覆蓋檔 — Claude 端可以覆蓋 Explore，這是兩家不對稱點）
- 內建 `general-purpose`／`Explore` **無 registry pin——繼承 spawning session 主模型**（ZCode 設計行為，官方 qa 文檔；設定頁可為內建單獨釘模型）；lite 角色任務誤派 general-purpose＝旗艦跑機械段（AIR-50 弧兩次實例）——要省成本層必派 registry lite agent
- 子智能體內**不能再派發子智能體**（Claude 可多層巢狀——官方文檔對深度上限記載版本間不一，勿釘死數字）→ 共用的系統提示詞不可依賴「spawn 下屬 agent」
- 定義修改不熱更新——快照在 session 啟動時建立（同 hooks 行為；2026-08-22 實測雙層快照：新檔案同 session 不進 registry、既有檔的 body 與 tools 修改同 session spawn 均不生效；重啟 app 後**續接同對話即刷新**——session id 不變但快照已更新，無需開新對話）
- 自 v3.7.1 起子智能體預設注入 user 級 + workspace AGENTS.md（與 Claude subagents 載入 CLAUDE.md layers 對稱）
- Beta 灰度上線 — 可用性以「設定 → 子智能體」面板實測為準

## Claude 限制

- 檔案監聽僅涵蓋 session 啟動時已存在的 agents 目錄 — 首次建立本目錄（symlink）後需重啟一次載入
- 需要隔離副本的角色用 `isolation: worktree`（ZCode 無對應，靜默忽略）
