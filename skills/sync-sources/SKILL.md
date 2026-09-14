---
name: sync-sources

description: "Single-source invariant 檢查 — 機械驗證 ai-guide 的『唯一/單一源』宣稱沒被 drift。/sync-sources"
when_to_use: "After editing ai-guide rules/skills/commands, before /commit, or when auditing single-source health. Mechanically checks declared single-source invariants (severity/confidence enums, audience classification, allow-list coverage, source-contains, and deployed-bundle freshness — the three non-Claude AGENTS.md deployments must byte-match a rebuild from current rules/ + guide). Catches the 'definition exists but schema dropped it' drift that AI-discipline-only maintenance misses."
argument-hint: ""
allowed-tools: Bash(uv run python *)
---

# /sync-sources — Single-Source Invariant 檢查

機械驗證 ai-guide 的 single-source 宣稱沒被 drift。這是 review-engine 重構當初**少開的那張處方**——設計者（transcript L135）預見了 drift、寫下了警告，但防護只做到「邊界表 + 手動 rg」，沒做到「schema 同步閘門」。本命令補上那道閘門。

> **受眾：LLM 執行鏈命令**。產出機器 findings（嚴重度 + 檔案:行），供 AI 或人決策修哪。不是人類 viewport（不渲染心智模型）；不取代逐項審查（那是 `/code-review`）。

## 執行

```bash
uv run python skills/scan-project/scripts/check_single_source.py
```

（從 ai-guide repo root 執行）

## 它檢查什麼

讀 `check_single_source.py` 頂部 REGISTRY（每個 single-source 宣稱一筆），對全 repo 機械驗證：

| 檢查 | 抓什麼 | 為什麼是機械的 |
|------|--------|---------------|
| **enforced_by 同步** | 定義在 source、強制 schema 在另一檔 → schema 必須真的含該欄位 | 抓「定義源/schema 源分離 drift」（如信心水準被 DimensionVerdict 丟棄）——這是純文字比對，無語義判斷 |
| **classification 自標** | CLAUDE.md 分類的命令本體必須含受眾字樣 | 抓「外部分類、命令不自知」——純字串包含檢查 |
| **coverage（allow-list 覆蓋）** | source_glob 下每個定義（如 skill name）必須被 enforced_by 提取的集合覆蓋 | 抓「定義源目錄 ↔ 執行源 allow-list」drift（rename 後未同步）——純集合比對 |
| **source_contains** | 定義源自身必須含關鍵值 | 防 drift 回非預期值——純字串包含檢查 |
| **部署 bundle 新鮮度** | 非 Claude 三端部署 AGENTS.md 必須 == source 重建 bundle | 抓「編輯 rules/ 後沒跑 deploy」（stale 部署 = 非 Claude session 讀舊規則）——rebuild + byte 比對，無語義判斷 |

## Finding 嚴重度

- **critical**：定義存在但 schema 丟棄（執行層缺陷，不只文檔——會在實際審查中產生錯誤行為）
- **important**：分類命令未自標受眾、schema 區段找不到（文檔層，但不修會持續 drift）

## 新增 single-source 宣稱

在 `check_single_source.py` 頂部 **REGISTRY** 加一筆（含 `source` + `enforced_by` 或 `commands`）。**登記 = 宣告單一源本來該付的成本**——之前用散文宣稱是欠了這成本沒付，drift 才會發生。

## 與其他命令

| 命令 | 關係 |
|------|------|
| `/code-review` | 發現 drift（深層思考）；`/sync-sources` 機械防復發 |
| `/consistency` | 單一文檔自洽；`/sync-sources` 跨檔 single-source invariant |
| `/commit` | 未來可在此跑 `/sync-sources` 當 commit gate（目前手動） |

## 範圍

機械檢查五類：**enum（enforced_by 同步）/ classification / coverage / source_contains / deploy_freshness**（可靠、零誤判）。以下為設計層 drift，靠 `/code-review` + 手動修，未機械化（未來可擴充）：
- 「唯一/單一源」強字眼過度承諾（如「唯一判定規則」卻有 carve-out）
- canonical flow 多處重畫
- 持久化 optional/預設語義漂移
