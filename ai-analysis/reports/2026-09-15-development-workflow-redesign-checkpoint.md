# 開發流程重設計：研究 checkpoint

> 狀態：規劃交付 checkpoint；完整 EP 的 review／judge／followup 已收斂。上方研究紀錄保留推理脈絡，接續以最末「規劃交付結算」為準。
> 任務：讀取當日流程／memory／compact 報告，以已完成 AIR-91 為基線，設計能節省使用額度、維持品質且讓人跟得上設計的新流程，最後產完整 execution-plan。
> 新增議題：user 要求以 Marshal 多模型協作重新檢查步驟與 overhead；最新增補見本文最末，前輪 EP 審查不涵蓋此次新提案。
> baseline: 0bbddb1ca69b8d574b6f5ef20cecaba14050a691

## 已確認的材料與現況

- 兩份 `2026-09-14-sub-model-marshal-cross-consult*.md` 均在本 reports 目錄，已完整讀取；先前對話「找不到」不成立。
- 當日材料：`2026-09-15-dev-flow-current-practices-inventory.md`、`2026-09-15-dev-flow-overhead-inventory.md`、`2026-09-15-controlled-compact-strategy.md`、`2026-09-15-memory-mechanism-analysis.md`、`2026-09-15-codex-compact-architecture.md`。
- AIR-91 成果在 `ai-analysis/_tasks/done/09-15-model-capability-routing/`；STATE.md 的 To Do 觀察已過時。後續核對結案 EP／卡與現行 doctrine，不能將昨天待裁事項當今天未完成。
- 開場既有 dirty：`.githooks/pre-commit`、`scripts/sync_agents.py`、`skills/model-routing/SKILL.md`、`skills/model-routing/catalog.toml`、`tests/test_sync_agents.py`；當日五份報告未追蹤。保留所有既有工作；本次只寫規劃產物。
- 已讀 execution-plan（user 提供全文）、rules-reminder、zcode-session-query、arch-thinking。ZCode skill 提供本機 readonly SQLite 與 tail 腳本；不能因 Codex 沒 ReadSessionContext 就宣稱本機對話不可讀。本次先完成 user 最新指定的報告分析。

## 初步設計方向（提案，尚未驗收）

1. 以工作狀態與證據驅動主鏈：定義問題 → 形成可接受計畫 → 實作及驗證 → 獨立審查與裁決 → 對人交付 → 授權提交。compact／resume 是跨階段接續協定。
2. 重用 AIR-91 的 WorkUnitContract、resolver、Role authority；Marshal 保持 workflow 責任，不新增常駐 agent／skill／runtime router。
3. 精簡重複審查與重複材料，保留 Writer/Reviewer 分離、Arbiter 裁決、critical invariant 驗證、授權邊界。review 深度依變更語義與風險，不能單憑 diff 大小；先核對現行 review-engine 與各入口的固定 legs。
4. 人類仍需理解行為與重要設計：保留簡短方向／成果 viewport；昂貴圖與持久 tour 是否必備，改為有觸發依據的提案，不能由靜態「高成本」表直接推論刪除。
5. checkpoint 保存未定案推論、排除方案、證據指針、工作狀態、外部 job 與下一步；memory 僅長期知識。compact 前不得把 memory 整理設為救援落盤的先決條件。
6. 不新增 harness compact hook／token threshold 的存在性假設。人工 checkpoint＋恢復驗證為可攜路徑；有實際能力與 runtime 證據再接 adapter。

## 已識別的報告限制

- overhead 報告是成本假設與決策材料，未有逐弧 token／時間／逃逸缺陷對照。自動排程「人力零成本」不等於 usage 零成本。
- Codex compact 報告是 sibling source 的靜態分析，不代表目前桌面／其他 harness 的 runtime；「換模型先 compact」僅候選建議，不能直接升級為全域強制規則。
- 舊 Marshal 圖解有修正 prose 計數：16 已覆蓋＋1 真空；該真空是歷史快照，現況由 AIR-91 結案材料判定。
- 首次批讀當日報告的工具輸出截斷，已分段補讀主要材料；大型輸出不作唯一證據。

## 下一步（按順序）

1. 補讀被截斷部分並核對主題卡／draft、AIR-91 final 與 AIR-96 排除範圍。
2. 精讀當前 review-engine、post-build、implement review cycle、compact-prep、metadata-sync 與殼契約的相關段，建立文件依賴與修改清單。
3. 形成目標流程／UC／Scenario Matrix／每項保留、條件化、合併的理由及替代防線；記錄仍需 user 裁決之處。
4. 在標準任務家建立 docs-mode implementation EP（若超過五個獨立中型子工程才改 blueprint）；附遷移、驗證、失敗回復、baseline、進度與 review 帳本。
5. 依現行規範安排獨立 EP review → judge → 回寫；缺額度／合格路由時標 review pending，不能用自審冒充。完成 task brief。每階段更新本 checkpoint 指向最新 EP。

