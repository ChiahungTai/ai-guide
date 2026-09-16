# EP：guides-refactoring——跨卡 decision contract 文檔化＋無主機械批

> **ep_type**: implementation（full-tier standalone EP；本弧含控制面語義＝跨卡 decision contract，屬 boundary 變更——closure 紀律將成後續所有 enforcement 類 AC 的驗收契約）
> **baseline**: `53f6362df2419a4a1a05e647171923add25eb591`（2026-09-16 寫 EP 時 main HEAD）
> **dirty 聲明**：working tree 有兩個未追蹤目錄——`ai-analysis/reports/guides-refactoring/`（本弧前期調查的框架 README 等文檔）與 `ai-analysis/_tasks/0917-guides-refactoring/`（本 EP 自身任務家）；皆屬預期產出、非髒污；除此 working tree clean。
> **docs mode**：product 變更全為 `.md`（rules/skills/report）＋一份 machine-local config（`~/.codex/config.toml`，非 repo 檔）。測試規劃段跳過——無可執行碼面（TC 凍結不適用；驗證全為 rg/機械掃描/啟動 smoke）；docs mode 結構裁剪——全篇研究摘要與整合策略不另立 top-level 段，內容已內嵌各段 Context。

## 實作總覽

guides-refactoring 弧的收斂結構（codex 三層建議，caller 裁決採納）：AIR-100 修 enforcement truth、AIR-113 修 skill ownership，本 EP 只持有**跨卡 coordination contract 文檔化（C 層）＋無主機械批**。三個段落：

- **S0**：closure 三層閘＋防線標記制文檔化——落點 `skills/acceptance-evidence/SKILL.md` 增節（本 EP 核心 boundary 產出）
- **S1**：無主機械批四項——upgrade-nt copy-paste 句、trading-analysis mosaic 殘留、rules 工具分工句 pointer 化、codex config stale hooks 殘留
- **S2**：AIR-100 交接包 `ai-analysis/reports/guides-refactoring/air100-handoff.md`

輸入證據群（已存在，唯讀）：`.agent-tmp/guides-refactoring/{synthesis,codex-opinion,m-a-output,m-d-output}.md`＋框架 `ai-analysis/reports/guides-refactoring/README.md`。

## UC 盤點

### Backlog 關聯

- 本 EP 對應 guides-refactoring 弧（caller 主 session 持有 scope 裁決；本弧 reports 目錄即工作現場）。**不建新卡**：S0/S1/S2 全部 UC 的 owner 即本 EP（經 caller 裁決授權）；與既有卡的邊界見「範圍外對照表」。EP 追蹤卡的建立與否＝caller/user 決策（本 EP 撰寫 session 受硬約束禁 git 寫操作），列 user gate。
- **Override provenance**：S1.1/S1.2 收進本 EP 係 caller 裁決覆蓋 codex 建議的 ownership 歸屬（codex 原議歸 AIR-113；裁決時間 2026-09-16 EP 撰寫 session、依據＝機械批與 fleet disposition 分軌可避免 113 開工阻塞；two sources of truth 風險由範圍外對照表「辨識」行＋S1.1 縮為查證項消除）。
- 相鄰卡（不重疊、僅對照）：AIR-100（memory 池治理 umbrella，To Do）、AIR-113（skills fleet 82 支逐支處置，To Do）、AIR-112（wt-close receipt，已建卡）。

### SYSTEM-MAP 影響

無 SYSTEM-MAP.md（元專案，正當跳過）。

### 掃描範圍

- `skills/acceptance-evidence/SKILL.md`（S0 落點）、`rules/acceptance-evidence.md`（always-on 核心，S0 參照不動）、`skills/memory-audit/SKILL.md`（統一定義表，S0 引用不重抄）
- `skills/upgrade-nt/SKILL.md`、`skills/trading-analysis/SKILL.md`、`rules/tool-discipline.md`、`rules/modern-cli-preference.md`、`rules/symbol-query-routing.md`、`~/.codex/config.toml`（S1 五變更標的＋一權威對照 symbol-query-routing.md——零變更）
- `backlog/tasks/air-100*.md`、`backlog/tasks/air-113*.md`（scope 對照）

### 同主題 memory 條目（結案蒸餾範圍）

