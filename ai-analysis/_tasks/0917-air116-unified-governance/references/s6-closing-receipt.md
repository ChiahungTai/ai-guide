# S6 receipt：bootstrap 契約＋收尾（AC-2.5 round-trip／AC-6.1～6.4／post-build 補跑）

> 執行日：2026-09-17。分支 `air-116`（S5 commit `4a3b547` 之上）。本段為弧收尾段。

## AC 逐項

### AC-6.1（契約存在性）PASS
- `manifest.toml [bootstrap_cli]`：command／surfaces／flags／exit_codes（0-4）四類鍵在場。
- README bootstrap 節七項清單在場（rg "dry-run|approve|--verify|--check|launchctl" → 24 命中 ≥4）。

### AC-6.2（argv 面 vs manifest 面對帳）PASS
- `CLI_SURFACES`／`CLI_FLAGS` 常數化（install.py）＋`tests/test_governance_contract.py` 四測：surfaces 逐項等值、flags 逐項等值、exit codes 鍵集合＝{0..4} 且對應 EXIT_* 常數、command 形態釘死。

### AC-6.3（模擬 bootstrap——fixture HOME）PASS（附四個新機器 bug 修復）
`.agent-tmp/ac63-fixture-home` 模擬乾淨機器跑七項清單：①uv 在場 ②dry-run 計畫可讀零寫入（EXIT=0）③install ③b 三 config＋雙 symlink 在場 ⑤verify PASS（codex 三層全過）⑥check 五面綠（CC symlink 拓撲腿以鏡像 symlink 補完後綠——拓撲歸 AIR-110，drift 正確報告＝閘有效實證）。muse 面 fixture 無法模擬（muse CLI 於未初始化 HOME 回「plugins not available」）——真機腿歸 AIR-110 bootstrap 驗證。

**fixture 揪出四個真新機器 bug（全修復＋回歸測試）**：
1. **面順序**：rules pointer preflight 需 skills 活視圖——skills symlink 改為先於 rules/agents wrap（`cmd_install_uninstall`）
2. **symlink 父目錄**：`~/.agents` 等不存在 → `mkdir(parents=True)` 補
3. **config 缺席語義**：`read_json_config` 缺席回 `{}` 自空根建（malformed 只指 parse 失敗）；codex 面 `live_text=""`；uninstall 缺席＝leave
4. **config 父目錄**：`apply_text_change` 補 `real.parent.mkdir(parents=True)`

### AC-6.4（AIR-110 對齊）PASS
air-110 卡 `--append-notes`：消費 `governance/install.py` 契約（指針 README bootstrap 節＋`[bootstrap_cli]`）＋blocked-by 依賴成立＋fixture 模擬結果摘要。

## AC-2.5（live uninstall round-trip——定版）PASS

`--uninstall --surface all`（C-1 修正後語義：含 muse disable＋monitor unload）→ 斷言（codex 套件標記零殘留／zcode hooks 鍵消失且 mcp/plugins 保留／cc hooks 全消且 env/permissions 保留／skills 母鏈拆／check exit 1）→ 重裝（`--surface all`＋`--surface monitor`）→ 三 config shasum **逐字回 round-trip 前值**＋skills 母鏈恢復＋check/verify 全綠。腳本＝`.agent-tmp/ac25-roundtrip.sh`。

**round-trip 新發現（muse 順序契約）**：disable 後 `approve` 無 active capabilities 會失敗——install path 改為 **install → enable → approve**（實證 enable 後 caps 回 `trusted_enabled`）。

## post-build 補跑（user 指示；S3-S6 全段一次性）

- **judge 降級記錄**：兩審查腿（audit-test agent／code-reviewer agent）皆獨立 context；judge 由主 session 承接（未另開 judge session——額度考量，顯式記錄）。muse 跨家族外審腿未派（額度）——同記降級。
- **audit-test findings**：1C／4I／7S → 全數採納處置。C1（"Trusted"⊂"Untrusted" substring oracle 失效）、I1（monitor 告警行 passthrough）改釘完整前綴；I2/I3/I4 寫入側補 `tests/test_governance_write_path.py`（merge_codex_text 五態／apply_text_change 安全語義四態／journal round-trip＋prune／symlink 建立冪等對稱）＋check/verify 補腿；S 級全補。修正後 84 tests 綠。
- **code-review findings**：1C／3I／5S＋五條 red lines 全 PASS（①config 面 chokepoint 附但書→I-2 修復補 plan 層斷言）。處置：
  - **C-1**：`--uninstall --surface all` 補 muse-disable＋monitor unload（EP rollback 契約「含 monitor unload」）；README uninstall 節載明 all 範圍與 install-all 不含 monitor 的設計性非對稱
  - **I-1**：codex exec rc≠0 → fail-closed FAIL（canary 未變但無法證明 deny）；日頻 L3 成本（~1 codex exec/日）文件化保留
  - **I-2**：`apply_plan` 入口第二層 `_DRY_RUN` 斷言（涵蓋 symlink/plist 面）
  - **I-3**：blueprint `onboarding.md`／`structure.md` 殘留指針改址
  - **S-1～S-5**：manifest scripts 存在性檢查腿（死鍵活化）／pool_setup_apply_args 消費化／多條目 drift 修復指引修正／probe 雙源對帳（mismatch→GUARD）／bak 檔名加 pid／fixture 空目錄自清／muse probe 測試 which 補丁
- **跨 session 轉交修復**（AIR-118 建卡 session 轉入）：pre-commit 測試閘 fresh-worktree 假敗——`test_matcher_parity` CC settings 缺席改 skip（`live-config-absent` 標記，比照 zcode-live 慣例）＋TEMPLATE 改指 `governance/registrations/zcode.json`（收編三來源斷鏈修復）；`test_check_single_source` parity fixtures 對齊新路徑（8 tests 回綠）
- **docs 鏈**：變更 `.md` 連結完整性檢查（修復 AIR-79 時代既有斷鏈 `hooks/MULTI-MACHINE.md`）；rename 反掃雙零殘留；`check_single_source` 實跑驗證 `zcode_live_parity` 綠；術語紅線檢查通過
- **EP amendment**：TC-6 P6-3（codex pipe payload）→ 三層驗收取代（已記 ep.md amendment 附錄）
- **既有缺陷記錄（非本弧引入，未修）**：`check_single_source` 的 `hook_registration` invariant 看不到 codex 註冊面 → `codex_memory_path_deny.py` 誤報孤兒 CRITICAL（實際已註冊於 codex config＋模板）；跟進＝checker 補 TOML 註冊面支援（另卡候選）。4 條 skill allowlist IMPORTANT 同屬既有（AIR-113 rename 後遺）

## 最終態

- 全套 pytest 788+ passed；governance 五檔 84 tests。
- machine 態：monitor `com.ai-guide.governance-health-monitor` 已載入（round-trip 後重載）；muse plugin `trusted_enabled`；三 live config 與模板 parity 綠。
- `.agent-tmp/` 弧產物（ac25-bak／ac25-roundtrip.sh／ac63-fixture-home／ac63-*.log／ac42 已清）——證據留至結案後清；`matcher-skip-probe` 已清。
