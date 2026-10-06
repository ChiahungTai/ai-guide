# EP — mail-waiter：session 級信件喚醒 watcher（AIR-266）

> baseline：`ff85c589`（main，2026-10-07 開工時點）
> 裁決源：tri 三方（muse＋codex 討論腿＋GLM-5.3 裁決，2026-10-07；brief＝primary repo
> `.agent-tmp/mail-waiter-brief.md`、verdict 全文＝卡 notes 所指 job finalText）＋研究腿
> （waiter 家族喚醒鏈實證——背景 shell exit＝ZCode 唯一 push 原語；bridge_waiter T1-T9
> ／harness_waiter 同骨架；dutymail wait class-6＝124 等價語義）。

## 核心原則（invariants——違反任一＝設計錯）

1. **waiter 純觀察軸（tri Q4 雙 agree，零例外）**：只消費 `dutymail wait`＋`events` face——永不呼叫 `bind`/`prepare`/`ack`/`send`（無 body 無法分診、無 holder 權威、回信/ack 屬 outward 逐次 AUTH——三重否決）；處理面恆＝`duty_receive process`（唯一 consuming authority 鏈）。
2. **events cursor ≠ delivery cursor**（觀察軸 vs transport 軸，凍結三軸不互代理）：waiter 推進自己的 events cursor，永不觸 receive ack 的 delivery cursor。
3. **exit 即通知、timeout 恆內部消化**（waiter 家族契約）：waiter exit 0＝新事件喚醒（尾行單行 JSON）；wait-timeout（class-6）內部 re-arm 不外洩（同 bridge 124 語義）；storage/fencing（class 4/5）跳輪＋心跳標記；usage/admission（class 2/3）fail-loud exit 2。處置權恆歸 caller（woken LLM）。
4. **喚醒回合 invariant（tri Q3 採 codex 加強版）**：woken LLM 的回合＝①跑 `duty_receive process` ②成功 re-arm——兩者完成才算喚醒回合結束（skill 明文合約）。
5. **開關語義**：`start`＝arm 背景 shell；`stop`＝落 flag（`desired=stopped` 寫 state）——flag 權威：re-arm 遇 flag 即退、尾行回報 `stopped`。
6. **generation CAS（tri 最大風險 codex 項）**：每次 arm `generation+=1`；worker 每輪檢查 state.generation 仍＝自己的值——不匹配＝已被新 arm 取代，靜默退（不寫 state）；state 寫入（cursor 推進/心跳）只在 generation match 下 read-modify-write。效果：雙 arm 後舊 worker 自退、cursor 不回退、stale worker 不覆蓋新 generation。
7. **session 級生命週期（tri 最大風險 muse 項＋codex 漏看面）**：`start` 的承諾＝**本 session 存活期間**（背景 shell 隨 session/app 存亡）——skill 開場明示，禁語義超賣；新 session 以 `status` 見 `desired=running` 但 worker stale 時提示 re-arm。
8. **coalesce＝cursor 推進天然保證**（muse 漏看面解法）：一次 exit 報該輪全部新事件（門牌×事件數）；處理後 re-arm 從新 cursor 起——舊信不再觸發；不需額外合併窗口。

## State schema（tri Q3；XDG state 機器級、0600 atomic）

`${XDG_STATE_HOME:-~/.local/state}/ai-guide/mail-waiter/state.json`：
```json
{"desired": "running|stopped", "generation": <int>, "armed_at": <unix>,
 "addresses": {"<alias>": {"cursor": "<events token|null=冷啟>", "last_event_seq": <int>}},
 "last_exit": {"code": <int>, "reason": "<str>", "at": <unix>}|null,
 "last_round_failed": <bool>}
```
- 冷啟（cursor null）：首輪 events 取 head 對滾（寧重不漏）。
- 損壞視同冷啟（generation 歸零重 arm）。
- 舊 AIR-265 duty-watch 目錄退場時清（S3）。

## CLI 面（凍結語義——實作引用）

```
dutymail wait --address <alias> --cursor <tok> --deadline-ms <ms>   # cap 600000；成功=exit 0＋non-empty page；deadline 盡=class-6
dutymail events --address <alias> [--cursor <tok>] [--limit <n>]   # keyset paging；payload 無 body（只有 sha256+envelopeId）
```
- binary 解析同源 import `scripts/duty_receive.py`（`_resolve_binary`）；waiter 內層 deadline 取短切片（如 60s）逐門牌輪轉（wait 無原生批次）。

## 段落

### S1 — `scripts/mail_waiter.py`（模組＋subcommand CLI）

