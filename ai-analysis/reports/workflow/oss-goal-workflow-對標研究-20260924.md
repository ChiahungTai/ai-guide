# OSS goal／workflow 機制對標研究報告（AIR-135.1 前期研究）

- **日期**：2026-09-24（調查與整合同日完成）
- **性質**：AIR-135.1（自動編排器——把卡片規矩編譯成機器可執行派工單）的前期對標研究；整合五條調查腿的原始材料，非剪貼簿——所有結論為跨源綜合判讀，原始 file:line 證據留在材料檔（見 §8 證據索引）
- **材料源**：`/Users/ctai/Github/ai-guide/.agent-tmp/air-135/oss-survey/` 下七份調查檔（詳 §2）
- **讀者假設**：self-contained——不需讀過 AIR-135 系列卡或任何受調 repo 即可全懂；ai-guide 側術語首次出現時給一句定位

---

## 1. 執行摘要

**研究目的**：AIR-135 家族要做的事——使用者目標（card 契約）→ 編譯成計畫（ArcSpec→ArcPlan）→ 編譯成派工單（DispatchSlice）→ 派工執行 → 驗收 → 結算，本質上是自建一個「開發工作流編排器」。在動工前，本調查問一個問題：**成熟的 coding harness（codex／ZCode／grok-build）與 OpenAI 官方實踐文檔，原生怎麼解同一組設計問題？** 八個設計問題（目標→計畫物、派工單、自主邊界與預算、斷線恢復、審查隔離、model routing、人機確認、context 管理）逐題對標。

**方法**：三條源碼機制腿（codex Rust 源碼兩輪、ZCode TS 源碼、grok-build Rust 源碼，各以八題工單外派調查、逐結論附 file:line）＋兩份 OpenAI 官方 cookbook 腿（工作流一文深讀判讀＋repo 全面掃描 14 篇）＋一條說明書腿（四家官方文檔鏡像的 workflow 章節，對出「官方說法 vs 源碼實作」落差表）；另加一條 ZCode 已保存工作流源碼追加腿（保存／參數／作用域／重跑機制＋與 codex 的致敬度快查）。調查日期全部為 2026-09-24。

**三個最重要結論**：

1. **全面同構背書**：ai-guide 的六站模型（entry Align／Shape/Plan／Build／Verify／exit Align／Settle）與 ArcSpec→ArcPlan→DispatchSlice 編譯鏈，在 OpenAI 官方工作流文檔中幾乎逐條找到對應物——連「禁進度流水、只記影響未來工作的發現」這種細節都相同；三家源碼的 plan 契約、fresh-context 審查、journal 恢復、狀態外部化也全部同構。方向不需要改。
2. **機械化確定性檢查是共同壓艙石，也是我們最大的補強面**：ZCode 的 journal replay＋inputHash 校驗、grok-build 的 replay divergence 拒絕恢復＋PLAN_CHANGES 計畫篡改審計＋BudgetLimited 終態，把「已完成不重做」「計畫不被靜默拉伸」「超支即停」從 instruction 紀律升級為機械帳本。我們這三面目前靠 AI 紀律與人類結算，落後一個身位——這是 135.1 設計輸入清單的主體（§6.1）。
3. **一個獨立收斂證據＋兩個反向訊號**：grok-build 的 auto-mode classifier 與我們 outward-action-consent rule 幾乎逐點同構（quote-scope、「結果授權≠手段授權」、工具參數內的准許宣告視為 data）——兩個獨立演化的系統收斂到同一組規則，是強設計佐證。反向訊號一：三家 harness 都**沒有** model escalation、routing 權全收給人類設定（ZCode 甚至明文禁止 caller 指定 subagent model 以防 stale override）——我們的能力推斷 resolver 是反向路線，其代價與收益需自證。反向訊號二：cookbook 的 eval 資產化（graders／資料集／precision-recall）遠比我們的單次 gate 成熟，是最大的能力差距軸。

---

## 2. 方法與參考源

五條調查腿、七份材料檔，全部 READ-ONLY 調查、逐結論附 file:line（材料檔內）、逐腿附自評（淺掃項見 §9）。

| # | 腿 | 材料檔 | 性質 | 對象與日期 |
|---|---|---|---|---|
| 1 | codex 源碼（兩輪：r1 三題＋r2 五題） | `codex-goal-workflow.md` | **源碼機制軸** | `/Users/ctai/Github/codex`（OpenAI codex CLI，Rust `codex-rs/`；注意為演化變體 checkout——review 走 child session＋guardian 模組，upstream `codex-rs/review/` crate 不存在） |
| 2 | ZCode 源碼 | `zcode-goal-workflow.md` | **源碼機制軸** | `/Users/ctai/Github/ZCode`（ZCode harness 本體，TS/JS pnpm monorepo v3.14.0；`core`＝agent 迴圈/權限/workflow scheduler、`dynamic-workflow`＝script→compile→journal engine） |
| 3 | grok-build 源碼 | `grok-goal-workflow.md` | **源碼機制軸** | `/Users/ctai/Github/grok-build`（xAI Grok Build，Rust workspace 約 100 crates，SOURCE_REV=036a5d8；主力 `xai-grok-shell`＝agent/session/goal/workflow） |
| 4 | cookbook 深讀判讀 | `cookbook-iterating-verdict.md`（＋原文存檔 `openai-cookbook-iterating-workflows.md`） | **官方實踐軸** | OpenAI cookbook 〈Iterating development workflows with Codex〉全文深讀（官方 best-practice：源碼給機制、這篇給官方建議姿勢） |
| 5 | cookbook 全面掃描 | `cookbook-full-survey.md` | **官方實踐軸** | openai-cookbook repo 全面掃描（14 篇深讀/大綱：工作流契約、CI 審查、修復閉環、多 agent 編排、eval 飛輪、治理） |
| 6 | ZCode 已保存工作流源碼追加 | `zcode-saved-workflows.md` | **源碼機制軸（追加）** | ZCode saved-workflows 面板對應的源碼（保存/參數/作用域/重跑）＋ZCode vs codex 致敬度快查 |
| 7 | 官方說明書 workflow 章節 | `mirrors-survey.md` | **說明書軸** | `ref-docs/harness/` 四家鏡像（zcode 27 頁／grok-build 24 頁／codex 149 頁抽查 6 頁／claude-code 精讀 2 頁）＋官方 vs 源碼落差表 |

**軸分工**：源碼機制軸×3＋追加×1 回答「機器實際怎麼運作」；官方實踐軸×2 回答「官方建議人類怎麼用」；說明書軸×1 回答「官方怎麼向用戶描述、與實作差多少」。三軸交叉才有 §5 的生態位發現（隱藏能力、文檔落後、marketing 面）。

**注意**：codex 與 grok-build 可能同源演化（工單明令「以本 checkout 為準、勿假設與 upstream 相同」）；ZCode 與 Claude Code 疑似同機制家族（§5.1）。因此「多家都有 X」不必然是獨立收斂——唯一可信的獨立收斂主張是 ai-guide vs grok-build 的 outward-consent（§7）。

---

## 3. goal 軸對照：目標→計畫物

### 3.1 逐家機制

**codex**（源：codex-goal-workflow.md §Q1）——兩套機制並存、無版本化契約：
- **Plan Mode**（collaboration mode，TUI 僅 Default/Plan 兩模式）：模板要求三階段「chat your way to a great plan」——非變異探索→intent chat→implementation chat，直到 spec「decision complete」；期間禁 mutating actions。產出＝文字計畫包 `<proposed_plan>` block（title/summary/API 變更/test cases/assumptions）。中途改目標：修訂必須**整份替換**（「any new `<proposed_plan>` must be a complete replacement」）、無增量機制；模式進出只由 developer message 控制。
- **`update_plan`**：todo/checklist 工具（明註「not plan mode」），`PlanItemArg {step, status}`、三態 Pending/InProgress/Completed；無獨立計畫檔，隨 rollout 事件流落盤。
- 取捨：計畫是「一次成型的文字產物」，改目標＝換整份，沒有計畫與實作的 drift 偵測。

**ZCode**（源：zcode-goal-workflow.md §Q1）——兩級分工、可覆寫 live 文檔：
- **plan mode**：`EnterPlanMode` 免核准／`ExitPlanMode` 強制核准——**計畫必須經 user 點頭才生效**；通過後 atomically 寫 `.zcode/plans/plan-<sessionId>.md`（空 plan 直接拒絕、上限 20,000 chars）；之後每次 session 恢復以 system-reminder 重注入「If this plan is relevant to the current work and not already complete, continue working on it.」
- **TodoWrite**：全量替換式清單，官方定位「rendered to the user as your working plan」；ExitPlanMode 通過後的模型訊息明確指示「Start with updating your todo list」——plan（承諾）→todo（執行追蹤）兩級分工。
- 取捨：**沒有失效機制**——plan 檔原地覆寫、todo 全量替換、「是否仍相關」交給模型自判；不驗 plan 與實作的 drift。另有 session 級 revert（branchCut/rewind）可倒轉訊息。

