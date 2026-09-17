---
name: commit

description: "Commit 入口：lint 閘門 → 分析變更 → 生成 message → 確認後提交"
when_to_use: "Commit current changes after lint check, message generation, and user confirmation. Supports push, rebase, and PR creation after commit."
argument-hint: "可選 --push 自動推送，--rebase <branch> rebase 後推送"
allowed-tools: ["Bash", "Read"]
---

# /commit — Commit 入口

Git Commit 工作流入口，從 lint 閘門到提交完成。

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則
- [agent-workflow](../agent-workflow/SKILL.md) — 「全生命週期 execution contract（消費側）」：commit 拆兩半——preparation（finalization 對帳、訊息草擬）可派 agent，**consent gate 永遠主 session 互動**（表主體在 agents/AGENTS.md）

---

## 執行流程

### 階段 1：Lint 閘門

**Ruff + MyPy 雙軌閘門**（兩者都必須通過才 commit）：

```bash
# Track A: Ruff（格式 + lint）
uv run ruff check --fix .    # Step 1: 自動修可修的
uv run ruff format .         # Step 2: 格式化
uv run ruff check .          # Step 3: 最終驗證（必須 0 errors）

# Track B: MyPy（型別檢查）
uv run mypy .                # 必須 0 errors
```

**mixed-tree 歸因分支**：全 repo 閘門 FAIL 時先歸因——FAIL 檔案**全非本次範圍**（並行 session 的未 commit 改動混入 working tree）→ 改 path-scoped 閘門（`uv run ruff check <本次檔案>`／`uv run mypy <本次檔案>`）＋報告註明並行線遺留；FAIL 在本次範圍內（含 pre-existing）→ 依下方手動修正流程處理。

**執行順序**：Step 1 → Step 2 → **並行** Step 3 + MyPy（ruff format 後同時跑 `ruff check` 和 mypy，省時間）。

> ⚠️ **MyPy/Pytest 閘門禁止 pipe 到 tail/grep**（exit code 會被遮蔽，見 [bash-hard-rules](../../rules/bash-hard-rules.md)）：`uv run mypy . | tail` 回報的是 `tail` 的 exit 0 而非 mypy 的非 0 → 誤判通過。看 output 重導檔案再 Read，別 `| tail`。

Ruff 或 MyPy 有錯誤 → **嘗試手動修正**（不直接放棄）：

| 錯誤類型 | 自動處理策略 |
|---------|------------|
| PLC0415（局部 import） | 移至 top-level import。**禁止假設 circular import** — AI 常偷懶放在函數內，99% 不是 circular。真正循環的解法是重構目錄結構，不是局部 import |
| F841（未使用變數） | 移除或加 `_` 前綴 |
| E402（sys.path 後的 import） | 加 per-file-ignores 到 pyproject.toml |
| MyPy 第三方套件型別缺口 | 依 [python-type-gap](../fix-test/python-type-gap.md) 四層策略處理 |
| 其他可修問題 | 依 fix-test 的 lint/type 修復指引（`skills/fix-test/lint-type-recipes.md`）修正 |

手動修正後仍無法通過 → 提示 `/fix-test`（lint/type 節），中止。

> **全量測試驗證不在 commit**（在 `/implement` 階段 3，見 [build.md](../implement/SKILL.md)）：commit 只守 lint + mypy。若本次變更**未經 `/implement`**（如直接修完就 commit），commit 前先跑專案全量測試（如 `make test`）確保無 regression。

### 階段 2：Git 狀態分析

`git status --porcelain` + `git diff` + `git diff --cached` + `git log --oneline -10`

深度理解：檔案層級（模組、功能區域）+ 程式碼層級（業務邏輯）+ 變更類型（feat/fix/refactor/perf/test/docs/style/chore）

**並行 session 防護（四條）**：

