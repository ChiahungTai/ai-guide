All verification complete. The projection-manifest hash repair corresponds to real drift (AGENTS.md changed 10-09 in AIR-290; manifest last committed 10-01 — stale for 8 days, this diff repairs it). Delivering the review report.

---

# AIR-327 Independent Fresh Correctness Review (GLM-5.3, fresh leg)

## Reviewed identity / scope

- WT `/Users/ctai/Github/ai-guide-air-327`, branch `air-327`, HEAD `7dbfd020fec402ca3c0eabb2c55a5752ae6e2057` — verified.
- **Degradation (identity)**: this session's tool policy denied every command outside the read-only git allowlist — `git diff | shasum`, `python3`, and `uv run` (including the explicitly authorized pytest invocation) were all blocked. **I could not compute the diff SHA256** to compare against expected `f712089b…`. Fallback fingerprint captured instead: 14 tracked modified files, 517 insertions / 104 deletions, file list identical to the brief's frozen scope (verified via `git status --porcelain` + `git diff --stat`); one untracked dir (`ai-analysis/_tasks/air-327-delivery-identity/`, not reviewed as source). Parent should re-verify the SHA before sealing.
- All 14 changed tracked files inspected via `git diff` plus full-file reads of both scripts, both test files, conftest, and the EP (read only after the fresh scan, per brief).

## Coverage

- **Manifest digest canonicalization**: `canonical_json` (allow_nan=False, sort_keys, compact, ensure_ascii=False, UTF-8) and `assigned_manifest_digest` (self-field excluded) read in full (arc_manifest.py:68-85); digest placement in `project_unit` (:293-301); producer/consumer single-source sharing confirmed structurally by CR. Independent test oracles re-derive the digest with inline `json.dumps` params (both test files) — not self-certifying.
- **Consumer expected binding**: three-way compare (manifest self-report / handback echo / `--expected-digest`) at arc_handback_join.py:76-104; hex64-lowercase format gate; `--expected-digest` required (argparse + subprocess-tested missing-arg path).
- **Fail-closed malformed input**: non-finite values rejected pre-projection (arc_manifest.py:112-113) and in join via canonicalization; malformed/missing files → stderr + exit 2; arc_manifest `main` now catches `OSError`/`UnicodeError` (improvement over baseline).
- **Output preflight / exclusive create**: whole-batch preflight before any write, canonical-equality idempotence preserving original bytes, `open("x")` exclusive creation, filename-collision invariant 4 pre-write, race → OSError → exit 2; non-atomicity explicitly documented, not claimed.
- **CLI error paths**: both CLIs read end-to-end; exit-code contract (0/2) consistent with docstrings; consumer surface swept via `git grep` (docs/tests only, no programmatic callers) **and** CR `callers` (see receipt).
- **Docs/fixtures consistency**: zero stale `/1` schema references in tracked files (only intentional legacy-rejection tests); `grok.json`, `projection_freshness.py`, `arc_settle_state.py` exist (no forward phantoms); blueprint S3 changes match root AGENTS.md claims (AIR-215/290 retirement state); projection-manifest hash updates are genuine drift repair (AGENTS.md last changed 10-09 by AIR-290; manifest last committed 10-01). Historical AIR-234/246 backlog cards retain old CLI forms — correct as time-stamped records, not phantoms.
- **S2 sweep**: no residual commit-to-prove-liveness requirements in active skills/agents/rules (only unrelated `--allow-empty-roots`, rebase empty-commit semantics, ping-matrix liveness wording).

## Findings

**F1 — Suggestion / pre-existing / evidence-based — `scripts/arc_handback_join.py:151`**
Unhashable `ac_id` in a handback verdict (e.g., `{"ac_id": ["3"], "verdict": "PASS", "evidence": "x"}`) makes `by_ac.setdefault(v.get("ac_id"), …)` raise `TypeError` (unhashable dict key); uncaught in `join()`/`main()` → traceback, exit 1. Docstring promises stdout line + exit 2. Failure is still fail-closed (non-zero, no false PASS) but violates the stated error contract. Grouping loop unchanged by this diff → pre-existing, attributed to baseline, not a regression.
*Validation*: pytest case feeding a list-valued `ac_id` expecting rc 2 and an `invalid:` line; fix = validate `isinstance(ac_id, str)` per verdict entry (mirroring the manifest-side per-entry pattern at :128-131).

