# S3 receipt：approve 分欄與 --verify（含 codex discovery 三層驗收）

> 執行日：2026-09-17。分支 `air-116`（S1+S2 commit `8a738f4` 之上）。
> 結論：**AC-3.1～3.5 全 PASS**；`--verify` stub 轉正（install.py）。途中 live 首跑
> 抓到 `codex_trust_diagnostics` 兩個潛伏 bug（該函式 S2 期為死碼，本段首次被驅動）。

## 實作落點

| 件 | 位置 |
|---|---|
| 四家 probe | `governance/install.py`：`probe_muse`／`probe_pipe_payload`／`probe_codex`（L1+L2+L3）／`run_probe`／`cmd_verify` |
| codex 三層 | L1＝`probe_codex` config 面註冊在場（identity 對照）；L2＝`codex_trust_diagnostics`（修復後）；L3＝`codex_host_level_fixture`（真 codex exec＋canary） |
| mixed-rep 掃描 | `codex_mixed_rep_warnings`（verify 報告行非 gate——Q5「--verify 不掃」與 S3「verify 亦報」的衝突調解：報告滿足 TC-10 P10-2「至少一者」，不影響 exit code） |
| 單元測試 | `tests/test_governance_verify.py`（21 tests——AC-3.3 negative 腿＋L2 回歸守衛） |
| README | 「`--verify` probe 面（S3）」節（probe 表＋三層語義＋未測標記）＋退出碼 4 補齊 |

## AC 逐項

### AC-3.1（Existence）PASS

- `rg -c "trusted_enabled|verify|discovery" governance/install.py` → 22 命中。
- `rg -n "approve" governance/README.md` → 分欄表（:31-38）＋state key positional 語義節（:40）＋verify 節（:52）。

### AC-3.2（Invocation——live 實跑）PASS

`uv run python governance/install.py --verify --surface all`，EXIT=0（逐字輸出）：

```
[verify:claude] PASS——合成 payload 被拒（exit 2）
[verify:zcode] PASS——合成 payload 被拒（exit 2）
[verify:muse] PASS——1 capability 全部 trusted_enabled
[verify:codex] PASS——層一註冊在場＋層三 host-level deny 生效
  [diag] codex-cli 0.154.0-alpha.6.2（state key 公式與 trust 行為隨版本可能變）
  [L1] 在場：PreToolUse/Bash ['block-python-c-comment.py', 'block-python-file-write.py']
  [L1] 在場：SessionEnd/ ['stop-notification.sh']
  [L1] 在場：Stop/None ['stop-notification.sh']
  [L1] 在場：PreToolUse/apply_patch ['codex_memory_path_deny.py']
  [L2] diagnostic key=/Users/ctai/.codex/config.toml:pre_tool_use:0:0 matcher='Bash' scripts=[...] → Trusted(state 在場)
  [L2] diagnostic key=/Users/ctai/.codex/config.toml:pre_tool_use:0:1 matcher='Bash' scripts=[...] → Trusted(state 在場)
  [L2] diagnostic key=/Users/ctai/.codex/config.toml:session_end:0:0 matcher='' scripts=['stop-notification.sh'] → Trusted(state 在場)
  [L2] diagnostic key=/Users/ctai/.codex/config.toml:stop:0:0 matcher=None scripts=['stop-notification.sh'] → Trusted(state 在場)
  [L2] diagnostic key=/Users/ctai/.codex/config.toml:pre_tool_use:1:0 matcher='apply_patch' scripts=['codex_memory_path_deny.py'] → Trusted(state 在場)
  [L3] PASS——canary byte-level 未變（codex exec exit 0）
[verify] 全部 PASS（CC/ZCode actual-runtime firing 未測——AIR-100 deferred 總驗卡承接）
```

附：`--verify --surface hooks` scoping 正確（只跑 claude/zcode/codex）；`--verify --surface skills` 印「無 probe 定義（parity 歸 --check）」exit 0；EP AC-3.2 括號「`:1:0` 缺場為活證」過時——本機五條 owned handlers 全 Trusted（P0-1 已記 user 完成 approve）。

### AC-3.3（Behavior negative——mock）PASS

`tests/test_governance_verify.py`：21 passed（`uv run pytest`）。

- muse probe：非 trusted（`trusted_disabled`／`modified`）→ FAIL＋detail 含「re-approve」；`runtime_capabilities` 空／鍵缺／壞 JSON → FAIL（fail-closed）；CLI 缺席 → GUARD。oracle 對標 `scripts/muse_approve_monitor.py evaluate()` 非實作自證。
- pipe probe：真 hook 實跑 PASS；hook 放行場景（mock exit 0）→ FAIL（**防恆綠自我驗證**）；timeout → FAIL；script 缺席 → GUARD。
- mixed-rep：重複 inline group／active `hooks.json` copy → warning；乾淨 config → 無 warning。

### AC-3.4（host-level，TC-9 層三）PASS

- 層三：真 `codex exec --skip-git-repo-check --sandbox workspace-write --dangerously-bypass-hook-trust`（cwd=~/.agents）對 canary（`~/.agents/memory/gov-probe-fixture-<ts>.md`，家目錄偽池）施 apply_patch → **canary byte-level 未變**、probe 自清。deny-bypass bug 先例的 host-level 腿本 EP 內完成。
- 層二：本機 user 已於 AIR-100 完成全部 approve（P0-1 十二條 state 在場為證）——本機以 Trusted 態驗收；新機器場景 installer 印手動步驟（blocked-on-user 語義保留於代碼與 README）。

### AC-3.5（誠實標記）PASS

`rg -c "未測" governance/README.md` → 1 命中（「CC/ZCode actual-runtime firing 未測——AIR-100 deferred 總驗卡承接」）；`--verify` PASS 尾行同文案。

## 途中抓到並修復的 bug（S2 死碼首次被驅動）

| # | bug | 症狀 | 修復 |
|---|-----|------|------|
| 1 | `HANDLER_HEADER` 缺 `re.MULTILINE` | `.findall(unit_text)` 掃多行 group text 時 `^` 只中字串開頭 → handlers 恆 0 → L2 診斷整段消失 | 編譯加 MULTILINE（`match()` 單行用法不受影響）；回歸守衛＝`test_codex_trust_diagnostics_*` 三測 |
| 2 | state key event 段 `event.lower()` | `PreToolUse`→`pretooluse`，真實 state 為 snake_case `pre_tool_use`（P0-1 公式）→ 誤報 Untrusted | `_codex_state_event()`：PascalCase→snake_case；live 重跑五條全 Trusted 與 P0-1 十二條吻合 |

教訓：S2 commit 的 `codex_trust_diagnostics` 從未被驅動（死碼）——死碼的 bug 要到消費者上線才暴露；S3 的 live verify 首跑即是它的第一次 Invocation 層驗證。

## 契約附帶修正

- manifest `[bootstrap_cli.exit_codes]`＋README 補 `"4" = 執行錯誤（malformed／lost-update／子進程失敗——plan journal 有線索）`——S2 已實裝 `EXIT_EXEC=4` 但投影漏列（drift 防範）。
