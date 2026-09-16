# Fresh-machine 重建 runbook

> **定位**：本檔從「硬碟壞掉、只有 repo 與外部備份可取」的狀態重建 ai-rules；每節明列現有支撐與缺口，遇到缺乏可靠 source 的步驟就停在缺口，不把舊機現況或歷史 report 拼成假 runbook。

## 使用原則

依下列順序重建：

```
工具鏈
  ↓
rules + skills 部署
  ↓
hooks 接線
  ↓
記憶池恢復
  ↓
cron + launchd 重建
  ↓
code-reality
```

狀態語義：

- `✅`：repo 已有可依循的現行 source／script。
- `⚠️`：核心形態有 source，但仍缺 setup、外部 machine state 或 recovery pointer。
- `❌`：目前 repo 沒有足以可靠重建的 source。

本檔只合成重建順序。個別機制的詳細 contract 仍以各節連結 source 為準。

## 1\. 工具鏈 — ❌ 統一 onboarding 尚缺

### 現況判定

`❌`

UC dry run 已確認：

- repo root 沒有完整 fresh-machine toolchain runbook。
- MULTI-MACHINE.md 只為 memory 移植列出 `bash`、coreutils、`jq`、`python3`。
- rules 部署需要 `uv`。
- repo workflow 使用 Backlog.md CLI。
- Node.js / npm / Backlog.md CLI 的建立方式沒有集中在一個現行 source。

因此這一節目前只能做 prerequisite probe：

```
command -v git
command -v bash
command -v shasum
command -v jq
command -v python3
command -v uv
command -v node
command -v npm
command -v backlog
```

判準：

- 全部存在 → 可以進下一節；這只證明 executable 可用，不證明 fresh-machine installation 已可重建。
- 任一缺失 → **停止 runbook**，記錄缺哪個 prerequisite；目前 repo 沒有權威 installation procedure 可供本 runbook 繼續。
- 不從舊機 PATH、shell history、歷史 report 或臨時網路搜尋結果反推並固化安裝命令。

### 最小工具集合

- Git
- bash
- `shasum`、`date`
- `jq`
- Python runtime
- `uv`
- Node.js + npm
- Backlog.md CLI

code-reality 的額外工具在第 6 節處理。

## 2\. Rules + skills 部署 — ⚠️ 核心來源完整，fresh-machine symlink setup 尚未集中

### 2.1 非 Claude rules bundle — ✅

source：[deploy_agents.py](../../scripts/deploy_agents.py)

執行：

```
uv run python scripts/deploy_agents.py
```

它把 guide + neutral rules 生成到非 Claude harness 的 user-level `AGENTS.md`。

完成後依 [rules/AGENTS.md](../../rules/AGENTS.md) 的 deployment verification 驗證各端；generator exit 0 不等於 runtime loader 已讀到正確內容。

### 2.2 Claude guide + rules symlink — ⚠️

source：rules/AGENTS.md

預期 topology：

```
~/.claude/CLAUDE.md → <repo>/ai-development-guide.md
~/.claude/rules/    → <repo>/rules/
```

`deploy_agents.py` 刻意不建立 Claude 端 symlink。

repo 已記載 topology，但 fresh-machine 尚缺一個集中 setup 步驟處理 create/replace/verify。

### 2.3 Agent registry symlink — ⚠️

source：[agents/AGENTS.md](../../agents/AGENTS.md)

預期：

```
~/.zcode/agents  → <repo>/agents/zcode/
~/.claude/agents → <repo>/agents/claude/
```

registry 內容由 `agents/roles/` 經 `scripts/sync_agents.py` 產生；fresh-machine 缺的是兩條 user-level symlink 的集中建立與驗證程序。

若需要重建 generated registry，依 source 執行：

```
uv run python scripts/sync_agents.py
```

再建立／驗證上述 symlink。

### 2.4 Skills symlink — ⚠️

