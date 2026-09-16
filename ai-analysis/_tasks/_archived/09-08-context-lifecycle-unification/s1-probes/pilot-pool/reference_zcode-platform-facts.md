---
name: zcode-platform-facts
description: ZCode 平台事實：compact 恢復、跨 session 參考、db.sqlite 遙測、ENOENT 故障、內建 memory 拓撲
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_75794c58-c131-4e06-8e87-b809c2b15d0d
---

ZCode 平台實測事實集（09-08 蒸餾：流程已轉正 skill 者壓成指針，留配方＋陷阱＋判別法）。

> merged_from: reference_zcode-compact-recovery, reference_zcode-cross-session-reference, reference_zcode-session-agent-communication, reference_zcode-telemetry-db (2026-09-03)

### compact 恢復（活路＝compact-prep skill＋db.sqlite SQL；程式觸發全死路）

- 流程三動作住 `skills/compact-prep/SKILL.md`（外部化檔＋新鮮度檢查＋compact 後讀檔）；re-injection 快照是當時內容非現況——與摘要矛盾重讀裁決。
- 死路（實測）：Skill 調 compact、`SessionStart(compact)` hook（零派發，feedback#357）、桌面 CUA——皆不通；CC 端 compact matcher 是官方食譜（`hooks/compact-tail-inject.py` 已 port，CC live 未驗）。
- **raw SQL 恢復**：`~/.zcode/cli/db/db.sqlite` `part` 表留 compact 前全部對話——user turn 錨字串定時間窗→LIKE 取 `$.text` 全文；排除 `session_id LIKE 'sess_subagent_%'`；`part.sequence` per-message、全域時序用 `message.sequence`。ReadSessionContext 是再摘要（會誤報/超時），verbatim 直查 sqlite。工具陷阱：sqlite3 CLI 無聲空輸出——python＋`file:...?mode=ro` uri。compact-lab 實證：z.ai 無 server-side compaction；usage 真實 prompt 看 `cache_read_input_tokens`；GLM 中英 ≈1.8 chars/token；**摘要指示 verbatim 保留無效——結構性保留（落檔）勝指示**。

相關：[[zcode-hooks-porting]]、[[agents-registry-split-design]]、[[relay-claims-verify-current-state]]

### 跨 session 參考與通訊

- ZCode 無 session 互發訊息機制——協作靠檔案系統（EP 自足/STATE/MEMORY）＋cron/at 接力。ReadSessionContext＝跨 session 唯讀單向（`relevant` 對大 session 300s 逾時；`handoff` 策略可用）；SendMessage＝同主 session 派生 agent 間（subagent 不可再派）；side chat 回覆不回流——回流靠 user 手貼/ReadSessionContext/直查 DB。resume 引用他 session 注入 system_reminder。fork＝分岔語義（parent memory 照常可讀）。
- **直讀 DB 三層**：`session`（id/title/time_archived）→`message`（role/modelID/cost/semantics）→`part`（正文）。最新 session：`time_archived IS NULL ORDER BY time_updated DESC`。**真人判別**：`role=user` 且無 `synthetic` 欄位。tail 配方住 `skills/zcode-session-query/`。**活躍 peek 三坑**：id 存 DB 帶 `sess_` 前綴；tail 按 `time_created` 排（sequence 會被 reasoning 洗掉）；`step-finish reason='stop'`＝turn 結束、`tool-calls`＝還在跑。Read 局部即註冊 read-state——補段換 offset/limit（09-07 實證），真重載才退 cat。

相關：[[at-skill-zcode-cron-gaps]]、[[project_session-topology-single-writer]]、[[feedback_subagent-background-spawn]]

### 遙測 DB（request 級配方集）

- **路徑**：實體 `~/.zcode/cli/db/db.sqlite`；同層 `db.sqlite` 0-byte 殘檔是陷阱。**modelID 歸因**：`model_usage` 濾 `agent` 非空→`model_id` 驗 pin、`variant`＝effective effort（sticky user 層級在場記 user 值非定義值——#339/#306 家族）。**大小寫＝來源**：大寫＝session runtime（手動切換）、小寫＝registry pin；帶 provider 前綴（`ZCode/`、`Grok/`）亦＝runtime 形態——跨 provider 漂移實證（code-reviewer 曾跑 Grok/grok-4.6）。
- **關鍵表**：`model_usage`（request：session/agent/model/tokens/retry/status/ms epoch）／`turn_usage`／`tool_usage`（主 session 濾 `parent_id IS NULL`；與 model_usage JOIN 會 cross-product——分開聚合）／`part`（Skill 參數/Edits 可行為分析，帶 time_created 才有時序）／`session`（parent NULL＝主）／`local_setting`（user 級設定實體——reasoningLevel 存放處：`scope='user', namespace='model', key='reasoningLevel'`；改它對運行中 app 無效，見內建模型面 flip 實驗）。另 `rollout/model-io-sess_*.jsonl`、`log/zcode-*.jsonl`；DB WAL 活寫入＝當下快照。`computed_total_tokens=input+output` 精確；`input` 已含 cache_read→fresh＝input−cache_read。
- **查詢陷阱四則**：part 全表 LIKE 必先 `json_extract($.type)='tool'`（實測 7,345 假命中）；對話 mining 必濾 `task_type='interactive'`（side_chat 複製 parent user 訊息 3x 通膨＋疑問句假陽性 ~17％）；聚合 key 禁截短 id（`sess_subagent_agent_` 前綴撞 key）；Skill 歸因暈染——per-skill 成本先抽窗口實際命令構成。skill 滲透稽核／spawn 分析配方見 skills/corrections-weekly、standup scripts（JOIN 鍵 `message.session_id`、`session.task_type='subagent_child'`）。
- **清理**：子表 FK cascade 須 `PRAGMA foreign_keys=ON`；`input_history` 無 FK 手清；檔案端按 session id（`cli/exec|artifacts|agents/sess_*`、`rollout/`；`claude-import-*` 前綴另算）；app 開著禁 VACUUM。腳本 `.agent-tmp/zcode_*.py` 可重用。
- **診斷錨**：慢啟動 25s＝`setting.json.lock` 殘鎖（刪即好；看 cli/log durationMs＋v2 RPC log）；subagent 掛死看 metadata.json＋child parts＋`model.sdk.stream.failed`（harness 無 client 逾時——parts 0 不可靠，用 completed 事件判）；flash 派工：精簡合約＋禁 5 路併發＋首步即 tool call；registry 新定義須新 session（快照凍結）；**改名同受快照管轄（09-08 實證）**——session 內改名的 agent（impl-flash→impl-lite）新名 spawn 不到（"not found"），快照舊名仍可 spawn 且＝同一支定義檔同 pin（語義等價的 workaround）；file symlink 可載入（09-06 新 chat 實證，判決載體一律新 chat）；subagent cwd＝session 工作目錄（相對路徑 cwd 錨定）。

