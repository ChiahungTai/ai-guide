---
id: AIR-39
title: memory 索引 rank 排序——fail-soft 載入設計（排序鍵進 frontmatter、截斷損失導向冷門尾端）
status: Done
assignee: []
created_date: '2026-09-07 05:34'
updated_date: '2026-09-07 05:46'
labels:
  - skills
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/_archived/09-07-memory-rank-sorting/ep.md
  - ai-analysis/_tasks/_archived/09-07-memory-rank-sorting/
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
索引載入截斷（200 行/25K chars 尾端不載）從 bug 轉設計：排序改 type 分組×rank×mtime 尾序——重要在前、冷門隨時間沉底，機制失靈時損失有序化〔baseline：ai-rules 9977496〕〔已決策勿重辯：①rank 進條目 frontmatter（hot|core|cold、default core 不懲罰存量）——MEMORY.md 仍是機械投影禁手寫，「定期整理」＝整理排序鍵非手排索引（user 09-07 拍板）；②排序軸＝type 分組（feedback→project→reference 維持）×組內 rank（hot→core→cold）×同 rank mtime 尾序；③截斷只降召回率不丟資料（條目檔仍在池、rg 可查）——排序把召回損失導向冷門條目＝fail-soft 第四層縱深（gate/夜波/2.8 閘門全不動）；④波段職責加 rank 通膨覆核（防寫入時自判全 hot）；⑤寫入時 rank 初判＝LLM 一句裁量，非機械〕〔驗收：①generator 排序函數 test（rank 分層＋mtime 尾序＋default core 相容＋invalid rank 處置）通過；②memory-audit skill 三處條文（寫入端 rank 初判／波段排序鍵覆核＋通膨檢查／「定期整理排序鍵」語義取代手排）；③ai-rules 池 generator 副本原子刷新後 regen 正常（既有 cmp/cp 機制）；④skills/CLAUDE.md memory-audit 索引行同步〕
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
memory 索引 rank 排序 fail-soft 落地：generator type×rank×mtime 尾序（TDD RED 先行、引號剝除/雙落點/永不 errs 三陷阱處置）＋memory-audit 三處條文＋池副本刷新部署（regen 順序變化實證）；dual-family 17 findings 全吸收
<!-- SECTION:FINAL_SUMMARY:END -->
