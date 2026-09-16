---
name: skills-deploy-dir-level-symlink
description: skills 部署形態會漂——.agents 目錄級 symlink 恆真；.zcode 兩觀測矛盾——判定當場 ls -ld＋ls -i 比 inode，勿信快照
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_46296df8-834d-4b38-a1ec-ca15be970844
---

ai-rules `skills/` 的跨 harness 部署觀測史（形態至少變過/誤判過一次——**判定一律當場驗**）：

- `~/.agents/skills` → 目錄級 symlink 直指 repo skills/（歷次觀測一致）。
- `~/.zcode/skills`：09-02 觀測＝目錄級 symlink；09-06A 觀測＝真目錄＋per-file hardlink（同 inode、`cp` 報 identical）；**09-06B 觀測＝目錄級 symlink 直指 repo skills/**（`ls -ld ~/.zcode/skills` 直證；Edit 換 inode 後兩路徑同新 inode＝同檔語義，hardlink+rename 寫入會分岔）；**09-07 觀測＝per-file hardlink 再現**（post-build SKILL.md 兩路徑同 inode 320475168；Edit 就地寫後 cmp SYNCED＝hardlink 保住免 relink；同日稍後 deep-work/compact-prep/tour-bootstrap/CLAUDE.md 連續五檔跨多批 Edit 後 cmp 恆 SYNCED——hardlink 在 Edit 就地寫入下穩定保持；斷鏈修復形＝`ln -f <src> <deploy>`）。同日 handoff brief 稱「~/.zcode/skills 為部署拷貝非 symlink」是誤標——relay 描述不可信（[[relay-claims-verify-current-state]]）。09-06A 可能正是踩了下述陷阱①（leaf readlink 空、未沿父層鏈上溯即判 hardlink）。兩個 09-06 觀測直接矛盾——**可攜結論不是「現在是哪型」，是「每次部署疑問當場 ls -ld 父層鏈＋ls -i 比 inode」**。

- 09-07（project-review 刪除弧）：三路徑（.zcode/.agents/**.claude**——.claude skills 首次入觀測）的 skill leaf `ls -ld` 皆現真目錄形（未沿父層鏈驗，勿據此斷 copy）；但 repo 端 7 檔 Edit 後三路徑部署面 cmp 恆 SYNCED＋rg 殘留掃空＋mtime 隨編輯刷新——**部署面隨 repo 編輯即時一致、免手動搬運**（alias 語義強訊號；底層機制未驗，leaf 真目錄形可能正是陷阱①的父層鏈穿透）。**同弧收案：`readlink ~/.claude/skills ~/.zcode/skills ~/.agents/skills` 三根全數 → `/Users/ctai/Github/ai-rules/skills`——三根皆目錄級 symlink，leaf 真目錄形確為陷阱①父層穿透，「底層機制未驗」懸念終結**。leaf `ls -ld` 真目錄形在同 session 內兩度誤導 AI 判「實體拷貝非 symlink」（rm -rf「三處部署」實為穿透同檔 no-op）——對照組＝skills/CLAUDE.md:17「三根符號連結指向本目錄」宣稱經 readlink 驗證屬實，文檔宣稱比 leaf 形態觀測可靠。09-06A 與本行前半的「per-file hardlink」判決同被此收案覆蓋（未沿父層鏈的誤判家族）。

驗證紀律：①leaf `readlink` 回空、`ls -la` 顯示真目錄——可能是穿過父層 symlink，也可能是 hardlink，**首查直接 `readlink <根>`（三根各自一發即判目錄級 symlink），未決才沿父層鏈逐一 readlink 到家目錄**；②兩路徑視為兩實體（或宣稱「copy 需重部署」）前先 `ls -i` 比 inode（[[symlink-alias-before-two-entities]]）；③Edit 寫入後再比 inode 可分辨同檔 vs 斷鏈（同新 inode＝同一檔；分岔＝hardlink 被 rename 式寫入斷鏈）。hooks 是對照例外（config 絕對路徑註冊、symlink 無效，見 [[zcode-hooks-porting]]）。
