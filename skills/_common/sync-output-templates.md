# Sync 輸出格式模板

> **載入時機**: 僅在 `/instruction-sync` 執行時按需讀取。本檔案定義 6 組輸出格式模板，供 sync 命令產出標準化報告。

---

## 模板 1: 單檔案檢查輸出

```
## instruction 檔同步檢查報告

檔案: /path/to/AGENTS.md（legacy CLAUDE.md 僅轉移檢查，範例）

### 程式碼一致性檢查

#### 檔案路徑引用
- ✅ src/core/engine.py
- ✅ src/core/config.py
- ❌ src/legacy/old_module.py（檔案不存在）

#### 類別/函數簽名
- ✅ DataEngine
- ✅ process_data()
- ⚠️  validate_input()（簽名已變更：現在需要 config 參數）

#### 行為描述
- ⚠️  "DataEngine 會自動重連" → 實際程式碼沒有自動重連邏輯

#### 語義正確性 spot-check
- ✅ "<behavior> 使用 <logic>" → 實際 <file>.py 確實如此
- ⚠️ "<Class> 用 <claimed_metric> 排序" → 實際 metric="<actual>"（語義不準確，來源: <file>.py:<行號>）

### 涵蓋性檢查

#### 重要模組檢查
掃描目錄: /path/to/src/
- ✅ src/core/ 的 instruction 檔
- ⚠️  src/api/（未記錄在主文檔）
- ⚠️  src/utils/（未記錄在主文檔）

#### 公開 API 檢查
發現 N 個公開函數，文檔記錄 M 個
- ⚠️  遺漏: helper_function(), validate_config(), get_status()

### 元資訊檢查（整合 /instruction-clean）
- ❌ 發現版本號: vX.Y
- ❌ 發現更新日期: YYYY-MM-DD
- ✅ 可保留: 符號連結說明、專案概述、繼承關係
- 💡 建議執行 `/instruction-sync --clean` 或 `--all` 清理

### 蒸餾評估（整合 /instruction-clean --distill，--all 選項）
- ✅ 精華: N 個核心原則、M 個架構圖
- ❌ 冗餘: K 個過時範例、L 個重複說明
- ⚠️ 灰色地帶: P 個（預設保留）
- 💡 建議執行 `/instruction-sync --all` 完整處理

### 內部品質檢查

#### 自洽性 [✅/⚠️/❌]
[發現的問題或「通過」]

#### 矛盾性 [✅/⚠️/❌]
[發現的問題或「通過」]

#### 順序 [✅/⚠️/❌]
[發現的問題或「通過」]

#### 自包含 [✅/⚠️/❌]
[發現的問題或「通過」]

#### 精準度 [✅/⚠️/❌]
[發現的問題或「通過」]

### Signal/Noise Ratio 評估

#### High Signal 內容
- 設計理由: N 處
- 架構約束: N 處
- 失敗教訓: N 處

#### Low Noise 內容
- API 簽名: N 處
- 參數表: N 處
- 完整範例 >5 行: N 處

#### 評估結果
- Signal/Noise Ratio: [X]% [✅/⚠️/❌]
- 💡 建議動作: [保持現狀 / 執行 /instruction-clean --distill]

### 導航有效性檢查

#### 概念→符號連結
抽查概念: [概念A, 概念B, 概念C]
- ✅ [概念A]: → `ClassName`（路徑由 LSP 解析）
- ❌ [概念B]: 無 symbol 指引（導航缺口）
- ✅ [概念C]: → `function_name()`（路徑選用）

#### 職責→符號對應
- ✅ [職責A]: 指向 `ClassName`
- ⚠️ [職責B]: 有描述但無 symbol 指引

#### 跨模組依賴導航
- ✅ [依賴A]: 具體到 `other_module.ClassName`
- ❌ [依賴B]: 只寫模組名，缺少 class/function 指引

#### 資料流可追蹤性 [✅/⚠️/❌/N/A]
[多步驟流程的 step 間銜接驗證結果，無流程標 N/A]

#### 導航 Decoder Test
- Q1「修改 X 核心符號是什麼？」: [✅ 可回答 / ❌ 無法定位]
- Q2「Y 這個概念在哪裡實作？」: [✅ 可回答 / ❌ 無法定位]
- Q3「Z 的上游資料從哪來？」: [✅ 可回答 / ❌ 無法定位]

### 總結
- 程式碼一致性: X%
- 涵蓋性: Y%
- 導航有效性: Z% [✅/⚠️/❌]
- 內部品質: W/100
- 元資訊: 需要清理

建議優先處理：
1. 移除不存在的檔案引用
2. 更新變更的 API 簽名
3. 修正語義不準確的描述（spot-check 發現）
4. 補充導航缺口（概念→符號連結缺失處）
5. 補充遺漏的模組說明
6. 修正內部品質問題
7. 清理元資訊
```

