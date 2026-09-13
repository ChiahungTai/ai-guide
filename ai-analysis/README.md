# ai-analysis — 分析側工作區（ai-rules 自家）

> 本 repo 亦消費自家 skills（部署迴圈）——任務放置規則以 skills「任務家探測」單一源（`skills/_common/illustrate-html-mode.md`「產物位置分流」）為準；本檔是 ai-rules **自家目錄**的放置說明。2026-09-02 三池對齊起，探測在本 repo 解析到 `_tasks/`（此前任務住 repo-root `00-tasks/`——已遷）。

## 目錄

| 目錄 | 角色 |
|------|------|
| `_tasks/` | **任務家**（`<MM-DD-name>/`＝ep.md＋spec.md＋Report Shell 殼；完成→同家 `done/`） |
| `flow-feedback/` | 回饋 inbox（user 反饋待處理條目；處理完搬 `_done/`——既有慣例不變，有 skill 接線） |
| `reports/` | 一次性分析報告（日期前綴；歷史記錄不改寫） |
| `prompts/` | prompt 範本資產 |
| `tours/` | tour 相關產物 |
| `archive/` | **唯一歸檔根**（原 `execution-plans/`、`specs/` 兩退役慣例 2026-09-02 歸檔於此；歷史去 git log/歸檔區查） |

## 產物→家

| 產物 | 家 |
|------|-----|
| 新任務（EP/spec/殼） | `ai-analysis/_tasks/<MM-DD-name>/`（`/spec --write`、`/execution-plan` 自動落此——探測已接線） |
| user 反饋 | `flow-feedback/`（skill 接線） |
| 服務目錄產物歸檔 | `archive/` |

## 三池與承諾紀律

* **承諾池** `backlog/tasks` 為唯一承諾入口（`backlog task create`）；`_tasks/` 為承諾的**執行家**，**不另建獨立承諾**，依賴 `backlog → 執行家` 單向。
* **去重前置**（中）：`backlog task create` 前必 `backlog search <關鍵詞>` + 查 `backlog/drafts/`（未承諾草稿歸宿）與同域 open-items（例：mosaic 側 `marking/open-items.md`）待處理段，命中則復用/連結既有指針，避免一行指針與卡重複承諾。放置單一源見 `skills/_common/illustrate-html-mode.md`「產物位置分流」。
