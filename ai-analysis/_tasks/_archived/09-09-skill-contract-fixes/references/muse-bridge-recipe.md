---
name: project-muse-code-review-adoption
description: muse bridge 群——09-09 直跑範式定案（agent 轉發退役）/沙箱邊界＋校準 n=20 連續全真＋resume 鏈試驗（n=22 進行中：review→judge→修正→同 session resume followup）
metadata:
  node_type: memory
  type: project
  originSessionId: sess_9fc4760c-6ecf-4b20-9f50-ba002e8889c2
merged_from:
  - project-muse-review-calibration
---

muse（Muse Code，`~/.local/bin/muse`）經 bridge（`~/Github/muse-plugin-cc`，spawn-per-task）做跨家族任務面委派。逐弧 findings 校準帳（n=9）見本檔 project-muse-review-calibration 段；model/effort/並發與 external-runtime 路由單一源在 ai-rules model-routing skill（pin/flag 值以該表為準，記憶不硬編）。

## 編制定案
- **第三票／獨立第二意見：合格且值得編入、不值得取代**（多弧一致）。最強實證：審已 commit 抓本家族兩輪 review 都漏的真 bug（v1 收斂誤丟非深負守衛；10 findings 採 4/棄 6）；**MOS-27 post-build dual-context 再證**（user 一詞「muse」指定編制）：muse 抓 M-F1（golden 分支靜默丟 dir＝test-isolation 破口，執行證實）——同 diff 三輪 Claude 審查全未抓；F2 亦 confirmed。Claude 撞 5h 額度→fail-loud 記錄降級＋重置後補齊（額度事件不改編制結論）；**MOS-71（09-07）角色對調再證**：user 指定「primed 用 muse」→muse=primed 側（工單餵 12 條設計承諾清單對照軸）＋ZCode agent=fresh 側；muse 抓最重 P1（`except Exception` 吞 AssertionError 違 crash-only）fresh 邊界軸漏；「承諾清單逐條兌現＋末行 JSON」primed 工單形態輸出結構化可直接 judge（8/12 兌現＋6 findings），可為 primed 工單範本
- 剖面互補：muse 強局部不變量/數值邊界/預防性發現/源碼挖掘深/文檔結構升格；弱系統互動與跨 flag 組合推理（漏全場最重一條）、沙箱限制誤判為受審缺陷（曾在最高 P1）、壓縮型重寫掉資訊、技術對語境盲。GLM 反之——雙向互補
- **verdict 與 P1+ 不可直接信**：逐條 judge 反證（本機重現/rg/實測）才動手；量測數字必獨立重測——muse 會把幻覺數字寫進 code 註解撐決策閘門（「import 0.02s」實 978ms）；自述改檔清單對 git 實查；量測預估會錯（連「預期輸出」一起驗）。對 user 報告 judge 結果禁用內部術語——「反證成立」曾被 user 追問「是啥意思」（09-07），白話＝「我逐條查證過它說的都對/它抓對了」
- 意圖覆蓋把關：muse 漏 user 點名泛化意圖有實證——user 原話對照是主 session 不可讓渡職責

## 不變決策（紅線）
- 絕不設 `META_API_KEY`（訂閱制根基）；額度現實：~8 requests≈5h 窗 10%，xhigh 多檔 review 單次數個百分點——重大 diff 跨家族 review＝軟提醒非硬閘，額度不足顯式記錄降級。**MOS-48 判讀再證**：bridge 回 `429 Subscription quota exhausted ... resets at 00:00Z`（每日窗口）——撞頂任務零產出，當日湊不齊 quorum；量測前先確認餘量。**雙家族同乾降階梯（MOS-54/55）**：GLM 1308→muse 承接（429 次窗 reset）→lite-verify 機械補位（自標非對抗）＋Finding Record 記降級＋PENDING 補審——reset 後 user「你可以 fresh eye」即補 spawn；auth-fail（查 setup）與 quota-exhausted（純等窗）死因不同
- review 必帶 `--network restricted`；`--yolo` 僅 caller 明示＋隔離環境；實作可不帶 restricted
- **exit 0 ≠ review 正確**——verdict 永遠從輸出末行 JSON 解析
- 未帶 `--trust-workspace` 時 muse 忽略 repo AGENTS.md——fresh-eyes 校準刻意不帶；要守慣例就寫進工單

