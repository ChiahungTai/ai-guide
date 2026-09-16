# AIR-48 P2 統一定義表 v1——審計副本

> 本體落點＝`skills/memory-audit/SKILL.md`「載體統一定義表」節（單一源）。本檔是審計副本：設計決策記錄＋Decoder test 反查記錄＋修改面清單——驗收材料，不承载判準本身（判準以本體為準）。

## 1. 設計決策記錄（含取捨理由）

| # | 決策 | 為什麼（含被排除方案） |
|---|------|----------------------|
| D1 | 定義表落 memory-audit skill、放「寫入端紀律」段**之前** | EP 既定落點；動線＝查「該寫哪」先見廣域表（九載體），落 memory 才進寫入端紀律（六問/預算）——廣→深。查詢場景多數源於「要寫 memory 嗎」瞬間，表放寫入閘門最近處 |
| D2 | instruction-writing 四行決策樹表格**搬走**、留 hook 三判準論證＋指針 | 合一的對象是「表」（查詢視圖），不是論證——三判準論證（假確定性比真語義危險）＋對照組是撰寫治理方法論，屬 instruction-writing 職責。表單一源＝memory-audit；論證單一源＝instruction-writing，互指不重複 |
| D3 | prompt/LLM 流程**不列表行**、只進一行流機制入口 | 它是執行編排不落檔：零 context 佔用、無寫入面、無稀缺層抉擇——列表行會製造「它也是存放載體」的誤讀 |
| D4 | 放置閘（M1 處置）＝**提醒注入**非判斷攔截 | P1 實證 Q1（任務終態判定）是語義——hook 三判準不全，硬擋＝假確定性。注入指針無擋/放決策（零誤判面），純機械——合乎 hook-vs-LLM 分工。P1 證據：正確載體同等可達（習慣非距離），故「寫入瞬間歸零指針距離」是對症設計 |
| D5 | desc 內容閘（M2 處置）＝**可硬擋**（三判準全過） | regex 可決定（日期/`sess_` 形態）、入口單一（既有 `block-memory-index-write.py` desc 檢查同路徑）、無語義例外（desc 三不明文禁止）——與放置閘的語義面形成對照，正是 D4/D5 差異展示三判準的用法 |
| D6 | M3 處置掛 stale-collision 訊息擴充 | collision error（P1 實證 13 次）是唯一機械可見的多 writer 觸發點；新建放置閘攔不到既有條目加段迭代——兩閘互補覆蓋 M1（新建面）與 M3（迭代面） |
| D7 | 工具層明確「不做」 | memory 寫入是 harness auto 行為非 CLI 入口，包裝不可行；卡側 backlog CLI 已在場（P1：正確載體同等可達）——記錄排除理由防重提 |
| D8 | B1 處置＝維持雙 ref | P1 未發現確證 scope creep（104 commits 抽驗 3/3 溯源）——無誤置不設計新機制（YAGNI） |

## 2. Decoder test——P1 taxonomy 全案例反查定義表

> 驗收判準：每個誤置案例反查定義表，答得出「該寫哪、為什麼」。反查路徑一律走「該寫哪（一行流）」知識入口。

