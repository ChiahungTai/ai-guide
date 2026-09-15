# Codex Compact 架構分析——機制全圖與對我們的借鏡

> 來源：`/Users/ctai/Github/codex`（Apache-2.0； sibling checkout，只讀分析，未改該 repo 任何檔）。
> 調查日：2026-09-15。分析視角：arch-thinking（use case → 責任/邊界 → 結構證據 → 限制）。
> 方法：直接讀 source（下表），未跑 codex 測試、未追 runtime 行為；行號是該 checkout 當下值。

## 0. 調查範圍與新鮮度

| 讀了什麼 | 路徑 | 規模/深度 |
|---|---|---|
| local compact 主流程 | `codex-rs/core/src/compact.rs` | 全讀 828 行 |
| 手動 compact 任務分派 | `codex-rs/core/src/tasks/compact.rs` | 全讀 76 行 |
| token-budget compact | `codex-rs/core/src/compact_token_budget.rs` | 全讀 84 行 |
| remote v2 compact | `codex-rs/core/src/compact_remote_v2.rs` | 結構＋核心段（全檔 1,252 行；attempt/images 子檔未深讀） |
| window token 狀態 | `codex-rs/core/src/session/context_window.rs` | 全讀 121 行 |
| token budget 預警 | `codex-rs/core/src/session/token_budget.rs` | 全讀 248 行 |
| window state | `codex-rs/core/src/state/auto_compact_window.rs` | 核心段約 120 行 |
| 歷史替換＋新 window | `codex-rs/core/src/session/mod.rs` §replace_compacted_history（L3980-4058）、§start_new_context_window（L4445-4496） | 精讀兩函式 |
| turn 層觸發點 | `codex-rs/core/src/session/turn.rs`（rg 命中行） | 觸發位點 |
| hook payload | `codex-rs/hooks/src/events/compact.rs`（rg 命中行） | 欄位列舉 |
| prompt 模板 | `codex-rs/prompts/templates/compact/{prompt.md,summary_prefix.md}` | 全讀（prompt.md 9 行、summary_prefix.md 空檔） |
| TUI 入口 | `codex-rs/tui/src/slash_command.rs`（rg 命中行） | 一行描述 |
| rollout trace | `codex-rs/rollout-trace/src/compaction.rs` 前 100 行 | checkpoint 語義 |
| config schema | `codex-rs/core/config.schema.json` §compact_prompt 等 | 欄位描述 |

未驗證：remote v2 的 attempt 重試細節與 image budget 演算法全文、guardian review session 的 compact 用法全文、
TUI `/compact` dispatch 全路徑、`docs/` 無 compact 專文（rg 確認零命中）、實際跑起來的行為。

## 1. Use case 定位（一句話）

在 codex，compact 是**第一等 runtime 機制**：由 turn loop 擁有的 context-window 生命週期管理
（觸發 → 摘要/清空 → 歷史替換 → 持久化 checkpoint → 通知），不是使用者的手動整理術。
對照我們：compact 本體是 harness 擁有的黑盒，`compact-prep` skill 只能做「壓縮前外部化＋壓縮後恢復指針」。
這個**擁有權差異**是後面一切對照的前提：codex 能保證 replacement 語義，我們只能保證落檔材料。

## 2. 總架構：三策略 × 三觸發 × 多階段

### 2.1 策略分派（`tasks/compact.rs` 手動路徑）

手動 `/compact` 進 `CompactTask` 後按序分派，只走一條：

1. `Feature::TokenBudget` 開 → `compact_token_budget::run_manual_compact_task`（無摘要，直接開新 window）。
2. 否則看 provider 能力 `remote_compaction`：`V2` → `compact_remote_v2::run_remote_compact_task`（server 端做）。
3. `Unsupported` → `compact::run_compact_task`（local：用當前 model 跑一輪摘要 turn 再替換）。

三策略**共用同一 lifecycle 殼**：pre-compact hooks → 主體 → post-compact hooks →
`ContextCompaction` turn item（started/completed 事件）→ analytics。token-budget 版註解明說：
即使跳過摘要也要走同一 lifecycle，讓 hooks 與 turn items 觀測到一致事件。

### 2.2 觸發（三種，`CompactionTrigger`）

