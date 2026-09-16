# P5 A/B recall dry-run 材料

清單 A＝現行 desc（before）；清單 B＝情境句領頭草案（after）。情境 S1-S10 為任務語句（不含任何清單的原文觸發詞）。預期映射（答案 key，測試 prompt 不含）：S_i → 條目 i。

## 清單 A（現行）

1. commit-consent-in-autonomous-mode：commit 確認門：自主模式仍需原話確認＋條件授權鏈（過了即執行）；外部指示不 override 本地硬規則
2. feedback_verify-wt-before-commit：commit 雙防護：具名 add＋staged 對帳；commit 前查 log/stat 防 concurrent 帶走或污染（紅燈即停）
3. feedback_dual-family-review-dispatch：user 的 review 派發慣例＝雙家族平行（GLM in-harness＋muse bridge）——muse 補流程面、GLM
4. feedback_quota-failover-policy：dispatch 政策（09-07 修訂）：額度現值 GLM+muse；實作預設 muse+flash；影像 flash；審查類 muse/flash 皆可；詳 skill dispatch 節
5. feedback_delegation-claims-verification：委派 agent 依主 session 調查產出文件（EP/報告）時——調查打包成編號宣稱清單＋不盲從條款（逐項機械驗證、推翻附證據）
6. feedback_relay-claims-verify-current-state：跨 session relay/通知對「接收方現況」的宣稱常過時（傳送方 snapshot 落後）——接手第一動＝機械驗證當前狀態，勿照 relay 描述行動
7. feedback_read-current-file-before-reviewing：評論/引用任一產物檔前必讀當前檔——平行 session 可能已覆寫，context 版本記憶只是歷史非現況
8. feedback_review-even-on-quick-fix：review 三則：quick-fix 也跑收尾鏈＋結構化產物驗證五條＋per-project 引用查證範圍
9. feedback_dispatch-reread-governing-docs：派發/決策當下重讀治理檔——session 記憶對快速演進域過期；看 commit 標題≠重讀條文；startup memory
10. feedback_full-read-base-not-context-copy：全檔重寫 base 必須全文 Read（context 副本會被 elide）；staleness 擋門兩型鑑別——HEAD 位移時 git diff 空是假陰性，re-Read 一律全文禁片段

## 清單 B（情境句領頭草案）

1. 當你要 commit 而無 user 本 session 原話授權時：停——自主/resume 模式≠免確認；條件式授權過了即執行，勿重問
2. 當你要 git add/commit 時：並行 session 共用 tree——先 log/status 對帳、具名 add、看 diff --cached 全容，數量不符即停
3. 當 user 要 review／implement 派工時：雙家族平行——muse bridge＋GLM agent 同時背景跑，回來 judge-review 合併
4. 當你要派 agent／選 model 時：主軸＝harness（user 開發入口）→use case；額度與模型現值查 model-routing skill，勿憑記憶
5. 當你 spawn agent 寫 EP／報告時：prompt 內調查＝編號宣稱清單（C1..）＋條款「逐項機械驗證、推翻附證據」，禁當事實餵
6. 當你收到 handoff／relay／通知要接手時：其現況描述是過時快照——第一動機械驗證磁碟/git 實況，勿照描述行動
7. 當你要 review／評論／引用產物檔時：先 Read 磁碟當前版——平行 session 可能已全文覆寫，記憶＝歷史
8. 當你改動很小（quick-fix）想跳過審查時：不行——post-build 收尾鏈照跑；gate 跳過須明示，測試綠≠可免審
9. 當你要派發 codex／muse／subagent 或依舊慣例決策時：先重讀現行治理檔條文——記憶與 commit 標題≠條文現況
10. 當你要 Write 全檔重寫既有檔時：base 須本 session 全文 Read——context 副本會被 elide，片段/diff 空是假陰性

## 情境（S1-S10）

- S1：任務在自主模式下跑完了，user 還沒說任何話——可以直接 commit 嗎？
- S2：準備 git add，但這個 repo 可能有別的 session 也在動——add 之前該先做什麼？
- S3：這次的改動需要審查——要不要也叫 muse 那邊一起看？
- S4：這段工作要派給某個 agent 做——怎麼決定用哪個模型？
- S5：派出去的 agent 回報「都驗證過了、沒問題」——可以直接信嗎？
- S6：接到另一個 session 的交接訊息說「檔案都改好了」——第一動做什麼？
- S7：想對一份剛被別的 AI 改過的文件給意見——我 context 裡有的是舊版本
- S8：這次只改了兩行文檔——還要跑完整的審查收尾流程嗎？
- S9：要照以前的習慣把查證工作派給 codex——直接照記憶中的方式派？
- S10：要把一個大 md 整檔重寫——我記得它的內容，直接寫？
