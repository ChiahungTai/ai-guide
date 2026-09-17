# AIR-100 收編分診提案表（lite-verify 91/91，2026-09-17）

> 全文＝分診 agent 回報（job ledger 可考）；此檔為人裁與 EP 輸入的持久版。統計：收編 35／修寫後收編 30／退役候選 22／拆分 4／待查 0；3 投影檔 regen 隨波 commit；1 D（role-vocabulary-discussion-pending）刪除合理確認。
> 機械基礎：desc>100 共 38（16 隨退役、22 隨修寫）；desc 含日期 12、含 sess_ 1（six-card）、語義截斷 4、壞損 1（minimal-touchpoint desc="user"）；29 個被引 hash `git cat-file -e` 零 MISSING。

## 人裁重點一：退役候選 22（M1+M4 雙命中）
M（4）：air87-skills-contract-inflight、card-format-audience-split-pending、execution-tapestry-0910、submodel-dispatch-arc-landed
??（18）：air105-governance-wiring、air106-governance-wave2-inflight、air111-ep-carrier-four-tier-inflight、air91-s3-behavior-experiment-b-plan、air98-quota-freshness-card、at-scheduled-repo-memory-audit-0916、conversation-dispatch-doctrine-gap、dev-workflow-redesign-plan-ready、execution-order-3lane-proposal、marshal-three-line-air77-81-84-inflight、memory-pool-89-adjudication-pending（隨流入快照移除）、mos105-muse-control-gap-handoff-assessed、reinstall_audit_0916、review-panel-naming-pending（self-tombstone）、review-panel-tri-bi-landed、usage-fit-audit-0201-scheduled、usage-fit-audit-terminal、wave1-handoffs-landed
judge 裁量：可保留 2-3 條高頻誤觸主題為指針形 tombstone（如 air111）。

## 人裁重點二：拆分 4
1. reference_model-capability-ordering → 能力序裁定移 spine/routing family 表後退役（AIR-91 已吸收治理議題）
2. reference_muse-code-cli-facts → 13,066 chars 超 12K 上限；plugin 面分流給 muse-plugin-probe-facts 後壓回
3. project_air96-residual-batch-inflight → 流水退役；「sweep-commit 協調形態」教訓抽出成 feedback
4. project_role-vocabulary-terminal → doctrine 已正典；兩未決尾巴（muse 換主 harness、user WT 想法）先開卡承接再退役；body EP 路徑 `_tasks/done/`→`_archived/` 順手修

## caller 關注：疑似 A 誤置 5 條（正典在 rules/skills → 指針化改寫非刪除）
1. feedback_commit-propose-before-execute（正典＝outward-action-consent commit 段）
2. feedback_control-plane-text-needs-external-review（正典＝AIR-105 審查閘）
3. feedback_closure-cards-stay-on-board（正典＝kanban skill 結案段）
4. feedback_readonly-orders-ban-git-switch（正典＝bridge-dispatch Brief 動詞紀律）
5. feedback_adjudications-reverify-on-site-before-apply（borderline watch——user 處置流程，未 rule 化）
典範形態＝feedback_cross-session-commit-on-active-branch（單一源指針＋事故脈絡）。

## 其餘
- 修寫後收編 30 的主體工作＝desc 壓 ≤100（含 278 chars 的 codex-lifecycle-hooks-doc-facts、209 的 muse-plugin-probe-facts）、去日期/sess_、補 4 條截斷、重寫 1 條壞損（minimal-touchpoint）
- drift 順手修：air87 與 role-vocabulary-terminal 引用的 `_tasks/done/` 實為 `_tasks/_archived/`
- unverified 8 項見原回報（皆不影響判定）
