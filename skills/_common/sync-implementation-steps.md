# Sync 實作步驟詳細定義

> **載入時機**: 僅在 `/instruction-sync` 執行時按需讀取。本檔案定義步驟 0.5-10.5 的詳細實作邏輯。

---

## 步驟 0.5: Snapshot 載入

> **觸發條件**：專案根目錄存在 `.project-snapshot.json` 時執行。無 snapshot 時跳過，所有 snapshot 相關步驟降級為獨立模式。

從 `.project-snapshot.json` 載入預計算的知識快照，供後續步驟使用：

```
1. 偵測專案根目錄是否有 .project-snapshot.json
2. 如果存在：
   a. 讀取 JSON
   b. 驗證 schema_version >= 5（否則視為舊格式，建議重新掃描）
   c. Staleness 檢查：如果 scan_timestamp 超過 24 小時，
      記錄警告 "[WARN] snapshot is stale, recommend /scan-project first"，
      不阻塞後續步驟（資料可能過時但仍有參考價值）
   d. 提取以下的資料供後續步驟使用：
      - dep_graph.modules + dep_graph.edges → 步驟 1.5 依賴鏈擴展（精確取代 naive grep）
      - findings → 步驟 10.5（預計算的 X-cap-path/X-ep-ready/X6 問題）
      - fingerprint → 變化偵測（counts + hashes）
3. 如果不存在：記錄 "running without snapshot"，後續步驟用傳統方式
```

**其餘資訊（Capabilities、Kanban、instruction 檔（AGENTS.md/CLAUDE.md）內容）由 LLM 直接讀取檔案系統，不經 snapshot。**

**Snapshot 資料消費對照**：

| 步驟 | 消費的 snapshot 資料 | 取代的傳統方式 |
|------|---------------------|---------------|
| 1.5 依賴鏈擴展 | `dep_graph.edges[]` | naive grep import chain |
| 4 驗證一致性 | LLM 直接 Read instruction 檔 | 逐一 Read AGENTS.md/CLAUDE.md |
| 10.5 交叉驗證 | `findings[]` + LLM 直接讀取 Capabilities/backlog 卡 | 無（新增能力） |

---

## 步驟 1: 遞歸發現 instruction 檔

遞歸發現邏輯: [recursive-discovery.md](./recursive-discovery.md)

---

## 步驟 1.5: 依賴鏈擴展

> **觸發條件**：目標目錄中有 `git diff` 變更的 `.py` 檔案時執行。或使用 `--changed-since` 參數。

從變更的程式碼出發，追蹤 import 鏈，將消費端目錄的 instruction 檔加入檢查清單：

```
1. git diff --name-only 提取變更的 .py 檔案
   - 無 --changed-since → git diff HEAD
   - 有 --changed-since → git log --since="$SINCE" --name-only --pretty=format:
2. 對每個變更檔案，搜尋消費端：
   - 有 snapshot → 直接查 edges[]（精確、快速）
   - 無 snapshot → Grep 搜尋整個專案中 import 該模組的檔案
3. 從消費端檔案路徑推導其所屬目錄
4. 檢查消費端目錄是否有 instruction 檔（AGENTS.md/CLAUDE.md）→ 有的話加入檢查清單
5. 去重，合併到步驟 1 發現的 instruction 檔清單
```

**--changed-since 增量模式**：

當指定 `--changed-since` 時，步驟 1 只掃描 git 變更涉及的目錄，而非全部目錄。這大幅縮小檢查範圍，適合 daily-maintain 的 Phase 1 使用。

增量模式分兩個 Phase 收集待檢查的 instruction 檔，合併後執行 sync：

```
Phase A: Code 變更 → 對應目錄的 instruction 檔
  1. git log --since="$SINCE" --name-only --pretty=format: -- "*.py"
  2. 對每個變更 .py，映射到所屬模組目錄（取 library root 下一層目錄）
  3. 檢查該目錄是否有 instruction 檔 → 加入檢查清單
  範例：src/data/parsing.py 變更 → 檢查 src/data/AGENTS.md 或 src/data/CLAUDE.md

Phase B: instruction 檔本身被直接修改
  1. git log --since="$SINCE" --name-only --pretty=format: -- "**/AGENTS.md" "**/CLAUDE.md"
  2. 這些 instruction 檔直接加入檢查清單

合併：
  1. Phase A + Phase B 去重
  2. 步驟 1.5 的依賴鏈擴展仍然執行（確保消費端 instruction 檔也被檢查）
  3. 對最終清單中的每個 instruction 檔執行 sync 檢查
```

