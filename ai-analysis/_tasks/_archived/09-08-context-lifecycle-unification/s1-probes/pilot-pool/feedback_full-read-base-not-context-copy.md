---
name: feedback_full-read-base-not-context-copy
description: 全檔重寫 base 必須全文 Read（context 副本會被 elide）；staleness 擋門兩型鑑別——HEAD 位移時 git diff 空是假陰性，re-Read 一律全文禁片段
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_83042391-91fe-41fb-aa12-18762b005566
---

對既有檔案做**全檔重寫**（Write 取代）時，base 必須是本 conversation 內的**全文 Read**；不得以 system-reminder 帶入的檔案內容、或早先輪次殘留在 context 的副本當 ground truth。

> merged_from: feedback_write-staleness-mtime-vs-content.md, 2026-08-31

**Why**: 長對話的 context 管理會**刪節舊內容**（含 system-reminder 內嵌的 instruction 檔內容）——副本比 repo 現況短而不自覺。實證（2026-08-21 ai-rules 截斷修復審查輪）：3 個 rules 檔依 context 副本＋片段 Read 重寫，把 repo HEAD 有、副本被 elide 的段落**無聲回退**（合作約束的輸出格式模板、深層思考輸出模板等）；靠「diff 刪除行規範語句逐一驗存活＋與 HEAD 全文對帳」才抓回，補救 5 處。片段 Read 只夠當小修的 Edit 前置，**不夠當重寫的 base**。

**第二實證（2026-08-30 T2-2，staleness 變體）**：Write 被 staleness 擋下後誤判 mtime 假警報，只片段 re-Read 前 15 行就重寫 rules/model-routing.md 全文——read-state 其實落後一個並行 commit（8201987 更新了 vision cell），漏掉的 :21 隨骨架重寫回退到兩版前的語義，三個 review agent 交叉同中才抓回。教訓：staleness 後 re-Read 一律全文；HEAD 位移時 `git diff` 空是假陰性（兩型鑑別見下方段）。

**How to apply**:
- 重寫（Write）前：全文 Read 目標檔（未讀過或只片段讀過 → 補全文 Read）
- 重寫後必驗：機械掃 diff 刪除行中的規範性語句（禁止/必須/強制等 marker），逐條確認概念仍存活於新文或已明確搬遷（pointer/skill 落點）
- 相關：[[feedback_cjk-char-corruption-rg-verify]]（改後機械驗證同族紀律）

## Staleness 擋門兩型鑑別：mtime 假警報 vs HEAD 位移假陰性（write-staleness-mtime-vs-content 併入）

Write/Edit 的 staleness 擋門有兩型，被擋後的鑑別與 re-Read 紀律（2026-08-30 T2-2 兩階段實證，第二階段即上方第二實證）：

- **①mtime 假警報型**：Write 被擋，`git diff` 空＋**HEAD 未動**＝純 mtime 假警報（git 索引刷新），re-Read 後重試即可。
- **②HEAD 位移型**：首讀在並行 session 數批 commit **之前**、被擋時 HEAD 已位移——`git diff`（working tree vs **新** HEAD）空是**假陰性**：diff 只證 working tree==新 HEAD，不證「自 read 以來未變」（相對我的 read-state，檔案可能已被並行 commit 帶入新內容）。誤判成 mtime 型後只片段 re-Read 就重寫＝語義回退 regression（上方第二實證）。

**How to apply（staleness 段）**：被擋時先 `git diff <file>`＋`git log`（比對 read 當時的 HEAD 是否位移）——HEAD 未動且 diff 空＝mtime 假警報；HEAD 已位移＝diff 空是假陰性。兩型共同鐵律：**re-Read 必須全文**（或 `git diff <read-time-HEAD>..HEAD -- <file>` 看真實變更），片段 re-Read 只夠當局部 Edit 前置、絕不可當全檔重寫 base；重寫後對照 read-time-HEAD 驗無回退。
