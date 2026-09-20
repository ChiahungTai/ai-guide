# TC-4 dogfood 報告——timebox 模型端到端（真 subagent）

- date: 2026-09-20 22:4x local
- 載體: 真 subagent `agent_c4494d36-3066-476a-bf29-3fe3e52e26ec`（brief＝sleep 300 靜默阻塞）；registry `att-tc4-final`；watcher `HARNESS_WAITER_FREEZE_MIN=2`

## 結果：鏈路端到端走通至 STOP_INCOMPLETE（fail-closed 正確觸發＋一個真 finding）

| 步驟 | 結果 | 證據 |
|---|---|---|
| 註冊（S2 --register） | ✓ | createdAt generation anchor 自真 metadata 機械讀取 |
| T1-T3 輪詢 | ✓ | cycle 1-2 fresh（9.8s→69.8s，exec-lease-held telemetry 正確顯示不豁免） |
| T4 timebox 到（130s≥2m） | ✓ | bounded 收割（rollout tail 64KB＋sha256、exec size 0、metadata running、harvestPartial=true）→pending receipt（dedup）→exit 3 喚醒 |
| wake receipt | ✓ | `interventionPolicy=interactive`＋`retryBudget={attemptsUsed:1,budgetRemaining:1}`＋suggestedAction 五步明列（harvest-A→wake→terminal-recheck→branch→retry-gate） |
| 主 session TaskStop | ✓ | harness 級停止成功（stopped notification） |
| --verify | ⚠️ STOP_INCOMPLETE | reasons=`metadata-corrupt: 缺 createdAt`×2——**fail-closed 正確**（禁重派） |
| --harvest-delta | unknown 同因 | 一致 |

## 真 finding（本 dogfood 的產出）

**TaskStop 後的 stopped-state metadata schema 與 spawn 時不同——`createdAt` 欄位消失**（實測 stopped metadata 僅剩 agentId/childSessionId/completedAt/status）。S1 verifier 的 fail-closed（缺 createdAt＝corrupt 禁重派）正確擋下——但這代表 **TaskStop 後的任務永遠無法到達 STOP_CONFIRMED**（verifier 認證面對 stopped-metadata 恆 fail）。

修法方向（擇一，小改）：
- verifier 放寬：terminal face 只需 `status ∈ terminal 值域`＋childSessionId 匹配（createdAt 錨點已由 registry 承載，stop 後不必重驗）
- 或上游：harness stopped-rewrite 保留 createdAt（與 SC-166/M 尚未回報事項同族——harness schema 一致性）

## K1/Pivot 的活體再驗證

cycle 1-5 的 fresh＋cycle 6 all-terminal：**全程無 rollout 依賴**（本 agent 的 rollout 存在與否不影響判定——round 2 的 K1 收據案例為 rollout 不存在，本輪 rollout 存在但 timebox 照樣走）——timebox 模型對「有/無 rollout」兩種形態都正確工作。

## 殘留
- STOP verifier 放寬（上述）→ AIR-149 follow-up 小卡候補
- K3 註冊率 dogfood、24h 觀察 → S4 賸餘

## Round 3（post-pivot 修復後）——T4 timebox 全鏈活體驗證 ✓

真 dummy `agent_80943c91`（sleep 300 靜默阻塞）＋乾淨 registry＋`HARNESS_WAITER_FREEZE_MIN=2`：
- cycle 1-2 fresh（9.6s→69.6s，**exec-lease-held telemetry 正確顯示不豁免**——amendment 生效）
- cycle 3 **frozen 129.9s→timebox-wake exit 3**：receipt 含 policy=interactive（fail-safe 預設✓）、retryBudget{attemptsUsed:1}、harvestPartial=false、survivingHandles=[]、五步 suggestedAction
- **K1 pivot 活體再驗證**：rollout tail `absent:true` 正確處理（無 rollout 不妨礙 timebox）——有/無 rollout 兩形態都正確工作
- wake 後主 session TaskStop（真 task 級停止✓）→ --verify → STOP_INCOMPLETE（已知 quirk：TaskStop 重寫 metadata 掉 createdAt——verifier fail-closed 正確，修法方向見上節）
- 對照修復前：同場景 lease 豁免使 acc 每輪歸零、watcher 永遠 fresh——**amendment 的直接活體證據**
