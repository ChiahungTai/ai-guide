---
id: AIR-9005
title: 日期字串契約樣本——未引用日期不得自動轉型
status: To Do
assignee: []
created_date: 2026-10-11
updated_date: 2026-10-11 09:00
labels: []
dependencies: []
ordinal: 900500
---

## Description

created_date／updated_date 不帶引用——pyyaml 對 timestamp 形 scalar 預設轉型
datetime/date，validator 的 timestamp constructor 覆寫須把它收成原字串（層②
日期契約正向樣本：本檔必須 PASS，若轉型泄漏會在層④誤報「須為非空字串」）。
