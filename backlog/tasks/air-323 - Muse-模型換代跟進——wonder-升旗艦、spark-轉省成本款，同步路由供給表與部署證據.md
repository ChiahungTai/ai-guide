---
id: AIR-323
title: Muse 模型換代跟進——wonder 升旗艦、spark 轉省成本款，同步路由供給表與部署證據
status: Done
assignee: []
created_date: '2026-10-12 22:36'
updated_date: '2026-10-12 23:21'
labels: []
dependencies: []
references:
  - skills/model-routing/catalog.toml
ordinal: 308000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Muse（跨家族審查與備援用的 AI 服務）換代：供應商 2026-10-12 把預設旗艦換成 muse-wonder-1.0（context 與舊旗艦同值、effort 新增 max 檔位），委派工具 bridge 3.14.0 已跟進。user 裁定：**wonder 從此是旗艦、spark-1.3 降為 lite 省成本款**。

**做什麼**
- 同步「模型供給事實」：model-routing catalog、effort 家族表、agents 對照表、相關測試——wonder 旗艦（深推理建議升 max）、spark lite 留用（顯式指名才派）
- 工作資格誠實處理：spark 上實測的資格留在 spark；wonder 新列「待首次實測」
- 補記供應商逆向新證據到部署紀律：rules 檔超過啟動限制會被截尾（共享池）——裁決＝維持 bundle 瘦身不變
- 補 commit 上一卡（AIR-318）漏掉的 mail-autoarm marker 檔

**不做什麼**
- 不改路由政策骨架（muse 仍是跨家族第二意見＋額度備援腿）
- 不重驗 spark 既有資格、不動歷史報告／歸檔／官方文檔鏡像

**現在到哪**：剛建卡，等開工。

