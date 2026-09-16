# 工單：illustrate 報告殼 template 化——S1 template 本體＋S2 spec 瘦身＋S3 本 task 殼（首個消費者）

## 1. 紅線（首段，違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡狀態——止步於 working tree 編輯（git 僅允許唯讀查詢：`git status`／`git diff`）
- 本工單為**寫入型**：寫入僅限 §6「動」清單內檔案；清單外一切視同 read-only
- 禁把產物寫到 `/tmp` 或 repo 外；中間筆記不留檔
- 紅線違反＝失敗，非風格問題

## 2. 目標（一句話）

把 /illustrate html 報告殼的布局/視覺/互動決策從 prose 規格（illustrate-html-mode.md）抽成共用 HTML template（`skills/_common/illustrate-report-shell.html`，含可折疊 sidebar），完成 spec 瘦身與引用同步，並以本 task 的任務簡報殼作首個 template 消費者——EP S1→S2→S3 全段實作。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree）
- 工作目錄：repo root
- base commit：`46005e2da22a4d488c62c9d23dfdaeb85404983a`
- 並行改動聲明（已有但不屬本任務，勿動勿納入 diff 判讀）：`M AGENTS.md`、`M ai-analysis/_tasks/_archived/09-02-muse-plugin-cc/ep.md`、`M backlog/tasks/air-17 …`、staged `backlog/tasks/air-23 …`（本任務卡，主 session 已建）

## 4. 必讀（按序，絕對路徑）

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-04-illustrate-shell-template/ep.md`——**全文**（核心：實作總覽、S1 凍結決策六條、S1-S3 各段「核心實作要點」與「驗證策略」、EP Review Findings 六項已回寫的修正）
2. `/Users/ctai/Github/ai-rules/skills/_common/illustrate-html-mode.md`——「html 報告殼（Report Shell）」整段（手術標的；**保留政策層**的邊界見 §5）
3. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/_archived/09-03-air13-unified-subagent-arch/index.html`——template 的事實參考殼（視覺/結構/JS 基底，承襲來源）
4. `/Users/ctai/Github/ai-rules/skills/illustrate/SKILL.md`——檔尾 Supporting Files 表（加 template 行處）
5. `/Users/ctai/Github/ai-rules/skills/CLAUDE.md`——判斷索引結構是否需要補 template 行（條件改，§6）

## 5. 已決策（勿重辯）＋矛盾例外

以下已凍結（源＝EP S1「已決策凍結」＋EP Review F1-F6 回寫），勿重辯、勿另行設計：

1. template 落點 `skills/_common/illustrate-report-shell.html`（殼帶 ai-rules 工作流語義，不落 archify）
2. 承襲參考殼全部既有決策：dark palette（`#0d1117` 系 CSS variables）、sidebar 264px sticky、iframe `calc(100vh - 190px)` min 640px、main `max-width: 1480px`、`go()` section 切換＋hash restore、iframe `?embed=1`、元件詞彙（dots/card/kpi/note/table/src/frame-wrap）、board＋viewer backlinks
3. **可折疊 sidebar**＝`body.sidebar-collapsed` class 切換（nav width→0、main flex 吃滿）；**禁任何觸發 iframe 重載的實作**（display:none 施於 nav 可、施於 iframe/section 承載禁）；折疊鈕＝button 元素＋`aria-expanded`＋折疊態浮出鈕＋localStorage 記憶
4. 首屏 active JS：無 hash 載入時 active＝**首個含 `.frame-wrap` 章節**（`.frame-wrap.degraded` 計入）；無任何 `.frame-wrap` → 首章
5. 降級統一＝同一 template 的 `.frame-wrap.degraded` 變體（顯示待裝提示＋安裝指路文案），**非第二套殼 codepath**
6. 檔頭 `<!-- usage -->` 註解塊：slot 清單＋填法＋**三條硬約束 rationale**（①首屏 active 規則＋AIR-14 教訓：iframe 僅靠 display:none 章節承載首屏＝rect 0×0 失效（2026-09-03 Playwright 實錄）②折疊禁觸發 iframe 重載 ③aria-expanded/localStorage 語義）——這是失敗教訓的 durable 落點，必寫
7. 不做 manifest 驅動產生器（YAGNI）；零依賴 vanilla JS（禁 CDN/framework）
8. **archify 在場且健康**（clone＋doctor 全綠）——本 task 殼採基礎款（無圖）的理由是**成本分級**（升級款按 EP 規模/user 點名），非缺場；殼內 degraded slot 是 SM-4 的**刻意測試變體**，文案必須標示「降級變體示範：archify 實際在場，此槽位展示缺場時長相」——不得在殼內聲稱 archify 缺場
9. S2 瘦身邊界：illustrate-html-mode.md 只收斂**布局/視覺/互動細節**（~200 行自製、視口尺寸數字、dark theme 數值、首屏細節）為一句 pointer「殼結構/視覺/互動單一源＝template，建殼＝複製＋填 slot」＋降級句改「同 template degraded slot」；**政策層不搬**＝內容篩選通則、敘事骨架變體表、產物位置分流、殼生命週期掛點、雙向一致性、badge 語義/回源義務
10. 殼內容＝EP 判斷材料的投影（雙向一致性：裝判斷材料——動機鏈/凍結決策/S1-S3 做了什麼/驗收證據/回源；不裝執行細節；不得出現 EP 沒有的大方向級主張）

**矛盾例外**：發現現有檔案內容與上述具體衝突（如行號已漂、參考殼缺宣稱的結構），**停下來在報告中舉證**（file:line＋逐字引用），不自行改設計、不服從工單靜默做錯。

