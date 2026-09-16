# muse memory inbox gate 升級 user-scope plugin（AIR-79，AIR-54 續弧）

> **ep_type**: implementation
> baseline: 5bb410012372a5c332bacf1ff2e7b64f2ea2c719（main，EP 建立當下）

## 實作總覽

把 AIR-54 落地的 per-repo muse memory inbox 閘（`.muse/hooks.json`〔machine-local〕＋`hooks/muse_memory_inbox.sh`）升級為 **user-scope 獨立 muse plugin `muse-memory-governance`**：裝一次（`muse plugins install --scope user`＋`plugins approve`）、所有帶明確 opt-in marker 的 repo 生效。設計已於 09-12 收斂（GLM 主 session arch-thinking＋codex 對抗討論，user 拍板；codex advisory＝bridge job-mtxp38so-dfcac2）——本 EP 承接其決策勿重辯（完整清單＝AIR-79 卡 desc「已決策勿重辯」段）。

核心形態變化：legacy 閘的 repo 解析靠**腳本所在位置**（script-relative，`hooks/muse_memory_inbox.sh:20`）；plugin 腳本住在 machine-global cache，**每次呼叫都要動態解析目標 repo**＋判 marker 三態。divert 語義（atomic 代存 inbox＋deny＋CAS enrichment）與 consolidation 站（memory-audit skill「Inbox 消費」節）**完全不變**——本弧只換承載載體與觸發面。

範圍邊界：plugin source home＝ai-rules；首批 cutover＝ai-rules 自身；mosaic_alpha 側移植由 mosaic 承接（本 EP 僅留介面契約）。delegate plugin 不搭載（獨立 identity）。bootstrap installer（一鍵雙 plugin）不在本弧。

## 段落 0：全域研究摘要

> 研究形態註記：設計討論已收斂 scope（FINDINGS.md 結晶＋AIR-79 卡），研究目標可精確枚舉——由主 session 直讀已知錨點檔完成（非 cr-research spawn）；shell/json/md 面無 symbol graph 需求。probe scratch（delegate-bridge `.agent-tmp/muse-plugin-probe/`）已吸收進本 EP，EP 不依賴該路徑。

### Live-probed 機械事實（muse 1.1.1，09-12 實測——設計輸入，勿重測）

1. `muse plugins install <path> --scope user` 可用；cache 為 content-addressed（`~/.local/share/muse/plugins/cache/local/<id>/<package_sha>/package`）。
2. manifest＝nested `.muse-plugin/plugin.json`（`schemaVersion:1`＋`compat.manifestDir`＋`capabilities.hooks[] = {id, event, command[]}`，command 為 plugin-root-relative）；**exactly ONE** nested manifest（`.muse-plugin`/`.codex-plugin`/`.claude-plugin` 擇一——雙 manifest 被 reject）。
3. **plugin hooks 無 matcher**（event-keyed only；官方回覆 matcher aliasing 另案追蹤）——腳本必須 self-filter stdin `tool_name`。
4. deny 合約與 project-level gate 同構：stdout `{hookSpecificOutput:{permissionDecision:"deny",...}}`（`muse plugins hook test`＋fixture 已驗證）。
5. trust：install 後 `trust:"user-local"`＋警告「hooks require review before activation」；`plugins approve` per capability 才會 live firing。
6. optional hook 欄位：`timeout_ms`、`async`。
7. probe plugin 已完整移除（machine 乾淨）。

### 可複用基礎設施

| 元件 | 位置 | 用法 |
|---|---|---|
| legacy 閘腳本（divert 全邏輯） | `hooks/muse_memory_inbox.sh:1-62` | S1 以其為基底改寫（保留 lexical gate／CAS／atomic 語義逐條） |
| pytest fixture 模式（tmp-repo skeleton＋subprocess 驅動） | `tests/test_muse_memory_inbox.py:20-46` | S1 測試沿用同形態 |
| hook stdin/deny 合約實證 | `hooks/muse_memory_inbox.sh:9-16`（09-09 實驗註記） | 沿用；muse 對 hook 失敗 fail-open 是設計前提 |
| 最小 plugin skeleton | probe `p2/`（已吸收——manifest 欄位逐項內聯於 S1 要點 1/4，EP 不依賴 scratch 路徑） | 參考用；非 build 輸入 |
| inbox 消費站（WAL state machine＋path contract） | `skills/memory-audit/SKILL.md:76-87` | **不動**——契約相容性是 S1 驗收條件 |
| watchdog（inbox liveness 雙檢查） | `skills/daily-maintain/SKILL.md:45` | 不動；S5 確認零 drift |
| hook 往返 smoke | `hooks/verify-memory-topology.sh:51-57,60-67` | S4 cutover 後兩段改造：51-57 hooks.json 存在性檢查→plugin approve 健檢；60-67 往返改指 plugin 腳本 |

### 依賴關係與關鍵約束

- 控制面消費端（改動須同步）：`AGENTS.md:108`（專案結構 Muse memory 段）、`skills/memory-audit/SKILL.md:78`（hook 承載形態句）、`hooks/AGENTS.md:37`＋`hooks/MULTI-MACHINE.md:23,28`（setup-muse-hooks 條目）、`hooks/verify-memory-topology.sh:51-57,60-67`（51-57 hooks.json 存在性檢查＋60-67 smoke 往返——cutover 後兩段都要處置）、`ai-analysis/blueprint/onboarding.md:182,187,190,263,287`（教 setup-muse-hooks／含指向 setup 腳本的相對連結）、`ai-analysis/blueprint/workflow.md:166`、`ai-analysis/blueprint/index.html:409`、`.gitignore:66-67`（註釋指名 setup 腳本＋`.muse/hooks.json` 條目）。排除面（不動＋理由）：`ref-docs/harness/contracts.md:15` 對 `.muse/hooks.json` 的描述是 vendor capability 事實（外部文檔鏡像）；`ai-analysis/reports/`、`_tasks/_archived/`、`backlog/` 命中屬歸檔/歷史面。〔審查修訂：EP 初版宣稱「rg＝上述集合」不實——初掃 `head -15` 截斷漏 blueprint 三檔＋.gitignore（M/C 兩腿獨立糾出；modern-cli-preference「盤點雙掃陷阱」實證）〕
- consolidation 契約耦合：inbox payload 格式（原始 tool_input JSON＋`_inbox_meta`）與 path contract 六條（memory-audit skill）——plugin 產物必須位元組級相容，否則夜波消費站 silently reject/mismatch。
- muse fail-open 前提：hook 腳本故障（exit≠0/bad schema）→ tool 照跑＝直寫池。legacy 靠「腳本極簡＋dependency-light」自守；plugin 版在 governed repo 必須反轉為 **fail-closed**（marker 宣告治理即不得 fail-open——設計決策④，見卡）。

### 類似實作位置

- per-repo hook 註冊形態：`.muse/hooks.json`（machine-local，`hooks/setup-muse-hooks.sh:15-25` 生成）——即本弧要退役的 legacy shim。
- delegate-bridge plugin（nested manifest 結構參考；其雙 nested manifest 被 muse exactly-one 規則拒——不可搭載的原因之一）。

### 風險假設清單

