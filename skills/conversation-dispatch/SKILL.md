---
name: conversation-dispatch
description: "與 user 對話討論期間產生查資料、盤點、機械驗證、背景研究等查證需求時載入——判斷該查證是否外派 sub agent 背景跑，主 agent 保持討論座席、不需 user 指派。觸發詞：主動派工、討論座席、查證外派、背景研究、邊聊邊查、外派查證、派 sub agent 查。內容：每查證問句一次的派/不派判準表（heuristic 非 normative，正表＋負空間等重）、spawn prompt 模板（WorkUnitContext：objective/constraints/relevant_files/expected_output，不倒整段對話）、回報契約（結論＋path:line 逐字錨點＋未驗項分列）、額度同意邊界（唯讀 in-harness 自主派、bridge/external-runtime 必先問 user）；spawn 機械與路由歸 agent-workflow／model-routing，本 skill 不重複。"
when_to_use: "Fires when a verification need (查資料/盤點/機械驗證/背景研究) appears mid-conversation and the main session should stay in the discussion seat — decide per-question dispatch vs direct query."
---

# Conversation Dispatch — 會話主動派工判準

> 分工：本 skill 管「**會話何時派**」（dispatch policy）；「怎麼安全 spawn」歸 [agent-workflow](../agent-workflow/SKILL.md)、「派給誰（model/role 解析）」歸 [model-routing](../model-routing/SKILL.md)——機械與路由全引用，零拷貝。

## 模組定位

與 user 對話討論期間，查證／盤點／機械驗證類打雜活自動外派 sub agent 背景跑，主 agent 保持討論座席專心判讀與裁決。

邊界（不做什麼）：

- session 級自主模式（無人值守整段開發流程）＝ [deep-work](../deep-work/SKILL.md)——本 skill 是會話內逐問句的派工判準，非 session 駐留態
- 各 workflow 的 demand 判定唯一源＝owning workflow rows（AIR-91）——本表是會話場景的 heuristic 預設，與 owning rows 衝突時以後者為準

## 觸發情境

- 與 user 討論中出現查證需求（查資料、盤點、機械驗證、背景研究）——user 未指派也主動判斷是否外派
- 判斷粒度＝**每查證問句判一次**（不是進入一次就整段 session 都外派）；skill 載入後 session 內常駐，後續問句逐次套判準表

**觸發路徑矩陣（per-harness，2026-09-16 activation 實證）**——ZCode：available-skills 注入僅 name＋path、desc 不進模型決策面（ai-analysis/_tasks/09-16-conversation-dispatch/activation-results.md 取證），主觸發路徑＝rule 行為錨（rules/context-management.md「會話查證外派」句）＋明示 invoke；CC：desc 觸發未測。本表 per-harness 差異變更時更新。

## 判準表（heuristic 預設——非 normative）

> 正表與負空間等重——**先查負空間（不派），再查正表（派給誰）**。role 名引用 registry，model pin 值不在此重抄（查 [model-routing](../model-routing/SKILL.md)）。

### 負空間（不外派——主 session 直做）

| 訊號 | 處置 |
|---|---|
| 查證範圍 ≤2 檔且路徑已知 | 直接 Read/rg——外派開銷（延遲＋額度）大於收益 |
| 結果是當前步驟立即依賴 | 直查；真要外派僅限 <30s 前台 probe（機械規範見 [agent-workflow](../agent-workflow/SKILL.md)「Spawn 預設背景」） |
| 判讀、裁決、方向決策、方案取捨 | 主 session 職責——收集/判讀分離，研究腿不替主 session 做決策 |
| 寫入類工作（改檔、commit、建卡） | 不屬會話查證外派——走既有 workflow（[implement](../implement/SKILL.md) 等） |

### 正表（外派——唯讀＋背景）

| 查證問句形態 | 外派對象 | 備註 |
|---|---|---|
| 廣度探索（多檔掃描、「哪些/哪裡」類） | 內建 `Explore`（繼承主 session 模型＝唯讀探察正確形態） | spawn 型別分流：唯讀探察用 Explore（以主 session 所在 tier 查 model-routing 並發表） |
| 機械對帳（rg 清點、diff 對照、殘留掃描） | registry 角色 `lite-verify` | lite 機械必 registry 角色——內建型別無 pin＝旗艦燒機械段（AIR-50） |
| 逐字規格查詢（API 簽名、條文原文、參數表） | registry 角色 `spec-miner` | |
| 多源交叉查證（db/git/log/memory/cr 多軸） | registry 角色 `cross-verify-investigator` | |

spawn 前機械確認、並發上限、prompt 注入清單全按 [agent-workflow](../agent-workflow/SKILL.md) spawn 自檢清單；model/effort 解析按 [model-routing](../model-routing/SKILL.md)。

## spawn prompt 模板（WorkUnitContext）

只給工作單元所需最小 context，**不倒整段對話**——對話歷史不進 spawn prompt：

```
objective: <一句話查證目標——回答什麼問題>
constraints: <唯讀紅線＋工具紀律摘要（rg/fd 禁 grep/find 等——注入清單源＝agent-workflow spawn 自檢清單與 rules-reminder 摘要項）＋禁再委派句；查證腿唯讀工具面優先；載體無法保證唯讀時，工單明示殘餘風險>
relevant_files: <已知路徑清單；無則寫「無——由你定位」>
expected_output: 結論＋每條結論附 path:line 逐字錨點＋未驗項分列（unverified＝查了但證據不足；not-found＝找不到）
```

- constraints 必含**禁再委派句**——查證腿不得自行轉包 bridge／external runtime（否則下方同意邊界被繞過）
- expected_output 即回報契約：**結論＋path:line 逐字錨點＋未驗項分列**；free-text 回報、不強制 nested schema（複雜 schema 對原料型產出＝retry-exhausted 反模式，schema 嚴格度表見 [agent-workflow](../agent-workflow/SKILL.md)）
- 收集/判讀分離：研究腿只回 evidence 與錨點，不做 disposition

## 回收驗收（主 session 義務）

1. 背景回收：spawn 帶背景（機械規範見 [agent-workflow](../agent-workflow/SKILL.md)「Spawn 預設背景」）；回收前過 liveness checkpoint（同檔「背景 agent liveness」）
2. **錨點驗收**：逐條以 rg/Read 對 `path:line` 驗證逐字命中——錨點失效（行號漂移／內容不符）退回重取，**禁降級採用**（no-silent-downgrade 的會話層投影）
3. 回到討論座席：回報帶「影響什麼／未決什麼」——討論連續性不因派工中斷

## 額度同意邊界

- **唯讀＋in-harness＝可自主派**：Explore／registry roles 的唯讀查證不需 user 逐次批准（並發上限沿用 [model-routing](../model-routing/SKILL.md)「rate limit 與並發上限」表）
- **bridge／external-runtime（muse/codex/glm）＝必先問 user**：會話查證腿不得自主跨 external runtime——先向 user 提案獲同意再派（跨 runtime 額度消耗）
- 過度派工＝延遲＋額度雙燒：負空間命中即直查，不為「看起來勤勞」外派