**grok-build**（源：grok-goal-workflow.md §Q1）——三家中唯一的「凍結契約＋篡改審計」：
- **互動 plan mode**：`PlanModeTracker` 狀態機 Inactive→Pending→Active→ExitPending；Active 時「Write tools are blocked except for the plan file」。
- **自主 goal loop**：`/goal <objective>` 觸發 goal planner agent「run ONCE at goal creation」，把目標編成 plan.md 嚴格契約——Goal kind（code-change/analysis/research）、Acceptance criteria（3-5 條 outcome-based）、Verification plan（每步標 `gating|evidence`）、Non-goals、Assumed scope、Task checklist（3-8 個 checkbox；harness 挖第一個未勾框當下回合 next-step nudge）。核心原則明文「**Specify OUTCOMES, not architecture**」——凍結 HOW 會讓 verifier 駁回正確實作；planner prompt 並假設契約讀者「some of which run on small models」（計畫要為小模型可讀而寫）。
- **中途改目標**：implementer 只能往單一 `## Deviations` 節加 bullet、禁改 plan 原文；對 plan 的編輯被記成 **PLAN_CHANGES diff 交給 verifier**——「A weakened, deleted, or self-serving criterion is itself grounds to refute」；strategist 只准改 HOW 禁碰 plan。
- 取捨：計畫是「可答辯的凍結契約」而非共享草稿——**改計畫本身就是被審計的行為**。

**claude-code**（說明書軸，無源碼腿；源：mirrors-survey.md §任務A·claude-code）：
- `/goal`＝session-scoped prompt-based Stop hook 的包裝：small fast model 逐輪評審三判定（not yet／met／impossible）、resume 全路線還原 goal、錯誤分類（unrecoverable 清 goal／retry／pause＋check-in backoff 至 4 倍間隔）、可 non-interactive（`claude -p "/goal …"`）。
- plan 是權限模式之一；多 agent 兩級（sub-agents＋agent-teams 共享 task list）。
- 與 codex 互證：`/goal` 目標上限 4,000 字兩家文檔相同、每輪外部 evaluator、resume 還原——docs 互證同源（源：mirrors-survey.md §任務C #9）。