| # | 假設 | 等級 | 驗證落點 |
|---|---|---|---|
| A1 | plugin hook 經 approve 後在 live（非 `hook test` 夾具）session 真的 fire | **致命** | S2 P-ACT-D/P-ACT-B；offline 已探測間接證據（`plugins hook test` 過）但 live 未證 |
| A2 | bridge headless spawn 的 muse 讀 user-scope plugin registry | **致命**（UNKNOWN） | S2 P-ACT-B |
| A3 | hook stdin 帶 host workspace 欄位 | 高 | S2 P-WS；缺席→upward git resolution 遞補（設計已雙路） |
| A4 | plugin 升級（reinstall 新 content）不需重新 approve | 高 | S3 P-UPGRADE；若重置→headless 靜默 fail-open，須 setup health check |
| A5 | 每 tool-call spawn overhead（無 matcher＝全 tool call 都 spawn）在可接受 budget | 中 | S3 P-OVERHEAD |
| A6 | untrusted workspace 的 suppress 形態（何謂 trusted） | 中 | S2 P-UNTRUSTED（觀察項，非繞過目標——決策⑥：合理邊界） |
| A7 | hostile repo 經 marker＋symlink inbox 把 user 權限寫入導向站外 | 中 | S1 設計防護（inbox 路徑逐段 lstat 拒 symlink；見 S1 要點⑤）＋S2 觀察 |
| A8 | `git rev-parse --show-toplevel` 在 hostile cwd 的安全性 | 低 | rev-parse 不執行 repo hooks；S1 註記 PATH 依賴面（jq/git），untrusted suppress（A6）為主要收斂邊界 |

**致命假設的 EP 存活性**：A1/A2 任一失敗→觸發 **fallback 形態**（決策⑨：薄 per-repo registration＋單一共享 hook artifact）——EP 段落 S1/S4 的腳本與測試在 fallback 下**全數保留**（邏輯同一份），僅承載層換（user-scope plugin → per-repo hooks.json 指向共享路徑）。fallback 判定點＝S2/S3 gates 後（見整合策略）。

## UC 盤點

### Backlog 關聯

- AIR-79（本弧追蹤卡，已建已 commit——desc 三必有自足）；血統＝AIR-54（done，機制建立弧）。
- 自動建卡結果：無新建——本 EP 單一 UC 由 AIR-79 承載。

### SYSTEM-MAP 影響

無 SYSTEM-MAP.md（meta-project）——正當跳過。

### 掃描範圍

- `AGENTS.md`（專案結構 Muse memory 段）、`hooks/AGENTS.md`、`hooks/MULTI-MACHINE.md`、`skills/memory-audit/SKILL.md`、`skills/daily-maintain/SKILL.md`、`hooks/verify-memory-topology.sh`、`backlog task list --plain`（AIR-54 done／AIR-79 To Do）。
- 建卡前去重（09-12）：`backlog search "muse memory inbox plugin"`／`"memory-governance"` 零命中；`ai-analysis/_inbox/pending-decisions.md` 零命中。

### 同主題 memory 條目（結案蒸餾範圍）

- 掃描 `.agents/memory/_inventory.md`（rg muse/inbox）：**零直接命中**（命中項皆 dispatch/harness 詞彙域，非本弧機制）——結案蒸餾預期「無相關條目」，屆時明示。

### 既有 UC 狀態

| 能力 | 狀態 | 來源 | 影響 | 說明 |
|---|---|---|---|---|
| muse memory 寫入流受約束（AIR-54：PreToolUse 閘→inbox→consolidation） | ✅ | `AGENTS.md:108`＋`hooks/muse_memory_inbox.sh` | 更新 | 承載層換 user-scope plugin；閘語義與消費站不變 |

### 新增 UC

| 能力 | 狀態 | 實作路徑 |
|---|---|---|
| muse memory 寫入閘 user-scope plugin 化——跨 repo 單一邏輯源＋版本化 marker 三態 opt-in（absent→allow native／valid→divert／malformed→deny） | 📋 | `muse-plugins/memory-governance/` |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|---|---|---|---|---|
| SM-1 | muse 在 governed repo 寫 memory | `add_memory`/`edit_memory`＋marker valid | 代存 inbox＋deny（與 legacy 位元組級同構） | 無 | 新增 UC |
| SM-2 | muse 在 ungoverned repo 寫 memory | 同上但 marker absent | allow native（零攔截、零落地） | 無 | 新增 UC |
| SM-3 | marker 宣告了但壞掉 | JSON parse 失敗／`protocol` 非 integer `1`（`0`／`-1`／`"1"`／`null`／`true`／`false`——型別混淆全屬 invalid，非僅 `>1`） | **deny＋報錯、不落地**（禁 fail-open） | 修 marker 後重試 | 新增 UC |
| SM-4 | marker 是未來版本 | `protocol: 2`（integer >1） | deny＋報錯（unsupported） | 升級 plugin | 新增 UC |
| SM-5 | 遷移疊窗：legacy 閘還在 | `.muse/hooks.json` 存在**可工作的 legacy owner**（structured 判準，見 S1 要點 ④） | plugin-origin 呼叫 **no-op**（exit 0，legacy 全權）；legacy-origin（wrapper 帶 mode env）照 divert | 逐 repo cutover 完刪 shim | 新增 UC |
| SM-6 | bridge headless 委派 muse 寫 memory | bridge `task --family muse` 於 marker repo（workspace root 判準見 S2 P-ACT-B） | hook 照 fire＋inbox receipt（UNKNOWN 待證） | S2 gate ③ | 新增 UC |
| SM-7 | untrusted workspace | muse suppress 判定 | plugin 不執行（合理安全邊界，不繞） | 無 | 新增 UC |
| SM-8 | 非 memory 工具呼叫 | 任意其他 `tool_name` | self-filter 早退（最快路徑，零寫入） | 無 | 新增 UC |
| SM-9 | plugin 升級 | reinstall 新 content | approve 續存→照 fire；重置→health check 攔截 | S3 gate ⑤ | 新增 UC |
| SM-10 | 從子目錄跑 muse | cwd＝repo subdir | upward git resolution 找到 repo root 後照三態 | 無 | 新增 UC |
| SM-11 | 非 git 目錄跑 muse | `git rev-parse` 判定非 git repo（與 git binary 缺失/執行錯誤分流，見 S1 要點 ②） | allow native（等同 SM-2） | 無 | 新增 UC |
| SM-12 | hostile repo 放 marker＋symlink inbox | inbox 逐段 lstat 命中 symlink | deny＋報錯、**不落地**（導流寫入拒絕）；inbox 尚未存在的路徑段（ENOENT）＝safe（將來自建） | 無 | 新增 UC |
| SM-13 | stdin 空／非 JSON | hook 收到空或無效 payload | exit 0（legacy `muse_memory_inbox.sh:24` 早退語義繼承） | 無 | 新增 UC |
| SM-14 | marker valid 但 plugin 未 approve／disabled | capability 未 activation（trust≠per-capability approve，見 §1b 兩層 invariant） | muse 本身 fail-open→原生寫（activation 層缺口——非 marker 可防）；偵測面＝consolidation 異常篩＋daily-maintain 直寫偵測＋S3 health check | S3 gate ⑤ | 新增 UC |

## 段落劃分原則

