---
name: bridge-dispatch
description: "delegate-bridge 委派深層載體 — codex web pool（webgpt）大內容紀律（turn body 計算含整個 turn、session 歷史計入；大材料寫進 repo 檔案只派路徑；失敗勿原樣重派——carrier 自動重試同 payload 放大限流；觀測值與失敗態分流）與 dispatch⇄collection 完整模式（背景 detach 完成不通知、waiter exit 即通知；單顆短工前景 shell vs N 顆平行 --background＋fan-in wait 場景；wait exit 124 re-arm 禁重派；--stuck-after family 起跳值；重啟後恢復 playbook——runs 禁盲重派、show --json 收完成、重掛 wait；綠 runs 不證健康）。always-on 核心（registry pin 唯一源、caller surface→合法路徑對照表、禁造第二 pin、glm provision 前置／resume model-match 契約）在 rules/bridge-dispatch.md；跨 repo 呼叫 delegate-bridge、派工後收結果、背景 job 卡死或 app 重啟後恢復時載入。觸發詞：delegate-bridge、task --background、wait、fan-in、webgpt、codex web pool、chatgpt-web、stuck-after、runner id、re-arm、exit 124、prune、pin resolver、installed_plugins.json、caller surface、dispatch collection、派工回收、bridge_waiter、CollectionReceipt、stalled-advisory。"
---

# bridge-dispatch — delegate-bridge 委派深層

> 本 skill 是 `rules/bridge-dispatch.md` 的 on-demand 深層載體：rule 端保留 always-on 核心（registry pin 唯一真相源、caller surface→合法路徑對照表、禁造第二 pin、glm provision 前置＋resume model-match 兩條、webgpt 序列化一句、dispatch⇄collection 配對一句）；本檔承載 webgpt 大內容段與 dispatch⇄collection 完整模式。事故脈絡與權威細節在 delegate-bridge repo（各節附路徑）。

手拼版本化 cache 路徑事故（rule 端禁手拼的 why）：反覆 GLM 派工摸到 stale 舊版 binary，`Model creation failed` 連敗且被誤分類為額度問題，診斷燒掉一輪——修好的新版就在同一個 cache。「第二 pin」的常見形態另有 `ls | sort -V | tail` 猜最大版。

## codex web pool（webgpt）大內容

ChatGPT web edge 拒絕過大 turn body，計算含**整個 turn**（session 歷史計入；resume 中型舊 session 也會超標）。大材料寫進 repo 檔案、prompt 只派**檔案路徑**讓 runtime 自讀；失敗**勿原樣重派**——carrier 會自動重試同一 payload，放大限流。精確觀測值與失敗態分流 → delegate-bridge repo `AGENTS.md`「Caller dispatch discipline」節。

## Dispatch⇄collection 配對（派工必配回收）——完整模式

delegated job 完成時**不會通知任何人**——`task --background` detach 是設計（setsid 背景工人生存過 app 重啟），代價＝完成無人觸發；root cause 是 caller 紀律缺口（派了沒安排回收），**waiter exit 就是通知**。單顆短工＝前景 `task` 丟 harness 背景 shell（shell exit＝完成通知；app 重啟即死，僅廉價輪可受）；N 顆平行／長工（muse 6–15+ min）／須活過重啟＝各 `--background`＋**派工同 step 自動 arm watcher**——開**一顆**背景 shell 跑 `uv run python scripts/bridge_waiter.py <jobId...> [--kind discussion|implementation|research] [--sink jobId:PATH] [--anchor jobId:TOKEN]`（watcher 內部包 fan-in `wait`：正常長跑期間零喚醒、exit 124 恆內部消化 re-arm 永不外洩；全 terminal 才叫醒並 stdout 尾行輸出 CollectionReceipt JSON——exit 0＝全 terminal completed 且 delivery 過（manual-anchor 視同過）、exit 1＝任一 terminal 非 completed，或 completed 但 sink 三步驗收不過（兩者皆出 receipt）、exit 2＝fail-loud（reconcile＝ledger 重生／重派跡象——**禁 retry 禁重派**；error、usage 透傳）、exit 3＝stalled-advisory 只喚醒不處置——偵測與處置分離，stop／重派決策恆歸主 session）。手動 fan-in `wait` 全部 id 降為 fallback：script 不可用時的替代（`wait` exit 124＝timeout 到仍在跑→**re-arm 非失敗**、禁重派——detached worker 仍在燒額度）與 app 重啟後手動恢復路徑——**重啟後對 running id 重新 arm watcher（同主路徑）；playbook＝script 不可用時的手動替代**（playbook 見下指針）；`--stuck-after` 起跳值按 family scale；`--sink`／`--anchor` 可重複（N 顆多 sink 常態）。push／daemon＝out-of-scope（forwarder 紀律）。

完整模式（場景表＋sh 範例＋family 起跳值＋重啟後恢復 playbook：先 `runs` 禁盲重派、`show <id> --json` 收完成、running 重掛 `wait <id> --stuck-after`——綠 runs 不證健康）→ delegate-bridge repo `plugins/delegate/skills/delegate-run-output/SKILL.md`「Dispatch ⇄ collection discipline」節。

watcher 節（本 repo）：自動 arm 規約與場景分工見上「Dispatch⇄collection 配對——完整模式」段；watcher 狀態機 frozen spec T1-T9、exit 契約、動態 T 公式（T0=clamp(P50/3, 5m, 15m)、fresh progress T×1.5 cap 20m）單一源＝`scripts/bridge_waiter.py` module docstring（變更走卡 amendment）；CollectionReceipt 欄位集權威＝AIR-135.7 AC#2 bounded receipt（watcher 側投影定義在 bridge_waiter.py docstring，非新 schema；AIR-149 EP＝bridge／harness 兄弟契約同源文件；sink 三步驗收程序單一源＝delegate-run-output「Receipt acceptance」節，本檔引用不自創）。
