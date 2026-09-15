---
harness-scope: neutral
---

# 工具紀律

## 工具選擇原則

符號→code-reality、型別→bridge、文字→rg、檔案→fd（詳 [symbol-query-routing.md](symbol-query-routing.md)）。視覺判讀走 vision-review agent，禁主 session 讀圖；spawn prompt 必指定工具（如 LSP hover、rg），禁只寫「讀取/驗證」。

## Skill 調用紀律

意圖對應既有 skill 時，主 session 先讀再動手/派發；換 agent 不換方法論。

## Python 命令執行（單一源）

一律 `uv run python`/`uv run pytest` 前綴，禁 `python`/`python3`/`PYTHONPATH`（含 `=$PWD` 形式）。多行 `python -c` 禁換行後 `#` 註解；改單行或 .py。pytest 背景跑；禁外部 `timeout`/`gtimeout`（macOS 無此命令）。逾時替代法、ModuleNotFoundError 處置見 debugging-and-error-recovery skill。

## zsh 動態 flag 組合（陣列、禁純量）

動態 flags 用 `args=(--flag 1)`＋`cmd "${args[@]}"`，禁 `"--flag 1"` 純量；替代＝分支組合或 `--flag=1`。

## 檔案修改禁令

- 禁 sed 修改 .py/.md/.yaml/.json/.toml；只可過濾流。
- Edit/Write 前先 Read；外部改動後重讀。共享檔先 rg 自己的唯一錨點，old_string 不包他人行；搬移拆精準 Edit。

## 背景執行

長命令與 spawn agent 背景執行：spawn **一律明帶 `run_in_background: true`**，回報進行中即結束 turn 等通知；**ZCode 端省略自動補背景，前景（含 <30s probe）須 prompt 帶 `[fg]`**。行為契約見 agent-workflow skill「Spawn 預設背景」。

## 閘門命令禁 pipe 到 tail/grep

pipe 預設回最後程序 exit，會偽裝綠燈；gate 輸出重導再 Read 或 `set -o pipefail`，禁憑 tail/grep exit 宣稱通過。

## Read 紀律（context 佔用）

已完整讀過的檔案重查用 rg/offset/limit，禁再全讀；大檔具體問題先定位。

## 獨立呼叫批次化

獨立 Read/搜尋/git/LSP/不重疊 Edit 同 block 發；下步需本步結果才算依賴。lint/type/test 組單命令、各自重導標失敗段再 Read。

## 輸出慣例

繁體中文＋英文術語。

Edit 失敗階梯全文、zsh flags 邊界、Read 紀律案例見 tool-discipline skill。
