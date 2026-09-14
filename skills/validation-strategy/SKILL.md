---
name: validation-strategy
description: "build/commit 驗證段決定測試類型與方式時載入——驗證策略紀律：e2e 優先於單元隔離、交易相關 replay >>> live、驗證放 scripts/、不重驗 package 已驗證的部分、整合器型變更判定（三條件＋mock 循環論證＋兩層整合測試：接線 guard＋真實邊界）、消費端驗證模式（完整流程＋測試集機械反查）、crash-only 邊界（設計方法與誤用）。觸發詞：e2e、replay、驗證策略、測試類型、live、不重驗 package、驗證放哪、交易驗證、回放、整合器型、真實邊界、整合測試、mock、消費端、機械反查。"
when_to_use: "Fires during build/commit 驗證段 when choosing test types（e2e vs unit isolation、replay vs live、驗證放 scripts/）, 判定整合器型變更, or planning 消費端驗證. Load BEFORE writing an EP 驗證策略 section."
---

# Validation Strategy — 驗證策略紀律

實戰驗證紀律：測**什麼類型**（e2e vs 單元）、**怎麼測**（replay vs live）、**放哪**（scripts/）、**不測什麼**（package 已驗證的）。與 [acceptance-evidence](../../rules/acceptance-evidence.md) L3-L5（證據階層）互補 — 本 skill 是「選擇紀律」，證據階層是「強度分級」。

## 四紀律

### ① e2e 優先 > 單元隔離

功能是給消費端用的，單元測試通過 ≠ 功能可用。**優先 e2e 驅動真實消費端流程**，單元補邊界邏輯。

判準：
- 涉及消費端完整流程（pipeline、API、CLI）→ e2e
- 純函數邏輯（計算、轉換）→ 單元
- 不確定 → e2e（寧可多整合）

### ② 交易相關 replay >>> live

交易驗證用 **replay（回放）** 優先，遠優於 live（連線）。

- replay：可重現、可控、不消耗資源、不影響真實帳戶
- live：不可控、消耗資源、風險（真實下單）

判準：
- 訊號 / 策略 / 回測邏輯 → replay
- 連線 / 下單基建 → live（但最小化，僅驗連通）

### ③ 驗證放 scripts/

驗證方法（demo、replay 腳本、對照工具）放 `scripts/`，不放 `tests/`（測試是 CI 自動化，scripts 是人為 / 半自動驗證）。

### ④ 不重驗 package 已驗證的部分

主要 package（NT、bokeh、panel）自己有測試，**別重測其內部**。只驗**你的整合**（public API 行為、你的呼叫方式），非 package 內部實作。

判準：
- 驗「NT 的 submit_order 在你的 context 怎麼行為」（你的整合）→ 驗
- 驗「NT submit_order 內部是否正確」（package 內部）→ 不驗（package 自己驗）

## crash-only 邊界（自 quality-constraints rule 承接）

- **設計方法**：狀態外部化（DB/隊列），操作等冪、服務無狀態；停止即崩潰、恢復即初始化。持久化輸出/備份禁 `tempfile.TemporaryDirectory`（scope 結束即毀），須放專案外持久路徑。
- **誤用警告**：crash-only 只保證意外失敗後可恢復，不豁免可預期的整合 bug、配置或合約錯誤。真實案例：ReplayHost SIGTERM 失敗曾被以 crash-only 跳過 graceful 處置；正解是 TDD red（xfail strict）釘 graceful 目標再修。

rule 端留核心句＋適用範圍＋pointer（[quality-constraints](../../rules/quality-constraints.md)）。

## 整合器型變更判定（真實邊界整合測試）

整合器型變更的完成定義必須含**真實邊界整合測試**（L3+，證據階層見 [acceptance-evidence](../../rules/acceptance-evidence.md)），不能只靠 mock。EP 段落同時滿足以下 → 整合器型：

- 主要價值是把 ≥2 個真實外部組件接起來（DB、catalog、第三方 SDK、跨進程、跨框架）
- 邊界正確性無法從任一單方文件推導（必須實際接起來跑）
- 錯了不是「調參數」而是「整天行為全錯」（時區偏移整天、序列化整批毀損）

