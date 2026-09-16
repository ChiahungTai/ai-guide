# EP：卡 branch 生命週期（線縮寫＋卡號，mosaic 主場）

> **ep_type**: implementation（docs mode——product 純 `.md`）

baseline: d4c98ab7cdf25f880551c29dc2c0ababf05f0b8f

## 實作總覽

落地「卡 branch」規則：**卡開工（implement 階段 1 起手式 ⑤ 之後的 ⑥）從 owning 線 checkout 以「線縮寫＋卡號」命名的 branch，工作 commits 落其上（message 帶卡 id）；結案 /commit 確認通過、卡 branch commit 至 clean 後，回 owning 線 `merge --ff-only` 吸收、刪 branch**。建卡（📋）不開 branch（建卡即 commit 進所在線，不變）。

**設計主場是 mosaic**（user 拍板）：user 日常開三個 VSCode 視窗對應 mosaic 三個 worktree（main/v2/warrant）——harness 與 VSCode 恆顯的 branch 名是唯一 ambient UI，現行顯示線名（`warrant`）看不到「這條線現在做到哪張卡」。卡 branch 命名 `<線縮寫>-<卡號>` 後，三視窗顯示 `lab-77`＝線＋卡一眼可讀。ai-rules（單線單 WT）是同構的簡化例。

**規則形態**（兩 repo 統一語義）：

| repo | 線 | 卡 branch 名 | 例（卡 id 顯示形↔branch） |
|------|----|-------------|--------------------------|
| ai-rules | main（唯一線） | `air-<N>`（線縮寫=repo 縮寫；與卡 id 前綴的字面重合同 L22 註記） | AIR-46 ↔ `air-46` |
| mosaic | main | `mos-<N>` | MOS-77 ↔ `mos-77` |
| mosaic | warrant | `lab-<N>` | MOS-77（owning=warrant）↔ `lab-77` |
| mosaic | v2 | `bt-<N>` | MOS-77（owning=v2）↔ `bt-77` |

命名語義：**前綴=worktree 縮寫**——線的身份是 worktree（路徑，穩定），不是 branch（該 WT 當前 checkout，開卡 branch 後就換了——branch 只是剛好）。卡號 N 全 repo 唯一（Backlog.md id）；**WT↔縮寫映射表住各 repo 的 git 慣例節**（key 取 WT basename——絕對路徑因機器而異不入表；ai-rules：repo 根↔main（`air-*`）；mosaic：`mosaic_alpha`↔main（`mos-*`）、`mosaic_alpha_offline_backtesting`↔v2（`bt-*`）、`mosaic_alpha_trading_lab`↔warrant（`lab-*`））——mosaic 的 branch 前綴與卡 id 前綴（mos-）不同屬 by-design（前綴指線非 repo），映射經 git 慣例節查表一跳可達。卡 id 顯示形大寫（AIR-46）、檔名與 branch 小寫（air-46）——`rg air-46` 撈卡檔＋commit；mosaic 側 `rg mos-77` 撈卡檔、`rg 77` 過寬勿用（branch 名另行判線）。

業界對照：ticket-ID 形態（`PROJ-123`，Atlassian/Graphite 生態標準）＋ AI-era branch-per-task 共識（Anthropic `--worktree`、Kempé、Osmani）；收尾 ff-only 直線屬 trunk-based 正統，不用 merge commit。

## UC 盤點

### Backlog 關聯
- 新建：**AIR-46**（本卡——capability 卡兼 EP 追蹤卡，單能力弧；已建卡即 commit `7c2f947`）
- 衍生（本 EP 定稿後、mosaic session 承接）：**MOS 卡**——線判定機械升級＋owning 線欄位＋mosaic 側 git 慣例節（引用本 EP，不在 ai-rules repo 動 mosaic 檔案）
- 去重：`backlog search branch` → AIR-33/AIR-38（皆 Done，無重複承諾）；`ai-analysis/_inbox/pending-decisions.md` 不存在

