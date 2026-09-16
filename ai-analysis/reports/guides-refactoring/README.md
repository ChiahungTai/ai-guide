# Guides Refactoring——載體分類構思過程與實作現況

> 日期：2026-09-16（21:4x 快照；數字以文內標注的機械來源為準）。
> 性質：整理文檔——自包含導覽，**非新規範、非定義源**。分類判準單一源仍是 `skills/memory-audit/SKILL.md`「載體統一定義表」；結案操作判準單一源是 kanban-board skill；部署紀律單一源是 `rules/AGENTS.md`。
> 目的：把 09-15 研究鏈的整體構思＋目前 rules／skills／agents／memory 四 corpus 的落地情形與殘留，整理成一份可獨立閱讀的基底，供後續重構（refactoring）討論與決策。
> 姊妹文檔：同日體檢 `.agent-tmp/20260916-2100-repo-memory-health-check.md`、卡片關係圖 `.agent-tmp/20260916-control-plane-card-map.md`。

---

## 1. 問題起點（這套設計在解什麼）

1. **AI coding 產出太快，人追不上**——需要 viewport／導覽讓人「追上實作、理解重要設計」（方向 >> 品質：災難是方向錯，不是 code 醜）。
2. **usage 額度與 context 壓力**——長 session 的 compact 會壓掉推論狀態；compact 品質直接影響後續推論品質。
3. **記憶池曾膨脹失控**（08-30 實證 56.6KB 正回授、149K 肥條目）——寫入端無紀律的池會反噬 recall。
4. **流程 overhead 累積**——多模型（Marshal）協作後，舊流程仍按「主模型／effort／agent 數」決定審查形態，形成兩套編排判準。
5. **四種載體（rules／skills／cards／memory）邊界靠感覺**——同一段內容放哪沒有共同判準，導致重複、誤置、漂移。

---

## 2. 構思過程——09-15 研究鏈（思路如何一步步演進）

### 2.1 鏈總覽（時序＋取代／吸收關係）

| # | 文檔（reports/2026-09-15-*） | 角色 | 關鍵產出 | 終態／被誰吸收 |
|---|---|---|---|---|
| 1 | controlled-compact-strategy | 最早的策略備忘 | threshold 觸發、context-preservation skill、summarizer 等候選 | **方向被否決**（#3 明確不採 threshold／新 skill）；自標「非現行規範」＋現行對應指針 |
| 2 | codex-compact-architecture | sibling repo（codex）源碼分析 | compact 是 harness 第一等 runtime 機制（三策略×三觸發×pre/post 鉤）；**擁有權差異**：我們只能做「壓縮前外部化＋壓縮後恢復」 | 10 條借鏡點進 #5 §8 與 #3；「不做的」也列明（防假裝遺漏） |
| 3 | compact-direction-handoff | 方向定案＋交接 | **checkpoint-first**：不造 summarizer／不新 skill／不建狀態庫；usage／context／品質三分；恢復七步；失敗案例十例；極低額度寫入順序 | 落地為 `_common/task-recovery.md`（恢復順序單一源）＋compact-prep／at／handoff 消費 |
| 4 | memory-mechanism-analysis | 記憶機制總分析 | 全拓撲（主體在 repo／三寫一讀／spine 跨池）；寫入六問；**載體全光譜十行表（§5）**；三層接續（memory／STATE／compact-context，§6）；外部對照（§7）；優化選項（§8） | §5 成為 #10 的素材；§8 優化項分流進 air-98／air-101 S3 |
| 5 | dev-flow-overhead-inventory | 38 項 overhead 決策材料 | 每項：內容／觸發／成本／為什麼有／砍了會怎樣；A（observed）／B（protection）／C（optimization）三類＋六刀法 | 消費於 redesign EP；**部分已被更正**（排程「零成本」→低人力成本；item 30「instruction-testing 沒跑」的判讀後被 AIR-91 行為實驗部分取代） |
| 6 | dev-flow-current-practices-inventory | 現況基線（AIR-91 Done 後） | 全光譜盤點：主鏈／受眾二分／角色體系（Role≠Agent≠Model≠Carrier）／model 體系／作法／追蹤鏈／記憶體系／雜項（§1–8）＋待問清單（§9） | 成為重構的現況底稿；數字已被 09-16 演進部分超越（見 §3.2） |
| 7 | marshal-workflow-overhead-decisions | 流程減量判斷 | **Role 是責任邊界不是 worker 數**；派工按可驗收成果切不按小動作切；省重讀不省新鮮度；最小主鏈 | 整合入 redesign EP S1/S2（M1–M4 外審閉環；正文較寬構想被最末節取代——文內自標） |
| 8 | development-workflow-redesign-checkpoint | 規劃 checkpoint | EP 迭代全史（usage 5%→21%→16% 各波）；規劃交付結算；compact 方向落盤（→#3）；CRUD 分工補充（→#10） | EP 交付；實作交 air-101 |
| 9 | development-workflow-ep-review | EP 獨立審查 | N1–N8＋S1，無 🔴，有條件執行；外部（muse）審查全 agree 後回寫 | 回寫完成（EP SHA `ac5c8b…`）；N5 記錄行錨漂移 +10 的處置方式 |
| 10 | **workflow-carriers-crud-principles** | **分類判準終端** | 四載體 CRUD 矩陣；Card 欄位再分工；8 問誤置判定；常見誤置表；機械／LLM 分工；token 成本觀；遷移六步＋驗收七條 | 本輪重構的判準基準。**不是第五套規則**——採納後應更新對應源（分類單一源＝memory-audit 統一定義表） |