**OpenAI 官方實踐**（cookbook；源：cookbook-iterating-verdict.md§逐條同構對照、cookbook-full-survey.md§3）：
- **GOALS.md**：purpose／outcomes／success conditions／scope／non-goals／constraints／known unknowns——outcome-oriented、禁抄實作程序與進度更新。
- **PLANS.md** roadmap＋**phase file**（`harness/build/phase-NN.md`）欄位集：number/title/status/source inputs/objective/in-scope/**explicit non-goals**/dependencies/affected files/**decisions requiring human input**/**approval gate**/RGRC plan/verification commands/**acceptance criteria**/**evidence required before complete**/**handoff stop condition**。
- **`using_goals_in_codex`**：Goal 最強定義六件事——**Outcome／Verification surface／Constraints／Boundaries／Iteration policy／Blocked stop condition**；Goal 是 persisted thread state，model 只能在證據支持時 mark complete，pause/resume/clear/budget 轉移權留在 user。

**ai-guide 對照基準**（供 self-contained 讀者）：entry 六欄契約＝intent verbatim／non-goals／revert 預算／預授權／假設台帳／成功謂詞；card Planning Contract＋slices＋AC；規模三級 simple/standard/full。

### 3.2 同構／差異表

| 維度 | codex | ZCode | grok-build | claude-code（文檔） | cookbook 官方 | ai-guide |
|---|---|---|---|---|---|---|
| 計畫物形態 | `<proposed_plan>` 文字 block＋update_plan 清單 | plan 檔（approved）＋TodoWrite 兩級 | plan.md 契約（goal loop 一次生成） | `/goal` prompt 契約＋task list | GOALS.md＋PLANS.md＋phase file 檔案族 | card 契約＋EP＋ArcSpec/ArcPlan |
| 結構化欄位 | title/summary/API/tests/assumptions | 自由文檔（20K chars 上限） | criteria/verification plan/non-goals/assumed scope/checklist | 未揭露 | 17 欄 phase file（最完整） | 六欄＋slice 欄位 |
| 中途改目標 | 整份替換、無增量 | 原地覆寫＋模型自判相關性 | Deviations 節＋**PLAN_CHANGES 篡改審計** | replace 動作 | phase file 由人審批後才寫 | intent 保持檢查（Intent Review 腿） |
| plan→todo 分工 | plan tool 明訂非 plan mode | ExitPlanMode→「Start with updating your todo list」 | checklist 未勾框＝next-step nudge | task list 共享 | phase 順序執行 | slice 逐卡推進 |
| 計畫版本/hash | 無 | 無（原地覆寫） | 有——編輯即留 diff 供審 | 未揭露 | 版控交 git | 無機制（靠結算） |
| 計畫生效閘 | developer message | **user 核准（ExitPlanMode needsApproval）** | goal 建立即凍結 | session-scoped | 人審 phase 檔＋approval gate 欄 | 人觸發 /execution-plan |

**要點**：三家源碼全部是「plan＋todo 兩級」同構（差別只在 plan 的硬度）；grok-build 獨走「凍結契約＋改計畫即審計」；官方 phase file 的欄位集最完整，幾乎就是機器可執行派工單的欄位範式。

### 3.3 我們六欄契約的定位

**領先處**（不必動）：
- **自治面欄位**：六欄的 revert 預算與預授權，官方 GOALS.md 與三家源碼計畫物都沒有——它們的預算/授權是 harness 設定而非契約欄位（源：cookbook-iterating-verdict.md§逐條同構對照「我們多出預算與預授權欄（它無自治面）」）。
- **intent verbatim**：六欄把原始意圖逐字凍結進契約；grok 只保護「plan 文本不被改」，我們保護「原始意圖不被改寫」——保護對象更上游。
- **規模分級**（simple/standard/full）：cookbook 的 right-sizing 原則（「Do not impose enterprise process when the repository and risk do not justify them」）與我們同構，但它寫進 skill 行為、我們寫進流程分級——方向一致（源：cookbook-iterating-verdict.md§差異）。
- **entry Align 互動釐清**：grok goal loop 明文禁互動釐清（目標須一次給全）、ZCode 靠 AskUserQuestion 限真未決；我們的 entry Align 是獨立站——比 grok 的「一次給全」多一條需求收斂腿（源：grok-goal-workflow.md§終場對照表）。

**可補處**（進 §6.1 借鑑清單）：
1. **PLAN_CHANGES 篡改審計**（grok）：把「計畫文本不可靜默變更」機械化——任何對 ArcPlan/card 契約的修訂留下 diff、交給驗收腿複核，且「弱化/刪除/自利條款本身就是駁回理由」。直接強化 intent-diff 防拉伸。
2. **Iteration policy＋Blocked stop condition 兩欄**（cookbook Goal 六欄）：我們的卡 AC 有 outcome＋驗證面，但 blocked 時「報什麼、什麼能解鎖」無標準格式；迭代政策（改打法前要不要回人）也未明文化。
3. **「evidence required before complete」欄**（cookbook phase file）：把「完成前必須記錄哪些證據」前置寫進 slice，讓驗收閘有逐項可核對的清單。
4. **「outcomes, not architecture」明文原則**（grok planner）：計畫禁凍結 HOW（模組/簽名），否則 verifier 會駁回正確實作——可成為 ArcPlan 寫作約束。
5. **Surprises & Discoveries 獨立節**（cookbook ExecPlan living document 四節之一）：異常發現＋證據 snippet 獨立成節，避免散落 notes 失傳。

---

## 4. workflow 軸對照（七子題）

每題結構：各家做法一覽→張力分析→對 135.1 的啟示。

### 4.1 派工單

**各家一覽**：

| 家 | 派工介面 | 欄位位置 | fail-loud 設計 |
|---|---|---|---|
| codex（源：codex-goal-workflow.md §Q2） | `spawn_agent` tool，子代理＝完整 fork Session | **呼叫端**（模型給）：message/items/agent_type/fork_context/model/reasoning_effort（V2＋task_name）；**無** tool 白名單/工作目錄/產出路欄位——繼承父 model/provider/approval/sandbox/cwd；role 只能「縮減」能力（關 shell/apps/skills） | message/items 二選一不可空；深度上限（預設 1，超限回「Solve the task yourself.」）；threads 上限（預設 6）；未知角色即錯並列 available；model/effort 白名單驗證；子代理強制 approval=Never |
| ZCode（源：zcode-goal-workflow.md §Q2） | Agent tool；dynamic workflow 的 `agent(name,persona).ask<T>(instructions)` | **設定檔**（人類定）：AgentProfile frontmatter 決定 tools 白黑名單/model+thoughtLevel/permissionMode/maxTurns/mcpServers/memory/skills；模型只給 prompt＋類型 | AgentInputSchema 嚴格驗證；SubagentPort 缺席即擲錯不靜默；workflow script 必先 typecheck+靜態分析才准進確認窗；`ask<T>()` 的 T 在編譯期合成輸出 JSON Schema；subagent_model 必須先對 catalog 解析成規範形「解不出來的根本走不到這裡」 |
| grok-build（源：grok-goal-workflow.md §Q2） | `task` tool | **混合**：wire 欄位精簡（prompt/description required＋subagent_type/run_in_background/isolation(none\|worktree)/resume_from/cwd/model/workspace/task_id）；能力用枚舉軸 `capability_mode`（ReadOnly/ReadWrite/Execute/All，harness-internal，由 role/persona 解析：spawn override＞role default＞persona default＞parent 繼承） | 未知 subagent_type 報錯列 available；persona 解析失敗 spawn 直接 aborted；cwd launch 時驗存在；session 級併發 admission 預設 32、**上限可調但不可關**（clamp 至 1） |
| ai-guide | DispatchSlice（卡片契約編譯產物） | **契約**：逐欄顯式、缺欄 fail-loud（第三條路——前三家分別是呼叫端/設定檔/混合） | （設計中） |

**張力分析**：派工欄位放哪裡是三條路線的根本分歧——codex 放呼叫端（彈性最大、stale override 風險最高，靠繼承＋縮減收斂）；ZCode 放設定檔（人類管欄位、模型零權，換來零 stale-override）；grok 混合（wire 精簡＋role 軸）。codex 的「繼承＋縮減」與 ai-guide「逐欄顯式、缺欄 fail-loud」是兩個極端（源：codex-goal-workflow.md §主 session 判讀）。另注意三家都有「產出契約」意識：ZCode 的 `ask<T>()` 編譯期 schema、codex 的 wait_agent 回流、grok 的 worktree 隔離＋顯式 merge。

**對 135.1 的啟示**：DispatchSlice 的「卡片契約編譯」路線成立（設定檔與契約同屬「人不逐次重寫」陣營）。可吸收：ZCode 的 `ask<T>` 型別驅動產出 schema（DispatchSlice 的產出契約可用 schema 合成，violation 走 model-legible 修復迴圈）；grok 的 capability_mode 枚舉軸（讀寫執行四態比逐 tool 白名單緊湊）與「併發上限不可關」（admission 設計鐵律）；codex 的 fail-loud 訊息設計（錯誤列 available 清單，讓模型可自修）。

### 4.2 自主邊界與預算

**各家一覽**：

| 家 | 邊界表達 | 預算表達 | 超支停法 |
|---|---|---|---|
| codex（源：codex-goal-workflow.md §Q3·自主邊界與預算） | AskForApproval 四型（OnRequest 預設/Granular/Never；UnlessTrusted 已退役）×SandboxPolicy（ReadOnly/WorkspaceWrite/ExternalSandbox/DangerFullAccess）＋PermissionProfile 新正規化；macOS Seatbelt／Linux landlock+bubblewrap+seccomp | token 預算整棵 agent 樹共享（RolloutBudgetConfig：output×權重＋非快取 input×權重；非有限值直接 Fatal）；門檻提醒注入 `<rollout_budget>`；**無步數上限（max_turns 未找到）、無時間型總預算** | graceful error（SessionBudgetExceeded break 迴圈但「let the user continue the conversation」）——非 abrupt kill |
| ZCode（源：zcode-goal-workflow.md §Q3） | permission mode 梯（plan 只讀→build 按 riskLevel 分梯→yolo 全放行；alwaysAsk 壓過一切；auto 未實作直接 deny）；**每工具自報風險屬性**（riskLevel/destructive/sideEffectScope/needsApproval/timeoutMs/maxOutputBytes/resultBudget） | profile maxTurns；journal spentTokens；修復迴圈硬上限 REPAIR_ATTEMPTS=3、NUDGE_ATTEMPTS=1 | 超支即停：quota cap 進 stop reason、連續失敗 circuit breaker、所有工具呼叫帶 abortSignal |
| grok-build（源：grok-goal-workflow.md §Q3） | ToolApprovalPolicy 三級（AlwaysPrompt／GrantsAllowed／UnattendedAllowed），ceiling 由 hub 按 host-kind 下達；reads never prompt；**wire 值壞→AlwaysPrompt（fail-closed 到多問）** | `/goal --budget N` turn-end gate；token ratchet；workflow DSL agent 數預算（預設 128/上限 1024/host calls 10000）＋BudgetState{total,spent,reserved,remaining} | **BudgetLimited 終態**（非軟警告），恢復須 `/goal clear` 顯式重設；另有 stall 偵測——連續 2 回合相同 gap 指紋→自動 NoProgressPaused |
| ai-guide | autonomous 紅線/黃線分級＋停續二分 | priced-autonomy 記帳（revert 預算餘額、扣款記錄） | 超支即停（設計）；批量夜承諾制 |

**張力分析**：邊界的表達哲學分裂成兩派——codex「政策枚舉＋沙箱」（人類選檔位）；ZCode/grok「工具自報屬性＋中央梯子/ceiling」（新增工具自動被涵蓋）。預算停法三型：codex graceful（對話可續）、ZCode stop reason 分類、grok 終態＋顯式人類重設——grok 最硬。值得注意 codex 連「無限值預算輸入」都 Fatal（IEEE 754 fail-open 防護意識下滲到預算記帳）。我們的 priced-autonomy 記帳比 codex 細（它只有共享 token 池），但 grok 的「超支＝可見終態＋顯式人類動作解鎖」比我們的「停續二分」語義更硬。

**對 135.1 的啟示**：ArcPlan budget context 採「樹共享池＋權重記帳＋門檻預警」的 codex 機制；超支停法採 grok 語義（BudgetLimited 終態＋raise-cap 需人類），並吸收 stall 偵測（無進步指紋→自動 pause）作為 priced-autonomy 之外的第五停法。ZCode 的「每工具自報風險屬性」對 DispatchSlice 的 tool 白名單設計是低成本替代（白名單枚舉會隨工具增殖腐爛，屬性軸不會）。

### 4.3 斷線恢復

**各家一覽**：

| 家 | 恢復事實源 | 「已完成不重做」保證 | 防禦 |
|---|---|---|---|
| codex（源：codex-goal-workflow.md §Q2 斷線恢復） | rollout JSONL 事件流（SessionMeta/ResponseItem/EventMsg/Compacted…）；`codex resume` 重放 items 重建 model context | **重放而非重執行**——已完成步驟以 ResponseItem 留在 history 成為前置脈絡，副作用不重放（注：此點為推得，未逐行追完 reconstruction，源：同檔 §自評） | model 換了發 warning；fork/revert 雙 id |
| ZCode（源：zcode-goal-workflow.md §Q4） | workflow journal（node:sqlite；run/actor/node/event 四表） | 「finished steps are replayed from the journal without spending tokens, unfinished steps are dispatched again」 | **replay 命中防禦性校驗 inputHash，不一致＝純度契約破壞、整個 run 大聲失敗**；journal 被外力改過→scriptHash mismatch 拒絕；stop reason 五類（user/model/provider/interrupted/superseded），只有非 superseded 可 resume |
| grok-build（源：grok-goal-workflow.md §Q4） | journal 每筆 host call `{seq, kind, req_hash, result, at_ms}` JSONL＋plan.md/goal snapshot/traces | replay 跳過已記錄 call | **replay divergence 拒絕恢復**（「the script issued a different call than the recorded run — the script is nondeterministic or was edited mid-run」）；seq 必須連續；journal 將滿預先擋寫（「would strand the run unresumable」）；parse 失敗→UnsafeRestore fail-closed；**corrupt/未來版 snapshot 一律映射 UserPaused——「A corrupt or forward-version snapshot can never resurrect as a self-driving goal」** |
| ai-guide | EP 段落自含＋task notes/journal（對話層 checkpoint） | 靠結算與段落邊界（治理帳本，非機械帳本） | quota 中斷接手先讀卡 notes——LLM 恢復，非 replay |

**張力分析**：恢復事實源光譜——codex 用「對話事件帳」（恢復的是 context）；ZCode/grok 用「機械 journal」（恢復的是執行狀態，token 不重付）；ai-guide 用「治理帳本」（恢復的是任務脈絡）。ZCode 的 inputHash 與 grok 的 divergence 偵測同構：**把 mid-run 編輯腳本／ nondeterminism 當攻擊面**，恢復前先驗確定性。三家都把「不可信狀態」導向 fail-closed（拒絕恢復/大聲失敗/paused），沒有任何一家讓 corrupt 狀態復活成自駕。

**對 135.1 的啟示**：AC#5「runtime tail 缺場或矛盾 fail-loud」的實作範式已經現成——journal replay＋hash 校驗＋divergence 拒絕。135.1 的 DispatchSlice/receipt 若配機械 journal，「已完成不重付 token」直接可達（ZCode 句式：「a run that dies on its twelfth of forty tasks still did eleven tasks' worth of work」）。恢復事實源應與對話記憶脫鉤——崩潰接手不靠 LLM 記得什麼，靠 event log 的 sequence+hash。

### 4.4 審查隔離

**各家一覽**：

| 家 | 隔離機制 | 特點 |
|---|---|---|
| codex（源：codex-goal-workflow.md §Q3 審查隔離） | `codex review` 跑 **child review session**（initial_history=New＝fresh context、不繼承父對話；輸入是 diff 範圍非對話；輸出結構化 findings/overall_correctness/confidence_score）；Guardian reviewer（動作自動審查）：獨立重組 config——guardian policy prompt、無 memories、無 skills、無 MCP 繼承、permission 交 read-only、審查模型可異於 parent，讀「captured action/authorization/context snapshots」而非完整對話 | 隔離＝fresh context＋config 面收窄 |
| ZCode（源：zcode-goal-workflow.md §Q5） | expert workflow 每 phase 獨立 child session、**phase 間不共享對話只靠 disk artifacts 傳遞**（prompt 只列 artifact 路徑，實作者自我陳述不進 reviewer context）；final critic loop：verdict pass\|fail＋acceptanceGaps＋reopenProposals，fail 依 proposal 重開 graph 節點重跑（maxIterations 封頂） | 隔離是**結構性**（通訊面收窄到 artifacts），非存取控制式；多出 critic→reopen→重跑的自動修復閉環 |
| grok-build（源：grok-goal-workflow.md §Q5） | adversarial verifier——「You are NOT the agent that produced the work. Default to `refuted: true` if uncertain」；四支柱：**audit-don't-author**（只審 implementer 已提交的 tests＋captured output、禁自建平行測試、證據缺失 REFUTE 而非代補）、**謊言面審計**（宣稱改了 CHANGED_FILES 之外檔案＝fabricated 駁回；TODO/skip 測試駁回）、**anti-ratchet**（重驗首要確認舊 gap 已修、bar 不逐回合升高防 whack-a-mole）、**blocking 分類**（none\|contradiction\|unverifiable——後兩者需人類裁決而非重試）；spawn 前 RoleCapability gate（工具不夠 fail-open 回 parent——「Failing open beats spawning an unusable verifier」） | 隔離核心不是「限制 reviewer 讀什麼」而是「**限制 reviewer 產什麼**」——只能寫 verdict/details 兩檔、只能反駁不能代工 |
| cookbook（源：cookbook-full-survey.md§3·review/repair、§權限分離） | Review/Repair/Validate 三段分離（review 禁改檔、repair 改副本、validation 產結構化 delta 回灌）；CI review read-only sandbox＋reviewer 無 PR write；「separate validator 負責 review 與 merge」 | 驗收面可插拔（「unit test, policy check, schema validator, simulation, or human approval step」） |
| ai-guide | Writer/Reviewer 分離（fresh subagent context）＋跨家族第二意見＋oracle S/H/I/N 分級＋/followup-review | 多跨家族軸；少自動修復閉環 |

**張力分析**：隔離技術三型——fresh context（codex）、通訊面收窄（ZCode artifacts）、權限/產出面收窄（grok 只准產 verdict；cookbook reviewer 無 write 權）。ZCode 未找到 critic 禁讀實作者 transcript 的硬限制（隔離靠結構推斷，源：同檔 §自評）——誠實標注。grok 的 anti-ratchet 是獨有問題意識：修復迴圈的隱藏失敗模式是「bar 逐回合升高使 goal 永不可完成」。我們的獨有軸是跨家族第二意見（三家皆單 harness 視野）。

**對 135.1 的啟示**：DispatchSlice 的 reviewer 契約可吸收 grok 四支柱——尤其 blocking 分類（contradiction/unverifiable→人類裁決而非重試，直接對上 pending 台帳）與 anti-ratchet（/followup-review 迴圈需「先確認舊 gap 已修、bar 恆定」條款）。ZCode 的 reopenProposals（critic 產出機器可執行的重開提案）是 135.1 自動修復閉環的參照。

### 4.5 model routing

**各家一覽**：

| 家 | 路由機制 | escalation/fallback |
|---|---|---|
| codex（源：codex-goal-workflow.md §Q3 model routing） | 每 thread 一 model slug＋ModelInfo；per-agent binding 三條路（spawn 參數 model+reasoning_effort／role 釘 model（工具描述標「cannot be changed」）／config 預設）；service tier 全樹共享 root；model 甚至可決定 multi-agent 後端版本 | **無 escalation（未找到）**。fallback 三種全是降級：provider fallback（要求 model 不在目錄→default，記 log）、compaction model fallback、server 端 reroute（高風險帳號被換 model） |
| ZCode（源：zcode-goal-workflow.md §Q6） | 靜態設定式：AgentProfile frontmatter＋workflow run 級 subagent_model（整場 run 所有 actor 共用）＋session 主模型 UI 選；**caller model 不能指定 subagent model**——schema 註解明言「若把調用級 model 暴露給父模型，歷史 tool call 會持續生成舊 override 並覆蓋當前配置」 | **無 model 級 fallback 鏈**（grep 無命中）；降級替代是行為級修復（3 repair＋1 nudge），修不好才失敗、**不換 model** |
| grok-build（源：grok-goal-workflow.md §Q6） | per-role {model, agent_type} 覆寫；task 的 model 參數 schema 文案「ONLY choose an explicit `model` when the user DIRECTLY requests it」；host 可設 Inherited 把 model 參數從 schema 整個移除；compaction 跑專用 model（覆寫序 agent setting＞harness config＞default）；resume 釘住 source model、新 override 靜默忽略 | 僅單層：首次 spawn 失敗 retry-once 退回 current model＋session harness——退路一律「繼承 parent」，無自動升級鏈 |
| cookbook（源：cookbook-full-survey.md§3·agent_improvement_loop） | （無 routing 表）「reviewed loop 起步，eval gate 信任度升後再加深自動化」——自動化程度是信任函數 | — |
| ai-guide | model-routing resolver：能力需求→catalog→model；no-silent-downgrade（無合格 candidate 顯性 no-candidate/escalation） | 顯性 escalation |

**張力分析**：三家 harness 驚人一致地把 routing 權收給人類設定與「繼承 parent」，且全都沒有 escalation——與 ai-guide「能力需求推斷 model」是路線分歧。ZCode 給出了最強的反面論證：把 model 選擇權交給模型/呼叫端，歷史 tool call 會持續生成舊 override（stale override）——這正是我們 presets/binding 設計（欄位住設定而非呼叫）已經規避的問題，反向印證了我們的 preset 層。grok 的「契約讀者含小模型」是獨有的下行紀律：計畫文件要為將執行它的最弱模型可讀而寫。cookbook 的「自動化程度＝eval gate 信任函數」則是漸進授權觀，對 dispatch 自動化的鋪開節奏有直接參考價值。

**對 135.1 的啟示**：resolver 路線繼續走，但要（a）把 binding 欄位鎖在 DispatchSlice/preset 層、不進模型呼叫面（ZCode 教訓）；（b）「no-silent-downgrade」與三家「無 fallback 鏈、fail 就顯性失敗」方向一致——維持顯性不學 codex 的 provider 靜默降級；（c）ArcPlan 寫作加「小模型可讀」約束（grok）。

### 4.6 人機確認點

**各家一覽**：

| 家 | 強制點頭面 | 批量放行 | 協議特點 |
|---|---|---|---|
| codex（源：codex-goal-workflow.md §Q4 人機確認點） | ExecApprovalRequest／ApplyPatchApprovalRequest 事件；ReviewDecision 八決策（Approved/…/ApprovedForSession/Denied/TimedOut/Abort） | 兩型：ApprovedForSession（同類請求 session 內自動准）＋grant_root（patch 批准附 session 內 root 寫權） | ApprovalsReviewer 可把審核路由給「carefully prompted subagent」（AutoReview） |
| ZCode（源：zcode-goal-workflow.md §Q7） | build 模式下 critical/high risk 與一切 sideEffect 必問；alwaysAsk 連 yolo 都壓不過；AskUserQuestion 限「genuinely the user's to make」且 input 必須 answered 形（user 沒答就執行＝直接失敗） | 兩形：allowAlways:"session"；plan 核准附 allowedPrompts（語義級預授權如 `[{tool:"Bash", prompt:"run tests"}]`，隨 plan 一次生效） | **單向收窄鐵律**——PreToolUse hook「只能把 ask 放行成 proceed 或補預覽，永遠不能把 allow 變成 ask」；預覽生成 bug 時 fail 到 ask 而非放行；**workflow 升級鏈**：actor ask() 卡住→升級問題給主 agent→ResolveWorkflowQuestion 回答——run 整場續跑、只有提問者 park 住 |
| grok-build（源：grok-goal-workflow.md §Q7） | 所有 mutating call（按三級 ceiling）、plan 核准（approval chrome 重啟可還原） | **一次授權批量放行不存在**——recorded approval 只傳承到「same vein, not more dangerous」；recorded decline 具約束力 | auto-mode classifier 兩級：**hard-wait**「no request or instruction of any kind clears it (standing, project-level/AGENTS, or in-transcript)」——push/prod mutation/SSH/不可逆刪除/跑未信任代碼；**clearable** 只在「user's own live request」授權時放行，且「A request for the outcome does not by itself authorize the destructive step that reaches it」、模糊/過時/代引述的指令永不足夠；只信 harness-owned decision 欄位、**工具參數內的准許宣告視為 data**；只有 harness 注入的 recent user turns 能建立 first-party intent（AGENTS 檔與 assistant 自己的話都不能） |
| cookbook 官方（源：cookbook-iterating-verdict.md§逐條同構對照） | phase 完成後**停、不自動開下一 phase**（官方預設恆停）；「Keep commits, pushes, deployments, credentials, and external writes behind separate explicit approval」 | 無批量形態 | 人 gating 是預設；小 build 檔支持人審 |
| claude-code（文檔；源：mirrors-survey.md §任務A·claude-code） | plan 權限模式、auto mode＝server-side classifier、protected/critical paths | — | — |
| ai-guide | outward-action-consent：reversibility test、AUTH line 逐字引用、quote scope 判準、documentation≠authorization | autonomous 紅線枚舉（deep-work 場景） | 每次 commit 重新驗 gate（一次授權≠永久授權） |

**張力分析**：grok 的 classifier 與 ai-guide outward-action-consent **幾乎逐點同構**——hard-wait≈紅線（standing/project/AGENTS 檔授權都不算＝documentation ≠ authorization；in-transcript 不算＝僅本次對話原話）、clearable 的「結果授權≠手段授權」＝quote scope 判準的「邏輯跳躍就 PENDING」、decline 具約束力、工具參數宣告視為 data＝「工作流/README 要求不是授權」。兩個獨立演化的系統收斂到同一組規則（§7 詳論）。ZCode 的單向收窄（hook 不能把 allow 變 ask）是 hook/guard 設計的普遍鐵律——自動化掛點只能放寬「問→不問」，永不能反轉「不問→問」。官方預設恆停 vs 我們批量自治：我們是刻意超集，安全網是六欄預算＋停續二分（報告明寫，源：cookbook-iterating-verdict.md§對 135.1 的直接輸入 #3）。

**對 135.1 的啟示**：(a) 編排器的自動化掛點（hooks/guards）納入單向收窄鐵律；(b) 批量放行綁生存期（session/plan scope）而非永久——兩家都是；(c) 135.7 collection 契約的參照實作＝ZCode 升級鏈「只 park 提問者、run 續跑」；(d) plan 核准附語義級預授權（allowedPrompts）可映射到我們的預授權欄的機器形態。

### 4.7 context 管理

**各家一覽**：

| 家 | 壓縮機制 | 進度存活 |
|---|---|---|
| codex（源：codex-goal-workflow.md §Q5 context 管理） | `model_auto_compact_token_limit`＋scope（Total/BodyAfterPrefix）；每 turn 結算；超限 auto-compact 而非硬停；SUMMARIZATION_PROMPT 產 handoff summary（progress/key decisions/what remains/critical data）；prompt 可換；pre/post_compact hooks | 壓進 summary＋rollout 為 append-only 事件帳（原 history 仍在檔、可 resume 重放） |
| ZCode（源：zcode-goal-workflow.md §Q8） | 預算是算出來的（200K−output reserve 32K−preflight 21K−buffer 13K＝觸發門檻；token 優先 provider usage）；**連續 3 次 compact 失敗觸發 circuit breaker 停手**；頭段 summary＋尾段 verbatim；microcompact 清舊工具輸出 | **summary 9 節強制結構**（Primary Request/Key Concepts/Files & Code/Errors & fixes/Problem Solving/**All user messages 全列**/Pending Tasks/Current Work/Next Step）——**安全約束須逐字保留、next step 須附原文引用防漂移**；壓縮後接續訊息帶 transcript 路徑；進度三件分級外部化：todo 存 sessionStore（不受 compact 影響）、plan 檔重注入、workflow journal 天然免疫 |
| grok-build（源：grok-goal-workflow.md §Q8） | transport-agnostic compaction engine 三型態（code_compaction＝whole-session **full-replace**／intra tail-keep／inter chunked）；tool-pair-safe tail-keep（tool_call/result 成對保留）；跑專用 model；可 mid-turn 跑（CompactAndResubmit） | 進度外部化四件：plan.md 每回合重注入（「A structured plan for this goal is on disk」）；**compaction 後 goal 從 plan 的 acceptance criteria re-seed todo list**；每回合 continuation directive 重注入 {objective/Status/Tokens/Elapsed/next_step}（400 字上限）；PlanModeTracker reminder 計數 reset on compaction |
| cookbook（源：cookbook-iterating-verdict.md§context 檔、cookbook-full-survey.md§3·exec_plans） | phase context 檔＋**materiality test**（省略會影響未來工作才記；**禁 transcript/scratchpad/progress log**；superseded decisions 要記） | ExecPlan living document 四節必填（Progress 含 timestamp／Surprises & Discoveries／Decision Log／Outcomes & Retrospective） |
| ai-guide | durable checkpoint（想法即時落盤）、EP 段落自含、compact-prep skill | 卡 notes／EP 進度節／session journal |

