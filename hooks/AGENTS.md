# hooks/ — 跨 harness Hook 實作腳本

> 本目錄腳本跨 Claude/ZCode 單一來源。hooks 無目錄載入點，**不能 symlink**——兩家 config 以絕對路徑引用：Claude `~/.claude/settings.json`；ZCode 3.7.7+ user-level hooks 註冊範本見 [zcode-registration.json](zcode-registration.json)（範本內容是 `~/.zcode/cli/config.json` `hooks:` 鍵下的子樹值，merge 進去而非整檔覆蓋）。`notification.sh` 不移植。

## zcode-registration.json 維護語義

- **hook 執行環境＝OS 預設 python3（CommandLineTools 3.9）**：ZCode.app（GUI 行程）spawn hooks，PATH 不含 user shell 的 pyenv/uv shim——bare `python3` 解析到 `/usr/bin/python3`；hook 腳本**禁 3.10+ 語法**（repo pyproject 宣告 py312，ruff auto-fix 會把新語法修進 hook——真實案例：UP017 `datetime.UTC` 在 3.9 ImportError，functional 複驗攔下）；改 hook 後必以 bare `python3` 實跑複驗，不可只信 ruff 綠
- **merge 方式**：取 `events` 子樹 merge 進 config 的 `hooks:` 鍵下，`_comment` 鍵不隨行
- **SessionEnd 條目＝範本預載、ZCode 端未 merge**：merge 閘門＝`ref-docs/harness/contracts.md` 的 ZCode hooks 事件表**出現 SessionEnd**（當前無——初測 3.7.7，子集實測見 04 報告 §207）；閘門開後對 zcode hooks 文檔事件表複核一次才 merge 進 config
- **plugin 升級＝路徑維護點**：plugin cache 版號路徑漂移會使範本內 muse/codex 條目的絕對路徑過時——plugin 升級時同步更新路徑
- **grok-build 未安裝**：安裝後照 muse/codex 條目形態補第三條 SessionEnd（其 cache 的 `scripts/session-lifecycle-hook.mjs` 同款）

## Agent 背景 gate（ZCode）

- `zcode_agent_background_gate.py`（PreToolUse，matcher `Agent`——官方語法兼容 `Agent`/`Task` alias）：ZCode Agent tool 原生預設前台，本 gate 把省略或 `run_in_background != true` 的派發以 `allow`＋`updatedInput` 補成背景——同一 call 生效、不拒絕不重派（deny 式才浪費一趟 request）。逃生口＝prompt 前 200 字含 `[fg]` 機械子串（user 確認要前景時用）；fail-open（任何內部錯誤靜默原樣放行）；全事件旁錄 `.agent-tmp/zcode-agent-gate.jsonl`（省略形態取證＋行為審計，post-build 清理自然收走）
- 配套：`rules/tool-discipline.md`「背景執行」＝prompt 層一律明帶 `run_in_background: true`（gate 失效／未註冊機器的 defense-in-depth）；`agents/AGENTS.md`「背景執行」＝agent 定義一律 `background: true`（Claude 端原生強制；ZCode 忽略此欄位，由本 gate 承接）
- 限制：hooks 是 per-session 啟動快照——註冊／改 script 後須新 session 才生效；`updatedInput` 是完整替換物件（原 keys 必須照抄，gate 已處理）
- 實證（2026-09-12）：新 session 省略參數派發 → log `rewrite_from_absent`、主對話零阻塞、agent 以背景完成通知收尾
- `zcode_agent_probe.py` 已刪——取證功能由 gate 的旁錄 log 吸收

## memory sensors（AIR-56，CC-only）

- `memory-write-sensor.py`（PostToolUse，matcher `Edit|Write`）：成功後才記 actor 證據→ `$MEMORY_HOOK_LOG`（預設 `~/.local/share/ai-rules/memory-hook-events.jsonl`）。池判定＝父目錄含 MEMORY.md。
- `memory-dirty-sensor.py`（FileChanged，omitted matcher——匹配所有 watched file）：只記 dirty（watcher≠writer，不指派）。**接線（2026-09-09 已接）**：matcher 種子是 cwd 域字面檔名 watch 不到池外路徑 → 經 `memory-watch-seed.py`（SessionStart 回傳 `watchPaths` 池條目絕對路徑）動態注入 watch list（CC 鏡像 FileChanged 節指引）。live 觸發驗證＝下個 CC session 的 hook log（首次 session start 後生效）；外部寫入後備仍是 hash 腿。
- ZCode hooks 事件子集**含 PostToolUse**（04 報告 §207 實測，初測 3.7.7）→ write-sensor 兩家都已接（ZCode 側 process 形態；payload schema 差異由 sensor 容錯吸收——最壞靜默 no-op fail-safe）。
- `memory-watch-seed.py`（SessionStart，CC-only——ZCode 無 FileChanged 事件故無此需求）：列 ai-rules 記憶池條目（頂層 .md、排除 MEMORY.md 與 `_` 前綴——與 `is_pool_entry` 同過濾）輸出 `hookSpecificOutput.watchPaths`；冪等、池缺場輸出空清單。
- 註冊（user 側 `~/.claude/settings.json` → symlink 至 repo `settings.json`〔gitignored，版控化 local-only〕，merge 非覆蓋；改前 cp .bak）：PostToolUse 條目 command 指本目錄絕對路徑＋matcher `Edit|Write`；FileChanged 條目 omitted matcher；SessionStart 條目＝watch-seed。ZCode 側範本 `zcode-registration.json` 已含 PostToolUse。collector 消費：`attribution --hook-events <log>`（merge 去重＋dirty 旗）。

## 孤兒清理落差（SessionEnd hook 在 ZCode 缺席）

- 三家 external-runtime plugin 都有 SessionEnd 孤兒清理 hook（muse「reconcile stale jobs on start, cancel+kill on end」、codex `terminateProcessTree`、grok 同款）——CC 原生載入；**ZCode 無 SessionEnd 事件（contracts.md 定案）→ plugin 孤兒清理 hook 在 ZCode 缺席**
- muse 側由 bridge `reconcileStaleRunning` ledger 兜底＋post-build 開工背景寫入者盤點涵蓋
- **remediation＝ZCode app 重開（收同生命週期進程；detached 背景進程跑完自然結束、結果照落 ledger）＋`git status` 檢 working tree 半套編輯——實務成本極低（user 2026-09-05 確認），非防護缺口**

## 多機移植（clone 到新機器）

- 程序見 [MULTI-MACHINE.md](MULTI-MACHINE.md)；機械支援＝`setup-memory-symlinks.sh`（dry-run 預設、`.bak` 備份）＋`verify-memory-topology.sh`（只讀驗證）。muse memory 閘＝user-scope plugin `muse-memory-governance`（source home `muse-plugins/memory-governance/`，AIR-79——install/approve 見其 README；plugin 為唯一寫入閘，legacy `.muse/hooks.json` 註冊與 launcher 已隨 cutover 退役，運維見其 README 運維節）。池傳輸（bundle／cp -a）與 cron 重建是手動步。
