---
name: inflow-needs-outflow
description: 記憶治理三原則：現值不記（A/B/C/D）＋寫入當下即蒸＋有進有出（流出腿）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_07836405-5f73-4d17-9619-5456406f7cd3
---

user 2026-09-03 原話「有進有出才是對的」：持續流入的面必配流出機制；寫入當下即蒸後形；會變的現值不記。

> merged_from: feedback_memory-no-drift-prone-snapshots, feedback_memory-write-distilled-at-write-time, 2026-09-07 cluster-merge wave

## 有進有出（original: feedback，keeper 本體）

治理設計裡**任何持續流入的面都必須搭配流出機制**——只設流入閘不設排水口＝積累成墳場。三場景同構：①memory 池（gate 是流入閘、夜間收斂 cron 是流出腿——放寬 gate 的前提是流出腿先建好）；②`_inbox` 任務進口（queue 無排水口必成墳場）；③暫存區（.agent-tmp/.at-contexts 只進不出）。**How**：設計「會進東西」的機制必答「排水口在哪——誰清、何時清、去哪（升級/歸檔/丟棄）」；無答案先補流出腿再談放寬。與 [[feedback_demand-pull-fails-silent-gaps]] 互補（彼量測、此流向）；實例見 [[gate-severity-solidification-queue]]。

## 現值不記（original: feedback，09-03「magic number 有意義嗎」）

audit 🟡多條是數字型（bundle 82→83KB、plist 六→九）——「修正數字」徒勞：改完瞬間又腐爛。**四類分界**：A 平台常數記（automation 上限 20、載入 200 行/25KB——變動本身即事件）；B 歷史事實記（sha、趨勢、「歷史：」前綴）；**C 現值快照不記**（現 bytes/數/卡數/版號——寫入即腐爛）；D 語義數字記（決策參數）。寫 memory 遇數字先問「明天會變嗎」——會→換一行查法或刪值留趨勢。cron prompt 版：只寫動態讀命令，連「參考現值」括號都不附。同原則他載體：[[feedback_rules-no-project-specific-facts]]、[[feedback-magnitude-over-precise-counts]]。

## 寫入當下即蒸（original: feedback，09-06 拍板治流入閘）

user 糾正「每次這樣壓也不是辦法」→「寫進 memory 就要精簡，不要寫一堆廢話後來再 audit」：廢話主入口＝弧結案敘事（timeline/commit 清單/findings 計數蒸掉四五成零損失；滿 context 自蒸品質必差）。**How**：寫前一句話測試（提煉不出核心事實＝不寫）；lesson-first＋實證錨一行，禁 timeline/in-flight（住 EP/卡）；**未定案歸因不入**（user「確定的東西再放」——memory 無信心欄位，recall 即事實；已確認的 gap 本身可寫）；機械閘新建 >3,000 硬擋；滿 context 結案改派 mem-distill 隔離蒸餾。