依賴序：S1（本體＋單元測試，零 muse 依賴）→ S2（live 環境 probe：activation/workspace/untrusted）→ S3（量測：upgrade/overhead）→ S4（gates 全綠才 cutover ai-rules＋legacy 退役）→ S5（控制面同步＋cleanup）。S2/S3 可平行。垂直切片：S1 交付可獨立測試的完整腳本；S2/S3 交付 evidence；S4/S5 交付部署與文檔。語義約束顯式標記於各段。

---

## S1：plugin 本體——manifest＋三態 marker 閘＋單元測試

### Context

- **背景**：legacy 閘（`hooks/muse_memory_inbox.sh`）以 script-relative repo 解析＋per-repo hooks.json 註冊。plugin 版腳本住 machine-global cache，需 per-call repo 解析＋marker 三態；divert 語義必須與 legacy 逐條等價（consolidation 站不可感知差異）。
- **需求邊界繼承**：無 `/spec`——邊界由 AIR-79 卡已決策段承載（Always：marker 三態語義、legacy no-op、fail-closed in governed repo、untrusted 不繞；Never：不禁 fail-open 於 governed repo、不搭 delegate plugin、不動 consolidation 站）。
- **UC 引用**：實作「muse memory 寫入閘 user-scope plugin 化——跨 repo 單一邏輯源＋版本化 marker 三態 opt-in」。
- **依賴關係**：S2-S4 全部消費本段產物；無外部段落依賴（可獨立 build＋測試）。
- **語義約束**：與 S4 共享「marker 檔名＝`.agents/memory-governance.json`、`protocol:1`（integer，非 1 全 invalid）」；與 S2 共享「stdin workspace 欄位探測優先序——**resolver＝provisional seam**：S2 P-WS 凍結欄位後回寫 S1 常數並**重跑完整 S1 acceptance**（該 code change 計入 S2 commit；S1 不宣稱對 workspace contract 封閉）」；與全部段落共享「inbox payload 格式＝legacy **wire/schema 語義相容**（consumer 依 `tool_name`/`path`/`_inbox_meta` 欄位語義運作；不做 byte parity——whitespace/key order 非 invariant）」。
- **基礎設施盤點**：見段落 0 表——legacy 腳本＋pytest fixture 模式＋p2 skeleton。
- **依賴錨點**：`muse_memory_inbox.sh` → 定義 `hooks/muse_memory_inbox.sh:17-62`（main body）／消費 `.muse/hooks.json`（machine-local）＋`tests/test_muse_memory_inbox.py:31-39`（subprocess 驅動）；`setup-muse-hooks.sh` → 定義 `hooks/setup-muse-hooks.sh:15-25`／消費 `hooks/MULTI-MACHINE.md:28`。
- **技術選型**：bash＋jq＋coreutils（沿用 legacy——muse hook 環境最薄依賴面；禁 python：hook 環境 PATH 不可假設）。單元測試＝pytest（repo 既有 tests/ 基建，subprocess 驅動 bash 腳本）。
- **成功標準**：單元測試覆蓋 SM-1/2/3/4/5/8/10/11/12 全綠；`uv run pytest tests/test_muse_memory_governance_plugin.py` 於乾淨環境可重跑。

### 1b. Invariant Impact（兩層拆解——審查修訂）

- **受影響 domain invariant**：「muse 寫入必經 inbox」拆兩層——
  - **① activation/liveness invariant**：plugin capability 確實載入且會 fire。marker 三態只在 hook **已被執行**後生效——plugin 未 approve／disabled／載入失效時 muse 本身 fail-open，marker 無防護力（SM-14）。守護面＝S2 gate ③（live activation）＋S3 gate ⑤（upgrade/health check——注意 `trust:"user-local"` ≠ per-capability approve，健檢欄位須實證）＋既有第二道（consolidation 波前異常篩 `skills/memory-audit/SKILL.md:82`＋daily-maintain Phase 0 直寫偵測 `:45`）。
  - **② in-hook invariant**：hook 進入且 repo marker valid 後，任何內部故障 → deny（fail-closed）——僅此層是 S1 腳本的責任邊界。
- **critical path 觸及**：silent-corruption path——兩層任一靜默失效＝muse 直寫池無 crash 訊號。
- **驗證對齊**：②層＝三態矩陣測試＋bootstrap failure 分流測試（見要點 ⑦）；①層＝S2/S3 live 證據＋health check（S1 測試不覆蓋也不宣稱覆蓋）。

### 核心實作要點

1. **目錄**（source home）：
   ```
   muse-plugins/memory-governance/
   ├── .muse-plugin/plugin.json      # schemaVersion:1, name muse-memory-governance,
   │                                 # capabilities.hooks[{id:memory-inbox, event:PreToolUse,
   │                                 #   command:["hooks/muse_memory_governance.sh"]}]
   ├── hooks/muse_memory_governance.sh
   └── README.md                      # install/approve/uninstall 操作與 trust 語義（無版本號/日期）
   ```
   腳本命名與 legacy（`muse_memory_inbox.sh`）刻意分流——遷移窗兩者並存期零混淆。
2. **腳本決策序**（每步早退，最快路徑在前；deny 發射一律 **jq-free printf 模板**——jq 缺失時仍能產出合法 deny schema）：
   ① self-filter：stdin `tool_name` ∉ {add_memory, edit_memory} → exit 0（SM-8；無 matcher 的代價控制）。
   ② repo 解析（決策⑦）：`GOVERNANCE_REPO` env 在場（launcher/wrapper 注入）→ 直接採用；否則 stdin host workspace 欄位（欄位名＝S2 P-WS 凍結，腳本以候選序探測＋容忍缺席——provisional seam）→ `git rev-parse --show-toplevel`（$PWD 向上）。**解析結果分流**：判定非 git repo（rev-parse 明確回 not-a-repo 語義）→ exit 0（SM-11）；git binary 缺失/執行錯誤（無法判定）→ 視 ⑦ 分流規則。**禁假設 $PWD==workspace root**。
   ③ marker 三態（決策④）：`<repo>/.agents/memory-governance.json`——absent → exit 0（SM-2）；jq parse＋`protocol` 為 integer `1` → 進 ④；**其餘一切**（parse 失敗／缺欄／`0`/`-1`/`"1"`/`null`/`true`/`false`/integer >1）→ **deny＋reason（不落地）**（SM-3/4；型別混淆域全數 invalid）。
   ④ legacy 共存（決策⑤）——**structured「可工作 legacy owner」判準**（字面掃描會誤判 stale/malformed/他腳本註冊而錯誤 surrender，兩腿審查獨立命中）：jq parse `<repo>/.muse/hooks.json` → 存在 PreToolUse entry，其 matcher 語義涵蓋 `add_memory|edit_memory`，**且註冊 command 的 realpath ≠ 本腳本自身（self-exclusion）**，**且該 command 檔存在＋executable**——三條全過 → exit 0（SM-5）；malformed JSON／stale command／wrong command／partial matcher → **不是可工作 owner，不 surrender**（照走 ⑤⑥——legacy 已死時 plugin 接手，不留裸露窗）。
   ⑤ 安全防護（A7）：`<repo>/.agents/memory-inbox` 逐段 lstat——任何已存在的 symlink component → deny＋reason（不落地）（SM-12）；**ENOENT 段（inbox 尚未存在）＝safe**（hook 將自建）。
   ⑥ divert＝legacy 逐條等價：umask 077、atomic tmp+rename、檔名＝timestamp+pid+content-hash、CAS enrichment（lexical gate T3-1/T3-3/T3-2/T4-2 全保留）、deny reason 帶 inbox 絕對路徑。
   ⑦ **fail-closed 分流**（bootstrap failure taxonomy——「確定非 governed」與「無法判定」分流，deny 發射 jq-free）：
      - marker **absent**（已解析 repo＋已讀目錄狀態）→ exit 0 allow（確定非 governed）。
      - **marker 在場（valid/invalid 皆然）後**任何依賴故障（jq 失敗/寫入失敗）→ printf 靜態 deny（governed 宣告即 fail-closed）。
      - **無法判定層**（jq 缺失導致無法 parse tool_name/marker，且 crude bash 字串比對命中 memory-tool 特徵）→ printf 靜態 deny＋reason「governance tooling degraded」（無法評估 opt-out 時保守拒絕；jq 缺失屬機器異常，修復指引入 reason）。
      - git binary 缺失（無法解析 repo、看不到 marker）→ allow（等同不可解析；機器無 git 時 muse workspace 概念本就不成立）——與「rev-parse 明確 not-a-repo」同走 exit 0，但測試分開釘（兩種到達路徑不同）。