- **staged 範圍核對**：commit 前 `git diff --cached --name-only` 必須 == 本次清單——staging area 是**單一共享狀態**，並行 session 的 staged 檔會混入（隔離式 add 對 active race 無效）；多餘 staged → `git restore --staged <他檔>` 後再 commit（補救四步：reset → add 正確集合 → commit → `git show --stat` 驗）。此核對只防「多」——finalization「少」由 [2.8 對帳閘門](#階段-28-finalization-對帳閘門)守
- **git mv 順序陷阱**：`git mv` 搬的是 **HEAD 內容**——先 Edit 後 mv 會把未 commit 改動留在原地（舊路徑冒出殘檔）。順序＝先 mv 再 Edit 新路徑；commit 後 `git show --stat` 驗搬家完整
- **同根因同 commit**：同一邏輯改動的多檔一個 commit（寧晚不拆散——拆散的中繼 commit 語義不完整）
- **外來產物對帳**：commit 非本 session 產生的檔案前，對可機械驗證宣稱（路徑存在／入口有效／狀態宣稱）跑 rg/ls 對帳——他 session 的自述不可信

### 階段 2.5：引用同步掃描

**當變更包含 `rules/`、`skills/` 下的 .md 檔案時執行，否則跳過。**

目的：修改 A 後，掃描是否有 B/C/D 引用了 A 但沒同步更新。

掃描範圍（按變更檔案類型）：

| 變更檔案 | 掃描目標 | 搜尋方式 |
|---------|---------|---------|
| `skills/*/SKILL.md` | `skills/CLAUDE.md` 索引 + 引用此 skill 的其他 .md | `rg "skill名" rules/ skills/` |
| `skills/_common/*.md` | 引用該子範本的 skills | `rg "檔名" skills/` |
| `rules/*.md` | 引用此 rule 的 skills | `rg "rule名或檔名" skills/` |
| `ai-development-guide.md` | 所有引用 guide 定義的 skills（如 UC 狀態 emoji） | `rg "具體定義文字" skills/` |

輸出：列出需檢查的檔案（不是要求全部更新，是提醒檢查是否需要更新）。用戶在階段 5 確認時一併判斷。

### 階段 2.6：Review Findings 提醒（optional）

**人主導工作流**（finding 在 review session 對話、`/copy` 搬到實作 LLM）：無 `.review/`，此階段跳過 —— finding 處置由用戶在階段 5 確認時對照 diff 判讀（B 軸 viewport，不靠 status 機械追蹤）。

**跨命令自動化工作流**（`/judge-review` / `/followup-review` 產生 `.review/`）：若 `.review/` 存在，列出殘留 `open` finding 提醒（不阻擋）。`status` 靠 LLM 更新會漏，僅作提醒非閘門。

> 無論哪種工作流，finding 處置的最終把關在階段 5（人確認 commit）—— 機制只列出不保證。

### 階段 2.7：POC/Demo 處置閘門

**commit 前檢查閘門**（與 2.5/2.6 同系列）。機械結算每個 POC/Demo 的去處，不靠 build LLM 自覺回頭看 —— 同 build「整合路徑覆蓋 rg 0 hits 就擋」的機械閘門模式，用「POC 不得無痕消失」倒逼測試覆蓋（預設改寫成 test，delete 須附證據）。

**時序**：掃描+歸類在 commit 流程內執行；處置清單隨階段 5 用戶確認一併確認；確認後在階段 6 commit 執行前，先跑已確認的處置（刪 poc/ 檔、歸併 demo）。

掃描 `poc/**/*.py` + `demo_*.py`（rg glob，機械事實不可靜默跳過）：

| 情境 | 處理 |
|------|------|
| 空（無命中） | 通過 |
| 非空 | 逐個處置（見下） |

**逐個處置**（跨段落豁免）：先讀 POC 檔頭「EP 段落」標注，判斷生命週期：

- 所屬段落尚未 build（活躍 POC）→ 標「待該段落 build 時處置」，暫不擋
- 所屬段落已 build+commit，或檔頭缺失 → 強制顯式歸類檔案去處

**強制歸類（檔案去處三選一）**：

| 產物 | 預設檔案去處 | 偏離預設 |
|------|------------|---------|
| `poc/**/*.py` | 改寫成 test（給測試路徑，須存在）| 選 delete 須附分類證據 |
| `demo_*.py` | 進 scripts/（給 demo 入口路徑）| 選 delete 須附分類證據 |

- 承接物（test/scripts 路徑）不存在 → 當場補，否則擋 commit

**delete 須附分類證據**（非憑空理由，三選一）：

- 「已被既有 test 覆蓋」→ 附 `test_path:line` + 該 assert 驗證的行為一句話（階段 5 可機械核對 assert 真覆蓋 POC 行為，非僅驗檔案存在）
- 「假設被推翻（行為不進生產）」→ 附 EP finding（ep-validate ❌ 結果記錄）
- 「純探索性（無對應 UC）」→ 說明探索目的 + 為何無對應 UC

提不出證據 → 不得 delete，須改寫成 test（倒逼覆蓋）。用戶階段 5 見處置清單（含證據），可核對 AI 是否全選 delete 編理由。

**刪除後 dangling-ref 全域掃描**（delete 路徑適用）：刪 POC/demo 檔後，機械掃指向已刪檔名的 ref —— `rg <已刪檔名>` 跨 `lab/`+`demo_*.py`+`tests/`+`ai-analysis/`（EP、docstring「實證 lab/poc_*.py」多處引用），逐個清或重指承接 test。範圍必須含 code + EP + docs，不只 `tests/` —— 不靠 AI 記得「還要查 lab/demo」。

> **demo 雙重**：「檔案去處三選一」是互斥分類（檔案層）。demo 驗證的「行為」是獨立層面 —— 若值得測，build 時另提煉 `test_<feature>.py`（不在 2.7 範圍）。2.7 掃 `demo_*.py` 只管檔案去處（預設 scripts / delete）。

### 階段 2.8：Finalization 對帳閘門

**commit 前檢查閘門**（與 2.7 同系列，**捷徑模式保留**）。機械掃 `git status --porcelain` 對 finalization 路徑面（路徑集**與階段 6 納入清單同源**）——階段 6 的 finalization 清單是散文列舉，漏 add 時安靜失敗（真實案例：MOS-28 結案卡＋EP 歸檔搬移懸掛 working tree，卡 refs 指向 git 未落地路徑）。

| 判定 | 處置 |
|------|------|
| 本任務 build 5a Built 結算物＋收斂後結案物（卡結案／EP 歸檔／flow-feedback 歸檔／instruction 檔／`.tours/delta/`） | 納入本次 add |
| 並行 session **活躍中**（非本任務範圍） | 顯式排除＋報告記錄 |
| 並行弧**已終結**但結算未 commit（孤兒結算：卡 Done／結算物在場、owning session 已結束） | **收編進本 commit 或另開補 commit**，不排除（實證：AIR-17 結算懸掛半日、前 commit 假結算） |

**半套歸檔偵測**（隱形漏失主形態）：` D` 舊路徑與 `??` 新路徑（`done/` 等）成對＝歸檔搬移只搬未 add——搬移必須雙側同 commit，否則卡 refs 指向 git 不存在的路徑（ai-guide `_tasks/` 弧 AIR-77 起永不搬，此處成對即異常；本條留給線任務／外部分類搬移）。

**memory 池對帳腿**（git 掃不到的出口保證——memory 池在 repo 外）：`rg` 本專案 memory 池（掃描面＝`_inventory.md` 全量 desc 投影＋常駐 MEMORY.md＋條目檔——B 形態下 MEMORY.md 只含常駐定額、全量條目只在 `_inventory.md`，漏掃即漏對帳；池形態例 repo `.agents/memory/` 主體或 `~/.zcode/cli/memories/projects/<id>/memory/`〔多為 symlink 指主體〕；載體細節見 [memory-audit](../memory-audit/SKILL.md)「適用載體」）。掃描鍵聯集＝本次弧建卡 id ∪ staged diff／branch 名內卡 id（2.8 時點 commit message 尚未生成、非掃描源）∪ 本 EP「UC 盤點」登記的「結案蒸餾範圍」條目路徑 ∪ 弧主題詞；池不存在 → 報告標「無 memory 池，跳過」。**結案態前置**（三分歸屬前）：`backlog task view <id> --plain` 取卡狀態（無 backlog CLI → 保守視為未結案）——卡未 Done／結案兩步未執行 → 命中條目標「活躍弧 in-flight——不動」（進行中弧線收案前禁加段、等一次性蒸餾）。命中三分歸屬（LLM/user 判）：**活知識錨**（教訓索引式引用）→ 保留；**弧流水**（狀態快照、進度、git 可推導內容、過期詞）→ 結案蒸餾當場做；**已是終態 facts** → 過。歸屬他弧且 owner 線未結案 → 保守不動、列清單標註。報告附命中清單＋歸屬判定（零命中亦標）。蒸餾方法論單一源＝[kanban-board](../kanban-board/SKILL.md)「弧結案蒸餾（第三動）」＋[memory-audit](../memory-audit/SKILL.md)「寫入端紀律」，此處不重述。

報告附 `git -c core.quotePath=false status --porcelain` 原始輸出（機械事實不可靜默跳過；quotePath 關閉與 guard 同口徑——非 ASCII 路徑不轉義）。歸屬判斷是語義的（本任務 vs 並行遺留），故為 skill 步驟而非 hook——機械掃描列命中、LLM/user 判歸屬（同 2.7「機械掃描＋逐項處置」模式）。

### 階段 2.9：控制面回執彙集（AIR-106）

staged 觸及控制面路徑（判定照 [instruction-writing](../instruction-writing/SKILL.md)「落地前審查閘」節；機械路徑清單單一源＝`.githooks/control-plane-guard.sh` 的 grep pattern——無 guard 檔的 repo 以 instruction-writing 同節的家族描述為判定）時執行，否則跳過。**閘存活探針先跑**：`git config core.hooksPath` 非 `.githooks`＝本 clone 隔離閘未上線（fail-open）——提案須揭露此事。從本弧卡 notes／EP 抓回執四欄 `classification／review／session-freshness／deployment-surfaces`（值域定義源＝instruction-writing「落地前審查閘」第 5 點；deployment 欄可由 post-build 部署面對帳 verdict 供應）——四欄附**階段 5 提案**與 commit message body（`Receipt:` 一行）。四欄不齊 → 提案如實標「回執未齊（缺何欄）」，不偽裝完備；user 確認時可退回補審——缺審查腿的 commit 先於審查回收＝activation-before-review 洞（F8）。非控制面 commit 此階段空跳——判定**恆以 guard pattern 為準**（backlog 卡檔、scripts 一般工具、ai-analysis 內非 AGENTS/CLAUDE 檔等不命中者空跳；`ai-analysis/blueprint/AGENTS.md` 這類深層 AGENTS.md 命中家族規則＝控制面，不空跳）。

### 階段 4：生成 Commit Message

**格式**：`<type>(<scope>): <description>`

**語言規範**：

| 部分 | 語言 | 範例 |
|------|------|------|
| type | 英文 | `feat`, `fix`, `refactor` |
| scope | 英文 | `data`, `commands`, `ui` |
| description | **繁體中文**（術語保留英文） | `新增 DataGateway 統一數據介面` |
| body | 繁體中文 + 英文術語 | 說明為什麼這樣改 |

### 階段 5：用戶確認

展示變更摘要 + 建議 commit message + Capabilities/Kanban 狀態提醒（如適用）→ **等待用戶明確確認**。

**留審時必附檢視指令**：user 要求「先不要 commit 我看一下」→ 變更留 working tree，報告附逐檔檢視指令（`git diff <path>`）與行號定位——user 要能一鍵看到改了什麼，不自行猜路徑。

**遵守 `outward-action-consent` rule（commit 場景）**：未收到確認絕不執行 git commit（例外形態見該 rule「Commit 專屬段」，此處不枚舉——rule 增刪即漂）。

### 階段 6：執行 Commit

**「commit 確認」結算（pre-commit、無 hash）**：若本任務在拍板池（ai-guide 形態＝backlog 卡 notes 的 PENDING 段——outward-action-consent「報 PENDING」的落點；mosaic 形態＝`ai-analysis/_inbox/pending-decisions.md`）有「commit 確認」PENDING 條目——user 於階段 5 確認後、git add 前：條目搬已結案段（一行：日期＋user 確認，**不含 hash**——hash 屬 git log 可推導）；結算敘事寫卡/EP final summary（同樣 commit 前、不含 hash）；殘餘驗收項（如 L6 驗收）拆獨立未勾條目留 queue。全部 commit 前完成 → 隨本 commit 落地。**禁止 post-commit 回寫拍板池**——記錄 commit 的文字進不了它記錄的那個 commit（雞生蛋懸掛）。

確認後 `git add`（**納入本次開發的完整產物**：主變更 + build 5a Built 結算＋收斂後結案的 finalization 檔 —— instruction 檔（AGENTS.md 為主，legacy CLAUDE.md）/ `backlog/`（卡＋drafts——CLI `autoCommit=false` 下只改檔，整目錄隨 finalization add）/ 任務家（EP＋spec＋Report Shell，含歸檔搬移——`ai-analysis/{_tasks,_projects}` 或 `00-tasks/`）/ `.tours/delta/`（持久 delta tour——post-build hook 2 產）/ flow-feedback 歸檔）+ `git commit`（含 attribution footer：`Co-Authored-By: <當前 harness 名>`——ZCode session 寫 `Co-Authored-By: ZCode`）。

**commit 成功後清除 ephemeral 工作產物**：review 筆記為工作過程產物，commit 結算後清除（同 POC 生命週期哲學，不進 git 歷史）。**per-branch 清除**（`.review/` 可能含多 branch — 如 main / replay / backbone）：只刪當前 branch 的 `.review/<branch>.md`，**勿 `rm -f .review/*.md`**（會誤刪他 branch review）。先 `ls .review/` 確認內容；`.review/` 為 gitignore ephemeral 產物（無 git 復原途徑），per-branch 清除正是為避免誤刪他 branch。保留 `.review/` 目錄供下次 review 直接寫入。

### 階段 7：選配分支操作

- `--push`：`git push`
- `--rebase <branch>`：fetch + rebase + push
- 建立 PR：`gh pr create`

---

## 執行約束

- **遵守 `outward-action-consent` rule（commit 場景）**：未經確認絕不 commit（例外形態見該 rule「Commit 專屬段」，此處不枚舉——rule 增刪即漂）
- **ruff + mypy 必須雙通過才 commit**（pre-existing 問題也需在此時處理：加 per-file-ignores / type: ignore 或直接修）
- **docs 單檔閘門**（任何路徑 `.md`，含 `backlog/` 卡；捷徑／直 commit 路徑皆適用）：本次弧未跑 post-build/consistency → commit 執行前對變更的 `.md` 檔跑 `/consistency`（單檔輕量）——ruff/mypy 對 `.md` 不適用，此為純 docs 直 commit 的唯一品質閘門（實證：孤兒結算收編直 commit 跳過收尾鏈，補跑才發現無閘門）
- **TEMP diagnostic log 掃描**（防殘留）：commit 前掃描 diff 有無 debug-only log 模式（`Diagnostic:`、`[OK] ...`、症狀導向 debug 變數如 `<debug_var> =` 等 ad-hoc 偵錯輸出）。命中 → flag 給用戶確認移除。未移除的 debug log 不得進 commit（違反 llm-output-convention：print 只用於 state transition）。
- **description 必須繁體中文**（技術術語保留英文）
- **基於實際 diff 分析**，不憑猜測
- **遵循 git log 風格**

禁止：未確認就 commit / 全英文 description / 跳過 ruff 或 mypy / 無意義 message

---

## 流程位置

commit 位於主鏈末端（主鏈定義＝ai-development-guide「Session 開場導引」；review flow 詳圖**以 code-review skill「流程位置」為單一源**——本命令不重畫）。

前置：`/fix-test` lint/type 節（lint 不通過時）、`/code-review`

**捷徑模式**：當 `/code-review` 已產生 commit message 時，跳過階段 2（Git 狀態分析，含 2.5 引用同步掃描），直接進入階段 1（Lint）→ **階段 2.7（POC/Demo 處置閘門）** → **階段 2.8（Finalization 對帳閘門）** → **階段 2.9（控制面回執彙集）** → 階段 5（確認）→ 階段 6（提交）。2.7/2.8/2.9 屬 commit 前檢查閘門（非被跳過的階段 2），捷徑保留；2.6 為 optional 提醒，捷徑不強制。
