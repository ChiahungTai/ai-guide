---
id: AIR-96
title: AIR-91 殘項收尾批——effort parity gate／inherit 正式化／muse bundle 瘦身／pre-commit 環境隔離＋glm bridge 診斷
status: Done
assignee: []
created_date: '2026-09-15 15:10'
updated_date: '2026-09-15 18:35'
labels: []
dependencies: [AIR-91]
references:
  - ai-analysis/_tasks/_archived/09-15-model-capability-routing/ep.md
ordinal: 78000
---

## Final Summary

使用者行為：派工時 effort 詞彙三處不再靜默漂移（loader fail-loud）；CC 未點名 spawn 有正式 inherit 語義；muse bundle 89% WARN→81.6%；git hook 污染環境不再破壞 repo；glm bridge 四缺陷有 file:line 級修復規格。

五項全落地：①②＝f68e77b；③＝09e08ab＋deploy 3/3（hash 4f4577b1d197、機械驗證、AC 80% 偏差 1.6pp user 接受）；⑤＝b9eaab6；④＝診斷完成（截斷根因在 carrier 非 bridge、slot workspace-scoped 翻案、--wait-slot/--idle-timeout/A-1 規格齊）——Rust 實作歸 delegate-bridge 弧。插曲：1308 陣亡後產物由平行 session 收編 commit（dirty checkout 帶走良性實例）。

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

## Implementation Notes

- ①②落地＝commit f68e77b；⑤＝b9eaab6（1308 陣亡後由平行 session 收編，標示正確）。
- ③落地＝working tree（rules/bridge-dispatch 3,460→1,795B＋rules/tool-discipline 3,459→2,199B＋兩新 reference skill＋3 處引用同步）；bundle 33,013→30,088B＝81.6%（WARN 消失；AC 80% 差 1.6pp——建議接受，再刀邊際收益低）。待 commit＋deploy AUTH。
- ④診斷完成（spec-miner，唯讀 delegate-bridge repo）——兩個翻案：
  1. **截斷根因不在 bridge**：jsonl（raw stdout byte-faithful）內的 `response` 值本身就是缺頭的（詞中切點 "ills..."、句中頓號起頭、carrier 自標「（續）」）——head bytes 從未到達 pipe，**截斷發生在 carrier（zcode.cjs）內部的 response 聚合**。bridge 側管線（pump_raw 首byte起積/atomic write）機械排除。修復規格：A-1 偵測（usage.outputTokens vs response 長度比值→ledger infraStatus 標註非 fatal）＋A-3 ride-along（warning 前綴剝除 re-parse，衛星案 S-10 既定）＋A-2 上游插樁 repro。
  2. **slot 是 workspace-scoped 非機器級全域**：埠＝workspace root 的 SHA256 雜湊（ai-guide→28667、delegate-bridge→36392；實測 35566 屬其他 workspace）——先前「跨 session 機器級競爭」判定修正為「同 workspace 併發」。修復規格：--wait-slot bounded retry（預設 fail-fast 不變，凍結契約面）。
  - 楔死：前景無 idle watchdog；最小切入＝wait loop 複用 event_dirty（--idle-timeout flag-gated 預設 off）。D 項：pin 紀律文檔已完備且現場已收斂（2.0.5 已 prune）。
  - 完整診斷報告（file:line 級）：本 session 對話產出＋delegate-bridge 側修復規格表已備——Rust 實作歸 delegate-bridge 弧（跨 repo）。
