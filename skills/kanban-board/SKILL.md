---
name: kanban-board
description: "當你要操作 backlog board 或查它的機制時，backlog board（Backlog.md）機制單一源——命令合約、結案兩步、ref 規則、precheck；execution-plan/implement/metadata-sync 消費端引用此處"
---

# kanban-board — backlog board（Backlog.md）機制單一源

> **繼承**: `@../CLAUDE.md`。UC-Driven 方法論見全局 guide。本 skill 是 **backlog board 的機制單一源**（命令合約、ref 規則、結案流程、UI 入口）——execution-plan／implement／metadata-sync 等消費端引用此處，不自帶定義。

## 定位

**board = view not container**：任務卡是 `backlog/` 下的 plain markdown（frontmatter＋段落標記），CLI 與 AI session 直接讀寫檔案，board 只是渲染層。`.kanban/` 四 lane 目錄制已退役（2026-09-02）——`mkdir .kanban/` 是錯誤動作。

## 初始化（repo 首次採用）

```bash
backlog init "<project>" --agent-instructions none
```

- `--agent-instructions none`：不注入 CRITICAL_INSTRUCTION 區塊（與本 repo AGENTS.md 治理／元資訊禁令衝突）
- config.yml 關鍵鍵：`statuses`（建議三欄 To Do/In Progress/Done）、`task_prefix`（repo 識別前綴，如 mosaic=`mos`、ai-guide=`air`）、`auto_commit: false`（外部 git 紀律——CLI 只改檔）、`check_active_branches: true`（多 WT repo 必開——board 唯讀顯示他 branch 已 commit 卡＋next-id 掃描跨 branch 卡防撞；untracked/staged 卡不在 branch ref 上，git 掃描天生看不見，殘餘防撞靠建卡預掃〔見命令合約建卡段〕；**ai-guide 現值 true**——09-16 AIR-72 隨 persistent card WT 上線切換（多 WT 落地＝跨 branch 掃描＋建卡預掃＋porcelain 面並用，單 WT 時代「working copy 單一真相」假設不再成立））

## 命令合約（消費端引用本段）

