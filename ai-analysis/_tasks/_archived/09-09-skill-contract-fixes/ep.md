# EP：開發流程 skill 契約修復＋反饋固化（codex 六斷點＋mosaic MOS-74 四條）

> **ep_type**: implementation
> **mode**: docs mode（product 全為 `.md`——skills/rules/_common 契約檔；無 executable source 變更）

**baseline: ba386cbc174226dedbeb1f75be63ba3f54702c3e**（定稿時更新——EP 建立時原記 ac6cccf；其間 air-46 弧 ff 併入 main（0cd90a5 建卡＋ba386cb 卡 branch 慣例），非本弧 product，baseline 移至開工前 trunk HEAD）

## 進度節（即時落盤區）

- 〔09-09〕EP 草稿成立。**狀態：草稿——未定稿**。定稿 gate＝段落 0 三個背景 agents 回報吸收完成＋EP Review Cycle 跑畢。
- 〔09-09〕三背景 agents 進行中（`.agent-tmp/dryrun/`）：agent1 transcript 考古（Claude/codex 池）、agent2 修法 dry-run 補遺、agent3 ZCode 專攻（user 指定——最近主力開發在 ZCode，證據權重最高）。
- 〔09-09〕codex 審查 checkpoint（`~/.codex/worktrees/5da1/ai-rules/.agent-tmp/skills-architecture-review/`）與 mosaic 反饋佇列（`/Users/ctai/Github/mosaic_alpha/.agent-tmp/ai-rules-feedback-queue.md`）皆屬 7 天清掃暫存——**段落 0 必須先搬 durable**（見 S0）。
- 〔09-09〕ZCode 側查證完成（本 session）：codex 六 headline＋次級 finding 引用全數核實屬實；三加強點——PB3 實為四方 drift（全域 guide 也是 5a 派）、JR1 前提錯誤（.review 同 worktree 跨 session 保留，post-build Resume 場景正依賴它）、IM2 另有 metadata-sync 檔內自矛盾（:21 vs :87）。
- 〔09-09 agent3（ZCode 專攻）回報——完成，`.agent-tmp/dryrun/agent3-zcode-transcript-archaeology.md`〕**資料源修正**：`~/.zcode/v2/sessions/` 僅 7 月初舊導入；真 ZCode session 庫＝`~/.zcode/cli/db/db.sqlite`（session/message/part 表；ai-rules 483 sessions）。**斷點實證裁定**：JR1 ✅——09-03「每晚 memory 收斂」全鏈實錄：judge 決策實際寫 `.review/main.md`（:56「寫 EP」從未被遵守）→ **S1 帳本修法＝正典化現狀（.review），非行為變更**；PB3 ✅——多數弧結案在 post-build/commit 後（S2 方向＝正典化多數派；AIR-44 反例、AIR-31/47 S5 未跑 post-build 即結案）；PB1 ✅——.md-only「三連形態」大宗（triage→ruff/rg→commit，無 code-review/judge）；EP1 ✅（790e217 單行 fix 無 EP；小修弧多＝暴露面大）；IM3 ✅（AIR-49 impl-lite 直寫主 WT，isolated 前提在 ZCode 不成立）。**證據修正兩條**：①CR1 降級——「大 WIP 漏已 commit 前段」未實證（實際形態＝uncommitted 全量或卡 baseline→HEAD），S1 弧模式改法保留、優先序降；②IM1 事實修正——ai-rules 無 architecture.md（情境 A 綁定在本 repo 是空集合），S3 的 IM1 修法主要服務消費端 repo（ai-rules 側痛點在 5b instruction 檔同步非 architecture.md）。
- 〔09-09 agent3 破壞面→修法硬約束〕**S2**：結案 gate 必須是 skill 流程步驟（post-build 階段 5／implement 階段 6），**禁掛 SessionEnd hook**（ZCode live hooks 僅 PreToolUse/Stop——SessionEnd 靜默 no-op）；ZCode 端 post-build 覆蓋率非 100% → implement 6 fallback 升為並列主路徑（措辭權重調整，原設計假設已預見）。**S3**：ai-rules 產出主體即文檔＝幾乎每弧落入控制面分流——**必須帶小修快道**（低風險 .md 走輕量檢查），防夜間/cron 弧 throughput 崩；docs-mode 行為審查在 ZCode 從未實裝＝新建非修補（收尾驗收要求首弧 dogfood）。**S4**：一弧多審常態（implement 審＋post-build 審＋外部二意見）無去重＝去重修法有實證需求；多卡 session（AIR-37 型一 session 六卡）以卡 baseline 定弧邊界避免重複審。
- 〔09-09〕**air-50 branch ref 已建於卡 commit `0cd90a5`**（純 pointer 不 checkout——平行 air-46 session 不受影響；user 裁定：流程架構級弧走自己的線）；開工時 checkout air-50（依 AIR-46 線上浮出的分線慣例）。
- 〔09-09 agent2（修法 dry-run 補遺）回報——完成，`.agent-tmp/dryrun/agent2-fix-dryrun-omissions.md`〕**EP 機械錯已修**：guide 路徑三處 `rules/` 前綴移除（檔在 repo root）。**分級**——可直接進 EP：S1a（補 execution-plan:353〔EP Review Cycle 的 judge 呼叫〕第三 caller＋多 WT 帳本可見性語義〔.review per-WT、EP 區段跨 WT〕＋rg 驗證範圍從目標檔擴全鏈）、S1e（judge-review:138 流程位置連動）、S1f（**補 implement 消費端接線——Context 欄無消費者＝死欄**＋檢查清單＋blueprint 繼承＋無 spec 時欄位來源）、S4a（code-review:32 弧動機文字＋implement:77「build 首個 code commit」語義殘留）、S4c（自動鏈判定傳遞機制）、S4d（過期標記載體＋DEPTH 接線）。**先決策**：S1b identity 形態（header 級非 per-row＋**必含 uncommitted digest**——只有 rev 會讓 PB2 核心場景〔HEAD 未變、WIP 變〕誤判吻合跳審）；S1c 範圍聲明（EP session 中無關並行 uncommitted 混入弧範圍——需「非本弧項」標註出口）；S1d（多 snapshot 選擇規則＋hook 2 持久 delta tour／debrief 的 before 端消費鍵連動）；S2a（**雙發布防護**：implement 階段 6 fallback 是「預測本弧不跑 post-build」且在 review 前發布 Done——需已結案偵測＋觸發條件收緊，否則 PB3 換位復活）；S2b/c（殘留清單 durable 落點——`.review` 會被 commit 清除；flow-feedback 歸檔 judgment gate 勿因 IM2 免確認全面拆防線）；S3b（refactor 規模判準來源——guide 規模表無對應列）；S4b（**條件精確化：同 profile 等價性＋記錄缺席→全審 fallback**——S1 允許 implement 階段 4 findings 走 context 不落盤，跨 session 比對鍵必然缺席，S1×S4 須明文接線，否則砍掉的是 acceptance-evidence 層 2 在自動鏈內的唯一體現）。**該改設計兩條**：**S3a 路徑枚舉 self-defeating**——本 EP S2 改的 repo-root `ai-development-guide.md` 不在 skills/rules/agents/commands 清單（修法自己的檔案逃過修法自己建的 gate）；消費端控制面（模組 AGENTS.md／SYSTEM-MAP.md／hooks）全不在清單（mosaic 2f874ca6 實證 PB1 不修）→ 改**語義判準**（「塑造 LLM 行為的 instruction／規範檔」）＋路徑降 hint＋純 typo 輕量出口（與 agent3 小修快道需求合流為一條快道）；**S3c 掛錯位置**——simple 多數入口＝裸任務直接實作（不載 execution-plan，掃描掛 EP 護不到多數入口）→ silent-corruption 例外**同步進 guide always-on 面**（小型變更條款），guide 入 S3 檔案清單。**S2 掃描補洞**：commit:174 用「5a 結算」措辭（rg `結案兩步` 掃不到——掃描組加 `5a 結算`／`--final-summary`）＋commit skill 與 execution-plan 收尾模板入 S2 檔案清單。**八場景驗證結論**（standalone 弧／docs-mode post-build／muse bridge／quota 死亡／cron／codex WT／多 WT／deep-work）：修法方向全部正確，破洞集中「跨 session 接手／消費端 repo／無 EP standalone」三場景（細節見報告 transcripts 節）。
- 〔09-09 agent1（transcript 考古——Claude/codex 池＋mosaic 消費端）回報——完成，`.agent-tmp/dryrun/agent1-transcript-archaeology.md`〕**斷點實證裁定**：**PB3 ✅✅ 唯一大規模實害**——fast-kchart 弧（2edb5b87）：00:55「5a 完成（Kanban Done＋EP _done）」→ 01:18 code-review 才發現 Important（鏈順序全靠 user 追問「有跑 /judge-review 嗎」撐起）；MOS-25 卡 Done 時仍有 finding 未綠＋L6 兩天後補；MOS-14「已 Done 補跑不重開」；**tour corpus 債滾雪球 77 FAIL**（多弧 Done 簽發＋tour_validate 只報不修）＝唯一真實爆炸。JR1 ✅ 但形態修正——無跨 session 爆炸（同 session 都接起）；**EP 在 5a 歸檔 → 「EP review 區段」結構性不可用 → `.review` 是事實帳本**（d9d7da01 judge 檔頭自述「無 EP，local-only fallback」照寫 .review；nt_v1 殘留證明決策欄住 .review）。PB1 路徑實證×2 後果輕微（2f874ca6 consistency 曾真抓 9 處錯；muse 弧把 .md/.json/.html 全判 docs-only vs AIR-23 HTML→code=yes——**兩週內兩種相反 triage＝不一致本身是證據**）。IM1 路徑發生未爆（agent 自問「did I change nav docs」補上）。**CR1/PB2 大多無實證**（`resume=yes` 全 corpus 零次——resume 路徑從未觸發；CR2 baseline≠HEAD 僅 AIR-23 一次人工解；baseline 靠 prompt 文字跨 session 傳非帳本 metadata）。EP1 無實證（simple 判定真實、皆低風險——掃描保留：成本低）。**IM2 已發生**（同 repo 連續兩弧走出相反行為＝雙契約隨機解析）；IM3 契約文字從未被執行（agents 一律直接讀 WIP）。
- 〔09-09 agent1 工作流形態→架構級約束〕**鏈非線性**：/code-review 38＋/judge-review 24 次呼叫（高頻、多 standalone）；/implement 各 1、/post-build 共 5——**implement→post-build 完整鏈從未一體跑過**，post-build 的 triage/resume 契約大多未行使；build 側由 mosaic 自有 /build（9 次）＋in-build review agents 承擔；收尾常由 user 口頭組裝。跨 session resume（/at 26＋/handoff 16）＋quota 死亡接手是真實模式（codex 09-08 弧前手 reviewer 死於 usage limit、靠 checkpoint 檔恢復）。**user 是實質糾錯環節**（追問補鏈、補 L6、半夜修 tour 債）——completion gate 最後一哩由人類記憶承擔。→ 修法服務 standalone 形態為主、pipeline 連續性假設降權；S2 殘留清單 fail-loud 是對 user 糾錯環節的支撐非裝飾。
- 〔09-09 三 agent 合成——證據修正後優先序〕①**PB3＋JR1 實害先行**（tour 債 77 FAIL 證明 Done 早發布滾真實債；agent1/agent3 獨立實證 judge 決策都落 `.review`）；②PB1 分級（語義判準＋快道——三 agent 收斂）；③CR1/PB2/CR2 機械一致性修正但降優先（路徑未行使）；EP1/IM1 低成本保留。**S1 帳本方向修正**：`.review`＝工作帳本（正典化事實——EP 歸檔後唯一可用＋judge 實際落點）；EP review 區段＝規劃期帳本（EP Review Cycle）；不強推 EP 唯一落點。各段吸收修訂已入 S1-S5。
- 〔09-09 MOS-74 resume 鏈一手實測（user 指供 session `sess_8a20c5bd` 後半）→ S5 證據補充〕bridge 直跑命令形態＝`node muse-bridge.mjs task --network restricted --steps 200 --session-id <uuid> --prompt-file <工單> > out 2>&1`＋主 session run_in_background（背景 Bash 無 timeout 上限，856s/442s 實證）；sessionId 取自 `runs --json`/`show --json` footer；followup 工單形態＝heredoc 檔＋逐條 F-1~F-6 清單（豁免項標「裁決非遺漏」）＋要求用原驗證式複驗＋檢查新引入問題；verdict 表附「實際命令與輸出節錄」欄；摩擦點＝多行 `python -c` 帶 `#` 註解被 hook 擋（既有 rule 已覆蓋）。
- 〔09-09 S0 收尾狀態〕三 agents 全數回報吸收完成 ✅；證據搬運 ✅（`references/`：codex-review×9＋mosaic-feedback-queue＋muse-bridge-recipe）；**tour_validate 重現＝不重現**（現行版中文目錄掃描正常、205 tours；17 fails 全為 `future_labels.py` 刪檔 stale 錨＝mosaic 側 corpus 債非 bug——`references/tour-validate-repro.md`）→ **S7 降級結案**（反饋④以不重現證據結案，無移交）。EP 修訂完成，進入 EP Review Cycle（定稿前置）。
- 〔09-09 EP Review 第一輪（GLM in-pipeline——glm-5.3 code-reviewer 載體）〕零 Critical、F1-F4 Important＋F5/F6 Suggestion，全數處置（F1 五消費端／F2 debrief 第四消費端／F3 執行鏈閉合 item 8／F4 卡 desc 回寫／F5 四檔統一／F6 預設決策）；40 錨點抽驗零漂移；baseline 更新 `ba386cb`。EP 進入定稿候選。
- 〔09-09 codex 跨家族複審（session `01a082f3-9f49-7343-a114-28d3ab294a51`，user 轉貼工單）——**5 Important 全採納、0 Critical/Suggestion/design-reversal**〕R1 identity 漏 untracked（`git diff HEAD` 不含新檔；以本 EP untracked＋diff 空零寫入實證）；R2 open=0≠收斂＋發布去重＋缺帳本分支；R3 S3 語義約束殘留路徑判準（前輪 F4 只改卡 desc 沒清段內——教訓：決策回寫要掃段落不是只掃卡）；R4 review-engine S1/S5 共寫漏序列化；R5 transport 三態表/thin forwarder 仍以 wrapper 為恢復主體。codex 自我否證兩候選（S9 P5 加 gate＝擴張範圍、F6 重辯）——判斷紀律好。20 錨點抽驗＋27 命中逐點處置表吸收（commit:139/:145 補入）。修正已回寫 S1/S2/S3/S5／整合策略／UC 表／SM（＋SM-11~14）。
- 〔09-09 muse 定向複審（審查鏈第一腿——bridge 直跑 job `job-mtt9w4kn-vsx951`、session `01a08340-6c9e-7153-8bcc-53b9dacfae8b`、工單 `.agent-tmp/muse-ep-review-air50.md`）〕**R1-R5 全數驗證落地**（逐項 rg 證據＋行錨點；14 錨點抽驗全中；`.agent-tmp/` gitignore 細節也查了）。新輪 **M-F1 Important**（UC product 表止於 S7——S8/S9〔user 裁定 C 線〕缺席＝可被略過；收尾計數過時）＋3 Suggestion（M-S1 快道「純修飾」producer 自判無背書——MUST→SHOULD 反例＝PB1 經快道復活；M-R3R 史表逐字自引絆倒 0-hits 機械門；M-F5 缺兩條 happy path）——judge 全採納已回寫：UC 表補 S8/S9＋S7 行降級、S3 快道加模態詞機械排除（詞表單一源）、史表 R3 行改述、SM-15/16 補、收尾改自舉。muse 否證義務有做（攻擊快道安全→部分成立→護欄收斂非推翻；自承歡迎 judge 推翻）。**下一步：muse 同 session followup resume 複驗（審查鏈第二腿，MOS-74 形態）**。
- 〔09-09 muse followup 複驗（審查鏈第二腿——同 session resume，job `job-mtta1oo8-j7m8y3`）〕**4/4 原 findings resolved**（自家驗證式重跑：M-F1 S8/S9 行＋自舉收尾、M-S1 模態詞條款、M-R3R 0-hits、M-F5 SM-15/16）；前輪紀錄完整性也驗了（codex＋muse 兩 bullet 在場——主 session 兩次 Edit 取代失誤已復原並經獨立確認）。**新殘留 2 條 Suggestion → fail（皆一行可收）**：N-1 詞表漏單字「禁」（repo 禁令主力形態＝禁掛/禁改/禁寫——work-order 3 hits 實證，現詞表放行）；N-2 SM-15 checkpoint「走一遍」非機械。judge 全採納已修（詞表加「禁」、checkpoint 機械化三查）→ 派第三腿複驗收斂。
- 〔09-09 muse followup 第二輪（收斂腿，job `job-mtta3tgi-48osfx`）——**PASS**〕N-1/N-2 皆 resolved（驗證式重跑：詞表含單字「禁」、SM-15 checkpoint 純機械三查）＋兩項新問題檢查皆過（「禁」誤傷可接受——代價僅多走 docs-mode 與護欄保守方向一致；三查在收斂後時點皆可機械執行）。**審查鏈收斂：muse review（M-F1~M-F5）→ followup 腿1（N-1/N-2）→ 收斂腿 pass——零殘留。EP 三輪獨立審查閉環（GLM in-pipeline F1-F6＋codex 跨家族 R1-R5＋muse 審查鏈 M/N 系列，全數回寫）。〔EP 定稿〕→ hook 1 建殼（badge 📋、殼頭聲明 baseline `ba386cbc…`）。
- 〔09-09 hook 1 完成〕任務家 `index.html` 骨架建畢（template 複製＋六章節導讀——為什麼/三線九段/推進驗收/風險降級/決策記錄/回源；diagram 槽 degraded 待 hook 2；出貨 gate `rg 'SLOT:|{{…}}'` 零命中 ✅；projection source＝ep@83a867015d65 content SHA）；卡 AIR-50 ref 已換殼 URL（開工雙 ref）。**規劃期閉環——下一步＝開工**：checkout air-50（自 main HEAD）＋卡起手式五步＋依 EP 執行序推進（build 形態依 user 裁定——codex 或 GLM 新 session）。
- 〔09-09〕user 指示：**codex 對 muse 鏈輪修正＋hook 1 殼做 delta 複審**（第三家族互審我的回寫——工單 `.agent-tmp/codex-delta-review-air50.md`，user 轉貼）。殼 projection SHA 隨本 bullet 後刷新。
- 〔09-09 codex delta 複審回報（第四輪獨立審查）——**1 Important＋3 Suggestion 全採納**；且確認 R1-R5 無回歸、muse 三腿紀錄無失真、殼 SHA/template JS/出貨 gate 全過〕D-A1 product 表缺 F1 五消費端＋debrief＋commit（收尾自舉源不完整）——表補齊＋聯集規則明文；D-A2 SM-15 三查未覆蓋 references 新址/SM 升級（可機械≠覆蓋完整）——補兩查；D-B1 殼「三輪全量審」失真（resume 腿非全量）——改「兩次全量＋一次 resume」；D-B2 degraded 槽指向不存在同目錄檔＋裝法越界——移除。修正後以 codex 驗證式機械複驗閉環。
- 〔09-09 dry-run 三輪＋考察閉環（含一次 1308 額度事件）〕①第一輪 RED baseline：11 checkpoint 對現況全紅（鑑別力證明）＋SM-15 對 AIR-46 真實走場綠（`.agent-tmp/dryrun/uc-sm-dryrun.md`）。②原派 2 flash 考察 agents（cross-verify-investigator——general-purpose 誤用已修正，見 memory `reference-zcode-agent-model-inheritance`）**雙雙死於 1308 五小時額度**（07:29，窗口 08:21 重置）——muse 接手完成兩份考察（`agentA-zcode-impl-review.md`／`agentB-mosaic-wt-review.md`）。③muse 吸收輪宣稱「零 EP 修訂需求」→ **codex 複審反對（4 Important＋1 Suggestion，主 session 獨立複核五組驗證公式全成立、全採納）**：I-1 bt/lab WT 曾各自提交再 rebase 匯流（reflog 實錘——「無跨 WT 作業」不成立，同檔碰撞 unverified）；I-2 tour 錨債是**既有 gate 執行缺口**非規則缺席（post-build:68 gate 在場、9aeb0609f 觸 .md 零 .tours）——交 mosaic 側追查，不加新規則不併 S9 P5；I-3 EP 定稿 commit（8aed63f2c）不能證明實作（9aeb0609f）受審——證據撤回標 unverified；I-4 AIR-46 帳本去向 unverified 不得固化為案例（撤回 S2 加句提議）；S-1 失配錨靜態可確認 ≥6 非 4、17 FAIL 組成 unverified。處置表已修正（uc-sm 第三輪）＋兩報告 errata 就地 append。**修正後「零 EP 修訂需求」成立**——dry-run 三輪關閉，開工條件恢復。
- 〔09-09 規劃 commit＋推進圖〕規劃閉環落地 commit `4f07ad8`（17 檔：EP＋殼＋references×14＋雙卡；air-50 branch 快進至同點）。user 指示 illustrate 預計實作——殼 s2 槽裝**三線九段推進圖**（HTML 塊直寫載體——對照/層次性質、零渲染管線；出貨 gate 零命中＋template JS `cmp` 逐字一致）；hook 2 仍照原計畫補實作面圖。**開工待 user 啟動**（GLM 窗口 08:21 重置後）。
- 〔09-09 user 裁定→**S10 新增**〕review agent 層（ep-review／code-review 審查 agents）**預設 lite（glm-5.3-flash）**——本弧四輪審查實證支撐（findings 生產層跨層品質皆高、判斷價值集中 judge 裁決層）；兼修 model-routing rule↔skill 既有 drift（骨架「full 為基準」vs skill:42 09-07 放寬）；registry pins 經 sync_agents 重生成。已決策入卡 desc ⑫。
- 〔09-09 mosaic 反饋⑤→**S11 新增**（user 仲介，合理性查證後採納）〕rename 反掃 instruction 檔——地毯掃描量化證據（44 AGENTS.md 1173 引用平時僅 7 失效、但 5/8 P1+P2 源自兩 rename 型 EP 結案未同步）；**主 session 抽驗屬實**（`TW_STOCK_REGIME` 仍殘留 mosaic `venues/tw/AGENTS.md`＋callstack）。證據 durable 化 `references/consistency-sweep/`（4 檔——原在 mosaic .agent-tmp 7 天清掃區）。post-build 共檔鏈擴為 S1→S2→S3→S11。
- 〔09-09 AIR-46 弧 session（`sess_88e4ceae`，user 指供）→ 接續鏈第二實證＋wrapper 定案〕三形態實測：agent 轉發跑 review（18 findings judge 逐條回源驗證全採納）／`--session-id` resume followup（F1–F10 一輪收斂、零殘留——**resume 經濟學成立**：第二輪記得自己 findings 編號措辭、只餘 delta）／**msg 118 定案：muse 腿改 Bash 直呼 bridge CLI——agent wrapper 只是載體（muse 是外部 runtime）、佔 agent slot 打 rate limit 不合理**。摩擦：agent 名錯誤（`muse-rescue` 不存在，正確＝`delegate-rescue`）。不滿意訊號：**judge 零否決×2**（18+10 全採納——sycophancy 下傳風險，三防線#2 未觸發）；15 行 docs 卡走三輪 muse＋兩次全量審＋一次 resume（**重量分級需求**——餵 S3 快道；反向警示：continuation 帶整包 context，可口述任務走 handoff doc）。結論：鏈結構有效，修 judge 否決力與重量分級非砍鏈。F7 附帶抓到 AIR-50 建卡 commit 誤落 air-46 branch（air-50 branch ref 已解）。
- 〔09-09 user 裁定＋arch-thinking 三視角——「GLM agent 包 muse agent」確認錯誤形態〕**依賴規則**：adapter-over-adapter（bridge CLI 之上再包 subagent）——process babysitting 是 infra 職責，背景 Bash 是 harness 原生 process supervisor，wrapper 零 domain 邏輯純轉發；**bounded context**：幽靈 context（有邊界無職責）＋failure surface（名稱錯誤實證）；**use case**：消費者要 findings＋jobId——直跑零中間層即滿足，wrapper 唯一「價值」是被誤判的 600s timeout 約束（run_in_background 從頭可用）。**錯在三處**：①派發側載體語義留白（收法決策樹已直跑，但 model-routing:42 審查類段／reviewer 交接契約未明文承載者＝背景 Bash）②`delegate-rescue` agent 存在＝官方感（工具強化慣例第三層——plugin 側殘留）③「簡單轉發」標題詞彙殘留＋ZCode 無 spawn-time model 參數讓人誤以為需 agent 定義載 model（bridge `--model/--effort` flags 直達）。**bridge CLI 本身無錯**（ledger 必經是對的設計）——錯在 agent 側包裝層。修法：S5 擴充（承載者明文）＋新段 S8（delegate-bridge repo 修訂工單）。
- 〔09-09〕**user 裁定「49 50 同一整合 EP」——對象待確認**：AIR-49 已 Done（四段全交付、011d420 落地）無殘餘；board 開著的是 **AIR-48**（In Progress——剩 P4 dogfood：3-5 session/48h 逐案四欄）＋AIR-50。推測指 **48＋50**（主題契合：agent wrapper 誤用正是 AIR-48 載體濫用統一定義表的新條目）——待 user 確認後併 EP 與卡。
- 〔09-09〕**user 確認 48＋50 合併**（AIR-49 為誤記）——S9 吸收 AIR-48 剩餘：P4 dogfood（窗口至 09-10、case#1 已記）＋P5 三 user 裁決點（writer 歸因 telemetry last-writer 投影——p5-writer-attribution-proposal.md）＋統一定義表補 wrapper 誤置條目；雙卡 notes 已互掛。**git 事件**：平行 session 已將 air-46 ff 併回 main（`ba386cb`）——卡 commit `0cd90a5` 已隨之入 trunk；user 誤刪 air-50 branch 已重建並快進至 main（開工 checkout 依新 git 慣例——AGENTS.md「git 慣例」節，air-46 弧落地）。

