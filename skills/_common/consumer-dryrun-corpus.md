# consumer-dryrun-corpus — 消費端演練契約（AIR-131）

> 測的是 instruction 系統真正的 UX：given 真實 consumer state＋真實任務，fresh agent 能否發現正確控制面並走到正確下一步。不是 instruction 文法檢查，不是 consistency——那歸 [consistency](../../skills/consistency/SKILL.md) 與 parity lint。

## 四型任務

| 型 | 測什麼 |
|---|---|
| cold navigation | 不給路徑提示，能否第一次就找到正確入口 |
| normal task | happy path 能否正確執行 |
| ambiguous/conflict task | 多個看似合理來源時選哪個 |
| resume task | fresh session 能否從 durable state 找到 resume point |

## 控制變數（硬性）

- **prompt 只描述 consumer goal，禁提示 instruction topology**（路徑／檔名／機制名一律不給——否則 discoverability bug 被藏掉）
- fresh agent＝與作者無共享 context 的獨立 spawn（跨家族更強）

## 記錄規格（五量測維度）

| 維度 | 可觀察現象 |
|---|---|
| Discoverability | 是否第一次就找到正確 source/skill/command |
| Navigation cost | 到 first correct action 前讀多少來源、走多少 hops（同 task corpus＋同 harness 前後對比，非全域 token 門檻） |
| Ambiguity | 是否同時存在兩個合理但不同的 action |
| Prompt repair | 是否需要 human 再補一句「去看 X」 |
| Workaround | 是否繞過設計入口才能完成 |

**workaround 比 failure 更有情報量**（agent 成功了但自己補了一條路——success rate 會藏掉它）。同一 workaround 在**兩個獨立 consumer contexts 再現→ 升格 design smell**；跨 repo/harness 重現＝更強證據（非必要條件）。

## 記錄 provenance（升格判定必需——codex finding）

每次演練記錄須帶 **corpus task id＋consumer/harness identity**（context provenance）——沒有 provenance，「兩個獨立 contexts」無法判定，升格規則失效。

## 觸發（掛 deep-work 劇本指針）

- 控制面變更弧必跑
- 每季 fresh-agent 開工演練保底（覆蓋「長期無大弧但持續小改」的漂移盲區）
- 觸發記錄入弧結算
