---
name: rebase-skill-nowt-ff-fix
description: rebase skill 無 worktree branch 純祖先 ff 修正——主修 0f6291e 閉環、二修 33d6aa6；09-04 後續 all ff 收斂鏈語義落地 250f716
metadata:
  node_type: memory
  type: project
  originSessionId: sess_9c0d1bc6-699f-43f4-89ce-5ee470189bf3
---

2026-08-30：mosaic rebase session handoff（sess_11311689）反饋落地於 `skills/rebase/SKILL.md`（13 edits：12 主修＋1 consistency finding 修復）。核心變更：Phase 3 枚舉源 `git worktree list` → `git branch` 全集（root cause＝無 wt branch 結構性不可見致單一模式漏報）；無 wt 純祖先（`--is-ancestor <feature> <trunk>` exit 0）走 `git fetch . <trunk>:<feature>` ref 層 ff（refspec 無 `+` 非 ff 自動拒絕）；單一模式維持 report-only、all 批次自動 ff。刻意偏離 relay patch（:185 註明→行為修正）見 [[relay-claims-verify-current-state]] 第二十二實例。

**主修已閉環：commit `0f6291e`**（user "OK" 確認、pre-commit hook 39 tests 全過、僅 rebase SKILL.md 單檔入 commit）。

**mosaic 獨立審查回執（基於 pre-commit 快照）**：裁決「改得好」——認可行為修正＞註明、git 語義零誤、report-only 紅線守住；回執「commit 未決」本身過時（[[relay-claims-verify-current-state]] 第二十三實例）。兩 nit 查證成立已修：①強制段「屆時各自做 clean 檢查」過度包含 fetch 路徑（ref 層 ff 不碰 checkout）→ rebase/SKILL.md:339 收斂僅 wt 路徑；②skills/CLAUDE.md:96「不自動 rebase」補「／ff」對齊 skill 約束。rg 驗證通過。

**二修已落地 33d6aa6**（stage 僅 rebase SKILL.md＋CLAUDE.md 兩檔；2026-08-31 audit 回寫；`skills/code-reality/SKILL.md` 並行 session 改動持續不納入）。skills 部署＝三方 symlink（~/.zcode、~/.claude、~/.agents 的 skills/ → ai-rules/skills），edit 即生效無 deploy 動作。
