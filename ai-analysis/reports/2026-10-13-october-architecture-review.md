# 十月架構檢查與改善設計

本報告是分析與設計提案，未授權或執行控制面修改。基線為 clean main `9007350e993dc5bcf90ac186ffe822db2776cc8f`；十月起歷史枚舉為 594 commits、152 個有變動的控制面路徑。這是依變更弧抽查契約與關鍵消費路徑，不代表逐行審完所有 commits，亦不是四個 harness 的 live acceptance。

## 建議

優先補齊「交付證據屬於哪一次派工規格」的身份契約，修正已證實的 authority 條款衝突，再刷新架構合成文件。保留現有 domain owners；暫不新增統一 watcher、policy engine 或大型派工 compiler。派工繁瑣的成因尚未量測，減少重複欄位與減少語義裁決不是同一問題。

十月變更可歸為：信箱身份與消費模型收斂、CC 面退役與 AGENTS 單檔化、ArcPlan 與交付契約機械化、監督及存活判斷、bundle 瘦身、model 資格路由、CR 證據與 Marshal 權責。新機制已有局部單一源；目前主要風險位於它們交接時的身份、權限與文件投影。

## 已核實發現

### A. Handback 缺派工版本綁定：最高優先

`scripts/arc_manifest.py:281` 已生產 contract digest；`scripts/arc_handback_join.py:39` 的 join 驗 schema、card、unit、AC 覆蓋、verdict 與非空 evidence，但未綁定 manifest 內容。`skills/_common/work-order.md:155` 的 handback schema 亦無對應 digest。

以既有 fixture 在記憶體中執行 join：原始回 `[]`；更換 contract_hash、所有 verifier 與 expected 後仍回 `[]`；刪去一個 verdict 則回 `missing: ac_id=3`。這證明身份覆蓋缺口；未證明整弧曾錯誤落地，也不是現行 join 明定契約的實作違反。

提案：dispatch 凍結 assigned manifest，handback 帶其 canonical digest，collection 對照當時保留的 artifact；digest 涵蓋 contract、unit 分派與 predicates。不能於收線時重算最新計畫投影來驗舊回執。attempt/source 綁定僅在具體重播風險成立時追加，避免合法 retry 被誤拒。join 做身份與結構檢查，語義 verdict 仍由獨立 review/judge 決定。

### B. 強制 commit 證活與 worker 權限衝突

`skills/agent-workflow/SKILL.md:99` 要求起手空 commit 與逐修 commit；`agents/roles/impl-lite.md:16` 及 `skills/_common/work-order.md:13` 禁 worker commit。這是可直接讀取的權限矛盾。

提案：移除「為證活必須 commit」的要求，以既有 exec、heartbeat 或工作輸出作活動觀測。`agent-workflow:119,130,134` 對 terminal 權威、活動弱訊號與判死證據的區分本身合理，應保留；活動停滯不得自動升級為 kill 或重派授權。

### C. 架構合成文件已落後 authoritative sources

`ai-analysis/blueprint/structure.md:23-28` 仍描述三個 bundle、Claude symlink、三個 bridge 家族；`governance/manifest.toml:59,65-69,96` 已反映四 target、更新 symlink 與 CC 註冊面退役。`governance/AGENTS.md:9` 的註冊清單也未完整反映 grok。

實跑 blueprint projection freshness：五個 upstream 中一個 drift，為 `AGENTS.md#命令的受眾視角` 到 `index.html`。現有 manifest 並未涵蓋所有 source 到合成敘事的關係，所以此數字不是全部文件漂移數。

提案：bounded refresh，移除已退役敘事，引用當前定義源並標示 live 未驗證處；沿用既有 freshness 工具，先不另造 provenance 引擎。Blueprint 是理解視角，不能升格為第二套 runtime policy。

### D. Qualification 首次使用流程未收斂

`skills/model-routing/SKILL.md:62` 要求 qualified-only；同檔首次使用與預設模型敘述、catalog 的 conditional/pending_first_use 記錄存在流程歧義。Flash 的 evidence_retrieval qualified 記錄在 zcode-registry 面，不能直接外推 bridge 面資格。

提案：將 availability、bounded pilot、正式 qualification 分開。若要允許 pilot，需明定非 decision scope、數量上限、獨立審查與 binding-scoped receipt，再由有權者判定晉升；禁止 READY probe 自動變成 qualification。本次使用者明示 Muse／Flash 協作的顧問輸出不構成常規資格先例，也未修改 catalog。

## 責任邊界設計

