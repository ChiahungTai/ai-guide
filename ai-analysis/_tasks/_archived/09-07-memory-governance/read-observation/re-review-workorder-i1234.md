# Work Order — AIR-41 I1-I4 修復重審（read-only second opinion）

> review/advisory variant（`skills/_common/work-order.md` 替換語義）：read-only、無 EP 重寫、無預期改檔。範圍限定重審——I1-I4 的修復 diff＋新測例，**不重審全 commit**。

## 1. 紅線（首段，違反＝失敗）

- read-only：禁任何寫入（含 `git add`／`git commit`／backlog 卡狀態／產物落檔——結論只在最終回覆文字承載）
- 禁把任何工具輸出寫到 repo 外（含 `/tmp`）；中間筆記不留檔
- 紅線違反＝失敗；審查未過不得結卡

## 2. 目標

AIR-41（memory 死亡條目觀測——reads telemetry）實作後雙家族 review 提出 4 個 Important（I1-I4）。本工單驗證修復是否真正解掉這四項——逐項對照修復 diff、新測例、live 證據，verdict（每項 fixed / partially-fixed / not-fixed / new-issue-introduced）＋新發現。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree）
- HEAD：`4051f3b`（AIR-41 原結案 commit——修復在其上的 working tree 未 commit 變更）
- dirty 聲明：tracked diff sha12 = `fce58a5e9bbc`（`git diff | shasum` 前 12）；改檔 4：backlog 卡（AIR-41 狀態）、`skills/memory-audit/SKILL.md`、`skills/memory-audit/scripts/memory_telemetry.py`、`tests/test_memory_read_observation.py`；untracked：`ai-analysis/_tasks/09-07-memory-governance/evidence/reads-post-i1234.json`（live 修復後證據）
- 審查端前後比對：不一致＝stale，停下舉證

## 4. 必讀（按序，絕對路徑）

1. 原始 findings（本工單 §11 附錄逐字）——I1-I4 是驗收標的
2. `git diff`（working tree）——修復本體；對照 §12 修復落點錨
3. `tests/test_memory_read_observation.py`——新測例 `test_i1_rank_mirror_fences_and_metadata_fallback`、`test_i2_unpaired_reads_count_as_contact`、`test_i3_window_shortfall_flags_partial`、`test_i4_reads_without_entry_rename_clue`
4. `skills/memory-audit/scripts/memory_telemetry.py`——`_frontmatter_rank`／`snapshot_entries`／`project_reads`
5. `skills/memory-audit/SKILL.md`「層 2」Read 觀測段（:47）——I3/I4 口徑條文
6. `/Users/ctai/.claude/projects/-Users-ctai-Github-ai-rules/memory/_generate_index.py` `parse_frontmatter`（:76-95）＋`parse_rank`（:98-102）——I1 mirror 的對照源
7. `ai-analysis/_tasks/09-07-memory-governance/read-observation/ep.md` R2/R4/R6 段——原驗收語義
8. `ai-analysis/_tasks/09-07-memory-governance/evidence/reads-post-i1234.json`——live 修復後行為
9. 方法論 bundle：`skills/review-engine/SKILL.md`（findings 詞彙沿用，不定義新詞）

## 5. 已決策（勿重辯）＋矛盾例外

- **I1 採行為等價 mirror 而非 import generator**：pool 的 `_generate_index.py` 是部署產物（各池可自換、可缺席），read-only collector 不執行外部代碼（importlib `exec_module` 跑 module-level）；等價契約以 `test_i1` 釘邊界（fence 錨定／metadata parent 限定／頂層空值 fallback／引號剝除），per-pool generator hash 已隨報告 `generator_schema` 揭露供 drift 對帳。**勿重辯「應該直接 import」**——除非你能證明 mirror 與 generator 在具體輸入上行為分歧（那是 bug 證據，歡迎舉證）。
- **I4 採方案 (b)**：HOLD＝EP 級 LLM 裁決面（skill 條文承載口徑），機械腳本只出 `reads_without_entry` 線索；`maintenance_only_unconfirmed` 假空槽已移除。勿提案「機械 hold 表」——EP R6 明文不自動合併身分。
- **矛盾例外**：發現實作／條文／EP／測試互相矛盾 → 停下舉證（file:line＋逐字引用），不自行改設計。

## 6. 範圍限定

- 動＝零（read-only）
- 不動＝全部（含 backlog 卡狀態）——交付以 `git status --short` 前後一致舉證

## 7. 工具接線

- 讀查：`bash`（`cat`／`rg`／`sed -n`）、`Read`；字串搜尋一律 `rg`
- 可跑唯讉驗證：`uv run pytest tests/test_memory_read_observation.py tests/test_memory_telemetry.py -q`（唯讀測試——fixture 在 tmp_path）
- 三禁令：禁 code-reality 寫入面；禁工具輸出寫 repo 外；禁自行妥協路徑（遇缺口停下舉證）

## 8. 驗收（逐條實跑，命令＋原始輸出）

