# EP: muse bridge 轉發 concurrency 釋放——fire-and-forget 收法慣例落地

> **ep_type**: implementation（docs mode——product 全為 instruction/documentation 檔）

baseline: 8e9915e

## 實作總覽

**痛點**：muse bridge 長跑轉發（10-30 分鐘）以「caller session 掛背景 Bash 等 exit」為預設形態——每次轉發佔用一個 caller session / concurrency slot；N 個並行 muse 任務＝N 個 session 被綁定轉發員角色。若收法用 session 輪詢（TaskOutput 反覆查），每次輪詢還是一個帶全 context 的 model request。

**解法**：收法升級為 **fire-and-forget**——`task --background` 提交（detached worker＋ledger 持久化＋立即返回 jobId）→ caller session 即時釋放 → 事後任何 session 以 `wait`/`show` 認領。**多工複用**：一個 session 持 N 個 jobId 統一掃描。

**本弧前置研究（已完成，段落 0 素材）**：

- **bridge 0.2.5 源碼實證**（`muse-market/muse/0.2.5/scripts/muse-bridge.mjs`）：
  - `--background` 路徑（:918-976）：先寫 running entry 進 ledger → spawn detached worker（`detached: true`＋`child.unref()`＋`stdio: "ignore"`——脫離 caller 進程樹）→ 立即印 jobId、exit 0
  - worker（`__bg_worker`，:821-872）完成時把 status/exitCode/summary 寫回 ledger entry（jobs.json）；**finalText 非 entry 欄位**——`show`/`wait` 讀取時由 per-job jsonl 重導出（`loadJobFinalText` :1650-1660）
  - CLI 家族（:698-703）：`task --background`／`wait <jobId> [--timeout ms]`（內部 sleep-poll，零 model request；timeout 到期 exit 124）／`show`／`runs`／`stop`／`export`；`--prompt-file` flag 讀檔案 prompt
  - ledger 位置＝workspace-local `.muse-bridge/`（per-repo，`LEDGER_DIR_NAME`，:12）
- **兩端 SessionEnd hook 差異**（`session-lifecycle-hook.mjs`＋hooks.json 實證）：plugin 掛 SessionStart（stale reconciler）/SessionEnd（**kill process tree＋標 interrupted**——「孤兒 muse 進程燒訂閱額度是 bug」）；此 hook **CC 端生效**（CC plugin hooks 機制）、**ZCode 端不生效**（`~/.zcode/cli/config.json` hooks 只掛 ai-rules user-level hooks，plugin hooks.json 不執行）→ **ZCode 端 background job 可跨 session 存活；CC 端 holder session 必須活著**
- **Muse 諮詢**（bridge job-mtqiot5x，2026-09-07，low effort）：fire-and-forget＋late-collect 為正確形態；陷阱＝jobId 持久化在 ledger（不依賴 session context）、`wait` 用有界 timeout 迴圈而非單一大 block、`stop`/清理前先 `show`/`export`、任務設計成冪等；計費語義＝並行不省 quota（同 5h window token 加總，並行買 wall-time）、實用並行上限 2-3 長任務；bridge 0.2.5 無 push callback（全 poll 形態），callback roadmap 在 muse-plugin-cc repo

**跨 repo 邊界（out of scope，僅記錄）**：muse-rescue agent 契約（前景 task-once 形態）與 bridge callback/notify roadmap 屬 `~/Github/muse-plugin-cc` repo——本弧不動 plugin repo。

## UC 盤點

### Backlog 關聯
- AIR-36（本弧追蹤卡，已建已 commit 8e9915e）
- 前弧脈絡：AIR-26（external-runtime 委派收法 push 化——背景 Bash exit 喚醒，Done）＝本弧直接前驅（push→fire-and-forget 迭代）；AIR-21（bridge wait 子命令 job 輪詢機械化，Done）＝wait 原語機械基礎

### SYSTEM-MAP 影響
- 無（元專案無 SYSTEM-MAP.md）

