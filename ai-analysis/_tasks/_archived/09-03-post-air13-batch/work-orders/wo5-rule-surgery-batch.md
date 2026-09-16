# 工單：後議規則手術批（11 個落點，WO-5）

> 定位：AIR-13 後議三項 user 裁定結果落地——mosaic 提煉的 8 條方法論＋擇要 3 條＋codex 現況 2 行，全部最小化手術（多為一句到一小節）。

## 紅線（違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡
- 只准動「範圍限定」列出的 9 個檔案
- 禁 /tmp 落檔；新增內容禁版本號／日期／統計數字；**禁 model id 入 rule/registry 層**（skills/model-routing/SKILL.md 解析表除外）
- **bundle 預算緊（93% of 90KiB gate）**——rule 檔（must-execute/modern-cli/tool-discipline/model-routing）每條壓到 1-3 行；skill 檔不限行數但忌冗

## 目標（一句話）

把 12 個已裁定項落進 9 檔：7 條方法論（四律2/4＋九律2/5/6/8/9）＋擇要 3 條（背景長跑/git pathspec/Edit 邊界）＋codex 現況 2 行。

## Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`；HEAD 越過 `2a6f018`（查 `git log --oneline -3` 記錄實際值入報告）；working tree 可能有本弧卡修改（AIR-19，staged）與任務家 untracked——既有狀態非衝突

## 必讀（按序）

