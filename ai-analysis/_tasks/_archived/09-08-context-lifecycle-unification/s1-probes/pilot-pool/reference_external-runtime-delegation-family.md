---
name: external-runtime-delegation-family
description: muse/codex/grok 委派同族——派發政策（實作預設/審查優先/gate）＋收法階層（fire-and-forget/認領制）
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_f7c5d96f-b42e-464c-b528-2888a526f654
---

三家 external-runtime 委派 plugin（muse / codex / grok-build）同族架構：bridge script（.mjs）包 headless CLI；rescue agent＝forwarder（恰好一次 task/run 呼叫、stdout 原樣返回、**禁自跑 status/result/poll——三家 skill 契約同款**）。

> merged_from: feedback_muse-delegation-option-not-default, 2026-09-07 cluster-merge wave（派發政策史作廢段落僅留指針，見本節 DROPPED）

## 派發政策與飄移防線（original: feedback，2026-09-07 併入）

**現值（09-07 user 拍板）**：implement profile 委派升**預設**（重實作段 muse、機械段 flash）；跨家族審查 muse 優先（09-05「Muse 應該在我要跨家族的審查時候先用」）；gated routing（eligibility gate＋reviewer 契約，不可省）——完整政策見 model-routing skill dispatch 節＋[[quota-failover-policy]]。**作廢**：09-07 前「muse 實作＝選項非預設／user 點名才啟動」已作廢。

**仍活①排序錨教訓**：單次指示≠常設模式——AI 因一句「一樣用 muse 實作」把 muse 批次當既定目標、舊前置卡排最前（AIR-13 D1/D2/D3 實證）。排序依實際價值與時效，委派由 user 當場表達，不從歷史指示外推。

**仍活②接管飄移防線（09-03 實證，user「我快瘋了，跟個笨蛋講話」）**：muse 執行力可用但兩系統性弱點——①**宣稱落地≠落地**（「design.md §3.3 已改」實 rg 零命中）；②**結構級修正弱**（分界移動只貼字不動圖/EP 分岔結構）。接管＝逐項 rg 驗其「已改」宣稱＋結論重落全部載體；字面修補循環直接換手。成功形對照（同日深夜 post-build 全綠＋GLM 複驗 100%）：分工照**工具能力**切（碰不到的工具 orchestrator 親做）＋七節工單＋「逐字引用驗收」條款——飄移防線在工单與驗收端。session 記錄讀取法見 [[muse-code-cli-facts]]。

DROPPED：09-03/09-04/09-05 政策演進流水（選項非預設→reviewer 優先→實作預設三段，終態已由 model-routing skill dispatch 節承載，repo 可推導）。

## 完成回報模型（09-05 盤點；doctrine＝push，AIR-26/4b1950d 定版）

- **收法階層（09-07 修訂，現值單一源＝model-routing skill「完成回報收法」決策樹）**：長跑頭形態＝**fire-and-forget**（`task --background` 提交→jobId 即回→caller 結束 turn 釋放→晚收 `wait` 有界迴圈／`show` 跨 session 認領；多工複用＝一 session 掃 N jobId）；簡單轉發／不想跨 session＝**push 阻塞形**（下方「真 push 收法」）；LLM 層 fallback＝ETA-gate。「前景阻塞」僅是機制描述非收法建議。**額度耗盡處置（429 quota exhausted 實證 09-07）**：fire-and-forget 補派可排程化——CronCreate 一次性排程於 reset+1min 自動提交（prompt 自足帶工單路徑與失敗處置），dual-family 另側顯式記錄降級不靜默。
- 前景阻塞同步＝機制事實：跑完最終輸出直接在 stdout；約束＝前景 Bash 10 分鐘上限，xhigh 長跑撞牆 → 走 fire-and-forget。
- **`--background` 形態**：muse＝detached worker（`detached:true`＋`unref()`，脫離 caller 進程樹）＋workspace ledger 持久化（`.muse-bridge/`——entry 存 status/exitCode，finalText 讀取時由 per-job jsonl 重導出；`show`／`export` 晚收）＋`--prompt-file`；codex＝detach 進 job queue，提示 `/codex:status <jobId>`；grok＝`/grok-build:runs <runId>`。外部 job 完成不推播進 session（三家皆無 callback——roadmap 在各自 plugin repo）；wrapper agent 提前 complete 的錯位三家結構上同在。codex 另有假完成形態：job 根本沒建立（[[reference_codex-config-zai-topology]]，解法重派新 agent 非輪詢）。
- **阻塞 wait 對照**（輪詢包進 bridge 內建 poll interval＋deadline，session 層一次阻塞呼叫收終態）：
  - codex：`node "$CLAUDE_PLUGIN_ROOT/scripts/codex-companion.mjs" status <jobId> --wait --timeout-ms <ms>`（task 本身無 --wait；先 --background 再 wait）；終局讀取＝同 CLI `result <jobId>`（plugin root＝`~/.zcode/cli/plugins/cache/openai-codex/codex/<ver>`，env 缺＝MODULE_NOT_FOUND）
  - grok：`runs --wait <runId>`（waitForSingleJobSnapshot）；review/critique 自帶 --wait
  - muse：bridge `wait` 子命令（0.2.4 落地，muse-bridge.mjs:1706）