```mermaid
flowchart LR
    mail["DB-118 換代通知信"] --> cat["catalog.toml<br/>wonder 旗艦 + spark lite"]
    mail --> fam["effort 家族表<br/>深推理建議升 max"]
    mail --> rule["部署紀律<br/>補截尾鐵證"]
    user["user 裁定<br/>wonder 旗艦 spark lite"] --> cat
    cat --> test["測試同步全綠"]
    fam --> test
    test --> review["獨立審查腿"]
    review --> merge["merge 回 main"]
    marker["AIR-318 marker 補 commit"] --> merge
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 catalog.toml：muse-wonder-1.0 identity＋bridge-muse-wonder-1.0 binding 在場（token/provider_native/effort_values 含 max/image_transport）；spark identity/binding 原樣保留；wonder 五 workload conditional/pending_first_use 播種＋drift 註記齊（is_default 翻轉、context_limit 同值、bridge 3.14.0 pin＋L4 job id）
- [x] #2 SKILL.md：dispatch 預設段＋family 表 muse 列改 wonder 旗艦＋spark lite（含 bridge 裸委派落 wonder、spark 需顯式 --model 註記）；深推理建議 max＋CLI 值域列明；容量欄 context_limit 1,007,997＋payload 天花板 460,800 tokens
- [x] #3 agents/AGENTS.md muse code 行同步（wonder 全棧、spark lite）
- [x] #4 全量測試綠：uv run pytest（含同步後 availability_snapshot/sync_agents/parity_lint 及受影響 fixtures）
- [x] #5 sync_agents.py --check 綠＋card_validate 綠＋live 源（skills/agents/rules/tests/root AGENTS.md）muse 引用語義一致（wonder＝旗艦／spark＝lite，無過時「spark 全棧」殘留）
- [x] #6 rules/AGENTS.md 尺寸 gate 節補 muse 1.4.6 截尾鐵證（共享池／截尾通知模板／skills catalog 32KB 壓縮三事實）；瘦身裁決不變
- [x] #7 .agents/mail-autoarm.json 入版控（AIR-318 補件）
- [x] #8 落地前審查閘回執四欄入卡 notes（classification/review evidence ref/session-freshness/deployment-surfaces）
- [x] #9 收 Done 時 Final Summary 帶 as-built 終態圖（mermaid）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 57716863〕
〔已決策勿重辯：①wonder＝旗艦、spark＝lite（user 2026-10-13 對話原話「另外要開始將wonder 列為旗艦 spark當成lite」）——雙 identity 並存，非 drift rename，比照 GLM 旗艦+flash lite 模式；②深推理建議檔位升 max（DB-118 信：CLI 值域 none|minimal|low|medium|high|xhigh|max|ultra）；③spark 既有 workload qualification 原樣保留（證據＝spark 實測）；wonder 播 conditional/pending_first_use 種子（比照 bridge-glm-5.3-flash implement 播種先例 catalog.toml 359-367），首次實測 PASS 後升 qualified；④effort_values：wonder＝[low,medium,high,xhigh,max,ultra]（max 歸因 wonder 檔位表）；spark 維持 [low,medium,high,xhigh,ultra]；⑤控制面弧（觸 skills/agents/rules/root AGENTS.md）→ persistent card WT authoring（scripts/wt-open.sh），canonical 主樹留 main；⑥不動白名單：ai-analysis/（歷史報告與任務凍結材料）、ref-docs/harness/（官方鏡像，更新走 crawl.py 另案）、backlog/ 歷史卡、測試凍結樣本 fixture 中屬歷史 snapshot 者（僅同步會隨 catalog 語義變動的斷言）〕

範圍：
A. skills/model-routing/catalog.toml——新增 [[model_identity]] id=muse-wonder-1.0（label Muse Wonder 1.0；native_vision capability 沿 family --image transport 事實 repo_observed）＋[[dispatch_binding]] id=bridge-muse-wonder-1.0（model_identity/token=muse-wonder-1.0、carrier=bridge、surface=muse-family、provider_native、family=muse、effort_encoding=param、effort_values 含 max、transport=[image_transport]）；spark identity/binding 原樣保留；wonder 五 workload 播種（ep_synthesis/adjudication/implement_from_accepted_ep/evidence_retrieval/review_findings，status=conditional、evidence_source=pending_first_use、binding_scope=[bridge-muse-wonder-1.3 對應新 id]）；條目旁 drift 註記（2026-10-12 meta catalog is_default 翻轉、context_limit 1,007,997 與 spark 同值、bridge 3.14.0 DEFAULT_MODEL pin＝wonder＋VALID_EFFORTS 補 max、L4 探針 job-mv5rv84c-xijkim）。
B. skills/model-routing/SKILL.md——dispatch 預設段 muse code 行：wonder 全棧旗艦、spark lite（顯式指名）；family→(model,effort,容量) 表 muse 列：model=muse-wonder-1.0（備註 spark lite：bridge 裸委派落 wonder〔DEFAULT_MODEL pin〕、spark 需顯式 --model）；effort 欄：預設 xhigh 不變、深推理可升 max（附 CLI 值域；舊 ultra alias 註記隨代換作廢）；容量欄：context_limit 1,007,997＋task payload 天花板 460,800 tokens（hard compaction threshold，caller 預算參考）。
C. agents/AGENTS.md——muse code 雙身分行同步（wonder 全棧＋spark lite）。
D. rules/AGENTS.md 尺寸 gate 節——Muse delegation startup 條補 1.4.6 逆向鐵證三事實：startup 共享池（rules＋skills catalog＋developer prompts 同鍋、fit_skill_catalog_rows_reserving）、超限截尾＋插一行通知（verbatim 模板事實，非僅警告）、skills catalog 32KB 即壓縮；「1M 對話 context 可放寬 bundle」前提不成立——裁決維持瘦身。
E. 測試同步——tests/test_availability_snapshot.py、tests/test_sync_agents.py、tests/test_parity_lint.py（CATALOG_TOKENS 補 muse-wonder-1.0）＋受影響 fixtures；全量 uv run pytest 綠。
F. .agents/mail-autoarm.json 入版控（AIR-318 補件——比照 .agents/marshal-governance.json／memory-governance.json tracked 慣例）。
G. 機械閘——scripts/sync_agents.py --check（parity）、scripts/card_validate.py、live 源 muse 引用語義掃描（wonder＝旗艦／spark＝lite 一致，無「spark 全棧」過時殘留）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔1013 checkpoint〕主實作回收（impl-lite att-1）：五 commit（1961d2ee catalog／df6199cb SKILL+agents／78b32218 rules 鐵證／4b90fb47 tests／90e10b8f marker 補件）、全量 3862 passed 1 skipped、parity/validator/語義掃描三閘綠、marshal 機械覆核 diff scope 符合。偏差②覆核結論：marker 檔為 primary untracked（不隨 WT），agent 重建 bytes 與 primary 現存檔一致（{\"protocol\": 1}）——無衝突。repair 腿（att-2）進行中：SKILL.md 檔位表深推理列＋可考值域註記 ultra→max 殘留三行（主實作 scope-out finding，同 face 前後矛盾）。審查閘分類：ordinary（供給事實同步、無 gate/authority 語義變更）→ 待一條獨立 context 審查腿。AIR-318 觀察：開場 advisory 陰性但 armed_at straddle 180s 窗＝不可判定；已重掛哨 gen 3（下個 session 結論性觀測機會）。

〔1013 收斂〕F1 微修 89a93ffd 落地（全量閘 3861 passed 2 skipped）。弧 code-complete：branch air-323 七顆 commit（1961d2ee/df6199cb/78b32218/4b90fb47/90e10b8f/0a21db23/89a93ffd）。〔落地前審查閘回執〕classification=ordinary（供給事實同步——外部 model 換代＋user 兩次裁定輸入；無 decision/authority/gate/authorization/acceptance 面語義變更，路由政策骨架不變）／review=獨立 context 腿 fresh-eyes code-reviewer att-air323-review-1：PASS-with-findings——2 info（F1 wonder qualification 消費點標註已採納修復；F2 branch-base 落後卡 md 差異由收線 rebase 吸收），軸 A-F（事實準確/單一源 drift/證據誠實/instruction 合規/結構/marker）全查證零 critical-major-minor，reviewer 自證命令清單在 session task receipt／session-freshness=fresh（本 session＝author session；弧中無 redeploy／bundle 變動；instruction-writing skill 於任何 instruction 檔編輯前已載入並注入工單）／deployment-surfaces=pending（merge 後 deploy_agents.py 重投影 rules bundle＋驗證——本卡觸 rules/AGENTS.md＋skills/agents 面）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
muse 換代落地（main b552b65f）：wonder-1.0 旗艦（bridge 裸委派預設、深推理建議 max）＋spark-1.3 lite（顯式指名）；catalog 雙 identity/binding 並存＋wonder 五 workload pending_first_use 播種（spark 實測證據原樣保留）；SKILL.md 五處語義同步；agents 對照表同步；rules/AGENTS.md 補 muse 1.4.6 截尾鐵證（裁決＝維持瘦身）；AIR-318 marker 補入版控；delta tour pending row 已 register（arcId=air-323）。收斂證據：全量 3862 passed、parity/validator/tour 閘綠、fresh-eyes 審查 PASS-with-findings（2 info 全處置：F1 已修 89a93ffd、F2 rebase 吸收）、回執四欄齊（deployment-surfaces=healthy——bundle freshness 通過、skills symlink 活）。

```mermaid
flowchart LR
    cat["catalog.toml<br/>wonder identity+binding<br/>spark 原樣＋5 pending 種子"]
    skill["SKILL.md 五處同步<br/>wonder 旗艦/spark lite<br/>深推理 max＋payload 460K"]
    docs["agents+rules 對照<br/>截尾鐵證維持瘦身"]
    tests["三測試檔同步<br/>3862 passed"]
    marker["marker 補件"]
    review["fresh-eyes 審查<br/>PASS-with-findings"]
    merge["wt-close full<br/>rebase+ff-only"]
    live["live：symlink 即時<br/>bundle freshness 綠"]
    cat --> merge
    skill --> merge
    docs --> merge
    tests --> merge
    marker --> merge
    review --> merge
    merge --> live
```
<!-- SECTION:FINAL_SUMMARY:END -->