**張力分析**：四源完全收斂於同一原則——**真相放磁碟、context 只留指針**（「壓縮假設 context 會失憶」）。差異在機械化程度：grok 最徹底（re-seed todo＋每回合 directive 重注入，連 directive 都有字數上限）；ZCode 的 9 節 summary 是「壓縮品質契約」的範式（安全約束逐字保留＝我們的「壓縮必保留」Summary Instructions 的 harness 級版）。ai-guide 的 durable-checkpoint 紀律與 cookbook materiality test 連「禁進度流水」都同構（源：cookbook-iterating-verdict.md§逐條同構對照）。

**對 135.1 的啟示**：長任務 DispatchSlice 的接續格式可直接採 grok directive（{objective/Status/Tokens/Elapsed/next_step}＋從 AC re-seed 進度）；compact-prep 可吸收 ZCode 9 節結構（尤其「All user messages 全列」「安全約束逐字保留」「next step 附原文」三條硬規則）。

---

## 5. 生態位發現

### 5.1 ZCode＝Claude Code 機制家族（移植證據鏈）

**判定**：ZCode 的 dynamic-workflow 與 Claude Code 官方文檔描述的 workflow 機制是同一機制家族（mirrors 腿判語「GLM 平台移植」——家族關係判定屬鏡像腿推論，移植的確切上游版本未考）（源：mirrors-survey.md §任務B）。證據鏈：

