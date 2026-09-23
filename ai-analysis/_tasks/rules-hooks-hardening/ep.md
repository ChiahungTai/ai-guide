# Rules 與 hooks 改善計畫

> ep_type: implementation
> 狀態：bounded scope 實作、獨立審查與整合驗證完成；已具備提交／合併條件。實際 landing 以本任務 commit 是否在 main ancestry 判定；外部 bundle 部署未執行。

## 目標與授權

使用者要求詳細分析並改善 rules 與 hooks，以 worktree 修改後合併 main。原話：`詳細分析改善 rules跟hooks裡面的內容，然後用wt 修改後合併到 main`。

Baseline：`3b3448aa`。獨立 worktree：`/Users/ctai/Github/ai-guide-rules-hooks`；branch：`codex/rules-hooks`。primary 保持 main；既有 deep-work 修改與 AIR-170 worktree 不屬本弧。

## Use cases 與 invariant

- Agent 讀到規範後，能以實際 harness 能力執行，規範不可要求不存在的參數或讓 authoring 先於落地審查。
- Hook 接收真實事件 JSON，依既有 policy 準確 allow／deny／advisory；不因普通合法輸入誤攔，也不把旁錄或內部錯誤冒充驗收。
- hook runtime 維持部署端 Python 3.9 相容；repo 測試使用 uv。既有 payload/output contract 不任意擴張。
- 不弱化使用者授權、獨立審查、memory 寫入或 canonical 控制面隔離邊界。
- 修改只能在本 WT；main 落地前完成 boundary fresh＋intent 分離審查及跨家族意見，judge 收斂後才 commit／merge。

## 分析方法與責任

主 session 負責規劃、證據裁決、整合驗證與 merge。native 獨立 context 分別掃 rules 文義與 hooks 行為；實作另派 worker。外審使用 delegate bridge Muse，availability snapshot 顯示可用，但需實際 dispatch 驗證。

風險 profile：boundary。instruction owner：rules/AGENTS.md、hooks/AGENTS.md；測試對應現存 tests。只修有來源或可重現證據的問題；比較維持原狀、刪除與局部修正，不全面重造 hook framework。

CR MCP 在場；對選定 hook detect_changes 回 0 symbols，這不足以證明無依賴／無影響。文件與 registration 拓樸走 rg，runtime claim 以 subprocess 測試為準；尚未 index 驗證的關係明列限制。

## 段落

1. 覆蓋盤點：rules 與 hooks 逐檔分類，列出來源、consumer、問題、保留理由、驗證缺口。回收審查 findings 後凍結 bounded scope。
2. 修復：各 worker 使用不重疊 write set；先建立 regression RED，再修為 GREEN。文件改動追查單一源引用；語義變更依 instruction-testing 執行代表情境。
3. 驗證：focused MIN → hook/registration SAMPLE → repo 必要 FULL；系統 Python runtime 實跑修改 hook；bundle dry-run＋引用／語法檢查。純文件的順序／能力宣稱以真實 source 與情境驗證。
4. 獨立驗收：fresh source/diff review、intent 對照與 external Muse review；主 session 逐條 judge，重要 findings 修正後複驗。final receipt 四欄齊備。
5. 收線：具名 stage、commit、確認 main 並行變更、必要 rebase＋ff-only merge；驗 main 包含成果且 unrelated dirty file 保留。工作樹確認無交付遺漏後移除 WT 與已合併 branch。

## 初始證據

- `uv run pytest tests/test_hooks.py tests/test_codex_memory_path_deny.py tests/test_marshal_admission_guard.py -q`：86 passed。
- 主 repo core.hooksPath=`.githooks`；隔離 authoring 使用非 canonical WT。
- 發現待核對：rules/AGENTS.md「改 rule 後即 deploy」與 instruction-writing prelanding review 的順序衝突；hooks/AGENTS.md 有已不在 registration 的 legacy plugin 維護敘述。

## 進度與接續

**最終結算優先於下方歷史檢查點**：H1–H4 與 R1–R5 已完成；native fresh、Muse intent／cross-family、H4 最後複驗均無剩餘阻擋項。接續 task 已核對原 24 檔 SHA-256，並同步 main 至 `5dc662da`；唯一交集 review-engine 的 upstream freshness 一行與本弧修改保留，獨立 integration delta review 通過。全量 1866 passed、2 skipped；完整回執與限制見 [validation.md](validation.md)「最終收斂與接續驗收」。

AUTH: user said "詳細分析改善 rules跟hooks裡面的內容，然後用wt 修改後合併到 main"；接續指定 task：`01a0cb9c-5c76-7011-8044-85df1f3359fd`。授權涵蓋本弧 commit、合併與 worktree 收線；未包含 push 或全域 bundle deploy。

Receipt: classification=boundary／review=native fresh + Muse intent/cross-family + native/Muse H4 followup + native integration delta（validation.md）／session-freshness=fresh（接續 task 核對現行來源及合併後 guidance）／deployment-surfaces=pending（canonical merge 後 symlink 面更新；三端 bundle 僅 dry-run，未部署）。

剩餘收線動作：具名 stage、正常 pre-commit gate、commit、main ff-only merge、驗 ancestry／clean tree，再移除本 WT 與已合併 branch。沒有 running worker 或待回收 review；policy 後續項列於 analysis.md，不列為本弧未閉合 finding。

中間檢查點：baseline 與兩份唯讀分析已回收；Muse 方法論外審 `job-mudcu4e3-e1byn1` completed。三個隔離 writer 正在完成規範與 hook 修正；memory affected suites 244 passed、1 skipped。尚未完成落地審查或 merge。

