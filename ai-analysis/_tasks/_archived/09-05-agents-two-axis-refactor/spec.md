# Spec：agents registry 兩軸重構（role × dispatch × harness 正交）

> **狀態**：定稿需求源——`/execution-plan`（codex 執行）以此為唯一需求輸入，自足可讀、不依賴任何對話歷史。
> **前序弧**：AIR-28（c83ddf4，已結案）建了 10 個特化 agent registry＋execution contract 表——本 spec 處理其部署面缺口。
> **沿用規範**：instruction-writing（元資訊禁令——agents/ 文檔禁版本號/日期/統計）、kanban-board（建卡合約）、model-routing（tier 語義與解析表）、outward-action-consent（commit 確認）。

## 1. 背景與現況

### 1.1 體系現況（repo：ai-rules）

- **agent registry**：10 個特化 role——code-reviewer（fresh-eyes 審查）、code-reviewer-primed（帶 context 審查）、cr-research（EP 段落 0 研究）、spec-miner（凍結源碼/文檔逐字挖掘）、impl-flash（EP 段落 TDD 實作）、lite-verify（機械驗證/consistency gate/findings 錨點驗證）、archify-gen（圖/殼產線）、mem-distill（memory 蒸餾，唯一寫入型）、vision-review（視覺驗收）、cross-verify-investigator（多源查證，軸＝prompt 參數）
- **目錄結構**：`agents/zcode/` 10 檔（ZCode registry＝`~/.zcode/agents` symlink 目標；8 檔帶 `model: glm-5.3-flash`＋`thoughtLevel: high` pins，2 個 reviewer 檔無 pin）＋`agents/claude/` 2 檔（僅 reviewer，Claude registry＝`~/.claude/agents`）＋`agents/shared/` 2 檔（reviewer 的 authoring 源）——**部署靠手動 cp 紀律**（agents/AGENTS.md「同步紀律」節），無 drift 偵測
- **ZCode registry 機制約束**：registry 內必須實檔拷貝（file-level symlink 靜默不載——已定案）；ZCode 設定 UI 可穿 symlink 寫入 repo（既有「UI 防護規則」：UI 編輯落在拷貝上、同步時被覆蓋）；ZCode spawn 無 model 參數——model 由 frontmatter pin 決定；`thoughtLevel` 是 ZCode 專屬欄位（Claude 對未知欄位容忍度未明→禁寫進共享檔）；MCP 全名寫進 frontmatter＝綁死「該工具在 spawn session 啟動快照在場」（未在場→spawn 直接失敗）
- **CC（Claude Code 2.1.261 實測）**：`--agent <name> --bg` named-agent 形態可用；引用不存在的名稱→warning＋session 立即退出；Agent tool spawn 可帶 model/effort 參數（spawn-time）
- **external runtime**：muse code（bridge 必經，`task`/`review` 子命令，`--model`/`--effort` passthrough）、codex（companion `task --model gpt-5.6-sol --effort <enum>`，enum=none~xhigh）、grok-build（同族委派 plugin；安裝態記載於 hooks/AGENTS.md，**dispatch contract 未證實**）——皆為工單介面，無 agent 定義檔概念
- **消費端**：分兩組盤點——**名稱消費者**（檔內出現 role 名；EP 盤點用 `rg "lite-verify|vision-review|archify-gen|impl-flash|cross-verify-investigator|spec-miner|cr-research|mem-distill|code-reviewer"`）與**語義消費者**（檔內有 ZCode-only／分流語句但無 role 名；EP 盤點補 `rg "ZCode-only|projection map"`——已知命中 agent-workflow／deep-work／cross-verify 三檔，本弧必改面含其過期分流語句）
- **grok-build 現況**：**未安裝**（`hooks/AGENTS.md:10`「grok-build 未安裝：安裝後照 muse/codex 條目形態補第三條 SessionEnd」）——harness matrix 該行全程標〔未安裝·dispatch contract 未證實〕，規劃與測試不得假設可用
- **同目錄舊 ep.md 已作廢**（勘正前版本）：codex `/execution-plan` 對其**全文覆寫**，不續用任何舊內容；AIR-29 既有 To Do 卡（40f47e8 建），卡務照 kanban-board 合約

### 1.2 痛點（P1-P6，本 spec 要解的題）

