# EP：review 系統演化——雙迴路＋Heat state machine＋跨卡掃描＋kill criteria＋dry-run corpus

- **卡**：AIR-131（owning）
- **日期**：2026-09-18　**baseline**：main@0f6035c8（開工前重確認）
- **狀態**：draft v3（muse＋codex ep-review findings 已全數修入）
- **ep_type：blueprint**——S1-S5 是 bounded child 邊界而非 implementation 級自含段；每段開工前衍生 implementation 級 Planning Contract（引用本 EP＋卡），方符合 execution-plan 對 implementation segment 的自含要求
- **研究依據**：`references/localopt-{muse,codex}-verdict.md`（＋同目錄兩份 briefing）——muse mu64bkv7＋codex mu64bkwm 雙腿＋user 三修（大審不可避免／避免 local opt 是重要方向／卡級審查時間軸盲目）

## 1. 問題與統攝命題

local opt 不是回饋距離問題，是**目標函數從未重新開放**——逐弧凍結決策（「已決策勿重辯」）各自正確、加總成沒人會設計的拓撲（38 項 overhead 每項有事故理由、總和從未被全局設計）。三種 failure 對應三種被拖遠的證據：中途不可行＝feasibility evidence、做完難用＝consumer behavior evidence、local optimum＝alternative-architecture evidence。

**統攝心智模型（勿重辯）**：內圈快證偽、外圈定期解凍。

## 2. 設計總則（已凍結，card Plan ①-⑩）

最小機制集**四件**＋第五件禁令（不為①-④再造 lifecycle/新平台——否則用「防止治理 local opt」製造下一層治理 local opt）：

### 2-1 Heat state machine（含定量初值——拷自 codex verdict L101-126）

五 signal family：R correction recurrence／G ritual growth／V vocabulary divergence／B boundary compounding／U consumer friction。觀察 window＝**最近 8 個治理相關 arcs**。

| 狀態 | Trigger（初值） | 動作 |
|---|---|---|
| **Cool** | 0–1 family active | 正常逐弧工作 |
| **Warm** | 同一 window ≥2 families；或同一 family 連續兩個 window 出現 | 對該 bounded area reheat review；**禁 additive repair 思考、必同時產生 delete/merge/rewrite 候選** |
| **Hot** | ≥3 families；或任一 tripwire | full-system／full-arc review |
| **Cooldown** | review 後連續一段 arcs 無 tripwire 且 <2 signals | 回 Cool |

三 tripwire（不經計分直升 Hot）：①大審找到日常 machinery 沒抓到的 systemic Critical②authoritative semantics 出現互斥定義③≥2 個獨立 consumer dry-run 因同一設計問題失敗。

**但書**：以上固定閾值只是初始控制參數、不是真理（A2 回測可修訂，修訂走 EP amendment）。

### 2-2 cadence hybrid（hybrid 數字同源 codex verdict）

事件觸發＋**12 治理弧 ceiling 起始**（arc 數比日曆好）＋每季 state-review sanity ceiling。escape 定義收緊：escaped Critical＝review 開始前已存在＋現行日常機制沒升格；reviewer 新標準首次套用抓到不算。調節：escaped Critical → `next_interval = max(6, interval × 0.5)`；連續兩輪零逃逸＋coverage 沒降 → `min(24, interval × 1.5)`；其他不變——慢降快升。**review-power guard（四項，全可比才配降頻）**：scope 可比／review taxonomy 可比／fresh-context independence 可比／異構 reviewer 覆蓋沒有縮水。Critical escape 是 thermostat sensor 不是 KPI——禁設「Critical=0」目標（否則 Critical→Important→Suggestion 數字好看系統沒變好）。

### 2-3 kill criteria 入 execution-plan

EP 加 1-3 個 load-bearing assumptions，四欄可否證格式（Assumption/Probe/Kill observation/Action）。spike 用 **evidence budget**（一個假設→一個 disposable spike→最多 2-3 個判別性 probes；**不做 production refactor、不順便把東西做好、UNKNOWN 是合法結果**——到 budget 邊界仍不能證明就是 UNKNOWN，禁「都研究這麼多了不如直接做」的 sunk-cost transition）。**弧終態三態**：DELIVERED／INVALIDATED／SUPERSEDED；**INVALIDATED＝成功終態**（uncertainty retired），成功條件＝原假設→falsifying evidence→kill decision→可重用 learning→**沒有留下半套 production mechanism**；追蹤 cost-to-disproof（會死的方案死得越來越早＝健康）。止損結案語義有別於廢棄（廢棄＝方向錯；止損＝不可行被證偽）。

### 2-4 consumer dry-run corpus

