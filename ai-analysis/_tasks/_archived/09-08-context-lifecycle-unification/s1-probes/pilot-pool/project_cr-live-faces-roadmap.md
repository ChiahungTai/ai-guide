---
name: project_cr-live-faces-roadmap
description: CR 三弧終態——SCIP 語義/換軌 token 評估/pyrefly PyPI＋滲透量測→AIR-32 範本層＋AIR-33 v0.6.4 閉合；修復迴路定形
metadata:
  node_type: memory
  type: project
  originSessionId: sess_c16a8998-b4b5-41c2-8bf4-1322cfd50753
  merged_from: [project_code-reality-own-graph-db, project_pyrefly-producer, cr-adoption-token-impact-eval, code-reality-tri-track]
---

CR 三弧（建構／採用／資料面）終態全收案。過程查 `~/Github/code-reality` git log；審計＝`ai-analysis/reports/cr-lsp-replacement-roadmap.md`（非 EP——建構在別 repo）。

### code-reality-tri-track（工具建構弧）

三軌責任地圖：泛化機械歸 ai-rules、repo 產物歸各 repo、跨 repo 走 user relay；軌＝mosaic／NT／ai-rules，工具鏈後獨立為 `~/Github/code-reality`（Rust carrier）。

三軌裁定：A1 F9 生成紀律落地；A2 sidecar 預設＋stdout 報告（EP 對過時快照起草屬教訓）；A3 graph_audit 並跑雙實現輸出等價驗收；A4 tour_validate 單括號 WARN 備查不動；A5 CRG 同鍵去重 bug 緩修（caller 邊可推導後僅剩自洽價值）。

**A6 五項勿重辯**：①repo-keyed slot（全局單一 slot 會互蓋）②stamp/[SRC]（sidecar＋stdout 首行＋漂移 WARN；無證據不輸出）③衍生 sqlite（SQL 只做候選縮小、匹配留 Python `_matcher` 單一真相源；**淘汰論證勿重辯**：parquet 點查形態不對／JSONL 僅 3x＋matcher 旁路 footgun／daemon 違 crash-only／dbm 嚴格劣化／活 LSP 無 SHA 標註）④Duplicate symbol 量化：FN multi-DEF 0.58%、影響低且顯性、無 code 變更⑤**refs 語義純度：refs＝所有 non-DEF occ，不可當呼叫數解讀**（syntax_kind/roles 全未填；已制度化進 SKILL.md）

**SCIP caller 邊兩次翻案定案**：caller 邊可從 SCIP 單獨推導（ref occ 行→同檔最內層 fn DEF containment；E2E 96.9%）。教訓：半邊驗證的完美分離支撐錯誤的全稱否定。分工＝互動查詢走 LSP、錨定批次走 SCIP。

架構終局：**三套共存非新增**——CRG（圖級）／lsp_mcp（互動）／scip_refs（錨定批次），擋第四套；終局＝SCIP 邊源注入 graph.db。CRG 地基 tree-sitter（語法）、SCIP 地基 rust-analyzer（編譯器前端）——呼叫歸屬語法不可見，CRG 自改上限 fan-out 級，**唯一到 SCIP 語義等級＝換資料源**。SCIP 動機：qualified_name UNIQUE 去重致 861 顆方法假空（「假 0 callers→誤刪活碼」實戰命中）；懶更新（WARN 驅動）。

獨立 repo＋MCP 統一：動機＝「LLM 讀文件走錯拿假資料」升級 server 機械路由（[SRC]＋stale WARN）；**LSP 互動層排除（user 定案）：LSP 跟 workspace 熱狀態、code reality 跟 commit 錨定——LSP 統包＝進程級 NO**。一次性搬遷（user 推翻漸進）：big-bang 遷入、舊碼留至消費端確認才刪；Rust 化＝靶向 pain-triggered 不全量重寫（NT byte-identical 契約＋hazard 依賴 Python ast）。**NT 鐵律**：治理鉤子走保留 CLI 面 byte-identical；MCP 是加法。plugin 現役；（早期宣稱「現行 session 的 MCP server 是啟動時舊進程——重建後次 session 才生效」**09-06 觀測推翻**：更新 binary 後舊 session 的 MCP 呼叫即時回新版行為，免新 session——詳 [[reference_code-reality-mcp-cli-faces]]）。雙活期教訓：修復落點＝活的消費路徑（user 糾正）；import 探針須中性 cwd；盯並行 repo commit；EP pseudo code 對現有介面先查證；ZCode 慢啟動真兇＝殘骸目錄卡 lock（[[zcode-platform-facts]]）。

