# EP：sub-agent 派發模型路由寫法修補——內建型別繼承語義補洞

> **ep_type**: implementation
> **mode**: docs mode（product 全為 `.md`——rules/skills/agents 定義與其生成物＋工作流索引；scripts/sync_agents.py 與 deploy_agents.py 僅被執行未修改）

**baseline: 083ffff105d0c0c5b1872e974942402ef226d5c9**（EP 建立當下 main HEAD；弧產物＝其上之未 commit 變更 35 檔，見進度節）

## 進度節（即時落盤區）

- 〔09-09〕觸發：AIR-50 弧（mosaic session `sess_85f80c51`）乾跑段兩次派「實作考察」agents 誤用內建 `general-purpose`（無 pin、繼承主 session GLM-5.3）跑 lite 機械查證，user 兩次抓包，裁定「這常犯錯，sub agents 那邊要重新審查寫法」。
- 〔09-09〕根因查證完成（證據見 S1 Context）；user 指示開卡寫 EP 正式化本弧。
- 〔09-09〕**狀態：S1＋S2 變更已全部落地並機械驗證畢（working tree 未 commit；commit 待 user 確認——outward-action-consent）**。含 registry regen（sync_agents）與三端 bundle 部署（deploy_agents）。
- 〔09-09〕S2（skills/CLAUDE.md 工作流索引兩行同步）於 EP 撰寫時補記落地——初版四層修補漏了索引面，EP 前置盤點抓到。
- 〔09-09〕**EP Review 第一輪（獨立 context reviewer）**：0 Critical、2 Important（F1／F3）＋2 Suggestion（F2／F4）——judge 全採納，回寫見「EP review 區段」；F1 產品面修正（agent-workflow 兩處粗體規則限縮 lite 場景）已落地。**EP 定稿**。
- 〔09-09 commit 前 dual-context 複審（AIR-50 session 主導——fresh-eyes＋primed 雙 code-reviewer〔glm-5.3 pins〕）〕**1 Important＋2 Suggestion，judge 全採納**：F1（fresh）rule research/explore 列「要釘模型時同 lite」vs agent-workflow「繼承旗艦＝正確」立場張力——**已修**（rule :28 括號改「預設繼承主模型即正確；歷史釘 lite 屬可選項非必要」，本弧 diff 內）。P1（primed，Important）〔tier: full〕roles 標籤 vs AIR-50 S10 pins 翻轉的協調洞——**歸 AIR-50 S10 承接**（其 EP 修改要點 item 3 已補 roles 標籤同步＋scope 表補 agents/roles；不擋本弧 commit）。P2（primed）設定頁例外細節 rule 單側——歸 S10 順手補（其 item 4 已記）。報告：`.agent-tmp/dryrun/cr-{fresh,primed}-model-routing-fix.md`。

## 實作總覽

| 段 | 內容 | 狀態 |
|----|------|------|
| S1 | 內建型別模型繼承語義——四層寫法修補＋registry regen＋三端部署（34 檔） | ✅ 已完成（未 commit） |
| S2 | 工作流索引同步（skills/CLAUDE.md 兩行——docs mode 收尾條款落地） | ✅ 已完成（未 commit） |
| 收尾 | commit（user gate）→ 卡結案兩步＋弧結案蒸餾 | ⏳ 待 commit 確認 |

## UC 盤點（docs mode：受影響命令/rules 清單）

### Backlog 關聯

- 去重掃描：`backlog search model-routing`——AIR-44/24/20（Done，歷史主題）＋AIR-50（To Do——本弧觸發源，其 EP 已把 incident 記為「memory 修補」，S1-S9 修法不含模型路由寫法層，零重複承諾）；`backlog search general-purpose` 零命中；`ai-analysis/_inbox/pending-decisions.md` 無相關待決。
- 自動建卡結果：本 EP 追蹤卡 ×1（建卡時分配 id）。

### SYSTEM-MAP 影響

- 無 SYSTEM-MAP.md——元專案（docs mode：正當跳過）。

### 掃描範圍

- rules/model-routing.md、skills/model-routing/SKILL.md、skills/agent-workflow/SKILL.md、agents/AGENTS.md、agents/roles/×10（＋生成物 zcode/、claude/ 各 ×10）、skills/CLAUDE.md（工作流索引）；`backlog task list --plain` 全板；memory 池 rg 掃描。

### 同主題 memory 條目（結案蒸餾範圍）

