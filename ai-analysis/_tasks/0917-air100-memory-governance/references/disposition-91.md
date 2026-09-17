# disposition-91——91 條存量處置銷帳表（已執行；AIR-100 S-D）

> **狀態：已執行（2026-09-17）**。user 人裁＝照分診提案全數執行；本工單逐筆銷帳。
> 池 commit：**45f7486**（reviewed admission 主批）＋**729b341**（投影 regen）。
> 對照基準＝`references/cutover-snapshot.txt`（07:19:30 快照，HEAD e4ec684，porcelain 105 條）。
> 分診逐筆依據＝分診 agent 全文回報（job ledger `~/.zcode/cli/agents/sess_014a87f8-*/agent_350ba252-*/output.txt`）＋持久版 `references/consolidation-triage.md`。
> 池鐵律遵守：僅增補 commit（reflog 抽查零 reset/clean/checkout）；add 全具名（零 `-A`/`add .`）。
>
> **執行態樣偏差**：分診表 §二將 `feedback_readonly-orders-ban-git-switch` 標「收編」，但其 §caller 關注與工單 A 誤置清單皆列指針化——依工單執行指針化（歸修寫）。故實績＝**收編 34／修寫 31**（分診帳面 35/30 的 readonly 一條移欄），總數 91 不變。

## 一、退役 22（21 退役＋1 墓碑；人裁重點一）

| id | disposition | 證據 |
|---|---|---|
| air87-skills-contract-inflight | 退役 | `git rm -f`（tracked M；staged D→45f7486）；body `_tasks/done/` drift 隨刪消失（目標條目 project_skills-corpus-governance-baseline 留池） |
| card-format-audience-split-pending | 退役 | `git rm -f`；正典＝kanban SKILL「欄位分工」節 |
| execution-tapestry-0910 | 退役 | `git rm -f`；藍圖真相源 `ai-analysis/blueprint-execution-order-0910.md` 在 repo |
| submodel-dispatch-arc-landed | 退役 | `git rm -f`；17a4fff 在場＋AIR-91 Done |
| air105-governance-wiring | 退役 | `rm`（untracked，從未入 index——git rm 不適用；快照留 bytes/mtime） |
| air106-governance-wave2-inflight | 退役 | `rm`（untracked） |
| air111-ep-carrier-four-tier-inflight | **墓碑改名** | `mv`→`project_air111-ep-carrier-four-tier-doctrine-pointer.md`＋改寫指針形（desc 94 chars：正典＝AGENTS.md UC-Driven 規模段＋execution-plan skill；卡 Done f827231；僅防高頻誤觸）——untracked 故 mv 非 git mv |
| air91-s3-behavior-experiment-b-plan | 退役 | `rm`（untracked） |
| air98-quota-freshness-card | 退役 | `rm`（untracked）；卡 Plan 承載（引用面：quota-spine／bridge-usage-json 條目 wikilink 已收斂為純文字） |
| at-scheduled-repo-memory-audit-0916 | 退役 | `rm`（untracked）；排程已執行完成 |
| conversation-dispatch-doctrine-gap | 退役 | `rm`（untracked）；AIR-99 卡 Plan 承載 |
| dev-workflow-redesign-plan-ready | 退役 | `rm`（untracked）；EP 任務家＋AIR-101 卡承載 |
| execution-order-3lane-proposal | 退役 | `rm`（untracked）；Wave-1 全閉（command-center 條目引用已收斂） |
| marshal-three-line-air77-81-84-inflight | 退役 | `rm`（untracked）；三線終態（six-card／wt-close-full-mode 條目引用已收斂） |
| memory-pool-89-adjudication-pending | 退役 | `rm`（untracked；隨流入快照移除——分診表明列） |
| mos105-muse-control-gap-handoff-assessed | 退役 | `rm`（untracked）；muse-plugins/tool-governance README 承載（codex-lifecycle-hooks／muse-plugin-probe／mv-first 引用已收斂） |
| reinstall_audit_0916 | 退役 | `rm`（untracked）；殘留已記 AIR-100 卡 P1 |
| review-panel-naming-pending | 退役 | `rm`（untracked；self-declared tombstone——本次收編即其宣告的清理波） |
| review-panel-tri-bi-landed | 退役 | `rm`（untracked）；命名正典＝model-routing SKILL |
| usage-fit-audit-0201-scheduled | 退役 | `rm`（untracked）；runner 已跑完 |
| usage-fit-audit-terminal | 退役 | `rm`（untracked）；報告 `ai-analysis/reports/guides-refactoring/usage-fit-audit-20260917.md` 全量承載（at-bootstrap／usage-stats 引用已收斂） |
| wave1-handoffs-landed | 退役 | `rm`（untracked）；動詞紀律正典＝rules/bridge-dispatch |

