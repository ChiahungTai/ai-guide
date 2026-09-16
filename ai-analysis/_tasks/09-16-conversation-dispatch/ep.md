# EP：AIR-99 會話主動派工模式（conversation-dispatch skill＋rule 觸發線）

> **ep_type**: implementation（docs mode——product 變更全為 `.md` instruction 檔）
> 卡：`backlog/tasks/air-99 - 會話主動派工模式——主-agent-討論座席、查證打雜自動外派-sub-agent（conversation-dispatch-skill＋rule-觸發線）.md`
> **baseline: 2bca820**（worker 接手當下 HEAD；卡 Plan 內 24cc3b2 為規劃期舊值，以工單為準）
> 已決策勿重辯：卡 Plan ①–⑦（不新增 Marshal／載體＝新 skill＋rule 觸發線＋引用既有機械／判準表明標 heuristic 非 normative／每查證問句判一次粒度／回報契約＝結論＋path:line 逐字錨點＋未驗項／spawn 型別分流＋禁再委派句／不動 workflow redesign EP 與 AIR-91/96 契約）。

## UC 盤點（docs mode：受影響 instruction/rules 清單）

| 檔 | 變更 | 說明 |
|---|---|---|
| `skills/conversation-dispatch/SKILL.md` | 新建 | 載體本體：trigger situations、判準表（正表＋負空間）、spawn prompt 模板、回收驗收、同意邊界 |
| `rules/context-management.md` | 升級既有句 | 「大範圍探索」句 → 行為錨＋pointer；不開新 rule 檔（A2） |
| `skills/agent-workflow/SKILL.md` | desc 補指向 | 邊界聲明：本 skill 管「怎麼安全 spawn」、conversation-dispatch 管「會話何時派」（最小改動，若需） |
| `skills/CLAUDE.md` | 索引補一行 | drift-prone 手動清單同步（新增 skill 必補） |
| `ai-analysis/_tasks/09-16-conversation-dispatch/` | 新檔 | EP、activation 測試結果（A5） |

邊界（不做）：不新增 Marshal/Role/engine/runtime；不改 catalog/schema/presets；不動 workflow redesign EP 與 AIR-91/96 契約；不建狀態庫；不做額度經濟學（reserve/shadow price，AIR-98 同軸後續線）；禁實跑 deploy（deploy＝user 授權，結案時統一做——本 EP 只 `--dry-run` 量測）。

## Scenario Matrix（docs 語境：觸發/預期行為＝LLM 行為可觀察面）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | AC |
|---|------|------|---------|------------|-----|
| SM-1 | 討論中出現廣度探索／多檔查證需求 | 會話問句命中廣度軸 | 外派唯讀 sub agent 背景跑、主 session 保持討論座席 | 回報帶 path:line 錨點 | A3/A5 |
| SM-2 | 討論中出現單點小查證 | ≤2 檔、當前步驟立即依賴 | 不外派，主 session 直查（負空間） | 無外派動作 | A3/A5 |
| SM-3 | 會話問句召回 | 載入會話帶派工意圖 vs 不帶 | 該派例召回 skill、不該派例不誤觸發 | activation 測試四態分類 | A5 |
| SM-4 | 查證需跨 external runtime | 候選腿＝muse/codex/glm bridge | 停下先問 user，禁自主派 | 同意邊界條文在場（rg） | A4 |
| SM-5 | 回收腿結論驗收 | sub agent 回報到達 | 主 session 以 rg/Read 驗證錨點命中；失效退回重取 | 錨點命中記錄 | A6 |

## 測試規劃段

**跳過**（純文檔 EP 無可執行碼面）。行為驗證由 P4 承接：activation 面（desc＋rule 觸發線）→ instruction-testing 四 surface gate 判 activation test（該派/不該派對稱）；A6 為端到端一例（真 spawn→背景回收→錨點驗收）。判分走機械觀察面 protocol（fresh context、四態分類、逐字 capture、禁挑綠重跑）。

---

## P1 新建 skills/conversation-dispatch/SKILL.md

### Context
會話討論中查證/盤點/機械驗證等打雜活自動外派 sub agent 背景跑，主 agent 保持討論座席。基礎設施九成在場（registry roles／model-routing／agent-workflow 背景 spawn），缺的是會話場景的派工判準與觸發。本段落實作 [會話主動派工判準與模板]。