3. **legacy wrapper 過渡（origin-mode 機制）**：`hooks/muse_memory_inbox.sh` 改為薄 launcher——`GOVERNANCE_ORIGIN=registered GOVERNANCE_REPO=<絕對路徑（dirname $0/..）> exec <共享腳本>`。共享腳本見 `GOVERNANCE_ORIGIN=registered` → **跳過 ②③④**（repo 顯式給定；自己的註冊不得自我 no-op；**marker 檢查也跳過——registered 閘無條件 divert，等同改造前 legacy 行為**。〔S1 實作裁定：原設計「marker 三態保留」會使 S1→S4 marker commit 前的 registered 閘靜默消失——重演 C1 根因；遷移窗契約以「與改造前 legacy 行為等價」為準，既有 10 個 legacy 測試零改動通過即此契約的機械證據〕）。**wrapper 的共享腳本解析序**（不得寫死 content-sha cache 路徑——腳本迭代即斷鏈→exec 失敗→exit≠0→fail-open）：①`MUSE_MEMORY_GOVERNANCE_HOME` env（測試注入用，預設 `~/.local/share/muse-memory-governance`）下 `current` symlink；②**repo 本地副本** `<repo>/muse-plugins/memory-governance/hooks/muse_memory_governance.sh`（部署窗回退——S1 commit 到 S4 install 之間固定安裝點尚未存在，repo 副本必在）；③雙失敗 → wrapper 自行 printf 靜態 deny（fail-closed 延伸到 launcher 層），禁裸 exec 失敗。此機制同時服務 fallback per-repo registration（見整合策略）——wrapper 化後遷移窗（S1 commit→S4 marker commit）閘語義不變。〔09-12 開工修訂：解析序加 repo 本地回退＋env override——原設計在部署窗會 deny-all（固定安裝點未存在）且測試無法隔離 machine 路徑；偏差屬實作落差修正〕
4. **manifest**（nested `.muse-plugin/`，exactly-one 規則）——欄位（**install 實證修正**：`version`/`description` 必填、`timeout_ms` 不支援——見 `poc/poc_activation.md` O1）：`{"schemaVersion":1, "name":"muse-memory-governance", "version":"0.1.0", "description":"…", "compat":{"manifestDir":".muse-plugin"}, "capabilities":{"hooks":[{"id":"memory-inbox","event":"PreToolUse","command":["hooks/muse_memory_governance.sh"]}]}}`——deny 需同步結果，**禁 `async`**。

### Pseudo Code

```
# muse_memory_governance.sh（決策序骨架；deny() 一律 printf 模板、不經 jq）
IN=$(cat); [ -n "$IN" ] || exit 0                       # SM-13
crude_match_memory_tool "$IN" || exit 0                  # ① self-filter（bash 字串比對，不經 jq）
command -v jq >/dev/null || { crude命中 && deny_degraded || exit 0; }   # ⑦ 無法判定層
[ -n "${GOVERNANCE_REPO:-}" ] && REPO="$GOVERNANCE_REPO" \
  || REPO=$(resolve_repo "$IN")                         # ② env→stdin 欄位→git；not-a-repo/binary缺→exit 0
[ "$GOVERNANCE_ORIGIN" = registered ] || legacy_owner_works "$REPO" && exit 0
                                                        # ④ structured 判準（parse+matcher語義+realpath≠self+executable）
ST=$(marker_state "$REPO")                              # ③ absent|valid|invalid（integer 1 之外全 invalid）
[ "$ST" = absent ] && exit 0
[ "$ST" = invalid ] && deny "memory-governance marker malformed/unsupported: <repo>"   # 不落地
inbox_safe "$REPO" || deny "inbox path fails symlink/containment check"                 # ⑤ ENOENT 段=safe
PAYLOAD=$(cas_enrich "$IN" "$REPO")                     # ⑥ legacy lexical gate 逐條
atomic_land "$REPO/.agents/memory-inbox" "$PAYLOAD" || deny "governed: divert failed"  # ⑦ fail-closed
deny "已代存 inbox: <path>（consolidation 站將處理入池）"

# hooks/muse_memory_inbox.sh（legacy launcher——遷移窗語義不變）
GOVERNANCE_ORIGIN=registered GOVERNANCE_REPO="$(cd "$(dirname "$0")/.." && pwd)" \
  exec ~/.local/share/muse-memory-governance/current/hooks/muse_memory_governance.sh \
  || printf_deny "legacy launcher: shared core unresolvable"   # fail-closed，禁裸 exec 失敗
```

### 驗證策略

- **測試類型**：單元（pytest＋subprocess 驅動，tmp-repo skeleton fixture——沿用 `tests/test_muse_memory_inbox.py` 模式）；無外部 API mock（jq/bash 真跑）。
- **關鍵情境**：SM-1/2/3/4/5/8/10/11/12/13 逐條對應測試；加：
  - **marker 值域矩陣**：integer 1 唯一 valid——`0`/`-1`/`"1"`/`null`/`true`/`false`/缺欄/parse 失敗全數 deny（型別混淆域）。
  - **legacy-owner 判準負面組**：malformed JSON／stale command／command 指向他腳本／partial matcher → 不 surrender（照 divert）；**同 repo 雙 origin 對照**：matcher 在場時 plugin-origin＝no-op、registered-origin（launcher env）＝deny+land。
  - **jq-free deny 自洽**：jq 從 PATH 移除時——crude 命中 memory tool → 靜態 deny；非 memory tool → exit 0；governed（marker valid）內部 jq 故障 → deny。
  - **repo 解析分流**：rev-parse not-a-repo vs git binary 缺失（兩路徑分開釘）。
  - **launcher 層**：固定安裝點 symlink 解析失敗 → printf deny（fail-closed）；成功 → registered origin 跳過 ②④ 行為驗證。
  - CAS、atomic、umask、非 .md path lexical gate 繼承、inbox ENOENT=safe、symlink inbox=deny。
