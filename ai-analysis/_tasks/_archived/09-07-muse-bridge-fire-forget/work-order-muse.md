# Work Order — AIR-36 實作委派（muse bridge task）：fire-and-forget 收法慣例落地（S1+S2）

## 1. 紅線（首段，違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡狀態——止步於 working tree 編輯
- 禁把任何產物寫到 `/tmp` 或 repo 外路徑；中間筆記不留檔（交付報告承載於最終回覆，不寫檔）
- 修改 `.md` 檔一律「讀目標節全文 → 精確區塊替換」；**禁 `sed`／regex 批次替換改 .md**（會破壞 Markdown 縮排與相鄰段落）
- 範圍外檔案連「順手修」都禁止（見 §6）
- 紅線違反＝失敗，非風格問題

## 2. 目標（一句話）

把 muse bridge 長跑轉發的收法慣例從「caller session 掛背景 Bash 等 exit」升級為 fire-and-forget（`task --background` 提交→jobId 即回→session 釋放→事後 `wait`/`show` 跨 session 認領→多工複用），落實於 ai-rules 三份 instruction 檔（EP S1+S2 段）。

### Role contract

非 registry role 派發（ad-hoc implement 工單）——本子段留空。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree，非 worktree）
- 工作目錄：repo root（bridge 預設）
- base commit：`8e9915e`
- **並行改動聲明（dirty mode，重要）**：working tree 已有未 commit 改動，**不屬本次清理範圍、不得覆蓋或回滾**：
  - `skills/model-routing/SKILL.md` 的「dispatch 預設」節（約 :22-35）——含三行政策修訂（額度現值、實作預設 muse+flash、審查類放寬）。你動的是同檔的「完成回報收法」決策樹節（約 :150-160），**兩節不同區域**；你的 `git diff` 會同時看到這組 pre-existing hunks——報告中需區分「pre-existing hunks（dispatch 節）vs 本次 hunks（決策樹節）」
  - `ai-analysis/_tasks/09-07-muse-bridge-fire-forget/`（EP、本工單——任務家產物）
  - `.agent-tmp/`（暫存）

