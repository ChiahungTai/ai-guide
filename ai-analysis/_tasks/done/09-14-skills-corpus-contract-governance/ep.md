# AIR-87 EP——skills corpus 載入/觸發契約治理

> **ep_type**: implementation
> 卡：AIR-87（In Progress）。baseline：air-87 @ `9771931`（開工 metadata commit）。
> 材料源：reports/2026-09-13-zcode-skills-baseline/report.md（97 active 盤查＋model-routing root cause）＋materials/superpowers-testing-research.md（durable，AIR-85 借鑑）＋AIR-85 EP「段 3 驗收證據」與「第二支 pilot」節（行為測試實證＋載具配方）＋AIR-88 卡（probe 2+2 PASS 配方）。

## UC 盤點（docs mode——受影響命令/rules 清單）

### Backlog 關聯
- AIR-87（本卡）；上游已結案：AIR-85（條件載入層＋行為測試配方）、AIR-88（probe 補跑）、AIR-89（model-routing 事實句）
- 自動建卡：無新 UC（skills 治理屬既有 corpus 維護，以卡承載）

### SYSTEM-MAP 影響
- 無（無 SYSTEM-MAP.md）

### 掃描範圍
- `skills/instruction-testing/SKILL.md`（改造本體，162 行）、`skills/instruction-writing/SKILL.md`（增補）、79 支 `skills/*/SKILL.md` desc 面
- `scripts/`（新掃描 script＋activation probe script 兩支入庫）
- `skills/CLAUDE.md` Skill 索引（desc 改寫 ripple——索引若摘述 desc 需同步）
- 官方契約源：`~/.zcode/cli/plugins/cache/zcode-plugins-official/zcode-guide/0.1.0/skills/diagnosing-skills/SKILL.md`

### 同主題 memory 條目（結案蒸餾範圍）
- `project_skills-corpus-governance-baseline`（本弧 baseline 條——結案蒸餾）
- `feedback_engine-skill-trigger-collision`（desc 觸發詞重疊=路由歧義——語義相關）
- `project_zcode-skill-usage-audit-0909`（80 skills 終態——歷史背景）

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| instruction-testing＝行為驗證 bounded context | ✅ | skills/instruction-testing | 更新 | 增機械觀察面 protocol＋四 surface gate（取代主觀三級風險表） |
| instruction-writing＝靜態 authoring 規範 | ✅ | skills/instruction-writing | 更新 | 增跨 harness desc 消費差異節（範圍#5） |
| desc 契約機械掃 | 無 | scripts/ | 📋 新增 | AC#1 入庫可重跑 |

---

## 段落 0：全域研究（已完成，材料＋本日 pre-scan）

1. **官方契約釘死**（zcode-guide/diagnosing-skills file:25/27/31/47，實證交叉）：
   - **drop 軸＝desc 值 >1024 chars**——非整行、非 bytes。實證：cr-query 值 1,022／nt-v1-query 值 1,014 兩者皆載入（本 session 清單在場）；model-routing 舊值 1,187 被 drop；現值 775 chars/1,189 bytes 載入成功（bytes>1024 不 drop→chars 軸）。**量測陷阱：awk length 給 bytes、CJK 3B/char——掃 script 必須 Python len()**
   - 觸發呈現＝name＋desc（截 ~250）＋`when_to_use` 鍵（官方認可鍵：name/description/when_to_use/license/metadata）；官方明言 front-load trigger wording 於前 250
   - flat `key: value` 解析；多行值需 `>`/`|` block scalar（載入 OK，實證 maintain/scan-project 在清單）
