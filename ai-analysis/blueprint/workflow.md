# AI coding 開發工作流

> **定位**：本檔把 ai-rules 的工作從「想法」到「運維」收斂成一條可執行主軸，並描述多 session 下 primary、card worktree、board 與 memory 的目標 ownership；尚未落地處明確標示現況。

## 八站主軸

工作流沿同一條主軸理解：

```
① 想法 → ② 規劃 → ③ 開工 → ④ 實作 → ⑤ 驗證 → ⑥ 收斂 → ⑦ 沉澱 → ⑧ 運維
```

| 站 | 一句職責 | 關鍵載體 |
| --- | --- | --- |
| ① 想法 | 把未承諾想法留在 draft／pending 區；一旦承諾工作才由 board control plane 建立 card 與配置 id | Backlog.md draft/task、pending decisions、建卡預掃 |
| ② 規劃 | 把 card intent 轉成可跨 session 接手的 self-contained research／spec／EP，固定 baseline、scope、已決策與驗收；task-home 報告殼的 source＝shell-ready md＋meta（殼是 deterministic viewport 非手寫產物——codegen 契約見 [illustrate-html-mode](../../skills/_common/illustrate-html-mode.md)，AIR-73）；**top-level 測試規劃段在實作段落前凍結 TC＋高風險/P0 pre-RED challenge（跨家族 blind-derive；v3.1 已落檔——execution-plan 測試規劃段）** | card `desc`、task home、`research.md`、`spec.md`、`ep.md`、shell-ready md、測試規劃段 |
| ③ 開工 | 為已存在 card 建立「由哪個 branch/WT 執行、起點是哪個 baseline、session cwd 在哪」的機械身份 | `wt-open`、card `In Progress`/refs、persistent card WT、freshness check |
| ④ 實作 | 讓 code/rules/skills/docs/EP 寫入在該工作 execution plane 內完成，避免共享 checkout 的 branch/cwd 被其他 session 改變 | card WT；免卡小修走 ephemeral WT fast-path；implement/TDD |
| ⑤ 驗證 | 讓 claim 對上足夠獨立的 evidence；negative claim 不以單次文字搜尋冒充行為證明；**測試驗證分工＝契約消費（frozen TC）＋provenance 三栓＋mutation authority gate＋軸A 機械審計／軸B 架構審查（v3.1 已落檔——implement／audit-test 角度 8／code-review 軸B／fix-test gate）**；**外部實作委派帶 `--yolo`（user 09-11 拍板 implement 一律）＋liveness ticker 防卡住（model-routing skill）** | tests、integration/demo/POC、code-review、acceptance evidence、TC＋audit/review 雙軸、yolo＋ticker；⚠️ [instruction-testing](../../skills/instruction-testing/SKILL.md) 承載 instruction artifact 行為驗證方法，pilot 尚未實跑 |
| ⑥ 收斂 | 把工作 review、修正並依既有 rebase→ff-only 規則吸回 owning line，再完成 session/card 收尾；Report Shell refresh＝更新 shell-ready md→`build_shell.py` 投影→gate 自驗（AIR-73 落地前為 LLM 手填殼 legacy）；**政策翻轉 consumer-propagation gate（AIR-75）——retire／政策句改寫弧的殘留偵測與傳播收口（post-build skill）** | post-build、working branch、`wt-close`、finalization、`build_shell.py`、policy-reversal gate |
| ⑦ 沉澱 | 將完成能力、設計理由與真正值得跨 session 留存的事實放回正確 carrier；memory 不成為規範副本 | AGENTS/Capabilities、architecture/blueprint、memory pointer/facts |
| ⑧ 運維 | 讓 hooks、排程、備份、清理與 fresh-machine recovery 可重建，避免 machine-local state 只存在某台機器或某次 session | hooks、schedule registry、launchd、memory bundle、onboarding runbook、code-reality |

八站是整體敘事，不取代各 skill 的細部 workflow。免 UC 的小型 fix 可以不建立 card/EP，但仍須有明確 execution plane、validation 與收斂路徑。

### 逐站怎麼做（導引層）

> 本表＝「八站 → 入口命令／詳讀來源」的人類 lifecycle mapping 單一源（index.html section 02 投影自此）；只列 command/skill ID＋link＋runtime status，**不重述 command 內部步驟**——command 語義以各 `skills/<x>/SKILL.md` 為權威，LLM 端命令拓撲在 [skills/AGENTS.md](../../skills/AGENTS.md)。command rename／退役／生命週期位置改變時，覆核本表再刷新 projection。

