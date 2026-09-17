---
id: AIR-125
title: >-
  pre-commit hook 合理化——backlog fast path＋live-reading 測試 hook 模式隔離＋card-WT path
  錨定修復（併 AIR-116 follow-up）
status: To Do
assignee: []
created_date: '2026-09-17 14:48'
updated_date: '2026-09-17 22:06'
labels: []
dependencies: []
ordinal: 110000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
commit gate 今天誤擋大宗來自三個設計缺陷：純 backlog metadata commit 付 25 秒全量測試稅（無 fast path）、governance 測試讀 live config 使 gate 非確定性（職責放錯層——live drift 偵測該歸 monitor 日頻）、card WT 的 path 錨定假漂移逼合法工作常態走 --no-verify（逃生口疲勞磨損閘門信用）。修完 hook 從半個找砸回到全值合理。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 fast path：staged diff 全屬 backlog/ 時跳 pytest（保留 control-plane-guard＋py_compile 腿）——metadata commit 從 25s 降到 1s 內，附冪等驗證
- [ ] #2 live-reading 測試 hook 模式隔離：governance live 面測試在 PRE_COMMIT=1（hook 自帶 env）時 skip/fixture-only；live drift 偵測職責歸 installer --check＋launchd monitor 日頻（職責歸位明文）
- [ ] #3 card-WT path 錨定修復（AIR-116 follow-up）：governance check 期望路徑錨定問題——card WT 跑 --check 的系統性假紅消除（muse source.path 指非 canonical 類假漂移）
- [ ] #4 TDD：三項各有測試；primary＋card-WT 兩環境實跑對照（修前紅修後綠）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@f892c34〕

〔已決策勿重辯：①評估脈絡（0917 實證）：hook 三腿各有真價值（control-plane-guard 真抓過直落 main、py_compile 3.9 地板正確、無 CI 環境全量 pytest 定位站得住）——修缺陷非廢閘②fast path 判準＝git diff --cached --name-only 全屬 backlog/（特赦①②③場景的機械對應）③live-reading 隔離形態＝hook 設 PRE_COMMIT=1 env＋live 面測試 skipif——live drift 偵測單一歸宿＝installer --check＋monitor 日頻（不在 commit gate）④card-WT 錨定＝governance check 的期望路徑錨定 WT root 所致（muse source.path 指非 canonical 假漂移實證）——修為 repo-root 錨定或 WT 感知⑤逃生口疲勞論證：--no-verify 常態化＝閘門信用磨損，本卡就是把它收回例外⑥AIR-116 follow-up 併入（同一根因族）〕

範圍——改：.githooks/pre-commit（fast path＋PRE_COMMIT env）；tests/test_governance_check.py 等 live 面測試（skipif 標注）；governance/install.py 或 check 邏輯（path 錨定修復——實查錨點位置再動）。
明示不動：control-plane-guard 邏輯、py_compile 腿、monitor 日頻職責、特赦條款本身。
AC 見卡面四條。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
0918 擴卡（air-124 衝突事故吸訥）：④owning-line 單調性條文進 root AGENTS.md git 慣例（他人 merge 已進 owning line＝既成事實，平行 session 禁 reset/revert/stash-restore 移除；衝突停寫交裁決、forward commit 收斂——codex collision verdict 條文級一句）⑤雙層機械防線：.git/card-leases/<卡id> durable claim（wt-open 原子認領、已有 active lease 硬擋）＋pre-commit lease guard（wt-identity 對不上 active lease 拒 commit——抓手建 WT 繞道）⑥③（card-WT path 錨定）大部分已由 air-110 branch 的 F-5 修復解決（_group_scripts REPO_ROOT 化、904 passed 零假漂移）——air-110 收線後本項轉為驗證殘留（monitor live 面等）。
<!-- SECTION:NOTES:END -->
