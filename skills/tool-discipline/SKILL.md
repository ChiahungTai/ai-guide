---
name: tool-discipline
description: "工具紀律深層載體 — Edit 失敗處置階梯全文（re-Read 取當前狀態→第二次同型 not found 停止盲試禁第三次→Python repr 唯讀診斷 bytes→縮小 old_string〔多位元組字元跨行匹配常是肇因〕→full Read＋Write 整檔覆寫前提：剛完成完整 Read 且確認無並行變更）、zsh 動態 flag 細則（未引號變數不 word-split、純量陷阱真實案例 --primary 1 被當單參數而 argparse 拒絕、≤2 組合可分支、單 flag 用 --flag=1、禁 setopt shwordsplit 與 ${=var}）、Read 紀律細則（已完整讀過的檔案重查用 rg/offset/limit 禁再全讀、大檔具體問題先定位、86KB 檔重讀十九次案例）。always-on 核心（uv run 前綴、禁 sed 修改、pytest 背景跑、pipe gate、批次化）在 rules/tool-discipline.md；Edit 連續配不上、組 zsh 動態命令列、重查已讀大檔前載入。觸發詞：Edit 失敗、old_string not found、多位元組、word-split、args 陣列、shwordsplit、flag 純量、重讀、context 佔用、repr 診斷、整檔覆寫。"
---

# tool-discipline — 工具紀律深層

> 本 skill 是 `rules/tool-discipline.md` 的 on-demand 深層載體：rule 端保留 always-on 核心（工具選擇、Skill 調用、Python 命令執行、檔案修改禁令、zsh flags 核心句、Read 紀律核心句、背景執行、pipe gate、批次化）；本檔承載 Edit 失敗處置階梯全文、zsh 動態 flag 細則與 Read 紀律細則。

## Edit 失敗處置階梯（canonical）

Edit 失敗 → 先 re-Read 取得當前狀態；第二次同型 not found 後停止盲試（禁第三次）。文字肉眼在場卻配不上 → 用 Python repr 唯讀診斷 bytes（唯讀查證，不違反 sed/Python 替換禁令）。接著縮小 old_string（多位元組字元跨行匹配常是肇因）；仍失敗才 full Read＋Write 整檔覆寫——前提：剛完成完整 Read 且確認無並行變更（整檔覆寫放大 blast radius）。

## zsh 動態 flag 組合（陣列、禁純量）

zsh 未引號變數不 word-split；動態 flags 用 `args=(--flag 1)`＋`cmd "${args[@]}"`，禁 `"--flag 1"` 純量（真實案例：`--primary 1` 被當單參數而 argparse 拒絕）。≤2 組合可分支、單 flag 用 `--flag=1`；禁 `setopt shwordsplit`/`${=var}`。

## Read 紀律（context 佔用）

已完整讀過的檔案重查用 rg/offset/limit，禁再全讀；大檔具體問題先定位，首次理解/小檔可全讀。真實案例：86KB 檔重讀十九次，重複佔滿 context。
