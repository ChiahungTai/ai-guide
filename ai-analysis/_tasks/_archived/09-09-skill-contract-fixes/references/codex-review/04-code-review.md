# code-review 檢查點

已完成本項文件契約審查；這次標的是既有 skills，沒有拿空 diff 當審查結果。

## CR1 — Important / confirmed：任務弧自動選取受殘留 diff 大小影響

證據：skills/code-review/SKILL.md:30-36。明確 baseline 參數會看完整弧；自動模式只在 uncommitted 空/trivial 時升弧。post-build:33 同樣只在空或尾段殘留時升弧。

反例：S1 已 commit 修改資料契約；S2 未 commit 且是大型消費端修改；已知同一 EP baseline，無參 review 因 diff 不 trivial 只審 S2。讀上下文可能發現 S1 問題，但 S1 不在正式範圍，也不保證完整審查跨段變化。

否證：使用者明傳 hash 可避免；但自動編排的承諾不能依賴每次手動補 hash。「同 branch 混其他任務」已有排除/註記規則，不是放棄任務弧的理由。

建議：先按已識別 task 決定 scope，再選 diff 取得方式；已知 EP 弧預設帶 baseline，局部 review 必須明確宣告。驗收：S1 committed + S2 large WIP 與 S1 committed + S2 tiny WIP，弧 scope 一致。

## CR2 — Important / confirmed（文件交接）：before snapshot 的身份不一致

證據：implement:79 允許 resume/EP 後另有 commits 時，snapshot 錨 build 起點現狀；code-review:108 固定由 EP baseline hash8 找 before sidecar。

反例：EP baseline=A，開始 implement 時 HEAD=B，準備階段產 B snapshot，下游找 A snapshot。文件已有 missing → 降級，因此不報 silent wrong-result；問題是合法 producer 產物不被 consumer 消費，正常接續失去機械對照。

建議：task integration baseline 與 structure before snapshot 分開記錄身份/路徑；review 消費實際 producer 產物，若 before 晚於 task baseline，明示對照只覆蓋該區間。若目標要完整弧，必須確保 A 基準存在。

未驗證：沒有在本次呼叫 code-reality 寫 snapshot，故不宣稱工具實際覆寫/偵測 stale 的行為。文件中的 HEAD==baseline 保護已存在，不報它「完全無保護」。

## 設計觀察

docs-mode 的架構/正確性/phantom 審查設計合理；真正斷點在 post-build 不呼叫它，見 PB1。fresh-eyes 與 primed 不同前提也合理，不以 agent 數量評估有效性。單檔高 ripple 的 architecture gate 有不足，但 code-review 已有獨立 structural doc reminder，不誇大成所有結構關注皆被跳過。
