# ai-guide governance 套件

> 跨 harness 治理安裝統一套件（AIR-116）：五部署面（rules bundle／skills 分發／hooks 註冊／agents registry／memory governance）的**安裝面單一源**。`manifest.toml`＝唯一期望定義；`install.py`＝唯一安裝入口。

**邊界（首段宣言）**：本套件只收斂「安裝/註冊面」——閘行為本體（`hooks/` scripts、`muse-plugins/memory-governance/`、bundle 內容、`sync_agents.py` 生成邏輯）**零改動**。與既有部署器的關係＝wrap（呼叫封裝、輸出透傳、退出碼串接），不重寫不取代。

**術語紅線**：本套件動詞一律 **install/uninstall**（安裝到 machine-local 消費點）。rules bundle 的「部署」（`scripts/deploy_agents.py`）是另一條線——本套件對它只 wrap 不擁有；文件禁裸用「deploy」指本套件動作。

## 調用

```bash
# 正典形態（Python 地板 3.11+；machine python3=3.9 會被檔頭守衛拒跑）
uv run python governance/install.py --surface {rules,skills,hooks,agents,memory,monitor,all} [--dry-run|--uninstall|--check|--verify]
```

四 flag（`--dry-run`／`--uninstall`／`--check`／`--verify`）**兩兩互斥**，違規組合 exit 2。退出碼：`0` 成功；`1` drift／verify FAIL；`2` 環境守衛（Python 地板／工具缺席／flag 衝突）；`3` 子命令未實裝；`4` 執行錯誤（malformed／lost-update／子進程失敗——plan journal 有線索）。

**投放預設態警示（AIR-126＋AIR-133）**：`install`／`check` 完成輸出結尾主動偵測防護並顯性警示（`[WARN]` 行，只加資訊不改退出碼）：① `core.hooksPath` 未設／非 `.githooks`＝控制面 guard 未啟用（行內附修復指令）；② `--surface all` 完成時 monitor 安裝副本缺席＝健康警鈴未開（行內附 `--surface monitor` 裝法；all 不含 monitor 屬設計，見 uninstall 節對稱性註記）；③（AIR-133）agents 機器活視圖 symlink 缺席／斷鏈／錯位＝subagent 視圖 fail-open（`--surface agents`／`all` 偵測；行內附 `install --surface skills` 裝法）。dry-run／uninstall 不印。

## 五面對照

| surface | 動作 | 機制 |
|---|---|---|
| `rules` | bundle 部署 | wrap `scripts/deploy_agents.py`（gate／--dry-run 輸出逐行透傳） |
| `skills` | symlink 活視圖 | 建 `~/.agents/skills`、`~/.claude/skills` → repo `skills/`（母鏈）＋四條 home symlink（AIR-110 G2：`~/.claude/CLAUDE.md`→`ai-development-guide.md`、`~/.claude/rules`→`rules/`、`~/.claude/agents`→`agents/claude/`、`~/.zcode/agents`→`agents/zcode/`）；已存在且指對＝零動作；指錯＝fail-loud 不自動改 |
| `hooks` | 四家註冊 | CC `~/.claude/settings.json`（symlink→repo settings.json，resolve 後寫）；ZCode `~/.zcode/cli/config.json`（只動 `hooks` 子樹，mcp/plugins 逐鍵不變）；codex `~/.codex/config.toml`（group 級 append＋註解標記）；muse 部分併 memory 面 |
| `agents` | registry 生成 | wrap `scripts/sync_agents.py`（check 模式串接其 `--check` 退出碼） |
| `memory` | muse plugin＋池拓撲 | `muse plugins install/approve`＋pool 轉移後 `hooks/setup-memory-symlinks.sh --apply` |
| `monitor` | health 排程 | launchd plist（`deploy/` 版控源 `{{REPO}}`/`{{HOME}}` 佔位 → render（parse-modify-dump——只替換已知路徑欄位，註解隨 dump 卸除）→ `~/Library/LaunchAgents/` 裝載；AIR-110 G4 參數化——跨機器零手改；`--check --surface monitor` 比對 live 與 render 期望） |

安全模型（Q3）：compute-then-apply——任何寫入前完成全部分析；plan journal 落 `~/.local/share/ai-guide/governance-plan-journal/`（保留 10 份，中途 kill 可精確 resume／回滾）；備份＝僅變更 target `.bak-*`（`copy2` 保 mtime，每目標保留 3 份）；malformed config（parse 失敗）**絕不覆寫**——fail-loud 報路徑＋錯誤；寫入＝temp＋parse 驗證＋preimage 對比＋`os.replace` 原子替換（codex 併發防護；CC 目標先 `Path.resolve()`——原子寫直打 symlink 路徑會斷鏈，P0-3 實證）。

## approve 分欄（install 後必讀）

