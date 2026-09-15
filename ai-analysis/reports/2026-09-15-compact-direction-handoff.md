# Compact 建議方向與實作交接

> user 回報 usage 剩 5%，要求先保存所有想法。本文件是設計補充與未定案事項，不是新增現行規則；新補充未另派獨立審查。已審主體是 [EP S3](../_tasks/09-15-development-workflow-redesign/ep.md)。實作交其他 LLM，HTML 本輪免驗。

## 明確推薦

**先把任務持續保存好，再讓 user 決定何時 compact；恢復後以實物驗證下一步。** 不開發自製 summarizer、不取代 harness compact、不新增 context-preservation skill 或狀態資料庫。把共用恢復順序放進已規劃的 `_common/task-recovery.md`，由既有 compact-prep／at／handoff 消費。

成功標準是接手能繼續正確工作：不重做已完成項、不重派活 job、不把未知說成完成、不丟失設計取捨、不越權。摘要短不短、能否背出摘要，都不是充分驗收。

## 先區分三種問題

| 問題 | 有效處理 | 不應期待 |
|---|---|---|
| 訂閱 usage 將盡 | 優先落盤，保留接手入口；依 user 選擇等待或交接 | compact 不能被當成重置帳號配額的方法 |
| context 壓力／大量重複材料 | 縮小讀取、成果外部化、有界派工；user 決定 compact | 不能假設指定百分比在所有 harness 都可讀或有效 |
| 推理漂移、反覆誤解、政策翻轉污染舊 context | 保存材料後用 fresh session，先重建必要 read-set | 同一卷 compact 不保證能清除錯誤假設或舊規則影響 |

user 報的 5% 是 usage 提醒，本輪沒有 context 使用量的可信測量；兩者不可混用。派 Muse 可減少主 session 查資料，但工單、回收、判斷仍消耗主 session，不能把最後額度全花在新增研究。

## 實作順序：先骨架，後補強

### A. 先做隨時可恢復的最小路徑

1. 現有 EP 進度節放唯一接續入口；user 指定 report 就連到該 report。無 EP 用既有 journal，不新增 pointer.json／registry。
2. 關鍵決策、失敗發現、段落完成、job 派出／回收時更新持久狀態；不是每次工具呼叫都寫流水帳。
3. compact-prep 先完成並讀回 checkpoint，再考慮 memory 候選整理。沒有權限、quota 或穩定結論時，memory 明列未做，但不阻塞保存工程狀態。
4. user 決定 compact／新 session／稍後接續。沒有 user 要求不自動排程、不自行切換模型或呼叫 compact。
5. 恢復時先讀入口與目前實物，驗證下一個具體動作的前置條件，再繼續工作。

最小路徑不依賴 transcript API、before_compact hook 或 token threshold。當日 controlled-compact-strategy 報告提的 threshold／新 skill 是候選想法，不直接採用；沿用既有入口即可。

### B. 再補語义保存與異常恢復

checkpoint 只需能回答以下問題；已有 EP／帳本欄位用引用，不重複貼：

- **正在做什麼**：目標、成功條件、當前階段、明確不做範圍。
- **為什麼這樣做**：已定方案、最重要理由、排除過的方案及原因、什麼新證據會改判。
- **現在真的有什麼**：cwd／owning WT、baseline、自己修改的檔案、外部 dirty 邊界、產物位置。
- **哪些是真的完成**：精確命令／結果／證據指針；區分計畫、已寫、已跑、獨立驗收。數字與錯誤字串照實物，不靠重新概括改寫。
- **哪些還未知**：失敗、未驗假設、未裁 findings、沒有讀到的來源、目前暫定判斷。
- **哪些還在外面跑**：jobId、owner、scope、目前狀態、收回命令／入口；無 jobId 時寫暫時 shell session 並明確待補。工具逾時不當 job 失敗。
- **下一動是什麼**：一個可執行動作、所需 read-set、成功／失敗後的分支。避免只寫「繼續完成」。
- **授權到哪**：user 原話或對話指針、範圍與仍適用條件；不把 compact 視為授權自動失效或自動延伸。

不要求保存隱藏推理逐字稿。保存可交接的決策摘要、證據、假設與取捨即可；長 log／完整 findings 留原始檔。

## 恢復端的具體順序

1. **認任務**：以 user 指定 EP／卡／report 判定，不用「最近修改」猜任務。核對 cwd 與 owning WT。
2. **認現況**：git HEAD/status、EP 進度、卡狀態、活 job；checkpoint 的 hash 是比對基線，不能照它 reset／checkout 回去。
3. **認未決**：讀 active findings、最新失敗證據、已採納但未修／已修但未驗的項目。
4. **認理由**：看已定取捨與排除方案。STATE 僅補觀察，memory 按需讀，不讓舊觀察覆蓋實物。
5. **認規範**：讀當前所需 skill／治理檔；政策刪除／翻轉依 freshness 要求 fresh context，不以「我剛重讀了」假裝舊污染消失。
6. **小步驗證**：針對下一動核對必要前置，如指定測試結果、目標檔內容、job 是否仍活。能核對舊證據就不重跑整套測試；證據已失效才重驗受影響範圍。
7. **繼續**：前置成立就做，不額外要求 user 重述整題。缺資訊只擋依赖該資訊的工作；能獨立推進者照做。