> 鏈的形狀：發散候選（#1）→ 源碼事實（#2）→ 方向收斂（#3）→ 機制全圖（#4）→ 現況與成本盤點（#5/#6）→ 減量原則（#7）→ 規劃與審查（#8/#9）→ **分類判準沉澱（#10）**。

### 2.2 核心設計原則（提煉後，自包含）

**四載體一句話分工**：
> **Rules 約束這次不能犯什麼錯；Skills 告訴 LLM 這類工作怎麼做；Cards 記錄這件工作承諾做什麼、做到哪；Memory 提供跨任務仍有用的個人／專案背景事實。**
> EP 是任務的詳細執行計畫；report 是證據／分析載體；git/code 是可推導實物——不應為硬塞四分法塞進 memory 或 rules。

**兩軸分開判**（內容屬於誰 × 何時載入）：
- ownership／scope：user-level、project、module、task——**讀取頻繁不能改變 scope**（project 事實不能因常用升全域 rule；全域規範不能只藏 project memory）。
- residency：常駐（rule/bundle）→ 任務載入（skill/EP）→ 按需檢索（memory inventory／rg）→ 零 context（git／scratch／hook）。
- 「某 harness 會自動載入某檔」≠「該檔內容本來就該常駐」。

**一行流判定**（載體統一定義表壓縮）：
> 任務終態→卡／EP → repo 可推導→不寫 → user-level 方法論→rule 資格測試 → 模組約束→模組 AGENTS.md → 跨 session user/project 事實→memory → 草稿暫存→`.agent-tmp/` → 純機械＋單一入口＋無語義例外三者皆全→hook（缺一即退 LLM 流程——假確定性比真語義危險）。

**rule 資格**：層級相容 ∩ 首個有後果決策前必須在場 ∩（user 裁定 ∪ verified calibration ∪ trigger bootstrap）。退出常駐過三測試（bootstrap／首動／跨來源重複）。

**memory 寫入端**：動筆前一句話核心事實測試（提煉不出＝不寫）；六問（終態？可推導？同主題？project-* 完結？尺寸？載體？）；desc 文法五條＋三不（不 hash／不日期流水／不 session id——hook 硬擋）；body 蒸後形（lesson-first、禁 timeline／in-flight）。**索引是機械投影禁手寫**；B 形態＝常駐定額（MEMORY.md，gate 6,000 chars）＋全量 `_inventory.md`（rg 可達不進開場）。

**skills 契約**：desc 是唯一觸發面，值 >1024 chars 整支靜默 drop；ZCode 注入面有 metadataBudget 總量預算（AIR-107 逆向＋probe 實證：溢出降級為僅名稱＋路徑）；**單檔單受眾**（LLM 執行鏈 vs 人類 viewport——一檔兩受眾必然 token 牆，/human-review 三度重建又棄的失敗實證）。

**三層接續互不取代**：memory（跨 session durable 活知識）／STATE.md（last-session 觀察層，覆寫非累積，完成度走 git＋卡面）／compact-context 檔（單次 compact 接續，用完即棄，不進任何索引）。

**機械 vs LLM 分工**：機械工具做清單與驗證（列檔、hash、broken refs、生成物差異、bundle 尺寸、卡狀態）；LLM 做 scope／事實假設／trigger 是否足夠／consumer 風險。**相似文字只能提候選，不能自動判語義等價或刪除；標籤（保留／拆分／合併／下沉／上提／引用現有源／退役候選／待查）不是自動 apply 許可**。