## Bridge 操作配方（09-09 直跑範式定案——agent 轉發形態退役）

- **🔑 直跑是預設（09-09 user 質疑「一定要浪費一個 agent 轉發嗎」→ 歸因：反模式）**：bridge task 就是一條長命令（10-40 分），**主 session `run_in_background` 直接跑**（背景 Bash 無 timeout 上限——856s features build/442s integration 皆此形態）＋stdout 重導檔案→完成通知→Read。舊「spawn agent 轉發」形態源於誤判約束（以為 Bash 只能 600s——`run_in_background` 從頭就可用，**約束從未真正存在**）＋解法固化（memory 活配方記了 agent 形態操作知識＋delegate-rescue 工具存在使慣例顯得官方）。轉發層製造的「兩段式收法」間接層（agent exec id ≠ bridge job id）整條消失
- bridge 命令形態：`node <bridge.mjs 絕對路徑> task --network restricted --steps 400 --prompt-file <工單>`（cwd＝target repo 根）；review read-only，實作可 write。**`--session-id <id>` 支援 resume**（bridge.mjs:767 flag 存在）——review→judge→修正→同 session resume followup 鏈用（session id 從 `runs --json`/`show --json` 的 sessionId 欄位取）
- bridge 步驟 `setup`（target repo 根執行；**非 muse CLI 子命令**——user 09-07 實測 muse 僅 init/auth/sandbox；此為 muse-bridge.mjs 的互動式前置）。script 位置：plugin cache `~/.zcode/cli/plugins/cache/muse-market/muse/<ver>/scripts/muse-bridge.mjs` 或 source `~/Github/muse-plugin-cc/`
- setup gate（SM-13 防 PAYG key 蓋訂閱）互動式計費 gate，AI 不代跑、報 user 手動；憑證 `repo/.muse-bridge/setup.json`（gitignore；per-worktree 驗 workspaceRoot）。**形態定位**：TUI＝user 常態（在場對話裁決、零前置）；bridge＝AI session 對 AI 派工的管道（主 session 直跑即可，無需 agent 中介）
- **muse 判讀停損（user 09-07 晚）**：「muse 不判斷了——效果不好且額度想用在代碼審查」；額度優先序＝代碼審查/實作 > 判讀
- ledger 判活：jsonl 只在 job 完成落盤（「沒 jsonl」≠異常）；判活四件套＝ledger status＋ps＋白名單 mtime＋子進程 CPU；僵屍簽名＝running 但 steps 凍 15+ 分＋jobs 空＋ps 無進程
- steps 耗盡→ledger `interrupted` 無 JSON，但死前檔多已寫完——主 session 直接機械驗收 working tree（ruff/mypy/pytest 重跑＋spot-check），不必重派
- TUI session：`muse export --session <uuid>` 匯事件；journal durable → `muse resume` 接續；TUI/direct 不進 ledger，歸因靠 mtime＋UUIDv7（reference-forensics-methods）

## 沙箱與環境限制（陷阱）
- workspace 外一律 Operation not permitted：`~/.claude/**` 池寫、`~/.mosaic` 讀、`~/.cache/uv` 寫全拒
- `uv run` 被拒 → 工單一律 `uv run --no-sync`（既有 .venv，免 cache 免網路）
- 涉 repo 外寫入（memory 池等）：prompt 預埋「環境限制回報＋禁妥協 /tmp」協議，回報後主 session 接手；它備 /tmp 的檔主 session 對帳後 cp——自述「需 user 手動」時有池寫權限即代搬
- 外部資產先複製進 repo `.agent-tmp/`（gitignored）；prompt 明示逃生口：「無法讀取直接輸出 `ENV_LIMIT: <原因>` 結束，不用想像代替」——muse 能看圖（多模 confirmed）
- muse 自建 workaround（如 redis mock conftest）不進 repo——備份刪除、主環境重跑綠確認；crash-only＋Protocol 衝突預埋工單省一輪

## Resume 鏈全弧閉環＋ai-rules 反饋固化（09-09 MOS-74 終弧）

