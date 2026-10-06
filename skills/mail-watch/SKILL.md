---
name: mail-watch
description: "machine-level dutymail 信件 watcher daemon — 跨 session 常駐輪詢 pendingCount，rising edge 時 say 音訊提醒（advisory 非保證）。涵蓋 start/stop/status 控制、唯讀單 face 不變式、與 duty_receive 處理器／monitor hook／SC INBOX 的分工、sleep/resume 行為與機器級 state 生命週期。觸發詞：信件待判讀、信箱監看、mail-watch、dutymail watcher、新信提醒、duty-watch。"
allowed-tools: [Bash]
---

# mail-watch：dutymail 信件 watcher daemon

> **載入時機**：要啟動／停止／證活 mail watcher、收到「信箱有 N 封新信待判讀」語音想查來源、或需釐清 watcher 與收信處理鏈職責邊界時載入。

## 定位聲明（先讀）

- **machine-level 第四通知通道**：daemon 跨 session 存活、baseline 機器級（不歸任一 session）——與三既有機制並存互不代理（見分工表）。
- **advisory 非保證**：say 音訊是召回提示，不是處理動作——不代理 transport cursor、不代理 SC human seen/done、不代理 monitor hook 的 session advisory。daemon 可能靜默死亡（crash／機器重啟後無人再 start）；**證活靠 `status`**（lock 持有態＋PID 活性＋last_poll_at 新鮮度）。
- **唯讀不變式**：watcher 的 dutymail 呼叫面只有 `receive status --address <alias>`——絕不觸達 bind/prepare/ack 等收信處理面（處理面單一源＝duty_receive 處理器；`scripts/duty_mail_watch.py` 結構上只 import 唯讀 face）。

## 用法

```bash
# 啟動（detach daemon；預設 ai-guide-marshal、30s 輪詢；singleton by flock）
uv run python scripts/duty_mail_watch.py start

# 多門牌＋自訂間隔（--address 可重複；--interval 下限 5s）
uv run python scripts/duty_mail_watch.py start --address ai-guide-marshal --interval 30

# 證活＋新鮮＋baseline＋現值（唯讀、可隨時跑）
uv run python scripts/duty_mail_watch.py status

# 停止（驗鎖不盲殺；state.json 保留——restart 後 edge 邏輯接手）
uv run python scripts/duty_mail_watch.py stop
```

觸發語義（per address，每輪）：

- `pendingCount > baseline` → say 一次＋baseline 落到現值（rising edge）。
- `pendingCount <= baseline` → 靜默＋baseline 落到現值（落下同步更新——收信處理清空信箱後歸零，下次上升會再通知）。
- 冷啟（state 缺席／損壞）＝baseline 0 起算＋pending>0 通知一次（寧重不漏——最多一次重複 advisory）。
- say 文案：中性句 ≤20 字（「ai-guide 信箱有 N 封新信待判讀」）、`say -v Meijia -r 180`、無稱謂——不入 voice skill 稱謂清單同步面、非 LLM say 面。

## 四機制分工（誰管什麼——不互代理）

| 機制 | 面 | 時間軸 | 職責 |
|---|---|---|---|
| duty_receive 處理器 | 收信處理 | prompt 邊界 | 唯一 transport cursor 前進邊（全批處置後才推進） |
| monitor hook（duty-monitor） | session advisory | prompt 邊界 | session-local baseline 提醒（值變化才一行） |
| SC INBOX | 人類 viewport | 永續 | human seen/done 權威、信件全文判讀面 |
| **mail-watch daemon（本 skill）** | 時間軸人類音訊 | 30s 輪詢 | machine-level rising edge say 提醒（advisory） |

## sleep/resume 行為

macOS 睡眠時 daemon loop 凍結（不補跑睡眠期間輪詢）；喚醒後下一輪照常——喚醒時 pendingCount 已上升者 rising edge 照觸發。睡眠中觸發的 say 若被系統丟棄＝已知一次性邊角（advisory 非保證；殘缺通知由冷啟／stale 週期補）。

## 生命週期與 state

- daemon 跨 session 存活（start 後持續到 stop／機器重啟）；singleton 由 flock 保證——`${XDG_STATE_HOME:-~/.local/state}/ai-guide/duty-watch/watch.lock`，crash（含 kill -9）自動釋放，直接再 start 即可。
- state＝同目錄 `state.json`（pid＋started_at＋last_poll_at＋per-address baseline；0600 atomic 寫）；`daemon.log`＝daemon stdout/stderr。**stop 不刪 state.json**——restart 後 baseline 接手：stop→新信→start＝pending>baseline＝rising edge 通知。
- fail 分級：dutymail storage/transient 失敗＝跳輪＋心跳標記（下輪重試）；usage/admission（壞配置）＝daemon exit 2 fail-loud 不硬跑——查 `daemon.log` 修配置後再 start。
