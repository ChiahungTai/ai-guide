---
id: AIR-102
title: opencode 停用後的 ai-guide 殘留清掃——腳本死路徑＋四支 skill 文檔
status: To Do
assignee: []
created_date: '2026-09-16 00:03'
updated_date: '2026-09-16 00:03'
labels:
  - tooling
dependencies: []
ordinal: 87000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
opencode harness 已停用（user 2026-09-16 裁決），mosaic_alpha 側已清完；本卡清 ai-guide repo 內殘留：一支檢查腳本的死路徑＋四支 skill 文檔提及。鏡像目錄 ref-docs/harness/opencode/ 暫保留，刪否等 user 拍板（決策 7）。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide main 2d57c56。handoff 所寫 baseline 178c3d8＝排程健檢弧 commit（平行 session 落 air-99，未觸本卡五目標檔——git show --stat 已驗）〕
〔已決策勿重辯：①opencode 停用＝user 原話「opencode 目前沒在做，直接刪除相關的」（2026-09-16）；清單來源＝mosaic 側審查簡報 /Users/ctai/Github/mosaic_alpha/.agent-tmp/opencode-removal-brief.md（MOS-107 弧不涵蓋本卡）②部署目標 zcode/codex/muse 三家不動、deploy_agents.py 零改③skills 面為 symlink 直達（repo 改即生效）——handoff 的 sync_agents.py 部署步驟不適用（agents registry 與 skills 面無關）④決策 7：ref-docs/harness/opencode/ 鏡像（7.5MB）預設保留待 user 拍板——保留則 AGENTS.md:108 五家描述不動；拍板刪除另開後續⑤ai-analysis/reports 歷史文檔不動（歸檔歷史不修）〕
範圍五項：①skills/scan-project/scripts/check_single_source.py:96 檢查路徑改現行三目標（~/.zcode、~/.codex、~/.config/muse 的 AGENTS.md）＋有測試補一條②skills/context7/SKILL.md:21 移除 OpenCode、Codex/Muse 支援狀態照實標注（未驗證不升格）③skills/symbol-query-routing/SKILL.md:97 harness 對照表 OpenCode 刪列（擇一勿混）④skills/instruction-init/SKILL.md:111 改「（ZCode/Codex）」⑤skills/zcode-session-query/SKILL.md:5 when_to_use 移除 OpenCode
<!-- SECTION:PLAN:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 check_single_source.py 檢查路徑清單＝~/.zcode、~/.codex、~/.config/muse 三目標；腳本實跑綠（有測試則補一條）
- [ ] #2 四支 SKILL.md（context7／symbol-query-routing／instruction-init／zcode-session-query）OpenCode 引用清除或標 retired，不混用
- [ ] #3 驗收掃描：rg -il opencode --glob '!ref-docs/**' --glob '!backlog/**' --glob '!ai-analysis/**' --glob '!.git/**' → 僅 AGENTS.md（決策 7 保留時的五家鏡像描述句）
- [ ] #4 symlink 直達驗證：readlink ~/.zcode/skills 相關條目證據——repo 改即生效，無部署步驟
<!-- AC:END -->
