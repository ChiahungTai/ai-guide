# Thinking skills 改版與審查裁定

## 交付範圍

使用者要求改善 arch-thinking、deep-thinking 的 LLM 可執行性，指定 Codex、Muse、GLM 5.3、GLM Flash 審查，由主 session 裁定修正。後續同意在獨立 worktree 實作後合併 main，保留主目錄 air-91 工作、延後部署；Flash 未產有效審查後，使用者明示「flash 沒有就算了，看其他的吧」。

基線：`9a924e664dcc7ed2de372d01a1b297c885f4da16`。實作 worktree：`/Users/ctai/Github/ai-guide-thinking`，branch：`codex/thinking-skills`。主目錄 air-91 的 model-routing／sync_agents／測試變更不屬本弧。

## 設計結果

| 載體 | 職責 | 改動理由 |
|---|---|---|
| [deep-thinking](../../../../skills/deep-thinking/SKILL.md) | 問題、事實／假設、選項、直接／間接後果、可逆性與改判條件 | 固定深度和重複模板容易讓檢查成本隨小任務膨脹；改為有範圍、能停止的決策流程，摘要併入消費命令 |
| [arch-thinking](../../../../skills/arch-thinking/SKILL.md) | use case、依賴、語義邊界與查證觸發 | 先選命中的檢查，再載對應配方；不以模型家族推定能力，也不強制四層目錄 |
| [reuse](../../../../skills/arch-thinking/reuse.md) | 既有機制與重用判斷 | 相似度只定位候選；實際抽取須核對語義、invariant、ownership、生命週期、依賴成本 |
| [state-and-compensation](../../../../skills/arch-thinking/state-and-compensation.md) | 補償關係、write sites、並行與中間態 | 單一 owner 不保證 invariant；補償可能經 cache 間接相依，修 source 與拆補丁須驗整個組合路徑 |
| [structure-evidence](../../../../skills/arch-thinking/structure-evidence.md) | City Map、call graph、type、data-flow、framework grounding、core 排序 | 機械關係、文件拓樸與 runtime 行為分開；工具路由引用單一源，人類閱讀深度留給 illustrate |

保留公開 skill 名稱與第一性原理／第二層思考的語義。共用契約正確而需求不同，採 consumer projection；authority 錯誤時修 source 並遷移消費者。依賴負擔修為「lean 廣用模組依賴 heavy 實作」才是反向耦合候選，heavy 使用 lean 本身不是缺陷。

同步 design-thinking rule、guide、索引、code-review、ep-review、judge-review、debugging、code-review-and-quality、illustrate 子範本與 symbol-query-routing。沒有調整模型路由、pin、global settings 或部署接線。

## 獨立審查與裁定

首輪原文與模型／job 資料：[reviews.json](reviews.json)。native Codex reviewer 因 quota 未產 findings，改走 Codex web pool `chatgpt-web/high`；這是不同執行面，不能稱 native reviewer 已通過。GLM 5.3 回傳 effectiveModel；Muse ledger 僅記 requested model `muse-spark-1.3`，不將 requested ID 當獨立 attestation。

| 來源 | 結果 | 主 session 裁定 |
|---|---|---|
| Codex web/high | accept，無 finding | 保留第二意見；無 finding 不推翻其他 reviewer 的具體反例 |
| GLM 5.3 | needs-fix | 採納 EP 固定層數、viewport 舊分數等實際殘留；部分採納標題消歧與事實查證補強 |
| Muse Spark 1.3 | needs-fix | 採納單檔刪除入口、補償實跑義務、消費端同步；保留有用的第一性原理詞彙並映射操作含義 |
| GLM Flash | 未取得有效審查 | 初次 failed-or-capped、無原因／文字；重試程序存活但無 session／文字，停止後改小工單；使用者免除該審，已停止，不當 accept |

| Finding 群 | 裁定與落地 | 改判條件 |
|---|---|---|
| GLM F1：兩層標題必然讓模型湊後果 | 部分採納：標題改「決策與後果」；保留直接／間接義務及查無影響的範圍。不接受「必然」行為宣稱 | 可重播的實際誤判證據可支持更強限制 |
| GLM F2 / Muse F3：EP 至少追蹤兩層殘留 | 採納：EP 改有證據的直接／間接影響與停止條件，code-review 同步 | 若呼叫者有特定深度契約，須明列適用情境 |
| GLM F3 / Muse F2：第一性原理詞彙過時 | 部分採納：保留詞義並映射到問題／約束／事實／選項；judge 交付依據與改判條件，不另交推理模板 | 同條件應用若持續錯解，再依失敗修措辭 |
| GLM F4 / Muse F1：LOW confidence／分數／工具分工殘留 | 採納：viewport 使用符號／檔案定位與語義判定；候選 ID 由呈現端選擇，工具依既有路由 | 若日後有校準且驗證過的 scorer，另定獨立契約 |
| GLM F5：always-on 事實查證消失 | 部分採納：其他 always-on 條款仍在，不能稱全域防線消失；局部 rule 補來源查證與假設不可冒充事實 | 實际載入證據發現全域缺口時另處理部署 |
| Muse F4：單檔刪除沒有明確入口 | 採納：派發前檢查触發表，命中就注入責任；single-agent／Architecture 軸均須承接，不以檔數省略 | 若實際派發仍漏，再修 producer 或 runtime 接線 |
| Muse F5：補償組合驗證要求弱化 | 採納：實作驗收須整合測試或可重播驗證，覆蓋中間資料／cache／消費端；唯讀審查只列待驗 | 合法例外須提供能證明相同 invariant 的替代證據 |
| Muse F6：debugging 無 pointer 所以完全不可達 | 部分採納：always-on 已路由，完全不可達不成立；debugging 補短入口改善獨立使用 | 實際 activation／retrieval 失敗可支持進一步修改 |
| Muse F7：description 刪了改判條件 | 不採納該事實宣稱：新 description 已含此詞；自然語義補留舊檢索錨 | 自動觸發尚未實測，不推論 recall 已改善 |

