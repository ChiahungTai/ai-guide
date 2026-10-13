---
name: mail-watch
description: "session 級 dutymail 信件喚醒 waiter — 背景 shell 掛哨 dutymail wait，新事件到＝worker exit 0 喚醒本 session（尾行 JSON 帶門牌×事件數＋re-arm 命令）；喚醒回合＝re-arm＋重進 mail-handle once 看信。涵蓋 start/stop/status 控制、waiter 純觀察軸紅線（零收信處理面呼叫）、generation CAS 雙 arm 防護、session 級生命週期（隨 session 存亡）、升級窗口（舊全域 watcher 停止程序）與 waiter 家族憲章（通知能力選擇唯一源＝waiter-charter）。觸發詞：信件喚醒、信箱掛哨、mail-watch、mail_waiter、dutymail watcher、waiter re-arm、背景 shell 喚醒。"
allowed-tools: [Bash]
---

# mail-watch：session 級信件喚醒 watcher

> **載入時機**：要掛哨／停哨／查哨信件喚醒（start/stop/status）、背景 shell 喚醒你且尾行 JSON 是 mail_waiter 收據、或需釐清 waiter 與收信處理鏈職責邊界時載入。
> **信件處理主流程**（once／看信模型／PENDING 面）＝[mail-handle](../mail-handle/SKILL.md)——本檔是 watcher 掛哨機制細節。

## 定位聲明（先讀——session 級生命週期＋per-repo）

- **`start` 的承諾僅及本 session 存活期間**：worker 是背景 shell，隨 session／app 存亡——session 結束＝worker 消失，**不是**跨 session 常駐 daemon（AIR-265 daemon 已退場）。新 session 接手時先 `status` 看 `desired` 與 staleness——見 `desired=running` 但 worker stale（armed_at 距今 > 輪詢週期×3）＝提示重新 arm。
- **watcher 只 watch 本 repo 信箱（AIR-312）**：門牌 alias＝呼叫端 repo 身份（git common-dir primary root basename——start 自動推導，免 --address；非 git cwd＝fail-loud exit 2；submodule／分離 git-dir／bare＝無法判定同拒——支援面與無 override 限制＝[mail-handle](../mail-handle/SKILL.md)「身份佈局限制」）；state per-repo（`<XDG>/ai-guide/mail-waiter/<repo 編碼>/state.json`——identity injective percent-encode，不折疊）——A stop 不影響 B；每 repo 一 watcher，零 daemon／協調層。
- **waiter 純觀察軸（紅線，零例外）**：worker 的 dutymail 呼叫面只有 `wait`＋`events`——絕不觸達 holder 綁定／批次預取／回執／送信面；喚醒回合不跑 `duty_receive process`（五態處置＋ACK digest 不是普通看信——禁）。看信走 [mail-handle](../mail-handle/SKILL.md) once（`inbox`／`mark-read`）。waiter 推進的是自己的 events 觀察游標，絕不代推收信面的 delivery 游標。
- **waiter 只喚醒不處理**：處置權恆歸 caller（被喚醒的 LLM）——worker exit 是通知，不是處理動作。

## 用法（命令可直接複製）

```bash
# ai-guide 源碼路徑從本 skill 真實位置反推（本檔經 symlink 部署——
# readlink -f 取真實路徑、三層 dirname 上溯（檔案→mail-watch 目錄→
# skills→repo root）＝repo root）；腳本一律
# 絕對路徑呼叫，絕不 cd 進 ai-guide（身份閘以呼叫當下 cwd 反推 repo
# 身份——cd 進去＝身份誤導成 ai-guide）。
AI_GUIDE="$(dirname "$(dirname "$(dirname "$(readlink -f <本 SKILL.md 檔路徑>)")")")"

# arm：generation+=1＋印 worker 背景命令（門牌＝本 repo 身份；免 --address）
uv run python "$AI_GUIDE/scripts/mail_waiter.py" start

# 唯讀五欄報告：desired/generation/armed_at（＋staleness）/per-address cursor/last_exit
uv run python "$AI_GUIDE/scripts/mail_waiter.py" status

# 停止＝落 flag（desired=stopped）——worker 下輪自退、尾行回報 stopped（只停本 repo）
uv run python "$AI_GUIDE/scripts/mail_waiter.py" stop
```

