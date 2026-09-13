---
harness-scope: neutral
---

# Model Routing（角色 → tier → model 解析）

subagent 的 model/effort 由角色需求決定，不依主 session 模型。兩跳：本檔 role→tier，再查 **model-routing skill** 的 harness×provider 權威表；model 值只在 skill，ZCode pins 由 sync_agents 材料化。

tier 是 requirement 能力檔：full＝旗艦、vision＝影像、lite＝一般；旗艦資格、升降級、坐位與歸因見 skill。

model 詞彙（user 裁定）：prose/doctrine 與 bridge 委派一律 provider native ID；CC 詞彙（sonnet/opus）僅限 CC harness 自身接線；**禁 native＋alias 複合表達**（alias fail-closed）。詞彙表與 guard 見 model-routing skill（`bridge_model_vocab` invariant）。

## 角色 → tier

| 角色 | tier 與約束 |
|---|---|
| code-reviewer / primed / review command agent | lite 預設（user 拍板）；僅高保護面/跨邊界語義升 full，禁順手升級 |
| impl-lite | lite——規格化機械段執行；lite test 只算規格陳述，驗收/判斷密集位由主 session 補 |
| judge-review / execution-plan / post-build 編排 | full，不可條件降級（sycophancy 非 effort 可補） |
| spec-miner / lite-verify / cross-verify-investigator / render / cron 機械段 | lite；read-only 查證，缺源標 unverified |
| mem-distill | lite 寫入型；prompt 清單守範圍 |
| vision-review | vision；remote 先落地、CR per-session 可掛 |
| research / explore | 全域研究 full（v3.1 裁決，AIR-76）＋CR 白名單；內建 Explore fallback 繼承主模型 |
| harness 內建 general-purpose / Explore | 無 pin 繼承主模型；機械/lite 工作派 registry，禁假設內建預設便宜 |

## external-runtime routing（family 軸）

family＝GLM/muse/codex；profile＝implement/review/advisory——tier/family/profile 詞彙由本檔定義，其他載體只引用。**委派、收法、定向接續/fork 前必載 model-routing skill**（解析表、webgpt 約束、eligibility、bridge 契約、rate limit 全在 skill）。external-runtime policy 不擴充 tier/pin；工單禁再委派時載 skill 不等於自行 spawn。