## 授權與邊界

user 授權規劃與 reports checkpoint；未開始新流程實作、未變更現行 rules/skills、未 deploy。既有 AIR-96 dirty 不是本弧產出。規劃中的流程改善不會在本 session 偷換現行執行規範。

## 最新接續點：EP 修訂與 followup

本節取代上方初步「下一步」。user 最新回報 Plus usage 剩 21%，要求繼續且頻繁 checkpoint；未要求排程或兌換額度。

- 完整 EP：[ep.md](../_tasks/09-15-development-workflow-redesign/ep.md)；閱讀版：[index.html](../_tasks/09-15-development-workflow-redesign/index.html)。四段含 UC、19 個情境、修改 manifest、驗證、遷移與回復。
- Marshal 實作 commit 已核對 `b4a301992356e8960892894f392e91346a4d492f`；本弧觀察基線 `0bbddb1ca69b8d574b6f5ef20cecaba14050a691` 是後續 AIR-96 建卡。原 ZCode session 已透過本機 readonly tail 腳本成功讀取尾部，與此順序相符；未聲稱恢復整份歷史。
- 獨立 Muse review 已回收：job `job-mu2dzpyw-geyy61`，completed、exit 0；原始結果：[review-muse.json](../_tasks/09-15-development-workflow-redesign/references/review-muse.json)。Reviewer 有核對 current workflows，但未全文重讀七份背景報告，也未驗 HTML。
- 六項均採納問題並完成計畫修訂：F1 fallback 缺弧級 review 禁結案；F2 保留整合器／注入點／UC-split extras；F3 補逐端部署驗收且釐清 pre/post deploy 順序；F4 pending 有 ledger/owner/恢復條件；F5 移除新結算 cache；F6 pointer 存既有載體並查 ignored 新檔。
- 修訂 followup 已派出，工單：[followup-work-order.md](../_tasks/09-15-development-workflow-redesign/references/followup-work-order.md)。目前工具 shell session `65786`；透過 write_stdin 收回。若 session 遺失，bridge runs 查本工單匹配 job，再 show；禁止盲重派。使用 checkout `/Users/ctai/Github/delegate-bridge/rust/target/release/delegate-bridge`，caller codex，family muse，model muse-spark-1.3，effort xhigh。
- 待辦：回收 followup 並處理未解項；校驗 EP／report 本地引用；同步 index.html 的來源 hash 與狀態；檢查瀏覽器導航、折疊、hash。HTML 視覺驗收仍未完成，不作已驗聲明。
- 目前六項狀態是 implemented（計畫已修），尚非 verified。新開發流程本身尚未實作，AIR-96 五檔既有 dirty 保持不動。

## 規劃交付結算（最新）

- followup `job-mu2e7wgx-ffgcbp` 已 completed／exit 0，六項全部 resolved，無新增 Important；主 session 核對後 EP 帳本六項標 verified（限計畫修訂）。兩個外部工作均已回收，不需再 wait／重派。
- [完整 EP](../_tasks/09-15-development-workflow-redesign/ep.md) 已具備四個自足段落、19 情境、ownership、修改 manifest、驗證策略、遷移／部署／回復與收尾。規劃任務完成；新預設待 user 採用並指示 implement。
- [閱讀版](../_tasks/09-15-development-workflow-redesign/index.html) 已同步審查終態與 EP hash；[驗證紀錄](../_tasks/09-15-development-workflow-redesign/references/planning-validation.md) 保存檢查結果與限制。本地引用、HTML id／fragment、placeholder、review JSON 檢查 PASS。
- 瀏覽器 file URL 被工具安全政策拒絕；沒有繞道。互動／視覺驗證保留未完成標記，不影響 EP 文字已審事實，但不能宣稱 HTML 已驗收。
- 下一次接手：先讀 EP 進度與 Review 帳本；若 user 要求實作，先對齊 AIR-60 承接的 AC／owner，核對最新 HEAD／dirty／governing rules，按 S1 開始。保持 AIR-96 既有變更獨立。若只討論設計，從四段與 SM-16/19 的風險取捨切入即可，無需重讀所有歷史報告。
- 沒有新工作排程、memory 寫入、流程實作、commit 或 deploy。user 報剩 21% usage 是續做預算提醒，未做額度重置操作。

## Marshal overhead 增補 checkpoint

