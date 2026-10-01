# AIR-57 Review Ledger — codex 鏡像斷源重接

- **reviewed revision**: HEAD `95f4952`（EP baseline `4f8e1e6`）＋ uncommitted working tree（審查時點快照：本弧 M= crawl.py/test_crawl.py/README.md/model-routing SKILL.md/卡、D=55 鏡像舊檔、??=新鏡像頁；並行非本弧：draft-4、air-54 卡、memory-audit SKILL.md、air-69 卡〔審查中途出現〕、2026-09-10-repo-consistency-scan.md）
- **reviewers**: muse `job-mtup4z51-of2uta`（muse-spark-1.3/xhigh，read-only 紅線）＋ codex `job-mtup4z7n-yeh98s`（chatgpt-web/high，`--network restricted` read-only sandbox）；皆經 bridge task 工單（.agent-tmp/air57-review-order.md）
- **independent verification**: lite-verify 10/10 PASS（AC×4 逐項，含 AC3 三頁線上重 curl 三向全等）；主 session AC3 獨立複驗 MATCH×3

## Findings 與 Judge 裁決

| # | 來源 | finding | severity | judge | 處置 |
|---|------|---------|----------|-------|------|
| F1 | muse | 6 刪除檔證據包 1/6 缺 308 Location（redirect-map.json 該條 DNS error） | Important/drift | ✅ 採納（已閉合） | migration-verdict.json（verify_coverage.py 重試版）已含 Location＝learn.chatgpt.com/guides/build-ai-native-engineering-team.md；judge 再 fresh probe HTTP/2 308 確認——6/6 審計鏈完整。muse 讀到的是較早 scratch（redirect-map.json）。無 code 變更 |
| F2 | muse＋codex（同根） | canonicalize 後 dedup 收斂無 test pin：fixture 各頁單 variant，真實索引 developer-commands.md×4；URL query-free 亦無斷言（codex：regression 若 relpath 去 query 但 url 留 query，現行 test 假綠） | Suggestion(confirmed)/Minor(confirmed) | ✅ 採納 | fixture 加同路徑第二 variant（developer-commands.md?surface=ide）＋`assert all("?" not in p.url)`；期望清單不變（5 頁）——dedup/canonicalize 移除即 fail |
| F3 | muse | `.md#anchor` 形狀會被 regex 靜默丟棄（現行索引零命中） | Suggestion/evidence-based | ❌ 不採納 | YAGNI——零現行實例、推測性 robustness；記為已知限制（上游若改 anchor 形態，全集 loose-count 對帳可抓——本次 146↔148 差異正是該法抓到） |
| F4 | muse | README L37「# 全三站」pre-existing（base 已五源） | Suggestion(confirmed)/pre-existing | ✅ 採納 | 改「全五站」（順手修） |
| F5 | codex（聚焦建議） | regex 收任何 query 而決策寫 `?surface=`——建議查 llms.txt query key 集合 | residual note | ✅ 已查證閉合 | `rg -o '\.md\?[^) ]+'` llms.txt → 僅 `surface`（cli×2＋ide×3）；現行設計安全 |

## Followup 驗收（apply 後）

- `uv run pytest tests/test_crawl.py -v` → exit 0、6 passed（dedup pin 生效：同路徑雙 variant 收斂 5 頁＋query-free 斷言過）
- `uv run ruff check`（三檔）→ exit 0 All checks passed
- README `# 全五站` 落地（README.md:37）
- 全量 `uv run pytest` → exit 0、**289 passed**

## Reviewer 環境限制（如實記錄）

- codex：read-only sandbox 擋 `~/.cache/uv` 寫 → 3 個 uv 驗收命令 BLOCKED（exit 2，未進 test body）；改以純 read-only ledger/shell 等價查證（148 頁 sha 全量逐頁一致、manifest↔disk 雙向集合相等、6 刪除頁雙側 absent）補強，未冒充指定 gate
- muse：`UV_NO_CACHE=1 --no-cache` 繞 cache 寫完成 pytest（6 passed）；自曝曾誤寫 /tmp 一檔已即刪
- 工單 §1「git diff --name-only 空」字面不可滿足（開工樹已髒）——兩 reviewer 改舉證「審查者零新增寫入」；工單措辭教訓：dirty WT 的 read-only 工單應寫「無新增變更」而非「diff 為空」

## 收斂判定

followup 全 verified、無殘留 open findings → **收斂，可結案**。
