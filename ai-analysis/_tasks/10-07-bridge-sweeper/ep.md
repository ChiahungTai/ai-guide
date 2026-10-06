# EP — bridge-ledger-sweeper：prompt 邊界收線 backstop（AIR-267）

> baseline：`cebc18bf`（main，2026-10-07 開工時點）
> 裁決源：tri 三方（muse＋codex 討論腿＋GLM-5.3 裁決，2026-10-07；brief＝primary repo
> `.agent-tmp/bridge-sweeper-brief.md`；verdict 全文＝卡 notes 所指 job finalText）。

## 核心原則（invariants）

1. **提醒面非處置面**：sweeper 只出一行 advisory（值變化才出聲）——處置（re-arm/show/收線）恆歸 session LLM；絕不自動 arm/stop/寫 ledger。
2. **機械真相源＝liveness 台帳**（`<repo>/.agent-tmp/liveness.jsonl`——schema liveness/1：armed/heartbeat/collected/advisory/rearmed，bridge_waiter 機器側寫入）；在場判據＝armed−collected 配對＋heartbeat 新鮮度，**禁 pgrep**（跨 session false-covered——tri muse 最大風險）。
3. **語義分層**（tri codex）：sweeper 只報機械層——措辭恆為「**可能未收**」；「session 已接收/驗收」是另一層，sweeper 零宣稱（一次 show≠真正消費）。
4. **fail-soft 恆安靜**：face/台帳任何失敗＝該檔 stderr 註記＋零 stdout＋exit 0——絕不擋 prompt、絕不轟炸。
5. **owner 分工凍結**：sweeper=prompt 邊界提醒；`watcher_pairing_nag`（Stop 配對）＝既有自有；liveness 台帤=waiter 自有；sweeper 只讀不寫 liveness。
6. **out of scope**：reconcile 變異（waiter T7 擁有）、「worker 活著 ledger 無行」（無可靠 process→job identity——只會假警報）、bridge 原生 retrieved_at/exported_at（D——併批次⑥後續信）。

## 偵測規則（每輪掃描；值變化才出聲）

資料面：`bridge_runs --json`（binary 經 duty_receive `_resolve_binary` 同源解析——唯讀 face）⋈ liveness.jsonl 事件流（per jobId 取最新事件＋heartbeat 最新 ts）。

| 態 | 判據 | 輸出（一行） |
|---|---|---|
| R1 孤兒 running | running 行 且 該 jobId 無 armed 事件、或 armed 但 heartbeat 逾新鮮度窗（default 30 分鐘，可調——tri-panel J-4 修正：原 15 違 waiter 20m 合法輪詢間距契約） | `[bridge-sweeper] running job <id> 無活 waiter——恢復 playbook：arm waiter` |
| R2 terminal 未收 | terminal(completed) 行 且 無 collected 事件 且 終態逾齡（default 30 分鐘） | `[bridge-sweeper] <N> 個 terminal job 可能未收（<ids 前 3>）——收線：bridge_show` |
| 乾淨 | 以上皆無 | 靜默（零 stdout） |

- terminal 非 completed（failed-\* 等）不提醒（失敗態處置是 dispatch 語義非收線語義——v1 收窄；記 skill known limitation）。
- liveness 缺席（新機器/清過 .agent-tmp）＝R2 退化不可判——只跑 R1（runs 自身可判）；stderr 註記不轟炸。
- amendment（tri-panel 修復 J-2，2026-10-07）：R2 前提＝liveness 有 armed 痕跡（真孤兒類）；無痕跡（pre-liveness/手動收線）不可判安靜——AC5 smoke 實證全報＝578 行誤報洪水。

## 節流與安靜（tri Q3 收斂；先例＝duty_mailbox_monitor）

- **SessionStart**：全掃（無節流）。
- **UserPromptSubmit**：90s 節流窗（state 記 last_scan_at）＋**anomaly signature 去重**（R1/R2 集合的 signature 雜湊==baseline→靜默；變化才出聲＋更新 baseline）。
- **cwd eligibility gate**：cwd 在本 repo（或帶 liveness 台帳的 repo）才跑；否則零查詢零輸出。
- state：`${XDG_STATE_HOME:-~/.local/state}/ai-guide/bridge-sweeper/<safe_session_id>.json`（0600 atomic；路徑可注入——測試 tmp）。

## 段落

### S1 — `scripts/bridge_sweeper.py`（核心模組＋CLI）

- `scan_once(runner, liveness_events, now)` 純函式（injectable runner 回 runs JSON、events 為已解析 list）→ advisories list；`run_hook(boundary)`＝eligibility→節流→掃描→signature 去重→輸出。
- hook 前導 `hooks/bridge_ledger_sweeper.py`（stdin payload→boundary 判定→importlib 載入核心——與 duty_receive hook 同形）。
- 安裝註冊＝governance `install.py` 面（SessionStart＋UserPromptSubmit 兩條目，sync additionalContext 通道）。

### S2 — wt-close drain（小修）

`scripts/wt-close.sh`：移除 WT 前，若 `<wt>/.delegate-bridge/jobs/` 或 `<wt>/.agent-tmp/liveness.jsonl` 在場→歸檔至 `~/.agents/bridge-ledger-archive/<wt-basename>-<YYYYMMDD-HHMMSS>/`（0600、防碰撞時間戳命名；v1 無 TTL/GC——量測後再議）；歸檔清單一行輸出（preflight 與 full 皆跑）。

### S3 — tests（`tests/test_bridge_sweeper.py`）

fixture：fake runs JSON＋liveness 事件 list 注入（零真 bridge 呼叫）；tmp state dir。
TC-S1 R1 兩形（無 armed／armed 但 heartbeat 逾窗）；TC-S2 R2（terminal 無 collected 逾齡出聲／未逾齡靜默／有 collected 靜默）；TC-S3 非 completed terminal 不提醒；TC-S4 節流（窗內第二掃靜默）＋signature 去重（同值靜默、值變出聲）；TC-S5 fail-soft（runs 拋錯→零 stdout exit 0）；TC-S6 liveness 缺席退化（只 R1）；TC-S7 eligibility gate（非 repo cwd 零查詢）；TC-S8 drain（造臨時 WT 形目錄→wt-close 段函式歸檔→0600＋內容在場）。

### S4 — 安裝＋文檔

install.py 註冊面＋`skills/bridge-dispatch/SKILL.md`「Dispatch⇄collection」節補 sweeper 一行（prompt 邊界腿——家族分工表：waiter=時間軸/sweeper=prompt 邊界/nag=Stop 配對）。

## 驗收映射

AC1=TC-S1/S2；AC2=TC-S4/S5/S7＋eligibility 實測；AC3=輸出措辭 rg 釘（「可能未收」在場、「已驗收/已消費」零命中）；AC4=TC-S8＋wt-close preflight/full 綠；AC5=主 session 真場 smoke（乾淨安靜＋孤兒注入出聲）＋drain 演練收執。

## 完成閘

`uv run pytest tests/test_bridge_sweeper.py -v` 全綠＋全套無新失敗＋ruff clean＋AC5 smoke 收執落卡。
