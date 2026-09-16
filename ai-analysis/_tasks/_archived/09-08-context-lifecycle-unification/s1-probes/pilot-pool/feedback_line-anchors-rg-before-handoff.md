---
name: line-anchors-rg-before-handoff
description: 行號/路徑錨點跨邊界給出（relay/handoff）前當場查證源 repo——行號 rg 核對、暫存材料重跑；錯值死路徑會被下游複製傳播
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_f3e9fd1c-fa00-48bd-9e00-fb93c4bd4093
---

2026-08-24 mosaic 驗收回報：M3 relay 給的 `evidence` 行號錯（conditions discovery.py 實際 :149、我給 :186；features 正確值 `features/discovery.py:206` 且未附）。錯值源頭是 M3 弧寫進 test fixture 的字串，未查證就複製：**test fixture → SKILL.md 範例 → relay prompt → mosaic profile 三跳傳播**，下游 rg 實測才抓到。同日已修六處（`discovery.py:186`→`:149`）並 commit `9244bb1`。

**Why**：行號是 drift-prone 錨（上游加減行即失效）；寫入 fixture/範例/relay 的行號會被後續 session 當「已驗證事實」複製——錯誤傳播半徑遠大於當下寫入成本。第一實例＝61974f0 教訓（EP 歸檔引用程式碼位置行號全落錯，改 symbol 錨）。

**How to apply**：給出帶行號的片段（profile evidence、relay prompt、歸檔文檔、commit message 引用）前，**當場 `rg -n` 源 repo 查證**該行仍指向宣稱的 symbol；能寫 symbol 錨（`discovery.py:auto_register_conditions`）就不寫行號。與 [[relay-claims-verify-current-state]] 同族（接收宣稱先驗證），此條是給出端義務。

**第二實例（08-30，行號來源＝工具回報的新形態）**：T2-3 白名單驗證引用 refs 回傳的 `check_broken_refs` DEF `:135`——那是 08-29 stale index 快照，檔案 08-30 重排後現況 `:154`（差 19 行）；`[SRC]` provenance 標查詢當下 HEAD，造成「新鮮」錯覺。**教訓擴展**：行號來源不只人工記憶/fixture——index 查詢工具的回報本身也是快照，工具行號進 relay/handoff/文檔前同樣當場 rg。

**第三實例（09-05，跨日重貼 handoff 前驗材料存活）**：要重貼含重現材料的 handoff（`.agent-tmp/dogfood-projection/`），材料已被夜間清淤掃掉（.agent-tmp 7 天線，08-30→09-05 恰過期）——handoff 引用的檔案路徑與行號同族，都是會死的錨。**How**：跨日重貼 handoff／relay 前，先 `ls` 引用的暫存路徑＋（若為重現步驟）實跑一次——這次重跑還順帶發現縫已被 CR 端修掉（handoff 本體失效），省掉無效派發。