恢復輸出宜短：「目前做到 X；證據 Y；未決 Z；接下來做 A」。這是核對結果，不是再生成一份完整摘要。

## Marshal／多模型特別處理

- Marshal 的任務狀態放 caller 可讀的 artifact，不能只存在某顆 worker 的對話裡。
- 派出時就登記收法；caller compact／重啟後先收既有 job，禁止因看不到通知重派。detached worker 是否活須查 runtime，不憑 run 清單綠色字樣。
- worker 回覆必帶自己的 scope、成果與未做項；同一 job 多成果要逐項狀態。新 session 不用「worker completed」推定整段已驗收。
- 資料交接優先檔案＋精簡工單；不要為延續記憶一律 resume 整卷。resume 可能攜帶大量舊 context，實際成本與支援依 carrier 查證。
- 穩定來源可在同 context 已讀且未變時復用；新 worker 仍需可達的最小契約。availability 每次 dispatch 查，不用 checkpoint 內舊 quota 當 available。
- 必需獨立 reviewer 的 fresh context 不為省讀而取消。分享實物可以，分享作者論證會改變 reviewer 的錨定條件，需符合其 profile。
- 主 session quota 極低時停止新增非必要分析腿，先回收與結算；仍在跑的工作記錄 owner/收法，不能為「乾淨收尾」擅自終止。

## 最後額度不足時的降階順序

**先写**：任務入口、目前未完成動作、最新結果／失敗、自己的未提交改動、活 job 與收法、下一步。

**再補**：關鍵決策理由、未驗假設、排除方案、scope/授權。

**有餘裕才做**：潤稿、去重舊日誌、memory 候選整理、簡報／圖、非必要廣域研究。

此處是寫 checkpoint 的優先序，不是授權跳測試後宣稱完成。極簡 checkpoint 也必須明列不完整之處；對話提到「已記錄」之前要確認檔案寫入成功。

## 要防的失敗模式與驗收

| 注入情境 | 正確行為 |
|---|---|
| STATE 說 Done，EP 尚有 implemented 未 verified | 保留未驗狀態，讀實物，不直接結案 |
| HEAD 一樣但 untracked 檔變了 | 內容身份失效，重驗受影響範圍 |
| wait timeout、worker 仍活 | 重掛收法，不重派 |
| worker 已完成但 caller 沒收回 | 回收原結果，不再次執行工單 |
| checkpoint 的測試結果找不到原始證據 | 標無法核對，再按風險補驗；不把摘要當獨立證據 |
| 設計理由丟了，只剩「改 A」 | 回源或保留未知，不自行發明理由；若影響下一動先釐清 |
| 無 transcript、無 hook、無 memory 寫權 | 仍能用 EP/實物恢復，標明不可恢復範圍 |
| 規則翻轉，舊卷仍大量持有舊規則 | fresh session 接續當前 read-set，不混合兩套政策 |
| quota 將盡，half-written patch／debug 中斷 | 精確標未完成與最後錯誤；不假 Done、不清掉未完成改動 |
| checkpoint 含旧授權 | 核對原 scope 與當前動作是否仍符合；不 blanket 清空／擴大 |

先用兩個 fresh contexts A/B 做可觀察恢復測試：A 到斷點寫檔；B 只收到入口指針，實際讀料並選正確下一動。對照相同場景無 checkpoint 的重建成本；記重複工作、錯任務、遺漏 pending、違反 invariant、所讀材料、可取得 usage。不能只以 B 能背誦摘要為 PASS。

這個測試驗的是恢復協議，不是 harness 真 compact 保真度；後者若要宣稱已支援，仍需在對應 harness 實際 compact 前後測試。不可混報。

## 尚未定案，保留給實作／後續研究

- checkpoint 是否可以有機械寫入／驗 ref helper：先手動契約跑通，確有重複錯誤再加工具；本 EP docs mode 不偷加 runtime。
- 何時提醒 compact：可用行為訊號（反覆重讀、持續 scope 漂移、user 指示）作建議，但沒有實測標準；不硬編 token 百分比或 turn 數。
- adaptive read-set：先放必要來源，遇到不足再展開；須測漏掉間接 consumer 的風險，不用越短越好作目標。
- 長期 journal 清理：傾向目前狀態一處、歷史決策與原始證據保留原 owner，避免每輪 append 讓接續又變考古；清理不能在 quota 救援路徑上，不能先刪後補。
- 更佳 trigger／harness adapter：只有存在實際 API 且可驗時另立範圍；目前不依賴 before_compact／SessionEnd。
- 恢復品質劣化的停止條件：若仍無法確定 task/owner/下一動前置，停止相應寫入並回報；不是硬撐到輸出看似流暢。

## 給接手 LLM 的明確指令

先讀主 EP S3 與本文件，把「已審 S3 契約」當實作主體；本文件新增的救援優先序、失敗案例與研究候選需區分。先完成 checkpoint producer＋recovery consumer 的最小可用路徑，再做場景驗收，不先建新 skill/服務。不重做 Marshal，不修改 memory 治理或 compact 時機權限。若新補充改變原 EP 行為／AC，先更新 S3 並做 scoped review，不能借原 EP verified 狀態冒充已審。

目前這條任務：規劃交付已完成、沒有仍在跑的 Muse job、新流程未實作、沒有 commit/deploy。最新 compact 補充即本檔，HTML 不需在本輪補驗。