- **resume 鏈試驗成功**（muse review flash 6 findings→GLM judge 6/6 採納→修正→**muse `--session-id` resume 同 session followup：pass 6/6 verified**＋2 新 issue）；review session id 從 bridge footer `[muse-bridge] job … session=<uuid>` 取。**「findings 每條附可機械複驗的驗證式」是工單範本關鍵要素**（followup 零背景重複、驗證式直接回收）——分工比例實測對：muse review/judge=GLM/followup=muse resume；flash 兩趟比 xhigh 一趟便宜
- **ai-rules 反饋固化已 handoff（09-09 `/handoff ai rules`——user 問「整體審查新做法 ai rules 有啥建議」產出）**：反饋佇列＝`mosaic_alpha/.agent-tmp/ai-rules-feedback-queue.md` 四條：①model-routing bridge 段改寫（直跑範式＋resume 鏈形態＋驗證式工單要素——本檔「Bridge 操作配方」段可作 patch 參考文本）②tool-discipline 通則「長命令背景跑是預設；spawn agent 不是繞 timeout 的手段」＋三層反模式案例（誤判約束→解法固化→工具存在強化慣例）③code-review/review-engine Finding 格式加「驗證式」欄 ④tour_validate 零匹配 bug（**caveat：當時命令用相對路徑 `--repo .`——與 code-reality 檔已記的相對路徑陷阱同形，ai-rules session 處理前應先以絕對路徑重現排除**，詳 [[project-code-reality-tools-evaluation]]）。分層已裁：操作事實留 memory、機制性知識進 ai-rules
- 跨專案固化原則（user 認可形態）：handoff 交 ai-rules session 固化（ai-rules 邊界——mosaic session 不直改）

## 審查工單 prompt 要點
- 末行 JSON verdict 契約＋read-only 紅線＋`--network restricted`＋400 steps
- 防洗衣：「不要被既有 Findings 表結論引導」；fresh-eyes 鏈不告知已審過一輪（防 anchoring）
- repo 慣例注入（讀不到 AGENTS.md）：assert-as-crash-only／uv run／Panel 版本／宿主限制直接寫進工單
- 範圍限縮：白名單逐列＋「working tree 有他 session 變更，ignore listed 以外」＋in-flight 清單
- 已定案決策開頭羅列（勿重辯勿擴張）；預期殘留例外明示；「已知待辦勿重報」清單防噪音
- **primed 側工單形態（09-07 MOS-71，user 指定「primed 用 muse」）**：主軸＝設計承諾編號清單（12 條逐條可驗），要求每條「兌現/部分/未兌現」判定＋JSON verdict 帶 `commitments_met: n_of_12`——MOS-41「餵什麼查什麼」應用形態（承諾側進工單、實作側在 diff）。dual-context 兩側可拆家族：fresh=ZCode code-reviewer agent、primed=muse bridge，同批背景平行。
- CR 接線：MCP 不過橋（三家同款），CLI 形態可通——把 `code-reality scip_refs`／`impact_radius` 用法寫進 prompt 並要求附輸出（graph build-time 產物，注意 stale）
- findings 要 file:line；EP 行號疑點各自 rg 驗

## 分工定式（user 逐輪指名的序列）
- EP 規劃/全域研究/post-build 審＝GLM 5.3 主 session；EP 審查與 code 實作＝muse（單工單垂直切片 400-600 steps）；視覺＝flash；跨家族 EP 審＝codex+muse 平行同題三方對照（共識採納、單家獨有逐條查證、與已修重複過濾）
- review→implement 兩段 muse 之間：主 session judge 反證＋EP 回寫不可省
- 實作工單切界：muse 只跑機械驗證（pytest/ruff/mypy 帶 --no-sync）；test-par/baseline/視覺/收尾/commit 留主 session；禁 git commit、禁寫 backlog/ 與 ai-analysis/
- 派發後 EP 有實質編輯 → 驗收含「新增條款逐條 rg」；工單不可假設 EP 凍結
- 同型補丁 rg 全 repo 同 pattern——muse 只補眼前炸的那個
- 實作配方五要素：真相源前置／已定案開頭羅列／pre-flight 錨點補差／預期殘留明示／凍結契約驗證法寫死

