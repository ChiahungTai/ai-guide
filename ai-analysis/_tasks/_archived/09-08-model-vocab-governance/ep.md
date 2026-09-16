# AIR-43 EP — model 詞彙治理：flash 去階層化承接、vision 定義收尾、full-tier 旗艦釘選

> **ep_type**: implementation
> **card**: AIR-43（backlog/tasks/air-43*.md，desc 四項「已決策勿重辯」為不可動搖設計裁決）
> **baseline**: 77eec0b（HEAD at EP 建立；含 AIR-43 建卡 commit）
> **模式**: mixed docs+code——S1/S4 文檔面（docs mode 驗證：rg 殘留/跨檔一致性）、S2 含 .py（TDD＋parity gate）、S3 為 L4 runtime 遙測驗證（跨 session）

---

## 實作總覽

三範圍項現況與本 EP 分工：

| 範圍項 | 現況 | 本 EP |
|--------|------|-------|
| flash 去階層化（詞彙清理） | **已落地 working tree 未 commit**（16 檔；sync --check 綠＋28 tests 綠已複驗） | S1 commit 承接＋全域 bundle 重部署 |
| vision tier＝「支援影像的 model」 | 已落地（rules tier 詞彙句＋skill dispatch 影像行），隨 S1 一併 commit | 無獨立段落 |
| full-tier 旗艦釘選（inherit 洞） | **主要剩餘工作**——洞已實證（見段落 0） | S2 落地＋S3 首例遙測驗證 |
| flash lane 殘餘 | 待 user 拍板 | S4（user 決策點） |

**洞的實證**（段落 0 遙測查證，非推測）：`~/.zcode/cli/db/db.sqlite` `model_usage` 聚合顯示 `zcode-code-reviewer` 曾以 `GLM-5.3-Flash` 跑 **392 requests**（code-reviewer-primed 另 107）——full-tier 審查 agent 在主 session 為 flash 時實際漂移到 lite 級；同時所有 pinned agents（vision-review/impl-lite 等）全以小寫 `glm-5.3-flash` 出現、零漂移列——「registry pin 不受 session 切換影響」同查證成立。釘選是實證支持的修法。

---

## 段落 0：全域研究摘要（已完成，結論直接可用）

> 本 EP 由背景 agent 撰寫，研究已機械執行完畢（rg/Read/遙測 SQL），以下為產出摘要＋證據。C1-C7 調查宣稱對帳見本節末表。

### 可複用基礎設施

- **投影管線** `scripts/sync_agents.py`：`ZCODE_PINS`（L46-49）→ `render_registry`（L222-234，條件 `requirement in ZCODE_PINS` 已泛化）→ `check_parity`（L121-158，model＋effort 雙層 parity guard）。**增 full 釘選只需動 dict＋regex 兩處，render/parity 邏輯零改**
- **測試契約** `tests/test_sync_agents.py`（28 tests，現全綠）：schema/render/check purity/map/idempotence/collision/parity 全覆蓋；S2 需刻意反轉 `test_render_zcode_full_omits_model`（L97-100）並更新 parser fixture（L297-310）
- **部署管線** `scripts/deploy_agents.py`（rules 改動後重部署全域 bundle；90KiB gate fail-loud）
- **遙測配方**（memory `reference_zcode-platform-facts` 遙測 DB 段）：`~/.zcode/cli/db/db.sqlite`（注意同層 0-byte 殘檔陷阱）；查詢用 python＋`file:...?mode=ro` URI（sqlite3 CLI 無聲空輸出）；`model_usage.agent` 欄區分主/subagent（`zcode-agent`=主、`zcode-<name>`=subagent，實測 agent 欄全非空——過濾要加 agent 名）；`model_id` 大小寫＝來源（大寫=session runtime、小寫=registry pin）；`variant`=effective effort

### 依賴關係（錨點，build 前先驗證未 drift）

| 錨點 | 定義端 | 消費端 |
|------|--------|--------|
| `ZCODE_PINS` | scripts/sync_agents.py:46-49 | render_registry:231-233；check_parity:141-157 |
| `_ZAI_PIN_RE` | scripts/sync_agents.py:67-69 | parse_skill_zai_pins:105-112 |
| tier×provider 權威表 full 行 | skills/model-routing/SKILL.md:16 | check_parity（_ZAI_PIN_RE 解析 zai 欄） |
| 部署填法表 | skills/model-routing/SKILL.md:52-56 | check_parity effort 層（`_EFFORT_RE` 全檔**首個** `thoughtLevel:` 值）＋agents/AGENTS.md pin 治理段 |
| 「full（inherit）為基準」措辭 | rules/model-routing.md:22-23 | 全域 bundle（~/.zcode/AGENTS.md 等四家） |
| 省略共用 model 行 | agents/AGENTS.md:96 | registry 治理敘事 |
| generate 註解 | scripts/sync_agents.py:43-45 | 讀者（「full＝model 省略故無列」——將失效） |

**關鍵結構約束（設計推導基礎）**：`_EFFORT_RE` 取全檔**第一個** `thoughtLevel: ([a-z]+)` 與所有 ZCODE_PINS 的 effort 單值比對——**full 若給 effort 必須與 lite/vision 同值（high）**，否則 parity 邏輯要分叉改寫。effort 對譯表（SKILL.md:74-79）已裁「審查／判斷（review 委派）= high」「registry pins 標配= high」→ 同值 high 是零邏輯改動且合於權威表的選擇。

### 風險假設清單

| # | 假設 | 等級 | 驗證歸屬 |
|---|------|------|---------|
| RA-1 | `model: glm-5.3`（小寫旗艦 id）在 ZCode wire 可解析 | 高（非致命） | S3 首例遙測。支持證據：小寫 `glm-5.3-flash` pin 5705 筆實解析、大寫 runtime/小寫 pin 對稱成立（段落 0 查證）；flash-pin 同形態已驗證 |
| RA-2 | full 釘選後 `thoughtLevel: high` 受 sticky 但書管轄（定義值可能不達 wire） | 已知（不阻斷 model 軸） | S3 一併記錄 `variant`；open bug 家族 #339/#306（SKILL.md:68） |
| RA-3 | 釘選與 09-07 dispatch 放寬（審查類 muse/glm-5.3-flash 皆可）衝突 | 已消解（設計） | 見 S2 設計決定 D3：釘選=base 非強制；ZCode 無 spawn-time model 參數（memory 09-01 判例）→ 顯式降級＝換 lite-tier 載體或 muse bridge，條款不變 |

### C1-C7 調查宣稱對帳（不盲從條款執行結果）

