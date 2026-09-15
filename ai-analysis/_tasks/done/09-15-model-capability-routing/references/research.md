# AIR-91 model capability routing research

## Scope and baseline

- Repository: `/Users/ctai/Github/ai-guide`
- Baseline: `df3741b81e90dad01ed30fb383750ad55630998d`
- Product surface: routing instructions, agent projection generator, generated registries, workflow skills, parity checks and tests.
- Source reports: `ai-analysis/reports/2026-09-14-sub-model-marshal-cross-consult.md` and its visual explanation.

## Current ownership map

| Concern | Current source | Consumers / projections |
|---|---|---|
| Always-on role-to-tier rule | `rules/model-routing.md:5-33` | deployed guide bundles, workflow decisions |
| tier-to-model and provider mechanics | `skills/model-routing/SKILL.md:10-70,101-286` | workflow skills, `sync_agents.py`, external-runtime dispatch |
| lifecycle stage-to-registry table | `agents/AGENTS.md:32-75` | `agent-workflow`, human navigation |
| neutral role prompts | `agents/roles/*.md` | generated `agents/zcode/*.md`, `agents/claude/*.md` |
| requirement and pin projection | `scripts/sync_agents.py:28-188,252-431` | generated registries, `--check`, `--map` |
| projection tests | `tests/test_sync_agents.py` | schema, render, purity, idempotence, parity and golden bytes |
| long-term invariant | `skills/scan-project/scripts/check_single_source.py` | `tests/test_check_single_source.py:266-331` |

## Confirmed structural facts

1. `vision` is described as a capability axis in `skills/model-routing/SKILL.md:12`, but `_TIER_TOKENS`, `ROLE_REQUIREMENTS` and `ZCODE_PINS` model it as a peer of `full` and `lite` in `scripts/sync_agents.py:28-69`.
2. `sync_agents.py` parses Markdown headings and table rows with `_ROLE_REQ_HEADING`, `_TIER_TABLE_HEADING`, `_ZAI_PIN_RE` and `_ANTHROPIC_ALIAS_RE`; `check_parity()` compares copied dicts against those parsed values. Adding more requirement dimensions to the same table would increase parser coupling.
3. `render_registry()` receives one scalar requirement and materializes a single model pin. Generated harness files therefore remain deployment presets even after the conceptual contract becomes multidimensional.
4. Workflow ownership is already split in practice: `skills/post-build/SKILL.md:19-28` locks role order, while its judge, fix and mechanical verification phases have different capability needs.
5. `agents/AGENTS.md:66` still lists `cr-research` as `lite`, while `rules/model-routing.md:23`, `skills/model-routing/SKILL.md:64` and `scripts/sync_agents.py:33` classify it as `full`. This is confirmed current-document drift.
6. Personal entitlement state already has a separate home: `.agents/memory/feedback_volatile-user-facts-not-in-instructions.md:10-13` and `~/.agents/memory-spine/reference_model-runtime-entitlements.md:8-18` separate volatile account/quota state from stable routing policy.
7. Existing real post-build evidence uses GLM judgment, Muse external review and Flash mechanical verification; the workflow is already routed per work unit rather than by one model for the whole skill.

## Code-reality and complementary evidence

- `.code-reality/graph.db` is present. `code-reality scip_refs` healed the Python index and reported `[SRC] scip index @ df3741b · repo HEAD @ df3741b`.
- `mcp__code_reality__impact_radius` over `scripts/sync_agents.py`, routing docs and `agents/AGENTS.md` identified the generator functions `_section`, `parse_skill_role_requirements`, `parse_skill_zai_pins`, `check_parity`, `render_registry`, `expected_projections`, `render_map` and `main`, but returned zero transitive impacted files. Markdown consumers and test imports are not represented sufficiently for this change, so this is not evidence of zero ripple.
- `rg` complementary scans identify active consumers in root/rules/agents navigation, `skills/CLAUDE.md`, execution-plan, implement, judge-review, post-build, agent-workflow, self-contained-prompt, `tests/test_sync_agents.py` and `tests/test_check_single_source.py`.

