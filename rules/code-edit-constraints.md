---
harness-scope: claude-specific
---

# 程式碼編輯約束（Claude）

> **載入機制**: 本檔 source 在 ai-guide repo `rules/`；Claude 端經 `~/.claude/rules/` symlink auto-load（claude-specific——不進非 Claude bundle）

> Claude Code 專屬的 Edit/Write 工具 API 約束。通用編輯紀律（SRP/DIP/變更紀律/禁混合寫法/向後相容）見 [edit-discipline.md](edit-discipline.md)（neutral）。

## Edit 工具使用約束

> **核心原則**：Edit 前必須先 Read，確保 `old_string` 精確匹配檔案當前內容。

### 強制規則

- **Edit 前必須 Read**：編輯任何檔案前，必須先讀取該檔案確認當前內容
- **重複編輯同一檔案**：每次 Edit 後若需再次編輯同一檔案，必須重新 Read 取得最新狀態
- **`old_string` 必須精確**：直接從 Read 輸出複製目標文字，不可憑記憶或推測拼湊

### ❌ 常見錯誤模式

```markdown
## ❌ 錯誤：未重讀就編輯（old_string 與檔案實際內容不符）
# 第一次 Edit 成功後，檔案內容已改變
# 第二次 Edit 仍用舊的 old_string → Error editing file

## ✅ 正確：每次 Edit 前重新 Read
# 1. Read file → 取得當前內容
# 2. Edit file（用 Read 到的精確內容）
# 3. 若需再次 Edit → 先 Read 取得更新後的內容
```

### ❌ replace_all 改名的子串陷阱

`replace_all` 用**子串匹配**（非整詞邊界），改名 `A→B` 時所有含 `A` 子串的都會被改 — 包括不想改的。Edit 工具無整詞邊界選項（不像 regex `\b`），只能事後 rg 查。

```markdown
## ❌ 錯誤：replace_all 改名誤改子串
# 改名 RateLimiter → SyncRateLimiterProtocol (replace_all)
# SyncRateLimiter (含 "RateLimiter" 子串) → SyncSyncRateLimiterProtocol (誤改!)

## ✅ 正確：replace_all 改名後 rg 確認無子串誤改
# 1. 改名前 rg "<目標詞>" 看是否是其他符號的子串（如 rg "RateLimiter" → 發現 SyncRateLimiter 含子串）
# 2. 改名後 rg "<新名><新名>" (如 rg "SyncSync") 確認無雙重重複
# 3. 或改用 Edit 逐處替換（非 replace_all），精確控制每處
```

> 真實案例：`SyncSyncRateLimiterProtocol`（rate_limiter 改名 `RateLimiter`→`SyncRateLimiterProtocol` 時，replace_all 誤改 `SyncRateLimiter`）— review 時抓到。

### 連續 Edit 失敗處理

Edit 失敗的完整處置階梯（re-Read → 停止盲試 → repr 唯讀診斷 → 縮小 old_string → Write 覆寫）見 [tool-discipline.md](tool-discipline.md)「Edit 失敗處置階梯」（neutral canonical）。Claude API 行為備註：跨行匹配含多位元組字元（中文等）可能失敗，即使 `old_string` 精確——縮小 old_string 只匹配目標周圍的 ASCII 部分可避開。

### 連續同類錯誤處理

寫出的程式碼反覆出現同類錯誤時，必須停下改變策略：

- **連續 3 次同類語法/邏輯錯誤** → 停下，用 `uv run python -c "compile(...)"` 或 `uv run ruff check` 驗證，確認修正方向正確後再繼續
- **禁止盲目重試**：不改變策略的反覆嘗試是浪費時間
