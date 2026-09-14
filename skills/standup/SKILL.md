---
name: standup
description: "昨日活動 digest——跨 worktree session 聚合 + commit/kanban/SYSTEM-MAP transition。晨間簡報、昨日做了什麼、standup、morning briefing、跨 worktree 對話整理、session 摘要時使用。機械素材由 aggregate_sessions.py 萃取,LLM 寫敘事;輸出 body(無 `## ` header,delivery 由 invoker 決定——排程載體 append「## 📝 昨日活動」進 daily-report,或 /standup 直接在 chat 顯示)。"
when_to_use: 每日晨間回顧昨日活動、跨 worktree 整理同一 main repo 的對話紀錄、產出 morning briefing、standup 晨間簡報。觸發詞:standup、晨間簡報、昨日活動、morning briefing、跨 worktree session。
allowed-tools: ["Read", "Bash", "Glob", "Grep"]
---

# standup skill — 昨日活動 digest

產出「昨日活動 digest」**body**——跨 worktree session 敘事 + commit/kanban/SYSTEM-MAP transition。**只產 body,不加 `## ` header**(header `## 📝 昨日活動` 由 invoker 加:排程載體 append 進 daily-report;或 `/standup` 直接在 chat 顯示 body)。這是機器狀態層報告（test-regression/BSR——nightly-thin 任務，registry 反查表 A6）未覆蓋的人類活動層。

## 🔴 輸出紀律(text output 會逐字進 daily-report)

排程載體抓**所有 assistant text block** append 進 daily-report——**你的 text output 會逐字出現在報告裡**。因此:

- **所有分析走 thinking + tool calls**(Bash/Read/Grep)——這些不是 text output,不會被捕獲進報告
- **text 只 emit 一次、在最後**——完成所有分析後,一次輸出完整 body(從 `### 昨日 Commits` 開始)
- **禁止過程獨白 / 狀態回報 / meta 評論**——例如「我會遵循 standup skill 的工作流程」「let me check...」「已收集 N 個 session」「I have all the material. Producing the standup body now.」「接下來我要...」這類**全部禁止**(2026-07-08 首跑這些獨白滲進 daily-report,是品質缺陷)
- **第一段 text 就是 body 本身**,前面不得有任何鋪陳

## 機械素材萃取(必做第一步)

跑 `aggregate_sessions.py` 取結構化 session 素材(scan-project pattern:腳本撈素材,LLM 寫敘事;**雙 harness**——Claude JSONL＋ZCode db.sqlite,session dict 含 `harness` 欄,主力開發在 ZCode 後單掃 Claude 會漏互動工作〔2026-08-19 daily-report 實證〕):

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/aggregate_sessions.py --project-root .
# ZCode 載體（無 CLAUDE_SKILL_DIR 環境變數）用 ai-rules 實體絕對路徑：
# uv run python /Users/ctai/Github/ai-rules/skills/standup/scripts/aggregate_sessions.py --project-root .
```

產出 JSON:`{date, repo, worktrees[], sessions[]}`;每個 session 含 `worktree` / `first_user_msg` / `user_messages[]` / `tool_calls[]` / `conclusions[]`。

**Read 重複熱點（週任務選配——T2-4 可見性迴路）**：跑 `uv run python /Users/ctai/Github/ai-rules/skills/standup/scripts/read_hotspots.py`（ZCode db 面，7 天窗 (session,file) 重讀 top-N）——**≥5 次重讀＝Read 紀律衰減熱點**，列進報告供人工判讀（subagent 深挖與 main session 浪費是不同形態，判讀時區分；腳本只報數據不判斷）。

**範圍界定**(drift-tolerant):腳本用 `git worktree list` 列當前 main repo 的所有 wt;Claude 側 normalize(`_`≡`-`)比對 `~/.claude/projects/` 找 session dir,ZCode 側以 session.directory 精確比對 worktree 路徑——容忍 wt 改名歷史(hyphen/underscore drift)。**時間過濾**:JSONL top-level `timestamp`(UTC)轉 local tz 後取 date,比對昨日——非檔案 mtime。

## workflow

1. **機械素材**(上方 bash)→ 讀 JSON
2. **commit 敘事**:`git log --since="yesterday 00:00:00" --until="today 00:00:00" --oneline --stat` → 每 commit 的 type/scope/description + 變更區域
3. **進行中(uncommitted)**:`git status --porcelain` + `git diff --stat` → 推斷進行中工作
4. **empty-sessions 分支**:若 JSON `sessions` 空 → body 標「昨日無對話活動」,僅含 commit/uncommitted/今日建議子段(仍 output,不空白)
5. **session 敘事**(消費 JSON):每 session 2-3 句——用戶要求(`user_messages`,**過濾 system slash-commands** `/clear`、`/help`、skill 載入等)/ 主要操作(`tool_calls` 的 file_path/description,同檔去重)/ AI 結論(`conclusions` 最末幾段)。跨 wt 分組標示 wt 名。
6. **cross-session 主題**:跨 session 綜合(當日主軸、重複模式、多 session 協作)
7. **transition digest**:`git log -p --since="yesterday 00:00:00" -- "**/AGENTS.md" "**/CLAUDE.md" "backlog/tasks/**/*.md" "backlog/completed/**/*.md" "SYSTEM-MAP.md"` → 摘狀態變化(Capabilities ✅/📋/❌、backlog 卡 status 變動、SYSTEM-MAP 功能生命週期升降級)
8. **今日建議**:基於 uncommitted + 未完成 task,不憑空建議

## 輸出格式(body,無 `## ` header)

```
### 昨日 Commits（N 個）
- `{hash}` **type(scope)**: description
  - 變更：{區域}

### 進行中（未 Commit）
- **{檔案/區域}**: {推斷}

### Session 敘事（N 個 session,跨 M 個 worktree）

#### [{wt 名}] {首個 user msg 摘要}
- **用戶要求**: {摘要}
- **主要操作**: {關鍵 tool calls}
- **AI 結論**: {conclusions 摘要}

### 主題
- {cross-session 綜合}

### Transition（昨日狀態變化）
- ✅ 完成：[能力]
- 📋 新增 Backlog：[能力]
- SYSTEM-MAP：{功能生命週期變化}

### 今日建議
- [ ] {基於客觀狀態的建議}
```

## 執行約束

- **JSONL 不全量讀**:`aggregate_sessions.py` 已 line-by-line 處理;本 skill 不直接 Read session 檔
- **只摘要昨日**:不含更早活動(timestamp 過濾在腳本)
- **工具呼叫去重**:同檔同工具連續操作只記一次(腳本已 dedupe by `(name, target)`)
- **今日建議基於客觀狀態**(uncommitted / 未完成 task),不憑空
- **body 無 `## ` header**:header 是 invoker 職責
- **文檔引用附 repo 相對路徑**:提及 spec/EP/validate/daily-report 等檔案時附 repo 相對路徑(如 `ai-analysis/_tasks/<task>/spec.md`——repo 任務家下實際路徑;無 ai-analysis 樹的 repo 用 `00-tasks/<task>/spec.md`),不用裸檔名——body 會逐字進 daily-report,讀者需能直接定位
