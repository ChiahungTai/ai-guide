# S1 模板等值驗證 receipt（AC-1.1/1.2/1.3）

## AC-1.1 Existence
- [PASS] governance/manifest.toml 在場
- [PASS] governance/README.md 在場
- [FAIL] governance/install.py 在場
- [PASS] governance/registrations/cc.json 在場
- [PASS] governance/registrations/zcode.json 在場
- [PASS] governance/registrations/codex.toml 在場
- [PASS] manifest surfaces.hooks 節在場
- [PASS] manifest surfaces.rules 節在場
- [PASS] manifest surfaces.skills 節在場
- [PASS] manifest surfaces.agents 節在場
- [PASS] manifest surfaces.memory 節在場

## AC-1.2 模板渲染 == live 對應段落（逐字）
- [PASS] cc.json 渲染 == live hooks 子樹（semantic）
- [PASS] cc.json 渲染 == live hooks 子樹（byte）
- [PASS] zcode.json 渲染 == live hooks 子樹（semantic）
- [PASS] codex.toml 每一行皆存在於 live config（逐字） — missing=[]
- [PASS] codex.toml 獨立可解析且四 groups

## AC-1.3 manifest scripts vs live 註冊面對帳
- [PASS] live 註冊 scripts ⊆ manifest scripts — 多出=[]
- [PASS] manifest scripts ⊆ live 註冊（全在場，四家聯集） — 缺席=[]

| script | CC | ZCode | codex |
|---|---|---|---|
| hooks/block-memory-index-write.py | ✓ | ✓ | — |
| hooks/block-python-c-comment.py | ✓ | ✓ | ✓ |
| hooks/block-python-file-write.py | ✓ | ✓ | ✓ |
| hooks/codex_memory_path_deny.py | — | — | ✓ |
| hooks/compact-tail-inject.py | ✓ | — | — |
| hooks/memory-dirty-sensor.py | ✓ | — | — |
| hooks/memory-index-regen.py | ✓ | ✓ | — |
| hooks/memory-watch-seed.py | ✓ | — | — |
| hooks/memory-write-sensor.py | ✓ | ✓ | — |
| hooks/notification.sh | ✓ | — | — |
| hooks/stop-notification.sh | ✓ | ✓ | ✓ |
| hooks/zcode_agent_background_gate.py | — | ✓ | — |

hooks/ 內未入 manifest 的腳本（工具/lib，正當缺席）：['memory_hook_common.py', 'setup-memory-symlinks.sh', 'verify-memory-topology.sh']

## 收編待辦（收尾步驟 2 處理）
- `hooks/zcode-registration.json` 內容已由 `governance/registrations/zcode.json` 吸收；原檔刪除＋`hooks/AGENTS.md` 指針改址歸收尾步驟（本段 S1 不動，零重複源終態待收尾）。

**總判讀：FAIL: governance/install.py 在場**
