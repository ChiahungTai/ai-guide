---
name: muse-code-cli-facts
description: Muse Code CLI 操作事實——JSONL 事件面、plugin gate、計費鐵則、bridge 機械、rules 64KiB 截斷 lane、session 記錄讀取
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_5ad68a25-9a25-4b25-95ac-84baf6c05d6f
---

Muse Code CLI（macOS arm64）實測操作事實。源＝`ref-docs/harness/meta/` 鏡像＋POC 實測；flag 級查證以實機 `--help` 為準。弧脈絡見 [[agents-registry-split-design]]。（09-08 蒸餾：收法 doctrine 歸 [[external-runtime-delegation-family]]，此檔留機械面）

## headless 委派面

- `muse exec --json`：**stdout＝JSONL 事件流、stderr＝人類可讀**；終局回覆 `run.terminal.completed`.payload.text、session id＝首行 `stream.id`、模型 `run.model.configured`.model_id。事件流內嵌 tool result——分類認事件型別/error table，泛 substring 必誤觸。exit code 只反映結束方式（0＝turn 完成≠做對、1＝失敗/取消/步數上限、2＝usage、130/143＝訊號；capped 亦 exit 1）——verdict 永不由 exit 推導。`--disable-approval` 含 network review 子層。`--model`／`--reasoning-effort none…ultra`（預設 high）／`--max-model-steps`／`--trust-workspace`（獨立於 --yolo）／`--session-id`／`--prompt-file`。

## rules 載入（09-07 probe 實證）

- **全域 user rules 路徑＝`~/.config/muse/AGENTS.md`**（官方文檔只說「machine-wide user rules always load」未載路徑；bridge task 三發 marker probe 實測：config/muse 命中逐字回引、`~/.agents/AGENTS.md` 與 `~/AGENTS.md` 皆不載）。always load（無 trust 前提）；衝突時專案 rules 贏。
- 專案層走訪序＝AGENTS.md → CLAUDE.md → `.agents/AGENTS.md` → `.claude/CLAUDE.md`（首個存在者贏該層、深者贏、上到 .git 邊界；需 workspace trust）——同目錄 AGENTS.md+CLAUDE.md 並存時 CLAUDE.md 被 ignore（bridge log warning 實證）。
- ai-rules guide bundle 已部署 muse（deploy_agents.py TARGETS 第四家）；~20K tokens 每 task 進 context（64KiB 截斷後）——訂閱 token 加總計費下委派成本面上升，必要時 `--steps`/短 prompt 控制總量；退場＝刪該檔＋移 TARGETS 行。
- **rules_file context block 硬上限 65,536B（64KiB；官方名＝subagent delegation startup context limit）、stderr 有 loud warning**（09-08 bridge review warning 全文實證：`rules file ... produced 92940 bytes, over the 65536 byte ... limit`——非全靜默，不重導 stderr 即漏）。**rendered ≠ 檔案大小 ≠ 入 context 值**：檔 79,287B → rendered 92,940B（全量渲染 log 值；舊記「92KB/produced」同此）→ 實入 context 65,53x（`text_bytes`）；session diagnostics 實證 65,536 截斷、65,534B 邊界檔全載。被切尾巴＝quality-constraints 中段＋tool-discipline 全部。官方文檔未載此上限。瘦身裁決材料見 ai-rules `backlog/drafts/draft-3`。
- **context assembly 面（09-08 枚舉）**：rules_file 單一 lane——無獨立 project-rules block、每 run 重組裝一次（同 session 多筆相同診斷＝多 run，非重複載入）；block 族＝workspace_identity/sandbox_policy/security_mode/skills_catalog（31.6KB 另 block 未截）/session_identity/memory_snapshot/workflow_availability/subagent_delegation。**lane 合流語義（09-08 機械定案）**：user/project **串接**進單一 rules_file lane 共享 64KiB，**user-first**（project 後串——超 cap 時專案層餓死：ai-rules 專案 AGENTS.md 12,550B 載入 0 bytes；**untrusted workspace：cap 降 32,000＋project 整檔跳過**〔`skipped_untrusted=1`；trading_lab 缺 `~/.config/muse/trust.json` 記錄實證——trust 是隱藏軸〕）；produced−檔 ≈ 專案層＋~1.1KB framing；UTF-8 字界 backoff（cap 65,536、CJK 字首切口 65,535）；23,583 之謎已解＝ai-rules workspace 串接渲染值（`sources=2 rendered_bytes=23583` log 鐵證）；mosaic 場景 rendered 123,208→65,536（砍 47%）——lane 全量測見 AIR-45 S0 report（ai-analysis/_tasks/09-08-context-lifecycle-unification/s0-report.md）。瘦身變體 user bundle 預算 ≈65,536−專案層−1.1KB（ai-rules 工作區 ≈51.9KB——draft-3 A 案數學按此）。四家截斷線對照＋量測細節＋處方：ai-analysis/reports/2026-09-08-codex-philosophy-instruction-layering.md（codex knob 102400 **已驗 runtime 生效**〔09-08 升級 0.153.4 後雙探針：尾端 sentinel＋71.5KB 處 rule 皆逐字回引——0.152.0 對 gpt-6-astra 過舊會 400〕；zcode 100KiB hardcode；opencode 09-08 退場〔本機無 CLI〕）。截斷未修期間，muse 工單須自足承載驗證/no-commit 紅線（被截尾巴正是那些 rules）。