| 站 | 怎麼做 |
| --- | --- |
| ① 想法 | **入口**：未承諾想法留 draft／pending；決定承諾時依 [kanban-board](../../skills/kanban-board/SKILL.md) 建 card，不先進實作流程。**詳讀**：看板生命週期與建卡／狀態／refs 以 kanban-board 為準。 |
| ② 規劃 | **入口**：需求仍需釐清可先 `/spec`；正式規劃走 [`/execution-plan`](../../skills/execution-plan/SKILL.md)，需要獨立覆核時用 [`/ep-review`](../../skills/ep-review/SKILL.md)，高技術風險假設可加 [`/ep-validate`](../../skills/ep-validate/SKILL.md)。pre-EP whole-picture 可用 [`/illustrate`](../../skills/illustrate/SKILL.md) 作人類 viewport。**詳讀**：[spec](../../skills/spec/SKILL.md)／[execution-plan](../../skills/execution-plan/SKILL.md)。 |
| ③ 開工 | **目標入口**：`wt-open <card>` 建立 card branch／persistent WT／baseline／cwd identity——**⚠️ 已落地（09-16 AIR-72）**：`scripts/wt-open.sh <card> --base main`（試點通過——AIR-73 dogfood）；未走 WT 的卡照舊依 [repo AGENTS.md「git 慣例」](../../AGENTS.md) 建 card branch（雙軌過渡條款，同卡禁混用），並依 [kanban-board](../../skills/kanban-board/SKILL.md) 完成 In Progress／refs 起手式（卡 metadata 寫入＝board-control）。**詳讀**：本檔「Worktree 形態定案／過渡條款」。 |
| ④ 實作 | **入口**：標準 EP 工作走 [`/implement`](../../skills/implement/SKILL.md)；程式邏輯變更依 [test-driven-development](../../skills/test-driven-development/SKILL.md) 的 TDD 方法。**execution plane**：target 為 persistent card WT／免卡小修 ephemeral WT；helper 已落地（`scripts/wt-open.sh`，含 `--ephemeral`）——雙軌過渡期，未走 WT 的卡仍依 repo AGENTS.md 現行 card-branch 慣例執行。 |
| ⑤ 驗證 | **入口**：實作流程內依 `/implement` 執行測試與 [`/audit-test`](../../skills/audit-test/SKILL.md)；instruction artifact 另依 [instruction-testing](../../skills/instruction-testing/SKILL.md) 做行為驗證。**詳讀**：[acceptance-evidence rule](../../rules/acceptance-evidence.md)＋[acceptance-evidence skill](../../skills/acceptance-evidence/SKILL.md)。（變更級獨立 review：邊界觸發的段級 review 在④由 `/implement` 啟動，全弧獨立 review 在⑥收斂站由 `/post-build` 編排——皆非本站日常入口） |
| ⑥ 收斂 | **入口**：[`/post-build`](../../skills/post-build/SKILL.md) 編排 `/code-review` → `/judge-review` → 修正 → consistency／metadata finalization；人類方向／結構 checkpoint 按需用 [`/illustrate`](../../skills/illustrate/SKILL.md) 或 [`/debrief`](../../skills/debrief/SKILL.md)；最後走 [`/commit`](../../skills/commit/SKILL.md)。**git 收斂**：target 為 `wt-close`——**⚠️ 已落地（09-16 AIR-72）**：`scripts/wt-close.sh --wt <path>`（`--preflight` 全檢查零變更，trunk 收斂由 marshal 收線自主執行（AIR-200 predicate delegation——fresh receipt＋ff-only＋控制面 landing eligible）；真卡收線已驗——air-77 首例 74d483d；receipt 每次執行自動落盤 .git/wt-close.log（AIR-112））；未走 WT 的卡依 [repo AGENTS.md「git 慣例」](../../AGENTS.md) 的 rebase→ff-only 規則。 |
| ⑦ 沉澱 | **入口**：通常由 `/implement`／`/post-build` 內的 [metadata-sync](../../skills/metadata-sync/SKILL.md) 把 Capabilities、SYSTEM-MAP、architecture／相關 metadata 收回正確載體；跨 session 事實再依 [memory-audit](../../skills/memory-audit/SKILL.md) 判斷，規範正文不得複製進 memory。**詳讀**：repo `AGENTS.md` 的載體治理＋memory-audit 載體統一定義表。 |
| ⑧ 運維 | **入口**：例行維護走 [`/daily-maintain`](../../skills/daily-maintain/SKILL.md)；fresh-machine／重建路徑從 [onboarding.md](onboarding.md) 進入。**詳讀**：[maintain](../../skills/maintain/SKILL.md)；排程現況看 [schedule-registry](../schedule-registry.md)，code-reality 接線看 [code-reality skill](../../skills/code-reality/SKILL.md)。 |