| # | 判定 | 證據／推翻說明 |
|---|------|---------------|
| C1 | **verified** | git status=13 M/D＋3 untracked（impl-lite ×3）；`sync_agents.py --check` exit 0；pytest 28 passed；殘留掃描僅 2 類（tests/test_memory_lifecycle.py:114 flash-forensic 實名引用；skills/ui-visual-verify/SKILL.md L3/82/84/91/93 flash lane） |
| C2 | **verified**（額度數字屬「體驗套餐 5 天」語境） | ref-docs/harness/zcode/cn/docs/configuration.md L95-96（300萬/500萬 token/日，體驗套餐）、L220（GLM-5.3 thoughtLevel low/high/max、預設 max）、L235（GLM-5.3-Flash 多模截圖理解款） |
| C3 | **verified** | skills/model-routing/SKILL.md:92 歸因紀律段原文 |
| C4 | **verified**（並新增 de-risk 證據） | pin 逐字到 wire=vision-review 首筆實證（SKILL.md:68）；`glm-5.3` 無首例=屬實；新增：遙測 DB 小寫 pin 形態 5705 筆可解析、大小寫對稱成立——S3 仍是必要首例驗證 |
| C5 | **verified＋1 處補充** | 9 處全命中（rules/model-routing.md:22-23；skills/model-routing/SKILL.md:16,40,42,54-55,197；agents/AGENTS.md:96；scripts/sync_agents.py:45）＋**額外 SKILL.md:68**（但書段 inherit 字樣，原清單未列，一併處理） |
| C6 | **verified** | SKILL.md:42「原『full inherit 為基準＋保護面厚度條件降 lite』門檻就此放寬」＋「judge 裁決層不變：固定主 session GLM 5.3（AIR-24 三防線）」——S2 設計據此定釘選語義=base |
| C7 | **部分推翻** | 機制=env flag `MOSAIC_UI_VISUAL_SHOTS` **verified**（mosaic test_kchart_component.py:23,113-114）；但「mosaic_alpha repo 零 flash 牽連」**不成立**——同檔 L23 模組 docstring 本身寫「flash lane（opt-in，非測試 gate）：`MOSAIC_UI_VISUAL_SHOTS=<dir>`」，暱稱已滲入 mosaic 側 docstring（S4 若改名，mosaic 側為跨 repo 殘留——主 session 處置） |

---

## EP Review Findings

> 三方審查（GLM fresh＝code-reviewer／GLM primed＝code-reviewer-primed／muse bridge）findings 經主 session judge 後回寫；verdicts：fresh=有條件執行、primed=有條件執行、muse=needs-fix。三方共通正面結論：EP 錨點 30+ 處全命中、遙測數字三方獨立複驗吻合、段落依賴成立。採納項已即時回寫對應段落。

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| R1(fresh) | 🟡 | S2 | inherit 落點漏 review 鏈消費端 3 處（review-engine/SKILL.md:143、_common/agent-review-cycle.md:50、_common/workflow-review-pattern.md:161-162——皆「review agent 預設 inherit 主 session」）；殘留掃描僅掃 4 檔，支撐不了「ZCode full-tier inherit 語義歸零」全稱宣稱 | S2 文檔表加 3 列；掃描範圍擴 skills/ 全域＋5 處 pointer 行逐命中判讀 | implemented |
| F1(primed) | 🟡 | S2/SM-4 | SM-4 宣稱「SM-3 同機制」不實——「有值但未解析到」分支（sync_agents.py:146-148）零測試覆蓋，未來重構可靜默壞掉 | GREEN 後補 parity 釘住測試（fixture full 行維持舊形態→斷言 drift 訊息）；SM-4 行修正 | implemented |
| M5(muse) | 🟡 | S2/D2 | 權威表 full 行新 cell 未規約形狀——regex 捕獲組要求 id 緊跟欄位分隔，寫成「旗艦釘選 `glm-5.3`…」前綴形態即解析不到→parity fail | D2 補規約：cell 必以 backtick `glm-5.3` 開頭；RED2 fixture 貼真實行全文 | implemented |
| M6(muse) | 🟡 | S2 | S2 段落本體缺 deploy 步驟（整合策略有載，但 build 以段落為真相源；rules/model-routing.md 又改→bundle 必 stale） | 驗證策略補顯式 step（commit 後跑 deploy_agents.py，與 S1 對稱） | implemented |
| M7(muse) | 🟡 | S3 | glm-5.3 wire 可解析性宜在 S2 commit 前驗證，避免壞 pin 過夜 | pre-check 機械不可行（registry 快照制＋ZCode 無 spawn-time model 參數——pin 落地前無法 spawn 驗證）；改形態採納：S2 commit 後**立即**開新 session 跑 S3，失敗當場修 pin（單行＋resync 小 commit） | implemented（改形態） |
| M1(muse) | 🟡 | S3 | EP 引 agents/AGENTS.md:113「生效時機」，實際在 :21 | 錨點修正 :21 | implemented |
| M8(muse) | 🟡 | 整合 | S3 證據回寫 commit 歸屬模糊（「隨 S2 修正或收尾」） | 明寫獨立小 commit | implemented |
| M9(muse) | 🟡 | S5 | index.html 骨架超出卡 AC（scope creep；「骨架」驗收不機械） | 結案雙 ref 用 md viewer 過渡 URL（kanban-board 合約明載過渡形態）；殼骨架移後續項 | implemented |
| M2(muse) | 🟡 | S1 | 殘留掃描「僅剩 2 類」需人工判讀 | 給預期計數：排除後**恰好 6 hits**（1 實名＋5 lane） | implemented |
| M3(muse) | 🟡 | S1 | bundle 抽查只給 ~/.zcode 一條命令，另三家缺 | 四家部署路徑（deploy_agents.py TARGETS 段）各跑一條 rg | implemented |
| M4(muse)＋F2(primed) | 🟡 | S2 | inherit 殘留「逐命中判讀」主觀——SKILL.md:42 歷史句與 :68 但書句會誤命中 | 允許集白名單列舉（CC 端語義／歷史敘述句／claude 投影省略） | implemented |
| M10(muse) | 🟡 | S3 | since_ms 獲取點未定義 | step 補 `date +%s000` 記錄 | implemented |
| M11(muse)＋F3(primed) | 🟡 | S3 | 確認行 max=3 語義未定義且並發表無 glm-5.3 專列 | 寫明＝並發上限保守值（沿用 haiku 系=3 行） | implemented |
| R2-R7(fresh)、F4(primed) | ℹ️ | S1-S3 | R2 帳面（inherit 落點敘述）；R4 RED1 弱斷言（"model: glm-5.3" 是 "model: glm-5.3-flash" 子串——誤釘 flash 仍綠）；R5 parse_skill_effort docstring 過時；R6 SQL like 涵蓋 primed 未註記；R7 untracked 帳面；F4 provider 前綴形態（ZCode/、Grok/）屬 runtime 且跨 provider 漂移已實際發生（47+9 筆） | 各自順手修正，見對應段落改動 | implemented |
| B1(主 session) | ℹ️ | 後續項 | model-routing skill flag profile 表 drift：bridge 0.2.5 的 `review` 無 `--schema`（實為 git-diff 審查工具：--base/--json）、`task` 無 `--disable-write`（read-only 靠工單紅線）——本次 EP review dispatch 實測撞上 | 後續項登記（本 repo＝flag 表修正；跨 repo＝muse-plugin-cc roadmap） | 登記後續項 |

