# EP: memory 索引 rank 排序——fail-soft 載入設計

> **ep_type**: implementation（混合弧：S1 含 .py code、S2/S3 docs）

baseline: 339e2c9

## 實作總覽

**設計根源**（user 09-07 洞察，arch-thinking 定案）：索引載入截斷（200 行／25,000 chars 先到為準、**尾端條目不載**）是無法消除的平台事實——與其追求完美壓縮（今天實證：gate 超限、蒸餾靠自覺、並行寫入者），不如讓截斷的失敗模式**有序**：重要在前、冷門隨時間沉底，機制失靈時損失的只是冷門尾端（fail-soft）。

**現況**（觀察＋review 實證）：MEMORY.md 排序＝`ORDER` 四組（`generate_index.py:54-59`：user→feedback→project→reference）× 組內**字母序**（`sorted(here.glob)` :102 饋入＋保序投影 :120——非顯式 entries.sort）——誰被截掉由字母決定，排序軸未對準消費者。截斷只影響開場自動載入（條目檔仍在池、on-demand rg 可查）——失敗真實形態＝召回率下降，排序把召回損失導向冷門條目。entries 元組（:112）不含 mtime——排序需新增每檔 `f.stat()`（129 檔量級可忽略）。

**四層縱深定位**：gate（流入節流）＋夜波（流出）＋2.8 閘門（結案出口）全不動；rank 排序是疊加的第四層——最後防線的失敗模式從無序變有序。

## UC 盤點

### Backlog 關聯
- AIR-39（本弧卡，339e2c9）
- 前弧脈絡：AIR-25（generator 制度）、AIR-27（errs 路徑）、AIR-37（2.8 memory 對帳閘門）——皆 Done

### SYSTEM-MAP 影響
- 無（元專案）

### 掃描範圍
- 變更面：`skills/memory-audit/scripts/generate_index.py`（資產源，排序函數＋rank 解析）、`tests/test_memory_lifecycle.py`（排序 test）、`skills/memory-audit/SKILL.md`（三處條文＋description 觸發詞補「rank」）、`skills/CLAUDE.md`（:134 索引行）、`rules/context-management.md:28`（寫入端紀律 rule 濃縮——補「rank 初判」半句，review F6）
- 部署面：ai-rules 池副本 `~/.zcode/cli/memories/projects/<id>/memory/_generate_index.py`（cmp/cp 原子刷新——SKILL 層 1 既有程序）

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| 索引機械投影（generator） | ✅ | generate_index.py | 更新 | 排序函數加 rank 維度 |
| 寫入端紀律（六問/desc 三不） | ✅ | memory-audit skill | 更新 | 加 rank 初判一句 |
| 夜間收斂波 | ✅ | memory-audit skill 層 3 | 更新 | 波次職責加排序鍵覆核 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| memory 索引 rank 排序（fail-soft 載入） | 📋 | generate_index.py＋memory-audit skill |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 新條目寫入（帶 rank） | frontmatter `rank: hot` | generator 投影至 type 組內 rank 層前段 | 無 | rank 排序 |
| SM-2 | 既有條目（無 rank） | 存量 129 條 default | default＝與顯式 core **同 rank 層**；組內位置隨 mtime 重排（舊條目沉尾＝預期 fail-soft，非劣化） | 無 | rank 排序 |
| SM-3 | invalid rank 值 | `rank: urgent`（拼錯/自造） | 容錯＝一律視同 core，**永不進 errs**（拼錯不讓整池 gate FAIL——errs 留給 frontmatter 結構性違規；review F3 鎖定） | 無 | rank 排序 |
| SM-4 | 截斷發生 | 索引超 25K/200 行 | 尾端不載＝cold/舊條目；WARNING 仍附（可觀測不變） | 無 | fail-soft |
| SM-5 | 弧結案蒸餾 | 2.8 閘門/第三動 | 蒸餾後條目 rank 併同覆核（活躍弧 hot→終態降 core/cold） | 無 | rank 排序 |
| SM-6 | rank 通膨 | 寫入時全標 hot | 波段排序鍵覆核：hot 佔比軟指標（如 >1/3 標警示）＋降級建議 | 無 | 波段覆核 |
| SM-7 | 池副本 stale | 資產源改版後 regen | Stop hook 跳過＋留 `_regen-skipped-stale`（既有）；層 1 cmp/cp 原子刷新後恢復——本弧收案時對 ai-rules 池執行一次 | 無 | 部署同步 |
| SM-8 | mtime 全池重置 | 備份還原／遷機／無 `-p` 複製 | 第三鍵失效→退化 name 尾鍵序＝現狀（條目不丟、確定性保）；S2 註記備份保留 mtime（rsync -a） | 無 | —（已知限制） |

## 段落劃分原則

S1 code（generator 排序＋test）先行定義語義；S2 條文同步；S3 部署＋收尾。

---

## S1：generator rank 排序（code——TDD）

