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

### Phase 0：先結算再排程（checkpoint-first）

排程前依 [task-recovery](../_common/task-recovery.md)「寫入端」把工程狀態落進 durable 載體；at-context（bootstrap ticket，Phase 2）只承載**任務身份與指針**——不抄 read-set、規格、完成度：

1. 有 EP → 只 append EP 進度節（checkpoint 必要欄位＝task-recovery 寫入端表）；有卡且具 board 寫權 → 卡 notes 僅加一行「進度見 EP §X」指針——**board single-writer：無 board 寫權的 session 連指針行也不寫**，改在 ticket Pointers 註記 `card: <id>（未寫 notes，無權）`
2. 無 EP → 既有 `.agent-tmp/session-journal.md`；user 指定 report → 該 report
3. STATE.md 僅在本 session 確有轉向／卡點觀察時更新（觀察層職責不變）；禁把 read-set／完成度／EP checkpoint 抄進 STATE 或 ticket
4. UC 級任務排程前必須已有卡——**/at 不建卡**（排程不是建卡入口；臨時非 UC 工作走 `task_ref: ad-hoc`，見 Phase 2）

> **接續授權失效條款**：resume 卷開場＝新授權週期——**卷內既有授權全部失效，outward 動作一律 PENDING**（outward-action-consent「一次授權≠永久授權」的會話層投影）；本命令的自主執行指令**不得解讀為授權展期**——自主續工可以，outward 動作照 PENDING 規則回報待 user 拍板。例外＝conditional commit delegation 不從舊卷繼承、但可從 canonical arc state＋當次 gate evidence 重新建立（predicate＝commit skill），重新成立即依 outward rule 執行。條款句＝Phase 3 capsule invariant。

### Phase 1：解析時間 + 提取任務目標

1. **解析用戶輸入**：

   | 輸入格式 | 解析方式 | 範例 |
   |---------|---------|------|
   | `HH:MM` | 今天指定時間；已過 → 明天 | `14:30` → 今天 14:30 |

   **觸發時刻 T = 輸入 +1 分鐘**（秒數誤差防護；時間邏輯同 [usage-ping](../usage-ping/SKILL.md)）。計算 cron 表達式（5-field：`分 時 日 月 週`）用 T pinned 到具體日/月（當前日期以 `date` 輸出為準，跨日跨月交給 `date -v` 疊加**不手算**），DoW = `*`。**不做整點/半點提前 shift**。

> **不支援相對時間**（`+Xh`/`+Xm`）：相對延遲須換算成絕對時刻，註冊瞬間時刻已過會靜默滾到一年後才觸發。用戶給相對時間時，用 `date` 查當前時間換算成絕對時刻（跨日時明確向用戶確認目標日期），再排程。

2. **提取任務目標**：時間之後的所有文字為**任務目標一行**（進 ticket 的 goal 行）；詳細規格／read-set 住 durable owner（EP 進度節／卡 notes／journal），不展開進 ticket。

### Phase 2：寫入 Context 檔案（bootstrap ticket）

> **路徑選擇理由**：判斷 auto mode 是否放行的條件是「路徑是否為 protected path」，與是否 gitignore 無關。`.claude/` 是 protected path（auto mode classifier 硬擋、accept-edits mode 彈框）；`.at-contexts/` 不是 protected path，所有 edit mode 零摩擦放行。

寫入 `.at-contexts/at-context-{YYYYMMDD-HHMM}.md`（排程時間戳，避免衝突）。**固定骨架、禁自由散文**——缺段即 malformed（補齊再排程），不允許第 4 段「背景資料」（規格與 read-set 住 durable owner，ticket 只留指針）：

```markdown
---
scheduled_at: "{ISO 時間}"
resume_at: "{ISO 時間}"
project_path: "{當前專案路徑}"
task_ref: "{卡 id | ad-hoc}"
owner_ref: "{EP 路徑#進度節 | .agent-tmp/session-journal.md | none}"
---

# {任務目標一行}
```

- `task_ref`／`owner_ref`＝read-set 指針——「已有欄位不重抄」（[task-recovery](../_common/task-recovery.md)）
- ad-hoc 任務（無卡非 UC）：`task_ref: ad-hoc`＋一行 goal 即可；若任務已需要大量規格，代表不再 ad-hoc——先進 durable owner 再排程

> **本區現況**：`.at-contexts/` 只剩 `at-context-*`（`handoff --save` 寫檔已退場，交接改 `backlog task edit --append-notes` 掛卡）；ticket resume 後刪，夜間掃 7 天兜底。