- **P1 · CC 端 8/10 role 不可達**：`claude --agent lite-verify` 之類引用→session 立即死（已實測）。後果：CC 上的 deep-work／全生命週期流程退化成「全部主 session 自做」——execution contract 表在 CC 端實質失效，且「CC 端不得引用 ZCode-only 名稱」的禁令寫在 projection map 裡＝把債務文件化當償還
- **P2 · external runtime 無 role 面**：muse/codex/grok-build 以工單派發，role 的紀律文本只存在 registry 檔裡——每次派發要重寫 role prompt，drift 溫床（同一套體系最反對的事）
- **P3 · 違反 AIR-24 自家裁決**：AIR-24 已定「tier＝能力檔語義、非模型綁定」，但 registry 把 `model:`/`thoughtLevel:` pins 凍結進檔案＝「這個 role 永遠 flash」——派發當下按任務選 model 的彈性被寫死
- **P4 · model 軸缺影像能力映射**：哪些任務需要影像在角色→tier 表已成文（vision tier），但「哪些 **model** 具影像能力」的 per-provider 映射從未成文——vision-review 的影像需求只藏在 pin 的選擇裡，未來換 pin 降級成非影像款無人擋（視覺驗收會靜默壞）
- **P5 · provider 與 harness 概念混用**：既有文檔把 GLM／CC／codex／muse 並列——公司與調用面不分，導致跨 harness 討論時持續誤導
- **P6 · 部署無機械防線**：手動 cp＋無 --check——AIR-28 期間 agent 檔 schema 外流、CJK 異體字損壞都靠外部 review 才抓到

### 1.3 能力剖面依據（sess_e905a8a2 鑑識＋AIR-24，勿重辯）

- flash 類模型**強**：機械/清單執行、驗證型任務、修正執行、報告誠實
- flash 類模型**弱**：judge 自證塌陷＋sycophancy（錯信心 finding＋順勢採納＝最危險組合）、跨單位語義換算（P0×2 實錄）、測試合法化 bug（寫的測試＝規格陳述非驗收證據）
- 結論：**判斷密集位（judge 裁決／EP 規劃／post-build 編排）必須旗艦**，且由主 session 執行不派 agent；「非旗艦＋高 effort 補償＝未驗證路徑，採用前先小規模實證」

## 2. 三層結構（權威定義——user 09-05 裁定）

- **公司（provider）**＝model 家族的擁有者：**zai**／**Anthropic**／**OpenAI**／**xai**／**meta**——每家公司提供多個 model，檔次不同
- **harness（調用面）**：zcode（綁 zai）／cc（綁 Anthropic）／codex-companion（綁 OpenAI）／grok-build（綁 xai）／muse code（綁 meta 系 muse-spark）；external bridge＝muse bridge／codex-companion
- **規則**：需求分類表以**公司為欄、model 為格**；harness 軸只記「綁哪家 provider＋怎樣調用」——dispatch 先選 harness，再在該 harness 綁定的 provider 內依需求類選 model

### 需求分類 × 公司（權威表；build 時落 model-routing skill）

| 需求類 | 語義（哪些任務） | zai | Anthropic | OpenAI | xai | meta |
|--------|----------------|-----|-----------|--------|-----|------|
| **一定要旗艦** | judge／EP 規劃／批判類判斷密集 | GLM 5.3 | opus | sol high／max | fabel | muse-spark 1.3 |
| **一定要影像** | 視覺類任務（vision-review 等） | glm-5.3-flash（多模✓ 已實戰） | claude 影像款〔查證待辦〕 | chatgpt 影像款〔查證待辦〕 | grok 影像款〔查證待辦〕 | muse `--image`✓（muse-spark） |
| **其他隨意** | 實作／機械驗證／挖掘／渲染 | glm-5.3-flash（標準款預設） | sonnet／haiku | **terra high+**；**luna 不要**（排除禁派發） | 〔待查證〕 | —（旗艦同體；額度貴非省成本預設） |

- 旗艦清單為 user 逐項指定（與五家公司一一對應）；GLM 5.3 調用形態＝主 session full inherit（AIR-24 語義；registry 不釘 id）
- 影像款三格（claude/chatgpt/grok）＝**查證待辦**（EP 排查證段，引用前先查 provider 文檔）
- tier 詞彙對齊：full＝旗艦需求、vision＝影像需求、lite＝隨意（標準款預設）——消 contract 表 tier 欄與本表的兩套詞彙漂移
- 「隨意」≠隨便——flash 分工律保護面約束照舊（執行產出仍受驗收證據規範）

## 3. User Story

