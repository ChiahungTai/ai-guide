# AIR-327 R1 Followup Closure (GLM-5.3, same fresh reviewer)

**Basis**: read `.agent-tmp/air327-writer/result.md` (Repair R1 section), `.agent-tmp/air327-adjudication-repro.json`, `.agent-tmp/air327-f3-baseline.txt`, current `scripts/arc_manifest.py`, `scripts/arc_handback_join.py`, both test files, `repair-r1-cr-freshness.json`; one live CR probe. **Tests: read only, none executed by me** (carrier blocks execution; parent executes separately). Writer log claims (4 failed RED → 96/390 passed GREEN, `repair-r1-*.log`) are writer evidence, not my runs.

## Per-finding closure

**fresh-F1 (unhashable ac_id) — VERIFIED (code+test read)**. Guard at `scripts/arc_handback_join.py:155-158` validates each verdict `ac_id` as non-empty string before the `setdefault` grouping (:159); list/dict values yield `invalid: verdicts[i] reason=ac_id 須為非空字串` + continue — typed exit-2 path, no TypeError capture. Parent repro (adjudication JSON: `TypeError: cannot use 'list' as a dict key`, exit 1) is closed by test `test_unhashable_handback_ac_is_diagnosed_before_grouping` (`tests/test_arc_handback_join.py:563-573`): parametrized `["3"]`/`{"id":"3"}`, asserts `verdicts[2]` diagnostic + follow-on `missing: ac_id=3` + valid identity throughout.

**fresh-F2 (TestCli re-parenting) — VERIFIED (structure read)**. `test_units_top_level_non_object_fails_clean` restored as last method of `class TestCli:` (`tests/test_arc_manifest.py:381`); `TestDispatchCustody` now begins at :396, `TestMalformedFilenameRepair` at :511. Oracle-provenance banners now correctly scoped.

**fresh-F3 (NUL suffix) — VERIFIED (code+test read); attribution correction preserved**: `.agent-tmp/air327-f3-baseline.txt` records parent's execution of the **HEAD baseline** producer observing `ValueError embedded null byte` — **F3 was pre-existing at baseline, not introduced by the AIR-327 diff** (supersedes my round-1 "new-code edge" framing). Repair at `scripts/arc_manifest.py:249-252`: precise `"\x00" in suffix` check in `_manifest_filename` with repr'd diagnostic — raised during `project_manifests`, i.e., before `_write_manifests`; no blanket ValueError catch. Test `test_nul_suffix_is_rejected_without_outputs` (`tests/test_arc_manifest.py:512-522`) asserts rc 2, `not out_dir.exists()`, `unit_id`+`NUL` in stderr.

**intent-F1 (surrogate digest normalization) — VERIFIED (code+test read)**. `except UnicodeEncodeError` at `scripts/arc_handback_join.py:81-84`, scoped to the identity try whose only encode site is the digest body's `.encode("utf-8")` (`canonical_json(handback)` performs no encode, so it cannot be masked); emits stable `invalid: identity reason=manifest JSON 須能 UTF-8 編碼（孤立 Unicode surrogate）`. Parent repro (exit-1 `UnicodeEncodeError … surrogates not allowed`) closed by `test_lone_surrogate_manifest_is_identity_diagnostic` (`tests/test_arc_handback_join.py:531-561`): ASCII-escaped JSON file reaches the real consumer UTF-8 boundary via subprocess, asserts exit 2, no Traceback. Echoed-digest surrogates remain caught by the hex64 charset check (:97-101).

## Regression check (changed branches only)

No regression found. Unknown-string-ac path intact (`test_unknown_ac_id_in_handback` :173-186, ac_id `"9"` — string passes the new guard, unknown branch unchanged); no surviving test depended on the old None-key grouping. Exception ordering `ManifestError` (:79) before `UnicodeEncodeError` (:81) is sound (disjoint). Expected binding fully intact post-R1: three-way tuple with `dispatch expected_digest` (:95), hex64/mismatch checks (:97-108), `join(manifest, handback, args.expected_digest)` pass-through (:238). NUL check changes only suffixes containing NUL.

## CR receipt (preprovided-cr)

`repair-r1-cr-freshness.json`: content-bound — `indexed_source_identity == current_source_identity` (`96e82748…`, sha256-v2), `serves: current-tree`, `head_drift: false`; not HEAD-only. Independently corroborated by my live `callers assigned_manifest_digest` probe: producer site now `arc_manifest.py:304` (R1-shifted from :300), consumer `:77`, import `:42` — the served graph reflects post-R1 source. No stale claim needed.

All four findings closed on read evidence; final adjudication and test execution remain parent-owned.
