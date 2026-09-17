---
name: model-runtime-entitlements
description: fixture——availability_snapshot 測試樣本（自真 spine 摘錄改編，AIR-123；非真實現值）
---

# model-runtime-entitlements（fixture）

**as-of 2026-09-16**（user 對帳）。本條會腐爛：過時以 provider dashboard／實際錯誤訊息為準，禁從本條歷史推定；查不到＝視同未知，先探測再派。

- **可用**：GLM（5.3 主力＋5.3-flash）＋muse＋codex 三家
- **GLM**：legacy v1 方案；訂閱至 2027-02-04；Models 與 Vision MCP 共用額度池；GLM-5.3-Flash 消耗≈5.3 的 0.4×（有額度時機械腿首選）
- **muse**：coding plan Power 等級；消耗比 GLM 快——定位偏向 review 腿
- **codex**：ChatGPT 帳號載體——**兩池是不同載體，派工前必分清**：web codex＝chatgpt-web/*（webgpt 瀏覽器傳輸）；native codex＝API 池（server 端現況拒派）；native 池的 usage-limit 訊號（exec approval 層）**不代表 web 池耗盡**——同 job 模型回應照常走完、同日重派成功（AIR-123 兩池回歸 AC fixture 樣本，句尾保留以驗證 note 不截斷）
- **Anthropic／xai**：未訂閱，禁派
- **額度事件（09-16 16:0x）**：in-harness flash spawn agent 撞 1308（5h 窗耗盡）——reset 前禁派 GLM 系（含 flash）（fixture 衝突態樣本：可用行列 GLM 但歷史事件行禁派——機械輸出須顯性並列，判斷歸 LLM）
- **額度事件（09-16 18:0x 續）**：user 實測 usage 已回滿——GLM 系恢復可用，回歸常態路由
- **能力序裁定（額度事件歸檔形態樣本，F1）**：gpt-6-astra 與 fabel 能力強於 gpt-5.6-sol／GLM-5.3——family 表未列二者＝帳號面不可達，非能力否認（fixture 並列複核樣本：含 family 名但無限制詞共現）