---

## 實作總覽

兩條工作流一次弧收斂（同碰 review 鏈契約檔，分攤 sync-sources/consistency 收尾成本）：

- **A 線——codex 架構審查六斷點修復**：跨 skill 契約接不起來的六個斷點（帳本分裂／結案時點四方 drift／.md 跳行為審查／refactor 跳架構同步／弧範圍與 resume 不綁內容身份／invariant 防線掛在已被排除的載體）＋次級（IM2 consent owner／IM3 shared-isolated 前置錯置／JR2 語氣／PB4 證據失效／EP2 需求邊界流失）。
- **B 線——mosaic MOS-74 全弧反饋固化四條**：bridge 直跑範式（agent 轉發退役）＋resume 鏈記載＋Finding 驗證式欄／工單要素、tool-discipline 背景跑通則＋三層反模式案例、tour_validate 中文目錄 bug 移交。
- **C 線——AIR-48 剩餘吸收（user 09-09 裁定 48＋50 同弧）**：P4 dogfood 收尾＋P5 writer 歸因三裁決點＋統一定義表補「agent wrapper 承載外部 runtime＝誤置」條目（與 S5/S8 同主題）。

修復原則（已決策，見卡 desc）：保留七 skill 入口不合併；先修交接→再修分流→最後減法；單一源紀律——動定義源必 rg 掃全引用同步。

