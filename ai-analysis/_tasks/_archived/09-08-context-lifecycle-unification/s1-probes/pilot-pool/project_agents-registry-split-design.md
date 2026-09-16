---
name: project-agents-registry-split-design
description: agents registry/dispatch 弧群終態：AIR-13/28/29＋09-06 健檢＋雙源去重落地＋registry slim 不可行定論＋symlink 判決重驗中
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5615b021-a44d-4c74-b58e-b5ba869564d7
  merged_from: [project_agent-mcp-remedy-verification-pending, project_research-flash-provenance]
---

merged_from: air-29-two-axis-registry-refactor, full-lifecycle-agent-arc-spec, air-13-unified-subagent-architecture

agents/registry/委派弧群（AIR-13 委派線→AIR-28 任務特化→AIR-29 兩軸重構）全收案。現行真相源：`agents/roles/`（authoring 單一源）＋`scripts/sync_agents.py`（生成投影）、`agents/AGENTS.md`（harness 軸 dispatch matrix＋execution contract 表）、model-routing skill（model 軸 tier×provider 解析表＋external-runtime 委派規範）、`skills/_common/work-order.md`（工單契約）。muse CLI 事實＝[[muse-code-cli-facts]]。

### project-agents-registry-split-design

registry 機制與平台邊界定案（兩家 registry runtime 驗證通過；部署結構終態見 air-29-two-axis-registry-refactor 節）。

- **registry 內是實檔拷貝**：現行理由＝per-harness frontmatter 差異需整檔分歧（zcode pins／claude 減 CR MCP 行），symlink 是整檔單位無法承載差異。**file-level symlink loader 可載入**（09-06 新 chat session 對照實驗：symlink／實檔探針雙雙載入，推翻 08-29「檔案 symlink 靜默不載」舊判決——舊判決疑為快照過期混淆：探針 mid-session 放入、未經新 session 即判）；hardlink 被 clone 斷不可用、symlink git 原生追蹤，**目錄 symlink 可穿透**（`~/.zcode/agents`→agents/zcode、`~/.claude/agents`→agents/claude）。開箱驗證缺口＝只驗 listing 未驗 spawn——兩臂都要 runtime 驗。
- **registry 快照語義三面實證**：config、agent tools 白名單、agent 定義檔皆 session 啟動快照——新增/變更 agent 定義一律需新 session 才生效；mid-session 修改 body/tools 均不生效（建檔 session spawn `Agent type not found` loud fail）。要重啟刷新的僅三例＝agent registry＋skill 清單＋MCP server 進程（MCP 面異常先查 binary 版本代溝再判 bug）。
- **spawn probe 五定案**：①自訂 tools 不排除 harness 隨附 MCP，但 user-config MCP 全被排除（官方文檔宣稱不精確）②tools 留空＝工具全集③subagent 也載 rules bundle——rules 與工具面可斷裂④共用定義列 union 安全（不存在的全名靜默忽略）⑤tools 行列 Grep/Glob 屬文檔/runtime 不一致（零調用）。
- **MCP 全名三態邊界（d32ddb0 定版）**：連線中 server 全名＝可列可呼叫；未連線 server 全名＝**整顆拒絕 spawn**；萬用字元 `mcp__…__*`＝靜默 no-op（spawn 正常但工具不掛）——兩種失敗形態不同，除錯先分辨。跨 session agent 定義去 MCP 化（遠端 URL 先 Bash curl 落地再 Read）。
- **copy-vs-reference 定論**：檔案系統/格式層引用全堵死，唯一活路＝**流程層引用**（source／registry copies=build artifact／`cmp`=正確性檢查）。多 wt 文字同步＝只改 main 一處收一 commit、其餘 wt rebase。
- **命名與封裝**：agent 名釘 tier/能力語義不釘 raw model 字串；包 skill 包指標不包內容（prompt 寫「先 Read SKILL.md 再執行」，蒸餾進 prompt＝雙真相源 drift 溫床）。新 agent 登記＝進 registry 同步補 model-routing 表列＋至少一個消費端接線（rg 驗非孤兒）。plugin＝發佈/慢節奏面、registry＝日常迭代面；plugin 命名不含引擎/harness（codex-plugin-cc 之惡）；不搬 marketplace 快取安裝層（stale＝以為測新實跑舊）。
- **flash/vision/ccr 實證**：vision tier 實戰 PASS（flash 視覺逐字忠實、與 4.6V 失敗模式互補——視覺任務歸 vision-review 人設）；**flash 無速度紅利**（telemetry：duration 由生成長度解釋）→lite pins 不擴大（mem-distill/cr-research＝任務驅動授權），剩餘價值＝並發寬度＋主模型卸載；thoughtLevel sticky bug 終局＝零改動等上游修（model pin 不受影響——逐字到 wire 實證）；ccr 終局＝direct-first 常態（ccr 斷 ZCode usage 額度顯示），降為 CC/VSCode 側選配。
- **ZCode MCP config 拓撲**：user-level＝`~/.zcode/cli/config.json` 的 `.mcp.servers`（鍵名非 `mcpServers`）；專案層＝`<repo>/.zcode/config.json` 同結構——**開陌生 repo 先檢查其 config，連上即執行其命令**。子系統不對稱：MCP 有專案層、hooks 專案層被忽略。
- **probe 方法論**：spawn 前主 session 先自呼同工具留 golden 對照——隔離「server 壞」vs「不注入」；寫入 session 的 spawn probe FAIL 屬預期非 bug。E3 A/B 校準：MCP 臂收益＝「一次查對」，最大節省在錯誤 finding 的下游輪次（成本 +69% token）。
- **溯源方法（可重用）**：誤寫檔定位＝telemetry `part` 表 `json_extract($.state.input.file_path)`＋`$.tool IN ('Write','Edit')` JOIN `session`，檔案 mtime 對照 part 時刻鎖定寫入 session。教訓＝跨 repo session 寫「本地」檔前先驗 symlink 指向。
- lsp-python 路由教訓（已退場）：payload 路由任何 harness 都給得起、header 路由 user-level 單一 entry 死——**工具不死於壞，死於遷移掉隊**。

