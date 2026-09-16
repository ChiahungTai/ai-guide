---
name: modern-cli-preference
description: "搜尋工具陷阱細則載體（reference skill）——fd/rg 旗標與 alternation 陷阱、grep 旗標遷移、glob 錨定、git pathspec 三陷阱、統計用途禁 head 截斷、盤點執行點雙掃；rule 已退為指針（路由權威＝symbol-query-routing rule；fd/rg 陷阱目錄在本 skill）。觸發詞：rg 陷阱、fd、pathspec、head 截斷、計數、統計、旗標遷移、盤點雙掃、-H、--hidden、alternation、ls-files。"
---

# modern-cli-preference — 搜尋工具陷阱細則

> 本 skill 是搜尋工具陷阱細則的 on-demand 載體：rule 端已退為指針，工具選擇路由權威＝symbol-query-routing rule；陷阱目錄在本檔——**寫 rg/fd/git pathspec 命令前載入**。

Claude Code 對 `find -exec`/`grep -r` 有系統層硬限制，`fd`/`rg` 預設可 auto-allow；其他 harness 無此限制，但 fd/rg 的語法與噪音優勢通用。

## fd/rg 陷阱（基礎語法是原生知識，此處只列會誤導的）

- **fd pattern 匹配檔名不是路徑**：搜尋特定目錄用 `fd . <dir>`；`fd src/` 是搜尋檔名含 `src/` 的檔案非搜尋 src/ 目錄
- **隱藏檔/gitignored 檔陷阱**：fd/rg 預設跳過 dotfiles 與 ignore 檔，**旗標跨工具不同義**——fd：`-H` hidden、`-u` 全解；rg：`--hidden`/`--no-ignore`（`-H` 是 with-filename 非 hidden）；dot+ignore 疊加態（如 `.code-review-graph/` 自帶 `*` ignore）兩旗標併用（NT graph.db 1.4G 誤判不存在實案）
- **rg alternation 陷阱**：`rg "a\|b"` 搜尋 literal `a|b`，**不是**「a 或 b」。多選一用 `rg "a|b"`（雙引號內 `|` 直傳 rg）或 `rg -e a -e b`（markdown 表格 cell 內一律用 `-e` 多 pattern，避開 `\|` 轉義歧義）
- **固定字串用 `-F`**（預設走正則）；**glob `-g` 比 `--type` 靈活**（`--type py` 不含 `.pyx`/`.rs`）
- **shell 版號比較禁字串不等**（字串序 `"1.10" < "1.9"` 為真）——比版號用 `sort -V` 語義序
- **多檔搜尋加 `--heading`**：檔名只印一次（預設每行重複完整路徑）；路徑已知時直接指定檔案不遞迴
- **grep 旗標不可遷移到 rg**：grep `-h`（抑制檔名）rg 是 help——免檔名用 `-I`；`-r` grep=遞迴、rg=--replace（複合旗標 `-rn` 拆開讀，`-r` 會替換 match 污染輸出）。真實案例：`rg -h pattern` 印整份 help、`rg -rn pattern` match 全成 "n"（grep 慣性遷移）
- **rg `-g` glob 錨定路徑 arg 形態**：`-g '!dir/**'` 對絕對路徑 root arg 靜默失效——要生效用 cwd＋arg `.` 或 `!**/dir/**`（hazard runner 實案：mock 全繞過、真 rg 測試才抓到）

## 統計/計數用途禁用 head 截斷

> **核心原則**：rg「展示用途」（看有哪些檔）與「統計用途」（得數字寫進文檔/claim）命令不同。統計用途禁 `| head -N` 截斷後人工數。

| 用途 | 命令 |
|------|------|
| 展示（看範例） | `rg -l "pattern" \| head -N` |
| **統計:檔案數**（寫進文檔/claim） | `rg -l "pattern" \| wc -l`（**禁 head 截斷**） |
| 統計:per-file match 數 | `rg -c "pattern"`（輸出 `file:count` 多行，語境不同於檔案數） |

**真實案例**：`rg -l "from <pkg>" | head -20` 截斷 → consumers **41 誤寫 20**（head 只列前段），多處文檔寫錯，**自審抓不到**（claim 與截斷證據共享盲點，需獨立第三方 rg 才揭露）。同類陷阱不同載體：符號查詢的 truncation/masking 見 [symbol-query-routing](../../rules/symbol-query-routing.md)。

## git pathspec 陷阱

git pathspec 命令（`ls-files`/`log`/`status`/`diff`）一律從 repo root 跑——目錄內執行會 CWD-relative 解析成巢狀不存在路徑**靜默回空**（誤判 untracked／無歷史）；staging 已消失目錄禁 trailing slash（`dir` 可 stage、`dir/` fatal）；`fatal` 短路 `&&` 鏈但 `;` 段照跑——批次 staging 後必看 `git diff --cached --stat` 勿信命令鏈跑完。

## 盤點執行點：間接層與直呼層雙掃

盤點執行點雙掃（間接層 make target/wrapper 引用＋直呼層 raw command——CI 跑哪些測試、哪些入口呼叫某工具、cutover 影響域的完整性盤點）見 [acceptance-evidence](../acceptance-evidence/SKILL.md)「盤點執行點雙掃」章。
