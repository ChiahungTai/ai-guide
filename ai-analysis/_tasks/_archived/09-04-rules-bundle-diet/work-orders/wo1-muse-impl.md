# WO-1：AIR-20 EP S1-S4 手術批＋S5 部署驗證項（docs mode）

## 1. 紅線（違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡狀態——止步於 working tree 編輯
- 禁把產物／中間筆記寫到 `/tmp` 或 repo 外（部署腳本寫各家 harness 全域位置是其既定行為，允許）
- 禁派發子 agent／委派語言（任務本文自行完成）
- 紅線違反＝失敗；審查未過不得視為完成

## 2. 目標（一句話）

執行 AIR-20 聯合弧 EP 的 S1-S4 四段結構手術（model-routing 降級／路由句去重／progressive-validation 併入／四檔精簡）＋S5 部署驗證項，把 always-on bundle 從 gate 95.1%（87,676B/92,160B）降到 ~88%。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree，非 worktree）
- 工作目錄：repo root
- base commit：`8d3c6f6`
- 並行改動聲明：working tree 已有 staged 改動——`backlog/`（AIR-20 卡＋draft 刪除）與 `ai-analysis/_tasks/09-04-rules-bundle-diet/ep.md`（本弧治理產物）；這些**不屬於你的改動**，`git diff` 對照時排除

