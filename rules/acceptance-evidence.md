---
harness-scope: neutral
---

# 驗收證據階層

## 核心原則:證據獨立性

證據強度取決於來源是否獨立於被驗證物。AI 同寫 test＋impl 共享理解，可能忠實實現同一錯誤前提；綠燈只證明自洽。認知誤差、Intent Drift、filter trap、runtime assurance 見 acceptance-evidence skill。

### Claim→Evidence→Trust(no-impact claim 校驗)

producer 宣稱「不影響 X」（accounting/risk/invariant）須有獨立機械證據（diff、rg 殘留、LSP references）；self-report 不能取代查證。數字/死碼/silent-failure/自報元資料各類 claim 判準見 acceptance-evidence skill（Claim→Evidence taxonomy 節）；review diff 見潛在 silent-corruption 引入時視為 no-impact claim 反向應用。

### oracle authority 分級（S/H/I/N 正典）

oracle 權威四級：**S**（獨立 authoritative oracle_source 的 frozen spec/TC）、**H**（歷史真實數據/carrier 行為）、**I**（impl 衍生）、**N**（無 oracle）——**I/N 禁 autonomous 補強授權**；frozen 本身不授予 S。判定流程、anchor 形態例＝acceptance-evidence skill。

## 證據階層

驗證深度按風險分級（L1 靜態→L6 人類觀察）；**禁用低層證據冒充高層驗收**，低風險不必爬滿六層。層級表、A/B 軸分工、驗證順序的單一落點＝acceptance-evidence skill。
