---
name: full-arc-delivery-vehicle-immediately
description: user 預期「處理這件事」＝設計到落地一弧做完——衍生工作收案時當場建載體（卡/EP），禁懸空「後續卡說一聲」
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_7622de15-8cf2-4fc5-a0b2-49b7f5f19f0b
---

2026-09-03 AIR-14 收案後 user 連三問：「所以是已經 build 好？」→「L1-L9 的實際手術還沒做…我以為你是會將所有都做好」→「我預期是在 air 14 做誒，這有 EP 了嗎？有的話 Muse agent 去做」。

**Why**：user 的弧心智模型＝一張卡＝一件事完整做完（設計＋落地執行）。卡驗收字面寫「文檔化落地清單」雖可結案，但留「之後開後續卡時說一聲」的口頭懸空承諾，在自家治理模型裡正是「未承諾」狀態（規格有、載體無）——自己設計的 draft↔card 分界，第一個違反者是自己。user 被迫追問「沒有 execution-plan 要怎樣進行」＝流程載體斷點被當場抓包。

**How to apply**：①收案時若還有衍生執行工作：**當場建卡（desc 過 gate 三必有）或落 draft**，不說「要開卡時說一聲」；②user 說「處理這件事／做好」默認 scope 含落地執行——不確定就問「設計定案就好，還是含手術落地？」；③被點名載體缺失時立即補鏈（AIR-18 教訓：卡＋EP＋雙 ref 十餘分鐘可齊，且 user 會直接指定執行者「Muse agent 去做」）；④設計卡的驗收句從源頭寫清交付邊界（「文檔化規格」vs「含落地」），避免字面合規、預期落差的兩種讀法；⑤**跨 repo 變體（同日鑑識實例）**：經授權改了別的 repo（服務 script 等活設施）→ 該 repo 內 scoped commit 立即收掉，「留給對方下次 batch」＝做一半就跑（user：「你做一半就跑了？」）——但 scoped commit 必先 `git diff --cached --name-only` 對帳（他人 staged 批在場，見 [[verify-wt-before-commit]] 跨 repo 段）；⑥**等待條件型衍生工作**（09-05 實證）：user 說「現在處理」但觸發條件未到（目標弧進行中、保護規則禁止現在動）→ 機械驗條件＋當場建 draft 載體＋指針釘在觸發條件正下方（pending-decisions 對應條目下）——這樣才是「處理完成」而不自破規則；⑦**EP「後續項」段不算載體（09-08 實證）**：弧結案把衍生工作只登記在 done/ EP 後續項段＝archive 後不可見的懸空變體——user 質問「為何不接著處理」後才補卡（AIR-44）；正解＝結案時同步建卡/draft，小到能當場修的（如 flag 表 drift）直接修掉不留登記。相關：[[feedback_fix-immediately-not-defer]]、[[backlog-md-integration-eval]]。