## 4. 必讀（按序，絕對路徑）

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-04-rules-bundle-diet/ep.md`——全文（尤其〔已決策勿重辯〕、S1-S5 各段「修改要點」與「語義約束」、Scenario Matrix SM-1~SM-6）
2. `/Users/ctai/Github/ai-rules/rules/model-routing.md`——S1 手術對象（:27-71 external-runtime 段）
3. `/Users/ctai/Github/ai-rules/skills/model-routing/SKILL.md`——S1 搬移目標（:23 起 External-runtime 段）
4. `/Users/ctai/Github/ai-rules/rules/AGENTS.md`——部署紀律＋機械檢查清單（動 rules/ 後的義務）

## 5. 已決策（勿重辯）＋矛盾例外

- 範圍凍結＝S1（A1）＋S2（B2）＋S3（B1）＋S4（C1-C4）＋S5 項 1-4；**A2／A3／O 軸不做**（out of scope，user 待裁）
- 執行順序（EP 整合策略，EP review 後修正）：**S2 → S3 → S4 → S1 → S5 項 1-4**——S2 先於 S4（tool-discipline :13 壓縮是 C1 基礎）、S3 先於 S4（acceptance-evidence :65 是 C4 基線）
- reference 分層模式：rule 留 always-on 核心＋pointer、深層住同名 skill（先例 acceptance-evidence／lsp-navigation）
- `rules/model-routing.md` 的 tier 詞彙句（family／profile 詞彙單一源）**不動**——搬的是映射表＋gate＋契約＋套用，非詞彙定義
- S3 刪檔=progressive-validation 內容**壓縮**併入 quality-constraints（~2.4K→~1.2K），非全文照搬；archive 歷史引用不動
- S4 每檔「保留清單」詞（EP S4 段內列）刪後必須仍 rg 命中；outward-action 的 reversibility test 全文＋AUTH line 模板＋commit 專屬段全文保留
- 被改檔案禁加元資訊／統計數字／日期（instruction-writing 慣例）
- **矛盾例外**：發現檔案現況與 EP 錨點（file:line）具體衝突時，停下在報告舉證（file:line＋逐字引用），不自行改設計也不靜默照做

## 6. 範圍限定

**動**（僅下列檔案）：
- `rules/model-routing.md`（S1 壓縮 external-runtime 段）
- `skills/model-routing/SKILL.md`（S1 搬入四塊）
- `skills/_common/work-order.md`、`agents/AGENTS.md`（僅 family 指向行改指 skill）
- `rules/modern-cli-preference.md`、`rules/tool-discipline.md`（S2 路由句壓縮；tool-discipline 另有 S4 C1 精簡）
- `rules/lsp-navigation.md`（S2 唯一源確認——預期零修改；若需微調以成為唯一源為限）
- `rules/progressive-validation.md`（S3 刪檔）
- `rules/quality-constraints.md`（S3 併入段）
- `ai-development-guide.md`（僅 :41 一行連結）、`rules/AGENTS.md`（僅部署清單行）、`rules/acceptance-evidence.md`（S3 引用行＋S4 C4 精簡）、`skills/audit-test/SKILL.md`（僅 :67/:193 引用行）
- `rules/collaboration-constraints.md`、`rules/outward-action-consent.md`（S4 C2/C3 精簡）
- `skills/CLAUDE.md`（僅當 model-routing 觸發詞覆蓋不足時補該行——預期免改）
- 執行（非修改）：`uv run python scripts/deploy_agents.py`

**不動**：其他一切——尤其 `agents/zcode/*.md`、`hooks/*`、`scripts/*`、`tests/*`、其他 skills、`CLAUDE.md`（repo root）、memory 池。交付報告附 `git diff --name-only` 舉證未越界。

## 7. 工具接線

- 讀查：`bash`（`cat`／`rg`／`ls`）＋檔案讀取；字串搜尋一律 `rg`；修改一律整檔／區段編輯（禁 `sed` 改檔）
- 最小可用：不引入非必要工具
- 三禁令：禁 code-reality 寫入面；禁任何輸出寫 repo 外（部署腳本例外見紅線）；禁遇缺口自行繞路（停下舉證）

## 8. 驗收（命令＋預期，逐條實跑附原始輸出）

1. `rg -n "eligibility|reviewer 交接契約|套用（三路徑" rules/model-routing.md` → 僅 pointer 語義行命中（≤3 行）
2. `rg -n "eligibility gate|reviewer 交接" skills/model-routing/SKILL.md` → 兩詞皆命中
3. `rg -n "code-reality（index 在場" rules/` → 僅 `rules/lsp-navigation.md` 1 檔命中
4. `test ! -f rules/progressive-validation.md && echo GONE` → 輸出 GONE
5. `rg -l "progressive-validation" /Users/ctai/Github/ai-rules --glob '!ai-analysis/**' --glob '!backlog/**'` → 零命中
6. `rg -n "DEPTH-MIN" rules/quality-constraints.md` → ≥1 命中
7. S4 保留詞抽查：`rg -c "AUTH: user said" rules/outward-action-consent.md` → ≥1；`rg -c "args=(|run_in_background" rules/tool-discipline.md` → ≥2 處（兩詞各≥1）；`rg -c "澄清一次問完" rules/collaboration-constraints.md` → ≥1；`rg -c "Claim→Evidence" rules/acceptance-evidence.md` → ≥1
8. `rg -n "rules/model-routing" skills/_common/work-order.md agents/AGENTS.md` → 命中行中指向 model-routing 來源者已改指 skill（含 work-order §8 例句 :61-63——needs-fix 例句改掃 `skills/model-routing/SKILL.md`）
9. `uv run python scripts/deploy_agents.py` → exit 0；輸出的 bundle bytes 記錄（硬標準 <92,160；預期 ~81K）
10. `rg -n "文字搜尋用 rg" rules/modern-cli-preference.md` → 仍命中（fd/rg 分工身分保留）但同一行不含「符號/圖譜查詢用 code-reality」完整路由句
11. 部署端點抽查：`rg "漸進式驗證" ~/.zcode/AGENTS.md` → ≥1 命中；`rg -c "progressive-validation" ~/.zcode/AGENTS.md` → 0

## 9. 證據紀律＋PII 禁令

- 每條驗收附完整命令與原始輸出（截斷標明）；宣稱「沒改 X」附 `git diff --name-only` 佐證
- 報告禁出現 email／人名等 PII
- 宣稱需獨立證據；失敗如實記錄不掩蓋

## 10. 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單（對應 `git diff --name-only`，標注 staged 並行改動之排除）
2. 逐段落落實說明：S1 四塊／S2 三處／S3 五引用＋併入段／S4 四檔各落在哪（file:line 級對照）
3. 驗收 1-10 命令與原始輸出
4. 偏差記錄：與 EP 規格出入處＋原因（EP 是收斂方向非合約，偏差是發現不是違規——但必須記錄）
5. 未驗證項／被阻擋項（無則標「無」）
6. 建議 reviewer 聚焦點（最有信心不足之處）
7. 附：jobId／thread id、deploy 實測 bundle bytes
