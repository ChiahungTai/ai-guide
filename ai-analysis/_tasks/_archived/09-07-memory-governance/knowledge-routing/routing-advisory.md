# AIR-42.1 S1 — Memory 載體分流 advisory（樣本判讀）

> 產出性質：advisory only——只列建議不改 memory 池（本卡無共享 memory 修改授權）。SHA 取自 `../evidence/reads-post-i1234.json` inventory（2026-09-07 快照）；樣本變動即 stale 需重核。
> 讀取用途註記：本 advisory 對池條目的每次 Read 均屬**維護用途**（AIR-41 EP review finding 2 條款），不污染工作 Read 觀測語義。

## 抽樣方法（K9 有限批）

源證據：AIR-40 `weekly-20260907.json`（7 日寫入流量 top_entries）× AIR-41 `reads-post-i1234.json`（90 日窗 body Read 觀測，129 現存 entries）。選樣邏輯：四組對照——①高寫入已消失（流量vs存量證據）②現存 zero-read 候選（含已知保留反例）③命名/語義邊界④高讀健康對照。有意含反例（K6/K8），不挑最肥。

## 觀測誤差與限制（AC#3，如實記錄）

- **流量vs存量 join 誤差（本次實錄）**：top_entries（寫入事件彙總）與 inventory（現存檔案）是不同集合——top12 中 4 條（`project_code-reality-tri-track` 等）已不在池，抽樣 join 時 absent 誤顯示為 reads=0。消費 telemetry 報告時 absent≠zero-read，需先對 inventory 求交。
- **觀測窗不足**：`window_shortfall=true`（zcode 最早 08-16、claude 最早 08-12，對 06-09 窗起點僅約 22/26 天）——zero-read 候選僅證觀測窗內無 body Read，不證從未讀。
- **未涵蓋源**：codex/muse/bash-rg 三家 uninstrumented；索引注入與 rg 讀取本指標不可見（AIR-41 定義）。
- `reads_without_entry` 66 條：多為 cluster-merge 波刪除的舊名（rename/刪除線索，identity 面交 LLM HOLD——本卡不處理）。

## 逐項判讀（10 條）

