# STATE.md（Last session 觀察層）——定義與寫入步驟（共享段）

> 共享子範本——`/at`、`/deep-work` 在 session 結束寫 STATE.md 時引用此處，不各自重寫（DRY，防三處 drift）。本檔承載 STATE.md 的**定義**（定位 / 邊界 / 職責矩陣 / 生命週期 / 路徑）與**寫入操作**（時機 / 內容 / 邊界紀律）；rule 端 context-management 留 pointer。

## 定位（Last session 觀察層）

跨 session resume 的**觀察層**——自己續工作的 session 主觀觀察（卡在哪、為何轉向、下次起手點）。補 at 排程（Claude: `/at`；任務目標一句）/ handoff 交接（Claude: `/handoff`；外部一次性）/ kanban（任務追蹤）/ MEMORY.md（harness learnings）都沒有的：**為什麼**這樣走的 session 主觀。

**邊界（觀察層 vs 事實層，A↔C）**：

- STATE.md = **觀察層**（session 主觀：卡在哪、為何轉向）
- [autonomous-execution](../autonomous-execution/SKILL.md)「Session 級 Recovery」= **事實層**（git + EP re-derive 完成度，機械可信）
- **recovery 不依賴 STATE.md**——STATE 僅補「為什麼」，不覆蓋「做到哪」。resume 完成度以 recovery 事實為準；STATE 觀察僅供意圖參考。

**職責矩陣（防載體重疊）**：

| 載體 | 職責 |
|------|------|
| rules（always-loaded） | 通用規範 |
| MEMORY.md | harness-native learnings（harness 管理） |
| handoff（Claude: `/handoff`） | 外部一次性交接 prompt |
| at（Claude: `/at`） | 任務目標（一次性 ephemeral） |
| kanban Backlog | 任務 / 跨 session 未結案追蹤（含 Open failures） |
| **STATE.md** | **Last session 觀察（獨有）** |

## 生命週期與路徑

- **覆寫非累積**：每次自主 session（at/deep-work）結束重寫，只保留最近一次觀察；互動 session 不寫，故兩次自主 session 間的工作不記入 → 可能偏舊——但觀察層非權威，recovery 的 git 事實才是真相。首次 session 無 STATE.md = 正常，resume 跳過讀取。增長上限由 context 約束。
- **路徑**：repo root `STATE.md`（避 `.claude/` protected path——auto-mode 下寫入會被擋）；per-project 語義（每個消費專案自己的 session 觀察）；gitignore 由各專案（本地 session 觀察，default gitignore）。
- **觸發**：「離開前寫」綁 session 結束（寫入時機見下）；「開場讀」綁 resume。

## 寫入時機

session 結束離開前——**寫入**由 `/at` 排程、`/deep-work` completion report 觸發（`/handoff` 僅標示 STATE.md 非交接選項，不寫入）。

## 寫入內容（Last session 觀察）

repo root `STATE.md`，**覆寫**（非累積）。三要素：

- **卡在哪**：當前進行中、未收尾的工作點
- **為何轉向**：決策轉折理由（為何選 X 不選 Y、為何擱置）
- **下次起手點**：resume 時該從哪接、第一個動作

## A↔C 邊界紀律（negative guidance，強制）

**STATE.md = 觀察層；禁含完成度宣稱**——完成度走事實層（git + EP re-derive，見 [autonomous-execution](../autonomous-execution/SKILL.md)「Session 級 Recovery」）。「卡在哪/為何轉向」本質隱含 soft completion signal（轉向=未完成 X），resume LLM 讀到不會自發做觀察/事實區分——須嚴守：

- ✗ **不寫完成度**：「segment 3 未完成、做到一半」「段落 X done」「進度 80%」
- ✓ **寫觀察**：「retry 間隔計算產生 0，推測 BackoffCalculator 邊界條件」「改用 schema-based approach，因 Y 效能瓶頸」

> **指導非強制**（docs-mode 紀律，無 schema enforce）——誠實標記如同其他 docs-mode 強度上限宣告（指導非強制，hook 補強列未來方向）。未來機械補強方向：STATE.md schema 無完成度欄位 / resume re-derive 前不讀 STATE 的流程約束。

## Open failures 不寫此處

跨 session 未結案的 bug/failure（含 repro）→ **走 backlog**（`backlog task create` failure 卡；無 `backlog/` 的 repo 走該 repo 慣例的 pending 家），**不進 STATE.md**（board/pending 已是跨 session 未結案追蹤）。
