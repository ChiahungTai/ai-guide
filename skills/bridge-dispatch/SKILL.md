---
name: bridge-dispatch
description: "跨 repo 呼叫 delegate-bridge 的 bootstrap gate 面才載——bridge 派工首個有後果決策前（rule 錨帶入），或結構證據收線核對／waiter watcher 治理／grok authority profile／session label 面載入。操作知識（caller surface 入口對照、MCP face 接線、dispatch⇄collection 完整模式、webgpt 雙軸預算、Brief capability 契約五要素、glm provision/resume）已隨 bridge release 出貨為 delegate:bridge-dispatch plugin skill（版本凍結、隨版控）；本檔只留 plugin pointer＋consumer governance 留守面（AIR-216 route 值域與收線核對、bridge_waiter 治理、grok contained writer、seam label、Brief 動詞紀律）。觸發詞：delegate-bridge、bridge 派工、結構證據收線核對、structural-evidence route、unverified-by-graph、bridge_waiter、CollectionReceipt、stalled-advisory、liveness、grok contained writer、session label。"
when_to_use: "Fires only at the bridge bootstrap gate face — the first consequential delegate-bridge dispatch decision (anchored by rules/bridge-dispatch.md), or the retained consumer-governance faces: AIR-216 structural-evidence collection check, bridge_waiter governance, grok authority profile, session label. Operational dispatch how-to lives in the delegate:bridge-dispatch plugin skill."
---

# bridge-dispatch — bootstrap gate 面＋consumer governance 留守

> **退役形態（AIR-268）**：bridge-native 操作知識已隨 delegate-bridge release 出貨為 **`delegate:bridge-dispatch` plugin skill**（版本凍結、隨版控——skill 快照＝出貨 plugin 版本，`delegate-bridge --version` 判讀在讀哪份）；Muse caller kit（delegate-bridge repo `docs/muse-caller-kit.md`）＝legacy projection。本檔＝ai-guide 側 always-on bootstrap 最小核心＋consumer governance 留守面。as-of bridge plugin 3.4.1（2026-10-07 對齊）。

## 模組定位

- **bootstrap gate 面**：跨 repo bridge 派工的首個有後果決策前，always-on 錨＝[rules/bridge-dispatch.md](../../rules/bridge-dispatch.md)（registry pin 唯一源＋禁手拼 pin／禁第二 pin、glm provision 前置、waiter 配對、長輸出檔案承載——最小核心與資格論證在 rule 端，本檔不重複）；本檔只做 plugin redirect＋留守面承載。
- **操作知識消費方式（pointer 接手可達）**：
  - ZCode／CC plugin session：`delegate:bridge-dispatch`（delegate plugin 安裝即達）。
  - Muse session：plugin projection（`plugin:delegate:bridge-dispatch`，stage-muse-projection 安裝）；caller kit＝legacy fallback。
  - bare shell／repo checkout fallback：caller-surface 合法入口對照表已隨 plugin skill「Legal entry points」節——plugin 面外從 registry pin（`installed_plugins.json` 取 `installPath`）或 repo checkout 解析，禁手拼版本化 cache 路徑、禁第二 pin。
- **已隨 plugin 出貨（本檔不再承載；rule／model-routing 端指針經此 redirect）**：caller surface 入口對照表、MCP face 接線與 MCP tool dispatch（knownFalseNegative、codex config wiring）、dispatch⇄collection 完整模式（waiter 配對／124 語義／terminal ≠ complete／sink 三步驗收——驗收程序單一源＝`delegate:delegate-run-output` plugin skill「Receipt acceptance」節）、webgpt 大內容（雙軸預算／fat-AGENTS 替代路由／review face 28K 閘階梯／失敗態分流）、Brief capability contract 五要素、glm provision fallback 語義／resume model-match／`--steps` 禁令、Dispatch prompt 禁以 `/` 開頭。

## 結構證據收線核對（terminal collection；AIR-216；as-of 2026-10-01——rg pattern 隨 bridge jsonl schema 漂移以實際欄位為準，且各 family ledger 事件鍵不同（四形）：glm＝`"toolName"`；muse/codex＝`payload_type`（tool.result／tool.search／tool.bash 等）；grok＝NDJSON camelCase tool 事件（toolCallId/toolName/rawInput）＋**事件錨定 status**（in-stream tool failure 永非終局、exit code 僅佐證；anchor-less text 串流＝`output-token-limit` 大聲失敗——bridge 2.10.0 DB-72，源＝delegate-bridge docs/ep.md S1 honest-completion 條款）——先判讀該 job 的 schema 再核，0 命中 floor 以 schema 確認後為準）

