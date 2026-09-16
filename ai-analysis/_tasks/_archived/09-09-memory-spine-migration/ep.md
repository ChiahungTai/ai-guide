# EP：跨池記憶主體遷移——muse project memory 一等公民（AIR-54）

> **ep_type**: implementation
> baseline: 48d0590

## 實作總覽

把 ai-rules 記憶池主體從 CC 私有路徑（`~/.claude/projects/-Users-ctai-Github-ai-rules/memory/`）遷到 repo 內 muse project memory 合約路徑（`<repo>/.agents/memory/`），CC 端原路徑換目錄 symlink 透明讀寫、ZCode 既有鏈雙跳、muse 原生 scope 零適配讀。寫入流：muse `add_memory`/`edit_memory` 被 PreToolUse hook 攔截代存 inbox，CC/ZCode 側 consolidation（補 frontmatter＋六問）後入池。mosaic 同形態移植。

**驅動**：muse 是可預見未來 CP 最高的 runtime——架構讓主力零適配（主體=muse 原生 scope），CC/ZCode 經最穩定的 POSIX symlink 透明語義。09-09 實驗鏈已把核心技術未知數全部消滅（注入/deny 契約/裸寫行為/symlink 拒絕全實測）。

## UC 盤點

### Backlog 關聯

- **AIR-54**（本卡，To Do）——EP 追蹤卡
- **AIR-52**（To Do）——S4 段「memory B 形態跟進」改 23:40 cron prompt 口徑；本弧 S2 會改同一 cron 的 `git -C <pool>` 路徑——**動作面重疊登記**：兩弧各改各的欄位，先落地者贏，後者 rebase 對帳。**追加共檔面（review F8）**：AIR-52 S2 動 `ai-analysis/schedule-registry.md` 與本弧 S2 的池路徑改動同檔
- **AIR-50**（To Do）——S9「memory-audit 統一定義表補 wrapper 誤置條目」與本弧 S4 同編 `skills/memory-audit/SKILL.md`（review F8）——AIR-50 先動（排序在前），本弧 S4 後動對帳
- **AIR-48**（In Progress，P4 dogfood）——本弧 S3 品質閘引用其三判準（純機械/單入口/無語義例外）；平行推進（user 09-09 拍板）
- **draft-2**（muse-grok telemetry 探測）——探測目標已被 09-09 實驗完成（session.jsonl 即記錄面）；歸因前提（「muse 不用自家 memory」）被本弧翻轉——本弧 S5 標記 draft-2 探測完成＋註記前提變更，接線部分留 draft
- **draft-3 / AIR-53**（muse bundle 治理）——正交（rules lane 64KiB），無動作

### SYSTEM-MAP 影響

無 SYSTEM-MAP.md（元專案，正當跳過）。

### 掃描範圍

- `AGENTS.md`（觀察池路由段、「Muse memory 唯讀」段）
- `skills/memory-audit/SKILL.md`＋`skills/memory-audit/scripts/generate_index.py`（generator 資產源）
- `hooks/block-memory-index-write.py`（CC 池寫入閘，邏輯移植參考）
- `rules/context-management.md`（memory 生命週期 pointer）
- `~/.agents/memory-spine/index.md`（認養表 muse 腿）
- `skills/corrections-weekly/SKILL.md`（`--pool` 實體路徑示例——review F7 補列）＋`ai-analysis/schedule-registry.md`（池路徑×2 處——F7；夜波 scope 定義源）
- memory 條目：`project_muse-memory-mechanism-divergence`（pending 收斂）、`reference_muse-code-cli-facts`（09-09 已更新）、`project_memory-cc-alignment-diagnosis-0905`（symlink 拓撲段）

### 同主題 memory 條目（結案蒸餾範圍）

- `project_muse-memory-mechanism-divergence`——「要用先重設計」pending 由本弧實現，結案蒸餾為終態
- `reference_muse-code-cli-facts`——09-09 已吸收實驗事實（hooks 契約/add_memory/symlink 拒絕），隨弧補搬遷後形態；已超 12K，本弧結案蒸餾時收斂
- `project_memory-cc-alignment-diagnosis-0905`——symlink 拓撲段隨 S5 更新（CC 端目錄 symlink 新形態）

### 既有 UC 狀態

| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| auto-memory 池治理（generator/hook/audit/夜間波） | ✅ | memory-audit skill | 更新 | 池路徑變更，治理資產隨主體搬遷＋路徑同步 |
| muse 唯讀掛載 | ✅ | AGENTS.md | 更新 | 升級為受約束寫入者（inbox 流） |
| copy 投影腿（09-09 POC） | 🟢 | .agent-tmp/poc_muse_projection.py | 退役 | 主體遷入後投影目錄被主體取代 |

### 新增 UC

| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| 跨池共享記憶主體（CC/ZCode/muse 三端等距「讀」；寫＝CC/ZCode 直寫、muse 經 inbox 收斂——SM-14） | 📋 | `<repo>/.agents/memory/`＋CC 目錄 symlink＋muse hooks inbox |
| muse 寫入流（inbox→consolidation→池） | 📋 | `.muse/hooks.json`＋`hooks/muse_memory_inbox.py`＋夜間波 inbox 步驟 |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | CC session 開場 | 新 CC session 於 ai-rules | 經 symlink 載入主體 MEMORY.md 索引如常（B 形態常駐面） | 池 git restore＋移除 symlink | 三端主體 |
| SM-2 | ZCode session 開場 | 新 ZCode session | 雙跳 symlink 讀到同 inode 內容 | 同上 | 三端主體 |
| SM-3 | muse task 開場 | bridge task / 互動 session | project scope 注入 MEMORY.md 全文＋清單（已實測形態） | — | 三端主體 |
| SM-4 | muse 想寫記憶 | add_memory/edit_memory 呼叫 | PreToolUse hook 攔截：content 代存 inbox，deny reason 告知已存位置 | 清 inbox | muse 寫入流 |
| SM-5 | bridge headless task 寫記憶 | 同上 | 同 SM-4——**bridge task 實測 trusted（user-config）且 hook 生效**（第三輪攔截實證：session 01a08405 `tool blocked by hook`）；真實缺口＝未 trust 的 workspace（新 clone）headless task 不載 hooks——工單紀律兜底 | 同上 | muse 寫入流 |
| SM-6 | consolidation | 夜間波 / 手動 | inbox 逐條六問→補 frontmatter→寫主體→regen→清 inbox | — | muse 寫入流 |
| SM-7 | 夜間收斂波 | 23:40 cron | `git -C <主體新路徑>` 波程序正常（marker/baseline/差異歸屬） | marker 留存程序 | 池治理 |
| SM-8 | 池 gate FAIL | 條目違規/超限 | generator 照寫出＋fail-loud（AIR-27 語義不變） | — | 池治理 |
| SM-9 | hook 腳本故障 | inbox hook 崩潰 | fail-open：**對 add＝品質閘失效（orphan 條目）；對 edit＝integrity loss（muse 直改 canonical）**（G2-6 校準）——S4 前置池 git 歸屬檢查為第二道偵測 | 修 hook | muse 寫入流 |
| SM-10 | muse 升版 | binary 更新 | **四契約 fixture（G2-12）**：開場注入／>48 recall sentinel／read_memory symlink policy／deny+fail-open 行為——升版 acceptance 是 contract suite 非「路徑還在」；project scope 合約路徑本身不受影響 | — | 三端主體 |
| SM-11 | 手術回滾 | S1 驗證失敗 | 無遷移後寫入：`rm symlink＋mv 回去`；已有寫入：**差異歸屬**（池 git diff/status 逐檔確認，禁整體 restore——波次 marker 同思路）；S2 已改 cron 則回滾含 cron 還原（否則夜波指向退役路徑靜默失效） | — | 全部 |
| SM-12 | mosaic 多 worktree | mosaic 移植 | owning 線（main worktree）放實體；其餘 worktree 的 `.agents/memory/` 與 CC project dir memory 皆 symlink 指實體；**次 worktree muse 腿視目錄層 symlink 實測結果（F2）** | — | mosaic 移植 |
| SM-13 | codex 第四端讀取 | codex session 檢索池 | 檔案級 Read 穿透如常；**目錄級 rg/glob 遍歷行為改變**（rg 預設不跟目錄 symlink）——AGENTS.md 觀察池路由段補 `-L` 或直指主體路徑指引 | — | 三端主體 |
| SM-14 | muse 寫後讀 lag | muse 寫 inbox→同日再讀 | **非即時**：deny reason 告知位置，池要等 consolidation——設計使然（UC 措辭＝三端等距「讀」、寫經 inbox 收斂非等距） | — | muse 寫入流 |

## 段落 0：全域研究摘要（09-09 實驗鏈先驗）

**可複用基礎設施**：
- `.agent-tmp/poc_muse_projection.py`——copy 投影腳本（搬遷程序參考；過渡形態）
- `skills/memory-audit/scripts/generate_index.py`——B 形態 generator（ASSET_SOURCE `__file__`-relative byte 比對——隨主體搬遷後相對結構不變）
- `hooks/block-memory-index-write.py`——CC 寫入閘（deny 邏輯移植 muse hooks 參考）
- `.agent-tmp/muse-hooks-findings.md`——deny 契約＋實驗矩陣＋能力面（stdin tool_name/tool_input、updatedInput、additionalContext）

**依賴關係**：
- 池 git（AIR-49 local repo）——.git 隨主體搬遷，歷史連續
- B 形態（AIR-48 P3）——`_resident-set.md` 凍結 12 條；主體遷移不改投影語義
- 夜間收斂 cron（AIR-52 S4 互動——見 UC 盤點）
- ZCode memory symlink（既有鏈 `~/.zcode/cli/memories/.../memory → CC projects/<encoded>/memory`）——CC 端換 symlink 後自動雙跳

**風險假設清單**（等級｜狀態）：
1. muse project scope 注入機制——**已驗**（14 檔 copy 投影實測：MEMORY.md 全文＋清單 13 檔）
2. hooks deny 契約——**已驗**（hookSpecificOutput/permissionDecisionReason，擋 add_memory 實證；bridge task trusted 下生效）
3. muse memory 拒 symlink——**已驗**（read_memory 報錯）——主體必須實體檔
4. add_memory 裸寫零 frontmatter——**已驗**——inbox 流的必要性依據
5. CC 原生載入器對自身 memory 目錄為 symlink——未直接驗（**中**）：ZCode 目錄 symlink 是既有在用形態（本弧規劃 session 活證）、mosaic 三 dir 共指同 inode 既有；CC 載入器不同實作但 POSIX 語義透明——S1 程序內建（側備份＋rmdir 併發 guard＋即時三端驗證＋回滾），不做獨立先驗段
6. generator/hook 於新路徑執行——低（review F14 源碼核實）：generator 無資產比對（glob 自身目錄、路徑無關）；byte 比對在 repo 端 `hooks/memory-index-regen.py`（`__file__`-relative 指回 repo skills/，與池位置正交）；部署副本 cp -a 後 byte 不變——S1 後真 session 覆蓋
7. muse 48 檔清單截斷（G2-7 重寫）：**真正 gate＝recall sentinel 而非截斷順序考古**——MEMORY.md 全文注入（含 desc）＋read_memory(path) 直讀之下，截斷順序重要性存疑。S1 後實測：選一個確定落在 >48 清單外的 sentinel 條目，muse task 以**自然語言召回**（不提示 path）＋explicit `read_memory(path)` 兩測——兩過＝一等公民成立（observer 召回可達）；僅 explicit 過＝召回面受限（記錄降級）；截斷形態僅記錄。治理檔灌清單的緩解（收 `_governance/` 子目錄）保留為選項——**✅ 已驗（雙實測合成，09-09）**：①工具鏈召回**綠**（muse 15:00 腿：清單內 `_inventory.md` 直讀全量索引→定位條目→讀 body——observer 召回可達，一等公民 gate 關閉）；②注入深度**受限**（VP3 body-only canary：token 僅在 body、negative control 成立、telemetry oracle 實證 read_memory call——開場 snapshot 純回想不可達清單外條目，explicit read ✓）——**結論＝一等公民成立（工具鏈可達）；直達注入限於清單內條目**——高價值跨池知識的 desc 投影品質決定「免工具直達」面（結果記錄：池 `reference_recall-sentinel-canary.md`）
8. muse 對 project scope 的 add_memory 行為——未驗（中；personal_project 已驗，機制應同）→ S3 實測
9. **MEMORY.md context tax（G2-8 部分採納說明）**：muse 開場全文注入 MEMORY.md——其尺寸**已受 generator B 形態 gate 約束**（常駐面 6,000 chars，AIR-48 P3）——muse 注入的就是這份被 gate 的投影，無需新機制；gate 语义隨弧補註「兼任 muse context tax 預算」

