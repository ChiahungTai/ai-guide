---
name: symlink-alias-before-two-entities
description: 兩路徑視為兩實體前先驗 symlink 別名——同檔 cmp identical 是 tautology 循環證據（09-03 mosaic 兩池誤判實證）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_07836405-5f73-4d17-9619-5456406f7cd3
---

**教訓**：把兩個路徑當兩個實體（兩池／兩目錄／兩檔案）前，第一步機械驗 `ls -la` 查 symlink 別名——**同一實體的兩個路徑名 cmp identical 是 tautology（循環證據），看起來像驗證、實際什麼都沒證**。

**Why**：路徑命名規則差異（ZCode basename-sha vs Claude dash 編碼）讓同一池擁有兩個外觀不同的路徑；未查 alias 的「機械驗證」會建構出虛構的雙實體世界，後續所有裁定（覆蓋範圍／缺口盤點／重複執行）都基於幻覺前提。

**How to apply**：跨路徑一致性檢查前先驗 alias（`ls -la`／`readlink`）；發現「兩實體 identical」先懷疑是同一個；誤判已落地時評冪等性（同池重複跑＝no-op 無害，但文字認知仍要修正——報告會呈現假雙份數字）。**inode 是比 readlink 更強的判準**（09-05 增量）：三個 mosaic memories 目錄 `readlink -f` 各回自身（非 symlink）、看似三實體，但 `ls -lai` 顯示 MEMORY.md **同一 inode**＝hardlink 共享單池三視圖——readlink 乾淨不等於相異實體，目錄非 symlink 仍可能檔案級共享；驗實體用 `ls -lai <路徑們>/<同名檔>` 比 inode。

**實證（09-03）**：mosaic session 裁定 nightly-watch 收斂波「兩池」對象——磁碟事實 `~/.zcode/cli/memories/projects/mosaic_alpha-91db1aef2f9baec8/memory` → symlink → Claude 池（Aug 14 建，與 ai-rules 同構）；其「兩池 generator cmp identical」驗證即 tautology。覆核翻案：單池（別名路徑勿重複跑）、審計腿缺口因前提崩塌不存在、`_audit-state.md` 存在（「MC 池無慣例」是錯句）。相關 [[memory-cc-alignment-diagnosis-0905]]（symlink 段）。
