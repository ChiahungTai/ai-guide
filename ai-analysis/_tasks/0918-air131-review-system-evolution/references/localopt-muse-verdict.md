# 逃離局部最優＋中途不可行＋難用才發現：設計討論（muse 腿，READ-ONLY）

先說總判斷：user 修正後的命題成立，且 codex「下次全弧零 Critical」路線圖確實有盲點——那條路線是**預防軸**（把每類 Critical 的 invariant 前移到產生點的 failure-injection contract），它優化的是**單個決策的品質**；local opt 是**複合病**（每個決策各自正確、加總成沒人會設計的拓撲），預防閘門驗證不了複合。證據：overhead 盤點 38 項每一項都有事故理由（`ai-analysis/reports/2026-09-15-dev-flow-overhead-inventory.md:100-106` 六刀法裡「③防過事故」一欄），但 38 項的總和從來沒被全局設計過——這正是 local opt 的定義。

## Q1. local opt 分類學與感測

### 形態學（五型，皆有本 repo 標本）

| 型 | 標本 | 連續訊號可偵測？ |
|---|---|---|
| ① 儀式累積 | 38 項 overhead，每項有理由、總和無人設計（overhead 盤點 `:18` 點名 9/27/28/30 待校準） | ✅ 每弧儀式成本趨勢、gate 數增長 |
| ② 權威複寫漂移 | 「三判準三寫、紅線 14 處、model 具名 18 處」（codex verdict §5 P1；AIR-128） | ✅ parity 漂移計數（`skills/scan-project/scripts/check_single_source.py` 已在） |
| ③ 決策複利拓撲 | 「已決策勿重辯」逐弧凍結 → 複合成無人設計的邊界（state-review 存在理由：每個 diff 各自乾淨、累積錯誤，`skills/state-review/SKILL.md:11`） | ❌ 只能跳躍（整體狀態視角） |
| ④ 投機機械（YAGNI 違反） | draft-11 telemetry 爭議：codex 主張「先補 deterministic gates 再量 residual」（verdict §1 draft-11 段） | ✅ 未被觸發的 gate／零消費 skill 清單 |
| ⑤ 觀測面腐爛 | 殼 provenance 腐爛、checker 部署權威模型過期（state-review `:11` 真實案例三件） | 半：gate 候選「第二次出現」计数（state-review `:23`） |

### 連續訊號（corrections-weekly 升級為 local-opt 儀表板的原料，全部已在系統內）

1. **corrections 分類趨勢**（`skills/corrections-weekly/SKILL.md:46` 七類）：「過度工程↑」＝YAGNI 訊號；「修了仍壞↑」＝gate 失效；「方向錯↑」＝EP／上游失效。現行判讀產出（`:64`）只問「某規則衰減」，加一問「某類儀式該退役」即成。
2. **parity 漂移計數**：single-source check 的殘留數逐週報——②型的直接量測。
3. **儀式成本趨勢**：overhead 盤點附三問（`:284-289`）本是一次性靜態盤點，把三問變成每季重跑的量測（靠殼搞懂弧的次數／段落 review 漏檢率／外審救弧率），即①型的趨勢線。
4. **零消費清單 delta**：usage-fit audit 已證明 `flow-feedback` 是「唯一完全零消費且非 young」（`ai-analysis/reports/guides-refactoring/usage-fit-audit-20260917.md:15,63,73`）——死亡儀式偵測器現成，定期重跑 usage 矩陣即可。
5. **Critical 逃逸率**：arc review 發現的 Critical 中「本可在日常閘攔下」的比例——codex §6 目標的操作化（見 Q2）。

### 只能靠跳躍（不連續）的

③決策複利拓撲與「重寫思想實驗」類問題：連續訊號只能告訴你「某處在爛」，不能給你「全局該長怎樣」。跳躍機制見「跳躍機制清單」——共同特徵是**換 oracle**（換家族／換消費者／換時間尺度／換「從零設計」視角），而非加量測。

## Q2. 大審 cadence：混合制＋具體觸發規則

採 codex 已提案的 risk-driven lanes＋convergence stop（verdict `:285-299`，以 marginal yield 決定停不停），我只補**頻率調制器**（何時排下一輪）：

