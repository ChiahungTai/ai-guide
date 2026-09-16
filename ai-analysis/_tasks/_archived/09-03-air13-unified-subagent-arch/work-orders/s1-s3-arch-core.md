# 工單：統一 external-runtime subagent 架構三層核心文檔（S1+S2+S3）

> 定位：修訂 ai-rules 的 model-routing 路由文檔、agents registry 治理段，並新建 foreign-runtime 工單模板。本工單自身即新模板形態的首個樣本（十節結構）。

## 紅線（違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡——止步於 working tree 編輯
- 只准動「範圍限定」節列出的 4 個檔案；其餘一律不碰（尤其 `agents/zcode/*.md` 定義檔、`rules/tool-discipline.md`、`skills/CLAUDE.md` 以外的索引檔）
- 禁把產物寫到 /tmp 或 repo 外；中間筆記不留檔
- 新增文檔內容禁版本號／日期／統計數字（元資訊禁止，見 rules/instruction-writing.md）
- model id 與容量數字**不得**出現在 rule／registry／模板層——只能住在 skills/model-routing/SKILL.md 解析表

## 目標（一句話）

把「三家族（GLM in-harness／muse／codex）委派路由」制度化為三層：routing 表（model-routing）＋flag profile（agents registry）＋工單模板（_common），EP 的 S1/S2/S3 三段一次落地。

## Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree，非 worktree）
- base commit：`63f2041`
- 並行改動聲明：working tree 已有本弧的 backlog 卡修改（staged）與任務家 untracked 檔案（`ai-analysis/_tasks/09-03-air13-unified-subagent-arch/`）——這些屬本弧正常狀態，不屬你的清理範圍

## 必讀（按序，絕對路徑）

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-03-air13-unified-subagent-arch/ep.md`——只讀「核心原則」「S1」「S2」「S3」四段＋「EP Review Findings」表中 M-F1/C-R1/C-R4/C-R5/M-F2/M-F3/M-F13 七列（這些是本工單規格的直接來源）
2. `/Users/ctai/Github/ai-rules/rules/model-routing.md`（全文——你將擴充它）
3. `/Users/ctai/Github/ai-rules/skills/model-routing/SKILL.md`（解析表結構）
4. `/Users/ctai/Github/ai-rules/agents/AGENTS.md`（治理段現況）
5. `/Users/ctai/Github/ai-rules/skills/_common/state-md-write.md`（只看檔頭——`_common` 層慣例＝`# 標題`＋blockquote 定位句，**無 YAML frontmatter**）

## 已決策（勿重辯）＋矛盾例外

以下已定案（三臭皮匠＋雙 ep-review＋user 裁定），不要重新設計：

1. 落點：external-runtime routing 進 model-routing（rule 精簡＋skill 解析表），不另開新 rule/skill
2. thin forwarder 維持——不新增任何 agent 定義檔
3. 兩層契約：解析表=權威值唯一落腳；`agents/zcode/` pin=既有允許 materialization（本次不動它們）；新內容 family/profile-only
4. 模板十節結構與節名照 EP S3 修改要點
5. family 表的角色與拆名（external second-opinion review vs in-harness acceptance reviewer）照 EP S1

**矛盾例外**：若你發現現有檔案內容與上述決策具體衝突（如同段已有矛盾的既定義），停下來在報告中舉證，不要自行改設計。

## 範圍限定

- 動：`rules/model-routing.md`、`skills/model-routing/SKILL.md`、`agents/AGENTS.md`、`skills/_common/work-order.md`（新建）
- 不動：其他一切

## 工具接線

- 讀查：bash（cat/rg/ls）。字串搜尋一律 rg
- 禁 code-reality 寫入面（build/snapshot/delta_tour/project）；查詢面可用可不用（本工單純文檔，大概率用不到）
- 禁把任何工具輸出寫到 repo 外

## 驗收（命令＋預期結果，逐條實跑）

1. `rg -n "external-runtime" rules/model-routing.md` → ≥1 命中（新節存在）
2. `rg -n "eligibility" rules/model-routing.md` → 命中（五條 gate 段在場）
3. `rg -n "needs-fix" rules/model-routing.md` → 命中（reviewer 契約含三態 verdict）
4. `rg -n "flag profile|thin forwarder" agents/AGENTS.md` → 兩詞皆命中
5. `test -f skills/_common/work-order.md && rg -n "紅線|Baseline|矛盾例外|PII|交付報告格式" skills/_common/work-order.md` → 檔在且五關鍵詞皆命中
6. `head -3 skills/_common/work-order.md | rg -c "^---"` → 0（無 YAML frontmatter）
7. 負向（family/profile-only）：`rg -n "muse-spark|gpt-|glm-" rules/model-routing.md agents/AGENTS.md skills/_common/work-order.md` → 零命中（**注意 skill 檔不在此列**——解析表允許 model id）
8. `rg -n "external-runtime" skills/model-routing/SKILL.md` → ≥2 命中（解析表新段＋frontmatter description 觸發詞同步）
9. `rg -n "model-routing" rules/AGENTS.md` → 讀現況並在報告列出（本次不改它——收尾段另段處理，此處只回報）

## 證據紀律＋PII 禁令

- 每條驗收附完整命令與原始輸出（截斷標明）
- 報告中禁出現任何 email／人名等 PII
- 宣稱「沒改 X」須附 `git diff --name-only` 輸出佐證

## 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單（對應 git diff）
2. 逐段落落實說明：EP S1 三塊／S2 兩點／S3 十節各落在哪
3. 驗收 1-9 命令與輸出（原始）
4. 偏差記錄：與 EP 規格有任何出入處＋原因
5. 未驗證項／被阻擋項
6. 建議 reviewer 聚焦點（你最有信心不足的地方）
