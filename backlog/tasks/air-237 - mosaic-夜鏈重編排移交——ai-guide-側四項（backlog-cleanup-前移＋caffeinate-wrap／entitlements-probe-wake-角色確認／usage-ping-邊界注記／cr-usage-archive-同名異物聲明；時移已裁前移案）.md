---
id: AIR-237
title: >-
  mosaic 夜鏈重編排移交——ai-guide 側四項（backlog-cleanup 前移＋caffeinate
  wrap／entitlements-probe wake 角色確認／usage-ping 邊界注記／cr-usage-archive
  同名異物聲明；時移已裁前移案）
status: In Progress
assignee: []
created_date: '2026-10-02 13:30'
updated_date: '2026-10-02 13:31'
labels: []
dependencies: []
ordinal: 228000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
mosaic 排程重編排 tri 收斂案移交（msg 7bdf4316→ai-guide-primary；sender ea1f3ae9；設計全文 mosaic_alpha/.agent-tmp/schedule-redesign/consolidated-design.md）。user 目標：半夜 3 點 pmset 喚醒跑 usage ping 就好、ZCode 不長駐防睡眠。user 授權時移裁量（原話「時移隨你裁決」）。

**時移裁決＝前移案（muse）**：3:00 窗只留 ping（3–5min）符合 user 原話語義；glm 不動案的 nightly catch-up 佔 ~20min 且自己標注「風扇噪屬臥室體感」，違反原意。ai-guide 側唯一 plist 異動＝backlog-cleanup 23:50→21:50（mosaic 側 2 顆 plist mosaic 自行做）。

四項：
① deploy/backlog-cleanup.plist Hour 23→21＋deploy/scripts/run-backlog-cleanup.sh 補 caffeinate -is wrap（guard＋exec 防 re-exec；兩腿共識缺口——睡眠中啟動的清場批次跑一半斷電＝半套 git 狀態；mosaic 側同款修改 mosaic 自行做——twin 註記同步）
② entitlements-probe wake 角色確認：StartInterval 3600 的 on-wake fire＝launchd 對睡眠逾時 interval 補 fire 一次（coalesce 單次——man launchd.plist＋glm 案註解雙源）；**--min-interval 裁決不縮短**——它是防連續重複 fire 閘（預設 30min），wake 前 machine 已睡數小時、age 恆過閘不擋 wake fire；縮短只增加無謂 probe 成本。03:00 窗快照最壞 ~40min 舊（GLM 5h 窗粒度可接受）。**live wake-fire 實測待 mosaic 側 pmset 03:00 wake 安裝後的次晨**——查 ~/.mosaic/logs/ops/launchagent-ai-guide-entitlements-probe.log 是否有 03:0x entry（本卡 NOTES 記結果）
③ skills/usage-ping/SKILL.md 增邊界注記：夜鏈 03:00 launchd claude -p 屬 headless 變體、非本 skill 排程面（CronCreate）；skill 的 session 綁定／host 關閉 skipped 不補跑語義不變——此語義是 mosaic 設計的關鍵依據，文檔明文化
④ scripts/cr_usage_archive.py 同名異物聲明：cr-usage＝code-reality 工具呼叫量測（AIR-206④），與 usage-ping／LLM 配額無關、無需接 ping log——docstring 明文化。「夜間機器不睡」假設段落掃描：rg skills/ rules/ scripts/ deploy/ 僅 harness_waiter.py 的 SM-7 睡眠會計邏輯（睡眠感知扣除——正確語義非假設），ai-guide 文檔零「不睡」假設、無需修改

```mermaid
flowchart LR
    M['mosaic 夜鏈重編排<br/>3:00 pmset wake＝ping 窗'] --> A1['① backlog-cleanup<br/>23:50→21:50＋caffeinate wrap']
    M --> A2['② entitlements-probe<br/>wake fire 角色確認<br/>min-interval 不縮短']
    M --> A3['③ usage-ping 邊界注記<br/>headless 變體非 skill 面']
    M --> A4['④ cr-usage-archive<br/>同名異物聲明']
    A2 --> T['live fire 實測<br/>pmset 安裝後次晨查 log']
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

- [ ] #1 backlog-cleanup plist 前移 21:50 且 XML 可解析 `uv run python -c "import plistlib; plistlib.load(open('deploy/backlog-cleanup.plist','rb')); print('ok')"` → exit 0 且 Hour integer 為 21
- [ ] #2 清場腳本 caffeinate wrap（guard 防 re-exec＋twin 註記同步） `rg -c "caffeinate -is" deploy/scripts/run-backlog-cleanup.sh` → ≥1 且 `bash -n deploy/scripts/run-backlog-cleanup.sh` → exit 0
- [ ] #3 usage-ping 邊界注記（headless 變體非 skill 排程面＋skipped 不補跑語義不變） `rg -c "headless" skills/usage-ping/SKILL.md` → ≥1
- [ ] #4 cr-usage-archive 同名異物聲明（與 usage-ping／LLM 配額無關） `rg -c "usage-ping" scripts/cr_usage_archive.py` → ≥1
- [ ] #5 ②的裁量與 live-test 計畫記卡 NOTES（min-interval 不縮短理由＋pmset 安裝後次晨查 log 步驟） `rg -c "min-interval" "backlog/tasks/air-237 - mosaic-夜鏈重編排移交——ai-guide-側四項（backlog-cleanup-前移＋caffeinate-wrap／entitlements-probe-wake-角色確認／usage-ping-邊界注記／cr-usage-archive-同名異物聲明；時移已裁前移案）.md"` → ≥1（NOTES 段）
