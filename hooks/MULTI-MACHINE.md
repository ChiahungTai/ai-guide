# Multi-machine porting runbook（AIR-54 後續支援）

池是 local-only git、永不進 repo 版控——clone **不會**帶來池。新機器＝空池起步。

依賴：bash、coreutils（`shasum`/`date`）、`jq`、`python3`（verify 的 inode/generator 檢查用；新機裸環境未必有 uv——本 runbook 不依賴 uv）。

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

user-scope plugin 裝一次全 marker repo 生效（repo opt-in marker＝`.agents/memory-governance.json`，隨 repo 走無需重跑）——plugin 是 muse memory 寫入閘唯一承載（legacy machine-local `.muse/hooks.json` 註冊已隨 AIR-79 cutover 退役）；運維（update 後必重 approve 等）見 [muse-plugins/memory-governance/README.md](../../muse-plugins/memory-governance/README.md) 運維節。

### 4. 重建排程（最易漏——僅 primary 機）

ZCode cron 住本機 DB，不跟 repo 走。**registry 記 primary 機的 automationId——副機自建 cron 但不回填 registry**（registry 單 automationId 欄＋「與 CronList 逐字一致」要求＝單機口徑；副機回填會讓 primary 側 governance drift。多機 machine identity 是 AIR-52 治理面範圍，決議前 primary-only）。副機若需夜波，比照 primary 建 cron、對象僅副機自己路徑，報告落各自機。

### 5. 驗證

```bash
hooks/verify-memory-topology.sh           # 只讀：三段＋inode＋generator
```

## 深層限制（架構邊界，非待修）

雙機＝雙池，無同步機制（local-only 是刻意設計）。模型：定一台主機，副機只讀或 bundle 單向追；禁雙寫（CAS 救不了跨機分叉）。