## 4. 必讀（按序，絕對路徑）

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-07-muse-bridge-fire-forget/ep.md`——全文（總覽研究事實＋S1/S2 是你的實作規格＋S3 僅供理解不執行）
2. `/Users/ctai/Github/ai-rules/skills/model-routing/SKILL.md`——「完成回報收法」決策樹節（搜尋 `**決策樹**`，約 :150-160；這是你 S1 的改寫對象）＋「dispatch 預設」節（約 :22-35，只讀理解、不動）
3. `/Users/ctai/Github/ai-rules/agents/AGENTS.md`——:29（派發與收法單一源 pointer）、:41（dispatch matrix「EP review（雙家族）」行——S2 改寫對象）、:83（muse code 行，只讀）
4. `/Users/ctai/Github/ai-rules/skills/_common/work-order.md`——:114 消費形態句（S2 改寫對象）
5. 事實源（best-effort——workspace 外路徑，讀不到就跳過，EP 總覽已內嵌所需事實摘要，不因此停工）：`/Users/ctai/.zcode/cli/plugins/cache/muse-market/muse/0.2.5/hooks/hooks.json` 與同目錄 `scripts/session-lifecycle-hook.mjs`（SessionEnd 殺 running jobs 的兩端差異事實）
6. `/Users/ctai/Github/ai-rules/skills/CLAUDE.md`——:132 附近 model-routing 行（收法描述「push 化決策樹：背景 Bash exit 喚醒」——S2 改寫對象）
7. `/Users/ctai/Github/ai-rules/rules/model-routing.md`——:34 附近骨架句（「push 化決策樹」括號——S2 中性化對象）

## 5. 已決策（勿重辯）＋矛盾例外

- `--background`／`wait`／`show`／`runs`／`export` 機制 bridge 0.2.5 已存在（EP 總覽有源碼行號）——本工單是**文檔慣例變更**，不是開發 bridge 功能，勿重造
- 兩端 SessionEnd hook 差異是**既存事實**（ZCode 端 config 不執行 plugin hooks→job 可跨 session 存活；CC 端執行→holder session 必須活著）——文檔記載差異，不是要修 hook
- 決策樹第 1 層（簡單轉發背景 Bash 阻塞直呼）**保留不動**；codex 側語義（`status --wait` 差異）**保留不動**
- **124 到期語義與家系拆分（muse exit 124＋status running＝重掛；codex exit 0＋`waitTimedOut`）原樣保留於新決策樹層**——晚收需要的語義，不是殘留，勿刪
- **bridge `review` 子命令無 `--background`（也無 `--prompt-file`）**——fire-and-forget 只適用 `task` 形態；涉及 review 路徑的文檔語義要區分兩形態，勿為 review 捏造 `--background` 命令
- judge 裁決層固定主 session 的既有拍板不變
- 詞形：用「fire-and-forget」（英文原詞）＋「跨 session 認領」「多工複用」——與 EP 一致，勿另造同義詞
- **矛盾例外**：若發現檔案實際內容與 EP 宣稱的行號/語義衝突（同段已有矛盾的既定義），**停下來在報告中舉證**（file:line＋逐字引用），不要自行改設計或為服從工單靜默做錯

## 6. 範圍限定

- **動（僅此五檔、僅指名節段）**：
  - `skills/model-routing/SKILL.md`——僅「完成回報收法」決策樹節（§7 工具接線到診斷手段行之間）
  - `agents/AGENTS.md`——僅 :41 dispatch matrix 該行的 muse 側形態短語（「背景 Bash 直呼 bridge（不佔 agent 並發）」→ fire-and-forget 語義、區分 task/review 兩路徑）
  - `skills/_common/work-order.md`——僅 :114 消費形態句（補 jobId 回報指引一句）
  - `skills/CLAUDE.md`——僅 :132 附近 model-routing 行的收法描述括號（同步 fire-and-forget 新形態）
  - `rules/model-routing.md`——僅 :34 附近骨架句括號詞彙（「push 化決策樹」→「收法決策樹」）
- **不動**：其他一切——尤其 `rules/` 其餘全部（rules/model-routing.md 僅 :34 一詞）、`agents/zcode/*.md`／`agents/claude/*.md`（生成檔，手改會被 sync 覆蓋）、`backlog/`、`skills/model-routing/SKILL.md` 的 dispatch 預設節、memory 池（repo 外，本次由主 session 處理）
- 違反範圍＝失敗；交付報告附 `git diff --name-only` 舉證僅三檔（pre-existing 的 dispatch 節 hunks 除外，見 §3）

## 7. 工具接線

- 讀查：`cat`／`rg`／`ls`（字串搜尋一律 `rg`，禁 `grep -r`）
- 修改：讀目標節全文 → 精確區塊替換（禁 sed／regex 批次）
- 三禁令：
  - 禁 code-reality 寫入面（`build`／`snapshot`／`delta_tour`／`project`）；查詢面可用可不用
  - 禁把任何工具輸出寫到 repo 外（含 `/tmp`）
  - 禁自行妥協路徑（遇缺口停下舉證，不繞路）

## 8. 驗收（命令＋預期結果，逐條實跑）

1. `rg -n "fire-and-forget" skills/model-routing/SKILL.md` → ≥2 命中（決策樹長跑層＋警示/複用段）
2. `rg -n "task --background" skills/model-routing/SKILL.md` → 決策樹節內命中（完整提交命令形態在場）
3. `rg -n "SessionEnd" skills/model-routing/SKILL.md` → 命中且同行/鄰近含「ZCode」與「CC」兩端差異語義
4. `rg -n "冪等" skills/model-routing/SKILL.md` → 命中（Muse 諮詢陷阱收編：有界 wait 迴圈／stop 前先 show\/export／任務冪等至少收編兩項）
5. `rg -n "背景 Bash 直呼|背景 Bash exit 喚醒" agents/AGENTS.md skills/CLAUDE.md` → :41 與 :132 已改後，殘留命中為 0 或僅剩語義正確的歷史敘事（逐一列出判讀）
6. `rg -n "jobId" skills/_common/work-order.md` → :114 消費形態句附近新增命中（長跑工單派發後回報 jobId）
7. `rg -n "push 化" rules/model-routing.md skills/CLAUDE.md` → 歸零（或僅歷史敘事、逐一判讀）；`rg -n "收法決策樹" rules/model-routing.md` → :34 命中
8. 決策樹單讀可執行自檢：以「未載入任何背景的 session」視角逐層走一遍新決策樹（何時 --background、何時阻塞直呼、收法命令、兩端判定）——報告自評＋引用新文本關鍵行
9. `git diff --name-only` → 僅五檔（`skills/model-routing/SKILL.md`、`agents/AGENTS.md`、`skills/_common/work-order.md`、`skills/CLAUDE.md`、`rules/model-routing.md`）
10. `git diff skills/model-routing/SKILL.md` → 報告中貼回並標注哪些 hunk 屬本次（決策樹節）、哪些屬 pre-existing（dispatch 預設節，§3 聲明的並行改動）

## 9. 證據紀律＋PII 禁令

- **宣稱落地 ≠ 落地**：每個「已改」宣稱附 rg 命中或該行 Read 內容為證（不接受「應該改好了」式自述）
- 每條驗收附完整命令與原始輸出（截斷標明）；宣稱「沒改 X」須附 `git diff --name-only` 佐證
- 報告中禁出現任何 email／人名等 PII
- 失敗如實記錄，不掩蓋

## 10. 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單（對應 `git diff --name-only`，含 pre-existing 區分）
2. 逐段落落實說明：EP S1 五個修改要點／S2 五點各落在哪（file:line 級對照）
3. 驗收 1-10 命令與原始輸出
4. 偏差記錄：與 EP 規格有任何出入處＋原因
5. 未驗證項／被阻擋項
6. 建議 reviewer 聚焦點（最有信心不足之處）

無對應項標「無」勿留空。
