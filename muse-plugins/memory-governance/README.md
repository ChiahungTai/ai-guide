# muse-memory-governance

user-scope muse plugin：把 muse 的 `add_memory` / `edit_memory` 寫入導流到 repo 內
`.agents/memory-inbox/`（atomic 代存＋deny），由 consolidation 站（memory-audit skill
「Inbox 消費」節）統一入池。機制出處 AIR-54（per-repo `.muse/hooks.json` 閘），
AIR-79 升級為 user-scope plugin——裝一次，所有帶 marker 的 repo 生效。

## Gate 語義（marker 三態）

per-repo marker 檔＝`.agents/memory-governance.json`：

| marker 狀態 | 行為 |
|---|---|
| absent | 不攔（native write，零攔截零落地） |
| `{"protocol": 1}`（JSON number 等於 1——lexical `1.0`/`1e0` 同數可接受） | 導流 inbox＋deny |
| 其餘一切（parse 失敗／缺欄／`0`／`-1`／`"1"`／`null`／`true`／`false`／`>1`） | deny＋報錯，**不落地** |

- governed repo 內閘的任何內部故障（jq 故障、寫入失敗）→ deny（fail-closed）。
- jq 缺失且偵測到 memory tool 特徵 → 保守 deny，reason 帶修復指引。
- inbox 路徑任一已存在段是 symlink → deny 不落地（containment 防護）；尚未存在的段由閘自建。
- 非 memory 工具一律 self-filter 早退（plugin hooks 無 matcher，腳本自濾 `tool_name`）。
- legacy 讓位語義已移除（2026-09-14 codex advisory：legacy 退役後讓位路徑＝repo 可控 hooks.json 誘導的繞閘面；plugin 為唯一閘、無讓位路徑）。

## Install（user-scope）

```
muse plugins install <path-to>/muse-plugins/memory-governance --scope user
muse plugins approve <id>
muse plugins list
```

- `approve` 是 per-capability 動作；install 後 `trust:"user-local"` **不等於** approved，
  未 approve 的 capability 不會 fire（muse 對 hook 缺席 fail-open——activation 層缺口
  由 consolidation 異常篩＋daily-maintain 直寫偵測把守）。
- manifest 為 nested `.muse-plugin/plugin.json`（exactly-one，雙 manifest 會被拒）。

## Per-repo opt-in marker

```
mkdir -p .agents
printf '{"protocol": 1}\n' > .agents/memory-governance.json
```

marker 進版控（repo 治理宣告）。worktree 只見所屬 branch checkout 的 marker——未 commit
marker 的 worktree 視為 ungoverned。

## 固定安裝點維護（已退役）

此維護流服務 per-repo launcher 時代（2026-09-14 退役）。現行寫入閘由 plugin cache
承載，版本面操作＝`muse plugins update`＋重新 approve（見運維節）；`~/.local/share/muse-memory-governance/`
殘留安裝點可刪。

## Health check

- `muse plugins list`：plugin 在冊（list **不暴露 per-capability approve 狀態**，其
  "hooks require review" warning 是常駐雜訊非訊號——approval 面看下方「運維（operations）」節
  的 `inspect --json` assert＋行為 smoke）。
- marker：`.agents/memory-governance.json` 存在且 `protocol` 為 JSON number 1。
- **跨副本一致性**：source home（`muse-plugins/memory-governance/`）與 plugin cache 兩份核心以
  reinstall 對齊；不一致＝行為依入口依賴的副本版本——先對齊再除錯。
- 行為 smoke：governed repo 呼叫 `add_memory` 應得 deny＋inbox receipt 檔；
  ungoverned repo 應零攔截；marker 改壞後同呼叫應 deny 且無新檔。

## 運維（operations）

- **每次 `muse plugins update` 後必須重新 `muse plugins approve <id>`**——approve 綁
  `definition_hash`（含 script 內容）：content update → hash 變 → runtime `status=modified`
  → hook 停火，形成 fail-open 窗口（窗口內記憶寫入 native 直寫 canonical），重釘即恢復。
  形態是「update 之後」而非「install 之後」（live 2026-09-14 L5 實證）。
- **health check 應 assert** `muse plugins inspect <id> --json` 的
  `runtime_capabilities[].status == "trusted_enabled"`（`modified`＝停火待重 approve）。
- `plugins list` 的 "hooks require review" warning 是 third-party 常駐雜訊，**非 approval
  訊號**——勿據此判健康（O7 修正，live 2026-09-14）。

## Uninstall

```
muse plugins remove muse-memory-governance
```

per-repo marker 移除即回到全 native；固定安裝點不再使用時整目錄移除。
