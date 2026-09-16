# AIR-48 P4 dogfood 首輪——B 形態行為對照記錄

> 範圍（EP P4 事先定）：N=接下來 3-5 個自然 session 或 48h 先到者；不擴成 benchmark。
> 通過判定＝**有確有知識需求案例且全部可核對軌跡下找得到**——「無 fail」不等於成功；無相關任務或觀測不足→標**未驗證**。
> 觀測限制（已知）：codex/muse/bash-rg 未 instrument——跨通道檢索以命令歷史為軌跡。
> 紅線：不動 `_resident-set.md`（凍結）；不動 generator；不為觀測造需求。
> A 期對照：P1 前的 A 形態時期檢索行為（MEMORY.md 全量開場、無 Routing）為基準——「找不到」事件與 A 期對照歸因。

## 記錄表（session 結束前 append；無需求 session 也記一行——分母）

| case | session | 確有知識需求？ | 可核對軌跡（rg/Read 命令） | 找得到？ | 用得出？ | 歸因/備註 |
|------|---------|--------------|--------------------------|---------|---------|----------|
| （例）#1 | zcode 09-09 | 是——任務涉及 X | `rg -i X _inventory.md`→Read 條目 | 是 | 是——條目教訓改變了處置 | — |
| #1 | zcode 09-08 | 是——commit 紀律＋relay 宣稱驗證 | 常駐即中（開場面：feedback_verify-wt-before-commit、feedback_relay-claims-verify-current-state）；未觸發 rg _inventory.md | 是（常駐） | 是——fresh status 對帳抓出 handoff 宣稱 9 檔→實際 staged 8 檔差異，查證歸因＝卡已被 88dc50f 帶走 | 段範圍＝handoff 接手→P3 commit；Routing 檢索路徑本段未實戰（常駐承載） |
| #1（續） | zcode 09-08 | 是——AIR-49 研究需 codex pipeline 四項實證來源與路由設計 | `rg -i "codex memories pipeline" _inventory.md` 命中→Read reference_codex-native-memory-pipeline.md | 是 | 是——四項設計（git 基線/usage 接線/注入條款/路由選項B）直接構成研究結論骨架 | inventory 首行即中；desc 條件句與任務語句同構——B 形態 Routing 路徑首次實戰成功 |
| #1（P5 段） | zcode 09-08 | 是——codex 執行旗標形態/認證拓撲/已知噪音預期 | `rg -i "codex topology" _inventory.md` 命中→Read reference_codex-config-zai-topology.md | 是 | 是——`--model gpt-5.5 -c model_reasoning_effort=low` 形態＋9×missing-content-type 噪音預期直接採用，探針一次過 | 另一發**事後諸葛**：`rg -rn` 的 `-r n` 替換陷阱踩了才想起 reference_rg-r-flag-display-replacement 在場——需求感知失敗（自認已知）非檢索失敗；recall 紀律候選信號 |
| #1（deep-work 段） | zcode 09-08 深夜 | 部分——codex 拓撲/管線條目續用（context 已在場零成本）；muse bridge ledger 探索屬新需求 | 續用＝context 內（零檢索）；bridge ledger 採 ad hoc 探索（jobs.json 直讀，3 call 收斂）——**未預先查 inventory** | 是（淺探即中） | 是——job 狀態/輸出提取成功 | bridge 探索未走 Routing 屬灰色：muse-code-cli-facts 在 inventory 但未查——損失輕（探索快）仍是「沒查就動手」信號，與 rg -rn 同型 |
| #2 | muse 09-09（AIR-50 接續） | 是——ZCode session 接續需跨 session 讀卷＋handoff 驗證紀律 | skill 經開場 catalog 直達（`read_skill zcode-session-query`，零檢索）；DB 直查（sqlite 只讀＋tail 腳本）；`feedback_relay-claims-verify-current-state` 常駐即中 | 是（常駐＋catalog） | 是——relay 驗證改變接續動作（ZCode todo＋DB 定位 S1 剩餘 debrief／review-engine 兩檔，補三處自審漏網）；載體審計：EP 進度節結算×7、卡只讀、`.review/air-50.md` 新建工作帳本（S1 契約自食）、memory 零寫入（muse 唯讀拓撲）、scratch 零落檔 | 載體觀察（非誤置）：`.review` 工作帳本載體未在統一定義表內——回餵候選，待首輪結束定案是否加行 |

