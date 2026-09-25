---
name: rebase

description: "Trunk-based worktree rebase：trunk 永不被 rebase，其餘方向（feature onto trunk / feature 互 rebase）由呼叫者決定；all 批次同步/吸收所有 feature；all ff＝收斂鏈全員同 tip"
when_to_use: "Rebase a feature branch onto another (trunk or another feature); trunk is never rebased. `/rebase all` batch-syncs all features onto trunk (from a feature wt) or batch-absorbs all ff-able features into trunk (from trunk) — for multi-worktree sync, 同步所有 feature, sync all worktrees. Normal single-branch mode reports laggards and prompts manual sync (never auto-rebase); batch is explicit opt-in via `all`."
argument-hint: "<branch|all>（branch 慣例 main） [ff] [--autostash|--stash]"
allowed-tools:
  - Bash
  - Read
  - Edit
---

# /rebase — Trunk-Based Worktree Rebase

Feature branch rebase。多 worktree 共用同一 `.git`，rebase 即時本地、不需 push。本命令保護 **trunk 永不被 rebase**（見鐵律），其餘方向（feature onto trunk、feature 之間互 rebase）由呼叫者決定。`<branch>` arg 的角色隨當前 branch 翻轉（在 trunk 上 = feature 要被吸收，在 feature 上 = 任意 branch 當 rebase base；見 Phase 0）。

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則

---

## Trunk 模型鐵律（執行前必讀）

1. **指定一條 trunk**（慣例 `main`）。Trunk 是唯一整合線。
2. **Trunk 只往前**：疊新 commit，或 fast-forward 到一條已 rebase 過 trunk 的 feature。Trunk **永遠不是 `git rebase` 的主詞**。
3. **讓 trunk 吸收 feature** 的正確兩步（**不是 `git rebase`**）：
   - feature 先 `rebase <trunk>`（feature 變成 trunk 的後代）
   - 在 trunk worktree：`git merge --ff-only <feature>`（fast-forward 吸收）
4. **為何 `merge --ff-only` 而非 `rebase`**：若 trunk 不是 feature 的祖先（你漏了上一步、或 trunk 自己有 feature 沒有的新 commit），`merge --ff-only` **大聲拒絕**；`git rebase` 同情況會**靜默改寫 trunk** —— trunk 已 push 時就是 force-push 災難。`--ff-only` 是安全欄杆。
5. **吸收的授權語義**（機制在本節；誰可執行）＝[outward-action-consent](../../rules/outward-action-consent.md)「Commit 專屬段」邊界宣告——本地 ff-only merge 為 marshal 自主（AIR-200 predicate delegation），rebase 後 receipt stale 須重驗；本 skill 不複刻 predicate。

> **rerere**：feature 反覆 rebase（onto trunk 或彼此）時，相同衝突自動套用前次解析。建議 `git config --global rerere.enabled true`。

---

## 執行流程

### Phase 0：arg 角色 = f(當前 branch)

