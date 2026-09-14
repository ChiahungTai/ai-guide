---
name: at

description: "排程工作接續 — 在指定時間自動 resume 當前工作（CronCreate one-shot）"
when_to_use: "LLM provider reset usage 後需要自動接續工作時"
argument-hint: "HH:MM | 任務簡述（可選）"
allowed-tools: ["Read", "Write", "Bash", "Glob", "CronCreate", "CronDelete", "CronList"]
---

# /at — 排程工作接續

在指定時間自動 resume 當前工作。對應 Unix `at` 命令（one-shot 排程）。

適用 LLM provider usage reset 後自動接續。排程觸發時 host 必須開啟（Claude Code = terminal session；ZCode = app）。

> **與 `/handoff` 分工**：本命令是「時間接續」（usage 用盡，**自己 resume**）；要把工作交給**另一個** session/provider 並行或接手，用 [`/handoff`](../handoff/SKILL.md)。

> **與 `/usage-ping` 分工**：本命令時間後面要接**任務**（reset 後自動接續工作）；只寫時間、只叫醒 LLM 確認配額回來（最小 call 成本、不接任務），用 [`/usage-ping`](../usage-ping/SKILL.md)。

---

## 執行流程

### Phase 1：解析時間 + 捕獲 Context

1. **解析用戶輸入**：

   | 輸入格式 | 解析方式 | 範例 |
   |---------|---------|------|
   | `HH:MM` | 今天指定時間；已過 → 明天 | `14:30` → 今天 14:30 |

   **觸發時刻 T = 輸入 +1 分鐘**（秒數誤差防護；時間邏輯同 [usage-ping](../usage-ping/SKILL.md)）。計算 cron 表達式（5-field：`分 時 日 月 週`）用 T pinned 到具體日/月（當前日期以 `date` 輸出為準，跨日跨月交給 `date -v` 疊加**不手算**），DoW = `*`。**不做整點/半點提前 shift**——usage-ping CC 端的 `:00`/`:30` +1 jitter 是探測場景防早跑需求；本命令是接續任務，提前數十秒觸發無害（user 裁定不做）。

> **不支援相對時間**（`+Xh`/`+Xm`）：相對延遲須 LLM 自算換算成絕對時刻，註冊瞬間時刻已過會靜默滾到一年後才觸發。用戶給相對時間時，用 `date` 查當前時間換算成絕對時刻（跨日時明確向用戶確認目標日期），再排程。

2. **提取 task hint**：時間之後的所有文字為任務簡述（**任務目標** — resume 接續的依據）；無則標記「用戶未提供具體描述，resume 時看 git log 推斷進度」。

> **不捕獲 git snapshot**：/at 預設是「usage reset 後接續」，resume 時狀態可能已變（quota 期間其他進度）。context 只記**任務目標**，resume 時看**當前 git log/status** 知進度到哪 — 不比對排程時 snapshot（舊狀態無意義）。

### Phase 2：寫入 Context 檔案

> **路徑選擇理由**：判斷 auto mode 是否放行的條件是「路徑是否為 protected path」,與是否 gitignore 無關。`.claude/` 是 protected path(auto mode classifier 硬擋、accept-edits mode 彈框);`.at-contexts/` 不是 protected path,所有 edit mode 零摩擦放行。故 context 寫 `.at-contexts/`。

寫入 `.at-contexts/at-context-{YYYYMMDD-HHMM}.md`(排程時間戳,避免衝突)。

**Context 檔案格式**：

```markdown
---
scheduled_at: "{ISO 時間}"
resume_at: "{ISO 時間}"
project_path: "{當前專案路徑}"
---

# 排程接續任務

## 任務目標
{task hint}

## ⛔ 給 Resume LLM 的指令
這是排程任務（usage reset 後接續），不是閒聊。你必須：
1. 先執行 `git log --oneline -10` + `git status` 看**當前進度**（做到哪、剩什麼）
2. 根據任務目標 + 當前進度，接續未完成的工作（不比對排程時狀態 — quota 期間進度可能已變）
3. 完成後刪除此檔案
```

**寫 STATE.md**（session 結束）：若本 session 有轉向 / 卡點觀察，寫 repo root `STATE.md` 補「為什麼」（覆寫非累積；步驟見 [state-md-write](../_common/state-md-write.md)）。`.at-contexts` 維持一次性 ephemeral lifecycle（排程時建立 → resume 後刪、gitignore），STATE.md 是持久觀察層——**兩者不取代**（不同 lifecycle，不可混溶）。

> **本區現況**：`.at-contexts/` 只剩 `at-context-*`（`handoff --save` 寫檔已退場，交接改 `backlog task edit --append-notes` 掛卡）；`at-context-*` resume 後刪維持，夜間掃 7 天兜底（見 rule 協作約束）。

### Phase 3：建立 CronCreate