**F2 — Suggestion / confirmed — `tests/test_arc_manifest.py:383,495`**
The inserted `TestDispatchCustody` class (banner: "Oracle provenance: S — AIR-327") landed mid-`TestCli`, re-parenting `test_units_top_level_non_object_fails_clean` (line 495) — an AIR-234-era structural test — into the AIR-327 provenance class. No functional impact (pytest discovers it; assertions unchanged); provenance banner is now misleading.
*Validation*: `grep -n "^class \|    def test_"` shows the method after the custody class's last test; fix = move insertion below the final `TestCli` method.

**F3 — Suggestion / inferred ⚠️未實證 / new-code edge — `scripts/arc_manifest.py:350` (except tuple :384)**
A unit_id suffix containing a NUL byte (JSON `\u0000`) passes `_manifest_filename` guards (no `/`, `\`, `..`) and reaches `path.open("x")`, which raises `ValueError` (embedded null) — not in the `(ManifestError, OSError, UnicodeError)` catch → traceback exit 1. `Path.exists()` swallows ValueError, so preflight won't intercept. Still fail-closed. Inferred from Python semantics — execution denied, not empirically confirmed.
*Validation*: pytest case with `unit_id "AIR-234#im\u0000pl-a"` expecting rc 2; fix = add `ValueError` to the except tuple or reject control characters in `_manifest_filename`.

No Critical or Important findings. Adversarial self-check: digest scheme satisfies UC1 (tamper, re-project, and stale-echo classes all bound by the three-way compare given Marshal-held dispatch records); operator copying expected-digest from a tampered manifest instead of dispatch records is an instruction-bounded risk, correctly documented in work-order.md as a prohibition.

## EP comparison (read after fresh scan)

Implementation matches the EP S1 frozen contract on every clause I checked: schema `/2` both sides with same-named field; digest definition solely in producer's public helper, imported by consumer; exact canonical form (sorted keys, compact separators, ensure_ascii=False, allow_nan=False, UTF-8, lowercase hex); three-way recomputed compare; required `--expected-digest`; idempotent-only re-run with whole-batch preflight + exclusive create; documented non-atomic race semantics. Oracles 1–11 each map to a concrete test (1→formatting/retry tests; 2→`test_changed_dispatch_rejects_old_handback` 4×2; 3→`test_handback_digest_invalid` 5 cases; 4→`test_identity_does_not_replace_structure` incl. identity-absent assertion; 5→`test_valid_identity_is_not_semantic_acceptance` + work-order "結構通過≠完成" bullet; 6→real-subprocess seam test; 7→nonfinite tests both CLIs; 8→recompute True/False branches; 9→predicates-truncation parametrization + reassign digest test; 10→retry/conflict/preflight tests; 11→`test_expected_only_oracle11` + missing-arg subprocess). S2 and S3 diffs match their frozen scopes with no scope creep. The EP's "reviewer reruns at least one mutation oracle" obligation could not be executed here (see degradations).

## Tests run / CR receipt

- **Tests run: none.** `uv run pytest tests/test_arc_manifest.py tests/test_arc_handback_join.py` was attempted exactly as authorized and denied by the session tool policy (three attempts, all blocked). Consequently: fixture digest value `961b585e…` verified textually consistent across all three fixtures, and its canonical correctness is asserted by the test suite, but **unverified by execution in this review**; projection-manifest SHA-1 correctness likewise unverified (the freshness gate will mechanically check it); F3 unempirical. A subsequent execution-capable leg should run the two test files and one mutation oracle (remove the expected-digest comparison; `test_expected_only_oracle11` must fail).
- **CR (live-cr:MCP)**: `get_minimal_context` → 5679 nodes/10113 edges, risk low; index identity `@ 7dbfd02` matching HEAD and resolving new uncommitted symbols → treated as fresh for this working tree. `callers join` → exactly 1: own `main` (arc_handback_join.py:230). `callers assigned_manifest_digest` → exactly 2 + import: producer `project_unit` (arc_manifest.py:300), consumer `join` (arc_handback_join.py:77), import :42. `callers project_manifests` → exactly 1: own `main` (arc_manifest.py:381). No `unverified-by-graph` claims remain for wiring; dynamic/config-driven consumers excluded per CR limits (none plausible for CLI-only scripts; corroborated by text sweep).

Findings only — disposition belongs to the parent.
