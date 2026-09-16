# Work Order — R1-R6 修復 followup review（read-only）

> followup-review variant：驗收實作方（主 session judge 修正輪）是否閉合 codex 整弧審查 findings。read-only、無預期改檔。

## 1. 紅線

read-only（禁 git/卡狀態/落檔）；禁輸出寫 repo 外；結論只在最終回覆承載。

## 2. 目標

驗證 R1-R6 六項修復閉合。原始 findings 逐字（含 codex 自述重現）＋judge 裁決與修復落點在本 repo EP：`ai-analysis/_tasks/_archived/09-07-memory-governance/read-observation/ep.md`「Codex 整弧審查 judge 裁決」段（先讀）。

## 3. Baseline identity

repo root `/Users/ctai/Github/ai-rules` 主 WT；working tree（未 commit 修正輪）；修復觸及：`skills/memory-audit/scripts/memory_telemetry.py`、`tests/test_memory_telemetry.py`、`skills/memory-audit/SKILL.md`、`skills/corrections-weekly/SKILL.md`、`ai-analysis/memory-telemetry/baselines/`（自 done/ 遷入）、EP 本身。

## 4. 必讀

1. EP 裁決段（上）——六項決策表＋修復對照
2. `git diff`（working tree）——修復本體
3. `skills/memory-audit/scripts/memory_telemetry.py`：SQL margin（read_zcode）、事件納入過濾（op 優先排他）、source protection resolve＋baseline 保護（main 開頭）、跨池同名 fail（main pools 段）、partial 消費 malformed/unreadable（project_reads）
4. 測例：`tests/test_memory_telemetry.py` 尾部 `test_r1*`/`test_r2*`/`test_r3_malformed_partial`/`test_r4*`
5. `skills/memory-audit/SKILL.md` 層 2 段「用途判讀帳」（R5）
6. `skills/corrections-weekly/SKILL.md` 步驟 2b 常態目錄（R6）

## 5. 已決策（勿重辯）

- R2 語義＝operation time 優先**且排他**（op 存在但窗外→排除，不 fallback record；無 op 才 record fallback）——codex 原文「只有缺失/無法解析時才 record fallback」
- R4 最小修＝跨池同名 fail-loud（不擴 per-pool schema）
- 矛盾例外：發現實作與本裁決矛盾→停下舉證

## 6. 範圍限定

動＝零；不動＝全部。

## 7. 工具接線

bash（rg/cat）/Read；唯讀驗證 pytest 可跑（fixture 在 tmp_path）。

## 8. 驗收（逐條實跑）

1. `uv run pytest tests/test_memory_telemetry.py tests/test_memory_read_observation.py -q` → 全 passed
2. R1 親測：構造小 SQLite db＋`--zcode-db <rel> --output <同檔 rel>` → exit 2 且檔案 bytes 不變；`--baseline-dir <池內>` → exit 2（fixture 放 /tmp 外的 repo 內暫存不被允許——用 python -c 在記憶體斷言或改用既有 test_r1 系列見證即可）
3. R2 讀碼：`rg -n 'operation time is authoritative|margin' skills/memory-audit/scripts/memory_telemetry.py` → 註解與邏輯在場
4. R3：`rg -n 'unreadable.*malformed|malformed.*partial' skills/memory-audit/scripts/memory_telemetry.py` → partial 消費在場
5. R4：跑 test_r4 → passed
6. R5：`rg -n '用途判讀帳' skills/memory-audit/SKILL.md` → 段在場且含三值＋第二表
7. R6：`rg -n 'memory-telemetry' skills/corrections-weekly/SKILL.md` → 常態路徑在場；`ls ai-analysis/memory-telemetry/baselines/` → baseline 檔在場
8. R6 承接：重跑 writes（輸出到 .agent-tmp/，baseline-dir 用常態目錄）→ report.index_delta.value 非 null

## 9. 證據紀律＋PII 禁令

每條附命令＋原始輸出；PII 禁。

## 10. 交付報告格式

1. 逐項 verdict：R1-R6 各 closed / not-closed（附證據）
2. 新發現（file:line＋嚴重度＋信心＋remedy）
3. 總結論：followup 通過／不通過