---

## UC 盤點

### Backlog 關聯

- **AIR-43**（唯一 To Do）——本 EP 對應卡，desc 四項已決策勿重辯
- 關聯已 Done 卡：AIR-24（lite 分工律＋judge 三防線——釘選不得違反）、AIR-29（agents 兩軸重構——投影管線本體）、AIR-38（路由詞彙 tier 非模型綁定——詞彙清理的法源）
- 自動建卡：**不需要**（三範圍項全由 AIR-43 覆蓋，無缺卡能力）

### SYSTEM-MAP 影響

- 無 SYSTEM-MAP.md（已掃，不存在）——提醒：本 repo 為治理 meta-repo，暫不建議建立

### 掃描範圍

- backlog `task list --plain`（僅 AIR-43 在 To Do）；memory 池 `~/.claude/projects/-Users-ctai-Github-ai-rules/memory/MEMORY.md`；受影響命令/rules 清單見「既有 UC 狀態」

### 同主題 memory 條目（結案蒸餾範圍）

| 條目 | 形態判讀 |
|------|---------|
| `project_flash-vocab-audit-0908` | **弧流水**（含「未 commit」「待 user consent」狀態詞＋「wire 首例無實證」）——S1/S3 完成後蒸餾為終態 |
| `reference_zcode-platform-facts` | 內建模型面段有「旗艦 id glm-5.3 作 pin 尚無首例實證（AIR-43 驗證段）」指針——S3 結果回填 |
| `reference_zcode-cc-subagent-model-thinking` | CC 別名實測（haiku→glm-5.3-flash）＋ZCode 無 spawn-time model 參數判例——S2/S 後續項引用 |
| `feedback_quota-failover-policy` | 09-07 dispatch 政策——C6 語義基準 |
| `project_flash-forensic-0905` / `project_air-38-routing-feedback-tier` | 歷史背景（不需改） |

### 既有 UC 狀態（docs mode：受影響命令/rules 清單）

| 能力／載體 | 狀態 | 影響 |
|-----------|------|------|
| model-routing 詞彙體系（rule＋skill 權威表） | ✅（AIR-38 落地） | 更新——tier 詞彙句不變，full 行從 inherit 改釘選 |
| agents 投影管線（sync_agents＋parity） | ✅（AIR-29 落地） | 更新——ZCODE_PINS 增 full 鍵＋regex 擴充 |
| lite 分工律（SKILL.md:83-93） | ✅（AIR-24 落地） | 無變更（條款不動；僅 dispatch 段加釘選語義句） |
| ui-visual-verify 編排配方 | ✅ | S4 條件更新（user 拍板後 flash lane→visual-shots lane） |
| agent-workflow Step 1 對照表 | 🟢 | 已知過時（opus→`glm-5-turbo` 為 5.3 前舊值＋缺 glm-5.3 列）——列後續項不在本弧修 |

### 新增 UC

| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| （無新增——AIR-43 卡即追蹤載體） | — | — |

---

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 主 session 手動切 flash 後 spawn code-reviewer | user 切模型＋spawn | agent 仍跑 glm-5.3（小寫 pin 形態，不漂移） | S3 遙測 model_id 斷言 | full-tier 釘選 |
| SM-2 | 主 session＝5.3（常態）spawn code-reviewer | 日常 | glm-5.3（行為不變，僅來源從大寫 runtime 變小寫 pin） | S3 遙測 | full-tier 釘選 |
| SM-3 | provider 換代：skill 權威表 full 行改值而 dict 未跟 | 改表忘改 dict | check_parity exit 2（fatal，非靜默舊 pin 上線） | parity 測試＋--check | 投影管線 parity |
| SM-4 | 權威表 full 行 zai 欄格式壞（非反引號 id 開頭） | 手改表格失誤 | _ZAI_PIN_RE 解析不到 → parity「有值但未解析到」fail loud（check_parity 另一分支 L146-148——與 SM-3 值不匹配分支不同路徑，各有測試釘住：SM-3＝既有 L270-282、SM-4＝S2 測試 #6） | parity 測試 #6＋--check | 投影管線 parity |
| SM-5 | 手改 agents/zcode/code-reviewer.md | UI/手動編輯生成物 | --check exit 1 列 drift（生成物 vs roles） | --check | 投影管線 |
| SM-6 | 裸 flash 殘留掃描 | commit 前驗收 | 0 殘留（排除 glm-5.3-flash/GLM-5.3-Flash 全名、ref-docs 鏡像、ai-analysis 歸檔、memory 實名引用、backlog 卡名） | S1/S4 驗證 | flash 去階層化 |
| SM-7 | S4 改名後搜 lane 名 | rg "visual-shots lane" | 命中 ui-visual-verify 全部用法＋grep 即得 env flag 名 | S4 驗證 | lane 改名（user 拍板後） |

---

## 段落劃分原則

- **S1 必須最先**：working tree 16 檔是前段成果，先 commit 鎖住乾淨 baseline——S2 疊改**同一批檔案**（rules/model-routing.md、skill、agents/AGENTS.md、sync_agents.py），不先切開會混提交語義
- **S3 依賴 S2 且需新 session**：registry 快照制（改定義同 session 不生效）；S3 指定給主 session／下個 session 執行（本弧 build session 改完定義後自身 spawn 驗不到新 pin）
- **S4 與 S2/S3 正交**（僅動 ui-visual-verify 一檔），可在 S1 後任意時點插入；含 user 決策 gate
- **語義約束（跨段共享）**：tier 詞＝requirement token（full/vision/lite）不變；「判斷密集位（judge/EP 規劃/post-build）＝主 session 直做不 agent 化」（AIR-24）不變；lite 分工律條款不變；desc 四項已決策勿重辯

---

