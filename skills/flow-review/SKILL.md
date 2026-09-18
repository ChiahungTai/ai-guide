---
name: flow-review

description: "定期讀 ai-analysis/flow-feedback/ 累積回饋，找重複摩擦 + 聚合 type-2 設計缺陷 + memory-routing 判定（程序記憶→Skill / 專案記憶→STATE / 一次性→棄）+ Skill 兩層判定，跟 user 討論怎改善 skills/commands。/flow-review [--since <date>]"
when_to_use: "Periodic review of accumulated flow-feedback. User fires when they have time. LLM globs all feedback files, finds recurring friction (systemic) + aggregates type-2 design-flaw candidates, then discusses improvement directions with the user. B-axis: human judgment drives the improvement decisions. Output → /execution-plan (big change; /spec to clarify requirements if needed) or kanban card (small change) → /implement."
argument-hint: "無參數讀全部 / --since YYYY-MM-DD 限定日期後"
allowed-tools: ["Read", "Grep", "Glob", "Bash"]
---

# /flow-review — 摩擦回顧 + 改善討論

> **核心理念**：演化迴圈的**討論端**。讀累積 flow-feedback → 找 pattern → 跟你討論 → 改善決策。深度反思在這裡（human-in-loop, B 軸）。

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則

---

## 流程

### 1. glob 回饋
`ai-analysis/flow-feedback/*.md`（或 `--since <date>` 限定）。若空 → 本期無素材可審——素材以手寫 `ai-analysis/flow-feedback/*.md` 進池（前收集器 skill `/flow-feedback` 已退役）。

**friction 三行入口（AIR-131——append-only 低儀式）**：繞閘/workaround 當下手寫一筆進 `ai-analysis/flow-feedback/`，三行——**時間＋哪條規則＋怎麼繞的（附 context：repo/harness——兩獨立 contexts 判定必需的 provenance）**（免 type 分類、免 counterfactual——高儀式入口是零消費的病因之一；分類由本 skill 聚合時判）。同一 workaround 在**兩個獨立 consumer contexts 再現→ 自動升 type-2 候選**（設計 smell）；跨 repo/harness 重現＝更強證據（非必要條件——同 repo/harness 的兩個獨立 context 也算，codex finding：禁收窄）。

### 2. 聚合分析
- **重複摩擦**：同一 command/skill 跨多筆反覆出現 → **系統性問題**（單次 = 偶然，重複 = 該改）
- **type-2 聚合**：跨筆的設計缺陷候選合併、強化
- **摩擦 heatmap**：哪個 command/skill 最多摩擦（tags 聚合——三行入口未帶 tags 時，由聚合時推斷補標）

### 3. memory-routing 判定（教訓→記憶去向）

聚合分析後、action-routing（決策段）前，先判**教訓的記憶去向**——與 action-routing（共識→EP/kanban/留）正交兩軸，**先判記憶去向再判 action 去向**。

**機械 proxy 先判**（降隨意性）：看教訓的**引用形態**——引用具體 module/class/file path → 專案特定候選；引用工具/流程/pattern 名 → 跨專案候選。再判通用性 + 重複性。

| 教訓性質 | 記憶去向 |
|---------|---------|
| 跨專案通用（程序記憶） | **Skill**（symlink 跨專案——寫進 Skill = 自動跨專案） |
| 專案特定（專案記憶） | **STATE.md / session**（見 [context-management](../../rules/context-management.md)「STATE.md」） |
| 一次性（不再發生） | **棄** |

> **基建已在**：symlink 讓「寫進 Skill = 自動跨專案」——本步補**觸發判定**，非基建。**不替代人類判斷（B 軸）**：memory-routing 是結構化提示，最終人類討論定案（見 step 4 討論）。
>
> **STATE.md 生命週期提醒**：STATE.md 每次 session 結束覆寫——routed 到 STATE.md 的專案記憶是**下一 session 接續用**（短期 continuity，非永久）；持久專案慣例應進該專案 AGENTS.md / rule。

### 4. 討論（互動，B 軸）
- 報告聚合發現（重複 + heatmap + type-2 候選）
- **挑戰 type-1**：這真的是時機問題，還是 type-2 設計問題被誤判成時機？（防 type-1 掩蓋 type-2）
- **深 type-2**：設計缺陷確認 + 改善方向探討
- 開放討論，不急結論（可多次 review 才定案）

### 5. 決策 → 落地

| 共識類型 | 去向 |
|---------|------|
| 大改（重寫 command、新命令） | `/spec` → `/execution-plan` → kanban（建卡歸 EP UC盤點） |
| 小改（措辭、流程微調） | kanban card |
| 還沒想清楚 | 留在 feedback，下次 review 再議 |

> **歸檔生命週期**：決策且對應變更經 `/implement`→`/commit` 落地 → **收斂後結案（情境 A final 結案）** 把該 feedback 歸檔到 `ai-analysis/flow-feedback/_done/`（同 EP 歸檔哲學，見 [metadata-sync](../metadata-sync/SKILL.md) flow-feedback 歸檔項）；「還沒想清楚」留 root 供下次 review。active inbox（root）= 未結案項。

---

## 討論方法論（防退化成閒聊）

- **找重複**：單次摩擦可能是個案，重複才是系統性
- **聚 type-2**：高價值，主動追
- **挑戰 type-1**：type-1 最容易產但最淺，逐一問「這真的只是時機？」
- **不替人決定**：LLM 提素材 + 挑戰，改善決策是你的判斷

---

## 邊界

- **B 軸**：討論品質取決於你的領域判斷 + 反覆詰問（像挖既有 viewport 命令設計缺陷那樣）。LLM 是素材提供者 + 挑戰者，不是決策者。
- **不急**：累積不夠或沒想清楚，就留著下次。寧可慢，別誤改。

---

## 與其他命令

- 素材源：`ai-analysis/flow-feedback/*.md`（手寫進池；前收集器 skill `/flow-feedback` 已退役，歷史檔案仍在）
- → `/execution-plan`（必要時先 `/spec` 釐清需求）/ kanban card / `/implement`：改善落地
