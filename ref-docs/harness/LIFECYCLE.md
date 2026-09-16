# ref-docs/harness 鏡像生命週期

> 本檔定義官方文檔鏡像（`ref-docs/harness/`）的新增／更新／退役判準與操作流程。機制面（抓取方式／manifest 維護／refresh 命令）單一源＝[README.md](README.md) 與 `crawl.py`，本檔不重寫——只放「何時」與「流程序」。

## 新增（何時進新鏡像）

兩條件**皆過**才新增，任一不過＝不建鏡像（要查證時線上查）：

1. **消費面存在**：有進行中或已承諾的弧在消費該 harness 的官方契約（跨 harness adapter 設計、harness-neutral 規則撰寫、[contracts.md](contracts.md) 對照分析）——「以後可能有用」不算
2. **值得離線鏡像**：官方文檔有穩定可抓取端點（`llms.txt`／SSR nav），且離線查證需求真實（契約對照高頻、或站點結構變動會破壞既有引用）

操作序：`crawl.py` `SOURCES` 註冊 source → smoke（`--source <name> --limit 3`）→ 全量抓取 → README 來源表＋目錄結構補行 → `contracts.md` 補對照欄 → repo AGENTS.md 的 ref-docs 條目鏡像清單更新。

## 更新（既有鏡像）

- **時點**：消費弧開工前、或 runtime 行為與鏡像文檔疑似漂移時。refresh 是增量（sha256 不變不寫檔），隨時可跑、不付全量成本
- **操作**：`uv run python ref-docs/harness/crawl.py [--source <name>]`——不要手動逐頁鏡像（discovery／增量／manifest 都在 crawl.py 內）
- **contracts.md 同步義務**：refresh 揭露契約面變化（API 改名、行為反轉、機制增刪）→ 對照分析欄**當場同步**，防「鏡像新、對照舊」drift（contracts.md 的價值就在對照，單側更新＝半套）

## 退役（何時刪鏡像）

判準（任一成立即候選；刪除前 user 拍板——鏡像是 7MB 級資產，非 session 自行決斷）：

1. **harness 退出個人工具棧**：user 裁定停用（首例：opencode 停用，2026-09-16，AIR-102）
2. **零消費者**：活消費面掃描零命中（掃描式見下方驗證段——排除 backlog／ai-analysis／.agent-tmp 歷史面後 `rg -il "<name>"` 零命中）

### 退役流程（AIR-102 決策 7 首例——連動清單逐處確認，禁只刪目錄）

| # | 連動點 | 操作 |
|---|--------|------|
| 1 | 鏡像目錄 | `git rm -r ref-docs/harness/<name>/` |
| 2 | manifest.json | 刪該 source 全部條目（結構照現狀——per-source key 或平列） |
| 3 | crawl.py | 刪 `SOURCES` 註冊（含該 source 的 discover／fetch 函式與 import） |
| 4 | AGENTS.md | ref-docs 條目的鏡像清單除名 |
| 5 | contracts.md | 對照欄／對照表刪列（AIR-102 實例：原稱「四處連動」，對照欄是實作時補的第五處） |

README 來源表與目錄結構同步刪行。

### 殘留掃描驗證（機械執行——逐條跑，零命中＝完成證據）

```bash
# 活消費面掃描（歷史面除外——歸檔歷史不回改）
rg -il "<name>" --glob '!backlog/**' --glob '!ai-analysis/**' --glob '!.agent-tmp/**' --glob '!.git/**' --glob '!ref-docs/harness/**' .
# 五處連動點逐一複掃
rg -in "<name>" ref-docs/harness/manifest.json ref-docs/harness/crawl.py ref-docs/harness/README.md ref-docs/harness/contracts.md AGENTS.md
```

第一條命中活面檔案、或第二條任一連動點殘留＝清掃未完；命中 `backlog/`／`ai-analysis/` 歷史記錄不算殘留（退役當下的卡與報告是事實記錄，不回改）。