**Phase A 是核心價值**：code 變了但 instruction 檔沒跟著更新，正是 sync 要抓的問題。不要跳過。

---

## 步驟 1.6: Sub-doc 擴展

> **觸發條件**：instruction 檔中引用了同目錄或相鄰目錄的 `.md` 子文件時執行。

從 instruction 檔的 markdown link 引用出發，發現子文件並分類，將「說明文檔」加入檢查清單：

```
1. 從 instruction 檔提取所有 markdown link 引用的 .md 檔案
   - 格式: [描述](path/to/doc.md) 或 [描述](doc.md)
   - 排除外部 URL（http/https）
   - 排除 @ transclusion（跨 harness 的 AGENTS.md 禁用 `@`——CC 專屬機制；僅 legacy CLAUDE.md 展開）
2. 驗證引用的 .md 檔案是否存在
3. 分類為「說明文檔」或「設計文檔」：
   - 說明文檔：描述 API、資料結構、流程、call stack → 加入檢查清單
   - 設計文檔：描述概念、提案、未來計畫 → 跳過
4. 合併到檢查清單，標記為 sub-doc（優先級同父 instruction 檔）
```

**Sub-doc 檢查範圍**：對說明文檔執行角度二（程式碼一致性）和角度六（內部品質），不重複涵蓋性檢查（由父 instruction 檔統一負責）。

---

## 步驟 2: 掃描程式碼結構

```bash
# 識別重要檔案和目錄
fd -e py -e pyx -e pxd . $TARGET_DIR | head -20
fd -t d . $TARGET_DIR --max-depth 2

# 掃描公開 API
rg "^def " -t py $TARGET_DIR
rg "^class " -t py $TARGET_DIR
```

---

## 步驟 3: 提取文檔引用

```python
# 從 instruction 檔提取引用
def extract_references(content: str) -> dict:
    """提取文檔中的引用"""

    references = {
        "file_paths": [],      # 檔案路徑
        "class_names": [],     # 類別名稱
        "function_names": [],  # 函數名稱
        "modules": [],         # 模組名稱
    }

    # 提取檔案路徑
    import re
    file_patterns = r'`[\w/.-]+/[\w/.-]+\.(py|yaml|toml)`|`[\w/.-]+/`'
    references["file_paths"] = re.findall(file_patterns, content)

    # 提取類別名稱
    class_patterns = r'\*\*[\w]+\*\*|`[\w]+`[\s]*類|class\s+[\w]+'
    references["class_names"] = re.findall(class_patterns, content)

    # 提取函數名稱
    func_patterns = r'`[\w]+\(\)`|function\s+[\w]+|函數\s+[\w]+'
    references["function_names"] = re.findall(func_patterns, content)

    return references
```

---

## 步驟 4: 驗證一致性

```bash
# 驗證檔案路徑
for path in "${references[file_paths]}"; do
    if [ -f "$path" ]; then
        echo "✅ $path"
    else
        echo "❌ $path 不存在"
    fi
done

# 驗證類別/函數
for name in "${references[class_names]}"; do
    if rg -q "class $name" -t py $TARGET_DIR; then
        echo "✅ $name"
    else
        echo "⚠️  $name 未找到"
    fi
done
```

---

## 步驟 5: 命令涵蓋性檢查

機械性檢查（用 `fd` + `rg`，避免 shell 變數與 `sed`）：

1. 列出所有命令檔：`fd -e md . <target-dir> --exclude AGENTS.md --exclude CLAUDE.md`
2. 對每個檔推導 skill 名（目錄名：`instruction-clean/SKILL.md` → `/instruction-clean`；他專案 `worktree/status.md` 之類 → `/worktree:status` 推導）—— 以具體檔名推導，不用 `$TARGET_DIR` 變數
3. 逐個驗證是否記錄：`rg -q "<命令名稱>" <target-instruction-file>`（找到 = ✅ 已記錄，未找到 = ❌ 未記錄；target-instruction-file 為 AGENTS.md 或 CLAUDE.md）

---

## 步驟 6: 程式碼涵蓋性檢查