## S1：詞彙清理 commit 承接＋全域 bundle 重部署

### Context

- **UC 引用**：落地「flash 去階層化」＋「vision＝支援影像的 model 定義」（AIR-43 範圍項 1/2——已在 working tree 完成，本段僅承接）
- **背景**：前段 session 已完成 impl-flash→impl-lite 改名（git mv 源＋pin key＋registry 重生成＋stale cleanup 自刪舊檔）、「flash 分工律」→「lite 分工律」跨檔引用、dispatch 簡稱全名化（glm-5.3-flash）、rules tier 詞彙句＋skill 影像行改寫（因果入檔：選 flash 因原生多模非因 lite tier）。驗證已過：`sync_agents.py --check` 綠＋`pytest tests/test_sync_agents.py` 28 綠（本 EP 段落 0 複驗同結果）
- **依賴**：無前置段落。**語義約束**：本段 commit 僅含 16 檔詞彙清理（見下方清單），不得混入 S2 改動或本 EP 檔案——`git add` 指名檔案（同 working tree 並行原則）
- **基礎設施盤點**：deploy_agents.py（bundle 重部署，rules/model-routing.md 在 bundle 內）；無程式改動
- **依賴錨點**：working tree 檔案清單＝機械清單（下方）；deploy 目標＝`~/.zcode/AGENTS.md` 等四家全域位置（AGENTS.md 檔頭註記）
- **技術選型／成功標準**：單一語義 commit＋四家 bundle 新詞彙可查

### 修改要點（無 Pseudo Code——純 commit 承接）

1. **commit 前複驗**（機械命令，全部綠才走 consent）：
   ```
   uv run python scripts/sync_agents.py --check
   uv run pytest tests/test_sync_agents.py -q
   git status --short   # 確認仍為 16 檔（13 M/D＋3 untracked），無新增意外改動；ai-analysis/_tasks/ EP 目錄 untracked 屬預期（指名 add 天然排除）
   ```
2. **commit 內容**（指名 add，僅此 16 檔）：
   - M：agents/AGENTS.md、rules/model-routing.md、scripts/sync_agents.py、skills/CLAUDE.md、skills/_common/illustrate-html-mode.md、skills/_common/workflow-review-pattern.md、skills/agent-workflow/SKILL.md、skills/blueprint-bootstrap/SKILL.md、skills/cross-verify/SKILL.md、skills/model-routing/SKILL.md
   - D：agents/claude/impl-flash.md、agents/roles/impl-flash.md、agents/zcode/impl-flash.md
   - 新增：agents/claude/impl-lite.md、agents/roles/impl-lite.md、agents/zcode/impl-lite.md
   - 訊息方向：`refactor(vocab): flash 去階層化——impl-flash→impl-lite、flash 分工律→lite 分工律、dispatch 簡稱全名化、vision＝支援影像的 model（AIR-43）`（主 session 定稿）
3. **commit consent gate**：主 session 展示變更摘要＋訊息，等 user 確認（outward-action-consent；EP 只規劃內容）
4. **commit 後全域重部署**：`uv run python scripts/deploy_agents.py`（rules/model-routing.md 有改→bundle 必須刷新；90KiB gate 若撞線按寫作治理「先修剪測試＋選對載體」處置）

### 驗證策略

- **文檔驗證（docs mode）**：
  - 部署後抽查 bundle：`rg -c "lite 分工律" ~/.zcode/AGENTS.md`（≥1）＋`rg -c "flash 分工律" ~/.zcode/AGENTS.md`（=0）
  - 殘留掃描（SM-6 基線）：`rg -i flash rules/ skills/ agents/ scripts/ tests/ hooks/ | grep -v -i "glm-5.3-flash"` → **預期恰好 6 hits**＝2 類刻留（test_memory_lifecycle.py:114 實名 ×1、ui-visual-verify flash lane ×5——後者歸 S4 處置）；多出或少於 6 即停下判讀
- **四家 bundle 抽查**：部署路徑清單見 `scripts/deploy_agents.py` TARGETS 段（:59-64）——四家各跑 `rg -c "lite 分工律" <部署檔>`（≥1）＋`rg -c "flash 分工律" <部署檔>`（=0）

---

## S2：full-tier 旗艦釘選——文檔＋程式＋測試（TDD）

### Context

- **UC 引用**：落地「full-tier 旗艦保障」（AIR-43 範圍項 3；desc 已決策③：ZCODE_PINS 增 full→glm-5.3，方向 user 已定）
- **背景**：洞機制＝unpinned subagent 跟 spawning session 模型走（SKILL.md:92 歸因紀律），主 session 可為 flash（手動切換/quota failover）→ full-tier agent（code-reviewer／code-reviewer-primed）漂移 lite 級，違 AIR-24 精神。**遙測實證洞已發生**（code-reviewer×392＋primed×107 requests 跑 GLM-5.3-Flash）
- **依賴**：S1 已 commit（同檔案疊改）；**語義約束**：與 S3 共享「pin 生效需新 session（快照制）」；與 S4 無交集
- **基礎設施盤點**：見段落 0（投影管線已泛化，程式面改動極小）
- **依賴錨點**（build 前驗證）：
  - `ZCODE_PINS` → 定義 scripts/sync_agents.py:46-49 / 消費 render_registry:231-233＋check_parity:141-157
  - `_ZAI_PIN_RE` → 定義 scripts/sync_agents.py:67-69 / 消費 parse_skill_zai_pins:105-112
  - tier 表 full 行 → skills/model-routing/SKILL.md:16；部署填法表 full 列 → :55
  - 測試契約 → tests/test_sync_agents.py:97-100（omit 契約——本段刻意反轉）、:297-310（parser fixture）
