---
id: AIR-98
title: model 額度記憶自動保鮮——排程探測回寫＋重置週期記錄＋額度事件入帳
status: To Do
assignee: []
created_date: '2026-09-15 13:03'
updated_date: '2026-09-15 13:03'
labels:
  - governance
  - memory
  - model-routing
dependencies: []
ordinal: 83000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AI 派工前靠共享記憶裡的各家模型額度資料決定派誰，但這份資料現在靠手動更新、已經過時（as-of 停在 09-13）。這張卡讓它自動保鮮：定時探測額度寫回共享記憶（spine）、記錄各家重置週期、額度用罄事件即時入帳。跨池讀取已行為驗證可用（09-15 POC 五腿全 PASS），此卡只補資料新鮮度，不動路由架構。驗收＝AC A1–A5（機械可驗）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A1 freshness：per-family 新鮮定義在場（或 last-probe 時間戳欄）；連續 7 天證據三件一致（排程 run id／probe JSON 含 family+pool+timestamp+failure-class／spine diff 出自 ai-guide 寫手且無人工 commit）；probe 失敗日記 explicit unknown 不算新鮮，排程缺勤與 probe 失敗區分記分
A2 窗口語義：重置週期正典在 model-routing SKILL 指名節＋spine 只留指針行＋至少一處消費端（workflow redesign EP 或 AvailabilitySnapshot 節）引用；負向：spine 無週期數字拷貝
A3 事件入帳：合成 429 注入（不燒真額度）覆蓋三種簽名（原生 429／GLM 1308 含重置時間戳／web usage limit）；提醒觸發 log＋spine 事件行 diff 經 ai-guide 側寫回；runtime 無直寫 spine 路徑（rg 可驗）
A4 unsupported 顯性化：probe 程式 allow-list 僅 codex/glm；probe 碼無 muse usage 假造（rg 零命中）；muse 現值 provenance 只能是 event/429
A5 護欄：spine 寫入 commit 皆出自 ai-guide 寫手（單一寫者不變）；sync_agents.py --check 綠＋catalog 無 volatile 欄
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 2d1c432；證據＝ai-analysis/reports/2026-09-15-spine-cross-pool-recall-poc.md（跨池召回 5/5 PASS）＋ delegate-bridge usage 實測（codex/glm live、muse unsupported）〕

〔已決策勿重辯：①跨池召回已行為驗證（POC 五腿），不重驗、不推翻 spine 機制——缺口只有資料新鮮度②寫入者不變＝ai-guide 側 session 單一寫（spine 慣例）：排程 probe 只產出落地檔（family/pool/timestamp/raw/parsed/failure-class），由 ai-guide 側 session 消費校驗後寫回；runtime/cron/worker 永不直寫 spine（muse F2.1＋codex ② 雙腿一致）③窗口重置週期正典住 skills/model-routing/SKILL.md（AvailabilitySnapshot/1308 retryable-at 節旁），spine 只留指針行＋as-of＋事件行——對稱原則：volatile 不住 rule、穩定 policy 不住 spine（spine 條目自述既定分工；09-15 裁定採 muse 版否決 codex 住-spine 版，理由＝既有權威分工＋避免 as-of bump 帶週期 diff 噪音）④muse usage unsupported 是一等 capability 資料（probe capability matrix 顯性記錄），非缺數據；禁假 probe、禁以缺席推可用（stale/unknown 永不當 available——model-routing hard invariant）⑤codex 額度分 codex-native／chatgpt-web 兩池記錄永不合併（usage API 只見原生訂閱池，web 池盲區——muse F5.1 最高風險）⑥probe 失敗＝explicit unknown＋fail-loud，禁沿用舊值冒充新鮮⑦宿主不掛 daily-maintain（跨 workspace＋授權基礎不合——muse F2.1）；ai-guide 側輕量消費掛點開工時定（既有 #1 收斂延伸或 ai-guide workspace 新輕量 cron）⑧probe 不做成 dispatch-time 阻塞 gate——排程 hint 是優化，dispatch 時 probe-or-no-candidate 已由 AvailabilitySnapshot 覆蓋〕

範圍四項：
P1 Runtime probe pipeline——bridge usage（codex-native／chatgpt-web 分池＋glm）排程 probe→產物落地→ai-guide 側消費寫回 spine（as-of＋per-family 現值）；頻率上限＋backoff；排程環境憑證先確認（無憑證＝fail-loud 不靜默舊值）。
P2 Window semantics metadata——GLM 5h rolling／muse 每日 08:00 台北重置等週期，正典落 model-routing 指名節；消費語義＝形態可推度（距 last-probe 超過週期→值得再 probe）／現值不可推度（retryable-at≠available）；交付含 workflow redesign EP 可引用的介面句與落點（不做 EP 本體）。
P3 Quota event capture/reconciliation——dispatch 撞 429/1308/web usage limit 時，bridge runs 機械訊號→提醒處置 session 更新 spine 事件行；提醒式不自動寫。
P4 Unsupported probe capability——capability matrix（codex=supported/glm=supported/muse=unsupported）顯性記錄。

不做：不改 model-routing schema/catalog（AIR-91/96 定稿）、不新增 state store（含額度歷史庫——spine git log 即歷史）、不動 workflow redesign EP 本體、不推翻 spine 跨池機制、週期不雙寫（正典＋指針，禁兩處複製數字）。

風險面：web 池盲寫（最高）；hint 當 truth；誤解析寫入污染 V state；排程無憑證靜默舊值。相鄰不重複：DRAFT-4（記憶拓撲審視）、AIR-78（bridge 派工檔位）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Provenance：09-15 user 授權『整理建議→codex+muse 討論→OK 開卡』。muse job-mu2oi7ui-oj6kz6（verdict=adjust：寫入者形態/AC 操作化/per-family 新鮮 三處已吸收）；codex job-mu2oij5l-kvbdpk（verdict=GO：卡目標句與 P3 改名 event capture 已吸收）。衝突點 P2 歸屬裁定＝muse 版（正典 model-routing＋spine 指針），理由見 Plan ③。原始輸出 .delegate-bridge/jobs/ 兩 jobId jsonl。
<!-- SECTION:NOTES:END -->