### air-29-two-axis-registry-refactor

部署面兩軸重構（AIR-29）**已終結**（卡 Done＋歸檔）。起點＝user 挑戰「registry 在 cc/codex/grok/muse 就不能用了」機械證實：10 agent 中 8 個 ZCode-only、12 命令檔引用 ZCode-only 名稱（引用即死）。UC 盤點定案 role 集合不動——10 特化全過四判準（可凍結/單一 writer/紀律密集/跨弧重複；反判準＝判斷密集永遠主 session）、主 session 保留 7 處、consistency/metadata-sync 不特化（低頻 YAGNI）；負空間明講不拆：編排類、B 軸 viewport、L1 閘門、EP 作者/judge。缺口全在部署面 → EP 收斂部署面 only。

- **終態架構**：`agents/roles/` 單一源（①目標②做法③角色特定節；零 model/harness 字樣）→ `scripts/sync_agents.py` 生成 zcode/（＋frontmatter pins）與 claude/（−model/thoughtLevel/CR MCP 行）——**pins＝部署預設非 authoring，生成物禁手改**；dispatch matrix 兩軸：harness 軸→agents/AGENTS.md、model 軸（tier×provider 權威表）→model-routing skill；registry 檔名不變＝消費命令零改動。**harness×model 正交軸裁定**推翻舊「zcode pins＝唯一 provider 耦合點」設計。tier 詞彙收斂 **full/vision/lite**（F3-A 裁定；AIR-24「tier＝能力檔語義非模型綁定」的徹底執行）。
- **implement 關鍵點**：EP checkpoint 3/4 互斥偏差（canonical 化使 exact-bytes adoption 永不可能）→等效審計（HEAD 拓撲 cmp）＋顯式 rm+sync；CC L4 10/10 named PASS＋unknown-name 反向守衛；三視角 review 24 findings——pin parity 交叉雙命中修為值層比對＋負向測試（provider 換代不改 dict 會靜默上線舊 pin）、撕裂寫入改原子寫（temp+os.replace）；post-build muse 5 findings——parity/mismatch fatal＝**exit 2**、drift 保持 1；終態 124 tests。
- **Role contract 首消費成功**：muse 工單按 work-order §2 寫——role body 引用零重寫、requirement 查表得 muse-spark-1.3 xhigh；muse 輸出遵循 roles 方法論＝體系運作證據。
- **dispatch 預設（quota-failover 定案，harness 主軸版）**：GLM 5.3 主 session／flash lite 執行檔精確分工；muse code 雙身分（直用開發＋bridge 委派）；訂閱變更只改 model-routing skill 對應節。CC 端 provider＝zai（GLM backend，settings.json env 映射為證）；**CC lite 詞彙終態＝`sonnet` 別名**（dispatch 不綁 backend id；最低 sonnet/terra 級）；codex 容量 258K；CC named-agent＝inherit 主 session 模型，省成本靠 spawn-time 指定；muse 直用消費 roles＝文檔參考扮演（無 registry 機制）；muse 端跨家族審查缺 review 鏈＝未來項。
- **殼圖選型教訓**：mmdc SVG 全帶 `id="my-svg"` 碰撞→至多一張 inline、其餘 iframe；archify 全景 iframe 標「規劃時點產物非實作終態」；層次剛性圖用 HTML 塊圖非 flowchart；殼 badge 不提前 ✅（卡結案才升）。
- **上線健康檢查（telemetry model_usage 機械統計）＝zcode SAMPLE 承接**：pins 100% 命中零漂移（flash 系全跑 glm-5.3-flash、reviewer GLM-5.3 主＋flash 條件降級＝政策如設計生效）；硬錯誤僅 3 筆全基礎設施面；1302 rate limit 全數重試 completed；各 agent 真實流量在場、抽查尾段 contract 符合。但書：DB 只覆蓋 ZCode 端。快照制＝新定義須新 session 首例 spawn 才驗到。
- **機械事實與已決**：body 三份逐字相同＝生成投影 by design（zcode 約 +98B pins／claude 減 CR MCP 行、無 model 欄）；sync_agents.py 四 modes（check/map/sync/adopt-legacy）＋OWNERSHIP_MARKER＋同名 unmarked 檔 fail loud。`--check` drift gate 接線**已證實**：check_single_source.py 有 agents_projection_sync invariant（委派 sync_agents --check，drift＝critical；generator 缺席＝important）＋週日 23:00 治理 cron 覆蓋＋tests tripwire 釘零寫入——無 CI 下 drift 最長潛伏到週日 cron（ownership marker 擋手改生成物於下次 sync fail loud）。
- **09-06 架構重複檢視（user 發起「是否太多重複 bad smell」；處置已落地＝5 edits＋機械驗證，殘餘 consistency 兩筆 🟢＋commit）**：三份實檔拷貝＝平台約束正解非 smell（--check 實跑 exit 0）；真 smell＝agents/AGENTS.md「dispatch face 與收法」節與 model-routing skill「bridge 必經／完成回報收法」節雙源（收法演進快＝分叉必然，09-05 過期派發事故為同型前車）。四行處置：dispatch/收法細節刪＋留 pointer（讀者盤點＝A registry 維護者／B 派發者／C 委派者三類讀者無一為它而來）；**三態判定表＝repo 唯一份放錯家→搬 model-routing（非刪）**；thin forwarder 治理原則（不長特化 agent）留 registry 檔（registry membership 政策）；flag 形態表收/留＝user 裁量未決。_common 抽共享判準＝**≥2 真實消費者**（work-order.md 先例），本例僅 model-routing 一個 → pointer 即 _common 模式等價、不需新共享檔；flag 形態表已收（user 核可——與權威表低度差異化鏡像非真摘要層）。殘餘＝consistency 🟢×2（model-routing 工單模板 blockquote 搬至 #### 前＋description 觸發詞補「三態判定」）＋commit 待確認。
- **CC 官方文檔重複建議查證（09-06，user 指定查 ref-docs 鏡像＋skill-creator）**：agent 檔無任何 include/投影機制——官方對重複僅 override（同名近者勝；同目錄同名＝載入序未定義＋/doctor 建議 remove all but one）與 namespace（plugin skill 兩份共存）兩途；skill 內容重複官方解方＝progressive disclosure（references/ 按需讀＝_common 模式同構）；描述重疊＝官方點名路由風險（支撐 10 role 粒度不合併）。官方證據全面支持現行架構。
- **「symlink 若可用」設計沙盤**：檔案是原子——frontmatter 差異（pins、tools 減行）與 body 同檔，symlink 可載入≠registry 可 slim 成 10 條 link。唯一收斂形態＝pins＋tools 聯集上移 roles/＋雙 registry 全 symlink；三讓步＝①roles/ 中性紀律放棄（model 字串入共用檔）②Claude 對 thoughtLevel 鍵容忍未驗③Claude 對 tools 行 CR MCP 全名容忍未驗（ZCode 端已知：未連線全名＝整顆拒絕 spawn）。ZCode Agent tool 無 spawn-time model 參數（CC 有）→放棄 pins＝lite 全 inherit 主模型、省成本架構蒸發。git 原生追蹤 symlink（clone 存活）＝當初測 symlink 非 hardlink 的原因；就算判決 yes 也要先過兩個 Claude 容忍 probe 才值得換。
- git mv 對 untracked 目錄 fatal（source directory is empty）——untracked 歸檔用普通 mv。