**建卡**（execution-plan UC 盤點）：
```bash
# 多 WT id 防撞預掃（多 WT repo 必跑）：a) 檔案系統面——跨 WT max id，涵蓋他 WT untracked/staged 卡（git 掃描看不見）；b) porcelain 面——各 WT 未 commit 卡檔歸屬（誰該協調、卡何時進 ref）
for wt in $(git worktree list --porcelain | rg "^worktree " | cut -d" " -f2); do ls "$wt/backlog/tasks/" 2>/dev/null; done | rg -o '^[a-zA-Z]+-[0-9.]+' | sort -V | tail -1
for wt in $(git worktree list --porcelain | rg "^worktree " | cut -d" " -f2); do git -C "$wt" status --porcelain -- backlog/tasks/ 2>/dev/null; done
# 聚合判讀 a)：上行輸出＝filesystem 面 max-id 一行——全域最高卡號（涵蓋他 WT untracked/staged 卡）
# 聚合判讀 b)：本行輸出＝porcelain 面歸屬表——各 WT 未 commit 卡檔逐一列出（誰該協調、卡何時進 ref）
# 盲區聲明：兩掃母體皆為 `git worktree list --porcelain`——未註冊 WT 目錄（plain directory copy、pruned 殘留）不在掃描內
backlog task create "<標題>" -l <labels> -d <目標一句> [--ac "<驗收條件>"]   # CLI id=本 WT max+1，無 --id 可指定
backlog task edit <id> --plan "<工單 spec：baseline／已決策勿重辯／範圍>"   # desc 留人話、spec 住 Plan（詳「欄位分工」；`task create --plan` 限 active status，To Do 建卡後以 edit 補）
git add backlog/ && git commit -m "chore(backlog): <卡id> <標題>"   # 建卡即 commit（批次建卡併一顆）——跨 WT id 防撞靠卡及時進 branch ref；user 裁定此形態免逐次確認（例外條款見 [outward-action-consent](../../rules/outward-action-consent.md)「Commit 專屬段」）；建卡前確認當前 branch＝owning 線（非進行中卡 branch）——建卡 commit 落錯 branch 會污染他卡邊界（真實案例：AIR-46 狗糧——AIR-50 建卡落 air-46 上）
```
**共享 WT 活躍 branch 落點分流**（多 session 共享 primary WT、checkout 停在活躍弧卡 branch 時的外卡 commit 處置；commit 前必查 `git branch --show-current`——非預期 branch 是**換策略信號非停手信號**，branch 可能在本 session 中途被平行 session 切走，開場快照不算數）：
- **建卡 commit → 暫時 worktree 直進 main**：main 未被任何 worktree checkout 時（活躍弧佔 primary WT 是常態），`git worktree add <tmp> main` → `git -C <tmp> add <具名卡檔> && git -C <tmp> commit` → `git worktree remove <tmp>`——全程 `git -C`，絕不 cd 進暫時 worktree（cwd 懸死殺 Bash 面——前任 CC 事故）；代價＝board working copy 可見性延遲（弧 rebase/ff 後卡檔才現），接受——建卡到開工靠 handoff block 傳遞、不依賴 board 即時性；已隨弧 ff 進 main 的歷史建卡 commit 不搬
- **其他外卡小修 → 獨立顆粒 commit 落當前 branch**：message 標源卡 id（`fix(<源卡id>):` 形態）＋「跨 session 併入，隨 ff-merge 進 main」理由行；具名 add 只帶指名檔——檔案在 WT 有即時 board 可見性
- **懸掛 working tree 與切回 main 兩者皆禁**：前者會被活躍 session 批量 add 誤帶，後者共享 WT 切 branch 干擾活躍 session；分流 why——建卡進 main 讓線性乾淨（card commits 不搭弧便車），小修留 branch 因常與弧檔案有 context 關聯且需即時可見
- **同 session 暫停弧形態**：被 user 叫停的卡弧佔 primary WT 時，新弧規劃段（建卡/EP/卡面修訂/雙審）落 owning 線 main——`checkout main` 前先機械對帳 working tree（handoff 宣稱的「在飛未提交變更」可能不存在）；被暫停卡的 branch＋metadata commit 原樣保留（不回滾不 `-D`），恢復＝該 branch 續行、先 rebase main 吸收卡面修訂

**預掃衝突處置**：預掃輸出的全域最高 id 高於本 WT 所見最高 id → 他 WT 有未進版控的更高卡，CLI 自動配 id 會撞號 → **停下協調**（他 WT 卡 commit 進 branch 後 cross-branch 掃描接手，再建卡），不得就地建。

