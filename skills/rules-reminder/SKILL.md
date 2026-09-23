---
name: rules-reminder
description: "Enforces the most frequently violated cross-harness rules to prevent permission prompts. Use when writing any Bash command. Covers: rg/fd instead of grep/find, no # after newline in python -c, no $ shell expansion in Claude Bash, uv run for Python, no sed for code, Traditional Chinese output, independent tool calls batched in one block, Read target file before Edit/Write, re-read large files via rg/partial Read not full re-read."
---

# Rules Reminder — 最常被忘記的規則

> **典型觸發情境**：使用者看到 LLM 用了 `find`/`grep`，或多行 `python -c` 中用了 `#` 註解，這些都會觸發權限提示卡關。立即停下手邊動作，改用 `fd`/`rg`，或移除 `#` 註解。

以下是 LLM 最常犯的錯誤（多數觸發權限提示，少數浪費 request 或直接失敗）。**現在起嚴格遵守，不再犯。**

---

## 1. 多行 `python -c` 禁止 `#` 註解

Claude Code 偵測到引號內「換行後接 `#`」會觸發權限提示（"Newline followed by # inside a quoted argument can hide arguments from path validation"）。`#` 緊接開頭引號不觸發，但換行後的 `#` 會。

**❌ 禁止**：`uv run python -c "...\n# 註解\n..."` — 換行後的 `#` 觸發 "Newline followed by # inside a quoted argument can hide arguments from path validation"。即使 `#` 是有用註解也禁止。

```bash
# ✅ 正確 — 無註解
uv run python -c "
from module import something
print(something)
"

# ✅ 正確 — 複雜邏輯寫成 .py 檔案
uv run python scripts/check.py
```

**規則**：多行 `python -c` 中**絕對禁止** `#`。需要註解就寫檔案。

---

## 2. 用 `rg` 取代 `grep`，用 `fd` 取代 `find`

`find -exec` 和 `grep -r` 是 Claude Code 系統硬限制（CC 端機制宣稱；其他 harness 依各自 sandbox 規則），**無法被任何 allow 規則覆蓋**，每次都需手動批准。

```bash
# ❌ 禁止 — 每次都要手動批准
find . -name "*.py"
grep -r "pattern" .
find . -name "*.py" -exec grep "pattern" {} \;

# ✅ 正確 — auto-allow
fd -e py
rg "pattern"
fd -e py . path/to/search
```

### 快速對照

| 用途 | ❌ 禁止 | ✅ 使用 |
|------|---------|---------|
| 搜尋檔案 | `find . -name "*.py"` | `fd -e py` |
| 搜尋內容 | `grep -r "pattern" .` | `rg "pattern"` |
| 限定副檔名 | `grep -r --include="*.py"` | `rg -t py` |
| 排除目錄 | `grep --exclude-dir=dir` | `rg`（預設遵守 .gitignore） |
| 固定字串 | `grep -rF "exact"` | `rg -F "exact"` |
| 搜尋特定目錄 | `find path -name "*.py"` | `fd -e py . path` |

---

## 3. Python 命令執行

Python 命令與 hook owner runtime 例外依 [tool-discipline](../../rules/tool-discipline.md)「Python 命令執行」單一源。

---

## 4. 禁止 `sed` 修改程式碼或文檔

`sed` 不理解程式碼結構，批次替換常造成災難。

```bash
# ❌ 禁止
sed -i 's/old/new/g' script.py
sed -i 's/old/new/g' README.md

# ✅ 正確 — 使用 Edit 工具
# 先 Read → 再 Edit 精確替換
```

---

## 5. Claude Bash 禁止 `$` shell 展開

本節僅限 Claude Bash 權限面（[bash-hard-rules](../../rules/bash-hard-rules.md)）；不套其他 carrier。其他 carrier 的 zsh flags 依 [tool-discipline](../../rules/tool-discipline.md) 使用陣列。Claude Code 偵測到 `$` 開頭的結構會觸發權限提示：

```bash
# ❌ 禁止 — 觸發 simple_expansion
echo $HOME
cat $TMPDIR/file.txt

# ❌ 禁止 — 觸發 command_substitution
echo $(date)
python3 -c "$(echo 'print(1)')"

# ✅ 正確 — 用具體值或寫 .py 檔案
echo "/Users/ctai"
cat /tmp/file.txt
uv run python scripts/check.py
```

**規則**：Claude Bash 命令中**不使用 `$VAR`、`$(cmd)`**。需要變數時用具體值或寫成 `.py` 檔案。

---

## 6. 使用繁體中文 + 英文術語對話

使用者母語是繁體中文，對話和輸出必須使用繁體中文，技術術語保留英文。

```
# ❌ 禁止 — 使用簡體中文
这个模块的功能是什么？
帮我检查一下代码

# ✅ 正確 — 繁體中文 + 英文術語
這個模組的核心職責是什麼？
幫我檢查 code review 的結果
```

**規則**：所有對話、解釋、報告使用繁體中文。專有名詞、術語、程式碼識別符保留英文原樣（API、CLI、CLAUDE.md、doc-decode、filter-tree 等）。

---

## 7. 獨立呼叫批次化 + 改檔前先 Read

多個**獨立**無依賴的工具呼叫（Read、rg/fd、git 查詢、LSP 查不同 anchor、跨檔 Edit）在**同一個 block 一次發出**——每個獨立 call 各耗一個 model request，逐一發是浪費。機械驗證序列（lint/type/test）組成單一命令（`uv run` 前綴、輸出重導再 Read、`|| echo "x:FAIL"` 帶出失敗段）。

**Edit/Write 前目標檔必須已 Read**（harness 硬規則：未 Read 直接失敗；Read 後檔案又被外部改 = 過時失敗 → re-Read 再改）。

**規則**：獨立就同 block 發；改檔前必 Read；鄰近一行式小修合併成一個 Edit；已讀檔重查用 rg 或片段 Read，不再全讀（小檔除外）。

---

## 記憶口訣

> **`#` 是毒藥、Claude Bash 的 `$` 是禁區、`grep`/`find` 是禁區、`uv run` 是王道、`sed` 是地雷、`簡體字是違規`、獨立同發、先 Read 再改**

每次寫 Bash 命令或批次修改前，默念這幾條。

---

> **再次提醒**：你可能剛才用了 `find`/`grep`，或多行 `python -c` 裡寫了 `#` 註解，或在 Claude Bash 命令中用了 `$VAR`/`$(cmd)`。這些都會觸發權限提示。**現在起只用 `fd`/`rg`，多行 `python -c` 不加 `#`，Claude Bash 中不碰 `$`。**
