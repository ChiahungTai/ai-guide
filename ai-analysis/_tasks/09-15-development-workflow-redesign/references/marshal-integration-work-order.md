# Marshal overhead 增補：有界調查與計畫審查

user 明示派 Muse 調查；只做規劃，新流程將交其他 LLM 實作。HTML 互動/視覺驗證不做。repo `/Users/ctai/Github/ai-guide`。

你是 Reviewer，authority=findings，judgment_floor=decision，qualification=review_findings。禁止再委派、寫檔、memory 寫入、git checkout/switch/config/add/commit、測試或部署；只讀，返回證據與建議。主 session 負責裁決與落盤。若中途受限，直接返回已查/未查，不假報完成。

必讀：
- `ai-analysis/reports/2026-09-15-marshal-workflow-overhead-decisions.md`
- `ai-analysis/_tasks/09-15-development-workflow-redesign/ep.md`（重點 S1/S2/S4、scope、manifest）
- `skills/model-routing/SKILL.md` doctrine/schema/allow-list/dispatch policy（目前 dirty 為其他弧，不能改）；`skills/agent-workflow/SKILL.md` 相關 work-unit/派工段；`agents/AGENTS.md` lifecycle 契約
- 用 rg 定位 review-engine、post-build、execution-plan、implement 的直接 consumer 條款後分段讀。不要重讀七份背景報告，不重審已 resolved 六項。

回答：
1. 相容 work units 同一 context／同一 worker 承接，在現行 authority/qualification/independence 下哪些合法、哪些不可？不要只憑 Role 名稱推論。找出會讓 Reviewer 自裁、自驗、作者假獨立的反例。
2. 同 scope/read-set 工單批次化，需要新增什麼最小契約？是否只是 workflow adapter 編排就能完成，還是必須改 model-routing/供給 schema？請選可維持既有 doctrine 且不碰 AIR-96 dirty 的方案；若做不到明說。
3. 省重讀与每次 dispatch availability/freshness 如何共存？區分同 context 已讀與新 worker 沒讀，不能發明 TTL、cache 服務或假設 transport resume 支援。
4. 哪些 overhead 判斷有真實來源、哪些只是推測？零 findings 的快道已存在，不再當改革；提出最小可交其他 LLM 實作的 EP 插入點與驗收反例。

輸出一份精簡整合矩陣：提案/成立或限制/來源 path:line/精確落點/反例與驗收。再列最多四個 Important findings。不要重述整個 EP；找不到即未驗證。執行全文是 report 分析，不新增 production 政策。
