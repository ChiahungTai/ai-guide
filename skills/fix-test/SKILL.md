---
name: fix-test

description: "測試失敗修復＋Python lint/type 自動修正（ruff/mypy）— 先分類再修復，防止盲目讓測試通過；lint/type 修復 recipes 見 lint-type-recipes.md"
when_to_use: "Fix failing tests with first-principles classification. Use when tests fail after refactoring, implementation changes, or when pasting test failure logs. Also use for Python lint/type fixes — ruff format, ruff check --fix, mypy auto-fix and type-convention repair."
argument-hint: "可貼測試失敗 log。無參數時自動從 git 變更推斷受影響的測試"
allowed-tools: ["Read", "Edit", "Bash", "Grep", "Agent"]
---

# /fix-test — 測試失敗分類修復

測試失敗不是「讓它通過就好」。重構頻繁的專案中，測試失敗可能代表**程式碼有 bug**，也可能代表**測試該重寫**。本命令強制分類後再修復。

> **lint/type 修復**（前身 `/lint-fix` skill，AIR-113 reference-demotion 併入）：ruff 三步與 mypy 型別問題分析 recipes 見 [lint-type-recipes](lint-type-recipes.md)。

委託 Skills（需要深度 debug 時按需載入）：
- [debugging-and-error-recovery](../debugging-and-error-recovery/SKILL.md) — 系統化 root cause 診斷（Type A 適用）
- [test-driven-development](../test-driven-development/SKILL.md) — 測試撰寫方法論（Type B/C 適用）

---

## 核心原則

**先分類，再修復。未經分類的修復是盲目的。**

LLM 遇到測試失敗時的預設偏誤是「讓測試通過」。本命令強制在修復前先判斷：**是程式碼錯了，還是測試過時了？**

---

## 執行流程

### 階段 0：Context Gathering

兩種模式：

**模式 A — 用戶已貼 failure log**：
- 解析失敗測試名稱和錯誤訊息
- 若用戶未提及變更範圍，從 `git diff HEAD~1` + uncommitted diff 推斷源碼變更
- 直接進入階段 2

**模式 B — 未貼 log，從 git 推斷**：
1. 分析 uncommitted changes（`git diff HEAD` + `git diff --cached`）和 last commit（`git diff HEAD~1`）
2. 識別變更的 source 檔案 → 推斷對應 test 檔案（同名慣例：`foo.py` → `test_foo.py`）
3. 輸出推斷結果，詢問用戶：
   - 推斷的測試範圍是否正確？
   - 是否要加減測試檔案？
   - 確認後進入階段 0.5（無哨兵無病歷的冷啟動會自然落到階段 1）

### 階段 0.5：Triage（哨兵＋病歷＋仲裁）

全重跑一遍才分類是浪費，lastfailed 照單全收是誤判。先 triage，再決定跑什麼。模式 A（用戶已貼 log）跳過本階段，直接階段 2。

**三層分工**：

| 層 | 角色 | 給什麼 | 不給什麼 |
|----|------|--------|----------|
| 哨兵（sentinel） | 只決定「看哪裡」 | 待查 node ID 清單 | 失敗理由、是否仍紅 |
| 病歷（record） | 給失敗理由和歷史 | 理由＋歷史＋baseline 比對（先讀它） | — |
| 重跑 | 只做兩件事 | ① 修完驗證 ② 哨兵和病歷對不上時仲裁 | 平時不跑 |

- **哨兵**：`.pytest_cache/v/cache/lastfailed` 或 IDE 紅單（如 VSCode TestResults）。限制：每次 run 蓋寫；改名／刪除後舊 node ID 變殭屍（指向空氣）；不代表仍紅。
- **病歷**：project 的持久化失敗記錄（含 failures[]＋baseline 比對）。**路徑是 project 慣例，本 skill 不寫死**——project 在自己的 AGENTS.md 聲明路徑與格式（如 mosaic：`~/.mosaic/logs/ops/test-regression-<date>-findings.json`）。無病歷慣例的 project 跳過此步，只做哨兵＋仲裁。
- **IDE 結果無檔案落地時**（如 VSCode TestResults 住 extension host 記憶體）：人機想看同一份結果，在同一 run 加 `--junitxml=<path>` 落一檔，把路徑給 AI。junitxml 只給共享視圖（ID＋pass/fail＋耗時），分類仍要 `--tb=short` 的 traceback；opt-in，非必備。

