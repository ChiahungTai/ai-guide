---
name: git-mv-nesting-and-verification-traps
description: 遷移機械陷阱五連——git mv 嵌套、先 Edit 後 mv 遺漏（rename 100% similarity 症狀）、fd 限深度
  漏層、&&鏈斷後 ; 的 rm -rf 照跑、untracked 檔隨 rm -rf 滅不可復原
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_89592a9f-fbba-4b02-ade1-3b58b15bfd54
---

大批 git mv 遷移的機械陷阱（2026-09-02 ai-rules 三池遷移＋.kanban 退役實證，教訓已記 EP 但屬通用 CLI 規律）：

1. **`git mv <src> <已存在目錄>`＝嵌套**（mv 語義）：`git mv 00-tasks ai-analysis/_tasks`（_tasks 已 mkdir）→ 產出 `_tasks/00-tasks/…` 巢狀。正解＝目標不存在時才整體 mv，或逐檔攤內容；修法＝逐檔 `git mv` 攤平＋`rmdir`。
2. **結構驗證 fd 勿限深度＋記得 --hidden**：`fd '00-tasks' . -d 2` 漏第三層嵌套＝假 CLEAN（目錄存在性驗證一律無深度 `fd`）；dot-dir（`.kanban`）驗證需 `--hidden`（fd 預設跳 dotfiles——兩陷阱同一驗證動作連踩兩次）。
3. **`&&` 鏈中一環失敗後，`;` 分隔的清場命令照跑**：`mv(fail) && git rm(skip); rm -rf <dir>` → rm -rf 仍執行，且會把 untracked 檔一併掃掉。破壞性命令與條件鏈分開跑，或全程 `&&`。
4. **untracked 檔隨 rm -rf 滅不可復原**：`git mv` 對 untracked 檔報 bad source 不動它——但隨後的 `rm -rf` 不分 tracked/untracked。ai-rules `.kanban/CLAUDE.md` 從未入 git → 永久滅（所幸記載的是已退役慣例）。刪目錄前 `git ls-files <dir>` 盤點 tracked 集合；untracked 有價值內容先遷再清。

關聯：[[underscore-prefix-sort-cross-tool]]（fd hidden 旗標跨工具差異）。
