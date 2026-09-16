---
id: AIR-43
title: model 詞彙治理——flash 去階層化、vision＝支援影像的 model、full-tier 旗艦釘選（inherit 洞）
status: Done
assignee: []
created_date: '2026-09-07 23:36'
updated_date: '2026-09-08 00:50'
labels:
  - governance
  - agents
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/_archived/09-08-model-vocab-governance/ep.md
  - ai-analysis/_tasks/_archived/09-08-model-vocab-governance/ep.md
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔baseline：ai-rules 5c7c7d9＋未 commit 詞彙清理（working tree 13 檔）〕〔已決策勿重辯：①flash 僅作模型專名（glm-5.3-flash／GLM-5.3-Flash 全名形態），tier 詞彙＝full（旗艦）／lite（一般）／vision（影像）——非每家都有 flash 版本，flash 不當階層詞；②vision tier＝「支援影像的 model」（能力軸非強度軸；現值 glm-5.3-flash 因原生多模，非因 lite——ZCode 文檔 configuration.md 佐證）；③full-tier 旗艦保障——「inherit 主 session」隱含主 session＝旗艦假設是洞（主 session 可為 flash；unpinned subagent 跟 spawning session 模型走），registry 需支援旗艦釘選（方向＝ZCODE_PINS 增 full→glm-5.3；wire 解析首例待實證）；④判斷密集位（judge／EP 規劃）不可降——AIR-24 不變〕〔驗收：裸 flash 殘留掃描＝0（排除模型全名／歸檔／ref-docs／memory 條目實名引用）；vision 定義與 full-tier 釘選落地＋sync_agents parity 綠＋tests 綠；full 釘選後 spawn 遙測 per-message modelID＝glm-5.3 實證；EP 歸檔任務家〕。詞彙清理（impl-flash→impl-lite、flash 分工律→lite 分工律、dispatch 簡稱全名化、vision 定義句）已落地 working tree 未 commit——EP 涵蓋 commit 承接；殘餘：ui-visual-verify flash lane 改名（建議 visual-shots lane，對齊 mosaic env flag MOSAIC_UI_VISUAL_SHOTS）待 user 拍板。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 裸 flash 殘留掃描 0；sync_agents --check 綠；pytest tests/test_sync_agents.py 綠；full 釘選 spawn 遙測歸因實證；EP 產出
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
S1 ✅ 627dd67＋S2 ✅ 12a5673（tests 31／hook 202）＋雙路審查綠（lite-verify 8/8、muse accept）；S3 待新 session（快照制，接指尖＝EP S3 段）、S4 待 U3；詳 EP 進度結算節

S3 ✅ 首例實證（zcode-code-reviewer model_id=glm-5.3 小寫 pin 達 wire、variant=max）＋S4 ✅ visual-shots lane（兩 repo 7 處）——S1-S4 全畢，走 S5 結案
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
模型詞彙治理定版——flash 去階層化＋vision=支援影像的 model＋full-tier 旗艦釘選 glm-5.3（wire 首例實證）＋visual-shots lane；四 commits 627dd67/12a5673/fb60628/8c98374
<!-- SECTION:FINAL_SUMMARY:END -->
