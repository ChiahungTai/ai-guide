# Build 驗收記錄 — S1+S2（muse 實作）

> 2026-09-02。Writer：muse 1.0.1（`muse exec`，model=muse-spark-1.2、effort=high（CLI 預設）、--disable-approval、--trust-workspace、--max-model-steps 800）。Reviewer：本 session（Writer/Reviewer 分離）。

## 獨立驗證結果（全部實測，非採信自述）

| 項目 | 結果 |
|---|---|
| `node --test tests/` 重跑 | ✅ fail 0 / exit 0（44 tests、8 suites） |
| Bridge 真 E2E（真 muse＋訂閱 credential） | ✅ `REVIEW-OK`、exit 0、status=completed、sessionId 入 ledger（事件流 `poc-build.jsonl` 尾） |
| `setup` 對真 `auth.json` | ✅ credential 判別正確（onboarding/subscription carrier）；[WARN] workflows（預期，aarch64）；[WARN] sandbox 誤判（見 F2） |
| SM-11 行為 | ✅ 未帶 `--trust-workspace` 時 muse 跳過 repo AGENTS.md（警告如實顯示） |
| Code spot-check | ✅ model pin（DEFAULT_MODEL）、env strip（delete META_API_KEY）、`--` 分隔、prompt-file；❌ 原子寫缺失（F1） |
| NOTICE §4(d) | ⚠️→✅ muse 只再製 codex 原文；reviewer 補 grok 原文（GitHub raw），兩者齊＋addendum 變更清單 |
| 偏差清單 | ✅ 誠實（test-only `MUSE_BRIDGE_PROVIDER` override、classifyError 優先序、skippedUnknown 計數）文件化於 BUILD-REPORT.md |

## Review Findings（reviewer 獨立發現）

- **F1 [P1]** ledger 寫入非原子：`writeFileSync` 直寫三處（jobs.json / setup.json / jobs/<id>.jsonl），EP 契約（第三輪複審 #3 回寫）要求 tmp+rename——build 拿的是 handoff 時 EP 副本，時間差缺口
- **F2 [P2]** setup「sandbox」檢查誤判：trial exec 正常 JSONL 輸出被當 sandbox issue hint、detail 印整包原始 JSON——啟發式應以 exit code/錯誤關鍵字判定＋detail 截斷
- **F3 [P3]** ledger 欄位名 `exit` vs EP 契約 `exitCode`

**Fix round 1**：已回派 muse（背景，僅修 F1-F3＋重跑測試＋BUILD-REPORT 附錄）。NOTICE 由 reviewer 直接修（不在 fix round 範圍）。

## R2 帳務錨點追加

- #6：bridge 真 E2E `REVIEW-OK`（standard 模型、bridge spawn、~19:1x）——**這是 plugin 未來實際使用形態的第一個錨點**

## 備註

- muse 在自身沙箱內無法讀 `~/.config/muse`（credential），其「real bridge」自測用 echo provider——真訂閱路徑 E2E 由 reviewer 補測（上表）
- 本次 handoff 材料（docs/ reference/ BUILD.md）在 workspace 內；EP 第三輪回寫未同步進 workspace 副本（F1 根因）——fix round prompt 已內聯契約文字

---

## Fix round 2（2026-09-02 晚，user 實戰回報）

**回報**：mosaic_alpha 兩個 review job 標 `auth-failed` 但 exit 0＋verdict 完整交付；雜訊面良好（55 unknown-type lines 零崩）。

**根因**（雙重）：
1. `classifyError` 以 `includes("auth")` 裸 substring 掃**整個輸出**（含 tool result 與模型回答本文）——審 auth 相關程式碼時內容充滿 `AuthenticatedStaticFileHandler`/`auth-secret`/`401`（mosaic job 事件流實測：`auth`×36、`401`×29），必然誤觸
2. 分類結果**無條件覆寫** exit 映射——exit 0 的 completed 也被翻成 auth-failed

**修復**：
- `resolveJobStatus()` 抽出：**終局事實優先**——exit 0＋terminal 事件在場＝completed，分類永不翻案；細化只用於非乾淨結束
- 關鍵字收緊：移除裸 `"auth"`（連 "author" 都中）與裸 `"401"`，改精確片語（auth failed/authentication/unauthorized/invalid api key/not logged in/login/credential）
- 回歸測試：內容免疫（auth 碼符號→null）＋precedence（completed+auth-failed 分類→completed）；48/48 綠（新測試還抓到我自己留的裸 401 二次 bug——測試會咬人）

**待辦**：mosaic_alpha ledger 兩筆歷史誤標（auth-failed→completed）資料修正；commit 待 user 確認。

---

## Round 3（S3+S4，2026-09-02 晚）

Writer：muse（build 輪＋fix round 1＋fix round 2，皆 dogfood bridge 委派）。Reviewer：本 session（GLM，Writer/Reviewer 分離跨模型家族）。

### 獨立驗收（全部實測）