- Manual：user 下 `/compact`（standalone turn，自己 capture 新 step）。
- Auto：turn loop 內聯觸發（pre-turn 精確觸發＋mid-turn 迴圈內觸發，見 §4），不佔用一個獨立 user turn。
- （語義上第三種）model 切換觸發：`comp_hash` 變了 → pre-sampling 先跑 previous-model inline compact
  （`turn.rs` §maybe_run_previous_model_inline_compact），理由是不同模型的壓縮相容雜湊不同，
  摘要必須由「舊模型對自己歷史的理解」來做。

### 2.3 階段（`CompactionPhase`）

至少有 `StandaloneTurn`（手動）與 `PreTurn`（turn 前）。PreTurn 有特殊錯誤語義：
`SessionBudgetExceeded` 在 PreTurn 不向 user 發 error event（先保住 incoming prompt 再回報），
一般階段才發。這是「壓縮發生在 turn 邊界上」的補償邏輯：壓縮失敗不能吃掉 user 剛送的 prompt。

## 3. 三策略詳解

### 3.1 Local（`compact.rs`，預設形態）

流程（`run_compact_task_inner_impl`）：

1. 發 `ContextCompaction` turn-item-started。
2. 把 compaction prompt（`config.compact_prompt` 或預設 `SUMMARIZATION_PROMPT`，見 §7）
    append 進**複製出來的 history**（注意：是 clone 後操作，不污染 live history），
   以正常 turn 形態向 model 要摘要（含 stream 重試、budget/context 錯誤分流，見 §9）。
3. 從該 turn 取**最後一則 assistant message**當 `summary_suffix`，拼 `SUMMARY_PREFIX + suffix` 成 `summary_text`。
4. 收集舊 history 全部 user messages（排除已是 summary 的——`is_summary_message` 認 prefix；
   guardian ThreadOwned 模式保留 item id 否則重產——rollback 對帳用）。
5. `build_compacted_history`：retained user messages（由新到舊選，最多 `COMPACT_USER_MESSAGE_MAX_TOKENS = 20_000`
   tokens，超了截斷最舊一則）＋最後一則 summary（空摘要填 `(no summary available)`，永不產空 history）。
6. 依 `InitialContextInjection` 決定是否注入 initial context（見 §5）。
7. `advance_auto_compact_window` 取新 window 編號＋ids（見 §6）。
8. `replace_compacted_history` 原子替換 live history＋持久化 checkpoint（見 §8）。
9. `recompute_token_usage` 重算用量；發 turn-item-completed；**固定發一條 Warning**：
   長 thread＋多次 compact 會降準，能開新 thread 就開新的。

關鍵語義：**tool calls、assistant 推理、system/developer 訊息全部丟，只留 user 原話（20k 上限）＋一篇摘要**。
摘要的 factual anchor 只有 user messages；tool 證據面完全不保留（靠摘要轉述）。

### 3.2 Remote v2（`compact_remote_v2.rs`，server 端做）

差異只在「摘要誰做、保留什麼」，lifecycle 殼相同：

- 向 server 發專用 compaction request（attempt 層含追蹤：每個 checkpoint 一個穩定 compaction id，
  每次 request 重試各一個 request id；trace 記 input history vs replacement history 兩份）。
- Replacement 歷史＝**retained（最多 `RETAINED_MESSAGE_TOKEN_BUDGET = 64_000` tokens）＋ server 回的 compaction output**。
- Retained 篩選（`is_retained_for_remote_compaction_v2`，group 層級）：
  user+HookPrompt 留；developer 只在 `RetainClientDeveloperMessages` 開且 client-authored 才留，其餘全丟；
  agent message 丟 descendent progress 與 FINAL_ANSWER，且單則 >10k tokens 丟。
- 圖片另有 budget（`CompactionImageBudget` feature 開關；analytics 記 retained_image_count）。
- 失敗有 **model fallback**：換 fallback step 的 model 重跑一次（`should_retry_with_current_model` 判定；
  telemetry 記 fallback 事件；fallback 再敗回原 error）。
- stream 重試預算比一般 turn 小（`MAX_REMOTE_COMPACTION_V2_STREAM_RETRIES = 2`，註解明說 compact 本來就跑得久）。

### 3.3 Token-budget（`compact_token_budget.rs`，無摘要清空）

- 不跑 model、不跑 server：直接 `start_new_context_window`（全新 initial context＋可選 retained client developer messages）。
- 但**仍走 pre/post compact hooks＋ContextCompaction turn item**，外部觀測面與另兩條一致。
- 搭配 §6 的兩段式預警（reminder＋fallback prompt）使用：這條策略假設「model 已被提前警告、
  把重要事寫進 history notes 類擴充」，所以清空是安全的。這是三策略裡對 model 自律要求最高的。