## Worktree 形態定案

正式裁決採「control plane 與 execution plane 分離」，分界按**寫入責任**，不是按任務時間或大小。

### Primary checkout：control plane — ❌ target 尚未落地

目標形態：

- primary 固定承擔 owning line／trunk 的 control-plane checkout，不供一般實作 session 任意切 working branch。
- primary 的 repo 寫入職責限於 board/card control state：task id allocation、status、refs、final summary 與同類 runtime metadata。
- board 唯一 working-copy owner＝primary 的 `backlog/tasks/*.md`（state ownership）；UI 載體可替換（VSCode extension 主力／TUI／`backlog browser` on-demand），不設常駐、不定義 ownership。
- code、rules、skills、一般 docs、EP、test、script 的工作寫入走 execution plane。
- 建立／結束 execution WT 的 helper 從 control plane 發起，並用 lock 序列化 board state 變更。

目前 repo 為**雙軌過渡**：卡可走 persistent card WT（control/execution plane 分離生效），未走 WT 的卡仍在 primary 自 `main` checkout card branch（過渡條款）；因此上述 permanent control-plane 行為要等 checkout 模式退役才算完全落地。

### Card worktree：execution plane — ⚠️ 已落地（09-16 AIR-72；與 checkout 模式雙軌並存）

有 card 的寫入型工作目標採：

```
1 card = 1 branch = 1 persistent worktree
```

- branch 命名、owning line 與最終 rebase/ff-only 規則仍由 repo `AGENTS.md`「git 慣例」定義。
- WT 從 committed owning line 建立；未提交 primary working-copy 狀態不視為 card baseline。
- 一張 card 跨 session 接續時重用同一 persistent WT。
- 同一 card identity 可供 writer 與 reviewer 指向同一份工作狀態；**共用 identity 表示可共同讀取並按流程串行寫入，同檔並發寫仍按 collaboration constraints 處理；board metadata 另外受 primary single-writer 限制。**
- execution plane 可讀 card state；目標架構下不直接寫 board runtime metadata，status/ref/finalization 由 control plane 處理。

`wt-open`／`wt-close` 與 persistent card WT lifecycle **已由 AIR-72 落地**（09-16：`scripts/wt-open.sh`／`scripts/wt-close.sh`；wt-open 試點通過，wt-close 經 pipe-test、真卡收線已驗——air-77 首例 74d483d；receipt 每次執行自動落盤 .git/wt-close.log（AIR-112））——本節維持 target contract 定位，實作差異以各段標記與腳本檔頭「設計決策」為準。

### 免卡小修：ephemeral WT fast-path — ⚠️ 已落地（09-16 AIR-72：`scripts/wt-open.sh --ephemeral <name>`）

全域 guide 允許 simple bug fix／小型調整免 UC、免建 card；WT 化不能反過來強迫所有微小工作先造卡。

目標 routing：

```
免卡 + 會寫 repo
        ↓
建立 ephemeral working branch / WT
        ↓
修改 + 驗證
        ↓
依既有 consent 做 commit / 收斂
        ↓
移除 ephemeral WT
```

約束：

- 不為了取得 WT identity 人工製造假 card。
- ephemeral WT 只適用真正符合 guide 小型免 UC 條件的工作；碰單位、時區、會計、風控、跨模組架構等仍依既有規模規則升級。
- 若修改過程擴大成 standard+ 工作，停止 fast-path，先建立正式 card/EP，再轉 persistent card WT。
- primary 仍不因此重新成為一般 code writer。

helper 已定案：由 `wt-open --ephemeral` 承載（`scripts/wt-open.sh --ephemeral <name> --base <ref>`——免卡、branch＝`ephemeral/<name>`、base 顯式規則與 card 模式相同）。

### 唯讀／顧問 session — ⚠️ 現有做法可支撐，尚未統一機械化

- 只讀當前 card 實作：target 形態下優先進該 card WT，使所見 source 與 writer 一致。
- 跨 card audit／顧問：可使用 clean read-only checkout、detached/ephemeral WT 或其他不會改變 active writer cwd/branch 的環境。
- 純架構討論、外部顧問、report 閱讀不必為形式上的「一 session 一 WT」建立 persistent working copy。
- 跨 repo 工作回到各 repo 自己的 ownership，不把 ai-rules primary 當另一 repo 的 execution plane。

