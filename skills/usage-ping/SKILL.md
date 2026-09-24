---
name: usage-ping
description: "usage reset 探測叫醒 — 在估計的重置時間排 ping（one-shot 階梯：Claude Code 3 發；ZCode 單發——session 綁定限制），落地即確認配額回來；固定時刻制配額用網格模式 every Nh from HH:MM（recurring cron）。滾動窗口制（GLM 5 小時窗口類）無法自動輪詢——讀 provider UI 邊界重跑一次性，或無參數保底 now+301min（落地後重跑＝手動接力）。每個 trigger 最小 call 成本；只寫時間不帶任務（要接續工作用 /at）。觸發詞：叫醒、ping、配額重置、reset 探測、usage reset、5 小時窗口、滾動窗口"
when_to_use: "LLM provider usage reset 時間是估計值（一次性時刻或固定時刻週期）、只需要叫醒 LLM 確認配額（不接任務、最小 call 成本）時"
argument-hint: "HH:MM | every 5h from HH:MM"
allowed-tools: ["Bash", "CronCreate", "CronDelete", "CronList"]
---

# /usage-ping — usage reset 探測叫醒

在估計的 usage reset 時間排 **ping**，時間到叫醒 LLM——model turn 能發生 = 配額已重置（**落地即確認**）。**只叫醒不接任務**——reset 後要接續工作用 [`/at`](../at/SKILL.md)、交給另一個 session/provider 用 [`/handoff`](../handoff/SKILL.md)。

## 核心語義

- **落地即確認**：call 本身觸發/證明配額回來，不需查詢 usage 狀態的機制；估早的 ping 撞死配額 → turn 不發生（0 call）→ 下一 rung 15 分鐘後再試（有界重試）
- **單 call 紀律**（per-call 計費）：landing 只回一行確認文字、**零工具呼叫**——任何工具 round-trip 都是多一個 request，不划算
- **無語音**（user 09-09 定案——簡單事不浪費 token）：無排程確認 say、無召回機制；確認靠 landing 一行文字（session 內可見）
- **落地不做清理**：清理成本（CronList＋CronDelete ≈ 2-3 calls）與讓未 fire rung 空落地（各 1 call）相當且零失敗模式。殘留兩種——未 fire 的後續 rung、ZCode one-shot 跑完的 completed/failed 記錄（**不自動刪且佔 20 條名額**；Claude Code 跑完自刪無此殘留）——都由下次排程 supersede（步驟 2）清掉

## 執行流程（一次性 `HH:MM`）

1. **解析時間**：T = 輸入 +1 分鐘（秒數誤差防護——reset 若在 HH:MM:00，不延後會在重置完成前偷跑，浪費 rung）；T 落在 `:00`/`:30` 再 +1 分（Claude Code one-shot 整點/半點最多提前 90 秒 fire）。rungs = T / T+15m / T+30m，`date -v` 疊加換算（macOS `-v` 專屬且可疊加，如 `date -v+1M -v+15M`；跨日跨月交給 date，**不手算**）。輸入時刻今天已過 → 排明天（同 /at）。相對時間：ZCode 用 `delayMinutes`（工具契約禁把相對短語換算成固定時刻）、Claude Code 用 `date` 換算絕對時刻（跨日向用戶確認）。用戶在時間後寫任務 → 提示改用 `/at`
2. **Supersede**：`CronList` → 刪所有 title/prompt 含 `usage-ping` 的排程（**`CronCreate` 無同名覆蓋——不刪舊，舊 rung 照樣 fire**；completed/failed 殘留一併清）。清理後 ZCode 名額（上限 20 條；completed/failed/skipped 記錄都佔位）餘量 <3 → 降級 rung 數（2 或 1）並在摘要明說
3. **建階梯**：`CronCreate` × 3——每發 `recurring: false`、pinned cron（`分 時 日 月 *`）、prompt 用下方模板（首行 marker 供 supersede 匹配）。**ZCode 只建 rung 1 即止**：session 首個 automation 建立後，該 session 相關記錄（pending **或 completed**）在場，後續 `CronCreate` 全拒、刪除記錄才釋放（實測；fire 本身不釋放）——降級 1-rung、摘要明說；Claude Code 無此限制（×3 同批照建）。title `usage-ping {實際時刻} 叫醒 rung {i}/3`（標 +1 後的實際觸發時刻非輸入值；ZCode 必填，Claude Code 端工具無 title 參數則省略）
4. **摘要**：排程時刻（ZCode 註明僅 rung 1——session 綁定）、supersede 對象、成本上界（= 實際 rung 數 calls）

**rung prompt 模板（每發相同、自足）**：

```
🔴 usage-ping 落地（{time}）。本 turn 能發生＝配額已重置。只回一行確認文字（例：「🔴 usage-ping 落地（14:31）— 配額已重置」）；禁止任何工具呼叫、不清理不接任務。
```

## 週期-網格模式（`every Nh from HH:MM`，固定時刻制）