**第一個動作，任何操作前。** 若 arg = `all` → 進入 [all 批次模式](#all-批次模式)（語義仍由當前 worktree 決定，見該節）。

否則，`/rebase <branch>` 的 `<branch>` 是「另一端」——**角色由當前 branch 決定，不是固定 trunk**。第一步永遠：

```bash
git branch --show-current
```

| 當前 = | `<branch>` 是 | 操作 |
|--------|--------------|------|
| **trunk**（慣例 `main`） | feature | `git merge --ff-only <branch>`（吸收步，鐵律 3）→ Phase 3 報告 |
| **feature** | 任意 branch（trunk 或另個 feature） | 進入 Phase 1 rebase 流程 |

**當前 = trunk（吸收步）**：**不 rebase**（鐵律 2）。前置檢查：
- arg 須是 feature（≠ trunk；arg = trunk 本身 → 拒絕）。
- 工作目錄須 clean —— dirty → 停下，提示先 commit/stash（merge 路徑不適用 `--autostash`，旗標忽略；吸收步在整合線上，不 smooth over trunk dirt）。例外：WIP 與 incoming diff 路徑**不相交**時可 ff（判準見 all 批次模式「ff 後綴」節）。

先驗 ff —— trunk 須是 arg 祖先才能快轉：

```bash
git merge-base --is-ancestor HEAD <branch>   # exit 0 = 當前（trunk）是 arg 祖先 = ff 可能
```

- **exit 0** → `git merge --ff-only <branch>`，印 `✅ <current>: merge --ff-only <branch>`。吸收步不 rebase（跳過 Phase 1-2），但 **trunk 剛前進 → 進入 Phase 3** 報告其他 feature 落後狀態 + 提示自行同步。
- **exit 1** → arg 尚未 rebase onto trunk；**不強制 merge**，提示「切到 `<branch>` worktree 跑 `/rebase main`（鐵律 3 step 1：feature 先 rebase onto trunk）」。

> **方向記法**：`--is-ancestor A B` =「A 是 B 祖先」。要把 `<branch>` 併進 trunk，trunk 須落後 arg → 查 `--is-ancestor <trunk> <branch>`，**不是** `<branch> <trunk>`。

**當前 = feature（rebase 步）**：arg 是任意非當前 branch（trunk 或另一個 feature）→ 進入 Phase 1。Feature 之間互 rebase 的依賴鏈與 replay 順序由呼叫者自負。

### Phase 1：確認狀態 + 分叉預覽

> 到此必為「當前 = feature」（Phase 0 已分流）。`<branch>` 是 rebase base（trunk 或另一個 feature）；下文以「**base**」指稱 `<branch>`，「trunk」專指整合線（慣例 `main`）。

1. **`git status --porcelain`** — 確認工作目錄狀態（clean / dirty）
2. **分叉預覽**：判斷 rebase 風險等級

```bash
git merge-base --is-ancestor HEAD <branch>   # exit 0 = HEAD 落後 base → fast-forward
git merge-base --is-ancestor <branch> HEAD    # exit 0 = HEAD 已含 base → up-to-date
# 兩者皆 exit 1 → diverged。單一指令取雙方計數（避免 parallel 鏡像 A..B 結果錯位）：
git rev-list --left-right --count <branch>...HEAD   # 左=base 獨有，右=current 獨有（將被 replay）
```

| 分叉狀態 | 風險 | 說明 |
|---------|------|------|
| fast-forward | 🟢 零風險 | HEAD 落後 base，直接快轉 |
| up-to-date | 🟢 零風險 | HEAD 已包含 base，rebase no-op |
| diverged | 🟡 可能衝突 | 雙方各有獨有 commit，N commits replay |

3. **印出確認**：`當前分支: <current>，base: <branch>，<分叉狀態>`

4. **base worktree HEAD vs base branch ref 消歧**（防誤讀 `git worktree list`）：rebase 的 base 永遠是 **`<branch>` 的 branch ref**（`git rev-parse <branch>`）。`git worktree list` 顯示的 base worktree HEAD 可能**落後** base branch ref（該 worktree 未 checkout 最新，或處於 detached），但那與 rebase base **無關** —— 你不在 base worktree 操作。若 `git worktree list` 的 base HEAD ≠ `git rev-parse <branch>`，提示「base 採 branch ref（`<ref>`），非 base worktree HEAD（`<head>`）」消歧，省下釐清 stale HEAD 的 tool call。

**不 clean 的處理**：
- **預設（無 `--autostash`）** → 停下，提示用戶先 commit 或 stash。
- **帶 `--autostash`** → 不阻擋，Phase 2 改用 `git rebase --autostash`（git 自動 stash→rebase→pop）。

### Phase 2：Rebase 當前 branch

```
git rebase [--autostash] <branch>   # --autostash 僅在帶旗標時加
```

**基本規則**：當前（feature）branch rebase onto 輸入的 `<branch>`（base）。帶 `--autostash` 時，git 自動把 dirty 變更 stash、rebase 完 pop 回來。

> ⚠️ **autostash pop ≠ rebase 衝突流程**：autostash 的 `git stash pop` 發生在 rebase 完成（或衝突解完 `--continue`）之後，是獨立事件。若 pop 衝突（WIP 與 rebase 結果撞行），留下 conflict markers，需手動 Read + Edit 解 —— 不在下方「衝突分析流程」涵蓋內。帶旗標前自問 WIP 是否可能撞 base 改動。

| 結果 | 處理 |
|------|------|
| 成功 | `✅ <current> rebase onto <branch>（N commits replayed）` |
| 衝突 | **進入衝突分析流程**（見下方） |
| 空 commit（變更已包含在 base） | AI 預設建議 `git rebase --skip`（rebase 後空 commit 無語義價值），除非用戶有明確理由保留 |

### 衝突分析流程（rebase 衝突時觸發）

> ⚠️ **Rebase 中 ours/theirs 與 merge 相反**
>
> | 操作 | `<<<<<<< HEAD`（:2:） | `>>>>>>> branch`（:3:） |
> |------|----------------------|------------------------|
> | **merge** | 當前分支 | 被合併的分支 |
> | **rebase** | base 分支（`<branch>`） | 當前分支（被 replay） |

Git index stages: `:1:` = 共同祖先, `:2:` = HEAD（base branch = `<branch>`）, `:3:` = incoming（current branch）

#### Step 1：收集衝突資訊

- `git diff --name-only --diff-filter=U` — 列出所有衝突檔案
- 逐檔 `Read` 衝突標記區段，用 `rg -n "^<{7}|^={7}|^>{7}" <file>` 定位每個 conflict block

#### Step 2：產出衝突比對表（強制）

**每個衝突檔案必須產出以下表格**，每個 conflict block 一列。漏列 = 漏分析 = 解決不完整。

衝突類型分類：

| 衝突類型 | 定義 | 正確解法 |
|---------|------|---------|
| **獨立新增** | 雙方在同一位置加不同東西（最常見：import 衝突） | **兩者都保留** |
| **架構重構** | 一方重構結構，另一方用舊結構 | 採重構方，適配另一方邏輯 |
| **邏輯衝突** | 雙方對同一行有不同意圖 | 需用戶判斷 |
| **刪除 vs 修改** | 一方刪除，另一方修改同處 | 需用戶判斷（刪除是否過時？）；機械遷移 vs **較新 user 裁決**衝突＝較新裁決勝出 |
| **同名 drift**（cherry-pick／跨 wt 雙寫） | 同名同目的、不同結局（兩邊各自改了同一檔） | **取 incoming**（replay 語義忠實——保留 feature branch 已 commit 的意圖；取 HEAD 會吃掉 feature 獨有內容） |
| **核銷 replay**（`[ ]`→`[x]`） | commit message 明言核銷意圖的 checklist replay | **採 incoming**（零判斷機械保留使用者自己的 commit 內容；同型續解不需再確認） |
| **同一行新舊版** | 同名行衝突兩側非等價——一側含後續批次更新、另一側為舊版 | **比對內容保較新語義**（非按 ours/theirs 慣例機械取側） |

比對表格式：

```markdown
### <file> 衝突比對

| Block | 行號 | HEAD（<branch>）加/改 | Incoming（<current>）加/改 | 衝突類型 | 建議 |
|-------|------|----------------------|--------------------------|---------|------|
| 1 | 36-41 | `import SubscriptionGroup` | `import RankedStock, RankingSnapshot` | 獨立新增 | 保留兩者 |
| 2 | 140-150 | `_resolved_subscriptions` + 多行註解 | `_watchlist_data: WatchlistData` | 架構重構 | 採 incoming + 遷移 HEAD 端 `_resolved_subscriptions` 用法至新介面 |
```

#### Step 3：等用戶確認

逐衝突或批次確認。用戶可：
- 接受建議
- 指定不同方案
- 要求看更多細節（如完整 conflict block 內容）
- **`abort`** — 放棄 rebase（`git rebase --abort`，完整回到 rebase 前狀態，不需 reflog）

**確認 gate 無回應 fallback**（AskUserQuestion 未獲回覆）：衝突屬**零歧義機械型**（上表「兩者都保留／取 incoming／採 incoming」類）＋操作可逆（rebase 可 abort／reflog 舊 tip 可回復）→ 依建議自主解決＋報告附回復路徑（abort 指令／舊 tip sha）；**邏輯衝突仍停等**。兩條件缺一不得套用。

#### Step 4：執行解決 + 驗證

1. `Edit` 精確寫入解決內容（逐 block，非整檔覆寫）
2. `git add <file>`
3. **驗證**：確認 resolved file 包含比對表中標註「保留兩者」的雙方內容
   - 在 resolved file 中 `rg` 搜尋比對表列出的 HEAD 端和 incoming 端識別符
   - 發現漏失 → 修正後再 continue

4. 確認無漏失後 `git rebase --continue`
5. 如有後續 commit 衝突，重複 Step 1-4

### Phase 2.5：Post-Rebase 語義驗證

Rebase 成功後（無衝突或衝突已解決），檢查**非衝突區域**的語義一致性。

**為什麼需要**：Git 三方合併只標記「同一行的不同修改」。如果一方將 X 改名為 Y 且與另一方衝突（同行），衝突會被標記。但如果檔案另一處也引用 X 但該行沒被另一方修改 → git 認為「無衝突」auto-merge 保留舊名 X → runtime crash。

**驗證步驟**：

1. 識別 incoming commits（`git diff ORIG_HEAD..HEAD`，rebase 後 `ORIG_HEAD` 自動指向 rebase 前的 tip）中涉及的**識別符改名**（如 `futures_codes → futures_watchlist`、class 刪除、函數簽名變更）
2. `rg` 搜尋被改名/刪除的舊識別符在**整個 codebase**（不限衝突檔案）中是否還有殘留引用
3. 特別關注：import 改名、dataclass 欄位改名、函數簽名改名 — 這些會波及 git 認為「無衝突」auto-merge 的檔案
4. 發現殘留 → 視同衝突，Read + 分析 + 用戶確認 + Edit 修正

### Phase 3：報告其他 feature 的 trunk 落後狀態（提示，不自動 rebase）

> **核心：方向由呼叫者決定**（呼應開頭鐵律）。Phase 3 **絕不自動 rebase 或 ff 任何 branch**。它只報告「哪些 feature 落後 trunk 多少」並提示對應同步動作（有 wt 切 worktree 跑 `/rebase`；純祖先無 wt 用 ref 層 ff 指令）。多 worktree 同步是你在 VSCode workspace 切換的決定，不是本命令的批次動作。

**觸發條件**（兩條獨立路徑之一，見下表；feature 互 rebase 不觸發，見下方「不觸發」段）：

| 到達方式 | base | 報告對象 |
|---------|------|---------|
| 吸收步後（Phase 0 `merge --ff-only` 成功，trunk 剛前進）| 不適用（吸收步不走 rebase）| **所有** feature（trunk 前進，每個 feature 都可能落後）|
| feature onto trunk 後（Phase 2 成功）| trunk | **其他** feature（排除當前 —— 當前剛 rebase 完已在 trunk 上）|

**不觸發**：base = feature（feature 互 rebase，Phase 2 的 base 是另一個 feature）→ **跳過整個 Phase 3**。這次是 feature 間依賴調整，與 trunk 基線同步無關，提示只會是噪音。

**報告步驟**（只讀，不 rebase）：

1. `git branch --format='%(refname:short)'` — feature 全集（**不以 `git worktree list` 當全集**：無 wt 的 branch 在其中結構性不可見）；`git worktree list` — branch → worktree 對應，分出 wt-backed 與無 wt 兩群（都屬報告對象，排除 trunk 與當前）
2. 對每個報告對象 feature，查落後 trunk 量：
   ```bash
   git rev-list --count <feature>..<trunk>   # trunk 獨有、feature 沒有的 commit 數 = 落後量
   ```
3. 列出現狀 + 提示，**不執行任何 rebase / ff**：
   - 落後 > 0（有 wt）→ `⚠️ <feature> 落後 <trunk> N commits → 切到該 worktree 跑 /rebase <trunk>`
   - 落後 > 0（無 wt）→ `git merge-base --is-ancestor <feature> <trunk>`：exit 0（純祖先，零獨有 commit）→ `⚠️ <feature> 落後 <trunk> N commits（無 worktree）→ git fetch . <trunk>:<feature>（ref 層 ff）`；exit 1（diverged）→ `⚠️ <feature> diverged 且無 worktree —— 同步需建 wt`（真死路，如實報）
   - 落後 = 0 → `✅ <feature> 已在 <trunk> 上`（可省略）

無其他 feature → 跳過。

> 要讓 feature 的工作**進 trunk**：Phase 2 把 feature rebase 到 trunk 之上（feature 變 trunk 後代）後，在 trunk worktree 跑 `git merge --ff-only <feature>` 才真正推進 trunk（鐵律 3）。

### Phase 4：報告

```
## Rebase Report

當前: replay → trunk: main

### 結果
✅ replay: rebase onto main（5 commits replayed）

### 其他 feature（Phase 3 報告，未自動同步）
⚠️ backbone 落後 main 3 commits → 切到 backbone worktree 跑 /rebase main
⚠️ legacy-sync 落後 main 2 commits（無 worktree，純祖先）→ git fetch . main:legacy-sync

### 總結
1/1 成功，0 衝突（backbone/legacy-sync 待你手動同步）
```

---

## all 批次模式

`/rebase all` 把 Phase 0 的單一動作**批次套用到所有 feature**。語義由當前 worktree 決定（沿用 Phase 0，零特判）：

| 當前 worktree | all 語義 | 對每個 feature 做什麼 | 碰哪些 worktree |
|---|---|---|---|
| **trunk**（`main`） | 批次**吸收** | `git merge --ff-only <feature>`（只 ff-able 的） | 只 trunk（ff-only 不碰 feature wt） |
| **feature** | 批次**同步** | 當前 `git rebase main` + 其他 `git -C <wt> rebase main` | 當前 + 其他（`git -C`，不換 session） |

> all 永遠 onto trunk，**不管 feature 互 rebase**（那是呼叫者手動的 `/rebase <other-feature>`，依賴鏈自負）。多個 diverged feature 各自 onto trunk rebase，互不影響，順序無關。

> **user 慣用泛化（超出「永遠 onto trunk」文法）**：「all rebase on `<branch>`」＝非 trunk base 批次（user 實證用法）——全員 ff-able 時：main 側走**吸收步**（wt clean 前置＋`git -C <main-wt> merge --ff-only <branch>`，鐵律不 rebase trunk）、有 wt feature `git -C <wt> rebase <branch>`（=ff）、無 wt `git fetch . <branch>:<feature>`——零 replay 零風險，終態同 tip。

> **雙 feature 同內容收斂**：feature 互 rebase 後兩條攜帶「同內容、不同 hash」——收斂順序＝main 吸收**超集**那條（`merge --ff-only`），另一條 `git rebase --empty=drop <tip>`：patch-identical commits 全變空自動 drop（replay 原版 patch-id 與已解衝突副本不同，`--skip` 手動逐個不等效；rerere 已啟用時同款衝突自動套前次解）。另有淨零對齊法：replay 後 `git diff <base> <branch>` 零實質差（僅空行位置）且主題已承載於 base → `git -C <wt> reset --hard <base>`（wt clean 前置）——比留空 commits 乾淨。

> ⚠️ **同步語義改寫其他 worktree HEAD**：`git -C <wt> rebase` 會改寫其他 feature wt 的 HEAD/index。執行前確認其他 feature wt 無並行 session（否則該 session 的 git 假設失效）。dirty 檢查擋住資料遺失，但 clean wt 的進行中 session 仍受影響。

> **all 與 Phase 3 的關係**：all 同步語義已把所有 feature rebase onto trunk，落後狀態當場消除——不另跑 Phase 3 落後報告（無落後可報）。all 的產出是 Step A4 三類報告（✅/⚠️/❌），不是 Phase 3 的「誰落後多少」。

### Step A0：決定語義 + 動態列舉 feature（禁寫死）

```bash
git branch --show-current                    # 當前 = trunk → 吸收；當前 = feature → 同步
git branch --format='%(refname:short)'       # 所有本地 branch —— all 目標集合的唯一來源
git worktree list                            # branch → worktree 對應（同步語義 git -C 用）
```

**目標集合 = 當次 `git branch` 輸出 − trunk**。列舉必須來自本次執行的 git 即時輸出——禁止寫死：不用本文件示例名（`replay`/`backbone` 等是格式示意）、不用記憶或上次執行的清單；不同 repo、不同時刻 branch 集合都不同。

- **trunk 解析**：慣例 `main`。同步語義下 `main` 不在 `git branch` 輸出 → 停下問用戶 trunk 是哪條，不猜測。
- **branch 無 worktree**：
  - 吸收語義：`merge --ff-only <feature>` 不需要 feature wt —— 無 wt 的 branch 照樣是吸收對象。
  - 同步語義（diverged）：rebase 須在該 branch 自己的 wt 內跑（`git -C <wt>`）—— 無 wt 且 diverged 的 branch 列入 A4 報告 ⚠️（無 worktree，未同步），不在當前 wt checkout 它 rebase（會切走當前 wt 的 branch）。
  - 同步語義（純祖先）：`--is-ancestor <feature> <trunk>` exit 0（落後、零獨有 commit）→ `git fetch . <trunk>:<feature>`（ref 層 ff，不碰任何 checkout；refspec 無 `+` 前綴時非 ff git 自動拒絕——內建欄杆）。

### Step A1：對每個 feature 算分叉分類（Phase 1 既有，批次套用）

同步語義：

| feature 狀態 | 判定 | 動作 |
|---|---|---|
| up-to-date（含 feature 領先 trunk，rebase no-op） | `--is-ancestor <trunk> <feature>` exit 0（trunk 是 feature 祖先 = 相等或領先） | skip ✅ |
| fast-forward（落後、無自己 commit） | `--is-ancestor <feature> <trunk>` exit 0 | 有 wt：`git -C <wt> rebase <trunk>`（= ff，零風險）；無 wt：`git fetch . <trunk>:<feature>`（ref 層 ff，見 Step A0） |
| diverged（有自己 commit） | 兩個 `--is-ancestor` 鏡像皆 exit 1 | 完整 rebase，**衝突才停** |

吸收語義：`--is-ancestor <trunk> <feature>` exit 0 = ff-able（`merge --ff-only`）；exit 1 = ff 不符（觸發停止點 #4）。並行兄弟 feature 只有第一個能 ff（吸收後 main 前進，其餘相對新 main 不再 ff-able）—— ff-only 自然拒絕，不 special handle。

同步時檢查每個 feature wt dirty；吸收時檢查 trunk wt dirty。

### Step A2：批次驅動（`git -C`，不換 session）

依分類執行。up-to-date / ff 自動跑完不問（`git fetch .` ff 無 replay，不需 Phase 2.5）。**遇停止點才停 + 給菜單**（Step A3）。每個 rebase 成功的 feature 跑 Phase 2.5 語義驗證（identifier 改名殘留，見「Phase 2.5：Post-Rebase 語義驗證」段）——與既有 reuse 的 Phase 1 / 衝突流程並列。

### Step A3：停止點菜單（每個停止點 = 問題 + 處置選項，等你選）

| # | 停止點 | 觸發 | 處置選項（選一） |
|---|---|---|---|
| 1 | feature dirty | 該 feature wt 有 uncommit | ① 去 wt commit/stash 後重跑這個 ② `--autostash` 重跑（pop 可能衝突）③ **跳過這個，繼續其他** ④ abort all |
| 2 | feature 衝突 | rebase 撞衝突 | 既有衝突流程（Step 1-4 比對表+建議）：① 接受建議 ② 改方案 ③ `--skip` 該 commit ④ abort 該 rebase ⑤ abort all |
| 3 | main dirty | trunk wt 有 uncommit | ① 去 trunk commit/stash 後重跑 ② **跳過，繼續其他** ③ abort all（merge 路徑**不** autostash；trunk 的 uncommit 不自動動；WIP×incoming 不相交的 ff 例外見「ff 後綴」節） |
| 4 | 吸收 ff 不符 | trunk 上 all，feature 落後/diverged 不能 ff | ① 提示「切到該 wt 跑 `/rebase main` 先同步再吸收」② 跳過 ③ abort all |
| 5 | 空 commit | 變更已含在 base | ① `--skip`（建議）② 保留 ③ abort all |

**共通出口**：每個停止點都可「**跳過這個繼續其他**」或「**abort all**」。不自動跳過——跳過的若是關鍵 feature 結果不完整，你該知情。

### Step A4：報告（三類，列遺留）

```
## Rebase Report（all）

當前: feature（同步）→ trunk: main

### 結果
✅ replay: rebase onto main（2 commits replayed）
✅ legacy-sync: fetch ff onto main（無 worktree）
⚠️ backbone: 跳過（dirty，未處理）
❌ features-x: 衝突未解（卡在 rebase，等你處置）

### 總結
2/4 完成，1 跳過，1 待處置
```

跳過/失敗的 feature 不能默默丟下——報告列遺留，你一眼看到哪些還沒同步。

### `ff` 後綴（`/rebase all ff`）：收斂鏈交付語義

**語義**：把目標集合（Step A0 全集，含無 wt 衛星）收斂到**同一 tip**。收斂鏈是交付物不是報告——結束時全員同 tip，不留「跳過＋建議指令」菜單。`ff` 後綴擋的是**無謂 replay**（patch-identical／空 commit），**不是 diverged 停等**：diverged feature 的自有 commits 屬必要 replay，照做跑完。

**標準動線**（有 diverged 時的收斂鏈；全員 ff-able 即退化為「user 慣用泛化」形）：

1. **Survey（每次重新）**：`git branch -v` + `git rev-list --left-right --count` 分類——並行 session 隨時移動 branch（含整鏈 rebase 重寫、hash 全數過期），同 session 早前快照（含自己剛跑的 rebase 結果）不可信
2. **Feature 鏈對齊**：diverged feature `git -C <wt> rebase <base>` replay 自有 commits（patch-identical 的 git 自動 skip）
3. **trunk 吸收**：`git -C <trunk-wt> merge --ff-only <superset-tip>`（trunk wt clean 前置；吸收前先算 count——`<trunk>...<feature>` = 0/0 表示終態已達，不需執行 merge）
4. **其餘 branch ff 對齊 tip**：wt-backed `git -C <wt> merge --ff-only <tip>`（clean 時 `rebase` 同效）；無 wt 衛星 `git fetch . <tip>:<branch>`（ref 層 ff）

**dirty wt 的 ff 例外**（吸收步與衛星 ff 同適用）：ff 型操作（`merge --ff-only`）允許 dirty wt——前檢「WIP 檔 × incoming diff 路徑」`comm -12` 交集（untracked 路徑同查）：**不相交 → 執行**（git 內建 overwrite 保護為欄杆，WIP 原樣保留；並行 session 的 WIP 不代為收尾）；**相交 → 停止點 #1/#3**。rebase 型操作（含必要 replay）仍須 clean 或 `--autostash`。

**傳播紀律**：跨 worktree 的變更傳播一律走 rebase/ff 鏈，不手動鏡射/寫入其他 wt（含 trunk wt——生產 checkout，命令外的任何寫入都越權）；本命令吸收步寫入 trunk wt 屬命令授權範圍。

**Upstream 慣例**：工作 branch 純本地（不設 upstream、不 push），只有 trunk 追蹤 origin——收斂後「trunk 領先 origin N commits 未 push」是標準遺留項，push 恆待 user AUTH。

---

## 參數

| 參數 | 說明 |
|------|------|
| **\<branch\>** | 「另一端」分支，**角色由當前 branch 決定**（見 Phase 0）：當前 = trunk → `<branch>` 是 feature（被吸收）；當前 = feature → `<branch>` 是 rebase base（trunk 或另個 feature） |
| **all** | 批次模式：把 Phase 0 動作套用到所有 feature。語義仍由當前 worktree 決定——trunk 上 = 批次吸收（`merge --ff-only`）、feature 上 = 批次同步（`rebase <trunk>`）；見 [all 批次模式](#all-批次模式) |
| **ff 後綴**（搭配 `all`）| 收斂鏈交付語義：全集收斂同 tip——必要 replay（diverged 自有 commits）照做、擋無謂 replay；標準動線與 dirty wt 例外見 all 批次模式「ff 後綴」節 |
| **--autostash** | dirty 工作目錄時自動 stash→rebase→pop（預設停下問；**僅 rebase 路徑**；`--stash` 為 user 慣用同義詞）。帶旗標 = 你知道有 WIP、要保留、且準備好處理 pop 衝突 |

**對比例子**：
- 在 `main`（trunk）上 `/rebase replay` → `<branch>` = `replay`（feature）→ `git merge --ff-only replay`（吸收步）
- 在 `replay`（feature）上 `/rebase main` → `<branch>` = `main`（trunk）→ `git rebase main`
- 在 `replay`（feature）上 `/rebase backbone` → `<branch>` = `backbone`（另個 feature）→ `git rebase backbone`（feature 互 rebase，依賴鏈由呼叫者自負）
- 在 `replay`（feature）上 `/rebase all` → 批次同步：當前 `rebase main` + 對每個其他 feature（`git branch` 動態列舉，見 Step A0）`git -C <wt> rebase main`（無 wt 且純祖先 → `git fetch . main:<feature>`，見 Step A0）
- 在 `main`（trunk）上 `/rebase all` → 批次吸收：對每個 feature（`git branch` 動態列舉，見 Step A0）逐一 `merge --ff-only`（只 ff-able）
- 在 `replay`（feature）上 `/rebase all ff` → 收斂鏈：survey → diverged 必要 replay → main `merge --ff-only` 吸收 superset → 其餘 ff 對齊同 tip（見 all 批次模式「ff 後綴」節）

---

## 執行約束

### 強制

- 必須先確認當前分支和工作目錄狀態
- 必須當前 worktree clean 才能 rebase（帶 `--autostash` 例外：dirty 由 git 自動 stash/pop）
- Phase 3 僅報告其他 feature 落後狀態，**不執行 rebase、也不自動執行 `git fetch .` ff** —— 正因不執行，無需確認其他 worktree clean（要同步由你自行跑：有 wt 切過去 `/rebase`，屆時做 clean 檢查；純祖先無 wt 直接 `git fetch .`——ref 層不碰 checkout，無 clean 檢查問題）
- 必須使用 `git -C <path>` 操作跨 worktree，禁止 `cd`
- 衝突時必須分析雙方變更意圖，提出解決方案，等用戶確認後才執行
- 未經用戶確認不得執行 `git rebase --continue`

### 禁止

- ❌ **`git checkout --theirs` / `git checkout --ours`** — 這是核彈級操作，直接丟棄一方所有變更。必須逐衝突 Read + Edit 精確解決
- ❌ 未經用戶確認就解決衝突並 continue rebase
- ❌ `cd` 到其他 worktree 目錄
- ❌ 跳過 clean 檢查直接 rebase
- ❌ **未先 `git branch --show-current` 分流 arg 角色就動作**（本命令最常見誤判：假設 arg 一律是 trunk）
- ❌ **當前 = trunk 卻跑 `git rebase`**（鐵律 2；trunk 用 `merge --ff-only` 吸收）
- ❌ **一般 `/rebase <branch>` 的 Phase 3 自動 rebase / ff 其他 feature**（含對無 wt branch 跑 `git fetch .`；方向由呼叫者決定，Phase 3 只報告 + 提示）。批次同步/吸收改用 `/rebase all`（顯式 opt-in，帶停止點菜單）
- ❌ **all 模式自動跳過卡住的 feature**（停止點必須停下給菜單；跳過是用戶選的，非預設）
- ❌ **all 模式把目標 branch 寫死**（目標集合 = 當次 `git branch` 即時輸出 − trunk；本文件示例中的 `replay`/`backbone` 是格式示意，不是列舉來源）

---

## 回復機制

Rebase 完成但用戶不滿意結果時，用 reflog 回復：

```bash
git reflog show <branch> --format="%h %gD: %gs" | head -10
# 找到 rebase 前的 commit（通常是 "rebase (finish)" 之前的條目）
git reset --hard <pre-rebase-commit>
```

⚠️ 如果 branch 已 push 過，回復後需要 `git push --force-with-lease` 同步 remote。你手動同步多個 feature 後若要回復，被 push 過的每個都需要 force push。

---

## 流程位置

```
/commit（--push / --rebase）→ /rebase <branch>（單一 feature，trunk 永不被 rebase；Phase 3 報告其他 feature 落後 + 提示自行同步）
/rebase all（批次：feature 上 = 同步所有 feature onto trunk；trunk 上 = 吸收所有 ff-able feature）
```

獨立使用，通常在 commit 之後或每日開工前執行。每日開工同步多 feature，在任一 feature wt 上跑 `/rebase all`。