- **技術選型（設計決定 D1-D4）**：
  - **D1 pin 值＝`("glm-5.3", "high")`**。理由：(a) effort 必須與 lite/vision 同值（`_EFFORT_RE` 全檔首值單值比對的結構約束，異值=parity 邏輯分叉）；(b) effort 對譯表「審查／判斷（review 委派）= high」「registry pins 標配= high」（SKILL.md:77-78）已是權威裁決；(c) `high` 是 GLM-5.3 合法檔位（configuration.md L220）；(d) sticky 但書下定義值本就可能不達 wire（RA-2），實際 effort 由 S3 遺測記錄。**考慮過 model-only pin（thoughtLevel 省略）並拒絕**——需 tuple 型別分叉＋render 條件＋parity skip 三處邏輯改動，換到的只有「sticky 缺席時 effort 落模型預設 max 而非 high」，而對譯表已裁 review=high，非必要複雜度
  - **D2 skill 權威表 full 行 zai 欄改 backtick 形態**（regex 可解析的必要條件）：`GLM 5.3＝主 session inherit（不釘 id）〔repo-observed〕` → `` `glm-5.3` ``（旗艦釘選，AIR-43——inherit 洞修補）〔repo-observed；**registry pin wire 首例 first-real-usage-pending→S3 後改 repo-observed**〕。**cell 形狀規約（M5）**：欄位分隔符之後**必須立即**是 `` `glm-5.3` ``（regex 捕獲組要求 id 緊跟首欄——寫成「旗艦釘選 `glm-5.3`…」等前綴敘述形態會解析不到→parity fail）；佐證文字一律放 id 之後
  - **D3 釘選語義＝基準（base）非強制**，與 09-07 dispatch 放寬共存：ZCode 無 spawn-time model 參數（memory reference_zcode-cc-subagent-model-thinking 09-01 判例）→ dispatch 層的顯式降級＝換 lite-tier 載體（cr-research／cross-verify 形態）或 muse bridge，非改 code-reviewer 的 pin；「審查類 muse／glm-5.3-flash 皆可」條款與 AIR-24 judge 不變——文檔層以此句收進 SKILL.md:42
  - **D4 CC 端（agents/claude/）維持 inherit、本弧排除釘選**：CC 別名 opus 在 GLM provider 的映射目標未查證（agent-workflow Step 1 對照表 :57 仍列 `glm-5-turbo`——5.3 前舊值；memory 僅實證 haiku→glm-5.3-flash），且 CC 非日常主力 harness——釘選 CC 端需先查證映射，列「後續項」（見收尾後續清單），勿假設
- **成功標準**：TDD 綠＋parity 綠＋--map 顯示 code-reviewer=full＋zcode 生成檔帶 `model: glm-5.3`＋claude 生成檔不帶（對照不變）

### 核心實作要點

**程式（scripts/sync_agents.py，共 4 處）**：

```python
# 1) L43-45 註解改寫（原「full＝model 省略（inherit）故無列」刪除）：
# ZCode 部署預設 pins（值抄 skill tier×provider 權威表 zai 欄——
# check_parity 逐 tier 機械比對，改表不改 dict → fail）；
# full＝旗艦釘選（AIR-43 inherit 洞修補：unpinned 會跟主 session 漂移）

# 2) ZCODE_PINS 增鍵（排序：full/lite/vision 字母序）：
ZCODE_PINS: dict[str, tuple[str, str]] = {
    "full": ("glm-5.3", "high"),
    "lite": ("glm-5.3-flash", "high"),
    "vision": ("glm-5.3-flash", "high"),
}

# 3) _ZAI_PIN_RE alternation 擴充：
r"^\|\s*\*{0,2}(full|lite|vision)\*{0,2}（.*?）\s*\|\s*`?([a-z0-9.\-]+)`?"
```

# 4) parse_skill_effort docstring（L116）「lite/vision 共用一值」→「全 tier 共用一值」（full 加入後過時——R5）

render_registry（L231）與 check_parity（L141-157）**零改**——已泛化於 `requirement in ZCODE_PINS`／dict 迭代。

**文檔（inherit 落點 13 處——繼承 C5 9 處，補充：SKILL.md:68 但書句、agents/AGENTS.md:12/:41/:43；SKILL.md:54 為 CC 端語義保留不改、sync_agents.py:45 由程式改動 #1 承接；另 review 鏈消費端 3 處＝R1）**：

| 檔案:行 | 現況 | 改為 |
|---------|------|------|
| skills/model-routing/SKILL.md:16 | full 行 zai=inherit 不釘 id | D2 backtick 形態 |
| skills/model-routing/SKILL.md:40 | 「其餘角色 inherit 主 model」 | 「full-tier agent＝registry 釘 glm-5.3（AIR-43——不隨主 session 漂移）；lite 執行檔＝glm-5.3-flash」 |
| skills/model-routing/SKILL.md:42 | 審查類 dispatch 段 | 段尾加釘選語義句（D3）：「registry 釘選=base 非強制——顯式降級＝換 lite-tier 載體或 muse（ZCode 無 spawn-time model 參數）」 |
| skills/model-routing/SKILL.md:55 | full 列「`model` 省略（inherit）——任何 harness」 | 「ZCode：`model: glm-5.3`＋`thoughtLevel: high`（AIR-43 釘選）；CC：`model` 省略（inherit）——CC 別名映射未查證，見後續項」 |
| skills/model-routing/SKILL.md:68 | 但書「inherit 時不生效」 | 補一句：full 釘選後定義 thoughtLevel 進入但書管轄（sticky 在場記 user 值）——model 軸不受影響 |
| skills/model-routing/SKILL.md:197 | CC Workflow path「review agent = inherit」 | 標註「（CC 端；ZCode 端＝registry 釘選）」 |
| rules/model-routing.md:22-23 | 「full（inherit）為基準」×2 行 | 「full 為基準（ZCode＝registry 釘 glm-5.3——AIR-43；CC＝inherit）；條件式降 lite」——降級條款文字不動 |
| agents/AGENTS.md:12 | 「lite/vision 帶 model+thoughtLevel」 | 「lite/vision/full 帶 model+thoughtLevel」 |
| agents/AGENTS.md:41,43 | contract 表「full（省略 model）為基準」×2 行 | 「full（ZCode 釘 glm-5.3）為基準」 |
| agents/AGENTS.md:96 | 省略共用 model 行 | 修訂：省略=inherit 僅存於 CC 投影；ZCode 端 pins 全 tier 覆蓋（full 亦釘——AIR-43） |
| skills/review-engine/SKILL.md:143 | 「agent model 預設 = 主 session（inherit）」——review 執行預設單一源（五命令引用） | 補「（ZCode 端 full tier＝registry 釘 glm-5.3；CC＝inherit）」 |
| skills/_common/agent-review-cycle.md:50 | 「review agent 模型預設 = 主 session（inherit…）」 | 同上標註 |
| skills/_common/workflow-review-pattern.md:161-162 | JS 模板註解「review command agent = 主 session（inherit…）」 | 同上標註（模板行保留 CC 語義，註明 ZCode 端 spawn 走 registry pin） |

**測試（tests/test_sync_agents.py，TDD 順序）**：

