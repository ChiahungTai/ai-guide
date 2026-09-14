---
id: AIR-93
title: muse 原生 session-end 記憶寫入繞閘——governance 覆蓋缺口修復（mosaic 證據鏈承接）
status: To Do
assignee: []
created_date: '2026-09-14 03:13'
labels: []
dependencies: []
ordinal: 79000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕mosaic 發現 muse 在 session 結束時會用「非 tool 呼叫」的原生路徑直接寫記憶池，繞過我們的 governance 閘（閘只能攔 tool 呼叫）。這張卡先確認機制，再把閘的覆蓋補起來或加上偵測網。

〔baseline：ai-rules main @ 807ace5〕證據源＝mosaic_alpha 池兩檔 mtime 2026-09-14 10:43:51（model-quota-status.md／model-routing-four-family-comparison.md，同秒批量寫入）晚於 governance tool deny 10:41:54、無 inbox receipt；mosaic 側 journal 有完整證據鏈（讀 mosaic_alpha .agent-tmp/ 或向 mosaic session 索引）

〔已決策勿重辯：①缺口成立——PreToolUse 閘只能攔 tool 呼叫，原生 session-end 寫入路徑不經 tool 層（mosaic 實證）②本卡歸 ai-rules（plugin 與治理設計所有權；mosaic 不改 ai-rules 已聲明）③修法候選待機制確認後裁：muse 設定關閉原生寫入（查 meta 鏡像 configuration.md）／sandbox .agents read-only 與 --yolo 的相剋（implement 委派一律 yolo 是 user 通則，動不得）／偵測網（池條目無對應 inbox receipt＝flag，併 memory-audit 機械層）④修復不得破壞 implement 委派 --yolo 通則〕

〔驗收：①機制確認落卡（muse 原生寫入的觸發條件與路徑，文檔或實測證據）②閘覆蓋修復落地或偵測網上線（擇一或並行，user 拍板）③重放驗證：模擬 session-end 寫入被攔/被偵測④文檔同步（README 運維節＋AGENTS.md Muse memory 段若受影響）〕
<!-- SECTION:DESCRIPTION:END -->