- `reference-zcode-agent-model-inheritance`（reference 形態；mosaic session 09-09 寫入——事實經本弧核實正確。rule 現已承載同一事實，結案蒸餾時對齊措辭＋標註 rule 落地，避免雙源 drift）。
- `feedback_dispatch-model-tier-glm53`（feedback 形態；同 session 09-09 **較早**寫入——`:12`「落到 flash 預設」與 `:14`「general-purpose 不在 registry＝harness 預設 flash」兩處錯誤機制表述，與同檔 `:18`（已更正的抓包實錄）／rule:29／qa.md:95 相抵。錯誤信念源——蒸餾時**必改**，非僅收斂；EP Review F3 補列）。

### 既有 UC 狀態

| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| subagent 模型分層路由（角色→tier→model） | ✅ | model-routing rule＋skill | 更新 | 補內建型別語義＋spawn 反模式——能力面不變、缺口補洞 |
| registry 生成與部署（roles→雙 registry→bundle 三端） | ✅ | agents/AGENTS.md＋sync/deploy scripts | 更新 | roles description 增 tier 標籤（frontmatter 白名單內，生成器相容） |

### 新增 UC

| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| spawn 選單 tier 可見性（roles description tier 標籤） | 📋→✅（S1） | agents/roles/（經 sync_agents 投影雙 registry） |

## Scenario Matrix（docs mode——rg 命中／0 殘留語境）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | session 派 lite 機械任務（查證／驗證／挖掘） | spawn 選型別當下 | 選單 description 前綴〔tier: lite〕可見＋always-on rule 內建型別列在場 | `rg -c "〔tier: lite〕"` 三目錄各 7（lite 系）；內建列 zcode/codex bundle＋Claude rules symlink 三處在場（muse 變體 by-design 排除 model-routing——tier 派發是主 session 職責，deploy_agents.py 排除列） | spawn 選單 tier 可見性 |
| SM-2 | session 直覺想派 general-purpose 跑機械段（常犯錯） | 錯誤操作 | rule 反模式句攔截（「subagent 預設便宜層是錯覺」） | `rg "旗艦[燒跑]機械段"` 六處語義一致（rule＋兩 skill＋agents/AGENTS.md＋索引；燒/跑字形分歧、語義同構） | 模型分層路由 |
| SM-3 | roles/ 改動後未 regen（生成物漂移） | 邊界 | `sync_agents --check` exit 1 fail-loud | `uv run python scripts/sync_agents.py --check` exit 0 | registry 生成 |
| SM-4 | bundle 尺寸膨脹觸截斷線 | 效能／尺寸 | 90KiB gate 拒部署（100KiB 截斷線前擋） | deploy 輸出尺寸行（本次 74,655 bytes＝81% gate） | bundle 部署 |
| SM-5 | 同一事實各檔表述分歧（跨檔 drift） | 跨檔一致性 | 「無 pin——繼承主 session 模型」語義多檔一致 | 單源 rg 掃描（見 S1 驗證表末行） | 模型分層路由 |

## 段落劃分原則

單一產品語義（一個事實、多個承載面）——S1 四層＋regen＋部署為一體（拆段破壞同 commit 原子性）；S2 索引同步是 docs mode 收尾條款的產品面落地，獨立標段但不獨立 commit。收尾（commit／結案）走收尾步驟，非產品段。

## S1：內建型別模型繼承語義——四層寫法修補〔已完成〕

### Context

- **背景（incident 還原）**：AIR-50 弧 mosaic session 兩次派考察 agents（lite 機械查證性質）用內建 `general-purpose`——內建型別不在 `~/.zcode/agents/` registry、無 model pin，**繼承主 session 模型 GLM-5.3**（官方設計行為：`ref-docs/harness/zcode/cn/docs/qa.md:95`「不指定時繼承父會話的主模型」）。第一次口頭被抓、第二次 user 再抓（session msg [148]-[149]）→ TaskStop 重派 `cross-verify-investigator`（registry 釘 glm-5.3-flash）。重派後兩顆死於 **1308 額度**（窗口 08:21 重置）——與寫法無關，muse 承接＝既有 failover 條文路徑。
- **寫法缺口（根因，三個）**：
  1. always-on `rules/model-routing.md` 角色→tier 表零提內建型別——「無 pin 繼承主模型」事實只住在 skill「歸因紀律」段（事後歸因框架，非 spawn 前反模式）與官方文檔鏡像，派發當下不可見
  2. spawn 選單（Agent tool 清單）只帶 description——registry 描述 role-rich 但 tier 全缺席，被路由的維度（模型）在決策點不可見
  3. 文化印象反向補位：「lite subagent 執行檔＝flash 省成本層」被外推成「subagent 預設都便宜」，無文字反駁——錯誤信念填了真空
