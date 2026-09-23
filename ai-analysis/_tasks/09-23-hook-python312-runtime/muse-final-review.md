# Muse combined final followup

Bridge job: job-mudz0hdo-qfpru8; family=muse; model=muse-spark-1.3; effort=xhigh; session=01a0cda6-a41c-7750-a4ab-bd9e762fa141. Read-only reviewer report below; process-pending remarks reflect its review instant. Main settlement and subsequent full-test/precommit evidence are in landing.md.

## ✅ AIR-174 Final Arbiter Receipt — APPROVE

Bounded followup verdict on the combined worktree (migration + 639a479b repair + judge-repair + cc-parity + static cleanup) vs baseline `7016266`. No writes made; CR index absent → source/`rg` fallback disclosed throughout.

### Per-finding closure (verified in current source)

| ID | Status | Current-source evidence |
|----|--------|------------------------|
| M1 | closed | `probe_pipe_payload` catches `GovernanceError` → `GUARD` ([install.py:1707](file)), resolver hoisted before tmpdir; `test_pipe_payload_probe_resolver_failure_is_guard` + `test_cmd_verify_resolver_failure_is_guard_not_crash` present |
| M2 | closed | `test_canonical_registrations_use_hook_python_token` enforces per-harness shape (CC/ZCode exec/process form, Codex `{{HOOK_PYTHON}}` prefix) + no residual token after render |
| M3 | closed | All three check faces catch → drift entries, exit-1 contract kept ([install.py:1275,1341](file)); install/apply still fail-loud; `check_hooks_scripts` site included |
| M4 | rejection holds | Cache still plain early-return ([install.py:144-146](file)); no revalidation added — overturn condition never triggered |
| M5 | process-only, pending main | Card is modified in WT; no code action. Requires only main's receipt write-up (validation/review/deployment notes + as-built diagram, AC4 honest-unprojected) |
| C1 | closed | `render_uninstall()` ([install.py:205](file)) expands only REPO/HOME; both uninstall legs branch on it ([install.py:845,866](file)); `test_hooks_uninstall_does_not_require_hook_python` present |
| C2 | closed | cc.json Python hooks are exec form (`command` + `args`, shell hooks untouched); `render_codex` = shlex.quote + TOML escape ([install.py:221](file)); `test_rendered_hook_commands_support_space_paths` present. TOML-quote parse bug found-and-fixed during GREEN per receipt |
| C3 | closed | Matrix legs are `managed-312` (absolute resolver, skip-with-reason if absent — [test_hooks.py:18](file)) + `system-python` rollback; no `uv run` leg |
| C4 | closed | `test_all_registered_python_hooks_parse_as_py39` derives from manifest scripts + registration refs (covers all 16 `hooks/*.py`, stronger than static-gate's 11-file scan) |
| C5 | closed | `hooks/AGENTS.md:3` + `compact-prep/SKILL.md` both point at canonical `zcode.json` + installer; stale manual-registration files deleted |
| C6 | closed | ZCode UserPromptSubmit round-trip test ([test_governance_contract.py:276](file)): external preserved, compact added/removed only |
| CC-parity follow-up | closed | `_cc_wiring` combines `command`+`args`; RED 3 fail / GREEN 15 pass / file 97 pass per receipt; receipt hashes match WT bytes exactly (see below) — no clobber by concurrent static edits |

### Original-hardening preservation (H1–H4, R1–R5)

- Frozen hashes match repair.md exactly: `block-memory-index-write.py 6945c4d…`, `compact-tail-inject.py 39f6dee2…`. H1/H2/H3 diffs vs baseline are the already-closed repair (generator-aligned parser, full-envelope exclusion) — untouched since.
- Static-cleanup semantic edits spot-checked equivalent: SIM108 collapse in `marshal_admission_guard` (identical fall-through), `%`→f-string (`%s`≡`!s`, `%d`≡`:d`), `check=False` (default no-op), `TypedDict` (runtime plain dict), `TextIO` rename (annotation-only); format receipt shows `ast_equal:true` on all 21 files.
- `rules-reminder`/`python-standards` deltas match the repair doc's Instruction row; no logic change.

### Source hashes (current WT)

```
15457ad9…  skills/scan-project/scripts/check_single_source.py  (= cc-parity receipt)
20d70ca5…  tests/test_check_single_source.py                   (= cc-parity receipt)
664ea15a…  governance/install.py
0a11eb80…  governance/registrations/cc.json
6d9d2639…  governance/registrations/codex.toml
f263f1ef…  governance/registrations/zcode.json
bd28a508…  hooks/AGENTS.md
6945c4d0…  hooks/block-memory-index-write.py                   (= frozen)
39f6dee2…  hooks/compact-tail-inject.py                        (= frozen)
44152955…  hooks/marshal_admission_guard.py
```

### Scope limits / non-blockers

- **Not verified**: live install, live firing, deployed-config parity — no install authorized or performed. Merge activates symlinked rules/hooks source only, not machine registration projection (card AC4 covers the honest-unprojected state).
- **Pending, main-owned**: final full suite + precommit after static cleanup; M5 card receipts; `.review` settlement.
- **New observation (non-blocking)**: `tests/test_watcher_pairing_nag.py` now uses `from datetime import UTC` (3.11+ import-time). Test-only file, test floor is 3.12 — no rollback-contract impact, flagging for awareness only.
- Full suite not re-run here per instructions; relying on recorded GREEN receipts (migration 1880+1, repair 2030+2, cc-parity 97) + source confirmation above.

**Verdict: APPROVE for main merge.** No actionable blockers.


---

## IR1 followup — job-mudzcr27-qegr44

## ✅ AIR-174 IR1 Delta Followup — APPROVE

Supersedes the prior APPROVE for this interaction only; all other legs stand as previously judged (not re-run).

### IR1 / C1 / C2 closure

**Bug mechanism independently confirmed** (in-memory repro, managed 3.12, roots patched to `/virtual/repo space`): old raw-regex identity returned `[]` for the shell-quoted owned Stop group and `[]` for the vendor external — collision confirmed `True`. New `_codex_group_identity` returns `('Stop', None, {'stop-notification.sh'})` vs `('Stop', None, frozenset())` — distinct confirmed. This validates both reported harms (same-event/matcher overwrite on install; uninstall-template vs live identity mismatch leaving all four groups).

**Fix verified in source** ([install.py:564-582](file)): TOML-decode the unit → `shlex.split` each command (adjacent quoted/unquoted segments rejoin to the true argv — the exact property quoting relies on) → `fullmatch` per argv against hook roots. `render_codex(resolve_python=False)` keeps REPO/HOME quoting identical while leaving `{{HOOK_PYTHON}}` raw, so uninstall identities equal install identities (asserted in-test) with zero resolver calls — C1 and C2 both hold simultaneously, which the previous `render_uninstall`-for-codex approach could not satisfy.

**Test evidence** (read from logs, not re-run): RED `6 failed, 3 passed` (only `plain` passed pre-fix — correct shape for a quoting bug); GREEN `9 passed`; governance focused `156 passed`; `gates.json` ruff/format/mypy all 0. Note: `completion.json` was absent; receipt rests on `red.log`/`green.log`/`focused.log`/`gates.json` + the independent repro above.

### Ownership-semantics assessment (raw regex → parsed argv)

- Direction is strictly narrowing in the safe way: old code harvested basenames from *any* raw-text match (comments, statusMessage included); new code counts only real command argv entries. No canonical template loses identity; external groups can newly collide only on genuinely identical (event, matcher, scripts) — correct ownership.
- Matcher edge: single-quoted or escaped matchers now TOML-decode instead of regex-miss; realistic matchers (`Bash`, `apply_patch`, `""`) unaffected.
- JSON side (CC/ZCode) correctly untouched — exec-form/argv need no quoting.
- **Advisory, non-blocking**: new failure modes for hand-corrupted live TOML — non-string `command` raises bare `TypeError` (not `GovernanceError`), and a group unit unparseable by `tomllib` raises `TOMLDecodeError`, both bypassing the clean-fail contract M3 just established. Requires deliberate live-config corruption; installer never emits it. Suggest a one-line `isinstance` guard → `GovernanceError` at a later pass, not a merge blocker.

### Preservation

Frozen hashes unchanged (`block-memory-index-write.py 6945c4d0…`, `compact-tail-inject.py 39f6dee2…`, `check_single_source.py 15457ad9…`). `ir1.diff` touches only `install.py` + `test_governance_contract.py`.

### Hashes (current WT)

```
11b88181…  governance/install.py
14e34c67…  tests/test_governance_contract.py
```

### Scope limits

No full suite (main owns; pre-IR1 full was 2033+2skips, final adds the 9). M5 metadata and undeployed live configs remain main-owned. CR index still absent — source/`rg` fallback disclosed.

**Verdict: APPROVE for main merge.** No blockers; one advisory above.

Main adjudication: native IR2 subsequently reopened compatibility acceptance; this verdict closes IR1 only, not the later IR2 delta. The malformed-external-command advisory overlaps the ownership boundary now being reviewed.
