# EP: memory 卡資訊生命週期閘門——commit 對帳腿＋開卡登記腿

> **ep_type**: implementation（docs mode——product 全為 instruction/documentation 檔）

baseline: 3a264e6

## 實作總覽

**痛點**：memory 池的卡相關流水（弧狀態快照、git 可推導內容）在結案時靠「弧結案蒸餾第三動」（kanban skill 條文）清理——**流程自覺、無機械保證**。存量實證：21 條 `project_*` 條目（合計 ~130KB）＋6 檔含結案未清流水詞（「殘餘 commit 待確認」類）。desc 是開場載入層——過期快照不只膨脹，還**主動誤導**（09-05 過期派發事故根因之一＝「memory desc 舊教義開場持續灌輸」）。

**缺口本質**（arch-thinking）：commit 2.8 finalization 對帳閘門只掃 git 範圍（backlog/任務家）——memory 池在 repo 外掃不到；「有沒有做蒸餾」是單一入口機械可查（掃卡 id 殘留），正是閘門形態的合法位（hook vs LLM 分工律：語義壓縮＝LLM，存在性對帳＝機械掃描＋LLM 判歸屬）。

**掃描鍵洞（review F1）**：卡 id 是弱鍵——21 條 `project_*` 中 11 條完全不含 `AIR-` 字串（無卡弧〔handoff brief 即工單〕、弧自有條目不 literal 寫 id）——掃描鍵必須是「卡 id ∪ EP 登記清單 ∪ 弧主題詞」的聯集，兩腿共享資料非只共享詞形。

**解法＝閉環補兩腿**（既有四機制不動）：

| 層 | 機制 | 形態 | 狀態 |
|----|------|------|------|
| 流入 | 寫入六問首問「任務終態→卡不進 memory」 | LLM 流程＋尺寸 hook | 既有 |
| 登記 | **開卡時同主題 memory 條目盤點** | EP UC 盤點掃描＋輸出行 | **本弧 S2** |
| 出口 | 弧結案蒸餾第三動 | LLM 流程 | 既有（kanban skill） |
| 保證 | **commit 2.8 memory 對帳腿** | 機械掃描列命中＋LLM 判歸屬 | **本弧 S1** |
| 存量 | 夜波收斂／audit 層 4 | gate 驅動波段 | 既有（不清存量，EP 記指針） |

**跨 repo 邊界**：memory 池路徑 per-project（如 `~/.zcode/cli/memories/projects/<id>/memory/`）——條文寫「memory 池（本專案池，路徑見 memory-audit skill 適用載體段）」不 hardcode 完整路徑（跨專案 skill 慣例）。

## UC 盤點

### Backlog 關聯
- AIR-37（本弧追蹤卡，已建已 commit 3a264e6）
- 前弧脈絡：AIR-25（memory 系統矯正——寫入六問/desc 契約/結案蒸餾制度化）、AIR-14（Backlog 治理——結案兩步＋蒸餾第三動條文所在）、AIR-27（generator errs 路徑）——皆 Done，本弧在其上補保證層

### SYSTEM-MAP 影響
- 無（元專案無 SYSTEM-MAP.md）