## UC 盤點（docs mode：受影響命令/rules 清單）

### 受影響檔案面（本 EP 的 product scope）

| 線 | 段落 | 檔案 |
|----|------|------|
| A | S1 | skills/judge-review、skills/post-build、skills/code-review、skills/implement、skills/followup-review、skills/debrief、skills/review-engine（唯一 owner——S5 消費）、skills/_common/workflow-review-pattern.md、skills/execution-plan |
| A | S2 | skills/implement、skills/metadata-sync、skills/_common/illustrate-html-mode.md、ai-development-guide.md（全域部署源；S3 invariant 例外面共編此檔）、skills/kanban-board、skills/post-build、skills/commit、skills/flow-review、skills/blueprint-bootstrap、skills/maintain、skills/CLAUDE.md、rules/context-management.md（後六者＝F1 五消費端＋commit——codex D-A1 補齊） |
| A | S3 | skills/post-build、skills/implement、skills/metadata-sync、skills/execution-plan |
| A | S4 | skills/implement、skills/post-build、skills/code-review、skills/agent-workflow |
| B | S5 | skills/model-routing、skills/_common/work-order.md（followup-review／review-engine 共檔部分待 S1——見整合策略 codex R4） |
| B | S6 | rules/tool-discipline.md |
| B | S7 | （降級結案——重現不重現；產出＝`references/tour-validate-repro.md`，無 product 變更） |
| B | S8 | （跨 repo 工單——產出 `references/delegate-bridge-redesign.md` 新檔；無 skill 編修） |
| C | S9 | skills/memory-audit（統一定義表新條目——唯 product edit）＋任務家 09-08-carrier-misuse-definition 消費（P4 dogfood 記錄/p5 提案） |
| 裁 | S10 | skills/model-routing（tier 段 :42＋:40 例外細節）、rules/model-routing.md（角色→tier 表）、skills/ep-review、skills/code-review（spawn 指引）、agents/roles/（code-reviewer(-primed) tier 標籤）、agents/zcode/ 經 `scripts/sync_agents.py` 重生成（生成檔不手改） |
| B | S11 | skills/post-build（metadata-sync 段——與 S1/S2/S3 共檔序列化）；證據 `references/consistency-sweep/`（唯讀消費） |

> **收尾自舉範圍＝本表與各段「修改要點」所指檔案的聯集**（codex D-A1 明文）；表為 file-level 完整清單，單一檔可多段共編（如 guide 同時是 S2 結案時點與 S3 invariant 例外面）。

### Backlog 關聯

- EP 追蹤卡：AIR-50（建卡即 commit；開工雙 ref 掛 implement 階段 1）
- 無重複承諾卡（`backlog search 契約/review 鏈` 已掃——Done 卡無同域）

### 同主題 memory 條目（結案蒸餾範圍）

- `project_codex-skills-arch-review-0909`（本審查弧紀錄——結案時蒸為終態：六斷點確認清單＋修復落地事實）
- `project_commit-finalization-gate`（S2 脈絡：commit 2.8 對帳閘門／孤兒結算既有決策——修法不得與其衝突）
- `feedback_judge-review-stays-main-agent`、`feedback_consistency-gate-not-optional`、`feedback_review-even-on-quick-fix`（S1/S3 修法不得違反的既有 feedback）
- mosaic 側 `project-muse-code-review-adoption`（B 線 patch 參考文本——mosaic 側已改寫，承接不重做）

### 掃描範圍

- codex checkpoint 00-08 檔（暫存，S0 搬入本任務 `references/`）
- mosaic `.agent-tmp/ai-rules-feedback-queue.md`（暫存，S0 搬入 `references/`）
- `~/.zcode/cli/memories/projects/ai-rules-01610fbb20315a8b/memory/`（rg 命中如上）

