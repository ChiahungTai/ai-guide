# s0-probes PROVENANCE

每個 `.out` 的生成來源。原 S0 執行（impl-lite）部分 one-liner 未留存腳本——muse review F2 指出後，於 post-build 修正迴圈補建等值腳本並重跑（標 `rebuilt`）；throwaway debug 腳本已刪（muse review F3）。

| .out / 檔案 | 生成腳本 / 命令 | 狀態 |
|---|---|---|
| p1_scan1-6, 8-10 | 對應 `p1_scan*.py`（原建） | original |
| p1_scan7 | `p1_scan7.py`——**已修**（原版 `substr(m.data,1,2500)` 截斷 JSON 後 `json.loads` 必炸，muse review F1；改 SQL `json_extract` 拉欄位）並重跑 | fixed+rerun |
| p1_local_setting.out | `p1_local_setting.py`（rebuilt——原 one-liner 未留存） | rebuilt |
| p1_schema.out | `p1_schema.py` | original |
| p3_scan.out | `p3_scan.py`（P3 主證據） | original |
| p3_blocks.out | 由 `p3_scan.py` 涵蓋（block 族枚舉段落）；獨立 .out 為中途觀察 | covered-by-p3_scan |
| p3_debug.py / p3_debug2.py | —（hardcode 單 session 的 throwaway，被 p3_scan 取代） | **deleted**（F3） |
| p4_sections.out | `p4_sections.py`（rebuilt） | rebuilt |
| p5_entries.out | `p5_entries.py`（rebuilt） | rebuilt |
| p5_charcount.out | `p5_charcount.py`（rebuilt——after 文字取自 s0-report P5 表） | rebuilt |
| p6_codex.out | shell：`codex exec "逐字引用…"`（EP 紅線只試一次；失敗記錄） | original |