**共享 WT 建卡 id 佔用查驗三面**（多 session 共享單 WT、撞號反覆發生後強化——working copy 單一真相不豁免）：①本 WT `ls backlog/tasks/`＋`git status --porcelain backlog/tasks/`（untracked／staged 新建——porcelain 面抓平行 session 未 commit 卡檔，`??`＝untracked、`A `＝staged）；②`git ls-tree <各未 merge branch> backlog/tasks/`（他 branch 上的卡本 WT 看不到）；③`git log --all -- 'backlog/tasks/<prefix>-*'`（卡 id 不可重用——歷史重用同樣撞）。撞號修復先例＝owning branch 上 `git mv`＋frontmatter id 改（任務保留不廢棄）。
**建卡 spec gate**（跨 session To Do 卡必過；session 內即辦豁免）：工單三必有住 `Implementation Plan`——①`baseline`（`〔baseline：<repo> <hash>〕`）②`已決策勿重辯`（`〔已決策勿重辯：①…〕`）——驗收條款（③）住 AC；語義在場即可，標記形式不限。軟自查：`rg -c "baseline|已決策|驗收" backlog/tasks/<卡>.md` 應 ≥3（豁免卡除外）。風險面屬性標註（「寫入契約首改」「跨文件交叉推導」「無保護面新能力」）是「已決策」段的合法內容形態。
**欄位分工（desc 人話／Plan 工單）**（user 拍板——board 不只是 AI 工單池，也是 user 的主視圖；09-15 改制取代舊〔human-summary〕desc 頂部標記慣例）：①`title` 用人話——避免 AI 術語壓縮堆疊（治理黑話/多技術名並列），判準＝非本 repo 的開發者一眼知道這卡在幹嘛；機器檢索面靠 id＋labels 承載（人話 triage 靠 desc、spec 檢索靠 Plan），title 不背 AI 檢索職責。②`desc` **全段人話**（1-3 句）：這卡在幹嘛/現在到哪/等 user 什麼——建卡寫初版、開工/結算/結案時更新；AI 工單內容不進 desc。③`Implementation Plan`＝AI 工單 spec（baseline／已決策勿重辯／範圍）——原生欄位零 hack、工具寫回永不重排（檔案段落 canonical 順序＝Description→Plan→AC→Notes→Final Summary，round-trip 實證）；spec 禁放 Notes（Notes 是 `--append-notes` 的 append 目標，spec 會被進度筆記同段堆疊掩埋）。④`AC`=驗收 checklist、`Notes`=append 進度、`Final Summary`=結算。建卡流程＝`task create`（To Do，帶人話 desc）→ `task edit --plan` 補 spec。既有卡下次觸及時順手搬，不專門回填。

**建卡前去重**（中）：`backlog search <關鍵詞>` + 查 `backlog/drafts/`（未承諾草稿歸宿；與同域 `open-items.md`，例：mosaic 側 `marking/open-items.md`）待處理段，命中則復用/連結既有指針，不重複承諾（一行指針 ≠ 承諾，`backlog` 卡 = 承諾）。

**開工——起手式五步**（凡要動某卡的 session——implement 階段 1 是標準入口；automation／監控／report 等衍生 session 不走 implement 亦同）：
```bash
# ① 第一動——平行 session 可見
backlog task edit <id> -s "In Progress"   # 🔴 必是動卡的第一個動作
# ② 讀卡全層：frontmatter → desc（人話）→ plan（spec）→ AC → notes → references
# ③ 讀卡知形態：references 有無 EP——承諾時已定（不重判）；scope 遠超 Plan → 先升 EP 再動工
# ④ 新鮮度核對：Plan baseline vs `git log --oneline <baseline>..HEAD` 非空→對照 Plan 範圍；notes relay 宣稱→機械驗證當前狀態
# ⑤ 開工雙 ref（09-11 新制：只掛 repo 相對路徑，不掛 http——免 report-server 存活依賴）
backlog task edit <id> --ref "<EP repo 相對路徑>[,<shell index.html 相對路徑>]"
```

（採卡 branch 的 repo 在 ⑤ 之後另有 **⑥ checkout 卡 branch**——規則源＝該 repo AGENTS.md「git 慣例」節；通用起手式恆五步，⑥ 是 repo 層擴充）

**開工 metadata 即 commit（user 09-11 特赦）**：起手式 ①⑤ 的 backlog 檔變更（In Progress＋雙 refs）隨後立即 commit **僅 `backlog/`**（message `chore(backlog): <id> 開工…`）——卡狀態是跨 WT 可見性契約，未 commit 平行 session 看不見；例外條款單一源＝[outward-action-consent](../../rules/outward-action-consent.md)「Commit 專屬段」②；Capabilities／程式碼結算物不隨此例外。

**board single-writer 例外分工（09-16）**：automation／衍生／spawned session 的開工狀態翻轉改為**唯讀判定＋verdict 回報 board-control（marshal／主 session）代為落盤**——本段舊文「衍生 session 不走 implement 亦同（做第一動）」自 single-writer 條款（見下）生效日起由 board-control 代行，衍生 session 本身不執行 ①⑤ 的卡 metadata 寫入。

