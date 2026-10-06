# EP — mail-watch skill：dutymail 信件 watcher（AIR-265）

> baseline：`e7dfaec6`（main，2026-10-06 開工時點）
> 裁決源：三顧問設計討論（muse `job-muwr72bx-jnyk7p`＋codex `job-muwr72ez-sibfsk`＋GLM-5.3 裁決，2026-10-06）——
> brief＝primary repo `.agent-tmp/mail-watch-design-brief.md`；verdict 全文＝兩 job finalText（卡 notes 有摘要）。
> 契約參考：`skills/_common/dutymail-roundtrip.md`、`skills/voice-notification/SKILL.md`、
> `hooks/duty_mailbox_monitor.py`（決策表對齊對象）、`scripts/duty_receive.py`（binary 解析／state 慣例同源）。

## 核心原則（invariants——違反任一＝設計錯）

1. **唯讀單 face**：watcher 只消費 `dutymail receive status --address <alias>`——永不呼叫 `bind`/`prepare`/`ack`/`send`/`holder`（Q3 裁決採 codex：duty_receive 只在 prompt 邊界觸發，idle holder 正是本 watcher 要補的 gap；活躍 session 處理窗口 <30s 者 rising edge 自然不觸發——自然去抖，無需 holder face）。
2. **人類音訊面不搶職責**：notify 是 say 音訊（advisory 非保證），不是處理動作；不代理 transport ack、不代理 SC human seen/done、不代理 monitor hook 的 session advisory。
3. **machine-level baseline**：watcher baseline 跨 session 機器級、不歸任一 session；與 roundtrip 三線表的 session-local advisory baseline 並存互不代理（S3 契約註記）。
4. **寧重不漏**：state 損壞視同冷啟（最多一次重複 advisory）；say 失敗 fail-soft（log 續跑）；face typed-failure 跳過該輪（心跳標記失敗）不崩潰。
5. **singleton by flock**：跨進程互斥靠 `fcntl.flock` 狀態鎖（crash 自動釋放＝stale 偵測免費）；stop 驗鎖不盲殺——鎖可取＝無 daemon（清殘留即可）、鎖被持才殺 PID 檔指名的進程。
6. **say 慣例**：`say -v Meijia -r 180`、中性句（對齊 voice skill 開始通知先例——無稱謂、避免稱謂清單第三份同步副本）、文案 ≤20 字。
7. **不做 launchd**（YAGNI）：user 要 skill 級 start/stop 控制；常駐 daemon 是不同承諾。

## 設計裁決摘要（三顧問收斂）

| 題 | 裁決 | 源 |
|---|---|---|
| 資料源 | `receive status` pendingCount 30s 輪詢 | muse+codex agree（events/wait 誤報退役理由同 monitor hook） |
| 觸發 | rising edge＋冷啟一次（state 缺席/損壞時）＋同值靜默；**baseline 落下同步更新**（holder ack 後歸零，下次上升可再通知） | muse+codex agree |
| holder 互動 | **不依賴 holder face**（呼叫面無 holder status） | codex disagree 成立、5.3 裁決採納 |
| 載體 | python daemon（JSON 契約解析＋atomic 0600 寫＋typed-failure 分類） | muse agree＋codex alternative（flock＋identity） |
| state | `${XDG_STATE_HOME:-~/.local/state}/ai-guide/duty-watch/`（watch.lock＋state.json）；**stop 不刪 state.json**——restart 後 edge 邏輯自然接手（stop→新信→start＝pending>baseline＝rising edge 通知） | muse+codex agree |
| 通知 | say 中性句（見 invariant 6） | 5.3 調和（muse/codex 同方向） |

## CLI 面（凍結語義——實作引用，不重定義）

```
dutymail receive status --address <alias>
# 成功：{"schemaVersion":1,"ok":true,"result":{...,"pendingCount":N,...}}
# typed failure：{"ok":false,"error":{code,class,message,retryable}} exit 2-6
```

- binary 解析**同源 import** `scripts/duty_receive.py` 的 `_resolve_binary`（`DUTYMAIL_BIN` env → PATH → plugin cache 版本最新；禁手 pin 版化路徑、禁複製邏輯）。
- dutymail 契約凍結＝CLI 3.1.0/3.2.1（roundtrip 文檔；本 EP 不重刻 envelope 細節）。

## 段落

### S1 — daemon 核心（`scripts/duty_mail_watch.py`：模組＋subcommand CLI）

