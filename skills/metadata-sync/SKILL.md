---
name: metadata-sync
description: "metadata finalization 單一真相源 — build 後的文檔狀態結算(模組 Capabilities 寫入——AGENTS.md 為主、CLAUDE.md legacy、Kanban 搬 Done、SYSTEM-MAP 生命週期、architecture.md、EP 歸檔、flow-feedback 歸檔、導航文檔 /consistency 閘門)。三 mode(build 5a 依情境結算／收斂後結案／standalone 補漏)。被 /implement 階段5、/post-build hook 2（收斂後結案）、/metadata-sync 共用 invoke。觸發詞：metadata finalization、commit 收尾、Capabilities 同步、Kanban 搬 Done、EP 歸檔、SYSTEM-MAP 更新、architecture.md、漏掉 finalization、build 完更新文檔、flow-feedback 歸檔、文檔狀態結算。"
---

# Metadata Sync — metadata finalization 單一真相源

build 後的「文檔狀態結算」方法論（commit 不再內嵌 finalization）。把程式碼變更反映到專案導航文檔的**狀態層**(UC ✅、Kanban lane、SYSTEM-MAP 生命週期、EP 生命週期)——不是文檔「內容」同步(程式碼改 → 文檔描述改,那屬 [instruction-writing](../../rules/instruction-writing.md) 的職責,在 build 階段 5b 處理)。

**單一源**:本 skill 是 finalization 邏輯的唯一定義處。三個 invoke 點(build 階段 5 結算／收斂後結案／standalone 補漏)共用,消除「同一邏輯散落多處 → drift」。

## 三 mode(finalization 在 build 結算,commit 純提交)

| mode | 觸發者 | 職責 |
|------|--------|------|
| **build** | `/implement` 階段 5 | 依情境結算(見情境矩陣)—— 結算是 working tree 編輯,不需 outward-action-consent(commit 場景) |
| **收斂後結案** | `/post-build` hook 2（收斂點 invoke 本 skill 結案段；無 post-build 弧走 `/implement` 階段 6 fallback） | 僅結案段（backlog 結案兩步＋SYSTEM-MAP 升級＋EP 歸檔＋flow-feedback 歸檔） |
| **standalone** | `/metadata-sync`(獨立入口) | 偵測漏項/過時 → 補(commit 前更新 + 事後補漏共用;偵測 git 錨定見下方 standalone 段) |

> **build mode 零偵測**:build 是變更的 producer——EP 路徑、UC 清單、情境矩陣都在自己 context 內,結算項**由情境矩陣 + EP 內容直接推導**,不跑 standalone 的偵測流程(producer 不 rediscover 自己剛做的變更)。

> **為什麼結算在 build 不在 commit**:finalization 是 working tree 編輯(改 CLAUDE.md / mv EP / 搬 Kanban),不是 git 寫入 —— build 階段 5 自主做,commit 退回純 git 提交(一次帶走 code + finalization)。舊設計(commit 階段 3 內嵌)對 LLM 是建議性、會漏跑(實證:commit 歷史多個「補漏」單獨 commit)。working tree 編輯沒 commit 就不永久,跟 code 一起 stash/checkout,不會「Capabilities 標 ✅ 但沒進 git」不一致 —— 真正風險是選擇性 commit(只 commit code 不 commit CLAUDE.md),靠 commit `git add` 納入 finalization 檔規範。

> **UC 狀態流轉（自 guide 承接）**：✅→主要實作模組 Capabilities（同一 UC 一處，`能力|入口|狀態`，入口含 CLI＋函式）；🟢→附限制；❌→移出；📋/🔧→backlog To Do；🟡→In Progress；未承諾→drafts。scripts/ 是人類 demo，不放 Capabilities。

### 結算情境矩陣(build mode 核心 spec)

