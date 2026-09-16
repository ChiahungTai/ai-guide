# EP：落地手術批 L1-L9——治理設計執行

> **ep_type**: implementation（**docs mode**——全變更為 `.md`＋兩條 CronUpdate prompt＋一條 memory 條目）
> **backlog**: AIR-18（追蹤卡；desc 過 gate 三必有）
> **baseline**: `e45de1f`（2026-09-03）
> **規格唯一源**：[`done/09-03-backlog-governance-design/design.md` §6 落地清單](../done/09-03-backlog-governance-design/design.md)——本 EP 只做「規格→檔案」錨定與分批，**不重新設計**（AIR-14 已定案：承諾時判定／出口兩腿／handoff --save 退場改 --comment／.review solo 可退場）
> **審查策略**：規格已在 AIR-14 弧雙重審過（EP review 8 findings＋post-build consistency＋GLM 接管驗收）；錨點由主 session rg 逐一驗證在場——build 後由 post-build 鏈＋GLM 驗收閉環，不重跑前置 EP review

## 實作總覽

**目標**：design §6 的 L1-L9 全批落地——5 個 skill 手術＋1 個 rule 手術（含全域部署）＋2 條 cron prompt 更新＋1 條 memory 壓指針＋sync-sources 全域掃描。

**已決策（勿重辯）**：①規格逐行照 design §6，語義不改 ②L5 掛 23:40 cron 與 AIR-17 首跑共存（AIR-17 判準＝記憶腿產物，不受新腿影響；新腿明晚起自有產物驗證）③L4 動 rule 後必跑 `deploy_agents.py`＋三部署檔 cmp＋bundle gate 檢查 ④同根因同 commit（一批一 commit）。

## UC 盤點（docs mode：受影響文檔清單）

- **Backlog 關聯**：AIR-18 追蹤卡（已建、已 In Progress）；無其他卡
- **受影響文檔**：`skills/kanban-board|handoff|execution-plan|at|post-build/SKILL.md`、`skills/self-contained-prompt/SKILL.md`（sync-sources 連帶）、`rules/collaboration-constraints.md`（→觸發全域部署）、三部署檔 `~/.zcode/AGENTS.md`×3（deploy 產物）、兩條 automation prompt（CronUpdate）、memory `reference_periodic-task-landscape.md`
- SYSTEM-MAP：無

## Scenario Matrix（文檔語境）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 段 |
|---|------|------|---------|------------|----|
| SM-1 | session 讀 kanban-board 開工 | L1 後 | 開工段＝起手式五步（含讀卡知形態）；建卡段含 desc gate；「卡即 handoff」小節在場 | design §6 L1 驗證命令 | S1 |
| SM-2 | handoff --save 消費者 | L2 後 | `--save` 語義改 `backlog --comment` 掛卡；`.at-contexts/handoff` 引用歸零 | `rg -c "at-contexts/handoff" skills/handoff/SKILL.md`=0 | S1 |
| SM-3 | EP review F-1 型校準 | L3 後 | 建卡步驟含 desc gate；Apply Changes 段含 F-1 desc 同步義務 | `rg "desc gate|同步" skills/execution-plan/SKILL.md` | S1 |
| SM-4 | at 排程 resume | L6 後 | `.at-contexts` 段注記只剩 `at-context-*`；夜掃兜底在場 | `rg "at-context-\*" skills/at/SKILL.md` | S1 |
| SM-5 | post-build 收尾 | L9 後 | 階段 5 含 `.agent-tmp` 預設清（列清單→LLM 判→刪＋報） | `rg "agent-tmp" skills/post-build/SKILL.md` | S1 |
| SM-6 | 全域 bundle 消費端 | L4 後 | rule 補出口兩腿＋三區時限＋新區門檻；deploy 三檔 cmp 一致；gate 未爆 | `wc -c`＋`cmp`×2＋deploy 輸出 | S2 |
| SM-7 | 今晚 23:40 cron | L5 後 | prompt 含三區 mtime 掃＋報告明細＋刪 | `CronList` prompt 含 `mtime` 掃段 | S3 |
| SM-8 | 週日治理 cron | L8 後 | prompt 含 registry 比對腿 | `CronList` prompt 含 `schedule-registry` | S3 |
| SM-9 | session 查排程總覽 | L7 後 | memory 條目壓為指針（指 schedule-registry.md） | `rg "schedule-registry" <池>/reference_periodic-task-landscape.md` | S4 |
| SM-10 | 術語/引用漂移 | sync-sources | `handoff --save`/`.at-contexts/handoff` 殘留引用清零（含 self-contained-prompt:71） | `rg "handoff.*--save|at-contexts/handoff" skills/ rules/` 逐判 | S4 |

