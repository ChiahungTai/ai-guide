# EP：rules audit × bundle 減量聯合弧（AIR-20）

> **ep_type**: implementation（docs mode——變更全為 `.md`、無 `.py` callable）
baseline: 8d3c6f6

## 實作總覽

bundle 87,676B＝gate（92,160B）95.1%，WARN 線（85%＝78,336B）已穿。本 EP 執行四段結構手術（降級 ×1、去重 ×1、合併 ×1、精簡 ×4 檔），預估淨減 ~6.5KB → ~81KB（~88% gate）。成長歸因＝AIR-18/19 刻意新增（非 drift），本弧是「加完料後的盤點收斂」。

〔已決策勿重辯〕
- 範圍凍結＝B1＋B2＋C1-C4＋A1（session 09-04 早 advisory，user 開 EP 即視為確認推薦組合）
- A2（modern-cli 陷阱群降級新薄 skill）、A3（memory 四問搬 memory-audit skill）＝**out of scope 待 user 裁決**——裁定併入時以追加段落處理（材料見 AIR-20 卡 notes）
- O 軸（guide 本身 10.5KB 減量）＝另弧，本 EP 不碰 guide 內文（僅 S3 改其一行連結）
- reference 分層先例（rule 留 always-on 核心＋pointer、深層住同名 skill）：acceptance-evidence / lsp-navigation
- 詞彙定義層不動：model-routing rule 的 tier 詞彙句（family／profile 詞彙單一源）保留在 rule；搬移的是「角色→family→profile 映射表＋eligibility gate＋reviewer 契約＋套用路徑」（派工單時才需要的知識群）

〔預估省量表〕（±30%，實值以 S5 deploy 輸出為準）

| 段 | 動作 | 預估淨減 |
|----|------|---------|
| S1 | model-routing external-runtime 段 rule→skill | ~2.2K |
| S2 | 工具路由句三重複去重 | ~0.3K |
| S3 | progressive-validation 併入 quality-constraints＋刪檔 | ~1.2K |
| S4 | C 批四檔內文精簡 | ~2.8K |

## 段落 0 研究摘要（09-04 session 內已完成，證據內嵌）

- **可複用落點**：`skills/model-routing/SKILL.md` 已有 External-runtime 解析表（family→model 值表＋flag profile 表，:23-49）——S1 搬移是收斂 rule/skill 雙寫，非新落點；skill description 觸發詞已含 external-runtime／eligibility／委派／工單
- **依賴關係（機械證據）**：
  - B1 ripple：`progressive-validation` 活引用 5 行（4 檔；audit-test 兩行）——`ai-development-guide.md:41`（連結）、`rules/AGENTS.md:50`（部署清單行）、`rules/acceptance-evidence.md:65`（關係段連結）、`skills/audit-test/SKILL.md:67,193`（審查維度引用）＋archive 2 檔（歸檔歷史不動）
  - A1 ripple：`external-runtime` 引用——`skills/_common/work-order.md`、`agents/AGENTS.md`（family 詞彙源指向）、`skills/CLAUDE.md`（索引）、`rules/AGENTS.md`
  - 工具路由句重複：`rules/modern-cli-preference.md:13` ≡ `rules/lsp-navigation.md:13`（lsp 版最完整）＋`rules/tool-discipline.md:13` 同義第三份
- **重量 census**（bundle 佔比）：tool-discipline 9,059B＞collaboration 7,561B＞acceptance-evidence 7,316B＞quality 6,427B＞model-routing 5,750B＞outward-action 5,402B
- **風險假設**：
  - 中：搬移後 spawn 端找不到 eligibility gate—— mitigated by skill description 觸發詞已覆蓋；S1 驗證含此項
  - 中：C 批精簡誤刪行為約束——S4 定「保留清單」逐檔核對
  - 低：省量預估偏差——實值以 deploy 輸出為準，accept 標準是 gate 狀態非絕對 KB 數
