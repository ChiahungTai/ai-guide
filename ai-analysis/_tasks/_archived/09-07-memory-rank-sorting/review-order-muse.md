# Work Order — AIR-39 EP 審查（read-only 深審，advisory）

## 1. 紅線
read-only：禁任何寫入（含 repo 外、memory 池、/tmp）；禁 git 寫入/卡狀態；交付＝最終回覆文字。

## 2. 目標
審查 AIR-39 EP（memory 索引 rank 排序——fail-soft 載入設計：generator 排序函數＋memory-audit 三處條文＋池部署同步）的設計合理性與引用 drift。

## 3. Baseline
repo `/Users/ctai/Github/ai-rules`（主 WT）；base `339e2c9`。

## 4. 必讀（scope manifest）
- core：`ai-analysis/_tasks/09-07-memory-rank-sorting/ep.md`（審查對象）；`skills/memory-audit/scripts/generate_index.py`（S1 改寫對象——排序現況/errs 慣例/frontmatter 解析結構與 EP 假設對照）；`tests/test_memory_lifecycle.py`（既有錨與 S1 test 計畫相容性）
- leaf：`skills/memory-audit/SKILL.md`（S2 三處條文落點：層 1 :35/寫入端紀律/夜波 bullet）；`skills/CLAUDE.md` :134
- exclusions：ref-docs/、backlog/、其他 ai-analysis/、memory 池（repo 外）

## 5. 已決策（勿重辯）
- rank 三值 hot/core/cold、default core 不懲罰存量；排序鍵進 frontmatter（「定期整理」＝整理排序鍵非手排 MEMORY.md——user 拍板）
- 排序軸＝type×rank×mtime 尾序（fail-soft：截斷損失導向冷門）
- gate/夜波/2.8 閘門不動（第四層縱深）
- 矛盾例外：EP 假設與 generator 實際結構衝突 → 停下舉證（file:line＋逐字引用）

## 6. 範圍限定
動＝零；不動＝全部。

## 7. 工具接線
cat/rg/ls（一律 rg）＋`uv run python -c` 可跑唯讀片段（如 sorted 模擬）；禁 code-reality 寫入面。

## 8. 驗收（查證命令＋預期）
1. `rg -n "sort" skills/memory-audit/scripts/generate_index.py` → 現況排序邏輯定位（EP 假設「type 分組×字母序」驗證）
2. `rg -n "metadata|frontmatter" skills/memory-audit/scripts/generate_index.py | head -10` → frontmatter 解析結構（EP「rank 欄位位置實作時定奪」的可行性）
3. `rg -n "ASSET_REL|parity" tests/test_memory_lifecycle.py` → 既有錨（EP S1 test 共存性）
4. `rg -n "mtime" skills/memory-audit/scripts/generate_index.py` → generator 是否已取 mtime（EP 假設「已掃檔案系統可取」）

## 9. 證據紀律
每 finding 附 file:line＋逐字引用；禁 PII；方法論限制段。

## 10. 交付（findings schema）
每 finding：錨點/嚴重度 H-M-L/信心/remedy 三分類（bug/drift/design-reversal）/一句修法。維度：EP 假設 vs generator 實際（引用 drift）／設計合理性（rank 語義可操作性、mtime 排序的副作用〔如 git checkout 後 mtime 全變——排序跳動？〕、SM 覆蓋）／漏改（rg 掃 rank/sort 相關引用面）／過度工程線。末行總評：可定稿／需修正後定稿。