| harness | approve 形態 | 你要做的事 |
|---|---|---|
| muse | CLI 自動 | 無（install 流程內含 `muse plugins approve`；update 後需重跑） |
| Claude Code | `/hooks` UI（**user 手動**） | 開 `/hooks` 審查新增條目——無 CLI 替代（P0-5 確認） |
| ZCode | per-session 快照 | 重開 session 生效（舊 session 不生效**非失敗**） |
| codex | trust review（**user 手動**） | 新 session startup review 或 `/hooks` TUI approve——installer **禁代寫 `[hooks.state]`**（無 supported installer API；`--dangerously-bypass-hook-trust` 僅 per-invocation） |

**codex trust/state 語義**：state key 公式＝`"<key_source>:<event>:<group_index>:<handler_index>"`（event snake_case；inline hook 的 key_source＝config 絕對路徑，plugin＝`plugin@market:path`）。**positional key 非 stable identity**——group 插入/刪除/重排即變；本套件所有驗證以「註冊在場＋trust 態診斷＋host-level 測試」為準，禁以 predicted key 當驗收契約。install 直後 trust＝Untrusted 是**預期態非 FAIL**；套件升級改 hook 內容後 trustStatus=Modified，需再 approve（獨立 failure class 非一般 drift）。

**matcher alias 語義（Q9）**：`apply_patch` 一條 matcher 覆蓋 built-in path——`Edit`/`Write` 是 apply_patch 的 **matcher aliases**（內部 tool 暴露 canonical name＋額外 aliases，非「轉換」）。禁再擴第二條 matcher。

## 健康檢查

- 手動：`uv run python governance/install.py --check --surface all`（唯讀五面 parity，drift 即列清單 exit 1）＋`--verify`（probe 面，見下節）。
- 排程：`com.ai-guide.governance-health-monitor` launchd（日頻；AIR-100 S-E muse approve monitor 已收編）——`scripts/governance_health_monitor.py` 消費 install.py `--verify`＋`--check --surface all`，輸出透傳落 log；任一 FAIL 非零 exit＋告警行（fail-loud）。裝載／卸載＝`--surface monitor`；排程面自身 parity＝`--check --surface monitor`（AIR-110 G4：live plist vs render(版控源)，顯式面——`all` 不含）。
- codex mixed representation：`--check` 掃同 semantic hook 是否另有 `~/.codex/hooks.json` copy／重複 inline copy（同 layer 混載＝warning＋雙 fire）。

### `--verify` probe 面（S3）

逐家執行 manifest `[probes]`；exit 0 全 PASS／1 FAIL／2 GUARD（probe 工具缺席）。**fail-closed**：muse inspect 輸出不可判定、payload 非 dict、`runtime_capabilities` 空或缺＝FAIL（「無法證明 trusted」即 FAIL，語義源＝AIR-100 S-E monitor，已吸收為本 probe）。

| probe | 機制 | PASS 判準 |
|---|---|---|
| muse | `muse plugins inspect <id> --json` | `runtime_capabilities[].status` 全部 `trusted_enabled` |
| claude／zcode | 自含 fixture（暫存目錄放空 `_generate_index.py`）合成 deny payload → `hooks/block-memory-index-write.py` | exit 2（①索引手寫攔截分支；不觸任何真實池） |
| codex | 三層（TC-9），見下 | L1 註冊在場＋L3 canary byte-level 未變；L2 如實報告不 gate |

**codex 三層語義**：
- **L1 discovery**：config 面套件 group 註冊在場（identity 對照模板；P0-10——無 live discovery 讀取 API，降級契約＝config 在場性＋state 診斷＋L3）。
- **L2 trust**：`[hooks.state]` 檔面診斷（key 公式見「approve 分欄」節；positional key 僅診斷輸出）。**Untrusted＝install 直後預期態非 FAIL**——印手動 approve 步驟。
- **L3 host-level fixture**：真 `codex exec`（`--skip-git-repo-check --sandbox workspace-write --dangerously-bypass-hook-trust`）對 canary 檔施 apply_patch，斷言 **byte-level 未變**。bypass flag＝per-invocation、不寫 `[hooks.state]`、非模擬 approve——文檔明載用途（已審 hook 源的自動化）。canary 落 `~/.agents/memory/`（家目錄偽池＝deny 根之一），deny 意外失敗的殘留不觸真實治理池；PASS 即清，FAIL 保留作證據。2026 apply_patch deny-bypass bug 先例：script pipe 不可替代本層。

**未測範圍（誠實標記）**：CC/ZCode 的 actual-runtime firing（hook 在真 session 被事件驅動）未由本 probe 涵蓋——AIR-100 deferred 總驗卡承接，`--verify` PASS 輸出尾行明載。codex L2 Trusted 態＝state 檔面診斷＋user `/hooks` 目視，runtime 態以 L3 為準。

## uninstall 影響（拆接線不刪源）