### SYSTEM-MAP 影響
- 無 SYSTEM-MAP.md（元專案）——正當跳過

### 掃描範圍
- `ai-rules/AGENTS.md`（全文）；`skills/kanban-board/SKILL.md`（起手式五步、差異宣告兩條、建卡即 commit、清理批次——**product 含兩處編輯**，見 S1）；`skills/rebase/SKILL.md`（trunk 鐵律、--ff-only 吸收、all 批次目標集合定義）；`skills/commit/SKILL.md`（commit gate、2.8 掃描鍵、per-branch 清除）；`skills/implement/SKILL.md`（階段 1）；`backlog task list`（AIR-44 Done、AIR-45 In Progress；快照 09-08，AIR-44 本 session 結案）

### 同主題 memory 條目（結案蒸餾範圍）
- `project_session-topology-single-writer`（ai-rules 單一寫入者拓撲——air 側前提）
- `project_rebase-skill-nowt-ff-fix`（rebase/ff 語義——吸收步機械單一源）

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 |
|------|------|------|------|
| 建卡即 commit（跨 WT id 防撞） | ✅ | kanban skill | 無影響（維持落所在線） |
| /rebase trunk 鐵律＋--ff-only 吸收 | ✅ | rebase skill | 互補引用（收尾兩步直接沿用）；all 批次需卡 branch 護欄（SM-14） |
| 卡結案兩步（Done 欄＋done/ ref） | ✅ | kanban skill | 無影響 |
| /commit 2.8 掃描鍵 | ✅ | commit skill | **相容證據**：掃描鍵已含「branch 名內卡 id」——commit 側早預期 branch 帶卡 id |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| 卡 branch 生命週期——開工 checkout `<線縮寫>-<卡號>`、結案 ff-only 吸收回 owning 線；ambient 顯示（線＋卡）＋整卡 diff 邊界＋整卡可拋棄 | 📋 | ai-rules/AGENTS.md「git 慣例」節＋kanban skill 兩處編輯（本 EP S1）；mosaic 側＝衍生 MOS 卡 |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | Happy path 開工（ai-rules） | implement 階段 1，起手式 ⑤ 完成 | `git checkout -b air-46`（自 main） | 無 | UC 主行 |
| SM-2 | Happy path 開工（mosaic） | 同上，卡屬 warrant 線 | `git checkout -b lab-77`（**自 warrant**——起點必為 owning 線 branch）；VSCode 顯示 `lab-77` | 無 | UC 主行 |
| SM-3 | 跨 session 接續／同名遺留撞名 | `/handoff`／`/at` 接手 branch 已存在；或開工 `checkout -b` 撞同名未吸收遺留 | 既有形：`git checkout lab-77` 續用（不 `-b`）；起手式 ④ 新鮮度核對擴及 `git log warrant..lab-77`。branch 名不需 handoff 傳遞——由卡 id＋owning 線（卡 desc）機械重建。撞名處置：`git log <owning線>..<branch>` 有本卡未吸收 commits → 改續用（不 `-b`）；無 → 依卡狀態判（吸收或拋棄，SM-4） | 無 | UC 主行 |
| SM-4 | session 死亡未收 | quota 死亡，branch 遺留（跨 session/過夜屬正常非異常） | 接手者處置：卡仍活→續用；卡判死→吸收或拋棄 | 卡 notes | UC 主行 |
| SM-5 | 整卡拋棄 | 探索失敗，**user 明確確認後** | `git branch -D lab-77`（不可逆破壞需確認——/commit gate quote-scope 不涵蓋 `-D`）；已 push 者補 `git push --delete`；卡標 ❌；owning 線零中間 commit 留痕 | user 確認 | UC 可拋棄 |
| SM-6 | 吸收時 owning 線已前進 | 卡期間線收斂（rebase onto main）或他卡吸收 | `--ff-only` 大聲拒絕 → `/rebase <owning線名>` 兩步：卡 branch rebase onto **owning 線**（mosaic 禁默認 `main`——錯 base 即跨線污染）→ 再 ff 吸收。衝突解壞走 rebase skill abort/reflog 復原（skill 既有，引用不重述） | 無 | UC 吸收 |
| SM-7 | 夜間 automation 落點 | launchd 清理批次在 WT commit（WT 當時在卡 branch） | commits 落卡 branch 屬正常，吸收時一併回線；無害。**已知接受的盲區**：WT 停卡 branch 時，cleanup precheck `--not HEAD` 排除本卡——他卡跨線訊號看不到，屬保守側（只會誤放不會誤清） | 無 | UC 吸收 |
| SM-8 | 忘記 checkout 就動工 | 起手式漏 ⑥，commits 直落線 branch | 軟失敗：卡 branch 上 commits message 帶卡 id（前提由 S1-A2 message 慣例建立），追溯不斷；**不回頭搬 commits**（禁 cherry-pick 重寫已確認內容）；規則是慣例非硬 gate | 無 | UC 主行 |
| SM-9 | 卡 branch push 與否 | 預設 | 本地 branch 不 push；跨機接續確需 push 時，重寫僅限 `--force-with-lease` 該 branch；拋棄時補 `push --delete` 遠端清理；線/trunk 永不 force | 無 | UC 吸收 |
| SM-10 | 無卡小修 | 小型變更不建卡不開工 | 不開 branch，照舊直 commit 所在線——規則只綁「有卡的 In Progress」 | 無 | — |
| SM-11 | 線判定（automation） | session/腳本判「這 WT 是哪條線」——任何 branch 下皆成立（含卡 branch 開著時） | `git rev-parse --show-toplevel` 取 basename 查映射表（`mosaic_alpha_trading_lab`→warrant；`mosaic_alpha`→main；ai-rules repo 根→main）；branch 不再參與判定（卡 branch 開著時原 branch 已不可見——branch 前綴匹配方案退役）；映射表住各 repo git 慣例節 | 無 | UC 顯示 |
| SM-12 | 開錯 base 防護 | 開工時 checkout 起點非 owning 線 | 卡 desc 記 owning 線（desc 已決策段）；開工驗證起點 branch == owning 線名，不符即停 | 卡 desc | UC 主行 |
| SM-13 | 單 writer 前提 | 想同線同時開兩張卡 branch | **不是並行授權**——每線同一時間一張進行中卡（board In Progress 可見）；開工時 `git branch --list '<線縮寫>-*'` 非空即停（自律變他律；`*` 不可省——無 `*` 只精確匹配字面名，永遠空） | board | — |
| SM-14 | `/rebase all` 誤吸收護欄 | trunk/線上跑 `/rebase all`（all 目標集合＝`git branch` − trunk——進行中卡 branch 會被當 feature 提前吸收，SM-5 可拋棄保證破裂） | 規則文護欄：**all 之前檢查無進行中卡 branch**（`git branch --list '<線縮寫>-*'` 非空 → 先收卡或先刪，不跑 all；`*` 不可省——見 SM-13） | 無 | UC 吸收 |
| SM-15 | owning 線中途變更 | 卡做到一半換線（規劃變更） | 刪舊卡 branch（未吸收 commits 隨 git 保留於 reflog/或先吸收）＋改卡 desc owning 線＋新線重開 `<新線縮寫>-<N>`——舊 branch 前綴與 desc 同步過期，驗證才不會永久紅燈 | 卡 desc | UC 主行 |
| SM-16 | stale branch 稽核 | 忘記 `-d`（結案漏刪），卡 branch 堆積污染 `/rebase all` 與 Phase 3 落後報告 | 起手式 ④ 順帶一行：`git branch --merged <owning線> | rg '<線縮寫>-'`——已吸收未刪者當場清 | 無 | UC 吸收 |