| # | 情境 | UC/EP 完成變化 | 結算動作 |
|---|------|--------------|---------|
| **A** | EP **最後段**,UC 全完成 | ✅ 新 UC + EP 完成 | **Built 結算（5a）**(Capabilities 寫入 + 消費場景寫入 + SYSTEM-MAP 預覽 + architecture.md(條件) + consistency)；**final 結案（收斂後——post-build hook 2／implement 階段 6 fallback）**(backlog 結案兩步＋弧結案蒸餾第三動 + SYSTEM-MAP 升級 + EP 歸檔 + flow-feedback 歸檔) |
| **B** | EP **中間段** | ❌ UC 未全完成 | **預覽 only**(SM 📋→✅ Built,不寫 ✅、不升 Verified) |
| **C** | **小型變更**（bug fix／單檔小 tweak，無新 UC） | ❌ | **跳過** Capabilities／Kanban 結算（純 refactor 不自動歸此——依規模，見 [implement](../implement/SKILL.md) 小型變更段） |
| **D** | **docs-mode EP**(無 .py UC,EP 完成) | EP 完成、無 UC | **EP 歸檔 only**(無 Cap/Kanban) |

> deep-work `/implement` 委派 build 全流程,繼承情境 A–D;deep-work 純 fix/debug(不走 build)= 情境 C 跳過。**code-review 後改 code**(UC 已結算過,入口可能變)= standalone mode 更新(冪等重跑);**事後發現漏結算** = standalone mode 補漏。

> **review identity 復用邊界（S4 對帳條款）**：review 證據身份吻合（[workflow-review-pattern](../_common/workflow-review-pattern.md) 帳本 header identity 三欄——scope／review_profile／coverage）**只授權復用 review 結論，不代表 metadata 結算已完成**——結算項仍逐項核對。**引用已完成結算項的前提**＝既有 EP 進度指向相同輸入內容、且結算產物仍在場（Capabilities 行／歸檔目錄／SYSTEM-MAP 狀態可實際核對）；無法核對 → 由本 skill 對適用項**冪等重跑**，不以「review 過了」推導「結算過了」。

## finalization 項目(build mode 依情境執行子集)

| 項目 | 情境 | 做什麼 |
|------|------|--------|
| **Capabilities 寫入** | A（時點＝5a） | 對應模組 instruction 檔（AGENTS.md 為主，legacy CLAUDE.md）`## Capabilities` 表格新增 ✅ 行(格式 `\| 能力 \| 入口 \| 狀態 \|`,入口含 CLI + 函式路徑;UC 狀態流轉見本檔前述承接註記) |
| **消費場景寫入** | A（時點＝5a） | 從 EP Scenario Matrix 提煉引用該 UC 的場景為自包含一句話(不引用 EP/SM 編號),寫入 Capabilities 備註或 backlog 卡(`backlog task edit <id> --append-notes`) |
| **backlog 結案** | A（時點＝收斂後） | 已完成 UC 的卡結案兩步＋弧結案蒸餾第三動（本弧 memory 條目終態化）：`task edit <id> -s Done --final-summary` → `--ref` 換 `done/` 新 URL，卡留 Done 欄（命令合約見 [kanban-board](../kanban-board/SKILL.md)） |
| **SYSTEM-MAP 結算** | A（時點＝收斂後） | 受影響功能生命週期升級(`✅ Built → ✅🔍 Verified`,若有整合驗證);移除已修復 ⚠️;更新全域統計(若有) |
| **SYSTEM-MAP 預覽** | B | 中間段:生命週期 `📋→✅ Built`(全 UC ✅ + 測試通過 + build loop 收斂);**不升級 Verified**;loop 未收斂 → 阻止升級 + 標 ⚠️;**全域統計由情境 A 結算,預覽不動** |
| **architecture.md** | 任何情境（內容條件——不綁情境 A；ai-guide 本 repo 無此檔，主服務消費端 repo） | 涉及設計決策／原則／模組結構／新抽象層 → 同步更新對應段落（refactor 弧主觸發面）；純 feature（不改設計）跳過 |
| **EP 歸檔** | A, D（時點＝收斂後） | **歸檔前查證（防 ghost-done）**：列 EP 交付物（UC盤點/收尾/各段 deliverable）逐項 rg/fd/Read 驗落地——「段落完成」≠ codebase 真有（曾發生整份 EP 100% ghost-done 誤歸檔）；有 ghost-done 不歸檔（補做或標 🔧）。全綠才歸檔 → **task 目錄整搬**（目錄級非單檔 mv；EP/spec/Report Shell 同目錄一起走）至 **任務家下 repo 既有歸檔慣例**：任務家探測（`ai-analysis/_tasks/` 在場→雜項家；線任務 EP→`ai-analysis/_projects/<線>/`、歸檔落同線 `done/`；否則 repo-root `00-tasks/`），其下探測 `done/` 或 `_done/`（含 `_done/<YYYY>/` 年分層——存在則搬入當前年層）任一存在者沿用，兩者並存沿用最近歸檔落點；皆無 → 建任務家下 `done/`（跨專案 skill 不 hardcode 單一歸檔形態——曾 hardcode `_done/<YYYY>/` 與消費端 `done/` 慣例漂移，照 skill 走會建出第二歸檔目錄；舊 `ai-analysis/execution-plans/` 慣例退役）;綱要 EP(blueprint)等所有衍生子 EP 完成才歸檔 master |
| **flow-feedback 歸檔** | A（時點＝收斂後） | 本次實作解決的 `ai-analysis/flow-feedback/*.md`(root)→ `mv _done/`(`_done/` 不存在先建);討論中 / 未解決的不歸檔。**判斷是 judgment 非機械**(feedback↔change 非 1:1,不像 EP↔段落明確)→ forgetting 風險靠兩段式執行的「展示清單 + 用戶確認」把關(同 standalone mode) |
| **consistency 閘門** | A, B, D | 對本次動過的 AGENTS.md / CLAUDE.md / architecture.md / SYSTEM-MAP.md 逐一跑 `/consistency`(單檔內部自洽);🔴 / 🟡 inconsistency → 修正後才算完成 |

