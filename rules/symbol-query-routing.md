---
harness-scope: neutral
---

# 符號／型別查詢路由（code-reality 優先）

## 核心原則（cr-first 路由）

搜尋前分清符號/引用/呼叫鏈與字串/config：符號優先 code-reality（refs/callers/closure，核對 [SRC] provenance/stale），型別走 code-reality-lsp-bridge hover/check_file（缺場退 LSP），文字 rg、檔案 fd；即時 working-tree 回饋用 LSP——index 是 build-time，編輯後須重 harvest。載體對照、staleness 處置、rg 反例群見 symbol-query-routing skill。

## 任務啟動 gate（符號查詢任務強制）

涉及依賴/引用/fan-in/消費者/呼叫鏈/跨域/context/_private/邊界/循環/反向耦合/簽名/型別/定義/實作查詢，**第一步確認 cr 在場**（MCP 或 `.code-reality/graph.db`；detect 見 cr-query skill）；禁用 which/timeout shell proxy 探測。純 Read 理解、demo、log 不觸發。

## fallback 與 zero-hit 紀律

index 缺/過期且不可重建→LSP；LSP 亦缺才 rg；工單工具/唯讀限制優先。降級須標「未 index 驗證」，**禁把未查到斷言為不存在**——rg 會漏符號/local import（反例見 skill），引用可疑少先查 index/workspace 新鮮度。