## 段落 0 研究摘要

- **拓撲事實**（本 session 機械查證）：ai-rules 單 branch `main`（`git branch -a`）；mosaic 三 WT（`git worktree list` 顯示路徑＋`[branch]`——`mosaic_alpha`／`mosaic_alpha_offline_backtesting`／`mosaic_alpha_trading_lab`）；卡檔名前綴小寫（`backlog/tasks/air-45 - *.md`）、卡 id 顯示形大寫
- **可複用基礎設施**：`/rebase` skill 兩步（feature rebase onto trunk → trunk `merge --ff-only` 吸收；trunk 永不被 rebase）；kanban 起手式五步——⑥ 步以**定義源 pointer** 形態挂接（見 F3-2 處置）
- **「WT branch==線名」消費者盤點**（muse 審查 F4 表收編，皆實讀驗證）：
  | 消費者 | 查證結果 | 處置 |
  |---|---|---|
  | `run-backlog-cleanup.sh`（precheck `--all --not HEAD`） | 落點 SM-7 覆蓋；卡 branch 開著時他卡跨線訊號盲區 | 已知接受（保守側），記 SM-7 |
  | `backlog_precheck.sh` | 純 branch-agnostic（grep message） | 已驗證無影響 |
  | backlog CLI `check_active_branches` | 卡 branch 增多→掃描集合變大；語義不變 | 監控項（mosaic 落地後觀察噪音） |
  | `/rebase all` 目標集合（`git branch`−trunk） | **進行中卡 branch 誤吸收** | SM-14 護欄（規則文層，不動通用 skill） |
  | rebase Phase 3 落後報告 | 卡 branch 列為 feature 噪音 | 接受（nit） |
  | `/handoff`、`/at` | 兩 SKILL.md 零 `branch` 命中——無假設 | 已驗證無影響 |
  | collaboration-constraints owning-WT | WT 路徑層判定，branch 不影響語義 | 已驗證無影響 |
  | /commit 2.8 掃描鍵 | 已含「branch 名內卡 id」 | **相容證據**（引用為既有 UC 表行） |
  | mosaic twin `run-backlog-cleanup.sh` | 腳本頭註明 twin 修改須同步 | S2 item 1 補盤點雙份 |