## 二、拆分 4（人裁重點二）

| id | 拆出 | 原條目 disposition | 證據 |
|---|---|---|---|
| reference_model-capability-ordering | 能力序裁定一行移 spine `~/.agents/memory-spine/reference_model-runtime-entitlements.md`「能力序裁定（0914 user）」條（rg 驗證：astra 已在 model-routing SKILL family 表、**fabel 兩處皆缺**→依工單補 spine 後退役） | 退役（`git rm -f`→45f7486） | spine 檔 rg「能力序裁定」1 命中 |
| reference_muse-code-cli-facts | plugin/hook/memory 機制面三 bullet（plugin 工具鏈實測／validate 補充／feature-config gate＋原生 hooks＋add_memory/memory_pack）移入 `reference_muse-plugin-probe-facts.md` 新節「自 muse-code-cli-facts 分流」 | 修寫後收編：13,066→**9,606 chars**（≤12,000）＋desc 96→壓縮＋指針節 | 45f7486；兩檔 char 數機械驗證 PASS |
| project_air96-residual-batch-inflight | 「sweep-commit 協調形態」教訓抽成新 feedback 條目 `feedback_sweep-commit-coordination-form.md`（desc 91 chars） | 流水退役（`rm` untracked） | 新條目入 45f7486 |
| project_role-vocabulary-terminal | 兩未決尾巴開想法承接：**DRAFT-9**（muse 換主 harness 研究）＋**DRAFT-10**（user 每次自行產生 WT 想法）；EP 路徑 drift（`_tasks/done/`→`_tasks/_archived/`）修正在 draft 內承載 | 退役（`rm` untracked） | `backlog/drafts/draft-9/-10` 檔在場（未 commit——autonomous session 無 repo commit 權，留 user gate） |

## 三、A 誤置 5（指針化改寫；典範形態＝cross-session-commit-on-active-branch）

| id | 指針目標 | 證據 |
|---|---|---|
| feedback_commit-propose-before-execute | rules/outward-action-consent commit 專屬段 | desc 62→「非特赦 commit 先提案後執行的事故證據記錄——…」；body＝單一源指針＋0916 兩事故脈絡（7291c01＋界線質問） |
| feedback_control-plane-text-needs-external-review | AIR-105 instruction-writing 落地前審查閘 | desc 118→指針形；body＝0916 兩 handoff 事故＋漏審三因（程序四點歸閘） |
| feedback_closure-cards-stay-on-board | kanban SKILL 結案段 | desc 72→指針形；body＝0916「移到 DONE」誤解事故 |
| feedback_readonly-orders-ban-git-switch | rules/bridge-dispatch Brief 動詞紀律 | desc 88→指針形；body＝AIR-91 reflog 事故（**分診 §二原標收編——依工單 A 誤置清單執行指針化**） |
| feedback_adjudications-reverify-on-site-before-apply | （無正典——watch） | desc 108→99 去日期；保留 user 指示全文＋body 增「**尚未 rule 化**（borderline watch）」狀態行 |

## 四、收編 34（as-is；全數過六問＋45f7486 入池）

M（15）：feedback_cjk-char-corruption-rg-verify／feedback_command-center-orchestration-mode†／feedback_cross-session-commit-on-active-branch／feedback_drift-scan-include-variants／feedback_relay-claims-verify-current-state／feedback_small-task-do-now-not-defer†／feedback_verify-wt-before-commit／feedback_volatile-user-facts-not-in-instructions／project_agents-registry-split-design†／reference_backlog-md-section-model†／reference_bridge-review-subcommand-facts／reference_ff-merge-over-rebase-hash-references／reference_stacked-branch-merge-order／reference_zcode-platform-facts／reference_zcode-skill-load-contract