- **timeout 訊號拆家系（AIR-26 審查實證，照一家操作另一家＝假成功）**：muse 到期＝`process.exit(124)`＋`--timeout 0`=forever；codex 到期＝**正常 exit 0**＋`--json` 帶 `waitTimedOut: true`（以此旗標判讀重掛，124 偵測對 codex 永不觸發）；codex **無 0=forever**——`--timeout-ms 0` 靜默回落 4min 預設（codex-companion.mjs:319 `Number(x)||DEFAULT` falsy fallback）
- **plugin hooks 三家皆有，ZCode 端無事件可觸發**：muse 0.2.4 hooks.json＝SessionStart reconcile stale jobs／SessionEnd cancel+kill on end；codex＝SessionStart/End（孤兒 job terminateProcessTree）＋Stop review gate；grok 同款——但 ZCode 3.7.7+ hooks＝7 事件子集**無 SessionEnd**（`ref-docs/harness/contracts.md:15,25` 定案）→ 孤兒清理 hook 在 ZCode 缺席。**09-07 視角反轉：此缺席正是 ZCode 端 fire-and-forget 的可行性基礎**——detached job 跨 session 存活、任何 session 以 `runs`/`show` 認領；CC 端 hook 生效＝SessionEnd 殺 running job，holder session 必須活著（fire-and-forget 限縮 session 內釋放 turn）。Remediation（user 09-05 確認）＝ZCode app 重開＋`git status` 查半套編輯；P0 教訓：宣稱「X 無 hook」前逐家 cat hooks.json。
- **背景 wait 形（session 活著需接續的首選；session 層零輪詢）**：背景 Bash 直呼 bridge 阻塞呼叫（process exit＝harness 自動 re-invoke，stdout 即終局輸出，背景 Bash 無 10min 限制）；或兩段式 `--background` 拿 jobId → 背景 Bash `status --wait <jobId>` → exit 喚醒 → `result` 讀取。**進度查詢面（非收法）**：ledger `runs --json`／`show <jobId>` status 瞬時；per-job jsonl 事件流（模型進行到哪）；mtime 增長＝活性；ps worker 進程——主動查＝這些，「等通知」只是省 request 的被動收法。**收法分流定案（09-07 dogfood 自抓 bug 後修入決策樹）**：純 `--background` 提交後完成**無推送不會自己回來**——session 活著要接續＝背景 Bash 掛 `wait`（首選兩段式，exit 自動喚醒）；不在乎即時＝認領制主動 `show`。曾因決策樹把 wait 形態誤描述為「session 仍被佔用」而漏收 review findings 五分鐘（user 抓包「你剛剛沒有一做完就知道然後接續做事？」）。
- **user 口語 effort 詞彙對譯（AIR-28 post-build 實用）**：「codex 用 sol max」＝`--model gpt-5.6-sol --effort xhigh`（「sol」＝gpt-5.6-sol；codex enum 頂格 `xhigh`＝「max」對譯——codex 無 `max` 值）；muse 端 pin spark-1.3/xhigh 免旗標；工單 read-only 靠 omit `--write`（codex）＋prompt 紅線（muse，task 無 --disable-write 旗標）。現值單一源＝model-routing skill effort 對譯表。

## 09-05 過期派發事故（教訓）

用 session 記憶的舊詞「resume-to-poll」叫 codex wrapper 回來輪詢 → wrapper 明確拒絕（thin forwarder 契約禁 poll/status/result）→ 正解＝主 session 直跑 companion CLI 背景 `--wait`。**當下條文（4b1950d 改寫 agents/AGENTS.md dispatch face）精確無誤**——錯在派發時用 session 記憶而非重讀治理檔：撞號調查時已看到 4b1950d commit 標題卻沒重讀條文就派發（「知道有改版」≠「重讀再派發」）；且 memory desc 舊教義（同步回報）開場載入持續灌輸舊模式。**教訓：派發外部 runtime 當下重讀 model-routing skill「完成回報收法」節——session 記憶與 memory desc 是過期源**。

## plugin 安裝面

- **codex**：marketplace `openai/codex-plugin-cc`（GitHub）；本地 clone `~/Github/codex-plugin-cc`＝upstream master＋本地 docs commits；版本真源＝repo `plugins/codex/.claude-plugin/plugin.json`，更新判定用內容 diff 非版號印象。
- **grok**：repo `xai-org/grok-build-plugin-cc`；本機 clone `~/Github/grok-build-plugin-cc/`＋**CLI 本體在場 `~/.grok/bin/grok`（Grok Build TUI、互動式；09-08 user 冒煙 🟢）**；plugin 形態 09-05 時點未安裝（ZCode enabledPlugins／CC 皆無）——安裝走 ZCode UI：Settings → Plugin Management → Discover。bridge subcommand 詞彙：task 位叫 `run`、另有 `critique`（codex 無此位）、`review`/`runs`。
- **安裝狀態判定法**：看 `~/.zcode/cli/plugins/installed_plugins.json`＋config.json `plugins.enabledPlugins`，**勿以 cache 目錄存在判定**（xai-grok-build 空殘目錄曾誤導——已清）。
