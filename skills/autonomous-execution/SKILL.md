---
name: autonomous-execution
description: "Guides autonomous execution — decision-making, error recovery, completion reporting, workspace safety, session-level recovery. Use when implementing without user interaction, such as EP-based build or deep-work mode. Triggers on: autonomous execution, self-healing, session recovery, false-done 偵測, workspace safety, path invariants, deferred questions, completion report, don't-self-decide boundaries."
when_to_use: "Fires during unattended execution when a decision, error, or completion claim must be handled without the user——歧義自決＋記錄理由、紅線／黃線分級（commit、force push、DB DROP 等不自主執行）、error recovery、false-done 偵測、completion report 彙整、workspace safety。觸發詞：autonomous execution、無人介入、自主執行、deferred questions。啟動整套開發流程（plan→build→post-build 編排）屬 deep-work；流程已跑起來後的無人決策與安全邊界歸本 skill（deep-work 內同樣適用）。"
---

# Autonomous Execution

Methodology for autonomous implementation when user should not be disturbed. All questions are deferred to a completion report.

## Core Principles

- **不問問題**：遇到歧義時選擇最合理的方案並記錄決策理由
- **不亂要權限**：優先使用 Edit/Write/Read，Bash 僅用於 `uv run` 驗證
- **不趕時間**：充分理解任務後再動手
- **不交半成品**：每個段落必須完整實作、測試通過

## Decision Framework

| 情境 | 決策策略 |
|------|----------|
| 需求/描述有歧義 | 選擇最符合上下文的方案，記錄理由 |
| 多種技術路徑 | 優先選擇簡單、可維護的方案 |
| 命名選擇 | 遵循 python-standards 命名規範 |
| API 設計 | 參考同目錄已有程式碼風格 |
| 錯誤處理 | 遵循 crash-only design 或合理 fallback |
| 測試策略 | 核心邏輯必須有單元測試，邊界情況至少覆蓋一個 |

## Don't-Self-Decide Boundaries

以下情況不自主執行，依紅線/黃線分級處置：

### 🔴 紅線（跳過 + 記錄，絕不自主執行）

**不可逆操作** —— 自主執行風險大於任務完成度。跳過並記錄到 completion report 紅線跳過清單段：

| 類型 | 範例 |
|------|------|
| 檔案刪除（不可逆） | `rm -rf`、`find -delete`、`git clean -fd` |
| Git 遠端 / 歷史破壞 | `git push --force`、`git reset --hard`、影響共享 history 的 `git rebase` |
| Git commit | `git commit`（預設需用戶確認；autonomous 唯一例外＝[outward-action-consent](../../rules/outward-action-consent.md) 0921「conditional commit delegation」——active arc＋有效 post-build receipt，每次 commit 重新驗 gate，predicate 驗收程序＝commit skill；無有效 receipt 的散 commit 仍需確認） |
| 系統層變更 | `sudo *`、`brew uninstall`、`chmod` 系統路徑、`osascript`（macOS 自動化） |
| 外部服務狀態 | `docker rm`、`docker stop`、DB `DROP`/`DELETE`、redis `FLUSHDB` |
| 語意型紅線（既有） | 刪除 API、修改 DB schema、變更外部整合介面、安全邏輯、付費操作 |

> 紅線跳過時 deep-work **不阻塞、不語音通知** —— 早上看 completion report 判讀（呼應 [acceptance-evidence](../../rules/acceptance-evidence.md) L6 人類觀察層：半夜自主跑時人類 viewport 是危險操作的唯一兜底）。
>
> **`git commit` 跳過的語義**：deep-work 階段 5 finalization 預設不自主 commit，變更留在 working tree 等用戶接手（用戶回來後 `/commit` 走 outward-action-consent 流程）；唯一例外＝弧內 review gate 背書成立時走 conditional commit delegation（見上 Git commit 列）。
>
> **`git commit` 預設不因 session 性質改變**：紅線「跳過 + 等用戶接手」為預設 —— 半夜無人（記錄到 completion report 後續）、long session 中用戶回來互動（停下來、展示 commit message、等獨立確認）。autonomous mode 的「連續執行」vibe **不延伸到 commit** —— 無委任時 commit 永遠是互動式 gate（一次授權 ≠ 永久授權）；唯一例外＝outward rule「conditional commit delegation」，且每次 commit 重新驗 gate（一 receipt 一 commit）。

### 機械空間不變量（workspace safety）

紅線清單（上）是**行為枚舉**（`rm -rf`、`git push --force`…），必然漏新形態（新型 symlink 攻擊、路徑遍歷變體）。補**機械空間不變量**雙層——agent 在 worktree 內執行 Bash 時，自我驗證路徑運算不逃逸 worktree root。

