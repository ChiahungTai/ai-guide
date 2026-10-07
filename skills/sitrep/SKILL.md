---
name: sitrep
description: "值星／接手 session 打一發看全況的唯讀即時快照——一次彙總七面各一行、異常面才展開：active 卡狀態、STATE.md 起手點、信箱 pending、watcher 態、bridge job 收線態、spawn subagent 進度、git 乾淨度；bridge 與 subagent 兩面必帶運行時間＋產出活性（卡住與做完沒回報都要現形）。純唯讀——只報告不處置：不處理信、不 re-arm watcher、不收線 job、不 kill sub、不 commit。觸發詞：sitrep、值星、現況快照、值星進度、信箱現況、全景快照、接手看況、卡住了嗎、做完怎麼沒回報。"
when_to_use: "值星 session 起手／中途巡邏／接手交接，要一眼看「現在做到哪、背景工作還活著嗎」時；user 說「看下現況」「sitrep」「值星快照」時。昨日回顧用 standup、深審用 state-review、自動修正用 daily-maintain——本命令只做現在快照。"
allowed-tools: [Bash, Read]
---

# sitrep：值星 session 唯讀即時全景快照

> **載入時機**：值星／接手 session 要一眼看全況（做到哪、信箱、watcher、bridge job、subagent、git），或懷疑背景工作「卡住了」／「做完了卻沒回來說」時載入。

## 定位與紅線（先讀）

- **唯讀 viewport**：七面各一行、異常面才展開；產出給人快速判讀——「講人話」是正當風格，一行講不清的才展開。
- **紅線——只報告，處置歸 session 判斷**（sitrep 自身零寫入、零處置）：
  - **不處理信**——`duty_receive process` 是 holder-gated 唯一處理面，sitrep 禁觸任何處理面
  - **不 re-arm watcher**——arm/stop 是 [mail-watch](../mail-watch/SKILL.md) 的寫入面；stale 只提示，不代 arm
  - **不收線 bridge job**——collect／sink 驗收是 caller 的活（sweep 本身就只標不殺）
  - **不 kill 卡住的 subagent**——卡住嫌疑只標記；殺不殺、要不要重派，session 決定
  - **不 commit／不 add**——止步 working tree 觀察
- **pending 分層措辭（禁越層宣稱）**：`receive status` 的 `pendingCount` 是 **delivery cursor 面**（未過收信處理游標）——措辭＝「未處理 N 封」，**禁宣稱「信都看過了」**。三屬互不代理：watcher 觀察游標（已看到的時間線）≠ delivery cursor（已處置）≠ 人類 SC INBOX seen/done（已判讀）。

## 七面清單（每面一行＋機械來源）

### 面 1：active 卡狀態

```bash
rg "^status:" backlog/tasks/*.md
```

一行＝非 Done 卡數＋`id 狀態` 列表；全 Done 也明說。

### 面 2：STATE.md 起手點

Read repo root `STATE.md`（Last session 觀察層）——取「卡在哪／為何轉向」＋「下次起手點」各一句（三要素用語對齊 [state-md-write](../_common/state-md-write.md)——STATE.md 無「弧標題」欄位）。缺席＝報「無 STATE.md（無觀察層）」，禁靜默跳過。

### 面 3：信箱 pending

```bash
dutymail receive status --address <alias>
```

- 對值星相關 alias 各查一行（alias 清單＝面 4 watcher status 列出的門牌；無 watcher 時用 session 已知門牌）
- binary 解析階梯（`DUTYMAIL_BIN` → PATH → plugin cache 最新版）單一源＝`scripts/duty_receive.py` `_resolve_binary()`——**禁手拼版本化 cache 路徑**
- CLI 不可達時 MCP 同面 fallback：delegate-bridge 的 `bridge_mail_status`（同面四欄：pendingCount／lastDeliverySeq／primaryCursor／liveBatch）
- 一行＝`<alias> pending=N（未處理，非已判讀）`

### 面 4：watcher 態

```bash
uv run python scripts/mail_waiter.py status
```

一行＝`desired`＋fresh/stale（status 自帶 armed_at 距今與 threshold 判定）。`desired=running` 但 stale＝提示重新 arm（只提示；arm 步驟見 mail-watch）。

### 面 5：bridge job 收線態（雙 state-root）

```bash
uv run python scripts/agent_liveness_sweep.py
```