呼叫 `CronCreate`：

```
cron: "{分} {時} {日} {月} *"
recurring: false
prompt: |
  🔴 排程接續任務 — 用戶於 {scheduled_time} 排程此工作在 {resume_time} 自動接續。

  立即執行：
  1. 讀取 context 檔案：{context_file_path}（任務目標）
  2. 執行 `git log --oneline -10` + `git status` 看**當前進度**（不比對排程時 snapshot — quota 期間進度可能已變）
  3. 根據任務目標 + 當前進度，接續未完成的工作
  4. 完成後刪除 context 檔案 {context_file_path}

  ⛔ 禁止事項：
  - 禁止回答「目前沒有需要做的事」— 用戶明確排程了這次接續
  - 禁止靜默結束 — 如果無法判斷任務，產出 git 狀態報告
  - 禁止詢問用戶確認 — 這是自主執行模式

  如果 context 檔案不存在或無法判斷任務：
  → 執行 git status + git log -5 + git stash list
  → 產出「當前狀態報告」
  → 不要靜默結束
```

> `{context_file_path}` = `.at-contexts/at-context-{YYYYMMDD-HHMM}.md`（Phase 2 寫入的 context 檔路徑）

### Phase 4：確認 + 通知

印出排程摘要：

```
✅ 排程已建立（/at）
- Resume 時間：{HH:MM}（輸入 +1 分後的實際觸發時刻）
- Cron ID：{job_id}
- Context：{context_file_path}
- 任務：{task hint}
```

語音通知：`say -v Meijia -r 180 "已排程在 HH:MM 接續工作"`（報實際觸發時刻）

---

## Resume 後的行為

Resume 觸發時，LLM 應：

1. **讀 context 檔案** → 了解**任務目標**（`.at-contexts/` 非 protected path，讀取零摩擦）
2. **讀 STATE.md**（repo root，若存在）→ 補 **Last session 觀察**（卡在哪、為何轉向、下次起手點）——「為什麼」參考；**完成度走 recovery 事實層**（git + EP re-derive，見 [autonomous-execution](../autonomous-execution/SKILL.md)「Session 級 Recovery」），STATE 不覆蓋完成度
3. **看當前進度** → `git log --oneline -10` + `git status` 知做到哪（**不比對排程時 snapshot**，理由見 Phase 1）
4. **接續未完成** → 建進度提醒 sentinel（`touch /tmp/.claude-voice-pending`），根據任務目標 + 當前進度，自主完成剩餘（同 `/deep-work` 模式）
5. **清理** → 完成後刪除 context 檔案
6. **通知** → 清 sentinel（`rm -f /tmp/.claude-voice-pending`）+ 套 [voice-notification skill](../voice-notification/SKILL.md)「任務完成」樣板 say（隨機稱謂）

---

## 使用範例

```bash
# 指定時間接續（14:30 輸入 → 14:31 實際觸發）
/at 14:30

# 指定時間 + 任務簡述
/at 14:30 繼續 /implement docs/execution-plan.md 段落 3
```

---

## 執行約束

- **觸發時 host 必須開啟**：排程由 host 進程在觸發時刻 dispatch — Claude Code 是 terminal session、ZCode 是 app；關閉期間到點不觸發，重開後排程定義仍在但補觸發無保證，需接續就把 host 開到觸發時刻
- **生命週期因 harness 而異**：Claude Code 綁 session，session 結束排程即消失；ZCode automation 持久於 workspace（跨重啟存活、one-shot 跑完留 completed 記錄不自動刪）— 殘留檢查用 CronList、清理用 CronDelete。一次性接續用途足夠（善用 usage reset 後的配額窗口內接續工作）
- **one-shot miss 識別**：ZCode 上 one-shot 若觸發時刻 host 未開啟，記錄可能呈 `enabled=false`＋`lifecycleStatus=completed`＋`runCount=0` 且無 `lastRunAt`——外觀為 completed 但並未執行、無執行證據且仍佔名額；殘留判讀與 supersede 掃描**不可依賴 `runCount`/`lastRunAt` 判斷是否真的跑過**，以 `CronList` 現場狀態與 `.at-contexts/` 殘留為準
- **清理**：Resume 完成後必須刪除 context 檔案，避免殘留
- **多個排程**：若 `.at-contexts/` 已有 `at-context-*` 檔案，提示用戶確認是否有衝突
- **版控排除（一次性設定，與 auto-mode 放行無關）**：`.at-contexts/` 含任務目標描述，建議加入該專案 `.gitignore` 或全域 `core.excludesFile`，避免誤 commit
- **排程經濟**：每次觸發即消耗 quota（≈1 prompt + 全 context 重送）——排**資訊密集**的任務（一次量多指標，如同批多項驗證）、polling 型（usage-ping 類）保持最低頻率
- **語音通知**：遵循 `voice-notification` skill 規範
