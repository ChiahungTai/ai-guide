# illustrate 報告殼 template 化（可折疊 sidebar）

> **ep_type**: implementation
> **docs mode**: product 變更全為 `.md` 與 static `.html` Report Shell（`skills/_common/` 新 template、`illustrate-html-mode.md` 瘦身、本 task 殼生成）；inline JS 保留 browser/DOM runtime 與視覺驗收，不以 docs mode 跳過行為驗證。任務家 `verify-shell.cjs` 只服務本 artifact 驗收、無 production consumer，列為 evidence artifact（跳過 TDD/mypy/pytest，本 verifier 必須實跑）

## 實作總覽

**問題**：報告殼的布局/視覺/互動約束（dark theme、NB 視口尺寸、首屏 active 規則、`?embed=1`）目前以 prose 承載在 [illustrate-html-mode.md](../../../../skills/_common/illustrate-html-mode.md)——每次建殼由 AI 從規格重新手寫 ~200 行 HTML，每輪重推導都是 drift 機會（AIR-14 實證：首屏 active 落在無圖章節 → 圖 `rect 0×0`）。

**解法**：抽成共用 template（`skills/_common/illustrate-report-shell.html`）——結構決策一次寫進 code，AI 建殼只填 slot；順勢新增**可折疊 sidebar**（NB 視口下圖吃滿全寬——「圖是主角」裁決的自然延伸）。本 EP 的 task 殼即首個消費者（S3），dogfooding 驗證。

**分工**：GLM 寫 EP＋審查＋委派監工；muse 跑 implement（單工單覆蓋 S1-S3，序列依賴線性）。

## 段落 0 研究摘要（主 session 機械掃描 2026-09-04）

- **事實參考（de-facto baseline）**：`ai-analysis/_tasks/_archived/09-03-air13-unified-subagent-arch/index.html` ——dark palette（`#0d1117` 系 CSS variables）、sidebar 264px sticky＋brand block（badge/標題/baseline meta）、`go()` section 切換＋hash restore、`.frame-wrap` iframe＋`?embed=1`＋全屏連結、backlinks（board :6420＋viewer :6421）、元件詞彙（dots/card/kpi/note/table/src）。**template 以此為基底演化，非從零重寫**
- **archify 在場且健康**（2026-09-04 補證：clone `~/Github/archify/archify/bin/archify.mjs` 存在＋`doctor` exit 0 全綠。首掃只查 skills 根、漏了 spec 偵測順序第 2 步——教訓：偵測照 [illustrate-html-mode.md](../../../../skills/_common/illustrate-html-mode.md) 偵測順序全跑）→ 本 task 殼採**基礎款（無圖）**的理由＝成本分級（升級款按 EP 規模/user 點名），非缺場；degraded slot＝SM-4 的刻意測試變體（殼內標示「示範用——archify 實際在場」，不把錯誤環境聲稱固化進殼）。升級款圖＝post-build 可選拉伸（template 結構不變）
- **ripple 面（skills/ scope 枚舉，2026-09-04 實跑 11 檔）**：implement、spec、code-review、debrief、execution-plan、post-build、illustrate、_common/illustrate-artifact-menu、_common/illustrate-parallel-architecture、_common/illustrate-structure-viewport、_common/illustrate-examples——多數僅 link 引用（不需改）。引用「將被搬走的布局細節」者＝illustrate-html-mode.md:50（手術標的）＋execution-plan/SKILL.md:358（`~200 行` 成本模型，S2 同步）。全 repo 另有 ai-analysis/ 等 9 檔（link 引用，S2 不搬檔不斷鏈，不在掃描 scope）
- **backlog 場勘**：`backlog task list --plain` 無同域卡（去重過）；下一號 AIR-23
- **muse 場勘**：`.muse-bridge/setup.json` green:true（workspaceRoot=ai-rules）——委派前置已滿足
- **風險假設**：①折疊 toggle 若用 display:none 於 nav 會改 main 佈局但**不重載 iframe**（CSS width/transform 切換，iframe src 不變）——低風險，S3 DOM 斷言驗證；②`skills/CLAUDE.md` 是否需列 template——開工時查其索引結構決定（低）