## 段落劃分原則

依賴序：S1（手術，程序內建先驗與回滾——review 定案砍除獨立 S0：CC 載入器無乾淨測試介面，S0 空轉〔F14/F16〕）→ S2（路徑同步）→ S3（muse 閘+inbox）→ S4（consolidation，**需 S2 後**——同檔面：23:40 cron prompt 與 memory-audit SKILL.md 兩處〔F6〕）→ S5（文檔）→ S6（mosaic）。S3 可與 S2 平行（無檔案重疊，已驗）；S6 獨立可後延。語義約束：主體路徑常數 `AGENT_MEM=/Users/ctai/Github/ai-rules/.agents/memory`、inbox＝`$AGENT_MEM-inbox/`（hook 腳本內以 `dirname $0` 推導絕對路徑，**不依賴 cwd**〔F3——bridge task cwd 未契約保證〕）；CC 端介面路徑 `CC_MEM=~/.claude/projects/-Users-ctai-Github-ai-rules/memory`（不變——它是 symlink）。

---

## S1：主體搬遷手術（ai-rules）

### Context
UC 引用：實作「跨池共享記憶主體」。依賴：無前置段（先驗內建本段程序）。語義約束：AGENT_MEM 主體、CC_MEM 為 symlink 介面（語義不變）、`$POOL.bak` 側備份路徑＝`~/.claude/projects/-Users-ctai-Github-ai-rules/memory.bak`。

### 核心實作要點
0. **時序防護（F11）**：手術避開 23:40±30min 夜波窗口
1. **側置備份**：`cp -a $POOL $POOL.bak`（mtime 保留——rank mtime 排序防護）
2. **garbage 清除（G2-10 換軌）**：backup 已留副本——直接從 live `$POOL` 刪 `_trash-0908/` 與 `_decay-candidates.*`（原「mv 進 .bak」手法經 repro 證實不可靠：BSD mv move-into 語義產生 nested 髒形態）
3. **過渡投影退役**：`rm -rf $AGENT_MEM`——whole-rename 前提＝destination 不存在
4. **whole-directory rename（G2-1）**：前置同 FS 檢查（`stat -f %d` 比 device id）；同 FS→`mv $POOL $AGENT_MEM`（單目錄原子 rename；**`mv dir/. dest/` 形態經 repro 證實 BSD mv 拒絕〔Invalid argument〕，禁用**）；跨 FS→退 `cp -a`＋`rm -rf`（backup 已在場，接受非原子並記錄）
5. `ln -s $AGENT_MEM $POOL`
6. ZCode 端不動（既有 symlink 經 CC_MEM 雙跳）——驗 `readlink -f` 到 AGENT_MEM
7. `.gitignore` 兩行已於 59baf29 落地（驗證在場即可）
8. **E2E 驗證矩陣（G2-9＝`.bak` 解鎖條件）**：三端開場讀＋**CC/ZCode write-through**（經 symlink 寫測試條目→regen→讀回→刪）＋**muse 攔截鏈**（add→deny→inbox 落地）＋consolidation 模擬（含 path contract）＋夜波 dry-run＋inner git 操作（status/log）
9. **E2E 全綠後**：先手動產出首份 repo 外 bundle（`git -C $AGENT_MEM bundle create ~/.agents/memory-bundles/ai-rules-$(date +%F).bundle --all`——歸零「刪 .bak 到首個夜波」之間的無備份空窗）→ 才刪 `$POOL.bak`

### Pseudo Code
```
POOL=~/.claude/projects/-Users-ctai-Github-ai-rules/memory
AGENT_MEM=$PWD/.agents/memory
# 時序檢查：date '+%H%M' 避開 2320-2410；不然中止
cp -a "$POOL" "$POOL.bak"                                  # 側備份
rm -rf "$POOL/_trash-0908" "$POOL"/_decay-candidates.*     # backup 已留證（G2-10）
rm -rf "$AGENT_MEM"                                        # 投影退役＋rename 前提
[[ $(stat -f %d "$POOL") == $(stat -f %d "$PWD/.agents") ]] || echo "WARN: 跨FS→rename退化copy"
mv "$POOL" "$AGENT_MEM"                                    # whole rename（G2-1）
ln -s "$AGENT_MEM" "$POOL"
# E2E（G2-9）：三端開場＋write-through＋muse攔截鏈＋consolidation模擬＋夜波dry-run＋inner git
# 全綠 → rm -rf "$POOL.bak"
```

