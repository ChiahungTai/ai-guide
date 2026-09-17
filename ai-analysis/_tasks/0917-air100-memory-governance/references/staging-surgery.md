# staging 形態 (a) symlink 手術紀錄（AIR-100 S-D；2026-09-17 07:55）

## before（手術前現值）

```
~/.zcode/cli/memories/projects/ai-guide-91ff86777c287082/memory
  → symlink → /Users/ctai/.claude/projects/-Users-ctai-Github-ai-guide/memory
  → symlink → /Users/ctai/Github/ai-guide/.agents/memory   （池主體）
```
（雙跳：ZCode 原生 memory 目錄指 CC 側目錄、CC 側再指池——ZCode auto-memory 背景寫入者經此鏈直達池＝SM-6 污染路徑）

## 手術（僅拆 ZCode 側；CC 側 symlink 不動）

1. `rm /Users/ctai/.zcode/cli/memories/projects/ai-guide-91ff86777c287082/memory`（僅拆 symlink）
2. `mkdir -p /Users/ctai/.zcode/cli/memories/projects/ai-guide-91ff86777c287082/memory`（原地建真實目錄＝staging）

## after（手術後驗證）

| 檢查 | 命令 | 結果 |
|---|---|---|
| ZCode memory 非 symlink | `readlink ~/.zcode/cli/memories/projects/ai-guide-91ff86777c287082/memory` | exit 1（非 symlink） |
| 真實空目錄在場 | `ls -la .../memory` | `drwxr-xr-x@ 2`（空目錄） |
| 池不受手術影響 | `ls /Users/ctai/Github/ai-guide/.agents/memory/MEMORY.md` | 在場（POOL-INTACT） |
| CC 側 symlink 未動 | `readlink ~/.claude/projects/-Users-ctai-Github-ai-guide/memory` | 仍指 `.agents/memory`（CC pull 面不變） |

## 理由（落地當日記錄——EP S-D 要求）

1. **P0-3 已驗證無痛**：user 已於 0917 UI 關閉 ZCode auto-memory（v3.6.4+ 預設關、僅新 session 生效）——新 session 開場注入回退原生 index、背景寫入者停寫（P0-3 觀察項）；拆 symlink 後即使 auto-memory 重開，寫入落本真實目錄（staging），池 HEAD 保持 approved。
2. **形態 (a) 勝出**：相對 (b)（symlink 改指 `.agents/memory-auto/`）——(a) 不新增 repo 內 gitignored 目錄、不動 wt-open/close 池 symlink 敘述連帶；staging 即 ZCode 原生目錄，晉升＝pull 逐條六問重寫（AC-D5 程序，memory-audit skill 承載）。
3. **rollback**：依 before 現值重建即可——`ln -s ~/.claude/projects/-Users-ctai-Github-ai-guide/memory ~/.zcode/cli/memories/projects/ai-guide-91ff86777c287082/memory`（先 rm 本真實目錄）。
