# 開發流程 skills 架構審查

中間檢查點。基準 HEAD：ac6cccf50299637ff9587559d166834cf33e8b7d；工作目錄 /Users/ctai/.codex/worktrees/5da1/ai-rules。開始時 git status --short 為空；detached HEAD。審查當前 worktree，使用者貼文作為背景，證據行號以工作樹為準。

授權：逐項架構審查並寫 checkpoint。只寫本目錄；不改 skills/rules、不建卡、不 commit、不執行被審查的 implement/post-build 副作用。

方法：arch-thinking 的 docs 路徑（rg 跨檔拓樸 + Read），review-engine 的自證/否證與信心標記。Markdown 是 LLM 執行控制面，審查焦點為指令可執行性、責任歸屬、交接狀態、scope 與證據時效。非 Python import 圖任務，不以 CR/LSP 證明 Markdown 行為。未實跑不同 harness 的整鏈；可確認文件契約矛盾，不宣称每個 LLM 都必然走錯。

順序：spec → execution-plan → implement → code-review → judge-review → post-build → 跨鏈合成。arch-thinking 本身作方法論；其設計觀察另記。

責任圖：spec 產需求；EP 產可執行段落與意圖基準；implement 改產品與驗證；code-review 產 findings；judge 產 decisions；post-build 編排 apply/followup/文檔/殼。旁路共用源：metadata-sync、workflow-review-pattern、followup-review、review-engine。

已浮出待逐項核實：docs triage 是否略過行為審查；finding 的 EP vs .review 帳本分裂；finalization 早於末輪驗證；spec 邊界是否完整進 EP。