**步驟**：
1. 讀哨兵 → N 個候選 ID。
2. 讀病歷（若有）→ 每個 ID 的理由＋歷史。
3. 對照分三種命運：
   - 確認紅 → 進入階段 2 分類（A/B/C/D/E）。
   - 已自癒 flaky（病歷顯示間歇／歷史曾過）→ 不修，記一筆；病歷模糊才仲裁。
   - 殭屍（該 ID 已 collect 不到：改名／刪除）→ 用 `pytest --collect-only -q` 或查檔確認，直接丟棄，不重跑。
4. 哨兵和病歷對不上（哨兵有而病歷無理由、病歷有而哨兵無、flaky 反覆上榜）→ 只重跑這 M 個仲裁：`uv run pytest <node IDs> -v --tb=short`。其餘不跑。

**強制輸出 line**（triage 結束必須先報這行，再進階段 1/2）：

```
TRIAGE: sentinel N, record <各ID理由一句>, arbitration M: <node IDs or "none">
```

### 階段 1：Run Tests（只跑 triage 沒覆蓋的）

- 階段 0.5 已仲裁 → 直接用仲裁結果，不再重跑。
- 無哨兵無病歷（如模式 B 從 git 推斷的冷啟動）→ 才跑 `uv run pytest <targets> -v --tb=short`。
- 捕獲完整輸出（含 traceback）；識別所有 FAILED；無失敗 → 報告通過，結束

### 階段 2：Failure Classification（核心）

對**每個**失敗測試，執行以下分析：

1. **讀取測試碼** — 理解測試的意圖（測的是什麼行為？）
2. **讀取變更的源碼** — 理解最近的契約變化（API 改了什麼？）
3. **分類** — 根據下方標準判斷類型
4. **附理由** — 為什麼是這個類型而非其他

#### 五類失敗分類

| 類型 | 名稱 | 判斷標準 | 行動 |
|------|------|----------|------|
| **A** | 實作缺陷 | 新改的 code 邏輯有錯，測試正確抓到問題 | 修程式碼 |
| **B** | 契約變更 | 重構改了 API 簽名、回傳型別、行為語意（舊意圖在新系統仍有效），測試仍用舊契約 | 重寫測試 |
| **C** | 測試腐化 | 測試耦合實作細節（private method、內部狀態、排序依賴），非行為面的 | 重寫測試 |
| **D** | 基礎設施 | Import error、fixture 過時、conftest 缺設定、path 問題 | 修測試基礎設施 |
| **E** | 測試過時 | 行為已合理改變，測試驗證的舊意圖在新系統不再適用 | **刪除或標記 deprecated**（非重寫迎合） |

#### 分類決策樹

```
測試失敗
├── 是 import error / fixture error / setup error？
│   └── YES → Type D（基礎設施）
├── 變更了 API 簽名或回傳型別？
│   ├── 測試使用舊簽名 → Type B（契約變更）
│   └── 測試使用新簽名但結果不對 → Type A（實作缺陷）
├── 測試耦合實作細節（private、內部狀態）？
│   └── YES → Type C（測試腐化）
├── 重構改了行為語意（同一函式，不同語意）？
│   ├── 舊意圖在新系統仍有效 → Type B（契約變更，重寫驗證新契約）
│   └── 舊意圖已失效 → Type E（過時，刪除/deprecated）
└── 以上皆非 → Type A（實作缺陷）
```

#### Type B/C 重寫的強制要求

