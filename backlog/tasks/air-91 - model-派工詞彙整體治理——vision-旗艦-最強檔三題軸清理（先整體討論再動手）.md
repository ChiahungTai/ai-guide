---
id: AIR-91
title: 依工作階段能力自動選擇合適模型
status: Done
assignee: []
created_date: '2026-09-14 08:36'
updated_date: '2026-09-15 14:30'
labels: []
dependencies: []
references:
  - ai-analysis/_tasks/done/09-15-model-capability-routing/ep.md
  - ai-analysis/_tasks/done/09-15-model-capability-routing/index.html
ordinal: 77000
---

## Final Summary

使用者行為：呼叫 execution-plan／implement／judge-review／post-build 時，系統依每階段 WorkUnitContract（Role／authority／judgment floor／qualification／capabilities）自動解析候選（catalog 供給×presets 部署×availability snapshot），判斷密集位不再被座位或額度靜默降級、機械位不浪費 decision 檔——全程一命令入口。

落地：S1 catalog.toml＋resolver protocol；S2 presets.toml＋projection 等價切換（9-agent pins 逐 byte 不變）；S3 十二檔 work-unit doctrine＋accepted-EP 硬閘門＋視覺證據 envelope；S4 manifest＋doctrine gate＋導航收斂。驗證：每段 scoped judge（修補全落地）＋全套 510 tests＋行為實驗 30/30 PASS 零 regression＋外部 review 三腿（codex×2 零 finding、muse 5 findings 全 ✅ apply）＋三 harness deploy 完成＋fresh-load 驗證。殘項（後續卡候選）：effort-domain 機械 parity gate、inherit pseudo-binding 正式化、muse bundle 89% 瘦身。

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
讓 execution-plan、implement、judge-review、post-build 等工作流依每個階段真正需要的能力自動選模型，使用者只需啟動原本的工作流。影像能力、判斷能力、provider 特性與個人方案分開管理，避免用單一強弱檔位誤判模型。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## 工單身份

- baseline：`ai-guide@df3741b81e90dad01ed30fb383750ad55630998d`
- EP：`ai-analysis/_tasks/done/09-15-model-capability-routing/ep.md`
- 背景材料：`ai-analysis/reports/2026-09-14-sub-model-marshal-cross-consult.md`、`ai-analysis/reports/2026-09-14-sub-model-marshal-cross-consult-圖解說明.md`

## 目標

把現行 `role → full/lite/vision → model` 改造成下列解析鏈，並維持使用者的一命令入口：

`workflow phase → WorkUnitContract → model identity × dispatch binding × effective effort → runtime compatibility → availability → override / policy → DispatchPlan → carrier`

工作流負責何時推進，Role 定義責任與裁決權，model resolver 選擇誰執行，agent／main session／bridge 只代表執行載體。

## Use Cases

1. 使用者只呼叫 execution-plan、implement、judge-review、post-build，工作流按 phase 自動派工。
2. EP synthesis、judge、重大架構裁決等判斷密集工作只由已 qualification 的 decision-grade model 執行，禁止因額度不足靜默降級。
3. 已有自足 EP 的實作可交 execution-grade model；遇規格衝突、invariant、跨邊界決策或反覆失敗時升級。
4. 小型查詢、證據蒐集與機械驗證可平行派工，但只產 evidence，不取得最終裁決權。
5. 重要審查可要求不同 provider family 提供獨立意見，最終仍由 decision-grade Arbiter 裁決。
6. 原生影像是獨立 capability；模型可同時是 execution-grade 且 visual-qualified。
7. quota、帳號、provider 或 runtime 不可用時，只能換成仍滿足硬性能力要求的候選者，所有降級須可見。
8. 使用者顯式指定 model／provider／family 時優先；不可用時回報，不得暗換。

## 已決策勿重辯

