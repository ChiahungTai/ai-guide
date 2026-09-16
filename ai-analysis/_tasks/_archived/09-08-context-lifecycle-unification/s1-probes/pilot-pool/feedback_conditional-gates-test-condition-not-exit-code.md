---
name: conditional-gates-test-condition-not-exit-code
description: 條件閘門要驗「條件成立」（test -f／rg -l 輸出）非 exit code 短路——fd 無命中仍 exit 0，`fd X && cmd` 誤跑檢查（09-03 實證）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_9184c58a-9f15-4d81-934e-6cb9060e653d
---

2026-09-03 實證（CR 改善弧收案段）：post-build 階段 4 條文「repo **有** `.tours/manifest.toml` → 跑 tour_validate」，我寫成 `fd manifest.toml .tours && code-reality tour_validate ...`——fd 無命中仍 exit 0，`&&` 鏈照跑，在無 manifest 的 ai-rules 產生 FAIL 噪音；且第一時間歸因成「pre-existing scaffold 噪音」把自身誤跑 externalize（user 追問「這檢查是 cr 還是你這邊跑的」才釐清：決策在 ai-rules 側 gate、FAIL 語義在 CR 側，但觸發是我沒守住 gate）。

**Why**：工具 exit code 表達「命令執行成功」非「條件為真」——搜尋工具無命中時 exit 語義各異（fd=0、grep=1），拿 exit code 當條件閘門是隱式契約、換工具即碎；skill 條文寫的是「條件存在」，對應的機械檢查應直接驗條件本身。

**How to apply**：條件閘門一律顯式驗輸出——`test -f <path>`、`rg -l <pat> <dir> | grep -q .`、或先 ls 再判斷；`fd X && cmd` 形態僅在確認該工具「無命中 exit 非 0」時可用。歸因紀律對偶：回報「pre-existing 噪音／環境問題」前先自查執行面——「這檢查/這步驟本來該跑嗎」。相關：[[git-mv-nesting-and-verification-traps]]（&& 鏈陷阱家族）、[[settlement-scripts-are-code]]（量測/執行腳本自身先受檢）。