### Context
- **UC 引用**：實作「memory 索引 rank 排序」
- 資產源＝`skills/memory-audit/scripts/generate_index.py`（部署形態：副本進各池更名 `_generate_index.py`；Stop hook 信任邊界 cmp 副本 vs 資產源——**資產源與副本 bytes 必須一致**，改版後各池要刷新）
- **語義約束**：排序鍵三元組＝type 分組（既有）× rank（新）× 組內 mtime 尾序（新，同 rank 內冷舊沉底）；`rank` 為 frontmatter 可選欄（合法值 hot/core/cold，缺省＝core）；MEMORY.md 投影格式不變（one-line-per-entry）——只動順序
- **基礎設施盤點**：generator 既有結構（frontmatter 解析/gate/errs 路徑/atomic write）；**無既有排序函數**——排序隱含於 `sorted(here.glob("*.md"))`（:102，鍵＝檔名）＋分組按迭代序保序投影（:119-125）；`tests/test_memory_lifecycle.py` 既有錨（ASSET_REL parity/cross-layer；`os.utime` 顯式 mtime 先例 :196-197）
- **依賴錨點**：`generate_index.py` entries 迴圈（:102-112）與分組輸出段（:119-125）——排序插入點；`test_memory_lifecycle.py` ASSET_REL 區

### 核心實作要點
- `rank` 解析：frontmatter `metadata` 同層或 `metadata.rank`？——**實作時按既有 frontmatter 慣例定奪**（條目 frontmatter 現有 name/description/metadata.{node_type,type,originSessionId}——rank 放 top-level 或 metadata 內，test 釘住選擇）；缺省/invalid→core（invalid 處置見 SM-3）
- 排序函數：type 順序表（既有 ORDER）× RANK_ORDER（hot=0/core=1/cold=2）× 組內 `-mtime`（同 rank 內冷舊沉底）；同分穩定排序（fallback name——可重現）。**mtime 語義（review mF2/F4 合併）**：content-edit 觸碰即上浮＝預期 activity 信號；**重置源＝備份還原／遷機／無 `-p` 整池複製**（池不在 git 內——clone/checkout 不觸池）→第三鍵失效、退化 name 尾鍵序＝現狀，可接受非災難；備份保留 mtime（rsync -a／cp -p）註記進 S2
- **invalid rank 永不進 errs**（review mF3/GLM F3 鎖定）：一律視同 core 靜默容錯、至多 [INFO] 一行——errs 路徑＝壞條目**跳過投影**＋exit 1，會讓合法條目逐出索引＝召回斷裂（違 fail-soft 主張與 AIR-27 欄位級違規不擋投影教訓）
- gate/errs/generator 其餘行為零變更

### Pseudo Code

```python
RANK_ORDER = {"hot": 0, "core": 1, "cold": 2}  # 缺省/invalid -> core（永不進 errs）
TYPE_ORDER = {t: i for i, (t, _) in enumerate(ORDER)}  # review F5

def parse_rank(fm) -> int:
    raw = fm.get("rank") or fm.get("metadata.rank")  # 兩種落點皆支援（probe 實證可解析）
    return RANK_ORDER.get(str(raw).strip().strip("'\"").lower(), RANK_ORDER["core"])  # 巢狀引號剝除（review F6）

def sort_key(entry):
    return (TYPE_ORDER[entry.type], parse_rank(entry.frontmatter), -entry.mtime, entry.name)
# entries.sort(key=sort_key)  # 投影迴圈前；穩定可重現（name 尾鍵）
```

### 驗證策略（TDD）
- RED→GREEN：新增 test（tmp 池 fixture：三 type×三 rank×新舊 mtime 組合；**fixture 以 `os.utime` 顯式設 mtime 差**防 flaky——review F10，既有先例 :196-197）——斷言投影順序＝type 分組×rank 層×mtime 尾序；default core 相容（無 rank 條目與顯式 core 同層）；invalid rank→core；**`metadata.rank: "hot"` 巢狀帶引號 case 錨住引號剝除**（review mF6）；兩種落點（top-level rank／metadata.rank——沿 type 先例 :106 雙收，review F9）皆解析
- 既有 test 全綠（`test_memory_lifecycle.py` 全檔＋`test_sync_agents.py` 回歸）
- 真池冒煙：ai-rules 池（副本刷新後）`--check` 冪等、regen 輸出 diff 僅順序變化（無行增刪）

---

## S2：memory-audit skill 條文三處（docs）

### Context
- **UC 引用**：更新寫入端紀律／層 1／波段職責
- **語義約束**：與 S1 rank 語義同一詞源（hot/core/cold＋default core）；「定期整理排序鍵」取代任何「整理 MEMORY.md」語義（投影禁手寫）
- **依賴錨點**：`skills/memory-audit/SKILL.md` 層 1（generator 說明 :35）、寫入端紀律段、層 3 夜間收斂波 bullet

