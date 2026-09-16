---
id: AIR-111
title: >-
  EP 載體四層分級——standard=card Planning Contract＋parent EP inheritance＋promotion
  ladder
status: Done
assignee: []
created_date: '2026-09-16 10:15'
updated_date: '2026-09-16 11:50'
labels: []
dependencies: []
references:
  - ai-development-guide.md
  - skills/execution-plan/SKILL.md
  - skills/_common/work-order.md
ordinal: 96000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
codex session 01a0a93f 研究（兩條 muse 研究腿＋user 拍板）收斂：EP 載體四層模型——simple=card AC 直行／standard（跨檔、無新 boundary 決策）=card Planning Contract（六欄：Baseline＋已決策＋Scope＋Scenarios＋Integration＋驗證式）／full/boundary=standalone EP／parent EP bounded child=引用 parent EP＋contract。加 promotion ladder（實作中發現新 boundary 決策→升 EP amendment/子 EP）。落點：execution-plan 流程規模分級＋guide 規模句＋work-order §8＋drift scan 同步。boundary 級控制面變更（AIR-105）：bi 審查（codex＋flash）＋GLM-5.3 judge＋回執四欄＋card WT 隔離 authoring。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【checkpoint 0916 18xx】codex 01a0a93f 研究接手：四層模型已凍結（simple 直行／standard=Planning Contract 六欄／full/boundary=standalone EP／parent-EP bounded child=引用+contract；promotion ladder）。AIR-111 建卡 9a0fb62＋開工 a86bdf7（特赦①②）；card WT ~/Github/ai-guide-air-111（branch air-111 @ a86bdf7）。實作腿已派：impl-lite（glm-5.3-flash，ArcOverride user「改用FLASH回到原本模式」），agent_d331e367，spec=十節工單（A execution-plan 四層表+六欄+promotion／B guide 視模句／C work-order §8 規劃載體前置 pointer／D drift scan）。待辦：回收→我獨立驗收→flash 審查腿（fresh context）+codex 外審腿（bridge review --base main，路徑已解析 delegate/2.0.12/bin）→GLM-5.3 judge（bridge --model GLM-5.3 read-only）→修正迴圈→GREEN probe（behavior scenario control/treatment）→consistency 逐檔→commit gate（user）→merge+deploy+回執四欄。分類=boundary（記錄於本 notes）；落地前審查閘腿齊前不 merge 不 deploy。

【checkpoint2 審查腿回收】codex intent 腿（job-mu3ypk35-8coz94，chatgpt-web/high）：needs-fix 0C/4I/1Minor。C-01 promotion 判準窄於 full trigger（消費者契約/invariant 涵蓋不了新 module responsibility/dependency direction）→對齊 full 判準。C-02 standard 已決策欄無 provenance 要求→agent 可 contract 內做 boundary 決策再標已決策→要求 boundary 決策錨定卡前已接受 authority；unresolved/new→contract 成立前即 promotion。C-03 guide/skill classifier 雙寫且有判準差異（skill 多架構/跨模組/🔴；跨模組無 boundary 歸屬無 precedence）。C-04 Minor：「開卡」應為建立或更新 owning 卡；跨檔 refactor 語義掉了。C-05 bounded-child gate 誤把 parent accepted 當充分條件→改 decision-ownership 判準（child 所需決策全由 parent 定案可 anchor）。我的初步 disposition（待 judge 裁）：C-01/02/05 照修；C-03 折衷——guide 是 always-on bundle 必須自足承載分級（消費端未必載 skill），修法＝兩處判準關鍵詞逐字對齊＋表格列序即 precedence＋把 guide↔skill parity 登記 check_single_source.py REGISTRY 機械閘（codex 建議的投影會破壞 always-on 自足性）；C-04 照修。等 flash fresh 腿（agent_dd6cb701）→GLM-5.3 judge 消費雙腿。