- **UC 引用**：更新〔subagent 模型分層路由〕；新增〔spawn 選單 tier 可見性〕。
- **依賴關係**：roles/ →（sync_agents.py 生成）→ agents/zcode/＋agents/claude/ →（`~/.zcode/agents` symlink）runtime registry；rules/ →（deploy_agents.py bundle）→ 三非 Claude 端 AGENTS.md。S1 變更雙鏈尾端皆已重生成。
- **語義約束**：tier 詞彙（full/lite/vision）單一源＝`rules/model-routing.md`——roles description 只用 tier 詞、**禁 model 名**（roles/ 是 harness-neutral authoring 源，零 model 字樣紀律）；model 值唯一源＝skill tier×provider 表（sync_agents 部署預設表材料化）。與 S2 共享：索引行只摘要 skill 內容、不引入第二定義。
- **基礎設施盤點**：`scripts/sync_agents.py`（frontmatter 白名單 name/description/tools/background——description 逐字投影，tier 標籤相容）；`scripts/deploy_agents.py`（90KiB gate＋三端部署＋尺寸輸出）。
- **依賴錨點**：
  - 內建型別 rule 列 → 定義 `rules/model-routing.md:29` ／ 消費 `skills/agent-workflow/SKILL.md:41,229`
  - 內建繼承事實深層 → 定義 `skills/model-routing/SKILL.md:40`（dispatch 預設 ZCode 段；歸因紀律段既有行同構）／ 消費 memory `reference-zcode-agent-model-inheritance`
  - tier 標籤 → 定義 `agents/roles/*.md` description ／ 消費 `agents/zcode/*.md`＋`agents/claude/*.md`（生成投影）
  - 官方事實源 → `ref-docs/harness/zcode/cn/docs/qa.md:95`（鏡像）
- **技術選型**：四層承載（rule 反模式／skill 深層案例／消費側檢查點／registry 治理）＋spawn 選單標籤。對比替代案「設定頁釘死 general-purpose→flash」——**否決**：general-purpose 是無能力上界的 fallback，釘死會把需要旗艦的一般委派靜默降級；路由由 registry 角色承載。
- **成功標準**：派 lite 任務的 session 在兩個決策點（always-on rule、spawn 選單 description）都看得到 tier／內建繼承語義；機械可驗（SM-1/2/5）。

### 修改要點（docs mode——pseudo code 裁剪）

1. `rules/model-routing.md` 角色→tier 表新增列：`harness 內建型別（general-purpose／Explore）｜無 pin——繼承主 session 模型｜誤派反模式＋「預設便宜層是錯覺」（AIR-50 弧兩次實例）`
2. `skills/model-routing/SKILL.md`：dispatch 預設 ZCode 段補內建語義＋真實案例；description 觸發詞＋`general-purpose`／`內建型別`／`繼承主模型`
3. `skills/agent-workflow/SKILL.md`：消費側 dispatch 程序 item 2 補「lite／機械角色任務 spawn 型別必須 registry 角色（唯讀探察＝內建 Explore 承接，rule research/explore 列）」；spawn 前自檢清單新項（:229）——F1 修正後措辭
4. `agents/AGENTS.md` ZCode 限制節新 bullet（:112——內建繼承＋反模式）
5. `agents/roles/` 全 10 檔 description 前綴 `〔tier: lite|full|vision〕`
6. 生成＋gate：`uv run python scripts/sync_agents.py`（雙 registry 20 檔）→ `--check` exit 0
7. 部署：`uv run python scripts/deploy_agents.py`（zcode/codex/muse 三端 bundle）

### S2：工作流索引同步〔已完成〕

`skills/CLAUDE.md` 兩行（:130 agent-workflow、:132 model-routing）：補「spawn 型別 gate／內建型別無 pin 繼承＋反模式」摘要——docs mode 收尾條款（工作流索引 description 同步）的產品面落地；只摘要不引入第二定義（單一源在 rule/skill）。

### 驗證策略（docs mode——已執行，證據）

| 驗 | 方法 | 結果 |
|----|------|------|
| tier 標籤投影 | `rg -c "〔tier: " agents/{roles,zcode,claude}/` | 10/10/10（字形完整＝CJK 無損壞） |
| pin 與標籤共存 | `head agents/zcode/cross-verify-investigator.md` | description 帶〔tier: lite〕＋`model: glm-5.3-flash` |
| 兩端 bundle＋Claude rules 在場 | rg 新 rule 列關鍵詞於 `~/.zcode/AGENTS.md`（:599）／`~/.codex/AGENTS.md`／`~/.claude/rules/model-routing.md`（symlink） | 各 1 hit（muse 變體 by-design 不含 model-routing——deploy_agents.py 排除列；muse bundle 本次已部署、時間戳更新） |
| 部署 hash 一致 | `shasum` zcode vs codex bundle | 同 hash |
| 生成物 drift gate | `sync_agents.py --check`（隨 `&&` 鏈） | exit 0 |
| bundle 尺寸 | deploy 輸出 | 74,655 bytes（81% of 90KiB gate；ZCode 100KiB 截斷線內） |
| neutral 格式檢查 | rules/AGENTS.md 機械清單（裸 slash／`@`／跨域路徑／絕對路徑） | 零命中 |
| 單源一致性 | `rg general-purpose` 於 rule＋兩 skill＋agents/AGENTS.md | 語義一致（無 pin 繼承＋反模式同構，無矛盾表述） |

