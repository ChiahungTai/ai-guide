---
name: reference-bash32-set-u-empty-array-trap
description: shell 陷阱四則：set -e 賦值繼承/set -u 空陣列/zsh equals展開/多位元組變數名——護衛語法＋實證
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_67e0c1d8-0c00-4239-946f-694e9e86df4b
---

shell 嚴格模式＋展開是靜默腐敗家族——exit 碰巧對／輸出看似正常最危險；護衛語法＋空集合／特殊字元必測。

> merged_from: reference_bash-set-e-capture-assign-trap, reference_zsh-equals-expansion-trap, bash-32-multibyte-varname-trap, 2026-09-07 cluster-merge wave

## set-e 命令替換賦值陷阱（original: reference）

`set -euo pipefail` 下函數非零退出時，呼叫端 `f=$(find_card "$id")` 繼承退出碼觸發 set -e 提前終止——後續 controlled flow 全跳。**實證（09-03 backlog_precheck.sh）**：找不到卡 return 1 → 腳本被殺、`[不可清]` 訊息沒印，但 exit=1 碰巧等於預期 blocked 碼——happy path 測試抓不到。同族教訓見 [[feedback_conditional-gates-test-condition-not-exit-code]]（驗條件成立不信 exit code）。

**How to apply**：查找類函數尾顯式 `return 0` 或呼叫處 `|| true`；對抗 case 驗**訊息有印**不只 exit code；空 glob（`for f in dir/*.md` 無匹配 $f 是字面）加 `[ -e "$f" ] || continue`。

## set-u 空陣列展開（original: reference，keeper 本體）

bash 3.2（macOS `/bin/bash` 恆 3.2）三則，09-06 `run-backlog-cleanup.sh` 實證：**空陣列** `for x in "${ids[@]}"` 在 <4.4 報 unbound——護衛 `${ids[@]+"${ids[@]}"}`；**pipe 餵 while 落 subshell**（counter 帶不回）——先收陣列再迴圈（3.2 無 mapfile，用 process substitution）；空集合路徑是獨立必測分支（scratch 有資料全綠、真實 0 筆才炸）。rg 旗標陷阱另見 [[reference_rg-r-flag-display-replacement]]。

## zsh equals 展開陷阱（original: reference）

zsh 未引號 `==` 開頭觸發 equals-expansion（`command not found`、exit 127、&& 鏈全斷，08-31 實證）；**雙引號內反引號＝command substitution**（`--interval` 被執行、desc 靜默吃字，09-05 實證）。含 markdown 反引號的長 CLI 引數一律**單引號**包裹；改完 rg 驗特殊字元段在場。bash 慣性遷移家族（word-split、`-r` 旗標同族）。

## 多位元組變數名陷阱（original: reference）

`"$wt（detached"`——$wt 後緊接 CJK 全形字元，bash 3.2 把其位元組吃進變數名，set -u 下 unbound 崩潰（09-06 最小重現確證）。**launchd 無 locale＝production 活陷阱**（開發 shell UTF-8 可能不炸——本機跑過≠排程跑得過）；只在該行實際執行時炸，錯誤分支潛伏到深夜排程。解法 `${var}` 大括號；review 把 `$var` 後緊接非 ASCII 列必查位點。

## shell cwd 跨 call 持續（09-08 實證）

工作目錄跨 Bash call 持續——`cd` 進子目錄後沒回，後續相對路徑全歪：`git add <repo 相對路徑>` 報 pathspec 不存在、`ls <目錄>` 假空（stderr 被 `2>/dev/null` 吞時更險）。誤診風險：症狀像「檔案被平行 session 搬走/刪了」——**先 `pwd` 自查再懷疑別人**。防護：複合命令 cd 後記得回 root，或跨 call 作業一律絕對路徑。