對 brief 宣告的 structural-evidence route 核實際 evidence channel——live-cr:MCP 核 job tool events（glm 形例：`rg -o '"toolName":"[^"]+"' <job workspace>/.delegate-bridge/jobs/<id>.jsonl | sort | uniq -c`；ledger per-workspace，cwd 須＝job workspace）；live-cr:CLI 核 command payload 是否實際呼叫 code-reality 查詢（toolName=Bash 不代表零 CR；例：`rg -o 'code-reality (refs|callers|closure|impact-radius)' <job>.jsonl | sort | uniq -c`）；preprovided-cr 核 read-set artifact／provenance receipt（cr-query `[SRC]` provenance 戳）；degraded 核受影響的結構 finding／claim 是否逐條帶 unverified-by-graph，降級原因依成因記值——bridge worker 無 CR query face＝`no-cr-query-face`、WT graph 缺席／過期＝`WT-graph-absent`／`WT-graph-stale`（值清單指涉單一源＝[cr-query](../cr-query/SKILL.md)「card-WT 結構證據供給（AIR-228）」節）。**宣告 live-cr 卻無相應 evidence channel（0 命中＝fail-loud floor；零星命中＋Read 主導＝實質違反 live-cr 禁令〔禁逐檔 Read 重建結構事實〕，照該禁令條判）、或宣告 degraded 卻漏標記＝delivery defect**——處置：逐條補標或退回；histogram 行貼進卡 notes／receipt（證據非自報；loopback 紀律管報告內部一致性，不涉 histogram 語義）。本核對只證 route 遵循，**不證 query 正確或 graph freshness**（CR hit>0 不洗白 stale graph 上的負存在斷言——仍依 cr-query／symbol-query-routing 判定）。腳本化門檻：需自動阻擋 collection、跨 MCP／CLI／family tool-name normalization、或 parser 誤報出現時再議；此前禁腳本化。

## 結構查證腿——evidence route 宣告（條件節；AIR-216）

brief 含結構事實查證（callers／refs／closure／impact radius／符號事實）時，capability manifest 旁必須明示該腿的 structural-evidence route，三態擇一（**按 carrier 當次實際 surface 宣告，禁空願望、禁按家族推定**；live-cr 依 query face 再分 MCP／CLI 兩形——見收線核對）。宣告形態（brief 逐腿一行，機械可掃）：`route：live-cr[:MCP|:CLI]`｜`route：preprovided-cr`｜`route：degraded`。surface 判定＝work-order §7 carrier 分流 guard（當次探測為準）；「glm 腿默認 degraded」是可反駁起點非推定——探測到 CR face 即升 live-cr：

- **live-cr**——worker 當次 surface 有可用 CR query face（MCP 在場，或唯讀 CLI `code-reality` 經 Bash 可達）：結構事實須由 CR 取得；Read 僅可在結構範圍縮小後查行為／語義（分工語義＝cr-query「LSP vs code-reality — the division」），**禁以逐檔／逐行 Read 重建 callers／impact 等結構事實**（違＝brief 缺陷，禁派——要素 1＋2 之實例化）。
- **preprovided-cr**——dispatcher 已先跑 CR、evidence artifact（含 provenance receipt）附於 read-set：worker 不必重查，收線核 read-set 所列 artifact。
- **degraded**——無可用 CR query face（例：glm isolated home MCP 不隨行，bridge L1 未落地前 glm 腿默認此態）：依 symbol-query-routing／`skills/_common/work-order.md` §7 既有 fallback 宣告實際降級面（rg／Grep；LSP 僅在可用時列入，禁預設），**受影響的結構 finding／claim 逐條標 `unverified-by-graph`（未經結構圖驗證）**；報告頂層 `[WARN] structural context degraded` 只作匯總，不取代逐條標記。**workspace CR 面在場（`.code-reality/graph.db`／`.code-reality.toml`／`.code-reality/scip/` 任一——三形態對齊 db-101 AC#1）的 glm isolated 腿，dispatch 必帶 `mcpSupply=[code-reality]`**（bridge 預設供給 db-101 落地則降為記載面；AIR-295）——有 face 可供即升 live-cr，不默認 degraded。

