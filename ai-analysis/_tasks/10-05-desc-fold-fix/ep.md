# EP——desc 摺疊續行修法：hook/generator 計數三口徑收斂（AIR-250）

> **ep_type**: implementation
> card: AIR-250（In Progress）；design discussion evidence＝codex job-muufhibk＋GLM-5.3 job-muufhiqw（converged，RECOMMEND A+B）
> author_family: glm（author＝本 session GLM-5.3-Flash；implement 預定 impl-lite＝同 family——same-family precondition 見測試規劃段）
> baseline: 17507fed

## EP Review Cycle 帳本（boundary：fresh＋intent 分離）

| # | source | finding | 裁決 | 落點 |
|---|---|---|---|---|
| F1 | fresh (M)＋intent (M) | TC-A2「物理形 vs 值等比」歧義 | ✅ 採納值等比（鏡像 :286）——摺疊-in-place 同值重寫記 A 風格面已知殘餘 | TC-A2 oracle 已改述 |
| F2 | fresh (M) | matrix 同步清單漏 :344 空值續行行 | ✅ 採納 | S2 已補 |
| F3 | fresh (L) | memory_telemetry 鏡像 hash 漂移訊號未註記 | ✅ 採納 | 段落 0 已補 |
| F4 | fresh (L) | marker strip 輸入未 strip（`>- ` 尾隨空白） | ✅ 採納 | S1 要點已補 |
| F5 | fresh (L)＋intent (M-同源) | `>-` 無續行→errs 無 TC；空值形未入凍結表 | ✅ 採納 | TC-B1/B2 已補 Given |
| F6 | fresh (L)＋intent (L) | TC-A1 只凍結 Write；litelite 錯字 | ✅ 採納 | TC-A1 參數化 Write/Edit；錯字改 lite |
| F7 | fresh (L)＋intent (L) | S4 錨點偏移（:212-218）＋SKILL:36/:40 自洽未列 | ✅ 採納 | S4 已改寫 |
| F8 | intent (L) | 卡 plan 漏「只掃尾否決」已決策項 | ✅ 採納 | 卡 plan 補一行（隨 apply commit） |
| F9 | intent 建議 | fresh 腿明寫 blind diff review＋回執記 impl job id | ✅ 採納 | 回執預填已載 |

fresh VERDICT: needs-attention（F1/F2 文字級——已回寫）；intent VERDICT: aligned。**帳本全 terminal（implemented/rejected 無 open）→ EP accepted**。

## 實作總覽

frontmatter `description` 摺疊續行（縮排第二行）時，hook 寫入閘與 generator 投影**只讀首行**（兩者行式解析刻意對齊——對齊了一個錯誤語義），真值只有夜波 ad-hoc regex 可見：100-char 閘被繞過、投影丟續行、積壓到夜波才發現（9 檔積壓 8-12 夜實證；存量摺疊 37 檔在場——codex 枚舉、coordinator 掃描器 `---` break bug 修正後確認）。

修法 A+B（雙腿設計討論收斂）：
- **B（主修・讀端正確化）**：generator `parse_frontmatter` 與 hook `extract_desc` 的 **description scalar collector** 正確摺疊——plain 續行 join 空格、`>`/`>-`/`>+` block marker 清空後接內容、接縫空格硬規則；**禁泛化**（其他 key 續行維持丟棄——metadata.type 巢狀靠 parent 分支，泛化＝回歸）
- **A（輔・寫入端單行不變式）**：hook block「新增/改 desc 成多行」；**存量不溯及**（body-only Edit 且 desc 未變→放行，鏡像 :286 `desc == previous_desc → skip` 既有模式）
- **配套**：memory-audit SKILL desc 文法段加「desc 必須單行」＋夜波計數單一源行（import 池內 parse_frontmatter、先驗副本新鮮度、禁 ad-hoc regex 限長度計數）

## UC 盤點

### Backlog 關聯
- AIR-250（本 EP 追蹤卡）；`backlog search desc 摺疊` 零命中其他卡——無重複承諾
- 本 EP 不新增 product UC（治理基建修復）；受影響能力＝memory 治理面的 desc 寫入閘與索引投影

### SYSTEM-MAP 影響
- 元專案無 SYSTEM-MAP.md——跳過（正當跳過，標記理由）

### 掃描範圍
- `skills/memory-audit/SKILL.md`（desc 文法五條段＋夜波收斂 desc 掃尾段）
- `hooks/block-memory-index-write.py`、`skills/memory-audit/scripts/generate_index.py`（源碼錨點見段落 0）
- backlog 卡：AIR-250；tests：test_memory_lifecycle.py／test_block_memory_hook_suffix.py

