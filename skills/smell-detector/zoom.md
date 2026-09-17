# zoom mode — 變焦批判完整規格

> 本檔是 [smell-detector](SKILL.md) **zoom mode**（`/smell-detector <dir|files>`，預設）的完整規格。mode 分工與測試 smell 三類見 [SKILL.md](SKILL.md)。

## 黑盒子（mode input → output）

- **input**：你指著一個 dir/files 的既有 code（預設含對應 test）
- **output**：一份報告——哪些 code/test 不該存在、為什麼、怎麼修、查證過程（結論 + 全貌 + 問題 + 建議 + 圖 + 查證誠信）；**同時落檔 `ai-analysis/smell-detector/<dir>/<scope>.md`**（finding 帶 ID F1/F2/T1...，供 `/followup-review` 跨 session 對照驗收）

read-only 偵測器（不改 code）；先結論（倒金字塔）→ 全貌 → per-finding 查證 → 查證誠信表。

## 定位（三向 + 分工）

| 命令 | 定位 | 觸發 |
|------|------|------|
| `/code-review` | 審 diff 正確性（change-driven） | 改完 code |
| `/audit-test` | 測試反模式機械稽核（表格，廣而深） | build / commit gate |
| `/debrief` | AI 改動理解簡報（行動後） | 改完想理解改了啥 |
| **zoom mode** | **放大鏡**：質疑存在 → 判準查證 → 問題+建議+圖 | 想批判檢視既有 code |
| baseline mode（同 skill `--baseline`） | 盤點模組穩固度（守護既有） | onboarding / 週期 |

**與 baseline 的關鍵區隔**：baseline 問「這模組穩不穩」（守護既有）；zoom 問「**這些 code/test 該不該存在**」（質疑存在）。兩者正交。典型觸發是懷疑 AI 亂加，但不一定要先懷疑——任何想質疑既有 code 存在價值時都適用。

## 委託 Skills（跨 skill）

- [review-engine](../review-engine/SKILL.md) — 嚴重度 / 信心 / 審查者自證 / LSP 查證（共用真相源）
- [arch-thinking](../arch-thinking/SKILL.md) — **結構性判準（1/4）預設 lens**：core/leaf tiering + dep weight + 重用/邊界 + LSP 查證
- [cr-query](../cr-query/SKILL.md) — graph 結構事實（engine 若在場）
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則

## 核心目標

**質疑存在**——這些 code/test 該不該存在？用 6 條判準 + 機械查證深挖，**批判性追查**（查證、深化、撤銷 false positive、展示判斷過程），非機械列 finding（那是 audit-test）。

## 審查範圍

| 用法 | source | 場景 |
|------|--------|------|
| `/smell-detector <dir>` | 目錄 source + 對應 test | 想檢視整個模組 |
| `/smell-detector <file...>` | 指定檔 + 對應 test | 想檢視特定檔 |

**預設 source + test 同審**（AI 亂加 code 與亂寫測試是同一類問題，同 mode 處理）；**user 可明確排除**（prompt 註明只審 source / 只審 test，或 dir 無對應 test 時自動只審 source）。test 側聚焦判準 2（production wrapper 重複），反模式深度（mock / 覆蓋對稱）編排 [audit-test](../audit-test/SKILL.md)。

## 執行模式

**直接執行為主**（單 session，read-only 偵測器，仿 [audit-test](../audit-test/SKILL.md) stance）：scope 是 dir/files（通常 ≤ 10 檔），fit 一個 session。讀 source + test → 6 判準查證 → 產報告。

scope 極大（50+ 檔）才用 Agent（free-text 產出，主 session 組報告；**禁 complex nested schema**，教訓見 baseline.md 執行模式段）。

## 6 條判準 × 機械查證

> 判準 = 用戶 viewport（人類判讀），機械查證 = 手段。完整定義見下方「Domain 層」；此表為摘要。