## Scenario Matrix（docs 語境——rg 命中／行為改變可驗）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應 |
|---|------|------|---------|------------|------|
| SM-1 | .md-only 行為控制面變更跑收尾 | 只改 skills/ 下某 skill 的契約段 | post-build triage 判「行為控制面」（語義判準）→ 走 code-review docs-mode（跨檔契約被審），非僅 consistency | rg：post-build triage 表含控制面語義分流（非路徑枚舉） | S3 |
| SM-2 | 收尾修正迴圈未收斂 | post-build 3 輪失敗 | 卡維持 🟡／In Progress、Done/badge ✅ 未發布、殘留清單進報告（無模糊 Done） | 收尾報告＋卡 frontmatter 可機械查 | S2 |
| SM-3 | 大 WIP 跨 session（S1 已 commit＋S2 大 uncommitted） | 無參 post-build/code-review | 弧模式依 EP baseline 觸發（baseline..HEAD＋uncommitted），不依「uncommitted 空/trivial」 | rg：舊觸發條件 0 殘留 | S1 |
| SM-4 | 無 EP standalone judge 要持久化 | 獨立 /judge-review 無 EP | `.review` 是明確合法決策落點（caller 無 EP 時）；有 EP 由 caller 指定 | workflow-review-pattern 位置表更新 | S1 |
| SM-5 | 單檔 silent-corruption fix 判 simple | 消費端量化 repo（如單位轉換 fix） | simple 分流前掃 invariant 清單：命中 → 升 standard 或 simple 附輕量 invariant 聲明 | rg：execution-plan 分流段有掃描步驟 | S3 |
| SM-6 | 跨模組純 refactor 無新 UC | 大型 refactor EP | 5b 照跑、architecture.md 依內容條件同步（不綁情境 A） | rg：implement/metadata-sync 舊條件 0 殘留 | S3 |
| SM-7 | judge 中斷跨 session 接續 | quota 死亡接手 | 帳本單一（caller 指定）＋reviewed revision 在帳本 → 接手讀到含決策最新清單 | Finding Record 欄位在場 | S1 |
| SM-8 | external reviewer（muse）工單 | bridge review 委派 | 工單要求 findings 每條附可機械複驗驗證式（rg/pytest） | rg：work-order 有驗證式要素 | S5 |
| SM-9 | 長命令（>10 分）需執行 | 任何長跑命令 | 背景 Bash 跑是預設；spawn agent 不是繞 timeout 的手段 | rg：tool-discipline 通則條款在場 | S6 |
| SM-10 | 外部 runtime 審查委派 | bridge review/followup 委派 | 主 session 背景 Bash 直呼 bridge，不佔 agent slot；無 wrapper agent | rg：model-routing 承載者條款在場 | S5/S8 |
| SM-11 | untracked-only WIP 改變後 resume | 新檔內容改、HEAD 不變（tracked diff 空） | identity 含 untracked 清單/content hash → 不沿用舊審查 identity、補審 | rg：identity 條款含 untracked（codex R1——本 EP 即實證） | S1 |
| SM-12 | 非 open 未完成 finding 存在 | 帳本有 adopted 未實作／implemented 未 verified | 不得以 open=0 宣稱收斂——按狀態生命週期處置 | EP S2 收斂檢查條款（codex R2） | S2 |
| SM-13 | fallback 已發布後再進 hook 2 | 結案過一次、post-build 再跑到 hook 2 | 發布去重：任務身份＋結案狀態核對 → 跳過不重做 | EP S2 發布去重條款（codex R2） | S2 |
| SM-14 | bridge 直跑中途死亡 | 背景 Bash 跑 bridge、transport 死中途 | 恢復處置以 caller process／bridge job 主體表述（非 wrapper） | rg：transport 三態表無 wrapper 依賴（codex R5） | S5 |
| SM-15 | 收斂後正常結案（happy path） | 帳本全 verified、post-build 收斂 | 結案兩步＋EP 歸檔＋SM 升級一次發布（卡 Done） | 卡 status＝Done＋結案第二步 references 已換 done/ 新址（`task view` ref 欄）＋EP 歸檔入 done/＋Capabilities ✅ 行在場＋受影響 SM 功能狀態非 📋/⚠️（muse M-F5；N-2 機械化＋codex D-A2 補完整覆蓋；重入語義由 SM-13 承載） | S2 |
| SM-16 | 三鍵等價 delta-only（happy path） | implement 階段 4 已審同範圍＋同 revision＋同 profile | post-build 只補修正迴圈 delta＋跨段整合面（不全審） | 帳本 identity 對照可機械判（muse M-F5） | S4 |
| SM-17 | EP/code review spawn 審查 agents | ep-review／code-review 執行 | 審查 agents 跑 lite（flash pin）；judge 仍主 session full | rg：registry pins＋skill「lite 預設」條款（user 09-09） | S10 |
| SM-18 | rename/move/retire 型 EP 結案 | 弧含符號改名/下沉/退役 | metadata-sync 段反掃舊符號（AGENTS.md 家族＋快 drift 檔）→ 命中修或記 drift；非 rename 弧空跳 | rg：post-build 反掃條款在場；實證錨＝mosaic `TW_STOCK_REGIME` 殘留 | S11 |
| SM-19 | 刪除／派工前查證 | 刪無測試檔／派 bridge 工單／user 提模型詞 | 刪前查 backlog 卡；bridge 派發印 echo；口語詞經 family 表正規化（非表內詞＝查表訊號） | rg 三條款在場（user 09-09——四事故收口） | S12 |

## 段落劃分原則

- 垂直切片 by 根因群（codex 08-final-index 分群）；A/B 線共檔者已併段（反饋③驗證式欄併 S1——同碰 Finding Record）。
- **序列約束**：post-build 與 implement 被 S1/S2/S3/S4 多段共編 → A 線依 S1→S2→S3→S4 序列執行；B 線（S5/S6）與 A 線檔案不重疊，可平行。
- S7 無 ai-rules product 變更，隨時可做（建議先做——實證輸出餵 S0 記錄）。

## 段落 0：研究收斂與證據落地（定稿 gate）

**Context**：EP 定稿前必須收齊三件事——(1) 暫存證據搬 durable（防 7 天清掃）(2) 三背景 agents 遺漏吸收（3) tour_validate bug 重現實證。未收齊不定稿、不建殼（hook 1）。

**任務**：

1. **證據搬運**：`mkdir references/`；cp codex checkpoint 00-08 → `references/codex-review/`；cp mosaic `ai-rules-feedback-queue.md` → `references/mosaic-feedback-queue.md`；cp mosaic 側 memory `project-muse-code-review-adoption.md` 的「Bridge 操作配方」段 → `references/muse-bridge-recipe.md`（patch 參考文本）
2. **三 agents 吸收**：讀 `.agent-tmp/dryrun/agent{1,2,3}-*.md`；逐修法段（S1-S6）append「dry-run 吸收」小節——遺漏項要嘛入段（修法擴充）、要嘛明確排除（附理由）；修法優先序若被實證推翻（某斷點從未實際發生且修法成本高）→ 降級或移出，記進度節
3. **tour_validate 重現**（可提前，輸出供 S7）：在 mosaic repo 跑 `code-reality tour_validate --manifest --repo /Users/ctai/Github/mosaic_alpha` 與 `--tours-dir .tours/arch` 顯式形態，節錄輸出存 `references/tour-validate-repro.md`（read-only 對 mosaic——只跑驗證命令不改其檔）

**驗證**：references/ 三組檔在場；三 agents 報告都被吸收且每段有「dry-run 吸收」小節或明確「無遺漏」；進度節記錄定稿決定。

## S1：交接契約統一（JR1＋PB2＋CR1＋CR2＋JR2＋EP2＋反饋③驗證式欄）

**Context**：
- **背景**：review 鏈的 findings 帳本、審查範圍、resume 身份各自為政——judge 自選 EP 作決策落點而 post-build 全鏈讀 `.review`；弧模式觸發綁「uncommitted 空」而非任務身份；resume 只認帳本存在＋open 不認審過哪版。
- **依賴**：S0 吸收（agent1/agent3 的實證決定優先序；agent2 的遺漏決定修法形態）。S2 共編 post-build/implement（序列在前）。
- **語義約束**：與 S5 共享「帳本」詞彙——S5 改 followup-review muse 續接段時，帳本指向須與本段 caller-指定模型一致，兩段不得各自定義。
- **基礎設施盤點**：既有 Finding Record（workflow-review-pattern:95-126）＋status 生命週期已完備，擴欄不重建；muse 續接驗收形態（followup-review:53-62）已存在，本段統一其帳本引用。
- **依賴錨點**（現行——執行前重驗，drift 先更新）：
  - judge-review/SKILL.md:56（持久化段——禁 .review 作決策落點）、:31（反拖延「當下落地」無 actor）、:87（不實作）
  - post-build/SKILL.md:33（弧模式觸發）、:35（Resume 場景）、:43/:49/:58（.review 讀寫）
  - code-review/SKILL.md:34（弧觸發）、:108（snapshot 消費＝EP baseline hash8）、:178（.review 寫入時機）
  - implement/SKILL.md:79（snapshot 錨 build 起點現狀）
  - workflow-review-pattern.md:99-115（Finding Record 欄位）、:117-126（持久化位置表）
  - followup-review/SKILL.md:36（zoom 報告作帳本）、:51（更新）、:61（.review 法定帳本）
  - debrief/SKILL.md:25（EP Review F2——「uncommitted 空/trivial → 弧模式」條件的第四消費端）
  - execution-plan/SKILL.md:195（段落 Context 的 spec 引用）
- **技術選型**：擴欄＋改條件，不新建檔、不造新機制（帳本仍是 markdown Finding Record）。
- **成功標準**：SM-3/4/7/8 場景行為改變且 rg 可驗。

**修改要點**：

1. **帳本正典化——`.review`＝工作帳本、EP review 區段＝規劃期帳本**（吸收修訂：agent1/agent3 獨立實證 judge 決策實際都落 `.review`；EP 5a 歸檔後「EP review 區段」結構性不可用〔fast-kchart 弧〕）：跨命令鏈（post-build 編排、standalone code-review→judge→followup）帳本＝`.review`；EP review 區段僅服務 EP Review Cycle（規劃期、EP 未歸檔）；judge-review 持久化段改「更新呼叫端指定帳本（鏈上預設 `.review`）」——刪「不作為決策落點」貶抑與「跨 session 不保留」錯誤前提（改為：local-only、同 worktree 跨 session 保留、跨 branch/worktree 不保留——post-build Resume 正依賴此；`.review` 隨 commit 清除——晚到 findings 的 durable 落點由 S2 殘留清單承載）；workflow-review-pattern 位置表改「工作鏈＝`.review`（caller 指定可覆寫）；規劃期＝EP review 區段」；caller 清單三處——post-build、implement 階段 4、execution-plan:353（EP Review Cycle 的 judge 呼叫）；followup-review 讀寫帳本對齊、保留 zoom 報告為合法 baseline 形態之一；muse 續接段措辭對齊；judge-review:138 流程位置行連動
2. **Finding Record 擴欄（header 級 identity＋逐條驗證式）**：表頭加 identity 區塊——task baseline（卡 desc 或 EP 整合策略）＋reviewed hash＋**uncommitted identity**（**本弧 tracked diff hash＋untracked 路徑清單＋content hash**——沿用 work-order §3 既有 dirty identity 契約同詞；`git diff HEAD` 不含 untracked，缺 untracked 面則「untracked-only WIP 改變」場景假吻合跳審——codex R1 以本 EP 自身實證：untracked、`diff HEAD` 空、內容持續變）＋writer；逐條加 `驗證式`（verification formula：rg 命令／pytest case——Important+ 必附；反饋③）；code-review Finding 呈現段、**review-engine spawn prompt 契約（S1 唯一 owner——S5 消費驗證同詞不寫入，codex R4）**同步加驗證式要求
3. **弧模式觸發改任務身份優先**（吸收降級：兩池實測「大 WIP 漏前段」未發生——卡 baseline→HEAD 形態已在跑，本項是機械一致性修正非止血）：code-review:34、post-build:33、**debrief:25（EP Review F2——第四消費端）** 改「context EP／卡 desc 記有 baseline（或殼頭可讀）→ 弧模式（baseline..HEAD＋uncommitted）；無 baseline 才退 uncommitted」——刪「uncommitted 空/trivial」條件；fail-loud 分支保留；**同樹多任務出口**：弧範圍內非本弧 commits／uncommitted 檔列「非本弧項」清單（AIR-23 allowlist 人工形態正典化）
4. **resume 身份核對**：post-build:35 Resume 條件改「帳本 reviewed revision 與當前任務狀態吻合才跳 code-review；不吻合 → 保留舊 findings、補審新增變更（delta review）」
5. **snapshot 身份對齊**：implement:79 錨點與 code-review:108 消費鍵統一——EP baseline 與 build 起點 snapshot 分開記身份；code-review 消費實際存在者，snapshot 晚於 baseline 時明示對照只覆蓋該區間
6. **JR2 語氣**：judge-review:31 反拖延段加 actor（「apply 由呼叫端；judge 義務＝交付可執行決策＋驗證依據」）
7. **EP2 需求邊界**：execution-plan 段落 Context 元素加「需求邊界繼承」——有 spec 時 Always/Ask First/Never 顯式入段（不引用編號，自包含轉述）

**驗證策略**：rg 殘留——`不作為決策落點`、`uncommitted 空（或僅尾段殘留）`、`跨 session 不保留` 於目標檔（**含 debrief**）0 hits；`驗證式` 在 **workflow-review-pattern／code-review／review-engine／work-order 四檔**（S5 連動——EP Review F5 統一清單）在場且同詞；跨檔一致性——「帳本由 caller 指定」敘述在 judge/post-build/followup/workflow-review-pattern 同語義；每個變更檔跑 `/consistency`；`/sync-sources` 機械檢查。