### 修改要點（結構）
- frontmatter：`name`＋`description`（觸發條件句前置＋會話觸發詞：主動派工/討論座席/查證外派/背景研究；值 ≤950 chars、引號化）＋`when_to_use`（repo 慣例）
- **模組定位**：一句話職責＋邊界（session 級自主模式＝deep-work、spawn 機械＝agent-workflow、路由＝model-routing、demand 唯一源＝owning workflow rows〔AIR-91〕——均不在此重定義）
- **觸發情境**：與 user 對話討論期間產生查證需求（查資料/盤點/機械驗證/背景研究），不需 user 指派
- **判準表**：明標 heuristic 預設非 normative；**正表**（廣度探索→Explore／機械對帳→lite-verify／逐字規格→spec-miner／多源交叉→cross-verify-investigator）＋**負空間等重**（≤2 檔直查、<30s 前台 probe、當前步驟立即依賴、判讀裁決、寫入類不在會話派工範圍）
- **spawn prompt 模板句**：WorkUnitContext 四欄（objective/constraints/relevant_files/expected_output）——不倒整段對話；含回報契約（結論＋path:line 逐字錨點＋未驗項 unverified/not-found 分列）、禁再委派句、spawn 型別分流一行（lite 機械必 registry 角色、唯讀探察用 Explore——AIR-50 教訓）
- **回收驗收步驟**：背景回收（agent-workflow「Spawn 預設背景」）→ 主 session rg/Read 驗錨點命中 → 失效退回重取禁降級 → 回到討論座席帶「影響什麼/未決什麼」
- **額度同意邊界**：唯讀＋in-harness 自主派；bridge/external-runtime（muse/codex/glm）必先問 user；並發上限沿用 model-routing 並發表（引用不拷貝）
- spawn 機械/路由**零拷貝**：全引用 agent-workflow＋model-routing

### 驗證策略
- rg 驗 desc 觸發詞四詞在場（A1）
- rg 驗無實質重複（判準表外逐條引用）：agent-workflow/model-routing 零拷貝（A1）
- rg 驗 heuristic 非 normative 標記、負空間、同意邊界、spawn 型別分流、禁再委派句在場（A3/A4）

## P2 rules/context-management.md 觸發線升級＋部署量測

### Context
進場機制＝rule 常駐提供模式在場感（不需顯式 invoke）；既有「大範圍探索」句已在 Session 管理段，升級為行為錨＋pointer 即可，不開新 rule 檔（bundle 預算稀缺）。

### 修改要點
- 既有句尾追加會話查證外派行為錨：廣度探索/多檔查證先判外派；唯讀查證腿可自主派→載入 skill 判準表；pointer＝`skills/conversation-dispatch/SKILL.md`（plain path 形態，bundle 內相對 link 不可用）
- 部署面：`uv run python scripts/deploy_agents.py --dry-run` 量測 bundle size gate 並記錄數字（基線 30,231B／82.05%、WARN=31,334B；預期 +83B~110B）。**只 dry-run，實跑 deploy 禁止**（deploy＝user 授權，結案時統一做）

### 驗證策略
- rg 驗升級句關鍵詞（外派／conversation-dispatch pointer）在場；CJK 完整性抽查
- dry-run 輸出節錄進 verdict（bytes／percent／PASS）

## P3 desc 觸發詞＋交叉指向＋索引

### 修改要點
- conversation-dispatch desc 觸發詞（P1 已含）
- agent-workflow desc 補最小指向（若需）：對話場景 dispatch policy 指向 conversation-dispatch
- `skills/CLAUDE.md` 索引補一行（放「專案維運」群 agent-workflow 旁）

### 驗證策略
- `uv run python scripts/scan_skills_desc.py` 機械 gate（desc 值長度/形式）；rg 驗索引行在場

## P4 activation 行為測試＋A6 端到端

### Context
A5：instruction-testing 方法論，會話問句召回（該派≥2 例＋不該派≥2 例），fresh context、機械觀察面 protocol、逐字 capture 落 `.agent-tmp/air-99/`，結果整理落任務家；禁挑綠重跑。A6：實際 spawn 一枚 Explore（`run_in_background: true`）做真實查證（本工單唯一允許的再派發），prompt 注入：禁 /tmp、寫不進就回報、暫存集中 `.agent-tmp/`、用 rg/fd 禁 grep/find、禁再委派、回報契約（path:line 逐字錨點＋未驗項）；主 session rg/Read 驗錨點命中；錨點失效退回重取禁降級。

### 驗證策略
- A5：每例 fresh context 判分（recall＋premature-action 面），四態分類記錄（PASS/FAIL/UNEXPECTED/INCONCLUSIVE）
- A6：回收結論逐條錨點以 `rg -n` / Read 對帳，命中記錄進 verdict；失效重取

## 收尾步驟（docs mode）

- 受影響命令/rules 行為已反映（P2 觸發線＋P3 索引）
- `skills/CLAUDE.md` 索引同步（P3）
- activation 測試結果＋A6 錨點驗收記錄落任務家與 `.agent-tmp/air-99/verdict.md`
- 結案動作（卡狀態／deploy 實跑／commit）＝主 session 職責，本工單不執行