固定時刻 reset（每天同牆上時刻、秒級抖動）：單條 `recurring: true` cron——錨點 = 邊界時刻 +1 分（`date` 換算：分=59 進位到下小時，**不手算分+1**），通用式 `{錨點分} {錨點時 mod N}-23/{N} * * *`——`from 17:41`（N=5）→ 錨點 17:42 → `42 2-23/5 * * *`（每天 02/07/12/17/22:42）；`from 17:59` → 錨點 18:00 → `0 3-23/5 * * *`。N 不整除 24 有跨日接縫（5h 網格 22→02 只隔 4h），與 provider 實際排程不符就用新觀察邊界重跑本命令 re-anchor（supersede 刪舊 recurring）。

- **prompt 靜態自足、禁引用本檔**：recurring prompt 每週期原樣發送——landing session 讀 SKILL.md 是多 1 個 call，禁
- **成本**：每週期 1 call（純文字確認）；recurring 不留 completed 記錄、恆佔 1 名額。miss 週期 = turn 不發生 = **0 call 免費失敗**（cron 無秒級 retry，+1 分 margin 是唯一吸收機制）
- **漂移侵蝕**：邊界秒差累積 → margin 縮 → fire 開始 miss（記 failed）→ re-anchor
- title `usage-ping every {N}h 週期叫醒`（marker 供 supersede 匹配）；ZCode session 綁定同步驟 3（recurring 恆 active，建立後同 session 再建排程預期被拒）

**recurring prompt 模板**：

```
🔴 usage-ping 週期落地。本 turn 能發生＝配額已重置。只回一行確認文字（例：「🔴 usage-ping 週期落地 — 配額已重置」）；禁止任何工具呼叫。
```

## 滾動窗口制（GLM 5h 類）——無法自動輪詢

窗口從首用起算、邊界漂移，任何自動排程必漂移。實務：讀 provider UI 的下次 reset 時刻 → `/usage-ping HH:MM`（一次性），每次邊界重跑。無 UI 數字時**無參數保底**：T = now+301min——本次對話本身即配額使用，證明錨點 ≤ 現在 → 邊界 ≤ now+5h < T，任何時刻排都保證過邊界；不加 +1、不走 jitter（301 已含 margin）。**建排程照上方步驟 2–4**（跳過步驟 1 的 +1/jitter）；ZCode 單發可直接 `delayMinutes=301`。landing 即新窗口首用、錨定下輪邊界 = landing+5h → **落地後重跑本命令＝手動接力**（中途重跑會晚於邊界但仍正確）。

### 自排鏈已棄用（真實案例：2026-08-20 實測災難）

曾設計 landing turn 自排下一發（delayMinutes=301，landing call 即新窗口錨點、每輪重錨零漂移）。實測首發落地即退化迴圈：冷 context 下 landing LLM 重複呼叫首工具（CronList）約 50 次、context 累積放大燒盡 usage，鏈斷（成功率 0/1）。教訓：

- **冷 context trigger 禁多步工具工作流**——cron dispatch 無對話歷史，LLM 陷入「重複首工具」退化吸引子；若首工具是 CronCreate，迴圈指數複製排程（**不可用重排步驟順序修**）
- prompt 內 call 上限指令擋不住退化（退化時指令被忽略）；機械 hook 斷路器只能限損不能救鏈
- 一次性 landing「零工具、一行回覆」實測可靠

## 執行約束

- **host 開啟前提**（同 /at）：dispatch 由 host 在觸發時刻執行——host 關閉期間到點不觸發（ZCode 記「跳過」不補跑），需要就把 host 開到觸發時刻
- **失敗消耗假設**（一次性）：fire 失敗（配額仍死）也消耗該 one-shot（兩端文檔皆未記載 retry，保守假設）→ 靠多 rungs 有界取樣，不依賴單發重試（ZCode 僅 1 rung，miss 即無重試）；網格 recurring 恆存續（miss 週期 = 0 call）
- **生命週期**（同 /at）：Claude Code 綁 session（session 結束排程消失）；ZCode workspace 持久——殘留 completed 記錄佔 20 條名額，下次 supersede 清
- **已知缺口（真實案例：southchariot sc-231.1）——程式化建排程（CronCreate）依 session host 分兩道牆**：extension-chat-hosted——arm 即死 -32601；CLI-hosted——arm 成功但 desktop dispatch 失敗「Automation 模型选择不可用」（providerId 前綴 `builtin:` vs registry canonical `account:`；desktop Automations UI 重選模型可救）。完整兩道牆事實（症狀／根因／出路）單一源＝[at](../at/SKILL.md) known-gap 節；本命令不自造 session 內替代，**arm 成功不證明 ping 會落地**——落地即確認的驗證點在 fire 不在 arm

## 使用範例

```bash
/usage-ping 14:30               # 一次性 → +1 分 → rungs 14:31/14:46/15:01（ZCode 僅 14:31）
/usage-ping every 5h from 17:41 # 固定時刻制 → recurring cron 42 2-23/5 * * *（每天五發）
/usage-ping 01:02               # 滾動窗口（讀 UI 邊界後）→ 一次性
/usage-ping                     # 滾動窗口保底 → now+301min；落地後重跑＝手動接力
```