### SYSTEM-MAP 生命週期推導(共用規則)

| 條件 | 狀態 |
|------|------|
| 功能內 UC 全 ✅ + 有整合驗證 | ✅🔍 Verified |
| 全 ✅ 但無整合驗證 | ✅ Built |
| 有 📋 / 🔧 | ⚠️ Issues 或 📋 Planned |

build 情境 A 憑整合驗證升 Verified;情境 B(中間段)只到 Built 預覽。

## standalone 偵測(git 錨定,獨立入口核心智能)

`/metadata-sync`(standalone mode)用於 **commit 前更新**(code-review 後 code 變了)或**事後補漏**。`--check` flag = 只跑兩段式第 1 步(偵測 + 報告),不執行

> **偵測入口 = git 事實,非倉庫掃描**。漏項是 delta 問題——用事件(git 變更)推狀態,不從倉庫快照反推(實測教訓:無錨點偵測以 `ls` 全目錄 + `rg` 內容掃描起頭,數十 call 收斂不了)。git 錨定 = 1-2 個 call 得變更檔集,掃描 = O(全倉文件) 猜測。

**第一步——變更檔集(情境選一)**:

| 情境 | 命令 |
|------|------|
| commit 前(uncommitted) | `git status --porcelain` + `git diff --name-only`(含 `--cached`) |
| 事後補漏(committed) | `git log --oneline -15 --name-only` |

**第二步——路徑模式分類(變更檔集 → 命中項,只驗命中項;未命中 = 該項跳過)**:

| 漏項 | 觸發訊號(變更檔集模式) | 窄驗證 |
|------|----------------------|--------|
| EP 歸檔漏 | EP 段落交付物已 commit(code/test)且任務家對應 task 目錄仍未歸檔（未搬歸檔目錄） | `fd -e md -E done -E _done . <任務家>`（存在的任務家：`ai-analysis/_tasks/`、`00-tasks/`；線任務另查 `fd -e md . ai-analysis/_projects/*/tasks/`）比對已交付未歸檔 |
| Capabilities 漏 | feat/fix commit 觸及模組目錄,但該模組 AGENTS.md(CLAUDE.md legacy)不在變更檔集 | 讀**該模組** AGENTS.md Capabilities 表比對(窄讀) |
| backlog 漏 | Capabilities 漏命中 | `backlog task list --json` 比對命中 UC 卡仍非 Done（無 `backlog/` 跳過） |
| SYSTEM-MAP 漏 | Capabilities 漏命中 | 消費 `/doc-health` findings(不重造偵測) |
| architecture.md 漏 | commit 觸及新模組/新抽象/依賴方向,且 architecture.md 不在變更檔集 | 讀對應段落窄比對 |
| flow-feedback 漏 | 修復型 commit(fix) | `ls ai-analysis/flow-feedback/*.md`(單 call) |