【checkpoint3 雙腿齊＋judge 派出】flash fresh 腿（agent_dd6cb701）：needs-fix 0C/5I/5m。Important：F-01 kanban:135『PLAN 不寫進卡唯一源=EP』與 :120 新句同檔矛盾／F-02 standard 執行載體未閉環（implement 階段0 predicate 全以 EP ledger 為前提、5a 情境矩陣無 standard 情境——近 Critical）／F-03 promotion 觸發集漏 architecture（≡C-01 兩腿獨立收斂）／F-10 ep_type 表:47『implementation 適用小型/單一中型』與四層表同檔相反／F-11 frontmatter 觸發面過寬。Minor F-04~F-09（驗證式vsAC雙源、full/boundary 並列名、standard+ 記號、deep-work/spec/zoom 殘留二分）。程序註記：flash 腿兩起 READ-ONLY 違規自曝＋已復原（暫存檔/.venv 皆刪）。judge 已派：GLM-5.3 顯式（job-mu3z92mo-r79ow8，plan read-only，Arbiter），卷宗 .agent-tmp/air111-judge-brief.md（雙腿 findings＋orchestrator 預 disposition：C-03 折衷——guide 自足性優先、關鍵詞逐字對齊＋列序 precedence＋parity 登記機械閘；F-02 傾向 option A 本弧補完整閉環）。裁決回來→修正迴圈→GREEN probe→consistency。

【checkpoint4 judge 裁決】GLM-5.3（job-mu3z92mo-r79ow8）：accept-with-fixes，16 項修正工單（卷宗 air111-judge-brief.md／裁決 air111-judge-out.md）。裁量點全定案：C-02=雙防線（成立時 provenance gate 落第2欄＋實作中 promotion 觸發集對齊 full）；C-03=orchestrator 三件套、③REGISTRY 登記記 followup 不入本弧（scripts/ 範圍外）；F-02=option A（implement 階段0 加 contract 分支＋5a 補 standard 結算情境——modified 檔 4→5 正當擴弧）；minors 全修。免二輪外審判準：16 項逐項機械複驗＋kanban 矛盾掃描＋guide↔skill 判準 diff 對照＋禁區檢查＋bundle gate 實跑。修正迴圈已派 flash（fresh impl-lite）；#16 followup 由主 session 記卡：guide↔skill classifier parity 登記 check_single_source.py REGISTRY（PENDING，scripts/ 弧外）。

【checkpoint5 修正迴圈收＋末驗證波】修正迴圈 15/15 落地（8 檔：原 4＋implement/deep-work/spec/zoom）。我的獨立複驗：錨點全數重現（provenance anchor/評估順序/contract 分支/PLAN 不寫進卡 full tier 限定/full/boundary=0/standard+=0/開卡→建立或更新/Skip if）、8 檔零禁區、核心節眼見合格、guide↔skill full 判準 8 關鍵詞逐字一致、writer 兩偏差皆 benign（spec 指路句插列舉滿足驗收字面；zoom 第4欄 registry 重複留原樣）。bundle gate dry-run 綠（zcode/codex 35%、muse 87% WARN＝既有 slimming 追蹤項）。末驗證波已發：4 probe（S1 跨檔無 boundary→應答 contract；S2 收斂卡＋無 anchor state ownership 新決策→應答 promotion 到 full；control=舊文/treatment=新文，fresh flash 各測）＋2 consistency（execution-plan 單檔＋guide 等六檔）。齊後：probe 判讀→（綠）提案 commit＋結案兩步＋回執四欄。判讀欄位：S1t=Planning Contract PASS／S1c=寫 EP（旧行為基線）／S2t=promotion-full PASS／S2c=模糊或照卡（重演研究實錄）。