## 過渡條款：現行 git 慣例與 target WT 形態

目前 repo AGENTS.md 的有效規則仍要求卡開工後從 `main` 執行 `git checkout -b air-<N>`，收尾再 checkout `main` 並 ff-only merge。這與「primary 永久留 control plane」的 target 形態互斥。

過渡期規則：

1. **WT 基建弧已落地（09-16 AIR-72）**：repo `AGENTS.md`「git 慣例」已補雙軌過渡條款——未走 `wt-open` 的卡仍以 checkout 模式為 runtime authority；本檔 WT 章節升為可執行參考（實作差異以腳本為準）。
2. **基建弧落地時**：同一弧同步改版 repo `AGENTS.md`「git 慣例」與 kanban 消費接線（board single-writer 條款、check_active_branches 切換、建卡預掃 porcelain 面）——已完成。
3. **改版完成後**：`workflow.md` 的 target 標記已依實際驗證結果升為 `⚠️`（wt-open：試點通過；wt-close：pipe-test 驗證、真卡收線已驗——air-77 首例；receipt 每次執行自動落盤 .git/wt-close.log（AIR-112））。
4. 過渡期間不得混合兩種 lifecycle，例如 primary 已切 card branch、同時又建立同 card persistent WT，否則 ownership 再次不唯一。

## 寫入責任決策樹

```
這個動作會寫入嗎？
│
├─ 否
│  ├─ 只看當前 card → 讀該 card 的 current execution state
│  └─ 跨 card / 顧問 / audit → clean read-only checkout 或 ephemeral WT
│
└─ 是
   │
   ├─ 寫 board/card control state？
   │  └─ primary control plane
   │     └─ 經 single-writer lock 做 id / status / ref / finalization
   │
   ├─ 有 card，且寫 code / rules / skills / docs / EP / tests / scripts？
   │  └─ 該 card persistent WT
   │
   ├─ 無 card，且符合 guide 的小型免 UC 條件？
   │  └─ ephemeral WT fast-path
   │     └─ scope 擴大時升正式 card
   │
   └─ 寫另一個 repo？
      └─ 到該 repo 自己的 control/execution topology
```

判斷核心是「這份 state 的唯一 writer 是誰」。execution identity 可以多人共讀；寫入仍要有明確 serialization／ownership。

## 記憶池拓撲 — ⚠️ primary canonical pool 已落地；card-WT 接線尚未落地

### Primary canonical state：✅

primary repo 內既有 canonical state：

```
<primary>/.agents/
├── memory/          # 實體 canonical pool
└── memory-inbox/    # 實體 canonical inbox
```

WT 化沿用這個 canonical state，不重新遷移 memory 主體。

### Card WT 接線：✅ 已落地（wt-open 內建）

每個 persistent card WT 目標只建立兩條 repo-local symlink：

```
<card-wt>/.agents/
├── memory       -> <primary>/.agents/memory
└── memory-inbox -> <primary>/.agents/memory-inbox
```

約束：

- 不複製 live memory pool；每 WT copy 會形成多份 snapshot，破壞單一真相、CAS、attribution 與 consolidation。
- 不 symlink 整個 `.agents/`；只共享已裁決的 `memory` 與 `memory-inbox` state。
- 夜間 consolidation 仍只消費一份 canonical inbox/pool。
- primary 既有 CC/ZCode memory topology 不因 WT 化重新設計。
- Muse secondary WT 對 directory symlink 的 native memory 能力可能退化，因此 native `read_memory` 不列為所有 secondary WT 的 invariant；必要時按正式契約使用可達 canonical state 的 fallback。
- Muse write gate 必須最終把寫入導向 canonical inbox。

Muse hook 接線策略已由 AIR-79 落地並完成 cutover：user-scope plugin `muse-memory-governance`＋repo marker 三態（install/approve 每機一次，marker 隨 repo 走）——「每 WT 生成 hooks.json」與「參數化生成」兩案的共同後繼形態，plugin 為唯一寫入閘（過渡期 legacy per-repo 註冊與 launcher 已退役）。

## Board single-writer — ⚠️ 大致落地（09-16 AIR-72）

落地現況：`backlog/config.yml` `check_active_branches: true`（`backlog task list --plain` 實證）；kanban skill「board single-writer」條款（卡 metadata 只有 board-control 可寫、spawned worker 禁碰）＋建卡預掃 porcelain 面；wt-open／wt-close 的共享 `.git` mkdir lock 序列化開收交易。殘項：card WT 內禁 `task edit` 目前是語義條款（kanban skill）非機械 enforcement。

