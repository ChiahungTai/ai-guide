# Usage × 適配度審計——ai-guide skills/rules/hooks 實際使用證據與工作流適配（self-contained 報告）

> ⚠️ **更正（2026-09-17，sess_b25cf458 反轉後補記）**：本報告 §「ZCode 端零 fire」相關結論（原 :18、:148——「518 筆全 source=claude／ZCode hooks 從未 fire」）**已失效**：根因＝`hooks/memory-write-sensor.py:48` 硬編 `"source": "claude"` label——ZCode hooks 一直在 fire（event log 393 筆 64/64 session join 實證）。真盲區＝背景蒸餾器寫入（非 tool call，架構上不觸發 PostToolUse）。修復＝AIR-100 S1（`--source` 註冊端顯式傳入）。引用本報告 sensor 歸因數據者以本更正為準。

> 產出：2026-09-17 02:0x–03:xx（02:01 排程 deep-work 自主弧，report-only——零 commit、零 skills/rules/hooks 修改、零卡面變更）。
> 觸發：user 2026-09-16 23:09 原話——「檢查目前每個 skill 是否都有被使用，派一個 flash agent 去查看看對話紀錄……跑之前跟 codex 建議，我覺得目前應該有些不需要 rules/skills/hooks；另外每個 skills 也要檢查是不是有跟目前工作流程不搭，例如 /at overhead 是不是太大……最後請 5.3 去做統整跟分析，然後跟 codex 討論後出一個 self-contained 的完整報告」。
> 執行鏈：codex 設計審（job-mu4evo0v）→ flash 統計腿（lite-verify/glm-5.3-flash，唯讀掃三家對話紀錄）→ GLM 5.3 統整（native）→ codex 結論討論（job-mu4fy1g0）→ 本報告。
> 姊妹文檔：同目錄 `README.md`（框架＋八議題）、`dispatch-plan.md`（第一波腿規格）、`_tasks/0917-guides-refactoring/ep.md`（AIR-115 EP，In Progress——本報告與其正交：usage 證據軸是第一波未覆蓋的增量）。
> 證據檔（raw）：`.agent-tmp/usage-audit/{usage-matrix.md, codex-design-prompt.md, codex-design-reply.md, codex-conclusion-prompt.md}`＋抽取腳本同目錄（`.agent-tmp` 7 天清理——本報告已內嵌全部關鍵數字，raw 檔消失不影響自足性）。

---

## 0. TL;DR——十條結論

1. **82 支 skills 中 77 支在 30 天觀測窗內有 confirmed consumption**（explicit invocation〔Skill 呼叫／slash〕或 direct read 任一）；嚴格零 invocation 且零直讀者 5 支中，**唯一非 young 的真零消費支是 `flow-feedback`**（lint-fix／python-type-gap／swing-analysis 有 Read 直讀＝confirmed consumption；tool-discipline 建檔才 2 天）。術語：**explicit invocation**（Skill tool／slash）與 **confirmed consumption**（含 direct read）分開報——direct read 可能是審查/稽核，「被消費」可確認、「被用來完成任務」不能一概確認（codex 結論討論定案）。
2. **user 的直覺部分成立**：確實存在零／低用支（flow-feedback、frontend-ui-engineering 等），但 **沒有任何「高用卻被標退役」的反例**——usage 證據與第一波 M-A 語義判讀零衝突，且強化了 4 支既有 retire-candidate（swing／upgrade-nt／upgrade-sj／現代 CLI 偏好 rule）。新增候選採保守級：flow-review **不與** flow-feedback 綁 pair 退（45 讀＋聚合器責任在場——評估 orphan/re-point-producer）；UI 三支責任互異（建構規範／互動協作／驗收），低用≠重複。
3. **三源觀測窗都只有 ~30 天**（ZCode DB 08-17 起、CC 預設 30 天輪替、codex 08-18 起）——所有「零用」結論必須讀作「30 天窗內零」，不是史來零；90 天口徑實際退化為 30 天。
4. **三家消費形態結構性不同**：ZCode＝Skill tool 呼叫驅動（2,173 次／54 支）、codex＝讀檔驅動（11,595 次讀／73 支）、CC 幾乎停用（23 次／15 支）——工作重心已實質移到 ZCode＋codex；skill 的「使用」在 codex 端以路徑消費形態存在，任何 usage 統計只看 invocation 會系統性漏報。
5. **`/at` 是「高用＋成本結構問題」不是「該退役」**（37 呼叫＋21 slash＋46 讀）：AIR-77 已把 at-context 收斂到任務目標；實測殘餘 overhead 是**三重投影**——本弧排程時同一份 read-set 手寫三遍（at-context 檔＋STATE.md 起手點＋cron prompt），Phase 0 對 EP／卡 notes 雙寫，Phase 3 模板內嵌 resume 步驟與 task-recovery 單一源重複。三個減量提案見 §5.1。
6. **hooks 面——初版「ZCode sensor 零 fire」假說已被 negative control 否證（audit trail 保留）**：初版解讀「JSONL 518 筆全 claude → ZCode 端 sensor 靜默 no-op」是錯的——次日 morning session 實跑探針（ZCode session Write 池條目）證實 **sensor 對 ZCode session 正常發射**，真正的問題是 `memory-write-sensor.py:48` 的 `"source": "claude"` **硬編碼**——全部事件（含 394/521 筆 `sess_` 前綴＝ZCode session）都被標成 claude。夜波 T4-1 的「ZCode 感測覆蓋 31-33%」數字建立在此歸因 bug 上，需 re-derive。修法＝一行（source 依 session_id 前綴推導）＋ T4-1 口徑重算——歸 AIR-100。
7. **rules 無 invocation 概念**（always-on 注入），usage 軸不適用；其處置已由第一波 M-A 判讀＋AIR-115 S1.3（working tree 未 commit）承接——本報告不重複裁決，僅補一個結構觀察：三支工具路由 rules 的 reference-pair skills 全部零 invocation（屬讀檔消費層，by design）。
8. **instruction-testing 的 keep 維持**：7 天 1 呼叫＋101 讀——非零消費，M-A 三條失效條件（含「連續兩 audit 週期零消費」）皆未觸發。
9. **清單數機械勘誤：82 支非 84**（`ls -d skills/*/` 83 目錄含 `_common`；AIR-113 卡面同為 82；框架 README §3.2 的「84 支」為 stale 數字）。
10. **處置權歸屬不變**：usage 是 evidence modifier 非 owner——本報告所有建議都是提案，逐支 disposition 仍走 AIR-113（skills）／AIR-100（memory/hooks）／接續鏈小卡（/at）。