### 掃描範圍
- 引用面掃描：`rg "背景 Bash 直呼|bridge 直呼|fire-and-forget|forwarder"` 命中三檔——`agents/AGENTS.md`、`skills/_common/work-order.md`、`skills/model-routing/SKILL.md`（rules/ 零命中，bundle 骨架層 pointer 不需動）
- `backlog task list --plain`：非 Done 欄清空，無進行中衝突卡

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| external-runtime 委派收法（push 決策樹/ETA-gate） | ✅ | skills/model-routing/SKILL.md「完成回報收法」節 | 更新 | 決策樹長跑層升級 fire-and-forget 優先 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| muse bridge fire-and-forget 收法（跨 session 認領＋多工複用） | 📋 | skills/model-routing/SKILL.md（決策樹）＋消費端同步 |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 長跑轉發（>10min） | 主 session 需派 muse 長跑任務 | `task --background` 提交 → jobId 即回 → session 繼續其他事；不掛前景、不綁 session | 無 | fire-and-forget 收法 |
| SM-2 | 事後收結果 | 需要報告/verdict 時 | `wait <jobId>`（有界 timeout 迴圈）或 `show` 讀 ledger finalText；完整 stdout 在 jsonl | 無 | fire-and-forget 收法 |
| SM-3 | 跨 session 認領 | 提交 session 已結束（ZCode 端） | 任何 session `runs`/`show` 讀 workspace ledger——worker detached 存活 | 僅 ZCode 端（hook 不執行） | fire-and-forget 收法 |
| SM-4 | CC 端 holder 結束 | CC session 結束時 job 仍在跑 | SessionEnd hook 殺 process tree＋標 interrupted——CC 端 holder session 必須活著（文檔警示，決策樹承載） | 無 | fire-and-forget 收法 |
| SM-5 | 多工並行 | 2-3 個 muse 長跑同時 | 一個 session 持 N 個 jobId 統一掃 `runs`/`show`；quota 語義＝同 5h window 加總、並行買 wall-time 不省花費 | 無 | fire-and-forget 收法 |
| SM-6 | 簡單轉發（快速往返） | review/diagnosis 秒~分鐘級 | 背景 Bash 阻塞直呼仍合法（決策樹第 1 層保留不動） | 無 | —（既有） |

## 段落劃分原則

定義源（skill 決策樹）先行，消費端同步隨後，收尾段獨立。三段皆 docs mode：修改要點替代 Pseudo Code、驗證為文檔驗證（rg 殘留／跨檔一致性／單讀可執行），無 TDD/mypy/pytest。

---

## S1：model-routing skill 收法決策樹重排（定義源）

### Context
- **UC 引用**：實作「muse bridge fire-and-forget 收法（跨 session 認領＋多工複用）」
- 現行決策樹（AIR-26 落地，:150-160）四層：①簡單轉發前景直呼 ②長跑兩段式（`--background` 拿 jobId → 背景 Bash 掛 wait → exit 喚醒）③prompt 工程 wrapper ④LLM 層 ETA-gate fallback。第 2 層已含 `--background` 但形態仍是「掛 wait arm」——session 仍被佔用，痛點未解
- **依賴關係**：S2 的消費端語義同步依賴本段定稿
- **語義約束**：與 S2 共享「fire-and-forget」詞形與「跨 session 認領」語義；judge 裁決層不變的既有拍板（AIR-24）不得被本段稀釋
- **基礎設施盤點**：決策樹所在節＋「派發與收法單一源」pointer（agents/AGENTS.md:29）——無程式碼基礎設施
- **依賴錨點**（文檔行號錨點）：決策樹 = `skills/model-routing/SKILL.md:150-160`；hook 差異事實源 = plugin `scripts/session-lifecycle-hook.mjs`＋`hooks/hooks.json`（跨 repo 引用，路徑去版本段寫法 `…/muse-market/muse/<ver>/`＋註記「以 plugin cache 現版為準」——避免版本號元資訊入 instruction 檔）