| # | 判準（用戶 viewport） | 機械查證 | 既有引用（不重寫） |
|---|---|---|---|
| 1 | **YAGNI 嚴格**（沒用就刪） | LSP `findReferences` + rg 確認零消費者；filter trap 區分（YAGNI 往刪 / 驗證不能刪）；**arch-thinking 觀：是否 connected dead cluster / 重用缺口**（不只零 caller）；**新舊並存**（enum/property/alias 兩套寫法同時在場）＝重構未完成訊號——`git log -S` 找引入 commit＋查消費點是否已切換 | [collaboration-constraints](../../rules/collaboration-constraints.md) YAGNI check + [acceptance-evidence skill](../acceptance-evidence/SKILL.md) filter trap |
| 2 | **測試要有實際價值** | 隱含覆蓋查證（收窄：production wrapper 重複測試，見下方編排段）；不為覆蓋率寫 | 委外 [audit-test](../audit-test/SKILL.md)（角度 1/6：反模式、過時與其餘冗餘） |
| 3 | **嚴格不放水** | 機械查證不靠善意；對抗性自查（挑戰自己判斷） | [collaboration-constraints](../../rules/collaboration-constraints.md) 反 Sycophancy + [review-engine](../review-engine/SKILL.md) 審查者自證 |
| 4 | **質疑命名/設計** | 命名碰撞（LSP）/ domain 一致 / phantom API（rg + LSP 確認符號存在）；**arch-thinking 觀：bounded context 邊界 / dep weight / 設計 pattern** | **本 mode 自帶**（分散承載 → 封裝即價值；詳見 Domain 層） |
| 5 | **scope 釐清** | mixed-tree 分組（`git status`）+ 結論 framing 對應 scope | **本 mode 自帶**（完全無既有承載；詳見 Domain 層） |
| 6 | **大改動管控** | 風險分級 → 直接改 / card Planning Contract / EP 三分流（[ai-development-guide](../../ai-development-guide.md) 風險＋規模分級） | [ai-development-guide](../../ai-development-guide.md) 風險 + 規模分級 |

## 輸出格式（全貌 + 問題 + 建議 + 圖 + 查證誠信）

> 倒金字塔：**結論 → 全貌（黑盒子 + 結構級 verdict）** → 每個 finding「問題 + 建議 + 微圖」→ 查證誠信段。

```
# Smell-Detector zoom — <scope>

> ✅ 結論：<一句話，行動導向 — 健康或有 N 個債，建議改 X>

## 全貌（黑盒子：這模組做什麼 + 坐哪）
<2-4 行：模組 input→output 行為 + 在結構中的位置 + 結構級 verdict（arch-thinking 觀：pattern / 邊界 / 重用）；macro 結構圖交 /illustrate @<scope>，此處引用不重畫>

## Source 問題 + 建議
### <F1> 🟡 <問題標題> ［狀態：待修｜不修｜已修｜已驗］
**問題**：<描述，含 file:line>
**建議：<明確推薦>** — <理由>
<ASCII 圖：現況 vs 建議>

## Test 問題 + 建議
### <T1> <❌撤銷|✅保留|💡可改> <標題> ［狀態：待修｜不修｜已修｜已驗］
... （同上格式）

## 查證誠信（過程記錄）
| Finding | 原判斷 | 查證 | 最終（翻案/深化/確認） |

## 附錄（折疊，僅參考）
<details>方法論限制 + 歷史回顧（若有）</details>
```

**關鍵（避開前次失敗陷阱）**：
- **推薦先行**（非選項清單）：每個 finding 給「建議 X，因為 Y」，不給「A or B 你選」
- **查證誠信段必含**：記錄翻案（撤銷）/ 深化 / 確認，展示「批判性追查」——對 audit-test 的差異化
- **撤銷的 finding 保留**（標 ❌）：查證推翻不刪除，示範自我否證建立信任
- **微觀 ASCII 圖**（problem → fix 對照）：**僅當釐清該 finding 的 problem→fix 時才畫**（非每個 finding 必畫，避免噪音）；**結構巨觀圖（call graph / city map / 重用 / 邊界）不自畫——交 `/illustrate @<scope>`**
- **LSP stale 警告**：判死碼前 LSP `findReferences` 回可疑少（只 intra-file）必須 rg 補（[symbol-query-routing skill](../symbol-query-routing/SKILL.md) 條件式 fallback）——dogfood 實證：`throttle()` LSP 只回定義點，rg 才發現 production 在用

## 執行流程

| 步驟 | 動作 |
|------|------|
| 1 | 解析 scope（dir/files）+ `git status`（mixed-tree 分組，判準 5） |
| 2 | 讀 source + 對應 test（完整，非截取） |
| 3 | 6 判準查證（LSP `findReferences` + rg；判準 4/5 詳見 Domain 層） |
| 4 | test 側：判準 2（隱含覆蓋查證）+ 編排 audit-test 深度（反模式 / mock） |
| 5 | 查證誠信：每個 finding 標信心；inferred 必查證（防 false positive）；翻案 / 深化記錄 |
| 6 | 產報告（**全貌** + 問題 + 建議 + 圖 + 查證誠信），倒金字塔 |

## Finding → 修正 → 驗證 workflow（human-in-the-loop）

zoom 是 read-only（產 finding + 建議，不改 code）。後續修正 + 驗證用其他命令接力——human 在判讀 / 決策 / 確認介入：