- **業界 grounding**（本 session web 查證）：Anthropic 官方 worktrees（`--worktree` per session）；Kempé「worktree per task 可拋棄」；Osmani sandbox branch（merge winners/discard losers）；ticket-ID branch naming（Atlassian/Graphite）；trunk-based 直線正統（trunkbaseddevelopment.com）
- **風險假設與監控項**：「線收斂週期 ≫ 卡 branch 生命」未驗證（muse 反轉對照⑤）——落地後監控 SM-6 觸發頻率；backlog 跨 branch 掃描噪音（上表）同監控

## S1：ai-rules/AGENTS.md「git 慣例」節＋kanban skill 兩處編輯

### Context
- **UC 引用**：實作「卡 branch 生命週期」（UC 盤點新增 UC）
- **依賴錨點**：`skills/kanban-board/SKILL.md`（起手式定義 ~:37；差異宣告第 2 條 ~:104——**兩處皆 product**）；`skills/rebase/SKILL.md`（trunk 模型鐵律、--ff-only 兩步、all 目標集合定義 ~:262）；`ai-rules/AGENTS.md` 消費端 context「git 認知」bullet
- **插入位置**：`ai-rules/AGENTS.md`「消費端 context」節之後、「命令的受眾視角」之前——新節 `## git 慣例（本 repo 卡 branch）`
- 語義約束：與 `/rebase` 鐵律共用「trunk/線永不被 rebase」詞彙；branch 名一律小寫；與 kanban 差異宣告改寫後的「預設解耦；採卡 branch repo 以 AGENTS.md 為準」互為單一源呼應

### 修改要點（docs mode 替代 pseudo code）

