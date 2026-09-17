---
id: AIR-120
title: check_single_source 健檢誤報修正——hook_registration 補 codex 註冊面＋skill allowlist 同步
status: To Do
assignee: []
created_date: '2026-09-17 08:51'
updated_date: '2026-09-17 08:51'
labels: []
dependencies: []
ordinal: 105000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
兩類既有誤報（0917 AIR-116 S6 收尾實跑發現，非該弧引入）：①hook_registration invariant 只認兩個註冊面（settings.json＝CC、governance/registrations/zcode.json＝ZCode），看不到 codex 註冊面（~/.codex/config.toml，模板 governance/registrations/codex.toml）→ codex_memory_path_deny.py 被誤報孤兒 CRITICAL（實際已註冊接線，AIR-100 落地）——checker 需補 TOML 註冊面解析；②skill_allowlist_coverage 報 4 支 skill（bridge-dispatch／conversation-dispatch／instruction-testing／tool-discipline）存在於 skills/ 但不在 settings.json allow-list——AIR-113 rename 後 allow-list 未同步新名，AI 呼叫時跳權限詢問。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【spec 要點（0917 AIR-116 收尾實證帶入）】①hook_registration 補 codex 面：registrations 清單加 governance/registrations/codex.toml＋live ~/.codex/config.toml；checker 需 TOML 解析＋group 級 wiring 抽取（event＋matcher＋script basename 三元組——可參考 install.py 的 codex_group_units/_codex_group_identity，唯讀 import 或等價實作）；現有 CC/ZCode 兩面檢查語義不變。②allowlist 同步：4 支 skill 補 Skill(<name>) 入 settings.json（或逐支裁決豁免並記理由）；settings.json 是 gitignored local-only（fresh clone 缺場 → 比照既有豁免語義）。③驗收：實跑 check_single_source 全綠（或僅剩真實 finding 逐條附證據）；既有 tests/test_check_single_source.py 補 codex 面測試。
<!-- SECTION:NOTES:END -->