| P1 案例 | 一行流查詢點 | 判決（該寫哪） | 為什麼 |
|---------|------------|--------------|--------|
| M1：mosaic `project-backlog-md-integration-arc`（markers=38 日期流水） | 「任務終態/進度 → 卡 notes／EP 進度節（永不進 memory）」 | 卡 notes／EP | 38 個 markers 是弧歷程 session 流水——任務綁定資訊，session 完結後 recall 價值歸零；卡/EP 是該弧工作單元，自然承載 |
| M1：ai-rules `memory-cc-alignment`（markers=14＋hash 引用 7） | 同上＋「repo 可推導 → 不寫」 | 卡 notes；hash 引用刪（git log 可查） | 進度 markers 歸卡；commit hash 屬 git 可推導事實，desc 三不也禁 |
| M2：`project_card-branch-rule-proposal-pending` desc=190 | 「任務終態/進度 → 卡」＋desc 不放易變快照（表 M2 行） | 弧狀態歸卡 desc/notes；desc 壓回 ≤100 條件句 | desc 記「09-08 進行中」類現值＝易變快照；且「proposal-pending」是承諾/待辦——一行流「承諾→卡」 |
| M3：`muse-code-cli-facts` 9 mains 17 事件（6 sessions） | 「暫存/草稿 → scratch」＋表 scratch 行「草稿迭代住這」 | 迭代過程 → scratch／卡；條目只收終態 facts | 9 個 session 對同一條目反覆寫＝草稿式迭代；「寫入當下即蒸後形」（寫入端紀律）要求每次寫入已是終態——違反即 M3 |
| M3：爆寫波 27 條目/2 秒 | 同上 | 批次結果 → EP 進度節／報告 | 2 秒 27 條是機械批次傾倒，非逐條教訓產生——弧產物形態，任務家承載 |
| M4：`reference-zcode-memory-generator` | 「repo 可推導 → 不寫」 | 不寫；模組操作知識 → 模組 AGENTS.md | generator 源碼＋註解在場（M4 證據：描述其機制）——repo 即真值源；若屬某模組反覆需要的操作約束，模組 AGENTS.md 3-6 行 |
| specimen：session-id 弧條目 2h≥5 寫入≥4 身份 | 「任務終態/進度 → EP 進度節」＋寫入端紀律「進行中弧線條目禁加段」 | 弧線進度 → EP 進度節（即時落盤既有機制）；弧結案一次蒸餾入 memory | ≥4 身份接力寫=弧線未收案的多 writer 迭代；context-management rule 既有「想法即時落盤 EP」正是正確載體 |
| B1：bundle 104 commits 抽驗 3/3 溯源 | （無誤置——反向案例） | 變更承載 → EP/卡（現行有效） | 定義表回答「為什麼 bundle 乾淨」：ai-rules 的變更治理本就以 EP/卡為承諾源（雙 ref 紀律）——機制在場且有效，維持 |
| SM-5：originSessionId ≠ 末位 writer 71/128＋73/106 | （缺口非誤置——表列「—」） | 修法建議 → P5（條目 writer log 行／telemetry 擴欄／generator 註記） | 歸因可見性是基礎設施缺口不是放置錯誤——定義表不裁決，移交 P5 設計產物 |

**反查結論**：9/9 案例定義表答得出「該寫哪、為什麼」；其中 SM-5 正確識別為非誤置（缺口），B1 正確識別為無誤置（維持）——表不過度擴權。

## 3. 修改面清單（本段落落地檔案）

| 檔案 | 變更 | 性質 |
|------|------|------|
| `skills/memory-audit/SKILL.md` | 新增「載體統一定義表」節（交叉表＋一行流＋誤置→處置＋寫入摩擦設計，165→204 行）；層 3 收斂落點改指針；六問 Q6 改指針；description 觸發詞擴 | 本體（單一源） |
| `skills/instruction-writing/SKILL.md` | 「載體決策樹」段→「載體選擇」：四行表格移除（入統一定義表）、保留 hook 三判準論證＋對照組、加指針 | 指針改造 |
| `AGENTS.md` | 寫作治理第 2 點：指針改「統一定義表見 memory-audit＋hook 論證見 instruction-writing『載體選擇』」 | 引用同步 |
| `rules/context-management.md` | Memory 生命周期規範 pointer：加「該寫哪＝memory-audit『載體統一定義表』」＋觸發詞「該寫哪」 | 引用同步 |
| 任務家 `index.html` | hook 1 補殼（骨架＋P1 結果章節＋degraded 圖槽登記延後項）＋卡 ref 換殼 URL | 殼 |

**未動**（鎖定面）：`deploy_agents.py` 與 bundle 邏輯（EP：本弧原則上不動 bundle 內容；rules/ 變更的部署同步走收尾鏈）；歸檔歷史（done EP、completed 卡）不追改。

## 4. 與 P3 的交接面

- P3 B 切換＝定義表首次執法：`_resident-set.md`（常駐清單檔）是「memory 條目」行稀缺層（索引常駐＝定額）的實作載體——表不變更，切換只是把表的常駐語義落到 generator。
- 內容閘（M2）與 collision 訊息擴充（M3）已過三判準驗證，實作建議掛 P3 之後另裁（本弧 P2 只設計）；`_inventory.md` 手寫防護＝P3 既有實作項（EP P3⑤）。
- P4 dogfood 的「找不到」事件將回餵定義表 v1.1——表設計已預留演進位（versioned：v1）。
