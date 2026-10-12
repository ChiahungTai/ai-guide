---
harness-scope: neutral
---

# 協作約束

## 理解與查證

需求不明先複述理解、列解讀並一次澄清，禁猜測實作；非硬 gate 的確認集中完成報告。commit、破壞性、單向門依 [outward-action-consent](outward-action-consent.md)。

分析須據實碼附 `path:line`＋特徵；「支援／不做 X」都須查證，自審不可替代獨立證據（acceptance-evidence）。AGPL 可研究行為／設計，禁搬碼或逐行翻譯；依自身規格實作。fork/divergent 的 state-dependent 行為查本地 runtime source，不以 upstream 文檔代替。

刪／併疑似等價的無測試檔前，查 README 指名、Capabilities、git 活躍度、backlog 依賴；存活檔只搬路徑未吸收內容＝刪錯訊號，停下重判。

## 表達與建議

禁無據的「大概／可能／應該可以」；給步驟及 `path:line`，技術比較附原理＋範例。因 rule/skill/hook 停止、降級、改道時，首行標來源＋原因。檔案連結用 backtick 包 workspace 相對 `path:line`；行號未知只列路徑，禁捏造；不套一般 code span。

接收建議依 READ→UNDERSTAND→VERIFY→EVALUATE→RESPOND→IMPLEMENT；查不了明說，錯誤建議附理由反對，成立才修；盲改指標可能污染回測。YAGNI／filter trap 判準見 acceptance-evidence skill。

## Workspace 與派工

不 `cd` 其他 repo；跨 repo 用絕對路徑或 `git -C`。他人未提交變更預設無關，不審不改；commit 僅 add 指名檔；目標檔已有他人變更或同區域改法衝突，停下確認。

跨 repo 寫入由主 session 授權／協調，mutation 走 writer／對方主權隔離面，主 session 不親改。spawned／automation 限卡 owning WT；寫不進或 ownership 不明就回報，禁轉給受限 agent。寫檔 agent prompt 注入三條，WT 自檢依 agent-workflow skill。
