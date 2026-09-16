---
name: plugin-review-absorption-p1-p7
description: Anthropic plugin review 方法論吸收（P1-P6 採/P7 不採）——已隨 AIR-28 c83ddf4 落地（09-05）；證據釘 marketplace SHA
metadata:
  node_type: memory
  type: project
  originSessionId: sess_3380ab28-4197-4433-aa66-e2f54587b64b
---

反饋任務（mosaic session 09-05 交付）：吸收 Anthropic 官方 plugin 的 review 方法論 7 點進 ai-rules review 體系。**狀態＝AIR-28 EP S2 定稿版**（雙家族 review 後 judge 落點精化）：**P2 拆分流**——review-engine 只收「所有 review 命令都適用」條款（:11 收進判準），HIGH SIGNAL filter 屬 PR bug-review policy 落 code-review-and-quality／code-review（全域化會壓掉 ep-review/audit 的合法 Important/Suggestion——codex R4）＋補收漏掉的兩條（appears-bug-but-correct／quality 類僅 instruction 明示才報——後者本 repo load-bearing）；**P3 限縮措辭**——「All tools functional」不當 runtime fact（與 degraded contract 衝突），改「禁無目的 probe＋失敗走既有 [WARN]+fallback」；**P6 落點＝code-review-and-quality Correctness checklist 層**（lens 在 review-engine、checklist 屬 profile）；P1 併 lite-verify（口徑統一不另建 findings-verifier）；P4「最近者優先」標為本弧新決策；殘留掃描 pattern 擴五詞（+logForDebugging/logEvent）。教訓：user 對「P1-P7」標籤失憶（「這啥？」）——重提標籤必附一句內容摘要。

**證據源（pinned）**：marketplace clone `/Users/ctai/.claude/plugins/marketplaces/claude-code-plugins/` @ `d7dbd9a0`（已驗 == clone HEAD；日後 update 用 `git -C <clone> show d7dbd9a:<path>` 取回）。code-review plugin 保留 disabled（檔案在場可讀）、feedmob 已移除。

**逐點預判（裁決時直接用）**：
- **P1 per-issue 對抗驗證→採納分級形態**：Critical 維持 3-verifier quorum；B 模式 Important+ 補 **lite-verify 機械錨點驗證**（file:line/符號存在性，清單批次）——錨點屬實性（機械/lite）vs 裁決（judge/full）職責分離；不照抄 plugin 全量 per-issue spawn（成本爆炸）
- **P2 DO-NOT-FLAG 清單→採納**，落 review-engine 單一源；pre-existing 條對齊 mixed-tree 歸因分支（「不報為新引入」非全禁）；「linter 會抓的不報＋禁跑 linter」直接吸收
- **P3 preamble token 紀律→採納**（三行：工具皆可用禁測試/exploratory calls/每 call 有目的），落 review-engine spawn 模板
- **P4 指令檔適用範圍→採納**：只考慮同路徑或祖先路徑的 AGENTS.md、最近者優先——防 primed agent 拿上層規則審下層覆寫慣例的系統性誤報
- **P5 冗餘分流→採納（quorum 段細化註記）**：compliance＝recall 問題（冗餘有益）、judgment＝bias 問題（需 context 差異）——與「quorum 對共同盲點無效」不矛盾而是精化
- **P6 silent-failure 枚舉紀律→採納素材重寫、禁照抄**（殘留 errorIds.ts/Sentry/Statsig 內部引用）；錯誤處理點系統化枚舉（try/except/callback/fallback default/optional chaining/log-and-continue）×五維；diff 語義觸發＝六軸條件啟動同型
- **P7 type-design 四維評分→傾向不採**：1-10 自評＝被 Anthropic 自己演化掉的舊形態（信心分→對抗驗證）、與 arch-thinking contract slice 重疊；僅收 "invariants enforced only through documentation" 一句素材
- 考古加值：README↔實作 drift（信心分→per-issue 驗證演化史）＝acceptance-evidence「self-report 零獨立性」外部印證＋instruction-writing drift 反面教材

**對位**：P1/P3/P6 屬 agent 強化；P2/P4/P5 屬 review-engine/code-review skill 面；P1 分級驗證＝deepwork workflow 化的兩種 verify node 形態（見 [[reference_cc-workflow-model-zcode-absence]]）。

**同批已定案**：report shell flash 適用題（分工律首用）——組裝/餵料 flash、篩選/敘事 full、視覺 vision＝EP 已決策第 7 條（S4 承載：**殼宣稱只從機械底稿帶入**〔防 flash 文檔宣稱漂移弱面〕＋確定性再生 diff 當測試釘住等價物）。

**驗收**：每點裁決紀錄（採納＋落點 path／不採納＋理由）＋採納項 /sync-sources 綠；內容落 rules/ 時跑 deploy_agents.py。背景：ai-rules 機械證據層/dual-context/六軸判定全面領先 plugin 版（對比分析已完成勿重做）。

相關：[[project_flash-forensic-0905]]（分工律來源）、[[feedback_capability-tier-not-model-binding]]（能力檔語義）、[[reference_cc-workflow-model-zcode-absence]]（deepwork 化載體）