- subcommands：`start`（寫 desired=running＋generation+=1→印 arm 命令（背景 shell 形，供 skill/LLM 直接複製））/ `stop`（寫 desired=stopped；worker 下輪自退）/ `status`（desired/generation/armed_at/per-address cursor/staleness：armed_at 距今 > 輪詢週期×3＝stale 提示 re-arm）/ 內部 `worker`（背景 shell 主體——start 印的命令即 `worker` 形）。
- worker loop（per address 輪轉）：讀 state（generation/desired/cursor）→ desired=stopped 或 generation 不匹配＝安靜退（尾行 JSON state=superseded|stopped）→ `wait --deadline-ms 60000` → exit 0（新事件）：events 翻頁取 cursor 推進＋彙總（門牌×新事件數）→ 寫 state（generation-guarded）→ **exit 0＋尾行 JSON**：`{"state":"mail","new":[{address,count}...],"rearm":"<arm 命令>"}`；class-6→內部續輪；class 4/5→跳輪＋last_round_failed；class 2/3→exit 2 fail-loud。
- 尾行 JSON 是唯一機判面（單行、stdout 最後一行）——同 bridge_waiter CollectionReceipt 慣例。

### S2 — `skills/mail-watch/SKILL.md` 重寫（skill 名沿用）

- start/stop/status 用法（命令列可直接複製）＋**喚醒回合 invariant**（①process ②re-arm 才算完）＋session 級生命週期明示（開場即寫）＋**waiter 家族憲章節**（tri Q2 裁決：契約單一源文件化——背景 shell exit＝通知/exit 0=喚醒+尾行 JSON/timeout 內部消化/處置歸 caller；bridge_waiter/harness_waiter/mail_waiter 三員同契約；_waiter_core 程式抽取列為下次新 waiter 時的 follow-up）。

### S3 — AIR-265 退場清場

- 刪 `scripts/duty_mail_watch.py`＋`tests/test_duty_mail_watch.py`；`skills/voice-notification/SKILL.md` 四通道回三通道（表行＋標題＋註記回退）；`skills/_common/dutymail-roundtrip.md` machine-level 註記改寫指向 AIR-266 mail-waiter；`skills/AGENTS.md` mail-watch 索引條目改新語義＋voice 條目回三通道；`rg -l duty_mail_watch` 殘留零命中（.agent-tmp/歷史文件除外）；舊 state 目錄 `~/.local/state/ai-guide/duty-watch/` 清（清場收執記卡 notes——機器本地不入 git）。
- EP／卡面歷史不動（git 歷史即證據）。

### S4 — tests（`tests/test_mail_waiter.py`，fake dutymail stub）

fake `wait`/`events` stub binary（記 argv＋可注入行為序列）；state dir tmp 注入。

**TC 清單**：
| TC | 案例 | 期望 |
|---|---|---|
| W1 喚醒契約 | wait exit 0 帶新事件 | 尾行 JSON `state=mail`＋new 清單＋rearm 命令；cursor 推進 |
| W2 timeout 消化 | 連續 class-6 ×N 再新事件 | 不 exit、續輪至事件才 exit 0 |
| W3 stop flag | desired=stopped 下 worker 輪 | 安靜退、尾行 state=stopped |
| W4 fail-loud | class-2 usage | exit 2＋尾行 state=fail-loud |
| W5 跳輪 | class-4 storage 一輪後恢復 | 跳輪＋last_round_failed→恢復輪繼續 |
| W6 generation CAS | worker A 活著再 start（gen+1） | A 下輪見 gen 不匹配安靜退（superseded）；新 worker cursor 不受 A 覆蓋 |
| W7 冷啟 | state 缺席 | events head 對滾＋首輪彙總 exit（寧重不漏） |
| W8 唯讀結構證 | allowlist stub | 全生命週期 argv 只 wait/events face（零 bind/prepare/ack/send） |
| W9 stop 權威 | desired=stopped 落下後 re-arm | 新 worker 首輪即退 stopped（flag 權威） |

## 驗收映射

- AC1＝TC-W1/W8＋`rg "bind|prepare|\.ack\b|send" scripts/mail_waiter.py` 零呼叫面命中
- AC2＝TC-W3/W9＋status 輸出五欄在場
- AC3＝TC-W6（雙 arm 舊退新續、cursor 無回退）
- AC4＝TC-W2/W4/W5
- AC5＝S3 清場清單逐項＋rg 零命中收執
- AC6＝主 session 手動 smoke（真 store 唯讀輪＋fake 事件注入）

## 完成閘

`uv run pytest tests/test_mail_waiter.py -v` 全綠＋全套 `uv run pytest` 無新失敗＋ruff clean＋AC5 rg 收執＋AC6 smoke 收執落卡。