- **已知未覆蓋**：live muse 行為（A1/A2/A3）——S2 範圍；overhead——S3 範圍；activation 層 invariant（SM-14）——S2/S3 live 證據＋health check。
- **完成檢查**：`uv run pytest tests/`（含既有 289 baseline 全綠）＋ `bash -n` 語法檢查（腳本於乾淨 PATH）。

---

## S2：live probe——activation（direct/bridge）、stdin workspace 欄位、untrusted 形態

### Context

- **背景**：offline 探測（`plugins hook test`）已證 deny 合約，但 **live firing**（A1）與 **bridge headless registry 讀取**（A2）UNKNOWN；stdin workspace 欄位（A3）決定 repo 解析主路徑。
- **UC 引用**：驗證「user-scope plugin 化」的可用性前提。
- **依賴關係**：消費 S1 產物；產出餵 S4 gate ③ 與整合策略 fallback 判定。
- **語義約束**：與 S1 共享 marker/spec 凍結值；probe 用腳本可為 S1 腳本的儀器變體（stdin 鍵位 dump 開關），**probe 完必復原 machine 乾淨**（沿 FINDINGS 紀律：裝→測→移除）。
- **基礎設施盤點**：bridge `task --family muse`（ai-rules workspace 委派）；fixture 形態沿 probe `fixture.json`。
- **依賴錨點**：memory-inbox 消費站 → 定義 `skills/memory-audit/SKILL.md:83-87`（receipt 形態）／消費＝本段觀察 inbox receipt 落地。
- **技術選型**：probe 以可重跑腳本形態落任務家 `poc/`（`poc/poc_activation.md` 記錄程序＋證據；muse 操作列命令）。
- **成功標準**：四項 probe 各有 YES/NO 結論＋原始輸出節錄；machine 狀態復原（`muse plugins list` 乾淨）。

### 1b. Invariant Impact

- 無（probe 段唯讀觀察＋可復原操作；不觸寫入契約——probe 的 add_memory 呼叫落在 probe repo 的 inbox，屬閘正常導流）。

### 核心實作要點

1. **P-WS（stdin workspace 欄位）**：儀器化腳本 dump stdin key 結構（muse direct＋bridge 兩形態各取樣）；凍結欄位名與優先序**回寫 S1 resolver 常數並重跑完整 S1 acceptance**（code change 計入本段 commit——S1 resolver 是 provisional seam）。
2. **P-ACT-D（direct live activation）**：install→approve→真 muse session 呼叫 `add_memory`（marker valid 之 probe repo）→ 觀察 inbox receipt＋deny。direct 互動形態需 user 在場協作（或 headless `muse exec` 直跑——兩者取其一併記錄形態；bridge 必經規範限制的是 repo 任務委派，機制 probe 的 direct 腿屬診斷非委派，先 bridge 腿自動化、direct 腿 user 協作）。
3. **P-ACT-B（bridge headless——workspace identity 釘死）**：bridge child muse 的 workspace root＝spawn 時 git root（cwd 契約）——**nested probe repo 的 marker 不是 muse 所見 workspace，屬 mis-probe**。positive lane 做法（擇一，build 時記錄採用形）：(a) 以 dedicated probe repo 為 workspace（bridge 自 probe repo cwd 派工）；(b) ai-rules 暫時性 marker——此形 **teardown 必含清 probe receipt＋`git -C <池> status --porcelain` 對帳**（防 probe junk 進真池/夜波收走）。trusted probe workspace 與 P-UNTRUSTED 分 lane 記錄。結論同時回答 A2（registry 讀取）。
4. **P-UNTRUSTED（untrusted 形態觀察）**：非信任目錄（隨意 tmp clone）重複 P-ACT 最小形——記錄 suppress 行為與「trusted」判定線索（觀察項，禁繞過——決策⑥）。
5. **時序**：全 probe 在**暫時 marker**環境跑；ai-rules 正式 marker 到 S4 才落——避免半套治理狀態。

### Pseudo Code

```
for probe in P-WS P-ACT-D P-ACT-B P-UNTRUSTED:
  setup probe-repo (marker valid) → install plugin --scope user → approve
  drive muse (direct / bridge task / untrusted dir)
  observe: inbox receipt? deny in transcript? stdout schema?
  record YES/NO + raw evidence → poc/poc_activation.md
teardown: plugins remove → `muse plugins list` clean → marker cleanup
```

### 驗證策略

- 證據形態：每 probe 附命令列＋原始輸出節錄（jobId／transcript 路徑）；結論行 YES/NO。
- 完成檢查：`muse plugins list` 乾淨；probe repo 殘留清單空；`poc/poc_activation.md` 四段齊。
- 已知未覆蓋：muse 版本漂移（1.1.1 事實集——升級重測屬後續維護，不屬本弧）。

---

## S3：量測 probe——upgrade re-approval＋per-tool-call overhead budget

### Context

- **背景**：A4（approve 語義）與 A5（無 matcher 全 tool call spawn）是 cutover 前最後兩個量測型 gate；A4 失敗形態（靜默 fail-open 直寫）必須有 health check 攔截。
- **UC 引用**：驗證「user-scope plugin 化」可運維性（升級不停擺、效能可承受）。
- **依賴關係**：消費 S1 腳本；可與 S2 平行；產出餵 gate ④⑤ 與 fallback 判定。
- **語義約束**：與 S2 共享 machine-clean 紀律（裝→測→移除）。
- **基礎設施盤點**：`muse plugins hook test`（可計時的 offline 往返）＋fixture；shell 計時（`time` 迴圈／hyperfine 若在場）。
- **依賴錨點**：無新錨點（S1 腳本＋S2 程序）。
- **技術選型**：量測腳本落 `poc/poc_overhead.sh`（可重跑）；結果表落 `poc/poc_activation.md` 量測節。
- **成功標準**：gate ④⑤ 各有量測數字＋判定（budget 內/外）；health check 產物（若 A4 失敗形態成立）落地。

### 1b. Invariant Impact

- 無（量測段；A4 攔截設計屬運維面，不動寫入契約本體——閘失效時的第二道防線已由 consolidation/daily-maintain 承擔）。

### 核心實作要點

1. **P-UPGRADE**：install v1（content A）→ approve → bump content（v2）→ reinstall → live 呼叫：fire＝approve 續存；不 fire＝**重置形態成立**。**approval 欄位實證**（activation invariant 的一環）：`trust:"user-local"` 與 per-capability `plugins approve` 是兩個狀態——先實證哪個 machine-readable 欄位真正代表 capability approval/activation（`plugins list`/config 面逐欄查），health check 檢**該欄位**；無可靠靜態欄位 → health check 改用**能證 live firing 的 probe**（一次性輕量 add_memory 往返）。重置形態成立 → health check 納入安裝程序（README）＋`hooks/verify-memory-topology.sh` 擴節。
2. **P-OVERHEAD**：兩軸量測——(a) 腳本軸：fixture 驅動 N 次（非匹配 tool 早退路徑＋divert 全路徑各一組）取 median/p95；(b) runtime 軸：`muse plugins hook test`（含 muse spawn 面）往返計時對照 install 前後。budget 提案（評審可調）：早退 ≤100ms median（腳本軸）、divert ≤250ms、runtime 往返增量 ≤300ms——超標且不可收斂（腳本已極簡）→ fallback 判定輸入。
3. **收斂手段預留**（超標時先試再 fallback）：早退路徑的 jq 依賴延後（crude bash 字串比對先行，jq 僅 governed 路徑使用——S1 ①已是此形）。