## S2：完成狀態單一發布時點（PB3＋IM2）

**Context**：
- **背景**：結案兩步（`-s Done`）／EP 歸檔／badge ✅ 有兩派發布時點——implement 5a 情境 A（implement:251、metadata-sync:27/40/44、全域 guide UC 生命週期）vs illustrate-html-mode:94-95（5a 卡不動、結案放 post-build hook 2）。post-build:59 允許未收斂退出——5a 派先發布 Done 後無撤回契約。
- **已決策**：採 illustrate-html-mode 版時點——結案單一發布於**收斂後**（post-build hook 2；無 post-build 弧＝implement 階段 6 fallback）；5a 只到 🟡 Built 預覽。與 `project_commit-finalization-gate` 既有決策（commit 2.8 對帳／孤兒結算）不得衝突——結案仍在 working tree、隨弧 commit 帶走。
- **依賴**：S1 序列在前（共編 post-build）；agent3 軸 A/C（ZCode 端 post-build 實際使用率——若 ZCode 弧極少跑 post-build，fallback 路徑＝主路徑，措辭權重調整）。
- **語義約束**：Capabilities ✅ 寫入時點隨結案（5a 情境 A 的「全項結算」拆兩段：5a＝Capabilities＋消費場景＋SM 預覽〔🟡〕；收斂後＝結案兩步＋EP 歸檔＋flow-feedback 歸檔＋SM 升級）；「結案兩步」一詞全 repo 單一語義。
- **依賴錨點**：implement/SKILL.md:251（情境 A）、:252（情境 B 預覽）、:256（為什麼結算在 build）、:258（badge 同步）、:273；metadata-sync/SKILL.md:16-21、:27-30（情境矩陣）、:40（backlog 結案）、:44（EP 歸檔）、:87（兩段式確認）；illustrate-html-mode.md:93-96（掛點表）；ai-development-guide.md（UC 生命週期段——行號執行時 rg 定位）；kanban-board SKILL（結案兩步段）；post-build/SKILL.md:59、:83（badge）；**（EP Review F1 補五消費端）** skills/flow-review/SKILL.md:59（flow-feedback 歸檔掛 5a 情境 A——與收斂後時點直接矛盾）、skills/CLAUDE.md:56-57（「finalization 已在 build 5a 結算」）、skills/blueprint-bootstrap/SKILL.md:29、skills/maintain/SKILL.md:127、rules/context-management.md:39（bundle 部署面——隨 deploy_agents 同步）
- **成功標準**：SM-2 場景可驗；四方（guide/implement/metadata-sync/illustrate-html-mode/kanban-board）同詞同時點。

**修改要點**：

1. implement 5a 情境矩陣重劃：情境 A 拆「Built 結算（5a）」與「final 結案（收斂後）」兩動；273 小型變更措辭與 5b 脫鉤（見 S3）
2. metadata-sync：情境矩陣同步拆段；兩段式第 2 步（:87）build mode 移除用戶確認要求（授權來源＝EP 已批准＋IM2 單一 authority；standalone 保留確認）；EP 歸檔項目標註時點＝收斂後
3. guide UC 生命週期 ✅ 段改「5a Built 結算 → post-build 收斂後結案兩步」；**rg `結案兩步` 掃全 repo**（含 agents/、commands/、skills/CLAUDE.md 索引）逐一同步——這是定義源變更，漏一處即 drift
4. post-build:83 badge 段對齊（✅ 只在收斂後；implement 5a 同步的是 🟡）；:59 未收斂退出 → 明確「維持 🟡、殘留清單進報告、不發布結案」
5. kanban-board 結案兩步段時點措辭對齊（「build 5a / post-build」→「收斂後（post-build hook 2／implement 6 fallback）」）
6. **雙發布防護**（dry-run 洞＋codex R2 拆解）：implement 階段 6 fallback 觸發條件收緊（user 明示不跑 post-build／弧終止才走，非 session 自行預測）＋兩道檢查——**①收斂檢查**：發布結案前按帳本完整狀態生命週期處置（`open`／`adopted` 未實作／`implemented` 未 verified 皆屬未收斂，**不得以 `open=0` 宣稱收斂**；`needs-confirmation` 保留既有裁決語義、彙整報告不阻塞）；**②發布去重檢查**：核對任務身份與實際結案狀態（卡 status／hook 2 已執行 → 跳過不重做——fallback 已發布後再進 hook 2 必須能識別）；**缺帳本**（`.review` 不存在）→ 明確分支（fail-loud 標示＋以 git／卡狀態推導），**不以空集合冒充驗收通過**；fallback 與 hook 2 同為**並列主路徑**（ZCode 實測 post-build 覆蓋率非 100%——AIR-31/47 S5 未跑即結案）；**結案 gate 一律是 skill 流程步驟，禁掛 SessionEnd hook**（ZCode live hooks 僅 PreToolUse/Stop——SessionEnd 靜默 no-op）
7. **殘留清單 durable 落點**：未收斂項除收尾報告外寫 EP 進度節（`.review` 隨 commit 清除、報告在對話——兩者皆非 durable）；user 是實質糾錯環節（agent1 實證：追問補鏈、補 L6、半夜修 tour 債）——fail-loud 殘留清單是對這環節的支撐；flow-feedback 歸檔的 judgment gate **保留**用戶確認（IM2 免確認僅限機械狀態結算，判斷型結算不拆防線）
8. **收斂後結案的執行鏈閉合**（EP Review F3）：metadata-sync 兩 mode 觸發者表加第三觸發者——**post-build hook 2（收斂點 invoke metadata-sync 結案段）**；post-build 正文（階段 5 後）補結案步驟敘述（結案不能只住在 illustrate-html-mode 掛點表）；implement 階段 6 fallback 同段呼應。**F6 決策（預設）**：Capabilities 行維持 5a 寫入（導航職責、working tree 未 commit 前不外發），語義張力以「情境 A 結算＝Built（🟡）」措辭收斂——✅ 完成宣稱的正式時點仍是結案兩步

**驗證策略**：rg 掃描組 `結案兩步|5a 結算|--final-summary` 全 repo 逐命中檢查時點語義一致（**含 skills/commit/SKILL.md:139/:145/:174——:139 亦「5a 結算」措辭、:145 結案態 guard、:174 已知；codex 27 命中表吸收**；含 execution-plan 收尾步驟模板）；檔案清單補 skills/commit 與 skills/execution-plan（兩者皆描述結案時點）；guide 改動後跑 `uv run python scripts/deploy_agents.py`（部署同步）＋`/sync-sources`；每檔 `/consistency`。

## S3：分流維度修正（PB1＋IM1＋EP1）

**Context**：
- **背景**：三個分流把「載體/規模/UC」維度錯接——副檔名 .md ≠ 無行為影響（ai-rules 的 md 就是控制面）；純 refactor ≠ 小型（恰是最需架構同步的變更）；simple ≠ 無 invariant（silent-corruption 修復的防線掛在 simple 不寫的 EP 元素上）。
- **依賴**：S1/S2 序列在前（共編 post-build/implement）；agent1/3 於消費端 repo（mosaic 等）找 .md-only 與 refactor 弧實證。
- **語義約束**（codex R3 修正——前版殘留路徑判準已清）：「行為控制面」判準＝**語義**（塑造 LLM 行為的 instruction／規範檔——AGENTS.md 家族／rules／skills／agents／commands／hooks／settings／guide，含消費端 repo 同類檔）；路徑清單僅為 **hint** 非判準；與 execution-plan docs mode 觸發判準（:269）同詞對齊，不在 post-build 重定義（implement:40 舊偵測同步引用單一源）。
- **依賴錨點**：post-build/SKILL.md:27-31（triage 表）、:64-67（docs 鏈）、:112（「含 docs-mode 弧」的內部緊張）；implement/SKILL.md:40（docs 偵測）、:273；metadata-sync/SKILL.md:43（architecture.md 綁情境 A）；execution-plan/SKILL.md:48（simple 不寫 EP）、:52（防濫用）、:54-59（結構性修復非 simple）、:203-214（§1b）、:210（唯一防線自陳）；code-review/SKILL.md:80-82（docs-mode 軸）
- **成功標準**：SM-1/5/6 可驗；控制面 .md 變更不再只跑 consistency。

**修改要點**：

1. post-build triage 改**語義判準＋分級快道**（吸收修訂——路徑枚舉 self-defeating：repo-root guide 與消費端控制面〔模組 AGENTS.md／SYSTEM-MAP／hooks〕都不在 skills/rules/agents/commands 清單，本 EP S2 改的 guide 逃過自己建的 gate；mosaic 兩週內兩種相反 triage 實證不一致）：**控制面變更**（塑造 LLM 行為的檔——AGENTS.md 家族／rules／skills／agents／commands／hooks／settings／guide；路徑清單降為 hint）→ code-review docs-mode（正確性/架構/phantom 軸）→ judge → followup；**純修飾**（單檔 typo／措辭、無契約語義變更）→ 輕量快道（consistency＋rg 引用掃——防 ai-rules「產出主體即文檔」每弧全鏈）——**機械排除（muse M-S1 護欄）**：diff 命中規範模態詞（`禁（單字——覆蓋禁掛/禁改/禁寫/禁用，本 repo 禁令主力形態；muse N-1）／必須／禁止／不得／應該／永不／MUST／SHOULD／NEVER`——詞表單一源列此處）→ 一律升 docs-mode 不得走快道（producer「無語義變更」自述不背書——Claim→Evidence；反例：單檔 MUST→SHOULD 過 consistency＋rg 卻改變控制語義＝PB1 失敗模式經快道復活）；**資料/報告文檔**（ai-analysis 分析文）→ consistency 鏈。判準定義引用 execution-plan docs mode 單一源（同步修訂其觸發判準）
2. implement:273 修文：「小型變更」以規模判準（bug fix/單檔小 tweak）；純 refactor 不再與情境 C 劃等號——情境 C 只跳 5a Capabilities/Kanban 結算，5b 依規模（大型/中型）照跑；**guide 變更規模分級表補「純 refactor」對應列**（「依規模照跑」需判準來源——目前表無 refactor 行）
3. metadata-sync:43 architecture.md 觸發脫離情境欄——內容條件（涉及設計決策/模組結構/新抽象層）即可觸發，任何情境（吸收註記：ai-rules 本 repo 無 architecture.md——此項服務消費端 repo；ai-rules 側實害面在 5b instruction 檔同步，由 item 2 承載）
4. simple 路徑 invariant 防線**雙掛**（吸收修訂——多數 simple 修復走裸任務直接實作、不載 execution-plan，掃描掛 EP 護不到主要入口）：①execution-plan 分流段加前置掃描（silent-corruption 清單——§1b:208 定義；命中 → 升 standard〔優先〕或 simple＋輕量 invariant 聲明〔受影響 invariant＋驗證式，3 行內〕）；②**guide always-on 面**——「小型變更」條款納 silent-corruption 例外（碰單位邊界/除權息/時區/會計/風控 → 非 simple，至少附 invariant 聲明）——guide 入本段檔案清單；§1b:210「唯一結構化防線」措辭對齊現實（簡單路徑防線以輕量聲明形態存在）
5. 「結構性修復非 simple」清單（:54-59）與 §1b 觸發（:205-208）的條件重疊段交叉引用對齊（同條件共用，非兩處各表）