## MOS-41 judge 工單實戰（2026-09-05，user 指定 muse judge）
- **派發形態**：muse-rescue 也被 ZCode spawn 閘門拒（concurrency）→ 主 session Bash 背景直呼 `node <bridge> task ... -- "$(cat 工單檔)"`（shell 額度與 agent 額度分離）；兩段式收法照舊。
- **工單邊界＝能力邊界**：verdict pass 10/10＋NF 全真（範圍內零誤判），但漏三項實質（P1 docstring↔斷言矛盾、P2 EP 承諾未兌現、P3 不可達分支）——根因在派工端：裁決表沒給 **EP 全文承諾清單**＋docstring 一致性非工單軸。**餵什麼查什麼**——跨文件交叉查證須兩側都進工單。
- **verdict JSON 契約有效**：末行解析乾淨；judge 類工單比 review 更省 steps。

## 其他任務面（簡）
- 討論 handoff：user 貼 self-contained handoff 進 muse TUI 平行腦——可 /consistency、修 findings、（指示下）/commit、改寫 EP、backlog 治理
- 根因調查：GLM+muse 雙背景平行獨立查，主 session 蒸餾對照；prompt 注入背景標「勿重查」＋file:line＋「查不到明說，禁推測」＋read-only
- 文檔平行變體：正版落地後 muse 寫變體隔離 `muse-variant/` 防同化，內嵌 user 裁決當 ground truth；**採納＝增量拼裝非整段替換**
- K 線判讀對照：batch-in-one 穩定；muse 保守精瘦 anchor 銳利，vision 續任主力（project-annotate-workbench-arc）
- 治理/清單查證類唯讀工單適配良好——清單機械生成、set 差集對帳消費

## 09-07 cluster-merge handoff 執行（n=10；TUI 形態）

- **單份 self-contained handoff 承載 14-cluster 記憶池合併＋五步收尾零回問**，含兩個突發（並行 writer 漂移）處置正確——handoff 規格要素（caps/desc 規則/對照表/收尾步序/凍結清單/fail-loud 指示）即 load-bearing 最小集。
- 超規格判斷：自加「rm 前 mtime 全員稽核」——一漂移回收（mechanical 新行重吸收）、一 HOLD（mos48：凍結 keeper 禁改下選 HOLD＋三選項交 user，不盲刪不盲併）。
- 誠實度複驗過：4 項偏差主動揭露＋DB 直讀反查委託 session 宣稱（結論一致）。
- 數字漂移復發：14 keeper chars 自述 13/14 精確、1 例 +504（git-commit-feedback 7,150 vs 7,654，mtime＝其自身寫入）——「量測數字必獨立重測」維持。

## 09-07 MOS-65/67 整弧能力實證（n=11/n=12；TUI 形態）

- **n=11 MOS-65 整弧（handoff→EP→實作→commit）**：user 指定「EP 跟實作分開評價，看之後怎樣利用」。EP=A-（依賴考古發現 writer 僅 append 無刪除能力、R1 Panel 鍵盤橋風險 rg 零命中識別、Codex checkpoint 6 項推翻自我吸收——原刪尾筆 undo 被考古推翻：human_overlay.json 是 dict 覆寫非 append-only、誠實「無跨檔交易」不假裝有事務）；實作=A 且**兩處超越 EP**（receipt new_entry 用寫後磁碟實值、undo 雙層對帳）＋寫入契約零稀釋（append_overlay 零改、`replace_overlay_entry` 唯一刪改入口＋crash-only 比對）——**危險域（golden_writer）派 muse 零事故的前提＝handoff 紅線寫到「唯一入口/crash-only/契約不動」密度**。muse commit 不報數字，主 session 重跑全綠（unit 732＋kbd 契約 3 真瀏覽器）。
- **n=12 MOS-67 blueprint in-flight（架構翻轉級）**：user 本體論裁決（單 mutex 樹→五獨立 membership 樹無主次）下產出 952 行七檔 blueprint（主＋六子 EP）。規劃力證據：①補償 pair 識別（near-tie/co-label/secondary＝mutex 樹補償件，原子退役防 double-count）②D10 量綱分析（各樹 gap 貨幣自家 p90 不可比→flag-not-rank）③existence_gap 禁復用 nearest_alt_gap（互斥語義不可移植——審查者最大疑點它自識別）④語料實況誠示 true_labels 零筆。**新弱點＝跨 WT 意識零**：workspace＝user 開 TUI 處（warrant），卡在 v2，EP 未登記錯位。EP 自寫未審（deferred 登記）——judge 留主 session 不變。
- **能力結論（升級）**：垂直切片執行（65）→架構翻轉級規劃（67，user 對話式裁決下：它提三候選→user 質疑→它收斂）。利用：可派架構級 EP；handoff 必綁 workspace/卡歸屬；大 EP 完工後主 session 補獨立審。
- **TUI trajectory 鑑識法**：TUI session 不進 bridge ledger（jobs/ 無新 job≠沒在跑）；`muse export --session <uuid>` → repo root trajectory-*.json（29MB 級）。結構＝events[].envelope.payload_type 分流：`runtime.user_intent.accepted`=user 指令全文、`assistant_tool_calls_committed`=工具 args（檔案路徑從 args regex 撈）、`session.workspace_branch.observed`=**workspace 真身**（定位「repo 無痕跡」的 muse 在哪個 WT 幹活的鑰匙）；pytest 自跑證據從 raw JSON rg "N passed"。