`--uninstall` 移除套件註冊條目、保留他鍵；共享 scripts 留 repo（dead but harmless）；**rules/agents 面不受 uninstall 影響**（wrap 不反部署——bundle 回退走 `rules/AGENTS.md` 部署紀律、registry 走 `sync_agents.py` 自身）；skills 面 symlink 拆除（母鏈＋G2 四條）＝harness 即時讀不到 ai-guide skills／CC 端 guide＋rules／兩家 agents registry 活視圖（session 內已載入者不受影響）；codex `[hooks.state]` orphan 條目 codex 無 GC 路徑——`key＋trusted_hash` 皆相符才精準 cleanup，否則 leave-and-report（隨 session 自然失效）；**positional index 前移警告**：uninstall 本套件 group 後，同-event 後續 group 的既有 trust 會失效（輸出會警告）。

**`--uninstall --surface all` 範圍**（review C-1 定案）：五面反裝＋**muse disable＋monitor unload**（EP rollback 契約「全包含 monitor unload」）。對稱性註記：install-all 不含 monitor 裝載（monitor＝顯式排程面，`--surface monitor` 單獨裝載）——反裝取「清除機器上一切套件痕跡」的保守語義。

## 已知限制

- ZCode 事件子集：無 FileChanged／SessionEnd（harness 限制，不可套件化修補）。
- CC FileChanged 單家（memory-dirty-sensor 僅 CC 註冊）。
- codex trust 無法自動化（見 approve 分欄）；`codex-cli 0.154.0-alpha.6.2` 基準——state key 公式與 trust 行為隨版本可能變，`--verify` 輸出帶版本診斷行。
- P0-2 凍結：CC/ZCode config 序列化＝`json.dumps(indent=2, ensure_ascii=False)`＋尾換行（byte-stability 實證）；非套件鍵區域 byte-equal。

## 面外排程清單（installer 範圍外）

AIR-110 G5 決策：下列 launchd 排程**不入 installer**（monitor 面維持單 plist）——版控源在 `deploy/`（`{{REPO}}`/`{{HOME}}` 佔位，render 語義與 installer 同款），安裝形態＝本清單列出、user 手動裝載：

| Label | 版控源 | 行為 | 手動裝載 |
|---|---|---|---|
| `com.ai-guide.backlog-cleanup` | `deploy/backlog-cleanup.plist` | backlog Done 欄清場批次（每日 23:50；行為主體＝`deploy/scripts/run-backlog-cleanup.sh`） | render 佔位→絕對路徑，`cp` 至 `~/Library/LaunchAgents/com.ai-guide.backlog-cleanup.plist`，`launchctl bootstrap gui/$(id -u) <副本>`；卸載＝`launchctl bootout`＋刪副本 |

## bootstrap（新機器——AIR-110 消費契約）

穩定契約（凍結；變更走 semver——`[package]` version bump＋理由記卡）：

```
uv run python governance/install.py --surface {rules,skills,hooks,agents,memory,monitor,all} [--dry-run|--uninstall|--check|--verify]
退出碼 0=成功 1=drift/verify FAIL 2=環境守衛 3=未實裝
前提：uv 在場、repo 已 clone 本機（先決條件歸 bootstrap 執行器＝AIR-110）
```

**新 clone 預設態＝fail-open（AIR-126 明示）**：安裝前兩道防護預設關閉——控制面 guard（`core.hooksPath` 未設，pre-commit 不 fire；修復＝`git config core.hooksPath .githooks`，per-clone）與健康警鈴（monitor 未裝，drift/fail 無日頻告警）。installer `install`／`check` 完成輸出會以 `[WARN]` 行顯性列出——看到警示不是安裝失敗，是預設態的如實揭露；照行內修復指令／裝法收斂即關閉 fail-open。

新機器逐面檢查清單（「全綠」＝各項 PASS；機器可讀投影＝`manifest.toml [bootstrap_cli]`）：

1. 前提：`uv --version` 在場；repo 在本機路徑。
2. 計畫可讀：`uv run python governance/install.py --surface all --dry-run` 輸出逐面計畫、零寫入。
3. 安裝：`uv run python governance/install.py --surface all`（machine-local config 生成 `.bak-*`）。
4. 手動 approve：CC `/hooks`、codex trust review、ZCode 重開 session（見分欄表）。
5. 驗證：`--verify`——muse PASS、CC/ZCode pipe probe PASS、codex 層一 discovery 在場（trust 態如實報告）。
6. parity：`--check --surface all` 五面綠。逐面 PASS 定義＝manifest 七面（五 surface 中 rules/agents/memory 各含 symlink／拓撲腿）；`git config core.hooksPath` 輸出 `.githooks` 由 bootstrap 清單獨立項驗（repo clone 步驟，非本套件面）——install/check 結尾另有 guard fail-open 顯性警示（AIR-126，偵測非驗證；修復指令見警示行）。
7. 排程：`--surface all` 不含 monitor（顯式排程面）——`--surface monitor` 裝載後 `launchctl start com.ai-guide.governance-health-monitor` 觸發一輪，log 出現五面執行紀錄；`--check --surface monitor` 驗排程面 parity（live plist＝render 期望）。bootstrap 編排器已自動跑此兩步（Phase 2 `all` 成功後接 `--surface monitor`；Phase 4 `--check --surface monitor`）——手動逐面操作時照本清單。