### 掃描範圍
- 變更面：`skills/commit/SKILL.md`（階段 2.8 段）、`skills/execution-plan/SKILL.md`（UC 盤點步驟 3 段）
- 引用面：`skills/kanban-board/SKILL.md`（結案蒸餾第三動條文——被引用不修改）、`skills/memory-audit/SKILL.md`（寫入端紀律/層 4——被引用不修改）

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| 弧結案蒸餾第三動 | ✅ | kanban skill 結案兩步段 | 更新（被互指） | 加反向 pointer 到 commit 2.8？——最小改動判定：不加（2.8 單向引用即可，蒸餾方法論單一源不動） |
| commit finalization 對帳閘門 | ✅ | commit skill 階段 2.8 | 更新 | 加 memory 池對帳腿 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| memory 卡流水結案機械對帳（卡 id 掃描→三分歸屬→流水當場蒸） | 📋 | skills/commit/SKILL.md（2.8）＋skills/execution-plan/SKILL.md（UC 盤點） |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 弧結案 commit | 卡 Done＋commit 進行（2.8 閘門） | 本次弧卡 id `rg` 掃 memory 池 → 命中列清單 → 三分歸屬 → 流水項結案蒸餾當場做 | 無 | memory 卡流水對帳 |
| SM-2 | 開卡（EP UC 盤點） | execution-plan 建卡流程 | 同主題 memory 舊條目掃描列入 EP「UC 盤點」輸出（標「結案蒸餾範圍」） | 無 | memory 卡流水對帳 |
| SM-3 | 命中是活知識錨 | 教訓索引（「AIR-24 式」引用） | 三分歸屬＝保留——錨是合法引用非流水 | 無 | — |
| SM-4 | memory 池零命中 | 小弧無 memory 互動 | 閘門快速通過（命中清單空，報告標「零命中」） | 無 | — |
| SM-5 | 命中屬他弧條目 | 弧間互引（一條目可含 10 處他弧 AIR 引用）；跨 WT 同池 | 歸屬他弧且 owner 線未結案 → **保守不動**（不看天數看結案態——慢弧 >7 天活躍不掉出排除分支），列清單標註 | 無 | — |
| SM-6 | mid-arc commit | 逐段 commit（弧未結案）時 2.8 跑到本弧 in-flight 條目 | **結案態前置**：卡未 Done／結案兩步未執行 → 標「活躍弧 in-flight——不動」（對齊 memory-audit「進行中弧線禁加段、等收案一次性蒸餾」），不觸發當場蒸 | 無 | memory 卡流水對帳 |
| SM-7 | memory 池不存在 | 無 auto memory 池的專案（commit skill 跨專案通用） | 報告標「無 memory 池，跳過」——閘門執行證據仍輸出 | 無 | — |

## 段落劃分原則

定義源（commit 2.8 腿）先行，登記腿（UC 盤點）隨後，收尾獨立。docs mode：修改要點替代 Pseudo Code、驗證為文檔驗證。

---

## S1：commit skill 2.8 memory 對帳腿（出口保證——定義源）

### Context
- **UC 引用**：實作「memory 卡流水結案機械對帳」
- 現行 2.8 段（`skills/commit/SKILL.md` 階段 2.8）：機械掃 `git status --porcelain` 對 finalization 路徑面——三列表（結算物納入/並行活躍排除/孤兒結算收編）＋半套歸檔偵測。**盲區：memory 池 repo 外、git 掃不到**——弧結案蒸餾（第三動）做了沒不可考
- **依賴關係**：S2 的登記語義依賴本段三分歸屬詞形定稿
- **語義約束**：與 S2 共享「三分歸屬」詞形（活知識錨保留／弧流水蒸餾／終態 facts 過）；與 kanban 蒸餾第三動、memory-audit 寫入端紀律的分工＝**方法論單一源在彼、閘門觸發在此**（引用不重抄）
- **基礎設施盤點**：commit skill 2.8 段（`:2.8` 標題至階段 4 前）；kanban skill 結案兩步段（被引用）；memory-audit 寫入端紀律段（被引用）
- **依賴錨點**（文檔錨點，rg 驗證）：`skills/commit/SKILL.md` 2.8 表格與「半套歸檔偵測」段；`skills/kanban-board/SKILL.md`「弧結案蒸餾（第三動）」行

### 修改要點（docs mode）
1. 2.8 表格後新增 **memory 池對帳腿**小節（與半套歸檔偵測並列）：
   - 機械掃描：**掃描鍵聯集**＝本次弧卡 id（建卡 id ∪ staged diff／branch 名內卡 id——**2.8 時點 commit message 尚未生成，非掃描源**）∪ 本 EP「UC 盤點」登記的「結案蒸餾範圍」條目路徑（S2 產出——登記清單是本閘門的掃描輸入）∪ 弧主題詞；`rg` 本專案 memory 池（形態例：`~/.zcode/cli/memories/projects/<id>/memory/`——ZCode 池為 symlink 至 Claude 實體池，兩端同一份）——含 desc 投影（MEMORY.md）與條目檔；**池不存在 → 標「無 memory 池，跳過」**（執行證據仍輸出）
   - **結案態前置**（三分歸屬前；前置讀取＝`backlog task view <id> --plain` 取卡狀態，無 backlog CLI → 保守視為未結案）：卡未 Done／結案兩步未執行（mid-arc commit）→ 命中條目標「活躍弧 in-flight——不動」（進行中弧線禁加段、等收案一次性蒸餾——memory-audit 既有政策），不觸發當場蒸
   - 命中三分歸屬（LLM/user 判，同 2.7「機械掃描＋逐項處置」模式）：**活知識錨**（教訓索引——「AIR-24 三防線」式）→ 保留；**弧流水**（狀態快照、進度、git 可推導內容、「殘餘待確認」類過期詞）→ 結案蒸餾當場做（方法論＝kanban 蒸餾第三動）；**已是終態 facts** → 過
   - 報告附命中清單＋歸屬判定（零命中也標——閘門跑過的證據）
   - 並行排除：命中條目歸屬他弧且 owner 線未結案 → 保守不動、列清單標註（並行原則）
