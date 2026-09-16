---
name: feedback_sj-nt-authority-routing
description: SJ/NT 查證路由（user 2026-09-01）：SJ 問 shioaji skill、NT 讀 repo（v1/v2
  兩目錄＋nt-query skills）；補記憶前先查既有記載只補缺
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_243e6d50-4ac0-4457-9e5f-5a69277871d4
---

user 2026-09-01 於 mosaic 記憶治理 session 兩度指示（「SJ 有 Skill 可以用，重點是要去問 sj skill」「NT 有 repo，也分 v1 v2 兩個不同目錄，也有 nt query skill，這些都要利用，記憶要記住這些吧」）：

**查證路由**——SJ 行為疑問 → 問 shioaji skill（designated authority；upgrade-sj skill 已明文路由「使用 Shioaji Skill 查證實際行為」）；NT 行為疑問 → 讀 NT repo 源碼，**分 v1/v2 兩個目錄**（`~/Github/nt_v1` 與 `~/Github/nautilus_trader` fork workspace），並利用 nt-query／nt-v1-query skills。memory 條目的定位＝踩坑記錄＋專案接線，非行為權威源——查證回源頭。

**補記憶紀律**——「你是要去查看看記憶有沒有寫好，有寫好就不用寫，沒寫好才要補」：接到「記住 X」類指示，先機械掃既有記載再決定寫不寫。掃描要含連字號變體（rg "shioaji skill" 帶空格會漏 "shioaji-skill"）。實查結果（mosaic 池）：nt_v1 路徑（reference-sync-stubs 條）、nt-query 教訓段（nautilus-trader）、v2 fork（project-nt-v2-migration）已散在多條；SJ 明確路由句是主要缺口——D1 蒸餾落地後只在 nautilus-trader.md／sj-api-and-stubs.md 檔頭補缺行。**後續閉環（09-01 固化波 f715840）**：upgrade-sj 補「SJ Sync Stubs」段＝skill 端缺口已補，sj-api 記憶的「upgrade-sj 零記載」句同步改指針（「固化→濃縮同步義務」首次應用）。

**載體形態（2026-09-01 user 點破「這是 plugin 的 skill 啊」）**——shioaji skill 是 **marketplace plugin skill（Claude 端 plugin 系統，dev Sinotrade、v1.7.4），不在 ai-rules**：①因此不在 skill-dedup 比對語料（A6 findings 已正確標註）；②可用性受限——只在掛載該 plugin 的 session（Claude Code）問得到，未掛載環境（如純 ZCode session）退而查其 HTTP API 文檔或 memory 踩坑記錄；③涵蓋面比 memory 條目廣得多（Python sync/async、CLI、HTTP API、SSE streaming、JS/TS/Go/C/C++/C#/Rust/Java/Kotlin SDK、下單/行情/Contract V2 lazy lookup/即時 K 棒/加值指數/市場訊號/帳戶/watchlist/預約單/遷移/troubleshooting）。補進 sj-api-and-stubs.md 的路由行須標明 plugin 形態與此 fallback。

與 rules/context-management 寫入四問 Q2（同主題已有→加段）同構——此條是其「user 要求記住 X」場景的實證應用； user 原話為糾正錨。