ai-rules 三接線（歷史，被 cutover 超越）：implement snapshot／code-review 模式 B／debrief §3 自產 §5 hub——工具細節零重複；review-engine 刻意不動（DIP）。教訓：**新 gate 觸發語義不可掛既有「條件式」動作**（綁「補記 baseline」＝永不觸發）；**EP 對照落點＝機械底稿跟消費者走不跟編排器**（code-review 需獨立自足、post-build 純編排不擁方法論），可見性掛自動鏈終點。授權面 CRG MIT／rust-analyzer MIT-Apache／scip.proto Apache-2.0／protobuf BSD-3。08-29 修復：條文寫 MCP 但 spawned agent 只有 Bash→spawn prompt 必帶 CR **CLI** 清單＋誠實界線（CR 全綠≠無 ripple）。

CRG 共享 HTTP server（興亡存查，已全清）。**lsp-python 之死不適用 CRG＝路由機制**：header 路由死（user-level 單一 entry 不能逐專案換 header）、CRG 走 tool-call `repo_root` 參數路由活——**MCP 接不進先查路由是 header 還是參數，命運完全不同**。省略 repo_root＝自信假陰性（「graph is empty」非報錯）；ZCode MCP 兩層（user config＋專案層），只查 user 層就宣稱未接是錯的；serverInfo 版號是上游漂移勿信。**退役清場必含 hook matcher 註冊**（config／範本／腳本／SKILL.md）——matcher substring 對改名後工具名不命中＝靜默 no-op（[[multi-harness-architecture-direction]]）。

cutover 定案：CRG 不可停——code-reality 自身依賴 CRG graph.db＝分層互賴；LSP 不禁用（Python repo 符號真相仍只有 LSP），切換點僅「Rust repo＋SCIP 在場→符號引用查詢 CR 優先」；**面別陷阱**：plugin MCP 工具＝refs/callers/closure/audit、CLI 無這些子命令——instruction 引用須標面別；uv run 全域炸＝多包 repo 刪 `packages` 後 auto-discovery 歧義，修＝`[tool.uv] package = false`。

NT chain_tour parity（收案 PASS）：Rust 重產 arch tours 76/76 對照 Python corpus，差異全落 pattern 轉義方言（re.escape vs regex::escape——語義等價、byte 不同）；三腿驗證＋否證測試（改 pattern 必 FAIL）。**判定＝語義等價非 byte-parity**（Rust port 修過真 bug、重建 confound）；輸出隔離＝`--out-dir` 樹外。

教訓結晶：收編快照會過時——同步前先 diff 源頭；並跑雙實現輸出等價＝強於 fresh-eyes 靜態 diff；歸檔文檔引用用 symbol 錨非行號（[[line-anchors-rg-before-handoff]]）；數字 claim 禁心算（13 名心算錯 12）；exit code 禁過管；契約被消費端依賴時「勿改」＝與鉤子端共同演化；relay 主張先驗現況（[[relay-claims-verify-current-state]]）。

### cr-adoption-token-impact-eval（採用弧）

**初測＝減量機制沒啟動**：觀察窗 CR 結構查詢＝零、implement requests 反增。兩教訓：①prose 接線對 LLM 消費者無機械閉環——**宣告式依賴≠行為式依賴，白名單 agent 工具可見域才是生產路徑**；②滲透量測 pattern 被檔名誤配汙染——契約帶 subcommand 錨（已進 cr-query skill）。implement 減量槓桿在批次化/Read 紀律非 CR；CR 價值主張＝結構證據品質。

