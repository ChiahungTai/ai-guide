---
name: dual-family-review-dispatch
description: user 的 review 派發慣例＝雙家族平行（GLM in-harness＋muse bridge）——muse 補流程面、GLM
  補維度面；muse findings 需慣例判讀
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_07836405-5f73-4d17-9619-5456406f7cd3
---

user 多次指示審查用雙家族平行派發（09-03「也讓 muse 去做 code-review」、09-04「寫完用 muse ep-review」「審查過 muse implement」）：muse bridge review（外部第二意見，working tree diff）＋GLM in-harness agent（F1-F5／3-perspective 維度 profile）同時背景跑，回來 judge-review 合併。**implement 承接面同型（09-04 WO-1 首戰）**：muse 當 writer（十節工單＋bridge `task --background --prompt-file`）＋GLM 當 acceptance reviewer（讀料序 work order→EP→diff→writer report 最後；verdict accept/reject/needs-fix）；muse 沙箱擋 home 寫入（deploy 類）由主 session 補跑。**單跑變體（09-04 user 點名）**：「/code-review 要用另一個 model」＝跨家族**單跑**——muse review 子命令（working-tree scope＋schema verdict）直接承擔，不必湊 dual；dual 是預設形態，user 點名另一家時單跑該家即可。

**Why**：兩家族抓互補盲點——muse 抓流程級（staging 分裂、baseline 過時引用）與框架慣例面（frontmatter 缺失）；GLM 補維度覆蓋（muse review 不支援自訂 prompt，`--prompt-file` 對 review throw，維度 profile 只能 GLM 側承載）。

**How to apply**：涉 muse 的 review 指示＝雙路背景派發。muse findings 逐項對 repo 慣例判讀後才採納——muse 不載入本 repo 慣例，建議會「通用正確、本地錯誤」（09-04 實證：建議移除 backlog 卡 ref 的 localhost URL，但 kanban 開工雙 ref 慣例要求 http URL＋相對路徑並存＝reject 附理由）。GLM 側（ep-review skill）的維度 prompt 要自帶查證義務與輸出格式。**WO-1 acceptance 首戰驗證（09-04）**：GLM reviewer 產出 accept verdict＋獨立複跑記錄（Claim→Evidence——驗收命令全部自己重跑、bundle 逐 byte 相符、三端點 cmp）＋把 writer 自陳「信心最弱處」寫進 reviewer prompt 聚焦點有效（抓到 2🟡 全中）——複跑記錄/writer 聚焦點/讀料序 report 最後三件套續用。

**互換常態模型（09-04 user 明示）**：目前主力＝GLM 5.3＋muse spark 兩家族，**可以的話互相實作/審查互換**（muse 實作→GLM acceptance 主審；GLM 實作→muse second-opinion——即 model-routing family 表既有兩方向），「除非之後有改」。互換是**手動派發**，鏈上無自動家族分化（code-review agents＝full tier inherit 主 session model＝同家族；post-build 的 dual-family 降級句是揭露義務非自動派發）。方法論契約＝arch-thinking 載體中性（[[project_instruction-init-blueprint-scope]] arch-thinking 段）。

**GLM 額度擋時的替補形態（09-05 AIR-28 post-build 實證）**：GLM 1308 usage 窗口（~4h 重置）擋住 in-harness 3-perspective 時，user 直接指示「muse codex /post-build — codex 用sol max」＝**雙外部家族替補**（muse bridge task＋codex companion task 平行背景阻塞形，findings 回來主 session judge）；GLM 側顯式記額度降級不靜默。**「sol max」詞彙對譯**＝`--model gpt-5.6-sol`＋effort `max`→codex enum 頂格 `xhigh`（codex 無 max 檔）；review 工單不帶 `--write`＝read-only 沙箱。雙外部共用同一工單檔（`--prompt-file` 兩家皆支援）。

**task 工單形態＝review 子命令的通用替代（09-04 arch-thinking 弧首跑實證）**：bridge `review` 子命令需 template/schema 資產在場（安裝面攤平佈局解析——cache 舊包在非 muse-plugin-cc workspace 必炸，詳 [[agents-registry-split-design]]（review 資產解析段））；`task` 子命令免資產、**可自訂審查軸 prompt**（紅線 read-only＋必讀方法論 bundle＋findings 沿用 review-engine 嚴重度/信心詞彙）——補掉「review 不支援自訂 prompt」限制，維度 profile 也能 muse 側承載。實證 F1（Important）＋F2（Suggestion）查證品質高：file:line＋rg 對照＋「查過無問題項」明列不硬湊。

**首戰結果（09-05 AIR-28 post-build 雙外部跑完）**：muse `job-mtnw1xgm-13tzyp`（9 findings：0C/3I/6S＋完整 found-nothing 軸報告——引用完整性/禁則殘留/UC 逐行/術語/L4 底稿實讀）＋codex（9：3C/6I 全 confirmed）——兩家**交叉命中**殼的兩個問題（corroborated：false-green 7/7 宣稱＋ghost hash）＋codex 獨抓 3 critical（agent 定義 MCP 綁死 spawn、workflow join 鍵碰撞、殼 false-green）。judge 18 條→✅15＋已執行 3＋⚠️1。**教訓：reviewer findings 逐項機械複核再採納**——muse R3 前提被反證（rg 小寫 `lint` 掃不到大寫標題 `Lint 預檢`＝**大小寫盲區 false positive**），但其可讀性點仍部分採納；codex 全數 confirmed 零誤報（sol/xhigh 高 effort 對應高查證密度）。**殼誠實性是外部 reviewer 的集中獵區**——自己產的報告殼/底稿宣稱會被第一個核（本弧三殼相關 findings 全中）。**findings 對 remedy 也要 judge（09-07 AIR-41 實證）**：GLM 找到真分歧（F1 rank mirror 引號空白家族）但 remedy 公式自身不精確——四趟統一 normalize 會在巢狀案例反向分歧（generator 頂層雙趟/巢狀單趟的不對稱）；正解＝層次模擬定義源。採納 finding ≠ 採納 remedy——修法要對照定義源語義驗證，與 finding 查證同等義務。**「全 closed」驗收宣稱也要跨家族覆核（09-08 實證）**：muse followup 對 R1-R6 驗「6/6 closed」被 codex 二輪三反例推翻（margin 非契約／guard 集合≠事件集合／None 進分組鍵）——muse 驗的是「修復落地＋原案例通過」（happy path），codex 打的是契約邊界反例（窄窗長 drift／歷史事件／缺失證據）；驗收面互補＝落地驗證（muse）×契約邊界（codex），「全 closed」只在邊界反例也過才可信。

**審查範圍＝弧邊界非最新 diff（09-08 user 點名）**：「代碼審查不要漏掉 s1 s2」——build 跨多 commit 時（S1 詞彙清理 commit＋S2 釘選），審查範圍必須釘 EP baseline hash..HEAD 全弧 diff，只看最新 working diff 會漏掉已 commit 的段落；EP 整合策略的 baseline 欄就是審查邊界單一源。同日 pipeline 指令形態「muse flash 審查」＝雙路（muse bridge task＋in-harness flash/lite-verify），judge/post-build 固定主 session。

相關：[[muse-code-cli-facts]]、[[reference_external-runtime-delegation-family]]、[[review-even-on-quick-fix]]
