---
name: settlement-scripts-are-code
description: 量測誠信（尺與被量物）——結算/度量腳本自身 bug 腐敗證據（噪聲虛增缺口膨脹估值）；AI 評估報告正負向宣稱都需同等嚴格查證
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_c16a8998-b4b5-41c2-8bf4-1322cfd50753
---

結算/度量腳本（coverage gate、parity 對帳、驗收數字產生器）本身是程式碼——它的 bug 會**靜默腐敗它所產出的證據**，且這種腐敗有自我隱蔽性：數字「合理」時沒人查腳本。

> merged_from: feedback_evaluating-ai-reviews.md, 2026-08-31

**兩個陷阱形態（W2 實例，2026-08-28 code-reality s5_coverage.py）**：
1. **度量腳本 keying bug**：首版把 callee kind 併進 pair key——B7b 偽建構子（Function kind）與 legacy Class 節點同 key 不同 kind 被排除，**低報自己正在量測的改善**；更險的是「raw 72% 重現凍結數字」被當成腳本正確的證據——實為 bug 副作用（修正版 raw 83.5%）。**「重現了預測」≠腳本正確**：錯的腳本可以恰好重現錯的歷史數字。
2. **結算未套用全部凍結條款**：s5 結算漏套 R2-3 constructor 剔分母條款（72.3% 實應 94.7%）；B8 歸因「疑 get_ast None」未查條款面（實為 fn-tail gate 設計性濾除）——第三同型實例（前兩次：S5 結算漏 R2-3、B7 歸因錯機制）。

**Why**：證據鏈的最脆弱環節是「產生數字的那段 code」——它同時是量尺和被驗物的一部分；度量腳本享有不當的免審信任（大家查被測系統、不查尺）。

**How to apply**：① gate/結算腳本進 dual-context 審查範圍（與被測 code 同等——W2 正是 review 抓出 keying bug）；② 「重現歷史數字」作為腳本驗證時，先問歷史數字本身的產生條件是否同型（凍結條款套用與否、keying 口徑）；③ 結算前逐條對照**全部**凍結條款/口徑 clause，漏套任何一條＝數字層次錯置；④ 指標跳變（raw 14,712→17,148）先查腳本 diff 再查語料 drift——重寫過的度量邏輯優先懷疑自己。

**W6 評估弧四輪噪聲（2026-08-28，ad-hoc spike 掃描器）——實例群擴充且形態升級：量測噪聲會膨脹「值得建」的估值**：①字串 off-by-one（plain-string 起掃 `j=i` 自匹配開引號→runaway span＋字串內容誤計 35k）②fn 宣告自匹配（`fn prop_foo` 宣告名被當呼叫——「309 高信心 pairs」修掉後剩 6）③std 撞名 join（`f64::midpoint` 撞 repo 同名 `midpoint`＝假恢復）④grain bug（`fn_tail` `#`/`.` elif 分支→已覆蓋 pairs 誤判為 recovery candidates）。**新增 How to apply**：量測「缺口/殘餘/gap」類腳本的噪聲方向＝**虛增缺口**→直接膨脹建設案的價值估算（W6 若照首輪數字建 syn producer＝為 35k 幻影邊付 W2-W3 級弧）；對抗手段＝每輪除噪後的樣本**目檢封口**（W6 用雙向封口：真漏驗真〔load_boxes〕、假 join 驗假〔midpoint〕——不只往單方向打）。

**第三實例群：keying 截斷合併（2026-08-30 read_hotspots.py，fresh-eyes 審查 R1 抓出）**：聚合 key 用 `session_id[:16]`——subagent id 前綴 `sess_subagent_agent_` 長度 20 > 16，**492 個 subagent sessions 全部合併成同一 key**，把「跨 session 累積」偽報成「同 session 重讀」（Read 紀律是 per-session 口徑）、top-N 零身分資訊；首跑「成功」（[OK] 行＋合理數字）完全不暴露此 bug——又是「數字合理時沒人查腳本」。修法＝**計數 key 用完整 id、display 才截短**（口徑鍵與展示鍵分離）。同輪另一形態：SQL 排除條件漏 `task_type`——side_chat 複製 parent user 訊息致糾正計數 3x 通膨（修＝`task_type='interactive'`）。

## 同軸：AI 評估報告的宣稱查證（evaluating-ai-reviews 併入）

AI 評估報告（如 code review 品質對比、蒸餾效果分析）常見兩種不可靠的分析模式：

1. **計數式分析**：用關鍵詞頻率、覆蓋率百分比、pytest 次數等 proxy metrics 代替實際品質判斷。這些指標可以產生，但不等於品質。
2. **順向推論**：結論符合預期時（如「蒸餾提升品質」），容易跳過查證直接接受。

**Why**: LLM 的評估能力受自身 bias 限制 — 傾向產生聽起來合理的量化數據，但背後可能是 keyword matching 而非深度分析。與本文同軸：量尺（評估方法/度量腳本）與被量物不可同源未審。

**How to apply（宣稱查證面）**：
- 正向宣稱（「品質提升 X%」）和負向宣稱（「品質下降」）需要同等嚴格的查證
- 追問「這個分數怎麼算的？基於什麼具體證據？」
- 警惕沒有附帶原始數據的量化結論
- verify-review 的查證範圍應包含「方法論是否可靠」，不只查「結論是否正確」
- **審查者標「無法驗證/author-attested」的宣稱，若作者 session 持有第一手 runtime 證據，作者證據優先於審查者的 doc-only grounding**（真實案例 2026-08-14：審查者查官方文檔無 `run_in_background` 參數記載而質疑規則，但它沒有 Agent tool 無法實測；作者 session 正是用該參數背景 spawn 了審查者本身——文檔落後 runtime 時，實測證據勝出，但 grounding 措辭要如實標「runtime 實測、文檔未載」而非「官方明說」）

關聯：[[cr-live-faces-roadmap]]（pyrefly W1 實例）、acceptance-evidence 證據獨立性原則（尺與被量物不可同源未審）。
