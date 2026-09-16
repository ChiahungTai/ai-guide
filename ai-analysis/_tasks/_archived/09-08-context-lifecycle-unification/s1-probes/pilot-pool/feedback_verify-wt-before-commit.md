---
name: feedback_verify-wt-before-commit
description: commit 雙防護：具名 add＋staged 對帳；commit 前查 log/stat 防 concurrent 帶走或污染（紅燈即停）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d5b0964b-d5f8-4bc6-bd0d-3db4ccd88ab1
---

多 session 共用 working tree——commit 前查 log/stat（防帶走）＋具名 add＋staged 對帳（防撈進）；**看 `git diff --cached` 內容**，name-only 不夠。（09-08 蒸餾：舊實例壓行，留互補盲點四則）

> merged_from: feedback_git-add-specific-files.md, 2026-08-31 (earlier wave)

**核心三律**：①commit 前（尤其放了一陣子）先 `git log --oneline -5`＋`git status --short`——working tree 不是你上次看到的狀態；②**stat 與預期檔數不符＝紅燈停**（refactor 只跑 1 檔先查 concurrent 帶走，勿產出文不對題 commit）；③`git add <具體檔>`禁 `-A/.`（含 skill 內建目錄級 add——並行期目錄 add 後必掃 staged 清單退外來檔），commit 後 `git diff-tree` 驗。

**互補盲點四則**：
- **staging 早被污染（09-03 mosaic 實證）**：具名 add 防不住「staging 裡本來就有別人 staged 的」——commit 前必 `git diff --cached --name-only` 對帳本次清單；補救＝soft reset→`restore --staged .`→只 add 自己的→驗 cached→commit→精確還原他人 staged。
- **反向：我的編輯被帶走（09-06 AIR-30）**：staged 核對要抓「少」不只「多」——某檔從清單消失先 `git log -2 -- <path>` 診斷；內容已落地就不重做，移除出清單＋記錄歸屬。
- **同檔 hunk 糾纏（09-01）**：同檔不同行並行改動整檔 add 必撈進——`git diff` 產 patch 濾 hunk `apply --cached`；**context 3 行會合併 ≤8 行相鄰改動**→先 `-U1` 拆 hunk；「File modified since read」＝並行寫入信號先看全貌。
- **git mv 自帶 stage（09-08 建卡 commit 汙染）**：git mv 早把 rename stage 進 index，後續 scoped `git add <dir>`＋commit 照樣把殘留 rename 掃進去——rename 顯示 100% 相似＝mv 後的內容編輯根本沒被 stage；commit 後 `git show <sha>` 驗實際內容，汙染＝reset mixed→具名 add 重 commit（僅 local 未 push 可救）。
- **pathspec commit 隔離（09-04）**：`git commit -m … -- <paths>`（--only 語義）完全不動共享 staging——比 unstaged 四步干擾小；前提該 path 全屬自己（先 diff 核對）。

舊例壓行：ruff 閘門擴張（08-19，diff 純格式→獨立 style commit）／untracked 目錄 staged 展開（08-28，cached 按 M/A 分解對帳）／patch 匯出缺件（08-25，apply 後對 M 清單）／接手判準（08-26，mtime＋.review 收斂態＋獨立複驗）／lint 閘門 mypy 未配如實記（08-19）。