### 修改要點（docs mode——無 Pseudo Code）
1. **決策樹第 2 層（長跑）改寫為 fire-and-forget 優先**：`task --background`（或 `--prompt-file` 形態）提交 → jobId 即回 → caller 結束 turn 釋放；**收＝事後 `wait`（有界 timeout 迴圈，起點 bridge 預設 5min）或 `show` 認領**；「背景 Bash 掛 wait arm」降級為「不想跨 session 時的便利形態」一句帶過；**124 到期語義與家系拆分（muse exit 124＋status running＝重掛；codex exit 0＋`waitTimedOut`）原樣保留於新層——晚收同樣需要的語義，非殘留**
2. **新增兩端 SessionEnd hook 差異警示**：ZCode 端 plugin hooks 不執行 → background job 可跨 session 存活（fire-and-forget 完整可用）；CC 端 SessionEnd hook 殺 running job → holder session 必須活著（fire-and-forget 限縮為「session 內釋放 turn」，跨 session 認領前須確認 holder 在場）
3. **新增多工複用段**：一個 session 持 N 個 jobId 統一掃（`runs --json` sweep）；並行 quota 語義一句（同 5h window 加總、實用並行 2-3 長任務）
4. **收編 Muse 諮詢陷阱**（決策樹尾注）：`wait` 有界迴圈勿單一大 block；`stop`/清理前先 `show`/`export`（ledger GC 會吃證據）；委派工單設計成冪等（timeout 後可能重 wait）；jobId 持久化在 ledger 不依賴 session context
5. codex 側（對照腿）不在本弧 scope——決策樹既有 codex 語義（status --wait 差異）保留不動

### 驗證策略（docs mode）
- rg 殘留：舊第 2 層「掛 wait arm 為主形態」語義改寫後無孤立殘留；**124／家系拆分語義屬保留項非殘留**（決策樹內部一致性）
- 跨檔一致性：S2 完成後 `rg "背景 Bash 直呼"` 全 repo 命中語義正確（dispatch matrix 行更新後或歸零）
- **單讀可執行**（skill 原有剛性要求）：未載入背景的 session 單讀決策樹能執行——fire-and-forget 層含完整命令形態（--background/--prompt-file/wait/show）與兩端判定步驟
- 導航有效性：決策樹引用的 plugin 路徑（hook 差異事實）實際存在

---

## S2：消費端語義同步（agents/AGENTS.md＋work-order.md）

### Context
- **UC 引用**：更新「muse bridge fire-and-forget 收法」的消費端指向
- **依賴關係**：依賴 S1 定稿的詞形與語義；本段完成後 rg 殘留掃才有意義
- **語義約束**：與 S1 共享 fire-and-forget 詞形；「派發與收法單一源在 model-routing skill」的 pointer 結構不變（消費端不複製決策樹內容）
- **基礎設施盤點**：`agents/AGENTS.md:41`（dispatch matrix「EP review（雙家族）」行——muse 側現寫「背景 Bash 直呼 bridge（不佔 agent 並發）」）；`skills/_common/work-order.md:114`（消費形態句「經 bridge task／codex 派發」）；`skills/CLAUDE.md:132`（工作流索引 model-routing 行——收法描述「push 化決策樹：背景 Bash exit 喚醒」）；`rules/model-routing.md:34`（骨架句「push 化決策樹」括號）
- **依賴錨點**：`agents/AGENTS.md:41` / `skills/_common/work-order.md:114` / `skills/CLAUDE.md:132` / `rules/model-routing.md:34`（文檔行號錨點，rg 驗證指向預期內容）

### 修改要點
1. `agents/AGENTS.md:41`：muse 側形態短語改為 fire-and-forget 語義，**區分兩路徑**——`task` 形態＝`--background` fire-and-forget 提交＋晚收；`review` 子命令形態仍背景 Bash 阻塞（`review` 無 `--background`/`--prompt-file`，`parseReviewArgs` :1309-1348）——保留「不佔 agent 並發」事實並補「不佔 caller session」（task 形態）
2. `skills/_common/work-order.md:114` 消費形態句補 jobId 回報指引一句：長跑工單派發後回報 jobId（供晚收/認領），收法單一源指向 model-routing skill 決策樹——範本不自帶定義
3. 掃 `agents/AGENTS.md` 全檔其他「直呼」出現點（:29/:83 已確認為 pointer/事實描述不需改）
4. `skills/CLAUDE.md:132`：收法描述括號同步新樹頭形態（「push 化決策樹：背景 Bash exit 喚醒」→「fire-and-forget 決策樹（--background 提交＋跨 session 認領＋wait/show 晚收）」）
5. `rules/model-routing.md:34`：骨架句括號詞彙中性化——「push 化決策樹」→「收法決策樹」（fire-and-forget 為頭形態後 push 不再概括全樹）；`rules/` 其餘零命中不動