### Pseudo Code

```
P-UPGRADE: install(A) → approve → drive(fire=YES) → install(B) → drive(fire=?)
  → NO: health-check artifact + README 節
P-OVERHEAD: for path in early_exit divert: loop N { time fixture|script }
  → median/p95 table → vs budget → PASS/FAIL(→fallback input)
```

### 驗證策略

- 證據形態：量測表（原始數字）＋判定行；upgrade 兩輪 live 觀察輸出。
- 完成檢查：`muse plugins list` 乾淨；數字與判定落 `poc/poc_activation.md`。
- 已知未覆蓋：muse 未來 native matcher 支援（官方另案）落地後的 overhead 重測。

---

## S4：cutover ai-rules——marker 落地＋plugin 常駐＋legacy 退役

### Context

- **背景**：五個 cutover gate（整合策略表）全綠後執行；ai-rules 是首批標的，同時是 plugin source home（dogfood）。
- **UC 引用**：交付「user-scope plugin 化」於首個 repo 生效。
- **依賴關係**：消費 S1（腳本）＋S2/S3（gate 證據）；產出餵 S5（文檔同步的事實基準）。
- **語義約束**：與 S1 共享 marker 凍結值；「逐 repo cutover 後刪 shim」（決策⑤）——本段只動 ai-rules 的 shim；mosaic shim 由 mosaic 側承接（介面契約＝marker 檔案＋plugin install/approve 程序＋本 EP）。
- **基礎設施盤點**：`hooks/verify-memory-topology.sh:60-67`（smoke 往返——cutover 後改指 plugin 腳本）；`hooks/setup-muse-hooks.sh`（退役對象）。
- **依賴錨點**：`.muse/hooks.json` → 生成 `hooks/setup-muse-hooks.sh:15-25`／消費 muse runtime（machine-local 檔，退役即刪）。
- **技術選型**：無新工具——既有 muse CLI＋git。
- **成功標準**：ai-rules 上 muse 寫入經 plugin 導流（live 證據）；legacy 檔面清乾淨；`verify-memory-topology.sh --smoke` 綠。

### 1b. Invariant Impact

- **受影響 domain invariant**：同 S1（寫入必經 inbox）——cutover 當下是 invariant 的載體切換瞬間，疊窗防護（SM-5 no-op）與切除序直接決定有無裸露窗。
- **critical path 觸及**：silent-corruption——切除順序錯誤（先刪 legacy 後裝 plugin）＝無閘窗。
- **驗證對齊**：cutover 步驟序測試（安裝→marker→live 驗證→刪 shim 的順序由本段清單釘死）；live receipt 證據＝gate ③ 同形。

### 核心實作要點

1. **可逆 handoff 步驟序**（順序即防護；每步有 live 證據才進下一步）：
   ① plugin install（user-scope）→ approve → **plugin-owned live fire 驗證於 probe repo**（此時 ai-rules 尚無 marker，plugin 對 ai-rules no-op-eligible、legacy 全權——閘不斷）。
   ② ai-rules commit marker（`.agents/memory-governance.json`，`protocol:1`）→ **legacy-owner 路徑 live 驗證**（`.muse/hooks.json` 仍註冊 wrapper；wrapper registered-origin 照 divert——驗證的是 legacy 腿接棒新腳本）。
   ③ 備份並移除 machine-local `.muse/hooks.json` → **立即 plugin-owned live 驗證於 ai-rules**（marker 在＋無 legacy——plugin 首次真正 owning；muse live session 導流 receipt 成立才續行）。**失敗 → 立即 restore hooks.json（可逆恢復點）＋記錄＋進 fallback 評估**。誠實宣稱邊界：③ 的驗證 probe 前瞬間存在有界假設窗（plugin 若壞＝裸露）——不宣稱「已證 zero-window」，宣稱「verify-restore 迴圈收斂」。
   ④ 退役：刪 `hooks/setup-muse-hooks.sh`＋`hooks/muse_memory_inbox.sh` launcher＋legacy 測試（併入 plugin 測試）。
   ⑤ `hooks/verify-memory-topology.sh` 改造：51-57 hooks.json 存在性檢查 → plugin approve/health 檢查（欄位依 S3 實證）；60-67 smoke 往返改指 plugin 腳本 → 跑綠。
2. **marker 進版控**（ai-rules 是 source home——marker 屬 repo 治理宣告，非 machine-local；`.gitignore:59-64` 未涵蓋該路徑，已核）。
3. **跨 WT 語義記載**：worktree 只見所屬 branch checkout 的 marker（未 commit marker 的 WT＝ungoverned）——顯式語義非 cwd 偶然（決策⑧ worktree 條）。

### Pseudo Code

```
install --scope user → approve → live(probe-repo)✓
git add .agents/memory-governance.json → live(ai-rules)✓
rm .muse/hooks.json; retire setup-muse-hooks.sh + wrapper + legacy tests
patch verify-memory-topology.sh --smoke → run → green
```

### 驗證策略

- live 導流證據（direct 或 bridge 形態，與 S2 同法）＋inbox receipt 檔。
- `uv run pytest tests/` 全綠（legacy 測試退役後 baseline 更新）；`verify-memory-topology.sh --smoke` 綠。
- 已知未覆蓋：mosaic cutover（他側）。

---

## S5：控制面同步＋cleanup＋收尾

### Context

- **背景**：docs 同步是 ai-rules 弧的交付本體（文件即產品）；probe scratch 與 POC 檔的清除時點在本段（must-execute-before-complete：POC 到所屬 EP 段落 build＋commit 為止）。
- **UC 引用**：完成「user-scope plugin 化」的規範層記載。
- **依賴關係**：消費 S4 事實基準（安裝/approve/marker/退役語義）。
- **語義約束**：與全域部署紀律一致（`rules/AGENTS.md`——本弧不動 rules/；AGENTS.md 段落更新屬專案檔）。
- **基礎設施盤點**：`AGENTS.md:108`、`skills/memory-audit/SKILL.md:78`、`hooks/AGENTS.md:37`、`hooks/MULTI-MACHINE.md:23,28`、`skills/CLAUDE.md`（工作流索引——memory-audit description 是否需動，rg 確認）。
- **依賴錨點**：全部為文檔行號錨點（段落 0 已列，rg 驗證後改）。
- **成功標準**：rg 殘留掃描（`setup-muse-hooks|\.muse/hooks\.json` 於活文檔零殘留——歸檔區/reports 不動）；`/consistency` 綠。

### 1b. Invariant Impact

- 無（文檔段；行為面已由 S1-S4 釘住）。

### 核心實作要點