## 09-07 MOS-69 EP review（n=13；bridge 形態）

- **重組型 EP 審查＝跨家族補規劃者盲點的另一實證**：8 findings 全真、judge 全採納。三層價值：①分類表 2 個錯桶（行為語義 vs 實體段落位置——規劃者塊狀分類的系統性滑差）②**gate 可達性**（ruff format baseline 本來就紅→不先正規化則收口 gate 永不可達；mypy `tests.* ignore_errors` 對 tests 恆綠＝真空門）③計畫內部一致性（class 搬移形態未定義 vs「逐字搬移」條款矛盾）。②③是 EP 自身邏輯——本家族規劃者自查難抓、muse 乾淨抓到。
- 機械核對全過（名集合雙向 diff、27 helpers 逐一對帳、AST 零模組級狀態）——工單給「機械核對清單＋抽查自選 N 案」框架产出扎实；venv 實跑 230 passed 自帶執行證據。
- spawn 形態：經 muse-rescue agent 轉發 bridge，findings 全文隨 agent result 回——此形態免兩段式收法。

## project-muse-review-calibration

（project）muse 校準（n=9 九弧）——剖面互補/沙箱歸因弱項/數字造假獨立重測推翻/蘊含誤讀型誤判；跨家族價值最強實證。首測 2026-09-02 tagging-s2 uncommitted diff（GLM 三 agent＋作者知識為對照）。

- **n=1 tagging-s2**：verdict JSON 一次可析零幻覺；4 findings 採納 2——market guard 缺口（muse 評 P1 比 GLM 💡準）＋gap20_max inf 邊界（GLM 全漏）。漏最重的 subset 組合炸彈（GLM 抓到）——**剖面互補**（muse 強局部數值邊界/對稱 guard、弱跨 flag 組合）。結論：編入 dual-context 第三側不取代；3-5 弧再定編制。
- **n=2 backlog-integration（文檔/基建 diff）**：verdict needs-attention 無 P0；5 findings＝4 採納＋**1 P1 推翻**——誤判形態＝**沙箱環境歸因**（restricted 擋它 git fetch → 誤推環境缺陷建議改 config；judge 反證 task list stderr 0 行＋fetch exit 0）。與 n=1 相反：**環境自覺是弱項**。正面：源碼挖掘到機制層（panel handler 證無 listing，深於 GLM 實測）、抽 5 卡 git show 對照、wrapper guard 預防性發現、`.locks` 交叉印證。read-only 邊緣：實測建 MOS-12 測試卡（收尾乾淨但 prompt 說 do not modify）。**紀律：verdict 與 P1+ 不可直接信，逐條 judge 反證；家族偏誤形態互異正是價值**。
- **n=3 磁碟暴增根因調查（read-only）**：**機械歸因全對**（觸發者 daily-workflow log 鐵證、specs 演化 commit、venv python 復現 key 精確匹配、hardlink 否證）——但**架構定性錯**（把「每天全量自癒重算」定性為按設計運作，被 user 直球糾正：設計＝年度增量尾補）。**邊界：歸因正確 ≠ 定性正確**——agent 傾向把實況正當化為設計意圖；定性以 user 設計記憶裁決。**提取手法**：output.txt 只有外殼，報告主體在 `.muse-bridge/jobs/<jobid>.jsonl` 的 payload.text。
- **n=8 測試污染架構討論（advisory）**：意見品質高——抓到主 session 全鏈漏的兩事實：①受害者自己也是 writer（load 寫死 cached——二分法不精確）②gap 防護當前已是 WARN+None 非 crash（移動靶，直接改 fix 形狀）；方案有立場（A3 最小正確、餘逐一反對＋ordering trap）。另指 canary 應斷言路徑不只 pass。
- **Bridge bug（回報 muse-plugin-cc）**：job `status=auth-failed`＋exit 0＋完整 verdict 並存——分類啟發式誤標（n=2 重現）。
- **CR 接線結論（兩弧一致）**：兩次零 CR 呼叫（輸出 0 hits）——MCP 不過橋（三家通病）；CR CLI 在場可用，差在知不知道該用（無 trust-workspace 連 AGENTS.md 都忽略）。正解＝CR CLI 用法寫進 prompt 模板，不靠自動發現；結果同樣過 judge（stale 誤判風險）。軌跡：`muse export --session <id>` → events payload，tool 名在 committed.tool_calls。

