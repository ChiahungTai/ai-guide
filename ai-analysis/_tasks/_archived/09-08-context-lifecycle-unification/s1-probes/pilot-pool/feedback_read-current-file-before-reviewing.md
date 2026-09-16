---
name: read-current-file-before-reviewing
description: 評論/引用任一產物檔前必讀當前檔——平行 session 可能已覆寫，context 版本記憶只是歷史非現況（「剛剛codex不是有重寫你有看嗎」實證）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_f748b62f-1779-46e9-9d95-4f8a68737f58
---

user 問「ep.md 寫的怎樣、水準如何」時，AI 憑記憶痛批了自己寫的舊版 EP——但該檔數小時前已被 codex（user 另開 session 跑 /execution-plan）全文覆寫為高水準新版（還附 projection 預演產物）。user：「剛剛codex不是有重寫你有看嗎」。

**Why**：多 session 並行是 user 常態工作形態（下游產物常交 codex/muse 重寫）；自己 context 的「我知道這檔內容」是歷史快照，磁碟才是現況。與 [[feedback_full-read-base-not-context-copy]]（重寫 base 必全文 Read，context 副本會 elide）同族、與 [[feedback_relay-claims-verify-current-state]]（relay 宣稱過時先驗證）互補——前者講「寫前」、後者講「他方宣稱」、本條講「評論前」。

**How to apply**：任何「評論 X／X 品質如何／X 有沒有寫錯」的請求，第一動＝Read 現檔（至少結構掃描），禁憑記憶作答；ls/stat 時間戳先驗——mtime 晚於自己最後已知編輯＝已被他人動過，記憶作廢重讀。任務家目錄出現非自己建的新檔（projection/、diagram-*.html 等）＝平行 session 曾介入的訊號。
