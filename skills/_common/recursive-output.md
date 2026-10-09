# 遞歸模式輸出格式

```
## 遞歸{操作}報告

目錄: /path/to/project
發現 instruction 檔: N 個（AGENTS.md 為主；legacy CLAUDE.md 標記轉移檢查，範例）

### 🔴 Critical（專案根目錄）
**檔案**: AGENTS.md
- {狀態描述}

### 🟠 High（主要模組）
**檔案**: src/AGENTS.md
- {狀態描述}

**檔案**: src/core/AGENTS.md
- {狀態描述}

### 🟡 Medium（子模組）
**檔案**: src/core/utils/AGENTS.md
- {狀態描述}

### 🟢 Low（測試）
**檔案**: tests/AGENTS.md
- {狀態描述}

### 📊 整體統計
- instruction 檔數量: N 個
- {統計項目 1}: X 個
- {統計項目 2}: Y 個

建議執行: `{命令} --recursive`
```

### 輸出範例處理進度

```
[1/N] 🔴 AGENTS.md（根目錄 source）
   ✓ X 行 → Y 行 (-Z%)
   ✓ 備份: AGENTS.md.backup

[2/N] 🔴 CLAUDE.md（legacy，轉移檢查標記）
   ✓ X 行 → Y 行 (-Z%)
   ✓ 備份: CLAUDE.md.backup

[3/N] 🟠 src/AGENTS.md（主要模組）
   ✓ X 行 → Y 行 (-Z%)
   ✓ 備份: src/AGENTS.md.backup
```