先前 dry run 將 `ls` 穿透 directory symlink 的結果誤判成「多個實體複製」。實際 topology 是單根（AIR-107 後續已退役 `~/.zcode/skills` 冗餘根）：

```
~/.agents/skills → <repo>/skills/
```

因此 fresh machine 不需要逐個複製 skill，也不需要一套 generated inventory deployment；真正缺的是把這條 symlink 重建並驗證。**禁補建 `~/.zcode/skills`**——ZCode 預設同掃 `.zcode` 與 `.agents` 兩根，雙根並存＝skill 清單重複注入（同 `skills/CLAUDE.md` 架構節）。

驗證時必須檢查 link 本身，而不是列出 link target 後誤判內容來源：

```
ls -ld ~/.agents/skills
readlink ~/.agents/skills
```

應解析到目前 ai-guide repo 的 `skills/`。

### 2.5 本節缺口

本節的 substrate 已存在；fresh-machine 缺的是一個集中、可安全重跑的 symlink bootstrap，涵蓋：

- Claude guide/rules。
- ZCode/Claude agents。
- ZCode/agents skills（單根 `~/.agents/skills`；禁補建 `~/.zcode/skills`）。

helper 應處理「target 已存在但不是預期 symlink」的情況，不直接破壞現有內容。

## 3\. Hooks 接線 — ⚠️ ZCode/Muse 可重建，CC 有 local secret dependency

### 3.1 ZCode user-level hooks — ✅

source：[zcode-registration.json](../../hooks/zcode-registration.json)、[hooks/AGENTS.md](../../hooks/AGENTS.md)

`zcode-registration.json` 是 `~/.zcode/cli/config.json`（machine-local，不入連結）中 `hooks:` 子樹的註冊範本。

重建：

1. 讀現有 user config。
2. 只取範本 `events` 子樹。
3. merge 進 config 的 `hooks:`。
4. `_comment` 不隨行。
5. 不以範本覆蓋整份 config。
6. 只 merge 目前 ZCode runtime 支援的事件。

核心 invariant 是「merge hooks 子樹」，不是「以 registration template 重建完整 config」。

### 3.2 Muse memory 閘 — ✅ user-scope plugin（AIR-79）＋repo 隨行 marker

source：[muse-plugins/memory-governance/](../../muse-plugins/memory-governance/)（README＝install/approve/health 操作）

執行（每機一次）：

```
muse plugins install <repo>/muse-plugins/memory-governance --scope user
muse plugins approve muse-memory-governance
```

repo opt-in marker＝`.agents/memory-governance.json`（`{"protocol": 1}`，進版控隨 repo 走）—— absent＝不攔、valid＝導流 inbox＋deny、壞掉＝deny 報錯（禁 fail-open）。plugin 是 muse memory 寫入閘唯一承載（legacy machine-local `.muse/hooks.json` 註冊與重建腳本已隨 AIR-79 cutover 退役）。

### 3.3 Muse 新 repo opt-in — ❌

UC7 dry run 顯示：ai-rules 本身已有 hook generator，但另一個新 repo 要採用同一套 Muse memory hook 時，尚缺正式 onboarding contract 說明需要哪些 asset、如何接線與如何驗證。

### 3.4 Claude settings — ⚠️

source：hooks/AGENTS.md

repo 已記載 CC memory sensors 所需的：

- PostToolUse
- FileChanged
- SessionStart

及 matcher/command 語義。

但 Claude settings 是 machine-local，且可能包含 API keys，因此不進 repo 版控。fresh clone 不會恢復 secret state。

缺口是 recovery pointer，而不是把 secret 值移進 repo。需要明確知道：

```
settings 結構來源
+ secret 由哪個外部安全來源恢復
+ merge 步驟
+ hook 驗證
```

## 4\. 記憶池恢復 — ✅ project pool 主鏈完整；⚠️ spine/new-pool 有邊界缺口

### 4.1 既有 ai-rules pool — ✅

