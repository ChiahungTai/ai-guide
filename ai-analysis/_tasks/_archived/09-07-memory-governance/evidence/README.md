# Evidence — AIR-42 前期 POC（唯讀探測，非正式 production 證據）

產出：`../poc/poc_telemetry.py`（唯讀：ZCode DB `mode=ro`＋CC transcript 目錄掃描，metadata-only，不存對話正文）。
跑法輸出見 `probe.log` 尾行；本目錄 `telemetry.json` 為該次輸出快照。

## 觀測窗與來源覆蓋

- `window`：請求窗 2026-06-09→2026-09-07（90 天）。
- `zcode_bounds`：實際 ZCode 資料 `first` 2026-08-16 → `last` 2026-09-07，`global_parts` 390226。**不足 90 天——不可宣稱完整 90 天結論。**
- `cc`：掃描 ai-rules 主 transcript 目錄 22 檔（`first` 08-12 → `last` 09-05，`malformed_lines` 0）。**已移除 worktree 歷史目錄未列舉——覆蓋不全。**

## 欄位

- `counts`：`<來源>:<工具>:<狀態>` 事件計數（成功／error 分開；失敗不可計入成功）。
- `top_writes[]`：`source/session/entry/events/payload_chars`——**raw top，含 fork/side-chat 複製，不可當正式榜單**。
- `origin_last_writer_mismatch[]`：`originSessionId ≠ 觀測最後寫入者` 條目（`origin_mismatch_count` 86/128）——origin 只作來源參考，不可當作者歸因。
- `inventory[]`：128 現存條目快照（entry/current_chars/mtime/origin/successful_reads/writers/last_writer）。
- `clone_candidate_groups[]`（`clone_candidate_group_count` 70）：同 input hash＋操作時間、callID 不同——fork/side-chat 複製候選，需 lineage 查證，不可按 callID 去重。
- `observed_zero_body_read_count`（32）：觀測窗內零 body Read 計數——**raw 數，不是可刪候選數**（維護 Read 未分類＋來源覆蓋不全）。
- `limitations[]`：7 條已知限制（以此檔為準，引用時逐條核對）。

## 使用約束

正式 collector（AIR-40 S1/S2）不可直接沿用本快照數字作首跑證據；`origin_mismatch`、`clone`、`zero_read` 三數僅證明「問題存在」，不可當正式報告數字。