### 內建模型面（09-08；源＝ref-docs/harness/zcode/cn/docs/configuration.md 鏡像，數字以 provider 為準）

內建＝**GLM-5.3＋GLM-5.3-Flash 兩款**（編程套餐登入即用，300萬/500萬 token/日量級）；**flash 是多模款**（截圖理解/看圖分析——vision tier 選它的原因，能力軸非強度軸）；GLM-5.3 thoughtLevel low/high/max；模型 ID 參與能力匹配但非唯一依據（同模型經不同供應商/協議接入判讀可變——能力宣稱前先確認接入面）。registry pin 字串逐字到 wire——旗艦 id `glm-5.3` 首例已實證（AIR-43 S3 遙測：`zcode-code-reviewer` 小寫 `glm-5.3` 命中；對照主 session runtime 大寫 `GLM-5.3`/`GLM-5.3-Flash`——大小寫＝來源判別錨）。variant 欄觀察值 `max`（thoughtLevel 定義值 `high` 未達 wire、全 agent 一致——sticky 但書，RA-2 數據點；flip 實驗 09-08：直寫 local_setting DB 改 level=low 後同 session spawn，variant 仍 max＝session 快取值——定義值 silent no-op 確認＋spawn 不逐次重讀 DB（app 快取 session 起始值）；UI 動態改是否傳播未測，user UI 級實驗殘餘）。user reasoningLevel 存放處＝db.sqlite `local_setting` 表（row：scope='user'、scope_id='default'、namespace='model'、key='reasoningLevel'，value JSON `{"level":"max"}`）——config.json 只有 mcp/plugins/hooks 三鍵，user 設定不走該檔。

### Bash spawn ENOENT（session 級故障，修復＝開新 session）

`spawn /bin/zsh ENOENT` 連 5+ 次＝持久 cwd 被刪（曾 cd 的 scratch 目錄事後 rm -rf）——Node spawn 帶入不存在 cwd。subagent 同死（代跑非出路）；Read/Edit/MCP 不走 spawn 照常用；恢復探針 `echo ok`（session 內未見自癒）；預防＝刪目錄前 cd 回專案根；pending 動作標阻斷回報不硬繞。

### Memory 內建（per-project 隔離——cross-harness symlink 地基）

原生路徑 `~/.zcode/cli/memories/projects/<名-hash16>/memory/`（v3.6.4+、預設關、只對新 session 生效）；**純 markdown 檔案制，無 sqlite backing**——查詢靠 rg/grep，diff/version-friendly。記四類：偏好／糾正／目標約束／外部參考；不記 code 結構/git/instruction 已有物；無管理頁、索引截斷上線。共用池＝每池 `memory` symlink→Claude 池（[[memory-cc-alignment-diagnosis-0905]] symlink 段）。**單池三視圖**：同 repo 多 worktree 各有目錄但**同一 inode**——readlink 各回自身≠分池，inode 比對才是判據；整理只做一遍（派 agent 整理把此事實燒進 prompt）。

**召回機制（09-08 AIR-45 S0 db 鑑識定案）**：**無 desc-matching 動態召回**——memory 入 context 只有①Read tool call（agent 主動）②compaction 重放（tool result 重放為 synthetic system_reminder）；17,7xx 條 user message kind 分佈無 memory-recall 類、210 條 system_reminder 全是 compaction 鏈/Read 警告/fork 通知。runtime 注入＝synthetic user messages 管道（todo_reminder 5,795/background_notification 3,209 皆持久化於 message 表）——動態召回的機制座位存在、memory 未接上（想做召回可循此形態）。request 組裝期注入（agentsMd 靜態 bundle）不落 db——db 鑑識排除面限「被持久化的」。

相關：[[cr-live-faces-roadmap]]、[[memory-cc-alignment-diagnosis-0905]]、[[memory-index-load-truncation]]