- 未掃（本 EP 撰寫 session 受硬約束唯讀；implement 階段 5 收尾時由實作 session 補掃 memory 池——`rg -i "guides-refactoring|closure|coverage matrix" /Users/ctai/Github/ai-guide/.agents/memory/_inventory.md`）。

### 既有 UC 狀態

| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| acceptance-evidence 承載驗收證據階層 | ✅ | skills/acceptance-evidence/SKILL.md | 更新 | 擴增 closure 三層閘＋防線標記制（跨卡 decision contract 落檔） |
| upgrade-nt 觸發語義正確 | ✅ | skills/upgrade-nt/SKILL.md | 更新 | when_to_use copy-paste 錯置句修正 |
| trading-analysis 跨專案可攜 | ✅ | skills/trading-analysis/SKILL.md | 更新 | Layer 2 mosaic 模組名殘留清理 |
| 工具選擇路由單一源 | ✅ | rules/symbol-query-routing.md | 無影響 | 本 EP 明確其權威地位；tool-discipline/modern-cli-preference 退為 pointer |
| codex hooks 接線乾淨 | ✅ | ~/.codex/config.toml | 更新 | stale `[hooks.state]` 殘留清理（machine-local） |

### 新增 UC

| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| enforcement 類 AC 的 closure 驗收契約（三層閘＋防線標記） | 📋 | skills/acceptance-evidence/SKILL.md（S0） |
| AIR-100 開工交接包（單一入口文檔） | 📋 | ai-analysis/reports/guides-refactoring/air100-handoff.md（S2） |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 後續卡（如 air-100 P3）宣稱「硬擋已上線」並請求結案 | 一張卡帶 enforcement 類 AC、卡面勾 Done | 驗收必須出示 Existence（實作錨在場）→ Invocation（registration/caller 真會走到）→ Behavior（negative case 被擋＋positive control 放行）三層證據；缺任一層＝不得 Done——「卡面 Done 是 metadata，不是 capability evidence」 | 無（S0 契約防患於前） | closure 三層閘 |
| SM-2 | 審查者面對多層防線宣稱（hook＋閘＋reconcile）想推論「聯合起來應該都護到了」 | 各防線各自驗綠、無人持有合併視圖 | 禁跨類推論：每個 writer×防線格必須明標 `prevented / detected / unsupported` 三態之一，聯合 coverage matrix 是 acceptance artifact；「每層各有 Done」不可推論 union coverage | 無 | 防線標記制 |
| SM-3 | implement LLM 修正 rules 檔時直接在 canonical main WT 上編輯 | S1 開工、canonical 主樹在 main | 控制面路徑 editing 必須在卡 branch（或 persistent card WT）；canonical main 直 commit 會被 pre-commit guard 擋——被擋＝走卡 branch 重做，不是繞過 | 控制面隔離閘（S0.5 執行紀律） | 工具分工 pointer 化等 rules 變更 |
| SM-4 | codex config 清理後 codex CLI 啟動失敗（TOML parse error） | S1.4 刪錯 `[hooks.state]` 表格邊界 | 從 `.bak` 備份還原 config 後重做；AC 已強制先備份——還原是恢復點 | `cp ~/.codex/config.toml.bak-<date> ~/.codex/config.toml` | codex hooks 接線乾淨 |
| SM-5 | 讀者（air-100 實作 session）想找 runtime validation 該跑什麼、順序如何 | air-100 開工、session 需要 digest | 讀單一入口 `air100-handoff.md` 即獲：synthesis 議題 5/6 精華＋M-D 九條 runtime validation 清單＋Segment 0 五步順序；不需回讀四份 `.agent-tmp` 原稿 | 無 | AIR-100 交接包 |

## 段落劃分原則

- S0 先行（契約文檔是 boundary 產出，且 S1 的「enforcement 驗證式」語義由它定義）；S1/S2 相互獨立、可平行。
- 每段自足（compact 後可單段接續）：各段 Context 內嵌必要背景，不依賴其他段的推論狀態。
- 語義顯式化：S0 與 S1 共享「驗證式＝命令＋預期結果」契約（S0 定義、S1 示範）；S2 不依賴 S0/S1 完成度（handoff 內容源自我有調查產物）。

---

## S0：closure 三層閘＋防線標記制——acceptance-evidence 增節

### Context