作為跨 harness（zcode／cc／grok-build／muse code）工作的 solo developer，我想要 agent role 定義、model 選擇、harness 調用方式三者正交分離——**role 說「這份工作是什麼、怎麼做」（目標最重要），需求分類說「什麼任務必須旗艦／必須影像／其他隨意」，harness matrix 說「每家怎樣調用」**——因為同一批 role 要在每個 harness 都可達、model+effort 要按任務性質在派發當下選擇，不是被 registry 檔案的 pin 凍結。

- **痛點**：P1-P6（見 1.2）
- **現在怎麼處理（workaround）**：CC 端引用 role 名即死→只能主 session 自做；external 派發手動重寫 role 文本；pin 凍結靠「改 registry 檔」換模型；部署一致性靠人眼＋外部 review 兜底

## 4. Use Cases（四個，寫清楚）

### UC-1 · role 單一源（`agents/roles/<name>.md`）
- **消費者**：所有 harness 的 dispatch 端（zcode 生成器／cc 生成器／external 工單作者）
- **行為**：10 個 role 的 authoring 單一源；每檔結構＝①**目標**（第一節——這個 role 解決什麼問題、成功樣態一句話）②做法（紀律與程序）③skills 引用（需要哪些 skill 方法論）；frontmatter 白名單＝`name`／`description`／`tools`／`background`（**零 model、零 harness、零 thoughtLevel 字樣**）
- **「零 model 字樣」斷言的精確定義**（避免詞彙碰撞——role 名 `impl-flash` 與分工律句天然含 flash/lite 詞）：斷言 regex 集合＝`model:`（frontmatter 欄）、`thoughtLevel`、model id 前綴 `glm-|gpt-|claude-|opus|sonnet|haiku|terra|luna|fabel|spark`；**tier 詞（full/lite/vision）與「分工律：flash 執行＋強模型 judge」類語義句是保留項**（描述能力剖面非釘 model）——description 內這類句保留，不改寫
- **成功樣態**：上述 regex 斷言 roles/ 全檔零命中；現有 8 檔 ZCode-only body 的 2 處 ZCode 字樣（cross-verify-investigator:16、mem-distill:25）neutralize；reviewer 2 檔自 `shared/` 平移；`agents/shared/` 退役（不留 tombstone）

### UC-2 · dispatch matrix 兩軸
- **消費者**：任何 harness 上的派發者（人類或主 session）
- **行為**：**harness 軸**（agents/AGENTS.md）——每家一行：調用形態（zcode registry spawn／cc `--agent`＋Agent tool／grok-build 工單〔dispatch contract 未證實，標註〕／muse bridge 工單必經）＋綁定 provider＋role 從哪來；**model 軸**（model-routing skill）——第 2 節權威表落位＋tier 詞彙對齊行
- **成功樣態**：從任何 harness 查表可回答「這個 role 在這家怎麼派、用什麼 model+effort」；contract 表 tier 欄詞彙與需求分類無漂移

### UC-3 · 生成式部署投影（`scripts/sync_agents.py`）
- **消費者**：repo 維護（role 編輯後的重生成）；兩家 registry 的載入（zcode/claude）
- **行為**：roles/ 單一源→生成 `agents/zcode/`（body＋`model`/`thoughtLevel` pins——pins 是**部署預設**，值抄 model-routing 解析表；生成器 pin dict 帶 `req` 需求欄，**值直接用 tier 詞 full/vision/lite**〔與 §2 對齊行同詞彙，不另造 flagship/any 第三套〕，vision 的 pin 禁降非影像款）與 `agents/claude/`（body 省略 model/thoughtLevel；tools 沿 known-divergence 規則）；**req/pin dict 的載體＝`scripts/sync_agents.py` 內的部署預設表**（非 roles/ frontmatter——白名單不含 req）；`--check`＝唯讀比對生成預期 vs 實體（drift→FAIL loud 列清單；**check 模式零寫入**）；stale 清除（roles/ 已無對應的生成物移除）；`--map`＝輸出 role→registry 可用性表
- **成功樣態**：TDD（tests/test_sync_agents.py）；`--check` 綠；新增/刪除 role 的完整生命週期被測；`--check` **必須先讀後寫分流**（check 模式零寫入）