四型任務（cold navigation／normal task／ambiguous-conflict／resume）。控制變數＝**prompt 只描述 consumer goal、禁提示 instruction topology**（否則 discoverability bug 被藏掉）。workaround 比 failure 更有情報量（agent 成功了但自己補了一條路）；**同一 workaround 兩獨立 contexts 再現＝design smell**（跨 repo/harness 更強）。控制面變更弧必跑＋每季 fresh-agent 開工演練保底（enforcement 掛點見 S4）。

### 2-5 跨卡 context 掃描（user 命題：卡級審查時間軸盲目——今天三事故全此形態）

審查準備步四掃：相關卡池／近期同域落地（`git log --since`）／平行在飛 worktree+branch／drafts 向前。兩問（全文）：「近期落地與既有①②③決策重複/衝突嗎？」「④最可能相交的卡，本卡設計讓它更易還是更難？」機械產出 related-work 塊進審查 brief。

### 2-6 code-review --arc mode

method ownership=code-review：scope＝committed baseline..tip＋final-state invariants；multi-leg evidence＋convergence judge＋consumer probes；**risk-driven lanes＋convergence stop 取代固定腿數**——三量＝unique findings/leg＋severity-weighted＋overlap，新腿連續只產已知 finding 即停；不與 state-review 合併（歷史弧「系統被改成什麼」vs 現在態「整體對不對」，兩個問題、cadence 各自獨立）。orchestration 歸 deep-work 劇本。

## 3. Load-bearing assumptions / kill criteria（自我套用 §2-3）

| Assumption | Probe（驗證性工作不計額度；判別性 probe ≤3） | Kill observation | Action |
|---|---|---|---|
| A1：七支感測器全可從既有資料源產訊號（零新基建） | 七支各寫一條示例命令實跑（驗證性，不計 probe 額度）；判別性 probe 針對聚合規則本身 | 感測器**需新基建／新排程**才能產訊號。部分覆蓋條款：僅單 harness 可產（如 corrections 僅 ZCode 面、usage 窗 ~30 天、Muse 端 unverified）＝降級人工判讀欄，**不觸 kill** | 觸 kill 的感測器砍——禁加基建（第五件禁令具體化） |
| A2：Heat 閾值初值在真實歷史資料上不會常態 Hot（常態＝回測窗口內 ≥2 週處於 Warm 以上） | 用既有 corrections 月檔回測聚合一次（S1 驗證段） | 回測常態 Hot | S1 內閉環：重訂閾值一次→再回測；仍常態 Hot → INVALIDATED 聚合面（保留感測器原始輸出），閾值重訂本身走 EP amendment 非棄案 |
| A3：--arc mode 塞得進 code-review skill 現有結構（第五件禁令具體化） | 一版 --arc 段大綱＋一次對照 code-review skill 現有節的套入演練（evidence＝大綱能映射到現有節；不計時） | 映射需要新 top-level 節或新 skill 承載 | **kill/pivot --arc 方案或縮 scope**（如 lanes 進 --arc、invariants 留 state-review）——「新 skill 承載」＝第五件禁令的**重新開放決策，須 user 裁決**，非既定 fallback；禁硬塞出第二 drift 源 |

各 assumption：evidence budget 耗盡且 Kill observation 未觸發＝**UNKNOWN——hypothesis/spike 層的合法結果（非弧終態）**——顯性裁決（加 probe／升級討論／棄），禁 UNKNOWN 自動滑入 implementation（§2-3 已載；滑入＝sunk-cost transition；弧仍須裁決到三態之一）。

## 4. 工作分段（一段一 session 可結算；段落 self-contained）