---

## 1. Corpus coverage & confidence

| 源 | observable 窗 | 量 | gaps |
|---|---|---|---|
| ZCode telemetry sqlite（3.5GB） | 2026-08-17 → 09-17 | 3,346 sessions（interactive 773／subagent 2,540） | DB 僅 ~31 天；更早 ZCode 使用不可見 |
| Claude Code jsonl | 2026-08-17 → 09-16 | 94 jsonl／18 專案目錄 | `settings.json` 無 `cleanupPeriodDays`＝**預設 30 天輪替**——舊 session 已消失 |
| Codex sessions | 2026-08-18 → 09-17 | 1,283 rollout 檔 | 目錄只從 08-18 起 |
| Muse | — | 無本地 log | **82 支全數 unverified**（不腦補） |

**信心二分標註**（codex 結論討論定案）：
- **Confirmed in observable window**（一次 confirmed event 即足以反駁「未使用」）：某支「30 天內曾被 invocation/read」的存在性判斷；flow-feedback 零直接消費；instruction-testing 已有消費；`/at` 明確仍在使用；82 支計數。
- **Single-window observation (~30d)**（不可外推 90d 或歷史生命週期）：頻率高低、calls/day 排序、梯隊劃分、CC 幾乎停用、趨勢類敘述。
- **High-confidence hypothesis → 已裁定**（negative control 實跑翻案）：初版「ZCode sensor 靜默 no-op」假說被探針實驗否證——sensor 正常 fire，`source` 欄位硬編碼 `"claude"`（sensor.py:48）才是事實；詳見 §5.3 更正版。
- **unverified**：Muse 端一切。

## 2. 方法（usage taxonomy）

三層證據分類（codex 設計審 job-mu4evo0v 定案，本弧遵守）：

| 層 | 定義 | 計入 calls？ |
|---|---|---|
| **executed** | ZCode `Skill` tool 呼叫／CC tool_use `name="Skill"`／CC user slash（`/name` 或 `<command-name>`，僅 user 本體）／codex 讀取命令把 `skills/<name>/SKILL.md` 當目標 | ✅ |
| **referenced** | 路徑或名稱文字提及（含 cron prompt 指名、tool output/diff 內路徑）——無讀取/呼叫 | ❌（另列） |
| **exposed** | skills 清單 desc 注入（每 session 皆然） | ❌（不逐支計） |

**本弧統整時的一處校正（codex 雙輪確認）**：統計腿依規格把「ZCode Read 工具直讀 SKILL.md」放 notes 不入 exec 欄；統整層將 `zcode_read_direct` 與 `codex_read` 對稱升級為 **confirmed consumption** 同層證據，但與 **explicit invocation**（Skill tool／slash）分欄分詞——兩者是不同事件模型，絕對數不可跨 harness 互比排名，只在「有沒有 confirmed consumption」時取聯集。此校正改變零用清單解讀：嚴格零 invocation 的 5 支中，3 支（lint-fix 6 次、python-type-gap 3 次、swing-analysis 3 次）實為低消費。

其他口徑：視窗＝now−90d（三源起點皆晚於此 → 90d 欄≡lifetime 欄≡~30 天窗）；`first_observed`＝git `--diff-filter=A`（49 支直查＋33 支 `--follow` 追搬遷）；`eligible_days=min(90, age)`；前綴碰撞（code-review／code-review-and-quality）以 `/SKILL.md` 錨定＋lookahead 斷尾；`skills/_common` 命中（codex 端 27,828 次）全數排除。Muse 常用字污染（`commit` 出現於 1,661/10,068 sessions）只影響 referenced 參考欄，exec 欄不受影響。

**統計腿自檢**（ lite 產出經主 session 抽驗）：at=37、usage-ping=17、model-routing=48、flow-feedback=0、frontend-ui-engineering=1 逐項 SQL 覆核吻合；per-skill 加總==事件總數（aggregate assert）；CC `<command-name>` 18 命中中 8 個位於 tool_result 引用 blob 已排除；零用 5 支經第二方法（原版 SQL＋rg -F）三重核對。

## 3. 82-skill usage 矩陣（核心數據）

### 3.1 總量與分佈

- confirmed use（exec＋讀消費）：**77/82 支**；嚴格 exec 零用 5 支（見 §3.2）；完全零消費（無 exec 無直讀）**僅 flow-feedback**（非 young）。
- 總量：zcode exec **2,173**（54 支；out-of-scope 103 次為 plugin skills 不計）｜cc exec **23**（15 支；tool 13＋slash 10）｜codex_read **11,595**（73 支）｜codex mention 168,007（referenced 層）。
- actor：subagent 僅 4 事件（zcode 3＋cc 1）——**消費 99.8% 來自主 session**，registry agents 的 skill 消費可忽略（spawned agent 吃 spawn prompt 不吃 skill 清單）。

