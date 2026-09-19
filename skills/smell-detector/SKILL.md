---
name: smell-detector
description: "壞味道偵測 / code smell / 架構審查 / 重構前研究 / 測試優化盤點 / 質疑 code 存在價值 / 懷疑 AI 亂加 code 或測試 / baseline 盤點 / codebase 穩固度 / 架構 onboarding——兩 mode：`<dir|files>` zoom 變焦批判（6 判準+查證誠信）、`--baseline <dir>` 廣角盤點（4 檔+invariants+drift 追蹤）。read-only 偵測器，修復走 /implement、/fix-test。"
when_to_use: "Code smells, architecture review, pre-refactor research, test-suite cost/structure inventory, or questioning whether existing code/tests deserve to exist. Zoom <dir|files> for targeted critique (typical trigger: suspect AI added junk code/tests, no suspicion required); --baseline <dir> for per-directory baseline or onboarding. NOT for: change-diff review (/code-review), test-content anti-patterns (/audit-test), post-change comprehension (/debrief)."
argument-hint: "<dir|files>（zoom 預設） | --baseline <dir> | --status | --stale [dir] | --architecture (--arch) | --invariants"
allowed-tools: ["Read", "Edit", "Write", "Bash", "Agent", "LSP", "WebFetch", "mcp__code-reality__*"]
---

# /smell-detector — 壞味道偵測：架構審查＋重構前期研究＋測試優化盤點

> **定位**：行動前的人類 viewport——重構/refactor EP 之前的研究入口，或對既有 code 的批判檢視。與 `/debrief`（行動後聽取報告）對仗。
>
> **smell 語義**：壞味道 = **表面訊號，指向但不指控**——偵測器只說「這裡聞起來怪」，判讀是人（no-severity，與 illustrate drift overlay 同構）。code smell / architecture smell / test smell 三個術語世界對應本 skill 三塊 scope。
>
> **重構前期第一問：最好的重構是刪除**——zoom 的存在質疑（YAGNI/phantom API/測試價值）就是 pre-refactor research 的第一段。
>
> **CR 接線（唯一，cr-audit R8）**：YAGNI/dead-code verdict（「可刪/沒人用」型結論）須走三步——CR `callers` 歸零 → CLI `hub_refs <sym> --repo <root>` hazard 分層（含 test/prod 切分、dynamic dispatch 防護）→ `rg` 字串引用 complement（工具語義見 [cr-query](../cr-query/SKILL.md)）；negative verdict 永遠不可單憑 rg 宣稱。其他 smell 軸（命名/結構/測試價值）不接 CR。
>
> **read-only 偵測器**：只產 advisory 報告，不審又修——修復走 `/implement`、`/fix-test`。

## 兩 mode 分工

| mode | 觸發 | 意圖 | 完整規格 |
|------|------|------|---------|
| **zoom**（預設） | `/smell-detector <dir\|files>` | 變焦批判：這些 code/test 該存在嗎、命名設計對嗎、測試有價值嗎 | [zoom.md](zoom.md) |
| **baseline**（廣角） | `/smell-detector --baseline <dir>` | 廣角盤點：per-directory 穩固度 baseline（4 檔+invariants+sha drift 追蹤）；`--status` / `--stale` / `--architecture` / `--invariants` 續掛此 mode | [baseline.md](baseline.md) |

**選擇**：針對性懷疑（典型：懷疑 AI 亂加）→ zoom；onboarding / 週期盤點 / 首次全面審 → baseline。重機制（4 檔+狀態）是顯式 opt-in——誤觸 4 檔重機制的代價遠高於誤觸 console 報告。

報告輸出遵循[結論先行原則](../_common/conclusion-first.md)——先結論後 id／代碼。

## 測試 smell 三類（兩 mode 共用段；grounded 於真實案例）

> 邊界：`/audit-test` 管測試**內容**正確性反模式（同義反覆/mock/幽靈斷言）；本 skill 管測試**套件地形**的成本與結構。正交。

| smell 類 | 訊號 | 偵測方法 |
|----------|------|---------|
| **資源 smell** | 每目錄峰值 RSS / 執行時長超標 | **優先讀既有量測資料**（nightly per-batch `/usr/bin/time -l` RSS 落檔之類的 ops log）；無量測資料時標「無量測資料」不用猜 |
| **怪獸測試 smell** | 輸入規模 >> 測試意圖（全量資料測小行為） | 讀 fixture/conftest 的資料窗設定 vs 測試斷言的意圖 |
| **結構 smell** | 分批完整性 / silent skip / junit 合併破損 | 收集數 vs 合併數對帳；skip 標記盤點 |

> **真實案例**（2026-08-15 nightly 記憶體事件）：測試全綠但 nightly 單進程 pytest 結構性吃到 7-16GB（session-scoped fixture 累積）——三類 smell 在同一事件全部現形：資源（16GB 峰值）、怪獸測試（37 年全史測 5 年窗即可的行為，`data_window` 收窗後 10-16× 瘦身）、結構（分批後需 collect-only 覆蓋 guard 防「新目錄靜默漏跑」）。教訓不依賴特定符號現狀。

## 與其他命令協作

| 想問的問題 | 命令 |
|-----------|------|
| 哪裡有壞味道（行動前/審既有） | `/smell-detector` |
| AI 改了啥、證據在哪（行動後） | `/debrief` |
| 結構長怎樣 | `/illustrate` |
| 變更 diff 正確性（機器 finding） | `/code-review` |
| 測試內容反模式 | `/audit-test` |
| 修正驗收 | `/followup-review` |

## 語音通知

遵循 [voice-notification](../voice-notification/SKILL.md)：開始 touch sentinel + say「開始壞味道偵測」；完成清 sentinel + say 完成樣板。
