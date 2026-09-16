# 快照：codex-opinion 第 2 點（Segment 0 順序——runtime validation 先於 architecture freeze）

> 來源：`.agent-tmp/guides-refactoring/codex-opinion.md` 第 2 點逐字快照（`.agent-tmp` 為暫存區會清，本快照為唯一持久源）。
> 快照日：2026-09-16（guides-refactoring EP S2 開工前置）。

---

2. **順序：runtime validation 放 EP 的 Segment 0，但必須在 EP architecture freeze 前跑完。**  
   這正符合你們現行 execution-plan 的 Segment 0 用法：先收 decision-changing evidence，再凍結後續設計。也就是可以先寫 EP skeleton，但 `muse approve` 三斷言、Write/Edit replay、NotebookEdit 實際路徑、reconcile chain 結果尚未回來前，不應把後面的防線形態寫成「已決策」。
   
   memory 這條我建議順序是：
   
   **cutover snapshot → 關閉／隔離新污染來源 → 補 forward guard → 再做存量處置 → 最後 reconcile acceptance。**
   
   因此「後綴擋」不應等待池內 86 條（或 cutover 時實際數量）處置完才做；方向相反。先讓池不再形成 moving target，再清 stock。更精確地說，suffix deny 只能擋一類 state pollution，所以若 staging/cutover 能先完成，應先做更上游的 containment，再補 suffix invariant。存量清理則排後。
   
   AIR-100 現有 notes 已經出現 41→78 這種基線成長；這本身就證明「先清後堵」會把 inventory count 變成追逐中的數字。
