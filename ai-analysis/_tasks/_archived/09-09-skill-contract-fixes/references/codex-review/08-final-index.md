# 最終索引與可信邊界

本輪完成：六個 skill 的逐項架構審查、arch-thinking 必要性觀察、跨鏈建議與評價。基準 ac6cccf50299637ff9587559d166834cf33e8b7d。沒有修改被審查的 skills/rules，沒有建卡或 commit；最終 git diff --exit-code = 0。所有本輪產物在本目錄（.agent-tmp 為暫存區，受既有清理政策管理）。

## 閱讀順序

- [07 必要性、整體架構與評價](07-necessity-and-architecture.md)：優先閱讀的合成結論。
- [01 spec](01-spec.md)：需求邊界保存與 optional 取捨。
- [02 execution-plan](02-execution-plan.md)：EP1 invariant 分流漏洞、EP2 邊界交接。
- [03 implement](03-implement.md)：IM1 refactor 同步、IM2 consent owner、IM3 shared/isolated 前置混淆。
- [04 code-review](04-code-review.md)：CR1 任務弧範圍、CR2 snapshot 身份。
- [05 judge-review](05-judge-review.md)：JR1 決策帳本、JR2 裁決/實作措辭。
- [06 post-build](06-post-build.md)：PB1 docs 跳審、PB2 resume 新鮮度、PB3 完成時點、PB4 證據失效。
- [00 範圍與初始拓樸](00-scope.md)：保留初始中間觀察，完成狀態以本檔為準。

## 優先修正的根因群

1. **交接身份與新鮮度**：JR1 + PB2 + CR1 + CR2。一次解析 task/scope/artifact/reviewed identity，避免下游重猜。
2. **完成狀態 ownership**：PB3 + IM2。完成條件與授權判斷各有唯一 owner。
3. **分流維度錯接**：PB1 + IM1 + EP1。載體副檔名、是否新增 UC、是否要完整 EP，都不能代替行為/結構/invariant 風險。
4. **執行環境與流程重複**：IM3 與 review 去重建議。先辨 shared/isolated，再定 dependency transfer；已有效的 review 證據不要因命令換名就失效。

## 方法論限制

- 證據是目前工作樹 Markdown 的原文、行號、producer/consumer 對照；confirmed 指「契約矛盾已核實」，不是已實證每個 harness 必定出錯。
- 未啟動被審 skills 的 build/review mutation 流程、未實跑多 harness 端到端、未量測 review 的獨有 finding 收益或 token 成本。
- 本輪為主 session 文件審查，未取得另一 reviewer 的獨立驗收。未把被審查的 code-review 命令當成空 diff 任務執行，也未聲稱完成其 dual-context 協議。
- 沒有把所有文件互引視為架構循環；報告只追實際決策/狀態/產物 ownership。沒有要求強制 DDD 四層程式結構。
- checkpoint 的最小反例是依指令路徑推導的反例，不是 runtime 實驗日誌。修正後仍須用 07 所列辨識性場景驗收。

最終評價：保留能力與入口，收斂流程權責；先修交接，後做減法。暫不接受「完整跑鏈即可保證可接續、可自動宣告完成」的架構宣稱。