## 4. Auto-compact 觸發位點（turn loop 內）

`session/turn.rs` 至少四個觸發位：

1. **Pre-sampling compact**（turn 正式 sampling 前）：先跑 previous-model compact（comp_hash 變了才跑），
   再看 `token_status.token_limit_reached`，到了就地 compact。註解留 TODO：目前是事後觸發，
   理想是 preemptive（context 更新＋diff＋user input 進來前先算會不會爆）。
2. **Mid-turn 迴圈內**：每次迭代重算 token status；`take_new_context_window_request() || token_limit_reached`
   → roll over（token-budget 形態開新 window 或跑 compact）。註解說：只要 compact 能把用量打到遠低於上限，
   就不怕迴圈。
3. **Guardian budget**：guardian review 的 budget 觸發 compact，但**每 model step 只 retry 一次**
  （`guardian_budget_compacted` 旗），無效 compact 不能 loop；且只有 summarizing compact（local/remote，
   非 token-budget 清空）能保住 action＋evidence。
4. **Fallback prompt 互斥**：`allow_auto_compact_fallback = !should_roll_over && !token_limit_reached`——
   已經在 roll over 就不再塞 fallback prompt，避免雙重觸發。

## 5. Initial context 注入（replacement 語義的關鍵分支）

`InitialContextInjection` 兩形態（`compact.rs` L71-77，註解寫了訓練語義理由）：

- `DoNotInject`（pre-turn／手動用）：replacement 只有 retained＋summary，`reference_context_item` 清掉；
  下一個正常 turn 會**完整重注** initial context。代價是一次全量重注，語義最乾淨。
- `BeforeLastUserMessage`（mid-turn 用）：model 被訓練成「mid-turn compact 後 summary 是 history 最後一項」，
  所以必須把 initial context 插在**最後一則真 user message 之前**（找不到真 user msg 就插 summary 前；
  再找不到就插 compaction item 前；都沒有才 append）。此時 `reference_context_item` 設為當前 step 的
  turn-context 快照，讓後續 turn 只發 context diff 不再全注。

`insert_initial_context_before_last_real_user_or_summary` 的 fallback 鏈寫得很細，
連「remote compact 只回 compaction items」的退化形態都處理了。這是整個 compact 實作裡
**邊界條件最密**的一塊。

附帶：`WorldState` baseline 在 compaction 起點必須是 full snapshot（`replace_compacted_history`
註解），mid-turn/full 兩路徑都要帶；live world-state 變化可在 turn 內獨立推進 baseline。

## 6. Window state 與計費口徑（`state/auto_compact_window.rs`＋`context_window.rs`）

`AutoCompactWindow` 持有：window_number（saturating +1）、三代 window ids
（first／previous／current，Uuid v7；current 每 advance 重產）、new_context_window_requested、
prefill baseline、兩個 once-per-window claims（reminder、fallback）。

- `advance()` 同時清 request＋兩個 claims：新 window 重新取得預警資格。
- Prefill 有兩種（`ServerObserved` 優先，`Estimated` 兜底）：resume／重算的估計值會被第一次 server
  usage 樣本取代；且只取該 response 的 input 側當 baseline，output 算 body 增長。
- 計費口徑 `model_auto_compact_token_limit_scope`：
  `Total`＝整窗用量直接比 model 的 auto_compact_token_limit；
  `BodyAfterPrefix`＝（用量 − prefill）比可配的 `model_auto_compact_token_limit`（config 或 model 預設）。
  full context window 是獨立硬頂（`resolved_context_window × effective_percent`），與 scope 無關。
- `token_limit_reached`＝（scope 用量 ≥ scope 上限＋fallback buffer）或（全量 ≥ 全窗硬頂）。
  fallback buffer 只有在配了 fallback prompt 時才保留（§token_budget `maybe_record` 的配套）。
- `base_window_tokens_remaining` 取兩口徑剩餘的 min：reminder／fallback 的觸發標尺。

## 7. Prompt 面（可配、模板化）

- `SUMMARIZATION_PROMPT`（`prompts/templates/compact/prompt.md`，9 行）：
  定義任務為 CONTEXT CHECKPOINT COMPACTION，產物是給下一個 LLM 的 handoff summary；
  四要項：進度＋決策／context-約束-偏好／剩餘下一步／繼續所需的關鍵資料-範例-引用；
  風格：concise、structured、seamless continue。注意：**沒有 verbatim 要求、沒有 preserve-list 結構**。