```python
# RED 1（反轉 L97-100 契約）：
def test_render_zcode_full_pins_flagship():
    rendered = sync.render_registry("t-full", ROLE_FULL, "zcode", "full")
    head = rendered.split("\n---\n")[0]
    assert "model: glm-5.3\n" in head  # 精確斷言——防 "glm-5.3" ⊂ "glm-5.3-flash" 前綴假綠（R4）
    assert "thoughtLevel: high" in head

# RED 2（parser fixture L297-310 更新——full 行改 backtick 形態反映新表）：
#   fixture 權威表 full 行 → "| **full**（旗艦） | `glm-5.3`〔pin〕 | opus |"（cell 以 id 開頭——D2 規約；fixture 貼**真實表格行全文**而非簡化縮影——M5）
#   斷言 pins == {"full": "glm-5.3", "lite": "glm-5.3-flash", "vision": "glm-5.3-flash"}
#   （段落外誘餌行維持不解析）

# GREEN 後補：
# 3) golden bytes：zcode full 形態（model: glm-5.3＋thoughtLevel: high，仿 L414-436 手寫錨）
# 4) parity 值層 full 變體（仿 L270-282：skill full 行 glm-5.3→glm-6.0 → 斷言 ZCODE_PINS[full] drift）
# 5) 對照不變確認：test_render_claude_no_target_fields_and_strips_cr_mcp（L103-111）維持綠——CC 端零 model/thoughtLevel
# 6) SM-4 分支釘住（F1）：fixture 權威表 full 行維持舊 inherit 敘述形態（非反引號 id 開頭）→ 斷言 drift 含「ZCODE_PINS[full] 有值但 skill 權威表 zai 欄未解析到」——此分支（L146-148）先前零測試覆蓋，仿 L270-282 寫法約 6 行
```

### 驗證策略

- **TDD**：先改測試（RED：render full pins＋parser fixture）→ 跑 `uv run pytest tests/test_sync_agents.py -q` 見紅 → 實作 4 處程式改動＋13 處文檔 → 綠（含既有 28 中未動者全綠）
- **parity／投影閉環**：`uv run python scripts/sync_agents.py --check`（改表未 sync → exit 1 列 drift）→ `sync` → `--check` 綠 → `--map` 確認 code-reviewer／code-reviewer-primed=requirement full
- **生成物抽查**：`agents/zcode/code-reviewer.md` frontmatter 含 `model: glm-5.3`＋`thoughtLevel: high`；`agents/claude/code-reviewer.md` 不含 model/thoughtLevel（D4 對照）
- **殘留掃描（範圍擴全域——R1/M4/F2）**：`rg -n "inherit" rules/ agents/ scripts/ skills/` → 逐命中對白名單：①CC 端語義（「CC＝inherit」標註後形態）②歷史敘述句（SKILL.md:42「原『full inherit…』門檻就此放寬」——不改）③claude 投影省略 ④SKILL.md:54 lite/vision 行 CC 端 ⑤thoughtLevel 但書段語義句（「inherit 時不生效」——機制描述非路由宣稱）⑥5 處 pointer 行（execution-plan:305、deep-work:155、ep-review:28、code-review:56、implement:166 的「model inherit」摘要詞）→ 改為「model 預設」引用 review-engine 單一源；白名單外命中＝ZCode full-tier inherit 語義殘留，必須歸零
- **commit 後全域重部署（顯式 step——M6，與 S1 對稱）**：`uv run python scripts/deploy_agents.py`（rules/model-routing.md 又改→bundle 必 stale；90KiB gate 處置同 S1）＋四家抽查（同 S1 命令）
- **已知未覆蓋**：pin 是否真達 wire 是 S3（本段只保證生成物層正確）
- **commit**：與 S1 同 gate（主 session consent）；訊息方向 `feat(agents): full-tier 旗艦釘選 glm-5.3——AIR-43 inherit 洞修補（ZCODE_PINS+parity+文檔 13 處+tests）`

---

## S3：full pin 首例遙測驗證（L4，跨 session——主 session／下個 session 執行）

### Context

- **UC 引用**：AIR-43 驗收條款「full 釘選後 spawn 遙測 per-message modelID＝glm-5.3 實證」；desc「wire 解析首例待實證」
- **背景**：C4——`model: glm-5.3` 旗艦 id 字串在 ZCode wire 的實際解析**無首例**（flash 小寫 pin 已 5705 筆實證，形態對稱支持但非證據）。**快照制**：registry 改動同 session 不生效（agents/AGENTS.md:21「生效時機」；memory 判例「新 chat 判決」）——本段必須在 S2 sync＋commit **之後的新 session** 執行（寫 EP 的本 session 與 build session 都不行），且**緊接 S2 執行**（不隔夜、不疊其他段——pin 若不可解析當場修，避免壞 pin 過夜——M7 改形態）
- **依賴**：S2 完成（生成檔已帶 pin）；**語義約束**：驗證 spawn 用最低成本任務（如「Read 某 loan 檔給一行摘要」），read-only
- **基礎設施盤點**：遙測配方（段落 0）；python＋`file:...?mode=ro` URI

### 核心實作要點（執行程序）

1. 新 session（ZCode 重啟續接同對話亦可刷新快照——判決載體一律新 chat 最穩）；記錄 epoch ms：`date +%s000`（since_ms 用——M10）
2. spawn `code-reviewer`（背景 `run_in_background: true`；短任務；確認行 `[Agent] model=glm-5.3(full pin), max=3`——max=並發上限保守值，並發表無 glm-5.3 專列、沿用 haiku 系=3 行——M11/F3）
3. agent 完成後查遙測（時間窗用 spawn 前一刻的 epoch ms）：

```python
import sqlite3, time
con = sqlite3.connect('file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro', uri=True)
rows = con.execute("""
  select agent, model_id, variant, count(*) from model_usage
  where agent like 'zcode-code-reviewer%' and started_at > ?
  group by 1,2,3
""", (since_ms,)).fetchall()
```

4. 判讀（大小寫=來源；帶 provider 前綴〔`ZCode/`、`Grok/` 等〕亦屬 runtime 形態——F4，跨 provider 漂移已實際發生 47+9 筆）：`model_id='glm-5.3'`（小寫=registry pin）→ **首例實證成立**；SQL `like 'zcode-code-reviewer%'` 涵蓋 primed（同為 full pin）——兩者小寫命中皆屬實證成立、互為第二證據點（R6）；若出現 `GLM-5.3-Flash`／大寫 `GLM-5.3`／provider 前綴形態（=runtime inherit，pin 未生效——先查是否舊快照 session）→ 見 fallback
5. `variant` 一併記錄（RA-2：預期 `high` 或 sticky user 值——但書數據點）

### 驗證策略