**🔴 雙 ref 合約**（09-11 新制：只掛 repo 相對路徑——ext／VSCode 直接消費：`.md`→編輯器、`.html`→外部瀏覽器；新卡不掛 http URL）：
- 第一值＝EP（無 EP 的 simple 卡掛主交付物）的 repo 相對路徑（必備）
- 第二值＝report shell `index.html` 的 repo 相對路徑（有殼才並列；殼未建不寫 viewer 過渡 URL——EP 路徑一點即編輯器／preview）
- 既有卡 http 值由批次遷移清除（pilot MOS-93）；過渡期殘留視為待遷，不視為錯誤
- 已知取捨：browser（on-demand 後備）上相對路徑不可點（`TaskDetailsModal.tsx:1362-1375` 只 linkify http(s)）；主力 UI＝ext 直接開檔不受影響

**結案兩步**（收斂後——post-build hook 2／無 post-build 弧走 implement 階段 6 fallback；ref 路徑生命週期隨任務目錄遷 `done/` 變更）：
```bash
backlog task edit <id> -s Done --final-summary "<一句>"
backlog task edit <id> --ref "<done/ EP 相對路徑>[,<shell 相對路徑>]"   # --ref 整組替換
```
**結案 metadata commit 特赦（user 09-11，條件授權鏈；autonomous 適用性 09-13 user 裁定收回）**：結案兩步＋其 commit（僅 `backlog/`＋結算搬移檔、**同 commit**）在 **precheck 綠（跨線掃描 exit 0）** 時免逐次確認——機械守門替代人確認（例外條款③，**限互動 session**；autonomous session 所有 commit 一律待用戶確認）；條件不滿足 → 走確認 gate。註：precheck 在此是特赦的守門條件，非結案兩步本身的新要求（「結案兩步不需 precheck」現狀不變）。

**弧結案蒸餾（第三動，同時機）**：owning session 將本弧 project_/feedback_ memory 條目重寫為終態 facts——刪日期/session id/進度流水與 git 可推導內容，留決策教訓與終態結論，敘事指向 repo 檔案（EP/卡）；無相關條目明示無。規則細節＝[memory-audit](../memory-audit/SKILL.md)「寫入端紀律」（含 desc 三不）。

結案後**卡留 board Done 欄**（官方預設工作流——Done 欄可見＝完成工作可見）；`task complete <id>`（搬 `completed/`）是清場動作，延後到 board 清理批次（maintain 週期）或 user 指示，不隨結案當場執行。**清理批次自動腿**：ai-guide／mosaic 每日排程跑 `deploy/scripts/run-backlog-cleanup.sh`（時刻/plist 見 ai-guide ai-analysis/schedule-registry.md——launchd 表＋反查表 A3）——`Done` 且 `updated_date`>30d 的卡逐卡 precheck → `task complete` → commit（`BACKLOG_CLEANUP_AGE_DAYS` 可覆寫；多 worktree 全展開，跨線訊號卡保守跳過）。CLI 原生 `backlog cleanup` 是互動式 TUI（stdin 關閉時假成功 no-op），不可用於無人值守。

**🔴 清理前跨線掃描**（凡 `task complete`／歸檔／清板之前，強制先跑；結案兩步本身不需 precheck——結案 Done 留板可見）：
```bash
bash <skills 根>/kanban-board/scripts/backlog_precheck.sh [卡id ...]   # skills 根：ZCode ~/.zcode/skills、Claude ~/.claude/skills（symlink 同源）；無參=掃全部 To Do 卡；exit 1 = 停手
```
腳本檢查：①`status=In Progress` 卡永不可清；②跨線訊號 `git log --all --not HEAD --grep <卡id>`——「有 commit 提及此卡、但當前 branch 不包含」＝真平行線訊號（裸 `--all --grep` 會命中本線建卡 commit，永遠誤報）。exit 1 → 停手先協調，不就地清（真實案例：分岔 branch commit 標題含卡 id、平行 session 對同卡各自結案，此檢查可攔下）。

