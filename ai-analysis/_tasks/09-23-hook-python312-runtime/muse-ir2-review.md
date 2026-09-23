# Final IR2 independent review

job-mudzulxa-e1dpd1; family=muse; model=muse-spark-1.3; effort=xhigh. Fresh context replaces quota-blocked native final followup. Main accepts the findings and stated limitations; no blocking finding remains.

## Verdict: APPROVE

Independent IR2 delta review of the three scoped files. Current source read in full; hashes verified with `sha256sum` and match `completion.json` exactly.

### Verified hashes

- `governance/install.py`: `6217ddc97a8f29e600a72c4dcbd0f57b0ba0d7623c5fa3212346acd67cc6a735`
- `tests/test_governance_contract.py`: `f8d7422b0f04ec2536a03a9f664c6b84ea5ba346fe2302d978ac7c6b4561872f`
- `tests/test_governance_write_path.py`: `e3c40fbf8a2372c5b33da7a4917a98dd129c9a3cba6d0443667902a79f9adaee`

### Ownership boundary — independently confirmed

Re-implemented the recognizer core from [install.py](/Users/ctai/Github/ai-guide-air-174/governance/install.py:564) in memory (no repo import, no writes) and ran 14 counterexamples with `/bin/sh -n` as oracle:

- `printf ok # don't…` (sh valid, rc 0) → shlex `ValueError` → unowned, preserved. The `except ValueError: continue` path is what prevents valid vendor commands from blocking management — correct.
- Comment with quoted hook path, heredoc, `invalid` quote, non-string, data-arg, midword-hash (both vendor-argv0 and python-argv0 legs) → all unowned, byte-preserved. The midword-hash-via-python leg (not directly covered by tests, which use a vendor argv0) also resolves to unowned via `fullmatch` failure — logic holds.
- Owned legs verified: quoted single-arg direct form, `python3` + script, `{{HOOK_PYTHON}}` + script, spaced interpreter path — all owned after `shlex.split(comments=False)` decode.
- Rejected-candidate rationale confirmed mechanically: `comments=True` strips `['/vendor/tool', '/x/hooks/a.sh#documentation']` → `['/vendor/tool', '/x/hooks/a.sh']` and `printf ok # '<path>'` → `['printf', 'ok']`. `comments=False` avoids both failure modes.
- Template gate: [codex.toml](/Users/ctai/Github/ai-guide-air-174/governance/registrations/codex.toml) emits only the two direct forms (single script; token + script), so the recognizer covers everything the package generates. `_codex_template_groups` enforces nonempty + unique, so template idents can never collide with empty foreign identities.

### Regression assessment

- JSON faces untouched; change surface is `_codex_group_identity`, `_codex_template_groups`, and the two test files. Consumer legs (`_codex_owned_state_keys`, positional warnings, check) now see strictly fewer false ownership claims — safe direction.
- Write-path ordering is sound: template gate raises inside `merge_codex_text` before `apply_text_change`; uninstall never consults the resolver (`render_codex(resolve_python=False)` keeps the token, and the token leg needs no resolution). Tests assert byte-identical vendor preservation and pre-write failure for bad templates.
- Test oracle quality is good: `/bin/sh -n` validity is independent of the implementation, and the 4 path flavors × 7 foreign kinds matrix covers the IR1/IR2 bug shapes.

### Limitations (accepted, not blockers)

1. Deliberately not a shell parser: `python3 script extra`, flag forms, `env`/wrapper invocations, 3-component interpreter basenames stay unowned and preserved.
2. Pre-arc unquoted space-path codex installs will leave stale entries as unowned orphans (those entries were already broken/drifted pre-arc); may need one-time manual cleanup on affected machines only. Non-space roots are unaffected (old unquoted paths still fullmatch).
3. `TOMLDecodeError` propagation from a malformed live unit substring in the check path is pre-existing IR1 shape, unchanged by IR2.
4. Static gates and suite re-run are Main's at commit per scope — not re-run here. Frozen hook files out of scope per instructions; noted the WT-wide diff is the whole uncommitted arc, whose commit/ledger Main owns.
