---
id: AIR-13
title: 統一 external-runtime subagent 架構定案＋首批委派工單
status: Done
assignee: []
created_date: '2026-09-03 04:31'
updated_date: '2026-09-03 13:27'
labels:
  - muse
  - model-routing
  - delegation
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-03-air13-unified-subagent-arch/index.html
  - ai-analysis/_tasks/_archived/09-03-air13-unified-subagent-arch/index.html
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
三層架構落地（09-03 三臭皮匠合併定案＋雙 ep-review 回寫）：①model-routing rule+skill 增 external-runtime routing 節——family 軸（GLM in-harness tiers 照舊；muse=實作／external second-opinion review／advisory 掃描，具視覺能力；codex=診斷 rescue；in-harness acceptance reviewer=GLM 主審委派工單）＋五條 eligibility gate＋reviewer 交接契約。model id 與容量數字單一源=skill 解析表（兩層契約：agents/zcode pin 為允許 materialization 須比對一致；rule/模板層 family/profile-only）。②registry 維持 thin forwarder（鑑=muse-plugin-cc FIX-S3-R2），特化長在 spawn flag profile（advisory/implement/review），落 agents/AGENTS.md 治理段。③工單模板 skills/_common/work-order.md——十節硬欄位：紅線首段（預設禁 git add/commit/push）／目標／baseline identity／必讀／已決策＋矛盾例外／範圍／工具接線／驗收（命令＋預期）／證據紀律＋PII 禁令／交付報告格式；foreign runtime 共用、派發一律背景跑。批次 triage：直做三小項（review-engine 背景句 pointer／python-standards 相對 import 行／at-skill miss 允許 no-op——現況已預跑全未承載）；委派兩項首用工單（受影響測試集三處〔錨 mosaic_alpha 9f151add、證據三級〕、post-build 四缺口）＋量測四欄；後議三項人先定邊界（四律九律／debugging+modern-cli 擇要／contracts.md muse 對照欄）。API-provider 議題歸 muse-plugin-cc 側。bridge roadmap 三條（--disable-write 暴露、-w worktree 暴露、task 類 job 加 export）記錄轉 muse-plugin-cc。已決策勿重辯：三層分工／thin forwarder／模板泛化／兩層契約（三臭皮匠共識＋雙 reviewer 修正＋user 裁定 09-03）。驗收：精確詞 rg 殘留零命中＋/consistency 過＋首批工單 reviewer record 在 EP＋consumer disposition table 13 檔＋deploy cmp＋90KiB gate 未爆。EP：ai-analysis/_tasks/09-03-air13-unified-subagent-arch/ep.md
<!-- SECTION:DESCRIPTION:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-09-03 13:27
---
【handoff 09-03】承接方：同 repo 未來 session。
■ 任務一句話：AIR-13 架構已落地（commit 47aa89d＋2a6f018，卡 Done）——接手標的是三件衍生：後議三項（人先定邊界才可成工單）、muse-plugin-cc roadmap 三條（跨 repo 僅記錄待轉達）、rules bundle 93% 瘦身觸發。
■ baseline：2a6f018。
■ 來源：ai-analysis/_tasks/_archived/09-03-air13-unified-subagent-arch/ep.md（EP Review 22+3 findings 全回寫＋4 條 reviewer record＋量測結算）；殼=index.html 同目錄。
■ 已決策（勿重辯）：三層分工（routing=model-routing／介面=agents registry／協議=work-order.md）；thin forwarder 不長特化 agent（鑑 FIX-S3-R2）；model id 兩層契約（解析表=唯一權威值；agents/zcode pin=允許 materialization）；muse dispatch 預設直呼 bridge CLI（wrapper=別名）；後議三項屬 viewport 軌道——AI 不自行裁定歸屬，等 user 邊界。
■ 下一步：①user 裁定後議三項→逐項建卡/工單（四律九律分拆〔落點方向：四律→execution-plan、九律分拆 acceptance-evidence 等，逐條歸屬待裁〕；debugging+modern-cli 擇要〔候選：背景長跑三態、git pathspec、Edit 邊界，user 選 2 條；VSCode 7 組已裁不建〕；contracts.md muse 對照欄〔硬約束：過時以原站為準＋每格附行號〕）②muse-plugin-cc 側開 session 承接 roadmap：bridge 暴露 --disable-write、-w worktree、task 類 job 加 muse export③下次加 rule 前先 bundle 瘦身（86,594B/90KiB gate 93%）。
■ 驗收：後議項落地時依 work-order.md 十節工單＋GLM acceptance reviewer 契約（無 record 不結卡）。
■ 承接不重做：架構三層與批次已入版——rg 'external-runtime' rules/model-routing.md 應命中；勿重落地。
---
<!-- COMMENTS:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
統一 external-runtime subagent 架構落地：三層（model-routing family 軸＋registry flag profile＋work-order 十節模板）＋eligibility gate＋reviewer 契約＋dispatch 三態；首批 muse 工單 4/4＋GLM reviewer 4/4 accept 零重工；量測結論=可擴大委派
<!-- SECTION:FINAL_SUMMARY:END -->
