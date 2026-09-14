---
name: voice-notification
description: "語音通知規範 — 長任務進行中定期召回提醒（Stop hook 機械執行）+ 任務完成通知（LLM say）。適用耗時實作/審查/分析任務（build/deep-work/code-review/execution-plan 等）；不適用快速查詢。觸發詞：語音通知、任務完成通知、進度提醒、召回提醒、通知用戶、say。"
allowed-tools: [Bash]
---

# 語音通知系統

> **載入時機**：任務開始/完成需通知、或建置進度提醒 sentinel 時按需載入。

## 核心理念：召回提醒優先

語音通知的本質是**召回用戶注意力** —— 用戶離開時提醒「該回來檢查了」。**誤報無害**（回來看一眼沒損失），**漏報才有成本**（成果閒置、用戶不知任務推進）。設計因此傾向「寧可多提醒」，不追求精準的完成判斷。

## 三條語音通道（職責分工，台詞不重疊 = 天然 single-source）

| 通道 | 觸發 | 載體 | 誰執行 |
|------|------|------|--------|
| **系統召回** | AI agent 需使用者輸入（權限確認等） | [notification.sh](../../hooks/notification.sh) hook | 機械（Notification event） |
| **進度提醒** | 長任務進行中，每 10 分鐘 | [stop-notification.sh](../../hooks/stop-notification.sh) hook | 機械（Stop event + sentinel） |
| **完成通知** | 任務完成 | 本 skill say 樣板 | LLM 自主 |

> 系統召回與進度提醒由 hook 機械執行（不靠 LLM 記得）；完成通知由 LLM 在 command 內 say。三通道台詞語意不重疊，稱謂清單只在本 skill 定義一處。

## 機械白名單（哪些任務觸發語音）

語音通知只適用以下 command，**其餘一律不 say**（消除「該不該通知」的判斷負擔）：

- **實作**：`/implement`、`/deep-work`
- **審查**：`/code-review`、`/ep-review`、`/ep-validate`、`/judge-review`、`/followup-review`
- **分析 / 維護 / 文檔產生**：`/execution-plan`、`/daily-maintain`、`/instruction-init`
- **升級**：`/upgrade-nt`、`/upgrade-sj`
- **排程接續**：`/at`（排程確認 + resume 完成）。（`/usage-ping` 語音面已退役 09-09——全面無語音，確認靠 landing 一行文字）

快速查詢、建議、`/illustrate`、`/commit`、`/help` 等**不 say**。

## 稱謂清單（標準定義處）

完成通知與進度提醒的隨機稱謂標準定義於此。`stop-notification.sh` 因 shell 無法讀 markdown，持一份同步副本（T 陣列）——**改稱謂時兩處同改**（本清單 + `hooks/stop-notification.sh`）：

`主人` `帥哥` `前輩` `道友` `陛下` `道祖`

## 可執行 bash 樣板（LLM 直接複製，不自己選稱謂）

```bash
# 任務開始（LLM 填任務名）
say -v Meijia -r 180 "開始{任務名}"

# 任務完成（稱謂隨機由 bash 陣列決定，LLM 只填任務名）
T=("主人" "帥哥" "前輩" "道友" "陛下" "道祖"); say -v Meijia -r 180 "${T[$((RANDOM % ${#T[@]}))]}！{任務名}完成"
```

> 逐字複製此樣板，不要改寫成 python 或拆多行。稱謂隨機交給 bash 陣列 `${T[$((RANDOM % ${#T[@]}))]}`，LLM 不做選擇（消除判斷負擔）。

## Stop hook sentinel 規範（進度提醒）

長任務（白名單中多步驟者，如 build/deep-work/execution-plan）開始時建立 sentinel，讓 Stop hook 機械執行進度提醒：

```bash
# 長任務開始（第一個動作前）
touch /tmp/.claude-voice-pending

# 長任務完成（say 完成通知之後）
rm -f /tmp/.claude-voice-pending
```

- sentinel 存在 = 有任務在跑 = Stop hook 每 10 分鐘 say「{隨機稱謂}，做到一個段落了，該檢查囉」
- **不判斷完成**：sentinel 存在就提醒，中途被提醒 = 進度提醒（用戶要的，非誤報）
- 完成 `rm` sentinel = 停止提醒；SessionEnd hook 會清殘留
- **僅長任務建 sentinel**：快速任務（單步完成）不建，避免多餘提醒
- ~~usage-ping 召回 sentinel~~（已退役 09-09——`/usage-ping` 全面去語音；hook 的 PING 邏輯已自 stop-notification.sh 移除，殘留 `/tmp/.usage-ping-pending` 由 SessionEnd 清）

## say 格式規則

- **20 字內**，確保語音清晰
- 完整口語句，避免技術術語
- voice 固定 `Meijia`、rate `180`
- 開始通知用中性句（「開始{任務名}」）；完成通知帶隨機稱謂（樣板已含）
