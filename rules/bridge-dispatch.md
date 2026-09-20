---
harness-scope: neutral
---

# Bridge Dispatch 紀律（delegate-bridge 委派）

跨 repo 呼叫 delegate-bridge（`task`/`review`/`usage`/`provision`）時：registry pin＝安裝位置**唯一真相源**，**禁手拼版本化 cache 絕對路徑**（`.../delegate/<version>/bin/...`——版本號寫進筆記即腐爛）。合法入口**按 caller surface 對號入座**：

| Caller surface | 合法路徑 |
|---|---|
| ZCode／Claude Code plugin surface | `${CLAUDE_PLUGIN_ROOT}/bin/delegate-bridge`——harness 自動注入並解析 pin |
| Codex plugin context（delegate-codex skill） | `${PLUGIN_ROOT}/bin/delegate-bridge`（`CLAUDE_PLUGIN_ROOT` 僅 alias）；任務必帶 `--caller-harness codex` |
| ZCode／Claude Code bare shell | 讀 `~/.zcode/cli/plugins/installed_plugins.json`（Claude Code 同名檔）取 `installPath` 拼 `bin/delegate-bridge` |
| Codex bare shell | **無 pin resolver**——禁猜 cache 路徑；走 plugin surface 或 repo checkout |
| Muse session | plugin-less caller kit（delegate-bridge repo `docs/muse-caller-kit.md`） |
| 任何 harness 的 repo checkout | dev binary `rust/target/release/delegate-bridge` |

- **禁造第二 pin**——第二真相源必漂移；殘留靠 prune，讓 stale 路徑大聲失敗。
- **glm provision 前置**：glm family 於 workspace 首次委派前必跑一次 `delegate-bridge provision --family glm`（delegate-bridge 面**唯一 sanctioned config write**；憑證輪替＝重跑 provision）。spawn verify-only：缺漏／未 provision／drift＝fail-loud 附指引，不自動補、禁 derive credential。
- **glm resume model-match**：定向接續 glm session 必帶**建立時**的 `--model <id>`（不帶＝落 manifest `defaultModel`）；不符＝carrier `Select a model` fail-closed。兩條定義源＝delegate-bridge repo `AGENTS.md`「Build loop」glm provisioning 段＋`docs/ep.md` S1（本兩行僅指針）。
- **webgpt 大內容**：turn body 過大（整 turn＋session 歷史計入）被 web edge 拒——大材料序列化進 repo 檔案只派**檔案路徑**；失敗勿原樣重派。
- **Dispatch⇄collection 配對**：派工必配回收——背景 detach 完成不通知，**waiter exit 即通知**；watcher 主路徑＝`scripts/bridge_waiter.py` 背景 shell fan-in 包 wait（exit 124 內部消化 re-arm、全 terminal 喚醒輸出 CollectionReceipt、exit 2＝fail-loud reconcile 禁 retry 重派、stalled＝exit 3 advisory 只喚醒不處置；exit 契約單一源＝bridge_waiter.py docstring）；裸 `wait` 背景 shell 降為 fallback（script 缺時；exit 124 仍＝re-arm 非失敗、禁重派）。terminal ≠ complete：有 sink 登記者以 artifact 機驗（存在＋非空＋錨點）為完成，無登記者以 bounded receipt 非空為完成；workflow 層配套（bounded slices／checkpoint 續寫）單一源＝AIR-135.7 契約。
- **長輸出任務形狀（dispatch-side）**：預期輸出逼近 catalog 上限的交接任務→交付一律檔案承載（sink 工單指定；單檔或分塊＋checkpoint 續寫），禁純文字回傳長文。定義源＝delegate-bridge repo `AGENTS.md`「Caller dispatch discipline」Long-output task shape 段（DB 弧 e115664；本行僅指針）。
- **Brief 動詞紀律（可寫 carrier）**：brief 的動詞決定可寫 carrier 的行為——審查／調查／盤點類 brief 必帶顯式 `READ-ONLY / no writes / no git`（走 work-order 模板 review/advisory variant），實作類 brief 必帶 scope fence（格式見 work-order 模板範圍限定節）＋禁 commit（commit 恆為主 session gate）；**省略動詞約束＋brief 內出現 CHANGE/ADD/DELETE 條目＝實質實作授權**。各 carrier 寫檔能力表單一源＝delegate-bridge repo `AGENTS.md`，禁兩 repo 重刻（案例群見 bridge-dispatch skill）。

webgpt 觀測值/失敗態分流與 dispatch⇄collection 完整模式見 bridge-dispatch skill。