## 09-07 MOS-67 S4 雙家族審查（n=15；bridge task 轉發形態）

- **dual-family 編制新形態**：muse=primed 側（3-perspective 工單：clean/UC-anchored/Correctness——第三軸查 three-way 融合縫隙）＋本地 GLM code-reviewer=fresh 側——跨家族性由「muse vs 本地」達成（比兩個 GLM subagent 更獨立）；muse 9 findings＋GLM 10 findings 互補（muse 抓欄位語義錯位 F-U1、GLM 抓 activate 後 cache 缺 P1/P2——兩側無重疊＝剖面互補再證）。
- **muse-rescue agent 合約禁 `review` 子命令**——只能經 `task --prompt-file <工單>` 轉發，read-only 語義由工單紅線承載（muse 回報 complied）；findings 全文隨 agent result 回（免兩段式收法，同 n=13 形態）。
- **bridge 環境警告如實轉達**：workspace untrusted（`--trust-workspace` 未經授權不得加）→專案 AGENTS.md 被跳過（慣例須寫進工單——既有紅線的實證）；`~/.config/muse/AGENTS.md` 80KB 超 32KB 上限被截斷。
- **F-U1 型價值＝語義錯位深挖**：欄名 `comparable_new` 語義實為「一致旗」（stash 命名錯位）＋分子沿用舊旗＝混合口徑 metric——muse 從「S5 消費者會讀錯趨勢」角度抓到；judge 修真時測試紅燈才暴露斷言還鎖著混合值（0.6）——**修正帶出的紅燈是命名錯位的第二層證據**。meta 鍵名不變（消費端零波及）是修真時的關鍵約束。

## 09-09 MOS-74 resume 鏈試驗（n=22；user 設計新流程——**全弧成功閉環**）

- **鏈形態驗證通**：muse review（bridge flash，needs-attention 6 findings：3 P2＋3 P3——含抓到主 session 自己批量修正的 callstack 錨 off-by-one＝作者盲點型）→ 主 session GLM judge（6/6 採納，F-4 部分：data 側 underscore 別名修、features 接線名按 EP 豁免）→ 修正（muse 給的驗證式逐條複驗綠）→ **muse `--session-id` resume 同 session followup：pass 6/6 verified**＋2 條新 issue（N-1 另 4 檔既有 stale 錨範圍外順手修／N-2 poc churn info）。resume 優點實證：followup 工單零背景重複（reviewer 記得自己 findings）、驗證式直接回收複用、reviewer 對自己 findings 的修正驗證比 fresh context 準。
- **「findings 須可機械複驗」＝本試驗最該固化單點**：review 工單預告每條附 rg/pytest 驗證式 → 修正後複驗是跑命令非重新理解 → followup 零摩擦。分工比例正確：muse 出 findings、GLM judge 零裁決成本（findings 品質高到只查證）、followup 回 muse 家族自驗；review＋followup 兩次 flash 比單輪 xhigh 便宜。
- bridge `--session-id` flag 原生支援（muse-bridge.mjs:767；sessionId 從 runs/show JSON footer 取）；resume 棒即主 session 直跑形態。
- **ai-rules 反饋佇列已落檔**（`.agent-tmp/ai-rules-feedback-queue.md`，mosaic repo，待 ai-rules session 固化）四條：①model-routing bridge 段改直跑範式＋resume 鏈形態記載＋工單範本要素（驗證式要求）②tool-discipline 補「長命令（>10 分）背景跑是預設——spawn agent 不是繞 timeout 的手段」通則＋三層反模式案例（誤判約束→解法固化→工具強化慣例）③code-review/review-engine 的 Finding 格式加「驗證式」欄（external reviewer 契約）④code-reality tour_validate 中文目錄掃描 bug 重申。