- **逃逸率調制（主規則）**：「arc review 的 Critical 逃逸率」當感測器——連續兩輪零 Critical 逃逸 → 降頻（拉長間隔或縮小 scope 到 delta-slice，codex Step 1 的 main-since-baseline 邏輯 `:161-162`）；再出 Critical 逃逸 → 升溫（針對受影響 slice 即時加一輪，不等日曆）。
- **日曆上限（ceiling）**：即使零逃逸，每季至少一次 state-review。理由：state-rot 是靜默累積，連續訊號看不見（state-review `:11`）——ceiling 防的是「量測盲區」，不是「已知問題」。
- **冷卻下限（floor）**：Critical 修完、merged-state acceptance（codex Step 3 `:194-210`）完成前不排下一輪大審——修復需要 bake time，否則審的是同一批殘留。
- **訊號觸發（override）**：corrections 儀表板出現「過度工程連兩週↑」「parity 漂移數破閾」「新增零消費 skill」任一 → 提前觸發對應 slice 的小審（不必全弧）。

關鍵區分（接 codex `:274-284` 不合併論）：`code-review --arc`（歷史弧把系統改成什麼）與 `state-review`（現在整體狀態對不對）是兩種問題，降頻／升溫各自獨立計算——arc 零逃逸不代表 state 無 rot。

## Q3. 寫到一半不可行：給致命先驗加上牙齒

既有機制錨點：`skills/execution-plan/SKILL.md:243-245`（致命先驗：先跑 `poc/poc_*.py` 再繼續設計）＋`:297-299`（前期 POC 驗高風險假設）。它缺三顆牙：

1. **kill criteria 可否證條款**：現行條文只說「驗證可行性」，沒說「什麼結果算死」。提案：每個致命假設配一行「若 POC 顯示 X，則本 EP 作廢／轉向 Y」——寫在 EP 裡，judge 可執行。成本＝一行格式（execution-plan skill 編輯，非新機制）。
2. **spike timebox**：POC 配顯式 timebox（到點即判：升級／降級／砍）。無 timebox 的 POC 是沉沒成本的培養皿。
3. **「止損是成功」的記帳**：本 repo 真實沉沒案例——我以中英文多組關鍵詞 rg 了 `ai-analysis/` 與 execution-plan 面，**沒找到已建檔的中途放棄／止損案例**（且 CJK 檢索在這批工具鏈有漏檢前科，absence≠evidence，這點記入限制段）。但記帳位置現成：backlog triage／archive 治理（overhead `:184` item 32）＋flow-feedback type-1（時機教訓）。提案：卡結案加「止損結案」語義（區別於 Done 與廢棄——廢棄＝方向錯，止損＝不可行被證偽，是成功的驗證），corrections-weekly 不計為失敗，flow-feedback 留一筆 type-1。這是為了對抗「續撐因為停下來算失敗」的隱性激勵。

## Q4. 用起來不好用：四形態各有現成感測器

user 命名的四形態映射：

| 難用形態 | 現成感測器 | 現狀證據 |
|---|---|---|
| 找不到 | usage confirmed-consumption（usage-fit audit taxonomy `:45-55`） | flow-feedback 零消費（`:73`）——連摩擦收集器本身都沒人用 |
| 載入太貴 | bundle size gate 90KiB（overhead `:262-264` item 35） | /at 三重投影（usage-fit `:19`） |
| 互相衝突 | parity lint＋consistency | AIR-128 權威複寫 |
| 執行歧義 | dogfood 發現（illustrate-drift：spec 沒要求讀 AGENTS.md 設計意圖，`flow-feedback/2026-07-31-illustrate-drift-design-intent.md:16-19`） | build 後自動 dogfood 的 type-1 建議（同檔 `:11-13`） |

- **consumer dry-run 該不該標準化**：該，但**不要「每 N 弧」**——codex 已警告 sampling evidence 不可提升為全 consumer proof（verdict `:210`）且 legs 不寫死（`:285-299`）。提案：**control-plane 變更弧必 dry-run＋日曆保底每季一次 fresh-agent 開工演練**。比每 N 弧便宜（靜默期只付保底），且覆蓋「長期無大弧但持續小改」的漂移盲區。codex 是最大消費者（讀檔驅動 11,595 次，usage-fit `:16`），dry-run 家族應含 codex 腿。
- **friction log 接 flow-feedback**：workaround＝比抱怨更強的訊號（繞過規則證明規則在流程上已死）。但入口必須**低儀式**：現行 flow-feedback 要求 type-1/type-2＋counter-factual 格式，而它的收集器 skill 已退役（flow-review `:22`「手寫進池」）、本體零消費——高儀式入口可能是零消費的原因之一。提案：append-only 輕量入口（時間＋哪條規則＋怎麼繞的，三行），workaround 條目在 flow-review 自動升 type-2 候選；聚合與 memory-routing（flow-review `:29-43`）不變。

