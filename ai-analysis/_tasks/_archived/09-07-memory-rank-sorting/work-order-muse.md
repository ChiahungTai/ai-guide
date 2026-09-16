# Work Order — AIR-39 實作委派（muse bridge task）：rank 排序 S1(code TDD)＋S2(條文)

## 1. 紅線（違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改 backlog 卡狀態——止步 working tree
- 禁寫 /tmp 或 repo 外（含 memory 池）；中間筆記不留檔
- `.md` 修改＝讀目標節全文→精確區塊替換（禁 sed/regex 批次）；**`.py` 修改同此且禁風格重排（只改指名處）**
- Python 執行一律 `uv run` 前綴；pytest 跑 `uv run pytest <path> -q`（輸出重導檔案再讀，禁 pipe tail）
- 範圍外禁順手修

## 2. 目標

落地 memory 索引 rank 排序（fail-soft）：S1 generator 排序函數（**TDD——RED 先行**）＋S2 memory-audit 等條文。EP 的 Review Record 含 dual-family 17 findings 定案條款——**全部以修正後 EP 為準**。

## 3. Baseline

repo `/Users/ctai/Github/ai-rules`（主 WT）；base `339e2c9`。並行改動：working tree 有本弧任務家 untracked（ep/review-order）——不屬程式範圍。

## 4. 必讀

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-07-memory-rank-sorting/ep.md`——**全文**（S1 pseudo-code＋Review Record 定案條款是規格）
2. `/Users/ctai/Github/ai-rules/skills/memory-audit/scripts/generate_index.py`——**全檔**（ORDER :54-59／frontmatter 解析 :62-81〔巢狀攤平、頂層剝引號 :80 巢狀不剝 :76〕／errs 路徑 :108-109,135-145〔結構違規跳過投影＋exit 1〕／entries 迴圈 :102-112〔鍵＝檔名〕／分組投影 :119-125）
3. `/Users/ctai/Github/ai-rules/tests/test_memory_lifecycle.py`——ASSET_REL/make_pool 結構（:23-28）＋os.utime 先例（:196-197）
4. `/Users/ctai/Github/ai-rules/skills/memory-audit/SKILL.md`——層 1（:35 附近）/寫入端紀律段/層 3 夜波 bullet
5. `/Users/ctai/Github/ai-rules/skills/CLAUDE.md` :134／`/Users/ctai/Github/ai-rules/rules/context-management.md` :28

## 5. 已決策（勿重辯，全部 EP Review 定案）

- 排序鍵＝`(TYPE_ORDER[type], parse_rank, -mtime, name)`；TYPE_ORDER 由 `enumerate(ORDER)` 導出（ORDER 四組 user→feedback→project→reference 為既有事實勿改）
- rank 三值 hot=0/core=1/cold=2；**缺省/invalid 一律 core、永不進 errs**（至多 [INFO] 一行）——invalid 走 errs 會逐出合法條目＝召回斷裂
- **parse_rank 引號剝除**：巢狀 `metadata.rank: "hot"` 值帶引號（解析器 :76 巢狀不剝）——`.strip().strip("'\"").lower()`；雙落點（top-level `rank`／`metadata.rank`——沿 type 先例 :106）
- mtime＝每檔 `f.stat().st_mtime`；同分 fallback name（可重現）；edit 上浮＝預期 activity 信號
- gate/errs/atomic write/generator 其餘行為零變更；**資產源與池副本 bytes 一致性由 Stop hook cmp 守——你只改資產源，副本刷新是主 session 收案事**
- S2 詞形：hot/core/cold、「定期整理＝整理排序鍵（frontmatter），MEMORY.md 是投影禁手排」、hot 計數行進波次①盤點輸出
- 矛盾例外：檔案實際與 EP 行號/語義衝突 → 停下舉證

## 6. 範圍限定

- **動（五檔）**：
  - `skills/memory-audit/scripts/generate_index.py`——排序插入（entries 迴圈後/分組投影前）＋parse_rank/TYPE_ORDER/RANK_ORDER 常數＋mtime 取樣
  - `tests/test_memory_lifecycle.py`——新增排序 test（見 §8）
  - `skills/memory-audit/SKILL.md`——三處條文（寫入端 rank 初判一句／層 1 排序語義一行／夜波排序鍵覆核＋hot 計數＋整理排序鍵語義）＋description 觸發詞補「rank」
  - `skills/CLAUDE.md` :134——memory-audit 行列舉補「rank 排序」
  - `rules/context-management.md` :28——寫入端紀律濃縮補「rank 初判」半句
- **不動**：其他一切（特別 hooks/、backlog/、任務家、memory 池、generate_index.py 的 gate/errs 邏輯）

## 7. 工具接線

cat/rg/ls＋`uv run python`/`uv run pytest`；`git diff` 舉證；三禁令照舊

## 8. 驗收（逐條實跑，TDD 順序）

**RED 證據先**（步驟 0）：先寫排序 test → `uv run pytest tests/test_memory_lifecycle.py -q` → **新 test FAIL**（排序未實作）——輸出存證（這是 TDD 紅燈證據，報告必附）
1. GREEN 後：排序 test 全過——斷言覆蓋：type 四組序×rank 三層×mtime 尾序；default core 與顯式 core 同層；invalid（`rank: urgent`）→core；**`metadata.rank: "hot"`（巢狀、值帶引號 `"hot"`）解析為 hot**；top-level `rank: cold` 解析為 cold；fixture 以 `os.utime` 顯式設 mtime 差（防 flaky）
2. `uv run pytest tests/test_memory_lifecycle.py tests/test_sync_agents.py -q` → 全綠（回歸）
3. `rg -n "RANK_ORDER|parse_rank|TYPE_ORDER" skills/memory-audit/scripts/generate_index.py` → 命中
4. `rg -n "rank" skills/memory-audit/SKILL.md | head -8` → ≥4 命中（三處條文＋description）；`rg -n "排序鍵" skills/memory-audit/SKILL.md` → 命中（整理排序鍵語義）
5. `rg -n "rank" rules/context-management.md skills/CLAUDE.md` → 兩檔命中
6. `rg -c "errs" skills/memory-audit/scripts/generate_index.py` → errs 邏輯行數不變（未誤動）
7. `git diff --name-only` → 僅五檔
8. 冒煙（不動池）：`cd /tmp 禁`——改用 repo 內暫存？**跳過真池冒煙**（副本刷新屬主 session S3；你只跑 unit test）

## 9. 證據紀律＋PII

宣稱落地≠落地——逐項附 rg/pytest 輸出；RED 證據必附；「沒改 X」附 git diff；禁 PII；失敗如實記。

## 10. 交付報告

1. 改檔清單；2. S1/S2 逐點落實對照（file:line）；3. **RED 證據**＋驗收 1-7 命令與原始輸出；4. 偏差記錄；5. 未驗證項；6. reviewer 聚焦點