### Phase 3：建立 CronCreate

呼叫 `CronCreate`，cron 欄位依 Phase 1 計算（`recurring: false` one-shot）。prompt capsule **八行封頂**：

```
🔴 /at resume — {resume_time}，task_ref: {task_ref}
context: {context_file_path}

1. 讀 context → 沿指針讀 durable owner（EP 進度節／卡／journal）→ 按 {repo 絕對路徑}/skills/_common/task-recovery.md 恢復順序核對當前實物（git log/status），接續剩餘工作
2. ⛔ 前卷 outward 授權已失效——commit/push/deploy/send 等 outward 一律 PENDING 等新授權；其餘工作自主完成
3. context 缺失／不可讀 → 以 task_ref 定位 durable owner；仍無法確立任務身份 → 產出狀態報告（首行標 `at-context missing: {path}`），禁靜默結束、禁推測另一任務
4. 刪 context 檔時機＝恢復已成功且（工作完成 OR 進度已 re-checkpoint 回 durable owner）
```

> **capsule invariants**：第 2、3 條是 /at 特有語義（授權失效＋fail-loud）——**禁併入 generic recovery 指針、禁後續簡化移除**（review 時當 gate 查）。`task_ref` 在 capsule 與 ticket 各留一次＝刻意的**身份冗餘**（ticket 被清淤誤刪後 fresh session 仍能辨認任務），非 read-set 投影。

### Phase 4：確認 + 通知

印出排程摘要：

```
✅ 排程已建立（/at）
- Resume 時間：{HH:MM}（輸入 +1 分後的實際觸發時刻）
- Cron ID：{job_id}
- Ticket：{context_file_path}
- task_ref：{task_ref}｜任務：{任務目標一行}
```

語音通知：`say -v Meijia -r 180 "已排程在 HH:MM 接續工作"`（報實際觸發時刻）

---

## Resume 後的行為

/at 場景落點＝讀 ticket → 按 [task-recovery](../_common/task-recovery.md) 恢復順序執行（定位任務→核對實物→恢復→接續）；完成通知沿用 [voice-notification](../voice-notification/SKILL.md)「任務完成」樣板（隨機稱謂）＋清 sentinel。

---

## 使用範例

```bash
# 指定時間接續（14:30 輸入 → 14:31 實際觸發）
/at 14:30

# 指定時間 + 任務目標一行（規格在 EP/卡，ticket 只留指針）
/at 14:30 繼續 EP 段落 3
```

---

## 執行約束

- **觸發時 host 必須開啟**：排程由 host 進程在觸發時刻 dispatch — Claude Code 是 terminal session、ZCode 是 app；關閉期間到點不觸發，重開後排程定義仍在但補觸發無保證，需接續就把 host 開到觸發時刻
- **生命週期因 harness 而異**：Claude 綁 session（session 結束排程即消失）；ZCode automation 持久於 workspace（跨重啟存活、one-shot 跑完留 completed 記錄不自動刪）——殘留檢查用 CronList、清理用 CronDelete
- **one-shot miss 識別**：ZCode 上 one-shot 若觸發時刻 host 未開啟，記錄可能呈 `enabled=false`＋`lifecycleStatus=completed`＋`runCount=0` 且無 `lastRunAt`——外觀 completed 但並未執行；判讀**不可依賴 `runCount`/`lastRunAt`**，以 `CronList` 現場狀態與 `.at-contexts/` 殘留為準
- **清理**：resume 完成（恢復成功＋工作完成或 re-checkpoint）後刪 ticket；夜間清淤以 mtime>7 天掃 `.at-contexts/`——**排程超過 7 天的 ticket 會被誤刪**（已知缺口：清淤應依 `resume_at`＋grace 判；現行 mtime 口徑僅適合 ≤7 天排程，長程排程需另定保留對策）
- **多個排程**：若 `.at-contexts/` 已有 `at-context-*` 檔案，提示用戶確認是否有衝突
- **版控排除（一次性設定）**：`.at-contexts/` 含任務目標描述，加入該專案 `.gitignore` 或全域 `core.excludesFile`
- **排程經濟**：每次觸發即消耗 quota（≈1 prompt + 全 context 重送）——排**資訊密集**的任務，polling 型（usage-ping 類）保持最低頻率
- **語音通知**：遵循 [voice-notification](../voice-notification/SKILL.md) 規範
