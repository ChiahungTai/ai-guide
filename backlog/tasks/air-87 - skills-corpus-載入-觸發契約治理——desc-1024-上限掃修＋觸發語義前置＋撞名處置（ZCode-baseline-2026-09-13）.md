---
id: AIR-87
title: skills-corpus 載入/觸發契約治理——desc 1024 上限掃修＋觸發語義前置＋撞名處置（ZCode baseline 2026-09-13）
status: In Progress
assignee: []
created_date: '2026-09-13 04:50'
updated_date: '2026-09-13 21:40'
labels: []
dependencies: []
ordinal: 73000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## 目標一句話
把 ZCode skills 盤查（ai-analysis/reports/2026-09-13-zcode-skills-baseline/report.md）發現的系統性載入/觸發契約問題收斂：desc 長度上限系統掃修、觸發語義前置、同名撞名、frontmatter 變異。

## baseline
ai-rules main @ 開卡 commit。材料源＝baseline 報告（97 active：repo 79＋plugin 18；ZCode 官方載入規則實證）＋model-routing desc hotfix（root cause 案例：raw desc 1,198>1024 被 drop——已先行修復 776 chars 觸發前置，2026-09-13，隨本卡 commit 入庫）。

## 已決策（勿重辯）
- ZCode 載入契約（官方文檔 zcode-guide/diagnosing-skills 實證）：扁平 key:value 解析；desc 缺失或 raw 行 >1024 chars → 整支 drop；觸發呈現只取 desc 前 ~250 chars——「觸發詞尾掛」模式對 ZCode 無效，語義必須前置
- 兩種解析器量測差異：完整 YAML 會剝 # 註解、ZCode flat parser 不剝——長度以 raw 行為準；desc 一律引號化
- model-routing hotfix 已先行（獨立於本卡，root cause 定案材料）
- **行為測試方法論（09-13 codex+5.3 arch-thinking 討論收斂，AIR-85 實證背書）**：
  - desc 改寫＝**activation surface 修改**（skill 會不會被找到/觸發），非 output-shaping——驗收跑 **activation test**（positive＋nonmatch），非 micro-test；skill 清單出現或 body 可摘要（description recall）**不算**觸發成功
  - 四個機械 surface gate（diff 觸及面→測試類型，取代主觀風險判定）：**activation 面**（name/desc/trigger 詞/frontmatter/bootstrap pointer）→ positive＋nonmatch activation test；**decision 面**（must/禁止/gate/authorization/fail-closed）→ behavior scenario，discipline 類升完整 RED→GREEN→REFACTOR；**output 面**（required field/template slot/recipe）→ micro-test；僅 typo/link/格式 → static-only
  - 架構：**不建新 skill**——instruction-testing 是行為驗證 bounded context 擁有者（方法論本體已自 superpowers 吸收）；改造形態＝主文新增 15-25 行「機械觀察面 protocol」（跨 harness invariant：control/treatment、consumer-visible state、premature-action 檢查、四態分類 PASS/FAIL/UNEXPECTED/INCONCLUSIVE、RUNS 統計≠retry-to-green、recall≠behavior 分層、present/missing 對稱）＋**換內容不增肥**（移出 must-execute pilot 案例段 L119-149——已完成設計用途）＋L10 措辭修訂（「不引入 upstream drill harness」≠「不擁有自研 validated adapter」）；**載具配方（ZCode HOME=scratch provider staging／CC settings symlink＋InstructionsLoaded hook）不進 SKILL body**——屬 harness adapter 易漂移，落 scripts/ 或 durable report
  - 成本紀律：RUNS 產分布禁 fail-retry（flaky≠regression）；evals 慢（分/案級）不進常規 pipeline——surface gate 觸發才跑

## 範圍項
1. 全 79 支 repo skill desc 機械掃（raw 長度/引號/# 陷阱/block scalar）＋修復
2. 觸發語義前置改寫（前 250 chars 承載 when-to-use）——高流量 skills 優先（memory-audit/implement/execution-plan/kanban-board 等）
3. code-reality 同名撞名處置（repo 15,361B vs plugin 19,532B，內容不同，載入序 user>plugin 實際生效 repo 版）
4. mermaid 0700 權限、plugin cache 孤兒（110 vs active 18）清理裁定
5. 跨 harness desc 消費差異文檔化（CC 全文 vs ZCode 250 截斷）——instruction-writing skill 增補
6. **instruction-testing skill 改造先行**（本卡改 desc 前落地測試方法）：機械觀察面 protocol＋四 surface gate 入主文、pilot 案例段移出、L10 措辭修訂、載具 adapter 落位——材料＝materials/superpowers-testing-research.md（durable）＋AIR-85 行為測試實證（ai-analysis/_tasks/09-13-conditional-loading-vertical-slice/ep.md「段 3 驗收證據」節：canary/逐字引用/四態/兩載具配方全驗證）
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 desc 契約機械掃 script 入庫可重跑；79 支全綠（raw≤1024、引號一致、無 # 陷阱）
- [ ] #2 觸發語義前置：高流量 skills 前 250 chars 承載 when-to-use
- [ ] #3 撞名/權限/孤兒處置各有裁定記錄落卡
- [ ] #4 跨 session 載入驗證：新 ZCode session skill 清單含 model-routing（hotfix 舉證）＋抽樣舉證
- [ ] #5 desc 觸發語義抽驗（activation test）：至少 3 支高流量已改 skill，各以 isolated fresh ZCode session 跑 positive/nonmatch 各 5 reps；以「首個 consequential action 前是否實際載入／nonmatch 是否未載入」判分並記 PASS/FAIL/UNEXPECTED/INCONCLUSIVE 四態；skill-list 出現或 description recall 不算通過
- [ ] #6 instruction-testing 改造落地：機械觀察面 protocol＋四 surface gate 入主文、pilot 案例段移出（換內容不增肥）、L10 措辭修訂、載具 adapter 落 scripts/ 或 durable report
<!-- AC:END -->