- **通過**：小寫 `glm-5.3` 命中＋寫回三處——(a) skill 權威表 full 行證據標註 first-real-usage-pending→repo-observed；(b) EP 進度節記 SQL 輸出節錄；(c) memory `reference_zcode-platform-facts` 內建模型面段「尚無首例實證」句改為實證結果（含 variant 觀察）
- **fallback（pin 未生效）**：依序排查——① session 快照（是否新 chat）② `agents/zcode/code-reviewer.md` frontmatter 是否真帶 pin（`rg "model:" agents/zcode/code-reviewer.md`）③ provider 模型目錄實際 id 串（ZCode 設定→模型供應商面板；可能非 `glm-5.3` 字面）→ 修 pin 值→ resync → 重跑本段；不可解析則**標 unverified 回報 user**，禁腦補「應該有效」
- **已知未覆蓋**：sticky flip 實驗（分辨 sticky override vs silent no-op）不屬本段——SKILL.md:68 既有待跑項，本段 variant 觀察順帶累積數據點即可

---

## S4：flash lane 改名（user 決策點 D5）

### Context

- **UC 引用**：AIR-43 desc 殘餘項「ui-visual-verify flash lane 改名（建議 visual-shots lane，對齊 mosaic env flag MOSAIC_UI_VISUAL_SHOTS）待 user 拍板」
- **背景**：機制實名=env flag `MOSAIC_UI_VISUAL_SHOTS`（mosaic test_kchart_component.py:23,113-114 已驗證）；「flash lane」是 ai-rules 自創暱稱且**已滲入 mosaic 側 docstring**（同檔 L23——C7 推翻點）。三義混用（模型專名/階層代稱/測試通道）正是本弧清理對象
- **依賴**：S1 後即可（與 S2/S3 正交）；**user 決策 gate 前不動工**
- **語義約束**：改名僅動暱稱，機制（env flag、opt-in、不入 hard gate）不變

### 修改要點（user 拍板 visual-shots lane 後）

1. `skills/ui-visual-verify/SKILL.md` 5 處：L3（description 觸發詞「flash lane」→「visual-shots lane」）、L82、L84、L91（小節標題）、L93（真實案例行「flash lane 範本」→「visual-shots lane 範本」）
2. mosaic 側殘留（跨 repo——**主 session 處置或 mosaic session 做**，本 repo session 不 cd 過去）：`tests/integration_tests/ui/browser/test_kchart_component.py` L23 docstring「flash lane（opt-in…）」→「visual-shots lane（opt-in…）」——一行 docstring 改動，可與下次 mosaic 弧順帶；不動也不阻斷本弧驗收（殘留掃描範圍是 ai-rules repo）
3. 若 user 選保留「flash lane」：記錄理由（如歷史可讀性）於卡 notes，本段關閉

### 驗證策略

- `rg -n "visual-shots lane" skills/ui-visual-verify/SKILL.md` ≥5 命中且 `rg -i flash skills/ui-visual-verify/SKILL.md` =0（SM-7）
- 全域殘留掃描歸零覆核（SM-6：排除全名/歸檔/ref-docs/memory 實名/backlog 卡名後零命中）
- 觸發詞查驗：description 觸發詞與正文小節名一致（rg 兩詞互相對照）

---

## S5：收尾（卡結案＋memory 蒸餾＋EP 歸檔）

### Context

- **UC 引用**：AIR-43 驗收「EP 歸檔任務家」＋卡結案兩步（kanban-board 命令合約）
- **依賴**：S1-S4 全完成（S3 實證或 unverified 標記均屬可結案態——unverified 需 user 裁定）

### 修改要點

1. **結案兩步**：`backlog task edit AIR-43 -s In Progress`（開工時已做）→ 完成後 `-s Done --final-summary "<一句>"` → `--ref` 換 done/ 新 URL（EP 任務家遷 done/ 後），卡留 Done 欄
2. **memory 蒸餾**（弧結案第三動，見 UC 盤點清單）：`project_flash-vocab-audit-0908` 弧流水→終態（清「未 commit」狀態詞、收編釘選＋S3 實證結果）；`reference_zcode-platform-facts` 首例句回填；`MEMORY.md` 投影隨條目檔自動（禁手寫）
3. **instruction 檔同步檢查**：`skills/CLAUDE.md` 工作流索引的 model-routing description 行是否需反映 full 釘選；root AGENTS.md 無涉（專案結構段 pins 描述已在 agents/AGENTS.md 更新）
4. **/audit-test**：對 S2 修改後的 tests/test_sync_agents.py 跑品質稽核（反模式/覆蓋對稱性），結果附完成報告
5. **結案雙 ref 用 md viewer 過渡 URL**（`http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/<任務路徑>/ep.md`——kanban-board 合約明載過渡形態；report shell 骨架超出卡 AC，移後續項——M9）
6. **AC delta 揭露**（R3）：SM-6 排除集含「backlog 卡名」而卡 AC 字面僅列「模型全名／歸檔／ref-docs／memory 條目實名引用」——結案報告向 user 揭露此解釋擴張，避免 AC 判定基準爭議

---

## 整合策略

- **baseline**: 77eec0b（`git rev-parse HEAD` at EP 建立）——下游 code-review 任務弧的範圍邊界
- **commit 序列**：S1 詞彙清理（16 檔，單獨 commit）→ S2 釘選（文檔+程式+tests+生成檔，一 commit）→ S3 證據回寫（skill 標註升級 repo-observed＋EP 進度節＋memory 回填）＝**獨立小 commit**（M8）→ S4 視 user 決策（獨立小 commit）
- **跨 session 接續**：S3 指定新 session；EP 各段自足（本檔＋卡即開工材料）；`deploy_agents.py` 在 S1 與 S2 commit 後各跑一次
- **EP review 迴圈**：由主 session 於 EP 回收後執行（execution-plan skill「EP Review Cycle」——本背景 agent 無法 spawn 下層 agent，ZCode 子智能體不可巢狀）；findings 處置表寫回本檔末尾

## 收尾步驟（彙總——詳 S5）

1. Capabilities／instruction 檔：agents/AGENTS.md（S2 已動）＋skills/CLAUDE.md 索引覆核
2. Kanban：AIR-43 結案兩步（卡留 Done 欄）
3. memory：同主題條目蒸餾（見 UC 盤點表）
4. /audit-test（S2 測試面）
5. SYSTEM-MAP：不存在，跳過（正當跳過——meta repo）

## 後續項（本弧外，登記不擴 scope）

