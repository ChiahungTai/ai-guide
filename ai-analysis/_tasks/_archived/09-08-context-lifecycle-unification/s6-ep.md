# S6 子 EP：觸發面對齊與 spine（S3/S4 驗證後展開）

> **ep_type**: implementation（docs/probe mode——文法對齊＋spine 實體＋跨池驗收；不動 registry 投影生成機制；驗收含 SM-1 跨池重跑）
> **parent**: ai-analysis/_tasks/09-08-context-lifecycle-unification/ep.md（master blueprint，S6 段＋Review 承接 17/20）
> baseline: 28734c5

## Context

S3/S4 通過後才展開（staging）；複用 S1 已驗證合約，不倒改前置依賴。依賴 S1–S5。

## 做什麼

1. skills catalog desc 文法對齊（S1 定案可執行部分；觸發詞任務語境化，不物理合併 harvest 機制）。
2. `agents/` registry roles description 納入文法對齊（僅文法，投影生成機制不動）。
3. spine 實體：候選載體（二選一定案：CC/ZCode 共用池兄弟目錄或 `~/.agents/memory-spine/`；plain md、同格式 frontmatter）＋生成掛點（各池 generator 認養 routing 行段，spine 條目由 ai-rules 側 session 寫入）＋各池/各 repo routing 行。
4. 跨 harness 投影確認：CC symlink 面驗原生可達性（不宣稱 bundle 投影）、muse read-only、codex auto-memory 不碰。

## 驗收

SM-1 跨池版（真實 catalog 載入面重跑，納入 P6 desc 縮短情境）＋spine 路由行在場。S1 單池結論不自動推廣為跨池結論。

## 產出

`s6-report.md`（對齊清單＋spine 位置決議＋跨池驗收）。
