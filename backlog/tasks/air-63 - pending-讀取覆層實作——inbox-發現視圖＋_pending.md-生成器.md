---
id: AIR-63
title: pending 讀取覆層實作——inbox 發現視圖＋_pending.md 生成器
status: Done
assignee: []
created_date: '2026-09-09 09:59'
updated_date: '2026-09-16 03:05'
labels:
  - memory
  - governance
  - cross-harness
dependencies: []
references:
  - skills/memory-audit/SKILL.md
ordinal: 49000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
把 draft-5 設計稿實作出來：確定性 _pending.md 生成器＋MEMORY.md 固定 pointer＋異常偵測豁免＋refresh 觸發，讓 inbox 候選在 consolidation 前可發現（provisional，不提前信任）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 7 點 review 清單全過；canonical>pending 優先序有文字＋測試背書；ghost pending 零容忍；_pending.md 不進正式索引；AIDetector 豁免落地
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔詳細設計 09-09〕來源：draft-5（設計定案＋7 點 review 清單＋scope 邊界）。動工前三拍板：①觸發點（建議預設手動＋夜波 refresh 段，SessionStart 接線另議）②池 git 處置（建議池級 gitignore，provisional 不入歷史）③excerpt N 與單檔上限（建議 content 前 300 字＋單檔 4K 上限，超量只列條目不貼文）。段落：S1 生成器 skills/memory-audit/scripts/generate_pending.py（確定性：掃 inbox new/＋對池查 CAS state；輸出 _pending.md 原子發布；禁碰 MEMORY.md/_inventory.md；edit 標 Pending correction／add 標 candidate；base 失效標 conflict/stale）；S2 MEMORY.md 固定 pointer（改 generate_index.py render_b_form＋routing 行，只一行）；S3 豁免（T4-1 三 allow 訊號＋daily-maintain Phase0 加 _pending.md refresh 為合法自產物）；S4 觸發接線＋pool-gitignore；S5 測試（markings／優先序文字／ghost lifecycle：fake inbox→done 後 pending 消失／excerpt bound／多 edits 展示語義）。排序：AIR-54 合併進 main 後自 main 開 air-57（同 skill 檔，避免同檔併發）。驗收＝7 點清單＋T4-1 豁免實測（refresh 後 porcelain 不告警）。S6 mosaic 不受影響。

〔triage 併弧 09-10——升級為視圖雙件弧〕併入 AIR-64（handoff 網頁版改寫：web-brief 雙軌〔問架構/講實作〕＋可重現＋輕機密——原卡搬 completed/ 可查）。兩件檔案面不同可內部平行，一卡連續做收斂。draft-5 殼同步清除。

〔S1–S5 實作進度 09-15 lane63 worker〕**S1 ✅** `skills/memory-audit/scripts/generate_pending.py`（確定性生成器：掃 inbox root `*.json`〔WAL light〕＋`new/`＋`processing/*.json`，done/rejected 不掃＝ghost lifecycle 收斂；edit 類對 canonical 查 CAS——base 相等＝current、不等或 canonical 缺失＝STALE conflict、add 指既有 path 視同 conflict〔T3-6〕；原子發布 tmp+rename 只清 >60s aged 殘檔；禁碰 MEMORY.md/_inventory.md；`--repo-root/--pool/--inbox` 可注入；excerpt 前 300 字＋單檔 4K 上限超量降條目模式；候選損壞 fail loud 不發布、既有視圖保留；同 inbox+池狀態重跑同 bytes）。**S5 ✅** `tests/test_generate_pending.py` 21 tests（markings／優先序文字在場／ghost lifecycle done 後消失／excerpt 300 截斷＋4K 條目模式／同目標多筆依攔截順序展示／原子寫 aged 清理＋in-flight 不誤殺／零碰索引 sentinel 斷言／CAS current·STALE·deleted 三態／malformed fail loud／確定性／CLI exit 契約）——先 RED（FileNotFoundError）後 GREEN。**S3 ✅** `scripts/reconcile_memory_pool.py` 加 `ALLOWED_SELF_PRODUCED = ("_pending.md",)` 豁免（parse 後過濾；pool 整刪分支不適用）＋`tests/test_reconcile_memory_pool.py` +2 tests；daily-maintain SKILL Phase0 加雙池 refresh 一行；memory-audit SKILL「Inbox 消費」段加 Pending 讀取覆層指針＋T4-1 訊號③枚舉補 `_pending.md`。**閘門**：ruff check exit 0／ruff format exit 0／mypy exit 0（`uv run --with mypy mypy` 2 files no issues；repo 本身未配 mypy）／pytest 兩檔 54 passed、全量 534 passed。**L4 實跑**：tmp fixture 5 候選（同目標 edit current×2／edit STALE／add／processing）→ `_pending.md` 2,315 chars full 模式；reconciler 實測 refresh delta→clean exit 0、stray 繞閘→dirty exit 2 僅列 stray。**S2＋S4-pool ⏳ MARSHAL 待套用**：patch 落 `/.agent-tmp/air-63/s2-pointer.patch`（絕對路徑 `/Users/ctai/Github/ai-guide-lane63/.agent-tmp/air-63/s2-pointer.patch`；`.agent-tmp` 不入 git——須在本 lane WT 在場時套用或先複製）。三節：①資產源 `skills/memory-audit/scripts/generate_index.py`（與②同檔同步改，否則 Stop hook cmp 新鮮度檢查視池副本 stale 而停用 regen）②池 `_generate_index.py` render_b_form Routing 行後加一行 pending pointer③池 `.gitignore` 追加 `_pending.md` 一行（該檔主池已存在非新建）。已驗：`git apply --check` 通過、apply 後三檔與預期 bytes 全等、修補版 generator 於 scratch 池實跑 pointer 行在場。**套用步驟**（合併 air-63 後於 ai-guide 主 worktree repo 根）：`git apply .agent-tmp/air-63/s2-pointer.patch`（或 `patch -p1 <` 同檔）→ `cmp skills/memory-audit/scripts/generate_index.py .agents/memory/_generate_index.py`（必須一致）→ `git -C .agents/memory add _generate_index.py .gitignore && git -C .agents/memory commit -m "AIR-63 S2: MEMORY.md pending pointer 行＋gitignore 排除 _pending.md"` → `uv run python .agents/memory/_generate_index.py` → `git -C .agents/memory add MEMORY.md && git -C .agents/memory commit -m "AIR-63 S2: MEMORY.md regen（pending pointer）"` → `rg -n "Pending 候選" .agents/memory/MEMORY.md`（驗 pointer 行）→ `uv run python scripts/reconcile_memory_pool.py . --json`（應 clean exit 0）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
pending 讀取覆層全鏈落地：生成器 pending 視圖＋reconciler 豁免＋memory-audit 條文＋池 S2 commit（reflog 實證）＋夜波接線。UI-SC audit 雙腿共識 done-looking、marshal 抽查錨點全命中；卡面「待套用」為 stale 記錄（池側實已提交）。
<!-- SECTION:FINAL_SUMMARY:END -->