## 段落劃分

S1（skills 五檔手術，可平行編輯）→ S2（rule＋部署，S1 完成後跑避免與 S1 的 skills 編輯交錯）→ S3（cron 兩條）→ S4（memory＋全域掃描＋收尾）。S1-S3 無相互依賴，S4 收尾依賴全部。

---

## S1：skills 手術（L1/L2/L3/L6/L9）

**Context**：規格＝design §6 對應行；錨點已驗證。目標檔皆已由主 session 本輪讀過結構，muse 動手前仍須逐檔 Read。

**修改要點**：

1. **L1 [kanban-board/SKILL.md](../../../skills/kanban-board/SKILL.md)**——「開工」段（:32）改寫為起手式五步：①`task edit -s "In Progress"`（第一動）②讀卡三層（frontmatter→desc→notes→references）③**讀卡知形態**（references 有無 EP——承諾時已定，不重判；scope 遠超 desc→先升 EP）④新鮮度核對（desc baseline vs `git log <baseline>..HEAD`；notes relay 宣稱機械驗證）⑤開工雙 ref；「建卡」段補 desc gate 三必有（baseline／已決策勿重辯／驗收；適用＝跨 session To Do 卡，session 內即辦豁免；rg 軟自查）；新增「卡即 handoff」小節（三層分工 desc=決策層/EP=規劃層/notes=留言層＋兩層判定承諾時定形態＋desc 同步義務一句，引 execution-plan 規模分級不新造）
2. **L2 [handoff/SKILL.md](../../../skills/handoff/SKILL.md)**——:69 產出段與 :79 參數表的 `--save` 語義改：交接內容 `backlog task edit <id> --comment` 掛卡 `comments` 段（隨卡歸檔；board 可見）；**不寫 `.at-contexts/handoff-*.md`**（SM-12 退場）
3. **L3 [execution-plan/SKILL.md](../../../skills/execution-plan/SKILL.md)**——UC 盤點建卡步驟 3（:86）補：`-d` desc 過 gate 三必有（蒸餾自 EP 總覽）；「主 LLM — Apply Changes」段（:348）補：findings 含 F-1 型（scope/驗收校準）→ 同步回寫追蹤卡 desc（決策層變更才同步）
4. **L6 [at/SKILL.md](../../../skills/at/SKILL.md)**——:67 附近 `.at-contexts` 段注記：本區只剩 `at-context-*`（`handoff --save` 已退場改 `--comment`）；既有 resume 後刪維持；夜間掃 7 天兜底
5. **L9 [post-build/SKILL.md](../../../skills/post-build/SKILL.md)**——階段 5（:61）段首補前置清理：列 `.agent-tmp/` 清單→LLM 判「後續還用嗎」→用則保留、不用當場刪＋清單入收尾報告（第一腿；夜掃兜底）

**驗證策略**：design §6 L1/L2/L3/L6/L9 驗證命令逐行＋`rg "handoff.*--save|at-contexts/handoff" skills/` 僅剩 at skill 的「已退場」注記形態。

---

## S2：rule 手術＋全域部署（L4）