**背景**：guides-refactoring 前期調查（M-D 涵蓋面審）發現兩個結構性模式（synthesis §2）：①卡面 Done 但 enforcement 不存在（AIR-90「狀態後綴硬擋」卡面 Done、實作零行——`hooks/block-memory-index-write.py` 全文無 stem-suffix 邏輯，repo-wide 掃描零條 suffix-deny）；②多層防線宣稱堆疊但覆蓋率從未合併檢視（M-D 第一次組出 writer×防線矩陣，結論是覆蓋率遠低於 README 直覺）。codex 意見第 6 點裁決：治理方式不是新增 card schema，而是把 closure 紀律沉進 acceptance-evidence（本 EP caller 採納為 C 層核心產出）。

**前置紀律**：EP 內任何「X 是 bug／殘留／錯置」的判定句，其證據源必須已核對過該句的權威載體（骨架／權威 rule／實作檔）；未核對的判源不得直接進 AC——這正是本節三層閘要治理的「宣稱先於驗證」形態，EP 自身不豁免。

**需求邊界**：Always＝落點只能是 `skills/acceptance-evidence/SKILL.md` 增節（不動 `rules/acceptance-evidence.md` always-on 核心、不新開檔）；引用 memory-audit 統一定義表用指針不重抄。Ask First＝無。Never＝不把 AIR-100/113 的實作決策寫進來（本節是跨卡契約不是某卡的 plan）；不在 rule 層複製本節內容（residency：on-demand 方法論住 skill）。

**UC 引用**：實作「enforcement 類 AC 的 closure 驗收契約」。**Invariant Impact**：無（文檔變更，silent-corruption path 不適用——但本節自身就是對此類風險的治理產出）。

**依賴**：無段落依賴（S1 的驗證式格式消費本節語義，但 S1 實作不需 S0 先落地——rg 驗證式已是既有慣例）。**語義約束**：與 S1 共享「驗證式＝命令＋預期結果」。**基礎設施盤點**：`skills/acceptance-evidence/SKILL.md` 現有結構（L1-L6 證據階層、Claim→Evidence→Trust）；`skills/memory-audit/SKILL.md:139-149` 載體統一定義表（指針目標）；instruction-writing skill 撰寫規範（增節須遵守）。**依賴錨點**：S0 只寫 `skills/acceptance-evidence/SKILL.md`（定義端），消費端＝後續所有 enforcement 類卡（未來態，無現存 caller 需改）。

### 修改要點（Pseudo Code 裁剪——docs mode）

`skills/acceptance-evidence/SKILL.md` 新增一節（建議節名「Closure 三層閘與防線標記制」；插入位置由實作時按現有結構選擇，鄰接驗收/證據階層主題）：

1. **Closure 三層閘**（enforcement 類 AC 專用——宣稱 hard guard / deny / enforcement / hook 的 AC 適用）：
   - **Existence**：實作與測試 artifact 存在（file:line 錨，rg 可達）。
   - **Invocation**：實際 registration / caller 會走到它（wiring 錨，非「檔案裡有這段字」）。
   - **Behavior**：negative case 被擋＋positive control 放行（雙向實測；只驗 negative 會擋掉合法流量而不自知）。
   - claim 涵蓋某 harness 時加第四層：actual-runtime receipt（該 harness 實跑證據）。
   - 結案時 fresh rerun，receipt 掛回卡；Done status 是 metadata，不作為 capability evidence。
2. **AIR-90 反例全文入册**：以 AIR-90（狀態後綴硬擋——卡面 Done、`hooks/block-memory-index-write.py` 全文無 stem-suffix 邏輯（行數以入册時 `wc -l` 實測為準，不固化二手數字）、repo-wide 掃 `hooks/|muse-plugins/|scripts/|skills/memory-audit/` 零條 suffix-deny；M-D 實測「被擋的 writer 路徑＝無（零）」）作為反例案例，說明「卡面宣稱≠enforcement 錨存在」與結案 gate 為何漏（驗收了文件宣稱而非 code 錨）。
3. **防線標記制**：writer×防線聯合 coverage matrix 為 acceptance artifact——每格明標 `prevented`（事前攔截）/ `detected`（事後偵測，如 reconcile）/ `unsupported`（無防線）三態之一；**禁跨類推論**（detected 不可當 prevented 用；「每層各自驗綠」不可推論 union coverage）。
4. 全節經 instruction-writing 規範（AI 可執行、結構可機械解析）；引用 memory-audit 統一定義表處用一行指針，不重抄表格。

### 驗證策略（AC）