2. **79 支 pre-scan 現況**（.agent-tmp/air87/desc_prescan.py，2026-09-14；數字一律 as-written 口徑＝含引號）：over1024=2（cr-query／nt-v1-query——**值未超**，在線上但零餘裕）、unquoted=30、block scalar=2（maintain/scan-project）、hash 陷阱=2（python-type-gap/rules-reminder，已引號→安全）。**when_to_use 鍵實測 47/79 支已在用**（工作流 skills 全面；cr-query/nt-v1-query/implement/execution-plan/post-build/consistency 皆帶）——ZCode 觸發面＝desc-250 截斷＋when_to_use 全文**雙 surface**；AC#5 probe FAIL 時無法歸因單一 surface（已知限制，補救迴路兩面同時調）
3. **高流量 desc 前 250 現況**：kanban-board＝既有典範（「當你要…時」開頭）；implement（63 chars）/execution-plan（97 chars）＝what-it-is 開頭無觸發條件；memory-audit（613）/instruction-writing（414）/acceptance-evidence（464）＝when-to-use 落在 250 邊界外
4. **行為測試方法論**（卡已決策勿重辯）：四 surface gate＋activation/decision/output/static 測試型映射；AIR-85/88 probe 實證（scratch carrier＋canary＋premature-action 判準＋四態）
5. **風險假設**：
   - （中）probe 直連 zcode.cjs 的安裝路徑與 provider config 解析——AIR-85 已驗證同法五輪，屬低風險重現；bridge 2.0.4 carrier 注入法（AIR-88）為替代腿
   - （中）desc 改寫的 CC 端回歸——CC 消費全文 desc，改寫僅重排語義不刪觸發詞則無害；AC#5 nonmatch 臂護之
   - （中）**provider 故障**（AIR-85 實證：z.ai「Model creation failed」當日阻斷 probe；本弧 codex web 池亦連兩敗）——處置＝時間盒順延整段，**不在故障窗 retry-to-green**（RUNS 統計≠挑綠燈）
   - （低）when_to_use 增補＝本弧新增 4 支對齊既有 47 支慣例（user 裁定 (b)），非全面改寫路徑

## Scenario Matrix（關鍵情境）

| # | 情境 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|---|---|---|---|---|
| S1 | desc 值 >1024 的 skill | 新 ZCode session 掃 skills | 清單不含該 skill（drop） | model-routing 舊例舉證 | desc 契約掃 |
| S2 | unquoted desc 含 ` #` | 完整 YAML vs flat parser 雙讀 | 兩者長度分歧（掃 script flag） | pre-scan 2 例 | desc 契約掃 |
| S3 | 高流量 skill 收到匹配任務 prompt | isolated fresh session positive 臂 | 首個 consequential action 前實際載入 | AC#5 probe | 觸發語義前置 |
| S4 | 高流量 skill 收到無關任務 prompt | nonmatch 臂 | 零載入 | AC#5 probe | 觸發語義前置 |
| S5 | instruction-testing 被改 desc | surface gate 判定 | activation 面→positive/nonmatch test | 段 1 自舉 | instruction-testing 改造 |
| S6 | 撞名 skill（repo vs plugin 同名） | ZCode 載入序 | user>workspace>plugin——repo 版生效 | 段 5 裁定 | 撞名處置 |

---

## 段落 1：instruction-testing skill 改造（AC#6）——凍結規格先行

**Context**：本弧改 desc 前先落地測試方法（卡範圍#6）。高保護面改動（行為驗證 bounded context 擁有者）——**凍結規格→codex 諮詢→實作→獨立審**（handoff 工作形態）。

**要點**：
1. **L10 措辭修訂**（審查 #10 精確版）：「不引入 superpowers 的 bootstrap／drill eval harness／plugin 分發結構；自研 validated adapter（scripts/skill_activation_probe.py）與 scenario 配方由本 skill 擁有，易漂移細節住 scripts/／durable report，body 只留跨 harness invariant」
2. **四 surface gate 取代「先判風險，再決定驗證深度」三級主觀表**（卡已決策）：diff 觸及面→測試型——activation 面（name/desc/trigger 詞/frontmatter/bootstrap pointer）→positive＋nonmatch activation test；decision 面（must/禁止/gate/authorization/fail-closed）→behavior scenario，discipline 類升完整 RED→GREEN→REFACTOR——**discipline 判定特徵句隨遷**（agent 知道規則但速度/sunk cost/authority/方便性誘因推違規；失效破壞 workflow gate／安全邊界／驗收可信度——舊表專有，不隨遷即成無定義詞）；output 面（required field/template slot/recipe）→micro-test；僅 typo/link/格式→static-only。**非三面關鍵詞但可寫 X/Y 的語義編輯→至少輕量 behavior scenario（舊中類 retrieval/application 路徑落點，防降級）**；「分類不確定時先寫一句可觀察失敗 X/Y」保留（機械化輔助判面）
3. **機械觀察面 protocol 段入主文（15-25 行）**——跨 harness invariant：control/treatment 對照、consumer-visible state 判分、premature-action 檢查（首個 Skill 載入前無實質 tool_use）、四態分類（PASS/FAIL/UNEXPECTED/INCONCLUSIVE——非預期≠目標失敗）、RUNS 統計重複≠retry-to-green、recall（skill 清單出現/description 複述）≠behavior 分層標注、present/missing 場景對稱、**機械判分只當 locator、flagged case 必人工讀**
4. **移出 pilot 案例段 L119-149**（31 行）→ `materials/must-execute-pilot-scenarios.md`（本任務家，durable；已完成逐字遷出）；skill body 留一行指針
5. **載具 adapter 不進 body**：ZCode scratch carrier（HOME=scratch＋`.agents/skills` 單根＋config 0600＋headless 直連）與 CC settings symlink＋probe 形態——落 `scripts/skill_activation_probe.py`；**script 殼隨段 1 commit**（body 指針的引用存在性才能綠，段 4 補全功能）
6. 完成判準清單同步新結構；「換內容不增肥」——移出 31 行 vs 新增 ~20 行 protocol＋4 行 gate 表，淨 −7 行左右
7. 自舉宣稱：本 skill desc 今日僅引號化＝static 面＋在場舉證（本 session 清單在場）；段 1 若動 trigger 詞則自納 AC#5 抽驗