**改動 A——AGENTS.md 新節**（約 12 行，內容六塊）：
1. **命名**：卡 branch＝`<線縮寫>-<卡號>`；本 repo 單線 → `air-<N>` 小寫，映射 `air-*`↔main；卡號=Backlog.md id
2. **生命**：開工（implement 階段 1 起手式 ⑤ 後的 ⑥）自 main checkout `-b`；建卡不開；**卡 branch 上 commits message 帶卡 id**（`air-46: ...` 或括注形態）
3. **收尾**：/commit 確認通過、卡 branch commit 至 **clean** 後——`checkout main && merge --ff-only air-XX && branch -d air-XX`（WT 回 main）；dirty checkout 未必被拒（不衝突即帶走）——clean 紀律由 /commit gate 守，非 checkout 護欄（R2 user 拍板）
4. **`/rebase all` 護欄**：all 之前 `git branch --list 'air-*'` 非空 → 先收卡，不跑 all（SM-14；`*` 不可省）
5. **軟條款**：忘記 checkout 直落 main 屬軟失敗不回頭搬（SM-8）；夜間 automation commits 落卡 branch 無害（SM-7）；拋棄需 user 明確確認（SM-5）；跨 session 遺留屬正常處置（SM-4）
6. **mosaic 變體指針**：多線形態（`lab-77`/`bt-77`/`mos-77`、owning 線欄位、線判定路徑查表、SM-6 base=owning 線）定義源＝本 EP——只留一行指針不重述（單一源）

**改動 B——kanban skill 差異宣告第 2 條**（一行改寫）：「不掝 per-task branch——任務與分支解耦」→「**預設**任務與分支解耦；採卡 branch 的 repo 以其 AGENTS.md git 慣例節為準（多 worktree 紀律由各 repo 自訂）」——消除「禁止與要求並存」的指令矛盾（F3-1）

**改動 C——kanban 起手式 pointer**（半行，計數不動）：起手式段末補「（採卡 branch 的 repo 在 ⑤ 之後另有 ⑥ checkout 卡 branch 步——該 repo AGENTS.md git 慣例節）」——通用定義恆五步，採用 repo 的擴充有定義源指針，不產生計數 drift（F3-2 處置）

### 驗證策略（docs mode）
- **rg 一致性**：AGENTS.md 新節與 rebase 鐵律用語一致（「永不 rebase」「--ff-only」）；kanban 改動 B/C 後全文無殘留「不掝 per-task branch」舊句；與消費端 context「git 認知」bullet 無矛盾；無元資訊（instruction-writing 禁令）
- **Decoder test**：新 session 只讀 AGENTS.md 新節即可正確執行開工 checkout、message 慣例、結案吸收、all 護欄，不需另讀 EP
- **跨檔**：`skills/CLAUDE.md` 工作流索引不需動（規則非 skill）；改動 B/C 後 `rg "per-task branch" skills/` 僅剩新句
- `/consistency` 一輪

### Invariant Impact
無（純文檔；不觸會計/風控/domain service/silent-corruption path）

## S2（衍生，非本 EP product）：mosaic 側落地工單

> 本節是**設計定稿**（給 mosaic session 的 handoff 契約），本 EP 不在 ai-rules repo 動 mosaic 檔案。執行載體＝mosaic session 開 MOS 卡，引用本 EP 路徑。

