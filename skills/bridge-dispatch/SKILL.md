---
name: bridge-dispatch
description: "delegate-bridge 委派深層載體 — codex web pool（webgpt）大內容紀律（turn body 計算含整個 turn、session 歷史計入；大材料寫進 repo 檔案只派路徑；失敗勿原樣重派——carrier 自動重試同 payload 放大限流；觀測值與失敗態分流）與 dispatch⇄collection 完整模式（背景 detach 完成不通知、waiter exit 即通知；單顆短工前景 shell vs N 顆平行 --background＋fan-in wait 場景；wait exit 124 re-arm 禁重派；--stuck-after family 起跳值；重啟後恢復 playbook——runs 禁盲重派、show --json 收完成、重掛 wait；綠 runs 不證健康）。always-on 核心（registry pin 唯一源、caller surface→合法路徑對照表、禁造第二 pin、glm provision 前置／resume model-match 契約）在 rules/bridge-dispatch.md；跨 repo 呼叫 delegate-bridge、派工後收結果、背景 job 卡死或 app 重啟後恢復時載入。觸發詞：delegate-bridge、task --background、wait、fan-in、webgpt、codex web pool、chatgpt-web、stuck-after、runner id、re-arm、exit 124、prune、pin resolver、installed_plugins.json、caller surface、dispatch collection、派工回收。"
---

# bridge-dispatch — delegate-bridge 委派深層

> 本 skill 是 `rules/bridge-dispatch.md` 的 on-demand 深層載體：rule 端保留 always-on 核心（registry pin 唯一真相源、caller surface→合法路徑對照表、禁造第二 pin、glm provision 前置＋resume model-match 兩條、webgpt 序列化一句、dispatch⇄collection 配對一句）；本檔承載 webgpt 大內容段與 dispatch⇄collection 完整模式。事故脈絡與權威細節在 delegate-bridge repo（各節附路徑）。

手拼版本化 cache 路徑事故（rule 端禁手拼的 why）：反覆 GLM 派工摸到 stale 舊版 binary，`Model creation failed` 連敗且被誤分類為額度問題，診斷燒掉一輪——修好的新版就在同一個 cache。「第二 pin」的常見形態另有 `ls | sort -V | tail` 猜最大版。

## codex web pool（webgpt）大內容

ChatGPT web edge 拒絕過大 turn body，計算含**整個 turn**（session 歷史計入；resume 中型舊 session 也會超標）。大材料寫進 repo 檔案、prompt 只派**檔案路徑**讓 runtime 自讀；失敗**勿原樣重派**——carrier 會自動重試同一 payload，放大限流。精確觀測值與失敗態分流 → delegate-bridge repo `AGENTS.md`「Caller dispatch discipline」節。

## Dispatch⇄collection 配對（派工必配回收）——完整模式

delegated job 完成時**不會通知任何人**——`task --background` detach 是設計（setsid 背景工人生存過 app 重啟），代價＝完成無人觸發；root cause 是 caller 紀律缺口（派了沒安排回收），**waiter exit 就是通知**。單顆短工＝前景 `task` 丟 harness 背景 shell（shell exit＝完成通知；app 重啟即死，僅廉價輪可受）；N 顆平行／長工（muse 6–15+ min）／須活過重啟＝各 `--background`＋**一顆**背景 shell fan-in `wait` 全部 id。`wait` exit 124＝timeout 到仍在跑→**re-arm 非失敗**、禁重派（detached worker 仍在燒額度）；`--stuck-after` 起跳值按 family scale。push／daemon＝out-of-scope（forwarder 紀律）。

完整模式（場景表＋sh 範例＋family 起跳值＋重啟後恢復 playbook：先 `runs` 禁盲重派、`show <id> --json` 收完成、running 重掛 `wait <id> --stuck-after`——綠 runs 不證健康）→ delegate-bridge repo `plugins/delegate/skills/delegate-run-output/SKILL.md`「Dispatch ⇄ collection discipline」節。
