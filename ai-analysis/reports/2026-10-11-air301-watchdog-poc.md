# AIR-301 AC#4 — watchdog POC 報告：各 harness adapter 能力盤點

> 問題：長弧 heartbeat 的 dead-man switch 不能只靠 LLM 自停（liveness gate 條文是第一道）——額度歸零時 LLM 連自停都停不了（真實案例：codex 大架構弧 heartbeat 每 5 分鐘喚醒 96 次全空回應、殭屍 8 小時，`credits.balance: "0"`，零通知零失敗紀錄）。第二道＝進程外獨立 watchdog。本 POC 先查各 harness adapter 能否取得 quota／session 事件，再定最小可行 driver 形態。探查方法全唯讀（bridge 公開 CLI＋目錄存在性檢查；委派 session 環境，HOME 重定向至 WT `.delegate-bridge/zcode-home`——機器層目錄佈局探查僅供參考）。

## 發現：quota 面逐 harness

額度查詢已有集中式唯讀 face——`delegate-bridge usage [--family <f>] [--json]`（stateless：無 ledger、無 setup cache、不 gate 任何東西）。2026-10-11 實測輸出：

| family | usage face | 實測結果 |
|--------|-----------|---------|
| codex | **live** | 本委派環境 `codex not logged in`（環境面，非能力面——bridge 判定其為 live family） |
| glm | **live** | 本委派環境 provider preflight 讀不到 provision setting（delegated HOME 無 provision——primary checkout 跑一次 `delegate-bridge provision --family glm` 即解；bridge 判定其為 live family） |
| muse | **unsupported by design** | runtime 不暴露結構化 usage 源（headless exec stream 無 usage 事件、無 usage subcommand、無本地 state 檔）——face 回顯式 unsupported entry，非靜默 |
| grok | **unsupported by design** | 同上 |

**結論（quota 軸）**：codex／glm 額度可被進程外 watchdog 觀測（消費 `delegate-bridge usage --json` 即可，零 harness 內部接觸）；muse／grok 的額度軸**明確不可行**（runtime 無結構化源——不是探查不足，是 bridge usage face 的設計裁定），對這兩家退回「liveness gate 條文（第一道）＋checkpoint 凍結偵測（進程外）」，額度本身不可外部觀測。

## 發現：session 事件／活體訊號面

| 訊號面 | 可達性 | 載體 |
|--------|-------|------|
| bridge 腿活體 | **已達**（現成） | `.agent-tmp/liveness.jsonl`（waiter armed/heartbeat/advisory/collected 台帳）——watcher／sweeper／nag 已消費，watchdog 直接讀同一台帳，零新儀表 |
| thread-level heartbeat 活體 | **可達**（靠 liveness gate 留痕） | liveness gate 要求 wake 即一行進度落盤（checkpoint append）——checkpoint 檔 mtime 凍結即心跳凍結訊號，harness 中立；watchdog 對「申報中的 automation」監看其 checkpoint 路徑 |
| subagent 進程活體 | **已達**（AIR-296 已建） | spawn artifacts 掃描（zombie sweeper——launchd 唯讀 reporter＋事件台帳） |
| codex thread session jsonl 直讀 | 〔未驗證〕 | 本委派環境 HOME 重定向不可驗；watchdog v1 不需要它（checkpoint＋quota 兩輸入已足） |

## 結論：最小可行 driver 形態

**可行。最小形態＝launchd（或 cron）排程的唯讀 reporter 腳本**，完全 reuse AIR-296 zombie sweeper 的載體模式（唯讀 reporter＋結構化事件台帳＋五級告警；偵測與處置分離——禁自動 TaskStop／重派／寫 completed，處置恆人裁）：

- **輸入①**：`delegate-bridge usage --json`——額度歸零（codex/glm）→ loud 失敗落盤＋告警（正是 LLM 自停不可依賴的那個終態）。
- **輸入②**：申報中 heartbeat automation 的 checkpoint 路徑集——**「產物停滯＋心跳凍結」雙訊號**判 zombie（禁單一 CPU 訊號——model-bound 低 CPU 是常態，SC ticker 誤報教訓）。
- **輸入③**：bridge 腿沿用 `.agent-tmp/liveness.jsonl` heartbeat 軸（HEARTBEAT_STALE_THRESHOLD_MIN 既有閾值語義）。
- **輸出**：事件台帳（AIR-296 去重慣例）＋loud 失敗檔；處置建議留人裁。

**明確不可行面**：muse／grok 額度軸（見上）；此兩家的 watchdog 覆蓋率=「進程仍在但額度歸零」情境只能靠 checkpoint 凍結間接偵測（額度歸零→wake 空回應→零工具呼叫→checkpoint 不再前進——liveness gate 條文使空回應可被進程外觀測）。

## 後續（承接點）

driver 實作屬新工程（腳本＋launchd plist＋告警面接線），不在 AIR-301 條文範圍——建議另開卡承接，落點候選：擴充 `scripts/agent_liveness_sweep.py`（AIR-296 載體，共用判定核心）或平行新腳本；plist 版控落點依 AGENTS.md 慣例 `deploy/`。