| # | 待辦 | 驗收 |
|---|------|------|
| 1 | 線判定改為路徑查表：盤點所有依賴「WT branch == 線名」的消費者（rg 掃腳本/文檔/launchd：`run-backlog-cleanup.sh` **含 mosaic twin 副本雙份**、線 tag↔WT 規則文檔）→ 判定改為 `toplevel basename 查映射表`（branch 只代表當下，不再當身份） | 任一 branch 下（含卡 branch `lab-77` 開著時）逐消費者實跑判定，輸出=warrant；盤點清單全數處置（改或記已驗證） |
| 2 | owning 線欄位：卡 desc「已決策」段記 owning 線；開工驗證 checkout 起點（SM-12）；換線程序（SM-15） | 抽一張卡演練開工驗證＋換線，desc/branch 同步更新 |
| 3 | mosaic 側 git 慣例節：mosaic AGENTS.md 對應節（`lab-`/`bt-`/`mos-` 映射表＋收尾回 owning 線＋all 護欄＋SM-6 base=owning 線禁默認 main） | Decoder test：新 session 讀節可執行；映射表涵蓋三線 |
| 4 | 生效排序：**MOS 卡（判定升級）先落地，之後 mosaic 才開第一張卡 branch**——避免判定升級前的 automation 誤讀窗口 | 里程碑記卡 notes；首張卡 branch 開工時判定升級已 verified |

## 整合策略

單 product 段（S1：AGENTS.md 新節＋kanban 兩處編輯）無段間整合。EP/殼在同一 working tree 批次隨 /commit 帶走（建卡已先行 commit `7c2f947`）。

## 收尾步驟（docs mode）

1. AGENTS.md git 慣例節＋kanban 兩處編輯行為已反映；受影響命令引用面核對無 drift
2. 卡結案兩步（AIR-46 `-s Done --final-summary` → `--ref` 換 done/ URL）＋弧結案蒸餾（memory 兩條：session-topology、rebase-skill）
3. SM 提煉消費場景進卡 notes（`--append-notes`，自包含描述不引 SM 編號）
4. `/consistency` 綠

## EP Review 區段（muse 審查→judge 處置記錄）

**審查者**：muse（跨家族獨立 context，read-only）；**verdict**：需修正後實作；**judge**：主 session，18 項 findings 全數採納（無不採納；F2-1 細部修正——卡 id 顯示形大寫/檔名小寫兩形並存，EP 統一表述於實作總覽）。已全數寫回 EP 正文。

