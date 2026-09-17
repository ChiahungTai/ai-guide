---
id: AIR-119
title: 主鏈跳步機械閘——post-build receipt＋commit gate＋Stop hook 雙端即時攔截
status: In Progress
assignee: []
created_date: '2026-09-17 08:35'
updated_date: '2026-09-17 10:11'
labels: []
dependencies: []
references:
  - hooks/post-build-gate.py
ordinal: 104000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
implement build 收斂後直接停、跳過 /post-build——LLM 紀律失敗（0917 實例：三 commit 完即回報等 user）。落地機械閘兩件：A＝事後收口（/post-build 末尾寫 receipt＋/commit 新增階段 2.95 檢查 receipt）；B＝即時攔截（Stop hook 於卡 branch 且無有效 receipt 的 turn 結束 block 續跑——CC＋ZCode 雙端註冊）。豁免（窄、純機械）：branch=main；或 vs merge-base 改動全 .md（純文檔／卡務／排程 session）。ZCode Stop hook block 續跑已 POC 實證（0917——sentinel mtime＋reason 注入＋3 次上限，證據 .agent-tmp/stop-poc/）。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【spec gate——已決策勿重辯（0917 user 工單＋POC 實證）】baseline＝main@收線後 HEAD（開工重刷）。八點已決策：①問題＝implement 跳過 /post-build（0917 實例三 commit 即停）②ZCode Stop hook block 續跑已 POC（fire/block/reason 注入/#N 計數/上限 3——證據 .agent-tmp/stop-poc/ read-only 禁刪）③豁免＝branch main 或 vs merge-base 全 .md（純文檔／卡務／nightly 排程 commit 涵蓋）④ZCode 無 SessionEnd——B 只掛 Stop⑤A/B 共用判定函式單一源（hooks/post-build-gate.py：純機械 git＋檔案存在、<1s、內部錯誤 exit 0 fail-open、arm-gated 單發 self-limiting）⑥receipt＝.agent-tmp/post-build-receipts/<branch>.json（branch/head_sha/legs 結算/completed_at/report 指針；head≠HEAD＝stale 要求重跑；7 天清淤可接受）⑦/post-build 階段 6 末寫 receipt；/commit 階段 2.95（2.9 後）無 receipt→fail-loud 指引、stale→列差異⑧B 註冊 fold-in 序列保 AIR-116 byte-parity：先 live 註冊（ZCode hooks.events.Stop＋CC settings hooks.Stop，備份＋parse 驗證，ZCode 只動 hooks 子樹——或直接走 governance installer --surface hooks）→再更新 manifest [surfaces.hooks].scripts＋模板→installer --check 綠。已決策：live config 禁殘留 stop-hook-poc（已拆勿復原）。實作約束：動 skill 檔前載 instruction-writing；完成後 fresh-eyes 審查腿（gate 面＝非 lite）；建議 tier 一般以上。AC 草案：A＝docs-only 不擋／code 無 receipt fail-loud／有 receipt＋head 一致通過／stale 擋並列差異；B＝卡 branch 無 receipt turn 結束 block 一次（reason 可見）／post-build 後放行／main·docs-only·排程不觸發；CC＋ZCode 各一輪 live 驗證 receipt 附完成報告。同步點（muse 腿補抓）：implement SKILL.md 六處、handoff 承接面、blueprint workflow、guide bundle 側。
<!-- SECTION:NOTES:END -->