### full-lifecycle-agent-arc-spec

AIR-28 任務特化 agent 弧**已終結**（commit c83ddf4、卡 Done、EP 歸檔）。定義：每個重複任務型別有自己的 registry agent（model＋effort＋tools 白名單，按分工律 tier 對號）；**effort 是第一公民**——家族對譯 ZCode `thoughtLevel`／CC `effort`／muse `low~ultra`／codex `none~xhigh`（現值單一源＝model-routing skill 解析表）；workflow 化範圍＝開卡→commit 整段（不限 deep-work）。

- **交付**：全生命週期 execution contract 表（每段 owning orchestrator/registry name/tier/artifact/failure fallback；**commit 拆 preparation〔可派 agent〕＋consent gate〔永遠主 session〕）＋registry projection map＋effort 對譯表；HIGH SIGNAL filter 單源 code-review-and-quality（quality 類僅 instruction 明示才報）；review-engine mixed-tree 歸因＋spawn 工具紀律（不把「工具皆可用」當 runtime fact）；workflow-review-pattern **分級 verify node**（Important+ 錨點批次〔單 lite agent〕→Critical 3-verifier quorum＋compliance/judgment 分流）；**P4「最近者優先、子層覆寫上層」**；`skills/cross-verify`＋cross-verify-investigator（單一參數化六軸、源缺場回報 unverified 不腦補）；deep-work `--agent <name> --bg`＋ownership state machine（dispatch from committed ref→attach 驗收→consent→commit→rebase 回主線閉環）；illustrate 殼生成分工三 tier＋機械底稿（數據宣稱只從 JSON/命令輸出原文帶入）＋確定性再生 diff。
- **三個 critical 修復（codex 抓到、機械確認）**：①investigator frontmatter 硬掛 CR MCP 全名→無 plugin session 整顆 spawn 失敗（即 registry 節「未連線全名整顆拒絕」實例）——**去 MCP 化**（tools=Read/Bash/WebFetch/WebSearch，cr 軸走 CLI）；②workflow 錨點批次裸 `id` join 跨 dimension 同名錯配→`${dimension}:${id}` namespace＋DimensionVerdict required＋verifier prompt 餵主張＋suggestion 不靜默流失；③殼 false-green（宣稱 7/7 但 FAIL 行在場）→**修驗證合約本身＋同命令重跑刷新**（非只改報告）。
- **L4 實證**：cross-verify 對 impl-flash 交叉對帳 corroborated、db 軸拔源→`[WARN] 源缺場` 不腦補（SM-9 端到端成立）；log 軸 gitignore 遮蔽首掃——`--no-ignore` 重掃見真面；CC modelID 抽查＝GLM-5.3-Flash 逐字達 wire、effort 面 variant=`max`（sticky 蓋定義值）。
- **失敗家系（不泛化）**：1302/classifier 重試≤2、1301 禁同 prompt、1308 等重置、429 backoff。
- **教訓**：①平行 session 共弧——依落檔制消費他 session L4 產物：採用不覆蓋、只修被機械證據反駁的數據點（消費側重述單源表 schema＝表本體外流，機械檢查抓得到）；②Edit old_string mismatch 揭露潛伏 CJK 損壞（`覄`U+8984）；③user 對代號標籤會失憶——重提必附一句內容摘要；「查得到他怎樣做嗎」＝先查鏡像文檔再答。mypy 本 repo 未配置＝commit gate 記 ruff＋pytest。

