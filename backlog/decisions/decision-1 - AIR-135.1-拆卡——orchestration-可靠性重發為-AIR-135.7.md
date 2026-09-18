---
id: decision-1
title: AIR-135.1 拆卡——orchestration 可靠性重發為 AIR-135.7
date: '2026-09-18 13:28'
status: accepted
---
## Context

AIR-135 跨家族審查（muse job-mu6yvfsr-qb10ze）F5：AIR-135.1 單卡 11 條 AC，其中 main-seat／artifact-first／collection／bounded-slices 任一皆 EP 量級，合併單卡導致驗收全有全無。judge 裁 ⚠️ 留 user；user 0918 晚拍板「拆卡，重編號沒關係，以免搞混」。

## Decision

AIR-135.1 保留 compiler 本體（ArcSpec/ArcPlan/DispatchSlice、Marshal automation、dogfood、recovery、authority/identity，6 條 AC）；orchestration 可靠性五條（main-seat、artifact-first delivery、collection contract、bounded slices/checkpoint、context 對接）連同相關 notes 重發為新子卡 AIR-135.7（parent_task_id=AIR-135）。135.1 deps 改指 135.7；parent AC#7／S3、135.6 介面 ownership 連動改指。

## Consequences

- 單卡 AC 全有全無驗收問題消除；執行序 DAG：135.6 → 135.7 → 135.1。
- 既有的 135.1～135.6 id 零 churn（新編號避免重編混淆——user 裁決原話）。
- 落地 commit：主線 d8a6b0f2 前的 90e51931（branch air-135 已 ff-merge 進 main）。