工具路由階梯與 freshness 語義以 symbol-query-routing／cr-query 為單一源，本節不重刻。**降級不可靜默**——選到無 CR query face 的 carrier 時，unverified-by-graph 標記是強制義務（carrier 選擇與 capability 篩選歸 model-routing，本節不設家族偏好）。

## waiter／watcher consumer governance（`scripts/bridge_waiter.py` 家族）

dispatch⇄collection 完整模式（自動 arm 規約與場景分工、family 起跳值、重啟後恢復 playbook）已隨 plugin skill（「Dispatch ⇄ collection pairing」節）；本節只載本 repo wrapper 治理。watcher 狀態機 frozen spec T1-T9、exit 契約、動態 T 公式（T0=clamp(P50/3, 5m, 15m)、fresh progress T×1.5 cap 20m）單一源＝`scripts/bridge_waiter.py` module docstring（變更走卡 amendment）；bare shell 呼叫 watcher 須帶 `DELEGATE_BRIDGE_BIN=<bridge 絕對路徑>`（watcher 預設只查 PATH，找不到即 clean fail-loud exit 2 附修法——路徑由 installed_plugins.json registry pin 解析，解析面＝plugin skill「Legal entry points」節；0921 dogfood 實證）；雙軸 stalled 判準已對齊 bridge producer canonical（task.rs 單一實作「no ageable data is never reported」——0921 codex 腿 drift finding 修復）；**codex web 長生成期 heartbeat 滯後→worker 軸 5m floor 常態性誤報**（0921 高強度研究工單實證×3，job 本體活躍）——研究類派工帶 `--kind research` 抬 runtime floor 並容忍 advisory；watcher 增量定位＝124 透明 re-arm＋advisory wake＋CollectionReceipt 機驗（native wait 已原生支援 N-job batch fan-in 與雙軸 stuck 觀察——勿重複實作，長期 liveness 語義下沉回 producer）；0921 消費同步已落地：bridge ≥2.0.23 時 waiter 內部自動走 native wake（版本閘自選，arm 命令不帶 wake 參數——`--wake-on-stuck/--wake-axis` 是 bridge `wait` 的旗，由 waiter 內部傳遞），exit 3 wake JSON 轉譯為現行 stalled-advisory（自算雙軸輪詢退役；124 re-arm／terminal collect／exit 2 分流保留）——選 runtime 軸不選 worker，因 codex web 長生成期 heartbeat 滯後誤報×3（前述），選軸即把誤報消化在 producer；<2.0.23 維持自算雙軸（版本閘控雙模，MIN pin 不變 2.0.22——ZCode pin 翻轉後自動走 native）；CollectionReceipt 欄位集權威＝AIR-135.7 AC#2 bounded receipt（watcher 側投影定義在 bridge_waiter.py docstring，非新 schema；AIR-149 EP＝bridge／harness 兄弟契約同源文件；sink 三步驗收程序單一源＝`delegate:delegate-run-output` plugin skill「Receipt acceptance」節，本檔引用不自創）；workflow 層配套（bounded slices／checkpoint 續寫）單一源＝AIR-135.7 契約。

**prompt 邊界 backstop（AIR-267）**：`hooks/bridge_ledger_sweeper.py`（核心＝`scripts/bridge_sweeper.py`；SessionStart 全掃／UserPromptSubmit 90s 節流＋anomaly signature 去重、cwd eligibility、fail-soft 恆安靜）在 prompt 邊界掃 `bridge runs ⋈ .agent-tmp/liveness.jsonl`——running 行無活 waiter（armed−collected 配對＋heartbeat 30m 新鮮度窗，不掃進程）→一行「恢復 playbook：arm waiter」；terminal completed 有 armed 痕跡且無 collected 逾 30 分鐘→一行「可能未收——收線：bridge_show」（R2 前提＝liveness 有 armed 痕跡——真孤兒類；無痕跡〔pre-liveness／手動收線〕不可判安靜）（措辭恆機械層「可能未收」，session 層驗收是另一層零宣稱；terminal 非 completed＝failed-\* 不提醒——v1 收窄，失敗態處置是 dispatch 語義）。提醒面非處置面——arm/show/收線處置恆歸 session LLM；liveness 台帳 waiter 自有、sweeper 只讀。收線三腿家族分工：**waiter＝時間軸（背景盯場）／sweeper＝prompt 邊界（收線 backstop 提醒）／watcher_pairing_nag＝Stop 配對（離場攔）**；WT 證據（`.delegate-bridge/jobs/`＋liveness.jsonl）隨 wt-close drain 歸檔至 `~/.agents/bridge-ledger-archive/<wt>-<ts>/`（0600；v1 無 TTL）。

