---
id: AIR-121
title: 機械面寫入驗收閘——審查帳本格式 lint＋解析器正規化＋寫入權準則正典化
status: To Do
assignee: []
created_date: '2026-09-17 08:58'
updated_date: '2026-09-17 08:59'
labels: []
dependencies: []
ordinal: 106000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AI 手寫的審查帳本格式一直漂（9 份歷史帳本 4 種格式），機械解析對不上還會說謊。本卡三件事：給帳本上格式 lint（寫入時機械驗證）、把帳本解析 POC 正規化、把『寫入權由讀取面決定』準則寫成條文。muse＋codex 兩家外審通過並附修正案（三輪討論收斂）。等 user 開工拍板。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 帳本 lint 上線：canonical 機械欄位＝identity（reviewed revision／scope／review_profile）＋decision＋terminal status（實際被 parse/join/count 的欄位才 schema 化）；掛 post-build 與 commit gate；lint 約束條款與記錄面保護條款同 commit 落地
- [ ] #2 parser 正規化（POC 承接）：9 份歷史帳本回歸全分類（parse 或明確拒收）；狀態跨表 ID-join last-wins；prose 計數禁用（否定句陷阱）；exit 契約 fail-closed（0/1/2/3 各有測試）
- [ ] #3 寫入權準則正典化：兩句 normative core 進 rules/quality-constraints.md；分類軸（機械/記錄/混合 × 程式/LLM/拆分）進 memory-audit 載體統一定義表；workflow-review-pattern、kanban-board、compiler 卡三處各一行指針不重寫
- [ ] #4 窗期寫入分流條文化：卡在 main 而 WT 在弧 branch 時，verdict 緩衝落輸出檔＋EP notes、開工②/結案③補落（緩衝制為預設、不擴特赦）
- [ ] #5 instruction-writing 審查閘通過（profile=boundary、跨家族腿 verdict 回卡）；serializer 升級明示不在本卡（顯性觸發才做：lint 長期紅或出現真 join/count 消費者）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@dd3f87d〕

〔已決策勿重辯：①寫入權準則（bi 雙家裁定合成版）：機械依賴 ⇒ 機械強制驗收邊界（非『程式寫入』——codex source code 反例：LLM 寫 code 合法因有 parser/compiler 驗收）；LLM 供語義值、自由文字格式不得直接承擔機械契約 ②寫入權是時間函數（muse）：機械讀者上線才收緊對應面，對記錄面預先收稅＝YAGNI 違規；記錄面開放理由＝爆炸半徑小可事後修（非『讀者容錯』——air-86 政策分叉、air-70 指針腐爛兩起 prose 事故實證）③混合面（prose 內嵌指針／計數）取較嚴寫入權；僅 authoritative count/gate/join 算機械面，convenience grep 不算 ④例外門階梯：schema loader/CLI 即驗即拒 ≻ 實證強容錯讀者（明示降級語義＋誤差方向安全只省略不捏造＋容忍格式不含語義）＞容錯回讀（無效——回讀者必須 ≡ 生產機械讀者同一實現，kanban:116 反證）⑤帳本最小第一刀＝lint 非 serializer（muse：.review ephemeral 隨 commit 清、爆炸半徑小、改動面 ≥6 skills）；lint canonical 欄位採 codex 三欄＝identity＋decision＋terminal status（實際被消費的欄位才 schema 化；severity 未被計數不收）⑥帳本已翻機械面（parser 上線即觸發）→ lint 必須與 parser 同弧落地 ⑦prose 計數禁用：決策住欄位不住散文（air-91『零 ❌』否定句被 regex 數成 1 實證）；狀態跨表 ID-join last-wins（發現時態 vs 終態分表，naive 計數說謊實證）⑧窗期寫入（卡在 main、WT 在弧 branch、卡檔不可見）：緩衝制為預設——verdict 落工單輸出檔＋EP notes，開工②/結案③既有特赦 commit 補落；不擴特赦（09-13 AI 自主 commit 禁紅線）⑨spine 判定：混合面未拆分、frontmatter 側輕違規（_generate_index.py parse_frontmatter 機械解析 vs session 手寫）；frontmatter 寫入閘＝順位三可另卡 ⑩審查紀錄：三輪 bi 外審——compiler 架構（job-mu59xt4g-368jvp／job-mu59xt5m-uzdogu）、寫入權（job-mu5ai4dl-hlm3ml／job-mu5ai4ew-6ypgu2）；muse 抓出 spine:8 引證放大（矛盾舉證成立已吸收）；全文在 .agent-tmp/dispatch-compiler-proposal/（gitignored，結算時 verdict 摘要落本卡 notes）⑪控制面條文語義變更：落地走 instruction-writing 審查閘（profile=boundary、跨家族腿）；保護條款（記錄面自由度）與約束條款（lint）同 commit 落地，缺一即否決〕

範圍——新增：skills/post-build/scripts/（帳本 lint＋parser 正規化＋pytest fixture 用 9 份歷史帳本）；改：rules/quality-constraints.md（兩句 normative core：寫入保障 ≥ 下游讀取契約；寫入權是時間函數）；skills/memory-audit/SKILL.md（載體統一定義表加寫入權軸：機械/記錄/混合 × 程式/LLM/拆分）；skills/_common/workflow-review-pattern.md（status 寫入責任節指針＋canonical 欄位宣稱）；skills/post-build/SKILL.md（收斂態落卡步＋lint 掛接）；skills/judge-review/SKILL.md（落帳本指針）；skills/kanban-board/SKILL.md（窗期寫入分流段）。
明示不動：bridge ledger、backlog CLI、spine（frontmatter 閘另卡）、serializer（顯性觸發才做）、AIR-118（審查腿簡化，範圍正交）。
掃描法：rg「status 寫入|append-notes|Finding Record」找齊消費面指針點；codex 需原文驗證項＝quality-constraints 是否已有更近 invariant（實查後併）。
<!-- SECTION:PLAN:END -->