**誤置 taxonomy**（memory-audit 統一定義表承載）：A＝user 規範進 project memory；B＝project 知識上提 user rule；V＝現值進 instruction（→spine）；M1＝任務終態入池；M2＝desc 三不；M3＝草稿迭代進池；M4＝repo 可推導入池；M5＝外部委派走 wrapper。

**遷移順序**（六步，不可跳）：確認 scope/owner → 目標源補齊內容 → 更新 consumers/pointers → 驗語義與實際載入 → 清舊副本 → 再驗殘留與部署。**驗收七條**：原情境找得到規範／wrong-task 不誤載／fresh session 首動不漏必要約束／Card 接手能判下一步／memory 不把推測當事實／刪舊源後引用不斷／跨 harness bundle 真正新鮮。僅「檔案更短」不算分類正確。

---

## 3. 目前的實作情形

### 3.1 思路→實作對照（治理卡帳本）

| 載體面 | 卡（狀態） | 落了什麼 |
|---|---|---|
| memory 基建 | air-54（Done） | muse memory 主體遷移 repo `.agents/memory/`＋寫入閘起點 |
| memory 索引 | air-63（Done） | pending 讀取覆層（inbox 發現視圖＋_pending.md 生成器）；**殘留＝零 pending 時路由行斷鏈（F5）** |
| memory 寫入閘 | air-79＋92（Done） | muse 寫入閘 user-scope plugin（一次安裝全 repo 生效）＋live 腿收尾 |
| memory 繞閘 | air-93（Done） | muse session-end 原生直寫的對帳網（`reconcile_memory_pool.py`；偵測非根治） |
| memory 收案 | air-83＋90（Done，**併入 air-100**） | 夜波抽檢半機械化＋池收案流水治理（狀態後綴硬擋＋存量處置） |
| memory 保鮮 | air-98（Done） | spine `model-runtime-entitlements` 探測回寫＋窗口語義正典＋probe 事件入帳 |
| **memory umbrella** | **air-100（To Do）** | 池治理整併弧——auto-memory 導流納管＋存量補審＋寫入防護＋夜波半機械化（併 90/83）→ **本群唯一 open owner** |
| rules 部署面 | air-85（Done） | 條件載入層 vertical slice（bundle-mode-marker＋deploy 投影——pointer projection 的落地弧） |
| rules corpus | air-86（Done） | rules v2 搬遷：slim 三檔＋B 拓撲拆分＋治理檔排除＋guide 批次（acceptance-evidence／symbol-query-routing／instruction-writing 先例） |
| rules 預算 | air-96（Done） | muse bundle 瘦身第一輪 89%→81.6%；**收益已被增長吃回 87.9%（F3，無 owner）** |
| skills 契約 | air-87（Done） | desc 1024 上限掃修＋觸發語義前置＋撞名處置 |
| skills activation | air-88＋107（Done） | pointer activation probe＋per-harness 盤點（矩陣：31 rule 錨／24 語義自明／21 弱名／6 零路徑）＋metadataBudget 機制解 |
| **skills 收尾** | **air-113（To Do）** | 82→84 支逐支處置＋注入面複測（輸入＝107 矩陣）→ **本群唯一執行卡** |
| skills 寫作層 | air-84（Done） | instruction-writing 跨 harness 撰寫層（dir 層四家可達性差異＋model-routing webgpt 失敗態六→八類） |
| model／agents | air-91（Done）＋air-71（To Do） | WorkUnitContract／catalog／presets／resolver 七步／registry 生成制（9 roles）；fleet×WT 調度未開工 |
| 接續鏈 | air-60（Done）＋air-77（In Progress） | rehydration 單一源（task-recovery）＋at 先結算再排程＋授權失效條款；_tasks 工作區一次放好 |
| 治理接線 | air-105＋106＋111（Done） | instruction 審查閘（pre-commit guard）＋部署對帳＋activation-before-review 治理第二波＋EP 載體四層分級（simple/standard/full/bounded-child＋promotion ladder） |
| 收卡防護 | air-104＋108（Done） | kanban 收卡慣例（做完即 Done、L4 集中總驗卡）＋precheck 反向檢查＋judge 結論強制回卡 |
| 改名／bootstrap | air-94（Done）＋air-110（To Do） | ai-rules→ai-guide 全表面遷移；全新機器一鍵安裝未做 |
| 規劃載體重設計 | air-101（Done） | redesign EP S1–S4 落地：依風險安排審查、checkpoint-恢復、成果視圖、（#7 的減量原則進主鏈） |

