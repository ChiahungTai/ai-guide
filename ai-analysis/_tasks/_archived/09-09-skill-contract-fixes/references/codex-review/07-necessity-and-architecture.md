# 必要性、整體架構建議與評價

最終架構判斷；建議未實作。此檔將前六項 checkpoint 的局部問題合成，不把每個症狀都變成新 gate。

## 整體評價

這套流程的方法論成熟度高於其執行契約成熟度。它知道要防什麼：方向漂移、同一模型自洽、跨模組 ripple、假的完成證據。但它把這些防線散落在多個命令，各命令又各自定義分流、迴圈、落盤與結案，形成多個局部正確卻不能確定組合的控制流程。

最需要改的是 ownership 與交接，不是再加審查維度。保留職責分離；刪掉跨 skill 重複的決策權。

| 評價面向 | 評價 | 根據 |
|---|---|---|
| 問題意識與方法論 | 強 | spec/EP 自足、致命先驗、consumer 驗證、review/judge 分工、證據階層 |
| 單 skill 的角色定位 | 中上 | 名义职责大致清楚；judge 不實作、post-build 編排是可保留邊界 |
| 跨 skill 契約一致性 | 弱 | JR1 帳本分裂、PB3 雙完成時點、IM2 consent 重判 |
| 中斷與接續可靠度 | 不足 | PB2 只認 open、CR1 scope 依 WIP 大小、CR2 before 身份不一致 |
| 對 solo developer 的流程成本 | 偏重 | implement 完整 review loop 後 post-build 再起 review；EP 也攜帶大量固定收尾程序 |
| 風險分流精準度 | 不穩 | PB1 按副檔名跳審、IM1 refactor 當小型、EP1 invariant 在不產 EP 時消失 |

這是定性設計評價，沒有實測 token/耗時/漏報率，不用看似精確的總分代表品質。

結論：可以在有經驗的人持續介入下使用；不宜把「跑完這條鏈」當成跨 session 可可靠接續、可自動宣告完成的保證。文件層架構審查 no-go 的對象是這個保證，不是宣稱所有現有開發結果失效。

## 各 skill 是否有必要

| skill | 處置 | 必須保留的價值 | 可刪／移出的部分 |
|---|---|---|---|
| spec | 保留可選入口 | 把模糊意圖、禁止事項、成功条件變成可傳遞需求 | 不固定互動輪數；已明確需求不重做 ceremony |
| execution-plan | 保留，自足但縮身 | 工作分段、依賴、風險假設、驗證、跨 session 接續 | 通用收尾操作不要逐字複製進每份 EP；EP 列此任務要結算什麼、引用執行 owner |
| implement | 保留，收窄為執行與證據 producer | 逐段實作、變更理由、consumer 驗證、段落 checkpoint | 不再自行發布最終 Done；完整末輪 review 與 post-build 避免無差別重跑 |
| code-review | 保留獨立入口與共用 reviewer | 在明確版本/範圍上提供外部於 writer context 的發現 | 被 post-build 呼叫時不提前產 commit message；修正後的最終 commit 命名交 commit |
| judge-review | 保留獨立職責；不必每次都成為使用者手動步驟 | 查證 finding、否證錯誤建議、判斷解法及必要性 | 刪掉本地「立即實作」語氣、重定帳本位置、重判流程授權 |
| post-build | 保留作一個收斂入口 | 找到有效 review/decision/evidence，補缺口、apply/followup、最終結算 | 不把每次呼叫都視為从零跑完整鏈；清理/庫存/廣泛 corpus 維護不應混成產品完成條件 |
| arch-thinking | 保留方法論入口，按需讀 recipe | dependency/context/use-case 視角、補償 pair、ownership 粒度 | 把工具操作配方/專門 viewport 資料生成放可按需讀的引用檔，避免只需一個 lens 仍讀整包 |

沒有足夠理由把六個使用者入口直接刪成一個大 skill。其需求時點不同，跨 session 獨立呼叫有價值。應合併的是底下重複的流程邏輯，不能把「入口多」直接當成「過度工程」。

## 明確建議刪除或取消的重複

