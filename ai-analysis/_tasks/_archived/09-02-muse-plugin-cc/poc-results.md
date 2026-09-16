# POC 實測記錄（R1/R3 完成、R2 半證）

> 2026-09-02，muse 1.0.1（1.0.1-R2006.1），macOS arm64。受控 run 檔：`poc-exec-run.jsonl`（同目錄）。

## R1：CLI 可跑 — ✅ 過

- binary：`/Users/ctai/.local/bin/muse`，`Muse Code 1.0.1 (1.0.1-R2006.1)`
- `muse exec --json --disable-approval --max-model-steps 10 "Reply with exactly: PONG"` → exit 0

## R3：`--json` JSONL 可解析 — ✅ 過

- 16 行全數 `JSON.parse` 成功
- 事件 schema：每行 `{schema_version, id, stream{kind,id}, sequence, recorded_at, record_type, payload_type, payload}`
- `payload_type` 詞彙表（本次觀察）：`runtime.command.accepted`、`session.run.linked`、`run.model.configured`、`task.lifecycle.status`、`task.lifecycle.completed`、`run.terminal.completed`
- 最終文字在 `run.terminal.completed` payload 的 `text` 欄（本次=`"PONG"`，正確）
- 豐富元資料：`model_id`、`request_id`、`response_id`（`resp_*` 開頭——CLI 走 Responses API 的直接證據）、串流統計（bytes_read/wire_events/time_to_first_event_ms）

## R2：headless 走訂閱計費 — 半證（第一層證據成立，歸屬核對待 user）

**第一層（已完成）**：env 無 `META_API_KEY` ✓、`~/.config/muse/` 只有 `auth.json`（簽入 credential，無 `muse auth set` 痕跡）✓ → 受控 run 成功＝必然使用簽入 credential＝訂閱綁定的那把（subscriptions.md:42）。
**加分訊號**：`run.model.configured` 顯示 `model_id: muse-spark-1.2-contributor`——文檔未記載的變體名（文檔只有 muse-spark-1.1/1.2），疑似訂閱帳號的模型層標記。
**帳務錨點**：`request_id: 2cc49bc5-a2b6-4b8d-b96f-33d40c9fe80d`、`response_id: resp_6a97fd44d4f49e1a5a7a41c9`（18:43 左右，session `01a061b5-4951-7551-81aa-b954a5f566f3`）。

**第二層（user 肉眼核對，判別實驗）**：
1. dev.meta.ai `/usage`（API dashboard）→ 這個 request **不應出現**（出現＝PAYG，R2 敗）
2. Accounts Center 訂閱用量 → 5h 窗口計數 **應 +1**（不動＝R2 敗）

## 附帶發現

- **muse 掃到 91 個 skills**（`~/.agents/skills` 等跨 agent 目錄），其中 `python-type-gap` 被判 malformed：`SKILL.md frontmatter must end with ---`——muse 的 frontmatter 驗證比其他家嚴，跨 harness skill 相容性需修
- workspace root 判定：cwd `/tmp` → root `/private/tmp`；正式委派以 repo cwd 為準
- stderr 與 stdout 分流：人類可讀狀態在 stderr、事件流在 stdout（bridge 設計可直接消費 stdout）

---

# 第二輪 POC（真委派，2026-09-02 晚）

## 委派 E2E — ✅ 過（poc-delegate.jsonl）

- 任務：修 `calc.py` 的 `add()` bug＋自跑 `python3 test_calc.py` 驗證
- muse 自己修（`a - b`→`a + b`）、自己跑驗證；**我獨立複驗 PASS**；exit 0
- 事件流豐富：`task.lifecycle.*` 全生命週期（proposed→accepted→scheduled→side_effect_intent→started→output→completed）、`tool.result`、`run.output.delta`（串流）

## Resume — ✅ 過（poc-resume.jsonl）

- `muse exec --session-id <uuid>` 同 session 續跑，正確回想「`add()` returned `a - b` instead of `a + b`」
- **session id 捕獲機制實證**：事件流第一行 `stream.id`（SM-7 的 ledger sessionId 來源已解）

## 網路任務 under default flags — ✅ 過（poc-network.jsonl）

- `--disable-approval` + 預設沙箱（proxy-only）下 curl https://example.com → 200、exit 0
- **實證 `--disable-approval` 涵蓋 network 子層 review**（permissions.md:90「新 host 停 for review」在 headless disable-approval 下不卡）——EP review C-P1-5 除雷

## 模型穩定性 — ⚠️ 新風險（R7）

4 個 runs 的 `run.model.configured`：PONG=contributor、bugfix=standard、resume=standard、network=contributor
→ **CLI 預設模型不穩定**（catalog/rollout 決定，非固定）。plugin 設計：S1 預設 flags 顯式 pin `--model muse-spark-1.2`（standard——數據不用於訓練，隱私保守），caller 可覆寫
→ 兩種模型在簽入 credential 下都可用（非 contributor 不影響可用性）

## contributor tier 文檔結論（models.md:29、pricing-rate-limits.md:27-29）

- contributor = 同 checkpoint 的折扣 tier，代價＝「prompts and completions may be used to train future Meta models」；standard = 不用於訓練
- **訂閱與 contributor 的綁定關係文檔未明說**；CLI 預設會落在 contributor（部分 runs）
- plugin README 必須警告：預設/貢獻者模型的隱私代價（對機密 repo 如 mosaic 重要）

## R2 帳務核對錨點（4 個，待 user dashboard 核對）

| # | 時間 | 模型 | 內容 |
|---|---|---|---|
| 1 | 18:43 | contributor | PONG |
| 2 | ~18:50 | standard | bugfix 委派 |
| 3 | ~18:55 | standard | resume 問答 |
| 4 | ~19:00 | contributor | curl 200 |

判別：全部不出現在 dev.meta.ai `/usage`＝走訂閱；特別注意 #2/#3（standard 模型）是否例外——若 standard runs 進 API dashboard 而 contributor runs 不進，代表訂閱只涵蓋 contributor tier（plugin 預設 pin contributor 就變成計費必要）。