| 責任 | 保留的 owner | 改善方向 |
|---|---|---|
| 行為與權限政策 | 現有 rule／skill 定義源 | 修真正面衝突；consumer gate 不靠 startup advisory |
| 派工規格 | ArcPlan／assigned manifest | 凍結交付身份；只投影機械欄位 |
| 執行與 terminal 事實 | bridge／各 harness | 保留各自 authoritative evidence |
| 回收與驗收 | join → review → Marshal judge | 身份合格、結構合格、語義接受分開 |
| 活動觀測 | 各域 waiter／watcher | 弱訊號只喚醒，不授予控制權 |
| 人類理解 | blueprint／reports | 從 authoritative sources 合成，明示 freshness |

Mail、bridge job、harness worker 的 lifecycle 不同，目前不合併其判定核心。AIR-312 custody 已採 repo basename，不恢復 per-caller consume 設定。Minimum Dispatch Packet 也不等於現行十節或 compile gate 的豁免。

## 複雜度與遷移次序

| 階段 | 範圍 | 相對複雜度／風險 | 依賴與完成條件 |
|---|---|---|---|
| 1 | assigned manifest 身份綁定 | 中／高：共用契約 | standalone EP、producer/consumer 一起設計、獨立 review、重播 oracle |
| 2 | blueprint 刷新與 commit 證活條款修訂 | 低至中／控制面政策風險 | 非 canonical WT；政策修改依 instruction review gate |
| 3 | 明定 qualification pilot | 中／高：路由 authority | 先定 policy，不自動放寬 decision 資格 |
| 4 | 抽樣派工成本，必要才做最小 projector | 調查低；建置待定 | 證明重複轉錄是瓶頸，再定成功門檻 |

四份核心方法文件合計 181,105 bytes，只能說明潛在讀取負擔，不能等同每輪實際載入 tokens。先量測最近工單重複欄位、錯填與裁決成本，不先承諾效能提升。Deep-work 的 quota-zero 自停限制已有記錄，不列新 bug；域外 observer 另案評估，不因本報告自行掛排程。

## 驗收情境

| 情境 | 建議預期 |
|---|---|
| card/unit/AC 相同但 contract、verifier、expected 或分派改變 | 舊 handback identity mismatch |
| digest 缺失、不符 | fail-closed，不進接受判定 |
| 合法未變更派工的回執 | 身份與結構通過，仍需語義驗收 |
| FAIL/NOT-DONE 回執 | 可結構有效，不等於 DONE |
| 缺少 AC verdict | 保留 missing 診斷 |
| worker 無 commit 權限但持續產出 | 可觀測活動，不要求越權 commit |
| watcher 靜默或過期 | 喚醒／診斷，不自動 kill 或重派 |
| availability 成功但資格不符 | 不自動晉升正式 decision 路由 |

## SC 來信補充：測試隔離

已唯讀取得 `sc-20261013-test-skill-stub-default` 全文，實際來源 South Chariot，目的址仍是 `ai-guide-marshal`，deliverySeq 75。查詢時 pending=true、hasReply=false；現行 watcher 是 `ai-guide`，所以未因這封舊址信觸發。未 ACK 舊址或寄回執。

信件主張 SC-344/SC-347 的 unit helper 應預設 stub 外部 binary/spawn，並附 worker 與 Marshal 環境分歧。這些 SC 實驗數字是來信陳述，本次未獨立重現。

初步比對：`test-driven-development:84-94` 已要求測試分類、unit 不藏外部依賴；`validation-strategy:54-71` 要求真實邊界 integration 證據。因此可研究的增量是 unit helper 的預設外部 IO 隔離與防漏機驗，不是將全部測試改成 stub。正式改動前仍需 cluster-first 查重與 SC 原始案例核實；不因收信就視作實作授權。

## 證據與合作回執

- CR 重建後 fresh=true，source identity `3de3c18b1f829b7cf7d65061c8e58f6dd0cbfeec298789dc3424148f676abd30`；Python 結構覆蓋不能冒充全文件或全 runtime 覆蓋。
- 五組 Arc 契約測試：350 passed；single-source 檢查 15 invariants 通過。這些綠燈不否定本次身份缺口，也不代表全 repo 驗收。
- Blueprint freshness：1/5 upstream drift；join replay probe 直接重現上述缺口，未修改 fixture 或 source。
- Flash history `job-mv69oce8-sewac8`、Flash contracts `job-mv69od2p-2lbozs` 完成。
- Muse 第一輪 `job-mv69od92-tbfmfw`、第二輪 `job-mv69tt9t-4o4l2i` 完成。第二輪撤回恢復舊 custody 設定、simple 豁免 gates、統一 watcher 核心、以 blueprint 為 runtime 權威等未成立建議；採納 assigned-manifest digest 的強化建議。
- 原始回執、探針、檢查 log 與 prompts 位於 `.agent-tmp/oct-architecture-20261013/`。未做產品／規則實作、commit 或部署。
