# EP — 值星收信處理器（duty receive adapter，AIR-254.3）

> baseline：`2556afdd`（main，2026-10-06 開工時點）
> 裁決源（read-only，住 delegate-bridge repo）：
> `00-tasks/2026-10/10-04-dutymail/references/address-model-synthesis.md`、
> `inbox-uc-synthesis.md`、`cutover-arch-report.md`。
> dutymail CLI＝plugin 出貨 3.1.0（`~/.zcode/cli/plugins/cache/delegate-market/delegate/3.1.0/bin/aarch64-apple-darwin/dutymail`；M2 契約凍結面＝`00-tasks/2026-10/10-04-dutymail/delivery/ep.md` S1-S5）。

## 核心原則（invariants——違反任一＝設計錯）

1. **mail plane 不吸收 session registry**（parent EP "No replacement session registry in dutymail"）——本 EP 不做 session 發現（那是 AIR-254.1 seam）。
2. **label 是 display metadata 不是地址**——地址＝exact alias（byte-for-byte）；本 EP 不處理 label。
3. **同一 address 任一時刻僅一個 consuming authority**（epoch-fenced holder）——處理器經 `holder bind` 的 consent CAS 取得權威；絕不繞過 CAS 強取。
4. **prepare 不消耗；ack 是唯一 cursor 前進邊**；ack 只在**全批次處置完成後**下達（auto 處理或呈報值星都算處置）——**絕不 flush-ack**（處置前 ack＝紅線）。
5. **transport ack／human seen-done／AI 提醒三線獨立**——處理器的 ack 只推 delivery cursor，永不代 SC 的 seen/done，也不觸發 AIR-233 面的提醒語義。
6. **自動處理 default-deny**——class×action 表（config 非 code）＋四條全成立才 auto：registered class、intent∈{inform, receipt}、schema 可判定＋可機械驗證、無 outward；**絕不宣稱 work accepted**（terminal status 只是 fact）。恆人工：handoffs、跨 repo 協調、人類寄信、不明意圖/類別。
7. **絕不主動送信**——v1 處理器不呼叫 `send`／`replies`（回信＝outward，須逐次 AUTH，非本 EP 範圍）。
8. **閒置完全安靜**——處理器只掛在 SessionStart／UserPromptSubmit 邊界（值星在場）；無 session＝零查詢零輸出。

## 地址模型（裁定落地）

- **per-repo mailbox**：alias＝`ai-guide-marshal`（與 AIR-233 註冊既有門牌一致；exact alias，3-32 bytes）。
- **epoch-fenced holder**：值星 session＝現在誰值班。bind 走 consent CAS（`--expected-epoch`＝`holder status` 觀察值）；lease 到期只移除消費權威（不動信件）；renew 是 heartbeat。
- **session-local holder state**：token（bearer capability，bind 只回一次）存 per-session state 檔（`~/.local/state/ai-guide/duty-receive/<session_id>.json`，0600）；session 死＝lease 自然到期，下個值星 rebind 換代（不搬信）。

## CLI 面（3.1.0 凍結語義——實作引用，不重定義）

```
dutymail store init                                   # 一次性（機器本地 ~/.dutymail/）
dutymail address create --alias ai-guide-marshal      # 一次性
dutymail holder status  --address <alias>             # 唯讀——觀察 epoch/lease
dutymail holder bind    --address <alias> --expected-epoch <N> [--lease-ms <MS>]
dutymail holder renew   --address <alias> --token <T> # expiry 前 heartbeat
dutymail receive prepare --address <alias> --token <T> [--max-count <N>] [--max-bytes <B>] [--invalidate]
dutymail receive status  --address <alias>            # 唯讀 projection
dutymail receive ack     --address <alias> --token <T> --batch <BATCH-TOKEN>
```

- envelope＝strict source-envelope-v2（body ≤8192 bytes）；每命令輸出恰一個 JSON 物件（typed failure＝`{"schemaVersion":1,"ok":false,"error":{code,class,message,retryable}}`，exit class 2/3/4/5/6）。
- batch token 只在 prepare 回一次；ack 提交**整個** issued contiguous prefix（不支援部分 ack）——因此「絕不 flush-ack」落地為：**處置未完成就不到達 ack 呼叫**；未完成批次用 `--invalidate` 顯式作廢（信不動，下輪重 prepare）。
- one live prepared batch per address：前一邊界遺留未 ack 批次 → 先處置完畢 ack；無法處置（例：本 session 上下文已不記得）→ invalidate 重來（寧重不漏）。

## 分診與輸出（inbox-uc UC-a 裁定版）

- **digest 優先**：每批次一行總結——「新到 N、M 件例行已處理、K 件等你」＋每 class 計數＋最舊 pending 年齡（`receive status`）。
- **triage 項才給全文**：非 auto 項全文呈報，每邊界上限 3 筆全文（防 context 洪水）；超出者一行 header 摘要（from/class/intent/envelope_id）——全部都算「已呈報」（處置完成），細節可事後以 `events` 查。
- 輸出通道＝ZCode `hookSpecificOutput.additionalContext`（sync；與 AIR-233 hook 同形）。
- **body machine-headers**：`class`（handoff/patrol/work-order/receipt/terminal-completion/usage-liveness…）、`intent`（inform/solicit/receipt）、`task`/`card`、`reply_address`（地址模型裁定 2：從 repo mailbox 發出者 reply_address 一律 originating repo-marshal）。

## 段落

### S1 — processor 核心（純邏輯＋CLI adapter，可測）