### 驗證策略
- E2E 矩陣如要點 8（`.bak` 刪除的前置）；`readlink -f`、inode 一致、generator `--check`
- **回滾（F9＋G2-1 簡化）**：whole-rename 使回滾更乾淨——無遷移後寫入：`rm $POOL && mv $AGENT_MEM $POOL`（單目錄）；已有寫入→差異歸屬（池 git diff/status 逐檔，禁整體 restore）；S2 已改 cron→回滾含 cron 還原

---

## S2：治理路徑同步

### Context
UC 引用：更新「auto-memory 池治理」。依賴：S1。語義約束：**CC_MEM 路徑是 harness 介面——出現在 transcript/telemetry 的路徑不變**；要改的是「治理工具 hardcode 池實體路徑」處。

### 核心實作要點
1. **機械盤點**：`rg -l 'projects/-Users-ctai-Github-ai-rules' <repo> ~/.zcode/cli/config.json ~/.claude/settings.json`＋夜間 cron 定義（CronList）＋ZCode hook config——分類：介面路徑（留）vs 實體路徑依賴（改指 AGENT_MEM）；**加 AIR-56 接線面（8c4fa14）**：write-sensor／dirty-sensor（FileChanged watchPaths）／watch-seed 的路徑生成源與 watch 目標清單——介面路徑（CC_MEM 形態）經 symlink 理論透明，但生成源若掃實體池目錄須驗證搬遷後行為＋live 觸發確認（8c4fa14 遺留的「下個 session hook log 驗證」與本弧 S1 後合併驗）
2. 夜間 23:40 cron prompt 的 `git -C <pool>` → AGENT_MEM（AIR-52 互動：只改路徑欄，口徑欄歸 AIR-52）
3. Stop hook regen：hook 以記憶目錄內 generator 為準（`__file__`-relative）——驗證即可，預期零改
4. telemetry：CC 側路徑模式不變（Read 事件路徑＝CC_MEM）——零改，記錄理由
5. memory-audit skill 文檔內路徑示例同步

### Pseudo Code
盤點清單表（路徑→分類→動作），全綠後 `rg '<舊實體路徑字串>' --hidden` 掃 config/cron/skill 零殘留（介面路徑除外，附列舉）。

### 驗證策略
- 夜間波手動觸發一次（或等當晚）——波程序完整跑（marker/baseline/差異歸屬在 AGENT_MEM 上運作）
- rg 殘留掃描輸出附報告

---

## S3：muse hooks 品質閘＋inbox 流

### Context
UC 引用：實作「muse 寫入流」。依賴：S1。基礎設施：`hooks/`（跨 harness 單一源慣例）、`block-memory-index-write.py`（判準參考）、muse-hooks-findings.md（契約）。語義約束：AIR-48 三判準——本閘為**純機械導流**（攔截＋代存），語義判斷（六問/frontmatter 補全）全留 consolidation 站，閘不做語義。

### 核心實作要點（**本文已隨實作修訂 09-09——實作單一源＝`hooks/muse_memory_inbox.sh`；原規劃見 git history**）
1. `hooks/muse_memory_inbox.sh`：讀 stdin JSON（`tool_input.content/path/scope`）→ 落 `.agents/memory-inbox/<TS>-<pid>-<content-hash-12>.json`（**payload＝原始 JSON 原樣**〔G2-5 定案取代原「frontmatter stub」案〕；檔名不含模型 basename；path 命中池內既有條目時附 `_inbox_meta.base_sha256`〔CAS base——T3-6：條件是 path 存在，非 tool==edit〕）→ stdout 輸出 deny JSON（CC 新式 hookSpecificOutput）。lexical gate：absolute/slash path 跳過 enrichment（deny+land 照走——T3-1/T4-2）；jq parse 失敗不殺腳本（`|| true`——否則整個導流 fail-open，review F1）
2. `.muse/hooks.json`：PreToolUse matcher `add_memory|edit_memory` → 上述腳本（絕對路徑）——**machine-local 生成物**（`hooks/setup-muse-hooks.sh` 產、gitignore；修訂自原案：muse 要求 hook command 絕對路徑，committed hooks.json 無可攜性——結構源〔setup script〕版控）
3. **fail-open 約束**：腳本故障＝閘開（muse 直寫主體）——腳本保持極簡（無網路、無外部依賴、`set -euo pipefail`）；edit_memory 的 deny 會擋合法編輯嗎？——**第一版全導流**（user「先 inbox 看看」），觀察誤傷率後再議 allowlist
4. muse 對 project scope add_memory 實測（風險 8）：確認導流前路徑行為——**已驗**（VP2：project/personal_project scope 皆被 matcher 攔截導流）
5. ~~hooks.json 進 repo（版控）~~ → **修訂（見要點 2）**：machine-local 生成物＋結構源版控；gitignore 排除 hooks.json 與 inbox