- **AC-S0-1（三層閘在場）**：`rg -n "Existence|Invocation|Behavior" skills/acceptance-evidence/SKILL.md` → 命中新增節，且三層各有一段可執行定義（非僅名詞列舉）；同時 `rg -n "negative.*positive|positive control" skills/acceptance-evidence/SKILL.md` → 命中（Behavior 層雙向要求在場）。
- **AC-S0-2（AIR-90 反例入册）**：`rg -n "AIR-90" skills/acceptance-evidence/SKILL.md` → 命中反例段，內文含「Done status 是 metadata，不是 capability evidence」（或同義句）＋後綴硬擋零實作事實＋行數宣稱（如有）與入册時 `wc -l` 一致。
- **AC-S0-3（防線三態＋禁跨類推論）**：`rg -n "prevented|detected|unsupported" skills/acceptance-evidence/SKILL.md` → 三態齊現；「禁跨類推論」條款在場（`rg -n "跨類推論|union coverage"` 命中）。
- **AC-S0-4（指針不重抄＋撰寫規範）**：`rg -n "memory-audit" skills/acceptance-evidence/SKILL.md` 新增節命中指針行，且新節內**無**統一定義表欄位複製（目視＋`rg -n "載體統一定義表"` 只出現指針不出現表格重刻）；`rules/acceptance-evidence.md` 零變更（`git diff --stat rules/acceptance-evidence.md` → 空）。

---

## S1：無主機械批（四項，各自獨立 AC）

### Context（S1 總）

**背景**：synthesis EP 種子清單「機械可判、幾乎無爭議」項，經 caller 裁決收進本 EP（其餘歸 air-100/113，見範圍外對照表）。四項互不依賴，可逐項實作逐項驗收。**UC 引用**：分見各子項。**Invariant Impact**：無（文檔＋machine-local config）。

**依賴錨點（四子項共用背景）**：`rules/symbol-query-routing.md:9` 是工具分工的權威載體（M-A F1-1「唯一 bootstrap 責任者」）；三支 rules 的分工句重述＝M-A F1-2/F1-3 判讀的語義等價雙錨。

**執行紀律（S1 全體適用，先讀 S0.5）**：`rules/`、`skills/` 是控制面路徑——editing 必須在卡 branch（或 persistent card WT），canonical main 直 commit 被 `control-plane-guard.sh` 擋；**部署（rules/AGENTS.md 部署紀律的 bundle 同步）不在本 EP scope**——列 user gate，implement LLM 不執行 deploy。

### S1.1：upgrade-nt when_to_use「SJ 測試」句——查證後決策項

- **Context**：`skills/upgrade-nt/SKILL.md` when_to_use 寫「必須在收盤後執行（需跑 SJ external API 測試）」。M-A F3-2 判此為 copy-paste 錯置（SJ 屬 upgrade-sj），**但該判源未讀 `_common/upgrade-flow.md` 骨架**；骨架 `:9-12` 明載「必須在收盤後執行…升級後需跑 `tests/external_api/sj/` 完整外部 API 測試」、`:64-65` DEPTH-FULL 即跑 `tests/external_api/sj/`，而 upgrade-nt 本體將流程全面委派骨架、無 override——骨架文本支持「該句非錯置」。**先查證、後決策**（S0 原則：宣稱不得先於驗證）。**UC 引用**：更新「upgrade-nt 觸發語義正確」。
- **查證路徑（實作 session 第一動，S1.1 其餘步驟凍結）**：①mosaic 端確認 `tests/external_api/sj/` 存在且升級流程實際觸達（`ls tests/external_api/sj/`＋比對 upgrade-flow DEPTH-FULL 段在該 repo 的實際執行紀錄／升級 receipt）；②對照 upgrade-nt 佔位符代入值（本檔只承載 NT 專屬內容）確認無 SJ 排除條款。
- **決策分支**：查證證實「升級後會跑 SJ 測試」→ **整項撤銷不動檔**（本句非 bug；ledger 記「前提否證」結案）；查證證實「不跑」→ 保留「收盤後執行」半句、僅刪 SJ 括號，且 completion report 須附 mosaic 端證據錨點。查證無法完成（mosaic 不可達）→ 整項 defer 並在 ledger 記錄殘餘未知。
- **驗證式（依分支）**：撤銷分支＝`git diff --stat skills/upgrade-nt/SKILL.md` → 空；修正分支＝`rg -n "SJ" skills/upgrade-nt/SKILL.md` → 0 hits＋`rg -n "when_to_use" skills/upgrade-nt/SKILL.md` → 欄位在場且與骨架制約一致＋`git diff --stat skills/upgrade-sj/` → 空。