## Canonical dispatch runbook——長跑腿面＋session label（步驟 6；步驟 1–5 registry pin／provision／派發／watcher 配對／resume 已隨 plugin skill）

**長跑腿禁 MCP face——CLI 背景派（2026-10-09 實證；plugin skill「MCP bridge_wait suits short waits only」條款的 dispatch 面延伸）**：MCP `bridge_review`／`bridge_task` 等非即時面在 harness client tool-call cap（實測 ~30s）內可能**零 dispatch**（ledger 零 jobs——呼叫被殺在 job 建立前；`bridge_wait` 同 cap 只適短等待）。審查腿／judge／任何分鐘級面開場即 CLI 背景派：cwd＝owning WT＋`review --family <f> --base <owning 線 trunk ref——單 WT＝main；省略＝merge-base 預設，顯式 flag 假定 branch 已 rebase 到該線> --caller-harness zcode`（glm 加 `--home-mode inherit`；task 用 `--prompt-file`）。回收＝waiter 配對恆為主方法（bridge_waiter 家族——liveness 歸它）；`show --json` 輪詢＝終端收集／手動 fallback（MCP `bridge_wait` 同死）。上游修正歸 bridge repo（plugin skill 版本凍結）。

**session label（AIR-248 掛名退役→AIR-254.2 seam label）**：job spawn 回執取得 native session id（回執無 id 時 seam `find` 對照 workspace／harness 最新註冊）後 `uv run --project /Users/ctai/Github/ai-guide python /Users/ctai/Github/ai-guide/scripts/session_discovery.py label set --session-id <id> --label <session-label 欄值>`——欄定義與自 id 發現法單一源＝[work-order.md](../_common/work-order.md) §3；id 無法確立（carrier 未註冊 seam）＝跳過不阻塞、禁捏造 id

## grok family authority profile——consumer 判讀面（AIR-226；producer facts 歸 bridge）

> producer facts 單一源＝delegate-bridge repo `docs/ep.md` db-71 grok 段（＋carrier docs `~/.grok/docs/user-guide/18-sandbox.md`）；plugin skill 家族寫面速查已含 contained writer 一行。本節只留消費端判讀依據（AIR-268 收縮——sandbox spec 複刻面刪除改指針）。

- **default leg＝contained writer**（kernel-enforced Seatbelt；AC10 live 雙向驗證終態：containment 成立、`/tmp`＝in-bounds 契約面非缺口）——write 集＝CWD＋`~/.grok/`＋temp dirs。
- **profile 判讀**：`--yolo`／`--marshal`＝無 sandbox 的另一 authority profile（非 contained）——禁把 default face 的 containment 證據外推到該兩腿；enforcement 前提＝profile 套用成功（套用失敗 carrier 不帶圍欄續跑，細節＝db-71 段）。
- **kernel 證據邊界**：enforcement 事實限當前 macOS/Seatbelt face，不擴寫跨平台通用保證；review face 騎 default contained-writer face——reviewer 唯讀紀律是 work-order 紀律，carrier 沙箱面照樣可寫。

## Brief 動詞紀律（caller-side 語義留守；五要素契約本體隨 plugin skill）

brief 的動詞決定可寫 carrier 的行為——審查／調查／盤點類 brief 必帶顯式 `READ-ONLY / no writes / no git`（work-order 模板 review/advisory variant，§6 動＝零），實作類 brief 必帶 scope fence（格式＝work-order 模板範圍限定節）＋禁 commit（commit 恆為主 session gate）；**省略動詞約束＋brief 內出現 CHANGE/ADD/DELETE 條目＝實質實作授權**。`no git` 限定 mutation 面（checkout／commit／push）——唯讀 git 檢視（diff/log/show）經 capability manifest 顯式宣告後可用（先例＝db-69 WO「git diff/log 只讀」）。各 carrier 寫檔能力表單一源＝delegate-bridge repo `AGENTS.md`，禁兩 repo 重刻。案例：muse 審查 job 收到全 CHANGE 條目的 spec brief、漏 read-only 指令→muse 讀完逕行實作 444 行（Writer/Reviewer 分離被打破）。