**驗證策略**：rg——`僅 \`.md\` 變更` 舊 triage 列 0 殘留；`純 refactor` 於 implement:273 語境已改；`唯一結構化防線` 措辭已對齊；SM-1/5/6 以目標檔現行文本走一遍（文檔語境 rg 命中驗證）；每檔 `/consistency`。

## S4：執行環境前置與重複消除（IM3＋review 去重＋commit message＋PB4）

**Context**：
- **背景**：平行模式 pre-flight 把 isolated worktree 的「先 commit」前置誤套到共享主 worktree（implement:103 vs :107/:320——未經授權 commit 成了執行依賴）；implement 階段 4 review 與 post-build 再 review 的重疊面無證據身份比對；自動鏈中 code-review 提前產 commit message（apply 後即過期）；apply 後受影響驗證證據無失效標記。
- **依賴**：agent1/3 的 review 成本形態實證（findings 重疊度）決定去重強度；agent2 的 CR1 連動（S1 改觸發後 S4 比對邏輯才穩）。
- **語義約束**：去重≠砍審查——跨段整合面、不同 context、高风险第二意見仍全審（codex 建議 #6 但書，已決策採納）；commit message 產生保留於 standalone code-review（便利用途），自動鏈摘除。
- **依賴錨點**：implement/SKILL.md:103（Pre-flight）、:107（Agent 直接寫主 worktree）、:320（禁止未授權 commit）、:77（「build 首個 code commit 的 parent」語義——S2 改結案時點後需對齊）、:157（全量測試）、:224（apply）；agent-workflow/SKILL.md:118-121（isolated worktree 源頭）；post-build/SKILL.md:41-43（階段 1）、:57-60（修正迴圈）、:62（≥3 檔補審）；code-review/SKILL.md:194-217（Commit Message 段）、:32（弧模式動機文字——條件改後同步）
- **成功標準**：共享樹平行派工不再要求先 commit；post-build 有證據身份比對步驟；SM-9（S6）外無新增流程步驟膨脹。

**修改要點**：

1. implement:103 Pre-flight 改「先判 execution environment：Agent 直接寫主 worktree（共享樹）→ uncommitted 變更可見、不需 commit；isolated worktree spawn → dependency transfer（已授權 commit 或明確快照）」——引用 agent-workflow:118-121 源頭語義
2. post-build 階段 1 前加「證據身份比對」：implement 階段 4 review 已覆蓋**同範圍＋同內容 revision＋同審查 profile** 三者等價 → 只補 delta（修正迴圈 diff＋跨段整合面）；任一不等價或**比對鍵缺席**（implement 階段 4 findings 走 context 未落帳本——跨 session 必然）→ **fallback＝全審**（明文接線——防 delta-only 永不觸發或誤砍 fresh-eyes）；比對鍵＝S1 帳本 header identity（S1×S4 接線）。吸收註記：agent1 實測 implement→post-build 完整鏈從未一體跑過——本機制主場景是同 session 連續弧與 standalone 鏈的重複審收斂，非 pipeline 常態
3. 自動鏈（post-build 編排場景）code-review 不產 commit message——code-review:194 段加「跨命令自動化場景略過（apply 後即過期；最終命名屬 /commit）」
4. PB4：post-build 修正迴圈 apply 後——受影響驗證證據標過期、按變更風險重跑（組合命令形態，非全量無差別）

**驗證策略**：rg——`有 uncommitted changes 是 Agent dependency` 0 殘留；`證據身份比對`（或吸收後定名）在 post-build 在場；code-review commit message 段有自動鏈豁免語句；每檔 `/consistency`。

## S5：bridge 直跑範式＋resume 鏈＋工單驗證式要素固化（反饋①＋③工單側）

**Context**：
- **背景**：MOS-74 全弧（muse review → GLM judge → 修正 → muse 同 session resume followup pass 6/6）實證——bridge task 直跑嚴格更優（主 session 背景 Bash＋stdout 重導；856s/442s 實證；timeout 約束從未存在）；舊「agent 轉發＋兩段式收法」是誤判約束的多餘間接層，memory 活配方已改寫（mosaic 側），ai-rules 側待固化。
- **已決策（handoff 勿重辯）**：直跑 vs 轉發已定案；resume 鏈分工比例實測有效；跨專案分層——操作事實留 memory、機制性知識進 ai-rules。
- **依賴**：S1 帳本模型（muse 續接段帳本指向對齊）；`references/muse-bridge-recipe.md`（S0 搬入的 patch 參考文本）。
- **語義約束**：「兩段式」一詞 drift 險——agent 轉發時代「兩段式收法」（exec id≠job id ledger 考古）與現行「背景 Bash 掛 wait 兩段」（提交→wait）同詞異義；固化時舊義標退役、現行形態換明確詞（如「wait 收法」），不留歧義。delegate-rescue agent（plugin 側 thin wrapper）不在本 EP 處置範圍——僅作 S6 案例素材。
- **依賴錨點**：model-routing/SKILL.md:184-204（完成回報收法——item 1 標題「簡單轉發」仍轉發措辭、內容已直跑）、:162-180（session 定向接續——機制在場、鏈形態缺）、:149（thin forwarder 治理引用——codex R5）、:206-214（transport 三態判定——wrapper 措辭，codex R5）；followup-review/SKILL.md:53-62（muse 續接驗收——:53 掛「未實戰，首跑後回報修訂」，MOS-74 即首跑實證）；work-order.md（review 工單要素段——:45 附近）；bridge script `~/.zcode/cli/plugins/cache/muse-market/muse/0.2.6/scripts/muse-bridge.mjs:767`（--session-id 解析，引用時以 plugin cache 現版為準）；**MOS-74 一手實測＝session `sess_8a20c5bd` 後半**（user 指供）——命令形態／sessionId 取法／followup 工單形態（heredoc＋逐條清單＋豁免標註＝裁決非遺漏＋驗證式複驗要求）／verdict 附實際命令輸出節錄
- **成功標準**：SM-8 可驗；model-routing 無 agent 轉發殘留敘述。

**修改要點**：

1. model-routing 收法決策樓 item 1 改名去「轉發」措辭（內容已是直跑）；全段掃 agent 轉發形態殘留（`rg "agent 轉發|spawn prompt 給絕對路徑"`）——歷史實證段（item 3）保留但明標「已退役形態，僅供考古」
2. resume 鏈形態記載：model-routing「session 定向接續」節補審查工作流鏈形態（review 工單預告驗證式 → judge → 修正 → `--session-id` 同 session followup——reviewer 帶自己 findings context 複驗，優於 fresh context）；followup-review:53-62 「未實戰」標記改 MOS-74 實證（session `01a082f3-…`／job `mtt7fkm0`／pass 6/6＋2 新 issue）——語義升級為已驗證形態
3. work-order.md review 工單要素固化：「findings 每條附可機械複驗的驗證式（rg 命令/pytest case）」為 external reviewer 工單標準要求（本次 followup 零摩擦關鍵單點）；review-engine 契約**由 S1 唯一擁有**（codex R4）——本段僅消費驗證同詞（rg 對照），不寫入
4. **外部 runtime 承載者明文**（user 裁定＋AIR-46/MOS-74 兩弧實證）：model-routing 派發側（:42 審查類段／reviewer 交接契約）明文「外部 runtime 委派的承載者＝caller 背景 Bash process（run_in_background＋stdout 重導），**禁 subagent wrapper 承載**——外部 runtime 不佔 in-harness agent slot／rate limit（wrapper 唯一『價值』是被誤判的 600s timeout 約束）」；收法 item 1 標題「簡單轉發」改「簡單直跑」；dual-family 鏈 judge 層顯性引用三防線#2 全採納自查（AIR-46 實證零否決×2 未觸發）
5. **transport 恢復分支同步**（codex R5）：model-routing「transport 三態判定」表（:206-214——「wrapper 已收」「wrapper 空轉…TaskStop wrapper」）與 :149 thin forwarder 治理引用——直跑化後恢復動作改以 **caller 背景 Bash process／bridge job** 主體表述（`TaskStop wrapper` → 殺背景 Bash job／bridge `stop`）；歷史敘述可留但**不得擔任現行恢復程序**；驗證掃描組加 `wrapper|thin forwarder|TaskStop` 逐命中分類（現行程序零依賴；歷史／禁令用途不要求零命中）

**驗證策略**：rg——`agent 轉發` 於 model-routing 僅存於標記退役的歷史段；`驗證式` 於 work-order/review-engine/workflow-review-pattern 三處同詞；`未實戰` 於 followup-review 0 殘留；每檔 `/consistency`。

## S6：tool-discipline 背景跑通則（反饋②）

**Context**：
- **背景**：三層反模式（誤判約束→解法固化→工具強化慣例）真實案例——以為 Bash 只能 600s（實際 run_in_background 從頭可用）→ 為繞誤判約束產生 agent 轉發形態沉澱 memory → delegate-rescue wrapper 存在讓形態顯得官方。成本：agent 開銷＋間接層＋收斂路徑變長；無人回頭問「原約束還在嗎」。
- **依賴**：無（檔案獨立——rules/tool-discipline.md）。
- **語義約束**：通則放「背景執行」節（:50-52 現行）；案例帶「真實案例」marker（instruction-writing 規範）；與 model-routing 收法（S5）不重複——此處只放通則與案例，bridge 細節留 model-routing。
- **依賴錨點**：rules/tool-discipline.md:50-52（背景執行節——pytest 背景跑條款所在）
- **成功標準**：SM-9 可驗。

**修改要點**：「背景執行」節補通則——「長命令（>10 分）背景跑是預設；spawn agent 不是繞 Bash timeout 的手段（它從不是必要手段——約束誤判實證）」＋三層反模式案例（真實案例 marker：2026-09 bridge 轉發形態）。部署面：rules/ 變更走 bundle 同步（sync-sources / deploy_agents 紀律）。

**驗證策略**：rg 通則條款在場；`/sync-sources` bundle 新鮮度檢查過（rules/ → 非 Claude 部署 bundle）。

## S7：tour_validate 中文目錄 bug——重現實測不重現，降級結案（反饋④）

**Context**：`code-reality tour_validate` 對中文目錄（`01-資料讀取三路徑/01.tour`）疑似零匹配——`--tours-dir` 顯式亦炸；mosaic 側靠手修 callstack 錨繞過（09-08 登記、09-09 重申）。修復屬 code-reality repo（Rust carrier，獨立 repo）——**本 EP 不跨 repo 寫入**（collaboration-constraints：跨 repo 寫入是 spawn 端/user 決策）。
- **依賴**：S0 的重現實證（`references/tour-validate-repro.md`）。
- **重現結果（09-09 實測）：不重現**——現行 code-reality 對 mosaic repo（含中文目錄 `.tours/arch/資料組裝與擴充/`）掃描正常（205 tours；`--manifest` 與 `--tours-dir .tours/arch` 兩形態同結果）；17 fails 全為真錨債（`future_labels.py` 已刪檔 stale 錨——mosaic 側 corpus 債，非工具 bug）。
- **修改要點**（吸收修訂——降級結案）：①反饋④以「不重現證據」結案——repro 紀錄留 `references/` 供 code-reality 版本史對照（09-08 症狀可能後續版本已修或原環境相依；重現僅驗證文件化 `--repo` 形態）；②post-build 已知限制註記**取消**（無可註記的 bug）；③mosaic 側 17 錨債不在本弧（其 post-build 修復閉環範圍）。
- **驗證**：repro 紀錄在場＋進度節結案標記。