`start` 印出的 `worker` 命令（`uv run python <$AI_GUIDE/scripts/mail_waiter.py 絕對路徑> worker --address <repo> --generation N --state-dir <per-repo 目錄>`，shlex shell-safe quoting）放到背景 shell 執行即完成 arm——script 絕對路徑＋`--address`＋`--state-dir` 已釘死，背景 shell cwd 無關；喚醒收據的 `rearm` 欄位同形可直接複製。

## 喚醒回合 invariant（skill 明文合約）

worker exit 0（尾行 JSON `state=mail`）喚醒你後，**你的回合＝re-arm＋重進 once**：把尾行 JSON 的 `rearm` 命令（或 `start` 新印的命令）放上背景 shell，再走 [mail-handle](../mail-handle/SKILL.md) once 流程（`pending-replies`→`inbox` 全文→逐封 `mark-read`）。喚醒回合**不跑** `duty_receive process`（它建立五態處置帳並 ACK digest＝transport cursor 前進，不是普通看信）；新事件的存在由尾行 `new`（kinded 計數）如實呈報。`stop` 只停等待、保留待回覆。

漏掉 re-arm＝本 session 之後無人再喚醒你。尾行 `state=stopped`＝stop flag 權威（不 re-arm）；`state=superseded`＝新 arm 已接管（不需動作，除非 `status` 顯示無活 worker）；`state=fail-loud`＝配置面壞了（查 stderr 修因，不硬重試）。

### 夜間喚醒回合強化（AIR-318——夜間通信鏈）

1. **順序恆 re-arm → `status` 自檢 → once**：先貼 re-arm 命令、再跑 `status` 看 desired／staleness 自檢（`state=stopped`／`superseded` 依上段處置），最後進 once 看信。re-arm 失敗（命令非 0／背景 shell 未成立）→ 仍跑 once 看信，晨報記「watch 鏈已斷」（單夜從此無人喚醒——fail-loud 不靜默）。
2. **bounded batch**：喚醒回合最多處理 10 封、最多 1 個新設計分岔；超量記 deferred（夜間台帳留名）續原工作——喚醒回合是收信回合，不是開新弧的回合。
3. **熔斷**：單夜喚醒 >10 次 → `stop` 停哨＋晨報（防 ping-pong 燒額度——每輪喚醒都吃 context 與 token；>10 次＝通信鏈本身有迴圈，停哨等晨間判讀）。

## waiter 家族憲章（契約單一源——tri Q2 裁決；通知能力選擇唯一源＝[waiter-charter](../_common/waiter-charter.md)）

三員同契約：`scripts/bridge_waiter.py`（delegate-bridge fan-in）、harness_waiter、`scripts/mail_waiter.py`（本卡）。

- **背景 shell exit＝本家族的喚醒原語**：watcher 以背景 shell 退出喚醒自己的 session——這是本家族機制面，不是跨 harness 的唯一通知路徑；該 shell exit 能否把 session 叫回來依 carrier 當次實際能力判定（選路唯一源＝[waiter-charter](../_common/waiter-charter.md)）。
- **exit 0＝喚醒**：stdout 尾行單行 JSON＝唯一機判面（mail_waiter：`{"state":"mail","new":[{address,count}...],"rearm":"..."}`）；其餘進度行走 stdout、診斷走 stderr。
- **timeout 恆內部消化**：等待超時（dutymail class-6／bridge 124 等價語義）內部 re-arm 續輪，絕不外洩成喚醒。
- **處置權恆歸 caller**：watcher 只喚醒；stalled／錯誤面交人（或 woken LLM）判斷，watcher 不 stop 不重派不代處理。
- typed-failure 分流：storage/fencing＝跳輪＋心跳標記；usage/admission＝fail-loud exit 2（壞配置不硬跑）。
- coalesce：一次 exit 報該輪全部新事件（門牌×事件數；多門牌喚醒時其餘門牌以 events 非阻塞快照併入）——re-arm 從新 cursor 起，舊信不再觸發，不需合併窗口。
- `_waiter_core` 共用程式抽取：列為下次新 waiter 時的 follow-up（現三員各自內含，YAGNI）。