### UC-4 · external 工單 role 段引用
- **消費者**：向 muse code／codex／grok-build 派發的工單作者
- **行為**：work-order 模板（現 10 節）新增 role 段——**落位裁定（EP review 二輪定案）：§2 內子段**（推翻本節原「§4 後」建議——保持十個 top-level 節、§3–§10 consumer 不因重編號漂移）；內容約定＝role 紀律核心引用 `agents/roles/<name>.md` body（貼進工單或給路徑令其讀；與 §4 必讀清單的分工——§4 列 repo 內材料路徑，role 段承載 role 選擇依據＋model/effort 按任務查需求分類表）；與 agents/AGENTS.md external-runtime 節互指（單一源在模板）；紅線段（§1）不變
- **成功樣態**：向 external runtime 派發任何 role 時零重寫文本；模板與 agents/AGENTS.md external-runtime 節互指（單一源在模板）

## 5. Scenario Matrix（自包含——不依賴 EP 編號）

| # | 場景 | 觸發 | 預期行為 |
|---|------|------|---------|
| SM-1 | zcode spawn 任一 role | registry spawn（背景） | 生成檔生效——frontmatter 帶部署預設 pin；role 行為與重構前等價 |
| SM-2 | cc named-agent 調任一 role | `claude --agent <role> --bg` | 10 名全數載入成功（現狀 8 名即死）；不存在的名稱照樣退出（反向守衛仍在） |
| SM-3 | cc Agent tool spawn | spawn-time model+effort | 按 model 軸查表填（需求分類→provider→model+effort） |
| SM-4 | external 工單派 role | muse/codex/grok-build 工單 | role 段引用 roles/ body＋model/effort 按任務；luna 不出現在任何派發 |
| SM-5 | 編輯 role body | 改 roles/<name>.md | 只改 roles/→腳本重生成→兩 registry 同步；UI 手改生成拷貝會被下次生成覆蓋（明示） |
| SM-6 | 判斷密集任務誤派非旗艦 | dispatch 選錯檔 | 需求分類表＋AIR-24 裁決擋（judge/EP＝旗艦需求）；「非旗艦＋高 effort 補償＝未驗證路徑」標註照搬 |
| SM-7 | 新增 role | 建 roles/<name>.md | 腳本重生成＋投影同步；**缺 pin 鍵→fail loud 列清單**（防靜默 unpinned 上線） |
| SM-8 | 生成物 drift | 手改 zcode//claude/ 檔 | `--check` FAIL loud（列不一致檔）；修因後重跑轉綠 |
| SM-9 | 刪除 role | roles/ 移除檔案 | 腳本清除對應生成物（不留孤兒；與既有 fork 條款的衝突見 §7 約束） |
| SM-10 | 影像 role 的 pin 被降非影像款／影像任務派非影像 model | 生成／dispatch | 需求欄（tier 詞 full/vision/lite）防線——生成期 fail loud；model 軸需求欄擋 |
| SM-11 | 單一源宣稱 drift | roles/ 與生成物長期演化 | 「agents-projection-sync」invariant 登記進 check_single_source（**路徑 `skills/scan-project/scripts/check_single_source.py`**——根目錄 scripts/ 只有 deploy_agents.py；沿用 INVARIANTS type 系統，必要時新增 sub-process 型 check 函數委派 `sync_agents.py --check`） |
| SM-12 | role 名被命令檔引用 | 12+ 消費檔 | registry name 零改動——引用完整性以 rg 對帳（**非**「檔案零 diff」——治理文檔與分流語句本弧必改，見 §7） |
| SM-13 | 生成器 bug 把 ZCode 專屬欄寫進 claude/（thoughtLevel 洩漏） | `--check`／生成測試 | 生成測試含負向斷言：claude/ 生成物零 `thoughtLevel`／零 `model:` 欄（UC-3 白名單的機械面） |
| SM-14 | rules/ 變更後 bundle 未部署（sync→deploy 順序） | `rules/model-routing.md` 觸面後 | rules 觸面→必跑 `uv run python scripts/deploy_agents.py`＋三 bundle cmp（zcode/opencode/codex）；EP 排序：sync_agents 與 deploy_agents 互不依賴，但收尾驗證兩者都綠 |
| SM-15 | ZCode registry 快照制——生成後同 session 驗不出 | SM-1 的 L4 實測 | zcode spawn 生效驗證須**新 session**（快照制：session 啟動時載入 registry——agents/AGENTS.md 生效時機節）；EP 驗收步驟明記此前置 |

## 6. 邊界

