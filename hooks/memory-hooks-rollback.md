# Memory Hooks Rollback——換軌回滾指引

> **何時用**：新 session 兩條 live 實測任一失敗（① 手寫 MEMORY.md 未被 PreToolUse 攔、或攔了但指引未達模型且造成重試迴圈；② turn 結束索引未重生成）。原始 inline 指令逐字留存於此（單一留存處），任何 session 可執行，不依賴 transcript。

## Claude 端（settings.json＝repo 本地 gitignored 檔，經 `~/.claude/settings.json` symlink 生效）

把下方兩條原始指令貼回對應 hook 物件的 `command`（取代 `python3 /Users/ctai/Github/ai-guide/hooks/...` 兩行）：

**Stop 陣列第二個 hook 物件**（目前是 `python3 .../memory-index-regen.py`）：

```
M="$HOME/.claude/projects/$(echo "$CLAUDE_PROJECT_DIR" | sed 's|[^A-Za-z0-9]|-|g')/memory"; if [ -f "$M/_generate_index.py" ]; then python3 "$M/_generate_index.py" || true; fi
```

**PreToolUse（matcher `Edit|Write|NotebookEdit`）hook 物件**（目前是 `python3 .../block-memory-index-write.py`）：

```
F=$(python3 -c 'import sys,json;print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))'); D=$(dirname "$F"); if [ "${F##*/}" = "MEMORY.md" ] && [ -f "$D/_generate_index.py" ]; then echo "⛔ MEMORY.md 是 generator 投影，禁手寫——改條目檔後執行: python3 $D/_generate_index.py（Stop hook 也會自動重生成）" >&2; exit 2; fi
```

改動生效時效：**ZCode 需新 session**（官方文檔 per-session snapshot 語義）；**Claude 端新 session 必生效**（熱載入未證——config 定稿後啟動的 session 屬保證路徑，編輯後同 session 即測的結果不可預期）。

## ZCode 端（live `~/.zcode/cli/config.json`，repo 外）

移除本弧新增的兩組接線（恢復到本弧前狀態）：

1. PreToolUse 刪 `matcher: "Edit|Write|NotebookEdit"` 整組（block-memory-index-write.py）
2. Stop 陣列刪 `memory-index-regen.py` 那個 hook 物件（保留 stop-notification.sh）
3. **保留** `block-python-file-write.py`（Bash matcher）——那是既有 template parity 修復，非本弧產物

`hooks/zcode-registration.json`（repo 模板）**不隨回滾**——它是 repo 資產；回滾僅作用 live config。回滾後 repo 腳本留在 hooks/（不刪）：rule/skill 已宣稱機制，修復後可重接線（check_single_source 的 `zcode_live_parity` 會在重接前報 critical——這是預期行為，提示接線未完成）。

## 修復後重接線

ZCode：把 `hooks/zcode-registration.json` 全文重新 merge 進 live config 的 `hooks` 鍵（merge 不是整檔覆蓋——config 含 mcp/plugins 區塊）。Claude：把 repo script 指令貼回（見上方「目前是」的兩行）。