**升級①**：tier-pinned `cr-research` agent（lite pin＋CR MCP 白名單 in-path）承接 EP 段落 0，生效＝新 session。**複測＝換軌生效**：結構查詢 0→16 次、EP fresh input −36% 但 requests 持平——**token 紅利在 fresh input 非 request 數**。殘餘＝引用落地斷鏈（查了用了沒留痕）；修法＝research 產物落檔 task 目錄。三改善（user「都做」）：①impact_radius 修復（`/` 邊界匹配＋真 miss 帶 note）②offline_backtesting＋trading_lab graph.db 建成 ③cr-research 紀律行（module path 不含路徑；絕對路徑＋limit）。**常態化＝CR 健檢併入 `corrections-weekly`**（`cr_usage.py` 量 CR 調用 vs rg 對照；零使用一週＝滲透退化訊號）。

**升級②＋投影接線**：registry review agents tools 白名單四顆 CR MCP 全名＋MCP-first fallback（claude 側減 MCP 行——CC 接線未確認，分歧記於 agents/AGENTS.md）；新 session 雙 probe 實呼 PASS。投影圖四檔：execution-plan 段落 0（整合器型/跨模組觸發、`[projected]`＝宣告非證據）＋ep-review F3 HOLE/MISSING/WIRED＋工具表。dogfood：MISSING/HOLE ✓；**WIRED 歸因縫**（minted_edges=1 鑄造成功但 graft +0、claim 判 HOLE——鑄造↔查詢歸因掉鏈靜默）交 CR session 修。遙測警示：skill 歸因有暈染；宣稱前抽 part 表驗窗口。

EP2 換軌（凍結勿重辯）：implement 全鏈 CR 分層換軌——主 session MCP 優先／registry agents 白名單／generic Explore CLI 寫進 spawn prompt。關鍵：implement 的 review agents 是 Explore 型非 registry code-reviewer——白名單 MCP-first 只適用 /code-review dual-context。

**09-06 滲透量測→AIR-32 範本層落地（弧閉合，卡 Done）**：EP2 換軌處方被量測證偽——ZCode db.sqlite 三天量測（Skill 調用 session join part 表掃工具）：review-flavored Explore spawn prompt 帶 CR CLI 指引 **0/66**、registry code-reviewer 掛白名單＋定義檔 MCP-first 指引仍 **~4/40** 觸發；唯一穩定重度使用者＝cr-research（spawn prompt 明示）——**觸發載體定律：prompt 明示是唯一被實證的觸發形態；註記層/定義層處方不會自己觸發**。落地：review-engine「spawn prompt 工具紀律」新增 CR 接線查證段＝單一源（registry=MCP 形態／generic=CLI 形態、callers 空=嫌疑補 rg 互補腿、engine 缺場 WARN+fallback、無 callable 變更標 N/A），agent-review-cycle／workflow-review-pattern／code-review 三模板掛硬性必含行、implement 階段 4 改指向單一源、handoff Phase 0 補 EP 弧 snapshot 行（handoff 續跑弧 4/4 跳過 snapshot 的結構性原因＝接力 session 依 handoff 行動、不重讀 skill 階段）。AIR-33 三缺口（class DEF 查無／CJK emit panic／heal churn）經 user「太早查詢？」challenge 複測精確歸因（時機/stale 假說否證、panic 間歇、查無 DEF 反覆觸發 full heal——量測細節見 [[reference_code-reality-mcp-cli-faces]]）。**AIR-33 全弧閉合（09-06，卡 Done）**：code-reality `f75b86a`（v0.6.4）修復三缺口，owning 側 L4 驗收全綠——**驗收設計先公佈再機械執行**（step 0 安裝面 gate＝`--version` vs main HEAD；三 class 樣本＋函數對照組防回歸；CJK regen ×2 零 panic；重複查詢計時 0.08–0.11s 零 heal；MCP/CLI 同結果）。**demand 卡→/handoff 跨 repo→修復→user relay→owning 側驗收**＝cr-demand 迴路定形——relay 數字（53 suites／15 callers）是修復方 L2，驗收只認自己跑的。兩教訓：①第一次 relay「修好了」過時（修復 session 死在考古後、零 commit——重發 handoff 帶戰利品續弧，戰利品續傳讓第二腿零重做）；②**b30af73 考古翻案＝文檔化限制非修復**（commit 標題「class DEF semantics」實際只把「class 名非可查 key」寫進 SKILL.md）——「勿重做」清單以實際 diff 考古為準，非 commit 標題。**09-07 結案 relay 驗證全過（接收側機械複核）**：f75b86a＋tags v0.6.4-v0.6.7 在場（後續 UX 弧＝hook burst debounce／hook install 原地升級＋舊格式 nudge／hook pin release-face 優先消費端 log 不吃 dev-face WARN）；三缺口根因——①class DEF＝兩層 lookup miss（engine Bare matcher＋cache ingest 皆只收 fn-tail；修＝class_tail_name 端錨定抽取器＋SCHEMA_VERSION 1→2 透明重建）②CJK panic＝emit 期重讀磁碟 vs AST byte offsets 的 TOCTOU（修＝api::drive 單讀快照＋always-on assert）③反覆 heal＝活躍 writer mtime staleness 非查無 DEF 觸發（修＝churn-armed cooldown）；ai-rules 側零文檔同步需求複核成立（class-query 限制行不在本 repo）；CR plugin cache skill 0.6.7 已載修復事實。卡 Done 已進版控（list 可見）。