| 段 | 內容 | 變更檔 | AC 對應 |
|---|---|---|---|
| S1 | Heat 聚合進 corrections-weekly：週報加 Heat 態行（§2-1 表＋tripwire——數字全在 EP 內，無需回讀 verdict）＋A1 七感測器示例命令實跑＋A2 歷史回測；附帶 state-review「gate 候選第二次出現→自動升溫觸發輸入」一行（muse 整合提案，強化既有 :23） | `skills/corrections-weekly/SKILL.md`、`skills/state-review/SKILL.md` | AC①、A1/A2 |
| S2 | execution-plan 加 kill criteria 段：四欄格式表＋evidence budget 條款（含 UNKNOWN 合法＋三不自律）＋弧終態三態＋INVALIDATED 成功條件＋止損結案語義（與 backlog 治理銜接——止損≠廢棄） | `skills/execution-plan/SKILL.md` | AC② |
| S3 | code-review --arc mode 全文：§2-6 全部要素——lanes 三量（unique findings/leg＋severity-weighted＋overlap；新腿連續只產已知 finding 即停）＋cadence 規則（§2-2 數字）＋review-power guard 四項。A3 套入演練先行。細節權威＝卡 Plan ⑧（仲裁 verdict 引文不在 references/——不追外部行號） | `skills/code-review/SKILL.md` | AC③、A3 |
| S4 | 跨卡 context 掃描進 review-engine 審查準備步（§2-5 四掃＋兩問全文→related-work 塊）；deep-work 劇本加**兩行**指針：①arc-risk threshold 觸發 → code-review --arc②dry-run 保底觸發（控制面變更弧必跑＋每季 fresh-agent 演練——enforcement 掛點） | `skills/review-engine/SKILL.md`、`skills/deep-work/SKILL.md` | AC④ |
| S5 | consumer dry-run corpus 檔：四型任務＋控制變數（禁 topology 提示）＋**dry-run 記錄規格用 codex 五量測維度**（Discoverability/Navigation cost/Ambiguity/Prompt repair/Workaround——正式演練儀器）＋workaround 升格規則；friction log 走 **muse 三行格式**（時間＋哪條規則＋怎麼繞的——日常入口低儀式優先，muse Q4；與 dry-run 五維度是兩種儀器不衝突：friction=日常 append-only，dry-run=正式演練記錄）；flow-review 接入口＋自動升 type-2 候選 | 新 `skills/_common/consumer-dryrun-corpus.md`、`skills/flow-review/SKILL.md` | AC⑤ |

每段落地走 **instruction-writing 落地前審查閘**（AC⑥）：classification=boundary（控制面 gate/authority 條文）→ fresh＋intent 分離＋跨家族 external second-opinion 腿（muse/codex，user 已授權額度）；receipt 四欄隨段結算入卡 notes。

## 5. 跨卡對帳裁決

- **AIR-127（波前機械化）**：**獨立平行、不合併、順序無關。**重疊疑慮消解：127 的機械化對象是 memory-audit 收斂波前（`scripts/consolidation_preflight.py`＋`skills/memory-audit/SKILL.md`——card Plan 已凍結掛點），與本 EP 五段變更檔**零交疊**（muse ep-review 機械核查確認：corrections-weekly／execution-plan／code-review／review-engine／deep-work／corpus 新檔／flow-review 無一命中）。先前 handoff 擔心的 corrections-weekly 衝突不存在（127 掛點是 memory-audit）。127 走卡 Planning Contract 直行。
- **AIR-129（審查分級）**：獨立平行 EP（`../0918-air129-review-triage/ep.md`）——檔案面零交疊（129 只碰 instruction-writing 落地閘節）。**唯一跨依賴**：S3 lanes 術語引用 129 分級表，129 未落地則記卡 notes pending 對帳（不阻塞 S3——術語可後續對齊）。
- **AIR-126/128**：已結案，無對帳面。

## 6. 驗收（卡面 AC ①-⑦）

①corrections-weekly 週報含 Heat 態行，**且行為 predicate**：Warm 態輸出必帶 delete/merge/rewrite 候選要求、三 tripwire 各有可判條件、閾值初值與 §2-1 表一致②execution-plan kill criteria 四欄格式表在場，**且條文含** evidence budget／UNKNOWN 合法終態／非 wall-clock 顯式語句③code-review --arc 段在場，**且行為 predicate**：lanes stop 規則可機械判（新腿 findings ⊆ 既有 finding 集即停）、review-power guard 四項齊（scope/taxonomy/fresh-context independence/異構覆蓋）、cadence 數字與 §2-2 一致④跨卡掃描掛點＋兩問全文在審查準備步＋related-work 塊格式可機械產出⑤dry-run corpus 檔在場（四型＋禁 topology 提示＋五維度記錄規格＋friction 三行），**且 dry-run invocation 掛點在 deep-work 劇本在場**（兩行指針——「實際會被觸發」由掛點承載並由本條驗收）⑥每段 instruction-writing 審查閘（boundary 跨家族）回執齊⑦本 EP §5 對帳表在場（127 處置、優先序）。

全量驗證：每段 uv run pytest 零回歸；S1 的 A2 回測輸出進段結算。

## 7. 明示不做（含有意裁剪）

- 不建 deep-review-arc skill（codex 已否決——無新 ontology）
- 不合併 state-review 與 arc-review（歷史弧 vs 現在態）
- 不做常駐 telemetry／architecture health score（Goodhart）
- 不為①-④造新 lifecycle（第五件禁令）
- dry-run 不進 state-review（A 軸機器 vs 消費者視角分離——守 codex 不合併線；保底 enforcement 走 deep-work 劇本，見 S4）
- friction log 棄 codex 七字段格式、取三行（日常入口低儀式優先；七字段的分析需求由 dry-run 五維度規格承載——兩種儀器，非刪功能）