目標 invariant：

- backlog/config.yml 使用 `check_active_branches: true`，讓多 WT repo 能發現其他 branch 已 commit card，並讓 cross-branch id 掃描生效。
- board UI 載體不設常駐（VSCode extension 為主 viewport；`backlog browser` on-demand 後備）。
- `backlog/tasks` runtime metadata 只有 control plane 是 writer。
- card WT 不直接執行會修改 card runtime state 的 `backlog task edit/create/complete`。
- 建卡 id allocation、開工 status/ref、收尾 finalization 經 control-plane helper，在 repo-local single-writer lock 下執行。
- 建卡保留跨 WT filesystem max-id 預掃，補 `check_active_branches` 看不到 untracked/staged card 的盲區。
- `check_active_branches` 只解 cross-branch discovery；working-copy local card 仍可能遮住其他 branch 同 id 狀態，因此不能以 config flag 取代 single-writer ownership。

09-16 起 `backlog/config.yml` 已切 `check_active_branches: true`（AIR-72）。

control-plane metadata commit 授權（user 09-11 裁定）：建卡＋開工 metadata 特赦；結案兩步 metadata 走條件授權鏈（precheck 綠＋結算物與卡狀態同 commit）——單一源＝outward-action-consent「Commit 專屬段」，blueprint 不另行擴張。

## `wt-open` / `wt-close`：目標 transaction — ⚠️ 已落地（AIR-72；wt-open 試點通過、wt-close pipe-test 驗證＋真卡收線已驗——air-77 首例；receipt 每次執行自動落盤 .git/wt-close.log（AIR-112））

`wt-open` **只接收已存在 card**。建卡與 id allocation 屬①想法站的 board-control 工作，不塞進開工 transaction。

### 1\. 取得 control-plane lock，讀取已存在 card

`wt-open <card>` 在 primary 取得 single-writer lock後：

- 確認 card 已存在。
- 讀 baseline、已決策、驗收、notes、refs。
- 依 kanban 開工語義處理 `In Progress` 與開工 refs。
- 若這些 metadata 必須成為新 WT 的 committed baseline，依基建弧最後裁定的 commit/consent contract 處理。

找不到 card 時直接停止；`wt-open` 不代建卡、不 allocate id。

### 2\. 建立或重用 persistent card WT

由 committed owning line 建立：

```
owning line → card branch → persistent card WT
```

- branch 命名沿 repo `AGENTS.md` 的 repo-specific 規則。
- branch 已存在時，先驗 owning line 到 branch 的 commits 是否確實屬此卡。
- 非本卡殘留不得直接重用。
- WT path 使用可由 card/branch 機械推導的固定形態，避免 handoff 依賴人記路徑。

### 3\. 驗證 baseline 與 execution identity

啟動 writer 前至少驗證：

```
{git toplevel, current branch, card id, baseline}
```

並執行既有 freshness 語義：

- card baseline 對目前 owning line / HEAD。
- baseline 後已有 commit 時，判斷是否碰 card scope。
- notes/relay 宣稱回查目前 repo state。
- WT isolation 不構成跳過 freshness check 的理由。

失敗即停止 open transaction。

### 4\. 接 shared state，從 WT cwd 啟動 session

建立 card WT 的：

```
.agents/memory
.agents/memory-inbox
```

兩者都解析到 primary canonical state。

再依 WT 基建弧選定的 Muse 接線方案生成或配置正確 hook。

完成後以 **card WT 作 cwd** 啟動寫入型 ZCode／Claude 等 session；branch、cwd、HEAD、dirty state 後續皆以 Git/current filesystem 現查。

open transaction 成功後釋放 control-plane lock。

### 5\. `wt-close` preflight 與 git 收斂

實作、驗證、review、必要修正與 commit consent 都先在 execution WT 完成。

`wt-close` 重新取得 control-plane lock，並驗：

- target WT / branch identity 正確。
- working tree 無未處理變更。
- commits 與工作 scope 相符。
- owning line 的新變更沒有使原 baseline／relay 假設失效。

接著沿既有收斂規則：

1. owning line 沒前進且 branch 可直接吸收 → ff-only candidate。
2. owning line 已前進 → rebase working branch onto owning line。
3. rebase 成功 → owning line ff-only absorb。
4. ff-only 仍失敗 → 停下查原因。
5. owning line / trunk 本身不被 rebase、不 force。

