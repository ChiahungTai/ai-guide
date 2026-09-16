---
name: quota-failover-policy
description: dispatch 政策（09-07 修訂）：額度現值 GLM+muse；實作預設 muse+flash；影像 flash；審查類 muse/flash 皆可；詳 skill dispatch 節
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_f748b62f-1779-46e9-9d95-4f8a68737f58
---

user 訂閱狀況異質（GLM/muse 額度足、codex 最少、Anthropic/xai 未訂閱）且每次耗用不同——dispatch 的正確主軸是 **harness（user 的開發入口）→ use case**，不是額度線、也不是單線 failover。

**Why（三連勘正軌跡）**：①初版寫「主力序 GLM→muse」單線 failover——muse 被降格成 GLM 撞 1308 的備援；user 勘正「Muse 應該在我要跨家族的審查時候先用…再好好想 uc」→②重寫按 UC 分派，但仍把「muse 實作」寫成「僅 user 點名的 bridge 委派選項」；user 再勘正「**如果我用 muse code 開發，這裡就是 muse 阿，這跟 harness 有關係，你這想錯了**，然後目前 glm 我通常用 5.3 主力，不是 flash，muse 是 1.3」→③定案 **harness 主軸**。兩個病根：ZCode 本位視角（把 user 直接在別的 harness 開發寫成 ZCode 的委派選項）＋model 精確度不足（GLM 主力＝**5.3 主 session**，flash 只是 lite 執行檔省成本層）。

**How to apply**：
- **harness 主軸**：ZCode 開發（日常）＝GLM 5.3 主 session（判斷/規劃/EP/judge）＋glm-5.3-flash lite subagent；**muse code 直用開發＝該弧主力 harness**（muse-spark-1.3 全棧，實作/審查都在裡面；repo AGENTS.md 會載入〔bridge log 實證〕，全域 guide 部署點未查證；**muse code 目前無法換其他模型——鎖 1.3，user 等 muse code 發展後再說**，屆時 meta 欄才有多檔次可言）
- **「muse 實作」兩型勿混**：user 直在 muse code 開發（harness 切換，主形態）≠ ZCode→bridge 委派（AIR-13 單批指示，[[reference_external-runtime-delegation-family]]）
- **跨家族審查（任一端要第二意見）→ 對側家族、muse 優先**（跨家族價值＝非 GLM 視角）；codex 與未訂閱家（Anthropic/xai）→ 僅 user 顯式指定（「codex sol max」式）。**無合法相異家族可自動選時（muse caller 未指定——僅剩 codex 而 explicit-only 不可被解析繞過）→ 停下要求 user 選擇**（09-06 拍板）：顯式指定 codex／明示接受同家族 degraded review（caller-harness full dual-context 承接＋記錄）二選一——**降級的選擇權在 user，禁解析層自選降級**（強於既有「降級必記錄」）；解析表落 model-routing review/advisory 條款
- **額度僅撞牆時用**：GLM 1308（錯誤含重置時間戳）→ muse 承接執行段；皆乾→`/at` 等 reset 或 user 裁定；降級必顯式記錄（AIR-13）。額度不降檔只換行（requirement 是任務性質；影像任務額度再緊不派非影像款）；大工單選 muse 是容量考量（codex 容量現值落 skill family 表，09-05 實值 258K——memory 不記現值）非額度
- **並發語義（09-05 user 裁定，AI 病根＝把「失敗→降」混成一團）**：**1308 usage limit 不是降並發信號**——窗口制，能用＝已重置，與並發數量無關（重置後照原並發跑）；**只有 429 rate limit 持續才降並發**（N→N/2→serialization），且降並發**不砍 dual-context**——fresh/primed 兩側用序列化保（一次跑一個但都跑），複雜任務不用 lens 數換速度。另一面：**external 委派（muse bridge 背景 Bash 直呼）不佔 in-harness agent 並發 slot**——不需要 GLM wrapper agent 包裹（user 顧慮「你這會佔一定 concurrent」；wrapper 僅 prompt 工程場景）；條文落 agent-workflow spawn 失敗階梯＋contract 表
- **CC harness 的 provider 綁定＝本機部署配置，非原生家**（09-05 user 確認勘誤）：本機 CC 掛 **GLM backend**（L4 實證 session 跑 glm-5.3）——10 role 在 CC 全可達的底層原因；原生家 Anthropic 未訂閱（user **之後視性價比評估**再決定訂閱，屆時 backend 可重配）。**CC 端 dispatch 用 CC 自己的模型詞彙**（user 勘正「在 cc 環境下就用 cc 的 model，不用太複雜」——AI 曾犯「直填 flash」越層：把 backend 事實洩進 dispatch 決策，破壞正交）：預設 inherit（named-agent 跟主 session 5.3）、lite 點名 **`sonnet` 別名**——落到哪顆是 env 映射層的事，dispatch 不綁實體 backend id。**lite 地板＝sonnet/terra 級**（user 09-05「haiku 跟 luna 基本上不會用」；ANCHOR_MODEL 三跳 flash→haiku→sonnet 定案）。**別名→GLM 映射實體＝`ai-rules/settings.json` env 的 `ANTHROPIC_DEFAULT_{HAIKU,SONNET,OPUS}_MODEL` 三鍵（user 自管，非 AI 改）**——語義陷阱：**sonnet 也指 flash 檔**（與 haiku 同層），CC 端 spawn "sonnet" 實為 lite/flash，非中檔；opus 指 glm-5.3（主 session 檔）——映射現值會隨世代漂，查該處不看記憶
- **家族指定的作用域＝external 委派位**（「muse post-build」語義追跡定案）：指定只改變 external review 那一段的家族，**不會把整條鏈 muse 化**——judge／編排／consistency／殼敘事等判斷密集位永遠主 session GLM 5.3（AIR-24；與 [[feedback_judge-review-stays-main-agent]] 同根：跨家族只用審查側不用裁決側）。鏈上一句話版：**GLM 5.3 做所有需要判斷的事、flash 做所有機械的事（vision 另按能力軸＝需支援影像的 model，09-08 勘正非 flash 附屬）、muse-spark-1.3 只在點名的 external 審查出場**；dual 時兩側 findings 都回 GLM judge 合併裁決、衝突標 conflict 不自行裁
- **政策現值單一源＝`skills/model-routing/SKILL.md`「dispatch 預設」節＋tier 表格標註**＋agents/AGENTS.md harness 軸 muse code 雙身分行——派發前查該節；memory 不複製現值；訂閱變了→user 說一聲只改該節＋格標註

