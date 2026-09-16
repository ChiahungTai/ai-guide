---
name: arch-thinking
description: "當設計或審查模組邊界、依賴、共用契約、重用、state ownership，或修缺陷／刪除／重構可能影響其他消費者時使用；設計 API／模組邊界／公開介面合約（Hyrum's Law、邊界驗證、agent-friendly interface）時亦用——合約細節見 interface-design 側檔。以 use case、Clean Architecture、DDD 判斷責任，按觸發條件查既有機制、補償邏輯與寫入路徑，產結構證據及限制。City Map、call graph、type structure、data-flow、Pattern Radar 配方按需讀取；決策摘要由 deep-thinking、呈現由消費命令負責。"
---

# Architecture Thinking — 結構判準與查證

先問消費者需要什麼行為，再判責任與邊界；視角不強制四層模板。使用 [deep-thinking](../deep-thinking/SKILL.md) 比較選項、查直接與間接後果、交付決策摘要；本 skill 提供架構判準及證據需求，不另定報告版型。

## 使用契約

方法論跟任務角色走，不依模型家族分版本。消費命令指定受眾、範圍與呈現：review 產 finding，illustrate 產人類 viewport；工具能力由當前環境確認，不以家族名推定。

依序執行：**定位 use case 與變更範圍 → 套用 §一判準 → 依 §二觸發表讀對應配方 → 查證 → 將結論及限制交呼叫端**。多條件命中時合併查證範圍，每個命中的檢查都要有結果；不把所有配方全跑一遍。

## 一、設計視角

### Use case 與責任

辨識主要消費者、需要的行為與不可破壞的 invariant。先查既有同類機制，再決定新增、擴充或保留。層數、檔案數與抽象數不是品質指標；新邊界須解決具體的語義、依賴或變更責任問題。

### 依賴規則

domain／use case 的政策不依賴外部技術細節；adapter 實作內層需要的介面。常見表示為 domain ← use case ← adapter，infra 提供外部實作；箭頭表示**原始碼依賴**，不是 runtime 呼叫順序，也不是每個 repo 必須有的目錄結構。

查新增依賴、循環與傳遞負擔。**反向耦合**候選是 lean 廣用模組新增對 heavy 實作的依賴，使其消費者承擔原本不需的負擔；heavy 模組依賴 lean 工具本身不構成反向耦合。是否真的增加載入／部署成本須查實際路徑，不能只看套件名稱。

### Bounded context 與共用契約

bounded context 是語義與模型的一致性邊界，不能只憑資料夾或 private 命名判定。查同一概念在各消費者的意思、authority、生命週期與修改責任；跨域使用公開合約，不直接操作他域內部 state。

**共用 domain service 外溢**：

- 共用契約正確、消費需求不同 → 消費端投影／轉換，不為單一消費者偷偷改共用語義。
- 共用契約或實作錯誤 → 修正 authority，盤點消費者遷移與補償邏輯；不永久疊加 consumer patch 掩蓋錯誤。
- 同名概念其實語義不同 → 明確分開模型或介面；只有共同且穩定的政策才抽共用。不能因欄位相同就合併 context。

介面合約的具體設計交 [interface-design](interface-design.md)；本節判定誰擁有什麼責任。

## 二、結構機械：觸發與配方

先用下面的可觀察條件選檢查。**命中就先讀指定配方，再作相應結論或修改**。沒有命中的配方不載入；只需局部判斷時以局部為界，關鍵未知影響推薦才向外擴張。