**Context**：[collaboration-constraints.md](../../../rules/collaboration-constraints.md)「Agent 檔案寫入紀律」段（:86）——bundle 預算緊（總量已 ~90% gate），**新增控制在 ~500B 內**。

**修改要點**：「暫時產物」條後補三行——①出口兩腿：post-build 收尾預設清（列清單→LLM 判→刪＋報）＋夜間掃兜底（`.agent-tmp`/`.at-contexts` mtime>7d、`.review`>30d——時限是緩衝非保存承諾）②`.at-contexts` 只收 `at-context-*`（handoff 交接走 backlog `--comment`）③新 dot-area 門檻四條（語義最近區→四問有答→規則承載→掃腿覆蓋）。

**驗證策略**：`uv run python scripts/deploy_agents.py` → 三部署檔 `cmp` 兩兩一致＋`wc -c` 對 gate（動態讀 `BUNDLE_MAX_BYTES`）未爆；`rg` 確認部署檔含新段。

---

## S3：cron 兩條（L5/L8）

**Context**：CronUpdate 全文替換 prompt——須以當下 CronList 現值為基礎追加（不重寫既有內容）。

**修改要點**：
1. **L5 `automation-751ecce2`（23:40）**：既有記憶收斂步驟逐字不動，末尾追加「檔案型清淤兜底腿」段——掃 `/Users/ctai/Github/ai-rules` 三區：`.agent-tmp/` 與 `.at-contexts/` 檔案 `mtime>7d`、`.review/` 檔案 `mtime>30d`（`find <區> -type f -mtime +N`）；清單全列進報告後刪除（報告＝可復原判斷的證據）；報告加「檔案型清淤：刪 N 檔」行；不碰其他 dot-area
2. **L8 `automation-fed036ff`（週日 23:00）**：追加段 3——`CronList` 各 automationId 對 `ai-analysis/schedule-registry.md` 逐字比對（`rg automationId` 抽兩側），drift 列報告（advisory 不動手）

**驗證策略**：CronList 讀回 prompt 含新段原文；既有段逐字未變（與更新前 CronList 值 diff）。

---

## S4：memory 壓指針（L7）＋sync-sources 全域掃描＋收尾

1. **L7**：memory 池 `<池>/reference_periodic-task-landscape.md`——現值清單段壓為指針（「ai-rules 排程現值→`ai-analysis/schedule-registry.md`；mosaic 側 plist 清單→`ls ~/Library/LaunchAgents/`」），保留歷史趨勢語義；desc ≤100 chars
2. **sync-sources 三類掃描**：①互引（`rg "kanban-board" skills/`、`rg "collaboration-constraints" rules/ skills/`——引用面與新段一致）②部署（S2 cmp 證據）③術語（`rg "起手式|desc gate|讀卡知形態" skills/` 定義源唯一——kanban-board 為源、execution-plan 引用不重複定義）
3. **收尾**：AIR-18 結案兩步（`-s Done --final-summary` → `--ref` done/ 新 URL）＋任務家遷 `done/`；基礎款殼（本批為手術執行弧，殼可指回 design 殼＋一行結案摘要——由 muse 判斷，最小形態即可）

**驗證策略**：SM-9/SM-10 checkpoint＋design §6 全部驗證命令彙總表（逐行 pass/fail）。

---

## 整合策略

- 全部 working tree，同根因同 commit（L1-L9 一批一 commit；deploy 產生的部署檔變更不入 git——它們在 repo 外）
- 不碰：mosaic 側任何檔案、AIR-17 卡、memory 池其他條目

## 收尾步驟（implement 階段 5）

- AIR-18 結案兩步＋任務家遷 `done/`（URL 形態 `http://127.0.0.1:6421/ai-rules/_tasks/_archived/<task>/`）
- `skills/CLAUDE.md` 工作流索引：本批改 skills 行為不改命令入口——description 檢查一遍，不需動則記「查過無需動」
- post-build 收尾鏈（docs 鏈 consistency＋metadata-sync）＋GLM 驗收
