# Rules、hooks 與方法論品質分析

狀態：分析與本弧修復驗收完成。基線 `3b3448aa`；最後驗證結果與落地判準見同目錄 EP 的最終結算及 validation.md。政策後續項保留，不等同本弧已修復。

## 結論

現況的主要問題是「宣稱與執行不一致」，不是規範太少。hook 有明確責任與既有 regression suite，但部分 predicate 檢查了錯誤對象；rules 中有跨 harness 的假設外推、部署先後順序衝突；用來審查它們的 skill 也含相互矛盾的查證指示。因此本次以修復實際錯誤、縮減重複權威與準確描述能力邊界為主，不增加一套 hook framework，也不把遵循 skill 當作品質證明。

最初 focused suite 為 86 passed，仍能重現以下缺陷。這說明既有綠燈只覆蓋原先案例，不能替未驗輸入或 consumer 行為背書。

## Hook 的具體缺陷與選擇

| 問題 | 基線來源 | 可觀察失敗 | 採用方案與理由 |
|---|---|---|---|
| log 寫入位置誤判 | hooks/memory_hook_common.py:52–76 | is_pool_entry 排除索引、底線前綴與非 Markdown 後，log_path 反而接受 MEMORY.md、_inventory.md、_generate_index.py 作 append 目的地 | 分離「需要記錄的 entry」與「允許寫入 log 的位置」。log 與 rotation 都不可碰池內容，合法外部 JSONL 保留 |
| 局部 Edit 漏驗 description | hooks/block-memory-index-write.py:254 | description: SAFE 中只替換 SAFE，new_string 不含 description:，長度、hash、日期、session id gate 全漏 | 依 Edit payload 建記憶體 candidate，檢查修改後 description；body-only 不追溯攔舊 desc，維持既有修復通道 |
| compact 尾段消失 | hooks/compact-tail-inject.py:69 | 最新單筆超過預算就 break，回傳空字串，較早 user request 也消失 | 保留最新 UTF-8 尾片段並明示截斷；同步處理 separators 與 JSON escaping。不能只 continue 跳過最新訊息 |
| heredoc 字串被當寫檔 | hooks/block-python-file-write.py:35 | 唯讀 probe 將 write_text 字樣放在測試字串，hook 對整段 regex 導致實際拒絕 | 可辨識 Python heredoc 用 AST 分辨 inert 字串／註解與呼叫；無法辨識時維持保守 heuristic，避免假装具有完整 shell 語義 |

H1 的 reviewer 重現攔截了 open 目的地，沒有實際污染池；H2/H3 使用 in-memory source/transcript。H4 在 reviewer 的唯讀工具呼叫當下被既有 hook 阻斷。實作驗收另用隔離 filesystem fixture 与 subprocess，不能把這些初查直接當修復完成。

### 保留、不做與間接影響

- 刪除 sensors 會失去既有 attribution evidence；只禁止全部 override 會破壞測試與合法外部收集位置。修正 destination predicate 保留兩項能力。
- 刪除 description gate 會把格式義務全退回 LLM；只增加 regex 分支仍無法涵蓋 substring Edit。candidate 是既有 Edit 的最小 semantic unit，不另造 schema。
- 刪除 compact 注入會失去原文接續；單純提高預算會碰 harness 輸出上限。截斷是必要的資訊損失，必須讓 consumer 看得出來。
- heredoc gate 不能成為完整安全邊界：shell alias、動態 Python、任意 script invocation 仍不在其完整覆蓋面。本次修正已重現的誤攔，不擴張成 sandbox。
- log 判斷可能影響 write/dirty 兩 sensor；Edit 變更同時影響 CC/ZCode；compact-tail 只由 CC 的 compact SessionStart 模板註冊；heredoc gate 的實際觸發仍受各 harness matcher/tool schema 約束。

## Rules 的修復與盤點