## UC 盤點（docs mode：受影響命令/rules 清單）

### Backlog 關聯
- 掃描：`backlog task list --plain`（2026-09-04）——無同域卡
- 自動建卡：AIR-23「illustrate 報告殼 template 化（可折疊 sidebar）」（EP 追蹤卡，建卡即 `git add backlog/`）

### SYSTEM-MAP 影響
- 無 SYSTEM-MAP.md（元專案，正當跳過）

### 掃描範圍
- `skills/illustrate/SKILL.md`（html 模式入口＋supporting files 表）、`skills/_common/illustrate-html-mode.md`（殼規格單一源）、`skills/CLAUDE.md`（工作流索引）、`rg -l "報告殼|Report Shell"` 15 檔（引用面）

### 受影響命令（行為變更 = 殼生成來源從「每次手寫」改為「複製 template 填 slot」）
| 命令 | 引用機制 | 變更 |
|------|---------|------|
| `/illustrate`（html 模式） | illustrate-html-mode.md | 生成路徑改 template；SKILL.md supporting files 表加 template 行 |
| `/execution-plan`（hook 1 建殼） | :358 成本分級句引用手寫殼成本模型（`~200 行`） | **一處同步**：基礎款描述改「複製 template＋填 slot」 |
| `/implement`（5a badge 同步）、`/metadata-sync`（殼 refresh）、`/post-build`（hook 2） | link 引用 | 同上 |
| `/debrief`、`/spec`、`/commit`、`/kanban-board` | link/概念引用 | 不改（S2 複掃確認無布局值殘留） |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應 |
|---|------|------|---------|------------|------|
| SM-1 | 建殼 happy path | `/illustrate html @ep` / hook 1 | 複製 template→填 slot→章節導覽可切換、hash restore 可用 | 無 | S1/S3 |
| SM-2 | 折疊 sidebar | 點折疊鈕 | nav 收起、main/iframe 吃滿寬、**iframe src 不變（不重載）**、浮出鈕出現、鍵盤可達（button＋aria-expanded）、折疊態 localStorage 記憶 | 無 | S1 |
| SM-3 | 首屏 active 落點 | 殼載入、無 hash | active 落在**首個含 `.frame-wrap` 章節**（degraded 計入）；無任何 `.frame-wrap` → 首個章節（AIR-14 規則進 code） | 無 | S1/S3 |
| SM-4 | archify 缺場降級 | 圖 slot 無 diagram-*.html | 同一 template 的 `.frame-wrap.degraded` 顯示待裝提示——**不生成第二套殼 codepath** | 無 | S1/S3（本 task 殼實證） |
| SM-5 | 投影鎖定重投影 | 本體（ep.md）修訂 | 重投影只換 slot 內容，template 檔不動；task baseline 固定，殼頭部 projection source 更新（未 commit 用 ep.md content SHA） | post-build 修訂 ep.md 後重算 content SHA，殼 marker 必須同步 | S2/S3 |
| SM-6 | 窄視口 | <NB 寬（如 1024px） | 折疊鈕仍可達、main 不破版（最低可用，不追求完整 RWD） | 無 | S1 |

## 段落劃分原則

S1（template 本體）→ S2（spec 瘦身＋ripple 同步，依賴 S1 存在才能 pointer）→ S3（本 task 殼回填＝消費端驗證，依賴 S1+S2）。全序列，單工單。

---

## S1 — template 本體 `skills/_common/illustrate-report-shell.html`

