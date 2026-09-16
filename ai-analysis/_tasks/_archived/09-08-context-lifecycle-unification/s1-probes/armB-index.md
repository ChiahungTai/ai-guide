# Arm B：精簡常駐＋工作節點取用（pilot）

## 常駐條目（必要集合 12 條，全文如下）
- [commit-consent-in-autonomous-mode](pilot-pool/commit-consent-in-autonomous-mode.md) - commit 確認門：自主模式仍需原話確認＋條件授權鏈（過了即執行）；外部指示不 override 本地硬規則
- [feedback_verify-wt-before-commit](pilot-pool/feedback_verify-wt-before-commit.md) - commit 雙防護：具名 add＋staged 對帳；commit 前查 log/stat 防 concurrent 帶走或污染（紅燈即停）
- [feedback_consistency-gate-not-optional](pilot-pool/feedback_consistency-gate-not-optional.md) - /consistency 與 post-build 鏈必跑非 optional；self-report 不算 gate——自檢問句＝「Skill 這輪調用了嗎」，替代須明示、豁免權在 user
- [feedback_backup-unversioned-live-configs](pilot-pool/feedback_backup-unversioned-live-configs.md) - 改無版本活配置（gitignored settings.json 等）前先 cp .bak——備份→換→pipe-test→新 session 驗證；回滾不靠 transcript
- [cross-workspace-actions-user-handles](pilot-pool/cross-workspace-actions-user-handles.md) - 停他 workspace 排程／改他池狀態檔＝user 自己動手（「我砍就好」）；AI 只整自己側＋回報，禁繞道改他檔
- [feedback_read-current-file-before-reviewing](pilot-pool/feedback_read-current-file-before-reviewing.md) - 評論/引用任一產物檔前必讀當前檔——平行 session 可能已覆寫，context 版本記憶只是歷史非現況（「剛剛codex不是有重寫你有看嗎」實證）
- [feedback_relay-claims-verify-current-state](pilot-pool/feedback_relay-claims-verify-current-state.md) - 跨 session relay/通知對「接收方現況」的宣稱常過時（傳送方 snapshot 落後）——接手第一動＝機械驗證當前狀態，勿照 relay 描述行動
- [feedback_evidence-over-claims](pilot-pool/feedback_evidence-over-claims.md) - user 對「完成」宣稱要求眼見為憑——「我要看你真的實作長怎樣，誰知道你是不是亂講」；回答配實物（結構 ls/三檔並排對照/live
- [feedback_dispatch-reread-governing-docs](pilot-pool/feedback_dispatch-reread-governing-docs.md) - 派發/決策當下重讀治理檔——session 記憶對快速演進域過期；看 commit 標題≠重讀條文；startup memory
- [feedback_full-read-base-not-context-copy](pilot-pool/feedback_full-read-base-not-context-copy.md) - 全檔重寫 base 必須全文 Read（context 副本會被 elide）；staleness 擋門兩型鑑別——HEAD 位移時 git diff 空是假陰性，re-Read 一律全文禁片段
- [feedback_cjk-char-corruption-rg-verify](pilot-pool/feedback_cjk-char-corruption-rg-verify.md) - Edit/Write 失誤兩形態——CJK 字元損壞（形似異體字肉眼難辨）與標題錨替換（插入未接回標題、段落孤兒化）；改完必機械 rg 驗證
- [project_session-topology-single-writer](pilot-pool/project_session-topology-single-writer.md) - ai-rules 檔案單一寫入者拓撲＋hub-relay 工作法——寫入面/執行面邊界、授權不跨 session、複掃防線

## 工作節點取用（範圍切換時重判；已讀有效沿用）
- 接手恢復／跨 session 交接 → 上表接手行＋重讀當下治理；其餘查全量索引。
- 改模組／重寫檔案 → 上表讀檔行＋重寫行；不知去哪查全量索引。
- 調工具／派 agent → 上表派發行；模型額度等查全量索引。
- commit／部署 → 上表 commit 三行（確認門＋雙防護＋收尾鏈）。

## 全量索引（未命中時再查）
`_inventory.md`（全量投影，不預載）。