> **docs-mode 強度上限**：機械不變量在此是「指導」非 code-level enforce——LLM 可能不遵循。hook 補強（`settings.json` PreToolUse 攔截 Bash 路徑逃逸）列為**未來方向（另一 EP）**，本段不實作。

**執行時不變量**（agent 在 worktree 內跑 Bash 時自我驗證）：

- **path-in-root**：所有 Bash 路徑運算（讀寫、`cd`、`find`/`rg` 範圍）相對於當前 worktree root，**不寫絕對路徑到 worktree 外**。判定：路徑 resolve 後須落在 worktree root 子樹內。
- **symlink-escape 偵測**：不跟隨 canonical path 逃出 worktree root 的 symlink——expanded path 在 root 內但 canonical path 在 root 外即 escape，拒絕。判定法：對路徑 segment-by-segment canonicalize，canonical 結果逃出 root 即拒絕。

**建立時決策**（觸發時機與執行時不變量不同，分開標記）：

- **優先 EnterWorktree**（建立時已限 path `.claude/worktrees/` + name `[A-Za-z0-9._-]`），非裸 `git worktree add`；若必須裸 git worktree，name 需手動 sanitize 同白名單。建立時保護已有，本段聚焦執行時不變量。

### 🟡 黃線（自主決策 + 記錄到 completion report）

**可逆但有風險** —— 選最合理方案繼續，理由寫入 completion report 待確認清單段：

| 類型 | 範例 | 自主策略 |
|------|------|---------|
| Git local 可逆 | `git tag`、`git stash`、`git add`（stage 可逆） | 自主執行（`git commit` 見紅線段——outward-action-consent 要求用戶確認） |
| 檔案系統可逆 | `mkdir`、`mv`、`touch`、單檔 `rm`（可重建） | 自主執行 |
| 開發工具執行 | `uv run`、`pytest`、`make`、`docker run`（新增 container） | 自主執行 |
| 依賴變更 | `uv add`、`uv remove`、`brew install <pkg>` | 自主執行，記錄理由 |

> **紅線清單與通用 rule 的邊界**：紅線清單是 outward action 的 deep-work 場景列舉（快查子集），通用定義（reversibility test + AUTH line + source of truth 邊界）見 [outward-action-consent](../../rules/outward-action-consent.md)。

> 黃線是「任務關鍵依賴」時（例如中段必須 commit 才能繼續），LLM 自主判斷降級路徑（git stash、worktree 隔離等）。

### 與「不問問題」原則的關係

本分級**不 override** Core Principles 的「不問問題」——歧義仍選最合理方案並記錄。但紅線操作的本質是「做了就無法事後修正」，不適用「選最合理」——選了不等於安全。

## Error Self-Healing

```
錯誤發生
  → 讀取錯誤訊息，理解根因
  → 修改程式碼修正
  → 重新驗證
  → 仍失敗 → 換一種修法
  → 連續 3 次失敗 → 記錄問題，標記為 ⚠️，繼續下一個任務
```

## Session 級 Recovery（false-done 偵測 + crash-only reconciliation）

Error Self-Healing（上）是 per-error（單一錯誤重試 ceiling）。**缺 session 級**：LLM 自稱段落 done 但 EP 未真完整（false-done）；跨 session resume 無結算對賬。本段補兩個 solo 形態——continuation retry（normal-exit≠done）+ crash-only reconciliation（resume re-derive 真相）。solo 無 always-on tick、無外部 truth source（如 issue tracker），故兩形態皆 **episodic**（在確定時機觸發一次，非持續監督）。

> **delegate→verify loop（上游見 agent-workflow）**：本段 false-done 偵測是 loop **下游**——上游委派框架（[agent-workflow](../agent-workflow/SKILL.md)「委派框架」delegate→verify）降低 false-done 發生率，本段捕捉殘餘。互补非重複。

### completeness validation（false-done 偵測）

- solo 最危險 drift = 「LLM 自稱 done 但 EP 段落未真完整」（false-done，normal-exit≠done）
- **觸發點**：completion report 生成時（solo 無 always-on tick，改在完成報告這個確定時機——不算太晚，攔截 false-done 後 LLM 可繼續補完）
- **機制**：completion report 對照 EP planned deliverable（段落矩陣全 done？）；未完整 → 標記「normal-exit≠done」+ 列缺漏，**不宣稱 EP 完成**
- **命名釐清**：用「completeness validation」/「false-done 偵測」，**不用「stall 偵測」**——stall = 行程活著不推進；本機制 = 正常 exit 但工作未完整，本質不同
- **範圍限制**：本機制**僅偵測虛假完成聲明**；真正的 silent stall（LLM 從不宣稱 done / 卡住）**不可偵測**，需 session 超時 / 用戶返回等外部機制（超出本段範圍）

### crash-only reconciliation（resume re-derive）