### S1.2：trading-analysis mosaic 模組名殘留清理

- **Context**：`skills/trading-analysis/SKILL.md:29-32` Layer 2 列 `mosaic_alpha/indicators|structure|features` 三行 mosaic 專屬模組名——M-A F3-3 判「保留本 skill 須先清 project 殘留」。處置＝**參數化**（該節已有的「跨專案時替換為當前專案的對應模組」句已指出方向）：把三行 mosaic 具名清單改為佔位描述（例：「當前專案的指標模組（如 RSI, MACD, ATR 計算層）／結構模組（swing/leg/trajectory 類）／特徵工程模組」），或整段收斂為一行佔位＋例。**保 trigger 辨別力**：frontmatter description 與觸發詞零變更。**UC 引用**：更新「trading-analysis 跨專案可攜」。**驗證式**：`rg -n "mosaic_alpha" skills/trading-analysis/SKILL.md` → 0 hits；`git diff skills/trading-analysis/SKILL.md` 目視＝變更僅及 Layer 2 清單段，frontmatter 區零 diff。`:61`「材料源：mosaic MOS-42 現增事件弧」歸屬句**保留不動**（歷史 provenance 記錄，非模組殘留）。

### S1.3：rules 工具分工句 pointer 化（tool-discipline＋modern-cli-preference）

- **Context**：分工句「文字→rg、檔案→fd」live 面三處重述（`rules/tool-discipline.md:9`、`rules/modern-cli-preference.md:7`、`rules/symbol-query-routing.md:9`）；M-A 裁：symbol-query-routing＝權威保留；tool-discipline 分工句＝pointer 化；modern-cli-preference 整檔（僅 2 行有效內容）＝唯一增量「fd 預設遵守 .gitignore」半句。caller 裁決：**先 pointer 化、後退役；最終退役（刪 rule 檔）defer 到「fd-.gitignore 非 bootstrap」驗證——列 open decision，非本 EP AC**（對應 codex 意見第 4 點 defer 原則）。
- **修改要點**：
  1. `rules/tool-discipline.md:9` 分工句段退為一行 pointer：保留首句語義的極簡形（例：「符號/文字/檔案/型別查詢路由見 symbol-query-routing.md（fd 預設遵守 .gitignore）；視覺判讀走 vision-review agent，禁主 session 讀圖；spawn prompt 必指定工具，禁只寫『讀取/驗證』」）——「fd 預設遵守 .gitignore」半句從 modern-cli-preference 併入此處；視覺判讀 spawn 句與其餘節不動。
  2. `rules/modern-cli-preference.md` 退為 pointer 形態：標題與指針保留（指 symbol-query-routing rule＋modern-cli-preference skill 陷阱目錄），分工句正文刪；**檔案本體不刪**（退役＝open decision，見「Open Decisions」節）。
  3. `rules/symbol-query-routing.md` 零變更（權威端）。
- **UC 引用**：無影響「工具選擇路由單一源」（反向強化——重述消除後單一源真成立）。**驗證式**：
  - `rg -n "文字→rg" rules/` → **0 hits**（重述消除——權威端本就用空格形「文字 rg、檔案 fd」）；`rg -n "文字 rg、檔案 fd" rules/symbol-query-routing.md` → 命中（權威端原句在場、零變更）。
  - `rg -n "vision-review" rules/tool-discipline.md` → 命中（vision 句未誤刪）。
  - `rg -n "gitignore" rules/tool-discipline.md` → 命中（fd 半句已併入）；`rg -n "gitignore" rules/modern-cli-preference.md` 命中與否皆可（該檔已 pointer 化即合規）。
  - `ls rules/modern-cli-preference.md` → 檔案仍在（退役未執行）。
  - **bundle 尺寸不得上漲**：pointer 化是減量操作——`git diff --stat rules/tool-discipline.md rules/modern-cli-preference.md` 淨行數應為負或持平。

### S1.4：codex config stale `[hooks.state]` 殘留清理（machine-local live config）

