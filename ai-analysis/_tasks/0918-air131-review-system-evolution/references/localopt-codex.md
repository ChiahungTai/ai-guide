# 設計討論——逃離局部最優＋中途不可行＋難用才發現（codex 腿）

## 0. 紅線
- READ-ONLY：不寫檔、不 git；禁再委派；純推理（材料內聯）；產出＝最終回覆本文

## 1. 背景
solo dev＋AI 的 instruction 治理系統（ai-guide）：規則/技能給四家 AI harness 消費。系統逐弧演化（每弧=卡→計畫→實作→審查→收線），每弧凍結決策「勿重辯」＝局部最優化器。日常機械閘存在（parity/consistency/hooks/corrections 週報）。剛完成一次全弧深審（255 commits、6 異構腿、28 findings、judge 收斂）效果顯著。

**user 的成熟命題**：
1. 沒有預知能力、做了才知道——**大範圍定期審查不可避免，目的是逃離 local opt**
2. 三子題：(a) local opt（逐弧最佳化的全局病：儀式累積/詞彙漂移/邊界決策複利/YAGNI 違反——沒人會全局設計出現在的樣子）(b) 寫到一半發現不可行 (c) 做完才發現用起來不好用（AI 消費的 instruction 難用＝找不到/載入貴/衝突/歧義）

之前 codex 裁決過「下次全弧零 Critical」路線（預防軸：invariant failure-injection→parity lint→semantic-risk routing→activation observability）——user 指出那是預防軸，**local opt 軸是另一件事**：就算零日常錯誤，累積形態仍可能全局差。

## 2. 討論問題（逐題，機制設計層）
1. **local opt 的理論與感測**：逐弧凍結決策的系統，其 local opt 形態學；什麼連續訊號能偵測「該跳了」（規則修正率/儀式成本曲線/詞彙分歧度/決策複利證據）？什麼只能靠不連續跳躍（重寫思想實驗/跨家族/消費端視角）？給一個「升溫觸發規則」的具體設計
2. **大審 cadence**：訊號觸發 vs 日曆 vs 混合；「arc review Critical 逃逸率」當 self-calibrating 感測器（零 Critical 連續 N 輪→降頻，出 Critical→升溫）——這個回饋迴路的設計與風險
3. **寫到一半不可行**：kill criteria 的可否證設計（EP 內預寫「出現 X 就止損」）；spike timebox；止損記帳（避免沉沒成本——止損弧怎麼結案才不激勵硬撐）
4. **難用才發現**：消費端 dry-run（fresh agent 在消費 repo 演練任務——剛實證有效：兩 repo 都走到正確 resume point、同時暴露 STATE.md 弱點）標準化的形態；friction log（workaround=設計臭味）的收集面；「難用」對 AI 消費者的操作化定義與量測
5. **統攝**：這三子題有沒有統一的機制骨架（例：全都是「回饋迴路太長」的病——縮短回饋迴路的設計原則）？給 user 一個可記住的心智模型＋最小機制集

## 3. 交付
逐題機制設計（可落地粒度）→ 升溫觸發規則具體案 → 統攝心智模型 → 最小機制集（對既有系統的增量最小）→ 方法論限制段。
