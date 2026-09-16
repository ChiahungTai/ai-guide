---
name: feedback_diagnose-installed-vs-source-first
description: 外部工具（plugin/binary/bridge）炸時先比對「安裝面版本 vs source HEAD」再下診斷——修復常已
  commit 只是未發佈；「資產缺失」宣稱前先 ls 安裝面攤平佈局
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_75794c58-c131-4e06-8e87-b809c2b15d0d
---

診斷跨 repo 工具故障（plugin cache、安裝的 binary、bridge 腳本）時，第一步比對**安裝面版本 vs source repo HEAD**——修復可能已經 commit 只是未發佈/未重裝；「打包缺口／資產缺失」的診斷要先看安裝面的**攤平佈局**（marketplace cache 會把 source 子目錄攤平到頂層——資產常在場、只是工具解析路徑沒跟上攤平形）。

真實案例（2026-09-04 muse bridge）：`review` 子命令在外部 workspace exit 2 "Review template missing"——初診「cache 沒打包 prompts」兩處錯：①資產在場（攤平在 `<cache>/<ver>/prompts/`），是舊包 bridge candidate 只認 source 佈局 `../plugins/muse/prompts/`；②source HEAD 早已修好（6a2b2b7 加攤平 candidate），只差發佈＋重裝。handoff 差點寫成「請修 code」，實際只需「發佈＋重裝＋驗證」。

**Why**：安裝面與 source 是兩個時間點的快照——只看安裝面會把「已修未發佈」誤診成「沒人修」；只看單一佈局會把「攤平」誤診成「缺失」。誤診直接污染 handoff 內容（對方照錯誤診斷重做已存在的修復）。

**How to apply**：外部工具炸時序列——①查安裝面版本（cache 目錄名／plugin.json）②`git -C <source> log --oneline` 比對 HEAD 是否已有相關 fix commit ③ls 安裝面攤平位置確認資產在場 ④才下「修 code vs 發佈重裝」的診斷。同族：[[feedback_relay-claims-verify-current-state]]（機械驗證當前狀態，勿照陳述行動）。

**dev 機雙安裝面（2026-08-30 CR 實例）**：同一工具兩個安裝面並存——uv-pinned `~/.local/bin/code-reality`（消費面：plugin wrapper 與文檔 CLI 形態都指它）＋cargo face（dev 權威）；`cargo install --path` 重建**只更新 cargo 面**，uv-pinned 面版本不動（實測 0.4.1 續存→文檔指引的 `project` 子命令「不存在」假象）。對齊＝`uv tool install --force code-reality==<ver>`。附：binary 自報 `installed != repo HEAD` WARN 有兩種成因——真落後 vs checkout 前移（pinned release face 對前移後的 HEAD 恆 WARN，非異常；以 `--version` 的 `<pkg>+<rev>` 對 tag 判讀）。

**已修仍炸＝修復面不全（2026-09-06 CR 實例）**：安裝面＝source HEAD（0.6.3+1b53f6b、無部署落差）且 source 已有同名修復（b30af73「Python class DEF semantics」已在 binary 內），bug 仍重現——比對的第二層答案：**不是「沒人修」也不是「未發佈」，是既有修復未涵蓋該 repro 路徑**。handoff/下一步必帶「既有修復 commit＋勿重做、先 diff 其覆蓋面」，否則接手方重做同型修復。

**源碼查證層自身會錯——三層驗證陷阱（09-06 Backlog.md 遮蔽根因弧）**：查「機制在不在/為何不生效」時每種證據源各有失效模式——①**文件鏡像層**（zread 等）會服重構**前**舊快照：本例給出已除名的 standalone 函式形態、漏掉 BACK-624 class 重構——查現行碼以**本地 clone（含 tag、可 `git show <tag>:<file>` 對版）為權威**，鏡像只當線索；②**binary 靜態掃**：Bun 編譯 binary 的 strings 掃 JS 字面值全失效（payload 壓縮嵌入，連已知存在的 config key 都 0 命中）——**機械「不存在」結論前必跑正控制組**（先掃一個確定存在的字串；控制組也 0＝掃描器壞、非目標缺席——本例初掃四關鍵詞全 0，若無控制組就誤判「機制不存在於 1.50.1」）；③**接線事實＝版本對照 L4 實測**：抓目標版本平台 binary（在 npm 平台子套件 tarball 內）對真實 repo 開臨時 port 跑 API 對比——「程式碼存在但行為沒生效」這類接線問題靜態讀不出，實測定案。
