# AIR-174 post-build review ledger

> identity: baseline=7016266e61afc050062e1254ccd1ddcd7c52e33d · reviewed=7016266e61afc050062e1254ccd1ddcd7c52e33d · uncommitted=tracked bef1e3851298b9903b1478fdc8a8cfadeb2c4070597748ff6b953dae32fbf6f6 + untracked ai-analysis/_tasks/09-23-hook-python312-runtime/ep.md@7b8097f3d58cae196a229a2af7d6fc4b2e348605f3e3ca1153e728b531e6f300 · scope=AIR-174 hook runtime ownership across governance installer, CC/ZCode/Codex registrations, tracked Python hooks, compact-restore retirement, runtime/rollback tests and docs; exclude pre-existing duplicate hook groups and live-config drift · review_profile=boundary review-engine@2fd72abfbcb0 · coverage=fresh cross-family completed via Muse job-mudvwq8f-p5izv4; intent/correctness cross-family completed via Codex job-mudvyikd-b3f01c; host validation evidence focused 104 passed + affected hooks 115 passed + full suite 1871 passed/1 skipped + Python 3.9 grammar scan clean + hooks verify PASS; CR structural evidence unavailable because dirty-WT freshness preflight lacked .code-reality/scip/index.scip · writer=post-build main session

## Muse fresh review Findings — air-174

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|----|--------|---------|------|------|--------|------|------|
| M1 | 🟡 important | governance/install.py:1374 | `probe_pipe_payload()` 內 `resolve_hook_python()` 的 `GovernanceError` 不在目前 helper 的 timeout catch 內；Muse 認為 resolver 缺失會破壞 helper tuple contract，並把 CLI `--verify` 描述為 crash。此 finding 與 top-level `main()` 的 `GovernanceError` catch 存在待 judge 裁決的語義衝突。 | 區分 helper contract 與 CLI contract；若 helper 必須穩定回 tuple，將 resolver failure 映射為 FAIL/GUARD，否則拒絕把 top-level clean fail 稱為 crash。 | `uv run pytest -q tests/test_governance_verify.py` | verified | ✅ |
| M2 | 🟡 important | tests/test_governance_check.py:24 | 現有測試驗單一 render/resolver，但沒有掃 canonical CC/ZCode/Codex registration templates，無法防未來重新出現 bare `python3` 或漏用 `{{HOOK_PYTHON}}`。 | 加 template-wide regression，從 canonical registration source 枚舉並驗所有 Python hook command 使用 runtime token、render 後 token 消失。 | `uv run pytest -q tests/test_governance_check.py` | verified | ✅ |
| M3 | 🟡 important | governance/install.py:1053 | Muse 認為 `--check` 內 render 觸發 resolver failure 時會 traceback/crash，而不是既有 drift/fail-loud output；但 top-level `main()` 會 catch `GovernanceError`，需 judge 以 CLI 實際 contract 裁決。 | 最小實測 missing-resolver CLI 行為；只有在真 traceback 或違反 exit/output contract 時才改 check path。 | `uv run pytest -q tests/test_governance_check.py` | verified | ✅ |
| M4 | 🔵 suggestion | governance/install.py:122 | `_HOOK_PYTHON_CACHE` 命中後不重驗 path exists/X_OK；Muse 認為長生命週期 process 中 interpreter 被移除/升級會留下 stale cache。 | 核對 installer CLI process lifetime 與 uv minor alias symlink；只有實際存在同 process runtime mutation 風險才重驗 cache。 | `uv run pytest -q tests/test_governance_check.py::test_resolve_hook_python_uses_installed_managed_312` | closed | ❌ |
| M5 | 🟡 important | backlog/tasks/air-174 - 治理-hooks-統一到-Python-3.12-runtime.md:30 | Muse 指出 AC3-AC5 在審查當時尚未附 runtime equivalence、dry-run/check/verify 與 post-build review/judge receipt。這是 post-build 當時的 process state，不一定是 implementation defect。 | post-build 收斂後把實際 validation/review/deployment receipt 寫回 card；不要用此 finding 驅動產品碼修改。 | `uv run python skills/post-build/scripts/review_ledger.py parse .review/air-174.md` | verified | ✅ |