**Always（一定做）**：role 檔零 model／harness 字樣；registry name 不變（消費端引用語義不變）；AIR-24 判斷密集位裁決照舊（judge/EP 規劃/post-build 編排＝旗艦需求＋主 session 不派 agent）；ZCode registry 實檔拷貝機制照舊（file-level symlink 禁用）；ZCode UI 防護明示（UI 改生成拷貝會被覆蓋）；luna 全域排除
**Ask First（先討論再做）**：zcode//claude/ 保留為生成物（現有設計傾向保留——zcode 無 spawn-time model 參數，生成檔是必要部署面）；grok-build dispatch contract（未證實，引用前先查證）；影像款三格查證（claude/chatgpt/grok）
**Never（不做）**：不新增／砍除 role 集合（10 role 經 UC 盤點驗證）；不把 model 值寫進 roles/；不動 judge／EP 規劃／post-build 編排的主 session 裁決；不引入 file-level symlink 部署；不派 luna；不加統計/日期/版本號進任何 instruction 檔（instruction-writing 元資訊禁令）

## 7. 已知設計約束（雙家族 review 30 findings 蒸餾——EP 必須編入，防重發明）

1. **generator contract**：`--check` 先讀後寫分流（check 模式零寫入——先比對後寫入的偽碼順序是 bug）；生成物帶 ownership marker（檔頭標「generated by sync_agents.py——勿手改」）；stale 清除需**fork 豁免機制**（agents/AGENTS.md 既有「要釘模型→在 zcode/ 建 fork」條款與無差別清除衝突——豁免清單或 manifest 擇一）；缺 pin 鍵 fail loud；skill 解析表↔pin dict **parity test**（讀 model-routing skill 表比對 dict）；`--map` 輸出形狀也要測
2. **projection 規則**：frontmatter 白名單（UC-1）；tools 三族投影規則各列（CR MCP 白名單族／impl-flash 的 Grep-Glob union 族／reviewer 的 background+context7 族）；MCP 全名綁「spawn 啟動快照在場」的通則約束寫進生成器不變式（codex R1 教訓——CC 側剝 CR 行只是既有分歧的延續，通則要成文）
3. **消費端對帳**：驗收閘＝「registry name 引用完整性」（rg），**非**「消費檔零 diff」——本弧必改面：`skills/code-review/SKILL.md`（逐字引用 `agents/shared/` 路徑）、**語義消費者三檔的過期分流語句**（`skills/agent-workflow/SKILL.md:41`「僅限 claude/ registry 在場名稱／引用 ZCode-only 名稱立即退出」、`skills/deep-work/SKILL.md:50` 同型語句、`skills/cross-verify/SKILL.md:30`「cross-verify-investigator 是 ZCode-only registry name」——弧後這些語句為假，必改）、contract 表 harness registry 欄（隨投影同步）＋「CC 端不得引用 ZCode-only 名稱」禁令行（弧後為假，刪）、`agents/AGENTS.md` 全面重寫（**附 keep-list——保留與兩軸重構無關的營運節**：Thin forwarder 與 flag profile、dispatch face 與收法、三態判定表、欄位相容策略、tools 清單陷阱、ZCode/Claude 限制——只重寫 registry 結構／同步紀律／pin 單一源／projection map／execution contract 表相關節；**「2026-08-XX 實測/定案」類日期註記是 provenance 非元資訊，保留不刪**）、root `AGENTS.md` agents/ 條目、`skills/CLAUDE.md`／`memory-audit` 等指 `agents/zcode/` 的表述、`rules/model-routing.md:12,24-26`（zcode 表述——**rules 觸面→必跑 deploy_agents.py**，取消「rule 零改動」假設；兩張路由表關係見下條）
4. **兩張路由表的結構關係**（防第三表 drift）：model-routing skill 既有 tier→(model,effort) 解析表與新「需求分類×公司」表重疊——**處置＝分層合併**：新表為上層（需求類→tier 映射，即 §2 對齊行正式化），既有 tier 表為下層（tier→各 provider model+effort）——兩跳查詢（需求類→tier→model）；parity test 比對目標＝**下層 tier 表**↔sync_agents pin dict（值層）；新表只管需求語義不重複 model 值
4. **治理**：單一源宣稱登記 `skills/scan-project/scripts/check_single_source.py` INVARIANTS（type 系統沿用，必要時新增 sub-process 型；instruction-writing 對 recurring invariant 的要求）；「hook 1」類無定義術語禁出現；工作順序決策——`shared/`→roles/ 用 `git mv` 保履歷
5. **驗收層級誠實**：SM-2（cc named-agent）＋SM-1（zcode spawn）可 L4 實測；SM-3（cc Agent tool）／SM-4（external 工單）標「文檔對帳＋首例實戰補驗」——不高報為已完成 L4；zcode 抽查至少三族各一（lite-verify＋impl-flash＋code-reviewer）
6. **事實修正**：grok-build 非零事實——hooks/AGENTS.md 有安裝態記載（僅 dispatch contract 未證實）；工單模板實為 10 節（非 9）；「8 檔」表述改「10 檔 registry（8 pinned＋2 reviewer）」