### Context
- **動機**：布局/視覺決策從 prose 進 code（單一源）；AIR-14 類首屏 bug 從「靠 session 記性」變「結構上不可能」
- **UC 引用**：殼生成來源 template 化（受影響命令表全體）
- **依賴錨點**（docs mode 文檔行號，寫作當下驗證）：
  - 殼三層結構與自製殼定義 → `skills/_common/illustrate-html-mode.md:42-55`
  - dark theme 裁決 → `illustrate-html-mode.md:52`；NB 視口尺寸 → `:51`；首屏 active 規則 → `:54`
  - 降級（基礎款殼）→ `illustrate-html-mode.md:55`
  - 共通必備（badge/回源/board 反向連結）→ `illustrate-html-mode.md:84`
  - 事實參考殼 → `ai-analysis/_tasks/_archived/09-03-air13-unified-subagent-arch/index.html`（全檔）
- **語義約束**：與 S2 共享「template 是殼結構唯一權威，prose 只留政策層」；與 S3 共享 slot 命名
- **基礎設施盤點**：無現成 html 資產（`fd -e html skills/` 零命中）——template 是首個；參考殼如上
- **技術選型**：零依賴 static HTML＋vanilla JS（~300 行）；禁外部 CDN/framework

### 已決策凍結（writer 禁重辯；發現具體證據衝突可停下舉證）
1. 落點 `skills/_common/`（殼帶 ai-rules 工作流語義——badge/board/任務家——**不落 archify repo**）
2. 承襲參考殼全部既有決策：dark palette、sidebar 264px、`calc(100vh - 190px)` min 640px、main max-width 1480px、`go()`＋hash restore、`?embed=1`、元件詞彙（dots/card/kpi/note/table/src/frame-wrap）
3. 折疊＝`body.sidebar-collapsed` class 切換（nav width→0、main flex 吃滿）；**禁任何觸發 iframe 重載的實作**（display:none 於 nav 可、於 iframe/section 承載禁——AIR-14）
4. 降級統一＝同一 template 的 `.frame-wrap.degraded` 變體（待裝提示＋安裝指路），非第二套殼
5. 不做 manifest 驅動產生器（YAGNI）
6. 檔頭帶 `<!-- usage -->` 註解塊：slot 清單＋填法＋**三條硬約束 rationale**（①首屏 active 規則與 AIR-14 教訓：iframe 僅靠 display:none 章節承載首屏＝rect 0×0 失效 ②折疊禁觸發 iframe 重載 ③aria-expanded/localStorage 語義）——失敗教訓自 illustrate-html-mode.md 瘦身後的 durable 落點（AI 消費的自述文件，單一源）

### 核心實作要點（docs mode：修改要點）
- **slot 標記**：`SLOT:title`、`SLOT:badge`、`SLOT:meta`（task baseline 與 projection source 分欄）、`SLOT:nav`（章節清單）、每章節 `SLOT:section-content`＋可選 `SLOT:diagram`（frame-wrap 或 degraded 二擇一）、`SLOT:backlinks`（board＋viewer EP 連結）、`SLOT:source`（回源段）；範例值統一用 `{{UPPER_SNAKE_CASE}}` placeholder
- **固定行為（template 擁有，非 slot）**：首屏 active JS（首個含 `.frame-wrap` 章節，fallback 首章）、折疊 toggle（aria-expanded＋浮出鈕＋localStorage）、hash restore、計畫物樣式 `.tag-plan`（「S<N> 計畫中」）
- **摺疊鈕位置**：sidebar 右緣垂直居中（展開態）；折疊態浮出鈕固定左上
- **SM-6 最低保障**：nav `min-width` 折疊態為 0、main `min-width:0`（flex 溢出防護）

### 驗證策略
- 結構：slot 標記齊全（rg `SLOT:` 對照本段清單）、placeholder token 格式一致、折疊/首屏/降級三機制各有對應 code（rg class/id 錨點）
- 承襲值機械核對：rg `#0d1117|calc\(100vh - 190px\)|1480px|\?embed=1` 於 template 全命中
- 渲染：serve 後 HTTP 200＋browser parse 後 title/charset/body 文案正確＋無 JS console error（S3 一併做互動斷言）

---

## S2 — spec 瘦身＋ripple 同步