## S8：delegate-bridge 設計修訂——agent wrapper 層退役（跨 repo 工單；arch-thinking 產出）

**Context**：arch-thinking 三視角結論（進度節 09-09 分析）——bridge CLI 本身無錯（ledger 必經正確），錯在 plugin 附帶的 `delegate-rescue` thin wrapper agent：adapter-over-adapter、幽靈 context（有邊界無職責）、存在即官方感（工具強化慣例第三層實證——AIR-46 msg 118 定案同向）。delegate-bridge repo（`~/Github/delegate-bridge`，獨立 repo）——**本 EP 不跨 repo 寫入**，產出修訂工單。

- **依賴**：S5 承載者明文（措辭對齊）；arch-thinking 分析結論（進度節）。
- **修改要點**（ai-rules 側動作）：①產出 bridge repo 修訂工單 `references/delegate-bridge-redesign.md`：`delegate-rescue` agent 退役（定義移除或標 deprecated＋遷移說明：背景 Bash 直呼形態）、docs 明示承載形態（caller harness 背景 process 機制）、`--session-id` resume 鏈形態記載（MOS-74＋AIR-46 兩弧實證）②S5 的承載者條款與 bridge docs 同詞對齊
- **驗證**：工單在場；bridge 側落地後 plugin agent 清單不再出現 delegate-rescue（本弧外驗收）

## S9：AIR-48 剩餘吸收——P4 dogfood 收尾＋統一定義表 wrapper 條目＋P5 裁決點（C 線）

**Context**：user 09-09 裁定 AIR-48＋AIR-50 同一整合弧。AIR-48 已完成 P1（誤置 taxonomy——任務家 p1-taxonomy.md）、P2（統一定義表 v1——memory-audit SKILL「載體統一定義表」節，九載體交叉表＋誤置→處置）、P3（memory index B 形態上線）、P5（catalog 探針＋writer 歸因建議）；剩餘＝P4 dogfood（窗口 48h 至 09-10、case#1 已記、n=1/3-5）＋P5 三 user 裁決點＋結案。本弧新增素材：agent wrapper 誤用（S5/S8 主題）正是定義表域的新條目。

- **依賴**：S5/S8（wrapper 分析結論與定義表條目同詞）；AIR-48 任務家 `ai-analysis/_tasks/09-08-carrier-misuse-definition/`（P4 dogfood 記錄與 p5 提案在場——本段消費不重建）。
- **語義約束**：定義表是 memory-audit SKILL 單一源——S9 只加條目不改表結構；dogfood 回餵走定義表的「誤置→處置」欄位慣例。
- **修改要點**：①P4 dogfood 收尾——補收 case 至 n=3-5 或窗口到期（09-10）以已收結案，**不定格等待**；回餵定義表（誤置→處置修正，附 case 證據）②統一定義表補「外部 runtime 委派承載」條目：正確載體＝caller 背景 Bash process（與 S5 承載者明文同詞）；agent wrapper 承載＝誤置（AIR-46 msg 118＋MOS-74 實證；處置＝直跑）③P5 三 user 裁決點彙整進收尾報告供 user 裁決（telemetry last-writer 投影建議案）④AIR-48 結案兩步隨本弧收斂後時點（同 S2 契約）
- **驗證**：dogfood 記錄（n＋回餵差異）在場；`rg "wrapper" skills/memory-audit/SKILL.md` 命中新條目；AIR-48 卡 Done 隨本弧收尾。

## S10：review agent 層 lite 化（user 09-09 裁定——ep-review／code-review 審查 agents 預設 lite）

**Context**：本弧四輪審查的實證——findings **生產層**跨家族/跨層品質皆高（glm-5.3 code-reviewer、codex、muse、flash 系考察各有斬獲），判斷密集價值集中在 judge **裁決層**（主 session）。現狀三處不一致：model-routing skill:42 已 09-07 放寬「審查類可用 glm-5.3-flash」，但 ①措辭是「皆可」非預設 ②`rules/model-routing.md` 骨架仍寫「full 為基準（registry 釘 glm-5.3——AIR-43）」——rule↔skill drift ③registry pins 仍 glm-5.3。user 09-09 裁定收斂：**審查 agent 預設 lite**。

- **依賴**：與 S5 共檔 model-routing（bridge 段 vs tier 段——同檔序列化，見整合策略）；`agents/zcode/` 為生成檔（sync_agents 產出）不手改。
- **修改要點**：
  1. model-routing skill :42 強化：「review agent 層（ep-review／code-review 的審查 agents）**預設 lite（glm-5.3-flash）**；升 full 條件＝高保護面／跨邊界語義面（保護面厚度概念反轉為升級觸發）；**judge 裁決／EP 規劃層不變（full 主 session，AIR-24）**；跨家族第二意見仍 muse 優先」
  2. `rules/model-routing.md` 角色→tier 表 code-reviewer row 對齊（「full 為基準＋條件式降 lite」→「**lite 預設（user 09-09）＋條件式升 full**」——兼修 rule↔skill 既有 drift）
  3. registry pins：tier×provider 權威表（skill）改後跑 `scripts/sync_agents.py` 重生成 `agents/zcode/`（code-reviewer／code-reviewer-primed → `glm-5.3-flash`）；claude 側 spawn-time 分層同步；**agents/roles/ 標籤隨 pins 同步**（code-reviewer(-primed) description `〔tier: full〕`→`〔tier: lite〕`——09-09 subagent-model-routing-fix 弧引入的靜態標籤，pins 翻轉後不同步＝spawn 選單顯示 full、實際 wire flash；judge P1——該弧 dual-context 審查抓到的協調洞，S10 item 4 原「roles 引用不變」作廢）＋regen
  4. ep-review／code-review skills：spawn 指引註記 lite 載體——ep-review 現指定 `Explore`（內建型別**繼承主模型**，見 memory `reference-zcode-agent-model-inheritance`）→ 改為 registry 唯讀 lite 載體（lite-verify 等——read-only 契約＋flash pin 雙確定性）；code-review 模式 B 的 `agents/roles/` 引用不變（roles 定義層不綁 model——model 綁定走 pins 與 tier 標籤，見 item 3）；**skill:40 補 rule 同款「設定頁可為內建單獨釘模型、清空恢復繼承」例外細節**（judge P2——rule 單側，S10 動 tier 段順手補）
- **驗證**：`rg "^model:" agents/zcode/code-reviewer*.md` → `glm-5.3-flash`；rule 與 skill 同詞（`rg "lite 預設" rules/model-routing.md skills/model-routing/SKILL.md` 兩處命中）；sync_agents 重跑冪等；SM-17。

## S11：rename 反掃 instruction 檔——post-build metadata-sync 機械步驟（mosaic 反饋⑤）

**Context**：mosaic 09-09 一致性地毯掃描（三 agents＋主 session 抽驗 12/12 屬實）量化證據——44 AGENTS.md ~1173 條引用平時僅 7 失效（基礎不漂），但 **5/8 條 P1+P2 全部源自兩個 rename/move 型 EP 結案後文檔未同步**（`TW_STOCK_REGIME`→`TW_STOCK_ANALYSIS`、`_to_pandas` 下沉等）；自述「快 drift」的藍圖檔靠人工記憶更新＝會漏的那層。根因：rename 知識只活在 EP 段落，結案流程無「拿舊符號名反掃文檔」動作。**主 session 抽驗屬實**：`TW_STOCK_REGIME` 現仍殘留於 mosaic `venues/tw/AGENTS.md`＋`callstack/condition-rendering-tags.md`（正是兩 EP 之後漂的）。證據 durable 化：`references/consistency-sweep/`（4 檔）。

- **依賴**：post-build 共檔（加入序列化）；與 code-review「架構文檔 ripple 提醒」互補（提醒＝review 期 flag；本步＝結案 gate 機械收口）。
- **修改要點**：post-build 階段 4 metadata-sync 段補機械步驟——①**rename 清單萃取**：弧 diff 萃取 rename/move/retire 舊符號（檔級 rename 用 `git diff --diff-filter=R -M`；符號級由 LLM 讀 diff 提取——弧內 diff 便宜）②**反掃**：`rg "<舊符號>"` 掃 AGENTS.md 家族（`fd -g AGENTS.md`）＋專案快 drift 檔（參數化——各 repo 藍圖層慣例不同，由專案 AGENTS.md 宣稱或 EP 攜帶清單）③**處置**：命中即修（新錨點）或顯式記 drift；零命中＝步驟完成證據。**不做全檔重驗**（成本與弧大小成正比——A 軸證明基礎命中率高，平時不漂）。非 rename/move/retire 弧＝步驟自然空跳（清單空）
- **驗證**：SM-18；rg post-build 反掃條款在場；實證錨——mosaic `TW_STOCK_REGIME` 殘留（修法落地後該類弧結案會命中）。

## S12：派工／查證三修補（user 09-09 裁定——當日四事故的規則面收口）

**Context**：general-purpose 誤派 ×2（最大洞已由 AIR-51 補）、muse effort 口語誤讀（表在場未查）、standup 誤刪（刪除查證清單缺 backlog 卡面）——三個一行級修補。

- **依賴**：model-routing 加入共檔序列鏈尾（S5 bridge 段→S10 tier 段→**S12 派發段**）；rules/collaboration-constraints.md 無共檔。
- **修改要點**：
  1. `rules/collaboration-constraints.md`「破壞性選擇的查證觸發」清單補：「**backlog 卡（To Do／In Progress／drafts）是否提及或依賴**」——standup 事故：恢復事實只記在 AIR-52 desc，原清單不含卡面
  2. `skills/model-routing/SKILL.md` 派發段補 **bridge echo**：「派 bridge 工單必印 `[Bridge] family=<f> model=<m> effort=<e>`」——與 in-harness「spawn 前印確認 `[Agent] model=…`」對稱（muse effort=medium 事故若印出，出發前即被肉眼攔）
  3. 同檔補**口語正規化**：「user 對話中的模型／檔位詞（flash／max…）不是值——派發前經 family 表正規化；非表內詞＝查表觸發訊號，禁猜測直接套用」（flash 對 muse 非合法 effort 值，本身就是該查表的訊號）
- **驗證**：三條款 rg 在場；SM-19。

## 整合策略

- **執行序**：S0（gate，已完成）→ S7（已降級結案）→〔S1→S2→S3→S4→S11 序列（S11 排 S4 後——post-build 共檔鏈收尾）；S6、S8、S9、S10、S12 與 A 線平行——S9 的定義表條目待 S5 承載者明文定稿後落〕→ 收尾。**共檔序列化（codex R4 修正＋S10/S11 增補）**：`post-build` 共檔鏈 S1→S2→S3→S11 依序動；`followup-review` 與 `review-engine` 兩檔的 S5 部分均**待 S1 完成後再動**（S1 唯一擁有 review-engine 擴欄、followup-review 帳本措辭；S5 消費驗證同詞）；**`model-routing` 同檔序列：S5（bridge 段）→ S10（tier 段）→ S12（派發段）依序動**；S5 其餘檔案（work-order）與 A 線不重疊；S10 的 rules/model-routing.md／ep-review／code-review／registry 無共檔。
- **全弧 rg 掃描清單**（定義源變更必掃，single-source drift 防護）：`結案兩步`（S2）、`兩段式`（S5）、`agent 轉發`（S5/S6）、`驗證式`（S1/S5 同詞）、`docs mode` 觸發判準（S3）、`uncommitted 空`（S1）、`唯一結構化防線`（S3）。
- **部署面**：ai-development-guide.md（S2）與 rules/tool-discipline.md（S6）變更後跑 `uv run python scripts/deploy_agents.py`＋`/sync-sources`（bundle 新鮮度）；skills/CLAUDE.md 工作流索引 description 同步（收尾）。

