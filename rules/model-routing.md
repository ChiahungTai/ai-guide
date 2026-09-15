---
harness-scope: neutral
---

# Model Routing（work unit → candidate → dispatch）

subagent 的 model/effort 由 work unit 的能力需求決定，不依主 session 模型。正式 resolver＝**model-routing skill 的 instruction protocol**（glossary／WorkUnitContract schema／precedence 七步／輸出契約——派工前必載）；穩定供給事實單一源＝`skills/model-routing/catalog.toml`（ModelIdentity／DispatchBinding／qualification；`sync_agents.py` loader 驗 schema）——**rule 端不材料化 model 值**。

## precedence（always-on 骨架；全協議在 skill）

WorkUnitContract → qualification/judgment/capability hard filter → binding/carrier compatibility → availability tri-state → ArcOverride constraint → RoutingPolicy soft ranking → DispatchPlan（無單一合格 candidate＝declared decomposition 或 no-candidate）。

## hard invariants（違反＝路由錯誤，load 與處置 fail loud）

- **no-silent-downgrade**：judgment floor／capability hard requirement 無合格 candidate 時顯性 no-candidate／escalation；中途靜默換 model／降 effort／棄審禁用；任何降級必顯式記錄。
- **token provenance**：每個 wire token 帶 kind（provider native ID／harness alias／carrier slug），native／alias／slug 分欄禁混型、禁複合表達；prose／bridge 委派一律 provider native ID；token 值只在 catalog。
- **effective effort**：candidate＝(model identity, binding, requested effort, effective effort) 四元組；effective effort 無法確認時只能 conditional，不滿足 decision hard gate；effort 不能把未 qualification 的 candidate 補成 decision-qualified。
- **model fact single source**：model identity／binding／capability／qualification 只住 catalog（loader 驗證）；rule／workflow／模板禁雙寫（parity gate＝`sync_agents.py --check`）。
- volatile state（訂閱／quota／reset／帳號／即時 availability）不住 catalog／rule——每次 dispatch 前由 memory spine（`model-runtime-entitlements`）／probe 形成 AvailabilitySnapshot；stale／unknown 不得當 available。

external-runtime（family 軸）委派、收法、定向接續前必載 model-routing skill；external-runtime policy 不擴充本檔詞彙；工單禁再委派時載 skill 不等於自行 spawn。