1. **取消第二份 finalization 狀態機**：完成何時發布只定義一次；implement 段落完成不等於 post-build 最終完成。PB3。
2. **取消各 skill 自選 finding 檔的自由**：同一輪由 caller 解析一個 artifact，其餘消費它。JR1。
3. **取消「無新 UC 就跳架構同步」**：UC 功能維度與 architecture 結構維度本來就獨立。IM1。
4. **取消「Markdown 就只有 consistency」**：控制面 Markdown 本身會改行為。PB1。
5. **取消已被後續修改淘汰的提前 commit-message 產生**：單獨 code-review 可保留便利用途；自動鏈中在 apply 前產 message 只會製造額外 claim 維護。來源 code-review 的 Commit Message 段與 post-build 階段 1→3。
6. **取消同內容、同範圍、同 profile 的完整重審預設**：implement 已跑有效 review，post-build 應先比對證據身份，再決定補跨段整合/改動 delta；不能只因命令名稱不同再審一遍。不同 context、不同範圍或高風險第二意見仍保留。

第 6 項是設計建議而非已證明「第二次 review 沒價值」。只有基於實際弧比較獨有 findings、誤報與成本，才能決定少跑哪一輪；不可先砍所有獨立 reviewer。

## 不建議新增的東西

- 不再做一份總控 mega-skill，讓它重抄所有子技能。
- 不再加一層分類軸，令 LLM 在 file-count、risk、scope、invariant、docs 上做更多交叉推理。
- 不把所有事情做成 hook。是否合理採納、需要哪個邊界測試仍是語義判斷。
- 不要求每個簡單修改生成 EP + HTML + tour；也不以全面刪掉 viewport 作省 token 手段。
- 不把每個重複 finding 自動變成 backlog 卡或新規則；先修造成它反覆出現的 ownership。

## 建議的最小架構

**需求層**：spec 可選；穩定的使用者要求/禁區/成功條件必須進 EP 或 simple 任務摘要。允許變的是技術方案，不能混成使用者授權也可自行更改。

**任務層**：EP 持有 task scope、baseline、段落及當前進度。simple 任務用短摘要，免完整 EP，仍保留命中的 invariant。

**執行層**：implement 產出 code、偏差、有效驗證證據與 Built 狀態。段落失敗先記錄並阻止依賴它的後續段落；獨立段可繼續。

**評估層**：code-review 讀指定範圍與版本，產 finding；judge 只裁決；caller apply；followup 驗收採納清單及新引入問題。各輪共享同一帳本。這是現有職責的收斂，不是新造六個流程。

**收斂層**：post-build 檢查現有證據是否仍有效，只補缺的 review/verification；未決事項可報告但不得假裝最終完成。全綠後調 metadata-sync 發布 Done/歸檔，再投影 Report Shell。standalone implement 的終止分支若需要結案，走同一 finalization gate。

**維護層**：暫存清理、corpus 存量維修、庫存統計可維持既有入口與政策；與本弧產品完成分開記錄。相關 tour 因本弧壞掉仍是本弧責任。

## 需要傳遞的最少資訊

不必先造 JSON DB 或 runtime engine。先用既有 EP/帳本的頂部 metadata 明確傳：task 身份與 scope、integration baseline、reviewed content identity、findings artifact 路徑、before snapshot 身份（使用時）、目前有效驗證與未決項。用同一份資料決定 resume、review 與完成，避免各 skill 重新猜。

如果將來這些欄位仍頻繁漏填，再把「檔案存在／版本吻合／decision 狀態合法」機械化。其餘採納與風險判斷維持 LLM，先不要為修流程 drift 開發新的工作流平台。

## 建議順序與風險

| 優先序 | 範圍 | 相對複雜度 | 主要風險／验收 |
|---|---|---|---|
| 先修交接 | JR1、PB2、CR1、PB3 | 中 | 無 EP/換 session/大 WIP/修正失敗四路径，確保不讀舊帳本、不漏弧、不假完成 |
| 再修分流 | PB1、IM1、EP1、IM2、IM3 | 中 | leaf 不膨脹，invariant/refactor/docs-control 不降錯；授權不重判 |
| 最後減流程 | review 去重、EP 固定收尾模板減重、post-build 維護分離、arch-thinking 按需 recipe | 中至高 | 不丟原有獨立性；用真實弧記錄独有 findings 與成本後再精簡 |

## 驗收建議

選少數有辨識力的流程場景做 dry-run：單檔 invariant 修正、無新 UC 大 refactor、純 Markdown 改交接契約、部分 committed 大 WIP、judge 後中斷接續、post-build 未收斂、無 EP standalone review。每個場景比較「誰讀哪個 artifact、誰能寫哪個狀態、停在哪裡、證據是否屬當前產品」。

本次已做文件逐條與跨檔對照，以上 dry-run 為後續修改驗收建議，沒有聲稱本次已實跑各 harness。
