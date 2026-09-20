# corrections-2026-09 — 糾正模式月檔（corrections-weekly skill 產出）

> 週週 append；分類語義見 skill。08-30 基線：~30 糾正/2 週（方向錯 8＞重複 6＞遺漏 5）。

## 09-05 ~ 09-12 週報（09-12 23:10 排程 run 產出；09-06 首跑靜默空轉，由本窗補採——原標「手動觸發」係 run 自身誤標，DB 投遞紀錄證實為排程）

- 計數：方向錯 7／過度工程 3／驗推用戶 1／其他（溝通清晰度）1／疑似 1（候選 188、真糾正 ~17、噪音 ~171＝91%）
- Top 引述：
  - [09-08 04:05] sess_64b24ccc「你判讀的時候知道是要判 anchor point 那一天之前的 label 吧，不要看到未來資料」——look-ahead bias（資料洩漏險進 model；quant 鐵律相關，質重）
  - [09-08 05:42] sess_f34ad4bc「９．５ 是不是漲跌停板的原因啊，這種你不能改誒……這種 venue 相關不要搞混弄進來」——venue 邊界參數泛化（domain grounding 缺）
  - [09-06 07:09~07:15] sess_5ad68a25 三連：「是不是應該指導寫入不要這麼多廢話」「寫入前想一下要寫啥，不要無腦寫一堆廢話」——memory 寫入端精簡紀律（治理設計層，已觸發 AIR-40 軌道）
- vs 前週：方向錯仍居首（結構與 08-30 基線相似）；**噪音佔比暴增是本週新形態**（見訊號①）
- 訊號：
  1. **新湧現：排程普及後 cron prompt 成為候選噪音主體**（🔴 排程接續／【每晚 memory 收斂波】等 user-role 機器注入 ~90% 候選；另有 TodoWrite 提醒、compact 續讀摘要、Read replay 殘留）——建議 mine_corrections.py 排除清單下輪擴（cron prompt 特徵＋continuation 摘要頭）
  2. **memory 寫入端紀律為本週新主題**（5ad68a25 糾正群＋telemetry 實證：單條目 13 次寫入累計 97K chars——見下方 Memory 段），AIR-40 已承接，驗收看下週 top_entries 是否收斂
  3. **「rule 在檔、session 未遵守」兩實證**：`from __future__ import annotations`（python-standards 明文禁）×2、legacy 支援（edit-discipline 明文預設不保留）——rule 存在但 mosaic 端 session 未遵守（跨 repo 傳遞或 context 壓力），屬規則衰減的訊號但非 rule 缺失

### CR 使用（R5 換軌後形態）

- 健康診斷：CR skill 1 session；CR MCP callers **34 sessions**／refs 19／impact_radius 14／snapshot 13（對照 08-30 基線滲透 4-5%——白名單 rollout＋接線後大幅成長，無滲透退化）；對照 Bash rg 11,976 parts
- KPI：略（本週未取材 negative-claim／rename-delete 弧）
- 事件觸發註記：本週 wiring 變更＝R5 換軌（09-10，CR 段量測語義改版）＋identity gotcha doc（09-05）；本報告即事件數字來源

### Memory 寫入（AIR-40）

- successful 261（**errors 58 如實報**／aliases 32／ambiguous 0／unknown_actors 0）
- top actors（皆 subagent——抽驗線索）：sess_ffbc2596 6 次×74K chars、sess_29cb35e0 11 次×43K、sess_13e2faa2 2 次×14K
- top entries：**project_cr-live-faces-roadmap.md 13 次×97K chars**（單條目錘擊＝寫入精簡紀律的實證缺口，呼應本週糾正群）、agents-registry-split-design 7 次×31K、memory-cc-alignment-diagnosis 8 次×9K
- index_delta：首輪 baseline 已建（`ai-analysis/memory-telemetry/baselines/`）
- evidence：ai-analysis/memory-telemetry/weekly-20260912.json

---

## 09-13 ~ 09-19 週報（2026-09-19 23:10 排程觸發 run 產出）

- 計數：方向錯 27／過度工程 16／其他（溝通、流程、bug、治理）22／遺漏 11／重複 4／驗推用戶 2／修了仍壞 1／疑似 16（候選 166、真糾正 ~83、噪音 ~67＝40%）
- Top 引述：
  - [09-18 14:05] sess_0990d02e「問題是在根本不需要這麼多欄位啊，你是不是解錯問題」——解錯問題（problem-model blind spot；方向>>品質正典實例）
  - [09-18 16:10] sess_22964f70「四個重複？認真？你這不是可以真的撈資料然後自己判斷嗎？認真點」——可機械自證卻拋回用戶（驗證責任）
  - [09-17 19:37] sess_7ee5e230「你不要外推，真的問ＴＲＩ」——外推代替查證（事實查證原則）