2. **單一源紀律**：蒸餾怎麼做（寫入即蒸後形/刪 git 可推導）不在 2.8 重抄——一句指向 kanban 蒸餾第三動＋memory-audit 寫入端紀律
3. **`skills/CLAUDE.md` commit 行 2.8 枚舉同步**（review F4）：既有枚舉「finalization 對帳〔2.8：半套歸檔偵測、「commit 確認」pre-commit 無 hash 結算〕」補「memory 池對帳腿」

### 驗證策略（docs mode）
- rg 條文在場：`rg "memory 池對帳|三分" skills/commit/SKILL.md` 命中
- 單一源不重抄：2.8 新段**不含**「刪日期流水/蒸後形」等蒸餾方法論細節（那些詞只在 memory-audit/kanban）——rg 對照
- 跨檔詞形：與 S2 完成後 `rg "結案蒸餾範圍|三分"` 兩檔對齊
- 單讀可執行：未載入背景的 session 讀 2.8 能執行（知道掃什麼、怎麼判、流水找誰的方法論）

---

## S2：execution-plan UC 盤點登記腿（存量債隨弧消化）

### Context
- **UC 引用**：更新「memory 卡流水結案機械對帳」的登記側
- **依賴關係**：依賴 S1 定稿的三分歸屬詞形；登記的出口就是 S1 閘門＋既有蒸餾第三動
- **語義約束**：與 S1 共享詞形；登記是「列入蒸餾範圍」不是「當場清理」（弧進行中條目仍會成長）
- **基礎設施盤點**：execution-plan skill「UC 盤點」節步驟 3（掃描 backlog 卡關聯＋自動建卡——含去重前置 `backlog search`＋pending-decisions 查詢）；輸出格式（掃描範圍/既有 UC 狀態/新增 UC 表格）
- **依賴錨點**：`skills/execution-plan/SKILL.md` UC 盤點步驟 3 去重前置行＋輸出格式段

### 修改要點
1. **步驟 3 外的獨立子步**：同主題 memory 條目盤點——rg 主題詞掃本專案 memory 池（desc 投影＋條目檔），命中即列入 EP「UC 盤點」輸出「同主題 memory 條目（結案蒸餾範圍）」行；含弧流水形態（過期狀態詞）者標記。**不受步驟 3「repo 有 `backlog/` 時」分支限制**——memory 池與 backlog 制正交（S1 閘門跨專案通用，登記腿同步通用；無池 → 標跳過）
2. 輸出格式模板（UC 盤點輸出段）同步加「同主題 memory 條目（結案蒸餾範圍）」行槽位；結案銜接語義一句：本弧結案蒸餾（kanban 第三動）範圍含登記條目——存量債隨弧消化，不等波段
3. 輕量約束：掃描是清單級（列條目名＋一行形態判讀），不做內容審（那是 memory-audit 層 2 的事）

### 驗證策略（docs mode）
- `rg "結案蒸餾範圍" skills/execution-plan/SKILL.md` 命中
- 詞形跨檔一致（S1 驗證覆蓋）
- 不越界：UC 盤點新行不含蒸餾方法論細節（單一源）

---

## S3：收尾（元專案 docs mode）

