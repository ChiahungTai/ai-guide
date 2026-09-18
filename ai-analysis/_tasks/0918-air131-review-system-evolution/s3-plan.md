# S3 Planning Contract——code-review --arc mode（AIR-131 blueprint child）

- **parent**：`ep.md` §2-2/§2-6/§4-S3　**baseline**：card WT air-131（S1/S2 已結算）
- **變更檔**：`skills/code-review/SKILL.md`（單檔——A3 套入演練 PASS：六要素映射既有結構錨點，無需新 skill）
- **AC 對應**：EP §6-③（行為 predicate：lanes stop 可機械判、guard 四項齊、cadence 數字與 §2-2 一致）

## 交付物

`code-review` 新增 `## --arc mode` 段（置於審查模式選擇之後、六軸之前）：scope（baseline..tip＋final-state invariants）、multi-leg risk-driven lanes＋convergence stop（三量）、convergence judge（judge-review）、consumer probes（§2-4 corpus 接線）、cadence（§2-2 全數字＋review-power guard 四項）、與 state-review 邊界（不合併）。

## 不做

- 不動 A/B 載體配置與六軸定義（--arc 是 scope 變體非新 ontology）
- orchestration 指針歸 S4（deep-work）——本段只留被觸發的執行契約
- consumer-dryrun-corpus 檔歸 S5——本段引用其契約名

## A3 套入演練留痕（PASS）

六要素→既有結構錨點映射：scope（既有審查範圍節的用法表形態——新增 --reheat 列）／lanes（A/B 載體 legs 與六軸衍生）／convergence judge（judge-review 既有鏈）／consumer probes（§2-4 corpus 契約名）／cadence（§2-2 數字）／與 state-review 邊界（既有不相併條文引用）。結論：skill 內擴充 `##` 節即可承載，非 EP A3 kill 條文所指的「新 skill／新 top-level ontology」——A3 不觸發。