| 材料 | 本次判斷 |
|---|---|
| rules/AGENTS.md | 改 rule 即正式 deploy 與落地前審查衝突。authoring 改 dry-run；正式 deploy 留給授權且已通過審查的 canonical revision |
| rules/tool-discipline.md | run_in_background 不能當所有 carrier 的必要參數；目前 native spawn schema 無此鍵且本身非同步。保留非阻塞與回收义務，adapter 決定 API |
| rules/symbol-query-routing.md | 保留 cr-first、freshness 與 zero-hit 限制；修 consumer review-engine 的偏離，不再定義第二份 routing 表 |
| rules/acceptance-evidence.md | 保留獨立證據與 oracle 等級；本次從「綠測試但仍有 bug」驗到其必要性 |
| rules/_ai-behavior-constraints.md | 保留 source/consumer 同步要求；本次規範 drift 正是此要求要防的問題 |
| rules/bridge-dispatch.md | 保留合法 caller surface、唯讀 brief 和 collection。dev binary watcher 版本探測失敗已揭露，採 native wait 收件，不重派 |
| rules/collaboration-constraints.md | 保留實際來源、工作樹主權與並行修改隔離 |
| rules/context-management.md | 保留 checkpoint 與 rule freshness；本次 WT 修改不提前讓 canonical symlink 生效 |
| rules/design-thinking.md | POC「用後即清」與 must-execute 的 commit 後清理有期限歧義；本弧改引用既有清理時點，不批准刪除尚未承接的證據 |
| rules/edit-discipline.md | 保留必要改動、先查 consumers 與不混合矛盾寫法 |
| rules/instruction-writing.md | pointer 本身合理；它指向的 skill 品質須獨立評估，見下節 |
| rules/llm-output-convention.md | 保留 pointer；本次 hook stdout 是 harness protocol，不能混一般 print tag |
| rules/model-routing.md | 保留 authority／qualification 邊界；native inheritance 的精確 model/effort 未回報時不偽造 runtime 證據 |
| rules/modern-cli-preference.md | 保留工具分工 pointer；避免在更多材料複製選型表 |
| rules/must-execute-before-complete.md | 保留實跑要求；hook 必須另外用部署 interpreter 驗，uv 的新版 Python 綠燈不證 Python 3.9 相容 |
| rules/outward-action-consent.md | 本次使用者已明示 WT 修改與合併 main。保留既有授權邊界，不利用本次修法取消 consent |
| rules/python-standards.md | 修正「NaN 任何比較均 False」：有序比較與 == 為 False，!= 為 True；明列 reject predicate 的差別。hook runtime 的例外放 hooks owner，不把 3.12 改寫套到系統 3.9 |
| rules/quality-constraints.md | 保留 consumer-equivalent 機驗、fail-loud 與漸進驗證；區分 advisory hook 與 admission gate 的錯誤行為 |
| rules/bash-hard-rules.md | Claude scope 已明示；本弧修正 rules-reminder 與 agent-workflow 的 carrier scope drift，不改 Claude owner |
| rules/code-edit-constraints.md | 已標 Claude scope；未在本次查得需要改動的行為缺陷 |

「保留」表示本次範圍未取得足夠修改理由，不表示形式完美或已驗證所有 consumer 行為。slash 名稱作語義引用與 UI 能力的混淆另牽涉 deploy purity predicate，留為完整配套後續，避免只改散文而違反實際檢查。

## 三份方法論是否寫得夠水準

品質準據是：能否引導正確且可執行的決策、成本是否對應失敗風險、是否自己遵守單一源與可查證要求。不是要求所有文字越短越好，也不是凡有歷史事故就無限加 gate。

### instruction-writing：核心可用，但機械化精度與證據不相稱

有效部分：隔離 authoring、先分辨 instruction 的作用面、單一 owner、避免跨 harness transclusion 誤用。這些都有可辨識的 consumer／失敗邊界。

不足：