### Context
- **動機**：template 落地後 prose 佈局約束成第二真相源——依 single-source drift 防護收斂為 pointer，**保留政策層**
- **依賴錨點**：`illustrate-html-mode.md:42-55`（三層結構＋布局約束段——瘦身標的）、`skills/illustrate/SKILL.md:168`（supporting files 表）、`skills/CLAUDE.md`（工作流索引——開工時查是否需補行）
- **語義約束**：與 S1 共享 凍結決策 1-6；政策層**不搬**＝內容篩選通則、敘事骨架變體表、產物位置分流、殼生命週期掛點、雙向一致性、badge 語義/回源義務（這些是「殼該說什麼」；template 管「殼長什麼樣」）

### 核心實作要點
- `illustrate-html-mode.md` 三層結構段改寫：布局/視覺/互動細節（~200 行自製、視口尺寸、dark theme、首屏規則、折疊）收斂為一句 pointer——「**殼結構/視覺/互動單一源＝template `skills/_common/illustrate-report-shell.html`，建殼＝複製＋填 slot**」＋降級句改「同 template degraded slot」；政策段落落不動
- `skills/execution-plan/SKILL.md:358` 成本分級句同步：基礎款從「純文字殼，~200 行」改「複製 template＋填 slot」（升級款句不動）
- `skills/illustrate/SKILL.md` Supporting Files 表加一行 template
- `skills/CLAUDE.md`：若索引結構列 _common 檔則補；否則不動（開工判斷）

### 驗證策略（機械）
- 殘留掃描：`rg -n "calc\(100vh|#0d1117|980|~200 行|1512|1728|264px|1480|display:none" skills/` → 布局值/成本模型只允許出現在 template（值）；allowlist 無關命中＝memory-audit「200 行」（memory 索引預算，無 `~` 前綴自然排除）、consistency:85（行號假設例）——allowlist 外命中 = FAIL
- 引用面複掃（枚舉 gate）：`rg -l "illustrate-html-mode" skills/` = 段落 0 枚舉 11 檔逐檔在場且無新增；`rg -n "illustrate-report-shell" skills/` 命中 = illustrate/SKILL.md＋illustrate-html-mode.md＋execution-plan/SKILL.md（新引用落點）
- `/consistency skills/_common/illustrate-html-mode.md`＋`/consistency skills/illustrate/SKILL.md`（改動檔逐一）

---

## S3 — 消費端驗證：本 task 殼（首個 template 消費者）

### Context
- **動機**：消費端驗證模式——template 的主要消費者是「建殼的 AI」與「看殼的人」，在真實流程（hook 1 交付）中驗證非孤立測試
- **依賴錨點**：殼輸出 `ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/index.html`（本目錄）；掛點規格 `illustrate-html-mode.md:75-84`
- **語義約束**：殼＝EP 投影（雙向一致性：大方向不可失真）；既有 `done/` 三殼**不動**（歸檔歷史文檔）

### 核心實作要點
- 從 template 複製填 slot：badge 📋（build 後隨 5a 同步）、meta＝AIR-23＋baseline `46005e2`、章節＝EP 判斷材料（動機/凍結決策/三段做了什麼/驗證證據/回源）
- **一個 degraded diagram slot 作 SM-4 刻意測試變體**——文案標示「降級變體示範：archify 實際在場，此槽位展示缺場時長相」（誠實投影）
- 遵守內容篩選通則：裝判斷材料（凍結決策表、為什麼、驗收），不裝執行細節

### 驗證策略
- 靜態：slot 全填，`SLOT:` 與 `{{PLACEHOLDER}}` 零殘留（rg），章節錨點與 nav 一致
- 渲染＋互動：serve HTTP 200；Playwright 驗證 browser parse、折疊後 iframe 不重載、main 真正吃滿、focus 不進 hidden nav、localStorage reload restore、有效 hash restore、`#sidebar`／未知 hash fallback 不會形成空白頁，以及 1024px collapsed viewport 不破版
- 視覺驗收：截圖交 vision-review agent（合約 dispatch：視覺錨點＋verdict；禁主 session 直讀圖）——門檻：dark theme 一致、折疊互動可發現、首屏價值主張可見

