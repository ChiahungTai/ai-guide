# P1 drill 記錄（AIR-49——池 git 基線 diff-driven 收斂，L4 實彈）

> 執行：2026-09-08 深夜。池＝`~/.claude/projects/-Users-ctai-Github-ai-rules/memory/`（CC 真目錄；zcode symlink 同實體）。
> 基線 commit：`f068330371a8a97bcad9e99238e76a29469cf451`（`chore(memory): 池基線建立`，159 檔，`.gitignore` 三項：`__pycache__/`／`_regen-failed`／`_regen-skipped-stale`）。
> drill 目標條目：`feedback_absorb-patterns-not-tools.md`（**非** `_resident-set.md` 12 常駐清單成員；09-05 user 拍板記錄非活躍弧線）。基準 sha256＝`e0a7b67701c0a8e973e1fc4807b8bf76de62c311a1261742a336ea35192b5daa`（1,408 bytes）。

## a. SM-1 波中斷半套 → discard 回基線 — PASS

| 步驟 | 命令 | 結果 |
|------|------|------|
| 刻意壞編輯 | `echo "DRILL-GARBAGE-LINE-AIR49-P1 …" >> <entry>` | 檔尾多一行 |
| diff 可見 | `git diff` | `1 file changed, 1 insertion(+)`；`+DRILL-GARBAGE-LINE-AIR49-P1 1788880608` |
| 單檔還原 | `git checkout -- feedback_absorb-patterns-not-tools.md` | exit 0 |
| 淨＋逐字還原 | `git status --porcelain`＋`shasum -a 256` | status 空；sha256 `e0a7b677…` 與基準一致 |

## b. SM-2 蒸餾誤刪 → 單檔 checkout — PASS

| 步驟 | 命令 | 結果 |
|------|------|------|
| 誤刪 | `rm <entry>` | status：` D feedback_absorb-patterns-not-tools.md` |
| 單檔還原 | `git checkout -- feedback_absorb-patterns-not-tools.md` | exit 0 |
| 逐字還原 | `wc -c`＋`shasum -a 256` | 1,408 bytes；sha256 `e0a7b677…` 與基準一致 |

## c. SM-6 池 git 化不擾 generator／開場面 — PASS

- 前置：`.git` 在場（`ls -d <pool>/.git` → 路徑回傳）
- `python3 <pool>/_generate_index.py --check` → **exit 0**；輸出節錄：`[OK] 12 resident, 2244 chars, 26 lines（B gate: 6000 chars）／_inventory.md: 132 entries, 21108 chars, 144 lines（--check 未寫入）`＋`rank 分層：hot=0 core=131 cold=1`
- `wc -m <pool>/MEMORY.md` → **2244**（與本弧開場基線 2,244 chars 完全一致——開場面不變代理驗證）
- `--check` 後 `git status --porcelain` 仍空（generator 未寫入、git 化零擾動）

## d. SM-7 並行 writer 撞波二分 — PASS（兩分支）

**分支 1（任一 dirty 檔 <30min → 停波報告，不真跑波）**：
- 製造髒檔：append `DRILL-DIRTY-SM7` → `git status --porcelain`：` M feedback_absorb-patterns-not-tools.md`
- 波前判定（EP 口徑＝檢 **dirty 檔** mtime，非全池 mtime 掃描）：該髒檔 mtime＝23:17:35（<30min，活躍 writer 訊號）→ **判定停波**：`dirty=feedback_absorb-patterns-not-tools.md → SIMULATED HALT (no wave run)`——列檔報告，不覆寫
- 觀察記錄：`find -mmin -30` 全池掃另見 4 檔（`_inventory.md`／`MEMORY.md`／`reference_codex-cli-exec-facts.md`／`project_session-id-continuation-absorption-0908.md`）在 30min 窗內＝並行 session／Stop hook 真實寫入，但其內容與 HEAD 一致（status 淨）——不參與波前判定，佐證 EP 口徑（dirty 檔 mtime）正確：全池 mtime 掃描會誤停

**分支 2（dirty 檔 mtime 全 >30min → 流入快照 commit）**：
- `touch -t` 回調髒檔 mtime 至 2 小時前（21:17:00）
- `git add -A && git commit -m "chore(memory): 流入快照 drill"` → **exit 0**，commit `6bfe03b`（`1 file changed, 1 insertion(+)`）
- log：`6bfe03b chore(memory): 流入快照 drill` → `f068330 chore(memory): 池基線建立`

**drill 產物收尾（池零殘留）**：
- `git reset --hard HEAD~1` → exit 0，`HEAD is now at f068330`
- 終態驗證：log 僅基線 `f068330`；`status --porcelain` 空；目標條目 sha256 `e0a7b677…` 逐字還原；`wc -m MEMORY.md`＝2244

## 已知未覆蓋

- 波中途 writer 撞（EP 誠實標註：機率低、既有「刪除前 mtime 稽核」互補——不模擬）
- 新 ZCode session 開場面 live 腿（SM-6 以 `wc -m` 2,244 chars 代理驗證——本 session 為 subagent 無法開新 session）

## 池終態

`git -C <pool> log --oneline`＝單 commit `f068330`；`status --porcelain` 空；無 remote、無 push；`_trash-0908/` 留存不動；`_resident-set.md`／`_generate_index.py`／`MEMORY.md`／`_inventory.md` 內容零變更。

## 事故記錄（09-09 清晨——F2/F3 補驗 drill 釀成；codex F1-F3 修正輪）

**事故**：主 session 在**真池**上補驗 marker/untracked drill 時，未先跑「波前二分」即執行 `git reset --hard`——並行 session（sess_6af3f89d，air-47 S5 知識同步）04:02-04:04 的 **10 筆未 commit 條目編輯（6 檔，delegate-bridge v1.0.0 終態蒸餾）被一併丟棄**。drill 驗的正是 F1-F3 要防的事故類，而執行 drill 本身違反波前二分（當時 status 已列出 6+2 檔 M——「只是跑個小驗證」心智跳過了檢查）。

**復原**（commit `c64595a`）：ZCode db `part` 表逐筆提取 10 筆 Edit 的 old/new payload（status=completed、時間窗過濾、session 過濾），Edit 工具逐筆重放於 reset 後基準——10/10 全中；regen 後常駐面仍 2,244 chars；池 status 淨。

**未復原（2 檔 delta）**：`at-skill-zcode-cron-gaps.md`／`project_memory-redesign-read-path-0908.md`——寫入者於 ZCode db／CC transcripts／muse bridge jobs 三通道全查無（**來源未知——「查無」只支持不可考，不判定第三通道**〔codex R2 輪歸因修正〕；redesign-read-path 有早於池基線的 db 寫入記錄，屬基線前歷史、不能當本次 delta 重建依據）。committed base 完好；delta 可重推（後者＝AIR-45 終態條目補 AIR-48 終態行，內容在 EP/卡可導出）。

**教訓**（大於 drill 本身）：①**drill 應預設在隔離池跑**——波前二分假設執行者會看 status，但小驗證心智會跳過（本記錄即案例）；②池 git 基線的第一受惠者恰是事故復原（無基準則 delta 永不可考）；③來源未知的 delta 目前缺乏可核對的寫入 payload，尚未復原；此結果支持改善 writer 歸因與復原證據，不能據此判定寫入通道或斷言永不可復原。