### 修改要點
1. **存量債指針**（EP 承載、不另建載體）：21 條 `project_*`（~130KB）＋**5 檔**流水詞（清單：`project_air-26-push-collection`、`project_agents-registry-split-design`、`project_memory-cc-alignment-diagnosis-0905`、`project_postbuild-tour-repair-loop-0907`＋MEMORY.md 投影——初版列的 `feedback_conditional-commit-authorization` 經覆核為誤報：其 "pending" 是教訓敘述非結案流水）——出口＝夜波/audit 波段（既有機制），本弧不直接清
2. 卡結案兩步＋第三動（本弧自身 memory 蒸餾——AIR-37 相關條目若有）
3. /audit-test：docs mode 無測試——跳過（標記）

### 驗證策略
- 卡 Done＋雙 ref；EP 歸檔；存量指針在 EP 在場

---

## 整合策略

- baseline: 3a264e6（AIR-37 建卡 commit；working tree 含前兩弧〔AIR-36＋memory-audit〕未 commit 變更——AIR-36 已隨 3211323 落地，memory-audit 一檔待 commit）
- 兩腿詞形共享（三分歸屬/結案蒸餾範圍）**且資料共享**（S2 登記清單＝S1 掃描輸入）；方法論單一源（kanban/memory-audit）不動不重抄

## EP Review Record（dual-family；GLM fresh-eyes 09-07 完成＋muse 腿額度降級——reset 13:00 後補審修正版）

| # | Finding | 嚴重度/信心 | 裁決 | 處置 |
|---|---------|------------|------|------|
| F1 | 掃描鍵（卡 id）漏 52% 債形——11/21 project_ 不含 AIR- 字串（無卡弧）；S2 登記清單無 S1 消費機制＝閉環未閉 | H/0.85 | ✅採納 | 掃描鍵擴為「卡 id ∪ 登記清單 ∪ 弧主題詞」聯集，S1 條文明寫登記清單為掃描輸入 |
| F2 | mid-arc commit 的「當場蒸」打爆「進行中弧線禁加段、一次性蒸餾」既有政策 | H/0.7 | ✅採納 | 三分歸屬前加結案態前置（in-flight 不動）；SM 補 SM-6 |
| F3 | 池路徑指針（memory-audit 適用載體段）落空——該段無根路徑，單讀不可執行 | M/0.6 | ✅採納 | S1 條文自帶根路徑形態例 |
| F4 | skills/CLAUDE.md:56 commit 行 2.8 枚舉過時 | M/0.7 | ✅採納 | S1 要點 3 增列 |
| F5 | SM-5「近 7 天非本弧」無機械判準且慢弧掉出排除分支被誤蒸 | M/0.6 | ✅採納 | 判準改「歸屬他弧且 owner 線未結案→保守不動」（結案態非天數） |
| F6 | 缺「memory 池不存在」場景（跨專案通用 skill） | M/0.55 | ✅採納 | SM-7＋S1 條文分支 |
| F7 | 存量清單 feedback_conditional-commit-authorization 誤報（pending 是教訓敘述） | L/0.8 | ✅採納 | S3 清單改 5 檔＋覆核註記 |

### muse 補審（job-mtqrxjd9，額度重置後 fire-and-forget；前審 7 項修正全確認）

| # | Finding | 嚴重度/信心 | 裁決 | 處置 |
|---|---------|------------|------|------|
| F-A | 掃描鍵「commit message 內 id」在 2.8 時點不可觀察（message 於階段 4 才生成） | M/0.75 | ✅採納 | 掃描鍵改 staged diff／branch 名內 id＋時序註記 |
| F-B | S2 登記行掛步驟 3「有 backlog/ 時」分支——無 backlog repo 整腿靜默跳過 | L/0.7 | ✅採納（非 reversal：memory 池與 backlog 制正交，通用性修法不反轉拍板） | S2 提升為獨立子步 |
| F-C | 結案態前置需讀卡狀態，2.8 無 backlog 讀步驟 | L/0.65 | ✅採納 | 前置讀取句（view --plain；無 CLI 保守未結案） |
| F-D | S2 未同步輸出格式模板槽位 | L/0.6 | ✅採納 | 模板加行槽位 |

## 收尾步驟

（S3 全涵——元專案 docs mode：卡結案兩步＋本弧 memory 蒸餾；無 Capabilities/SYSTEM-MAP/audit-test）
