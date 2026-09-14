---
harness-scope: neutral
---

# Bridge Dispatch 紀律（delegate-bridge 委派路徑）

任何 session／script 跨 repo 呼叫 delegate-bridge（`task`/`review`/`usage` 等）：registry pin 是安裝位置的**唯一真相源**，**禁手拼版本化 cache 絕對路徑**（`.../delegate/<version>/bin/delegate-bridge`——版本號寫進筆記或工單的瞬間開始腐爛。真實案例：反覆 GLM 派工摸到 stale 舊版 binary，`Model creation failed` 連敗且被誤分類為額度問題，診斷燒掉一輪——修好的新版就在同一個 cache）。合法入口**按 caller surface 對號入座**：

| Caller surface | 合法路徑 |
|---|---|
| ZCode／Claude Code plugin surface（harness session） | `${CLAUDE_PLUGIN_ROOT}/bin/delegate-bridge`——harness 在 plugin 指令／skill 語境注入，自動解析 pin |
| Codex plugin context（delegate-codex skill） | `${PLUGIN_ROOT}/bin/delegate-bridge`（`CLAUDE_PLUGIN_ROOT` 僅 compatibility alias）；任務必帶 `--caller-harness codex` |
| ZCode／Claude Code bare shell | 呼叫當下 re-resolve：讀 `~/.zcode/cli/plugins/installed_plugins.json`（Claude Code 為 `~/.claude/plugins/` 下同名檔）取 `installPath` 拼 `bin/delegate-bridge` |
| Codex bare shell | **無 pin resolver**（config.toml 只有 marketplace source）——禁猜 cache 路徑；走 plugin surface 或 repo checkout dev binary |
| Muse session | plugin-less caller kit（delegate-bridge repo `docs/muse-caller-kit.md`）——無 plugin cache 語義 |
| 任何 harness 的 repo checkout | dev binary `rust/target/release/delegate-bridge` |

## 執行約束

- **禁造第二 pin**（stable symlink、「latest」 shim、`ls | sort -V | tail` 猜最大版）——任何第二真相源必漂移；殘留舊版靠 prune 清除，讓 stale 路徑 file-not-found 大聲失敗，而非靜默跑舊 binary。
- **codex web pool（webgpt）大內容**：ChatGPT web edge 拒絕過大 turn body，計算含**整個 turn**（session 歷史計入；resume 中型舊 session 也會超標）。大材料寫進 repo 檔案、prompt 只派**檔案路徑**讓 runtime 自讀；失敗**勿原樣重派**——carrier 會自動重試同一 payload，放大限流。精確觀測值與失敗態分流 → delegate-bridge repo `AGENTS.md`「Caller dispatch discipline」節。
