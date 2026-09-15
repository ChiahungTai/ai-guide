# EP 獨立審查工單

Role=Reviewer；authority=findings only；judgment_floor=decision；qualification=review_findings。唯讀，不改任何檔案、不 commit、不部署、不跑長測試、不再委派。主 session 會寫入你的 findings 並裁決。cwd=/Users/ctai/Github/ai-guide。這是文件控制面設計審查，rg/Read 查文件拓樸即可，無 callable CR 檢查需求。

先讀 `ai-analysis/_tasks/09-15-development-workflow-redesign/ep.md` 全文。此計畫是新流程提案，不是現行規範；不能僅因它改變現有固定多 reviewer 預設就判違規。Marshal 實作基線 b4a301992356e8960892894f392e91346a4d492f 已完成，本 EP 不重新實作。

方法論讀 `skills/ep-review/SKILL.md` F1–F5、`skills/review-engine/SKILL.md` 嚴重度/查證、`skills/arch-thinking/SKILL.md`；據疑點用 rg 定位、分段讀 EP 指名的 current sources。尤其 `skills/post-build/SKILL.md` 去重、`skills/_common/workflow-review-pattern.md` identity、`skills/compact-prep/SKILL.md`、`skills/metadata-sync/SKILL.md`。不要把全部 skills 全載或另做全 repo review。

覆蓋 F1完整性/F2合規/F3一致性與責任邊界/F4遺漏/F5情境。重點：是否減量卻丟防線、是否復用錯誤證據、checkpoint 另造狀態庫、AIR-60重複承諾、部署切換與rollback、自稱 docs mode 卻需程式碼、conditional review 是否存在無人驗收出口、哪些設計已現存卻重造。

只交有實據且可修正的 findings，附 severity/confidence、EP file:line、反例場景、建議修法、可機械驗證式；最多列最重要六項，沒有就明說無 actionable findings。不要給 final disposition 或 apply，不產待 user 問題清單。尾部列五維度覆蓋及未讀/未驗證限制。輸出以繁體中文，簡潔自足，首尾不可截斷。