- vs 前週：方向錯 7→27 大幅上升居首（多線施工峰：SC UI 波＋AIR-135 投影弧＋AIR-94 rename，UI/mockup 域集中 ~10 件）；**噪音佔比 91%→40%——上週訊號①排除清單擴充落地實證**
- 訊號：
  1. 上週兩訊號皆閉環：①mine_corrections.py 排除清單（🔴/cron/at 喚醒頭、TodoWrite、續讀摘要、task-notification）已生效，噪音 91%→40%；②memory 寫入錘擊（13×97K）消失、top actor payload 74K→17K 級（見 Memory 段），AIR-40 軌道收斂實證
  2. 新形態：stale relay／範圍過寬群（stale 工單差點重做、跨 workspace 可見性、處理範圍超出本 workspace）3+ 件——與既有 memory 條目 relay-claims-verify-current-state 同向，暫無新動作
  3. 過度工程 16 件呈「做出來再被砍」模式（git 工具、tab 條、上下鍵、SC13、週末抓取、閒置 WT）——規劃面 delete-first 未內化（見 Heat 候選③）
- Heat（AIR-131）：**Warm**（families: R recurrence＋V vocabulary divergence）——R＝方向錯 7→27（七類週趨勢，ZCode 面）；V＝check_single_source 3 CRITICAL（~/.zcode、~/.codex、~/.config/muse 三面 bundle stale）。B activation 健康（drift 由日常感測器抓到＝非逃逸）；G／U 季跑未採樣。Warm 動作（禁 additive，delete/merge/rewrite 候選）：① V 修復＝`uv run python scripts/deploy_agents.py` 同步三面（sync 既有機制非新閘）② rewrite 產出慣例：人類面報告先結論後 id（溝通糾正群 3 件，改既有 viewport 慣例）③ 規劃段落把「不做/delete 選項」列必答（rewrite 既有 planning 慣例）

### CR 使用（R5 換軌後形態）

- 健康診斷：CR skill（cr-query＋code-reality skill 調用）0 sessions（前週 1）；CR MCP distinct sessions：snapshot 3／build 2／callers 2／refs 2／hub_nodes 1／lsp_status 1／affected_flows 1；對照 Bash rg 17,499 parts。bridge 面 1,071 jobs 中 call-evidence 僅 4 jobs（CR CLI 5 次、寫入面 0），evidence-bearing 382（unverified marker 373 為大宗）
- KPI：略——本週窗內 AIR-94 rename 弧目錄 rg 無 preflight 命中，分母不可考不硬造；留弧側附卡補
- 事件觸發註記：無 CR wiring 變更

### Memory 寫入（AIR-40）

- successful 133（**errors 24 如實報**，前週 58→24／unmatched 0／folded 1／ambiguous 0／aliases 1）；unknown actors 0
- top actors：sess_subagent_agent_997d4b83 61 次×17.4K chars（subagent 大戶，總量已自上週 74K 級收斂）、sess_f315a82c 47×4.9K、sess_1f53a0c4 11×3.3K
- top entries：reference_muse-plugin-probe-facts 4×5.5K、reference_zcode-cron-workspace-scoping 3×2.5K、project_role-vocabulary-terminal 1×1.5K——**上週 13×97K 錘擊條目消失＝寫入精簡收斂實證**；池內 zz-probe-* 三件為 AIR-100 機械閘探針產物（預期）
- index_delta：本 pool 路徑首輪 baseline 建立（`baselines/_Users_ctai_Github_ai-guide_.agents_memory.json`；前週 baseline 未涵蓋本 pool 路徑）
- evidence：ai-analysis/memory-telemetry/weekly-20260919.json

---

**判讀**（09-19 更新，涵蓋兩週）：上週兩建議皆收斂（噪音 91%→40%；memory 寫入量降一個量級），無需追加。本週新訊號＝方向錯回升主導（27 件，UI/mockup 域集中）＋Heat 升 **Warm**（R＋V 兩 family）——首要動作：三面 bundle stale 跑 `deploy_agents.py` 同步（V 修復，機械 sync，屬治理動作留 user／下一弧執行）；下週看方向錯回落與三面 bundle 回 fresh，連續兩 window 未收斂再升 Hot 檢討。
