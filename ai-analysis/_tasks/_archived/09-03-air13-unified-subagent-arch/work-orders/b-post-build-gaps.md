# 工單：post-build 四通用缺口補入（WO-4／EP S5-B）

> 定位：把 mosaic 治理觀察提煉的四條通用缺口補進 skills/post-build/SKILL.md。

## 紅線（違反＝失敗）

- 禁 `git add`／`commit`／`push`／改任何 backlog 卡
- 只准動 `skills/post-build/SKILL.md` 一檔
- 禁 /tmp 落檔；新增內容禁版本號／日期／統計；禁 model id 入文

## 目標（一句話）

在 post-build skill 補四條通用缺口：額度降級措辭鐵律／增量≥3 檔補審／階段 0 背景寫入者前置／並行線排除明列。

## Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`；base `63f2041`；working tree 已有 WO-1/WO-2/WO-3 未 commit 修改（既有狀態，非衝突）

## 必讀（按序）

1. `/Users/ctai/Github/ai-rules/skills/post-build/SKILL.md` 全文——特別是收尾鏈編排（code-review → judge → 修正迴圈 → consistency → metadata-sync）、階段 0（掃描分诊）、審查升級（dual-context ≥3 files）段
2. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-03-air13-unified-subagent-arch/ep.md`——S5 段修改要點 3

## 已決策（勿重辯）＋矛盾例外

四條語義方向（各一句、落點跟隨 post-build 既有結構，不新開大節）：

1. **額度降級措辭鐵律**：dual-family 第二審查者（如 muse review）因訂閱窗口／額度不足而跳過時，**必須顯式記錄降級**（「額度降級：X 跳過，原因＝…」進收尾報告），禁靜默略過——與「主動揭露錯誤（Fail Loud）」同族
2. **增量≥3 檔補審**：修正迴圈或收尾期間 diff 增量擴大至多檔（≥3）時，補一輪審查視角（不需全鏈重跑，但不得零審）——與既有 dual-context ≥3 files 升級條款對齊（先讀現況條款位置，語義銜接勿重複）
3. **階段 0 背景寫入者前置**：收尾鏈開跑前，先盤點在場背景寫入者（背景 agent／bridge job／排程任務）——有在跑的寫入者先收或明確排除，避免收尾掃描吃到進行中寫入的中間態
4. **並行線排除明列**：收尾掃描（rg 殘留／consistency 範圍）必須明列並行 session 改動的排除清單（非本弧的 working tree 變更不納入、不順手修）——引用 collaboration-constraints 並行原則，不重述

**矛盾例外**：任一條在現況已有等效條款（rg 驗證），該條標 no-op 附行號，勿重加。

## 範圍限定

- 動：`skills/post-build/SKILL.md`
- 不動：其他一切

## 工具接線

- bash（cat/rg）；禁 CR 寫入面；禁 /tmp

## 驗收（命令＋預期，逐條實跑）

1. `rg -n "額度降級" skills/post-build/SKILL.md` → 命中（條 1）
2. `rg -n "3 檔|≥3" skills/post-build/SKILL.md` → 新句命中（條 2；區分既有 dual-context 條款）
3. `rg -n "背景寫入者" skills/post-build/SKILL.md` → 命中（條 3）
4. `rg -n "並行" skills/post-build/SKILL.md` → 新句命中（條 4；現況已有並行相關句則確認語義分工）
5. 結構檢查：四句各落 post-build 既有段落（階段 0／修正迴圈／收尾報告），無新開懸空小節——報告附各句 file:line 與所在段落名
6. 負向：`rg -n "muse-spark|gpt-|glm-" skills/post-build/SKILL.md` → 零命中

## 證據紀律＋PII 禁令

每條驗收附完整命令與原始輸出；`git diff --name-only` 佐證範圍（僅 1 檔＋宣告過的既有改動）；報告禁 PII。

## 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單 2. 四條逐項說明（file:line＋所在段落＋與既有條款銜接）3. 驗收 1-6 原始輸出 4. 偏差記錄（含 no-op 判定）5. 未驗證項 6. 建議 reviewer 聚焦點
