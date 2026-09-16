---
name: reference-hook-python-heredoc-write-block
description: PreToolUse hook 擋 python heredoc 寫檔（Edit/sed 禁令繞道偵測）——改檔含
  scratch/POC 一律 Read+Edit/Write 工具管道
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_67e0c1d8-0c00-4239-946f-694e9e86df4b
---

本環境（ai-rules workspace、ZCode）PreToolUse hook 攔截 `python3 - <<EOF` 內含 `write_text()`/`open(...,'w')` 的呼叫——判定為 Edit 工具與 sed 禁令的繞道形態（hook 自述遙測實測 319 次），理由：不可追溯、無 read-state 保護。**適用範圍含暫存/POC 檔**（09-06 scratch repo 回填卡片日期被擋實證）。heredoc 僅用於純計算/查詢；任何改檔——含 `.agent-tmp/` scratch——走 Read＋Edit/Write 工具管道。