1. static-only 條款（基線 SKILL.md:24）把渲染 byte 等價、NFC word-level Levenshtein、各類排除 token 與模態詞整行判定放進一個 LLM 程序。repo 的 tests/scripts 與此 skill 搜尋未找到相應 checker；這只證明已查範圍缺少工具，不證明外部工具不存在。缺 tokenizer／renderer 契約時，不能宣稱豁免判斷已機械化。保守不豁免能避免誤放，但成本需要另測。
2. Capabilities grammar（基線 :353–367）同時聲明「待 user 拍板」「試行」，又說缺 desc 視為未覆蓋、每層必備四列。試行與全面驗收權威混在一起，是明確的作用域歧義。回查 AIR-45 archived EP:208，當時 user 明確決定 `_cap_` 留試行；instruction-init:96 卻直接要求依此文法產生 Capabilities。已查材料沒有提供正式升格的新決策，不能由 reviewer 自行批准 pilot；應在後續把試行適用範圍與正常生成要求一併釐清。
3. 內容規範仍含形式代理品質（例如 code block 與 table 的全面區別、固定範例長度）。真正應驗的是導航是否準確且不重複；單靠表格形態不能證明 drift，仍需實際 consumer 案例。

取捨：不為了本次快合併而刪除落地審查，也不臨時新增一個 exemption parser。這些更動會重定義整體治理，需以代表案例證明新判準比現狀好。

本弧實際修正的局部項目是導航-B 的「LSP live 且 100% 準確」宣稱；改引用查詢路由 owner，明列 source freshness、coverage 與動態引用限制。上述 static-only／pilot 政策尚未改寫。

### arch-thinking：三者中責任界線較清楚，問題主要在消費方式

有效部分：先問 use case 與 invariant，不以資料夾判 bounded context；觸發才讀 recipe；查 compensation、state ownership；允許局部問題局部處理、工具不足時限制結論。正文 :14 已要求合併命中範圍，:43 已說無關 recipe 不載入，:57–59 分清文件／runtime 證據。因此 Muse 指控「不能合併、必須全系統窮舉」不成立。

風險：多個 trigger 同時命中時，worker 仍可能把配方当作待填表格。改善方向是檢驗 agent 能否選出與當次變更有因果關係的路徑；不是無條件只看 1–2 條路徑，也不是再複製 cr-query 的 fallback 表。

本次保留原文。若實際案例顯示它導致無關查證與成本升高，應修改觸發條件或停止條件，不能用「可能浪費」當成已證實 defect。

### review-engine：證據核心有價值，但內部矛盾已達必修程度

有效部分：Writer/Reviewer 分離、severity 與 confidence 分欄、fresh/intent 的不同錨定、review findings 仍需裁決。這次 Muse 的部分建議不被採納，正好说明 reviewer 不等於 authority。

必修部分：基線 :62 把 LSP zero hits 寫成確認 dead code；:87–94 又禁止把查無當不存在；acceptance-evidence 明確要求動態／config／scripts consumers。:75–83 的工具表另與 cr-first 分工不一致。這批修成一個 routing authority，加上 query coverage／freshness／dynamic consumer 的結論限制。

追查同一宣稱後，同步 code-quality-profile、instruction-writing、symbol-query-routing、audit-test 與 debugging-and-error-recovery 的直接消費段，避免入口指針正確、下游仍宣稱動態引用 100% 完整。

仍需深入評估的部分：actionable instruction blanket boundary 的分類成本；Critical 定義是否過廣；forced-inferred downgrade 是否混淆「嚴重性」與「證據充分程度」。本次沒有靠改級別來繞過自身審查。

## 外審裁決

外審：Muse `job-mudcu4e3-e1byn1`，6 項建議；非投票，逐項對照正文與後果。

| 建議 | 裁決 |
|---|---|
| F1 語義編輯審查成本過高，刪 SLA／縮小 panel | 成本疑慮有理由；直接删 SLA／降低 gate 無實證支撐，未採實作 |
| F2 static-only 由 LLM 計算不可靠，新增 checker | 接受缺工具支撐的批評；不立即新增 checker，避免再造未驗證控制面 |
| F3 Capabilities pilot 被寫成 MUST | 接受作用域矛盾；最新採用決策仍需查明，不替 user 裁決 pilot 升格 |
| F4 arch-thinking 改只抽樣 1–2 路、內嵌 fallback | 不採：原文已允許合併與局部化；固定取樣不能保證 invariant，內嵌另造 routing 重複源 |
| F5 小於約 200 行即可單 reviewer | 不採：diff size 不是 authority／state 邊界風險的代理；一行也可放寬權限 |
| F6 EP 缺 scope freeze／docs 行為判準／外審失敗與 main 前進處置 | 採納需要明确化的部分，EP 已補。其聲稱完全未提 instruction-testing／rebase 不準確，原 EP 已提，但缺具體案例 |