### 修改要點
1. **寫入端紀律**加一句：新條目 frontmatter 初判 `rank`（hot＝活躍弧/高頻教訓；core＝default；cold＝冷門/清候選）——一句裁量非機械，六問之後順手標
2. **層 1 generator 說明**補排序語義一行（type×rank×mtime；default core 不懲罰存量；rank 欄位位置與 S1 test 一致）
3. **夜間收斂波** bullet 加「排序鍵覆核」：rank 通膨檢查＋弧結案蒸餾時 rank 併同調整（活躍 hot→終態降 core/cold）；明示「定期整理＝整理排序鍵（frontmatter），MEMORY.md 是投影禁手排」；**hot 計數行寫死進波次① `--check` 盤點輸出**（可觀測先行——review F4）
4. `skills/CLAUDE.md:134` memory-audit 行——列舉補「rank 排序」一詞（若字數允許）

### 驗證策略（docs mode）
- `rg "rank" skills/memory-audit/SKILL.md` 三處命中；`rg "排序鍵"` 命中（整理排序鍵語義）
- `rg "整理 MEMORY.md|手排"` ——殘留掃（不該有手排語義殘留）
- 詞形與 generator test 常數一致（hot/core/cold）

---

## S3：部署同步＋收尾

### Context
- 資產源改版→各池副本 stale（Stop hook 會跳過並留標記）——本弧至少刷新 ai-rules 池（收案時驗證）；mosaic 池交既有刷新程序（層 1 cmp/cp——下次 audit 波或 handoff 帶）

### 修改要點
1. ai-rules 池副本原子刷新（cp .new→mv）＋regen＋`--check` 驗證；觀察投影順序變化（預期：現有條目全 default core＝組內 mtime 序——順序會變！這是預期行為，regen 後 diff 記錄）
2. 卡結案兩步＋第三動（本弧 memory 蒸餾）；/audit-test（S1 有 code——跑測試品質稽核：排序 test 的覆蓋對稱性）
3. EP 歸檔

### 驗證策略
- 刷新後 `uv run python _generate_index.py --check` exit 0；投影 diff 僅順序
- 卡 Done 雙 ref

---

## 整合策略

- baseline: 339e2c9
- S1 定義語義→S2 條文對齊→S3 部署驗證；rank 詞源單一在 S1 test（S2 引用）
- 跨池部署：ai-rules 池本弧刷；其他池（mosaic 等）走既有層 1 程序

## EP Review Record（dual-family 全收：muse job-mtqt5iwt 7 findings＋GLM fresh-eyes 10 findings——重複項互證）

| # | Finding | 嚴重度/信心 | 裁決 | 處置 |
|---|---------|------------|------|------|
| mF1 | EP 現況句漏 ORDER 首位 User 組 | L/高 | ✅採納 | 現況句補四組＋行號實證 |
| mF2 | mtime 排序副作用未載明 | M/高 | ✅採納（GLM F4 糾正重置源：池不在 git——備份還原/遷機非 checkout） | S1 mtime 語義句合併修正 |
| mF3 | invalid rank errs 選項矛盾 | M/高 | ✅採納（GLM F3 互證：errs＝跳過投影→召回斷裂） | 鎖定永不進 errs＋[INFO] 至多一行 |
| mF4 | hot 通膨無可觀測執行點 | L/中 | ✅採納 | hot 計數行寫死進波次①盤點輸出 |
| mF5 | pseudo-code TYPE_ORDER 未定義 | L/高 | ✅採納 | 補 enumerate(ORDER) 一行 |
| mF6 | 巢狀 frontmatter 引號剝除不對稱 | M/高 | ✅採納 | parse_rank strip 引號＋test 錨 case |
| mF7 | S1 殘留疑問句「或字串欄位」 | L/高 | ✅採納 | 刪除鎖定 mtime |
| F2 | 「排序函數」不存在（字母序＝sorted-glob 檔名鍵）＋錨點指空 | L/0.8 | ✅採納 | 錨點改 :102-112/:119-125＋現鍵註明 |
| F4 | mtime 重置源糾正（池不在 git）＋退化語義 | M/0.7 | ✅採納 | 併 mF2；SM-8 補場景 |
| F5 | SM-2「組內位置不劣化」不可測 | L/0.75 | ✅採納 | 改「同 rank 層；組內隨 mtime 重排」 |
| F6 | rules/context-management.md:28 寫入濃縮漏 rank | M/0.6 | ✅採納 | 變更面補（半句 rank 初判） |
| F7 | memory-audit description 觸發詞補 rank 取捨未記 | L/0.6 | ✅採納 | 變更面明記（description 補「rank」） |
| F9 | rank 雙落點沿 type 先例 | L/0.7 | ✅採納 | pseudo-code 雙收＋test 釘 |
| F10 | fixture mtime 同值 flaky 風險 | L/0.6 | ✅採納 | os.utime 顯式設差 |

（GLM F1/F3/F8 與 mF1/mF3/mF4 重複互證，不另列。）正面觀察：池已有 `feedback_memory-failsoft-importance-ordering.md` 預載同定案語義（type 組×rank×mtime、缺省 core）——EP 與之零衝突。

## 收尾步驟

（S3 全涵：部署驗證＋卡結案＋memory 蒸餾＋audit-test）