1. 各目標檔的目標段落（下方逐項已附定位提示；動筆前 rg 驗證現況）
2. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/_archived/09-03-air13-unified-subagent-arch/ep.md` 只讀「核心原則」段（family/profile-only 紀律）

## 已決策（勿重辯）＋矛盾例外

逐項規格（**每項動筆前先 rg 現況——已有等效內容則該項標 no-op 附行號，勿重加**）：

1. **execution-plan skill（四律2 dogfood 循環——預期大部分 no-op）**：查證 `skills/execution-plan/SKILL.md` 段落 0「致命先驗」與驗證策略「前期 POC」、`skills/implement/SKILL.md`「POC → RED 測試銜接」——若已承載 dogfood 前兩腿（EP 邊寫邊 POC、implement POC 起工素材）則標 no-op 附行號；**確定缺的第三腿補入 `skills/post-build/SKILL.md`**（階段 1 附近一句）：「新工具／新流程的首個真實消費者＝自己的 build 弧——消費對照寫進收尾報告（工具驗收與弧審查合同一件事，不另造驗收場景）」
2. **rules/must-execute-before-complete.md（四律4 POC 清理判準）**：「POC 暫時性」段補一句（1-2 行）：「清理判準＝知識固化任一成立且完備即刪（test docstring 引用／EP 結論收編／量測文件收編數字）；量測型（測外部世界非 library 行為）固化後直接刪，test 轉移非必要」
3. **execution-plan skill（九律2 規劃假設標註）**：段落 0「風險假設識別」補一條：「框架行為 bug（渲染／race／client-server 狀態同步）的根因假設常錯——規劃層禁寫死修法，根因標『推測，需 L4/POC 驗證』、修法段標『待確認根因』（純邏輯 bug 才可規劃層寫死）」
4. **skills/acceptance-evidence/SKILL.md（九律5 全量對帳）**：併入既有盤點/抽樣家族（先 rg「盤點執行點雙掃」附近）補一節或一段：「抽樣結論寫母體假設前自問『樣本怎麼選的？選擇機制會不會正好偏一邊？』；主儲存／退役／範圍類設計判斷先全量機械對帳，不靠抽樣推廣（實例：3 檔樣本恰是全市場僅有的例外擁有者）；user 對系統行為的歷史印象值得查 log 基線（AI 的『一直以來都這樣』常只看近窗）」
5. **skills/implement/SKILL.md（九律6 誠實盤點）**：階段 6 完成報告補 2-3 行：「效能／成本宣稱分列『上界估計』vs『現行實測』（沒跑過的路徑不得當現況宣稱）；工具／流程投資附退役地圖（取代了什麼、哪些變便宜）；『無優勢』也是要報的結果」
6. **skills/arch-thinking/SKILL.md（九律8 先查既有）**：補一段：「設計任何注入／fallback／provider／reader 機制前，查證廣度＝定義處＋消費端慣例＋模組 AGENTS.md 設計宣稱三查——先查既有同類 reader 與注入先例，只查定義處會精確繞過既有介面（LLM 傾向自命發明新機制）」
7. **skills/debugging-and-error-recovery/SKILL.md（九律9 debug 先證據）**：補一段：「圖表／視覺化 mismatch 第一步 print 各資料源實際範圍（series 日期 min/max＋count 對比視窗），勿推理——視覺 bug 常藏在 filter 不一致；runtime bug（UI 沒反應）先讀 log 再理論——handler 從未觸發≠被打斷，log 是辨識證據；exit 0≠圖對（視覺交付物需肉眼驗）」
8. **debugging skill（擇要 A 背景長跑 pipe 失明）**：補一段：「背景長跑命令禁尾端 pipe（`cmd | tail`）——pipe 讓輸出只在命令結束時出現，數十分鐘期間零可見性；改『重導檔案＋輪詢讀』（`cmd > out.log 2>&1`＋定期讀）；追進度優先產物側訊號（目錄檔數增長／progress json），非 stdout。與 tool-discipline『閘門禁 pipe』不同切面：那是 exit code、這是可見性」
9. **rules/modern-cli-preference.md（擇要 B git pathspec，壓 2-3 行）**：陷阱家族補：「git pathspec 命令（ls-files/log/status/diff）一律從 repo root 跑——目錄內部執行會 CWD-relative 解析成巢狀不存在路徑**靜默回空**（誤判 untracked／無歷史）；staging 已消失目錄的刪除，pathspec 禁 trailing slash（`dir` 可 stage、`dir/` fatal）；`fatal` 短路 `&&` 鏈但 `;` 段照跑——批次 staging 後必看 `git diff --cached --stat` 勿信命令鏈跑完」
10. **rules/tool-discipline.md（擇要 C Edit 邊界，壓 2-3 行）**：「檔案修改禁令」段補：「共享檔案（多 session 並行寫入）Edit 前先 rg 定位自己行的唯一錨點——old_string 誤包他人 session 的行＝靜默刪除他人內容（搬移拆兩個精準 Edit、編後重讀對照行數）；old_string 連續兩次 not found＝context 渲染與實際 bytes 有出入——改以 python repr 讀目標行重組，禁第三盲重試」
11. **codex 現況 2 行（D）**：`rules/model-routing.md` family 表 codex 行備註「環境診斷與救援」→「ad-hoc 選項（想到再用、低頻）；context 小＋消耗快禁大工單」；`skills/model-routing/SKILL.md` 解析表 codex 行備註同步同一語義（可略展開，不改 model/effort 欄）

**矛盾例外**：任一項發現現況已有等效條款（rg 證據）→ 該項 no-op 附行號；發現規格與檔案結構具體衝突 → 停下舉證。

## 範圍限定

- 動：`skills/execution-plan/SKILL.md`、`skills/implement/SKILL.md`、`skills/post-build/SKILL.md`、`rules/must-execute-before-complete.md`、`skills/acceptance-evidence/SKILL.md`、`skills/arch-thinking/SKILL.md`、`skills/debugging-and-error-recovery/SKILL.md`、`rules/modern-cli-preference.md`、`rules/tool-discipline.md`、`rules/model-routing.md`、`skills/model-routing/SKILL.md`（11 檔）
- 不動：其他一切（含 memory 檔、backlog、ref-docs——contracts.md 屬 WO-6）

## 工具接線

bash（cat/rg/ls）；字串搜尋一律 rg；禁 CR 寫入面；禁 /tmp。

## 驗收（命令＋預期，逐條實跑）

1. `rg -n "首個真實消費者" skills/post-build/SKILL.md` → 命中（項 1 第三腿）
2. `rg -n "清理判準" rules/must-execute-before-complete.md` → 命中（項 2）
3. `rg -n "框架行為 bug" skills/execution-plan/SKILL.md` → 命中（項 3）
4. `rg -n "樣本怎麼選" skills/acceptance-evidence/SKILL.md` → 命中（項 4）
5. `rg -n "上界估計" skills/implement/SKILL.md` → 命中（項 5）
6. `rg -n "注入先例|先查既有" skills/arch-thinking/SKILL.md` → 命中（項 6）
7. `rg -n "先讀 log|print 各資料源" skills/debugging-and-error-recovery/SKILL.md` → 命中（項 7）
8. `rg -n "零可見性|尾端 pipe" skills/debugging-and-error-recovery/SKILL.md` → 命中（項 8）
9. `rg -n "pathspec" rules/modern-cli-preference.md` → 命中（項 9）
10. `rg -n "唯一錨點|盲重試" rules/tool-discipline.md` → 命中（項 10）
11. `rg -n "ad-hoc" rules/model-routing.md skills/model-routing/SKILL.md` → 兩檔命中（項 11）
12. 負向：`rg -n "muse-spark|gpt-" rules/model-routing.md rules/modern-cli-preference.md rules/tool-discipline.md` → 零命中；新增行零日期/版本
13. bundle gate：`uv run python scripts/deploy_agents.py` 跑完報 gate 百分比（未爆＝通過；爆＝回報勿自行砍內容）
14. 範圍：`git diff --name-only` ⊆ 11 檔＋宣告過既有

## 證據紀律＋PII 禁令

每條驗收附完整命令與原始輸出；no-op 項附行號證據；報告禁 email／人名。

## 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單（git diff 對照） 2. 12 項逐項落實說明（file:line；no-op 項附證據） 3. 驗收 1-14 原始輸出 4. 偏差記錄 5. 未驗證項 6. 建議 reviewer 聚焦點