### 同主題 memory 條目（結案蒸餾範圍）
- `reference_generate-index-cwd-write-trap`（generator 同域——本弧結案時併入本修法事實一行）
- `reference_bridge-glm-family-facts` 的 tool-surface 段（派發 cwd 教訓——非本弧範圍，不動）

### 既有 UC 狀態／新增 UC
- 無 UC 變更（基建修復）；夜波 desc 掃尾行為由「ad-hoc regex」改「單一源 parser」＝行為等價替換

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 單行 desc 正常寫入 | 主 session Write/Edit ≤100 單行 | 閘過、投影原樣 | pytest | — |
| SM-2 | 新寫入 plain 摺疊 desc | description 行後接縮排續行 | **A block**（單行不變式訊息） | hook exit 2＋訊息錨 | — |
| SM-3 | 新寫入 `>-` block desc | `description: >-` | **A block**（block marker 判 multiline） | 同上 | — |
| SM-4 | 存量摺疊檔 body-only Edit | desc 物理形未變 | **放行**（存量不溯及） | hook exit 0 | — |
| SM-5 | 存量摺疊檔投影 | regen | 全值投影＋>100 截斷 `…` | pytest parity | — |
| SM-6 | subagent 寫摺疊 desc | 繞 hook 寫入面 | 投影仍正確（B 覆蓋）；夜波掃尾兜底 | pytest | — |
| SM-7 | metadata.type 巢狀 | `metadata:`＋縮排 type/rank | **不回歸**（parent 巢狀保留） | pytest 回歸錨 | — |
| SM-8 | CRLF 檔 | \r\n 行尾 | 兩 parser canonical 相同 | parity | — |
| SM-9 | 重複頂層 description | 兩個 description key | last-wins（兩端一致） | parity | — |
| SM-10 | 摺疊 desc >100 投影 | 全值 >100 | 截斷 99＋`…`（既有語義接手） | pytest | — |

## 測試規劃段（TC 凍結）

oracle_source 權威＝**S**（本 TC 凍結於實作前；語義源＝本 EP＋codex 設計討論矩陣）。evidence class L1（單元）／L4（管線行為）。

| TC | claim | Given-When | oracle（predicate-ID） | oracle_source | uncovered |
|---|---|---|---|---|---|
| TC-B1 | plain 續行摺疊全值抽出 | desc 首行＋縮排續行；另含空值形（`description:` 空值＋縮排） | P1: parse 結果＝兩行 join 單空格；P2: 接縫恰一空格；P3: 空值形抽得續行全值 | 本 EP 語義規格 | 無 |
| TC-B2 | `>-` marker 清空 | `description: >-`＋縮排內容；**另 Given**：`>-` 無續行 | P: 有內容→結果不含 `>-` 前綴；無續行→desc 空＝落 errs（條目不出投影） | codex 指摘（marker 是語法記號）＋索引可見變化（fresh-F5） | `|` literal family（池內無案例，記 uncovered） |
| TC-B3 | metadata 巢狀不回歸 | `metadata:`＋縮排 type/rank | P: `metadata.type`＝project、rank 解析同現值 | 現行行為（HEAD 測試） | 無 |
| TC-B4 | duplicate last-wins | 兩個頂層 description | P: 取後者（兩端一致） | 現行行為 | 無 |
| TC-B5 | CRLF parity | \r\n 檔 | P: canonical desc 與 LF 版相同 | 正規化語義 | 無 |
| TC-B6 | 投影截斷接手 | 摺疊全值 >100 | P: 投影 99＋`…`（canonical＝兩端各過 `" ".join(split())` 後比較） | 既有 TRUNCATE_DESC 語義 | 無 |
| TC-B7 | hook 量到真值 | 摺疊全值 >100 經 hook | P: DESC_LIMIT 觸發 block | 既有 DESC_LIMIT 語義 | 無 |
| TC-A1 | A block 新增/改為多行 desc | 參數化 tool＝Write（新檔）與 Edit（單行改摺疊，candidate≠previous）；形＝plain／`>-` | P: exit 2＋訊息含單行不變式措辭 | A 規格 | 無 |
| TC-A2 | A 存量放行 | 既有摺疊檔 body-only Edit（**canonical desc 值相等**——鏡像 :286 `desc == previous_desc`） | P: exit 0；已知殘餘＝同值摺疊-in-place 重寫亦放行（A 風格面，B 仍擋 >100） | 存量不溯及決策（值等比，非物理形） | 無 |
| TC-A3 | metadata.description 不誤中 | 縮排 `description:` 於 metadata 區 | P: A/B 皆不視為頂層 desc | 頂層錨定語義 | 無 |