- 不新增「最強檔」tier；ModelCatalog 只記錄 model supply、binding 與各 workload 的 qualification，不建立單一綜合智力排行榜，也不吸收 Role、workflow demand 或 registry preset。
- reasoning requirement 與 capability flags 拆軸；`native_vision` 不再與 `decision/execution` 放在同一枚舉。
- GLM Flash 的原生影像能力以 user-observed、visual-qualified 記錄；此資格與其一般判斷檔位無關。
- GLM 5.3、ChatGPT Web High、Sol medium-high、Astra、Opus、Fabel 列為 EP synthesis／judge 的 user-qualified 候選；Muse Spark 1.3 暫列 conditional，須保留 evidence status。
- 高推理＋影像沒有單一合格模型時，接受兩段式 fallback：visual-qualified model 觀察原圖並輸出 grounded observations，再由 decision-grade model 裁決；結果必標示 Arbiter 未直接看原圖，不宣稱與單模型原生視覺裁決等價。
- Composite workflow skill 承擔 Marshal 責任；不新增 Marshal skill 或 Marshal agent。Marshal 只決定何時推進與升級，不直接選 model、不取代 Arbiter。
- Reviewer 只有 findings／意見權；Arbiter 才有採納、拒絕、需確認的裁決權。
- Subagent 不等於 Role。Role 只由 WorkUnitContract 指派；ExecutionPreset 只描述 tools、權限、sandbox、background 與 default binding。第一階段允許保留既有 registry slug 作 compatibility adapter，避免為詞彙重構製造不必要的 runtime 破壞。
- ModelIdentity、DispatchBinding 與 effective effort 合起來才是一個可評估候選者；provider-native ID、harness alias 與 carrier slug 分欄保存，不得混作單一 model ID。
- qualification 的 `status` 與 `evidence_source` 分欄；`conditional` 是資格狀態，`user_observed` 是證據來源，availability 不屬於任一欄。
- resolver 是 `model-routing` skill 的 instruction protocol；`sync_agents.py` 只做 catalog／preset 的機械驗證與 registry projection，不讀個人 memory、不執行即時 fallback。
- ai-guide 保存穩定能力契約、qualification、provider/runtime 機制與 fallback policy；個人訂閱、帳號、quota、reset 與當弧偏好留在 memory／spine。
- 遷移採行為等價優先：既有常用 routing 結果與 generated registry pins 不因拆軸意外改變；新增的兩段式 visual fallback 與顯性 dispatch evidence 除外。

## 能力契約

每個 WorkUnitContract 至少聲明：

- `qualification`：如 `ep_synthesis`、`adjudication`、`implement_from_accepted_ep`、`evidence_retrieval`、`review_findings`、`visual_observation`
- `judgment_floor`：`decision` 或 `execution`
- `capabilities`：硬性能力 flags，首個正式 flag 為 `native_vision`
- `authority`：evidence、findings、apply、final disposition
- `surface`：read/write、tool、workspace、context／payload 限制
- `independence`：`kind`、`relative_to`、`required` 與缺場 fallback
- `escalation`：遇到哪類新判斷時停止本腿並升級

availability、latency、quota、成本與偏好只在滿足硬性要求的候選者之間排序，不得降低 capability contract。

視覺 direct path 同時要求 ModelIdentity 的 `native_vision` 與 DispatchBinding 的 `image_transport`；只有 dispatcher 的 source-delivery receipt 能證明 Arbiter 真的取得原圖。

## 路由順序

1. Workflow phase 產生 WorkUnitContract，包括 Role、authority、qualification、judgment floor、capabilities、surface、independence 與 escalation。
2. 依 qualification、judgment floor、capabilities 與 authority hard-filter ModelCatalog；不合格者不可由高 effort 補成合格。
3. 展開 DispatchBinding 並檢查 carrier／surface／image transport／effective effort 的 runtime compatibility。
4. 套用 `available/unavailable/unknown` snapshot；unknown 必須 probe 或顯性 no-candidate。
5. 使用者覆寫只約束或提高仍相容候選者的排序；指定不合格或不可用候選者時零 dispatch 並回報，不暗換。
6. RoutingPolicy 在剩餘集合排序，形成 main session、registry preset 或 bridge 的 DispatchPlan。
7. 每個 work unit 輸出 DispatchTrace；候選耗盡時 fail loud，或只採 WorkUnitContract 已允許的 decomposition。

