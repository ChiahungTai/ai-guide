# Handoff 草稿：ai-rules 承接——背景 agent liveness 兩項 skill 修正（源：delegate-bridge session 2026-09-13）

> 狀態：**時點已裁定（09-13 user/5.3）＝新 session 第一件事執行（~15 分鐘，lite 可——規格定死），然後才開 AIR-87**。內容經 codex 復議定版（bridge job-mtzs63qz）勿重辯；兩項 doc fix 免卡（commit message 帶事故脈絡）；probes/WAL 後續等要做時建卡（本 drafts 為歸宿）。源 repo 證據錨＝delegate-bridge fdc8c47；ai-rules baseline 4bf0570。
> 額外記錄（09-13 晚）：bridge GLM family 持續 failed-usage（Model creation failed）——已排除：provider 死（互動 session GLM 活）、staged key 過期（fresh restage 直測仍敗）；**root cause 未定**（候選：app 更新後 headless 路徑 auth/config 期望變更）＝delegate-bridge 側驗證修復；AIR-88 probe 同故障域阻塞中。與本 handoff 兩項正交（:227 修宣稱過期，與 bridge 現況故障無關）。
> 內容：model-routing SKILL.md:227 stale heartbeat 宣稱修正（bridge 已交付 d1/2.0.3/39b6964；flag 名＝`--stuck-after` 非 `--stuck-alert`）＋agent-workflow 背景 subagent 死亡盲區 doctrine（防禦階梯/watermark reconciliation/per-agent 分類/silence≠death、old-generation unresolved≠safe-to-retry；事故根因＝ZCode app 更新重啟殺 child process，2026-09-13 19:23 實證）。
> 範圍外另案：probes（lifecycle parent/in-process kill）＋register/check/reconcile 工具＋receipt WAL（等 probes 建卡）；上游 z.ai feedback 回報；glm bridge 先前 pending handoff（native-only＋write-mode edit 呼叫教學）。
> 完整 handoff prompt 原文＝本檔歷史（chat 落盤版）；codex 設計原文＝delegate-bridge .agent-tmp/codex-agentliveness-design.out（暫存勿依賴，要點已內嵌）。