1. **機制逐一對應**：claude-code 鏡像 workflows.md 記載的保存兩級（專案 `.claude/workflows/` vs 個人 `~/.claude/workflows/`）、存檔後成 `/<name>` 指令、args 參數化重跑、journal replay（完成的 agent 回快取結果、失敗者之後全部重跑）、`Date.now`/`Math.random` 被 ban 以保 replay 決定性——與 ZCode 源碼的 `.zcode/workflows`/`~/.zcode/workflows`、SaveWorkflow args、journal engine 逐一對應（源：mirrors-survey.md §任務B、zcode-saved-workflows.md §1-4）。
2. **工具命名貼 Claude Code 家族**：TodoRead/TodoWrite、EnterPlanMode/ExitPlanMode、AskUserQuestion；Agent tool 同時把 `Task` 認作別名（`compat.ts` 的 `TASK_TOOL_NAME="Task"`——檔名自證相容層性質）（源：zcode-saved-workflows.md §5）。
3. **授權語彙與 codex 零重疊**：codex 兩軸 AskForApproval×SandboxPolicy vs ZCode 單軸 plan/build/yolo——概念同構、語彙零重合；"yolo" 是社群俚語非 codex 詞（源：zcode-saved-workflows.md §5）。
4. **codex 側無對應物**：保存工作流面板在 codex repo 搜 workflow/automation/saved 零命中——這一整塊不可能是致敬 codex（源：zcode-saved-workflows.md §5）。

**致敬度結論（誠實邊界）**：概念同構度中高，但「精確相似度數字（如 87%）無從證明，不應引用」；AGENTS.md 兩邊都讀屬跨廠商標準遵循、不構成致敬證據（源：zcode-saved-workflows.md §5）。**實務含義**：ZCode 源碼可以當 Claude Code workflow 機制的可讀代理標本——我們想理解 CC 的 workflow 行為，讀 ZCode 源碼比讀 CC marketing 文檔可靠。

### 5.2 grok-build 文檔落後源碼

grok-build 源碼有完整的 `/goal` 契約＋journal＋adversarial verifier（源碼腿八題全收），但官方鏡像 24 頁對 "goal" 一詞**零命中**；對照 codex（developer-commands.md:496 完整 `/goal` 頁）與 claude-code（goal.md 整頁）都有正式 `/goal` 文檔——同源機制、文檔落後（源：mirrors-survey.md §任務C #1）。附帶發現：grok 官方文檔自揭 hooks fail-open（timeout/crash 只記錄放行、僅 explicit deny 擋）——與 ai-guide「hook 只 advisory、correctness gate 在 consumer boundary」的 AIR-135 條 3 同向，但源碼對帳未做（源：mirrors-survey.md §任務C #6）。**注意**：grok 鏡像僅 24 頁（對照 codex 149 頁），若其官網還有 /goal 或 workflows 頁在 crawl discover 範圍外，本結論會翻——建議對 grok-build 官方 docs 做一次索引級（llms.txt/sitemap）對帳（源：mirrors-survey.md §自評）。

### 5.3 官方 vs 源碼落差表精華

九條落差（全表見 mirrors-survey.md §任務C），按類型精華：

