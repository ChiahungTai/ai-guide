---
id: AIR-TEST-MIXED
title: 合成混類卡——compiler 分類測試用
status: In Progress
---

## Description

合成 fixture（AIR-135.1.1 測試用；非真實卡）——涵蓋四類：已勾無 verifier／
verifier open／prose judgment_required／已勾帶 verifier。

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 已完成的前段——重編譯不丟已完成證據
- [ ] #2 套件綠 `uv run pytest tests/test_demo.py -q` → exit 0
- [ ] #3 人類裁決面——純 prose 描述無 explicit verifier，須落 judgment_required
- [x] #4 已勾且帶 verifier `rg "foo" bar.py` → 3 hits
<!-- AC:END -->

## Implementation Plan

（略）