source：[MULTI-MACHINE.md](../../hooks/MULTI-MACHINE.md)

memory pool 是 local-only Git state；一般 repo clone 不會帶回 `.agents/memory/`。

有 bundle：

```
git clone <bundle> <repo-root>/.agents/memory/
```

沒有 bundle 時，從舊機完整傳輸 pool，需保留 `.git` 與 mtime；現行 runbook 指定 `cp -a`／`rsync -a` 這類 preservation 語義。

只複製 markdown 而遺失 pool Git 不算完整恢復。

### 4.2 重建 harness memory symlink — ✅

先 dry-run：

```
hooks/setup-memory-symlinks.sh
```

確認 plan 後：

```
hooks/setup-memory-symlinks.sh --apply
```

現有 script 的安全語義：

- primary `.agents/memory/` 必須是實體目錄。
- 被替換 path 先搬成 `.bak-*`。
- CC project directory 尚未存在時 fail loud；先從 repo 開一次 CC session，再重跑。
- ZCode path 經 CC memory path 最終解析到 canonical pool。

### 4.3 Muse memory 閘 — ✅

同 §3.2（user-scope plugin install＋approve；marker 隨 repo 走，無 per-WT 步驟）。

### 4.4 驗證 topology — ✅

只讀：

```
hooks/verify-memory-topology.sh
```

現有 verifier 檢：

- primary pool real-dir。
- CC symlink。
- ZCode double-hop。
- 三腿 `MEMORY.md` 同 inode。
- generator `--check`。

Muse write gate 健檢＝plugin 面（`muse plugins inspect <id> --json` 的 `runtime_capabilities[].status`），單一源＝[muse-plugins/memory-governance/README.md](../../muse-plugins/memory-governance/README.md) 運維節（legacy `.muse/hooks.json` 檢查與 `--smoke` hook 往返已隨 AIR-79 cutover 退役）。

### 4.5 Memory spine — ⚠️

`~/.agents/memory-spine/` 位於 project pool 之外，不在目前 pool bundle runbook 涵蓋範圍。

現有 evidence 尚不足以證明它有獨立 backup/rebuild source，因此「project pool 恢復成功」不能擴張成「全部 memory state 已恢復」。

### 4.6 新 repo 建 pool — ⚠️

UC7 dry run 已找到 generator、resident-set 與 audit 組件，但缺完整 bootstrap source：

```
建立 pool
→ deploy generator
→ first regen
→ 選 A/B 形態
→ B 形態 resident set 初建
→ first audit state
→ hooks adoption
```

其中 `_resident-set.md` 屬 user-frozen state，不能由 AI 自行生成內容。

## 5\. Cron + launchd 重建 — ⚠️ inventory 在，完整 reconstruction source 不足

### 5.1 ZCode cron inventory — ⚠️

source：[schedule-registry.md](../schedule-registry.md)

registry 已保存：

- automation identity
- schedule
- 職責
- target scope
- writer/auditor/reporting role

現行 runtime 的機械真相仍是 `CronList`；registry 是職責 projection。

fresh machine 的缺口是 ZCode cron state 位於 local DB，而且 repo 尚無 cron prompt 的 verbatim reconstruction source。只有 automation id、schedule、職責摘要，無法保證重建出同一 prompt。

需要的終態關係是：

```
repo-owned verbatim prompt source
        ↓
CronCreate / CronUpdate
        ↓
CronList machine truth
        ↓
schedule-registry responsibility projection
```

或等價、可證明能逐字恢復的備份機制。

### 5.2 launchd inventory — ⚠️

schedule registry 已記載本 repo 相關：

- backlog browser（常駐已退役 09-11——plist 移除；board UI 走 extension／on-demand）
- backlog cleanup

UC dry run 的 evidence：