- **Context**：F-C unverified 11 發現 `~/.codex/config.toml` `[hooks.state]` 區段殘留指向**已退役** `~/.codex/hooks.json` 的 trusted_hash 條目。寫 EP 時實況（2026-09-16 讀檔）：不只 caller 引的 `:208-209,238-239`——**共 6 條** local hooks.json 條目（`pre_tool_use:0:0`〔208〕、`session_start`〔211〕、`session_end`〔214〕、`subagent_start`〔217〕、`stop`〔220〕、`pre_tool_use:0:1`〔238〕）；market plugin 條目（`delegate@delegate-market`／`muse@muse-market`）與 `config.toml:interrupt`／`config.toml:pre_tool_use` 條目是 **live 接線，禁動**。
- **操作順序（AC 強制）**：①先備份 `cp -n ~/.codex/config.toml ~/.codex/config.toml.bak-$(date +%Y%m%d)`（no-clobber：備份已存在則不覆蓋並先核對，防二次執行摧毀原始恢復點）；②刪 `[hooks.state]` 區段內所有路徑含 `/Users/ctai/.codex/hooks.json` 的條目（連同其 `trusted_hash` 行，注意 TOML 表格邊界——刪後相鄰表格頭不得黏連）；③改後驗證 codex 啟動。
- **驗證式**：
  - 備份在場：`ls ~/.codex/config.toml.bak-*` → 命中當日備份。
  - 殘留歸零：`sed -n '/\[hooks.state\]/,/^$/p' ~/.codex/config.toml | rg 'hooks\.json'` → 0 hits（掃描範圍限 `[hooks.state]` 區段——market plugin 條目路徑含 `hooks.json` 但非 local 殘留，禁誤刪；以 `rg -n 'Users/ctai/.codex/hooks.json' ~/.codex/config.toml` 為精確判準 → 0 hits）。
  - live 條目未動：`rg -n 'config.toml:pre_tool_use|config.toml:interrupt|delegate@|muse@' ~/.codex/config.toml` → 各命中且數量與改前相同（改前先記錄基準數）。
  - 啟動驗證：`codex --version` 正常輸出＋跑一次 `codex exec "reply ok"` smoke（或等效最短互動）無 TOML parse 錯誤、無 hooks 載入錯誤訊息。
  - **回復**：任何驗證失敗 → `cp ~/.codex/config.toml.bak-<date> ~/.codex/config.toml` 還原後重新診斷（SM-4）。

---

## S2：AIR-100 交接包

### Context

**背景**：guides-refactoring 前期調查（synthesis 議題 5/6＋M-D coverage matrix＋codex 意見）產出了 air-100 開工所需的全部裁決輸入，但它們散落四份 `.agent-tmp` 文檔（`.agent-tmp` 是暫存區，弧結束後會清）；air-100 卡 notes 已指定開工 session 必讀 `.agent-tmp/six-card-review/dossier.md`——本交接包補上 guides-refactoring 弧這一份。**不改 air-100 卡面**（卡 metadata 更新列 completion report 提案交 user——board single-writer 紀律）。

**開工前置（快照）**：S2 開工第一動先快照內容源——`m-d-output.md`「Runtime validation 建議清單」節、synthesis 議題 5/6、codex-opinion 第 2 點——至 `ai-analysis/reports/guides-refactoring/sources/`（逐字快照或精確摘錄）；快照完成後 S2 的一切引用改指快照路徑（`.agent-tmp` 會被清，快照是唯一持久源）。

**UC 引用**：實作「AIR-100 開工交接包」。**依賴**：無（內容源自我有調查產物，S0/S1 完成度不影響）。**驗證式（AC）**：

- **AC-S2-1（檔案在場＋結構三段）**：`ai-analysis/reports/guides-refactoring/air100-handoff.md` 存在，且含三個標題段：①synthesis 議題 5（hooks wiring 矩陣）＋議題 6（後綴擋零實作＋coverage matrix 精華）；②M-D 九條 runtime validation 清單（逐條：CC/ZCode Write 重放、NotebookEdit 缺口確認、subagent 負對照、muse 三斷言、teardown 偵測鏈、後綴擋可驗性前置、codex 面、consolidation 轉寫稽核、approve 漂移監控——自快照 `sources/`（開工前置快照）逐條攜帶；源檔已清則以快照為唯一源）；③Segment 0 順序五步：cutover snapshot → 關閉／隔離新污染來源 → forward guard → 存量處置 → reconcile acceptance（codex 意見第 2 點；含「先堵後清」理由——41→78 基線成長實證 moving target）。
- **AC-S2-2（不自立新決策）**：handoff 不含 AIR-100 已決策事項的重辯或新裁決——卡 Plan 的七條「已決策勿重辯」以指針引用（`rg -n "已決策" <handoff>` 命中指針行、無重述表格）；防線形態（subagent/codex/teardown prevented vs detected）以 M-D 三態標記呈現選項，不替 air-100 拍板。
- **AC-S2-3（卡面零變更）**：`git diff --stat 'backlog/tasks/air-100*'` → 空；completion report 中列「air-100 卡面更新提案」（如 notes 增 handoff 指針）交 user。