## generation CAS（雙 arm 防護）

每次 `start` 推進 `generation`；worker 每輪開頭驗 state.generation 仍＝自己的代、每次 state 寫入前重讀比對（read-modify-write guard）。效果：雙 arm 後舊 worker 自退（尾行 `superseded`、不寫 state）；events cursor 不回退；stale worker 不覆蓋新 generation 的 state。**同一輪喚醒只需貼一次 rearm 命令**——重複 arm 無害（舊代自退）但浪費背景 shell。

## state 與觀察軸游標

- state＝`${XDG_STATE_HOME:-~/.local/state}/ai-guide/mail-waiter/<repo 編碼>/state.json`（AIR-312 per-repo；identity injective 編碼——safe 字元原樣、其餘 percent-encode〔`%`→`%25`〕，不折疊；0600 atomic 寫）：`desired`／`generation`／`armed_at`（worker 每輪刷新＝活性證據）／per-address 雙 cursor（`cursor`＝unkinded events 觀察游標供 `wait` 掛哨（face 無 `--kind`）；`accepted_cursor`＝kinded 游標供 `events --kind accepted` 計數——喚醒真值恆 kinded 軸（wait 只是中斷器），兩軸 token 不可互餵；null=冷啟）＋`last_event_seq`／`last_exit`／`last_round_failed`。
- 冷啟（cursor null／state 缺席或損壞）：首輪雙軸 events 由頭對滾到 head＋彙總喚醒（寧重不漏——歷史事件可能重複觸發一次喚醒）。
- **觀察軸 vs transport 軸不互代理**：waiter 的 events cursor 只標記「已看到的時間線位置」；收信面的 delivery cursor 恆由消費面在處置後推進（S2 消費整合接線前不推進——信留原處）——兩線獨立，waiter 推進自己的不等於信已處理。

## 升級窗口：舊全域 watcher（AIR-266 形態——M3）

新 `stop` 只寫本 repo 的 per-repo state（`mail-waiter/<repo 編碼>/`）——**不控制**升級前以舊全域單檔 state（`<XDG>/ai-guide/mail-waiter/state.json`——無 `<repo>` 層）掛哨的舊 worker：舊 worker 讀舊檔、新面只讀 per-repo 目錄，兩者互不可見。升級程序（**無自動遷移、無跨 repo 自動 stop**）：

1. 升級前在**原 session** 跑（舊版）`stop`——舊 CLI 落 flag 到舊全域 state；或確認舊 worker 背景 shell 已隨其 session 結束（session 級生命週期——背景 shell 不跨 session）。
2. 程序面檢查：`ps` 查 `mail_waiter.py worker` 程序在場與否；在場且非本 session 所 arm＝殘留——回原 session stop 或終結該程序。
3. 活性判準＝`status` 的 per-repo state＋上述 ps 檢查；殘留舊全域 state 檔無人再讀（新面只讀 per-repo 目錄）、留置無害——禁以該檔存在宣稱任何 watcher 在場。

## 職責分工（誰管什麼——不互代理）

| 機制 | 面 | 時間軸 | 職責 |
|---|---|---|---|
| **mail_waiter（本 skill）** | 觀察軸掛哨 | 背景 shell（session 級） | 新事件喚醒本 session（wait＋events 唯讀面） |
| duty_receive S2 inbox | 普通看信 | once（`inbox`／`show` 全文＋`mark-read` 逐封 ACK＋`pending-replies` 義務） | transport cursor 前進邊（逐封 ACK 後推進；原信留原處） |
| ~~monitor hook（duty-monitor）~~ | ~~session advisory~~ | ~~prompt 邊界~~ | **已退役（AIR-312）且 inert no-op**——session-local baseline 提醒註冊拆除，腳本留 repo 無接線（舊 session snapshot 觸發＝零副作用；stale 註冊升級＝operator `--prune-stale`，見 [hooks/AGENTS.md](../../hooks/AGENTS.md)） |
| SC INBOX | 人類 viewport | 永續 | human seen/done 權威、信件全文判讀面 |