### 6\. Finalization

只有 git convergence 成功後，primary control plane 才進行：

- status → `Done`
- final summary
- 完成態 refs
- 既有流程要求的 Capabilities／metadata 結算
- 有值得保存的 project memory 時，按 memory-audit 寫入端紀律蒸餾終態 facts

board `Done` 應表示工作已被 owning line 接收，不先於 convergence。

### 7\. 移除 execution plane

finalization 完成後：

- 移除 card WT。
- 刪除已被 owning line 完整吸收的 working branch。
- 用 `git worktree list` 與 ancestry 做最終確認。
- 釋放 lock。
- card 留在 `Done`；archive/complete 仍由既有延後清理與 precheck 負責。

任一步失敗都要保留可判斷的 branch/WT/control state；不得靠刪 WT 或 branch 製造表面完成。

## 收斂序列：既有 git 紀律不變

WT target 改的是 working-directory ownership，不改 trunk-based convergence：

```
execution WT
  │
  ├─ work / validate / review / commit
  │
  ├─ owning line advanced?
  │      ├─ no  → ff-only candidate
  │      └─ yes → rebase working branch onto owning line
  │
  └─ owning line ff-only absorb
         │
         └─ success → finalization → remove WT/branch
```

仍維持：

- trunk 不 rebase。
- 不以 merge commit 迴避 ff-only 失敗。
- branch 承載工作生命週期；WT path 承載穩定 execution location。
- `/rebase all` 等 repo 級操作仍服從既有 active-card 護欄。
- commit consent 不因 WT helper 自動失效。

## Relay freshness check 保留

persistent WT 能解 shared checkout 被別 session 切 branch 的競爭，但不會讓舊資訊自動更新。

因此開工 freshness invariant 保留：

```
card baseline
    ↓ compare
current owning-line / HEAD
    ↓
relay / notes claim
    ↓ mechanically verify
current repo state
```

原則：

- relay 是接手說明，不是 repository truth。
- branch、cwd、HEAD、dirty state、檔案內容由當前環境讀。
- baseline→HEAD 有新 commit 時，先判是否碰工作 scope。
- persistent WT 不構成跳過 baseline 驗證的理由。

WT 處理的是 execution-location interference；relay freshness 是獨立問題，兩者不能互相替代。

## 六線波次在 WT 形態下的語義

衝突矩陣 O1–O8 描述 shared files、定義源與語義先後依賴。每 card 一個 WT 不會讓這些衝突消失。

第一輪排序維持：

```
L6 = AIR-68：跨 repo，可獨立平行

ai-rules 主序列：
L1 = AIR-58
  ↓
L3 = AIR-70
  ↓
L2 = AIR-67
  ↓
L4 = AIR-60
  ↓
L5 = AIR-63
```

- O1 的 `work-order` 是 L3/L2/L4 真正同源衝突。
- O2 要求 L4 先於 L5。
- O3/O5 讓 L4 等 L3/L2 定義先收斂。
- O4/O6/O7 是較弱共享面，WT 只能降低 checkout interference。
- O8 的 `memory-audit` 落點仍由 owning arc 裁決。

WT 基建落地後，可以移除「因共享單一 checkout，所以同 repo card session 絕不能並存」這個機械限制；是否真的平行仍依 shared-file / semantic overlap 判斷，不能直接打散既有波次。

## 人類 viewport 供給：產物怎麼看、放哪 — ⚠️ 架構定案；慣例句未落檔

> 真相源：[viewport 供給架構裁決](../reports/2026-09-10-viewport-serving-architecture.md)（8765 事故、三方諮詢與 user 裁決全記錄）；服務機械事實＝mosaic `deploy/scripts/run-report-server.sh`（:6421 腳本，跨 repo）＋[kanban-board](../../skills/kanban-board/SKILL.md)「UI 入口」＋[schedule-registry](../schedule-registry.md) 條 A5（board browser 常駐 09-11 退役，`run-backlog-browser.sh` 已刪）；放置規範源＝[illustrate-html-mode](../../skills/_common/illustrate-html-mode.md)「產物位置分流」。

三層分工：