後續檢查點：docs 16 份完成，native fresh＋delta review 無 findings。完整 suite 在修正 Git fixture 搜尋邊界後 1753 passed、2 skipped；native code fresh review 找出 H4 的 computed mode 與 alias signature 兩項 regression，已採納修復。Muse final intent 發現 Method Coverage 漏修已完成並經 native followup；H4 與末段 docs intent delta 尚待。main 已由並行 AIR-169／AIR-170 前進，新增 hook 不與本弧 write set 重疊；最後將以 task 自有變更隔離 rebase 再驗。

## Scope freeze 與裁決

已接受實作範圍：

- H1：memory_hook_common 的 log override 不可寫入含 MEMORY.md 的池、池內索引／generator／子路徑或指向它們的 symlink；合法外部 log 照常可用。entry attribution 與 log destination 分開判定；default 亦不可成為未驗證 fallback。
- H2：block-memory-index-write 的 Edit 以記憶體 candidate 驗 final description，包含 substring 與 replace_all；body-only 修改不被原有不良 desc 追溯攔截。保持既有膨脹／收斂契約。
- H3：compact-tail-inject 保留超大最新訊息的 UTF-8 尾部、標示截斷；計入 framing／separator／JSON escape 後仍輸出有效 bounded JSON，避免最終 guard 導致整段資訊消失。
- H4：block-python-file-write 在可辨識 Python heredoc 中分清 AST 寫入呼叫與 inert 字串／註解；無法解析時保守維持既有 heuristic，明示此為有限 admission heuristic 而非 shell sandbox。不建完整 shell parser。
- R1：rules/AGENTS 部署順序改成 authoring dry-run、review／授權完成才正式部署；不弱化 landing gate。
- R2：rules/tool-discipline 與 agent-workflow 的背景要求以 carrier 能力表達；native 已非阻塞且無 run_in_background 參數者使用原生回收，不捏造 API。
- R3：review-engine 刪除 zero-hit=死碼確認、LSP 覆蓋動態引用的錯誤宣稱；查詢路由回引用 symbol-query-routing 單一源，保留證據範圍與自我否證。
- R4：hooks/AGENTS 同步實際註冊與 Python runtime、sensor log 安全及 compact 邊界，移除目前 registration 不含的 plugin cache／grok 操作指示。
- R5（final review 前 amendment）：design-thinking 的 POC 清理時點引用 must-execute 唯一源；rules-reminder 與 agent-workflow 的 Claude Bash 特有限制補 carrier 條件；python-standards 的 NaN 比較敘述以隔離 probe 校正。皆為已有對照源的局部修正，不改授權或風險 profile。
- R3 的必要引用閉合：instruction-writing 導航-B、review-engine/code-quality-profile、symbol-query-routing、audit-test、debugging-and-error-recovery 同一查詢能力宣稱同步；移除「LSP 100% 涵蓋 runtime 動態引用」及固定 LSP-first 的第二份路由。agents/AGENTS 的 grok 安裝指針不再依賴已移除的 hook 歷史敘述。這些僅同步既有定義，不改模型、review profile 或安裝政策。

主 session 接受上述 scope 為執行契約；worker 僅在指定 write set 修改。使用者新增指示：繼續，已換帳號，額度夠，好好做。

未接受的擴張：依 diff 行數降審查級別、任意刪除審查 SLA、arch-thinking 只抽樣 1–2 路徑、引入新 exemption checker、全面重寫 instruction framework。Muse F1/F2/F3 的成本／試行條款問題留報告評估；F4/F5 的「小 diff 即可減審」缺少失敗機制證據，不採。F6 已由本 scope、下方驗證與既有收線步驟補齊。

## 可觀察驗證情境

- H1：MEMORY.md、_inventory.md、_generate_index.py、nested path、symlink 全不被 append／rotate；外部 JSONL 正常追加。
- H2：超長／hash／date／session desc 的 partial Edit 拒絕；body-only、合法 desc、縮小條目允許；replace_all 使用真正 candidate。
- H3：超長 ASCII／CJK／大量需 JSON escape 文字仍有最新尾部；一般多訊息順序、上代 marker 過濾、STATE 與最終 bytes 上限不退化。
- H4：真 write_text／write_bytes／open 寫入呼叫拒絕，純字串／註解／print 範例允許；外部 shell 與不同 heredoc 不誤歸 Python。
- R1/R2/R3：instruction application probe 使用 native fresh contexts；舊版与新版除 guidance 外保持情境一致，檢查部署前實際決策、無參數 spawn 選擇與 zero-hit 刪除決策。若 baseline 本就選對，記「未觀察到行為回歸」而非製造 RED 或宣稱提升成功率。已跑 zero-hit control，選擇正確保留並查 registry；文字矛盾仍由逐句證據成立。
- 若外審失敗／無容量：在本 EP 記 no-candidate pending、保留 WT 與 findings、merge blocked；不當作正常完成。
- Merge 前重新核對 main 與 branch baseline，若 main 前進先確認交疊再 rebase，補驗整合差異；不以開場快照替代最後檢查。

## 外審回收紀錄

Muse 使用 repository dev binary（合法 caller surface）。bridge_waiter 因該 binary 不提供版本而 exit 2，沒有重試或重派 job；改用原生 wait 收件。原生 wait 一次 exit 124 只代表仍執行；後續 show 確認 completed 且 finalText 非空。此 adapter 限制屬外部工具，未擅改。
