# work-order 憑證 schema（canonical 單一源）

marshal spawn 時發放至卡 WT 根 `.agent-tmp/work-order.json` 的在場憑證
（SC-199.1；本檔由 AIR-194 立為規格唯一源）。**任何消費端禁各自另立定義**——
變更本檔須同步全部消費端並跑對應測試。

## 消費端（引用指針）

- 驗證端：`hooks/marshal_admission_guard.py`（`WORK_ORDER_SCHEMA`／
  `WORK_ORDER_REQUIRED`／`load_work_order`——只驗在場性＋形，不做內容語義驗證）
- 發行端：對端 repo `scripts/issue-work-order.mjs`（或等值發行面）

## v1 schema

```json
{"schema":"work-order/1","worker":"…","card":"…","scope":"…","brief":"…","issuedBy":"…","issuedAt":"…"}
```

| 欄 | 型 | 語義 |
|---|---|---|
| schema | str | 恆 `"work-order/1"`（版本錨；不符＝憑證無效） |
| worker | 非空 str | 受派 worker 身分 |
| card | 非空 str | 卡 id |
| scope | 非空 str **或** 非空 list[str] | 寫入範圍宣告（兩形語義見下） |
| brief | 非空 str | 一句話任務摘要 |
| issuedBy | 非空 str | 發放者（marshal） |
| issuedAt | 非空 str | ISO8601 時戳 |

## scope 兩形語義

- **list[str]（正典）**：發行工具開出形——每元素一條範圍宣告，順序不具語義。
- **str（向下相容）**：手寫／舊憑證形——單一範圍宣告，語義等價單元素清單。
- 兩形皆須非空；list 形全元素須非空 str。其他形（空 str／空清單／含空或混型
  元素的清單／數字／dict）＝憑證無效。
- 驗證端不解析內容（glob 展開、與實際寫入座標比對皆不在 v1 面）——治理靠
  AIR-135.8 審計線。

## 驗證語義（消費端契約）

- 缺席／爛 JSON／非 dict／`schema` ≠ `work-order/1`／任一必填欄位缺、空或
  型不符 → 憑證無效（與缺席同罪，fail-closed deny）。
- 豁免面（寫入不觸發憑證要求）：`backlog/`、`.agent-tmp/`（含憑證檔自身——
  寫憑證不需憑證）、`docs/`；governance json 由 marker 檔恆豁免涵蓋。

## 最小手寫憑證範例

```json
{"schema":"work-order/1","worker":"implement-lite","card":"AIR-XXX","scope":"src/**","brief":"one-line task brief","issuedBy":"marshal","issuedAt":"2026-01-01T00:00:00Z"}
```

deny 訊息內嵌同款範例；改動範例形態前先確認 `load_work_order` 仍收（文案↔
schema drift 防護有測試把關：`tests/test_marshal_admission_guard.py`）。
