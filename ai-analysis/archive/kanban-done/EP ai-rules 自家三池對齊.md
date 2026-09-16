[tag:common]

# EP ai-rules 自家三池對齊（full domain）

## 目標

ai-rules 自家分析側採 `ai-analysis/_tasks/` 任務家（與 mosaic 一致，user 2026-09-02 裁定 full domain）＋退役清債（execution-plans/specs 實體歸 archive）＋放置規則 README 單一源。

## 相關

- EP：`ai-analysis/_tasks/_archived/09-02-ai-rules-three-pool/ep.md`（simple 清單；✅ 2026-09-02 全段完成＋歸檔——S2 遷移隨 muse 增補代 commit `83a31b4` 解鎖 gate 後執行）
- 設計脈絡：mosaic 三池重構（S9 任務家探測已寫進 skills——本任務是 ai-rules 自家 dogfood）

## 驗收標準

- [ ] `fd '00-tasks' . -d 2` 零命中；`ai-analysis/` 含 `_tasks/`＋`archive/`、不含 `execution-plans/`＋`specs/`
- [ ] 新 session `/spec --write` 落 `_tasks/`（探測解析正確）
- [ ] 引用 sweep 白名單外零命中
