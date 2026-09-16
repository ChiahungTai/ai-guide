# S1 必要常駐集合初判（待 user 確認後凍結；判準＝漏掉後果＋有無可靠後續觸發點）

## 必中（漏掉即違規或不可逆）
1. `commit-consent-in-autonomous-mode`——commit 確認門。
2. `feedback_verify-wt-before-commit`——並行樹污染防護。
3. `feedback_consistency-gate-not-optional`——收尾鏈必跑。
4. `feedback_backup-unversioned-live-configs`——無版本活配置，低頻但一次漏即災難。
5. `cross-workspace-actions-user-handles`——越界改他檔，低頻高風險。

## 高頻護欄（本 session 高頻使用，漏掉即返工）
6. `feedback_read-current-file-before-reviewing`
7. `feedback_relay-claims-verify-current-state`
8. `feedback_evidence-over-claims`
9. `feedback_dispatch-reread-governing-docs`
10. `feedback_full-read-base-not-context-copy`
11. `feedback_cjk-char-corruption-rg-verify`
12. `project_session-topology-single-writer`

## 不進集合（有可靠後續觸發點，按需取用）
- 計費/額度類（`feedback_quota-*`、`feedback_per-call-billing-model`）：派工節點觸發詞可達。
- 領域 reference（SJ/NT、shell 陷阱、rg 旗標）：任務關鍵詞直配。
- 終態史實類（各 `project_*` 終態條）：init/結案節點，不常駐。
