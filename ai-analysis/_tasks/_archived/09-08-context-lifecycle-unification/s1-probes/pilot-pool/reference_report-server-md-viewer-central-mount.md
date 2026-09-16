---
name: report-server-md-viewer-central-mount
description: ":6421 md preview 中央掛載定案（09-03 選項②）——viewer 單一源
  ai-rules/report-assets；URL 帶 route 前綴（ai-rules=/ai-rules/）不含 ai-analysis/ 段、
  .md 連結一律 viewer 形態（raw 直連違 lint）"
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_7622de15-8cf2-4fc5-a0b2-49b7f5f19f0b
---

report server＝mosaic launchd `com.mosaic.report-server`（:6421，panel `--static-dirs` route：main/v2/warrant/ai-rules；route root＝ai-analysis 內容、URL 不含 `ai-analysis/` 段）。

## 中央 viewer（09-03 晚 user 定案選項②「一次改好」）

- **單一源版控**：`ai-rules/report-assets/_md-viewer.html`（3.2KB——`fetch(?p=)` 同源絕對路徑＋marked/mermaid CDN）；server 加 mount `viewer=<該目錄>`
- **preview URL 形態**：`http://127.0.0.1:6421/viewer/_md-viewer.html?p=/<route>/<相對於該 route root 的路徑>`——一份 viewer 渲染任一 route 的 md
- **raw `.md` 直連 by design 原檔**（static server 不做內容轉換）——user 預期點 md 就是 preview；鑄 .md 的 http 連結（卡 ref 過渡形態）**一律 viewer 形態**（kanban-board 雙 ref 合約行已補精確 URL＋注記）
- 相容：mosaic per-route 舊份 `/main/_md-viewer.html` 留住（歷史卡連結不斷）；per-route 副本不再新增（ai-rules route 根的臨時副本已移除）
- **防呆三層（09-03 晚，user 問「之後寫 card 會搞錯嗎」）**：①kanban-board 雙 ref 合約行已含精確 viewer URL＋「raw 直連永遠原檔」注記——同 repo 四 harness session 動卡載 skill 即得②muse/subagent 不載 skill——工單對卡機制**指向合約路徑不內嵌值**（詳 [[work-order-contract-point-to-source]]；AIR-18 結案 raw URL 失誤即工單內嵌舊值所致）③機械網雙腿：週日治理 cron fed036ff 段 3 卡 ref lint（advisory）＋**ai-rules repo 內殼 lint 已機械化**（scripts/check_report_shells.py `_RAW_MD_ROUTE` 規則——tracked 殼 href 含 `/ai-rules/...*.md` 且非 viewer 形態＝violation，經 `report_shell_provenance` invariant 接進 check_single_source；09-06 落地，實作者 raw URL 回歸即由此線抓回）
- 改 mount 動 `mosaic_alpha/deploy/scripts/run-report-server.sh`（`--static-dirs` 單 flag 空格分隔陷阱見檔頭注記；guard 對不存在 dir 拒起）＋重啟 `launchctl kickstart -k gui/$(id -u)/com.mosaic.report-server`；mosaic 側 script 已 scoped commit `23f6c151`（user 鑑識「你做一半就跑了？」後收掉——跨 repo 活改動不留未 commit 給對方 batch）
- **不採**：掛整個 `~`（.ssh/憑證全變可 fetch）；~ 下未版控資料夾（離開版控）

## 診斷模式：「服務掛了」先辨死活

user 回報掛了→先分辨 **server 死 vs 連結指向已搬走的東西**：`~/.mosaic/logs/ops/launchagent-report-server-err.log` 的 404 路徑會說話（09-03 實證：muse 遷任務家 done/＋viewer 中央化同一分鐘發生，user 手上舊分頁全 404 但 server 活著——多寫入者並行期，搬遷類操作會使既有連結集體失效）。

**路徑形態錯誤家族（09-08 實證）**：從舊卡（air-20，pre-contract 形態）抄 URL 樣板 → `?p=/ai-rules/ai-analysis/...` 多含 `ai-analysis/` 段 → 整批連結 404。判別法：**已知舊檔也 404 ＝ 路徑形態錯，非檔案消失**（`/ai-rules/_tasks/_archived/<舊任務>/ep.md` 對照 curl）；URL 形態以本條合約為準（不含 `ai-analysis/` 段），**勿抄舊卡**。**lint 缺口**：`check_report_shells.py` `_RAW_MD_ROUTE` 只抓 raw-vs-viewer，抓不到「viewer 形態但路徑含 `ai-analysis/` 段」——09-08 五處錯連結全繞過防線靠 user 404 回報才發現；候選補規則：`?p=` 路徑禁含該段（記給 AIR-45 S3/lint 段）。