| 用途 | 載體 | 性質 |
| --- | --- | --- |
| 日常點開 artifact | VS Code 內建 Integrated Browser（右鍵 `.html` → Open in Integrated Browser，`file:` 直載） | 零 server、零埠、零擴充（VS Code 1.121 起內建） |
| board 卡 refs／跨 repo 穩定引用／md viewer | `:6421` report-server（launchd 常駐；route：`main`/`v2`/`warrant`/`ai-rules`/`viewer`） | addressability 層——stable URL 契約，非「為了預覽而存在的 server」；讀活磁碟（未 commit 內容可達） |
| 手改 HTML 未存檔即時刷新 | Live Preview 擴充（選配） | 內部埠隨 window 漂移；僅編輯期價值 |

規則：

- **臨時 server 淘汰**：session 不再自建 `http.server`——交付路徑（user 自己點開）或 :6421 URL（deep link 場景）。
- **命名空間規則**：Live Preview／任何臨時埠 URL 永不寫進 board 卡或持久引用；持久引用只用 :6421 stable URL。
- **artifact 慣例**：人類 viewport 產物維持自包含單檔 HTML（資產內嵌、無外部 fetch），`file:` 直開成立的前提。
- **origin 分離**：`file:` 與 `:6421` 是不同 origin，頁內 localStorage（如主題記憶）各自保存，不作跨入口契約。

放置規則（規範源在 illustrate-html-mode「產物位置分流」，此處只投影）：

即日起，新弧任務目錄直接落 _tasks/2026-09/<MM-DD-主題>/，不進 done/；歷史 done/ 31 弧由 AIR-77 遷移弧一次收入 _archived/。此慣例使遷移不再追著移動目標跑。

| 產物類型 | 位置 | 入口 |
| --- | --- | --- |
| 弧產物（有卡） | `ai-analysis/_tasks/YYYY-MM/<MM-DD-主題>/`（永不搬移；狀態只看卡 status）；線任務 `_projects/<線>/tasks/`；歷史完成弧一次性收入同家 `_archived/`（凍結） | `index.html`（ep/spec/殼同處） |
| 常設 domain 導覽 | `ai-analysis/<域>/`（如 `blueprint/`） | 域名即路徑 |
| 按需視覺／決策 viewport | `ai-analysis/<域>/`（如 `blueprint/`、`test-contract/`——AIR-74 起 arch-report 退役） | `index.html`（進 git） |
| md 沉澱 | `ai-analysis/reports/` | — |

心法一句：**會動的都在 `ai-analysis/`、弧的家照日期命名、入口一律 `index.html`**（VSCode `Cmd+P` 打日期或主題詞即達；board 卡 refs 是導航主力）。

新 repo onboarding：viewport 面**零步驟**（自包含慣例＋內建瀏覽器即通）；需 deep link 才加 :6421 route（opt-in，非必備件）。

已取消的替代案（裁決記錄見 report §6）：:6421 擴 route 到 repo 根、route 註冊 carrier 中立化、新專案 viewport runbook——「路徑即可點開」成立後均無必要。

待落檔（併既有「四小項」批）：session 交付慣例句、全域 `workbench.browser.autoReloadOnFileChange`、kanban refs 命名空間句。

## 結構治理待建項 — ⚠️ 已定案待落檔

三方結構重構諮詢（muse＋codex，2026-09-11）定案：

- **③ commit 粒度互補規則**（codex 版）：「不同 root cause 若可獨立 revert 且各自保持 repository invariant，應拆 commit；同 root cause 的 source＋consumer synchronization 必須同 commit」——現行 commit skill「同根因同 commit」的互補面，防多主題一顆。落點＝commit skill。
- **④ bundle warning-zone ratchet**（codex 版）：muse 36KiB gate 的 85% warning zone 已在場（deploy_agents.py），但缺防「每次小增直到撞牆」的機械防線——**壓力區（≥warning threshold）時 working-tree bundle 若比 baseline/HEAD 淨增長即 fail**，輸出 per-rule byte delta；縮小或持平放行。落點＝deploy_agents.py＋tests。

## 測試契約與驗證分工 — ✅ 已落檔（三方裁決 v3.1）

> 真相源：[測試契約×驗證分工裁決](../reports/2026-09-11-test-contract-design.md)（user 三輪挑戰＋muse/codex 三輪 session-resume 複驗全記錄；人類 viewport＝ai-analysis/test-contract）。本節是規範投影；**六檔已落檔**（execution-plan 測試規劃段／implement same-family gate＋RED 三栓＋frozen TC carve out／audit-test 角度 8／code-review 軸B 六項／fix-test mutation authority gate），runtime 走 v3.1 流程。

**設計原則**：family separation 放在 **judgment boundary**，不放在 every authorship boundary——獨立性買在「審規格」（challenge）與「審結構」（review），不買在「把 oracle 抄成 pytest」（oracle 凍結後翻譯者近乎不重要）。

