# Work Order — AIR-37 實作委派（muse bridge task）：memory 卡資訊生命週期閘門（S1＋S2）

## 1. 紅線（首段，違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡狀態——止步於 working tree 編輯
- 禁把任何產物寫到 `/tmp` 或 repo 外路徑（含 memory 池——repo 外，本次不碰）；中間筆記不留檔
- 修改 `.md` 檔一律「讀目標節全文 → 精確區塊替換」；**禁 `sed`／regex 批次替換改 .md**
- 範圍外檔案連「順手修」都禁止（見 §6）

## 2. 目標（一句話）

把 memory 卡流水的結案清理從流程自覺升為機械保證：commit skill 2.8 加 memory 池對帳腿（掃描鍵聯集→結案態前置→三分歸屬）、execution-plan UC 盤點加同主題 memory 登記腿（EP S1+S2 段）。

### Role contract

非 registry role 派發（ad-hoc implement 工單）——本子段留空。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree）
- base commit：`7ef65c6`（AIR-37 EP baseline 為 3a264e6，其後有兩顆 commit——以 working tree 現況為準）
- 並行改動聲明（dirty mode）：working tree 已有未 commit 改動不屬本次範圍——`skills/model-routing/SKILL.md`（決策樹收法分流修正一行，pre-existing）＋兩個 untracked 任務家目錄（`ai-analysis/_tasks/09-07-memory-card-lifecycle-gate/`、`09-07-routing-feedback-tier/`）。你動 `skills/CLAUDE.md` 時注意該檔已有本弧外的 :132 model-routing 行改動（committed）——只需加 :56 枚舉補詞。

## 4. 必讀（按序，絕對路徑）

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-07-memory-card-lifecycle-gate/ep.md`——全文（S1/S2 是你的實作規格；S3 主 session 自做不執行；EP Review Record 含已吸收的審查修正——條文以修正後 EP 為準）
2. `/Users/ctai/Github/ai-rules/skills/commit/SKILL.md`——階段 2.8 段（搜尋 `2.8`，S1 改寫對象：三列表＋半套歸檔偵測後加小節）
3. `/Users/ctai/Github/ai-rules/skills/execution-plan/SKILL.md`——UC 盤點節（搜尋 `UC 盤點`，S2 對象：步驟 3 附近＋輸出格式模板）
4. `/Users/ctai/Github/ai-rules/skills/CLAUDE.md`——:56 附近 commit 行（2.8 枚舉補詞）

## 5. 已決策（勿重辯）＋矛盾例外

- 蒸餾方法論單一源在 kanban（弧結案蒸餾第三動）／memory-audit（寫入端紀律）——2.8 新段**只引用不重抄**（禁把「刪日期流水/蒸後形」等方法論細節抄進 commit skill）
- 掃描鍵＝「建卡 id ∪ staged diff／branch 名內卡 id（**commit message 尚未生成，非掃描源**）∪ EP 登記清單 ∪ 弧主題詞」——EP Review F-A 定案
- S2 登記腿是**步驟 3 外的獨立子步**（不受「repo 有 backlog/ 時」分支限制——memory 池與 backlog 制正交；無池標跳過）——Review F-B 定案
- 結案態前置需讀卡狀態（`backlog task view <id> --plain`；無 CLI 保守視為未結案）——Review F-C 定案
- 輸出格式模板要加「同主題 memory 條目（結案蒸餾範圍）」行槽位——Review F-D 定案
- 詞形：「三分歸屬」（活知識錨保留／弧流水蒸餾／終態 facts 過）、「結案蒸餾範圍」——與 EP 一致勿另造
- **矛盾例外**：發現檔案實際內容與 EP 行號/語義衝突 → 停下舉證（file:line＋逐字引用），不自行改設計

## 6. 範圍限定

- **動（僅此三檔、僅指名節段）**：
  - `skills/commit/SKILL.md`——僅階段 2.8 段（半套歸檔偵測之後加「memory 池對帳腿」小節：掃描鍵聯集＋池路徑形態例＋結案態前置＋三分歸屬＋命中清單入報告＋他弧保守不動＋無池跳過；一段~十行內，方法論指向 kanban/memory-audit 不重抄）
  - `skills/execution-plan/SKILL.md`——僅 UC 盤點節（步驟 3 後加獨立子步「同主題 memory 條目盤點」＋輸出格式模板加行槽位）
  - `skills/CLAUDE.md`——僅 :56 附近 commit 行的 2.8 枚舉（補「memory 池對帳腿」一詞）
- **不動**：其他一切——尤其 `skills/model-routing/SKILL.md`（pre-existing 修正）、兩個任務家目錄、`rules/`、`backlog/`、memory 池（repo 外）
- 違反範圍＝失敗；交付報告附 `git diff --name-only` 舉證

## 7. 工具接線

- 讀查：`cat`／`rg`／`ls`（字串搜尋一律 rg）
- 修改：讀目標節全文 → 精確區塊替換（禁 sed／regex 批次）
- 三禁令：禁 code-reality 寫入面；禁輸出寫 repo 外；禁自行妥協路徑（遇缺口停下舉證）

## 8. 驗收（命令＋預期結果，逐條實跑）

1. `rg -n "memory 池對帳" skills/commit/SKILL.md` → 命中（新小節在場）
2. `rg -n "三分歸屬" skills/commit/SKILL.md` → 命中
3. `rg -n "staged diff" skills/commit/SKILL.md` → 命中（掃描鍵含 staged diff 形態；`rg -n "commit message 內 id" skills/commit/SKILL.md` → 零命中）
4. `rg -n "結案蒸餾範圍" skills/execution-plan/SKILL.md` → ≥2 命中（獨立子步＋模板槽位）
5. `rg -n "同主題 memory" skills/execution-plan/SKILL.md` → 命中且**不在「repo 有 \`backlog/\` 時」分支行內**（獨立子步形態）
6. `rg -n "memory 池對帳" skills/CLAUDE.md` → :56 附近命中
7. 單一源不重抄自檢：`rg -n "刪日期|蒸後形|寫入即蒸" skills/commit/SKILL.md` → 零命中（方法論細節未抄入；「蒸餾」一詞作 pointer 指向 OK）
8. `git diff --name-only` → 僅三檔
9. 決策樹式單讀自檢：以未載入背景的 session 視角讀 2.8 新小節——能執行（知道掃什麼鍵、怎麼判結案態、三分怎麼分、流水找誰的方法論）——報告自評＋引用新文本關鍵行

## 9. 證據紀律＋PII 禁令

- **宣稱落地 ≠ 落地**：每個「已改」宣稱附 rg 命中或該行內容為證
- 每條驗收附完整命令與原始輸出；宣稱「沒改 X」附 `git diff --name-only` 佐證
- 禁 PII；失敗如實記錄

## 10. 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單（對應 git diff）
2. 逐段落落實說明：EP S1 三塊／S2 兩點各落在哪（file:line 對照）
3. 驗收 1-9 命令與原始輸出
4. 偏差記錄（與 EP 規格出入＋原因）
5. 未驗證項／被阻擋項
6. 建議 reviewer 聚焦點

無對應項標「無」勿留空。