相關：project-backlog-md-integration-arc、reference-zcode-platform。

## 09-08 MOS-67 S6 post-build（n=17；warrant bridge 直派 fresh-eyes 全鏈）

- **warrant setup.json 在場（09-07 19:32 建）→ muse-rescue 經 bridge `task --prompt-file` 直派成功**（xhigh／400 steps 用滿／`--network restricted`／末行 JSON verdict 乾淨可析）——上文「warrant 無 setup」段正式作廢（09-08 行內已標）；bridge 直派＝warrant 常態可用，不再需要 TUI 繞道。
- **fresh-eyes 3 findings 全真全採**：F1 multi-present agree 口徑無 pinning test（P2——與 primed F-R3 的 D-12 偏離記錄互補，接住測試面）；F2 label_sets docstring 殘留 **≡ primed F-R1 雙側獨立同擊**（合併 7 findings 唯一重疊、去重後零衝突＝「全採納」判斷的信心基礎）；F3 conftest `_feat` provenance stale。**執行證據自帶**：自跑 409 tests（research+scripts 179＋annotate 230）＋ruff 全 pass＋3 參數檔過 repo 自身 validator。
- **工單防噪音段生效實證**：「已知待辦勿重報」列了 doc drift／0.03 過渡值／TAIFEX——三項全沒被重報；「已定案決策開頭羅列」七條（v8 凍結/canonical/D10 等）零重辯。編制 user 指定「一個 muse 搭配 5.3，fresh＋primed」＝muse 退回 fresh 側（剖面互補最強位）、5.3 primed（意圖判斷密集側）——與 n=15 反向，兩種編排都成立。

## 09-08 MOS-22.3 素材文檔審查（n=18；bridge 經 muse-rescue 直派）

- **文檔/規劃素材審查面新證**：七軸工單（證據錨逐條核對／五樹數字獨立重測禁照抄／藍圖引文核對／卡現文對照／內部一致性／registry 機制驗證／遺漏面）——muse 執行力強（13 錨全查、數字全重算、藍圖原文核實），7 findings **6 採納 1 推翻**。採納 6 條全是作者盲點型：root 計數錯（三顆→兩顆）、「節點」口徑未定義（內部分裂節點 vs sklearn 總節點 2n+1）、`combine:"OR"` 既有例外漏查（動量轉向 tag）、文檔同步範圍漏項（architecture §5.1 drift）、行號錯位×2、EP 骨架縫隙（回流③無歸宿/deferred 缺註記/異質源壓縮成單表擴欄）。
- **🔴 推翻的是它評的唯一 P1——新誤報機制**：宣稱五樹數據「負乖離手寫規則 `days_below_25>6` 符號寫反、應為 ≤6」；實為 **muse 誤讀 `per_label_trees.json` `leaf_names` 的鍵命名空間**（鍵=`樹名:節點id`，前綴是樹名非葉標籤）→把 n2（負葉 非負乖離）當正葉、極性整個反轉。judge 開 JSON 對質：正葉 n3 確實 `>6`、`leaf_names` 本串亦同。**P1 幻覺＋六條小真＝「verdict/P1 不可直接信、逐條 judge」紅線再證**——文檔審查面它的數字/行號/一致性抓漏價值高，但最高嚴重度項需要主 session 開原始檔對質。
- 工單形態補充：read-only 紅線＋`--network restricted`＋400 steps＋末行 JSON verdict（含 anchors_checked/tree_numbers_reverified/axes_executed 結構化欄位，可直接機械判讀）；「working tree 他 session 變更 ignore listed 以外」明示；findings 全文隨 muse-rescue agent result 回（免兩段式）。

