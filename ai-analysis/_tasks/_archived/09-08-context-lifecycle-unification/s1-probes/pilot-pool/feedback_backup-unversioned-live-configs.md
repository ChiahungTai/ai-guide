---
name: feedback_backup-unversioned-live-configs
description: 改無版本活配置（gitignored settings.json 等）前先 cp .bak——備份→換→pipe-test→新 session 驗證；回滾不靠 transcript
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_17c46ac6-2f64-4ecd-9a98-ef1651a3fcb1
---

2026-08-30 memory hooks 接線：把 Claude settings.json（gitignored、正生效）與 ~/.zcode/cli/config.json（repo 外）的 inline hook 換軌成 repo script——**兩者皆無 git、皆未先備份**，舊指令只存在於當下 session transcript（Read 過的原文）。

**Why**：「已讀原文」是最脆弱的備份——context 會被壓縮 elide、session 會消失；gitignored ≠ 不需回滾。換軌動作本身正當（single-source），錯在順序：先整合後驗證，新 session 實測若失敗，回滾路徑=從對話記錄撈字串。

**How to apply**：Edit 任何無版本控制且正在生效的配置前 `cp x x.bak-YYYYMMDD`；正確換軌序=備份→換→pipe-test→新 session 驗證→驗證過才刪 .bak。同型場景：launchd plist、MCP config 等任何 live 系統的替換。**常態化形態（08-30 弧收斂）＝差異留存進 tracked rollback doc**：換軌前原始字串逐字＋還原步驟寫進 repo 內文件（`hooks/memory-hooks-rollback.md` 實例）——優於 .bak 全檔：git 版本控制、跨 session 可執行、無「忘了刪 .bak」問題；.bak 仍是臨時保險，rollback doc 是持久資產。

相關：[[memory-cc-alignment-diagnosis-0905]]
