---
name: consistency-gate-not-optional
description: /consistency 與 post-build 鏈必跑非 optional；self-report 不算 gate——自檢問句＝「Skill 這輪調用了嗎」，替代須明示、豁免權在 user
metadata:
  node_type: memory
  type: feedback
  originSessionId: fb113184-00fc-456e-bcaf-b9b092167852
---

docs-mode 收尾我把 `/consistency` 標「optional，manual rg 驗過就好」→ user：「現在跑啊，不然紀律很差」。經八次再犯收斂出本教訓。

> merged_from: feedback_chain-steps-formal-or-labeled.md (2026-08-31)

**Why**：正式 gate 是紀律/連貫的承載點；writer 自己的 manual rg／自評有 self-review bias，不構成 gate 的獨立性。user 視 formal gate 為完成定義的一部分，不是可選 stamp。**self-report 汙染家族**（八犯的共同根因）：收尾報告的格式可單獨生成（×4「報告長得像」≠「鏈被調用」）；自評可宣稱 gate 過（×3「自評冒充 gate」——補跑時 gate 真抓到自評漏看的 finding：新舊術語並存，逐 hunk 看不到、whole-document 視角才撞見＝writer bias 實物示範）；鏈的零件（drift 掃描＋部署 ×6；規格驗證命令重跑＋cmp ×7；GLM 獨立驗收）做得再全也不是鏈——「做了鏈的零件」≠「跑了鏈」。

**How to apply（最終版自檢問句，經 ×3→×4→×6 逐次修正）**：commit 前問「**Skill(post-build)／/consistency 這輪調用了嗎（本對話紀錄可指認的調用）**」——不是「報告出了嗎」、「審過了嗎」、「該做的動作我做了嗎」。收尾報告裡的 gate 結果只能引用實際調用的輸出，不得預寫；殘留掃描 rg 必須檢查 exit/輸出並**有 hit 時擋 commit**，不是印出來看看。

**完整規則**：
- **順序**：「覺得合理就改 → 改好跑 /consistency → 跑完 OK 才 /commit」——gate 在 fix 與 commit 之間，不可倒置。post-build 是多段鏈（triage→review→judge→fix→followup→docs 鏈→收尾報告），commit 在全部走完之後；「review 發生」≠「鏈走完」（×2 先 commit 補跑鏈）。
- **逐檔列舉義務**：每個變更 .md 都須 formal（或明示宣告的等價替代）——任何一檔漏＝鏈沒走完，部分跑＝沒跑（×4 skills 索引行漏 consistency）。
- **「輕」不是跳過理由**（×5/×8）：docs-only／docstring-only／單行修／收編別弧結算／補 commit 全照走鏈——變更輕重是 AI 自行分級，user 的紀律是每個 commit 前鏈走完；比例化體現在鏈內（弧模式 diff=baseline..HEAD；docstring-only 無實作邏輯可錯位時 single fresh-eyes 替代 dual-context 且理由明示），不在跳過鏈。md-only「鏈太重」也不成立——triage 表已把 md-only 導向輕量 docs 鏈，成本顧慮被機制吸收；ad-hoc 反而漏 commit skill formal 步驟（2.5 引用掃描／2.7 POC 掃描／attribution footer——實證漏 Co-Authored-By footer）。
- **替代標明**（chain-steps-formal-or-labeled 併入）：每步要嘛 formal 調用、要嘛收尾報告逐項標「替代方式＋為何等價」（consistency＝獨立 agent 六維度 ✅ 已標明 vs code-review docs mode＝機械掃描 ❌ 未標明）；**自創替代路徑先講再跑**，事後揭露＝延遲透明。
- **等價替代載體**：forked `/consistency` 撞 step-0 guard bug（把檔內容當 target→fail-fast）時，用獨立 agent（隔離 context、同六維度：自洽/矛盾/順序/自包含/精準度/SNR）＝user 接受——原則「gate 要跑，載體可換，別因工具 bug 卡住」。Skill tool args 必須是裸存在的 .md 路徑——自然語言描述（即使內含路徑）也觸發 fail-fast。
- **gate 範圍**：authored .md only；`crawl.py` 鏡像外部快照排除（對它跑六維＝範疇錯置，品質歸上游）。
- **被質疑時**：不爭辯各輪算不算——直接弧模式重跑（baseline..HEAD＋uncommitted），用調用紀錄對齊報告宣稱；已 commit 仍可補跑 formal 鏈（findings fix-forward，淨效果等同正序）。
- **豁免權在 user**：AI 判斷 trivial 可主動建議跳過（附一句理由），決定不自己拿；user 未表態一律走鏈。user 當場明示豁免（「不用吧，浪費token」）≠ AI 自行分級（×5）——兩者不矛盾，跳過權專屬 user。
- **累積編輯後的重跑維度**（09-05 AIR-29）：一個弧內累積多輪 user 建議修改（同日 ~15 項政策編輯）後，user 會主動要求**重跑收尾鏈確認整體流暢**（「剛剛改了許多建議，你應該重新跑 post-build，尤其 consistency」）——多輪增量各自綠 ≠ 跨輪自洽；重跑形態＝機械跨檔對帳（舊詞/標註/互指/殘留）＋逐檔 whole-document consistency，非只看本輪 diff。主動在「編輯批次收束點」自查是否該重跑，不等 user 點名。
- 🟡 finding 當下 fix-up commit，不「之後再修」——[[feedback_fix-immediately-not-defer]]；純 docs 直 commit 的結構洞（目前零閘門）與 2.5 擴條修法提案見 [[commit-finalization-gate]]。
- 技術副產品：markdown 表格欄數一致性檢查用管線符計數（`awk -F'|'`——awk 預設空白切分數的是文字不是表格欄）。

**八犯形態索引（一行例證，教訓已收上方規則）**：×1 標 optional 被令現跑；×2 先 commit 補跑鏈；×3 自評寫「六維過」冒充 gate；×4 照格式自寫收尾報告＋部分跑；×5 docs-only 當跳過理由；×6 做了鏈零件（drift 掃描＋部署）直接提案 commit；×7 GLM 獨立驗收≠post-build 鏈（補跑抓到真 🟡：規格命令全綠但 handoff 語義缺口）；×8 收編/單行修直奔 commit。
