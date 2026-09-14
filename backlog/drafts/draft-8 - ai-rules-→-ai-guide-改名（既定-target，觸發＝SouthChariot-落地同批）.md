---
id: DRAFT-8
title: ai-rules → ai-guide 改名（既定 target，觸發＝SouthChariot 落地同批）
status: Draft
assignee: []
created_date: '2026-09-14 05:57'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔2026-09-14 觸發改寫〕user 拍板**即時執行**（codex 裁定零技術耦合——原「SouthChariot 落地同批」觸發條件作廢，local decision）；落地由正式任務卡承接，全表面調查＝`.agent-tmp/ai-guide-rename/investigation.md`。以下為原決策留檔（歷史不動）。

〔human-summary〕這張 draft 記錄一個已討論定案但「掛在外部事件上」的改名決策：ai-rules 未來改叫 ai-guide，等 SouthChariot（zcode-vscode 轉型）落地時同批執行。現在什麼都不用做。

〔決策〕**ai-rules → ai-guide 為既定 rename target**；觸發條件＝SouthChariot（zcode-vscode 轉型為跨 harness chat extension）落地，**同批執行**（同族命名分兩批會讓「指南車→指引」敘事只落地一半；但 SouthChariot 吸收 ai-lifecycle 後形態還會變，提前改是押注太早）。

〔三輪討論收斂（codex＋GLM-5.3 各三輪，2026-09-14）〕
- v1：不改為上、ai-policy 排除（policy=約束語義不涵蓋 79 skills 方法論主體）、ai-rules 已专名化
- v2：受眾分層命名原則（對外產品＝敘事名／內部基礎設施＝功能名——ai-rules 對機器受眾功能名是資產）；機械耦合密度論證（部署面/symlink 鏈/觀察池/spine）；mosaic 命名真因＝短路徑好打
- v3：**ai-guide 兩家一致升首選**——語義（guide 是 rules＋skills 的公共上義：style guide/user guide）＋體系（指南車→指引，同一語源雙語對仗；分工＝戰車載人對話、guide 指引行為方向）＋機械（8 字元同構）三軸同時成立

〔語義邊界（誠實記錄）〕hooks/muse-plugins/deploy 執行體不是「指引」——guide 罩不住這區（ai-rules 同樣罩不住，非退化）；codex 保留警告：guide 比 rules 稍弱化「塑造 agent 行為的系統」能力感。

〔遷移清單（觸發時照此執行）〕
1. GitHub rename（redirect 自動）＋各 clone remote 更新
2. `scripts/deploy_agents.py` 註釋與生成物引用
3. symlink 鏈：`~/.claude/CLAUDE.md`、`~/.claude/rules/`、`~/.codex/AGENTS.md`、`~/.config/muse/AGENTS.md` 等 deploy TARGETS
4. **硬編碼絕對路徑字串**（`/Users/ctai/Github/ai-rules`——memory 條目、AGENTS.md、跨 repo 文件大量在場；8 字元同構救不了純文字引用，rg 全掃逐項改）
5. CC 舊徑 `~/.claude/projects/-Users-ctai-Github-ai-rules/`（路徑即名）；觀察池路由；memory spine
6. 跨 repo AGENTS.md 活引用（ai-lifecycle/mosaic/delegate-bridge/SouthChariot——判準「今天新 session 讀到會不會誤導」）
7. **歷史文本不動**（AIR-* 卡/dossier/reports 舊稱保留，git 可考）；root AGENTS.md 加一行新舊名對照供 AI 檢索舊文本解引用

〔驗收〕活引用 rg 零殘留（歷史檔除外）＋四家 harness 部署驗證＋新舊名對照行在場。

〔關聯〕SouthChariot 材料＝`/Users/ctai/Github/zcode-vscode/ai-analysis/southchariot/`（HANDOFF.md/naming.md 八輪屍檔）；討論發起＝user 09-14。
<!-- SECTION:DESCRIPTION:END -->
