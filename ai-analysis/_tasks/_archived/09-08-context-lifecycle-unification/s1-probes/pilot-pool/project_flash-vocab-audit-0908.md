---
name: project_flash-vocab-audit-0908
description: AIR-43 flash 詞彙治理弧終態—tier 定版（vision=支援影像的model）、full-tier 釘選 glm-5.3 已實證 wire、flash 僅存全名形態
metadata:
  node_type: memory
  type: project
  originSessionId: sess_505eb9a4-736e-4e30-b2d5-50cc545b0ad9
---

**終態（AIR-43 全段閉環，2026-09-08；過程與 commits 見 EP＋卡——`ai-analysis/_tasks/_archived/09-08-model-vocab-governance/`）**

- **詞彙定版**：flash 是 GLM 專屬產品名，不作階層詞（Anthropic=haiku、OpenAI=mini——非每家都有 flash 版）。tier 正式詞彙＝full（旗艦）／lite（一般）／vision（影像）。**vision＝「支援影像的 model」——能力軸非強度軸**（user 勘正「影像走 lite tier」：非所有 lite 款有多模；glm-5.3-flash 獲選因原生多模）。flash 合法形態僅模型全名（`glm-5.3-flash`／`GLM-5.3-Flash` 歷史指涉）＋三刻留（test_memory_lifecycle.py:114 memory 條目實名、backlog 歷史卡名、ref-docs／ai-analysis 歸檔豁免區）。測試截圖通道 lane 名＝**visual-shots lane**（對齊 mosaic env flag `MOSAIC_UI_VISUAL_SHOTS`——grep lane 名即得開關名）。
- **full-tier 旗艦釘選（inherit 洞修補）**：洞＝unpinned subagent 跟 spawning session 模型走（遙測實證 code-reviewer 曾跑 flash 392+107 requests——主 session 為 flash 時 full-tier 全漂移）；修法＝`ZCODE_PINS["full"]=(glm-5.3, high)`＋parity regex 擴 full。**wire 首例已實證**（S3 遙測 `zcode-code-reviewer` 小寫 `glm-5.3` 命中；variant=max＝thoughtLevel 定義值不達 wire 的 sticky 但書數據點）。CC 端**別名釘選已落地**（AIR-44 收束，`67c5836`：`CLAUDE_PINS={"full":"opus"}`＋`_ANTHROPIC_ALIAS_RE` parity guard＋TDD 32 tests）——**釘別名非釘 id＝provider 可攜**（user 09-08 確認：env 映射切回真 opus／接 fabel 端點時 alias 直接可用、免重釘；切換點單一＝env 映射表）。CC env 映射現值（定義源 `~/.claude/settings.json` `ANTHROPIC_DEFAULT_*`，z.ai 相容端點走 GLM 額度）：opus→glm-5.3[1m]、sonnet/haiku→glm-5.3-flash[1m]；lite/vision 維持省略 inherit。sticky flip DB 形態已跑（見 [[reference_zcode-platform-facts]]）；skill flag 表 drift B1 已當場修——7ad42c0。
- **教訓**：①registry 快照制——session 內 spawn 不到改名後的 agent 名（impl-lite 撞名實證），registry 改動驗證必須新 session；②EP 由 5.3 agent 撰寫＋不盲從條款（宣稱打包 C1-C7 逐項自驗、推翻附證據）產出品質高——可沿用形態；③終審驗收鏈（三方 findings→judge 回寫→muse 新 session 靠 EP 內 findings 表自足驗收回寫）值得沿用；④建卡 commit 前查 staged 區（git mv 殘留 rename 會被 scoped add 後的 commit 掃走——[[feedback_verify-wt-before-commit]]）。

相關：[[project_air-38-routing-feedback-tier]]（tier 詞彙源頭）、[[project_flash-forensic-0905]]（lite 分工律鑑識出處）、[[reference_zcode-platform-facts]]（wire 首例＋variant 詳實證）
