---
name: mail-watch
description: "session 級 dutymail 信件喚醒 waiter — 背景 shell 掛哨 dutymail wait，新事件到＝worker exit 0 喚醒本 session（尾行 JSON 帶門牌×事件數＋re-arm 命令）；喚醒回合＝①duty_receive process ②re-arm 兩步完成才算完。涵蓋 start/stop/status 控制、waiter 純觀察軸紅線（零收信處理面呼叫）、generation CAS 雙 arm 防護、session 級生命週期（隨 session 存亡）與 waiter 家族憲章。觸發詞：信件喚醒、信箱掛哨、mail-watch、mail_waiter、dutymail watcher、waiter re-arm、背景 shell 喚醒。"
allowed-tools: [Bash]
---

# mail-watch：session 級信件喚醒 waiter

> **載入時機**：要掛哨／停哨／查哨信件喚醒（start/stop/status）、背景 shell 喚醒你且尾行 JSON 是 mail_waiter 收據、或需釐清 waiter 與收信處理鏈職責邊界時載入。

## 定位聲明（先讀——session 級生命週期）

- **`start` 的承諾僅及本 session 存活期間**：worker 是背景 shell，隨 session／app 存亡——session 結束＝worker 消失，**不是**跨 session 常駐 daemon（AIR-265 daemon 已退場）。新 session 接手時先 `status` 看 `desired` 與 staleness——見 `desired=running` 但 worker stale（armed_at 距今 > 輪詢週期×3）＝提示重新 arm。
- **waiter 純觀察軸（紅線，零例外）**：worker 的 dutymail 呼叫面只有 `wait`＋`events`——絕不觸達 holder 綁定／批次預取／回執／送信面；**處理面恆＝`duty_receive process`**（唯一 consuming authority 鏈）。waiter 推進的是自己的 events 觀察游標，絕不代推收信面的 delivery 游標。
- **waiter 只喚醒不處理**：處置權恆歸 caller（被喚醒的 LLM）——worker exit 是通知，不是處理動作。

## 用法（命令可直接複製）

```bash
# arm：generation+=1＋印 worker 背景命令（複製到背景 shell 執行）
uv run python scripts/mail_waiter.py start

# 多門牌（--address 可重複；預設 ai-guide-marshal）
uv run python scripts/mail_waiter.py start --address ai-guide-marshal

# 唯讀五欄報告：desired/generation/armed_at（＋staleness）/per-address cursor/last_exit
uv run python scripts/mail_waiter.py status

# 停止＝落 flag（desired=stopped）——worker 下輪自退、尾行回報 stopped
uv run python scripts/mail_waiter.py stop
```

`start` 印出的 `worker` 命令（`uv run python scripts/mail_waiter.py worker --address … --generation N --state-dir …`）放到背景 shell 執行即完成 arm；喚醒收據的 `rearm` 欄位同形可直接複製。

## 喚醒回合 invariant（skill 明文合約）

worker exit 0（尾行 JSON `state=mail`）喚醒你後，**你的回合＝兩步，兩者完成才算結束**：

1. **處理**：跑 `duty_receive process`（唯一處理面——收信、分診、呈報；waiter 絕不代勞）。
2. **re-arm**：把尾行 JSON 的 `rearm` 命令（或 `start` 新印的命令）放上背景 shell。

漏掉 ②＝本 session 之後無人再喚醒你。尾行 `state=stopped`＝stop flag 權威（不 re-arm）；`state=superseded`＝新 arm 已接管（不需動作，除非 `status` 顯示無活 worker）；`state=fail-loud`＝配置面壞了（查 stderr 修因，不硬重試）。

## waiter 家族憲章（契約單一源——tri Q2 裁決）

三員同契約：`scripts/bridge_waiter.py`（delegate-bridge fan-in）、harness_waiter、`scripts/mail_waiter.py`（本卡）。

- **背景 shell exit＝唯一 push 原語**：harness 無原生回呼——watcher 以退出喚醒 session。
- **exit 0＝喚醒**：stdout 尾行單行 JSON＝唯一機判面（mail_waiter：`{"state":"mail","new":[{address,count}...],"rearm":"..."}`）；其餘進度行走 stdout、診斷走 stderr。
- **timeout 恆內部消化**：等待超時（dutymail class-6／bridge 124 等價語義）內部 re-arm 續輪，絕不外洩成喚醒。
- **處置權恆歸 caller**：watcher 只喚醒；stalled／錯誤面交人（或 woken LLM）判斷，watcher 不 stop 不重派不代處理。
- typed-failure 分流：storage/fencing＝跳輪＋心跳標記；usage/admission＝fail-loud exit 2（壞配置不硬跑）。
- coalesce：一次 exit 報該輪全部新事件（門牌×事件數；多門牌喚醒時其餘門牌以 events 非阻塞快照併入）——re-arm 從新 cursor 起，舊信不再觸發，不需合併窗口。
- `_waiter_core` 共用程式抽取：列為下次新 waiter 時的 follow-up（現三員各自內含，YAGNI）。

## generation CAS（雙 arm 防護）

每次 `start` 推進 `generation`；worker 每輪開頭驗 state.generation 仍＝自己的代、每次 state 寫入前重讀比對（read-modify-write guard）。效果：雙 arm 後舊 worker 自退（尾行 `superseded`、不寫 state）；events cursor 不回退；stale worker 不覆蓋新 generation 的 state。**同一輪喚醒只需貼一次 rearm 命令**——重複 arm 無害（舊代自退）但浪費背景 shell。

## state 與觀察軸游標

- state＝`${XDG_STATE_HOME:-~/.local/state}/ai-guide/mail-waiter/state.json`（0600 atomic 寫）：`desired`／`generation`／`armed_at`（worker 每輪刷新＝活性證據）／per-address `cursor`（events 觀察游標，null=冷啟）＋`last_event_seq`／`last_exit`／`last_round_failed`。
- 冷啟（cursor null／state 缺席或損壞）：首輪 events 由頭對滾到 head＋彙總喚醒（寧重不漏——歷史事件可能重複觸發一次喚醒，處理面冪等吸收）。
- **觀察軸 vs transport 軸不互代理**：waiter 的 events cursor 只標記「已看到的時間線位置」；收信面的 delivery cursor 由 `duty_receive process` 在處置後推進——兩線獨立，waiter 推進自己的不等於信已處理。

## 職責分工（誰管什麼——不互代理）

| 機制 | 面 | 時間軸 | 職責 |
|---|---|---|---|
| **mail_waiter（本 skill）** | 觀察軸掛哨 | 背景 shell（session 級） | 新事件喚醒本 session（wait＋events 唯讀面） |
| duty_receive 處理器 | 收信處理 | prompt 邊界／喚醒回合① | 唯一 transport cursor 前進邊（全批處置後才推進） |
| monitor hook（duty-monitor） | session advisory | prompt 邊界 | session-local baseline 提醒（值變化才一行） |
| SC INBOX | 人類 viewport | 永續 | human seen/done 權威、信件全文判讀面 |