- **solo 真相源** = git state（事實：working-tree diff vs session 前基準）+ EP 段落定義（意圖：每段 scope + 成功標準，靜態文檔）對照
- **觸發點**：跨 session resume（`/at` resume 主要；手動開新 session 次之；handoff 交他人另議）
- **機制**：resume 時 re-derive（git diff 推斷已做事實 vs EP 段落 scope 定義對照 → 推斷哪些段落 done）；**不 restore in-memory**（session 記憶不可信）；**不依賴顯式 done 標記**（deep-work 不 commit，無持久進度追蹤檔）；不符 → 結算差異報告（做了未涵蓋 / 涵蓋未做）
- **intent 來源**：EP 段落定義本身（靜態文檔：scope + 成功標準），**非動態「進度檔」**——reconciliation = 事實（git diff）vs 意圖（EP scope）對照推斷完成度，不需先讀進度追蹤檔；已驗/未驗輸入另讀 EP 進度節「段落結果」欄位（產物路徑／實跑指針／未驗與下一步）——作輸入不作完成度真相；deep-work 無 EP 弧沿用既有 journal，不新造進度檔
- **恢復順序**：跨入口單一源＝[task-recovery](../_common/task-recovery.md)（「恢復順序」節）；本段 crash-only reconciliation 是其機械核對＋語義核對的落地——只重述摘要不算恢復驗證

### 與既有機制的分工（避免重疊）

| 機制 | 作用域 | 觸發點 |
|------|--------|--------|
| **Session 級 Recovery**（本段） | 段落/EP 級 done 驗證 + resume 結算 | completion report 生成 / resume |
| batch ceiling（[build.md](../implement/SKILL.md) 階段 2） | 單 session 內 context 累積防漂移 | 累積多段未經人類判讀（軟觸發） |
| session-boundary review（[acceptance-evidence](../../rules/acceptance-evidence.md) B 軸） | 跨 session intent drift 審查 | resume 時觸發（本段提供觸發器） |

三者作用域不同（段落級 completeness / 單 session context fatigue / 跨 session intent direction），觸發點不重疊。

> **substrate vs review 邊界**：本段 reconciliation = 機械真相 re-derivation（**事實層**：git vs EP scope → 差異報告）；session-boundary intent-drift review = **判讀層**（差異報告 → intent 是否漂移）。本段是 intent-drift review 的 **substrate + 觸發器，不是 review 本身**——避免寫成完整 intent-drift review（scope creep）或只 dump git log（過窄）。本段部分回應 deferred card `session-boundary-intent-drift-review.md`（resume 機械觸發 + re-derive）。

## Permission Minimization

| 操作 | 策略 |
|------|------|
| 修改檔案 | Edit/Write（acceptEdits 模式自動通過） |
| 讀取檔案 | Read/Grep/Glob（無需權限） |
| Python 執行 | 僅用 `uv run pytest` 和 `uv run python` |
| 內聯腳本 | `python -c`、`python3 -c`、`uv run python -c` 等一律**禁止使用 `#` 註解**（會觸發權限提示），需要註解時改寫為 `.py` 檔案 |
| Shell 展開 | **Claude Bash 禁止 `$VAR`、`$(cmd)`**（觸發 simple_expansion / command_substitution），需要變數時用具體值或寫 `.py`；其他 carrier 的 zsh arrays 依 [tool-discipline](../../rules/tool-discipline.md) |
| 多行驗證 | 寫成 `.py` 檔案再 `uv run` |

## Completion Report

實作完成後輸出報告，包含：

```markdown
## 實作完成報告

### 實作結果

**新增檔案**:
- [路徑] - [用途]

**修改檔案**:
- [路徑] - [修改摘要]

**測試結果**: ✅ N passed / ❌ M failed

### 架構決策記錄

| 決策 | 選擇 | 理由 |
|------|------|------|
| [決策] | [選項] | [為什麼] |

### 待確認清單（實作過程中的疑慮）

> 以下是我覺得有問題、自行做了決策的地方。請檢查是否合理，如需調整請告知。

| # | 疑慮描述 | 我的作法 | 理由 | 其他可行方案 |
|---|---------|---------|------|------------|
| 1 | [遇到的問題] | [選了什麼做法] | [為什麼選這個] | [方案A / 方案B] |

### 🔴 紅線跳過清單
- [紅線操作 / 跳過理由 / 影響範圍]（半夜自主跑時不阻塞，供早上判讀；定義見 Don't-Self-Decide Boundaries 紅線段）

### 旗艦裁決摘要（非空時必帶——deep-work「旗艦裁決授權」形態）
- verdict 摘要＋PENDING 殘留（verdict 物四欄全文記卡 Notes，此處只帶摘要供晨間判讀）

### ⚠️ 未解決問題
- [技術失敗或無法降級的問題]
```

> 報告開頭若紅線清單非空 → 加註「⚠️ 含 N 項紅線跳過，需人類判讀」。