---

## 模板 2: Sync Summary（結構化結論，供 daily-maintain 消費）

> **設計理念**：保留 sync 的完整人類可讀報告（Layer 1），同時在報告末尾附加結構化結論（Layer 2），讓 daily-maintain Phase 4 可以直接消費 sync 的發現。

```yaml
---

## Sync Summary

module: {module_name}
inconsistencies:
  - type: outdated_description
    location: <instruction-file>:{行號}   # AGENTS.md:42 或 CLAUDE.md:15
    detail: "描述的 <OldClass> 已重構為 <NewClass>"
    confidence: high
    source: <old_module>.py:{行號}
  - type: missing_reference
    location: <instruction-file>:{行號}
    detail: "新模組 <new_module>.py 未在 instruction 檔提及"
    confidence: high
    source: <new_module>.py:1
  - type: signature_changed
    location: <instruction-file>:{行號}
    detail: "evaluate() 新增參數 strict_mode"
    confidence: high
    source: <file>.py:{行號}
coverage_gaps:
  - file: new_module.py
    location: <instruction-file>:(未提及)
    detail: "新增的 .py 檔案未記錄"
metadata_issues:
  - type: version_number
    location: <instruction-file>:{行號}
navigation_gaps:
  - concept: "{概念名稱}"
    location: <instruction-file>:{行號}
    detail: "提到概念但無 symbol 指引"
    confidence: high
  - dependency: "{跨模組依賴}"
    location: <instruction-file>:{行號}
    detail: "只寫模組名，缺少具體 class/function 指引"
    confidence: medium
signal_noise:
  ratio: 65%
  status: acceptable
  low_noise_items: 3
sync_score: {X}%
needs_update: true/false
```

---

## 模板 3: Sync Summary ACTION（可執行的 instruction 檔修改）

> **設計理念**：sync 不只報告問題，還要產出可直接 copy-paste 的修改。只有 High Signal 項目（導航缺口、語義錯誤、設計決策缺失）才產出 ACTION。Low Noise 項目（API 簽名、參數值）跳過。

```yaml
actions:
  - type: add_navigation
    target: "<instruction-file>:{章節名}"
    concept: "{概念名稱}"
    text: |
      - **{概念描述}** → `ClassName`
    signal_level: high
    reason: "導航缺口：概念無程式碼指引"

  - type: fix_description
    target: "<instruction-file>:{行號}"
    old: "{現有不正確文字}"
    new: "{修正後文字}"
    signal_level: high
    reason: "語義不準確"
    source: "file.py:{行號}"

  - type: add_design_decision
    target: "<instruction-file>:{章節名}"
    text: |
      - **{設計決策名稱}**：{一句話理由} → `ClassName`
    signal_level: high
    reason: "設計決策缺失（從程式碼猜不到）"

  - type: remove_noise
    target: "<instruction-file>:{行號}"
    text: "{應移除的 Low Noise 內容}"
    signal_level: low
    reason: "API 簽名/參數表，從程式碼可推導"
```

---

## 模板 4: 遞歸同步檢查報告範例

遞歸輸出格式: [recursive-output.md](./recursive-output.md)

