---
id: AIR-95
title: codex hook 控制面探測——同一套 AI 協作防護能否裝到 codex
status: To Do
assignee: []
created_date: '2026-09-15 06:12'
updated_date: '2026-09-16 07:17'
labels: []
dependencies: []
ordinal: 81000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
MOS-105 討論中發現 codex 官方文檔有 lifecycle hooks 機制（PreToolUse 等事件，文檔鏡像層證據、未 runtime 驗證）。這卡探測 codex hooks 在現行環境是否可用、契約形狀與 ZCode/muse 是否同構，評估把 MOS-105 的 bash-write-guard 防護移植過去的成本，供 user 決定要不要開移植卡。目前待開工（等 MOS-105 弧收斂後排序）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 codex hooks runtime 可用性判定（available／flagged／unavailable）附機械證據；stdin 契約形狀記錄並與 muse/ZCode 對照；移植成本評估結論（低中高＋理由）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide ba43ed7〕
〔實測與調查（0916，全證據在 .agent-tmp/air-95/）：①stdin 契約＝與 ZCode 同構（tool_name/command/exit 2 deny 逐欄文檔明文）②firing 實測（bridge codex-web，非 repo cwd）＝NOT_FIRING（ARM-1 過、ARM-2 未攔、無警告）③T1 canary 實驗（bypass trust＋本地 codex exec）＝hooks 確實觸發、stdin cmd 正規化為 command、多行 python -c 被 deny 且模型自述被攔改單行——機制端到端有效④T2（拿掉 bypass）＝canary 零新增、探針完整執行——**trust 閘靜默 skip 定罪**⑤成本：單次 ~80-90ms（直譯器啟動 ~76ms 支配）⑥卡面原觸發描述有誤：c-comment hook 攔多行 python -c 非 heredoc；heredoc 防護（block-python-file-write.py）未註冊 codex〕
〔已決策勿重辯：①信任語義＝trust hash 綁定語境未覆蓋 daemon 派工 context——bridge 派工的 hooks 靜默 skip、無警告可達 worker ②防護結論：codex 端防護現況＝實質未生效（註冊在場、firing 缺席）③本卡範圍＝取得 firing 證據＋根因定位（已完成）＋剩餘修復決策待 user〕
剩餘範圍（user 拍板後執行）：A．trust 註冊修復——codex app /hooks 重 approve 或 config 層信任（二擇一，修後以 T2 同協議複驗 canary 出現＋ARM-2 被攔）B．heredoc 防護缺口——block-python-file-write.py 是否補註冊 codex（含同 trust 問題）C．timeout 對齊——codex 條目補 timeout 10s（對齊 ZCode）或明示接受 600s
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔0916 實測結案記錄〕FIRING 實測 NOT_FIRING（firing.out）→T1 canary＝機制有效（FIRING_CONFIRMED 級：deny＋模型 workaround 行為正確）→T2＝trust skip 定罪。AC-2 firing 證據已產（.agent-tmp/air-95/＋~/.air-95-firing/）；AC stdin 對照已產（dossier §1）；AC-3 成本已產（80-90ms）。剩 A/B/C 三項決策待 user（見 Plan）。卡面原描述『bash-write-guard 移植評估』的觸發載體描述已修正（c-comment 攔多行 python -c 非 heredoc）。

〔0916 launcher 調查反轉（muse）〕launcher（codex-chatgpt-web）從不啟動 codex 進程——codex exec argv 由 delegate-bridge Rust carrier 組裝（rust/crates/bridge-families/src/codex.rs:126-194 build_args 硬編碼 exec --json --skip-git-repo-check，無 trust flag 無透傳）。注入點排序：①bridge build_args 加 --dangerously-bypass-hook-trust（自家 repo 最強升級存活）②零改碼＝EXPLICIT_PATH_ENV 指 shim（codex.rs:100-121 非空即權威）③requirements.toml managed hook（trusted by policy，路徑待驗）④/hooks 互動信任（止血，hook 一變即失效）⑤fork 改動＝構造不出 codex argv，排除。已驗：managed 區塊不隨升級重寫；非託管區安全。待實機：V1 launcher 自寫 hash codex 認不認、V3 requirements.toml 路徑。

〔0916 firing 終局證據〕連續 3 次 headless exec（無 bypass、非 repo cwd）均攔截成功——codex router log 逐字：ERROR codex_core::tools::router: Command blocked by PreToolUse hook: [Hook Blocked] python -c 命令含換行 + # 註解。先前 NOT_FIRING 實例（bridge job／T2）現已不可重現＝非確定性靜默 skip（transient），非確定性 trust 閘；監測方式＝本協議可隨時重跑。B（file-write 註冊＋timeout 10s）已落地 hooks.json；A（bridge 旗標）暫不需要——若靜默 skip 復發再議（contingency：bridge build_args 或 launcher 旗標）。
<!-- SECTION:NOTES:END -->