1. `git diff skills/memory-audit/scripts/memory_telemetry.py | rg -n '_frontmatter_rank|startswith|metadata'` → I1 落點存在
2. `git diff skills/memory-audit/scripts/memory_telemetry.py | rg -n 'unpaired|window_shortfall|reads_without_entry'` → I2/I3/I4 鍵存在
3. `git diff skills/memory-audit/scripts/memory_telemetry.py | rg -n 'maintenance_only'` → **零命中**（假空槽移除）
4. `uv run pytest tests/test_memory_read_observation.py -q` → 10 passed
5. `uv run pytest tests/test_memory_telemetry.py -q` → 22 passed
6. `rg -n 'window_shortfall|reads_without_entry|unpaired_reads' ai-analysis/_tasks/09-07-memory-governance/evidence/reads-post-i1234.json | head -5` → live 鍵在場（window_shortfall: true、reads_without_entry 非空）
7. 對照 I1 mirror 與 generator：構造差分案例心證（如頂層 `rank: 'hot'` 引號、metadata 巢狀引號、frontmatter 缺閉合）——兩者行為是否一致
8. `rg -n 'maintenance_only' skills/ tests/` → 零命中（全 repo 消費端無殘留引用）

## 9. 證據紀律＋PII 禁令

- 每條宣稱附命令＋原始輸出（截斷標明）；「沒改 X」附 `git status --short` 佐證
- 報告禁 email／人名 PII；失敗如實記錄

## 10. 交付報告格式（最終回覆承載，不寫檔）

1. **逐項 verdict**：I1/I2/I3/I4 各一——fixed / partially-fixed / not-fixed / new-issue-introduced，附證據（file:line＋命令輸出節錄）
2. **新發現 findings**：每條附 file:line 錨點、嚴重度（Critical/Important/Suggestion——review-engine 三級）、信心水準、remedy 三分類（bug／drift／design-reversal）；Important 以上附可機械化驗收設計
3. 環境前提自曝（HEAD、dirty hash 核對結果）＋方法論限制段（用了什麼、什麼無法驗證）
4. 總結論：重審通過／不通過（不通過＝仍有 not-fixed 或 new Critical/Important）

## 11. 附錄——原始 findings 逐字（驗收標的）

**I1（Important，fresh）rank mirror 不等价：memory_telemetry.py:495,511-516 註解聲稱 mirror generate_index.parse_rank，但缺 metadata.rank 落點、frontmatter 切分用 split("---",2) 不等价（body 含 ---＋rank 行會幻覺）。修：直接 import parse_frontmatter/parse_rank（同目錄），或补落点＋startswith 锚定＋两测例。Live 池今日无 rank 键故是 latent，未酿成误报。**

**I2（Important，fresh）unmatched/unknown Read 静默丢弃：:264,287-288,536-540——CC unmatched（Read 已发出、缺 result）与 zcode unknown 状态不进 reads 也不进 read_errors，会把读过的条目打成 zero 候选，方向性错误。修：unmatched 计接触（或另立 unpaired 揭露）＋测例。**

**I3（Important，primed）保留期不足无旗标：project_reads partial 只看源有无。实算：窗 06-09 起，zcode 最早 08-16、claude 最早 08-12——~26 天观测挂 90 天窗名，partial=False。修：加 window_shortfall（bounds.first>since 即 true）进 coverage_limited＋skill 註记＋1 fixture test。**

**I4（Important，primed）HOLD/identity 无载体：maintenance_only_unconfirmed 硬编码 []（静态 JSON 无处给 LLM 填）；R6 的 identity_unknown/HOLD code＋skill 皆无键；EP 点名的 owner未知/rename fixture 缺。修（二选一写进 skill）：(a) 机械 hold 表，或 (b) EP 级裁决 HOLD 纯 LLM 面＋留一次可重放记录；至少补 rename＋unmatched-Read fixture。**

## 12. 附錄——修復落點錨（對照用）

- I1：`memory_telemetry.py` 新函式 `_frontmatter_rank(text)`（RANKS 定義後）＋`snapshot_entries` 改用之；`tests/test_memory_read_observation.py::test_i1_rank_mirror_fences_and_metadata_fallback` 四斷言（metadata nested／非 metadata parent 不匹配／頂層空 fallback／body fence 不幻覺）
- I2：`project_reads` unmatched/unknown Read 進 `body_reads`（帶 `status` 鍵）＋`coverages["unpaired_reads"]`；`test_i2_unpaired_reads_count_as_contact`
- I3：`project_reads` 簽名加 `since`；`coverages["window_shortfall"]`（bounds.first > since）併入 `partial`；`test_i3_window_shortfall_flags_partial`（late/early 兩形）；skill 層 2 段註記
- I4：`candidates["reads_without_entry"]`（rename/刪除線索）取代 `maintenance_only_unconfirmed`；skill 層 2 段 HOLD 口徑（EP 級 LLM 裁決＋可重放）；`test_i4_reads_without_entry_rename_clue`
- live：`reads-post-i1234.json`——window_shortfall=true、reads_without_entry 非空（cluster-merge 舊名）、unpaired_reads=0（live 無案例）、zero_body_read=33 不變
