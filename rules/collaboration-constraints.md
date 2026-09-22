---
harness-scope: neutral
---

# 協作約束

## 理解優先實作

需求不明先複述理解、列可能解讀並澄清，禁猜測實作；疑問一次彙整（避每次往返重送 context）。非硬 gate 的確認集中到完成報告；commit、破壞性、單向門依 [outward-action-consent](outward-action-consent.md)。

## 事實查證原則

分析結論須依實際程式碼，附 path:line＋具體特徵；任何「X 支援/不做 Y」都須查證，自審不能取代獨立證據（見 [acceptance-evidence](acceptance-evidence.md)）。AGPL 可研究行為/設計，禁搬碼或逐行翻譯，實作對自己的規格寫；fork/divergent 依賴的 state-dependent 行為查本地 runtime/`.venv/` source，upstream 文檔不代表 fork。

### 破壞性選擇的查證觸發

刪/併看似等價的無測試檔前，查 README 權威指名、Capabilities、git 活躍度/內容完整性及 backlog 依賴，禁憑檔名選；存活檔只改路徑卻沒吸收內容是刪錯訊號，停下重判。

## 具體明確表達

避免「大概/可能/應該可以」；提供具體步驟與 path:line。技術對比附範例＋原理。

## 接收建議與回饋（反 Sycophancy）

建議先 READ→UNDERSTAND→VERIFY codebase→EVALUATE→RESPOND→IMPLEMENT；核對適用性、既有功能與決策。查不了明說；錯誤建議附理由反對，成立就修——盲改指標會靜默污染回測。YAGNI（刪）與 filter trap（驗證不能刪）見 acceptance-evidence skill。

## 工作目錄紀律

- 不 cd 其他 repo；以 Primary working directory 為準，跨 repo 用完整路徑或 `git -C`。
- 他人未提交變更預設不相關，不審不改；commit 只 add 指名檔。**僅目標檔已有他人變更或同區域不同改法才是停下確認的機械衝突訊號**。

## Agent 派發與產出回收

跨 repo 寫入由主 session 負責；spawned/automation 只在卡 owning WT 操作，agent 寫不進目標或不能判定 owning 就回報主 session，禁把責任丟給受限 agent。寫檔 agent prompt 必注入三條（禁 /tmp／寫不進就回報／暫存集中 `.agent-tmp/`）；worktree 能力確認與完整自檢清單見 **agent-workflow skill**「Agent tool spawn 前」。
