# S4 receipt：drift gate（--check 五面 parity）

> 執行日：2026-09-17。分支 `air-116`（S3 commit `56a7980` 之上）。
> 結論：**AC-4.1～4.6 全 PASS**；`--check` stub 轉正。

## 實作落點

| 件 | 位置 |
|---|---|
| JSON 面（cc/zcode） | `check_json_face`——模板條目 vs live 套件條目語義 diff（缺／多／內容差，F-5 窄鍵＝`_pkg_scripts`）＋`enabled` 對照＋**symlink 健康腿**（P0-3：`target_is_symlink` 且普通檔＝斷鏈形 drift） |
| codex 面 | `check_codex_face`——註冊在場＋group text 逐行等值＋**trust Modified 獨立 class**（state key 在場僅供分類——Q4 紅線：非驗收契約，drift 兩態都成立）＋mixed-rep 掃描（codex ⑦） |
| muse 面 | `check_muse_face`——在冊＋`source.path` canonical＋approve 態（複用 `probe_muse`，S3/S4 共用判定）＋**R6 source↔cache 腿**（逐檔 byte 比較，不知 codex/muse hash 公式也能機械偵測 stale cache） |
| rules 面 | `check_rules_face`——唯讀 import `deploy_agents.expected_bundle_for()`（:106，handoff 指定介面）比對部署檔 bytes，零重造 |
| agents 面 | `check_agents_face`——子進程串接 `sync_agents.py --check` 退出碼，輸出透傳 |
| skills 面 | `check_skills_face`——母鏈在場＋readlink 等值（指錯＝fail-loud 不自動改） |
| 單元測試 | `tests/test_governance_check.py`（21 tests：缺/多/內容差/enabled/symlink/malformed/缺席＋codex Modified/缺 group/mixed-rep＋muse R6 三態＋rules/skills＋AC-4.6） |

## AC 逐項

### AC-4.1（Existence）PASS
- `rg -n "def check|semantic_diff|trustStatus|hooks.json" governance/install.py` → 命中（`def check_*` ×7、`trustStatus=Modified` drift 措辭、`hooks.json` mixed-rep 掃描）。
- live 乾淨態：`--check --surface all` → `[check] 五面 parity 綠（唯讀）`、**EXIT=0**。

### AC-4.2（Invocation——live mutation＋復原）PASS
- 刪 CC `settings.json` 的 `PreToolUse` Edit|Write group（block-memory-index-write）→ `--check --surface hooks` **EXIT=1**＋drift 逐字命中：`- [cc] 缺條目 PreToolUse/['block-memory-index-write.py']`。
- 復原（backup cp 回）→ shasum 逐字相等（`baf2bf76df64…` 前後一致）→ check EXIT=0。
- 附帶實證：mutation 腳本以 heredoc 寫入被 ZCode `block-python-file-write.py` 即時攔——治理閘在 authoring session 自己身上生效（改走 Write 工具落 `.agent-tmp/` 腳本）。

### AC-4.3（muse／規則面 negative）PASS（mock——真機不動 approve 態）
- `tests/test_governance_check.py`：非在冊 → drift「不在冊」；source.path 非 canonical → drift；R6 cache stale（內容差/cache 多檔）→ drift 兩行（update＋re-approve 指引）。

### AC-4.4（codex trust class，TC-10）PASS（fixture）
- 內容變（timeout 10→11）＋state key 在場 → drift `trustStatus=Modified（內容已變，trust 針對舊內容）——需 user 再 approve`（獨立措辭非一般 drift）。
- 內容變無 state → 一般「內容差」（不誤報 Modified）。
- `~/.codex/hooks.json` copy 在場 → drift `mixed-rep：…（同 layer 混載＝雙 fire）`。

### AC-4.5（wrap 面串接）PASS（live）
- 暫時弄髒 `agents/zcode/impl-lite.md`（生成檔）→ `sync_agents --check` rc=1 → `--check --surface agents` **EXIT=1**＋drift `sync_agents --check 非零（rc=1，輸出見上）`＋工具自身輸出逐行透傳。
- 復原 → byte-equal → EXIT=0。

### AC-4.6（防 dead 檢查／缺席容錯）PASS
- negative AC-4.2 即防恆綠（真 drift 被抓）。
- live config 缺席（fixture tmp targets）→ drift「live config 缺席（新機器？跑 install）」不 crash（`test_cmd_check_missing_configs_exit_drift_not_crash`）。

## 位置 key 語義註記（Q4 紅線合規）

`--check` 使用 `_codex_owned_state_keys()`（predicted positional key）**僅**用於 Modified/內容差的 drift 分類措辭——兩態都是 drift、都要求處置；key 不入期望值契約、不作「已 approve」的驗收依據（approve 態驗收歸 `--verify` L2 診斷＋L3 host-level）。