**已知未覆蓋**：L6 人類觀察——「下一個 session 不再誤派」無法本弧自證（registry/bundle 快照制，新 session 才載入；mosaic session 重啟前不可見）。屬 dogfood 面，卡 desc 記錄，不作本弧驗收條件。

### Invariant Impact

無 domain invariant（文檔弧）。但 model-routing rule 屬「跨 context 全 session 消費」的共用規範——變更影響面＝所有消費端 session 的派發行為；保護機制＝SM-3/4 機械 gate＋單源紀律（語義約束節＋驗證表末行）。

## EP review 區段

### EP Review Findings — 09-09-subagent-model-routing-fix（第一輪：獨立 context reviewer；judge＝主 session 全採納）

| ID | 嚴重度 | 檔案:行 | 問題 | 建議 | 狀態 | 決策 |
|----|--------|---------|------|------|------|------|
| F1 | 🟡 important | skills/agent-workflow/SKILL.md:41,:229 | 「spawn 型別必須 registry 角色」無條件粗體與既存 Explore 模板（rule:28 research/explore 列、execution-plan:324/:337、implement:196）字面衝突——EP Review Cycle 按 :337 spawn Explore 會踩 :229 自檢項 | 限縮為 lite／機械角色任務；唯讀探察＝內建 Explore 承接 | implemented | ✅ |
| F2 | 🟢 suggestion | ep.md SM-2 | checkpoint `rg "旗艦燒機械段"` 字面漏 agents/AGENTS.md:112 與 agent-workflow:229 的「跑」字形——照字面跑會誤判缺列 | checkpoint 改 `rg "旗艦[燒跑]機械段"` | implemented | ✅ |
| F3 | 🟡 important | memory feedback_dispatch-model-tier-glm53:12,:14 | 蒸餾範圍漏列此條——「general-purpose＝harness 預設 flash」錯誤機制表述殘留 memory 池（錯誤信念源），與同檔 :18／rule:29／qa.md:95 相抵（judge 已親驗原文） | 收尾蒸餾補列，:12/:14 必改 | adopted（收尾執行） | ✅ |
| F4 | 🟢 suggestion | ep.md SM-1/驗證表 | 「三端」指涉漂移：deploy 三端含 muse，但 muse bundle by-design 排除 model-routing（deploy_agents.py:67）；驗證實際覆蓋 zcode/codex＋claude | 統一措辭「兩端 bundle＋Claude rules」＋註明 muse 排除 | implemented | ✅ |

> 審查者自證：行錨點 7/7 重驗、計數全對、`--check`/hash/bundle 重跑全過；方法論限制——同家族 LLM context 獨立、共享系統偏誤仍在。

## 整合策略

- **同 commit 原子性**：S1＋S2 共 35 檔單一 commit（rule/skill/roles/生成物/部署一起走——文檔與其生成物不可拆）；git add 具名清單，不碰 AIR-48/50 卡（他 session dirty）與 `ai-analysis/_tasks/09-09-skill-contract-fixes/`（在飛 EP）。
- **生效時機**：registry 與 bundle 皆快照制——新 session 載入；已運行 session（含觸發本弧的 mosaic session）重啟前不可見。
- 建卡 commit（chore(backlog) 顆粒）先行走 main——跨 WT id 防撞。

## 收尾步驟

1. **commit（user gate——outward-action-consent）**：本弧 35 檔＋EP 任務家（ep.md＋index.html）；訊息帶卡 id
2. **卡結案兩步＋弧結案蒸餾第三動**：`task edit <id> -s Done --final-summary` → `--ref` 換 done/ URL → memory 蒸餫：`reference-zcode-agent-model-inheritance` 對齊（rule 已承載事實，條目收斂為指向）；`feedback_dispatch-model-tier-glm53` `:12/:14` 錯誤機制表述（「harness 預設 flash」）必改——對齊 rule:29 繼承語義（EP Review F3）
3. **Capabilities**：無新增表格行——能力描述由 rule/skill 承載（docs mode 元專案：受影響命令行為已反映＝S2 索引同步）
4. **/consistency**（post-build 鏈；commit 前跑）