1. `AGENTS.md` Muse memory 段改寫：user-scope plugin＋marker 三態＋legacy 退役＋跨 WT marker 語義。
2. `memory-audit` skill「Inbox 消費」節承載形態句置換（機制句、消費站契約零改）。
3. `hooks/AGENTS.md`＋`MULTI-MACHINE.md`：setup-muse-hooks 條目退役、plugin 安裝/approve/health-check 條目補。
4. **blueprint 三檔＋.gitignore**（段落 0 已列錨點）：`onboarding.md:182,187,190,263,287`（setup 教學句＋指向 setup 腳本的相對連結——刪檔即斷鏈，須一併改）、`workflow.md:166`、`blueprint/index.html:409`、`.gitignore:66-67`（註釋＋`.muse/hooks.json` 條目處置——plugin 形態下該 machine-local 檔已不存在，條目留刪由 build 判）。
5. Cleanup：delegate-bridge `.agent-tmp/muse-plugin-probe/`（跨 repo 刪除由主 session 執行——FINDINGS 紀律）；任務家 `poc/` 依 must-execute 規則處置（行為固化進測試後刪，量測文件保留則結案註記）。
6. 收尾三件＋`/audit-test`＋`/consistency`＋AIR-79 結案兩步＋弧結案蒸餾（預期「無相關 memory 條目」明示）。
7. **殘留掃描 gate 措辭**：`setup-muse-hooks|\.muse/hooks\.json` 於**活操作文檔**（AGENTS.md/hooks/skills/blueprint/.gitignore）零殘留——**scoped 查詢**，排除 `ref-docs/`（vendor 鏡像：對 `.muse/hooks.json` 的能力描述是外部事實，不得刪）、`ai-analysis/reports/`、`_tasks/_archived/`、`backlog/`（歸檔/歷史面）。禁用全 repo 零命中當 gate。

### Pseudo Code（修改要點）

```
AGENTS.md:108 段重寫; memory-audit:78 承載句置換
hooks/AGENTS.md + MULTI-MACHINE.md 條目置換; blueprint 三檔＋.gitignore（段落 0 錨點）
rg 殘留掃描（scoped，排除 ref-docs/reports/done/backlog）→ 活面 0; /consistency; /audit-test; kanban 結案兩步
```

### 驗證策略

- 文檔驗證：rg 殘留、跨檔一致性、`/consistency`；導航有效性（AGENTS.md 段↔skill↔plugin README 互指）。
- 已知未覆蓋：無。

---

## 整合策略

### Cutover gates（全綠才切 S4；任一紅→fallback 判定）

| Gate | 內容 | 證據來源 |
|---|---|---|
| ① | explicit versioned marker 落地（`.agents/memory-governance.json`＋`protocol:1`） | S1+S4 |
| ② | legacy 共存 no-op 實證 | S1 單元✓＋offline harness 對照✓（poc O4：working owner→no-op／malformed→不讓位）；live 腿 parked |
| ③ | direct＋bridge headless 雙 live activation（untrusted suppress 形態一併記錄） | S2——**parked**（muse 額度 429，2026-09-14T00:00Z 重置；offline harness 腿已綠＝poc O2/O3） |
| ④ | per-tool-call spawn overhead 在 budget 內 | script 軸✓（early-exit ≈7ms、divert ≈50ms，20-run）；runtime 軸 parked |
| ⑤ | upgrade re-approval 語義確定（fire 續存或 health check 攔截） | 靜態半✓（poc O7：list 不暴露 approve 欄位→欄位式健檢死路；update 後 review 警告復現）；live 腿 parked |

> **Park 狀態（09-12）**：live 腿 L1-L6 全部停在 muse 額度窗口（恢復程序見 `poc/poc_activation.md`）；S4 cutover 需 gate ③⑤ live 證據——弧停在 S2/S3 live 段，S1 已結算（03376b5）。
> **終態（09-12 結案）**：user 裁定「muse 沒有測試沒關係」——live 腿 L1-L6 豁免、gate ③⑤ 以 offline harness 證據收斂；S4 以 **S4-lite** 形態交付（install＋approve 常駐、marker 進版控、雙路 offline 驗證；3df3386），legacy `.muse/hooks.json` 保留為過渡註冊——** deferred 步**：額度重置後跑 `poc/poc_activation.md` 恢復程序（live 驗證）→ 移除 `.muse/hooks.json`＋退役 `hooks/muse_memory_inbox.sh` launcher＋`setup-muse-hooks.sh`＋`verify-memory-topology.sh` 51-57/60-67 段最終 patch。S5 控制面同步完成（活面殘留掃描綠）。

### Fallback 判定點與形態（決策⑨——細節現在凍結，不留「fallback 時定案」）

- **觸發**：gate ③ 失敗（plugin 不 fire live/bridge）或 gate ④ 超 budget 且收斂手段無效。
- **形態（凍結）**：薄 per-repo registration＋單一共享 hook artifact：
  - **共享 artifact 固定安裝點**：`~/.local/share/muse-memory-governance/`（stable 路徑，不受 plugin cache content-sha 漂移影響）；**atomic update**＝新版目錄寫入後 `current` symlink 以 tmp+rename 原子換指。
  - **per-repo registration＝thin launcher**（與 S1 legacy wrapper 同一機制）：`<repo>/.muse/hooks.json`（或 muse 未來 registration 形態）指向 repo 內 launcher，launcher 設 `GOVERNANCE_ORIGIN=registered GOVERNANCE_REPO=<絕對路徑>` exec 共享腳本——**repo root 顯式傳遞，不依賴 stdin workspace 欄位或 $PWD 偶然**（若 gate ③ 根因正是 stdin 缺席＋$PWD 不可靠，此機制直接修掉根因）；registered origin 跳過 ②④（自我註冊不自我 no-op）。
  - **drift 面**＝「N 份薄接線」（launcher 生成腳本統一產出）。
- **保留面**：S1 腳本/測試、marker 三態、S2/S3 證據全保留；置換僅承載層（S4 步驟序改為 per-repo registration 生成）。
- **決策記錄**：fallback 觸發時回寫 AIR-79 卡 notes（形態+理由+觸發 gate）。

### 整合順序與 commit 邊界

S1（code＋tests，一 commit）→ S2（probe 證據，一 commit）→ S3（量測＋可選 health check，一 commit）→ gate 判定 → S4（cutover，一 commit）→ S5（docs＋cleanup，一 commit）→ post-build 鏈（code-review→judge→consistency→metadata-sync）→ 結案。每段 commit 帶 `AIR-79` scope。

## 收尾步驟

1. Capabilities/規範面：`AGENTS.md` 專案結構新增/更新能力行（`muse memory 寫入閘（user-scope plugin）| muse-plugins/memory-governance/＋install/approve | ✅`）；`skills/CLAUDE.md` 工作流索引 rg 確認（memory-audit description 預期零改）；Scenario Matrix 消費場景提煉入卡 notes。
2. Kanban：AIR-79 結案兩步（Done＋final summary＋ref 更新）＋弧結案蒸餾（同主題 memory 條目——預期無，明示）。
3. instruction 檔更新：S5 清單全項＋instruction-writing 品質標準。
4. `/audit-test`（新增測試品質稽核）＋`/consistency`。
5. POC/scratch 清理：任務家 `poc/`、delegate-bridge probe scratch、machine 狀態（`muse plugins list` 僅留正式 plugin）。

## EP Review Findings