**09-07 修訂（user 拍板「額度狀況要有固定記載處」）**：①**額度現值常態錨進 skill dispatch 節開頭行**（GLM＋muse 可用；codex 不派、未訂閱家禁派）——固定記載處＝skill（全域部署跨專案可見；memory 池 per-project），「memory 不複製現值」拍板維持；②**實作預設 muse**（重實作段 muse、lite 機械段 flash；CR 工具鏈 agent 同收斂）——推翻 09-05「muse 實作＝仍 user 點名」（[[reference_external-runtime-delegation-family]] 09-03「選項非預設」同步作廢）；③**影像（vision tier）現值＝flash**，muse --image 非路由；④其餘角色不變（inherit 主 model GLM 5.3）；⑤**審查類（ep-review／code-review 等 review agent 層）放寬 muse＋flash 皆可**（judge 裁決層不變，固定主 session）。

**09-08 增補（inherit 洞，user 攔下 EP dispatch 錯誤）**：「full tier＝inherit 主 session」**不是旗艦保證**——unpinned subagent 跟 spawning session 模型走，主 session 被切到 flash（手動省成本/切換）時判斷密集 dispatch 靜默拿到 lite 級（違 AIR-24）。派判斷密集任務前先確認主 session 當前模型；解法弧＝registry 旗艦釘選（ZCODE_PINS 增 full→glm-5.3；user 拍板「可以有使用旗艦模型的 agent」；AIR-43 進行中，詳 [[project_flash-vocab-audit-0908]]）。

與 [[feedback_harness-model-orthogonal-axes]]（三層結構第四次勘正即本次）同族；與 [[feedback_capability-tier-not-model-binding]]：dispatch 決策跟 harness＋任務性質走，不凍結進定義。