### 3.2 零用／低用清單（核心產出）

**嚴格零 exec（5）**：

| skill | age | 直讀證據 | 統整層判定 |
|---|---|---|---|
| flow-feedback | 93d | **無**（mention 248） | **唯一完全零消費且非 young——retire-candidate** |
| lint-fix | 220d | Read 6 次 | 低用（讀消費在場）；併入候選 |
| python-type-gap | 125d | Read 3 次 | 低用；併入候選 |
| swing-analysis | 127d | Read 3 次 | 低用；M-A retire（遷 mosaic）強化 |
| tool-discipline | **2d** | 無 | young——不可判（reference-pair 新建檔） |

**低用（lifetime ≤2 非 young）**：frontend-ui-engineering（146 天、life=1、直讀 7）——**retire/merge candidate**；UI 三支群（ui-collab 1、ui-visual-verify 1〔young 18d〕）整群用量結構性低。

**young 保護清單**（age<60d 不進零用判據）：tool-discipline(2d)、conversation-dispatch(1d)、bridge-dispatch(2d)、state-review(11d)、cross-verify(12d)、diagram-selection(11d)、instruction-testing(7d)、modern-cli-preference skill(13d)、symbol-query-routing skill(27d) 等——其中多支是近期治理弧產物，零 exec 是「沒機會用」不是「沒用」。

### 3.3 高用端（對照）

| 梯隊 | skills（lifetime exec＋讀） |
|---|---|
| 熱區 | model-routing（48+1092，18d）、review-engine（0 exec+1029 讀）、arch-thinking（152+661）、code-review（106+680）、post-build（264+393）、memory-audit（22+581）、execution-plan（128+407）、instruction-writing（40+431） |
| 主鏈 | implement（123+354）、commit（246+194）、ep-review（50+328）、kanban-board（61+300）、judge-review（94+239）、handoff（191+101）、consistency（192+42）、deep-work（57+64）、at（37+46）、rebase（48+19） |

### 3.4 完整 82-row 明細

見附錄 A（本報告內嵌，源＝`.agent-tmp/usage-audit/usage-matrix.md`，掃描時點 2026-09-17 02:09）。

## 4. Usage × disposition 衝突矩陣

**結論：零衝突**——沒有「高用卻被 M-A 標退役」的支；usage 證據對既有 disposition 只強化不推翻。逐列：

| skill | M-A 標籤（第一波） | usage 實測（30d） | 矩陣判定 |
|---|---|---|---|
| swing-analysis | retire（遷 mosaic） | 0 exec＋3 讀 | ✅ 強化——遷出成本低（幾乎無人用） |
| upgrade-nt | retire（遷 mosaic） | 0 exec＋4 讀 | ✅ 強化 |
| upgrade-sj | retire（遷 mosaic） | 1 exec＋10 讀 | ✅ 強化 |
| nt-v1-query | 保留＋既定 sunset | 1 exec（young 31d） | ✅ 支持 sunset 既定方向 |
| nt-query | 保留＋desc 瘦身 | 0 exec＋4 讀 | ➖ 中性（保留理由是觸發詞 distinctive 非用量） |
| trading-analysis | 保留＋清 mosaic 殘留 | 0 exec＋17 讀 | ➖ 中性偏弱（S1.2 已在 AIR-115 working tree 清殘留） |
| kbar-form-analysis | 保留 | 3 exec＋3 讀（young 16d） | ➖ 中性（young） |
| instruction-testing | keep＋三失效條件 | 1 exec＋101 讀（young 7d） | ✅ keep 維持——非零消費，失效條件③未觸發 |
| flow-feedback | （M-A 未涵蓋——Group D） | **完全零消費** | ⚠️ **新增 retire-candidate**（usage 軸首例自主發現） |
| frontend-ui-engineering | （M-A 未涵蓋） | life=1（146d） | ⚠️ **新增 merge/localize candidate（保守級）**——UI 三支責任互異（frontend＝Panel/Bokeh 建構規範、ui-collab＝互動協作、ui-visual-verify＝驗收），低用不能證明重複 |
| lint-fix／python-type-gap | （M-A 未涵蓋） | 0 exec＋6/3 讀 | ⚠️ 低用——AIR-113 逐支時併「併入鄰近」（fix-test／debugging-and-error-recovery）選項；前提＝保住獨特 lint/type recipes |
| flow-review | （Group D 對偶） | 0 exec＋45 讀＋4 直讀 | ➖ **不與 flow-feedback 綁退**（codex 保守級）——聚合器責任在場，獨立評估 orphan／re-point-producer |

**「零用但 protective/keep」衝突列**（codex 提醒的形態）：唯一接近的是 tool-discipline skill（2d young）——young 保護優先，無實質衝突。

### 4.1 跨題材發現（codex 結論討論補強版）

- **三家消費形態不對稱＝「需求 × 載具行為」的混合測量**：codex 讀檔（11,595）與 ZCode Skill 呼叫（2,173）**不是同一事件模型，絕對數不可跨 harness 排名**——矩陣保留 invocation／read／mention 三軸，只在「有沒有 confirmed consumption」存在性判斷時取聯集。`review-engine`（0 invocation／1,029 讀）、`cr-query`（0／513）、`code-review-and-quality`（0／436）、`validation-strategy`（0／144）這些「零 invocation」支在 codex 端是高消費 reference 文檔——**任何「沒人用」判斷若只看 invocation 會系統性誤殺 reference 層**。
- **低用 ≠ 低 fit——需要 opportunity denominator**：upgrade／UI／subagent 類 skill 本來觸發機會稀少（subagent 全窗僅 4 事件）。零低用證據必須搭配「窗口內是否真的出現過其適用任務」判讀——upgrade-nt/sj 的適用任務（NT/SJ 升級事件）30 天內本就罕見，零用是「沒機會」與「沒人要」的疊加，遷出決策權仍在 M-A 的 scope 論證（層級硬閘），usage 只是降低遷移成本預期。
- **反向也成立——高 read 可能內生**：高讀數可能由 instruction 自己要求 agent 去讀（如審查腿 read-set 指名）而內生生成；「高用」只證明 exposure 不證明設計值得保留。高用支（model-routing 等）的保留理由仍是其職能，usage 只否證「沒人用」。
- **CC 實質停用**（23 次/30d，多為排程 automation 產生；Single-window observation）——共用 corpus 維護成本仍合理（單一源部署），但 CC-only 行為假設在統計中權重極低。
- **subagent 不吃 skills**（4 事件）——skills 的消費者是主 session；spawn prompt 注入方法論才是 subagent 的知識通道。