```
## 遞歸同步檢查報告

目錄: /path/to/project
發現 instruction 檔: 6 個（AGENTS.md 為主；legacy CLAUDE.md 轉移檢查）

### Critical（專案根目錄）
**檔案**: AGENTS.md（source）
- 程式碼一致性: ✅ 90%
- 涵蓋性: ⚠️ 75%
- 內部品質: ⚠️ 85/100（2 個矛盾問題）
- 元資訊: ❌ 需要清理（版本號、日期）
- 蒸餾評估: ⚠️ 3 個冗餘、2 個灰色地帶

**檔案**: CLAUDE.md（legacy，轉移檢查）
- 遷移候選標記: ✅ 已列入報告
- 元資訊: ✅ 乾淨

### High（主要模組）
**檔案**: src/AGENTS.md
- 程式碼一致性: ✅ 95%
- 涵蓋性: ✅ 90%
- 內部品質: ✅ 95/100
- 元資訊: ✅ 乾淨
- 蒸餾評估: ✅ 精華為主

**Sub-doc**: src/condition_system.md（說明文檔）
- 程式碼一致性: ⚠️ 85%（1 個型別引用過時）
- 內部品質: ✅ 95/100

**Sub-doc**: src/<design_doc>.md（設計文檔）
- ⏭️ 跳過（設計文檔，不檢查程式碼一致性）

**檔案**: src/core/AGENTS.md
- 程式碼一致性: ⚠️ 80%（2 個 API 簽名變更）
- 涵蓋性: ✅ 85%
- 內部品質: ✅ 90/100
- 元資訊: ❌ 有版本號
- 蒸餾評估: ⚠️ 1 個過時範例

### Medium（子模組）
**檔案**: src/core/utils/AGENTS.md
- 程式碼一致性: ✅ 100%
- 涵蓋性: ⚠️ 70%（遺漏 helper 函數）
- 內部品質: ⚠️ 80/100（術語不一致）
- 元資訊: ✅ 乾淨

### Low（測試）
**檔案**: tests/AGENTS.md
- 程式碼一致性: ✅ 95%
- 涵蓋性: ✅ 90%
- 內部品質: ✅ 100/100
- 元資訊: ✅ 乾淨

### 整體統計
- instruction 檔數量: 6 個
- 平均程式碼一致性: 90%
- 平均涵蓋性: 82%
- 平均內部品質: 90/100
- 需要清理: 2 個
- 需要蒸餾: 1 個

建議執行: `/instruction-sync --recursive --clean`

> 當 ⚠️ 項目 ≥ 3 個時，建議執行 `/instruction-sync {module} --all` 進行完整 12 角度深度驗證。
```

---

## 模板 5: 執行清理後輸出

```
## instruction 檔同步檢查 + 清理完成

檔案: /path/to/AGENTS.md（legacy CLAUDE.md 僅轉移檢查，範例）

### ✅ 檢查完成
- 一致性: X%（已報告問題）
- 涵蓋性: Y%（已報告遺漏）

### 清理完成
- 移除版本號: vX.Y
- 移除更新日期: YYYY-MM-DD
- 移除歷史章節: 無
- 移除統計資訊: 無

### 處理結果
- 原始行數: N 行
- 清理後: M 行 (-Z%)
- 備份檔案: AGENTS.md.backup 或 CLAUDE.md.backup
```

---

## 模板 6: --all 完整處理輸出

```
## instruction 檔完整處理（檢查 + 清理 + 蒸餾）

檔案: /path/to/AGENTS.md（legacy CLAUDE.md 僅轉移檢查，範例）

### 步驟 1: 同步檢查
- 一致性問題: N 項
- 涵蓋性遺漏: M 項
- 元資訊問題: K 項

### 步驟 2: 清理元資訊
- 移除版本號、日期
- 移除統計資訊
- X 行 → Y 行

### 步驟 3: 蒸餾精簡
- 識別精華: N 個核心原則
- 移除冗餘: M 個實作細節
- Y 行 → Z 行

### 最終結果
- 原始: X 行
- 處理後: Z 行 (-P%)
- 備份: AGENTS.md.backup / CLAUDE.md.backup (原始)
- 備份: AGENTS.md.pre-distill.md / CLAUDE.md.pre-distill.md (清理後)
```