### 3.2 corpus 機械快照（09-16 21:xx 實測）

| corpus | 規模 | 機械閘 | 分類健康度 |
|---|---|---|---|
| rules/ | 20 檔＝17 neutral（進 bundle）＋2 claude-specific（`bash-hard-rules`／`code-edit-constraints`——Edit/Bash API 約束，指針回 neutral 正典）＋AGENTS.md（meta） | muse bundle **32,387B＝87.9%**（36KiB gate；20:04 部署）；ZCode 90KiB gate 內 | B-form pointer projection（instruction-writing／llm-output-convention）運作中；scope 軸（claude-specific vs neutral）前後一致 |
| skills/ | 84 支 | desc 1024 契約（air-87 掃過）；metadataBudget 梯度（AIR-107） | AIR-107 矩陣是現成分類基礎；instruction-testing 仍 draft 未 pilot |
| agents/ | 9 roles＋presets.toml＋雙 harness 生成 registry | `sync_agents.py --check` **PASS exit 0** | authoring（roles/presets）與 projection（zcode/claude）單一源制衡清楚 |
| `.agents/memory/`（專案池） | 347 條（feedback 164／project 84／reference 99／user 0）＋resident 13＋_inventory 58,629 chars | `--check` **PASS**（frontmatter 全合法）；`reconcile_memory_pool.py` **FAIL exit 2＝86 條未收編**（25M＋60??＋1D） | B 形態正確運作；task-state 命名（`-inflight/-landed/-pending`）機械掃到 **38 條**（多屬已完成弧）＋非後綴同型若干 |
| `~/.agents/`（跨池根） | memory-spine 2 檔＋memory-bundles 7 個日期快照＋probe-entitlements 時間戳 JSON 群＋commands（空）＋skills（symlink） | spine frontmatter 合規；entitlements 今晚 18:08 更新 | spine 內容新鮮但**無 git**；memory-bundles／probe-entitlements 兩個累積面無清理政策 |

### 3.3 已知殘留（open findings，09-16 體檢編號）

- **F1［已解］**：canonical WT 5 個控制面檔曾未 commit 且 live（air-107 doc-sync 以 `a00f291` 收進 main）——缺口形態（live-before-commit 時間窗）留為 air-106① 機制化論據。
- **F2［P1］**：池 86 條未收編——consolidation 波 overdue（最後收編 09-16 05:19）。
- **F3［P2］**：muse bundle 瘦身回漲 87.9%（air-96 一輪到 81.6% 後被增長吃回）——**現無 owner 卡**。
- **F4［P2］**：池 task-state 條目誤置（抽樣 4/4 命中；38 條後綴命名群）——M1 誤置大宗。
- **F5［P3］**：`_pending.md` 斷鏈——generator `_generate_index.py:208-211` 無條件生成路由行、檔案不存在；三選一待裁（機械觀點傾向 generator 條件化）。
- **F6［P3］**：`memory-audit/SKILL.md:149`「projection 機制尚未落地（AIR-85）」已過時（部署實況已落地）——條款反向誤導風險。
- **F7［P3］**：spine 無 git（單副本無歷史）；entitlements 內 webgpt 待辦已被 air-84 修正落 main、可銷帳。
- **F8［P3］**：池 rank 通膨（hot=0／core=346／cold=1，分層軸未發揮）；CRUD 報告自身 kanban:43 錨點漂移。

### 3.4 待討論題清單（本輪重構的入口；只列題不裁決）

**分類正確性／冗餘／多餘（本輪核心三問的初步候選）**：