外審另稱「deploy 是 build artifact 而非 landing」不可採：部署器會實際寫全域 AGENTS.md，正是落地。正確修法是 review 前 dry-run，review 後再依授權部署。

## 證據限制與後續

- CR detect_changes 對選定 hooks 回 0 symbols，不作零影響證據。唯讀 reviewer 的 refs 工具自行觸發 index heal；它沒有改 source，但本輪不能宣稱完全零 filesystem 副作用。
- 舊 zero-hit guidance 的獨立選擇 probe 仍選對（不刪、先查 registry），沒有取得行為 RED。修正文義矛盾有來源證據，但不得宣稱已提升 agent 的成功率；probe 是 action-record 情境，未執行真正刪除。
- baseline bundle 為 36,644 bytes，Muse 36KiB gate 僅餘 220 bytes。跨 harness wording 應盡量精煉，完成時重建 bytes 驗證，不能只驗其他兩端。
- 使用者授權落點為 main；機器外部部署與新 session 真實 hook 觸發分開報告，不把 subprocess 測試稱為已安裝端 E2E。

### 既有 registration 檢查落差

`skills/scan-project/scripts/check_single_source.py` 在 primary main 與本 WT 都報一筆 critical：compact-restore-inject 未在它列出的 registration 檔出現。逐項核對後：

- tracked `hooks/compact-restore-inject.registration.json` 含 canonical repo 路徑。
- 唯讀查本機 ZCode `hooks.events.UserPromptSubmit`，確有 `python3 /Users/ctai/Github/ai-guide/hooks/compact-restore-inject.py`、enabled=true、timeoutMs=10000。
- scanner 列出的查詢來源不含 live ZCode config，也不含該 standalone registration；因此其「接線從未存在」結論超出證據。這是本次變更前已存在的 checker 缺口。
- AIR-155 卡已記 machine 註冊完成、live restore dogfood 待真 compact；INSTALL-PROTOCOL 中仍有舊 WT 路徑說明。不能把「實際有註冊」外推成「live restore 已驗收」。

本次沒有重複安裝 hook、改 live config 或把失敗檢查標綠。完整收編需同步 governance template／manifest／standalone protocol 與 scanner；本弧 owner 文檔只準確描述這個獨立接線面。

### Hooks 其餘覆蓋

| 檔案／群組 | 本輪處置 |
|---|---|
| codex_memory_path_deny.py、marshal_admission_guard.py | 讀 payload／path／canonical 邊界；baseline 相關測試已跑，未修改 |
| block-python-c-comment.py | 讀 parser 與 failure 路徑，未取得新增 defect 證據 |
| compact-restore-inject.py | 讀 DB gate、receipt、錯誤分流；registration 落差另列，未改 body |
| memory-index-regen.py | 讀 generator source 比對與 marker 寫入，未對真池執行 regeneration |
| memory-write-sensor.py、memory-dirty-sensor.py | 消費修正後共用 log helper，需雙入口 subprocess 驗收 |
| memory-watch-seed.py | 讀過濾與輸出契約，未新增修改 |
| post-build-gate.py | 讀 receipt、budget 與豁免；未為了本弧改 gate |
| watcher_pairing_nag.py | 讀 ledger／liveness／state，沒有把未重現的 race 報成確定缺陷 |
| zcode_agent_background_gate.py | input keys 保留 rewrite 已查；硬編碼 log 路徑為 portability 剩餘項，未牽動 dispatch gate |
| notification.sh、stop-notification.sh | 讀 subprocess／sentinel，未觸發語音或刪除 sentinel |
| setup-memory-symlinks.sh、verify-memory-topology.sh | 讀拓樸與操作流程，未執行安裝或搬移池 |
