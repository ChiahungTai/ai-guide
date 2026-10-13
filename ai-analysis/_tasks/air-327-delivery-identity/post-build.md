# AIR-327 post-build 收尾

本報告保留 post-build 收斂時的合併前快照：source 在 air-327 隔離 worktree，HEAD 7dbfd020fec402ca3c0eabb2c55a5752ae6e2057；R1 tracked diff SHA256 `05c33e2b1fbec7b97f3af6229141300443442a98d936b295eb160e9fc6a170f8`。後续提交與 main 整合結果以卡 notes 的 landing 回執為準。

## 改動與裁決

交付回執升為 schema /2，綁定凍結 assigned manifest 與派工時記錄的 expected digest；只比 card/unit/AC 的舊規格回執不再接受。producer 拒絕覆寫不同分派內容，保留相同內容 retry。身份／結構過關仍不代表語義完成。

移除 worker 必須 commit 證活的矛盾，觀測不增權；保持原有 terminal、hard-death 與 retry-safe 邊界。同步既有 blueprint/source projection 與 governance 導航，不新增投影引擎或排程。

GLM fresh 與 intent 各獨立 context，Marshal 實測後採納四 finding：Unicode surrogate、非字串 verdict AC、NUL 檔名的 typed error 診斷，以及舊測試 class 歸屬。NUL 原本亦存在，已用 baseline 實測否決「新增回歸」歸因。Sol 單一 writer 修正，GLM 定向 followup 四項 verified；沒有遺留 source blocker。

## 證據

| 驗證面 | 結果與來源 |
|---|---|
| 初輪 TDD | baseline48 passed；新oracle44 failed→92 passed；expected-only mutation由綠翻紅再還原 |
| 修正 TDD | malformed regressions4 failed→target96 passed，Arc390 passed |
| Parent 修後全 repo | **3929 passed，1 skipped，161.00s**；[完整輸出](evidence/full-suite.log) |
| 真 CLI | 原三種缺口exit1；修後surrogate/list-ac/dict-ac/NUL四案皆exit2、無traceback，parent重跑確認 |
| 品質 | ruff/format、兩executable語法import/type diagnostics通過；diff-check通過 |
| 文件 | intent reviewer讀完整5份變更MD；single-source15項零critical/important；blueprint5來源hash一致 |
| S2 | [三情境應用審查](evidence/s2-scenarios.md)；synthetic LLM判讀，非production behavior或B軸驗收 |
| CR | 最終content-bound fresh/current-tree，identity96e82748…；followup讀receipt並實際查helper callers |

原native Sol reviewer容量失敗，沒有計入coverage；以GLM-5.3 fresh替補。Flash提供oracle1–11靜態對照，但plan-mode拒絕執行；兩GLM初審也不能跑測試，機械實跑由parent承載。並未把blocked或transport completed當PASS。Intent reviewer撤回其「graph必然stale」推論，原腿只記freshness未驗證；R1以content-bound證據結算。

原始報告：[writer](evidence/writer.md)、[fresh](evidence/fresh-review.md)、[intent](evidence/intent-review.md)、[followup](evidence/followup.md)、[Flash](evidence/flash-static.md)、[parent重現](evidence/adjudication-repro.json)。舊報告中的暫定結論以本裁決與followup為準。

## 收尾邊界

提交前 delta：Sol 將測試 helper 的 `**overrides: dict` 修成 `object`；Marshal 逆換該單行後 hash 與 R1 完全一致，確認沒有改 body／assertions。定向96 tests通過。四個變更Python檔的mypy（`MYPYPATH=tests`、`--explicit-package-bases --follow-imports=silent`）通過；未抑制變更檔錯誤。未加 silent 的傳遞檢查另報未變動 `tests/conftest.py:14-15` 三個既有loader optional錯誤，明列為範圍外型別債，不宣稱全repo mypy全綠。詳[evidence/type-finalization.md](evidence/type-finalization.md)。本次source語義仍由R1審查覆蓋，annotation delta由不同於writer的Marshal核對；提交hook將再跑全repo測試。

classification=boundary；review=fresh＋intent＋R1 closure＋S2 application；session-freshness=本弧未改canonical，依凍結WT現文審查；deployment-surfaces=healthy（觸及skills母鏈指向canonical且存活），**新source啟用仍待合併**。rules bundle、plugin、CR binary均未觸及，不執行部署。

無新增可執行入口／頂層模組，scripts/AGENTS已接owner；無rename。Tour corpus無.tour，條件空跳；無callstack-plan庫存面。delta tour未產：uncommitted模式，EP人工對照S1–S3＋定向malformed修補均已解釋。HTML只內容刷新，未宣稱視覺驗收。

Improvement早期掃描僅cross-arc recurrence101為計數訊號，無具體同根失敗證據，不據此另造卡。模型容量與plan-mode權限限制已記實證，留給後續歷史dry-run判讀。記憶池未寫入；本弧scratch／POC與review證據保留至commit及證據承接，不清他弧資料。

此快照當時止步於post-build的commit前邊界；使用者後續明示「就merge main啊」，已授權提交與 main 整合。Flash＋Terra歷史dry-run已另行結算，監控架構提案亦獨立於本source acceptance；不因合併本卡而視為新設計已實作。