| 觀察到的任務／變更 | 必做檢查 | 讀取配方 |
|---|---|---|
| 新增 abstraction、注入、provider、fallback、reader | 先查既有同類機制：定義、實際消費慣例、模組 AGENTS.md 設計宣稱 | [重用與既有機制](reuse.md) |
| 新 enum／function／data structure，或準備抽共用 | Pattern Radar：先找相似候選，再判語義、invariant、ownership、生命週期與依賴成本是否相容 | [重用判定](reuse.md) |
| 修改共用 domain service 的語義／計算 | 消費者契約差異＋補償關係；依 §一區分 consumer projection 與 authority 修復 | [state 與補償](state-and-compensation.md) |
| 修缺陷，刪除整檔／class／method，或 refactor 遷移邏輯 | 補償邏輯盤點：查動到一側是否使另一側復活或 over-correct | [補償邏輯盤點](state-and-compensation.md) |
| 觸及 mutable state／invariant，或遷移改變 ownership | 變更路徑計數：write sites、owner、並行與順序、atomicity、invariant | [變更路徑計數](state-and-compensation.md) |
| 新增跨模組依賴／跨域存取，或需結構與影響範圍 | City Map、call graph、type structure、data-flow 中對應問題的資料 | [結構證據](structure-evidence.md) |
| 對外部框架作能力／語義宣稱 | domain grounding：查實際使用的 source/stub/契約；未確認保持 open | [結構證據](structure-evidence.md) |
| 排定既有骨幹的審查優先序 | core identification：消費範圍、critical path、耦合與證據缺口 | [結構證據](structure-evidence.md) |

### 工具與資料契約

符號／圖譜／型別路由依 [symbol-query-routing rule](../../rules/symbol-query-routing.md)，具體 CR 能力與缺場 gate 依 [cr-query](../cr-query/SKILL.md)；本 skill 不複製工具優先序或家族操作表。純 docs 用 rg 查引用與語義，標明是文件拓樸，不能冒充實際載入／執行。混合 repo 按被查材料分流，不因缺 Python 而把其他語言當 docs。

每項結論攜帶：**問題與範圍、查到的關係／行為、來源與新鮮度、尚未驗證處**。工具缺場、索引過期或結果不完整時依路由降級，限制結論；「未找到」不能寫成不存在。graph 是結構證據，dynamic dispatch／config／reflection 與 runtime 值需另查 source 或執行。

## 三、流程注入點

| 階段 | 本 skill 的工作 |
|---|---|
| spec／EP | 從 use case 確認責任，查既有機制、契約與消費者，檢查提案的關鍵假設 |
| build | 按變更觸發配方；重用落地後重查新 symbol 的落點與依賴成本 |
| review | 對實際 diff 與消費路徑查證，包括刪除側、補償側與 ownership 變化 |
| illustrate／既有結構盤點 | 產出指定範圍的結構資料及不確定性，供消費端決定如何展示與審查 |

## 四、與既有 skill 邊界

- [deep-thinking](../deep-thinking/SKILL.md)：決策問題、選項、後果與改判條件；本 skill 供結構判準。
- [debugging-and-error-recovery](../debugging-and-error-recovery/SKILL.md)：主導故障定位；涉及共用契約、補償、ownership 時調用本 skill，除錯不是排除條件。
- [acceptance-evidence](../acceptance-evidence/SKILL.md)／[validation-strategy](../validation-strategy/SKILL.md)：決定驗證深度與方式；本 skill 指出需要驗證的 invariant 與組合路徑。
- [interface-design](interface-design.md)：介面合約設計；本 skill 處理語義與責任邊界。
- [illustrate](../illustrate/SKILL.md)／[code-review](../code-review/SKILL.md)：擁有 viewport／finding 形式、審查者與嚴重度政策。

## 五、不做與完成條件

不強制分層模板，不產 runtime tracing，不在此定義人類逐行審查或 finding 嚴重度，也不把模型家族當作能力證據。

**分析方法論誠實性**：結構結論須交代用了什麼工具及範圍、索引／workspace 新鮮度、哪些無法驗證，以及哪些是原則推論。呼叫端已有 evidence／限制欄位就填入，不另造重複報告。

命中的檢查均有結果、影響決策的未知已解決或顯式標為阻塞、證據足以支撐所作結論，即可交付。未完成查證仍可提出有條件建議，不能報成結構或行為已驗收。
