# 工單：受影響測試集機械列舉三處＋回歸錨驗證（WO-3／EP S5-A）

> 定位：把「受影響測試集」的列舉從 LLM 目錄直覺升級為機械反查，落三處，並以 mosaic 歷史漏網案例做回歸驗證。

## 紅線（違反＝失敗）

- 禁 `git add`／`commit`／`push`／改任何 backlog 卡
- **mosaic repo（~/Github/mosaic_alpha）唯讀**——只准 git show／rg／ls／code-reality 查詢面，禁任何寫入
- 只准動「範圍限定」列出的 3 個 ai-rules 檔案
- 禁 /tmp 落檔；新增內容禁版本號／日期／統計；禁 model id 入文

## 目標（一句話）

「受影響」測試集的列舉改為機械反查（cr `callers`/`impact_radius` 或 `rg "<符號>" tests/ -l`）、禁目錄直覺，落進 quality-constraints 機制句＋cr-query 標準配方＋implement 驗證指針三處，並用 mosaic `9f151add` 漏網實例回歸驗證配方有效。

## Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`；base `63f2041`；working tree 已有 WO-1/WO-2 未 commit 修改（既有狀態，非衝突）
- 唯讀側：`/Users/ctai/Github/mosaic_alpha`（mosaic 三 worktree 之一，回歸錨 `9f151add` 在此）

## 必讀（按序）

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-03-air13-unified-subagent-arch/ep.md`——S5 段修改要點 2（工單 A 規格源，含證據三級定義）
2. `rules/quality-constraints.md`——「跨模組影響擴散」段與「消費端驗證模式」表附近（機制句落點）
3. `skills/cr-query/SKILL.md`——全文結構（配方落點；注意其 graph 缺場 `[WARN]` gate 先例）
4. `skills/implement/SKILL.md`——階段 2「整合路徑覆蓋檢查」段（指針落點）

## 已決策（勿重辯）＋矛盾例外

1. 機制句語義（quality-constraints）：「受影響」測試集**必須**機械反查——code-reality `callers`/`impact_radius` 或 `rg "<符號>" tests/ -l`——禁以目錄直覺代替（測試檔跨目錄擺放時直覺必漏）
2. cr-query 標準配方形態：「修改檔 → 受影響 test files」——①有 graph：`code-reality graph_query impact_radius --repo <root> --files <絕對路徑>` 取影響檔案集，再對 tests 目錄 rg 交叉；②無 graph／stale：退 `rg "<符號>" tests/ -l`；③輸出**證據三級標記**：graph-derived／text-derived／未驗證 dynamic consumers（rg 命中≠完整 impact——動態派發與字串鍵耦合是 CR 盲區）
3. implement 指針形態：階段 2 驗證的整合路徑檢查附近補一句「受影響測試集列舉走機械反查（配方見 cr-query skill）」——pointer 不展開
4. 回歸錨事實：mosaic `9f151add` 改 `structure/pre_swing_profiler.py`，其測試住 `tests/unit_tests/alpha_forge/`——歷史結案時目錄直覺漏列、8 個 baseline FAIL 活過結案（修復 `ef114979`）。配方反查**應**列出這些測試檔

**矛盾例外**：發現三檔現況已有等效機制句（rg 驗證），停下舉證勿重加。

## 範圍限定

- 動：`rules/quality-constraints.md`、`skills/cr-query/SKILL.md`、`skills/implement/SKILL.md`
- 唯讀：`/Users/ctai/Github/mosaic_alpha`（全 repo）
- 不動：ai-rules 其他一切

## 工具接線

- bash（cat/rg/ls/git -C）；mosaic 側 code-reality 查詢面可用可不用（graph 在場則用、缺場退 rg——本身即配方的三級示範）；禁 CR 寫入面；禁 /tmp

## 驗收（命令＋預期，逐條實跑）

1. `rg -n "機械反查" rules/quality-constraints.md` → ≥1 命中（機制句）
2. `rg -n "受影響 test|受影響測試集" skills/cr-query/SKILL.md` → ≥1 命中（配方）
3. `rg -n "機械反查|受影響測試集" skills/implement/SKILL.md` → ≥1 命中（指針）
4. `rg -n "graph-derived|text-derived" skills/cr-query/SKILL.md` → 兩詞命中（證據三級）
5. 回歸錨（mosaic 唯讀）：`git -C /Users/ctai/Github/mosaic_alpha show --stat 9f151add | head -20` 原始輸出（確認標的檔）＋反查 `rg -l "pre_swing_profiler" /Users/ctai/Github/mosaic_alpha/tests/` 原始輸出——**期望列出 `tests/unit_tests/alpha_forge/` 下測試檔**，輸出標記證據等級（text-derived；若你用了 graph 則標 graph-derived）
6. 負向：`rg -n "muse-spark|gpt-|glm-" rules/quality-constraints.md skills/cr-query/SKILL.md skills/implement/SKILL.md` → 零命中

## 證據紀律＋PII 禁令

每條驗收附完整命令與原始輸出；`git diff --name-only` 佐證範圍；報告禁 PII。

## 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單 2. 三落點逐項說明（file:line）3. 驗收 1-6 原始輸出（回歸錨輸出全文——它是本工單的靈魂證據）4. 偏差記錄 5. 未驗證項 6. 建議 reviewer 聚焦點