**驗證策略**：靜態——五維自洽＋引用存在性＋rg 殘留（pilot 段零殘留）；獨立 code-review（post-build 鏈，flash＋codex）；行為面＝AC#5 抽驗覆蓋（若 trigger 詞有動）。

## 段落 2：desc 契約掃 script＋79 支全綠（AC#1）

**Context**：實作卡範圍#1。量測軸釘死＝**desc 值 chars**（含引號字元、Python len）。

**要點**：
- `scripts/scan_skills_desc.py`：掃 `skills/*/SKILL.md` frontmatter——①值 ≤1024 chars（>1024 = FAIL）②形式＝雙引號單行或 block scalar（bare unquoted／單引號 = FAIL——僅認雙引號）③quoted 值內含 ` #` 警告（雙解析器語義 OK 但追蹤）④前 250 觸發語義＝**AC#2 人工判讀面、掃不承作**（語義判定非機械，docstring 同步此界）⑤輸出 per-skill 表＋exit code（0 全綠/1 有 FAIL）；`--fix` 引號化 bare desc；`--headroom N` 餘裕檢查
- 修復面：30 支 unquoted→雙引號化；cr-query/nt-v1-query 值收斂 ≤950（留餘裕）；block scalar 2 支維持（官方支援、觸發正常——不為一致而改）；**轉義規約：值內遇 `"` 優先改寫內文而非 escape**（execution-plan 既有 `\"` 形態為歷史相容，不改）
- **scripts 入口層級紀律**：純機械掃描，無 library 依賴
- 已知限制（docstring 記）：block scalar 量法採 space-fold 近似；跨多個 block key 的連續行會混收（本 repo 僅 2 支單鍵，實害零）

**驗證策略**：實跑 script（must-execute）——修復前 FAIL 名單 vs 修復後全綠對照**落卡 notes**（AC#1 出口證據，非只住 .agent-tmp）；`tests/test_scan_skills_desc.py` 9 條契約軸回歸（值 chars 軸、CJK≠bytes、行前綴不計、bare/quoted/block/missing 判形）隨入庫；語法 ruff。

## 段落 3：高流量 skills 觸發語義前置（AC#2）＋AC#4 舉證

**Context**：實作卡範圍#2。改寫模式＝「觸發條件句（當…時/…前）——內容索引」（kanban-board 典範）。

**要點**：
- 高流量清單（凍結）：memory-audit、implement、execution-plan、instruction-writing、acceptance-evidence、validation-strategy、post-build、consistency；kanban-board 驗證不重寫；model-routing 已 hotfix 不動
- 每支：前 250 chars 承載 when-to-use（觸發條件句「當…時／…前」——內容索引）；觸發詞（中英）保留；CC 端全文消費不刪語義
- **when_to_use 增補 4 支**（user 裁定 (b)，2026-09-14）：memory-audit/instruction-writing/acceptance-evidence/validation-strategy——恰好都沒有 when_to_use，對齊既有 47 支慣例（additive 官方鍵，ZCode 全文觸發面直接補強）
- ripple：`skills/CLAUDE.md` Skill 索引行若摘述 desc 需同步
- AC#4 舉證兩時點：(a) model-routing 面——本 session（hotfix 後新鮮 session）清單在場，舉證文字落卡；(b) **段 3 commit 後**新鮮 session 抽樣 ≥2 支改寫 skill 清單在場