**排程時刻變更＝整合器觸發情境**（實證：BSR 連敗根因＝`today−1` 凌晨語義——排程跑在「今天」但資料是「昨天」）：改排程時刻的盤點必走**兩層**——①引用層（rg 掃得到）②**隱含時間假設層**（`today±N`、時段條件、跨日邊界——rg 掃不到，逐檔人工判）。時間語義測試釘法：helper 收 `now: datetime` 參數＋mock 多時刻 case（排程時刻前後／凌晨／白天／跨日邊界／假日鏈），非只測「當下」。

**mock 循環論證陷阱**：當 EP 主要價值是「把外部組件接對」，mock 測試的假設本身可能是 bug 來源 — mock 驗證「假設成立的話行為正確」，無法驗證「假設本身是否成立」。例：catalog 存 naive Taiwan-local 時間，`tz_localize("UTC")` 只貼標不轉換，mock 假設「catalog 回傳正確 UTC」就是 bug 來源，mock unit test 結構上抓不到 +8h 時區偏移。

**兩層整合測試**（缺任一即缺口）：

| 測試類型 | 性質 | 目錄 | marker |
|--|--|--|--|
| 接線 guard | 純邏輯、無 IO（registry lookup、membership 斷言） | `tests/unit_tests/` | `quick` |
| 真實邊界 | 真實 DB / Catalog / 資料，跑完整消費端 pipeline | `tests/integration_tests/` | `integration` |

**不可互代**：接線 guard 廉價擋高頻接線 regression；真實邊界昂貴擋跨層 schema / 展開失敗。命名含 `_integration` 但純邏輯仍留 unit_tests（依依賴判斷，不看名稱）。

## 接線覆蓋與漸進驗證

symbol 出現在測試不代表新參數、接線或組合真的被驅動：新 public 參數/注入點必測既有符號＋新參數組合；全是 `guard=None` 不涵蓋 guard 注入，可用 `rg "<param>=" tests/` 查接線。registry 新成員須斷言 auto-discovery membership（如 `list_*_classes()`）；per-class 測試不證明已註冊。整合器型變更仍須同時有接線 guard＋真實邊界測試。

驗證採 DEPTH-MIN→SAMPLE→FULL：每次修改先以 3–5 個多分支案例做 MIN，至少含一個已知易錯案例；穩定後 SAMPLE，再到風險要求的 FULL。任何階段失敗都先分析/修正並回 MIN，禁修改後直接 FULL 或 FULL 失敗後盲重跑。風險分級決定最終深度，漸進順序決定如何抵達。

## 消費端驗證模式（消費端上下文驗）

先定位主要消費者並跑完整流程：scoring/ranking 用 watchlist 真資料；除權息用真股票日/週/月 K；DB 改動跑 fetch→transform→write→read。共用模組驗整個影響面。

**測試集須機械反查，不憑目錄直覺**：查「哪些測試覆蓋某符號」用 code-reality `impact_radius`／`scip_refs --callers`，或 `rg "<符號>" tests/ -l`——禁憑目錄位置推斷測試歸屬。

## 與 test-driven-development 邊界

- [test-driven-development](../test-driven-development/SKILL.md)：RED/GREEN **流程** + Test Classification（單元 / 整合 / 外部 API 分類）。
- 本 skill：測試類型**選擇紀律**（e2e vs 單元、replay vs live）。

**分工**：TDD 是「怎麼寫測試」（流程）；本 skill 是「測什麼類型 / 方式」（選擇）。層次不同，非重造 Test Classification。

## 與既有邊界

- [acceptance-evidence](../../rules/acceptance-evidence.md) L3-L5：證據**強度**階層（整合 / 可執行 / 對抗）。本 skill 是**選擇**紀律（引用階層，非重述）。
- [quality-constraints](../../rules/quality-constraints.md) 消費端驗證：rule 留 invariant（先定位主要消費者＋測試集機械反查），細則與工具命令在本 skill「整合器型變更判定」「接線覆蓋與漸進驗證」「消費端驗證模式」段。

## 不適用

- TDD 流程（RED/GREEN）→ `test-driven-development`
- 測試反模式稽核 → `/audit-test`
- 證據強度分級 → `acceptance-evidence`
