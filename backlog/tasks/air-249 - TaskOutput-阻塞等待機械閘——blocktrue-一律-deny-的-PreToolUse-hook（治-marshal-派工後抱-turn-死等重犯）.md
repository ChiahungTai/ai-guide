---
id: AIR-249
title: >-
  TaskOutput 阻塞等待機械閘——block=true 一律 deny 的 PreToolUse hook（治 marshal 派工後抱 turn
  死等重犯）
status: In Progress
assignee: []
created_date: '2026-10-04 13:07'
updated_date: '2026-10-04 13:38'
labels: []
dependencies: []
references:
  - hooks/taskoutput_block_gate.py
ordinal: 240000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
marshal 派完背景任務後，用 TaskOutput(block=true) 抱著 turn 死等——user 同日糾正兩次、教訓寫進 STATE 也治不了（記憶面對重犯無效）。mosaic 側提案（mos-171 session，信件 envelope 04efefd8）：加機械閘根治——背景任務結束時本來就會自動發完成通知（今天值星 session 實證），阻塞等待從非必要操作。

**做什麼**：PreToolUse hook 掛 TaskOutput——input.block == true 一律 deny，deny 訊息固定指引（「背景任務由完成通知回收；查狀態用 block=false；請結束 turn 或做不重疊工作」）。落地件：hook 腳本＋測試＋governance manifest 註冊＋ZCode ~/.zcode/cli/config.json user-level hooks 註冊（merge subtree 非整檔覆蓋）＋RED/GREEN 驗收 probe（block:true 被 deny／block:false 放行）。

**不做什麼**：不治判斷形狀的失誤（派工後沒找平行工作——那是判斷不是工具形狀，提案方誠實聲明的覆蓋邊界）；不部署 CC 端（CC face 已退役 AIR-215）；不改 TaskOutput 本體（harness 內建）。

**現在到哪／等 user**：Description 先行待點卡確認；初評已過三判準（單一入口／無語義例外／純機械），instruction owner 已存在（rules/tool-discipline.md 背景執行節）——hook 是既有規則的 enforcement。確認後補 AC/Plan 再實作。

```mermaid
flowchart LR
    U['user 糾正×2<br/>STATE 教訓無效'] --> P['mosaic 提案信<br/>機械閘根治']
    P --> H['PreToolUse hook<br/>TaskOutput block=true → deny']
    H --> G['block=false 放行<br/>查狀態正當用途']
    H --> N['背景任務 exit<br/>自動完成通知回收']
    N --> S['marshal 不阻塞<br/>重犯被機械根治']
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 hook 可編譯 uv run python -m py_compile hooks/taskoutput_block_gate.py → exit 0
- [ ] #2 deny 判準單元測試全綠（uv run pytest tests/test_taskoutput_block_gate.py）：block=true+timeoutMs=60001→deny exit 2＋JSON schema；block=true+timeoutMs=60000→allow；block=true 無 timeoutMs→allow；block=false→allow；block="true" 字串→allow；壞 JSON→allow；tool 非 TaskOutput→allow；deny 零副作用（無檔寫入）
- [ ] #3 governance manifest 註冊 rg -c "taskoutput_block_gate" governance/manifest.toml → ≥1
- [ ] #4 ZCode 註冊模板 rg -c "taskoutput_block_gate" governance/registrations/zcode.json → ≥1
- [ ] #5 hooks/AGENTS.md 同步 rg -c "taskoutput" hooks/AGENTS.md → ≥1
- [ ] #6 機械 probe 實跑：deny-case payload 管線輸入 → exit 2；allow-case → exit 0（管線 probe 非 live session）
- [ ] #7 live 註冊：~/.zcode/cli/config.json 含 entry＋JSON 可解析＋改前 .bak 備份在場；in-session live 觸發驗證＝新 session 首用時補（per-session 快照限制，notes 記錄）
- [ ] #8 回信 mos-171 completed（result_pointer 指向 hook commit）＋卡 notes 補 message_id
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide c9dd4b72〕
〔已決策勿重辯：①機制＝PreToolUse hook 掛 TaskOutput，deny 僅當 block==true（boolean）且 timeoutMs>60000——codex 討論腿 verdict「修正後 GO」：blanket deny 被否證（block=true 是 ZCode 正式等待語義、mid-turn 短等待與 completed 即返正當），原提案保險絲反轉為主規則；②fail-open 紀律閘（腳本異常放行＋stderr 診斷，kanban-skill-gate 同慣例）；③instruction owner 已存在＝rules/tool-discipline.md 背景執行節——hook 是 enforcement 非新規則；④CC 端 face 已退役（AIR-215）不部署；⑤提案源＝mosaic mos-171 信（envelope 04efefd8，user 指示 codex 討論後落地）；⑥字串 "true"／malformed 輸入＝fail-open 放行非 deny；⑦60000 邊界含（>60000 才擋）〕
範圍：hooks/taskoutput_block_gate.py（新）＋tests/test_taskoutput_block_gate.py（RED 先行）＋governance/manifest.toml surfaces.hooks 註冊＋governance/registrations/zcode.json PreToolUse matcher TaskOutput＋hooks/AGENTS.md 同步一行＋live 註冊（~/.zcode/cli/config.json 經 governance installer，.bak 備份先行）。verdict 檔＝.agent-tmp/taskoutput-gate/codex-verdict.md。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
codex 討論腿收線（job-mutuoblo-ittztp，watcher exit 0＋sink 機驗 .agent-tmp/taskoutput-gate/codex-verdict.md）：verdict＝修正後 GO——①零誤判主張被否證（block=true 是 ZCode 正式等待語義；mid-turn running task 短等待＋completed 即返皆正當），blanket deny 不採，原提案保險絲反轉為主規則（deny 僅 timeoutMs>60000，60000 邊界含＝放行）；②fail-open（crash／malformed／"true" 字串皆放行）；③deny 文案＝原因＋block=false 指引＋完成通知回收＋短 wait 例外；④部署＝manifest＋registrations/zcode.json＋hooks/AGENTS.md 同步＋新 session live 驗；⑤probe 增 timeout 邊界／completed／malformed／字串／alias／crash fail-open／deny 零副作用；⑥覆蓋邊界＝僅 PreToolUse 可見的 TaskOutput 形狀（不保證通知、worker 活性）。設計 pivot 記錄（值星初評被糾正）：初評支持 blanket deny＋丟 fuse——被 codex 否證，fuse 保留為主規則。
<!-- SECTION:NOTES:END -->
