# hooks/ — 跨 harness Hook 實作腳本

> 本目錄擁有共享 hook 腳本的行為與 runtime 契約；`governance/` 擁有已收編的 machine-local 安裝／註冊。harness 不會掃描本目錄載入 hooks，須由註冊逐項引用腳本；已收編來源＝[CC](../governance/registrations/cc.json)、[ZCode](../governance/registrations/zcode.json)、[Codex](../governance/registrations/codex.toml)；compact restore 接線見下節（註冊單一源＝[ZCode governance template](../governance/registrations/zcode.json)，安裝經 `governance/install.py --surface hooks`）。installer 將 `{{REPO}}` 展開為來源 repo 絕對路徑；live 安裝須過落地閘及授權，入口＝`uv run python governance/install.py --surface hooks`，不能從 authoring WT 提前安裝。模板存在不等於 live 已啟用，模板缺項也不代表機器上未註冊；安裝／trust／核對流程見 [governance README](../governance/README.md)。

## 註冊維護與 runtime

- **治理 hook Python runtime**：tracked registrations 以 `{{HOOK_PYTHON}}` 表示 interpreter；`governance/install.py` 在 render／check／verify 時用 uv 解析**已安裝的 managed CPython 3.12**，再把絕對 interpreter path 寫入 live config。hook fire 本身不呼叫 uv、不依賴 user shell PATH／project discovery／uv cache；缺 uv 或缺 managed 3.12 時 installer fail-loud，先 `uv python install 3.12`。mixed-session／rollback 窗期暫時保留 Python 3.9 語法相容 gate，這是 rollback compatibility floor，不是部署 interpreter。開發／pytest 仍走 `uv run python`；修改 Python hook 後用 installer resolver 所得 interpreter 對隔離 fixture 實跑 entrypoint，並保留既有 3.9 parse compatibility test，驗 stdin／stdout／exit 與副作用。
- **註冊寫入**：installer 維護 CC settings 的 hooks、ZCode `~/.zcode/cli/config.json` 的 hooks 子樹與 Codex config 的 inline hooks，保留非本套件設定；備份／preimage／原子寫規則由 governance 擁有。
- **設定載入與 script 執行分開驗**：ZCode 在 session 啟動取得 hook 配置快照，改註冊或啟停 plugin 後須新 session 驗接線；這不能推導「script bytes 也被快照」。既有 process 註冊以 command＋args 執行路徑上的腳本；只改同路徑 source 時先跑 entrypoint，再以事件觸發驗實際載入，沒有證據不得一概要求重開 session。Codex trust 依 governance 流程由 user approve，不由 installer 代寫。
- **接線現況**：ZCode 模板含 PreToolUse／PostToolUse／Stop／UserPromptSubmit；CC 與 Codex 的 SessionEnd 都註冊 `stop-notification.sh`，沒有 external-runtime job cleanup 條目。這些模板使用 repo 腳本，沒有 plugin cache 版號路徑；不可由其他 plugin 的能力推定本套件已接線。

## Agent 背景 gate（ZCode）

- `zcode_agent_background_gate.py`（PreToolUse，matcher `Agent`——官方語法兼容 `Agent`/`Task` alias）：ZCode Agent tool 原生預設前台，本 gate 把省略或 `run_in_background != true` 的派發以 `allow`＋`updatedInput` 補成背景——同一 call 生效、不拒絕不重派（deny 式才浪費一趟 request）。逃生口＝prompt 前 200 字含 `[fg]` 機械子串（user 確認要前景時用）；fail-open（任何內部錯誤靜默原樣放行）；全事件旁錄 `.agent-tmp/zcode-agent-gate.jsonl`（省略形態取證＋行為審計，post-build 清理自然收走）
- 配套：`rules/tool-discipline.md`「背景執行」要求使用 carrier 非阻塞機制；ZCode Agent schema 有 `run_in_background` 時明帶 `true`（gate 失效／未註冊機器的 defense-in-depth）。其他 carrier 不套此 gate；`agents/AGENTS.md` 的 `background: true` 為 Claude 定義欄位，ZCode 忽略，由本 gate 承接。
- 限制：ZCode 註冊改動須新 session 驗證，source 載入另依上節查證；`updatedInput` 是完整替換物件（原 keys 必須照抄，gate 已處理）
- 實證（2026-09-12）：新 session 省略參數派發 → log `rewrite_from_absent`、主對話零阻塞、agent 以背景完成通知收尾
- `zcode_agent_probe.py` 已刪——取證功能由 gate 的旁錄 log 吸收

## marshal admission guard（AIR-135.10，ZCode/CC/codex 三面）

- `marshal_admission_guard.py`（PreToolUse；ZCode/CC matcher `Edit|Write`——`tool_input.file_path`，codex matcher `apply_patch`——patch 標頭抽取 adapter 照 `codex_memory_path_deny.py` 形態、多檔 patch 任一命中即整 call deny）：控制面路徑 × canonical 主樹 → deny＋指路卡 WT——AIR-106 隔離閘從 commit 時點前移到編輯當下。canonical 判定＝git-common-dir→PRIMARY（`scripts/wt-open.sh` 同款拓撲錨，棄 wt-identity 存在性判據）；patterns 單一源＝`.githooks/control-plane-guard.sh --match-path` 子入口（Python 側零複製 regex）；repo self-gate（common dir 比對）防 user-level hook 殺其他 repo 同名路徑；crash fail-open（exit 0＋stderr 診斷）；**無 bypass env**——break-glass＝human 停 registration（本檔「註冊維護與 runtime」及 governance 安裝／trust 流程）
- 覆蓋邊界：Bash redirect／MCP write 不在 hook 面（定位＝Marshal admission guard 非防惡意 sandbox——提高違規成本＋留審計跡，禁宣稱完整 write security boundary）；subagent 寫入不觸發本 hook 家族（同下方 memory sensor 同款 ZCode 實證）——spawned worker 在卡 WT 的寫入（理想形態）本就不經此閘
- rollout：依上節分別驗註冊與 source 載入；CC／ZCode／Codex 接線見各 tracked registration，不以模板存在宣稱 live 已受保護。Muse 側無本 guard 的 registration 模板，coverage 未驗證，啟用前須實測。

