# 設計討論——逃離局部最優＋中途不可行＋難用才發現（muse 腿）

## 1. 紅線（違反＝失敗）
- READ-ONLY：禁任何寫入、禁 git 寫操作；禁再委派；禁 /tmp；產出＝最終回覆本文

## 2. 背景與 user 命題
ai-guide 是 solo dev＋AI 的 instruction 治理 repo（規則/技能給四家 harness 的 AI session 消費）。系統逐弧演化：每弧（卡→EP→實作→審查→收線）局部最優化，決策凍結「勿重辯」。已有機制：日常機械閘（parity/consistency/hooks）、corrections-weekly（規則衰減週報）、flow-feedback（摩擦收集）、overhead 盤點、/state-review、剛完成的全弧深審（GUIDE-CR：255 commits 六腿 28 findings）。

**user 修正後的命題**（比「日常品質高到不需搶救弧」更成熟）：
1. 有些問題**沒有預知能力、做了才知道**——大範圍定期審查不可避免，目的是**逃離局部最優**
2. 三個子問題：(a) 陷入 local opt（逐弧最佳化的全局病：儀式累積/詞彙漂移/邊界決策複合成沒人會全局設計的拓撲）(b) 寫到一半發現不可行 (c) 做完才發現用起來不好用
3. 問：有什麼建議的機制設計

## 3. 必讀（既有機制——你的設計要接這些而非重造）
1. /Users/ctai/Github/ai-guide/skills/corrections-weekly/SKILL.md——規則衰減偵測（現有「local opt 感測器」候選）
2. /Users/ctai/Github/ai-guide/skills/flow-review/SKILL.md＋flow-feedback 機制（rg 找）——摩擦→卡的既有鏈
3. /Users/ctai/Github/ai-guide/skills/state-review/SKILL.md——全 repo state-rot 掃描
4. /Users/ctai/Github/ai-guide/ai-analysis/reports/2026-09-15-dev-flow-overhead-inventory.md——儀式成本盤點先例
5. .agent-tmp/dispatch-compiler-proposal/gcr-arbitration-codex-verdict.md 末段——codex 對「下次全弧零 Critical」的路線圖（你評它的盲點：那是預防軸，不是 local opt 軸）

## 4. 討論問題（逐題）
1. **local opt 的分類學與感測**：這個系統的 local opt 形態學（儀式累積/詞彙漂移/決策複利/YAGNI 違反/結構債）；哪些可用**連續訊號**偵測（corrections 率上升=規則失效？parity 漂移計數？每弧儀式成本趨勢？corrections-weekly 能否升級為 local-opt 儀表板）？哪些只能靠不連續跳躍（新 context/跨家族/消費端視角/重寫思想實驗）？
2. **大審的 cadence 設計**：訊號觸發 vs 日曆觸發 vs 混合？「arc review 的 Critical 逃逸率」本身當感測器（連續兩輪零 Critical→降頻；再出 Critical→升溫）？給具體觸發規則
3. **寫到一半不可行**：既有「致命先驗 POC」的強化——kill criteria 寫在 EP 裡的可否證條款？spike timebox？「止損是成功」的記帳方式（避免沉沒成本續撐——本 repo 有真實案例嗎，rg 找）
4. **用起來不好用**：AI 消費的 instruction 其「難用」=找不到/載入太貴/互相衝突/執行歧義。GUIDE-CR 的消費端 dry-run（兩 repo fresh agent 演練開工）剛證明有效——該不該標準化為「每 N 弧一次消費端演練」？friction log（agent 繞過規則的 workaround 即設計臭味）怎麼接 flow-feedback？
5. **整合提案**：把你的設計整合進既有系統（哪些進 corrections-weekly、哪些進 state-review、哪些是新機制）——最小新增面

## 5. 交付
逐題結論（附既有機制錨點 file:line）→ 感測器清單（連續訊號）→ 跳躍機制清單（不連續）→ cadence 觸發規則具體案 → 整合提案（最小新增）→ 方法論限制段。