| 階段 | 規模 | 命令 |
|------|------|------|
| 修正 | 輕量（文件 / 刪碼） | 對話 |
| 修正 | 大型（跨檔 / 邏輯） | `/implement`（Planning Contract／EP 驅動） |
| **品質閘門** | 所有 code 修正 | ruff + mypy + test（範例：`uv run ruff check --fix .` + `uv run mypy .` + `make test`）——確認 code 沒壞（純文件修正可跳過；action 修正必跑） |
| 驗證 | action 修正（刪碼 / 改邏輯） | `/followup-review`（對照 finding 驗收 + 機械查證 test / 副作用） |
| 驗證 | 輕量修正（文件） | 重跑 zoom（before/after：finding 消除 = 修對） |

報告 finding 標狀態（待修 / 不修 / 已修 / 已驗）追蹤跨階段。

## 執行約束 + 誠信約束

- **read-only**（偵測器，非判官）：只產 finding + 建議，不自動改 code（[audit-test](../audit-test/SKILL.md) stance）
- **推薦先行**：不給選項清單，給明確推薦 + 理由
- **查證必須**：inferred finding 必查證（LSP / rg）才報；未查標 `inferred ⚠️`（防 false positive——dogfood T1 教訓：未查就報「符號不存在」，rg 推翻）
- **撤銷透明**：查證推翻的 finding 標 ❌ 保留，不刪（示範誠信）
- **LSP stale 警告**：判死碼 LSP 回可疑少 → rg 補（[symbol-query-routing skill](../symbol-query-routing/SKILL.md)）
- **不重造機械**：死碼 → arch-thinking / LSP；測試反模式 → audit-test；severity / confidence → review-engine
- **預設 source + test 同審**；user 可明確排除——不強制，避免稀釋放大鏡焦點

## 設計脈絡（genesis）

前次設計死因是「分類軸思維 + token 牆 + 重造機械」（過度投資 AI 機械、欠投資人類產出）。本 mode 定位翻轉：**source 側的 audit-test**——借 audit-test 成熟範式（偵測器 stance + 問題/建議格式）+ 機械全委外既有 skill + 用戶判準封裝成 viewport。「人類產出格式優先」教訓為本 skill 兩 mode 共同設計依據。

## 流程位置

**user-driven 主動偵查入口**（非 canonical chain）。用戶想批判檢視既有 code → zoom 放大鏡。非 build / commit 流程節點（那是 code-review / audit-test）。重構前期研究場景：zoom（存在質疑）→ baseline（穩固度地圖）→ card Planning Contract／EP。

---

## Domain 層（判準 4/5 詳定義）

通用審查邏輯（severity / confidence / 審查者自證）在 [review-engine](../review-engine/SKILL.md)；測試反模式偵測在 [audit-test](../audit-test/SKILL.md)；本檔不重造，只補 zoom 獨有部分。

### 判準 4：質疑命名/設計（AI 產出的命名/設計盲點）

AI 寫 code 時犯三類命名/設計錯誤，zoom **預設質疑**（不假設 AI 命名正確）：

#### 4a 命名碰撞

符號名與既有概念碰撞，造成語義混淆。

- 機械：LSP `workspaceSymbol` 查同名候選 + 讀定義確認語義是否真相同
- 範例：domain class `CashAccount`（現金累算器）與 NT `AccountType.CASH`（帳戶類型）—— 同名不同概念，讀者混淆
- 判定：同名但語義不同 → finding（建議改名或文件標明區隔）

#### 4b domain 一致性（名稱反映涵蓋）

命名/設計與 domain 模型不一致——名稱宣稱的涵蓋範圍 ≠ 實際定義。

- 機械：讀 Protocol / 型別 / 介面定義，比對「名稱宣稱」vs「實際涵蓋」
- 範例：`RateLimiter` Protocol 只定義 sync CM，名稱卻宣稱通用 → 涵蓋缺口（消費者標註的 instance 可能是 AsyncRateLimiter，不符 Protocol）
- 判定：名稱過廣 / 過窄 → finding（建議改名 / 補定義 / 拆分）

#### 4c phantom API（AI 幻覺造的符號）— **限 source 側**

docstring / 註解 / 範例引用不存在的 method / class（AI 文檔幻覺）。

- **scope**：限 **source 側** docstring 幻覺；**test 側** docstring/assert 幻覺走 [audit-test](../audit-test/SKILL.md) 角度 1
- 機械：rg / LSP 確認 docstring 提及的符號真實存在（定義點 + import 鏈）
- 範例：`__init__.py` docstring 引用 `throttle_request()`（不存在的方法，AI 幻覺）
- 判定：docstring 提及符號不存在 → finding（建議修正 docstring）

> ⚠️ **查證陷阱（dogfood 教訓）**：查 phantom API **不能只查「符號在不在」**，要查「引用語意對不對」——符號存在但 docstring 放錯 class / 宣稱錯使用場景，仍是 finding（語意誤導，見 dogfood T4：符號 `_get_historical_bars_sync` 存在，但 docstring 放 `TestAsyncThrottle` 下暗示它是 throttle 使用，實際走 acquire）。

