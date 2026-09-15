---
id: AIR-96
title: AIR-91 殘項收尾批——effort parity gate／inherit 正式化／muse bundle 瘦身／pre-commit 環境隔離＋glm bridge 診斷
status: In Progress
assignee: []
created_date: '2026-09-15 15:10'
labels: []
dependencies: [AIR-91]
references: []
ordinal: 78000
---

## Description

AIR-91 結案後的五個殘項一次收（user 09-15「都做吧」）：

1. **effort-domain 機械 parity gate**：catalog.toml `effort_values`／model-routing SKILL effort 家族對譯表／`sync_agents.py _EFFORT_ORDINAL` 三處並存無機械對帳——加 loader 驗證或 doctrine gate，改任一處不同步即紅。
2. **inherit pseudo-binding 正式化**：CC 未點名 model 的 spawn（8/9 preset 實際路徑）目前只有一句 bypass 敘述——正式化為 carrier adapter 的第四形態（語義：identity／contract-preserving 攜帶／與 pending_binding sonnet 的關係）。
3. **muse bundle 瘦身**：部署 bundle 33,013B＝muse 36KiB gate 的 89%（WARN）——量測 per-rule 尺寸、依 reference-skill 分層既定模式（rule 留核心＋pointer、深層住 skills/<同名>/SKILL.md）瘦身最肥規則，目標 ≤80%。
4. **glm bridge 四操作缺陷（診斷腿）**：單 slot 機器級／頭截斷 ~30-40%／楔死／plugin 版本中途替換——handoff 已寫（`.agent-tmp/` 對話產出）；本卡做 delegate-bridge repo 唯讀診斷產修復規格，修復實作歸 delegate-bridge 側（跨 repo）。
5. **pre-commit hook 環境隔離**：`.githooks/pre-commit` 跑 pytest 時繼承 GIT_DIR 等環境變數污染臨時 git repo（`core.bare=true` 汙染今日二度發生）——hook 內機械清環境變數（codex 弧 wrapper 的永久化）。

## Acceptance Criteria
- [ ] #1 三處 effort 值域任一改動、餘兩處未同步 → 機械驗證紅燈（測試釘住）
- [ ] #2 SKILL carrier adapter 段有 inherit 正式語義；無第二處雙寫
- [ ] #3 部署後 muse bundle ≤ gate 80%；deploy 前 target diff 攤 user AUTH；fresh session 驗證
- [ ] #4 診斷報告落 delegate-bridge repo 或 handoff 附件，含修復規格（file:line 級）
- [ ] #5 hook 在污染環境（GIT_DIR 注入）下跑全套 tests 綠且不再改動主 repo config