??（19）：feedback_detailed-method-with-mechanism-impact／feedback_governance-options-external-challenge／feedback_mv-first-unless-git-history†／feedback_pilot-before-bulk-model-confirm／feedback_plain_language_reports／feedback_scale-ai-proposes-user-vetoes／feedback_shared-dir-rotation-filter-own-prefix／feedback_shell-diagram-task-type-defaults／feedback_uncertain_consult_external_ok／project_flash-marshal-three-preconditions／reference_bridge-glm-output-truncation／reference_check-single-source-checkout-artifacts／reference_dryrun-evaluation-workorder-form／reference_judge-truncation-salvage／reference_lane-muse-review-bundle-form／reference_large-diff-chunked-review-form／reference_multi-round-advisory-workorder-form†／reference_pool-write-provenance-signals／reference_wt_close_pipefail_dogfood_bugs

（†＝收編中附帶懸空 wikilink 修復——見 §六；desc 均原值合規 ≤100）

## 五、修寫後收編 31（desc 壓縮／去日期 sess_／截斷補全／壞損重寫／指針化；45f7486 入池）

| id | 修寫內容 | desc 前後 |
|---|---|---|
| feedback_adjudications-reverify-on-site-before-apply | 去 0917 日期＋未 rule 化標記（§三） | 108→99 |
| feedback_closure-cards-stay-on-board | 指針化（§三） | 72→52 |
| feedback_codex-usage-limit-attribution | 去 0916 日期；正典指 spine（body 已載） | 110→63 |
| feedback_commit-propose-before-execute | 指針化（§三） | 62（摺行）→49 |
| feedback_control-plane-text-needs-external-review | 指針化（§三） | 118→50 |
| feedback_main-agent-discussion-seat-proactive-dispatch | 摺行 desc 補全語義（「…主 agent」斷句）＋制度化單一源標注 | 48（斷頭）→83 |
| feedback_minimal-touchpoint-automation-goal | 壞損重寫（原 desc="user" 摺行殘） | 4→62 |
| feedback_readonly-orders-ban-git-switch | 指針化（§三；分診偏差移欄） | 88→58 |
| project-muse-user-bundle-budget | desc 去水位現值（違 desc 文法 4：現值入 desc 會腐爛）＋去日期 | 105→56 |
| project-uisc-audit-11card-arbitration | 壓縮（唯一蒸餾記錄＋jsonl receipts 保留語義） | 154→64 |
| project_carrier-crud-audit-pool-pending | 壓縮 209→64＋body 現況更新（分診已執行） | 209→64 |
| project_guides-refactoring-baseline | 壓縮 270→63＋body 兩處 wikilink 收斂 | 270→63 |
| project_six-card-review-bipanel-inflight | 壓縮 206→60＋**去 desc `sess_014a87f8`**＋marshal wikilink 收斂 | 206→60 |
| project_skills-cleanup-card-pending | 壓縮 183→62 | 183→62 |
| reference_at-bootstrap-ticket-contract | 壓縮 131→65＋body 增單一源指針＋usage-fit wikilink 收斂 | 131→65 |
| reference_bridge-glm-family-facts | 壓縮 106→62 | 106→62 |
| reference_bridge-usage-json-output | 壓縮 141→64 去（09-15 live 實證）＋air98 wikilink 收斂 | 141→64 |
| reference_codex-lifecycle-hooks-doc-facts | 壓縮 278→94＋mos105 wikilink 收斂 | 278→94 |
| reference_core-bare-corruption | 壓縮 123→60 | 123→60 |
| reference_delegate-bridge-version-path-rot | 壓縮 133→57＋body 指針＋案例形（rule 正典保留） | 133→57 |
| reference_headless-chrome-render-smoke | 壓縮 130→60 | 130→60 |
| reference_lane-wt-pool-write-deferral | 壓縮 137→57 | 137→57 |
| reference_memory-sensor-source-mislabel | 壓縮 123→59 | 123→59 |
| reference_muse-plugin-probe-facts | 壓縮 209→63＋併入 cli-facts 分流內容（§二）＋mos105 wikilink 收斂 | 209→63 |
| reference_quota-spine-time-semantics-gaps | 摺行 desc 補全語義（「…額度 user-level」斷句）＋air98 wikilink 收斂 | 61（斷頭）→60 |
| reference_state-md-gitignored-and-wtclose-trunk-clean | 壓縮 126→57 | 126→57 |
| reference_temp-worktree-precommit-pool-tests | 壓縮 143→57 | 143→57 |
| reference_usage-stats-source-paths | 壓縮 118→59＋usage-fit wikilink 收斂 | 118→59 |
| reference_webgpt-task-inline-material-not-paths | 壓縮 103→59（微壓） | 103→59 |
| reference_wt-close-full-mode-and-rename-residue | 摺行 desc 補全語義（「--preflight」斷句）＋marshal wikilink 收斂 | 60（斷頭）→58 |
| reference_zcode-skills-injection-budget-ladder | 摺行 desc 補全語義（「＋budget」斷句） | 64（斷頭）→62 |

