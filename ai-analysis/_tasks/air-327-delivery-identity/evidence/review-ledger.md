# AIR-327 review ledger

reviewed=7dbfd020fec402ca3c0eabb2c55a5752ae6e2057
baseline=7dbfd020fec402ca3c0eabb2c55a5752ae6e2057
uncommitted identity=05c33e2b1fbec7b97f3af6229141300443442a98d936b295eb160e9fc6a170f8 (final R1); untracked task report/EP/evidence are parent-authored, excluded source review, hashes recorded in post-build receipt.
scope=14 tracked files in writer frozen patch; UC1 frozen assignment identity, UC2 no-commit liveness, UC3 bounded blueprint refresh. Excludes archived records, report/EP authorship, unrelated mail proposals and qualification policy.
review_profile=boundary review-engine@ab95eecc481d
writer=Marshal post-build adjudication
legs：fresh job-mv6cb8sn-54qrlk trigger；intent job-mv6c2p98-n5olo0 trigger；flash job-mv6cb834-o4ypjp n/a；closure job-mv6d1vf5-88v2zg trigger；s2 job-mv6d1w44-1f26xe n/a

coverage=fresh correctness and intent/architecture/whole-changed-doc consistency inspected; runtime tests blocked in reviewer plan-mode, parent final full suite3929passed/1skipped + explicit before/after CLI reproduction supplements execution. R1 followup verified four findings; three S2 synthetic application scenarios reviewed, no production behavior claim.
landing delta=Sol annotation-only test helper dict→object; Marshal independently reversed exactly that line and matched R1 file SHA256. No body/assertion changes; target96passed, changed-four-file scoped mypy green with imported-module diagnostics silent; conftest three preexisting imported loader errors disclosed separately. Card and parent reports finalized as non-control metadata. No new behavior boundary. R1 identity above remains the reviewed baseline; final staged identity recorded in refreshed receipt.
fresh: cr(route=live-cr:MCP, evidence=.agent-tmp/air327-glm-fresh-result.md); actual callers events for join/assigned_manifest_digest/project_manifests verified by Marshal. Freshness rationale HEAD-only in report is insufficient; dispatch supply and writer final source freshness receipts provide the content-bound R0 evidence, not HEAD alone.
intent: cr(route=degraded, reason=freshness not verified within leg; report's claim of necessarily stale graph is unsupported, structural claims unverified-by-graph, evidence=.agent-tmp/air327-glm-review-result.md)
flash: cr: n/a（reason=literal oracle mapping/mechanical checks only, no structural query trigger; dispatch ref=.agent-tmp/air327-flash-final.md）
cr-closure：fresh checked
cr-closure：intent checked
cr-closure：flash checked
closure: cr(route=preprovided-cr, evidence=.agent-tmp/air327-glm-closure-result.md); R1 content-bound fresh receipt read, live helper callers corroborated. Parent checked actual tool event and source-frozen identity.
s2: cr: n/a（reason=synthetic instruction decision scenarios, no structural query; dispatch ref=.agent-tmp/air327-glm-s2.md）
cr-closure：closure checked
cr-closure：s2 checked

## code-review Findings

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|----|--------|------|------|------|--------|------|------|
| intent-F1 | Important | scripts/arc_handback_join.py:81 | 孤立 surrogate 經新 digest UTF8 encode 拋 UnicodeEncodeError，CLI exit1 偏離 exit2 | 已精確捕捉 identity encode error並診斷 | parent-r1-repro.log，真CLI exit2無traceback；followup.md | verified | ✅ 實測before/after，修正公開exit契約 |
| fresh-F1 | Suggestion | scripts/arc_handback_join.py:155 | 既存 verdict ac_id list/dict 未先驗型，setdefault TypeError | grouping 前驗非空字串並診斷 | parent-r1-repro.log list/dict各exit2；followup.md | verified | ✅ 既存同邊界缺口，定向回歸通過 |
| fresh-F2 | Suggestion | tests/test_arc_manifest.py:381 | 原TestCli測試被移入新S oracle class，provenance失真 | 恢復原class归屬，保留斷言 | TestCli::test_units_top_level_non_object_fails_clean通過；followup.md | verified | ✅ parent與reviewer核實class歸屬恢復 |
| fresh-F3 | Suggestion | scripts/arc_manifest.py:249 | NUL unit suffix 引發ValueError exit1；reviewer稱new edge但baseline亦同 | filename邊界驗NUL，明確exit2 | parent-r1-repro.log exit2且無output；baseline air327-f3-baseline.txt | verified | ✅ 修缺口；否決新回歸歸因：baseline亦ValueError embedded null byte |

## Adjudication notes

所有三個執行缺口已由 parent 真CLI重現。四項採納不以共識代替查證；對F3做baseline否證，確認不是新增regression。無錯誤PASS證據；不擴成認證／交易原子性需求。交原Sol writer修R1，reviewer沒有apply權限。

Native Sol fresh reviewer 01a13411-c06d-7b20-a749-c1c1731600a3 capacity失敗，零coverage；已由fresh GLM替補。Flash第一次plan-only job-mv6c3qoo-2905mg不接受；resume結果只接受static mapping，未把工具封鎖當PASS。兩GLM測試均permission blocked，parent的實跑另記而非回填reviewer。
