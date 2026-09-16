# delegate-bridge 修訂工單：agent wrapper 層退役（跨 repo 工單）

> 來源：ai-rules AIR-50 EP S8（arch-thinking 三視角結論，EP 進度節 09-09 分析）。
> 本檔是交 delegate-bridge repo（`~/Github/delegate-bridge`，獨立 repo）的修訂工單——ai-rules 側不跨 repo 寫入，落地由 bridge 側執行。本弧外驗收：plugin agent 清單不再出現 delegate-rescue。

## 架構結論（已決策，勿重辯）

bridge CLI 本身無錯（ledger 必經正確）——錯在 plugin 附帶的 `delegate-rescue` thin wrapper：adapter-over-adapter（bridge CLI 之上再包 subagent，process babysitting 是 infra 職責，零 domain 邏輯純轉發）／幽靈 context（有邊界無職責，名稱錯誤 friction 實證）／存在即官方感（工具強化慣例第三層）。wrapper 唯一「價值」是被誤判的 600s timeout 約束（run_in_background 從頭可用，856s／442s 實證）。

## ① `delegate-rescue` agent 退役

- 定義移除或標 deprecated＋遷移說明：背景 Bash 直呼形態（caller `run_in_background`＋stdout 重導，主 session 直跑 bridge task 長命令）。
- 退役前掃 plugin 內殘留引用（收法「簡單轉發」類措辭、transport 恢復分支以 wrapper 為主體的表述）同步改寫，不得擔任現行恢復程序。

## ② docs 明示承載形態

- bridge repo docs 明示：外部 runtime 委派的承載者＝caller harness 背景 process 機制（caller 背景 Bash process），禁 subagent wrapper 承載——外部 runtime 不佔 in-harness agent slot／rate limit。
- 措辭與 ai-rules model-routing S5 承載者條款同詞對齊。

## ③ `--session-id` resume 鏈形態記載

- 記載 resume 鏈形態：review 工單預告驗證式 → judge → 修正 → `--session-id` 同 session followup（reviewer 帶自己 findings context 複驗，只餘 delta）。
- 實證：MOS-74（review→judge→修正→同 session resume followup 收斂）＋AIR-46（`--session-id` resume followup 一輪收斂、零殘留——resume 經濟學）；session id 取自 runs／show footer。
