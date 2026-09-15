---
id: AIR-99
title: >-
  會話主動派工模式——主 agent 討論座席、查證打雜自動外派 sub agent（conversation-dispatch skill＋rule
  觸發線）
status: To Do
assignee: []
created_date: '2026-09-15 14:09'
updated_date: '2026-09-15 14:10'
labels:
  - governance
  - skills
  - agent-workflow
dependencies: []
ordinal: 84000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
跟 AI 討論事情時，查資料、盤點、機械驗證這類打雜活自動派給 sub agent 背景跑，主 agent 專心陪使用者討論、判讀、裁決，不用使用者指派。基礎設施（角色 registry、路由、背景 spawn）九成已在場，缺的是會話場景的派工判準與觸發。已過 muse＋codex 雙腿討論收斂（adjust-go／GO）。驗收＝AC A1–A6（機械可驗）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A1 載體在場：conversation-dispatch skill 新建，desc 帶會話觸發詞（主動派工/討論座席/查證外派/背景研究）；spawn 機械以引用 agent-workflow/model-routing 承接，零拷貝（rg 驗無重複條文）
A2 rule 觸發線：rules/context-management.md 既有「大範圍探索」句升級為帶行為錨＋pointer（廣度探索/多檔查證先判外派；唯讀結論回報域可自主派→載入 skill 判準表）；不開新 rule 檔；部署依 rules/AGENTS.md（deploy 逐端＋size gate）
A3 判準表＝heuristic 預設：明標非 normative（demand 唯一源仍在各 owning workflow rows——AIR-91）；正表（單點≤2檔直查／廣度→Explore／機械對帳→lite-verify／逐字規格→spec-miner／多源→cross-verify-investigator／判讀裁決→主 session）＋負空間（≤2 檔、<30s 前台 probe、當前步驟立即依賴）等重在場；role 名引用 registry 不拷貝 pins
A4 額度同意邊界：唯讀＋in-harness 自主派；bridge/external-runtime（muse/codex/glm）必先問使用者；並發上限沿用——條文在場（rg 可驗）
A5 activation 行為測試：instruction-testing 跑會話問句召回（該派/不該派各 ≥2 例），結果落任務家；不挑綠重跑
A6 端到端一例：實際 spawn→背景回收→結論帶 path:line 逐字錨點→主 session 錨點驗收命中（rg/Read 對得上）；錨點失效退回重取不降級採用
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 24cc3b2；討論輸入＝/Users/ctai/Downloads/fabel_astra_multimodel_cost_architecture_review.md（§10/16/22：cheap 收集 evidence pack、strong model 只做 judgment）＋ 09-15 session 實證（主 session 直讀 170KB 報告 vs POC 腿派工回收兩形態對照）〕

〔已決策勿重辯：①不新增 Marshal skill/role——AIR-91 裁決保留（Marshal＝composite workflow orchestration responsibility）；會話派工是 dispatch policy/session 行為（muse＋codex 雙腿一致否決 C）②載體＝新 conversation-dispatch skill＋rule 觸發線＋引用既有機械（codex B+D 形態；否決 muse A 增節版——agent-workflow 管「怎麼安全 spawn」、本卡管「session 何時 spawn」兩個問題，且獨立 skill 對 user「進入模式」心智可見）③吸收 muse 三補強：判準表明標 heuristic 預設（非 normative；AIR-91 demand 唯一源＝owning workflow rows，不重演多處重寫 demand）；負空間與正表等重；額度同意邊界（唯讀 in-harness 自主、bridge/external 必先問——feedback_external-dispatch-ask-first）④進場機制＝rule 常駐提供模式在場感（不需顯式 invoke）＋desc 觸發詞輔助＋activation 行為測試驗收；skill 載入後 session 內常駐；決策粒度＝每查證問句判一次（非 deep-work 式 session 駐留態——muse 糾正）⑤回報契約＝結論＋path:line 逐字錨點＋未驗項（unverified/not-found 分列）；不強制 nested schema（/codebase-sweep 6/6 retry 前車）；收集/判讀分離——研究腿回 evidence 不替主 session 做決策；錨點驗收失敗退回重取，不降級採用（no-silent-downgrade 會話層投影）⑥spawn 型別分流一行寫明：lite 機械必 registry 角色、唯讀探察用 Explore（AIR-50 旗艦燒機械段教訓）；禁再委派句必帶（防會話腿自行轉包 bridge）⑦邊界：不動 development workflow redesign EP（凍結待 implement）與 AIR-91/96 契約；會話表跟隨 redesign S1/S2 review 預設、不領先；Reserve Policy/ExpectedCost/歷史成功率（額度經濟學）不入本卡（後續線，與 AIR-98 同軸）〕

範圍：
P1 新 skill skills/conversation-dispatch/SKILL.md——trigger situations、判準表（正表＋負空間）、spawn prompt 模板句（WorkUnitContext：objective/constraints/relevant_files/expected_output——不倒整段對話）、回收驗收步驟；spawn 機械/路由全引用 agent-workflow＋model-routing。
P2 rules/context-management.md「大範圍探索」句升級為行為錨＋pointer；部署照 rules/AGENTS.md（預覽 diff＋size gate＋逐端驗證）。
P3 skill desc 會話觸發詞＋agent-workflow desc 補指向（若需）。
P4 activation 行為測試（該派/不該派各 ≥2 例）＋端到端一例（派→回收→錨點命中），結果落任務家。

不做：不新增 Marshal/Role/engine/runtime；不改 catalog/schema/presets；不動 workflow redesign EP；不建狀態庫；不做額度經濟學（reserve/shadow price）。

風險面：討論連續性中斷（回收需帶「影響什麼/未決什麼」）；context 洩漏（prompt 最小 WorkUnitContext）；過度派工（延遲＋額度雙燒——負空間+threshold 擋）；external dispatch 未問先派（同意邊界條文擋）。相鄰不重複：DRAFT-6（family×任務 fit）、AIR-98（額度新鮮度）、deep-work（session 級自主模式，非會話派工）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Provenance：09-15 user 提問（主 agent 討論座席＋主動派 sub agent 打雜＝進入一種模式，名稱不重要），arch-thinking 分析後雙腿討論。muse job-mu2qulll-hc6rze（verdict=adjust 後 go：推 A+D 窄版；貢獻 heuristic 聲明/負空間/同意邊界/per-turn 粒度糾正）；codex job-mu2qv8sv（verdict=adjust：推 B+D+引用 A、evidence pack 契約、收集判讀分離）。裁定＝B+D 形態＋muse 三補強（理由見 Plan ②③）。原始輸出 .delegate-bridge/jobs/ 兩 jobId jsonl。
<!-- SECTION:NOTES:END -->