---

## S0.5：執行紀律（附段——S1 開工前必讀）

1. **控制面隔離（硬約束）**：`skills/`、`rules/` 是控制面路徑——editing 必須在卡 branch（自 main `git checkout -b air-<N>`，N＝本弧追蹤卡號）或 persistent card WT（`scripts/wt-open.sh <卡id> --base main`）。canonical main 直 commit 被 pre-commit `control-plane-guard.sh` 擋；被擋＝走卡 branch 重做（軟條款不適用控制面路徑）。`~/.codex/config.toml` 是 machine-local 檔、不進版控，不受此閘管——但受 S1.4 備份紀律管。
2. **deploy 不在本 EP scope**：rules/skills 變更後的 bundle 部署與部署驗證（rules/AGENTS.md「部署紀律」）＝**user gate**——implement LLM 完成編輯＋rg 驗證後停手，completion report 列「待 deploy」交 user；禁自主執行 `deploy_agents.py`。
3. **commit 紀律**：每子項一個 commit（message 帶卡 id）；**每個 commit 均經 `/commit` user gate**（outward-action-consent：一次授權≠永久授權）；autonomous／退化 session 一律不 commit、只結算回報；`/commit` 確認通過後才收 branch——收尾 merge 照 AGENTS.md「收尾」條（`--ff-only`）。
4. **每項 AC 驗證式＝命令＋預期結果**（S0 契約的示範形態）：結案時 fresh rerun，receipt 落 completion report。

## 範圍外對照表（零重疊聲明）

| 項目 | owner | 為何不在本 EP |
|------|-------|--------------|
| 後綴擋實作（block-memory-index-write.py stem-suffix exit-2） | AIR-100 P3 | 決策已有（air-90:20→air-100 承接）、code 缺席＝純落地，屬 enforcement truth 修復 |
| NotebookEdit dead-matcher 處置（補分支或移 matcher 字面）＋ matcher/handler single-source coverage assertion | AIR-100 | writer governance boundary（codex A 層） |
| subagent／codex／muse teardown 防線形態（prevented/detected/unsupported 政策） | AIR-100 | prevention-vs-detection policy＝控制面 boundary 決策 |
| M-D 九條 runtime validation 的**執行** | AIR-100 開工第一動 | 本 EP 只文檔化清單（S2），不執行 |
| 池 86 條收編／38 條後綴群處置／cutover snapshot | AIR-100 P2 | 存量治理 |
| memory-audit:149（卡面記 :147）stale 條款修正 | AIR-100 P5（AC A5） | 卡面已有 owner；本 EP S0 不碰 memory-audit |
| `~/.agents` 清理政策（memory-bundles／probe-entitlements）執行 | AIR-100 或夜波（待裁） | 裁決輸入已在 synthesis 議題 7，owner 未定≠本 EP 吸收 |
| 六支 domain skills 遷出評估（nt-query／nt-v1-query／upgrade-nt／upgrade-sj／swing-analysis／kbar-form-analysis） | AIR-113 AC#2 | fleet disposition＝113 核心 scope；本 EP 的 S1.1 只修 copy-paste 句**不動遷出決策**（upgrade-nt/sj 遷出與否仍歸 113） |
| instruction-testing 去留＋`:56` 歸因修正 | AIR-113 AC#4 | 同上 |
| desc 瘦身（nt-query／nt-v1-query 等） | AIR-113 | 同上 |
| 六支 when_to_use 補欄（驗 trigger 辨別力非僅欄位存在） | AIR-113 | 同上——**辨識**：本 EP S1.1 修 upgrade-nt 既有 when_to_use 的錯置句，非補欄，兩者不重疊 |
| 11 篇 09-15 reports lifecycle 分類 | AIR-113 | report 載體治理 |
| modern-cli-preference rule **退役執行**（刪檔） | open decision（下節） | defer 到驗證，非本 EP AC |

