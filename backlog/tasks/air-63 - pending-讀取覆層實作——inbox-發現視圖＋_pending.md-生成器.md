---
id: AIR-63
title: pending 讀取覆層實作——inbox 發現視圖＋_pending.md 生成器
status: In Progress
assignee: []
created_date: '2026-09-09 09:59'
updated_date: '2026-09-15 15:49'
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
<!-- SECTION:NOTES:END -->