Muse 針對性複驗為 accept，逐項原文證據見 [muse-followup.json](muse-followup.json)。程序限制：首輪 Muse 自報使用 /tmp 與 python3，複驗仍自報一次 python3；這些違反工單，不聲稱其工具紀律合規。引用其可核實文字 findings，不據自報升格 runtime 驗收。

## 應用驗證與限制

固定七個可信合成案例：不同語義的 Invoice、正確共用契約的投影、authority 修復與拆補丁、單一 owner 的 race、經 cache 的補償、動態名稱下零搜尋命中、純局部 label。原文及 baseline／treatment 各五個 fresh-context 回覆見 [application-results.json](application-results.json)。使用 native subagent 繼承主模型，未另指定或取得模型 ID attestation。

- baseline、首版 treatment 各五次，七案主要決策均符合預定判準。沒有 baseline correctness failure，因此不能宣稱正確率提升；此證據只支持已測案例的應用回歸。
- 各回覆字元數（非 token）baseline：2691、2634、2670、2422、2637；treatment：2191、1926、2089、2007、2184。觀察到較少重複模板；樣本少且無 no-guidance arm，不推論普遍效率或統計顯著改善。
- 修正版另以 GLM 5.3 fresh context 跑七案例，核心決策均符合判準，見 [glm-final-probe.json](glm-final-probe.json)。這不是跨模型對照，也不是對 production source 的執行驗收。
- 該輪延伸分流在「命中 Architecture 檢查」上正確，但把 ≥3 files 外推為 Workflow，分類為 UNEXPECTED。回查後確認 ≥3 files 在 Agent Tool 的 dual-context 有既有用途，不能一併禁止。中間補句曾過度概括「不由檔數切換 dual」，已撤回並改成：A/B 依 effort／max-agents；single／dual 依既有 dual-context 與無 EP 降級；觸發表只增加檢查責任。中間複驗 case B 的已選 single 與四檔條件缺 EP 資訊，不能当成功判分；最終複驗改給完整政策輸入，結果另附。
- [中間分流複驗](glm-routing-intermediate.json) 保留原文，不挑綠燈丟棄問題樣本。[完整輸入的分流複驗](glm-routing-final.json) 正確選出 A=Agent Tool single＋補償、B=Agent Tool dual＋重用／state、C=Workflow＋Correctness／Readability；另指出 dual 的配方承接者不明。採納此 omission：將責任改為三列明表，dual 的兩份 prompt 都含命中配方，意圖材料仍分開。最後這項明確指派由主 session 做靜態覆蓋核對，沒有追加實際 spawn 測試。
- description 自動 activation、按需讀取的機械事件序、實際派發與長 context 行為未驗證；不能把 reviewer 自報讀檔當載入順序證據。GLM Flash、Sol、Terra 沒有本弧獨立行為驗收。

## 靜態驗證與部署邊界

- `git diff --check` 通過。
- `uv run python scripts/scan_skills_desc.py --root skills`：FAIL=0；兩項既存 quoted-# 警告（python-type-gap、rules-reminder）。
- 新增相對連結檢查無缺失；舊教學 placeholder 不當新斷鏈。
- `uv run python scripts/deploy_agents.py --dry-run` 通過：三端 bundle 各 33,389 bytes；Muse 約達 36KiB gate 的 90%，有尺寸警告。沒有實際部署。
- `check_single_source.py` 在 linked WT 非全綠：三個未部署 bundle 差異，加上 WT 沒有 local-only settings.json 所致的兩個 hook registration 告警。主目錄對照為 critical 0、既有 instruction-testing allowlist important 1。不能報整個 repo 全綠；本弧不改 shared settings 或其他 session 的接線。

### 提交環境問題與驗證

首次 commit 被既有 `.githooks/pre-commit` 擋下：404 passed、29 failed；失敗集中於測試建立臨時 Git repo，出現 `must be run in a work tree`。當下真實 repo 的 `core.bare` 變為 true，已恢復 false。失敗前 staged 變更仍在，HEAD 未前進。

hook 直接跑 pytest，未隔離外層 Git 定位變數；測試內 `git init` 可被導向外層 repo。隔離重現確認：注入 GIT_DIR 後，指定的內層目錄沒有建立自己的 `.git`；該小重現未重現 bare 切換，不能把每個症狀都稱為已獨立重現。離開 hook 繼承環境後，原失敗族群的最小選樣 3 passed。

一次性 local wrapper 以 `git rev-parse --local-env-vars` 枚舉並清除繼承變數，再執行原 `.githooks/pre-commit`，完整測試 433 passed，原有 py_compile 閘亦通過。wrapper 只供本次 `git -c core.hooksPath=... commit` 使用，沒有改共用 hook 或略過原測試。既有 pre-commit 的永久環境隔離修復仍是獨立待辦；後續其他 worktree 提交可能遇到相同問題。

## 整合契約

AUTH: user said "你這要不要開ｗｔ實作然後最後再 rebase/merge?"

AUTH: user said "你建議的OK"

只提交本弧 instruction 與證據，feature rebase onto main，再 ff-only 合併 main。主目錄 air-91 與其未提交變更保留；不 push、不部署。主目錄吸收 main 後，才由該工作線執行正式 deploy 並核对新 session 載入，避免 worktree source 與全域 bundle 混版。
