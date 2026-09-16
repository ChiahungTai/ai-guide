# spec 檢查點

中間檢查點；已讀完整 spec。尚待 EP consumer 核實後決定是否升正式 finding。

合理設計：需求澄清與 codebase 研究分開；spec 可省略、EP 自足，避免同一研究做兩次。預設不寫檔、--write 支援跨 session，是清楚的成本取捨，不能把 optional persistence 本身報 bug。

疑慮 S1：spec 的主要增量包含 Always/Ask First/Never 與成功條件（skills/spec/SKILL.md:76-85、95-105）；目前出口對 EP 的說法僅「引用 UC/SM」。須查 EP 是否有完整保留需求邊界與變更授權的欄位；若只保留功能正向情境，Never 約束在跨 session 可能流失。

不升 finding：Phase 1 的 2-3 turns 是互動成本提示；沒有證據表明一定迫使用戶多輪確認。小型跳過 spec 本身合理，是否 high-risk 單檔漏 gate 應看 EP 的 scope 定義。

架構想法：需求 artifact 的價值是保留使用者意圖與禁區，不只是讓 builder 拿到測試清單。EP 可變的技術方案與使用者已確定的界線應分別表達；不需要因此強制所有任務先跑 spec。