## 感測器清單（連續訊號，全部已有資料源）

1. corrections 七類週趨勢（ZCode db 面；CC 面缺，`corrections-weekly:74` 邊界）
2. parity 漂移殘留計數（check_single_source.py）
3. 儀式成本三問重跑（overhead `:284-289` 季度化）
4. usage 零／低消費清單 delta（usage 矩陣定期重跑；觀測窗僅 ~30 天，usage-fit `:17`）
5. Critical 逃逸率（arc review findings 分類）
6. gate 候選「第二次出現」計數（state-review `:23`）
7. deployment activation 健康（configured/loaded/active/covering，codex §5 P3 `:383-394`）

## 跳躍機制清單（不連續，換 oracle）

1. **跨家族深審**（state-review `:21`——與 caller 相異是派發理由本身）
2. **消費端 dry-run**（GUIDE-CR 實證；Q4 保底制）
3. **重寫思想實驗**（零成本：「若今天重寫這條 rule，還會長這樣嗎」——只產判斷，不產 code，破「勿重辯」凍結而不破其穩定價值）
4. **code-review --arc 當 calibration／sentinel**（codex §6 step 7——成熟後 finding profile 應變成 edge-case＋stale-docs＋YAGNI＋輕量清理 `:456-473`；profile 本身即成熟度量表）
5. **flow-review B 軸討論**（`skills/flow-review/SKILL.md:45-49`——人類判斷是獨立性最高的 oracle，但只在素材夠時開；「不急」`:75` 是 feature）

## 整合提案（最小新增面）

- **進 corrections-weekly**（改月檔格式，加三行）：過度工程類趨勢句、parity 殘留數、零消費 delta。無新 skill、無新排程。
- **進 state-review**（強化既有 `:23`）：gate 候選「第二次出現」→ 自動成為升溫觸發輸入（接 Q2）。dry-run 不進 state-review（A 軸機器 vs 消費者視角分離，守 codex 不合併線）。
- **execution-plan skill 加一行格式**：kill criteria 子句（Q3-1）＋POC timebox 欄。skill 編輯，非新機制。
- **新建（僅二，皆輕）**：(a) friction/workaround append-only 輕量入口（單檔，低儀式）；(b) dry-run 日曆保底掛 deep-work 劇本（codex `:258-266` orchestration 位）。
- **明確不建**：`deep-review-arc` skill（codex `:231-256` 已否決——無新 ontology，另開即下一批 drift）、state-review 與 arc-review 合併（`:274-284`）、常駐 telemetry（draft-11 暫緩邏輯：先 deterministic gates，再量 residual，verdict §1）。

## 方法論限制

1. 本腿未讀 28 findings 原文與 fix diffs——能裁的是機制設計與觸發規則，不能為「每條修對」背書（同 codex `:479-485` 的自我設限，本腿繼承）。
2. Q3 的「無 repo-local 止損案例」是 rg 結論，但 CJK 檢索在本次 słonecznie 回空多組（含 `POC|kill|等級|停止` 在 ep-validate 面回空，而 execution-plan 面同類查詢有命中——檢索面本身不均勻），應讀作「未建檔或未被我找到」，不是「沒發生過」。
3. usage 數字全是 ~30 天窗（usage-fit `:17,30-35`）、corrections 只覆 ZCode 面（`:74`）、Muse 端一切 unverified（usage-fit `:35`）——感測器 1、4 的外推上限。
4. dry-run 是 sampling evidence（codex `:210`）；六腿非統計獨立（`:483`）——跳躍機制 2、4 的結論只能是「收斂訊號」，不是 proof。
5. 本討論為 muse 腿單發 READ-ONLY 產出，未經 in-family judge 與跨家族否證——按 state-review 迴路（`:24` 防全採否證至少一項），至少需一次對立審查才可進 EP。