- **死路假設排查**：progressive-validation 內容有活消費者（5 檔引用）——併入而非單純刪除，無死路

## EP Review Findings

> 雙審查（muse bridge + GLM F1-F5 agent，09-04）。muse 4 項流程級（staging 補齊/baseline 對齊已採納；localhost URL 不採納——kanban 雙 ref 慣例必要項）屬卡與 staging 層，不入本表。GLM 9 🟡＋6 ℹ️ 逐項判讀如下，全數採納並回寫各段。

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| F3-1 | 🟡 | 整合策略 vs S2 語義約束 | 執行順序矛盾（S4 的 C1 依賴 S2 壓縮後的 tool-discipline，但順序 S4 在 S2 前） | 改序（S2∥S3）→ S4 → S1 → S5 | implemented |
| F1-1 | 🟡 | S3 驗證 vs 修改要點 | guide 現文無 "DEPTH-MIN"，驗證命令必失敗或誘導硬湊 | :41 新連結文字明定含 DEPTH-MIN | implemented |
| F1-2 | 🟡 | S1 修改要點 | :27-71 內兩夾層 blockquote（:43 review 邊界、:55 sandbox --yolo）不在「四塊」清單——孤兒化風險 | 明列歸屬隨所屬塊搬 skill | implemented |
| F4-1 | 🟡 | S1 ripple | work-order.md §8 例句 :61-63 直接掃 rule 的 needs-fix 等——S1 後落空 | ripple 擴及 §8 例句 | implemented |
| F5-1 | 🟡 | SM-2/SM-4 | rg `\|` 是 literal pipe（本 repo 自載陷阱）＋SM-4 模式詞不存在於目標檔（vacuous check） | 改 `-e` 形態＋實際用語 | implemented |
| F5-2 | 🟡 | SM-1/SM-6 | deploy broken-ref guard 不攔刪檔死鏈——S3 漏改會靜默進 bundle | 部署端點抽查（舊引用歸零＋新錨點在場） | implemented |
| F4-2 | 🟡 | S1 ripple | rules/AGENTS.md:67 model-routing 行描述 S1 後過時 | 加核對項 | implemented |
| F3-2 | 🟡 | S4 C4 | 錨點含糊——對照表實在 :41-47（:63-65 是散文段）且 C4 基線是 S3 後狀態 | 明確行錨點＋基線標記 | implemented |
| F1-3 | 🟡 | S3 保留清單 | 「最小集合選擇原則」三條（:31-35）去向未明——行為指導靜默丟失風險 | 收斯為一句保留 | implemented |
| ℹ-1 | ℹ️ | 研究摘要 | 「活引用 5 檔」實為 5 行（4 檔） | 改標籤 | implemented |
| ℹ-2 | ℹ️ | S2 | shorthand link 不被 deploy LINK_PATTERN 認 | 落完整 markdown link | implemented |
| ℹ-3 | ℹ️ | S2 | agents/* code-reviewer.md :21 有路由句變體（第四~六份） | 註記刻意不動 | implemented |
| ℹ-4 | ℹ️ | S3 | upgrade-flow.md:53-93 DEPTH 詞彙自包含 | 註記供術語掃參考 | implemented |
| ℹ-5 | ℹ️ | S5 | skills/CLAUDE.md :130 index 行描述完整性＋description 缺「reviewer 交接」觸發詞 | 核對清單擴及 | implemented |
| ℹ-6 | ℹ️ | F2 整體 | 合規面通過（無元資訊計畫、pointer 中性、neutral→neutral 搬移） | — | 無動作 |

## UC 盤點（docs mode——受影響 rules/skills 清單）

### 受影響清單

| 檔案 | 動作 | 段 |
|------|------|----|
| `rules/model-routing.md` | external-runtime 段降級（刪映射表/gate/契約/套用，留 pointer） | S1 |
| `skills/model-routing/SKILL.md` | 搬入四塊（映射表放值表前、gate/契約放值表後） | S1 |
| `skills/_common/work-order.md`、`agents/AGENTS.md` | family 表引用指向改 skill | S1 |
| `rules/lsp-navigation.md` | 路由句單一源（不動內容，成為唯一源） | S2 |
| `rules/modern-cli-preference.md`、`rules/tool-discipline.md` | 路由句改壓縮＋pointer | S2 |
| `rules/progressive-validation.md` | **刪檔**（內容壓縮併入） | S3 |
| `rules/quality-constraints.md` | 新增「漸進式驗證」段 | S3 |
| `ai-development-guide.md:41`、`rules/AGENTS.md:50`、`rules/acceptance-evidence.md:65`、`skills/audit-test/SKILL.md:67,193` | 引用改指 | S3 |
| `rules/tool-discipline.md`、`rules/collaboration-constraints.md`、`rules/outward-action-consent.md`、`rules/acceptance-evidence.md` | 內文精簡 | S4 |
| `skills/CLAUDE.md` | model-routing description 觸發詞覆蓋確認 | S5 |

### Backlog 關聯

- 追蹤卡：AIR-20（In Progress；references 已掛本 EP）
- 新增 UC：無（治理弧，無新能力）——「rule 降級搬移」模式已有先例，非新 UC

### SYSTEM-MAP 影響

- 無 SYSTEM-MAP.md（元專案，正當跳過）

## Scenario Matrix（docs mode——文檔語境：rg 命中／0 殘留）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | deploy gate 未爆 | `uv run python scripts/deploy_agents.py` | exit 0；bundle <92,160B（預估 ~81K）；無 FAIL | 部署 backup 檔 | — |
| SM-2 | 搬移斷鏈 | `rg -e "eligibility gate" -e "reviewer 交接" rules/model-routing.md` | rule 端僅 pointer 行；skill 端全文在場 | 無 | — |
| SM-3 | 刪檔孤兒引用 | `rg -l "progressive-validation"` 排除 archive／任務家／backlog | 活引用 0 殘留 | 無 | — |
| SM-4 | 詞彙源漂移 | `rg -n "rules/model-routing" skills/_common/work-order.md agents/AGENTS.md` | 命中行中指向 model-routing 來源者已改指 skill（alternation 一律 `-e` 形態——`\|` 是 rg literal-pipe 陷阱） | 無 | — |
| SM-5 | 精簡傷語義 | S4 每檔「保留清單」關鍵詞 rg | 核心約束詞命中不變 | git revert（單檔） | — |
| SM-6 | 部署同步＋死鏈抽查 | deploy 後 cmp 三家全域檔＋端點抽查：`rg "漸進式驗證" ~/.zcode/AGENTS.md` 在場、`rg -c "progressive-validation" ~/.zcode/AGENTS.md` = 0 | 內容一致＋新錨點在場、舊引用零殘留（deploy broken-ref guard 不攔刪檔死鏈） | 重跑 deploy | — |

## 段落劃分原則

依賴順序：S3 先於 S4（acceptance-evidence 同檔——S4 的 C4 以 S3 併入後的新錨點為準）；S1/S2 互不依賴可平行；S5 收尾最後。每段驗證自足（rg 殘留＋deploy 可單段跑）。

---

## S1：model-routing external-runtime 段降級（rule→skill 收斂雙寫）

### Context

rule `rules/model-routing.md:27-71` 的 external-runtime routing 段（定位句 :27-29、family 映射表 :31-43、eligibility gate 五條 :45-55、reviewer 交接契約 :57-61、套用三路徑 :63-69、pointer :71）是「派工單時才需要」的知識群；skill `skills/model-routing/SKILL.md` 已承載同域值表（:23-49）。always-on 正當性只到「tier 表＋兩跳解析＋詞彙句」。

- **依賴錨點**：源 `rules/model-routing.md:27-71`；目標 `skills/model-routing/SKILL.md:23`（External-runtime 段）；ripple `skills/_common/work-order.md`＋`agents/AGENTS.md`（rg `family` 定位引用行）
- **語義約束**：與 S5 共享 gate 目標；tier 詞彙句（:23 附近「family／profile 詞彙單一源」）**不動**——詞彙定義留 rule，映射表搬 skill
- **技術選型**：搬移非改寫——四塊內容原文搬入 skill，僅段落銜接句微調
- **成功標準**：SM-2＋SM-4 過；bundle 淨減 ~2.2K

### 修改要點

1. rule 端：§external-runtime routing 段壓縮為——段頭＋定位一句（policy 家族軸）＋一行 pointer（「角色→family→profile 映射、eligibility gate 五條、reviewer 交接契約、套用三路徑——見 model-routing skill」）。既有 :71 pointer 段併入。段內兩個夾層 blockquote 隨所屬塊**原文搬 skill**（禁孤兒化）：:43「兩種 review 邊界」隨 family 表、:55「sandbox-error 禁 --yolo」隨 eligibility gate
2. skill 端 External-runtime 段擴：映射表插值表前（「角色→family→profile」與「family→model 值」兩表相鄰）；eligibility gate＋reviewer 交接契約插值表後；套用三路徑併入段尾
3. ripple：work-order.md／agents/AGENTS.md 中「family 表在 rules/model-routing.md」類指向 → 改 skill；work-order.md §8 驗收例句 :61-63 直接掃 rule（needs-fix 例句 S1 後落空）→ needs-fix 例句改掃 `skills/model-routing/SKILL.md`，:61-62 eligibility/external-runtime 例句語義核對；`rules/AGENTS.md:67` derived overview 的 model-routing 行描述（「family 軸（在 rule）」）過時則更新；rule 端 tier 詞彙句的「agents/AGENTS.md 與工單模板引用之」語義核對（詞彙定義仍在 rule，引用仍合法則不動）

### 驗證策略

- `rg -n "eligibility|reviewer 交接|套用（三路徑" rules/model-routing.md` → 僅 pointer 行命中
- skill 端四塊全文 rg 命中；description 觸發詞已含（不另改）
- work-order/agents-AGENTS 指向行 rg 驗證
- 單段跑 deploy 看 bytes 變化（可逆驗證）

---

## S2：工具路由句三重複去重

### Context

「符號→code-reality、型別→bridge、文字→rg、檔案→fd」路由句三處：`rules/modern-cli-preference.md:13` ≡ `rules/lsp-navigation.md:13`＋`rules/tool-discipline.md:13` 同義。三份同義句是 drift 面（改一處漏兩處——single-source drift 防護的反模式）。lsp-navigation 是 cr-first 專門檔且句子最完整 → 單一源。

- **依賴錨點**：三檔 :13（現況 rg 已驗證）
- **語義約束**：三檔各自身分不變——modern-cli＝搜尋工具分工（fd/rg＋陷阱）、lsp-navigation＝符號/圖譜查詢路由、tool-discipline＝工具紀律總表；S4 的 C1 精簡 tool-discipline 時以本段壓縮後版本為基礎
- **成功標準**：`rg "code-reality（index 在場" rules/` 僅 lsp-navigation 一處

### 修改要點

1. lsp-navigation :13 不動（成為唯一源）
2. modern-cli 核心原則段壓縮：「文字搜尋用 rg、檔案搜尋用 fd（預設遵守 .gitignore，減少噪音）；符號/圖譜與型別面路由見 [lsp-navigation.md](lsp-navigation.md)」——fd/rg 身分保留、符號路由讓出
3. tool-discipline :13 bullet 壓縮：「工具四路路由（符號→code-reality、型別→bridge、文字→rg、檔案→fd）見 [lsp-navigation.md](lsp-navigation.md)；本檔載紀律與陷阱」
4. 實作註記：pointer 一律完整 markdown link 形態（`[lsp-navigation.md](lsp-navigation.md)`——deploy LINK_PATTERN 只認完整形態，shorthand 不算）；`agents/shared|claude|zcode/code-reviewer.md:21` 的 rg/fd 子集句為已知變體——agent prompt 自包含性質，**刻意不動**

### 驗證策略

- `rg -n "code-reality（index 在場" rules/` → 僅 1 命中
- 三檔互相 link rg 驗證（pointer 有效性）
- deploy bytes 記錄

---

## S3：progressive-validation 併入 quality-constraints＋刪檔

### Context

`rules/progressive-validation.md`（2,371B；inbound 最低群、2 個月零 commit）與 quality-constraints 同屬驗證紀律（後者＝驗證深度與標準，前者＝驗證順序 DEPTH-MIN→SAMPLE→FULL），guide :41 兩者並列引用。併入收斂主題、省檔案 scaffolding＋separator。

- **依賴錨點**：源 `rules/progressive-validation.md` 全檔；目標 `rules/quality-constraints.md`（驗證相關段落後）；5 個活引用行（研究摘要已列 file:line）
- **語義約束**：併入段是**壓縮**（~2.4K→~1.2K：核心原則一句＋三層表＋最小集合選擇原則一句〔覆蓋多分支、3-5 個、含已知易錯案例〕＋禁止行為三條＋為什麼一句），非全文照搬；「與風險分級的關係」段（兩者互補論述）一併收斂為一句；archive 引用不動（歸檔歷史）
- **成功標準**：SM-3 過；quality-constraints 含 DEPTH 三層錨點可被 guide/audit-test 連結

### 修改要點

1. quality-constraints 新增「## 漸進式驗證（DEPTH-MIN→SAMPLE→FULL）」段（壓縮版）
2. 刪 `rules/progressive-validation.md`
3. 改 5 引用：guide :41 新連結文字明定含 DEPTH 錨點——「漸進式驗證（DEPTH-MIN→FULL）見 [quality-constraints.md](rules/quality-constraints.md)」（使驗證命令的 guide `DEPTH-MIN` 命中成立，不誘導硬湊）；rules/AGENTS.md :50 部署清單行刪；acceptance-evidence :65 連結與句子微調（同檔併提）；audit-test :67 表格行＋:193 定義連結改指
4. 註記：`skills/_common/upgrade-flow.md:53-93` 使用 DEPTH 詞彙但自包含（不連 progressive-validation）——無斷鏈免動，供 sync-sources 術語掃參考

### 驗證策略

- `fd progressive-validation rules/` → 不存在
- `rg -l "progressive-validation" --glob '!ai-analysis/**' --glob '!backlog/**'` → 0 命中
- `rg "DEPTH-MIN" rules/quality-constraints.md ai-development-guide.md skills/audit-test/SKILL.md` → 命中在場
- deploy bytes 記錄

---

## S4：C 批四檔內文精簡

### Context

四檔合計 ~29KB（bundle 33%）。精簡不改語義——每檔先列「保留清單」（不可刪的核心約束詞），刪的是實例展開、重複論述、與 skill 重疊段。

- **依賴錨點**：四檔（C1 `rules/tool-discipline.md` zsh 段＋背景執行段；C2 `rules/collaboration-constraints.md` 對比格式段＋Agent 派發段；C3 `rules/outward-action-consent.md` 場景表＋Source of truth 邊界段；C4 `rules/acceptance-evidence.md` 「與既有規則的關係」段）
- **語義約束**：**S3 先行**——C4 精簡 acceptance-evidence 時引用新錨點；C1 以 S2 壓縮後的 tool-discipline 為基礎；C3 保守——reversibility test 全文＋AUTH line 模板＋commit 專屬段**全文保留**（安全核心），只收斂與 autonomous-execution skill 重疊的邊界論述
- **成功標準**：SM-5 過；每檔淨減且保留清單詞 rg 命中不變

### 修改要點（每檔保留清單）

1. **C1 tool-discipline**：zsh 段三規則＋一案例句保留、其餘實例刪；背景執行「為什麼」與「例外」合併一段論述。保留詞：`zsh`、`args=(`、`run_in_background`、`TaskOutput`、`block=true`
2. **C2 collaboration-constraints**：對比格式模板保留、範例塊收短；Agent 派發三條收緊（每條一句）。保留詞：`/tmp`、`agent-tmp`、`worktree`、`澄清一次問完`
3. **C3 outward-action-consent**：場景表壓縮至代表行、Source of truth 邊界段併一句＋pointer autonomous-execution skill。保留詞：`AUTH: user said`、`reversibility`、`commit`、`PENDING`
4. **C4 acceptance-evidence**：精確錨點＝「根本禁令」下的既有禁令↔冒充關係**對照表（:41-47）**（非 :63-65 散文關係段——兩處名稱相近）→ 一句總結＋連結（S3 後的 quality-constraints 新錨點）；**C4 基線＝S3 後狀態**（:65 已被 S3 改過）。保留詞：`L1`、`L4`、`證據獨立`、`Claim→Evidence`

### 驗證策略

- 每檔保留詞 rg 命中不變（before/after 對照）
- 精簡後通讀一遍（段落銜接不成孤兒——feedback_cjk-char-corruption-rg-verify 教訓）
- deploy bytes 記錄

---

## S5：收尾——deploy＋gate 驗證＋同步掃描＋結案

### 修改要點

1. `uv run python scripts/deploy_agents.py` → gate 檢查：exit 0＋bundle <92,160B（預估 ~81K/~88%；accept 標準＝無 FAIL，KB 數為參考）
2. 三部署檔 cmp（`~/.zcode/AGENTS.md`、`~/.config/opencode/AGENTS.md`、`~/.codex/AGENTS.md`）＋**部署端點抽查**：`rg "漸進式驗證" ~/.zcode/AGENTS.md` 在場、`rg -c "progressive-validation" ~/.zcode/AGENTS.md` = 0（deploy broken-ref guard 不攔刪檔死鏈——此抽查承接 `rules/AGENTS.md` 部署驗證義務）；Claude 端 rules/ symlink 抽查（目錄 symlink，刪檔即時反映）
3. sync-sources 機械新鮮度三掃描（互引／部署／術語）
4. `skills/CLAUDE.md` 工作流索引：model-routing 的 description 觸發詞覆蓋（已含 external-runtime/eligibility——可一行補「reviewer 交接」）＋ :130 index 行描述完整性（S1 後 skill 承載 gate/契約/套用，描述行應反映）
5. backlog AIR-20 結案兩步（`-s Done --final-summary` → `--ref` 換 done/ URL）；EP 任務家遷 `ai-analysis/_tasks/_archived/09-04-rules-bundle-diet/`
6. A2/A3 裁決狀態記入卡（未裁＝out of scope 留待後續；裁併入＝本 EP 追加段落後再結案）

### 驗證策略

- SM-1＋SM-6；deploy 輸出貼 EP（實際 bytes vs 預估）
- `backlog_precheck.sh` 於結案前跑

## 整合策略

段落執行順序：（S2 ∥ S3 互不依賴，序列執行 S2 → S3）→ S4 → S1 → S5——S2 先於 S4（tool-discipline :13 壓縮是 C1 的基礎）、S3 先於 S4（acceptance-evidence :65 改動是 C4 的基線）。每段完跑單段驗證＋deploy bytes 記錄（進度可結算）；中斷接續靠本 EP 段落自足。全部完成後 post-build 收尾鏈（code-review dual-context ≥3 files）→ commit（user 確認）。

## Invariant Impact

無（docs mode，無 domain invariant／silent-corruption path）。
