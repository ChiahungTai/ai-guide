# Work Order — AIR-42.1 S1/S2 review（read-only docs profile）

> review variant（`skills/_common/work-order.md` 替換語義）：read-only、無預期改檔。範圍＝S1 advisory＋S2 規則修訂 diff。

## 1. 紅線

- read-only：禁任何寫入（git/卡狀態/產物落檔）；結論只在最終回覆承載
- 禁工具輸出寫 repo 外；中間筆記不留檔

## 2. 目標

AIR-42.1（memory 載體分流校準，docs-mode）S1+S2 落地審查：S1 產出 `routing-advisory.md`（10 條樣本判讀）；S2 修訂 memory-audit SKILL 四處＋context-management rule 瘦身。驗證判讀證據鏈與規則修訂是否符合 EP S2 要點。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 WT）；HEAD `3cc3284`
- dirty：`M rules/context-management.md`、`M skills/memory-audit/SKILL.md`、untracked `ai-analysis/_tasks/09-07-memory-governance/knowledge-routing/routing-advisory.md`（本工單亦 untracked）

## 4. 必讀

1. EP：`ai-analysis/_tasks/09-07-memory-governance/knowledge-routing/ep.md`（S1/S2 要點＋K1-K9 情境）
2. S1 產物：`ai-analysis/_tasks/09-07-memory-governance/knowledge-routing/routing-advisory.md`
3. S2 diff：`git diff rules/context-management.md skills/memory-audit/SKILL.md`
4. 證據源：`../evidence/reads-post-i1234.json`（inventory SHA/zero 候選）、`../evidence/weekly-20260907.json`（寫入流量）
5. 對照 rule：`rules/edit-discipline.md`（no-backward-compat 承載）、`rules/model-routing.md`（tier 句承載）
6. 方法論：`skills/review-engine/SKILL.md`

## 5. 已決策（勿重辯）

- advisory only——不改共享 memory 池（無授權）；退出候選交 user 裁
- mem-distill role 終態句**判保留**（身份聲明非歷程流水——蒸餾形態需要）
- rule 瘦身＝程序細節單一源在 skill（寫前載入）；「rule 缺就補 rule」改「先判用途與最小範圍」
- 矛盾例外：發現實作/條文/EP 互相矛盾 → 停下舉證（file:line＋逐字）

## 6. 範圍限定

動＝零；不動＝全部（含卡狀態）——`git status --short` 前後一致舉證。

## 7. 工具接線

bash（cat/rg）/Read；可跑唯讀驗證（無需 pytest——docs mode）。禁 code-reality 寫入面；禁輸出寫 repo 外。

## 8. 驗收（逐條實跑）

1. `rg -n 'rule 缺就補 rule' rules/ skills/ agents/` → 零命中（舊句移除）
2. `rg -n '寫入端紀律' rules/context-management.md skills/memory-audit/SKILL.md` → rule 引用＋skill :113 段在場
3. advisory 判讀抽驗 ≥3 條：#4 no-backward-compat 的 `rules/edit-discipline.md:11,18` 承載屬實？#5 tier 句 `rules/model-routing.md:16` 屬實？#7 settings-sync 在 `skills/code-review/SKILL.md` 真零承載？
4. advisory 觀測誤差段（流量vs存量 join、window_shortfall）與 `../evidence/reads-post-i1234.json` 的 coverage 一致？
5. `rg -n 'AIR-42.1' skills/memory-audit/SKILL.md` → 修訂處標記在場（Q1 blocker 拆解/Q2 用途先判/固化分層/cluster 同召回情境）
6. `git diff --name-only -- hooks/` → 空（無新閘門）

## 9. 證據紀律＋PII 禁令

每條宣稱附命令＋原始輸出；PII 禁。

## 10. 交付報告格式

1. S1 advisory：verdict（可信/有缺陷）——抽驗條目證據鏈核對、分流建議合理性（K1-K9 對照）、觀測誤差如實性
2. S2 修訂：與 EP S2 要點逐條對照（Q2 用途先判/固化分層/blocker 拆解/cluster 判準/rule 瘦身）＋單一源方向核對（rule 不再重述程序細節）
3. 新發現 findings：嚴重度＋file:line＋信心＋remedy 三分類
4. 總結論：通過／不通過