**same-family precondition**：author glm＋impl litelite glm——**same-family**。degraded 明示：設計段已有跨家族 critique（codex chatgpt-web 腿，blind read 源碼後指摘）＋TC 由 codex 矩陣擴充；RED 前不另做 pre-RED challenge（非 silent-corruption path）。實作後 fresh review 腿（同 family——degraded 一併記錄於回執）。

## 段落 0：全域研究（證據——已完成，摘要引用）

- **源碼錨點**：generator `parse_frontmatter` `skills/memory-audit/scripts/generate_index.py:102-121`（縮排行→parent 分支→parent=None 丟棄）；`main` desc 正規化 `:232`（`" ".join(split())`）；hook `extract_desc` `hooks/block-memory-index-write.py:124-149`（docstring :130 刻意對齊）＋:47-48 舊契約「品洞非完整性洞，不修」＋DESC_LIMIT 檢查 :206＋存量 skip 模式 :286-287
- **設計討論雙腿**（cross-family）：codex job-muufhibk（chatgpt-web/high——B 收窄、`>-`、37 存量、test :536/:340 錨、四影響面）＋GLM-5.3 job-muufhiqw（A 增量重定義、parent 保留、接縫空格、配套新鮮度、部署時序）。兩腿 RECOMMEND converged：A+B
- **存量實測**：37 檔摺疊（codex 枚舉；coordinator 首掃 0＝掃描器 `---` break bug，直查 codex 樣本檔證實摺疊在場）
- **negative 宣稱**：「池內無多行值其他 key 案例」——rg 掃描單腿（literal 互補腿：`rg '^\s' <pool>/*.md` frontmatter 區段抽驗）——本宣稱限 desc 修復面，不影響其他 key 行為（B 不改其他 key 路徑）
- **鏡像消費者註記（fresh-F3）**：memory_telemetry.py `_frontmatter_rank`（:569-605）自稱 generator 行為鏡像——B 只改 description 歸宿、rank 路徑不動→行為不受影響；generator 改後 `generator_schema` hash 漂移訊號預期觸發（非缺陷）
- **風險假設**：①`>-`/`|` 混合形態實池分佈未知（低——池現值無 `>-` desc，防禦性支援）②hook 摺疊偵測在 `description:` 空值形（`:~` 空值＋縮排）須涵蓋（glm Q3 指摘——測試錨含）

## 段落 S1——B：generator description scalar collector

**Context**：`parse_frontmatter`（:102-121）現行：頂層 key 帶值→parent=None；縮排行→巢狀分支→parent=None 時丟棄。**只改 description 的歸宿**：帶值頂層 `description:` 後的縮排續行，接回該值（join 單空格）；`>-` marker 值先清空。其他 key 行為不變（parent 巢狀保留——TC-B3）。
**要點**：狀態機加 `last_scalar_key`（僅追蹤 `description`；其他 key 帶值後縮排續行維持丟棄——最小語義面）；`description:` 空值＋縮排＝也可摺疊（涵蓋 glm Q3 空值形）；CRLF 由既有 `replace` 統一（:132 同形）；`main` :232 既有 `" ".join(split())` 不動（正規化單一源）。marker 清空前 `value.strip()`（fresh-F4——`>- ` 尾隨空白形）。
**Pseudo Code**：
```
for line in frontmatter_lines:
    if indented(line):
        if last_scalar_key == "description" and pending_desc is not None:
            clean = strip_block_marker_if_unconsumed(pending_desc)  # ^[>|][+-]?$ → ""
            pending_desc = join_single_space(pending_desc_cleaned, line.strip())
        elif parent:  # 既有巢狀分支（不動）
            ...
        continue
    key, _, value = partition(line)
    if key == "description":
        last_scalar_key = "description"
        pending_desc = value  # block marker 保留至下一續行或收尾時清空
    else:
        last_scalar_key = None  # 其他 key 續行維持丟棄
收尾：description 結果去 block marker（若無續行）＋去引號（既有）
```
**驗證**：TC-B1/B2/B3/B4/B5/B6（test_memory_lifecycle.py 新增摺疊案例群——RED 先行）

## 段落 S2——B：hook extract_desc 對齊＋docstring 同步