- **耗時須知（跑之前讀）**：sweep 無上限參數——雙根 `jobs/*.jsonl` 全量逐檔讀（GB 級、只增不減），實測 30s+ 才一次性輸出。以 ≥300s 逾時呼叫；中途靜默屬正常，勿重跑勿中砍；逾時＝一行如實標「未收斂（逾時）」——ledger 體積失控本身就是 finding，處置歸 session。急巡（user 明說要快）可跳過本面，一行標「未掃（耗時面）」；值星起手／接手交接／懷疑卡住或收線檢查必跑完整 sweep
- 唯讀 reporter，預設雙根——ai-guide＋delegate-bridge 兩 workspace 的 ledger 都盤（值星實務橫跨兩 workspace，禁只看單根）
- 一行＝running-fresh／terminal-unclaimed／zombie-suspect 計數；異常類才展開 job id＋family＋最後活動
- 每個異常 job 帶**運行時間**（sweep 的「最後活動 X 前」欄）；**產出增長**＝對 running-fresh job 的 ledger 檔兩次取樣（間隔 30–60s，`stat -f "%z %m"`，同面 6 手法）——檔案＝`~/Github/<root 標籤>/.delegate-bridge/jobs/<job-id>.jsonl`（root 標籤＝sweep 展開行的 `@ai-guide`／`@delegate-bridge`）；size 增長＝在跑，停滯＝卡住嫌疑（事件流逐 turn 落盤，短窗無增長未必卡死——併「最後活動距今」判讀）；無 running job 時本子步驟跳過。**terminal 未收**（completed 但台帳無 collect 紀錄）與 **zombie 停滯**（>6h 無活動）兩種都要現形
- 台帳對接鍵＝job id（session-journal.md 六欄表）；補台帳／collect／殺 job 都歸 session

### 面 6：spawn subagent 進度（活性三訊號）

目錄布局（ZCode 端，已實證）：`~/.zcode/cli/agents/sess_<id>/agent_<id>/`——`metadata.json`（status 四態實證：running／completed／failed／stopped；description／cwd／createdAt／completedAt〔缺席退 `updatedAt`〕）＋`output.txt`（產出流，轉錄活性錨點）＋`task.output`（任務輸出檔；本面活性判定只消費前兩檔）。

```bash
# 活性掃描：mtime 距今＋size
ls -lt ~/.zcode/cli/agents/*/agent_*/output.txt 2>/dev/null | head -8
# running 標記清單
rg -l '"status":\s*"running"' ~/.zcode/cli/agents/*/agent_*/metadata.json 2>/dev/null
```

判讀三訊號（面 6 必帶運行時間＋產出活性）：

- **status 是意圖面，mtime 才是活性真相**——session 異常終止不會 finalize，metadata 殘留 running 標記是常態（存量長尾實證：running 標記遠多於真活在跑）。真活＝running 標記＋mtime 新
- **增長趨勢**：對嫌疑 agent 的 output.txt 兩次取樣（間隔 30–60s，`stat -f "%z %m" <file>`）——size 增長＝工作中；停滯＋running 標記＝**卡住嫌疑**
- **靜默終態**：metadata status ∈ {completed, failed, stopped}＋終態時間（`completedAt`，缺席退 `updatedAt`）距今近＋parent session 未消化＝**做完沒回報嫌疑**（本 session 收過結果的不算）——三態都要現形，failed 常帶 `error` 欄（展開時附一句）
- 下鑽：`rg -o '"description": "[^"]*"' <metadata.json>`（做什麼）＋ `"cwd"` 欄（哪個 repo）

一行＝真活數（增長中）／卡住嫌疑數／靜默終態嫌疑數（completed／failed／stopped 各自計），嫌疑者附 description 摘要＋最後活動距今（failed 加 error 摘要）。

### 面 7：git 乾淨度

```bash
git status --porcelain
git worktree list
```

一行＝clean／N 檔未提交＋在場 WT 清單（值星常有多卡 WT 並行，逐一列名）。

## 產出格式

```
sitrep @ <working repo>（HH:MM）
1/7 卡：<N> 張未結（air-XXX In Progress、…）／全 Done
2/7 STATE：<卡在哪→為何轉向→下次起手點>／無 STATE.md
3/7 信箱：<alias> pending=N（未處理）；…
4/7 watcher：running fresh（armed Xs 前）／stopped／stale（提示 re-arm）
5/7 bridge：fresh=N zombie=N terminal-unclaimed=N（異常展開：job-…｜family｜最後活動 X 前｜增長中／停滯）／未掃（急巡跳過）／未收斂（逾時）
6/7 sub：真活 N（增長中）／卡住嫌疑 N／靜默終態 N（completed/failed/stopped；description…｜X 分前）
7/7 git：clean／N 檔未提交＋WT：…（逐一列名）
```

正常面一行帶過；異常面（非零嫌疑、stale、terminal 未收、dirty）才在該行下展開 1–3 行細節。

## 分工（誰管什麼）

| 命令／機制 | 職責 | 與 sitrep 邊界 |
|---|---|---|
| [standup](../standup/SKILL.md) | 昨日跨 session 回顧 | sitrep＝現在快照，不回顧歷史 |
| [state-review](../state-review/SKILL.md) | 全 repo 深審（state-rot 盤點） | sitrep 一行快照，不做深審 |
| [daily-maintain](../daily-maintain/SKILL.md) | 自動修正＋commit 寫入面 | sitrep 零寫入 |
| mail_waiter／sweeper／liveness_sweep | 單面機制 | sitrep 是**消費端**——呼叫其唯讀面（status/sweep），不重刻機制 |
