# ai-rules-three-pool — ai-rules 自家分析側三池對齊（full domain）

> 級別：simple 清單任務（git mv＋引用 sweep＋README——無程式邏輯）
> line: —（本 repo 基礎設施）
> baseline：動工當下 `git rev-parse HEAD` 補記
> 設計脈絡：user 2026-09-02 裁定「我是要 full domain」——ai-rules 自家也採 `ai-analysis/_tasks/` 任務家，與 mosaic 一致；探測規則文字不動（跨專案 skill 需 fallback 給無 ai-analysis 樹的 repo），但 **user 的 repo 群逐一採結構後，實踐上全域一致**（mosaic ✓、ai-rules 本任務、未來 code-reality/codetour 可複製本模式）。

## 🔴 前置 gate（動 S2 前必查）

`git status --porcelain -- 00-tasks/` 必須乾淨——**muse-plugin-cc session（09-02）正在飛**（ep.md＋build-acceptance.md 有未 commit 修改）。樹清才動遷移（並行弧時機 gate 教訓：大批 uncommitted 遷移會污染並行 session 的 diff triage、搬目錄斷其引用）。非 0 → 停，等它收尾。

## 清單

- [x] **S1 建構**：`mkdir -p ai-analysis/{_tasks,archive}`（✅ 2026-09-02）
- [x] **S2 任務家遷入（含本任務自遷）**（✅ 2026-09-02——muse 增補經 user 指示代 commit〔`83a31b4`〕後 gate 解鎖）：root `00-tasks/` 消失、`fd '00-tasks'` 全深度零命中。**教訓**：`git mv 00-tasks ai-analysis/_tasks` 在目標已存在時＝**嵌套**（mv 語義）——發生 `_tasks/00-tasks/` 後以逐檔 `git mv` 攤平＋`rmdir` 修正；正解＝目標不存在時 mv 或先攤內容。另：驗證命令 `-d 2` 深度不足以抓第 3 層嵌套（漏報）——結構驗證用無深度 `fd`
- [x] **S3 退役清債**：`git mv ai-analysis/execution-plans ai-analysis/archive/execution-plans`；`git mv ai-analysis/specs ai-analysis/archive/specs`（✅ 2026-09-02）
- [x] **S4 flow-feedback 決策（已定）**：**保留原名不動**——有 skill 接線＋既有 `_done/` 慣例；角色寫進 S5 README。日後要併 `_inbox/` 另案
- [x] **S5 放置規則單一源**：`ai-analysis/README.md` 已建（✅ 2026-09-02——目錄表＋產物→家＋「衝突時以 skills 探測為準」）
- [x] **S6 引用面 sweep**（✅ 2026-09-02——判定**零活層修正**：skills ×3 是「慣例退役」敘述句〔保留〕、tour-bootstrap 指 mosaic v2 worktree 跨 repo 路徑〔保留〕、reports ×3 歷史報告〔不改寫，同 mosaic 慣例〕；specs 活層引用本來就是零）
- [x] **S7 .gitignore 檢查**（✅ 2026-09-02——root `.gitignore` 無 `00-tasks`/diagram 條目、本 repo 任務殼無 diagram 產物——不加預防性條目，最小 churn）
- [ ] **S8 結算**：memory 池更新（`project_task-flow-restructure-00-tasks` 等引用 ai-rules 自家 00-tasks 路徑的條目——隨 S2 一起做）；`.kanban/` 不在範圍

## 驗收

- `fd '00-tasks' . -d 2` 零命中；`ls ai-analysis/` 含 `_tasks/`、`archive/`，不含 `execution-plans/`、`specs/`
- 新 session 跑 `/spec --write` 落 `ai-analysis/_tasks/<MM-DD-name>/spec.md`（探測解析正確）
- S6 sweep 白名單外零命中
- commit（user 確認；單一 commit 即可——變更原子性：結構＋引用＋README 同 commit）