1. **［冗餘候選］rules 三重述**：`tool-discipline.md`「工具選擇原則」、`modern-cli-preference.md`（9 行全文）、`symbol-query-routing.md` 核心原則——三支 always-on rules 都在講「文字→rg、檔案→fd、符號→code-reality」。候選：modern-cli-preference 退役或併入 tool-discipline 一行（走退出三測試）。
2. **［多餘候選］instruction-testing hanging**：draft、pilot 未跑（overhead inventory item 30 舊判讀→AIR-91 行為實驗是其 B 方案縮減實例）；「先跑起來或判死刑，二選一比 hanging 好」仍未決。
3. **［scope 歸類討論］專案域 skills 住全域共享根**：trading-analysis／swing-analysis／kbar-form-analysis／upgrade-nt／upgrade-sj／nt-query／nt-v1-query 等——ai-guide `skills/` 經 `~/.agents/skills`＋`~/.claude/skills` 對**所有** repo 注入 desc。skills 端沒有像 rules 的 harness-scope／paths 隔離機制；是否需要 per-domain gate（air-85 bundle marker 的 skills 版）→ 討論題。
4. **［群內邊界抽樣］**（air-113 的工作範圍，此處只列對）：instruction 維護群 7 支（init/clean/sync/doc-health/sync-sources/writing/testing）功能邊界互咬檢查；review 群 review-engine vs code-review-and-quality 分工；接續群（compact-prep/at/handoff/deep-work/autonomous-execution＋_common）；維護群（daily-maintain/maintain/standup/corrections-weekly/flow-feedback/flow-review）。
5. **［多餘候選］`~/.agents` 累積面**：memory-bundles/ 7 個日期快照（含改名前 ai-rules-*、mosaic 舊檔——舊快照已被池 git 歷史取代）；probe-entitlements/ 時間戳 JSON 群（AIR-98 probe 產物，retention 政策未見）。歸 air-100 或夜波認養清理政策。
6. **［多餘候選］池 task-state 群**：38 條後綴＋非後綴同型（`project_at-scheduled-repo-memory-audit-0916`、`project_dev-workflow-redesign-plan-ready` 等）——「只剩任務歷程」退役候選，併 F2 收編波裁決。
7. **［防線疑點］air-90「寫入端狀態後綴硬擋」已 Done 但今晚流入 60 條照帶後綴**——硬擋疑只護 muse inbox 路徑，ZCode/CC session 直寫未護。air-100 開工第一動＝驗涵蓋面。
8. **［report 載體自身］**：09-15 研究鏈 11 篇的分類皆正確（report＝證據載體；#1/#7 文內自標被取代關係＋現行指針✓）。多餘面＝#5/#6 兩份 inventory 數字已被 09-16 演進超越、且已消費於 air-101——候選：加「已消費於 air-101」標記或歸檔，不刪（report 是存證載體）。reports/ 目錄本身無 lifecycle 管理（air-103 做的是 ref-docs harness 鏡像）。

**機制面遺留**（inventory §9 摘錄＋體檢）：B 形態常駐 13 條的輪替機制（user 凍結清單手動）；8K–12K 條目區間政策（AIR-69 未決）；池 rank 軸（F8）；muse session-end bypass 根治 vs 維持對帳網（air-93 遺留）；telemetry muse/codex 盲區。

---

## 4. 判定流程怎麼用（操作面摘要，詳版＝CRUD 原則報告）

1. 對「可獨立成立的一段內容」逐項過 **8 問**：事實／方法／約束／任務狀態？哪層 scope？哪個現存來源能證明？等到觸發才讀會不會太晚？已有 owner 嗎？輸出給誰用？更新或刪除會讓哪些 consumer 失效？失效條件是什麼？
2. 裁定標籤：保留／拆分／合併／下沉按需／上提最小 bootstrap／回任務載體／引用現有源／退役候選／待查。**標籤不是 apply 許可**。
3. 機械先行的證據：`sync_agents.py --check`／`_generate_index.py --check`／`reconcile_memory_pool.py`／deploy size gate——四閘全可唯讀跑。
4. 遷移走六步順序＋七條驗收（§2.2 末）；寫入／提交／部署權限各自遵守現行規範（commit 恆為 user gate）。

---

## 5. 來源清單

**思路鏈（`ai-analysis/reports/2026-09-15-*`）**：controlled-compact-strategy／codex-compact-architecture／compact-direction-handoff／memory-mechanism-analysis／dev-flow-overhead-inventory／dev-flow-current-practices-inventory／marshal-workflow-overhead-decisions／development-workflow-redesign-checkpoint／development-workflow-ep-review／**workflow-carriers-crud-principles**（判準基準）＋ `_tasks/09-15-development-workflow-redesign/`（EP＋references 證據群 14 檔）。

**定義源**：`skills/memory-audit/SKILL.md`（分類單一源：載體統一定義表＋六問＋誤置 taxonomy）；`skills/kanban-board/SKILL.md`（Card 欄位＋結案）；`rules/AGENTS.md`（部署紀律＋scope 分類）；`skills/model-routing/SKILL.md`（Role/glossary 正式定義）。

**現況證據（09-16）**：`.agent-tmp/20260916-2100-repo-memory-health-check.md`（體檢 F1–F8）；`.agent-tmp/20260916-control-plane-card-map.md`（卡片關係圖）；四閘實跑輸出（本文 §3.2）。
