---
name: zcode-session-query

description: "（ZCode 專用）跨 session 查詢與參考：查 session 清單/id、讀指定 session 尾部真人互動、ReadSessionContext 引用。handoff / relay 的「讀進來」側"
when_to_use: "ZCode session 需要理解另一個 ZCode session 的內容時：handoff 接手方回查來源 session、user relay 互傳訊息、比對 compact 前後品質、盤點並行 session。僅 ZCode 有效（依賴 ~/.zcode 遙測 DB 與 ZCode 內建 ReadSessionContext；Claude / Codex 端不適用）"
allowed-tools:
  - Bash
  - Read
---

# zcode-session-query — ZCode 跨 session 查詢（唯讀）

> **ZCode 專用**：資料源是 `~/.zcode/cli/db/db.sqlite`（ZCode 遙測 DB），工具依賴 ZCode 內建 `ReadSessionContext`。其他 harness 無此 DB 與工具，本 skill 不適用。

ZCode **無 session 間直接通訊**（`SendMessage` 僅限同 session 的 subagent）。跨 session 理解一律走唯讀查詢：本 skill 是「讀進來」側；「給出去」側（產交接 prompt）用 `handoff` skill，兩者互補。

## 操作一：查 session 清單 / id

```bash
uv run python - <<'EOF'
import sqlite3
con = sqlite3.connect("file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro", uri=True)
for sid, title, ts in con.execute(
    "SELECT id, title, datetime(time_updated/1000,'unixepoch','localtime') "
    "FROM session WHERE time_archived IS NULL ORDER BY time_updated DESC LIMIT 5"
):
    print(sid, "|", ts, "|", title)
con.close()
EOF
```

活躍 session 即時可查（訊息逐輪寫入，不需等結束）。`task_type='subagent_child'` 是 subagent，跨 session 查詢時通常排除。

## 操作二：讀指定 session 尾部真人互動

```bash
uv run --project ~/Github/ai-guide python ~/.zcode/skills/zcode-session-query/scripts/zcode_tail_chat.py <session-id前綴> [輪數=4] [每則字數=400]
```

輸出最後 N 輪 `[USER]`/`[AI]` 交錯原文——user 的話 + AI 的文字回覆，排除工具呼叫/系統噪音。適合：看對方 session「剛剛談到哪」、handoff 前確認來源狀態、compact 品質比對的「實際紀錄」側。

## 操作三：ReadSessionContext（AI 端摘要讀取）

對話中直接調用 ZCode 內建 `ReadSessionContext` 工具，讓 AI 帶 query 讀取另一個 session：

- **`strategy=handoff`**：返回 Handoff Capsule（接續摘要）——預設選擇，實測可用
- **`strategy=relevant`**：聚焦檢索——**大 session（數百則訊息）實測逾時 300s**，僅小 session 用
- 活躍 session 可讀；唯讀單向（被讀方無感、無法回覆）

## 陷阱（實測得來）

- **session id 禁手打**：uuid 一個字元抄錯即 silently not found——一律複製貼上，或不確定時用 `LIKE 'sess_<前8碼>%'` 前綴查
- **`sqlite3` CLI 對此 DB 會無聲空輸出**（原因未查明）——改用 python `sqlite3` 模組 + `file:...?mode=ro` uri 連線
- `ReadSessionContext` / `SendMessage` 官方文檔未記載（2026-08 全量鏡像 27 頁零記載）——行為以實測為準，升級後重新驗證

## 資料結構速查（DB 直查 / 維護腳本時用）

三層：`session`（id / title / directory / time_archived）→ `message`（一輪；`data` JSON 是 metadata：role / modelID / cost / semantics）→ `part`（正文；`data.type='text'` 的 `text` 欄位）。

真人互動判別：`role='user'` 且 part **無 `synthetic` 欄位**＝真人輸入（tool result / continuation note / system reminder 都帶 `synthetic: true`）；`role='assistant'` + `type='text'`＝AI 文字回覆。一輪 assistant message 含多 part（`tool` / `reasoning` / `text`），只取 `text`。