兩種消費 UC（「兩種 UC」指此框架非 Capabilities UC）：**UC-A 理解既有程式碼**：cold-start tours＋chain；退役 explorer/scope/runtime UI；核心「知道有關係，然後呢？」——動作是去 code 跳轉不是讀圖。**UC-B 變更伴隨**：弧起 snapshot→審查 transition→走讀 delta_tour→收斂回 UC-A；**接點在「入 plan」非「即生成」**（一鏈 ~5.6M tokens；事件加菜單項不加開火）；arc 收尾三選：新機制→plan 加行／實質改動→標待重生成／內部調整→不動。**delta_tour 唯一流程內自動入口＝debrief**（tour 消費者是人）；**刻意不接 post-build**（機器鏈＋產了沒人走＝受眾錯位）。corpus-recall：超瀏覽閾值後「一個個看」不會發生——檢索前門缺位（找不到＝沒寫）；輕量程序 skill 先行，機械模式重複後才沉澱工具（YAGNI 不上向量）。

scan-project ×cr 拆軸（拆軸非取代）：dep 軸（Module Boundaries）cr 可接手且更強——三級 fallback：cr index→cr graph；CBM graph→CBM（C+Go repo）；否則 scan-project／Explore。doc 軸不可取代：cr 符號世界沒有「文檔宣稱什麼」——instruction_files／findings X6／dir_inventory 是 instruction-init 核心輸入。實務：unfamiliar codebase 通常沒 cr index——cr-first＝順手 `code-reality build`；scan-project 零依賴 fallback 價值仍在。

C+Go 語言面評估（advisory 未實作）：data plane SCIP-based producer-agnostic——加語言＝加一腿 producer；spawn（外部 bin 產 SCIP）vs embedded（自建 crate 鏈）。**Go＝低-中先做**：scip-go 現成、與 RA leg 同構；0.x 社區治理（pin 留意）。**C＝中-高 spike-first**：scip-clang；三成本＝compile_commands.json 前置（Make repo 須真實 build——「必須 build」是 make 生態代價非 SCIP 通性）、C 語義噪音（macro/header/function pointer）、無 namespace 需 minting。三結構性後果：①C 索引非唯讀、與建置成敗耦合 ②**freshness 經濟模型被打破**（每索引＝compile 級 pass，self-heal 不成立）③解釋 CBM 近似路線必然性。**建置依賴光譜**：tree-sitter/CBM 純讀→scip-go 下載不編譯→rust-analyzer proc-macro 編→scip-clang 完整建置＋compile 級 re-index。**ts 腿產自己的 cache kind 直建 graph，不偽造 SCIP 格式**（語法事實假裝解析事實＝語義不誠實）。

