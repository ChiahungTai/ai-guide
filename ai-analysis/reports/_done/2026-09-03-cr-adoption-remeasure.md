# 升級①複測：cr-research 換軌後的 CR 滲透與用量（2026-09-03）

> 排程執行（2026-09-03 觸發；origin：user 2026-09-01 05:33 `/at 9/3 00:20 再看看效果`）。
> 觀察窗 after2 ＝ `cf5a7ca`（2026-09-01 03:59）～ 2026-09-03 05:38；對比基線＝[2026-09-01-cr-adoption-token-impact.md](2026-09-01-cr-adoption-token-impact.md)。
> 資料源：遙測 DB（rm_*.csv 於 `.agent-tmp/`）；判定準則預定義於排程 context（滲透零→換軌失效；滲透>0→量化幅度）。

## 判定（TL;DR）

**換軌生效——升級①的機制閉環活了。** after2 窗口 cr-research 被 spawn ×5（4 次正牌 EP 段落 0）、CR 結構查詢 16 次（refs ×8／callers ×5／impact_radius ×3；after1 全窗為 0）；EP fresh input median 降 36%（342K→220K）。殘餘問題一個：**引用落地斷鏈**——查詢結果有進 EP（依賴錨點形態可辨），但 `[SRC]`／工具輸出引用沒落進文檔。implement 用量仍無減少（預期內——hotspot 在批次化非符號查證）。

## 1. 滲透複測（新度量契約：MCP 工具名＋CLI subcommand 錨）

| 指標 | after1（EP2 窗，基線） | after2（升級①窗，本次） |
|---|---|---|
| EP/implement episode 內結構查詢（MCP refs/callers/closure/impact_radius） | **0** | **16**（cr-research sessions 內） |
| EP/implement episode 內結構查詢（CLI subcommand 錨） | 3 | **0** |
| snapshot（data-face，MCP） | 0 | **43**（implement child ×40＋main ×3） |
| cr-research spawn | 不存在 | **×5**（122 requests / 10.5M in_tok） |
| EP 產出 `[SRC]` 引用 | 0 檔 | **0 檔**（引用斷鏈，見 §3） |

**cr-research spawn 歸因**（parent session Skill 史機械對照）：

| spawn 時刻 | parent | 歸屬 |
|---|---|---|
| 09-01 13:56:30 | annoate-workflow（EP Skill @13:55:58） | **EP 段落 0** ✓ |
| 09-01 21:38:09 | sidebar EP（EP Skill @21:36:44） | **EP 段落 0** ✓（主 research 股） |
| 09-01 21:48:18 ×2 | sidebar EP（同上） | **EP 段落 0** ✓（消費端盤點股＋資產文檔盤點股——平行三股形態） |
| 09-01 05:59:06 | B2 EP switch（該 session 零 Skill 調用） | inline 流程（EP 段落 0 形態但未走 Skill） |

CR 工具實際使用：3/5 sessions 跑結構查詢（主 research 股 refs×5+impact×1；消費端盤點股 refs×3+callers×3；annoate 全域研究 callers×2+impact×2）；另 2 sessions 純盤點（rg/Read）——資產文檔盤點不需 graph，屬正當。**EP episode 滲透率 2/10 = 20%**（vs before 真實滲透 4-5%、after1 為 0）。

## 2. 用量對比（episodes median / mean）

| skill | phase | n | requests | fresh input | input_tokens |
|---|---|---|---|---|---|
| execution-plan | before | 35 | 42 / 95 | 342K / 890K | 13.0M / 33.9M |
| execution-plan | after1 | 9 | 13 / 74（含 trivial 調用） | 221K / 637K | 3.4M / 22.8M |
| **execution-plan** | **after2** | **10** | **39 / 61** | **220K / 438K** | **11.2M / 23.1M** |
| implement | before | 37 | 166 / 217 | 896K / 1.5M | 63.1M / 79.3M |
| **implement** | **after2** | **9** | **191 / 245** | **1.38M / 1.81M** | **92.3M / 93.3M** |

- **EP**：after2 全是真實規劃 sessions（09-01/02 mosaic 弧）——requests median 39 vs before 42 **持平**；**fresh input −36%**（342K→220K）；in_tok −14%。token 紅利主要體現在 fresh input（cache 命中結構改善），不是 request 數。
- **implement**：仍無減少（requests +15%、in_tok +46% vs before）——與基線判定一致：implement 用量槓桿在批次化/Read 紀律（已兩波落地），符號查證本來就非其大頭。附帶正面信號：baseline snapshot 走上 MCP（×43）——EP2 資料面 MCP-first 翻轉（08-30）首次實際發生。

## 3. 殘餘問題：引用落地斷鏈（最後一哩）

cr-research 的查詢結果**有進 EP 文檔**——`mosaic_alpha ai-analysis/_tasks/_archived/09-01-switch-preamble-consolidation/ep.md` 的「依賴錨點清單」是 callers 形態（`_begin_switch → 定義 shell / 消費 base _on_instrument_change`），結構資料可辨——但 **`[SRC]`／工具輸出引用標記全部遺失**；`09-02-tagging-machine-loop/ep.md` 的依賴宣稱（如「兄弟線已收 e4d4a176」）以 commit hash 引用；`09-01-readiness-bounded-probe/ep.md` 直接標明「rg 全掃」形態。EP skill「每個 ripple 宣稱附工具輸出引用」條文未閉環：**查了、用了、沒留痕**——驗證軌跡（哪個工具、哪個輸出）不可回溯。

ai-rules 端兩個新 EP（muse-plugin-cc、three-pool）為 docs-mode 無 ripple 宣稱，CR 缺席屬正當（GATE 不觸發）。

## 4. 下一步建議（優先序）

1. **修引用落地（最後一哩）**：兩個方向擇一——(a) EP 段落 0 產出條文加「research 產物落檔 task 目錄 `research.md`（含完整 `[SRC]` 引用），EP 正文只摘要」——muse EP 已有 research.md 形態先例，artifact 保存引用比正文內聯更穩；(b) cr-research 輸出格式強制引用塊。建議 (a)：落檔是機械可驗收的（`fd research.md`＋`rg [SRC]`），正文內聯會再斷一次。
2. **implement wiring 驗證換軌（輕改）**：implement:166 的 review Explore spawn 改 cr-research 優先——形態已驗證，同款改法。
3. **用量面不再動作**：EP fresh −36% 方向正確、requests 持平屬實；implement 減量本就不該期望來自 CR。持續觀察，下次治理看照順帶看滲透即可。

## 附錄：資料檔

`.agent-tmp/`：`q_remeasure.sql`／`q_crresearch.sql`（可重跑）、`rm_episodes.csv`（117 episodes 四相明細）、`rm_agents.csv`（窗口 agent 形態全譜——cr-research 122 reqs／5 sessions 在場）、`rm_mcp_cr.csv`、`rm_cli_cr.csv`、`rm_crresearch_sessions.csv`、`rm_crresearch_tools.csv`。
