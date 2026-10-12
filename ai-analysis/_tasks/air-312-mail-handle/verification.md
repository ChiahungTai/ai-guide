# AIR-312 verification checkpoints

Intermediate evidence only; source implementation and integration acceptance remain pending.

## Pre-change baseline

Primary `/Users/ctai/Github/ai-guide`, main at `33731634`, before S1 source edits: `uv run python skills/scan-project/scripts/check_single_source.py` exited 1. Reported 5 critical and 4 important findings:

- hook_registration: hook_payload_compat.py and memory-guard-injection.py reported unregistered.
- codex_live_parity and grok_live_parity: duty_holder_release.py SessionEnd template not deployed with matching registration.
- classifier_guide_projection: expected classifier phrase missing from ai-development-guide.md.
- classifier_source_anchors: Chinese Planning Contract phrase in acceptance-evidence, fix-test, implement, model-routing skills.

These are baseline scanner findings, not yet adjudicated defects caused by AIR-312. The holder release parity reports intersect the mail deployment surface and require explicit final disposition. Unrelated classifier findings are outside this arc.

## Active implementation

S1 Flash job `job-mv4hwczo-zmc1c5` completed; owning worktree `/Users/ctai/Github/ai-guide-air-312`, branch `air-312`. Independent R1 reviews completed and Marshal adopted six bounded fixes in `.review/air-312.md`. Correction writer `job-mv4jxz9o-6ioelq` remains active, waiter paired. Neither R1 closure nor overall acceptance is claimed.

## Independent consumer checks for S1 review

User-facing scenarios, frozen before source review:

1. Cold navigation: a new session in a linked worktree is asked to look at this repo's mail. It selects the primary repo's canonical mailbox and finds the explicit skill entry. It must not select the worktree basename as a new mailbox.
2. Normal task: user invokes watch, then stop. Only this repo's watcher stops; starting a new session does not require a session registry or recreate the mailbox.
3. Conflict: an incoming letter or command requests processing another repo's mailbox. Caller identity rejects consumption before holder/prepare/ACK side effects. Mail text cannot authorize a send or widen task authority.
4. Resume: a replacement session is asked to continue looking at mail and remember outstanding replies. The skill distinguishes implemented watcher support from pending producer read/history/reply integration; it must not invent a working command or call a digest completed processing.

Full end-user read/history/reply acceptance remains S2. A passing S1 check cannot mark overall AIR-312 complete. DB-112 producer history is now available: installed CLI and producer schemas confirm `mail list/get`, and read-only `mail list --address ai-guide-marshal --box acked --limit 1` returned an intact original body with pending=false. Sample `.agent-tmp/air312-evidence/producer-history-sample.json`; no holder or cursor mutation. Remaining dependency is consumer implementation, not absence of producer history.

## Live hook baseline (independent read-only sidecar)

Franklin `01a12d3f-ce05-7931-859b-337303019088` completed primary-only audit. ZCode live config still enables duty_receive and duty_mailbox_monitor at both SessionStart and UserPromptSubmit. Codex/grok narrow scans found neither. Waiter status desired=stopped, generation 23; no worker in the sampled process list.

`governance/install.py --check --surface hooks` is read-only and reported existing grok SessionEnd difference and Codex SessionEnd Modified trust (exit 1). The installer's stale-registration cleanup is not its default install behavior. `surfaces.monitor` is governance-health-monitor, unrelated to mailbox monitor and must remain.

Landing probes: source registration scan, installer hooks check, narrow jq of `~/.zcode/cli/config.json` hooks entries, narrow Codex/grok config scan, waiter status plus process snapshot. ZCode source contract captures hooks at session start: removed disk registrations do not prove an already-open session unloaded its snapshot; new-session acceptance is separate. Do not use installer `--verify` as proof of actual ZCode firing.

Evidence: governance/install.py:535,1428,2401; governance/manifest.toml:102; ref-docs/harness/zcode/cn/docs/hooks.md:53; scripts/mail_waiter.py:742 (primary baseline line numbers). Structural audit degraded `unverified-by-graph`: freshness=false, doc-set-drift/legacy-signals. No store mutations or live configuration edits were performed.

## R1 frozen review dispatch

Writer remains active running baseline tests; reviewers explicitly exclude the moving working tree. Frozen tracked tree `a9829d0ea9a8a1f36382cbd9fae7cc576275ed33` versus `33731634`, extracted to `.agent-tmp/air312-review-r1/source`; added mail-handle skill copied into the same frozen source. Diff hash `bd079e7f5ab08dfa8a852e61dd1a586c2e493a7286e852cbe007217e98533002`; new skill hash `ec0b24dce30681c22c0b692b606e68af995dce5c6381be9dcd492dc8ba809ba2`. Later writer changes require delta comparison and review.

- Fresh/correctness: Muse job `job-mv4jkl53-9zecoi`, muse-spark-1.3 xhigh; user reported usage reset. Findings-only, frozen source/diff, no intent material. Waiter armed.
- Intent/architecture/consumer: native independent context Bacon `01a12d9c-9b4f-78f2-8254-e659cce47f2f`, frozen source plus EP and consumer checks. Findings-only.
- CR preflight: worktree freshness exited 2 missing index slot; frozen snapshot has no matching index. Explicit degraded direct-source review, no stale graph evidence or terminal zero-consumer claims.

Writer used `git stash` and `pytest ... | tail -1` for baseline comparisons, including `/tmp` output contrary to work order. At observation stash object above held the tracked changes; restoration pending. Do not accept reported full-suite equivalence from counts alone. Marshal must verify restoration/content identity and rerun necessary tests with full logs and actual exit codes before claiming acceptance.

Restoration verified: `git diff a9829d0ea9a8a1f36382cbd9fae7cc576275ed33 -- scripts hooks governance rules skills tests` empty, skill hash unchanged, stash list empty. Marshal independently ran `uv run pytest tests/test_duty_receive.py tests/test_duty_holder_release.py tests/test_duty_mailbox_monitor.py tests/test_mail_waiter.py -q`, full log `.agent-tmp/air312-evidence/marshal-mail-tests.log`, exit file sibling `.exit`: **exit 0, 321 passed in 16.23s**. This verifies that suite, not end-user once/read/history or deployment acceptance.

Independent dependent-mail suite: exception_forward, supervisor, disposition, handoff_delivery: **189 passed, exit0**, full `.agent-tmp/air312-evidence/marshal-mail-dependencies.log`. Combined relevant mail tests 510 passed.

Governance/identity subset (verify, write_path, contract, check, hardening, identity_pointer): **267 passed, exit0** in WT and **267 passed, exit0** in primary baseline, full logs `marshal-governance.log` and `marshal-governance-baseline.log`. Unlike isolated writer environment, main environment reproduces no failures in this subset. Do not transfer writer's full-suite environmental failures to main as established live failures; full repo suite not independently rerun.