- backlog-browser plist 有 tracked source（dry-run 當時；09-11 退役已移除——現無）。
- backlog-cleanup plist 當時在 machine 上存在，但未找到 tracked source；已有既有工作承接該缺口（AIR-70 F1）。
- repo 缺現行、完整的 launchctl enable/bootstrap verification runbook。

要達到可重建，需有：

```
plist source
→ install location
→ bootstrap/load
→ status verification
→ update/restart procedure
```

### 5.3 排程重建完成時的驗收條件

未來本節升 `✅` 前至少要能機械確認：

- `CronList` 與 verbatim prompt source／registry 對帳。
- launchd service 已 load。
- backlog browser 常駐不重建（已退役；on-demand `backlog browser` 可 smoke，不要求 plist／load）。
- cleanup service 可定位 script 與 precheck。
- memory nightly writer 指到新機器 canonical pool/inbox。
- 非 primary machine 不把自己的 automation identity 回寫 primary registry。

## 6\. Code-reality — ✅ 安裝與 repo data-plane 有 source

source：[code-reality skill](../../skills/code-reality/SKILL.md)

### 6.1 安裝 CLI/tooling

一般安裝面：

```
uv tool install code-reality
uv tool install pyrefly-producer
uv tool install code-reality-lsp-bridge
```

Rust language support：

```
rustup component add rust-analyzer
```

plugin runtime 另有自己的 bootstrap/pin 行為；判定實際呼叫哪個 binary face 時，以 code-reality skill 的 resolution contract 為準。

### 6.2 驗證 binary

```
command -v code-reality
code-reality --version
```

不要以其他 terminal/session 的 PATH 推論目前 GUI harness 解析到相同 binary。

### 6.3 重建 repo data plane

```
code-reality build --repo <repo-root>
```

sidecar/graph 是可重建資料，不需從舊硬碟備份。

工具的 stale guard、producer、refs、graph semantics 由 code-reality skill/plugin source 擁有，本 runbook 不複製。

### 6.4 新 repo onboarding

新 repo 採用 code-reality：

1. 建立或確認 `.code-reality.toml`。
2. 先做符合該 repo layout 的 smoke。
3. `code-reality build --repo <repo-root>`。
4. 檢查 graph/index source stamp。
5. repo specialization 留在 repo profile，不寫回工具層。

UC dry run 對這條路徑判定為 `✅`。

## Fresh-machine 完成 gate

| 面 | 完成條件 | 現況 |
| --- | --- | --- |
| 工具鏈 | 必要 binary 有 repo-owned/明確 recovery procedure，空機可照 runbook 裝到 presence check 全過 | ❌ |
| rules/skills | bundle 可生成；Claude rules、agents、skills symlink 可從集中 setup 重建並驗證 | ⚠️ |
| hooks | ZCode/CC/Muse 都有 setup + verify，CC secret recovery 有 pointer，新 repo Muse adoption 有 contract | ⚠️ |
| memory | project pool、links、hooks、bundle 可重建；spine 與 new-pool bootstrap 有定義 | ⚠️（project pool 主鏈 ✅） |
| cron/launchd | prompt/plist 有 reconstruction source，可 load 並對帳 runtime | ⚠️ |
| code-reality | binary + repo graph 可從 source 重建 | ✅ |

## 待補缺口清單

1. 統一 fresh-machine 工具鏈 installation/recovery runbook。
2. Claude guide/rules、ZCode/Claude agents、ZCode/agents skills symlink 的集中 bootstrap + verify。
3. Claude settings/API-key 外部恢復來源 pointer。
4. ZCode cron prompt verbatim backup/rebuild source。
5. launchd tracked source、啟用與驗證 runbook 的完整閉環。
6. memory-spine backup/rebuild 定義。
7. memory-audit new-pool bootstrap。
8. Muse hooks new-repo adoption 流程。

這些缺口只有在相應 source 與可執行 recovery path 真正存在並驗證後才升級狀態；「目前這台機器上已經有」本身不是 fresh-machine recovery 證據。