**掃描**：
- AI 消費：`backlog task list --plain`（非互動 canonical 輸出）
- 機械消費：`--json`（**僅 list/view/task/search 四指令支援**）
- 想法池：`backlog draft create "<想法>"` → Drafts 頁累積 → 拍板 `backlog draft promote <id>`（想法→承諾）

**backbone triage（user 拍板）**：優先序 backbone 由 project blueprint 決定（target 形態＋收斂序列，見 `ai-analysis/blueprint/`）；未被 backbone 支撐的 To Do 卡須定期 triage——升主線候選／demote → draft／archive，To Do 池只留近期可開工承諾。

**遠期卡治理（draft vs archive vs Icebox）**（實證 2026-09-03，例：mosaic `MOS-2/3/7 → DRAFT-1/2/3` 後 `To Do: MOS-10/16 + Done 7`；決策見 [Backlog.md 治理設計](../../ai-analysis/_tasks/done/09-03-backlog-governance-design/design.md)）：
| 情境 | 動作 | 命令 | 版面效果 |
|------|------|------|----------|
| 遠期研究/暫緩（`To Do` 噪音） | **demote → draft**（官方停車場） | `backlog task demote <id>` → `backlog/drafts/draft-*.md` | board 完全隱形；`backlog draft list --plain`/`view DRAFT-x --plain`/`browser /drafts` 可見；`search`/`board` 不撈 |
| 廢棄/永不做 | **archive** | `backlog task archive <id>` → `backlog/archive/` | 同上隱形，但語義為廢棄 |
| 想保留 To Do 可見性 | **不加 Icebox 欄** | 維持 `statuses [To Do, In Progress, Done]` 三欄，遠期用 `draft` 替代 | 加 `Icebox` 仍多一欄、噪音未根除；`To Do` 應只留可開工承諾 |

- 起手式：`backlog draft list --plain` 巡 `drafts` → `backlog draft view DRAFT-x --plain` 看內容 → `backlog draft promote DRAFT-x` 回 `backlog/tasks`（遠期如 `ECPPE` 可先記 `ai-analysis/_projects/<線>/open-items.md` 一行指針，熬到可開工才 `task create`，避免先佔承諾池）

**註記追加**（消費場景等）：`backlog task edit <id> --append-notes "<文字>"`

**🔴 board single-writer（多 WT 形態，09-16 AIR-72 定案）**：卡 metadata（status／refs／id allocation／final summary）只有 **board-control**（marshal／主 session，依 blueprint 寫入責任決策樹）可寫；**spawned／衍生 session 禁碰卡 metadata**（**board-control automation（backlog cleanup 批次）除外**——`run-backlog-cleanup` 的 `task complete`＋commit 為既有合法自動腿，見「清理批次自動腿」段）——禁 `task edit`／`task create`／改 `backlog/` 卡檔，worker 發現一律經 verdict 回報、由 board-control 落盤（execution plane 可讀 card state，不寫）。開／收 WT 的互斥鎖＝`scripts/wt-open.sh`／`wt-close.sh` 的共享 `.git` mkdir lock。卡 metadata 的 **marshal 單點 commit 慣例**：metadata commit 集中由 board-control 單一主體執行（建卡①／開工②／結案③特赦皆同主體，例外條款單一源＝[outward-action-consent](../../rules/outward-action-consent.md)「Commit 專屬段」）——多 WT 下這是撞寫防線，不是風格偏好。

