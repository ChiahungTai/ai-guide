# K1 觸發收據（TC-4 round 2 活體證偽）

- date: 2026-09-20（watcher 掛起 21:5x～23:0x local；原始 log＝同目錄 k1-replay2.txt）
- attempt: att-tc4-r2／task: sess_subagent_agent_62ff4091-507b-4b9d-9468-f60df29fcdff（真 subagent，brief＝sleep 300 靜默阻塞）
- 觀察窗: watcher 掛起後 60s 間隔輪詢；cycle 1＝fresh elapsed 3.1s（exec-lease-held telemetry）；cycle 2＝**unknown: rollout-anchor-missing**

## 事實（逐項機驗）
1. metadata status=running（真機活體：`~/.zcode/cli/agents/sess_2c1d13c6-8229-4156-95c0-1e3d71b2a862/agent_62ff4091-507b-4b9d-9468-f60df29fcdff/metadata.json` createdAt=2026-09-20T13:19:04Z）
2. rollout 檔**不存在**：`ls ~/.zcode/cli/rollout/ | rg 62ff4091` → 零命中（rollout 目錄僅三個 session 級檔案：2c1d13c6＝parent 16.8MB、c5edae9e、b9e0c3b8）
3. exec dir 存在：`~/.zcode/cli/exec/sess_subagent_agent_62ff4091-.../`（sleep 之 call log，fd held、零寫入）
4. artifacts 無
→ running 中的真 subagent：**四觀察面全數靜默/缺席**——「三面觀察判定靜默」前提證偽，K1 kill criteria 觸發（EP 預先承諾 Action＝pivot）

## 結論
- 子 agent model I/O **折疊進 parent session 層**（rollout 目錄僅 session 級檔案：parent 2c1d13c6、b9e0c3b8＝135.5 session、c5edae9e）——per-task rollout 前提死
- 凍結偵測（靜默計數）＝INVALIDATED；pivot＝timebox 模型（EP frozen spec v2）
- watcher 的 fail-loud（unknown rollout-anchor-missing，exit 1 禁誤報）行為正確——「無訊號≠死亡」紀律守住