> **code review 追加輪（09-12，implement 後）**：雙腿 codex（job-mtxsd4ap-3arlpw）＋GLM-5.3-Flash code-reviewer——2🔴＋4🟡＋4ℹ️ 全採納並已修正（deny 控制字元完備 escape／matcher word-boundary／git 故障分流／cd-cat 防護／stdin seam git-root 對帳／解析序 env→repo-local→固定點／protocol 契約鬆綁為 JSON number 1／補 12 測試）；帳本＝`.review/air-79.md`；343 passed。live 腿 parked 不變。

> 雙審（user 指定鏈）：C 腿＝codex chatgpt-web/high（bridge job-mtxq1dxw-zxv0we，7🔴＋3🟡＋1ℹ️，判定「需修正後重新審查」）；M 腿原排 muse-spark-1.3 因額度 429（窗口 09-14 重置，job-mtxq1dvu failed-usage）改由 user 指定 GLM-5.3-Flash——registry code-reviewer（1🔴＋6🟡＋3ℹ️，判定「有條件執行」）。Judge（主 session GLM-5.3）：**全數採納**——legacy no-op 自我抵消由兩腿獨立命中（cross-family blind spot 校驗有效）。legacy no-op 根因、activation invariant、bootstrap failure taxonomy、可逆 handoff、fallback 凍結、控制面盤點修正已分別回寫對應段落（狀態 implemented）；正向確認項記錄不動。

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| C1+F1 | 🔴 | S1④/S1要點3/S4/整合策略 | legacy no-op 自我偵測迴圈：wrapper 化後 plugin 見自家 matcher 即 no-op——兩腿皆不攔；遷移窗（S1→S4 marker）閘靜默消失；S4 導流驗證與 SM-5 互斥；fallback 共享腳本 DoA | origin-mode（`GOVERNANCE_ORIGIN=registered` 跳過 ②④）＋structured owner 判準＋command realpath self-exclusion；同 repo 雙 origin 對照測試 | implemented |
| C2 | 🔴 | §1b/S3/SM | fail-closed 宣稱過寬：marker 只在 hook 已執行後生效；activation 缺口（未 approve/disabled）muse 本身 fail-open；`trust` ≠ per-capability approve | invariant 拆兩層（activation/liveness vs in-hook）；P-UPGRADE 實證 machine-readable approval 欄位，無則 live-fire probe 作健檢；SM 補「marker valid＋plugin unapproved」列（SM-14） | implemented |
| C3+F7 | 🔴 | S1⑦ | jq 缺失時 deny JSON 也生不出（deny 靠 jq 不自洽）；「確定非 governed」與「依賴故障無法判定」未分流；git binary 缺失與 not-a-repo 混流 | deny 發射一律 jq-free printf 模板；bootstrap failure taxonomy 四分流；git 缺失/not-a-repo 分開釘測 | implemented |
| C4 | 🔴 | S1④/SM-5 | legacy no-op 字面掃描過寬：stale/malformed/他腳本註冊都會錯誤 surrender → 裸露 | structured「可工作 legacy owner」判準（parse＋matcher 語義＋executable＋realpath≠self）＋negative tests（stale/invalid JSON/wrong command/partial matcher） | implemented（併 C1 機制） |
| C5 | 🔴 | S4 | cutover 序未證 plugin 接棒：刪 hooks.json 前驗的是 legacy 腿；smoke 是 bash 直呼不證 runtime 載入 | 可逆 handoff：legacy restorable→停用 legacy→立即 plugin-owned live probe→成功才退役；失敗 restore；不宣稱 zero-window，宣稱 verify-restore 收斂 | implemented |
| C6 | 🔴 | S2 P-ACT-B/fallback | bridge probe workspace identity 未釘死（child cwd＝git root，nested marker 不算 workspace）；fallback 細節留「fallback 時定案」違 EP 自足 | P-ACT-B 釘 positive lane（dedicated workspace 或 temp marker＋receipt cleanup＋pool 對帳）；fallback 現在凍結：固定安裝點＋atomic symlink 換指＋launcher 顯式傳 `GOVERNANCE_REPO` | implemented |
| C7+F3 | 🔴 | 段落0/S5 | 控制面盤點不實（初掃 head 截斷）：漏 blueprint 三檔（onboarding/workflow/index.html）＋.gitignore:66-67＋verify-topology:51-57；全 repo 零殘留 gate 會誤刪 ref-docs vendor 事實 | 集合修正＋scoped 殘留 gate（排除 ref-docs/reports/done/backlog，理由明示） | implemented |
| F2 | 🟡 | S4/基礎設施表 | verify-memory-topology.sh:51-57 hooks.json 存在性檢查——cutover 後必紅且指向已刪腳本 | S4 步驟⑤補 51-57 段處置（改 plugin approve 健檢） | implemented |
| C8 | 🟡 | S1 語義約束 | 「位元組級相容」過度宣稱——consumer 是 schema/語義相容，byte parity 非 invariant | 改 wire/schema 語義相容（欄位語義）；不加 differential oracle | implemented |
| C9 | 🟡 | S1↔S2 | 反向依賴：P-WS 凍結欄位要回改 S1 resolver 常數，S1 卻宣稱封閉 | resolver 定為 provisional seam；S2 回寫後重跑完整 S1 acceptance，code change 計入 S2 | implemented |
| C10 | 🟡 | SM-3/S1 測試 | marker invalid 域列舉不足（只列 parse fail/缺欄/>1，漏型別混淆） | 值域矩陣：integer 1 唯一 valid——`0`/`-1`/`"1"`/`null`/`true`/`false` 全 deny | implemented |
| F4 | 🟡 | 段落0 基礎設施表 | p2/ dangling 錨點（宣稱不依賴 scratch 又回指；S5 要刪它） | manifest 欄位內聯 S1 要點；p2 列改「已吸收」 | implemented |
| F5 | 🟡 | S1 要點3 | wrapper 寫死 cache 路徑＝content-sha 漂移斷鏈→exec 失敗 fail-open | 固定安裝點 symlink 解析＋解析失敗 wrapper 自行 printf deny（fail-closed 到 launcher 層） | implemented |
| F6 | 🟡 | S2 P-ACT-B/1b | probe receipt 污染 ai-rules 真 inbox（夜波可能收走）；teardown 漏清；與 S2 1b 宣稱不一致 | P-ACT-B 優先 dedicated workspace；temp marker 形 teardown 增清 receipt＋`git -C <池> status` 對帳 | implemented |
| F8 | ℹ️ | S1 要點3 | 「repo 解析恰同」未證宣稱（muse hook cwd 未 probe） | wrapper 顯式傳 `GOVERNANCE_REPO`，不依賴推測 | implemented |
| F9 | ℹ️ | SM/S1 測試 | 空 stdin／非 JSON 行為未入矩陣；inbox ENOENT 段語義未寫明 | SM-13＋ENOENT＝safe（S1⑤、測試清單） | implemented |
| C11 | ℹ️ | S4 | marker 進版控可行性正向確認（.gitignore 未涵蓋） | 無動作 | no-action |
| F10 | ℹ️ | F2 全域 | 合規正向確認：無版本號/日期/統計引入；錨點全核；baseline 一致；skills/CLAUDE.md 零改成立 | 無動作 | no-action |


