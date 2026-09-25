---
harness-scope: neutral
---

# Bridge Dispatch 紀律

跨 repo 呼叫 delegate-bridge：registry pin＝安裝位置唯一真相源，禁手拼版本化 cache 路徑、禁第二 pin；caller surface 合法入口對照表＝bridge-dispatch skill。

- glm provision 前置：首次 glm 委派前必跑 `delegate-bridge provision --family glm`。
- 派工必配回收：waiter exit 即通知、全 terminal 喚醒輸出 CollectionReceipt；watcher＝`scripts/bridge_waiter.py` 背景 shell fan-in 包 wait（124 內部消化、exit 3 stalled advisory wake、exit 2 禁重派）；裸 `wait` 背景 shell 降為 fallback（exit 124 仍＝re-arm 非失敗、禁重派）。terminal ≠ complete：有 sink 登記者以 artifact 機驗（存在＋非空＋錨點）為完成，無登記者以 bounded receipt 非空為完成；workflow 層配套（bounded slices／checkpoint 續寫）單一源＝AIR-135.7 契約。
- 長輸出：預期輸出逼近上限→交付一律檔案承載（分塊＋checkpoint），禁純文字長文。
- codex web 整包預算 <100K chars（死亡線 ~100K–126K）；估算式、替代路由、大內容細節＝bridge-dispatch skill（webgpt 節）。
- MCP face（2.2.0+）：plugin 自帶 `.mcp.json`（ZCode/CC 安裝即註冊九個 `bridge_*` tools，安裝即 pin transition、免接線免 rot）；codex 走 `scripts/codex-mcp-wiring.mjs`（config.toml stanza，易腐——codex 更新後重跑 apply＋doctor）；`bridge_task` MCP tool 恆 `--background`＋receipt→`bridge_wait` 回收；codex-web `knownFalseNegative` extra（upstream #674）＝失敗先查 ChatGPT tab／worktree 產物再論重派（re-dispatch trap）。細節＝bridge-dispatch skill（MCP face 節）。

webgpt、glm resume model-match、Brief 動詞紀律、失敗態分流等細節＝bridge-dispatch skill。
