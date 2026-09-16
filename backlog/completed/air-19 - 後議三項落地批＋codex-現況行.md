---
id: AIR-19
title: 後議三項落地批＋codex 現況行
status: Done
assignee: []
created_date: '2026-09-03 14:00'
updated_date: '2026-09-03 14:24'
labels:
  - governance
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/_archived/09-03-post-air13-batch/work-orders/wo5-rule-surgery-batch.md
  - >-
    ai-analysis/_tasks/_archived/09-03-post-air13-batch/work-orders/wo5-rule-surgery-batch.md
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-13 後議三項 user 已裁定（09-03）：四律2/4＋九律2/5/6/8/9 進 ai-rules（四律3 推算優先不進——帳制趨勢 token 化、設計偏向 request/token 雙少、大概判斷即可）；擇要三條全進（背景長跑 pipe 失明→debugging、git pathspec→modern-cli、Edit 邊界→tool-discipline）；contracts.md 補 muse 欄兩張表（每格附鏡像 file:line、過時以原站為準）；codex 現況行（family 表＋解析表備註→ad-hoc 選項低頻、context 小禁大工單）。載體：WO-5 手術批＋WO-6 contracts 欄，muse 工單＋GLM reviewer。驗收：各落點精確詞 rg 命中＋bundle gate 未爆（93% 起跳、rule 側每條最小化）＋reviewer record
<!-- SECTION:DESCRIPTION:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-09-03 14:24
---
【reviewer records 09-03】WO-5（11 檔手術批）：muse 12 項全落地（項1 dogfood 前兩腿驗證已承載 no-op 附行號、只補第三腿）＋GLM reviewer accept——1🟡 F-1 兩 skill description 缺新節觸發詞（reviewer 側已修：acceptance-evidence＋抽樣/全量對帳/樣本選擇、arch-thinking＋先查既有/注入先例/自命發明）＋5ℹ️（post-build 註記搬執行約束✓、九律9 懸空標籤移除✓、數字補回✓、報告 provenance、工單 9vs11 計數規格瑕疵）。WO-6（contracts muse 欄）：muse 7/7 過＋五處底稿不符以鏡像為準＋GLM reviewer needs-fix→4🟡 全修（10m→5m、mcpServers 引用改 changelog.md:35〔全檔 rg 抓到引用錯檔〕、browser 窮盡宣稱修正、hooks.json :82 空行→:83,87）＋F6 observers 補 :48。L4 事實實證：pathspec 兩陷阱 live demo confirmed（root 112 檔 vs 目錄內 0 檔；dir/ fatal vs dir stage 成功）。驗證 watch 清單（本批 12 項的行為面驗證預測，corrections-weekly 週報承接）：①背景長跑→應重導檔案輪詢非 tail pipe②目錄內 pathspec→應回 root③共享檔搬移→應先 rg 錨點④抽樣推廣→應問樣本選擇機制⑤框架行為 bug EP→根因應標推測需 L4⑥收尾報告→應有上界/實測分列。違反即規則未生效信號。
---
<!-- COMMENTS:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
後議三項全落地：mosaic 方法論 10 條（四律2/4＋九律×5＋擇要×3）進 ai-rules 各 skill/rule、codex 行降級 ad-hoc、contracts.md 兩表補 Muse 欄（每格 file:line）——muse 工單×2＋GLM reviewer×2（1 accept＋1 needs-fix 修堊）、L4 pathspec 實證、deploy 3/3 gate 95%
<!-- SECTION:FINAL_SUMMARY:END -->
