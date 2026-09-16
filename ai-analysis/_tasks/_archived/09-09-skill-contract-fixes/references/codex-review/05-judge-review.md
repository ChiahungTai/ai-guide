# judge-review 檢查點

已完成本項文件契約審查。

## JR1 — Important / confirmed：finding 決策帳本在呼叫鏈分裂

證據：judge-review:56 要寫 EP 並排除 .review 作決策落點；post-build:43、49、58 固定 .review 生產、讀取、followup；workflow-review-pattern:121-126 是有 EP 用 EP、無 EP 用 .review；followup-review:61 又稱 .review 為法定帳本。

反例 A：post-build 產 F1=open 到 .review；judge 在 EP 寫 F1=adopted；apply 後 followup 按呼叫端指定讀 .review，看到舊 open/無 decision。反例 B：獨立 judge 無 EP，callee 禁 .review 決策、又必須持久化，沒有明確合法落點。

否證：同 session 可把決策放 context 傳遞，因此不是每次都失敗；但這正違反持久化用於跨 session 交接的目的。gitignore 不會在同一 worktree 換 session 時刪除實體檔，local-only 與「跨 session 不保留」不可混為一談。

建議：caller 明確解析並傳 findings artifact 路徑，review/judge/apply/followup 更新同一份；無 EP 的持久化 fallback 必須可用。不是強制所有人工 review 寫帳本。

驗收：有 EP/無 EP、同 session/換 session 四情境，F1 從 open→adopted→implemented→verified 全程同一 artifact，不靠對話補接；拒絕與 needs-confirmation 不被錯當待 apply。

## JR2 — Suggestion / confirmed：裁決與執行的命令語氣互撞

judge-review:31 要「採納就當下落地」，56、87-89 則明定只裁決、不實作。後者是明確終點，故不認定必然越權；前者作通用政策未指定 actor，會干擾獨立模式。

建議：反拖延義務明確給呼叫端 apply，judge 的 obligation 是交付可執行決策與驗證依據。保留裁決與實作分離。

## 設計觀察

三防線的證據/否證/實測要求有價值；但「成立問題」與「採用這個解法」應各自可否證。inferred finding 必須實测的例外（純規範矛盾、無權限環境）目前靠 needs-confirmation，不建議為這次審查硬造 runtime POC 證明文字矛盾。