## Codex intent/correctness review Findings — air-174

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|----|--------|---------|------|------|--------|------|------|
| C1 | 🟡 important | governance/install.py:700 | `--uninstall --surface hooks` 會先 runtime-resolved `render()` canonical template；若 uv/managed 3.12 已消失，rollback 在移除 package-owned registrations 前就 fail。Removal identity 只需要 matcher + hook script identity，不需要 interpreter。 | 將 install/check/verify 的 runtime render 與 uninstall identity render 分離；uninstall 不要求 `resolve_hook_python()`，補 CC/ZCode/Codex resolver-unavailable uninstall regression。 | `uv run pytest -q tests/test_governance_contract.py::test_hooks_uninstall_does_not_require_hook_python` | verified | ✅ |
| C2 | 🟡 important | governance/registrations/cc.json:25 | CC/Codex 把 resolved interpreter 與 repo hook path 拼成未 quote command string。Claude mirror 明載無 `args` 時走 shell form；合法含空白 path 會拆 argv。ZCode 已是 process+args direct argv。 | CC 若 schema 支援則改 exec form `command` + `args`; Codex 若只有 command string，installer 對 interpreter/script path 做 shell-safe quoting；加 space-path fixture。 | `uv run pytest -q tests/test_governance_check.py::test_rendered_hook_commands_support_space_paths` | verified | ✅ |
| C3 | 🟡 important | tests/test_hooks.py:137 | TC4 的「新 runtime」entrypoint matrix 仍用 `uv run python`，既不等於 deployed absolute 3.12 path，也未 pin 3.12；delegated sandbox 的 44 failures 是 uv cache 權限問題，反而證明此 oracle 引入已排除的 uv runtime dependency。 | pytest 可由 `uv run pytest` 啟動，但 hook subprocess 新腿直接使用 `resolve_hook_python()` 的 absolute 3.12；rollback 腿保留 `/usr/bin/python3` 3.9。 | `uv run pytest -q tests/test_hooks.py::test_write_entrypoint_runtime_contract tests/test_hooks.py::test_h4_followup_mode_and_receiver_contract tests/test_compact_tail_inject.py::test_entrypoint_escaped_tail_and_state_stay_bounded` | verified | ✅ |
| C4 | 🟡 important | tests/test_marshal_admission_guard.py:617 | mixed-session contract 是所有 tracked Python hooks 保持 Python 3.9 grammar，但 durable gate 只覆蓋兩個 hook；本次 ad-hoc 全 hooks grammar scan 為 0 failures，現況安全但 regression gate coverage 不完整。 | 從 manifest/registration derive Python hook scripts，單一測試 `ast.parse(..., feature_version=(3, 9))` 全面守住 contract。 | `uv run pytest -q tests/test_governance_check.py::test_all_registered_python_hooks_parse_as_py39` | verified | ✅ |
| C5 | 🔵 suggestion | hooks/AGENTS.md:3 | 已刪除舊 compact-restore manual registration/protocol source，但文件開頭仍寫「獨立註冊見下節」，與後文 canonical ZCode governance template ownership 衝突。 | 改成直接指向 `governance/registrations/zcode.json` 與 installer，移除「獨立註冊」措辭。 | `rg -n "compact-restore-inject" hooks/AGENTS.md skills/compact-prep/SKILL.md governance` | verified | ✅ |
| C6 | 🔵 suggestion | governance/install.py:361 | `merge_json_hooks()` 對 `UserPromptSubmit` 的 external group preservation 依 source inspection 看正確，但沒有 dedicated regression test 固化此次 manual→generic installer 邊界遷移最關鍵的 coexistence contract。 | 加 ZCode round-trip fixture：external group → install 保留且新增 compact group → uninstall 只移 compact group。 | `uv run pytest -q tests/test_governance_contract.py -k UserPromptSubmit` | verified | ✅ |

### Evidence notes

- Muse review job: `job-mudvwq8f-p5izv4` — completed, exit 0, verdict `needs-attention`.
- Codex intent/correctness review job: `job-mudvyikd-b3f01c` — completed, exit 0.
- Codex delegated sandbox broader test run had 44 `uv-run-python` failures caused by uv cache initialization permission failure; they are environment evidence relevant to C3, not implementation regressions.
- Live `--check --surface hooks` reports 22 expected drifts because this authoring WT has not deployed live configs; duplicate CC/ZCode block-python groups are pre-existing and excluded from AIR-174 scope.

## Final combined followup

Muse Arbiter job-mudz0hdo-qfpru8: APPROVE, current source verified; M1-M3/C1-C6 closed, M4 rejection holds, CC command+args parity regression closed. M5 remains main-owned metadata finalization. Combined full suite after static cleanup: 2033 passed / 2 intentional PRE_COMMIT skips. No live install or host-level acceptance claimed. Native final followup pending.

## Final integration finding

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|----|--------|------|------|------|------|------|------|
| IR1 | 🔴 critical | governance/install.py:227,563 | Codex quote 後 script identity 為空；含空白 repo 的 package Stop group 可覆寫 external Stop，卸載殘留四個 group | install/check/uninstall 從 decoded command argv 辨識相同 ownership，uninstall 仍不解析 interpreter | space/quote roots + external same-event/matcher install/remove roundtrip | verified | ✅ |

IR1 source: native Lagrange final combined review, confirmed in-memory counterexample. Muse prior APPROVE superseded for C1/C2; mandatory fix and both followups before landing.

## IR2 followup

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|----|--------|------|------|------|------|------|------|
| IR2 | 🟡 important | governance/install.py:571 | shlex.split comments=False 將合法 shell 註解中的單引號誤判成未閉合，引發外部 hook 阻斷所有操作 | shell comment semantics + quoted hash path 保全 | external comment install/check/resolver-free uninstall | verified | ✅ |

## Final settlement

All actionable findings closed. M4 remains rejected per Muse Arbiter. IR1 and IR2 verified by independent counterexamples and regression tests; fresh Muse IR2 job-mudzulxa-e1dpd1 APPROVE at exact completion.json hashes. M5 complete: card Done with five checked AC, as-built diagram, historical primary notes preserved and honest pending deployment. Full 2083 passed/2 intentional skips; post-build receipt applies to source-final-sha256.json. Earlier header/source identities and pending notes are historical.

Receipt: classification=boundary / review=native fresh+intent, Muse external+Arbiter, fresh Muse IR2 final APPROVE (job-mudzulxa-e1dpd1); main judge adopts closure / session-freshness=fresh (source hashes verified) / deployment-surfaces=pending (live configs and bundles not deployed).