【checkpoint6 probe GREEN】4 probe 判讀齊（fresh flash、control/treatment 各測、rep=1/臂如實註記、A 軸證據）：S1c=更新既有卡無規劃結構要求（舊缺口本體）→S1t=card Planning Contract 六欄 PASS；S2c=照卡直行（逐字重演研究文檔失敗——新 state ownership 決策被吸收進卡內決策紀律）→S2t=full/standalone EP PASS（且正確消費 precedence：跨模組開工前可知→一開始就 full；promotion=第二防線；user 拍板≠載體夠用）。behavior GREEN 達成。剩 2 consistency 腿（execution-plan＋guide 等六檔）→齊後 commit 提案。

【checkpoint7 consistency 兩腿＋終掃派出】execution-plan 腿：F1 desc 舊觸發面（judge 單#8 寫 desc/when_to_use，writer 漏 desc——真漏）／F2 大型/中型必填族十餘處殘留／F3 blueprint 裸中型變更（guide 連結斷鏈——新規模句已無中型變更定義）／F4 存量三項實列四項。六檔腿：G-F1 metadata-sync 結算情境矩陣單一源仍 A-D（implement:314 指名單一源、E 只加在 implement 端——single-source drift 本體）／G-F2 implement:380 列舉漏 E／G-F3 kanban:69 豁免只點 simple／G-F4 zoom:117/140 舊二分殘留／G-F5 kanban:120 全形＋形似退役記號；G-F6/7/8 資訊級記錄（一 EP=session bounded child 張力、implement:34 qualification token、work-order 列舉不窮盡——皆不阻落地，記卡）。終掃工單已派 flash（10 項，9 檔面）。收後：我複驗→commit 提案。

【checkpoint8 終掃收＋回執】終掃 21 處（flash）＋marshal 殘尾 13 處直收（執行-plan 測試規劃段/收尾 5a-5d/simple 變更段、metadata-sync C 列+finalization 表 E 納入+存量斷引「小型變更不需 UC」→「小 bug/doc 免 UC」、implement 強制#6）——9 檔面。殘留掃描零、bundle gate 複跑綠。**回執四欄**：classification=boundary（UC 規模分級＝decision/gate 面，記錄於本卡）；review=bi（muse→flash，ArcOverride user「改用FLASH」）——flash fresh 腿（agent_dd6cb701，0C/5I/5m 全採）＋codex intent 腿（job-mu3ypk35，0C/4I/1m：4 照修/C-03 折衷裁定）＋GLM-5.3 Arbiter（job-mu3z92mo，accept-with-fixes 16 項）＋機械複驗（錨點/殘留/禁區/bundle）＋behavior GREEN probe 2 情境（S1t/S2t PASS、S2c 重演基線失敗；A 軸）＋consistency 雙腿（發現殘留全清）；session-freshness=fresh（全程載 instruction-writing/model-routing/instruction-testing，governing docs 無中途變更）；deployment-surfaces=gates dry-run 綠（zcode/codex 35%、muse 87% WARN＝既有 slimming 追蹤項）、實際 deploy pending merge。PENDING followup（記錄在案）：①guide↔skill classifier parity 登記 check_single_source.py REGISTRY（scripts/ 弧外）②G-F6 一 EP=session bounded-child 張力③G-F7 implement:34 qualification token ④implement/metadata-sync 殘餘大型/中型詞彙（spec/deep-work 自有 Phase 軸屬合法）。待 user commit gate。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
EP 載體四層分級落地（30bab35→f3db408 進 main）：simple 直行／standard=card Planning Contract 六欄（provenance gate 防先決策後標案）／full=standalone EP／parent-EP bounded child=引用+contract；promotion ladder 雙防線。9 檔（execution-plan/implement/metadata-sync/guide/kanban/work-order/deep-work/spec/zoom）。鏈：flash 實作→flash fresh＋codex intent 雙審（9I 全採）→GLM-5.3 Arbiter 16 項修正→behavior GREEN probe（S1/S2 PASS、control 重演基線失敗）→consistency 雙腿殘留全清。回執四欄見卡 notes checkpoint8。followup：guide↔skill classifier parity 登記 REGISTRY（PENDING）。
<!-- SECTION:FINAL_SUMMARY:END -->