分工形態：

- **契約層（② 規劃站）**：EP top-level「測試規劃」段放在**實作段落之前**（文件順序＝時間順序）——TC（claim／Given/When／oracle〔predicate-ID 拆分〕／oracle_source／evidence class／uncovered）在任何人寫實作碼前凍結。oracle 獨立性由「EP 作者↔實作者本來就跨家族」兌現。
- **挑戰層（高風險＋P0 強制）**：pre-RED challenge＝跨家族 advisory、fresh context、**blind derive→reveal**（先自行推 oracle 再比對，防錨定）＋completeness（抓漏場景）；必產 falsifiable 探針。oracle 錯→EP amendment（authority 四分：user intent→人類）。
- **實作層（same-writer）**：實作家族（單一 model、context 連續）照凍結 TC 寫 RED→GREEN→REFACTOR；**provenance 三栓**——RED receipt 落檔存證（非中途 commit）／gate 過後 contract-test digest 凍結／基線跑法（baseline 上必須紅）。撞牆走 **mutation authority gate**（想改哪側 truth→有沒有 authority；改 TC oracle 必經 amendment，「實作現況」永遠不是證據）。
- **審計層（軸A 機械）**：audit-test——TC↔test predicate 對帳／mock↔evidence class／oracle 圓形依賴／receipt＋digest 驗證／基線跑法／fixture provenance／路徑覆蓋反查。
- **審查層（軸B 架構面）**：/code-review dual-context（boundary profile 的 fresh＋primed 雙腿——派發由風險 profile 決定）加一軸——整體測試邏輯 vs diff 結構（拓撲 vs blast radius／層級平衡／符號≠路徑／evidence fidelity／shared dependency／耦合面）；翻譯忠實度明寫不歸它。
- **routing**：`test-gen`＝**P0 最後手段**（啟用條件預寫死：MVP 證明防線擋不住 fixture fidelity 級穿透才啟用）——AIR-70 幽靈角色答案反轉。

**agent 分工原則（判斷密集 vs 機械可驗）**：探索／研究不派 lite——EP 段落 0 全域研究（可複用盤點＋**風險假設識別**）是判斷密集位，`cr-research` 升 **full**；淺研究「自信但薄」→EP 重造既有／漏致命假設，研究省的 token 遠小於錯 EP 的重工。機械子腿（逐字引用、CR 查詢執行）仍可 flash 承接——作為 full 研究者的下游查詢，不獨立出研究結論。

**MVP（卡內第一步）**：seeded fault-injection（Lane A oracle mutant 考 challenge／Lane B 六類架構 mutant 考 audit＋review），量 recall＋誤報＋attribution accuracy＋defect routing correctness，過線標準預凍結。修改面六檔＋研究鏈清單見 report §5。

## 待建基建

基建 substrate 由 WT 基建弧（AIR-72，09-16）整體收斂，現況：

- ✅ `wt-open`：只接已存在 card，建立／重用 persistent card WT（`scripts/wt-open.sh`——試點通過：AIR-73 dogfood）。
- ⚠️ `wt-close`：preflight、rebase/ff-only、finalization、WT/branch removal 的可重入 transaction（`scripts/wt-close.sh`——pipe-test 驗證；真卡收線已驗——air-77 首例 74d483d；receipt 每次執行自動落盤 .git/wt-close.log（AIR-112））。
- ✅ primary board single-writer lock（兩腳本共享 `.git` mkdir lock）＋kanban board single-writer 條款。
- ✅ [backlog/config.yml](../../backlog/config.yml) `check_active_branches: true`，`backlog task list --plain` 實際驗證通過。
- ✅ card WT 的 canonical `memory` / `memory-inbox` symlink 接線（wt-open 內建＋`.git/info/exclude` 防污染面；exclude 為 machine-local 非版本控——新 clone／新機首跑前無保護，首跑 wt-open 即冪等追加）。
- ✅ Muse hooks 處置：`.muse/hooks.json` 已隨 plugin 單閘退役（09-14）——腳本零 hooks 步驟，無死代碼。
- ✅ 免卡小修的 ephemeral WT fast-path（`wt-open --ephemeral`）。
- ✅ repo `AGENTS.md` git 慣例補雙軌過渡條款（checkout 模式與 WT lifecycle 並存，同卡禁混用）。
- ⬜ control-plane status/ref/finalization 與 commit-consent contract 的一致化（隨真卡收線全流程驗證收斂）。