（desc 長度為 folding 後單行 chars；「斷頭」＝原 generator 只讀首行致語義截斷的摺行 desc）

## 六、drift 順手修＋懸空 wikilink 收斂（fabf4e7 先例）

- air87／role-vocabulary-terminal 的 `_tasks/done/`→`_archived/`：兩條目均退役——路徑修正在 **DRAFT-9/10**（role-vocab）與刪除消失（air87）承載
- 懸空 wikilink 修復 11 處（存活檔 → 已退役條目）：backlog-md-section-model、wt-workflow-form-decision、os-architect-review-posture、mv-first、holistic-dryrun、blueprint-before-new-cards、command-center-orchestration-mode、static-server-arch-spec-0910、multi-round-advisory-workorder-form、guides-refactoring-baseline（2 處）、carrier-crud-audit（stale 狀態句同步更新為「已執行」）
- 其中 5 檔為 **91 條外舊條目**（wt-workflow-form-decision／os-architect-review-posture／holistic-dryrun／blueprint-before-new-cards／static-server-arch-spec-0910）——原 tracked clean，僅因連結修復入本批 commit（具名 add）

## 七、D 確認（分診第三節）

| id | 判定 | 證據 |
|---|---|---|
| project_role-vocabulary-discussion-pending | 刪除合理 PASS | 成對蒸餾由 role-vocabulary-terminal 完整承接（本批亦退役、尾巴入 DRAFT-9/10）；歷史可 `git show HEAD:<file>` 取回；刪除 staged→45f7486 |

## 八、投影與驗證

- regen：`uv run python .agents/memory/_generate_index.py` exit 0（B 形態 13 resident 2,575/6,000；inventory 343 entries 57,968 chars）
- `--check`：**PASS exit 0**
- 池 git：45f7486（主批）＋729b341（投影）；reflog 抽查＝零 reset/clean/checkout（僅增補自證）
- reconcile：exit 2（dirty 13 條）——**殘留全為分診後新流入，明列於 §九**

## 九、殘留（分診後新流入——非本批，交 owning 弧／次波 consolidation）

分診掃描（~05:5x）後、快照（07:19）前後新流入 13 檔，未經人裁、不擅入 reviewed admission commit：

- M：flow-feedback-done-archive（06:16 他弧改）、project_agents-fleet-orchestration-vision（06:32 他弧改）
- ??：feedback_guard-last-line-instruction-first（05:58 誕生晚於分診掃描）、feedback_guard-block-check-staged-baseline／project_air113-s2-terminal／reference_project-skill-placement-gitignore-flip（快照後 07:3x 出現）、project_air116-unified-governance-package、project_air117-postbuild-memory-cleanup、project_bi-postbuild-air115-inflight、reference_bi-panel-review-dispatch-form、reference_postbuild-mechanical-gates-form、reference_project-skill-discovery-paths、reference_skill-library-architecture-evidence（平行弧 AIR-112/113/114/115/116/117＋sensor 工作產物）

## 十、污染基線重審（卡 Plan ③）——本工單未執行

`git log -S originSessionId -- .agents/memory/` 定量＋逐條重審在 EP S-D pseudo step 4，惟本工單 Phase 0-5 未含（spawn prompt 範圍外）——**未解決項，留主 session／次波**。