| 類型 | 落差 |
|---|---|
| 隱藏能力（源碼有、文檔無） | grok `/goal` 契約＋journal（#1）；ZCode dynamic-workflow 全套——saved 兩級/args/journal/amend runtime 在場，鏡像 0 頁記載工作流面板（#2） |
| 官方淺於實作 | ZCode goal.md 只講行為不講機制；CC 同構頁揭露 evaluator＝small fast model＋Stop-hook 包裝＋三判定（#3） |
| 矛盾候選 | ZCode safety-confirm.md「提問超時 5 分 Agent 自動挑方向續行」vs runtime workflow escalation（ResolveWorkflowQuestion）是無限等待——兩種語義並存、文檔未提差異（#4） |
| 官方未寫 | ZCode subagents.md 只列內建＋用戶自訂；plugin/registry agents 載入來源未記載（#5） |
| 無法對帳 | CC workflows.md 宣稱面大（ultracode／1000 agent cap／schema 5 retries）——CC 源碼不在本次調查軸，marketing 屬性未知（#7） |
| 一致互證 | codex+CC `/goal` 4,000 字上限、每輪外部 evaluator、resume 還原——docs 互證同源；grok 缺席更突兀（#9） |

**方法論含義**：三軸交叉是必要方法——只讀說明書會漏掉兩家的最大能力（workflow 編排與 goal 契約都是隱藏能力）；只讀源碼會誤判產品的官方承諾面。

---

## 6. 對 135.1 的設計輸入清單（最重要節）

### 6.1 借鑑清單

按落點分組；「落點」使用 AIR-135.1 擬定 artifacts（ArcSpec＝目標契約、ArcPlan＝計畫、DispatchSlice＝派工單、receipt＝派工回執；另及 135.7 collection 契約、135.8 correction 迴路）。

**A. 恢復與確定性（機械帳本層）**

| # | 模式 | 來源 | 建議落點 |
|---|---|---|---|
| 1 | journal replay——「finished steps replayed without spending tokens, unfinished steps dispatched again」 | ZCode（§4.3） | 135.1 runtime：DispatchSlice 執行配機械 journal；receipt 記每步完成事件 |
| 2 | replay 命中防禦性校驗 inputHash——不一致＝純度契約破壞、整個 run 大聲失敗 | ZCode（§4.3） | 同上；AC#5 恢復 invariant 的實作 |
| 3 | replay divergence 拒絕恢復（mid-run 編輯/nondeterminism 當攻擊面）＋seq 連續強制＋journal 將滿預先擋寫 | grok-build（§4.3） | 同上；與 #2 二擇一或並用（hash 驗輸入、divergence 驗行為） |
| 4 | corrupt/未來版狀態一律映射 paused——corrupt snapshot 永不能復活成 self-driving goal | grok-build（§4.3） | ArcPlan recovery 語義：fail-closed 到人類，禁自駕復活 |

**B. intent 防拉伸（計畫治理層）**

| # | 模式 | 來源 | 建議落點 |
|---|---|---|---|
| 5 | PLAN_CHANGES 篡改審計——plan 編輯留 diff 交 verifier，弱化/刪除/自利 criterion 本身即駁回理由；implementer 只能往 Deviations 節加 bullet | grok-build（§3.1/§4.4） | ArcSpec/ArcPlan：契約修訂流＝diff＋驗收腿複核；強化 135.3 AC#7 |
| 6 | Goal 契約補兩欄：Iteration policy（迭代/改打法前要不要回人）＋Blocked stop condition（blocked 時報什麼＋什麼能解鎖） | cookbook（§3.1） | ArcPlan/card 契約欄位 |
| 7 | 「Specify OUTCOMES, not architecture」＋「契約讀者含小模型」——計畫禁凍結 HOW、要為最弱執行模型可讀而寫 | grok-build（§3.1/§4.5） | ArcPlan 寫作約束 |
| 8 | 「decisions requiring human input」＋「evidence required before complete」逐 slice 欄位 | cookbook phase file（§3.1） | DispatchSlice 欄位 |

**C. 預算與停法（priced-autonomy 層）**

| # | 模式 | 來源 | 建議落點 |
|---|---|---|---|
| 9 | BudgetLimited 終態＋顯式重設（raise cap 是人類動作）＋token ratchet | grok-build（§4.2） | priced-autonomy 超支語義：終態化而非軟警告 |
| 10 | stall 偵測——連續 2 回合相同 gap 指紋→自動 NoProgressPaused | grok-build（§4.2） | 第五停法（預算/紅線/停續二分之外） |
| 11 | 全樹共享 token 預算池＋權重記帳（output×權重＋非快取 input×權重）＋非有限值 Fatal＋門檻預警注入 | codex（§4.2） | ArcPlan budget context 記帳規則 |

**D. 派工介面（DispatchSlice 層）**

| # | 模式 | 來源 | 建議落點 |
|---|---|---|---|
| 12 | `ask<T>()` 型別驅動產出 schema（編譯期合成輸出 JSON Schema）＋model-legible violation 修復迴圈（3 repair＋1 nudge 封頂） | ZCode（§4.1） | DispatchSlice 產出契約：schema 合成＋修復上限 |
| 13 | capability_mode 枚舉軸（ReadOnly/ReadWrite/Execute/All）替代逐 tool 白名單＋isolation(none\|worktree) 軸 | grok-build（§4.1） | DispatchSlice 權限欄位 |
| 14 | 併發 admission：上限可調但不可關（clamp 至 1） | grok-build（§4.1） | 135.1 派工 admission |
| 15 | fail-loud 訊息設計：未知角色/模型即錯並列 available 清單（讓呼叫方可自修） | codex＋grok（§4.1） | 135.1 錯誤契約 |
| 16 | 每工具自報風險屬性（riskLevel/destructive/sideEffectScope/needsApproval）＋中央判定梯——新增工具自動被涵蓋 | ZCode（§4.2） | DispatchSlice tool 選擇的長期形態（白名單會腐爛、屬性軸不會） |

**E. 協調與接續（編排器運行層）**

| # | 模式 | 來源 | 建議落點 |
|---|---|---|---|
| 17 | 升級問題只 park 提問者、run 整場續跑（actor ask()→升級主 agent→ResolveWorkflowQuestion） | ZCode（§4.6） | 135.7 collection 契約 |
| 18 | 站間 schema 化 handoff（每段輸出 JSON schema，下一段消費機器可讀 findings/delta）＋artifact 存在性機械確認才解鎖下一站（PM gated handoff——cookbook 用 prompt 層，我們可上機械層更強） | cookbook（cookbook-full-survey.md§4） | 135.1 站間介面 |
| 19 | dispatch receipt 欄位範式＝build-log 結構化欄位（Status/Branch/Red/Green/Verification/Limitations/Blockers/Next action/Evidence references；append-only；「describe what actually happened, not what the plan predicts」） | cookbook（cookbook-iterating-verdict.md§對 135.1 的直接輸入 #2） | receipt 格式 |
| 20 | 長任務接續 directive：每回合重注入 {objective/Status/Tokens/Elapsed/next_step}（字數上限）＋compaction 後從 acceptance criteria re-seed todo | grok-build（§4.7） | DispatchSlice 長任務接續格式 |
| 21 | compact 9 節強制結構：安全約束逐字保留、user messages 全列、next step 附原文引用防漂移 | ZCode（§4.7） | compact-prep 升級 |

**F. 審查迴路（Verify 層）**

| # | 模式 | 來源 | 建議落點 |
|---|---|---|---|
| 22 | blocking 分類 none\|contradiction\|unverifiable——後兩者需人類裁決而非重試 | grok-build（§4.4） | pending 台帳分類（evidence-contradicts-intent 類的鏡像） |
| 23 | anti-ratchet——重驗首要確認舊 gap 已修、bar 恆定，防 whack-a-mole 使 goal 永不可完成 | grok-build（§4.4） | /followup-review 迴圈條款 |
| 24 | critic→reopenProposals→重開 graph 節點重跑（機器可執行的修復提案） | ZCode（§4.4） | 135.1 自動修復閉環 |
| 25 | verifier 只准產 verdict/details、禁代工補測試；謊言面審計（宣稱範圍外檔案＝fabricated 駁回） | grok-build（§4.4） | reviewer 契約（audit-don't-author） |

**G. 能力成長（135.8 層）**

| # | 模式 | 來源 | 建議落點 |
|---|---|---|---|
| 26 | eval 資產化——session 軌跡/review findings 累積成可重跑 eval（graders/資料集）；「失敗案例→eval case」步驟；自動化程度＝eval gate 信任函數 | cookbook（cookbook-full-survey.md§4） | 135.8 correction 迴路（見 §7 挑戰） |
| 27 | forward-testing 明文化——skill/harness 修正後用 fresh session 驗證（正負觸發案例、不洩題、隔離測試產物） | cookbook（cookbook-iterating-verdict.md§差異 #1） | 135.8 驗證腿（材料檔已註記「登記給 135.8、S7/user 裁決項」） |
| 28 | retrospective 每個教訓分派唯一 owner（七擇一載體路由）＋new skill 六條件——與 135.8 載體路由幾乎逐條相同（背書多於借鑑） | cookbook（§7 背書） | 已有；引用對照即可 |
| 29 | Surprises & Discoveries 獨立節＋epistemic support 四級 ledger（confirmed/approximate/blocked/uncertain）作為研究型任務產出格式 | cookbook（cookbook-full-survey.md§4） | EP 進度節欄位／六站驗收產出格式 |

### 6.2 已領先不必動