| # | entry（SHA12） | 觀測 | 召回情境 | 確定事實 | 影響行動 | 當前權威來源 | 建議 | 理由（K 條款） |
|---|---|---|---|---|---|---|---|---|
| 1 | ~~project_code-reality-tri-track~~（已消失） | 寫 12.5K/7 日窗 | — | 已被 `project_cr-live-faces-roadmap` `merged_from` 吸收（含 cr-adoption-token-impact-eval、code-reality-own-graph-db、pyrefly-producer 共 4 條） | — | 後繼條目＋git log | 無動作（機制已承擔） | 任務歷程歸弧：cluster-merge 蒸餾路徑正常運作（K5 實證） |
| 2 | ~~project_backlog-md-integration-eval~~（已消失） | 寫 8.9K | — | 吸收者＝`project_ai-analysis-restructure-design`（`merged_from` 機械錨）；主題後繼 `reference_backlog-md-browser-id-mechanics` 現存（主題推斷，無 merged_from 錨） | — | 後繼條目 | 無動作 | 同上（K5） |
| 3 | feedback_no-sandbox-layer（225da825） | zero-read、mtime 06-16（無豁免） | 提寫入權限解法時 | user 拍板：sandbox 已關，禁提議 sandbox.allowWrite，走 permission list | 阻止錯誤建議方向 | 僅此 memory | **保留** | K6 反例：低 Read ≠ 低價值——user 偏好屬低頻重大約束（AIR-41 首跑已判） |
| 4 | feedback_ai-rules-no-backward-compat（2c85f8f2） | zero-read、recent | 審 ai-rules 重構提案時 | ai-rules 演化性預設不向後相容；**F7 裁決增量：不預寫未發生情境的條件式文案**（「若 X 計費則…」投機條款被否——2026-08-18，repo 零承載） | 阻止「相容保留」寫法＋阻止投機條件條款 | `rules/edit-discipline.md:11,18`（硬性條文；:62-66 例外機制） | **部分覆蓋→壓成指針保留**（review 修正：原判「退出候選」漏計 F7 增量） | K4 分層：規則主體已承載，F7 條款是行動增量——壓指針非刪 |
| 5 | feedback_capability-tier-not-model-binding（4e381062） | zero-read、recent | 討論模型 routing/治理時 | tier 綁能力檔語義不綁模型 | 阻止模型名硬編碼進治理條文 | `rules/model-routing.md:16`（完整句在場） | **退出候選** | K4 同型：rule 已含「單一源在 skill 解析表」；memory 無額外召回價值 |
| 6 | feedback-magnitude-over-precise-counts（aad28a51） | zero-read、09-04 新式命名 | 寫含 codebase 統計的文檔時 | method 如實計數與 display magnitude 分離 | 文檔顯示層避免精確整數 | `AGENTS.md`（粗版「無需精確專案數字」）；method/display 分離**無 skill 承載**（instruction-writing 零命中） | **保留** | K1/K4：repo 承載粗版，memory 細化有增量；日後可考慮細化下沉 instruction-writing |
| 7 | code-review-settings-sync（28c1f56d） | zero-read、08-24、無前綴舊命名 | code-review 收尾時 | code-review 完成後檢查 settings.json 是否同步新增 skill permission | 補齊收尾步驟 | 機械檢查在 `/sync-sources` skill（allow-list coverage invariant——本條 :16 即其抓漏實例）；**「code-review 收尾步驟」放置無承載** | **分流候選：memory → code-review skill 收尾步驟**（機械面順手跑 /sync-sources） | K2：收尾方法屬 skill 載體；memory 是錯置（advisory 提案，遷移需另授權） |
| 8 | reference_muse-code-cli-facts（fe59b2ec） | 19 reads（高）＋12.4K 寫入 | muse 委派/bridge 操作時 | CLI 事實（JSONL 面、計費、bridge 機械） | 正確派發與收法 | 本條＋repo `docs/`（獨立 repo） | **保留** | 健康對照：活躍 reference 跨 repo 事實，memory 是正確載體 |
| 9 | project_agents-registry-split-design（44a214da） | 13 reads＋19.6K | registry/dispatch 決策時 | 弧群終態＋symlink 判決**重驗中**（in-flight） | 後續弧引用 | 本條（EP :20 點名同主題） | **保留** | K4：內容仍含活躍成分；弧全閉後隨結案蒸餾（既定機制） |
| 10 | project_cr-live-faces-roadmap（777b81ed） | 16 reads＋累計寫入 87.6K（現檔 13K chars＝軟預警線 1.6×） | CR 工具鏈決策時 | 三弧終態已閉（AIR-32/33 閉合）但持續高讀 | 後續 CR 工作引用 | 本條 | **保留＋蒸餾觀察** | K5/K8：巨型終態條目——活躍度支撐保留；弧完全靜止後列夜波蒸餾（軟預警線 1.6×，靠既有機制不新增閘門） |

## 彙總

- **退出候選 1 條**（#5——rule 句完整承載且無增量；user 裁後刪，本卡不動）；**指針保留 1 條**（#4——review 修正：F7 條款增量〔不預寫條件式文案〕在條目內、repo 零承載，壓指針非刪）
- **載體遷移候選 1 條**（#7 settings-sync → code-review skill 收尾步驟；遷移執行需另授權，本卡僅建議）
- **保留 8 條**（含 2 條已消失「無動作」、1 條蒸餾觀察）——**全保留合法**（K8）：zero-read 候選中僅 #5 有 repo 完整承載證據，其餘或有用戶意志/條款增量、或無承載、或活躍
- **無新閘門**：本 advisory 不新增任何機械閘門；蒸餾靠既有夜波/rank 機制
- 樣本 hash 以 `reads-post-i1234.json` 為準，池變動後重核

## S2 修訂輸入（餵給規則修準）

- 「通用原則→rule」表述需先判**用途**（#6 型：粗版在 repo、細化在 memory 是合法分層，非 drift）
- 固化指針條件實證：#5 屬「完全覆蓋」型（rule 句完整、無增量）；#4/#6 屬「部分覆蓋」型（F7 條款/method-display 細化增量在）——退出候選只列前者；**判「完全覆蓋」前必須 rg 驗證條目 body 的每一個行動增量段**（review 修正實證：#4 初判漏計 F7 條款，險些誤導 user 刪除）
- 已消失高寫入條目組（#1/#2）證明 cluster-merge 機制承擔任務歷程回收——「歷程歸弧」條文與機制一致，無需新規則
