# A5 activation 行為測試結果（conversation-dispatch）

> 執行面：`.agent-tmp/air-99/run_activation_probe.py` v2（複用 `scripts/skill_activation_probe.py` validated adapter：stage_carrier／carrier_env／run_one／classify；carrier＝scratch HOME＋`.agents/skills` symlink＋headless `zcode.cjs --mode plan --json`）。
> 判分＝機械 locator（positive PASS＝首個實質 tool_use 前載入目標 skill；nonmatch PASS＝零載入）；非 PASS reps 依 protocol 人工複讀 rollout 定案。
> 原始證據：`.agent-tmp/air-99/probe/run2-070214/`（v2 有效矩陣）、`probe/run-064402/`（v1 部分——GREEN 臂證據，RED 臂被 v1 覆蓋缺陷丟失）。

## 矩陣與結果（v2 run2-070214，10 runs）

場景 prompts 凍結（不點名 skill）：POS-1 錯誤處理盤點（討論座席情境）、POS-2 skills desc 背景研究（直接命中 desc 觸發詞「背景研究」）、NON-1 錯字直修、NON-2 數檔直查。

| phase | arm | rep | state | why | secs |
|---|---|---|---|---|---|
| RED（skill 過濾缺席） | positive | 1 | FAIL | not loaded, acted without it | 82.0 |
| RED | positive | 2 | FAIL | not loaded, acted without it | 63.9 |
| GREEN（skill 在場） | positive | 1 | FAIL | not loaded, acted without it | 61.2 |
| GREEN | positive | 2 | FAIL | not loaded, acted without it | 64.2 |
| GREEN | positive | 3 | FAIL | not loaded, acted without it | 24.0 |
| GREEN | positive | 4 | FAIL | not loaded, acted without it | 87.1 |
| GREEN | nonmatch | 1 | PASS | no load, acted on task directly | 38.1 |
| GREEN | nonmatch | 2 | PASS | no load, acted on task directly | 20.4 |
| GREEN | nonmatch | 3 | PASS | no load, acted on task directly | 13.3 |
| GREEN | nonmatch | 4 | PASS | no load, acted on task directly | 12.8 |

- **RED 2/2 FAIL＝預期 baseline**（skill 缺席，模型 inline／spawn 直做）——guidance 解真問題的信號面成立。
- **GREEN positive 4/4 FAIL＝activation 真失敗**（照實記錄，禁挑綠重跑——顯性失敗＞假綠）。
- **GREEN nonmatch 4/4 PASS＝零誤觸發**（不該派的場景確實不觸發；誤觸發面無風險）。

## 假說判定：(a) activation 真失敗 vs (b) probe harness 缺陷

(b) 三子項逐項取證（v1 run-064402＋v2 rollout）：

1. 「skill 未注入 GREEN 臂」——**排除**。GREEN rollout 的 available-skills system-reminder 確實列出 `- conversation-dispatch (file: <carrier>/.agents/skills/conversation-dispatch/SKILL.md)`（8/8 rollout 2–5 次索引提及）；RED rollout 零提及（filter 生效）。
2. 「測試 session 沒有 skill 載入通道」——**排除**。request 的 tools 定義含 `Skill` tool（`"name":"Skill"` 在場）。
3. 「場景 prompt 不構成觸發情境」——**排除**。模型行為證明情境理解正確：rep1 查證後 AskUserQuestion 問「Result 型別要用現成庫還是自己手寫？」（討論座席語境）；rep1/3/4 spawn `Agent`（Explore）做盤點（查證外派語境）；POS-2 更直接命中 desc 觸發詞「背景研究」。

**真根因（(a) 深層版——desc 觸發語義不進模型決策面）**：rollout 全文內 skill desc／when_to_use 特徵詞（查證外派、討論座席、背景研究、Fires when a verification）**0 命中**——ZCode harness 的 available-skills reminder 只注入 `name (file: path)`，428 chars 的 description 完全不在模型上下文。觸發實際只能靠**名字字面關聯**：「conversation-dispatch」與 POS-1/POS-2 場景措辭無字面關聯 → 零載入。對照 AIR-87 四 skill PASS 機制：memory-audit↔「寫進 memory」、implement↔「逐段實作」、execution-plan↔「實作規劃」、nt-v1-query↔「NautilusTrader v1」——名字字面命中場景詞，probe 機制對「名字可觸發」的 skill 有效；meta 層功能名（conversation-dispatch）字面無效。

**結論**：不是 desc 寫不好（desc 觸發詞設計在「desc 會被注入」的載體上才有效，如 Claude Code 端 Skill 列表帶 desc），而是 ZCode 載體機制上 desc 不承載觸發。屬**待裁決**——coordinator 裁量，worker 禁自行大改 skill 語義。候選方向（僅列供裁決，非建議）：skill 更名（名字字面攜觸發語義）、rule 升級句做名稱錨引導直呼載入、接受「本 skill 靠 rule 指針＋明示 invoke 觸發」並記入 skill 文檔預期。

**marshal 裁決記錄（2026-09-16）**：A5 判定＝desc 路徑 ZCode FAIL（實證）；rule 路徑未測（probe 臂設計只變 skill 在場、未變 rule 錨——列卡後續，不以此結案宣稱 rule 路徑已驗）。

## 附帶發現

- **行為層 vs activation 層分離**：GREEN positive 6/8 reps（跨 v1+v2）模型自然 spawn Explore 做盤點——外派行為部分湧現，但未經 skill 載入（無判準表約束；v1 rep2 inline 直查 4 檔正是判準表負空間邊緣案例）。此觀察反證負空間 threshold 的約束價值。
- **v1 runner 缺陷兩枚（v2 已修）**：① raw 檔名不含 phase——GREEN 同名覆蓋 RED rollout 證據；② repo 樹污染無偵測（repo 根曾現 adv.txt/f.txt/m.txt，coordinator 已清；rollout 0 命中無法逐字取證，最可能出自 subagent 副產物——subagent rollout 隨 carrier shred）。v2：phase 獨立 subdir＋`git status --porcelain` 跑前後 diff 污染偵測閘（隔離 quarantine/）。**v2 污染偵測：clean（0 檔）**。
- timeout 分佈：v1 rep4 240s timeout（rollout 僅 1 request——Agent spawn 後等待 subagent 中 timeout）；v2 無 timeout。
