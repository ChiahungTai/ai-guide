---
name: air-26-push-collection
description: AIR-26 委派收法 push 化全弧終結——三層文檔＋範本預載＋POC 雙腿；AIR-21 附帶結案；殘餘 commit 待確認；grok W605 已結
metadata:
  node_type: memory
  type: project
  originSessionId: sess_f7c5d96f-b42e-464c-b528-2888a526f654
---

AIR-26（external-runtime 委派收法 push 化）2026-09-05 **全弧終結**：EP 定稿（10 findings 審查折入）→ flash agent implement（user 切 session flash＋unpinned general-purpose 繼承）→ diff 審查 2 P1 修復 → settlement（AIR-26 結案 Done、EP 歸檔 `ai-analysis/_tasks/_archived/09-05-external-runtime-push-collection/`、badge ✅）→ post-build（殼 hook 2 實作章節、docs 鏈、lint）→ **commit 提案待 user 確認**（10 檔 pathspec；排除平行 `impl-flash.md`）。

- **落地物**：S1 三層文檔——`agents/AGENTS.md` dispatch face 與收法段＋三態表 row-2、`skills/model-routing/SKILL.md`「完成回報收法」決策樹、`rules/model-routing.md` pointer（`deploy_agents.py` 三端 rg 驗證 3/3）；S2——`hooks/zcode-registration.json` 範本預載 muse/codex SessionEnd 條目（grok 註解待裝）＋`hooks/AGENTS.md` 落差記錄（config 不 merge——ZCode 無 SessionEnd）
- **審查兩輪 12 findings 全閉環**：EP 審 10（P0＝muse 其實有 SessionEnd hook——宣稱「X 無 hook」前逐家 cat hooks.json；P1＝ZCode 無 SessionEnd 是 contracts.md 既有定案→S2 降級；grok 未安裝；wait 撞預設 timeout）＋diff 審 2 P1（**codex timeout 訊號家系**：到期＝正常 exit 0＋`waitTimedOut:true` 非 124、無 0=forever——`--timeout-ms 0` falsy 回落 4min；照 muse 語義操作 codex＝假成功，已家系拆分寫進全部文檔）
- **POC 雙腿實證**：sleep 90 背景 Bash exit→自動喚醒（harness 前提閉環）；muse review 真實委派（job-mtnnzoez-jp8nq6）阻塞至終局 exit 0、stdout＝verdict——**push 收法用它自己驗證了自己**（委派 1 發、等待 0 request）
- **AIR-21 附帶結案**（user 質疑「還在 todo」觸發重讀驗收條款）：steps-1 探針 job L4 三路徑（短 wait 撞 running＝exit 124／長 wait 阻塞終局＝exit 0＋final JSON／既有 tests fail 0）；測試債（wait 零覆蓋）記 [[muse-code-cli-facts]]，補測試帶 muse-plugin-cc repo session
- **工單設計模式（可複用）**：POC 兩腿（零成本 probe 必跑＋真實腿 gate on setup.json green、subagent 禁自跑 setup＝計費判斷不下沉）；subagent 不能再 spawn → Agent Review/judge 留主 session、settlement 切 SendMessage resume 同 agent（單一寫入者）；平行 session 檔案明寫禁碰禁 add；agent 止於完成報告、commit 紅線留 user
- **殘餘**：①commit 待 user 確認 ②archify 決策樹圖（archify-gen 已入 registry，新 session spawn；產出換殼 s2 槽位）③W605＝AIR-25 已 commit 的 `block-memory-index-write.py:13`（regex `\s` escape，一行可修）④grok plugin 未安裝（ZCode UI 手動）⑤implement 5a docs-mode 漏項型：`skills/CLAUDE.md` 索引行漏「收法」——post-build metadata-sync 抓到已補
- 決策細節（push 優先／interval 階梯 YAGNI 但 timeout 面要管／S2 降級）勿重辯——單一源在 EP「已決策」段，機制對照見 [[external-runtime-delegation-family]]；flash 分工實證見 [[flash-forensic-0905]]