/implement 消耗分析（兩波落地）：**實測推翻理論**——Workflow quorum 在 ZCode 是死路徑（workflow_run 全空）；**真 hotspot＝主 session 零批次**（76% request 只帶 1 tool call）＋**大檔反覆全讀**（86KB 檔重讀 9-12 次、每次 +25-30K tokens 永久佔 context——LLM 無法搜尋自己 context）。落地：批次化＋Read 紀律（重查禁無參數全讀→rg/片段）＋驗證組合命令＋pytest 背景跑。**量測口徑**：場景內 M1 為主指標（82.0→76.9→68.7% 單調下降）；絕對消耗不減反增（工作量成長吃掉增益）——**效率看 per-action 非 total**。方法論：cost 分析先查遙測；per-skill 成本宣稱前抽查窗口命令構成（歸因暈染）。

### project_cr-live-faces-roadmap（資料面弧）

方向定案（勿重辯）：**CR＝AI-native 語意層**——工具面為 AI 查詢模式設計（refs 帶 provenance、callers 帶 site、stale 守衛），非把 LSP 薄翻譯給 AI；「統一＋超越」＝一 plugin 全語言＋graph 智慧，取代是自然結果非目標；CC 內建 LSP 不必關。翻案教訓：「完全取代 LSP 架構上不成立」作廢——pyrefly 是 in-process 引擎本體，live 型別面變分期可達；**可行性判決前先查 git-dep 實體**（`~/.cargo/git/checkouts/` 非 registry/src；頂層 `lsp/` 是 VSCode extension、CLI 在 `pyrefly/bin`）。型別面：LSP↔MCP bridge 語言無關基建（副檔路由 .py→pyrefly-lsp、.rs→rust-analyzer）；bounded context 物理化＝結構面（batch/冪等/graph 真相源）vs 型別面（互動/增量/工作區狀態）；pyright 僅存 golden oracle。包裝＝雙源分治：plugin 綁 standalone 級 skill（隨 CR 發版）、不綁 ai-rules 深度級；準則＝**揮發度**。

P0-P3 終態：P0 SCIP 雙語料＋**CALLS/REFERENCES 邊拆分**（ruff parse 分類 pyrefly ref rows——非獨立語法 producer）；P1 Python bridge：新 crate code-reality-lsp-bridge（stdio MCP、lazy spawn、hover/check_file/edit_file）；class 型 parity 單側斷言誠實排除（顯示深度本質不同——記錄非假裝通過）；P2 Rust bridge：副檔路由＝extension routing 非 backend 參數；rust-analyzer 三 probe（didChange 被無視→停滯重發／-32801 暫態重試）；CJK 檔名 percent-encode POC 修復；P3 lsp-python :8000 全域退役（~6.3GB）。

W1-W5 pyrefly 生產者線（全終結）：pyrefly 取代 scip-python 成 Python occurrence 預設生產面；import_legacy 完全拔除。實作：`crates/pyrefly-index`——引擎 git-dep **pin rev 非 tag**（tag 落後 ~2,445 行；crates.io 只有占位；升級＝顯式換 commit）；走 **SCIP protobuf face** 非直寫 cache。refs 密度（預期管理非 bug）：~12.7× 低於 lsp golden——pyright 計所有 attribute 存取＋constructor call 經 dunder 崩縮落 `__init__`。**cr 四裁決勿重辯**：①SCIP face 非直寫 cache ②`lsp_harvest` 保留＝golden oracle 產生器 ③scip-python fork 降級 fallback（cwd-workspace＋fatal-partial-index 兩坑）④`producer_of` 對 pyrefly 落 "scip"＝接受。B7b：dataclass/object-inherit mint 偽建構子＋補 DEF（class-callee missing 4,957→~110）；B8 真空檔＝語義空 document＋fn-tail gate 設計性濾除＝非 bug（loud 計數）。gate：95.42% 全歸因真匹配——**user「95% 夠了」＝接受**；W1 度量腳本 keying bug 曾低報——[[feedback_settlement-scripts-are-code]]。W4 sidecar silent-failure（實測）：不失效舊 sidecar→build 靜默產壞庫→雙層修復（producer 自動失效＋mtime 閘門 fail-loud）；W4b：PATH rust-analyzer 是 rustup proxy、依 cwd 解析 toolchain 靜默降版——直呼 repo-pin binary。刷鏈兩步：`pyrefly-index`→`graph_db build`（冪等全量）。W6 Rust macro/dyn＝**觸發式不建**（demand-triggered：判斷權在感受痛的消費端——`[cr-demand]` 卡→hub sweep→user 裁決）；**RA SCIP 幾乎零 std-method occurrences＝occurrence-attribution oracle 只對 workspace 符號有效**；py_calls 前提修正（ruff 只分類非獨立 producer）；**4.58%（Python legacy 殘差）vs 19.8%（Rust tree-sitter 互補）勿混**。翻案：RA 榨乾 spike 先行、首選 syn-based producer；cargo expand 否決（行號契約全毀）。