- **subcommands**：`start`／`stop`／`status`；flags `--address`（預設 `ai-guide-marshal`，可重複）／`--interval`（預設 30s，下限 5s）。
- **start**：`Popen(_daemon, start_new_session=True)` detach；daemon 先取 flock（非阻塞）——失敗＝single-instance 拒絕（exit 碼帶回「already running PID X」）；成功＝寫 state.json（pid＋started_at）後進 loop。starter 等 ready 信號（state.json pid 就位，bounded ~3s）再回報。
- **stop**：驗鎖不盲殺——先試非阻塞 flock：可取＝無 daemon（清 stale state.json 回報 clean-stale）；被持＝讀 state.json pid → `SIGTERM` → bounded grace（5s）內退出＝成功；未退＝回報失敗（不升級 SIGKILL，留 human）。
- **status**（唯讀、可隨時跑）：lock 持有態＋PID 活性（`kill(pid,0)`）＋`last_poll_at` 新鮮度（> interval×3 標 stale-heartbeat 警告）＋per-address baseline＋現值 pendingCount（一發 live probe）。
- **daemon loop**：每 interval＝`receive status`（逐 address）→ edge 判定 → 心跳寫入（atomic 0600：`last_poll_at`/`last_seen`/失敗輪標記）→ sleep。SIGTERM handler＝乾淨退出（fd 關＝鎖自動釋放；state.json 保留）。
- **edge 判定**（per address）：`count > baseline` → say＋baseline=count；`count <= baseline` → 靜默＋baseline=count（落下更新）。state 缺席/損壞（冷啟）＝baseline 0 起算＋pending>0 通知一次。
- **fail-soft 面**：face typed-failure（storage/transient）＝跳過該輪＋心跳標記；usage/config 類＝exit 2 fail-loud（壞配置不硬跑）；say 失敗＝log 續跑（寧重不漏：baseline 已更新、下輪不重試本輪——殘缺通知由冷啟/stale 週期補）。
  > amendment 2026-10-06 tri-panel J-2：say 失敗改 baseline 不前進下輪重試（原：不回滾不重試）——恢復後一次通知最新值。
- **macOS sleep/resume**：loop 凍結、resume 後下一輪補上（rising edge 照觸發）；睡眠中觸發的 say 若被系統丟棄＝已知一次性邊角（advisory 非保證；記 skill）。

### S2 — skill（`skills/mail-watch/SKILL.md`）

- frontmatter＋用法（start/stop/status 命令列）＋定位聲明：**machine-level 第四通知通道、advisory 非保證**（daemon 靜默死亡可能——status 證活證新鮮）＋唯讀不變式＋與三既有機制分工表（holder 處理面／monitor session advisory／SC 人類 viewport——watcher＝時間軸人類音訊面）＋sleep/resume 行為＋生命週期（跨 session 存活、機器級 state）。
- 寫作依 instruction-writing 慣例（AI 消費導向、可機械遵行）；禁人類認知論證。

### S3 — 契約同步兩處（single-source drift 防護——改定義源必同步引用面）

- `skills/voice-notification/SKILL.md` 通道表加第四行：「**信件待判讀** | holderless pending 上升（時間軸 30s 輪詢） | duty_mail_watch daemon | 機械（rising edge）」＋一行註記：daemon 面中性句（不入稱謂清單同步面、非 LLM say 面）。
- `skills/_common/dutymail-roundtrip.md` 三線獨立表「AI 提醒 baseline」行補註記：machine-level watcher baseline（AIR-265）與 session-local baseline 並存、互不代理。

### S4 — tests（`tests/test_duty_mail_watch.py`，fixture 驅動＋injectable runner）

fake dutymail runner（同 duty_receive 測試形態）＋tmp state dir 注入；say 以 stub 捕獲（斷言 voice/rate/文案）。

**TC 清單**：

| TC | 案例 | 期望 |
|---|---|---|
| W1 冷啟通知 | state 缺席、pending=3 | say 一次（文案含 3）、baseline=3 |
| W2 rising/falling | 0→2→2→4→0→1 | say@2、靜默@2、say@4、靜默@0（baseline 落至 0）、say@1 |
| W3 restart 接手 | baseline=2 stop→新信至 4→start | say 一次（4>2）；無冷啟重複通知 |
| W4 face fail-soft | typed failure（storage） | 跳輪＋心跳標記、不崩、baseline 不動 |
| W5 singleton | daemon 活著二次 start | 拒絕＋訊息含現 PID、exit≠0 |
| W6 stale 自動釋放 | kill -9 daemon 後再 start | 鎖已釋、start 成功（crash 清理免費） |
| W7 stop 乾淨 | SIGTERM | exit 0、鎖釋放、state.json 保留 |
| W8 say 慣例 | 任一通知 | `say -v Meijia -r 180`、中性句、≤20 字、無稱謂 |
| W9 唯讀結構證 | monkeypatch runner allowlist | daemon 全生命週期只出現 `receive status` 呼叫 |

## 驗收映射（卡 AC→本 EP 證據）

- AC1（唯讀不變式）＝TC-W9＋`rg -n "holder|prepare|\.ack|send" scripts/duty_mail_watch.py` 無呼叫面命中（註解/docstring 除外）
- AC2（觸發語義）＝TC-W1/W2/W3 綠
- AC3（監督契約）＝TC-W5/W6/W7 綠＋status 輸出帶 PID 活性＋last_poll_at
- AC4（契約同步）＝`rg "duty_mail_watch" skills/voice-notification/SKILL.md`＋`rg "machine-level" skills/_common/dutymail-roundtrip.md` 命中
- AC5（手動 smoke）＝start→status（證活＋新鮮）→stop（乾淨）實跑收執；sleep/resume 行為記 skill 文件

## 完成閘

`uv run pytest tests/test_duty_mail_watch.py -v` 全綠＋全套 `uv run pytest`（背景）無新失敗＋AC5 smoke 收執＋ruff clean。