| 面 | 我們現狀 | 外部對照（為何不必動） |
|---|---|---|
| outward-action-consent | reversibility test＋AUTH 逐字引用＋quote scope | grok 獨立收斂出同構規則（§7）；三家 harness 無一更細 |
| model-routing resolver | 能力需求→catalog→model；no-silent-downgrade | 三家皆無 escalation、皆靜態設定——我們的 resolver 是超集；唯一要吸收的是 ZCode 的 stale-override 教訓（binding 鎖設定層） |
| 跨家族第二意見 | delegate-bridge muse/codex/glm | 三家皆單 harness 視野，無對應物 |
| 批量自治形態 | deep-work 承諾制＋停續二分＋晨間裁決 | 官方預設恆停（cookbook）；我們是刻意超集且安全網明確 |
| Settle 站治理 | commit skill＋結案兩步＋卡/backlog | 三家 goal/workflow 都不管 commit、無卡概念（grok 終場對照表「ai-guide 獨有」） |
| entry Align 互動釐清 | spec skill＋需求釐清流程 | grok goal loop 禁互動釐清（目標須一次給全）——我們多一條收斂腿 |
| oracle 分級 | S/H/I/N 正典 | cookbook 的 verifying-implementations 只有 pass@k/pass^k 指標面，無分級本體論 |
| dirty-worktree 紀律 | 他人變更禁碰、commit 只 add 指名檔 | codex prompting guide 條款幾乎逐字同源（「NEVER revert existing changes you did not make」）——同向互證 |
| 多 harness 治理 | 同一套 rules 部署四家 | cookbook 單 harness 視野 |
| EP 結算接續 | 段落自含＋/at ＋/handoff | ExecPlan living document 同構；grok directive 是機械化補充（#20）而非取代 |
| fail-closed 輸出閘 | gate 禁 pipefail 偽綠＋Crash-Only | cookbook「Do not treat a failed Codex run or invalid output as an empty findings result」同源 |

### 6.3 開放問題

1. **ZCode critic 的 transcript 隔離是推斷非碼證**——「critic 是否看到實作者 transcript」未讀 critic prompt 原文；expert workflow 與 dynamic-workflow 兩套並存的分工邊界也未查清（源：zcode-goal-workflow.md §自評）。
2. **codex「副作用不重放」是推得**——resume 只重建 context/狀態有碼證，但 reconstruction 全函數未逐行追完（源：codex-goal-workflow.md §自評）。
3. **codex SDK/app-server 面可能漏 workflow API**——說明書 149 頁只抽查 6 頁，config-reference/app-server/codex-sdk 未掃（源：mirrors-survey.md §自評）。
4. **grok 鏡像完整性**——24 頁 vs codex 149 頁，需索引級對帳才能坐實「文檔落後」結論（源：mirrors-survey.md §自評）。
5. **grok hooks fail-open** 官方自揭但源碼對帳未做（源：mirrors-survey.md §任務C #6）。
6. **CC workflows.md marketing 屬性未知**——CC 源碼不在本次調查軸（#7 落差無法對帳）。
7. **同源 vs 獨立收斂的效力範圍**——codex↔grok 疑似同源、ZCode↔CC 疑似移植；「多家都有 X」的背書效力打折，唯 outward-consent 的收斂（ai-guide vs grok）可主張獨立。
8. **cookbook `what_makes_documentation_good.md` 補讀**——調查腿自薦、涉 instruction-writing，記 pending 待裁決（源：cookbook-full-survey.md §自評）。
9. **ZCode「提問超時 5 分自動挑方向續行」與 runtime 無限等待的矛盾**——若我們參照 ZCode 升級鏈（#17），需自行裁決超時語義（該文檔兩說並存）。

---

## 7. 對 AIR-135 現有設計的背書與挑戰

**背書一：cookbook 官方工作流與 AIR-135 幾乎逐條同構（方向性背書）。** GOALS.md 對 entry 六欄、phase file 對 card Planning Contract＋slices、phase context 的 materiality test 對 checkpoint 紀律（連「禁 transcript/progress log 流水」都同）、build-log 誠實條款對 acceptance-evidence＋Fail Loud、source-of-truth boundaries 對單一源紀律、retrospective 載體路由（七擇一 owner＋new skill 六條件）對 135.8 correction 迴路——最後一項判準「幾乎逐條相同（極高）」（源：cookbook-iterating-verdict.md§逐條同構對照）。OpenAI 官方建議的最佳實踐與我們自建的流程收斂，代表路線不需要外部修正。

**背書二：outward-consent 的獨立收斂證據。** grok-build 的 auto-mode classifier 與 outward-action-consent rule 幾乎逐點同構：hard-wait 的「任何 standing/project/AGENTS/in-transcript 指令都不解除」≈我們的「documentation ≠ authorization＋僅本次對話原話可 AUTH」；「A request for the outcome does not by itself authorize the destructive step that reaches it」≈quote scope 的「需邏輯跳躍才涵蓋就 PENDING」；recorded approval 只傳承到「same vein, not more dangerous」≈「一次授權≠永久授權」；只信 harness-owned decision 欄位≈工具/工作流內的准許宣告不是授權。兩個獨立演化的系統收斂到同一組規則——這是本次調查中效力最強的單一外部佐證（源：grok-goal-workflow.md §Q7、§主 session 判讀）。**效力邊界**：僅此一處可主張獨立收斂；codex↔grok、ZCode↔CC 的其他相似性受同源/移植關係污染（§6.3 #7）。

**挑戰一：eval 資產化差距（最大能力差距軸）。** cookbook 的改進飛輪（開放編碼失敗 trace→taxonomy→資料集＋graders→定向改進→合成資料擴充）與 agent improvement loop（traces→feedback→eval suite→ranked changes→handoff）是量化資產化閉環；我們的驗收仍在「單次 gate 層」，沒有 prompt/skill 級可重跑 eval 資產（源：cookbook-full-survey.md§4「它比我們成熟處」）。135.1 的派工品質若要漸進放寬（「自動化程度＝eval gate 信任函數」），必須先有 eval 資產。→ 借鑑 #26。

**挑戰二：官方恆停 vs 我們批量自治。** 「phase 完成停、不自動開下一 phase」是官方預設；我們的批量夜自治是刻意超集。這個選擇有代價——官方沒有「預算內自主做到完」的需求，因為它不背還原預算與越權風險。我們必須持續用六欄預算＋停續二分＋priced-autonomy 記帳證明這個超集安全，而非視其為免費預設（源：cookbook-iterating-verdict.md§對 135.1 的直接輸入 #3）。

**挑戰三：resolver 路線的孤例性。** 三家 harness 都不讓模型選 model、都無 escalation；ai-guide 的能力推斷 resolver 是唯一走「語義判斷選 model」的系統。這不是判 resolver 錯（我們有跨家族/跨 provider 的供給現實，harness 沒有），而是要求 resolver 的錯誤面（誤判能力需求→降級）有顯性偵測——no-silent-downgrade 已是正確答案，但需配 eval 資產才能驗 resolver 本身的品質（挑戰一的下游）。

**挑戰四：機械帳本層的落差（結論 2 的正面表述）。** 恢復（journal replay/hash 校驗）與 intent 防拉伸（PLAN_CHANGES）在三家 harness 是機制、在我們是紀律。135.1 若只編譯派工單而不配機械帳本，等於把外部已解的確定性問題留在 instruction 層。這是設計輸入清單 A/B 組（#1-#9）為何排在最前面的原因。

---

## 8. 證據索引

全部原始材料在 `/Users/ctai/Github/ai-guide/.agent-tmp/air-135/oss-survey/`；本報告引用採「檔名＋節名」，不重抄 file:line。

| 檔案 | 節結構 | 本報告主要消費處 |
|---|---|---|
| `codex-goal-workflow.md` | r1：主題1 派工單／主題2 自主邊界與預算／主題3 model routing／主 session 判讀；r2：Q1 目標→計畫物／Q2 斷線恢復／Q3 審查隔離／Q4 人機確認點／Q5 context 管理／自評 | §3.1、§4.1-4.7 各家一覽、§6.1 #11/#15、§6.3 #2 |
| `zcode-goal-workflow.md` | Repo 速覽／Q1-Q8／終場對照表：ZCode ↔ ai-guide 六站模型／自評／主 session 判讀 | §3.1、§4 各題、§5.1、§6.1 #1/#2/#12/#16/#17/#21/#24、§6.3 #1/#9 |
| `grok-goal-workflow.md` | Repo 速覽／Q1-Q8／終場對照表／自評／主 session 判讀 | §3.1/§3.3、§4 各題、§7 背書二、§6.1 A/B/C 組 |
| `cookbook-iterating-verdict.md` | 核心結論／逐條同構對照／差異／對 135.1 的直接輸入／處置 | §3.1 官方實踐、§4.4/§4.6、§6.1 #6/#8/#19/#27/#28、§7 背書一/挑戰二 |
| `cookbook-full-survey.md` | 目錄地圖／相關文章清單／逐篇要點／對 AIR-135 的可學點／自評／主 session 判讀 | §3.1、§4.4/§4.5、§6.1 #18/#26/#29、§7 挑戰一、§6.3 #8 |
| `zcode-saved-workflows.md` | 保存機制／參數化重跑／作用域／與 journal run 的關係／致敬度快查 | §5.1 |
| `mirrors-survey.md` | 任務 A 四家摘要／任務 B ZCode 工作流面板／任務 C 落差表／自評 | §3.1 claude-code、§5.2/§5.3、§6.3 #3/#4/#5/#6 |
| `openai-cookbook-iterating-workflows.md` | cookbook 原文逐字存檔（GOALS/PROMPTS/phase file 模板/build-log/validator/retrospective） | §3.1 欄位集核對 |