**🔴 卡編輯前查驗**（凡 `task edit`——開工/結案/改 refs/註記同；非跨線掃描 precheck〔那是 `task complete` 前置〕）：
- **對時卡 id 歸屬**：只引用建卡 CLI 回報的 id，禁假設下一號（編號會被平行 session 佔走——真實案例：假設下一號 AIR-26 實配 AIR-28，`task edit -s --ref` 打在平行 session 的**已結案卡**上，refs 被整組替換毀掉、status 被覆蓋）；對非本 session 建的卡操作前先讀卡（status/refs 對時）——「本 session 無其他寫入者」保證可能數小時內過時
- **`--ref` 整組替換即毀原 refs**：誤打他卡＝直接毀卡（結案兩步靠此語義換路徑——見上結案 bash 註解）
- **誤改復原**：已 commit 卡被誤改 → **先確認該卡 diff 全屬本次誤改**（共享 WT 下他人合法未提交變更在同檔＝停，依 collaboration-constraints 機械衝突訊號確認）→ 才 `git checkout HEAD -- <卡檔>` 全量復原（反向 CLI 操作不夠——格式化差異會留 diff）
- **SECTION marker 雙包裹檢查**：`task edit` 類操作可把 `<!-- SECTION:*:BEGIN/END -->` 成對寫成兩層嵌套（CLI 讀卡正常不報錯、肉眼易漏——真實案例：結案複審以「marker 重複」抓到）；檢查＝`rg -c "SECTION:FINAL_SUMMARY:BEGIN" backlog/tasks/*.md` 任一檔 >1＝dup（其他 SECTION marker 同型風險）；修法＝去重留一對，發現一例後全板掃描確認是否孤例；commit 前複審抓「格式重複」類 finding 先機械驗證再修

## 卡即 handoff（卡拼裝＝self-contained）

卡 `desc`＋`plan`＋`AC`＋`notes`＋`references`＋`EP`（若有）拼裝即 handoff——接手 session 讀卡即接手，不重辯已定事。分工：`desc`=人話摘要層（詳「欄位分工」）／`Implementation Plan`=決策層（baseline／已決策勿重辯／範圍，不變共識）／`AC`=驗收層／`EP`=規劃層（怎麼做）／`notes`=留言層（接手指針，過程不沉澱）。兩層判定承諾時已定（見 [execution-plan](../execution-plan/SKILL.md) 規模分級，不新造）：small 不建 EP 直行、standard+ 建 EP。決策層變更（scope／驗收校準）→同步回寫卡 Plan／AC。

## UI 入口

board server **常駐已退役**（09-11 三方裁定：state ownership 在 primary 的 `backlog/tasks/*.md`，UI 載體可替換——launchd/plist/固定埠治理一併移除）：

| 形態 | 命令／載體 | 說明 |
|------|------|------|
| **VSCode extension（主力）** | `chtai.backlog-cards`（activity bar 巡覽＋點卡詳情＋references 直達：`.md`→預設編輯器、`.html`→外部瀏覽器、http→Simple Browser（停用退外部）） | 唯讀 browse；workspace 含 `backlog/config.yml` 自動啟用 |
| TUI 快照 | `backlog board` | 終端 markdown 三欄板，即開即退；CJK 寬度留意 |
| AI 面 | CLI（現行）／`backlog mcp`（stdio MCP） | 直讀寫 md，零 server |
| 瀏覽器（on-demand 後備） | `backlog browser --no-open --port <port> &` | CLI 內建子命令，隨叫隨開、用完 Ctrl+C；**port 衝突靜默跳下一個可用埠——起後 `lsof -iTCP:<port> -sTCP:LISTEN -P` 驗證實際綁埠**；6421 保留給 report server 勿佔 |

## 與官方工作流的差異宣告（兩條）

1. **PLAN 不寫進卡**——實作計畫唯一源＝EP（任務家 `<task>/ep.md`）；卡用 `references` 指回 EP/殼（EP 深度＝baseline hash/Report Shell/post-build 鏈，是卡 PLAN 欄位的超集）
2. **任務與分支預設解耦；採卡 branch 的 repo 以其 AGENTS.md「git 慣例」節為準**（多 worktree 紀律由各 repo 自訂）；spawned／automation session 的 owning-WT 約束單一源＝[collaboration-constraints rule](../../rules/collaboration-constraints.md)「Agent 派發與產出回收」（always-load 層—— spawned session 不載本 skill 也約束得到）

## 容錯

無 `backlog/` 目錄 → 卡片動作整項跳過不報錯（board 是 repo opt-in 層；任務追蹤退化為任務目錄存在性）。
