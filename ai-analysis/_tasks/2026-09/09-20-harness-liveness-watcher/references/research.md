# 段落 0 研究紀錄（references）——harness liveness watcher

> 本檔吸收三份暫存調查（原在 gitignored `.agent-tmp/`，EP 禁依賴暫存路徑——依 AIR-146 guard 教訓轉錄）。provenance：lite-verify probe（AIR-148）、codex 死亡語義討論（bridge job job-mu9lcidp-aamqvr）、codex harvest-kill 確認輪（job-mu9lxzsj-5aepja）、codex guard-v2（job-mu9lxzq1-mymixh，屬 card-diagram guard 弧非本 EP）。

## 一、ZCode subagent 可觀察面（AIR-148 probe 實證）

- **執行模型**：subagent 無獨立 process——跑在 parent session 的 `zcode-cli` process 內（祖鏈實測 `zsh ← zcode-cli ← zcode-host-local-1 ← ZCode GUI`）；ps 無 per-task 特徵。host CLI 死＝任務死；**不會被新 process 接管**（接管偵測不需要）
- **主登記**：`~/.zcode/cli/agents/sess_<parent>/agent_<id>/metadata.json`——status（running/completed/failed/stopped）spawn 與 terminal 兩點寫入；**run 期間 mtime 零推進（反指標，禁當 liveness）**
- **最佳 liveness 檔**：`~/.zcode/cli/rollout/model-io-<taskId>.jsonl`——每次 model I/O 即時 append（mtime 落後 <10s）
- **exec 面**：`~/.zcode/cli/exec/sess_<taskId>/call_*-stdout.log`——工具執行中 zsh 持 fd 直寫（可用 lsof 偵測 open lease）；完成後目錄清空
- **terminal 面**：`~/.zcode/cli/log/zcode-YYYY-MM-DD.jsonl` 的 `subagent.background.started/.completed`（僅兩點、無心跳、無 pid）；`output.txt` terminal 一次性寫
- **陷阱**：`~/.zcode/v2/tasks-index.sqlite` 不收 Task-tool subagent；39 個 stale-running metadata（最老 25 天）證明 crash-without-terminal-event 真實存在且無清掃
- **bridge 前景派工無心跳軸**：heartbeatAt/lastEventAt 僅寫 `--background` job（rust task.rs:1032-1037「Foreground tasks never call this」）

## 二、codex 死亡語義（job-mu9lcidp）採納結論

- 術語：禁 zombie→`stale-running`／`dead-host`／`orphaned-running-record`
- 四 invariant：`EXECUTION_DEAD ≠ WORK_FAILED ≠ RETRY_SAFE`；`TERMINAL ≠ COMPLETE`；`STUCK_SUSPECT ≠ DEAD`
- 三事分離：body alive?／surviving work exists?／deliverable already exists?
- false-death 最壞＝split-brain（雙 writer／晚到覆蓋／雙外部 job／control plane 不知哪個 attempt canonical）
- worker heartbeat（選項 C）不進 correctness path：長 reasoning 無法 touch file；prompt compliance 與 wedge 相關失敗
- 上游 task-status API（選項 B）＝replacement path——fs layout 包 adapter 層，未來換源不動語義

## 三、harvest-then-kill 政策（user 裁決 0920＋codex 確認輪修正）

- **user 實證裁決**：20 分鐘全面零輸出＝bug（非深推理）——model streaming 連推理 token 都寫 rollout
- **凍結判準（精確定義）**：`20m 無 rollout/artifact growth ＋ 無 active exec lease/handle ＋ 無 terminal transition`。注意：zsh 持 fd 不會推進 mtime/size——長靜默命令須以 **open-fd lease**（lsof）豁免，否則誤殺；無法判定＝dispatch-time `silence_budget` lease（有期限，禁永久 class whitelist）
- **機器 suspend 不計靜默**：兩次 poll 間隔異常大→重置/扣除該段
- **順序**：`freeze → harvest A → wake main → TaskStop → stop verification → harvest B/delta`。**禁 kill 前重檢 silence**（那是把政策又變回 liveness inference——20:30 吐一行就逃過處置）；恢復活動記 `resumed_during_quarantine=true` telemetry，仍照砍
- **TaskStop ≠ all-writers-gone**（detached child 存活是殘餘 split-brain 路徑）→ 護欄：①in-harness brief 禁未登記 long-lived/daemonized child（要 server 須在 dispatch 記 ownership handle）②STOP verification：metadata terminal＋cursors 短 grace 不再變，否則 `STOP_INCOMPLETE` 禁重派
- **harvest bounded**：先 metadata/cursor/raw tail/manifest；超限 `harvest_partial=true` 照樣砍；JSONL 收 raw bytes（append 中末行半截合法，kill 後再解析）
- **wake dedup**：freeze alert 後留 pending intervention receipt，不逐輪重發
- **generation mismatch（host 死/registry 移除）＝hard-death path，立即喚醒**，不等 20 分鐘
- **attempt fencing 重型實施拿掉**；留薄 attempt_id/generation 供 harvest/stop receipt/redispatch 對帳；`EXECUTION_DEAD` vs `RETRY_SAFE` 分離保留（TaskStop 成功＝harness 執行終止；外部 side effect 未必 retry-safe）
- **自動 retry actor＝獨立 boundary，不在本 EP**（AIR-135.7「偵測與處置分離」邊界保留）

## 四、bridge watcher（AIR-146）設計事實

- bridge 背景工維持 advisory-only（遠端、計費異域、實證可靠）；AIR-146 `no stop/no retry` 不隨本 EP 改
- bridge CLI 2.0.22 無 `--version` 面（實測 exit 2）——版本 pin 走 registry pin 路徑段兜底（AIR-146 已實作）
- `wait` exit 面：0 全 completed／1 任一 terminal 非 completed／124 timeout→re-arm／2 usage