**禁令**:偵測段禁全倉內容掃描(無路徑限定的 `rg`)與逐檔讀——一切從變更檔集出發。ghost-done 歸檔前查證(EP 交付物逐項驗落地,任一 mode)是**執行段**查證,不屬偵測段、不受此禁令影響。

## 兩段式執行(三 mode 共用)

1. **偵測 → 展示清單**:build mode 依情境矩陣列該做的結算項；收斂後結案 mode 列結案段四件；standalone mode 列漏項/過時項
2. **用戶確認**:standalone mode 遵循 [outward-action-consent](../../rules/outward-action-consent.md) 精神獨立確認；build mode 免確認（授權來源＝EP 已批准＋finalization consent 單一 owner＝build 流程——流程內機械結算不另確認）；**收斂後結案 mode**——機械結算三件（backlog 結案兩步／SYSTEM-MAP 升級／EP 歸檔）免確認（授權＝EP 已批准＋收斂 gate 已過），**flow-feedback 歸檔屬判斷型結算、保留獨立確認**（與 :48 flow-feedback 判斷 gate 同義）
3. **執行**:寫入 / 搬移 / 歸檔
4. **consistency 閘門**:對動過的導航文檔跑 `/consistency`

> **原子性**:build 情境 A 分兩時點原子——5a Built 結算三件「Capabilities 寫入 + 消費場景寫入 + SYSTEM-MAP 預覽」同時；收斂後 final 結案四件「backlog 結案兩步 + SYSTEM-MAP 升級 + EP 歸檔 + flow-feedback 歸檔」同時（各時點內部分完成 = 狀態不一致誤導 LLM）。architecture.md 更新 / consistency 閘門隨 5a（各自獨立條件時序，與三件平行）。standalone 補漏/更新不要求原子(補的是各自獨立的漏項)。

## 容錯(三 mode 共用)

無對應檔案 → 該項跳過不報錯(容錯是方法論的一部分,定義於此單一源,三 mode 共用):

| 缺漏 | 跳過項 |
|------|--------|
| 無 SYSTEM-MAP.md | SYSTEM-MAP 預覽 / 結算(如 ai-guide 元專案無 SYSTEM-MAP) |
| 無 `backlog/` | backlog 結案兩步（卡層動作全跳過） |
| 無 architecture.md | architecture.md 條件更新 |
| 無 `ai-analysis/flow-feedback/` | flow-feedback 歸檔 |

> 容錯定義僅此一處（單一源）。

## 與既有邊界

- [`/doc-health`](../doc-health/SKILL.md):**檢查 / 報告**(問「文件準確嗎」),消費 scan findings + LLM 讀取驗證,含 `--sync-system-map`。本 skill 是**執行修補**(問「finalization 該做的做了嗎,沒做就補」)。SYSTEM-MAP 偵測消費 doc-health findings,不重造。
- [`/consistency`](../consistency/SKILL.md):**單檔內部自洽**(術語 / 章節 / 引用 / 邏輯 / 格式)。本 skill 的 consistency 閘門 invoke 它,非重造自洽邏輯。
- [`kanban-board`](../kanban-board/SKILL.md):看板卡片**通用 CRUD 工具**。本 skill 的「Kanban 搬 Done」是綁定 build 結算語意的特定操作(可用 kanban-board 的移動能力執行)。
- [`/audit-test`](../audit-test/SKILL.md):**測試品質**稽核(反模式 / 覆蓋 / mock)。與文檔 metadata 正交。
- build 階段 5b(instruction 檔 / arch **內容**同步):反映程式碼變更到文檔描述(導航-A 種子、模組職責),屬 [instruction-writing](../../rules/instruction-writing.md) 職責,**非**狀態結算;與本 skill 結算在同一段 5 協調(5a 結算寫 ✅ 行、5b 同步描述)。

## 不適用

- 文檔**內容**同步(程式碼改 → 描述改)→ build 階段 5b + [instruction-writing](../../rules/instruction-writing.md)
- 單檔內部自洽檢查 → `/consistency`
- 文件準確性 / 過時 / drift 報告 → `/doc-health`
- 看板通用操作(非 build 結算)→ `kanban-board`