### air-13-unified-subagent-architecture

external-runtime（muse/codex/grok）委派線全收案（本節已併 muse eval、bridge ledger、review 資產解析三弧）。

- **AIR-13 終態**：build 4/4——muse 工單全一次成功、GLM acceptance reviewer 4/4 accept、重工 0（reviewer 抓 writer 報告層失準：**契約讀料順序 writer report 最後＋獨立重跑**有效）。交付：model-routing external-runtime 節（family 表＋五條 eligibility gate＋reviewer 交接契約）、agents/AGENTS.md（thin forwarder＋dispatch face＋三態判定）、`skills/_common/work-order.md` 十節模板。
- **dispatch face 定案**：wrapper 提前 complete 是系統常態→muse 委派預設主 session 直呼 bridge CLI；**已由 AIR-26 push 化取代**（背景 Bash 掛阻塞 task/wait、exit 喚醒、poll 降 fallback）＋bridge `wait <jobId> [--timeout]`。**bridge 必經（muse 委派唯一入口）**：禁直呼 `muse exec`（上游入口攔不到，規範面 ai-rules 是唯一有效槓桿）；完成回報攜 jobId、缺席＝入口違規（ledger 可考性）。
- **muse plugin 弧（0.2.x 全落地）**：定案自寫 plugin（唯一吃到訂閱 flat-rate；API 供給路徑全 PAYG）。**計費定案**：全程無 API key＝全部 runs 計訂閱窗口、standard 模型 runs 也吃訂閱（**勘誤：user 從未用 PAYG**——勿再表述「PAYG 封死」）。user 拍板：純訂閱制（bridge 剝除 `META_API_KEY`）、`--yolo` opt-in、`--trust-workspace` 獨立 flag、**預設 pin muse-spark-1.3＋task effort xhigh（權威值住 model-routing skill 解析表）**、`--model`/`--effort` passthrough 僅臨時 override、**muse 是實作者**（AI＝工單＋reviewer）、不用 Rosetta。0.2.4：review 資產根因＝marketplace 打包慣例攤平頂層 `prompts/`/`schemas/` 非「未打包」→bridge 加攤平 candidate＋錯誤列全部 tried candidates；task-workaround 退役、dual-family 審查回 review 子命令正典。
- **muse 實作品質定案**：執行力強、誠實度高、**對抗性思考弱**＝中階實作者（修 round 淺根因、輸入域盲區、安靜偏離規格、NOTICE 過度宣稱）→**Writer/Reviewer 分離必要**。**advisory 掃描載體（穩定用法）**：read-only 掃描扎實（寫入/蒸餾面留本地 mem-distill）；派工要點＝prompt 自足＋餵方法論 skill 路徑令其先讀＋宣告 read-only 紅線＋報告承載於最終回覆不寫檔。
- **結構通則（muse 對 CR 無知推廣）**：rules-based tool routing 不傳播給被委派的 foreign runtime——**接線必須 prompt 層顯式做**；委派出去的工具面永遠是對方原生三件套。classifyError 教訓：裸 `includes("auth")` 掃整體輸出必誤觸（審 auth 碼時事件流 auth×36）→**終局事實優先**（exit 0＋terminal text＝completed 永不翻案）＋啟發式只認精確片語。
- **instruction 變更驗證四層**：L1 機械（rg/deploy cmp）＋L4 事實基礎（引用事實 live demo）＋L2 行為層（唯一證據＝「該發生的錯誤沒發生」——可證偽預測 watch-list 掛卡）＋L3 dogfood。後議裁定：四律/九律十條拆進對應 rules/skills；**四律3「推算優先」user 裁定不進**（probe 算不準——設計本就要 request/token 雙少）；codex 現況＝ad-hoc 選項（context 小＋消耗快禁大工單）。治理警訊：弧 +3KB 曾達 bundle gate 93%——加 rule 前先瘦身。