## 5. Deep dives

### 5.1 `/at` overhead（user 點名首例——「現在都有 backlog.md 開卡，不需要這麼多背景資料寫到 at context」）

**使用度**：at 在場且高用——zcode 37 呼叫＋21 user slash＋19 直讀＋codex 46 讀；usage-ping（搭檔）17 呼叫。問題不是存在性，是**成本結構**。

**現行形態已是第二次收斂後的產物**：AIR-77 已實施「先結算再排程」——checkpoint 進 durable 載體（EP 進度節／卡 notes），at-context 只記任務目標（ephemeral）。user 的擔憂（背景資料灌進 at-context）在**常規路徑已解**。

**實測殘餘 overhead＝三重投影＋雙寫＋模板重複**（本弧自身就是測量樣本）：

1. **同一份 read-set 手寫三遍**：本弧排程（2026-09-16 23:1x）時，「讀什麼接續」寫了三處——at-context 檔（步驟 0 read-set）、STATE.md（「下次起手點」＋「接手 read-set」兩節）、CronCreate prompt（步驟 2）。三處皆手工維護、無機械單一源；任何一處過時就是 drift 面。at-context 檔本體 6,698 bytes，其中約半數與 STATE/cron prompt 重疊。
2. **Phase 0 雙寫**：有 EP 又有卡時，at SKILL 要求 EP 進度節 append **＋**卡 notes append——違反 task-recovery 單一源原則（「已有欄位不重抄——owner 只留指針」；卡 notes 應只留「進度見 EP §X」指針）。
3. **Phase 3 模板內嵌 resume 步驟**：CronCreate prompt 模板硬編 read-set＋fallback 行為，與 task-recovery（自稱單一源，at SKILL :131 也這樣宣稱）及「Resume 後的行為」節三處同義重複。

**減量提案（三項＋保留條款）——〔已落地〕**：user 拍板後經 codex＋muse 雙家族設計討論（`/at` 優化工單，codex job-mu4lsfk8＋muse job-mu4lsfle）收斂為最終形態，**同日互動 session 已改寫 `skills/at/SKILL.md`**（working tree，待 commit）：
- **P1｜卡 notes 指針化**：Phase 0 改為「EP append＋卡 notes 一行指針」——對齊 task-recovery「owner 已有就不重抄」（task-recovery.md:29-33），零風險。
- **P2｜cron prompt 模板收斂＋bootstrap capsule 保留**：模板縮為「task identity／context path＋讀 task-recovery＋接續」骨幹，但**保留 /at 特有兩條不藏進 generic recovery**——①既有 outward authorization 失效條款（resume 卷授權重置）②missing-pointer fail-loud（context 檔缺失時產出狀態報告不靜默）。read-set 只住 at-context 一處，STATE／cron prompt 都指它。
- **P3｜UC 級任務「要求已有卡」而非由 /at 建卡**：排程時任務若達 UC 級，應已有卡（user／排程 session 先建——豁免①允許），at-context 正文壓成一行目標＋EP/卡指針；**/at 本身不得因排程而額外建卡**（副作用禁令）。把「規格載體」職責交給卡 desc/EP。本弧 6.7KB context 檔就是反例樣本（排程時無卡可用——正是 P3 要堵的形態）。

### 5.2 「零用但 keep」檢驗——instruction-testing

M-A keep 的失效條件③是「連續兩 audit 週期零消費觀測」。實測：建檔 7 天內 1 次 Skill 呼叫（09-16）＋101 次 codex 讀——**非零消費**，條件未觸發。keep 維持；usage 軸無新動作。（此列展示 conflict row 的正確處理：usage 不推翻語義判讀。）

### 5.3 hooks——「註冊在場但零作用」實測

F-C wiring 矩陣（12 rows）已 mapping 註冊面；本弧補上**發射面實測**（hooks 的「usage」＝真的 fire）：

- **memory-write-sensor（PostToolUse，CC+ZCode 雙註冊）——〔更正版〕**：事件 log `~/.local/share/ai-guide/memory-hook-events.jsonl` 521 筆（09-09 起）。初版解讀「100% claude → ZCode 端零 fire／靜默 no-op」**已探針否證**：morning session 於 ZCode 內 Write 合法池探針條目，3 秒內 JSONL 即出現本 session（`sess_d3890708`）事件——**sensor 對 ZCode 正常發射**。真相＝`hooks/memory-write-sensor.py:48` `"source": "claude"` **硬編碼字面值**（AIR-56 CC-only 時代遺留）——521 筆中 394 筆帶 `sess_` 前綴 session_id＝ZCode session 事件，全被誤標 claude。**衍生影響**：夜波 T4-1「ZCode session 寫入的 hook 感測覆蓋 15/46、28/89（31-33%）」兩晚數字以此歸因為前提，需以修正後 source 重算（真實缺口可能遠小於 67%，或本質是 file-path matching 而非 harness 歸因問題——待 re-derive）。修法一行（`source` 依 `session_id` 前綴 `sess_` 推導）——歸 AIR-100；本弧 report-only 未動 hook 程式碼。
- **block-memory-index-write（PreToolUse）**：無發射 log（設計上只 exit 2），静态不可測發射率；其實際攔截面由 M-D coverage matrix 持有（subagent/teardown/Bash redirect＝gap）。
- **memory-index-regen（Stop）**：索引持續新鮮（MEMORY.md 投影運作中）＝間接發射證據。
- **watch-seed／dirty-sensor（CC-only）**：live firing 未驗（F-C #6）。

