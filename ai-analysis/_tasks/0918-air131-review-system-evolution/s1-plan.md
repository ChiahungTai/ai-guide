# S1 Planning Contract——Heat 聚合進 corrections-weekly（AIR-131 blueprint child）

- **parent**：`ep.md`（AIR-131 blueprint）§2-1/§4-S1　**baseline**：main@f6cc00c1（card WT air-131）
- **變更檔**：`skills/corrections-weekly/SKILL.md`、`skills/state-review/SKILL.md`
- **AC 對應**：EP §6-①（行為 predicate：Warm 輸出帶 delete/merge/rewrite 候選要求、三 tripwire 可判、閾值與 §2-1 一致）＋A1（感測器盤點）＋A2（回測）

## 交付物

1. corrections-weekly 新增「Heat 聚合（AIR-131）」步驟＋月檔模板 Heat 行：
   - 聚合規則＝EP §2-1 表全文（window 8 弧／Cool 0-1／Warm ≥2 families 或同 family 連兩 window／Hot ≥3 或 tripwire／Cooldown）——**Warm 動作條文必含「禁 additive repair、必產 delete/merge/rewrite 候選」**
   - 感測器映射表（A1 實測結果入條文）：機械三支（corrections 七類＝mine_corrections.py／parity 殘留＝check_single_source.py／activation 健康＝installer --check/--verify）＋人工判讀四支（儀式成本三問季跑／usage 零消費 delta／Critical 逃逸率／gate 二次出現——A1 部分覆蓋條款：單面可產＝人工欄，不觸 kill）
   - 三 tripwire 各一行可判條件
2. state-review 步驟 5 加一行：gate 候選清單＝Heat 升溫觸發輸入（R family——recurrence 語義最貼近「同類第二次出現」）
3. A1 感測器盤點：三機械命令實跑證據＋四人工欄標註
4. A2 回測：既有 corrections 月檔套 §2-1 閾值——「常態 Hot」判定（≥2 週 Warm 以上）

## 不做

- 不動 corrections 七類分類本體／CR 段／memory 段（既有三職不變）
- 不建新排程/新腳本（第五件禁令——Heat 聚合是週報判讀面的新小節）