## 6. 範圍限定

- **動**：
  - `skills/_common/illustrate-report-shell.html`（新建）
  - `skills/_common/illustrate-html-mode.md`（「html 報告殼」段布局細節收斂為 pointer）
  - `skills/illustrate/SKILL.md`（Supporting Files 表加一行）
  - `skills/execution-plan/SKILL.md`（**僅 :358「成本分級」一句**：基礎款從「純文字殼，~200 行」改「複製 template＋填 slot」；升級款句不動）
  - `skills/CLAUDE.md`（**條件**：僅當其索引結構列舉 _common 檔案時補一行；否則不動並在報告說明判斷）
  - `ai-analysis/_tasks/09-04-illustrate-shell-template/index.html`（新建——本 task 殼，從 template 複製填 slot）
- **不動**：其他一切——尤其 `ep.md`（矛盾→舉證）、`work-orders/`、`done/` 三個舊殼（歸檔歷史）、`backlog/`、`rules/`、`agents/`、`AGENTS.md`、`STATE.md`、`ai-analysis/` 其餘、`.muse-bridge/`
- 違反範圍＝失敗；交付報告附 `git status --short` 舉證不動檔未被改

## 7. 工具接線

- 讀查：bash（`cat`／`rg`／`ls`／`test`／`git status`／`git diff --name-only`）＋read_file；字串搜尋一律 `rg`
- 最小可用：不引入非必要工具；本任務純文檔/HTML，無需 code-reality（其寫入面無論如何禁用）
- 禁把任何工具輸出寫到 repo 外（含 `/tmp`）；遇缺口停下舉證，不自行妥協路徑

## 8. 驗收（命令＋預期結果，逐條實跑；cwd＝repo root）

1. `test -f skills/_common/illustrate-report-shell.html && rg -c "SLOT:" skills/_common/illustrate-report-shell.html` → 檔在且 ≥8（slot 標記：title/badge/meta/nav/section-content/diagram/backlinks/source 等）
2. `rg -n "sidebar-collapsed" skills/_common/illustrate-report-shell.html` → 命中（折疊機制）；`rg -n "aria-expanded|localStorage" skills/_common/illustrate-report-shell.html` → 兩者命中
3. `rg -n "#0d1117" skills/_common/illustrate-report-shell.html` → 命中；`rg -n "calc\(100vh - 190px\)" skills/_common/illustrate-report-shell.html` → 命中；`rg -n "1480px|264px" skills/_common/illustrate-report-shell.html` → 命中；`rg -n "embed=1" skills/_common/illustrate-report-shell.html` → 命中（承襲值全在 template）
4. `rg -n "frame-wrap" skills/_common/illustrate-report-shell.html` → 命中（含 degraded 變體）
5. `rg -n "calc\(100vh|#0d1117|980px|~200 行|1512|1728|264px|1480" skills/_common/illustrate-html-mode.md` → **零命中**（布局值/成本模型殘留歸零）
6. `rg -n "illustrate-report-shell" skills/_common/illustrate-html-mode.md skills/illustrate/SKILL.md skills/execution-plan/SKILL.md` → 三檔皆命中（pointer＋兩處引用）
7. `rg -n "~200 行" skills/execution-plan/SKILL.md` → 零命中（:358 已改 template 模型）；`rg -n "複製 template|填 slot" skills/execution-plan/SKILL.md` → 命中
8. `rg -n "SLOT:" ai-analysis/_tasks/09-04-illustrate-shell-template/index.html` → **零命中**（slot 全填畢）
9. `rg -n "degraded" ai-analysis/_tasks/09-04-illustrate-shell-template/index.html` → ≥1 命中且同段落含「示範」字樣
10. `rg -c "<section" ai-analysis/_tasks/09-04-illustrate-shell-template/index.html` → ≥4（章節殼：動機/決策/做了什麼/驗收證據/回源）
11. `rg -l "illustrate-html-mode" skills/` → 恰 11 檔：implement、spec、code-review、debrief、execution-plan、post-build、illustrate、_common/illustrate-artifact-menu、_common/illustrate-parallel-architecture、_common/illustrate-structure-viewport、_common/illustrate-examples（枚舉 gate，逐檔列出比對）
12. `git status --short` → 新增/修改僅 §6「動」清單（＋並行改動三項＋staged air-23＝baseline 既有，非你所動）

## 9. 證據紀律＋PII 禁令

- 每條驗收附完整命令與原始輸出（截斷標明）；不可只貼結論
- 宣稱「沒改 X」須附 `git status --short`／`git diff --name-only` 佐證
- 報告禁出現任何 email／人名 PII
- 失敗如實記錄不掩蓋；宣稱需有獨立證據

## 10. 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單（對應 `git status --short`）
2. 逐段落落實說明：S1 template（slot 清單實作、折疊/首屏/降級三機制、usage 註解塊含三條 rationale）／S2 三處（html-mode pointer、execution-plan :358、illustrate 表行；CLAUDE.md 判斷結果）／S3 殼（章節結構、badge 🟡、baseline 46005e2、backlinks、degraded 示範槽）——file:line 級對照
3. 驗收 1-12 命令與原始輸出
4. 偏差記錄：與 EP 規格有任何出入處＋原因
5. 未驗證項／被阻擋項（如渲染/互動 DOM 斷言屬主 session 驗收，標未驗證）
6. 建議 reviewer 聚焦點（最有信心不足之處）

**Completion check（回報前自評）**：逐條對 §8 十二項驗收自評——每項標 pass/fail/partial；任何 fail/partial 不得宣稱「完成」，如實標記並說明殘留。
