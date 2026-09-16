# ai-rules 反饋佇列（mosaic session 產出，待 ai-rules session 固化）

## ① model-routing skill「bridge 段」——直跑範式＋resume 鏈（2026-09-09 MOS-74 全弧驗證）

**事實**：bridge task 直跑完全可行且嚴格更優——主 session `run_in_background` 跑 `node muse-bridge.mjs task …`（背景 Bash 無 timeout 上限；856s/442s 實證）＋stdout 重導檔案直接 Read。舊「spawn agent 轉發」形態的 timeout 約束**從未真正存在**（run_in_background 一直可用）；轉發層製造的「兩段式收法」（agent exec id ≠ bridge job id 的 ledger 考古）整條是多餘間接層。

**建議 patch 方向**：bridge 操作段改寫為直跑範式；刪「spawn prompt 給絕對路徑」等轉發形態操作知識；補「`--session-id <id>` resume（sessionId 從 `runs --json`/`show --json` footer 取）」。

**resume 鏈形態（新審查工作流，值得獨立記載）**：
```
muse review（bridge task；工單預告「findings 每條附可機械複驗的驗證式」）
→ 主 session judge（逐條 ✅/❌/⚠️）
→ 修正
→ muse resume 同 session（--session-id）followup：帶自己 findings context 逐條複驗＋檢查修正新引入問題
```
MOS-74 實證：review 6 findings → followup pass 6/6 verified＋2 條新 issue（N-1 stale 錨/N-2 info）。優點：followup 工單零背景重複（reviewer 記得自己 findings）；驗證式直接回收複用；reviewer 對自己 findings 的修正驗證比 fresh context 更準。

**工單範本要素固化**：「findings 須可機械複驗——每條附 rg/pytest 驗證式」應成為 external reviewer 工單的標準要求（本次是 followup 零摩擦的關鍵）。

## ② tool-discipline rule——「長命令背景跑是預設」通則＋反模式案例

**反模式案例（三層歸因，可作 rules 的真實案例 marker）**：
1. 誤判約束：以為 Bash 只能 600s（實際 run_in_background 從頭可用）
2. 解法固化：為繞（誤判的）約束產生 agent 轉發形態，沉澱進 memory 活配方
3. 工具強化慣例：delegate-rescue「thin forwarding wrapper」agent 的存在讓形態顯得官方
→ 成本：agent 開銷＋兩段式收法間接層＋收斂路徑變長；無人回頭問「原約束還在嗎」

**建議 patch 方向**：tool-discipline「背景執行」段補通則——「長命令（>10 分）背景跑是預設；spawn agent 不是繞 Bash timeout 的手段（它從不是必要手段）」＋上述案例。

## ③ code-review skill / review-engine——external reviewer 的 Finding 格式契約

跨家族 reviewer（muse）的 findings 加「驗證式」欄（verification formula：rg 命令/pytest case——修正後可機械複驗）。現有 Finding Record（id/severity/file:line/問題/建議）可加一欄；本地 reviewer agent 也可比照（提升 followup 機械性）。

## ④ code-reality——tour_validate 中文目錄掃描 bug（2026-09-08 登記重申）

`code-reality tour_validate --manifest --repo .` 報「有 corpus 目錄但零 .tour 匹配」——實際 .tour 存在（fd 可見）；`--tours-dir .tours/arch` 顯式亦炸。疑似中文目錄名掃描問題（`01-資料讀取三路徑/01.tour`）。mosaic callstack 錨本次靠手修繞過。