## 收尾步驟（docs mode）

1. 受影響命令行為已反映：**本次修改過的每個 skill／rule／_common 檔（依 UC 盤點 product 面自舉——含 S8/S9 新增面與 F1 五消費端）**，其行為描述與 skills/CLAUDE.md 工作流索引一致（description 欄同步）——不寫死計數（清單隨吸收修訂成長，muse M-F1）
2. `/consistency` 逐檔（本次修改過的每個導航/契約檔）
3. `/sync-sources` 機械 invariants 全綠（含 `skill_allowlist_coverage`——若 skill 檔名未變則被掃項不變）
4. guide 部署同步（deploy_agents.py）＋抽驗 `~/.zcode/AGENTS.md` bundle 已含 S2/S6 變更
5. post-build docs-mode 弧自食（SM-1 場景——本弧自己就是控制面 .md 變更，收尾鏈依修後 triage 走 docs-profile review）
6. EP 歸檔（done/）＋**AIR-50 與 AIR-48 結案兩步**（同弧收斂後時點）＋弧結案蒸餾（`project_codex-skills-arch-review-0909` 蒸終態）——時點依修後契約（收斂後）

## EP Review Findings（兩輪獨立審查——GLM in-pipeline〔F1-F6〕＋codex 跨家族〔R1-R5〕；報告 `.agent-tmp/dryrun/ep-review-primed.md`＋`codex-ep-review-findings.md`）

| ID | 嚴重度 | 位置 | 問題 | 決策 | 處置 |
|----|--------|------|------|------|------|
| F1 | 🟡 important | S2 檔案清單 | 漏列 5 個結案時點消費端（flow-review:59／skills/CLAUDE.md:56-57／blueprint-bootstrap:29／maintain:127／context-management:39） | ✅ | 錨點與檔案清單補列 |
| F2 | 🟡 important | S1 弧模式 | debrief:25 第四消費端漏列 | ✅ | S1 item 3＋錨點＋驗證範圍補 |
| F3 | 🟡 important | S2 執行鏈 | 收斂後結案呼叫鏈未閉合（metadata-sync 觸發者缺 post-build hook 2；post-build 正文無結案步驟） | ✅ | S2 新增 item 8 |
| F4 | 🟡 important | 卡 desc | 已決策④（路徑判）⑩（移交）與 EP 修訂漂移 | ✅ | 卡 desc 回寫（語義判準／降級結案） |
| F5 | 💡 suggestion | S1/S5 | 驗證式同詞清單不一致（S1 漏 review-engine、S5 漏 code-review） | ✅ | 統一四檔清單 |
| F6 | 💡 suggestion | S2 | 5a 寫 Capabilities ✅（Built）與「✅＝已完成」放置原則張力 | ⚠️→定 | 預設維持 5a 寫入＋「情境 A＝Built（🟡）」措辭；正式完成宣稱＝結案兩步（S2 item 8） |
| R1 | 🟡 important | S1 identity | `git diff HEAD` digest 漏 untracked——untracked-only WIP 改變假吻合（以本 EP 零寫入實證） | ✅ | identity 改 tracked hash＋untracked 清單/content hash（work-order §3 同詞）＋SM-11 |
| R2 | 🟡 important | S2 雙發布防護 | open=0 ≠收斂（adopted/implemented 未完成仍在）；fallback 已發布無去重；缺帳本無分支 | ✅ | 拆收斂檢查／發布去重／缺帳本明確分支＋SM-12/13 |
| R3 | 🟡 important | S3 語義約束 | 同段殘留舊路徑式判準（路徑枚舉）與語義判準並存——兩種 triage 指令 | ✅ | 語義約束行改語義判準（路徑＝hint）＋SM-1 checkpoint 同步 |
| R4 | 🟡 important | S1/S5 共檔 | review-engine 兩段共寫、平行策略漏列 | ✅ | S1 唯一 owner；S5 消費＋整合策略/UC 表序列化 |
| R5 | 🟡 important | S5 transport 恢復 | 三態表/thin forwarder 治理仍以 wrapper 為恢復主體 | ✅ | S5 item 5：恢復動作改 caller process/job 主體＋掃描分類＋SM-14 |
| M-F1 | 🟡 important | UC 表＋收尾 | product 面表止於 S7——S8/S9（user 裁定 C 線）缺席＝可被略過；收尾計數過時 | ✅（muse 輪） | 補 S8/S9 行＋S7 行降級更新＋收尾改自舉措辭 |
| M-S1 | 💡 suggestion | S3 快道 | 「純修飾」producer 自判無背書——MUST→SHOULD 反例＝PB1 經快道復活 | ✅（muse 輪） | 快道加模態詞機械排除（詞表單一源）＋掃描組 |
| M-R3R | 💡 suggestion | Findings 史表 | R3 行逐字引用舊約束——絆倒 0-hits 機械門 | ✅（muse 輪） | 史行改述避開 banned bigram |
| M-F5 | 💡 suggestion | Scenario Matrix | 缺兩條 happy path（正常結案全發布／三鍵等價 delta-only） | ✅（muse 輪） | 補 SM-15/16 |
| N-1 | 💡 suggestion | S3 快道詞表 | 詞表漏單字「禁」——repo 禁令主力形態（禁掛/禁改/禁寫）放行 | ✅（followup 腿） | 詞表加「禁（單字）」 |
| N-2 | 💡 suggestion | SM-15 checkpoint | 「流程可走一遍」非機械 | ✅（followup 腿） | checkpoint 改機械斷言（卡 status/歸檔/Capabilities 三查） |
| D-A1 | 🟡 important | UC product 表 | 表缺 F1 五消費端＋debrief＋commit——收尾自舉源不完整 | ✅（codex delta 輪） | 表補齊＋「表×各段修改要點聯集」規則明文 |
| D-A2 | 💡 suggestion | SM-15 checkpoint | 三查未覆蓋 references 新址與 SM 升級（可機械 ≠ 覆蓋完整） | ✅（codex delta 輪） | 補兩查（ref 新址＋SM 狀態） |
| D-B1 | 💡 suggestion | 殼 s1 敘事 | 「三輪全量審」失真（resume 腿非全量） | ✅（codex delta 輪） | 改「兩次全量＋一次 resume」 |
| D-B2 | 💡 suggestion | 殼 degraded 槽 | 指向不存在的「同目錄 html-mode 檔」＋裝法細節越界（內容篩選通則） | ✅（codex delta 輪） | 移除裝法句 |

## 進度結算（段落完成時更新）

（段落完成 → 標 ✅＋一句驗證證據；段落失敗 → 記錄＋阻止依賴段）

- 〔09-09〕S6 ✅（muse B 線 job-mttjod8d：tool-discipline 背景跑通則＋3 層反模式案例，git diff 對帳＋4 行無 scope creep）／S8 ✅（同 job：`references/delegate-bridge-redesign.md` 工單新檔，三骨架在場）
- 〔09-09〕S1 ✅（9 檔：rg 殘留三式 `不作為決策落點`／`uncommitted 空`／`跨 session 不保留` 0 hits；`驗證式` 在 pattern／code-review／review-engine 同詞在場〔work-order 待 S5〕；帳本 caller-指定六處同語義）
- 〔09-09〕S2 ✅（11 檔：情境 A 拆 Built（5a）／final（收斂後）兩動＋metadata-sync 三 mode＋雙發布防護六件＋hook 2 結案段；掃描組 `結案兩步|5a 結算|--final-summary` 全 repo 逐命中時點一致〔agents/ 零命中；maintain／blueprint／context-management 無時點衝突免動〕；`deploy_agents.py` 3/3 綠；illustrate 掛點表 badge 行同步 🟡）
- 〔09-09〕S3 ✅（5 檔：triage 語義判準＋純修飾快道〔模態詞表單一源〕；docs-mode「行為控制面」單一源＋同詞引用；情境 C 去 refactor 化〔:253＋:273〕；architecture.md 脫情境欄；simple 前置掃描雙掛〔EP 分流段＋guide always-on 例外〕＋§1b 交叉引用；`僅 .md 變更` 0 殘留；deploy 3/3 綠）
- 〔09-09〕S4 ✅（3 檔：pre-flight 先判環境〔共享樹免 commit〕；階段 1 前證據身份比對〔三等價＋fallback 全審〕；自動鏈 commit message 豁免＋弧動機文字同步；修正迴圈 PB4 證據過期標記；baseline 語義對齊；`有 uncommitted changes 是 Agent dependency` 0 殘留）
- 〔09-09〕post-build 中段 checkpoint（S1–S4）收斂：triage＝控制面 docs-mode 全鏈；Resume 不適用（.review/main.md 屬 AIR-49）；證據比對＝fallback 全審；自審 F1–F5＋獨立 reviewer R-F1–R-F4 全修全驗（帳本 `.review/air-50.md`，無殘留）；結案段＋hook 2 跳過（S5＋未做，S2 收斂後規則）；tour 無變動跳過；metadata-sync 結案段跳過；無 commit
- 〔09-09〕S5 ✅（3 檔：直跑改名＋wait 收法＋退役標＋transport caller 主體＋承載者硬性＋judge 三防線#2＋resume 鏈形態；followup 去未實戰；work-order 驗證式入 findings schema；`agent 轉發` 0 殘留；驗證式三處同詞；備註：EP 點名 session/job ID 與 recipe 對不上〔01a082f3 實為 codex 複審 session〕，未驗證不引用，實質照 recipe 寫）
- 〔09-09〕S10 ✅（6 檔＋生成 4 檔：分配表 full 列清空＋script dict 同步＋roles 標籤 lite＋rule/skill lite 預設同詞＋ep-review 三處改 registry lite-verify；sync 重生成冪等，zcode pins＝glm-5.3-flash；SM-17）
- 〔09-09〕S12 ✅（2 檔三條款：查證清單加 backlog 卡面＋bridge echo＋口語正規化；SM-19 走一遍成立）
- 〔09-09〕S9 ✅（2 檔：P4 記 case#2〔本 session 真實軌跡＋ID 引用核對失敗事件〕n=2，窗口至 09-10 晚不定格等待；定義表加 M5 wrapper 誤置條目；P5 三裁決點彙整待收尾 user 裁決；AIR-48 結案隨本弧收尾）
- 〔09-09〕S11 ✅（1 檔：post-build 階段 4 加 rename 反掃三步〔萃取→AGENTS.md 家族＋快 drift 檔反掃→修或記 drift〕；非 rename 弧空跳；SM-18）
- 〔09-09〕post-build 自食收斂（S5–S12）：delta reviewer Verdict Needs-fix（S10 drift 家族：review-engine:143＋model-routing:222＋agent-review-cycle:50＋agents/AGENTS.md 四處「full 為基準」漏改）→ D-F1–D-F4 全修全驗；parser／管轄／編號／M5 語法 reviewer PASS；帳本 `.review/air-50.md` 三輪無殘留