- 已讀替換後 AGENTS 指令，重新查現行 review-engine／execution-plan／post-build 與 model-routing 相關段。
- 新增 [減量判斷報告](2026-09-15-marshal-workflow-overhead-decisions.md)：明確列可刪預設、可合併工作、已存在快道、不能刪的防線；新核心是 Role 不等於 worker、按可驗收成果切工單、省重讀但不省新鮮度。
- 確認目前仍有 agent 數量=max-agents、依主模型/effort 判 review 形態的舊條款；post-build 空 findings 跳 judge 已存在，不冒領優化。文件層事實不等於實際每弧執行頻率。
- 本輪只新增分析，未改已審 EP 的內容與 projection hash；新增三項尚未獨立審查。下一步為核對相容 work units／批次化是否修改 routing/authority，再將確定部分併入 S1/S2 並跑 scoped review。既有六項 verified 僅涵蓋前輪稿。
- 無新 delegated job；沒有規則實作、commit 或 deploy。新指令已取代舊指令，控制面政策實作應在 fresh context 按 read-set 接續。

## 骨架整合進行中（user 最新要求）

- user 回報 usage 16%，明示可派 Muse 調查；本 session 只交計畫，實作交其他 LLM。HTML 互動／視覺驗證本輪免做，不再作規劃收斂阻擋。
- 派出有界 Muse 調查／findings 工單 `references/marshal-integration-work-order.md`，工具 shell session `11628`，收法 write_stdin；若中斷先查 bridge job ledger，不重派。模型 muse-spark-1.3、bridge binding、xhigh；qualification 查 current catalog review_findings=qualified；不讓 Muse 做 final adjudication。
- availability probe 無 Muse 結構化 usage（unknown，未聲稱額度充足）；本次依 user 指定作一次有界 runtime 嘗試，失敗保留 checkpoint、不盲重試。GLM 5h 仍 100% used。
- 下一步：收回契約相容性矩陣，主 session 判斷哪些能只在 workflow adapter 落地；先把骨架插入 S1/S2，再加輸出責任、情境與交接驗收。每個新決策不沿用前輪 verified 標記。

## 骨架與細節已整合，增補複核中

- 調查 job `job-mu2fgaqy-d9l930` 已 completed/exit 0 並收回，原始 JSON 在任務家 references/marshal-integration-review.json。
- EP 已納入：S1 先選 profile 再 batching；S2 同 authority／逐 unit 契約的多成果工單、共同 read-set、部分失敗與依賴失效、followup 契約和 final disposition 分離；SM-20–24；既有 work-order 的 S2 manifest；給實作 LLM 的接手入口。
- 裁決 M1 部分採納、M2/M3 採納、M4 採納問題但限縮過強說法。普通三腿減量仍是本 EP 待行為驗收的政策選擇，不因舊規則存在而取消；新 profile 要求的獨立性不可被 batching 吞掉。
- 已派精簡增補 followup，工單 references/marshal-followup-work-order.md，工具 session `5378`，write_stdin 收回；禁止盲重派。只驗 M1–M4，HTML 免做、實作不做。
- 目前 EP 比閱讀版更新；複核後再一次同步 HTML projection 與 report 終態，避免每次增補都重產殼。本輪目標是把可交其他 LLM 的計畫完全填好。

## 增補三項漏洞修訂 checkpoint

- 增補複核 job `job-mu2fn09e-d6vjf8` 已收回：M3 resolved，M1/M2/M4 各一 Important 已採納並修訂。
- 最終範圍更窄：批次只限機械查證／實作成果，禁止多 review units 共 context；followup 回證據，主鏈編排者是 status 單一寫者，Arbiter 保有 disposition；明指 post-build:88 修改完整輸出／coverage 閘。
- 三點修訂與來源在 EP 最末 Review 帳本；closure 工單 references/marshal-closure-work-order.md 已派 Muse，只核這三點，不擴張研究。
- 等 closure 收回再同步交付終態。HTML 測試依 user 免做，新流程仍由其他 LLM 實作。

## 最終交付：骨架與細節、增補審查已收斂

- closure `job-mu2fstmq-gouh8l` 已 completed/exit 0，M1-B1/M2-B1/M4-B1 全 resolved、無新增 Important；原 F1–F6 與增補 M1–M4 計畫修訂均 verified。所有 Muse jobs 已收回，沒有待收／仍跑工作。
- EP 現為四個自足段落、24 個情境，含 Marshal 編排骨架、work-unit 批次契約、唯一帳本寫入者、read-set/freshness、精確 consumer 落點、分段驗證及給實作 LLM 的入口。
- 終態選擇：不合併跨 authority／多 review contexts；同權限機械查證與實作成果可批次。保留 reviewer→Arbiter 的權限分離；status（verified/closed）由主鏈編排者單寫，不混成 disposition。失敗／截斷／空白不走零 findings 快道。
- 文字與簡報已同步；HTML 互動／視覺驗證依 user 本輪免做，不阻擋計畫交付。實作／behavior／pilot／成本量測尚未執行，交其他 LLM；無 commit、deploy、memory 寫入或新排程。
- 接手不需重調查：讀 EP 進度→增補終態→接手入口；user 指示實作後對齊 AIR-60 owner/AC 及最新 HEAD/dirty/治理檔，從 S1 起。若 current source 已改，針對差異重定位，勿照舊行號盲改。