| 項目 | 結果 |
|---|---|
| `node --test` 獨立重跑（每輪） | ✅ 74/74（fix1 後）→ **85/85**（fix2 後：bridge 48＋s3s4 37） |
| EP S1 flag 面凍結 | ✅ `buildMuseArgs`/`mapExitCode`/`classifyError`/`resolveJobStatus`/`parseJsonlLoose` 全程未動 |
| SM-8 review 離線＋xhigh | ✅ 行為斷言（fake 驗 args 在場）＋實跑 spawn 行確認 |
| SM-15 export 容錯 | ✅ 行為測試＋真 E2E trajectory 落檔 |
| 真訂閱 E2E review ×2 | 第一次：機制 fail-loud 正確（review-fail＋原文透傳＋trajectory 落檔）但**抓到 G2 真 bug**（extractBalancedJson 無條件 fence 剝除切壞合法 verdict——本 session 機械重現確認）；第二次（fix2 後）：✅ 合法 verdict 通過 schema 閘、exit 0、trajectory export 成功 |
| Dual-context 審查（GLM） | fresh-eyes 🔴0/🟡9/🟢14＋primed 15 條 → 合併去重 27 條（`.review/main.md`） |
| Judge | 25 ✅（22 muse 範圍＋2 orchestrator 親修＋1 defer 記錄）/ 2 ❌（G23 無界緩衝可接受、G24 `.review/` gitignore 誤報） |
| Fix round 2 逐項核對 | ✅ G1-G22 全數落地（G2 用第一次 E2E 的真 finalText 重跑重現＝EXTRACTED；G5+G11 共用 helper 抽出、gate 順序對齊；G6/G7 契約文件手術後自洽） |
| Orchestrator 親修 | G25（`scripts/AGENTS.md`＋`plugins/muse/AGENTS.md` 邊界聲明改真——bridge 讀 review 模板＋schema）、G26（EP S1 status 枚舉補 `review-fail`＋S4 `--scope` deviation 註記） |
| Post-fix E2E 交互作用 | **新 finding**：G1（納入 untracked）× 80k diff 截斷 → 全量 diff 超限 mid-file 截斷，verdict 誠實標 evidence-incomplete 拒 approve → orchestrator 直修 `REVIEW_DIFF_TRUNCATE_AT` 80000→800000（1M context 設計意圖；NOTICE-級 trivial 修正，測試全綠） |
| Consistency（docs 鏈） | ✅ 契約文件引用路徑雙基底檢查唯一「缺失」＝S6 前瞻引用（合法）；術語 exitCode 一致 |
| Metadata sync | Capabilities：S4 ✅、S3 🟢（S6 安裝後才可呼叫）；README＋AGENTS.md 兩表同步 |

### 殘留（記錄不阻擋）

- 截斷 marker 無直接測試（S5 補）；`getBridgeFlagTokens` export 但測試自行掃 source（冗餘 export）；drift-scan `rePush` pattern 過度近似（任何 `--x` 字串計入 supported set）
- review exit≠0＋合法 verdict 併存時，ledger `status`=completed 蓋過 infra 細化（capped 等）——`exitCode` 原值並存故審計不失真；S5 統一 status 語義時處理（E2E-3 finding，P3 稀有邊角）
- G27 install-path 盲區（`${CLAUDE_PLUGIN_ROOT}`）、真機 `/muse` 消費端 E2E → S6
- `--scope` 縮減為 `--base`（deviation 已記 BUILD-REPORT＋EP）
- 測試套件需 Node ≥22（module-syntax detection）；runtime 仍 ≥18
- R2 帳務錨點：本輪 muse build×1、fix×2、review E2E×2（standard pin）＋fix2 長輪（~15min）

**E2E-3（截斷上限修正後，user 授權加跑）**：verdict=needs-attention、4 findings＝**零新缺陷**——2 個已記錄殘留（截斷測試、drift-scan 近似）＋1 個已裁定 deviation（`--scope`）＋1 個新 P3 nuance（上方已列）。軌跡 3MB（含完整 300KB+ prompt——untracked 全量納入的直接證據）。**完整證據鏈閉環：審查面看到全部 S3+S4 變更，發現的都是已知已裁定項。**

**commit 待 user 確認**（build commit：muse 全部產出＋fix rounds＋orchestrator 結算）。

---

## Round 4（S5+S6，2026-09-02 深夜）＋雙端消費端驗收

Writer：muse（build＋marketplace 結構 fix）。Reviewer：本 session。

### 獨立驗收

- 101/101 tests 綠（獨立重跑；一次 flake＝S5 真程序測試計時敏感，複跑 4 次綠——已知抖點）
- H1：marketplace 結構偏離 code-reality 已證形態（plugin 檔散置根目錄）→ fix round 重排為 `./plugin` 子目錄
- Capabilities 過早結算（muse 全翻 ✅，與自家 note 矛盾）→ reviewer 親修回 🟢 gate
- orchestrator 直修：CC 端 `.claude-plugin/marketplace.json` 雙慣例輸出（CC 官方 marketplace 布局與 ZCode 根目錄慣例並存；CC 首次 add 失敗暴露的慣例差異）

### 雙端消費端驗收（EP S6 準則：缺任一端不算完成）

- **ZCode ✅**：plugin 安裝（cache＋註冊 `muse@muse-market`）、skills/agent 在 session 生效、`muse-rescue` 首次真委派（job-mtk53peu：單 call、21.5s、訂閱計費、輸出準確）、`runs` 表格與全程 ledger 對帳、hooks 隨 plugin 註冊（SessionEnd 生效）
- **CC ✅**：marketplace add（directory source）＋install；CC cache bridge 煙測（query-only、共享 workspace ledger）；**headless 完整迴路**（CC session → plugin muse-rescue → bridge → 真 muse → job-mtk5g9qe completed exit 0，寫入共享 ledger）
- 教訓：CC headless 首試踩 variadic `--allowedTools` 吃掉 prompt 的 CLI 陷阱，且 `| tail` 遮蔽 exit code 造成假成功——去 pipe＋prompt 前置後通

### EP 關帳

五 UC 全數完成：任務委派（S1＋S3）／結構化 review（S4）／runs 管理＋lifecycle hooks（S5）／環境健檢（S2）／雙端發佈（S6——雙端實裝＋消費端驗證）。收尾：ai-rules 卡搬 `Done/`＋AGENTS.md 專案結構指紋行＋ep.md 回同步任務家。