**驗證策略**：段 2 script 重跑全綠（改寫不撞限額）＋AC#5 activation 抽驗（4 支）。

## 段落 4：activation probe 載具＋AC#5 抽驗

**Context**：卡 AC#5。判準＝「首個 consequential action 前是否實際載入／nonmatch 未載入」；recall 不算（卡已決策）。

**要點**：
- `scripts/skill_activation_probe.py`（段 1 落位共用）：stage scratch HOME→`.agents/skills` symlink 指 repo skills→config stage（provider 解析照 AIR-85 EP 段 3 方法注記；0600）→headless 直連跑 prompt→JSON 流判分（premature-action check＋Skill tool invoke／body 逐字引用）
- 抽驗 4 支：memory-audit、implement、execution-plan、**nt-v1-query**（第 4 支＝審查 #5：段 2 修剪實刪候選觸發詞＝on_order_filled、submit_order、daemon thread、BarDataWrangler——position 計算/accounting 仍在 desc，須行為面覆蓋）；positive/nonmatch 各 5 reps、四態記錄落卡 notes
- 成本紀律：RUNS 統計非 retry；per-run 預算上限；CLI exit code 不參與判準；**provider 故障→時間盒順延整段（段落 0 風險 3）**
- 已知限制（落卡）：8 支段 3 改寫僅 4 支 probe，其餘 4 支（instruction-writing/acceptance-evidence/validation-strategy/consistency＋post-build 不動）僅 static 面覆蓋；probe 單根環境 vs 正式環境雙清單差異（AIR-85 已證單根可行）；雙 surface 歸因限制（段落 0）

**驗證策略**：probe 產出逐 rep 四態表＋flagged case 人工讀（機械 matcher 只當 locator）。

## 段落 5：撞名/權限/孤兒裁定＋跨 harness 差異文檔化（AC#3＋範圍#5）

**Context**：卡範圍#3/#4/#5。多數是裁定記錄落卡（AC#3），少數伴隨小動作。

**要點**：
- 撞名（code-reality repo 15,361B vs plugin 19,532B）：裁定預期＝維持 repo 版生效＋文檔化載入序事實（不改名——repo 版是治理源；plugin 版隨 plugin 升級）
- mermaid 0700 權限：對齊 0755（低風險 chmod＋記錄）
- plugin cache 孤兒（110 vs active 18）：裁定＝不動 cache（plugin 系統自管，清理屬 harness 維護非本 repo 契約面）；記錄理由
- instruction-writing 增補「跨 harness desc 消費差異」：CC 全文 vs ZCode 值 ≤1024 drop＋~250 截斷呈現＋when_to_use 官方鍵（deferred 選項）＋量測陷阱（chars 非 bytes、raw 兩解析器分歧）——落 skill 對應節

**驗證策略**：裁定三項各有記錄落卡（AC#3）；instruction-writing 增補走靜態檢查＋/consistency。

## 整合策略

- 段 1 先行（測試方法落地）→段 2（掃修工具）→段 3（內容改寫，用段 2 script 驗限額）→段 4（行為抽驗，用段 1 方法論＋載具）→段 5（裁定收尾）
- 全弧 commit 分顆粒：段 1（skill 改造＋materials 遷移）／段 2-3（掃修＋改寫）／段 4（probe＋抽驗記錄）／段 5＋收尾
- baseline: `9771931`

## 收尾步驟

- `/consistency` 全綠＋check_single_source；script 兩支語法綠＋實跑證據
- 卡 notes 落：AC#3 裁定三項＋AC#5 四態表＋段 2 修復前後對照
- **卡面決策層回寫（卡即 handoff 紀律）**：(1) 「raw 行 >1024／長度以 raw 行為準」修訂為「desc 值 chars >1024」（實證細化）；(2) 「desc 一律引號化」補 block scalar 2 支例外裁定；(3) when_to_use 增補 4 支裁定
- AC#1-6 逐項對照勾選
- 結案兩步（precheck 綠→metadata commit）＋弧結案蒸餾（memory 條目三條見 UC 盤點）
- `skills/CLAUDE.md` 索引同步檢查

## Build 狀態檢查點（2026-09-14，中間檢查點）

