---
id: AIR-120
title: check_single_source 健檢誤報修正——hook_registration 補 codex 註冊面＋skill allowlist 同步
status: In Progress
assignee: []
created_date: '2026-09-17 08:51'
updated_date: '2026-09-17 13:30'
labels: []
dependencies: []
ordinal: 105000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
兩類既有誤報（0917 AIR-116 S6 收尾實跑發現，非該弧引入）：①hook_registration invariant 只認兩個註冊面（settings.json＝CC、governance/registrations/zcode.json＝ZCode），看不到 codex 註冊面（~/.codex/config.toml，模板 governance/registrations/codex.toml）→ codex_memory_path_deny.py 被誤報孤兒 CRITICAL（實際已註冊接線，AIR-100 落地）——checker 需補 TOML 註冊面解析；②skill_allowlist_coverage 報 4 支 skill（bridge-dispatch／conversation-dispatch／instruction-testing／tool-discipline）存在於 skills/ 但不在 settings.json allow-list——AIR-113 rename 後 allow-list 未同步新名，AI 呼叫時跳權限詢問。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@c2446dd〕

〔已決策勿重辯：①兩誤報皆 AIR-116 S6 實跑發現的機械 bug（desc 全文為準），非新設計——修 checker 不改安裝器②hook_registration 補第三註冊面：codex＝~/.codex/config.toml（模板 governance/registrations/codex.toml，已進 manifest）——checker 解析 TOML 註冊面後 codex_memory_path_deny.py 不再誤報孤兒③skill_allowlist 4 支＝AIR-113 rename 殘留（bridge-dispatch/conversation-dispatch/instruction-testing/tool-discipline）——settings.json allow-list 同步新名；settings.json 為 local-only（gitignored），同步後 rg 驗證四名在場＋舊名零殘留④修復後 check_single_source 對三註冊面全綠＝AC〕

範圍——改：check_single_source 所在 script（實查定位，大概率 scripts/ 或 skills/consistency/scripts/）＋settings.json（local）。明示不動：governance installer、registrations 模板、catalog。
AC：①checker 三註冊面（CC/ZCode/codex TOML）解析＋codex hook 零誤報②allowlist 四新名在場③check 全綠實跑證據④pytest 既有測試零回歸。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【spec 要點（0917 AIR-116 收尾實證帶入）】①hook_registration 補 codex 面：registrations 清單加 governance/registrations/codex.toml＋live ~/.codex/config.toml；checker 需 TOML 解析＋group 級 wiring 抽取（event＋matcher＋script basename 三元組——可參考 install.py 的 codex_group_units/_codex_group_identity，唯讀 import 或等價實作）；現有 CC/ZCode 兩面檢查語義不變。②allowlist 同步：4 支 skill 補 Skill(<name>) 入 settings.json（或逐支裁決豁免並記理由）；settings.json 是 gitignored local-only（fresh clone 缺場 → 比照既有豁免語義）。③驗收：實跑 check_single_source 全綠（或僅剩真實 finding 逐條附證據）；既有 tests/test_check_single_source.py 補 codex 面測試。
<!-- SECTION:NOTES:END -->
