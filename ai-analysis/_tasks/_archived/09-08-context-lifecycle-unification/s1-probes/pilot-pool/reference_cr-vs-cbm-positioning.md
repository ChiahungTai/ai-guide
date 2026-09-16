---
name: reference_cr-vs-cbm-positioning
description: cr vs CBM 定位定論（08-30）——cr=證據機器（A 軸機械驗證）、CBM=地圖機器（導航）；frontier 兩穩定點非互取代；問題＝哪類查詢路由到誰
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_b3591376-6323-4b4d-a172-744a5f37afa0
---

2026-08-30 深度對比定論（user 問「深度思考 cr 跟 cb memory 差異」）：

**身份定位**：cr＝**證據機器**（evidence machine）——存在理由是 AI 同寫 code 與 claim 需要獨立機械證據（refs truth、deletability、EP-claimed vs actual drift），對應 acceptance-evidence 框架的 A 軸；CBM＝**地圖機器**（map machine）——存在理由是 LLM 缺 whole picture、需要便宜廣覆蓋的導航地圖（探索替代、token 節省）。兩者架構差異全部由這個存在理由分化衍生。

**各軸差異**：精度（引擎級＋`[SRC]` provenance＋freshness 紀律，服務有後果的決策 vs 近似解析＋zero-edge guarantee＋自評 benchmark，導航 90% 夠用）；覆蓋（窄而深 2 語言＝user 實際寫的 vs 廣而中 162 語法＋10 resolver）；架構（資料面分離：SCIP interchange→自有 graph.db→CLI/MCP 查詢面、producer 可替換，代價＝整合面 bins/slots/stamps vs 單體 pipeline 全編進一顆 binary，紅利＝零安裝）；信任模型（自家源碼＋byte-deterministic＋golden oracle parity vs 第三方 binary＋供應鏈紀律 SLSA-3/VirusTotal）；生命週期接線（dev-loop 原生：post-commit refresh／delta_tour／projection overlay vs session-loop 原生：watcher/daemon／跨 agent session 協調／incremental re-index）。

**第二層後果（為何是穩定點、非一個是另一個的劣化版）**：cr 追廣度（加 tree-sitter 近似層搶語言數）→ deletability 查詢跑在近似邊上＝拿不確定證據做不可逆決策——靜默腐敗的正是 cr 被建造來守護的那類決策；zero-edge guarantee 是好設計但混淆「無法解析」與「確定無引用」（對 negative claim 是兩回事）。CBM 追精度 → 需 per-language 真引擎＝162 語言廣度死＋零安裝承諾死（不可能內嵌 162 個編譯器）。「用誰取代誰」是範疇錯置；正確問題＝**哪類查詢路由到誰**。

**路由結論**：精確閘門（deletability／refs truth／EP 對帳）→ cr（C+Go 需要時：Go 加 scip-go 腿性價比最高；C symbol 層只在真需求出現才 spike scip-clang）。定位導航（instruction-init Module Boundaries、unfamiliar repo orientation）→ 三級：cr index 在場→cr；CBM 在場→CBM graph（C+Go repo 走這級）；否則 scan-project（py）／Explore。

架構詳情：[[reference_cbm-architecture-tree-sitter-hybrid-lsp]]；C+Go 語言腿評估與 resolution 成本規律：[[cr-live-faces-roadmap]]（語言面＋拆軸段）。