- 段 2 ✅（scan script＋tests 9 條＋30 支引號化＋cr-query 930/nt-v1-query 938；FAIL=0 WARN=2；AC#1 出口證據已落卡 notes）
- 段 1 ✅ 實作面（162→152 行淨 −10；四 surface gate＋protocol＋pilot 遷出＋L10 修訂＋probe script 落位；獨立審待 post-build 鏈）
- 段 3 ✅（flash 凍結規格 7 支 desc 前置改寫＋when_to_use×4；scan 重跑全綠；Claim→Evidence 覆核吻合）
- 段 5 ✅（裁定三項落卡＋instruction-writing 跨 harness 差異節插入＋mermaid 0755；skills/CLAUDE.md 索引判定無 ripple——索引行為功能摘要非 desc 鏡像）
- 段 4 🏃（flash 執行中：smoke→classify 修正→40-run 矩陣→flagged-cases；staging 已修成 bridge 2.0.4 完整形態——cli/config.json model.main＋v2/provider_config.json strict-zod＋env pins；首版 v2-only staging 因 runtime 讀 cli 面而 Model creation failed，經 bridge echo 交叉測試定位）
- **段 4 機制發現（2026-09-14 smoke，影響 AC#2/#5 前提——矩陣完成後定案）**：①ZCode headless `--json` stdout＝單一 final envelope 非事件流——判分事實源改 `$HOME/.zcode/cli/rollout/model-io-sess_*.jsonl`（toolCalls 結構，已逐 rep 複製進 matrix outdir）；②**headless available-skills 呈現＝名稱＋檔案路徑，無 desc/when_to_use**——「desc-250 觸發面」在 headless 環境不存在，實際觸發面＝skill 名稱（與官方文檔 diagnosing-skills:31 宣稱分歧——開放機制問題，AC#5 結果依此解讀）；③scratch home 在 repo 內致 AGENTS.md 往上注入（兩臂對稱汙染——與 production session 同形，視為真實主義非隔離缺陷）
- **段 4 矩陣中斷記錄（2026-09-14 重開機）**：背景矩陣死於 18/40（ZCode app 重啟殺背景 agents——AIR-89 doctrine 活例）。已到手：memory-audit positive 0/5（5×FAIL not loaded——名稱面穩定不觸發形態）、nonmatch 5/5 PASS；implement positive 3/5 PASS（r1 loaded-late、r5 not loaded）、nonmatch 3/3 PASS。續跑由接手 agent 帶 --arm/--reps-from 旗標完成（script 已補 resume 面）
- 機械驗證：ruff/format 全綠、pytest 413 passed（404+9 契約軸）
- 卡面軸修訂已回寫（值 chars＋block scalar 例外＋when_to_use 裁定）
- **Rider（user 09-14 裁決）——model-routing rule 修正**：「judge-review／execution-plan／post-build 編排＝full 不可條件降級」原本只禁降級、未寫 seat 低於角色 tier 時的執行路徑（主 session 換 flash 時 judge 無所適從）。修法（rules/model-routing.md:19）：補「seat 非 full → 升級外派 bridge full-tier model（現值查 model-routing skill tier 表）代行裁決，禁 in-session 降級自判——tier 約束跟角色走、不跟座位走」。drift 掃描確認單一源（skill 端不重複此表）；deploy 3/3 端＋CC rules 落地、413 tests 綠
- 尚待：段 4 矩陣結果＋四態落卡（AC#5）→ post-build 鏈（flash code-review＋codex＋**judge 裁決派 bridge full-tier model（現值查 model-routing skill tier 表）——user 09-14 裁定：主 session 已換 flash，裁決禁 in-session 自判**）→ AC#4(b) 抽樣 → commit 批次 → 結案

## EP Review Findings（2026-09-14，獨立 Explore agent——codex web 池兩敗後 fallback）

總評 GO 附條件（先修 #1/#2/#3/#5/#7）。18 條：17 採納、#18 部分採納（記 known limitation 不擴 probe 面）。關鍵採納落點：#1 when_to_use 47/79 事實→段 0/段 3；#2 discipline 特徵句隨遷＋#3 中類落點行→段 1 要點 2；#4 前 250 掃不承作→段 2；#5 nt-v1-query 納抽驗第 4 支＋#8 provider 時間盒→段 4；#7 AC#4 兩時點→段 3；#9/#14 卡面軸修訂回寫→收尾；#10 L10 精確版＋#11 locator 句→段 1 要點 1/3；#12 probe 殼隨段 1 commit→段 1 要點 5；#13/#15/#16/#17→段 2 已知限制/口徑/tests/轉義規約。原文 18 條全文見 `.agent-tmp/air87/`（審查報告隨弧保存）。