## 開場煙霧（每 session 第一個回報）

| case | 開場面＝12 常駐＋Routing？ | 證據（一行） |
|------|--------------------------|-------------|
| （例）#1 | 是 | system 訊息 MEMORY.md 段含 `## Routing` |
| #1 | 是 | 開場 MEMORY.md header「B 形態——常駐定額」；常駐＝Feedback 11＋Project 1＝12 條；`## Routing` 段在（system 訊息直接可見） |

## 「找不到」事件（最高價值信號——逐案歸因）

歸因類別：清單漏列（該升常駐候選）／desc 觸發詞不配（desc 文法修正候選）／inventory 缺（投影 bug）／關鍵詞選擇問題（檢索技巧）。

| case | 找什麼 | 歸因 | 處置候選 |
| #2 | AIR-50 EP 引用的 MOS-74 followup session／job ID（`01a082f3-…`／`mtt7fkm0`）——S5 需據以改 followup 段 | 引用與 S0 參考文本對不上：`01a082f3-…` 實為 codex 跨家族複審 session（EP 另節自記）；recipe 只有 pass 6/6＋2 issue 無 ID | 未驗證不引用——followup 段照 recipe 實質寫，EP 結算行記偏差（AIR-50 弧內判例：ID 級引用須逐字可考） |
|------|--------|------|---------|

## 回餵（首輪結束時填）

> 09-09 清晨三軸回測預填（A 期基準對照腿＋decay 參數校準——完整報告 `.agent-tmp/replay-*.md`；窗口仍開放，回饋待首輪結束定案）：

- rank/常駐集合調整候選：**讀取面**——回溯覆蓋 65/65=100%（常駐直達 6＋Routing 59/59 首輪命中、零 miss 零歧義）；高頻非常駐（數據非裁決）：muse-code-cli-facts（16 reads）／zcode-platform-facts（13）／external-runtime-delegation-family（7）。**張力信號（decay 軸）**——4 常駐條目 91d 窗零 body read、純靠 mtime 豁免存活（decay 規則無常駐集輸入；常駐與 decay 的協調屬回饋裁決面）
- 定義表 v1.1 候選：desc 檢索詞宜**前置**（inventory 行截斷吃尾部詞——2/118 詞落截斷點外）；Routing 指引補 rg `--` 分隔符陷阱（`--session-id` 開頭詞被吃成旗標＝假零命中，回測實證）
- **寫入面攔截矩陣（09-09 補；755 calls 重放）**：Q1 改道面 23.6% 目標 M1-form（閘是提醒、實效掛 LLM）；**desc 日期閘（T1 口徑）＝最值得實裝**（會攔 107 calls/45 條目、誤傷≈0——P1「31 條日期流水全放行」本窗會全接住；P2 摩擦設計「另裁項」的實作證據升級）；sess_ 閘純防禦零成本；hash 閘 live 6/0 誤傷；新建>3,000 重放會攔 11（recorded 0＝上線晚）；索引手寫 0＝威懾完全成立；**注入條款機械化≈100% 誤傷（148 命中真注入 0）——AIR-49 放 LLM-flow 不放 hook 的決策被回測直接支持**
- 停止條件覆核（3-5 session 或 48h 到了嗎；有確有需求案例了嗎）：n=2 sessions＋三軸回測（A 期基準腿已補）；48h 至 09-10 晚——case 累積與覆核待窗口結束（不定格等待：AIR-50 弧先行收斂，P4 以窗口到期時已收結案）
