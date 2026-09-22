---
harness-scope: neutral
---

# Model Routing（work unit → candidate → dispatch）

subagent 的 model/effort 由 work unit 的能力需求決定，不依主 session 模型。正式 resolver＝**model-routing skill 的 instruction protocol**（glossary／WorkUnitContract schema／precedence 七步／輸出契約——派工前必載）；穩定供給事實單一源＝`skills/model-routing/catalog.toml`（ModelIdentity／DispatchBinding／qualification；`sync_agents.py` loader 驗 schema）。

## precedence（always-on 骨架；全協議在 skill）

WorkUnitContract → qualification/judgment/capability hard filter → binding/carrier compatibility → availability tri-state → ArcOverride constraint → RoutingPolicy soft ranking → DispatchPlan（無單一合格 candidate＝declared decomposition 或 no-candidate）。

## hard invariants（違反＝路由錯誤，load 與處置 fail loud；全細節＝skill protocol）

- **no-silent-downgrade**：無合格 candidate 顯性 no-candidate/escalation；靜默換 model／降 effort／棄審禁用，降級必顯式記錄。
- **token provenance**：wire token 帶 kind，native/alias/slug 分欄禁混型；bridge/prose 委派一律 provider native ID。
- **effective effort**：candidate 四元組；effort 無法確認僅 conditional、不滿足 decision gate；effort 不補 qualification。
- **model fact single source**：identity/binding/capability/qualification 只住 catalog；rule／workflow／模板禁雙寫（parity gate＝`sync_agents.py --check`）。
- volatile state（訂閱/quota/availability）不住 catalog——dispatch 前由 spine/probe 形成 AvailabilitySnapshot；stale/unknown≠available。

external-runtime（family 軸）委派、收法、定向接續前必載 model-routing skill；external-runtime policy 不擴充本檔詞彙；工單禁再委派時載 skill 不等於自行 spawn。
