---
name: state-review
description: "全 repo 狀態對抗審查——抓 diff-review 的結構盲區（state-rot：跨弧累積漂移，每個 diff 各自乾淨但累積錯誤）。迴路＝環境凍結（clean-tree 預設＋scope manifest）→ external family 單發深審（work-order review variant）→ in-family judge-review → gate 候選提案。read-only 全程：產出報告與提案，落檔/建卡由 user 拍板。週期盤點／懷疑累積漂移／多 worktree 權威面審計用。"
when_to_use: "週期性（大弧收尾後）或觸發性（懷疑累積 drift、部署面疑似腐爛）的全 repo 狀態審查。NOT for: 任務弧 diff 審查（/code-review——diff-anchored）、人類 viewport 壞味道（/smell-detector——B 軸）、doc 連結健康（/doc-health）、單一修復驗收（/followup-review）。"
argument-hint: "[--family muse|codex|glm]（顯式指定深審家族；未指定＝依 caller 解析**相異**家族——非 muse caller→muse、muse caller→fail-loud 要求顯式指定；解析表單一源在 model-routing review/advisory 條款）"
allowed-tools: ["Read", "Bash", "Glob", "Grep", "Agent"]
---

# /state-review — 全 repo 狀態對抗審查

> **存在理由（真實案例）**：codex sol high 對 ai-guide 全 repo 深審，全部 Important findings 皆為 diff-review 結構性抓不到的 state-rot——殼 provenance 腐爛（前弧留下）、checker 的部署權威模型（多弧前寫的）、README 語義與 code 各自演化。每個當下的 diff 都通過了自己的 review，累積起來卻是錯的。

## 為什麼 diff-review 抓不到

[/code-review](../code-review/SKILL.md) 全鏈錨在任務弧邊界（baseline＋delta_tour＋EP 對照）——它驗證「這次變更對不對」，不驗證「現在的整體狀態對不對」；狀態腐爛的每一筆都發生在各自的綠燈裡。與近鄰的邊界：[/smell-detector](../smell-detector/SKILL.md) `--baseline` 是 B 軸人類 viewport（壞味道直覺、per-directory）；本 skill 是 A 軸機器 findings 進 judge 鏈（[受眾模型](../../AGENTS.md)）。

## 迴路

1. **環境凍結**（spawn 前自產）：**clean tree 預設**——`git status` 非空 → 先收斂，或顯式改 dirty 模式（記錄 tracked diff hash＋untracked 清單與 content hash）。凍結：HEAD sha、worktree 拓撲（`git worktree list`）、index/graph 新鮮度聲明、（dirty 模式）diff＋untracked 指紋。深審結束前**前後比對**（HEAD＋status／指紋）——不一致＝報告標 `stale` fail-loud，不得自稱凍結基線
2. **scope manifest**：審查範圍逐 path 分類——**core**（逐檔讀 source 與 failure branch）／**leaf**（機械全量掃＋異常深讀）／**generated**（驗投影與 hash parity，不當源）／**mirror**（驗 manifest 帳與回源）。每個 target path 恰屬一 bucket、exclusions 明列——沒進 manifest 的 path＝未審，不得自稱 full-repo
3. **深審派發**：external family、[work-order review variant](../_common/work-order.md)。family 解析＝[model-routing 跨家族解析表](../model-routing/SKILL.md)（**與 caller 相異**是派發理由本身）：未指定 → GLM/ZCode 與 codex/glm caller→muse；**muse caller→fail-loud**（無合法相異家族可自動選——**停下要求 user 選擇**：顯式 `--family codex` 或 `--family glm`，或明示接受同家族 degraded review〔caller-harness decision-grade dual-context 承接＋記錄〕，禁解析層自選降級）；顯式指定與 caller 同 family → fail-loud。派發內容＝凍結資料＋scope manifest＋輸出格式要求（見下）。**派發形態現況**：muse 腿經 bridge 自動化已實戰；codex 腿本弧為 user-relay——自動派發未驗證〔first-real-usage-pending〕（唯一一次派發被 user 中止：dispatch prompt 是薄清單而非 work-order、context 不自足，user 判斷後改 relay 直跑——非 run 失敗）；自動派發前必須逐節填滿 review variant 工單，首跑實測後回報
4. **in-family 裁決**（[/judge-review](../judge-review/SKILL.md)）：每項機械重現（不沿用宣稱）、防全採否證至少一項
5. **gate 候選提案**：每個採納項標注「同類 finding 是否第二次出現？」——是 → 列入報告的 **gate 候選清單**（proposal——建卡/做閘門由 user 拍板後續弧執行；有進有出：findings 是流入、gates 是流出）
6. **修復**走 /implement；驗收走 /followup-review

## 深審 work-order 的輸出格式要求（review variant findings schema）

schema 單一源在 [work-order review variant](../_common/work-order.md)（remedy 三分類／驗收設計／環境前提自曝／方法論限制段）；本 skill 追加兩條：

- **撤銷紀錄**：查證後推翻的初始判斷照列——撤銷過程常比初始判斷更有價值（存在理由案例中，審查者對自身 false findings 的自我否證正是最有價值的輸出）
- **gate 輸出也是 claim**：checker／linter 輸出先驗環境前提再引用（見 [acceptance-evidence](../acceptance-evidence/SKILL.md)「機械閘門的環境前提」）

## 執行約束

- **read-only 全程**：深審、裁決、報告皆不動 main working tree——不寫檔、不建卡、不 commit；產出＝對話內報告＋gate 候選清單
- 報告落 `ai-analysis/reports/`、殘項建卡＝**顯式 `--persist` 或 user 拍板後**的後續動作，非本 skill 預設路徑（backlog 建卡即 commit——outward action 授權在 user，skill invocation 不構成授權）
- 派發前查 model-routing 額度與 eligibility（review/advisory 形態條款——read-only 委派不以 implementation-loop 條件判定）；額度不足顯式降級（in-harness decision-grade 承接＋記錄），禁靜默略過