| # | 維度 | 嚴重度 | finding 摘要 | 處置（寫回處） |
|---|------|--------|-------------|---------------|
| F3-1 | 一致性 | must | kanban「不掝 per-task branch」與 EP 直接矛盾；「通用層零改動」主張不成立 | ✅ 改動 B（kanban 差異宣告第 2 條改寫為預設解耦＋repo opt-in）；product scope 擴（F1-2 同步） |
| F3-2 | 一致性 | must | 起手式「五步」計數 drift | ✅ 改動 C（定義源 pointer，計數不動——F3-1 既已開 kanban 編輯，pointer 同批） |
| F1-1 | 完整性 | should | S2 四項無驗收 | ✅ S2 改表格制，每項一行驗收 |
| F1-2 | 完整性 | should | 檔案清單漏 kanban SKILL.md | ✅ 掃描範圍＋S1 product 更新 |
| F2-1 | 合規 | nit | 大小寫不統一；mosaic branch↔卡非子串對應 | ✅ 實作總覽統一表述（顯示形大寫/branch 小寫）；映射表住 git 慣例節 |
| F2-2 | 合規 | nit | typo 軟失敟 | ✅ 已修 |
| F3-3 | 一致性 | should | 「不留過夜為原則」無 SM 源 | ✅ S1 內容塊 5 改為與 SM-4 對齊（跨 session 遺留屬正常處置） |
| F3-4 | 一致性 | should | ai-rules air→main 映射洞 | ✅ 內容塊 1 補映射行 |
| F4-1 | 遺漏 | — | cleanup precheck 卡 branch 盲區 | ✅ SM-7 記已知接受（保守側） |
| F4-2 | 遺漏 | — | backlog_precheck.sh 無影響未記 | ✅ 消費者盤點表記已驗證 |
| F4-3 | 遺漏 | — | check_active_branches 掃描集合變大 | ✅ 監控項（段落 0） |
| F4-4 | 遺漏 | — | **/rebase all 誤吸收進行中卡** | ✅ SM-14＋內容塊 4 護欄 |
| F4-5 | 遺漏 | nit | Phase 3 落後報告噪音 | ✅ 接受，盤點表記 |
| F4-6 | 遺漏 | — | /handoff、/at 無 branch 假設 | ✅ SM-3 註明 branch 名由卡 id+owning 線重建 |
| F4-7 | 遺漏 | — | collaboration-constraints path 層判定 | ✅ 盤點表記已驗證 |
| F4-8 | 遺漏 | — | /commit 2.8 branch-aware | ✅ 引用為相容證據（既有 UC 表） |
| F4-9 | 遺漏 | — | mosaic twin 腳本雙份 | ✅ S2 item 1 補 |
| F5-1..F5-8 | 場景 | should/nit | base 歧義／換線缺失／stale 稽核／message 前提／-D 確認／dirty 邊界／push --delete | ✅ SM-6 點名 base＋abort 指針；SM-15 換線；SM-16 稽核；內容塊 2 message 帶卡 id；SM-5 user 確認＋--delete；內容塊 3 clean 後吸收；SM-13 補機械自查 |
| 反轉①-⑦ | — | — | muse 前次反對論點對照：①部分化解（窗口期→S2 生效排序）②基本化解（F5-2 殘餘已補）③部分化解（SM-16＋--delete 補）④方向化解（message 慣例入規則文）⑤基本化解（收斂頻率假設→監控項）⑥化解（SM-13 他律化）⑦反轉成立（ambient UI 需求壓過 tag 替代） | ✅ 全數吸收進正文 |
| R1 | 一致性 | must | 護欄命令缺 `*`：SM-13/SM-14/S1-A4 的 `git branch --list '<縮寫>-'` 無通配只精確匹配字面名，永遠空——SM-14 護欄成空殼（F4-4 緩解失效）；SM-16 的 `rg` 子串匹配不受影響 | ✅ 三處已補 `*`（/tmp probe 實測 `'war-'`零命中／`'war-*'`命中） |
| R2 | 一致性 | should | S1-A3「吸收前 dirty＝checkout 會被拒＝護欄」誇大：dirty 切 branch 未必被拒（不衝突即帶著走），不能當護欄；前置「commit 至 clean」本身正確 | ✅ user 拍板改寫（09-09）——內容塊 3 拿掉護欄宣稱，clean 紀律歸 /commit gate |
| R3 | 場景 | nit | 同名未吸收殘留 branch 會撞 `checkout -b`：SM-16 只管已吸收未刪（`--merged`），quota 死遺留的未吸收同名殘留開工即撞；SM-4/SM-5 有處置但開工路徑未寫 | ✅ user 拍板補（09-09）——SM-3 觸發/行為欄補撞名處置（`git log <owning線>..<branch>` 判本卡遺留） |
| R4 | 設計 | should（user 拍板已改） | 線身份改走路徑：branch 只是該 WT 當前 checkout（開卡 branch 後即換），線身份應為 worktree 路徑（key 取 basename）；SM-11 branch 前綴匹配退役，改 `toplevel` 查表 | ✅ L22＋SM-11＋S1-A6＋S2-1 已改寫；殼 s2 表 key 改 WT |
| R5 | 命名 | should（user 拍板已定） | 前綴取自 WT 目錄名（非 branch）：trading_lab→lab-、offline_backtesting→bt-（user 二選一親定）；v2 branch 名未定案不影響縮寫；mos-/air- 維持 | ✅ EP/殼/卡全量更名；卡 desc④同步為路徑查表 |

**第二輪**：前綴＝worktree 縮寫（lab/bt/mos，user 親定）；準則 worktree≠branch≠WT 路徑；中間誤改已回退，僅 R1 `*` 保留。另：kanban 改 repo 源即時生效（symlink），無部署落差。過程細節見 git log。