## 範圍

### In scope

- `rules/model-routing.md` 的 always-on 路由骨架與硬性 invariant。
- `skills/model-routing/SKILL.md` 的 requirement schema、model capability／qualification catalog、provider/runtime traits、availability pointer、resolver 與 fallback。
- execution-plan、implement、judge-review、post-build 的 phase capability declaration 與 escalation 條件。
- agent-workflow、agents/AGENTS.md、agents authoring／projection 語義，以及 `scripts/sync_agents.py` 的 requirement/capability 解析與 parity。
- generated ZCode／Claude registries、`skills/CLAUDE.md`、root／rules／agents 導航與 single-source checks。
- 既有 `cr-research` full/lite 文件 drift 一併收斂。

### Out of scope

- 改動 provider 帳號、訂閱或 quota。
- 建立跨 provider 公開 benchmark 或聲稱未實測的模型優劣。
- 修改 delegate-bridge transport protocol。
- 新增 Marshal agent、Marshal skill 或另一套 workflow engine。
- 因詞彙重構任意更換目前已驗證的預設 model pin。

## 驗收邊界

- supply catalog、workflow demand、ExecutionPreset 與 generated projection 各自只有一個 owner；未知 requirement、capability、binding、qualification 或缺失 pin fail loud。
- vision-review 能表達 `judgment_floor=execution + native_vision`，解析結果仍為目前 visual-qualified model。
- decision-grade work unit 不因 quota、provider failure 或高 effort 配置降成 execution-grade model。
- 兩段式 visual fallback 保留 observation provenance、不確定項與 Arbiter 未直接看圖標記。
- workflow dispatch preview 至少能回答 work unit、Role/authority、能力需求、model identity/binding、requested/effective effort、carrier、override、attempts 與是否 fallback。
- agent authoring source 不直接寫 provider model ID；generated registry 的 model pin 由 resolver/projection policy 產生。
- repo instruction、parser、generator、測試與部署 bundle 無 `full/lite/vision` 舊單軸語義殘留；合法歷史報告不改，只排除出 current-doctrine gate。
<!-- SECTION:PLAN:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 WorkUnitContract 已拆分 qualification、judgment floor、capabilities、authority、surface、independence 與 escalation；candidate 明確包含 model identity、binding 與 effective effort
- [ ] #2 execution-plan、implement、judge-review、post-build 已按 phase 聲明需求與升級條件，使用者入口仍是一個 workflow 命令
- [ ] #3 ModelCatalog 只記 supply/binding/qualification，status 與 evidence source 分欄；個人方案和即時 availability 仍只住 memory／spine
- [ ] #4 Marshal／Role／Arbiter／execution profile／model／provider／carrier 邊界已在單一來源定義，未新增 Marshal agent 或 skill
- [ ] #5 高推理＋影像無單一合格模型時，兩段式 fallback 保留 grounded observation provenance 與非等價標記
- [ ] #6 ExecutionPreset 不含 Role／demand，sync_agents projection、generated registries、single-source guards 與相關 tests 已支援拆軸且未知值 fail loud
- [ ] #7 既有 routing 行為與 pins 經 golden/parity probe 證明無意外改變，cr-research drift 與 current-doctrine 舊語義殘留已清除
- [ ] #8 instruction behavior experiments、consumer smoke、targeted tests、sync_agents --check/--map 與 consistency 全部通過；deploy 前已展示所有 target diff/hash 並另取明確授權
<!-- AC:END -->
