Verification leg complete. Final report follows.

---

# AIR-327 flash-final mechanical verification report

session-label `air327-flash-final` · WT `/Users/ctai/Github/ai-guide-air-327` · evidence only, no disposition.

## 1. Execution status — what actually ran vs blocked

**Executed with real output (Bash, before the permission block):** baseline identity — `git rev-parse HEAD && git branch --show-current && git status --porcelain` → HEAD `7dbfd020fec402ca3c0eabb2c55a5752ae6e2057` ✓, branch `air-327` ✓, dirty set = the writer's 14 modified files + untracked `ai-analysis/_tasks/air-327-delivery-identity/` ✓ (matches writer index). Task-dir `ls` confirmed `ep.md` + `index.html` only.

**Blocked, zero execution:** all four work-order §7 commands and the rg scans — `git diff --check`, `uv run pytest tests/test_arc_manifest.py tests/test_arc_handback_join.py -q`, `uv run python scripts/projection_freshness.py --manifest ai-analysis/blueprint/projection-manifest.toml`, `uv run python skills/scan-project/scripts/check_single_source.py`, and both `rg` residual scans — were rejected by the harness permission layer with `Plan mode only allows read-only, non-destructive tools` (three attempts shown, all Bash denied wholesale). **No test counts, exit codes, freshness, or single-source results below come from my own runs; nothing is claimed as executed.** Writer-index claims (92 passed, 5/5 fresh, 15 invariants critical0/important0) remain index-only, not evidence.

**Read-verified instead (Read tool permitted):** both test files in full; both scripts in full; the two S2 owner files; `agents/roles/impl-lite.md`.

## 2. Static S1 facts verified by read

- Digest helper single source: `scripts/arc_manifest.py:82-85` defines public `assigned_manifest_digest()` over `canonical_json` (`arc_manifest.py:68-79` — sorted keys, compact separators, `ensure_ascii=False`, `allow_nan=False`); the join imports it rather than duplicating (`scripts/arc_handback_join.py:39-44`). Matches the EP frozen encoding contract.
- `--expected-digest` is `required=True` in argparse (`arc_handback_join.py:216-220`); missing flag → argparse error exit 2.
- Three-way identity check present: recomputed digest compared against manifest self-report, handback echo, and dispatch expected, each must be lowercase hex64 (`arc_handback_join.py:82-104`); `main` passes the CLI value in at `:230`.
- Non-finite JSON raises `finite JSON required` and is surfaced as an identity reject — consistent with oracle 7 tests asserting `"finite"` in output.
- Semantic separation intact: verdicts are checked only against the {PASS, FAIL, NOT-DONE} set; FAIL/NOT-DONE produce no structural error (`arc_handback_join.py:174-183`).

## 3. S2 residual scan — read-based substitute (repo-wide rg NOT run)

- `skills/agent-workflow/SKILL.md:99`: liveness now anchors on content evidence only (program output / exec activity / artifact updates / WT diff); explicit “不要求為證活提交” (no commit required to prove liveness). No `allow-empty` occurrence in the file. Legitimate commit-before-spawn hits remain and are classified legitimate: worktree preflight "commit first, then spawn" (`:198-200`, `:316`) is real-work commit so worktrees see it, and `:318` is user-consent gating — neither is liveness-by-empty-commit.
- `skills/_common/work-order.md`: §1 no-commit red line intact; Handback closure section carries `/2` schemas, digest echo, dispatch-recorded expected, legacy `/1` rejection, and “結構通過≠完成”.
- `agents/roles/impl-lite.md`: forbids commit entirely (`:16`), heartbeat protocol is the liveness channel — no residual.
- **Not covered:** the repo-wide literal scan over all active skills/ and remaining roles/presets could not run. Absence of residuals beyond the files read is **unverified**.

## 4. Oracle 1–11 mapping (from test bodies; static, not run)

| EP oracle | Covering tests |
|---|---|
| 1 | `test_formatting_and_retry_preserve_identity` (key reorder → 0); producer whitespace variant via `test_same_content_retry_preserves_original_bytes` |
| 2 | `test_changed_dispatch_rejects_old_handback` — field ∈ {contract_hash, verifier, expected, predicates}, each with old handback+expected → 2 |
| 3 | `test_handback_digest_invalid` — missing(None)/42/[]/"wrong"/64×"0" → 2 |
| 4 | `test_identity_does_not_replace_structure` — missing/duplicate/unknown/empty → existing diagnostics, "identity" absent from output |
| 5 | `test_valid_identity_is_not_semantic_acceptance` (FAIL/NOT-DONE → 0) + `TestJoinPass` — per work order §5, join0 is recorded as identity/structure pass only, **not** semantic completion |
| 6 | `test_real_cli_producer_join_and_required_expected` (real subprocess producer→files→join, ± rounds) + `TestSeamWithArcManifest` |
| 7 | `test_nonfinite_cli_exit2` (join) + `test_nonfinite_inputs_fail_without_outputs` (producer); nonfinite leg also in `test_preflight_whole_batch_preserves_known_conflict` |
| 8 | same test as O2: `recompute=False` = tampered artifact + old stored digest → 2; `recompute=True` = re-projected digest + old expected/echo → 2 |
| 9 | `test_reassign_ac_subset_changes_digest_only_not_contract_hash` (hash unchanged, digest changes) + O2 predicates-recompute leg (old receipt rejected) + same-content retry passes |
| 10 | `test_same_content_retry_preserves_original_bytes`, `test_changed_contract_cannot_overwrite_dispatch`, `test_preflight_whole_batch_preserves_known_conflict` (zero pre-writes), `test_exclusive_creation_race_fails_and_preserves_competitor`; nonfinite exit-2 legs run in-process for both CLIs |
| 11 | `test_expected_only_oracle11` — manifest+stored+echo all valid, only expected differs → 2; correct expected → 0; missing-flag leg in the subprocess test |

All 11 oracles have named covering tests present in the frozen bodies; both oracle classes carry provenance comments citing the accepted EP S1 freeze.

## 5. Missing coverage / explicit non-verification

1. **No independently executed tests or check scripts** — pytest/freshness/single-source/diff-check all blocked; all green claims unverified by this leg.
2. **Oracle 11 mutation leg not re-run** — temporarily removing the expected comparison requires source edits, forbidden by the READ-ONLY red line. Statically, the test isolates the expected-only mismatch (every other field valid), so it *would* target that comparison; sensitivity is not independently demonstrated. Writer mutation logs are index-only.
3. Join-side whitespace-only variation of O1 is implicit (JSON parse), key-order leg explicit; producer side covers the whitespace variant.
4. Repo-wide liveness residual scan over all skills/roles: not performed (blocked); only the files named in §3 were read.
5. Full-repo Arc suite (writer claims 386 passed) outside §7 scope — not run.

No fixes, no git mutation, no retries-to-green; failures and blocks reported as observed. Parent judge decides disposition.
