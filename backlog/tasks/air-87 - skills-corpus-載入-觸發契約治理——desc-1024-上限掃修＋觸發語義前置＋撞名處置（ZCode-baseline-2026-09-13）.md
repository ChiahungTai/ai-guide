---
id: AIR-87
title: skills-corpus 載入/觸發契約治理——desc 1024 上限掃修＋觸發語義前置＋撞名處置（ZCode baseline 2026-09-13）
status: Done
assignee: []
created_date: '2026-09-13 04:50'
updated_date: '2026-09-14 01:34'
labels: []
dependencies: []
references:
  - ai-analysis/_tasks/_archived/09-14-skills-corpus-contract-governance/ep.md
ordinal: 73000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## 目標一句話
把 ZCode skills 盤查（ai-analysis/reports/2026-09-13-zcode-skills-baseline/report.md）發現的系統性載入/觸發契約問題收斂：desc 長度上限系統掃修、觸發語義前置、同名撞名、frontmatter 變異。

## baseline
ai-rules main @ 開卡 commit。材料源＝baseline 報告（97 active：repo 79＋plugin 18；ZCode 官方載入規則實證）＋model-routing desc hotfix（root cause 案例：raw desc 1,198>1024 被 drop——已先行修復 776 chars 觸發前置，2026-09-13，隨本卡 commit 入庫）。

## 已決策（勿重辯）
- ZCode 載入契約（官方文檔 zcode-guide/diagnosing-skills 實證）：扁平 key:value 解析；desc 缺失或 **desc「值」>1024 chars → 整支 drop**〔開工軸修訂 09-14：原記「raw 行」——實證細化：cr-query 值 1,022／nt-v1-query 值 1,014 兩支在清單而整行 >1024；量測軸＝值 chars 含引號，非整行非 bytes〕；觸發呈現只取 desc 前 ~250 chars＋`when_to_use` 全文（官方鍵，repo 47/79 支既有使用）——「觸發詞尾掛」模式對 ZCode 無效，語義必須前置
- 兩種解析器量測差異：完整 YAML 會剝 # 註解、ZCode flat parser 不剝——長度以值 as-written 為準；desc 一律引號化〔開工例外裁定 09-14：block scalar（`>`/`|`）2 支（maintain/scan-project）屬官方支援的顯式形式，維持不改〕；高流量 4 支（memory-audit/instruction-writing/acceptance-evidence/validation-strategy）補 when_to_use 對齊既有慣例（user 裁定 09-14）
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
- [x] #1 desc 契約機械掃 script 入庫可重跑；79 支全綠（desc 值 chars ≤1024、僅認雙引號或 block scalar、無 # 陷阱）〔開工修訂：值 chars 非 raw 行；單引號 gate 為 judge 修正批新增〕
- [x] #2 觸發語義前置：高流量 skills 前 250 chars 承載 when-to-use
- [x] #3 撞名/權限/孤兒處置各有裁定記錄落卡
- [x] #4 跨 session 載入驗證：新 ZCode session skill 清單含 model-routing（hotfix 舉證）＋抽樣舉證
- [x] #5 desc 觸發語義抽驗（activation test）：至少 3 支高流量已改 skill，各以 isolated fresh ZCode session 跑 positive/nonmatch 各 5 reps；以「首個 consequential action 前是否實際載入／nonmatch 是否未載入」判分並記 PASS/FAIL/UNEXPECTED/INCONCLUSIVE 四態；skill-list 出現或 description recall 不算通過
- [x] #6 instruction-testing 改造落地：機械觀察面 protocol＋四 surface gate 入主文、pilot 案例段移出（換內容不增肥）、L10 措辭修訂、載具 adapter 落 scripts/ 或 durable report
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC#3 裁定三項（2026-09-14）：
①撞名（code-reality repo 15,361B vs plugin 19,532B）＝維持現狀＋文檔化——載入序 user>workspace>plugin 決定論性生效 repo 版（治理源；AGENTS.md 工具用法真相源本就指 repo 版），plugin 版隨 plugin 升級自走；不改名不刪（改名斷全 repo 引用、刪失去治理控制，撞名無實害——兩版皆可載、生效者確定）。
②mermaid 權限 0700→0755 對齊其餘 78 支（歷史異常、載入不受影響、純 hygiene；flash 執行中）。
③plugin cache 孤兒（110 SKILL.md vs active 18）＝不動——plugin cache 是 ZCode plugin 系統自管面（版本史/未安裝殘留），清理屬 harness 維護非本 repo 契約層，誤刪傷 rollback。

