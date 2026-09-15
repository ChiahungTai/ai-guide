---
id: AIR-98
title: model 額度記憶自動保鮮——排程探測回寫＋重置週期記錄＋額度事件入帳
status: In Progress
assignee: []
created_date: '2026-09-15 13:03'
updated_date: '2026-09-15 16:17'
labels:
  - governance
  - memory
  - model-routing
dependencies: []
references:
  - skills/model-routing/SKILL.md
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

開工第一步（user 09-15 指示）：與 user 對帳目前購買的訂閱／額度現況——訂了哪些家、各家的池（原生訂閱／web 池）、窗口形態與重置時間、帳號載具形態；此對帳是 P1 probe 對象與 P2 週期正典的事實基礎，未對帳不動工（週期數字由 user 口述確認後才寫進 model-routing 正典，不從舊報告推度）。

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
09-15 user 開卡後補指示：開工第一件事＝問 user 目前買的額度狀況（已入 Plan「開工第一步」段）。

開工第一步對帳完成（09-15 user 提供，已同步 spine model-runtime-entitlements as-of 09-15）：①GLM 訂閱至 2027-02-04；窗口＝5h/week（非 5h rolling——P2 週期正典以此為準，修正原 Plan 假設）②Models＋Vision MCP 共用額度池；premium 尖峰 3×（週一~五 14:00–18:00 UTC+8）離峰 1×③GLM-5.3-Flash 消耗≈5.3 的 0.4×——機械腿首選④活動 09-03~09-20 每日 23:00–09:00 SGT：Flash 經 ZCode 零額度無限、經其他 agents 額度×2；僅 Flash；達 5h/week 上限暫停參與；需 ZCode 3.10+（版本符合性待驗——實作時確認）⑤SouthChariot（~/Github/SouthChariot）有既有 usage＋reset time 實作（src/chat/reset.ts＋test/quota.test.ts）——P1 probe 候選源，實作時評估復用 vs bridge usage。路由含義：活動期間夜間窗口（23:00–09:00）Flash 經 ZCode 免費——夜波/排程/機械腿排夜間＝零額度。

09-15 user 對帳補充（已同步 spine）：①GLM＝legacy v1：5h 上限、無 weekly（修正前註 5h/week——活動條款的 weekly 字樣不適用本方案）；窗口觸發語義＝滿額後再呼叫一次才起算五小時②ZCode v3.11.2+ 已確認，活動生效中③muse＝Power、5h 窗口、request 計費非 token、無公開上限、定位偏 review；TUI /usage 存在——P4 探測項：驗證程式化查詢路徑（CLI flag 或 TUI pipe）④codex 主力＝Web High（≤5 tabs、過快暫停、launcher 1-2 天自動 logout、額度充裕——137 job 實證）⑤webgpt 健康監控三訊號（user Flash 勘查報告）：(1) curl http://127.0.0.1:17841/healthz——accepting_turns===true＋last_successful_model_catalog_request_at 距今不久（唯一證明 ChatGPT 端有回應；全綠只證 process 活）(2) ls -t ~/.codex-chatgpt-web/diagnostics/browser-turns/ 最新 *.json——turn-completed 健康 vs turn-failed+rate limit 節流（僅留 10 trace、lazy prune；無目錄≠不健康）(3) codex-chatgpt-web doctor --json（含 2s live 探測；connector 綁定只能 warning）。明確不存在：reconnect counter 不落盤、rate-limit 無 marker 檔、accepting_turns 與帳號有效性脫鉤。CLI另有 service status/cancel-turns、browser check、dev status；drain=/admin/drain|resume。P1 probe 設計：webgpt 用三訊號組合（catalog 時間戳＋最新 turn 狀態）取代不存在的 usage 面。

P1 Runtime probe pipeline 實作完成（2026-09-15 worker session，working tree 待 marshal 審後提交）：交付①scripts/probe_entitlements.py——glm/codex/muse 經 delegate-bridge usage --json（binary resolve＝installed_plugins.json delegate@delegate-market installPath；bounded timeout 60s；exit map 契約＝聚合內含 family error 回 1 但 stdout 仍完整，per-family status 才是 fail-loud 切面，live 抓到後已釘測試）＋codex chatgpt-web 池健康兩訊號（healthz accepting_turns＋catalog 時間戳、browser-turns 最新 trace checkpoint——真實 layout 為 traceId 子目錄內 NN-checkpoint.json，非平鋪 *.json；doctor --json 留 TODO）；usage allow-list={codex,glm}、muse 只落 unsupported+reason、webgpt 欄 pool_visibility=none 零用量數字；落地 schema v1 原子寫+latest 指針至 ~/.agents/probe-entitlements/；--min-interval 30 skip 防重疊、--family 過濾、全腿非 ok exit 1；②tests/test_probe_entitlements.py 29 綠（RED→GREEN，bridge 三形態 fixture/webgpt 兩訊號 tmp 注入/原子寫/exit 語義/min-interval/allow-list 負向/檔名 schema）；③schedule-registry.md launchd 表加列 entitlements-probe（待安裝）＋plist 內容備於 .agent-tmp/air-98/entitlements-probe.plist（不 install）；live 實跑：glm ok（plan pro+limits 原樣）、codex upstream_error（not logged in，fail-loud 示範）、muse unsupported、webgpt verdict=degraded（healthz 全綠但最新 turn failed 非 rate limit——三訊號組合價值實證），exit 0。消費協議：ai-guide session 讀 latest-*.json 校驗（probe_ts_utc/failure_class）後寫 spine as-of+per-family 現值；probe/runtime/cron 永不直寫 spine。P2 窗口語義正典／P3 429 事件入帳／P4 capability matrix 檔案化本弧未做。mypy 不在 repo dev 工具鏈（僅 pytest+ruff），段級閘門以 ruff+pytest 為準。
<!-- SECTION:NOTES:END -->