## 8. 成功條件

- 10 role 全數 CC named-agent 可達（L4 逐名啟動正向測試；zcode 側 L4 因快照制須新 session——SM-15）＋unknown-name 反向測試仍退出
- roles/ 零 model 字樣（**UC-1 定義的 regex 集合**斷言零命中）；`--check` 綠；agents-projection-sync invariant 登記且運作（check_single_source 路徑見 SM-11）
- 需求分類表落 model-routing skill（旗艦/影像/隨意 × 五公司欄，與 §2 權威表逐格一致；**與既有 tier 表分層合併**——§7.4）；luna 零出現
- 工單模板 role 段在場（引用 roles/ 路徑；落位見 UC-4）；dispatch matrix 兩軸表在場（harness 怎樣用→agents/AGENTS.md；model 怎麼選→model-routing skill）
- 消費端引用完整性 rg 對帳綠（**含語義消費者**——`rg "ZCode-only|projection map"` 過期語句清零）；rules/ 觸面時 deploy_agents 三 bundle cmp 一致
- 影像款查證待辦三格有結論（claude/chatgpt/grok 哪些 model 支援影像）——查證結果寫回權威表

## 9. Spec Review Findings（ep-review F1-F5，2026-09-05——全數回寫 implemented）

| ID | 嚴重度 | spec 段落 | 問題摘要 | 處置 |
|----|--------|----------|---------|------|
| R-1 | important | §7.3/§1.1 | 語義消費者過期語句不在必改面＋枚舉法抓不到（agent-workflow:41/deep-work:50/cross-verify:30 弧後為假） | ✅ §1.1 雙 pattern 盤點法＋§7.3 增列三檔 |
| R-2 | important | UC-1 | 「零 model 字樣」斷言遇 impl-flash 詞彙碰撞不可機械判定 | ✅ UC-1 給精確 regex 集合＋保留項宣告 |
| R-3 | important | UC-3/§2 | req 值第三套詞彙（flagship/any）＋載體未指明 | ✅ req 值改用 tier 詞（full/vision/lite）＋載體＝sync_agents pin dict |
| R-4 | important | §2/§7.1 | 新需求表與既有 tier 表重疊、parity test 目標不明 | ✅ §7.4 分層合併裁決（需求類→tier→model 兩跳；parity 比對下層 tier 表） |
| R-5 | important | §7.3 | 「agents/AGENTS.md 全面重寫」無 keep-list＋日期註記界線未定 | ✅ keep-list 六節＋「實驗日期註記＝provenance 保留」 |
| R-6 | suggestion | §1.1 | grok-build「未安裝」未明示 | ✅ 明示＋規劃測試不得假設可用 |
| R-7 | suggestion | SM-11 | check_single_source 路徑與登記形態未給 | ✅ SM-11 補路徑＋type 系統沿用 |
| R-8 | suggestion | UC-4 | 工單 role 段落位＋舊 ep.md 作廢＋卡務未說明 | ✅ UC-4 落位建議＋§1.1 作廢宣告＋卡務 |
| R-9 | suggestion | P4 | 「從未成文」過度陳述（vision tier 已成文） | ✅ 改「model 側影像能力映射缺」 |
| R-10 | suggestion | §1.1 | 名稱/語義消費者混排 | ✅ 拆兩組＋各自枚舉法 |
| R-11 | suggestion | SM 表 | 缺 thoughtLevel 洩漏負向／sync→deploy 順序／快照制前置三場景 | ✅ SM-13/14/15 |

found-nothing 軸（審查者驗證屬實）：repo 事實抽查 20+ 項全過（10 role 檔名、8 pinned＋2 reviewer、shared/ 引用點、model-routing rule zcode 表述、tools 三族、「2 處 ZCode 字樣」精確計數）；F2 合規零違規；F3 三層結構零越位；F5 大類齊。未驗證項：CC 實測行為（文件呼應在場）、sess_e905a8a2 鑑識（外部 session）、影像三格（自標查證待辦）。
