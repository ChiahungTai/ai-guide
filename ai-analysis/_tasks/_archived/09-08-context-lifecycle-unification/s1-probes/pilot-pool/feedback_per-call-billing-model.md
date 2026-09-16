---
name: per-call-billing-model
description: 計費模型定案＝token-value 制（Claude Max 同構）——策略雙軸＝省 requests＋省 context；輪次非計量軸、premium 倍率不可精算
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_38bc3cc9-d5eb-4080-8c39-168647bca011
---

計費認知演化（2026-08-17~18 四次修正，最終定案）：

1. ~~per-call request 制~~（08-17 用戶當時理解）→ 2. ~~prompts/query 制~~（08-18 官方文件字面）→ 3. ~~不可精算故省 prompt 輪次~~（08-18 用戶 V1 模糊+倍率裁定的中間態）→ **4. 定案：token-value 制**。

**定案證據三角（08-18）**：① Claude 官方先例——usage 限制是 token 制（「長對話每則訊息消耗更多 token，整個 context 重新處理」；5h rolling + weekly cap + 「換算 API 定價 ≈ 月費 15-30×」與 ZCode 文件逐條對應，即 Claude Max 同構）；② 用戶 dashboard 顯示 Token usage 4.7B（meter 機制看得到 token）；③ 用戶算術——Pro 以上 + 額度 1-2h 用完 + 消耗隨時段變化，turn/request 制在其量級（最忙 5h 僅 113 turns/~1.3K requests）永遠撞不到牆，只有 value 制能解釋。「prompts」（1 prompt ≈ 15-20 invocations）是 UI 話術；用戶「介於 message 跟 call 之間」的直覺=兩個 UI 單位都不是真相。premium model 倍率=value 制特徵。

**Why**: 計量是 token 時，**省 requests 和省 context 雙軸都直接省錢**；省 turn/message 輪次只剩次要價值（每輪 context 重送的間接效果）。

**How to apply**:
- 已落地紀律（批次化/Read 紀律/git 錨定/組合命令）在 token 制下**全數正確且更對**——不需新增「省 prompt 輪次」核心紀律
- 輪次類優化（澄清一次問完/確認彙整到末端/排程經濟）**已落地（2026-08-18，collaboration-constraints + at skill）**——每次往返 = 全 context 重送，token 制下有實值；護欄：該問仍要問（湊一次問非不問）、硬 gate 例外（commit consent/destructive/單向門）
- **背景 spawn 維持不翻（已解除猶豫）**：通知接手與前台等的 token 帳等價（context 重送都一次、cache TTL 看壁鐘），背景買 UX+平行是淨賺
- F4（135KB bundle 分層減肥）復活為現役候選——「整個 context 每則訊息重新處理」正是 Claude 先例警告；但刪規則傷行為的取捨在，**開 EP 正規做非順手砍**
- F9 不做機械 cache 保溫（定時 ping 反而多燒）；批次化/組合命令已是其正確形態
- 計量細節（倍率值）不可精算——不做無法驗證的計費逆向
- 相關：[[cr-live-faces-roadmap]]（implement 消耗分析段）、[[feedback-subagent-background-spawn]]、[[token-billing-discipline-rederivation]]