> **重寫前必須先通過必要性審查**：這個測試驗證的意圖，在重構後的系統中仍然有效嗎？若**否 → 歸類 Type E（刪除/deprecated），而非重寫迎合**。重寫測試去配合新實作，是把測試從「驗證意圖」降級為「反映實作」 — 過時測試比沒測試更危險（虛假信心）。刪除過時測試是正解，不是偷懶。理論見 [acceptance-evidence](../../rules/acceptance-evidence.md)「證據時效性」。

**Type B（契約變更）** 必須回答：
- 舊契約是什麼？（測試原本期望的行為）
- 新契約是什麼？（重構後的實際行為）
- 新測試如何驗證新契約？

**Type C（測試腐化）** 必須回答：
- 測試耦合了哪些實作細節？
- 正確的行為面測試應該測什麼？
- 新測試如何只測行為不測實作？

**Type E（測試過時）** 必須回答：
- 測試原本驗證的意圖是什麼？
- 為什麼這個意圖在新系統不再適用？（行為如何合理改變）
- 刪除是否遺漏仍有價值的斷言？（若有 → 拆出保留，其餘刪除）

#### Mutation authority gate（v3.1 測試契約——測試對應凍結 TC 時）

> 掛點：階段 2 分類後、階段 3 確認前。Type B/C/E 的行動（重寫/刪除）都是**改測試側 truth**——凍結 TC 在場時，改 truth 需 authority，非分類完成即可動手。本 gate 是後掛檢查，不改道決策樹（分類仍照上方樹走）；escalation 是 signal，最終裁決在人類確認（階段 3）。

測試對應 EP 凍結 TC（TC-ID 可對上）時，Type B/C/E 判定後強制過本 gate：

1. **查 authority**：變更理由屬 amendment authority 四分哪類？（四分定義見 [execution-plan](../execution-plan/SKILL.md) 測試規劃段 amendment 附錄——本處引用，不重列映射）
2. **「實作現況」作為重寫/刪除理由 → 擋下**：「實作現況」永遠不是證據——指向 amendment（走 execution-plan amendment 附錄：old/new oracle＋reason＋independent evidence＋authority），非就地改測試迎合
3. **無凍結 TC**（舊 EP/存量測試）→ gate 跳過，沿用現行必要性審查（Type B/C 重寫強制要求不變）

互掛：[implement](../implement/SKILL.md) 撞牆（GREEN 期想改 frozen test）的出口指向本 gate；本 gate 的 amendment 出口指向 execution-plan 附錄。

### 階段 3：Present + Confirm

**所有類型（A/B/C/D/E）都須用戶確認後才動手。**

輸出格式：

```
## 測試失敗分類報告

### 摘要

| 測試 | 類型 | 行動 | TC escalation | 說明 |
|------|------|------|------|------|
| test_xxx | A（實作缺陷） | 修程式碼 | — | ... |
| test_yyy | B（契約變更） | 重寫測試 | TC-7／gate 過（authority 已判定，類別見四分） | 舊：... → 新：... |
| test_zzz | C（測試腐化） | 重寫測試 | TC-7／gate 擋下→amendment | 耦合了 ... |

**TC escalation 欄**（v3.1；Type B/C/E 且測試對應凍結 TC 時填）：對應 TC-ID＋mutation authority gate 判定結果（authority 類別／擋下轉 amendment）；Type A/D 或無凍結 TC 填「—」。**escalation 是 signal 不是自動判決**——人類確認時一併裁決。

### 建議執行順序
1. [先修哪個，為什麼]
2. [再修哪個]

確認後開始修復？(y/n/調整)
```

### 階段 4：Execute + Verify

按確認的順序執行修復：

- **Type A**：修程式碼，不改測試。修完跑測試確認通過。
- **Type B/C**：重寫測試。必須先說明新測試的意圖，再撰寫。跑測試確認通過。
- **Type D**：修基礎設施（conftest、fixture、import）。跑測試確認通過。
- **Type E**：刪除或標記 deprecated（先確認無仍有價值的斷言可拆出保留）。跑受影響測試確認無殘留引用。