## 09-08 MOS-73 S1 diff 審查（n=19；bridge 直派 fresh-eyes）

- **首次 6/6 全真全採**（2 P2＋4 P3；verdict needs-attention）——code diff 面且全附執行證據（自跑 venues 325 tests；PYTHONHASHSEED=0/1/2 三態實測 set 編碼不穩）。最重兩條都是作者「**同型檢查只蓋一層**」盲點：F-1 作者只擋**同層**錨×DAILY 格歧義、**跨層**（override 格×繼承錨）靜默遮蔽漏——with_overrides 補 raise；F-2 最微妙邏輯（store.execute 身分閘——delegation 等值性所繫）零 e2e 測試，補 test_policy_binding.py 三分支。F-4 顯式 NaN buffer（`<= -nan` 恆 False→靜默全 0）＝crash-only 缺口；F-6 PRODUCT_OVERRIDES 裸碼跨 class 誤套（0050 on FUTURES 實測）→ScopedProductOverride fail-loud。
- 工單防噪音段有效再證（已定案五條＋已知勿重報三條零重辯零重報）；verdict 附 `scenario_rows_covered` 百分比＝對 EP 場景矩陣缺口盤點直接可用的新形態欄位。
- **剖面結論細化（n=18 P1 幻覺 vs n=19 全真）**：數字/行號/一致性/「作者檢查只蓋一層」型缺口＝強項；跨欄位極性語義（leaf_names 鍵命名空間）＝弱項。

## 09-08 MOS-73 S2 diff 審查（n=20；bridge 直派 fresh-eyes）

- **needs-attention 7 findings（2 P1＋5 P3）全真全採**——S2 核心判定正確＋EP 場景四行覆蓋確認。兩條 P1 都是**作者機械遷移的系統性遺漏**型（符號/介面全遷了、但下游「字串匹配分支」與「fixture 形態測試」兩種不 import 符號的消費面漏網）：F-1＝`cmd_assemble` boundary 過濾器仍匹配退役詞彙（tag 字串比對分支）——新 kind 制 tag 靜默掉出 boundary-keys.json（靜默訊號遺失，非 crash 不可見）；F-2＝`test_golden_pretriage.py` 整檔在符號反查網外 3 紅（fixture 形態測試不 import 被改符號）。**遷移/退役弧的 muse 價值＝獨立掃「非符號消費面」（字串匹配/資料形狀斷言）**——主 session 的 rg 符號反查結構性漏此面（教訓入 verification-feedback 反查雙網）。
- P3 五條全採（__all__/深拷貝對稱/真實路徑 pinning/負側邊界＋同 raw 雙 scale/normalization bool 繞過）——「作者知道但沒釘」型缺口的補釘建議質量高。修正後 884 passed 綠。

## 09-08 MOS-75/76 diff 審查（n=21；bridge 直派 fresh-eyes）

- **needs-attention 2 findings（1 P2＋1 P3）全真全採**——微型混合 diff（code 衛生 3 檔＋文檔 re-anchor 7 檔）照抓真缺口：F-1 P2＝uc-matrix:27 col2 re-anchor 了但**同行 col3** 承接者欄殘留舊 baseline（「daily_update → FactorCache 年度段 append＋LabelStore 完成窗」與 off() 事實矛盾）——「同型檢查只蓋一層」第三實例且新形態＝**表格行級**（修一欄必掃同行全部欄）；F-2 P3＝EP 執行記錄速記「全樹僅×2」實 11 檔四類豁免（正式 gate 範圍無恙、僅速記失真——驗證者照抄會誤判 gate 跳紅）。
- 正面：rename 非符號消費面分面掃描（yaml/json/toml/ini/tests/getattr 字串形態）獨立驗證零命中；三處新註解語義 vs 呼叫者逐處核實全符（連 service.py:1578 write-gate 註解原文都對上）；錨點 commit 實錘（驗 `0f377da16` 是 HEAD ancestor）——文檔面查證紀律穩定。
- 作者側預防：改表格/多欄宣稱的任一欄後，同行其餘欄逐欄掃同族舊語——/consistency 抓跨檔、muse 抓同行，兩層都過才乾淨。