### Pseudo Code（hook 腳本核心——F3/F13/G2-5 修正版）
```bash
#!/usr/bin/env bash
set -euo pipefail
umask 077
REPO=$(cd "$(dirname "$0")/.." && pwd)     # 絕對路徑推導，不依賴 cwd（F3）
INBOX="$REPO/.agents/memory-inbox"
IN=$(cat)                                  # stdin: {tool_name, tool_input:{scope,path,content}}
TS=$(date +%Y%m%d-%H%M%S)
SUM=$(printf '%s' "$IN" | shasum -a 256 | cut -c1-12)
OUT="$INBOX/${TS}-$$-${SUM}.json"          # 檔名＝TS+pid+content hash——不含模型 basename（G2-5：basename 污染面）
TMP="$INBOX/.tmp-${TS}-$$-${SUM}"
mkdir -p "$INBOX"
PAYLOAD="$IN"
P=$(printf '%s' "$IN" | jq -r '.tool_input.path // empty')
if [ -n "$P" ] && [ -f "$REPO/.agents/memory/$P" ]; then
  H=$(shasum -a 256 "$REPO/.agents/memory/$P" | cut -d' ' -f1)
  PAYLOAD=$(jq -c --arg p "$P" --arg h "$H" '. + {_inbox_meta:{base_path:$p, base_sha256:$h}}' <<<"$IN")
fi
# _inbox_meta：hook 附加觀測欄——edit CAS 的 base hash（G2-3）；缺席＝add 或 path 不存在，payload 原樣
printf '%s' "$PAYLOAD" > "$TMP" && mv "$TMP" "$OUT"    # 原子發布（G2-4：temp+rename）
jq -nc --arg p "$OUT" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:("已代存 inbox: "+$p+"（consolidation 站將處理入池）")}}'
# deny JSON 全由 jq 構造——$OUT 含任意字元也正確 escape（G2-5：printf %s 塞 JSON 的 fail-open 漏洞）
```
（payload 為 JSON 檔非 markdown fence——consolidation 端用 jq 讀，content 含 ``` 不再破壞解析〔G2-5〕）

### 驗證策略
- SM-4/5：muse task 呼叫 add_memory → deny reason 含 inbox 路徑＋inbox 檔落地（content 原樣）
- SM-9：腳本故障模擬（PATH 砍 jq）→ fail-open 行為記錄（muse 直寫主體——確認非資料遺失形態）
- 邊界：content 含 frontmatter 樣態、path 含子目錄、空 content

---

## S4：consolidation 站

### Context
UC 引用：完成「muse 寫入流」。依賴：S3。語義約束：寫入六問單一源＝memory-audit skill（不重述）；consolidation 是 LLM 面非機械面。

### 核心實作要點
1. **掛點**：夜間收斂波第一步（波前二分之後）加 inbox 掃描段＋memory-audit skill 補「inbox 消費」小節（手動觸發路徑：本 skill session）——**S4 需在 S2 後執行**（兩處同檔面：23:40 cron prompt、SKILL.md——F6）
2. **consolidation 前置——fail-open 第二道偵測（G2-6）**：先跑池 git `status --porcelain`＋diff 歸屬——**無 receipt 且非 CC/ZCode provenance 的變更**（=muse fail-open 直寫的形態特徵）→ quarantine 清單分類處置（git 是獨立於 hook subsystem 的訊號源——hook 全掛時系統仍有第二道訊號）
3. **path contract（G2-2——confused deputy 防護；**T3/T4 修訂後現況單一源＝memory-audit skill「Inbox 消費」節**）**：consolidation 寫主體前逐條機械檢查 payload 的 path——① project scope only ② **池根 basename**（禁子目錄——generator/watch-seed/索引連結只看頂層；T4-2）③ ancestry delimiter-aware（`$AGENT_MEM/` 含尾 slash 前綴；拒 `..` escape／absolute；T3-3）④ symlink component 逐段 lstat 拒絕（containment 僅必要條件；T3-2）⑤ 非 reserved（大小寫無關；`MEMORY.md`、`_inventory.md`、`_resident-set.md`、`_generate_index.py`、`.git/`、`_` 前綴治理檔）⑥ edit 命中已存在且 frontmatter 合法的條目——**攔下的 path 是模型提出的未驗證 input，不得直接當寫入座標**
4. **CAS（G2-3；T3-6 修訂）**：操作類只以 payload 不可變 `tool_name` 判；`_inbox_meta` 出現條件是「path 命中已存在條目」非 tool==edit——`base_sha256` vs 目標條目當前 hash 相等才自動套用；不等（攔截後被 CC/ZCode 改過）→ conflict queue 留人裁；add 類整併時同名已存在 → 同 conflict queue
5. **WAL light（G2-4，user 拍板 LIGHT）**：`new`（inbox root）→ claim（`mv` 進 `processing/`）→ `done/`|`rejected/`（receipt 一行 JSON：來源檔名/去處/時間）；`processing/` 殘留＝中斷證據——停下人判，不自動重跑；hook 端原子發布（temp+rename）保證 consolidation 不讀半檔
6. 流程：inbox 非空 → 前置檢查（要點 2）→ 逐檔 claim → path contract → CAS → 六問 → 合格：補/修 frontmatter → 寫主體 → regen → done receipt；不合格：rejected receipt 記錄理由（任務終態/repo 可推導/未定案→去卡或棄置）
7. cron prompt 補 inbox 步驟（AIR-52 同檔互動——已登記）
8. **逾期 inbox 語義（F5＋G2-13）**：夜掃三 dot-area 不含 `.agents/`——逾期不被靜默清，是 consolidation 停擺警訊；**watchdog 外掛**（G2-13：monitor 與被監控不可同故障域）——oldest-inbox-age 檢查掛 standup/daily-maintain 路徑（排程已存在），非 consolidation 自檢；連續兩晚逾期→升級處置

### Pseudo Code
流程文檔形態（LLM 步驟＋機械檢查清單，非單一腳本）；夜波 prompt 增量。

### 驗證策略
- SM-6：測試 inbox 條目（合格/不合格/path 攻擊樣本〔`../`／absolute／reserved〕/CAS 衝突樣本 各一）→ consolidation 全路徑 → 池條目落地＋regen＋receipt 正確＋攻擊樣本全被 contract 擋下

---

## S5：過渡投影退役＋文檔/條目同步

### Context
UC 引用：更新「muse 唯讀掛載」→「受約束寫入者」。依賴：S1-S4 全綠。注：投影退役已提前併 S1 步驟 2（主體進駐即退役）；本段收尾文檔面。

### 核心實作要點
1. `AGENTS.md`：「Muse memory 唯讀」段改寫——muse 讀主體（read_memory project scope／read_file）＋寫經 inbox（hook 導流）＋禁止直寫條目與索引（品質閘承載）；「觀察池路由」段補新路徑事實
2. memory 條目：divergence 條目收斂（pending 已實現）；cc-alignment 條目 symlink 拓撲段補「CC 端目錄 symlink→repo 內主體」新形態
3. `~/.agents/memory-spine/index.md` 認養表：muse 腿註記「池主體直連（AIR-54）」；ZCode registry 待辦腿維持（後議，不擴 scope）
4. draft-2 標記：探測完成（session.jsonl）＋歸因前提變更註記
5. `.agent-tmp/poc_muse_projection.py`＋`muse-hooks-findings.md`：吸收進 EP 後由夜掃清理（POC 生命週期慣例）

### 驗證策略
- docs mode 驗證：rg 舊敘述殘留（「唯讀」字樣對 muse 段落）零誤引；跨檔路徑一致（AGENTS.md vs skill vs spine index）

---

## S6：mosaic 移植

### Context
UC 引用：橫展「跨池共享記憶主體」。依賴：S1-S5 定型（ai-rules 為模板）。獨立可後延。

### 核心實作要點
0. **既有形態情報（09-09 muse relay，S6 前置）**：mosaic 已有 muse 自建 `.agents/memory/`（MEMORY.md index＋`reference-infra-repo-map.md`＋`shared-memory-pool.md`——活知識，MLM 機制 09-07 user 明示）＋三 WT 目錄層 symlink 共指 main worktree 實體＋`.git/info/exclude` 排除版控。**搬遷前置處置**：muse 自建條目先合併入池主體（過六問＋frontmatter 補全）或遷 `processing/` 暫存，再進主體搬遷。**F2 降級線索**：mosaic 三 WT 目錄層 symlink 下 muse 自述注入正常（未獨立驗證——S6 實測保留，風險由「未驗」降「有實證線索」）
1. mosaic 池主體 → mosaic repo（owning 線 main worktree）`.agents/memory/`（步驟 0 處置後進駐）；版控排除**沿用 mosaic 既有 `.git/info/exclude` 慣例**（不強推 .gitignore）
2. mosaic 的 CC project dir（多個，多 worktree 對應）memory 逐一換 symlink 指實體
3. 其餘 worktree 的 `.agents/memory/` → symlink 指 main worktree 實體（**既有 symlink 在場，驗證即可**）——F2 實測：次 worktree 開 muse task read_memory 經目錄 symlink；若目錄層也拒→**顯性降級**：muse 僅在 owning worktree 一等，次 worktree 的 muse 讀池走 read_file 絕對路徑（已驗穿透）＋AGENTS.md 註明
4. **寫入流＝比照 inbox（user 09-09 定案——直寫 ML M 廢止）**：mosaic 09-07「所有寫入進 MLM」直寫政策隨 S6 廢止——當時是權宜（無跨池主體/hook 契約知識），今天實測下直寫＝投影斷裂（裸寫零 frontmatter→generator 跳過→跨端召回失效）＋品質閘全繞過＋無 CAS；inbox 彌補全部且 muse 自讀能力無損（read_memory(path) 直讀不靠投影）。mosaic 側 hooks.json＋AGENTS.md 同步移植；mosaic 端 muse 政策條目（memory-policy.md「所有寫入進 MLM」）同步改寫
6. mosaic 夜間波/telemetry 路徑比照 S2；**repo 外 bundle 同步落地（G2-11）**：夜波尾巴 `git -C <mosaic 主體> bundle create ~/.agents/memory-bundles/mosaic-$(date +%F).bundle --all`（輪替保留 7 份）——補池 git local-only 的既有備份缺口＋worktree 誤刪面（owning 線 `--force` remove／清理腳本可連 inner .git 一起刪）

### 驗證策略
- SM-12：mosaic 三端開場＋worktree 間 inode 一致性；mosaic 夜波一輪

---

## 整合策略

- 順序閘：S1 三端驗證任一 fail → SM-11 回滾（差異歸屬程序）後修因再手術；CC 載入器拒 symlink（風險 5 成真）→ EP 回退決策點（回退 copy 投影形態，回報 user）
- **夜波尾巴補 repo 外 bundle（G2-11）**：`git -C $AGENT_MEM bundle create ~/.agents/memory-bundles/ai-rules-$(date +%F).bundle --all`＋輪替保留 7 份——刪除 `.bak` 後系統仍有 repo 外 recovery copy（池 git 本 local-only 無 remote，此為既有缺口的輕量補法；掛夜波＝零新機制）
- S2 與 AIR-52 的 cron 同檔互動：先落地者贏、後者對帳（兩弧 UC 盤點互指已登記）
- S3 hooks.json 進版控（repo 資產）；inbox gitignore（durable 不入版控——**逾期 inbox＝consolidation 停擺警訊非垃圾，夜掃三 dot-area 不含 `.agents/`、不靜默清**〔F5 修正——原宣稱的夜掃規則不存在〕；S4 驗證含逾期模擬）
- baseline: 48d0590（EP 定稿時點）。**實作弧邊界澄清（09-09 收尾——review I1）**：48d0590..HEAD 含多弧 commits（AIR-50/56/51/53 已結案弧＋5a6ce2e air-57 建卡〔muse session 順產，非本弧但隨收尾 merge 進 main——commit message 已帶正確卡 id〕）；本弧 S1-S5 實作全部以 **uncommitted working tree** 形態交付、單一 commit 收斂；air-57 draft（draft-5）/air-58 卡為非本弧 untracked 項，具名 add 紀律排除。

## 收尾步驟

1. Capabilities/文檔：AGENTS.md 已於 S5；`skills/CLAUDE.md` 工作流索引檢查是否需補 memory 主體新路徑指引
2. 卡結案：AIR-54 兩步（`-s Done --final-summary` → `--ref` 換 done/ URL）＋弧結案蒸餾第三動（同主題 memory 條目三條——見 UC 盤點）
3. SYSTEM-MAP：不存在，跳過
4. instruction 檔同步檢查：`rules/context-management.md` pointer 面驗證（路徑語義未變則零改）
5. /audit-test：S3 hook 腳本若有可測邏輯（jq 解析/落檔）提煉最小測試；手術程序類段落以驗證報告代替
6. **整體記憶管理機制審視（含 ZCode——user 09-09 拍板）**：弧末產出三端鏈路總圖（muse 原生 scope／CC 目錄 symlink／ZCode 雙跳）＋ZCode 端待辦清點（spine registry routing 待辦腿〔AIR-45 S6 遺留〕、ZCode memory config 面、per-session 記憶行為）＋後續提案落 drafts/或 spine index 更新——審視與提案性質，不擴本弧實作 scope

## EP Review 紀錄

### 第一輪（09-09，獨立 context Explore agent＋主 session judge）

16 findings（6 P1＋10 P2）；judge：15 ✅ 採納、F4 ⚠️ 部分採納（review 引 findings 檔過時推導；實測第三輪攔截即在 bridge task 生效——修 findings 檔而非 EP SM-5，SM-5 補證據錨）。全數已 apply：

| # | finding（摘要） | 判決 | 落點 |
|---|------|------|------|
| F1 | S1 cp/rdir 互斥恆失敗 | ✅ | S1 重寫：mv＋側備份＋rmdir 併發 guard |
| F2 | S6 次 worktree 目錄 symlink vs muse 拒 symlink 未驗 | ✅ | S6 補目錄層實測＋顯性降級聲明；SM-12 |
| F3 | inbox 相對路徑＋hook cwd 未保證 | ✅ | S3 pseudo：dirname $0 絕對路徑推導 |
| F4 | 「bridge task trusted」與 findings 檔矛盾 | ⚠️ | findings 檔修正（實測反證舊記載）；SM-5 補 session 錨＋未 trust 缺口註 |
| F5 | 夜掃 `.agents/` 規則不存在 | ✅ | S4/整合策略改「逾期＝停擺警訊非垃圾」 |
| F6 | S4 與 S2 同檔面未登記 | ✅ | 依賴序改「S4 需 S2 後」 |
| F7 | 掃描範圍漏 corrections-weekly/schedule-registry | ✅ | UC 盤點掃描範圍補列 |
| F8 | 真實共檔面＝SKILL.md/schedule-registry | ✅ | UC 盤點補 AIR-50 S9／AIR-52 S2 共檔登記 |
| F9 | 回滾未涵蓋遷移後寫入與 cron 副作用 | ✅ | S1 驗證策略＋SM-11 差異歸屬＋cron 還原 |
| F10 | 缺 codex 第四端場景（rg 不跟目錄 symlink） | ✅ | 補 SM-13＋S5 路由段指引 |
| F11 | 缺並發/時序防護 | ✅ | S1 要點 0（避 23:40 窗口）＋rmdir guard |
| F12 | 寫後讀 lag 未顯性化 | ✅ | 補 SM-14＋UC 措辭校準（等距讀、寫收斂） |
| F13 | hook 腳本細部缺陷（覆蓋/null/provenance/stub drift） | ✅ | S3 pseudo 重寫（$$／fallback／stdin 全存） |
| F14 | ASSET_SOURCE 歸屬錯（比對在 regen hook 非 generator） | ✅ | 風險 6 重寫（源碼核實） |
| F15 | `_trash-0908` 隨遷灌爆清單 | ✅ | S1 要點 1（trash 進 .bak 不隨遷） |
| F16 | S0 對致命假設空轉 | ✅ | S0 段砍除（與 user 09-09 討論定案一致）；風險 5 降級中、S1 內建 |

### 第二輪（09-09，GPT web 跨 provider 審查＋主 session judge）

架構替代裁決＝**不換架構**（四軸對照「現方案＋WAL/CAS 硬化」最優，與主 session 判斷一致）。13 findings：12 ✅、1 ⚠️；兩個 P0 論據經本地 shell repro 覆現驗證（#1 全對；#10 結論對、細節形態不同——BSD mv 是 move-into nested 而非失敗留池）。user 三點拍板：WAL=LIGHT／bundle 掛夜波＋弧末整體審視含 ZCode／edit CAS 第一版就上。

| # | finding（摘要） | 判決 | 落點 |
|---|------|------|------|
| G2-1（P0） | `mv dir/. dest/` 不可作為搬遷 primitive（repro 屬實） | ✅ | S1 改 whole-directory rename＋同 FS 前置檢查 |
| G2-2（P0） | `tool_input.path` 未驗證升格 privileged write（confused deputy） | ✅ | S4 要點 3 path contract（scope/relative/resolve 邊界/symlink component/reserved） |
| G2-3 | edit_memory 缺 base-version CAS（delayed lost update） | ✅ | hook 附 `_inbox_meta.base_sha256`；S4 要點 4 CAS＋conflict queue |
| G2-4 | inbox 無原子發布/single consumer/idempotency | ✅ LIGHT | temp+rename＋processing/done/rejected＋receipt；不做 full ingestion_id WAL（user 拍板） |
| G2-5 | hook serialization edge（$OUT 未 escape 進 JSON＝fail-open 漏洞；basename 污染；code fence） | ✅ | deny 由 `jq -nc --arg` 構造；payload 純 .json；檔名 TS+pid+content hash |
| G2-6 | fail-open 嚴重度低估（edit＝integrity loss）；需獨立第二道偵測 | ✅ | SM-9 校準＋S4 要點 2（consolidation 前池 git 歸屬檢查——獨立訊號源） |
| G2-7 | Risk 7 問錯問題——gate 是 recall 不是截斷順序 | ✅ | 風險 7 重寫：recall sentinel（自然語言召回＋explicit read 兩測） |
| G2-8 | MEMORY.md 成 muse 強制 context 無 budget | ⚠️ | 部分——B 形態 gate（6,000 chars）已在管；風險 9 補說明，無新機制 |
| G2-9 | 驗證偏 read-path；`.bak` 解鎖太早 | ✅ | S1 要點 8 E2E 矩陣（write-through＋攔截鏈＋consolidation＋夜波 dry-run）為解鎖條件 |
| G2-10 | trash 隔離修法 regression（repro 覆現：結論對、細節異） | ✅ | S1 要點 2 換軌：backup 後直接刪 live garbage |
| G2-11 | worktree lifecycle coupling＋池 git 無 repo 外備份（既有缺口） | ✅ | 夜波尾巴 git bundle（~/.agents/memory-bundles/，輪替 7 份）——ai-rules＋mosaic |
| G2-12 | 升版驗證需 contract suite | ✅ | SM-10 擴四契約 fixture |
| G2-13 | 逾期檢查與 consolidation 同故障域 | ✅ | watchdog 外掛 standup/daily-maintain（S4 要點 8） |

### 第五輪（09-09 收尾，post-build dual-context＋codex 跨家族，18+4 findings 全裁決）

in-harness dual-context（code-reviewer-primed＋code-reviewer，lite/flash）＋codex 獨立審查（4 Important）；findings 帳本＝`.review/air-54.md`。裁決：採納 20、部分 1（setup 腳本函式合併不採——YAGNI）、記錄 1。要點級修正：hook 腳本 jq parse 失敗改 `|| true`（導流 fail-open 直放缺口——fresh F1 實證）、空 stdin guard、lexical gate 拿掉 `*..*`/`*\\*` 誤傷面、`.tmp-*` 偵測語義入 SKILL.md、池 generator 部署同步（ruff format drift）、MULTI-MACHINE cron 資料模型定案 primary-only（副機不回填 registry——codex I3）、EP S3/S4 本文隨實作修訂（hooks.json machine-local flip＋contract 現況——codex I2）、弧邊界澄清（codex I1）。verdict：pass-with-findings → findings 全 apply → followup 重驗綠。

### 第三輪（09-09，跨 provider 終審＋主 session judge＋修畢）

總判 Conditional Pass（架構成立、無新 P0；不關卡、不解 `.bak` gate）。7 findings：6 ✅（1 部分），judge 追加實證兩處（dirty-sensor live 未驗＋watchdog 無排程執行者——比 T3-4 原文再深一層；池全 ASCII basename——T3-7 Unicode 限縮）。修畢待關項＝今晚首波＋P5 執行者拍板。

| # | finding（摘要） | 判決 | 落點 |
|---|------|------|------|
| T3-1（P1） | hook 在 contract 前先 dereference 未驗證 P（read/hash deputy＋大檔 fail-open） | ✅→複審仍開放→再修 | lexical gate＋尾段 symlink 跳過；複審反例 `alias/secret.md`（中間段 symlink 穿透）舊邏輯覆現成立→補 intermediate 逐段 lstat＋2 測試（alias 反例＋nested 正例），9 綠 |
| T3-2（P1） | realpath-containment ≠ symlink-component 拒絕 | ✅ | contract 文字硬化：逐段 lstat（containment 僅必要條件） |
| T3-3（P1） | sibling-prefix 碰撞（`memory-inbox` 誤判池內） | ✅ | delimiter-aware（尾 slash）＋`../memory-inbox/x.md` 回歸樣本 |
| T3-4（P1） | git 第二訊號無獨立執行者；watchdog 只看 inbox age（hook 全掛時沉默） | ✅ | daily-maintain Phase 0 加 porcelain-vs-receipt 第二檢查；執行者缺口記 P5 待拍板 |
| T3-5（P1 方法論） | 自然召回 oracle 太弱（desc 即可答對） | ✅ | sentinel 重做：body-only canary＋telemetry 讀事件 oracle＋快照缺席 negative control |
| T3-6（P2） | meta 條件是 exists 非 tool==edit | ✅ | 行為釘測試（add 指既有亦附 meta）＋consumer 只以 tool_name 判類 |
| T3-7（P2） | 大小寫/Unicode 檔名別名 | ⚠️ | reserved/同名比對大小寫無關化；池全 ASCII，Unicode 暫 N/A |

### 第四輪（09-09，接合處審查＋主 session judge＋修畢）

對象＝HEAD 上 AIR-54 未提交實作；S6／首波／P5 不重算。2 findings 全 ✅＋ruff 整潔。

| # | finding（摘要） | 判決 | 落點 |
|---|------|------|------|
| T4-1（P1） | 異常檢查排在流入快照之後——>30min 直寫先被 `add -A && commit` 收下，偵測訊號滅失 | ✅ | 波前二分③加異常篩（receipt／hook-event／自產出三 allow，三無→quarantine＋停波待裁），走在快照提交前；驗證待首波實測 |
| T4-2（P2） | contract 許子目錄但 generator 只掃頂層→done 卻索引不可見（隔離池 repro：exit 0、0 entries） | ✅ | 合約收緊池根 basename（子目錄明確 rejected）；hook 同步跳過含 slash enrichment（T3-1b walk 被取代、更簡）；nested 測試翻轉；池零子目錄零遷移 |
| ruff | 測試檔 PLC0415 區域 import×3 | ✅ | import 全上頂層；`ruff check`＋`git diff --check` 綠 |
