# AIR-48 P1 鑑識腿——三面誤置 taxonomy

> 執行：lite-verify flash agent（read-only）；主 session 驗收抽樣 3 輪通過（specimen 時間線／muse-facts 多 writer 17 事件 6 sessions／desc len 190 逐一覆核吻合）。中間產物 `.agent-tmp/p1-writes-air48-*.json`＋分析腳本 3 支。
> 窗：2026-09-02 00:00 ～ 09-08 21:14（+08:00）。管線＝`memory_telemetry.py writes` 複用（rows_scanned=116,515；CC 轉錄 ai-rules 23 檔＋mosaic 249 檔 malformed=0）。

## 0. specimen 數字校正（load-bearing）

原宣稱「24＋32 呼叫≈30 Write」＝**rollout naive 字串計數的膨脹假象**（model-io 每 request 重複整段歷史，命中隨後續 request 線性膨脹——機制已三重實證還原）。**db 真值**：sess_5220505c 對兩條目各 Write 1 error＋1 completed（20:15:58 err→20:17:18 ok），全窗共 4 次寫入。**定性結論更強**：條目 `project_session-id-continuation-absorption-0908` 兩小時內 ≥5 次寫入、**≥4 個寫入身份**（6af3f89d 創建＋5220505c 覆寫＋e9d91786 Edit＋21:06 未歸因 writer〔db/CC 皆無事件——第三通道〕）、3 種路徑形態（CC 真池/zcode symlink/覆蓋外）——frontmatter 只記創建者一人。rollout 計數類宣稱自此源揮發後不可復驗——**後續歸因以 db part 表為準**。

## 1. Taxonomy

| # | 誤置類型 | 面 | 頻率 | 證據 |
|---|---------|----|------|------|
| M1 | 任務終態/進度入 memory（六問 Q1 違反） | memory | 含任務狀態 markers 條目：ai-rules 8／mosaic 30 | mosaic `project-backlog-md-integration-arc` markers=38、`feedback-interaction-style` 34＋日期流水 42；ai-rules `memory-cc-alignment` 14＋hash 引用 7 |
| M2 | desc 三不違反／>100 | memory | 現存違反：ai-rules 12／mosaic 21（>100：2 條） | `project_card-branch-rule-proposal-pending` desc=190（驗收覆核✓）；**長度閘活著（窗內攔 39 次）、內容閘（日期/session id）不存在**——31 條日期流水 desc 全放行 |
| M3 | 多 writer 草稿式迭代 | memory | ≥2 獨立 mains：ai-rules 60（31 現存＋29 已刪）／mosaic 64；寫入事件 378ok/88err＋469ok/160err；**stale-collision error 13 次** | top：`muse-code-cli-facts` 9 mains（抽查覆核：17 事件/6 raw sessions✓）；爆寫波 18+22 波（極端 27 條目/2 秒） |
| M4 | repo 可推導佔主體 | memory | 抽樣：mosaic 2 條高置信 | `reference-zcode-memory-generator`（描述 ai-rules 的 generator 機制）；`reference-zcode-platform` 40.8K |
| B1 | 無承諾源變更（scope creep） | bundle/rules/skills | 窗內 bundle 觸及 104 commits；抽驗 3/3 可溯源（任務家 EP 承載） | **未發現確證 scope creep**——但書：63 無標記 commits 未逐條抽驗 |

## 2. SM-5 歸因破口（量化）

frontmatter `originSessionId` ≠ 窗內末位 writer：**ai-rules 71/128、mosaic 73/106**——破口是常態不是例外。池拓撲勘誤：CC 路徑是真池目錄、zcode 路徑是 symlink——同實體雙寫入路徑並存，加劇歸因破碎。完整清單 `.agent-tmp/p1_air48_analysis.json`。

## 3. 預設路徑改道評估

- **可解（高置信）**：M1/M3 的任務狀態面——三個 specimen writer 同 session 內本來就在寫卡/EP（cwd=repo、backlog CLI 在手），正確載體**同等可達**；寫 memory 是習慣非距離被迫。**摩擦不對稱實證**：MEMORY.md 直寫窗內 0 次（既有 hook 完全威懾）、desc 長度閘攔 39 次——**hook 在已實裝的面有效；缺的是「該不該進池」放置閘**。機械可先行：desc 日期/session-id 內容閘＋stale-collision（13 次）作觸發點。
- **不可解（需語義）**：Q1 邊界與 repo 可推導判定——hook 只能提示，P2 定義表職責。

## 4. 覆蓋率

已查：zcode db part/session（116,515 rows）、CC 轉錄兩池、池實檔 mtime×frontmatter、git log 104 commits。**揮發**：rollout（5220505c 已清；**e9d91786 rollout 於分析進行中當場消失**——揮發窗即時目擊；存活僅 3 檔高輪轉）。**未覆蓋**：muse/codex CLI harness 寫入（第三通道實證存在——21:00 後 mtime 變更無 db/CC 事件）、bash 直寫（specimen 創建 Write 未見於 db）。