**處置建議**：negative control runtime 實驗（在 ZCode session 對池條目做一次 Edit → 觀察 JSONL 是否記 zcode 事件）列入 AIR-100 開工 runtime validation 清單首位——半小時內可判定「不 fire」vs「fire 但 filter 掉」，兩者修法不同（registration 修 config vs filter 修 payload 解析）。

## 6. rules 面（usage 軸不適用——處置已在軌道上）

rules 是 always-on 注入（bundle），無 invocation 概念——usage 統計對 rules 的唯一對應是「被 pointer/引用」（F-A inbound 已測）。現況：三支工具路由 rules 的處置（symbol-query-routing 權威保留／tool-discipline pointer 化／modern-cli-preference 退役候選）已由 AIR-115 S1.3 實作在 working tree（未 commit、等 user gate）——本報告不重複裁決。**一個結構觀察**：三支 rules 的 reference-pair skills（symbol-query-routing／modern-cli-preference／tool-discipline skill）全部 0 exec、純讀檔消費（153／29／— 讀；tool-discipline 2d）——reference 層的價值本來就是「被指到時可讀」，0 exec 是 by design 非 unused 信號；但每支仍付 desc 注入常駐成本（AIR-113 逐支時可併考量）。

## 7. 建議處置表（全部 proposal——執行權在 user／owning 卡）

| # | 標的 | 建議 | 證據 | owner |
|---|---|---|---|---|
| 1 | flow-feedback | retire——**〔已執行〕**同日 user 拍板移除：刪 `skills/flow-feedback/`＋CLAUDE.md 索引行＋flow-review 三處指針改「素材手寫進池」（working tree 待 commit）；`ai-analysis/flow-feedback/` 目錄與結案歸檔機械不動（引用目錄非 skill） | 93 天零 invocation＋零直讀（唯一非 young 真零消費） | user 直令＋AIR-113 記錄 |
| 1b | flow-review | **獨立評估**（不綁 pair 退）：orphan 或 re-point-producer 兩案 | 0 invocation 但 45 讀＋4 直讀＋聚合器責任 | AIR-113 |
| 2 | frontend-ui-engineering | merge/localize candidate（保守級）——UI 三支責任互異，逐支驗重複性後再動 | 146 天 life=1 | AIR-113 |
| 3 | swing／upgrade-nt／upgrade-sj 遷出 | 維持 M-A 遷出方向（usage 強化） | 0-1 exec | AIR-113（AC#2） |
| 4 | lint-fix／python-type-gap | 不單獨退役；逐支時併「併入 fix-test／debugging」選項（前提＝保住獨特 lint/type recipes） | 0 exec＋6/3 直讀 | AIR-113 |
| 5 | instruction-testing | keep 維持（無動作） | 7d 內 1 exec＋101 讀 | 原 M-A 標籤不變 |
| 6 | /at 減量三提案 | **〔已執行〕**codex＋muse 雙家族設計討論後落地：bootstrap ticket（固定骨架禁散文、task_ref/owner_ref 指針）＋8 行 cron capsule（兩條 invariant 標記：授權失效＋fail-loud；task_ref 刻意雙寫防清淤單點）＋刪檔時機改「恢復成功且完成或 re-checkpoint」＋board 無權不寫指針＋「/at 不建卡」；token 估計 resume 省 50-75%、排程端降至百 token 級 | §5.1＋雙家族回函（`.agent-tmp/usage-audit/`） | 已改寫 working tree，commit 等 user |
| 7 | ZCode sensor 歸因修正 | **negative control 已跑——假說翻案**：sensor 正常 fire，`source` 硬編碼 `"claude"`（`memory-write-sensor.py:48`）才是 bug；修法一行（依 `sess_` 前綴推導）＋夜波 T4-1 覆蓋數字 re-derive | 探針實驗＋394/521 `sess_` 事件（§5.3 更正版） | AIR-100 |
| 8 | README「84 支」→82 勘誤 | 框架 README §3.2 數字修 | `ls -d skills/*/`=83 含 _common | 順手改（本弧 report-only 未動） |
| 9 | usage 矩陣再生產 | 抽取腳本（`.agent-tmp/usage-audit/`）如需週期重跑可歸檔 `scripts/` | — | AIR-113 認養與否 |
| 10 | 矩陣餵 AIR-113 開工 | 本報告 §3/§4 作為 AIR-113「82 支逐支處置」的 usage 證據輸入 | — | AIR-113 |

## 8. Rejected alternatives（考慮過而不採）

- **全史掃描**——三源皆有硬上限（CC 30 天輪替最短）；無 pre-rotation export 可用，接受 30 天窗＋明確標註。
- **把 desc 注入／文字提及計入 usage**——exposure≠use（codex 設計審定案）；避免「被看到」冒充「被使用」。
- **重設計 /at**——AIR-77 已收斂 at-context；殘餘問題是指投影重複，用指針紀律解，不推翻現行形態。
- **usage 直接判退役**——usage 是 evidence modifier；零用＋keep 的衝突列（tool-discipline young）示範了為何不能單軸獨裁。
- **為 Muse 造統計腿**——無本地 log，任何數字都是腦補；維持 unverified 標註。