**Context**：`extract_desc`（:124-149）與 generator 同語義改造（collector 邏輯鏡像——非 import，兩份實作 cross-layer parity tests 鎖住：TC-B1-B5 每 case 兩端 canonical 相同）。
**要點**：docstring 同步（兩個區塊、三個語義點）——:47-48 舊契約（「品洞非完整性洞，不修」）刪除改載新語義；:125-130「縮排行是巢狀 key」改「description 例外：續行摺疊（2026-10 AIR-250）；其他 key 維持巢狀」；測試 :536（folded hash passthrough 預期）反轉為 block；test_block_memory_hook_suffix.py consumer-selection matrix **兩行同步——:351（`>-` 行）與 :344（空值續行行：selected 由 "" 變全值、expected 0→2）**（fresh-F2）。
**驗證**：TC-B1-B5/B7 parity（canonical 定義＝兩端各過 `" ".join(split())` 後比較）＋反轉測試

## 段落 S3——A：hook 摺疊偵測 block

**Context**：B 落地後既有 DESC_LIMIT 閘量到真值（>100 摺疊自動擋——TC-B7）；A 增量＝**風格單行不變式**：全值 ≤100 的摺疊也擋＋`>-` 形擋＋指向性訊息。
**要點**：偵測＝extract 過程標記「值曾跨行」（plain 續行或 block marker 任一）；**存量不溯及**——Edit 分支鏡像 :286（**canonical desc 值相等**→skip 全部 desc 檢查；已知殘餘＝同值摺疊-in-place 重寫放行，B 仍擋 >100——fresh-F1 擇一寫死）；**新/改 desc 成多行→block**（Write 與 Edit 兩路徑——TC-A1 參數化）；訊息＝「desc 必須單行 ≤100——單行保簡易 parser 可機械解析；摺疊形請攤平重寫（AIR-250）」；`metadata.description` 縮排形不誤中（TC-A3）。
**驗證**：TC-A1/A2/A3（hook 測試檔）

## 段落 S4——配套：memory-audit SKILL 加行

**Context**：指令面單行規則正典化（避免 hook 比規範多隱性 policy——codex 指摘④）。
**要點**：desc 文法五條段（SKILL.md:212-218，按節標題定位）第 5 條擴「**必須單行**——摺疊續行擋寫入閘、投影吃全值（AIR-250）」；夜波收斂 desc 掃尾段（:73 附近）加「計數一律 import **池內副本** `_generate_index.py` 的 parse_frontmatter（先驗副本新鮮度——`_regen-skipped-stale` 在場＝先刷新）；禁 ad-hoc regex 限**長度計數**（摺疊形結構偵測不受限）」；自洽更新兩處——:36 hook 行為清單（僅列 >100 硬擋→補單行不變式）與 :40 索引預算表 desc 預算措辭（intent-F6）。
**驗證**：rg 錨點在場＋skill 自洽（文法五條→六條或第 5 條擴充的編號一致性）

## 段落 S5——收尾

1. 全套 pytest（lifecycle＋hook_suffix＋回歸切片）
2. `/audit-test` 新增測試品質稽核
3. memory-audit SKILL 改動＝instruction 面——已含於 fresh review 腿範圍（boundary profile）
4. 卡 AIR-250：AC 勾稽→結案兩步→弧結案蒸餾（generate-index-cwd-write-trap 併入本修法事實）
5. 回執四欄（見整合策略）

## 整合策略

- **載體**：ephemeral WT（`scripts/wt-open.sh --ephemeral desc-fold-fix --base main`）——控制面路徑，canonical main 禁直 commit
- **author_family: glm**；實作＝impl-lite（glm lite pin，EP 自足接手）；same-family degraded 明示（見測試規劃段）
- **review**：fresh code-reviewer 腿（EP＋diff，boundary 維度：閘語義/回歸面/測試矩陣覆蓋）＋design-phase cross-family 證據（codex 腿）隨回執引用
- **部署時序**（glm 指摘）：hook 治理中央部署即時生效；generator 需池副本刷新（`cp .new && mv` 原子）——收線腿含 ai-guide 池副本同步＋cmp＋`--check`
- baseline: 17507fed
- 回執四欄預填：classification=boundary（hook gate＋投影語義）／review=<fresh 腿＋cross-family codex design job-muufhibk＋glm judge job-muufhiqw>／session-freshness=fresh／deployment-surfaces=<merge 後池副本 sync＋--check 重驗→healthy>

## 收尾步驟

見段落 S5（audit-test／卡結案兩步＋蒸餾／instruction 檔更新已含 S4／EP 歸檔隨弧收線）。