- `SUMMARY_PREFIX`（`summary_prefix.md`——本 checkout 為空檔；`prompts/src/compact.rs:2` 以 `include_str!` 載入即空字串）：本 checkout 無導語文本。`is_summary_message` 的 prefix 匹配呼叫仍在（`compact.rs` 內 `starts_with` 用法），但匹配對象為空前綴＋換行，識別力存疑——重驗時以當下檔內容為準。
- 可配點：`config.compact_prompt`（整段換掉）、`experimental_compact_prompt_file`（檔案載入）。
  兩者都是「換整段 prompt」，沒有段落級開關。

## 8. 持久化與可觀測面

### 8.1 Rollout checkpoint（`replace_compacted_history`，L3980-4058）

一次 compact 落一個 `RolloutItem::Compacted`，欄位：summary message、**replacement_history 全份**、
retained_context、guardian_history、mcp resource origins、window 三代 ids、compaction_response_id、
當下 token record。後面再追 `WorldState`（full baseline，在 replacement 之後，順序有要求）、
`TurnContext`（有才落）、applied settings event（凍結的 turn context 不得覆蓋現行 settings）。
寫前先拿 settings 持久化鎖，防止後到的更新超車。寫完排一個 `SessionStartSource::Compact`，
讓下一個 session-start 觀測到「我是從 compact 恢復的」。

rollback 語義：guardian ThreadOwned 模式把 `compaction_model_hash` 寫進 checkpoint metadata，
讓 rollback 能把重建的 message 對回 thread 擁有的 retained evidence（`collect_annotated_user_messages`
的 Preserve／Regenerate 分支即為此服務）。

### 8.2 Hooks（`hooks/src/events/compact.rs`）

- `PreCompactRequest`／`PostCompactRequest` 皆帶：session_id、turn_id、subagent ctx、cwd、
  transcript_path、model、trigger（字串）。Pre 可 `should_stop` 中斷 compact（→ TurnAborted＋analytics 記 Interrupted）；
  Post 的 stop 發生在成功後，同樣轉 TurnAborted（local 路徑；token-budget 路徑同）。
- 這是**因果位置正確**的擴充點：pre 在摘要前（可注入材料／可擋）、post 在替換後（可做恢復）。
  對照我們：ZCode 的 SessionStart(compact) 實測是死路（compact 不派發），Claude 端才有 raw-tail 注入。
  codex 這裡證明了「compact 前後各一個第一等 hook」是該有的形狀。

### 8.3 Analytics（`compact.rs` §CompactionAnalyticsAttempt）

每趟記：thread／turn、trigger／reason／implementation／phase、strategy（寫死 `Memento`）、
status（Completed／Interrupted／Failed 三態，由 result 映射，中斷與失敗分開）、error kind＋http status、
**before／after active tokens**（after 在 track 當下重讀）、retained images、summary tokens、
cache 讀寫 tokens、起止 unix time＋duration_ms。before 取「開始時總用量」，
remote v2 則用 server 回的 usage 覆寫（input→before，output→summary）。

### 8.4 TUI

`/compact` 一鍵，描述只有一句 "summarize conversation to prevent hitting the context limit"。
成功後固定 Warning（長 thread＋多次 compact 降準，呼籲開新 thread）。TUI 另有 compaction 專用
tests（含 slash dispatch），表示這是受測的第一等命令。

## 9. 失敗與重試語義（分家得很細）

| 錯誤 | 處理 |
|---|---|
| stream 一般錯誤 | backoff 重連，最多 `stream_max_retries`（remote v2 固定 2） |
| Interrupted／TurnAborted | 直接回傳，不重試、不發 error event |
| SessionBudgetExceeded | 記 telemetry；PreTurn 相不發 error event（保 prompt），其餘發 |
| ContextWindowExceeded（連摘要 turn 自身都塞不下） | 從最舊 history item 逐項 trim（保 prefix cache、保近期），retries 歸零重來；只剩 1 項還爆 → 設 total_tokens_full＋分相發錯 |
| remote v2 失敗 | 符合 `should_retry_with_current_model` 且有 fallback step → 換 model 重跑一次並記 telemetry，否則回原 error |
| guardian budget compact 無效 | 每 step 只一次，不 loop |

## 10. 對我們的對照與可借鏡點

以下按「改動成本由小到大」排；每條標它對應我們哪個現有物。