## 9. 後續卡候選（供 user 拍板，不執行）

1. ~~/at 減量小卡~~ → **已執行**：雙家族討論收斂後同日改寫 `skills/at/SKILL.md`（見 §7 #6）——commit 等 user gate。
2. **AIR-113 開工輸入包**：本報告 §3.2/§4 矩陣＋§7 #1-#5 處置建議——AIR-113 已是「82 支逐支處置」owner，不需新卡，只需把本報告掛進 refs（board 寫入=user 拍板，board single-writer）。flow-feedback 移除＋flow-review 指針已先行落地。
3. **AIR-100 後續**：sensor `source` 歸因修正（一行）＋夜波 T4-1 覆蓋數字以修正後 source re-derive（§5.3 更新版）。

## 10. 附錄 A——82-row 完整矩陣（2026-09-17 02:09 掃描）

> 欄：skill｜zcode_exec（≡90d≡life，30 天窗）｜cc_exec｜codex_read｜codex_mention｜last_used｜first_observed｜age_days｜eligible｜calls/eligible_day｜actor(m/s)｜flags｜notes。零用排最前，餘按 lifetime 降冪。

| skill | zc_exec | cc_exec | cx_read | cx_mention | last_used | first_obs | age | elig | c/e_day | m/s | flags | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| flow-feedback | 0 | 0 | 0 | 248 | never | 2026-06-16 | 93 | 90 | 0 | 0/0 | reference_only | 無任何直接消費 |
| lint-fix | 0 | 0 | 0 | 291 | never | 2026-02-09 | 220 | 90 | 0 | 0/0 | reference_only | read_direct=6 |
| python-type-gap | 0 | 0 | 0 | 373 | never | 2026-05-15 | 125 | 90 | 0 | 0/0 | reference_only | read_direct=3 |
| swing-analysis | 0 | 0 | 0 | 342 | never | 2026-05-13 | 127 | 90 | 0 | 0/0 | reference_only | read_direct=3 |
| tool-discipline | 0 | 0 | 0 | 16 | never | 2026-09-15 | 2 | 2 | 0 | 0/0 | young | reference-pair 新建 |
| model-routing | 48 | 0 | 1092 | 22421 | 09-17 zc | 2026-08-30 | 18 | 18 | 63.3 | 48/0 | young | read_direct=159 |
| review-engine | 0 | 0 | 1029 | 8725 | 09-17 cx | 2026-06-20 | 89 | 89 | 11.6 | 0/0 | | read_direct=83 |
| arch-thinking | 151 | 1 | 661 | 3721 | 09-17 cx | 2026-06-19 | 90 | 90 | 9.0 | 152/0 | | read_direct=68 |
| code-review | 106 | 0 | 680 | 6628 | 09-17 cx | 2025-10-14 | 338 | 90 | 8.7 | 106/0 | | read_direct=78 |
| post-build | 263 | 1 | 393 | 6599 | 09-17 cx | 2026-08-15 | 33 | 33 | 19.9 | 264/0 | young | read_direct=104 |
| memory-audit | 21 | 1 | 581 | 11932 | 09-17 cx | 2026-08-16 | 32 | 32 | 18.8 | 22/0 | young | read_direct=96 |
| execution-plan | 127 | 1 | 407 | 7395 | 09-16 cx | 2025-10-14 | 338 | 90 | 5.9 | 128/0 | | read_direct=109; slash=1 |
| cr-query | 0 | 0 | 513 | 1984 | 09-16 cx | 2026-07-23 | 56 | 56 | 9.2 | 0/0 | young | read_direct=26 |
| rules-reminder | 1 | 0 | 482 | 1421 | 09-15 cx | 2026-05-14 | 126 | 90 | 5.4 | 1/0 | | read_direct=5 |
| implement | 122 | 1 | 354 | 6256 | 09-17 cx | 2026-04-24 | 146 | 90 | 5.3 | 123/0 | | read_direct=109; slash=1 |
| agent-workflow | 6 | 0 | 466 | 5428 | 09-17 cx | 2026-05-19 | 121 | 90 | 5.2 | 6/0 | | read_direct=35 |
| instruction-writing | 40 | 0 | 431 | 4621 | 09-17 cx | 2026-08-21 | 27 | 27 | 17.4 | 40/0 | young | read_direct=67 |
| commit | 246 | 0 | 194 | 3282 | 09-16 zc | 2026-05-15 | 125 | 90 | 4.9 | 246/0 | | read_direct=43; slash=1 |
| code-review-and-quality | 0 | 0 | 436 | 4502 | 09-15 cx | 2026-04-24 | 146 | 90 | 4.8 | 0/0 | | read_direct=46 |
| ep-review | 49 | 1 | 328 | 3712 | 09-17 cx | 2026-04-24 | 146 | 90 | 4.2 | 49/1 | | read_direct=34 |
| kanban-board | 61 | 0 | 300 | 4700 | 09-16 zc | 2026-06-09 | 100 | 90 | 4.0 | 61/0 | | read_direct=70 |
| deep-thinking | 4 | 0 | 329 | 1988 | 09-16 cx | 2026-08-30 | 18 | 18 | 18.5 | 4/0 | young | read_direct=4 |
| judge-review | 94 | 0 | 239 | 1654 | 09-16 zc | 2026-03-25 | 176 | 90 | 3.7 | 94/0 | | read_direct=23 |
| handoff | 188 | 3 | 101 | 973 | 09-16 zc | 2026-06-26 | 83 | 83 | 3.5 | 191/0 | | read_direct=52; cc slash=2 |
| acceptance-evidence | 1 | 0 | 278 | 2028 | 09-17 cx | 2026-08-21 | 27 | 27 | 10.3 | 0/1 | young | read_direct=37 |
| consistency | 191 | 1 | 42 | 795 | 09-16 zc | 2026-03-16 | 185 | 90 | 2.6 | 192/0 | | read_direct=30 |
| symbol-query-routing | 0 | 0 | 153 | 1119 | 09-17 cx | 2026-08-21 | 27 | 27 | 5.7 | 0/0 | young | read_direct=7 |
| followup-review | 38 | 0 | 110 | 1151 | 09-16 cx | 2026-04-24 | 146 | 90 | 1.6 | 38/0 | | read_direct=19 |
| validation-strategy | 0 | 0 | 144 | 681 | 09-16 cx | 2026-06-19 | 90 | 90 | 1.6 | 0/0 | | read_direct=20 |
| metadata-sync | 36 | 0 | 102 | 1733 | 09-17 cx | 2026-06-29 | 80 | 80 | 1.7 | 36/0 | | read_direct=31 |
| audit-test | 36 | 0 | 101 | 1400 | 09-15 zc | 2026-06-02 | 107 | 90 | 1.5 | 36/0 | | read_direct=32 |
| illustrate | 56 | 0 | 67 | 2263 | 09-17 cx | 2026-06-04 | 105 | 90 | 1.4 | 56/0 | | read_direct=37 |
| deep-work | 56 | 1 | 64 | 1457 | 09-16 zc | 2026-04-22 | 148 | 90 | 1.3 | 57/0 | | read_direct=22; cc slash=1 |
| self-contained-prompt | 2 | 0 | 112 | 561 | 09-15 cx | 2026-06-26 | 83 | 83 | 1.4 | 2/0 | | read_direct=22 |
| corrections-weekly | 1 | 0 | 102 | 2006 | 09-13 cx | 2026-08-30 | 18 | 18 | 5.7 | 1/0 | young | cron 驅動 |
| instruction-testing | 1 | 0 | 101 | 1479 | 09-16 zc | 2026-09-10 | 7 | 7 | 14.6 | 1/0 | young | read_direct=23 |
| code-reality | 6 | 5 | 87 | 8238 | 09-15 cx | 2026-08-22 | 26 | 26 | 3.8 | 11/0 | young | read_direct=131 |
| compact-prep | 33 | 0 | 58 | 364 | 09-15 cx | 2026-08-23 | 25 | 25 | 3.6 | 33/0 | young | read_direct=17; slash=1 |
| at | 37 | 0 | 46 | 1125 | 09-17 cx | 2026-06-12 | 97 | 90 | 0.9 | 37/0 | | read_direct=19; slash=21 |
| debugging-and-error-recovery | 0 | 0 | 74 | 464 | 09-17 cx | 2026-04-24 | 146 | 90 | 0.8 | 0/0 | | read_direct=11 |
| zcode-session-query | 11 | 0 | 62 | 700 | 09-16 zc | 2026-08-23 | 25 | 25 | 2.9 | 11/0 | young | read_direct=24 |
| voice-notification | 1 | 0 | 70 | 369 | 09-13 cx | 2026-02-11 | 218 | 90 | 0.8 | 1/0 | | read_direct=10 |
| fix-test | 1 | 0 | 69 | 1046 | 09-11 cx | 2026-05-22 | 118 | 90 | 0.8 | 1/0 | | read_direct=8 |
| autonomous-execution | 0 | 0 | 68 | 820 | 09-17 cx | 2026-04-26 | 144 | 90 | 0.8 | 0/0 | | read_direct=11 |
| rebase | 47 | 1 | 19 | 1193 | 09-16 zc | 2026-06-08 | 101 | 90 | 0.7 | 48/0 | | read_direct=14; slash=9 |
| test-driven-development | 0 | 0 | 62 | 425 | 09-16 cx | 2026-04-24 | 146 | 90 | 0.7 | 0/0 | | read_direct=7 |
| state-review | 0 | 0 | 58 | 1679 | 09-13 cx | 2026-09-06 | 11 | 11 | 5.3 | 0/0 | young | read_direct=6 |
| sync-sources | 2 | 0 | 48 | 693 | 09-16 cx | 2026-06-22 | 87 | 87 | 0.6 | 2/0 | | read_direct=2 |
| flow-review | 0 | 0 | 45 | 327 | 09-14 cx | 2026-06-16 | 93 | 90 | 0.5 | 0/0 | | read_direct=4 |
| usage-ping | 17 | 0 | 26 | 781 | 09-16 zc | 2026-08-18 | 30 | 30 | 1.4 | 17/0 | young | read_direct=14; slash=1 |
| ui-visual-verify | 1 | 0 | 38 | 581 | 09-15 cx | 2026-08-30 | 18 | 18 | 2.2 | 1/0 | young | read_direct=11 |
| instruction-init | 12 | 0 | 21 | 889 | 09-12 cx | 2026-06-04 | 105 | 90 | 0.4 | 12/0 | | read_direct=21 |
| scan-project | 0 | 0 | 33 | 7424 | 09-13 cx | 2026-06-05 | 104 | 90 | 0.4 | 0/0 | | read_direct=17 |
| tour-bootstrap | 6 | 0 | 27 | 1316 | 09-15 cx | 2026-08-23 | 25 | 25 | 1.3 | 6/0 | young | read_direct=38 |
| blueprint-bootstrap | 3 | 0 | 29 | 701 | 09-12 cx | 2026-08-23 | 25 | 25 | 1.3 | 3/0 | young | read_direct=25 |
| modern-cli-preference | 0 | 0 | 29 | 341 | 09-17 cx | 2026-09-04 | 13 | 13 | 2.2 | 0/0 | young | reference-pair |
| llm-output-convention | 1 | 0 | 22 | 212 | 09-14 zc | 2026-08-30 | 18 | 18 | 1.3 | 1/0 | young | read_direct=5 |
| api-and-interface-design | 0 | 0 | 22 | 267 | 09-16 cx | 2026-04-24 | 146 | 90 | 0.2 | 0/0 | | |
| cross-verify | 0 | 0 | 20 | 694 | 09-14 cx | 2026-09-05 | 12 | 12 | 1.7 | 0/0 | young | read_direct=6 |
| mermaid | 3 | 0 | 16 | 266 | 09-10 cx | 2025-11-20 | 301 | 90 | 0.2 | 3/0 | | read_direct=8 |
| doc-health | 0 | 0 | 18 | 789 | 09-12 cx | 2026-06-09 | 100 | 90 | 0.2 | 0/0 | | read_direct=7 |
| trading-analysis | 0 | 0 | 17 | 321 | 09-17 cx | 2026-06-13 | 96 | 90 | 0.2 | 0/0 | | read_direct=8 |
| daily-maintain | 0 | 2 | 14 | 1452 | 09-10 cx | 2026-06-10 | 99 | 90 | 0.2 | 2/0 | | cc slash=2 |
| debrief | 11 | 0 | 5 | 414 | 09-17 cx | 2026-08-16 | 32 | 32 | 0.5 | 11/0 | young | read_direct=38 |
| instruction-clean | 0 | 0 | 14 | 826 | 09-12 cx | 2026-02-10 | 219 | 90 | 0.2 | 0/0 | | read_direct=1 |
| ep-validate | 10 | 0 | 3 | 201 | 09-13 cx | 2026-06-04 | 105 | 90 | 0.1 | 10/0 | | read_direct=3 |
| instruction-sync | 4 | 1 | 8 | 529 | 09-12 cx | 2026-02-10 | 219 | 90 | 0.1 | 5/0 | | read_direct=2 |
| maintain | 0 | 1 | 12 | 728 | 09-11 cx | 2026-06-10 | 99 | 90 | 0.1 | 1/0 | | cc_tool=1 |
| diagram-selection | 1 | 0 | 11 | 390 | 09-11 cx | 2026-09-06 | 11 | 11 | 1.1 | 1/0 | young | read_direct=7 |
| smell-detector | 2 | 0 | 10 | 1797 | 09-13 zc | 2026-08-16 | 32 | 32 | 0.4 | 1/1 | young | read_direct=4 |
| spec | 6 | 0 | 6 | 255 | 09-09 cx | 2026-04-24 | 146 | 90 | 0.1 | 6/0 | | read_direct=10 |
| upgrade-sj | 1 | 0 | 10 | 266 | 09-11 cx | 2026-06-05 | 104 | 90 | 0.1 | 1/0 | | read_direct=2 |
| standup | 0 | 2 | 6 | 1017 | 09-13 cx | 2026-07-08 | 71 | 71 | 0.1 | 2/0 | | cc slash=2 |
| ui-collab | 1 | 0 | 6 | 212 | 09-15 zc | 2026-05-13 | 127 | 90 | 0.1 | 1/0 | | read_direct=9 |
| kbar-form-analysis | 3 | 0 | 3 | 198 | 09-10 cx | 2026-09-01 | 16 | 16 | 0.4 | 3/0 | young | read_direct=12 |
| bridge-dispatch | 5 | 0 | 0 | 13 | 09-16 zc | 2026-09-15 | 2 | 2 | 2.5 | 5/0 | young | read_direct=2 |
| nt-query | 0 | 0 | 4 | 517 | 09-11 cx | 2026-06-17 | 92 | 90 | 0.04 | 0/0 | | read_direct=2 |
| upgrade-nt | 0 | 0 | 4 | 190 | 09-17 cx | 2026-06-05 | 104 | 90 | 0.04 | 0/0 | | read_direct=2 |
| context7 | 0 | 0 | 3 | 206 | 09-04 cx | 2026-05-13 | 127 | 90 | 0.03 | 0/0 | | read_direct=5 |
| conversation-dispatch | 1 | 0 | 0 | 214 | 09-16 zc | 2026-09-16 | 1 | 1 | 1 | 1/0 | young | read_direct=4 |
| frontend-ui-engineering | 1 | 0 | 0 | 159 | 09-03 zc | 2026-04-24 | 146 | 90 | 0.01 | 1/0 | | read_direct=7 |
| nt-v1-query | 1 | 0 | 0 | 513 | 08-20 zc | 2026-08-17 | 31 | 31 | 0.03 | 1/0 | young | read_direct=5 |

## 附錄 B——codex 兩輪回函

- **設計審**（job-mu4evo0v，chatgpt-web/high，02:0x）：全文收錄 `.agent-tmp/usage-audit/codex-design-reply.md`；要點＝三層 taxonomy／90d+lifetime／corpus coverage 必報／usage=evidence modifier／/at 先驗證現況不重設計／五段報告骨架。
- **結論討論**（job-mu4fy1g0-w0d6oo，chatgpt-web/high，02:37）：全文收錄 `.agent-tmp/usage-audit/codex-conclusion-reply.md`；要點＝①invocation/consumption 分詞＋flow-feedback 判定成立（direct read 可能是稽核的 caveat）②flow-review 不綁退（orphan 評估）、UI 群責任互異保守級、lint/type recipes 保留前提③/at 三提案方向同意＋bootstrap capsule 兩條保留（授權失效條款＋missing-pointer fail-loud）＋/at 不自行建卡④信心二分標註法（Confirmed in window／Single-window／high-confidence hypothesis／unverified）⑤兩個跨題材補充（invoked/read 事件模型不可跨 harness 排名；opportunity denominator——低用≠低 fit、高 read 可能內生）。
