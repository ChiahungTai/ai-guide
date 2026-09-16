# 快照：M-D「Runtime validation 建議清單」節（九條）

> 來源：`.agent-tmp/guides-refactoring/m-d-output.md`「Runtime validation 建議清單（未執行）」節逐字快照（`.agent-tmp` 為暫存區會清，本快照為唯一持久源）。
> 快照日：2026-09-16（guides-refactoring EP S2 開工前置）。
> 原文性質聲明（自源檔）：以下來自 static wiring＋文件證據，未執行任何 runtime 驗證。

---

1. **CC/ZCode 主 session Write 重放**：generator 池內新建條目故意 desc＞100 chars，預期 exit 2；同測 hash／日期／`sess_`／新建＞3K／膨脹＞12K 各一例＋收斂方向放行一例。用後即清測試檔。
2. **NotebookEdit 缺口確認**：同條件以 NotebookEdit 寫入，確認直通或 dead-matcher（需觀測區分）。
3. **Subagent 負對照**：受控 subagent 對池 scratch 檔 Write，查 hook log 無記錄且寫入落地。
4. **muse 閘現況三斷言**：`muse plugins inspect <id> --json` assert `trusted_enabled`；governed repo `add_memory` smoke 預期 deny＋inbox receipt；marker 改壞後預期 deny。任一不過即 row 8 由 unknown 轉 gap。
5. **Teardown 偵測鏈驗證**：先手放檔模擬直寫驗 reconcile exit 2；再跑真 muse session-end 重放驗觸發。
6. **後綴擋可驗性前置**：任何 writer 級驗證前，先以 rg 定位 suffix-RE＋單元測試存在性——目前錨不存在＝無驗證可跑。
7. **Codex 面**：查 codex session rollout 有無池路徑寫入實例；長期以 reconcile clean 趨勢＋telemetry 盲區聲明監控。
8. **Consolidation 轉寫路徑稽核**：抽查 inbox→pool 消費，確認轉寫確由 CC/ZCode 主 session tool 發起。
9. **Approve 漂移監控**：每次 `muse plugins update` 後重跑第 4 項。