### 驗證策略（docs mode）
- `rg -n "背景 Bash 直呼|背景 Bash exit 喚醒"` 全 repo（排除 ref-docs/backlog/ai-analysis/memory）——命中點逐一判讀：語義已同步或屬歷史敘事
- `rg -n "fire-and-forget|--background"` 新語義命中 S1+S2 目標檔
- `rg -n "push 化" rules/model-routing.md skills/CLAUDE.md` → 改寫後歸零（或僅歷史敘事、逐一判讀）
- dispatch matrix 行的 tier/harness 欄位未被誤動（只改形態短語）

---

## EP Review Record（fresh-eyes agent，2026-09-07；dual-family muse 腿＝本弧前置設計諮詢 job-mtqiot5x 覆蓋）

| # | Finding | 嚴重度/信心 | 裁決 | 處置 |
|---|---------|------------|------|------|
| 1 | skills/CLAUDE.md:132 工作流索引收法描述「push 化決策樹：背景 Bash exit 喚醒」改後失準，掃描 pattern 不含此變體 | M/0.85 | ✅採納 | S2 要點 4 增列 |
| 2 | S2 範例短語逐字套 :41 會為 review 路徑捏造 `--background` 命令形態（review 子命令無此 flag，parseReviewArgs :1309-1348） | M/0.65 | ✅採納 | S2 要點 1 區分 task/review 兩路徑 |
| 3 | finalText「寫回 ledger entry」不精確——show/wait 讀取時由 jsonl 重導出（loadJobFinalText :1650-1660） | L/0.85 | ✅採納 | 總覽改述 |
| 4 | 124 到期語義/家系拆分保留未明示，實作者可能當殘留刪除 | L/0.6 | ✅採納 | S1 要點 1＋驗證策略明示保留 |
| 5 | rules/model-routing.md:34「push 化決策樹」詞彙 drift（pattern 零命中但語義在場） | L/0.75 | ✅採納 | S2 要點 5 中性化 |
| 6 | SM-6「前景直呼」與第 1 層實文「背景 Bash 阻塞直呼」不符 | L/0.8 | ✅採納 | SM-6 措辭修正 |
| 7 | 決策樹引用 plugin 路徑含版本段＝版本號元資訊且隨升級 rot | L/0.6 | ✅採納 | S1 錨點去版本段＋「以現版為準」註記 |

---

## S3：收尾（元專案 docs mode 收尾）

### Context
- **依賴關係**：S1+S2 完成後執行
- docs mode 收尾形態：元專案跳過 Capabilities/kanban 結案之外的常規項（受影響命令/rules 行為已反映＝S1/S2 本身；`skills/CLAUDE.md` 工作流索引 description 若 model-routing description 未變則跳過——本弧不動 description）

### 修改要點
1. **memory 蒸餾**：`reference_external-runtime-delegation-family` 條目收法描述更新為 fire-and-forget 階層（push＝exit 喚醒仍真，其上疊 fire-and-forget＝--background 提交跨 session 認領；兩端 hook 差異一句）——寫入當下即蒸後形
2. **卡結案兩步＋第三動**：AIR-36 `-s Done --final-summary` → `--ref` 換 done/ URL（殼建後）→ memory 蒸餾同時機
3. **/audit-test**：docs mode 無測試產物——跳過（標記理由）

### 驗證策略（docs mode）
- memory 條目 rg 驗證：新語義在場、舊單層 push 描述已收斂
- 卡狀態 Done＋雙 ref（http URL＋相對路徑）

---

## 整合策略

- baseline: 8e9915e（建卡後 HEAD；working tree 已含本日 dispatch 節政策修訂〔額度現值/實作預設/審查類放寬〕未 commit——與本弧同檔不同節，commit 時同行，審查邊界以此聲明）
- 單一定義源（skill 決策樹）＋消費端 pointer 同步；跨 repo（muse-plugin-cc muse-rescue 契約/callback roadmap）明確 out of scope 已記錄於總覽

## 收尾步驟

（S3 全涵——元專案 docs mode：memory 蒸餾＋卡結案兩步＋蒸餾第三動；無 Capabilities 表/SYSTEM-MAP/audit-test）