### 判準 5：mixed-tree scope framing（完全無既有承載）

> **review 面對 mixed working tree 怎麼 framing 結論**在 commit 視角工具之外完全無承載——本 mode 補此缺口（最大省 prompt 價值之一）。

mixed working tree = 多 session / 來源的變更混在同一 working tree。zoom 審某 scope 時，working tree 常有無關變更（其他 session、pre-existing、unstaged）。

#### 5a 分組（git status）

`git status` 看所有變更，按邏輯單元分組。

#### 5b 標明誰的變更

每組標「**本次審查標的**」vs「**混入的其他來源**」。

#### 5c 結論 framing 對應 scope

**結論只涵蓋審查範圍**，禁下全域結論。若 working tree 有未審變更，明確標「本次結論僅覆蓋 \<X\>，\<Y\> 未審」。

- 🔴 反例：`/code-review` 審 rate_limiter 子集，下「無 Critical」全域結論，但 working tree 有 `client.py`（production concurrency）未審 → `/judge-review` 才揭露
- ✅ 正解：標「無 Critical（**僅 rate_limiter 子集**）；`client.py` 未審，需另跑」

#### 5d scope 判定 checklist（操作準則）

1. **本次標的** = user 明確指定的 dir/files（參數）
2. **其他來源** = working tree 中不在本次標的的變更，進一步判定：
   - `git log --oneline -5 <file>` 看最近 commit author/timestamp——與本次 session 不同的 author 或近期 commit = 其他 session / 來源
   - `git diff HEAD <file>` vs `git diff --cached <file>`——staged vs unstaged 區分
   - 變更內容與本次標的無邏輯關聯（不同模組/功能）= 獨立來源
3. **處理**：其他來源變更不審（不在本次 scope），但在報告結論**最後列「未審清單」**（標明檔名 + 推測來源）
4. **禁下全域結論**：即使 working tree 全綠，也只能說「本次標的（X）無 Critical」，不可說「全部無 Critical」

## 編排 audit-test（test 側）

zoom 的 test 段聚焦**判準 2（收窄：production wrapper 重複測試）**，其餘隱含覆蓋 / 反模式委外 audit-test：

| zoom test 段做（判準 2 收窄） | 委外 audit-test |
|---|---|
| **production wrapper 重複測試**（測 thin wrapper，但 wrapper 本體已被別處測；**且 wrapper 無獨立 production 入口**）| 反模式（幽靈斷言 / 同義反覆 / 空殼）— 角度 1 |
| test 與 production 脫節（docstring 語意誤導）| 過時 / 死測試 — 角度 6 |
| —（其餘隱含覆蓋場景：同行為不同入口重複測等） | 反模式 / 過時死測試 / 測試必要性 — 角度 1 / 角度 6 |

**判準 2 收窄理由**：audit-test 域 1（反模式＋測試必要性）已覆蓋多數隱含覆蓋場景。zoom 判準 2 **真正獨有**的是「**production wrapper 重複測試**」判斷——測 wrapper 時要查 wrapper 是否有**獨立 production 入口**：

- 有獨立 production 入口（如 `throttle()` 被 production 直接呼叫）→ **保留**（覆蓋 production 路徑，非重複）
- 無獨立 production 入口（wrapper 只被 test 呼叫，本體已被別處測）→ **冗餘**（建議清除）

> 區分 audit-test 域 1 測試必要性：該節是「**動態過時**」（重構後 assertion 迎合實作）；本判準是「**production wrapper 重複**」（wrapper 無獨立入口）。語義不同。

## 誠信 stance（對 audit-test 的差異化）

zoom 不是機械列 finding（那是 audit-test），是**批判性追查**。基本約束見上方「執行約束 + 誠信約束」段（單一源）。本段承載 domain 獨有：

- **對抗性自查**：每個 finding 挑戰自己判斷（不放水，判準 3）
- **兩個查證陷阱（dogfood 實證，必記）**：
  1. **LSP-stale**：判死碼時 LSP `findReferences` 回可疑少（只 intra-file / 跨檔消失）→ 必須 rg 補（[symbol-query-routing skill](../symbol-query-routing/SKILL.md) 條件式 fallback）。dogfood 實證：`throttle()` LSP 只回定義點，rg 才見 production 消費者
  2. **符號路徑**：**符號存在 ≠ 走你想當然的路徑**。看到符號被引用，別假設它走你預期的路徑——**讀 body 確認**。dogfood 實證：`_get_historical_bars_sync` 符號存在且被 docstring 引用，初版假設它是 throttle 消費者；fresh-eyes 讀 body 才發現走 `async with`（acquire），不是 throttle
