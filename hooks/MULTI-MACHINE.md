# Multi-machine porting runbook（AIR-54 後續支援）

池是 local-only git、永不進 repo 版控——clone **不會**帶來池。新機器＝空池起步。

依賴：bash、coreutils（`shasum`/`date`）、`jq`、`python3`（verify 的 inode/generator 檢查用；新機裸環境未必有 uv——本 runbook 不依賴 uv）。

> **有 uv 的機器**：安裝/註冊面（hooks 四家註冊、skills symlink、rules bundle、agents registry、muse plugin、monitor 排程）統一走 governance installer——新機器入口＝`uv run python scripts/bootstrap.py`（見下「新機器全裝總覽」），契約與逐面檢查清單見 [governance/README.md](../governance/README.md) bootstrap 節。本 runbook＝**無 uv 裸環境 fallback**；本文的傳池步驟（§1）installer/bootstrap 皆不涵蓋，照走。

## 新機器全裝總覽（AIR-110）

入口＝**`scripts/bootstrap.py` 冪等編排器**（五階段：preflight → installer（primary 含 monitor 裝載）→ approve 暫停點 → verify 探針 → 面外清單；唯一安裝入口＝governance installer，不下手工 config；`--approved`＝resume——跳過安裝直接 verify（`--check` 自證 Phase 2 產物在場））：

```bash
uv run python scripts/bootstrap.py --dry-run     # 唯讀 preflight＋印計畫（零執行）
uv run python scripts/bootstrap.py               # 安裝→停在 approve 暫停點（手動三項後續跑）
uv run python scripts/bootstrap.py --approved    # 手動 approve 後 resume：跳過安裝，verify 探針＋面外清單
```

- **installer 七項**（CC/ZCode/codex 三家 hooks 註冊＋muse plugin、skills/rules symlink、agents registry、monitor 排程、逐面驗證命令）：單一源＝[governance/README.md](../governance/README.md) bootstrap 節——本檔不重抄。
- **面外步驟**（bootstrap 列印不安裝）：
  - G1 secrets：`<repo>/settings.json`（gitignored local-only、含 API keys）從舊機拷——preflight 缺席＝fail-loud 擋下，不自動建不代寫。
  - G3 hooksPath：`git config core.hooksPath .githooks`（per-clone，clone 後手動一次；非 .githooks＝preflight WARN、verify 完成檢查 FAIL）。
  - G5 backlog-cleanup plist：已版控（`deploy/backlog-cleanup.plist`）——手動裝載見 [governance/README.md](../governance/README.md) 面外排程清單。
  - G6 池傳輸：§1（池 local-only 永不進 repo——clone 不帶池，新機空池起步）。
  - spine：`~/.agents/memory-spine/` 跨池共享目錄——缺席＝degraded WARN（報告非擋）。
  - cron/monitor 裝載＝primary-only：§4（monitor 已併 bootstrap primary 安裝——`--surface all` 成功後接 `--surface monitor`；`--role secondary` 本弧僅介面）。
- **跨 repo 工具**（各自 repo/skill 為安裝真相源）：delegate-bridge plugin（marketplace 安裝；repo `~/Github/delegate-bridge`）、code-reality binary（[skills/code-reality/SKILL.md](../skills/code-reality/SKILL.md)）、NT 查詢工具鏈（已遷 mosaic repo-local `.agents/skills/`）、mosaic `com.mosaic.*` launchd 排程（mosaic repo 側管理）、entitlements-probe（`deploy/entitlements-probe.plist` 手動裝載）。

## 程序（按依賴序）

### 1. 傳池（二選一）

- 有 bundle：把舊機 `~/.agents/memory-bundles/` 最新一份拷過來，新機器 `git clone <bundle> <repo>/.agents/memory/`。
- 無 bundle：整目錄拷（`cp -a`／rsync -a，連 `.git` 一起——保 mtime，rank 排序依賴它）。

### 2. 重建 symlink（腳本）

```bash
hooks/setup-memory-symlinks.sh            # dry-run，先看 plan
hooks/setup-memory-symlinks.sh --apply    # 執行；被換掉的原條目一律先 mv 成 .bak-<timestamp>，不用 rm
```

- 命名規則（2026-09-09 實測）：CC 目錄＝repo 路徑 `/`→`-`；ZCode 目錄＝`<basename>-<sha256(repo路徑)[:16]>`；鏈＝ZCode→CC→池。
- CC project 目錄不存在→腳本 fail-loud：先去新機器 repo 開一次 CC session 再重跑。
- muse 端零動作（project scope 跟 repo 走）。

### 3. Muse memory 閘（AIR-79 plugin 化）

```bash
muse plugins install <repo>/muse-plugins/memory-governance --scope user
muse plugins approve muse-memory-governance
```

user-scope plugin 裝一次全 marker repo 生效（repo opt-in marker＝`.agents/memory-governance.json`，隨 repo 走無需重跑）——plugin 是 muse memory 寫入閘唯一承載（legacy machine-local `.muse/hooks.json` 註冊已隨 AIR-79 cutover 退役）；運維（update 後必重 approve 等）見 [muse-plugins/memory-governance/README.md](../muse-plugins/memory-governance/README.md) 運維節。

### 4. 重建排程（最易漏——僅 primary 機）

ZCode cron 住本機 DB，不跟 repo 走。**registry 記 primary 機的 automationId——副機自建 cron 但不回填 registry**（registry 單 automationId 欄＋「與 CronList 逐字一致」要求＝單機口徑；副機回填會讓 primary 側 governance drift。多機 machine identity 是 AIR-52 治理面範圍，決議前 primary-only）。副機若需夜波，比照 primary 建 cron、對象僅副機自己路徑，報告落各自機。

### 5. 驗證

```bash
hooks/verify-memory-topology.sh           # 只讀：三段＋inode＋generator
```

## 深層限制（架構邊界，非待修）

雙機＝雙池，無同步機制（local-only 是刻意設計）。模型：定一台主機，副機只讀或 bundle 單向追；禁雙寫（CAS 救不了跨機分叉）。