每個修復完成後立即驗證該測試。全部完成後跑一次受影響的完整測試套件（背景跑）。

### 階段 4.5：Twin Sweep（每修完一個缺陷後強制）

每完成一個修復並驗證通過後，立即執行本階段（嵌入階段 4 的 per-fix loop 內），再進行下一個修復。搜尋同類缺陷的其他位置。單點修復不是完成。

**強制輸出 line**（必須出現於修復報告）：

```
TWINS: searched <pattern> - found <N> other sites: <files, or "none">
```

- **pattern**：剛修的錯誤構造（rg/LSP 搜尋的精確 pattern）
- **N=0**：完成
- **N>0**：列出位置；建議是否一併修（同一 commit 或分拆由用戶決定）

**搜尋工具**：符號查詢 cr-first（cr `refs`；缺場 LSP `findReferences`）；文字 pattern 用 rg（工具選擇見 [symbol-query-routing](../../rules/symbol-query-routing.md)）。

**pattern 範例**（依 fix-test 失敗類型）：

| 類型 | pattern 範例 | 搜尋目標 |
|------|-------------|---------|
| A 實作缺陷 | `rg "if x is None:"`（應為 `is not` 的邏輯翻轉） | 同類邏輯錯誤 |
| B 契約變更 | `rg "<old_signature>"`（舊 signature 殘留） | 其他用舊契約的 caller |
| C 測試腐化 | LSP `findReferences` on private method | 其他耦合同 private 的測試 |
| D 基礎設施 | `rg "fixture_<name>"` 或 `rg "conftest"` | 同類 fixture 過時 |
| E 測試過時 | `rg "@pytest.mark.<marker>"`（標記的過時意圖） | 其他同類過時測試 |

**與 acceptance-evidence filter trap 的差異**：filter trap 是反向（移除補丁前查 caller 是否阻斷 case）；TWINS 是正向（修缺陷後查同類）。方向相反、正交不衝突（工具重疊但用途不同），並列使用。

---

## 禁止行為

- ❌ 偷改 assertion 數值或字串讓測試通過（未理解契約變更就改 assertion = 盲目修復）
- ❌ 用 `@pytest.skip`、`@pytest.mark.xfail`（非 strict）壓制失敗 — strict 釘住已知 bug 是 TDD red 機制（非壓制），見 [test-driven-development](../test-driven-development/SKILL.md)
- ❌ 放寬 assertion（`==` → `in`、移除檢查項、`assertAlmostEqual` 替代 `assertEqual`）
- ❌ 改 test setup 繞過失敗路徑（改 fixture 只為了避開報錯的 code path）
- ❌ 只改測試碼但不理解契約為什麼變了
- ❌ 跳過分類直接修復
- ❌ 拿到紅單（lastfailed／IDE TestResults）就全量重跑一遍才分類（先走階段 0.5 triage）
- ❌ 把 lastfailed 照單全收當失敗理由（它是哨兵，不是病歷）

---

## 與其他命令的協作

```
/refactor 或手動重構 → 測試失敗 → /fix-test（含 lint/type 修復——recipes 見 lint-type-recipes.md）→ /commit
/implement 段落驗證失敗 → /fix-test（分類後決定修 code 或修 test）
```

---

## 品質檢查清單

- [ ] triage 先報 `TRIAGE:` line（哨兵 N、病歷理由、仲裁 M），無全量重跑
- [ ] 每個失敗測試都已分類（A/B/C/D/E）
- [ ] Type B/C 有說明新契約或正確行為
- [ ] 用戶確認後才開始修復
- [ ] 每個修復後都驗證該測試通過
- [ ] 全部修復後跑完整受影響測試套件
- [ ] 修復報告含 `TWINS:` line（階段 4.5）
- [ ] 未使用任何禁止行為
