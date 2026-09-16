---
name: user-project-first-containment
description: user 以專案（線）為單元要物理包含；結構美化（前綴/傘形/改名）會被喊停——交付最小功能差異；00- hack/sprint 不提
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_89592a9f-fbba-4b02-ade1-3b58b15bfd54
---

2026-09-02 目錄重設計弧中 user 多度修正我，按序沉淀：

**① 專案包含（兩度 push）**：「大方向專案裡面應該會有小任務＋相關文檔」「一個 page 裡面可能有許多小任務啊，當然雜項可以另外算」，自述工作觀「人類一般應該會是以一個專案專案的形式做事情」。我第一版給 flat＋line-tag＋tasks.md 帳冊（邏輯包含、以 ai-rules 機械 hardwire 為由反對巢狀），被 push 後改判物理巢狀（`projects/<線>/tasks/`→`<線>/done/`，雜項池退位）——改判後帳冊可直接刪（done/ 即歷史），嚴格更簡單，原顧慮（放置分支手術、misc→線晉升 git mv、全域視圖 fd 化）皆有界。

**② 前綴真相**：user 揭露 `00-` 前綴＝「AI 幫我把 tasks 往上拉的作法」，當時意圖＝AI coding 目錄聚頂好查（VSCode 瀏覽）；「00-tasks 這名字也是蠢」。並抓到我自相矛盾：才說「不放 ai-rules」卻把 marking 埋在中段字母序 ai-analysis/——口頭守 repo 分工、實際違他目標。後續查證：`_` 前綴排序跨工具不穩（Finder 忽略前導底線）、業界語義＝私有/框架保留非釘頂。

**③ 喊停過度工程（弧末關鍵）**：v5 傘形 `_work/` 交付後 user：「你這跟目前用 ai rules 有啥差？我只要把 00-tasks 重訂位加上 projects 跟整理就好了啊？」——四輪設計每輪加一層結構（lines/→`_` 前綴→傘形），功能核心從未變；聚頂/前綴訴求是 user 初始直覺，看到成本後自己放棄。

**Why**：user 的存取模式是線內局部性（知識＋待辦＋任務＋歷史同樹）；但他對「跟現況差距多大的結構改寫」極敏感——結構純度與機械便利論不敵最小改動；替代品（tag/view/ledger）與無語義排序 hack（`00-`）在 user 確認接受前不該當答案交付；宣稱的設計原則要與他的目標一致，半套落實會被抓矛盾。

**How to apply**：為 user 設計目錄/工作流時：①專案層物理包含是預設形態；②聚頂/前綴排序訴求 scope 敏感——repo-root 規模被喊停、user 瀏覽層（如 ai-analysis/ 內）是真需求；提案帶語義前綴（`_`=活躍面這類 self-documenting 標記）非無語義 hack，跨工具限制（Finder）標註但影響 bound 在單層目錄；③**功能核心穩定的迭代裡勿順手加結構純度層——每輪自問「跟現況的 functional delta 是什麼」並明說；cosmetic 與 functional 分開標籤，cosmetic 標「可丟」**；④排序/命名機制提案前必跨工具查證＋業界語義 grounding——聚類需求優先用包含（結構）達成、不賭 collation；⑤時間盒方法（sprint/timebox）對 solo+AI 事件驅動預設不提——節奏改用 WIP limit＋定期 triage＋STATE.md 焦點面；⑥設計評估可用背景 agent 模擬使用者視角走查（user 明確背書）；⑦跨 repo 設計討論（session cwd≠標的 repo）路徑必錨定 repo 歸屬（絕對路徑或 repo 名前綴）——相對路徑 tree 讓 user 失向（兩 repo 都有 ai-analysis/ 同名異物加劇混淆）。弧脈絡：[[mosaic-ai-analysis-directory-review]]。