- `scripts/duty_receive.py`：模組＋CLI。核心函式吃 injectable runner（AIR-233 hook 同款測試形態）：
  - `ensure_holder(state, runner)`：無 token → status→bind；有 token → renew；renew/batch 失敗（fenced/lease-expired/invalid-token）→ status→rebind（CAS 失敗＝surface 衝突、不重試轟炸）。
  - `process_batch(runner)`：prepare → 逐封 `triage(envelope, policy)` → 全部處置 → ack；任何未處置＝不 ack（回 invalidate 或留批次）。
  - `triage(envelope, policy)`：default-deny 判定——`policy.allows(class, intent)`＋機械驗證（body JSON 可解析＋必要 machine-headers 在場＋（receipt 類）idempotency 鍵存在）；不合格一律 `surface`。
  - policy 載入 `governance/dutymail-processor.toml`（class×action 表；未知鍵 fail-loud）。
- AC：
  1. `uv run pytest tests/test_duty_receive.py -v` 全綠；覆蓋：bind/renew/rebind 分流、default-deny triage（未知 class、solicit intent、壞 body 全 surface）、ack 只在全處置後（flush-ack 防護＝測試「處置中斷不觸發 ack」）、invalidate 路徑。
  2. `uv run python scripts/duty_receive.py --help` exit 0。
  3. rg 驗證：`rg -n "send|replies" scripts/duty_receive.py` 命中僅限 docstring/註解宣稱「v1 不送信」——無實際 `dutymail send`／`dutymail replies` 呼叫。

### S2 — hook 接線＋註冊＋config

- `hooks/duty_receive.py`：stdin JSON（SessionStart/UserPromptSubmit）→ eligibility gate（cwd 在 repo 內，同 AIR-233 模式）→ session_id 取自 payload → 呼 scripts 核心邏輯（import 或 subprocess——實作取 import，hooks/ 與 scripts/ 同 repo；Windows 無關）→ additionalContext 輸出。fail-soft：store 缺席／face 失敗＝stderr 註記＋零 stdout exit 0（pre-migration 世界不擋 turn）。
- `governance/dutymail-processor.toml`：初始表（default-deny；首版 auto 入列僅 `usage-liveness`＋`terminal-completion`（inform、digest 吸收、宣稱語義禁 work accepted）；`receipt` intent=receipt 可 auto；`handoff`/`patrol`/`work-order` 恆 surface；未列 class 恆 surface）。欄位註解在檔頭。
- `governance/registrations/zcode.json`：SessionStart＋UserPromptSubmit 各加一條（args 帶 `--address ai-guide-marshal`）；cc.json（dormant）同形追加保持對稱。
- 部署：跑 governance installer 安裝面（hooks/AGENTS.md 部署紀律）；`~/.zcode/cli/config.json` merge 驗證（不可整檔覆蓋）。
- AC：
  4. `rg -n "duty_receive" governance/registrations/zcode.json` ≥2 命中；安裝後 `python3 -c`（json load ~/.zcode/cli/config.json）出現 `duty_receive.py` 且原有條目數不減。
  5. `uv run pytest tests/test_duty_receive.py`（hook 面：stdin payload 驅動 run()——degraded（store 缺席）＝零 stdout exit 0；eligibility gate 不過＝零查詢零輸出）。
  6. `uv run python hooks/duty_receive.py --help` exit 0（args 誤用 exit 2 同 AIR-233 慣例）。

### S3 — 信箱開通＋真實資料往返＋round-trip 文件

- 開通（機器本地、可逆）：`dutymail store init`＋`address create --alias ai-guide-marshal`；建立第二測試門牌 `dutymail-test-sender`（同名 store；alias 是信箱身分非 session）。
- 真實往返驗證（L2 實證層）：
  1. 測試 sender `send` 三封真實 envelope（class=usage-liveness intent=inform、class=handoff intent=inform、class=unknown 壞 body 各一）到 ai-guide-marshal；
  2. 跑 `hooks/duty_receive.py`（stdin 餵 SessionStart payload，cwd=repo）——預期：digest 行「新到 3、1 件例行已處理、2 件等你」（壞 body 者落 surface）＋`receive status` cursor 前進 3；
  3. 再跑一次（無新信）——預期零 stdout（無新到不囉嗦）；
  4. crash 重送語義：prepare 後不 ack 直接再跑（模擬中斷）——信不跳不丟（prepare 不消耗；重跑重 prepare）。
- `skills/_common/dutymail-roundtrip.md`：一頁 round-trip——send（intent＋reply_address＋envelope_id）→ durable inbox → processor receive → transport ack → semantic accept（真正承接）→ work → completed（result/evidence）→ user done；三線獨立（transport ack／human seen-done／AI 提醒）；地址模型與 reply_address 慣例；auto default-deny 表引用。
- AC：
  7. S3 往返腳本實跑輸出留 `.agent-tmp/dw-dutymail/s3-receipt.md`（命令＋原始輸出）；`receive status` 逐段驗證。
  8. `test -f skills/_common/dutymail-roundtrip.md && rg -c "transport ack|semantic accept|reply_address" skills/_common/dutymail-roundtrip.md` ≥3。
  9. 清場：測試信件不影響真實使用（store 留 local 機器，不進版控；測試 sender alias 保留供 G4 驗證重用）。

## 風險與邊界

- **SC receiver authority（cutover report 風險 #1）**：本 EP 只在 **dutymail store** 內成為 ai-guide-marshal 的 consuming authority；SC 現行消費面在 scbus store（M5/M6 前不切）——兩 store 並存無競爭。S3 writer activation 的共同 gate（M3 reconciliation 後）不在本 EP。
- **token 外洩面**：bearer capability 存 user-state 0600；hook 只在 repo 內 eligible session 執行。
- **context 洪水**：digest-first＋全文上限 3；`max-count` 預設 8（bounded batch）。
- **不做**：session 發現（254.1）、label（254.2）、monitor（254.4）、SC 投影（80.5）、scbus send 遷移（G5）、M7 migration runbook。