## 隱藏 subcommand 與 plugin gate（09-06 實測）

- `muse schema generate-json-schema --out DIR`＝錯誤分類規格源（29 錯誤枚舉）；`muse serve`＝MSP stdio（持久 session 升級面）；`muse sandbox` 僅 windows（macOS 間接推斷）。
- **可用性真相源＝feature-config gate**（`~/.local/share/muse/feature-config/<hash>.json`，ttl 3600）：probe＝`muse plugins --help` 存在即開；文檔永遠落後（changelog 停 0.2.1、binary 已 1.0.3）。`--help` 不刷新 gate——刷新＝開一次互動 session。gate 關＝可寫不可裝（create-plugin skill 出貨，安裝步留 user）。muse↔CC plugin＝manifest 通、元件部分通（拒 tools/agents/outputStyles；hooks 格式差異未驗）。**user 定調**：gate 開前不投產 muse plugin；GLM 接軌不走 plugin（無 provider 面），launcher 路徑 `--provider echo|meta`＋`--base-url`（wire 相容未驗）。

## 模型與計費

- 裸 CLI 預設模型漂（1.2-contributor↔1.2）——必顯式 `--model`；**bridge 穩定 pin 1.3**；1.3 官方上架。contributor＝訓練折扣價，機密 repo pin standard。訂閱只綁 CLI 簽入 credential；優先序 env key＞stored key＞browser（**stored PAYG 靜默蓋訂閱**——判別＋硬前提）。
- 額度鐵則：~8 requests≈5h 窗 10％；xhigh 400-step 單 task 可耗盡整窗。**耗盡形態**：`run.terminal.failed` 帶 `429 Subscription quota exhausted…resets at <ISO>`——等 reset 不重試，時間戳直轉 CronCreate 補派；bridge 狀態 `failed-usage` exit 1。effort 兩層（API max／CLI ultra alias）現值見 model-routing skill 對譯表。credential 判別鍵 `mechanism`/`obtained_via`；PII 禁入輸出。

## bridge 機械（muse-plugin-cc；收法見 family 檔）

- setup green gate 一次性 per-workspace（ledger setup.json；主 session 可自主補跑，subagent 禁自跑）。`task --prompt-file` 的 prompt＝任務本文（委派語言禁入→muse-in-muse 鎖死實證）。job 回收 `.muse-bridge/jobs/<id>.jsonl`（terminal 文在 `payload_type=="run.terminal.completed".payload.text）；reconcileStaleRunning 或早標 interrupted——以 jobs.json＋jsonl 為準；wrapper 提前 complete≠job 終局。
- `review` 子命令：預設 scope＝working tree；**0.2.5 實旗標**＝`--base <ref>`（git diff base）／`--json`／`--steps`／`--effort`／`--model`——**無 `--schema`**（model-routing skill flag 表原 `--schema verdict` 是 drift——已修正對齊，7ad42c0）；`task` 亦**無 `--disable-write`**（read-only 靠工單紅線承載）——review 本質是 diff 審查，**文件審查（EP 等）走 `task`＋紅線**；`--prompt-file` 不支援、無檔案級 scope（維度由 GLM 補）；severity enum 誤產 `"info"`→`review-fail` 但內容可判讀（非真失敗勿重跑）；`review --help` 炸（usage 文字在 script 內 "Flags for review:" 段，python find 抽取）。template 安裝形 0.2.4 已修。**輪詢陷阱**：`show --json` status 巢在 `job.` 下；只對 running 續等＋拍數上限；先實測一次結構再寫解析。wait 零測試覆蓋（09-05 L4 行為驗收通過，補測試待 plugin repo session）。
- 沙箱寫不進 home——部署屬主 session；工單 deploy 驗收預期回報 gate 計算值。原生工具＝bash/read_file/search；`muse export --session` 可提工具統計。**三層知識**：機器層（全 run）／workspace 慣例（trusted only）／memory（interactive only）——headless 只有機器層；對照實驗必 `--model` pin。Cron* 工具 muse 碰不到——排程手術主 session 親做。exec 留 `.project-snapshot.json` 副產物（gitignore 或刪）。

## Session 記錄讀取

位置 `~/.local/share/muse/sessions/YYYY/MM/DD/<id>/session.jsonl`（活度看 mtime；runtime index 另處）。三形態：頂層 `payload_type`／`retained_frame.children[].record_json`（遞迴 harvest）／`omitted_record`。抽對話：user＝`refill_blocks[]` text；assistant＝runtime.session。17MB+ 禁直讀（腳本轉 md 再分段）。

## 其他

- Skills 零改動相容（`~/.agents/skills` symlink 活同步）；frontmatter 收尾 `---` 自成一線（見 [[frontmatter-triggers-on-yaml-trap]]）。workflows：aarch64 缺引擎——多 agent 用 subagent fanout 替代。`node --test tests/` 裸目錄炸——指檔或裸 `node --test`。