## Reusable infrastructure

- `scripts/sync_agents.py` already provides compute-then-apply, zero-write `--check`/`--map`, marker ownership, collision failure and atomic writes.
- Python stdlib `tomllib` can load a structured catalog without adding a dependency.
- `tests/test_sync_agents.py` already has fixtures for three requirement classes, generated-byte assertions, missing-policy failures, tree snapshots and real-repo parity.
- `check_single_source.py` already invokes `sync_agents.py --check`; it can remain the convergence gate if the generator validates the new catalog and profile bindings.
- Existing report-shell template and post-build hooks can carry the plan and final dispatch evidence without introducing another UI.

## Model and workflow facts accepted for this task

- Decision-work candidates are based on the user's prior experiments: GLM 5.3, ChatGPT Web High, Sol medium-high, Astra, Opus and Fabel are user-qualified for EP synthesis and judge work; Muse Spark 1.3 is conditional.
- GLM Flash is user-qualified for native visual observation and may outperform GLM 5.3 on that capability. This is a routing qualification, not a public benchmark claim.
- A good accepted EP lowers implementation judgment requirements. It does not transfer final acceptance authority to the execution model.
- When no single candidate meets decision-grade plus native vision, the accepted fallback is visual observation by a qualified visual model followed by decision-grade adjudication, with explicit non-equivalence and provenance.

## Risks and assumptions

| Risk / assumption | Level | Planned check |
|---|---|---|
| A structured catalog can become the model-ID and preset-binding source without changing generated bytes | High | RED fixtures around catalog parsing, legacy golden bytes and `sync_agents --check` |
| Harness registries only need one materialized default model even though conceptual requirements are multidimensional | High | Preserve scalar generated frontmatter; validate chosen model satisfies preset requirements before render |
| Workflow phase declarations can remain owned by each workflow without recreating a central duplicate table | Medium | current-doctrine `rg` and review of all four workflow skills |
| Role and subagent can be separated semantically without renaming all existing registry entries immediately | Medium | define Role/authority and execution-profile/preset separately; retain registry names as compatibility adapters |
| Availability data remains outside the catalog | Medium | catalog schema rejects quota/reset/account-state fields; skill points to memory spine |
| Two-stage visual fallback preserves enough evidence for adjudication | High | work-order schema requires grounded observations, image/region provenance, uncertainty and `arbiter_viewed_source=false` |

## Negative claims and limits

- No claim is made that archived reports contain no old tier terminology; archive is excluded from current-doctrine zero-hit gates.
- No claim is made that all listed providers are currently available. Capability qualification and personal availability are separate.
- No claim is made that GLM Flash is globally stronger than GLM 5.3; only native visual qualification is accepted.
- Code-reality zero impacted files is not treated as a safe-change verdict because the main ripple is Markdown and generated artifacts.

## Independent review evidence

- Native architecture/completeness/UC reviewers found the original ownership, resolver, preset escalation, authority, accepted-EP, independence, visual-delivery, testing and deployment gaps. Their accepted findings are normalized as R-01 through R-19 in `../ep.md`.
- Muse Spark 1.3 external review completed as `job-mu1yenkk-6nki0y`; GLM 5.3 external review completed as `job-mu1yersn-qie38t`. Both were read-only advisory runs through delegate-bridge.
- A fresh GLM 5.3 follow-up (`job-mu1z29x2-qwsjec`) reviewed the rewritten EP and AIR-91 card and returned `ACCEPTED` with no remaining Critical or Important finding.
- Raw external receipts remain in `.agent-tmp/air91-*-review.json` and `.agent-tmp/air91-glm53-followup-wait.out`; the EP ledger is the tracked adjudication record.