AC#1 出口證據（段 2）：修復前 FAIL=30（全 bare unquoted：acceptance-evidence/api-and-interface-design/arch-thinking/code-review-and-quality/compact-prep/context7/cr-query/cross-verify/debugging-and-error-recovery/deep-thinking/frontend-ui-engineering/instruction-testing/instruction-writing/kanban-board/kbar-form-analysis/llm-output-convention/metadata-sync/nt-query/nt-v1-query/post-build/review-engine/self-contained-prompt/standup/symbol-query-routing/test-driven-development/trading-analysis/ui-collab/ui-visual-verify/validation-strategy/voice-notification）＋over1024 零（cr-query 值 1,022/nt-v1-query 值 1,014 恰在線上零餘裕）→修復後（--fix 引號化＋cr-query 930/nt-v1-query 938 收斂）FAIL=0 WARN=2（python-type-gap/rules-reminder quoted-# 追蹤項）；scan exit 0；tests/test_scan_skills_desc.py 9 條契約軸回歸綠（值 chars 軸/CJK≠bytes/行前綴不計）。

AC#4 舉證(a)：本 session（2026-09-14 開、hotfix ca369c2 之後的新鮮 ZCode session）harness skill 清單實際含 model-routing（desc 值 775 chars/1,189 bytes 載入在場——同時證 bytes>1024 不 drop、限額軸=值 chars）；(b) 段 3 改寫 8 支之抽樣：段 3 commit 後新鮮 session 舉證（收尾時補）。

——AIR-87 結算（2026-09-14，judge GLM-5.3 GO 條件式→條件全數履行）——

AC#5 定案（judge 裁決 PASS＋修法 b，落卡結論句）：activation probe 定案（三 run 100 runs，39 筆非 PASS 逐 rollout 判讀）：desc-250/when_to_use 自然語言匹配僅在 prompt↔skill 名/desc 強詞彙錨點時促成自動觸發（nt-v1-query 8/10，全數 skill-tool@0 首動作）；弱訊號（日常語言）下工作流 skills 自動觸發不成立——memory-audit 0/10、implement 0/10、execution-plan 0/15（合法條件計），啟動依賴顯式 slash 指令；nonmatch 60/60 零誤觸發。AC#2 的 desc 前置改寫價值隨之重定位：headless available-skills 呈現實測僅名稱＋路徑（與官方文檔分歧，開放機制問題），desc 改寫在 headless 名稱面無法被量測到效果——其價值面在互動端呈現與強錨點匹配，非弱訊號自動觸發。修法裁 (b)：接受「弱訊號自動觸發不成立」為機制事實；強錨點觸發已證可用，desc 撰寫以此為準。效度演進：Run A（leaked 對照）→Run B（乾淨）→Run C（seed 修復），證據＝.agent-tmp/air87/probe/summary-all.md＋flagged-cases.md（39 筆）。

AC#4(b) 舉證：Run B/C rollout 機械實證——改寫 skill（memory-audit/nt-v1-query 等）於 isolated fresh-session available-skills 清單在場（名稱＋路徑呈現形態），重寫未致 drop。

Pr3 裁定（judge 可貼文字）：post-build desc 裁定免改——時序觸發條件已在 desc 首句與 when_to_use 前置在場；本弧僅引號化未改寫，屬「未動筆」非「未達標」。EP「7 支」更正為「7 支改寫＋post-build 引號化（裁定免改）」。

Pr7 更正：裁定② mermaid 實際 0644 非 0755（意圖＝對齊 corpus 已達成，記錄值更正）。

修正批＋收斂批結算：judge 20 findings（19✅/1❌ Fr10 不修）＋codex 附錄全數落地——scan 單引號 gate（RED→GREEN＋3 測試）、BOM、docstring 已知限制、probe kind guard＋carrier shred＋跨切片註記、instruction-writing probe 但書＋轉義規約、model-routing skill 銜接句、Fr4 雙點去材料化（bundle rg 零殘留）、EP 數字更正、agent-workflow 喚醒盲區條款、CLAUDE.md when_to_use stale 宣稱修正（consistency 🔴）＋風險分級語彙收斂三檔。consistency：instruction-testing PASS、instruction-writing FAIL→收斂批後綠。416 tests 綠。

 riders：agent-workflow 補「subagent 自持背景命令完成後自動續跑不可依賴」（本弧兩案例：重開機殺背景、喚醒丟失）；Pr8 pilot 死 link 修復後置至 EP 歸檔時。

judge 前置條件履行：Pr1 branch 收斂（本 commit 序）✓、Fr4 雙點＋rescan ✓、Pr8 後置記錄 ✓、Fr10 不修 ✓。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
skills corpus 載入/觸發契約治理閉合——79 支 desc 全綠（值 chars 軸＋引號 gate 入庫可重跑）＋7 支高流量觸發前置＋when_to_use×4＋instruction-testing 四 surface gate/機械觀察面 protocol 改造＋activation probe 三 run 100 runs 定案（強錨點 8/10 唯一穩定、弱訊號自動觸發不成立＝機制事實、nonmatch 60/60 乾淨；修法 b）＋撞名/權限/孤兒三裁定＋model-routing judge 升級外派 rider；judge GLM-5.3 GO、20 findings 19✅全落地、consistency 收斂、416 tests 綠
<!-- SECTION:FINAL_SUMMARY:END -->