相關：[[reference-zcode-cc-subagent-model-thinking]]、[[reference_zcode-platform-facts]]、[[reference_ccr-local-gateway]]、[[reference_cc-agent-view-bg-sessions]]、[[reference_cc-workflow-model-zcode-absence]]、[[reference_lsp-python-mcp-server]]、[[feedback_harness-model-orthogonal-axes]]、[[feedback_quota-failover-policy]]、[[feedback_spec-self-contained-foreign-handoff]]、[[feedback_read-current-file-before-reviewing]]、[[feedback_evidence-over-claims]]、[[feedback_relay-claims-verify-current-state]]、[[feedback-shell-diagram-quality-bar]]、[[feedback_agent-transient-death-autopsy]]、[[feedback_cjk-char-corruption-rg-verify]]、[[feedback_absorb-patterns-not-tools]]、[[feedback_dual-family-review-dispatch]]、[[feedback_work-order-contract-point-to-source]]、[[session-topology-single-writer]]、[[external-runtime-delegation-family]]、[[multi-harness-architecture-direction]]、[[billing-trend-token-design]]、[[gate-severity-solidification-queue]]、[[project_plugin-review-absorption-p1-p7]]、[[project_flash-forensic-0905]]、[[project_archify-illustrate-html-mode-eval]]、[[muse-code-cli-facts]]
