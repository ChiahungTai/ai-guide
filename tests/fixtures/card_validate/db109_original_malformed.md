---
id: DB-109
title: dutymail read-only face output-shape discoverability — replies replyType surface + per-face schema docs
status: In Progress
assignee: []
created_date: '2026-10-11 14:00'
updated_date: '2026-10-11 14:00'
labels:
  - dutymail
  - standard-tier
dependencies: []
references:
  - Incident work-order envelope `ca058d9d-b181-4725-8aaf-0dd12fbdf93e` (ai-guide-marshal, 2026-10-11, AUTH recorded therein)
  - Reply envelope `db109-workorder-reply-001-1791688724` (accept 中間態; completed reply owed after landing)
  - Anchor: dutymail/crates/dutymail-core/src/query.rs:81 `canonical_envelope: Option<String>` (frozen envelope-v2 grammar — NOT a bug, out of scope)
---

## AC

1. （regression 樣本——本檔 frontmatter 為 delegate-bridge 開卡 commit a4446ea 的原文，
   第三條 reference 內未引用的 `canonical_envelope: Option<String>` 使 plain scalar
   破裂，pyyaml 報 "mapping values are not allowed here"；板解析器把卡靜默打進
   Unparsed。修復 commit＝0912d9b「quote reference strings」。本樣本是 card_validate
   層②（YAML strict）的原始 regression 依據，禁改 frontmatter。）
