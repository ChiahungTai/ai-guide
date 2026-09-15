# EP 修訂 followup（唯讀、禁止再委派）

任務目錄 `/Users/ctai/Github/ai-guide/ai-analysis/_tasks/09-15-development-workflow-redesign/`。
讀 `ep.md` 與 `references/review-muse.json`。僅核 F1–F6 修訂是否解決原問題及有無新直接矛盾；需要時精讀先前 findings 所指 source。不要重讀當日報告、不要審 AIR-91/AIR-96、不要跑 tests。
輸出六列：finding ID／resolved 或 unresolved／實際 EP 錨點／理由；有新 Important 必附反例。你只有 findings authority，不能批准實作或改 accepted 狀態。
全程 read-only，禁止寫檔、git checkout/switch/config/add/commit、部署、改卡、memory 寫入或跨 repo 修改。檢查完直接返回，不 spawn、不代實作。
