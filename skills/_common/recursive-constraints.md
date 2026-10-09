# 遞歸處理約束

### 基本約束
- **使用 fd**: 正確發現所有 instruction 檔（`fd "(AGENTS|CLAUDE)\.md" <dir>`，預設排除隱藏檔與 .gitignore；AGENTS.md 為主、CLAUDE.md legacy）
- **分類處理**: 按重要性分類（Critical/High/Medium/Low），優先處理關鍵文檔
- **順序處理**: 從根目錄到深層模組，按重要性順序處理
- **進度報告**: 每處理一個檔案報告進度
- **錯誤處理**: 單一檔案失敗不影響其他檔案
- **可還原性**: 所有操作都可透過備份還原

### 分類標準

| 分類 | 說明 | 範例路徑 |
|------|------|---------|
| **Critical** | 專案根目錄 | `AGENTS.md`（legacy 專案另可能有 `CLAUDE.md`） |
| **High** | 主要模組 | `src/AGENTS.md`, `core/AGENTS.md` |
| **Medium** | 子模組 | `src/core/utils/AGENTS.md` |
| **Low** | 測試、範例、文檔 | `tests/AGENTS.md`, `examples/AGENTS.md` |
