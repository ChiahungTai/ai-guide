# 快照：synthesis 議題 5（hooks wiring 矩陣）＋議題 6（後綴擋零實作＋coverage matrix）

> 來源：`.agent-tmp/guides-refactoring/synthesis.md` 議題 5／議題 6 兩節逐字快照（`.agent-tmp` 為暫存區會清，本快照為唯一持久源）。
> 快照日：2026-09-16（guides-refactoring EP S2 開工前置）。
> 原文標記體系：〔事實〕＝有錨、〔M-A 判讀〕、〔M-D 判讀〕、〔推論〕＝歸納者。

---

### 議題 5：hooks wiring 矩陣（memory-write governance）

- 〔事實〕CC＋ZCode 兩家：PreToolUse `Edit|Write|NotebookEdit`→block-memory-index-write.py、PostToolUse→memory-write-sensor.py、Stop→memory-index-regen.py；CC 另有 FileChanged dirty-sensor＋SessionStart watch-seed（CC-only）（F-C rows 1-5/7-9）。
- 〔事實〕Codex：**memory-write governance 零 registration**——`~/.codex/config.toml:339-381` 全事件盤點無 `Edit|Write` matcher／memory script；retired 檔亦無（F-C row 6＋not-found 1）。
- 〔事實〕ZCode SessionEnd：live config 無該事件鍵——ZCode 3.7.7+ 事件子集限制，**非遺漏**（F-C row 10）。
- 〔事實〕muse plugin 僅註冊 PreToolUse（自濾 add_memory/edit_memory→inbox 導流＋終局 deny）；runtime approve 靜態不可證＝unknown——update 後未重 approve 即停火 fail-open 窗口（F-C row 11）。
- 〔事實〕codex config stale `[hooks.state]` 殘留引用已退役 `~/.codex/hooks.json` 路徑（`config.toml:208-209,238-239`）（F-C unverified 11）。
- F-C 與 M-D 兩矩陣逐 row 相符，無矛盾。

### 議題 6：涵蓋面——「狀態後綴硬擋未實作」重大發現

- 〔M-D 判讀，事實錨齊〕**air-90「狀態後綴（-pending/-inflight/-landed 等）新建條目 exit-2 硬擋」完全未落地**：決策文本在 air-90 卡 `:20`、承接 air-100 P3（`:42`），但 `hooks/block-memory-index-write.py` 全文 269 行無任何 stem-suffix 邏輯；repo-wide regex 掃 `hooks/`、`muse-plugins/`、`scripts/`、`skills/memory-audit/` 零條 suffix-deny 實作。**被擋的 writer 路徑＝無（零）；沒被擋＝全部**（M-D「對狀態後綴的具體回答」節）。
- **矛盾顯式列出**：README 議題 7 猜「硬擋疑只護 muse inbox 路徑」；M-D 實測＝**連 muse inbox 路徑也沒護，對所有 writer 皆 gap**（四層宣稱對照①）。README 猜測過於樂觀，以 M-D 實測為準。
- 〔M-D 判讀〕coverage matrix 其餘：CC/ZCode 主 session Write/Edit＝covered（附條件：opt-in 限有 generator 目錄、crash 非阻斷、stderr 送達未證）；**NotebookEdit＝gap**（matcher 含字面但 script 無分支直落 exit 0，CC+ZCode 皆然——dead-matcher）；**subagent tool write＝gap**（ZCode 2026-09-01 實證 16,154 chars 落地無攔）；muse tool write＝**unknown**（接線齊、fire 未證；2026-09-14 live receipt 屬過期證據）；muse teardown／Bash redirect shell 直寫／codex 寫池＝gap（前兩者僅事後偵測 reconcile；codex 連偵測掛點都無——「唯讀」僅紀律非機械）。
- 〔推論〕「air-90 卡面 Done 但 enforcement 不存在」與議題 2「pilot 宣稱 draft 未跑」同屬「卡面狀態與實作脫鉤」模式（§2）。

> 快照註：源文「全文 269 行」為 M-D 審查時點數字；2026-09-16 入册實測該檔已為 273 行（檔案持續演化，行數快照以當下 `wc -l` 為準）——結構性事實（無 stem-suffix 邏輯）不隨行數變化。