1. **Warning 文案**：codex 在每次 compact 成功後固定提醒「長 thread＋多次 compact 降準，開新 thread」。
   我們可在 `compact-prep` 步驟 4 的交付確認裡加一句同義提醒（或記入 STATE 起手點）。成本最小。
2. **摘要 prompt 四要項**：進度＋決策／約束偏好／下一步／關鍵資料引用。我們的 preserve-list 比它細
   （已讀改路徑、測試 verbatim、懸掛動作、計數），**不需要降級對齊**；但可借「handoff summary 給下一個 LLM」
   的 framing，檢查 compact-prep 產物是否每段都回答「下一個 session 怎麼用」。
3. **Pre／Post 兩鉤**：codex 證明正確形狀是壓縮前後各一鉤。我們現況：ZCode 無（死路）、Claude 只有 post 側 raw-tail。
   pre 側目前只能靠「請 user 先跑 compact-prep 再 /compact」的人工程序補；若將來 harness 開鉤，
   compact-prep 步驟 2（落檔）是天然的 pre-compact hook body，步驟 5（讀檔恢復）是 post-compact body。
   建議把 skill 內步驟按 pre／post 標好，屆時整段搬。
4. **Window 編號＋三代 ids**：我們的 compact-context 檔只有 date 後綴，無代際鏈。
   可借：檔頭加 `window_number`（本 session 第幾次 compact）＋ `previous_file` 指針，形成可追溯鏈；
   compact-audit 的三色比對也可按 window 歸檔。這是純約定，零依賴。
5. **Retained budget 概念**：local 20k user-tokens、remote 64k。對應我們的實測「/compact 壓掉 verbatim」：
   codex 的答案是「user 原話保留＋tool 證據全丟」，而我們的答案是「落檔保 verbatim」。
   兩者互補不衝突；但值得在 compact-prep 明寫一句：**harness 側保留的主要是 user 原話，tool 輸出靠我們的落檔**，
   讓 user 理解為什麼落檔不能省。
6. **Reminder／fallback 兩段預警**：用量接近上限先塞 reminder（once per window），歸零再塞 fallback prompt。
   我們無用量計可 hook，但有等價物：`/at` 的 usage-reset 接續＋STATE 觀察層。
   可借的是「once-per-window claim」語義：同一次 compact 週期內，同一提醒只發一次（防洗版）。
   若將來做自動化 compact 提醒，記得帶 claim。
7. **計費口徑 BodyAfterPrefix**：把 prefix（system＋initial context）排除在觸發標尺外，只看 body 增長。
   對我們的意義是方法論：評估「session 有多肥」時，user 任務增量與 harness prefix 要分開看；
   compact-audit 抽樣時同理（別把 prefix 當任務訊號）。
8. **Checkpoint 持久化**：codex 每趟落 replacement 全份＋window ids＋token before／after。
   我們等價物是 compact-context 檔＋（選配）compact-audit。差距：我們沒記 before／after 用量
   （拿不到）、沒把 replacement（即壓縮摘要本體）存檔。可借：compact-audit 跑的時候把摘要本體一併存檔，
   與外部化檔放同一目錄，形成「摘要＋落檔」成對材料。
9. **comp_hash 觸發**：模型切了就重壓。這是 harness 內語義，我們做不了；但對應一條操作紀律：
   **換主力模型後的第一個大任務前，先 compact 一次**（讓新模型在乾淨 window 起跑，而不是在舊模型的殘留脈絡裡接）。
   可考慮寫進 model-routing 或 at skill 的操作段。
10. **不做的**：server 端壓縮、image budget、guardian 專線——都是 harness 內能力，無對應借鏡點，
    列在這裡是為了說明「已看過，不適用」，不是遺漏。

## 11. 限制與未驗證

- 只讀 source，未跑 codex 單測、未實際觸發 compact 看行為；concurrency（compaction 與 turn 並行）只看了鎖的形狀，
  沒驗死鎖面。
- remote v2 的 attempt／images 子檔只看了函式簽名層；guardian review session 的 compact 調用只看了 rg 命中行。
- 行號會隨 codex 上游演進漂移；本報告的價值在機制圖，不在行號錨。將來重驗時以檔名＋符號名（`build_compacted_history`、
  `replace_compacted_history`、`AutoCompactWindow`、`maybe_record`）為錨重找。
- 本報告描述行為與設計，未複製 codex 程式碼（Apache-2.0 雖允許，仍只引最小識別片段如常數名與 prompt 大意）。