## memory sensors（write：CC／ZCode；watch：CC）

- `memory-write-sensor.py`（PostToolUse，matcher `Edit|Write`）：成功後才記 actor 證據→ `$MEMORY_HOOK_LOG`（預設 `~/.local/share/ai-guide/memory-hook-events.jsonl`）。entry attribution＝父目錄含 MEMORY.md 的條目，排除索引與 `_` 前綴；與 log destination 安全判定分開。
- `memory_hook_common.py` 的 log 契約：override 與 default 都須檢查，log／rotation 目的地不得落在含 MEMORY.md 的池、池內索引／generator／子路徑或指向它們的 symlink；沒有安全目的地時不寫 log，不能用未驗證 default 繞過。sensor 是旁錄，不是寫入授權或阻擋閘；缺 log 不證明沒發生寫入。
- `memory-dirty-sensor.py`（FileChanged，omitted matcher——匹配所有 watched file）：只記 dirty（watcher≠writer，不指派）。**接線（2026-09-09 已接）**：matcher 種子是 cwd 域字面檔名 watch 不到池外路徑 → 經 `memory-watch-seed.py`（SessionStart 回傳 `watchPaths` 池條目絕對路徑）動態注入 watch list（CC 鏡像 FileChanged 節指引）。live 觸發驗證＝下個 CC session 的 hook log（首次 session start 後生效）；外部寫入後備仍是 hash 腿。
- ZCode hooks 事件子集**含 PostToolUse**（04 報告 §207 實測，初測 3.7.7）→ write-sensor 兩家都已接（ZCode 側 process 形態；payload schema 差異由 sensor 容錯吸收——最壞靜默 no-op fail-safe）。
- `memory-watch-seed.py`（SessionStart，CC-only——ZCode 無 FileChanged 事件故無此需求）：列 ai-guide 記憶池條目（頂層 .md、排除 MEMORY.md 與 `_` 前綴——與 `is_pool_entry` 同過濾）輸出 `hookSpecificOutput.watchPaths`；冪等、池缺場輸出空清單。
- 註冊由 governance installer 維護；以 tracked CC／ZCode 模板及 live 核對結果為準，不依賴個別機器 settings symlink 形態。Codex 模板未接 sensors，其 memory 寫入限制由 `codex_memory_path_deny.py` 的 apply_patch admission 承接。collector 消費：`attribution --hook-events <log>`（merge 去重＋dirty 旗）。

## Compact 注入邊界

- `compact-tail-inject.py` 接在 CC SessionStart、matcher `compact`，只讀事件提供的 `transcript_path` 與 cwd 的 STATE.md；不猜其他 session 的 transcript。ZCode／Codex 模板未接此注入器。
- 輸出契約：在預算內優先保留最新尾段；單則訊息過長時保留 UTF-8 可解碼尾部並標示截斷，總預算須包含 framing、separator 與 JSON escaping。排除完整上代注入 envelope（一般提及 marker 保留），避免 compact 遞迴膨脹；最終 stdout 仍須是有效且 bounded 的 JSON。錯誤維持 fail-open（stderr 診斷、空 stdout），不能把注入缺席當作原文不存在。
- `compact-restore-inject.py` 是 ZCode UserPromptSubmit 接線：檢查尚未消費的 session checkpoint 並注入 thin pointer，未註冊環境依 [compact-prep](../skills/compact-prep/SKILL.md) fallback。註冊單一源已收編到 [ZCode governance template](../governance/registrations/zcode.json)，安裝／check／verify 走 `governance/install.py --surface hooks`；機器註冊與 live dogfood 分別驗證，不能由 template 在場推定 live 已啟用。

## 背景工作回收邊界

本套件 SessionEnd 的通知 hook 不承擔 external-runtime job 清理。工作回收由派發端持有 collection owner，依 [agent-workflow](../skills/agent-workflow/SKILL.md) 與 [bridge-dispatch](../skills/bridge-dispatch/SKILL.md) 收取 authoritative terminal 狀態及產物；程序重啟或一段時間無輸出不能代替完成／死亡證據。外部 plugin 的 lifecycle 接線由該 plugin 的 registration/runtime 負責，需獨立查證。

## 多機移植（clone 到新機器）

- 程序見 [MULTI-MACHINE.md](MULTI-MACHINE.md)；機械支援＝`setup-memory-symlinks.sh`（dry-run 預設、`.bak` 備份）＋`verify-memory-topology.sh`（只讀驗證）。muse memory 閘＝user-scope plugin `muse-memory-governance`（source home `muse-plugins/memory-governance/`，AIR-79——install/approve 見其 README；plugin 為唯一寫入閘，legacy `.muse/hooks.json` 註冊與 launcher 已隨 cutover 退役，運維見其 README 運維節）。池傳輸（bundle／cp -a）與 cron 重建是手動步。
