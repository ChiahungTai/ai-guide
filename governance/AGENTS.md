# governance/ — 跨 harness 治理安裝套件

> 五部署面（rules bundle／skills 分發／hooks 註冊／agents registry／memory governance＋monitor）的**安裝面單一源**（AIR-116）。完整 README＝[README.md](README.md)；本檔是導航索引（AIR-164 coverage 補齊）。

## 構件

- **`install.py`** — 唯一安裝入口：`uv run python governance/install.py --surface {rules,skills,hooks,agents,memory,monitor,all} [--dry-run|--uninstall|--check|--verify]`（四 flag 兩兩互斥；Python 地板 3.11+ 由檔頭守衛把關）。動詞紅線：本套件只說 **install/uninstall**——rules bundle 的「部署」是另一條線，installer 對它只 wrap 不擁有。
- **`manifest.toml`** — 唯一期望定義（五面安裝語義＋home symlink 母鏈＋`[bootstrap_cli]` 穩定契約投影）；`install.py` 只消費不擴 schema，`--check` 以其為模板。改安裝行為先改 manifest，再對齊 installer。
- **`registrations/`** — active hooks 模板 `grok.json`／`zcode.json`／`codex.toml`；Muse 併 memory plugin 面，`cc.json`＋`cc-allowlist.json` 留作 dormant 歷史資產。註冊面**契約源**＝`manifest.toml` 的 registrations：grok 獨佔檔整檔 render、ZCode 只 merge `hooks:` 子樹（mcp/plugins 逐鍵不變）、Codex 按 TOML group merge；模板內容即期望態，接線更新先對齊模板與 manifest，再由 installer 安裝。
- **`conventions.md`** — 套件內慣例。

## 不做什麼（邊界）

- **閘行為本體零改動**：`hooks/` scripts、`muse-plugins/memory-governance/`、bundle 內容、`sync_agents.py` 生成邏輯——installer 只 wrap（呼叫封裝、輸出透傳、退出碼串接），不重寫不取代。
- **bridge repo 不在收編面**：delegate-bridge（`~/Github/delegate-bridge`）自帶安裝/marketplace 面，本套件不管。
- **sc-router 不在收編面**：非本套件五面範圍，勿掛進 manifest。
