---
name: feedback-subagent-background-spawn
description: subagent 預設背景跑已固化為全域規則（rules/tool-discipline.md 背景執行段）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_9f18d654-1029-400d-a249-9465416c9bae
---

User feedback：ZCode subagent spawn 不帶背景參數會卡住主對話 turn，使用者無法繼續對話。

**Why:** ZCode 無預設背景行為（Claude 2.1.198+ 才有），前台/後台由 spawn 端每次決定。

**How to apply:** 已固化為 `rules/tool-discipline.md`「背景執行（不阻塞對話）」段並經 deploy_agents.py 全域部署——規則是唯一真相源，本 memory 僅留回饋脈絡。code-reviewer 另有 frontmatter `background: true`（Claude 端強制背景；ZCode 靜默忽略）。

**Token 經濟學背書（2026-08-18 用戶質疑後定案）**：曾猶豫「notification resume 若計 prompt 則背景模式多燒」——用戶反問「不花這個你怎樣背景跑完後繼續做事？背景跑很重要」。定案：**背景 vs 前台 token 等價**——兩者接手時各送一次全 context（cache TTL 是壁鐘制，前台傻等照樣逾期）；差別僅 turn +1，而 turn 非計量軸（見 [[per-call-billing-model]]）。通知接手是接手的唯一載體、不是額外開銷；背景換到 UX 插話 + 多 agent 平行 = 同樣的錢買更多能力。**勿再以計費理由挑戰背景模式**。

**背景 spawn 可被無聲 stop（2026-08-25 實例）**：dual-context 審查的 fresh-eyes agent spawn 後被 stop（52 秒、無 findings 落地；usage 壓力或中斷皆可能）——背景結果不是保證交付。防護：重要審查/長任務 spawn 後，把「哪些 agent 在飛、結果是否落地」寫進 at-context/handoff context 檔，接手方才能機械判斷需重跑（本例 context 檔記「fresh-eyes 被 stop 需重跑」實現無縫接續）；通知未達且任務關鍵 → 主動重 spawn 比等待便宜。

**背景 agent 死活偵測指紋（2026-08-25 同日補）**：spawn 逾時未收到通知時，用 output 檔 **metadata** 判死活（`ls -la` 看 size/mtime，禁讀內容——是 transcript JSONL）：**size ≈31 bytes＋mtime 凍結在 spawn 時刻＝掛掉指紋**（placeholder 從未成長）；剛 spawn 的 agent output 檔可能還不存在（非死訊）。掛了就直接背景重 spawn（同 prompt），不必等也不必修——同日 primed 審查 agent 以此法確認死亡並重跑成功。

**收法層規則（2026-09-02 實證＋固化）**：spawn 背景後用 `TaskOutput(block=true)` 長阻等＝兩重傷害——①主對話卡死（user 體感「沒有在背景跑」）②**阻等待被中斷/取消時 agent 連帶被殺**（status=killed、結果遺失；同日驗證 agent 因此重跑）。正解＝spawn 後結束 turn 等完成通知、前景先做別的事；block=true 僅限 <30s 短 probe。已固化 `rules/tool-discipline.md`「背景 agent 的收法」段（spawn 規則的配套）。
