# .review/air-91.md — AIR-91 收斂鏈 findings 帳本

## Header identity

- reviewed revision：air-91 branch HEAD `c8bb0d3`＋uncommitted（porcelain ~50 筆：S1–S4 全部產物）
- review 形態：post-build 分腿 external review（user 指定鏈：codex＋muse→5.3 judge）
- legs：L1 codex（機械層）job `job-mu29ljvl-qsxou8`；L3 codex（workflow doctrine）job `job-mu29n3id-0gme2s`；L2 muse（供給層）job `job-mu29lju3-4kj221`
- receipts：`.agent-tmp/air91-s4/review-L{1,2,3}-*.out`

## Finding Record

| ID | 嚴重度 | 位置 | finding（摘要） | remedy 分類 | 狀態 |
|---|---|---|---|---|---|
| F-01 | Important | SKILL.md:146↔agents/AGENTS.md:27↔rules/model-routing.md | family／profile 詞彙定義無家：雙向指針互指、兩端皆無定義句 | drift | open |
| F-02 | Suggestion | agents/AGENTS.md:25 | tier 詞彙歷史語義指針指向 rules/model-routing.md——slimming 後零命中，指針懸空 | drift | open |
| F-03 | Suggestion | catalog.toml effort_values↔SKILL.md:123-130↔sync_agents.py:96-105 | effort 值域三處並存無機械對帳；SKILL:8「不重抄 model 值」宣稱句過寬（政策表必具名） | drift（跨檔 parity 缺） | open |
| F-04 | Important | catalog.toml qualification records | 六 workload 僅三個有記錄——`implement_from_accepted_ep`／`evidence_retrieval`／`review_findings` 零筆＝引用它們的 work unit 形式上 fail-closed no-candidate；今日 dogfood 實跑（impl-lite/lite-verify/reviewers）反而構成觀察證據 | design-gap（EP 未排播種 owner） | open |
| F-05 | Suggestion | SKILL.md:103/307；catalog/presets | CC「預設 sonnet」無 binding 著陸；inherit 路徑（CC 8/9 preset 實際路由）在 candidate 四元組 schema 外 | design-gap（formalization 洞） | open |

## Legs with zero findings

- L1 codex：五軸全 clean（loader 健全性／等價矩陣誠實度〔含 `git show df3741b` legacy 對照〕／projection 純度／invariant 取捨〔附已知 recall 限制〕／測試品質）——NO FINDING
- L3 codex：五軸全 clean（跨檔 WorkUnitContract 一致性／predicate 無繞道／escalation 相容／independence schema／manifest 誠實度）——NO FINDING

## Judge 決策

**5.3 judge（job `job-mu29qqa2-vg8v2w`；receipt `.agent-tmp/air91-s4/judge-final-glm.out`——輸出頭截斷，逐條修法由被採納的 muse remedy 段重構，透明註記）**：F-01～F-05 **全數 ✅ 採納**、零 ❌、零 ⚠️ user 決策項。修法三類：文案指針修正（F-01／F-02／F-05）、宣稱句收窄＋cross-link 註解（F-03）、catalog 補 6 筆 qualification（F-04——播種證據=2026-09-15 dogfood repo_observed）。

**追蹤項（不擋結案，後續卡承接）**：①effort-domain 機械 parity gate；②inherit pseudo-binding 正式化。

| ID | 狀態 | apply 落點 |
|---|---|---|
| F-01 | resolved | SKILL glossary 增 family／profile 定義行＋SKILL:146 指針反轉＋AGENTS.md:27 重指 |
| F-02 | resolved | AGENTS.md:25 重指 SKILL dispatch 預設／lite 分工律 |
| F-03 | resolved | SKILL:8/:12 宣稱句收窄＋catalog 表頭三處 cross-link 註解（機械 gate→追蹤①） |
| F-04 | resolved | catalog.toml 增 6 筆（3 workload × flash-zcode/muse-bridge，repo_observed，附播種證據註解） |
| F-05 | resolved | SKILL CC 行標 pending_binding＋套用段增 inherit＝contract-preserving carrier bypass 句（正式化→追蹤②） |

**收斂驗證（judge 三條件）**：①`sync_agents --check` exit 0 ✅；②`uv run pytest tests/` **510 passed** ✅；③本帳本狀態全 resolved ✅——**AIR-91 收斂完成，無殘餘阻擋項**。