---

## 9. 淺讀與殘留（誠實邊界）

各腿自評的淺掃項彙總（未經整合腿重驗；引用相關結論時注意效力）：

**codex 腿**：Q2「已完成副作用不重放」由 reconstruction 作用面推得、未逐行追完（中等）；Q3 child review session 的 reviewer prompt 模板與 sandbox 讀寫限制未逐檔展開（較淺）；checkout 為演化變體——review/guardian 面與 upstream 可能不同，收錄以本 checkout 為準。

**ZCode 腿**：session 主對話 crash 恢復只查到 CLI 入口與 store 端口面；Q6 僅掃 `provider-node`（services/desktop 未窮盡）；Q5 最淺——critic prompt（`parsers/critic.ts`）未讀、「critic 是否見實作者 transcript」是結構推斷；expert workflow vs dynamic-workflow 分工邊界未查清（已列 §6.3 #1）。

**grok 腿**：Q4 session transcript 持久化格式未逐檔讀（恢復全貌由 journal+tracker+resume types 拼出）；Q6 `xai-grok-models` crate 僅抽查、未窮舉 catalog/escalation 可能的其餘機制。

**cookbook 全面掃描腿**：ipynb 內嵌圖致數篇僅抽大綱（gpt-5-2_prompting_guide、sandboxed-code-migration、evaluate_agents 等——模式已由同群深讀篇覆蓋）；漏掃風險：`what_makes_documentation_good.md` 未讀（建議補讀，pending）；registry.yaml 未逐條核對；純 py/ipynb 內文的 plan/approval 命中未全掃。版本觀察：cookbook 條目生命週期短（兩篇 CI 文已歸檔＋安全警示）——引用時模式（gate/handoff/flywheel）比 API 載體穩定。

**mirrors 腿**：grok-build 精讀 7 頁、其餘未讀；codex 149 頁抽查 6 頁（SDK/app-server 面「可能漏 workflow API 記載」）；claude-code 的 agent-sdk/typescript Workflow tool 條目未讀；任務 C #1/#2 依前次源碼結論＋本 session runtime 工具面、codex/grok-build 源碼細節本次未重驗。

**致敬度快查（最弱）**：10 分鐘淺查、未讀兩邊系統提示詞全文、codex 問詢工具名未落實——定性結論可用、任何精確相似度數字禁用（源：zcode-saved-workflows.md §證據弱點自評）。

**整合腿新增限制**：本報告為材料綜合，未對任何源碼做獨立重驗；跨源結論的效力受「同源/移植關係」污染處已逐處標注（§6.3 #7）；ai-guide 側現狀描述以材料檔內的對照表為準，未重讀 135 系列卡核對。

---

## 10. 審查收口（muse＋codex 雙腿，2026-09-24）

雙腿 verdict 均 **GO-WITH-FIXES**（findings：`oss-survey/report-review-{muse,codex}.md`）。收斂結論已採納為本報告的使用方式：

### 10.1 共同修正：MVP 分揀（§6.1 的正確讀法）

**135.1 的 MVP 是 instruction compiler（產派工單靜態物），不是 daemon/runtime。** §6.1 的 29 條按「落差大小」排序，但落地須按「135.1 依賴序」分揀：

- **進 MVP（~13 條＋2 條僅語義）**：B 組 intent 防拉伸全組（PLAN_CHANGES 修訂流／Iteration policy＋Blocked stop 兩欄／outcomes-not-architecture／decisions＋evidence 欄）＋D 組派工介面 schema（ask<T> 式輸出契約／capability 枚舉／fail-loud 訊息）＋E 組 handoff schema 與 receipt 欄位形狀＋F 組審查契約三行（blocking 分類／anti-ratchet／audit-don't-author——皆為契約文字）＋A/C 組僅取宣告語義（corrupt→paused 一行規則／BudgetLimited 終態語義）。
- **延後（~13 條，歸 runtime／135.7／135.8）**：journal replay／inputHash／divergence 引擎（A 組機械體）／stall 偵測／共享池權重記帳／admission 限流器／reopen graph／eval 資產化——**只預留 receipt/journal 欄位形狀（seq/hash/事件名），此刻不建引擎**。
- **砍**：#28 retrospective 路由（已有 135.8，引用即可）。

### 10.2 雙腿指出的外推失效點（本報告結論使用限制）

1. **單一信任域假設失效**：三家的派工都在同 harness 內 fork——跨家族 bridge 派工沒有全域 admission、沒有共享 token 池，#11/#14 不可直搬。
2. **inputHash/divergence 類比錯誤**：journal divergence 守的是確定性 host-call；LLM 語義工作天然非確定，divergence 照搬會永遠開火——hash 只能用於機械面（檔＋參數），不能用於 prompt 面。
3. **stale-override 教訓方向反轉**：跨家族派工必須在呼叫點選 family/model（callee 能力派工時才發現）——model-routing resolver 留呼叫面是需求，不是 §4.5 所述的違規。
4. **樣本獨立性折價**：codex↔grok 疑同源、ZCode↔CC 疑移植，「多家都有 X」背書效力約剩 1.5 個獨立樣本——A 組恰是污染嫌疑最大組，優先序再降一檔。
5. **終態語義缺 settle 尾**：借來的 BudgetLimited 終態須延伸覆蓋 commit/push 等 outward 尾，否則一半風險面借了等於沒借。
6. **缺失模式（五源皆無、135.1 真正的未知工作量）**：部分失敗／重複派工的 at-least-once 語義、muse/codex/glm 異質回執正規化成單一 receipt schema、跨 repo/worktree 協調、按 family 價格延遲路由。

### 10.3 開工邊界（雙腿收斂版）

- **Slice 1（最小可用）**：schema-first compiler——ArcSpec／ArcPlan／DispatchSlice／receipt 四物欄位定義（含 B 組全＋D 組 #12/#13/#15＋E 組 #18/#19＋F 組三行語義）＋fail-loud 校驗＋PLAN_CHANGES 修訂流（git diff＋驗收腿複核）＋**拿一張真實 standard 卡端到端編出人類可手派的派工單**；muse 建議故意納入一張需 bridge 派工的卡做樣本，防 schema 長成單 harness 形狀。成功謂詞：marshal 不問 compiler 任何問題即可手派。
- **開工前 bounded design 決策群（合併雙腿約 8 項）**：①compiler/runtime 邊界畫線（哪些歸 135.7/135.8）②四物 artifact ownership（誰寫誰讀誰可改）③欄位二分（machine invariant vs LLM guidance）④ArcPlan 修訂權威（Deviations-only vs 重寫＋PLAN_CHANGES 誰複核）⑤binding 位置（resolver 留呼叫面、禁進模型呼叫面）⑥終態語義（BudgetLimited＋raise-cap＋settle 尾）⑦receipt minimum contract（第一版什麼證據才算 slice 完成）⑧跨家族欄位（family/model/帳本歸屬至少留形狀）。
- **明示非目標**：replay 引擎、admission 限流、eval 資產、compact 改動、六站模型重議。
- **#26 eval 資產化啟動判準**：「首批 N 張機器編譯派工單落袋後」（非時間點）。

### 10.4 報告其餘部分的效力邊界

§1-§5／§7-§9 的對照分析與背書判定經雙腿審查無修正項；§6.1 以 §10.1 分揀為準、§6.3/§9 作為 135.1 EP 的「已知未知」清單直接引用。

### 10.5 追記修正（user 挑戰觸發——「機械帳本不會其實早就做好了吧」）

§1 結論 2「機械化確定性檢查落後一個身位」的敘事**不準確，修正如下**：

**已在運行的帳本基礎（調查時未被計入「我們已有的」）**：
- 派工事件帳＝`.delegate-bridge/jobs/`（每 job 的 id/status/model/時間戳/回執——批量夜判讀腿以此機驗）
- liveness 流水＝`liveness.jsonl`（armed/heartbeat/collected/advisory 四態、323 行實運）＋bridge_waiter.py（1305 行）＋agent_liveness_sweep.py（682 行）
- 回執契約＝CollectionReceipt（terminal≠complete＋sink/anchor 機驗——實攔過假完成）
- hash 綁定＝restore-proven（sha256＋verified_at）
- 派工前執法＝decisions_pending.py lint --card（135.8 機制基礎）

**真缺的只有四個增量**：①帳本自動重播恢復未完成 slice（現靠 checkpoint＋人讀帳）②重放 inputHash 防禦閘 ③三家族異質回執正規化為單一 schema ④token 用量彙總成預算帳本。

**落點修正**：四增量大多歸 **135.7 collection 升級＋delegate-bridge repo**（bridge 側 ledger schema），不是 135.1。正確敘事＝「機械帳本地基早已在跑，135.1 編譯器蓋好、批量夜 #2 產生真實派工量後，135.7 做四增量升級」——不是「從零落後」。§10.1 的分揀結論（MVP 只留欄位形狀）不變，但理由從「我們沒有」改為「已有地基、增量等量」。