```bash
# 如果目錄中有程式碼檔案，檢查是否被記錄
CODE_FILES=$(fd -e py -e pyx -e pxd . $TARGET_DIR)
if [ -n "$CODE_FILES" ]; then
    echo ""
    echo "### 程式碼檔案涵蓋性檢查"
    for code_file in $CODE_FILES; do
        filename=$(basename "$code_file")
        if rg -q "$filename" "$INSTRUCTION_FILE"; then
            echo "✅ $filename 已記錄"
        else
            echo "⚠️  $filename 未記錄"
        fi
    done
fi
```

---

## 步驟 7: 清理元資訊（--clean 選項）

```bash
# 呼叫 /instruction-clean 功能
# 移除版本號、日期、統計等元資訊
```

---

## 步驟 8: 蒸餾（--all 選項）

```bash
# 呼叫 /instruction-clean --distill 功能
# 蒸餾精簡 instruction 檔
```

---

## 步驟 9: 內部品質檢查（品質層，--quality）

### 五維度檢查流程

**9.1 自洽性檢查**
- 術語使用是否統一（相同概念是否用相同詞彙）
- 前後描述是否一致
- 定義與使用是否吻合

**9.2 矛盾性檢查**
- 是否存在互相矛盾的陳述
- 規則之間是否有衝突
- 範例與說明是否矛盾

**9.3 順序檢查**
- 章節編號是否連續
- 標題層級是否正確（`#` → `##` → `###`，不跳級）
- 內容組織是否合理

**9.4 自包含檢查**
- 引用的檔案/路徑是否存在（已在前面的步驟驗證）
- 外部依賴是否可獲取
- 讀者是否需要額外資訊才能理解

**9.5 精準度檢查**
- 技術描述是否正確
- 程式碼範例是否可執行
- 連結是否有效

---

## 步驟 10: 導航有效性檢查（核心層，最重要）

> 導航是 sync 最核心的檢查。其他步驟發現的問題（路徑不存在、簽名不對）最終都轉化為導航修復。

```
1. 從 instruction 檔抽取 3-5 個關鍵概念
2. 驗證每個概念是否有指向具體檔案、class 或 function 的導航路徑
3. 對照職責描述與檔案結構，驗證每項職責有對應的檔案指引
4. 檢查跨模組依賴是否具體到 class/function（不只是模組名）
5. 對多步驟流程驗證 step 間 input/output 可追蹤性（無流程標 N/A）
6. 執行導航 Decoder Test：不查源碼，嘗試回答 3 個導航問題
7. 對每個導航缺口產出 ACTION 修改建議（見 Sync Summary ACTION）
```

---

## 步驟 10.5: 交叉驗證（vs Snapshot）

> **觸發條件**：`.project-snapshot.json` 存在時執行。無 snapshot 時跳過。

消費步驟 0.5 載入的 snapshot 資料 + LLM 直接讀取，執行跨 artifact 交叉驗證（角度 10-11）。

```
1. 消費 findings[] 中的預計算結果：
   - X-cap-path 問題：Capabilities 入口路徑不存在 → 標記為 important
   - X-ep-ready 問題：To Do/In Progress 卡片引用的 EP 不存在 → 標記為 important
   - X6 問題：模組缺 instruction 檔 → 轉為角度 11（模組覆蓋缺口）

2. 角度 10：dep-graph 矛盾（X1）
   - LLM 直接讀取 instruction 檔中的 "Does NOT depend on" 段落
   - 比對 dep_graph.edges[] 中是否有對應的 import edge
   - 有矛盾 → 標記 [X1] critical

3. 角度 11：模組覆蓋缺口（X6）
   - 遍歷 dep_graph.modules[]（file_count >= 3）
   - LLM 直接檢查目錄中是否有 instruction 檔（AGENTS.md 或 CLAUDE.md）
   - 缺少 instruction 檔 → 標記 [X6] important
```

**輸出格式**：

```markdown
### Cross-Validation (vs Snapshot)

- [X1] data/AGENTS.md 宣告 "Does NOT depend on strategies" 但 dep_graph.edges 有 data→strategies
- [X6] Module 'services' (12 files) 缺少 instruction 檔（AGENTS.md）
- [X-cap-path] Capabilities entry path 'runner.py' does not exist (in <package>/data/AGENTS.md)
```
