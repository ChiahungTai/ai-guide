# S5 receipt：monitor 收編與排程（五面 governance health）

> 執行日：2026-09-17。分支 `air-116`（S4 commit `1758dd9` 之上）。
> 結論：**AC-5.1～5.5 全 PASS**；AIR-100 S-E muse approve monitor 吸收收編完成，
> 五面 health 上線（launchd 在線、實跑綠、冪等）。

## 對帳（AC-5.1——已落地形態 vs EP 期望態）

| 腿 | 對帳前（AIR-100 S-E 形態） | 對帳後（本 EP 期望態） | 處置 |
|---|---|---|---|
| muse approve | `scripts/muse_approve_monitor.py` evaluate()（fail-closed） | 語義由 `install.py probe_muse`（S3）＋`check_muse_face`（S4）承接——同一實作非兩套 | **吸收**：舊 script＋`tests/test_muse_approve_monitor.py` 刪除；non-dict payload 腿補回 `probe_muse`（absorption 時發現的缺口） |
| 五面 health | 無（僅 muse 腿） | `scripts/governance_health_monitor.py`——子進程消費 `install.py --verify --surface all`＋`--check --surface all`（F-4：uv run），輸出透傳落 log，任一非零＝告警行＋exit 1（fail-loud） | **新建（薄編排層，零判定重寫）** |
| plist 排程 | `deploy/muse-approve-monitor.plist`／label `com.ai-guide.muse-approve-monitor` | `deploy/governance-health-monitor.plist`／label `com.ai-guide.governance-health-monitor`（git mv＋改 ProgramArguments/log 路徑/PATH） | **改名收編**＋`--surface monitor` install/uninstall 映射（manifest `[surfaces.monitor]`） |
| 告警消費 | log-only（Q8 預設 (a)） | 同（延續） | 無 delta |

五面 health 腿清單 vs manifest probes 對帳：verify＝claude/zcode/muse/codex 四 probe（manifest `[probes]` 全量）＋check＝rules/skills/hooks/agents/memory 五面（AC-4.1 同源）——monitor log 逐行可見（AC-5.4 實證）。

## AC 逐項

- **AC-5.1**：對帳表如上（本檔即 receipt）。
- **AC-5.2**：直跑 `scripts/governance_health_monitor.py` → **EXIT=0**，verify 四 probe PASS（含 codex L2 五 handlers Trusted、L3 canary byte-unchanged）＋check 五面綠＋`[governance-health] PASS` 尾行。
- **AC-5.3（TC-7）**：單元測試 5 支（`tests/test_governance_health_monitor.py`）——verify FAIL／check FAIL／雙 FAIL／timeout → 告警行＋exit 1（fail-loud）；PASS → exit 0。
- **AC-5.4**：`launchctl start com.ai-guide.governance-health-monitor` → log（`~/.mosaic/logs/ops/launchagent-ai-guide-governance-health.log`）出現 `[verify:claude|zcode|muse|codex]`＋`[check] 五面 parity 綠`＋`[governance-health] PASS`——**五面腿實際執行，非版本守衛拒絕**（斷言 rg 命中＋無「需要 Python 3.11」字樣）。
- **AC-5.5**：`rg -ln "muse_approve_monitor" scripts/ deploy/ AGENTS.md skills/ governance/` → **零命中**；label `muse-approve-monitor` 同掃零命中（README/install.py 指針已改「AIR-100 S-E monitor evaluate()（已吸收）」措辭）。launchd 最終態＝`governance-health`＋`backlog-cleanup`＋`entitlements-probe` 三 label，舊 label 不在。

## 收編途中三事故（全結構性修復）

1. **launchd PATH 無 codex → probe_codex 裸 crash**：版本診斷行 `codex --version` 未先 `which` 檢查（fixture 有、診斷行漏）→ `FileNotFoundError` traceback。修：`has_cli` 守衛——CLI 缺席時 L1/L2（config/state 檔面）照常報告＋L3 標 GUARD 不 crash；回歸測試 `test_probe_codex_cli_absent_guard_with_l1`。附帶：plist PATH 補 `~/.npm-global/bin`（codex 實際安裝處）。
2. **XML 註解含 `--`（flag 字面）→ plist 嚴格解析拒讀**：首次安裝走「created」路徑未驗證源內容，帶病寫入（launchd 寬容收載、plistlib 拒讀）。修：註解去雙連字號（語法限制記入註解）＋**create 路徑補源內容 `plistlib` 驗證**（帶病寫入 chokepoint 堵死）＋R7 fail-loud 擋下後續帶病 reload（防線有效實證）。
3. **stale-loaded 分支誤報 noop**：`created`＋launchd 仍載舊版 → 舊邏輯落入 noop 不重載。修：`outcome in (written, created)` 且已載入 → bootout＋bootstrap 重載。

附帶實證：fail-loud（R7 malformed 拒寫）在帶病安裝副本上正確攔截 reload——「malformed 絕不覆寫」由結構保證非紀律；恢復＝機械刪除本 session 自建的事故殘留（owner 自證）＋乾淨重裝。

## 最终態

- launchd：`com.ai-guide.governance-health-monitor` 載入、exit 0、日頻（StartInterval 86400）。
- 冪等：`--surface monitor` 重跑 → `noop（版控源與安裝副本等值且已載入）`。
- uninstall 契約：`--uninstall --surface monitor`＝bootout＋刪安裝副本（版控源/script 留 repo——dead but harmless；live uninstall round-trip 歸 AC-2.5 全段驗證）。