---

## 整合策略

- **baseline**: `46005e2da22a4d488c62c9d23dfdaeb85404983a`
- 並行 session 改動（`M AGENTS.md`、`M ai-analysis/_tasks/_archived/09-02-muse-plugin-cc/ep.md`、`M backlog/tasks/air-17…`）**不屬本 EP**——不審不改不 add；本 EP commit 只 add 指名檔案
- 變更檔案預期：`skills/_common/illustrate-report-shell.html`（新）、`skills/_common/illustrate-html-mode.md`、`skills/illustrate/SKILL.md`、`skills/execution-plan/SKILL.md`（成本分級與 docs-mode trigger）、（條件）`skills/CLAUDE.md`、`ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/`（ep.md＋index.html＋work-orders/＋task-local verifier）、`backlog/tasks/air-23…`（新卡）

## 收尾步驟（docs mode）

1. 受影響命令行為已反映（S2 ripple 掃描綠）＋ `skills/CLAUDE.md` 工作流索引同步（如需）
2. `/consistency` 三檔：illustrate-html-mode.md、illustrate/SKILL.md、skills/CLAUDE.md（有動才跑）
3. 情境 D 結算（docs-mode EP 無 .py UC）：EP 歸檔程序照任務家慣例（build 終態後）＋ AIR-23 卡結案兩步（`-s Done --final-summary` → `--ref` 換 done/ URL，卡留 Done 欄）
4. 殼 badge 同步：build 完成 → ✅（本 EP 殼即 S3 產物，同步在同一弧內）

## EP Review Findings — 09-04-illustrate-shell-template

> EP review agent（獨立 context）2026-09-04；主 session judge-review 裁決；F1 事實經主 session 補證（clone 在場＋doctor exit 0 全綠）。

| ID | 嚴重度 | 檔案:行 | 問題 | 建議 | 狀態 | 決策 |
|----|--------|---------|------|------|------|------|
| F1 | 🔴 | ep.md 段落0／S3／SM-4 | 「archify 缺場」與現況不符（clone 在場＋doctor 全綠）——錯誤環境事實會固化進殼敘事 | 改以成本分級支撐基礎款；degraded slot＝刻意測試變體＋示範標示 | implemented | ✅ |
| F2 | 🔴 | execution-plan/SKILL.md:358 | S2 gate 與 UC「不改檔」互斥：:358 引用將被搬走的成本模型（true positive）；pattern `200 行` 含 false positives | :358 納入 S2 ripple；pattern 收緊 `~200 行`＋allowlist | implemented | ✅ |
| F3 | 🟡 | ep.md 段落0／S2 驗證 | 引用面計數錯（稱 15 檔，實況 skills/ 11、全 repo 20）且 gate 只有數字無清單不可執行 | 改列枚舉清單，gate 改逐檔存在＋無新增 | implemented | ✅ |
| F4 | 🟡 | ep.md S1 決策6 | AIR-14 教訓自 prose 瘦身後無 durable 落點（EP 會歸檔），與「禁觸失敗教訓」張力 | template 檔頭註解承接三條硬約束 rationale | implemented | ✅ |
| F5 | 🟢 | ep.md SM-3／S3 斷言② | SM-3 fallback 措辭與 S3 斷言在「僅 degraded 殼」情境矛盾 | fallback 改「無任何 `.frame-wrap`（含 degraded）→ 首章」 | implemented | ✅ |
| F6 | 🟢 | ep.md S2 驗證／SM-5 | pattern 未覆蓋 1512/1728/264px/1480 等布局值；SM-5 本 EP 生命期不可測 | pattern 收緊＋allowlist done/；SM-5 標設計性質 | implemented | ✅ |

裁決摘要：採納 6 / 不採納 0 / 需確認 0。各項已回寫 EP 對應段落（段落 0、UC 表、SM-3/SM-5、S1 決策 6、S2 要點與驗證策略、S3、整合策略）。