## Open Decisions（非本 EP AC——列 user 裁決）

1. **modern-cli-preference 退役執行**：S1.3 pointer 化完成後，刪 `rules/modern-cli-preference.md` 的前置驗證＝「fd 預設遵守 .gitignore 非 bootstrap 必要知識」（rule 資格公式：首個有後果決策前是否必須在場——反駁條件來自 M-A F1-3）。驗證法建議：退出常駐三測試（bootstrap／首動／跨來源重重複）實跑一輪；通過＝另開小卡或隨 AIR-113 執行刪檔＋`skills/CLAUDE.md` 索引同步。
2. **本 EP 追蹤卡建立**：EP 撰寫 session 受硬約束禁 git 寫——建卡（`backlog task create`＋ref 掛本 EP）交 caller/user。
3. **deploy 時點**：S1.3 rules 變更後的 bundle 部署（含 muse bundle 尺寸複測——pointer 化屬減量，預期 F3 回漲壓力略降）交 user 排程。

## 回復方式

- **repo 內（S0/S1.1–S1.3）**：卡 branch 上 `git revert` 或 `/commit` 前丟棄（`git checkout -- <file>`）；merge 後回復＝revert commit（控制面路徑照隔離閘走 branch）。
- **machine-local（S1.4）**：`cp ~/.codex/config.toml.bak-<date> ~/.codex/config.toml`（S1.4 強制備份）。
- **report（S2）**：直接刪檔（report 是證據載體，無下游消費者）。

## 收尾步驟（docs mode 形態）

1. 受影響命令/rules 行為已反映：S0 增節納 acceptance-evidence 既有審查鏈消費（後續 enforcement 卡自動吃到）；`skills/CLAUDE.md` 工作流索引若列 acceptance-evidence description 需同步（有動 desc 才同步）。
2. 結案兩步＋弧結案蒸餾（照 kanban-board 命令合約；追蹤卡由 user 建後適用）。
3. instruction 檔檢查：本 EP 未動模組 AGENTS.md；`rules/AGENTS.md` 部署紀律段無需更新（pointer 化是既有分層模式應用）。
4. `/audit-test`：跳過（純文檔＋config，無測試面）——completion report 記理由。
5. memory 池補掃（UC 盤點同主題條目項）＋本弧結案蒸餾。

---

## 給 implement LLM 的接手入口

1. **先讀**：本 EP 全文（自足）＋`skills/instruction-writing/SKILL.md`（S0 增節與 S1.1–S1.3 編輯的撰寫規範）。`.agent-tmp/guides-refactoring/*` 四份是證據源——**唯讀**，不假設它們在場（`.agent-tmp` 會清；S2 的目的就是把精華落盤到 reports）。
2. **開工起手式**：⑤ kanban 起手式後自 main 開卡 branch（卡號＝user 建的追蹤卡；未建前**不開工**——向 user 回報等待建卡）。WT 形態（checkout 卡 branch vs `scripts/wt-open.sh` persistent card WT）由 caller 於開工指示；未指示＝預設 checkout 形態。走 persistent 形態則收尾觸發 AIR-112 wt-close receipt 鏈（`--preflight`）。
3. **從哪段開始**：S0 → S2 快照前置（若 `.agent-tmp` 已清，改用快照）→ S1（S1.1→S1.2→S1.3→S1.4 任意序，S1.4 記得先備份）→ S2 本體。S1 開工前重讀 S0.5 執行紀律。
4. **每段完成**：跑該段全部驗證式（命令＋預期結果）→ 結果貼段落驗收紀錄 → commit（帶卡 id）。
5. **Red lines（autonomous 禁令）**：禁 commit 以外的 git 寫操作中未經 user 確認的形態（`branch -D`／force／rebase main）；**禁 deploy**（`deploy_agents.py`／bundle 同步＝user gate）；**禁動 air-100/air-113 卡面**（S2 AC-S2-3）；禁碰範圍外對照表所列任何項目；S1.4 改壞即從 `.bak` 還原並回報，不嘗試第二次猜測式修復。
6. **完成報告**：各段 AC 驗證式輸出＋現代化提案清單（air-100 notes 指針、追蹤卡建立、deploy 排程、open decisions 三項）交 user。