- **CC 端 full 釘選查證**（D4 排除理由）：CC session 實測 opus 別名映射（方法：memory reference_zcode-cc-subagent-model-thinking——transcript `rg -o '"model": ?"[^"]*"'`）→ 查證後更新 agent-workflow Step 1 對照表（:55-58，`glm-5-turbo` 舊值＋缺 glm-5.3 列）並考慮 CC 端釘選
- **sticky flip 實驗**（SKILL.md:68 既有待跑項）：S3 variant 數據點可作輸入
- **閃光殘餘最終態**：tests/test_memory_lifecycle.py:114（memory 條目實名引用）與 backlog 卡名為永久刻留，不改
- **model-routing skill flag profile 表修正**（B1——本次 EP review dispatch 實測撞上）：bridge 0.2.5 的 `review` 無 `--schema` 旗標（實為 git-diff 審查工具：`--base`／`--json`）、`task` 無 `--disable-write`（read-only 靠工單紅線承載）——skill「flag profile → spawn 參數」節需對齊安裝面；跨 repo 部分（flag 暴露）登 muse-plugin-cc bridge roadmap
- **report shell 骨架**（M9）：AIR-43 結案雙 ref 用 md viewer 過渡 URL；殼骨架（illustrate html-mode 基礎款）超出卡 AC，user 需要時另起

## User 決策點清單

| # | 決策 | 建議案 | 所在段 |
|---|------|--------|--------|
| U1 | S1 詞彙清理 commit consent | 照 S1 內容與訊息方向 commit | S1 |
| U2 | S2 釘選 commit consent | 照 S2 內容 commit | S2 |
| U3 | **flash lane 改名**（visual-shots lane vs 保留 vs 其他名） | **visual-shots lane**——對齊 env flag 實名（grep lane 名即得開關名）、消除第三義撞名；mosaic 側 docstring 一行順帶修（跨 repo 由主 session 處置） | S4 |
| U4 | （可否決）D1 effort=high／D4 CC 端排除 | 依設計理由維持；異議時回 S2 調整 | S2 |

---

## 進度結算（2026-09-08 build session）

- **S1 ✅**：commit `627dd67`（pre-commit hook 199 passed）＋`deploy_agents.py` 部署 4/4＋四家 bundle 抽查（`lite 分工律`=2／`flash 分工律`=0 全綠）
- **S2 ✅**：impl 執行檔＝impl-flash（glm-5.3-flash pin；本 session registry 快照為改名前舊名——spawn impl-lite 不存在的快照制實證，行為等價）TDD——RED 2 failed（形態正確）→ GREEN **31 passed**、`--check` 1→0 閉環、`--map` 兩 reviewer=requirement full、生成物釘選抽查（zcode 帶 pin／claude 對照無）；主 session git diff 機械對帳吻合後 commit `12a5673`（hook 全量 **202 passed**）＋部署 4/4＋四家抽查綠。**偏差 4 項**：①mypy 不存在於本 repo（pyproject dev deps＝pytest+ruff）——ruff 為靜態閘門，如實記錄非跳過②殘留掃描 4 hits 英文術語誤命中（inheritance chain 等）歸類③EP 測試 #5 由既有負向測試＋golden bytes 對照雙重承載，未複製④fixture 逐字 D2 證據標註
- **雙路審查 ✅**（範圍 `77eec0b..HEAD`＝S1＋S2 全在面內）：lite-verify（flash）**8/8 pass**（commit 邊界／測試重跑／SM-6 恰 6 hits／inherit 白名單 19 hits 歸類零漏／生成物／四家 bundle／vision 定義／斷言強度）；muse **accept**（四軸 ✅＋備註 6 條 judge 處置：M1 wire 首例→S3、M2 thoughtLevel 變生效之 variant 確認→S3、M3 成本方向反轉＝意圖內 trade-off 已向 user 報告、M4 觸發詞召回 pending 低風險、M5 backtick 不對稱化妝品不動、M6 部署端 symlink 零孤兒——已機械清案）
- **U4 默認生效**：D1（`("glm-5.3","high")`）／D4（CC 端本弧排除）未獲否決，照 EP 執行
- **S3 ✅（首例遙測驗證，09-08 新 session 執行）**：spawn `code-reviewer`（最低成本 read-only 任務，背景；agent 逐字引用正確回報）→ 遙測 SQL（`model_usage`，窗 `> 1788828176000`）scoped 命中 **`('zcode-code-reviewer', 'glm-5.3', 'max', 2)`**——小寫 pin 達 wire，**RA-1 首例實證成立**（M1 清案）。同窗對照組：主 session `zcode-agent` 大寫 `GLM-5.3-Flash`(5)/`GLM-5.3`(2)（runtime 形態——F4 大小寫對比錨）、registry pin 的 `zcode-impl-lite` 小寫 `glm-5.3-flash`(1)（同窗第二證據點）。**variant（M2/RA-2）觀察＝`max`**：非 frontmatter 定義值 `high`、全 agent（含主 session）一致 `max`——sticky 但書數據點（定義值不達 wire；分辨 sticky override vs silent no-op 屬 SKILL.md:68 既有 sticky flip 實驗，本段僅累積數據點）。備註：ZCode Agent 啟動輸出無 `[Agent] model=…` 確認行（M11 預期形未現身）——遙測 SQL 為唯一斷言面。寫回三處：(a) SKILL.md 權威表 full 行標註升級＋`test_sync_agents.py` fixture 同步；(c) memory `reference_zcode-platform-facts` 首例句回填（含 variant 觀察）
- **post-build docs 鏈**：skills/CLAUDE.md model-routing 索引行補 full 釘選語義（EP S5 item3）；consistency 以機械形態覆蓋（lite-verify #4/#6/#7＋muse 跨檔一致性軸＋AGENTS.md pin 治理句核對），未逐檔跑完整 /consistency skill——18 檔多為單行替換，完整單檔自洽可於 user 要求時補跑
- **S4 ✅**（user 拍板 U3＝visual-shots lane；本 build session 執行）：impl 執行檔（flash pin）兩 repo 共 7 處改名——ai-rules `skills/ui-visual-verify/SKILL.md` ×5（L3/82/84/91/93）＋mosaic `test_kchart_component.py` ×2（L23 docstring＋L108 註解——EP 原記 1 處，實為 2 處補改）；驗證五項全過（SM-7 ≥5 hits／skill 0 flash／觸發詞一致／SM-6 全域恰剩 1 hit＝test_memory_lifecycle.py:114 實名永久刻留／env flag `MOSAIC_UI_VISUAL_SHOTS` 計數不變）；muse 審查 **accept**（五軸全過、numstat 5/5＋2/2 恰合、無夾帶）。mosaic 側改動留 working tree（跨 repo——user 於該 repo 處置）
- **待辦**：卡結案兩步＋弧結案蒸餾（S5——S1-S4 全完成即可走）