graph.db 處置（長期有效）：**永不 commit**——冪等重建、machine-specific、百 MB 級；ignore 二分：fork repo 自帶 `.code-reality/.gitignore` 寫 `*`、自家 repo root 一行 `.code-reality/`。**位置＝in-repo（終態）**：`~/.mosaic/code-reality/` 集中 slot 已退役，四 repo 各自 in-repo——repo 事實歸 repo／worktree 獨立；代價＝每 worktree 一份＋gitignore；重議觸發＝worktree 數量/體積痛。儲存對標詳 [[reference_generated-artifact-storage-patterns]]。刷新＝WARN 驅動非排程——ENOSPC 教訓 [[mac-nightly-sequence-oom-crash]]。schema（存查）：nodes 以 producer symbol 為鍵、edges 一行一 call site、derived flows/communities build 後置物化。

legacy 退場代價（語義損失存查）：impact_radius 7,905→275＝TESTED_BY 33,117 隨退場；tree-sitter 互補面（macro/多行 ~19.8%＋TESTED_BY）永久消失——未來選項＝自建 tree-sitter producer；量測分母宇宙跟著換代。

freshness／分發（終態）：每 bin 嵌 `CR_BUILD_REV`、`--version` 印 `<pkg>+<rev>`（查證直讀非 mtime）、stale WARN 雙信號＋post-commit hook 自動重裝。**分發收斂＝PyPI 單層**（npm face 整拆）：wrapper deferred install（exact pin→exec；升版 `--force`）＋**PEP 668 地雷**（uv-first、不做 pip fallback）＋`CODE_REALITY_BOOTSTRAP=off` dev 逃逸；npm 拆除＝CC-only＋單平台 wheel＋第二 registry 負擔；`build` 傘形一鍵。細節真相源 [[reference_code-reality-mcp-cli-facts]]。cr-query 改名教訓：**rg 範圍須含 root `*.json`**（漏掃＝新名觸權限提示）；CLI op 名 vs MCP tool 名勿混淆。

驗證電池關鍵發現：🔴 hazard_registry class 回歸（已修）——pyrefly SCIP 無 class DEF→graph 全 Function→`hub_refs` 對 class 靜默退化→「0 callers 可刪」安全網對 Python class 靜默關閉。**教訓：新面驗收電池須涵蓋每個語義面的真實消費案例**。文檔死名清了、binary 輸出面還有（next_tool_suggestions 印死名）——兩面分開掃；監看 label by 內容非 session ID 順序。

治理：**hub-relay**——CR 回執→hub 翻 ai-rules 真相源→產下游 handoff→roadmap 打勾；user 郵差貼上、gate 不跨線；多 worktree 文字同步＝只改 main 收一 commit、其餘 wt rebase。**gate-first 預發**：上弧 gate 未過可預發下弧 handoff（入場檢查＝prompt 第一步）。

關聯：[[reference_code-reality-mcp-cli-facts]]、[[feedback_relay-claims-verify-current-state]]、[[agents-registry-split-design]]、[[reference_cbm-architecture-tree-sitter-hybrid-lsp]]
